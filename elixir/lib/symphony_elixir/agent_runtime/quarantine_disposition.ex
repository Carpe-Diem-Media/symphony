defmodule SymphonyElixir.AgentRuntime.QuarantineDisposition do
  @moduledoc false

  alias SymphonyElixir.AgentRuntime.RecoveryGeneration

  @type state ::
          :clear
          | :quarantined
          | :block_reuse
          | :operator_resolution_pending
          | :released_for_new_authorization
          | :remains_quarantined
  @type t :: %__MODULE__{
          state: state(),
          reason: SymphonyElixir.AgentRuntime.AttemptBoundary.reason() | nil,
          evidence_ref: String.t() | nil,
          generation: RecoveryGeneration.t(),
          resolution_ref: String.t() | nil
        }

  defstruct [:state, :reason, :evidence_ref, :generation, :resolution_ref]

  @states [
    :clear,
    :quarantined,
    :block_reuse,
    :operator_resolution_pending,
    :released_for_new_authorization,
    :remains_quarantined
  ]
  @reasons [
    :owner_unknown,
    :identity_conflict,
    :stale_generation,
    :fence_unverified,
    :cleanup_unverified,
    :possible_disclosure,
    :storage_uncertain,
    :external_effect_ambiguous,
    :operator_resolution_required
  ]

  @spec new(map()) :: {:ok, t()} | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def new(attrs) when is_map(attrs) do
    with true <-
           Enum.sort(Map.keys(attrs)) ==
             Enum.sort([:state, :reason, :evidence_ref, :generation, :resolution_ref]),
         state when state in @states <- Map.get(attrs, :state),
         reason when is_nil(reason) or reason in @reasons <- Map.get(attrs, :reason),
         true <- optional_id?(Map.get(attrs, :evidence_ref)),
         {:ok, generation} <- nested_generation(Map.get(attrs, :generation)),
         true <- optional_id?(Map.get(attrs, :resolution_ref)) do
      {:ok, struct(__MODULE__, %{attrs | generation: generation})}
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
  defp optional_id?(nil), do: true
  defp optional_id?(value), do: is_binary(value) and byte_size(value) in 1..256 and String.trim(value) != ""

  defp exact_struct?(value, module) do
    expected = [:__struct__ | module.__struct__() |> Map.from_struct() |> Map.keys()]
    Enum.sort(Map.keys(value)) == Enum.sort(expected)
  end
end
