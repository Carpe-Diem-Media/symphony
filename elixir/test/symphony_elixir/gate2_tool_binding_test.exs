defmodule SymphonyElixir.Gate2ToolBindingTest do
  use SymphonyElixir.TestSupport

  alias SymphonyElixir.AgentRuntime.{AttemptLedger, Router, ToolBinding}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.Config.Schema
  alias SymphonyElixir.Plane.AgentTool
  alias SymphonyElixir.WorkControl.{WorkflowLifecycle, WorkItem}

  @project "p05-fixture"
  @plane "f1050000-0000-4000-8000-000000000001"
  @item "f1050000-0000-4000-8000-000000000002"
  @workspace "f1050000-0000-4000-8000-000000000003"
  @operation "plane_get_current_work_item"
  @prompt "Offline P05 fixture"
  @adapter {AgentTool, :execute, 3}

  setup do
    prior_key = System.get_env("PLANE_API_KEY")
    System.put_env("PLANE_API_KEY", "P05-FIXTURE-NONSECRET")
    on_exit(fn -> restore_env("PLANE_API_KEY", prior_key) end)
    root = Path.dirname(Workflow.workflow_file_path())
    File.chmod!(root, 0o700)
    source = fixture_checkout(root)
    policy_root = Path.join(root, "policies")
    File.mkdir!(policy_root)
    policy = Path.join(policy_root, "planner.md")
    File.write!(policy, "Offline fixture policy. Read only.")
    previous = Application.fetch_env(:symphony_elixir, :role_prompt_root)
    Application.put_env(:symphony_elixir, :role_prompt_root, policy_root)
    on_exit(fn -> restore_policy_root(previous) end)

    raw = fixture_config(root)
    {:ok, settings} = Schema.parse(raw)
    [commit, tree] = git!(source, ["rev-parse", "HEAD", "HEAD^{tree}"]) |> String.split()

    grant = %{
      project_id: @project,
      plane_project_id: @plane,
      work_item_id: @item,
      responsibility: "planning",
      source_commit: commit,
      source_tree: tree,
      config_identity: Config.pilot_configuration_identity(settings, @prompt),
      runtime_lineage: "p05-fixture-lineage",
      deadline_ms: 120_000
    }

    raw = put_in(raw, ["agent", "pilot"], grant)
    File.write!(Workflow.workflow_file_path(), "---\n" <> Jason.encode!(raw) <> "\n---\n" <> @prompt)
    assert :ok = WorkflowStore.force_reload()
    settings = Config.settings!()
    assert {:ok, ^grant} = Config.pilot_binding(settings)
    item = fixture_item(settings.provider_project_contract)
    assert {:ok, route} = Router.resolve(item, settings.agent.profiles, settings.agent.routes)

    tracker = Tracker.identity(settings.tracker)
    assert {:ok, ledger} = AttemptLedger.open(@project, tracker, root: root)
    on_exit(fn -> AttemptLedger.close(ledger) end)
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    attempt_opts = [pilot_binding: grant, route_fingerprint: route.fingerprint]
    assert {:ok, record} = AttemptLedger.begin_attempt(ledger, @item, attempt_opts)

    identity = Identity.allocate(@item, route, record.lineage_id)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, @item, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert :ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity)

    # Trace the actual adapter and the fallback. Test workers are the only tracees.
    Code.ensure_loaded!(AgentTool)
    Code.ensure_loaded!(SymphonyElixir.Orchestrator)
    :erlang.trace_pattern(@adapter, true, [])
    fallback = {SymphonyElixir.Orchestrator, :semantic_tool_context, 2}
    :erlang.trace_pattern(fallback, true, [])

    on_exit(fn ->
      :erlang.trace_pattern(@adapter, false, [])
      :erlang.trace_pattern(fallback, false, [])
    end)

    fixture = %{
      ledger: ledger,
      grant: grant,
      identity: identity,
      route: route,
      item: item,
      source: source,
      absolute_deadline_ms: System.monotonic_time(:millisecond) + 30_000
    }

    {:ok, fixture: fixture, root: root, policy: policy, tracker: tracker}
  end

  test "one exact read reaches the real adapter and exposes only its bound projection", ctx do
    binding = bind!(ctx)
    assert {{:ok, result}, 1} = invoke(binding)

    assert result == %{
             "workItemId" => @item,
             "identifier" => "P05-FIXTURE-1",
             "title" => "Synthetic P05 work item",
             "canonicalLifecycleState" => "planning",
             "dependencyCompleteness" => "complete",
             "providerObservation" => %{
               "stateName" => "Planning",
               "observedAt" => DateTime.to_iso8601(ctx.fixture.item.provider_observation.observed_at),
               "providerUpdatedAt" => "2026-11-20T00:00:00Z"
             }
           }

    assert {:ok, :audited_terminal} = ToolBinding.recover(binding)
    retain_journal(ctx.root, "successful-read")
    assert {{:error, :slot_consumed}, 0} = invoke(binding)
    assert {{:error, :slot_consumed}, 0} = invoke(binding, changed(binding, "request_id", "different"))
    assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.fixture.ledger)
  end

  test "wrong exact authority and request shape refuse before invocation", ctx do
    binding = bind!(ctx)

    for field <- ~w(grant attempt lineage work_item role project starting_state configuration policy source_commit source_tree observation catalog request_id thread turn deadline_ms) do
      assert {{:error, :request_refused}, 0} = invoke(binding, changed(binding, field, "incorrect"))
    end

    assert {{:error, :request_refused}, 0} = invoke(binding, changed(binding, "tool", "plane_request_lifecycle_transition"))
    assert {{:error, :request_refused}, 0} = invoke(binding, changed(binding, "args", %{"issueId" => @item}))
    assert {{:error, :request_refused}, 0} = invoke(binding, changed(binding, "url", "https://example.invalid"))
    assert {{:error, :request_refused}, 0} = invoke(binding, String.duplicate("x", 8193))
    assert {{:error, :request_refused}, 0} = invoke(binding, "{")
    assert {{:error, :request_refused}, 0} = invoke(binding, String.replace_prefix(frame(binding), "{", ~s({"args":{},)))
    assert {{:error, :request_refused}, 0} = invoke(binding, String.replace(frame(binding), ~s("args":{}), ~s("args":{"a":1,"a":2})))
    assert {:ok, :bound} = ToolBinding.recover(binding)
  end

  test "missing injected fixture cannot fall back and stale policy refuses", ctx do
    assert {:error, :binding_refused} = ToolBinding.bind(:p05_fixture, %{ctx.fixture | item: nil})
    binding = bind!(ctx)
    File.write!(ctx.policy, "Changed policy")
    assert {{:error, :refused_before_invocation}, 0} = invoke(binding)
    assert {:ok, :refused_before_invocation} = ToolBinding.recover(binding)
    assert {{:error, :slot_consumed}, 0} = invoke(binding)
  end

  test "a dead binding owner cannot be replaced even before intent", ctx do
    owner = self()

    {pid, monitor} =
      spawn_monitor(fn ->
        send(owner, {:binding, ToolBinding.bind(:p05_fixture, ctx.fixture)})
      end)

    assert_receive {:binding, {:ok, binding}}, 2_000
    assert_receive {:DOWN, ^monitor, :process, ^pid, :normal}
    assert {:ok, :bound} = ToolBinding.recover(ctx.fixture)
    assert {{:error, :request_refused}, 0} = invoke(binding)
    assert {:error, :slot_consumed} = ToolBinding.bind(:p05_fixture, ctx.fixture)
  end

  test "an expired absolute deadline refuses without dispatch", ctx do
    fixture = %{ctx.fixture | absolute_deadline_ms: System.monotonic_time(:millisecond) + 250}
    assert {:ok, binding} = ToolBinding.bind(:p05_fixture, fixture)
    Process.sleep(300)
    assert {{:error, :refused_before_invocation}, 0} = invoke(binding)
  end

  test "the current attempt is checked again at invocation", ctx do
    binding = bind!(ctx)
    assert :ok = AttemptLedger.quarantine_pilot(ctx.fixture.ledger, ctx.fixture.identity, :worker_lost)
    assert {{:error, :refused_before_invocation}, 0} = invoke(binding)
  end

  test "a changed checkout refuses before dispatch", ctx do
    binding = bind!(ctx)
    File.write!(Path.join(ctx.fixture.source, "fixture.txt"), "changed after binding")
    assert {{:error, :refused_before_invocation}, 0} = invoke(binding)
  end

  for phase <- [:after_read, :after_result_sync, :after_acceptance] do
    @tag phase: phase
    test "deadline boundary at #{phase} agrees with recovery", ctx do
      fixture = %{ctx.fixture | absolute_deadline_ms: System.monotonic_time(:millisecond) + 2_000}
      assert {:ok, binding} = ToolBinding.bind(:p05_fixture, fixture)
      worker = start_invocation(binding, frame(binding), {:pause, ctx.phase, self()})
      {pid, _monitor} = worker
      assert_receive {:p05_paused, ^pid, phase}, 1_500
      assert phase == ctx.phase
      assert {:ok, :worker_active} = ToolBinding.recover(binding)
      refute journal_file?(ctx.root, "terminal.json")
      assert {{:error, :slot_consumed}, 0} = invoke(binding)
      Process.sleep(max(fixture.absolute_deadline_ms - System.monotonic_time(:millisecond) + 1, 0))
      send(pid, {:p05_resume, phase})
      {result, 1} = finish_invocation(worker)

      if phase == :after_acceptance do
        assert {:ok, %{"workItemId" => @item}} = result
        assert {:ok, :audited_terminal} = ToolBinding.recover(binding)
      else
        assert {:error, :quarantined_consumed} = result
        assert {:ok, :quarantined_consumed} = ToolBinding.recover(binding)
        refute journal_file?(ctx.root, "terminal.json")
      end

      retain_journal(ctx.root, phase)
      assert {{:error, :slot_consumed}, 0} = invoke(binding)
    end
  end

  test "an active worker with a durable result cannot be audited by recovery", ctx do
    binding = bind!(ctx)
    worker = start_invocation(binding, frame(binding), {:pause, :after_acceptance, self()})
    {pid, _monitor} = worker
    assert_receive {:p05_paused, ^pid, :after_acceptance}, 1_500
    assert journal_file?(ctx.root, "result.json")
    assert {:ok, :worker_active} = ToolBinding.recover(ctx.fixture)
    refute journal_file?(ctx.root, "terminal.json")
    Process.exit(pid, :kill)
    assert {{:crashed, :killed}, 1} = finish_invocation(worker)
    assert {:ok, :audited_terminal} = ToolBinding.recover(ctx.fixture)
    assert journal_file?(ctx.root, "terminal.json")
    retain_journal(ctx.root, "confirmed_worker_loss")
  end

  test "decision open failure leaves a consumed slot without a decision file", ctx do
    binding = bind!(ctx)
    assert {{:error, :quarantined_consumed}, 0} = invoke(binding, frame(binding), :decision_open)
    refute journal_file?(ctx.root, "decision.json")
    assert {:ok, :quarantined_consumed} = ToolBinding.recover(binding)
    assert {{:error, :slot_consumed}, 0} = invoke(binding)
    assert {:error, :slot_consumed} = ToolBinding.bind(:p05_fixture, ctx.fixture)
    retain_journal(ctx.root, :decision_open)
  end

  for field <- [:grant, :attempt, :lineage, :project, :item, :role, :configuration, :policy] do
    @tag authority_field: field
    test "actual #{field} drift with the original request refuses before dispatch", ctx do
      binding = bind!(ctx)
      changed = mutate_authority(binding, ctx, ctx.authority_field)

      if ctx.authority_field in [:attempt, :lineage] do
        assert {{:error, :request_refused}, 0} = invoke(changed, frame(binding))
        assert {:ok, :bound} = ToolBinding.recover(binding)
      else
        assert {{:error, :refused_before_invocation}, 0} = invoke(changed, frame(binding))
        assert {:ok, :refused_before_invocation} = ToolBinding.recover(binding)
      end
    end
  end

  test "concurrent submissions cannot produce a second adapter call", ctx do
    binding = bind!(ctx)
    workers = for _ <- 1..12, do: start_invocation(binding, frame(binding), :none)
    outcomes = Enum.map(workers, &finish_invocation/1)
    assert Enum.count(outcomes, &match?({{:ok, %{}}, 1}, &1)) == 1
    assert Enum.count(outcomes, &(&1 == {{:error, :slot_consumed}, 0})) == 11
  end

  for fault <- [:reservation_write, :reservation_sync] do
    @tag fault: fault
    test "reservation failure #{fault} fences the slot with zero dispatch", ctx do
      binding = bind!(ctx)
      assert {{:error, :quarantined_consumed}, 0} = invoke(binding, frame(binding), ctx.fault)
      assert {:ok, :quarantined_consumed} = ToolBinding.recover(binding)
      retain_journal(ctx.root, ctx.fault)
      assert {{:error, :slot_consumed}, 0} = invoke(binding)
      assert {:error, :slot_consumed} = ToolBinding.bind(:p05_fixture, ctx.fixture)
    end
  end

  for {fault, count, disposition} <- [
        {:crash_after_intent, 0, :quarantined_consumed},
        {:crash_after_dispatch, 1, :quarantined_consumed},
        {:lose_result, 1, :audited_terminal}
      ] do
    @tag fault: fault, dispatches: count, disposition: disposition
    test "#{fault} retains the slot across worker exit and ledger reopen", ctx do
      binding = bind!(ctx)
      assert {{:crashed, :killed}, ctx.dispatches} == invoke(binding, frame(binding), ctx.fault)
      assert :ok = AttemptLedger.close(ctx.fixture.ledger)
      assert_recovery_in_fresh_vm(ctx, :worker_state_uncertain)
      refute journal_file?(ctx.root, "terminal.json")
      assert {:ok, disposition} = ToolBinding.recover(binding)
      assert disposition == ctx.disposition
      assert_recovery_in_fresh_vm(ctx, ctx.disposition)
      assert {:ok, reopened} = AttemptLedger.open(@project, ctx.tracker, root: ctx.root)
      on_exit(fn -> AttemptLedger.close(reopened) end)
      fixture = %{ctx.fixture | ledger: reopened}
      assert {:error, :slot_consumed} = ToolBinding.bind(:p05_fixture, fixture)
      assert {:ok, state} = ToolBinding.recover(fixture)
      assert state == ctx.disposition
      retain_journal(ctx.root, ctx.fault)
      assert {{:error, :slot_consumed}, 0} = invoke(binding)
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(reopened)
    end
  end

  test "an invalid real adapter projection retains consumed state", ctx do
    invalid = put_in(ctx.fixture, [:item, Access.key(:title)], %{"unexpected" => "not a title"})
    assert {:ok, binding} = ToolBinding.bind(:p05_fixture, invalid)
    assert {{:error, :quarantined_consumed}, 1} = invoke(binding)
    assert {:ok, :quarantined_consumed} = ToolBinding.recover(binding)
    assert {{:error, :slot_consumed}, 0} = invoke(binding)
  end

  test "a real adapter projection above four KiB is refused", ctx do
    oversized = put_in(ctx.fixture, [:item, Access.key(:title)], String.duplicate("x", 4096))
    assert {:ok, binding} = ToolBinding.bind(:p05_fixture, oversized)
    assert {{:error, :quarantined_consumed}, 1} = invoke(binding)
    assert {:ok, :quarantined_consumed} = ToolBinding.recover(binding)
  end

  defp mutate_authority(binding, _ctx, :grant), do: put_in(binding.fixture.grant.deadline_ms, 121_000)
  defp mutate_authority(binding, _ctx, :attempt), do: put_in(binding.fixture.identity.runtime_attempt_id, "other-attempt")
  defp mutate_authority(binding, _ctx, :lineage), do: put_in(binding.fixture.identity.lineage_generation, "other-lineage")
  defp mutate_authority(binding, _ctx, :project), do: put_in(binding.fixture.item.provider_observation.project_id, @workspace)
  defp mutate_authority(binding, _ctx, :item), do: put_in(binding.fixture.item.id, @workspace)
  defp mutate_authority(binding, _ctx, :role), do: put_in(binding.fixture.route.responsibility, "review")

  defp mutate_authority(binding, _ctx, :configuration) do
    path = Workflow.workflow_file_path()
    bytes = File.read!(path)
    changed = String.replace(bytes, ~s("max_concurrent_agents":1), ~s("max_concurrent_agents":2))
    refute changed == bytes
    File.write!(path, changed)
    WorkflowStore.force_reload()
    binding
  end

  defp mutate_authority(binding, ctx, :policy) do
    File.write!(ctx.policy, "A different fixture policy.")
    binding
  end

  defp journal_file?(root, name), do: Path.wildcard(Path.join([root, "p05-*", name])) != []

  defp bind!(ctx) do
    assert {:ok, binding} = ToolBinding.bind(:p05_fixture, ctx.fixture)
    binding
  end

  defp frame(binding), do: binding |> ToolBinding.request() |> Jason.encode!()

  defp changed(binding, key, value), do: binding |> ToolBinding.request() |> Map.put(key, value) |> Jason.encode!()

  defp invoke(binding, request \\ nil, fault \\ :none) do
    binding |> start_invocation(request || frame(binding), fault) |> finish_invocation()
  end

  defp start_invocation(binding, request, fault) do
    recipient = self()

    {pid, monitor} =
      spawn_monitor(fn ->
        receive do
          :invoke -> send(recipient, {:invocation, self(), ToolBinding.invoke(binding, request, fault)})
        end
      end)

    :erlang.trace(pid, true, [:call])
    send(pid, :invoke)
    {pid, monitor}
  end

  defp finish_invocation({pid, monitor}) do
    result =
      receive do
        {:invocation, ^pid, result} ->
          assert_receive {:DOWN, ^monitor, :process, ^pid, :normal}, 2_000
          result

        {:DOWN, ^monitor, :process, ^pid, reason} ->
          {:crashed, reason}
      after
        5_000 -> flunk("fixture worker did not terminate")
      end

    delivered = :erlang.trace_delivered(pid)
    assert_receive {:trace_delivered, ^pid, ^delivered}
    Process.demonitor(monitor, [:flush])
    refute_received {:trace, ^pid, :call, {SymphonyElixir.Orchestrator, :semantic_tool_context, _}}
    {result, adapter_calls(pid, 0)}
  end

  defp adapter_calls(pid, count) do
    receive do
      {:trace, ^pid, :call, {AgentTool, :execute, [@operation, %{}, opts]}} ->
        assert Keyword.keys(opts) == [:agent_tool_context, :semantic_tool_context, :tracker_settings]
        assert is_map(opts[:semantic_tool_context])
        adapter_calls(pid, count + 1)

      {:trace, ^pid, :call, {AgentTool, :execute, _}} ->
        flunk("fixture dispatched an unauthorized adapter operation")
    after
      0 -> count
    end
  end

  defp assert_recovery_in_fresh_vm(ctx, disposition) do
    script = """
    alias SymphonyElixir.AgentRuntime.{AttemptLedger, ToolBinding}
    alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
    [workflow, root, project, workspace, plane, attempt, lineage, expected] = System.argv()
    :ok = SymphonyElixir.Workflow.set_workflow_file_path(workflow)
    tracker = %{tracker_kind: "plane", provider_scope: %{workspace_slug: "p05-fixture", workspace_id: workspace, project_id: plane}}
    {:ok, ledger} = AttemptLedger.open(project, tracker, root: root)
    identity = %Identity{runtime_attempt_id: attempt, lineage_generation: lineage}
    {:ok, disposition} = ToolBinding.recover(%{ledger: ledger, identity: identity})
    true = Atom.to_string(disposition) == expected
    :ok = AttemptLedger.close(ledger)
    IO.puts("P05 fixture recovered from disk: " <> expected)
    """

    code_paths = Enum.flat_map([:symphony_elixir, :jason, :ecto], &["-pa", to_string(:code.lib_dir(&1, :ebin))])
    identity = ctx.fixture.identity
    expected = Atom.to_string(disposition)

    args = code_paths ++ ["-e", script, "--", Workflow.workflow_file_path(), ctx.root, @project, @workspace, @plane, identity.runtime_attempt_id, identity.lineage_generation, expected]

    {output, status} = System.cmd(System.find_executable("elixir"), args, stderr_to_stdout: true)
    assert status == 0, output
    assert String.trim(output) == "P05 fixture recovered from disk: " <> expected
  end

  defp retain_journal(root, label) do
    if evidence = System.get_env("P05_FIXTURE_TEST_EVIDENCE") do
      [journal] = root |> Path.join("p05-*") |> Path.wildcard() |> Enum.filter(&File.dir?/1)
      destination = Path.join(evidence, to_string(label))
      File.mkdir!(destination)

      for file <- Path.wildcard(Path.join(journal, "*.json")) do
        File.cp!(file, Path.join(destination, Path.basename(file)))
      end

      if File.dir?(Path.join(journal, "claim")), do: File.mkdir!(Path.join(destination, "claim"))
    end
  end

  defp fixture_item(contract) do
    issue = %Issue{
      id: @item,
      identifier: "P05-FIXTURE-1",
      title: "Synthetic P05 work item",
      description: "unselected fixture field",
      state: "Planning",
      workspace_id: @workspace,
      project_id: @plane,
      provider_state_id: "state-planning",
      provider_state_group: :unstarted,
      updated_at: ~U[2026-11-20 00:00:00Z]
    }

    assert {:ok, item} =
             WorkItem.from_issue(issue, %{
               provider: :plane,
               prior_validated_lifecycle_state: :planning,
               provider_project_contract: contract
             })

    item
  end

  defp fixture_config(root) do
    %{
      "symphony" => %{"project_id" => @project},
      "tracker" => %{"kind" => "plane", "api_key" => "$PLANE_API_KEY", "workspace_slug" => "p05-fixture", "workspace_id" => @workspace, "project_id" => @plane},
      "workspace" => %{"root" => root},
      "source_control" => %{
        "kind" => "github",
        "repository" => "offline/fixture",
        "repository_id" => 1,
        "base_branch" => "main",
        "token_env" => "SYNTHETIC_UNUSED_GITHUB_TOKEN",
        "required_checks" => [%{"context" => "offline", "app_id" => 1, "subject" => "head"}]
      },
      "agent" => %{"routing" => "routed", "max_concurrent_agents" => 1},
      "provider_project_contract" => %{
        schema_version: 1,
        provider: :plane,
        workspace_id: @workspace,
        project_id: @plane,
        state_mappings: Map.new(WorkflowLifecycle.states(), &{&1, %{state_id: "state-#{&1}", name: WorkflowLifecycle.display(&1)}})
      }
    }
  end

  defp fixture_checkout(root) do
    source = Path.join(root, "checkout")
    File.mkdir!(source)
    git!(source, ["init", "-q"])
    File.write!(Path.join(source, "fixture.txt"), "synthetic source")
    git!(source, ["add", "fixture.txt"])
    git!(source, ["-c", "user.name=P05 Fixture", "-c", "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false", "commit", "-qm", "Fixture"])
    source
  end

  defp git!(source, args) do
    {output, 0} = System.cmd("/usr/bin/git", ["-C", source | args], stderr_to_stdout: true)
    output
  end

  defp restore_policy_root({:ok, prior}), do: Application.put_env(:symphony_elixir, :role_prompt_root, prior)
  defp restore_policy_root(:error), do: Application.delete_env(:symphony_elixir, :role_prompt_root)
end
