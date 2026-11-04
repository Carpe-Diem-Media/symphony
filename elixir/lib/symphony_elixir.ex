defmodule SymphonyElixir do
  @moduledoc """
  Entry point for the Symphony orchestrator.
  """

  @doc """
  Start the agent runtime in the current BEAM node.
  """
  @spec start_link() :: Supervisor.on_start()
  def start_link do
    with {:ok, settings} <- SymphonyElixir.Config.settings(),
         :ok <- SymphonyElixir.Config.validate_attempt_boundary(settings) do
      case runtime_start_decision(settings) do
        :legacy -> SymphonyElixir.AgentRuntimeSupervisor.start_link([])
        :gate2_dormant -> {:error, :gate2_dormant}
        {:error, reason} -> {:error, reason}
      end
    end
  end

  @doc false
  @spec runtime_start_decision(SymphonyElixir.Config.Schema.t()) ::
          :legacy | :gate2_dormant | {:error, :gate2_profile_incomplete | :invalid_request}
  def runtime_start_decision(%{agent: %{attempt_boundary: %{mode: "legacy"}}}), do: :legacy
  def runtime_start_decision(%{agent: %{attempt_boundary: %{mode: "gate2_foundation"}}}), do: :gate2_dormant
  def runtime_start_decision(%{agent: %{attempt_boundary: %{mode: "gate2_enforced"}}}), do: {:error, :gate2_profile_incomplete}
  def runtime_start_decision(_settings), do: {:error, :invalid_request}
end

defmodule SymphonyElixir.Application do
  @moduledoc """
  OTP application entrypoint that starts core supervisors and workers.
  """

  use Application

  alias SymphonyElixir.Plane.WebhookIngressMetrics

  @dialyzer {:nowarn_function, start_burrito_cli: 0}

  @impl true
  def start(_type, _args) do
    if burrito_runtime?() do
      start_burrito_cli()
    else
      start_runtime()
    end
  end

  @doc false
  @spec start_runtime() :: Supervisor.on_start()
  def start_runtime do
    with {:ok, settings} <- SymphonyElixir.Config.settings(),
         :ok <- SymphonyElixir.Config.validate_attempt_boundary(settings),
         :legacy <- SymphonyElixir.runtime_start_decision(settings) do
      do_start_runtime()
    else
      :gate2_dormant -> {:error, :gate2_dormant}
      {:error, reason} -> {:error, reason}
    end
  end

  defp do_start_runtime do
    :ok = SymphonyElixir.LogFile.configure()
    :ok = WebhookIngressMetrics.initialize()

    children = [
      {Phoenix.PubSub, name: SymphonyElixir.PubSub},
      SymphonyElixir.WorkflowStore,
      {SymphonyElixir.AgentRuntime.RuntimeIsolation, name: SymphonyElixir.AgentRuntime.RuntimeIsolation},
      SymphonyElixir.AgentRuntimeSupervisor,
      SymphonyElixir.HttpServer,
      SymphonyElixir.StatusDashboard
    ]

    Supervisor.start_link(
      children,
      strategy: :one_for_one,
      name: SymphonyElixir.Supervisor
    )
  end

  @impl true
  def stop(_state) do
    SymphonyElixir.StatusDashboard.render_offline_status()
    :ok
  end

  defp start_burrito_cli do
    Task.start_link(fn ->
      SymphonyElixir.CLI.main(
        plain_arguments(),
        &start_runtime/0
      )
    end)
  end

  defp burrito_runtime?, do: System.get_env("__BURRITO") == "1"

  defp plain_arguments, do: Enum.map(:init.get_plain_arguments(), &to_string/1)
end
