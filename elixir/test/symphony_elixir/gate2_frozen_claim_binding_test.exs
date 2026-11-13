defmodule SymphonyElixir.Gate2FrozenClaimBindingTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.Gate2.{EvidenceApplicability, FrozenClaimBinding, Qualification, QualificationIdentity}

  @root Path.expand("../../..", __DIR__)
  @docs Path.join(@root, "docs/symphony-hardening-playbook-v4.1")
  @packet "GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json"
  @catalog "GATE2_IMPLEMENTATION_QUALIFICATION_MANIFEST.json"
  @now 1_800_000_000

  test "exact real frozen bytes bind the complete ET-005 definition and exact catalogue only" do
    record = record()
    result = FrozenClaimBinding.evaluate([record], identity(), @now)
    assert result["state"] == "REFERENCE_BOUND"
    assert result["reason"] == "EXACT_FROZEN_REFERENCE"
    assert result["artifact_integrity"] == "VERIFIED_BYTES"
    assert result["reference_binding"] == "VERIFIED"
    assert result["reference_provenance"] == "PINNED_ACCEPTED_RECORD"
    assert result["catalog_sha256"] == digest(File.read!(Path.join(@docs, @catalog)))
    assert result["definition"] == frozen_definition()
    assert result["declared_identity_sha256"] == identity().digest
    assert_unqualified(result)
    refute Map.has_key?(result, "bytes")
    refute Map.has_key?(result, "evidence")
  end

  test "wrong catalogue and recomputed altered-meaning catalogue cannot select their own authority" do
    altered_catalog = Qualification.catalog() |> put_in(["transfers", Access.at(4), "transferred_property"], "Anything now transfers")
    record = record()

    for sha <- [String.duplicate("0", 64), digest(Jason.encode!(altered_catalog))] do
      assert_refused(%{record | "catalog_sha256" => sha}, "CATALOG_MISMATCH")
    end
  end

  test "same claim ID with any modified frozen field refuses including omitted inventory or limits" do
    record = record()

    for {field, value} <- frozen_definition() do
      changed = if is_list(value), do: [], else: "substituted"
      assert_refused(put_in(record, ["definition", field], changed), "CLAIM_DEFINITION_MISMATCH")
      assert_refused(%{record | "definition" => Map.delete(record["definition"], field)}, "CLAIM_DEFINITION_MISMATCH")
    end
  end

  test "wrong authority source identity refuses every substituted field" do
    record = record()

    for {field, _value} <- record["source"] do
      assert_refused(put_in(record, ["source", field], "substituted"), "SOURCE_MISMATCH")
    end
  end

  test "candidate, source tree and all other qualification declarations must match exactly" do
    for field <- QualificationIdentity.fields() do
      record = put_in(record(), ["evidence", "identity", field], String.duplicate("b", String.length(bindings()[field])))
      assert_refused(record, "IDENTITY_MISMATCH")
    end
  end

  test "relabeling unchanged packet bytes does not establish a different claim or proof class" do
    for id <- ["ET-004", "OB-023", "BP-01", "ET-999"] do
      assert_refused(put_in(record(), ["evidence", "claim_id"], id), "UNSUPPORTED_CLAIM")
    end

    for proof <- ["IR", "MP", "PASS", "UNKNOWN"] do
      assert_refused(put_in(record(), ["evidence", "proof_class"], proof), "UNSUPPORTED_PROOF_CLASS")
    end
  end

  test "fabricated producer and supplied success or acceptance flags refuse at closed boundaries" do
    for {field, value} <- [{"producer", "Master Governance"}, {"verified", true}, {"accepted", true}, {"status", "PASS"}, {"predecessor", "ACCEPTED"}] do
      assert_refused(Map.put(record(), field, value), "INVALID_BINDING_ENVELOPE")
      assert_refused(update_in(record(), ["evidence"], &Map.put(&1, field, value)), "INVALID_EVIDENCE_ENVELOPE")
    end
  end

  test "valid byte integrity alone cannot authenticate substituted reference evidence" do
    bytes = "a perfectly intact self-reported PASS"
    record = record() |> put_in(["evidence", "bytes"], bytes) |> put_in(["evidence", "sha256"], digest(bytes))
    assert EvidenceApplicability.evaluate(record["evidence"], identity(), @now)["artifact_integrity"] == "VERIFIED_BYTES"
    assert_refused(record, "ARTIFACT_SOURCE_MISMATCH")
  end

  test "modified or oversized bytes refuse before any reference success" do
    assert_refused(put_in(record(), ["evidence", "bytes"], "changed"), "INTEGRITY_MISMATCH")
    assert_refused(put_in(record(), ["evidence", "bytes"], String.duplicate("x", 1_048_577)), "INVALID_EVIDENCE_ENVELOPE")
  end

  test "missing, duplicate, conflicting, flooded and improper collections cannot bind a prefix" do
    record = record()
    conflict = put_in(record, ["definition", "claim"], "replaced")

    for {records, reason} <- [
          {[], "MISSING"},
          {[record, record], "CONFLICTING"},
          {[record, conflict], "CONFLICTING"},
          {List.duplicate(record, 10_000), "CONFLICTING"},
          {[record | :invalid], "INVALID_BINDING_COLLECTION"},
          {nil, "INVALID_BINDING_COLLECTION"}
        ] do
      result = FrozenClaimBinding.evaluate(records, identity(), @now)
      assert result["state"] == "REFUSED"
      assert result["reason"] == reason
      assert result["reference_binding"] == "UNVERIFIED"
      assert_unqualified(result)
    end
  end

  test "stale and future declarations refuse and reload always recomputes" do
    record = record()
    saved = FrozenClaimBinding.evaluate([record], identity(), @now)
    assert saved["state"] == "REFERENCE_BOUND"
    assert FrozenClaimBinding.reload(saved, [record], identity(), @now) == saved
    assert FrozenClaimBinding.reload(saved, [record], identity(), @now + 1)["reason"] == "STALE"
    assert FrozenClaimBinding.reload(saved, [], identity(), @now)["state"] == "REFUSED"
    assert FrozenClaimBinding.reload(%{"state" => "INDEPENDENTLY_REVIEWED", "verified" => true}, [], identity(), @now)["reference_binding"] == "UNVERIFIED"
    assert_refused(put_in(record, ["evidence", "observed_at"], @now + 1), "INVALID_EVIDENCE_ENVELOPE")
    future = record |> put_in(["evidence", "observed_at"], @now + 1) |> put_in(["evidence", "expires_at"], @now + 2)
    assert_refused(future, "FUTURE")
  end

  test "unsupported host, predecessor, mechanical and independent scopes refuse" do
    for scope <- ["HOST_PROOF", "UNSUPPORTED_HOST", "UNSUPPORTED_CONFIGURATION", "ACCEPTED_PREDECESSOR", "MECHANICAL_PROOF", "INDEPENDENT_REVIEW"] do
      assert_refused(put_in(record(), ["evidence", "scope"], scope), "UNSUPPORTED")
    end
  end

  test "invalid cutoff and forged qualification identity refuse" do
    for cutoff <- [nil, -1, "now", 9_223_372_036_854_775_808] do
      assert FrozenClaimBinding.evaluate([record()], identity(), cutoff)["state"] == "REFUSED"
    end

    identity = %{identity() | digest: String.duplicate("0", 64)}
    assert FrozenClaimBinding.evaluate([record()], identity, @now)["state"] == "REFUSED"
  end

  test "reference result cannot enter assessment slots or open either higher lifecycle edge" do
    result = FrozenClaimBinding.evaluate([record()], identity(), @now)
    assessment = Qualification.assess(identity(), [result], @now)
    assert assessment["state"] == "UNQUALIFIED"
    assert assessment["proof_status"] == "UNVERIFIED"
    assert length(Qualification.requirements()) == 58
    assert Enum.sum(Enum.map(Qualification.requirements(), &length(&1["required_proof_classes"]))) == 218
    assert {:error, :mechanical_verifier_unconfigured} = Qualification.transition("CHARACTERIZED", "MECHANICALLY_QUALIFIED", identity(), [], @now)
    assert {:error, :independent_review_unconfigured} = Qualification.transition("MECHANICALLY_QUALIFIED", "INDEPENDENTLY_REVIEWED", identity(), [], @now)
    assert {:error, :invalid_transition} = Qualification.transition("UNQUALIFIED", "INDEPENDENTLY_REVIEWED", identity(), [], @now)
  end

  @tag :tmp_dir
  test "actual compilation refuses every changed authority input without selecting caller pins", %{tmp_dir: tmp_dir} do
    source_path = Path.join(@root, "elixir/lib/symphony_elixir/gate2/frozen_claim_binding.ex")
    source = File.read!(source_path) |> String.replace("defmodule SymphonyElixir.Gate2.FrozenClaimBinding do", "defmodule P09FrozenClaimSourceDriftProbe do")
    fixture_source_path = Path.join(tmp_dir, "elixir/lib/symphony_elixir/gate2/frozen_claim_binding.ex")

    paths = [
      "docs/symphony-hardening-playbook-v4.1/" <> @packet,
      "docs/symphony-hardening-playbook-v4.1/" <> @catalog,
      "docs/symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_ACCEPTANCE_2026-11-02.md",
      "docs/superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md"
    ]

    for path <- paths do
      File.mkdir_p!(Path.dirname(Path.join(tmp_dir, path)))
      File.write!(Path.join(tmp_dir, path), File.read!(Path.join(@root, path)))
    end

    for path <- paths do
      fixture_path = Path.join(tmp_dir, path)
      bytes = File.read!(fixture_path)
      File.write!(fixture_path, bytes <> "\n")

      assert_raise ArgumentError, "accepted P09 reference source mismatch: #{path}", fn ->
        Code.compile_string(source, fixture_source_path)
      end

      File.write!(fixture_path, bytes)
    end
  end

  test "nonmaps, extra fields and substituted source shape cannot become bound references" do
    for record <- [nil, %{}, Map.put(record(), "unexpected", true)] do
      assert_refused(record, "INVALID_BINDING_ENVELOPE")
    end

    assert_refused(%{record() | "source" => nil}, "SOURCE_MISMATCH")
    assert_refused(%{record() | "definition" => nil}, "CLAIM_DEFINITION_MISMATCH")
  end

  test "deep and oversized untrusted metadata refuses against the fixed finite reference" do
    deep = Enum.reduce(1..100_000, :untrusted, fn _, acc -> [acc] end)
    huge_map = Map.new(1..100_000, &{&1, &1})
    huge_binary = :binary.copy("x", 4_194_304)
    reference = record()

    for definition <- [deep, huge_map, Map.put(reference["definition"], "claim", deep), Map.put(reference["definition"], "claim", huge_binary)] do
      assert_refused(%{reference | "definition" => definition}, "CLAIM_DEFINITION_MISMATCH")
    end

    for source <- [huge_map, Map.put(reference["source"], "sha256", deep)] do
      assert_refused(%{reference | "source" => source}, "SOURCE_MISMATCH")
    end
  end

  defp record do
    bytes = File.read!(Path.join(@docs, @packet))

    evidence = %{
      "claim_id" => "ET-005",
      "proof_class" => "EB",
      "identity" => bindings(),
      "observed_at" => @now - 1,
      "expires_at" => @now + 1,
      "scope" => "DEVELOPMENT_COMPONENT",
      "sha256" => digest(bytes),
      "bytes" => bytes
    }

    FrozenClaimBinding.reference() |> Map.put("evidence", evidence)
  end

  defp frozen_definition do
    @docs |> Path.join(@packet) |> File.read!() |> Jason.decode!() |> Map.fetch!("evidence_transfer_matrix") |> Enum.find(&(&1["claim_id"] == "ET-005"))
  end

  defp assert_refused(record, reason) do
    result = FrozenClaimBinding.evaluate([record], identity(), @now)
    assert result["state"] == "REFUSED"
    assert result["reason"] == reason
    assert result["reference_binding"] == "UNVERIFIED"
    assert_unqualified(result)
  end

  defp assert_unqualified(result) do
    for field <- ~w(claim_applicability run_provenance proof_status independent_acceptance operational_host_qualification) do
      assert result[field] == "UNVERIFIED"
    end

    assert result["qualification_state"] == "UNQUALIFIED"
    refute result["gate2_activation"]
    refute result["h100_acceptance"]
  end

  defp bindings, do: Map.new(QualificationIdentity.fields(), &{&1, String.duplicate("a", if(String.ends_with?(&1, "_sha"), do: 40, else: 64))})
  defp identity, do: elem(QualificationIdentity.new(bindings()), 1)
  defp digest(bytes), do: Base.encode16(:crypto.hash(:sha256, bytes), case: :lower)
end
