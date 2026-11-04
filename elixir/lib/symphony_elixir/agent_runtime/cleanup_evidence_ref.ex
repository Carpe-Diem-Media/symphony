defmodule SymphonyElixir.AgentRuntime.CleanupEvidenceRef do
  @moduledoc false

  alias SymphonyElixir.AgentRuntime.RecoveryGeneration
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  @type t :: %__MODULE__{
          schema_version: 1,
          evidence_id: String.t(),
          evidence_sha256: String.t(),
          project_namespace: String.t(),
          grant_id: String.t(),
          runtime_identity: Identity.t(),
          fence_epoch: pos_integer(),
          resource_set_sha256: String.t(),
          verification_generation: RecoveryGeneration.t(),
          verifier_implementation_sha256: String.t()
        }

  defstruct [
    :schema_version,
    :evidence_id,
    :evidence_sha256,
    :project_namespace,
    :grant_id,
    :runtime_identity,
    :fence_epoch,
    :resource_set_sha256,
    :verification_generation,
    :verifier_implementation_sha256
  ]

  @fields [
    :schema_version,
    :evidence_id,
    :evidence_sha256,
    :project_namespace,
    :grant_id,
    :runtime_identity,
    :fence_epoch,
    :resource_set_sha256,
    :verification_generation,
    :verifier_implementation_sha256
  ]

  @spec new(map()) :: {:ok, t()} | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def new(attrs) when is_map(attrs) do
    with true <- Enum.sort(Map.keys(attrs)) == Enum.sort(@fields),
         1 <- Map.get(attrs, :schema_version),
         true <- id?(Map.get(attrs, :evidence_id)),
         true <- digest?(Map.get(attrs, :evidence_sha256)),
         true <- id?(Map.get(attrs, :project_namespace)),
         true <- id?(Map.get(attrs, :grant_id)),
         %Identity{} = identity <- Map.get(attrs, :runtime_identity),
         true <- identity?(identity),
         epoch when is_integer(epoch) and epoch > 0 <- Map.get(attrs, :fence_epoch),
         true <- digest?(Map.get(attrs, :resource_set_sha256)),
         {:ok, generation} <- nested_generation(Map.get(attrs, :verification_generation)),
         true <- digest?(Map.get(attrs, :verifier_implementation_sha256)) do
      {:ok, struct(__MODULE__, %{attrs | verification_generation: generation})}
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
end
