defmodule SymphonyElixir.PilotRehearsal do
  @moduledoc false

  import ExUnit.Assertions
  import ExUnit.Callbacks, only: [on_exit: 1]

  alias SymphonyElixir.AgentRuntime.{AttemptLedger, Codex, Router}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.Config
  alias SymphonyElixir.Config.Schema
  alias SymphonyElixir.HostEvidence.C01EvidenceReview
  alias SymphonyElixir.PathSafety
  alias SymphonyElixir.ProviderEffect.RequestLedger
  alias SymphonyElixir.TestSupport
  alias SymphonyElixir.Tracker
  alias SymphonyElixir.Tracker.Issue
  alias SymphonyElixir.WorkControl.{WorkflowLifecycle, WorkItem}
  alias SymphonyElixir.Workflow
  alias SymphonyElixir.WorkflowStore

  @project "11111111-1111-4111-8111-111111111111"
  @item "22222222-2222-4222-8222-222222222222"
  @workspace "33333333-3333-4333-8333-333333333333"
  @prompt "Read the tracked planner_input.txt and return a short plan."
  @input "SLICE_C_TRACKED_FILE_PROOF\n"

  @behaviour SymphonyElixir.AgentRuntime
  @impl true
  defdelegate capabilities(), to: Codex
  @impl true
  defdelegate runtime_metadata(), to: Codex
  @impl true
  defdelegate run_turn(session, prompt, issue, opts), to: Codex
  @impl true
  defdelegate stop_session(session), to: Codex

  @impl true
  def start_session(workspace, opts) do
    observe_session(Codex.start_session(workspace, opts), opts)
  end

  def observe_session(result, opts) do
    capture_result(result, fn
      {_ref, %{pilot_holder_context: %{digest: digest, binding: %{workspace: path}}}} ->
        send(Keyword.fetch!(opts, :rehearsal_observer), {:rehearsal_binding, digest, path})
    end)
  end

  # Observation must never replace the return that lets AgentRunner own stop.
  def capture_result({:ok, session} = result, capture) do
    try do
      capture.(session)
    catch
      _, _ -> :ok
    end

    result
  end

  def capture_result(result, _capture), do: result

  def digest(bytes), do: :crypto.hash(:sha256, bytes) |> Base.encode16(case: :lower)

  def freeze(root, inputs), do: record(root, "prepared.json", inputs)

  def inspect_prepared(root) do
    with {:ok, bytes} <- read_regular(Path.join(root, "prepared.json")) do
      Jason.decode(bytes)
    end
  end

  @qualification_checks ~w(source_build_match trusted_executables network_isolation resource_controls descendant_termination hypervisor_fallback evidence_export encrypted_backup)

  def execute_once(root, measured, qualification_sha, host, execute) do
    with {:ok, prepared_bytes} <- read_regular(Path.join(root, "prepared.json")),
         {:ok, ^measured} <- Jason.decode(prepared_bytes),
         {:ok, qualification_bytes} <- read_regular(Path.join(root, "qualification.json")),
         true <- digest(qualification_bytes) == qualification_sha,
         {:ok, decoded} <- Jason.decode(qualification_bytes, objects: :ordered_objects),
         {:ok, qualification} <- unique_approval_fields(decoded),
         prepared_sha = digest(prepared_bytes),
         true <- approved?(qualification, root, prepared_sha, host, Map.take(measured, ~w(hostname boot_id))) do
      case record(root, "execution.started", %{"prepared_sha256" => prepared_sha, "qualification_sha256" => qualification_sha}) do
        :ok -> {:ok, execute.()}
        {:error, :eexist} -> {:error, :execution_already_started}
        {:error, _reason} -> {:error, :preflight_refused}
      end
    else
      _ -> {:error, :preflight_refused}
    end
  end

  # Decode the closed approval without quietly accepting repeated JSON fields.
  defp unique_approval_fields(%Jason.OrderedObject{values: pairs}) do
    Enum.reduce_while(pairs, {:ok, %{}}, fn {key, value}, {:ok, fields} ->
      with false <- Map.has_key?(fields, key),
           {:ok, value} <- unique_approval_fields(value) do
        {:cont, {:ok, Map.put(fields, key, value)}}
      else
        _ -> {:halt, :error}
      end
    end)
  end

  defp unique_approval_fields(value) when is_binary(value) or is_boolean(value), do: {:ok, value}
  defp unique_approval_fields(_value), do: :error

  defp approved?(
         %{
           "schema" => "h100-rehearsal-approval-v1",
           "scope" => "one-evidence-only-execution",
           "root" => root,
           "prepared_sha256" => prepared_sha,
           "host" => host,
           "guest" => guest,
           "prerequisites" => checks
         } = approval,
         root,
         prepared_sha,
         host,
         guest
       )
       when map_size(approval) == 7 do
    identity?(host) and identity?(guest) and checks == Map.new(@qualification_checks, &{&1, true})
  end

  defp approved?(_approval, _root, _prepared_sha, _host, _guest), do: false

  defp identity?(%{"hostname" => name, "boot_id" => boot} = identity) when map_size(identity) == 2 do
    is_binary(name) and byte_size(name) in 1..253 and match?({:ok, ^boot}, Ecto.UUID.cast(boot))
  end

  defp identity?(_identity), do: false

  def read_regular(path, max_bytes \\ 1_048_576) do
    with {:ok, ^path} <- PathSafety.canonicalize(path),
         {:ok, %File.Stat{type: :regular, size: size}} when size <= max_bytes <- File.lstat(path),
         {:ok, bytes} when byte_size(bytes) == size <- File.read(path) do
      {:ok, bytes}
    else
      {:error, _reason} = error -> error
      _ -> {:error, :unexpected_file}
    end
  end

  def record(root, name, value), do: write_exclusive(Path.join(root, name), Jason.encode!(value) <> "\n")

  def write_exclusive(path, bytes) do
    case File.open(path, [:write, :binary, :exclusive], &write_and_sync(&1, bytes)) do
      {:ok, :ok} -> sync_directory(Path.dirname(path))
      {:ok, {:error, _reason} = error} -> error
      {:error, _reason} = error -> error
    end
  end

  defp write_and_sync(file, bytes) do
    with :ok <- IO.binwrite(file, bytes), do: :file.sync(file)
  end

  defp sync_directory(path) do
    with {:ok, file} <- :file.open(String.to_charlist(path), [:read, :raw, :directory]) do
      try do
        :file.sync(file)
      after
        :file.close(file)
      end
    end
  end

  def sealed_copies(root, files, true) do
    originals = Path.join(root, "originals")
    readback = Path.join(root, "readback")

    with :ok <- File.mkdir(originals), :ok <- File.mkdir(readback) do
      Enum.reduce_while(files, {:ok, %{}}, &seal_file(&1, &2, originals, readback))
    end
  end

  def sealed_copies(_root, _files, false), do: {:error, :unverified_retained}

  defp seal_file({name, path}, {:ok, hashes}, originals, readback) do
    with {:ok, bytes} <- read_regular(path, 16_777_216),
         :ok <- write_exclusive(Path.join(originals, name), bytes),
         :ok <- write_exclusive(Path.join(readback, name), bytes) do
      {:cont, {:ok, Map.put(hashes, name, digest(bytes))}}
    else
      error -> {:halt, error}
    end
  end

  def verify_copies(root, files, hashes) do
    unchanged? =
      Enum.all?(files, fn {name, path} ->
        expected = Map.fetch!(hashes, name)
        paths = [path, Path.join([root, "originals", name]), Path.join([root, "readback", name])]
        Enum.all?(paths, &same_bytes?(&1, expected))
      end)

    if unchanged?, do: :ok, else: {:error, :unverified_retained}
  end

  defp same_bytes?(path, expected) do
    case read_regular(path, 16_777_216) do
      {:ok, bytes} -> digest(bytes) == expected
      _ -> false
    end
  end

  def snapshot(ledger, work_item, attempt, journal_path) do
    {:ok, pilot} = AttemptLedger.pilot_status(ledger)
    {:ok, current} = AttemptLedger.current(ledger, work_item)
    {:ok, effects} = RequestLedger.open(attempt, path: journal_path)
    %{pilot: pilot, current: current, events: effects.events, records: RequestLedger.records(effects), closed?: effects.closed?}
  end

  def replay_refusal(ledger, grant, snapshot) do
    work_item = grant.work_item_id

    with %{pilot: %{state: state, grant: ^grant}, current: %{issue_id: ^work_item}} = before
         when state in [:consumed, :running, :stopverified, :quarantined] <- snapshot.(),
         {:error, :pilot_allowance_consumed} <- AttemptLedger.begin_attempt(ledger, work_item, pilot_binding: grant),
         ^before <- snapshot.() do
      {:ok, before}
    else
      _ -> {:error, :replay_refusal_unverified}
    end
  end

  def canonical_grant(grant) do
    fields =
      Enum.map(~w(project_id plane_project_id work_item_id responsibility source_commit source_tree config_identity runtime_lineage)a, fn key ->
        value = Map.fetch!(grant, key)
        [<<byte_size(value)::32>>, value]
      end)

    digest(["H100-C01-FIXTURE-GRANT-V1", <<0>>, fields, <<grant.deadline_ms::64>>])
  end

  def artifact(path, hashes, receipt_fields \\ %{}) do
    case read_regular(path, 16_777_216) do
      {:ok, bytes} ->
        hash = digest(bytes)

        default_hash = if receipt_fields == %{}, do: hash
        sealed_hash = Map.get(hashes, Path.basename(path), default_hash)

        if sealed_hash == hash and receipt_matches?(bytes, receipt_fields) do
          {:observed, hash}
        else
          {:ambiguous, :unconfirmed, hash}
        end

      {:error, :enoent} ->
        :missing

      {:error, _} ->
        {:ambiguous, :unreadable, nil}
    end
  end

  defp receipt_matches?(_bytes, fields) when map_size(fields) == 0, do: true

  # The producer owns stop semantics. Correlate these exact retained bytes with
  # the independent session binding and attempt before projecting an observation.
  defp receipt_matches?(bytes, fields) do
    case Jason.decode(bytes, objects: :ordered_objects) do
      {:ok, %Jason.OrderedObject{values: pairs}} ->
        receipt = Map.new(pairs)
        map_size(receipt) == length(pairs) and Map.take(receipt, Map.keys(fields)) === fields

      _ ->
        false
    end
  end

  def resource(path, root) do
    parent = Path.dirname(path)

    with true <- String.starts_with?(path, root <> "/"),
         {:ok, ^parent} <- PathSafety.canonicalize(parent),
         {:ok, %File.Stat{type: :directory}} <- File.lstat(parent) do
      observe_path(path)
    else
      _ -> {{:ambiguous, :partial_coverage, nil}, nil}
    end
  end

  defp observe_path(path) do
    case File.lstat(path) do
      {:ok, %File.Stat{type: :symlink}} ->
        {{:ambiguous, :unconfirmed, nil}, %{path: path, type: :symlink}}

      {:ok, stat} ->
        metadata = Map.take(stat, [:type, :mode, :uid, :gid, :major_device, :minor_device, :inode])
        resource_observed(Map.merge(metadata, %{path: path, present: true}))

      {:error, :enoent} ->
        resource_observed(%{path: path, present: false})

      {:error, _} ->
        {{:ambiguous, :unreadable, nil}, nil}
    end
  end

  defp resource_observed(metadata), do: {{:observed, digest(Jason.encode!(metadata))}, metadata}

  def stage_fixture(root, binary) do
    source = Path.join(root, "source")
    File.mkdir!(source)
    git!(source, ["init", "-q"])
    File.write!(Path.join(source, "planner_input.txt"), @input)
    git!(source, ["add", "planner_input.txt"])
    git!(source, ["-c", "user.name=Offline", "-c", "user.email=offline@example.invalid", "-c", "commit.gpgSign=false", "commit", "-qm", "Planner fixture"])
    codex = Path.join(root, "codex")
    File.cp!(binary, codex)
    File.chmod!(codex, 0o700)
    policy = Path.join(root, "policy")
    File.mkdir!(policy)
    File.write!(Path.join(policy, "planner.md"), "Inspect the tracked fixture file only.\n")
  end

  def fixture_inputs(root) do
    source = Path.join(root, "source")
    [commit, tree] = git!(source, ["rev-parse", "HEAD", "HEAD^{tree}"]) |> String.split()
    codex = Path.join(root, "codex")
    policy = Path.join(root, "policy")
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

    %{root: root, source: source, settings: settings, parsed: parsed, grant: grant, issue: issue}
  end

  def fixture_route(issue, settings) do
    {:ok, work_item} =
      WorkItem.from_issue(issue, %{
        provider: :plane,
        prior_validated_lifecycle_state: :planning,
        provider_project_contract: settings.provider_project_contract
      })

    {:ok, route} = Router.resolve(work_item, settings.agent.profiles, settings.agent.routes)
    {work_item, route}
  end

  def admit(ledger, grant, route, context \\ %{}) do
    issue = grant.work_item_id
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    options = [pilot_binding: grant, route_fingerprint: route.fingerprint]
    assert {:ok, record} = AttemptLedger.begin_attempt(ledger, issue, options)
    identity = Identity.allocate(issue, route, record.lineage_id)

    identity =
      case context do
        %{fixture_close_attempt_id: id} ->
          %{identity | runtime_attempt_id: id}

        %{fixture_attempt_first_byte: byte} ->
          suffix = :crypto.strong_rand_bytes(15)
          %{identity | runtime_attempt_id: Base.url_encode64(<<byte, suffix::binary>>, padding: false)}

        _ ->
          identity
      end

    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, issue, identity)
    consumed = AttemptLedger.consume_pilot(ledger, grant, identity)
    assert {:ok, %{state: :consumed, runtime_identity: ^identity}} = consumed
    identity
  end

  def native_pin(root, native, context, model_catalog) do
    codex = Path.join(root, "codex")
    evidence_root = (is_nil(context[:rehearsal_root]) && System.get_env("SLICE_C_ROUTED_EVIDENCE")) || Path.join(root, "native-evidence")
    driver = Path.join(native, "tests/run_attempt.py")
    binaries = Enum.map(~w(guard host holder-probe tool-broker request-effect), &Path.join([native, "build", &1]))
    files = [driver, codex, model_catalog, Path.join(native, "tests/provider_fixture.py") | binaries]

    %{
      schema2: :functional,
      pinned_codex: true,
      holder: codex,
      model_catalog: model_catalog,
      driver: driver,
      evidence_root: evidence_root,
      files: Map.new(files, &{&1, digest(File.read!(&1))}),
      fault: Map.get(context, :fixture_fault, "none")
    }
  end

  def prepare(root, staged) do
    assert {:ok, _git} = PathSafety.trusted_executable_identity("/usr/bin/git")
    assert File.ls!(root) == []
    stage_fixture(root, staged.holder)
    {_fixture, _route, _pin, measured} = measure(root, staged)
    freeze(root, measured)
  end

  def execute(root, staged, qualification, host, runner) do
    with {:ok, entries} <- File.ls(root),
         true <- Enum.sort(entries) == ~w(codex policy prepared.json qualification.json source),
         {:ok, {fixture, route, pin, measured}} <- remeasure(root, staged) do
      execute_once(root, measured, qualification, host, fn -> run_rehearsal(fixture, route, pin, runner) end)
    else
      _ -> {:error, :preflight_refused}
    end
  end

  defp remeasure(root, staged) do
    {:ok, measure(root, staged)}
  rescue
    _ -> {:error, :preflight_refused}
  end

  @rehearsal_sources ~w(
    elixir/test/symphony_elixir/pilot_functional_holder_test.exs
    elixir/test/support/test_support.exs
  )

  # The owner qualifies a clean Mix test build of this exact dirty checkout.
  # Execution uses Mix's --no-compile/--no-deps-check and remeasures that build.
  def checkout_provenance(checkout) do
    [commit, tree] = git!(checkout, ["rev-parse", "HEAD", "HEAD^{tree}"]) |> String.split()
    assert git!(checkout, ["ls-files", "--others", "--exclude-standard", "-z"]) == ""
    changed = git!(checkout, ["diff", "--name-only", "-z", "HEAD"])
    assert Enum.all?(String.split(changed, <<0>>, trim: true), &(&1 in @rehearsal_sources))

    ignored = git!(checkout, ["ls-files", "--others", "--ignored", "--exclude-standard", "--directory", "-z"])
    assert Enum.all?(String.split(ignored, <<0>>, trim: true), &(&1 in ~w(elixir/_build/ elixir/deps/ elixir/log/ native/pilot_c02/build/)))

    build = Mix.Project.build_path()
    elixir = Path.join(checkout, "elixir")
    assert Path.expand(".") == elixir and build == Path.join(elixir, "_build/test")
    code_paths = Enum.map(:code.get_path(), &Path.expand(List.to_string(&1)))
    staged_paths = Path.wildcard(Path.join(build, "lib/*/ebin")) ++ [Path.join(build, "lib/symphony_elixir/consolidated")]
    tool_roots = [List.to_string(:code.root_dir()), Path.expand("../..", List.to_string(:code.lib_dir(:elixir)))]
    assert Enum.all?(code_paths, &approved_code_path?(&1, staged_paths, tool_roots, elixir))
    assert Path.join(build, "lib/symphony_elixir/ebin") in code_paths
    assert Path.wildcard(Path.join(elixir, "*.beam"), match_dot: true) == []

    code_files =
      Enum.flat_map(staged_paths, &Path.wildcard(Path.join(&1, "*.{beam,app}"))) ++
        Enum.filter(Path.wildcard(Path.join(build, "lib/*/priv/**/*"), match_dot: true), &File.regular?/1)

    binaries = Map.new(code_files, &{&1, File.read!(&1) |> digest()})
    assert Enum.all?(:code.all_loaded(), &loaded_code_matches?(&1, binaries, build))
    assert build_sources_match?(checkout, build)

    %{
      "commit" => commit,
      "tree" => tree,
      "tracked_diff_sha256" => digest(git!(checkout, ["diff", "--binary", "--full-index", "HEAD"])),
      "build_sha256" => digest(:erlang.term_to_binary(binaries, [:deterministic])),
      "build_files" => map_size(binaries),
      "code_paths" => code_paths,
      "test_modules" => test_module_provenance(checkout),
      "elixir_version" => System.version(),
      "erts_version" => List.to_string(:erlang.system_info(:version))
    }
  end

  defp build_sources_match?(checkout, build) do
    source_paths = git!(checkout, ["ls-files", "-z", "--", "elixir/lib"])
    tracked = MapSet.new(String.split(source_paths, <<0>>, trim: true), &Path.join(checkout, &1))
    beams = Path.wildcard(Path.join(build, "lib/symphony_elixir/ebin/*.beam"))
    beams != [] and Enum.all?(beams, &tracked_source?(&1, tracked))
  end

  defp tracked_source?(file, tracked) do
    with {:ok, {_, [compile_info: compile]}} <- :beam_lib.chunks(String.to_charlist(file), [:compile_info]),
         path when is_list(path) <- Keyword.get(compile, :source) do
      MapSet.member?(tracked, Path.expand(List.to_string(path)))
    else
      _ -> false
    end
  end

  defp test_module_provenance(checkout) do
    modules = [__MODULE__, TestSupport, SymphonyElixir.PilotFunctionalHolderTest]

    for mod <- modules, Code.ensure_loaded?(mod), into: %{} do
      source = mod.module_info(:compile)[:source] |> List.to_string() |> Path.expand()
      assert Path.relative_to(source, checkout) in @rehearsal_sources

      {Atom.to_string(mod),
       %{
         "source_sha256" => digest(File.read!(source)),
         "loaded_md5" => Base.encode16(mod.module_info(:md5), case: :lower)
       }}
    end
  end

  defp approved_code_path?(path, staged_paths, tool_roots, elixir) do
    path == elixir or path in staged_paths or Enum.any?(tool_roots, &String.starts_with?(path, &1 <> "/"))
  end

  defp loaded_code_matches?({mod, file}, binaries, build) when is_list(file) do
    path = Path.expand(List.to_string(file))

    if String.starts_with?(path, build <> "/") do
      with {:ok, expected} <- Map.fetch(binaries, path),
           current <- File.read!(path),
           true <- digest(current) == expected,
           {:ok, {^mod, md5}} <- :beam_lib.md5(current) do
        mod.module_info(:md5) == md5
      else
        _ -> false
      end
    else
      # A loaded module whose selected BEAM comes from the review build must
      # have been loaded from there, including modules shadowed before preflight.
      case :code.where_is_file(Atom.to_charlist(mod) ++ ~c".beam") do
        selected when is_list(selected) -> not Map.has_key?(binaries, Path.expand(List.to_string(selected)))
        _ -> true
      end
    end
  end

  defp loaded_code_matches?(_entry, _binaries, _build), do: true

  defp measure(root, staged) do
    assert {:ok, _git} = PathSafety.trusted_executable_identity("/usr/bin/git")
    fixture = fixture_inputs(root)
    assert git!(fixture.source, ["status", "--porcelain=v1", "--untracked-files=all"]) == ""
    assert File.read!(Path.join(fixture.source, "planner_input.txt")) == @input
    {_work_item, route} = fixture_route(fixture.issue, fixture.parsed)
    pin = native_pin(root, staged.native, %{rehearsal_root: root}, staged.catalog)
    assert pin.files[pin.holder] == digest(File.read!(staged.holder))
    checkout = checkout_provenance(staged.checkout)
    {:ok, hostname} = :inet.gethostname()
    root_stat = File.lstat!(root)

    executables = [
      "/usr/bin/python3",
      "/usr/bin/unshare",
      "/usr/bin/git",
      System.find_executable("elixir"),
      System.find_executable("erl"),
      staged.wrapper
    ]

    measured = %{
      "hostname" => List.to_string(hostname),
      "boot_id" => File.read!("/proc/sys/kernel/random/boot_id") |> String.trim(),
      "root_identity" => [root_stat.major_device, root_stat.minor_device, root_stat.inode],
      "checkout" => checkout,
      "grant" => Map.new(fixture.grant, fn {key, value} -> {Atom.to_string(key), value} end),
      "route" => route.fingerprint,
      "starting_state" => route.starting_state_fingerprint,
      "policy_sha256" => digest(File.read!(Path.join([root, "policy", "planner.md"]))),
      "native_files" => pin.files,
      "executables" => Map.new(executables, fn path -> {path, digest(File.read!(path))} end),
      "evidence_root" => pin.evidence_root,
      "fault" => pin.fault
    }

    {fixture, route, pin, measured}
  end

  def activate_fixture(%{root: root, settings: settings, grant: grant, issue: issue}, context, pin_for_run) do
    File.write!(Workflow.workflow_file_path(), "---\n" <> Jason.encode!(put_in(settings, ["agent", "pilot"], grant)) <> "\n---\n" <> @prompt)
    assert :ok = WorkflowStore.force_reload()
    loaded = Config.settings!()
    assert {:ok, ^grant} = Config.pilot_binding(loaded)
    {work_item, route} = fixture_route(issue, loaded)
    assert is_nil(context[:approved_route]) or context.approved_route === route
    tracker = Tracker.identity(loaded.tracker)
    {:ok, ledger} = AttemptLedger.open(grant.project_id, tracker, root: root)
    on_exit(fn -> AttemptLedger.close(ledger) end)

    identity = admit(ledger, grant, route, context)

    pin = pin_for_run.()

    put_fixture_env(:test_native_pilot, pin)

    opts = [
      pilot_binding: grant,
      attempt_ledger: ledger,
      runtime_attempt_identity: identity,
      route: route,
      work_item: work_item,
      ownership_ledger: TestSupport.workspace_ownership_ledger(),
      runtime: Codex,
      test_native_pilot: pin,
      test_runtime_isolation_admit: fn _, _, _ -> {:ok, :offline_fixture} end,
      test_routed_guard_tool_paths: %{"unshare" => "/usr/bin/unshare", "python3" => "/usr/bin/python3"},
      issue_state_fetcher: fn _ -> flunk("C01 must not request continuation") end,
      plane_epoch_snapshot_reader: fn -> flunk("C01 must not query Plane") end
    ]

    %{issue: issue, opts: opts, grant: grant, ledger: ledger, tracker: tracker, root: root, directory: Path.join(pin.evidence_root, identity.runtime_attempt_id)}
  end

  def assert_positive_evidence(ctx) do
    identity = ctx.opts[:runtime_attempt_identity]
    attempt = identity.runtime_attempt_id

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

    assert {:ok, %{closed?: true} = effects} = RequestLedger.open(attempt, path: Path.join(ctx.directory, "provider-effects.journal"))

    assert [
             %{ordinal: 1, state: :terminal, runtime_attempt_id: ^attempt} = first,
             %{ordinal: 2, state: :terminal, runtime_attempt_id: ^attempt} = second
           ] = RequestLedger.records(effects)

    assert Enum.count(effects.events, &(&1.kind == :closed)) == 1

    assert first.request_id != second.request_id
    assert second.prior_request_id == first.request_id
    assert first.send_may_have_occurred and second.send_may_have_occurred
    assert first.thread_id == result.thread_id and second.turn_id == result.turn_id

    result
  end

  defp run_rehearsal(fixture, route, pin, runner) do
    root = fixture.root

    ctx =
      preserve_failure(root, :not_started, fn ->
        # Refuse leftover or conflicting state before shared setup can write anything.
        assert Enum.sort(File.ls!(root)) == ~w(codex execution.started policy prepared.json qualification.json source)
        assert :ok = TestSupport.start_workflow_fixture(root, :rehearsal)
        ctx = activate_fixture(fixture, %{approved_route: route}, fn -> pin end)
        identity = ctx.opts[:runtime_attempt_identity]
        assert {:ok, %{state: :consumed, runtime_identity: ^identity}} = AttemptLedger.pilot_status(ctx.ledger)
        assert :ok = record(root, "consumed.json", %{attempt: identity.runtime_attempt_id})
        ctx
      end)

    preserve_failure(root, :failed, fn ->
      opts = Keyword.merge(ctx.opts, runtime: __MODULE__, rehearsal_observer: self())
      assert :ok = runner.(ctx, opts)
    end)

    preserve_failure(root, :completed, fn -> collect_rehearsal(ctx, route) end)
  end

  defp collect_rehearsal(ctx, route) do
    root = ctx.root
    identity = ctx.opts[:runtime_attempt_identity]
    result = assert_positive_evidence(ctx)
    assert_received {:rehearsal_binding, binding, workspace}

    snapshot = fn -> snapshot(ctx.ledger, ctx.grant.work_item_id, identity.runtime_attempt_id, Path.join(ctx.directory, "provider-effects.journal")) end
    assert {:ok, %{pilot: %{result: ^result}} = expected} = replay_refusal(ctx.ledger, ctx.grant, snapshot)
    assert :ok = AttemptLedger.close(ctx.ledger)

    files = [
      {"attempt.dets", ctx.ledger.path},
      {"provider-effects.journal", Path.join(ctx.directory, "provider-effects.journal")},
      {"functional-ready.json", Path.join(ctx.directory, "functional-ready.json")},
      {"functional-stop.json", Path.join(ctx.directory, "functional-stop.json")},
      {"routed-stop-observation.json", Path.join(ctx.directory, "routed-stop-observation.json")},
      {"functional-broker-stop.json", Path.join(ctx.directory, "functional-broker-stop.json")},
      {"schema2-input.json", Path.join(ctx.directory, "schema2-input.json")}
    ]

    assert {:ok, hashes} = sealed_copies(root, files, true)
    assert :ok = verify_copies(root, files, hashes)
    assert %{pilot: pilot, current: current} = actual = fresh_rehearsal_status(ctx)
    assert actual === expected
    assert :ok = verify_copies(root, files, hashes)
    assert :ok = record(root, "replay-refusal.json", %{attempt: identity.runtime_attempt_id, result: :pilot_allowance_consumed})
    c04 = %{attempt: identity.runtime_attempt_id, outcome: result.outcome, ledger_sha256: hashes["attempt.dets"]}
    assert :ok = record(root, "c04-readback.json", c04)
    packet = review_packet(ctx, route, pilot, current, binding, workspace, hashes)
    assert :ok = record(root, "guest-evidence.json", packet)
    if packet.evidence_complete, do: :ok, else: {:error, :guest_evidence_incomplete}
  end

  defp preserve_failure(root, execution, action) do
    action.()
  rescue
    exception ->
      capture_result({:ok, nil}, fn _ ->
        record(root, "guest-failure.json", %{
          execution: execution,
          evidence_complete: false,
          stores_verified: false,
          failure: exception.__struct__
        })
      end)

      reraise exception, __STACKTRACE__
  end

  def fresh_rehearsal_status(ctx) do
    code = """
    [path, journal, project, work_item, attempt, tracker64] = System.argv()
    alias SymphonyElixir.AgentRuntime.AttemptLedger
    Code.ensure_loaded!(SymphonyElixir.Tracker)
    Code.ensure_loaded!(AttemptLedger)
    tracker = tracker64 |> Base.decode64!() |> :erlang.binary_to_term([:safe])
    # Reject a dirty store before the ordinary API can repair the working copy.
    {:ok, table} = :dets.open_file(:rehearsal_integrity_check, file: String.to_charlist(path), type: :set, access: :read, repair: false)
    :ok = :dets.close(table)
    {:ok, ledger} = AttemptLedger.open(project, tracker, path: path)
    alias SymphonyElixir.ProviderEffect.RequestLedger
    {:ok, pilot} = AttemptLedger.pilot_status(ledger)
    {:ok, current} = AttemptLedger.current(ledger, work_item)
    {:ok, effects} = RequestLedger.open(attempt, path: journal)
    snapshot = %{pilot: pilot, current: current, events: effects.events, records: RequestLedger.records(effects), closed?: effects.closed?}
    :ok = AttemptLedger.close(ledger)
    IO.write(Base.encode64(:erlang.term_to_binary(snapshot)))
    """

    readback = Path.join(ctx.root, "readback")

    fresh_beam(code, [
      Path.join(readback, "attempt.dets"),
      Path.join(readback, "provider-effects.journal"),
      ctx.grant.project_id,
      ctx.grant.work_item_id,
      ctx.opts[:runtime_attempt_identity].runtime_attempt_id,
      ctx.tracker |> :erlang.term_to_binary() |> Base.encode64()
    ])
  end

  @receipt_formats %{
    "native_ready" => %{"scope" => "SYNTHETIC_PIPE", "kind" => "native-ready", "sequence" => 0},
    "native_stop" => %{"scope" => "SYNTHETIC_PIPE", "kind" => "native-stopped", "sequence" => 1},
    "namespace_stop" => %{"scope" => "SYNTHETIC_PIPE"},
    "broker_stop" => %{"schema" => "H100-HOST-BROKER-STOP-1"}
  }

  defp receipt_fields(slot, attempt, binding) do
    case Map.fetch(@receipt_formats, slot) do
      {:ok, fields} -> Map.merge(fields, %{"attempt" => attempt, "binding" => binding})
      :error -> %{}
    end
  end

  def review_packet(ctx, route, pilot, current, binding, workspace, hashes) do
    identity = ctx.opts[:runtime_attempt_identity]
    %{runtime_attempt_id: attempt} = identity
    {:ok, bytes} = read_regular(Path.join(ctx.directory, "schema2-input.json"))
    assert digest(bytes) == hashes["schema2-input.json"]
    %{"context" => native} = Jason.decode!(bytes)

    native_inputs = %{
      binding_sha256: native["binding_id"],
      attempt_id: native["attempt_id"],
      project_id: native["project_id"],
      work_item_id: native["work_item_id"],
      role: native["role"],
      grant_sha256: native["grant_id"],
      source_commit: native["source_commit"],
      source_tree: native["source_tree"],
      configuration_digest: native["configuration_digest"]
    }

    resources = %{
      "home" => Path.join(ctx.directory, "home"),
      "codex-home" => Path.join(ctx.directory, "codex-home"),
      "materialize.sock" => Path.join(ctx.directory, "materialize.sock"),
      "workspace" => workspace
    }

    reference =
      {:c01_reference_v1,
       %{
         expected_grant: ctx.grant,
         pilot: Map.take(pilot, [:state, :grant, :runtime_identity]),
         current: Map.take(current, [:schema_version, :project_namespace, :issue_id, :lineage_id, :route_fingerprint, :authority_fence]),
         route: route,
         native_binding_sha256: binding,
         resource_ids: Map.keys(resources)
       }}

    artifacts = %{
      "native_ready" => Path.join(ctx.directory, "functional-ready.json"),
      "native_stop" => Path.join(ctx.directory, "functional-stop.json"),
      "namespace_stop" => Path.join(ctx.directory, "routed-stop-observation.json"),
      "broker_stop" => Path.join(ctx.directory, "functional-broker-stop.json"),
      "request_close" => Path.join(ctx.directory, "provider-effects.journal"),
      "c04_readback" => Path.join(ctx.root, "c04-readback.json"),
      "replay_refusal" => Path.join(ctx.root, "replay-refusal.json")
    }

    resource_observations = Map.new(resources, fn {key, path} -> {key, resource(path, ctx.root)} end)

    observations =
      Enum.map(artifacts, fn {key, path} ->
        status = artifact(path, hashes, receipt_fields(key, attempt, binding))
        {{:artifact, key}, attempt, binding, status}
      end) ++
        Enum.map(resource_observations, fn {key, {status, _metadata}} -> {{:resource, key}, attempt, binding, status} end)

    fixture =
      {:c01_evidence_fixture_v1,
       %{
         runtime_identity: identity,
         route_fingerprint: route.fingerprint,
         canonical_grant_sha256: canonical_grant(ctx.grant),
         native: native_inputs,
         observations: observations
       }}

    assert {:ok, :correlated, inventory} = C01EvidenceReview.review(reference, fixture)
    complete? = inventory.missing == [] and inventory.ambiguous == []

    %{
      execution: :completed,
      evidence_complete: complete?,
      stores_verified: true,
      attempt: attempt,
      binding: binding,
      sealed_sha256: hashes,
      resources: Map.new(resource_observations, fn {key, {_status, metadata}} -> {key, metadata} end),
      observations:
        Enum.map(observations, fn {{kind, name}, _, _, status} ->
          %{kind: kind, name: name, status: Tuple.to_list(if(is_tuple(status), do: status, else: {status}))}
        end)
    }
  end

  def fresh_beam(code, arguments) do
    code_paths = Enum.flat_map(:code.get_path(), &["-pa", List.to_string(&1)])

    {output, 0} =
      System.cmd(System.find_executable("elixir"), code_paths ++ ["-e", code, "--" | arguments],
        stderr_to_stdout: true,
        env: [{"ERL_FLAGS", "+S 2:2 +SDio 1 +SDcpu 1"}]
      )

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

  def put_fixture_env(key, value) do
    prior = Application.fetch_env(:symphony_elixir, key)
    Application.put_env(:symphony_elixir, key, value)

    on_exit(fn ->
      case prior do
        {:ok, old} -> Application.put_env(:symphony_elixir, key, old)
        :error -> Application.delete_env(:symphony_elixir, key)
      end
    end)
  end

  def git!(source, args) do
    {output, 0} = System.cmd("/usr/bin/git", ["-c", "core.hooksPath=/dev/null", "-C", source | args], stderr_to_stdout: true)
    output
  end

  # External observations are inputs to this decision, never inferred from a guest result.
  def disposition(
        %{execution: :completed, evidence_complete: true, stores_verified: true},
        %{outer_stopped: true, normal_service_exit: true, inventory_verified: true, backup_verified: true}
      ),
      do: :evidence_preserved

  def disposition(
        %{execution: :failed, evidence_complete: true, stores_verified: true},
        %{outer_stopped: true, inventory_verified: true, backup_verified: true}
      ),
      do: :failed_retained

  def disposition(_guest, _external), do: :incomplete_retained
end

if binary = System.get_env("PINNED_CODEX_FUNCTIONAL_BINARY") do
  defmodule SymphonyElixir.PilotFunctionalHolderTest do
    use SymphonyElixir.TestSupport, h100_rehearsal: true

    alias SymphonyElixir.AgentRuntime.{AttemptLedger, Codex}
    alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
    alias SymphonyElixir.PilotRehearsal, as: Rehearsal
    alias SymphonyElixir.ProviderEffect.RequestLedger
    alias SymphonyElixir.TestSupport
    @binary binary
    @item "22222222-2222-4222-8222-222222222222"

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

            {:request_close, _arm} ->
              :ok
          end

          {:ok, {session, Keyword.fetch!(opts, :attempt_ledger), fault}}
        end
      end

      @impl true
      def run_turn({session, _ledger, {:request_close, arm}}, prompt, issue, opts) do
        opts = Keyword.update!(opts, :on_message, &close_fault_callback(&1, arm))

        try do
          result = Codex.run_turn(session, prompt, issue, opts)
          send(self(), {:fixture_close_turn_result, result})
          result
        after
          File.rm(arm)
        end
      end

      def run_turn({session, _ledger, _fault}, prompt, issue, opts) do
        Codex.run_turn(session, prompt, issue, opts)
      end

      def close_fault_callback(on_message, arm) do
        fn message ->
          case message do
            %{event: :notification, payload: %{"method" => "item/completed", "params" => %{"item" => %{"phase" => "final_answer"}}}} ->
              File.write!(arm, "active", [:exclusive])
              send(self(), :fixture_close_fault_armed)

            %{event: :turn_completed} ->
              send(self(), :fixture_successful_turn_event)

            _ ->
              :ok
          end

          on_message.(message)
        end
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
      def stop_session({session, _ledger, {:request_close, _arm}}), do: Codex.stop_session(session)
    end

    setup_all do
      assert System.get_env("PLANE_API_KEY") == "SYNTHETIC-NONLIVE-PLANE-KEY"
      native = Path.expand("../../../native/pilot_c02", __DIR__)

      if is_nil(System.get_env("H100_REHEARSAL_MODE")) do
        {output, status} = System.cmd("/usr/bin/make", ["-C", native, "all"], stderr_to_stdout: true)
        assert status == 0, output
      end

      {:ok, native: native}
    end

    setup %{native: native} = context do
      if context[:rehearsal_root] do
        :ok
      else
        root = Path.dirname(Workflow.workflow_file_path())
        Rehearsal.stage_fixture(root, @binary)
        fixture = Rehearsal.fixture_inputs(root)
        {:ok, Rehearsal.activate_fixture(fixture, context, fn -> Rehearsal.native_pin(root, native, context, Path.expand("../native/pinned_codex/tests/fixtures/synthetic_model.json")) end)}
      end
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
      assert :ok = AgentRunner.run(ctx.issue, self(), ctx.opts)
      result = Rehearsal.assert_positive_evidence(ctx)
      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, @item, pilot_binding: ctx.grant)
      assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
      assert :ok = AttemptLedger.close(ctx.ledger)
      identity = ctx.opts[:runtime_attempt_identity]
      assert %{state: :stopverified, runtime_identity: ^identity, result: ^result} = fresh_pilot_status(ctx)
      assert %{closed?: true, states: [{1, :terminal}, {2, :terminal}]} = fresh_request_status(ctx)
    end

    @tag skip: System.get_env("H100_REHEARSAL_MODE") not in ["prepare", "inspect", "execute"]
    @tag :h100_evidence_only_rehearsal
    test "one evidence-only Planner rehearsal", %{rehearsal_root: root, rehearsal_mode: mode, native: native} do
      staged = %{
        holder: @binary,
        native: native,
        catalog: Path.expand("../native/pinned_codex/tests/fixtures/synthetic_model.json"),
        checkout: Path.expand(".."),
        wrapper: System.get_env("H100_REHEARSAL_SOCKET_WRAPPER")
      }

      case mode do
        "prepare" ->
          assert :ok = Rehearsal.prepare(root, staged)

        "inspect" ->
          assert {:ok, %{"grant" => _}} = Rehearsal.inspect_prepared(root)

        "execute" ->
          qualification = System.fetch_env!("H100_REHEARSAL_QUALIFICATION_SHA256")
          host = System.fetch_env!("H100_REHEARSAL_HOST_IDENTITY") |> Jason.decode!()
          runner = fn ctx, opts -> AgentRunner.run(ctx.issue, self(), opts) end
          assert {:ok, :ok} = Rehearsal.execute(root, staged, qualification, host, runner)
      end
    end

    if close_fault = System.get_env("SLICE_C_CLOSE_FIXTURE") do
      @tag fixture_close_attempt_id: System.fetch_env!("SLICE_C_CLOSE_ATTEMPT_ID")
      @tag close_fault: close_fault
      test "real stop remains mandatory when the completed Planner turn cannot confirm journal closure", ctx do
        arm = System.fetch_env!("H100_FIXTURE_ARM")

        opts =
          Keyword.merge(ctx.opts,
            runtime: FaultedStorage,
            fixture_storage_fault: {:request_close, arm},
            defer_runtime_stop: true
          )

        reason = if ctx.close_fault == "corrupt", do: :journal_corrupt, else: :journal_sync_failed
        actual = capture_fault(ctx, opts)

        assert_received :fixture_close_fault_armed
        assert_received {:fixture_close_turn_result, turn_result}
        assert {:error, {:turn_failed, {:provider_effect_close_unconfirmed, ^reason}}} = turn_result
        assert {:raised, RuntimeError, "Pilot execution failed"} = actual
        refute_received :fixture_successful_turn_event
        assert_received {:runtime_attempt_lifecycle, @item, _, :stopping}
        assert_received {:runtime_attempt_lifecycle, @item, _, :containment_proven_dead}
        assert_functional_stop(ctx)
        assert %{"events" => events} = fault_receipt(ctx, "functional-rpc-observations.json")
        assert Enum.any?(events, &match?(%{"method" => "turn/completed", "status" => "completed"}, &1))
        assert_one_finished_tool(ctx)
        assert_failed_request_close(ctx, reason)

        identity = ctx.opts[:runtime_attempt_identity]

        assert {:ok, %{state: :stopverified, runtime_identity: ^identity, result: result}} =
                 AttemptLedger.pilot_status(ctx.ledger)

        assert %{outcome: :failed, model_state: :failed, stop_disposition: :verified} = result
        assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
        assert :ok = AttemptLedger.close(ctx.ledger)
        assert %{runtime_identity: ^identity, result: ^result} = fresh_pilot_status(ctx)
      end

      if close_fault == "write" do
        alias SymphonyElixir.AgentRuntime.Profile
        alias SymphonyElixir.Codex.AppServer

        @tag fixture_close_attempt_id: System.fetch_env!("SLICE_C_CLOSE_ATTEMPT_ID")
        @tag :nondeferred_close_fault
        test "direct AppServer turn stops before returning the journal close error", ctx do
          arm = System.fetch_env!("H100_FIXTURE_ARM")
          identity = ctx.opts[:runtime_attempt_identity]
          assert :ok = AttemptLedger.claim_pilot_launch(ctx.ledger, ctx.grant, identity)
          assert {:ok, workspace} = Workspace.create_for_issue(ctx.issue, nil, ctx.opts[:ownership_ledger])

          opts =
            ctx.opts
            |> Keyword.merge(Profile.runtime_options(ctx.opts[:route].profile))
            |> Keyword.put(:runtime_issue, ctx.issue)
            |> Keyword.put(:absolute_deadline_ms, System.monotonic_time(:millisecond) + ctx.grant.deadline_ms)

          assert {:ok, %{port: port} = session} = AppServer.start_session(workspace, opts)
          monitor = Port.monitor(port)
          prompt = PromptBuilder.build_prompt(ctx.issue, opts)

          try do
            assert {:error, {:provider_effect_close_unconfirmed, :journal_sync_failed}} =
                     AppServer.run_turn(session, prompt, ctx.issue,
                       model: opts[:model],
                       defer_runtime_stop: false,
                       on_message: FaultedStorage.close_fault_callback(fn _ -> :ok end, arm)
                     )

            assert_received :fixture_close_fault_armed
            refute_received :fixture_successful_turn_event
            assert_receive {:DOWN, ^monitor, :port, ^port, _}, 1_000
            assert_functional_stop(ctx)
            assert_one_finished_tool(ctx)
          after
            File.rm(arm)
            if Process.demonitor(monitor, [:flush, :info]), do: AppServer.stop_session(session)
          end
        end
      end

      defp assert_functional_stop(ctx) do
        assert %{"helper_stopped" => true, "tool_stopped" => true} = fault_receipt(ctx, "functional-broker-stop.json")
        assert %{"pid1_stop_verified" => true, "port_down_observed" => true} = fault_receipt(ctx, "routed-stop-observation.json")
      end

      defp assert_one_finished_tool(ctx) do
        states =
          ctx.directory
          |> Path.join("broker-events.jsonl")
          |> File.stream!()
          |> Enum.map(&Jason.decode!(&1)["state"])

        assert Enum.count(states, &(&1 == "STARTED")) == 1
        assert Enum.count(states, &(&1 == "STOP_VERIFIED")) == 1
      end

      defp assert_failed_request_close(ctx, :journal_corrupt) do
        path = Path.join(ctx.directory, "provider-effects.journal")
        assert File.read!(path) |> String.ends_with?("\n{")
        assert {:error, :journal_corrupt} = fresh_request_status(ctx)
      end

      defp assert_failed_request_close(ctx, :journal_sync_failed) do
        closed? = ctx.close_fault != "write"
        assert %{closed?: ^closed?, states: [{1, :terminal}, {2, :terminal}]} = fresh_request_status(ctx)
      end
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

    for {fault, ordinal, request_state, expected_native} <- [
          {"native_ack_lost", 1, :pre_send_intent, "POSSIBLE_SEND_ACK"},
          {"invocation_permission_lost", 1, :ambiguous, "INVOCATION_PERMITTED"},
          {"response_headers_lost", 1, :ambiguous, "INVOCATION_PERMITTED"},
          {"response_created_lost", 1, :ambiguous, "INVOCATION_PERMITTED"},
          {"tool_item_lost", 1, :ambiguous, "OBSERVED_ACCEPTANCE"},
          {"final_stream_lost", 2, :ambiguous, "OBSERVED_ACCEPTANCE"}
        ] do
      @tag fixture_fault: fault
      @tag recovery_cut: true
      test "reopens consumed authority after #{fault}", ctx do
        assert {:returned, {:error, {:runtime_containment_unconfirmed, :termination_timeout}}} = capture_fault(ctx, ctx.opts)

        ordinal = unquote(ordinal)
        state = unquote(request_state)
        assert %{"checkpoint" => unquote(fault), "ordinal" => ^ordinal} = fault_receipt(ctx, "recovery-checkpoint")

        assert [%{ordinal: ^ordinal, state: ^state, request_id: request_id} | prior] =
                 Enum.reverse(request_records(ctx))

        assert length(prior) == ordinal - 1
        assert Enum.all?(prior, &match?(%{state: :terminal}, &1))
        path = Path.join(ctx.directory, "request-effect-#{request_id}.jsonl")
        assert %{"state" => unquote(expected_native)} = path |> File.stream!() |> Enum.map(&Jason.decode!/1) |> List.last()

        attempt = ctx.opts[:runtime_attempt_identity].runtime_attempt_id
        assert {:ok, %{closed?: true}} = RequestLedger.open(attempt, path: Path.join(ctx.directory, "provider-effects.journal"))
        refute File.exists?(Path.join(ctx.directory, "routed-stop-observation.json"))
        identity = ctx.opts[:runtime_attempt_identity]

        assert {:ok, %{state: :quarantined, runtime_identity: ^identity, result: result}} =
                 AttemptLedger.pilot_status(ctx.ledger)

        assert %{outcome: :failed, final_answer: nil} = result

        assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, @item, pilot_binding: ctx.grant)
        assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
        assert :ok = AttemptLedger.close(ctx.ledger)
        assert %{state: :quarantined, runtime_identity: ^identity, result: ^result} = fresh_pilot_status(ctx)
      end
    end

    @tag fixture_fault: "missing_tool_pidfd"
    test "without a pidfd for the started tool, the routed path retains quarantine", ctx do
      assert {:returned, {:error, {:runtime_containment_unconfirmed, :termination_timeout}}} = capture_fault(ctx, ctx.opts)
      assert %{"state" => "STARTED", "pid" => pid} = fault_receipt(ctx, "tool-pidfd-fault.json")

      events = ctx.directory |> Path.join("broker-events.jsonl") |> File.stream!() |> Enum.map(&Jason.decode!/1)
      assert Enum.any?(events, &match?(%{"state" => "STARTED", "pid" => ^pid}, &1))
      refute Enum.any?(events, &match?(%{"state" => "STOP_VERIFIED"}, &1))
      refute File.exists?(Path.join(ctx.directory, "broker-release"))
      refute File.exists?(Path.join(ctx.directory, "functional-broker-stop.json"))
      refute File.exists?(Path.join(ctx.directory, "routed-stop-observation.json"))
      assert [%{ordinal: 1, state: :terminal}] = request_records(ctx)
      identity = ctx.opts[:runtime_attempt_identity]
      assert {:ok, %{state: :quarantined, runtime_identity: ^identity, result: result}} = AttemptLedger.pilot_status(ctx.ledger)
      assert %{outcome: :failed, final_answer: nil} = result
      assert {:error, _} = AttemptLedger.begin_attempt(ctx.ledger, @item, pilot_binding: ctx.grant)
      assert_raise RuntimeError, "Pilot launch refused", fn -> AgentRunner.run(ctx.issue, self(), ctx.opts) end
      assert :ok = AttemptLedger.close(ctx.ledger)
      assert %{state: :quarantined, runtime_identity: ^identity, result: ^result} = fresh_pilot_status(ctx)
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
      assert {:ok, ledger} = request_journal(ctx)
      RequestLedger.records(ledger)
    end

    defp request_journal(ctx) do
      path = Path.join(ctx.directory, "provider-effects.journal")
      attempt = ctx.opts[:runtime_attempt_identity].runtime_attempt_id
      RequestLedger.open(attempt, path: path)
    end

    defp fresh_request_status(ctx) do
      path = Path.join(ctx.directory, "provider-effects.journal")
      attempt = ctx.opts[:runtime_attempt_identity].runtime_attempt_id

      code = """
      alias SymphonyElixir.ProviderEffect.RequestLedger
      [attempt, path] = System.argv()
      result =
        case RequestLedger.open(attempt, path: path) do
          {:ok, ledger} ->
            %{closed?: ledger.closed?, states: Enum.map(RequestLedger.records(ledger), &{&1.ordinal, &1.state})}
          error ->
            error
        end
      IO.write(Base.encode64(:erlang.term_to_binary(result)))
      """

      Rehearsal.fresh_beam(code, [attempt, path])
    end

    defp fresh_pilot_status(ctx) do
      code =
        "alias SymphonyElixir.AgentRuntime.AttemptLedger; " <>
          "{:ok, ledger} = AttemptLedger.open(#{inspect(ctx.grant.project_id)}, #{inspect(ctx.tracker)}, root: #{inspect(ctx.root)}); " <>
          "{:ok, state} = AttemptLedger.pilot_status(ledger); " <>
          ":ok = AttemptLedger.close(ledger); IO.puts(Base.encode64(:erlang.term_to_binary(state)))"

      Rehearsal.fresh_beam(code, [])
    end
  end
end

defmodule SymphonyElixir.PilotRehearsalTest do
  use ExUnit.Case

  alias SymphonyElixir.AgentRuntime.AttemptLedger
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.PilotRehearsal, as: Rehearsal
  alias SymphonyElixir.ProviderEffect.RequestLedger
  alias SymphonyElixir.TestSupport

  setup do
    root = Path.join(System.tmp_dir!(), "h100-rehearsal-test-#{System.unique_integer([:positive])}")
    File.mkdir!(root)
    File.chmod!(root, 0o700)
    on_exit(fn -> File.rm_rf!(root) end)
    %{root: root}
  end

  test "preparation freezes inputs once, without admission or runner entry", %{root: root} do
    input = %{"commit" => "fixture", "binary" => "held"}
    assert :ok == Rehearsal.freeze(root, input)
    assert {:error, :eexist} == Rehearsal.freeze(root, %{"commit" => "other"})
    assert {:ok, ^input} = Rehearsal.inspect_prepared(root)
    refute File.exists?(Path.join(root, "execution.started"))
    assert File.ls!(root) == ["prepared.json"]
  end

  test "execution refuses changed or unapproved inputs before calling admission, and runs once", %{root: root} do
    input = %{"commit" => "fixture", "binary" => "held"}
    host = identity("host")
    input = Map.merge(input, identity("guest"))
    assert :ok == Rehearsal.freeze(root, input)
    hash = approve(root, host)

    execute = fn ->
      send(self(), :c01_admission)
      send(self(), :runner_entry)
      :ran
    end

    changed_inputs = %{input | "binary" => "changed"}
    assert {:error, :preflight_refused} = Rehearsal.execute_once(root, changed_inputs, hash, host, execute)
    assert {:error, :preflight_refused} = Rehearsal.execute_once(root, input, "wrong", host, execute)
    assert {:error, :preflight_refused} = Rehearsal.execute_once(root, input, hash, identity("other"), execute)
    refute_received :c01_admission
    refute_received :runner_entry
    refute File.exists?(Path.join(root, "execution.started"))

    assert {:ok, :ran} == Rehearsal.execute_once(root, input, hash, host, execute)
    assert_received :c01_admission
    assert_received :runner_entry
    assert {:error, :execution_already_started} == Rehearsal.execute_once(root, input, hash, host, execute)
    refute_received :c01_admission
    refute_received :runner_entry
    assert {:ok, ^input} = Rehearsal.inspect_prepared(root)
  end

  test "root retention is scoped to the opted-in module, tagged case and private root", %{root: root} do
    keys = ["H100_REHEARSAL_MODE", "H100_REHEARSAL_ROOT"]
    prior = Map.new(keys, &{&1, System.get_env(&1)})

    on_exit(fn ->
      Enum.each(keys, &System.delete_env/1)
      System.put_env(Map.reject(prior, fn {_key, value} -> is_nil(value) end))
    end)

    assert :ordinary = TestSupport.fixture_root(false, %{h100_evidence_only_rehearsal: true})
    System.put_env(%{"H100_REHEARSAL_MODE" => "inspect", "H100_REHEARSAL_ROOT" => root})
    assert {:rehearsal, ^root, "inspect"} = TestSupport.fixture_root(true, %{h100_evidence_only_rehearsal: true})
    assert_raise RuntimeError, "H-100 rehearsal fixture root refused", fn -> TestSupport.fixture_root(true, %{}) end
    File.chmod!(root, 0o755)

    assert_raise RuntimeError, "H-100 rehearsal fixture root refused", fn ->
      TestSupport.fixture_root(true, %{h100_evidence_only_rehearsal: true})
    end
  end

  test "ordinary cleanup removes its root, while rehearsal cleanup preserves partial evidence", %{root: root} do
    ordinary = Path.join(root, "ordinary")
    retained = Path.join(root, "retained")
    File.mkdir!(ordinary)
    File.mkdir!(retained)
    marker = Path.join(retained, "partial-journal")
    File.write!(marker, "original")
    assert :ok == TestSupport.finish_fixture_root(ordinary, :ordinary)
    assert :ok == TestSupport.finish_fixture_root(retained, :rehearsal)
    refute File.exists?(ordinary)
    assert File.read!(marker) == "original"
  end

  test "collector exceptions preserve the started session for stop handling" do
    session = {make_ref(), %{pilot_holder_context: %{digest: "binding"}}}
    stop = fn ^session -> send(self(), :stopped) end

    assert {:ok, ^session} = Rehearsal.capture_result({:ok, session}, fn _ -> raise "collector failure" end)
    stop.(session)
    assert_received :stopped
    capture = fn _ -> send(self(), :unexpected_capture) end
    assert {:error, :start_failed} = Rehearsal.capture_result({:error, :start_failed}, capture)
    refute_received :unexpected_capture
  end

  test "failure after admission starts retains originals and permanently refuses another invocation", %{root: root} do
    inputs = Map.put(identity("guest"), "commit", "fixture")
    host = identity("host")
    assert :ok = Rehearsal.freeze(root, inputs)
    hash = approve(root, host)
    original = Path.join(root, "partial-journal")

    assert_raise RuntimeError, "interrupted", fn ->
      Rehearsal.execute_once(root, inputs, hash, host, fn ->
        File.write!(original, "partial")
        raise "interrupted"
      end)
    end

    assert {:error, :execution_already_started} =
             Rehearsal.execute_once(root, inputs, hash, host, fn -> flunk("ran twice") end)

    assert File.read!(original) == "partial"
  end

  test "closed bytes are sealed separately and a changed readback cannot be promoted", %{root: root} do
    original = Path.join(root, "journal")
    File.write!(original, "source bytes")
    files = [{"journal", original}]

    assert {:error, :unverified_retained} = Rehearsal.sealed_copies(root, files, false)
    refute File.exists?(Path.join(root, "readback"))
    assert {:ok, hashes} = Rehearsal.sealed_copies(root, files, true)
    assert :ok = Rehearsal.verify_copies(root, files, hashes)
    assert {:observed, _} = Rehearsal.artifact(original, hashes)
    assert :missing == Rehearsal.artifact(Path.join(root, "absent"), hashes)

    File.write!(Path.join([root, "readback", "journal"]), "changed")
    assert {:error, :unverified_retained} = Rehearsal.verify_copies(root, files, hashes)
    assert File.read!(original) == "source bytes"
    assert File.read!(Path.join([root, "originals", "journal"])) == "source bytes"
    File.write!(original, "conflicting bytes")
    assert {:ambiguous, :unconfirmed, _} = Rehearsal.artifact(original, hashes)
  end

  test "admission-only refusal leaves pilot, fence and full journal unchanged", %{root: root} do
    grant = %{
      project_id: "pilot-functional",
      plane_project_id: "11111111-1111-4111-8111-111111111111",
      work_item_id: "22222222-2222-4222-8222-222222222222",
      responsibility: "planning",
      source_commit: String.duplicate("a", 40),
      source_tree: String.duplicate("b", 40),
      config_identity: String.duplicate("c", 64),
      runtime_lineage: "rehearsal",
      deadline_ms: 25_000
    }

    identity = %Identity{
      runtime_attempt_id: Base.url_encode64(<<1::128>>, padding: false),
      work_item_id: grant.work_item_id,
      responsibility: "planning",
      runtime_profile: "planner",
      lineage_generation: grant.runtime_lineage
    }

    tracker = %{tracker_kind: "memory", provider_scope: %{project_slug: "pilot"}}
    assert {:ok, ledger} = AttemptLedger.open(grant.project_id, tracker, root: root)
    on_exit(fn -> AttemptLedger.close(ledger) end)
    assert :ok = AttemptLedger.configure_pilot(ledger, grant)
    assert {:ok, _} = AttemptLedger.begin_attempt(ledger, grant.work_item_id, pilot_binding: grant)
    assert {:ok, _} = AttemptLedger.bind_runtime_attempt(ledger, grant.work_item_id, identity)
    assert {:ok, _} = AttemptLedger.consume_pilot(ledger, grant, identity)

    journal = Path.join(root, "journal")
    assert {:ok, effects} = RequestLedger.open(identity.runtime_attempt_id, path: journal)
    assert {:ok, _} = RequestLedger.close_admission(effects)
    snapshot = fn -> Rehearsal.snapshot(ledger, grant.work_item_id, identity.runtime_attempt_id, journal) end
    before = snapshot.()
    assert {:ok, ^before} = Rehearsal.replay_refusal(ledger, grant, snapshot)
    assert before == snapshot.()

    assert {:error, :replay_refusal_unverified} =
             Rehearsal.replay_refusal(ledger, grant, fn -> Map.put(snapshot.(), :different, make_ref()) end)

    assert :ok = AttemptLedger.close(ledger)

    files = [{"attempt.dets", ledger.path}, {"journal", journal}]
    assert {:ok, hashes} = Rehearsal.sealed_copies(root, files, true)
    working_ledger = Path.join([root, "readback", "attempt.dets"])
    working_journal = Path.join([root, "readback", "journal"])
    assert {:ok, reopened} = AttemptLedger.open(grant.project_id, tracker, path: working_ledger)
    assert ^before = Rehearsal.snapshot(reopened, grant.work_item_id, identity.runtime_attempt_id, working_journal)
    assert :ok = AttemptLedger.close(reopened)
    assert :ok = Rehearsal.verify_copies(root, files, hashes)
  end

  defp identity(name), do: %{"hostname" => name, "boot_id" => "8cb7233b-83ea-4a7c-9718-b6b007c78dd5"}

  defp approval(root, host) do
    prepared = File.read!(Path.join(root, "prepared.json"))
    guest = Map.take(Jason.decode!(prepared), ~w(hostname boot_id))
    checks = ~w(source_build_match trusted_executables network_isolation resource_controls descendant_termination hypervisor_fallback evidence_export encrypted_backup)

    %{
      "schema" => "h100-rehearsal-approval-v1",
      "scope" => "one-evidence-only-execution",
      "root" => root,
      "prepared_sha256" => Rehearsal.digest(prepared),
      "host" => host,
      "guest" => guest,
      "prerequisites" => Map.new(checks, &{&1, true})
    }
  end

  defp approve(root, host), do: write_approval(root, approval(root, host))

  defp write_approval(root, record) do
    bytes = Jason.encode!(record)
    File.write!(Path.join(root, "qualification.json"), bytes)
    Rehearsal.digest(bytes)
  end

  test "correlation alone cannot finalize a rehearsal" do
    complete = %{outer_stopped: true, normal_service_exit: true, inventory_verified: true, backup_verified: true}
    guest = %{execution: :completed, evidence_complete: true, stores_verified: true}
    failed = %{guest | execution: :failed}

    assert :evidence_preserved == Rehearsal.disposition(guest, complete)
    assert :failed_retained == Rehearsal.disposition(failed, complete)

    for key <- Map.keys(complete) do
      assert :incomplete_retained == Rehearsal.disposition(guest, Map.put(complete, key, false))
    end

    for disposition <- [guest, failed], key <- [:evidence_complete, :stores_verified] do
      assert :incomplete_retained == Rehearsal.disposition(Map.put(disposition, key, false), complete)
      assert :incomplete_retained == Rehearsal.disposition(Map.delete(disposition, key), complete)
    end
  end

  test "actual preparation and execution exercise the same frozen inputs and closed approval", %{root: root} do
    use_synthetic_tracker_key()
    {run, staged} = stage_synthetic(root)
    assert :ok = Rehearsal.prepare(run, staged)
    assert {:ok, prepared} = Rehearsal.inspect_prepared(run)
    refute File.exists?(Path.join(run, "attempt-ledger"))
    refute File.exists?(Path.join(run, "execution.started"))
    assert File.ls!(run) |> Enum.sort() == ~w(codex policy prepared.json source)
    assert prepared["checkout"]["build_files"] > 0
    assert prepared["grant"]["source_commit"] == git_head(Path.join(run, "source"))

    host = identity("external-host")
    approval = approval(run, host)
    reject = fn _ctx, _opts -> flunk("runner reached despite rejected prerequisite") end

    for rejected <- [
          Map.delete(approval, "prerequisites"),
          Map.delete(approval, "host"),
          Map.put(approval, "prerequisites", []),
          update_in(approval["prerequisites"], &Map.delete(&1, "network_isolation")),
          Map.put(approval, "extra", true),
          Map.put(approval, "scope", "inspection"),
          Map.put(approval, "guest", identity("wrong-guest")),
          Map.put(approval, "host", identity("wrong-host")),
          Map.put(approval, "prepared_sha256", String.duplicate("0", 64)),
          put_in(approval, ["prerequisites", "resource_controls"], false)
        ] do
      assert {:error, :preflight_refused} = Rehearsal.execute(run, staged, write_approval(run, rejected), host, reject)
      refute File.exists?(Path.join(run, "attempt-ledger"))
      refute File.exists?(Path.join(run, "execution.started"))
    end

    duplicate = ~s({"scope":"inspection",) <> String.trim_leading(Jason.encode!(approval), "{")
    File.write!(Path.join(run, "qualification.json"), duplicate)
    assert {:error, :preflight_refused} = Rehearsal.execute(run, staged, Rehearsal.digest(duplicate), host, reject)
    refute File.exists?(Path.join(run, "attempt-ledger"))

    approved_hash = write_approval(run, approval)
    assert {:error, :preflight_refused} = Rehearsal.execute(run, staged, String.duplicate("0", 64), host, reject)
    original = File.read!(staged.holder)
    File.write!(staged.holder, original <> "changed")
    assert {:error, :preflight_refused} = Rehearsal.execute(run, staged, approved_hash, host, reject)
    File.write!(staged.holder, original)

    build_file = Path.join(Mix.Project.build_path(), "lib/symphony_elixir/ebin/h100_extra_test_artifact.app")
    assert :ok = File.write(build_file, "unapproved generated bytes", [:exclusive])

    try do
      assert {:error, :preflight_refused} = Rehearsal.execute(run, staged, approved_hash, host, reject)
    after
      File.rm!(build_file)
    end

    refute File.exists?(Path.join(run, "attempt-ledger"))
    refute File.exists?(Path.join(run, "execution.started"))

    assert {:ok, :ok} = Rehearsal.execute(run, staged, approved_hash, host, &synthetic_completion/2)
    assert_received {:synthetic_runner, ctx, workspace}
    refute_received {:synthetic_runner, _, _}
    assert {:error, :preflight_refused} = Rehearsal.execute(run, staged, approved_hash, host, reject)
    assert {:ok, ^prepared} = Rehearsal.inspect_prepared(run)
    assert prepared["grant"]["source_commit"] == git_head(Path.join(run, "source"))

    packet = run |> Path.join("guest-evidence.json") |> File.read!() |> Jason.decode!()
    assert %{"execution" => "completed", "evidence_complete" => true, "stores_verified" => true} = packet
    assert Enum.frequencies_by(packet["observations"], & &1["kind"]) == %{"artifact" => 7, "resource" => 4}
    verify_negative_projections(ctx, workspace, packet)
  end

  for {finding, receipts} <- [
        {"wrong binding", [{"functional-ready.json", "native_ready", %{"binding" => String.duplicate("b", 64)}}]},
        {"wrong attempt", [{"functional-stop.json", "native_stop", %{"attempt" => "foreign-attempt"}}]},
        {"matching namespace and broker bindings from another session",
         [
           {"routed-stop-observation.json", "namespace_stop", %{"binding" => String.duplicate("b", 64)}},
           {"functional-broker-stop.json", "broker_stop", %{"binding" => String.duplicate("b", 64)}}
         ]},
        {"malformed JSON", [{"functional-stop.json", "native_stop", "{malformed"}]},
        {"duplicate identity field", [{"functional-ready.json", "native_ready", :duplicate_binding}]},
        {"wrong receipt kind", [{"functional-ready.json", "native_ready", %{"kind" => "native-stopped"}}]}
      ] do
    test "sealed receipts cannot complete evidence with #{finding}", %{root: root} do
      use_synthetic_tracker_key()
      {run, staged} = stage_synthetic(root)
      assert :ok = Rehearsal.prepare(run, staged)
      host = identity("external-host")
      approval = approve(run, host)
      receipts = unquote(Macro.escape(receipts))

      result =
        Rehearsal.execute(run, staged, approval, host, fn ctx, opts ->
          assert :ok = synthetic_completion(ctx, opts)
          Enum.each(receipts, &alter_synthetic_receipt(ctx.directory, &1))
        end)

      assert {:ok, {:error, :guest_evidence_incomplete}} = result
      assert_received {:synthetic_runner, ctx, _workspace}
      packet = run |> Path.join("guest-evidence.json") |> File.read!() |> Jason.decode!()
      assert %{"execution" => "completed", "evidence_complete" => false, "stores_verified" => true} = packet

      for {file, slot, _change} <- receipts do
        bytes = File.read!(Path.join(ctx.directory, file))
        assert File.read!(Path.join([run, "originals", file])) == bytes
        hash = Rehearsal.digest(bytes)
        assert packet["sealed_sha256"][file] == hash
        assert %{"kind" => "artifact", "name" => slot, "status" => ["ambiguous", "unconfirmed", hash]} in packet["observations"]
      end
    end
  end

  defp alter_synthetic_receipt(directory, {file, _slot, change}) do
    path = Path.join(directory, file)
    bytes = File.read!(path)

    changed =
      case change do
        fields when is_map(fields) -> bytes |> Jason.decode!() |> Map.merge(fields) |> Jason.encode!()
        :duplicate_binding -> ~s({"binding":"foreign-binding",) <> String.trim_leading(bytes, "{")
        malformed -> malformed
      end

    File.write!(path, changed)
  end

  test "a collection failure preserves completed execution as a separate fact", %{root: root} do
    use_synthetic_tracker_key()
    {run, staged} = stage_synthetic(root)
    assert :ok = Rehearsal.prepare(run, staged)
    host = identity("external-host")
    hash = approve(run, host)

    assert_raise ExUnit.AssertionError, fn ->
      Rehearsal.execute(run, staged, hash, host, fn ctx, opts ->
        assert :ok = synthetic_completion(ctx, opts)
        ready = Path.join(ctx.directory, "functional-ready.json")
        File.rename!(ready, ready <> ".unavailable")
      end)
    end

    assert_received {:synthetic_runner, ctx, _workspace}
    assert File.regular?(ctx.ledger.path)
    assert File.regular?(Path.join(ctx.directory, "provider-effects.journal"))
    refute File.exists?(Path.join(run, "guest-evidence.json"))

    failure = run |> Path.join("guest-failure.json") |> File.read!() |> Jason.decode!()
    assert %{"execution" => "completed", "evidence_complete" => false, "stores_verified" => false} = failure
  end

  defp use_synthetic_tracker_key do
    prior_key = System.get_env("PLANE_API_KEY")
    System.put_env("PLANE_API_KEY", "SYNTHETIC-NONLIVE-PLANE-KEY")
    on_exit(fn -> if prior_key, do: System.put_env("PLANE_API_KEY", prior_key), else: System.delete_env("PLANE_API_KEY") end)
  end

  test "checkout measurement refuses extra code paths and untracked checkout inputs", %{root: root} do
    checkout = Path.expand("..")
    assert %{"build_files" => count, "build_sha256" => hash} = Rehearsal.checkout_provenance(checkout)
    assert count > 0 and byte_size(hash) == 64
    path = String.to_charlist(root)
    assert true = :code.add_patha(path)

    try do
      assert_raise ExUnit.AssertionError, fn -> Rehearsal.checkout_provenance(checkout) end
    after
      :code.del_path(path)
    end

    stray = Path.join(checkout, "h100-untracked-#{System.unique_integer([:positive])}")
    assert :ok = File.write(stray, "unexpected", [:exclusive])

    try do
      assert_raise ExUnit.AssertionError, fn -> Rehearsal.checkout_provenance(checkout) end
    after
      File.rm!(stray)
    end
  end

  test "actual shared teardown retains rehearsal bytes after failure and removes the ordinary fixture", %{root: root} do
    for retention <- [:ordinary, :rehearsal] do
      path = Path.join(root, Atom.to_string(retention))
      marker = Path.join(path, "partial-original")

      {pid, monitor} =
        spawn_monitor(fn ->
          ExUnit.OnExitHandler.register(self())
          assert :ok = TestSupport.start_workflow_fixture(path, retention)
          assert :ok = File.write(marker, "original durable bytes")
          flunk("injected fixture assertion failure")
        end)

      assert_receive {:DOWN, ^monitor, :process, ^pid, {%ExUnit.AssertionError{}, _}}, 5_000
      assert :ok = ExUnit.OnExitHandler.run(pid, 5_000)

      case retention do
        :ordinary -> refute File.exists?(path)
        :rehearsal -> assert File.read!(marker) == "original durable bytes"
      end
    end
  end

  defp stage_synthetic(root) do
    run = Path.join(root, "run")
    File.mkdir!(run)
    File.chmod!(run, 0o700)
    native = Path.join(root, "native")

    for path <- ~w(tests/run_attempt.py tests/provider_fixture.py build/guard build/host build/holder-probe build/tool-broker build/request-effect) do
      file = Path.join(native, path)
      File.mkdir_p!(Path.dirname(file))
      File.write!(file, "synthetic " <> path)
    end

    for name <- ~w(holder catalog wrapper), do: File.write!(Path.join(root, name), name)

    {run, %{checkout: Path.expand(".."), holder: Path.join(root, "holder"), native: native, catalog: Path.join(root, "catalog"), wrapper: Path.join(root, "wrapper")}}
  end

  defp git_head(path), do: Rehearsal.git!(path, ["rev-parse", "HEAD"]) |> String.trim()

  defp synthetic_completion(ctx, opts) do
    assert {:ok, %{state: :consumed, grant: grant, runtime_identity: identity}} = AttemptLedger.pilot_status(ctx.ledger)

    assert {:ok, %{authority_fence: %{state: :bound, runtime_attempt: ^identity}}} =
             AttemptLedger.current(ctx.ledger, grant.work_item_id)

    assert :ok = AttemptLedger.claim_pilot_launch(ctx.ledger, grant, identity)
    attempt = identity.runtime_attempt_id
    binding = Rehearsal.digest("synthetic host binding")
    workspace = Path.join([ctx.root, "workspaces", "synthetic"])
    send(self(), {:synthetic_runner, ctx, workspace})
    File.mkdir_p!(workspace)
    File.mkdir_p!(ctx.directory)
    receipt = %{attempt: attempt, binding: binding, scope: "SYNTHETIC_PIPE"}
    ready = Map.merge(receipt, %{kind: "native-ready", sequence: 0})
    stop = Map.merge(receipt, %{kind: "native-stopped", sequence: 1})
    assert :ok = Rehearsal.record(ctx.directory, "functional-ready.json", ready)
    assert :ok = Rehearsal.record(ctx.directory, "functional-stop.json", stop)

    assert :ok =
             Rehearsal.record(ctx.directory, "routed-stop-observation.json", %{
               attempt: attempt,
               binding: binding,
               scope: "SYNTHETIC_PIPE",
               port_down_observed: true,
               pid1_stop_verified: true,
               namespace_pid1: %{pid: 2}
             })

    assert :ok =
             Rehearsal.record(ctx.directory, "functional-broker-stop.json", %{
               schema: "H100-HOST-BROKER-STOP-1",
               attempt: attempt,
               binding: binding,
               helper_stopped: true,
               tool_stopped: true
             })

    assert :ok =
             Rehearsal.record(ctx.directory, "schema2-input.json", %{
               context: %{
                 binding_id: binding,
                 attempt_id: attempt,
                 project_id: grant.project_id,
                 work_item_id: grant.work_item_id,
                 role: "Planner",
                 grant_id: Rehearsal.digest(:erlang.term_to_binary(grant, [:deterministic])),
                 source_commit: grant.source_commit,
                 source_tree: grant.source_tree,
                 configuration_digest: grant.config_identity
               }
             })

    session = {make_ref(), %{pilot_holder_context: %{digest: binding, binding: %{workspace: workspace}}}}
    assert {:ok, ^session} = Rehearsal.observe_session({:ok, session}, opts)
    assert :ok = synthetic_requests(grant, attempt, Path.join(ctx.directory, "provider-effects.journal"))

    result = %{
      outcome: :completed,
      model_state: :completed,
      stop_disposition: :verified,
      final_answer: "Synthetic only",
      session_id: "session-1",
      thread_id: "thread-1",
      turn_id: "turn-1"
    }

    assert :ok = AttemptLedger.persist_pilot_result(ctx.ledger, identity, result)
  end

  defp verify_negative_projections(ctx, workspace, packet) do
    readback = Rehearsal.fresh_rehearsal_status(ctx)
    assert %{pilot: pilot, current: current, closed?: true, records: [first, second]} = readback
    assert pilot.result.outcome == :completed
    assert current.authority_fence.state == :bound
    assert first.state == :terminal and second.state == :terminal
    assert second.prior_request_id == first.request_id

    route = Keyword.fetch!(ctx.opts, :route)
    project = fn binding -> Rehearsal.review_packet(ctx, route, pilot, current, binding, workspace, packet["sealed_sha256"]) end

    assert_raise ExUnit.AssertionError, fn -> project.(Rehearsal.digest("conflicting binding")) end

    ready = Path.join(ctx.directory, "functional-ready.json")
    bytes = File.read!(ready)
    File.rename!(ready, ready <> ".fixture")
    missing = project.(packet["binding"])
    refute missing.evidence_complete
    assert %{kind: :artifact, name: "native_ready", status: [:missing]} in missing.observations

    File.write!(ready, bytes <> "different")
    conflicting = project.(packet["binding"])
    refute conflicting.evidence_complete
    assert Enum.any?(conflicting.observations, &match?(%{name: "native_ready", status: [:ambiguous, :unconfirmed, _]}, &1))

    File.rename!(ready <> ".fixture", ready)
    File.ln_s!(workspace, Path.join(ctx.directory, "codex-home"))
    incomplete = project.(packet["binding"])
    refute incomplete.evidence_complete
    assert %{kind: :resource, name: "codex-home", status: [:ambiguous, :unconfirmed, nil]} in incomplete.observations
  end

  defp synthetic_requests(grant, attempt, path) do
    assert {:ok, journal} = RequestLedger.open(attempt, path: path)
    first = terminal_request(journal, request_attrs(grant, attempt, 1))

    next = %{
      prior_request_id: first.request_id,
      prior_response_id: "resp-1",
      tool_operation_id: "tool-op-1",
      tool_call_id: "call-1",
      tool_output_digest: Rehearsal.digest("fixture output"),
      tool_output_bytes: 14
    }

    terminal_request(journal, Map.merge(request_attrs(grant, attempt, 2), next))
    assert {:ok, _} = RequestLedger.close_admission(journal)
    :ok
  end

  defp terminal_request(journal, attrs) do
    assert {:ok, request} = RequestLedger.prepare(journal, attrs)
    id = request.request_id
    assert {:ok, _permit, _} = RequestLedger.acknowledge_possible_send(journal, id, request.revision)
    assert {:ok, _} = RequestLedger.record_observation(journal, id, :invocation_observed, %{})
    assert {:ok, _} = RequestLedger.record_observation(journal, id, :accepted, %{response_id: "resp-#{request.ordinal}"})

    assert {:ok, record} =
             RequestLedger.record_observation(journal, id, :terminal, %{
               terminal_kind: "response.completed",
               terminal_digest: Rehearsal.digest("terminal-#{request.ordinal}")
             })

    record
  end

  defp request_attrs(grant, attempt, ordinal) do
    Map.new(
      ordinal: ordinal,
      runtime_attempt_id: attempt,
      grant_id: Rehearsal.digest(:erlang.term_to_binary(grant, [:deterministic])),
      project_id: grant.project_id,
      item_id: grant.work_item_id,
      planning_role: "planner",
      source_digest: Rehearsal.digest("source"),
      config_digest: grant.config_identity,
      policy_digest: Rehearsal.digest("policy"),
      holder_digest: Rehearsal.digest("holder"),
      profile_id: "synthetic-planner",
      host_id: "host-1",
      boot_id: "boot-1",
      credential_generation: "fixture-gen-1",
      context_digest: Rehearsal.digest("context"),
      nonce: "frame-nonce-#{ordinal}",
      thread_id: "thread-1",
      turn_id: "turn-1",
      method: "POST",
      url: "https://api.openai.com/v1/responses",
      model: "synthetic-planner-v1",
      catalog_digest: Rehearsal.digest("catalog"),
      tool_digest: Rehearsal.digest("tool"),
      body_digest: Rehearsal.digest("body-#{ordinal}"),
      body_bytes: 128,
      content_type: "application/json",
      stream: true,
      store: false,
      parallel_tool_calls: false,
      permission_id: "permission-1",
      permission_generation: 1,
      lease_id: "lease-1",
      lease_generation: 1,
      deadline_monotonic_ms: System.monotonic_time(:millisecond) + 30_000
    )
  end
end
