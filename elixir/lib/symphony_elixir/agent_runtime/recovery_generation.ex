defmodule SymphonyElixir.AgentRuntime.RecoveryGeneration do
  @moduledoc """
  Host-bound recovery epoch metadata.

  `boot_id` identifies the host boot, not the lifetime of an OTP process. Sequence
  and nonce distinguish successive recoveries on the same boot. Construction
  validates stored metadata shape; authoritative current boot identity is read
  separately by the resource ledger before admission.
  """

  @type t :: %__MODULE__{
          schema_version: 1,
          project_namespace: String.t(),
          host_id: String.t(),
          boot_id: String.t(),
          sequence: pos_integer(),
          nonce: String.t()
        }

  defstruct [:schema_version, :project_namespace, :host_id, :boot_id, :sequence, :nonce]

  @fields [:schema_version, :project_namespace, :host_id, :boot_id, :sequence, :nonce]
  @uuid ~r/\A[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}\z/

  @spec new(map()) :: {:ok, t()} | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def new(attrs) when is_map(attrs) do
    with :ok <- fields(attrs, @fields),
         1 <- Map.get(attrs, :schema_version),
         true <- id?(Map.get(attrs, :project_namespace)),
         true <- id?(Map.get(attrs, :host_id)),
         true <- id?(Map.get(attrs, :boot_id)),
         sequence when is_integer(sequence) and sequence > 0 <- Map.get(attrs, :sequence),
         true <- id?(Map.get(attrs, :nonce)) do
      {:ok, struct(__MODULE__, attrs)}
    else
      _ -> {:error, :invalid_request}
    end
  end

  def new(_attrs), do: {:error, :invalid_request}

  @doc "Checks Linux boot UUID syntax; this predicate does not establish provenance."
  @spec valid_boot_id?(term()) :: boolean()
  def valid_boot_id?(value), do: is_binary(value) and Regex.match?(@uuid, value)

  defp fields(attrs, allowed) do
    keys = Map.keys(attrs)
    if Enum.sort(keys) == Enum.sort(allowed), do: :ok, else: :error
  end

  defp id?(value), do: is_binary(value) and byte_size(value) in 1..256 and String.trim(value) != ""
end
