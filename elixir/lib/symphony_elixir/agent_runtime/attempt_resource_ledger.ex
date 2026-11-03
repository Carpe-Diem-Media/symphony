defmodule SymphonyElixir.AgentRuntime.AttemptResourceLedger do
  @moduledoc """
  Stores host-owned resource intent with synchronous DETS writes.

  P01 accepts reservations, fencing intent and quarantine.
  A successful write is acknowledged only after DETS sync. A storage-integrity, write or sync error
  blocks this process until validated close and reopen. Restart validates the schema, host,
  namespace, current generation, resource rows and resource keys.

  P01 denies allocation, activation, destruction and verified absence. Fencing
  only reduces authority. Quarantine dispositions retain their meaning across recovery generations,
  and a quarantined resource cannot return to fencing.
  """

  use GenServer

  alias SymphonyElixir.AgentRuntime.AttemptResource
  alias SymphonyElixir.AgentRuntime.CleanupEvidenceRef
  alias SymphonyElixir.AgentRuntime.QuarantineDisposition
  alias SymphonyElixir.AgentRuntime.RecoveryGeneration

  @schema_version 1
  @resource_states [
    :reserved,
    :allocating,
    :allocated,
    :active,
    :fencing,
    :fenced,
    :destroying,
    :absent_verified,
    :cleanup_unverified,
    :quarantined
  ]

  @opaque t :: GenServer.server()
  @type error :: SymphonyElixir.AgentRuntime.AttemptBoundary.error()

  @type transition :: %{
          required(:to) => AttemptResource.state(),
          required(:generation) => RecoveryGeneration.t(),
          required(:allocation_identity_sha256) => String.t() | nil,
          required(:evidence_ref) => String.t() | nil,
          required(:cleanup_ref) => SymphonyElixir.AgentRuntime.CleanupEvidenceRef.t() | nil,
          required(:quarantine) => QuarantineDisposition.t()
        }

  @spec start_link(keyword()) :: {:ok, t()} | :ignore | {:error, term()}
  def start_link(opts) when is_list(opts) do
    case Keyword.get(opts, :owner_name, SymphonyElixir.Orchestrator) do
      owner_name when is_atom(owner_name) ->
        if Process.whereis(owner_name) == self() do
          start_and_link(opts)
        else
          {:error, :unauthorized_caller}
        end

      _ ->
        {:error, :invalid_request}
    end
  end

  def start_link(_opts), do: {:error, :invalid_request}

  @spec close(t()) :: :ok | {:error, error()}
  def close(server), do: safe_call(server, :close)

  @spec reserve_sync(t(), AttemptResource.t()) :: {:ok, AttemptResource.t()} | {:error, error()}
  def reserve_sync(server, resource), do: safe_call(server, {:reserve, resource})

  @spec transition_sync(t(), String.t(), non_neg_integer(), transition()) ::
          {:ok, AttemptResource.t()} | {:error, error()}
  def transition_sync(server, resource_id, revision, transition) do
    safe_call(server, {:transition, resource_id, revision, transition})
  end

  @spec fetch(t(), String.t()) :: {:ok, AttemptResource.t()} | :not_found | {:error, error()}
  def fetch(server, resource_id), do: safe_call(server, {:fetch, resource_id})

  @spec list_for_grant(t(), String.t()) :: {:ok, [AttemptResource.t()]} | {:error, error()}
  def list_for_grant(server, grant_id), do: safe_call(server, {:list_for_grant, grant_id})

  @spec current_generation(t()) :: {:ok, RecoveryGeneration.t()} | {:error, error()}
  def current_generation(server), do: safe_call(server, :current_generation)

  @impl true
  def init(opts) do
    with {:ok, path} <- required_path(opts),
         {:ok, namespace} <- required_id(opts, :project_namespace),
         {:ok, host_id} <- required_id(opts, :host_id),
         {:ok, current_generation} <- startup_generation_option(opts),
         {:ok, owner_name} <- owner_name(opts),
         {:ok, owner_pid} <- registered_pid(owner_name),
         {:ok, recovery_owner_name} <- recovery_owner_name(opts),
         {:ok, recovery_owner_pid} <- optional_registered_pid(recovery_owner_name),
         {:ok, table, path_lock_id} <- open_table(path),
         :ok <- ensure_no_recovery_pending(table),
         {:ok, current_generation} <- choose_startup_generation(table, namespace, host_id, current_generation, opts),
         :ok <- prepare_table(table, path_lock_id, namespace, host_id, current_generation, opts) do
      owner_ref = Process.monitor(owner_pid)

      {:ok,
       %{
         table: table,
         path: path,
         path_lock_id: path_lock_id,
         namespace: namespace,
         host_id: host_id,
         current_generation: current_generation,
         owner_name: owner_name,
         owner_pid: owner_pid,
         owner_epoch: {owner_pid, current_generation},
         owner_ref: owner_ref,
         recovery_owner_name: recovery_owner_name,
         recovery_owner_pid: recovery_owner_pid,
         write_fun: Keyword.get(opts, :write_fun, &:dets.insert/2),
         sync_fun: Keyword.get(opts, :sync_fun, &:dets.sync/1),
         close_fun: Keyword.get(opts, :close_fun, &:dets.close/1),
         blocked: false
       }}
    else
      {:error, reason} -> {:stop, reason}
    end
  end

  defp prepare_table(table, path_lock_id, namespace, host_id, current_generation, opts) do
    with :ok <- ensure_metadata(table, namespace, host_id, current_generation, opts),
         :ok <- validate_rows(table, namespace, host_id, current_generation),
         :ok <- validate_unique_rows(table) do
      :ok
    else
      {:error, reason} ->
        close_table(table)
        release_path_lock(path_lock_id)
        {:error, reason}
    end
  end

  defp start_and_link(opts) do
    case GenServer.start(__MODULE__, opts) do
      {:ok, pid} ->
        try do
          Process.link(pid)
          {:ok, pid}
        catch
          :exit, reason -> {:error, normalize_start_error(reason)}
        end

      {:error, reason} ->
        {:error, normalize_start_error(reason)}
    end
  end

  @impl true
  def handle_call(:close, from, state) do
    with :ok <- authorize(from, state),
         :ok <- close_table(state.table, state.close_fun) do
      release_path_lock(state.path_lock_id)
      {:stop, :normal, :ok, %{state | table: nil}}
    else
      {:error, reason} -> authorization_failure_reply(from, reason, state)
    end
  end

  def handle_call(_request, _from, %{blocked: true} = state) do
    {:reply, {:error, :storage_unavailable}, state}
  end

  def handle_call(request, from, state) do
    case authorize(from, state) do
      :ok ->
        request |> handle_authorized_call(state) |> latch_storage_failure()

      {:error, reason} ->
        authorization_failure_reply(from, reason, state)
    end
  end

  defp authorization_failure_reply({caller, _tag}, reason, state) do
    {epoch_pid, _generation} = state.owner_epoch
    uncertain? = reason == :storage_unavailable or authorized_owner?(caller, state, epoch_pid)
    next_state = if uncertain?, do: %{state | blocked: true}, else: state
    {:reply, {:error, reason}, next_state}
  end

  defp latch_storage_failure({:reply, {:error, reason}, state})
       when reason in [:storage_unavailable, :storage_corrupt, :write_failed, :sync_failed],
       do: {:reply, {:error, reason}, %{state | blocked: true}}

  defp latch_storage_failure(reply), do: reply

  @impl true
  def handle_info({:DOWN, owner_ref, :process, owner_pid, _reason}, %{owner_ref: owner_ref, owner_pid: owner_pid} = state) do
    {:stop, :normal, state}
  end

  def handle_info(_message, state), do: {:noreply, state}

  @impl true
  def terminate(_reason, %{table: nil, path_lock_id: path_lock_id}) do
    release_path_lock(path_lock_id)
    :ok
  end

  def terminate(_reason, %{table: table, path_lock_id: path_lock_id}) do
    result = close_table(table)
    release_path_lock(path_lock_id)
    result
  end

  defp handle_authorized_call({:reserve, resource}, state) do
    with {:ok, resource} <- validate_resource(resource, state),
         {:ok, existing} <- lookup_resource(state.table, resource.resource_id) do
      case existing do
        nil ->
          reserve_if_unclaimed(state, resource)

        ^resource ->
          sync_duplicate(state, resource)

        conflict ->
          quarantine_conflict(state, conflict)
      end
    else
      {:error, reason} -> {:reply, {:error, reason}, state}
    end
  end

  defp handle_authorized_call({:transition, resource_id, revision, transition}, state) do
    with true <- id?(resource_id),
         true <- is_integer(revision) and revision >= 0,
         {:ok, transition} <- validate_transition(transition),
         {:ok, resource} <- lookup_resource(state.table, resource_id),
         false <- is_nil(resource),
         :ok <- transition_guards(resource, revision, transition, state) do
      updated = apply_transition(resource, transition)
      persist(state, {:resource, resource_id}, updated)
    else
      true -> {:reply, {:error, :resource_not_found}, state}
      false -> {:reply, {:error, :invalid_request}, state}
      {:error, reason} -> {:reply, {:error, reason}, state}
    end
  end

  defp handle_authorized_call({:fetch, resource_id}, state) do
    if id?(resource_id) do
      case lookup_resource(state.table, resource_id) do
        {:ok, nil} -> {:reply, :not_found, state}
        {:ok, resource} -> {:reply, {:ok, resource}, state}
        {:error, reason} -> {:reply, {:error, reason}, state}
      end
    else
      {:reply, {:error, :invalid_request}, state}
    end
  end

  defp handle_authorized_call({:list_for_grant, grant_id}, state) do
    if id?(grant_id) do
      case read_all(state.table) do
        {:ok, resources} ->
          selected = resources |> Enum.filter(&(&1.grant_id == grant_id)) |> Enum.sort_by(& &1.resource_id)
          {:reply, {:ok, selected}, state}

        {:error, reason} ->
          {:reply, {:error, reason}, state}
      end
    else
      {:reply, {:error, :invalid_request}, state}
    end
  end

  defp handle_authorized_call(:current_generation, state), do: {:reply, {:ok, state.current_generation}, state}

  defp handle_authorized_call(_request, state), do: {:reply, {:error, :invalid_request}, state}

  defp reserve_if_unclaimed(state, resource) do
    case conflicting_identity(state.table, resource) do
      {:ok, nil} -> insert_reservation(state, resource)
      {:ok, conflict} -> quarantine_conflict(state, conflict)
      {:error, reason} -> {:reply, {:error, reason}, state}
    end
  end

  defp insert_reservation(state, resource) do
    with :ok <- unique_identity(state.table, resource),
         {:reply, {:ok, ^resource}, next_state} <- persist(state, {:resource, resource.resource_id}, resource) do
      {:reply, {:ok, resource}, next_state}
    else
      {:error, reason} -> {:reply, {:error, reason}, state}
      {:reply, reply, next_state} -> {:reply, reply, next_state}
    end
  end

  defp sync_duplicate(state, resource) do
    case sync(state) do
      :ok -> {:reply, {:ok, resource}, state}
      {:error, reason} -> {:reply, {:error, reason}, %{state | blocked: true}}
    end
  end

  defp quarantine_conflict(state, %AttemptResource{state: :quarantined}) do
    case sync(state) do
      :ok -> {:reply, {:error, :resource_conflict}, state}
      {:error, reason} -> {:reply, {:error, reason}, %{state | blocked: true}}
    end
  end

  defp quarantine_conflict(state, %AttemptResource{state: :absent_verified}) do
    {:reply, {:error, :ownership_ambiguous}, %{state | blocked: true}}
  end

  defp quarantine_conflict(state, %AttemptResource{} = resource) do
    quarantine = %QuarantineDisposition{
      state: :quarantined,
      reason: :identity_conflict,
      evidence_ref: nil,
      generation: state.current_generation,
      resolution_ref: nil
    }

    quarantined = %AttemptResource{
      resource
      | state: :quarantined,
        revision: resource.revision + 1,
        reconciliation_generation: state.current_generation,
        quarantine: quarantine
    }

    case persist(state, {:resource, resource.resource_id}, quarantined) do
      {:reply, {:ok, _}, next_state} -> {:reply, {:error, :resource_conflict}, next_state}
      {:reply, {:error, reason}, next_state} -> {:reply, {:error, reason}, next_state}
    end
  end

  defp conflicting_identity(table, resource) do
    case read_all(table) do
      {:ok, rows} ->
        match =
          Enum.find(rows, fn row ->
            row.project_namespace == resource.project_namespace and row.owner_host_id == resource.owner_host_id and
              (row.stable_locator == resource.stable_locator or
                 (row.grant_id == resource.grant_id and row.runtime_identity == resource.runtime_identity and
                    row.class == resource.class))
          end)

        {:ok, match}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp persist(state, key, value) do
    case safe_storage_call(state.write_fun, [state.table, {key, value}]) do
      :ok ->
        case sync(state) do
          :ok -> {:reply, {:ok, value}, state}
          {:error, reason} -> {:reply, {:error, reason}, %{state | blocked: true}}
        end

      {:error, _} ->
        {:reply, {:error, :write_failed}, %{state | blocked: true}}

      _ ->
        {:reply, {:error, :write_failed}, %{state | blocked: true}}
    end
  end

  defp sync(state) do
    case safe_storage_call(state.sync_fun, [state.table]) do
      :ok -> :ok
      _ -> {:error, :sync_failed}
    end
  end

  defp transition_guards(resource, revision, transition, state) do
    cond do
      resource.revision != revision ->
        {:error, :revision_conflict}

      transition.generation != resource.reconciliation_generation or
          transition.generation != state.current_generation ->
        {:error, :recovery_generation_mismatch}

      transition.to not in [:fencing, :quarantined] ->
        {:error, :gate2_profile_incomplete}

      transition.cleanup_ref != nil ->
        {:error, :cleanup_verifier_unavailable}

      not valid_transition_for_resource?(resource, transition) ->
        {:error, :transition_invalid}

      true ->
        :ok
    end
  end

  defp valid_transition_for_resource?(resource, transition) do
    transition.allocation_identity_sha256 == resource.allocation_identity_sha256 and
      valid_transition_quarantine?(transition) and resource.state != :absent_verified and
      allowed_state_transition?(resource.state, transition.to) and
      monotonic_quarantine?(resource.quarantine, transition.quarantine, transition.to)
  end

  defp allowed_state_transition?(state, :fencing) when state in [:reserved, :allocating, :allocated, :active], do: true
  defp allowed_state_transition?(:fencing, :fencing), do: false

  defp allowed_state_transition?(state, to)
       when state in [:reserved, :allocating, :allocated, :active, :fencing, :fenced, :destroying] and
              to == :quarantined,
       do: true

  defp allowed_state_transition?(:cleanup_unverified, :quarantined), do: true
  defp allowed_state_transition?(:quarantined, :quarantined), do: true
  defp allowed_state_transition?(_, _), do: false

  defp monotonic_quarantine?(
         %QuarantineDisposition{state: :clear, generation: generation},
         %QuarantineDisposition{state: :clear, generation: generation},
         :fencing
       ),
       do: true

  defp monotonic_quarantine?(%QuarantineDisposition{state: old}, %QuarantineDisposition{state: new}, :quarantined) do
    progression = [:clear, :quarantined, :block_reuse, :operator_resolution_pending, :remains_quarantined]
    old_index = Enum.find_index(progression, &(&1 == old))
    new_index = Enum.find_index(progression, &(&1 == new))
    old_index != nil and new_index == old_index + 1
  end

  defp monotonic_quarantine?(_, _, _), do: false

  defp valid_transition_quarantine?(%{to: :fencing, quarantine: %QuarantineDisposition{state: :clear} = quarantine, evidence_ref: nil} = transition) do
    valid_quarantine?(quarantine) and quarantine.reason == nil and quarantine.evidence_ref == nil and
      quarantine.resolution_ref == nil and quarantine.generation == transition.generation
  end

  defp valid_transition_quarantine?(%{to: to, quarantine: %QuarantineDisposition{} = q} = transition)
       when to == :quarantined do
    with {:ok, rebuilt} <- QuarantineDisposition.new(Map.from_struct(q)),
         true <- rebuilt == q,
         true <- q.state in [:quarantined, :block_reuse, :operator_resolution_pending, :remains_quarantined],
         true <-
           q.reason in [
             :cleanup_unverified,
             :owner_unknown,
             :identity_conflict,
             :stale_generation,
             :fence_unverified,
             :possible_disclosure,
             :storage_uncertain,
             :external_effect_ambiguous,
             :operator_resolution_required
           ],
         true <- q.generation == transition.generation,
         true <- transition.evidence_ref == q.evidence_ref do
      true
    else
      _ -> false
    end
  end

  defp valid_transition_quarantine?(_), do: false

  defp apply_transition(%AttemptResource{} = resource, transition) do
    %AttemptResource{
      resource
      | state: transition.to,
        revision: resource.revision + 1,
        reconciliation_generation: transition.generation,
        last_evidence_ref: transition.evidence_ref,
        quarantine: transition.quarantine
    }
  end

  defp validate_transition(transition) when is_map(transition) do
    expected = [:to, :generation, :allocation_identity_sha256, :evidence_ref, :cleanup_ref, :quarantine]

    if Enum.sort(Map.keys(transition)) == Enum.sort(expected) and
         transition.to in @resource_states and valid_generation?(transition.generation) and
         optional_digest?(transition.allocation_identity_sha256) and
         optional_id?(transition.evidence_ref) and valid_cleanup_ref?(transition.cleanup_ref) and
         valid_quarantine?(transition.quarantine) do
      {:ok, transition}
    else
      {:error, :invalid_request}
    end
  end

  defp validate_transition(_), do: {:error, :invalid_request}

  defp validate_resource(%AttemptResource{} = resource, state) do
    with true <- exact_struct?(resource, AttemptResource),
         {:ok, normalized} <- AttemptResource.new(Map.from_struct(resource)),
         true <- normalized == resource,
         true <- resource.state == :reserved and resource.revision == 0,
         true <- is_nil(resource.allocation_identity_sha256) and is_nil(resource.last_evidence_ref),
         true <- resource.quarantine.state == :clear,
         true <- is_nil(resource.allocation_identity_sha256) and is_nil(resource.last_evidence_ref),
         true <- resource.quarantine.state == :clear,
         true <- resource.project_namespace == state.namespace,
         true <- resource.owner_host_id == state.host_id,
         true <- resource.creation_generation.project_namespace == state.namespace,
         true <- resource.creation_generation.host_id == state.host_id,
         true <- resource.reconciliation_generation.project_namespace == state.namespace,
         true <- resource.reconciliation_generation.host_id == state.host_id,
         true <- resource.reconciliation_generation == state.current_generation,
         true <- resource.creation_generation == state.current_generation do
      {:ok, resource}
    else
      false when resource.project_namespace != state.namespace -> {:error, :namespace_mismatch}
      false when resource.owner_host_id != state.host_id -> {:error, :namespace_mismatch}
      false -> {:error, :invalid_request}
      {:error, reason} -> {:error, reason}
    end
  end

  defp validate_resource(_, _state), do: {:error, :invalid_request}

  defp lookup_resource(table, resource_id) do
    case safe_storage_call(&:dets.lookup/2, [table, {:resource, resource_id}]) do
      {:ok, []} ->
        {:ok, nil}

      {:ok, [{{:resource, ^resource_id}, %AttemptResource{resource_id: ^resource_id} = resource}]} ->
        normalize_stored_resource(resource)

      {:ok, _} ->
        {:error, :storage_corrupt}

      _ ->
        {:error, :storage_unavailable}
    end
  end

  defp normalize_stored_resource(resource) do
    if is_struct(resource, AttemptResource) and exact_struct?(resource, AttemptResource) do
      case AttemptResource.new(Map.from_struct(resource)) do
        {:ok, ^resource} -> {:ok, resource}
        _ -> {:error, :storage_corrupt}
      end
    else
      {:error, :storage_corrupt}
    end
  end

  defp read_all(table) do
    case safe_storage_call(&:dets.foldl/3, [fn row, acc -> [row | acc] end, [], table]) do
      {:ok, rows} ->
        reduce_resource_rows(rows)

      _ ->
        {:error, :storage_unavailable}
    end
  end

  defp reduce_resource_rows(rows) do
    Enum.reduce_while(rows, {:ok, []}, &read_resource_row/2)
  end

  defp read_resource_row(
         {{:resource, id}, %AttemptResource{resource_id: id} = resource},
         {:ok, acc}
       ) do
    case normalize_stored_resource(resource) do
      {:ok, normalized} -> {:cont, {:ok, [normalized | acc]}}
      {:error, reason} -> {:halt, {:error, reason}}
    end
  end

  defp read_resource_row({{:meta, :ledger}, _metadata}, {:ok, acc}), do: {:cont, {:ok, acc}}
  defp read_resource_row(_row, _acc), do: {:halt, {:error, :storage_corrupt}}

  defp unique_identity(table, resource) do
    case read_all(table) do
      {:ok, rows} ->
        if Enum.any?(rows, fn row ->
             row.project_namespace == resource.project_namespace and row.owner_host_id == resource.owner_host_id and
               (row.stable_locator == resource.stable_locator or
                  (row.grant_id == resource.grant_id and row.runtime_identity == resource.runtime_identity and row.class == resource.class))
           end) do
          {:error, :resource_conflict}
        else
          :ok
        end

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp ensure_metadata(table, namespace, host_id, current_generation, opts) do
    expected = %{
      schema_version: @schema_version,
      project_namespace: namespace,
      host_id: host_id,
      current_generation: current_generation
    }

    case safe_storage_call(&:dets.lookup/2, [table, {:meta, :ledger}]) do
      {:ok, []} ->
        initialize_empty_metadata(table, expected)

      {:ok, [{{:meta, :ledger}, %{schema_version: version} = metadata}]} ->
        validate_metadata(table, metadata, expected, version, opts)

      {:ok, _} ->
        {:error, :storage_corrupt}

      _ ->
        {:error, :storage_unavailable}
    end
  end

  defp initialize_empty_metadata(table, expected) do
    if :dets.info(table, :size) == 0, do: initialize_metadata(table, expected), else: {:error, :storage_corrupt}
  end

  defp validate_metadata(table, metadata, expected, version, opts) do
    cond do
      version != @schema_version -> {:error, :unsupported_schema}
      not valid_metadata_shape?(metadata, expected) -> {:error, :storage_corrupt}
      metadata == expected -> :ok
      recovery_generation?(metadata, expected) -> reconcile_generation(table, metadata, expected, opts)
      true -> {:error, :schema_mismatch}
    end
  end

  defp valid_metadata_shape?(metadata, expected) do
    Enum.sort(Map.keys(metadata)) == Enum.sort(Map.keys(expected)) and
      valid_stored_generation?(Map.get(metadata, :current_generation), expected.project_namespace, expected.host_id)
  end

  defp valid_stored_generation?(%RecoveryGeneration{} = generation, namespace, host_id) do
    generation.project_namespace == namespace and generation.host_id == host_id and
      match?({:ok, ^generation}, RecoveryGeneration.new(Map.from_struct(generation)))
  end

  defp valid_stored_generation?(_, _, _), do: false

  defp recovery_generation?(old, fresh) do
    Map.keys(old) |> Enum.sort() == Map.keys(fresh) |> Enum.sort() and
      old.schema_version == @schema_version and old.project_namespace == fresh.project_namespace and
      old.host_id == fresh.host_id and old.current_generation.project_namespace == fresh.project_namespace and
      old.current_generation.host_id == fresh.host_id and
      fresh.current_generation.sequence > old.current_generation.sequence and
      fresh.current_generation.boot_id != old.current_generation.boot_id and
      fresh.current_generation.nonce != old.current_generation.nonce
  end

  defp reconcile_generation(table, old_metadata, fresh_metadata, opts) do
    old_generation = old_metadata.current_generation
    fresh_generation = fresh_metadata.current_generation

    write_fun = Keyword.get(opts, :write_fun, &:dets.insert/2)
    sync_fun = Keyword.get(opts, :sync_fun, &:dets.sync/1)

    with :ok <- validate_rows(table, old_metadata.project_namespace, old_metadata.host_id, old_generation),
         :ok <- validate_unique_rows(table),
         {:ok, rows} <- read_all(table),
         :ok <- recovery_write(table, {{:meta, :recovery_pending}, true}, write_fun),
         :ok <- recovery_sync(table, sync_fun),
         :ok <- write_reconciled_rows(table, rows, fresh_generation, write_fun),
         :ok <- recovery_write(table, {{:meta, :ledger}, fresh_metadata}, write_fun),
         :ok <- recovery_sync(table, sync_fun),
         :ok <- safe_delete(table, {:meta, :recovery_pending}),
         :ok <- recovery_sync(table, sync_fun) do
      :ok
    else
      {:error, reason} -> {:error, reason}
    end
  end

  defp ensure_no_recovery_pending(table) do
    case safe_storage_call(&:dets.lookup/2, [table, {:meta, :recovery_pending}]) do
      {:ok, []} -> :ok
      {:ok, [{{:meta, :recovery_pending}, true}]} -> {:error, :storage_unavailable}
      {:ok, _} -> {:error, :storage_corrupt}
      _ -> {:error, :storage_unavailable}
    end
  end

  defp safe_delete(table, key) do
    case safe_storage_call(&:dets.delete/2, [table, key]) do
      :ok -> :ok
      _ -> {:error, :write_failed}
    end
  end

  defp write_reconciled_rows(table, rows, generation, write_fun) do
    Enum.reduce_while(rows, :ok, fn %AttemptResource{} = resource, :ok ->
      quarantine = recovery_quarantine(resource.quarantine, generation)

      updated = %AttemptResource{
        resource
        | state: :quarantined,
          revision: resource.revision + 1,
          reconciliation_generation: generation,
          quarantine: quarantine
      }

      case recovery_write(table, {{:resource, resource.resource_id}, updated}, write_fun) do
        :ok -> {:cont, :ok}
        {:error, reason} -> {:halt, {:error, reason}}
      end
    end)
  end

  defp recovery_quarantine(%QuarantineDisposition{state: :clear}, generation) do
    %QuarantineDisposition{
      state: :quarantined,
      reason: :stale_generation,
      evidence_ref: nil,
      generation: generation,
      resolution_ref: nil
    }
  end

  defp recovery_quarantine(%QuarantineDisposition{} = quarantine, _generation), do: quarantine

  defp recovery_write(table, row, write_fun) do
    case safe_storage_call(write_fun, [table, row]) do
      :ok -> :ok
      _ -> {:error, :write_failed}
    end
  end

  defp recovery_sync(table, sync_fun) do
    case safe_storage_call(sync_fun, [table]) do
      :ok -> :ok
      _ -> {:error, :sync_failed}
    end
  end

  defp initialize_metadata(table, metadata) do
    case :dets.insert(table, {{:meta, :ledger}, metadata}) do
      :ok ->
        case :dets.sync(table) do
          :ok -> :ok
          _ -> {:error, :sync_failed}
        end

      _ ->
        {:error, :write_failed}
    end
  end

  defp validate_rows(table, namespace, host_id, current_generation) do
    case safe_storage_call(&:dets.foldl/3, [fn row, acc -> [row | acc] end, [], table]) do
      {:ok, []} ->
        :ok

      {:ok, rows} ->
        Enum.reduce_while(rows, :ok, fn
          {{:resource, id}, %AttemptResource{resource_id: id} = resource}, :ok ->
            validate_resource_row(resource, namespace, host_id, current_generation)

          {{:meta, :ledger}, _metadata}, :ok ->
            {:cont, :ok}

          {{:meta, :recovery_pending}, _marker}, :ok ->
            {:cont, :ok}

          _row, _acc ->
            {:halt, {:error, :storage_corrupt}}
        end)

      _ ->
        {:error, :storage_unavailable}
    end
  end

  defp validate_resource_row(resource, namespace, host_id, current_generation) do
    case normalize_stored_resource(resource) do
      {:ok, normalized} ->
        if resource_matches_ledger?(normalized, namespace, host_id, current_generation),
          do: {:cont, :ok},
          else: {:halt, {:error, :storage_corrupt}}

      _ ->
        {:halt, {:error, :storage_corrupt}}
    end
  end

  defp resource_matches_ledger?(resource, namespace, host_id, current_generation) do
    resource.project_namespace == namespace and resource.owner_host_id == host_id and
      resource.creation_generation.project_namespace == namespace and
      resource.creation_generation.host_id == host_id and
      resource.reconciliation_generation.project_namespace == namespace and
      resource.reconciliation_generation.host_id == host_id and
      resource.reconciliation_generation == current_generation
  end

  defp validate_unique_rows(table) do
    case read_all(table) do
      {:ok, rows} ->
        ambiguous? =
          Enum.with_index(rows)
          |> Enum.any?(fn {left, index} ->
            rows
            |> Enum.drop(index + 1)
            |> Enum.any?(fn right ->
              left.project_namespace == right.project_namespace and left.owner_host_id == right.owner_host_id and
                (left.stable_locator == right.stable_locator or
                   (left.grant_id == right.grant_id and left.runtime_identity == right.runtime_identity and
                      left.class == right.class))
            end)
          end)

        if ambiguous?, do: {:error, :storage_corrupt}, else: :ok

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp open_table(path) do
    File.mkdir_p!(Path.dirname(path))
    table = path
    lock_id = {{__MODULE__, path}, self()}

    if :global.set_lock(lock_id, [node()], 0) do
      case :dets.open_file(table,
             file: String.to_charlist(path),
             type: :set,
             auto_save: :infinity,
             repair: false
           ) do
        {:ok, ^table} ->
          {:ok, table, lock_id}

        {:error, _} ->
          release_path_lock(lock_id)
          {:error, :storage_unavailable}
      end
    else
      {:error, :storage_unavailable}
    end
  rescue
    _ -> {:error, :storage_unavailable}
  end

  defp release_path_lock(lock_id) do
    :global.del_lock(lock_id, [node()])
    :ok
  catch
    _, _ -> :ok
  end

  defp close_table(nil), do: :ok

  defp close_table(table) do
    close_table(table, &:dets.close/1)
  end

  defp close_table(table, close_fun) do
    case safe_storage_call(close_fun, [table]) do
      :ok -> :ok
      _ -> {:error, :storage_unavailable}
    end
  end

  defp authorize({caller, _tag}, state) do
    {epoch_pid, epoch_generation} = state.owner_epoch

    if authorized_owner?(caller, state, epoch_pid) and epoch_generation == state.current_generation do
      authorize_metadata(state, epoch_generation)
    else
      {:error, :unauthorized_caller}
    end
  end

  defp authorized_owner?(caller, state, epoch_pid) do
    registered_owner? = registered_owner?(caller, state, epoch_pid)
    registered_recovery_owner? = registered_recovery_owner?(caller, state)
    registered_owner? or registered_recovery_owner?
  end

  defp registered_owner?(caller, state, epoch_pid) do
    Process.whereis(state.owner_name) == state.owner_pid and caller == state.owner_pid and
      state.owner_pid == epoch_pid
  end

  defp registered_recovery_owner?(caller, state) do
    state.recovery_owner_name != nil and
      Process.whereis(state.recovery_owner_name) == state.recovery_owner_pid and
      caller == state.recovery_owner_pid
  end

  defp authorize_metadata(state, epoch_generation) do
    case safe_storage_call(&:dets.lookup/2, [state.table, {:meta, :ledger}]) do
      {:ok, [{{:meta, :ledger}, metadata}]} ->
        validate_authority_metadata(metadata, state, epoch_generation)

      {:ok, _} ->
        {:error, :unauthorized_caller}

      _ ->
        {:error, :storage_unavailable}
    end
  end

  defp validate_authority_metadata(metadata, state, epoch_generation) do
    expected_keys = [:schema_version, :project_namespace, :host_id, :current_generation]

    if is_map(metadata) and Enum.sort(Map.keys(metadata)) == Enum.sort(expected_keys) and
         metadata.schema_version == @schema_version and
         metadata.project_namespace == state.namespace and metadata.host_id == state.host_id and
         metadata.current_generation == epoch_generation do
      :ok
    else
      {:error, :unauthorized_caller}
    end
  end

  defp safe_call(server, request) do
    GenServer.call(server, request, 5_000)
  catch
    :exit, _ -> {:error, :boundary_unavailable}
  end

  defp normalize_start_error({:shutdown, reason}), do: normalize_start_error(reason)

  defp normalize_start_error(reason)
       when reason in [
              :invalid_request,
              :unauthorized_caller,
              :storage_unavailable,
              :storage_corrupt,
              :write_failed,
              :sync_failed,
              :unsupported_schema,
              :schema_mismatch
            ],
       do: reason

  defp normalize_start_error(_reason), do: :boundary_unavailable

  defp required_path(opts) do
    case Keyword.get(opts, :path) do
      path when is_binary(path) and byte_size(path) > 0 -> {:ok, Path.expand(path)}
      _ -> {:error, :invalid_request}
    end
  end

  defp required_id(opts, key) do
    case Keyword.get(opts, key) do
      value when is_binary(value) and byte_size(value) in 1..256 -> {:ok, value}
      _ -> {:error, :invalid_request}
    end
  end

  defp required_generation(opts) do
    case Keyword.get(opts, :current_generation) do
      %RecoveryGeneration{} = generation ->
        if valid_generation?(generation), do: {:ok, generation}, else: {:error, :invalid_request}

      _ ->
        {:error, :invalid_request}
    end
  end

  defp startup_generation_option(opts) do
    if Keyword.get(opts, :startup_recovery, false) do
      {:ok, nil}
    else
      required_generation(opts)
    end
  end

  defp choose_startup_generation(_table, namespace, host_id, %RecoveryGeneration{} = generation, _opts) do
    if generation.project_namespace == namespace and generation.host_id == host_id,
      do: {:ok, generation},
      else: {:error, :namespace_mismatch}
  end

  defp choose_startup_generation(table, namespace, host_id, nil, opts) do
    case safe_storage_call(&:dets.lookup/2, [table, {:meta, :ledger}]) do
      {:ok, []} ->
        fresh_generation(namespace, host_id, 1, opts)

      {:ok, [{{:meta, :ledger}, metadata}]} ->
        next_startup_generation(metadata, namespace, host_id, opts)

      {:ok, _} ->
        {:error, :storage_corrupt}

      _ ->
        {:error, :storage_unavailable}
    end
  end

  defp next_startup_generation(metadata, namespace, host_id, opts) do
    with true <- valid_startup_metadata?(metadata, namespace, host_id),
         %RecoveryGeneration{} = generation <- Map.get(metadata, :current_generation),
         {:ok, validated} <- RecoveryGeneration.new(Map.from_struct(generation)) do
      fresh_generation(namespace, host_id, validated.sequence + 1, opts)
    else
      _ -> {:error, :storage_corrupt}
    end
  end

  defp valid_startup_metadata?(metadata, namespace, host_id) when is_map(metadata) do
    Enum.sort(Map.keys(metadata)) == [:current_generation, :host_id, :project_namespace, :schema_version] and
      metadata.schema_version == @schema_version and metadata.project_namespace == namespace and
      metadata.host_id == host_id
  end

  defp valid_startup_metadata?(_, _, _), do: false

  defp fresh_generation(namespace, host_id, sequence, _opts) do
    RecoveryGeneration.new(%{
      schema_version: 1,
      project_namespace: namespace,
      host_id: host_id,
      boot_id: Base.encode16(:crypto.strong_rand_bytes(16), case: :lower),
      sequence: sequence,
      nonce: Base.encode16(:crypto.strong_rand_bytes(16), case: :lower)
    })
  end

  defp valid_cleanup_ref?(nil), do: true

  defp valid_cleanup_ref?(%CleanupEvidenceRef{} = reference) do
    exact_struct?(reference, CleanupEvidenceRef) and
      match?({:ok, ^reference}, CleanupEvidenceRef.new(Map.from_struct(reference)))
  end

  defp valid_cleanup_ref?(_), do: false

  defp valid_quarantine?(%QuarantineDisposition{} = quarantine) do
    exact_struct?(quarantine, QuarantineDisposition) and
      match?({:ok, ^quarantine}, QuarantineDisposition.new(Map.from_struct(quarantine)))
  end

  defp valid_quarantine?(_), do: false

  defp owner_name(opts) do
    case Keyword.get(opts, :owner_name, SymphonyElixir.Orchestrator) do
      name when is_atom(name) -> {:ok, name}
      _ -> {:error, :invalid_request}
    end
  end

  defp recovery_owner_name(opts) do
    case Keyword.get(opts, :recovery_owner_name) do
      nil -> {:ok, nil}
      name when is_atom(name) -> {:ok, name}
      _ -> {:error, :invalid_request}
    end
  end

  defp registered_pid(name) do
    case Process.whereis(name) do
      pid when is_pid(pid) -> {:ok, pid}
      _ -> {:error, :unauthorized_caller}
    end
  end

  defp optional_registered_pid(nil), do: {:ok, nil}
  defp optional_registered_pid(name), do: registered_pid(name)

  defp safe_storage_call(fun, args) do
    case apply(fun, args) do
      {:ok, _} = ok -> ok
      :ok -> :ok
      {:error, _} = error -> error
      list when is_list(list) -> {:ok, list}
      other -> {:error, other}
    end
  rescue
    _ -> {:error, :storage_unavailable}
  catch
    _, _ -> {:error, :storage_unavailable}
  end

  defp valid_generation?(%RecoveryGeneration{} = generation) do
    exact_struct?(generation, RecoveryGeneration) and
      match?({:ok, ^generation}, RecoveryGeneration.new(Map.from_struct(generation)))
  end

  defp valid_generation?(_), do: false

  defp exact_struct?(value, module) do
    is_struct(value, module) and
      Enum.sort(Map.keys(value)) == Enum.sort([:__struct__ | Map.keys(Map.from_struct(module.__struct__()))])
  end

  defp id?(value), do: is_binary(value) and byte_size(value) in 1..256 and String.trim(value) != ""
  defp optional_id?(nil), do: true
  defp optional_id?(value), do: id?(value)
  defp optional_digest?(nil), do: true
  defp optional_digest?(value), do: is_binary(value) and Regex.match?(~r/\A[a-f0-9]{64}\z/, value)
end
