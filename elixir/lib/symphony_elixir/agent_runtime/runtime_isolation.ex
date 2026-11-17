defmodule SymphonyElixir.AgentRuntime.RuntimeIsolation do
  @moduledoc """
  Serializes and caches real Codex isolation verification by runtime fingerprint.
  """

  use GenServer

  alias SymphonyElixir.{AgentRunner, Config, PathSafety, Workflow}
  alias SymphonyElixir.AgentRuntime.AttemptLedger
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.Codex.IsolationProfile

  @type evidence :: %{
          status: :verifying | :verified | :failed | :stale,
          fingerprint: String.t(),
          executable: Path.t(),
          version: String.t(),
          platform: term(),
          result: term()
        }

  @pilot_holder_test_build Code.ensure_loaded?(Mix) and Mix.env() == :test

  @doc "Operational dependencies for the opt-in C02 profile. No fixture promotes these states."
  @spec pilot_holder_dependencies() :: %{String.t() => atom()}
  def pilot_holder_dependencies do
    %{
      "P01" => :dormant_no_live_permission,
      "P02" => :pilot_storage_unqualified,
      "P03" => :credential_owner_unavailable,
      "P04" => :qualified_holder_unavailable,
      "P05" => :qualified_tool_boundary_unavailable,
      "P08" => :authoritative_disposal_unavailable
    }
  end

  @doc """
  Prepares only the nonsecret pilot interface. Production always refuses while
  the native dependencies are unavailable; no credential or native API exists
  here. Test builds may exercise a pinned synthetic peer and signed receipts.
  Its journal is test evidence, never operational materialization qualification.
  """
  @spec prepare_pilot_holder(Path.t(), keyword()) :: {:ok, map() | nil} | {:error, atom()}
  def prepare_pilot_holder(workspace, opts) do
    with {:ok, settings} <- Config.settings(),
         {:ok, selection} <- Config.pilot_holder_selection(settings) do
      prepare_selected_pilot_holder(selection, settings, workspace, opts)
    else
      _ -> {:error, :pilot_holder_binding_invalid}
    end
  rescue
    _ -> {:error, :pilot_holder_binding_invalid}
  end

  defp prepare_selected_pilot_holder(nil, _settings, _workspace, _opts), do: {:ok, nil}

  if @pilot_holder_test_build do
    defp prepare_selected_pilot_holder(selection, settings, workspace, opts) do
      with {:ok, binding} <- pilot_holder_binding(settings, workspace, opts, selection),
           {:ok, peer} <- synthetic_pilot_peer(opts),
           {:ok, receipt} <- synthetic_pilot_receipt(peer, :launch, binding, nil) do
        {:ok, %{assurance: :synthetic_test_only, binding: binding, receipt: receipt, peer: peer, opts: opts}}
      end
    end
  else
    defp prepare_selected_pilot_holder(selection, settings, workspace, opts) do
      with {:ok, _binding} <- pilot_holder_binding(settings, workspace, opts, selection) do
        {:error, :pilot_holder_boundary_unavailable}
      end
    end
  end

  @doc """
  Rechecks current authority before thread/turn use. Disposal uses the original
  binding so revoked forward authority cannot prevent bounded cleanup. A fresh
  signed challenge is mandatory; caller-provided receipt maps are never accepted.
  Failure returns only a stable nonsecret code and cannot rearm C01.
  """
  @spec check_pilot_holder(map() | nil, :thread | :turn | :cleanup) :: :ok | {:error, atom()}
  def check_pilot_holder(nil, _phase) do
    case Config.settings() do
      {:ok, settings} ->
        case Config.pilot_holder_selection(settings) do
          {:ok, nil} -> :ok
          _ -> {:error, :pilot_holder_binding_invalid}
        end

      _ ->
        {:error, :pilot_holder_binding_invalid}
    end
  end

  if @pilot_holder_test_build do
    def check_pilot_holder(%{assurance: :synthetic_test_only, binding: binding, peer: peer, receipt: receipt, opts: opts}, phase)
        when phase in [:thread, :turn, :cleanup] do
      with {:ok, ^peer} <- synthetic_pilot_peer(opts),
           :ok <- current_pilot_holder_binding(binding, opts, phase),
           {:ok, _receipt} <- synthetic_pilot_receipt(peer, phase, binding, receipt) do
        :ok
      end
    rescue
      _ -> {:error, :pilot_holder_binding_invalid}
    end
  else
    def check_pilot_holder(%{assurance: :synthetic_test_only}, _phase),
      do: {:error, :pilot_holder_boundary_unavailable}
  end

  def check_pilot_holder(_context, _phase), do: {:error, :pilot_holder_binding_invalid}

  defp pilot_holder_binding(settings, workspace, opts, selection) do
    grant = Keyword.get(opts, :pilot_binding)
    identity = Keyword.get(opts, :runtime_attempt_identity)
    issue = Keyword.get(opts, :runtime_issue)
    deadline = Keyword.get(opts, :absolute_deadline_ms)
    profile = Keyword.get(opts, :profile)
    now = System.monotonic_time(:millisecond)

    with {:ok, ^grant} when is_map(grant) <- Config.pilot_binding(settings),
         %Identity{} <- identity,
         true <- Identity.valid?(identity) and identity.responsibility == "planning",
         true <- identity.work_item_id == grant.work_item_id and identity.runtime_profile == profile.name,
         true <- profile == settings.agent.profiles[identity.runtime_profile],
         true <- profile.responsibility == "planning" and is_nil(Keyword.get(opts, :worker_host)),
         true <- Keyword.get(opts, :command, settings.codex.command) == profile.command,
         true <- Keyword.get(opts, :model) == profile.model,
         true <- issue.id == grant.work_item_id and issue.project_id == grant.plane_project_id,
         true <- is_integer(deadline) and deadline > now and deadline <= now + grant.deadline_ms,
         true <- selection["lifetime_budget"]["maximum_attempt_wall_time_ms"] == grant.deadline_ms,
         {:ok, %{state: :running, grant: ^grant, runtime_identity: ^identity}} <-
           AttemptLedger.pilot_status(Keyword.get(opts, :attempt_ledger)),
         {:ok, authority} <- Config.pilot_configuration_snapshot(settings, pilot_workflow_prompt()),
         true <- authority.identity == grant.config_identity and authority.role_policy.profile_name == profile.name,
         :ok <- AgentRunner.validate_pilot_checkout(workspace, grant, authority.git),
         {:ok, canonical} <- PathSafety.canonicalize(workspace) do
      {:ok,
       %{
         grant: grant,
         attempt: Map.from_struct(identity),
         profile: Map.from_struct(profile),
         selection: selection,
         workspace: canonical,
         absolute_deadline_ms: deadline
       }}
    else
      _ -> {:error, :pilot_holder_binding_invalid}
    end
  rescue
    _ -> {:error, :pilot_holder_binding_invalid}
  end

  defp pilot_workflow_prompt do
    {:ok, %{prompt_template: prompt}} = Workflow.load()
    prompt
  end

  if @pilot_holder_test_build do
    @pilot_receipt_keys ~w(schema phase binding challenge holder_ref durable_ref access_expires_ms lease_expires_ms disposition)

    defp current_pilot_holder_binding(_binding, _opts, :cleanup), do: :ok

    defp current_pilot_holder_binding(binding, opts, _phase) do
      with {:ok, settings} <- Config.settings(),
           {:ok, selection} when is_map(selection) <- Config.pilot_holder_selection(settings),
           {:ok, ^binding} <- pilot_holder_binding(settings, binding.workspace, opts, selection) do
        :ok
      else
        _ -> {:error, :pilot_holder_binding_invalid}
      end
    end

    defp synthetic_pilot_peer(opts) do
      # This is deliberately not an operational boundary adapter. A production
      # implementation requires separate native qualification and review.
      with true <- test_environment?(),
           {pid, public_key} = peer when is_pid(pid) and is_binary(public_key) and byte_size(public_key) == 32 <-
             Keyword.get(opts, :test_pilot_holder_peer),
           ^peer <- Application.get_env(:symphony_elixir, :test_pilot_holder_peer) do
        {:ok, peer}
      else
        _ -> {:error, :pilot_holder_boundary_unavailable}
      end
    end

    defp synthetic_pilot_receipt({pid, public_key}, phase, binding, prior) do
      remaining = binding.absolute_deadline_ms - System.monotonic_time(:millisecond)
      challenge = :crypto.strong_rand_bytes(32)

      if remaining > 0 do
        response = GenServer.call(pid, {:pilot_holder_receipt, phase, binding, challenge}, min(remaining, 5_000))

        if System.monotonic_time(:millisecond) < binding.absolute_deadline_ms do
          validate_synthetic_pilot_receipt(response, public_key, phase, binding, challenge, prior)
        else
          {:error, :pilot_holder_receipt_refused}
        end
      else
        {:error, :pilot_holder_receipt_refused}
      end
    catch
      _kind, _reason -> {:error, :pilot_holder_receipt_refused}
    end

    defp validate_synthetic_pilot_receipt({:synthetic_receipt, payload, signature}, public_key, phase, binding, challenge, prior)
         when is_map(payload) and is_binary(signature) do
      bytes = :erlang.term_to_binary(payload, [:deterministic])

      valid? =
        pilot_receipt_signature?(payload, bytes, signature, public_key) and
          pilot_receipt_binding?(payload, phase, binding, challenge) and
          pilot_receipt_lifetime?(payload, phase, binding, prior)

      if valid?, do: {:ok, payload}, else: {:error, :pilot_holder_receipt_refused}
    rescue
      _ -> {:error, :pilot_holder_receipt_refused}
    end

    defp validate_synthetic_pilot_receipt(_response, _key, _phase, _binding, _challenge, _prior), do: {:error, :pilot_holder_receipt_refused}

    defp pilot_receipt_signature?(payload, bytes, signature, public_key) do
      byte_size(bytes) <= 16_384 and byte_size(signature) == 64 and
        Enum.sort(Map.keys(payload)) == Enum.sort(@pilot_receipt_keys) and
        :crypto.verify(:eddsa, :none, bytes, signature, [public_key, :ed25519])
    end

    defp pilot_receipt_binding?(payload, phase, binding, challenge) do
      payload["schema"] == "C02-SYNTHETIC-RECEIPT-1" and payload["phase"] == Atom.to_string(phase) and
        payload["binding"] == binding and payload["challenge"] == challenge and
        pilot_receipt_reference?(payload["holder_ref"]) and pilot_receipt_reference?(payload["durable_ref"]) and
        payload["disposition"] == if(phase == :cleanup, do: "disposed", else: "ready")
    end

    defp pilot_receipt_lifetime?(receipt, phase, binding, prior) do
      same_holder? = is_nil(prior) or Enum.all?(~w(holder_ref access_expires_ms lease_expires_ms), &(receipt[&1] == prior[&1]))
      budget = binding.selection["lifetime_budget"]
      required_expiry = binding.absolute_deadline_ms + Enum.sum(Map.values(budget)) - budget["maximum_attempt_wall_time_ms"]

      same_holder? and is_integer(receipt["access_expires_ms"]) and is_integer(receipt["lease_expires_ms"]) and
        (phase == :cleanup or
           (receipt["access_expires_ms"] >= required_expiry and
              receipt["lease_expires_ms"] >= binding.absolute_deadline_ms))
    end

    defp pilot_receipt_reference?(value), do: is_binary(value) and Regex.match?(~r/\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\z/, value)
  end

  @spec child_spec(keyword()) :: Supervisor.child_spec()
  def child_spec(opts) do
    %{
      id: Keyword.get(opts, :name, __MODULE__),
      start: {__MODULE__, :start_link, [opts]},
      type: :worker
    }
  end

  @spec start_link(keyword()) :: GenServer.on_start()
  def start_link(opts \\ []) do
    name = Keyword.get(opts, :name)

    if is_atom(name) do
      GenServer.start_link(__MODULE__, opts, name: name)
    else
      GenServer.start_link(__MODULE__, opts)
    end
  end

  @spec admit(String.t() | nil, Path.t(), keyword()) ::
          {:ok, evidence()} | {:error, term()}
  def admit(worker_host, _executable, _opts) when is_binary(worker_host) do
    {:error, {:runtime_isolation_unavailable, :remote_containment_unproven}}
  end

  def admit(nil, executable, opts) do
    case admission_server(opts) do
      {:ok, server} -> verify(executable, Keyword.put(opts, :server, server))
      :error -> {:error, {:runtime_isolation_unavailable, :verifier_unavailable}}
    end
  end

  @spec verify(Path.t(), keyword()) :: {:ok, evidence()} | {:error, term()}
  def verify(executable, opts \\ []) when is_binary(executable) do
    server = Keyword.get(opts, :server, __MODULE__)

    with {:ok, identity} <- IsolationProfile.runtime_identity(executable),
         {:ok, server} <- ensure_server(server) do
      try do
        GenServer.call(server, {:verify, identity}, :infinity)
      catch
        :exit, _reason -> {:error, {:runtime_isolation_unavailable, :verifier_unavailable}}
      end
    end
  end

  @spec evidence(Path.t(), keyword()) :: evidence() | nil | {:error, term()}
  def evidence(executable, opts \\ []) when is_binary(executable) do
    server = Keyword.get(opts, :server, __MODULE__)

    with {:ok, identity} <- IsolationProfile.runtime_identity(executable),
         {:ok, server} <- ensure_server(server) do
      GenServer.call(server, {:evidence, fingerprint(identity)})
    end
  end

  @spec clear(keyword()) :: :ok
  def clear(opts \\ []) do
    server = Keyword.get(opts, :server, __MODULE__)

    with {:ok, server} <- ensure_server(server) do
      GenServer.call(server, :clear)
    end
  end

  @impl true
  def init(opts) do
    {:ok,
     %{
       records: %{},
       current_by_path: %{},
       probe: Keyword.get(opts, :probe, &default_probe/1)
     }}
  end

  @impl true
  def handle_call({:verify, identity}, _from, state) do
    fingerprint = fingerprint(identity)
    path = identity.executable

    state = mark_previous_fingerprint_stale(state, path, fingerprint)

    case Map.get(state.records, fingerprint) do
      %{status: :verified} = evidence ->
        {:reply, {:ok, evidence}, state}

      %{status: :failed, result: reason} ->
        {:reply, {:error, {:runtime_isolation_failed, reason}}, state}

      _missing_or_stale ->
        verifying = base_evidence(identity, fingerprint, :verifying, :verifying)
        state = %{state | records: Map.put(state.records, fingerprint, verifying)}
        result = run_probe(state.probe, identity)
        evidence = build_evidence(identity, fingerprint, result)

        next_state = %{
          state
          | records: Map.put(state.records, fingerprint, evidence),
            current_by_path: Map.put(state.current_by_path, path, fingerprint)
        }

        case evidence.status do
          :verified -> {:reply, {:ok, evidence}, next_state}
          :failed -> {:reply, {:error, {:runtime_isolation_failed, evidence.result}}, next_state}
        end
    end
  end

  def handle_call({:evidence, fingerprint}, _from, state) do
    {:reply, Map.get(state.records, fingerprint), state}
  end

  def handle_call(:clear, _from, state) do
    {:reply, :ok, %{state | records: %{}, current_by_path: %{}}}
  end

  defp ensure_server(server) when is_pid(server), do: {:ok, server}

  defp ensure_server(server) when is_atom(server) do
    case Process.whereis(server) do
      pid when is_pid(pid) ->
        {:ok, pid}

      nil ->
        case GenServer.start(__MODULE__, [], name: server) do
          {:ok, pid} -> {:ok, pid}
          {:error, {:already_started, pid}} -> {:ok, pid}
          {:error, reason} -> {:error, {:runtime_isolation_unavailable, {:verifier_start_failed, reason}}}
        end
    end
  end

  defp registered_server(server) when is_pid(server) do
    if Process.alive?(server), do: {:ok, server}, else: :error
  end

  defp registered_server(server) when is_atom(server) do
    case Process.whereis(server) do
      pid when is_pid(pid) -> {:ok, pid}
      nil -> :error
    end
  end

  defp registered_server(_server), do: :error

  defp admission_server(opts) do
    if test_environment?() and Keyword.has_key?(opts, :server) do
      registered_server(Keyword.get(opts, :server))
    else
      supervised_server()
    end
  end

  defp supervised_server do
    with supervisor when is_pid(supervisor) <- Process.whereis(SymphonyElixir.Supervisor),
         {__MODULE__, child_pid, _type, _modules} <-
           Enum.find(Supervisor.which_children(supervisor), fn
             {__MODULE__, pid, _type, _modules} when is_pid(pid) -> true
             _child -> false
           end),
         ^child_pid <- Process.whereis(__MODULE__) do
      {:ok, child_pid}
    else
      _ -> :error
    end
  catch
    :exit, _reason -> :error
  end

  defp test_environment? do
    Code.ensure_loaded?(Mix) and function_exported?(Mix, :env, 0) and Mix.env() == :test
  rescue
    _reason -> false
  end

  defp mark_previous_fingerprint_stale(state, path, fingerprint) do
    case Map.get(state.current_by_path, path) do
      nil ->
        state

      ^fingerprint ->
        state

      previous_fingerprint ->
        records =
          case Map.get(state.records, previous_fingerprint) do
            nil -> state.records
            previous -> Map.put(state.records, previous_fingerprint, %{previous | status: :stale})
          end

        %{state | records: records}
    end
  end

  defp run_probe(probe, identity) when is_function(probe, 1) do
    case probe.(identity) do
      :ok -> :ok
      {:ok, result} -> {:ok, result}
      {:error, reason} -> {:error, safe_reason(reason)}
      _other -> {:error, :invalid_probe_result}
    end
  rescue
    _error -> {:error, :probe_raised}
  catch
    _kind, _reason -> {:error, :probe_failed}
  end

  defp default_probe(identity) do
    IsolationProfile.run_actual_probe(identity.executable, identity.native_executable)
  end

  defp build_evidence(identity, fingerprint, :ok) do
    base_evidence(identity, fingerprint, :verified, :verified)
  end

  defp build_evidence(identity, fingerprint, {:ok, result}) do
    base_evidence(identity, fingerprint, :verified, sanitize_probe_result(result))
  end

  defp build_evidence(identity, fingerprint, {:error, reason}) do
    base_evidence(identity, fingerprint, :failed, safe_reason(reason))
  end

  defp base_evidence(identity, fingerprint, status, result) do
    %{
      status: status,
      fingerprint: fingerprint,
      executable: identity.executable,
      version: identity.version,
      platform: identity.platform,
      result: result
    }
  end

  defp sanitize_probe_result(result) when is_map(result) do
    Map.take(result, [:read_only, :reviewer_read, :workspace_write, :fixer_write, :platform])
  end

  defp sanitize_probe_result(_result), do: :verified

  defp safe_reason(reason) when is_atom(reason), do: reason

  defp safe_reason({tag, detail}) when is_atom(tag) and is_atom(detail), do: {tag, detail}

  defp safe_reason({tag, access, result, process_mismatch})
       when is_atom(tag) and is_atom(access) and is_map(result) and is_boolean(process_mismatch),
       do: {tag, access, result, process_mismatch}

  defp safe_reason(_reason), do: :probe_failed

  defp fingerprint(identity) do
    identity
    |> Map.take([
      :executable,
      :native_executable,
      :size,
      :mtime,
      :inode,
      :digest,
      :native_size,
      :native_mtime,
      :native_inode,
      :native_digest,
      :version,
      :platform
    ])
    |> :erlang.term_to_binary()
    |> then(&:crypto.hash(:sha256, &1))
    |> Base.encode16(case: :lower)
  end
end
