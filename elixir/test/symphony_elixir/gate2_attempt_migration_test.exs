defmodule SymphonyElixir.Gate2AttemptMigrationTest do
  use ExUnit.Case, async: false

  alias Mix.Tasks.Symphony.AttemptMigrate
  alias SymphonyElixir.AgentRuntime.{AttemptLedger, AttemptLedgerMigration, AttemptPolicy}

  @namespace "migration-test"

  @pinned_v1_baseline_sha256 "b71b752161e9a1ff3cd1a6d9cc0fefa32735a979119dcd920b3b8cc3ab17a313"
  @pinned_v1_baseline_gzip """
  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
  AA==
  """
  @identity %{tracker_kind: "memory", provider_scope: %{project_slug: "migration-test"}}
  @request %{
    project_namespace: @namespace,
    tracker_identity_sha256: @identity |> :erlang.term_to_binary([:deterministic]) |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower),
    authority_ref: "maintenance-test",
    source_schema: 1,
    target_schema: 2
  }

  setup do
    root = Path.join(System.tmp_dir!(), "gate2-migration-" <> Base.encode16(:crypto.strong_rand_bytes(12), case: :lower))
    File.mkdir_p!(root)
    previous = Application.get_env(:symphony_elixir, :attempt_ledger_root)
    Application.put_env(:symphony_elixir, :attempt_ledger_root, root)

    on_exit(fn ->
      if previous do
        Application.put_env(:symphony_elixir, :attempt_ledger_root, previous)
      else
        Application.delete_env(:symphony_elixir, :attempt_ledger_root)
      end

      File.rm_rf(root)
    end)

    {:ok, root: root, path: AttemptLedger.path_for(@namespace)}
  end

  for {namespace, valid?} <- [
        {"project-a", true},
        {"Project_01.2", true},
        {"a", true},
        {String.duplicate("a", 128), true},
        {" project ", true},
        {"", false},
        {" ", false},
        {"tenant/project", false},
        {"../project", false},
        {".hidden", false},
        {"-prefix", false},
        {"a:b", false},
        {"a\nb", false},
        {String.duplicate("a", 129), false},
        {"项目", false}
      ] do
    @tag :scope01_namespace
    test "runtime and migration agree on namespace #{inspect(namespace)}", %{root: root} do
      namespace = unquote(namespace)
      valid? = unquote(valid?)
      configured_root = Path.join(root, "ledgers")
      File.mkdir_p!(configured_root)
      path = AttemptLedger.path_for(namespace, root: configured_root)
      request = %{@request | project_namespace: namespace}
      opened = AttemptLedger.open(namespace, @identity, root: configured_root)
      assert match?({:ok, _}, opened) == valid?

      case opened do
        {:ok, ledger} ->
          assert :ok = AttemptLedger.close(ledger)
          assert {:ok, %{committed: true}} = migrate_isolated(path, request, root: configured_root)
          assert {:ok, upgraded} = AttemptLedger.open(namespace, @identity, root: configured_root)
          assert AttemptLedger.schema_version(upgraded) == 2
          assert :ok = AttemptLedger.close(upgraded)

        {:error, _reason} ->
          before = Path.wildcard(Path.join(configured_root, "**/*"), match_dot: true)
          assert {:error, :migration_not_permitted} = migrate_isolated(path, request, root: configured_root)
          assert Path.wildcard(Path.join(configured_root, "**/*"), match_dot: true) == before
          refute File.exists?(path <> ".migration-journal")
          refute File.exists?(path)
      end
    end
  end

  test "maintenance command validates usage without touching the ledger", %{path: path} do
    assert_raise Mix.Error, ~r/usage: mix symphony.attempt_migrate/, fn ->
      AttemptMigrate.run([])
    end

    refute File.exists?(path)
    refute File.exists?(path <> ".migration-journal")
  end

  test "maintenance command migrates and resumes only through a committed receipt", %{path: path} do
    seed_v1(path)
    assert :ok = maintenance_isolated(:cli_migrate, path, @request)
    assert :ok = maintenance_isolated(:cli_resume, path, @request)
    assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert AttemptLedger.schema_version(ledger) == 2
    assert {:ok, %{schema_version: 2}} = AttemptLedger.current(ledger, "issue-a")
    assert :ok = AttemptLedger.close(ledger)
    assert {:error, message} = maintenance_isolated(:cli_abort, path, @request)
    assert message == "attempt ledger maintenance failed: migration_not_permitted"
  end

  test "maintenance command aborts a pre-replacement journal without changing v1", %{path: path} do
    seed_v1(path)
    assert :simulated_crash = migrate_isolated(path, @request, crash_at: :journal_synced)
    assert :ok = maintenance_isolated(:cli_abort, path, @request)
    assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert AttemptLedger.schema_version(ledger) == 1
    assert :ok = AttemptLedger.close(ledger)
    refute File.exists?(path <> ".migration-journal")
  end

  test "new binary opens populated v1 without implicit migration", %{path: path} do
    seed_v1(path)
    assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert AttemptLedger.schema_version(ledger) == 1
    assert {:ok, %{schema_version: 1}} = AttemptLedger.current(ledger, "issue-a")

    assert {:ok, written} =
             AttemptLedger.persist_safety(ledger, "issue-b", %{
               ordinary_failures: 0,
               ordinary_retries: 0,
               review_cycles: 0
             })

    refute Map.has_key?(written, :boundary_binding)
    assert match?({:error, _}, AttemptLedger.put(ledger, Map.put(written, :boundary_binding, %{kind: :legacy})))
    assert :ok = AttemptLedger.close(ledger)
  end

  test "v1 rearm writes the old record shape", %{path: path} do
    seed_v1(path, exhausted: true)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert {:ok, current} = AttemptLedger.rearm(ledger, "issue-a", "reason", "operator", 1_700_000_000_000)
    refute Map.has_key?(current, :boundary_binding)
    assert {:ok, [history]} = AttemptLedger.history(ledger)
    refute Map.has_key?(history, :boundary_binding)
    assert :ok = AttemptLedger.close(ledger)
  end

  test "v1 records with boundary bindings are corrupt", %{path: path} do
    seed_v1(path)
    rewrite_row(path, {:current, "issue-a"}, &Map.put(&1, :boundary_binding, %{kind: :legacy}))
    assert {:error, {:corrupt_attempt_record, {:current, "issue-a"}, :invalid_record}} = AttemptLedger.open(@namespace, @identity)
  end

  test "legacy-only project remains v1 until explicit maintenance", %{path: path} do
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert AttemptLedger.schema_version(ledger) == 1
    assert AttemptLedger.schema_version() == 2
    assert :ok = AttemptLedger.close(ledger)
    assert {:ok, _receipt} = migrate_isolated(path, @request)
  end

  test "eager migration converts metadata current and history together", %{path: path} do
    seed_v1(path, history: true)
    source_rows = rows(path)
    assert {:ok, receipt} = migrate_isolated(path, @request)
    assert receipt.current_record_count == 1
    assert receipt.history_record_count == 1
    rows = rows(path)
    assert Enum.all?(rows, fn {_key, value} -> not is_map(value) or Map.get(value, :schema_version) == 2 end)
    assert Enum.count(rows, &match?({{:current, _}, _}, &1)) == 1
    assert Enum.count(rows, &match?({{:history, _}, _}, &1)) == 1
    journal = read_journal(path)

    assert Map.keys(journal) |> Enum.sort() == [
             :authority_ref,
             :committed,
             :current_record_count,
             :history_record_count,
             :migration_id,
             :phase,
             :project_namespace,
             :receipt_sha256,
             :schema_version,
             :source_records_sha256,
             :source_schema,
             :stage_basename,
             :target_records_sha256,
             :target_schema,
             :tracker_identity_sha256
           ]

    assert journal.phase == :committed
    assert journal.schema_version == 1
    assert journal.stage_basename == Path.basename(path) <> ".migration-stage-" <> journal.migration_id
    assert journal.source_records_sha256 == logical_digest(source_rows)
    assert journal.target_records_sha256 == logical_digest(rows)
    assert journal.current_record_count == 1
    assert journal.history_record_count == 1

    assert receipt ==
             Map.take(journal, [
               :schema_version,
               :migration_id,
               :project_namespace,
               :source_records_sha256,
               :target_records_sha256,
               :current_record_count,
               :history_record_count,
               :target_schema,
               :committed
             ])
  end

  test "migration preserves the canonical ledger mode", %{path: path} do
    seed_v1(path)
    :ok = File.chmod(path, 0o600)

    assert {:ok, _receipt} = migrate_isolated(path, @request)
    assert {:ok, %File.Stat{mode: mode}} = File.stat(path)
    assert Bitwise.band(mode, 0o777) == 0o600
  end

  test "startup rejects a committed receipt with a corrupted digest", %{path: path} do
    seed_v1(path)
    assert {:ok, _receipt} = migrate_isolated(path, @request)
    journal = read_journal(path) |> Map.put(:receipt_sha256, String.duplicate("0", 64))
    write_journal(path, journal)
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
  end

  test "committed receipt admits ordinary valid v2 writes", %{path: path} do
    seed_v1(path)
    assert {:ok, _receipt} = migrate_isolated(path, @request)
    rewrite_row(path, {:current, "issue-a"}, &Map.put(&1, :updated_at, &1.updated_at + 1))
    assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert AttemptLedger.schema_version(ledger) == 2
    assert :ok = AttemptLedger.close(ledger)
  end

  test "startup rejects a noncommitted phase with receipt fields", %{path: path} do
    seed_v2_mixed(path)
    commit_fixture_receipt(path)
    write_journal(path, Map.put(read_journal(path), :phase, :replaced))
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
  end

  test "path admission requires a valid committed snapshot and receipt", %{path: path} do
    seed_v1(path)
    assert :ok = AttemptLedgerMigration.admission_check(path)
    assert {:ok, _receipt} = migrate_isolated(path, @request)
    assert :ok = AttemptLedgerMigration.admission_check(path)
    rewrite_row(path, {:current, "issue-a"}, &Map.put(&1, :schema_version, 1))
    assert {:error, :migration_in_progress} = AttemptLedgerMigration.admission_check(path)
    assert {:error, :migration_commit_uncertain} = maintenance_isolated(:resume, path, @request)
  end

  test "maintenance requests reject non-map authority and non-path input" do
    for operation <- [:migrate_v1_to_v2, :resume_v1_to_v2, :abort_v1_to_v2] do
      assert {:error, :migration_not_permitted} = apply(AttemptLedgerMigration, operation, [nil, @request])
      assert {:error, :migration_not_permitted} = apply(AttemptLedgerMigration, operation, ["unused", nil])
    end
  end

  test "resume and abort reject missing journals without modifying v1", %{path: path} do
    seed_v1(path)
    original = rows(path)
    assert {:error, :migration_in_progress} = maintenance_isolated(:resume, path, @request)
    assert {:error, :migration_not_permitted} = maintenance_isolated(:abort, path, @request)
    assert rows(path) == original
    refute File.exists?(path <> ".migration-journal")
  end

  test "changed source after journal cannot be resumed or aborted", %{path: path} do
    seed_v1(path)
    assert :simulated_crash = migrate_isolated(path, @request, crash_at: :journal_synced)
    rewrite_row(path, {:current, "issue-a"}, &Map.put(&1, :updated_at, &1.updated_at + 1))
    changed = rows(path)
    assert {:error, :migration_commit_uncertain} = maintenance_isolated(:resume, path, @request)
    assert {:error, :migration_not_permitted} = maintenance_isolated(:abort, path, @request)
    assert rows(path) == changed
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
  end

  test "journal authority cannot be replaced by a resume or abort caller", %{path: path} do
    seed_v1(path)
    assert :simulated_crash = migrate_isolated(path, @request, crash_at: :journal_synced)
    original = rows(path)

    for request <- [%{@request | authority_ref: "other-authority"}, %{@request | tracker_identity_sha256: String.duplicate("0", 64)}] do
      assert {:error, :migration_not_permitted} = maintenance_isolated(:resume, path, request)
      assert {:error, :migration_not_permitted} = maintenance_isolated(:abort, path, request)
    end

    assert rows(path) == original
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
  end

  test "real crash points leave one complete version and resume only forward", %{path: path} do
    points = [:journal_synced, :stage_synced, :stage_validated, :renamed, :directory_synced, :receipt_synced]

    for point <- points do
      reset_fixture(path)
      assert :simulated_crash = migrate_isolated(path, @request, crash_at: point)
      versions = rows(path) |> Enum.filter(fn {_key, row} -> is_map(row) end) |> Enum.map(fn {_key, row} -> row.schema_version end) |> Enum.uniq()
      expected_version = if point in [:journal_synced, :stage_synced, :stage_validated], do: 1, else: 2
      assert versions == [expected_version]

      if point == :receipt_synced do
        assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
        assert AttemptLedger.schema_version(ledger) == 2
        assert :ok = AttemptLedger.close(ledger)
      else
        assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
      end

      assert {:ok, _receipt} = maintenance_isolated(:resume, path, @request)
      assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
      assert AttemptLedger.schema_version(ledger) == 2
      assert :ok = AttemptLedger.close(ledger)
    end
  end

  test "abort removes an unchanged pre-replacement migration and refuses post-replacement downgrade", %{path: path} do
    seed_v1(path)
    assert :simulated_crash = migrate_isolated(path, @request, crash_at: :stage_validated)
    assert :ok = maintenance_isolated(:abort, path, @request)
    assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert AttemptLedger.schema_version(ledger) == 1
    assert :ok = AttemptLedger.close(ledger)

    reset_fixture(path)
    assert :simulated_crash = migrate_isolated(path, @request, crash_at: :renamed)
    assert {:error, :migration_not_permitted} = maintenance_isolated(:abort, path, @request)
    assert {:ok, _receipt} = maintenance_isolated(:resume, path, @request)
  end

  test "migration rejects a valid but altered stage before replacement", %{path: path} do
    seed_v1(path)
    assert {:error, :migration_target_invalid} = migrate_isolated(path, @request, fault: :alter_valid_stage)
    assert Enum.all?(rows(path), fn {_key, row} -> not is_map(row) or row.schema_version == 1 end)
    assert :ok = maintenance_isolated(:abort, path, @request)
    assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert AttemptLedger.schema_version(ledger) == 1
    assert :ok = AttemptLedger.close(ledger)
  end

  test "rename and parent sync uncertainty block startup until forward recovery", %{path: path} do
    for fault <- [:rename_failure, :parent_sync_after_replace] do
      reset_fixture(path)
      assert {:error, :migration_commit_uncertain} = migrate_isolated(path, @request, fault: fault)
      versions = rows(path) |> Enum.filter(fn {_key, row} -> is_map(row) end) |> Enum.map(fn {_key, row} -> row.schema_version end) |> Enum.uniq()
      assert versions == if(fault == :rename_failure, do: [1], else: [2])
      assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
      assert {:ok, _receipt} = maintenance_isolated(:resume, path, @request)
      assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
      assert AttemptLedger.schema_version(ledger) == 2
      assert :ok = AttemptLedger.close(ledger)
    end
  end

  test "v2 project supports legacy and gate2 lineages without mixed versions", %{path: path} do
    seed_v2_mixed(path)
    commit_fixture_receipt(path)
    assert {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert AttemptLedger.schema_version(ledger) == 2
    assert {:ok, %{boundary_binding: %{kind: :legacy}, schema_version: 2}} = AttemptLedger.current(ledger, "issue-a")

    assert {:ok,
            %{
              boundary_binding: %{
                kind: :gate2,
                binding_version: 1,
                lineage_binding_id: "binding-b",
                resource_ledger_namespace: "resources-test"
              },
              schema_version: 2
            }} =
             AttemptLedger.current(ledger, "issue-b")

    assert :ok = AttemptLedger.close(ledger)
  end

  test "schema 2 without a committed receipt is not admitted", %{path: path} do
    seed_v2_mixed(path)
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
  end

  test "committed receipt is bound to metadata namespace and tracker identity", %{path: path} do
    seed_v2_mixed(path)
    commit_fixture_receipt(path)
    rewrite_row(path, {:meta, @namespace}, &Map.put(&1, :project_namespace, "other-project"))
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
  end

  test "committed receipt rejects a different requested tracker identity", %{path: path} do
    seed_v2_mixed(path)
    commit_fixture_receipt(path)

    assert {:error, :migration_in_progress} =
             AttemptLedger.open(@namespace, %{tracker_kind: "other", provider_scope: %{project_slug: @namespace}})
  end

  test "gate2 binding identifiers reject whitespace", %{path: path} do
    seed_v2_mixed(path)
    commit_fixture_receipt(path)

    rewrite_row(path, {:current, "issue-b"}, fn row ->
      put_in(row, [:boundary_binding, :lineage_binding_id], " binding-b")
    end)

    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
  end

  test "migration rejects a runtime-selected alternate path", %{root: root} do
    seed_v1(Path.join(root, "alternate.dets"))
    request = Map.put(@request, :project_namespace, @namespace)
    assert {:error, :migration_not_permitted} = migrate_isolated(Path.join(root, "alternate.dets"), request)
  end

  test "migration rejects a symlinked canonical file or parent", %{root: root, path: path} do
    actual_root = Path.join(root, "actual")
    File.mkdir_p!(actual_root)
    actual_path = Path.join(actual_root, Path.basename(path))
    seed_v1(actual_path)
    File.ln_s!(actual_path, path)
    assert {:error, :migration_not_permitted} = migrate_isolated(path, @request)
    assert File.lstat!(path).type == :symlink
    assert Enum.any?(rows(actual_path), &match?({{:meta, _}, %{schema_version: 1}}, &1))
    File.rm!(path)

    alias_root = Path.join(root, "alias")
    File.ln_s!(actual_root, alias_root)
    Application.put_env(:symphony_elixir, :attempt_ledger_root, alias_root)
    aliased_path = AttemptLedger.path_for(@namespace)
    seed_v1(aliased_path)
    assert {:error, :migration_not_permitted} = migrate_isolated(aliased_path, @request)
  end

  test "migration refuses an open canonical ledger", %{path: path} do
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert {_output, 0} = System.cmd("fuser", ["-s", path], stderr_to_stdout: true)
    assert {:error, :ledger_in_use} = migrate_isolated(path, @request)
    assert :ok = AttemptLedger.close(ledger)
  end

  test "migration cannot replace a pending or committed journal", %{path: path} do
    seed_v1(path)
    pending = %{phase: :prepared, migration_id: "pending"}
    write_journal(path, pending)
    assert {:error, :migration_in_progress} = migrate_isolated(path, @request)
    assert read_journal(path) == pending

    File.rm!(path <> ".migration-journal")
    assert {:ok, _receipt} = migrate_isolated(path, @request)
    committed = read_journal(path)
    assert {:error, :migration_in_progress} = migrate_isolated(path, @request)
    assert read_journal(path) == committed
  end

  test "open creates a missing nested ledger parent", %{root: root} do
    nested_root = Path.join([root, "new", "nested"])
    Application.put_env(:symphony_elixir, :attempt_ledger_root, nested_root)
    nested_path = AttemptLedger.path_for(@namespace)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert File.regular?(nested_path)
    assert :ok = AttemptLedger.close(ledger)
  end

  test "migration lock contention is reported without touching the source", %{path: path} do
    seed_v1(path)
    port = hold_os_lock(path)

    try do
      assert {:error, :migration_lock_unavailable} = migrate_isolated(path, @request)
      assert Enum.any?(rows(path), &match?({{:meta, _}, %{schema_version: 1}}, &1))
    after
      release_test_lock(port)
    end
  end

  test "restart before replacement retains complete v1 and blocks pending journal", %{path: path} do
    seed_v1(path)
    File.write!(path <> ".migration-journal", :erlang.term_to_binary(%{phase: :staged, source_schema: 1}))
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
    assert Enum.all?(rows(path), fn {_key, value} -> not is_map(value) or Map.get(value, :schema_version) == 1 end)
  end

  test "caller-set maintenance process data cannot bypass a pending journal", %{path: path} do
    seed_v1(path)
    File.write!(path <> ".migration-journal", :erlang.term_to_binary(%{phase: :staged, source_schema: 1}))
    Process.put(:attempt_ledger_maintenance_lock_path, Path.expand(path))

    try do
      assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
    after
      Process.delete(:attempt_ledger_maintenance_lock_path)
    end
  end

  test "restart after replacement sees complete v2 and requires commit completion", %{path: path} do
    seed_v1(path)
    assert {:ok, _} = migrate_isolated(path, @request)
    File.write!(path <> ".migration-journal", :erlang.term_to_binary(%{phase: :replaced, source_schema: 1, target_schema: 2}))
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity)
    assert Enum.all?(rows(path), fn {_key, value} -> not is_map(value) or Map.get(value, :schema_version) == 2 end)
  end

  test "old reader refuses upgraded metadata", %{path: path} do
    seed_v1(path)
    assert {:ok, _} = migrate_isolated(path, @request)

    assert {:error, {:ledger_schema_version_unsupported, 2}} = pinned_v1_reader_isolated(path)
  end

  test "history and rearm preserve boundary binding", %{path: path} do
    seed_v1(path, exhausted: true)
    assert {:ok, _} = migrate_isolated(path, @request)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity)
    assert {:ok, _} = AttemptLedger.rearm(ledger, "issue-a", "reason", "operator", 1_700_000_000_000)
    assert {:ok, [%{boundary_binding: %{kind: :legacy}, schema_version: 2}]} = AttemptLedger.history(ledger)
    assert {:ok, %{boundary_binding: %{kind: :legacy}, schema_version: 2}} = AttemptLedger.current(ledger, "issue-a")
    assert :ok = AttemptLedger.close(ledger)
  end

  test "metadata and record version mismatch is corruption", %{path: path} do
    seed_v1(path)
    {:ok, _} = migrate_isolated(path, @request)
    rewrite_row(path, {:current, "issue-a"}, fn row -> Map.put(row, :schema_version, 1) end)
    assert {:error, _} = AttemptLedger.open(@namespace, @identity)
  end

  test "corrupt source or target cannot be committed", %{path: path} do
    seed_v1(path)
    rewrite_row(path, {:current, "issue-a"}, fn row -> Map.delete(row, :lineage_id) end)
    assert {:error, :migration_source_invalid} = migrate_isolated(path, @request)
    assert Enum.any?(rows(path), &match?({{:meta, _}, %{schema_version: 1}}, &1))
  end

  defp seed_v1(path, opts \\ []) do
    exhausted = opts[:exhausted]

    record = %{
      schema_version: 1,
      project_namespace: @namespace,
      issue_id: "issue-a",
      lineage_id: "lineage-a",
      safety_counters: %{
        ordinary_failures: if(exhausted, do: AttemptPolicy.max_ordinary_retries() + 1, else: 0),
        ordinary_retries: if(exhausted, do: AttemptPolicy.max_ordinary_retries(), else: 0),
        review_cycles: 0
      },
      status: if(exhausted, do: :exhausted, else: :open),
      stop_reason: if(exhausted, do: :ordinary_retry_limit, else: nil),
      route_fingerprint: "sha256:test",
      in_flight: false,
      authority_fence: nil,
      close_pending: false,
      updated_at: 1_700_000_000_000
    }

    metadata = %{schema_version: 1, project_namespace: @namespace, tracker_identity: @identity}
    history = Map.merge(record, %{status: :closed, closed_reason: :terminal})
    items = [{{:meta, @namespace}, metadata}, {{:current, "issue-a"}, record}]
    items = if opts[:history], do: items ++ [{{:history, "lineage-old"}, Map.put(history, :lineage_id, "lineage-old")}], else: items
    {:ok, table} = :dets.open_file(:migration_fixture, file: String.to_charlist(path), type: :set, repair: false)
    :ok = :dets.delete_all_objects(table)
    :ok = :dets.insert(table, items)
    :ok = :dets.sync(table)
    :ok = :dets.close(table)
  end

  defp seed_v2_mixed(path) do
    legacy = %{
      schema_version: 2,
      boundary_binding: %{kind: :legacy},
      project_namespace: @namespace,
      issue_id: "issue-a",
      lineage_id: "lineage-a",
      safety_counters: %{ordinary_failures: 0, ordinary_retries: 0, review_cycles: 0},
      status: :open,
      stop_reason: nil,
      route_fingerprint: "sha256:test",
      in_flight: false,
      authority_fence: nil,
      close_pending: false,
      updated_at: 1_700_000_000_000
    }

    gate2 =
      legacy
      |> Map.merge(%{
        issue_id: "issue-b",
        lineage_id: "lineage-b",
        boundary_binding: %{
          kind: :gate2,
          binding_version: 1,
          lineage_binding_id: "binding-b",
          resource_ledger_namespace: "resources-test"
        }
      })

    metadata = %{schema_version: 2, project_namespace: @namespace, tracker_identity: @identity}
    {:ok, table} = :dets.open_file(:migration_fixture, file: String.to_charlist(path), type: :set, repair: false)
    :ok = :dets.insert(table, [{{:meta, @namespace}, metadata}, {{:current, "issue-a"}, legacy}, {{:current, "issue-b"}, gate2}])
    :ok = :dets.sync(table)
    :ok = :dets.close(table)
  end

  defp commit_fixture_receipt(path) do
    rows = rows(path)
    migration_id = "0123456789abcdef0123456789abcdef"

    journal = %{
      schema_version: 1,
      migration_id: migration_id,
      project_namespace: @namespace,
      tracker_identity_sha256: @request.tracker_identity_sha256,
      authority_ref: "fixture-authority",
      source_schema: 1,
      target_schema: 2,
      source_records_sha256: String.duplicate("a", 64),
      target_records_sha256: logical_digest(rows),
      stage_basename: Path.basename(path) <> ".migration-stage-" <> migration_id,
      current_record_count: 2,
      history_record_count: 0,
      phase: :committed,
      committed: true
    }

    write_journal(path, Map.put(journal, :receipt_sha256, term_digest(journal)))
  end

  defp rows(path) do
    {:ok, table} =
      :dets.open_file(:migration_fixture_read, file: String.to_charlist(path), type: :set, access: :read, repair: false)

    result = :dets.match_object(table, :_)
    :ok = :dets.close(table)
    result
  end

  defp read_journal(path), do: File.read!(path <> ".migration-journal") |> :erlang.binary_to_term([:safe])
  defp write_journal(path, journal), do: File.write!(path <> ".migration-journal", :erlang.term_to_binary(journal, [:deterministic]))
  defp logical_digest(rows), do: rows |> Enum.sort() |> :erlang.term_to_binary([:deterministic]) |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower)
  defp term_digest(term), do: term |> :erlang.term_to_binary([:deterministic]) |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower)

  defp rewrite_row(path, key, fun) do
    {:ok, table} =
      :dets.open_file(:migration_fixture_rewrite, file: String.to_charlist(path), type: :set, repair: false)

    [{^key, row}] = :dets.lookup(table, key)
    :ok = :dets.insert(table, {key, fun.(row)})
    :ok = :dets.sync(table)
    :ok = :dets.close(table)
  end

  defp pinned_v1_reader_isolated(path) do
    source = @pinned_v1_baseline_gzip |> String.replace(~r/\s/, "") |> Base.decode64!() |> :zlib.gunzip()
    assert :crypto.hash(:sha256, source) |> Base.encode16(case: :lower) == @pinned_v1_baseline_sha256
    encoded_source = Base.encode64(source)
    code_args = Enum.flat_map(:code.get_path(), fn code_path -> ["-pa", List.to_string(code_path)] end)

    script = """
    [path, namespace, encoded_identity, encoded_source, expected_sha] = System.argv()
    source = Base.decode64!(encoded_source)
    true = Base.encode16(:crypto.hash(:sha256, source), case: :lower) == expected_sha
    source = String.replace(source, "defmodule SymphonyElixir.AgentRuntime.AttemptLedger do", "defmodule SymphonyElixir.Gate2PinnedAttemptLedgerV1 do")
    [{SymphonyElixir.Gate2PinnedAttemptLedgerV1, _}] = Code.compile_string(source)
    identity = encoded_identity |> Base.decode64!() |> :erlang.binary_to_term([:safe])
    result = SymphonyElixir.Gate2PinnedAttemptLedgerV1.open(namespace, identity, path: path)
    IO.puts("T3_OLD_READER=" <> Base.encode64(:erlang.term_to_binary(result, [:deterministic])))
    """

    encoded_identity = @identity |> :erlang.term_to_binary([:deterministic]) |> Base.encode64()

    case System.cmd(
           "elixir",
           code_args ++
             ["-e", script, "--", path, @namespace, encoded_identity, encoded_source, @pinned_v1_baseline_sha256],
           stderr_to_stdout: true
         ) do
      {output, 0} ->
        case Regex.run(~r/T3_OLD_READER=([^\n]+)/, output) do
          [_, encoded] -> encoded |> Base.decode64!() |> :erlang.binary_to_term([:safe])
          _ -> {:error, {:pinned_reader_failed, output}}
        end

      {output, _status} ->
        {:error, {:pinned_reader_failed, output}}
    end
  end

  defp migrate_isolated(path, request) do
    isolated_call(:migrate, path, request, [])
  end

  defp migrate_isolated(path, request, opts) do
    isolated_call(:migrate, path, request, opts)
  end

  defp maintenance_isolated(operation, path, request) do
    isolated_call(operation, path, request, [])
  end

  defp isolated_call(operation, path, request, opts) do
    Code.ensure_loaded!(SymphonyElixir.AgentRuntime.AttemptLedgerMigration)
    code_args = Enum.flat_map(:code.get_path(), fn path -> ["-pa", List.to_string(path)] end)
    encoded_request = request |> :erlang.term_to_binary([:deterministic]) |> Base.encode64()
    encoded_opts = opts |> :erlang.term_to_binary([:deterministic]) |> Base.encode64()
    cover_file = Path.join(System.tmp_dir!(), "t3-cover-#{System.unique_integer([:positive])}.coverdata")
    cover_module = :cover
    retain_cover_args = [AttemptLedgerMigration]

    retain_cover? =
      Code.ensure_loaded?(cover_module) and apply(cover_module, :is_compiled, retain_cover_args) != false

    script = """
    [root, path, encoded_request, encoded_opts, operation, cover_file] = System.argv()
    retain_cover = cover_file != "-"
    if retain_cover do
      {:ok, _cover_pid} = :cover.start()
      :cover.compile_beam(SymphonyElixir.AgentRuntime.AttemptLedger)
      :cover.compile_beam(SymphonyElixir.AgentRuntime.AttemptLedgerMigration)
      :cover.compile_beam(Mix.Tasks.Symphony.AttemptMigrate)
    end
    Code.ensure_loaded!(SymphonyElixir.AgentRuntime.AttemptLedgerMigration)
    Application.put_env(:symphony_elixir, :attempt_ledger_root, root)
    request = encoded_request |> Base.decode64!() |> :erlang.binary_to_term([:safe])
    opts = encoded_opts |> Base.decode64!() |> :erlang.binary_to_term()
    Process.put(:attempt_ledger_migration_crash_at, Keyword.get(opts, :crash_at))
    Process.put(:attempt_ledger_migration_fault, Keyword.get(opts, :fault))
    migration = SymphonyElixir.AgentRuntime.AttemptLedgerMigration
    result = case operation do
      "migrate" -> migration.migrate_v1_to_v2(path, request)
      "resume" -> migration.resume_v1_to_v2(path, request)
      "abort" -> migration.abort_v1_to_v2(path, request)
      cli when cli in ["cli_migrate", "cli_resume", "cli_abort"] ->
        Mix.start()
        args = [request.project_namespace, request.tracker_identity_sha256, request.authority_ref]
        args = case cli do
          "cli_resume" -> ["--resume" | args]
          "cli_abort" -> ["--abort" | args]
          _ -> args
        end
        try do
          Mix.Tasks.Symphony.AttemptMigrate.run(args)
          :ok
        rescue
          error in Mix.Error -> {:error, error.message}
        end
    end
    if retain_cover, do: :cover.export(cover_file)
    IO.puts("T3_RESULT=" <> Base.encode64(:erlang.term_to_binary(result, [:deterministic])))
    """

    selected_cover_file = if retain_cover?, do: cover_file, else: "-"

    args = [
      "-e",
      script,
      "--",
      Keyword.get(opts, :root, Path.dirname(path)),
      path,
      encoded_request,
      encoded_opts,
      Atom.to_string(operation),
      selected_cover_file
    ]

    result = run_isolated_command(code_args ++ args, opts)
    import_coverage(cover_module, retain_cover?, cover_file)
    result
  end

  defp run_isolated_command(args, opts) do
    case System.cmd("elixir", args, stderr_to_stdout: true) do
      {output, 0} -> decode_isolated_result(output)
      {_output, 86} when is_list(opts) and opts != [] -> :simulated_crash
      {output, _status} -> {:error, {:isolated_migration_failed, output}}
    end
  end

  defp decode_isolated_result(output) do
    case Regex.run(~r/T3_RESULT=([^\n]+)/, output) do
      [_, encoded] -> encoded |> Base.decode64!() |> :erlang.binary_to_term([:safe])
      _ -> {:error, {:isolated_migration_failed, output}}
    end
  end

  defp import_coverage(cover_module, true, cover_file) do
    if File.exists?(cover_file) do
      import_args = [cover_file]
      apply(cover_module, :import, import_args)
      File.rm(cover_file)
    end
  end

  defp import_coverage(_cover_module, false, _cover_file), do: :ok

  defp reset_fixture(path) do
    case File.read(path <> ".migration-journal") do
      {:ok, bytes} ->
        case :erlang.binary_to_term(bytes, [:safe]) do
          %{stage_basename: basename} -> File.rm(Path.join(Path.dirname(path), basename))
          _ -> :ok
        end

      _ ->
        :ok
    end

    File.rm(path <> ".migration-journal")
    seed_v1(path)
  end

  defp hold_os_lock(path) do
    executable = System.find_executable("flock")
    port = Port.open({:spawn_executable, executable}, [:binary, :use_stdio, :exit_status, :stderr_to_stdout, {:args, ["-n", path <> ".maintenance-lock", "-c", "printf T3_LOCKED; IFS= read -r _"]}])
    assert_receive {^port, {:data, "T3_LOCKED"}}, 2_000
    port
  end

  defp release_test_lock(port) do
    _ = Port.command(port, "\n")
    assert_receive {^port, {:exit_status, _}}, 2_000
  end
end
