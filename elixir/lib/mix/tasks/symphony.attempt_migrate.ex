defmodule Mix.Tasks.Symphony.AttemptMigrate do
  use Mix.Task

  @shortdoc "Explicitly migrate the configured attempt ledger from schema 1 to 2"

  @moduledoc """
  Runs the offline whole-ledger attempt migration. Arguments are
  `PROJECT_NAMESPACE TRACKER_IDENTITY_SHA256 AUTHORITY_REF` for migration,
  or `--resume` / `--abort` followed by those same arguments.
  """

  @impl Mix.Task
  def run([namespace, identity_digest, authority_ref]) do
    run_migration(:migrate, namespace, identity_digest, authority_ref)
  end

  def run(["--resume", namespace, identity_digest, authority_ref]) do
    run_migration(:resume, namespace, identity_digest, authority_ref)
  end

  def run(["--abort", namespace, identity_digest, authority_ref]) do
    run_migration(:abort, namespace, identity_digest, authority_ref)
  end

  def run(_),
    do: Mix.raise("usage: mix symphony.attempt_migrate [--resume|--abort] PROJECT_NAMESPACE TRACKER_IDENTITY_SHA256 AUTHORITY_REF")

  defp run_migration(operation, namespace, identity_digest, authority_ref) do
    alias SymphonyElixir.AgentRuntime.{AttemptLedger, AttemptLedgerMigration}

    path = AttemptLedger.path_for(namespace)

    request = %{
      project_namespace: namespace,
      tracker_identity_sha256: identity_digest,
      authority_ref: authority_ref,
      source_schema: 1,
      target_schema: 2
    }

    result =
      case operation do
        :migrate -> AttemptLedgerMigration.migrate_v1_to_v2(path, request)
        :resume -> AttemptLedgerMigration.resume_v1_to_v2(path, request)
        :abort -> AttemptLedgerMigration.abort_v1_to_v2(path, request)
      end

    case result do
      :ok -> Mix.shell().info("attempt ledger migration aborted")
      {:ok, receipt} -> Mix.shell().info(inspect(receipt, pretty: true))
      {:error, reason} -> Mix.raise("attempt ledger maintenance failed: #{reason}")
    end
  end
end
