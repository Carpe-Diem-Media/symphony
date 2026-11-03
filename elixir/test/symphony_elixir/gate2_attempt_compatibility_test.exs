defmodule SymphonyElixir.Gate2AttemptCompatibilityTest do
  use ExUnit.Case, async: false

  alias SymphonyElixir.AgentRuntime.AttemptLedger
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.WorkControl.SuspensionContext

  @namespace "compatibility-test"
  @identity %{tracker_kind: "memory", provider_scope: %{project_slug: @namespace}}
  @gate2_binding %{
    kind: :gate2,
    binding_version: 1,
    lineage_binding_id: "binding-a",
    resource_ledger_namespace: "resources-a"
  }

  setup do
    root = Path.join(System.tmp_dir!(), "gate2-compat-#{System.unique_integer([:positive])}")
    File.rm_rf!(root)
    File.mkdir_p!(root)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity, root: root)

    on_exit(fn ->
      AttemptLedger.close(ledger)
      File.rm_rf!(root)
    end)

    {:ok, %{root: root, ledger: ledger}}
  end

  test "legacy release remains valid for legacy binding", %{ledger: ledger} do
    assert {:ok, record} = AttemptLedger.begin_attempt(ledger, "legacy")
    assert :ok = AttemptLedger.release_armed_authority_fence(ledger, "legacy")
    assert {:ok, released} = AttemptLedger.current(ledger, "legacy")
    assert released.authority_fence.state == :released
    assert released.schema_version == record.schema_version
  end

  test "legacy release rejects gate2 bound and already-released records", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{in_flight: true, authority_fence: %{state: :armed}})
    before = current!(ledger, "gate2")

    assert {:error, :attempt_resource_verification_required} = AttemptLedger.release_armed_authority_fence(ledger, "gate2")
    assert current!(ledger, "gate2") == before

    ledger = install_gate2_record(ledger, "released", %{in_flight: false, authority_fence: %{state: :released}})
    before = current!(ledger, "released")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.release_armed_authority_fence(ledger, "released")
    assert current!(ledger, "released") == before
  end

  test "put cannot remove or replace gate2 binding", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{in_flight: false, authority_fence: nil})
    record = current!(ledger, "gate2")

    for rewritten <- [Map.delete(record, :boundary_binding), Map.put(record, :boundary_binding, %{kind: :legacy})] do
      assert {:error, :attempt_resource_verification_required} = AttemptLedger.put(ledger, rewritten)
      assert current!(ledger, "gate2") == record
    end

    fresh_gate2 = %{record | issue_id: "fresh", lineage_id: "lineage-fresh"}
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.put(ledger, fresh_gate2)
    assert :not_found = AttemptLedger.current(ledger, "fresh")
  end

  test "put rejects same-binding lineage replacement", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{in_flight: false, authority_fence: nil})
    record = current!(ledger, "gate2")

    assert {:error, :attempt_resource_verification_required} =
             AttemptLedger.put(ledger, %{record | lineage_id: "lineage-replaced"})

    assert current!(ledger, "gate2") == record
  end

  test "put rejects same-binding released fence injection", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{in_flight: false, authority_fence: nil})
    record = current!(ledger, "gate2")

    assert {:error, :attempt_resource_verification_required} =
             AttemptLedger.put(ledger, %{record | authority_fence: %{state: :released}})

    assert current!(ledger, "gate2") == record
  end

  test "put cannot overwrite a corrupt gate2 binding", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "corrupt", %{in_flight: false, authority_fence: nil})
    record = current!(ledger, "corrupt")
    corrupt = %{record | boundary_binding: %{kind: :gate2, binding_version: 1}}
    :ok = :dets.insert(ledger.table, {{:current, "corrupt"}, corrupt})
    :ok = :dets.sync(ledger.table)

    assert {:error, :invalid_record} = AttemptLedger.put(ledger, Map.put(record, :boundary_binding, %{kind: :legacy}))
    assert {:error, :invalid_record} = AttemptLedger.current(ledger, "corrupt")
  end

  test "safety clear close fence and rearm cannot downgrade binding", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{status: :open, in_flight: true, authority_fence: %{state: :armed}})
    before = current!(ledger, "gate2")

    identity = %Identity{
      runtime_attempt_id: "attempt-a",
      work_item_id: "gate2",
      lineage_generation: before.lineage_id,
      responsibility: "implementation",
      runtime_profile: "implementation"
    }

    safety_result = AttemptLedger.persist_safety(ledger, "gate2", before.safety_counters, in_flight: false)
    assert {:error, :attempt_resource_verification_required} = safety_result
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.clear_in_flight(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.close_lineage(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.confirm_lineage_close(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.bind_runtime_attempt(ledger, "gate2", identity)
    suspension_result = AttemptLedger.mark_suspension_pending(ledger, "gate2", identity, %{})
    assert {:error, :attempt_resource_verification_required} = suspension_result
    release_result = AttemptLedger.release_authority_fence(ledger, "gate2", identity)
    assert {:error, :attempt_resource_verification_required} = release_result

    assert {:error, :attempt_resource_verification_required} =
             AttemptLedger.release_suspension_fence(ledger, "gate2", identity, %SuspensionContext{})

    assert {:error, :attempt_resource_verification_required} = AttemptLedger.release_armed_authority_fence(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.begin_attempt(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.fence_attempt(ledger, "gate2")
    assert {:error, :gate2_boundary_required} = AttemptLedger.rearm(ledger, "gate2", "reason", "operator", 1)
    assert current!(ledger, "gate2") == before

    ledger = install_gate2_record(ledger, "idle", %{status: :open, in_flight: false, authority_fence: nil})
    idle_before = current!(ledger, "idle")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.begin_attempt(ledger, "idle")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.fence_attempt(ledger, "idle")
    assert current!(ledger, "idle") == idle_before

    ledger = install_gate2_record(ledger, "closed", %{status: :closed, in_flight: false, authority_fence: nil})
    closed_before = current!(ledger, "closed")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.begin_attempt(ledger, "closed")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.fence_attempt(ledger, "closed")
    assert current!(ledger, "closed") == closed_before
  end

  defp install_gate2_record(ledger, issue_id, overrides) do
    record = %{
      schema_version: 2,
      project_namespace: @namespace,
      issue_id: issue_id,
      lineage_id: "lineage-#{issue_id}",
      safety_counters: %{ordinary_failures: 0, ordinary_retries: 0, review_cycles: 0},
      status: :open,
      stop_reason: nil,
      route_fingerprint: nil,
      in_flight: false,
      authority_fence: nil,
      close_pending: false,
      updated_at: 1
    }

    record = Map.merge(record, overrides) |> Map.put(:boundary_binding, @gate2_binding)
    :ok = :dets.insert(ledger.table, {{:current, issue_id}, record})
    :ok = :dets.insert(ledger.table, {{:meta, @namespace}, %{schema_version: 2, project_namespace: @namespace, tracker_identity: @identity}})
    :ok = :dets.sync(ledger.table)
    %{ledger | schema_version: 2}
  end

  defp current!(ledger, issue_id) do
    assert {:ok, record} = AttemptLedger.current(ledger, issue_id)
    record
  end
end
