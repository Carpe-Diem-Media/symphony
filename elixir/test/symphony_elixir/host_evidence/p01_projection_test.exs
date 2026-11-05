defmodule SymphonyElixir.HostEvidence.P01ProjectionTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.AgentRuntime.{AttemptGrant, AttemptLedger, AttemptResource, CleanupEvidenceRef, QuarantineDisposition, RecoveryGeneration, RuntimeAttempt}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.HostEvidence.P01Projection, as: P

  @u64 18_446_744_073_709_551_615
  @digest String.duplicate("a", 64)
  @identity_fields ~w(runtime_attempt_id work_item_id lineage_generation responsibility runtime_profile)a

  test "grant_ref_exact_namespace" do
    grant = grant()
    reference = AttemptGrant.reference(grant)
    assert Enum.sort(Map.keys(reference)) == Enum.sort(~w(grant_id project_namespace runtime_identity fence_epoch grant_sha256)a)

    tuple =
      {1, "grant-1", "project-1", @digest, {"attempt-1", "item-1", "lineage-1", "builder", "profile-1"}, {1, "project-1", "host-1", "BOOT-Unchanged", 1, "Nonce-Unchanged"}, @digest, "registration-1",
       1, "resource-1", @digest, @digest, @digest, @digest, @digest, [:workspace_read], 1}

    expected_digest = :crypto.hash(:sha256, :erlang.term_to_binary(tuple, [:deterministic])) |> Base.encode16(case: :lower)
    assert reference.grant_sha256 == expected_digest
    assert {:ok, wire} = P.grant_ref(reference, reference)
    assert Map.keys(wire) |> Enum.sort() == ~w(fence_epoch grant_id grant_sha256 project_namespace runtime_identity)
    assert wire["grant_sha256"] == expected_digest
    assert wire["runtime_identity"]["responsibility"] == "builder"

    assert_rejection(reference, fn -> P.grant_ref(%{reference | project_namespace: "project-2"}, reference) end, :namespace_mismatch)

    for field <- @identity_fields do
      changed = Map.update!(reference.runtime_identity, field, &(&1 <> " "))
      assert_rejection(reference, fn -> P.grant_ref(%{reference | runtime_identity: changed}, reference) end, :identity_mismatch)
    end

    assert Identity.same?(identity(), %{identity() | responsibility: " builder "})

    for field <- [:grant_id, :grant_sha256, :fence_epoch] do
      value = if field == :fence_epoch, do: 2, else: "different"
      value = if field == :grant_sha256, do: String.duplicate("b", 64), else: value
      assert_rejection(reference, fn -> P.grant_ref(Map.put(reference, field, value), reference) end, :stale_grant)
    end

    assert_rejection(reference, fn -> P.grant_ref(Map.put(reference, :policy, "extra"), reference) end, :invalid_request)
    assert AttemptGrant.reference(grant) == reference
  end

  test "stored_struct_fields_exact" do
    expected = [
      {Identity, @identity_fields},
      {RecoveryGeneration, ~w(schema_version project_namespace host_id boot_id sequence nonce)a},
      {QuarantineDisposition, ~w(state reason evidence_ref generation resolution_ref)a},
      {CleanupEvidenceRef,
       ~w(schema_version evidence_id evidence_sha256 project_namespace grant_id runtime_identity fence_epoch resource_set_sha256 verification_generation verifier_implementation_sha256)a},
      {AttemptResource,
       ~w(schema_version resource_id project_namespace grant_id runtime_identity class state revision stable_locator allocation_identity_sha256 capacity_profile_sha256 owner_host_id creation_generation reconciliation_generation last_evidence_ref quarantine)a},
      {AttemptGrant,
       ~w(schema_version grant_id project_namespace tracker_identity_sha256 runtime_identity recovery_generation route_fingerprint subscription_registration_id credential_generation workspace_resource_id source_admission_policy_sha256 process_policy_sha256 network_policy_sha256 tool_policy_sha256 capacity_profile_sha256 allowed_operations fence_epoch)a}
    ]

    for {module, fields} <- expected do
      assert Enum.sort(Map.keys(Map.from_struct(struct(module)))) == Enum.sort(fields)
    end

    assert AttemptLedger.schema_version() == 2
    ref = AttemptGrant.reference(grant())
    records = [identity(), generation(), grant(), resource(), cleanup(), quarantine()]

    preserve(records, fn ->
      assert {:ok, identity_wire} = P.identity(identity())
      assert identity_wire["responsibility"] == "builder"
      assert {:ok, gen_wire} = P.generation(generation())
      assert gen_wire["boot_id"] == "BOOT-Unchanged"
      assert gen_wire["nonce"] == "Nonce-Unchanged"
      assert {:ok, resource_wire} = P.resource(resource(), ref, generation())
      assert resource_wire["schema_version"] == 1
      refute Map.has_key?(resource_wire, "stable_locator")
      assert resource_wire["stable_locator_sha256"] == :crypto.hash(:sha256, "locator-1") |> Base.encode16(case: :lower)
      assert {:ok, cleanup_wire} = P.cleanup_ref(cleanup(), ref, generation())
      assert cleanup_wire["schema_version"] == 1
      assert {:ok, q_wire} = P.quarantine(quarantine())
      assert q_wire["evidence_ref"] == nil
    end)

    for {state, revision} <- [reserved: 0, fencing: 1] do
      row = %{resource() | state: state, revision: revision}

      preserve(row, fn ->
        assert {:ok, %{"state" => wire}} = P.resource(row, ref, generation())
        assert wire == Atom.to_string(state)
      end)
    end

    for state <- ~w(clear quarantined block_reuse operator_resolution_pending released_for_new_authorization remains_quarantined)a do
      q = %{quarantine() | state: state, evidence_ref: "unknown-old", resolution_ref: "Opaque Resolution"}

      preserve(q, fn ->
        assert {:ok, wire} = P.quarantine(q)
        assert wire["state"] == Atom.to_string(state)
        assert wire["resolution_ref"] == "Opaque Resolution"
        assert wire["evidence_ref"] == %{"kind" => "prior", "id" => "unknown-old"}
      end)
    end

    for record <- [
          Map.put(resource(), :extra, true),
          %{resource() | schema_version: 2},
          %{resource() | last_evidence_ref: %{"kind" => "current", "id" => nil}},
          %{resource() | runtime_identity: Map.put(identity(), :extra, true)}
        ] do
      assert_rejection(record, fn -> P.resource(record, ref, generation()) end, :unencodable_p01_value)
    end

    assert_rejection(cleanup(), fn -> P.cleanup_ref(%{cleanup() | project_namespace: "other"}, ref, generation()) end, :namespace_mismatch)
    assert_rejection(cleanup(), fn -> P.cleanup_ref(%{cleanup() | runtime_identity: %{identity() | responsibility: " builder "}}, ref, generation()) end, :identity_mismatch)
    assert_rejection(cleanup(), fn -> P.cleanup_ref(cleanup(), ref, %{generation() | sequence: 2}) end, :recovery_generation_mismatch)
    assert_rejection(resource(), fn -> P.resource(%{resource() | owner_host_id: "other"}, ref, generation()) end, :recovery_generation_mismatch)
    assert_rejection(resource(), fn -> P.resource(%{resource() | reconciliation_generation: %{generation() | sequence: 2}}, ref, generation()) end, :recovery_generation_mismatch)
  end

  test "historical_and_current_links" do
    for stored <- [nil, " UnKnown-History ", "ev2-" <> @digest, String.duplicate("x", 256)] do
      preserve(stored, fn ->
        assert {:ok, wire} = P.evidence_link(stored)
        assert {:ok, ^stored} = P.restore_evidence_link(wire)
        if stored, do: assert(wire == %{"kind" => "prior", "id" => stored}), else: assert(wire == nil)
      end)
    end

    context = context()
    current = %{"kind" => "current", "id" => nil}

    for slot <- ["last_evidence_ref", "quarantine_evidence_ref"] do
      preserve({resource(), context}, fn ->
        assert {:ok, ^current} = P.current_link("object-1", "resource-1", slot, context)
        assert {:ok, "object-1"} = P.restore_current_link(current, "object-1", "resource-1", slot, context)
      end)
    end

    for invalid <- [
          nil,
          %{},
          %{context | phase: :pre_snapshot},
          %{context | phase: :standalone_quarantine},
          %{context | object_id: "other"},
          %{context | resource_id: "other"},
          %{context | self_bindings: []},
          %{context | self_bindings: false},
          %{context | self_bindings: [%{"resource_id" => "other", "slot" => "last_evidence_ref"}]},
          %{context | self_bindings: [%{"resource_id" => "resource-1", "slot" => "invalid"}]},
          Map.put(context, :verified, true),
          Map.put(context, :release_authorized, true)
        ] do
      assert_rejection({resource(), invalid}, fn -> P.current_link("object-1", "resource-1", "last_evidence_ref", invalid) end, :invalid_request)
    end

    for {stored, id, slot} <- [
          {nil, "resource-1", "last_evidence_ref"},
          {"Object-1", "resource-1", "last_evidence_ref"},
          {"object-1", "resource-2", "last_evidence_ref"},
          {"object-1", "resource-1", "resolution_ref"}
        ] do
      error = if is_nil(stored), do: :unencodable_p01_value, else: :invalid_request
      assert_rejection({stored, context}, fn -> P.current_link(stored, id, slot, context) end, error)
    end

    for malformed <- [
          current,
          %{"kind" => "current", "id" => "object-1"},
          %{"kind" => "prior", "id" => nil},
          %{"kind" => "prior", "id" => "old", "verified" => true},
          %{kind: "prior", id: "old"},
          "old",
          1
        ] do
      assert_rejection(malformed, fn -> P.restore_evidence_link(malformed) end, :invalid_request)
    end

    for malformed <- [%{"kind" => "current", "id" => "object-1"}, Map.put(current, "verified", true), %{"kind" => "prior", "id" => "object-1"}] do
      assert_rejection(malformed, fn -> P.restore_current_link(malformed, "object-1", "resource-1", "last_evidence_ref", context) end, :invalid_request)
    end

    for field <- [:evidence_ref, :resolution_ref] do
      q = Map.put(quarantine(), field, current)
      assert_rejection(q, fn -> P.quarantine(q) end, :unencodable_p01_value)
    end

    assert_rejection(current, fn -> P.evidence_link(current) end, :unencodable_p01_value)
    # Even completely forged, mutually consistent context is only a wire conversion.
    forged = %{context | object_id: "not-a-real-object"}
    attempt = RuntimeAttempt.new(identity(), :running)

    preserve({attempt, resource(), cleanup()}, fn ->
      assert {:ok, ^current} = P.current_link("not-a-real-object", "resource-1", "last_evidence_ref", forged)
      refute is_struct(current, CleanupEvidenceRef)
      assert attempt.state == :running
      assert resource().state == :reserved
      assert quarantine().state == :clear
      refute function_exported?(P, :verify, 1)
      refute function_exported?(P, :authorize, 1)
    end)
  end

  test "p01_id_128_129_256_257" do
    for size <- [128, 129, 256] do
      value = String.duplicate("X", size)

      preserve(value, fn ->
        assert {:ok, ^value} = P.identifier(value)
        assert {:ok, wire} = P.evidence_link(value)
        assert {:ok, ^value} = P.restore_evidence_link(wire)
        assert {:ok, _} = P.identity(%{identity() | work_item_id: value})
        assert {:ok, _} = P.generation(%{generation() | nonce: value})
      end)
    end

    assert {:ok, " X "} = P.identifier(" X ")

    for bad <- ["", " ", "   ", "\n", "x\t", "x\r", <<0>>, <<31>>, <<127>>, "é", <<255>>, String.duplicate("x", 257), 1, 1.0, @u64 + 1, nil, :id, %{}] do
      assert_rejection(bad, fn -> P.identifier(bad) end, :unencodable_p01_value)
      assert_rejection(bad, fn -> P.evidence_link(bad) end, :unencodable_p01_value, bad == nil)
    end

    for value <- ["é", "x\n", String.duplicate("x", 257), 42] do
      row = %{resource() | resource_id: value}
      assert_rejection(row, fn -> P.resource(row, AttemptGrant.reference(grant()), generation()) end, :unencodable_p01_value)
      id = %{identity() | work_item_id: value}
      assert_rejection(id, fn -> P.identity(id) end, :unencodable_p01_value)
    end

    assert {:ok, _} = P.generation(%{generation() | sequence: @u64})
    assert_rejection(generation(), fn -> P.generation(%{generation() | sequence: @u64 + 1}) end, :unencodable_p01_value)
    ref = AttemptGrant.reference(grant())

    for bad <- [-1, 0, 1.0, @u64 + 1] do
      assert_rejection(ref, fn -> P.grant_ref(%{ref | fence_epoch: bad}, ref) end, :unencodable_p01_value)
    end

    assert_rejection(resource(), fn -> P.resource(%{resource() | revision: @u64 + 1}, ref, generation()) end, :unencodable_p01_value)
    assert_rejection(identity(), fn -> P.identity(%{identity() | responsibility: :builder}) end, :unencodable_p01_value)
  end

  test "T02-F01 accepts only the historical persisted P01 resource progression" do
    reference = AttemptGrant.reference(grant())

    for {state, minimum} <- [quarantined: 1, block_reuse: 2, operator_resolution_pending: 3, remains_quarantined: 4], evidence <- [nil, "Opaque old Evidence"], revision <- [minimum, minimum + 5] do
      row = quarantined_resource(state, revision, evidence)

      preserve(row, fn ->
        assert {:ok, ^row} = AttemptResource.new(Map.from_struct(row))
        assert {:ok, wire} = P.resource(row, reference, row.reconciliation_generation)
        assert wire["state"] == "quarantined"
        assert wire["quarantine"]["state"] == Atom.to_string(state)
        assert {:ok, ^evidence} = P.restore_evidence_link(wire["last_evidence_ref"])
        assert wire["quarantine"]["evidence_ref"] == wire["last_evidence_ref"]
      end)
    end

    # Equal generations are allowed only with exactly equal bytes. Older
    # generations may retain different boot/nonce bytes at a lower sequence.
    row = quarantined_resource(:quarantined, 1, nil)
    same = %{row | creation_generation: generation(), reconciliation_generation: generation(), quarantine: %{row.quarantine | generation: generation()}}
    preserve(same, fn -> assert {:ok, _} = P.resource(same, reference, generation()) end)
  end

  test "T02-F01 rejects shape-valid impossible historical rows without rewriting facts" do
    reference = AttemptGrant.reference(grant())
    base = resource()
    qrow = quarantined_resource(:quarantined, 1, "old")

    invalid =
      Enum.map(~w(allocating allocated active fenced destroying absent_verified cleanup_unverified)a, &%{base | state: &1}) ++
        [
          %{base | revision: 7},
          %{base | state: :fencing, revision: 0},
          %{base | state: :fencing, revision: 2},
          %{base | last_evidence_ref: "old"},
          %{base | allocation_identity_sha256: @digest},
          %{base | quarantine: %{quarantine() | state: :quarantined}},
          %{base | quarantine: %{quarantine() | reason: :cleanup_unverified}},
          %{base | quarantine: %{quarantine() | evidence_ref: "old"}},
          %{base | quarantine: %{quarantine() | resolution_ref: "resolution"}},
          %{base | quarantine: %{quarantine() | generation: %{generation() | nonce: "other"}}},
          %{base | creation_generation: generation(), reconciliation_generation: %{generation() | sequence: 2}},
          %{qrow | quarantine: %{qrow.quarantine | state: :clear}},
          %{qrow | quarantine: %{qrow.quarantine | state: :released_for_new_authorization}},
          %{qrow | quarantine: %{qrow.quarantine | reason: nil}},
          %{qrow | last_evidence_ref: "different"},
          %{qrow | allocation_identity_sha256: @digest},
          %{qrow | quarantine: %{qrow.quarantine | generation: %{qrow.quarantine.generation | project_namespace: "other"}}},
          %{qrow | quarantine: %{qrow.quarantine | generation: %{qrow.quarantine.generation | host_id: "other"}}},
          %{qrow | quarantine: %{qrow.quarantine | generation: %{qrow.creation_generation | nonce: "same-sequence-different"}}},
          %{qrow | quarantine: %{qrow.quarantine | generation: %{qrow.reconciliation_generation | nonce: "same-sequence-different"}}},
          %{qrow | quarantine: %{qrow.quarantine | generation: %{qrow.quarantine.generation | sequence: 4}}},
          %{qrow | creation_generation: %{qrow.creation_generation | sequence: 3}, reconciliation_generation: %{qrow.reconciliation_generation | sequence: 4}}
        ] ++
        Enum.map([quarantined: 1, block_reuse: 2, operator_resolution_pending: 3, remains_quarantined: 4], fn {state, minimum} ->
          quarantined_resource(state, minimum - 1, nil)
        end)

    for row <- invalid do
      assert {:ok, ^row} = AttemptResource.new(Map.from_struct(row))
      assert_rejection(row, fn -> P.resource(row, reference, row.reconciliation_generation) end, :invalid_request)
    end
  end

  test "T02-F02 preserves identifier encoding errors through both current-link directions" do
    current = %{"kind" => "current", "id" => nil}
    invalid_ids = ["é", <<255>>, <<0>>, "x\n", "x\t", <<127>>, "", " ", String.duplicate("x", 257), 42, 1.0]

    for id <- invalid_ids do
      cases = [
        {id, "resource-1", %{context() | object_id: id}},
        {"object-1", "resource-1", %{context() | object_id: id}},
        {id, "resource-1", context()},
        {"object-1", id, %{context() | resource_id: id, self_bindings: [%{"resource_id" => id, "slot" => "last_evidence_ref"}]}},
        {"object-1", "resource-1", %{context() | self_bindings: [%{"resource_id" => id, "slot" => "last_evidence_ref"}]}}
      ]

      for {stored, resource_id, input} <- cases do
        original = {stored, resource_id, input}
        assert_rejection(original, fn -> P.current_link(stored, resource_id, "last_evidence_ref", input) end, :unencodable_p01_value)
        assert_rejection(original, fn -> P.restore_current_link(current, stored, resource_id, "last_evidence_ref", input) end, :unencodable_p01_value)
      end
    end

    for size <- [128, 129, 256] do
      id = String.duplicate("X", size)
      input = %{context() | object_id: id, resource_id: id, self_bindings: [%{"resource_id" => id, "slot" => "last_evidence_ref"}]}

      preserve({id, input}, fn ->
        assert {:ok, ^current} = P.current_link(id, id, "last_evidence_ref", input)
        assert {:ok, ^id} = P.restore_current_link(current, id, id, "last_evidence_ref", input)
      end)
    end
  end

  test "T02-F02 keeps malformed and nonmatching context errors distinct from encoding errors" do
    current = %{"kind" => "current", "id" => nil}

    for input <- [
          nil,
          %{},
          %{context() | phase: :pre_snapshot},
          %{context() | phase: :standalone_quarantine},
          %{context() | object_id: "different"},
          %{context() | resource_id: "different"},
          %{context() | self_bindings: []},
          %{context() | self_bindings: false},
          %{context() | self_bindings: [%{"resource_id" => "different", "slot" => "last_evidence_ref"}]},
          %{context() | self_bindings: [%{"resource_id" => "resource-1", "slot" => "wrong"}]},
          %{context() | self_bindings: [%{"resource_id" => "resource-1", "slot" => "last_evidence_ref", "verified" => true}]},
          Map.put(context(), :verified, true)
        ] do
      assert_rejection(input, fn -> P.current_link("object-1", "resource-1", "last_evidence_ref", input) end, :invalid_request)
      assert_rejection(input, fn -> P.restore_current_link(current, "object-1", "resource-1", "last_evidence_ref", input) end, :invalid_request)
    end
  end

  test "malformed self-binding lists reject without exceptions" do
    for bindings <- [
          [%{"resource_id" => "resource-1", "slot" => "last_evidence_ref"} | :invalid],
          [hd(context().self_bindings), hd(context().self_bindings)],
          [%{"resource_id" => "resource-1", "slot" => "last_evidence_ref", "verified" => true}]
        ] do
      input = %{context() | self_bindings: bindings}
      assert_rejection(input, fn -> P.current_link("object-1", "resource-1", "last_evidence_ref", input) end, :invalid_request)
    end
  end

  test "creation generation requires exact bytes at equal sequence" do
    row = %{resource() | creation_generation: %{generation() | nonce: "different"}}
    assert_rejection(row, fn -> P.resource(row, AttemptGrant.reference(grant()), generation()) end, :recovery_generation_mismatch)
  end

  defp preserve(original, fun) do
    bytes = :erlang.term_to_binary(original, [:deterministic])
    path = Path.join(System.tmp_dir!(), "p08-t02-#{System.unique_integer([:positive])}.term")
    File.write!(path, bytes)

    try do
      result = fun.()
      assert :erlang.term_to_binary(original, [:deterministic]) == bytes
      assert File.read!(path) == bytes
      assert :erlang.binary_to_term(File.read!(path)) === original
      result
    after
      File.rm!(path)
    end
  end

  defp assert_rejection(original, fun, error, nil_allowed \\ false) do
    preserve(original, fn ->
      if nil_allowed, do: assert(fun.() == {:ok, nil}), else: assert(fun.() == {:error, error})
    end)
  end

  defp quarantined_resource(state, revision, evidence) do
    current = %{generation() | sequence: 3, nonce: "reconciled", boot_id: "new-boot"}
    quarantined = %{generation() | sequence: 2, nonce: "quarantine-generation"}
    q = %{quarantine() | state: state, reason: :cleanup_unverified, evidence_ref: evidence, generation: quarantined, resolution_ref: "opaque-resolution"}
    %{resource() | state: :quarantined, revision: revision, last_evidence_ref: evidence, quarantine: q, reconciliation_generation: current}
  end

  defp identity, do: %Identity{runtime_attempt_id: "attempt-1", work_item_id: "item-1", lineage_generation: "lineage-1", responsibility: "builder", runtime_profile: "profile-1"}
  defp generation, do: %RecoveryGeneration{schema_version: 1, project_namespace: "project-1", host_id: "host-1", boot_id: "BOOT-Unchanged", sequence: 1, nonce: "Nonce-Unchanged"}
  defp quarantine, do: %QuarantineDisposition{state: :clear, reason: nil, evidence_ref: nil, generation: generation(), resolution_ref: nil}

  defp resource,
    do: %AttemptResource{
      schema_version: 1,
      resource_id: "resource-1",
      project_namespace: "project-1",
      grant_id: "grant-1",
      runtime_identity: identity(),
      class: :workspace,
      state: :reserved,
      revision: 0,
      stable_locator: "locator-1",
      allocation_identity_sha256: nil,
      capacity_profile_sha256: @digest,
      owner_host_id: "host-1",
      creation_generation: generation(),
      reconciliation_generation: generation(),
      last_evidence_ref: nil,
      quarantine: quarantine()
    }

  defp cleanup,
    do: %CleanupEvidenceRef{
      schema_version: 1,
      evidence_id: "old-evidence",
      evidence_sha256: @digest,
      project_namespace: "project-1",
      grant_id: "grant-1",
      runtime_identity: identity(),
      fence_epoch: 1,
      resource_set_sha256: @digest,
      verification_generation: generation(),
      verifier_implementation_sha256: @digest
    }

  defp grant,
    do: %AttemptGrant{
      schema_version: 1,
      grant_id: "grant-1",
      project_namespace: "project-1",
      tracker_identity_sha256: @digest,
      runtime_identity: identity(),
      recovery_generation: generation(),
      route_fingerprint: @digest,
      subscription_registration_id: "registration-1",
      credential_generation: 1,
      workspace_resource_id: "resource-1",
      source_admission_policy_sha256: @digest,
      process_policy_sha256: @digest,
      network_policy_sha256: @digest,
      tool_policy_sha256: @digest,
      capacity_profile_sha256: @digest,
      allowed_operations: [:workspace_read],
      fence_epoch: 1
    }

  defp context,
    do: %{
      phase: :predicted_post_snapshot,
      object_id: "object-1",
      resource_id: "resource-1",
      self_bindings: [%{"resource_id" => "resource-1", "slot" => "last_evidence_ref"}, %{"resource_id" => "resource-1", "slot" => "quarantine_evidence_ref"}]
    }
end
