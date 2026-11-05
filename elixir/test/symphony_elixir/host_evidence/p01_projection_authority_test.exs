defmodule SymphonyElixir.HostEvidence.P01ProjectionAuthorityTest do
  use ExUnit.Case, async: false

  alias SymphonyElixir.AgentRuntime.{AttemptBoundary, AttemptResource, CleanupEvidenceRef, QuarantineDisposition}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.HostEvidence.P01Projection, as: P

  test "structural conversions cannot release authority or mutate the boundary ledger" do
    root = Path.join(System.tmp_dir!(), "p08-t02-boundary-#{System.unique_integer([:positive])}")
    path = Path.join(root, "resources.dets")
    Process.register(self(), :p08_t02_projection_test_owner)
    {:ok, boundary} = AttemptBoundary.start_link(owner_name: :p08_t02_projection_test_owner, resource_ledger_opts: [path: path, project_namespace: "project-1", host_id: "host-1"])

    try do
      {:ok, generation} = AttemptBoundary.reconcile_startup(boundary)
      identity = %Identity{runtime_attempt_id: "attempt-1", work_item_id: "item-1", lineage_generation: "lineage-1", responsibility: "builder", runtime_profile: "profile-1"}
      digest = String.duplicate("a", 64)
      ref = %{grant_id: "grant-1", project_namespace: "project-1", runtime_identity: identity, fence_epoch: 1, grant_sha256: digest}
      q = %QuarantineDisposition{state: :clear, reason: nil, evidence_ref: nil, generation: generation, resolution_ref: nil}

      row = %AttemptResource{
        schema_version: 1,
        resource_id: "resource-1",
        project_namespace: "project-1",
        grant_id: "grant-1",
        runtime_identity: identity,
        class: :workspace,
        state: :reserved,
        revision: 0,
        stable_locator: "locator-1",
        allocation_identity_sha256: nil,
        capacity_profile_sha256: digest,
        owner_host_id: "host-1",
        creation_generation: generation,
        reconciliation_generation: generation,
        last_evidence_ref: nil,
        quarantine: q
      }

      assert {:ok, ^row} = AttemptBoundary.reserve_resource_sync(boundary, row)
      state_before = :sys.get_state(boundary)
      table = :sys.get_state(state_before.ledger).table
      assert :ok = :dets.sync(table)
      rows_before = :dets.foldl(fn item, acc -> [item | acc] end, [], table) |> Enum.sort()
      bytes_before = File.read!(path)

      evidence = %CleanupEvidenceRef{
        schema_version: 1,
        evidence_id: "fabricated-object",
        evidence_sha256: digest,
        project_namespace: "project-1",
        grant_id: "grant-1",
        runtime_identity: identity,
        fence_epoch: 1,
        resource_set_sha256: digest,
        verification_generation: generation,
        verifier_implementation_sha256: digest
      }

      context = %{phase: :predicted_post_snapshot, object_id: "fabricated-object", resource_id: "resource-1", self_bindings: [%{"resource_id" => "resource-1", "slot" => "last_evidence_ref"}]}

      assert {:ok, resource_wire} = P.resource(row, ref, generation)
      assert {:ok, evidence_wire} = P.cleanup_ref(evidence, ref, generation)
      assert {:ok, current_wire} = P.current_link("fabricated-object", "resource-1", "last_evidence_ref", context)

      for wire <- [resource_wire, evidence_wire, current_wire] do
        assert {:error, :cleanup_reference_invalid} = AttemptBoundary.release(boundary, wire)
      end

      assert {:error, :cleanup_reference_stale} = AttemptBoundary.release(boundary, evidence)
      assert {:error, :invalid_request} = P.current_link("different", "resource-1", "last_evidence_ref", context)
      assert {:error, :namespace_mismatch} = P.resource(row, %{ref | project_namespace: "different"}, generation)
      # Corrected historical validation and encoding failures must also leave
      # the real owner's state, rows and durable bytes untouched.
      assert {:error, :invalid_request} = P.resource(%{row | state: :active}, ref, generation)
      assert {:error, :invalid_request} = P.resource(%{row | revision: 7}, ref, generation)
      assert {:error, :invalid_request} = P.resource(%{row | last_evidence_ref: "fabricated-object"}, ref, generation)
      invalid_context = %{context | object_id: "é"}
      assert {:error, :unencodable_p01_value} = P.current_link("é", "resource-1", "last_evidence_ref", invalid_context)
      assert {:error, :unencodable_p01_value} = P.restore_current_link(current_wire, "é", "resource-1", "last_evidence_ref", invalid_context)
      assert :sys.get_state(boundary) == state_before
      assert :dets.foldl(fn item, acc -> [item | acc] end, [], table) |> Enum.sort() == rows_before
      assert File.read!(path) == bytes_before
    after
      if Process.alive?(boundary), do: GenServer.stop(boundary)
      Process.unregister(:p08_t02_projection_test_owner)
      File.rm_rf!(root)
    end
  end
end
