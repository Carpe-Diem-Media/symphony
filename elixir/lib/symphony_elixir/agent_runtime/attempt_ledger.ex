defmodule SymphonyElixir.AgentRuntime.AttemptLedger do
  @moduledoc """
  Small disk-backed boundary for safety-relevant attempt lineage state.

  The ledger is deliberately not a scheduler or a source of current tracker
  truth. It stores only the counters and exhaustion state needed to preserve
  autonomous safety decisions across a process restart.
  """

  alias SymphonyElixir.AgentRuntime.AttemptBoundary
  alias SymphonyElixir.AgentRuntime.AttemptLedgerMigration
  alias SymphonyElixir.AgentRuntime.AttemptPolicy
  alias SymphonyElixir.AgentRuntime.CleanupEvidenceRef
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.Config.Schema
  alias SymphonyElixir.WorkControl.{ProviderObservation, SuspensionContext}

  @schema_version 2
  @durable_counter_keys [:ordinary_failures, :ordinary_retries, :review_cycles]
  @base_record_keys [
    :schema_version,
    :project_namespace,
    :issue_id,
    :lineage_id,
    :safety_counters,
    :status,
    :stop_reason,
    :route_fingerprint,
    :in_flight,
    :authority_fence,
    :close_pending,
    :updated_at
  ]
  @history_record_keys @base_record_keys ++ [:closed_reason, :rearm_reason, :rearmed_by, :rearmed_at]
  @allowed_identity_keys [:tracker_kind, :provider_scope]
  @allowed_scope_keys [:project_slug, :repo, :project_key, :project_gid, :workspace_slug, :workspace_id, :project_id]

  defstruct [:table, :path, :project_id, :tracker_identity, :write_fun, :sync_fun, schema_version: 1]

  @type t :: %__MODULE__{
          table: term(),
          path: Path.t(),
          project_id: String.t(),
          tracker_identity: map(),
          write_fun: (atom(), term() -> term()),
          sync_fun: (atom() -> term()),
          schema_version: 1 | 2
        }

  @type record :: %{atom() => term()}

  @spec schema_version() :: 2
  def schema_version, do: @schema_version

  @spec schema_version(t()) :: 1 | 2
  def schema_version(%__MODULE__{schema_version: version}), do: version

  @doc false
  def configured_schema(project_id, tracker_identity, opts \\ [])

  @spec configured_schema(String.t(), map(), keyword()) ::
          {:ok, 1 | 2, boolean()} | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}

  def configured_schema(project_id, tracker_identity, opts)
      when is_binary(project_id) and is_map(tracker_identity) and is_list(opts) do
    path = path_for(project_id, opts)

    if File.regular?(path),
      do: configured_schema_for_existing_file(path, project_id, tracker_identity),
      else: {:error, :migration_required}
  rescue
    _ -> {:error, :storage_corrupt}
  end

  def configured_schema(_project_id, _tracker_identity, _opts), do: {:error, :invalid_request}

  defp configured_schema_for_existing_file(path, project_id, tracker_identity) do
    case AttemptLedgerMigration.with_open_lock(path, fn ->
           read_configured_schema(path, project_id, tracker_identity)
         end) do
      {:ok, result} -> result
      {:error, _reason} -> {:error, :migration_in_progress}
    end
  end

  @doc false
  def configured_mode(mode, project_id, tracker_identity, opts \\ [])

  @spec configured_mode(String.t(), String.t(), map(), keyword()) ::
          :ok | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}

  def configured_mode("legacy", project_id, tracker_identity, opts) do
    case configured_schema(project_id, tracker_identity, opts) do
      {:ok, 2, true} -> {:error, :binding_downgrade_denied}
      {:ok, _version, _has_gate2_binding} -> :ok
      {:error, :migration_required} -> :ok
      {:error, reason} -> {:error, reason}
    end
  end

  def configured_mode("gate2_foundation", project_id, tracker_identity, opts) do
    case configured_schema(project_id, tracker_identity, opts) do
      {:ok, 2, _has_gate2_binding} -> :ok
      {:ok, _version, _has_gate2_binding} -> {:error, :migration_required}
      {:error, reason} -> {:error, reason}
    end
  end

  def configured_mode("gate2_enforced", _project_id, _tracker_identity, _opts),
    do: {:error, :gate2_profile_incomplete}

  def configured_mode(_mode, _project_id, _tracker_identity, _opts),
    do: {:error, :invalid_request}

  defp read_configured_schema(path, project_id, tracker_identity) do
    # Validate the locked snapshot before checking its receipt. Reopening an
    # already-owned read-write table as read-only would reject a healthy ledger.
    with {:ok, rows} <- read_configured_rows(path),
         {:ok, version} <- configured_rows_schema(rows),
         :ok <- validate_snapshot(project_id, tracker_identity, rows, version),
         :ok <- AttemptLedgerMigration.admission_check(path, project_id, tracker_identity, version) do
      gate2_binding? =
        Enum.any?(rows, fn
          {{kind, _key}, %{boundary_binding: %{kind: :gate2}}} when kind in [:current, :history] -> true
          _ -> false
        end)

      {:ok, version, gate2_binding?}
    else
      {:error, reason} -> {:error, normalize_configured_schema_error(reason)}
    end
  end

  defp read_configured_rows(path) do
    if :dets.info(path) == :undefined,
      do: open_configured_rows(path),
      else: read_open_configured_rows(path)
  rescue
    _ -> {:error, :storage_corrupt}
  end

  defp open_configured_rows(path) do
    case :dets.open_file(path, file: String.to_charlist(path), type: :set, access: :read, repair: false) do
      {:ok, ^path} ->
        result = {:ok, :dets.foldl(fn row, acc -> [row | acc] end, [], path)}
        if :dets.close(path) == :ok, do: result, else: {:error, :storage_unavailable}

      {:error, {:already_started, _pid}} ->
        read_open_configured_rows(path)

      {:error, _reason} ->
        {:error, :storage_corrupt}
    end
  end

  defp read_open_configured_rows(path) do
    case :dets.info(path, :access) do
      access when access in [:read, :read_write] ->
        {:ok, :dets.foldl(fn row, acc -> [row | acc] end, [], path)}

      _ ->
        {:error, :storage_unavailable}
    end
  end

  defp configured_rows_schema(rows) do
    case Enum.find(rows, &match?({{:meta, _}, _}, &1)) do
      {{:meta, _}, %{schema_version: version}} when version in [1, 2] -> {:ok, version}
      {{:meta, _}, %{schema_version: _version}} -> {:error, :unsupported_schema}
      _ -> {:error, :storage_corrupt}
    end
  end

  @spec normalize_configured_schema_error(term()) ::
          :migration_in_progress
          | :unsupported_schema
          | :storage_unavailable
          | :namespace_mismatch
          | :identity_mismatch
          | :schema_mismatch
          | :storage_corrupt
  defp normalize_configured_schema_error(:migration_in_progress), do: :migration_in_progress
  defp normalize_configured_schema_error(:unsupported_schema), do: :unsupported_schema
  defp normalize_configured_schema_error(:storage_unavailable), do: :storage_unavailable

  defp normalize_configured_schema_error(reason)
       when reason in [:namespace_mismatch, :identity_mismatch, :schema_mismatch],
       do: reason

  defp normalize_configured_schema_error(_reason), do: :storage_corrupt

  @spec path_for(String.t(), keyword()) :: Path.t()
  def path_for(project_id, opts \\ []) when is_binary(project_id) do
    case Keyword.get(opts, :path) do
      path when is_binary(path) ->
        Path.expand(path)

      _ ->
        root =
          Keyword.get(opts, :root) ||
            Application.get_env(:symphony_elixir, :attempt_ledger_root) ||
            default_root()

        Path.join(Path.expand(root), project_id <> ".dets")
    end
  end

  @spec open(String.t(), map(), keyword()) :: {:ok, t()} | {:error, term()}
  def open(project_id, tracker_identity, opts \\ [])
      when is_binary(project_id) and is_map(tracker_identity) do
    with :ok <- validate_project_id(project_id),
         :ok <- validate_tracker_identity(tracker_identity),
         path <- path_for(project_id, opts),
         :ok <- ensure_parent_directory(path),
         {:ok, result} <-
           AttemptLedgerMigration.with_open_lock(path, fn ->
             open_locked(path, project_id, tracker_identity, opts)
           end) do
      result
    end
  end

  defp open_locked(path, project_id, tracker_identity, opts) do
    with :ok <- migration_journal_clear(path),
         {:ok, table} <- open_table(path) do
      open_table_ledger(table, path, project_id, tracker_identity, opts)
    end
  end

  defp open_table_ledger(table, path, project_id, tracker_identity, opts) do
    result =
      with {:ok, ledger} <- build_ledger(table, path, project_id, tracker_identity, opts),
           :ok <- AttemptLedgerMigration.admission_check(path, project_id, tracker_identity, ledger.schema_version),
           :ok <- initialize_or_validate(ledger) do
        {:ok, ledger}
      end

    case result do
      {:ok, _ledger} ->
        result

      {:error, _reason} = error ->
        _ = close_table(table)
        error
    end
  end

  defp migration_journal_clear(path) do
    AttemptLedgerMigration.admission_check(path)
  end

  @doc false
  @spec validate_snapshot(String.t(), map(), [term()], 1 | 2) ::
          :ok | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def validate_snapshot(project_id, tracker_identity, rows, expected_schema)
      when is_binary(project_id) and is_map(tracker_identity) and is_list(rows) and expected_schema in [1, 2] do
    ledger = %__MODULE__{
      project_id: project_id,
      tracker_identity: tracker_identity,
      schema_version: expected_schema
    }

    with {:ok, metadata} <- metadata_record(rows),
         :ok <- validate_metadata(metadata, ledger),
         true <- Map.fetch!(elem(metadata, 1), :schema_version) == expected_schema,
         :ok <- validate_stored_records(rows, ledger) do
      :ok
    else
      false -> {:error, :storage_corrupt}
      {:error, reason} -> {:error, normalize_snapshot_error(reason)}
    end
  rescue
    _ -> {:error, :storage_corrupt}
  end

  defp normalize_snapshot_error({:ledger_project_namespace_mismatch, _, _}), do: :namespace_mismatch
  defp normalize_snapshot_error({:ledger_tracker_identity_mismatch, _, _}), do: :identity_mismatch
  defp normalize_snapshot_error({:ledger_schema_version_unsupported, _}), do: :unsupported_schema
  defp normalize_snapshot_error(_), do: :storage_corrupt

  @spec close(t()) :: :ok | {:error, term()}
  def close(%__MODULE__{table: table}) do
    close_table(table)
  end

  @spec bind_gate2_fence_sync(t(), String.t(), SymphonyElixir.AgentRuntime.AttemptGrant.ref()) ::
          :ok | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def bind_gate2_fence_sync(%__MODULE__{} = ledger, issue_id, reference)
      when is_binary(issue_id) and is_map(reference),
      do: AttemptBoundary.bind_gate2_fence_sync(ledger, issue_id, reference)

  def bind_gate2_fence_sync(_ledger, _issue_id, _reference), do: {:error, :invalid_request}

  @spec release_gate2_authority_fence(
          t(),
          String.t(),
          Identity.t(),
          SymphonyElixir.AgentRuntime.CleanupEvidenceRef.t()
        ) :: :ok | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def release_gate2_authority_fence(
        %__MODULE__{} = ledger,
        issue_id,
        %Identity{} = identity,
        %CleanupEvidenceRef{} = evidence
      )
      when is_binary(issue_id),
      do: AttemptBoundary.release_gate2_authority_fence(ledger, issue_id, identity, evidence)

  def release_gate2_authority_fence(_ledger, _issue_id, _identity, _evidence), do: {:error, :invalid_request}

  @doc false
  @spec bind_gate2_fence_from_boundary(t(), String.t(), SymphonyElixir.AgentRuntime.AttemptGrant.ref()) ::
          :ok | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def bind_gate2_fence_from_boundary(%__MODULE__{} = ledger, issue_id, reference) do
    case validate_gate2_binding_request(ledger, issue_id, reference) do
      :ok ->
        case current(ledger, issue_id) do
          :not_found ->
            persist_new_gate2_lineage(ledger, issue_id, reference)

          {:ok, record} ->
            bind_existing_gate2_lineage(ledger, issue_id, record, reference)

          {:error, reason} ->
            {:error, normalize_gate2_error(reason)}
        end

      {:error, reason} ->
        {:error, normalize_gate2_error(reason)}
    end
  end

  def bind_gate2_fence_from_boundary(_ledger, _issue_id, _reference), do: {:error, :invalid_request}

  defp validate_gate2_binding_request(ledger, issue_id, reference) do
    boundary = AttemptBoundary

    cond do
      Process.whereis(boundary) != self() -> {:error, :gate2_boundary_required}
      ledger.schema_version != 2 -> {:error, :gate2_boundary_required}
      not is_binary(issue_id) -> {:error, :gate2_boundary_required}
      not valid_gate2_reference?(reference) -> {:error, :gate2_boundary_required}
      reference.project_namespace != ledger.project_id -> {:error, :gate2_boundary_required}
      true -> :ok
    end
  end

  defp bind_existing_gate2_lineage(ledger, issue_id, record, reference) do
    with %{kind: :gate2, resource_ledger_namespace: namespace} <- Map.get(record, :boundary_binding),
         true <- namespace == ledger.project_id,
         true <- reference.runtime_identity.work_item_id == issue_id,
         true <- reference.runtime_identity.lineage_generation == record.lineage_id,
         %{state: :bound, runtime_attempt: identity} = fence <- current_fence(record),
         true <- identity == reference.runtime_identity do
      bind_existing_gate2_fence(ledger, issue_id, record, fence, reference)
    else
      false -> {:error, :gate2_boundary_required}
      nil -> {:error, :grant_not_found}
      _ -> {:error, :grant_not_found}
    end
  end

  defp bind_existing_gate2_fence(ledger, issue_id, record, fence, reference) do
    case Map.get(fence, :gate2_fence) do
      nil ->
        updated_fence = Map.put(fence, :gate2_fence, %{reference: reference, status: :requested})
        updated = record |> Map.put(:authority_fence, updated_fence) |> Map.put(:updated_at, now_ms())
        persist_gate2_update(ledger, issue_id, updated)

      %{reference: ^reference, status: :requested} ->
        :ok

      _ ->
        {:error, :binding_downgrade_denied}
    end
  end

  defp persist_gate2_update(ledger, issue_id, updated) do
    with :ok <- validate_record(updated, ledger, issue_id, allowed_record_keys(updated)),
         :ok <- persist_records(ledger, [{{:current, issue_id}, updated}]) do
      :ok
    else
      {:error, reason} -> {:error, normalize_gate2_error(reason)}
    end
  end

  defp persist_new_gate2_lineage(ledger, issue_id, reference) do
    identity = reference.runtime_identity

    record = %{
      schema_version: 2,
      project_namespace: ledger.project_id,
      issue_id: issue_id,
      lineage_id: identity.lineage_generation,
      safety_counters: durable_counter_defaults(),
      status: :open,
      stop_reason: nil,
      route_fingerprint: nil,
      in_flight: true,
      authority_fence: %{
        state: :bound,
        runtime_attempt: identity,
        route_fingerprint: nil,
        gate2_fence: %{reference: reference, status: :requested}
      },
      close_pending: false,
      updated_at: now_ms(),
      boundary_binding: %{
        kind: :gate2,
        binding_version: 1,
        lineage_binding_id: new_lineage_id(),
        resource_ledger_namespace: ledger.project_id
      }
    }

    with true <- reference.runtime_identity.work_item_id == issue_id,
         :ok <- validate_record(record, ledger, issue_id, @base_record_keys),
         :ok <- validate_record(record, ledger, issue_id, allowed_record_keys(record)),
         :ok <- persist_records(ledger, [{{:current, issue_id}, record}]) do
      :ok
    else
      false -> {:error, :identity_mismatch}
      {:error, reason} -> {:error, normalize_gate2_error(reason)}
    end
  end

  @doc false
  @spec request_gate2_fence_from_boundary(t(), String.t(), SymphonyElixir.AgentRuntime.AttemptGrant.ref(), atom()) ::
          :ok | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def request_gate2_fence_from_boundary(%__MODULE__{} = ledger, issue_id, reference, reason) do
    boundary = SymphonyElixir.AgentRuntime.AttemptBoundary

    with true <- Process.whereis(boundary) == self(),
         true <- ledger.schema_version == 2,
         true <- valid_gate2_reference?(reference),
         true <- reason in [:completion, :cancellation, :failure, :restart, :publication],
         {:ok, record} <- current(ledger, issue_id),
         %{
           state: :bound,
           gate2_fence: %{reference: ^reference, status: :requested} = gate2
         } = fence <- current_fence(record) do
      case Map.get(gate2, :requested_reason) do
        nil ->
          updated_gate2 = Map.put(gate2, :requested_reason, reason)
          updated_fence = Map.put(fence, :gate2_fence, updated_gate2)
          updated = record |> Map.put(:authority_fence, updated_fence) |> Map.put(:updated_at, now_ms())

          persist_gate2_update(ledger, issue_id, updated)

        ^reason ->
          :ok

        _other ->
          {:error, :binding_downgrade_denied}
      end
    else
      false -> {:error, :gate2_boundary_required}
      nil -> {:error, :grant_not_found}
      {:error, reason} -> {:error, normalize_gate2_error(reason)}
      _ -> {:error, :grant_not_found}
    end
  end

  def request_gate2_fence_from_boundary(_ledger, _issue_id, _reference, _reason), do: {:error, :invalid_request}

  @doc false
  @spec gate2_fence_reference(t(), String.t()) ::
          {:ok, SymphonyElixir.AgentRuntime.AttemptGrant.ref()} | :not_found | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def gate2_fence_reference(%__MODULE__{} = ledger, issue_id) when is_binary(issue_id) do
    case current(ledger, issue_id) do
      {:ok,
       %{
         authority_fence: %{state: :bound} = fence,
         boundary_binding: %{kind: :gate2, resource_ledger_namespace: namespace}
       }} ->
        requested_gate2_reference(ledger, namespace, fence)

      {:ok, _} ->
        :not_found

      :not_found ->
        :not_found

      {:error, reason} ->
        {:error, normalize_gate2_error(reason)}
    end
  end

  def gate2_fence_reference(_ledger, _issue_id), do: {:error, :invalid_request}

  defp requested_gate2_reference(ledger, namespace, fence) do
    case Map.get(fence, :gate2_fence) do
      %{reference: reference, status: :requested} = gate2
      when namespace == ledger.project_id and map_size(gate2) in [2, 3] ->
        if valid_gate2_reference?(reference) and valid_requested_reason?(gate2),
          do: {:ok, reference},
          else: {:error, :storage_corrupt}

      _ ->
        :not_found
    end
  end

  @spec current(t(), String.t()) :: {:ok, record()} | :not_found | {:error, term()}
  def current(%__MODULE__{table: table} = ledger, issue_id) when is_binary(issue_id) do
    case safe_lookup(table, {:current, issue_id}) do
      {:ok, [{_, record}]} ->
        case validate_record(record, ledger, issue_id, allowed_record_keys(record)) do
          :ok -> {:ok, record}
          {:error, reason} -> {:error, reason}
        end

      {:ok, []} ->
        :not_found

      {:error, reason} ->
        {:error, reason}
    end
  end

  @spec open_lineages(t()) :: {:ok, [record()]} | {:error, term()}
  def open_lineages(%__MODULE__{} = ledger) do
    with {:ok, records} <- all_records(ledger) do
      records
      |> Enum.filter(fn {key, record} ->
        match?({:current, _issue_id}, key) and
          (Map.get(record, :status) in [:open, :exhausted] or Map.get(record, :close_pending, false))
      end)
      |> Enum.map(&elem(&1, 1))
      |> then(&{:ok, Enum.sort_by(&1, fn record -> record.issue_id end)})
    end
  end

  @spec history(t()) :: {:ok, [record()]} | {:error, term()}
  def history(%__MODULE__{} = ledger) do
    with {:ok, records} <- all_records(ledger) do
      records
      |> Enum.filter(&match?({{:history, _lineage_id}, _record}, &1))
      |> Enum.map(&elem(&1, 1))
      |> then(&{:ok, Enum.sort_by(&1, fn record -> record.updated_at end)})
    end
  end

  @spec put(t(), record()) :: :ok | {:error, term()}
  def put(%__MODULE__{} = ledger, record) when is_map(record) do
    issue_id = Map.get(record, :issue_id)
    current_record = if is_binary(issue_id), do: current(ledger, issue_id), else: :not_found

    with :ok <- preserve_boundary_binding(current_record, record),
         :ok <- validate_put_fence(current_record, record),
         :ok <- validate_record(record, ledger, issue_id, @base_record_keys),
         issue_id when is_binary(issue_id) <- issue_id,
         :ok <- persist_status_allowed?(ledger, issue_id, Map.get(record, :status)) do
      persist_records(ledger, [{{:current, issue_id}, record}])
    else
      nil -> {:error, {:corrupt_attempt_record, :current, :invalid_record}}
      {:error, reason} -> {:error, reason}
    end
  end

  def put(_ledger, _record), do: {:error, {:corrupt_attempt_record, :current, :invalid_record}}

  defp validate_put_fence({:ok, %{in_flight: true} = current_record}, record) do
    current_fence = Map.get(current_record, :authority_fence)
    incoming_fence = Map.get(record, :authority_fence)

    cond do
      incoming_fence != current_fence -> {:error, :authority_fence_transition_invalid}
      Map.get(record, :in_flight, false) == true -> :ok
      fence_state(current_record) == :released -> :ok
      true -> {:error, :authority_fence_unresolved}
    end
  end

  defp validate_put_fence(_current, %{in_flight: true, authority_fence: %{state: :armed}}), do: :ok
  defp validate_put_fence(_current, %{in_flight: true}), do: {:error, :authority_fence_unresolved}
  defp validate_put_fence(_current, _record), do: :ok

  defp preserve_boundary_binding({:ok, %{boundary_binding: %{kind: :gate2}}}, _record),
    do: {:error, :attempt_resource_verification_required}

  defp preserve_boundary_binding({:ok, %{boundary_binding: %{kind: :legacy}}}, %{boundary_binding: %{kind: :gate2}}),
    do: {:error, :attempt_resource_verification_required}

  defp preserve_boundary_binding(:not_found, %{boundary_binding: %{kind: :gate2}}),
    do: {:error, :attempt_resource_verification_required}

  defp preserve_boundary_binding({:error, reason}, _record), do: {:error, reason}

  defp preserve_boundary_binding(_current, _record), do: :ok

  defp legacy_write_allowed(ledger, issue_id) do
    case current(ledger, issue_id) do
      {:ok, %{boundary_binding: %{kind: :gate2}}} -> {:error, :attempt_resource_verification_required}
      {:ok, _record} -> :ok
      :not_found -> :ok
      {:error, reason} -> {:error, reason}
    end
  end

  @spec begin_attempt(t(), String.t()) :: {:ok, record()} | {:error, term()}
  def begin_attempt(ledger, issue_id), do: begin_attempt(ledger, issue_id, [])

  @spec begin_attempt(t(), String.t(), keyword()) :: {:ok, record()} | {:error, term()}
  def begin_attempt(%__MODULE__{} = ledger, issue_id, opts) when is_binary(issue_id) do
    with :ok <- legacy_write_allowed(ledger, issue_id) do
      case current(ledger, issue_id) do
        {:ok, %{status: :exhausted}} ->
          {:error, :lineage_exhausted}

        {:ok, %{status: :open, in_flight: true}} ->
          {:error, :attempt_in_flight}

        {:ok, %{status: :closed, close_pending: true}} ->
          {:error, :lineage_close_pending}

        {:ok, %{status: :open, safety_counters: counters}} ->
          persist_safety(ledger, issue_id, counters,
            status: :open,
            stop_reason: nil,
            route_fingerprint: Keyword.get(opts, :route_fingerprint),
            in_flight: true,
            authority_fence: %{state: :armed},
            updated_at: Keyword.get(opts, :updated_at, now_ms())
          )

        {:ok, %{status: :closed}} ->
          persist_safety(ledger, issue_id, durable_counter_defaults(),
            status: :open,
            stop_reason: nil,
            route_fingerprint: Keyword.get(opts, :route_fingerprint),
            in_flight: true,
            authority_fence: %{state: :armed},
            updated_at: Keyword.get(opts, :updated_at, now_ms())
          )

        :not_found ->
          persist_safety(ledger, issue_id, durable_counter_defaults(),
            status: :open,
            stop_reason: nil,
            route_fingerprint: Keyword.get(opts, :route_fingerprint),
            in_flight: true,
            authority_fence: %{state: :armed},
            updated_at: Keyword.get(opts, :updated_at, now_ms())
          )

        {:error, reason} ->
          {:error, reason}
      end
    end
  end

  def begin_attempt(_ledger, _issue_id, _opts), do: {:error, :invalid_attempt_arguments}

  @spec fence_attempt(t(), String.t()) :: {:ok, record()} | {:error, term()}
  def fence_attempt(ledger, issue_id), do: fence_attempt(ledger, issue_id, [])

  @spec fence_attempt(t(), String.t(), keyword()) :: {:ok, record()} | {:error, term()}
  def fence_attempt(%__MODULE__{} = ledger, issue_id, opts) when is_binary(issue_id) do
    with :ok <- legacy_write_allowed(ledger, issue_id) do
      case current(ledger, issue_id) do
        {:ok, %{status: :exhausted}} ->
          {:error, :lineage_exhausted}

        {:ok, %{status: :closed, close_pending: true}} ->
          {:error, :lineage_close_pending}

        {:ok, %{status: :open, in_flight: true}} ->
          {:error, :attempt_in_flight}

        {:ok, %{status: :open, safety_counters: counters} = record} ->
          persist_safety(ledger, issue_id, counters,
            status: :open,
            stop_reason: nil,
            route_fingerprint: Keyword.get(opts, :route_fingerprint, Map.get(record, :route_fingerprint)),
            in_flight: true,
            authority_fence: %{state: :armed},
            updated_at: Keyword.get(opts, :updated_at, now_ms())
          )

        {:ok, %{status: :closed}} ->
          persist_safety(ledger, issue_id, durable_counter_defaults(),
            status: :open,
            stop_reason: nil,
            route_fingerprint: Keyword.get(opts, :route_fingerprint),
            in_flight: true,
            authority_fence: %{state: :armed},
            updated_at: Keyword.get(opts, :updated_at, now_ms())
          )

        :not_found ->
          persist_safety(ledger, issue_id, durable_counter_defaults(),
            status: :open,
            stop_reason: nil,
            route_fingerprint: Keyword.get(opts, :route_fingerprint),
            in_flight: true,
            updated_at: Keyword.get(opts, :updated_at, now_ms())
          )

        {:error, reason} ->
          {:error, reason}
      end
    end
  end

  def fence_attempt(_ledger, _issue_id, _opts), do: {:error, :invalid_attempt_arguments}

  @spec bind_runtime_attempt(t(), String.t(), Identity.t()) :: {:ok, record()} | {:error, term()}
  def bind_runtime_attempt(%__MODULE__{} = ledger, issue_id, %Identity{} = identity) do
    with :ok <- legacy_write_allowed(ledger, issue_id),
         true <- Identity.valid?(identity) || {:error, :invalid_runtime_attempt_identity},
         {:ok, record} <- current(ledger, issue_id),
         true <- identity.work_item_id == issue_id || {:error, :runtime_attempt_identity_mismatch},
         true <- identity.lineage_generation == record.lineage_id || {:error, :runtime_attempt_identity_mismatch},
         %{state: state} <- current_fence(record),
         true <- state != :released || {:error, :authority_fence_terminal},
         true <- state == :armed || {:error, :authority_fence_transition_invalid} do
      updated =
        record
        |> Map.put(:authority_fence, %{
          state: :bound,
          runtime_attempt: identity,
          route_fingerprint: Map.get(record, :route_fingerprint)
        })
        |> Map.put(:updated_at, now_ms())

      with :ok <- validate_record(updated, ledger, issue_id, allowed_record_keys(updated)),
           :ok <- persist_records(ledger, [{{:current, issue_id}, updated}]) do
        {:ok, updated}
      end
    else
      false -> {:error, :authority_fence_transition_invalid}
      :not_found -> {:error, :lineage_not_found}
      {:error, reason} -> {:error, reason}
      _ -> {:error, :authority_fence_transition_invalid}
    end
  end

  def bind_runtime_attempt(_ledger, _issue_id, _identity), do: {:error, :invalid_runtime_attempt_identity}

  @spec release_armed_authority_fence(t(), String.t()) :: :ok | {:error, term()}
  def release_armed_authority_fence(%__MODULE__{} = ledger, issue_id) when is_binary(issue_id) do
    case legacy_write_allowed(ledger, issue_id) do
      {:error, :attempt_resource_verification_required} = error -> error
      {:error, reason} -> {:error, reason}
      :ok -> release_legacy_armed_fence(ledger, issue_id)
    end
  end

  def release_armed_authority_fence(_ledger, _issue_id), do: {:error, :invalid_attempt_arguments}

  defp release_legacy_armed_fence(ledger, issue_id) do
    case current(ledger, issue_id) do
      {:ok, %{in_flight: true, authority_fence: %{state: :armed}} = record} ->
        persist_released_fence(ledger, issue_id, record, record.authority_fence)

      {:ok, %{authority_fence: %{state: :released}}} ->
        :ok

      :not_found ->
        {:error, :lineage_not_found}

      {:error, reason} ->
        {:error, reason}

      _unresolved ->
        {:error, :authority_fence_unresolved}
    end
  end

  @spec mark_suspension_pending(t(), String.t(), Identity.t(), map()) :: {:ok, record()} | {:error, term()}
  def mark_suspension_pending(%__MODULE__{} = ledger, issue_id, %Identity{} = identity, intent)
      when is_map(intent) do
    intent = Map.put_new(intent, :suspension_id, suspension_id_for(identity))

    with :ok <- legacy_write_allowed(ledger, issue_id),
         {:ok, record} <- current(ledger, issue_id),
         fence <- current_fence(record),
         :ok <- validate_fence_identity(fence, identity, issue_id, record.lineage_id),
         :ok <- validate_suspension_intent_for_identity(intent, identity) do
      mark_suspension_pending_from_fence(ledger, issue_id, record, fence, intent)
    else
      :not_found -> {:error, :lineage_not_found}
      {:error, reason} -> {:error, reason}
    end
  end

  def mark_suspension_pending(_ledger, _issue_id, _identity, _intent), do: {:error, :invalid_suspension_intent}

  defp mark_suspension_pending_from_fence(ledger, issue_id, record, fence, intent) do
    case fence do
      %{state: :suspension_pending, intent: existing} ->
        if equivalent_suspension_intent?(existing, intent) do
          {:ok, record}
        else
          {:error, :suspension_intent_conflict}
        end

      %{state: :bound} ->
        persist_suspension_pending_fence(ledger, issue_id, record, fence, intent)

      %{state: :suspension_pending} ->
        {:error, :suspension_intent_conflict}

      _ ->
        {:error, :authority_fence_transition_invalid}
    end
  end

  @spec release_authority_fence(t(), String.t(), Identity.t()) :: :ok | {:error, term()}
  def release_authority_fence(%__MODULE__{} = ledger, issue_id, %Identity{} = identity) do
    with :ok <- legacy_write_allowed(ledger, issue_id),
         {:ok, record} <- current(ledger, issue_id),
         fence <- current_fence(record),
         :ok <- validate_fence_identity(fence, identity, issue_id, record.lineage_id),
         %{state: :bound} <- fence do
      persist_released_fence(ledger, issue_id, record, fence)
    else
      %{state: :released} -> :ok
      :not_found -> {:error, :lineage_not_found}
      {:error, reason} -> {:error, reason}
      _ -> {:error, :authority_fence_unresolved}
    end
  end

  def release_authority_fence(_ledger, _issue_id, _identity), do: {:error, :invalid_runtime_attempt_identity}

  @spec release_suspension_fence(t(), String.t(), Identity.t(), SuspensionContext.t()) :: :ok | {:error, term()}
  def release_suspension_fence(
        %__MODULE__{} = ledger,
        issue_id,
        %Identity{} = identity,
        %SuspensionContext{} = context
      ) do
    with :ok <- legacy_write_allowed(ledger, issue_id),
         {:ok, record} <- current(ledger, issue_id),
         fence <- current_fence(record),
         :ok <- validate_fence_identity(fence, identity, issue_id, record.lineage_id),
         :ok <- validate_terminal_suspension_context(context, issue_id, record.lineage_id) do
      case fence do
        %{state: :suspension_pending, intent: intent} ->
          release_pending_suspension_fence(ledger, issue_id, record, fence, identity, intent, context)

        %{state: :released} ->
          :ok

        _unresolved ->
          {:error, :suspension_context_not_terminal}
      end
    else
      :not_found -> {:error, :lineage_not_found}
      {:error, reason} -> {:error, reason}
    end
  end

  def release_suspension_fence(_ledger, _issue_id, _identity, _context), do: {:error, :suspension_context_not_terminal}

  defp release_pending_suspension_fence(ledger, issue_id, record, fence, identity, intent, context) do
    with :ok <- validate_suspension_context_correlation(identity, intent, context) do
      persist_released_fence(ledger, issue_id, record, fence)
    end
  end

  defp persist_released_fence(ledger, issue_id, record, fence) do
    released_fence = %{
      state: :released,
      runtime_attempt: Map.get(fence, :runtime_attempt),
      route_fingerprint: Map.get(fence, :route_fingerprint)
    }

    updated = Map.put(record, :authority_fence, released_fence)

    with :ok <- validate_record(updated, ledger, issue_id, allowed_record_keys(updated)) do
      persist_records(ledger, [{{:current, issue_id}, updated}])
    end
  end

  defp persist_suspension_pending_fence(ledger, issue_id, record, fence, intent) do
    updated = Map.put(record, :authority_fence, Map.merge(fence, %{state: :suspension_pending, intent: intent}))

    with :ok <- validate_record(updated, ledger, issue_id, allowed_record_keys(updated)),
         :ok <- persist_records(ledger, [{{:current, issue_id}, updated}]) do
      {:ok, updated}
    end
  end

  defp validate_fence_identity(%{runtime_attempt: current}, identity, issue_id, lineage_id) do
    if Identity.same?(current, identity) and identity.work_item_id == issue_id and
         identity.lineage_generation == lineage_id,
       do: :ok,
       else: {:error, :runtime_attempt_identity_mismatch}
  end

  defp validate_fence_identity(_fence, _identity, _issue_id, _lineage_id),
    do: {:error, :runtime_attempt_identity_mismatch}

  defp validate_suspension_intent(%{reason: reason, provider_observation: observation, required_evidence: evidence, created_at: %DateTime{}} = intent)
       when not is_nil(reason) and is_list(evidence) do
    valid_observation? = is_nil(observation) or match?(%ProviderObservation{}, observation)
    valid_evidence? = Enum.all?(evidence, &(is_atom(&1) or is_map(&1)))
    suspension_id = Map.get(intent, :suspension_id)
    valid_suspension_id? = is_nil(suspension_id) or valid_suspension_id?(suspension_id)

    if valid_observation? and valid_evidence? and valid_suspension_id?,
      do: :ok,
      else: {:error, :invalid_suspension_intent}
  end

  defp validate_suspension_intent(_intent), do: {:error, :invalid_suspension_intent}

  defp validate_suspension_intent_for_identity(intent, identity) do
    with :ok <- validate_suspension_intent(intent),
         true <- Map.get(intent, :suspension_id) == suspension_id_for(identity) do
      :ok
    else
      false -> {:error, :invalid_suspension_intent}
      {:error, reason} -> {:error, reason}
    end
  end

  defp validate_suspension_intent_for_fence(intent, identity) do
    with :ok <- validate_suspension_intent(intent) do
      validate_suspension_fence_correlation(Map.get(intent, :suspension_id), identity)
    end
  end

  defp validate_suspension_fence_correlation(nil, _identity), do: :ok

  defp validate_suspension_fence_correlation(suspension_id, identity) do
    if suspension_id == suspension_id_for(identity), do: :ok, else: {:error, :invalid_record}
  end

  defp validate_terminal_suspension_context(%SuspensionContext{} = context, issue_id, lineage_id) do
    cond do
      context.status not in [:resolved, :escalated] ->
        {:error, :suspension_context_not_terminal}

      context.work_item_id != issue_id or context.lineage_generation != lineage_id ->
        {:error, :suspension_context_mismatch}

      true ->
        :ok
    end
  end

  defp validate_suspension_context_correlation(identity, intent, context) do
    expected_id = suspension_id_for(identity)

    if valid_suspension_id?(expected_id) and Map.get(intent, :suspension_id) == expected_id and
         Map.get(context, :suspension_id) == expected_id do
      :ok
    else
      {:error, :suspension_context_mismatch}
    end
  end

  defp suspension_id_for(%Identity{runtime_attempt_id: runtime_attempt_id}) when is_binary(runtime_attempt_id) do
    :crypto.hash(:sha256, runtime_attempt_id)
    |> Base.encode16(case: :lower)
  end

  defp suspension_id_for(_identity), do: nil

  defp valid_suspension_id?(value) when is_binary(value), do: String.trim(value) != ""
  defp valid_suspension_id?(_value), do: false

  defp equivalent_suspension_intent?(left, right) do
    Map.take(left, [:reason, :provider_observation, :required_evidence, :suspension_id]) ==
      Map.take(right, [:reason, :provider_observation, :required_evidence, :suspension_id])
  end

  defp current_fence(record) do
    case Map.get(record, :authority_fence) do
      nil -> if(Map.get(record, :in_flight, false), do: %{state: :legacy_ambiguous}, else: %{state: :not_in_flight})
      fence -> fence
    end
  end

  defp fence_state(record), do: Map.get(current_fence(record), :state)

  @spec clear_in_flight(t(), String.t()) :: :ok | {:error, term()}
  def clear_in_flight(ledger, issue_id), do: clear_in_flight(ledger, issue_id, [])

  @spec clear_in_flight(t(), String.t(), keyword()) :: :ok | {:error, term()}
  def clear_in_flight(%__MODULE__{} = ledger, issue_id, opts) when is_binary(issue_id) do
    case legacy_write_allowed(ledger, issue_id) do
      {:error, :attempt_resource_verification_required} = error -> error
      {:error, reason} -> {:error, reason}
      :ok -> clear_legacy_in_flight(ledger, issue_id, opts)
    end
  end

  def clear_in_flight(_ledger, _issue_id, _opts), do: {:error, :invalid_attempt_arguments}

  defp clear_legacy_in_flight(ledger, issue_id, opts) do
    case current(ledger, issue_id) do
      :not_found ->
        :ok

      {:ok, %{status: :closed}} ->
        :ok

      {:ok, %{status: :open, in_flight: false}} ->
        :ok

      {:ok, record} ->
        clear_in_flight_record(ledger, issue_id, record, opts)

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp clear_in_flight_record(ledger, issue_id, record, opts) do
    cond do
      not Map.get(record, :in_flight, false) ->
        persist_cleared_in_flight_record(ledger, issue_id, record, opts)

      fence_state(record) != :released ->
        {:error, :authority_fence_unresolved}

      true ->
        with :ok <- sync(ledger) do
          persist_cleared_in_flight_record(ledger, issue_id, record, opts)
        end
    end
  end

  defp persist_cleared_in_flight_record(ledger, issue_id, record, opts) do
    updated =
      record
      |> Map.put(:in_flight, false)
      |> Map.put(:updated_at, Keyword.get(opts, :updated_at, now_ms()))

    with :ok <- validate_record(updated, ledger, issue_id, @base_record_keys) do
      persist_records(ledger, [{{:current, issue_id}, updated}])
    end
  end

  @spec sync(t()) :: :ok | {:error, term()}
  def sync(%__MODULE__{table: table, sync_fun: sync_fun}), do: invoke_sync(sync_fun, table)

  @spec persist_safety(t(), String.t(), map(), keyword()) :: {:ok, record()} | {:error, term()}
  def persist_safety(%__MODULE__{} = ledger, issue_id, counters, opts \\ [])
      when is_binary(issue_id) and is_map(counters) do
    status = Keyword.get(opts, :status, :open)

    existing_fence = preserved_authority_fence(current(ledger, issue_id))

    in_flight = Keyword.get(opts, :in_flight, false)
    default_fence = if in_flight, do: existing_fence || %{state: :armed}, else: existing_fence
    authority_fence = Keyword.get(opts, :authority_fence, default_fence)

    with :ok <- legacy_write_allowed(ledger, issue_id),
         :ok <- persist_status_allowed?(ledger, issue_id, status),
         {:ok, lineage_id} <- lineage_id_for(ledger, issue_id),
         {:ok, binding} <- boundary_binding_for(ledger, issue_id),
         {:ok, safety_counters} <- durable_counters(counters),
         stop_reason <- Keyword.get(opts, :stop_reason),
         record <- %{
           schema_version: ledger.schema_version,
           project_namespace: ledger.project_id,
           issue_id: issue_id,
           lineage_id: lineage_id,
           safety_counters: safety_counters,
           status: status,
           stop_reason: stop_reason,
           route_fingerprint: Keyword.get(opts, :route_fingerprint),
           in_flight: in_flight,
           authority_fence: authority_fence,
           close_pending: false,
           updated_at: Keyword.get(opts, :updated_at, now_ms())
         },
         record <- maybe_put_boundary_binding(record, ledger, binding),
         :ok <- put(ledger, record) do
      {:ok, record}
    else
      {:error, reason} -> {:error, reason}
    end
  end

  @spec close_lineage(t(), String.t(), keyword()) :: :ok | {:error, term()}
  def close_lineage(%__MODULE__{} = ledger, issue_id, opts \\ []) when is_binary(issue_id) do
    case legacy_write_allowed(ledger, issue_id) do
      {:error, :attempt_resource_verification_required} = error -> error
      {:error, reason} -> {:error, reason}
      :ok -> close_legacy_lineage(ledger, issue_id, opts)
    end
  end

  defp close_legacy_lineage(ledger, issue_id, opts) do
    case current(ledger, issue_id) do
      :not_found ->
        :ok

      {:ok, %{status: :closed, close_pending: true}} ->
        confirm_lineage_close(ledger, issue_id)

      {:ok, %{status: :closed}} ->
        :ok

      {:ok, record} ->
        close_lineage_record(ledger, issue_id, record, opts)

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp preserved_authority_fence({:ok, record}) do
    if fence_state(record) == :released or Map.get(record, :in_flight, false),
      do: current_fence(record),
      else: nil
  end

  defp preserved_authority_fence(_current), do: nil

  defp close_lineage_record(ledger, issue_id, record, opts) do
    if Map.get(record, :in_flight, false) and fence_state(record) != :released do
      {:error, :authority_fence_unresolved}
    else
      persist_close_pending_lineage(ledger, issue_id, record, opts)
    end
  end

  defp persist_close_pending_lineage(ledger, issue_id, record, opts) do
    closed_record =
      record
      |> Map.put(:status, :closed)
      |> Map.put(:closed_reason, Keyword.get(opts, :reason, :terminal))
      |> Map.put(:in_flight, false)
      |> Map.put(:close_pending, true)
      |> Map.put(:updated_at, Keyword.get(opts, :updated_at, now_ms()))

    with :ok <- validate_record(closed_record, ledger, issue_id, @history_record_keys),
         :ok <- persist_records(ledger, [{{:current, issue_id}, closed_record}]) do
      finalize_closed_lineage(ledger, issue_id, closed_record)
    end
  end

  @spec confirm_lineage_close(t(), String.t()) :: :ok | {:error, term()}
  def confirm_lineage_close(%__MODULE__{} = ledger, issue_id) when is_binary(issue_id) do
    case legacy_write_allowed(ledger, issue_id) do
      {:error, :attempt_resource_verification_required} = error -> error
      {:error, reason} -> {:error, reason}
      :ok -> confirm_legacy_lineage_close(ledger, issue_id)
    end
  end

  def confirm_lineage_close(_ledger, _issue_id), do: {:error, :invalid_attempt_arguments}

  defp confirm_legacy_lineage_close(ledger, issue_id) do
    case current(ledger, issue_id) do
      {:ok, %{status: :closed}} ->
        with :ok <- sync(ledger),
             {:ok, confirmed} <- current(ledger, issue_id) do
          finalize_confirmed_close(ledger, issue_id, confirmed)
        end

      {:ok, _record} ->
        {:error, :lineage_not_closed}

      :not_found ->
        {:error, :lineage_not_found}

      {:error, reason} ->
        {:error, reason}
    end
  end

  @spec rearm(t(), String.t(), String.t(), String.t(), non_neg_integer()) ::
          {:ok, record()} | {:error, term()}
  def rearm(%__MODULE__{} = ledger, issue_id, reason, operator, timestamp)
      when is_binary(issue_id) and is_binary(reason) and is_binary(operator) and is_integer(timestamp) and
             timestamp >= 0 do
    with :ok <- rearm_binding_allowed(ledger, issue_id),
         :ok <- validate_rearm_value(reason, :reason),
         :ok <- validate_rearm_value(operator, :operator),
         {:ok, exhausted} <- exhausted_current(ledger, issue_id) do
      old_lineage_id = exhausted.lineage_id

      history =
        exhausted
        |> Map.merge(%{
          status: :closed,
          closed_reason: :rearmed,
          close_pending: false,
          rearm_reason: String.trim(reason),
          rearmed_by: String.trim(operator),
          rearmed_at: timestamp,
          updated_at: timestamp
        })

      new_record =
        exhausted
        |> Map.take(@base_record_keys)
        |> Map.merge(%{
          schema_version: ledger.schema_version,
          project_namespace: ledger.project_id,
          issue_id: issue_id,
          lineage_id: new_lineage_id(),
          safety_counters: durable_counter_defaults(),
          status: :open,
          stop_reason: nil,
          route_fingerprint: nil,
          in_flight: false,
          authority_fence: nil,
          updated_at: timestamp
        })
        |> maybe_put_boundary_binding(ledger, Map.get(exhausted, :boundary_binding, %{kind: :legacy}))

      with :ok <- validate_record(history, ledger, issue_id, @history_record_keys),
           :ok <- validate_record(new_record, ledger, issue_id, @base_record_keys),
           :ok <-
             persist_records(ledger, [
               {{:history, old_lineage_id}, history},
               {{:current, issue_id}, new_record}
             ]) do
        {:ok,
         new_record
         |> Map.put(:rearm_reason, String.trim(reason))
         |> Map.put(:rearmed_by, String.trim(operator))
         |> Map.put(:rearmed_at, timestamp)}
      end
    else
      {:error, reason} -> {:error, reason}
    end
  end

  def rearm(_ledger, _issue_id, _reason, _operator, _timestamp), do: {:error, :invalid_rearm_arguments}

  defp rearm_binding_allowed(ledger, issue_id) do
    case current(ledger, issue_id) do
      {:ok, %{boundary_binding: %{kind: :gate2}}} -> {:error, :gate2_boundary_required}
      {:ok, _record} -> :ok
      :not_found -> :ok
      {:error, reason} -> {:error, reason}
    end
  end

  defp build_ledger(table, path, project_id, tracker_identity, opts) do
    write_fun = Keyword.get(opts, :write_fun, &:dets.insert/2)
    sync_fun = Keyword.get(opts, :sync_fun, &:dets.sync/1)

    stored_schema =
      case :dets.lookup(table, {:meta, project_id}) do
        [{{:meta, ^project_id}, %{schema_version: version}}] when version in [1, 2] -> version
        _ -> 1
      end

    if is_function(write_fun, 2) and is_function(sync_fun, 1) do
      {:ok,
       %__MODULE__{
         table: table,
         path: path,
         project_id: project_id,
         tracker_identity: tracker_identity,
         schema_version: stored_schema,
         write_fun: write_fun,
         sync_fun: sync_fun
       }}
    else
      {:error, :invalid_ledger_callbacks}
    end
  end

  defp initialize_or_validate(%__MODULE__{} = ledger) do
    with {:ok, records} <- all_records(ledger) do
      initialize_records(records, ledger)
    end
  end

  defp initialize_records([], %__MODULE__{} = ledger) do
    persist_records(ledger, [{{:meta, ledger.project_id}, metadata(ledger)}])
  end

  defp initialize_records(records, %__MODULE__{} = ledger) do
    case metadata_record(records) do
      {:ok, metadata} ->
        case validate_metadata(metadata, ledger) do
          :ok -> validate_stored_records(records, ledger)
          {:error, reason} -> {:error, reason}
        end

      {:error, :missing_metadata} ->
        {:error, {:corrupt_attempt_record, :metadata, :missing_metadata}}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp metadata_record(records) do
    metadata = Enum.filter(records, &match?({{:meta, _project_id}, _metadata}, &1))

    case metadata do
      [] -> {:error, :missing_metadata}
      [{key, value}] -> {:ok, {key, value}}
      _ -> {:error, {:corrupt_attempt_record, :metadata, :invalid_record}}
    end
  end

  defp validate_metadata({{:meta, project_id}, metadata}, ledger) when is_binary(project_id) and is_map(metadata) do
    cond do
      project_id != ledger.project_id ->
        {:error, {:ledger_project_namespace_mismatch, project_id, ledger.project_id}}

      Map.keys(metadata) |> Enum.sort() != [:project_namespace, :schema_version, :tracker_identity] ->
        {:error, {:corrupt_attempt_record, :metadata, :invalid_record}}

      true ->
        validate_metadata_values(metadata, ledger)
    end
  end

  defp validate_metadata(_metadata, _ledger), do: {:error, {:corrupt_attempt_record, :metadata, :invalid_record}}

  defp validate_metadata_values(metadata, ledger) do
    with :ok <- validate_schema_version(Map.get(metadata, :schema_version)),
         :ok <- validate_project_namespace(Map.get(metadata, :project_namespace), ledger.project_id),
         :ok <- validate_tracker_identity(Map.get(metadata, :tracker_identity)) do
      validate_tracker_identity_match(metadata.tracker_identity, ledger.tracker_identity)
    end
  end

  defp validate_tracker_identity_match(stored, expected) when stored == expected, do: :ok

  defp validate_tracker_identity_match(stored, expected),
    do: {:error, {:ledger_tracker_identity_mismatch, stored, expected}}

  defp validate_stored_records(records, ledger) do
    Enum.reduce_while(records, :ok, fn
      {{:meta, _project_id}, _metadata}, :ok ->
        {:cont, :ok}

      {{:current, issue_id}, record}, :ok ->
        case validate_record(record, ledger, issue_id, allowed_record_keys(record)) do
          :ok ->
            {:cont, :ok}

          {:error, {:ledger_schema_version_unsupported, version}} ->
            {:halt, {:error, {:ledger_schema_version_unsupported, version}}}

          {:error, reason} ->
            {:halt, {:error, {:corrupt_attempt_record, {:current, issue_id}, reason}}}
        end

      {{:history, lineage_id}, record}, :ok ->
        case validate_record(record, ledger, record_issue_id(record), @history_record_keys) do
          :ok when record.lineage_id == lineage_id ->
            {:cont, :ok}

          :ok ->
            {:halt, {:error, {:corrupt_attempt_record, {:history, lineage_id}, :invalid_record}}}

          {:error, {:ledger_schema_version_unsupported, version}} ->
            {:halt, {:error, {:ledger_schema_version_unsupported, version}}}

          {:error, reason} ->
            {:halt, {:error, {:corrupt_attempt_record, {:history, lineage_id}, reason}}}
        end

      {key, _record}, :ok ->
        {:halt, {:error, {:corrupt_attempt_record, key, :invalid_record}}}
    end)
  end

  defp allowed_record_keys(record) when is_map(record) do
    if Map.get(record, :status) == :closed, do: @history_record_keys, else: @base_record_keys
  end

  defp allowed_record_keys(_record), do: @base_record_keys

  defp record_issue_id(%{issue_id: issue_id}), do: issue_id
  defp record_issue_id(_record), do: nil

  defp validate_record(record, ledger, issue_id, allowed_keys)
       when is_map(record) and is_binary(issue_id) do
    with :ok <- validate_record_keys(record, allowed_keys),
         {:ok, in_flight, close_pending} <- fetch_safety_fields(record),
         :ok <- validate_schema_version(Map.get(record, :schema_version)),
         :ok <- validate_record_schema_and_binding(record, ledger),
         :ok <- validate_project_namespace(Map.get(record, :project_namespace), ledger.project_id),
         :ok <- validate_non_empty_string(Map.get(record, :issue_id), :issue_id),
         :ok <- validate_non_empty_string(Map.get(record, :lineage_id), :lineage_id),
         :ok <- validate_counters(Map.get(record, :safety_counters)),
         :ok <- validate_status(Map.get(record, :status)),
         :ok <- validate_stop_reason(Map.get(record, :stop_reason)),
         :ok <- validate_route_fingerprint(Map.get(record, :route_fingerprint)),
         :ok <- validate_gate2_fence_binding(record, ledger),
         :ok <- validate_in_flight(in_flight),
         :ok <- validate_close_pending(close_pending),
         :ok <- validate_authority_fence(Map.get(record, :authority_fence), in_flight),
         :ok <- validate_timestamp(Map.get(record, :updated_at)) do
      if record.issue_id != issue_id do
        {:error, :invalid_record}
      else
        validate_safety_state(record)
      end
    end
  end

  defp validate_record(_record, _ledger, _issue_id, _allowed_keys), do: {:error, :invalid_record}

  defp validate_gate2_fence_binding(record, ledger) do
    fence = Map.get(record, :authority_fence)

    if is_map(fence) and Map.has_key?(fence, :gate2_fence),
      do: validate_gate2_binding_record(Map.get(record, :boundary_binding), Map.get(fence, :gate2_fence), ledger),
      else: :ok
  end

  defp validate_gate2_binding_record(
         %{kind: :gate2, resource_ledger_namespace: namespace},
         gate2,
         ledger
       )
       when namespace == ledger.project_id do
    valid? =
      is_map(gate2) and valid_requested_reason?(gate2) and
        valid_gate2_reference?(Map.get(gate2, :reference))

    if valid?, do: :ok, else: {:error, :invalid_record}
  end

  defp validate_gate2_binding_record(_binding, _gate2, _ledger), do: {:error, :invalid_record}

  defp validate_record_keys(record, allowed_keys) do
    valid? = Enum.all?(Map.keys(record), fn key -> key in allowed_keys or (key == :boundary_binding and Map.get(record, :schema_version) == 2) end)
    if valid?, do: :ok, else: {:error, :invalid_record}
  end

  defp fetch_safety_fields(record) do
    with {:ok, in_flight} <- Map.fetch(record, :in_flight),
         {:ok, close_pending} <- Map.fetch(record, :close_pending) do
      {:ok, in_flight, close_pending}
    else
      _ -> {:error, :invalid_record}
    end
  end

  defp validate_schema_version(version) when version in [1, 2], do: :ok
  defp validate_schema_version(version), do: {:error, {:ledger_schema_version_unsupported, version}}

  defp validate_record_schema_and_binding(%{schema_version: 1}, %{schema_version: 1}), do: :ok
  defp validate_record_schema_and_binding(%{schema_version: 2, boundary_binding: %{kind: :legacy} = binding}, %{schema_version: 2}) when map_size(binding) == 1, do: :ok

  defp validate_record_schema_and_binding(
         %{
           schema_version: 2,
           boundary_binding:
             %{kind: :gate2, binding_version: 1, lineage_binding_id: id, resource_ledger_namespace: namespace} =
               binding
         },
         %{schema_version: 2}
       )
       when map_size(binding) == 4 and is_binary(id) and byte_size(id) in 1..128 and
              is_binary(namespace) and byte_size(namespace) in 1..128 do
    if String.trim(id) == id and id != "" and String.trim(namespace) == namespace and namespace != "",
      do: :ok,
      else: {:error, :invalid_record}
  end

  defp validate_record_schema_and_binding(_, _), do: {:error, :invalid_record}

  defp boundary_binding_for(%{schema_version: 1}, _issue_id), do: {:ok, nil}

  defp boundary_binding_for(ledger, issue_id) do
    case current(ledger, issue_id) do
      {:ok, record} -> {:ok, Map.get(record, :boundary_binding, %{kind: :legacy})}
      :not_found -> {:ok, %{kind: :legacy}}
      {:error, reason} -> {:error, reason}
    end
  end

  defp maybe_put_boundary_binding(record, %{schema_version: 2}, binding), do: Map.put(record, :boundary_binding, binding)
  defp maybe_put_boundary_binding(record, _ledger, _binding), do: record

  defp validate_project_namespace(project_id, project_id) when is_binary(project_id), do: :ok
  defp validate_project_namespace(_stored, _expected), do: {:error, :invalid_record}

  defp validate_project_id(project_id) do
    if Schema.valid_project_id?(project_id), do: :ok, else: {:error, {:invalid_symphony_project_id, project_id}}
  end

  defp validate_tracker_identity(identity) when is_map(identity) do
    cond do
      Enum.sort(Map.keys(identity)) != Enum.sort(@allowed_identity_keys) ->
        {:error, :invalid_tracker_identity}

      not is_binary(identity.tracker_kind) or String.trim(identity.tracker_kind) == "" ->
        {:error, :invalid_tracker_identity}

      not valid_scope?(identity.provider_scope) ->
        {:error, :invalid_tracker_identity}

      true ->
        :ok
    end
  end

  defp validate_tracker_identity(_identity), do: {:error, :invalid_tracker_identity}

  defp valid_scope?(scope) when is_map(scope) do
    Enum.all?(scope, fn {key, value} ->
      key in @allowed_scope_keys and is_binary(value) and String.trim(value) != ""
    end)
  end

  defp valid_scope?(_scope), do: false

  defp validate_counters(counters) when is_map(counters) do
    if Enum.sort(Map.keys(counters)) == Enum.sort(@durable_counter_keys) and
         Enum.all?(counters, fn {_key, value} -> is_integer(value) and value >= 0 end) do
      :ok
    else
      {:error, :invalid_record}
    end
  end

  defp validate_counters(_counters), do: {:error, :invalid_record}

  defp validate_status(status) when status in [:open, :exhausted, :closed], do: :ok
  defp validate_status(_status), do: {:error, :invalid_record}

  defp validate_stop_reason(nil), do: :ok
  defp validate_stop_reason(reason) when is_atom(reason), do: :ok
  defp validate_stop_reason(_reason), do: {:error, :invalid_record}

  defp validate_route_fingerprint(nil), do: :ok
  defp validate_route_fingerprint(value) when is_binary(value), do: :ok
  defp validate_route_fingerprint(_value), do: {:error, :invalid_record}

  defp validate_timestamp(timestamp) when is_integer(timestamp) and timestamp >= 0, do: :ok
  defp validate_timestamp(_timestamp), do: {:error, :invalid_record}

  defp validate_in_flight(value) when is_boolean(value), do: :ok
  defp validate_in_flight(_value), do: {:error, :invalid_record}

  defp validate_close_pending(value) when is_boolean(value), do: :ok
  defp validate_close_pending(_value), do: {:error, :invalid_record}

  defp validate_authority_fence(nil, true), do: :ok
  defp validate_authority_fence(nil, false), do: :ok
  defp validate_authority_fence(%{state: :armed}, true), do: :ok

  defp validate_authority_fence(%{state: :bound, runtime_attempt: %Identity{}, route_fingerprint: route} = fence, true)
       when is_binary(route) or is_nil(route) do
    case Map.get(fence, :gate2_fence) do
      nil ->
        :ok

      %{reference: reference, status: :requested} = gate2 when map_size(gate2) in [2, 3] ->
        valid_reason = Map.get(gate2, :requested_reason) in [nil, :completion, :cancellation, :failure, :restart, :publication]

        if valid_gate2_reference?(reference) and valid_reason, do: :ok, else: {:error, :invalid_record}

      _ ->
        {:error, :invalid_record}
    end
  end

  defp validate_authority_fence(
         %{
           state: :suspension_pending,
           runtime_attempt: %Identity{} = identity,
           route_fingerprint: route,
           intent: intent
         },
         true
       )
       when is_binary(route) or is_nil(route) do
    validate_suspension_intent_for_fence(intent, identity)
  end

  defp validate_authority_fence(%{state: :released} = fence, in_flight) when is_boolean(in_flight) do
    if Map.get(fence, :runtime_attempt) == nil or match?(%Identity{}, Map.get(fence, :runtime_attempt)), do: :ok, else: {:error, :invalid_record}
  end

  defp validate_authority_fence(%{state: :legacy_ambiguous}, true), do: :ok
  defp validate_authority_fence(_fence, _in_flight), do: {:error, :invalid_record}

  defp valid_gate2_reference?(
         %{
           grant_id: grant_id,
           project_namespace: namespace,
           runtime_identity: identity,
           fence_epoch: epoch,
           grant_sha256: digest
         } = reference
       ) do
    expected = [:grant_id, :project_namespace, :runtime_identity, :fence_epoch, :grant_sha256]

    Enum.sort(Map.keys(reference)) == Enum.sort(expected) and id?(grant_id) and id?(namespace) and
      strict_gate2_identity?(identity) and is_integer(epoch) and epoch > 0 and digest?(digest)
  end

  defp valid_gate2_reference?(_), do: false

  defp valid_requested_reason?(%{status: :requested} = gate2) do
    Enum.sort(Map.keys(gate2)) in [[:reference, :status], [:reference, :requested_reason, :status]] and
      Map.get(gate2, :requested_reason) in [nil, :completion, :cancellation, :failure, :restart, :publication]
  end

  defp valid_requested_reason?(_), do: false

  @spec strict_gate2_identity?(term()) :: boolean()
  defp strict_gate2_identity?(%Identity{} = identity) do
    expected = [:runtime_attempt_id, :work_item_id, :lineage_generation, :responsibility, :runtime_profile]

    Enum.sort(Map.keys(identity)) == Enum.sort([:__struct__ | expected]) and
      Enum.all?(expected, fn field -> id?(Map.get(identity, field)) end)
  end

  defp strict_gate2_identity?(_), do: false

  defp id?(value), do: is_binary(value) and byte_size(value) in 1..256 and String.trim(value) != ""
  defp digest?(value), do: is_binary(value) and Regex.match?(~r/\A[a-f0-9]{64}\z/, value)

  defp normalize_gate2_error(:ledger_project_namespace_mismatch), do: :namespace_mismatch
  defp normalize_gate2_error(:corrupt_attempt_record), do: :storage_corrupt
  defp normalize_gate2_error({:ledger_write_failed, _}), do: :write_failed
  defp normalize_gate2_error({:ledger_sync_failed, _}), do: :sync_failed
  defp normalize_gate2_error({:ledger_read_failed, _}), do: :storage_unavailable
  defp normalize_gate2_error(_), do: :storage_corrupt

  defp validate_safety_state(%{status: status} = record) do
    if Map.get(record, :close_pending, false) and status != :closed do
      {:error, :invalid_record}
    else
      case status do
        :open -> validate_open_safety_state(record)
        :exhausted -> validate_exhausted_safety_state(record)
        :closed -> validate_closed_safety_state(record)
        _ -> {:error, :invalid_record}
      end
    end
  end

  defp validate_open_safety_state(%{safety_counters: counters, stop_reason: nil}),
    do: safety_state_result(open_counters?(counters))

  defp validate_open_safety_state(_record), do: {:error, :invalid_record}

  defp validate_exhausted_safety_state(%{safety_counters: counters, stop_reason: stop_reason} = record) do
    safety_state_result(not Map.get(record, :in_flight, false) and exhausted_counters?(counters, stop_reason))
  end

  defp validate_exhausted_safety_state(_record), do: {:error, :invalid_record}

  defp validate_closed_safety_state(%{safety_counters: counters, stop_reason: stop_reason} = record) do
    safety_state_result(not Map.get(record, :in_flight, false) and closed_counters?(counters, stop_reason))
  end

  defp validate_closed_safety_state(_record), do: {:error, :invalid_record}

  defp safety_state_result(true), do: :ok
  defp safety_state_result(false), do: {:error, :invalid_record}

  defp open_counters?(%{
         ordinary_failures: ordinary_failures,
         ordinary_retries: ordinary_retries,
         review_cycles: review_cycles
       }) do
    ordinary_failures in 0..AttemptPolicy.max_ordinary_retries() and
      ordinary_retries == ordinary_failures and
      review_cycles in 0..AttemptPolicy.max_review_cycles()
  end

  defp open_counters?(_counters), do: false

  defp exhausted_counters?(counters, :ordinary_retry_limit) do
    review_cycles_valid?(counters) and
      counters.ordinary_failures == AttemptPolicy.max_ordinary_retries() + 1 and
      counters.ordinary_retries == AttemptPolicy.max_ordinary_retries()
  end

  defp exhausted_counters?(counters, :review_cycle_limit) do
    ordinary_counters_open?(counters) and
      counters.review_cycles == AttemptPolicy.max_review_cycles()
  end

  defp exhausted_counters?(counters, :ci_retry_disabled), do: open_counters?(counters)
  defp exhausted_counters?(_counters, _reason), do: false

  defp closed_counters?(counters, nil), do: open_counters?(counters)
  defp closed_counters?(counters, stop_reason), do: exhausted_counters?(counters, stop_reason)

  defp ordinary_counters_open?(%{ordinary_failures: ordinary_failures, ordinary_retries: ordinary_retries}) do
    ordinary_failures in 0..AttemptPolicy.max_ordinary_retries() and
      ordinary_retries == ordinary_failures
  end

  defp ordinary_counters_open?(_counters), do: false

  defp review_cycles_valid?(%{review_cycles: review_cycles}),
    do: review_cycles in 0..AttemptPolicy.max_review_cycles()

  defp review_cycles_valid?(_counters), do: false

  defp validate_non_empty_string(value, _field) when is_binary(value) do
    if String.trim(value) == "", do: {:error, :invalid_record}, else: :ok
  end

  defp validate_non_empty_string(_value, _field), do: {:error, :invalid_record}

  defp lineage_id_for(ledger, issue_id) do
    case current(ledger, issue_id) do
      {:ok, %{lineage_id: lineage_id, status: status}} when status in [:open, :exhausted] ->
        {:ok, lineage_id}

      :not_found ->
        {:ok, new_lineage_id()}

      {:ok, _closed} ->
        {:ok, new_lineage_id()}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp persist_status_allowed?(ledger, issue_id, status) do
    case current(ledger, issue_id) do
      {:ok, %{status: :closed, close_pending: true}} -> {:error, :lineage_close_pending}
      {:ok, %{status: :exhausted}} when status != :exhausted -> {:error, :lineage_exhausted}
      {:error, reason} -> {:error, reason}
      _ -> :ok
    end
  end

  defp durable_counters(counters) do
    if Enum.all?(@durable_counter_keys, &(is_integer(Map.get(counters, &1)) and Map.get(counters, &1) >= 0)) do
      {:ok, Map.take(counters, @durable_counter_keys)}
    else
      {:error, :invalid_safety_counters}
    end
  end

  defp durable_counter_defaults, do: Map.take(AttemptPolicy.new(), @durable_counter_keys)

  defp exhausted_current(ledger, issue_id) do
    case current(ledger, issue_id) do
      {:ok, %{status: :exhausted} = record} -> {:ok, record}
      {:ok, _record} -> {:error, :lineage_not_exhausted}
      :not_found -> {:error, :lineage_not_found}
      {:error, reason} -> {:error, reason}
    end
  end

  defp validate_rearm_value(value, _field) do
    if String.trim(value) == "", do: {:error, :invalid_rearm_arguments}, else: :ok
  end

  defp finalize_closed_lineage(%__MODULE__{} = ledger, issue_id, record) do
    finalized_record = Map.put(record, :close_pending, false)

    with :ok <- validate_record(finalized_record, ledger, issue_id, @history_record_keys) do
      persist_records(ledger, [{{:current, issue_id}, finalized_record}])
    end
  end

  defp finalize_confirmed_close(%__MODULE__{} = ledger, issue_id, record) do
    if Map.get(record, :close_pending, false) do
      finalize_closed_lineage(ledger, issue_id, record)
    else
      :ok
    end
  end

  defp persist_records(%__MODULE__{table: table, write_fun: write_fun, sync_fun: sync_fun}, records) do
    case invoke_write(write_fun, table, records) do
      :ok -> invoke_sync(sync_fun, table)
      {:error, _reason} = error -> error
    end
  end

  defp invoke_write(write_fun, table, records) do
    case write_fun.(table, records) do
      :ok -> :ok
      {:error, reason} -> {:error, {:ledger_write_failed, reason}}
      other -> {:error, {:ledger_write_failed, other}}
    end
  rescue
    error -> {:error, {:ledger_write_failed, error}}
  catch
    kind, reason -> {:error, {:ledger_write_failed, {kind, reason}}}
  end

  defp invoke_sync(sync_fun, table) do
    case sync_fun.(table) do
      :ok -> :ok
      {:error, reason} -> {:error, {:ledger_sync_failed, reason}}
      other -> {:error, {:ledger_sync_failed, other}}
    end
  rescue
    error -> {:error, {:ledger_sync_failed, error}}
  catch
    kind, reason -> {:error, {:ledger_sync_failed, {kind, reason}}}
  end

  defp all_records(%__MODULE__{table: table}) do
    {:ok, :dets.foldl(fn record, records -> [record | records] end, [], table)}
  catch
    kind, reason -> {:error, {:ledger_read_failed, {kind, reason}}}
  end

  defp safe_lookup(table, key) do
    {:ok, :dets.lookup(table, key)}
  catch
    kind, reason -> {:error, {:ledger_read_failed, {kind, reason}}}
  end

  defp open_table(path) do
    table = path

    case :dets.open_file(table, type: :set, file: String.to_charlist(path), auto_save: :infinity) do
      {:ok, ^table} ->
        case File.chmod(path, 0o600) do
          :ok ->
            {:ok, table}

          {:error, reason} ->
            _ = close_table(table)
            {:error, {:ledger_permissions_failed, reason}}
        end

      {:error, {:already_started, _pid}} ->
        {:error, {:ledger_already_open, path}}

      {:error, reason} ->
        {:error, {:ledger_open_failed, reason}}
    end
  end

  defp close_table(table) do
    case :dets.info(table) do
      :undefined -> :ok
      _ -> :dets.close(table)
    end
  catch
    :exit, reason -> {:error, {:ledger_close_failed, reason}}
  end

  defp ensure_parent_directory(path), do: path |> Path.dirname() |> File.mkdir_p()

  defp metadata(%__MODULE__{} = ledger) do
    %{
      schema_version: ledger.schema_version,
      project_namespace: ledger.project_id,
      tracker_identity: ledger.tracker_identity
    }
  end

  defp default_root do
    state_root = System.get_env("XDG_STATE_HOME") || Path.join(System.user_home!(), ".local/state")
    Path.join(state_root, "symphony/attempt-ledger")
  end

  defp new_lineage_id do
    "lineage-" <> Base.encode16(:crypto.strong_rand_bytes(16), case: :lower)
  end

  defp now_ms, do: System.system_time(:millisecond)
end
