if Mix.env() == :test do
  defmodule SymphonyElixir.AgentRuntime.ToolBinding do
    @moduledoc """
    Test-only host boundary for one P05 read. The private journal sits beside the
    synthetic attempt ledger. It records evidence and never writes that ledger.

    The slot directory is exclusive and permanent for the lifetime of the fixture.
    A synchronized bound record admits the original in-memory binding only. An
    exclusive, synchronized claim directory serializes contenders and survives
    decision-file creation failure. A persisted worker identity gates recovery.
    The deadline guards adapter entry and the acceptance decision after result
    sync. Once accepted in time, terminal audit can finish after the deadline.
    Recovery never restores authority or returns a projection.
    """

    alias SymphonyElixir.{AgentRunner, Config, PathSafety, Tracker, Workflow}
    alias SymphonyElixir.AgentRuntime.{AttemptLedger, Route}
    alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
    alias SymphonyElixir.Config.Schema
    alias SymphonyElixir.Plane.AgentTool
    alias SymphonyElixir.WorkControl.{ProviderObservation, ProviderProjectContract, WorkItem}

    @project "p05-fixture"
    @plane "f1050000-0000-4000-8000-000000000001"
    @item "f1050000-0000-4000-8000-000000000002"
    @workspace "f1050000-0000-4000-8000-000000000003"
    @tool "plane_get_current_work_item"
    @schema %{"type" => "object", "additionalProperties" => false, "properties" => %{}}
    @max_frame 8_192
    @max_result 4_096
    @faults [
      :none,
      :decision_open,
      :reservation_write,
      :reservation_sync,
      :crash_after_intent,
      :crash_after_dispatch,
      :lose_result
    ]
    @pause_phases [:after_read, :after_result_sync, :after_acceptance]
    @vm_key {__MODULE__, :fixture_vm}

    @enforce_keys [:fixture, :path, :owner, :request]
    defstruct @enforce_keys
    @opaque t :: %__MODULE__{fixture: map(), path: Path.t(), owner: pid(), request: map()}

    @doc "Binds a deliberately selected synthetic fixture and creates its durable slot."
    @spec bind(atom(), map()) :: {:ok, t()} | {:error, atom()}
    def bind(:p05_fixture, %{absolute_deadline_ms: deadline} = fixture) when is_integer(deadline) do
      with {:ok, authority} <- authority(fixture),
           true <- deadline > now() and deadline <= now() + fixture.grant.deadline_ms,
           {:ok, path} <- slot_path(fixture),
           :ok <- ensure_fixture_vm(),
           :ok <- create_slot(path) do
        request = build_request(authority, deadline)
        binding = %__MODULE__{fixture: fixture, path: path, owner: self(), request: request}

        case record(path, "bound", bound_record(binding)) do
          :ok -> {:ok, binding}
          _ -> {:error, :quarantined_consumed}
        end
      else
        {:error, :eexist} -> {:error, :slot_consumed}
        _ -> {:error, :binding_refused}
      end
    end

    def bind(_, _), do: {:error, :binding_refused}

    @doc "Returns the host-generated request. Thread and turn are explicitly absent."
    @spec request(t()) :: map()
    def request(%__MODULE__{request: request}), do: request

    @doc "Accepts one exact frame. Fault points are fixed synthetic persistence and process-loss tests."
    def invoke(binding, frame, fault \\ :none)

    @spec invoke(t(), binary(), atom() | {:pause, atom(), pid()}) :: {:ok, map()} | {:error, atom()}
    def invoke(%__MODULE__{} = binding, frame, fault) do
      with :ok <- validate_fault(fault),
           {:ok, path} when path == binding.path <- slot_path(binding.fixture),
           {:ok, ^path} <- canonical_private_directory(path),
           {:ok, claimed} <- claim_exists(path),
           false <- claimed,
           :ok <- validate_frame(frame, binding.request),
           {:ok, bound} <- read_record(path, "bound"),
           true <- bound == bound_record(binding),
           true <- Process.alive?(binding.owner) do
        decide(binding, fault)
      else
        true -> {:error, :slot_consumed}
        _ -> {:error, :request_refused}
      end
    end

    def invoke(_, _, _), do: {:error, :request_refused}

    @doc """
    Recovers a claimed slot only after observing the exact invocation worker stop.
    A foreign VM requires an already synchronized stop receipt. Never dispatches.
    """
    @spec recover(t() | map()) :: {:ok, atom()} | {:error, :unavailable}
    def recover(%__MODULE__{fixture: fixture}), do: recover(fixture)

    def recover(fixture) do
      with {:ok, path} <- slot_path(fixture),
           {:ok, ^path} <- canonical_private_directory(path),
           {:ok, %{"state" => "bound", "request" => request}} <- read_record(path, "bound"),
           %{"attempt" => attempt, "lineage" => lineage, "tool" => @tool, "request_id" => id} <- request,
           true <- attempt == fixture.identity.runtime_attempt_id and lineage == fixture.identity.lineage_generation do
        recover_slot(path, id, request["deadline_ms"])
      else
        _ -> {:error, :unavailable}
      end
    end

    defp recover_slot(path, id, deadline) do
      with {:ok, true} <- claim_exists(path),
           {:ok, worker} <- read_record(path, "worker"),
           :ok <- confirm_worker_stop(path, id, worker) do
        recover_decision(path, id, deadline)
      else
        {:ok, false} -> {:ok, :bound}
        {:error, :worker_active} -> {:ok, :worker_active}
        _ -> {:ok, :worker_state_uncertain}
      end
    end

    defp recover_decision(path, id, deadline) do
      case read_record(path, "decision") do
        {:ok, %{"request_id" => ^id, "state" => "refused_before_invocation"}} -> {:ok, :refused_before_invocation}
        {:ok, %{"request_id" => ^id, "state" => "intent_durable"}} -> recover_result(path, id, deadline)
        _ -> {:ok, :quarantined_consumed}
      end
    end

    defp recover_result(path, id, deadline) do
      with {:ok, %{"request_id" => ^id, "state" => "in_flight"}} <- read_record(path, "in-flight"),
           {:ok, row} <- read_record(path, "result"),
           %{"request_id" => ^id, "state" => "result_durable", "projection" => projection} <- row,
           :ok <- validate_projection(projection),
           {:ok, accepted} <- read_record(path, "accepted"),
           :ok <- validate_acceptance(accepted, id, deadline, row) do
        recover_accepted(path, accepted)
      else
        _ -> {:ok, :quarantined_consumed}
      end
    end

    defp recover_accepted(path, accepted) do
      with :ok <- sync_file(Path.join(path, "result.json")),
           :ok <- sync_file(Path.join(path, "accepted.json")),
           :ok <- sync_directory(path),
           :ok <- audit(path, accepted) do
        {:ok, :audited_terminal}
      else
        _ -> {:ok, :audit_pending}
      end
    end

    defp confirm_worker_stop(path, id, %{"request_id" => id, "vm" => vm, "pid" => pid} = worker)
         when is_binary(vm) and is_binary(pid) do
      receipt = Map.put(worker, "state", "worker_stopped")

      if vm == fixture_vm() do
        observe_local_stop(path, pid, receipt)
      else
        with {:ok, ^receipt} <- read_record(path, "worker-stopped"),
             :ok <- sync_file(Path.join(path, "worker-stopped.json")),
             do: sync_directory(path)
      end
    end

    defp confirm_worker_stop(_, _, _), do: {:error, :unconfirmed_worker}

    defp observe_local_stop(path, pid, receipt) do
      pid = :erlang.list_to_pid(to_charlist(pid))

      if Process.alive?(pid) do
        {:error, :worker_active}
      else
        persist_once(path, "worker-stopped", receipt)
      end
    rescue
      ArgumentError -> {:error, :unconfirmed_worker}
    end

    defp decide(binding, fault) do
      with :ok <- File.mkdir(Path.join(binding.path, "claim")),
           :ok <- sync_directory(binding.path),
           :ok <- record(binding.path, "worker", worker_identity(binding)) do
        case current_authority(binding) do
          {:ok, _authority} -> reserve(binding, fault)
          _ -> refuse_before_invocation(binding)
        end
      else
        {:error, :eexist} -> {:error, :slot_consumed}
        _ -> {:error, :quarantined_consumed}
      end
    end

    defp worker_identity(binding) do
      %{
        "request_id" => binding.request["request_id"],
        "vm" => fixture_vm(),
        "pid" => self() |> :erlang.pid_to_list() |> to_string()
      }
    end

    defp refuse_before_invocation(binding) do
      case record(binding.path, "decision", transition(binding, "refused_before_invocation")) do
        :ok -> {:error, :refused_before_invocation}
        {:error, :eexist} -> {:error, :slot_consumed}
        _ -> {:error, :quarantined_consumed}
      end
    end

    defp reserve(binding, fault) do
      case record(binding.path, "decision", transition(binding, "intent_durable"), fault) do
        :ok -> dispatch(binding, fault)
        {:error, :eexist} -> {:error, :slot_consumed}
        _ -> {:error, :quarantined_consumed}
      end
    end

    defp dispatch(binding, fault) do
      crash_at(fault, :crash_after_intent)

      with :ok <- record(binding.path, "in-flight", transition(binding, "in_flight")),
           {:ok, authority} <- current_authority(binding),
           {:ok, projection} <- selected_read(authority),
           :ok <- pause_at(fault, :after_read),
           :ok <- validate_projection(projection),
           true <- now() < binding.request["deadline_ms"] do
        crash_at(fault, :crash_after_dispatch)
        save_result(binding, projection, fault)
      else
        _ -> {:error, :quarantined_consumed}
      end
    end

    defp save_result(binding, projection, fault) do
      result = Map.put(transition(binding, "result_durable"), "projection", projection)

      with :ok <- record(binding.path, "result", result),
           :ok <- pause_at(fault, :after_result_sync) do
        complete_accepted_read(binding, result, projection, fault)
      else
        _ -> {:error, :quarantined_consumed}
      end
    end

    defp complete_accepted_read(binding, result, projection, fault) do
      accepted_at = now()

      if accepted_at < binding.request["deadline_ms"] do
        accepted =
          binding
          |> transition("accepted_before_deadline")
          |> Map.merge(%{"accepted_at_ms" => accepted_at, "result_digest" => digest(result)})

        with :ok <- record(binding.path, "accepted", accepted),
             :ok <- pause_at(fault, :after_acceptance),
             :ok <- crash_at(fault, :lose_result),
             :ok <- audit(binding.path, accepted) do
          {:ok, projection}
        else
          _ -> {:error, :audit_pending}
        end
      else
        {:error, :quarantined_consumed}
      end
    end

    defp validate_acceptance(
           %{"request_id" => id, "state" => "accepted_before_deadline", "accepted_at_ms" => at, "result_digest" => hash},
           id,
           deadline,
           result
         )
         when is_integer(at) and is_integer(deadline) and at < deadline do
      if hash == digest(result), do: :ok, else: {:error, :invalid_acceptance}
    end

    defp validate_acceptance(_, _, _, _), do: {:error, :invalid_acceptance}

    defp audit(path, accepted) do
      persist_once(path, "terminal", %{accepted | "state" => "audited_terminal"})
    end

    defp persist_once(path, name, row) do
      case record(path, name, row) do
        {:error, :eexist} ->
          with {:ok, ^row} <- read_record(path, name),
               :ok <- sync_file(Path.join(path, name <> ".json")),
               do: sync_directory(path)

        result ->
          result
      end
    end

    defp validate_fault(fault) when fault in @faults, do: :ok
    defp validate_fault({:pause, phase, observer}) when phase in @pause_phases and is_pid(observer), do: :ok
    defp validate_fault(_), do: {:error, :invalid_fault}

    defp pause_at({:pause, phase, observer}, phase) do
      send(observer, {:p05_paused, self(), phase})

      receive do
        {:p05_resume, ^phase} -> :ok
      after
        5_000 -> {:error, :fixture_pause_timeout}
      end
    end

    defp pause_at(_, _), do: :ok

    defp crash_at(point, point), do: Process.exit(self(), :kill)
    defp crash_at(_, _), do: :ok

    defp selected_read(%{route: route, item: item, contract: contract, identity: identity}) do
      # A concrete map unconditionally selects AgentTool's injected-context branch.
      context = %{work_item: item, provider_project_contract: contract, runtime_attempt_identity: identity}

      host_opts = [
        agent_tool_context: %{route: route, runtime_attempt_identity: identity},
        semantic_tool_context: context,
        tracker_settings: %{kind: "plane", workspace_id: @workspace, project_id: @plane}
      ]

      case AgentTool.execute("plane_get_current_work_item", %{}, host_opts) do
        %{"success" => true, "output" => output} when is_binary(output) and byte_size(output) <= @max_result ->
          Jason.decode(output)

        _ ->
          {:error, :invalid_projection}
      end
    rescue
      _ -> {:error, :invalid_projection}
    end

    defp validate_projection(
           %{
             "workItemId" => @item,
             "identifier" => identifier,
             "title" => title,
             "canonicalLifecycleState" => "planning",
             "dependencyCompleteness" => "complete",
             "providerObservation" =>
               %{
                 "stateName" => "Planning",
                 "observedAt" => observed,
                 "providerUpdatedAt" => updated
               } = observation
           } = result
         )
         when map_size(result) == 6 and map_size(observation) == 3 and
                is_binary(identifier) and is_binary(title) and is_binary(observed) do
      with {:ok, _, _} <- DateTime.from_iso8601(observed),
           true <- valid_updated_at?(updated),
           {:ok, bytes} when byte_size(bytes) <= @max_result <- Jason.encode(result) do
        :ok
      else
        _ -> {:error, :invalid_projection}
      end
    end

    defp validate_projection(_), do: {:error, :invalid_projection}

    defp valid_updated_at?(nil), do: true
    defp valid_updated_at?(value) when is_binary(value), do: match?({:ok, _, _}, DateTime.from_iso8601(value))
    defp valid_updated_at?(_), do: false

    defp current_authority(binding) do
      with %{"deadline_ms" => deadline} <- binding.request,
           true <- deadline == binding.fixture.absolute_deadline_ms and now() < deadline,
           {:ok, authority} <- authority(binding.fixture),
           true <- authority_fields(authority) == Map.drop(binding.request, ~w(request_id deadline_ms)),
           true <- now() < deadline do
        {:ok, authority}
      else
        _ -> {:error, :binding_refused}
      end
    end

    defp authority(
           %{
             ledger: %AttemptLedger{project_id: @project} = ledger,
             grant: grant,
             identity: %Identity{} = identity,
             route: %Route{} = route,
             item: %WorkItem{} = item,
             source: source
           } = fixture
         ) do
      # The store may retain its previous settings after a rejected reload.
      with {:ok, %{config: config, prompt_template: prompt}} <- Workflow.load(),
           {:ok, settings} <- Schema.parse(config),
           :ok <- fixture_settings(settings, ledger),
           {:ok, ^grant} <- Config.pilot_binding(settings, prompt),
           :ok <- fixture_item(item, route, settings),
           {:ok, snapshot} <- Config.pilot_configuration_snapshot(settings, prompt),
           true <- snapshot.identity == grant.config_identity,
           true <- snapshot.role_policy.profile_name == route.profile_name,
           true <- source == Path.join(Path.dirname(ledger.path), "checkout"),
           :ok <- AgentRunner.validate_pilot_checkout(source, grant, snapshot.git),
           {:ok, catalog} <- catalog(route),
           :ok <- attempt_authority(ledger, grant, identity, route) do
        authority = %{
          grant: grant,
          identity: identity,
          route: route,
          item: item,
          source: fixture.source,
          policy: snapshot.role_policy,
          contract: settings.provider_project_contract,
          catalog: catalog
        }

        {:ok, authority}
      else
        _ -> {:error, :binding_refused}
      end
    end

    defp authority(_), do: {:error, :binding_refused}

    defp fixture_settings(
           %{
             symphony: %{project_id: @project},
             tracker: %{kind: "plane", api_key: "P05-FIXTURE-NONSECRET", workspace_id: @workspace, project_id: @plane},
             provider_project_contract: %ProviderProjectContract{
               provider: :plane,
               workspace_id: @workspace,
               project_id: @plane
             }
           } = settings,
           ledger
         ) do
      if ledger.tracker_identity == Tracker.identity(settings.tracker), do: :ok, else: {:error, :wrong_fixture}
    end

    defp fixture_settings(_, _), do: {:error, :wrong_fixture}

    defp attempt_authority(
           ledger,
           %{project_id: @project, plane_project_id: @plane, work_item_id: @item} = grant,
           identity,
           route
         ) do
      fence = %{state: :bound, runtime_attempt: identity, route_fingerprint: route.fingerprint}

      lineage = grant.runtime_lineage
      expected_pilot = %{state: :running, grant: grant, runtime_identity: identity, result: nil}

      with true <- Identity.valid?(identity) and identity.work_item_id == @item,
           true <- identity.lineage_generation == lineage,
           true <- identity.responsibility == route.responsibility and identity.runtime_profile == route.profile_name,
           {:ok, ^expected_pilot} <- AttemptLedger.pilot_status(ledger),
           {:ok, %{lineage_id: ^lineage, authority_fence: ^fence}} <- AttemptLedger.current(ledger, @item) do
        :ok
      else
        _ -> {:error, :stale_attempt}
      end
    end

    defp attempt_authority(_, _, _, _), do: {:error, :stale_attempt}

    defp fixture_item(
           %WorkItem{
             id: @item,
             validated_lifecycle_state: state,
             provider_observation: %ProviderObservation{
               provider: :plane,
               work_item_id: @item,
               workspace_id: @workspace,
               project_id: @plane,
               presence: :present,
               observed_at: %DateTime{} = observed
             }
           },
           %Route{
             issue_id: @item,
             starting_state: "planning",
             responsibility: "planning",
             profile_name: "planner"
           } = route,
           settings
         )
         when state in ["planning", :planning] do
      valid =
        route.profile == settings.agent.profiles["planner"] and route.fingerprint == Route.fingerprint(route) and
          route.starting_state_fingerprint == Route.starting_state_fingerprint(route) and
          DateTime.diff(DateTime.utc_now(), observed, :millisecond) in 0..120_000

      if valid, do: :ok, else: {:error, :invalid_fixture_item}
    end

    defp fixture_item(_, _, _), do: {:error, :invalid_fixture_item}

    defp catalog(route) do
      case Enum.filter(AgentTool.agent_tool_specs(%{route: route}), &(&1["name"] == @tool)) do
        [%{"inputSchema" => @schema} = spec] -> {:ok, digest(spec)}
        _ -> {:error, :catalog_mismatch}
      end
    end

    defp build_request(authority, deadline) do
      Map.merge(authority_fields(authority), %{
        "request_id" => Base.url_encode64(:crypto.strong_rand_bytes(16), padding: false),
        "deadline_ms" => deadline
      })
    end

    defp authority_fields(authority) do
      context = {authority.item, authority.route, authority.contract, authority.identity, authority.source}

      %{
        "version" => 1,
        "grant" => digest(authority.grant),
        "attempt" => authority.identity.runtime_attempt_id,
        "lineage" => authority.identity.lineage_generation,
        "project" => @plane,
        "work_item" => @item,
        "role" => "planning",
        "starting_state" => "planning",
        "configuration" => authority.grant.config_identity,
        "policy" => digest(authority.policy),
        "source_commit" => authority.grant.source_commit,
        "source_tree" => authority.grant.source_tree,
        "fixture_context" => digest(context),
        "observation" => digest(authority.item.provider_observation),
        "catalog" => authority.catalog,
        "thread" => "NOT_APPLICABLE",
        "turn" => "NOT_APPLICABLE",
        "tool" => @tool,
        "args" => %{}
      }
    end

    defp validate_frame(frame, expected) when is_binary(frame) and byte_size(frame) <= @max_frame do
      with {:ok, %Jason.OrderedObject{values: pairs}} <- Jason.decode(frame, objects: :ordered_objects),
           true <- length(pairs) == map_size(expected),
           shaped <-
             Enum.map(pairs, fn
               {"args", %Jason.OrderedObject{values: []}} -> {"args", %{}}
               pair -> pair
             end),
           true <- Map.new(shaped) == expected do
        :ok
      else
        _ -> {:error, :request_refused}
      end
    end

    defp validate_frame(_, _), do: {:error, :request_refused}

    defp slot_path(%{ledger: %AttemptLedger{path: ledger_path, project_id: @project}, identity: %Identity{} = identity})
         when is_binary(ledger_path) do
      parent = Path.dirname(ledger_path)

      with true <- parent == Path.dirname(Workflow.workflow_file_path()),
           {:ok, ^parent} <- canonical_private_directory(parent),
           {:ok, %File.Stat{type: :regular, uid: uid}} <- File.lstat(ledger_path),
           {:ok, %File.Stat{uid: ^uid}} <- File.lstat(parent),
           true <- Path.basename(ledger_path) == @project <> ".dets" do
        slot = digest({@tool, identity.runtime_attempt_id, identity.lineage_generation})
        {:ok, Path.join(parent, "p05-" <> slot)}
      else
        _ -> {:error, :invalid_journal_root}
      end
    end

    defp slot_path(_), do: {:error, :invalid_journal_root}

    defp canonical_private_directory(path) do
      with {:ok, ^path} <- PathSafety.canonicalize(path),
           {:ok, %File.Stat{type: :directory, mode: mode}} <- File.lstat(path),
           true <- Bitwise.band(mode, 0o777) == 0o700 do
        {:ok, path}
      else
        _ -> {:error, :invalid_journal_root}
      end
    end

    defp create_slot(path) do
      with :ok <- File.mkdir(path),
           :ok <- File.chmod(path, 0o700),
           {:ok, ^path} <- canonical_private_directory(path),
           do: sync_directory(Path.dirname(path))
    end

    defp bound_record(binding) do
      %{"state" => "bound", "owner" => digest({fixture_vm(), binding.owner}), "request" => binding.request}
    end

    defp transition(binding, state), do: %{"request_id" => binding.request["request_id"], "state" => state}

    defp claim_exists(path) do
      case File.lstat(Path.join(path, "claim")) do
        {:ok, %File.Stat{type: :directory}} -> {:ok, true}
        {:error, :enoent} -> {:ok, false}
        _ -> {:error, :unconfirmed_claim}
      end
    end

    defp read_record(path, name) do
      file = Path.join(path, name <> ".json")

      with {:ok, %File.Stat{type: :regular, size: size}} when size <= @max_frame <- File.lstat(file),
           {:ok, bytes} when byte_size(bytes) <= @max_frame <- File.read(file) do
        Jason.decode(bytes)
      else
        {:error, _} = error -> error
        _ -> {:error, :invalid_record}
      end
    end

    defp record(path, name, row, fault \\ :none)

    defp record(_path, "decision", _row, :decision_open), do: {:error, :injected_open_failure}

    defp record(path, name, row, fault) do
      file = Path.join(path, name <> ".json")

      with {:ok, bytes} <- Jason.encode(row),
           {:ok, io} <- :file.open(to_charlist(file), [:write, :raw, :binary, :exclusive]) do
        result =
          with :ok <- File.chmod(file, 0o600),
               :ok <- persist(io, bytes, fault),
               do: sync_directory(path)

        close = :file.close(io)
        if result == :ok, do: close, else: result
      end
    end

    defp persist(_io, _bytes, :reservation_write), do: {:error, :injected_write_failure}

    defp persist(io, bytes, fault) do
      with :ok <- :file.write(io, bytes) do
        if fault == :reservation_sync, do: {:error, :injected_sync_failure}, else: :file.sync(io)
      end
    end

    defp sync_file(path), do: sync_path(path, [:read, :raw])
    defp sync_directory(path), do: sync_path(path, [:read, :raw, :directory])

    defp sync_path(path, modes) do
      with {:ok, io} <- :file.open(to_charlist(path), modes) do
        result = :file.sync(io)
        close = :file.close(io)
        if result == :ok, do: close, else: result
      end
    end

    defp ensure_fixture_vm do
      :global.trans(
        {@vm_key, self()},
        fn ->
          if is_nil(fixture_vm()) do
            :persistent_term.put(@vm_key, Base.encode16(:crypto.strong_rand_bytes(16), case: :lower))
          end

          :ok
        end,
        [node()]
      )
    end

    defp fixture_vm, do: :persistent_term.get(@vm_key, nil)
    defp now, do: System.monotonic_time(:millisecond)

    defp digest(value) do
      bytes = :erlang.term_to_binary(value, [:deterministic])
      :sha256 |> :crypto.hash(bytes) |> Base.encode16(case: :lower)
    end
  end
end
