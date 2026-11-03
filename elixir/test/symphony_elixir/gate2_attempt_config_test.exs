defmodule SymphonyElixir.Gate2AttemptConfigTest do
  use ExUnit.Case, async: false

  import SymphonyElixir.TestSupport, only: [write_workflow_file!: 2]

  alias SymphonyElixir.Workflow

  alias SymphonyElixir.AgentRunner
  alias SymphonyElixir.AgentRuntime.AttemptLedger
  alias SymphonyElixir.Config
  alias SymphonyElixir.Config.Schema
  alias SymphonyElixir.Orchestrator
  alias SymphonyElixir.Tracker.Issue
  alias SymphonyElixir.Workspace.OwnershipLedger

  defmodule RunnerProbeRuntime do
    def start_session(_workspace, opts) do
      send(Keyword.fetch!(opts, :test_pid), :runner_probe_started)
      raise "runner probe reached runtime"
    end
  end

  setup context do
    if context[:runner_fixture] do
      root = temp_root()
      File.mkdir_p!(root)
      workflow_path = Path.join(root, "WORKFLOW.md")
      previous_workflow = Application.get_env(:symphony_elixir, :workflow_file_path)
      previous_ledger_root = Application.get_env(:symphony_elixir, :attempt_ledger_root)
      Workflow.set_workflow_file_path(workflow_path)
      Application.put_env(:symphony_elixir, :attempt_ledger_root, Path.join(root, "attempts"))
      write_workflow_file!(workflow_path, workspace_root: Path.join(root, "workspaces"), tracker_kind: "memory", agent_routing: "legacy")
      settings = Config.settings!()

      {:ok, ledger} =
        OwnershipLedger.open(
          settings.symphony.project_id,
          SymphonyElixir.Tracker.identity(settings.tracker),
          root: Path.join(root, "ownership"),
          workspace_root: Config.local_workspace_root()
        )

      on_exit(fn ->
        OwnershipLedger.close(ledger)
        restore_environment(:workflow_file_path, previous_workflow)
        restore_environment(:attempt_ledger_root, previous_ledger_root)
        if Process.whereis(SymphonyElixir.WorkflowStore), do: SymphonyElixir.WorkflowStore.force_reload()
        File.rm_rf(root)
      end)

      {:ok, ownership_ledger: ledger}
    else
      :ok
    end
  end

  defp restore_environment(key, nil), do: Application.delete_env(:symphony_elixir, key)
  defp restore_environment(key, value), do: Application.put_env(:symphony_elixir, key, value)

  test "missing configuration preserves legacy default" do
    assert {:ok, settings} = Schema.parse(%{})
    assert settings.agent.attempt_boundary.mode == "legacy"
  end

  test "foundation requires schema2 but never auto-migrates" do
    assert {:ok, settings} = Schema.parse(%{agent: %{attempt_boundary: %{mode: "gate2_foundation"}}})
    root = temp_root()
    tracker_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "project-1"}}
    {:ok, ledger} = AttemptLedger.open("t6-config-project", tracker_identity, root: root)
    :ok = AttemptLedger.close(ledger)
    path = AttemptLedger.path_for("t6-config-project", root: root)
    before = File.read!(path) |> then(&:crypto.hash(:sha256, &1))

    assert {:ok, 1, false} = AttemptLedger.configured_schema("t6-config-project", tracker_identity, root: root)

    assert {:error, :migration_required} =
             SymphonyElixir.Config.validate_attempt_boundary(settings,
               project_id: "t6-config-project",
               tracker_identity: tracker_identity,
               root: root
             )

    after_hash = File.read!(path) |> then(&:crypto.hash(:sha256, &1))
    assert before == after_hash
  end

  test "foundation cannot launch runtime" do
    assert {:ok, settings} = Schema.parse(%{agent: %{attempt_boundary: %{mode: "gate2_foundation"}}})
    assert :gate2_dormant = SymphonyElixir.runtime_start_decision(settings)
  end

  @tag :runner_fixture
  test "AgentRunner blocks foundation before starting a runtime" do
    project_id = "t6-runner-foundation"
    workflow_path = Workflow.workflow_file_path()
    identity = %{tracker_kind: "memory", provider_scope: %{}}
    workspace_root = Config.local_workspace_root()
    seed_gate2_binding(AttemptLedger.path_for(project_id), project_id, identity)

    File.write!(
      workflow_path,
      "---\nworkspace:\n  root: #{inspect(workspace_root)}\nsymphony:\n  project_id: #{project_id}\ntracker:\n  kind: memory\nagent:\n  attempt_boundary:\n    mode: gate2_foundation\n---\nTest prompt.\n"
    )

    assert :ok = SymphonyElixir.WorkflowStore.force_reload()
    assert Config.settings!().agent.attempt_boundary.mode == "gate2_foundation"

    ownership_root = temp_root()

    {:ok, ownership_ledger} =
      OwnershipLedger.open(project_id, identity,
        root: ownership_root,
        workspace_root: Config.local_workspace_root()
      )

    on_exit(fn ->
      OwnershipLedger.close(ownership_ledger)
      File.rm_rf(ownership_root)
    end)

    issue = %Issue{id: "runner-foundation", identifier: "SYM-RUNNER-FOUNDATION", title: "Foundation", state: "Ready"}

    assert_raise RuntimeError, ~r/gate2_dormant/, fn ->
      AgentRunner.run(issue, self(),
        runtime: RunnerProbeRuntime,
        test_pid: self(),
        ownership_ledger: ownership_ledger
      )
    end

    refute_received :runner_probe_started
    refute File.exists?(Path.join(workspace_root, issue.identifier))
  end

  @tag :runner_fixture
  test "legacy AgentRunner reaches the supplied fake runtime", %{ownership_ledger: ledger} do
    assert Config.settings!().agent.attempt_boundary.mode == "legacy"
    assert Config.settings!().agent.routing == "legacy"
    issue = %Issue{id: "runner-legacy", identifier: "SYM-RUNNER-LEGACY", title: "Legacy", state: "Ready"}

    assert_raise RuntimeError, "runner probe reached runtime", fn ->
      AgentRunner.run(issue, self(),
        runtime: RunnerProbeRuntime,
        test_pid: self(),
        ownership_ledger: ledger
      )
    end

    assert_received :runner_probe_started
  end

  test "enforced profile is rejected before qualification" do
    assert {:ok, settings} = Schema.parse(%{agent: %{attempt_boundary: %{mode: "gate2_enforced"}}})
    assert {:error, :gate2_profile_incomplete} = SymphonyElixir.Config.validate_attempt_boundary(settings)
  end

  test "reload cannot downgrade stored gate2 binding" do
    root = temp_root()
    project_id = "t6-config-project"
    identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "project-1"}}
    path = AttemptLedger.path_for(project_id, root: root)

    try do
      seed_gate2_binding(path, project_id, identity)

      assert {:error, :binding_downgrade_denied} =
               AttemptLedger.configured_mode("legacy", project_id, identity, root: root)
    after
      File.rm_rf(root)
    end
  end

  test "attempt boundary mode rejects unknown nested keys and values" do
    assert {:error, {:invalid_workflow_config, _}} =
             Schema.parse(%{agent: %{attempt_boundary: %{mode: "legacy", enabled: true}}})

    assert {:error, {:invalid_workflow_config, _}} =
             Schema.parse(%{agent: %{attempt_boundary: %{mode: "legacydefault"}}})
  end

  test "explicit null mode values are rejected without falling back to legacy" do
    assert {:error, {:invalid_workflow_config, _}} =
             Schema.parse(%{agent: %{attempt_boundary: nil}})

    assert {:error, {:invalid_workflow_config, _}} =
             Schema.parse(%{agent: %{attempt_boundary: %{mode: nil}}})
  end

  test "live reload cannot discard Gate2 binding when the new config removes project identity" do
    root = temp_root()
    identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "project-1"}}
    path = AttemptLedger.path_for("t6-config-project", root: root)
    seed_gate2_binding(path, "t6-config-project", identity)
    {:ok, ledger} = AttemptLedger.open("t6-config-project", identity, path: path)

    on_exit(fn ->
      AttemptLedger.close(ledger)
      File.rm_rf(root)
    end)

    state = %Orchestrator.State{attempt_ledger: ledger, attempt_ledger_status: :ready}
    {:ok, config} = Schema.parse(%{})
    updated = Orchestrator.synchronize_attempt_ledger_config_for_test(state, config)
    assert updated.attempt_ledger == ledger
    assert updated.attempt_ledger_status == {:blocked, {:attempt_ledger_unavailable, :binding_downgrade_denied}}
    assert {:ok, [_]} = AttemptLedger.open_lineages(ledger)
  end

  test "disabled ledger and stale mode cannot dispatch a Gate2-bound work item" do
    root = temp_root()
    identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "project-1"}}
    path = AttemptLedger.path_for("t6-config-project", root: root)
    seed_gate2_binding(path, "t6-config-project", identity)
    {:ok, ledger} = AttemptLedger.open("t6-config-project", identity, path: path)

    on_exit(fn ->
      AttemptLedger.close(ledger)
      File.rm_rf(root)
    end)

    state = %Orchestrator.State{attempt_ledger: ledger, attempt_ledger_status: :disabled}
    assert {:error, :gate2_dormant} = Orchestrator.attempt_boundary_dispatch_decision(state, "item-1")
    assert :ok = Orchestrator.attempt_boundary_dispatch_decision(state, "legacy-item")
  end

  test "legacy cold start inspects its configured ledger and retains a Gate2 block" do
    root = temp_root()
    identity = %{tracker_kind: "memory", provider_scope: %{}}
    path = AttemptLedger.path_for("t6-config-project", root: root)
    seed_gate2_binding(path, "t6-config-project", identity)
    on_exit(fn -> File.rm_rf(root) end)
    {:ok, config} = Schema.parse(%{tracker: %{kind: "memory"}, symphony: %{project_id: "t6-config-project"}})
    options = [attempt_ledger_opts: [root: root]]
    state = Orchestrator.initialize_attempt_ledger_for_test(%Orchestrator.State{}, config, options)
    assert state.attempt_ledger_status == {:blocked, {:attempt_ledger_unavailable, :binding_downgrade_denied}}
    {:ok, removed_identity} = Schema.parse(%{})
    updated = Orchestrator.synchronize_attempt_ledger_config_for_test(state, removed_identity)
    assert updated.attempt_ledger_status == state.attempt_ledger_status
  end

  test "configured ledger inspection preserves namespace and tracker mismatch errors" do
    root = temp_root()
    identity = %{tracker_kind: "memory", provider_scope: %{}}
    {:ok, ledger} = AttemptLedger.open("t6-config-project", identity, root: root)
    :ok = AttemptLedger.close(ledger)
    on_exit(fn -> File.rm_rf(root) end)
    drift = %{tracker_kind: "memory", provider_scope: %{project_slug: "different"}}
    assert {:error, :identity_mismatch} = AttemptLedger.configured_schema("t6-config-project", drift, root: root)
    assert {:error, :namespace_mismatch} = AttemptLedger.configured_schema("other-project", identity, path: ledger.path)
  end

  @tag :scope01_identity_reload
  test "legacy identity drift reaches existing reconciliation without hiding Gate2 bindings" do
    root = temp_root()
    project_id = "t6-legacy-reload"
    old_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "before"}}
    new_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "after"}}
    {:ok, settings} = Schema.parse(%{})
    {:ok, ledger} = AttemptLedger.open(project_id, old_identity, root: root)
    assert {:ok, _record} = AttemptLedger.begin_attempt(ledger, "legacy-item")
    assert :ok = AttemptLedger.close(ledger)
    on_exit(fn -> File.rm_rf(root) end)

    options = [project_id: project_id, tracker_identity: new_identity, root: root]
    assert :ok = Config.validate_attempt_boundary(settings, options)

    assert {:error, :identity_mismatch} = AttemptLedger.configured_schema(project_id, new_identity, root: root)
    {:ok, reopened} = AttemptLedger.open(project_id, old_identity, root: root)
    state = %Orchestrator.State{attempt_ledger: reopened, attempt_ledger_status: :ready}
    {:ok, routed} = Schema.parse(%{tracker: %{kind: "memory"}, symphony: %{project_id: project_id}, agent: %{routing: "routed"}})
    updated = Orchestrator.synchronize_attempt_ledger_config_for_test(state, routed)
    assert match?({:blocked, _}, updated.attempt_ledger_status)
    assert updated.attempt_ledger == reopened
    assert :ok = AttemptLedger.close(reopened)
  end

  @tag :scope01_identity_reload
  test "legacy identity drift cannot hide a stored Gate2 binding from configuration admission" do
    root = temp_root()
    project_id = "t6-gate2-reload"
    old_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "before"}}
    new_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "after"}}
    seed_gate2_binding(AttemptLedger.path_for(project_id, root: root), project_id, old_identity)
    on_exit(fn -> File.rm_rf(root) end)
    {:ok, settings} = Schema.parse(%{})

    options = [project_id: project_id, tracker_identity: new_identity, root: root]
    assert {:error, :binding_downgrade_denied} = Config.validate_attempt_boundary(settings, options)
  end

  test "legacy identity fallback rejects corrupt rows before admitting configuration" do
    root = temp_root()
    project_id = "t6-corrupt-reload"
    old_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "before"}}
    new_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "after"}}
    {:ok, settings} = Schema.parse(%{})
    {:ok, ledger} = AttemptLedger.open(project_id, old_identity, root: root)
    assert :ok = :dets.insert(ledger.table, {{:current, "item-1"}, :corrupt})
    on_exit(fn -> File.rm_rf(root) end)

    options = [project_id: project_id, tracker_identity: new_identity, root: root]
    assert {:error, :storage_corrupt} = Config.validate_attempt_boundary(settings, options)

    assert :ok = AttemptLedger.close(ledger)
  end

  test "legacy identity fallback cannot bypass the schema2 committed receipt" do
    root = temp_root()
    project_id = "t6-receipt-reload"
    old_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "before"}}
    new_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "after"}}
    path = AttemptLedger.path_for(project_id, root: root)
    seed_gate2_binding(path, project_id, old_identity)
    File.rm!(path <> ".migration-journal")
    on_exit(fn -> File.rm_rf(root) end)
    {:ok, settings} = Schema.parse(%{})

    options = [project_id: project_id, tracker_identity: new_identity, root: root]
    assert {:error, :migration_in_progress} = Config.validate_attempt_boundary(settings, options)
  end

  for envelope <- [:unsupported_key, :route_mismatch] do
    @tag :r05_envelope
    test "startup rejects #{envelope} before restoring Gate2 reconciliation facts" do
      root = temp_root()
      project_id = "t6-r05-startup"
      identity = %{tracker_kind: "memory", provider_scope: %{}}
      path = AttemptLedger.path_for(project_id, root: root)
      seed_gate2_binding(path, project_id, identity)
      {:ok, ledger} = AttemptLedger.open(project_id, identity, path: path)
      {:ok, record} = AttemptLedger.current(ledger, "item-1")

      record =
        case unquote(envelope) do
          :unsupported_key -> put_in(record.authority_fence, Map.put(record.authority_fence, :cleanup_verified, true))
          :route_mismatch -> %{record | route_fingerprint: "future-route"}
        end

      assert :ok = :dets.insert(ledger.table, {{:current, "item-1"}, record})
      assert :ok = :dets.sync(ledger.table)
      assert :ok = AttemptLedger.close(ledger)
      before = File.read!(path)
      on_exit(fn -> File.rm_rf(root) end)
      config_attrs = %{tracker: %{kind: "memory"}, symphony: %{project_id: project_id}, agent: %{routing: "routed"}}
      {:ok, config} = Schema.parse(config_attrs)
      initial = %Orchestrator.State{}
      options = [attempt_ledger_opts: [path: path]]
      state = Orchestrator.initialize_attempt_ledger_for_test(initial, config, options)
      on_exit(fn -> if state.attempt_ledger, do: AttemptLedger.close(state.attempt_ledger) end)
      assert state.attempt_ledger_status == {:blocked, {:attempt_ledger_unavailable, :migration_in_progress}}
      assert state.attempt_lineages == %{}
      assert state.durable_in_flight == MapSet.new()
      assert File.read!(path) == before
    end
  end

  defp temp_root do
    Path.join(System.tmp_dir!(), "symphony-gate2-config-" <> Base.encode16(:crypto.strong_rand_bytes(12), case: :lower))
  end

  defp seed_gate2_binding(path, project_id, identity) do
    File.mkdir_p!(Path.dirname(path))
    {:ok, ledger} = AttemptLedger.open(project_id, identity, path: path)
    :ok = AttemptLedger.close(ledger)

    request = %{
      project_namespace: project_id,
      tracker_identity_sha256: identity |> :erlang.term_to_binary([:deterministic]) |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower),
      authority_ref: "t6-isolated-fixture-migration",
      source_schema: 1,
      target_schema: 2
    }

    encoded = request |> :erlang.term_to_binary([:deterministic]) |> Base.encode64()
    code_args = Enum.flat_map(:code.get_path(), fn code_path -> ["-pa", List.to_string(code_path)] end)

    script =
      "request = System.argv() |> Enum.at(1) |> Base.decode64!() |> :erlang.binary_to_term([:safe]); path = System.argv() |> Enum.at(0); Application.put_env(:symphony_elixir, :attempt_ledger_root, Path.dirname(path)); result = SymphonyElixir.AgentRuntime.AttemptLedgerMigration.migrate_v1_to_v2(path, request); IO.inspect(result)"

    {output, 0} = System.cmd(System.find_executable("elixir"), code_args ++ ["-e", script, "--", path, encoded], stderr_to_stdout: true)
    assert output =~ "{:ok,"

    runtime_identity = %SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity{
      runtime_attempt_id: "attempt-1",
      work_item_id: "item-1",
      lineage_generation: "lineage-1",
      responsibility: "implementation",
      runtime_profile: "implementation"
    }

    reference = %{grant_id: "grant-1", project_namespace: project_id, runtime_identity: runtime_identity}
    reference = Map.merge(reference, %{fence_epoch: 1, grant_sha256: String.duplicate("a", 64)})

    record = %{
      schema_version: 2,
      project_namespace: project_id,
      issue_id: "item-1",
      lineage_id: "lineage-1",
      safety_counters: %{ordinary_failures: 0, ordinary_retries: 0, review_cycles: 0},
      status: :open,
      stop_reason: nil,
      route_fingerprint: nil,
      in_flight: true,
      authority_fence: %{
        state: :bound,
        runtime_attempt: runtime_identity,
        route_fingerprint: nil,
        gate2_fence: %{reference: reference, status: :requested}
      },
      close_pending: false,
      updated_at: 1_700_000_000_000,
      boundary_binding: %{
        kind: :gate2,
        binding_version: 1,
        lineage_binding_id: "binding-1",
        resource_ledger_namespace: project_id
      }
    }

    table = :t6_gate2_config_fixture
    {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(path), type: :set)
    :ok = :dets.insert(table, {{:current, "item-1"}, record})
    :ok = :dets.sync(table)
    :ok = :dets.close(table)
  end
end
