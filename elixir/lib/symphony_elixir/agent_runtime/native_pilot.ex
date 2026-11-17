defmodule SymphonyElixir.AgentRuntime.NativePilot do
  @moduledoc """
  Runs the native C02 development slice under an already consumed pilot attempt.

  The native binaries enforce synthetic materialization and process controls.
  They do not implement the patched Codex holder or qualify host custody. This
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
    alias SymphonyElixir.CredentialBoundary

    def exercise(binding, pin) do
      with true <- Mix.env() == :test and pin == Application.get_env(:symphony_elixir, :test_native_pilot),
           :ok <- validate_pin(binding, pin),
           {:ok, directory} <- prepare_evidence(binding, pin),
           {:ok, native} <- execute_native(binding, pin, directory),
           true <- native["binding"] == binding_digest(binding),
           true <- native["attempt"] == binding.attempt.runtime_attempt_id,
           true <- native["disposition"] == "CONTROLLED_REFUSAL" and native["stop_verified"] == true,
           true <- native["inference_succeeded"] == false do
        {:error, :pilot_holder_native_controlled_refusal}
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

    defp execute_native(binding, pin, directory) do
      remaining = binding.absolute_deadline_ms - System.monotonic_time(:millisecond)

      if remaining >= 2_000 do
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
          to_string(min(remaining - 1_000, 2_500))
        ]

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
