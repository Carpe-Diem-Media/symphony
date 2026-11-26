defmodule SymphonyElixir.HostEvidence.C01EvidenceReview do
  @moduledoc """
  Correlates one synthetic C01 fixture with an independent reference.

  The result accounts for observation slots. Digests supplied by observations
  are opaque claims, and correlation grants no operational authority.
  """

  alias SymphonyElixir.AgentRuntime.{Profile, Route}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.HostEvidence.P01Projection

  @artifact_names ~w(native_ready native_stop namespace_stop broker_stop request_close c04_readback replay_refusal)
  @ambiguity_reasons [:unreadable, :unconfirmed, :partial_coverage]
  @consumed_states [:consumed, :running, :stopverified, :quarantined]
  @grant_frame_fields ~w(project_id plane_project_id work_item_id responsibility source_commit source_tree config_identity runtime_lineage)a
  @max_u64 18_446_744_073_709_551_615

  @type key :: {:artifact, String.t()} | {:resource, String.t()}
  @type ambiguity :: :unreadable | :unconfirmed | :partial_coverage
  @type summary :: %{observed: [key()], missing: [key()], ambiguous: [{key(), ambiguity()}]}
  @type error ::
          :invalid_reference
          | :invalid_fixture
          | :unconsumed_pilot
          | :grant_mismatch
          | :identity_mismatch
          | :route_mismatch
          | :native_mismatch
          | :canonical_grant_mismatch
          | :native_grant_mismatch
          | :unknown_slot
          | :observation_binding_mismatch
          | :duplicate_slot
          | :conflicting_slot
          | :missing_slot

  @doc "Checks closed fixture shapes and returns the correlated inventory without interpreting its artifacts."
  @spec review(term(), term()) :: {:ok, :correlated, summary()} | {:error, error()}
  def review(reference, fixture) do
    with {:ok, reference} <- validate_reference(reference),
         {:ok, fixture} <- validate_fixture(fixture),
         :ok <- check(reference.pilot.state != :configured, :unconsumed_pilot),
         :ok <- check(reference.pilot.grant === reference.expected_grant, :grant_mismatch),
         :ok <- check(identity_matches?(reference, fixture.runtime_identity), :identity_mismatch),
         :ok <- check(route_matches?(reference, fixture.route_fingerprint), :route_mismatch),
         :ok <- check(native_matches?(reference, fixture.native), :native_mismatch),
         :ok <- check(fixture.canonical_grant_sha256 == canonical_commitment(reference.pilot.grant), :canonical_grant_mismatch),
         :ok <- check(fixture.native.grant_sha256 == native_grant_digest(reference.pilot.grant), :native_grant_mismatch) do
      correlate_inventory(reference, fixture.observations)
    end
  end

  defp validate_reference(
         {:c01_reference_v1,
          %{
            expected_grant: grant,
            pilot: pilot,
            current: current,
            route: route,
            native_binding_sha256: binding,
            resource_ids: [_ | _] = resource_ids
          } = reference}
       )
       when map_size(reference) == 6 do
    with :ok <-
           check(
             grant?(grant) and pilot?(pilot) and current?(current) and route?(route) and digest?(binding) and
               bounded_list?(resource_ids, 32, &identifier?/1) and length(Enum.uniq(resource_ids)) == length(resource_ids),
             :invalid_reference
           ) do
      {:ok, reference}
    end
  end

  defp validate_reference(_reference), do: {:error, :invalid_reference}

  defp validate_fixture(
         {:c01_evidence_fixture_v1,
          %{
            runtime_identity: identity,
            route_fingerprint: fingerprint,
            canonical_grant_sha256: commitment,
            native: native,
            observations: observations
          } = fixture}
       )
       when map_size(fixture) == 5 do
    with :ok <-
           check(
             identity?(identity) and route_hash?(fingerprint) and digest?(commitment) and native?(native) and
               bounded_list?(observations, 64, &observation?/1),
             :invalid_fixture
           ) do
      {:ok, fixture}
    end
  end

  defp validate_fixture(_fixture), do: {:error, :invalid_fixture}

  defp grant?(
         %{
           project_id: project_id,
           plane_project_id: plane_project_id,
           work_item_id: work_item_id,
           responsibility: "planning",
           source_commit: source_commit,
           source_tree: source_tree,
           config_identity: config,
           runtime_lineage: lineage,
           deadline_ms: deadline
         } = grant
       )
       when map_size(grant) == 9 do
    identifier?(project_id) and uuid?(plane_project_id) and uuid?(work_item_id) and
      oid?(source_commit) and oid?(source_tree) and digest?(config) and
      lineage?(lineage) and is_integer(deadline) and deadline in 1..@max_u64
  end

  defp grant?(_grant), do: false

  defp pilot?(%{state: :configured, grant: grant, runtime_identity: nil} = pilot) when map_size(pilot) == 3, do: grant?(grant)

  defp pilot?(%{state: state, grant: grant, runtime_identity: identity} = pilot)
       when map_size(pilot) == 3 and state in @consumed_states,
       do: grant?(grant) and identity?(identity)

  defp pilot?(_pilot), do: false

  defp current?(
         %{
           schema_version: 1,
           project_namespace: namespace,
           issue_id: issue_id,
           lineage_id: lineage,
           route_fingerprint: fingerprint,
           authority_fence: %{state: :bound, runtime_attempt: identity, route_fingerprint: fence_hash} = fence
         } = current
       )
       when map_size(current) == 6 and map_size(fence) == 3 do
    identifier?(namespace) and uuid?(issue_id) and lineage?(lineage) and route_hash?(fingerprint) and
      identity?(identity) and route_hash?(fence_hash)
  end

  defp current?(_current), do: false

  defp identity?(
         %Identity{
           runtime_attempt_id: attempt_id,
           work_item_id: work_item_id,
           lineage_generation: lineage,
           responsibility: "planning",
           runtime_profile: "planner"
         } = identity
       )
       when map_size(identity) == 6 do
    identifier?(attempt_id) and identifier?(work_item_id) and identifier?(lineage) and Identity.valid?(identity)
  end

  defp identity?(_identity), do: false

  defp route?(
         %Route{
           issue_id: issue_id,
           starting_state: "planning",
           profile_name: "planner",
           runtime_name: "codex",
           responsibility: "planning",
           profile: profile,
           fingerprint: fingerprint,
           starting_state_fingerprint: starting_hash
         } = route
       )
       when map_size(route) == 9 do
    uuid?(issue_id) and profile?(profile) and route_hash?(fingerprint) and route_hash?(starting_hash)
  end

  defp route?(_route), do: false

  defp profile?(
         %Profile{
           name: "planner",
           runtime: "codex",
           responsibility: "planning",
           sandbox: "read-only",
           model: "synthetic-planner-v1",
           command: command,
           prompt: prompt,
           concurrency_class: concurrency_class,
           max_turns: max_turns
         } = profile
       )
       when map_size(profile) == 10 do
    optional_string?(command) and optional_string?(prompt) and optional_string?(concurrency_class) and
      is_integer(max_turns) and max_turns > 0
  end

  defp profile?(_profile), do: false

  defp native?(
         %{
           binding_sha256: binding,
           attempt_id: attempt_id,
           project_id: project_id,
           work_item_id: work_item_id,
           role: "Planner",
           grant_sha256: grant_sha256,
           source_commit: source_commit,
           source_tree: source_tree,
           configuration_digest: config
         } = native
       )
       when map_size(native) == 9 do
    digest?(binding) and identifier?(attempt_id) and identifier?(project_id) and uuid?(work_item_id) and
      digest?(grant_sha256) and oid?(source_commit) and oid?(source_tree) and digest?(config)
  end

  defp native?(_native), do: false

  defp observation?({{tag, name}, attempt_id, binding, status}) when tag in [:artifact, :resource] do
    identifier?(name) and identifier?(attempt_id) and digest?(binding) and observation_status?(status)
  end

  defp observation?(_observation), do: false

  defp observation_status?({:observed, digest}), do: digest?(digest)
  defp observation_status?(:missing), do: true
  defp observation_status?({:ambiguous, reason, digest}), do: reason in @ambiguity_reasons and (is_nil(digest) or digest?(digest))
  defp observation_status?(_status), do: false

  # Walk only the permitted number of entries and verify the list terminator.
  defp bounded_list?([], _remaining, _test), do: true

  defp bounded_list?([entry | rest], remaining, test) when remaining > 0,
    do: test.(entry) and bounded_list?(rest, remaining - 1, test)

  defp bounded_list?(_other, _remaining, _test), do: false

  defp identifier?(value), do: match?({:ok, ^value}, P01Projection.identifier(value))
  defp optional_string?(nil), do: true
  defp optional_string?(value), do: is_binary(value) and String.valid?(value)
  defp uuid?(value), do: is_binary(value) and byte_size(value) == 36 and Regex.match?(~r/\A[0-9a-f]{8}(?:-[0-9a-f]{4}){3}-[0-9a-f]{12}\z/, value)
  defp lineage?(value), do: is_binary(value) and byte_size(value) in 1..256 and Regex.match?(~r/\A[A-Za-z0-9.:-]+\z/, value)
  defp oid?(value), do: is_binary(value) and byte_size(value) == 40 and Regex.match?(~r/\A[0-9a-f]+\z/, value)
  defp digest?(value), do: is_binary(value) and byte_size(value) == 64 and Regex.match?(~r/\A[0-9a-f]+\z/, value)
  defp route_hash?("sha256:" <> digest), do: digest?(digest)
  defp route_hash?(_value), do: false

  defp identity_matches?(%{pilot: pilot, current: current}, identity) do
    grant = pilot.grant

    identity === pilot.runtime_identity and identity === current.authority_fence.runtime_attempt and
      current.project_namespace == grant.project_id and current.issue_id == grant.work_item_id and
      identity.work_item_id == grant.work_item_id and current.lineage_id == grant.runtime_lineage and
      identity.lineage_generation == grant.runtime_lineage and identity.responsibility == grant.responsibility
  end

  defp route_matches?(%{route: route, current: current, pilot: pilot}, fixture_hash) do
    fingerprint = Route.fingerprint(route)

    route.issue_id == pilot.grant.work_item_id and route.starting_state_fingerprint == Route.starting_state_fingerprint(route) and
      Enum.all?([route.fingerprint, current.route_fingerprint, current.authority_fence.route_fingerprint, fixture_hash], &(&1 == fingerprint))
  end

  defp native_matches?(%{pilot: pilot, native_binding_sha256: binding}, native) do
    grant = pilot.grant

    Map.delete(native, :grant_sha256) === %{
      binding_sha256: binding,
      attempt_id: pilot.runtime_identity.runtime_attempt_id,
      project_id: grant.project_id,
      work_item_id: grant.work_item_id,
      role: "Planner",
      source_commit: grant.source_commit,
      source_tree: grant.source_tree,
      configuration_digest: grant.config_identity
    }
  end

  defp canonical_commitment(grant) do
    fields =
      Enum.map(@grant_frame_fields, fn field ->
        bytes = Map.fetch!(grant, field)
        <<byte_size(bytes)::unsigned-big-32, bytes::binary>>
      end)

    sha256(["H100-C01-FIXTURE-GRANT-V1", <<0>>, fields, <<grant.deadline_ms::unsigned-big-64>>])
  end

  # Mirrors the historical NativePilot context digest over the same stored grant.
  defp native_grant_digest(grant), do: sha256(:erlang.term_to_binary(grant, [:deterministic]))
  defp sha256(bytes), do: :crypto.hash(:sha256, bytes) |> Base.encode16(case: :lower)

  defp correlate_inventory(reference, observations) do
    expected =
      MapSet.new(Enum.map(@artifact_names, &{:artifact, &1}) ++ Enum.map(reference.resource_ids, &{:resource, &1}))

    binding = {reference.pilot.runtime_identity.runtime_attempt_id, reference.native_binding_sha256}

    recorded =
      Enum.reduce_while(observations, %{}, fn observation, seen ->
        record_observation(observation, expected, binding, seen)
      end)

    expected_count = MapSet.size(expected)

    case recorded do
      {:error, reason} -> {:error, reason}
      entries when map_size(entries) == expected_count -> {:ok, :correlated, summarize(entries)}
      _entries -> {:error, :missing_slot}
    end
  end

  defp record_observation({key, attempt_id, binding_sha256, status}, expected, binding, seen) do
    cond do
      not MapSet.member?(expected, key) -> {:halt, {:error, :unknown_slot}}
      {attempt_id, binding_sha256} != binding -> {:halt, {:error, :observation_binding_mismatch}}
      not Map.has_key?(seen, key) -> {:cont, Map.put(seen, key, status)}
      Map.fetch!(seen, key) === status -> {:halt, {:error, :duplicate_slot}}
      true -> {:halt, {:error, :conflicting_slot}}
    end
  end

  defp summarize(entries) do
    ordered = Enum.sort_by(entries, &elem(&1, 0))

    %{
      observed: for({key, {:observed, _digest}} <- ordered, do: key),
      missing: for({key, :missing} <- ordered, do: key),
      ambiguous: for({key, {:ambiguous, reason, _digest}} <- ordered, do: {key, reason})
    }
  end

  defp check(true, _reason), do: :ok
  defp check(false, reason), do: {:error, reason}
end
