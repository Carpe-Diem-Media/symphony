defmodule SymphonyElixir.AgentRuntime.NativePilot do
  @moduledoc """
  Runs the native C02 development slice under an already consumed pilot attempt.

  The native binaries enforce synthetic materialization and process controls.
  The selected executable can be the probe or patched standalone app-server.
  Neither path qualifies host custody or enables authenticated inference. This
  entry point always refuses model execution. Test builds can retain native
  observations bound to the existing RuntimeAttempt; other builds refuse.
  Existing C01/C03/C04 remain the only attempt authority and terminal owner.
  """

  @test_build Code.ensure_loaded?(Mix) and Mix.env() == :test

  @doc """
  Exercises only a test-harness pinned native slice, retaining nonsecret evidence.
  A completed probe returns controlled refusal, never authenticated readiness.
  Any uncertainty refuses and leaves the consumed entitlement with its caller.
  """
  @spec exercise(map(), term()) :: {:error, atom()}
  if @test_build do
    alias SymphonyElixir.{AgentRunner, Config, CredentialBoundary, Workflow}

    def exercise(binding, pin) do
      with true <- Mix.env() == :test and pin == Application.get_env(:symphony_elixir, :test_native_pilot),
           :ok <- validate_pin(binding, pin),
           {:ok, directory} <- prepare_evidence(binding, pin),
           {:ok, schema2_context} <- prepare_schema2_input(binding, pin, directory),
           {:ok, native} <- execute_native(binding, pin, directory),
           true <- native["binding"] == binding_digest(binding),
           true <- native["attempt"] == binding.attempt.runtime_attempt_id,
           true <- native["inference_succeeded"] == false,
           true <- schema2_manifest_bound?(binding, directory, native, schema2_context),
           {:error, reason} <- native_disposition(binding, pin, directory, native),
           :ok <- retain_adapter_observation(binding, pin, directory, reason) do
        {:error, reason}
      else
        _ -> {:error, :pilot_holder_native_refused}
      end
    rescue
      _ -> {:error, :pilot_holder_native_refused}
    catch
      _kind, _reason -> {:error, :pilot_holder_native_refused}
    end

    defp validate_pin(binding, pin) when is_map(pin) do
      valid? =
        binding.selection["holder_artifact_identity"] == pin.files[pin.holder] and
          binding.profile.command == pin.holder <> " app-server" and
          Enum.all?(pin.files, fn {path, digest} ->
            case File.read(path) do
              {:ok, bytes} -> sha256(bytes) == digest
              _ -> false
            end
          end)

      if valid?, do: :ok, else: {:error, :native_identity_refused}
    end

    defp validate_pin(_binding, _pin), do: {:error, :native_identity_refused}

    defp prepare_evidence(binding, pin) do
      directory = Path.join(pin.evidence_root, binding.attempt.runtime_attempt_id)

      with :ok <- File.mkdir_p(pin.evidence_root),
           :ok <- File.mkdir(directory),
           :ok <- File.chmod(directory, 0o700),
           :ok <- File.write(Path.join(directory, "binding.json"), Jason.encode!(binding), [:exclusive]),
           :ok <- File.chmod(Path.join(directory, "binding.json"), 0o600) do
        {:ok, directory}
      end
    end

    defp prepare_schema2_input(binding, %{schema2: mode, pinned_codex: true} = pin, directory)
         when mode in [:refusal, :interrupt] do
      with {:ok, settings} <- Config.settings(),
           {:ok, %{prompt_template: prompt}} <- Workflow.load(),
           {:ok, authority} <- Config.pilot_configuration_snapshot(settings, prompt),
           true <- authority.identity == binding.grant.config_identity,
           true <- authority.role_policy.profile_name == binding.attempt.runtime_profile,
           :ok <- AgentRunner.validate_pilot_checkout(binding.workspace, binding.grant, authority.git),
           {:ok, bytes} <- File.read(pin.model_catalog),
           true <- sha256(bytes) == pin.files[pin.model_catalog],
           {:ok, %{"models" => [%{"slug" => slug}]} = catalog} <- Jason.decode(bytes),
           true <- is_binary(slug) and slug == binding.profile.model do
        context = schema2_context(binding, authority.role_policy, catalog, slug, prompt, directory, mode)
        path = Path.join(directory, "schema2-input.json")

        with :ok <- File.write(path, Jason.encode!(%{context: context, cancel: mode == :interrupt}), [:exclusive]),
             :ok <- File.chmod(path, 0o600) do
          {:ok, Map.new(context, fn {key, value} -> {Atom.to_string(key), value} end)}
        end
      else
        _ -> {:error, :native_schema2_input_refused}
      end
    end

    defp prepare_schema2_input(_binding, pin, _directory) do
      if Map.has_key?(pin, :schema2), do: {:error, :native_schema2_input_refused}, else: {:ok, nil}
    end

    defp schema2_context(binding, policy, catalog, slug, prompt, directory, mode) do
      %{
        project_id: binding.grant.project_id,
        work_item_id: binding.grant.work_item_id,
        role: "Planner",
        binding_id: binding_digest(binding),
        attempt_id: binding.attempt.runtime_attempt_id,
        grant_id: binding.grant |> :erlang.term_to_binary([:deterministic]) |> sha256(),
        configuration_digest: binding.grant.config_identity,
        source_commit: binding.grant.source_commit,
        source_tree: binding.grant.source_tree,
        policy_root: policy.canonical_root,
        policy_text: policy.bytes,
        policy_digest: sha256(policy.bytes),
        holder_sha256: binding.selection["holder_artifact_identity"],
        holder_profile: "H100_FUNCTIONAL_CODEX_SYNTHETIC_V1",
        holder_profile_digest: binding.selection["holder_profile_identity"],
        permission_reference: binding.selection["host_permission_ref"],
        host_identity: binding.selection["host_id"],
        boot_identity: binding.selection["host_boot_id"],
        credential_generation: to_string(binding.selection["credential_generation"]),
        model_slug: slug,
        model_catalog: catalog,
        prompt_text: prompt,
        text_digest: sha256(prompt),
        workspace: binding.workspace,
        home: Path.join(directory, "home"),
        codex_home: Path.join(directory, "codex-home"),
        wait_for_interrupt: mode == :interrupt
      }
    end

    defp schema2_manifest_bound?(_binding, _directory, _native, nil), do: true

    defp schema2_manifest_bound?(binding, directory, native, expected) do
      with {:ok, bytes} when byte_size(bytes) <= 131_072 <- File.read(Path.join(directory, "manifest.json")),
           true <- sha256(bytes) == native["manifest_sha256"],
           {:ok, %{"schema" => 2, "profile" => "H100_FUNCTIONAL_CODEX_SYNTHETIC_V1", "context" => context} = manifest} <- Jason.decode(bytes) do
        manifest["binding"] == binding_digest(binding) and
          manifest["attempt"] == binding.attempt.runtime_attempt_id and
          manifest["holder_sha256"] == binding.selection["holder_artifact_identity"] and
          Map.drop(context, ~w(context_digest model_catalog_digest)) == expected
      else
        _ -> false
      end
    end

    defp retain_adapter_observation(binding, %{schema2: _}, directory, reason) do
      record = %{
        binding: binding_digest(binding),
        attempt: binding.attempt.runtime_attempt_id,
        outcome: reason,
        synthetic_stop_verified: reason in [:pilot_holder_native_controlled_refusal, :pilot_holder_native_interrupted],
        operational_namespace_qualified: false
      }

      path = Path.join(directory, "adapter-observation.json")

      case File.open(path, [:write, :binary, :exclusive], &sync_observation(&1, record)) do
        {:ok, :ok} -> :ok
        _ -> {:error, :native_observation_refused}
      end
    end

    defp retain_adapter_observation(_binding, _pin, _directory, _reason), do: :ok

    defp sync_observation(io, record) do
      with :ok <- IO.binwrite(io, Jason.encode!(record)), do: :file.sync(io)
    end

    defp native_disposition(binding, %{schema2: mode}, directory, native) do
      {terminal, disposition, reason} =
        case mode do
          :refusal -> {"failed", "CONTROLLED_REFUSAL", :pilot_holder_native_controlled_refusal}
          :interrupt -> {"interrupted", "INTERRUPTED", :pilot_holder_native_interrupted}
        end

      with %{
             "schema2" => true,
             "scope" => "SYNTHETIC_NATIVE_NOT_ROUTED_C01_QUALIFICATION",
             "qualified_host" => false,
             "native_exec" => true,
             "protocol_verified" => true,
             "consumed" => true,
             "replay_refused" => true,
             "stop_verified" => true,
             "native_disposal_verified" => true,
             "materialization_count" => 1,
             "guard_exit_code" => 0,
             "host_exit_code" => 0,
             "disposition" => ^disposition,
             "protocol_evidence" => events
           } <- native,
           true <- core_terminal?(events, terminal),
           true <- synthetic_stop?(binding, directory) do
        {:error, reason}
      else
        _ -> {:error, :pilot_holder_native_refused}
      end
    end

    defp native_disposition(_binding, _pin, _directory, %{"disposition" => "CONTROLLED_REFUSAL", "stop_verified" => true}),
      do: {:error, :pilot_holder_native_controlled_refusal}

    defp native_disposition(_binding, _pin, _directory, _native), do: {:error, :pilot_holder_native_refused}

    defp core_terminal?(
           [
             %{"id" => 1},
             %{"id" => 2, "result" => %{"thread" => %{"id" => thread}}},
             %{"method" => "thread/started", "params" => %{"thread" => %{"id" => thread}}},
             %{"id" => 3, "result" => %{"turn" => %{"id" => turn}}},
             %{"method" => "turn/started", "params" => %{"threadId" => thread, "turn" => %{"id" => turn}}},
             event,
             %{"method" => "turn/completed", "params" => %{"threadId" => thread, "turn" => %{"id" => turn, "status" => status} = result}}
           ],
           status
         )
         when is_binary(thread) and thread != "" and is_binary(turn) and turn != "" do
      case {status, event} do
        {"failed", %{"method" => "error", "params" => %{"threadId" => ^thread, "turnId" => ^turn, "willRetry" => false, "error" => error}}} ->
          error == %{"message" => "SYMPHONY_PROVIDER_BOUNDARY_UNAVAILABLE", "codexErrorInfo" => "other"} and result["error"] == error

        {"interrupted", %{"id" => 4}} ->
          is_nil(result["error"])

        _ ->
          false
      end
    end

    defp core_terminal?(_events, _terminal), do: false

    defp synthetic_stop?(binding, directory) do
      digest = binding_digest(binding)
      attempt = binding.attempt.runtime_attempt_id
      markers = ~w(consumed channel-closed schema2-clean-exit guard-reaped disposed)

      with true <- Enum.all?(markers, &(File.read(Path.join(directory, &1)) == {:ok, digest})),
           {:ok, journal} when byte_size(journal) <= 16_384 <- File.read(Path.join(directory, "events.jsonl")),
           events <- journal |> String.split("\n", trim: true) |> Enum.map(&Jason.decode!/1),
           true <- Enum.all?(events, &(&1["binding"] == digest and &1["attempt"] == attempt)),
           [
             %{"pid" => guard, "state" => "HOST_PERMISSION_VALIDATED"},
             %{"pid" => pid, "state" => "BOOTSTRAP_CREATED"} | child_events
           ]
           when is_integer(guard) and guard > 1 and is_integer(pid) and pid > 1 and pid != guard <- events,
           true <- Enum.all?(child_events, &(&1["pid"] == pid)) do
        states = Enum.map(child_events, & &1["state"])
        timeline = ~w(MATERIALIZATION_INTENT SYNTHETIC_MATERIALIZED CREDENTIAL_CHANNEL_CLOSED SCHEMA2_CHANNEL_CLOSED_BEFORE_RPC TERMINATION_REQUESTED)
        stop = ~w(TERMINATION_VERIFIED SCHEMA2_CLEAN_EXIT GUARD_REAPED)

        Enum.take(states, length(timeline)) == timeline and
          Enum.sort(Enum.slice(states, length(timeline), length(stop))) == Enum.sort(stop) and
          Enum.find_index(states, &(&1 == "SCHEMA2_CLEAN_EXIT")) < Enum.find_index(states, &(&1 == "GUARD_REAPED")) and
          Enum.drop(states, length(timeline) + length(stop)) == ["DISPOSAL_VERIFIED"]
      else
        _ -> false
      end
    end

    defp execute_native(binding, pin, directory) do
      remaining = binding.absolute_deadline_ms - System.monotonic_time(:millisecond)

      schema2? = Map.has_key?(pin, :schema2)

      if remaining >= if(schema2?, do: 6_000, else: 2_000) do
        args = [
          "-I",
          pin.driver,
          "--root",
          directory,
          "--binding",
          binding_digest(binding),
          "--attempt",
          binding.attempt.runtime_attempt_id,
          "--holder",
          pin.holder,
          "--fault",
          pin.fault,
          "--duration-ms",
          to_string(min(remaining - 1_000, if(schema2?, do: 5_000, else: 2_500)))
        ]

        args = if Map.get(pin, :pinned_codex, false), do: args ++ ["--pinned-codex"], else: args

        args = if schema2?, do: args ++ ["--schema2"], else: args

        env = CredentialBoundary.routed_port_env([], Path.join(directory, "home"), Path.join(directory, "codex-home"))
        port = Port.open({:spawn_executable, ~c"/usr/bin/python3"}, [:binary, :exit_status, :use_stdio, :stderr_to_stdout, args: args, env: env])

        with {:ok, native} <- collect_native(port, binding.absolute_deadline_ms, <<>>),
             {:ok, bytes} <- File.read(Path.join(directory, "correlation.json")),
             {:ok, %{"binding" => retained, "native" => ^native}} <- Jason.decode(bytes),
             true <- retained == Jason.decode!(Jason.encode!(binding)) do
          {:ok, native}
        end
      else
        {:error, :native_deadline_refused}
      end
    end

    defp collect_native(port, deadline, output) do
      remaining = deadline - System.monotonic_time(:millisecond)

      if remaining > 0 do
        receive_native(port, deadline, output, remaining)
      else
        close_native_port(port)
        {:error, :native_deadline_refused}
      end
    end

    defp receive_native(port, deadline, output, remaining) do
      receive do
        {^port, {:data, bytes}} when byte_size(output) + byte_size(bytes) <= 65_536 ->
          collect_native(port, deadline, output <> bytes)

        {^port, {:exit_status, 0}} ->
          Jason.decode(output)

        {^port, _other} ->
          close_native_port(port)
          {:error, :native_observation_refused}
      after
        remaining ->
          close_native_port(port)
          {:error, :native_deadline_refused}
      end
    end

    defp close_native_port(port) do
      Port.close(port)
    rescue
      ArgumentError -> :ok
    end

    defp binding_digest(binding), do: binding |> :erlang.term_to_binary([:deterministic]) |> sha256()
    defp sha256(bytes), do: :crypto.hash(:sha256, bytes) |> Base.encode16(case: :lower)
  else
    def exercise(_binding, _pin), do: {:error, :pilot_holder_boundary_unavailable}
  end
end
