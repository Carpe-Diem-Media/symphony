"""Focused parser and trust-boundary checks for the P08 verifier."""

import importlib.util
import base64
import hashlib
import json
import os
import copy
from pathlib import Path
import subprocess
import sys
import unittest
from unittest import mock
from p08_qualification_runner import install_write_audit, fixture_bytes

install_write_audit()


spec = importlib.util.spec_from_file_location(
    "p08_authority_verify", Path(__file__).resolve().parents[1] / "p08_authority" / "verify.py")
verify = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verify)


OUT = Path(__file__).resolve().parents[2] / ".p08-authority-test-output"
FIX = OUT / "fixtures" / "verify"
KEYS = OUT / "keys"
SSH = "/usr/bin/ssh-keygen"


def _digest(raw):
    return hashlib.sha256(raw).hexdigest()


def _record_case(case_id, expected, actual):
    """Retain the observed diagnostic for a concrete qualification case."""
    log_dir = OUT / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    with (log_dir / "verify-cases.jsonl").open("a", encoding="ascii") as stream:
        stream.write(json.dumps({"id": case_id, "expected": expected, "actual": actual},
                                sort_keys=True, separators=(",", ":")) + "\n")


def _assert_case_refusal(test, case_id, expected, operation):
    try:
        operation()
    except verify.Refusal as error:
        actual = error.code
    else:
        actual = "ACCEPTED"
    _record_case(case_id, expected, actual)
    test.assertEqual(expected, actual, case_id)


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


def sign_fixture(name, role, namespace=None, value=None):
    """Sign one enumerated synthetic record with one enumerated fixture role."""
    namespaces = {
        "source-stage-acceptance.json": "symphony.p08.source-stage.v1",
        "input-review.json": "symphony.p08.input-review.v1",
        "owner-input-decision.json": "symphony.p08.input-owner.v1",
        "native-execution-grant.json": "symphony.p08.native-grant.v1",
        "generated-native-execution-grant.json": "symphony.p08.native-grant.v1",
        "compilation-result.json": "symphony.p08.build-result.v1",
    }
    if name not in verify.SIGNABLE_FIXTURES or role not in ("owner", "reviewer", "rogue"):
        raise ValueError("fixture signer or record is outside the frozen set")
    namespace = namespace or namespaces[name]
    if namespace not in {"symphony.p08.source-stage.v1", "symphony.p08.input-owner.v1",
                         "symphony.p08.native-grant.v1", "symphony.p08.input-review.v1",
                         "symphony.p08.build-result.v1"}:
        raise ValueError("fixture namespace is outside the frozen set")
    path = FIX / name
    path.write_bytes(verify.canonical(value) if value is not None else path.read_bytes())
    signature_path = path.with_suffix(".sshsig")
    if signature_path.exists():
        signature_path.unlink()
    generated_signature = Path(str(path) + ".sig")
    if generated_signature.exists():
        generated_signature.unlink()
    subprocess.run([SSH, "-Y", "sign", "-f", str(KEYS / role), "-n", namespace, str(path)],
                   check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5)
    # OpenSSH writes <input>.sig. Custody uses the closed detached-signature
    # filename expected by the verifier; this rename stays in the fixture root.
    Path(str(path) + ".sig").rename(signature_path)
    return path.read_bytes(), signature_path.read_bytes()


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
    ns = {"project-owner-issuer": sorted(["symphony.p08.source-stage.v1", "symphony.p08.input-owner.v1", "symphony.p08.native-grant.v1"]),
          "independent-reviewer": sorted(["symphony.p08.input-review.v1", "symphony.p08.build-result.v1"])}
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
    profile = {"schema": "p08-verifier-enrollment-2", "keys": keys,
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
    base_tree_bytes = fixture_bytes("BASE_SOURCE_INVENTORY")
    base_tree = json.loads(base_tree_bytes.decode("ascii"))
    base_entries = base_tree["entries"]
    source_entries = copy.deepcopy(base_entries)
    identity_path = "native/gate2/protocol/tests/locked_build_identity.rs"
    changed_entry = next(entry for entry in source_entries if entry["path"] == identity_path)
    changed_entry.update({"bytes": 1, "git_blob": "c"*40, "sha256": "d"*64})
    source_inventory = {"schema": "p08-source-inventory-1", "commit": "f"*40, "tree": "e"*40,
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
        "source_inventory_sha256": source_digest, "build_image_profile_sha256": image_digest,
        "execution_profile_sha256": execution_digest, "host_std_profile_sha256": host_digest,
        "musl_std_profile_sha256": musl_digest, "crt_profile_sha256": crt_digest,
        "toolchain_profile_sha256": tool_digest, "linker_profile_sha256": linker_digest,
        "rust_provenance_profile_sha256": rust_digest, "sbom_sha256": build_image["sbom_sha256"],
        "license_inventory_sha256": build_image["licenses_sha256"]})
    manifest["identity_test_sha256"] = changed_entry["sha256"]
    source = _default_record("source-stage-acceptance.json")
    source.update({"independent_review_sha256":evidence_hash, "issued_at": now-100, "issuer_id": "test-owner", "trust_profile_sha256": trust_hash})
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
    sign_ns = {"source-stage-acceptance.json":"symphony.p08.source-stage.v1",
        "input-review.json":"symphony.p08.input-review.v1", "owner-input-decision.json":"symphony.p08.input-owner.v1",
        "native-execution-grant.json":"symphony.p08.native-grant.v1"}
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
    source_archive = fixture_bytes("BOOTSTRAP_REVIEW_ARCHIVE")
    profiles["evidence_bytes"] = {evidence_hash: evidence_blob, _digest(source_archive): source_archive}
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

    receipt = {"schema": "p08-compilation-result-1", "receipt_id": "1"*32,
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
    manifest.update({"schema":"p08-generated-input-approval-1", "approval_id": "f"*32, "issued_at": now+8, "not_before": now+8,
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

    result_bundle = {"source-stage-acceptance.json":producer_bundle["source-stage-acceptance.json"],
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


def rechain(bundle, context, changes=None, review_change=None, action_change=None, delay=0, grant_change=None):
    """Re-sign an altered synthetic chain in the accepted acyclic order.

    Independent facts are preserved. This helper never repairs source facts or
    a producer receipt, so a mutation cannot manufacture those observations.
    """
    mname = 'generated-input-approval.json' if 'generated-input-approval.json' in bundle else 'build-input-approval.json'
    gname = 'generated-native-execution-grant.json' if mname.startswith('generated-') else 'native-execution-grant.json'
    m, r, o, g = [verify.parse_record(bundle[n], n) for n in
                  (mname, 'input-review.json', 'owner-input-decision.json', gname)]
    ro = json.loads(context['profiles'][r['review_observation_sha256']])
    ao = json.loads(context['profiles'][g['action_observation_sha256']])
    st = json.loads(context['profiles'][g['status_report_sha256']])
    if changes:
        m.update(changes)
    if delay:
        for record in (m, r, o, g):
            for field in ('issued_at', 'not_before', 'expires_at'):
                if field in record:
                    record[field] += delay
        ro['observed_at'] += delay
        for field in ('observation_started_at', 'observed_at'):
            ao[field] += delay
        st['observed_at'] += delay
        for field in ('now_min', 'now_max'):
            context['status'][field] += delay
        ao['completed_monotonic_ns'] += delay * 1_000_000_000
        context['status']['monotonic_ns'] += delay * 1_000_000_000
    def add(value):
        raw = verify.canonical(value); digest = _digest(raw)
        context['profiles'][digest] = raw
        return digest
    def observed():
        return [{'id':k.removesuffix('_sha256'), 'bytes':len(context['profiles'][v]),
                 'sha256':v, 'provenance_sha256':ro['profiles'][0]['provenance_sha256']}
                for k,v in sorted(m.items()) if (k.endswith('_profile_sha256') and k != 'trust_profile_sha256') or k == 'source_inventory_sha256']
    mraw = verify.canonical(m); mh = _digest(mraw)
    bundle[mname] = mraw; (FIX / mname).write_bytes(mraw)
    ro.update(manifest_sha256=mh, profiles=observed())
    if review_change:
        ro.update(review_change)
    r.update(manifest_sha256=mh, review_observation_sha256=add(ro))
    bundle['input-review.json'], rsig = sign_fixture('input-review.json', 'reviewer', value=r)
    o.update(manifest_sha256=mh, review_report_sha256=_digest(bundle['input-review.json']),
             review_signature_sha256=_digest(rsig))
    bundle['owner-input-decision.json'], osig = sign_fixture('owner-input-decision.json', 'owner', value=o)
    g.update(manifest_sha256=mh, review_report_sha256=_digest(bundle['input-review.json']),
             review_signature_sha256=_digest(rsig), owner_decision_sha256=_digest(bundle['owner-input-decision.json']),
             owner_signature_sha256=_digest(osig))
    if grant_change:
        g.update(grant_change)
        if 'run_id' in context['status']:
            context['status']['run_id']=g['run_id']
    for key in list(g):
        if key.startswith('observed_'):
            g[key] = m[key.removeprefix('observed_')]
    ao.update(manifest_sha256=mh, review_report_sha256=g['review_report_sha256'],
              owner_decision_sha256=g['owner_decision_sha256'], profiles=observed(),
              grant_id=g['grant_id'], run_id=g['run_id'], nonce=g['nonce'],
              command_profile_sha256=g['command_profile_sha256'], authorization_scope=g['authorization_scope'])
    if action_change:
        ao.update(action_change)
    g['action_observation_sha256'] = add(ao)
    st.update(run_id=g['run_id'], observed_at=context['status']['now_min'])
    g['status_report_sha256'] = add(st)
    bundle[gname], unused = sign_fixture(gname, 'owner', value=g)
    return bundle, context


def replace_generated(bundle, context, qchange=None, receipt_change=None):
    """Retain exact changed generated inputs and refresh their synthetic chain."""
    m = verify.parse_record(bundle['generated-input-approval.json'], 'generated-input-approval.json')
    q = json.loads(context['profiles'][m['generated_inputs_profile_sha256']])
    b = verify.parse_record(bundle['compilation-result.json'], 'compilation-result.json')
    execution = json.loads(context['profiles'][m['execution_profile_sha256']])
    def add(value):
        raw = verify.canonical(value); digest = _digest(raw); context['profiles'][digest] = raw; return digest
    if qchange:
        qchange(q)
    qhash = add(q)
    execution['commands'][0]['executable'] = q['executables'][0]
    execution['commands'][0]['argv'][0]['value'] = q['executables'][0]['path']
    execution_hash = add(execution)
    b['generated_inputs_profile_sha256'] = qhash
    if receipt_change:
        b.update(receipt_change)
    braw, bsig = sign_fixture('compilation-result.json', 'reviewer', value=b)
    bundle['compilation-result.json'] = braw
    return rechain(bundle, context, changes={'generated_inputs_profile_sha256':qhash,
        'compilation_result_sha256':_digest(braw), 'compilation_result_signature_sha256':_digest(bsig),
        'execution_profile_sha256':execution_hash},
        grant_change={'command_profile_sha256':_digest(verify.canonical(execution['commands'][0]))})


class CanonicalParsingTests(unittest.TestCase):
    def test_canonical_emits_ascii_sorted_minimal_json_without_newline(self):
        self.assertEqual(verify.canonical({"z": 2, "a": "ok"}), b'{"a":"ok","z":2}')

    def test_parser_rejects_noncanonical_whitespace(self):
        with self.assertRaises(verify.Refusal) as raised:
            verify.parse_record(b'{ "schema":"p08-source-stage-acceptance-1" }',
                                "source-stage-acceptance.json")
        self.assertEqual(raised.exception.code, "FORMAT_INVALID")

    def test_parser_rejects_duplicate_fields_before_mapping(self):
        with self.assertRaises(verify.Refusal) as raised:
            verify.parse_record(b'{"schema":"x","schema":"y"}', "source-stage-acceptance.json")
        self.assertEqual(raised.exception.code, "FORMAT_INVALID")

    def test_parser_rejects_booleans_and_unicode(self):
        for raw in (b'{"x":true}', '{"x":"é"}'.encode("utf-8")):
            with self.subTest(raw=raw), self.assertRaises(verify.Refusal) as raised:
                verify.parse_record(raw, "source-stage-acceptance.json")
            self.assertEqual(raised.exception.code, "FORMAT_INVALID")

    def test_self_declared_bundle_cannot_supply_trust_context(self):
        with self.assertRaises(verify.Refusal) as raised:
            verify.verify_bundle({}, {})
        self.assertEqual(raised.exception.code, "STATUS_INVALID")

    def test_valid_signed_s_m_r_o_g_chain_resolves_execution_profile(self):
        bundle, context = make_fixture()
        result = verify.verify_bundle(bundle, context)
        self.assertEqual(set(result["records"]), {
            "source-stage-acceptance.json", "build-input-approval.json", "input-review.json",
            "owner-input-decision.json", "native-execution-grant.json"})
        self.assertEqual(result["command"]["authorization_scope"], "BUILD_ONLY")
        self.assertEqual(result["action_observation"]["purpose"], "ACTION_PREFLIGHT_ONLY")

    def test_validly_parsed_owner_change_breaks_the_signed_chain(self):
        bundle, context = make_fixture()
        owner = verify.parse_record(bundle["owner-input-decision.json"], "owner-input-decision.json")
        owner["decision_id"] = "f" * 32
        bundle["owner-input-decision.json"] = verify.canonical(owner)
        with self.assertRaises(verify.Refusal) as raised:
            verify.verify_bundle(bundle, context)
        self.assertEqual(raised.exception.code, "CHAIN_MISMATCH")

    def test_generated_receipt_requires_separate_complete_test_chain(self):
        bundle, context = make_generated_fixture()
        result = verify.verify_bundle(bundle, context)
        self.assertEqual("BUILD_IDENTITY_TEST_EXECUTION", result["grant"]["authorization_scope"])
        self.assertNotEqual(result["manifest"]["execution_profile_sha256"],
            verify.parse_record(context["producer_bundle"]["build-input-approval.json"],
                                "build-input-approval.json")["execution_profile_sha256"])

    def test_duplicate_wire_key_cannot_fill_two_roles(self):
        bundle, context = make_fixture()
        profile = copy.deepcopy(context["profile"])
        for field in ("public_key", "fingerprint"):
            profile["keys"][1][field] = profile["keys"][0][field]
        with self.assertRaises(verify.Refusal) as raised:
            verify.validate_enrollment(profile, context["status"]["now_min"])
        self.assertEqual("ROLE_MISMATCH", raised.exception.code)

    def test_owner_signature_cannot_be_reused_for_another_purpose(self):
        bundle, context = make_fixture()
        name = "source-stage-acceptance.json"
        sign_fixture(name, "owner", namespace="symphony.p08.input-owner.v1")
        with self.assertRaises(verify.Refusal) as raised:
            verify.verify_signature(name, bundle[name], FIX / "source-stage-acceptance.sshsig",
                context["profile"], context["status"]["now_min"], context["allowed_signers_root"])
        self.assertEqual("SIGNATURE_INVALID", raised.exception.code)

    def test_production_cli_cannot_select_synthetic_authority(self):
        with self.assertRaises(verify.Refusal) as raised:
            verify.main()
        self.assertEqual("INDEPENDENT_VERIFIER_INSTALLATION_NOT_APPROVED", raised.exception.code)


class QualificationRegressionCases(unittest.TestCase):
    def test_environment_count_has_no_unaccepted_4096_limit(self):
        bundle, context = make_fixture()
        manifest = verify.parse_record(bundle['build-input-approval.json'], 'build-input-approval.json')
        execution = json.loads(context['profiles'][manifest['execution_profile_sha256']])
        execution['environment'] = [{'name': 'X' + str(i).zfill(4), 'value': ''}
                                    for i in range(4097)]
        raw = verify.canonical(execution)
        self.assertLess(len(raw), verify.MAX_PROFILE)
        parsed = verify.parse_profile(raw, 'execution-profile')
        self.assertEqual(4097, len(parsed['environment']))
        execution['environment'][0]['name'] = 'AUTH_TOKEN'
        _assert_case_refusal(self, 'VF01', 'FORMAT_INVALID',
                             lambda: verify.parse_profile(verify.canonical(execution), 'execution-profile'))

    def test_vf02_schema_valid_profile_and_inventory_boundaries(self):
        bundle,context=make_fixture();m=verify.parse_record(bundle['build-input-approval.json'],'build-input-approval.json')
        execution=json.loads(context['profiles'][m['execution_profile_sha256']])
        execution['environment']=[{'name':'X'+str(i).zfill(4),'value':''}for i in range(260)]
        gap=verify.MAX_PROFILE-len(verify.canonical(execution));width,remainder=divmod(gap,260)
        self.assertLess(width+1,4096)
        for i,entry in enumerate(execution['environment']):entry['value']='A'*(width+(i<remainder))
        raw=verify.canonical(execution);self.assertEqual(verify.MAX_PROFILE,len(raw))
        self.assertEqual('p08-execution-2',verify.parse_profile(raw,'execution-profile')['schema'])
        _record_case('VF02','ACCEPT_VALID_MAX_PROFILE','ACCEPT_VALID_MAX_PROFILE')
        execution['environment'][0]['value']+='A';raw=verify.canonical(execution)
        self.assertEqual(verify.MAX_PROFILE+1,len(raw))
        _assert_case_refusal(self,'VF02','FORMAT_INVALID',lambda:verify.parse_profile(raw,'execution-profile'))
        digest=_digest(b'')
        inventory={'schema':'p08-input-inventory-1','entries':[
            {'kind':'regular','path':'/i'+str(i).zfill(6),'mode':'0644','bytes':0,'sha256':digest}for i in range(100000)]}
        raw=verify.canonical(inventory);self.assertLess(len(raw),16*1024*1024)
        self.assertEqual(100000,len(verify.parse_profile(raw,'input-inventory')['entries']))
        _record_case('VF02','ACCEPT_VALID_MAX_ENTRY_COUNT','ACCEPT_VALID_MAX_ENTRY_COUNT')
        inventory['entries'].append({'kind':'regular','path':'/i100000','mode':'0644','bytes':0,'sha256':digest})
        raw=verify.canonical(inventory);self.assertLess(len(raw),16*1024*1024)
        _assert_case_refusal(self,'VF02','FORMAT_INVALID',lambda:verify.parse_profile(raw,'input-inventory'))
        inventory['entries']=inventory['entries'][:30000]
        gap=16*1024*1024-len(verify.canonical(inventory));width,remainder=divmod(gap,30000)
        self.assertLessEqual(width+1+len('/i000000'),512)
        for i,entry in enumerate(inventory['entries']):entry['path']+='a'*(width+(i<remainder))
        raw=verify.canonical(inventory);self.assertEqual(16*1024*1024,len(raw))
        self.assertEqual(30000,len(verify.parse_profile(raw,'input-inventory')['entries']))
        _record_case('VF02','ACCEPT_VALID_MAX_INVENTORY_BYTES','ACCEPT_VALID_MAX_INVENTORY_BYTES')
        inventory['entries'][0]['path']+='a';raw=verify.canonical(inventory)
        self.assertEqual(16*1024*1024+1,len(raw))
        _assert_case_refusal(self,'VF02','FORMAT_INVALID',lambda:verify.parse_profile(raw,'input-inventory'))

    def test_vf02_flat_schema_maximum_analysis_and_bounded_file_reads(self):
        analysis=[]
        for name,schema in verify.SCHEMAS.items():
            record=_default_record(name)
            for field,prop in schema['properties'].items():
                if 'const' in prop:continue
                if 'enum' in prop:record[field]=max(prop['enum'],key=lambda value:len(str(value)))
                elif prop.get('type')=='integer':record[field]=prop.get('maximum',2**64-1)
                elif prop.get('type')=='string' and not __import__('re').fullmatch(r'\^\[0-9a-f\]\{\d+\}\$',prop.get('pattern','')):
                    record[field]='a'*128
            raw=verify.canonical(record);verify.parse_record(raw,name)
            self.assertLess(len(raw),verify._record_limit(name))
            analysis.append({'record':name,'schema_maximum_format_bytes':len(raw),'cap':verify._record_limit(name),
                'scope':'Format witness only; intervals, signatures and approval semantics are not asserted'})
        (OUT/'logs/flat-record-boundary-analysis.json').write_text(json.dumps(analysis,sort_keys=True,indent=2))
        path=FIX/'bounded-public-input';path.write_bytes(b'public bytes')
        self.assertEqual(b'public bytes',verify._read_regular(path,12,'FORMAT_INVALID'))
        with mock.patch.object(verify.os,'read') as read:
            _assert_case_refusal(self,'VF02','FORMAT_INVALID',lambda:verify._read_regular(path,11,'FORMAT_INVALID'))
            read.assert_not_called()

    def test_vf02_exact_sshsig_input_limit(self):
        bundle,context=make_fixture();path=FIX/'source-stage-acceptance.sshsig';sig=path.read_bytes()
        ending=b'-----END SSH SIGNATURE-----\n'
        padded=sig[:-len(ending)]+b'\n'*(4096-len(sig))+ending
        self.assertEqual(4096,len(padded));path.write_bytes(padded)
        verify.verify_signature('source-stage-acceptance.json',bundle['source-stage-acceptance.json'],path,
            context['profile'],context['status']['now_min'],context['allowed_signers_root'])
        _record_case('VF02','ACCEPT_VALID_4096_BYTE_SSHSIG','ACCEPT_VALID_4096_BYTE_SSHSIG')
        path.write_bytes(padded[:-len(ending)]+b'\n'+ending)
        _assert_case_refusal(self,'VF02','SIGNATURE_INVALID',lambda:verify.verify_signature(
            'source-stage-acceptance.json',bundle['source-stage-acceptance.json'],path,context['profile'],
            context['status']['now_min'],context['allowed_signers_root']))

    def test_p07_two_synthetic_target_roles_require_separate_grants(self):
        # Both existing pinned tools are data-only stand-ins. No produced or
        # native binary is created or invoked by this test.
        bundle,context=make_generated_fixture()
        m=verify.parse_record(bundle['generated-input-approval.json'],'generated-input-approval.json')
        q=json.loads(context['profiles'][m['generated_inputs_profile_sha256']])
        e=json.loads(context['profiles'][q['compilation_evidence_sha256']])
        c=json.loads(context['profiles'][q['custody_evidence_sha256']])
        inventory=json.loads(context['profiles'][q['files_inventory_sha256']])
        def add(obj):
            raw=verify.canonical(obj);h=_digest(raw);context['profiles'][h]=raw;return h
        sshraw=Path(SSH).read_bytes();entry={'kind':'regular','path':SSH,'mode':'0755',
            'bytes':len(sshraw),'sha256':_digest(sshraw)}
        inventory['entries']=sorted(inventory['entries']+[entry],key=lambda x:x['path']);ih=add(inventory)
        c['inventory_sha256']=ih;ch=add(c)
        e.update(output_inventory_sha256=ih,custody_evidence_sha256=ch);eh=add(e)
        identity=copy.deepcopy(q['executables'][0]);identity.update(inventory_sha256=ih,provenance_sha256=eh)
        codec={'id':'codec_test','path':SSH,'resolved_path':SSH,'bytes':len(sshraw),'sha256':_digest(sshraw),
            'provenance_sha256':eh,'inventory_sha256':ih,'path_entry_sha256':_digest(verify.canonical(entry)),
            'resolved_entry_sha256':_digest(verify.canonical(entry)),'symlink_chain':[]}
        q.update(files_inventory_sha256=ih,custody_evidence_sha256=ch,compilation_evidence_sha256=eh,
                 executables=[codec,identity]);qh=add(q)
        execution=json.loads(context['profiles'][m['execution_profile_sha256']])
        identity_command=copy.deepcopy(execution['commands'][0]);identity_command.update(id='locked_build_identity',executable=identity)
        codec_command=copy.deepcopy(identity_command);codec_command.update(id='codec_test',executable=codec,
            authorization_scope='CODEC_TEST_EXECUTION',argv=[{'index':i,'value':v}for i,v in enumerate([
                SSH,'-Y','verify','-f',str(FIX/'signers/owner'),'-I','test-owner','-n',
                'symphony.p08.source-stage.v1','-s',str(FIX/'source-stage-acceptance.sshsig')])])
        execution['commands']=[codec_command,identity_command];xh=add(execution)
        b=verify.parse_record(bundle['compilation-result.json'],'compilation-result.json')
        b.update(generated_inputs_profile_sha256=qh,compilation_evidence_sha256=eh)
        braw,bsig=sign_fixture('compilation-result.json','reviewer',value=b);bundle['compilation-result.json']=braw
        bundle,context=rechain(bundle,context,changes={'generated_inputs_profile_sha256':qh,
            'compilation_result_sha256':_digest(braw),'compilation_result_signature_sha256':_digest(bsig),
            'execution_profile_sha256':xh},grant_change={'authorization_scope':'CODEC_TEST_EXECUTION',
                'command_profile_sha256':_digest(verify.canonical(codec_command))})
        first=verify.verify_bundle(bundle,context)
        old_g=first['grant']['grant_id']
        bundle,context=rechain(bundle,context,grant_change={'authorization_scope':'BUILD_IDENTITY_TEST_EXECUTION',
            'command_profile_sha256':_digest(verify.canonical(identity_command)),
            'grant_id':'7'*32,'run_id':'8'*32,'nonce':'9'*64})
        second=verify.verify_bundle(bundle,context)
        self.assertNotEqual(old_g,second['grant']['grant_id'])
        self.assertEqual({'codec_test','locked_build_identity'},
                         {first['command']['executable']['id'],second['command']['executable']['id']})
        _record_case('P07','ACCEPTED_TWO_SEPARATE_GRANTS','ACCEPTED_TWO_SEPARATE_GRANTS')

    def test_local_installed_identity_and_custody_cases(self):
        directory=FIX/'local-inputs';directory.mkdir(parents=True,exist_ok=True)
        first,second=directory/'first',directory/'second'
        for path in (first,second):path.write_bytes(b'synthetic input');path.chmod(0o700)
        entries=[{'kind':'regular','path':str(p),'mode':'0700','bytes':len(p.read_bytes()),'sha256':_digest(p.read_bytes())}
                 for p in (first,second)]
        inventory={'schema':'p08-input-inventory-1','entries':entries}
        ref={'id':'fixture_input','path':str(first),'resolved_path':str(first),
             'bytes':entries[0]['bytes'],'sha256':entries[0]['sha256'],'provenance_sha256':'b'*64,
             'inventory_sha256':_digest(verify.canonical(inventory)),
             'path_entry_sha256':_digest(verify.canonical(entries[0])),
             'resolved_entry_sha256':_digest(verify.canonical(entries[0])),'symlink_chain':[]}
        verify.verify_installed_artifact(ref,inventory,[str(OUT)],actual_path=str(first),actual_argv0=str(first))
        _record_case('P02','ACCEPTED','ACCEPTED')
        for case in ('N27','N30','N51','VF08'):
            _assert_case_refusal(self,case,'EXECUTABLE_PATH_MISMATCH',lambda:verify.verify_installed_artifact(
                ref,inventory,[str(OUT)],actual_path=str(second),actual_argv0=str(second)))
        changed=dict(ref,path_entry_sha256='a'*64)
        _assert_case_refusal(self,'N28','EXECUTABLE_INVENTORY_MISMATCH',lambda:verify.verify_installed_artifact(changed,inventory,[str(OUT)]))
        changed=dict(ref,path='/usr/bin/../bin/python3.14')
        _assert_case_refusal(self,'N44','FORMAT_INVALID',lambda:verify.verify_installed_artifact(changed,inventory,[str(OUT)]))
        first.write_bytes(b'x'*100)
        _assert_case_refusal(self,'N22','CUSTODY_FAILURE',lambda:verify.verify_installed_artifact(ref,inventory,[str(OUT)]))
        real=directory/'real';real.mkdir(exist_ok=True);leaf=real/'input';leaf.write_bytes(b'data');leaf.chmod(0o700)
        alias=directory/'directory-alias'
        if not alias.is_symlink():alias.symlink_to(real,target_is_directory=True)
        alias_path=str(alias/'input')
        entry={'kind':'regular','path':alias_path,'mode':'0700','bytes':4,'sha256':_digest(b'data')}
        inv={'schema':'p08-input-inventory-1','entries':[entry]}
        wrong=dict(ref,path=alias_path,resolved_path=alias_path,bytes=4,sha256=entry['sha256'],
            inventory_sha256=_digest(verify.canonical(inv)),path_entry_sha256=_digest(verify.canonical(entry)),
            resolved_entry_sha256=_digest(verify.canonical(entry)))
        _assert_case_refusal(self,'N31','EXECUTABLE_RESOLUTION_INVALID',lambda:verify.verify_installed_artifact(wrong,inv,[str(OUT)]))

    def test_build_approval_cannot_select_generated_grant(self):
        bundle,context=make_generated_fixture()
        bundle.pop('generated-input-approval.json')
        bundle['build-input-approval.json']=context['producer_bundle']['build-input-approval.json']
        for case in ('N15','N45'):
            _assert_case_refusal(self,case,'EXECUTION_NOT_GRANTED',lambda:verify.verify_bundle(bundle,context))

    def test_unapproved_command_and_stale_rebuild_outputs_refuse(self):
        bundle,context=make_fixture()
        bundle,context=rechain(bundle,context,grant_change={'command_profile_sha256':'e'*64})
        _assert_case_refusal(self,'N21','EXECUTION_PROFILE_MISMATCH',lambda:verify.verify_bundle(bundle,context))
        bundle,context=make_generated_fixture()
        bundle,context=rechain(bundle,context,grant_change={'command_profile_sha256':'e'*64})
        _assert_case_refusal(self,'N54','COMMAND_NOT_APPROVED',lambda:verify.verify_bundle(bundle,context))
        bundle,context=make_generated_fixture();context['producer_facts']['exclusive_fresh_outputs']=False
        _assert_case_refusal(self,'N25','PRODUCER_NOT_ELIGIBLE',lambda:verify.verify_bundle(bundle,context))

    def test_enrollment_and_real_signature_negative_cases(self):
        for case, kind, expected in (
                ('N02','rogue','SIGNER_UNAUTHORIZED'), ('N03','rogue','SIGNER_UNAUTHORIZED'),
                ('N04','reviewer','ROLE_MISMATCH'), ('N05','purpose','SIGNATURE_INVALID'),
                ('N06','oversize','SIGNATURE_INVALID'), ('VF03','message','SIGNATURE_INVALID')):
            with self.subTest(case=case):
                bundle, context = make_fixture()
                name = 'source-stage-acceptance.json'; raw = bundle[name]
                if kind in ('rogue','reviewer'):
                    sign_fixture(name, kind)
                elif kind == 'purpose':
                    sign_fixture(name, 'owner', namespace='symphony.p08.input-owner.v1')
                elif kind == 'oversize':
                    (FIX/'source-stage-acceptance.sshsig').write_bytes(b'x'*4097)
                else:
                    changed=verify.parse_record(raw,name);changed['decision_id']='f'*32;raw=verify.canonical(changed)
                _assert_case_refusal(self,case,expected,lambda:verify.verify_signature(name,raw,
                    FIX/'source-stage-acceptance.sshsig',context['profile'],context['status']['now_min'],context['allowed_signers_root']))

    def test_enrollment_context_rejects_ambiguous_or_unaccepted_authority(self):
        for case, change, expected in (
                ('EN01','wire','ROLE_MISMATCH'), ('EN02','principal','ROLE_MISMATCH'),
                ('EN03','algorithm','SIGNER_UNAUTHORIZED'), ('EN04','fingerprint','SIGNER_UNAUTHORIZED'),
                ('EN08','expired','APPROVAL_STALE')):
            with self.subTest(case=case):
                unused, context=make_fixture(); p=copy.deepcopy(context['profile']);now=context['status']['now_min']
                if change=='wire':
                    for field in ('public_key','fingerprint'):p['keys'][1][field]=p['keys'][0][field]
                elif change=='principal':p['keys'][1]['principal']=p['keys'][0]['principal']
                elif change=='algorithm':p['keys'][0]['public_key']='ssh-rsa AAAA'
                elif change=='fingerprint':p['keys'][0]['fingerprint']=_digest(p['keys'][0]['public_key'].encode('ascii'))
                else:p['keys'][0]['expires_at']=now
                _assert_case_refusal(self,case,expected,lambda:verify.validate_enrollment(p,now))
        for case, change, expected in (
                ('EN05','signers','VERIFIER_UNAPPROVED'), ('EN06','acceptance','STATUS_INVALID'),
                ('EN07','custody','INPUTS_INCOMPLETE'), ('EN09','profile','STATUS_INVALID'),
                ('N19','inventory','VERIFIER_UNAPPROVED'), ('VF07','profile','STATUS_INVALID')):
            with self.subTest(case=case):
                bundle,context=make_fixture()
                if change=='signers':
                    with(FIX/'signers/owner').open('ab')as f:f.write(b'\n')
                elif change=='acceptance':context.pop('accepted_profile_sha256')
                elif change=='custody':context['evidence_bytes'].clear()
                elif change=='profile':context['profile']['keys'][0]['custody_record_sha256']='e'*64
                else:context['profiles'].pop(context['profile']['verifier_inventory_sha256'])
                _assert_case_refusal(self,case,expected,lambda:verify.verify_bundle(bundle,context))
        for case in ('EN10','VF04','VF06'):
            _assert_case_refusal(self,case,'INDEPENDENT_VERIFIER_INSTALLATION_NOT_APPROVED',verify.main)

    def test_canonical_and_bound_preflights(self):
        source=_default_record('source-stage-acceptance.json')
        raw=verify.canonical(source)
        for index,bad in enumerate((raw+b'\n',b' '+raw,b'\xef\xbb\xbf'+raw,
                raw.replace(b'"issued_at":0',b'"issued_at":true'),
                raw.replace(b'"issued_at":0',b'"issued_at":1.0'),
                raw.replace(b'"issued_at":0',b'"issued_at":01'),
                raw.replace(b'"issued_at":0',b'"issued_at":18446744073709551616'),
                raw.replace(b'"ACCEPT"',b'"\\u0041CCEPT"'),raw+b'{}')):
            with self.subTest(index=index):
                _assert_case_refusal(self,'VF01','FORMAT_INVALID',lambda:verify.parse_record(bad,'source-stage-acceptance.json'))
        _assert_case_refusal(self,'N07','FORMAT_INVALID',lambda:verify.parse_record(b'{"x":1,"x":2}','source-stage-acceptance.json'))
        _assert_case_refusal(self,'VF02','FORMAT_INVALID',lambda:verify.parse_record(b' ' *8193,'source-stage-acceptance.json'))
        for kind,size in (('execution-profile',1024*1024+1),('input-inventory',16*1024*1024+1)):
            _assert_case_refusal(self,'VF02','FORMAT_INVALID',lambda:verify.parse_profile(b' '*size,kind))

    def test_source_and_observation_cross_record_cases(self):
        bundle,context=make_fixture();(FIX/'source-stage-acceptance.sshsig').unlink()
        _assert_case_refusal(self,'N08','ACCEPTANCE_UNAUTHENTICATED',lambda:verify.verify_bundle(bundle,context))
        for case,change in (('N09','commit'),('N10','inventory')):
            bundle,context=make_fixture()
            if change=='commit':context['source_facts']['commit']='b'*40
            else:context['source_facts']['observed_entries']=context['source_facts']['observed_entries'][:-1]
            _assert_case_refusal(self,case,'SOURCE_MISMATCH',lambda:verify.verify_bundle(bundle,context))
        bundle,context=make_fixture();m=verify.parse_record(bundle['build-input-approval.json'],'build-input-approval.json')
        source_inventory=json.loads(context['profiles'][m['source_inventory_sha256']]);source_inventory['commit']='1'*40
        raw=verify.canonical(source_inventory);digest=_digest(raw);context['profiles'][digest]=raw
        context['source_facts']['inventory_sha256']=digest
        bundle,context=rechain(bundle,context,changes={'source_inventory_sha256':digest})
        _assert_case_refusal(self,'N09','SOURCE_MISMATCH',lambda:verify.verify_bundle(bundle,context))
        for case,changes,expected in (
                ('N33',{'run_id':'a'*32},'ACTION_BINDING_MISMATCH'),
                ('N40',{'owner_decision_sha256':None},'ACTION_BINDING_MISMATCH')):
            bundle,context=make_fixture()
            if changes.get('owner_decision_sha256','') is None:changes={'owner_decision_sha256':_digest(bundle['source-stage-acceptance.json'])}
            bundle,context=rechain(bundle,context,action_change=changes)
            _assert_case_refusal(self,case,expected,lambda:verify.verify_bundle(bundle,context))
        for case,changes,expected in (
                ('N37',{'review_id':'b'*32},'REVIEW_BINDING_INVALID'),
                ('N42',{'observed_at':0},'REVIEW_BINDING_INVALID')):
            bundle,context=make_fixture();bundle,context=rechain(bundle,context,review_change=changes)
            _assert_case_refusal(self,case,expected,lambda:verify.verify_bundle(bundle,context))
        bundle,context=make_fixture();g=verify.parse_record(bundle['native-execution-grant.json'],'native-execution-grant.json')
        r=verify.parse_record(bundle['input-review.json'],'input-review.json')
        g['action_observation_sha256']=r['review_observation_sha256']
        bundle['native-execution-grant.json'],unused=sign_fixture('native-execution-grant.json','owner',value=g)
        _assert_case_refusal(self,'N32','OBSERVATION_PURPOSE_MISMATCH',lambda:verify.verify_bundle(bundle,context))
        bundle,context=make_fixture();g=verify.parse_record(bundle['native-execution-grant.json'],'native-execution-grant.json')
        r=verify.parse_record(bundle['input-review.json'],'input-review.json');r['review_observation_sha256']=g['action_observation_sha256']
        bundle['input-review.json']=verify.canonical(r)
        bundle,context=rechain(bundle,context)
        _assert_case_refusal(self,'N41','OBSERVATION_PURPOSE_MISMATCH',lambda:verify.verify_bundle(bundle,context))
        bundle,context=make_fixture();g=verify.parse_record(bundle['native-execution-grant.json'],'native-execution-grant.json')
        action=json.loads(context['profiles'][g['action_observation_sha256']]);action.pop('nonce')
        _assert_case_refusal(self,'N43','FORMAT_INVALID',lambda:verify.parse_profile(verify.canonical(action),'action-observation-report'))
        context['profiles'].pop(g['action_observation_sha256'])
        _assert_case_refusal(self,'N20','OBSERVATION_UNAUTHENTICATED',lambda:verify.verify_bundle(bundle,context))

    def test_generated_provenance_and_fresh_acceptance_cases(self):
        for case,change,expected in (
                ('N46','missing','COMPILATION_RECEIPT_MISSING'),
                ('N47','purpose','COMPILATION_RECEIPT_UNAUTHENTICATED'),
                ('N48','lineage','BUILD_PROVENANCE_MISMATCH'),
                ('N49','failed','PRODUCER_NOT_ELIGIBLE'),
                ('N52','custody','GENERATED_CUSTODY_INVALID'),
                ('N53','old-review','CHAIN_MISMATCH'),
                ('VF09','history','BUILD_PROVENANCE_MISMATCH'),
                ('VF10','old-review','CHAIN_MISMATCH')):
            with self.subTest(case=case):
                bundle,context=make_generated_fixture()
                if change=='missing':bundle.pop('compilation-result.json')
                elif change=='purpose':
                    raw,sig=sign_fixture('compilation-result.json','reviewer',namespace='symphony.p08.input-review.v1')
                    bundle,context=rechain(bundle,context,changes={'compilation_result_signature_sha256':_digest(sig)})
                elif change=='lineage':bundle,context=replace_generated(bundle,context,receipt_change={'producer_run_id':'9'*32})
                elif change=='failed':context['producer_facts']['complete_audit']=False
                elif change=='custody':context['producer_facts']['continuous_custody']=False
                elif change=='old-review':bundle['input-review.json']=context['producer_bundle']['input-review.json']
                else:context.pop('producer_bundle')
                _assert_case_refusal(self,case,expected,lambda:verify.verify_bundle(bundle,context))
        for case,change,expected in (
                ('N50','length','GENERATED_INPUT_MISMATCH'),
                ('N55','receipt-provenance','PROVENANCE_CYCLE_INVALID'),
                ('N56','runtime-role','GENERATED_TARGET_UNSUPPORTED'),
                ('N57','mixed','BUILD_PROVENANCE_MISMATCH')):
            with self.subTest(case=case):
                bundle,context=make_generated_fixture()
                old_b=bundle['compilation-result.json'];context['profiles'][_digest(old_b)]=old_b
                def mutate(q):
                    if change=='length':q['executables'][0]['bytes']+=1
                    elif change=='receipt-provenance':q['executables'][0]['provenance_sha256']=_digest(old_b)
                    elif change=='runtime-role':q['executables'][0]['id']='client'
                    else:
                        e=json.loads(context['profiles'][q['compilation_evidence_sha256']]);e['producer_nonce']='7'*64
                        eraw=verify.canonical(e);context['profiles'][_digest(eraw)]=eraw
                        q['executables'][0]['provenance_sha256']=_digest(eraw)
                bundle,context=replace_generated(bundle,context,qchange=mutate)
                _assert_case_refusal(self,case,expected,lambda:verify.verify_bundle(bundle,context))

    def test_positive_reuse_of_inputs_and_expired_producer_history(self):
        bundle,context=make_fixture();result=verify.verify_bundle(bundle,context)
        _record_case('P01','ACCEPTED', 'ACCEPTED' if result['grant']['authorization_scope']=='BUILD_ONLY' else 'WRONG_SCOPE')
        _record_case('EN11','ACCEPTED','ACCEPTED');_record_case('VF05','ACCEPTED','ACCEPTED')
        before=(bundle['input-review.json'],bundle['owner-input-decision.json'])
        context['status']['now_min']+=1;context['status']['now_max']+=1
        context['status']['monotonic_ns']+=1_000_000_000
        bundle,context=rechain(bundle,context,grant_change={'grant_id':'f'*32,'run_id':'1'*32,'nonce':'2'*64,
            'issued_at':context['status']['now_min'],'not_before':context['status']['now_min']})
        self.assertEqual(before,(bundle['input-review.json'],bundle['owner-input-decision.json']))
        verify.verify_bundle(bundle,context);_record_case('P04','ACCEPTED','ACCEPTED')
        bundle,context=make_generated_fixture();verify.verify_bundle(bundle,context)
        _record_case('P05','ACCEPTED','ACCEPTED');_record_case('VF11','ACCEPTED','ACCEPTED')
        bundle,context=rechain(bundle,context,delay=700)
        self.assertLess(verify.parse_record(context['producer_bundle']['native-execution-grant.json'],
            'native-execution-grant.json')['expires_at'],context['status']['now_min'])
        verify.verify_bundle(bundle,context);_record_case('P06','ACCEPTED','ACCEPTED')

    def test_n01_missing_grant_is_rejected(self):
        bundle, context = make_fixture()
        bundle.pop("native-execution-grant.json")
        _assert_case_refusal(self, "N01", "APPROVAL_MISSING",
                             lambda: verify.verify_bundle(bundle, context))

    def test_n11_grant_manifest_reference_must_match(self):
        bundle, context = make_fixture()
        grant = verify.parse_record(bundle["native-execution-grant.json"],
                                    "native-execution-grant.json")
        grant["manifest_sha256"] = "a" * 64
        bundle["native-execution-grant.json"] = verify.canonical(grant)
        _assert_case_refusal(self, "N11", "CHAIN_MISMATCH",
                             lambda: verify.verify_bundle(bundle, context))

    def test_n12_expired_signer_context_is_rejected(self):
        bundle, context = make_fixture()
        context["status"]["now_min"] = 1800000000
        context["status"]["now_max"] = 1800000000
        _assert_case_refusal(self, "N12", "APPROVAL_STALE",
                             lambda: verify.verify_bundle(bundle, context))

    def test_n13_revoked_active_grant_is_rejected(self):
        bundle, context = make_fixture()
        grant = verify.parse_record(bundle["native-execution-grant.json"],
                                    "native-execution-grant.json")
        context["status"]["revoked_ids"] = [grant["grant_id"]]
        _assert_case_refusal(self, "N13", "STATUS_INVALID",
                             lambda: verify.verify_bundle(bundle, context))

    def test_n16_policy_provenance_mismatch_is_rejected(self):
        bundle, context = make_fixture()
        manifest = verify.parse_record(bundle["build-input-approval.json"],
                                       "build-input-approval.json")
        raw = context["profiles"][manifest["rust_provenance_profile_sha256"]]
        provenance = json.loads(raw.decode("ascii"))
        provenance["certificate_sha256"] = "e" * 64
        _assert_case_refusal(self, "N16", "PROVENANCE_INVALID",
                             lambda: verify.parse_profile(verify.canonical(provenance),
                                                          "rust-provenance-profile"))

    def test_n18_missing_required_profile_is_rejected(self):
        fields = ("build_image_profile_sha256", "execution_profile_sha256",
                  "host_std_profile_sha256", "musl_std_profile_sha256",
                  "crt_profile_sha256", "toolchain_profile_sha256",
                  "linker_profile_sha256", "rust_provenance_profile_sha256",
                  "source_inventory_sha256")
        manifest = {field: "a" * 64 for field in fields}
        _assert_case_refusal(self, "N18", "INPUTS_INCOMPLETE",
                             lambda: verify._resolve_manifest_profiles(manifest, {}, {}))

    def test_n26_content_only_artifact_is_rejected(self):
        _assert_case_refusal(self, "N26", "FORMAT_INVALID",
                             lambda: verify.verify_installed_artifact({}, {}, ()))

    def test_n27_and_n30_invocation_path_must_match_reference(self):
        bundle, context = make_fixture()
        manifest = verify.parse_record(bundle["build-input-approval.json"],
                                       "build-input-approval.json")
        grant = verify.parse_record(bundle["native-execution-grant.json"],
                                    "native-execution-grant.json")
        resolved = verify._resolve_manifest_profiles(manifest, grant, context["profiles"])
        artifact, inventory = resolved["command"]["executable"], resolved["inventory"]
        _assert_case_refusal(self, "N27", "EXECUTABLE_PATH_MISMATCH",
                             lambda: verify.verify_installed_artifact(
                                 artifact, inventory, context["sealed_roots"],
                                 actual_path="/usr/bin/another-path"))
        _assert_case_refusal(self, "N30", "EXECUTABLE_PATH_MISMATCH",
                             lambda: verify.verify_installed_artifact(
                                 artifact, inventory, context["sealed_roots"],
                                 actual_argv0="/usr/bin/another-path"))

    def test_n29_declared_symlink_cycle_is_rejected(self):
        bundle, context = make_fixture()
        manifest = verify.parse_record(bundle["build-input-approval.json"],
                                       "build-input-approval.json")
        grant = verify.parse_record(bundle["native-execution-grant.json"],
                                    "native-execution-grant.json")
        resolved = verify._resolve_manifest_profiles(manifest, grant, context["profiles"])
        artifact = copy.deepcopy(resolved["command"]["executable"])
        link = FIX / "cycle"
        if link.is_symlink():
            link.unlink()
        link.symlink_to("cycle")
        entry = {"kind":"symlink", "path":str(link), "target":"cycle",
                 "resolved_path":artifact["resolved_path"], "resolved_sha256":artifact["sha256"]}
        inventory = {"schema":"p08-input-inventory-1", "entries":sorted([
            entry, resolved["inventory"]["entries"][0]], key=lambda x:x["path"])}
        artifact.update(path=str(link), inventory_sha256=_digest(verify.canonical(inventory)),
            path_entry_sha256=_digest(verify.canonical(entry)), symlink_chain=[_digest(verify.canonical(entry))])
        _assert_case_refusal(self, "N29", "EXECUTABLE_RESOLUTION_INVALID",
                             lambda: verify.verify_installed_artifact(
                                 artifact, inventory, context["sealed_roots"]))

    def test_n36_unknown_review_observation_field_is_rejected(self):
        observation = {"schema": "p08-review-observation-1", "purpose": "INPUT_REVIEW_ONLY",
                       "review_id": "a" * 32, "reviewer_id": "reviewer",
                       "operator_id": "operator", "manifest_sha256": "b" * 64,
                       "trust_profile_sha256": "c" * 64, "observed_at": 1,
                       "source_commit": "d" * 40, "source_tree": "e" * 40,
                       "profiles": [], "evidence_sha256": "f" * 64, "verdict": "MATCH",
                       "grant_id": "forbidden"}
        _assert_case_refusal(self, "N36", "FORMAT_INVALID",
                             lambda: verify.parse_profile(verify.canonical(observation),
                                                          "review-observation-report"))


if __name__ == "__main__":
    unittest.main()
