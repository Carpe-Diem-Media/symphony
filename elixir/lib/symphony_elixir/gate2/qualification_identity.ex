defmodule SymphonyElixir.Gate2.QualificationIdentity do
  @moduledoc """
  Exact, closed component binding for a dormant P09 assessment.

  Host/platform/configuration values identify measured records by digest. They do
  not assert those records are supported or qualified. No wildcard, omitted
  component, version label or caller-supplied acceptance flag is permitted.
  """

  @fields ~w(candidate_sha source_tree_sha upstream_sha patch_sha256 runtime_binary_sha256
    helper_sha256 scanner_sha256 kernel_sha256 lsm_sha256 nftables_sha256 storage_sha256
    crypto_sha256 configuration_sha256 policy_sha256 capacity_profile_sha256 host_profile_sha256)
  @enforce_keys [:bindings, :digest]
  defstruct [:bindings, :digest]

  @type t :: %__MODULE__{bindings: map(), digest: String.t()}

  @spec fields() :: [String.t()]
  def fields, do: @fields

  @doc "Validates all bindings and hashes the fixed, ordered field/value pairs."
  @spec new(term()) :: {:ok, t()} | {:error, :invalid_qualification_identity}
  def new(attrs) when is_map(attrs) and map_size(attrs) == length(@fields) do
    if Enum.all?(@fields, &valid_hash?(attrs[&1], &1)) do
      digest = @fields |> Enum.map(&[&1, attrs[&1]]) |> Jason.encode!() |> then(&:crypto.hash(:sha256, &1))
      {:ok, %__MODULE__{bindings: attrs, digest: Base.encode16(digest, case: :lower)}}
    else
      {:error, :invalid_qualification_identity}
    end
  end

  def new(_attrs), do: {:error, :invalid_qualification_identity}

  @doc "Revalidates a constructed identity, including its digest, at every assessment boundary."
  @spec valid?(term()) :: boolean()
  def valid?(%__MODULE__{bindings: bindings} = identity), do: new(bindings) == {:ok, identity}
  def valid?(_identity), do: false

  defp valid_hash?(value, field) when is_binary(value) do
    size = if String.ends_with?(field, "_sha"), do: 40, else: 64
    byte_size(value) == size and Regex.match?(~r/\A[0-9a-f]+\z/, value)
  end

  defp valid_hash?(_value, _field), do: false
end
