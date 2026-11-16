defmodule SymphonyElixir.AttemptLedgerPilotTest do
  use ExUnit.Case

  alias SymphonyElixir.AgentRuntime.AttemptLedger
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  @identity %{tracker_kind: "memory", provider_scope: %{project_slug: "pilot-project"}}

  setup do
    root = Path.join(System.tmp_dir!(), "symphony-pilot-ledger-#{System.unique_integer([:positive])}")
    File.mkdir_p!(root)
    on_exit(fn -> File.rm_rf(root) end)
    {:ok, path: Path.join(root, "attempts.dets")}
  end

  test "pilot grant can be configured once and consumed once across reopen", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    grant = grant()
    identity = runtime_identity()

    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, %{state: :configured, grant: ^grant}} = AttemptLedger.pilot_status(ledger)
    assert {:error, :pilot_binding_required} = AttemptLedger.begin_attempt(ledger, grant.work_item_id)

    assert {:ok, %{lineage_id: "lineage-1"}} =
             AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)

    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)

    assert {:ok, %{state: :consumed, runtime_identity: ^identity}} =
             AttemptLedger.consume_pilot(ledger, grant, identity)

    assert :ok = AttemptLedger.validate_pilot_attempt(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)
    assert {:error, :pilot_launch_already_claimed} = AttemptLedger.claim_pilot_launch(ledger, grant, identity)
    assert :ok = AttemptLedger.close(ledger)

    {:ok, reopened} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert {:ok, %{state: :running, runtime_identity: ^identity}} = AttemptLedger.pilot_status(reopened)
    assert {:error, :pilot_already_consumed} = AttemptLedger.consume_pilot(reopened, grant, identity)
    assert {:error, :pilot_grant_immutable} = AttemptLedger.configure_pilot(reopened, %{grant | work_item_id: "other"})
    assert :ok = AttemptLedger.close(reopened)
  end

  test "a pilot grant rejects a different runtime identity", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    grant = grant()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, runtime_identity())
    other_identity = %{runtime_identity() | runtime_attempt_id: "other"}

    assert {:error, :pilot_binding_mismatch} =
             AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, other_identity)

    assert {:ok, %{state: :configured}} = AttemptLedger.pilot_status(ledger)
    assert :ok = AttemptLedger.close(ledger)
  end

  test "configured allowance survives restart before first binding", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    grant = grant()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert :ok = AttemptLedger.close(ledger)

    {:ok, reopened} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert {:ok, %{state: :configured, grant: ^grant}} = AttemptLedger.pilot_status(reopened)
    assert {:ok, %{lineage_id: "lineage-1"}} = AttemptLedger.begin_attempt(reopened, grant.work_item_id, pilot_binding: grant)
    other_role = %{grant | responsibility: "review"}

    assert {:error, :pilot_binding_mismatch} =
             AttemptLedger.begin_attempt(reopened, grant.work_item_id, pilot_binding: other_role)

    assert :ok = AttemptLedger.close(reopened)
  end

  test "only a planning responsibility can bind a pilot allowance", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert {:error, :invalid_pilot_grant} = AttemptLedger.configure_pilot(ledger, %{grant() | responsibility: "review"})
    assert :not_found = AttemptLedger.pilot_status(ledger)
    assert :ok = AttemptLedger.close(ledger)
  end

  test "failed DETS sync does not authorize pilot consumption", %{path: path} do
    Process.put(:pilot_sync_result, :ok)
    sync_fun = fn _table -> Process.get(:pilot_sync_result) end
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path, sync_fun: sync_fun)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)

    Process.put(:pilot_sync_result, {:error, :disk_error})
    assert {:error, {:ledger_sync_failed, :disk_error}} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(ledger)
    assert {:error, :pilot_already_consumed} = AttemptLedger.consume_pilot(ledger, grant, identity)
    Process.put(:pilot_sync_result, :ok)
    assert :ok = AttemptLedger.close(ledger)
    {:ok, reopened} = AttemptLedger.open("project-pilot", @identity, path: path)

    assert {:ok, %{state: :quarantined, runtime_identity: ^identity, result: nil}} =
             AttemptLedger.pilot_status(reopened)

    assert {:error, :pilot_already_consumed} = AttemptLedger.consume_pilot(reopened, grant, identity)
    assert :ok = AttemptLedger.close(reopened)
    Process.delete(:pilot_sync_result)
  end

  test "failed final-result sync replaces tentative success with durable quarantine", %{path: path} do
    Process.put(:pilot_sync_result, :ok)
    sync_fun = fn _table -> Process.get(:pilot_sync_result) end
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path, sync_fun: sync_fun)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)

    evidence = %{
      outcome: :completed,
      model_state: :completed,
      stop_disposition: :verified,
      final_answer: "A complete safe answer.",
      session_id: "session-1",
      thread_id: "thread-1",
      turn_id: "turn-1"
    }

    Process.put(:pilot_sync_result, {:error, :disk_error})
    assert {:error, {:ledger_sync_failed, :disk_error}} = AttemptLedger.persist_pilot_result(ledger, identity, evidence)
    assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(ledger)
    Process.put(:pilot_sync_result, :ok)
    assert :ok = AttemptLedger.close(ledger)

    {:ok, reopened} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(reopened)
    assert :ok = AttemptLedger.close(reopened)
    Process.delete(:pilot_sync_result)
  end

  test "pilot result persists once and rejects secret-bearing or contradictory answers", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)

    evidence = %{
      outcome: :completed,
      model_state: :completed,
      stop_disposition: :verified,
      final_answer: "The bounded local pilot completed.",
      session_id: "session-1",
      thread_id: "thread-1",
      turn_id: "turn-1"
    }

    assert :ok = AttemptLedger.persist_pilot_result(ledger, identity, evidence)
    assert {:ok, %{state: :stopverified, result: ^evidence}} = AttemptLedger.pilot_status(ledger)

    assert {:error, :pilot_result_immutable} =
             AttemptLedger.persist_pilot_result(ledger, identity, %{evidence | final_answer: "Different"})

    assert :ok = AttemptLedger.close(ledger)

    {:ok, reopened} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert {:ok, %{state: :stopverified, result: ^evidence}} = AttemptLedger.pilot_status(reopened)
    assert :ok = AttemptLedger.close(reopened)
  end

  test "sensitive final answers quarantine the grant without storing answer bytes", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)

    evidence = %{
      outcome: :completed,
      model_state: :completed,
      stop_disposition: :verified,
      final_answer: "api_key=secret-value",
      session_id: "session-1",
      thread_id: "thread-1",
      turn_id: "turn-1"
    }

    assert {:error, :pilot_result_sensitive} = AttemptLedger.persist_pilot_result(ledger, identity, evidence)

    assert {:ok, %{state: :quarantined, result: nil, quarantine_reason: :sensitive_final_answer}} =
             AttemptLedger.pilot_status(ledger)

    assert :ok = AttemptLedger.close(ledger)
  end

  test "generic attempt paths cannot rearm or replace a consumed pilot", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:error, :pilot_binding_mismatch} = AttemptLedger.begin_attempt(ledger, "other-item", pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)

    assert {:error, :pilot_allowance_consumed} = AttemptLedger.begin_attempt(ledger, grant.work_item_id)
    assert {:error, :pilot_allowance_consumed} = AttemptLedger.fence_attempt(ledger, grant.work_item_id)

    assert {:error, :pilot_allowance_consumed} =
             AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)

    assert {:error, :pilot_allowance_consumed} = AttemptLedger.rearm(ledger, grant.work_item_id, "retry", "operator", 1)
    assert :ok = AttemptLedger.close(ledger)
  end

  test "quarantine is terminal and stores only an allowlisted reason", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)
    assert :ok = AttemptLedger.quarantine_pilot(ledger, identity, :worker_lost)

    assert {:ok, %{state: :quarantined, result: nil, quarantine_reason: :worker_lost}} =
             AttemptLedger.pilot_status(ledger)

    assert :ok = AttemptLedger.quarantine_pilot(ledger, identity, :worker_lost)
    assert {:error, :invalid_pilot_quarantine_reason} = AttemptLedger.quarantine_pilot(ledger, identity, :arbitrary)
    assert :ok = AttemptLedger.close(ledger)
  end

  test "uncertain stop preserves safe final evidence and the model completion fact", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)

    evidence = %{
      outcome: :failed,
      model_state: :completed,
      stop_disposition: :quarantined,
      final_answer: "The model completed, but process termination was not confirmed.",
      session_id: "session-1",
      thread_id: "thread-1",
      turn_id: "turn-1"
    }

    assert :ok = AttemptLedger.persist_pilot_result(ledger, identity, evidence)

    assert {:ok, %{state: :quarantined, quarantine_reason: :termination_unconfirmed, result: ^evidence}} =
             AttemptLedger.pilot_status(ledger)

    assert {:error, :pilot_result_immutable} = AttemptLedger.persist_pilot_result(ledger, identity, evidence())
    assert :ok = AttemptLedger.close(ledger)

    {:ok, reopened} = AttemptLedger.open("project-pilot", @identity, path: path)

    assert {:ok, %{state: :quarantined, quarantine_reason: :termination_unconfirmed, result: ^evidence}} =
             AttemptLedger.pilot_status(reopened)

    assert :ok = AttemptLedger.close(reopened)
  end

  test "a failed final-result sync never exposes a verified result", %{path: path} do
    Process.put(:pilot_sync_result, :ok)
    sync_fun = fn _table -> Process.get(:pilot_sync_result) end
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path, sync_fun: sync_fun)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)

    evidence = %{
      outcome: :completed,
      model_state: :completed,
      stop_disposition: :verified,
      final_answer: "A complete safe answer.",
      session_id: "session-1",
      thread_id: "thread-1",
      turn_id: "turn-1"
    }

    Process.put(:pilot_sync_result, {:error, :disk_error})
    assert {:error, {:ledger_sync_failed, :disk_error}} = AttemptLedger.persist_pilot_result(ledger, identity, evidence)
    assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(ledger)
    Process.put(:pilot_sync_result, :ok)
    assert :ok = AttemptLedger.close(ledger)

    {:ok, reopened} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(reopened)
    assert :ok = AttemptLedger.close(reopened)
    Process.delete(:pilot_sync_result)
  end

  test "quarantine fallback hides an unsynced final result if the injected writer also fails", %{path: path} do
    Process.put(:pilot_sync_result, :ok)

    write_fun = fn
      _table, [{_key, %{state: :quarantined}}] -> {:error, :quarantine_write_failed}
      table, records -> :dets.insert(table, records)
    end

    sync_fun = fn _table -> Process.get(:pilot_sync_result) end
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path, write_fun: write_fun, sync_fun: sync_fun)
    grant = grant()
    identity = runtime_identity()
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)

    Process.put(:pilot_sync_result, {:error, :disk_error})

    assert {:error, {:ledger_sync_failed, :disk_error}} =
             AttemptLedger.persist_pilot_result(ledger, identity, evidence())

    assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(ledger)
    Process.put(:pilot_sync_result, :ok)
    assert :ok = AttemptLedger.close(ledger)

    {:ok, reopened} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(reopened)
    assert :ok = AttemptLedger.close(reopened)
    Process.delete(:pilot_sync_result)
  end

  test "legacy mode cannot disable a configured pilot", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert :ok = AttemptLedger.close(ledger)
    assert :ok = AttemptLedger.configured_mode("legacy", "project-pilot", @identity, path: path)

    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert :ok = AttemptLedger.configure_pilot(ledger, grant())
    assert :ok = AttemptLedger.close(ledger)

    assert {:error, :binding_downgrade_denied} = AttemptLedger.configured_mode("legacy", "project-pilot", @identity, path: path)
    assert :ok = AttemptLedger.configured_mode("legacy", "project-pilot", @identity, path: path, pilot_runtime: true)
  end

  test "legacy mode rejects invalid arguments without resolving a ledger path" do
    assert {:error, :invalid_request} = AttemptLedger.configured_mode("legacy", nil, @identity, [])
    assert {:error, :invalid_request} = AttemptLedger.configured_mode("legacy", "project-pilot", nil, [])
    assert {:error, :invalid_request} = AttemptLedger.configured_mode("legacy", "project-pilot", @identity, :invalid)
  end

  test "reopen rejects an invalid pilot row in the real DETS table", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    assert :ok = AttemptLedger.configure_pilot(ledger, grant())
    assert :ok = AttemptLedger.close(ledger)

    assert {:ok, ^path} = :dets.open_file(path, file: String.to_charlist(path), type: :set)
    [{{:pilot, "project-pilot"}, pilot}] = :dets.lookup(path, {:pilot, "project-pilot"})
    assert :ok = :dets.insert(path, {{:pilot, "project-pilot"}, Map.put(pilot, :unexpected, true)})
    assert :ok = :dets.sync(path)
    assert :ok = :dets.close(path)

    assert {:error, {:corrupt_attempt_record, {:pilot, "project-pilot"}, :invalid_record}} =
             AttemptLedger.open("project-pilot", @identity, path: path)
  end

  test "concurrent grant, launch, and result transitions have one immutable winner", %{path: path} do
    {:ok, ledger} = AttemptLedger.open("project-pilot", @identity, path: path)
    first = grant()
    second = %{first | source_commit: String.duplicate("d", 40)}

    configured = concurrent([first, second], &AttemptLedger.configure_pilot(ledger, &1))
    assert Enum.count(configured, &(&1 == :ok)) == 1
    assert Enum.count(configured, &(&1 == {:error, :pilot_grant_immutable})) == 1, inspect(configured)
    {:ok, %{grant: winner}} = AttemptLedger.pilot_status(ledger)

    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, winner.work_item_id, pilot_binding: winner)
    identity = runtime_identity()
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, winner.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, winner, identity)

    claimed = concurrent(1..12, fn _ -> AttemptLedger.claim_pilot_launch(ledger, winner, identity) end)
    assert Enum.count(claimed, &(&1 == :ok)) == 1
    assert Enum.count(claimed, &(&1 == {:error, :pilot_launch_already_claimed})) == 11

    evidence = fn answer ->
      %{
        outcome: :completed,
        model_state: :completed,
        stop_disposition: :verified,
        final_answer: answer,
        session_id: "session-1",
        thread_id: "thread-1",
        turn_id: "turn-1"
      }
    end

    results = concurrent([evidence.("first"), evidence.("second")], &AttemptLedger.persist_pilot_result(ledger, identity, &1))
    assert Enum.count(results, &(&1 == :ok)) == 1
    assert Enum.count(results, &(&1 == {:error, :pilot_result_immutable})) == 1
    assert :ok = AttemptLedger.close(ledger)
  end

  defp concurrent(items, fun) do
    items
    |> Task.async_stream(fun, max_concurrency: 16, timeout: 5_000, ordered: false)
    |> Enum.map(fn {:ok, result} -> result end)
  end

  defp grant do
    %{
      project_id: "project-pilot",
      plane_project_id: "11111111-1111-4111-8111-111111111111",
      work_item_id: "22222222-2222-4222-8222-222222222222",
      responsibility: "planning",
      source_commit: String.duplicate("a", 40),
      source_tree: String.duplicate("b", 40),
      config_identity: String.duplicate("c", 64),
      runtime_lineage: "lineage-1",
      deadline_ms: 60_000
    }
  end

  defp evidence do
    %{
      outcome: :completed,
      model_state: :completed,
      stop_disposition: :verified,
      final_answer: "A complete safe answer.",
      session_id: "session-1",
      thread_id: "thread-1",
      turn_id: "turn-1"
    }
  end

  defp runtime_identity do
    %Identity{
      runtime_attempt_id: "attempt-1",
      work_item_id: "22222222-2222-4222-8222-222222222222",
      lineage_generation: "lineage-1",
      responsibility: "planning",
      runtime_profile: "pilot-planner"
    }
  end
end
