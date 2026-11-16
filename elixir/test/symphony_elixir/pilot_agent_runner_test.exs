defmodule SymphonyElixir.PilotSyntheticRuntime do
  def start_session(_workspace, opts) do
    send(Keyword.fetch!(opts, :test_pid), {:synthetic_session, Keyword.get(opts, :absolute_deadline_ms)})

    if callback = opts[:test_after_session_start], do: callback.()

    case Keyword.get(opts, :test_behavior) do
      :startup_failure -> {:error, :synthetic_startup_failure}
      _ -> {:ok, %{opts: opts}}
    end
  end

  def run_turn(session, prompt, _issue, opts) do
    if session.opts[:test_capture_prompt], do: send(session.opts[:test_pid], {:synthetic_prompt, prompt})
    send(Keyword.fetch!(session.opts, :test_pid), :synthetic_turn)
    answer = Keyword.get(session.opts, :test_answer, "The tracked file contains one constant. Plan: inspect its callers.")

    opts[:on_message].(%{
      event: :notification,
      timestamp: DateTime.utc_now(),
      payload: %{
        "method" => "item/completed",
        "params" => %{
          "item" => %{
            "type" => "agentMessage",
            "phase" => "final_answer",
            "id" => "final-1",
            "text" => answer
          }
        }
      },
      raw: "SENSITIVE_PROVIDER_METADATA_MUST_NOT_PERSIST"
    })

    if session.opts[:test_behavior] == :runtime_failure do
      {:error, {:synthetic_runtime_failure, "api_key=synthetic-error-secret"}}
    else
      {:ok, %{session_id: "session-1", thread_id: "thread-1", turn_id: "turn-1"}}
    end
  end

  def stop_session(session) do
    send(Keyword.fetch!(session.opts, :test_pid), :synthetic_stopped)
    if session.opts[:test_behavior] == :uncertain_stop, do: {:error, {:containment_unconfirmed, :termination_timeout}}, else: :ok
  end
end

defmodule SymphonyElixir.PilotAgentRunnerTest do
  use SymphonyElixir.TestSupport

  alias SymphonyElixir.AgentRuntime.{AttemptLedger, Router, RuntimeAttempt}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.Config.Schema
  alias SymphonyElixir.WorkControl.{WorkflowLifecycle, WorkItem}

  @plane_project "11111111-1111-4111-8111-111111111111"
  @workspace "33333333-3333-4333-8333-333333333333"
  @item "22222222-2222-4222-8222-222222222222"
  @prompt "Inspect the small tracked file and return a short technical plan."

  defmodule IntegratedRunner do
    def run(issue, recipient, opts) do
      fixture = Application.fetch_env!(:symphony_elixir, :pilot_integrated_fixture)
      SymphonyElixir.AgentRunner.run(issue, recipient, Keyword.merge(fixture, opts))
    end
  end

  setup context do
    root = Path.dirname(Workflow.workflow_file_path())
    source = Path.join(root, "source")
    File.mkdir_p!(source)
    git!(source, ["init", "-q"])
    File.write!(Path.join(source, "sample.ex"), "defmodule Sample, do: def(value, do: 1)\n")
    git!(source, ["add", "sample.ex"])
    git!(source, ["-c", "user.name=Offline fixture", "-c", "user.email=offline@example.invalid", "-c", "commit.gpgSign=false", "commit", "-qm", "Synthetic fixture"])
    [commit, tree] = git!(source, ["rev-parse", "HEAD", "HEAD^{tree}"]) |> String.split()
    codex = Path.join(root, "codex")
    File.write!(codex, "#!/bin/sh\nexit 99\n")
    File.chmod!(codex, 0o700)

    policy_root = Path.join(root, "policies")
    File.mkdir_p!(policy_root)
    policy_path = Path.join(policy_root, "planner.md")
    File.write!(policy_path, "Role policy: synthetic approved Planner\nInspect source only.\n")
    prior_policy_root = Application.get_env(:symphony_elixir, :role_prompt_root)
    Application.put_env(:symphony_elixir, :role_prompt_root, policy_root)

    on_exit(fn ->
      if prior_policy_root do
        Application.put_env(:symphony_elixir, :role_prompt_root, prior_policy_root)
      else
        Application.delete_env(:symphony_elixir, :role_prompt_root)
      end
    end)

    raw = %{
      "symphony" => %{"project_id" => "pilot-runner"},
      "tracker" => %{"kind" => "plane", "api_key" => "$PLANE_API_KEY", "workspace_slug" => "disposable", "workspace_id" => @workspace, "project_id" => @plane_project},
      "workspace" => %{"root" => Path.join(root, "workspaces")},
      "agent" => %{"routing" => "routed", "max_concurrent_agents" => 1, "max_turns" => 20},
      "codex" => %{"command" => "#{codex} app-server"},
      "source_control" => %{
        "kind" => "github",
        "repository" => "offline/fixture",
        "repository_id" => 1,
        "base_branch" => "main",
        "token_env" => "SYNTHETIC_UNUSED_GITHUB_TOKEN",
        "required_checks" => [
          %{"context" => "offline", "app_id" => 1, "subject" => "head"}
        ]
      },
      "hooks" => %{"after_create" => "git -c core.hooksPath=/dev/null clone --local --no-hardlinks #{source} ."},
      "provider_project_contract" => %{
        schema_version: 1,
        provider: :plane,
        workspace_id: @workspace,
        project_id: @plane_project,
        state_mappings:
          Map.new(WorkflowLifecycle.states(), fn state ->
            {state, %{state_id: "state-#{state}", name: WorkflowLifecycle.display(state)}}
          end)
      }
    }

    raw =
      if context[:pilot_custom_policy] do
        File.cp!(policy_path, Path.join(policy_root, "approved-custom.md"))
        put_in(raw, ["agent", "profiles"], %{"planner" => %{"prompt" => "approved-custom"}})
      else
        raw
      end

    {:ok, settings} = Schema.parse(raw)

    grant = %{
      project_id: "pilot-runner",
      plane_project_id: @plane_project,
      work_item_id: @item,
      responsibility: "planning",
      source_commit: commit,
      source_tree: tree,
      config_identity: Config.pilot_configuration_identity(settings, @prompt),
      runtime_lineage: "owner-issued-synthetic-lineage",
      deadline_ms: 120_000
    }

    raw = put_in(raw, ["agent", "pilot"], grant)
    File.write!(Workflow.workflow_file_path(), "---\n" <> Jason.encode!(raw) <> "\n---\n" <> @prompt)
    assert :ok = WorkflowStore.force_reload()
    settings = Config.settings!()
    assert {:ok, ^grant} = Config.pilot_binding(settings)

    issue = %Issue{
      id: @item,
      identifier: "DISPOSABLE-1",
      state: "Planning",
      title: "Offline pilot",
      workspace_id: @workspace,
      project_id: @plane_project,
      provider_state_id: "state-planning",
      provider_state_group: :unstarted,
      dispatchable: true
    }

    {:ok, work_item} =
      WorkItem.from_issue(issue, %{
        provider: :plane,
        prior_validated_lifecycle_state: :planning,
        provider_project_contract: settings.provider_project_contract
      })

    assert {:ok, route} = Router.resolve(work_item, settings.agent.profiles, settings.agent.routes)
    {:ok, ledger} = AttemptLedger.open("pilot-runner", Tracker.identity(settings.tracker))
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)

    assert {:ok, record} =
             AttemptLedger.begin_attempt(ledger, @item,
               pilot_binding: grant,
               route_fingerprint: route.fingerprint
             )

    identity = Identity.allocate(@item, route, record.lineage_id)

    unless context[:integrated_dispatch] do
      assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, @item, identity)
      assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    end

    opts = [
      pilot_binding: grant,
      attempt_ledger: ledger,
      runtime_attempt_identity: identity,
      route: route,
      work_item: work_item,
      ownership_ledger: workspace_ownership_ledger(),
      runtime: SymphonyElixir.PilotSyntheticRuntime,
      test_pid: self(),
      test_runtime_isolation_admit: fn _, _, _ -> {:ok, %{synthetic: true}} end,
      issue_state_fetcher: fn _ -> flunk("Pilot must not fetch a continuation") end,
      plane_epoch_snapshot_reader: fn -> flunk("Pilot must not fetch a Plane continuation") end
    ]

    on_exit(fn -> AttemptLedger.close(ledger) end)

    fixture = %{
      issue: issue,
      opts: opts,
      ledger: ledger,
      grant: grant,
      identity: identity,
      route: route,
      policy_root: policy_root,
      policy_path: policy_path
    }

    {:ok, fixture}
  end

  test "persists the final answer and correlations before success, survives runtime removal and restart", ctx do
    recipient = self()
    worker = Task.async(fn -> AgentRunner.run(ctx.issue, recipient, ctx.opts) end)
    assert :ok = Task.await(worker)
    refute Process.alive?(worker.pid)
    assert_receive {:synthetic_session, deadline}
    assert is_integer(deadline)
    assert_receive :synthetic_turn
    assert_receive :synthetic_stopped
    refute_receive :synthetic_turn, 25
    assert {:ok, %{state: :stopverified, grant: grant, result: result}} = AttemptLedger.pilot_status(ctx.ledger)
    assert grant.source_commit == ctx.grant.source_commit
    assert result.outcome == :completed
    assert result.model_state == :completed
    assert result.stop_disposition == :verified
    assert result.final_answer == "The tracked file contains one constant. Plan: inspect its callers."
    assert {result.session_id, result.thread_id, result.turn_id} == {"session-1", "thread-1", "turn-1"}
    assert :ok = AttemptLedger.close(ctx.ledger)
    {:ok, reopened} = AttemptLedger.open("pilot-runner", ctx.ledger.tracker_identity, path: ctx.ledger.path)
    assert {:ok, %{result: ^result}} = AttemptLedger.pilot_status(reopened)
    refute String.contains?(inspect(AttemptLedger.pilot_status(reopened)), "SENSITIVE_PROVIDER_METADATA")
    assert_raise RuntimeError, ~r/Pilot launch refused/, fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
    AttemptLedger.close(reopened)
  end

  test "uncertain termination cannot produce a completed result", ctx do
    assert {:error, {:runtime_containment_unconfirmed, :termination_timeout}} =
             AgentRunner.run(ctx.issue, self(), Keyword.put(ctx.opts, :test_behavior, :uncertain_stop))

    assert {:ok, %{state: :quarantined}} = AttemptLedger.pilot_status(ctx.ledger)

    assert {:ok, %{result: %{model_state: :completed, stop_disposition: :quarantined, final_answer: answer}}} =
             AttemptLedger.pilot_status(ctx.ledger)

    assert answer =~ "Plan: inspect its callers."
    assert {:ok, %{in_flight: true}} = AttemptLedger.current(ctx.ledger, ctx.issue.id)
  end

  test "startup and runtime failures spend the allowance permanently", ctx do
    assert_raise RuntimeError, fn -> AgentRunner.run(ctx.issue, self(), Keyword.put(ctx.opts, :test_behavior, :startup_failure)) end
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
    refute_receive :synthetic_turn, 25
  end

  test "runtime failure records failure after a verified stop without granting retry", ctx do
    log =
      capture_log(fn ->
        error =
          assert_raise RuntimeError, fn ->
            AgentRunner.run(ctx.issue, self(), Keyword.put(ctx.opts, :test_behavior, :runtime_failure))
          end

        refute error.message =~ "synthetic-error-secret"
      end)

    refute log =~ "synthetic-error-secret"

    assert {:ok, %{state: :stopverified, result: %{outcome: :failed, stop_disposition: :verified}}} =
             AttemptLedger.pilot_status(ctx.ledger)

    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
  end

  test "final evidence sync failure cannot return success or expose a verified final record", ctx do
    calls = :atomics.new(1, [])

    ledger = %{
      ctx.ledger
      | sync_fun: fn table ->
          if :atomics.add_get(calls, 1, 1) == 2, do: {:error, :synthetic_final_sync_failure}, else: :dets.sync(table)
        end
    }

    opts = Keyword.put(ctx.opts, :attempt_ledger, ledger)

    assert_raise RuntimeError, ~r/Pilot final evidence persistence failed/, fn ->
      AgentRunner.run(ctx.issue, self(), opts)
    end

    refute match?({:ok, %{state: :stopverified}}, AttemptLedger.pilot_status(ledger))
    assert {:error, _} = AttemptLedger.begin_attempt(ledger, ctx.issue.id, pilot_binding: ctx.grant)
  end

  test "a changed tracked checkout cannot start the synthetic model", ctx do
    {:ok, workspace} = Workspace.create_for_issue(ctx.issue, nil, ctx.opts[:ownership_ledger])
    File.write!(Path.join(workspace, "sample.ex"), "changed tracked bytes\n")
    assert_raise RuntimeError, fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
    refute_receive {:synthetic_session, _}, 25
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
  end

  test "untracked source outside the pinned tree cannot enter the pilot workspace", ctx do
    {:ok, workspace} = Workspace.create_for_issue(ctx.issue, nil, ctx.opts[:ownership_ledger])
    File.write!(Path.join(workspace, "unexpected.ex"), "untracked source\n")
    assert_raise RuntimeError, fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
    refute_receive {:synthetic_session, _}, 25
  end

  for prior_state <- [:consumed, :running] do
    @tag pilot_recovery_state: prior_state
    @tag :pilot_crash_recovery
    test "startup quarantines #{prior_state} without releasing the prior attempt", ctx do
      if ctx.pilot_recovery_state == :running do
        assert :ok = AttemptLedger.claim_pilot_launch(ctx.ledger, ctx.grant, ctx.identity)
      end

      name = Module.concat(__MODULE__, "CrashRecovery#{System.unique_integer([:positive])}")
      {:ok, orchestrator} = Orchestrator.start_link(name: name, start_quiesced: true)
      on_exit(fn -> if Process.alive?(orchestrator), do: GenServer.stop(orchestrator) end)
      state = :sys.get_state(orchestrator)
      assert state.pilot_binding == ctx.grant

      assert {:ok, %{state: :quarantined, quarantine_reason: :termination_unconfirmed, result: nil}} =
               AttemptLedger.pilot_status(ctx.ledger)

      assert {:ok, %{in_flight: true}} = AttemptLedger.current(ctx.ledger, ctx.issue.id)
      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
      refute_receive :synthetic_turn, 25
    end
  end

  test "quiesced startup recovers the spent grant and removal cannot enable legacy dispatch", ctx do
    assert :ok = AgentRunner.run(ctx.issue, self(), ctx.opts)
    name = Module.concat(__MODULE__, "Restart#{System.unique_integer([:positive])}")
    {:ok, orchestrator} = Orchestrator.start_link(name: name, start_quiesced: true)
    state = :sys.get_state(orchestrator)
    assert state.pilot_binding == ctx.grant
    assert {:error, _} = AttemptLedger.begin_attempt(state.attempt_ledger, ctx.issue.id, pilot_binding: ctx.grant)
    :ok = GenServer.stop(orchestrator)

    {:ok, workflow} = Workflow.load()
    raw = update_in(workflow.config, ["agent"], &Map.delete(&1, "pilot"))
    File.write!(Workflow.workflow_file_path(), "---\n" <> Jason.encode!(raw) <> "\n---\n" <> @prompt)
    assert {:error, :binding_downgrade_denied} = WorkflowStore.force_reload()
  end

  @tag :integrated_dispatch
  test "one orchestrator dispatch retains the final answer after worker removal without retry", ctx do
    Application.put_env(:symphony_elixir, :pilot_integrated_fixture, ctx.opts)
    name = Module.concat(__MODULE__, "Integrated#{System.unique_integer([:positive])}")
    {:ok, orchestrator} = Orchestrator.start_link(name: name, start_quiesced: true)

    on_exit(fn ->
      if Process.alive?(orchestrator), do: GenServer.stop(orchestrator)
      Application.delete_env(:symphony_elixir, :pilot_integrated_fixture)
    end)

    attempt = RuntimeAttempt.new(ctx.identity, :starting)

    dispatched =
      :sys.replace_state(orchestrator, fn state ->
        state = %{state | agent_runner: IntegratedRunner, work_control: %{ctx.issue.id => ctx.opts[:work_item]}}
        Orchestrator.spawn_prepared_issue_for_test(state, ctx.issue, ctx.route, nil, orchestrator, nil, attempt)
      end)

    assert Map.has_key?(dispatched.running, ctx.issue.id), inspect({dispatched.attempt_ledger_status, dispatched.blocked})

    assert_receive :synthetic_turn, 2_000
    assert_receive :synthetic_stopped, 2_000
    assert wait_for_removal(orchestrator, ctx.issue.id, 100)
    state = :sys.get_state(orchestrator)
    assert state.retry_attempts == %{}

    assert {:ok, %{state: :stopverified, runtime_identity: identity, result: result}} =
             AttemptLedger.pilot_status(ctx.ledger)

    assert identity == ctx.identity
    assert result.outcome == :completed
    assert result.final_answer =~ "Plan: inspect its callers."
    send(orchestrator, {:retry_issue, ctx.issue.id, make_ref()})
    refute_receive :synthetic_turn, 100
  end

  @tag :authority_binding_correction
  test "pilot grant refuses policy bytes changed after grant validation", ctx do
    File.write!(ctx.policy_path, "Role policy: substituted Planner\n")
    assert_raise ArgumentError, ~r/pilot_configuration_invalid/, fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
    refute_receive {:synthetic_session, _}, 25
  end

  @tag :authority_binding_correction
  test "pilot grant refuses a different effective policy root even with identical bytes", ctx do
    alternate = ctx.policy_root <> "-alternate"
    File.mkdir_p!(alternate)
    File.cp!(ctx.policy_path, Path.join(alternate, "planner.md"))
    Application.put_env(:symphony_elixir, :role_prompt_root, alternate)
    assert_raise ArgumentError, ~r/pilot_configuration_invalid/, fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
    refute_receive {:synthetic_session, _}, 25
  end

  for drift <- [:changed, :missing, :root] do
    @tag :authority_binding_correction
    @tag policy_drift: drift
    test "policy #{drift} during admission refuses session launch with the allowance spent", ctx do
      admission = fn _, _, _ ->
        case ctx.policy_drift do
          :changed -> File.write!(ctx.policy_path, "changed after validation")
          :missing -> File.rm!(ctx.policy_path)
          :root -> Application.put_env(:symphony_elixir, :role_prompt_root, ctx.policy_root <> "-missing")
        end

        {:ok, %{synthetic: true}}
      end

      assert_raise RuntimeError, fn ->
        AgentRunner.run(ctx.issue, self(), Keyword.put(ctx.opts, :test_runtime_isolation_admit, admission))
      end

      refute_receive {:synthetic_session, _}, 25
      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
    end
  end

  @tag :authority_binding_correction
  test "launched Planner prompt uses exactly the validated policy snapshot", ctx do
    approved = File.read!(ctx.policy_path)
    assert :ok = AgentRunner.run(ctx.issue, self(), Keyword.put(ctx.opts, :test_capture_prompt, true))
    assert_receive {:synthetic_prompt, prompt}
    assert prompt == approved <> "\n\n--- Workflow task ---\n" <> @prompt
  end

  @tag :authority_binding_correction
  @tag :pilot_custom_policy
  test "the configured Planner policy is bound instead of an unselected planner.md", ctx do
    File.write!(ctx.policy_path, "unselected policy changed")
    assert :ok = AgentRunner.run(ctx.issue, self(), Keyword.put(ctx.opts, :test_capture_prompt, true))
    assert_receive {:synthetic_prompt, prompt}
    assert prompt =~ "Role policy: synthetic approved Planner"
    refute prompt =~ "unselected policy changed"
  end

  @tag :authority_binding_correction
  test "policy removed during session establishment cannot start a model turn", ctx do
    opts = Keyword.put(ctx.opts, :test_after_session_start, fn -> File.rm!(ctx.policy_path) end)
    assert_raise RuntimeError, fn -> AgentRunner.run(ctx.issue, self(), opts) end
    assert_receive {:synthetic_session, _}
    assert_receive :synthetic_stopped
    refute_receive :synthetic_turn, 25
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
  end

  @tag :authority_binding_correction
  test "PATH substituted Git cannot fabricate a clean approved pilot checkout", ctx do
    {:ok, workspace} = Workspace.create_for_issue(ctx.issue, nil, ctx.opts[:ownership_ledger])
    File.write!(Path.join(workspace, "sample.ex"), "unapproved tracked bytes\n")
    fake_bin = Path.join(ctx.policy_root, "fake-bin")
    File.mkdir_p!(fake_bin)
    marker = Path.join(fake_bin, "git-was-used")

    File.write!(
      Path.join(fake_bin, "git"),
      "#!/bin/sh\nprintf used >> '#{marker}'\ncase \" $* \" in *rev-parse*) printf '%s\\n%s\\n' '#{ctx.grant.source_commit}' '#{ctx.grant.source_tree}';; esac\nexit 0\n"
    )

    File.chmod!(Path.join(fake_bin, "git"), 0o700)
    previous = System.fetch_env!("PATH")
    System.put_env("PATH", fake_bin <> ":" <> previous)

    try do
      assert_raise RuntimeError, fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
      refute_receive {:synthetic_session, _}, 25
      refute File.exists?(marker)
    after
      System.put_env("PATH", previous)
    end
  end

  defp wait_for_removal(orchestrator, item, remaining) when remaining > 0 do
    if Map.has_key?(:sys.get_state(orchestrator).running, item) do
      Process.sleep(10)
      wait_for_removal(orchestrator, item, remaining - 1)
    else
      true
    end
  end

  defp wait_for_removal(_orchestrator, _item, 0), do: false

  test "credential-bearing final text is refused without storing its bytes", ctx do
    secret = "api_key=synthetic-provider-secret"

    assert_raise RuntimeError, ~r/Pilot final evidence persistence failed/, fn ->
      AgentRunner.run(ctx.issue, self(), Keyword.put(ctx.opts, :test_answer, secret))
    end

    assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    refute String.contains?(inspect(AttemptLedger.pilot_status(ctx.ledger)), secret)
  end

  defp git!(source, args) do
    {output, code} = System.cmd("git", ["-c", "core.hooksPath=/dev/null", "-C", source | args], stderr_to_stdout: true)
    assert code == 0, output
    output
  end
end
