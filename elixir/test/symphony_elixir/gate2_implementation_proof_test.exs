defmodule SymphonyElixir.Gate2ImplementationProofTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.Gate2.{EvidenceApplicability, FrozenClaimBinding, ImplementationProof}
  alias SymphonyElixir.Gate2.{Qualification, QualificationIdentity}

  @now 1_800_000_000

  test "a dedicated dormant ET-005 implementation-proof boundary exists" do
    assert Code.ensure_loaded?(ImplementationProof)
    assert function_exported?(ImplementationProof, :assess, 3)
    assert function_exported?(ImplementationProof, :verify, 3)
    assert function_exported?(ImplementationProof, :reload, 4)
  end

  test "exact closed synthetic record characterizes declarations and bytes only" do
    result = assess(record())
    assert result["state"] == "STRUCTURALLY_VALID"
    assert result["structural_state"] == "STRUCTURALLY_VALID"
    assert result["reason"] == "STRUCTURAL_CHECKS_ONLY"
    assert result["artifact_integrity"] == "VERIFIED_BYTES"
    assert result["catalog_binding"] == "MATCHED_PINNED_DEFINITION"
    assert result["declared_interval"] == "CURRENT"
    assert result["claimed_result"] == "PASS"
    assert result["lifecycle"] == ["RECEIVED_UNTRUSTED", "STRUCTURALLY_VALID"]
    assert_unverified(result)
    refute Map.has_key?(result, "evidence")
    refute Map.has_key?(result, "bytes")
  end

  test "structural success always refuses producer authentication and proof verification" do
    result = ImplementationProof.verify([record()], identity(), @now)
    assert result["state"] == "REFUSED"
    assert result["structural_state"] == "STRUCTURALLY_VALID"
    assert result["reason"] == "TRUSTED_IMPLEMENTATION_PRODUCER_UNCONFIGURED"
    assert result["artifact_integrity"] == "VERIFIED_BYTES"
    assert result["lifecycle"] == ["RECEIVED_UNTRUSTED", "STRUCTURALLY_VALID", "REFUSED"]
    assert_unverified(result)
  end

  test "every required field is mandatory and extra or aliased fields refuse" do
    r = record()

    for key <- Map.keys(r) do
      assert_refused(Map.delete(r, key), "INVALID_PROOF_RECORD")
    end

    for key <- ["verified", "accepted", "status", "callback", "trusted_key", "signature", "host_qualified"] do
      assert_refused(Map.put(r, key, true), "INVALID_PROOF_RECORD")
    end

    assert_refused(%{r | "schema" => "P09-ET005-EB-IMPLEMENTATION-2"}, "UNSUPPORTED_SCHEMA")
    assert_refused(Map.put(Map.delete(r, "claimed_result"), :claimed_result, "PASS"), "INVALID_PROOF_RECORD")
  end

  test "each nested declaration is closed and cannot carry an acceptance shortcut" do
    for key <- ["producer", "observation", "custody", "prerequisites"] do
      assert_refused(put_in(record(), [key, "accepted"], true), "INVALID_" <> String.upcase(key))
      assert_refused(put_in(record(), [key], nil), "INVALID_" <> String.upcase(key))

      for nested_key <- Map.keys(record()[key]) do
        changed = update_in(record(), [key], &Map.delete(&1, nested_key))
        assert_refused(changed, "INVALID_" <> String.upcase(key))
      end
    end
  end

  test "only ET-005 EB and the selected newer implementation are recognized" do
    for claim <- ["ET-004", "OB-023", "BP-01", "ET-999"] do
      assert_refused(put_in(record(), ["evidence", "claim_id"], claim), "UNSUPPORTED_CLAIM")
    end

    for proof <- ["IR", "MP", "PASS", "UNKNOWN"] do
      assert_refused(put_in(record(), ["evidence", "proof_class"], proof), "UNSUPPORTED_PROOF_CLASS")
    end

    for implementation <- ["codex-cli 0.159.3", "codex-cli 0.162.2", "Codex", nil] do
      assert_refused(%{record() | "selected_implementation" => implementation}, "UNSUPPORTED_IMPLEMENTATION")
    end
  end

  test "exact catalogue revision and every full frozen definition field must match" do
    assert_refused(put_in(record(), ["reference", "catalog_sha256"], digest("changed catalogue")), "REFERENCE_MISMATCH")

    for key <- Map.keys(record()["reference"]["definition"]) do
      assert_refused(put_in(record(), ["reference", "definition", key], "changed meaning"), "REFERENCE_MISMATCH")
    end

    assert_refused(%{record() | "reference" => Map.put(record()["reference"], "proof_class", "EB")}, "REFERENCE_MISMATCH")
  end

  test "every pinned reference source identity refuses substitution" do
    for key <- Map.keys(record()["reference"]["source"]) do
      assert_refused(put_in(record(), ["reference", "source", key], "substitute"), "REFERENCE_MISMATCH")
    end
  end

  test "candidate source executable configuration host and all identity bindings must match" do
    for key <- QualificationIdentity.fields() do
      changed = put_in(record(), ["evidence", "identity", key], String.duplicate("b", byte_size(bindings()[key])))
      assert_refused(changed, "IDENTITY_MISMATCH")
    end
  end

  test "fabricated producer names keys and authority flags cannot select authentication" do
    for key <- ["name", "key", "signature", "verified", "authority", "callback"] do
      assert_refused(put_in(record(), ["producer", key], "trusted"), "INVALID_PRODUCER")
    end

    for key <- Map.keys(record()["producer"]) do
      r = put_in(record(), ["producer", key], digest("made-up authority"))
      assert assess(r)["state"] == "STRUCTURALLY_VALID"
      assert ImplementationProof.verify([r], identity(), @now)["producer_authentication"] == "UNVERIFIED"
    end
  end

  test "custody references must correlate but correlation authenticates no custodian" do
    assert_refused(put_in(record(), ["custody", "evidence_sha256"], digest("different bytes")), "CUSTODY_ARTIFACT_MISMATCH")
    assert_refused(put_in(record(), ["custody", "evidence_id"], digest("different observation")), "CUSTODY_OBSERVATION_MISMATCH")
    assert_refused(put_in(record(), ["custody", "integrity_method"], "TRUST_MY_SIGNATURE"), "INVALID_CUSTODY")
    r = put_in(record(), ["custody", "custody_record_sha256"], digest("forged custody"))
    assert assess(r)["state"] == "STRUCTURALLY_VALID"
    assert ImplementationProof.verify([r], identity(), @now)["custody_authentication"] == "UNVERIFIED"
  end

  test "recomputed digests of substituted evidence cannot make a verified proof" do
    r = replace_bytes(record(), "replaced content with a recomputed public digest")
    assert assess(r)["artifact_integrity"] == "VERIFIED_BYTES"
    assert ImplementationProof.verify([r], identity(), @now)["state"] == "REFUSED"
    assert_unverified(ImplementationProof.verify([r], identity(), @now))
  end

  test "unaltered digest over modified bytes refuses" do
    assert_refused(put_in(record(), ["evidence", "bytes"], "changed"), "INTEGRITY_MISMATCH")
  end

  test "whole submission refuses duplicate conflict flood improper tail or nonlist" do
    r = record()
    conflict = replace_bytes(r, "contradiction")

    for records <- [[r, r], [r, conflict], List.duplicate(r, 10_000)] do
      assert ImplementationProof.assess(records, identity(), @now)["reason"] == "DUPLICATE_OR_CONFLICTING_RECEIPTS"
      assert ImplementationProof.verify(records, identity(), @now)["state"] == "REFUSED"
    end

    for records <- [nil, %{}, [r | :invalid], :invalid] do
      assert ImplementationProof.assess(records, identity(), @now)["reason"] == "INVALID_RECEIPT_COLLECTION"
    end
  end

  test "replayed singleton cannot gain provenance in repeated calls or a fresh process" do
    r = record()
    first = ImplementationProof.verify([r], identity(), @now)
    assert first["state"] == "REFUSED"
    assert first["replay_protection"] == "UNVERIFIED"
    assert ImplementationProof.verify([r], identity(), @now) == first
    assert Task.async(fn -> ImplementationProof.verify([r], identity(), @now) end) |> Task.await() == first
    assert ImplementationProof.reload(first, [r], identity(), @now)["state"] == "REFUSED"

    renewed =
      r
      |> put_in(["observation", "run_id"], digest("replacement run"))
      |> put_in(["observation", "attempt_id"], digest("replacement attempt"))
      |> put_in(["observation", "completed_at"], @now + 10)
      |> put_in(["evidence", "observed_at"], @now + 10)
      |> put_in(["evidence", "expires_at"], @now + 70)

    assert ImplementationProof.verify([renewed], identity(), @now + 10)["state"] == "REFUSED"
    assert ImplementationProof.verify([renewed], identity(), @now + 10)["replay_protection"] == "UNVERIFIED"
  end

  test "no evidence is absent structurally and refused as a proof" do
    assert ImplementationProof.assess([], identity(), @now)["state"] == "ABSENT"
    assert ImplementationProof.verify([], identity(), @now)["state"] == "REFUSED"
    assert ImplementationProof.verify([], identity(), @now)["reason"] == "MISSING"
  end

  test "declared observation must be complete ordered and correlated with the envelope" do
    for {key, value} <- [{"started_at", nil}, {"started_at", -1}, {"started_at", @now + 1}] do
      assert_refused(put_in(record(), ["observation", key], value), "INVALID_OBSERVATION")
    end

    assert_refused(put_in(record(), ["observation", "completed_at"], @now - 1), "OBSERVATION_INTERVAL_MISMATCH")
    assert_refused(put_in(record(), ["observation", "completed_at"], @now + 1), "OBSERVATION_INTERVAL_MISMATCH")
  end

  test "freshness boundaries reject expired future reversed and invalid declarations" do
    r = record()
    assert assess(r, @now)["state"] == "STRUCTURALLY_VALID"
    assert assess(r, @now + 59)["state"] == "STRUCTURALLY_VALID"
    assert_refused(r, "STALE", @now + 60)
    assert_refused(r, "FUTURE", @now - 1)
    assert_refused(put_in(r, ["evidence", "expires_at"], @now), "INVALID_EVIDENCE_ENVELOPE")

    for cutoff <- [nil, -1, "now", 9_223_372_036_854_775_808] do
      assert assess(r, cutoff)["state"] == "REFUSED"
    end
  end

  test "fresh declarations are not an authenticated clock or replay witness" do
    result = assess(record())
    assert result["declared_interval"] == "CURRENT"
    assert result["observation_authentication"] == "UNVERIFIED"
    assert result["replay_protection"] == "UNVERIFIED"
  end

  test "unsupported scope profile or predecessor assertions never open proof verification" do
    for scope <- ["HOST_PROOF", "UNSUPPORTED_HOST", "UNSUPPORTED_CONFIGURATION", "MECHANICAL_PROOF", "INDEPENDENT_REVIEW"] do
      assert_refused(put_in(record(), ["evidence", "scope"], scope), "UNSUPPORTED")
    end

    for key <- Map.keys(record()["prerequisites"]) do
      assert_refused(put_in(record(), ["prerequisites", key], "ACCEPTED"), "INVALID_PREREQUISITES")
    end

    # Even mutually consistent caller-supplied host/profile hashes are declarations.
    attrs = bindings() |> Map.put("host_profile_sha256", digest("unknown host")) |> Map.put("capacity_profile_sha256", digest("unsupported capacity"))
    {:ok, claimed_identity} = QualificationIdentity.new(attrs)
    r = put_in(record(), ["evidence", "identity"], attrs)
    result = ImplementationProof.verify([r], claimed_identity, @now)
    assert result["state"] == "REFUSED"
    assert result["host_qualification"] == "UNVERIFIED"
    assert result["profile_qualification"] == "UNVERIFIED"
  end

  test "claimed PASS FAIL and UNCERTAIN are never verified results" do
    for claim <- ["PASS", "FAIL", "UNCERTAIN"] do
      r = %{record() | "claimed_result" => claim}
      assert assess(r)["claimed_result"] == claim
      assert assess(r)["verified_result"] == "UNVERIFIED"
      assert ImplementationProof.verify([r], identity(), @now)["state"] == "REFUSED"
    end

    for claim <- [true, "ACCEPTED", "VERIFIED", nil] do
      assert_refused(%{record() | "claimed_result" => claim}, "INVALID_CLAIMED_RESULT")
    end
  end

  test "reload ignores cached success and recomputes current identities times and bytes" do
    saved = %{"state" => "PROOF_VERIFIED", "accepted" => true, "producer_authentication" => "VERIFIED"}
    assert ImplementationProof.reload(saved, [record()], identity(), @now)["state"] == "REFUSED"
    r = put_in(record(), ["evidence", "bytes"], "changed after restart")
    assert ImplementationProof.reload(saved, [r], identity(), @now)["reason"] == "INTEGRITY_MISMATCH"
    assert ImplementationProof.reload(saved, [record()], identity(), @now + 60)["reason"] == "STALE"
    assert ImplementationProof.reload(saved, [], identity(), @now)["reason"] == "MISSING"
    r = put_in(record(), ["reference", "source", "source_tree"], String.duplicate("b", 40))
    assert ImplementationProof.reload(saved, [r], identity(), @now)["reason"] == "REFERENCE_MISMATCH"
    assert ImplementationProof.reload(saved, [replace_bytes(record(), "new bytes")], identity(), @now)["producer_authentication"] == "UNVERIFIED"
  end

  test "invalid qualification struct cannot self-authenticate" do
    forged = %{identity() | digest: digest("forged")}
    assert ImplementationProof.assess([record()], forged, @now)["reason"] == "INVALID"
    assert ImplementationProof.assess([record()], nil, @now)["reason"] == "INVALID"
  end

  test "all digests identifiers and scalar fields have bounded representations" do
    for parent <- ["producer", "observation", "custody"], {key, value} <- record()[parent], is_binary(value), byte_size(value) == 64 do
      for invalid <- [String.duplicate("a", 65), String.duplicate("z", 64), nil, []] do
        assert assess(put_in(record(), [parent, key], invalid))["state"] == "REFUSED"
      end
    end

    assert_refused(put_in(record(), ["evidence", "bytes"], String.duplicate("x", EvidenceApplicability.max_artifact_bytes() + 1)), "INVALID_EVIDENCE_ENVELOPE")
    assert assess(replace_bytes(record(), String.duplicate("x", EvidenceApplicability.max_artifact_bytes())))["state"] == "STRUCTURALLY_VALID"
  end

  test "malformed and huge metadata cannot trigger arbitrary enumeration or proof success" do
    deep = Enum.reduce(1..20_000, :leaf, fn _, x -> [x] end)

    for key <- ["reference", "producer", "observation", "custody", "prerequisites"] do
      assert assess(%{record() | key => deep})["state"] == "REFUSED"
    end

    for r <- [nil, %{}, %{"unknown" => true}, Map.new(1..10_000, &{&1, &1})] do
      assert_refused(r, "INVALID_PROOF_RECORD")
    end
  end

  test "contract results cannot enter qualification slots or manufacture independent review" do
    for result <- [assess(record()), ImplementationProof.verify([record()], identity(), @now)] do
      report = Qualification.assess(identity(), [result], @now)
      assert report["state"] == "UNQUALIFIED"
      assert report["proof_status"] == "UNVERIFIED"
      assert {:error, :mechanical_verifier_unconfigured} = Qualification.transition("CHARACTERIZED", "MECHANICALLY_QUALIFIED", identity(), [result], @now)
      assert {:error, :independent_review_unconfigured} = Qualification.transition("MECHANICALLY_QUALIFIED", "INDEPENDENTLY_REVIEWED", identity(), [result], @now)
      assert {:error, :invalid_transition} = Qualification.transition("UNQUALIFIED", "INDEPENDENTLY_REVIEWED", identity(), [result], @now)
      assert_unverified(result)
    end
  end

  defp assess(r, cutoff \\ @now), do: ImplementationProof.assess([r], identity(), cutoff)

  defp assert_refused(r, reason, cutoff \\ @now) do
    result = assess(r, cutoff)
    assert result["state"] == "REFUSED"
    assert result["reason"] == reason
    assert_unverified(result)
  end

  defp assert_unverified(result) do
    for key <- ~w(producer_authentication custody_authentication observation_authentication replay_protection
      implementation_applicability proof_status independent_acceptance verified_result host_qualification profile_qualification) do
      assert result[key] == "UNVERIFIED"
    end

    assert result["qualification_state"] == "UNQUALIFIED"
    refute result["gate2_activation"]
    refute result["h100_acceptance"]
  end

  defp record do
    bytes = "synthetic ET-005 implementation observation, not host evidence"

    %{
      "schema" => "P09-ET005-EB-IMPLEMENTATION-1",
      "reference" => FrozenClaimBinding.reference(),
      "selected_implementation" => "codex-cli 0.162.1",
      "evidence" => %{
        "claim_id" => "ET-005",
        "proof_class" => "EB",
        "identity" => bindings(),
        "observed_at" => @now,
        "expires_at" => @now + 60,
        "scope" => "DEVELOPMENT_COMPONENT",
        "sha256" => digest(bytes),
        "bytes" => bytes
      },
      "producer" => %{"component_sha256" => digest("producer"), "authority_record_sha256" => digest("claimed authority")},
      "observation" => %{"observation_id" => digest("observation"), "run_id" => digest("run"), "attempt_id" => digest("attempt"), "started_at" => @now - 1, "completed_at" => @now},
      "custody" => %{"evidence_id" => digest("observation"), "evidence_sha256" => digest(bytes), "custody_record_sha256" => digest("claimed custody"), "integrity_method" => "SHA256_SUPPLIED_BYTES"},
      "prerequisites" => %{"p08_host_qualification" => "UNVERIFIED", "capacity_profile" => "UNVERIFIED", "independent_review" => "UNVERIFIED"},
      "claimed_result" => "PASS"
    }
  end

  defp replace_bytes(r, bytes) do
    r |> put_in(["evidence", "bytes"], bytes) |> put_in(["evidence", "sha256"], digest(bytes)) |> put_in(["custody", "evidence_sha256"], digest(bytes))
  end

  defp bindings, do: Map.new(QualificationIdentity.fields(), fn field -> {field, String.duplicate("a", if(String.ends_with?(field, "_sha"), do: 40, else: 64))} end)
  defp identity, do: elem(QualificationIdentity.new(bindings()), 1)
  defp digest(bytes), do: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower)
end
