defmodule SymphonyElixir.Gate2GovernanceProjectionTest do
  use ExUnit.Case, async: true

  alias SymphonyElixir.Gate2.{EvidenceApplicability, Qualification}

  @root Path.expand("../../..", __DIR__)
  @docs Path.join(@root, "docs/symphony-hardening-playbook-v4.1")

  test "catalog preserves all frozen obligations and exact acceptance limits" do
    frozen = frozen()
    catalog = Qualification.catalog()
    assert length(catalog["obligations"]) == 26

    for {actual, original} <- Enum.zip(catalog["obligations"], frozen["obligations"]) do
      assert actual["id"] == original["obligation_id"]
      assert actual["title"] == original["title"]
      assert actual["acceptance_owner"] == original["acceptance_owner"]
      assert actual["pass_condition"] == original["pass_condition"]
      assert actual["failure_disposition"] == original["failure_disposition"]
      assert actual["disposition"] == "MISSING"
      assert actual["proof_status"] == "UNVERIFIED"
    end
  end

  test "proof classes match canonical plan section D for every obligation" do
    plan = File.read!(Path.join(@root, "docs/superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md"))
    section = plan |> String.split("## D. 26/26 obligation coverage matrix") |> List.last() |> String.split("### D1.") |> hd()
    classes = Regex.scan(~r/\*\*(OB-\d{3})\.[^\n]+\n\s+([A-Z\/]+)\./, section)
    assert length(classes) == 26

    for [_, id, proof_classes] <- classes do
      claim = Enum.find(Qualification.catalog()["obligations"], &(&1["id"] == id))
      assert claim["required_proof_classes"] == String.split(proof_classes, "/")
    end
  end

  test "all ET and BP records retain the frozen transfer, control and failure contracts" do
    catalog = Qualification.catalog()
    frozen = frozen()
    assert length(catalog["transfers"]) == 13
    assert length(catalog["bearer_paths"]) == 19

    for {actual, original} <- Enum.zip(catalog["transfers"], frozen["evidence_transfer_matrix"]) do
      assert actual["id"] == original["claim_id"]

      for key <- ~w(source authority_class original_scope transfer_status transferred_property non_transferred_property) do
        assert actual[key] == original[key]
      end

      assert actual["new_proof_required"]
      assert actual["required_proof_classes"] == ["EB", "IR"]
    end

    for {actual, original} <- Enum.zip(catalog["bearer_paths"], frozen["bearer_readability_proofs"]) do
      assert actual["id"] == original["claim_id"]

      for key <- ~w(channel_class positive_control negative_control failure_disposition) do
        assert actual[key] == original[key]
      end

      assert actual["required_proof_classes"] == ["POSITIVE_CONTROL", "NEGATIVE_CONTROL"]
    end
  end

  test "authority references are current bytes and the catalog grants no runtime authority" do
    catalog = Qualification.catalog()

    for reference <- catalog["authority_references"] do
      bytes = File.read!(Path.join(@root, reference["path"]))
      assert Base.encode16(:crypto.hash(:sha256, bytes), case: :lower) == reference["sha256"]
    end

    assert catalog["source_baseline"] == %{
             "commit" => "2ba7cb5f49399cbe41ea527af5abcdac0dda1281",
             "tree" => "75d6df5e972bd253b272974dd8adec6452f5e00d"
           }

    assert catalog["state"] == "UNQUALIFIED"
    assert catalog["scope"] == "DORMANT_DEVELOPMENT_ASSESSMENT_ONLY"
    assert catalog["operational_host_profiles"] == []
    assert catalog["mechanical_verification"] == "UNCONFIGURED"
    assert catalog["independent_review"] == "UNCONFIGURED"
    refute catalog["gate2_activation"]
    refute catalog["h100_acceptance"]
  end

  test "parser bounds derive from all slots and no catalog record claims applicability or acceptance" do
    catalog = Qualification.catalog()
    claims = catalog["obligations"] ++ catalog["transfers"] ++ catalog["bearer_paths"]
    slot_count = Enum.sum(Enum.map(claims, &length(&1["required_proof_classes"])))
    contract = catalog["assessment_input_contract"]
    assert slot_count == 218
    assert contract["max_records"] == slot_count
    assert contract["max_artifact_bytes"] == EvidenceApplicability.max_artifact_bytes()
    assert contract["max_payload_bytes"] == slot_count * contract["max_artifact_bytes"]
    assert contract["scope"] == "DEVELOPMENT_PARSER_ONLY"
    assert contract["operational_capacity_authority"] == "UNCONFIGURED"
    assert catalog["characterization_scope"] == "ARTIFACT_BYTES_AND_DECLARATIONS_ONLY"

    for record <- [catalog | claims], field <- ~w(claim_applicability evidence_catalog_binding independent_acceptance) do
      assert record[field] == "UNVERIFIED"
    end
  end

  defp frozen do
    @docs |> Path.join("GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json") |> File.read!() |> Jason.decode!()
  end
end
