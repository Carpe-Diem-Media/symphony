defmodule SymphonyElixir.HostEvidence.C01EvidenceReviewTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.AgentRuntime.{Profile, Route}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity
  alias SymphonyElixir.HostEvidence.C01EvidenceReview
  alias SymphonyElixir.Tracker.Issue

  @plane_project "00000000-0000-4000-8000-000000000011"
  @work_item "00000000-0000-4000-8000-000000000012"
  @commit String.duplicate("a", 40)
  @tree String.duplicate("b", 40)
  @config String.duplicate("c", 64)
  @binding String.duplicate("d", 64)
  @observation String.duplicate("e", 64)
  @other_digest String.duplicate("f", 64)
  @golden "043237f3824e394a8197faa91e8a12f565faa783508483c936075c02dbe12fa8"
  @max_u64 18_446_744_073_709_551_615
  @artifact_names ~w(broker_stop c04_readback namespace_stop native_ready native_stop replay_refusal request_close)
  @resource_ids ~w(metadata native_stop resource_ids)

  test "correlates the golden Planner vector regardless of grant insertion or inventory order" do
    {reference, fixture} = vector()
    {:c01_reference_v1, %{pilot: %{grant: grant}}} = reference
    assert fixture_commitment(grant) == @golden
    {:c01_evidence_fixture_v1, %{observations: observations}} = fixture
    expected = {:ok, :correlated, %{observed: keys(@resource_ids), missing: [], ambiguous: []}}

    assert expected == C01EvidenceReview.review(reference, fixture)
    reversed = grant |> Map.to_list() |> Enum.reverse() |> Enum.into(%{})
    assert expected == C01EvidenceReview.review(alter(reference, [:pilot, :grant], reversed), alter(fixture, [:observations], Enum.reverse(observations)))
  end

  test "classifies independent canonical and native digest failures and refuses swapped digests" do
    {reference, fixture} = vector()
    {:c01_evidence_fixture_v1, %{native: %{grant_sha256: native}}} = fixture

    assert {:error, :canonical_grant_mismatch} == C01EvidenceReview.review(reference, alter(fixture, [:canonical_grant_sha256], native))
    assert {:error, :native_grant_mismatch} == C01EvidenceReview.review(reference, alter(fixture, [:native, :grant_sha256], @golden))

    swapped = fixture |> alter([:canonical_grant_sha256], native) |> alter([:native, :grant_sha256], @golden)
    assert {:error, :canonical_grant_mismatch} == C01EvidenceReview.review(reference, swapped)
  end

  test "refuses both correct digests over a changed grant against the independent expectation" do
    {reference, fixture} = vector()
    {:c01_reference_v1, %{expected_grant: grant}} = reference
    changed = %{grant | deadline_ms: grant.deadline_ms + 1}

    changed_fixture =
      fixture
      |> alter([:canonical_grant_sha256], fixture_commitment(changed))
      |> alter([:native, :grant_sha256], native_digest(changed))

    assert {:error, :grant_mismatch} == C01EvidenceReview.review(alter(reference, [:pilot, :grant], changed), changed_fixture)
  end

  test "requires the same project, work item, lineage and exact runtime identity" do
    {reference, fixture} = vector()

    for {path, value} <- [
          {[:current, :project_namespace], "other-project"},
          {[:current, :issue_id], @plane_project},
          {[:current, :lineage_id], "other-lineage"},
          {[:pilot, :runtime_identity, :lineage_generation], "other-lineage"},
          {[:current, :authority_fence, :runtime_attempt, :runtime_attempt_id], "other-attempt"}
        ] do
      assert {:error, :identity_mismatch} == C01EvidenceReview.review(alter(reference, path, value), fixture)
    end

    for {field, value} <- [
          {:runtime_attempt_id, "other-attempt"},
          {:work_item_id, @plane_project},
          {:lineage_generation, "other-lineage"}
        ] do
      assert {:error, :identity_mismatch} == C01EvidenceReview.review(reference, alter(fixture, [:runtime_identity, field], value))
    end

    for {field, value} <- [responsibility: "Planning", responsibility: "planning ", runtime_profile: "builder"] do
      assert {:error, :invalid_fixture} == C01EvidenceReview.review(reference, alter(fixture, [:runtime_identity, field], value))
    end
  end

  test "recomputes both route hashes and rejects copied hashes over a changed profile" do
    {reference, fixture} = vector()
    other_hash = "sha256:" <> @other_digest

    paths = [
      [:route, :fingerprint],
      [:route, :starting_state_fingerprint],
      [:current, :route_fingerprint],
      [:current, :authority_fence, :route_fingerprint]
    ]

    for path <- paths do
      assert {:error, :route_mismatch} == C01EvidenceReview.review(alter(reference, path, other_hash), fixture)
    end

    changed_profile = alter(reference, [:route, :profile, :command], "other-codex app-server")
    assert {:error, :route_mismatch} == C01EvidenceReview.review(changed_profile, fixture)
    assert {:error, :route_mismatch} == C01EvidenceReview.review(reference, alter(fixture, [:route_fingerprint], other_hash))
  end

  test "matches individual native claims and the captured binding" do
    {reference, fixture} = vector()

    for {field, value} <- [
          binding_sha256: @other_digest,
          attempt_id: "other-attempt",
          project_id: "other-project",
          work_item_id: @plane_project,
          source_commit: @tree,
          source_tree: @commit,
          configuration_digest: @other_digest
        ] do
      assert {:error, :native_mismatch} == C01EvidenceReview.review(reference, alter(fixture, [:native, field], value))
    end

    assert {:error, :invalid_fixture} == C01EvidenceReview.review(reference, alter(fixture, [:native, :role], "planner"))
  end

  test "recognizes consumed states and refuses configured and incompatible ledger shapes" do
    {reference, fixture} = vector()

    for state <- [:consumed, :running, :stopverified, :quarantined] do
      assert {:ok, :correlated, _} = C01EvidenceReview.review(alter(reference, [:pilot, :state], state), fixture)
    end

    configured = reference |> alter([:pilot, :state], :configured) |> alter([:pilot, :runtime_identity], nil)
    assert {:error, :unconsumed_pilot} == C01EvidenceReview.review(configured, fixture)
    assert {:error, :invalid_reference} == C01EvidenceReview.review(alter(reference, [:pilot, :state], :configured), fixture)
    assert {:error, :invalid_reference} == C01EvidenceReview.review(alter(reference, [:pilot, :state], :unknown), fixture)
    assert {:error, :invalid_reference} == C01EvidenceReview.review(alter(reference, [:pilot, :runtime_identity], nil), fixture)
    assert {:error, :invalid_reference} == C01EvidenceReview.review(alter(reference, [:current, :schema_version], 2), fixture)

    for state <- [:armed, :released] do
      assert {:error, :invalid_reference} == C01EvidenceReview.review(alter(reference, [:current, :authority_fence, :state], state), fixture)
    end
  end

  test "retains separate observed, missing and ambiguous slots without returning C04 data" do
    {reference, fixture} = vector()
    {:c01_evidence_fixture_v1, %{observations: observations}} = fixture
    missing = {:artifact, "namespace_stop"}
    ambiguous = [{{:artifact, "request_close"}, :unconfirmed}, {{:resource, "resource_ids"}, :partial_coverage}]

    revised =
      Enum.map(observations, fn
        {^missing, id, binding, _} -> {missing, id, binding, :missing}
        {{:artifact, "request_close"} = key, id, binding, _} -> {key, id, binding, {:ambiguous, :unconfirmed, nil}}
        {{:resource, "resource_ids"} = key, id, binding, _} -> {key, id, binding, {:ambiguous, :partial_coverage, @observation}}
        entry -> entry
      end)

    expected = %{observed: keys(@resource_ids) -- [missing | Enum.map(ambiguous, &elem(&1, 0))], missing: [missing], ambiguous: ambiguous}
    assert {:ok, :correlated, ^expected} = C01EvidenceReview.review(reference, alter(fixture, [:observations], Enum.reverse(revised)))

    {:c01_reference_v1, %{pilot: pilot}} = reference
    raw_result = Map.put(pilot, :result, %{outcome: :completed, final_answer: "synthetic C04"})
    assert {:error, :invalid_reference} == C01EvidenceReview.review(alter(reference, [:pilot], raw_result), fixture)
  end

  test "distinguishes unknown, missing, duplicated and conflicting inventory keys" do
    {reference, fixture} = vector()
    {:c01_evidence_fixture_v1, %{observations: [first | rest] = observations}} = fixture

    for {added, reason} <- [
          {first, :duplicate_slot},
          {put_elem(first, 3, :missing), :conflicting_slot},
          {put_elem(first, 0, {:artifact, "unknown"}), :unknown_slot},
          {put_elem(first, 0, {:resource, "unknown"}), :unknown_slot},
          {put_elem(first, 0, {:unknown, "broker_stop"}), :invalid_fixture}
        ] do
      assert {:error, ^reason} = C01EvidenceReview.review(reference, alter(fixture, [:observations], [added | observations]))
    end

    assert {:error, :missing_slot} == C01EvidenceReview.review(reference, alter(fixture, [:observations], rest))

    for status <- [:missing, {:ambiguous, :unreadable, nil}, {:observed, @observation}] do
      entry = first |> put_elem(2, @other_digest) |> put_elem(3, status)
      assert {:error, :observation_binding_mismatch} == C01EvidenceReview.review(reference, alter(fixture, [:observations], [entry | rest]))
    end

    assert {:error, :observation_binding_mismatch} ==
             C01EvidenceReview.review(reference, alter(fixture, [:observations], [put_elem(first, 1, "other-attempt") | rest]))
  end

  test "rejects malformed nested shapes, extra struct keys, and improper or oversized lists" do
    {reference, fixture} = vector()
    {:c01_reference_v1, %{route: %Route{profile: profile} = route, expected_grant: grant}} = reference
    {:c01_evidence_fixture_v1, %{runtime_identity: identity, native: native, observations: [entry | _]}} = fixture

    for malformed <- [
          :bad,
          {:reference_v2, elem(reference, 1)},
          alter(reference, [:current, :authority_fence], {:bound, identity}),
          alter(reference, [:expected_grant], Map.put(grant, :grant_id, "P01-only")),
          alter(reference, [:route], Map.put(route, :extra, true)),
          alter(reference, [:route, :profile], Map.put(profile, :extra, true)),
          alter(reference, [:route, :profile], Map.from_struct(profile)),
          alter(reference, [:route, :profile, :command], fn -> :unexpected end),
          alter(reference, [:route, :profile, :prompt], <<255>>),
          alter(reference, [:route, :profile, :max_turns], 0)
        ] do
      assert {:error, :invalid_reference} == C01EvidenceReview.review(malformed, fixture)
    end

    for malformed <- [
          :bad,
          {:fixture_v2, elem(fixture, 1)},
          alter(fixture, [:native], Map.put(native, "attempt_id", identity.runtime_attempt_id)),
          alter(fixture, [:runtime_identity], Map.put(identity, :extra, true)),
          alter(fixture, [:runtime_identity], Map.from_struct(identity)),
          alter(fixture, [:observations], [entry | :tail]),
          alter(fixture, [:observations], List.duplicate(entry, 65)),
          alter(fixture, [:observations], [put_elem(entry, 3, {:ambiguous, :invented, nil})]),
          alter(fixture, [:observations], [put_elem(entry, 3, {:observed, <<255>>})]),
          alter(fixture, [:canonical_grant_sha256], String.duplicate("A", 64)),
          alter(fixture, [:native, :grant_sha256], String.duplicate("g", 64)),
          alter(fixture, [:native, :binding_sha256], :not_binary)
        ] do
      assert {:error, :invalid_fixture} == C01EvidenceReview.review(reference, malformed)
    end
  end

  test "accepts the bounded numeric and resource edges and rejects values beyond them" do
    for deadline <- [1, @max_u64] do
      {reference, fixture} = vector(deadline)
      assert {:ok, :correlated, _} = C01EvidenceReview.review(reference, fixture)
    end

    {reference, fixture} = vector()

    for deadline <- [0, -1, @max_u64 + 1, 25_000.0] do
      assert {:error, :invalid_reference} == C01EvidenceReview.review(alter(reference, [:expected_grant, :deadline_ms], deadline), fixture)
    end

    for bad_ids <- [[], ["r", "r"], ["r" | :tail], Enum.map(1..33, &"r#{&1}"), [String.duplicate("a", 257)]] do
      assert {:error, :invalid_reference} == C01EvidenceReview.review(alter(reference, [:resource_ids], bad_ids), fixture)
    end

    ids = Enum.map(1..31, &"r#{&1}") ++ [String.duplicate("a", 256)]
    {reference, fixture} = vector(25_000, ids)
    assert {:ok, :correlated, %{observed: observed}} = C01EvidenceReview.review(reference, fixture)
    assert observed == keys(ids)
  end

  test "checks input shape first and stops on the first semantic inventory error" do
    {reference, fixture} = vector()
    {:c01_evidence_fixture_v1, %{observations: [first | _] = observations}} = fixture
    configured = reference |> alter([:pilot, :runtime_identity], nil) |> alter([:pilot, :state], :configured)

    assert {:error, :invalid_reference} == C01EvidenceReview.review(:bad, :bad)
    assert {:error, :invalid_fixture} == C01EvidenceReview.review(configured, :bad)
    assert {:error, :invalid_fixture} == C01EvidenceReview.review(reference, alter(fixture, [:observations], [first, first, :malformed]))
    unknown = put_elem(first, 0, {:resource, "unknown"})
    assert {:error, :duplicate_slot} == C01EvidenceReview.review(reference, alter(fixture, [:observations], [first, first, unknown | observations]))
    assert {:error, :unknown_slot} == C01EvidenceReview.review(reference, alter(fixture, [:observations], [unknown, first, first | observations]))
  end

  defp vector(deadline \\ 25_000, resource_ids \\ @resource_ids) do
    grant = %{
      project_id: "pilot-functional",
      plane_project_id: @plane_project,
      work_item_id: @work_item,
      responsibility: "planning",
      source_commit: @commit,
      source_tree: @tree,
      config_identity: @config,
      runtime_lineage: "offline-functional-ordinal-test",
      deadline_ms: deadline
    }

    profile = Profile.default_profiles("codex app-server", 1)["planner"]
    route = Route.new(%Issue{id: @work_item, state: "Planning"}, %{profile | model: "synthetic-planner-v1"})

    identity = %Identity{
      runtime_attempt_id: "_synthetic-attempt",
      work_item_id: @work_item,
      lineage_generation: grant.runtime_lineage,
      responsibility: "planning",
      runtime_profile: "planner"
    }

    reference =
      {:c01_reference_v1,
       %{
         expected_grant: grant,
         pilot: %{state: :consumed, grant: grant, runtime_identity: identity},
         current: %{
           schema_version: 1,
           project_namespace: grant.project_id,
           issue_id: @work_item,
           lineage_id: grant.runtime_lineage,
           route_fingerprint: route.fingerprint,
           authority_fence: %{state: :bound, runtime_attempt: identity, route_fingerprint: route.fingerprint}
         },
         route: route,
         native_binding_sha256: @binding,
         resource_ids: resource_ids
       }}

    fixture =
      {:c01_evidence_fixture_v1,
       %{
         runtime_identity: identity,
         route_fingerprint: route.fingerprint,
         canonical_grant_sha256: if(deadline == 25_000, do: @golden, else: fixture_commitment(grant)),
         native: %{
           binding_sha256: @binding,
           attempt_id: identity.runtime_attempt_id,
           project_id: grant.project_id,
           work_item_id: @work_item,
           role: "Planner",
           grant_sha256: native_digest(grant),
           source_commit: @commit,
           source_tree: @tree,
           configuration_digest: @config
         },
         observations: Enum.map(keys(resource_ids), &{&1, identity.runtime_attempt_id, @binding, {:observed, @observation}})
       }}

    {reference, fixture}
  end

  defp keys(resource_ids) do
    Enum.map(@artifact_names, &{:artifact, &1}) ++ Enum.map(Enum.sort(resource_ids), &{:resource, &1})
  end

  defp alter({tag, map}, path, value), do: {tag, put_in(map, Enum.map(path, &Access.key/1), value)}

  defp native_digest(grant) do
    :sha256 |> :crypto.hash(:erlang.term_to_binary(grant, [:deterministic])) |> Base.encode16(case: :lower)
  end

  defp fixture_commitment(grant) do
    fields = Map.take(grant, ~w(project_id plane_project_id work_item_id responsibility source_commit source_tree config_identity runtime_lineage)a)

    frame =
      Enum.reduce(
        ~w(project_id plane_project_id work_item_id responsibility source_commit source_tree config_identity runtime_lineage)a,
        "H100-C01-FIXTURE-GRANT-V1\0",
        fn key, acc ->
          bytes = Map.fetch!(fields, key)
          acc <> <<byte_size(bytes)::32, bytes::binary>>
        end
      )

    :sha256 |> :crypto.hash(frame <> <<grant.deadline_ms::64>>) |> Base.encode16(case: :lower)
  end
end
