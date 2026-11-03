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

  test "configured schema and mode preserve legacy and missing-file outcomes", %{root: root} do
    assert {:ok, 1, false} = AttemptLedger.configured_schema(@namespace, @identity, root: root)
    assert :ok = AttemptLedger.configured_mode("legacy", @namespace, @identity, root: root)

    assert {:error, :migration_required} =
             AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, root: root)

    assert {:error, :migration_required} =
             AttemptLedger.configured_schema(@namespace, @identity, path: Path.join(root, "missing.dets"))

    assert {:error, :invalid_request} = AttemptLedger.configured_schema(nil, @identity, root: root)
    assert {:error, :invalid_request} = AttemptLedger.configured_mode("unknown", @namespace, @identity, root: root)
    assert {:error, :gate2_profile_incomplete} = AttemptLedger.configured_mode("gate2_enforced", @namespace, @identity, root: root)
  end

  test "configured mode detects Gate2 history in an admitted schema two ledger", %{root: root} do
    path = seed_committed_schema2(root)

    assert {:ok, 2, true} = AttemptLedger.configured_schema(@namespace, @identity, path: path)
    assert :ok = AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, path: path)

    assert {:error, :binding_downgrade_denied} =
             AttemptLedger.configured_mode("legacy", @namespace, @identity, path: path)

    assert {:error, :gate2_profile_incomplete} =
             AttemptLedger.configured_mode("gate2_enforced", @namespace, @identity, path: path)
  end

  test "configured schema rejects malformed Gate2 history", %{root: root} do
    path = seed_committed_schema2(root, true)

    assert {:error, :storage_corrupt} = AttemptLedger.configured_schema(@namespace, @identity, path: path)

    assert {:error, :storage_corrupt} =
             AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, path: path)
  end

  test "configured schema denies schema two metadata without a committed receipt", %{ledger: ledger, root: root} do
    _ledger = install_gate2_record(ledger, "uncommitted", %{in_flight: false, authority_fence: nil})

    assert {:error, :migration_in_progress} = AttemptLedger.configured_schema(@namespace, @identity, root: root)

    assert {:error, :migration_in_progress} =
             AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, root: root)
  end

  test "configured schema rejects unsupported stored versions", %{ledger: ledger, root: root} do
    :ok = :dets.insert(ledger.table, {{:meta, @namespace}, %{schema_version: 99}})
    :ok = :dets.sync(ledger.table)

    assert {:error, :unsupported_schema} = AttemptLedger.configured_schema(@namespace, @identity, root: root)

    assert {:error, :unsupported_schema} =
             AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, root: root)
  end

  test "requested Gate2 fence reference is read from durable lineage", %{ledger: ledger} do
    identity = %Identity{
      runtime_attempt_id: "attempt-requested",
      work_item_id: "requested-item",
      lineage_generation: "lineage-requested",
      responsibility: "implementation",
      runtime_profile: "implementation"
    }

    reference = %{
      grant_id: "grant-requested",
      project_namespace: @namespace,
      runtime_identity: identity,
      fence_epoch: 1,
      grant_sha256: String.duplicate("a", 64)
    }

    gate2_fence = %{reference: reference, status: :requested}

    ledger =
      install_gate2_record(ledger, "requested-item", %{
        in_flight: true,
        authority_fence: %{
          state: :bound,
          runtime_attempt: identity,
          route_fingerprint: nil,
          gate2_fence: gate2_fence
        },
        boundary_binding: %{
          kind: :gate2,
          binding_version: 1,
          lineage_binding_id: "requested-binding",
          resource_ledger_namespace: @namespace
        }
      })

    assert {:ok, ^reference} = AttemptLedger.gate2_fence_reference(ledger, "requested-item")
  end

  test "durable Gate2 binding requires the boundary owner process", %{root: root} do
    path = seed_committed_schema2(root)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity, path: path)
    on_exit(fn -> AttemptLedger.close(ledger) end)

    assert {:error, :gate2_boundary_required} =
             AttemptLedger.bind_gate2_fence_from_boundary(ledger, "issue", %{})
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

    record = Map.merge(record, overrides) |> Map.put_new(:boundary_binding, @gate2_binding)
    :ok = :dets.insert(ledger.table, {{:current, issue_id}, record})
    :ok = :dets.insert(ledger.table, {{:meta, @namespace}, %{schema_version: 2, project_namespace: @namespace, tracker_identity: @identity}})
    :ok = :dets.sync(ledger.table)
    %{ledger | schema_version: 2}
  end

  defp current!(ledger, issue_id) do
    assert {:ok, record} = AttemptLedger.current(ledger, issue_id)
    record
  end

  defp seed_committed_schema2(root, malformed_history? \\ false) do
    migration_root = Path.join(root, "committed-schema2")
    File.mkdir_p!(migration_root)
    path = AttemptLedger.path_for(@namespace, root: migration_root)
    {:ok, legacy} = AttemptLedger.open(@namespace, @identity, path: path)
    :ok = AttemptLedger.close(legacy)

    request = %{
      project_namespace: @namespace,
      tracker_identity_sha256:
        @identity
        |> :erlang.term_to_binary([:deterministic])
        |> then(&:crypto.hash(:sha256, &1))
        |> Base.encode16(case: :lower),
      authority_ref: "compatibility-test-schema2-receipt",
      source_schema: 1,
      target_schema: 2
    }

    encoded = request |> :erlang.term_to_binary([:deterministic]) |> Base.encode64()
    code_args = Enum.flat_map(:code.get_path(), fn code_path -> ["-pa", List.to_string(code_path)] end)

    script =
      "request = System.argv() |> Enum.at(1) |> Base.decode64!() |> :erlang.binary_to_term([:safe]); path = System.argv() |> Enum.at(0); Application.put_env(:symphony_elixir, :attempt_ledger_root, Path.dirname(path)); result = SymphonyElixir.AgentRuntime.AttemptLedgerMigration.migrate_v1_to_v2(path, request); IO.inspect(result)"

    {output, 0} =
      System.cmd(System.find_executable("elixir"), code_args ++ ["-e", script, "--", path, encoded], stderr_to_stdout: true)

    assert output =~ "{:ok,"

    record = %{
      schema_version: 2,
      project_namespace: @namespace,
      issue_id: "compatibility-history",
      lineage_id: "compatibility-lineage",
      safety_counters: %{ordinary_failures: 0, ordinary_retries: 0, review_cycles: 0},
      status: :closed,
      stop_reason: nil,
      route_fingerprint: nil,
      in_flight: false,
      authority_fence: nil,
      close_pending: false,
      updated_at: 1_700_000_000_000,
      closed_reason: :completed,
      rearm_reason: nil,
      rearmed_by: nil,
      rearmed_at: nil,
      boundary_binding: %{
        kind: :gate2,
        binding_version: 1,
        lineage_binding_id: "compatibility-binding",
        resource_ledger_namespace: @namespace
      }
    }

    table = :gate2_attempt_compatibility_receipt
    {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(path), type: :set)
    :ok = :dets.insert(table, {{:history, "compatibility-lineage"}, record})

    if malformed_history? do
      :ok = :dets.insert(table, {{:history, "broken-history"}, :corrupt})
    end

    :ok = :dets.sync(table)
    :ok = :dets.close(table)
    path
  end
end
