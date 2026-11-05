defmodule SymphonyElixir.HostEvidence.P01Projection do
  @moduledoc """
  Pure P01 compatibility projections for P08-SPEC-0.7.

  Results are untrusted string-keyed wire values, never grants, provenance
  receipts or cleanup verdicts. Nothing here reads a ledger, resolves evidence,
  computes an authoritative evidence hash or changes lifecycle state. Expected
  bindings and current-link context are caller-supplied comparison inputs.

  Historical evidence stays opaque and exact. A structurally matching current
  link is only a placeholder in a predicted post-snapshot. T10 must independently
  resolve the actual object and its self-bindings before authoritative hashing;
  the captured boundary retains every authorization check.
  """

  alias SymphonyElixir.AgentRuntime.{AttemptResource, CleanupEvidenceRef, QuarantineDisposition, RecoveryGeneration}
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  @type error ::
          :unencodable_p01_value
          | :invalid_request
          | :namespace_mismatch
          | :identity_mismatch
          | :stale_grant
          | :recovery_generation_mismatch
  @type result(value) :: {:ok, value} | {:error, error()}
  @type evidence_link :: nil | %{required(String.t()) => String.t() | nil}
  @type current_context :: %{
          phase: :predicted_post_snapshot,
          object_id: String.t(),
          resource_id: String.t(),
          self_bindings: [%{required(String.t()) => String.t()}]
        }

  @u64 18_446_744_073_709_551_615
  @identity_fields ~w(runtime_attempt_id work_item_id lineage_generation responsibility runtime_profile)a
  @ref_fields ~w(grant_id project_namespace runtime_identity fence_epoch grant_sha256)a
  @slots ["last_evidence_ref", "quarantine_evidence_ref"]

  @doc "Checks the wire ID subset without changing any bytes."
  @spec identifier(term()) :: result(String.t())
  def identifier(value) when is_binary(value) and byte_size(value) in 1..256 do
    bytes = :binary.bin_to_list(value)

    if Enum.all?(bytes, &(&1 in 32..126)) and Enum.any?(bytes, &(&1 != 32)),
      do: {:ok, value},
      else: unencodable()
  end

  def identifier(_value), do: unencodable()

  @doc "Projects an exact strict P01 binding identity, without legacy normalization."
  @spec identity(term()) :: result(map())
  def identity(%Identity{} = value) do
    # Identity.valid?/1 accepts broader legacy values. Strict P01 binding
    # constructors require exactly these five binary fields, each 1..256 bytes.
    with true <- exact_struct?(value, Identity),
         :ok <- identifiers(value, @identity_fields) do
      {:ok, stringify(Map.from_struct(value))}
    else
      _ -> unencodable()
    end
  end

  def identity(_value), do: unencodable()

  @doc "Projects historical generation bytes unchanged and rejects U64 overflow."
  @spec generation(term()) :: result(map())
  def generation(value) do
    with :ok <- stored_struct(value, RecoveryGeneration),
         :ok <- identifiers(value, [:project_namespace, :host_id, :boot_id, :nonce]),
         :ok <- unsigned(value.sequence, 1) do
      {:ok, stringify(Map.from_struct(value))}
    end
  end

  @doc "Projects exactly five reference fields after exact comparison with an expected reference. Neither input proves issuance."
  @spec grant_ref(term(), term()) :: result(map())
  def grant_ref(value, expected) do
    with {:ok, wire} <- reference_wire(value),
         {:ok, _} <- reference_wire(expected),
         :ok <- binding_matches(value, expected),
         true <- value.fence_epoch == expected.fence_epoch and value.grant_sha256 == expected.grant_sha256 do
      {:ok, wire}
    else
      false -> {:error, :stale_grant}
      {:error, _} = error -> error
    end
  end

  @doc "Projects a shape-valid cleanup reference against supplied binding/generation facts. It does not resolve or verify evidence."
  @spec cleanup_ref(term(), term(), term()) :: result(map())
  def cleanup_ref(value, expected_ref, current_generation) do
    with :ok <- stored_struct(value, CleanupEvidenceRef),
         :ok <- identifiers(value, [:evidence_id, :project_namespace, :grant_id]),
         {:ok, identity_wire} <- identity(value.runtime_identity),
         {:ok, generation_wire} <- generation(value.verification_generation),
         :ok <- unsigned(value.fence_epoch, 1),
         {:ok, _} <- reference_wire(expected_ref),
         {:ok, _} <- generation(current_generation),
         :ok <- binding_matches(value, expected_ref),
         :ok <- equal(value.fence_epoch, expected_ref.fence_epoch, :stale_grant),
         :ok <- generation_scope(current_generation, expected_ref.project_namespace),
         :ok <- equal(value.verification_generation, current_generation, :recovery_generation_mismatch) do
      {:ok,
       value
       |> Map.from_struct()
       |> stringify()
       |> Map.put("runtime_identity", identity_wire)
       |> Map.put("verification_generation", generation_wire)}
    end
  end

  @doc "Projects standalone quarantine with prior/null evidence only. The closed wire schema keeps resolution_ref as a nullable P01ID."
  @spec quarantine(term()) :: result(map())
  def quarantine(value) do
    with :ok <- stored_struct(value, QuarantineDisposition),
         {:ok, link} <- evidence_link(value.evidence_ref),
         :ok <- optional_identifier(value.resolution_ref),
         {:ok, generation_wire} <- generation(value.generation) do
      {:ok,
       %{
         "state" => Atom.to_string(value.state),
         "reason" => if(value.reason, do: Atom.to_string(value.reason), else: nil),
         "evidence_ref" => link,
         "generation" => generation_wire,
         "resolution_ref" => value.resolution_ref
       }}
    end
  end

  @doc """
  Projects the closed StoredResourceProjection against a supplied reference and
  current generation. Locator SHA-256 commits exact locator bytes only; it is
  neither ownership proof nor an evidence hash. The original locator remains
  solely in the unchanged P01 record. Evidence defaults to prior/null. Only
  historical rows admitted by the pinned P01 ledger can be projected; constructor
  enum membership does not admit future P08 lifecycle states.
  """
  @spec resource(term(), term(), term()) :: result(map())
  def resource(value, expected_ref, current_generation) do
    with :ok <- stored_struct(value, AttemptResource),
         :ok <- identifiers(value, [:resource_id, :project_namespace, :grant_id, :stable_locator, :owner_host_id]),
         :ok <- unsigned(value.revision, 0),
         {:ok, identity_wire} <- identity(value.runtime_identity),
         {:ok, creation} <- generation(value.creation_generation),
         {:ok, reconciliation} <- generation(value.reconciliation_generation),
         {:ok, q} <- quarantine(value.quarantine),
         {:ok, link} <- evidence_link(value.last_evidence_ref),
         {:ok, _} <- reference_wire(expected_ref),
         {:ok, _} <- generation(current_generation),
         :ok <- binding_matches(value, expected_ref),
         :ok <- resource_generation_matches(value, current_generation),
         :ok <- historical_resource(value) do
      {:ok,
       value
       |> Map.from_struct()
       |> Map.delete(:stable_locator)
       |> stringify()
       |> Map.merge(%{
         "runtime_identity" => identity_wire,
         "class" => Atom.to_string(value.class),
         "state" => Atom.to_string(value.state),
         "creation_generation" => creation,
         "reconciliation_generation" => reconciliation,
         "quarantine" => q,
         "last_evidence_ref" => link,
         "stable_locator_sha256" => :crypto.hash(:sha256, value.stable_locator) |> Base.encode16(case: :lower)
       })}
    end
  end

  @doc "Projects historical strings as exact opaque prior IDs; nil becomes null. Stored maps are rejected."
  @spec evidence_link(term()) :: result(evidence_link())
  def evidence_link(nil), do: {:ok, nil}

  def evidence_link(value) do
    with {:ok, id} <- identifier(value), do: {:ok, %{"kind" => "prior", "id" => id}}
  end

  @doc "Restores prior/null to the exact stored string/nil. Current and nonclosed links reject."
  @spec restore_evidence_link(term()) :: result(String.t() | nil)
  def restore_evidence_link(nil), do: {:ok, nil}

  def restore_evidence_link(%{"kind" => "prior", "id" => id} = link) when map_size(link) == 2 and is_binary(id) do
    identifier(id)
  end

  def restore_evidence_link(_link), do: {:error, :invalid_request}

  @doc """
  Checks untrusted structural context for a predicted post-snapshot placeholder.

  Only a declared resource/slot and an exact stored-string/object-ID match can
  produce the closed current link. Consistent fabricated context is still only
  structural input. Success establishes no provenance, authority or evidence
  digest and must not be consumed as such before T10 verification. Invalid
  identifier values return `:unencodable_p01_value`; malformed or nonmatching
  structural context returns `:invalid_request`.
  """
  @spec current_link(term(), term(), term(), term()) :: result(evidence_link())
  def current_link(stored, resource_id, slot, context) do
    with %{phase: :predicted_post_snapshot, object_id: object_id, resource_id: ^resource_id, self_bindings: bindings} <-
           context,
         true <- map_size(context) == 4,
         true <- slot in @slots,
         {:ok, ^stored} <- identifier(stored),
         {:ok, ^object_id} <- identifier(object_id),
         {:ok, ^resource_id} <- identifier(resource_id),
         true <- stored === object_id,
         :ok <- validate_self_bindings(bindings),
         true <- %{"resource_id" => resource_id, "slot" => slot} in bindings do
      {:ok, %{"kind" => "current", "id" => nil}}
    else
      {:error, :unencodable_p01_value} = error -> error
      _ -> {:error, :invalid_request}
    end
  end

  @doc "Restores a closed current placeholder only against the same explicit structural context and exact stored bytes."
  @spec restore_current_link(term(), term(), term(), term(), term()) :: result(String.t())
  def restore_current_link(%{"kind" => "current", "id" => nil} = link, stored, resource_id, slot, context)
      when map_size(link) == 2 do
    with {:ok, ^link} <- current_link(stored, resource_id, slot, context), do: {:ok, stored}
  end

  def restore_current_link(_link, _stored, _resource_id, _slot, _context), do: {:error, :invalid_request}

  defp reference_wire(value) do
    if is_map(value) and Enum.sort(Map.keys(value)) == Enum.sort(@ref_fields) do
      with :ok <- identifiers(value, [:grant_id, :project_namespace]),
           {:ok, id} <- identity(value.runtime_identity),
           :ok <- unsigned(value.fence_epoch, 1),
           true <- digest?(value.grant_sha256) do
        {:ok, value |> stringify() |> Map.put("runtime_identity", id)}
      else
        _ -> unencodable()
      end
    else
      {:error, :invalid_request}
    end
  end

  defp binding_matches(value, expected) do
    cond do
      value.project_namespace !== expected.project_namespace -> {:error, :namespace_mismatch}
      value.runtime_identity !== expected.runtime_identity -> {:error, :identity_mismatch}
      value.grant_id !== expected.grant_id -> {:error, :stale_grant}
      true -> :ok
    end
  end

  defp resource_generation_matches(value, current) do
    with :ok <- generation_scope(current, value.project_namespace),
         :ok <- equal(value.owner_host_id, current.host_id, :recovery_generation_mismatch),
         :ok <- equal(value.reconciliation_generation, current, :recovery_generation_mismatch),
         :ok <- generation_scope(value.creation_generation, value.project_namespace),
         :ok <- equal(value.creation_generation.host_id, current.host_id, :recovery_generation_mismatch),
         true <- value.creation_generation === current or value.creation_generation.sequence < current.sequence do
      :ok
    else
      false -> {:error, :recovery_generation_mismatch}
      {:error, _} = error -> error
    end
  end

  # These private invariants mirror AttemptResourceLedger at the pinned P01
  # baseline. Its constructor validates the wider value schema, while persisted
  # P01 rows can only describe this dormant progression. Do not widen this path
  # for future P08 states or call a ledger owner from a pure conversion.
  defp historical_resource(value) do
    if is_nil(value.allocation_identity_sha256) and
         generation_precedes?(value.creation_generation, value.reconciliation_generation) and
         historical_state?(value),
       do: :ok,
       else: {:error, :invalid_request}
  end

  defp historical_state?(%AttemptResource{state: state} = value) when state in [:reserved, :fencing] do
    expected_revision = if state == :reserved, do: 0, else: 1
    q = value.quarantine

    value.revision == expected_revision and is_nil(value.last_evidence_ref) and
      value.creation_generation == value.reconciliation_generation and
      q.state == :clear and is_nil(q.reason) and is_nil(q.evidence_ref) and is_nil(q.resolution_ref) and
      q.generation == value.reconciliation_generation
  end

  defp historical_state?(%AttemptResource{state: :quarantined} = value) do
    q = value.quarantine
    minimum_revision = %{quarantined: 1, block_reuse: 2, operator_resolution_pending: 3, remains_quarantined: 4}

    case Map.fetch(minimum_revision, q.state) do
      {:ok, minimum} ->
        value.revision >= minimum and q.reason != nil and value.last_evidence_ref == q.evidence_ref and
          generation_precedes?(value.creation_generation, q.generation) and
          generation_precedes?(q.generation, value.reconciliation_generation)

      :error ->
        false
    end
  end

  defp historical_state?(_value), do: false

  defp generation_precedes?(older, newer) do
    older.project_namespace == newer.project_namespace and older.host_id == newer.host_id and
      (older == newer or older.sequence < newer.sequence)
  end

  defp generation_scope(value, namespace), do: equal(value.project_namespace, namespace, :namespace_mismatch)
  defp equal(value, expected, _error) when value === expected, do: :ok
  defp equal(_value, _expected, error), do: {:error, error}

  defp stored_struct(value, module) do
    if exact_struct?(value, module) and module.new(Map.from_struct(value)) == {:ok, value},
      do: :ok,
      else: unencodable()
  end

  defp exact_struct?(value, module) do
    is_struct(value, module) and Enum.sort(Map.keys(value)) == Enum.sort(Map.keys(module.__struct__()))
  end

  defp identifiers(value, fields) do
    Enum.reduce_while(fields, :ok, fn field, :ok ->
      case identifier(Map.fetch!(value, field)) do
        {:ok, _} -> {:cont, :ok}
        error -> {:halt, error}
      end
    end)
  end

  defp unsigned(value, minimum) when is_integer(value) and value >= minimum and value <= @u64, do: :ok
  defp unsigned(_value, _minimum), do: unencodable()
  defp optional_identifier(nil), do: :ok
  defp optional_identifier(value), do: with({:ok, _} <- identifier(value), do: :ok)
  defp digest?(value), do: is_binary(value) and byte_size(value) == 64 and Regex.match?(~r/\A[0-9a-f]{64}\z/, value)
  defp stringify(map), do: Map.new(map, fn {key, value} -> {Atom.to_string(key), value} end)
  defp unencodable, do: {:error, :unencodable_p01_value}

  defp validate_self_bindings(bindings), do: validate_self_bindings(bindings, [])
  defp validate_self_bindings([], _seen), do: :ok

  defp validate_self_bindings([%{"resource_id" => id, "slot" => slot} = binding | rest], seen)
       when map_size(binding) == 2 do
    with true <- slot in @slots and binding not in seen,
         {:ok, _} <- identifier(id) do
      validate_self_bindings(rest, [binding | seen])
    else
      {:error, :unencodable_p01_value} = error -> error
      _ -> {:error, :invalid_request}
    end
  end

  defp validate_self_bindings(_bindings, _seen), do: {:error, :invalid_request}
end
