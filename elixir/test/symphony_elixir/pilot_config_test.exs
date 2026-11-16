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

  @tag :authority_binding_correction
  test "pilot snapshot includes selected Planner bytes and the trusted Git identity" do
    settings = settings()
    assert {:ok, snapshot} = Config.pilot_configuration_snapshot(settings, "prompt")
    assert snapshot.role_policy.bytes == File.read!(snapshot.role_policy.path)
    assert snapshot.git.path == "/usr/bin/git"
    assert snapshot.git.sha256 == Base.encode16(:crypto.hash(:sha256, File.read!("/usr/bin/git")), case: :lower)
    assert snapshot.identity == Config.pilot_configuration_identity(settings, "prompt")
  end

  @tag :authority_binding_correction
  test "trusted executable verification refuses missing, user-owned and symlink substitutes" do
    root = Path.join(System.tmp_dir!(), "pilot-git-trust-#{System.unique_integer([:positive])}")
    File.mkdir_p!(root)
    candidate = Path.join(root, "git")

    try do
      assert {:error, :untrusted_path} = SymphonyElixir.PathSafety.trusted_executable_identity(candidate)
      File.write!(candidate, "#!/bin/sh\nexit 0\n")
      File.chmod!(candidate, 0o755)
      assert {:error, :untrusted_path} = SymphonyElixir.PathSafety.trusted_executable_identity(candidate)
      File.rm!(candidate)
      File.ln_s!("/usr/bin/git", candidate)
      assert {:error, :untrusted_path} = SymphonyElixir.PathSafety.trusted_executable_identity(candidate)
      assert {:ok, %{path: "/usr/bin/git"}} = SymphonyElixir.PathSafety.trusted_executable_identity("/usr/bin/git")
    after
      File.rm_rf!(root)
    end
  end

  test "schema retains a configured grant and rejects explicit null" do
    settings = settings()
    grant = grant(settings)
    assert {:ok, parsed} = Schema.parse(%{agent: %{pilot: grant}})
    assert parsed.agent.pilot == grant
    assert {:error, _reason} = Schema.parse(%{agent: %{pilot: nil}})
  end
end
