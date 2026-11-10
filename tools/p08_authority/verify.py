"""Pure P08 verification.

`verify_bundle` accepts `bundle` as canonical filename -> raw bytes. Its trusted
context must come from the installed operator, never from that bundle. Required
context keys are `profile`, `profiles` (digest -> raw canonical profile bytes),
`status`, `bundle_root`, and `allowed_signers_root`. Status requires `now_min`,
`now_max`, `trust_epoch`, `clock_session_id`, `monotonic_ns`, `operator_id`,
`enrollment_sha256`, `current_decisions_sha256`, `revocations_sha256`,
`clock_evidence_sha256`, `register_observation_sha256`,
`policy_a_evidence_sha256`, and `revoked_ids`. The caller establishes custody
and independent authenticity for all trusted-context values.
"""

import hashlib
import json
import os
import base64
import struct
from pathlib import Path
import re
import subprocess
import stat


ROOT = Path(__file__).resolve().parent
SCHEMAS = json.loads((ROOT / "record-schemas.json").read_text("ascii"))["schemas"]
PROFILE_RULES = json.loads((ROOT / "profile-requirements.json").read_text("ascii"))
MAX_RECORD = 16384
MAX_PROFILE = 1024 * 1024
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
SIGNABLE_FIXTURES = (
    "source-stage-acceptance.json", "input-review.json", "owner-input-decision.json",
    "native-execution-grant.json", "generated-native-execution-grant.json",
    "compilation-result.json",
)


class Refusal(Exception):
    def __init__(self, code, authenticated_grant=None):
        self.code = code
        self.authenticated_grant = authenticated_grant
        super().__init__(code)


def sha256(raw):
    return hashlib.sha256(raw).hexdigest()


def _read_regular(path, limit, code):
    """Bound allocation before reading independently custodied record files."""
    try:
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
        try:
            before = os.fstat(fd)
            if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                raise Refusal(code)
            raw = bytearray()
            while len(raw) <= limit:
                block = os.read(fd, min(65536, limit + 1 - len(raw)))
                if not block:
                    break
                raw.extend(block)
            after = os.fstat(fd)
            if (len(raw) > limit or
                    (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) !=
                    (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns)):
                raise Refusal(code)
            return bytes(raw)
        finally:
            os.close(fd)
    except OSError as error:
        raise Refusal(code) from error


def _pairs(pairs):
    out = {}
    for key, value in pairs:
        if key in out:
            raise Refusal("FORMAT_INVALID")
        out[key] = value
    return out


def _ascii_tree(value, depth=0):
    if depth > 32:
        raise Refusal("FORMAT_INVALID")
    if isinstance(value, dict):
        for key, child in value.items():
            if (not isinstance(key, str) or not key.isascii() or
                    any(ord(c) < 32 or ord(c) > 126 or c in '"\\' for c in key)):
                raise Refusal("FORMAT_INVALID")
            _ascii_tree(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            _ascii_tree(child, depth + 1)
    elif isinstance(value, str):
        if not value.isascii() or any(ord(c) < 32 or ord(c) > 126 or c in '"\\' for c in value):
            raise Refusal("FORMAT_INVALID")
    elif isinstance(value, int) and not isinstance(value, bool):
        if value < 0 or value > 18446744073709551615:
            raise Refusal("FORMAT_INVALID")
    else:
        raise Refusal("FORMAT_INVALID")


def canonical(value):
    _ascii_tree(value)
    try:
        return json.dumps(value, ensure_ascii=True, sort_keys=True,
                          separators=(",", ":"), allow_nan=False).encode("ascii")
    except (TypeError, ValueError, UnicodeError):
        raise Refusal("FORMAT_INVALID")


def _validate_schema(value, schema):
    if schema.get("type") == "object":
        if not isinstance(value, dict) or set(value) != set(schema["required"]):
            raise Refusal("FORMAT_INVALID")
        for key, child in value.items():
            _validate_schema(child, schema["properties"][key])
        return
    typ = schema.get("type")
    if typ == "array":
        if not isinstance(value, list):
            raise Refusal("FORMAT_INVALID")
        if "minItems" in schema and len(value) < schema["minItems"]:
            raise Refusal("FORMAT_INVALID")
        if "maxItems" in schema and len(value) > schema["maxItems"]:
            raise Refusal("FORMAT_INVALID")
        for item in value:
            _validate_schema(item, schema["items"])
    elif typ == "string":
        if not isinstance(value, str):
            raise Refusal("FORMAT_INVALID")
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            raise Refusal("FORMAT_INVALID")
    elif typ == "integer":
        if not isinstance(value, int) or isinstance(value, bool):
            raise Refusal("FORMAT_INVALID")
        if not schema.get("minimum", 0) <= value <= schema.get("maximum", 18446744073709551615):
            raise Refusal("FORMAT_INVALID")
    elif typ == "boolean":
        if not isinstance(value, bool):
            raise Refusal("FORMAT_INVALID")
    elif typ:
        raise Refusal("FORMAT_INVALID")
    if "const" in schema and value != schema["const"]:
        raise Refusal("FORMAT_INVALID")
    if "const" in schema and type(value) is not type(schema["const"]):
        raise Refusal("FORMAT_INVALID")
    if "enum" in schema and value not in schema["enum"]:
        raise Refusal("FORMAT_INVALID")
    if isinstance(value, str) and "maxLength" in schema and len(value.encode("ascii")) > schema["maxLength"]:
        raise Refusal("FORMAT_INVALID")


def parse_record(raw, record_filename):
    if not isinstance(raw, bytes) or len(raw) > _record_limit(record_filename):
        raise Refusal("FORMAT_INVALID")
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_pairs,
                           parse_float=lambda _: (_ for _ in ()).throw(Refusal("FORMAT_INVALID")),
                           parse_constant=lambda _: (_ for _ in ()).throw(Refusal("FORMAT_INVALID")))
    except Refusal:
        raise
    except Exception:
        raise Refusal("FORMAT_INVALID")
    _ascii_tree(value)
    if canonical(value) != raw:
        raise Refusal("FORMAT_INVALID")
    try:
        schema = SCHEMAS[record_filename]
    except KeyError:
        raise Refusal("FORMAT_INVALID")
    _validate_schema(value, schema)
    if any(isinstance(v, str) and k.endswith("_sha256") and v == "0" * 64
           for k, v in value.items()):
        raise Refusal("FORMAT_INVALID")
    return value


def parse_profile(raw, profile_kind):
    limit = 16 * 1024 * 1024 if profile_kind == "input-inventory" else MAX_PROFILE
    if not isinstance(raw, bytes) or len(raw) > limit:
        raise Refusal("FORMAT_INVALID")
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_pairs,
                           parse_float=lambda _: (_ for _ in ()).throw(Refusal("FORMAT_INVALID")),
                           parse_constant=lambda _: (_ for _ in ()).throw(Refusal("FORMAT_INVALID")))
    except Refusal:
        raise
    except Exception:
        raise Refusal("FORMAT_INVALID")
    _ascii_tree(value)
    if canonical(value) != raw:
        raise Refusal("FORMAT_INVALID")
    if profile_kind not in PROFILE_RULES["profiles"]:
        raise Refusal("FORMAT_INVALID")
    _validate_profile(value, PROFILE_RULES["profiles"][profile_kind], profile_kind)
    return value


def _record_limit(filename):
    rules = json.loads((ROOT / "record-schemas.json").read_text("ascii"))["canonical_byte_rules"]
    if filename in ("build-input-approval.json", "generated-input-approval.json"):
        return rules["manifest_max_bytes"]
    if filename in ("native-execution-grant.json", "generated-native-execution-grant.json"):
        return rules["generated_grant_max_bytes"]
    if filename == "compilation-result.json":
        return rules["compilation_result_max_bytes"]
    return rules["other_record_max_bytes"]


def _validate_profile(value, rule, profile_kind):
    if not isinstance(value, dict) or set(value) != set(rule["required"]):
        raise Refusal("FORMAT_INVALID")
    for field, descriptor in rule["types"].items():
        _check_profile_value(field, value[field], descriptor, profile_kind)
    schema_value = rule["types"].get("schema", "")
    if schema_value.startswith("p08-") and value.get("schema") != schema_value:
        raise Refusal("FORMAT_INVALID")
    if profile_kind == "rust-provenance-profile":
        fixed = {"policy_decision_id": "5f6773bc-83ef-498f-b468-bd49d809b914",
                 "certificate_sha256": "e54b09a439647e006b4831eec9785cbaaf3e07ab371c3a6ee6a68e1bdb9fbc6b",
                 "manifest_sha256": "a7c8774a5fd8441c997d94c029776cbc5eb111e9d72ab5d256fa69866644347e",
                 "manifest_signature_sha256": "a9fed69b47daaaf29a6207af9df13aedb66d502ab0acc4ea557602edf87fd1aa",
                 "primary_fingerprint": "108f66205eaeb0aaa8dd5e1c85ab96e6fa1be5fe",
                 "signature_algorithm": "RSA/SHA512 primary direct signature",
                 "signature_time": "2026-09-03T12:54:14Z"}
        if any(value.get(key) != expected for key, expected in fixed.items()):
            raise Refusal("PROVENANCE_INVALID")
        archives = {x["id"]: x["sha256"] for x in value["archives"]}
        if archives != {
                "cargo": "ea1de9f9e23107d97ee2b41a72c552f34064a593da503789218387aee59f3ba4",
                "rustc": "e974f036b28565f37c0f3bd92ddefa809bee16c04f9dcf07b9ed96e05aaaf7c4",
                "ruststd_host": "fa3ff450172a16c026944030230c5069947af93c728d9179971d44e5e0cfb561",
                "ruststd_musl": "bd9f35880de21dab0e387e84009c00001ae7836a4ba565cb16823f13f75f325f"}:
            raise Refusal("PROVENANCE_INVALID")


def _check_entry(value, kind):
    spec = PROFILE_RULES["common"]["entry_types"][kind]
    if not isinstance(value, dict) or set(value) != set(spec["required"]):
        raise Refusal("FORMAT_INVALID")
    for field, descriptor in spec["types"].items():
        item = value[field]
        if field not in ("symlink_chain", "namespaces") and "u64" not in descriptor and not isinstance(item, str):
            raise Refusal("FORMAT_INVALID")
        if isinstance(item, list):
            if field not in ("symlink_chain", "namespaces") or len(item) > 32 or (all(isinstance(x, str) for x in item) and len(item) != len(set(item))):
                raise Refusal("FORMAT_INVALID")
            if "hex64" in descriptor and any(not isinstance(x, str) or not HEX64.fullmatch(x) for x in item):
                raise Refusal("FORMAT_INVALID")
            continue
        if "hex64" in descriptor and (not isinstance(item, str) or not HEX64.fullmatch(item) or item == "0" * 64):
            raise Refusal("FORMAT_INVALID")
        if "hex40" in descriptor and (not isinstance(item, str) or not re.fullmatch(r"[0-9a-f]{40}", item)):
            raise Refusal("FORMAT_INVALID")
        if "u64" in descriptor and (not isinstance(item, int) or isinstance(item, bool) or not 0 <= item < 2**64):
            raise Refusal("FORMAT_INVALID")
        if isinstance(item, str) and (not item.isascii() or len(item.encode("ascii")) > 4096):
            raise Refusal("FORMAT_INVALID")
        if not isinstance(item, (str, int)) or isinstance(item, bool):
            raise Refusal("FORMAT_INVALID")
        if field in ("id", "principal") and (not isinstance(item, str) or not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", item)):
            raise Refusal("FORMAT_INVALID")
        if field in ("path", "resolved_path") and (not isinstance(item, str) or not item or len(item) > 512):
            raise Refusal("FORMAT_INVALID")
    if kind == "authority_key":
        expected = {
            "project-owner-issuer": sorted(("symphony.p08.source-stage.v1", "symphony.p08.input-owner.v1", "symphony.p08.native-grant.v1")),
            "independent-reviewer": sorted(("symphony.p08.input-review.v1", "symphony.p08.build-result.v1")),
        }
        if value["role"] not in expected or value["namespaces"] != expected[value["role"]]:
            raise Refusal("FORMAT_INVALID")
        principal = value["principal"]
        if (not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", principal) or
                any(token in value["public_key"] for token in ("cert-", "@cert-authority", "*", "?"))):
            raise Refusal("FORMAT_INVALID")
    if kind == "argument":
        if value["index"] > 100000 or len(value["value"].encode("ascii")) > 4096:
            raise Refusal("FORMAT_INVALID")
    if kind == "source_file":
        if value["mode"] not in ("100644", "100755") or value["path"].startswith("/") or any(x in ("", ".", "..") for x in value["path"].split("/")):
            raise Refusal("FORMAT_INVALID")
    if kind in ("closure_regular_file", "closure_symlink", "installed_artifact"):
        for field in ("path", "resolved_path"):
            if field in value and (not value[field].startswith("/") or value[field].startswith("//") or os.path.normpath(value[field]) != value[field]):
                raise Refusal("FORMAT_INVALID")
    if kind == "closure_regular_file" and (value["kind"] != "regular" or not re.fullmatch(r"[0-7]{4}", value["mode"])):
        raise Refusal("FORMAT_INVALID")
    if kind == "closure_symlink" and (value["kind"] != "symlink" or "\x00" in value["target"] or len(value["target"].encode("ascii")) > 512):
        raise Refusal("FORMAT_INVALID")
    if kind == "environment" and (not re.fullmatch(r"[A-Z_][A-Z0-9_]*", value["name"]) or
            any(x in value["name"].lower() for x in ("proxy", "token", "secret", "credential", "agent", "password", "auth", "cookie", "session", "preload", "library_path", "pythonpath")) or
            value["name"].endswith(("_KEY", "_PASS"))):
        raise Refusal("FORMAT_INVALID")


def _check_profile_value(field, value, descriptor, kind):
    if field in ("purpose", "verdict") and descriptor in ("INPUT_REVIEW_ONLY", "ACTION_PREFLIGHT_ONLY", "MATCH", "ACTIVE", "SEALED_READ_ONLY") and value != descriptor:
        raise Refusal("FORMAT_INVALID")
    if field == "exit_code":
        if type(value) is not int or value != 0:
            raise Refusal("FORMAT_INVALID")
    elif "hex64" in descriptor:
        if not isinstance(value, str) or not HEX64.fullmatch(value) or set(value) == {"0"}:
            raise Refusal("FORMAT_INVALID")
    elif "hex40" in descriptor:
        if not isinstance(value, str) or not re.fullmatch(r"[0-9a-f]{40}", value) or set(value) == {"0"}:
            raise Refusal("FORMAT_INVALID")
    elif "u64" in descriptor or descriptor.startswith("1794201657"):
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < 2**64:
            raise Refusal("FORMAT_INVALID")
        if descriptor.startswith("1794201657") and value != 1794201657:
            raise Refusal("FORMAT_INVALID")
        ceilings = {"approval_max_age_s": 86400, "lease_max_s": 900,
                    "clock_skew_max_s": 30, "action_observation_max_age_s": 60}
        if field in ceilings and value != ceilings[field]:
            raise Refusal("FORMAT_INVALID")
    elif field == "keys":
        if not isinstance(value, list) or len(value) != 2:
            raise Refusal("FORMAT_INVALID")
        for entry in value:
            _check_entry(entry, "authority_key")
    elif kind == "input-inventory" and field == "entries":
        if not isinstance(value, list) or len(value) > 100000:
            raise Refusal("FORMAT_INVALID")
        for entry in value:
            if not isinstance(entry, dict) or entry.get("kind") not in ("regular", "symlink"):
                raise Refusal("FORMAT_INVALID")
            _check_entry(entry, "closure_regular_file" if entry["kind"] == "regular" else "closure_symlink")
        paths = [entry["path"] for entry in value]
        if paths != sorted(set(paths)):
            raise Refusal("FORMAT_INVALID")
    elif descriptor.startswith("array of") or descriptor.startswith("nonempty array") or descriptor.startswith("exact four"):
        if not isinstance(value, list) or len(value) > 100000:
            raise Refusal("FORMAT_INVALID")
        entry_kind = next((name for name in PROFILE_RULES["common"]["entry_types"]
                           if re.search(r"(?<![A-Za-z0-9_])" + re.escape(name) + r"(?![A-Za-z0-9_])", descriptor)), None)
        if entry_kind:
            for entry in value:
                _check_entry(entry, entry_kind)
        elif "command-profile" in descriptor:
            for entry in value:
                _validate_profile(entry, PROFILE_RULES["profiles"]["command-profile"], "command-profile")
        else:
            raise Refusal("FORMAT_INVALID")
        if descriptor.startswith("nonempty") and not value:
            raise Refusal("FORMAT_INVALID")
        if descriptor.startswith("exact four") and len(value) != 4:
            raise Refusal("FORMAT_INVALID")
        if entry_kind == "argument" and [item["index"] for item in value] != list(range(len(value))):
            raise Refusal("FORMAT_INVALID")
        if entry_kind == "source_file" and [item["path"] for item in value] != sorted({item["path"] for item in value}):
            raise Refusal("FORMAT_INVALID")
        if entry_kind == "environment" and [item["name"] for item in value] != sorted({item["name"] for item in value}):
            raise Refusal("FORMAT_INVALID")
        ids = [entry.get("id") for entry in value if isinstance(entry, dict) and "id" in entry]
        if ids and (len(ids) != len(value) or ids != sorted(set(ids))):
            raise Refusal("FORMAT_INVALID")
    elif "installed_artifact" in descriptor:
        _check_entry(value, "installed_artifact")
    elif isinstance(value, str):
        if not value or len(value.encode("ascii")) > 4096:
            raise Refusal("FORMAT_INVALID")
        if field == "working_directory" and (not value.startswith("/") or os.path.normpath(value) != value):
            raise Refusal("FORMAT_INVALID")
        enum_values = {"purpose": ("INPUT_REVIEW_ONLY", "ACTION_PREFLIGHT_ONLY"),
                       "verdict": ("MATCH", "ACTIVE", "SEALED_READ_ONLY"),
                       "authorization_scope": ("BUILD_ONLY", "INDEPENDENT_REBUILD", "BUILD_IDENTITY_TEST_EXECUTION", "CODEC_TEST_EXECUTION"),
                       "mode": ("100644", "100755"), "platform": ("linux/amd64",),
                       "role": ("toolchain", "host-std", "musl-std", "crt"),
                       "self_contained": ("ON", "OFF"),
                       "static_form": ("STATIC_PIE", "STATIC_NON_PIE"),
                       "signature_algorithm": ("RSA/SHA512 primary direct signature",)}.get(field)
        if enum_values and value not in enum_values:
            raise Refusal("FORMAT_INVALID")
        if "hex32" in descriptor and not re.fullmatch(r"[0-9a-f]{32}", value):
            raise Refusal("FORMAT_INVALID")
        if field == "authorization_scope" and value not in ("BUILD_ONLY", "INDEPENDENT_REBUILD", "BUILD_IDENTITY_TEST_EXECUTION", "CODEC_TEST_EXECUTION"):
            raise Refusal("FORMAT_INVALID")
        if field == "schema" and descriptor.startswith("p08-") and value != descriptor:
            raise Refusal("FORMAT_INVALID")
        if field == "platform" and value != "linux/amd64":
            raise Refusal("FORMAT_INVALID")
        if field == "mode" and value not in ("100644", "100755"):
            raise Refusal("FORMAT_INVALID")
    else:
        raise Refusal("FORMAT_INVALID")


def validate_enrollment(profile, now):
    try:
        _validate_profile(profile, PROFILE_RULES["profiles"]["verifier-enrollment-profile"], "verifier-enrollment-profile")
    except Refusal:
        raise Refusal("STATUS_INVALID")
    if profile.get("schema") != "p08-verifier-enrollment-2":
        raise Refusal("STATUS_INVALID")
    keys = profile.get("keys")
    if not isinstance(keys, list) or len(keys) != 2:
        raise Refusal("ROLE_MISMATCH")
    roles = {k.get("role") for k in keys if isinstance(k, dict)}
    principals = [k.get("principal") for k in keys if isinstance(k, dict)]
    if roles != {"project-owner-issuer", "independent-reviewer"} or len(set(principals)) != 2:
        raise Refusal("ROLE_MISMATCH")
    wire_keys = []
    for key in keys:
        if now < key["not_before"] or now >= key["expires_at"] or key["not_before"] >= key["expires_at"]:
            raise Refusal("APPROVAL_STALE")
        if not isinstance(key.get("public_key"), str) or not key["public_key"].startswith("ssh-ed25519 "):
            raise Refusal("SIGNER_UNAUTHORIZED")
        try:
            fields = key["public_key"].split(" ")
            if len(fields) != 2:
                raise ValueError
            wire = base64.b64decode(fields[1], validate=True)
            offset = 0
            n = struct.unpack(">I", wire[offset:offset + 4])[0]; offset += 4
            algorithm = wire[offset:offset + n]; offset += n
            n = struct.unpack(">I", wire[offset:offset + 4])[0]; offset += 4
            public = wire[offset:offset + n]; offset += n
            if algorithm != b"ssh-ed25519" or len(public) != 32 or offset != len(wire):
                raise ValueError
        except Exception:
            raise Refusal("SIGNER_UNAUTHORIZED")
        if not HEX64.fullmatch(key.get("fingerprint", "")) or hashlib.sha256(wire).hexdigest() != key["fingerprint"]:
            raise Refusal("SIGNER_UNAUTHORIZED")
        wire_keys.append(wire)
    if len(wire_keys) != 2 or wire_keys[0] == wire_keys[1]:
        raise Refusal("ROLE_MISMATCH")
    return {k["role"]: k for k in keys}


def verify_signature(record_filename, raw, signature_path, profile, now, allowed_signers_root):
    if record_filename not in SIGNABLE_FIXTURES:
        raise Refusal("VERIFIER_UNAPPROVED")
    roles = validate_enrollment(profile, now)
    record = parse_record(raw, record_filename)
    role = "independent-reviewer" if record_filename in ("input-review.json", "compilation-result.json") else "project-owner-issuer"
    key = roles[role]
    principal = key["principal"]
    namespace = {
        "source-stage-acceptance.json": "symphony.p08.source-stage.v1",
        "owner-input-decision.json": "symphony.p08.input-owner.v1",
        "native-execution-grant.json": "symphony.p08.native-grant.v1",
        "generated-native-execution-grant.json": "symphony.p08.native-grant.v1",
        "input-review.json": "symphony.p08.input-review.v1",
        "compilation-result.json": "symphony.p08.build-result.v1",
    }.get(record_filename)
    if not namespace or namespace not in key["namespaces"]:
        raise Refusal("ROLE_MISMATCH")
    signer_leaf = "reviewer" if role == "independent-reviewer" else "owner"
    signer_file = Path(allowed_signers_root) / signer_leaf
    try:
        if not signature_path.is_file() or not signer_file.is_file():
            raise Refusal("VERIFIER_UNAPPROVED")
    except AttributeError:
        signature_path = Path(signature_path)
        if not signature_path.is_file() or not signer_file.is_file():
            raise Refusal("VERIFIER_UNAPPROVED")
    try:
        sigraw = _read_regular(signature_path, 4096, "SIGNATURE_INVALID")
    except OSError:
        raise Refusal("SIGNATURE_INVALID")
    if not sigraw or len(sigraw) > 4096:
        raise Refusal("SIGNATURE_INVALID")
    wire_key, sig_namespace = _decode_sshsig(sigraw)
    try:
        fields = key["public_key"].split(" ")
        expected_wire = base64.b64decode(fields[1], validate=True)
    except Exception:
        raise Refusal("SIGNER_UNAUTHORIZED")
    fingerprint = hashlib.sha256(wire_key).hexdigest()
    if wire_key != expected_wire:
        other_keys = {hashlib.sha256(base64.b64decode(k["public_key"].split(" ")[1], validate=True)).hexdigest()
                      for k in roles.values() if k is not key}
        if fingerprint in other_keys:
            raise Refusal("ROLE_MISMATCH")
        raise Refusal("SIGNER_UNAUTHORIZED")
    if sig_namespace != namespace:
        raise Refusal("SIGNATURE_INVALID")
    result = subprocess.run(["/usr/bin/ssh-keygen", "-Y", "verify", "-f", str(signer_file),
                             "-I", principal, "-n", namespace, "-s", str(signature_path)],
                            input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                            timeout=5, check=False,
                            env={"PATH": "/nonexistent", "LC_ALL": "C.UTF-8", "LANG": "C.UTF-8"})
    if len(result.stdout) > 4096 or len(result.stderr) > 4096:
        raise Refusal("VERIFIER_UNAPPROVED")
    if result.returncode:
        raise Refusal("SIGNATURE_INVALID")
    return record


def _decode_sshsig(raw):
    begin, end = b"-----BEGIN SSH SIGNATURE-----", b"-----END SSH SIGNATURE-----"
    if not raw.startswith(begin + b"\n") or not raw.endswith(end + b"\n"):
        raise Refusal("SIGNATURE_INVALID")
    encoded = b"".join(raw[len(begin)+1:-len(end)-1].splitlines())
    try:
        data = base64.b64decode(encoded, validate=True)
    except Exception:
        raise Refusal("SIGNATURE_INVALID")
    def take_string(offset):
        if offset + 4 > len(data):
            raise Refusal("SIGNATURE_INVALID")
        size = int.from_bytes(data[offset:offset+4], "big")
        start, stop = offset + 4, offset + 4 + size
        if size > len(data) or stop > len(data):
            raise Refusal("SIGNATURE_INVALID")
        return data[start:stop], stop
    # SSHSIG starts with six literal magic bytes, followed by the u32 version.
    # The remaining fields use SSH length-prefixed strings.
    pos = 6
    if data[:pos] != b"SSHSIG" or pos + 4 > len(data) or int.from_bytes(data[pos:pos+4], "big") != 1:
        raise Refusal("VERIFIER_UNAPPROVED")
    pos += 4
    key_wire, pos = take_string(pos)
    namespace, pos = take_string(pos)
    reserved, pos = take_string(pos)
    hash_alg, pos = take_string(pos)
    signature, pos = take_string(pos)
    if pos != len(data) or reserved or hash_alg not in (b"sha256", b"sha512") or not signature:
        raise Refusal("VERIFIER_UNAPPROVED")
    try:
        alg_len = int.from_bytes(key_wire[:4], "big")
        alg = key_wire[4:4+alg_len]
        key_len = int.from_bytes(key_wire[4+alg_len:8+alg_len], "big")
        key_value = key_wire[8+alg_len:8+alg_len+key_len]
        if 8 + alg_len + key_len != len(key_wire) or alg != b"ssh-ed25519" or len(key_value) != 32:
            raise Refusal("VERIFIER_UNAPPROVED")
    except (IndexError, ValueError):
        raise Refusal("VERIFIER_UNAPPROVED")
    try:
        namespace.decode("ascii")
    except UnicodeError:
        raise Refusal("SIGNATURE_INVALID")
    return key_wire, namespace.decode("ascii")


def _resolve_manifest_profiles(manifest, grant, raw_profiles):
    field_kinds = {
        "build_image_profile_sha256": "build-image-profile",
        "execution_profile_sha256": "execution-profile",
        "host_std_profile_sha256": "component-profile",
        "musl_std_profile_sha256": "component-profile",
        "crt_profile_sha256": "component-profile",
        "toolchain_profile_sha256": "component-profile",
        "linker_profile_sha256": "linker-profile",
        "rust_provenance_profile_sha256": "rust-provenance-profile",
        "source_inventory_sha256": "source-inventory",
    }
    decoded = {}
    for field, kind in field_kinds.items():
        digest = manifest[field]
        raw = raw_profiles.get(digest)
        if raw is None:
            raise Refusal("INPUTS_INCOMPLETE")
        decoded[field] = parse_profile(raw, kind)
    execution = decoded["execution_profile_sha256"]
    source_inventory = decoded["source_inventory_sha256"]
    if (source_inventory["commit"] != manifest["source_commit"] or
            source_inventory["tree"] != manifest["source_tree"] or
            manifest["source_commit"] == manifest["source_base_commit"] or
            manifest["source_tree"] == manifest["source_base_tree"]):
        raise Refusal("SOURCE_MISMATCH")
    candidates = [command for command in execution["commands"]
                  if sha256(canonical(command)) == grant["command_profile_sha256"]]
    if len(candidates) != 1 or candidates[0]["authorization_scope"] != grant["authorization_scope"]:
        raise Refusal("COMMAND_NOT_APPROVED" if manifest["schema"] == "p08-generated-input-approval-1" else "EXECUTION_PROFILE_MISMATCH")
    if not candidates[0]["argv"] or candidates[0]["argv"][0]["value"] != candidates[0]["executable"]["path"]:
        raise Refusal("EXECUTABLE_PATH_MISMATCH")
    image = decoded["build_image_profile_sha256"]
    if manifest["sbom_sha256"] != image["sbom_sha256"] or manifest["license_inventory_sha256"] != image["licenses_sha256"]:
        raise Refusal("PROVENANCE_INVALID")
    for field, role, target in (("toolchain_profile_sha256", "toolchain", "x86_64-unknown-linux-gnu"),
                                ("host_std_profile_sha256", "host-std", "x86_64-unknown-linux-gnu"),
                                ("musl_std_profile_sha256", "musl-std", "x86_64-unknown-linux-musl"),
                                ("crt_profile_sha256", "crt", "x86_64-unknown-linux-musl")):
        component = decoded[field]
        if component["role"] != role or component["target"] != target:
            raise Refusal("PROVENANCE_INVALID")
        for ref in component["entry_points"]:
            if ref["inventory_sha256"] != component["files_inventory_sha256"]:
                raise Refusal("EXECUTABLE_INVENTORY_MISMATCH")
    linker = decoded["linker_profile_sha256"]
    if (linker["entry_point"]["inventory_sha256"] != linker["files_inventory_sha256"] or
            linker["crt_profile_sha256"] != manifest["crt_profile_sha256"]):
        raise Refusal("PROVENANCE_INVALID")
    for grant_field, manifest_field in (
        ("observed_build_image_profile_sha256", "build_image_profile_sha256"),
        ("observed_crt_profile_sha256", "crt_profile_sha256"),
        ("observed_execution_profile_sha256", "execution_profile_sha256"),
        ("observed_host_std_profile_sha256", "host_std_profile_sha256"),
        ("observed_linker_profile_sha256", "linker_profile_sha256"),
        ("observed_musl_std_profile_sha256", "musl_std_profile_sha256"),
        ("observed_rust_provenance_profile_sha256", "rust_provenance_profile_sha256"),
        ("observed_source_inventory_sha256", "source_inventory_sha256"),
        ("observed_toolchain_profile_sha256", "toolchain_profile_sha256"),
    ):
        if grant[grant_field] != manifest[manifest_field]:
            raise Refusal("ACTION_BINDING_MISMATCH")
    executable_ref = candidates[0]["executable"]
    inventory_raw = raw_profiles.get(executable_ref["inventory_sha256"])
    if inventory_raw is None:
        raise Refusal("INPUTS_INCOMPLETE")
    inventory = parse_profile(inventory_raw, "input-inventory")
    if _digest_profile(inventory) != executable_ref["inventory_sha256"]:
        raise Refusal("EXECUTABLE_INVENTORY_MISMATCH")
    decoded["input_inventory"] = inventory
    return {"command": candidates[0], "execution_profile": execution, "profiles": decoded,
            "inventory": inventory}


def _digest_profile(value):
    return sha256(canonical(value))


def _observation(raw, purpose):
    expected = "review-observation-report" if purpose == "INPUT_REVIEW_ONLY" else "action-observation-report"
    other = "action-observation-report" if purpose == "INPUT_REVIEW_ONLY" else "review-observation-report"
    try:
        value = parse_profile(raw, expected)
    except Refusal as error:
        try:
            parse_profile(raw, other)
        except Refusal:
            raise error
        raise Refusal("OBSERVATION_PURPOSE_MISMATCH")
    if value["purpose"] != purpose:
        raise Refusal("OBSERVATION_PURPOSE_MISMATCH")
    return value


def _require_sidecars(value, catalog):
    """Opaque control/report references still require retained exact bytes.

    Fixed historical contract/source/Policy-A identities are checked separately.
    No sidecar supplies code or an alternate trust root.
    """
    historical = {"certificate_sha256", "manifest_sha256", "manifest_signature_sha256"}
    if isinstance(value, dict):
        for field, child in value.items():
            if field.endswith("_sha256") and field not in historical:
                if child not in catalog:
                    raise Refusal("INPUTS_INCOMPLETE")
            elif isinstance(child, (dict, list)):
                _require_sidecars(child, catalog)
    elif isinstance(value, list):
        for child in value:
            _require_sidecars(child, catalog)


def verify_bundle(bundle, trusted_context):
    """Verify an exact bundle using independently installed operator inputs.

    `source_facts` supplies actual commit/tree/parent, base commit/tree, full
    base_inventory/observed_entries and inventory_sha256. `evidence_bytes`
    retains opaque reviewed sidecars by their raw SHA-256. Neither dictionary
    authenticates itself. The appointed operator establishes their provenance.

    Generated inputs additionally require producer_bundle, producer_context
    with its authenticated historical clock/status, and producer_facts. Those
    facts name operator_id, outcome, exit_code, completed_at and sealed_at and
    must affirm consumed, complete_audit, no_live_descendants,
    exclusive_fresh_outputs, inspection_authorized, continuous_custody and
    scope_observed. Historical permission is never current launch authority.
    """
    needed = {"profile", "profiles", "status", "bundle_root", "allowed_signers_root", "accepted_profile_sha256"}
    if not isinstance(trusted_context, dict) or not needed.issubset(trusted_context):
        raise Refusal("STATUS_INVALID")
    if not isinstance(bundle, dict):
        raise Refusal("FORMAT_INVALID")
    status = trusted_context["status"]
    status_fields = {"now_min", "now_max", "trust_epoch", "clock_session_id", "monotonic_ns",
                     "operator_id", "enrollment_sha256", "current_decisions_sha256",
                     "revocations_sha256", "clock_evidence_sha256", "register_observation_sha256",
                     "policy_a_evidence_sha256", "revoked_ids"}
    if not isinstance(status, dict) or not status_fields.issubset(status):
        raise Refusal("STATUS_INVALID")
    now_min, now_max = status["now_min"], status["now_max"]
    if (not isinstance(now_min, int) or isinstance(now_min, bool) or
            not isinstance(now_max, int) or isinstance(now_max, bool) or
            now_min < 0 or now_max < now_min or now_max >= 2**64 or now_max - now_min > 30):
        raise Refusal("APPROVAL_STALE")
    if (type(status["trust_epoch"]) is not int or not 0 < status["trust_epoch"] < 2**64 or
            type(status["monotonic_ns"]) is not int or not 0 <= status["monotonic_ns"] < 2**64 or
            not isinstance(status["clock_session_id"], str) or not re.fullmatch(r"[0-9a-f]{32}", status["clock_session_id"]) or
            status["clock_session_id"] == "0" * 32 or not isinstance(status["operator_id"], str)):
        raise Refusal("STATUS_INVALID")
    for field in ("enrollment_sha256", "current_decisions_sha256", "revocations_sha256",
                  "clock_evidence_sha256", "register_observation_sha256", "policy_a_evidence_sha256"):
        if not isinstance(status[field], str) or not HEX64.fullmatch(status[field]):
            raise Refusal("STATUS_INVALID")
    if not isinstance(status["revoked_ids"], list) or any(not isinstance(x, str) for x in status["revoked_ids"]):
        raise Refusal("STATUS_INVALID")
    roles = validate_enrollment(trusted_context["profile"], now_min)
    for role_key in roles.values():
        if now_min < role_key["not_before"] or now_max >= role_key["expires_at"]:
            raise Refusal("APPROVAL_STALE")
    if any(name not in SCHEMAS and name not in ("review-observation.json", "action-observation.json",
                                                 "status-report.json", "source-inventory.json")
           and not name.endswith(".profile.json") for name in bundle):
        raise Refusal("FORMAT_INVALID")
    records = {name: parse_record(raw, name) for name, raw in bundle.items() if name in SCHEMAS}
    manifests = [n for n in ("build-input-approval.json", "generated-input-approval.json") if n in records]
    grants = [n for n in ("native-execution-grant.json", "generated-native-execution-grant.json") if n in records]
    if len(manifests) != 1 or len(grants) != 1 or not {"source-stage-acceptance.json", "input-review.json", "owner-input-decision.json"}.issubset(records):
        raise Refusal("APPROVAL_MISSING")
    mname, gname = manifests[0], grants[0]
    if (mname.startswith("generated-") != gname.startswith("generated-") or
            (mname == "generated-input-approval.json") != (gname == "generated-native-execution-grant.json")):
        raise Refusal("EXECUTION_NOT_GRANTED")
    names = {"source-stage-acceptance.json", mname, "input-review.json", "owner-input-decision.json", gname}
    if mname == "generated-input-approval.json":
        if "compilation-result.json" not in bundle:
            raise Refusal("COMPILATION_RECEIPT_MISSING")
        names.add("compilation-result.json")
    if not names.issubset(bundle):
        raise Refusal("APPROVAL_MISSING")
    source, manifest, review, owner, grant = (records[x] for x in (
        "source-stage-acceptance.json", mname, "input-review.json", "owner-input-decision.json", gname))
    hashes = {name: sha256(bundle[name]) for name in names}
    profile = trusted_context["profile"]
    trust_hash = sha256(canonical(profile))
    if trusted_context["accepted_profile_sha256"] != trust_hash or any(r.get("trust_profile_sha256") != trust_hash for r in (manifest, review, owner, grant, source)):
        raise Refusal("STATUS_INVALID")
    try:
        signer_owner = _read_regular(Path(trusted_context["allowed_signers_root"]) / "owner",4096,"VERIFIER_UNAPPROVED")
        signer_reviewer = _read_regular(Path(trusted_context["allowed_signers_root"]) / "reviewer",4096,"VERIFIER_UNAPPROVED")
    except OSError:
        raise Refusal("VERIFIER_UNAPPROVED")
    def exact_signer_line(role):
        key = roles[role]
        algorithm, encoded = key["public_key"].split(" ")
        namespaces = ",".join(sorted(key["namespaces"]))
        return (f'{key["principal"]} namespaces="{namespaces}" {algorithm} {encoded}\n').encode("ascii")
    if (signer_owner != exact_signer_line("project-owner-issuer") or
            signer_reviewer != exact_signer_line("independent-reviewer") or
            sha256(signer_owner + signer_reviewer) != profile["allowed_signers_sha256"]):
        raise Refusal("VERIFIER_UNAPPROVED")
    verifier_inventory_raw = trusted_context["profiles"].get(profile["verifier_inventory_sha256"])
    if verifier_inventory_raw is None:
        raise Refusal("VERIFIER_UNAPPROVED")
    verifier_inventory = parse_profile(verifier_inventory_raw, "input-inventory")
    if (profile["verifier_artifact"]["path"] != "/usr/bin/ssh-keygen" or
            profile["verifier_artifact"]["inventory_sha256"] != profile["verifier_inventory_sha256"]):
        raise Refusal("VERIFIER_UNAPPROVED")
    verify_installed_artifact(profile["verifier_artifact"], verifier_inventory,
        trusted_context.get("sealed_roots", ()), actual_path="/usr/bin/ssh-keygen", actual_argv0="/usr/bin/ssh-keygen")
    if source["issuer_id"] != roles["project-owner-issuer"]["principal"]:
        raise Refusal("ROLE_MISMATCH")
    if manifest["issuer_id"] != source["issuer_id"] or manifest["reviewer_id"] != roles["independent-reviewer"]["principal"]:
        raise Refusal("ROLE_MISMATCH")
    if review["reviewer_id"] != manifest["reviewer_id"] or owner["issuer_id"] != manifest["issuer_id"]:
        raise Refusal("ROLE_MISMATCH")
    if source["scope"] != "SOURCE_PREPARATION_ONLY" or source["decision"] != "ACCEPT":
        raise Refusal("ACCEPTANCE_UNAUTHENTICATED")
    if manifest["source_stage_acceptance_sha256"] != hashes["source-stage-acceptance.json"] or review["source_stage_acceptance_sha256"] != hashes["source-stage-acceptance.json"] or owner["source_stage_acceptance_sha256"] != hashes["source-stage-acceptance.json"]:
        raise Refusal("CHAIN_MISMATCH")
    if review["manifest_sha256"] != hashes[mname] or owner["manifest_sha256"] != hashes[mname] or grant["manifest_sha256"] != hashes[mname]:
        raise Refusal("CHAIN_MISMATCH")
    if owner["review_report_sha256"] != hashes["input-review.json"] or grant["review_report_sha256"] != hashes["input-review.json"]:
        raise Refusal("CHAIN_MISMATCH")
    signature_hashes = {}
    for filename in ("source-stage-acceptance.json", "input-review.json", "owner-input-decision.json", gname):
        sigpath = (Path(trusted_context["bundle_root"]) / filename).with_suffix(".sshsig")
        try:
            sigraw = _read_regular(sigpath,4096,"ACCEPTANCE_UNAUTHENTICATED" if filename == "source-stage-acceptance.json" else "APPROVAL_MISSING")
        except OSError:
            raise Refusal("ACCEPTANCE_UNAUTHENTICATED" if filename == "source-stage-acceptance.json" else "APPROVAL_MISSING")
        if not sigraw or len(sigraw) > 4096:
            raise Refusal("SIGNATURE_INVALID")
        signature_hashes[filename] = sha256(sigraw)
    if owner["review_signature_sha256"] != signature_hashes["input-review.json"]:
        raise Refusal("CHAIN_MISMATCH")
    if grant["owner_signature_sha256"] != signature_hashes["owner-input-decision.json"] or grant["review_signature_sha256"] != signature_hashes["input-review.json"]:
        raise Refusal("CHAIN_MISMATCH")
    if grant["owner_decision_sha256"] != hashes["owner-input-decision.json"]:
        raise Refusal("CHAIN_MISMATCH")
    if manifest["source_commit"] != grant["source_commit"] or manifest["source_tree"] != grant["source_tree"]:
        raise Refusal("SOURCE_MISMATCH")
    if (source["source_commit"] != manifest["source_base_commit"] or source["source_tree"] != manifest["source_base_tree"] or
            source["source_parent"] != "e2e87701c73c0f55fdef040d29c57bb8ad2b3918"):
        raise Refusal("SOURCE_MISMATCH")
    source_facts = trusted_context.get("source_facts")
    if (not isinstance(source_facts, dict) or source_facts.get("commit") != manifest["source_commit"] or
            source_facts.get("tree") != manifest["source_tree"] or source_facts.get("parent") != source["source_commit"] or
            source_facts.get("inventory_sha256") != manifest["source_inventory_sha256"] or
            source_facts.get("base_commit") != source["source_commit"]):
        raise Refusal("SOURCE_MISMATCH")
    if grant["trust_epoch"] != status["trust_epoch"] or grant["run_id"] != status.get("run_id", grant["run_id"]):
        raise Refusal("STATUS_INVALID")
    allowed_actions = ("BUILD_ONLY", "INDEPENDENT_REBUILD") if mname == "build-input-approval.json" else ("BUILD_IDENTITY_TEST_EXECUTION", "CODEC_TEST_EXECUTION")
    if grant["authorization_scope"] not in allowed_actions:
        raise Refusal("EXECUTION_NOT_GRANTED")
    for name in names:
        raw = bundle[name]
        disk = Path(trusted_context["bundle_root"]) / name
        try:
            if _read_regular(disk,_record_limit(name),"CHAIN_MISMATCH") != raw:
                raise Refusal("CHAIN_MISMATCH")
        except OSError:
            raise Refusal("CHAIN_MISMATCH")
        if name not in (mname, "compilation-result.json"):
            verify_signature(name, raw, disk.with_suffix(".sshsig"), profile, now_min,
                             trusted_context["allowed_signers_root"])
    authenticated_grant = {"grant_id": grant["grant_id"], "run_id": grant["run_id"],
                           "nonce": grant["nonce"], "authorization_scope": grant["authorization_scope"],
                           "trust_epoch": grant["trust_epoch"]}
    try:
        for record in (manifest, review, owner, grant):
            if now_min < record["issued_at"] or now_max >= record["expires_at"]:
                raise Refusal("APPROVAL_STALE")
            if "not_before" in record:
                if not record["issued_at"] <= record["not_before"] < record["expires_at"] or now_min < record["not_before"]:
                    raise Refusal("APPROVAL_STALE")
        if manifest["expires_at"] - manifest["issued_at"] > profile["approval_max_age_s"] or review["expires_at"] - review["issued_at"] > profile["approval_max_age_s"] or owner["expires_at"] - owner["issued_at"] > profile["approval_max_age_s"]:
            raise Refusal("APPROVAL_STALE")
        if grant["expires_at"] - grant["issued_at"] > profile["lease_max_s"] or not 0 < grant["max_duration_s"] <= profile["lease_max_s"]:
            raise Refusal("APPROVAL_STALE")
        ceiling = min(manifest["expires_at"], review["expires_at"], owner["expires_at"],
                      *(key["expires_at"] for key in roles.values()))
        floor = max(manifest["not_before"], review["issued_at"], owner["not_before"],
                    *(key["not_before"] for key in roles.values()))
        if (grant["not_before"] < floor or grant["expires_at"] > ceiling or
                grant["not_before"] + grant["max_duration_s"] > grant["expires_at"]):
            raise Refusal("APPROVAL_STALE")
        for record, role in ((source, "project-owner-issuer"), (manifest, "project-owner-issuer"),
                             (review, "independent-reviewer"), (owner, "project-owner-issuer"),
                             (grant, "project-owner-issuer")):
            key = roles[role]
            if record["issued_at"] < key["not_before"] or record["issued_at"] >= key["expires_at"]:
                raise Refusal("APPROVAL_STALE")
        if not (source["issued_at"] <= manifest["issued_at"] and source["issued_at"] <= review["issued_at"] and source["issued_at"] <= owner["issued_at"]):
            raise Refusal("CHAIN_MISMATCH")
        raw_profiles = trusted_context["profiles"]
        if not isinstance(raw_profiles, dict):
            raise Refusal("CHAIN_MISMATCH")
        for digest, raw in raw_profiles.items():
            if not isinstance(raw, bytes) or sha256(raw) != digest:
                raise Refusal("CHAIN_MISMATCH")
        resolved = _resolve_manifest_profiles(manifest, grant, raw_profiles)
        evidence = trusted_context.get("evidence_bytes", {})
        if not isinstance(evidence, dict) or any(not isinstance(raw, bytes) or sha256(raw) != digest for digest, raw in evidence.items()):
            raise Refusal("INPUTS_INCOMPLETE")
        catalog = dict(raw_profiles, **evidence)
        catalog[sha256(signer_owner + signer_reviewer)] = signer_owner + signer_reviewer
        catalog[trust_hash] = canonical(profile)
        for raw in raw_profiles.values():
            try:
                candidate = json.loads(raw)
            except (ValueError, UnicodeError):
                continue
            if isinstance(candidate, dict) and candidate.get("schema") == "p08-input-inventory-1":
                for entry in candidate.get("entries", []):
                    catalog[sha256(canonical(entry))] = canonical(entry)
        if any(digest not in catalog for digest in (source["review_archive_sha256"],
                                                   source["independent_review_sha256"], review["findings_sha256"])):
            raise Refusal("INPUTS_INCOMPLETE")
        _require_sidecars(profile, catalog)
        for decoded in resolved["profiles"].values():
            _require_sidecars(decoded, catalog)
        for component_field in ("host_std_profile_sha256", "musl_std_profile_sha256", "crt_profile_sha256", "toolchain_profile_sha256", "linker_profile_sha256"):
            component = resolved["profiles"][component_field]
            component_inventory = _closed_profile(raw_profiles, component["files_inventory_sha256"], "input-inventory")
            refs = component.get("entry_points", [component.get("entry_point")])
            for ref in refs:
                verify_installed_artifact(ref, component_inventory, trusted_context.get("sealed_roots", ()))
        if mname == "generated-input-approval.json":
            _verify_generated_transition(bundle, trusted_context, records, manifest, grant,
                                        hashes, profile, roles, raw_profiles, resolved,
                                        status, now_min, now_max)
        base_entries = source_facts.get("base_inventory")
        current_entries = resolved["profiles"]["source_inventory_sha256"]["entries"]
        if not isinstance(base_entries, list) or len(base_entries) != 407 or len(current_entries) != 407 or source_facts.get("base_tree") != source["source_tree"]:
            raise Refusal("SOURCE_MISMATCH")
        base_by_path = {entry.get("path"): entry for entry in base_entries if isinstance(entry, dict)}
        current_by_path = {entry.get("path"): entry for entry in current_entries if isinstance(entry, dict)}
        if len(base_by_path) != 407 or len(current_by_path) != 407 or set(base_by_path) != set(current_by_path):
            raise Refusal("SOURCE_MISMATCH")
        changed_paths = [path for path in base_by_path if base_by_path[path] != current_by_path[path]]
        identity_path = "native/gate2/protocol/tests/locked_build_identity.rs"
        if (changed_paths != [identity_path] or
                current_by_path[identity_path].get("sha256") != manifest["identity_test_sha256"] or
                source_facts.get("observed_entries") != current_entries):
            raise Refusal("SOURCE_MISMATCH")
        review_raw = raw_profiles.get(review["review_observation_sha256"])
        if review_raw is None:
            raise Refusal("OBSERVATION_UNAUTHENTICATED")
        review_observation = _observation(review_raw, "INPUT_REVIEW_ONLY")
        _require_sidecars(review_observation, dict(catalog, **{hashes[mname]: bundle[mname]}))
        if (review_observation["purpose"] != "INPUT_REVIEW_ONLY" or review_observation["verdict"] != "MATCH" or
                review_observation["manifest_sha256"] != hashes[mname] or
                review_observation["review_id"] != review["review_id"] or
                review_observation["reviewer_id"] != review["reviewer_id"] or
                review_observation["source_commit"] != manifest["source_commit"] or
                review_observation["source_tree"] != manifest["source_tree"] or
                review_observation["trust_profile_sha256"] != trust_hash):
            raise Refusal("REVIEW_BINDING_INVALID")
        if not manifest["issued_at"] <= review_observation["observed_at"] <= review["issued_at"] <= owner["issued_at"]:
            raise Refusal("REVIEW_BINDING_INVALID")
        if review["issued_at"] - review_observation["observed_at"] > profile["approval_max_age_s"]:
            raise Refusal("REVIEW_OBSERVATION_STALE")
        _match_observed_profiles(review_observation["profiles"], manifest, raw_profiles=raw_profiles)
        observation_hash = grant["action_observation_sha256"]
        obs_raw = raw_profiles.get(observation_hash)
        if obs_raw is None:
            raise Refusal("OBSERVATION_UNAUTHENTICATED")
        observation = _observation(obs_raw, "ACTION_PREFLIGHT_ONLY")
        observation_catalog = dict(catalog)
        for filename, digest in hashes.items():
            observation_catalog[digest] = bundle[filename]
        observation_catalog[grant["command_profile_sha256"]] = canonical(resolved["command"])
        observation_catalog[trust_hash] = canonical(profile)
        _require_sidecars(observation, observation_catalog)
        if observation["purpose"] != "ACTION_PREFLIGHT_ONLY" or observation["verdict"] != "MATCH":
            raise Refusal("OBSERVATION_PURPOSE_MISMATCH")
        if (observation["grant_id"] != grant["grant_id"] or observation["run_id"] != grant["run_id"] or
                observation["nonce"] != grant["nonce"] or observation["manifest_sha256"] != hashes[mname] or
                observation["owner_decision_sha256"] != hashes["owner-input-decision.json"] or
                observation["review_report_sha256"] != hashes["input-review.json"] or
                observation["command_profile_sha256"] != grant["command_profile_sha256"] or
                observation["authorization_scope"] != grant["authorization_scope"] or
                observation["source_commit"] != manifest["source_commit"] or
                observation["source_tree"] != manifest["source_tree"] or
                observation["trust_profile_sha256"] != trust_hash or
                observation["clock_session_id"] != status["clock_session_id"] or
                observation["observed_at"] > grant["issued_at"] or
                observation["observed_at"] < observation["observation_started_at"] or
                observation["observation_started_at"] < max(manifest["issued_at"], review["issued_at"], owner["issued_at"])):
            raise Refusal("ACTION_BINDING_MISMATCH")
        _match_observed_profiles(observation["profiles"], manifest, grant, raw_profiles)
        if (status["monotonic_ns"] < observation["completed_monotonic_ns"] or
                status["monotonic_ns"] - observation["completed_monotonic_ns"] > profile["action_observation_max_age_s"] * 1_000_000_000 or
                now_max - observation["observed_at"] > profile["action_observation_max_age_s"]):
            raise Refusal("ACTION_OBSERVATION_STALE")
        status_raw = raw_profiles.get(grant["status_report_sha256"])
        if status_raw is None:
            raise Refusal("STATUS_INVALID")
        status_report = parse_profile(status_raw, "status-report")
        if (status_report["verdict"] != "ACTIVE" or status_report["trust_epoch"] != status["trust_epoch"] or
                status_report["run_id"] != grant["run_id"] or status_report["enrollment_sha256"] != status["enrollment_sha256"] or
                status_report["operator_id"] != status["operator_id"] or
                not now_min <= status_report["observed_at"] <= now_max or
                any(status_report[key] != status[key] for key in ("current_decisions_sha256", "revocations_sha256", "clock_evidence_sha256", "register_observation_sha256", "policy_a_evidence_sha256"))):
            raise Refusal("STATUS_INVALID")
        result_records = {"source-stage-acceptance.json": source, mname: manifest,
                          "input-review.json": review, "owner-input-decision.json": owner, gname: grant}
        active_ids = {record.get(key) for record in result_records.values()
                      for key in ("approval_id", "decision_id", "review_id", "grant_id", "run_id", "nonce") if record.get(key)}
        if active_ids.intersection(status["revoked_ids"]):
            raise Refusal("STATUS_INVALID")
        return {"records": result_records, "roles": roles,
                "profile_sha256": trust_hash, "command": resolved["command"],
                "execution_profile": resolved["execution_profile"],
                "inventory": resolved["inventory"], "profiles": resolved["profiles"],
                "action_observation": observation, "manifest": manifest, "grant": grant}
    except Refusal as error:
        error.authenticated_grant = authenticated_grant
        raise


def _closed_profile(raw_profiles, digest, kind):
    raw = raw_profiles.get(digest)
    if raw is None:
        raise Refusal("INPUTS_INCOMPLETE")
    value = parse_profile(raw, kind)
    if sha256(raw) != digest:
        raise Refusal("CHAIN_MISMATCH")
    return value


def _verify_generated_transition(bundle, context, records, manifest, grant, hashes,
                                 profile, roles, raw_profiles, resolved, status,
                                 now_min, now_max):
    """Authenticate historical build provenance before accepting generated inputs.

    The caller supplies the producer bundle and its independently authenticated
    historical context. That context describes the producer's completion-time
    validity window. Current revocations still come from the current status.
    """
    producer_bundle = context.get("producer_bundle")
    producer_context = context.get("producer_context")
    producer_facts = context.get("producer_facts")
    if not isinstance(producer_bundle, dict) or not isinstance(producer_context, dict) or not isinstance(producer_facts, dict):
        raise Refusal("BUILD_PROVENANCE_MISMATCH")
    if "generated-input-approval.json" in producer_bundle:
        raise Refusal("PROVENANCE_CYCLE_INVALID")
    producer = verify_bundle(producer_bundle, producer_context)
    pm = producer["manifest"]
    pg = producer["grant"]
    po = producer["records"]["owner-input-decision.json"]
    pr = producer["records"]["input-review.json"]
    if pm.get("schema") != "p08-build-input-approval-1" or pg.get("schema") != "p08-native-execution-grant-2":
        raise Refusal("PROVENANCE_INVALID")
    if pg["authorization_scope"] not in ("BUILD_ONLY", "INDEPENDENT_REBUILD"):
        raise Refusal("PROVENANCE_INVALID")
    producer_ids = {pg[k] for k in ("grant_id", "run_id", "nonce")}
    producer_ids.update((pm["approval_id"], pr["review_id"], po["decision_id"]))
    if producer_ids.intersection(status["revoked_ids"]):
        raise Refusal("STATUS_INVALID")
    b = records["compilation-result.json"]
    braw = bundle["compilation-result.json"]
    bsignature = (Path(context["bundle_root"]) / "compilation-result.sshsig")
    try:
        bsig_raw = _read_regular(bsignature,4096,"COMPILATION_RECEIPT_MISSING")
    except OSError:
        raise Refusal("COMPILATION_RECEIPT_MISSING")
    if sha256(bsig_raw) != manifest["compilation_result_signature_sha256"]:
        raise Refusal("COMPILATION_RECEIPT_UNAUTHENTICATED")
    if sha256(braw) != manifest["compilation_result_sha256"]:
        raise Refusal("COMPILATION_RECEIPT_MISSING")
    try:
        producer_grant_signature = _read_regular(Path(producer_context["bundle_root"]) / "native-execution-grant.sshsig",4096,"BUILD_PROVENANCE_MISMATCH")
    except (KeyError, OSError):
        raise Refusal("BUILD_PROVENANCE_MISMATCH")
    b_ids = {
        "producer_manifest_sha256": sha256(producer_bundle["build-input-approval.json"]),
        "producer_review_sha256": sha256(producer_bundle["input-review.json"]),
        "producer_owner_decision_sha256": sha256(producer_bundle["owner-input-decision.json"]),
        "producer_grant_sha256": sha256(producer_bundle["native-execution-grant.json"]),
        "producer_grant_signature_sha256": sha256(producer_grant_signature),
        "producer_grant_id": pg["grant_id"], "producer_run_id": pg["run_id"],
        "producer_nonce": pg["nonce"],
        "producer_command_profile_sha256": pg["command_profile_sha256"],
        "source_commit": pm["source_commit"], "source_tree": pm["source_tree"],
        "trust_profile_sha256": producer["profile_sha256"],
        "reviewer_id": pm["reviewer_id"],
    }
    if any(b.get(field) != value for field, value in b_ids.items()):
        raise Refusal("BUILD_PROVENANCE_MISMATCH")
    if (b["operator_id"] != producer_facts.get("operator_id") or
            b["reviewer_id"] != roles["independent-reviewer"]["principal"] or
            b["reviewer_id"] != pm["reviewer_id"] or
            producer_facts.get("outcome") != "SUCCESS_ELIGIBLE_OUTPUTS" or
            producer_facts.get("exit_code") != 0 or
            not b["started_at"] <= b["completed_at"] <= b["issued_at"] or
            b["completed_at"] != producer_facts.get("completed_at") or
            b["issued_at"] < producer_facts.get("sealed_at") or
            b["generated_inputs_profile_sha256"] != manifest["generated_inputs_profile_sha256"] or
            b["source_commit"] != manifest["source_commit"] or b["source_tree"] != manifest["source_tree"] or
            manifest["issued_at"] < b["issued_at"] or
            b["issued_at"] > now_max or
            not pg["not_before"] <= b["started_at"] <= b["completed_at"] < pg["expires_at"] or
            b["completed_at"] - b["started_at"] > pg["max_duration_s"]):
        raise Refusal("PRODUCER_NOT_ELIGIBLE")
    if producer_facts.get("continuous_custody") is not True:
        raise Refusal("GENERATED_CUSTODY_INVALID")
    if any(producer_facts.get(field) is not True for field in (
            "consumed", "complete_audit", "no_live_descendants", "exclusive_fresh_outputs",
            "inspection_authorized", "scope_observed")):
        raise Refusal("PRODUCER_NOT_ELIGIBLE")
    try:
        verify_signature("compilation-result.json", braw, bsignature, profile, now_min,
                         context["allowed_signers_root"])
    except Refusal as error:
        raise Refusal("COMPILATION_RECEIPT_UNAUTHENTICATED") from error
    qhash = manifest["generated_inputs_profile_sha256"]
    if b["generated_inputs_profile_sha256"] != qhash:
        raise Refusal("BUILD_PROVENANCE_MISMATCH")
    q = _closed_profile(raw_profiles, qhash, "generated-inputs-profile")
    ehash = q["compilation_evidence_sha256"]
    evidence = _closed_profile(raw_profiles, ehash, "compilation-evidence-report")
    ihash = q["files_inventory_sha256"]
    inventory = _closed_profile(raw_profiles, ihash, "input-inventory")
    custody = _closed_profile(raw_profiles, q["custody_evidence_sha256"], "generated-custody-report")
    generated_catalog = {**raw_profiles, **context.get("evidence_bytes", {})}
    for filename, raw in producer_bundle.items():
        generated_catalog[sha256(raw)] = raw
        if filename != "build-input-approval.json":
            sigraw = _read_regular((Path(producer_context["bundle_root"]) / filename).with_suffix('.sshsig'),4096,"BUILD_PROVENANCE_MISMATCH")
            generated_catalog[sha256(sigraw)] = sigraw
    generated_catalog[pg["command_profile_sha256"]] = canonical(producer["command"])
    for entry in inventory["entries"]:
        generated_catalog[sha256(canonical(entry))] = canonical(entry)
    for value in (q, evidence, custody):
        _require_sidecars(value, generated_catalog)
    producer_refs = {
        "producer_manifest_sha256": sha256(producer_bundle["build-input-approval.json"]),
        "producer_grant_sha256": sha256(producer_bundle["native-execution-grant.json"]),
        "compilation_evidence_sha256": ehash,
        "files_inventory_sha256": ihash,
        "custody_evidence_sha256": sha256(raw_profiles[q["custody_evidence_sha256"]]),
        "source_commit": pm["source_commit"], "source_tree": pm["source_tree"],
    }
    if any(q.get(k) != v for k, v in producer_refs.items()):
        raise Refusal("BUILD_PROVENANCE_MISMATCH")
    if (custody["verdict"] != "SEALED_READ_ONLY" or
            custody["producer_grant_sha256"] != producer_refs["producer_grant_sha256"] or
            custody["operator_id"] != producer_facts.get("operator_id") or
            custody["sealed_at"] > b["issued_at"] or custody["sealed_at"] < b["completed_at"] or
            custody["inventory_sha256"] != ihash or evidence["output_inventory_sha256"] != ihash or
            evidence["custody_evidence_sha256"] != q["custody_evidence_sha256"] or
            evidence["started_at"] != b["started_at"] or
            evidence["exit_code"] != 0 or evidence["completed_at"] != b["completed_at"] or
            b["compilation_evidence_sha256"] != ehash or
            any(evidence.get(k) != b.get(k) for k in ("producer_manifest_sha256", "producer_review_sha256", "producer_owner_decision_sha256", "producer_grant_signature_sha256", "producer_grant_sha256", "producer_grant_id", "producer_run_id", "producer_nonce", "producer_command_profile_sha256", "source_commit", "source_tree"))):
        raise Refusal("GENERATED_CUSTODY_INVALID")
    if not q["executables"] or [x["id"] for x in q["executables"]] != sorted({x["id"] for x in q["executables"]}):
        raise Refusal("GENERATED_TARGET_UNSUPPORTED")
    generated_refs = {canonical(x) for x in q["executables"]}
    command_refs = {canonical(command["executable"]) for command in resolved["execution_profile"]["commands"]
                    if command["authorization_scope"] in ("BUILD_IDENTITY_TEST_EXECUTION", "CODEC_TEST_EXECUTION")}
    if canonical(resolved["command"]["executable"]) not in generated_refs or canonical(resolved["command"]["executable"]) not in command_refs:
        raise Refusal("COMMAND_NOT_APPROVED")
    if resolved["command"]["authorization_scope"] not in ("BUILD_IDENTITY_TEST_EXECUTION", "CODEC_TEST_EXECUTION"):
        raise Refusal("COMMAND_NOT_APPROVED")
    if any(x["id"] not in ("codec_test", "locked_build_identity") for x in q["executables"]):
        raise Refusal("GENERATED_TARGET_UNSUPPORTED")
    if any(x["provenance_sha256"] != ehash for x in q["executables"]):
        for ref in q["executables"]:
            if ref["provenance_sha256"] != ehash:
                try:
                    _closed_profile(raw_profiles, ref["provenance_sha256"], "compilation-evidence-report")
                except Refusal:
                    raise Refusal("PROVENANCE_CYCLE_INVALID")
        raise Refusal("BUILD_PROVENANCE_MISMATCH")
    if any(x["inventory_sha256"] != ihash for x in q["executables"]):
        raise Refusal("GENERATED_INPUT_MISMATCH")
    if not set(x["path"] for x in q["executables"]).issubset({x["path"] for x in inventory["entries"]}):
        raise Refusal("EXECUTABLE_INVENTORY_MISMATCH")
    expected_scope = {"locked_build_identity": "BUILD_IDENTITY_TEST_EXECUTION", "codec_test": "CODEC_TEST_EXECUTION"}
    if expected_scope[resolved["command"]["executable"]["id"]] != grant["authorization_scope"]:
        raise Refusal("COMMAND_NOT_APPROVED")
    if grant["observed_generated_inputs_profile_sha256"] != qhash:
        raise Refusal("ACTION_BINDING_MISMATCH")
    for ref in q["executables"]:
        try:
            verify_installed_artifact(ref, inventory, context.get("sealed_roots", ()))
        except Refusal as error:
            raise Refusal("GENERATED_INPUT_MISMATCH") from error
    producer_manifest = pm
    for field in ("source_commit", "source_tree", "trust_profile_sha256", "build_image_profile_sha256",
                  "host_std_profile_sha256", "musl_std_profile_sha256",
                  "crt_profile_sha256", "toolchain_profile_sha256", "linker_profile_sha256",
                  "rust_provenance_profile_sha256", "source_inventory_sha256"):
        if manifest.get(field) != producer_manifest.get(field):
            raise Refusal("BUILD_PROVENANCE_MISMATCH")
    if manifest["reviewer_id"] != roles["independent-reviewer"]["principal"]:
        raise Refusal("ROLE_MISMATCH")
    new_ids = {manifest["approval_id"], records["input-review.json"]["review_id"],
               records["owner-input-decision.json"]["decision_id"], grant["grant_id"], grant["run_id"], grant["nonce"]}
    if len(new_ids) != 6 or new_ids.intersection(producer_ids):
        raise Refusal("CHAIN_MISMATCH")


def _match_observed_profiles(observed, manifest, grant=None, raw_profiles=None):
    if not isinstance(observed, list):
        raise Refusal("OBSERVATION_UNAUTHENTICATED")
    required = {key.removesuffix("_sha256"): value for key, value in manifest.items()
                if (key.endswith("_profile_sha256") and key != "trust_profile_sha256") or key == "source_inventory_sha256"}
    if grant and grant.get("observed_generated_inputs_profile_sha256"):
        required["generated_inputs_profile"] = grant["observed_generated_inputs_profile_sha256"]
    actual = {item.get("id"): item.get("sha256") for item in observed if isinstance(item, dict)}
    if len(actual) != len(observed) or actual != required:
        raise Refusal("OBSERVATION_UNAUTHENTICATED")
    if raw_profiles is not None and any(item["bytes"] != len(raw_profiles.get(item["sha256"], b"")) for item in observed):
        raise Refusal("OBSERVATION_UNAUTHENTICATED")


def verify_installed_artifact(ref, inventory, sealed_roots, actual_path=None, actual_argv0=None):
    if not isinstance(ref, dict) or not isinstance(inventory, dict) or inventory.get("schema") != "p08-input-inventory-1":
        raise Refusal("FORMAT_INVALID")
    _check_entry(ref, "installed_artifact")
    _validate_profile(inventory, PROFILE_RULES["profiles"]["input-inventory"], "input-inventory")
    path = ref.get("path")
    if not isinstance(path, str) or not path.startswith("/") or path.startswith("//") or os.path.normpath(path) != path:
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    if actual_path is not None and actual_path != path or actual_argv0 is not None and actual_argv0 != path:
        raise Refusal("EXECUTABLE_PATH_MISMATCH")
    entries = inventory.get("entries")
    if not isinstance(entries, list):
        raise Refusal("FORMAT_INVALID")
    if ref.get("inventory_sha256") != sha256(canonical(inventory)):
        raise Refusal("EXECUTABLE_INVENTORY_MISMATCH")
    path_entries = [x for x in entries if isinstance(x, dict) and x.get("path") == path]
    if len(path_entries) != 1:
        raise Refusal("EXECUTABLE_INVENTORY_MISMATCH")
    entry = path_entries[0]
    if ref.get("path_entry_sha256") != sha256(canonical(entry)):
        raise Refusal("EXECUTABLE_INVENTORY_MISMATCH")
    real = Path(path)
    roots = [Path(sealed_roots)] if isinstance(sealed_roots, (str, os.PathLike)) else [Path(root) for root in sealed_roots]
    try:
        if not real.is_absolute() or not any(os.path.commonpath((str(real), str(root))) == str(root) for root in roots):
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    except ValueError:
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    # Parent components must be actual directories. Only the named leaf may be
    # a symlink, and each hop must match the declared inventory chain.
    current = real.parent
    while current != current.parent:
        try:
            st_parent = current.lstat()
        except OSError:
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
        if not __import__("stat").S_ISDIR(st_parent.st_mode):
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
        current = current.parent
    chain = ref.get("symlink_chain")
    if not isinstance(chain, list) or len(chain) > 32 or len(chain) != len(set(chain)):
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    expected_chain = []
    target = real
    for _ in range(33):
        for parent in target.parents:
            try:
                if not stat.S_ISDIR(parent.lstat().st_mode):
                    raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
            except OSError:
                raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
        try:
            st = target.lstat()
        except OSError:
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
        if not __import__("stat").S_ISLNK(st.st_mode):
            break
        matches = [e for e in entries if e.get("path") == str(target)]
        if len(matches) != 1 or matches[0].get("kind") != "symlink":
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
        if (matches[0]["resolved_path"] != ref["resolved_path"] or
                matches[0]["resolved_sha256"] != ref["sha256"]):
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
        expected_chain.append(sha256(canonical(matches[0])))
        link = os.readlink(target)
        if not link or "\x00" in link or not link.isascii() or len(link.encode("ascii")) > 512:
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
        if matches[0].get("target") != link:
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
        candidate = Path(link) if os.path.isabs(link) else target.parent / link
        target = Path(os.path.normpath(candidate))
        try:
            inside_root = any(os.path.commonpath((str(target), str(root))) == str(root) for root in roots)
        except ValueError:
            inside_root = False
        if not inside_root:
            raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    else:
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    if chain != expected_chain:
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    endpoints = [e for e in entries if e.get("path") == str(target)]
    if len(endpoints) != 1:
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    endpoint = endpoints[0]
    if (target != Path(ref.get("resolved_path", "")) or endpoint.get("kind") != "regular" or
            ref.get("resolved_entry_sha256") != sha256(canonical(endpoint)) or
            endpoint.get("sha256") != ref.get("sha256") or endpoint.get("bytes") != ref.get("bytes")):
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    if not __import__("stat").S_ISREG(st.st_mode):
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    if endpoint.get("mode") != format(stat.S_IMODE(st.st_mode), "04o"):
        raise Refusal("EXECUTABLE_INVENTORY_MISMATCH")
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(target, flags)
    except OSError:
        raise Refusal("EXECUTABLE_RESOLUTION_INVALID")
    try:
        before = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_mode, before.st_size) != (st.st_dev, st.st_ino, st.st_mode, st.st_size):
            raise Refusal("CUSTODY_FAILURE")
        digest = hashlib.sha256()
        total = 0
        while True:
            chunk = os.read(fd, 65536)
            if not chunk:
                break
            total += len(chunk)
            if total > ref.get("bytes", -1):
                raise Refusal("CUSTODY_FAILURE")
            digest.update(chunk)
        after = os.fstat(fd)
        if (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
            raise Refusal("CUSTODY_FAILURE")
    finally:
        os.close(fd)
    if digest.hexdigest() != ref.get("sha256") or total != ref.get("bytes"):
        raise Refusal("EXECUTABLE_INVENTORY_MISMATCH")
    return entry


def main():
    # Source acceptance does not install a trusted context or enroll an issuer.
    raise Refusal("INDEPENDENT_VERIFIER_INSTALLATION_NOT_APPROVED")


if __name__ == "__main__":
    try:
        main()
    except Refusal as error:
        raise SystemExit(error.code)
