defmodule SymphonyElixir.AgentRuntime.AttemptLedgerMigration do
  @moduledoc "Offline, whole-ledger schema migration for the attempt ledger."

  alias SymphonyElixir.AgentRuntime.AttemptLedger
  alias SymphonyElixir.Config.Schema

  @journal_version 1
  @journal_keys [
    :authority_ref,
    :current_record_count,
    :history_record_count,
    :migration_id,
    :phase,
    :project_namespace,
    :schema_version,
    :source_records_sha256,
    :source_schema,
    :stage_basename,
    :target_records_sha256,
    :target_schema,
    :tracker_identity_sha256
  ]
  @receipt_keys [
    :committed,
    :current_record_count,
    :history_record_count,
    :migration_id,
    :project_namespace,
    :schema_version,
    :source_records_sha256,
    :target_records_sha256,
    :target_schema
  ]
  @committed_journal_extra [:committed, :receipt_sha256]

  @type migration_request :: %{
          project_namespace: String.t(),
          tracker_identity_sha256: String.t(),
          authority_ref: String.t(),
          source_schema: 1,
          target_schema: 2
        }
  @type migration_receipt :: %{
          schema_version: 1,
          migration_id: String.t(),
          project_namespace: String.t(),
          source_records_sha256: String.t(),
          target_records_sha256: String.t(),
          current_record_count: non_neg_integer(),
          history_record_count: non_neg_integer(),
          target_schema: 2,
          committed: true
        }

  @spec migrate_v1_to_v2(Path.t(), migration_request()) ::
          {:ok, migration_receipt()} | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def migrate_v1_to_v2(path, request) when is_binary(path) and is_map(request) do
    with :ok <- validate_invocation(path, request) do
      with_lock(path, fn -> migrate_locked(path, request) end)
    end
  rescue
    _ -> {:error, :migration_source_invalid}
  end

  def migrate_v1_to_v2(_, _), do: {:error, :migration_not_permitted}

  @spec resume_v1_to_v2(Path.t(), migration_request()) ::
          {:ok, migration_receipt()} | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def resume_v1_to_v2(path, request) when is_binary(path) and is_map(request) do
    with :ok <- validate_invocation(path, request) do
      with_lock(path, fn -> resume_locked(path, request) end)
    end
  rescue
    _ -> {:error, :migration_source_invalid}
  end

  def resume_v1_to_v2(_, _), do: {:error, :migration_not_permitted}

  @spec abort_v1_to_v2(Path.t(), migration_request()) ::
          :ok | {:error, SymphonyElixir.AgentRuntime.AttemptBoundary.error()}
  def abort_v1_to_v2(path, request) when is_binary(path) and is_map(request) do
    with :ok <- validate_invocation(path, request) do
      with_lock(path, fn -> abort_locked(path, request) end)
    end
  rescue
    _ -> {:error, :migration_source_invalid}
  end

  def abort_v1_to_v2(_, _), do: {:error, :migration_not_permitted}

  @doc false
  @spec admission_check(Path.t()) :: :ok | {:error, :migration_in_progress}
  def admission_check(path) when is_binary(path) do
    case read_journal(path) do
      :missing -> :ok
      {:ok, journal} -> if committed_journal_matches?(path, journal), do: :ok, else: {:error, :migration_in_progress}
      _ -> {:error, :migration_in_progress}
    end
  rescue
    _ -> {:error, :migration_in_progress}
  end

  @doc false
  @spec admission_check(Path.t(), String.t(), map(), 1 | 2) :: :ok | {:error, :migration_in_progress}
  def admission_check(path, namespace, identity, schema) do
    case read_journal(path) do
      :missing when schema == 1 ->
        :ok

      :missing ->
        {:error, :migration_in_progress}

      {:ok, journal} ->
        if admitted_committed_journal?(journal, path, namespace, identity, schema) do
          :ok
        else
          {:error, :migration_in_progress}
        end

      _ ->
        {:error, :migration_in_progress}
    end
  rescue
    _ -> {:error, :migration_in_progress}
  end

  defp admitted_committed_journal?(journal, path, namespace, identity, 2) do
    valid_journal?(journal, path) and journal.phase == :committed and
      journal.project_namespace == namespace and
      journal.tracker_identity_sha256 == identity_digest(identity)
  end

  defp admitted_committed_journal?(_journal, _path, _namespace, _identity, _schema), do: false

  @doc false
  @spec with_open_lock(Path.t(), (-> term())) :: {:ok, term()} | {:error, :migration_in_progress}
  def with_open_lock(path, fun) when is_binary(path) and is_function(fun, 0) do
    case acquire_host_lock(path) do
      {:ok, port} ->
        try do
          {:ok, fun.()}
        after
          release_host_lock(port)
        end

      _ ->
        {:error, :migration_in_progress}
    end
  end

  defp validate_invocation(path, request) do
    if valid_request?(request),
      do: validate_canonical_invocation(path, request.project_namespace),
      else: {:error, :migration_not_permitted}
  end

  defp validate_canonical_invocation(path, namespace) do
    canonical = AttemptLedger.path_for(namespace)

    cond do
      Path.expand(path) != canonical -> {:error, :migration_not_permitted}
      not path_has_no_symlink_component?(canonical) -> {:error, :migration_not_permitted}
      app_started?() -> {:error, :migration_not_permitted}
      true -> :ok
    end
  end

  defp migrate_locked(path, request) do
    namespace = request.project_namespace

    with :missing <- read_journal(path),
         :ok <- ensure_source_file(path),
         :ok <- ensure_no_open_handle(path),
         {:ok, source_rows} <- read_rows(path, :migration_source_invalid),
         {:ok, identity} <- stored_identity(source_rows),
         true <- identity_digest(identity) == request.tracker_identity_sha256,
         :ok <- validate_source(path, namespace, identity),
         target_rows <- upgrade_rows(source_rows),
         journal <- new_journal(path, request, source_rows, target_rows),
         :ok <- write_journal(path, journal),
         :ok <- crash_checkpoint(:journal_synced),
         :ok <- create_stage(path, journal, target_rows),
         :ok <- maybe_corrupt_stage(path, journal),
         :ok <- crash_checkpoint(:stage_synced),
         :ok <- validate_stage(path, journal, namespace, identity),
         journal <- Map.put(journal, :phase, :staged),
         :ok <- write_journal(path, journal),
         :ok <- crash_checkpoint(:stage_validated),
         :ok <- ensure_no_open_handle(path),
         :ok <- ensure_no_open_handle(stage_path(path, journal)),
         :ok <- replace_canonical(path, journal),
         :ok <- crash_checkpoint(:renamed),
         :ok <- sync_parent_after_replace(path),
         journal <- Map.put(journal, :phase, :replaced),
         :ok <- write_journal(path, journal),
         :ok <- crash_checkpoint(:directory_synced),
         {:ok, receipt} <- commit_receipt(path, journal),
         :ok <- crash_checkpoint(:receipt_synced) do
      {:ok, receipt}
    else
      {:ok, _journal} ->
        {:error, :migration_in_progress}

      false ->
        {:error, :migration_not_permitted}

      {:error, reason}
      when reason in [
             :migration_not_permitted,
             :migration_in_progress,
             :migration_lock_unavailable,
             :ledger_in_use,
             :migration_source_invalid,
             :migration_target_invalid,
             :migration_commit_uncertain,
             :storage_unavailable
           ] ->
        {:error, reason}

      _ ->
        {:error, :migration_source_invalid}
    end
  end

  defp resume_locked(path, request) do
    with {:ok, journal} <- read_journal(path),
         :ok <- validate_journal_request(journal, request, path),
         :ok <- ensure_no_open_handle(path),
         {:ok, identity} <- stored_identity_for_migration(path, journal),
         :ok <- verify_identity(identity, request),
         {:ok, canonical_rows} <- read_rows(path, :migration_source_invalid),
         {:ok, receipt} <- resume_from_rows(path, journal, canonical_rows, identity) do
      {:ok, receipt}
    else
      {:error, reason}
      when reason in [
             :migration_in_progress,
             :migration_not_permitted,
             :ledger_in_use,
             :migration_source_invalid,
             :migration_target_invalid,
             :migration_commit_uncertain,
             :storage_unavailable
           ] ->
        {:error, reason}

      _ ->
        {:error, :migration_in_progress}
    end
  end

  defp resume_from_rows(path, %{phase: :committed} = journal, _rows, identity) do
    if committed_journal_matches?(path, journal) and identity_digest(identity) == journal.tracker_identity_sha256 do
      {:ok, receipt_from_journal(journal)}
    else
      {:error, :migration_commit_uncertain}
    end
  end

  defp resume_from_rows(path, journal, rows, identity) do
    source_digest = logical_digest(rows)
    target? = source_digest == journal.target_records_sha256 and rows_schema?(rows, 2)

    cond do
      target? ->
        with :ok <- validate_target(path, journal.project_namespace, identity),
             :ok <- sync_parent(path),
             journal <- Map.put(journal, :phase, :replaced),
             :ok <- write_journal(path, journal),
             do: commit_receipt(path, journal)

      source_digest == journal.source_records_sha256 and rows_schema?(rows, 1) ->
        continue_from_source(path, journal, rows, identity)

      true ->
        {:error, :migration_commit_uncertain}
    end
  end

  defp continue_from_source(path, journal, source_rows, identity) do
    target_rows = upgrade_rows(source_rows)
    stage = stage_path(path, journal)

    with :ok <- validate_source(path, journal.project_namespace, identity),
         true <- logical_digest(target_rows) == journal.target_records_sha256,
         :ok <- stage_ready(path, stage, journal, target_rows, identity),
         :ok <- ensure_no_open_handle(path),
         :ok <- ensure_no_open_handle(stage),
         :ok <- replace_canonical(path, journal),
         :ok <- sync_parent(path),
         journal <- Map.put(journal, :phase, :replaced),
         :ok <- write_journal(path, journal),
         {:ok, receipt} <- commit_receipt(path, journal) do
      {:ok, receipt}
    else
      false -> {:error, :migration_commit_uncertain}
      {:error, reason} -> {:error, reason}
    end
  end

  defp stage_ready(path, stage, journal, target_rows, identity) do
    cond do
      File.regular?(stage) ->
        validate_stage(path, journal, journal.project_namespace, identity)

      journal.phase in [:prepared, :staged] ->
        with :ok <- create_stage(path, journal, target_rows),
             :ok <- validate_stage(path, journal, journal.project_namespace, identity),
             journal <- Map.put(journal, :phase, :staged),
             do: write_journal(path, journal)

      true ->
        {:error, :migration_target_invalid}
    end
  end

  defp abort_locked(path, request) do
    with {:ok, journal} <- read_journal(path),
         :ok <- validate_journal_request(journal, request, path),
         true <- journal.phase in [:prepared, :staged],
         :ok <- ensure_no_open_handle(path),
         {:ok, identity} <- stored_identity_for_migration(path, journal),
         :ok <- verify_identity(identity, request),
         {:ok, rows} <- read_rows(path, :migration_source_invalid),
         true <- rows_schema?(rows, 1) and logical_digest(rows) == journal.source_records_sha256,
         :ok <- validate_source(path, journal.project_namespace, identity),
         :ok <- remove_stage(stage_path(path, journal)),
         :ok <- remove_journal(path),
         :ok <- sync_parent(path) do
      :ok
    else
      false ->
        {:error, :migration_not_permitted}

      {:error, reason}
      when reason in [
             :migration_in_progress,
             :migration_not_permitted,
             :ledger_in_use,
             :migration_source_invalid,
             :migration_commit_uncertain,
             :storage_unavailable
           ] ->
        {:error, reason}

      _ ->
        {:error, :migration_not_permitted}
    end
  end

  defp validate_source(path, namespace, identity) do
    with {:ok, rows} <- read_rows(path, :migration_source_invalid),
         :ok <- AttemptLedger.validate_snapshot(namespace, identity, rows, 1) do
      :ok
    else
      _ -> {:error, :migration_source_invalid}
    end
  end

  defp validate_target(path, namespace, identity) do
    with {:ok, rows} <- read_rows(path, :migration_target_invalid),
         :ok <- AttemptLedger.validate_snapshot(namespace, identity, rows, 2) do
      :ok
    else
      _ -> {:error, :migration_target_invalid}
    end
  end

  defp validate_stage(path, journal, namespace, identity) do
    stage = stage_path(path, journal)

    with {:ok, target_rows} <- read_rows(stage, :migration_target_invalid),
         :ok <- AttemptLedger.validate_snapshot(namespace, identity, target_rows, 2),
         true <- rows_schema?(target_rows, 2),
         true <- logical_digest(target_rows) == journal.target_records_sha256,
         true <- row_counts(target_rows) == {journal.current_record_count, journal.history_record_count} do
      :ok
    else
      _ -> {:error, :migration_target_invalid}
    end
  end

  defp create_stage(path, journal, target_rows) do
    stage = stage_path(path, journal)

    if File.exists?(stage) do
      {:error, :migration_target_invalid}
    else
      write_rows(stage, target_rows)
    end
  end

  defp maybe_corrupt_stage(path, journal) do
    if Process.get(:attempt_ledger_migration_fault) == :alter_valid_stage do
      corrupt_stage(stage_path(path, journal))
    else
      :ok
    end
  rescue
    _ -> {:error, :migration_target_invalid}
  end

  defp corrupt_stage(stage) do
    case :dets.open_file(stage, file: String.to_charlist(stage), type: :set, repair: false) do
      {:ok, table} -> corrupt_open_stage(table)
      _ -> {:error, :migration_target_invalid}
    end
  end

  defp corrupt_open_stage(table) do
    result = corrupt_first_current(table)
    _ = :dets.sync(table)
    _ = :dets.close(table)
    if result == :ok, do: :ok, else: {:error, :migration_target_invalid}
  end

  defp corrupt_first_current(table) do
    case :dets.match_object(table, {{:current, :_}, :_}) do
      [{{:current, _}, record} | _] when is_map(record) ->
        :dets.insert(table, {{:current, record.issue_id}, Map.update!(record, :updated_at, &(&1 + 1))})

      _ ->
        {:error, :migration_target_invalid}
    end
  end

  defp write_rows(path, rows) do
    case :dets.open_file(path, file: String.to_charlist(path), type: :set, repair: false) do
      {:ok, table} ->
        result =
          with :ok <- File.chmod(path, 0o600) do
            write_table_rows(table, rows)
          end

        close_result = :dets.close(table)
        if result == :ok and close_result == :ok, do: :ok, else: {:error, :migration_target_invalid}

      _ ->
        {:error, :migration_target_invalid}
    end
  rescue
    _ -> {:error, :migration_target_invalid}
  end

  defp write_table_rows(table, rows) do
    with :ok <- :dets.insert(table, rows), do: :dets.sync(table)
  end

  defp read_rows(path, error) do
    case :dets.open_file(path, file: String.to_charlist(path), type: :set, access: :read, repair: false) do
      {:ok, table} ->
        rows_result =
          try do
            {:ok, :dets.foldl(fn row, acc -> [row | acc] end, [], table)}
          rescue
            _ -> {:error, error}
          end

        close_result = :dets.close(table)

        case {rows_result, close_result} do
          {{:ok, rows}, :ok} -> {:ok, rows}
          _ -> {:error, error}
        end

      _ ->
        {:error, error}
    end
  rescue
    _ -> {:error, error}
  end

  defp replace_canonical(path, journal) do
    if Process.get(:attempt_ledger_migration_fault) == :rename_failure do
      {:error, :migration_commit_uncertain}
    else
      case File.rename(stage_path(path, journal), path) do
        :ok -> :ok
        _ -> {:error, :migration_commit_uncertain}
      end
    end
  end

  defp sync_parent_after_replace(path) do
    if Process.get(:attempt_ledger_migration_fault) == :parent_sync_after_replace,
      do: {:error, :migration_commit_uncertain},
      else: sync_parent(path)
  end

  defp commit_receipt(path, journal) do
    receipt = receipt_from_journal(journal)
    committed = journal |> Map.put(:phase, :committed) |> Map.put(:committed, true)
    committed = Map.put(committed, :receipt_sha256, receipt_digest(committed))

    with :ok <- write_journal(path, committed),
         :ok <- sync_parent(path) do
      {:ok, receipt}
    end
  end

  defp new_journal(path, request, source_rows, target_rows) do
    migration_id = Base.encode16(:crypto.strong_rand_bytes(16), case: :lower)

    %{
      schema_version: @journal_version,
      migration_id: migration_id,
      project_namespace: request.project_namespace,
      tracker_identity_sha256: request.tracker_identity_sha256,
      authority_ref: request.authority_ref,
      source_schema: 1,
      target_schema: 2,
      source_records_sha256: logical_digest(source_rows),
      target_records_sha256: logical_digest(target_rows),
      stage_basename: Path.basename(path) <> ".migration-stage-" <> migration_id,
      current_record_count: elem(row_counts(source_rows), 0),
      history_record_count: elem(row_counts(source_rows), 1),
      phase: :prepared
    }
  end

  defp receipt_from_journal(journal) do
    journal
    |> Map.take(@receipt_keys)
    |> Map.put(:committed, true)
  end

  defp validate_journal_request(journal, request, path) do
    cond do
      not valid_journal?(journal, path) -> {:error, :migration_in_progress}
      journal.project_namespace != request.project_namespace -> {:error, :migration_not_permitted}
      journal.tracker_identity_sha256 != request.tracker_identity_sha256 -> {:error, :migration_not_permitted}
      journal.authority_ref != request.authority_ref -> {:error, :migration_not_permitted}
      true -> :ok
    end
  end

  defp valid_journal?(journal, path) when is_map(journal) do
    valid_journal_keys?(journal) and valid_journal_identity?(journal, path) and
      valid_journal_digests?(journal) and valid_journal_counts?(journal) and
      valid_committed_receipt?(journal)
  rescue
    _ -> false
  end

  defp valid_journal?(_, _), do: false

  defp valid_journal_keys?(journal) do
    expected = if journal[:phase] == :committed, do: @journal_keys ++ @committed_journal_extra, else: @journal_keys
    Enum.sort(Map.keys(journal)) == Enum.sort(expected)
  end

  defp valid_journal_identity?(journal, path) do
    valid_journal_version_phase?(journal) and valid_journal_id?(journal) and
      valid_journal_namespace?(journal.project_namespace) and valid_journal_authority?(journal.authority_ref) and
      valid_journal_stage?(journal, path)
  end

  defp valid_journal_version_phase?(journal) do
    journal.schema_version == @journal_version and journal.source_schema == 1 and journal.target_schema == 2 and
      journal.phase in [:prepared, :staged, :replaced, :committed]
  end

  defp valid_journal_id?(journal) do
    is_binary(journal.migration_id) and Regex.match?(~r/^[a-f0-9]{32}$/, journal.migration_id)
  end

  defp valid_journal_namespace?(namespace), do: Schema.valid_project_id?(namespace)

  defp valid_journal_authority?(authority) do
    is_binary(authority) and byte_size(authority) in 1..256 and String.trim(authority) != ""
  end

  defp valid_journal_stage?(journal, path) do
    is_binary(journal.stage_basename) and
      journal.stage_basename == Path.basename(path) <> ".migration-stage-" <> journal.migration_id
  end

  defp valid_journal_digests?(journal) do
    valid_digest?(journal.tracker_identity_sha256) and valid_digest?(journal.source_records_sha256) and
      valid_digest?(journal.target_records_sha256)
  end

  defp valid_journal_counts?(journal) do
    is_integer(journal.current_record_count) and journal.current_record_count >= 0 and
      is_integer(journal.history_record_count) and journal.history_record_count >= 0
  end

  defp valid_committed_receipt?(%{phase: :committed} = journal) do
    journal.committed == true and valid_digest?(journal.receipt_sha256) and
      journal.receipt_sha256 == receipt_digest(Map.delete(journal, :receipt_sha256))
  end

  defp valid_committed_receipt?(_journal), do: true

  defp committed_journal_matches?(path, journal) do
    with true <- valid_journal?(journal, path),
         :committed <- journal.phase,
         {:ok, rows} <- read_rows(path, :migration_source_invalid),
         true <- rows_schema?(rows, 2),
         {:ok, identity} <- stored_identity(rows),
         true <- identity_digest(identity) == journal.tracker_identity_sha256,
         [{{:meta, namespace}, %{schema_version: 2, project_namespace: namespace}}] <- Enum.filter(rows, &match?({{:meta, _}, _}, &1)),
         true <- namespace == journal.project_namespace,
         :ok <- AttemptLedger.validate_snapshot(namespace, identity, rows, 2) do
      true
    else
      _ -> false
    end
  rescue
    _ -> false
  end

  defp receipt_digest(journal), do: journal |> :erlang.term_to_binary([:deterministic]) |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower)

  defp read_journal(path) do
    case File.read(journal_path(path)) do
      {:ok, bytes} -> {:ok, :erlang.binary_to_term(bytes, [:safe])}
      {:error, :enoent} -> :missing
      _ -> {:error, :migration_in_progress}
    end
  rescue
    _ -> {:error, :migration_in_progress}
  end

  defp write_journal(path, journal) do
    if valid_journal?(journal, path) do
      temporary = path <> ".migration-journal-write-" <> Base.encode16(:crypto.strong_rand_bytes(8), case: :lower)

      result = write_journal_temp(temporary, path, journal)

      if result != :ok, do: File.rm(temporary)
      result
    else
      {:error, :migration_in_progress}
    end
  rescue
    _ -> {:error, :storage_unavailable}
  end

  defp write_journal_temp(temporary, path, journal) do
    case File.write(temporary, :erlang.term_to_binary(journal, [:deterministic]), [:sync]) do
      :ok -> rename_journal_temp(temporary, path, journal)
      _ -> journal_write_failure(journal)
    end
  end

  defp rename_journal_temp(temporary, path, journal) do
    case File.rename(temporary, journal_path(path)) do
      :ok -> sync_parent(path)
      _ -> journal_write_failure(journal)
    end
  end

  defp journal_write_failure(%{phase: phase}) when phase in [:replaced, :committed], do: {:error, :migration_commit_uncertain}
  defp journal_write_failure(_journal), do: {:error, :storage_unavailable}

  defp remove_journal(path) do
    case File.rm(journal_path(path)) do
      :ok -> :ok
      {:error, :enoent} -> :ok
      _ -> {:error, :storage_unavailable}
    end
  end

  defp remove_stage(path) do
    case File.rm(path) do
      :ok -> :ok
      {:error, :enoent} -> :ok
      _ -> {:error, :storage_unavailable}
    end
  end

  defp stage_path(path, journal), do: Path.join(Path.dirname(path), journal.stage_basename)
  defp journal_path(path), do: path <> ".migration-journal"

  defp sync_parent(path) do
    case :file.open(String.to_charlist(Path.dirname(path)), [:read, :raw, :directory]) do
      {:ok, io} ->
        sync_result = :file.sync(io)
        _ = :file.close(io)
        if sync_result == :ok, do: :ok, else: {:error, :migration_commit_uncertain}

      _ ->
        {:error, :migration_commit_uncertain}
    end
  rescue
    _ -> {:error, :migration_commit_uncertain}
  end

  defp stored_identity_for_migration(path, _journal) do
    with {:ok, rows} <- read_rows(path, :migration_source_invalid),
         {:ok, identity} <- stored_identity(rows) do
      {:ok, identity}
    else
      _ -> {:error, :migration_source_invalid}
    end
  end

  defp stored_identity(rows) do
    case Enum.find(rows, &match?({{:meta, _}, _}, &1)) do
      {{:meta, _}, %{tracker_identity: identity}} when is_map(identity) -> {:ok, identity}
      _ -> {:error, :migration_source_invalid}
    end
  end

  defp verify_identity(identity, request) do
    if identity_digest(identity) == request.tracker_identity_sha256, do: :ok, else: {:error, :migration_not_permitted}
  end

  defp upgrade_rows(rows) do
    Enum.map(rows, fn
      {{:meta, _} = key, metadata} -> {key, Map.put(metadata, :schema_version, 2)}
      {{:current, _} = key, record} when is_map(record) -> {key, record |> Map.put(:schema_version, 2) |> Map.put(:boundary_binding, %{kind: :legacy})}
      {{:history, _} = key, record} when is_map(record) -> {key, record |> Map.put(:schema_version, 2) |> Map.put(:boundary_binding, %{kind: :legacy})}
      row -> row
    end)
  end

  defp rows_schema?(rows, version) do
    Enum.all?(rows, fn
      {{:meta, _}, %{schema_version: ^version}} -> true
      {{kind, _}, %{schema_version: ^version}} when kind in [:current, :history] -> true
      _ -> false
    end) and Enum.count(rows, &match?({{:meta, _}, _}, &1)) == 1
  end

  defp row_counts(rows) do
    {Enum.count(rows, &match?({{:current, _}, _}, &1)), Enum.count(rows, &match?({{:history, _}, _}, &1))}
  end

  defp logical_digest(rows), do: rows |> Enum.sort() |> :erlang.term_to_binary([:deterministic]) |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower)
  defp identity_digest(identity), do: identity |> :erlang.term_to_binary([:deterministic]) |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower)
  defp valid_digest?(value), do: is_binary(value) and Regex.match?(~r/^[a-f0-9]{64}$/, value)

  defp ensure_source_file(path), do: if(File.regular?(path), do: :ok, else: {:error, :migration_source_invalid})

  defp path_has_no_symlink_component?(path) do
    {safe?, _current} =
      Enum.reduce_while(Path.split(Path.expand(path)), {true, ""}, fn component, {true, current} ->
        next = if current in ["", "/"], do: Path.join("/", component), else: Path.join(current, component)

        case File.lstat(next) do
          {:ok, %File.Stat{type: :symlink}} -> {:halt, {false, next}}
          {:ok, _stat} -> {:cont, {true, next}}
          {:error, :enoent} -> {:halt, {true, next}}
          _ -> {:halt, {false, next}}
        end
      end)

    safe?
  rescue
    _ -> false
  end

  defp ensure_no_open_handle(path) do
    local_open? = Enum.any?(:dets.all(), fn table -> :dets.info(table, :filename) == String.to_charlist(path) end)
    other_open? = other_process_has_file?(path)
    if local_open? or other_open?, do: {:error, :ledger_in_use}, else: :ok
  end

  defp other_process_has_file?(path) do
    case System.find_executable("fuser") do
      nil ->
        true

      fuser ->
        case System.cmd(fuser, ["-s", path], stderr_to_stdout: true) do
          {_output, 0} -> true
          {_output, 1} -> false
          _ -> true
        end
    end
  rescue
    _ -> true
  end

  defp with_lock(path, fun) do
    case acquire_host_lock(path) do
      {:ok, port} ->
        try do
          fun.()
        after
          release_host_lock(port)
        end

      _ ->
        {:error, :migration_lock_unavailable}
    end
  end

  defp acquire_host_lock(path) do
    case System.find_executable("flock") do
      nil ->
        {:error, :migration_lock_unavailable}

      executable ->
        lock = path <> ".maintenance-lock"
        port = Port.open({:spawn_executable, executable}, [:binary, :use_stdio, :exit_status, :stderr_to_stdout, {:args, ["-n", "-E", "75", lock, "-c", "printf T3_LOCKED; IFS= read -r _"]}])
        await_lock(port, System.monotonic_time(:millisecond) + 5_000)
    end
  rescue
    _ -> {:error, :migration_lock_unavailable}
  end

  defp release_host_lock(port) do
    _ = Port.command(port, "\n")

    released? =
      receive do
        {^port, {:exit_status, _status}} -> true
      after
        1_000 -> false
      end

    if not released? and Port.info(port), do: Port.close(port)
    :ok
  rescue
    _ -> :ok
  end

  defp await_lock(port, deadline) do
    receive do
      {^port, {:data, "T3_LOCKED"}} -> {:ok, port}
      {^port, {:data, _}} -> await_lock(port, deadline)
      {^port, {:exit_status, _}} -> {:error, :migration_lock_unavailable}
      {^port, :eof} -> {:error, :migration_lock_unavailable}
    after
      max(deadline - System.monotonic_time(:millisecond), 0) ->
        Port.close(port)
        {:error, :migration_lock_unavailable}
    end
  end

  defp crash_checkpoint(point) do
    if Process.get(:attempt_ledger_migration_crash_at) == point, do: System.halt(86), else: :ok
  end

  defp app_started?, do: Enum.any?(Application.started_applications(), fn {app, _, _} -> app == :symphony_elixir end)

  defp valid_request?(request) do
    valid_request_keys?(request) and valid_request_namespace?(request.project_namespace) and
      valid_digest?(request.tracker_identity_sha256) and valid_request_authority?(request.authority_ref) and
      request.source_schema == 1 and request.target_schema == 2
  end

  defp valid_request_keys?(request) do
    Enum.sort(Map.keys(request)) ==
      [:authority_ref, :project_namespace, :source_schema, :target_schema, :tracker_identity_sha256]
  end

  defp valid_request_namespace?(namespace), do: Schema.valid_project_id?(namespace)

  defp valid_request_authority?(authority) do
    is_binary(authority) and byte_size(authority) in 1..256 and String.trim(authority) != ""
  end
end
