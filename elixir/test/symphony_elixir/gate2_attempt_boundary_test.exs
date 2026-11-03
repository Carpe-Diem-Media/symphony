defmodule SymphonyElixir.Gate2AttemptBoundaryTest do
  use ExUnit.Case, async: false

  alias SymphonyElixir.AgentRuntime.AttemptBoundary
  alias SymphonyElixir.AgentRuntime.AttemptLedger
  alias SymphonyElixir.AgentRuntime.AttemptResource
  alias SymphonyElixir.AgentRuntime.CleanupEvidenceRef
  alias SymphonyElixir.AgentRuntime.QuarantineDisposition
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  setup context do
    root = Path.join(System.tmp_dir!(), "gate2-boundary-" <> Base.encode16(:crypto.strong_rand_bytes(12), case: :lower))
    File.mkdir_p!(root)
    name = String.to_atom("gate2_boundary_owner_#{System.unique_integer([:positive])}")
    Process.register(self(), name)
    attempt_path = Path.join(root, "project-1.dets")
    seed_attempt_ledger(attempt_path, include_current: not (context[:fresh_gate2] || false))

    {:ok, attempt_ledger} =
      AttemptLedger.open("project-1", %{tracker_kind: "memory", provider_scope: %{project_slug: "project-1"}}, path: attempt_path)

    resource_opts = [path: Path.join(root, "resources.dets"), project_namespace: "project-1", host_id: "host-1"]

    resource_opts =
      if context[:resource_fault] do
        Keyword.put(resource_opts, :write_fun, fn
          _table, {{:resource, _id}, _resource} -> {:error, :injected_write_failure}
          table, row -> :dets.insert(table, row)
        end)
      else
        resource_opts
      end

    {:ok, boundary} =
      AttemptBoundary.start_link(
        owner_name: name,
        attempt_ledger: attempt_ledger,
        resource_ledger_opts: resource_opts
      )

    on_exit(fn ->
      if Process.alive?(boundary), do: GenServer.stop(boundary)
      AttemptLedger.close(attempt_ledger)
      if Process.whereis(name) == self(), do: Process.unregister(name)
      File.rm_rf!(root)
    end)

    {:ok, boundary: boundary, attempt_ledger: attempt_ledger, attempt_path: attempt_path}
  end

  test "foundation cannot mint active grant or usable permit", context do
    assert {:error, :gate2_dormant} = AttemptBoundary.authorize(context.boundary, identity(), authorization_request())
    operation = operation_request()
    assert {:error, :gate2_dormant} = AttemptBoundary.authorize_operation(context.boundary, grant_ref(), operation)
  end

  @tag fresh_gate2: true
  test "foundation fence reports requested not verified", context do
    seed_resource(context.boundary)
    assert :ok = AttemptLedger.bind_gate2_fence_sync(context.attempt_ledger, "item-1", grant_ref())
    assert {:ok, fence} = AttemptBoundary.fence(context.boundary, %{grant_ref: grant_ref(), reason: :cancellation})
    assert fence.status == :requested
    assert is_nil(fence.evidence_ref)
    assert {:ok, record} = AttemptLedger.current(context.attempt_ledger, "item-1")
    assert record.authority_fence.gate2_fence.requested_reason == :cancellation

    if context[:fresh_gate2] do
      binding = record.boundary_binding
      assert binding.kind == :gate2
      assert binding.lineage_binding_id != grant_ref().grant_id
      assert :ok = GenServer.stop(context.boundary)
      assert :ok = AttemptLedger.close(context.attempt_ledger)
      tracker_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "project-1"}}
      assert {:ok, reopened} = AttemptLedger.open("project-1", tracker_identity, path: context.attempt_path)
      assert {:ok, recovered} = AttemptLedger.current(reopened, "item-1")
      assert recovered.authority_fence.gate2_fence.requested_reason == :cancellation
      assert :ok = AttemptLedger.close(reopened)
    end
  end

  test "release rejects missing forged stale and matching-shaped references", context do
    assert {:error, :cleanup_reference_missing} = AttemptBoundary.release(context.boundary, nil)
    assert {:error, :cleanup_reference_invalid} = AttemptBoundary.release(context.boundary, %{})
    generation = AttemptBoundary.reconcile_startup(context.boundary) |> elem(1)
    stale_evidence = cleanup_ref(generation, fence_epoch: 2)
    assert {:error, :cleanup_reference_stale} = AttemptBoundary.release(context.boundary, stale_evidence)
    seed_resource(context.boundary)
    assert :ok = AttemptLedger.bind_gate2_fence_sync(context.attempt_ledger, "item-1", grant_ref())
    evidence = cleanup_ref(generation)

    assert {:error, :attempt_resource_verification_required} =
             AttemptLedger.release_gate2_authority_fence(context.attempt_ledger, "item-1", identity(), evidence)

    assert {:error, :cleanup_verifier_unavailable} = AttemptBoundary.release(context.boundary, evidence)
  end

  @tag fresh_gate2: true
  test "missing durable grant denies cleanup without crashing the boundary", context do
    assert :not_found = AttemptLedger.gate2_fence_reference(context.attempt_ledger, "item-1")
    {:ok, generation} = AttemptBoundary.reconcile_startup(context.boundary)
    assert {:error, :cleanup_reference_stale} = AttemptBoundary.release(context.boundary, cleanup_ref(generation))
    assert {:ok, ^generation} = AttemptBoundary.reconcile_startup(context.boundary)
  end

  test "malformed fence requests return the stable error without terminating the boundary", context do
    for request <- [
          %{},
          %{grant_ref: grant_ref()},
          %{reason: :failure},
          %{grant_ref: grant_ref(), reason: :failure, unexpected: "rejected"}
        ] do
      assert {:error, :invalid_request} = AttemptBoundary.fence(context.boundary, request)
    end

    assert {:ok, _generation} = AttemptBoundary.reconcile_startup(context.boundary)
  end

  test "configured callback cannot produce cleanup authority", _context do
    options = [owner_name: SymphonyElixir.Orchestrator, resource_ledger_opts: [], cleanup_verifier: fn _ -> :ok end]

    assert {:error, :invalid_request} =
             AttemptBoundary.start_link(options)
  end

  test "startup syncs new generation and restores no active authority", context do
    assert {:ok, generation} = AttemptBoundary.reconcile_startup(context.boundary)
    assert generation.sequence >= 1
    assert {:error, :gate2_dormant} = AttemptBoundary.authorize(context.boundary, identity(), authorization_request())
  end

  test "partial grant binding and ambiguous ownership block reuse", context do
    reference = grant_ref()
    assert {:error, :grant_not_found} = AttemptLedger.bind_gate2_fence_sync(context.attempt_ledger, "item-1", reference)

    seed_resource(context.boundary)
    assert :ok = AttemptLedger.bind_gate2_fence_sync(context.attempt_ledger, "item-1", reference)

    duplicate = resource(context.boundary, resource_id: "resource-2")
    assert {:error, :resource_conflict} = AttemptBoundary.reserve_resource_sync(context.boundary, duplicate)
    assert {:error, :ownership_ambiguous} = AttemptBoundary.fence(context.boundary, %{grant_ref: reference, reason: :restart})

    forged_identity = Map.put(identity(), :secret, "must-not-be-persisted")
    forged_reference = Map.put(reference, :runtime_identity, forged_identity)
    result = AttemptLedger.bind_gate2_fence_sync(context.attempt_ledger, "item-1", forged_reference)
    assert {:error, :invalid_request} = result
  end

  @tag resource_fault: true
  test "poisoned resource ledger blocks boundary reuse", context do
    assert {:error, :write_failed} = AttemptBoundary.reserve_resource_sync(context.boundary, resource(context.boundary))
    request = authorization_request()
    assert {:error, :storage_unavailable} = AttemptBoundary.authorize(context.boundary, identity(), request)
  end

  defp identity do
    %Identity{runtime_attempt_id: "attempt-1", work_item_id: "item-1", lineage_generation: "lineage-1", responsibility: "builder", runtime_profile: "profile-1"}
  end

  defp authorization_request do
    %{
      route_fingerprint: "route-1",
      subscription_registration_id: "registration-1",
      credential_generation: 1,
      source_admission_policy_sha256: digest(),
      process_policy_sha256: digest(),
      network_policy_sha256: digest(),
      tool_policy_sha256: digest(),
      capacity_profile_sha256: digest()
    }
  end

  defp operation_request do
    %{operation_id: "operation-1", operation: :workspace_read, resource_id: "resource-1", arguments_sha256: digest()}
  end

  defp grant_ref do
    %{grant_id: "grant-1", project_namespace: "project-1", runtime_identity: identity(), fence_epoch: 1, grant_sha256: digest()}
  end

  defp cleanup_ref(generation, overrides \\ []) do
    attrs = %{
      schema_version: 1,
      evidence_id: "evidence-1",
      evidence_sha256: digest(),
      project_namespace: "project-1",
      grant_id: "grant-1",
      runtime_identity: identity(),
      fence_epoch: 1,
      resource_set_sha256: digest(),
      verification_generation: generation,
      verifier_implementation_sha256: digest()
    }

    attrs = Map.merge(attrs, Map.new(overrides))
    {:ok, ref} = CleanupEvidenceRef.new(attrs)
    ref
  end

  for operation <- [:fence, :release, :ledger_release] do
    @tag failed_read_operation: operation
    test "#{operation} storage read failure blocks later boundary calls", context do
      seed_resource(context.boundary)
      assert :ok = AttemptLedger.bind_gate2_fence_sync(context.attempt_ledger, "item-1", grant_ref())
      {:ok, generation} = AttemptBoundary.reconcile_startup(context.boundary)
      assert :ok = AttemptLedger.close(context.attempt_ledger)

      result =
        case context.failed_read_operation do
          :fence ->
            AttemptBoundary.fence(context.boundary, %{grant_ref: grant_ref(), reason: :failure})

          :release ->
            AttemptBoundary.release(context.boundary, cleanup_ref(generation))

          :ledger_release ->
            evidence = cleanup_ref(generation)
            AttemptLedger.release_gate2_authority_fence(context.attempt_ledger, "item-1", identity(), evidence)
        end

      assert {:error, :storage_unavailable} = result
      request = authorization_request()
      assert {:error, :storage_unavailable} = AttemptBoundary.authorize(context.boundary, identity(), request)
    end
  end

  defp seed_attempt_ledger(path, opts) do
    identity = identity()
    tracker_identity = %{tracker_kind: "memory", provider_scope: %{project_slug: "project-1"}}
    {:ok, legacy} = AttemptLedger.open("project-1", tracker_identity, path: path)
    :ok = AttemptLedger.close(legacy)

    request = %{
      project_namespace: "project-1",
      tracker_identity_sha256: tracker_identity |> :erlang.term_to_binary([:deterministic]) |> then(&:crypto.hash(:sha256, &1)) |> Base.encode16(case: :lower),
      authority_ref: "t5-test-maintenance",
      source_schema: 1,
      target_schema: 2
    }

    {:ok, _receipt} = migrate_in_isolated_vm(path, request)

    metadata = %{schema_version: 2, project_namespace: "project-1", tracker_identity: tracker_identity}

    record = %{
      schema_version: 2,
      project_namespace: "project-1",
      issue_id: "item-1",
      lineage_id: "lineage-1",
      safety_counters: %{ordinary_failures: 0, ordinary_retries: 0, review_cycles: 0},
      status: :open,
      stop_reason: nil,
      route_fingerprint: "route-1",
      in_flight: true,
      authority_fence: %{state: :bound, runtime_attempt: identity, route_fingerprint: "route-1"},
      close_pending: false,
      updated_at: 1_700_000_000_000,
      boundary_binding: %{kind: :gate2, binding_version: 1, lineage_binding_id: "binding-1", resource_ledger_namespace: "project-1"}
    }

    table = :gate2_attempt_seed_fixture
    {:ok, ^table} = :dets.open_file(table, file: String.to_charlist(path), type: :set)
    rows = [{{:meta, "project-1"}, metadata}]
    rows = if Keyword.get(opts, :include_current, true), do: [{{:current, "item-1"}, record} | rows], else: rows
    :ok = :dets.insert(table, rows)
    :ok = :dets.sync(table)
    :ok = :dets.close(table)
  end

  defp migrate_in_isolated_vm(path, request) do
    encoded = request |> :erlang.term_to_binary([:deterministic]) |> Base.encode64()
    code_args = Enum.flat_map(:code.get_path(), fn code_path -> ["-pa", List.to_string(code_path)] end)

    script = """
    [path, encoded] = System.argv()
    Application.put_env(:symphony_elixir, :attempt_ledger_root, Path.dirname(path))
    request = encoded |> Base.decode64!() |> :erlang.binary_to_term([:safe])
    result = SymphonyElixir.AgentRuntime.AttemptLedgerMigration.migrate_v1_to_v2(path, request)
    IO.puts("T5_RESULT=" <> Base.encode64(:erlang.term_to_binary(result, [:deterministic])))
    """

    {output, 0} = System.cmd(System.find_executable("elixir"), code_args ++ ["-e", script, "--", path, encoded], stderr_to_stdout: true)
    [_, result] = Regex.run(~r/T5_RESULT=([^\n]+)/, output)
    result |> Base.decode64!() |> :erlang.binary_to_term([:safe])
  end

  defp seed_resource(boundary) do
    resource = resource(boundary)
    assert {:ok, ^resource} = AttemptBoundary.reserve_resource_sync(boundary, resource)
  end

  defp resource(boundary, overrides \\ []) do
    {:ok, generation} = AttemptBoundary.reconcile_startup(boundary)
    {:ok, quarantine} = QuarantineDisposition.new(%{state: :clear, reason: nil, evidence_ref: nil, generation: generation, resolution_ref: nil})

    {:ok, resource} =
      AttemptResource.new(%{
        schema_version: 1,
        resource_id: Keyword.get(overrides, :resource_id, "resource-1"),
        project_namespace: "project-1",
        grant_id: "grant-1",
        runtime_identity: identity(),
        class: :workspace,
        state: :reserved,
        revision: 0,
        stable_locator: Keyword.get(overrides, :stable_locator, "locator-1"),
        allocation_identity_sha256: nil,
        capacity_profile_sha256: digest(),
        owner_host_id: "host-1",
        creation_generation: generation,
        reconciliation_generation: generation,
        last_evidence_ref: nil,
        quarantine: quarantine
      })

    resource
  end

  defp digest, do: String.duplicate("a", 64)
end
