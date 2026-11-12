defmodule SymphonyElixir.Gate2.FrozenClaimBinding do
  @moduledoc """
  Dormant, closed ET-005/EB binding to an accepted version-controlled reference.

  The trust anchor is the separately reviewed source pins below, not a supplied
  producer name, expected hash, callback or PASS field. Compilation refuses if
  the accepted packet, acceptance record, canonical plan or merged P09 catalogue
  changes. The full frozen definition and exact catalogue revision are compared
  before a reference can bind. No runtime filesystem or network access occurs.

  UNVERIFIED -> REFERENCE_BOUND requires one closed record, exact source and
  catalogue identities, the complete frozen definition, matching qualification
  declarations, current declared times and the accepted packet's exact bytes.
  Any missing, duplicate, conflicting, unsupported or uncertain input -> REFUSED.
  Refusal is terminal for that assessment. Reload discards saved results and
  repeats every guard; it can regress a bound reference to REFUSED.

  REFERENCE_BOUND verifies only the reference's content provenance to the pinned
  accepted record. It does not authenticate the submitter, observation time,
  actual candidate/runtime or external evidence producer. It does not prove the
  H-080B transfer applicable to a new implementation. Mechanical proof, independent
  acceptance and host qualification remain unverified. No proof slot or higher
  Qualification transition consumes this result. There are no persistent writes,
  host effects, execution entitlements or automatic qualification transitions.
  """

  alias SymphonyElixir.Gate2.{EvidenceApplicability, Qualification, QualificationIdentity}

  @docs "docs/symphony-hardening-playbook-v4.1/"
  @packet_path @docs <> "GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json"
  @catalog_path @docs <> "GATE2_IMPLEMENTATION_QUALIFICATION_MANIFEST.json"
  @acceptance_path @docs <> "GATE2_INVENTORY_FREEZE_ACCEPTANCE_2026-11-02.md"
  @plan_path "docs/superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md"
  @packet_sha256 "a651b1574ec0a186f6b4cd9548787cf9b67009f6692268ce5a8d0669d9d0636a"
  @catalog_sha256 "b3720a6e1a4747e38fc8101f8e4d002372eb2eff39fc2daffac13067011ead10"
  @acceptance_sha256 "0318dbd3c76b8c3407fe02a9c62e9013129477c853a9f677ffaf4f9009b7cd57"
  @plan_sha256 "a1d5cdba65c19a09e86ed814a595e8bbae0c9dcfc97afe021ab67826db09ff68"

  # Pins are reviewed code, never taken from adjacent caller-editable metadata.
  # Read each authority once, hash that read, then decode those same bytes.
  for {path, expected} <- [
        {@packet_path, @packet_sha256},
        {@catalog_path, @catalog_sha256},
        {@acceptance_path, @acceptance_sha256},
        {@plan_path, @plan_sha256}
      ] do
    absolute_path = Path.expand("../../../../" <> path, __DIR__)
    @external_resource absolute_path
    bytes = File.read!(absolute_path)

    unless Base.encode16(:crypto.hash(:sha256, bytes), case: :lower) == expected do
      raise ArgumentError, "accepted P09 reference source mismatch: #{path}"
    end

    cond do
      path == @packet_path -> @packet Jason.decode!(bytes)
      path == @catalog_path -> @catalog Jason.decode!(bytes)
      true -> :ok
    end
  end

  @definition Enum.find(@packet["evidence_transfer_matrix"], &(&1["claim_id"] == "ET-005"))
  @catalog_claim Enum.find(@catalog["transfers"], &(&1["id"] == "ET-005"))
  @transfer_fields ~w(source authority_class original_scope transfer_status transferred_property non_transferred_property)

  unless @definition["claim_id"] == @catalog_claim["id"] and @catalog_claim["required_proof_classes"] == ["EB", "IR"] and
           Enum.all?(@transfer_fields, &(@definition[&1] == @catalog_claim[&1])) do
    raise ArgumentError, "accepted ET-005 catalogue projection mismatch"
  end

  @source %{
    "path" => @packet_path,
    "sha256" => @packet_sha256,
    "git_blob" => "6cf92dbad8507d4e6c7553392b163fcac02b897d",
    "source_commit" => "4dc2cc0369874dc152931c38464e1fdfa87704f2",
    "source_tree" => "a659f7c9d8e92ed920b9179bbb1cd22b4cd3dfd5",
    "acceptance_sha256" => @acceptance_sha256,
    "plan_sha256" => @plan_sha256
  }
  @fields ~w(catalog_sha256 definition source evidence)

  @doc "Returns fixed reference metadata, never a verification receipt or execution grant."
  @spec reference() :: map()
  def reference, do: %{"catalog_sha256" => @catalog_sha256, "definition" => @definition, "source" => @source}

  @doc "Verifies at most one ET-005/EB reference. All implementation proof properties remain unverified."
  @spec evaluate(term(), term(), term()) :: map()
  def evaluate(records, identity, as_of) do
    {reason, artifact_integrity} = check_collection(records, identity, as_of)
    bound = reason == "EXACT_FROZEN_REFERENCE"

    Map.merge(reference(), %{
      "state" => if(bound, do: "REFERENCE_BOUND", else: "REFUSED"),
      "reason" => reason,
      "claim_id" => "ET-005",
      "proof_class" => "EB",
      "verified_property" => "FROZEN_REFERENCE_BINDING_ONLY",
      "reference_binding" => if(bound, do: "VERIFIED", else: "UNVERIFIED"),
      "reference_provenance" => if(bound, do: "PINNED_ACCEPTED_RECORD", else: "UNVERIFIED"),
      "artifact_integrity" => artifact_integrity,
      "declared_identity_sha256" => if(QualificationIdentity.valid?(identity), do: identity.digest, else: nil),
      "assessed_at" => if(EvidenceApplicability.valid_timestamp?(as_of), do: as_of, else: nil),
      "claim_applicability" => "UNVERIFIED",
      "run_provenance" => "UNVERIFIED",
      "proof_status" => "UNVERIFIED",
      "independent_acceptance" => "UNVERIFIED",
      "operational_host_qualification" => "UNVERIFIED",
      "qualification_state" => "UNQUALIFIED",
      "gate2_activation" => false,
      "h100_acceptance" => false
    })
  end

  @doc "Saved state is ignored. Rehash and rebind current inputs and declared cutoff on every reload."
  @spec reload(term(), term(), term(), term()) :: map()
  def reload(_saved_result, records, identity, as_of), do: evaluate(records, identity, as_of)

  # At most two cons cells inspected. Do not enumerate floods, hash a prefix or
  # accept a good record alongside a contradictory or duplicate reference.
  defp check_collection([], _identity, _as_of), do: {"MISSING", "UNVERIFIED"}
  defp check_collection([record], identity, as_of), do: check_binding(record, identity, as_of)
  defp check_collection([_, _ | _], _identity, _as_of), do: {"CONFLICTING", "UNVERIFIED"}
  defp check_collection(_records, _identity, _as_of), do: {"INVALID_BINDING_COLLECTION", "UNVERIFIED"}

  defp check_binding(record, identity, as_of) do
    cond do
      not closed_binding?(record) -> {"INVALID_BINDING_ENVELOPE", "UNVERIFIED"}
      record["catalog_sha256"] != @catalog_sha256 or Qualification.catalog() != @catalog -> {"CATALOG_MISMATCH", "UNVERIFIED"}
      record["source"] != @source -> {"SOURCE_MISMATCH", "UNVERIFIED"}
      record["definition"] != @definition -> {"CLAIM_DEFINITION_MISMATCH", "UNVERIFIED"}
      true -> check_evidence(record["evidence"], identity, as_of)
    end
  end

  defp check_evidence(evidence, identity, as_of) do
    cond do
      not EvidenceApplicability.valid_envelope?(evidence) -> {"INVALID_EVIDENCE_ENVELOPE", "UNVERIFIED"}
      evidence["claim_id"] != "ET-005" -> {"UNSUPPORTED_CLAIM", "UNVERIFIED"}
      evidence["proof_class"] != "EB" -> {"UNSUPPORTED_PROOF_CLASS", "UNVERIFIED"}
      true -> check_artifact(evidence, identity, as_of)
    end
  end

  defp check_artifact(evidence, identity, as_of) do
    result = EvidenceApplicability.evaluate(evidence, identity, as_of)

    cond do
      result["status"] != "CHARACTERIZED" -> {result["status"], result["artifact_integrity"]}
      evidence["sha256"] != @packet_sha256 -> {"ARTIFACT_SOURCE_MISMATCH", "VERIFIED_BYTES"}
      true -> {"EXACT_FROZEN_REFERENCE", "VERIFIED_BYTES"}
    end
  end

  defp closed_binding?(record) when is_map(record) and map_size(record) == length(@fields),
    do: Enum.all?(@fields, &Map.has_key?(record, &1))

  defp closed_binding?(_record), do: false
end
