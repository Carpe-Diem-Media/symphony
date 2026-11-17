defmodule SymphonyElixir.PilotProbeRunner do
  def run(issue, recipient, opts) do
    send(recipient, {:pilot_probe_started, issue.id, opts})

    receive do
      :finish -> :ok
    end
  end
end

defmodule SymphonyElixir.PilotOrchestratorTest do
  use SymphonyElixir.TestSupport

  alias SymphonyElixir.AgentRuntime.{AttemptLedger, Profile, Route, RuntimeAttempt}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  setup do
    project = "pilot-orchestrator-#{System.unique_integer([:positive])}"
    {:ok, ledger} = AttemptLedger.open(project, Tracker.identity(Config.settings!().tracker))
    supervisor = start_supervised!({Task.Supervisor, []})
    item = "22222222-2222-4222-8222-222222222222"

    grant = %{
      project_id: project,
      plane_project_id: "11111111-1111-4111-8111-111111111111",
      work_item_id: item,
      responsibility: "planning",
      source_commit: String.duplicate("a", 40),
      source_tree: String.duplicate("b", 40),
      config_identity: String.duplicate("c", 64),
      runtime_lineage: "pilot-lineage",
      deadline_ms: 500
    }

    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    issue = %Issue{id: item, identifier: "DISPOSABLE-1", title: "Synthetic pilot", state: "Planning", project_id: grant.plane_project_id}
    profile = Profile.default_profiles("codex app-server", 1)["planner"]

    route = %Route{
      issue_id: item,
      starting_state: "Planning",
      profile_name: "planner",
      runtime_name: "codex",
      responsibility: "planning",
      fingerprint: "pilot-route",
      profile: profile
    }

    assert {:ok, record} = AttemptLedger.begin_attempt(ledger, item, pilot_binding: grant)
    identity = Identity.allocate(item, route, record.lineage_id)
    attempt = RuntimeAttempt.new(identity, :starting)

    state = %Orchestrator.State{
      attempt_ledger: ledger,
      attempt_ledger_status: :ready,
      pilot_binding: grant,
      task_supervisor: supervisor,
      agent_runner: SymphonyElixir.PilotProbeRunner,
      codex_totals: %{input_tokens: 0, output_tokens: 0, total_tokens: 0, seconds_running: 0}
    }

    on_exit(fn -> AttemptLedger.close(ledger) end)
    {:ok, ledger: ledger, grant: grant, issue: issue, route: route, attempt: attempt, state: state}
  end

  test "consumes and synchronizes before exactly one worker spawn", ctx do
    state = spawn_attempt(ctx)
    assert_receive {:pilot_probe_started, _, opts}
    assert opts[:pilot_binding] == ctx.grant
    assert opts[:attempt_ledger].path == ctx.ledger.path
    assert is_integer(opts[:absolute_deadline_ms])
    assert {:ok, %{state: :consumed}} = AttemptLedger.pilot_status(ctx.ledger)
    second = Orchestrator.spawn_prepared_issue_for_test(state, ctx.issue, ctx.route, nil, self(), nil, ctx.attempt)
    assert map_size(second.running) == 1
    refute_receive {:pilot_probe_started, _, _}, 50
  end

  test "consumption sync failure cannot reach worker spawn", ctx do
    ledger = %{ctx.ledger | sync_fun: fn _ -> {:error, :synthetic_sync_failure} end}
    state = spawn_attempt(%{ctx | state: %{ctx.state | attempt_ledger: ledger}})
    assert state.running == %{}
    refute_receive {:pilot_probe_started, _, _}, 50
  end

  test "the absolute deadline kills only this worker and retains its fence", ctx do
    state = spawn_attempt(ctx)
    assert_receive {:pilot_probe_started, _, _}
    assert_receive {:pilot_attempt_deadline, item, identity}, 1_500
    assert item == ctx.issue.id
    assert identity == ctx.attempt.identity
    {:noreply, timed_out} = Orchestrator.handle_info({:pilot_attempt_deadline, item, identity}, state)
    assert_receive {:DOWN, _, :process, _, :killed}, 1_000
    assert timed_out.running[item].containment_status == :unconfirmed
    assert {:ok, %{in_flight: true}} = AttemptLedger.current(ctx.ledger, item)
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, item, pilot_binding: ctx.grant)
  end

  test "route changes and alternate prepared paths cannot spend a consumed grant", ctx do
    state = spawn_attempt(ctx)
    assert_receive {:pilot_probe_started, _, _}
    builder = %{ctx.route | responsibility: "implementation", profile_name: "builder"}
    attempt = RuntimeAttempt.new(Identity.allocate(ctx.issue.id, builder, ctx.grant.runtime_lineage), :starting)
    _ = Orchestrator.spawn_prepared_issue_for_test(state, %{ctx.issue | state: "Ready"}, builder, nil, self(), nil, attempt)
    refute_receive {:pilot_probe_started, _, _}, 50
    {:noreply, _} = Orchestrator.handle_info({:retry_issue, ctx.issue.id, make_ref()}, state)
    refute_receive {:pilot_probe_started, _, _}, 50
  end

  test "a second eligible Planning item cannot use this allowance", ctx do
    state = spawn_attempt(ctx)
    assert_receive {:pilot_probe_started, _, _}
    other = %{ctx.issue | id: "44444444-4444-4444-8444-444444444444", identifier: "DISPOSABLE-2"}
    route = %{ctx.route | issue_id: other.id}
    attempt = RuntimeAttempt.new(Identity.allocate(other.id, route, ctx.grant.runtime_lineage), :starting)
    denied = Orchestrator.spawn_prepared_issue_for_test(state, other, route, nil, self(), nil, attempt)
    assert map_size(denied.running) == 1
    refute Map.has_key?(denied.running, other.id)
    refute_receive {:pilot_probe_started, _, _}, 50
  end

  test "a stale deadline cannot terminate the current worker", ctx do
    state = spawn_attempt(ctx)
    assert_receive {:pilot_probe_started, _, _}
    stale = %{ctx.attempt.identity | runtime_attempt_id: "stale-attempt"}
    {:noreply, unchanged} = Orchestrator.handle_info({:pilot_attempt_deadline, ctx.issue.id, stale}, state)
    assert unchanged == state
    assert Process.alive?(state.running[ctx.issue.id].pid)
    assert {:ok, %{state: :consumed}} = AttemptLedger.pilot_status(ctx.ledger)
  end

  test "a delayed deadline preserves synchronized stop evidence while DOWN is pending", ctx do
    state = spawn_attempt(ctx)
    assert_receive {:pilot_probe_started, _, _}
    identity = ctx.attempt.identity
    assert :ok = AttemptLedger.claim_pilot_launch(ctx.ledger, ctx.grant, identity)

    evidence = %{
      outcome: :completed,
      model_state: :completed,
      stop_disposition: :verified,
      final_answer: "A safe final plan.",
      session_id: "session-1",
      thread_id: "thread-1",
      turn_id: "turn-1"
    }

    assert :ok = AttemptLedger.persist_pilot_result(ctx.ledger, identity, evidence)
    {:noreply, unchanged} = Orchestrator.handle_info({:pilot_attempt_deadline, ctx.issue.id, identity}, state)
    assert unchanged == state
    assert Process.alive?(state.running[ctx.issue.id].pid)
    assert {:ok, %{state: :stopverified, result: ^evidence}} = AttemptLedger.pilot_status(ctx.ledger)
    send(state.running[ctx.issue.id].pid, :finish)
  end

  defp spawn_attempt(ctx) do
    Orchestrator.spawn_prepared_issue_for_test(ctx.state, ctx.issue, ctx.route, nil, self(), nil, ctx.attempt)
  end
end
