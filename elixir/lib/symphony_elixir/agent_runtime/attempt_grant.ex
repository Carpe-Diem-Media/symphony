defmodule SymphonyElixir.AgentRuntime.AttemptGrant do
  @moduledoc false

  alias SymphonyElixir.AgentRuntime.RecoveryGeneration
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  @type operation ::
          :workspace_read
          | :workspace_write
          | :tool_execute
          | :model_request
          | :plane_read
          | :plane_transition
          | :source_control_read

  @type t :: %__MODULE__{
          schema_version: 1,
          grant_id: String.t(),
          project_namespace: String.t(),
          tracker_identity_sha256: String.t(),
          runtime_identity: Identity.t(),
          recovery_generation: RecoveryGeneration.t(),
          route_fingerprint: String.t(),
          subscription_registration_id: String.t(),
          credential_generation: pos_integer(),
          workspace_resource_id: String.t(),
          source_admission_policy_sha256: String.t(),
          process_policy_sha256: String.t(),
          network_policy_sha256: String.t(),
          tool_policy_sha256: String.t(),
          capacity_profile_sha256: String.t(),
          allowed_operations: [operation()],
          fence_epoch: pos_integer()
        }

  @type ref :: %{
          grant_id: String.t(),
          project_namespace: String.t(),
          runtime_identity: Identity.t(),
          fence_epoch: pos_integer(),
          grant_sha256: String.t()
        }

  defstruct [
    :schema_version,
    :grant_id,
    :project_namespace,
    :tracker_identity_sha256,
    :runtime_identity,
    :recovery_generation,
    :route_fingerprint,
    :subscription_registration_id,
    :credential_generation,
    :workspace_resource_id,
    :source_admission_policy_sha256,
    :process_policy_sha256,
    :network_policy_sha256,
    :tool_policy_sha256,
    :capacity_profile_sha256,
    :allowed_operations,
    :fence_epoch
  ]

  @fields [
    :schema_version,
    :grant_id,
    :project_namespace,
    :tracker_identity_sha256,
    :runtime_identity,
    :recovery_generation,
    :route_fingerprint,
    :subscription_registration_id,
    :credential_generation,
    :workspace_resource_id,
    :source_admission_policy_sha256,
    :process_policy_sha256,
    :network_policy_sha256,
    :tool_policy_sha256,
    :capacity_profile_sha256,
    :allowed_operations,
    :fence_epoch
  ]
  @operations [
    :workspace_read,
    :workspace_write,
    :tool_execute,
    :model_request,
    :plane_read,
    :plane_transition,
    :source_control_read
  ]

  @spec new(map()) :: {:ok, t()} | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def new(attrs) when is_map(attrs) do
    with :ok <- fields(attrs),
         1 <- Map.get(attrs, :schema_version),
         true <- id?(Map.get(attrs, :grant_id)),
         true <- id?(Map.get(attrs, :project_namespace)),
         true <- digest?(Map.get(attrs, :tracker_identity_sha256)),
         %Identity{} = identity <- Map.get(attrs, :runtime_identity),
         true <- identity?(identity),
         {:ok, generation} <- nested_generation(Map.get(attrs, :recovery_generation)),
         true <- id?(Map.get(attrs, :route_fingerprint)),
         true <- id?(Map.get(attrs, :subscription_registration_id)),
         credential when is_integer(credential) and credential > 0 <- Map.get(attrs, :credential_generation),
         true <- id?(Map.get(attrs, :workspace_resource_id)),
         true <- digest?(Map.get(attrs, :source_admission_policy_sha256)),
         true <- digest?(Map.get(attrs, :process_policy_sha256)),
         true <- digest?(Map.get(attrs, :network_policy_sha256)),
         true <- digest?(Map.get(attrs, :tool_policy_sha256)),
         true <- digest?(Map.get(attrs, :capacity_profile_sha256)),
         operations when is_list(operations) <- Map.get(attrs, :allowed_operations),
         true <- valid_operations?(operations),
         epoch when is_integer(epoch) and epoch > 0 <- Map.get(attrs, :fence_epoch) do
      {:ok, struct(__MODULE__, %{attrs | recovery_generation: generation})}
    else
      _ -> {:error, :invalid_request}
    end
  end

  def new(_attrs), do: {:error, :invalid_request}

  @spec reference(t()) :: ref()
  def reference(%__MODULE__{} = grant) do
    canonical = {
      grant.schema_version,
      grant.grant_id,
      grant.project_namespace,
      grant.tracker_identity_sha256,
      identity_tuple(grant.runtime_identity),
      generation_tuple(grant.recovery_generation),
      grant.route_fingerprint,
      grant.subscription_registration_id,
      grant.credential_generation,
      grant.workspace_resource_id,
      grant.source_admission_policy_sha256,
      grant.process_policy_sha256,
      grant.network_policy_sha256,
      grant.tool_policy_sha256,
      grant.capacity_profile_sha256,
      grant.allowed_operations,
      grant.fence_epoch
    }

    %{
      grant_id: grant.grant_id,
      project_namespace: grant.project_namespace,
      runtime_identity: grant.runtime_identity,
      fence_epoch: grant.fence_epoch,
      grant_sha256:
        :crypto.hash(:sha256, :erlang.term_to_binary(canonical, [:deterministic]))
        |> Base.encode16(case: :lower)
    }
  end

  defp fields(attrs), do: if(Enum.sort(Map.keys(attrs)) == Enum.sort(@fields), do: :ok, else: :error)

  defp valid_operations?(operations) do
    operations != [] and Enum.all?(operations, &(&1 in @operations)) and
      length(Enum.uniq(operations)) == length(operations)
  end

  defp nested_generation(%RecoveryGeneration{} = value) do
    if exact_struct?(value, RecoveryGeneration),
      do: RecoveryGeneration.new(Map.from_struct(value)),
      else: {:error, :invalid_request}
  end

  defp nested_generation(value) when is_map(value), do: RecoveryGeneration.new(value)
  defp nested_generation(_value), do: {:error, :invalid_request}

  defp identity?(identity) do
    if is_struct(identity, Identity) do
      expected = [:runtime_attempt_id, :work_item_id, :lineage_generation, :responsibility, :runtime_profile]

      exact_struct?(identity, Identity) and
        Enum.all?(expected, fn field ->
          value = Map.get(identity, field)
          is_binary(value) and byte_size(value) in 1..256 and String.trim(value) != ""
        end)
    else
      false
    end
  end

  defp exact_struct?(value, module) do
    expected = [:__struct__ | module.__struct__() |> Map.from_struct() |> Map.keys()]
    Enum.sort(Map.keys(value)) == Enum.sort(expected)
  end

  defp id?(value), do: is_binary(value) and byte_size(value) in 1..256 and String.trim(value) != ""
  defp digest?(value), do: is_binary(value) and Regex.match?(~r/\A[a-f0-9]{64}\z/, value)

  defp identity_tuple(%Identity{} = identity) do
    List.to_tuple([
      identity.runtime_attempt_id,
      identity.work_item_id,
      identity.lineage_generation,
      identity.responsibility,
      identity.runtime_profile
    ])
  end

  defp generation_tuple(%RecoveryGeneration{} = generation),
    do:
      List.to_tuple([
        generation.schema_version,
        generation.project_namespace,
        generation.host_id,
        generation.boot_id,
        generation.sequence,
        generation.nonce
      ])
end
