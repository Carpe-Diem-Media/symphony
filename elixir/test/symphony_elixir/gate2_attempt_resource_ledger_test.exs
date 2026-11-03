defmodule SymphonyElixir.Gate2AttemptResourceLedgerTest do
  use ExUnit.Case, async: false

  alias SymphonyElixir.AgentRuntime.AttemptResource
  alias SymphonyElixir.AgentRuntime.AttemptResourceLedger
  alias SymphonyElixir.AgentRuntime.QuarantineDisposition
  alias SymphonyElixir.AgentRuntime.RecoveryGeneration
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  setup do
    root = Path.join(System.tmp_dir!(), "gate2-resource-ledger-" <> Base.encode16(:crypto.strong_rand_bytes(12), case: :lower))
    File.mkdir_p!(root)
    path = Path.join(root, "resources.dets")
    name = String.to_atom("gate2_resource_owner_#{System.unique_integer([:positive])}")
    owner_pid = self()
    Process.register(owner_pid, name)

    on_exit(fn ->
      if Process.whereis(name) == owner_pid, do: Process.unregister(name)
      File.rm_rf!(root)
    end)

    {:ok, root: root, path: path, owner_name: name}
  end

  test "reservation is synchronized before success", context do
    resource = resource()
    counter = :atomics.new(1, [])
    {:ok, ledger} = start_ledger(context, sync_fun: counting_sync_fun(counter))

    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert :atomics.get(counter, 1) == 1
    assert :ok = AttemptResourceLedger.close(ledger)

    {:ok, reopened} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.fetch(reopened, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(reopened)
  end

  test "duplicate exact reservation is idempotent", context do
    resource = resource()
    counter = :atomics.new(1, [])
    {:ok, ledger} = start_ledger(context, sync_fun: counting_sync_fun(counter))

    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert :atomics.get(counter, 1) == 1
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert :atomics.get(counter, 1) == 2
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "conflicting resource identity is rejected", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)

    conflict = %{resource | stable_locator: "other-locator"}
    assert {:error, :resource_conflict} = AttemptResourceLedger.reserve_sync(ledger, conflict)
    assert {:ok, quarantined} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
    assert quarantined.stable_locator == resource.stable_locator
    assert quarantined.runtime_identity == resource.runtime_identity
    assert quarantined.revision == resource.revision + 1
    assert quarantined.state == :quarantined
    assert quarantined.quarantine.reason == :identity_conflict
    assert :ok = AttemptResourceLedger.close(ledger)

    {:ok, reopened} = start_ledger(context)
    assert {:ok, persisted} = AttemptResourceLedger.fetch(reopened, resource.resource_id)
    assert persisted.state == :quarantined
    assert persisted.quarantine.reason == :identity_conflict
    assert :ok = AttemptResourceLedger.close(reopened)
  end

  test "a repeated conflict with quarantined ownership syncs without rewriting it", context do
    resource = resource()
    counter = :atomics.new(1, [])
    {:ok, ledger} = start_ledger(context, sync_fun: counting_sync_fun(counter))
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)

    assert {:error, :resource_conflict} =
             AttemptResourceLedger.reserve_sync(ledger, %{resource | stable_locator: "other-locator"})

    {:ok, quarantined} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
    :atomics.put(counter, 1, 0)

    assert {:error, :resource_conflict} =
             AttemptResourceLedger.reserve_sync(ledger, %{resource | resource_id: "resource-2"})

    assert :atomics.get(counter, 1) == 1
    assert {:ok, ^quarantined} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "transition rejects stale revision and generation", context do
    resource = resource(reconciliation_generation: generation(2), creation_generation: generation(2))
    {:ok, current_generation} = RecoveryGeneration.new(generation(2))
    {:ok, ledger} = start_ledger(context, current_generation: current_generation)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)

    next_generation = resource.reconciliation_generation

    transition = transition(:fencing, next_generation)

    assert {:error, :revision_conflict} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 1, transition)

    {:ok, stale_generation} = RecoveryGeneration.new(generation(1))
    stale = transition(:fencing, stale_generation)

    assert {:error, :recovery_generation_mismatch} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 0, stale)

    assert {:ok, ^resource} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "actual OTP caller must be the registered owner", context do
    {:ok, ledger} = start_ledger(context)
    parent = self()

    task =
      Task.async(fn ->
        send(parent, {:unauthorized_result, AttemptResourceLedger.fetch(ledger, "resource-1")})
        :ok
      end)

    assert_receive {:unauthorized_result, {:error, :unauthorized_caller}}
    assert :ok = Task.await(task)
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "only the registered owner can start a ledger without opening its path", context do
    task =
      Task.async(fn ->
        start_ledger(context)
      end)

    assert {:error, :unauthorized_caller} = Task.await(task)
    refute File.exists?(context.path)
  end

  test "startup validates required options and owner registrations before opening the ledger", context do
    {:ok, current_generation} = RecoveryGeneration.new(generation(1))

    valid = [
      path: context.path,
      owner_name: context.owner_name,
      project_namespace: "project-1",
      host_id: "host-1",
      current_generation: current_generation
    ]

    invalid_options = [
      {Keyword.delete(valid, :path), :invalid_request},
      {Keyword.delete(valid, :project_namespace), :invalid_request},
      {Keyword.delete(valid, :host_id), :invalid_request},
      {Keyword.delete(valid, :current_generation), :invalid_request},
      {Keyword.put(valid, :owner_name, "not-an-owner-name"), :invalid_request},
      {Keyword.put(valid, :recovery_owner_name, "not-a-recovery-owner-name"), :invalid_request},
      {
        Keyword.put(
          valid,
          :owner_name,
          String.to_atom("gate2_missing_owner_#{System.unique_integer([:positive])}")
        ),
        :unauthorized_caller
      }
    ]

    for {opts, expected_error} <- invalid_options do
      assert {:error, ^expected_error} = AttemptResourceLedger.start_link(opts)
    end

    refute File.exists?(context.path)
  end

  test "startup rejects generation namespace and host mismatches and releases the path", context do
    mismatches = [
      %{generation(1) | project_namespace: "other-project"},
      %{generation(1) | host_id: "other-host"}
    ]

    for generation_attrs <- mismatches do
      {:ok, mismatched_generation} = RecoveryGeneration.new(generation_attrs)

      assert {:error, :boundary_unavailable} =
               start_ledger(context, current_generation: mismatched_generation)
    end

    {:ok, ledger} = start_ledger(context)
    assert {:ok, []} = AttemptResourceLedger.list_for_grant(ledger, "grant-1")
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "recovery authority remains bound to its registered process", context do
    resource = resource()
    recovery_name = String.to_atom("gate2_recovery_owner_#{System.unique_integer([:positive])}")
    recovery_owner = start_recovery_owner(recovery_name)
    on_exit(fn -> if Process.alive?(recovery_owner), do: Process.exit(recovery_owner, :kill) end)

    {:ok, ledger} = start_ledger(context, recovery_owner_name: recovery_name)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert {:ok, ^resource} = fetch_as(recovery_owner, ledger, resource.resource_id)

    recovery_ref = Process.monitor(recovery_owner)
    Process.exit(recovery_owner, :kill)
    assert_receive {:DOWN, ^recovery_ref, :process, ^recovery_owner, :killed}

    replacement = start_recovery_owner(recovery_name)
    on_exit(fn -> if Process.alive?(replacement), do: Process.exit(replacement, :kill) end)

    assert {:error, :unauthorized_caller} = fetch_as(replacement, ledger, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "owner epoch is invalidated when durable recovery generation changes", context do
    {:ok, ledger} = start_ledger(context)
    table = :sys.get_state(ledger).table
    {:ok, next_generation} = RecoveryGeneration.new(generation(2))

    assert :ok =
             :dets.insert(table, {{:meta, :ledger}, %{schema_version: 1, project_namespace: "project-1", host_id: "host-1", current_generation: next_generation}})

    assert {:error, :unauthorized_caller} = AttemptResourceLedger.fetch(ledger, "resource-1")
    assert :ok = GenServer.stop(ledger)
  end

  @tag :needs_repair
  test "startup refuses a DETS file that needs repair", context do
    {output, 0} =
      System.cmd(
        System.find_executable("erl"),
        [
          "-noshell",
          "-eval",
          "Path = os:getenv(\"DETS_FIXTURE_PATH\"), {ok, fixture} = dets:open_file(fixture, [{file, Path}, {type, set}]), ok = dets:insert(fixture, {row, valid}), halt()."
        ],
        env: [{"DETS_FIXTURE_PATH", context.path}],
        stderr_to_stdout: true
      )

    assert output == ""
    bytes = File.read!(context.path)

    repair_check_path = context.path <> ".repair-check"
    File.cp!(context.path, repair_check_path)
    repair_check_table = String.to_atom("gate2_repair_check_#{System.unique_integer([:positive])}")

    assert {:ok, ^repair_check_table} =
             :dets.open_file(repair_check_table,
               file: String.to_charlist(repair_check_path),
               type: :set,
               repair: true
             )

    assert :ok = :dets.close(repair_check_table)

    assert {:error, :storage_unavailable} = start_ledger(context)
    assert File.read!(context.path) == bytes
  end

  @tag :close_failure
  test "close reports an unavailable DETS table", context do
    close_fun = fn _table -> {:error, :simulated} end
    {:ok, ledger} = start_ledger(context, close_fun: close_fun)

    assert {:error, :storage_unavailable} = AttemptResourceLedger.close(ledger)
    assert {:error, :storage_unavailable} = AttemptResourceLedger.fetch(ledger, "resource-1")
    assert :ok = GenServer.stop(ledger)
  end

  test "owner death stops the ledger and releases its DETS table", context do
    owner_name = String.to_atom("gate2_resource_owner_death_#{System.unique_integer([:positive])}")
    parent = self()

    owner =
      spawn(fn ->
        Process.register(self(), owner_name)
        {:ok, current_generation} = RecoveryGeneration.new(generation(1))

        {:ok, ledger} =
          AttemptResourceLedger.start_link(
            path: context.path,
            project_namespace: "project-1",
            host_id: "host-1",
            current_generation: current_generation,
            owner_name: owner_name
          )

        send(parent, {:owner_ledger, ledger})

        receive do
          :hold -> :ok
        end
      end)

    assert_receive {:owner_ledger, ledger}
    ref = Process.monitor(ledger)
    Process.exit(owner, :kill)
    assert_receive {:DOWN, ^ref, :process, ^ledger, :killed}
    assert_file_reopenable(context.path)
  end

  test "profile-increasing transitions are denied and quarantine is terminal", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)

    active = transition(:active, resource.reconciliation_generation)

    assert {:error, :gate2_profile_incomplete} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 0, active)

    fencing = transition(:fencing, resource.reconciliation_generation)

    assert {:ok, fenced_intent} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 0, fencing)

    assert fenced_intent.state == :fencing

    {:ok, quarantined} =
      QuarantineDisposition.new(%{
        state: :quarantined,
        reason: :fence_unverified,
        evidence_ref: nil,
        generation: resource.reconciliation_generation,
        resolution_ref: nil
      })

    quarantine = transition(:quarantined, resource.reconciliation_generation, quarantined)

    assert {:ok, quarantined_resource} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 1, quarantine)

    assert {:error, :transition_invalid} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 2, fencing)

    assert quarantined_resource.state == :quarantined
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "cleanup uncertainty transition remains unavailable in P01", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)

    {:ok, quarantine} =
      QuarantineDisposition.new(%{
        state: :quarantined,
        reason: :cleanup_unverified,
        evidence_ref: nil,
        generation: resource.reconciliation_generation,
        resolution_ref: nil
      })

    cleanup = transition(:cleanup_unverified, resource.reconciliation_generation, quarantine)

    assert {:error, :gate2_profile_incomplete} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 0, cleanup)

    assert {:ok, ^resource} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "startup rejects a ledger configured for another generation", context do
    {:ok, ledger} = start_ledger(context)
    assert :ok = AttemptResourceLedger.close(ledger)

    {:ok, other_generation} = RecoveryGeneration.new(generation(2))
    assert {:error, :schema_mismatch} = start_ledger(context, current_generation: other_generation)
    assert_file_reopenable(context.path)
  end

  test "startup reconciles old facts into a fresh generation and restores no active authority", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert :ok = AttemptResourceLedger.close(ledger)

    {:ok, fresh_generation} =
      RecoveryGeneration.new(%{generation(2) | boot_id: "boot-2"})

    {:ok, recovered} = start_ledger(context, current_generation: fresh_generation)
    assert {:ok, quarantined} = AttemptResourceLedger.fetch(recovered, resource.resource_id)
    assert quarantined.state == :quarantined
    assert quarantined.creation_generation == resource.creation_generation
    assert quarantined.reconciliation_generation == fresh_generation
    assert quarantined.quarantine.reason == :stale_generation

    assert {:error, :transition_invalid} =
             AttemptResourceLedger.transition_sync(
               recovered,
               resource.resource_id,
               quarantined.revision,
               transition(:fencing, fresh_generation)
             )

    assert :ok = AttemptResourceLedger.close(recovered)
  end

  test "startup refuses partial or ambiguous old ownership without rewriting facts", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert :ok = AttemptResourceLedger.close(ledger)

    table = String.to_atom("gate2_ambiguous_resource_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)
    assert :ok = :dets.insert(table, {{:resource, "duplicate"}, %{resource | resource_id: "duplicate"}})
    assert :ok = :dets.close(table)
    before = File.read!(context.path)

    {:ok, fresh_generation} = RecoveryGeneration.new(%{generation(2) | boot_id: "boot-2"})
    assert {:error, :storage_corrupt} = start_ledger(context, current_generation: fresh_generation)
    assert File.read!(context.path) == before
    assert_file_reopenable(context.path)
  end

  test "startup refuses resource facts when ledger metadata is missing", context do
    table = String.to_atom("gate2_orphan_resource_#{System.unique_integer([:positive])}")
    row = resource()

    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)
    assert :ok = :dets.insert(table, {{:resource, row.resource_id}, row})
    assert :ok = :dets.sync(table)
    assert :ok = :dets.close(table)

    before = File.read!(context.path)
    assert {:error, :storage_corrupt} = start_ledger(context)
    assert File.read!(context.path) == before
    assert_file_reopenable(context.path)
  end

  test "startup rejects metadata with unknown fields without changing the ledger", context do
    {:ok, ledger} = start_ledger(context)
    assert :ok = AttemptResourceLedger.close(ledger)

    table = String.to_atom("gate2_extra_metadata_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)
    [{{:meta, :ledger}, metadata}] = :dets.lookup(table, {:meta, :ledger})

    assert :ok = :dets.insert(table, {{:meta, :ledger}, Map.put(metadata, :unexpected, true)})
    assert :ok = :dets.sync(table)
    assert :ok = :dets.close(table)

    before = File.read!(context.path)
    assert {:error, :storage_corrupt} = start_ledger(context)
    assert File.read!(context.path) == before
    assert_file_reopenable(context.path)
  end

  test "startup rejects a malformed recovery pending marker without rewriting it", context do
    {:ok, ledger} = start_ledger(context)
    assert :ok = AttemptResourceLedger.close(ledger)

    table = String.to_atom("gate2_bad_recovery_marker_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)
    assert :ok = :dets.insert(table, {{:meta, :recovery_pending}, :unexpected})
    assert :ok = :dets.sync(table)
    assert :ok = :dets.close(table)

    before = File.read!(context.path)
    assert {:error, :storage_corrupt} = start_ledger(context)
    assert File.read!(context.path) == before
    assert_file_reopenable(context.path)
  end

  test "startup rejects duplicate grant identity with distinct stable locators", context do
    original = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^original} = AttemptResourceLedger.reserve_sync(ledger, original)
    assert :ok = AttemptResourceLedger.close(ledger)

    duplicate = %{original | resource_id: "resource-2", stable_locator: "locator-2"}
    table = String.to_atom("gate2_duplicate_identity_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)
    assert :ok = :dets.insert(table, {{:resource, duplicate.resource_id}, duplicate})
    assert :ok = :dets.sync(table)
    assert :ok = :dets.close(table)

    before = File.read!(context.path)
    {:ok, fresh_generation} = RecoveryGeneration.new(%{generation(2) | boot_id: "boot-2"})

    assert {:error, :storage_corrupt} =
             start_ledger(context, current_generation: fresh_generation)

    assert File.read!(context.path) == before
    assert_file_reopenable(context.path)
  end

  test "a DETS open failure releases the path lock", context do
    table = String.to_atom("gate2_external_resource_table_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)

    assert {:error, :storage_unavailable} = start_ledger(context)
    assert :ok = :dets.close(table)

    {:ok, ledger} = start_ledger(context)
    assert {:ok, []} = AttemptResourceLedger.list_for_grant(ledger, "grant-1")
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "a symlinked resource path reopens the same durable ledger", context do
    alias_root = Path.join(context.root, "alias")
    File.ln_s!(context.root, alias_root)
    alias_path = Path.join(alias_root, Path.basename(context.path))
    resource = resource()

    {:ok, ledger} = start_ledger(context, path: alias_path)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert :ok = AttemptResourceLedger.close(ledger)

    {:ok, reopened} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.fetch(reopened, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(reopened)
  end

  test "stable locator conflicts across grants quarantine the existing owner", context do
    original = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^original} = AttemptResourceLedger.reserve_sync(ledger, original)

    other_grant = %{original | resource_id: "resource-2", grant_id: "grant-2"}
    assert {:error, :resource_conflict} = AttemptResourceLedger.reserve_sync(ledger, other_grant)

    assert {:ok, quarantined} = AttemptResourceLedger.fetch(ledger, original.resource_id)
    assert quarantined.state == :quarantined
    assert quarantined.quarantine.reason == :identity_conflict
    assert quarantined.grant_id == original.grant_id
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "startup sync uncertainty leaves a durable recovery block", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert :ok = AttemptResourceLedger.close(ledger)

    fail_sync = fn _table -> {:error, :injected} end

    assert {:error, :sync_failed} =
             AttemptResourceLedger.start_link(
               path: context.path,
               owner_name: context.owner_name,
               project_namespace: "project-1",
               host_id: "host-1",
               startup_recovery: true,
               sync_fun: fail_sync
             )

    assert {:error, :storage_unavailable} =
             AttemptResourceLedger.start_link(
               path: context.path,
               owner_name: context.owner_name,
               project_namespace: "project-1",
               host_id: "host-1",
               startup_recovery: true
             )

    assert_file_reopenable(context.path)
  end

  test "startup row write failure retains the pending recovery marker", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert :ok = AttemptResourceLedger.close(ledger)

    counter = :atomics.new(1, [])

    write_fun = fn table, row ->
      if :atomics.add_get(counter, 1, 1) == 2 do
        {:error, :simulated}
      else
        :dets.insert(table, row)
      end
    end

    {:ok, fresh_generation} = RecoveryGeneration.new(%{generation(2) | boot_id: "boot-2"})

    assert {:error, :write_failed} =
             start_ledger(context,
               current_generation: fresh_generation,
               write_fun: write_fun
             )

    assert {:error, :storage_unavailable} =
             AttemptResourceLedger.start_link(
               path: context.path,
               owner_name: context.owner_name,
               project_namespace: "project-1",
               host_id: "host-1",
               startup_recovery: true
             )

    assert_file_reopenable(context.path)
  end

  test "startup recovery rejects malformed persisted generation metadata without rewriting it", context do
    {:ok, ledger} = start_ledger(context)
    assert :ok = AttemptResourceLedger.close(ledger)

    table = String.to_atom("gate2_malformed_generation_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)
    [{{:meta, :ledger}, metadata}] = :dets.lookup(table, {:meta, :ledger})
    malformed_generation = %{metadata.current_generation | sequence: 0}

    assert :ok =
             :dets.insert(table, {{:meta, :ledger}, %{metadata | current_generation: malformed_generation}})

    assert :ok = :dets.sync(table)
    assert :ok = :dets.close(table)

    before = File.read!(context.path)

    assert {:error, :storage_corrupt} =
             AttemptResourceLedger.start_link(
               path: context.path,
               owner_name: context.owner_name,
               project_namespace: "project-1",
               host_id: "host-1",
               startup_recovery: true
             )

    assert File.read!(context.path) == before
    assert_file_reopenable(context.path)
  end

  test "startup rejects unsupported schema without changing the ledger", context do
    {:ok, ledger} = start_ledger(context)
    assert :ok = AttemptResourceLedger.close(ledger)

    table = String.to_atom("gate2_unsupported_resource_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)
    [{{:meta, :ledger}, metadata}] = :dets.lookup(table, {:meta, :ledger})
    assert :ok = :dets.insert(table, {{:meta, :ledger}, %{metadata | schema_version: 2}})
    assert :ok = :dets.sync(table)
    assert :ok = :dets.close(table)

    before = File.read!(context.path)
    assert {:error, :unsupported_schema} = start_ledger(context)
    assert File.read!(context.path) == before
    assert_file_reopenable(context.path)
  end

  test "a canonical ledger path cannot be opened by two ledger processes", context do
    {:ok, ledger} = start_ledger(context)

    assert {:error, :storage_unavailable} = start_ledger(context)
    assert {:ok, []} = AttemptResourceLedger.list_for_grant(ledger, "grant-1")
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "startup rejects resource rows stored under another identity key", context do
    {:ok, ledger} = start_ledger(context)
    assert :ok = AttemptResourceLedger.close(ledger)

    row = resource()
    table = String.to_atom("gate2_corrupt_resource_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(context.path), type: :set)
    assert :ok = :dets.insert(table, {{:resource, "wrong-key"}, row})
    assert :ok = :dets.close(table)

    assert {:error, :storage_corrupt} = start_ledger(context)
    assert_file_reopenable(context.path)
  end

  test "sync failure while quarantining a conflict blocks the ledger", context do
    resource = resource()
    counter = :atomics.new(1, [])

    sync_fun = fn table ->
      if :atomics.add_get(counter, 1, 1) == 1 do
        :dets.sync(table)
      else
        {:error, :simulated}
      end
    end

    {:ok, ledger} = start_ledger(context, sync_fun: sync_fun)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)

    assert {:error, :sync_failed} =
             AttemptResourceLedger.reserve_sync(ledger, %{resource | stable_locator: "other-locator"})

    assert {:error, :storage_unavailable} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  test "sync failure never acknowledges transition", context do
    resource = resource()
    counter = :atomics.new(1, [])

    sync_fun = fn table ->
      if :atomics.add_get(counter, 1, 1) == 1 do
        :dets.sync(table)
      else
        {:error, :simulated}
      end
    end

    {:ok, ledger} = start_ledger(context, sync_fun: sync_fun)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)

    fencing = transition(:fencing, resource.reconciliation_generation)

    assert {:error, :sync_failed} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 0, fencing)

    assert {:error, :storage_unavailable} = AttemptResourceLedger.fetch(ledger, resource.resource_id)

    assert {:error, :storage_unavailable} =
             AttemptResourceLedger.transition_sync(ledger, resource.resource_id, 0, fencing)

    assert :ok = AttemptResourceLedger.close(ledger)

    {:ok, reopened} = start_ledger(context)
    assert {:ok, persisted} = AttemptResourceLedger.fetch(reopened, resource.resource_id)
    assert persisted.state in [:reserved, :fencing]

    assert {:error, :gate2_profile_incomplete} =
             AttemptResourceLedger.transition_sync(
               reopened,
               resource.resource_id,
               persisted.revision,
               transition(:active, resource.reconciliation_generation)
             )

    assert :ok = AttemptResourceLedger.close(reopened)
  end

  test "write failure blocks reads until close and restart", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context, write_fun: fn _table, _row -> {:error, :simulated} end)

    assert {:error, :write_failed} = AttemptResourceLedger.reserve_sync(ledger, resource)
    assert {:error, :storage_unavailable} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(ledger)

    {:ok, reopened} = start_ledger(context)
    assert :not_found = AttemptResourceLedger.fetch(reopened, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(reopened)
  end

  test "write callbacks that raise or throw return stable errors and release the ledger on close", context do
    resource = resource()

    for failure <- [:raise, :throw] do
      write_fun = fn _table, _row ->
        case failure do
          :raise -> raise "injected write failure"
          :throw -> throw(:injected_write_failure)
        end
      end

      {:ok, ledger} = start_ledger(context, write_fun: write_fun)
      assert {:error, :write_failed} = AttemptResourceLedger.reserve_sync(ledger, resource)
      assert {:error, :storage_unavailable} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
      assert :ok = AttemptResourceLedger.close(ledger)

      {:ok, reopened} = start_ledger(context)
      assert :not_found = AttemptResourceLedger.fetch(reopened, resource.resource_id)
      assert :ok = AttemptResourceLedger.close(reopened)
    end
  end

  test "a throwing close callback blocks authority and termination releases the path", context do
    close_fun = fn _table -> throw(:injected_close_failure) end
    {:ok, ledger} = start_ledger(context, close_fun: close_fun)

    assert {:error, :storage_unavailable} = AttemptResourceLedger.close(ledger)
    assert {:error, :storage_unavailable} = AttemptResourceLedger.fetch(ledger, "resource-1")
    assert :ok = GenServer.stop(ledger)

    {:ok, reopened} = start_ledger(context)
    assert {:ok, []} = AttemptResourceLedger.list_for_grant(reopened, "grant-1")
    assert :ok = AttemptResourceLedger.close(reopened)
  end

  test "an absent verified identity conflict poisons authority without rewriting the fact", context do
    original = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^original} = AttemptResourceLedger.reserve_sync(ledger, original)

    table = :sys.get_state(ledger).table
    absent = %{original | state: :absent_verified}
    assert :ok = :dets.insert(table, {{:resource, original.resource_id}, absent})
    assert :ok = :dets.sync(table)

    conflict = %{original | resource_id: "resource-2"}
    assert {:error, :ownership_ambiguous} = AttemptResourceLedger.reserve_sync(ledger, conflict)
    assert {:error, :storage_unavailable} = AttemptResourceLedger.fetch(ledger, original.resource_id)
    assert :ok = AttemptResourceLedger.close(ledger)

    {:ok, reopened} = start_ledger(context)
    assert {:ok, ^absent} = AttemptResourceLedger.fetch(reopened, original.resource_id)
    assert :ok = AttemptResourceLedger.close(reopened)
  end

  test "quarantine progression accepts one step and rejects skips and regressions", context do
    resource = resource()
    {:ok, ledger} = start_ledger(context)
    assert {:ok, ^resource} = AttemptResourceLedger.reserve_sync(ledger, resource)

    quarantined = quarantine_for(:quarantined, resource.reconciliation_generation)

    assert {:ok, first} =
             AttemptResourceLedger.transition_sync(
               ledger,
               resource.resource_id,
               0,
               transition(:quarantined, resource.reconciliation_generation, quarantined)
             )

    skipped = quarantine_for(:operator_resolution_pending, resource.reconciliation_generation)

    assert {:error, :transition_invalid} =
             AttemptResourceLedger.transition_sync(
               ledger,
               resource.resource_id,
               first.revision,
               transition(:quarantined, resource.reconciliation_generation, skipped)
             )

    block_reuse = quarantine_for(:block_reuse, resource.reconciliation_generation)

    assert {:ok, second} =
             AttemptResourceLedger.transition_sync(
               ledger,
               resource.resource_id,
               first.revision,
               transition(:quarantined, resource.reconciliation_generation, block_reuse)
             )

    assert second.quarantine.state == :block_reuse

    assert {:error, :transition_invalid} =
             AttemptResourceLedger.transition_sync(
               ledger,
               resource.resource_id,
               second.revision,
               transition(:quarantined, resource.reconciliation_generation, quarantined)
             )

    pending = quarantine_for(:operator_resolution_pending, resource.reconciliation_generation)

    assert {:ok, third} =
             AttemptResourceLedger.transition_sync(
               ledger,
               resource.resource_id,
               second.revision,
               transition(:quarantined, resource.reconciliation_generation, pending)
             )

    remains = quarantine_for(:remains_quarantined, resource.reconciliation_generation)

    assert {:ok, fourth} =
             AttemptResourceLedger.transition_sync(
               ledger,
               resource.resource_id,
               third.revision,
               transition(:quarantined, resource.reconciliation_generation, remains)
             )

    released = quarantine_for(:released_for_new_authorization, resource.reconciliation_generation)

    assert {:error, :transition_invalid} =
             AttemptResourceLedger.transition_sync(
               ledger,
               resource.resource_id,
               fourth.revision,
               transition(:quarantined, resource.reconciliation_generation, released)
             )

    assert fourth.quarantine.state == :remains_quarantined
    assert {:ok, ^fourth} = AttemptResourceLedger.fetch(ledger, resource.resource_id)
    assert :ok = AttemptResourceLedger.close(ledger)
  end

  for disposition <- [
        :quarantined,
        :block_reuse,
        :operator_resolution_pending,
        :released_for_new_authorization,
        :remains_quarantined
      ] do
    @tag :scope01_quarantine
    test "restart preserves #{disposition} semantics without restoring live authority", context do
      disposition = unquote(disposition)
      original = resource()
      {:ok, ledger} = start_ledger(context)
      assert {:ok, ^original} = AttemptResourceLedger.reserve_sync(ledger, original)
      table = :sys.get_state(ledger).table

      quarantine = %{
        original.quarantine
        | state: disposition,
          reason: :operator_resolution_required,
          evidence_ref: "untrusted-evidence-reference",
          resolution_ref: "untrusted-resolution-reference"
      }

      stored = %{original | state: :quarantined, quarantine: quarantine}
      assert :ok = :dets.insert(table, {{:resource, original.resource_id}, stored})
      assert :ok = AttemptResourceLedger.close(ledger)
      {:ok, fresh} = RecoveryGeneration.new(%{generation(2) | boot_id: "boot-2"})
      {:ok, recovered} = start_ledger(context, current_generation: fresh)
      assert {:ok, row} = AttemptResourceLedger.fetch(recovered, original.resource_id)
      assert row.quarantine == quarantine
      assert row.creation_generation == original.creation_generation
      assert row.reconciliation_generation == fresh
      assert row.revision == stored.revision + 1
      assert row.state == :quarantined

      assert {:error, :transition_invalid} =
               AttemptResourceLedger.transition_sync(
                 recovered,
                 original.resource_id,
                 row.revision,
                 transition(:fencing, fresh)
               )

      assert :ok = AttemptResourceLedger.close(recovered)
      {:ok, reopened} = start_ledger(context, current_generation: fresh)
      assert {:ok, ^row} = AttemptResourceLedger.fetch(reopened, original.resource_id)
      assert :ok = AttemptResourceLedger.close(reopened)
    end
  end

  for operation <- [:fetch, :list, :reserve, :transition, :metadata] do
    @tag :scope01_corruption
    test "#{operation} corruption latches until validated close and reopen", context do
      operation = unquote(operation)
      original = resource()
      {:ok, ledger} = start_ledger(context)
      assert {:ok, ^original} = AttemptResourceLedger.reserve_sync(ledger, original)
      table = :sys.get_state(ledger).table
      key = corruption_key(operation, original.resource_id)
      [stored] = :dets.lookup(table, key)
      assert :ok = :dets.insert(table, {key, :corrupt})

      detected = detect_corruption(operation, ledger, original)
      expected = corruption_error(operation)
      assert detected == {:error, expected}
      assert :ok = :dets.insert(table, stored)
      assert :ok = :dets.sync(table)
      assert {:error, :storage_unavailable} = AttemptResourceLedger.fetch(ledger, original.resource_id)
      assert {:error, :storage_unavailable} = AttemptResourceLedger.list_for_grant(ledger, original.grant_id)
      assert {:error, :storage_unavailable} = AttemptResourceLedger.reserve_sync(ledger, original)
      assert {:error, :storage_unavailable} = AttemptResourceLedger.current_generation(ledger)

      assert {:error, :storage_unavailable} =
               AttemptResourceLedger.transition_sync(
                 ledger,
                 original.resource_id,
                 original.revision,
                 transition(:fencing, original.reconciliation_generation)
               )

      assert :ok = AttemptResourceLedger.close(ledger)
      {:ok, reopened} = start_ledger(context)
      assert {:ok, ^original} = AttemptResourceLedger.fetch(reopened, original.resource_id)
      assert :ok = AttemptResourceLedger.close(reopened)
    end
  end

  defp corruption_key(:metadata, _resource_id), do: {:meta, :ledger}
  defp corruption_key(_operation, resource_id), do: {:resource, resource_id}
  defp corruption_error(:metadata), do: :unauthorized_caller
  defp corruption_error(_operation), do: :storage_corrupt

  defp detect_corruption(:fetch, ledger, original), do: AttemptResourceLedger.fetch(ledger, original.resource_id)
  defp detect_corruption(:metadata, ledger, original), do: AttemptResourceLedger.fetch(ledger, original.resource_id)
  defp detect_corruption(:list, ledger, original), do: AttemptResourceLedger.list_for_grant(ledger, original.grant_id)
  defp detect_corruption(:reserve, ledger, original), do: AttemptResourceLedger.reserve_sync(ledger, original)

  defp detect_corruption(:transition, ledger, original) do
    AttemptResourceLedger.transition_sync(
      ledger,
      original.resource_id,
      original.revision,
      transition(:fencing, original.reconciliation_generation)
    )
  end

  defp start_ledger(context, extra \\ []) do
    {:ok, current_generation} = RecoveryGeneration.new(generation(1))

    defaults = [
      path: context.path,
      owner_name: context.owner_name,
      project_namespace: "project-1",
      host_id: "host-1",
      current_generation: current_generation
    ]

    AttemptResourceLedger.start_link(Keyword.merge(defaults, extra))
  end

  defp start_recovery_owner(name) do
    parent = self()

    pid =
      spawn(fn ->
        Process.register(self(), name)
        send(parent, {:recovery_owner_registered, self()})
        recovery_owner_loop()
      end)

    assert_receive {:recovery_owner_registered, ^pid}
    pid
  end

  defp recovery_owner_loop do
    receive do
      {:fetch, ledger, resource_id, caller, reference} ->
        send(caller, {reference, AttemptResourceLedger.fetch(ledger, resource_id)})
        recovery_owner_loop()

      :stop ->
        :ok
    end
  end

  defp fetch_as(owner, ledger, resource_id) do
    reference = make_ref()
    send(owner, {:fetch, ledger, resource_id, self(), reference})
    assert_receive {^reference, result}
    result
  end

  defp resource(overrides \\ []) do
    identity = %Identity{
      runtime_attempt_id: "attempt-1",
      work_item_id: "item-1",
      lineage_generation: "lineage-1",
      responsibility: "builder",
      runtime_profile: "profile-1"
    }

    {:ok, reconciliation_generation} =
      RecoveryGeneration.new(Keyword.get(overrides, :reconciliation_generation, generation(1)))

    {:ok, creation_generation} =
      RecoveryGeneration.new(Keyword.get(overrides, :creation_generation, generation(1)))

    {:ok, quarantine} =
      QuarantineDisposition.new(%{
        state: :clear,
        reason: nil,
        evidence_ref: nil,
        generation: reconciliation_generation,
        resolution_ref: nil
      })

    {:ok, resource} =
      AttemptResource.new(%{
        schema_version: 1,
        resource_id: "resource-1",
        project_namespace: "project-1",
        grant_id: "grant-1",
        runtime_identity: identity,
        class: :workspace,
        state: :reserved,
        revision: 0,
        stable_locator: "locator-1",
        allocation_identity_sha256: nil,
        capacity_profile_sha256: digest(),
        owner_host_id: "host-1",
        creation_generation: creation_generation,
        reconciliation_generation: reconciliation_generation,
        last_evidence_ref: nil,
        quarantine: quarantine
      })

    resource
  end

  defp generation(sequence) do
    %{
      schema_version: 1,
      project_namespace: "project-1",
      host_id: "host-1",
      boot_id: "boot-1",
      sequence: sequence,
      nonce: "nonce-#{sequence}"
    }
  end

  defp transition(to, generation, quarantine \\ nil) do
    quarantine = quarantine || clear_quarantine(generation)

    %{
      to: to,
      generation: generation,
      allocation_identity_sha256: nil,
      evidence_ref: nil,
      cleanup_ref: nil,
      quarantine: quarantine
    }
  end

  defp clear_quarantine(generation) do
    {:ok, quarantine} =
      QuarantineDisposition.new(%{
        state: :clear,
        reason: nil,
        evidence_ref: nil,
        generation: generation,
        resolution_ref: nil
      })

    quarantine
  end

  defp quarantine_for(state, generation) do
    {:ok, quarantine} =
      QuarantineDisposition.new(%{
        state: state,
        reason: :operator_resolution_required,
        evidence_ref: nil,
        generation: generation,
        resolution_ref: nil
      })

    quarantine
  end

  defp counting_sync_fun(counter) do
    fn table ->
      :atomics.add(counter, 1, 1)
      :dets.sync(table)
    end
  end

  defp assert_file_reopenable(path) do
    table = String.to_atom("gate2_reopen_check_#{System.unique_integer([:positive])}")
    assert {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(path), type: :set)
    assert :ok = :dets.close(table)
  end

  defp digest, do: String.duplicate("a", 64)
end
