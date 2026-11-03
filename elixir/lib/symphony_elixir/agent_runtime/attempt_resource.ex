defmodule SymphonyElixir.AgentRuntime.AttemptResource do
  @moduledoc false

  alias SymphonyElixir.AgentRuntime.QuarantineDisposition
  alias SymphonyElixir.AgentRuntime.RecoveryGeneration
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  @type class ::
          :workspace
          | :home
          | :xdg_config
          | :xdg_state
          | :xdg_data
          | :cache
          | :runtime_tmp
          | :provider_private
          | :process_scope
          | :mount_scope
          | :network_scope
          | :materialization
          | :candidate_stage
  @type state ::
          :reserved
          | :allocating
          | :allocated
          | :active
          | :fencing
          | :fenced
          | :destroying
          | :absent_verified
          | :cleanup_unverified
          | :quarantined
  @type t :: %__MODULE__{
          schema_version: 1,
          resource_id: String.t(),
          project_namespace: String.t(),
          grant_id: String.t(),
          runtime_identity: Identity.t(),
          class: class(),
          state: state(),
          revision: non_neg_integer(),
          stable_locator: String.t(),
          allocation_identity_sha256: String.t() | nil,
          capacity_profile_sha256: String.t(),
          owner_host_id: String.t(),
          creation_generation: RecoveryGeneration.t(),
          reconciliation_generation: RecoveryGeneration.t(),
          last_evidence_ref: String.t() | nil,
          quarantine: QuarantineDisposition.t()
        }

  defstruct [
    :schema_version,
    :resource_id,
    :project_namespace,
    :grant_id,
    :runtime_identity,
    :class,
    :state,
    :revision,
    :stable_locator,
    :allocation_identity_sha256,
    :capacity_profile_sha256,
    :owner_host_id,
    :creation_generation,
    :reconciliation_generation,
    :last_evidence_ref,
    :quarantine
  ]

  @fields [
    :schema_version,
    :resource_id,
    :project_namespace,
    :grant_id,
    :runtime_identity,
    :class,
    :state,
    :revision,
    :stable_locator,
    :allocation_identity_sha256,
    :capacity_profile_sha256,
    :owner_host_id,
    :creation_generation,
    :reconciliation_generation,
    :last_evidence_ref,
    :quarantine
  ]
  @classes [
    :workspace,
    :home,
    :xdg_config,
    :xdg_state,
    :xdg_data,
    :cache,
    :runtime_tmp,
    :provider_private,
    :process_scope,
    :mount_scope,
    :network_scope,
    :materialization,
    :candidate_stage
  ]
  @states [
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

  @spec new(map()) :: {:ok, t()} | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def new(attrs) when is_map(attrs) do
    with true <- Enum.sort(Map.keys(attrs)) == Enum.sort(@fields),
         1 <- Map.get(attrs, :schema_version),
         true <- id?(Map.get(attrs, :resource_id)),
         true <- id?(Map.get(attrs, :project_namespace)),
         true <- id?(Map.get(attrs, :grant_id)),
         %Identity{} = identity <- Map.get(attrs, :runtime_identity),
         true <- identity?(identity),
         class when class in @classes <- Map.get(attrs, :class),
         state when state in @states <- Map.get(attrs, :state),
         revision when is_integer(revision) and revision >= 0 <- Map.get(attrs, :revision),
         true <- id?(Map.get(attrs, :stable_locator)),
         true <- optional_digest?(Map.get(attrs, :allocation_identity_sha256)),
         true <- digest?(Map.get(attrs, :capacity_profile_sha256)),
         true <- id?(Map.get(attrs, :owner_host_id)),
         {:ok, creation} <- nested_generation(Map.get(attrs, :creation_generation)),
         {:ok, reconciliation} <- nested_generation(Map.get(attrs, :reconciliation_generation)),
         true <- optional_id?(Map.get(attrs, :last_evidence_ref)),
         {:ok, quarantine} <- nested_quarantine(Map.get(attrs, :quarantine)) do
      normalized = %{
        attrs
        | creation_generation: creation,
          reconciliation_generation: reconciliation,
          quarantine: quarantine
      }

      {:ok, struct(__MODULE__, normalized)}
    else
      _ -> {:error, :invalid_request}
    end
  end

  def new(_attrs), do: {:error, :invalid_request}

  defp nested_generation(%RecoveryGeneration{} = value) do
    if exact_struct?(value, RecoveryGeneration),
      do: RecoveryGeneration.new(Map.from_struct(value)),
      else: {:error, :invalid_request}
  end

  defp nested_generation(value) when is_map(value), do: RecoveryGeneration.new(value)
  defp nested_generation(_value), do: {:error, :invalid_request}

  defp nested_quarantine(%QuarantineDisposition{} = value) do
    if exact_struct?(value, QuarantineDisposition),
      do: QuarantineDisposition.new(Map.from_struct(value)),
      else: {:error, :invalid_request}
  end

  defp nested_quarantine(value) when is_map(value), do: QuarantineDisposition.new(value)
  defp nested_quarantine(_value), do: {:error, :invalid_request}

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
  defp optional_id?(nil), do: true
  defp optional_id?(value), do: id?(value)
  defp digest?(value), do: is_binary(value) and Regex.match?(~r/\A[a-f0-9]{64}\z/, value)
  defp optional_digest?(nil), do: true
  defp optional_digest?(value), do: digest?(value)
end
