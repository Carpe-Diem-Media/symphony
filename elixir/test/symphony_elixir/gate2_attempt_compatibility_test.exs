defmodule SymphonyElixir.Gate2AttemptCompatibilityTest do
  use ExUnit.Case, async: false

  alias SymphonyElixir.AgentRuntime.AttemptLedger
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.WorkControl.SuspensionContext

  @namespace "compatibility-test"
  @identity %{tracker_kind: "memory", provider_scope: %{project_slug: @namespace}}
  @gate2_binding %{
    kind: :gate2,
    binding_version: 1,
    lineage_binding_id: "binding-a",
    resource_ledger_namespace: @namespace
  }

  setup do
    root = Path.join(System.tmp_dir!(), "gate2-compat-#{System.unique_integer([:positive])}")
    File.rm_rf!(root)
    File.mkdir_p!(root)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity, root: root)

    on_exit(fn ->
      AttemptLedger.close(ledger)
      File.rm_rf!(root)
    end)

    {:ok, %{root: root, ledger: ledger}}
  end

  test "legacy release remains valid for legacy binding", %{ledger: ledger} do
    assert {:ok, record} = AttemptLedger.begin_attempt(ledger, "legacy")
    assert :ok = AttemptLedger.release_armed_authority_fence(ledger, "legacy")
    assert {:ok, released} = AttemptLedger.current(ledger, "legacy")
    assert released.authority_fence.state == :released
    assert released.schema_version == record.schema_version
  end

  test "schema two preserves legacy release and close alongside unresolved Gate2", %{root: root} do
    path = seed_committed_schema2(root)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity, path: path)
    assert {:ok, %{boundary_binding: %{kind: :legacy}}} = AttemptLedger.begin_attempt(ledger, "legacy-two")
    assert :ok = AttemptLedger.release_armed_authority_fence(ledger, "legacy-two")
    assert {:ok, %{authority_fence: %{state: :released}}} = AttemptLedger.current(ledger, "legacy-two")
    assert :ok = AttemptLedger.clear_in_flight(ledger, "legacy-two")
    assert :ok = AttemptLedger.close_lineage(ledger, "legacy-two")
    assert {:ok, %{status: :closed}} = AttemptLedger.current(ledger, "legacy-two")
    assert {:ok, [%{issue_id: "compatibility-current"}]} = AttemptLedger.open_lineages(ledger)
    assert {:ok, [%{boundary_binding: %{kind: :legacy}}]} = AttemptLedger.history(ledger)
    assert :ok = AttemptLedger.close(ledger)
    assert {:ok, reopened} = AttemptLedger.open(@namespace, @identity, path: path)
    assert {:ok, [%{issue_id: "compatibility-current"}]} = AttemptLedger.open_lineages(reopened)
    assert :ok = AttemptLedger.close(reopened)
  end

  test "configured schema and mode preserve legacy and missing-file outcomes", %{root: root} do
    assert {:ok, 1, false} = AttemptLedger.configured_schema(@namespace, @identity, root: root)
    assert :ok = AttemptLedger.configured_mode("legacy", @namespace, @identity, root: root)

    assert {:error, :migration_required} =
             AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, root: root)

    assert {:error, :migration_required} =
             AttemptLedger.configured_schema(@namespace, @identity, path: Path.join(root, "missing.dets"))

    assert {:error, :invalid_request} = AttemptLedger.configured_schema(nil, @identity, root: root)
    assert {:error, :invalid_request} = AttemptLedger.configured_mode("unknown", @namespace, @identity, root: root)
    assert {:error, :gate2_profile_incomplete} = AttemptLedger.configured_mode("gate2_enforced", @namespace, @identity, root: root)
  end

  test "legacy mode checks stored identity before deciding whether Gate2 is present", %{root: root} do
    changed_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "changed-project"}}

    assert {:error, :identity_mismatch} = AttemptLedger.configured_schema(@namespace, changed_identity, root: root)
    assert :ok = AttemptLedger.configured_mode("legacy", @namespace, changed_identity, root: root)
  end

  test "configured mode detects Gate2 current binding alongside legacy history", %{root: root} do
    path = seed_committed_schema2(root)

    assert {:ok, 2, true} = AttemptLedger.configured_schema(@namespace, @identity, path: path)
    assert :ok = AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, path: path)

    assert {:error, :binding_downgrade_denied} =
             AttemptLedger.configured_mode("legacy", @namespace, @identity, path: path)

    assert {:error, :gate2_profile_incomplete} =
             AttemptLedger.configured_mode("gate2_enforced", @namespace, @identity, path: path)
  end

  test "configured schema rejects malformed schema two history", %{root: root} do
    path = seed_committed_schema2(root, true)

    assert {:error, :storage_corrupt} = AttemptLedger.configured_schema(@namespace, @identity, path: path)

    assert {:error, :storage_corrupt} =
             AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, path: path)
  end

  test "configured schema denies schema two metadata without a committed receipt", %{ledger: ledger, root: root} do
    _ledger = install_gate2_record(ledger, "uncommitted", %{})

    assert {:error, :migration_in_progress} = AttemptLedger.configured_schema(@namespace, @identity, root: root)

    assert {:error, :migration_in_progress} =
             AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, root: root)
  end

  test "configured schema rejects unsupported stored versions", %{ledger: ledger, root: root} do
    :ok = :dets.insert(ledger.table, {{:meta, @namespace}, %{schema_version: 99}})
    :ok = :dets.sync(ledger.table)

    assert {:error, :unsupported_schema} = AttemptLedger.configured_schema(@namespace, @identity, root: root)

    assert {:error, :unsupported_schema} =
             AttemptLedger.configured_mode("gate2_foundation", @namespace, @identity, root: root)
  end

  test "requested Gate2 fence reference is read from durable lineage", %{ledger: ledger} do
    identity = %Identity{
      runtime_attempt_id: "attempt-requested",
      work_item_id: "requested-item",
      lineage_generation: "lineage-requested-item",
      responsibility: "implementation",
      runtime_profile: "implementation"
    }

    reference = %{
      grant_id: "grant-requested",
      project_namespace: @namespace,
      runtime_identity: identity,
      fence_epoch: 1,
      grant_sha256: String.duplicate("a", 64)
    }

    gate2_fence = %{reference: reference, status: :requested}

    ledger =
      install_gate2_record(ledger, "requested-item", %{
        in_flight: true,
        authority_fence: %{
          state: :bound,
          runtime_attempt: identity,
          route_fingerprint: nil,
          gate2_fence: gate2_fence
        },
        boundary_binding: %{
          kind: :gate2,
          binding_version: 1,
          lineage_binding_id: "requested-binding",
          resource_ledger_namespace: @namespace
        }
      })

    assert {:ok, ^reference} = AttemptLedger.gate2_fence_reference(ledger, "requested-item")
  end

  @r05_envelopes [:unsupported_key, :record_route_only, :fence_route_only, :future_route_pair, :missing_record_route]
  for envelope <- @r05_envelopes,
      read_path <- [:current, :open_lineages, :reference, :configured_schema, :snapshot, :reopen] do
    @tag :r05_envelope
    test "unsupported Gate2 envelope #{envelope} fails through #{read_path}", %{root: root} do
      path = seed_committed_schema2(root)
      {:ok, ledger} = AttemptLedger.open(@namespace, @identity, path: path)
      ledger = install_coherent_gate2_record(ledger)
      record = current!(ledger, "coherent") |> unsupported_gate2_envelope(unquote(envelope))
      assert :ok = :dets.insert(ledger.table, {{:current, "coherent"}, record})
      assert :ok = :dets.sync(ledger.table)
      assert_incoherent_read(unquote(read_path), ledger, path)
    end
  end

  @r04_states [:missing_fence, :armed, :bound_without_reference, :released, :closed_missing, :closed_released]
  for state <- @r04_states,
      read_path <- [:current, :open_lineages, :reference, :configured_schema, :reopen] do
    @tag :r04_admission
    test "impossible Gate2 #{state} fails closed through #{read_path}", %{root: root} do
      path = seed_committed_schema2(root)
      {:ok, ledger} = AttemptLedger.open(@namespace, @identity, path: path)
      ledger = install_coherent_gate2_record(ledger)
      record = current!(ledger, "coherent") |> impossible_gate2_state(unquote(state))
      assert :ok = :dets.insert(ledger.table, {{:current, "coherent"}, record})
      assert :ok = :dets.sync(ledger.table)
      assert_incoherent_read(unquote(read_path), ledger, path)
    end
  end

  for state <- [:missing_fence, :armed, :released, :closed_released, :bound_requested] do
    @tag :r04_admission
    test "impossible Gate2 history #{state} blocks scans and admission", %{root: root} do
      path = seed_committed_schema2(root)
      {:ok, ledger} = AttemptLedger.open(@namespace, @identity, path: path)
      ledger = install_coherent_gate2_record(ledger)
      record = current!(ledger, "coherent") |> impossible_gate2_state(unquote(state))
      key = {:history, record.lineage_id}
      assert :ok = :dets.insert(ledger.table, {key, record})
      assert :ok = :dets.sync(ledger.table)
      assert {:error, {:corrupt_attempt_record, ^key, :invalid_record}} = AttemptLedger.history(ledger)
      assert {:error, _} = AttemptLedger.open_lineages(ledger)
      assert {:error, :storage_corrupt} = AttemptLedger.configured_schema(@namespace, @identity, path: path)
      assert_incoherent_read(:reopen, ledger, path)
    end
  end

  @r01_corruptions ~w(
    work_item lineage outer_identity reference_namespace binding_namespace binding_namespace_without_fence
    outer_work_item_without_fence outer_lineage_without_fence
    released_work_item_without_fence released_lineage_without_fence
  )a
  for corruption <- @r01_corruptions,
      read_path <- [:current, :reference, :configured_schema, :reopen] do
    @tag :r01_coherence
    @tag r01_nonbound: corruption in [:released_work_item_without_fence, :released_lineage_without_fence]
    @tag r01_outer: corruption in [:outer_work_item_without_fence, :outer_lineage_without_fence]
    test "persisted Gate2 #{corruption} mismatch fails closed through #{read_path}", %{root: root} do
      corruption = unquote(corruption)
      read_path = unquote(read_path)
      path = seed_committed_schema2(root)
      {:ok, ledger} = AttemptLedger.open(@namespace, @identity, path: path)
      ledger = install_coherent_gate2_record(ledger)
      assert {:ok, original} = AttemptLedger.current(ledger, "coherent")
      inconsistent = corrupt_gate2_identity(original, corruption)
      assert :ok = :dets.insert(ledger.table, {{:current, "coherent"}, inconsistent})
      assert :ok = :dets.sync(ledger.table)

      assert_incoherent_read(read_path, ledger, path)
    end
  end

  @tag :r01_coherence
  test "Gate2 history without an embedded fence still enforces resource namespace", %{root: root} do
    path = seed_committed_schema2(root)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity, path: path)
    [{key, history}] = :dets.match_object(ledger.table, {{:history, :_}, :_})
    inconsistent = Map.put(history, :boundary_binding, @gate2_binding)
    inconsistent = put_in(inconsistent.boundary_binding.resource_ledger_namespace, "other-project")
    assert :ok = :dets.insert(ledger.table, {key, inconsistent})
    assert :ok = :dets.sync(ledger.table)
    assert {:error, {:corrupt_attempt_record, ^key, :invalid_record}} = AttemptLedger.history(ledger)
    assert {:error, :storage_corrupt} = AttemptLedger.configured_schema(@namespace, @identity, path: path)
    assert :ok = AttemptLedger.close(ledger)
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity, path: path)
  end

  test "durable Gate2 binding requires the boundary owner process", %{root: root} do
    path = seed_committed_schema2(root)
    {:ok, ledger} = AttemptLedger.open(@namespace, @identity, path: path)
    on_exit(fn -> AttemptLedger.close(ledger) end)

    assert {:error, :gate2_boundary_required} =
             AttemptLedger.bind_gate2_fence_from_boundary(ledger, "issue", %{})
  end

  test "legacy release rejects a valid Gate2 bound record", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{})
    before = current!(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.release_armed_authority_fence(ledger, "gate2")
    assert current!(ledger, "gate2") == before
  end

  test "put cannot remove or replace gate2 binding", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{})
    record = current!(ledger, "gate2")

    for rewritten <- [Map.delete(record, :boundary_binding), Map.put(record, :boundary_binding, %{kind: :legacy})] do
      assert {:error, :attempt_resource_verification_required} = AttemptLedger.put(ledger, rewritten)
      assert current!(ledger, "gate2") == record
    end

    fresh_gate2 = %{record | issue_id: "fresh", lineage_id: "lineage-fresh"}
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.put(ledger, fresh_gate2)
    assert :not_found = AttemptLedger.current(ledger, "fresh")
  end

  test "put rejects same-binding lineage replacement", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{})
    record = current!(ledger, "gate2")

    assert {:error, :attempt_resource_verification_required} =
             AttemptLedger.put(ledger, %{record | lineage_id: "lineage-replaced"})

    assert current!(ledger, "gate2") == record
  end

  test "put rejects same-binding released fence injection", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{})
    record = current!(ledger, "gate2")

    assert {:error, :attempt_resource_verification_required} =
             AttemptLedger.put(ledger, %{record | authority_fence: %{state: :released}})

    assert current!(ledger, "gate2") == record
  end

  test "put cannot overwrite a corrupt gate2 binding", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "corrupt", %{})
    record = current!(ledger, "corrupt")
    corrupt = %{record | boundary_binding: %{kind: :gate2, binding_version: 1}}
    :ok = :dets.insert(ledger.table, {{:current, "corrupt"}, corrupt})
    :ok = :dets.sync(ledger.table)

    assert {:error, :invalid_record} = AttemptLedger.put(ledger, Map.put(record, :boundary_binding, %{kind: :legacy}))
    assert {:error, :invalid_record} = AttemptLedger.current(ledger, "corrupt")
  end

  test "safety clear close fence and rearm cannot downgrade binding", %{ledger: ledger} do
    ledger = install_gate2_record(ledger, "gate2", %{})
    before = current!(ledger, "gate2")

    identity = %Identity{
      runtime_attempt_id: "attempt-a",
      work_item_id: "gate2",
      lineage_generation: before.lineage_id,
      responsibility: "implementation",
      runtime_profile: "implementation"
    }

    safety_result = AttemptLedger.persist_safety(ledger, "gate2", before.safety_counters, in_flight: false)
    assert {:error, :attempt_resource_verification_required} = safety_result
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.clear_in_flight(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.close_lineage(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.confirm_lineage_close(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.bind_runtime_attempt(ledger, "gate2", identity)
    suspension_result = AttemptLedger.mark_suspension_pending(ledger, "gate2", identity, %{})
    assert {:error, :attempt_resource_verification_required} = suspension_result
    release_result = AttemptLedger.release_authority_fence(ledger, "gate2", identity)
    assert {:error, :attempt_resource_verification_required} = release_result

    assert {:error, :attempt_resource_verification_required} =
             AttemptLedger.release_suspension_fence(ledger, "gate2", identity, %SuspensionContext{})

    assert {:error, :attempt_resource_verification_required} = AttemptLedger.release_armed_authority_fence(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.begin_attempt(ledger, "gate2")
    assert {:error, :attempt_resource_verification_required} = AttemptLedger.fence_attempt(ledger, "gate2")
    assert {:error, :gate2_boundary_required} = AttemptLedger.rearm(ledger, "gate2", "reason", "operator", 1)
    assert current!(ledger, "gate2") == before
  end

  defp unsupported_gate2_envelope(record, :unsupported_key),
    do: put_in(record.authority_fence, Map.put(record.authority_fence, :cleanup_verified, true))

  defp unsupported_gate2_envelope(record, :record_route_only), do: %{record | route_fingerprint: "future-route"}
  defp unsupported_gate2_envelope(record, :fence_route_only), do: put_in(record.authority_fence.route_fingerprint, "future-route")

  defp unsupported_gate2_envelope(record, :future_route_pair) do
    record = unsupported_gate2_envelope(record, :fence_route_only)
    %{record | route_fingerprint: "future-route"}
  end

  defp unsupported_gate2_envelope(record, :missing_record_route), do: Map.delete(record, :route_fingerprint)

  defp impossible_gate2_state(record, :bound_requested), do: record

  defp impossible_gate2_state(record, :missing_fence), do: %{record | in_flight: false, authority_fence: nil}
  defp impossible_gate2_state(record, :armed), do: %{record | authority_fence: %{state: :armed}}

  defp impossible_gate2_state(record, :bound_without_reference),
    do: %{record | authority_fence: Map.delete(record.authority_fence, :gate2_fence)}

  defp impossible_gate2_state(record, :released),
    do: %{record | in_flight: false, authority_fence: %{state: :released}}

  defp impossible_gate2_state(record, :closed_missing),
    do: %{impossible_gate2_state(record, :missing_fence) | status: :closed}

  defp impossible_gate2_state(record, :closed_released),
    do: %{impossible_gate2_state(record, :released) | status: :closed}

  defp assert_incoherent_read(:snapshot, ledger, _path) do
    rows = :dets.foldl(fn row, acc -> [row | acc] end, [], ledger.table)
    assert {:error, :storage_corrupt} = AttemptLedger.validate_snapshot(@namespace, @identity, rows, 2)
    AttemptLedger.close(ledger)
  end

  defp assert_incoherent_read(:open_lineages, ledger, _path) do
    assert {:error, {:corrupt_attempt_record, {:current, "coherent"}, :invalid_record}} =
             AttemptLedger.open_lineages(ledger)

    AttemptLedger.close(ledger)
  end

  defp assert_incoherent_read(:current, ledger, _path) do
    assert {:error, :invalid_record} = AttemptLedger.current(ledger, "coherent")
    assert {:error, :invalid_record} = AttemptLedger.release_armed_authority_fence(ledger, "coherent")
    AttemptLedger.close(ledger)
  end

  defp assert_incoherent_read(:reference, ledger, _path) do
    assert {:error, :storage_corrupt} = AttemptLedger.gate2_fence_reference(ledger, "coherent")
    AttemptLedger.close(ledger)
  end

  defp assert_incoherent_read(:configured_schema, ledger, path) do
    assert {:error, :storage_corrupt} = AttemptLedger.configured_schema(@namespace, @identity, path: path)
    AttemptLedger.close(ledger)
  end

  defp assert_incoherent_read(:reopen, ledger, path) do
    assert :ok = AttemptLedger.close(ledger)
    bytes = File.read!(path)
    assert {:error, :migration_in_progress} = AttemptLedger.open(@namespace, @identity, path: path)
    assert File.read!(path) == bytes
  end

  defp install_coherent_gate2_record(ledger), do: install_gate2_record(ledger, "coherent", %{})

  defp corrupt_gate2_identity(record, :work_item), do: put_in(record.authority_fence.gate2_fence.reference.runtime_identity.work_item_id, "other-item")
  defp corrupt_gate2_identity(record, :lineage), do: put_in(record.authority_fence.gate2_fence.reference.runtime_identity.lineage_generation, "other-lineage")
  defp corrupt_gate2_identity(record, :outer_identity), do: put_in(record.authority_fence.runtime_attempt.runtime_attempt_id, "other-attempt")
  defp corrupt_gate2_identity(record, :reference_namespace), do: put_in(record.authority_fence.gate2_fence.reference.project_namespace, "other-project")
  defp corrupt_gate2_identity(record, :binding_namespace), do: put_in(record.boundary_binding.resource_ledger_namespace, "other-project")

  defp corrupt_gate2_identity(record, :released_work_item_without_fence) do
    record = corrupt_gate2_identity(record, :outer_work_item_without_fence)
    %{record | in_flight: false, authority_fence: %{record.authority_fence | state: :released}}
  end

  defp corrupt_gate2_identity(record, :released_lineage_without_fence) do
    record = corrupt_gate2_identity(record, :outer_lineage_without_fence)
    %{record | in_flight: false, authority_fence: %{record.authority_fence | state: :released}}
  end

  defp corrupt_gate2_identity(record, :outer_work_item_without_fence) do
    record = put_in(record.authority_fence.runtime_attempt.work_item_id, "other-item")
    %{record | authority_fence: Map.delete(record.authority_fence, :gate2_fence)}
  end

  defp corrupt_gate2_identity(record, :outer_lineage_without_fence) do
    record = put_in(record.authority_fence.runtime_attempt.lineage_generation, "other-lineage")
    %{record | authority_fence: Map.delete(record.authority_fence, :gate2_fence)}
  end

  defp corrupt_gate2_identity(record, :binding_namespace_without_fence) do
    record = corrupt_gate2_identity(record, :binding_namespace)
    %{record | authority_fence: Map.delete(record.authority_fence, :gate2_fence)}
  end

  defp install_gate2_record(ledger, issue_id, overrides) do
    record = gate2_record(issue_id)
    record = Map.merge(record, overrides)
    :ok = :dets.insert(ledger.table, {{:current, issue_id}, record})
    :ok = :dets.insert(ledger.table, {{:meta, @namespace}, %{schema_version: 2, project_namespace: @namespace, tracker_identity: @identity}})
    :ok = :dets.sync(ledger.table)
    %{ledger | schema_version: 2}
  end

  defp gate2_record(issue_id) do
    identity = %Identity{
      runtime_attempt_id: "attempt-#{issue_id}",
      work_item_id: issue_id,
      lineage_generation: "lineage-#{issue_id}",
      responsibility: "implementation",
      runtime_profile: "implementation"
    }

    reference = %{grant_id: "grant-#{issue_id}", project_namespace: @namespace, runtime_identity: identity}
    reference = Map.merge(reference, %{fence_epoch: 1, grant_sha256: String.duplicate("a", 64)})

    %{
      schema_version: 2,
      project_namespace: @namespace,
      issue_id: issue_id,
      lineage_id: "lineage-#{issue_id}",
      safety_counters: %{ordinary_failures: 0, ordinary_retries: 0, review_cycles: 0},
      status: :open,
      stop_reason: nil,
      route_fingerprint: nil,
      in_flight: true,
      authority_fence: %{
        state: :bound,
        runtime_attempt: identity,
        route_fingerprint: nil,
        gate2_fence: %{reference: reference, status: :requested}
      },
      close_pending: false,
      updated_at: 1,
      boundary_binding: @gate2_binding
    }
  end

  defp current!(ledger, issue_id) do
    assert {:ok, record} = AttemptLedger.current(ledger, issue_id)
    record
  end

  defp seed_committed_schema2(root, malformed_history? \\ false) do
    migration_root = Path.join(root, "committed-schema2")
    File.mkdir_p!(migration_root)
    path = AttemptLedger.path_for(@namespace, root: migration_root)
    {:ok, legacy} = AttemptLedger.open(@namespace, @identity, path: path)
    :ok = AttemptLedger.close(legacy)

    request = %{
      project_namespace: @namespace,
      tracker_identity_sha256:
        @identity
        |> :erlang.term_to_binary([:deterministic])
        |> then(&:crypto.hash(:sha256, &1))
        |> Base.encode16(case: :lower),
      authority_ref: "compatibility-test-schema2-receipt",
      source_schema: 1,
      target_schema: 2
    }

    encoded = request |> :erlang.term_to_binary([:deterministic]) |> Base.encode64()
    code_args = Enum.flat_map(:code.get_path(), fn code_path -> ["-pa", List.to_string(code_path)] end)

    script =
      "request = System.argv() |> Enum.at(1) |> Base.decode64!() |> :erlang.binary_to_term([:safe]); path = System.argv() |> Enum.at(0); Application.put_env(:symphony_elixir, :attempt_ledger_root, Path.dirname(path)); result = SymphonyElixir.AgentRuntime.AttemptLedgerMigration.migrate_v1_to_v2(path, request); IO.inspect(result)"

    {output, 0} =
      System.cmd(System.find_executable("elixir"), code_args ++ ["-e", script, "--", path, encoded], stderr_to_stdout: true)

    assert output =~ "{:ok,"

    record = %{
      schema_version: 2,
      project_namespace: @namespace,
      issue_id: "compatibility-history",
      lineage_id: "compatibility-lineage",
      safety_counters: %{ordinary_failures: 0, ordinary_retries: 0, review_cycles: 0},
      status: :closed,
      stop_reason: nil,
      route_fingerprint: nil,
      in_flight: false,
      authority_fence: nil,
      close_pending: false,
      updated_at: 1_700_000_000_000,
      closed_reason: :completed,
      rearm_reason: nil,
      rearmed_by: nil,
      rearmed_at: nil,
      boundary_binding: %{kind: :legacy}
    }

    table = :gate2_attempt_compatibility_receipt
    {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(path), type: :set)
    :ok = :dets.insert(table, [{{:history, "compatibility-lineage"}, record}, {{:current, "compatibility-current"}, gate2_record("compatibility-current")}])

    if malformed_history? do
      :ok = :dets.insert(table, {{:history, "broken-history"}, :corrupt})
    end

    :ok = :dets.sync(table)
    :ok = :dets.close(table)
    path
  end
end
