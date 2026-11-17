defmodule SymphonyElixir.PilotCheckoutTest do
  use ExUnit.Case, async: false

  alias SymphonyElixir.{AgentRunner, CredentialBoundary, PathSafety}

  @moduletag :f03

  setup do
    root = Path.join(System.tmp_dir!(), "pilot-checkout-proof-#{System.unique_integer([:positive])}")
    source = Path.join(root, "source")
    File.mkdir_p!(Path.join(source, "nested"))
    git!(source, ["init", "-q"])
    File.write!(Path.join(source, "sample.txt"), "approved bytes\n")
    File.write!(Path.join(source, "nested/value.txt"), "nested bytes\n")
    File.write!(Path.join(source, "tab\tand-newline\n.txt"), "NUL-delimited path proof\n")
    File.write!(Path.join(source, "executable.sh"), "#!/bin/sh\nexit 0\n")
    File.chmod!(Path.join(source, "executable.sh"), 0o755)
    File.ln_s!("sample.txt", Path.join(source, "source-link"))
    git!(source, ["add", "--all"])
    git!(source, ["-c", "user.name=Offline fixture", "-c", "user.email=offline@example.invalid", "-c", "commit.gpgSign=false", "commit", "-qm", "Synthetic checkout fixture"])
    [commit, tree] = git!(source, ["rev-parse", "HEAD", "HEAD^{tree}"]) |> String.split()
    assert {:ok, git} = PathSafety.trusted_executable_identity("/usr/bin/git")
    on_exit(fn -> File.rm_rf!(root) end)
    {:ok, root: root, source: source, grant: %{source_commit: commit, source_tree: tree}, git: git}
  end

  test "ordinary checkout verifies actual modes, links and NUL-delimited tracked paths", ctx do
    before_index = File.read!(Path.join(ctx.source, ".git/index"))
    assert :ok = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
    assert File.read!(Path.join(ctx.source, ".git/index")) == before_index
  end

  for flag <- ["--assume-unchanged", "--skip-worktree"] do
    @tag index_flag: flag
    test "valid tracked bytes pass without modifying #{flag}", ctx do
      git!(ctx.source, ["update-index", ctx.index_flag, "sample.txt"])
      index = Path.join(ctx.source, ".git/index")
      before_index = File.read!(index)
      assert :ok = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
      assert File.read!(index) == before_index
    end
  end

  test "ordinary linked-worktree proof does not weaken the separate credential boundary", ctx do
    linked = Path.join(ctx.root, "linked")
    git!(ctx.source, ["worktree", "add", "--quiet", "--detach", linked, ctx.grant.source_commit])
    assert File.regular?(Path.join(linked, ".git"))
    index = git!(linked, ["rev-parse", "--path-format=absolute", "--git-path", "index"]) |> String.trim()
    before_index = File.read!(index)
    assert :ok = AgentRunner.validate_pilot_checkout(linked, ctx.grant, ctx.git)
    assert File.read!(index) == before_index
    # The normal AgentRunner still requires credential/ownership admission.
    assert {:error, _} = CredentialBoundary.workspace_credential_residue(linked)
  end

  test "a repository subdirectory cannot stand in for its complete approved worktree", ctx do
    assert {:error, :pilot_source_mismatch} =
             AgentRunner.validate_pilot_checkout(Path.join(ctx.source, "nested"), ctx.grant, ctx.git)
  end

  test "core.worktree redirection refuses even when both directories have approved bytes", ctx do
    linked = Path.join(ctx.root, "linked")
    git!(ctx.source, ["worktree", "add", "--quiet", "--detach", linked, ctx.grant.source_commit])
    git!(ctx.source, ["config", "core.worktree", linked])
    config = Path.join(ctx.source, ".git/config")
    before_config = File.read!(config)
    assert {:error, :pilot_source_mismatch} = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
    assert File.read!(config) == before_config
  end

  test "missing or unreadable tracked bytes refuse despite skip-worktree", ctx do
    file = Path.join(ctx.source, "sample.txt")
    git!(ctx.source, ["update-index", "--skip-worktree", "sample.txt"])
    File.chmod!(file, 0o000)
    assert {:error, :pilot_source_mismatch} = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
    File.rm!(file)
    assert {:error, :pilot_source_mismatch} = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
  end

  test "source mode changes refuse even when Git core.filemode ignores them", ctx do
    git!(ctx.source, ["config", "core.filemode", "false"])
    File.chmod!(Path.join(ctx.source, "sample.txt"), 0o755)
    assert {:error, :pilot_source_mismatch} = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
  end

  test "a changed tracked symlink refuses without following its target", ctx do
    git!(ctx.source, ["update-index", "--assume-unchanged", "source-link"])
    path = Path.join(ctx.source, "source-link")
    File.rm!(path)
    File.ln_s!("nested/value.txt", path)
    assert {:error, :pilot_source_mismatch} = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
  end

  test "a symlinked parent cannot redirect tracked reads outside the workspace", ctx do
    git!(ctx.source, ["update-index", "--assume-unchanged", "nested/value.txt"])
    outside = Path.join(ctx.root, "outside")
    File.mkdir_p!(outside)
    File.write!(Path.join(outside, "value.txt"), "nested bytes\n")
    File.rm_rf!(Path.join(ctx.source, "nested"))
    File.ln_s!(outside, Path.join(ctx.source, "nested"))
    assert {:error, :pilot_source_mismatch} = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
  end

  test "all inherited Git repository, index, object and configuration selectors are isolated", ctx do
    values = %{
      "GIT_DIR" => "/missing/offline/git-dir",
      "GIT_WORK_TREE" => "/missing/offline/worktree",
      "GIT_COMMON_DIR" => "/missing/offline/common",
      "GIT_INDEX_FILE" => "/missing/offline/index",
      "GIT_OBJECT_DIRECTORY" => "/missing/offline/objects",
      "GIT_ALTERNATE_OBJECT_DIRECTORIES" => "/missing/offline/alternates",
      "GIT_CONFIG_GLOBAL" => "/missing/offline/global",
      "GIT_CONFIG_SYSTEM" => "/missing/offline/system",
      "GIT_CONFIG_COUNT" => "invalid",
      "GIT_CONFIG_PARAMETERS" => "invalid",
      "GIT_CONFIG_KEY_0" => "core.worktree",
      "GIT_CONFIG_VALUE_0" => "/missing/offline/worktree"
    }

    prior = Map.new(values, fn {key, _} -> {key, System.get_env(key)} end)
    System.put_env(values)

    try do
      assert :ok = AgentRunner.validate_pilot_checkout(ctx.source, ctx.grant, ctx.git)
      assert Map.new(values, fn {key, _} -> {key, System.get_env(key)} end) == values
    after
      Enum.each(prior, fn {key, value} ->
        if value, do: System.put_env(key, value), else: System.delete_env(key)
      end)
    end
  end

  defp git!(workspace, args) do
    {output, 0} = System.cmd("/usr/bin/git", ["--no-optional-locks", "-c", "core.hooksPath=/dev/null", "-C", workspace | args], stderr_to_stdout: true)
    output
  end
end
