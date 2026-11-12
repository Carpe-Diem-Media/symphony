defmodule SymphonyElixir.Gate2QualificationManifestTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.Gate2.{EvidenceApplicability, Qualification, QualificationIdentity}

  @now 1_800_000_000

  test "assessment component exists without changing runtime admission" do
    assert Code.ensure_loaded?(Qualification)
  end

  test "identity binds every component and rejects absent, extra and malformed bindings" do
    attrs = bindings()
    assert {:ok, identity} = QualificationIdentity.new(attrs)
    assert {:ok, ^identity} = QualificationIdentity.new(attrs)

    for field <- QualificationIdentity.fields() do
      assert {:error, :invalid_qualification_identity} = QualificationIdentity.new(Map.delete(attrs, field))
      assert {:error, :invalid_qualification_identity} = QualificationIdentity.new(Map.put(attrs, field, "unknown"))
    end

    assert {:error, :invalid_qualification_identity} = QualificationIdentity.new(Map.put(attrs, "approved", true))
  end

  test "matching bytes characterize an artifact but never verify a proof or a PASS assertion" do
    identity = identity()
    record = evidence("OB-001", "MP", identity)
    result = EvidenceApplicability.evaluate(record, identity, @now)
    assert result["status"] == "CHARACTERIZED"
    assert result["artifact_integrity"] == "VERIFIED_BYTES"
    assert result["proof_status"] == "UNVERIFIED"
    assert result["reason"] == "PROOF_VERIFIER_UNCONFIGURED"

    assert EvidenceApplicability.evaluate(Map.put(record, "verified", true), identity, @now)["status"] == "INVALID"
    assert EvidenceApplicability.evaluate(%{"status" => "PASS"}, identity, @now)["status"] == "INVALID"
  end

  test "source tree, candidate and every other component must match exactly" do
    for field <- QualificationIdentity.fields() do
      changed = Map.update!(bindings(), field, &String.replace(&1, "a", "b"))
      {:ok, other} = QualificationIdentity.new(changed)
      record = evidence("OB-001", "MP", other)
      assert EvidenceApplicability.evaluate(record, identity(), @now)["status"] == "IDENTITY_MISMATCH"
    end
  end

  test "stale, future, reversed and malformed observation intervals refuse" do
    record = evidence("OB-001", "MP", identity())

    for {changes, status} <- [
          {%{"expires_at" => @now}, "STALE"},
          {%{"observed_at" => @now + 1}, "INVALID"},
          {%{"observed_at" => @now + 1, "expires_at" => @now + 2}, "FUTURE"},
          {%{"observed_at" => "yesterday"}, "INVALID"},
          {%{"expires_at" => nil}, "INVALID"}
        ] do
      assert EvidenceApplicability.evaluate(Map.merge(record, changes), identity(), @now)["status"] == status
    end
  end

  test "modified bytes and unsupported host or configuration evidence cannot qualify" do
    record = evidence("OB-001", "MP", identity())
    assert EvidenceApplicability.evaluate(%{record | "bytes" => "modified"}, identity(), @now)["status"] == "INTEGRITY_MISMATCH"

    for scope <- ["HOST_PROOF", "UNSUPPORTED_HOST", "UNSUPPORTED_CONFIGURATION", "INDEPENDENT_REVIEW"] do
      assert EvidenceApplicability.evaluate(%{record | "scope" => scope}, identity(), @now)["status"] == "UNSUPPORTED"
    end
  end

  test "invalid evidence metadata is never copied into a secret-free report" do
    record = evidence("OB-001", "MP", identity())
    record = %{record | "sha256" => "untrusted-private-payload", "observed_at" => %{"private" => "data"}}
    result = EvidenceApplicability.evaluate(record, identity(), @now)
    assert result["status"] == "INVALID"
    assert result["evidence_sha256"] == nil
    assert result["observed_at"] == nil
    refute Jason.encode!(result) =~ "untrusted-private-payload"
  end

  test "a modified identity struct or digest cannot bypass reconstruction validation" do
    original = identity()
    changed = Map.put(original, :digest, String.duplicate("0", 64))
    refute QualificationIdentity.valid?(changed)
    assert Qualification.assess(changed, complete_evidence(), @now)["state"] == "UNQUALIFIED"
  end

  test "artifact size and malformed envelope boundaries refuse" do
    record = evidence("OB-001", "MP", identity())

    for invalid <- [
          nil,
          %{},
          %{record | "bytes" => nil},
          %{record | "bytes" => String.duplicate("x", 1_048_577)},
          %{record | "identity" => nil},
          %{record | "sha256" => nil},
          %{record | "proof_class" => 1},
          %{record | "scope" => nil},
          Map.delete(record, "expires_at")
        ] do
      assert EvidenceApplicability.evaluate(invalid, identity(), @now)["status"] == "INVALID"
    end
  end

  test "empty evidence returns every frozen obligation, transfer and bearer disposition" do
    report = Qualification.assess(identity(), [], @now)
    assert report["state"] == "UNQUALIFIED"
    assert Enum.map(report["obligations"], & &1["id"]) == ids("OB", 26, 3)
    assert Enum.map(report["transfers"], & &1["id"]) == ids("ET", 13, 3)
    assert Enum.map(report["bearer_paths"], & &1["id"]) == ids("BP", 19, 2)
    assert Enum.all?(all_proofs(report), &(&1["status"] == "MISSING"))
    refute report["gate2_activation"]
    refute report["h100_acceptance"]
  end

  test "complete development artifacts permit characterization only" do
    records = complete_evidence()
    report = Qualification.assess(identity(), records, @now)
    assert report["state"] == "CHARACTERIZED"
    assert Enum.all?(all_proofs(report), &(&1["artifact_integrity"] == "VERIFIED_BYTES"))
    assert Enum.all?(all_proofs(report), &(&1["proof_status"] == "UNVERIFIED"))
    assert report["mechanical_verification"] == "UNCONFIGURED"
    assert report["independent_review"] == "UNCONFIGURED"
    assert report == Qualification.assess(identity(), Enum.reverse(records), @now)
  end

  test "development input contract derives count and byte ceilings without operational capacity authority" do
    contract = Qualification.catalog()["assessment_input_contract"]
    assert contract["scope"] == "DEVELOPMENT_PARSER_ONLY"
    assert contract["max_records"] == 218
    assert contract["max_artifact_bytes"] == 1_048_576
    assert contract["max_payload_bytes"] == 218 * 1_048_576
    assert contract["operational_capacity_authority"] == "UNCONFIGURED"
    assert length(complete_evidence()) == 218
    assert Qualification.assess(identity(), complete_evidence(), @now)["state"] == "CHARACTERIZED"
  end

  test "oversized collections and duplicate floods refuse before characterizing a prefix" do
    records = complete_evidence()

    oversized_collections = [
      records ++ [hd(records)],
      List.duplicate(hd(records), 10_000),
      List.duplicate(hd(records), 219) ++ :unexamined_tail
    ]

    for oversized <- oversized_collections do
      report = Qualification.assess(identity(), oversized, @now)
      assert report["state"] == "UNQUALIFIED"
      assert "INPUT_RECORD_LIMIT_EXCEEDED" in report["input_errors"]
      assert Enum.all?(all_proofs(report), &(&1["artifact_integrity"] == "UNVERIFIED"))
    end
  end

  test "an oversized individual artifact refuses before grouping or hashing" do
    record = evidence("OB-001", "MP", identity()) |> with_bytes(String.duplicate("x", 1_048_577))
    report = Qualification.assess(identity(), [record], @now)
    assert "INPUT_ARTIFACT_LIMIT_EXCEEDED" in report["input_errors"]
    assert Enum.all?(all_proofs(report), &(&1["artifact_integrity"] == "UNVERIFIED"))
  end

  test "aggregate payload boundaries include repeated bytes in every supplied record" do
    bytes = String.duplicate("x", 1_048_576)
    records = Enum.map(complete_evidence(), &with_bytes(&1, bytes))

    for delta <- [-1, 0, 1] do
      last_bytes = String.duplicate("x", 1_048_576 + delta)
      candidate = List.update_at(records, -1, &with_bytes(&1, last_bytes))
      assert Enum.reduce(candidate, 0, &(byte_size(&1["bytes"]) + &2)) == 218 * 1_048_576 + delta
      report = Qualification.assess(identity(), candidate, @now)

      if delta <= 0 do
        assert report["state"] == "CHARACTERIZED"
      else
        assert report["state"] == "UNQUALIFIED"
        assert "INPUT_PAYLOAD_LIMIT_EXCEEDED" in report["input_errors"]
        assert Enum.all?(all_proofs(report), &(&1["artifact_integrity"] == "UNVERIFIED"))
      end
    end
  end

  test "improper lists refuse without enumeration crashes or partial success" do
    record = evidence("OB-001", "MP", identity())

    for records <- [[record | :invalid_tail], List.duplicate(record, 218) ++ :invalid_tail] do
      report = Qualification.assess(identity(), records, @now)
      assert report["state"] == "UNQUALIFIED"
      assert "INVALID_EVIDENCE_LIST" in report["input_errors"]
    end
  end

  test "oversized metadata and unbounded integer encodings refuse" do
    record = evidence("OB-001", "MP", identity())
    huge = String.duplicate("x", 65_536)
    too_large_integer = Integer.pow(2, 256)

    for invalid <- [
          %{record | "claim_id" => huge},
          %{record | "proof_class" => huge},
          %{record | "scope" => huge},
          %{record | "sha256" => huge},
          %{record | "observed_at" => too_large_integer, "expires_at" => too_large_integer + 1},
          Map.merge(record, Map.new(1..1_000, &{"extra-#{&1}", nil}))
        ] do
      result = EvidenceApplicability.evaluate(invalid, identity(), @now)
      assert result["status"] == "INVALID"
      refute Jason.encode!(result) =~ huge
      refute Jason.encode!(result) =~ to_string(too_large_integer)
    end

    report = Qualification.assess(identity(), [], too_large_integer)
    assert "INVALID_CUTOFF" in report["input_errors"]
    assert report["assessed_at"] == nil
  end

  test "assessment rejects unbounded metadata before grouping and never characterizes a prefix" do
    records = complete_evidence()
    record = hd(records)
    huge = String.duplicate("x", 65_536)
    oversized_keys = Map.new(1..8, &{huge <> to_string(&1), nil})

    for invalid <- [
          %{record | "claim_id" => huge},
          %{record | "proof_class" => huge},
          %{record | "scope" => huge},
          Map.put(record, "unexpected", huge),
          Map.put(Map.delete(record, "scope"), huge, nil),
          oversized_keys,
          %{record | "identity" => Map.put(record["identity"], "host_profile_sha256", huge)}
        ] do
      report = Qualification.assess(identity(), [invalid | tl(records)], @now)
      assert report["state"] == "UNQUALIFIED"
      assert "INVALID_EVIDENCE_ENVELOPE" in report["input_errors"]
      assert Enum.all?(all_proofs(report), &(&1["artifact_integrity"] == "UNVERIFIED"))
    end
  end

  test "relabeling identical bytes never establishes exact-claim or catalog applicability" do
    original = evidence("OB-001", "MP", identity())

    for record <- [original, %{original | "claim_id" => "OB-002"}, %{original | "proof_class" => "IR"}] do
      result = EvidenceApplicability.evaluate(record, identity(), @now)
      assert result["artifact_integrity"] == "VERIFIED_BYTES"
      assert result["claim_applicability"] == "UNVERIFIED"
      assert result["evidence_catalog_binding"] == "UNVERIFIED"
      assert result["proof_status"] == "UNVERIFIED"
      assert result["independent_acceptance"] == "UNVERIFIED"
    end

    report = Qualification.assess(identity(), complete_evidence(), @now)
    assert report["state"] == "CHARACTERIZED"
    assert report["claim_applicability"] == "UNVERIFIED"
    assert report["evidence_catalog_binding"] == "UNVERIFIED"
    assert report["independent_acceptance"] == "UNVERIFIED"
    assert Enum.all?(all_proofs(report), &(&1["claim_applicability"] == "UNVERIFIED"))
  end

  test "changed catalog meaning and a recomputed payload digest remain unauthenticated" do
    catalog = Qualification.catalog()
    changed = put_in(catalog, ["obligations", Access.at(0), "pass_condition"], "A different claim with the same label")
    refute hash(Jason.encode!(catalog)) == hash(Jason.encode!(changed))

    for declaration <- [catalog, changed] do
      bytes = Jason.encode!(%{"catalog_sha256" => hash(Jason.encode!(declaration)), "claim" => hd(declaration["obligations"]), "status" => "PASS"})
      record = evidence("OB-001", "MP", identity()) |> with_bytes(bytes)
      result = EvidenceApplicability.evaluate(record, identity(), @now)
      assert result["artifact_integrity"] == "VERIFIED_BYTES"
      assert result["claim_applicability"] == "UNVERIFIED"
      assert result["evidence_catalog_binding"] == "UNVERIFIED"
      assert result["proof_status"] == "UNVERIFIED"
    end
  end

  test "unsupported proof and acceptance assertions cannot supply a verifier" do
    record = evidence("OB-001", "MP", identity())

    for invalid <- [
          Map.put(record, "claim_applicability", "VERIFIED"),
          Map.put(record, "catalog_sha256", hash(Jason.encode!(Qualification.catalog()))),
          Map.put(record, "independent_acceptance", "ACCEPTED")
        ] do
      result = EvidenceApplicability.evaluate(invalid, identity(), @now)
      assert result["status"] == "INVALID"
      assert result["claim_applicability"] == "UNVERIFIED"
    end

    records = [%{record | "proof_class" => "AUTHENTICATED_PROOF"} | tl(complete_evidence())]
    report = Qualification.assess(identity(), records, @now)
    assert "UNKNOWN_OR_MALFORMED_EVIDENCE" in report["input_errors"]
    assert report["state"] == "UNQUALIFIED"
    assert report["independent_acceptance"] == "UNVERIFIED"
  end

  test "missing BP positive or negative and missing ET coverage block characterization" do
    for id <- ["BP-01", "BP-19", "ET-001", "ET-013", "OB-026"] do
      records = Enum.reject(complete_evidence(), &(&1["claim_id"] == id))
      assert Qualification.assess(identity(), records, @now)["state"] == "UNQUALIFIED"
    end

    records = Enum.reject(complete_evidence(), &(&1["claim_id"] == "BP-01" and &1["proof_class"] == "NEGATIVE_CONTROL"))
    assert Qualification.assess(identity(), records, @now)["state"] == "UNQUALIFIED"
  end

  test "identical duplicates and contradictory evidence cannot mask missing coverage" do
    records = complete_evidence()
    original = hd(records)

    for duplicate <- [original, %{original | "bytes" => "conflicting"}] do
      report = Qualification.assess(identity(), [original, duplicate | Enum.drop(records, 2)], @now)
      assert report["state"] == "UNQUALIFIED"
      assert hd(hd(report["obligations"])["proofs"])["status"] == "CONFLICTING"
    end
  end

  test "unknown claims, proof classes and malformed inputs fail closed" do
    records = complete_evidence()

    for {invalid, reason} <- [
          {nil, "INVALID_EVIDENCE_ENVELOPE"},
          {%{}, "INVALID_EVIDENCE_ENVELOPE"},
          {%{hd(records) | "claim_id" => "OB-027"}, "UNKNOWN_OR_MALFORMED_EVIDENCE"},
          {%{hd(records) | "proof_class" => "APPROVED"}, "UNKNOWN_OR_MALFORMED_EVIDENCE"}
        ] do
      report = Qualification.assess(identity(), [invalid | tl(records)], @now)
      assert report["state"] == "UNQUALIFIED"
      assert reason in report["input_errors"]
    end

    for invalid <- [nil, %{}, :not_a_list] do
      assert Qualification.assess(identity(), invalid, @now)["state"] == "UNQUALIFIED"
    end

    assert Qualification.assess(%{}, records, @now)["state"] == "UNQUALIFIED"
    assert Qualification.assess(identity(), records, -1)["state"] == "UNQUALIFIED"
  end

  test "transfer limitations remain exact even with matching artifacts" do
    transfers = Qualification.assess(identity(), complete_evidence(), @now)["transfers"]
    assert Enum.at(transfers, 6)["transfer_status"] == "NOT_ACCEPTED"
    assert Enum.at(transfers, 7)["transfer_status"] == "DIAGNOSTIC_ONLY"
    assert Enum.at(transfers, 8)["transfer_status"] == "DIAGNOSTIC_ONLY"
    assert Enum.all?(transfers, & &1["new_proof_required"])
    assert Enum.at(transfers, 4)["non_transferred_property"] =~ "SIWC"
  end

  test "lifecycle rejects jumps, unverified mechanical proof and manufactured review" do
    records = complete_evidence()
    assert {:ok, %{"state" => "CHARACTERIZED"}} = Qualification.transition("UNQUALIFIED", "CHARACTERIZED", identity(), records, @now)
    assert {:error, :incomplete_characterization} = Qualification.transition("UNQUALIFIED", "CHARACTERIZED", identity(), [], @now)
    assert {:error, :invalid_transition} = Qualification.transition("UNQUALIFIED", "INDEPENDENTLY_REVIEWED", identity(), records, @now)
    assert {:error, :mechanical_verifier_unconfigured} = Qualification.transition("CHARACTERIZED", "MECHANICALLY_QUALIFIED", identity(), records, @now)
    assert {:error, :independent_review_unconfigured} = Qualification.transition("MECHANICALLY_QUALIFIED", "INDEPENDENTLY_REVIEWED", identity(), records, @now)
  end

  test "JSON restart reload rechecks identity, time and bytes and ignores claimed authority" do
    records = complete_evidence()
    report = Qualification.assess(identity(), records, @now)
    path = Path.join(System.tmp_dir!(), "p09-reload-#{System.unique_integer([:positive])}.json")
    on_exit(fn -> File.rm(path) end)
    File.write!(path, Jason.encode!(Map.put(report, "state", "INDEPENDENTLY_REVIEWED")))
    saved = path |> File.read!() |> Jason.decode!()
    assert Qualification.reload(saved, identity(), records, @now)["state"] == "CHARACTERIZED"
    assert Qualification.reload(saved, identity(), records, @now + 60)["state"] == "UNQUALIFIED"
    assert Qualification.reload(saved, identity(), [], @now)["state"] == "UNQUALIFIED"
    assert Qualification.reload(saved, %{}, records, @now)["state"] == "UNQUALIFIED"
  end

  defp bindings do
    Map.new(QualificationIdentity.fields(), fn key ->
      size = if String.ends_with?(key, "_sha"), do: 40, else: 64
      {key, String.duplicate("a", size)}
    end)
  end

  defp identity do
    {:ok, identity} = QualificationIdentity.new(bindings())
    identity
  end

  defp evidence(id, proof_class, identity) do
    bytes = Jason.encode!(%{"reported_status" => "PASS", "limitation" => "synthetic component fixture"})

    %{
      "claim_id" => id,
      "proof_class" => proof_class,
      "identity" => identity.bindings,
      "observed_at" => @now - 1,
      "expires_at" => @now + 1,
      "scope" => "DEVELOPMENT_COMPONENT",
      "sha256" => Base.encode16(:crypto.hash(:sha256, bytes), case: :lower),
      "bytes" => bytes
    }
  end

  defp complete_evidence do
    for claim <- Qualification.requirements(), proof_class <- claim["required_proof_classes"] do
      evidence(claim["id"], proof_class, identity())
    end
  end

  defp all_proofs(report), do: Enum.flat_map(report["obligations"] ++ report["transfers"] ++ report["bearer_paths"], & &1["proofs"])
  defp hash(bytes), do: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower)
  defp with_bytes(record, bytes), do: %{record | "bytes" => bytes, "sha256" => hash(bytes)}
  defp ids(prefix, n, width), do: Enum.map(1..n, &(prefix <> "-" <> String.pad_leading(to_string(&1), width, "0")))
end
