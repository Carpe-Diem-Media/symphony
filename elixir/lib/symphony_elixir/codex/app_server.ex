defmodule SymphonyElixir.Codex.AppServer do
  @moduledoc """
  Minimal client for the Codex app-server JSON-RPC 2.0 stream over stdio.
  """

  require Logger
  alias SymphonyElixir.AgentRuntime.{NativePilot, RuntimeIsolation}
  alias SymphonyElixir.Codex.DynamicTool
  alias SymphonyElixir.Codex.IsolationProfile
  alias SymphonyElixir.{Config, CredentialBoundary, PathSafety, SSH, Workspace}
  alias SymphonyElixir.Workspace.OwnershipLedger

  @initialize_id 1
  @thread_start_id 2
  @turn_start_id 3
  @port_line_bytes 1_048_576
  @max_stream_log_bytes 1_000
  @stop_poll_interval_ms 10
  @stop_poll_attempts 20
  @port_monitor_timeout_ms 5_000
  @routed_stop_token <<0, "SYMPHONY_STOP", "\n">>
  @linux_guard_stop_timeout_ms 5_000
  @functional_test_build Code.ensure_loaded?(Mix) and Mix.env() == :test

  @linux_runtime_guard_script ~S"""
  import ctypes, errno, json, os, selectors, signal, sys, time

  stop_token = b"\x00SYMPHONY_STOP\n"
  path, *runtime_args = sys.argv[1:]

  child_input, parent_input = os.pipe()
  parent_output, child_output = os.pipe()
  child = os.fork()

  if child == 0:
      try:
          os.dup2(child_input, 0)
          os.dup2(child_output, 1)
          os.dup2(child_output, 2)
          for descriptor in (child_input, parent_input, parent_output, child_output):
              if descriptor > 2:
                  os.close(descriptor)
          os.execve(path, [path, *runtime_args], os.environ)
      except BaseException as error:
          os.write(2, ("symphony runtime guard: runtime exec failed: " + type(error).__name__ + "\n").encode())
          os._exit(126)

  os.close(child_input)
  os.close(child_output)
  signal.signal(signal.SIGTERM, lambda _signum, _frame: None)
  signal.signal(signal.SIGINT, lambda _signum, _frame: None)
  signal.signal(signal.SIGHUP, lambda _signum, _frame: None)
  selector = selectors.DefaultSelector()
  os.set_blocking(0, False)
  os.set_blocking(parent_output, False)
  os.set_blocking(parent_input, False)
  selector.register(0, selectors.EVENT_READ, "host-input")
  selector.register(parent_output, selectors.EVENT_READ, "runtime-output")
  pending = bytearray()
  pending_runtime_output = bytearray()
  startup_response_seen = False
  stopping = False

  def write_all(descriptor, data):
      view = memoryview(data)
      while view:
          try:
              view = view[os.write(descriptor, view):]
          except InterruptedError:
              continue

  def reap_children():
      status = ctypes.c_int()
      waitpid = ctypes.CDLL(None, use_errno=True).waitpid
      waitpid.argtypes = (ctypes.c_int, ctypes.POINTER(ctypes.c_int), ctypes.c_int)
      waitpid.restype = ctypes.c_int
      while True:
          result = waitpid(-1, ctypes.byref(status), os.WNOHANG | 0x40000000)
          if result > 0:
              continue
          if result == 0:
              return
          if ctypes.get_errno() == errno.EINTR:
              continue
          if ctypes.get_errno() == errno.ECHILD:
              return
          raise OSError(ctypes.get_errno(), "waitpid failed")

  def namespace_processes():
      try:
          return [int(name) for name in os.listdir("/proc") if name.isdigit() and int(name) != 1]
      except OSError:
          return None

  def signal_namespace_processes(signum):
      pids = namespace_processes()
      if pids is None:
          return None
      for pid in pids:
          try:
              os.kill(pid, signum)
          except ProcessLookupError:
              pass
          except PermissionError:
              return None
      return pids

  def contain_namespace(timeout):
      deadline = time.monotonic() + timeout
      term_sent = False
      while time.monotonic() < deadline:
          pids = namespace_processes()
          if pids is None:
              return False
          if not pids:
              reap_children()
              return namespace_processes() == []
          if not term_sent:
              signal_namespace_processes(signal.SIGTERM)
              term_sent = True
          elif time.monotonic() + 0.2 < deadline:
              signal_namespace_processes(signal.SIGKILL)
          reap_children()
          time.sleep(0.01)
      return False

  while True:
      if stopping:
          if contain_namespace(4.0):
              os._exit(0)
          try:
              os.write(2, b"symphony runtime guard: descendants remain; retaining containment\n")
          except OSError:
              pass
          time.sleep(0.1)
          continue

      try:
          events = selector.select(timeout=0.1)
      except InterruptedError:
          continue
      reap_children()
      for key, _mask in events:
          if key.data == "host-input":
              try:
                  data = os.read(0, 65536)
              except BlockingIOError:
                  continue
              if not data:
                  selector.unregister(0)
                  stopping = True
                  try:
                      os.close(parent_input)
                  except OSError:
                      pass
                  break
              pending.extend(data)
              while b"\n" in pending:
                  line, _, remainder = pending.partition(b"\n")
                  pending = bytearray(remainder)
                  if line + b"\n" == stop_token:
                      stopping = True
                      selector.unregister(0)
                      try:
                          os.close(parent_input)
                      except OSError:
                          pass
                      break
                  try:
                      write_all(parent_input, line + b"\n")
                  except BrokenPipeError:
                      stopping = True
                      break
              if stopping:
                  break
          else:
              try:
                  data = os.read(parent_output, 65536)
              except BlockingIOError:
                  continue
              if not data:
                  selector.unregister(parent_output)
                  os.close(parent_output)
                  if not startup_response_seen:
                      stopping = True
                      try:
                          os.close(parent_input)
                      except OSError:
                          pass
              else:
                  pending_runtime_output.extend(data)
                  while b"\n" in pending_runtime_output:
                      line, _, remainder = pending_runtime_output.partition(b"\n")
                      pending_runtime_output = bytearray(remainder)
                      try:
                          message = json.loads(line)
                          if isinstance(message, dict) and message.get("id") == 1 and ("result" in message or "error" in message):
                              startup_response_seen = True
                      except (UnicodeDecodeError, json.JSONDecodeError):
                          pass
                  write_all(1, data)

  """
  @type session :: %{
          :port => port(),
          :os_pid => pos_integer() | nil,
          :metadata => map(),
          :approval_policy => String.t() | map(),
          :auto_approve_requests => boolean(),
          :thread_sandbox => String.t() | nil,
          :turn_sandbox_policy => map(),
          optional(:absolute_deadline_ms) => integer() | nil,
          optional(:runtime_namespace) => map() | nil,
          :thread_id => String.t(),
          :workspace => Path.t(),
          :worker_host => String.t() | nil,
          :dynamic_tool_binding => map(),
          :ephemeral_home => Path.t() | map() | nil,
          optional(:runtime_policies) => map(),
          optional(:routed) => boolean(),
          optional(:permission_profile) => String.t() | nil,
          optional(:runtime_workspace_roots) => [Path.t()] | nil,
          optional(:access) => :read | :write | nil
        }

  # Startup success depends on the external app-server protocol response.
  @dialyzer {:nowarn_function, run: 4}
  @spec run(Path.t(), String.t(), map(), keyword()) :: {:ok, map()} | {:error, term()}
  def run(workspace, prompt, issue, opts \\ []) do
    with {:ok, session} <- start_session(workspace, opts) do
      execution_result =
        capture_execution_result(fn ->
          run_turn(session, prompt, issue, Keyword.put(opts, :defer_runtime_stop, true))
        end)

      stop_result = stop_run_session(session, opts)
      combine_execution_and_stop(execution_result, stop_result)
    end
  end

  @dialyzer {:nowarn_function, capture_execution_result: 1}
  defp capture_execution_result(fun) do
    {:returned, fun.()}
  rescue
    exception -> {:raised, :error, exception, __STACKTRACE__}
  catch
    kind, reason -> {:raised, kind, reason, __STACKTRACE__}
  end

  @dialyzer {:nowarn_function, stop_run_session: 2}
  defp stop_run_session(session, opts) do
    test_stop_session = Keyword.get(opts, :test_stop_session)

    result =
      if test_environment?() and is_function(test_stop_session, 1) do
        test_stop_session.(session)
      else
        stop_session(session)
      end

    case result do
      :ok -> :ok
      {:error, reason} -> {:error, reason}
      other -> {:error, {:invalid_stop_result, safe_failure_tag(other)}}
    end
  rescue
    exception -> {:error, {:stop_exception, exception.__struct__}}
  catch
    kind, _reason -> {:error, {:stop_failure, kind}}
  end

  @dialyzer {:nowarn_function, combine_execution_and_stop: 2}
  defp combine_execution_and_stop({:returned, result}, :ok), do: result

  defp combine_execution_and_stop({:raised, kind, reason, stacktrace}, :ok) do
    :erlang.raise(kind, reason, stacktrace)
  end

  defp combine_execution_and_stop(execution_result, {:error, stop_reason}) do
    case execution_failure_context(execution_result) do
      nil -> {:error, {:runtime_stop_failed, stop_reason}}
      context -> {:error, {:runtime_stop_failed, stop_reason, context}}
    end
  end

  @dialyzer {:nowarn_function, execution_failure_context: 1}
  defp execution_failure_context({:returned, {:error, reason}}),
    do: {:turn_failed, safe_failure_tag(reason)}

  defp execution_failure_context({:returned, {:ok, _result}}), do: nil

  defp execution_failure_context({:returned, result}),
    do: {:turn_result, safe_failure_tag(result)}

  defp execution_failure_context({:raised, kind, reason, _stacktrace}),
    do: {:turn_raised, kind, safe_failure_tag(reason)}

  @dialyzer {:nowarn_function, safe_failure_tag: 1}
  defp safe_failure_tag(reason) when is_atom(reason), do: reason
  defp safe_failure_tag({tag, _reason}) when is_atom(tag), do: tag
  defp safe_failure_tag({tag, _first, _second}) when is_atom(tag), do: tag
  defp safe_failure_tag(_reason), do: :unspecified

  @spec start_session(Path.t(), keyword()) :: {:ok, session()} | {:error, term()}
  def start_session(workspace, opts \\ []) do
    worker_host = Keyword.get(opts, :worker_host)
    dynamic_tool_binding = DynamicTool.bind(opts)

    with :ok <- check_deadline(Keyword.get(opts, :absolute_deadline_ms)),
         {:ok, expanded_workspace} <- validate_workspace_cwd(workspace, worker_host),
         {:ok, session_policies} <- session_policies(expanded_workspace, worker_host, opts),
         {:ok, holder} <- RuntimeIsolation.prepare_pilot_holder(expanded_workspace, opts) do
      opts = Keyword.put(opts, :pilot_holder_context, holder)

      start_with_policies(
        expanded_workspace,
        worker_host,
        dynamic_tool_binding,
        opts,
        session_policies
      )
    end
  end

  defp start_with_policies(workspace, worker_host, dynamic_tool_binding, opts, session_policies) do
    case check_deadline(Keyword.get(opts, :absolute_deadline_ms)) do
      {:error, reason} -> cleanup_launch_after_error(nil, reason, opts)
      :ok -> prepare_and_start_launch(workspace, worker_host, dynamic_tool_binding, opts, session_policies)
    end
  end

  defp prepare_and_start_launch(workspace, worker_host, dynamic_tool_binding, opts, session_policies) do
    case prepare_launch(workspace, worker_host, session_policies, opts) do
      {:ok, launch} ->
        case check_deadline(Keyword.get(opts, :absolute_deadline_ms)) do
          :ok ->
            start_prepared_launch(
              workspace,
              worker_host,
              dynamic_tool_binding,
              opts,
              session_policies,
              launch
            )

          {:error, reason} ->
            cleanup_launch_after_error(launch, reason, opts)
        end

      {:error, reason, launch} ->
        cleanup_launch_after_error(launch, reason, opts)

      {:error, reason} ->
        cleanup_launch_after_error(nil, reason, opts)
    end
  end

  defp start_prepared_launch(
         workspace,
         worker_host,
         dynamic_tool_binding,
         opts,
         session_policies,
         launch
       ) do
    case revalidate_routed_workspace(workspace, session_policies, opts) do
      :ok ->
        start_prepared_port(
          workspace,
          worker_host,
          dynamic_tool_binding,
          opts,
          session_policies,
          launch
        )

      {:error, reason} ->
        cleanup_launch_after_error(launch, reason, opts)
    end
  end

  defp start_prepared_port(workspace, worker_host, dynamic_tool_binding, opts, session_policies, launch) do
    case start_port(workspace, worker_host, dynamic_tool_binding, opts, session_policies, launch) do
      {:ok, port, ephemeral_home} ->
        start_captured_port(
          port,
          ephemeral_home,
          workspace,
          worker_host,
          dynamic_tool_binding,
          opts,
          session_policies
        )

      {:error, reason} ->
        cleanup_launch_after_error(launch, reason, opts)
    end
  end

  defp start_captured_port(port, ephemeral_home, workspace, worker_host, dynamic_tool_binding, opts, session_policies) do
    namespace_result =
      if routed_policies?(session_policies) and pilot_execution?(Keyword.get(opts, :absolute_deadline_ms)),
        do: capture_runtime_namespace(port, Keyword.get(opts, :absolute_deadline_ms), Keyword.get(opts, :pilot_holder_context)),
        else: {:ok, nil}

    case namespace_result do
      {:ok, namespace_identity} ->
        start_session_on_port(
          port,
          ephemeral_home,
          workspace,
          worker_host,
          dynamic_tool_binding,
          opts,
          session_policies,
          namespace_identity
        )

      {:error, reason} ->
        cleanup_failed_session_start(
          port,
          ephemeral_home,
          reason,
          routed_policies?(session_policies),
          nil,
          Keyword.get(opts, :absolute_deadline_ms),
          opts
        )
    end
  end

  defp cleanup_launch_after_error(launch, reason, opts) do
    with :ok <- RuntimeIsolation.check_pilot_holder(Keyword.get(opts, :pilot_holder_context), :cleanup),
         :ok <- cleanup_launch(launch) do
      {:error, reason}
    else
      {:error, cleanup_reason} -> {:error, cleanup_reason}
    end
  end

  defp start_session_on_port(
         port,
         ephemeral_home,
         workspace,
         worker_host,
         dynamic_tool_binding,
         opts,
         session_policies,
         namespace_identity
       ) do
    deadline_ms = Keyword.get(opts, :absolute_deadline_ms)

    case do_start_session(
           port,
           workspace,
           session_policies,
           dynamic_tool_binding,
           Keyword.get(opts, :absolute_deadline_ms),
           Keyword.get(opts, :pilot_holder_context)
         ) do
      {:ok, thread_id} ->
        case check_deadline(deadline_ms) do
          :ok ->
            session_context = %{opts: opts, policies: session_policies, namespace: namespace_identity}

            {:ok,
             build_session(
               port,
               ephemeral_home,
               workspace,
               worker_host,
               dynamic_tool_binding,
               session_context,
               thread_id
             )}

          {:error, reason} ->
            cleanup_failed_session_start(
              port,
              ephemeral_home,
              reason,
              routed_policies?(session_policies),
              namespace_identity,
              deadline_ms,
              opts
            )
        end

      {:error, reason} ->
        cleanup_failed_session_start(
          port,
          ephemeral_home,
          reason,
          routed_policies?(session_policies),
          namespace_identity,
          deadline_ms,
          opts
        )
    end
  end

  defp build_session(
         port,
         ephemeral_home,
         workspace,
         worker_host,
         dynamic_tool_binding,
         %{opts: opts, policies: session_policies, namespace: namespace_identity},
         thread_id
       ) do
    os_pid = port_os_pid(port)

    %{
      port: port,
      os_pid: os_pid,
      metadata: port_metadata(port, worker_host),
      approval_policy: policy_value(session_policies, :approval_policy),
      auto_approve_requests: auto_approve_requests?(session_policies, opts),
      thread_sandbox: policy_value(session_policies, :thread_sandbox),
      turn_sandbox_policy: policy_value(session_policies, :turn_sandbox_policy, %{}),
      thread_id: thread_id,
      workspace: workspace,
      worker_host: worker_host,
      dynamic_tool_binding: dynamic_tool_binding,
      ephemeral_home: ephemeral_home,
      absolute_deadline_ms: Keyword.get(opts, :absolute_deadline_ms),
      pilot_holder_context: Keyword.get(opts, :pilot_holder_context),
      runtime_policies: session_policies,
      routed: routed_policies?(session_policies),
      runtime_containment: if(routed_policies?(session_policies), do: :linux_pid_namespace, else: nil),
      runtime_namespace: namespace_identity,
      permission_profile: policy_value(session_policies, :permission_profile),
      runtime_workspace_roots: policy_value(session_policies, :runtime_workspace_roots),
      access: policy_value(session_policies, :access)
    }
  end

  defp cleanup_failed_session_start(port, ephemeral_home, reason, routed?, namespace_identity, deadline_ms, opts) do
    stop_result =
      if routed? do
        stop_routed_port(port, namespace_identity, deadline_ms)
      else
        stop_port(port)
      end

    case stop_result do
      :ok ->
        with :ok <- RuntimeIsolation.check_pilot_holder(Keyword.get(opts, :pilot_holder_context), :cleanup),
             :ok <- cleanup_ephemeral_home(ephemeral_home) do
          {:error, reason}
        else
          {:error, cleanup_reason} -> {:error, cleanup_reason}
        end

      {:error, _stop_reason} = error ->
        error
    end
  end

  defp routed_failure(session, session_policies, reason, opts) do
    if routed_policies?(session_policies) and not Keyword.get(opts, :defer_runtime_stop, false) do
      case stop_session(session) do
        :ok -> {:error, reason}
        {:error, cleanup_reason} -> {:error, cleanup_reason}
      end
    else
      {:error, reason}
    end
  end

  @spec run_turn(session(), String.t(), map(), keyword()) :: {:ok, map()} | {:error, term()}
  def run_turn(
        %{
          port: _port,
          metadata: metadata,
          approval_policy: approval_policy,
          auto_approve_requests: auto_approve_requests,
          thread_id: thread_id,
          workspace: workspace,
          dynamic_tool_binding: dynamic_tool_binding
        } = session,
        prompt,
        issue,
        opts \\ []
      ) do
    session_policies =
      Map.get(
        session,
        :runtime_policies,
        %{
          approval_policy: approval_policy,
          turn_sandbox_policy: Map.get(session, :turn_sandbox_policy, %{}),
          routed: Map.get(session, :routed, false),
          permission_profile: Map.get(session, :permission_profile),
          runtime_workspace_roots: Map.get(session, :runtime_workspace_roots)
        }
      )

    on_message = Keyword.get(opts, :on_message, &default_on_message/1)
    turn_tool_binding = overlay_agent_tool_context(dynamic_tool_binding, opts)

    tool_executor =
      Keyword.get(opts, :tool_executor, fn tool, arguments ->
        DynamicTool.execute(tool, arguments, turn_tool_binding, issue: issue)
      end)

    deadline_ms = Map.get(session, :absolute_deadline_ms, Keyword.get(opts, :absolute_deadline_ms))

    turn_start =
      with :ok <- pilot_holder_turn_options(Map.get(session, :pilot_holder_context), opts),
           :ok <- RuntimeIsolation.check_pilot_holder(Map.get(session, :pilot_holder_context), :turn),
           :ok <- check_deadline(deadline_ms) do
        start_session_turn(
          session,
          thread_id,
          prompt,
          issue,
          workspace,
          session_policies,
          Keyword.get(opts, :model),
          deadline_ms
        )
      end

    case turn_start do
      {:ok, turn_id} ->
        session_id = "#{thread_id}-#{turn_id}"

        if pilot_execution?(deadline_ms) do
          Logger.info("Codex pilot turn started")
        else
          Logger.info("Codex session started for #{issue_context(issue)} session_id=#{session_id}")
        end

        emit_message(
          on_message,
          :session_started,
          %{
            session_id: session_id,
            thread_id: thread_id,
            turn_id: turn_id
          },
          metadata
        )

        result =
          await_session_turn(session, thread_id, turn_id, on_message, tool_executor, auto_approve_requests, deadline_ms)

        case result do
          {:ok, result} ->
            log_turn_success(deadline_ms, issue, session_id)

            {:ok,
             %{
               result: result,
               session_id: session_id,
               thread_id: thread_id,
               turn_id: turn_id
             }}

          {:error, reason} ->
            log_turn_error(deadline_ms, issue, session_id, reason)

            emit_message(
              on_message,
              :turn_ended_with_error,
              %{
                session_id: session_id,
                reason: reason
              },
              metadata
            )

            routed_failure(session, session_policies, reason, opts)
        end

      {:error, reason} ->
        log_turn_start_error(deadline_ms, issue, reason)

        result = routed_failure(session, session_policies, reason, opts)
        emit_message(on_message, :startup_failed, %{reason: elem(result, 1)}, metadata)
        result
    end
  end

  defp log_turn_success(deadline_ms, issue, session_id) do
    if pilot_execution?(deadline_ms) do
      Logger.info("Codex pilot response received; final evidence pending")
    else
      Logger.info("Codex session completed for #{issue_context(issue)} session_id=#{session_id}")
    end
  end

  defp log_turn_error(deadline_ms, issue, session_id, reason) do
    if pilot_execution?(deadline_ms) do
      Logger.warning("Codex pilot turn ended with error")
    else
      Logger.warning("Codex session ended with error for #{issue_context(issue)} session_id=#{session_id}: #{inspect(reason)}")
    end
  end

  defp log_turn_start_error(deadline_ms, issue, reason) do
    if pilot_execution?(deadline_ms) do
      Logger.error("Codex pilot startup failed")
    else
      Logger.error("Codex session failed for #{issue_context(issue)}: #{inspect(reason)}")
    end
  end

  @spec stop_session(session()) :: :ok | {:error, term()}
  def stop_session(%{port: port} = session) when is_port(port) do
    native_observation = request_functional_stop(port, session)

    stop_result =
      if Map.get(session, :runtime_containment) == :linux_pid_namespace do
        stop_routed_port(
          port,
          Map.get(session, :runtime_namespace),
          Map.get(session, :absolute_deadline_ms)
        )
      else
        stop_port(port, Map.get(session, :os_pid))
      end

    case stop_result do
      :ok ->
        with :ok <- native_observation,
             :ok <- RuntimeIsolation.check_pilot_holder(Map.get(session, :pilot_holder_context), :cleanup),
             :ok <- retain_functional_namespace_stop(session) do
          cleanup_ephemeral_home(Map.get(session, :ephemeral_home))
        end

      {:error, _reason} = error ->
        error
    end
  end

  if @functional_test_build do
    defp retain_functional_namespace_stop(%{pilot_holder_context: %{assurance: :synthetic_functional_only} = holder} = session) do
      NativePilot.retain_namespace_stop(holder, Map.get(session, :runtime_namespace))
    end
  end

  defp retain_functional_namespace_stop(_session), do: :ok

  defp validate_workspace_cwd(workspace, nil) when is_binary(workspace) do
    expanded_workspace = Path.expand(workspace)
    expanded_root = Config.local_workspace_root()
    expanded_root_prefix = expanded_root <> "/"

    with {:ok, canonical_workspace} <- PathSafety.canonicalize(expanded_workspace),
         {:ok, canonical_root} <- PathSafety.canonicalize(expanded_root) do
      canonical_root_prefix = canonical_root <> "/"

      cond do
        canonical_workspace == canonical_root ->
          {:error, {:invalid_workspace_cwd, :workspace_root, canonical_workspace}}

        String.starts_with?(canonical_workspace <> "/", canonical_root_prefix) ->
          {:ok, canonical_workspace}

        String.starts_with?(expanded_workspace <> "/", expanded_root_prefix) ->
          {:error, {:invalid_workspace_cwd, :symlink_escape, expanded_workspace, canonical_root}}

        true ->
          {:error, {:invalid_workspace_cwd, :outside_workspace_root, canonical_workspace, canonical_root}}
      end
    else
      {:error, {:path_canonicalize_failed, path, reason}} ->
        {:error, {:invalid_workspace_cwd, :path_unreadable, path, reason}}
    end
  end

  defp validate_workspace_cwd(workspace, worker_host)
       when is_binary(workspace) and is_binary(worker_host) do
    cond do
      String.trim(workspace) == "" ->
        {:error, {:invalid_workspace_cwd, :empty_remote_workspace, worker_host}}

      String.contains?(workspace, ["\n", "\r", <<0>>]) ->
        {:error, {:invalid_workspace_cwd, :invalid_remote_workspace, worker_host, workspace}}

      true ->
        {:ok, workspace}
    end
  end

  defp start_port(workspace, nil, dynamic_tool_binding, opts, session_policies, launch) do
    if routed_policies?(session_policies) do
      start_routed_local_port(workspace, dynamic_tool_binding, launch, opts)
    else
      start_legacy_local_port(workspace, dynamic_tool_binding, opts)
    end
  end

  defp start_port(workspace, worker_host, dynamic_tool_binding, opts, session_policies, _launch)
       when is_binary(worker_host) do
    if routed_policies?(session_policies) do
      {:error, {:runtime_isolation_unavailable, :remote_containment_unproven}}
    else
      remote_command = remote_launch_command(workspace, dynamic_tool_binding, opts)

      case SSH.start_port(worker_host, remote_command, line: @port_line_bytes) do
        {:ok, port} -> {:ok, port, nil}
        {:error, reason} -> {:error, reason}
      end
    end
  end

  defp start_legacy_local_port(workspace, dynamic_tool_binding, opts) do
    executable = System.find_executable("bash")

    if is_nil(executable) do
      {:error, :bash_not_found}
    else
      {port_env, ephemeral_home} = local_port_env(dynamic_tool_binding, opts)

      port =
        Port.open(
          {:spawn_executable, String.to_charlist(executable)},
          [
            :binary,
            :exit_status,
            :stderr_to_stdout,
            args: [~c"-lc", String.to_charlist(local_launch_command(dynamic_tool_binding, opts))],
            cd: String.to_charlist(workspace),
            env: port_env,
            line: @port_line_bytes
          ]
        )

      {:ok, port, ephemeral_home}
    end
  end

  defp start_routed_local_port(
         workspace,
         dynamic_tool_binding,
         %{
           resolved: resolved,
           session_home: session_home,
           launch_identity: launch_identity,
           runtime_evidence: runtime_evidence
         },
         opts
       ) do
    with :ok <- require_linux_routed_runtime(opts),
         {:ok, unshare} <- routed_guard_tool("unshare", opts),
         {:ok, python} <- routed_guard_tool("python3", opts),
         :ok <- validate_routed_runtime_identity(resolved, launch_identity, runtime_evidence),
         :ok <- validate_routed_runtime_path(resolved, opts),
         {:ok, runtime_command} <- routed_controller(opts, resolved, python) do
      env =
        CredentialBoundary.routed_port_env(
          dynamic_tool_binding.secret_environment_names,
          session_home.home,
          session_home.codex_home
        )

      args = [
        "--user",
        "--map-current-user",
        "--kill-child",
        "--pid",
        "--fork",
        "--mount-proc",
        python,
        "-I",
        "-S",
        "-c",
        @linux_runtime_guard_script
        | runtime_command
      ]

      {launcher, args} =
        case Keyword.get(opts, :pilot_holder_context) do
          %{assurance: :synthetic_functional_only, pin: %{driver: driver}} ->
            {python, ["-I", "-B", driver, "--host-broker", unshare | args]}

          _ ->
            {unshare, args}
        end

      port =
        Port.open(
          {:spawn_executable, String.to_charlist(launcher)},
          [
            :binary,
            :exit_status,
            :stderr_to_stdout,
            args: Enum.map(args, &String.to_charlist/1),
            cd: String.to_charlist(workspace),
            env: env,
            line: @port_line_bytes
          ]
        )

      {:ok, port, session_home}
    else
      {:error, _reason} = error -> error
    end
  rescue
    error in [ArgumentError, ErlangError] ->
      {:error, {:codex_spawn_failed, error.__struct__}}
  end

  defp routed_controller(opts, resolved, python) do
    case Keyword.get(opts, :pilot_holder_context) do
      %{assurance: :synthetic_functional_only} = holder ->
        NativePilot.functional_command(holder, python)

      _ ->
        {:ok, [resolved.native_executable | resolved.argv]}
    end
  end

  defp require_linux_routed_runtime(opts) do
    platform =
      if test_environment?() and Keyword.has_key?(opts, :test_routed_platform),
        do: Keyword.get(opts, :test_routed_platform),
        else: :os.type()

    case platform do
      {:unix, :linux} -> :ok
      _unsupported -> {:error, {:runtime_isolation_unavailable, :unsupported_platform}}
    end
  end

  defp validate_routed_runtime_path(resolved, opts) do
    enforce_trusted_path? =
      not test_environment?() or Keyword.get(opts, :test_routed_enforce_runtime_path_trust, false)

    if enforce_trusted_path?,
      do: validate_trusted_runtime_paths([resolved.executable, resolved.native_executable]),
      else: :ok
  end

  defp validate_trusted_runtime_paths(paths) do
    if Enum.all?(paths, &(validate_trusted_host_executable(&1) == :ok)),
      do: :ok,
      else: {:error, {:runtime_isolation_unavailable, :codex_installation_untrusted}}
  end

  defp routed_guard_tool(name, opts) do
    override = Keyword.get(opts, :test_routed_guard_tool_paths, %{})
    candidate = if test_environment?(), do: Map.get(override, name), else: nil
    candidate = candidate || System.find_executable(name)

    with true <- is_binary(candidate),
         {:ok, canonical} <- PathSafety.canonicalize(candidate),
         :ok <- validate_trusted_host_executable(canonical) do
      {:ok, canonical}
    else
      _failure ->
        {:error, {:runtime_isolation_unavailable, {:untrusted_linux_guard_tool, name}}}
    end
  end

  defp validate_trusted_host_executable(path), do: PathSafety.validate_trusted_executable(path)

  defp local_port_env(dynamic_tool_binding, opts) do
    if routed_profile?(opts) do
      home_dir = CredentialBoundary.create_routed_ephemeral_home!()

      {CredentialBoundary.routed_port_env(
         dynamic_tool_binding.secret_environment_names,
         home_dir
       ), home_dir}
    else
      {CredentialBoundary.port_env(dynamic_tool_binding.secret_environment_names), nil}
    end
  end

  defp local_launch_command(dynamic_tool_binding, opts) do
    unset_command =
      if routed_profile?(opts) do
        CredentialBoundary.routed_unset_shell_command(dynamic_tool_binding.secret_environment_names)
      else
        CredentialBoundary.unset_shell_command(dynamic_tool_binding.secret_environment_names)
      end

    [
      unset_command,
      "exec #{runtime_command(opts)}"
    ]
    |> Enum.reject(&is_nil/1)
    |> Enum.join(" && ")
  end

  defp cleanup_ephemeral_home(nil), do: :ok

  defp cleanup_ephemeral_home(%{} = session_home) do
    IsolationProfile.cleanup_session_home(session_home)
  end

  defp cleanup_ephemeral_home(home_dir) when is_binary(home_dir) do
    File.rm_rf(home_dir)
    :ok
  end

  defp cleanup_launch(%{session_home: session_home}), do: cleanup_ephemeral_home(session_home)
  defp cleanup_launch(_launch), do: :ok

  defp remote_launch_command(workspace, dynamic_tool_binding, opts) when is_binary(workspace) do
    unset_command =
      if routed_profile?(opts) do
        CredentialBoundary.routed_unset_shell_command(dynamic_tool_binding.secret_environment_names)
      else
        CredentialBoundary.unset_shell_command(dynamic_tool_binding.secret_environment_names)
      end

    [
      "cd #{shell_escape(workspace)}",
      unset_command,
      "exec #{runtime_command(opts)}"
    ]
    |> Enum.reject(&is_nil/1)
    |> Enum.join(" && ")
  end

  defp pilot_holder_turn_options(nil, _opts), do: :ok

  defp pilot_holder_turn_options(%{binding: %{profile: profile}}, opts) do
    if Keyword.get(opts, :model) == profile.model,
      do: :ok,
      else: {:error, :pilot_holder_binding_invalid}
  end

  defp pilot_holder_turn_options(_holder, _opts), do: {:error, :pilot_holder_binding_invalid}

  defp runtime_command(opts) do
    case Keyword.get(opts, :command) do
      command when is_binary(command) and byte_size(command) > 0 -> command
      _ -> Config.settings!().codex.command
    end
  end

  defp auto_approve_requests?(session_policies, opts) do
    routed_policies?(session_policies) == false and
      policy_value(session_policies, :approval_policy) == "never" and
      routed_profile?(opts) == false
  end

  defp routed_profile?(opts) do
    case Keyword.get(opts, :sandbox) do
      sandbox when sandbox in ["read-only", "workspace-write"] -> true
      _ -> false
    end
  end

  defp routed_policies?(session_policies) when is_map(session_policies) do
    policy_value(session_policies, :routed, false) == true
  end

  defp policy_value(session_policies, key, default \\ nil) when is_map(session_policies) do
    case Map.fetch(session_policies, key) do
      {:ok, value} -> value
      :error -> Map.get(session_policies, Atom.to_string(key), default)
    end
  end

  defp port_metadata(port, worker_host) when is_port(port) do
    base_metadata =
      case :erlang.port_info(port, :os_pid) do
        {:os_pid, os_pid} ->
          %{codex_app_server_pid: to_string(os_pid)}

        _ ->
          %{}
      end

    case worker_host do
      host when is_binary(host) -> Map.put(base_metadata, :worker_host, host)
      _ -> base_metadata
    end
  end

  defp send_initialize(port, deadline_ms) do
    payload = %{
      "method" => "initialize",
      "id" => @initialize_id,
      "params" => %{
        "capabilities" => %{
          "experimentalApi" => true
        },
        "clientInfo" => %{
          "name" => "symphony-orchestrator",
          "title" => "Symphony Orchestrator",
          "version" => "0.1.0"
        }
      }
    }

    send_message(port, payload)

    with {:ok, _} <- await_response(port, @initialize_id, deadline_ms) do
      send_message(port, %{"method" => "initialized", "params" => %{}})
      :ok
    end
  end

  defp session_policies(workspace, nil, opts) do
    Config.codex_runtime_settings(workspace, opts)
  end

  defp session_policies(workspace, worker_host, opts) when is_binary(worker_host) do
    Config.codex_runtime_settings(workspace, Keyword.put(opts, :remote, true))
  end

  defp prepare_launch(_workspace, worker_host, session_policies, _opts)
       when is_binary(worker_host) do
    if routed_policies?(session_policies) do
      {:error, {:runtime_isolation_unavailable, :remote_containment_unproven}}
    else
      {:ok, nil}
    end
  end

  defp prepare_launch(workspace, nil, session_policies, opts) do
    cond do
      routed_policies?(session_policies) ->
        prepare_routed_launch(workspace, session_policies, opts)

      match?(%{assurance: :synthetic_functional_only}, Keyword.get(opts, :pilot_holder_context)) ->
        {:error, :native_functional_routed_required}

      true ->
        {:ok, nil}
    end
  end

  defp prepare_routed_launch(workspace, session_policies, opts) do
    with :ok <- validate_routed_policy(session_policies, workspace),
         :ok <- revalidate_routed_workspace(workspace, session_policies, opts),
         {:ok, resolved} <- IsolationProfile.resolve_codex_executable(runtime_command(opts)),
         :ok <- IsolationProfile.validate_pilot_holder_artifact(pilot_holder_selection(opts), resolved),
         {:ok, launch_identity} <- runtime_file_identity(resolved),
         {:ok, runtime_evidence} <- admit_runtime(resolved.executable, opts),
         :ok <- validate_routed_runtime_identity(resolved, launch_identity, runtime_evidence),
         {:ok, session_home} <-
           IsolationProfile.prepare_session_home(
             workspace,
             policy_value(session_policies, :responsibility),
             resolved.native_executable,
             session_home_opts(opts)
           ) do
      bind_routed_session_home(
        resolved,
        session_home,
        session_policies,
        workspace,
        launch_identity,
        runtime_evidence
      )
    end
  end

  defp pilot_holder_selection(opts) do
    case Keyword.get(opts, :pilot_holder_context) do
      %{binding: %{selection: selection}} -> selection
      _ -> nil
    end
  end

  defp bind_routed_session_home(
         resolved,
         session_home,
         session_policies,
         workspace,
         launch_identity,
         runtime_evidence
       ) do
    case validate_session_home(session_home, session_policies, workspace) do
      :ok ->
        {:ok,
         %{
           resolved: resolved,
           session_home: session_home,
           launch_identity: launch_identity,
           runtime_evidence: runtime_evidence
         }}

      {:error, reason} ->
        {:error, reason, %{session_home: session_home}}
    end
  end

  defp revalidate_routed_workspace(workspace, session_policies, opts)
       when is_map(session_policies) do
    if routed_policies?(session_policies) do
      case test_runtime_workspace_admit(opts) do
        {:test, admission} ->
          invoke_test_workspace_admission(admission, workspace, opts)

        :production ->
          revalidate_runtime_workspace(workspace, opts)
      end
    else
      :ok
    end
  end

  defp test_runtime_workspace_admit(opts) do
    if test_environment?() do
      case Keyword.get(opts, :test_runtime_workspace_admit) do
        admission when is_function(admission, 2) -> {:test, admission}
        admission when is_function(admission, 3) -> {:test, admission}
        _missing -> :production
      end
    else
      :production
    end
  end

  defp invoke_test_workspace_admission(admission, workspace, opts)
       when is_function(admission, 2) do
    normalize_workspace_admission(admission.(Keyword.get(opts, :runtime_issue), workspace))
  end

  defp invoke_test_workspace_admission(admission, workspace, opts)
       when is_function(admission, 3) do
    normalize_workspace_admission(
      admission.(
        Keyword.get(opts, :runtime_issue),
        workspace,
        Keyword.get(opts, :ownership_ledger)
      )
    )
  end

  defp normalize_workspace_admission(:ok), do: :ok

  defp normalize_workspace_admission({:error, reason}),
    do: {:error, {:runtime_isolation_unavailable, {:workspace_identity_unproven, reason}}}

  defp normalize_workspace_admission(other),
    do: {:error, {:runtime_isolation_unavailable, {:workspace_admission_invalid, other}}}

  defp revalidate_runtime_workspace(workspace, opts) do
    issue = Keyword.get(opts, :runtime_issue)
    ledger = Keyword.get(opts, :ownership_ledger)

    with %OwnershipLedger{} <- ledger,
         true <- is_map(issue) or is_struct(issue),
         :ok <- Workspace.revalidate_owned_local_workspace(issue, workspace, ledger),
         :ok <- CredentialBoundary.workspace_credential_residue(workspace) do
      :ok
    else
      {:error, {:unsafe_workspace_scm_credentials, _reason}} ->
        {:error, {:runtime_isolation_unavailable, :workspace_scm_boundary_unproven}}

      {:error, _reason} ->
        {:error, {:runtime_isolation_unavailable, :workspace_identity_unproven}}

      _missing_context ->
        {:error, {:runtime_isolation_unavailable, :workspace_identity_unproven}}
    end
  end

  defp validate_routed_policy(session_policies, workspace) do
    responsibility = policy_value(session_policies, :responsibility)
    permission_profile = policy_value(session_policies, :permission_profile)
    runtime_workspace_roots = policy_value(session_policies, :runtime_workspace_roots)
    access = policy_value(session_policies, :access)

    cond do
      not is_binary(responsibility) or String.trim(responsibility) == "" ->
        {:error, {:invalid_routed_policy, :responsibility}}

      not is_binary(permission_profile) or String.trim(permission_profile) == "" ->
        {:error, {:invalid_routed_policy, :permission_profile}}

      access not in [:read, :write] ->
        {:error, {:invalid_routed_policy, :access}}

      runtime_workspace_roots != [workspace] ->
        {:error, {:invalid_routed_policy, :runtime_workspace_roots, [workspace], runtime_workspace_roots}}

      true ->
        :ok
    end
  end

  @doc false
  @spec validate_session_home(map(), map(), Path.t()) :: :ok | {:error, term()}
  def validate_session_home(session_home, session_policies, workspace) do
    expected_profile = policy_value(session_policies, :permission_profile)
    expected_access = policy_value(session_policies, :access)

    cond do
      session_home.permission_profile != expected_profile ->
        {:error, {:runtime_profile_mismatch, :prepared_session_home, expected_profile, session_home.permission_profile}}

      session_home.workspace != workspace ->
        {:error, {:runtime_workspace_mismatch, :prepared_session_home, workspace, session_home.workspace}}

      session_home.access != expected_access ->
        {:error, {:runtime_access_mismatch, :prepared_session_home, expected_access, session_home.access}}

      true ->
        :ok
    end
  end

  defp admit_runtime(executable, opts) do
    test_admission? =
      test_environment?() and Keyword.has_key?(opts, :test_runtime_isolation_admit)

    opts
    |> runtime_admission_callback()
    |> invoke_runtime_admission(executable)
    |> normalize_runtime_admission(test_admission?)
  rescue
    error in [ArgumentError, ErlangError] ->
      {:error, {:runtime_isolation_admission_failed, error.__struct__}}
  catch
    _kind, _reason -> {:error, :runtime_isolation_admission_failed}
  end

  defp runtime_admission_callback(opts) do
    if test_environment?(),
      do: Keyword.get(opts, :test_runtime_isolation_admit, &RuntimeIsolation.admit/3),
      else: &RuntimeIsolation.admit/3
  end

  defp invoke_runtime_admission(admit, executable) when is_function(admit, 3),
    do: admit.(nil, executable, [])

  defp invoke_runtime_admission(admit, executable) when is_function(admit, 2),
    do: admit.(nil, executable)

  defp invoke_runtime_admission(_admit, _executable),
    do: {:error, {:runtime_isolation_admission_invalid, :callback}}

  defp normalize_runtime_admission({:ok, _evidence}, true), do: {:ok, :test_admitted}

  defp normalize_runtime_admission({:ok, %{status: :verified, fingerprint: fingerprint}}, _test?),
    do: {:ok, {:verified, fingerprint}}

  defp normalize_runtime_admission({:error, reason}, _test?), do: {:error, reason}

  defp normalize_runtime_admission({:ok, _evidence}, _test?),
    do: {:error, {:runtime_isolation_admission_invalid, :evidence}}

  defp normalize_runtime_admission(other, _test?),
    do: {:error, {:runtime_isolation_admission_invalid, other}}

  defp runtime_file_identity(resolved) do
    paths = Enum.uniq([resolved.executable, resolved.native_executable])

    Enum.reduce_while(paths, {:ok, %{}}, fn path, {:ok, identities} ->
      with {:ok, canonical_path} <- PathSafety.canonicalize(path),
           {:ok, %File.Stat{} = stat} <- File.stat(canonical_path),
           {:ok, binary} <- File.read(canonical_path) do
        identity = %{
          path: canonical_path,
          device: {stat.major_device, stat.minor_device},
          inode: stat.inode,
          mode: stat.mode,
          size: stat.size,
          mtime: stat.mtime,
          digest: :crypto.hash(:sha256, binary)
        }

        {:cont, {:ok, Map.put(identities, path, identity)}}
      else
        _error ->
          {:halt, {:error, {:runtime_isolation_unavailable, :runtime_changed_after_admission}}}
      end
    end)
  rescue
    _error in [ArgumentError, File.Error, ErlangError] ->
      {:error, {:runtime_isolation_unavailable, :runtime_changed_after_admission}}
  end

  defp validate_routed_runtime_identity(resolved, expected_identity, runtime_evidence) do
    with {:ok, current_identity} <- runtime_file_identity(resolved),
         true <- current_identity == expected_identity,
         :ok <- validate_runtime_evidence(resolved.executable, runtime_evidence) do
      :ok
    else
      false -> {:error, {:runtime_isolation_unavailable, :runtime_changed_after_admission}}
      {:error, _reason} = error -> error
    end
  end

  defp validate_runtime_evidence(_executable, :test_admitted), do: :ok

  defp validate_runtime_evidence(executable, {:verified, fingerprint}) do
    case RuntimeIsolation.evidence(executable) do
      %{status: :verified, fingerprint: ^fingerprint} -> :ok
      _evidence -> {:error, {:runtime_isolation_unavailable, :runtime_changed_after_admission}}
    end
  rescue
    _error -> {:error, {:runtime_isolation_unavailable, :verifier_unavailable}}
  catch
    :exit, _reason -> {:error, {:runtime_isolation_unavailable, :verifier_unavailable}}
  end

  defp test_environment? do
    Code.ensure_loaded?(Mix) and function_exported?(Mix, :env, 0) and Mix.env() == :test
  rescue
    _ -> false
  end

  defp session_home_opts(opts) do
    case Keyword.get(opts, :runtime_session_root, Keyword.get(opts, :session_home_root)) do
      root when is_binary(root) -> [root: root]
      _ -> []
    end
  end

  if @functional_test_build do
    defp do_start_session(
           port,
           workspace,
           %{routed: true} = policies,
           _tools,
           deadline,
           %{assurance: :synthetic_functional_only} = holder
         ) do
      with :ok <- check_deadline(deadline),
           :ok <- await_functional_control(port, holder, :ready),
           :ok <- RuntimeIsolation.check_pilot_holder(holder, :thread),
           :ok <- initialize_functional_holder(port, deadline) do
        start_functional_thread(port, policies, workspace, deadline)
      end
    end
  end

  defp do_start_session(_port, _workspace, _policies, _tools, _deadline, %{assurance: :synthetic_functional_only}),
    do: {:error, :native_functional_routed_required}

  defp do_start_session(port, workspace, session_policies, dynamic_tool_binding, deadline_ms, holder) do
    with :ok <- check_deadline(deadline_ms),
         :ok <- send_initialize(port, deadline_ms),
         :ok <- RuntimeIsolation.check_pilot_holder(holder, :thread),
         :ok <- check_deadline(deadline_ms) do
      start_thread(port, workspace, session_policies, dynamic_tool_binding, deadline_ms)
    end
  end

  defp start_thread(port, workspace, session_policies, dynamic_tool_binding, deadline_ms) do
    if routed_policies?(session_policies) do
      start_routed_thread(port, workspace, session_policies, dynamic_tool_binding, deadline_ms)
    else
      start_legacy_thread(port, workspace, session_policies, dynamic_tool_binding, deadline_ms)
    end
  end

  if @functional_test_build do
    defp initialize_functional_holder(port, deadline) do
      send_message(port, %{
        "method" => "initialize",
        "id" => @initialize_id,
        "params" => %{"clientInfo" => %{"name" => "symphony-offline-planner", "version" => "1"}}
      })

      with {:ok, _response} <- await_response(port, @initialize_id, deadline) do
        send_message(port, %{"method" => "initialized", "params" => %{}})
        :ok
      end
    end

    defp start_functional_thread(port, policies, workspace, deadline) do
      send_message(port, %{"method" => "thread/start", "id" => @thread_start_id, "params" => %{}})

      with {:ok, %{"thread" => %{"id" => thread_id}} = response} when is_binary(thread_id) <-
             await_response(port, @thread_start_id, deadline),
           :ok <- validate_runtime_provenance(response, policies, workspace, :thread_start) do
        {:ok, thread_id}
      else
        {:error, _} = error -> error
        _ -> {:error, :native_functional_thread_refused}
      end
    end
  end

  defp start_legacy_thread(port, workspace, session_policies, dynamic_tool_binding, deadline_ms) do
    send_message(port, %{
      "method" => "thread/start",
      "id" => @thread_start_id,
      "params" => %{
        "approvalPolicy" => policy_value(session_policies, :approval_policy),
        "sandbox" => policy_value(session_policies, :thread_sandbox),
        "cwd" => workspace,
        "dynamicTools" => dynamic_tool_binding.tool_specs
      }
    })

    case await_response(port, @thread_start_id, deadline_ms) do
      {:ok, %{"thread" => thread_payload}} ->
        case thread_payload do
          %{"id" => thread_id} -> {:ok, thread_id}
          _ -> {:error, {:invalid_thread_payload, thread_payload}}
        end

      other ->
        other
    end
  end

  defp start_routed_thread(port, workspace, session_policies, dynamic_tool_binding, deadline_ms) do
    send_message(port, %{
      "method" => "thread/start",
      "id" => @thread_start_id,
      "params" => %{
        "approvalPolicy" => policy_value(session_policies, :approval_policy),
        "permissions" => policy_value(session_policies, :permission_profile),
        "runtimeWorkspaceRoots" => policy_value(session_policies, :runtime_workspace_roots),
        "cwd" => workspace,
        "dynamicTools" => dynamic_tool_binding.tool_specs
      }
    })

    case await_response(port, @thread_start_id, deadline_ms) do
      {:ok, %{"thread" => %{"id" => thread_id}} = response} ->
        case validate_runtime_provenance(response, session_policies, workspace, :thread_start) do
          :ok -> {:ok, thread_id}
          {:error, _reason} = error -> error
        end

      {:ok, %{"thread" => thread_payload}} ->
        {:error, {:invalid_thread_payload, thread_payload}}

      other ->
        other
    end
  end

  defp start_turn(
         port,
         thread_id,
         prompt,
         issue,
         workspace,
         session_policies,
         model,
         deadline_ms
       ) do
    with :ok <- check_deadline(deadline_ms) do
      base_params = %{
        "threadId" => thread_id,
        "input" => [
          %{
            "type" => "text",
            "text" => prompt
          }
        ],
        "cwd" => workspace,
        "title" => "#{issue.identifier}: #{issue.title}",
        "approvalPolicy" => policy_value(session_policies, :approval_policy)
      }

      params =
        if routed_policies?(session_policies) do
          Map.merge(base_params, %{
            "permissions" => policy_value(session_policies, :permission_profile),
            "runtimeWorkspaceRoots" => policy_value(session_policies, :runtime_workspace_roots)
          })
        else
          Map.put(
            base_params,
            "sandboxPolicy",
            policy_value(session_policies, :turn_sandbox_policy, %{})
          )
        end

      params = maybe_put_model(params, model)

      send_message(port, %{
        "method" => "turn/start",
        "id" => @turn_start_id,
        "params" => params
      })

      case await_response(port, @turn_start_id, deadline_ms) do
        {:ok, %{"turn" => %{"id" => turn_id}} = response} ->
          validate_turn_start_response(turn_id, response, session_policies, workspace)

        other ->
          other
      end
    end
  end

  defp validate_turn_start_response(turn_id, response, session_policies, workspace) do
    case validate_turn_provenance(response, session_policies, workspace) do
      :ok -> {:ok, turn_id}
      {:error, _reason} = error -> error
    end
  end

  defp validate_runtime_provenance(response, session_policies, workspace, phase) do
    expected_profile = policy_value(session_policies, :permission_profile)
    expected_roots = policy_value(session_policies, :runtime_workspace_roots)

    actual_profile =
      response
      |> Map.get("activePermissionProfile")
      |> profile_id()

    actual_roots = Map.get(response, "runtimeWorkspaceRoots")
    actual_cwd = Map.get(response, "cwd")

    with :ok <-
           compare_provenance(
             phase,
             :active_permission_profile,
             expected_profile,
             actual_profile
           ),
         :ok <- compare_provenance(phase, :runtime_workspace_roots, expected_roots, actual_roots) do
      compare_provenance(phase, :cwd, workspace, actual_cwd)
    end
  end

  defp validate_turn_provenance(response, session_policies, workspace) do
    case routed_policies?(session_policies) do
      true -> validate_routed_turn_provenance(response, session_policies, workspace)
      false -> :ok
    end
  end

  defp validate_routed_turn_provenance(response, session_policies, workspace) do
    turn_payload = Map.get(response, "turn", %{})

    case turn_provenance_present?(response, turn_payload) do
      true ->
        provenance = Map.merge(response, turn_payload_map(turn_payload))
        validate_runtime_provenance(provenance, session_policies, workspace, :turn_start)

      false ->
        {:error, {:runtime_provenance_missing, :turn_start}}
    end
  end

  defp turn_provenance_present?(response, turn_payload) do
    Enum.any?([response, turn_payload], &provenance_payload?/1)
  end

  defp provenance_payload?(payload) when is_map(payload) do
    Enum.any?(
      ["activePermissionProfile", "runtimeWorkspaceRoots", "cwd"],
      &Map.has_key?(payload, &1)
    )
  end

  defp provenance_payload?(_payload), do: false

  defp turn_payload_map(turn_payload) when is_map(turn_payload), do: turn_payload
  defp turn_payload_map(_turn_payload), do: %{}

  defp profile_id(%{"id" => id}) when is_binary(id), do: id
  defp profile_id(id) when is_binary(id), do: id
  defp profile_id(_profile), do: nil

  defp compare_provenance(_phase, _field, expected, expected), do: :ok

  defp compare_provenance(phase, field, expected, actual),
    do: {:error, {:runtime_provenance_mismatch, phase, field, expected, actual}}

  defp maybe_put_model(params, model) when is_binary(model) do
    if String.trim(model) == "", do: params, else: Map.put(params, "model", model)
  end

  defp maybe_put_model(params, _model), do: params

  defp check_deadline(nil), do: :ok

  defp check_deadline(deadline_ms) when is_integer(deadline_ms) do
    if deadline_ms > System.monotonic_time(:millisecond), do: :ok, else: {:error, :turn_timeout}
  end

  defp check_deadline(deadline_ms), do: {:error, {:invalid_absolute_deadline_ms, deadline_ms}}

  defp receive_timeout(timeout_ms, nil), do: timeout_ms

  defp receive_timeout(timeout_ms, deadline_ms) do
    min(timeout_ms, max(deadline_ms - System.monotonic_time(:millisecond), 0))
  end

  defp deadline_expired?(deadline_ms) when is_integer(deadline_ms),
    do: deadline_ms <= System.monotonic_time(:millisecond)

  defp deadline_expired?(_deadline_ms), do: false

  defp await_turn_completion(port, on_message, tool_executor, auto_approve_requests, deadline_ms) do
    receive_loop(
      port,
      on_message,
      Config.settings!().codex.turn_timeout_ms,
      "",
      tool_executor,
      auto_approve_requests,
      deadline_ms
    )
  end

  if @functional_test_build do
    defp start_functional_turn(port, thread_id, prompt, deadline) do
      send_message(port, %{
        "method" => "turn/start",
        "id" => @turn_start_id,
        "params" => %{"threadId" => thread_id, "input" => [%{"type" => "text", "text" => prompt}]}
      })

      case await_response(port, @turn_start_id, deadline) do
        {:ok, %{"turn" => %{"id" => turn_id}}} when is_binary(turn_id) and turn_id != "" -> {:ok, turn_id}
        {:error, _reason} = error -> error
        _ -> {:error, :native_functional_turn_refused}
      end
    end

    defp await_functional_turn(port, holder, thread, turn, on_message) do
      alias SymphonyElixir.AgentRuntime.HostBoundary

      with {:ok, boundary} <- HostBoundary.open(holder, thread, turn) do
        try do
          receive_functional_turn(port, boundary, holder.binding.absolute_deadline_ms, thread, turn, on_message, false)
        after
          HostBoundary.close(boundary)
        end
      end
    end

    defp receive_functional_turn(port, boundary, deadline, thread, turn, on_message, final?) do
      with {:ok, message, raw} <- functional_frame(port, deadline, "") do
        case functional_turn_message(message, raw, port, boundary, thread, turn, on_message, final?) do
          {:continue, next, final?} ->
            receive_functional_turn(port, next, deadline, thread, turn, on_message, final?)

          result ->
            result
        end
      end
    end

    defp functional_turn_message(%{"symphonyProviderEffect" => frame} = wrapper, _raw, port, boundary, _thread, _turn, _on_message, final?) when map_size(wrapper) == 1 and not final? do
      alias SymphonyElixir.AgentRuntime.HostBoundary

      with {:ok, reply, next} <- HostBoundary.effect(boundary, frame) do
        send_message(port, %{"symphonyProviderEffect" => reply})
        {:continue, next, false}
      end
    end

    defp functional_turn_message(
           %{
             "method" => "turn/started",
             "params" => %{
               "threadId" => thread,
               "turn" => %{"id" => turn}
             }
           },
           _raw,
           _port,
           boundary,
           thread,
           turn,
           _callback,
           final?
         ),
         do: {:continue, boundary, final?}

    defp functional_turn_message(
           %{
             "method" => "item/completed",
             "params" => %{
               "threadId" => thread,
               "turnId" => turn,
               "item" => %{"type" => "agentMessage", "phase" => "final_answer", "id" => id, "text" => answer}
             }
           } = message,
           raw,
           port,
           boundary,
           thread,
           turn,
           on_message,
           false
         )
         when is_binary(id) and byte_size(id) in 1..128 and is_binary(answer) and byte_size(answer) in 1..16_384 do
      alias SymphonyElixir.AgentRuntime.HostBoundary

      with :ok <- HostBoundary.completed?(boundary) do
        emit_turn_event(on_message, :notification, message, raw, port, message)
        {:continue, boundary, true}
      end
    end

    defp functional_turn_message(
           %{
             "method" => "turn/completed",
             "params" => %{
               "threadId" => thread,
               "turn" => %{"id" => turn, "status" => "completed"}
             }
           } = message,
           raw,
           port,
           boundary,
           thread,
           turn,
           on_message,
           true
         ) do
      alias SymphonyElixir.AgentRuntime.HostBoundary

      with :ok <- HostBoundary.completed?(boundary) do
        emit_turn_event(on_message, :turn_completed, message, raw, port, message)
        {:ok, message}
      end
    end

    defp functional_turn_message(
           %{
             "method" => "turn/completed",
             "params" => %{
               "threadId" => thread,
               "turn" => %{"id" => turn, "status" => status}
             }
           },
           _raw,
           _port,
           _boundary,
           thread,
           turn,
           _on_message,
           _final?
         )
         when status in ["failed", "interrupted"],
         do: {:error, :native_functional_turn_failed}

    defp functional_turn_message(%{"method" => "error", "params" => %{"threadId" => thread, "turnId" => turn}}, _raw, _port, _boundary, thread, turn, _on_message, _final?),
      do: {:error, :native_functional_turn_failed}

    defp functional_turn_message(%{"method" => "item/started", "params" => %{"threadId" => thread, "turnId" => turn}}, _raw, _port, boundary, thread, turn, _on_message, final?),
      do: {:continue, boundary, final?}

    defp functional_turn_message(_message, _raw, _port, _boundary, _thread, _turn, _callback, _final?),
      do: {:error, :native_functional_turn_refused}
  end

  if @functional_test_build do
    defp start_session_turn(
           %{port: port, pilot_holder_context: %{assurance: :synthetic_functional_only}},
           thread,
           prompt,
           _issue,
           _workspace,
           _policies,
           _model,
           deadline
         ) do
      start_functional_turn(port, thread, prompt, deadline)
    end
  end

  defp start_session_turn(%{port: port}, thread, prompt, issue, workspace, policies, model, deadline) do
    start_turn(port, thread, prompt, issue, workspace, policies, model, deadline)
  end

  if @functional_test_build do
    defp await_session_turn(
           %{port: port, pilot_holder_context: %{assurance: :synthetic_functional_only} = holder},
           thread,
           turn,
           on_message,
           _tool_executor,
           _auto_approve,
           _deadline
         ) do
      await_functional_turn(port, holder, thread, turn, on_message)
    end
  end

  defp await_session_turn(%{port: port}, _thread, _turn, on_message, tool_executor, auto_approve, deadline) do
    await_turn_completion(port, on_message, tool_executor, auto_approve, deadline)
  end

  if @functional_test_build do
    defp await_functional_control(port, holder, phase) do
      case functional_frame(port, holder.binding.absolute_deadline_ms, "") do
        {:ok, %{"symphonyNativeControl" => receipt} = wrapper, _raw} when map_size(wrapper) == 1 ->
          with {:ok, _validated} <- NativePilot.verify_functional_receipt(holder, phase, receipt), do: :ok

        {:ok, %{"method" => method}, _raw} when phase == :stopped and method in ["turn/completed", "error"] ->
          await_functional_control(port, holder, phase)

        _ ->
          {:error, :native_functional_observation_refused}
      end
    end

    defp functional_frame(port, deadline, pending) do
      with :ok <- check_deadline(deadline) do
        receive do
          {^port, {:data, {:eol, chunk}}} when byte_size(pending) + byte_size(chunk) <= 65_536 ->
            raw = pending <> chunk

            case Jason.decode(raw) do
              {:ok, message} when is_map(message) -> {:ok, message, raw}
              _ -> {:error, :native_functional_frame_refused}
            end

          {^port, {:data, {:noeol, chunk}}} when byte_size(pending) + byte_size(chunk) < 65_536 ->
            functional_frame(port, deadline, pending <> chunk)

          {^port, _message} ->
            {:error, :native_functional_frame_refused}
        after
          receive_timeout(@port_monitor_timeout_ms, deadline) -> {:error, :native_functional_timeout}
        end
      end
    end
  end

  if @functional_test_build do
    defp request_functional_stop(port, %{pilot_holder_context: %{assurance: :synthetic_functional_only} = holder}) do
      send_message(port, %{
        "symphonyNativeControl" => %{
          "schema" => "H100-NATIVE-CONTROL-1",
          "kind" => "stop",
          "binding" => holder.digest,
          "attempt" => holder.binding.attempt.runtime_attempt_id,
          "sequence" => 1
        }
      })

      await_functional_control(port, holder, :stopped)
    rescue
      ArgumentError -> {:error, :native_functional_stop_unverified}
    end
  end

  defp request_functional_stop(_port, _session), do: :ok

  defp receive_loop(
         port,
         on_message,
         timeout_ms,
         pending_line,
         tool_executor,
         auto_approve_requests,
         deadline_ms
       ) do
    if check_deadline(deadline_ms) == :ok do
      do_receive_loop(
        port,
        on_message,
        timeout_ms,
        pending_line,
        tool_executor,
        auto_approve_requests,
        deadline_ms
      )
    else
      {:error, :turn_timeout}
    end
  end

  defp do_receive_loop(
         port,
         on_message,
         timeout_ms,
         pending_line,
         tool_executor,
         auto_approve_requests,
         deadline_ms
       ) do
    receive do
      {^port, {:data, {:eol, chunk}}} ->
        complete_line = pending_line <> to_string(chunk)

        handle_incoming(
          port,
          on_message,
          complete_line,
          timeout_ms,
          tool_executor,
          auto_approve_requests,
          deadline_ms
        )

      {^port, {:data, {:noeol, chunk}}} ->
        receive_loop(
          port,
          on_message,
          timeout_ms,
          pending_line <> to_string(chunk),
          tool_executor,
          auto_approve_requests,
          deadline_ms
        )

      {^port, {:exit_status, status}} ->
        {:error, {:port_exit, status}}
    after
      receive_timeout(timeout_ms, deadline_ms) ->
        {:error, :turn_timeout}
    end
  end

  defp handle_incoming(port, on_message, data, timeout_ms, tool_executor, auto_approve_requests, deadline_ms) do
    if check_deadline(deadline_ms) == :ok do
      handle_incoming_payload(port, on_message, data, timeout_ms, tool_executor, auto_approve_requests, deadline_ms)
    else
      {:error, :turn_timeout}
    end
  end

  defp handle_incoming_payload(port, on_message, data, timeout_ms, tool_executor, auto_approve_requests, deadline_ms) do
    payload_string = to_string(data)

    case Jason.decode(payload_string) do
      {:ok, %{"method" => "turn/completed"} = payload} ->
        emit_turn_event(on_message, :turn_completed, payload, payload_string, port, payload)
        {:ok, :turn_completed}

      {:ok, %{"method" => "turn/failed", "params" => _} = payload} ->
        emit_turn_event(
          on_message,
          :turn_failed,
          payload,
          payload_string,
          port,
          Map.get(payload, "params")
        )

        {:error, {:turn_failed, Map.get(payload, "params")}}

      {:ok, %{"method" => "turn/cancelled", "params" => _} = payload} ->
        emit_turn_event(
          on_message,
          :turn_cancelled,
          payload,
          payload_string,
          port,
          Map.get(payload, "params")
        )

        {:error, {:turn_cancelled, Map.get(payload, "params")}}

      {:ok, %{"method" => method} = payload}
      when is_binary(method) ->
        handle_turn_method(
          port,
          on_message,
          payload,
          payload_string,
          method,
          %{
            timeout_ms: timeout_ms,
            deadline_ms: deadline_ms,
            tool_executor: tool_executor,
            auto_approve_requests: auto_approve_requests
          },
          tool_executor,
          auto_approve_requests
        )

      {:ok, payload} ->
        emit_message(
          on_message,
          :other_message,
          %{
            payload: payload,
            raw: payload_string
          },
          metadata_from_message(port, payload)
        )

        receive_loop(port, on_message, timeout_ms, "", tool_executor, auto_approve_requests, deadline_ms)

      {:error, _reason} ->
        log_non_json_stream_line(payload_string, "turn stream", deadline_ms)

        if protocol_message_candidate?(payload_string) do
          emit_message(
            on_message,
            :malformed,
            %{
              payload: payload_string,
              raw: payload_string
            },
            metadata_from_message(port, %{raw: payload_string})
          )
        end

        receive_loop(port, on_message, timeout_ms, "", tool_executor, auto_approve_requests, deadline_ms)
    end
  end

  defp emit_turn_event(on_message, event, payload, payload_string, port, payload_details) do
    emit_message(
      on_message,
      event,
      %{
        payload: payload,
        raw: payload_string,
        details: payload_details
      },
      metadata_from_message(port, payload)
    )
  end

  defp handle_turn_method(
         port,
         on_message,
         payload,
         payload_string,
         method,
         %{timeout_ms: timeout_ms, deadline_ms: deadline_ms} = wait_context,
         tool_executor,
         auto_approve_requests
       ) do
    metadata = metadata_from_message(port, payload)

    case maybe_handle_approval_request(
           port,
           method,
           payload,
           payload_string,
           on_message,
           metadata,
           tool_executor,
           auto_approve_requests
         ) do
      :input_required ->
        emit_message(
          on_message,
          :turn_input_required,
          %{payload: payload, raw: payload_string},
          metadata
        )

        {:error, {:turn_input_required, payload}}

      :approved ->
        receive_loop(port, on_message, timeout_ms, "", tool_executor, auto_approve_requests, deadline_ms)

      :approval_required ->
        emit_message(
          on_message,
          :approval_required,
          %{payload: payload, raw: payload_string},
          metadata
        )

        {:error, {:approval_required, payload}}

      :unhandled ->
        handle_unhandled_turn_method(port, on_message, payload, payload_string, method, wait_context, metadata)
    end
  end

  defp handle_unhandled_turn_method(port, on_message, payload, payload_string, method, wait_context, metadata) do
    if needs_input?(method, payload) do
      emit_message(
        on_message,
        :turn_input_required,
        %{payload: payload, raw: payload_string},
        metadata
      )

      {:error, {:turn_input_required, payload}}
    else
      emit_message(
        on_message,
        :notification,
        %{payload: payload, raw: payload_string},
        metadata
      )

      unless pilot_execution?(wait_context.deadline_ms), do: Logger.debug("Codex notification: #{inspect(method)}")

      receive_loop(
        port,
        on_message,
        wait_context.timeout_ms,
        "",
        wait_context.tool_executor,
        wait_context.auto_approve_requests,
        wait_context.deadline_ms
      )
    end
  end

  defp maybe_handle_approval_request(
         port,
         "item/commandExecution/requestApproval",
         %{"id" => id} = payload,
         payload_string,
         on_message,
         metadata,
         _tool_executor,
         auto_approve_requests
       ) do
    approve_or_require(
      port,
      id,
      "acceptForSession",
      payload,
      payload_string,
      on_message,
      metadata,
      auto_approve_requests
    )
  end

  defp maybe_handle_approval_request(
         port,
         "item/tool/call",
         %{"id" => id, "params" => params} = payload,
         payload_string,
         on_message,
         metadata,
         tool_executor,
         _auto_approve_requests
       ) do
    tool_name = tool_call_name(params)
    arguments = tool_call_arguments(params)

    result =
      tool_name
      |> tool_executor.(arguments)
      |> normalize_dynamic_tool_result()

    send_message(port, %{
      "id" => id,
      "result" => result
    })

    event =
      case result do
        %{"success" => true} -> :tool_call_completed
        _ when is_nil(tool_name) -> :unsupported_tool_call
        _ -> :tool_call_failed
      end

    emit_message(on_message, event, %{payload: payload, raw: payload_string}, metadata)

    :approved
  end

  defp maybe_handle_approval_request(
         port,
         "execCommandApproval",
         %{"id" => id} = payload,
         payload_string,
         on_message,
         metadata,
         _tool_executor,
         auto_approve_requests
       ) do
    approve_or_require(
      port,
      id,
      "approved_for_session",
      payload,
      payload_string,
      on_message,
      metadata,
      auto_approve_requests
    )
  end

  defp maybe_handle_approval_request(
         port,
         "applyPatchApproval",
         %{"id" => id} = payload,
         payload_string,
         on_message,
         metadata,
         _tool_executor,
         auto_approve_requests
       ) do
    approve_or_require(
      port,
      id,
      "approved_for_session",
      payload,
      payload_string,
      on_message,
      metadata,
      auto_approve_requests
    )
  end

  defp maybe_handle_approval_request(
         port,
         "item/fileChange/requestApproval",
         %{"id" => id} = payload,
         payload_string,
         on_message,
         metadata,
         _tool_executor,
         auto_approve_requests
       ) do
    approve_or_require(
      port,
      id,
      "acceptForSession",
      payload,
      payload_string,
      on_message,
      metadata,
      auto_approve_requests
    )
  end

  defp maybe_handle_approval_request(
         port,
         "item/tool/requestUserInput",
         %{"id" => id, "params" => params} = payload,
         payload_string,
         on_message,
         metadata,
         _tool_executor,
         auto_approve_requests
       ) do
    maybe_auto_answer_tool_request_user_input(
      port,
      id,
      params,
      payload,
      payload_string,
      on_message,
      metadata,
      auto_approve_requests
    )
  end

  defp maybe_handle_approval_request(
         _port,
         _method,
         _payload,
         _payload_string,
         _on_message,
         _metadata,
         _tool_executor,
         _auto_approve_requests
       ) do
    :unhandled
  end

  defp normalize_dynamic_tool_result(%{"success" => success} = result) when is_boolean(success) do
    output =
      case Map.get(result, "output") do
        existing_output when is_binary(existing_output) -> existing_output
        _ -> dynamic_tool_output(result)
      end

    content_items =
      case Map.get(result, "contentItems") do
        existing_items when is_list(existing_items) -> existing_items
        _ -> dynamic_tool_content_items(output)
      end

    result
    |> Map.put("output", output)
    |> Map.put("contentItems", content_items)
  end

  defp normalize_dynamic_tool_result(result) do
    %{
      "success" => false,
      "output" => inspect(result),
      "contentItems" => dynamic_tool_content_items(inspect(result))
    }
  end

  defp dynamic_tool_output(%{"contentItems" => [%{"text" => text} | _]}) when is_binary(text),
    do: text

  defp dynamic_tool_output(result), do: Jason.encode!(result, pretty: true)

  defp dynamic_tool_content_items(output) when is_binary(output) do
    [
      %{
        "type" => "inputText",
        "text" => output
      }
    ]
  end

  defp approve_or_require(
         port,
         id,
         decision,
         payload,
         payload_string,
         on_message,
         metadata,
         true
       ) do
    send_message(port, %{"id" => id, "result" => %{"decision" => decision}})

    emit_message(
      on_message,
      :approval_auto_approved,
      %{payload: payload, raw: payload_string, decision: decision},
      metadata
    )

    :approved
  end

  defp approve_or_require(
         _port,
         _id,
         _decision,
         _payload,
         _payload_string,
         _on_message,
         _metadata,
         false
       ) do
    :approval_required
  end

  defp maybe_auto_answer_tool_request_user_input(
         port,
         id,
         params,
         payload,
         payload_string,
         on_message,
         metadata,
         true
       ) do
    case tool_request_user_input_approval_answers(params) do
      {:ok, answers, decision} ->
        send_message(port, %{"id" => id, "result" => %{"answers" => answers}})

        emit_message(
          on_message,
          :approval_auto_approved,
          %{payload: payload, raw: payload_string, decision: decision},
          metadata
        )

        :approved

      :error ->
        :input_required
    end
  end

  defp maybe_auto_answer_tool_request_user_input(
         _port,
         _id,
         _params,
         _payload,
         _payload_string,
         _on_message,
         _metadata,
         false
       ),
       do: :input_required

  defp tool_request_user_input_approval_answers(%{"questions" => questions})
       when is_list(questions) do
    answers =
      Enum.reduce_while(questions, %{}, fn question, acc ->
        case tool_request_user_input_approval_answer(question) do
          {:ok, question_id, answer_label} ->
            {:cont, Map.put(acc, question_id, %{"answers" => [answer_label]})}

          :error ->
            {:halt, :error}
        end
      end)

    case answers do
      :error -> :error
      answer_map when map_size(answer_map) > 0 -> {:ok, answer_map, "Approve this Session"}
      _ -> :error
    end
  end

  defp tool_request_user_input_approval_answers(_params), do: :error

  defp tool_request_user_input_approval_answer(%{"id" => question_id, "options" => options})
       when is_binary(question_id) and is_list(options) do
    if String.starts_with?(question_id, "mcp_tool_call_approval_") do
      case tool_request_user_input_approval_option_label(options) do
        nil -> :error
        answer_label -> {:ok, question_id, answer_label}
      end
    else
      :error
    end
  end

  defp tool_request_user_input_approval_answer(_question), do: :error

  defp tool_request_user_input_approval_option_label(options) do
    options
    |> Enum.map(&tool_request_user_input_option_label/1)
    |> Enum.reject(&is_nil/1)
    |> case do
      labels ->
        Enum.find(labels, &(&1 == "Approve this Session")) ||
          Enum.find(labels, &(&1 == "Approve Once")) ||
          Enum.find(labels, &approval_option_label?/1)
    end
  end

  defp tool_request_user_input_option_label(%{"label" => label}) when is_binary(label), do: label
  defp tool_request_user_input_option_label(_option), do: nil

  defp approval_option_label?(label) when is_binary(label) do
    normalized_label =
      label
      |> String.trim()
      |> String.downcase()

    String.starts_with?(normalized_label, "approve") or
      String.starts_with?(normalized_label, "allow")
  end

  defp await_response(port, request_id, deadline_ms) do
    with_timeout_response(port, request_id, Config.settings!().codex.read_timeout_ms, "", deadline_ms)
  end

  defp with_timeout_response(port, request_id, timeout_ms, pending_line, deadline_ms) do
    if check_deadline(deadline_ms) == :ok do
      do_with_timeout_response(port, request_id, timeout_ms, pending_line, deadline_ms)
    else
      {:error, :turn_timeout}
    end
  end

  defp do_with_timeout_response(port, request_id, timeout_ms, pending_line, deadline_ms) do
    receive do
      {^port, {:data, {:eol, chunk}}} ->
        complete_line = pending_line <> to_string(chunk)
        handle_response(port, request_id, complete_line, timeout_ms, deadline_ms)

      {^port, {:data, {:noeol, chunk}}} ->
        with_timeout_response(port, request_id, timeout_ms, pending_line <> to_string(chunk), deadline_ms)

      {^port, {:exit_status, status}} ->
        {:error, {:port_exit, status}}
    after
      receive_timeout(timeout_ms, deadline_ms) ->
        if deadline_expired?(deadline_ms), do: {:error, :turn_timeout}, else: {:error, :response_timeout}
    end
  end

  defp handle_response(port, request_id, data, timeout_ms, deadline_ms) do
    if check_deadline(deadline_ms) == :ok do
      handle_response_payload(port, request_id, data, timeout_ms, deadline_ms)
    else
      {:error, :turn_timeout}
    end
  end

  defp handle_response_payload(port, request_id, data, timeout_ms, deadline_ms) do
    payload = to_string(data)

    case Jason.decode(payload) do
      {:ok, %{"id" => ^request_id, "error" => error}} ->
        {:error, {:response_error, error}}

      {:ok, %{"id" => ^request_id, "result" => result}} ->
        {:ok, result}

      {:ok, %{"id" => ^request_id} = response_payload} ->
        {:error, {:response_error, response_payload}}

      {:ok, %{} = other} ->
        unless pilot_execution?(deadline_ms),
          do: Logger.debug("Ignoring message while waiting for response: #{inspect(other)}")

        with_timeout_response(port, request_id, timeout_ms, "", deadline_ms)

      {:error, _} ->
        log_non_json_stream_line(payload, "response stream", deadline_ms)
        with_timeout_response(port, request_id, timeout_ms, "", deadline_ms)
    end
  end

  defp log_non_json_stream_line(_data, _stream_label, deadline_ms) when is_integer(deadline_ms), do: :ok

  defp log_non_json_stream_line(data, stream_label, _deadline_ms) do
    text =
      data
      |> to_string()
      |> String.trim()
      |> String.slice(0, @max_stream_log_bytes)

    if text != "" do
      if String.match?(text, ~r/\b(error|warn|warning|failed|fatal|panic|exception)\b/i) do
        Logger.warning("Codex #{stream_label} output: #{text}")
      else
        Logger.debug("Codex #{stream_label} output: #{text}")
      end
    end
  end

  defp pilot_execution?(deadline_ms), do: is_integer(deadline_ms)

  defp protocol_message_candidate?(data) do
    data
    |> to_string()
    |> String.trim_leading()
    |> String.starts_with?("{")
  end

  defp issue_context(%{id: issue_id, identifier: identifier}) do
    "issue_id=#{issue_id} issue_identifier=#{identifier}"
  end

  defp stop_port(port) when is_port(port) do
    stop_port(port, port_os_pid(port))
  end

  defp stop_routed_port(port, namespace_identity, deadline_ms) when is_port(port) do
    ref = :erlang.monitor(:port, port)

    try do
      Port.command(port, @routed_stop_token)
    rescue
      ArgumentError -> :already_closed
    end

    receive do
      {:DOWN, ^ref, :port, ^port, _reason} ->
        if pilot_execution?(deadline_ms), do: verify_namespace_stopped(namespace_identity, deadline_ms), else: :ok
    after
      receive_timeout(@linux_guard_stop_timeout_ms, deadline_ms) ->
        Process.demonitor(ref, [:flush])
        {:error, {:containment_unconfirmed, :termination_timeout}}
    end
  end

  defp stop_port(port, fallback_os_pid) when is_port(port) do
    os_pid = port_os_pid(port) || fallback_os_pid
    ref = :erlang.monitor(:port, port)

    close_result = close_port(port)

    receive do
      {:DOWN, ^ref, :port, ^port, _reason} ->
        case {close_result, os_pid} do
          {:already_closed, nil} ->
            {:error, {:stop_failed, :session_stopped}}

          _ ->
            case terminate_os_process(os_pid) do
              :ok -> :ok
              {:error, reason} -> {:error, {:stop_failed, reason}}
            end
        end
    after
      @port_monitor_timeout_ms ->
        Process.demonitor(ref, [:flush])
        _ = terminate_os_process(os_pid)
        {:error, {:stop_failed, :process_state_unavailable}}
    end
  end

  defp close_port(port) do
    Port.close(port)
    :closed
  rescue
    ArgumentError -> :already_closed
  end

  defp port_os_pid(port) when is_port(port) do
    case :erlang.port_info(port, :os_pid) do
      {:os_pid, os_pid} when is_integer(os_pid) -> os_pid
      _ -> nil
    end
  rescue
    ArgumentError -> nil
  end

  defp capture_runtime_namespace(port, deadline_ms, holder) do
    attempts = if match?(%{assurance: :synthetic_functional_only}, holder), do: 500, else: 50
    capture_runtime_namespace(port, deadline_ms, holder, attempts)
  end

  defp capture_runtime_namespace(_port, _deadline_ms, _holder, 0),
    do: {:error, {:containment_unconfirmed, :namespace_observation_unavailable}}

  defp capture_runtime_namespace(port, deadline_ms, holder, attempts) do
    with host_pid when is_integer(host_pid) <- port_os_pid(port),
         {:ok, children} <- File.read("/proc/#{host_pid}/task/#{host_pid}/children"),
         {:ok, host_namespace} <- namespace_inode("/proc/self/ns/pid"),
         {:ok, routed_children} <- routed_namespace_children(String.split(children), host_pid, host_namespace, holder),
         {:ok, [identity]} <- namespace_pid1_candidates(routed_children, host_pid, host_namespace) do
      {:ok, identity}
    else
      _failure ->
        cond do
          deadline_expired?(deadline_ms) ->
            {:error, :turn_timeout}

          not is_port(port) ->
            {:error, {:containment_unconfirmed, :namespace_observation_unavailable}}

          true ->
            Process.sleep(receive_timeout(10, deadline_ms))
            capture_runtime_namespace(port, deadline_ms, holder, attempts - 1)
        end
    end
  end

  if @functional_test_build do
    defp routed_namespace_children(children, host_pid, host_namespace, %{assurance: :synthetic_functional_only} = holder) do
      with {:ok, %{pid: pid, start_ticks: ticks}} <- NativePilot.host_supervisor_identity(holder, host_pid),
           true <- Integer.to_string(pid) in children,
           {:ok, status} <- File.read("/proc/#{pid}/status"),
           true <- process_parent(status) == host_pid,
           {:ok, ^host_namespace} <- namespace_inode("/proc/#{pid}/ns/pid"),
           {:ok, {^ticks, state}} when state not in ["Z", "X"] <- process_identity(pid) do
        {:ok, List.delete(children, Integer.to_string(pid))}
      else
        _ -> {:error, :namespace_observation_incomplete}
      end
    end
  end

  defp routed_namespace_children(children, _host_pid, _host_namespace, _holder), do: {:ok, children}

  defp namespace_pid1_candidates(children, expected_parent, host_namespace) do
    Enum.reduce_while(children, {:ok, []}, fn child, {:ok, candidates} ->
      with {pid, ""} <- Integer.parse(child),
           {:ok, status} <- File.read("/proc/#{pid}/status"),
           true <- process_parent(status) == expected_parent,
           [_, 1] <- process_namespace_pids(status),
           {:ok, inode} <- namespace_inode("/proc/#{pid}/ns/pid"),
           true <- inode != host_namespace,
           {:ok, {start_ticks, _state}} <- process_identity(pid) do
        identity = %{pid: pid, start_ticks: start_ticks, namespace_inode: inode, parent_pid: expected_parent}
        {:cont, {:ok, [identity | candidates]}}
      else
        _ -> {:halt, {:error, :namespace_observation_incomplete}}
      end
    end)
    |> case do
      {:ok, [identity]} -> {:ok, [identity]}
      {:ok, _} -> {:error, :namespace_observation_incomplete}
      error -> error
    end
  end

  defp process_parent(status) do
    case Regex.run(~r/^PPid:\s+(\d+)$/m, status) do
      [_, value] -> String.to_integer(value)
      _ -> nil
    end
  end

  defp process_namespace_pids(status) do
    case Regex.run(~r/^NSpid:\s+(.+)$/m, status) do
      [_, values] -> Enum.map(String.split(values), &String.to_integer/1)
      _ -> []
    end
  end

  defp process_identity(pid) do
    case File.read("/proc/#{pid}/stat") do
      {:ok, stat} ->
        with [_comm, fields] <- Regex.run(~r/^\d+ \(.*\) (.+)$/, stat),
             [state | after_state] <- String.split(fields),
             value when is_binary(value) <- Enum.at(after_state, 18),
             {ticks, ""} <- Integer.parse(value) do
          {:ok, {ticks, state}}
        else
          _ -> {:error, :process_state_unavailable}
        end

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp namespace_inode(path) do
    case File.read_link(path) do
      {:ok, "pid:[" <> rest} ->
        case Integer.parse(String.trim_trailing(rest, "]")) do
          {inode, ""} -> {:ok, inode}
          _ -> {:error, :namespace_state_unavailable}
        end

      {:error, reason} ->
        {:error, reason}

      _other ->
        {:error, :namespace_state_unavailable}
    end
  end

  defp verify_namespace_stopped(%{pid: pid, start_ticks: start_ticks, namespace_inode: inode}, deadline_ms) do
    with :ok <- check_deadline(deadline_ms),
         :ok <- verify_pid1_stopped(pid, start_ticks, inode),
         :ok <- check_deadline(deadline_ms) do
      :ok
    else
      _reason -> {:error, {:containment_unconfirmed, :termination_timeout}}
    end
  end

  defp verify_namespace_stopped(_identity, _deadline_ms),
    do: {:error, {:containment_unconfirmed, :termination_timeout}}

  # Linux guarantees that terminating PID namespace init sends SIGKILL to every
  # process in that namespace (pid_namespaces(7), "The namespace init process").
  # The outer port monitor is required as well; launcher death alone proves nothing.
  defp verify_pid1_stopped(pid, start_ticks, captured_inode) do
    case process_identity(pid) do
      {:ok, {^start_ticks, state}} when state in ["Z", "X"] ->
        :ok

      {:ok, {^start_ticks, _state}} ->
        case namespace_inode("/proc/#{pid}/ns/pid") do
          {:ok, ^captured_inode} -> {:error, :process_still_running}
          {:ok, _other_inode} -> {:error, :process_identity_mismatch}
          {:error, reason} -> {:error, {:process_state_unavailable, reason}}
        end

      {:ok, {_other_ticks, _state}} ->
        :ok

      {:error, :enoent} ->
        :ok

      {:error, reason} ->
        {:error, {:process_state_unavailable, reason}}
    end
  end

  defp terminate_os_process(nil), do: :ok

  defp terminate_os_process(os_pid) when is_integer(os_pid) and os_pid > 0 do
    case System.find_executable("kill") do
      nil ->
        {:error, :process_state_unavailable}

      kill ->
        run_kill(kill, ["-TERM", "-#{os_pid}"])
        run_kill(kill, ["-TERM", Integer.to_string(os_pid)])

        case await_os_process_exit(kill, os_pid, @stop_poll_attempts) do
          :ok ->
            :ok

          {:error, :process_still_running} ->
            run_kill(kill, ["-KILL", "-#{os_pid}"])
            run_kill(kill, ["-KILL", Integer.to_string(os_pid)])
            await_os_process_exit(kill, os_pid, @stop_poll_attempts * 5)

          {:error, _reason} = error ->
            error
        end
    end
  end

  defp await_os_process_exit(_kill, _os_pid, 0), do: {:error, :process_still_running}

  defp await_os_process_exit(kill, os_pid, attempts) do
    case run_kill(kill, ["-0", Integer.to_string(os_pid)]) do
      {:ok, 0} ->
        Process.sleep(@stop_poll_interval_ms)
        await_os_process_exit(kill, os_pid, attempts - 1)

      {:ok, _status} ->
        :ok

      :error ->
        {:error, :process_state_unavailable}
    end
  end

  defp run_kill(kill, args) do
    case System.cmd(kill, args, stderr_to_stdout: true) do
      {_output, status} -> {:ok, status}
    end
  rescue
    _ -> :error
  end

  defp emit_message(on_message, event, details, metadata) when is_function(on_message, 1) do
    message =
      metadata
      |> Map.merge(details)
      |> Map.put(:event, event)
      |> Map.put(:timestamp, DateTime.utc_now())

    on_message.(message)
  end

  defp metadata_from_message(port, payload) do
    port |> port_metadata(nil) |> maybe_set_usage(payload)
  end

  defp maybe_set_usage(metadata, payload) when is_map(payload) do
    usage = Map.get(payload, "usage") || Map.get(payload, :usage)

    if is_map(usage) do
      Map.put(metadata, :usage, usage)
    else
      metadata
    end
  end

  defp maybe_set_usage(metadata, _payload), do: metadata

  defp shell_escape(value) when is_binary(value) do
    "'" <> String.replace(value, "'", "'\"'\"'") <> "'"
  end

  defp default_on_message(_message), do: :ok

  defp overlay_agent_tool_context(binding, opts) do
    case Keyword.get(opts, :agent_tool_context) do
      context when is_map(context) -> Map.put(binding, :agent_tool_context, context)
      _missing -> binding
    end
  end

  defp tool_call_name(params) when is_map(params) do
    case Map.get(params, "tool") || Map.get(params, :tool) || Map.get(params, "name") ||
           Map.get(params, :name) do
      name when is_binary(name) ->
        case String.trim(name) do
          "" -> nil
          trimmed -> trimmed
        end

      _ ->
        nil
    end
  end

  defp tool_call_name(_params), do: nil

  defp tool_call_arguments(params) when is_map(params) do
    Map.get(params, "arguments") || Map.get(params, :arguments) || %{}
  end

  defp tool_call_arguments(_params), do: %{}

  defp send_message(port, message) do
    line = Jason.encode!(message) <> "\n"
    Port.command(port, line)
  end

  defp needs_input?("mcpServer/elicitation/request", payload) when is_map(payload), do: true

  defp needs_input?(method, payload)
       when is_binary(method) and is_map(payload) do
    String.starts_with?(method, "turn/") && input_required_method?(method, payload)
  end

  defp needs_input?(_method, _payload), do: false

  defp input_required_method?(method, payload) when is_binary(method) do
    method in [
      "turn/input_required",
      "turn/needs_input",
      "turn/need_input",
      "turn/request_input",
      "turn/request_response",
      "turn/provide_input",
      "turn/approval_required"
    ] || request_payload_requires_input?(payload)
  end

  defp request_payload_requires_input?(payload) do
    params = Map.get(payload, "params")
    needs_input_field?(payload) || needs_input_field?(params)
  end

  defp needs_input_field?(payload) when is_map(payload) do
    Map.get(payload, "requiresInput") == true or
      Map.get(payload, "needsInput") == true or
      Map.get(payload, "input_required") == true or
      Map.get(payload, "inputRequired") == true or
      Map.get(payload, "type") == "input_required" or
      Map.get(payload, "type") == "needs_input"
  end

  defp needs_input_field?(_payload), do: false
end
