"""Independent descriptor/evidence inspection; no producer imports or acceptance.

This reader supplies observations for a separately appointed verifier. Synthetic
key validation is not a production authentication or principal-separation proof.
"""

import hashlib
import hmac
import json
import os
import stat


class Unqualified(RuntimeError):
    """Independent operational acceptance has no qualified deployment boundary."""


class InvalidEvidence(ValueError):
    """Retained evidence is malformed, incomplete in framing, or unauthenticated."""


class CustodyMismatch(InvalidEvidence):
    """An observed identity or retained custody binding does not match."""


class ObservationUncertain(InvalidEvidence):
    """The observation is unstable or unavailable; no completed verdict exists."""


def _encode(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def _unique(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidEvidence("duplicate JSON member")
        result[key] = value
    return result


def read_history(records_fd, supervisor_key, custody_key):
    """Authenticate original records and received receipts without producer code.

    A valid unmatched proposal is retained as pending, never accepted as a
    committed transition. This does not reauthorize or resume its controller.
    Receipt expiry is checked by the receiving controller at admission time;
    this reader validates historical binding without treating old expiry as a
    defect in an otherwise authenticated historical record.
    """
    names = sorted(os.listdir(records_fd))
    if not names or len(names) > 2048:
        raise InvalidEvidence("empty or over-limit journal")
    previous = "0" * 64
    pending = None
    authenticated = []
    halted = False
    try:
        for sequence, name in enumerate(names, 1):
            if name != f"{sequence:06d}.json":
                raise InvalidEvidence("missing, extra or out-of-order record")
            fd = open_readonly(records_fd, name)
            try:
                identity = inspect_file(fd, limit=65536)
                if identity["mode"] != 0o400:
                    raise InvalidEvidence("evidence metadata mismatch")
                raw = os.pread(fd, 65537, 0)
            finally:
                os.close(fd)
            item = json.loads(raw, object_pairs_hook=_unique)
            if set(item) != {"record", "mac"} or raw != _encode(item) + b"\n":
                raise InvalidEvidence("noncanonical record framing")
            record = item["record"]
            if set(record) != {"scope", "namespace", "sequence", "previous", "kind", "case", "payload"}:
                raise InvalidEvidence("invalid record schema")
            body = _encode(record)
            expected = hmac.new(supervisor_key, body, "sha256").hexdigest()
            if not isinstance(item["mac"], str) or not hmac.compare_digest(expected, item["mac"]):
                raise InvalidEvidence("supervisor authentication mismatch")
            if (record["scope"] != "synthetic"
                    or record["namespace"] != "JCSchoeman96/symphony/ACQ-EXEC-06/B1/synthetic"
                    or type(record["sequence"]) is not int or record["sequence"] != sequence
                    or record["previous"] != previous):
                raise InvalidEvidence("scope, sequence or previous-record mismatch")
            current_hash = hashlib.sha256(body).hexdigest()
            kind = record["kind"]
            if sequence == 1:
                if kind != "session" or record["case"] != "":
                    raise InvalidEvidence("missing session boundary")
            elif kind.startswith("pending_"):
                if pending is not None:
                    raise InvalidEvidence("new proposal bypasses an unconfirmed predecessor")
                pending = (record, current_hash)
            elif kind.startswith("confirmed_"):
                if pending is None or kind != "confirmed_" + pending[0]["kind"][8:]:
                    raise InvalidEvidence("confirmation has no matching proposal")
                proposal, proposal_hash = pending
                payload = record["payload"]
                if (set(payload) != {"proposal", "receipt"} or payload["proposal"] != proposal_hash
                        or record["case"] != proposal["case"]):
                    raise InvalidEvidence("confirmation binds another proposal")
                receipt = payload["receipt"]
                if set(receipt) != {"actor", "body", "mac"} or receipt["actor"] != "C":
                    raise InvalidEvidence("invalid custody receipt")
                signed = {"actor": "C", "body": receipt["body"]}
                expected_mac = hmac.new(custody_key, _encode(signed), "sha256").hexdigest()
                if not isinstance(receipt["mac"], str) or not hmac.compare_digest(expected_mac, receipt["mac"]):
                    raise InvalidEvidence("custody authentication mismatch")
                ack = receipt["body"]
                if (set(ack) != {"scope", "namespace", "case", "sequence", "record_sha256", "expires"}
                        or ack["scope"] != "synthetic" or ack["namespace"] != record["namespace"]
                        or ack["case"] != proposal["case"] or type(ack["sequence"]) is not int
                        or ack["sequence"] != proposal["sequence"]
                        or ack["record_sha256"] != proposal_hash):
                    raise InvalidEvidence("receipt binding mismatch")
                pending = None
            elif kind == "halt":
                halted = True
            else:
                raise InvalidEvidence("unexpected journal event")
            previous = current_hash
            authenticated.append(record)
    except (OSError, KeyError, TypeError, UnicodeError, json.JSONDecodeError) as error:
        raise InvalidEvidence("unreadable or malformed retained evidence") from error
    return {"complete": pending is None and not halted, "records": len(names), "head": previous,
            "pending": pending[0]["sequence"] if pending else None,
            "halted": halted, "events": authenticated}


def review_candidate(directory_fd, inputs, expected):
    """Produce bounded independent artifact observations, never operational acceptance.

    Accepted input custody and the exact reviewed directory are prerequisites.
    Their mismatch or unavailable/unstable observation raises without a verdict.
    Known candidate defects on that established object yield a complete negative.
    Supervisor/entitlement/synchronization and continuous-custody evidence must
    be independently assessed as well before any operational decision.
    """
    try:
        return _review_candidate(directory_fd, inputs, expected)
    except OSError as error:
        raise ObservationUncertain("artifact/custody observation is unavailable") from error


def _review_candidate(directory_fd, inputs, expected):
    findings = []
    directory = os.fstat(directory_fd)
    if not stat.S_ISDIR(directory.st_mode):
        raise CustodyMismatch("review target is not a directory")
    candidate = expected.get("candidate")
    if (not isinstance(candidate, dict) or set(candidate) != set(_metadata(directory))
            or (directory.st_dev, directory.st_ino) != (candidate["device"], candidate["inode"])):
        raise CustodyMismatch("exact reviewed candidate identity is absent or mismatching")
    if _metadata(directory) != candidate:
        findings.append("candidate metadata differs from accepted binding")
    if (stat.S_IMODE(directory.st_mode) != 0o500 or directory.st_uid != expected["uid"]
            or directory.st_gid != expected["gid"]):
        findings.append("candidate directory metadata mismatch")
    wanted = {"qualification_authority.py", "source_review_packet.md"}
    entries = set(os.listdir(directory_fd))
    if entries != wanted:
        findings.append("candidate entry inventory mismatch")
    observations = {}
    input_observations = {}
    for role in ("source", "companion", "export"):
        identity = inspect_file(inputs[role])
        input_observations[role] = identity
        binding = expected["inputs"][role]
        retained = {k: v for k, v in binding.items() if k != "range"}
        if {k: v for k, v in identity.items() if k != "final_lf"} != retained:
            raise CustodyMismatch("accepted input identity/metadata/custody mismatch")
    for role, name in (("source", "qualification_authority.py"), ("companion", "source_review_packet.md")):
        if name not in entries:
            findings.append(role + " payload is absent")
            continue
        fd = open_readonly(directory_fd, name)
        try:
            actual = inspect_file(fd)
            observations[role] = actual
            binding = expected["inputs"][role]
            if (actual["bytes"] != binding["bytes"] or actual["sha256"] != binding["sha256"]
                    or not actual["final_lf"] or actual["mode"] != 0o400
                    or actual["uid"] != expected["uid"] or actual["gid"] != expected["gid"]
                    or not equal_files(inputs[role], fd)):
                findings.append(role + " content or metadata mismatch")
            first, end = binding["range"]
            if (os.pread(inputs["export"], end - first, first) != os.pread(fd, end - first, 0)
                    or os.pread(inputs["export"], 1, end - 1) != b"\n"):
                findings.append(role + " export slice or LF mismatch")
            entry = os.stat(name, dir_fd=directory_fd, follow_symlinks=False)
            if (entry.st_dev, entry.st_ino) != (actual["device"], actual["inode"]):
                raise InvalidEvidence("entry changed during verification")
        finally:
            os.close(fd)
    for role in ("source", "companion", "export"):
        if inspect_file(inputs[role]) != input_observations[role]:
            raise ObservationUncertain("accepted input custody changed during the review")
    if _metadata(os.fstat(directory_fd)) != _metadata(directory) or set(os.listdir(directory_fd)) != entries:
        raise ObservationUncertain("candidate identity/entries changed during the review")
    result = {"complete": True, "mechanism_failed": False, "positive": not findings,
              "findings": findings, "observations": observations, "inputs": input_observations,
              "directory": _metadata(directory)}
    return {**result, "evidence_sha256": hashlib.sha256(_encode(result)).hexdigest()}


def _metadata(value):
    return {"device": value.st_dev, "inode": value.st_ino, "bytes": value.st_size,
            "uid": value.st_uid, "gid": value.st_gid, "mode": stat.S_IMODE(value.st_mode),
            "links": value.st_nlink, "mtime_ns": value.st_mtime_ns, "ctime_ns": value.st_ctime_ns}


def review_result(parent_fd, inputs, context, records_fd, supervisor_key, custody_key, verifier_key):
    """Observe a synthetic result against authenticated, current O4 evidence.

    The callback's custodian supplies descriptors and synthetic keys. This
    performs actual independent artifact and journal reads; it is not production
    principal separation. A result cannot be signed from a producer digest alone.
    """
    history = read_history(records_fd, supervisor_key, custody_key)
    if (not history["complete"] or context["head"] != history["head"]
            or context["scope"] != "synthetic"
            or context["namespace"] != "JCSchoeman96/symphony/ACQ-EXEC-06/B1/synthetic"
            or _metadata(os.fstat(parent_fd)) != context["parent"]):
        raise InvalidEvidence("review context is not the current authenticated journal/parent")
    proposals = {}
    confirmed = []
    for event in history["events"]:
        if event["kind"].startswith("pending_"):
            proposals[hashlib.sha256(_encode(event)).hexdigest()] = event
        elif event["kind"].startswith("confirmed_") and event["case"] == context["case"]:
            confirmed.append((proposals[event["payload"]["proposal"]], event))
    initial = [proposal for proposal, _ in confirmed if proposal["kind"] == "pending_initialize"]
    transitions = [proposal["payload"] for proposal, _ in confirmed
                   if proposal["kind"] == "pending_transition"]
    expected = [("B1-T01", "P0", "P1"), ("B1-T02", "P1", "P2"),
                ("B1-T03", "P2", "P3"), ("B1-T06", "P3", "O0"),
                ("B1-T07", "O0", "O1"), ("B1-T08", "O1", "O2"),
                ("B1-T09", "O2", "O3"), ("B1-T10", "O3", "O4")]
    if len(initial) != 1 or [(p["request"]["body"]["transition"], p["source"], p["destination"])
                             for p in transitions] != expected:
        raise InvalidEvidence("case has no complete confirmed path to review intake")
    initialized = initial[0]["payload"]
    authorization = initialized["authorization"]["body"]
    if (initialized["state"] != "P0" or initialized["grant"] is not None
            or initialized["consumed"] is not False
            or hashlib.sha256(_encode(authorization)).hexdigest() != context["initialization"]
            or authorization["case"] != context["case"]):
        raise InvalidEvidence("review initialization binding mismatch")
    evidence = {p["request"]["body"]["transition"]: p["request"]["body"]["evidence"] for p in transitions}
    grant = evidence["B1-T06"]["grant"]
    if (grant != context["grant"] or evidence["B1-T02"]["packet"] != context["packet"]
            or grant["packet"] != context["packet"]
            or evidence["B1-T07"]["entitlement"] != grant["id"]
            or evidence["B1-T08"]["ready"] != grant["id"]
            or evidence["B1-T09"]["producer_complete"] is not True
            or evidence["B1-T10"]["review_authority"] != context["review_authority"]):
        raise InvalidEvidence("review plan/grant/attempt/intake binding mismatch")
    checkpoints = [(p, c) for p, c in confirmed if p["kind"] == "pending_checkpoint"]
    effects = [p["payload"] for p, _ in confirmed if p["kind"] == "pending_effect"]
    if ([value["name"] for value in effects]
            != ["mkdir", "source_create", "source_launch", "companion_create", "companion_launch",
                "finalize_directory"] or effects[2]["slot"] != 1 or effects[4]["slot"] != 2
            or effects[0]["destination"] != grant["destination"]):
        raise InvalidEvidence("ordered exclusive effect/launch evidence is incomplete")
    if [p["payload"]["name"] for p, _ in checkpoints] != ["source", "companion", "producer"]:
        raise InvalidEvidence("ordered acknowledged checkpoints are incomplete")
    for proposal, _ in checkpoints[:2]:
        value = proposal["payload"]
        if (value["output"] != context["outputs"][value["name"]] or value["fsync"] is not True
                or value["writer_closed"] is not True or value["child"]["exit"] != 0
                or value["child"]["writer_terminated"] is not True):
            raise InvalidEvidence("copy checkpoint binding mismatch")
    producer, confirmation = checkpoints[-1]
    if (hashlib.sha256(_encode(confirmation)).hexdigest() != context["producer_head"]
            or producer["payload"]["directory"] != context["candidate"]
            or producer["payload"]["active_writers"] is not False
            or producer["payload"]["sync_order"] != ["source", "companion", "directory", "parent"]):
        raise InvalidEvidence("producer completion evidence mismatch")
    directory = open_readonly(parent_fd, grant["destination"])
    try:
        actual = os.fstat(directory)
        if (actual.st_dev, actual.st_ino) != (context["candidate"]["device"], context["candidate"]["inode"]):
            raise InvalidEvidence("candidate identity differs from the confirmed producer checkpoint")
        result = review_candidate(directory, inputs, {"uid": context["candidate"]["uid"],
                                                      "gid": context["candidate"]["gid"],
                                                      "candidate": context["candidate"],
                                                      "inputs": grant["inputs"]})
        for role, observed in result["observations"].items():
            if {k: observed[k] for k in context["outputs"][role]} != context["outputs"][role]:
                result["findings"].append(role + " metadata differs from producer checkpoint")
        result["positive"] = not result["findings"]
        result["evidence_sha256"] = hashlib.sha256(_encode({
            k: v for k, v in result.items() if k != "evidence_sha256"})).hexdigest()
    finally:
        os.close(directory)
    body = {"scope": "synthetic", "namespace": context["namespace"], "binding": context, "result": result}
    signed = {"actor": "V", "body": body}
    return {**signed, "mac": hmac.new(verifier_key, _encode(signed), "sha256").hexdigest()}


def production_acceptance(*args, **kwargs):
    raise Unqualified("no appointed production verifier or qualified authentication/custody")


def open_readonly(parent_fd, name):
    if not isinstance(name, str) or not name or name in (".", "..") or "/" in name or "\x00" in name:
        raise ValueError("one literal directory entry is required")
    return os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_NONBLOCK
                   | os.O_CLOEXEC, dir_fd=parent_fd)


def inspect_file(fd, limit=131072):
    """Return independently calculated identity, preserving descriptor offset."""
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
        raise CustodyMismatch("object is not a bounded unique regular file")
    hashed = hashlib.sha256()
    total = 0
    last = b""
    while part := os.pread(fd, 16384, total):
        total += len(part)
        if total > limit:
            raise ObservationUncertain("object grew beyond verification bound")
        hashed.update(part)
        last = part[-1:]
    after = os.fstat(fd)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns,
        before.st_mode, before.st_uid, before.st_gid, before.st_nlink) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns,
        after.st_mode, after.st_uid, after.st_gid, after.st_nlink):
        raise ObservationUncertain("object changed during independent observation")
    if total != before.st_size:
        raise ObservationUncertain("complete object bytes could not be observed")
    return {"device": before.st_dev, "inode": before.st_ino, "bytes": total,
            "sha256": hashed.hexdigest(), "mode": stat.S_IMODE(before.st_mode),
            "uid": before.st_uid, "gid": before.st_gid, "links": before.st_nlink,
            "mtime_ns": before.st_mtime_ns, "ctime_ns": before.st_ctime_ns,
            "final_lf": last == b"\n"}


def equal_files(left_fd, right_fd):
    left = inspect_file(left_fd)
    right = inspect_file(right_fd)
    if left["bytes"] != right["bytes"]:
        return False
    for offset in range(0, left["bytes"], 16384):
        if os.pread(left_fd, 16384, offset) != os.pread(right_fd, 16384, offset):
            return False
    return inspect_file(left_fd) == left and inspect_file(right_fd) == right
