if binary = System.get_env("PINNED_CODEX_FUNCTIONAL_BINARY") do
  defmodule SymphonyElixir.PilotFunctionalHolderTest do
    use SymphonyElixir.TestSupport

    alias SymphonyElixir.AgentRuntime.{AttemptLedger, Codex, Router}
    alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
    alias SymphonyElixir.Config.Schema
    alias SymphonyElixir.ProviderEffect.RequestLedger
    alias SymphonyElixir.WorkControl.{WorkflowLifecycle, WorkItem}

    @binary binary
    @project "11111111-1111-4111-8111-111111111111"
    @item "22222222-2222-4222-8222-222222222222"
    @workspace "33333333-3333-4333-8333-333333333333"
    @prompt "Read the tracked planner_input.txt and return a short plan."
    @input "SLICE_C_TRACKED_FILE_PROOF\n"

    defmodule FaultedStorage do
      @moduledoc false
      @behaviour SymphonyElixir.AgentRuntime

      @impl true
      defdelegate capabilities(), to: Codex

      @impl true
      defdelegate runtime_metadata(), to: Codex

      @impl true
      def start_session(workspace, opts) do
        with {:ok, session} <- Codex.start_session(workspace, opts) do
          fault = Keyword.fetch!(opts, :fixture_storage_fault)

          case fault do
            {:request_intent, path} ->
              File.mkdir!(path)
              send(self(), {:fixture_intent_store_blocked, path})

            :c04 ->
              :ok
          end

          {:ok, {session, Keyword.fetch!(opts, :attempt_ledger), fault}}
        end
      end

      @impl true
      def run_turn({session, _ledger, _fault}, prompt, issue, opts) do
        Codex.run_turn(session, prompt, issue, opts)
      end

      @impl true
      def stop_session({session, ledger, :c04}) do
        with :ok <- Codex.stop_session(session),
             :ok <- AttemptLedger.close(ledger) do
          send(self(), {:fixture_closed_result_store, AttemptLedger.pilot_status(ledger)})
          :ok
        end
      end

      def stop_session({session, _ledger, {:request_intent, _path}}), do: Codex.stop_session(session)
    end

    setup_all do
      assert System.get_env("PLANE_API_KEY") == "SYNTHETIC-NONLIVE-PLANE-KEY"
      native = Path.expand("../../../native/pilot_c02", __DIR__)
      {output, status} = System.cmd("/usr/bin/make", ["-C", native, "all"], stderr_to_stdout: true)
      assert status == 0, output
      {:ok, native: native}
    end

    setup %{native: native} = context do
      root = Path.dirname(Workflow.workflow_file_path())
      source = Path.join(root, "source")
      File.mkdir!(source)
      git!(source, ["init", "-q"])
      File.write!(Path.join(source, "planner_input.txt"), @input)
      git!(source, ["add", "planner_input.txt"])
      git!(source, ["-c", "user.name=Offline", "-c", "user.email=offline@example.invalid", "-c", "commit.gpgSign=false", "commit", "-qm", "Planner fixture"])
      [commit, tree] = git!(source, ["rev-parse", "HEAD", "HEAD^{tree}"]) |> String.split()

      codex = Path.join(root, "codex")
      File.cp!(@binary, codex)
      File.chmod!(codex, 0o700)
      model_catalog = Path.expand("../native/pinned_codex/tests/fixtures/synthetic_model.json")

      policy = Path.join(root, "policy")
      File.mkdir!(policy)
      File.write!(Path.join(policy, "planner.md"), "Inspect the tracked fixture file only.\n")
      put_fixture_env(:role_prompt_root, policy)

      settings = %{
        "symphony" => %{"project_id" => "pilot-functional"},
        "tracker" => %{
          "kind" => "plane",
          "api_key" => "$PLANE_API_KEY",
          "workspace_slug" => "disposable",
          "workspace_id" => @workspace,
          "project_id" => @project
        },
        "workspace" => %{"root" => Path.join(root, "workspaces")},
        "agent" => %{
          "routing" => "routed",
          "max_concurrent_agents" => 1,
          "profiles" => %{"planner" => %{"model" => "synthetic-planner-v1"}},
          "pilot_holder" => holder_selection(codex)
        },
        "codex" => %{"command" => "#{codex} app-server"},
        "hooks" => %{"after_create" => "/usr/bin/git -c core.hooksPath=/dev/null clone --local --no-hardlinks #{source} ."},
        "source_control" => %{
          "kind" => "github",
          "repository" => "offline/fixture",
          "repository_id" => 1,
          "base_branch" => "main",
          "token_env" => "SYNTHETIC_UNUSED_GITHUB_TOKEN",
          "required_checks" => [%{"context" => "offline", "app_id" => 1, "subject" => "head"}]
        },
        "provider_project_contract" => %{
          schema_version: 1,
          provider: :plane,
          workspace_id: @workspace,
          project_id: @project,
          state_mappings:
            Map.new(WorkflowLifecycle.states(), fn state ->
              {state, %{state_id: "state-#{state}", name: WorkflowLifecycle.display(state)}}
            end)
        }
      }

      {:ok, parsed} = Schema.parse(settings)

      grant = %{
        project_id: "pilot-functional",
        plane_project_id: @project,
        work_item_id: @item,
        responsibility: "planning",
        source_commit: commit,
        source_tree: tree,
        config_identity: Config.pilot_configuration_identity(parsed, @prompt),
        runtime_lineage: "offline-functional-ordinal-test",
        deadline_ms: 25_000
      }

      File.write!(Workflow.workflow_file_path(), "---\n" <> Jason.encode!(put_in(settings, ["agent", "pilot"], grant)) <> "\n---\n" <> @prompt)
      assert :ok = WorkflowStore.force_reload()
      loaded = Config.settings!()
      assert {:ok, ^grant} = Config.pilot_binding(loaded)

      issue = %Issue{
        id: @item,
        identifier: "DISPOSABLE-1",
        state: "Planning",
        title: "Offline fixture",
        workspace_id: @workspace,
        project_id: @project,
        provider_state_id: "state-planning",
        provider_state_group: :unstarted,
        dispatchable: true
      }

      {:ok, work_item} =
        WorkItem.from_issue(issue, %{
          provider: :plane,
          prior_validated_lifecycle_state: :planning,
          provider_project_contract: loaded.provider_project_contract
        })

      {:ok, route} = Router.resolve(work_item, loaded.agent.profiles, loaded.agent.routes)
      tracker = Tracker.identity(loaded.tracker)
      {:ok, ledger} = AttemptLedger.open(grant.project_id, tracker, root: root)
      on_exit(fn -> AttemptLedger.close(ledger) end)

      assert :ok = AttemptLedger.configure_pilot(ledger, grant)

      assert {:ok, record} =
               AttemptLedger.begin_attempt(ledger, @item,
                 pilot_binding: grant,
                 route_fingerprint: route.fingerprint
               )

      identity = Identity.allocate(@item, route, record.lineage_id)

      identity =
        case Map.fetch(context, :fixture_attempt_first_byte) do
          {:ok, byte} ->
            suffix = :crypto.strong_rand_bytes(15)
            %{identity | runtime_attempt_id: Base.url_encode64(<<byte, suffix::binary>>, padding: false)}

          :error ->
            identity
        end

      assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, @item, identity)
      assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)

      evidence_root = System.get_env("SLICE_C_ROUTED_EVIDENCE") || Path.join(root, "native-evidence")
      driver = Path.join(native, "tests/run_attempt.py")
      binaries = Enum.map(~w(guard host holder-probe tool-broker request-effect), &Path.join([native, "build", &1]))
      files = [driver, codex, model_catalog, Path.join(native, "tests/provider_fixture.py") | binaries]

      pin = %{
        schema2: :functional,
        pinned_codex: true,
        holder: codex,
        model_catalog: model_catalog,
        driver: driver,
        evidence_root: evidence_root,
        files: Map.new(files, &{&1, digest(File.read!(&1))}),
        fault: Map.get(context, :fixture_fault, "none")
      }

      put_fixture_env(:test_native_pilot, pin)

      opts = [
        pilot_binding: grant,
        attempt_ledger: ledger,
        runtime_attempt_identity: identity,
        route: route,
        work_item: work_item,
        ownership_ledger: workspace_ownership_ledger(),
        runtime: Codex,
        test_native_pilot: pin,
        test_runtime_isolation_admit: fn _, _, _ -> {:ok, :offline_fixture} end,
        test_routed_guard_tool_paths: %{"unshare" => "/usr/bin/unshare", "python3" => "/usr/bin/python3"},
        issue_state_fetcher: fn _ -> flunk("C01 must not request continuation") end,
        plane_epoch_snapshot_reader: fn -> flunk("C01 must not query Plane") end
      ]

      {:ok, issue: issue, opts: opts, grant: grant, ledger: ledger, tracker: tracker, root: root, directory: Path.join(evidence_root, identity.runtime_attempt_id)}
    end

    test "real Planner turn is persisted after native and namespace stop and is readable in a fresh BEAM", ctx do
      assert_completed_planner(ctx)
    end

    for {first_byte, prefix} <- [{0, "A"}, {248, "-"}, {252, "_"}] do
      @tag fixture_attempt_first_byte: first_byte
      test "real routed Planner completes with authoritative #{prefix} prefixed runtime ID", ctx do
        assert <<unquote(prefix), _::binary>> = ctx.opts[:runtime_attempt_identity].runtime_attempt_id
        assert_completed_planner(ctx)
      end
    end

    defp assert_completed_planner(ctx) do
      identity = ctx.opts[:runtime_attempt_identity]
      attempt = identity.runtime_attempt_id

      assert :ok = AgentRunner.run(ctx.issue, self(), ctx.opts)

      assert {:ok, %{state: :stopverified, runtime_identity: ^identity, result: result}} =
               AttemptLedger.pilot_status(ctx.ledger)

      assert result.outcome == :completed
      assert result.model_state == :completed
      assert result.stop_disposition == :verified
      assert is_binary(result.final_answer) and byte_size(result.final_answer) > 0
      assert is_binary(result.thread_id) and is_binary(result.turn_id)
      stop = ctx.directory |> Path.join("routed-stop-observation.json") |> File.read!() |> Jason.decode!()
      assert %{"port_down_observed" => true, "pid1_stop_verified" => true, "namespace_pid1" => %{"pid" => pid}} = stop
      assert is_integer(pid) and pid > 1

      host_stop = ctx.directory |> Path.join("functional-broker-stop.json") |> File.read!() |> Jason.decode!()

      assert %{
               "schema" => "H100-HOST-BROKER-STOP-1",
               "binding" => binding,
               "attempt" => ^attempt,
               "helper_stopped" => true,
               "tool_stopped" => true
             } = host_stop

      assert %{"binding" => ^binding, "attempt" => ^attempt} = stop

      assert [
               %{ordinal: 1, state: :terminal, runtime_attempt_id: ^attempt} = first,
               %{ordinal: 2, state: :terminal, runtime_attempt_id: ^attempt} = second
             ] = request_records(ctx)

      assert first.request_id != second.request_id
      assert second.prior_request_id == first.request_id
      assert first.send_may_have_occurred and second.send_may_have_occurred
      assert first.thread_id == result.thread_id and second.turn_id == result.turn_id

      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, @item, pilot_binding: ctx.grant)
      assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
      assert :ok = AttemptLedger.close(ctx.ledger)
      assert %{state: :stopverified, runtime_identity: ^identity, result: ^result} = fresh_pilot_status(ctx)
    end

    test "real stop cannot turn an unavailable C04 result store into success", ctx do
      opts = Keyword.merge(ctx.opts, runtime: FaultedStorage, fixture_storage_fault: :c04)

      assert {:raised, RuntimeError, "Pilot final evidence persistence failed"} = capture_fault(ctx, opts)

      assert_received {:fixture_closed_result_store, {:error, {:ledger_read_failed, {:error, :badarg}}}}
      assert_received {:runtime_attempt_lifecycle, @item, _, :containment_proven_dead}

      assert [%{ordinal: 1, state: :terminal}, %{ordinal: 2, state: :terminal}] = request_records(ctx)
      assert %{"events" => events} = fault_receipt(ctx, "functional-rpc-observations.json")
      assert Enum.any?(events, &match?(%{"method" => "item/completed", "phase" => "final_answer"}, &1))
      assert Enum.any?(events, &match?(%{"method" => "turn/completed", "status" => "completed"}, &1))
      assert %{"helper_stopped" => true, "tool_stopped" => true} = fault_receipt(ctx, "functional-broker-stop.json")
      assert %{"pid1_stop_verified" => true, "port_down_observed" => true} = fault_receipt(ctx, "routed-stop-observation.json")
      assert File.regular?(Path.join(ctx.directory, "functional-stop.json"))
      identity = ctx.opts[:runtime_attempt_identity]
      assert %{state: :running, runtime_identity: ^identity, result: nil} = fresh_pilot_status(ctx)
      IO.puts("C04_FRESH_BEAM: running, result absent, original identity retained")

      {:ok, recovered} = AttemptLedger.open(ctx.grant.project_id, ctx.tracker, root: ctx.root)

      try do
        assert {:ok, %{state: :running, runtime_identity: ^identity, result: nil}} =
                 AttemptLedger.pilot_status(recovered)

        assert {:error, _} = AttemptLedger.begin_attempt(recovered, @item, pilot_binding: ctx.grant)
        retry_opts = Keyword.put(ctx.opts, :attempt_ledger, recovered)
        assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), retry_opts) end
      after
        AttemptLedger.close(recovered)
      end
    end

    for fault <- ["lost_ack", "incomplete"] do
      @tag fixture_fault: fault
      @tag fault_case: fault
      test "#{fault} retains the first effect and cannot authorize a second request", ctx do
        actual = capture_fault(ctx, ctx.opts)
        assert {:returned, {:error, {:runtime_containment_unconfirmed, :termination_timeout}}} = actual

        %{runtime_attempt_id: attempt} = identity = ctx.opts[:runtime_attempt_identity]

        assert [%{ordinal: 1, runtime_attempt_id: ^attempt, state: :ambiguous, send_may_have_occurred: true}] =
                 request_records(ctx)

        assert_received {:runtime_attempt_lifecycle, @item, ^identity, {:containment_unconfirmed, :termination_timeout}}
        refute File.exists?(Path.join(ctx.directory, "routed-stop-observation.json"))

        assert {:ok,
                %{
                  state: :quarantined,
                  runtime_identity: ^identity,
                  quarantine_reason: :termination_unconfirmed,
                  result: %{outcome: :failed, model_state: :failed, stop_disposition: :quarantined, final_answer: nil}
                }} = AttemptLedger.pilot_status(ctx.ledger)

        assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, @item, pilot_binding: ctx.grant)
        assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
      end
    end

    for fault <- ["wrong_call", "wrong_output", "interrupt"] do
      @tag fixture_fault: fault
      @tag fault_case: fault
      test "#{fault} refuses any further provider request", ctx do
        actual = capture_fault(ctx, ctx.opts)
        assert {:returned, {:error, {:runtime_containment_unconfirmed, :termination_timeout}}} = actual

        %{runtime_attempt_id: attempt} = identity = ctx.opts[:runtime_attempt_identity]
        state = if ctx.fixture_fault == "interrupt", do: :ambiguous, else: :terminal
        assert [%{ordinal: 1, runtime_attempt_id: ^attempt, state: ^state}] = request_records(ctx)

        assert {:ok,
                %{
                  state: :quarantined,
                  runtime_identity: ^identity,
                  result: %{outcome: :failed, stop_disposition: :quarantined, final_answer: nil}
                }} = AttemptLedger.pilot_status(ctx.ledger)

        if ctx.fixture_fault == "wrong_output" do
          assert %{"helper_stopped" => true, "tool_stopped" => true} = fault_receipt(ctx, "functional-broker-stop.json")
        else
          refute File.exists?(Path.join(ctx.directory, "broker-start-consumed"))
        end

        assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
      end
    end

    test "unavailable intent journal blocks request 1 before a possible send", ctx do
      path = Path.join(ctx.directory, "provider-effects.journal")
      opts = Keyword.merge(ctx.opts, runtime: FaultedStorage, fixture_storage_fault: {:request_intent, path})
      actual = capture_fault(ctx, opts)

      assert {:returned, {:error, {:runtime_containment_unconfirmed, :termination_timeout}}} = actual
      assert_received {:fixture_intent_store_blocked, ^path}
      %{runtime_attempt_id: attempt} = ctx.opts[:runtime_attempt_identity]
      assert {:error, :journal_not_regular} = RequestLedger.open(attempt, path: path)
      assert Path.wildcard(Path.join(ctx.directory, "request-effect-*.jsonl")) == []
      refute File.exists?(Path.join(ctx.directory, "broker-start-consumed"))

      assert {:ok, %{state: :quarantined, result: %{outcome: :failed, stop_disposition: :quarantined}}} =
               AttemptLedger.pilot_status(ctx.ledger)

      assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
    end

    @tag fixture_fault: "observe_failure"
    test "terminal model output cannot substitute for the missing native stop receipt", ctx do
      assert_raise RuntimeError, "Pilot execution failed", fn ->
        AgentRunner.run(ctx.issue, self(), ctx.opts)
      end

      assert [%{ordinal: 1, state: :terminal}, %{ordinal: 2, state: :terminal}] = request_records(ctx)
      refute File.exists?(Path.join(ctx.directory, "routed-stop-observation.json"))

      assert {:ok, %{state: :quarantined, result: %{outcome: :failed, stop_disposition: :quarantined}}} =
               AttemptLedger.pilot_status(ctx.ledger)
    end

    @tag fixture_fault: "contradictory_final"
    @tag fault_case: "contradictory_final"
    test "the compiled holder rejects contradictory final content before C04 completion", ctx do
      identity = ctx.opts[:runtime_attempt_identity]

      assert {:returned, {:error, {:runtime_containment_unconfirmed, :termination_timeout}}} =
               capture_fault(ctx, ctx.opts)

      assert [%{ordinal: 1, state: :terminal}, %{ordinal: 2, state: :ambiguous, send_may_have_occurred: true}] =
               request_records(ctx)

      assert {:ok, %{state: :quarantined, runtime_identity: ^identity, result: result}} =
               AttemptLedger.pilot_status(ctx.ledger)

      assert %{outcome: :failed, final_answer: nil} = result

      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, @item, pilot_binding: ctx.grant)
      assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
    end

    defp fault_receipt(ctx, file), do: ctx.directory |> Path.join(file) |> File.read!() |> Jason.decode!()

    defp capture_fault(ctx, opts) do
      actual =
        try do
          {:returned, AgentRunner.run(ctx.issue, self(), opts)}
        rescue
          error -> {:raised, error.__struct__, Exception.message(error)}
        end

      IO.puts("FAULT_ACTUAL_RETURN: #{inspect(actual)}")
      IO.puts("FAULT_PILOT_STATUS: #{inspect(AttemptLedger.pilot_status(ctx.ledger))}")
      actual
    end

    defp request_records(ctx) do
      path = Path.join(ctx.directory, "provider-effects.journal")
      attempt = ctx.opts[:runtime_attempt_identity].runtime_attempt_id
      assert {:ok, ledger} = RequestLedger.open(attempt, path: path)
      RequestLedger.records(ledger)
    end

    defp fresh_pilot_status(ctx) do
      code =
        "alias SymphonyElixir.AgentRuntime.AttemptLedger; " <>
          "{:ok, ledger} = AttemptLedger.open(#{inspect(ctx.grant.project_id)}, #{inspect(ctx.tracker)}, root: #{inspect(ctx.root)}); " <>
          "{:ok, state} = AttemptLedger.pilot_status(ledger); " <>
          ":ok = AttemptLedger.close(ledger); IO.puts(Base.encode64(:erlang.term_to_binary(state)))"

      code_paths = Enum.flat_map(:code.get_path(), &["-pa", List.to_string(&1)])

      {output, 0} =
        System.cmd(System.find_executable("elixir"), code_paths ++ ["-e", code], stderr_to_stdout: true, env: [{"ERL_FLAGS", "+S 2:2 +SDio 1 +SDcpu 1"}])

      output |> String.trim() |> Base.decode64!() |> :erlang.binary_to_term([:safe])
    end

    defp holder_selection(holder) do
      %{
        "profile" => "siwc_planner_pilot_v1",
        "contract" => "SIWC_CHATGPT_PLAN_OAUTH_RESPONSES",
        "holder_profile_identity" => String.duplicate("a", 64),
        "holder_artifact_identity" => digest(File.read!(holder)),
        "host_permission_ref" => "synthetic-permission-1",
        "registration_ref" => "synthetic-registration-1",
        "credential_generation" => 1,
        "host_id" => "synthetic-host-1",
        "host_boot_id" => "synthetic-boot-1",
        "lifetime_budget" => %{
          "startup_allowance_ms" => 1_000,
          "maximum_attempt_wall_time_ms" => 25_000,
          "cleanup_allowance_ms" => 5_000,
          "clock_skew_bound_ms" => 1_000,
          "credential_safety_margin_ms" => 1_000
        }
      }
    end

    defp put_fixture_env(key, value) do
      prior = Application.fetch_env(:symphony_elixir, key)
      Application.put_env(:symphony_elixir, key, value)

      on_exit(fn ->
        case prior do
          {:ok, old} -> Application.put_env(:symphony_elixir, key, old)
          :error -> Application.delete_env(:symphony_elixir, key)
        end
      end)
    end

    defp git!(source, args) do
      {output, 0} = System.cmd("/usr/bin/git", ["-c", "core.hooksPath=/dev/null", "-C", source | args], stderr_to_stdout: true)
      output
    end

    defp digest(bytes), do: :crypto.hash(:sha256, bytes) |> Base.encode16(case: :lower)
  end
end
