defmodule SymphonyElixir.Gate2.ImplementationProof do
  @moduledoc """
  Dormant, closed ET-005/EB implementation-proof contract for Codex 0.162.1.

  `assess/3` characterizes one untrusted record, using the pinned frozen reference,
  existing qualification identity and bounded development evidence envelope.
  Its producer, custody, observation and prerequisite records are declarations.
  Correlated identifiers and public digests authenticate neither their owners nor
  the actual host, binary, clock, observation or claim-specific result.

  ABSENT means no record was supplied. A singleton enters RECEIVED_UNTRUSTED and
  reaches STRUCTURALLY_VALID only after closed schema, reference, identity,
  interval, correlation and supplied-byte checks. Invalid, stale, duplicate or
  conflicting input reaches REFUSED. No valid prefix of a collection is accepted.

  `verify/3` always ends REFUSED. SOURCE_AUTHENTICATED would require an accepted
  independently installed producer/custody verifier; CLAIM_APPLICABLE would also
  require qualified exact host/profile and observation/replay evidence;
  PROOF_VERIFIED would additionally require substantive ET-005/EB verification.
  None of those authorities exists here. No key, callback, path, signature,
  producer name, saved status or caller-supplied approval can configure one.

  Refusal is terminal for that assessment, with no retry or execution entitlement.
  Reconciliation requires a new assessment of current inputs; `reload/4` ignores
  saved state and reruns verification. There is no persistent receipt store or
  trusted clock, so cross-call replay detection and actual freshness remain
  unverified. Repeated singletons always refuse verification. This pure module
  performs no I/O, activates no runtime, and opens no qualification transition.
  """

  alias SymphonyElixir.Gate2.{EvidenceApplicability, FrozenClaimBinding, QualificationIdentity}

  @fields ~w(schema reference selected_implementation evidence producer observation custody prerequisites claimed_result)
  @producer_fields ~w(component_sha256 authority_record_sha256)
  @observation_fields ~w(observation_id run_id attempt_id started_at completed_at)
  @custody_fields ~w(evidence_id evidence_sha256 custody_record_sha256 integrity_method)
  @prerequisites %{"p08_host_qualification" => "UNVERIFIED", "capacity_profile" => "UNVERIFIED", "independent_review" => "UNVERIFIED"}

  @doc "Checks at most one untrusted record. Structural validity is never proof acceptance."
  @spec assess(term(), term(), term()) :: map()
  def assess(records, identity, as_of) do
    {state, reason, claimed_result} = check_collection(records, identity, as_of)
    valid = state == "STRUCTURALLY_VALID"

    %{
      "state" => state,
      "structural_state" => state,
      "reason" => reason,
      "claim_id" => "ET-005",
      "proof_class" => "EB",
      "selected_implementation" => "codex-cli 0.162.1",
      "catalog_sha256" => FrozenClaimBinding.reference()["catalog_sha256"],
      "catalog_binding" => if(valid, do: "MATCHED_PINNED_DEFINITION", else: "UNVERIFIED"),
      "artifact_integrity" => if(valid, do: "VERIFIED_BYTES", else: "UNVERIFIED"),
      "declared_interval" => if(valid, do: "CURRENT", else: "UNVERIFIED"),
      "declared_identity_sha256" => if(QualificationIdentity.valid?(identity), do: identity.digest, else: nil),
      "assessed_at" => if(EvidenceApplicability.valid_timestamp?(as_of), do: as_of, else: nil),
      "claimed_result" => claimed_result,
      "verified_result" => "UNVERIFIED",
      "producer_authentication" => "UNVERIFIED",
      "custody_authentication" => "UNVERIFIED",
      "observation_authentication" => "UNVERIFIED",
      "replay_protection" => "UNVERIFIED",
      "host_qualification" => "UNVERIFIED",
      "profile_qualification" => "UNVERIFIED",
      "implementation_applicability" => "UNVERIFIED",
      "proof_status" => "UNVERIFIED",
      "independent_acceptance" => "UNVERIFIED",
      "qualification_state" => "UNQUALIFIED",
      "gate2_activation" => false,
      "h100_acceptance" => false,
      "lifecycle" => lifecycle(state)
    }
  end

  @doc "Refuses every proof. No accepted implementation producer/verifier is installed or selectable."
  @spec verify(term(), term(), term()) :: map()
  def verify(records, identity, as_of) do
    result = assess(records, identity, as_of)
    reason = if result["state"] == "STRUCTURALLY_VALID", do: "TRUSTED_IMPLEMENTATION_PRODUCER_UNCONFIGURED", else: result["reason"]
    path = if result["state"] == "REFUSED", do: result["lifecycle"], else: result["lifecycle"] ++ ["REFUSED"]
    Map.merge(result, %{"state" => "REFUSED", "reason" => reason, "lifecycle" => path})
  end

  @doc "Discards cached state and recomputes current structural and refusal-only verification guards."
  @spec reload(term(), term(), term(), term()) :: map()
  def reload(_saved, records, identity, as_of), do: verify(records, identity, as_of)

  # At most two cons cells are examined, before artifact hashing. The existing
  # one-MiB envelope and fixed metadata constrain development parsing only;
  # they are not accepted operational memory/capacity or host-support profiles.
  defp check_collection([], _identity, _as_of), do: {"ABSENT", "MISSING", nil}
  defp check_collection([record], identity, as_of), do: check_record(record, identity, as_of)
  defp check_collection([_, _ | _], _identity, _as_of), do: refused("DUPLICATE_OR_CONFLICTING_RECEIPTS")
  defp check_collection(_records, _identity, _as_of), do: refused("INVALID_RECEIPT_COLLECTION")

  defp check_record(record, identity, as_of) do
    cond do
      not closed?(record, @fields) -> refused("INVALID_PROOF_RECORD")
      record["schema"] != "P09-ET005-EB-IMPLEMENTATION-1" -> refused("UNSUPPORTED_SCHEMA")
      record["reference"] != FrozenClaimBinding.reference() -> refused("REFERENCE_MISMATCH")
      record["selected_implementation"] != "codex-cli 0.162.1" -> refused("UNSUPPORTED_IMPLEMENTATION")
      true -> check_declarations(record, identity, as_of)
    end
  end

  defp check_declarations(record, identity, as_of) do
    cond do
      not valid_producer?(record["producer"]) -> refused("INVALID_PRODUCER")
      not valid_observation?(record["observation"]) -> refused("INVALID_OBSERVATION")
      not valid_custody?(record["custody"]) -> refused("INVALID_CUSTODY")
      record["prerequisites"] != @prerequisites -> refused("INVALID_PREREQUISITES")
      record["claimed_result"] not in ["PASS", "FAIL", "UNCERTAIN"] -> refused("INVALID_CLAIMED_RESULT")
      true -> check_evidence(record, identity, as_of)
    end
  end

  defp check_evidence(record, identity, as_of) do
    evidence = record["evidence"]

    cond do
      not EvidenceApplicability.valid_envelope?(evidence) -> refused("INVALID_EVIDENCE_ENVELOPE")
      evidence["claim_id"] != "ET-005" -> refused("UNSUPPORTED_CLAIM")
      evidence["proof_class"] != "EB" -> refused("UNSUPPORTED_PROOF_CLASS")
      record["observation"]["completed_at"] != evidence["observed_at"] -> refused("OBSERVATION_INTERVAL_MISMATCH")
      record["custody"]["evidence_sha256"] != evidence["sha256"] -> refused("CUSTODY_ARTIFACT_MISMATCH")
      record["custody"]["evidence_id"] != record["observation"]["observation_id"] -> refused("CUSTODY_OBSERVATION_MISMATCH")
      true -> check_artifact(record, identity, as_of)
    end
  end

  defp check_artifact(record, identity, as_of) do
    case EvidenceApplicability.evaluate(record["evidence"], identity, as_of) do
      %{"status" => "CHARACTERIZED"} -> {"STRUCTURALLY_VALID", "STRUCTURAL_CHECKS_ONLY", record["claimed_result"]}
      %{"status" => reason} -> refused(reason)
    end
  end

  defp valid_producer?(record), do: closed?(record, @producer_fields) and Enum.all?(@producer_fields, &digest?(record[&1]))

  defp valid_observation?(record) do
    closed?(record, @observation_fields) and
      Enum.all?(~w(observation_id run_id attempt_id), &digest?(record[&1])) and
      EvidenceApplicability.valid_timestamp?(record["started_at"]) and
      EvidenceApplicability.valid_timestamp?(record["completed_at"]) and
      record["started_at"] <= record["completed_at"]
  end

  defp valid_custody?(record) do
    closed?(record, @custody_fields) and
      Enum.all?(~w(evidence_id evidence_sha256 custody_record_sha256), &digest?(record[&1])) and
      record["integrity_method"] == "SHA256_SUPPLIED_BYTES"
  end

  defp closed?(record, fields) when is_map(record) and map_size(record) == length(fields), do: Enum.all?(fields, &Map.has_key?(record, &1))
  defp closed?(_record, _fields), do: false
  defp digest?(value) when is_binary(value), do: byte_size(value) == 64 and Regex.match?(~r/\A[0-9a-f]{64}\z/, value)
  defp digest?(_value), do: false
  defp refused(reason), do: {"REFUSED", reason, nil}
  defp lifecycle("ABSENT"), do: ["ABSENT"]
  defp lifecycle(state), do: ["RECEIVED_UNTRUSTED", state]
end
