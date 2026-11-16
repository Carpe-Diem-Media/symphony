defmodule SymphonyElixir.PilotConfigTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.Config
  alias SymphonyElixir.Config.Schema

  @project "11111111-1111-4111-8111-111111111111"
  @item "22222222-2222-4222-8222-222222222222"

  defp settings do
    {:ok, settings} =
      Schema.parse(%{
        symphony: %{project_id: "pilot-test"},
        tracker: %{kind: "plane", workspace_slug: "disposable", project_id: @project},
        agent: %{routing: "routed", max_concurrent_agents: 1}
      })

    settings
  end

  defp grant(settings) do
    %{
      "project_id" => "pilot-test",
      "plane_project_id" => @project,
      "work_item_id" => @item,
      "responsibility" => "planning",
      "source_commit" => String.duplicate("a", 40),
      "source_tree" => String.duplicate("b", 40),
      "config_identity" => Config.pilot_configuration_identity(settings, "Inspect one file."),
      "runtime_lineage" => "owner-issued-lineage",
      "deadline_ms" => 120_000
    }
  end

  test "pilot is absent unless explicitly configured" do
    assert {:ok, nil} = Config.pilot_binding(settings(), "Inspect one file.")
  end

  test "exact nonsecret effective configuration and prompt bind the grant" do
    settings = settings()
    grant = grant(settings)
    configured = put_in(settings.agent.pilot, grant)
    assert {:ok, binding} = Config.pilot_binding(configured, "Inspect one file.")
    assert binding.work_item_id == @item
    assert binding.plane_project_id == @project
    assert binding.deadline_ms == 120_000
    assert {:error, :pilot_configuration_invalid} = Config.pilot_binding(configured, "Different prompt.")
    changed = put_in(configured.codex.command, "different-codex app-server")
    assert {:error, :pilot_configuration_invalid} = Config.pilot_binding(changed, "Inspect one file.")
  end

  test "pilot grant rejects unknown keys, other roles, scope drift, legacy routing and Gate 2" do
    settings = settings()
    grant = grant(settings)

    for invalid <- [
          Map.put(grant, "extra", true),
          Map.put(grant, "responsibility", "implementation"),
          Map.put(grant, "plane_project_id", @item),
          Map.put(grant, "work_item_id", "not-a-uuid"),
          Map.put(grant, "deadline_ms", 0)
        ] do
      assert {:error, :pilot_configuration_invalid} =
               Config.pilot_binding(put_in(settings.agent.pilot, invalid), "Inspect one file.")
    end

    for changed <- [put_in(settings.agent.routing, "legacy"), put_in(settings.agent.attempt_boundary.mode, "gate2_foundation")] do
      assert {:error, :pilot_configuration_invalid} =
               Config.pilot_binding(put_in(changed.agent.pilot, grant), "Inspect one file.")
    end
  end

  test "secret value changes do not require exposing or hashing credentials" do
    settings = settings()
    first = put_in(settings.tracker.api_key, "synthetic-secret-one")
    second = put_in(settings.tracker.api_key, "synthetic-secret-two")

    assert Config.pilot_configuration_identity(first, "prompt") ==
             Config.pilot_configuration_identity(second, "prompt")
  end

  test "schema retains a configured grant and rejects explicit null" do
    settings = settings()
    grant = grant(settings)
    assert {:ok, parsed} = Schema.parse(%{agent: %{pilot: grant}})
    assert parsed.agent.pilot == grant
    assert {:error, _reason} = Schema.parse(%{agent: %{pilot: nil}})
  end
end
