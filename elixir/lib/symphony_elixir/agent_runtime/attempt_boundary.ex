defmodule SymphonyElixir.AgentRuntime.AttemptBoundary do
  @moduledoc """
  Dormant Gate 2 coordinator. It records no active authority and cannot verify cleanup.
  """

  use GenServer

  alias SymphonyElixir.AgentRuntime.{AttemptGrant, AttemptLedger, AttemptResourceLedger, CleanupEvidenceRef}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  @type reason ::
          :owner_unknown
          | :identity_conflict
          | :stale_generation
          | :fence_unverified
          | :cleanup_unverified
          | :possible_disclosure
          | :storage_uncertain
          | :external_effect_ambiguous
          | :operator_resolution_required

  @type error ::
          :invalid_request
          | :unauthorized_caller
          | :boundary_unavailable
          | :gate2_dormant
          | :gate2_profile_incomplete
          | :namespace_mismatch
          | :identity_mismatch
          | :route_mismatch
          | :recovery_generation_mismatch
          | :stale_grant
          | :grant_not_found
          | :grant_not_active
          | :operation_denied
          | :permit_conflict
          | :resource_conflict
          | :resource_not_found
          | :revision_conflict
          | :transition_invalid
          | :binding_downgrade_denied
          | :gate2_boundary_required
          | :attempt_resource_verification_required
          | :quarantined
          | :ownership_ambiguous
          | :cleanup_verifier_unavailable
          | :cleanup_reference_missing
          | :cleanup_reference_invalid
          | :cleanup_reference_stale
          | :cleanup_resource_set_mismatch
          | :cleanup_not_verified
          | :external_effect_unresolved
          | :storage_unavailable
          | :storage_corrupt
          | :write_failed
          | :sync_failed
          | :migration_required
          | :migration_in_progress
          | :migration_lock_unavailable
          | :ledger_in_use
          | :migration_source_invalid
          | :migration_target_invalid
          | :migration_commit_uncertain
          | :migration_not_permitted
          | :unsupported_schema
          | :schema_mismatch

  @type authorization_request :: %{
          route_fingerprint: String.t(),
          subscription_registration_id: String.t(),
          credential_generation: pos_integer(),
          source_admission_policy_sha256: String.t(),
          process_policy_sha256: String.t(),
          network_policy_sha256: String.t(),
          tool_policy_sha256: String.t(),
          capacity_profile_sha256: String.t()
        }
  @type operation_request :: %{
          operation_id: String.t(),
          operation: AttemptGrant.operation(),
          resource_id: String.t() | nil,
          arguments_sha256: String.t()
        }
  @type operation_permit :: %{
          permit_id: String.t(),
          grant_ref: AttemptGrant.ref(),
          operation_id: String.t(),
          operation: AttemptGrant.operation(),
          resource_id: String.t() | nil,
          fence_epoch: pos_integer()
        }
  @type fence_request :: %{
          required(:grant_ref) => AttemptGrant.ref(),
          required(:reason) => :completion | :cancellation | :failure | :restart | :publication
        }
  @type fence_ref :: %{grant_ref: AttemptGrant.ref(), fence_epoch: pos_integer(), status: :requested | :verified, evidence_ref: String.t() | nil}

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts) when is_list(opts) do
    owner_name = Keyword.get(opts, :owner_name)

    case if(Keyword.has_key?(opts, :captured_owner_pid), do: {:error, :invalid_request}, else: valid_options(opts)) do
      :ok when is_atom(owner_name) ->
        owner_pid = self()

        if Process.whereis(owner_name) == owner_pid do
          GenServer.start_link(__MODULE__, Keyword.put(opts, :captured_owner_pid, owner_pid), name: __MODULE__)
        else
          {:error, :unauthorized_caller}
        end

      _ ->
        {:error, :invalid_request}
    end
  end

  def start_link(_), do: {:error, :invalid_request}

  @spec authorize(GenServer.server(), Identity.t(), authorization_request()) :: {:ok, AttemptGrant.t()} | {:error, error()}
  def authorize(server, identity, request), do: call(server, {:authorize, identity, request})

  @spec reserve_resource_sync(GenServer.server(), SymphonyElixir.AgentRuntime.AttemptResource.t()) ::
          {:ok, SymphonyElixir.AgentRuntime.AttemptResource.t()} | {:error, error()}
  def reserve_resource_sync(server, resource), do: call(server, {:reserve_resource, resource})

  @doc false
  @spec bind_gate2_fence_sync(SymphonyElixir.AgentRuntime.AttemptLedger.t(), String.t(), AttemptGrant.ref()) ::
          :ok | {:error, error()}
  def bind_gate2_fence_sync(ledger, issue_id, reference) do
    case Process.whereis(__MODULE__) do
      pid when is_pid(pid) -> call(pid, {:bind_gate2_fence, ledger, issue_id, reference})
      _ -> {:error, :gate2_boundary_required}
    end
  end

  @doc false
  @spec release_gate2_authority_fence(
          AttemptLedger.t(),
          String.t(),
          Identity.t(),
          CleanupEvidenceRef.t()
        ) :: :ok | {:error, error()}
  def release_gate2_authority_fence(ledger, issue_id, identity, evidence) do
    case Process.whereis(__MODULE__) do
      pid when is_pid(pid) -> call(pid, {:release_gate2_fence, ledger, issue_id, identity, evidence})
      _ -> {:error, :gate2_boundary_required}
    end
  end

  @spec authorize_operation(GenServer.server(), AttemptGrant.ref(), operation_request()) :: {:ok, operation_permit()} | {:error, error()}
  def authorize_operation(server, reference, request), do: call(server, {:authorize_operation, reference, request})

  @spec fence(GenServer.server(), fence_request()) :: {:ok, fence_ref()} | {:error, error()}
  def fence(server, request), do: call(server, {:fence, request})

  @spec reconcile_startup(GenServer.server()) ::
          {:ok, SymphonyElixir.AgentRuntime.RecoveryGeneration.t()} | {:error, error()}
  def reconcile_startup(server), do: call(server, :reconcile_startup)

  @spec release(GenServer.server(), CleanupEvidenceRef.t() | nil) :: :ok | {:error, error()}
  def release(server, reference), do: call(server, {:release, reference})

  @impl true
  def init(opts) do
    with :ok <- valid_options(opts),
         owner_name when is_atom(owner_name) <- Keyword.get(opts, :owner_name),
         owner_pid when is_pid(owner_pid) <- Keyword.get(opts, :captured_owner_pid),
         true <- Process.whereis(owner_name) == owner_pid,
         resource_options when is_list(resource_options) <- Keyword.get(opts, :resource_ledger_opts),
         true <- Process.whereis(__MODULE__) == self() do
      resource_options =
        resource_options
        |> Keyword.put(:owner_name, __MODULE__)
        |> Keyword.put(:recovery_owner_name, __MODULE__)
        |> Keyword.put(:startup_recovery, true)
        |> Keyword.delete(:current_generation)

      case AttemptResourceLedger.start_link(resource_options) do
        {:ok, ledger} ->
          {:ok, generation} = AttemptResourceLedger.current_generation(ledger)
          owner_ref = Process.monitor(owner_pid)

          {:ok,
           %{
             owner_name: owner_name,
             owner_pid: owner_pid,
             owner_epoch: {owner_pid, generation},
             owner_ref: owner_ref,
             ledger: ledger,
             attempt_ledger: Keyword.get(opts, :attempt_ledger),
             recovery_generation: generation,
             blocked: false
           }}

        {:error, reason} ->
          {:stop, reason}
      end
    else
      _ -> {:stop, :invalid_request}
    end
  end

  @impl true
  def handle_call(request, {caller, _tag}, state) do
    {owner_pid, generation} = state.owner_epoch

    case caller_status(caller, owner_pid, state, generation) do
      :ok -> check_current_generation(request, state, generation)
      {:error, reason} -> {:reply, {:error, reason}, state}
    end
  end

  defp caller_status(caller, owner_pid, state, generation) do
    cond do
      caller != owner_pid or Process.whereis(state.owner_name) != owner_pid or state.owner_pid != owner_pid ->
        {:error, :unauthorized_caller}

      state.recovery_generation != generation ->
        {:error, :recovery_generation_mismatch}

      state.blocked ->
        {:error, :storage_unavailable}

      true ->
        :ok
    end
  end

  defp check_current_generation(request, state, generation) do
    case AttemptResourceLedger.current_generation(state.ledger) do
      {:ok, ^generation} -> guarded_reply(request, state)
      {:ok, _other_generation} -> {:reply, {:error, :recovery_generation_mismatch}, state}
      {:error, reason} -> {:reply, {:error, reason}, %{state | blocked: true}}
    end
  end

  @impl true
  def handle_info({:DOWN, ref, :process, pid, _reason}, %{owner_ref: ref, owner_pid: pid} = state),
    do: {:stop, :normal, state}

  def handle_info(_message, state), do: {:noreply, state}

  defp guarded_reply(request, state) do
    case reply(request, state) do
      {:reply, {:error, reason} = error, next_state}
      when reason in [:storage_unavailable, :storage_corrupt, :write_failed, :sync_failed] ->
        {:reply, error, %{next_state | blocked: true}}

      result ->
        result
    end
  end

  defp reply({:authorize, %Identity{} = identity, request}, state) do
    reply_authorization_request(Identity.valid?(identity) and valid_authorization_request?(request), state)
  end

  defp reply({:authorize_operation, reference, request}, state) do
    valid_request? = valid_reference?(reference) and valid_operation_request?(request)
    reply_authorization_request(valid_request?, state)
  end

  defp reply({:reserve_resource, %SymphonyElixir.AgentRuntime.AttemptResource{} = resource}, state) do
    if resource.reconciliation_generation == state.recovery_generation do
      case AttemptResourceLedger.reserve_sync(state.ledger, resource) do
        {:error, reason} = error when reason in [:write_failed, :sync_failed, :storage_unavailable] ->
          {:reply, error, %{state | blocked: true}}

        result ->
          {:reply, result, state}
      end
    else
      {:reply, {:error, :recovery_generation_mismatch}, state}
    end
  end

  defp reply({:reserve_resource, _}, state), do: {:reply, {:error, :invalid_request}, state}

  defp reply({:bind_gate2_fence, ledger, issue_id, reference}, state) do
    cond do
      ledger != state.attempt_ledger -> {:reply, {:error, :gate2_boundary_required}, state}
      not is_binary(issue_id) or not valid_reference?(reference) -> {:reply, {:error, :invalid_request}, state}
      true -> bind_validated_fence(ledger, issue_id, reference, state)
    end
  end

  defp reply({:release_gate2_fence, ledger, issue_id, %Identity{} = identity, %CleanupEvidenceRef{} = evidence}, state) do
    if ledger == state.attempt_ledger and is_binary(issue_id) and Identity.valid?(identity) do
      validate_gate2_release(ledger, issue_id, identity, evidence, state)
    else
      {:reply, {:error, :gate2_boundary_required}, state}
    end
  end

  defp reply({:fence, request}, state) when is_map(request) do
    if valid_fence_request?(request) do
      request_fence(request, state)
    else
      {:reply, {:error, :invalid_request}, state}
    end
  end

  defp reply({:fence, _}, state), do: {:reply, {:error, :invalid_request}, state}

  defp reply(:reconcile_startup, state), do: {:reply, {:ok, state.recovery_generation}, state}
  defp reply({:release, nil}, state), do: {:reply, {:error, :cleanup_reference_missing}, state}

  defp reply({:release, %CleanupEvidenceRef{} = reference}, state) do
    case CleanupEvidenceRef.new(Map.from_struct(reference)) do
      {:ok, ^reference} ->
        resolve_cleanup_reference(reference, state)

      _ ->
        {:reply, {:error, :cleanup_reference_invalid}, state}
    end
  end

  defp reply({:release, _}, state), do: {:reply, {:error, :cleanup_reference_invalid}, state}
  defp reply(_, state), do: {:reply, {:error, :invalid_request}, state}

  defp reply_authorization_request(true, state), do: {:reply, {:error, :gate2_dormant}, state}
  defp reply_authorization_request(false, state), do: {:reply, {:error, :invalid_request}, state}

  defp bind_validated_fence(ledger, issue_id, reference, state) do
    case matching_resources(reference, state) do
      :ok ->
        result = AttemptLedger.bind_gate2_fence_from_boundary(ledger, issue_id, reference)
        storage_guarded_result(result, state)

      {:error, reason} ->
        {:reply, {:error, reason}, state}
    end
  end

  defp storage_guarded_result({:error, reason} = error, state)
       when reason in [:write_failed, :sync_failed, :storage_unavailable],
       do: {:reply, error, %{state | blocked: true}}

  defp storage_guarded_result(result, state), do: {:reply, result, state}

  defp validate_gate2_release(ledger, issue_id, identity, evidence, state) do
    case CleanupEvidenceRef.new(Map.from_struct(evidence)) do
      {:ok, ^evidence} -> resolve_gate2_release(ledger, issue_id, identity, evidence, state)
      _ -> {:reply, {:error, :cleanup_reference_invalid}, state}
    end
  end

  defp resolve_gate2_release(ledger, issue_id, identity, evidence, state) do
    case AttemptLedger.gate2_fence_reference(ledger, issue_id) do
      {:ok, reference} -> gate2_release_result(reference, identity, evidence, state)
      {:error, reason} -> {:reply, {:error, reason}, state}
      _ -> {:reply, {:error, :cleanup_reference_stale}, state}
    end
  end

  defp gate2_release_result(reference, identity, evidence, state) do
    matches_evidence? =
      reference.grant_id == evidence.grant_id and
        reference.project_namespace == evidence.project_namespace and
        reference.runtime_identity == identity and identity == evidence.runtime_identity and
        reference.fence_epoch == evidence.fence_epoch

    if matches_evidence?,
      do: {:reply, {:error, :attempt_resource_verification_required}, state},
      else: {:reply, {:error, :cleanup_reference_stale}, state}
  end

  defp valid_fence_request?(request) do
    has_expected_keys? = Enum.sort(Map.keys(request)) == [:grant_ref, :reason]
    valid_reason? = Map.get(request, :reason) in [:completion, :cancellation, :failure, :restart, :publication]
    has_expected_keys? and valid_reason? and valid_reference?(request.grant_ref)
  end

  defp request_fence(request, state) do
    case resolve_reference(request.grant_ref, state) do
      {:ok, grant} -> persist_fence_request(request, grant, state)
      error -> {:reply, error, state}
    end
  end

  defp persist_fence_request(request, grant, state) do
    result = persist_requested_fence(request, state)

    case result do
      :ok ->
        fence = %{grant_ref: request.grant_ref, fence_epoch: grant.fence_epoch, status: :requested, evidence_ref: nil}
        {:reply, {:ok, fence}, state}

      {:error, reason} = error when reason in [:write_failed, :sync_failed, :storage_unavailable] ->
        {:reply, error, %{state | blocked: true}}

      error ->
        {:reply, error, state}
    end
  end

  defp persist_requested_fence(request, state) do
    AttemptLedger.request_gate2_fence_from_boundary(
      state.attempt_ledger,
      request.grant_ref.runtime_identity.work_item_id,
      request.grant_ref,
      request.reason
    )
  end

  defp resolve_cleanup_reference(
         reference,
         %{attempt_ledger: %AttemptLedger{} = ledger} = state
       ) do
    case AttemptLedger.gate2_fence_reference(ledger, reference.runtime_identity.work_item_id) do
      {:ok, grant_ref} ->
        resolve_cleanup_grant(reference, grant_ref, state)

      :not_found ->
        {:reply, {:error, :cleanup_reference_stale}, state}

      {:error, reason} ->
        {:reply, {:error, reason}, state}
    end
  end

  defp resolve_cleanup_reference(_reference, state), do: {:reply, {:error, :cleanup_reference_stale}, state}

  defp resolve_cleanup_grant(reference, grant_ref, state) do
    cond do
      not same_cleanup_grant?(reference, grant_ref) ->
        {:reply, {:error, :cleanup_reference_stale}, state}

      reference.verification_generation != state.recovery_generation ->
        {:reply, {:error, :cleanup_reference_stale}, state}

      true ->
        cleanup_resources_result(matching_resources(grant_ref, state), state)
    end
  end

  defp same_cleanup_grant?(reference, grant_ref) do
    grant_ref.grant_id == reference.grant_id and grant_ref.project_namespace == reference.project_namespace and
      grant_ref.runtime_identity == reference.runtime_identity and grant_ref.fence_epoch == reference.fence_epoch
  end

  defp cleanup_resources_result(:ok, state), do: {:reply, {:error, :cleanup_verifier_unavailable}, state}
  defp cleanup_resources_result({:error, :ownership_ambiguous}, state), do: {:reply, {:error, :cleanup_resource_set_mismatch}, state}

  defp cleanup_resources_result({:error, reason}, state)
       when reason in [:storage_unavailable, :storage_corrupt, :write_failed, :sync_failed],
       do: {:reply, {:error, reason}, state}

  defp cleanup_resources_result(_result, state), do: {:reply, {:error, :cleanup_reference_stale}, state}

  defp resolve_reference(reference, state) do
    with true <- valid_reference?(reference),
         %AttemptLedger{} = attempt_ledger <- state.attempt_ledger,
         {:ok, ^reference} <-
           AttemptLedger.gate2_fence_reference(
             attempt_ledger,
             reference.runtime_identity.work_item_id
           ),
         :ok <- matching_resources(reference, state) do
      {:ok, %{fence_epoch: reference.fence_epoch}}
    else
      false when is_map(reference) -> {:error, :grant_not_found}
      {:error, reason} -> {:error, reason}
      _ -> {:error, :grant_not_found}
    end
  end

  defp matching_resources(reference, state) do
    case AttemptResourceLedger.list_for_grant(state.ledger, reference.grant_id) do
      {:ok, []} ->
        {:error, :grant_not_found}

      {:ok, resources} ->
        if Enum.all?(resources, &matching_resource?(&1, reference, state)),
          do: :ok,
          else: {:error, :ownership_ambiguous}

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp matching_resource?(resource, reference, state) do
    resource.project_namespace == reference.project_namespace and
      resource.runtime_identity == reference.runtime_identity and
      resource.reconciliation_generation == state.recovery_generation and resource.state == :reserved
  end

  defp valid_reference?(%{grant_id: id, project_namespace: namespace, runtime_identity: %Identity{} = identity, fence_epoch: epoch, grant_sha256: digest} = reference) do
    Enum.sort(Map.keys(reference)) == [:fence_epoch, :grant_id, :grant_sha256, :project_namespace, :runtime_identity] and
      valid_id?(id) and valid_id?(namespace) and strict_identity?(identity) and is_integer(epoch) and epoch > 0 and
      is_binary(digest) and Regex.match?(~r/\A[a-f0-9]{64}\z/, digest)
  end

  defp valid_reference?(_), do: false

  defp strict_identity?(identity) do
    expected = [:runtime_attempt_id, :work_item_id, :lineage_generation, :responsibility, :runtime_profile]

    is_struct(identity, Identity) and
      Enum.sort(Map.keys(identity)) == Enum.sort([:__struct__ | expected]) and
      Enum.all?(expected, fn key -> valid_id?(Map.get(identity, key)) end)
  end

  defp valid_authorization_request?(request) when is_map(request) do
    expected = [
      :route_fingerprint,
      :subscription_registration_id,
      :credential_generation,
      :source_admission_policy_sha256,
      :process_policy_sha256,
      :network_policy_sha256,
      :tool_policy_sha256,
      :capacity_profile_sha256
    ]

    Enum.sort(Map.keys(request)) == Enum.sort(expected) and valid_id?(request.route_fingerprint) and
      valid_id?(request.subscription_registration_id) and is_integer(request.credential_generation) and
      request.credential_generation > 0 and
      Enum.all?(
        expected -- [:route_fingerprint, :subscription_registration_id, :credential_generation],
        &(is_binary(Map.fetch!(request, &1)) and Regex.match?(~r/\A[a-f0-9]{64}\z/, Map.fetch!(request, &1)))
      )
  end

  defp valid_authorization_request?(_), do: false

  defp valid_operation_request?(request) when is_map(request) do
    expected = [:operation_id, :operation, :resource_id, :arguments_sha256]

    Enum.sort(Map.keys(request)) == Enum.sort(expected) and valid_id?(request.operation_id) and
      valid_operation?(request.operation) and
      (is_nil(request.resource_id) or valid_id?(request.resource_id)) and
      is_binary(request.arguments_sha256) and Regex.match?(~r/\A[a-f0-9]{64}\z/, request.arguments_sha256)
  end

  defp valid_operation_request?(_), do: false

  defp valid_operation?(operation) do
    operation in [
      :workspace_read,
      :workspace_write,
      :tool_execute,
      :model_request,
      :plane_read,
      :plane_transition,
      :source_control_read
    ]
  end

  defp valid_options(opts) do
    if valid_option_keys?(opts) and required_options?(opts),
      do: :ok,
      else: {:error, :invalid_request}
  end

  defp valid_option_keys?(opts) do
    allowed = [:owner_name, :resource_ledger_opts, :attempt_ledger, :captured_owner_pid]
    Keyword.keyword?(opts) and Enum.all?(Keyword.keys(opts), &(&1 in allowed))
  end

  defp required_options?(opts) do
    Keyword.has_key?(opts, :owner_name) and Keyword.has_key?(opts, :resource_ledger_opts)
  end

  defp valid_id?(value), do: is_binary(value) and byte_size(value) in 1..256 and String.trim(value) != ""

  defp call(server, request) do
    GenServer.call(server, request, 5_000)
  catch
    :exit, _ -> {:error, :boundary_unavailable}
  end
end
