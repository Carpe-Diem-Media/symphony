defmodule SymphonyElixir.Gate2.Qualification do
  @moduledoc """
  Dormant P09 coverage assessment. No runtime admission calls this module.

  UNQUALIFIED -> CHARACTERIZED requires digest-verified supplied bytes, matching
  identity declarations and current declared intervals for every frozen proof
  slot, with no unknown, duplicate or conflicting evidence. This establishes
  artifact characterization only. Claim applicability, catalog binding and
  provenance remain unverified, even when the same bytes are relabeled.

  CHARACTERIZED -> MECHANICALLY_QUALIFIED additionally requires accepted P01-P08,
  G00, numerical profiles and claim-specific proof verifiers. Those verifiers are
  unconfigured here, so this transition always refuses.

  MECHANICALLY_QUALIFIED -> INDEPENDENTLY_REVIEWED requires authenticated external
  review of the exact manifest and proofs. That interface is also unconfigured.
  No transition has host side effects, creates authority or accepts H-100/Gate 2.

  Reload recomputes from current evidence and cutoff. A saved disposition, digest,
  claimed review or local PASS cannot restore qualification or execution rights.
  """

  alias SymphonyElixir.Gate2.{EvidenceApplicability, QualificationIdentity}

  @external_resource Path.expand("../../../../docs/symphony-hardening-playbook-v4.1/GATE2_IMPLEMENTATION_QUALIFICATION_MANIFEST.json", __DIR__)
  @catalog_bytes File.read!(@external_resource)
  @manifest Jason.decode!(@catalog_bytes)
  @catalog_digest Base.encode16(:crypto.hash(:sha256, @catalog_bytes), case: :lower)
  @groups ~w(obligations transfers bearer_paths)
  @max_records Enum.sum(for group <- @groups, claim <- @manifest[group], do: length(claim["required_proof_classes"]))
  @max_artifact_bytes EvidenceApplicability.max_artifact_bytes()
  @max_payload_bytes @max_records * @max_artifact_bytes

  @spec catalog() :: map()
  def catalog, do: @manifest

  @spec requirements() :: [map()]
  def requirements, do: Enum.flat_map(@groups, &@manifest[&1])

  @doc "Returns all 26 OB, 13 ET and 19 BP dispositions, without evidence payloads."
  @spec assess(term(), term(), term()) :: map()
  def assess(identity, records, as_of) do
    {records, errors} = validate_inputs(identity, records, as_of)
    grouped = Enum.group_by(records, &{&1["claim_id"], &1["proof_class"]})
    claims = Map.new(@groups, &{&1, Enum.map(@manifest[&1], fn claim -> assess_claim(claim, grouped, identity, as_of) end)})

    complete = errors == [] and Enum.all?(@groups, fn group -> Enum.all?(claims[group], &(&1["disposition"] == "CHARACTERIZED")) end)

    report =
      Map.merge(claims, %{
        "schema_version" => @manifest["schema_version"],
        "scope" => @manifest["scope"],
        "requirements_sha256" => @catalog_digest,
        "assessment_input_contract" => @manifest["assessment_input_contract"],
        "characterization_scope" => "ARTIFACT_BYTES_AND_DECLARATIONS_ONLY",
        "claim_applicability" => "UNVERIFIED",
        "evidence_catalog_binding" => "UNVERIFIED",
        "proof_status" => "UNVERIFIED",
        "independent_acceptance" => "UNVERIFIED",
        "identity" => if(QualificationIdentity.valid?(identity), do: identity.bindings, else: nil),
        "identity_sha256" => if(QualificationIdentity.valid?(identity), do: identity.digest, else: nil),
        "assessed_at" => if(EvidenceApplicability.valid_timestamp?(as_of), do: as_of, else: nil),
        "state" => if(complete, do: "CHARACTERIZED", else: "UNQUALIFIED"),
        "input_errors" => errors,
        "mechanical_verification" => "UNCONFIGURED",
        "independent_review" => "UNCONFIGURED",
        "operational_host_qualification" => "UNVERIFIED",
        "gate2_activation" => false,
        "h100_acceptance" => false
      })

    # Digest uses OTP deterministic external term encoding; it is a content
    # identity for this report, never a signature or independent approval.
    Map.put(report, "assessment_sha256", Base.encode16(:crypto.hash(:sha256, :erlang.term_to_binary(report, [:deterministic])), case: :lower))
  end

  @doc "Checks only the next lifecycle edge, re-assessing all evidence each time."
  @spec transition(term(), term(), term(), term(), term()) :: {:ok, map()} | {:error, atom()}
  def transition("UNQUALIFIED", "CHARACTERIZED", identity, records, as_of) do
    case assess(identity, records, as_of) do
      %{"state" => "CHARACTERIZED"} = report -> {:ok, report}
      _report -> {:error, :incomplete_characterization}
    end
  end

  def transition("CHARACTERIZED", "MECHANICALLY_QUALIFIED", _identity, _records, _as_of), do: {:error, :mechanical_verifier_unconfigured}
  def transition("MECHANICALLY_QUALIFIED", "INDEPENDENTLY_REVIEWED", _identity, _records, _as_of), do: {:error, :independent_review_unconfigured}
  def transition(_from, _to, _identity, _records, _as_of), do: {:error, :invalid_transition}

  @doc "A persisted report is a projection only. Reload always computes a fresh disposition."
  @spec reload(term(), term(), term(), term()) :: map()
  def reload(_saved_report, identity, records, as_of), do: assess(identity, records, as_of)

  defp assess_claim(claim, grouped, identity, as_of) do
    proofs =
      Enum.map(claim["required_proof_classes"], fn proof_class ->
        result =
          case Map.get(grouped, {claim["id"], proof_class}, []) do
            [] -> unverified("MISSING")
            [record] -> EvidenceApplicability.evaluate(record, identity, as_of)
            _duplicates -> unverified("CONFLICTING")
          end

        Map.put(result, "proof_class", proof_class)
      end)

    disposition = if Enum.all?(proofs, &(&1["status"] == "CHARACTERIZED")), do: "CHARACTERIZED", else: "BLOCKED"
    claim |> Map.put("proofs", proofs) |> Map.put("disposition", disposition)
  end

  defp validate_inputs(identity, records, as_of) do
    errors = if QualificationIdentity.valid?(identity), do: [], else: ["INVALID_IDENTITY"]
    errors = if EvidenceApplicability.valid_timestamp?(as_of), do: errors, else: ["INVALID_CUTOFF" | errors]

    case bounded_records(records, 0, 0, []) do
      {:ok, bounded} ->
        slots = for claim <- requirements(), proof_class <- claim["required_proof_classes"], do: {claim["id"], proof_class}

        {known, unknown} =
          Enum.split_with(bounded, fn record ->
            is_map(record) and {record["claim_id"], record["proof_class"]} in slots
          end)

        {known, if(unknown == [], do: errors, else: ["UNKNOWN_OR_MALFORMED_EVIDENCE" | errors])}

      {:error, reason} ->
        {[], [reason | errors]}
    end
  end

  # Check at most max_records + 1 cons cells before grouping or artifact hashing.
  # These are defensive development-input ceilings, not accepted host capacity.
  # Reject the entire collection on overflow; never characterize its prefix.
  defp bounded_records([], _count, _bytes, acc), do: {:ok, Enum.reverse(acc)}

  defp bounded_records([_record | _rest], count, _bytes, _acc) when count >= @max_records,
    do: {:error, "INPUT_RECORD_LIMIT_EXCEEDED"}

  defp bounded_records([record | rest], count, bytes, acc) do
    payload_bytes = payload_size(record)
    total = bytes + payload_bytes

    cond do
      total > @max_payload_bytes -> {:error, "INPUT_PAYLOAD_LIMIT_EXCEEDED"}
      payload_bytes > @max_artifact_bytes -> {:error, "INPUT_ARTIFACT_LIMIT_EXCEEDED"}
      not EvidenceApplicability.valid_envelope?(record) -> {:error, "INVALID_EVIDENCE_ENVELOPE"}
      true -> bounded_records(rest, count + 1, total, [record | acc])
    end
  end

  defp bounded_records(_improper_or_nonlist, _count, _bytes, _acc), do: {:error, "INVALID_EVIDENCE_LIST"}

  defp payload_size(%{"bytes" => bytes}) when is_binary(bytes), do: byte_size(bytes)
  defp payload_size(_record), do: 0

  defp unverified(status) do
    %{
      "status" => status,
      "artifact_integrity" => "UNVERIFIED",
      "claim_applicability" => "UNVERIFIED",
      "evidence_catalog_binding" => "UNVERIFIED",
      "proof_status" => "UNVERIFIED",
      "independent_acceptance" => "UNVERIFIED"
    }
  end
end
