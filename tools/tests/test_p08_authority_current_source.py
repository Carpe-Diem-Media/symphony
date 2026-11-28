"""Authorized synthetic source tests, never operational approval or R1a release.

Run with python3 -B -m unittest discover -s tools/tests -p
 test_p08_authority_current_source.py. No historical guarded launcher is imported.
Synthetic keys are created only in an owner-scoped temporary test directory.
"""
import base64
import io
import os
import time
import socket
import stat
import tarfile
import subprocess
import copy
from unittest import mock
import hashlib
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
REPO = ROOT.parent
def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

gate = load('r3_test_gate', ROOT / 'p08_authority/gate.py')

class RoutingTests(unittest.TestCase):
    def test_legacy_profile_routes_without_rewriting_enrollment(self):
        self.assertTrue(hasattr(gate, 'select_verifier'), 'trusted profile dispatcher is missing')
        profile = {'schema': 'p08-verifier-enrollment-2'}
        context = {'profile': profile, 'accepted_profile_sha256': gate.verify.sha256(gate.verify.canonical(profile))}
        self.assertIs(gate.verify, gate.select_verifier(context))

    def test_unknown_and_unaccepted_profiles_refuse(self):
        self.assertTrue(hasattr(gate, 'select_verifier'), 'trusted profile dispatcher is missing')
        for profile, accepted in [({'schema':'unknown'},True), ({'schema':'p08-verifier-enrollment-2'},False)]:
            context = {'profile':profile, 'accepted_profile_sha256':gate.verify.sha256(gate.verify.canonical(profile)) if accepted else 'a'*64}
            with self.assertRaises(gate.Refusal): gate.select_verifier(context)

    def test_conflicting_top_level_selector_cannot_override_trusted_profile(self):
        profile = {'schema':'p08-verifier-enrollment-2'}
        for name in ('verifier','verifier_family','record_family'):
            context={'profile':profile,'accepted_profile_sha256':gate.verify.sha256(gate.verify.canonical(profile)),
                     name:'D02_CURRENT_SOURCE_REBIND_R3'}
            with self.assertRaises(gate.Refusal) as caught:gate.select_verifier(context)
            self.assertEqual('VERIFIER_FAMILY_UNAPPROVED',caught.exception.code)

    def test_r3_retains_shared_exception_and_legacy_module(self):
        self.assertTrue(hasattr(gate, 'select_verifier'), 'trusted profile dispatcher is missing')
        legacy = gate.verify
        profile = {'schema':'p08-verifier-enrollment-3', 'record_family':'D02_CURRENT_SOURCE_REBIND_R3'}
        context = {'profile':profile,'accepted_profile_sha256':legacy.sha256(legacy.canonical(profile))}
        selected = gate.select_verifier(context)
        self.assertIs(selected.Refusal, gate.Refusal)
        self.assertIs(gate.verify, legacy)
        self.assertIsNot(selected, legacy)



# These fixtures derive from the reviewed R2 tests but do not import or bypass
# their refusal-only R1a runner. This owner-authorized synthetic suite confers
# no external execution receipt or qualification. No operational key is read.
verify=gate._r3
OUT=None
FIX=None
KEYS=None
SSH='/usr/bin/ssh-keygen'

def _digest(raw): return hashlib.sha256(raw).hexdigest()


def _default_record(name):
    schema = verify.SCHEMAS[name]
    record = {}
    for field, prop in schema["properties"].items():
        if "const" in prop:
            record[field] = prop["const"]
        elif "enum" in prop:
            record[field] = prop["enum"][0]
        elif prop.get("type") == "integer":
            record[field] = prop.get("minimum", 0)
        elif prop.get("type") == "string":
            pattern = prop.get("pattern", "")
            match = __import__("re").fullmatch(r"\^\[0-9a-f\]\{(\d+)\}\$", pattern)
            if match:
                record[field] = "a" * int(match.group(1))
            elif "enum" in prop:
                record[field] = prop["enum"][0]
            else:
                record[field] = "synthetic"
        elif prop.get("type") == "array":
            record[field] = []
        elif prop.get("type") == "boolean":
            record[field] = False
        elif "enum" in prop:
            record[field] = prop["enum"][0]
        else:
            raise AssertionError((name, field, prop))
    return record


def _write_profile(profile):
    raw = verify.canonical(profile)
    return _digest(raw), raw


def _bind_synthetic_evidence(value, digest):
    """Replace repeated placeholder evidence references with one stored blob."""
    if isinstance(value, dict):
        for key, child in value.items():
            if key.endswith("_sha256") and key != "sha256" and isinstance(child, str) \
                    and len(child) == 64 and len(set(child)) == 1:
                value[key] = digest
            else:
                _bind_synthetic_evidence(child, digest)
    elif isinstance(value, list):
        for child in value:
            _bind_synthetic_evidence(child, digest)


def make_fixture(command_argv=None, working_directory=None):
    """Create a valid synthetic active build chain and sign its four signed records.

    The root runner must provide disposable keys in OUT/keys and restrict these
    exact ssh-keygen calls to this fixture directory.
    """
    FIX.mkdir(parents=True, exist_ok=True)
    (FIX / "signers").mkdir(exist_ok=True)
    (KEYS / "owner.pub").read_bytes()
    (KEYS / "reviewer.pub").read_bytes()
    principals = {"project-owner-issuer": ("owner", "test-owner"),
                  "independent-reviewer": ("reviewer", "test-reviewer")}
    ns = {"project-owner-issuer": sorted(["symphony.p08.r3.source-stage.v3", "symphony.p08.r3.input-owner.v2", "symphony.p08.r3.native-grant.v3"]),
          "independent-reviewer": sorted(["symphony.p08.r3.input-review.v3", "symphony.p08.r3.build-result.v2", "symphony.p08.r3.source-review.v1"])}
    keys = []
    for role in ("project-owner-issuer", "independent-reviewer"):
        publine = (KEYS / (principals[role][0] + ".pub")).read_text("ascii").split()
        wire = base64.b64decode(publine[1], validate=True)
        keys.append({"principal": principals[role][1], "role": role,
                     "public_key": " ".join(publine[:2]),
                     "fingerprint": hashlib.sha256(wire).hexdigest(), "namespaces": ns[role],
                     "custody_record_sha256": "b" * 64, "not_before": 1699990000, "expires_at": 1800000000})
    now = 1700000000
    signer_bytes = {}
    for role, (keyname, principal) in principals.items():
        publine = (KEYS / (keyname + ".pub")).read_text("ascii").split()
        leaf = "owner" if role == "project-owner-issuer" else "reviewer"
        signer_bytes[leaf] = f'{principal} namespaces="{",".join(ns[role])}" {publine[0]} {publine[1]}\n'.encode("ascii")
    verifier_path = "/usr/bin/ssh-keygen"
    verifier_bytes = Path(verifier_path).read_bytes()
    verifier_stat = Path(verifier_path).stat()
    verifier_entry = {"kind":"regular", "path":verifier_path,
        "mode":format(verifier_stat.st_mode & 0o777, "04o"), "bytes":len(verifier_bytes), "sha256":_digest(verifier_bytes)}
    verifier_inventory = {"schema":"p08-input-inventory-1", "entries":[verifier_entry]}
    verifier_inventory_hash, verifier_inventory_raw = _write_profile(verifier_inventory)
    verifier_artifact = {"id":"verifier", "path":verifier_path, "resolved_path":verifier_path,
        "bytes":len(verifier_bytes), "sha256":_digest(verifier_bytes), "provenance_sha256":"b"*64,
        "inventory_sha256":verifier_inventory_hash,
        "path_entry_sha256":_digest(verify.canonical(verifier_entry)),
        "resolved_entry_sha256":_digest(verify.canonical(verifier_entry)), "symlink_chain":[]}
    profile = {"schema": "p08-verifier-enrollment-3", "record_family":"D02_CURRENT_SOURCE_REBIND_R3", "keys": keys,
               "verifier_artifact": verifier_artifact, "verifier_inventory_sha256": verifier_inventory_hash,
               "verification_vectors_sha256": "d"*64, "allowed_signers_sha256": _digest(signer_bytes["owner"] + signer_bytes["reviewer"]),
               "revocation_procedure_sha256": "f"*64, "status_procedure_sha256": "1"*64,
               "preflight_procedure_sha256": "2"*64, "operator_appointment_sha256": "3"*64,
               "clock_procedure_sha256": "4"*64, "one_use_register_procedure_sha256": "5"*64,
               "approval_max_age_s": 86400, "lease_max_s": 900, "clock_skew_max_s": 30,
               "action_observation_max_age_s": 60}
    trust_hash = _digest(verify.canonical(profile))
    # The two allowed-signers files contain one principal and its closed namespace list.
    for role, (keyname, principal) in principals.items():
        publine = (KEYS / (keyname + ".pub")).read_text("ascii").split()
        leaf = "owner" if role == "project-owner-issuer" else "reviewer"
        namespaces = ",".join(ns[role])
        (FIX / "signers" / leaf).write_bytes(signer_bytes[leaf])

    # Create a closed one-file executable inventory and its installed reference.
    sentinel = "/usr/bin/python3.14"
    sentinel_bytes = Path(sentinel).read_bytes()
    sentinel_stat = Path(sentinel).stat()
    argv = command_argv or [sentinel, "-I", "-S", "-B", "-c", "pass"]
    entry = {"kind": "regular", "path": sentinel, "mode": format(sentinel_stat.st_mode & 0o777, "04o"),
             "bytes": len(sentinel_bytes), "sha256": _digest(sentinel_bytes)}
    inventory = {"schema": "p08-input-inventory-1", "entries": [entry]}
    inv_hash, inv_raw = _write_profile(inventory)
    artifact = {"id": "fixture-command", "path": sentinel, "resolved_path": sentinel,
                "bytes": len(sentinel_bytes), "sha256": _digest(sentinel_bytes), "provenance_sha256": "7"*64,
                "inventory_sha256": inv_hash, "path_entry_sha256": _digest(verify.canonical(entry)),
                "resolved_entry_sha256": _digest(verify.canonical(entry)), "symlink_chain": []}
    command = {"schema": "p08-command-2", "id": "fixture-command", "authorization_scope": "BUILD_ONLY",
               "executable": artifact, "argv": [{"index": i, "value": arg} for i, arg in enumerate(argv)],
               "working_directory": working_directory or str(FIX), "expected_results_sha256": "8"*64,
               "allowed_effects_sha256": "9"*64}
    execution = {"schema": "p08-execution-2", "commands": [command],
                 "mounts_profile_sha256": "a"*64, "uid_profile_sha256": "b"*64,
                 "write_roots_sha256": "c"*64, "environment": [], "cargo_ancestry_sha256": "d"*64,
                 "child_allowlist_sha256": "e"*64, "network_control_sha256": "f"*64,
                 "clock_profile_sha256": "1"*64, "observation_procedure_sha256": "2"*64,
                 "evidence_profile_sha256": "3"*64, "source_date_epoch": 1794201657}
    build_image = {"schema": "p08-build-image-1", "oci_manifest_sha256": "4"*64,
                   "platform": "linux/amd64", "layers": [], "publisher_provenance_sha256": "5"*64,
                   "files_inventory_sha256": inv_hash, "sbom_sha256": "6"*64, "licenses_sha256": "7"*64}
    component = {"schema": "p08-component-2", "role": "toolchain", "version": "synthetic",
                 "target": "x86_64-unknown-linux-gnu", "distribution_provenance_sha256": "8"*64,
                 "files_inventory_sha256": inv_hash, "entry_points": [artifact],
                 "configuration_sha256": "9"*64, "licenses_sha256": "a"*64}
    linker = {"schema": "p08-linker-2", "driver": "synthetic", "flavor": "synthetic", "entry_point": artifact,
              "files_inventory_sha256": inv_hash, "crt_profile_sha256": "b"*64, "self_contained": "OFF",
              "static_form": "STATIC_PIE", "arguments": [], "provenance_sha256": "c"*64, "licenses_sha256": "d"*64}
    evidence_blob = b"P08 synthetic fixture evidence"
    evidence_hash = _digest(evidence_blob)
    for value in (profile, inventory, build_image, execution, component, linker,
                  verifier_inventory, verifier_artifact):
        _bind_synthetic_evidence(value, evidence_hash)
    source_facts = source_fixture()
    base_entries = source_facts["base_inventory"]
    base_tree = {"commit":source_facts["base_commit"],"tree":source_facts["base_tree"]}
    source_entries = copy.deepcopy(source_facts["observed_entries"])
    identity_path = "native/gate2/protocol/tests/locked_build_identity.rs"
    changed_entry = next(entry for entry in source_entries if entry["path"] == identity_path)

    source_inventory = {"schema": "p08-source-inventory-1", "commit": source_facts["commit"], "tree": source_facts["tree"],
                        "entries": source_entries}
    archives = [
        {"id":"cargo", "bytes":1, "sha256":"ea1de9f9e23107d97ee2b41a72c552f34064a593da503789218387aee59f3ba4", "provenance_sha256":"3"*64},
        {"id":"rustc", "bytes":1, "sha256":"e974f036b28565f37c0f3bd92ddefa809bee16c04f9dcf07b9ed96e05aaaf7c4", "provenance_sha256":"4"*64},
        {"id":"ruststd_host", "bytes":1, "sha256":"fa3ff450172a16c026944030230c5069947af93c728d9179971d44e5e0cfb561", "provenance_sha256":"5"*64},
        {"id":"ruststd_musl", "bytes":1, "sha256":"bd9f35880de21dab0e387e84009c00001ae7836a4ba565cb16823f13f75f325f", "provenance_sha256":"6"*64},
    ]
    rust_profile = {"schema": "p08-rust-provenance-1", "policy_decision_id": "5f6773bc-83ef-498f-b468-bd49d809b914",
                    "certificate_sha256": "e54b09a439647e006b4831eec9785cbaaf3e07ab371c3a6ee6a68e1bdb9fbc6b", "manifest_sha256": "a7c8774a5fd8441c997d94c029776cbc5eb111e9d72ab5d256fa69866644347e",
                    "manifest_signature_sha256": "a9fed69b47daaaf29a6207af9df13aedb66d502ab0acc4ea557602edf87fd1aa", "primary_fingerprint": "108f66205eaeb0aaa8dd5e1c85ab96e6fa1be5fe",
                    "signature_algorithm": "RSA/SHA512 primary direct signature",
                    "signature_time": "2026-09-03T12:54:14Z", "archives": archives,
                    "acquisition_receipts_sha256": "f"*64, "extraction_receipts_sha256": "1"*64,
                    "key_status_evidence_sha256": "2"*64}
    _bind_synthetic_evidence(rust_profile, evidence_hash)
    trust_hash = _digest(verify.canonical(profile))
    raw_profiles = {}
    def addprof(obj):
        digest, raw = _write_profile(obj); raw_profiles[digest] = raw; return digest
    raw_profiles[verifier_inventory_hash] = verifier_inventory_raw
    inv_digest = addprof(inventory)
    image_digest, execution_digest = addprof(build_image), addprof(execution)
    host_digest, musl_digest, crt_digest, tool_digest = (addprof({**component, "role": role,
        "target": "x86_64-unknown-linux-gnu" if role in ("host-std", "toolchain") else "x86_64-unknown-linux-musl"})
        for role in ("host-std", "musl-std", "crt", "toolchain"))
    linker["crt_profile_sha256"] = crt_digest
    linker_digest, source_digest, rust_digest = addprof(linker), addprof(source_inventory), addprof(rust_profile)

    manifest = _default_record("build-input-approval.json")
    manifest.update({"approval_id": "a"*32, "issued_at": now, "not_before": now, "expires_at": now+3600,
        "issuer_id": "test-owner", "reviewer_id": "test-reviewer", "trust_profile_sha256": trust_hash,
        "source_commit": source_inventory["commit"], "source_tree": source_inventory["tree"],
        "source_base_commit":source_facts["base_commit"],"source_base_tree":source_facts["base_tree"],
        "source_inventory_sha256": source_digest, "build_image_profile_sha256": image_digest,
        "execution_profile_sha256": execution_digest, "host_std_profile_sha256": host_digest,
        "musl_std_profile_sha256": musl_digest, "crt_profile_sha256": crt_digest,
        "toolchain_profile_sha256": tool_digest, "linker_profile_sha256": linker_digest,
        "rust_provenance_profile_sha256": rust_digest, "sbom_sha256": build_image["sbom_sha256"],
        "license_inventory_sha256": build_image["licenses_sha256"]})
    manifest["identity_test_sha256"] = changed_entry["sha256"]
    source_fields, review_raw, review_sig, authority, review_evidence = source_review_fixture(source_facts, profile, now)
    source = _default_record("source-stage-acceptance.json")
    source.update(source_fields)
    source.update({"issued_at": now-100, "issuer_id": "test-owner", "trust_profile_sha256": trust_hash})
    manifest["source_stage_acceptance_sha256"] = _digest(verify.canonical(source))
    review = _default_record("input-review.json")
    review.update({"findings_sha256":evidence_hash, "review_id": "a"*32, "issued_at": now+2, "expires_at": now+3500,
        "manifest_sha256": _digest(verify.canonical(manifest)), "reviewer_id": "test-reviewer",
        "source_stage_acceptance_sha256": _digest(verify.canonical(source)), "trust_profile_sha256": trust_hash})
    observed_profiles = [{"id": key.removesuffix("_sha256"), "bytes": len(raw_profiles[value]),
                          "sha256": value, "provenance_sha256": "8"*64}
        for key, value in sorted(manifest.items())
        if (key.endswith("_profile_sha256") and key != "trust_profile_sha256") or key == "source_inventory_sha256"]
    owner = _default_record("owner-input-decision.json")
    owner.update({"decision_id": "b"*32, "issued_at": now+3, "not_before": now+3, "expires_at": now+3400,
        "issuer_id": "test-owner", "manifest_sha256": _digest(verify.canonical(manifest)),
        "review_report_sha256": _digest(verify.canonical(review)),
        "review_signature_sha256": "0"*64,
        "source_stage_acceptance_sha256": _digest(verify.canonical(source)), "trust_profile_sha256": trust_hash})
    grant = _default_record("native-execution-grant.json")
    grant.update({"grant_id": "c"*32, "run_id": "d"*32, "nonce": "e"*64,
        "issued_at": now+5, "not_before": now+5, "expires_at": now+600, "max_duration_s": 300,
        "issuer_id": "test-owner", "manifest_sha256": _digest(verify.canonical(manifest)),
        "owner_decision_sha256": _digest(verify.canonical(owner)), "owner_signature_sha256": "0"*64,
        "review_report_sha256": _digest(verify.canonical(review)), "review_signature_sha256": "0"*64,
        "command_profile_sha256": _digest(verify.canonical(command)), "authorization_scope": "BUILD_ONLY",
        "action_observation_sha256": "0"*64, "status_report_sha256": "0"*64,
        "trust_profile_sha256": trust_hash, "source_commit": manifest["source_commit"], "source_tree": manifest["source_tree"],
        "trust_epoch": 1})
    for gf, mf in (("observed_build_image_profile_sha256","build_image_profile_sha256"),
                   ("observed_crt_profile_sha256","crt_profile_sha256"),
                   ("observed_execution_profile_sha256","execution_profile_sha256"),
                   ("observed_host_std_profile_sha256","host_std_profile_sha256"),
                   ("observed_linker_profile_sha256","linker_profile_sha256"),
                   ("observed_musl_std_profile_sha256","musl_std_profile_sha256"),
                   ("observed_rust_provenance_profile_sha256","rust_provenance_profile_sha256"),
                   ("observed_source_inventory_sha256","source_inventory_sha256"),
                   ("observed_toolchain_profile_sha256","toolchain_profile_sha256")):
        grant[gf] = manifest[mf]
    review_observation = {"schema":"p08-review-observation-1", "purpose":"INPUT_REVIEW_ONLY",
        "review_id":review["review_id"], "reviewer_id":"test-reviewer", "operator_id":"test-operator",
        "manifest_sha256":_digest(verify.canonical(manifest)), "trust_profile_sha256":trust_hash,
        "observed_at":now+1, "source_commit":manifest["source_commit"], "source_tree":manifest["source_tree"],
        "profiles":observed_profiles, "evidence_sha256":"a"*64, "verdict":"MATCH"}
    _bind_synthetic_evidence(review_observation, evidence_hash)
    review_obs_hash = addprof(review_observation)
    review["review_observation_sha256"] = review_obs_hash
    status_report = {"schema":"p08-approval-status-1", "operator_id":"test-operator", "run_id":grant["run_id"],
        "observed_at":now+5, "trust_epoch":1, "enrollment_sha256":"c"*64, "current_decisions_sha256":"d"*64,
        "revocations_sha256":"e"*64, "clock_evidence_sha256":"f"*64, "register_observation_sha256":"1"*64,
        "policy_a_evidence_sha256":"2"*64, "verdict":"ACTIVE"}
    _bind_synthetic_evidence(status_report, evidence_hash)
    status_hash = addprof(status_report); grant["status_report_sha256"] = status_hash
    # Sign the dependent records in chain order so each signature hash is final.
    bundle_objects = {"source-stage-acceptance.json": source, "build-input-approval.json": manifest,
        "input-review.json": review, "owner-input-decision.json": owner, "native-execution-grant.json": grant}
    bundle = {}
    sign_ns = {"source-stage-acceptance.json":"symphony.p08.r3.source-stage.v3",
        "input-review.json":"symphony.p08.r3.input-review.v3", "owner-input-decision.json":"symphony.p08.r3.input-owner.v2",
        "native-execution-grant.json":"symphony.p08.r3.native-grant.v3"}
    def signed(name, obj, role):
        raw, signature = sign_fixture(name, role, value=obj)
        return raw, _digest(signature)
    bundle["source-stage-acceptance.json"], _ = signed("source-stage-acceptance.json", source, "owner")
    bundle["input-review.json"], review_sig_hash = signed("input-review.json", review, "reviewer")
    owner["review_signature_sha256"] = review_sig_hash
    owner["review_report_sha256"] = _digest(bundle["input-review.json"])
    bundle["owner-input-decision.json"], owner_sig_hash = signed("owner-input-decision.json", owner, "owner")
    grant["review_signature_sha256"] = review_sig_hash
    grant["owner_signature_sha256"] = owner_sig_hash
    grant["review_report_sha256"] = _digest(bundle["input-review.json"])
    grant["owner_decision_sha256"] = _digest(bundle["owner-input-decision.json"])
    action = {"schema":"p08-action-observation-1", "purpose":"ACTION_PREFLIGHT_ONLY",
        "operator_id":"test-operator", "grant_id":grant["grant_id"], "run_id":grant["run_id"], "nonce":grant["nonce"],
        "manifest_sha256":grant["manifest_sha256"], "owner_decision_sha256":grant["owner_decision_sha256"],
        "review_report_sha256":grant["review_report_sha256"], "trust_profile_sha256":trust_hash,
        "command_profile_sha256":grant["command_profile_sha256"], "authorization_scope":"BUILD_ONLY",
        "observation_started_at":now+4, "observed_at":now+5, "clock_session_id":"a"*32,
        "completed_monotonic_ns":1000000000, "source_commit":manifest["source_commit"], "source_tree":manifest["source_tree"],
        "profiles":observed_profiles, "evidence_sha256":"b"*64, "verdict":"MATCH"}
    _bind_synthetic_evidence(action, evidence_hash)
    action_hash = addprof(action); grant["action_observation_sha256"] = action_hash
    bundle["native-execution-grant.json"], _ = signed("native-execution-grant.json", grant, "owner")
    bundle["build-input-approval.json"] = verify.canonical(manifest)
    (FIX / "build-input-approval.json").write_bytes(bundle["build-input-approval.json"])
    status = {"now_min": now+5, "now_max": now+5, "trust_epoch":1,
            "clock_session_id":"a"*32, "monotonic_ns":2000000000, "operator_id":"test-operator",
            "enrollment_sha256":"c"*64, "current_decisions_sha256":"d"*64,
            "revocations_sha256":"e"*64, "clock_evidence_sha256":"f"*64,
            "register_observation_sha256":"1"*64, "policy_a_evidence_sha256":"2"*64, "revoked_ids":[]}
    _bind_synthetic_evidence(status, evidence_hash)
    profiles = {"profile": profile, "profiles": raw_profiles, "status": status,
        "accepted_profile_sha256": trust_hash, "bundle_root":str(FIX),
        "allowed_signers_root":str(FIX / "signers"),
        "sealed_roots":["/usr", str(OUT)],
        "source_facts":{"commit":manifest["source_commit"], "tree":manifest["source_tree"],
            "parent":source["source_commit"], "base_commit":base_tree["commit"], "base_tree":base_tree["tree"],
            "base_inventory":base_entries, "observed_entries":source_entries,
            "inventory_sha256":manifest["source_inventory_sha256"]}}
    bundle["source-review-attestation.json"]=review_raw
    profiles["source_review_authority"]=authority
    profiles["accepted_source_review_authority_sha256"]=_digest(verify.canonical(authority))
    profiles["source_facts"].update(source_facts)
    profiles["evidence_bytes"] = {evidence_hash:evidence_blob, **review_evidence}
    return bundle, profiles


def make_generated_fixture(mutation=None):
    """Build a synthetic B/Q/M_test/R_test/O_test/G_test chain.

    The Python interpreter stands in for a generated test executable. It is
    recorded as data and is never launched by this fixture.
    """
    producer_bundle, producer_context = make_fixture()
    producer_root = FIX / "producer"
    producer_root.mkdir(exist_ok=True)
    for name, raw in producer_bundle.items():
        (producer_root / name).write_bytes(raw)
        signature = FIX / name.replace(".json", ".sshsig")
        if signature.exists():
            (producer_root / signature.name).write_bytes(signature.read_bytes())
    producer_context = copy.deepcopy(producer_context)
    producer_context["bundle_root"] = str(producer_root)
    pm = verify.parse_record(producer_bundle["build-input-approval.json"], "build-input-approval.json")
    pg = verify.parse_record(producer_bundle["native-execution-grant.json"], "native-execution-grant.json")
    pr = verify.parse_record(producer_bundle["input-review.json"], "input-review.json")
    po = verify.parse_record(producer_bundle["owner-input-decision.json"], "owner-input-decision.json")
    now = producer_context["status"]["now_max"]
    raw_profiles = producer_context["profiles"]

    executable_path = "/usr/bin/python3.14"
    executable_raw = Path(executable_path).read_bytes()
    executable_stat = Path(executable_path).stat()
    executable_entry = {"kind": "regular", "path": executable_path,
        "mode": format(executable_stat.st_mode & 0o777, "04o"), "bytes": len(executable_raw),
        "sha256": _digest(executable_raw)}
    inventory = {"schema": "p08-input-inventory-1", "entries": [executable_entry]}
    inventory_hash = _digest(verify.canonical(inventory))
    raw_profiles[inventory_hash] = verify.canonical(inventory)
    executable = {"id": "locked_build_identity", "path": executable_path,
        "resolved_path": executable_path, "bytes": len(executable_raw), "sha256": _digest(executable_raw),
        "provenance_sha256": "2" * 64, "inventory_sha256": inventory_hash,
        "path_entry_sha256": _digest(verify.canonical(executable_entry)),
        "resolved_entry_sha256": _digest(verify.canonical(executable_entry)), "symlink_chain": []}
    fixture_evidence = b"P08 synthetic generated-output evidence"
    fixture_evidence_hash = _digest(fixture_evidence)
    custody = {"schema": "p08-generated-custody-1", "operator_id": "test-operator",
        "producer_grant_sha256": _digest(producer_bundle["native-execution-grant.json"]),
        "sealed_at": now, "inventory_sha256": inventory_hash, "mounts_profile_sha256": "a"*64,
        "custody_procedure_sha256": "b"*64, "evidence_sha256": fixture_evidence_hash, "verdict": "SEALED_READ_ONLY"}
    _bind_synthetic_evidence(custody, fixture_evidence_hash)
    custody_raw = verify.canonical(custody)
    custody_hash = _digest(custody_raw)

    evidence = {"schema": "p08-compilation-evidence-1",
        "producer_manifest_sha256": _digest(producer_bundle["build-input-approval.json"]),
        "producer_review_sha256": _digest(producer_bundle["input-review.json"]),
        "producer_owner_decision_sha256": _digest(producer_bundle["owner-input-decision.json"]),
        "producer_grant_sha256": _digest(producer_bundle["native-execution-grant.json"]),
        "producer_grant_signature_sha256": _digest((producer_root / "native-execution-grant.sshsig").read_bytes()),
        "producer_grant_id": pg["grant_id"], "producer_run_id": pg["run_id"], "producer_nonce": pg["nonce"],
        "producer_command_profile_sha256": pg["command_profile_sha256"], "source_commit": pm["source_commit"],
        "source_tree": pm["source_tree"], "started_at": now, "completed_at": now, "exit_code": 0,
        "prebuild_output_inventory_sha256": "3"*64, "output_inventory_sha256": inventory_hash,
        "custody_evidence_sha256": custody_hash, "input_reconciliation_sha256": "5"*64,
        "process_outcomes_sha256": "6"*64, "effects_audit_sha256": "7"*64,
        "inspection_authorizations_sha256": "8"*64, "inspection_results_sha256": "9"*64}
    _bind_synthetic_evidence(evidence, fixture_evidence_hash)
    evidence_hash = _digest(verify.canonical(evidence))
    executable["provenance_sha256"] = evidence_hash
    raw_profiles[evidence_hash] = verify.canonical(evidence)
    raw_profiles[custody_hash] = custody_raw
    generated = {"schema": "p08-generated-inputs-1",
        "producer_manifest_sha256": _digest(producer_bundle["build-input-approval.json"]),
        "producer_grant_sha256": _digest(producer_bundle["native-execution-grant.json"]),
        "compilation_evidence_sha256": evidence_hash, "files_inventory_sha256": inventory_hash,
        "custody_evidence_sha256": custody_hash, "source_commit": pm["source_commit"],
        "source_tree": pm["source_tree"], "executables": [executable]}
    generated_raw = verify.canonical(generated)
    generated_hash = _digest(generated_raw)
    raw_profiles[generated_hash] = generated_raw

    execution = json.loads(raw_profiles[pm["execution_profile_sha256"]].decode("ascii"))
    generated_command = copy.deepcopy(execution["commands"][0])
    generated_command.update({"id":"locked-build-identity-test",
        "authorization_scope":"BUILD_IDENTITY_TEST_EXECUTION", "executable":executable,
        "argv":[{"index":0,"value":executable_path},{"index":1,"value":"-I"},
                {"index":2,"value":"-S"},{"index":3,"value":"-B"},
                {"index":4,"value":"-c"},{"index":5,"value":"pass"}]})
    execution["commands"] = [generated_command]
    execution_raw = verify.canonical(execution)
    execution_hash = _digest(execution_raw)
    raw_profiles[execution_hash] = execution_raw

    receipt = {"schema": "p08-compilation-result-2", "receipt_id": "1"*32,
        "producer_manifest_sha256": _digest(producer_bundle["build-input-approval.json"]),
        "producer_review_sha256": _digest(producer_bundle["input-review.json"]),
        "producer_owner_decision_sha256": _digest(producer_bundle["owner-input-decision.json"]),
        "producer_grant_sha256": _digest(producer_bundle["native-execution-grant.json"]),
        "producer_grant_signature_sha256": _digest((producer_root / "native-execution-grant.sshsig").read_bytes()),
        "producer_grant_id": pg["grant_id"], "producer_run_id": pg["run_id"], "producer_nonce": pg["nonce"],
        "producer_command_profile_sha256": pg["command_profile_sha256"], "source_commit": pm["source_commit"],
        "source_tree": pm["source_tree"], "trust_profile_sha256": pm["trust_profile_sha256"],
        "reviewer_id": pm["reviewer_id"], "operator_id": "test-operator", "outcome": "SUCCESS_ELIGIBLE_OUTPUTS",
        "exit_code": 0, "started_at": now, "completed_at": now, "issued_at": now,
        "generated_inputs_profile_sha256": generated_hash, "compilation_evidence_sha256": evidence_hash}
    receipt_raw = verify.canonical(receipt)
    receipt_path = FIX / "compilation-result.json"
    receipt_path.write_bytes(receipt_raw)
    sign_fixture("compilation-result.json", "reviewer")
    receipt_sig_raw = receipt_path.with_suffix(".sshsig").read_bytes()

    manifest = _default_record("generated-input-approval.json")
    manifest.update({key: value for key, value in pm.items() if key in manifest})
    manifest.update({"schema":"p08-generated-input-approval-2", "approval_id": "f"*32, "issued_at": now+8, "not_before": now+8,
        "expires_at": now+3000, "compilation_result_sha256": _digest(receipt_raw),
        "compilation_result_signature_sha256": _digest(receipt_sig_raw),
        "generated_inputs_profile_sha256": generated_hash, "issuer_id": "test-owner",
        "reviewer_id": "test-reviewer", "trust_profile_sha256": pm["trust_profile_sha256"],
        "execution_profile_sha256":execution_hash})
    manifest["source_stage_acceptance_sha256"] = _digest(producer_bundle["source-stage-acceptance.json"])
    manifest_raw = verify.canonical(manifest)
    manifest_hash = _digest(manifest_raw)

    observed_profiles = [{"id":key.removesuffix("_sha256"), "bytes":len(raw_profiles[value]), "sha256":value,
        "provenance_sha256":fixture_evidence_hash}
        for key, value in sorted(manifest.items())
        if (key.endswith("_profile_sha256") and key != "trust_profile_sha256") or key == "source_inventory_sha256"]
    review_observation = {"schema":"p08-review-observation-1", "purpose":"INPUT_REVIEW_ONLY",
        "review_id":"2"*32, "reviewer_id":"test-reviewer", "operator_id":"test-operator",
        "manifest_sha256":manifest_hash, "trust_profile_sha256":pm["trust_profile_sha256"],
        "observed_at":now+8, "source_commit":pm["source_commit"], "source_tree":pm["source_tree"],
        "profiles":observed_profiles, "evidence_sha256":fixture_evidence_hash, "verdict":"MATCH"}
    review_observation_hash = _digest(verify.canonical(review_observation))
    raw_profiles[review_observation_hash] = verify.canonical(review_observation)
    review = _default_record("input-review.json")
    review.update({"findings_sha256":fixture_evidence_hash, "review_id":"2"*32, "issued_at":now+8, "expires_at":now+3000,
        "manifest_sha256":manifest_hash, "reviewer_id":"test-reviewer",
        "source_stage_acceptance_sha256":manifest["source_stage_acceptance_sha256"],
        "trust_profile_sha256":pm["trust_profile_sha256"], "review_observation_sha256":review_observation_hash})
    review_raw = verify.canonical(review)
    (FIX / "input-review.json").write_bytes(review_raw)
    sign_fixture("input-review.json", "reviewer")
    review_sig_raw = (FIX / "input-review.sshsig").read_bytes()
    owner = _default_record("owner-input-decision.json")
    owner.update({"decision_id":"3"*32, "issued_at":now+9, "not_before":now+9,
        "expires_at":now+2900, "issuer_id":"test-owner", "manifest_sha256":manifest_hash,
        "review_report_sha256":_digest(review_raw), "review_signature_sha256":_digest(review_sig_raw),
        "source_stage_acceptance_sha256":manifest["source_stage_acceptance_sha256"],
        "trust_profile_sha256":pm["trust_profile_sha256"]})
    owner_raw = verify.canonical(owner)
    (FIX / "owner-input-decision.json").write_bytes(owner_raw)
    sign_fixture("owner-input-decision.json", "owner")
    owner_sig_raw = (FIX / "owner-input-decision.sshsig").read_bytes()

    grant = _default_record("generated-native-execution-grant.json")
    grant.update({"grant_id":"4"*32, "run_id":"5"*32, "nonce":"6"*64,
        "issued_at":now+11, "not_before":now+11, "expires_at":now+300,
        "max_duration_s":120, "issuer_id":"test-owner", "manifest_sha256":manifest_hash,
        "owner_decision_sha256":_digest(owner_raw), "owner_signature_sha256":_digest(owner_sig_raw),
        "review_report_sha256":_digest(review_raw), "review_signature_sha256":_digest(review_sig_raw),
        "authorization_scope":"BUILD_IDENTITY_TEST_EXECUTION", "source_commit":pm["source_commit"],
        "source_tree":pm["source_tree"], "trust_profile_sha256":pm["trust_profile_sha256"], "trust_epoch":1,
        "observed_generated_inputs_profile_sha256":generated_hash})
    grant["command_profile_sha256"] = _digest(verify.canonical(generated_command))
    for grant_field, manifest_field in (("observed_build_image_profile_sha256","build_image_profile_sha256"),
        ("observed_crt_profile_sha256","crt_profile_sha256"),
        ("observed_execution_profile_sha256","execution_profile_sha256"),
        ("observed_host_std_profile_sha256","host_std_profile_sha256"),
        ("observed_linker_profile_sha256","linker_profile_sha256"),
        ("observed_musl_std_profile_sha256","musl_std_profile_sha256"),
        ("observed_rust_provenance_profile_sha256","rust_provenance_profile_sha256"),
        ("observed_source_inventory_sha256","source_inventory_sha256"),
        ("observed_toolchain_profile_sha256","toolchain_profile_sha256")):
        grant[grant_field] = manifest[manifest_field]
    if mutation == "mismatched-provenance":
        grant["observed_generated_inputs_profile_sha256"] = "0"*64

    status_report = {"schema":"p08-approval-status-1", "operator_id":"test-operator",
        "run_id":grant["run_id"], "observed_at":now+11, "trust_epoch":1,
        "enrollment_sha256":producer_context["status"]["enrollment_sha256"],
        "current_decisions_sha256":producer_context["status"]["current_decisions_sha256"],
        "revocations_sha256":producer_context["status"]["revocations_sha256"],
        "clock_evidence_sha256":producer_context["status"]["clock_evidence_sha256"],
        "register_observation_sha256":producer_context["status"]["register_observation_sha256"],
        "policy_a_evidence_sha256":producer_context["status"]["policy_a_evidence_sha256"], "verdict":"ACTIVE"}
    status_hash = _digest(verify.canonical(status_report))
    raw_profiles[status_hash] = verify.canonical(status_report)
    grant["status_report_sha256"] = status_hash
    owner_hash = _digest(owner_raw)
    action = {"schema":"p08-action-observation-1", "purpose":"ACTION_PREFLIGHT_ONLY",
        "operator_id":"test-operator", "grant_id":grant["grant_id"], "run_id":grant["run_id"],
        "nonce":grant["nonce"], "manifest_sha256":manifest_hash, "owner_decision_sha256":owner_hash,
        "review_report_sha256":_digest(review_raw), "trust_profile_sha256":pm["trust_profile_sha256"],
        "command_profile_sha256":grant["command_profile_sha256"],
        "authorization_scope":grant["authorization_scope"], "observation_started_at":now+10,
        "observed_at":now+10, "clock_session_id":producer_context["status"]["clock_session_id"],
        "completed_monotonic_ns":1900000000, "source_commit":pm["source_commit"],
        "source_tree":pm["source_tree"], "profiles":observed_profiles,
        "evidence_sha256":fixture_evidence_hash, "verdict":"MATCH"}
    action_hash = _digest(verify.canonical(action))
    raw_profiles[action_hash] = verify.canonical(action)
    grant["action_observation_sha256"] = action_hash
    grant_raw = verify.canonical(grant)
    grant_path = FIX / "generated-native-execution-grant.json"
    grant_path.write_bytes(grant_raw)
    sign_fixture("generated-native-execution-grant.json", "owner")

    result_bundle = {"source-review-attestation.json":producer_bundle["source-review-attestation.json"],"source-stage-acceptance.json":producer_bundle["source-stage-acceptance.json"],
        "generated-input-approval.json":manifest_raw, "input-review.json":review_raw,
        "owner-input-decision.json":owner_raw, "generated-native-execution-grant.json":grant_raw,
        "compilation-result.json":receipt_raw}
    (FIX / "generated-input-approval.json").write_bytes(manifest_raw)
    (FIX / "compilation-result.json").write_bytes(receipt_raw)
    result_context = copy.deepcopy(producer_context)
    result_context["bundle_root"] = str(FIX)
    result_context["producer_bundle"] = producer_bundle
    result_context["producer_context"] = producer_context
    result_context["producer_facts"] = {"operator_id":"test-operator", "outcome":"SUCCESS_ELIGIBLE_OUTPUTS",
        "exit_code":0, "completed_at":now, "sealed_at":now, "consumed":True,
        "complete_audit":True, "no_live_descendants":True, "exclusive_fresh_outputs":True,
        "inspection_authorized":True, "continuous_custody":True, "scope_observed":True}
    result_context["profiles"] = raw_profiles
    result_context["evidence_bytes"] = {**producer_context.get("evidence_bytes", {}),
        fixture_evidence_hash: fixture_evidence}
    result_context["source_facts"] = producer_context["source_facts"]
    result_context["status"].update({"now_min":now+11, "now_max":now+11,
        "clock_session_id":producer_context["status"]["clock_session_id"], "monotonic_ns":2000000000,
        "run_id":grant["run_id"]})
    return result_bundle, result_context

def sign_fixture(name, role, namespace=None, value=None):
    allowed = {x['record']:x['namespace'] for x in verify.contract['signature_bindings']}
    if name not in allowed or role not in ('owner','reviewer','rogue'): raise ValueError('closed synthetic fixture')
    path=FIX/name
    if value is not None: path.write_bytes(verify.canonical(value))
    signature=path.with_suffix('.sshsig')
    # Only disposable test files are replaced; no operational material exists here.
    for f in (signature,Path(str(path)+'.sig')):
        if f.exists(): f.unlink()
    subprocess.run([SSH,'-Y','sign','-f',str(KEYS/role),'-n',namespace or allowed[name],str(path)],
                   check=True,capture_output=True,timeout=5)
    Path(str(path)+'.sig').rename(signature)
    return path.read_bytes(),signature.read_bytes()

_SOURCE_CACHE=None
def source_fixture():
    global _SOURCE_CACHE
    if _SOURCE_CACHE is not None: return copy.deepcopy(_SOURCE_CACHE)
    base=[];blobs={}
    lines=subprocess.check_output(['git','ls-tree','-r','47d770aa099c4aae8b70dea2b862aed148b5e383'],cwd=ROOT.parent).splitlines()
    for line in lines:
        header,path=line.split(b'\t');mode,kind,oid=header.split();path=path.decode('ascii')
        raw=subprocess.check_output(['git','cat-file','blob',oid.decode('ascii')],cwd=ROOT.parent)
        blobs[path]=raw;base.append({'path':path,'mode':mode.decode('ascii'),'bytes':len(raw),'git_blob':oid.decode('ascii'),'sha256':_digest(raw)})
    current=copy.deepcopy(base)
    fixture_path=os.environ.get('P08_R3_REVIEWED_SOURCE_ARCHIVE')
    if not fixture_path:
        raise RuntimeError('P08_R3_REVIEWED_SOURCE_ARCHIVE must name the exact retained source fixture')
    fixture_bytes=Path(fixture_path).read_bytes()
    if _digest(fixture_bytes)!='e7cf02b3401c1c44d4438dd0d6ca7b0f0f6bb47b7af8f3eb3c2109d6adeef3c2':
        raise RuntimeError('reviewed source fixture archive identity mismatch')
    with tarfile.open(fileobj=io.BytesIO(fixture_bytes),mode='r:gz') as archive:
        fixture_members={m.name:m for m in archive if m.isfile()}
        fixture_source={entry['path']:archive.extractfile(next(m for n,m in fixture_members.items()
                        if n.endswith('/source/'+entry['path']))).read() for entry in verify.contract['reviewed_composition']}
        correction=archive.extractfile(next(m for n,m in fixture_members.items()
                         if n.endswith('/IDENTITY_PIN_CORRECTION.patch'))).read()
    for entry in verify.contract['reviewed_composition']:
        current.append(copy.deepcopy(entry))
        blobs[entry['path']]=fixture_source[entry['path']]
        if _digest(blobs[entry['path']])!=entry['sha256']:raise RuntimeError('reviewed fixture member mismatch')
    current.sort(key=lambda x:x['path']);previous=copy.deepcopy(current)
    old=verify.contract['historical_identity'];ip=old['path']
    # Reconstruct only synthetic fixture data in memory from the pinned archive.
    # Reviewers need no historical Git objects absent from protected main.
    oldraw=blobs[ip]
    removed=[line[1:] for line in correction.splitlines(keepends=True) if line.startswith(b'-') and not line.startswith(b'---')]
    added=[line[1:] for line in correction.splitlines(keepends=True) if line.startswith(b'+') and not line.startswith(b'+++')]
    if len(removed)!=4 or len(added)!=4:raise RuntimeError('fixture correction is not exactly four pin lines')
    for before,after in zip(removed,added):
        if oldraw.count(after)!=1:raise RuntimeError('fixture correction context mismatch')
        oldraw=oldraw.replace(after,before,1)
    if _digest(oldraw)!=old['sha256'] or verify.git_object_id('blob',oldraw)!=old['git_blob']:
        raise RuntimeError('historical fixture identity mismatch')
    previous=[{'mode':'100644',**old} if x['path']==ip else x for x in previous]
    c0tree=verify.source_tree(previous);c1tree=verify.source_tree(current)
    def commit(tree,parent):
        return ('tree '+tree+'\nparent '+parent+'\nauthor Synthetic <synthetic@invalid> 1 +0000\ncommitter Synthetic <synthetic@invalid> 1 +0000\n\nSYNTHETIC SOURCE TEST ONLY\n').encode('ascii')
    c0raw=commit(c0tree,'47d770aa099c4aae8b70dea2b862aed148b5e383');c0=verify.git_object_id('commit',c0raw)
    c1raw=commit(c1tree,c0);c1=verify.git_object_id('commit',c1raw)
    _SOURCE_CACHE={'repository_id':1368436395,'current_main_commit':'47d770aa099c4aae8b70dea2b862aed148b5e383',
        'current_main_tree':'6afa28cc5386944ec196e077f2c1f576dd8822e7','commit':c1,'tree':c1tree,
        'base_commit':c0,'base_tree':c0tree,'parent':c0,'protected_inventory':base,'base_inventory':previous,
        'observed_entries':current,'source_bytes':blobs,'c0_commit_raw':c0raw,'c1_commit_raw':c1raw,
        'base_identity_bytes':oldraw}
    return copy.deepcopy(_SOURCE_CACHE)


def source_review_fixture(facts,profile,now):
    index=[];stream=io.BytesIO()
    with tarfile.open(fileobj=stream,mode='w:gz') as archive:
        data=b'SYNTHETIC REVIEW ONLY; no operational approval'
        item=tarfile.TarInfo('REVIEW.txt');item.size=len(data);item.mode=0o600;item.mtime=0
        archive.addfile(item,io.BytesIO(data))
        index.append({'path':'REVIEW.txt','kind':'regular','mode':'0600','bytes':len(data),'sha256':_digest(data)})
    archive=stream.getvalue();indexraw=verify.canonical(index)
    t03=[x for x in verify.contract['reviewed_composition'] if x['path'].endswith(('codec.ex','codec_test.exs','codec.rs','codec_test.rs'))]
    attestation=_default_record('source-review-attestation.json')
    attestation.update({'review_id':'9'*32,'reviewer_id':'test-reviewer','issued_at':now-200,'expires_at':now+3600,
        'trust_profile_sha256':_digest(verify.canonical(profile)),'t03_inventory_sha256':_digest(verify.canonical(t03)),
        'c0_commit':facts['base_commit'],'c0_tree':facts['base_tree'],'c1_commit':facts['commit'],'c1_tree':facts['tree'],
        'c0_inventory_sha256':_digest(verify.canonical(facts['base_inventory'])),
        'c1_inventory_sha256':_digest(verify.canonical(facts['observed_entries'])),
        'archive_sha256':_digest(archive),'archive_bytes':len(archive),'archive_inventory_sha256':_digest(indexraw)})
    raw,sig=sign_fixture('source-review-attestation.json','reviewer',value=attestation)
    authority={'schema':'p08-source-review-authority-1','repository_id':1368436395,
        'trust_profile_sha256':_digest(verify.canonical(profile)),'review_attestation_sha256':_digest(raw),
        'review_signature_sha256':_digest(sig),'review_archive_sha256':_digest(archive),
        'reviewer_fingerprint':next(k['fingerprint'] for k in profile['keys'] if k['role']=='independent-reviewer'),
        'not_before':now-1000,'expires_at':now+4000,'authority_id':'8'*32}
    fields={'source_commit':facts['base_commit'],'source_tree':facts['base_tree'],'source_parent':'47d770aa099c4aae8b70dea2b862aed148b5e383',
        'c1_commit':facts['commit'],'c1_tree':facts['tree'],'independent_review_sha256':_digest(raw),
        'source_review_signature_sha256':_digest(sig),'review_archive_sha256':_digest(archive)}
    return fields,raw,sig,authority,{_digest(raw):raw,_digest(archive):archive,_digest(indexraw):indexraw}

class SourceContractTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global OUT,FIX,KEYS
        cls.temp=tempfile.TemporaryDirectory(prefix='p08-r3-synthetic-')
        OUT=Path(cls.temp.name);OUT.chmod(0o700);FIX=OUT/'fixtures';KEYS=OUT/'keys';KEYS.mkdir(mode=0o700)
        for name in ('owner','reviewer','rogue'):
            subprocess.run([SSH,'-t','ed25519','-N','','-C','SYNTHETIC-NONOPERATIONAL','-f',str(KEYS/name)],
                           check=True,capture_output=True,timeout=5)
    @classmethod
    def tearDownClass(cls): cls.temp.cleanup()
    def setUp(self): self.bundle,self.context=make_fixture()
    def refuses(self,code,operation,*args):
        with self.assertRaises(gate.Refusal) as caught: operation(*args)
        if code is not None:self.assertEqual(code,caught.exception.code)
        return caught.exception
    def test_complete_r3_chain_has_exact_legacy_result_contract(self):
        result=verify.verify_bundle(self.bundle,self.context)
        self.assertEqual(set(result),{'records','roles','profile_sha256','command','execution_profile','inventory','profiles','action_observation','manifest','grant'})
        self.assertEqual('p08-native-execution-grant-3',result['grant']['schema'])
    def test_review_authority_is_required_before_any_grant(self):
        self.context.pop('source_review_authority')
        error=self.refuses('SOURCE_REVIEW_AUTHORITY_MISSING',verify.verify_bundle,self.bundle,self.context)
        self.assertIsNone(error.authenticated_grant)
    def test_source_movement_refuses_before_grant_authentication(self):
        self.context['source_facts']['current_main_commit']='a'*40
        error=self.refuses('SOURCE_MOVEMENT_REQUIRES_REVIEW',verify.verify_bundle,self.bundle,self.context)
        self.assertIsNone(error.authenticated_grant)



    def test_closed_r3_records_and_all_r2_schemas_are_isolated(self):
        for name,raw in self.bundle.items():
            record=json.loads(raw)
            self.assertEqual(record,verify.parse_record(raw,name))
            with self.subTest(record=name):
                for mutation in ('missing','unknown','duplicate','r2_schema'):
                    changed=dict(record)
                    if mutation=='missing': changed.pop(next(iter(changed)))
                    if mutation=='unknown':changed['accepted']='PASS'
                    if mutation=='r2_schema':changed['schema']=gate.verify.SCHEMAS.get(name,{'properties':{'schema':{'const':'unknown'}}})['properties']['schema']['const']
                    if mutation=='duplicate':
                        field=next(iter(record));value=verify.canonical(record[field]);data=raw[:-1]+b','+json.dumps(field).encode()+b':'+value+b'}'
                    else:data=verify.canonical(changed)
                    self.refuses('FORMAT_INVALID',verify.parse_record,data,name)
    def test_r2_parser_still_accepts_exact_original_closed_schema(self):
        for name,schema in gate.verify.SCHEMAS.items():
            record={}
            for field,spec in schema['properties'].items():
                if 'const' in spec:record[field]=spec['const']
                elif 'enum' in spec:record[field]=spec['enum'][0]
                elif spec.get('type')=='integer':record[field]=spec.get('minimum',1)
                else:
                    import re
                    match=re.fullmatch(r'\^\[0-9a-f\]\{(\d+)\}\$',spec.get('pattern',''))
                    record[field]='a'*int(match[1]) if match else 'synthetic'
            raw=gate.verify.canonical(record)
            self.assertEqual(record,gate.verify.parse_record(raw,name))
            self.refuses('FORMAT_INVALID',verify.parse_record,raw,name)
    def test_unapproved_review_binding_and_self_supplied_bundle_authority_refuse(self):
        authority=self.context.pop('source_review_authority')
        self.bundle['source_review_authority']=verify.canonical(authority)
        error=self.refuses('SOURCE_REVIEW_AUTHORITY_MISSING',verify.verify_bundle,self.bundle,self.context)
        self.assertIsNone(error.authenticated_grant)
        self.context['source_review_authority']=authority
        self.context['accepted_source_review_authority_sha256']='f'*64
        error=self.refuses('SOURCE_REVIEW_AUTHORITY_UNAUTHENTICATED',verify.verify_bundle,self.bundle,self.context)
        self.assertIsNone(error.authenticated_grant)
    def test_review_authority_stale_revoked_wrong_repo_or_key_refuses(self):
        cases=[('expires_at',1700000005,'SOURCE_REVIEW_AUTHORITY_STALE'),
               ('repository_id',1,'SOURCE_REVIEW_AUTHORITY_MISMATCH'),
               ('reviewer_fingerprint','f'*64,'SOURCE_REVIEW_AUTHORITY_MISMATCH')]
        for field,value,reason in cases:
            context=copy.deepcopy(self.context);context['source_review_authority'][field]=value
            context['accepted_source_review_authority_sha256']=_digest(verify.canonical(context['source_review_authority']))
            self.assertIsNone(self.refuses(reason,verify.verify_bundle,self.bundle,context).authenticated_grant)
        self.context['status']['revoked_ids']=[self.context['source_review_authority']['authority_id']]
        self.refuses('SOURCE_REVIEW_AUTHORITY_REVOKED',verify.verify_bundle,self.bundle,self.context)
    def test_source_review_signature_and_archive_substitution_refuse(self):
        authority=self.context['source_review_authority'];path=FIX/'source-review-attestation.sshsig'
        sig=path.read_bytes();path.write_bytes(sig[:-8]+b'INVALID!')
        self.assertIsNone(self.refuses('SOURCE_REVIEW_UNAUTHENTICATED',verify.verify_bundle,self.bundle,self.context).authenticated_grant)
        path.write_bytes(sig)
        self.context['evidence_bytes'][authority['review_archive_sha256']]=b'changed archive'
        self.refuses('SOURCE_REVIEW_ARCHIVE_MISMATCH',verify.verify_bundle,self.bundle,self.context)
    def test_wrong_signature_namespace_and_owner_signed_review_refuse(self):
        raw=self.bundle['source-review-attestation.json']
        for role,namespace in [('reviewer','symphony.p08.input-review.v1'),('owner','symphony.p08.r3.source-review.v1')]:
            with self.subTest(role=role):
                _,sig=sign_fixture('source-review-attestation.json',role,namespace=namespace)
                authority=self.context['source_review_authority'];authority['review_signature_sha256']=_digest(sig)
                self.context['accepted_source_review_authority_sha256']=_digest(verify.canonical(authority))
                error=self.refuses('SIGNATURE_INVALID' if role=='reviewer' else 'ROLE_MISMATCH',verify.verify_bundle,self.bundle,self.context)
                self.assertIsNone(error.authenticated_grant)
    def test_issuer_reviewer_keys_must_be_distinct(self):
        profile=copy.deepcopy(self.context['profile'])
        owner,reviewer=profile['keys']
        reviewer['public_key']=owner['public_key'];reviewer['fingerprint']=owner['fingerprint']
        self.refuses('ROLE_MISMATCH',verify.validate_enrollment,profile,1700000000)
    def test_ancestry_projection_inventory_blob_and_pin_changes_refuse(self):
        source=verify.parse_record(self.bundle['source-stage-acceptance.json'],'source-stage-acceptance.json')
        review=json.loads(self.bundle['source-review-attestation.json'])
        mutations=[lambda f:f.update(c1_commit_raw=b'tree '+f['tree'].encode()+b'\n\n'),
            lambda f:f.update(base_commit='600ed38175fde5ef9c81c38c0d47693ce6eba385'),
            lambda f:f['observed_entries'].pop(),
            lambda f:f['base_inventory'].append(copy.deepcopy(f['base_inventory'][0])),
            lambda f:f['source_bytes'].update({next(iter(f['source_bytes'])):b'substitution'}),
            lambda f:f.update(base_identity_bytes=b'changed historical test'),
            lambda f:f.update(repository_id=1)]
        for mutate in mutations:
            facts=copy.deepcopy(self.context['source_facts']);mutate(facts)
            self.refuses(None,verify.verify_source_lineage,source,review,facts)
    def test_unknown_profile_schema_cannot_use_r3_directly(self):
        context=copy.deepcopy(self.context);context['profile']['record_family']='D02_R2'
        context['accepted_profile_sha256']=_digest(verify.canonical(context['profile']))
        self.refuses('VERIFIER_FAMILY_UNAPPROVED',verify.verify_bundle,self.bundle,context)
    def test_bad_grant_signature_never_exposes_authenticated_grant(self):
        sign_fixture('native-execution-grant.json','rogue')
        error=self.refuses('SIGNER_UNAUTHORIZED',verify.verify_bundle,self.bundle,self.context)
        self.assertIsNone(error.authenticated_grant)
    def test_late_refusal_retains_authenticated_grant(self):
        context=copy.deepcopy(self.context)
        context['source_facts']['inventory_sha256']=json.loads(self.bundle['build-input-approval.json'])['source_inventory_sha256']
        # Raw input closure inconsistency is detected after all S/R/O/G signatures.
        context['profiles']['f'*64]=b'not the declared digest'
        error=self.refuses('CHAIN_MISMATCH',verify.verify_bundle,self.bundle,context)
        self.assertEqual('c'*32,error.authenticated_grant['grant_id'])
    def test_restart_rechecks_review_and_current_source(self):
        verify.verify_bundle(self.bundle,self.context)
        restarted=gate._r3_module.CurrentSourceVerifier(gate.verify)
        context=copy.deepcopy(self.context);context.pop('accepted_source_review_authority_sha256')
        error=self.refuses('SOURCE_REVIEW_AUTHORITY_UNAUTHENTICATED',restarted.verify_bundle,self.bundle,context)
        self.assertIsNone(error.authenticated_grant)
    def test_generated_chain_requires_same_family_recursively(self):
        bundle,context=make_generated_fixture()
        result=verify.verify_bundle(bundle,context)
        self.assertEqual('p08-generated-native-grant-2',result['grant']['schema'])
        producer=json.loads(context['producer_bundle']['build-input-approval.json'])
        producer['schema']='p08-build-input-approval-1'
        context['producer_bundle']['build-input-approval.json']=verify.canonical(producer)
        error=self.refuses('FORMAT_INVALID',verify.verify_bundle,bundle,context)
        self.assertEqual('4'*32,error.authenticated_grant['grant_id'])
    def test_source_review_archive_rejects_duplicate_unsafe_missing_and_link_members(self):
        for kind in ('duplicate','parent','absolute','link','extra','missing','directory'):
            stream=io.BytesIO();index=[]
            with tarfile.open(fileobj=stream,mode='w') as archive:
                name={'parent':'../escape','absolute':'/escape'}.get(kind,'review.txt')
                member=tarfile.TarInfo(name);member.size=1;member.mode=0o600
                if kind=='link':member.type=tarfile.SYMTYPE;member.linkname='/escape';member.size=0
                if kind=='directory':member.type=tarfile.DIRTYPE;member.size=0
                archive.addfile(member,io.BytesIO(b'x'))
                if kind=='duplicate':archive.addfile(member,io.BytesIO(b'x'))
                if kind!='extra':index.append({'path':name,'kind':'regular','mode':'0600','bytes':1,'sha256':_digest(b'x')})
                if kind=='missing':index.append({'path':'unseen','kind':'regular','mode':'0600','bytes':1,'sha256':_digest(b'x')})
            self.refuses('SOURCE_REVIEW_ARCHIVE_MISMATCH',verify._verify_review_archive,stream.getvalue(),verify.canonical(index))
    def test_policy_a_constraints_are_unchanged(self):
        profile=json.loads(self.context['profiles'][json.loads(self.bundle['build-input-approval.json'])['rust_provenance_profile_sha256']])
        self.assertEqual(gate.verify.PROFILE_RULES['profiles']['rust-provenance-profile'],verify.PROFILE_RULES['profiles']['rust-provenance-profile'])
        profile['archives'][0]['sha256']='f'*64
        self.refuses('PROVENANCE_INVALID',verify._validate_profile,profile,verify.PROFILE_RULES['profiles']['rust-provenance-profile'],'rust-provenance-profile')

    def test_r2_real_signature_preserves_original_namespace_and_rejects_r3(self):
        profile=copy.deepcopy(self.context['profile']);profile['schema']='p08-verifier-enrollment-2';profile.pop('record_family')
        namespaces={'project-owner-issuer':sorted(('symphony.p08.source-stage.v1','symphony.p08.input-owner.v1','symphony.p08.native-grant.v1')),
                    'independent-reviewer':sorted(('symphony.p08.input-review.v1','symphony.p08.build-result.v1'))}
        for key in profile['keys']:key['namespaces']=namespaces[key['role']]
        for role,leaf in [('project-owner-issuer','owner'),('independent-reviewer','reviewer')]:
            key=next(k for k in profile['keys'] if k['role']==role)
            (FIX/'signers'/leaf).write_text(key['principal']+' namespaces="'+','.join(key['namespaces'])+'" '+key['public_key']+'\n',encoding='ascii')
        record={}
        for field,prop in gate.verify.SCHEMAS['source-stage-acceptance.json']['properties'].items():
            import re
            match=re.fullmatch(r'\^\[0-9a-f\]\{(\d+)\}\$',prop.get('pattern',''))
            record[field]=prop['const'] if 'const' in prop else (1700000000 if field=='issued_at' else
                'test-owner' if field=='issuer_id' else 'a'*int(match[1]) if match else 'a'*64)
        raw=gate.verify.canonical(record)
        sign_fixture('source-stage-acceptance.json','owner',namespace='symphony.p08.source-stage.v1',value=record)
        args=('source-stage-acceptance.json',raw,FIX/'source-stage-acceptance.sshsig',profile,1700000000,FIX/'signers')
        self.assertEqual(record,gate.verify.verify_signature(*args))
        sign_fixture('source-stage-acceptance.json','owner',namespace='symphony.p08.r3.source-stage.v3',value=record)
        self.refuses('SIGNATURE_INVALID',gate.verify.verify_signature,*args)

    def test_missing_grant_and_cross_family_grant_refuse_before_authentication(self):
        bundle=dict(self.bundle);bundle.pop('native-execution-grant.json')
        self.assertIsNone(self.refuses('APPROVAL_MISSING',verify.verify_bundle,bundle,self.context).authenticated_grant)
        bundle=dict(self.bundle);grant=json.loads(bundle['native-execution-grant.json']);grant['schema']='p08-native-execution-grant-2'
        bundle['native-execution-grant.json']=verify.canonical(grant)
        self.assertIsNone(self.refuses('FORMAT_INVALID',verify.verify_bundle,bundle,self.context).authenticated_grant)

    def test_expired_approval_is_authenticated_terminal_refusal(self):
        context=copy.deepcopy(self.context);context['status'].update(now_min=1700000600,now_max=1700000600)
        error=self.refuses('APPROVAL_STALE',verify.verify_bundle,self.bundle,context)
        self.assertEqual('c'*32,error.authenticated_grant['grant_id'])
    def _registered(self):
        path=Path(tempfile.mkdtemp(prefix='register-',dir=OUT))
        (path/'epoch.json').write_bytes(gate.verify.canonical({'epoch':1}));(path/'epoch.json').chmod(0o600)
        return path

    def _signature_failure_lifecycle(self, exception_type, late):
        bundle,context=make_generated_fixture() if late else (self.bundle,self.context)
        name='generated-native-execution-grant.json' if late else 'native-execution-grant.json'
        grant=json.loads(bundle[name])
        identity={key:grant[key] for key in ('grant_id','run_id','nonce','authorization_scope','trust_epoch')}
        signature=Path(context['bundle_root'])/('compilation-result.sshsig' if late else 'native-execution-grant.sshsig')
        code='SIGNATURE_VERIFIER_TIMEOUT' if exception_type is subprocess.TimeoutExpired else 'SIGNATURE_VERIFIER_UNAVAILABLE'
        expected_code='COMPILATION_RECEIPT_UNAUTHENTICATED' if late else code
        path=self._registered()
        before={p.name:p.read_bytes() for p in path.iterdir()}
        real_run=subprocess.run
        failures=[]

        def fail_verifier(argv,*args,**kwargs):
            if argv[:3]==[SSH,'-Y','verify'] and Path(argv[argv.index('-s')+1])==signature:
                failures.append(str(signature))
                if exception_type is subprocess.TimeoutExpired:
                    raise subprocess.TimeoutExpired(argv,kwargs['timeout'])
                raise OSError('synthetic signature executable unavailable')
            return real_run(argv,*args,**kwargs)

        observer=mock.Mock(side_effect=AssertionError('refused input must never reach execution admission'))
        with mock.patch.object(gate._r3_module.subprocess,'run',side_effect=fail_verifier):
            error=self.refuses(expected_code,verify.verify_bundle,bundle,context)
            self.assertEqual(identity if late else None,error.authenticated_grant)
            typed=error.__cause__ if late else error
            self.assertIsInstance(typed,gate.Refusal)
            self.assertEqual(code,typed.code)
            self.assertIsInstance(typed.__cause__,exception_type)
            with mock.patch.object(gate.os,'fsync',wraps=os.fsync) as synced:
                error=self.refuses(expected_code,gate.execute,bundle,context,path,
                                   lambda:copy.deepcopy(context['status']),observer)
            self.assertEqual(identity if late else None,error.authenticated_grant)
            self.assertGreaterEqual(len(failures),2)
            if late:
                self.assertGreaterEqual(synced.call_count,8)
                markers=[json.loads((path/leaf).read_bytes()) for leaf in gate.OneUseRegister._identities(grant)]
                expected={key:grant[key] for key in ('grant_id','run_id','nonce')}
                expected.update(epoch=grant['trust_epoch'],state='REFUSED')
                self.assertEqual([expected]*3,markers)
                events=[json.loads(p.read_bytes()) for p in path.glob('event-*.json')]
                self.assertEqual([{'details':expected_code,'epoch':grant['trust_epoch'],
                                  'grant_id':grant['grant_id'],'state':'REFUSED'}],events)
                # A fresh register instance must deny each identity independently.
                for field in ('grant_id','run_id','nonce'):
                    changed=dict(grant,grant_id='1'*32,run_id='2'*32,nonce='3'*64)
                    changed[field]=grant[field]
                    with gate.OneUseRegister(path,grant['trust_epoch']) as register:
                        self.refuses('GRANT_REPLAY',register.consume,changed)
                self.refuses('GRANT_REPLAY',gate.execute,bundle,context,path,
                             lambda:copy.deepcopy(context['status']),observer)
            else:
                self.assertEqual(0,synced.call_count)
                self.assertEqual(before,{p.name:p.read_bytes() for p in path.iterdir()})
        observer.assert_not_called()
        # Removing the fault restores real signature verification, not cached PASS.
        self.assertEqual(grant,verify.verify_bundle(bundle,context)['grant'])

    def test_signature_timeout_before_grant_leaves_register_unchanged(self):
        self._signature_failure_lifecycle(subprocess.TimeoutExpired,False)

    def test_signature_oserror_before_grant_leaves_register_unchanged(self):
        self._signature_failure_lifecycle(OSError,False)

    def test_signature_timeout_after_grant_durably_refuses_and_denies_replay(self):
        self._signature_failure_lifecycle(subprocess.TimeoutExpired,True)

    def test_signature_oserror_after_grant_durably_refuses_and_denies_replay(self):
        self._signature_failure_lifecycle(OSError,True)

    def test_signature_boundary_does_not_mask_programming_errors(self):
        path=self._registered()
        before={p.name:p.read_bytes() for p in path.iterdir()}
        with mock.patch.object(gate._r3_module.subprocess,'run',side_effect=RuntimeError('synthetic programming defect')):
            with self.assertRaisesRegex(RuntimeError,'synthetic programming defect'):
                gate.execute(self.bundle,self.context,path,lambda:copy.deepcopy(self.context['status']),lambda _:None)
        self.assertEqual(before,{p.name:p.read_bytes() for p in path.iterdir()})

    def test_shared_register_denies_cross_version_grant_run_nonce_reuse(self):
        path=self._registered();grant=json.loads(self.bundle['native-execution-grant.json'])
        with gate.OneUseRegister(path,1) as register:register.consume(grant,'REFUSED')
        for field in ('grant_id','run_id','nonce'):
            changed=dict(grant,grant_id='1'*32,run_id='2'*32,nonce='3'*64);changed[field]=grant[field]
            with gate.OneUseRegister(path,1) as register:self.refuses('GRANT_REPLAY',register.consume,changed)
    def test_gate_burns_authenticated_late_refusal_but_not_early_review_failure(self):
        path=self._registered();context=copy.deepcopy(self.context);context.pop('source_review_authority')
        self.refuses('SOURCE_REVIEW_AUTHORITY_MISSING',gate.execute,self.bundle,context,path,
                     lambda:copy.deepcopy(context['status']),lambda _:None)
        self.assertFalse(list(path.glob('grant-*.json')))
        context=copy.deepcopy(self.context);context['profiles']['f'*64]=b'wrong digest'
        self.refuses('CHAIN_MISMATCH',gate.execute,self.bundle,context,path,
                     lambda:copy.deepcopy(context['status']),lambda _:None)
        records=[json.loads(p.read_bytes()) for p in path.glob('grant-*.json')]
        self.assertEqual(['REFUSED'],[r['state'] for r in records])
    def test_r3_finite_sentinel_uses_shared_gate_and_cannot_replay(self):
        checked=verify.verify_bundle(self.bundle,self.context);path=self._registered()
        observed={k:v for k,v in checked['grant'].items() if k.startswith('observed_') or k in
                  ('grant_id','run_id','nonce','source_commit','source_tree','command_profile_sha256','authorization_scope')}
        observed.update(evidence_sha256=checked['action_observation']['evidence_sha256'],
                        clock_session_id=self.context['status']['clock_session_id'],monotonic_ns=self.context['status']['monotonic_ns'])
        status=lambda:copy.deepcopy(self.context['status'])
        result=gate.execute(self.bundle,self.context,path,status,lambda _:copy.deepcopy(observed))
        self.assertEqual(('COMPLETED',0),(result['state'],result['returncode']))
        self.refuses('GRANT_REPLAY',gate.execute,self.bundle,self.context,path,status,lambda _:copy.deepcopy(observed))




class LegacyR2CanonicalRegressions(unittest.TestCase):

    def test_canonical_emits_ascii_sorted_minimal_json_without_newline(self):
            self.assertEqual(gate.verify.canonical({"z": 2, "a": "ok"}), b'{"a":"ok","z":2}')

    def test_parser_rejects_noncanonical_whitespace(self):
            with self.assertRaises(gate.verify.Refusal) as raised:
                gate.verify.parse_record(b'{ "schema":"p08-source-stage-acceptance-1" }',
                                    "source-stage-acceptance.json")
            self.assertEqual(raised.exception.code, "FORMAT_INVALID")

    def test_parser_rejects_duplicate_fields_before_mapping(self):
            with self.assertRaises(gate.verify.Refusal) as raised:
                gate.verify.parse_record(b'{"schema":"x","schema":"y"}', "source-stage-acceptance.json")
            self.assertEqual(raised.exception.code, "FORMAT_INVALID")

    def test_parser_rejects_booleans_and_unicode(self):
            for raw in (b'{"x":true}', '{"x":"é"}'.encode("utf-8")):
                with self.subTest(raw=raw), self.assertRaises(gate.verify.Refusal) as raised:
                    gate.verify.parse_record(raw, "source-stage-acceptance.json")
                self.assertEqual(raised.exception.code, "FORMAT_INVALID")

    def test_self_declared_bundle_cannot_supply_trust_context(self):
            with self.assertRaises(gate.verify.Refusal) as raised:
                gate.verify.verify_bundle({}, {})
            self.assertEqual(raised.exception.code, "STATUS_INVALID")


def checked_action():
    grant = {"grant_id": "1" * 32, "run_id": "2" * 32, "nonce": "3" * 64,
             "trust_epoch": 7, "issued_at": 900, "not_before": 900, "expires_at": 1800,
             "max_duration_s": 2, "source_commit": "4" * 40, "source_tree": "5" * 40,
             "command_profile_sha256": "6" * 64, "authorization_scope": "BUILD_ONLY",
             "observed_execution_profile_sha256": "7" * 64}
    status = {"now_min": 1000, "now_max": 1000, "trust_epoch": 7,
              "clock_session_id": "8" * 32, "monotonic_ns": 120_000_000_000,
              "enrollment_sha256": "9" * 64, "current_decisions_sha256": "a" * 64,
              "revocations_sha256": "b" * 64, "operator_id": "test-operator", "revoked_ids": []}
    report = {"schema": "p08-action-observation-1", "purpose": "ACTION_PREFLIGHT_ONLY",
              "clock_session_id": status["clock_session_id"], "completed_monotonic_ns": 100_000_000_000,
              "evidence_sha256": "c" * 64}
    observed = dict(grant, evidence_sha256=report["evidence_sha256"],
                    clock_session_id=status["clock_session_id"], monotonic_ns=status["monotonic_ns"])
    checked = {"grant": grant, "records": {"G": grant}, "roles": {
        "project-owner-issuer": {"not_before": 800, "expires_at": 1900},
        "independent-reviewer": {"not_before": 800, "expires_at": 1900}},
        "action_observation": report, "external_status": status}
    return checked, status, observed

class LegacyR2GateRegressions(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global OUT
        cls.temp=tempfile.TemporaryDirectory(prefix='.p08-r2-gate-replay-',dir=REPO)
        OUT=Path(cls.temp.name);(OUT/'tmp').mkdir();(OUT/'logs').mkdir()
    @classmethod
    def tearDownClass(cls):cls.temp.cleanup()
    def setUp(self):
        self.case_observations=[]
        self.temp=tempfile.TemporaryDirectory(prefix='gate-',dir=OUT/'tmp')
        self.root=Path(self.temp.name);self.root.chmod(0o700)
        epoch=self.root/'epoch.json';epoch.write_bytes(gate.verify.canonical({'epoch':7}));epoch.chmod(0o600)
        self.checked,self.status,self.observed=checked_action()
    def tearDown(self):self.temp.cleanup()

    def test_family_selection_uses_only_accepted_installed_profile(self):
            # Legacy enrollment bytes need no new field or rewrite to retain R2.
            profile = {"schema": "p08-verifier-enrollment-2"}
            context = {"profile": profile,
                       "accepted_profile_sha256": gate.verify.sha256(gate.verify.canonical(profile))}
            self.assertIs(gate.verify, gate.select_verifier(context))
            original_verify, original_refusal = gate.verify, gate.Refusal
            context["accepted_profile_sha256"] = "f" * 64
            self.refuses("VERIFIER_FAMILY_UNAPPROVED", gate.select_verifier, context)
            self.assertIs(original_verify, gate.verify)
            self.assertIs(original_refusal, gate.Refusal)

    def refuses(self, code, function, *args, **kwargs):
            with self.assertRaises(gate.Refusal) as raised:
                function(*args, **kwargs)
            self.case_observations.append({'expected':code,'actual':raised.exception.code})
            self.assertEqual(code, raised.exception.code)
            return raised.exception

    @staticmethod

    def _history_record(grant=None, state="CONSUMED"):
            grant = grant or checked_action()[0]["grant"]
            return {"epoch": 7, "grant_id": grant["grant_id"], "nonce": grant["nonce"],
                    "run_id": grant["run_id"], "state": state}

    def _write_history(self, directory, role, record, identifier=None, raw=None):
            identifier = identifier or record["nonce" if role == "nonce" else role + "_id"]
            name = role + "-" + identifier + ".json"
            path = directory / name
            path.write_bytes(gate.verify.canonical(record) if raw is None else raw)
            path.chmod(0o600)
            return path

    @staticmethod

    def _history_snapshot(directory):
            snapshot = {}
            for path in directory.iterdir():
                info = path.lstat()
                if not stat.S_ISREG(info.st_mode):
                    raise AssertionError("unexpected nonregular history fixture")
                snapshot[path.name] = (info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode), path.read_bytes())
            return snapshot

    def _assert_invalid_history(self, directory, label, candidate=None):
            checked, context, status, observed = self._execution_context()
            if candidate is not None:
                checked["grant"] = candidate
                checked["records"]["G"] = candidate
                observed.update({key: candidate[key] for key in ("grant_id", "run_id", "nonce")})
            with gate.OneUseRegister(directory, 7):
                before = self._history_snapshot(directory)
            for entry in ("consume", "execute"):
                with self.subTest(history=label, entry=entry), \
                        mock.patch.object(gate.subprocess, "Popen",
                                          side_effect=AssertionError("unexpected history launch")) as process:
                    started = time.monotonic()
                    if entry == "consume":
                        with gate.OneUseRegister(directory, 7) as register:
                            self.refuses("REGISTER_UNCERTAIN", register.consume, checked["grant"])
                    else:
                        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
                            self.refuses("REGISTER_UNCERTAIN", gate.execute, {}, context, directory,
                                         lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
                    elapsed = time.monotonic() - started
                    self.assertLess(elapsed, 1.0)
                    process.assert_not_called()
                    self.assertEqual(before, self._history_snapshot(directory))
                    self.assertFalse(list(directory.glob("event-*.json")))
                    self.case_observations.append({"history": label, "entry": entry,
                        "expected": "REGISTER_UNCERTAIN", "actual": "REGISTER_UNCERTAIN",
                        "seconds": elapsed, "history_unchanged": True, "launches": 0,
                        "directory": directory.relative_to(OUT).as_posix()})

    def test_one_use_consumption_and_replay_exact_error(self):
            with gate.OneUseRegister(self.root, 7) as register:
                register.consume(self.checked["grant"])
                self.refuses("GRANT_REPLAY", register.consume, self.checked["grant"])
            self.assertEqual(3, len(list(self.root.glob("*-*.json"))))

    def test_run_and_nonce_cannot_be_reused_under_new_grant(self):
            with gate.OneUseRegister(self.root, 7) as register:
                register.consume(self.checked["grant"])
                for key in ("grant_id", "run_id", "nonce"):
                    changed = copy.deepcopy(self.checked["grant"])
                    for other in ("grant_id", "run_id", "nonce"):
                        changed[other] = "d" * len(changed[other])
                    changed[key] = self.checked["grant"][key]
                    self.refuses("GRANT_REPLAY", register.consume, changed)

    def test_partial_transaction_burns_all_three_identities(self):
            with gate.OneUseRegister(self.root, 7) as register:
                write = register._write
                calls = 0
                def fail_second(name, record):
                    nonlocal calls
                    calls += 1
                    if calls == 2:
                        raise OSError("synthetic write failure")
                    write(name, record)
                with mock.patch.object(register, "_write", fail_second):
                    self.refuses("REGISTER_UNCERTAIN", register.consume, self.checked["grant"])
                new = dict(self.checked["grant"], grant_id="e" * 32, run_id="f" * 32)
                self.refuses("GRANT_REPLAY", register.consume, new)

    def test_crash_after_first_marker_does_not_allow_nonce_replay(self):
            pid = os.fork()
            if pid == 0:
                with gate.OneUseRegister(self.root, 7) as register:
                    write = register._write
                    def crash(name, record):
                        write(name, record)
                        os._exit(17)
                    register._write = crash
                    register.consume(self.checked["grant"])
                os._exit(99)
            _, result = os.waitpid(pid, 0)
            self.assertEqual(17, os.waitstatus_to_exitcode(result))
            with gate.OneUseRegister(self.root, 7) as register:
                self.refuses("GRANT_REPLAY", register.consume,
                             dict(self.checked["grant"], grant_id="e" * 32, run_id="f" * 32))

    def test_fsync_uncertainty_is_terminal(self):
            with gate.OneUseRegister(self.root, 7) as register:
                with mock.patch.object(gate.os, "fsync", side_effect=OSError("synthetic fsync failure")):
                    self.refuses("REGISTER_UNCERTAIN", register.consume, self.checked["grant"])
                self.refuses("GRANT_REPLAY", register.consume, self.checked["grant"])

    def test_concurrent_consumers_have_one_winner(self):
            children = []
            for _ in range(2):
                pid = os.fork()
                if pid == 0:
                    try:
                        with gate.OneUseRegister(self.root, 7) as register:
                            register.consume(self.checked["grant"])
                        os._exit(0)
                    except gate.Refusal as error:
                        os._exit(1 if error.code == "GRANT_REPLAY" else 9)
                children.append(pid)
            results = [os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]) for pid in children]
            self.assertEqual([0, 1], sorted(results))

    def test_missing_epoch_and_epoch_rollback_refuse(self):
            self.refuses("STATUS_INVALID", lambda: gate.OneUseRegister(self.root, 8).__enter__())
            (self.root / "epoch.json").unlink()
            self.refuses("REGISTER_INVALID", lambda: gate.OneUseRegister(self.root, 7).__enter__())

    def test_replaced_lock_and_malformed_prior_history_refuse(self):
            target = self.root / "elsewhere"
            target.write_bytes(b"")
            (self.root / ".lock").symlink_to(target)
            self.refuses("REGISTER_INVALID", lambda: gate.OneUseRegister(self.root, 7).__enter__())
            (self.root / ".lock").unlink()
            p = self.root / ("grant-" + "a" * 32 + ".json")
            p.write_bytes(b'{"epoch":7}')
            p.chmod(0o600)
            with gate.OneUseRegister(self.root, 7) as register:
                self.refuses("REGISTER_UNCERTAIN", register.consume, self.checked["grant"])

    def test_invalid_historical_register_records_refuse_without_mutation(self):
            candidate = dict(self.checked["grant"], grant_id="d" * 32, run_id="e" * 32,
                             nonce="f" * 64)
            malformed_cases = (
                ("unknown-state", "grant", self._history_record(state="UNRECOGNIZED_STATE"), None, None),
                ("event-state", "grant", self._history_record(state="LAUNCHED"), None, None),
                ("unhashable-state", "grant", self._history_record(state=[{}]), None, None),
                ("wrong-epoch", "grant", dict(self._history_record(), epoch=8), None, None),
                ("boolean-epoch", "grant", None, None,
                 b'{"epoch":true,"grant_id":"' + b'1' * 32 + b'","nonce":"' + b'3' * 64
                 + b'","run_id":"' + b'2' * 32 + b'","state":"CONSUMED"}'),
                ("invalid-identity", "grant", dict(self._history_record(), run_id="bad"), None, None),
                ("unknown-field", "grant", dict(self._history_record(), extra=7), None, None),
                ("missing-field", "grant", {k: v for k, v in self._history_record().items()
                                             if k != "state"}, None, None),
                ("noncanonical-bytes", "grant", self._history_record(), None,
                 gate.verify.canonical(self._history_record()) + b'\n'),
                ("scalar-json", "grant", None, None, b'7'),
                ("array-dict-json", "run", None, None, b'[{"x":1}]'),
                ("mismatched-grant-filename", "grant", self._history_record(), "c" * 32, None),
                ("mismatched-run-filename", "run", self._history_record(), "c" * 32, None),
                ("mismatched-nonce-filename", "nonce", self._history_record(), "c" * 64, None),
            )
            for label, role, record, identifier, raw in malformed_cases:
                with self.subTest(history=label):
                    scratch = Path(tempfile.mkdtemp(prefix="invalid-history-", dir=OUT / "tmp"))
                    scratch.chmod(0o700)
                    (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
                    (scratch / "epoch.json").chmod(0o600)
                    if record is not None and label.startswith("mismatched-"):
                        key = role + "_id" if role != "nonce" else "nonce"
                        record = dict(record, **{key: "9" * len(record[key])})
                    if record is None:
                        # Keep the filename canonical for each malformed JSON value.
                        record = self._history_record()
                    self._write_history(scratch, role, record, identifier, raw)
                    self._assert_invalid_history(scratch, label, candidate)

    def test_history_scan_validates_all_records_before_replay(self):
            candidate = self.checked["grant"]
            match = self._history_record(candidate)
            malformed = dict(self._history_record(), run_id="9" * 32)
            for role, record in (("grant", match), ("run", malformed)):
                self._write_history(self.root, role, record)
            self._assert_invalid_history(self.root, "history-before-replay", candidate)

            for conflict in ("shared-run", "shared-nonce", "state"):
                scratch = Path(tempfile.mkdtemp(prefix="conflicting-history-", dir=OUT / "tmp"))
                scratch.chmod(0o700)
                (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
                (scratch / "epoch.json").chmod(0o600)
                first = self._history_record(dict(self.checked["grant"], grant_id="1" * 32,
                                                   run_id="2" * 32, nonce="3" * 64))
                second_grant = dict(self.checked["grant"], grant_id="4" * 32,
                                    run_id="5" * 32, nonce="6" * 64)
                second = self._history_record(second_grant)
                if conflict == "shared-run":
                    second["run_id"] = first["run_id"]
                elif conflict == "shared-nonce":
                    second["nonce"] = first["nonce"]
                else:
                    second["grant_id"], second["run_id"], second["nonce"] = (
                        first["grant_id"], first["run_id"], first["nonce"])
                    second["state"] = "REFUSED"
                self._write_history(scratch, "grant", first)
                self._write_history(scratch, "nonce", second)
                candidate = dict(self.checked["grant"], grant_id="7" * 32,
                                 run_id="8" * 32, nonce="9" * 64)
                self._assert_invalid_history(scratch, conflict, candidate)

    def test_valid_historical_register_shapes_remain_usable(self):
            base = self.checked["grant"]
            same_role_value = "a" * 32
            same_role = dict(base, grant_id=same_role_value, run_id=same_role_value,
                             nonce="b" * 64)
            with gate.OneUseRegister(self.root, 7) as register:
                register.consume(same_role, "REFUSED")
            unrelated = dict(base, grant_id="c" * 32, run_id="d" * 32, nonce="e" * 64)
            with gate.OneUseRegister(self.root, 7) as register:
                register.consume(unrelated)
            markers = [path for path in self.root.glob("*-*.json")
                       if path.name.startswith(("grant-", "run-", "nonce-"))]
            self.assertEqual(6, len(markers))
            self.assertTrue(all(json.loads(path.read_bytes())["state"] in {"CONSUMED", "REFUSED"}
                                for path in markers))
            self.case_observations.append({"expected": "REFUSED_HISTORY_AND_SHARED_CROSS_ROLE_VALUE_ACCEPTED",
                                           "actual": "ACCEPTED"})

            scratch = Path(tempfile.mkdtemp(prefix="valid-partial-", dir=OUT / "tmp"))
            scratch.chmod(0o700)
            (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
            (scratch / "epoch.json").chmod(0o600)
            history = self._write_history(scratch, "run", self._history_record(same_role))
            original = history.read_bytes()
            with gate.OneUseRegister(scratch, 7) as register:
                register.consume(unrelated)
                for key in ("grant_id", "run_id", "nonce"):
                    attempt = dict(base, grant_id="7" * 32, run_id="8" * 32, nonce="9" * 64)
                    attempt[key] = same_role[key]
                    self.refuses("GRANT_REPLAY", register.consume, attempt)
            self.assertEqual(original, history.read_bytes())
            self.assertEqual(4, len([p for p in scratch.iterdir()
                                   if p.name.startswith(("grant-", "run-", "nonce-"))]))
            self.case_observations.append({"history": "valid-partial", "expected": "UNRELATED_ACCEPTED_REPLAY_DENIED",
                                           "actual": "UNRELATED_ACCEPTED_REPLAY_DENIED"})

    def test_execute_invalid_history_refuses_without_event_or_launch(self):
            checked, context, status, observed = self._execution_context()
            old_grant = dict(checked["grant"], grant_id="d" * 32, run_id="e" * 32,
                             nonce="f" * 64)
            malformed = dict(self._history_record(old_grant), state="UNCERTAIN")
            self._write_history(self.root, "grant", malformed)
            with gate.OneUseRegister(self.root, 7):
                before = self._history_snapshot(self.root)
            with mock.patch.object(gate.verify, "verify_bundle", return_value=checked), \
                    mock.patch.object(gate.subprocess, "Popen",
                                      side_effect=AssertionError("unexpected history launch")) as process:
                started = time.monotonic()
                self.refuses("REGISTER_UNCERTAIN", gate.execute, {}, context, self.root,
                             lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
                process.assert_not_called()
            self.assertLess(time.monotonic() - started, 1.0)
            self.assertEqual(before, self._history_snapshot(self.root))
            self.assertFalse(list(self.root.glob("event-*.json")))

    def test_exact_sixty_second_freshness_boundary(self):
            observed = dict(self.observed, monotonic_ns=160_000_000_000)
            accepted = gate.check_launch(copy.deepcopy(self.checked), copy.deepcopy(self.status), observed)
            self.case_observations.append({'predicate':'exact 60 seconds','expected':True,'actual':accepted})
            self.assertTrue(accepted)
            observed["monotonic_ns"] += 1
            self.refuses("ACTION_OBSERVATION_STALE", gate.check_launch, copy.deepcopy(self.checked),
                         copy.deepcopy(self.status), observed)

    def test_clock_session_backwards_and_unknown_refuse(self):
            for patch in ({"clock_session_id": "0" * 32}, {"monotonic_ns": 99_999_999_999},
                          {"monotonic_ns": 2**64}, {"monotonic_ns": None}):
                self.refuses("CLOCK_CONTEXT_INVALID", gate.check_launch, self.checked, self.status,
                             dict(self.observed, **patch))

    def test_current_status_requires_clock_baseline(self):
            invalid = (
                {"clock_session_id": "0" * 32},
                {"clock_session_id": None},
                {"monotonic_ns": "120000000000"},
                {"monotonic_ns": None},
                {"monotonic_ns": True},
                {"monotonic_ns": -1},
                {"monotonic_ns": 2**64},
                {"monotonic_ns": 119_999_999_999},
            )
            for patch in invalid:
                with self.subTest(patch=patch):
                    self.refuses("CLOCK_CONTEXT_INVALID", gate.check_current, self.checked,
                                 dict(self.status, **patch))
            for key in ("clock_session_id", "monotonic_ns"):
                missing = dict(self.status)
                missing.pop(key)
                with self.subTest(missing=key):
                    self.refuses("CLOCK_CONTEXT_INVALID", gate.check_current, self.checked, missing)

    def test_fifo_history_is_rejected_without_blocking_open(self):
            for prefix in ("grant", "run", "nonce"):
                scratch = Path(tempfile.mkdtemp(prefix="fifo-case-", dir=OUT / "tmp"))
                scratch.chmod(0o700)
                (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
                (scratch / "epoch.json").chmod(0o600)
                with gate.OneUseRegister(scratch, 7) as register:
                    register.consume(self.checked["grant"])
                fifo_name = prefix + "-" + "c" * (64 if prefix == "nonce" else 32) + ".json"
                os.mkfifo(scratch / fifo_name, 0o600)
                changed = dict(self.checked["grant"], grant_id="d" * 32, run_id="e" * 32,
                               nonce="f" * 64)
                real_open = gate.os.open
                guarded_opens = []

                def guarded_open(path, flags, *args, **kwargs):
                    if path == fifo_name and (flags & os.O_ACCMODE) == os.O_RDONLY:
                        guarded_opens.append(flags)
                        self.assertTrue(flags & os.O_NONBLOCK,
                                        "FIFO history opens must use O_NONBLOCK")
                    return real_open(path, flags, *args, **kwargs)

                started = time.monotonic()
                with mock.patch.object(gate.os, "open", side_effect=guarded_open):
                    with gate.OneUseRegister(scratch, 7) as register:
                        self.refuses("REGISTER_INVALID", register.consume, changed)
                self.assertTrue(guarded_opens)
                self.assertLess(time.monotonic() - started, 1.0)
                markers = list(scratch.glob("*-*.json"))
                self.assertEqual(4, len(markers))
                self.assertEqual(3, sum(stat.S_ISREG(path.lstat().st_mode) for path in markers))
                self.case_observations.append({'position': prefix, 'type': 'FIFO',
                    'expected': 'REGISTER_INVALID', 'actual': 'REGISTER_INVALID',
                    'nonblocking_open_observed': bool(guarded_opens),
                    'seconds': time.monotonic() - started, 'regular_history_entries_retained': 3})

            scratch = Path(tempfile.mkdtemp(prefix="fifo-epoch-", dir=OUT / "tmp"))
            scratch.chmod(0o700)
            os.mkfifo(scratch / "epoch.json", 0o600)
            real_open = gate.os.open
            guarded_opens = []

            def guarded_epoch_open(path, flags, *args, **kwargs):
                if path == "epoch.json" and (flags & os.O_ACCMODE) == os.O_RDONLY:
                    guarded_opens.append(flags)
                    self.assertTrue(flags & os.O_NONBLOCK,
                                    "FIFO epoch opens must use O_NONBLOCK")
                return real_open(path, flags, *args, **kwargs)

            started = time.monotonic()
            with mock.patch.object(gate.os, "open", side_effect=guarded_epoch_open):
                self.refuses("REGISTER_INVALID", lambda: gate.OneUseRegister(scratch, 7).__enter__())
            self.assertTrue(guarded_opens)
            self.assertLess(time.monotonic() - started, 1.0)
            self.case_observations.append({'position': 'epoch', 'type': 'FIFO',
                'expected': 'REGISTER_INVALID', 'actual': 'REGISTER_INVALID',
                'nonblocking_open_observed': bool(guarded_opens), 'seconds': time.monotonic() - started})

            scratch = Path(tempfile.mkdtemp(prefix="directory-history-", dir=OUT / "tmp"))
            scratch.chmod(0o700)
            (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
            (scratch / "epoch.json").chmod(0o600)
            with gate.OneUseRegister(scratch, 7) as register:
                register.consume(self.checked["grant"])
            directory_name = "run-" + "b" * 32 + ".json"
            (scratch / directory_name).mkdir(mode=0o700)
            with gate.OneUseRegister(scratch, 7) as register:
                self.refuses("REGISTER_INVALID", register.consume,
                             dict(self.checked["grant"], grant_id="d" * 32,
                                  run_id="e" * 32, nonce="f" * 64))

    def test_socket_records_refuse_with_typed_error(self):
            # AF_UNIX filesystem fixtures only. No listen, connect or traffic.
            self.assertEqual(REPO, Path.cwd())
            for position in ('epoch', 'history'):
                scratch = Path(tempfile.mkdtemp(prefix='socket-', dir=OUT / 'tmp'))
                scratch.chmod(0o700)
                if position == 'history':
                    (scratch / 'epoch.json').write_bytes(gate.verify.canonical({'epoch': 7}))
                    (scratch / 'epoch.json').chmod(0o600)
                    with gate.OneUseRegister(scratch, 7) as register:
                        register.consume(self.checked['grant'])
                name = 'epoch.json' if position == 'epoch' else 'run-' + 'c' * 32 + '.json'
                with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as fixture:
                    # Relative spelling stays below the Unix socket path bound.
                    fixture.bind((scratch / name).relative_to(REPO).as_posix())
                    started = time.monotonic()
                    if position == 'epoch':
                        self.refuses('REGISTER_INVALID', lambda: gate.OneUseRegister(scratch, 7).__enter__())
                    else:
                        with gate.OneUseRegister(scratch, 7) as register:
                            self.refuses('REGISTER_INVALID', register.consume,
                                dict(self.checked['grant'], grant_id='d' * 32, run_id='e' * 32, nonce='f' * 64))
                    elapsed = time.monotonic() - started
                    self.assertLess(elapsed, 1.0)
                    self.assertTrue(stat.S_ISSOCK((scratch / name).lstat().st_mode))
                    self.case_observations.append({'position': position, 'type': 'AF_UNIX_SOCKET',
                        'expected': 'REGISTER_INVALID', 'actual': 'REGISTER_INVALID', 'seconds': elapsed})

    def _after_launch_clock_case(self, mutation):
            checked, context, status, observed = self._execution_context(
                "import time; time.sleep(2)")
            scratch = Path(tempfile.mkdtemp(prefix="clock-case-", dir=OUT / "tmp"))
            scratch.chmod(0o700)
            (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
            (scratch / "epoch.json").chmod(0o600)
            shared_status = copy.deepcopy(status)
            calls = 0
            seen_launch = False
            mutated = False
            samples = []

            def current():
                nonlocal calls, seen_launch, mutated
                calls += 1
                launched = any(json.loads(path.read_text("ascii"))["state"] == "LAUNCHED"
                               for path in scratch.glob("event-*.json"))
                if calls > 1 and not mutated:
                    shared_status["monotonic_ns"] += 1
                if launched:
                    seen_launch = True
                    if not mutated:
                        mutation(shared_status)
                        mutated = True
                samples.append({'session': shared_status.get('clock_session_id'),
                                'monotonic_ns': shared_status.get('monotonic_ns'),
                                'after_launch': launched})
                return shared_status

            def current_observation(unused):
                return dict(observed, monotonic_ns=shared_status["monotonic_ns"])

            with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
                error = self.refuses("LEASE_TERMINATED", gate.execute, {}, context, scratch,
                                     current, current_observation)
            self.assertTrue(seen_launch)
            self.assertIsNotNone(error.__cause__)
            self.assertEqual("CLOCK_CONTEXT_INVALID", error.__cause__.code)
            self.assertLess(error.result["returncode"], 0)
            events = [json.loads(path.read_text("ascii"))
                      for path in sorted(scratch.glob("event-*.json"))]
            self.assertEqual("FAILED", events[-1]["state"])
            self.assertEqual("LEASE_TERMINATED:CLOCK_CONTEXT_INVALID", events[-1]["details"])
            markers = [path for path in scratch.glob('*.json')
                       if path.name.startswith(('grant-', 'run-', 'nonce-'))]
            self.assertEqual(3, len(markers))
            for path in markers:
                retained = json.loads(path.read_text('ascii'))
                self.assertEqual('CONSUMED', retained['state'])
                for key in ('grant_id', 'run_id', 'nonce'):
                    self.assertEqual(checked['grant'][key], retained[key])
            with gate.OneUseRegister(scratch, 7) as register:
                self.refuses("GRANT_REPLAY", register.consume, checked["grant"])
            self.case_observations.append({"expected": "CLOCK_CONTEXT_INVALID_AFTER_LAUNCH",
                                           "actual_cause": error.__cause__.code,
                                           "returncode": error.result["returncode"],
                                           "samples": samples,
                                           "clock_sample": shared_status.get("monotonic_ns"),
                                           "session": shared_status.get("clock_session_id")})

    def test_clock_context_change_after_launch_terminates(self):
            cases = (
                lambda status: status.update(clock_session_id="0" * 32),
                lambda status: status.update(clock_session_id="e" * 32),
                lambda status: status.pop("clock_session_id"),
                lambda status: status.update(clock_session_id=None),
                lambda status: status.pop("monotonic_ns"),
                lambda status: status.update(monotonic_ns=True),
                lambda status: status.update(monotonic_ns=120_000_000_001),
            )
            for mutation in cases:
                with self.subTest(mutation=mutation):
                    self._after_launch_clock_case(mutation)

    def test_advancing_clock_context_completes_finite_sentinel(self):
            checked, context, status, observed = self._execution_context("pass")
            shared_status = copy.deepcopy(status)
            samples = []

            def current():
                shared_status["monotonic_ns"] += 1
                samples.append(shared_status["monotonic_ns"])
                return shared_status

            def current_observation(unused):
                return dict(observed, monotonic_ns=shared_status["monotonic_ns"])

            with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
                result = gate.execute({}, context, self.root, current,
                                      current_observation)
            self.assertEqual("COMPLETED", result["state"])
            self.assertTrue(samples)
            self.assertTrue(all(sample > status["monotonic_ns"] for sample in samples))
            self.assertEqual(sorted(samples), samples)
            self.case_observations.append({"expected": "COMPLETED_WITH_ADVANCING_CLOCK",
                                           "actual": result["state"], "samples": samples})

    def test_entire_utc_interval_must_be_inside_validity(self):
            self.refuses("CLOCK_CONTEXT_INVALID", gate.check_current, self.checked,
                         dict(self.status, now_max=1031))
            self.refuses("APPROVAL_STALE", gate.check_current, self.checked,
                         dict(self.status, now_min=1790, now_max=1800))
            self.refuses("APPROVAL_STALE", gate.check_current, self.checked,
                         dict(self.status, now_min=899, now_max=900))

    def test_wrong_run_nonce_command_or_custody_refuses(self):
            for key in ("grant_id", "run_id", "nonce", "source_commit", "source_tree",
                        "command_profile_sha256", "authorization_scope"):
                self.refuses("ACTION_BINDING_MISMATCH", gate.check_launch, self.checked, self.status,
                             dict(self.observed, **{key: "wrong"}))
            for key in ("evidence_sha256", "observed_execution_profile_sha256"):
                self.refuses("CUSTODY_FAILURE", gate.check_launch, self.checked, self.status,
                             dict(self.observed, **{key: "d" * 64}))

    def test_status_epoch_revocation_and_conflict_refuse(self):
            for patch in ({"trust_epoch": 6}, {"revoked_ids": ["grant"]}):
                self.refuses("STATUS_INVALID", gate.check_launch, self.checked,
                             dict(self.status, **patch), self.observed)
            self.refuses("STATUS_INVALID", gate.check_launch, self.checked,
                         dict(self.status, current_decisions_sha256="f" * 64), self.observed)

    def test_terminal_refusal_is_never_retried(self):
            with gate.OneUseRegister(self.root, 7) as register:
                register.consume(self.checked["grant"], "REFUSED")
                self.refuses("GRANT_REPLAY", register.consume, self.checked["grant"])

    def test_replaced_register_is_detected_before_reservation(self):
            with gate.OneUseRegister(self.root, 7) as register:
                previous = self.root.with_name(self.root.name + '-retained')
                self.root.rename(previous)
                self.root.mkdir(mode=0o700)
                self.refuses('REGISTER_UNCERTAIN', register.consume, self.checked['grant'])

    def test_authenticated_late_verifier_refusal_burns_all_ids(self):
            refusal = gate.Refusal('ACTION_OBSERVATION_STALE', self.checked['grant'])
            profile={'schema':'p08-verifier-enrollment-2'}
            context={'profile':profile,'accepted_profile_sha256':gate.verify.sha256(gate.verify.canonical(profile))}
            with mock.patch.object(gate.verify, 'verify_bundle', side_effect=refusal), \
                    mock.patch.object(gate.subprocess, 'Popen') as process:
                self.refuses('ACTION_OBSERVATION_STALE', gate.execute, {}, context, self.root,
                             lambda: copy.deepcopy(self.status), lambda _: copy.deepcopy(self.observed))
                process.assert_not_called()
            with gate.OneUseRegister(self.root, 7) as register:
                self.refuses('GRANT_REPLAY', register.consume, self.checked['grant'])

    def test_unknown_operator_installation_has_no_cli_path(self):
            self.refuses("INDEPENDENT_OPERATOR_INSTALLATION_NOT_APPROVED", gate.main)

    def test_missing_external_policy_status_blocks_without_launch(self):
            def unavailable():
                raise gate.Refusal('PROVENANCE_STALE')
            with mock.patch.object(gate.subprocess,'Popen') as process:
                self.refuses('PROVENANCE_STALE',gate.execute,{}, {},self.root,unavailable,lambda _: {})
                process.assert_not_called()

    def _execution_context(self, code="pass"):
            checked, status, observed = checked_action()
            raw = Path("/usr/bin/python3.14").read_bytes()
            entry = {"kind": "regular", "path": "/usr/bin/python3.14", "mode": "0755",
                     "bytes": len(raw), "sha256": gate.verify.sha256(raw)}
            inventory = {"schema": "p08-input-inventory-1", "entries": [entry]}
            invraw = gate.verify.canonical(inventory)
            ref = {"id": "fixture_python", "path": entry["path"], "resolved_path": entry["path"],
                   "bytes": len(raw), "sha256": entry["sha256"], "provenance_sha256": "d" * 64,
                   "inventory_sha256": gate.verify.sha256(invraw),
                   "path_entry_sha256": gate.verify.sha256(gate.verify.canonical(entry)),
                   "resolved_entry_sha256": gate.verify.sha256(gate.verify.canonical(entry)), "symlink_chain": []}
            checked["command"] = {"executable": ref, "working_directory": str(OUT), "argv": [
                {"index": i, "value": x} for i, x in enumerate([
                    "/usr/bin/python3.14", "-I", "-S", "-B", "-c", code])]}
            checked["execution_profile"] = {"environment": [{"name": "PATH", "value": "/nonexistent"}]}
            profile = {"schema": "p08-verifier-enrollment-2"}
            context = {"status": status, "profiles": {gate.verify.sha256(invraw): invraw}, "sealed_roots": ["/usr"],
                       "profile": profile, "accepted_profile_sha256": gate.verify.sha256(gate.verify.canonical(profile))}
            return checked, context, status, observed

    def test_late_observation_burns_grant_without_launch(self):
            checked, context, status, observed = self._execution_context()
            observations = iter([observed, dict(observed, monotonic_ns=160_000_000_001)])
            with mock.patch.object(gate.verify, "verify_bundle", return_value=checked), \
                    mock.patch.object(gate.subprocess, "Popen") as process:
                self.refuses("ACTION_OBSERVATION_STALE", gate.execute, {}, context, self.root,
                             lambda: copy.deepcopy(status), lambda _: next(observations))
                process.assert_not_called()
            with gate.OneUseRegister(self.root, 7) as register:
                self.refuses("GRANT_REPLAY", register.consume, checked["grant"])

    def test_exec_failure_burns_grant_without_retry(self):
            checked, context, status, observed = self._execution_context()
            with mock.patch.object(gate.verify, "verify_bundle", return_value=checked), \
                    mock.patch.object(gate.subprocess, "Popen", side_effect=OSError("synthetic exec failure")):
                with self.assertRaises(OSError):
                    gate.execute({}, context, self.root, lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
            with gate.OneUseRegister(self.root, 7) as register:
                self.refuses("GRANT_REPLAY", register.consume, checked["grant"])

    def test_finite_nonzero_sentinel_retains_failure(self):
            checked, context, status, observed = self._execution_context("raise SystemExit(7)")
            with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
                error = self.refuses("QUALIFICATION_FAILED", gate.execute, {}, context, self.root,
                             lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
            self.assertEqual(7,error.result['returncode'])
            self.assertEqual(b'',error.result['stdout'])
            self.case_observations.append({'expected_exit':7,'actual_exit':error.result['returncode']})
            self.assertTrue(list(self.root.glob("event-*.json")))

    def test_output_reader_enforces_exact_cap_without_an_extra_process(self):
            for overflow in (False, True):
                read_fd,write_fd=os.pipe();err_read,err_write=os.pipe()
                os.write(write_fd,b'x');os.close(err_write)
                out=os.fdopen(read_fd,'rb',buffering=0);err=os.fdopen(err_read,'rb',buffering=0)
                process=mock.Mock(stdout=out,stderr=err)
                process.poll.return_value=0
                chunks=iter((b'A'*65536,b'A' if overflow else b''))
                real_read=os.read
                def read(fd,count):
                    if fd==read_fd:
                        chunk=next(chunks);self.assertLessEqual(len(chunk),count);return chunk
                    return real_read(fd,count)
                try:
                    with mock.patch.object(gate.os,'read',side_effect=read):
                        if overflow:
                            error=self.refuses('RESULT_LIMIT_EXCEEDED',gate._collect,process,self.checked,
                                lambda:copy.deepcopy(self.status),gate.time.monotonic()+1)
                            self.assertEqual(65536,len(error.output['stdout']))
                            self.assertTrue(error.output['truncated'])
                        else:
                            stdout,stderr=gate._collect(process,self.checked,lambda:copy.deepcopy(self.status),gate.time.monotonic()+1)
                            self.assertEqual(b'A'*65536,stdout);self.assertEqual(b'',stderr)
                finally:
                    os.close(write_fd);out.close();err.close()

    def test_observed_revocation_terminates_finite_sentinel(self):
            checked, context, status, observed = self._execution_context("import time; time.sleep(2)")
            calls = 0
            def current():
                nonlocal calls
                calls += 1
                return dict(status, revoked_ids=["grant"] if calls >= 4 else [])
            with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
                self.refuses("LEASE_TERMINATED", gate.execute, {}, context, self.root,
                             current, lambda _: copy.deepcopy(observed))

    def test_status_source_change_terminates_even_without_revoked_id(self):
            checked, context, status, observed = self._execution_context("import time; time.sleep(2)")
            calls = 0
            def current():
                nonlocal calls
                calls += 1
                return dict(status, current_decisions_sha256="f" * 64) if calls >= 4 else copy.deepcopy(status)
            with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
                self.refuses("LEASE_TERMINATED", gate.execute, {}, context, self.root,
                             current, lambda _: copy.deepcopy(observed))

    def test_bounded_network_or_unlisted_exec_request_is_not_admitted(self):
            # This exercises gate admission without issuing a prohibited syscall.
            # The separately reviewed seccomp runner also denies the OS effects.
            spec = importlib.util.spec_from_file_location("runner_policy", Path(__file__).with_name("p08_qualification_runner.py"))
            policy = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(policy)
            self.assertFalse(policy.permitted_argv(["/usr/bin/curl", "https://example.invalid"], "gate"))
            self.assertFalse(policy.permitted_argv(["/usr/bin/python3.14", "-I", "-S", "-B", "-c", "import socket"], "gate"))
            self.assertFalse(policy.permitted_argv(["/usr/bin/codex"], "gate"))
            self.assertFalse(policy.permitted_argv(["/usr/bin/cargo", "test"], "gate"))
            self.assertTrue(policy.permitted_argv(["/usr/bin/python3.14", "-I", "-S", "-B", "-c", "pass"], "gate"))

if __name__=="__main__":unittest.main()
