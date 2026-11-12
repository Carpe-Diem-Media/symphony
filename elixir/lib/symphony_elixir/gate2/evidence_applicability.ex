defmodule SymphonyElixir.Gate2.EvidenceApplicability do
  @moduledoc """
  Reproducible characterization of supplied, nonsecret evidence bytes.

  This pure component has no filesystem, process, provider or acceptance access.
  Its explicit UTC cutoff must be supplied by the assessment caller. Time fields
  and provenance remain untrusted declarations, even after byte verification.
  A matching artifact is never equivalent to a verified claim-specific proof.
  Claim labels and the assessment catalog do not authenticate applicability.
  Relabeling or repeating bytes leaves applicability and acceptance unverified.
  Operational host/configuration and independent-review verification refuse.
  """

  alias SymphonyElixir.Gate2.QualificationIdentity

  @fields ~w(claim_id proof_class identity observed_at expires_at scope sha256 bytes)
  @max_artifact_bytes 1_048_576
  @max_timestamp 9_223_372_036_854_775_807

  @doc "Defensive artifact input ceiling only; this is not an operational capacity grant."
  @spec max_artifact_bytes() :: pos_integer()
  def max_artifact_bytes, do: @max_artifact_bytes

  @doc "Bounds UTC-second declarations to a nonnegative signed 64-bit representation."
  @spec valid_timestamp?(term()) :: boolean()
  def valid_timestamp?(value), do: is_integer(value) and value >= 0 and value <= @max_timestamp

  @doc "Checks closed, bounded input shape only; verifies neither artifact bytes nor claims."
  @spec valid_envelope?(term()) :: boolean()
  def valid_envelope?(record) when is_map(record) and map_size(record) == length(@fields) do
    Enum.all?(@fields, &Map.has_key?(record, &1)) and valid_labels?(record) and
      valid_payload?(record) and valid_interval?(record) and
      match?({:ok, _}, QualificationIdentity.new(record["identity"]))
  end

  def valid_envelope?(_record), do: false

  @spec evaluate(term(), term(), term()) :: map()
  def evaluate(record, identity, as_of) do
    status = disposition(record, identity, as_of)

    %{
      "status" => status,
      "artifact_integrity" => if(status == "CHARACTERIZED", do: "VERIFIED_BYTES", else: "UNVERIFIED"),
      "claim_applicability" => "UNVERIFIED",
      "evidence_catalog_binding" => "UNVERIFIED",
      "proof_status" => "UNVERIFIED",
      "independent_acceptance" => "UNVERIFIED",
      "reason" => if(status == "CHARACTERIZED", do: "PROOF_VERIFIER_UNCONFIGURED", else: status),
      "evidence_sha256" => safe_digest(record),
      "observed_at" => safe_time(record, "observed_at"),
      "expires_at" => safe_time(record, "expires_at")
    }
  end

  defp disposition(record, identity, as_of) do
    cond do
      not valid_record?(record, as_of) -> "INVALID"
      not QualificationIdentity.valid?(identity) -> "INVALID"
      record["identity"] != identity.bindings -> "IDENTITY_MISMATCH"
      record["scope"] != "DEVELOPMENT_COMPONENT" -> "UNSUPPORTED"
      record["observed_at"] > as_of -> "FUTURE"
      record["expires_at"] <= as_of -> "STALE"
      digest(record["bytes"]) != record["sha256"] -> "INTEGRITY_MISMATCH"
      true -> "CHARACTERIZED"
    end
  end

  defp valid_record?(record, as_of), do: valid_timestamp?(as_of) and valid_envelope?(record)

  defp valid_labels?(record) do
    bounded_binary?(record["claim_id"], 6) and bounded_binary?(record["proof_class"], 32) and
      bounded_binary?(record["scope"], 64)
  end

  defp bounded_binary?(value, limit), do: is_binary(value) and byte_size(value) <= limit

  defp valid_payload?(record) do
    is_binary(record["bytes"]) and byte_size(record["bytes"]) <= @max_artifact_bytes and
      valid_digest?(record["sha256"])
  end

  defp valid_interval?(record) do
    valid_timestamp?(record["observed_at"]) and valid_timestamp?(record["expires_at"]) and
      record["expires_at"] > record["observed_at"]
  end

  defp safe_digest(record) when is_map(record) do
    if valid_digest?(record["sha256"]), do: record["sha256"], else: nil
  end

  defp safe_digest(_record), do: nil

  defp safe_time(record, field) when is_map(record) do
    value = record[field]
    if valid_timestamp?(value), do: value, else: nil
  end

  defp safe_time(_record, _field), do: nil
  defp valid_digest?(value) when is_binary(value), do: byte_size(value) == 64 and Regex.match?(~r/\A[0-9a-f]{64}\z/, value)
  defp valid_digest?(_value), do: false
  defp digest(bytes), do: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower)
end
