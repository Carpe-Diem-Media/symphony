defmodule SymphonyElixir.Gate2AttemptTypesTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.AgentRuntime.AttemptGrant
  alias SymphonyElixir.AgentRuntime.AttemptResource
  alias SymphonyElixir.AgentRuntime.CleanupEvidenceRef
  alias SymphonyElixir.AgentRuntime.QuarantineDisposition
  alias SymphonyElixir.AgentRuntime.RecoveryGeneration
  alias SymphonyElixir.AgentRuntime.RuntimeAttempt.Identity

  test "grant binds all five runtime identity fields" do
    identity = identity()
    grant = grant(identity)

    assert {:ok, built} = AttemptGrant.new(grant)
    assert built.runtime_identity == identity

    for field <- [:runtime_attempt_id, :work_item_id, :lineage_generation, :responsibility, :runtime_profile] do
      changed = Map.update!(identity, field, &(&1 <> "-other"))
      assert {:ok, changed_grant} = AttemptGrant.new(Map.put(grant, :runtime_identity, changed))
      refute AttemptGrant.reference(built) == AttemptGrant.reference(changed_grant)
    end

    assert AttemptGrant.reference(built) == AttemptGrant.reference(built)
  end

  test "recovery generation is not lineage generation" do
    assert {:ok, generation} = RecoveryGeneration.new(generation())
    assert generation.sequence == 1

    assert {:error, :invalid_request} =
             RecoveryGeneration.new(Map.put(generation(), :sequence, 0))
  end

  test "cleanup reference shape is not cleanup authority" do
    assert {:ok, evidence} = CleanupEvidenceRef.new(cleanup_evidence())
    assert evidence.verification_generation.sequence == 1
    assert evidence.runtime_identity.lineage_generation == "lineage-1"
  end

  test "quarantine dispositions reject unknown states and malformed evidence references" do
    valid = quarantine()

    for invalid <- [
          %{valid | state: :unknown},
          %{valid | reason: :unknown},
          %{valid | evidence_ref: " "},
          %{valid | resolution_ref: " "},
          %{valid | generation: Map.put(generation(), :sequence, 0)}
        ] do
      assert {:error, :invalid_request} = QuarantineDisposition.new(invalid)
    end

    assert {:error, :invalid_request} = QuarantineDisposition.new(:invalid)
  end

  test "unknown and secret-bearing fields are rejected" do
    assert {:error, :invalid_request} =
             RecoveryGeneration.new(Map.put(generation(), :extra, "value"))

    assert {:error, :invalid_request} =
             AttemptGrant.new(Map.put(grant(identity()), :api_key, "secret"))

    assert {:error, :invalid_request} =
             AttemptResource.new(Map.put(resource(), :api_key, "secret"))

    assert {:error, :invalid_request} =
             QuarantineDisposition.new(Map.put(quarantine(), :api_key, "secret"))

    assert {:error, :invalid_request} =
             CleanupEvidenceRef.new(Map.put(cleanup_evidence(), :api_key, "secret"))

    assert {:ok, built} = AttemptGrant.new(grant(identity()))
    refute Map.has_key?(Map.from_struct(built), :api_key)
  end

  test "nested structs are revalidated before construction" do
    invalid_generation = struct(RecoveryGeneration, Map.put(generation(), :sequence, 0))
    secret_generation = Map.put(struct(RecoveryGeneration, generation()), :api_key, "secret")
    invalid_identity = Map.put(identity(), :api_key, "secret")
    oversized_identity = %Identity{identity() | work_item_id: String.duplicate("x", 257)}

    for nested <- [invalid_generation, secret_generation] do
      assert {:error, :invalid_request} =
               AttemptGrant.new(Map.put(grant(identity()), :recovery_generation, nested))
    end

    for nested <- [invalid_generation, secret_generation] do
      assert {:error, :invalid_request} =
               CleanupEvidenceRef.new(Map.put(cleanup_evidence(), :verification_generation, nested))
    end

    for nested <- [invalid_generation, secret_generation] do
      assert {:error, :invalid_request} =
               AttemptResource.new(Map.put(resource(), :creation_generation, nested))
    end

    assert {:error, :invalid_request} =
             AttemptResource.new(Map.put(resource(), :quarantine, Map.put(quarantine(), :generation, invalid_generation)))

    for changed <- [invalid_identity, oversized_identity] do
      assert {:error, :invalid_request} =
               AttemptGrant.new(Map.put(grant(changed), :runtime_identity, changed))

      assert {:error, :invalid_request} =
               CleanupEvidenceRef.new(Map.put(cleanup_evidence(), :runtime_identity, changed))

      assert {:error, :invalid_request} =
               AttemptResource.new(Map.put(resource(), :runtime_identity, changed))
    end
  end

  defp identity do
    %Identity{
      runtime_attempt_id: "attempt-1",
      work_item_id: "item-1",
      lineage_generation: "lineage-1",
      responsibility: "builder",
      runtime_profile: "profile-1"
    }
  end

  defp generation do
    %{
      schema_version: 1,
      project_namespace: "project-1",
      host_id: "host-1",
      boot_id: "boot-1",
      sequence: 1,
      nonce: "nonce-1"
    }
  end

  defp grant(identity) do
    %{
      schema_version: 1,
      grant_id: "grant-1",
      project_namespace: "project-1",
      tracker_identity_sha256: digest(),
      runtime_identity: identity,
      recovery_generation: generation(),
      route_fingerprint: digest(),
      subscription_registration_id: "registration-1",
      credential_generation: 1,
      workspace_resource_id: "workspace-1",
      source_admission_policy_sha256: digest(),
      process_policy_sha256: digest(),
      network_policy_sha256: digest(),
      tool_policy_sha256: digest(),
      capacity_profile_sha256: digest(),
      allowed_operations: [:workspace_read, :workspace_write],
      fence_epoch: 1
    }
  end

  defp cleanup_evidence do
    %{
      schema_version: 1,
      evidence_id: "evidence-1",
      evidence_sha256: digest(),
      project_namespace: "project-1",
      grant_id: "grant-1",
      runtime_identity: identity(),
      fence_epoch: 1,
      resource_set_sha256: digest(),
      verification_generation: generation(),
      verifier_implementation_sha256: digest()
    }
  end

  defp resource do
    %{
      schema_version: 1,
      resource_id: "resource-1",
      project_namespace: "project-1",
      grant_id: "grant-1",
      runtime_identity: identity(),
      class: :workspace,
      state: :reserved,
      revision: 0,
      stable_locator: "locator-1",
      allocation_identity_sha256: nil,
      capacity_profile_sha256: digest(),
      owner_host_id: "host-1",
      creation_generation: generation(),
      reconciliation_generation: generation(),
      last_evidence_ref: nil,
      quarantine: quarantine()
    }
  end

  defp quarantine do
    %{state: :clear, reason: nil, evidence_ref: nil, generation: generation(), resolution_ref: nil}
  end

  defp digest, do: String.duplicate("a", 64)
end
