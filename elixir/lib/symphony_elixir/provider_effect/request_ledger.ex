defmodule SymphonyElixir.ProviderEffect.RequestLedger do
  @moduledoc "Durable per-attempt journal for two synthetic request effects."

  alias SymphonyElixir.ProviderEffect.RequestRecord

  @schema "H100-REQUEST-EFFECT-1"
  @direct_fields RequestRecord.__struct__() |> Map.keys() |> Enum.reject(&(&1 in [:__struct__, :descriptor]))
  @descriptor_fields ~w(project_id item_id planning_role source_digest config_digest policy_digest holder_digest profile_id host_id boot_id credential_generation nonce tool_call_id tool_output_digest tool_output_bytes catalog_digest tool_digest content_type stream store parallel_tool_calls prior_response_id permission_id permission_generation lease_id lease_generation resolver_digest nftables_digest client_pool_digest upstream_request_id upstream_status terminal_kind terminal_digest cancelled cleanup_ref evidence_refs)a
  @record_fields @direct_fields ++ @descriptor_fields
  @required_attrs ~w(runtime_attempt_id grant_id project_id item_id planning_role source_digest config_digest policy_digest holder_digest profile_id host_id boot_id credential_generation context_digest nonce thread_id turn_id method url model catalog_digest tool_digest body_digest body_bytes content_type stream store parallel_tool_calls permission_id permission_generation lease_id lease_generation deadline_monotonic_ms)a
  @generated_fields [
    :revision,
    :state,
    :send_may_have_occurred,
    :evidence_scope,
    :authenticated,
    :operationally_qualified,
    :response_id,
    :upstream_request_id,
    :upstream_status,
    :terminal_kind,
    :terminal_digest,
    :cancelled,
    :cleanup_ref,
    :evidence_refs
  ]
  @allowed_attrs (@record_fields -- @generated_fields) ++ [:request_id, :ordinal]
  @observation_fields [
    :upstream_request_id,
    :response_id,
    :upstream_status,
    :terminal_kind,
    :terminal_digest,
    :cancelled,
    :cleanup_ref,
    :evidence_refs,
    :thread_id,
    :turn_id
  ]
  @transitions %{
    pre_send_intent: [:possible_send],
    possible_send: [:invocation_observed, :ambiguous],
    invocation_observed: [:accepted, :ambiguous],
    accepted: [:terminal, :ambiguous],
    terminal: [],
    ambiguous: []
  }

  @enforce_keys [:attempt_id, :path, :events, :closed?]
  defstruct [:attempt_id, :path, :events, :closed?]

  defmodule SendPermit do
    @moduledoc "One-use local permission returned after possible-send intent is durable."

    @enforce_keys [:request_id, :revision, :ack_nonce, :consumed?, :claim]
    defstruct [:request_id, :revision, :ack_nonce, :consumed?, :claim]
  end

  @type t :: %__MODULE__{}
  @type send_permit :: %SendPermit{}

  def open(attempt_id, opts \\ [])

  @spec open(String.t(), keyword()) :: {:ok, t()} | {:error, term()}
  def open(attempt_id, opts) when is_binary(attempt_id) and is_list(opts) do
    path = opts |> Keyword.fetch!(:path) |> Path.expand()

    with :ok <- validate_attempt_identifier(attempt_id),
         :ok <- ensure_parent(path),
         {:ok, events} <- read_events(path),
         :ok <- validate_journal(attempt_id, events) do
      {:ok, %__MODULE__{attempt_id: attempt_id, path: path, events: events, closed?: Enum.any?(events, &(&1.kind == :closed))}}
    end
  rescue
    _ -> {:error, :journal_unavailable}
  end

  def open(_, _), do: {:error, :invalid_attempt}

  @spec close(t()) :: :ok | {:error, :invalid_ledger}
  def close(%__MODULE__{}), do: :ok
  def close(_), do: {:error, :invalid_ledger}

  @spec prepare(t(), map()) :: {:ok, RequestRecord.t()} | {:error, term()}
  def prepare(%__MODULE__{closed?: false} = ledger, attrs) when is_map(attrs) do
    with {:ok, ledger} <- refresh(ledger),
         false <- ledger.closed?,
         :ok <- strict_attrs(attrs),
         ordinal <- Map.get(attrs, :ordinal),
         true <- ordinal in [1, 2],
         :ok <- next_ordinal(ledger.events, ordinal),
         :ok <- valid_lineage(ledger.events, attrs, ordinal),
         id when is_binary(id) <- Map.get(attrs, :request_id, random_id()),
         :ok <- validate_identifier(id) do
      record =
        attrs
        |> Map.put(:request_id, id)
        |> Map.put(:ordinal, ordinal)
        |> Map.put(:revision, 1)
        |> Map.put(:state, :pre_send_intent)
        |> Map.put(:send_may_have_occurred, false)
        |> Map.put(:evidence_scope, "SYNTHETIC_PIPE")
        |> Map.put(:authenticated, false)
        |> Map.put(:operationally_qualified, false)
        |> build_record()

      case append(ledger, %{schema: @schema, attempt_id: ledger.attempt_id, kind: :record, record: record}) do
        {:ok, _next} -> {:ok, record}
        {:error, reason} -> {:error, reason}
      end
    else
      {:error, reason} -> {:error, reason}
      false -> {:error, :invalid_ordinal}
      _ -> {:error, :invalid_request}
    end
  end

  def prepare(_, _), do: {:error, :ledger_closed}

  @spec acknowledge_possible_send(t(), String.t(), pos_integer()) ::
          {:ok, send_permit(), RequestRecord.t()} | {:error, term()}
  def acknowledge_possible_send(%__MODULE__{closed?: false} = ledger, request_id, revision) do
    with {:ok, ledger} <- refresh(ledger),
         false <- ledger.closed?,
         {:ok, record} <- current(ledger, request_id),
         true <- record.state == :pre_send_intent and record.revision == revision,
         updated <- %{record | state: :possible_send, revision: revision + 1, send_may_have_occurred: true},
         {:ok, _next} <-
           append(ledger, %{
             schema: @schema,
             attempt_id: ledger.attempt_id,
             kind: :record,
             record: updated
           }) do
      permit = %SendPermit{
        request_id: request_id,
        revision: updated.revision,
        ack_nonce: :crypto.strong_rand_bytes(32) |> Base.encode16(case: :lower),
        consumed?: false,
        claim: :atomics.new(1, signed: false)
      }

      {:ok, permit, updated}
    else
      false -> {:error, :request_not_sendable}
      {:error, _} = error -> error
      _ -> {:error, :request_not_sendable}
    end
  end

  def acknowledge_possible_send(_, _, _), do: {:error, :ledger_closed}

  @spec consume_permit(send_permit(), String.t(), pos_integer()) :: {:ok, send_permit()} | {:error, term()}
  def consume_permit(%SendPermit{consumed?: false, claim: claim} = permit, request_id, revision)
      when permit.request_id == request_id and permit.revision == revision do
    case :atomics.exchange(claim, 1, 1) do
      0 -> {:ok, %{permit | consumed?: true}}
      _ -> {:error, :invalid_or_reused_permit}
    end
  end

  def consume_permit(_, _, _), do: {:error, :invalid_or_reused_permit}

  @spec record_observation(t(), String.t(), atom(), map()) :: {:ok, RequestRecord.t()} | {:error, term()}
  def record_observation(%__MODULE__{closed?: false} = ledger, request_id, state, fields)
      when is_atom(state) and is_map(fields) do
    with {:ok, ledger} <- refresh(ledger),
         false <- ledger.closed?,
         true <- state in [:invocation_observed, :accepted, :terminal, :ambiguous],
         {:ok, record} <- current(ledger, request_id),
         true <- state in Map.get(@transitions, record.state, []),
         :ok <- strict_observation(fields),
         updated <- update_record(record, fields, state),
         {:ok, _next} <-
           append(ledger, %{
             schema: @schema,
             attempt_id: ledger.attempt_id,
             kind: :record,
             record: updated
           }) do
      {:ok, updated}
    else
      false -> {:error, :invalid_transition}
      {:error, _} = error -> error
      _ -> {:error, :invalid_observation}
    end
  end

  def record_observation(_, _, _, _), do: {:error, :ledger_closed}

  @spec records(t()) :: [RequestRecord.t()]
  def records(%__MODULE__{events: events}), do: latest_records(events)

  @spec close_admission(t()) :: {:ok, t()} | {:error, term()}
  def close_admission(%__MODULE__{closed?: false} = ledger) do
    ledger =
      case refresh(ledger) do
        {:ok, refreshed} -> refreshed
        _ -> ledger
      end

    case append(ledger, %{schema: @schema, attempt_id: ledger.attempt_id, kind: :closed}) do
      {:ok, next} -> {:ok, %{next | closed?: true}}
      error -> error
    end
  end

  def close_admission(_), do: {:error, :ledger_closed}

  defp strict_attrs(attrs) do
    with :ok <- validate_allowed_fields(attrs),
         :ok <- validate_required_fields(attrs),
         :ok <- validate_body_length(attrs),
         :ok <- validate_endpoint(attrs),
         :ok <- validate_request_options(attrs) do
      validate_input_digests(attrs)
    end
  end

  defp strict_observation(fields) do
    allowed? = Enum.all?(Map.keys(fields), &(&1 in @observation_fields))
    if allowed?, do: :ok, else: {:error, :unknown_observation_field}
  end

  defp validate_allowed_fields(attrs), do: validate_keys(Map.keys(attrs), @allowed_attrs)

  defp validate_required_fields(attrs) do
    if Enum.all?(@required_attrs, &Map.has_key?(attrs, &1)), do: :ok, else: {:error, :missing_request_field}
  end

  defp validate_body_length(attrs) do
    if is_integer(attrs.body_bytes) and attrs.body_bytes >= 0, do: :ok, else: {:error, :invalid_body_length}
  end

  defp validate_endpoint(attrs) do
    if attrs.method == "POST" and attrs.url == "https://api.openai.com/v1/responses" and attrs.model == "synthetic-planner-v1",
      do: :ok,
      else: {:error, :invalid_endpoint}
  end

  defp validate_request_options(attrs) do
    if attrs.content_type == "application/json" and attrs.stream == true and attrs.store == false and attrs.parallel_tool_calls == false,
      do: :ok,
      else: {:error, :invalid_request_options}
  end

  defp validate_input_digests(attrs) do
    fields = [
      :source_digest,
      :config_digest,
      :policy_digest,
      :holder_digest,
      :context_digest,
      :catalog_digest,
      :tool_digest,
      :body_digest
    ]

    if Enum.all?(fields, &valid_digest?(Map.get(attrs, &1))), do: :ok, else: {:error, :invalid_digest}
  end

  defp validate_keys(keys, allowed) do
    if Enum.all?(keys, &(&1 in allowed)), do: :ok, else: {:error, :unknown_request_field}
  end

  defp valid_lineage(_events, attrs, 1) do
    if Map.get(attrs, :prior_request_id) in [nil, ""] and Map.get(attrs, :tool_operation_id) in [nil, ""], do: :ok, else: {:error, :invalid_first_request_lineage}
  end

  defp valid_lineage(events, attrs, 2) do
    first = Enum.find(latest_records(events), &(&1.ordinal == 1))

    if match?(%RequestRecord{state: :terminal}, first) and
         Map.get(attrs, :prior_request_id) == first.request_id and
         is_binary(Map.get(attrs, :tool_operation_id)) and
         Map.get(attrs, :prior_response_id) == first.response_id and
         is_binary(Map.get(attrs, :tool_call_id)) and
         valid_digest?(Map.get(attrs, :tool_output_digest)) and
         is_integer(Map.get(attrs, :tool_output_bytes)) and Map.get(attrs, :tool_output_bytes) >= 0 do
      :ok
    else
      {:error, :invalid_second_request_lineage}
    end
  end

  defp next_ordinal(events, 1) do
    if latest_records(events) == [], do: :ok, else: {:error, :ordinal_already_used}
  end

  defp next_ordinal(events, 2) do
    case latest_records(events) do
      [%RequestRecord{ordinal: 1, state: :terminal}] -> :ok
      _ -> {:error, :ordinal_out_of_order}
    end
  end

  defp next_ordinal(_, _), do: {:error, :invalid_ordinal}

  defp current(ledger, request_id) do
    case Enum.find(latest_records(ledger.events), &(&1.request_id == request_id)) do
      nil -> {:error, :unknown_request}
      record -> {:ok, record}
    end
  end

  defp refresh(%__MODULE__{} = ledger) do
    with {:ok, events} <- read_events(ledger.path),
         :ok <- validate_journal(ledger.attempt_id, events) do
      {:ok, %{ledger | events: events, closed?: Enum.any?(events, &(&1.kind == :closed))}}
    end
  end

  defp latest_records(events) do
    events
    |> Enum.flat_map(fn
      %{kind: :record, record: record} -> [record]
      _ -> []
    end)
    |> Enum.reduce(%{}, &Map.put(&2, &1.request_id, &1))
    |> Map.values()
    |> Enum.sort_by(& &1.ordinal)
  end

  defp append(ledger, event) do
    line = Jason.encode!(encode_event(event)) <> "\n"
    lock = {{__MODULE__, ledger.path}, self()}

    :global.trans(lock, fn ->
      with {:ok, disk_events} <- read_events(ledger.path),
           :ok <- validate_append(disk_events, event),
           {:ok, file} <- :file.open(String.to_charlist(ledger.path), [:append, :binary, :raw]),
           :ok <- :file.write(file, line),
           :ok <- :file.sync(file),
           :ok <- :file.close(file),
           :ok <- sync_parent(ledger.path) do
        {:ok, %{ledger | events: disk_events ++ [event]}}
      else
        _ ->
          _ = try_sync_close(ledger.path)
          {:error, :journal_sync_failed}
      end
    end)
  rescue
    _ -> {:error, :journal_sync_failed}
  end

  defp read_events(path) do
    case File.read(path) do
      {:ok, contents} ->
        decode_contents(path, contents)

      {:error, :enoent} ->
        with {:ok, file} <- :file.open(String.to_charlist(path), [:write, :exclusive, :binary, :raw]),
             :ok <- File.chmod(path, 0o600),
             :ok <- :file.sync(file),
             :ok <- :file.close(file),
             :ok <- sync_parent(path) do
          {:ok, []}
        end

      {:error, _} ->
        {:error, :journal_unavailable}
    end
  rescue
    _ -> {:error, :journal_corrupt}
  end

  defp decode_contents(_path, ""), do: {:ok, []}

  defp decode_contents(path, contents) do
    if String.ends_with?(contents, "\n") do
      with :ok <- File.chmod(path, 0o600), do: decode_lines(contents)
    else
      {:error, :journal_corrupt}
    end
  end

  defp decode_lines(contents) do
    events = contents |> String.split("\n", trim: true) |> Enum.map(&Jason.decode!/1) |> Enum.map(&decode_event/1)
    {:ok, events}
  end

  defp decode_event(%{"schema" => @schema, "attempt_id" => attempt, "kind" => "record", "record" => fields}) do
    atom_fields = Map.new(fields, fn {key, value} -> {String.to_existing_atom(key), value} end)
    unless Enum.all?(Map.keys(atom_fields), &(&1 in @record_fields)), do: raise(ArgumentError, "unknown record field")

    decoded = Map.new(atom_fields, fn {key, value} -> {key, decode_value(key, value)} end)
    direct = Map.take(decoded, @direct_fields)
    descriptor = Map.drop(decoded, @direct_fields)
    record = struct!(RequestRecord, Map.put(direct, :descriptor, descriptor))
    %{schema: @schema, attempt_id: attempt, kind: :record, record: record}
  end

  defp decode_event(%{"schema" => @schema, "attempt_id" => attempt, "kind" => "closed"}), do: %{schema: @schema, attempt_id: attempt, kind: :closed}
  defp decode_event(_), do: raise(ArgumentError, "invalid journal event")

  defp decode_value(key, value) when key in [:state], do: String.to_existing_atom(value)
  defp decode_value(_key, value), do: value

  defp validate_journal(attempt_id, events) do
    cond do
      Enum.any?(events, &(&1.attempt_id != attempt_id)) -> {:error, :attempt_mismatch}
      not valid_event_order?(events) -> {:error, :journal_corrupt}
      length(latest_records(events)) > 2 -> {:error, :journal_corrupt}
      Enum.map(latest_records(events), & &1.ordinal) != Enum.take([1, 2], length(latest_records(events))) -> {:error, :journal_corrupt}
      true -> :ok
    end
  end

  defp valid_event_order?(events) do
    valid_event_order(events, %{}, false)
  end

  defp valid_event_order([], _records, _closed?), do: true

  defp valid_event_order([%{kind: :closed} | remaining], records, false),
    do: valid_event_order(remaining, records, true)

  defp valid_event_order([%{kind: :record, record: record} | remaining], records, false) do
    case validate_record_event(records, record) do
      {:ok, next_records} -> valid_event_order(remaining, next_records, false)
      :error -> false
    end
  end

  defp valid_event_order(_events, _records, _closed?), do: false

  defp validate_record_event(records, record) do
    with :ok <- validate_record_shape(record),
         :ok <- validate_record_revision(records, record) do
      {:ok, Map.put(records, record.request_id, record)}
    else
      _ -> :error
    end
  end

  defp validate_record_shape(record) do
    valid? =
      valid_identifier_value?(record.request_id) and record.ordinal in [1, 2] and
        is_integer(record.revision) and record.revision > 0 and
        record.state in Map.keys(@transitions) and synthetic_record?(record)

    if valid?, do: :ok, else: :error
  end

  defp synthetic_record?(record) do
    record.evidence_scope == "SYNTHETIC_PIPE" and record.authenticated == false and
      record.operationally_qualified == false and is_boolean(record.send_may_have_occurred) and
      is_map(record.descriptor)
  end

  defp validate_record_revision(records, record) do
    case Map.fetch(records, record.request_id) do
      :error -> validate_first_revision(records, record)
      {:ok, existing} -> validate_next_revision(existing, record)
    end
  end

  defp validate_first_revision(records, record) do
    valid? =
      record.revision == 1 and record.state == :pre_send_intent and
        record.send_may_have_occurred == false and record.ordinal == map_size(records) + 1

    if valid?, do: :ok, else: :error
  end

  defp validate_next_revision(existing, record) do
    valid? =
      record.ordinal == existing.ordinal and record.revision == existing.revision + 1 and
        record.state in Map.get(@transitions, existing.state, []) and record.send_may_have_occurred

    if valid?, do: :ok, else: :error
  end

  defp valid_identifier_value?(value),
    do: is_binary(value) and Regex.match?(~r/\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\z/, value)

  defp ensure_parent(path) do
    parent = Path.dirname(path)
    File.mkdir_p!(parent)

    with :ok <- File.chmod(parent, 0o700) do
      ensure_journal_file(path)
    end
  end

  defp ensure_journal_file(path) do
    case File.lstat(path) do
      {:ok, %File.Stat{type: :regular}} -> File.chmod(path, 0o600)
      {:ok, _} -> {:error, :journal_not_regular}
      {:error, :enoent} -> :ok
      {:error, _} -> {:error, :journal_unavailable}
    end
  end

  defp sync_parent(path) do
    case :file.open(String.to_charlist(Path.dirname(path)), [:read, :raw, :directory]) do
      {:ok, dir} ->
        result = :file.sync(dir)
        _ = :file.close(dir)
        result

      {:error, reason} ->
        {:error, reason}
    end
  end

  defp try_sync_close(path) do
    case :file.open(String.to_charlist(path), [:append, :binary, :raw]) do
      {:ok, file} ->
        _ = :file.sync(file)
        :file.close(file)

      _ ->
        :ok
    end
  end

  # RuntimeAttempt generates unpadded base64url from exactly 16 bytes.
  defp validate_attempt_identifier(value) when byte_size(value) == 22 do
    with {:ok, <<_::128>> = decoded} <- Base.url_decode64(value, padding: false),
         ^value <- Base.url_encode64(decoded, padding: false) do
      :ok
    else
      _ -> {:error, :invalid_identifier}
    end
  end

  defp validate_attempt_identifier(_value), do: {:error, :invalid_identifier}

  defp validate_identifier(value) do
    if Regex.match?(~r/\A[A-Za-z0-9][A-Za-z0-9._:-]{0,127}\z/, value), do: :ok, else: {:error, :invalid_identifier}
  end

  defp valid_digest?(value), do: is_binary(value) and Regex.match?(~r/\A[0-9a-f]{64}\z/, value)

  defp random_id do
    <<a::32, b::16, c::16, d::16, e::48>> = :crypto.strong_rand_bytes(16)
    [hex(a, 8), hex(b, 4), hex(c, 4), hex(d, 4), hex(e, 12)] |> Enum.join("-")
  end

  defp hex(value, width), do: value |> Integer.to_string(16) |> String.downcase() |> String.pad_leading(width, "0")

  defp build_record(fields) do
    direct = Map.take(fields, @direct_fields)
    descriptor = Map.drop(fields, @direct_fields)
    struct!(RequestRecord, Map.put(direct, :descriptor, descriptor))
  end

  defp update_record(record, fields, state) do
    direct_updates = Map.take(fields, @direct_fields)
    descriptor_updates = Map.drop(fields, @direct_fields)
    direct = record |> Map.from_struct() |> Map.merge(direct_updates)
    descriptor = Map.merge(record.descriptor, descriptor_updates)

    direct
    |> Map.put(:descriptor, descriptor)
    |> Map.put(:state, state)
    |> Map.put(:revision, record.revision + 1)
    |> then(&struct!(RequestRecord, &1))
  end

  defp encode_event(%{record: %RequestRecord{} = record} = event) do
    fields = record |> Map.from_struct() |> Map.delete(:descriptor) |> Map.merge(record.descriptor)
    %{event | record: fields}
  end

  defp encode_event(event), do: event

  defp validate_append(events, %{kind: :record, record: %RequestRecord{} = record}) do
    existing = Enum.find(latest_records(events), &(&1.request_id == record.request_id))

    cond do
      is_nil(existing) and record.revision == 1 and record.state == :pre_send_intent and record.ordinal == length(latest_records(events)) + 1 -> :ok
      existing && record.revision == existing.revision + 1 && record.ordinal == existing.ordinal -> :ok
      true -> {:error, :stale_or_replayed_request}
    end
  end

  defp validate_append(_events, %{kind: :closed}), do: :ok
  defp validate_append(_, _), do: {:error, :invalid_journal_event}
end
