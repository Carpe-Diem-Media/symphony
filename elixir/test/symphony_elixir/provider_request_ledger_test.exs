defmodule SymphonyElixir.ProviderEffect.RequestLedgerTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.ProviderEffect.RequestLedger

  test "durably records two ordered requests and returns a one-use send permit" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)

    assert {:ok, first} = RequestLedger.prepare(ledger, attrs(1))
    assert first.state == :pre_send_intent
    assert first.send_may_have_occurred == false

    assert {:ok, permit, possible_send} =
             RequestLedger.acknowledge_possible_send(ledger, first.request_id, first.revision)

    assert possible_send.revision == 2
    assert possible_send.send_may_have_occurred
    assert String.match?(permit.ack_nonce, ~r/\A[0-9a-f]{64}\z/)
    assert {:ok, consumed} = RequestLedger.consume_permit(permit, first.request_id, 2)
    assert consumed.consumed?

    assert {:error, :invalid_or_reused_permit} =
             RequestLedger.consume_permit(consumed, first.request_id, 2)

    assert {:error, :invalid_or_reused_permit} =
             RequestLedger.consume_permit(permit, first.request_id, 2)

    assert {:ok, _invoked} =
             RequestLedger.record_observation(ledger, first.request_id, :invocation_observed, %{})

    assert {:ok, _accepted} =
             RequestLedger.record_observation(ledger, first.request_id, :accepted, %{
               response_id: "resp_fixture_1",
               upstream_status: 200
             })

    assert {:ok, _terminal} =
             RequestLedger.record_observation(ledger, first.request_id, :terminal, %{
               terminal_kind: "response.completed",
               terminal_digest: digest("terminal-1")
             })

    second_attrs =
      attrs(2)
      |> Map.put(:prior_request_id, first.request_id)
      |> Map.put(:prior_response_id, "resp_fixture_1")
      |> Map.put(:tool_operation_id, "tool-op-1")
      |> Map.put(:tool_call_id, "call-1")
      |> Map.put(:tool_output_digest, digest("tool-output"))
      |> Map.put(:tool_output_bytes, 12)

    assert {:ok, second} = RequestLedger.prepare(ledger, second_attrs)
    assert second.ordinal == 2
    assert {:ok, reopened} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
    assert Enum.map(RequestLedger.records(reopened), & &1.ordinal) == [1, 2]

    first_line = ledger.path |> File.read!() |> String.split("\n", trim: true) |> hd()
    encoded_record = Jason.decode!(first_line)["record"]
    assert encoded_record["source_digest"] == digest("source")
    refute Map.has_key?(encoded_record, "descriptor")
    assert hd(RequestLedger.records(reopened)).descriptor.source_digest == digest("source")

    assert {:ok, stat} = File.stat(ledger.path)
    assert Bitwise.band(stat.mode, 0o777) == 0o600
    assert {:ok, parent_stat} = File.stat(Path.dirname(ledger.path))
    assert Bitwise.band(parent_stat.mode, 0o777) == 0o700
  end

  test "reopening after possible send preserves ambiguity and prevents replay" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)
    assert {:ok, first} = RequestLedger.prepare(ledger, attrs(1))
    assert {:ok, _permit, _} = RequestLedger.acknowledge_possible_send(ledger, first.request_id, 1)

    assert {:ok, reopened} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
    assert [%{state: :possible_send, send_may_have_occurred: true}] = RequestLedger.records(reopened)
    assert {:error, :ordinal_already_used} = RequestLedger.prepare(reopened, attrs(1))
    assert {:error, :ordinal_out_of_order} = RequestLedger.prepare(reopened, attrs(2))
  end

  test "rejects secrets, unknown fields, invalid ordinals, and broken second-request linkage" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)

    assert {:error, :unknown_request_field} = RequestLedger.prepare(ledger, Map.put(attrs(1), :authorization, "bearer secret"))
    assert {:error, :invalid_ordinal} = RequestLedger.prepare(ledger, Map.put(attrs(3), :ordinal, 3))
    assert {:error, :ordinal_out_of_order} = RequestLedger.prepare(ledger, attrs(2))

    assert {:ok, first} = RequestLedger.prepare(ledger, attrs(1))

    assert {:ok, _permit, _possible_send} =
             RequestLedger.acknowledge_possible_send(ledger, first.request_id, 1)

    assert {:ok, updated} = RequestLedger.record_observation(ledger, first.request_id, :invocation_observed, %{})

    assert {:ok, _} =
             RequestLedger.record_observation(ledger, first.request_id, :accepted, %{
               response_id: "resp-1",
               upstream_status: 200
             })

    assert {:ok, _} =
             RequestLedger.record_observation(ledger, first.request_id, :terminal, %{
               terminal_kind: "response.completed",
               terminal_digest: digest("terminal")
             })

    assert {:ok, latest} = RequestLedger.open(ledger.attempt_id, path: ledger.path)

    assert {:error, :invalid_second_request_lineage} =
             RequestLedger.prepare(
               latest,
               attrs(2)
               |> Map.put(:prior_request_id, "other")
               |> Map.put(:prior_response_id, "resp-1")
               |> Map.put(:tool_operation_id, "op")
               |> Map.put(:tool_call_id, "call")
               |> Map.put(:tool_output_digest, digest("out"))
               |> Map.put(:tool_output_bytes, 3)
             )

    assert updated.state == :invocation_observed
  end

  test "a journal filesystem failure blocks request admission" do
    root = temp_root()
    blocker = Path.join(root, "not-a-directory")
    File.write!(blocker, "x")
    assert {:error, _} = RequestLedger.open(Base.url_encode64(<<0::128>>, padding: false), path: Path.join([blocker, "ledger.jsonl"]))
    File.rm_rf!(root)
  end

  test "rejects a corrupt or cross-attempt journal on reopen" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)
    assert {:ok, _} = RequestLedger.prepare(ledger, attrs(1))
    assert {:error, :attempt_mismatch} = RequestLedger.open(Base.url_encode64(<<1::128>>, padding: false), path: ledger.path)
  end

  test "does not reopen admission from a torn, repeated, or out-of-order journal" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)

    assert {:ok, first} = RequestLedger.prepare(ledger, attrs(1))
    assert {:ok, _, _} = RequestLedger.acknowledge_possible_send(ledger, first.request_id, 1)
    assert {:ok, _} = RequestLedger.close_admission(ledger)
    durable_bytes = File.read!(ledger.path)
    [intent, acknowledged, closed] = String.split(durable_bytes, "\n", trim: true)

    for invalid <- [
          intent,
          intent <> "\n{\n",
          intent <> "\n{}\n",
          Enum.join([acknowledged, intent, closed, ""], "\n"),
          Enum.join([intent, acknowledged, acknowledged, closed, ""], "\n"),
          Enum.join([intent, closed, acknowledged, ""], "\n")
        ] do
      File.write!(ledger.path, invalid)
      assert {:error, :journal_corrupt} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
      assert {:error, :journal_corrupt} = RequestLedger.acknowledge_possible_send(ledger, first.request_id, 1)
      assert {:error, :journal_corrupt} = RequestLedger.record_observation(ledger, first.request_id, :ambiguous, %{})
      assert File.read!(ledger.path) == invalid
    end

    File.write!(ledger.path, durable_bytes)
    assert {:ok, reopened} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
    assert reopened.closed?
    assert [%{state: :possible_send, send_may_have_occurred: true}] = RequestLedger.records(reopened)
    assert {:error, :ledger_closed} = RequestLedger.record_observation(reopened, first.request_id, :ambiguous, %{})
    assert {:error, :ledger_closed} = RequestLedger.close_admission(reopened)
  end

  test "cannot record admission closed on a partially written journal event" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)
    assert {:ok, _} = RequestLedger.prepare(ledger, attrs(1))
    incomplete = File.read!(ledger.path) <> "{"
    File.write!(ledger.path, incomplete)

    assert {:error, :journal_sync_failed} = RequestLedger.close_admission(ledger)
    assert {:error, :journal_corrupt} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
    assert File.read!(ledger.path) == incomplete
  end

  test "refuses missing or invalid acknowledgments and never treats them as invocation" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)
    assert {:error, :invalid_request} = RequestLedger.prepare(ledger, Map.put(attrs(1), :request_id, 123))
    assert [] = RequestLedger.records(ledger)
    assert {:ok, first} = RequestLedger.prepare(ledger, attrs(1))
    durable_intent = File.read!(ledger.path)

    assert {:error, :unknown_request} = RequestLedger.acknowledge_possible_send(ledger, "unknown-request", 1)
    assert {:error, :request_not_sendable} = RequestLedger.acknowledge_possible_send(ledger, first.request_id, 2)
    assert {:error, :invalid_transition} = RequestLedger.record_observation(ledger, first.request_id, :terminal, %{})
    assert File.read!(ledger.path) == durable_intent

    assert {:ok, _, _} = RequestLedger.acknowledge_possible_send(ledger, first.request_id, 1)
    assert {:ok, reopened} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
    assert [%{state: :possible_send, revision: 2}] = RequestLedger.records(reopened)
  end

  test "will not open a journal through a symlink or directory" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)
    assert {:ok, _} = RequestLedger.prepare(ledger, attrs(1))
    bytes = File.read!(ledger.path)
    target = Path.join(root, "original")
    File.rename!(ledger.path, target)
    File.ln_s!(target, ledger.path)

    assert {:error, :journal_not_regular} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
    assert File.read!(target) == bytes

    File.rm!(ledger.path)
    File.mkdir!(ledger.path)
    assert {:error, :journal_not_regular} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
    assert File.read!(target) == bytes
  end

  for first_byte <- [0, 248, 252] do
    id = Base.url_encode64(<<first_byte, 0::120>>, padding: false)

    test "authoritative runtime attempt #{id} survives transitions and reopen" do
      id = unquote(id)
      {ledger, root} = open_ledger(id)
      on_exit(fn -> File.rm_rf!(root) end)

      assert {:ok, first} = RequestLedger.prepare(ledger, Map.put(attrs(1), :runtime_attempt_id, id))
      assert first.runtime_attempt_id == id
      assert {:ok, _permit, _} = RequestLedger.acknowledge_possible_send(ledger, first.request_id, 1)
      assert {:ok, reopened} = RequestLedger.open(id, path: ledger.path)
      assert [%{runtime_attempt_id: ^id, state: :possible_send}] = RequestLedger.records(reopened)
      assert {:ok, _} = RequestLedger.record_observation(reopened, first.request_id, :ambiguous, %{})
      assert {:ok, reopened} = RequestLedger.open(id, path: ledger.path)
      assert [%{runtime_attempt_id: ^id, state: :ambiguous}] = RequestLedger.records(reopened)
    end
  end

  for checkpoint <- [:possible_send, :invocation_observed, :accepted] do
    test "worker exit after #{checkpoint} never reopens request admission" do
      checkpoint = unquote(checkpoint)
      {ledger, root} = open_ledger()
      on_exit(fn -> File.rm_rf!(root) end)

      {_pid, monitor} =
        spawn_monitor(fn -> abandon_request_at(ledger, checkpoint) end)

      assert_receive {:DOWN, ^monitor, :process, _pid, :lost_worker}, 2_000
      assert {:ok, reopened} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
      assert [%{request_id: id, state: ^checkpoint, send_may_have_occurred: true}] = RequestLedger.records(reopened)
      assert {:error, :ordinal_already_used} = RequestLedger.prepare(reopened, attrs(1))
      assert {:error, :ordinal_out_of_order} = RequestLedger.prepare(reopened, attrs(2))
      assert {:ok, _} = RequestLedger.record_observation(reopened, id, :ambiguous, %{})
      assert {:ok, %{closed?: true}} = RequestLedger.close_admission(reopened)
      assert {:ok, closed} = RequestLedger.open(ledger.attempt_id, path: ledger.path)
      assert [%{state: :ambiguous}] = RequestLedger.records(closed)
      assert {:error, :ledger_closed} = RequestLedger.prepare(closed, attrs(2))
    end
  end

  test "rejects invalid attempt encodings while preserving request identifier rules" do
    {ledger, root} = open_ledger()
    on_exit(fn -> File.rm_rf!(root) end)

    for id <- [
          "",
          "../escape",
          String.duplicate("A", 23),
          String.duplicate("A", 21) <> "B",
          String.duplicate("A", 21) <> "/",
          String.duplicate("A", 21) <> <<0>>,
          String.duplicate("A", 21) <> "=",
          String.duplicate("A", 4096)
        ] do
      assert {:error, :invalid_identifier} = RequestLedger.open(id, path: ledger.path)
    end

    for request_id <- ["-request", "_request", "../request", String.duplicate("A", 129)] do
      assert {:error, :invalid_identifier} = RequestLedger.prepare(ledger, Map.put(attrs(1), :request_id, request_id))
    end

    assert {:ok, %{request_id: "A.request:1"}} =
             RequestLedger.prepare(ledger, Map.put(attrs(1), :request_id, "A.request:1"))
  end

  defp abandon_request_at(ledger, checkpoint) do
    {:ok, first} = RequestLedger.prepare(ledger, Map.put(attrs(1), :runtime_attempt_id, ledger.attempt_id))
    {:ok, _permit, _} = RequestLedger.acknowledge_possible_send(ledger, first.request_id, 1)

    if checkpoint in [:invocation_observed, :accepted] do
      {:ok, _} = RequestLedger.record_observation(ledger, first.request_id, :invocation_observed, %{})
    end

    if checkpoint == :accepted do
      {:ok, _} = RequestLedger.record_observation(ledger, first.request_id, :accepted, %{response_id: "resp-1"})
    end

    exit(:lost_worker)
  end

  defp open_ledger(id \\ Base.url_encode64(<<0::128>>, padding: false)) do
    root = temp_root()
    {:ok, ledger} = RequestLedger.open(id, path: Path.join(root, "request-effects.jsonl"))
    {ledger, root}
  end

  defp temp_root do
    path = Path.join(System.tmp_dir!(), "provider-request-ledger-#{System.unique_integer([:positive, :monotonic])}")
    File.mkdir_p!(path)
    path
  end

  defp digest(value), do: :crypto.hash(:sha256, value) |> Base.encode16(case: :lower)

  defp attrs(ordinal) do
    Map.new(
      ordinal: ordinal,
      runtime_attempt_id: "runtime-1",
      grant_id: "grant-1",
      project_id: "project-1",
      item_id: "item-1",
      planning_role: "planner",
      source_digest: digest("source"),
      config_digest: digest("config"),
      policy_digest: digest("policy"),
      holder_digest: digest("holder"),
      profile_id: "synthetic-planner",
      host_id: "host-1",
      boot_id: "boot-1",
      credential_generation: "fixture-gen-1",
      context_digest: digest("context"),
      nonce: "frame-nonce-#{ordinal}",
      thread_id: "thread-1",
      turn_id: "turn-1",
      method: "POST",
      url: "https://api.openai.com/v1/responses",
      model: "synthetic-planner-v1",
      catalog_digest: digest("catalog"),
      tool_digest: digest("tool"),
      body_digest: digest("body-#{ordinal}"),
      body_bytes: 128,
      content_type: "application/json",
      stream: true,
      store: false,
      parallel_tool_calls: false,
      permission_id: "permission-1",
      permission_generation: 1,
      lease_id: "lease-1",
      lease_generation: 1,
      deadline_monotonic_ms: System.monotonic_time(:millisecond) + 30_000
    )
  end
end
