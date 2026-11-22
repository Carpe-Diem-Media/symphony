defmodule SymphonyElixir.C02SyntheticHost do
  @moduledoc false
  use GenServer

  def start_link(journal, recipient), do: GenServer.start_link(__MODULE__, {journal, recipient})

  @impl true
  def init({journal, recipient}) do
    {public, private} = :crypto.generate_key(:eddsa, :ed25519)
    state = %{journal: journal, recipient: recipient, public: public, private: private}
    {:ok, Map.merge(state, %{stages: [], mutations: %{}, last: nil})}
  end

  @impl true
  def handle_call(:public_key, _from, state), do: {:reply, state.public, state}
  def handle_call({:mutate, phase, mutation}, _from, state), do: {:reply, :ok, %{state | mutations: Map.put(state.mutations, phase, mutation)}}
  def handle_call(:journal, _from, state), do: {:reply, File.read(state.journal), state}

  def handle_call({:pilot_holder_receipt, phase, binding, challenge}, _from, state) do
    send(state.recipient, {:holder_phase, phase})
    mutation = Map.get(state.mutations, phase)

    cond do
      mutation == :unavailable -> {:reply, {:error, :unavailable}, state}
      mutation == :timeout -> {:noreply, state}
      mutation == :replay -> {:reply, state.last, state}
      mutation == :sync_failure -> {:reply, {:error, :sync_failed}, state}
      phase in state.stages -> {:reply, {:error, :already_consumed}, state}
      true -> make_receipt(phase, binding, challenge, mutation, state)
    end
  end

  defp make_receipt(phase, binding, challenge, mutation, state) do
    payload = %{
      "schema" => "C02-SYNTHETIC-RECEIPT-1",
      "phase" => Atom.to_string(phase),
      "binding" => binding,
      "challenge" => challenge,
      "holder_ref" => "synthetic-holder-1",
      "durable_ref" => "synthetic-receipt-#{length(state.stages) + 1}",
      "access_expires_ms" => binding.absolute_deadline_ms + 60_000,
      "lease_expires_ms" => binding.absolute_deadline_ms,
      "disposition" => if(phase == :cleanup, do: "disposed", else: "ready")
    }

    payload = if is_function(mutation, 1), do: mutation.(payload), else: payload
    bytes = :erlang.term_to_binary(payload, [:deterministic])
    # Non-live fixture signing key stays in this test process. Only the nonsecret
    # receipt is journaled and synchronized before its signed response is sent.
    {:ok, file} = :file.open(String.to_charlist(state.journal), [:append, :binary, :raw])
    :ok = :file.write(file, <<byte_size(bytes)::32, bytes::binary>>)
    :ok = :file.sync(file)
    :ok = :file.close(file)
    signature = :crypto.sign(:eddsa, :none, bytes, [state.private, :ed25519])
    signature = if mutation == :bad_signature, do: <<0::512>>, else: signature
    response = {:synthetic_receipt, payload, signature}
    {:reply, response, %{state | stages: state.stages ++ [phase], last: response}}
  end
end

defmodule SymphonyElixir.PilotHolderInterfaceTest do
  use SymphonyElixir.TestSupport

  alias SymphonyElixir.AgentRuntime.{AttemptLedger, HostBoundary, NativePilot, Router, RuntimeIsolation}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.C02SyntheticHost
  alias SymphonyElixir.Codex.IsolationProfile
  alias SymphonyElixir.Config.Schema
  alias SymphonyElixir.ProviderEffect.RequestLedger
  alias SymphonyElixir.WorkControl.{WorkflowLifecycle, WorkItem}

  @plane_project "11111111-1111-4111-8111-111111111111"
  @workspace "33333333-3333-4333-8333-333333333333"
  @item "22222222-2222-4222-8222-222222222222"
  @prompt "Inspect the small tracked file and return a short technical plan."

  setup_all do
    native = Path.expand("../../../native/pilot_c02", __DIR__)
    # Rebuild from the tracked C sources, then verify the native lifecycle before
    # any test can select the holder probe. A stale local binary is insufficient.
    {output, status} = System.cmd("/usr/bin/make", ["--always-make", "-C", native, "check"], stderr_to_stdout: true)
    assert status == 0, "Native C02 fixture build/verification failed:\n#{output}"
    :ok
  end

  setup context do
    prior_plane_key = System.get_env("PLANE_API_KEY")
    System.put_env("PLANE_API_KEY", "SYNTHETIC-NONLIVE-PLANE-KEY")
    on_exit(fn -> restore_env("PLANE_API_KEY", prior_plane_key) end)

    root = Path.dirname(Workflow.workflow_file_path())
    source = Path.join(root, "source")
    File.mkdir_p!(source)
    git!(source, ["init", "-q"])
    File.write!(Path.join(source, "sample.ex"), "defmodule Sample, do: def(value, do: 1)\n")
    git!(source, ["add", "sample.ex"])
    git!(source, ["-c", "user.name=Offline fixture", "-c", "user.email=offline@example.invalid", "-c", "commit.gpgSign=false", "commit", "-qm", "Synthetic fixture"])
    [commit, tree] = git!(source, ["rev-parse", "HEAD", "HEAD^{tree}"]) |> String.split()
    codex = Path.join(root, "codex")
    protocol_log = Path.join(root, "synthetic-protocol-methods.jsonl")
    File.write!(codex, synthetic_codex(protocol_log))
    File.chmod!(codex, 0o700)

    native_codex =
      if context[:native_schema2], do: System.get_env("PINNED_CODEX_SCHEMA2_BINARY"), else: System.get_env("PINNED_CODEX_BINARY")

    if context[:native_boundary] do
      File.cp!(native_codex || Path.expand("../native/pilot_c02/build/holder-probe"), codex)
    end

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

    raw =
      if context[:native_schema2] || context[:schema2_boundary] do
        put_in(raw, ["agent", "profiles"], %{"planner" => %{"model" => "synthetic-planner-v1"}})
      else
        raw
      end

    selector = %{
      "profile" => "siwc_planner_pilot_v1",
      "contract" => "SIWC_CHATGPT_PLAN_OAUTH_RESPONSES",
      "holder_profile_identity" => String.duplicate("a", 64),
      "holder_artifact_identity" => Base.encode16(:crypto.hash(:sha256, File.read!(codex)), case: :lower),
      "host_permission_ref" => "synthetic-permission-1",
      "registration_ref" => "synthetic-registration-1",
      "credential_generation" => 1,
      "host_id" => "synthetic-host-1",
      "host_boot_id" => "synthetic-boot-1",
      "lifetime_budget" => %{
        "startup_allowance_ms" => 1_000,
        "maximum_attempt_wall_time_ms" => 120_000,
        "cleanup_allowance_ms" => 5_000,
        "clock_skew_bound_ms" => 1_000,
        "credential_safety_margin_ms" => 1_000
      }
    }

    raw = put_in(raw, ["agent", "pilot_holder"], selector)
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

    unless context[:full_runner], do: assert(:ok = AttemptLedger.claim_pilot_launch(ledger, grant, identity))
    {:ok, workspace} = Workspace.create_for_issue(issue, nil, opts[:ownership_ledger])
    {:ok, peer} = C02SyntheticHost.start_link(Path.join(root, "synthetic-host.journal"), self())
    public_key = GenServer.call(peer, :public_key)
    prior_peer = Application.get_env(:symphony_elixir, :test_pilot_holder_peer)
    Application.put_env(:symphony_elixir, :test_pilot_holder_peer, {peer, public_key})

    on_exit(fn ->
      if prior_peer,
        do: Application.put_env(:symphony_elixir, :test_pilot_holder_peer, prior_peer),
        else: Application.delete_env(:symphony_elixir, :test_pilot_holder_peer)
    end)

    opts =
      opts
      |> Keyword.put(:profile, route.profile)
      |> Keyword.put(:sandbox, route.profile.sandbox)
      |> Keyword.put(:command, route.profile.command)
      |> Keyword.put(:absolute_deadline_ms, System.monotonic_time(:millisecond) + grant.deadline_ms)
      |> Keyword.put(:test_pilot_holder_peer, {peer, public_key})
      |> Keyword.put(:runtime_issue, issue)

    opts =
      if context[:native_boundary] do
        native = Path.expand("../native/pilot_c02")
        files = Enum.map(~w(host guard holder-probe), &Path.join([native, "build", &1]))
        driver = Path.join(native, "tests/run_attempt.py")

        evidence_root =
          case System.get_env("PINNED_CODEX_EVIDENCE_ROOT") do
            nil -> Path.join(root, "native-evidence")
            path -> Path.join(path, identity.runtime_attempt_id)
          end

        pin = %{
          driver: driver,
          files: Map.new([driver, codex | files], &{&1, Base.encode16(:crypto.hash(:sha256, File.read!(&1)), case: :lower)}),
          holder: codex,
          evidence_root: evidence_root,
          fault: "none",
          pinned_codex: is_binary(native_codex)
        }

        pin =
          if mode = context[:native_schema2] do
            assert pin.pinned_codex, "Schema2 tests require the exact PINNED_CODEX_SCHEMA2_BINARY"
            catalog = Path.expand("../native/pinned_codex/tests/fixtures/synthetic_model.json")
            digest = Base.encode16(:crypto.hash(:sha256, File.read!(catalog)), case: :lower)

            Map.merge(pin, %{
              schema2: mode,
              model_catalog: catalog,
              files: Map.put(pin.files, catalog, digest),
              fault: Map.get(context, :native_stop_fault, "none")
            })
          else
            pin
          end

        Application.put_env(:symphony_elixir, :test_native_pilot, pin)
        on_exit(fn -> Application.delete_env(:symphony_elixir, :test_native_pilot) end)
        Keyword.put(opts, :test_native_pilot, pin)
      else
        opts
      end

    {:ok, Map.merge(fixture, %{workspace: workspace, selector: selector, opts: opts, peer: peer, raw: raw, protocol_log: protocol_log})}
  end

  @tag native_boundary: true
  test "C02 executes the native slice but refuses unqualified inference", ctx do
    assert {:error, :pilot_holder_native_controlled_refusal} = AppServer.start_session(ctx.workspace, ctx.opts)
    path = Path.join([ctx.opts[:test_native_pilot].evidence_root, ctx.identity.runtime_attempt_id, "correlation.json"])
    evidence = path |> File.read!() |> Jason.decode!()
    assert evidence["binding"]["attempt"]["runtime_attempt_id"] == ctx.identity.runtime_attempt_id
    assert evidence["binding"]["grant"]["config_identity"] == ctx.grant.config_identity
    assert evidence["native"]["native_exec"]
    assert evidence["native"]["stop_verified"]
    refute evidence["native"]["inference_succeeded"]
    refute_received {:holder_phase, _}
    assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
    assert {:error, :pilot_holder_native_refused} = AppServer.start_session(ctx.workspace, ctx.opts)
  end

  @tag native_boundary: true, full_runner: true
  test "native controlled refusal retains C01 and a noncompleted C04 result", ctx do
    opts = Keyword.put(ctx.opts, :runtime, SymphonyElixir.AgentRuntime.Codex)
    assert_raise RuntimeError, fn -> AgentRunner.run(ctx.issue, self(), opts) end
    assert {:ok, %{state: :quarantined, result: result}} = AttemptLedger.pilot_status(ctx.ledger)
    assert result.stop_disposition == :quarantined
    refute result.model_state == :completed
    path = Path.join([ctx.opts[:test_native_pilot].evidence_root, ctx.identity.runtime_attempt_id, "correlation.json"])
    assert File.regular?(path)

    if System.get_env("PINNED_CODEX_EVIDENCE_ROOT") do
      observation = %{
        runtime_attempt_id: ctx.identity.runtime_attempt_id,
        model_state: result.model_state,
        stop_disposition: result.stop_disposition
      }

      File.write!(Path.join(Path.dirname(path), "c04-observation.json"), Jason.encode!(observation))
    end

    refute_received {:holder_phase, _}
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
  end

  describe "schema2 adapter refusal without a Codex binary" do
    @describetag schema2_boundary: true

    test "invalid mode and missing pinned selection stop before launch", ctx do
      {binding, pin} = schema2_refusal_fixture(ctx)
      assert_prelaunch_refusal(binding, %{pin | schema2: :unexpected})
      assert_prelaunch_refusal(binding, %{pin | pinned_codex: false})
    end

    test "missing, unreadable and unpinned catalog inputs stop before launch", ctx do
      {binding, pin} = schema2_refusal_fixture(ctx)
      assert_prelaunch_refusal(binding, Map.delete(pin, :model_catalog))
      assert_prelaunch_refusal(binding, %{pin | model_catalog: ctx.workspace})
      assert_prelaunch_refusal(binding, %{pin | files: Map.delete(pin.files, pin.model_catalog)})
    end

    test "catalog must declare exactly the bound model", ctx do
      {binding, pin} = schema2_refusal_fixture(ctx)

      for catalog <- ["{", ~s({"models":[]}), ~s({"models":[{"slug":"other-model"}]})] do
        File.write!(pin.model_catalog, catalog)
        assert_prelaunch_refusal(binding, %{pin | files: Map.put(pin.files, pin.model_catalog, digest_file(pin.model_catalog))})
      end
    end

    test "stale configuration, runtime profile and tracked bytes stop before launch", ctx do
      {binding, pin} = schema2_refusal_fixture(ctx)
      assert_prelaunch_refusal(put_in(binding.grant.config_identity, String.duplicate("0", 64)), pin)
      assert_prelaunch_refusal(put_in(binding.attempt.runtime_profile, "builder"), pin)
      File.write!(Path.join(ctx.workspace, "sample.ex"), "unapproved tracked bytes")
      assert_prelaunch_refusal(binding, pin)
      assert {:ok, %{state: :running, runtime_identity: identity}} = AttemptLedger.pilot_status(ctx.ledger)
      assert identity == ctx.identity
      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
    end

    test "missing and altered sealed manifest observations refuse", ctx do
      {binding, pin} = schema2_refusal_fixture(ctx)

      for fault <- ["missing_manifest", "wrong_manifest_context"] do
        directory = assert_observation_refusal(binding, %{pin | fault: fault})
        refute File.exists?(Path.join(directory, "adapter-observation.json"))
      end
    end

    test "retryable core error and unverified stop cannot certify synthetic disposal", ctx do
      {binding, pin} = schema2_refusal_fixture(ctx)

      for fault <- ["retryable_error", "missing_disposal", "wrong_stop_pid", "wrong_stop_order"] do
        directory = assert_observation_refusal(binding, %{pin | fault: fault})

        assert %{
                 "attempt" => attempt,
                 "outcome" => "pilot_holder_native_refused",
                 "synthetic_stop_verified" => false,
                 "operational_namespace_qualified" => false
               } = directory |> Path.join("adapter-observation.json") |> File.read!() |> Jason.decode!()

        assert attempt == ctx.identity.runtime_attempt_id
      end

      refute File.exists?(ctx.protocol_log)
    end
  end

  describe "routed functional provider-effect boundary" do
    @describetag schema2_boundary: true

    test "binds and completes precisely two correlated provider requests", ctx do
      holder = functional_effect_fixture(ctx)
      assert {:ok, boundary} = HostBoundary.open(holder, "thread-1", "turn-1")
      refute File.exists?(Path.join(holder.directory, "provider-effects.journal"))
      assert {:error, :provider_effect_completion_unconfirmed} = HostBoundary.completed?(boundary)

      wrong_route = effect_descriptor(%{"url" => "https://unexpected.invalid/v1/responses"})
      assert {:error, :provider_descriptor_refused} = send_effect(boundary, 1, "VALIDATE_DESCRIPTOR", wrong_route)
      assert {:error, :provider_descriptor_refused} = send_effect(boundary, 2, "VALIDATE_DESCRIPTOR", second_descriptor())
      assert {:error, :provider_effect_frame_refused} = send_effect(boundary, 1, "UNRECOGNIZED", %{})
      assert {:error, :provider_effect_frame_refused} = HostBoundary.effect(boundary, [])

      {intent, boundary} = prepare_effect(boundary)
      assert {:error, :provider_effect_frame_refused} = HostBoundary.effect(boundary, %{"sequence" => boundary.sequence})
      assert {:error, :provider_possible_send_refused} = acknowledge_effect(boundary, %{intent | "revision" => 2})
      assert {:error, :provider_possible_send_refused} = acknowledge_effect(boundary, %{intent | "request_id" => "unknown"})
      assert {:error, :provider_acceptance_refused} = send_effect(boundary, 1, "OBSERVED_ACCEPTANCE", response_fields(intent, 1))
      {permission, boundary} = allow_effect(boundary, intent)
      assert permission["kind"] == "INVOCATION_PERMITTED"
      assert {:error, :provider_possible_send_refused} = acknowledge_effect(boundary, intent)
      expired = expired_effect(boundary)

      assert {:error, :provider_effect_frame_refused} =
               send_effect(expired, 1, "OBSERVED_ACCEPTANCE", response_fields(intent, 1))

      assert {:error, :provider_acceptance_refused} =
               send_effect(boundary, 1, "OBSERVED_ACCEPTANCE", %{response_fields(intent, 1) | "response_id" => " invalid"})

      assert {:error, :provider_terminal_refused} = send_effect(boundary, 1, "TERMINAL_CONFIRMATION", terminal_fields(intent, 1))
      boundary = complete_effect(boundary, intent, 1)
      assert {:error, :provider_effect_completion_unconfirmed} = HostBoundary.completed?(boundary)
      expired = expired_effect(boundary)
      assert {:error, :provider_effect_frame_refused} = send_effect(expired, 2, "VALIDATE_DESCRIPTOR", second_descriptor())

      assert {:error, :provider_descriptor_refused} =
               send_effect(boundary, 2, "VALIDATE_DESCRIPTOR", effect_descriptor(Map.put(second_descriptor_fields(), "tool_call_id", "wrong")))

      assert {:ok, second, boundary} = send_effect(boundary, 2, "VALIDATE_DESCRIPTOR", second_descriptor())
      {_, boundary} = allow_effect(boundary, second, 2)

      assert {:ok, %{"stage" => "accepted"}, second_accepted} =
               send_effect(boundary, 2, "OBSERVED_ACCEPTANCE", response_fields(second, 2))

      expired = expired_effect(second_accepted)

      assert {:error, :provider_effect_frame_refused} =
               send_effect(expired, 2, "TERMINAL_CONFIRMATION", terminal_fields(second, 2))

      assert {:ok, %{"stage" => "terminal"}, boundary} =
               send_effect(second_accepted, 2, "TERMINAL_CONFIRMATION", terminal_fields(second, 2))

      assert :ok = HostBoundary.completed?(boundary)
      assert :ok = HostBoundary.close(boundary)
      assert {:ok, %{closed?: true} = ledger} = read_effects(holder)
      assert [%{ordinal: 1, state: :terminal}, %{ordinal: 2, state: :terminal}] = RequestLedger.records(ledger)
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    test "recovers a native acknowledgment lost before host handoff without replay", ctx do
      holder = functional_effect_fixture(ctx)
      assert {:ok, boundary} = HostBoundary.open(holder, "thread-1", "turn-1")
      {intent, boundary} = prepare_effect(boundary)
      assert 0 == record_native_effect(holder, intent, "PRE_SEND_INTENT", 1)
      assert 0 == record_native_effect(holder, intent, "POSSIBLE_SEND_ACK", 1)
      assert 1 == record_native_effect(holder, intent, "POSSIBLE_SEND_ACK", 1)

      assert {:ok, ledger} = read_effects(holder)
      assert [%{ordinal: 1, state: :pre_send_intent, send_may_have_occurred: false}] = RequestLedger.records(ledger)
      assert ["PRE_SEND_INTENT", "POSSIBLE_SEND_ACK"] = native_effect_states(holder, intent)
      assert {:ok, recovered} = HostBoundary.open(holder, "thread-1", "turn-1")
      assert :ok = HostBoundary.close(recovered)
      assert {:error, :provider_possible_send_refused} = acknowledge_effect(boundary, intent)
      assert {:ok, %{closed?: true}} = read_effects(holder)
      assert ["PRE_SEND_INTENT", "POSSIBLE_SEND_ACK"] = native_effect_states(holder, intent)
      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
    end

    test "recovers a lost recorded invocation permission and refuses an additional ordinal", ctx do
      holder = functional_effect_fixture(ctx)
      assert {:ok, boundary} = HostBoundary.open(holder, "thread-1", "turn-1")
      {intent, boundary} = prepare_effect(boundary)
      assert 0 == record_native_effect(holder, intent, "PRE_SEND_INTENT", 1)
      assert 0 == record_native_effect(holder, intent, "POSSIBLE_SEND_ACK", 1)
      {permission, boundary} = allow_effect(boundary, intent)
      assert permission["revision"] == 2
      assert 0 == record_native_effect(holder, intent, "INVOCATION_PERMITTED", 2)
      assert 1 == record_native_effect(holder, intent, "INVOCATION_PERMITTED", 2)
      assert {:ok, ledger} = read_effects(holder)
      assert [%{state: :possible_send, send_may_have_occurred: true}] = RequestLedger.records(ledger)
      assert {:ok, without_permit} = HostBoundary.open(holder, "thread-1", "turn-1")

      assert {:error, :provider_acceptance_refused} =
               send_effect(without_permit, 1, "OBSERVED_ACCEPTANCE", response_fields(intent, 1))

      assert :ok = HostBoundary.close(without_permit)
      assert {:ok, %{closed?: true} = ledger} = read_effects(holder)
      assert [%{ordinal: 1, state: :ambiguous, send_may_have_occurred: true}] = RequestLedger.records(ledger)
      assert {:error, :provider_descriptor_refused} = send_effect(boundary, 2, "VALIDATE_DESCRIPTOR", second_descriptor())
      assert ["PRE_SEND_INTENT", "POSSIBLE_SEND_ACK", "INVOCATION_PERMITTED"] = native_effect_states(holder, intent)
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    test "expired and revoked bindings fence effects without erasing retained intent", ctx do
      holder = functional_effect_fixture(ctx)
      assert {:ok, boundary} = HostBoundary.open(holder, "thread-1", "turn-1")
      {intent, boundary} = prepare_effect(boundary)
      assert 0 == record_native_effect(holder, intent, "PRE_SEND_INTENT", 1)
      expired = expired_effect(boundary)

      for {kind, attrs} <- [
            {"VALIDATE_DESCRIPTOR", effect_descriptor()},
            {"POSSIBLE_SEND_ACK", ack_fields(intent)},
            {"OBSERVED_ACCEPTANCE", response_fields(intent, 1)},
            {"TERMINAL_CONFIRMATION", terminal_fields(intent, 1)}
          ] do
        assert {:error, :provider_effect_frame_refused} = send_effect(expired, 1, kind, attrs)
      end

      File.rm!(Path.join(holder.directory, "permission"))
      assert 1 == record_native_effect(holder, intent, "POSSIBLE_SEND_ACK", 1)
      assert :ok = AttemptLedger.quarantine_pilot(ctx.ledger, ctx.identity, :worker_lost)
      assert {:error, :pilot_holder_binding_invalid} = acknowledge_effect(boundary, intent)
      assert :ok = HostBoundary.close(boundary)
      assert {:ok, %{closed?: true} = ledger} = read_effects(holder)
      assert [%{state: :pre_send_intent, send_may_have_occurred: false}] = RequestLedger.records(ledger)
      assert ["PRE_SEND_INTENT"] = native_effect_states(holder, intent)
      assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    test "revoking permission after acceptance refuses terminal and retains a possible effect", ctx do
      holder = functional_effect_fixture(ctx)
      assert {:ok, boundary} = HostBoundary.open(holder, "thread-1", "turn-1")
      {intent, boundary} = prepare_effect(boundary)
      assert 0 == record_native_effect(holder, intent, "PRE_SEND_INTENT", 1)
      assert 0 == record_native_effect(holder, intent, "POSSIBLE_SEND_ACK", 1)
      {_, boundary} = allow_effect(boundary, intent)
      assert 0 == record_native_effect(holder, intent, "INVOCATION_PERMITTED", 2)

      assert {:ok, %{"stage" => "accepted"}, boundary} =
               send_effect(boundary, 1, "OBSERVED_ACCEPTANCE", response_fields(intent, 1))

      assert 0 == record_native_effect(holder, intent, "OBSERVED_ACCEPTANCE", 2)

      expired = expired_effect(boundary)
      assert {:error, :provider_effect_frame_refused} = send_effect(expired, 1, "TERMINAL_CONFIRMATION", terminal_fields(intent, 1))

      File.rm!(Path.join(holder.directory, "permission"))
      assert 1 == record_native_effect(holder, intent, "TERMINAL_CONFIRMATION", 3)
      assert :ok = AttemptLedger.quarantine_pilot(ctx.ledger, ctx.identity, :worker_lost)
      assert {:error, :pilot_holder_binding_invalid} = send_effect(boundary, 1, "TERMINAL_CONFIRMATION", terminal_fields(intent, 1))
      assert {:error, :pilot_holder_binding_invalid} = send_effect(boundary, 2, "VALIDATE_DESCRIPTOR", second_descriptor())
      assert :ok = HostBoundary.close(boundary)
      assert {:ok, %{closed?: true} = ledger} = read_effects(holder)
      assert [%{ordinal: 1, state: :ambiguous, send_may_have_occurred: true}] = RequestLedger.records(ledger)
      assert ["PRE_SEND_INTENT", "POSSIBLE_SEND_ACK", "INVOCATION_PERMITTED", "OBSERVED_ACCEPTANCE"] = native_effect_states(holder, intent)
      assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    test "AppServer forwards functional effects and refuses a premature final item", ctx do
      holder = functional_effect_fixture(ctx)
      assert {:error, :provider_effect_completion_unconfirmed} = run_effect_port(ctx, holder, "premature-final")
      assert {:ok, %{closed?: true} = ledger} = read_effects(holder)
      assert [] = RequestLedger.records(ledger)
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    test "AppServer returns a result only after both durable terminal observations", ctx do
      holder = functional_effect_fixture(ctx)
      assert {:ok, %{turn_id: "turn-1", thread_id: "thread-1"}} = run_effect_port(ctx, holder, "complete")
      assert {:ok, %{closed?: true} = ledger} = read_effects(holder)
      assert [%{ordinal: 1, state: :terminal}, %{ordinal: 2, state: :terminal}] = RequestLedger.records(ledger)
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    test "AppServer expires an acknowledged effect while fresh messages keep arriving", ctx do
      deadline = System.monotonic_time(:millisecond) + 7_000
      ctx = update_in(ctx.opts, &Keyword.put(&1, :absolute_deadline_ms, deadline))
      holder = functional_effect_fixture(ctx)

      assert {:error, reason} = run_effect_port(ctx, holder, "continuous")
      assert reason in [:turn_timeout, :native_functional_timeout]
      assert System.monotonic_time(:millisecond) >= deadline
      assert {:ok, %{closed?: true} = ledger} = read_effects(holder)
      assert [%{ordinal: 1, state: :ambiguous, send_may_have_occurred: true}] = RequestLedger.records(ledger)
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    for {fault, reason} <- [
          {"interrupted", :native_functional_turn_failed},
          {"protocol-error", :native_functional_turn_failed},
          {"wrong-turn", :native_functional_turn_refused},
          {"invalid-frame", :native_functional_frame_refused},
          {"oversized-frame", :native_functional_frame_refused}
        ] do
      test "AppServer closes effect admission after #{fault}", ctx do
        holder = functional_effect_fixture(ctx)
        assert {:error, unquote(reason)} = run_effect_port(ctx, holder, unquote(fault))
        assert {:ok, %{closed?: true} = ledger} = read_effects(holder)
        assert [] = RequestLedger.records(ledger)
        assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
      end
    end

    test "a malformed or refused turn start cannot open the provider-effect journal", ctx do
      holder = functional_effect_fixture(ctx)
      assert {:error, :native_functional_turn_refused} = run_effect_port(ctx, holder, "missing-turn-id")

      assert {:error, {:response_error, %{"code" => -32_603, "message" => "fixture refused turn"}}} =
               run_effect_port(ctx, holder, "turn-start-error")

      refute File.exists?(Path.join(holder.directory, "provider-effects.journal"))
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    for {case_name, fault, observation, expected} <- [
          {"no namespace observation", "stop", :missing, {:containment_unconfirmed, :termination_timeout}},
          {"a still-live observed process", "stop", :live, {:containment_unconfirmed, :termination_timeout}},
          {"a stopped process but invalid native control", "invalid-stop", :peer, :native_functional_observation_refused}
        ] do
      test "retains home after routed shutdown with #{case_name}", ctx do
        holder = functional_effect_fixture(ctx)
        assert {:error, unquote(Macro.escape(expected))} = stop_effect_port(holder, unquote(fault), unquote(observation))
        assert File.dir?(Path.join(holder.directory, "retained-home"))
        refute File.exists?(Path.join(holder.directory, "routed-stop-observation.json"))
        assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
      end
    end

    test "refuses functional launch if the selected driver pin or profile does not match", ctx do
      holder = functional_effect_fixture(ctx)
      pin = holder.pin
      pin = update_in(pin.files, &Map.delete(&1, pin.driver))
      Application.put_env(:symphony_elixir, :test_native_pilot, pin)

      assert {:error, :native_schema2_input_refused} = NativePilot.prepare_functional(holder.binding, pin, holder.opts)

      unselected = %{pin | schema2: :strict_fault}
      assert {:error, :pilot_holder_boundary_unavailable} = NativePilot.prepare_functional(holder.binding, unselected, holder.opts)
      boundary_unavailable = {:error, :pilot_holder_boundary_unavailable}
      assert ^boundary_unavailable = NativePilot.functional_command(%{holder | assurance: :unverified}, "/usr/bin/python3")
      refute File.exists?(Path.join(holder.directory, "provider-effects.journal"))
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    test "checks supervisor, broker and disposal receipt bindings after forward authority is revoked", ctx do
      holder = functional_effect_fixture(ctx)
      stop = functional_stop_fixture(holder)
      assert {:ok, _} = NativePilot.verify_functional_receipt(holder, :stopped, stop)
      assert {:ok, %{pid: 10, start_ticks: 1}} = NativePilot.host_supervisor_identity(holder, 9)
      assert {:error, :host_supervisor_unverified} = NativePilot.host_supervisor_identity(holder, 8)

      assert {:error, :native_functional_observation_refused} =
               NativePilot.verify_functional_receipt(holder, :stopped, %{stop | "sequence" => 0})

      assert :ok = AttemptLedger.quarantine_pilot(ctx.ledger, ctx.identity, :worker_lost)
      assert {:error, :pilot_holder_binding_invalid} = RuntimeIsolation.check_pilot_holder(holder, :turn)
      assert :ok = RuntimeIsolation.check_pilot_holder(holder, :cleanup)
      write_effect_fixture(holder, "disposed", "wrong binding")
      assert {:error, :native_functional_observation_refused} = RuntimeIsolation.check_pilot_holder(holder, :cleanup)
      write_effect_fixture(holder, "disposed", holder.digest)

      broker = Path.join(holder.directory, "functional-broker-stop.json") |> File.read!() |> Jason.decode!()

      for {key, value} <- [
            {"operation_id", "another-operation"},
            {"helper_stopped", false},
            {"tool", %{}},
            {"tool", broker["helper"]},
            {"supervisor_pid", 99}
          ] do
        write_effect_fixture(holder, "functional-broker-stop.json", Jason.encode!(Map.put(broker, key, value)))
        assert {:error, :native_functional_observation_refused} = RuntimeIsolation.check_pilot_holder(holder, :cleanup)
      end

      assert {:ok, %{state: :quarantined, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end

    test "correlates the startup receipt with the selected fixture and closed channel", ctx do
      holder = functional_effect_fixture(ctx)
      refused = {:error, :native_functional_observation_refused}
      fixture = Path.join(Path.dirname(holder.pin.driver), "provider_fixture.py")

      receipt = %{
        "scope" => "SYNTHETIC_PIPE",
        "kind" => "native-ready",
        "binding" => holder.digest,
        "attempt" => holder.binding.attempt.runtime_attempt_id,
        "sequence" => 0,
        "context_digest" => effect_digest("context"),
        "fixture_sha256" => holder.pin.files[fixture],
        "holder_pid" => 11,
        "guard_pid" => 12
      }

      bytes = Jason.encode!(receipt)
      write_effect_fixture(holder, "functional-ready.json", bytes)

      envelope =
        receipt
        |> Map.take(~w(binding attempt sequence context_digest holder_pid guard_pid))
        |> Map.merge(%{"schema" => "H100-NATIVE-CONTROL-1", "kind" => "ready", "receipt_sha256" => effect_digest(bytes)})

      assert {:ok, ^receipt} = NativePilot.verify_functional_receipt(holder, :ready, envelope)

      assert ^refused = NativePilot.verify_functional_receipt(holder, :ready, %{envelope | "holder_pid" => 12})

      for change <- [%{"fixture_sha256" => effect_digest("wrong fixture")}, %{"guard_pid" => 11}] do
        write_effect_fixture(holder, "functional-ready.json", Jason.encode!(Map.merge(receipt, change)))
        assert ^refused = NativePilot.verify_functional_receipt(holder, :ready, nil)
      end

      write_effect_fixture(holder, "functional-ready.json", bytes)
      File.rm!(Path.join(holder.directory, "channel-closed"))
      assert ^refused = NativePilot.verify_functional_receipt(holder, :ready, envelope)
    end

    test "retains a bound namespace stop once without replacing it with a changed identity", ctx do
      holder = functional_effect_fixture(ctx)
      path = Path.join(holder.directory, "routed-stop-observation.json")
      identity = %{pid: 11, parent_pid: 12, start_ticks: 2, namespace_inode: 3}

      assert {:error, :native_routed_stop_record_unavailable} = NativePilot.retain_namespace_stop(holder, nil)
      refute File.exists?(path)
      assert :ok = NativePilot.retain_namespace_stop(holder, identity)
      bytes = File.read!(path)
      digest = holder.digest
      attempt = ctx.identity.runtime_attempt_id

      assert %{
               "binding" => ^digest,
               "attempt" => ^attempt,
               "namespace_pid1" => %{"pid" => 11, "parent_pid" => 12, "start_ticks" => 2, "namespace_inode" => 3},
               "port_down_observed" => true,
               "pid1_stop_verified" => true
             } = Jason.decode!(bytes)

      changed_identity = %{identity | start_ticks: 4}
      refused = {:error, :native_routed_stop_record_unavailable}
      assert ^refused = NativePilot.retain_namespace_stop(holder, changed_identity)
      assert File.read!(path) == bytes
      assert {:ok, %{state: :running, result: nil}} = AttemptLedger.pilot_status(ctx.ledger)
    end
  end

  defp expired_effect(boundary) do
    put_in(boundary.holder.binding.absolute_deadline_ms, System.monotonic_time(:millisecond) - 1)
  end

  defp stop_effect_port(holder, fault, observation) do
    home = Path.join(holder.directory, "retained-home")
    File.mkdir!(home)
    stop = functional_stop_fixture(holder)
    assert {:ok, _} = NativePilot.verify_functional_receipt(holder, :stopped, stop)
    script = Path.expand("../support/h100_effect_peer.py", __DIR__)
    path = Path.join(holder.directory, "stop-peer.json")
    File.write!(path, Jason.encode!(%{fault: fault, stop: stop}))
    port = Port.open({:spawn_executable, "/usr/bin/python3"}, [:binary, :exit_status, {:line, 256}, {:args, ["-I", script, path]}])

    try do
      result =
        AppServer.stop_session(%{
          port: port,
          runtime_containment: :linux_pid_namespace,
          runtime_namespace: stop_observation(port, observation),
          pilot_holder_context: holder,
          absolute_deadline_ms: holder.binding.absolute_deadline_ms,
          ephemeral_home: home
        })

      refute Port.info(port)
      result
    after
      if Port.info(port), do: Port.close(port)
    end
  end

  defp stop_observation(_port, :missing), do: nil

  defp stop_observation(_port, :live), do: process_observation(String.to_integer(System.pid()))

  defp stop_observation(port, :peer) do
    {:os_pid, pid} = Port.info(port, :os_pid)
    process_observation(pid)
  end

  defp process_observation(pid) do
    [_, fields] = File.read!("/proc/#{pid}/stat") |> String.split(") ", parts: 2)
    start_ticks = fields |> String.split() |> Enum.at(19) |> String.to_integer()
    ["pid:", inode] = File.read_link!("/proc/#{pid}/ns/pid") |> String.split(["[", "]"], trim: true)
    # These local identities exercise the stop decision given a captured process.
    # The separate routed suite verifies actual namespace PID 1 containment.
    %{pid: pid, namespace_inode: String.to_integer(inode), start_ticks: start_ticks}
  end

  defp functional_stop_fixture(holder) do
    attempt = holder.binding.attempt.runtime_attempt_id
    journal = Jason.encode!(%{attempt: attempt, binding: holder.digest}) <> "\n"
    journal_sha = effect_digest(journal)
    manifest = Path.join(holder.directory, "manifest.json") |> File.read!() |> Jason.decode!()

    for file <- ~w(consumed guard-reaped disposed), do: write_effect_fixture(holder, file, holder.digest)
    write_effect_fixture(holder, "events.jsonl", journal)

    write_effect_fixture(
      holder,
      "functional-host-supervisor.json",
      Jason.encode!(%{
        schema: "H100-HOST-SUPERVISOR-1",
        binding: holder.digest,
        attempt: attempt,
        pid: 10,
        ppid: 9,
        start_ticks: 1
      })
    )

    write_effect_fixture(
      holder,
      "functional-broker-stop.json",
      Jason.encode!(%{
        schema: "H100-HOST-BROKER-STOP-1",
        binding: holder.digest,
        attempt: attempt,
        supervisor_pid: 10,
        operation_id: "tool-op-1",
        helper_stopped: true,
        tool_stopped: true,
        helper: %{pid: 11, start_ticks: 1},
        tool: %{pid: 12, start_ticks: 2}
      })
    )

    receipt = %{
      "scope" => "SYNTHETIC_PIPE",
      "kind" => "native-stopped",
      "binding" => holder.digest,
      "attempt" => attempt,
      "sequence" => 1,
      "context_digest" => manifest["context"]["context_digest"],
      "termination_observed" => true,
      "disposal_verified" => true,
      "journal_sha256" => journal_sha
    }

    bytes = Jason.encode!(receipt)
    write_effect_fixture(holder, "functional-stop.json", bytes)

    receipt
    |> Map.take(~w(binding attempt sequence context_digest journal_sha256 disposal_verified))
    |> Map.merge(%{"schema" => "H100-NATIVE-CONTROL-1", "kind" => "stopped", "guard_reaped" => true, "host_termination_observed" => true, "receipt_sha256" => effect_digest(bytes)})
  end

  defp run_effect_port(ctx, holder, fault) do
    assert {:ok, boundary} = HostBoundary.open(holder, "thread-1", "turn-1")

    spec = %{
      common: Map.drop(effect_frame(boundary, 1, "unused", %{}), ~w(kind ordinal sequence)),
      descriptors: [effect_descriptor(), second_descriptor()],
      terminal_sha256: effect_digest("terminal"),
      fault: fault
    }

    path = Path.join(holder.directory, "peer-test-input.json")
    File.write!(path, Jason.encode!(spec))
    script = Path.expand("../support/h100_effect_peer.py", __DIR__)
    port = Port.open({:spawn_executable, "/usr/bin/python3"}, [:binary, :exit_status, {:line, 128}, {:args, ["-I", script, path]}])

    session = %{
      port: port,
      metadata: %{},
      approval_policy: "never",
      auto_approve_requests: false,
      thread_id: "thread-1",
      workspace: ctx.workspace,
      dynamic_tool_binding: %{},
      pilot_holder_context: holder,
      absolute_deadline_ms: holder.binding.absolute_deadline_ms
    }

    try do
      AppServer.run_turn(session, @prompt, ctx.issue, model: holder.binding.profile.model, defer_runtime_stop: true)
    after
      if Port.info(port), do: Port.close(port)
    end
  end

  defp functional_effect_fixture(ctx) do
    {binding, pin} = schema2_refusal_fixture(ctx)
    native = Path.expand("../native/pilot_c02")
    driver = Path.join(native, "tests/run_attempt.py")

    files =
      [driver, Path.join(native, "tests/provider_fixture.py"), pin.holder, pin.model_catalog] ++
        Enum.map(~w(host guard tool-broker request-effect), &Path.join([native, "build", &1]))

    pin = %{pin | driver: driver, schema2: :functional, files: Map.new(files, &{&1, digest_file(&1)})}
    Application.put_env(:symphony_elixir, :test_native_pilot, pin)
    opts = ctx.opts |> Keyword.put(:model, ctx.route.profile.model) |> Keyword.put(:test_native_pilot, pin)
    assert {:ok, holder} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
    assert holder.binding == binding
    assert {:ok, ["/usr/bin/python3", "-I", ^driver | args]} = NativePilot.functional_command(holder, "/usr/bin/python3")
    assert "--interactive" in args
    assert "--schema2" in args

    expired = put_in(holder.binding.absolute_deadline_ms, System.monotonic_time(:millisecond))
    assert {:error, :native_functional_launch_refused} = NativePilot.functional_command(expired, "/usr/bin/python3")

    context = holder.directory |> Path.join("schema2-input.json") |> File.read!() |> Jason.decode!() |> Map.fetch!("context")
    deadline = 9_999_999_999_999
    nonce = effect_digest("nonce")
    fixture = pin.files[Path.join(native, "tests/provider_fixture.py")]
    broker = %{"binding" => %{"operation_id" => "tool-op-1", "tool_call_id" => "call-1", "deadline_ms" => deadline}}
    context = Map.merge(context, %{"context_digest" => effect_digest("context"), "broker_selftest" => broker, "model_catalog_digest" => pin.files[pin.model_catalog]})

    manifest = %{"binding" => holder.digest, "context" => context, "deadline_ms" => deadline, "provider" => %{"nonce" => nonce, "fixture_sha256" => fixture}}
    write_effect_fixture(holder, "manifest.json", Jason.encode!(manifest))
    assert {:error, :provider_boundary_unavailable} = HostBoundary.open(holder, "thread-1", "turn-1")

    write_effect_fixture(holder, "channel-closed", holder.digest)

    write_effect_fixture(
      holder,
      "functional-ready.json",
      Jason.encode!(%{
        "scope" => "SYNTHETIC_PIPE",
        "kind" => "native-ready",
        "binding" => holder.digest,
        "attempt" => ctx.identity.runtime_attempt_id,
        "sequence" => 0,
        "holder_pid" => 3,
        "guard_pid" => 2,
        "fixture_sha256" => fixture,
        "context_digest" => context["context_digest"]
      })
    )

    permission = [
      "C02_SYNTHETIC_SCHEMA2_V1",
      holder.digest,
      ctx.identity.runtime_attempt_id,
      pin.files[pin.holder],
      pin.files[Path.join(native, "build/guard")],
      "2",
      "1",
      to_string(deadline),
      effect_digest("manifest")
    ]

    write_effect_fixture(holder, "permission", Enum.join(permission, "\n") <> "\n")
    holder
  end

  defp write_effect_fixture(holder, name, bytes) do
    path = Path.join(holder.directory, name)
    File.write!(path, bytes)
    File.chmod!(path, 0o600)
  end

  defp effect_descriptor(overrides \\ %{}) do
    fields =
      Map.merge(
        %{
          "request_id" => nil,
          "method" => "POST",
          "url" => "https://api.openai.com/v1/responses",
          "model" => "synthetic-planner-v1",
          "body_sha256" => effect_digest("body"),
          "body_length" => 4,
          "content_type" => "application/json",
          "stream" => true,
          "store" => false,
          "parallel_tool_calls" => false,
          "tool_schema_sha256" => effect_digest("tools"),
          "prior_response_id" => nil,
          "tool_call_id" => nil,
          "tool_output_sha256" => nil,
          "tool_output_length" => nil
        },
        overrides
      )

    digest = fields |> Enum.sort() |> Jason.OrderedObject.new() |> Jason.encode!() |> effect_digest()
    Map.put(fields, "descriptor_sha256", digest)
  end

  defp second_descriptor_fields do
    %{"prior_response_id" => "response-1", "tool_call_id" => "call-1", "tool_output_sha256" => effect_digest("fixture read"), "tool_output_length" => 12}
  end

  defp second_descriptor, do: effect_descriptor(second_descriptor_fields())

  defp send_effect(boundary, ordinal, kind, attrs), do: HostBoundary.effect(boundary, effect_frame(boundary, ordinal, kind, attrs))

  defp effect_frame(boundary, ordinal, kind, attrs) do
    common = %{
      "schema" => "H100-EFFECT-PIPE-1",
      "kind" => kind,
      "context_digest" => boundary.context["context_digest"],
      "thread_id" => boundary.thread,
      "turn_id" => boundary.turn,
      "nonce" => boundary.nonce,
      "ordinal" => ordinal,
      "sequence" => boundary.sequence + 1,
      "deadline_ms" => boundary.native_deadline
    }

    Map.merge(common, attrs)
  end

  defp prepare_effect(boundary) do
    assert {:ok, %{"kind" => "PRE_SEND_INTENT"} = intent, next} =
             send_effect(boundary, 1, "VALIDATE_DESCRIPTOR", effect_descriptor())

    {intent, next}
  end

  defp ack_fields(intent), do: Map.take(intent, ~w(request_id revision descriptor_sha256))

  defp acknowledge_effect(boundary, intent, ordinal \\ 1), do: send_effect(boundary, ordinal, "POSSIBLE_SEND_ACK", ack_fields(intent))

  defp allow_effect(boundary, intent, ordinal \\ 1) do
    assert {:ok, permission, next} = acknowledge_effect(boundary, intent, ordinal)
    {permission, next}
  end

  defp response_fields(intent, ordinal), do: %{"request_id" => intent["request_id"], "response_id" => "response-#{ordinal}"}

  defp terminal_fields(intent, ordinal) do
    Map.merge(response_fields(intent, ordinal), %{"terminal_sha256" => effect_digest("terminal"), "terminal_length" => 8})
  end

  defp complete_effect(boundary, intent, ordinal) do
    assert {:ok, %{"kind" => "DURABLE_OBSERVATION", "stage" => "accepted"}, next} =
             send_effect(boundary, ordinal, "OBSERVED_ACCEPTANCE", response_fields(intent, ordinal))

    assert {:ok, %{"kind" => "DURABLE_OBSERVATION", "stage" => "terminal"}, next} =
             send_effect(next, ordinal, "TERMINAL_CONFIRMATION", terminal_fields(intent, ordinal))

    next
  end

  defp read_effects(holder), do: RequestLedger.open(holder.binding.attempt.runtime_attempt_id, path: Path.join(holder.directory, "provider-effects.journal"))

  defp record_native_effect(holder, intent, state, revision) do
    binary = Path.expand("../native/pilot_c02/build/request-effect")

    {_, status} =
      System.cmd(binary, [
        holder.directory,
        holder.digest,
        holder.binding.attempt.runtime_attempt_id,
        intent["request_id"],
        state,
        intent["descriptor_sha256"],
        to_string(revision),
        "1",
        intent["nonce"]
      ])

    status
  end

  defp native_effect_states(holder, intent) do
    holder.directory
    |> Path.join("request-effect-#{intent["request_id"]}.jsonl")
    |> File.stream!()
    |> Enum.map(&Jason.decode!(&1)["state"])
  end

  defp effect_digest(bytes), do: :crypto.hash(:sha256, bytes) |> Base.encode16(case: :lower)

  defp schema2_refusal_fixture(ctx) do
    opts = Keyword.put(ctx.opts, :model, ctx.route.profile.model)
    assert {:ok, %{binding: binding}} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
    assert_received {:holder_phase, :launch}
    root = Path.dirname(ctx.protocol_log)
    driver = Path.join(root, "schema2-refusal.py")
    catalog = Path.join(root, "schema2-catalog.json")
    holder = String.trim_trailing(binding.profile.command, " app-server")
    File.write!(driver, schema2_observation_fixture())
    File.write!(catalog, Jason.encode!(%{models: [%{slug: binding.profile.model}]}))

    pin = %{
      driver: driver,
      holder: holder,
      model_catalog: catalog,
      files: Map.new([driver, holder, catalog], &{&1, digest_file(&1)}),
      evidence_root: Path.join(root, "schema2-evidence"),
      schema2: :refusal,
      pinned_codex: true,
      fault: "unexpected_launch"
    }

    prior = Application.fetch_env(:symphony_elixir, :test_native_pilot)

    on_exit(fn ->
      case prior do
        {:ok, value} -> Application.put_env(:symphony_elixir, :test_native_pilot, value)
        :error -> Application.delete_env(:symphony_elixir, :test_native_pilot)
      end
    end)

    {binding, pin}
  end

  defp assert_prelaunch_refusal(binding, pin) do
    directory = exercise_schema2_refusal(binding, pin)
    refute File.exists?(Path.join(directory, "schema2-input.json"))
    refute File.exists?(Path.join(directory, "driver-entered"))
  end

  defp assert_observation_refusal(binding, pin) do
    directory = exercise_schema2_refusal(binding, pin)
    assert File.regular?(Path.join(directory, "driver-entered"))
    assert File.regular?(Path.join(directory, "correlation.json"))
    directory
  end

  defp exercise_schema2_refusal(binding, pin) do
    evidence_root = Path.join(pin.evidence_root, Integer.to_string(System.unique_integer([:positive])))
    pin = %{pin | evidence_root: evidence_root}
    Application.put_env(:symphony_elixir, :test_native_pilot, pin)
    assert {:error, :pilot_holder_native_refused} = NativePilot.exercise(binding, pin)
    directory = Path.join(evidence_root, binding.attempt.runtime_attempt_id)
    assert File.regular?(Path.join(directory, "binding.json"))
    directory
  end

  defp digest_file(path), do: :crypto.hash(:sha256, File.read!(path)) |> Base.encode16(case: :lower)

  # Only feeds rejected observations to the adapter. It never executes a holder.
  # The pinned-binary tests below provide the actual process and protocol evidence.
  defp schema2_observation_fixture do
    ~S"""
    import hashlib
    import json
    from pathlib import Path
    import sys

    args = dict(zip(sys.argv[1:-2:2], sys.argv[2:-2:2]))
    root = Path(args["--root"])
    fault = args["--fault"]
    (root / "driver-entered").touch()
    assert fault in ("missing_manifest", "wrong_manifest_context", "retryable_error",
                     "missing_disposal", "wrong_stop_pid", "wrong_stop_order")
    binding = args["--binding"]
    attempt = args["--attempt"]
    context = json.loads((root / "schema2-input.json").read_text())["context"]
    manifest = {"schema": 2, "profile": context["holder_profile"], "context": context,
                "binding": binding, "attempt": attempt, "holder_sha256": context["holder_sha256"]}
    if fault == "wrong_manifest_context":
        context["model_slug"] = "unapproved"
    manifest_bytes = json.dumps(manifest).encode()
    if fault != "missing_manifest":
        (root / "manifest.json").write_bytes(manifest_bytes)

    thread, turn = "fixture-thread", "fixture-turn"
    error = {"message": "SYMPHONY_PROVIDER_BOUNDARY_UNAVAILABLE", "codexErrorInfo": "other"}
    events = [
        {"id": 1},
        {"id": 2, "result": {"thread": {"id": thread}}},
        {"method": "thread/started", "params": {"thread": {"id": thread}}},
        {"id": 3, "result": {"turn": {"id": turn}}},
        {"method": "turn/started", "params": {"threadId": thread, "turn": {"id": turn}}},
        {"method": "error", "params": {"threadId": thread, "turnId": turn,
                                     "error": error, "willRetry": fault == "retryable_error"}},
        {"method": "turn/completed", "params": {"threadId": thread,
         "turn": {"id": turn, "status": "failed", "error": error}}},
    ]
    native = dict.fromkeys(("schema2", "native_exec", "protocol_verified", "consumed",
                            "replay_refused", "stop_verified", "native_disposal_verified"), True)
    native.update(binding=binding, attempt=attempt, inference_succeeded=False, qualified_host=False,
                  scope="SYNTHETIC_NATIVE_NOT_ROUTED_C01_QUALIFICATION", materialization_count=1,
                  guard_exit_code=0, host_exit_code=0, disposition="CONTROLLED_REFUSAL",
                  protocol_evidence=events, manifest_sha256=hashlib.sha256(manifest_bytes).hexdigest())
    if fault != "missing_disposal":
        for name in ("consumed", "channel-closed", "schema2-clean-exit", "guard-reaped", "disposed"):
            (root / name).write_text(binding)
        states = ["HOST_PERMISSION_VALIDATED", "BOOTSTRAP_CREATED", "MATERIALIZATION_INTENT",
                  "SYNTHETIC_MATERIALIZED", "CREDENTIAL_CHANNEL_CLOSED", "SCHEMA2_CHANNEL_CLOSED_BEFORE_RPC",
                  "TERMINATION_REQUESTED", "TERMINATION_VERIFIED", "SCHEMA2_CLEAN_EXIT", "GUARD_REAPED", "DISPOSAL_VERIFIED"]
        if fault == "wrong_stop_order":
            states[8], states[9] = states[9], states[8]
        journal = [dict(binding=binding, attempt=attempt, state=state, pid=22 if i == 0 else 33)
                   for i, state in enumerate(states)]
        if fault == "wrong_stop_pid":
            journal[-1]["pid"] = 44
        (root / "events.jsonl").write_text("".join(json.dumps(event) + "\n" for event in journal))
    retained = json.loads((root / "binding.json").read_text())
    (root / "correlation.json").write_text(json.dumps({"binding": retained, "native": native}))
    print(json.dumps(native))
    """
  end

  # The source-only CI checkout has no protected Codex executable. These cases
  # are selected with the retained, exact offline build via PINNED_CODEX_SCHEMA2_BINARY.
  if is_binary(System.get_env("PINNED_CODEX_SCHEMA2_BINARY")) do
    @tag native_boundary: true, full_runner: true, native_schema2: :refusal
    test "routed schema2 correlates actual failed terminal and synthetic stop", ctx do
      evidence = run_schema2(ctx, :pilot_holder_native_controlled_refusal)
      assert %{"disposition" => "CONTROLLED_REFUSAL", "protocol_verified" => true, "stop_verified" => true, "native_disposal_verified" => true, "materialization_count" => 1} = evidence["native"]
      assert [_, _, _, _, _, %{"method" => "error", "params" => error}, %{"method" => "turn/completed", "params" => terminal}] = evidence["native"]["protocol_evidence"]
      assert error["willRetry"] == false
      assert error["error"]["message"] == "SYMPHONY_PROVIDER_BOUNDARY_UNAVAILABLE"
      assert terminal["threadId"] == error["threadId"]
      assert terminal["turn"]["id"] == error["turnId"]
      assert terminal["turn"]["status"] == "failed"
      assert terminal["turn"]["error"] == error["error"]
    end

    @tag native_boundary: true, full_runner: true, native_schema2: :interrupt
    test "routed schema2 interrupts the real turn and verifies synthetic stop", ctx do
      evidence = run_schema2(ctx, :pilot_holder_native_interrupted)
      assert %{"disposition" => "INTERRUPTED", "protocol_verified" => true, "stop_verified" => true, "native_disposal_verified" => true} = evidence["native"]
      assert [_, _, _, _, %{"method" => "turn/started", "params" => started}, %{"id" => 4}, %{"method" => "turn/completed", "params" => terminal}] = evidence["native"]["protocol_evidence"]
      assert terminal["threadId"] == started["threadId"]
      assert terminal["turn"]["id"] == started["turn"]["id"]
      assert terminal["turn"]["status"] == "interrupted"
    end

    @tag native_boundary: true, full_runner: true, native_schema2: :refusal, native_stop_fault: "observe_failure"
    test "routed schema2 quarantines missing stop observation despite a real failed terminal", ctx do
      evidence = run_schema2(ctx, :pilot_holder_native_refused)
      assert %{"disposition" => "QUARANTINED", "protocol_verified" => true, "stop_verified" => false, "native_disposal_verified" => false} = evidence["native"]
      assert List.last(evidence["native"]["protocol_evidence"])["params"]["turn"]["status"] == "failed"
    end

    @tag native_boundary: true, full_runner: true, native_schema2: :refusal
    test "routed schema2 refuses both ledger replay and a second launch", ctx do
      first = run_schema2(ctx, :pilot_holder_native_controlled_refusal)
      path = schema2_evidence_path(ctx, "correlation.json")

      assert_raise RuntimeError, ~r/Pilot launch refused/, fn ->
        AgentRunner.run(ctx.issue, self(), Keyword.put(ctx.opts, :runtime, SymphonyElixir.AgentRuntime.Codex))
      end

      assert File.read!(path) |> Jason.decode!() == first
      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
    end

    defp run_schema2(ctx, reason) do
      opts = Keyword.put(ctx.opts, :runtime, SymphonyElixir.AgentRuntime.Codex)
      assert_raise RuntimeError, "Pilot execution failed", fn -> AgentRunner.run(ctx.issue, self(), opts) end
      assert {:ok, %{state: :quarantined, result: result}} = AttemptLedger.pilot_status(ctx.ledger)
      refute result.model_state == :completed
      assert result.stop_disposition == :quarantined
      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
      refute_received {:holder_phase, _}

      evidence = schema2_evidence_path(ctx, "correlation.json") |> File.read!() |> Jason.decode!()
      manifest = schema2_evidence_path(ctx, "manifest.json") |> File.read!() |> Jason.decode!()
      assert evidence["binding"]["grant"] == Jason.decode!(Jason.encode!(ctx.grant))
      assert evidence["binding"]["attempt"]["runtime_attempt_id"] == ctx.identity.runtime_attempt_id
      assert evidence["native"]["attempt"] == ctx.identity.runtime_attempt_id
      observation = schema2_evidence_path(ctx, "adapter-observation.json") |> File.read!() |> Jason.decode!()
      assert observation["outcome"] == Atom.to_string(reason)
      assert observation["attempt"] == ctx.identity.runtime_attempt_id
      assert observation["binding"] == evidence["native"]["binding"]
      assert observation["operational_namespace_qualified"] == false
      assert observation["synthetic_stop_verified"] == (reason != :pilot_holder_native_refused)

      assert evidence["native"]["qualified_host"] == false
      assert evidence["native"]["consumed"]
      assert evidence["native"]["replay_refused"]
      refute evidence["native"]["inference_succeeded"]
      assert manifest["context"]["source_commit"] == ctx.grant.source_commit
      assert manifest["context"]["source_tree"] == ctx.grant.source_tree
      assert manifest["context"]["configuration_digest"] == ctx.grant.config_identity
      assert manifest["holder_sha256"] == ctx.selector["holder_artifact_identity"]
      assert manifest["binding"] == evidence["native"]["binding"]

      File.write!(
        schema2_evidence_path(ctx, "c04-observation.json"),
        Jason.encode!(%{
          attempt: ctx.identity.runtime_attempt_id,
          model_state: result.model_state,
          stop_disposition: result.stop_disposition
        }),
        [:exclusive]
      )

      evidence
    end

    defp schema2_evidence_path(ctx, name) do
      Path.join([ctx.opts[:test_native_pilot].evidence_root, ctx.identity.runtime_attempt_id, name])
    end
  end

  @tag native_boundary: true
  test "native options cannot replace the trusted fixture selection", ctx do
    pin = %{ctx.opts[:test_native_pilot] | fault: "ambiguous_provider"}

    assert {:error, :pilot_holder_native_refused} =
             AppServer.start_session(ctx.workspace, Keyword.put(ctx.opts, :test_native_pilot, pin))

    refute File.exists?(pin.evidence_root)
    refute_received {:holder_phase, _}
  end

  @tag review_regression: true
  test "a forged profile cannot reuse a configured Planner identity", ctx do
    profile = %{ctx.route.profile | max_turns: ctx.route.profile.max_turns + 1}
    opts = Keyword.put(ctx.opts, :profile, profile)
    assert {:error, :pilot_holder_binding_invalid} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
    refute_received {:holder_phase, _}
  end

  @tag review_regression: true
  test "effective command and model cannot override the bound profile", ctx do
    for {key, value} <- [command: "/unexpected/codex app-server", model: "unapproved-model"] do
      opts = Keyword.put(ctx.opts, key, value)
      assert {:error, :pilot_holder_binding_invalid} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
    end

    refute_received {:holder_phase, _}
  end

  @tag review_regression: true
  test "a caller-selected signing peer cannot replace the harness trust pin", ctx do
    {:ok, other} = C02SyntheticHost.start_link(Path.join(Path.dirname(ctx.protocol_log), "other.journal"), self())
    key = GenServer.call(other, :public_key)
    opts = Keyword.put(ctx.opts, :test_pilot_holder_peer, {other, key})
    assert {:error, :pilot_holder_boundary_unavailable} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
    refute_received {:holder_phase, _}
  end

  test "missing synthetic trust pin cannot be replaced by receipt flags", ctx do
    Application.delete_env(:symphony_elixir, :test_pilot_holder_peer)
    assert {:error, :pilot_holder_boundary_unavailable} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    refute_received {:holder_phase, _}
  end

  test "a failed synthetic journal synchronization never issues a readiness receipt", ctx do
    GenServer.call(ctx.peer, {:mutate, :launch, :sync_failure})
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    assert {:error, :enoent} = GenServer.call(ctx.peer, :journal)
    assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
  end

  test "a completed first turn never permits a second turn", ctx do
    {:ok, holder} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    assert :ok = RuntimeIsolation.check_pilot_holder(holder, :thread)
    assert :ok = RuntimeIsolation.check_pilot_holder(holder, :turn)
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.check_pilot_holder(holder, :turn)
    assert :ok = RuntimeIsolation.check_pilot_holder(holder, :cleanup)
  end

  test "cleanup cannot extend the accepted absolute attempt deadline", ctx do
    {:ok, holder} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    expired = put_in(holder.binding.absolute_deadline_ms, System.monotonic_time(:millisecond) - 1)
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.check_pilot_holder(expired, :cleanup)
    refute_received {:holder_phase, :cleanup}
    assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
  end

  test "per-turn model options cannot replace the bound model", ctx do
    {:ok, session} = AppServer.start_session(ctx.workspace, protocol_opts(ctx))

    assert {:error, :pilot_holder_binding_invalid} =
             AppServer.run_turn(session, "synthetic", ctx.issue, model: "other-model")

    refute Enum.any?(protocol_messages(ctx), &(&1["method"] == "turn/start"))
    refute_received {:holder_phase, :turn}
  end

  @tag policy_order_regression: true
  test "policy rejection never stages a holder readiness permission", ctx do
    opts = Keyword.put(ctx.opts, :sandbox, "workspace-write")
    assert {:error, :routed_sandbox_mismatch} = AppServer.start_session(ctx.workspace, opts)
    refute_received {:holder_phase, :launch}
    assert {:error, :enoent} = GenServer.call(ctx.peer, :journal)
    assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
  end

  test "explicit selector is retained and covered by the existing configuration identity", ctx do
    assert Config.settings!().agent.pilot_holder == ctx.selector
    settings = Config.settings!()
    changed = put_in(settings.agent.pilot_holder["host_permission_ref"], "different-permission")
    refute Config.pilot_configuration_identity(changed, @prompt) == ctx.grant.config_identity
  end

  test "native dependencies cannot be promoted by a caller's receipt map", ctx do
    opts = ctx.opts |> Keyword.delete(:test_pilot_holder_peer) |> Keyword.put(:pilot_holder_receipt, %{authenticated: true, durable: true})
    assert {:error, :pilot_holder_boundary_unavailable} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
    assert Map.keys(RuntimeIsolation.pilot_holder_dependencies()) |> Enum.sort() == ~w(P01 P02 P03 P04 P05 P08)
  end

  test "signed durable synthetic launch, thread, turn and disposal bind one exact attempt", ctx do
    assert {:ok, holder} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    assert holder.assurance == :synthetic_test_only
    assert holder.binding.grant == ctx.grant
    assert holder.binding.attempt == Map.from_struct(ctx.identity)
    assert holder.binding.selection == ctx.selector
    assert :ok = RuntimeIsolation.check_pilot_holder(holder, :thread)
    assert :ok = RuntimeIsolation.check_pilot_holder(holder, :turn)
    assert :ok = RuntimeIsolation.check_pilot_holder(holder, :cleanup)
    assert {:ok, bytes} = GenServer.call(ctx.peer, :journal)
    assert byte_size(bytes) > 0
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.check_pilot_holder(holder, :turn)
    assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
  end

  for phase <- [:launch, :thread, :turn, :cleanup] do
    @tag phase: phase
    test "missing receipt refuses at #{phase}", ctx do
      holder = if ctx.phase != :launch, do: elem(RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts), 1)
      assert :ok = GenServer.call(ctx.peer, {:mutate, ctx.phase, :unavailable})
      result = if ctx.phase == :launch, do: RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts), else: RuntimeIsolation.check_pilot_holder(holder, ctx.phase)
      assert {:error, :pilot_holder_receipt_refused} = result
    end
  end

  for name <- [
        "binding",
        "deadline",
        "role",
        "permission",
        "holder profile",
        "credential generation",
        "expired access",
        "expired lease",
        "sensitive extra field",
        "project",
        "work item",
        "commit",
        "configuration",
        "host",
        "host boot"
      ] do
    @tag mutation: name
    test "signed synthetic receipt refuses mismatched #{name}", ctx do
      mutation = fn payload -> corrupt_receipt(payload, ctx.mutation) end
      GenServer.call(ctx.peer, {:mutate, :launch, mutation})
      assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    end
  end

  test "invalid signature refuses despite matching receipt fields", ctx do
    GenServer.call(ctx.peer, {:mutate, :launch, :bad_signature})
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
  end

  test "a prior signed receipt cannot answer a fresh phase challenge", ctx do
    {:ok, holder} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    GenServer.call(ctx.peer, {:mutate, :thread, :replay})
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.check_pilot_holder(holder, :thread)
  end

  test "changed validated policy cannot reuse the holder authority", ctx do
    {:ok, holder} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    File.write!(ctx.policy_path, "different policy")
    assert {:error, :pilot_holder_binding_invalid} = RuntimeIsolation.check_pilot_holder(holder, :thread)
  end

  test "forged metadata cannot replace the consumed ledger authority", ctx do
    opts = Keyword.delete(ctx.opts, :attempt_ledger)
    assert {:error, :pilot_holder_binding_invalid} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
    opts = Keyword.put(ctx.opts, :runtime_attempt_identity, %{ctx.identity | runtime_attempt_id: "different"})
    assert {:error, :pilot_holder_binding_invalid} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
  end

  test "deadline must remain finite and within the grant", ctx do
    for deadline <- [nil, System.monotonic_time(:millisecond) - 1, System.monotonic_time(:millisecond) + ctx.grant.deadline_ms * 2] do
      assert {:error, :pilot_holder_binding_invalid} =
               RuntimeIsolation.prepare_pilot_holder(ctx.workspace, Keyword.put(ctx.opts, :absolute_deadline_ms, deadline))
    end
  end

  test "receipt timeout is finite and does not restore the C01 grant", ctx do
    GenServer.call(ctx.peer, {:mutate, :launch, :timeout})
    opts = Keyword.put(ctx.opts, :absolute_deadline_ms, System.monotonic_time(:millisecond) + 500)
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, opts)
    assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
  end

  test "AppServer refuses unavailable holder before runtime probing or process creation", ctx do
    opts = ctx.opts |> Keyword.delete(:test_pilot_holder_peer) |> Keyword.put(:test_runtime_isolation_admit, fn _, _, _ -> flunk("Must refuse before runtime probing") end)
    assert {:error, :pilot_holder_boundary_unavailable} = AppServer.start_session(ctx.workspace, opts)
    refute_received {:holder_phase, _}
  end

  test "selector rejects unknown, credential-bearing and incomplete configuration", ctx do
    for selector <- [
          Map.put(ctx.selector, "access_token", "synthetic-forbidden"),
          Map.delete(ctx.selector, "host_permission_ref"),
          put_in(ctx.selector, ["lifetime_budget", "clock_skew_bound_ms"], -1)
        ] do
      assert {:error, _} = Schema.parse(put_in(ctx.raw, ["agent", "pilot_holder"], selector))
    end
  end

  test "production environment rejects even a valid synthetic peer", ctx do
    previous = Mix.env()

    try do
      Mix.env(:prod)
      assert {:error, :pilot_holder_boundary_unavailable} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    after
      Mix.env(previous)
    end
  end

  test "real synthetic protocol passes all gates and preserves fresh cleared homes", ctx do
    opts = protocol_opts(ctx)
    System.put_env("ACCESS_TOKEN", "synthetic-parent-access-never-inherit")

    try do
      assert {:ok, session} = AppServer.start_session(ctx.workspace, opts)
      home = session.ephemeral_home.root
      assert File.dir?(home)
      assert {:ok, _} = AppServer.run_turn(session, "Synthetic read-only planning", ctx.issue)
      assert :ok = AppServer.stop_session(session)
      refute File.exists?(home)
      messages = protocol_messages(ctx)
      assert Enum.map(messages, & &1["method"]) == ["initialize", "initialized", "thread/start", "turn/start"]
      assert Enum.all?(messages, &(not &1["access_present"] and not &1["refresh_present"]))
      assert Enum.all?(messages, &String.starts_with?(&1["home"], home <> "/"))
      assert_receive {:holder_phase, :launch}
      assert_receive {:holder_phase, :thread}
      assert_receive {:holder_phase, :turn}
      assert_receive {:holder_phase, :cleanup}
      assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
    after
      System.delete_env("ACCESS_TOKEN")
    end
  end

  for phase <- [:thread, :turn] do
    @tag refused_phase: phase
    test "AppServer never sends #{phase}/start after its receipt is refused", ctx do
      GenServer.call(ctx.peer, {:mutate, ctx.refused_phase, :unavailable})

      if ctx.refused_phase == :thread do
        assert {:error, :pilot_holder_receipt_refused} = AppServer.start_session(ctx.workspace, protocol_opts(ctx))
      else
        {:ok, session} = AppServer.start_session(ctx.workspace, protocol_opts(ctx))
        assert {:error, :pilot_holder_receipt_refused} = AppServer.run_turn(session, "synthetic", ctx.issue)
      end

      refute Enum.any?(protocol_messages(ctx), &(&1["method"] == "#{ctx.refused_phase}/start"))
      assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
    end
  end

  test "uncertain disposal keeps session home and never claims successful stop", ctx do
    {:ok, session} = AppServer.start_session(ctx.workspace, protocol_opts(ctx))
    GenServer.call(ctx.peer, {:mutate, :cleanup, :unavailable})
    assert {:error, :pilot_holder_receipt_refused} = AppServer.stop_session(session)
    assert File.dir?(session.ephemeral_home.root)
    assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
    # Fixture ownership only: remove retained synthetic home after checking evidence.
    IsolationProfile.cleanup_session_home(session.ephemeral_home)
  end

  test "wrong artifact refuses before launch and disposes pending host permission", ctx do
    File.write!(ctx.route.profile.command |> String.split() |> hd(), "#!/bin/sh\nexit 88\n")
    assert {:error, :pilot_holder_artifact_mismatch} = AppServer.start_session(ctx.workspace, protocol_opts(ctx))
    refute File.exists?(ctx.protocol_log)
    assert_receive {:holder_phase, :cleanup}
  end

  test "expired context cannot issue a turn even if peer remains alive", ctx do
    {:ok, session} = AppServer.start_session(ctx.workspace, protocol_opts(ctx))
    holder = put_in(session.pilot_holder_context.binding.absolute_deadline_ms, System.monotonic_time(:millisecond) - 1)
    assert {:error, :pilot_holder_binding_invalid} = AppServer.run_turn(holder, "synthetic", ctx.issue, defer_runtime_stop: true)
    refute Enum.any?(protocol_messages(ctx), &(&1["method"] == "turn/start"))
    # The tampered context is not authority for cleanup; use the original binding.
    assert :ok = AppServer.stop_session(session)
  end

  @tag full_runner: true
  test "full runner persists the Planner answer only after synthetic disposal", ctx do
    opts = protocol_opts(ctx) |> Keyword.put(:runtime, SymphonyElixir.AgentRuntime.Codex)
    assert :ok = AgentRunner.run(ctx.issue, self(), opts)
    assert {:ok, %{state: :stopverified, result: result}} = AttemptLedger.pilot_status(ctx.ledger)
    assert result.final_answer == "Plan: inspect the single tracked source file."
    assert result.stop_disposition == :verified
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
  end

  @tag full_runner: true
  test "full runner quarantines uncertain disposal and retains its consumed entitlement", ctx do
    GenServer.call(ctx.peer, {:mutate, :cleanup, :unavailable})
    opts = protocol_opts(ctx) |> Keyword.put(:runtime, SymphonyElixir.AgentRuntime.Codex)
    assert_raise RuntimeError, fn -> AgentRunner.run(ctx.issue, self(), opts) end
    assert {:ok, %{state: :quarantined, result: result}} = AttemptLedger.pilot_status(ctx.ledger)
    assert result.stop_disposition == :quarantined
    assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, ctx.issue.id, pilot_binding: ctx.grant)
  end

  test "missing selected context refuses thread, turn and disposal claims" do
    for phase <- [:thread, :turn, :cleanup] do
      assert {:error, :pilot_holder_binding_invalid} = RuntimeIsolation.check_pilot_holder(nil, phase)
    end
  end

  test "peer death cannot be repaired by replaying its cached signed receipt", ctx do
    {:ok, holder} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    GenServer.stop(ctx.peer)
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.check_pilot_holder(holder, :thread)
    assert {:ok, %{state: :running}} = AttemptLedger.pilot_status(ctx.ledger)
  end

  for offset <- [0, -1] do
    @tag lifetime_offset: offset
    test "access lifetime threshold #{offset} is enforced against the immutable deadline", ctx do
      mutate = fn payload ->
        budget = ctx.selector["lifetime_budget"] |> Map.values() |> Enum.sum()
        expiry = payload["binding"].absolute_deadline_ms + budget - ctx.grant.deadline_ms + ctx.lifetime_offset
        Map.put(payload, "access_expires_ms", expiry)
      end

      GenServer.call(ctx.peer, {:mutate, :launch, mutate})

      if ctx.lifetime_offset == 0 do
        assert {:ok, _} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
      else
        assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
      end
    end
  end

  test "generation or holder rollover is refused within a running attempt", ctx do
    {:ok, holder} = RuntimeIsolation.prepare_pilot_holder(ctx.workspace, ctx.opts)
    GenServer.call(ctx.peer, {:mutate, :thread, fn p -> Map.put(p, "holder_ref", "replacement-holder") end})
    assert {:error, :pilot_holder_receipt_refused} = RuntimeIsolation.check_pilot_holder(holder, :thread)
  end

  defp protocol_opts(ctx) do
    Keyword.put(ctx.opts, :test_runtime_isolation_admit, fn _, _, _ -> {:ok, :synthetic_admitted} end)
  end

  defp protocol_messages(ctx) do
    case File.read(ctx.protocol_log) do
      {:ok, bytes} -> bytes |> String.split("\n", trim: true) |> Enum.map(&Jason.decode!/1)
      {:error, :enoent} -> []
    end
  end

  defp synthetic_codex(log) do
    """
    #!/usr/bin/python3
    import json, os, sys
    log = #{Jason.encode!(log)}
    for line in sys.stdin:
        request = json.loads(line)
        method = request.get("method")
        with open(log, "a") as stream:
            stream.write(json.dumps({"method": method, "home": os.environ.get("HOME"), "codex_home": os.environ.get("CODEX_HOME"), "access_present": "ACCESS_TOKEN" in os.environ, "refresh_present": "REFRESH_TOKEN" in os.environ}) + "\\n")
        if method == "initialize":
            result = {}
        elif method == "thread/start":
            params = request["params"]
            result = {"thread": {"id": "synthetic-thread"}, "activePermissionProfile": {"id": params["permissions"]}, "runtimeWorkspaceRoots": params["runtimeWorkspaceRoots"], "cwd": params["cwd"]}
        elif method == "turn/start":
            params = request["params"]
            result = {"turn": {"id": "synthetic-turn"}, "activePermissionProfile": {"id": params["permissions"]}, "runtimeWorkspaceRoots": params["runtimeWorkspaceRoots"], "cwd": params["cwd"]}
        else:
            continue
        print(json.dumps({"id": request["id"], "result": result}), flush=True)
        if method == "turn/start":
            print(json.dumps({"method": "item/completed", "params": {"item": {"type": "agentMessage", "phase": "final_answer", "id": "synthetic-final", "text": "Plan: inspect the single tracked source file."}}}), flush=True)
            print(json.dumps({"method": "turn/completed", "params": {"turn": {"id": "synthetic-turn", "status": "completed"}}}), flush=True)
    """
  end

  defp corrupt_receipt(p, "project"), do: put_in(p["binding"].grant.plane_project_id, "wrong-project")
  defp corrupt_receipt(p, "work item"), do: put_in(p["binding"].grant.work_item_id, "wrong-item")
  defp corrupt_receipt(p, "commit"), do: put_in(p["binding"].grant.source_commit, String.duplicate("e", 40))
  defp corrupt_receipt(p, "configuration"), do: put_in(p["binding"].grant.config_identity, String.duplicate("f", 64))
  defp corrupt_receipt(p, "host"), do: put_in(p["binding"].selection["host_id"], "other-host")
  defp corrupt_receipt(p, "host boot"), do: put_in(p["binding"].selection["host_boot_id"], "other-boot")
  defp corrupt_receipt(p, "binding"), do: put_in(p["binding"].grant.source_tree, String.duplicate("c", 40))
  defp corrupt_receipt(p, "deadline"), do: update_in(p["binding"].absolute_deadline_ms, &(&1 + 1))
  defp corrupt_receipt(p, "role"), do: put_in(p["binding"].attempt.responsibility, "implementation")
  defp corrupt_receipt(p, "permission"), do: put_in(p["binding"].selection["host_permission_ref"], "wrong")
  defp corrupt_receipt(p, "holder profile"), do: put_in(p["binding"].selection["holder_profile_identity"], String.duplicate("d", 64))
  defp corrupt_receipt(p, "credential generation"), do: put_in(p["binding"].selection["credential_generation"], 2)
  defp corrupt_receipt(p, "expired access"), do: Map.put(p, "access_expires_ms", System.monotonic_time(:millisecond) - 1)
  defp corrupt_receipt(p, "expired lease"), do: Map.put(p, "lease_expires_ms", System.monotonic_time(:millisecond) - 1)
  defp corrupt_receipt(p, "sensitive extra field"), do: Map.put(p, "access_token", "synthetic-forbidden-bearer")

  defp git!(workspace, args) do
    {output, 0} = System.cmd("/usr/bin/git", ["-c", "core.hooksPath=/dev/null", "-C", workspace | args], stderr_to_stdout: true)
    output
  end
end
