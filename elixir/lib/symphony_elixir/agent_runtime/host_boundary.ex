if Code.ensure_loaded?(Mix) and Mix.env() == :test do
  defmodule SymphonyElixir.AgentRuntime.HostBoundary do
    @moduledoc "Test-only owner for the selected provider effect frames and durable permissions."

    alias SymphonyElixir.AgentRuntime.{NativePilot, RuntimeIsolation}
    alias SymphonyElixir.ProviderEffect.RequestLedger

    @schema "H100-EFFECT-PIPE-1"
    @common ~w(schema kind context_digest thread_id turn_id nonce ordinal sequence deadline_ms)
    @descriptor ~w(request_id method url model body_sha256 body_length content_type stream store
      parallel_tool_calls tool_schema_sha256 prior_response_id tool_call_id tool_output_sha256 tool_output_length)
    @response_fields ~w(request_id response_id)

    @spec open(map(), String.t(), String.t()) :: {:ok, map()} | {:error, term()}
    def open(holder, thread, turn) do
      with {:ok, receipt} <- NativePilot.verify_functional_receipt(holder, :ready, nil),
           {:ok, bytes} when byte_size(bytes) <= 131_072 <- File.read(Path.join(holder.directory, "manifest.json")),
           {:ok, %{"binding" => binding, "context" => context, "provider" => provider, "deadline_ms" => deadline}} <-
             Jason.decode(bytes),
           true <- binding == holder.digest and context["context_digest"] == receipt["context_digest"],
           %{"binding" => broker} <- context["broker_selftest"],
           true <- digest?(provider["nonce"]) and digest?(provider["fixture_sha256"]),
           true <- is_integer(deadline) and deadline > 0,
           true <- broker["deadline_ms"] == deadline do
        {:ok,
         %{
           holder: holder,
           context: context,
           broker: broker,
           nonce: provider["nonce"],
           native_deadline: deadline,
           thread: thread,
           turn: turn,
           sequence: 0,
           permit: nil,
           descriptor_digest: nil
         }}
      else
        _ -> {:error, :provider_boundary_unavailable}
      end
    end

    @spec effect(map(), map()) :: {:ok, map(), map()} | {:error, term()}
    def effect(boundary, frame) when is_map(frame) do
      with true <- common_matches?(boundary, frame),
           :ok <- RuntimeIsolation.check_pilot_holder(boundary.holder, :turn),
           {:ok, ledger} <- open_ledger(boundary),
           {:ok, reply, next} <- transition(boundary, ledger, frame) do
        base = Map.take(frame, @common)
        {:ok, Map.merge(base, reply), %{next | sequence: frame["sequence"]}}
      else
        {:error, _} = error -> error
        _ -> {:error, :provider_effect_frame_refused}
      end
    end

    def effect(_boundary, _frame), do: {:error, :provider_effect_frame_refused}

    @spec completed?(map()) :: :ok | {:error, atom()}
    def completed?(boundary) do
      with {:ok, ledger} <- open_ledger(boundary),
           [%{ordinal: 1, state: :terminal}, %{ordinal: 2, state: :terminal}] <- RequestLedger.records(ledger) do
        :ok
      else
        _ -> {:error, :provider_effect_completion_unconfirmed}
      end
    end

    @spec close(map()) :: :ok
    def close(boundary) do
      with {:ok, ledger} <- open_ledger(boundary),
           :ok <- retain_ambiguous_effect(ledger),
           {:ok, updated} <- open_ledger(boundary) do
        RequestLedger.close_admission(updated)
      end

      :ok
    end

    defp retain_ambiguous_effect(ledger) do
      uncertain = Enum.find(RequestLedger.records(ledger), &(&1.send_may_have_occurred and &1.state not in [:terminal, :ambiguous]))

      case uncertain do
        nil ->
          :ok

        record ->
          with {:ok, _} <- RequestLedger.record_observation(ledger, record.request_id, :ambiguous, %{}), do: :ok
      end
    end

    defp common_matches?(boundary, frame) do
      frame["schema"] == @schema and frame["context_digest"] == boundary.context["context_digest"] and
        frame["thread_id"] == boundary.thread and frame["turn_id"] == boundary.turn and
        frame["nonce"] == boundary.nonce and frame["ordinal"] in [1, 2] and
        frame["sequence"] == boundary.sequence + 1 and frame["deadline_ms"] == boundary.native_deadline and
        System.monotonic_time(:millisecond) < boundary.holder.binding.absolute_deadline_ms
    end

    defp transition(boundary, ledger, %{"kind" => "VALIDATE_DESCRIPTOR"} = frame) do
      with true <- keys_match?(frame, ["descriptor_sha256" | @descriptor]),
           digest <- descriptor_digest(frame),
           true <- digest == frame["descriptor_sha256"],
           true <- descriptor_valid?(frame),
           {:ok, prior} <- prior_effect(boundary, ledger, frame),
           {:ok, record} <- RequestLedger.prepare(ledger, descriptor_attributes(boundary, frame, prior)) do
        reply = %{
          "kind" => "PRE_SEND_INTENT",
          "request_id" => record.request_id,
          "revision" => record.revision,
          "descriptor_sha256" => digest
        }

        {:ok, reply, %{boundary | permit: nil, descriptor_digest: digest}}
      else
        _ -> {:error, :provider_descriptor_refused}
      end
    end

    defp transition(boundary, ledger, %{"kind" => "POSSIBLE_SEND_ACK"} = frame) do
      with true <- keys_match?(frame, ~w(request_id revision descriptor_sha256)),
           {:ok, record} <- record_for(ledger, frame),
           true <- frame["revision"] == record.revision,
           true <- frame["descriptor_sha256"] == boundary.descriptor_digest,
           {:ok, permit, updated} <-
             RequestLedger.acknowledge_possible_send(ledger, record.request_id, record.revision),
           {:ok, permit} <- RequestLedger.consume_permit(permit, updated.request_id, updated.revision) do
        reply = %{
          "kind" => "INVOCATION_PERMITTED",
          "request_id" => updated.request_id,
          "revision" => updated.revision,
          "ack_nonce" => permit.ack_nonce
        }

        {:ok, reply, %{boundary | permit: permit}}
      else
        _ -> {:error, :provider_possible_send_refused}
      end
    end

    defp transition(boundary, ledger, %{"kind" => "OBSERVED_ACCEPTANCE"} = frame) do
      with true <- keys_match?(frame, @response_fields),
           {:ok, record} <- record_for(ledger, frame),
           %{request_id: id, consumed?: true} <- boundary.permit,
           true <- record.state == :possible_send and id == record.request_id,
           true <- identifier?(frame["response_id"]),
           {:ok, _invoked} <- RequestLedger.record_observation(ledger, record.request_id, :invocation_observed, %{}),
           {:ok, updated} <- open_ledger(boundary),
           {:ok, _accepted} <-
             RequestLedger.record_observation(updated, record.request_id, :accepted, %{
               response_id: frame["response_id"],
               upstream_status: 200
             }) do
        {:ok, observation_reply(frame, "accepted"), boundary}
      else
        _ -> {:error, :provider_acceptance_refused}
      end
    end

    defp transition(boundary, ledger, %{"kind" => "TERMINAL_CONFIRMATION"} = frame) do
      with true <- keys_match?(frame, @response_fields ++ ~w(terminal_sha256 terminal_length)),
           {:ok, record} <- record_for(ledger, frame),
           true <- record.state == :accepted and frame["response_id"] == record.response_id,
           true <- digest?(frame["terminal_sha256"]) and frame["terminal_length"] in 1..262_144,
           {:ok, _completed} <-
             RequestLedger.record_observation(ledger, record.request_id, :terminal, %{
               terminal_kind: "response.completed",
               terminal_digest: frame["terminal_sha256"]
             }) do
        {:ok, observation_reply(frame, "terminal"), %{boundary | permit: nil}}
      else
        _ -> {:error, :provider_terminal_refused}
      end
    end

    defp transition(_boundary, _ledger, _frame), do: {:error, :provider_effect_frame_refused}

    defp observation_reply(frame, stage) do
      frame |> Map.take(@response_fields) |> Map.merge(%{"kind" => "DURABLE_OBSERVATION", "stage" => stage})
    end

    defp record_for(ledger, frame) do
      case Enum.find(RequestLedger.records(ledger), &(&1.ordinal == frame["ordinal"] and &1.request_id == frame["request_id"])) do
        nil -> {:error, :provider_request_unknown}
        record -> {:ok, record}
      end
    end

    defp keys_match?(frame, keys), do: Enum.sort(Map.keys(frame)) == Enum.sort(@common ++ keys)

    defp descriptor_valid?(%{
           "method" => "POST",
           "url" => "https://api.openai.com/v1/responses",
           "model" => "synthetic-planner-v1",
           "content_type" => "application/json",
           "stream" => true,
           "store" => false,
           "parallel_tool_calls" => false,
           "request_id" => nil,
           "body_length" => length,
           "body_sha256" => body,
           "tool_schema_sha256" => tools
         })
         when length in 1..1_048_576 do
      digest?(body) and digest?(tools)
    end

    defp descriptor_valid?(_frame), do: false

    defp prior_effect(_boundary, _ledger, %{"ordinal" => 1} = frame) do
      if Enum.all?(~w(prior_response_id tool_call_id tool_output_sha256 tool_output_length), &is_nil(frame[&1])),
        do: {:ok, nil},
        else: {:error, :unexpected_prior_effect}
    end

    defp prior_effect(boundary, ledger, %{"ordinal" => 2} = frame) do
      with [%{ordinal: 1, state: :terminal, response_id: response_id} = record] <- RequestLedger.records(ledger),
           true <- frame["prior_response_id"] == response_id,
           true <- frame["tool_call_id"] == boundary.broker["tool_call_id"],
           true <- digest?(frame["tool_output_sha256"]) and frame["tool_output_length"] in 1..8192 do
        {:ok, record}
      else
        _ -> {:error, :prior_effect_unconfirmed}
      end
    end

    defp descriptor_attributes(boundary, frame, prior) do
      context = boundary.context
      binding = boundary.holder.binding

      %{
        ordinal: frame["ordinal"],
        runtime_attempt_id: binding.attempt.runtime_attempt_id,
        grant_id: context["grant_id"],
        project_id: binding.grant.project_id,
        item_id: binding.grant.work_item_id,
        planning_role: "planning",
        config_digest: binding.grant.config_identity,
        policy_digest: context["policy_digest"],
        source_digest: sha256(binding.grant.source_commit <> binding.grant.source_tree),
        holder_digest: context["holder_sha256"],
        profile_id: context["holder_profile_digest"],
        host_id: context["host_identity"],
        boot_id: context["boot_identity"],
        credential_generation: context["credential_generation"],
        context_digest: context["context_digest"],
        nonce: boundary.nonce,
        thread_id: boundary.thread,
        turn_id: boundary.turn,
        prior_request_id: if(prior, do: prior.request_id),
        tool_operation_id: if(prior, do: boundary.broker["operation_id"]),
        tool_call_id: frame["tool_call_id"],
        tool_output_digest: frame["tool_output_sha256"],
        tool_output_bytes: frame["tool_output_length"],
        prior_response_id: frame["prior_response_id"],
        permission_id: context["permission_reference"],
        permission_generation: 1,
        lease_id: context["permission_reference"],
        lease_generation: 1,
        catalog_digest: context["model_catalog_digest"],
        tool_digest: frame["tool_schema_sha256"],
        method: frame["method"],
        url: frame["url"],
        model: frame["model"],
        content_type: frame["content_type"],
        stream: true,
        store: false,
        parallel_tool_calls: false,
        body_digest: frame["body_sha256"],
        body_bytes: frame["body_length"],
        deadline_monotonic_ms: binding.absolute_deadline_ms
      }
    end

    defp descriptor_digest(frame) do
      frame
      |> Map.take(@descriptor)
      |> Enum.sort()
      |> Enum.map_join(",", fn {key, value} ->
        Jason.encode!(key) <> ":" <> Jason.encode!(value)
      end)
      |> then(&sha256("{" <> &1 <> "}"))
    end

    defp open_ledger(boundary) do
      RequestLedger.open(boundary.holder.binding.attempt.runtime_attempt_id,
        path: Path.join(boundary.holder.directory, "provider-effects.journal")
      )
    end

    defp digest?(value), do: is_binary(value) and Regex.match?(~r/\A[0-9a-f]{64}\z/, value)
    defp identifier?(value), do: is_binary(value) and Regex.match?(~r/\A[A-Za-z0-9][A-Za-z0-9._-]{0,127}\z/, value)
    defp sha256(data), do: :crypto.hash(:sha256, data) |> Base.encode16(case: :lower)
  end
end
