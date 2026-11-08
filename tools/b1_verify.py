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

    Known byte/metadata differences yield a complete negative artifact review.
    An inability to observe the objects raises; it is not a completed rejection.
    Supervisor/entitlement/synchronization and continuous-custody evidence must
    be independently assessed as well before any operational decision.
    """
    findings = []
    directory = os.fstat(directory_fd)
    if not stat.S_ISDIR(directory.st_mode):
        raise ValueError("review target is not a directory")
    if (stat.S_IMODE(directory.st_mode) != 0o500 or directory.st_uid != expected["uid"]
            or directory.st_gid != expected["gid"]):
        findings.append("candidate directory metadata mismatch")
    wanted = {"qualification_authority.py", "source_review_packet.md"}
    entries = set(os.listdir(directory_fd))
    if entries != wanted:
        findings.append("candidate entry inventory mismatch")
    observations = {}
    for role in ("source", "companion", "export"):
        identity = inspect_file(inputs[role])
        binding = expected["inputs"][role]
        if identity["bytes"] != binding["bytes"] or identity["sha256"] != binding["sha256"]:
            raise InvalidEvidence("accepted input identity mismatch")
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
    result = {"complete": True, "mechanism_failed": False, "positive": not findings,
              "findings": findings, "observations": observations}
    return {**result, "evidence_sha256": hashlib.sha256(_encode(result)).hexdigest()}


def production_acceptance(*args, **kwargs):
    raise Unqualified("no appointed production verifier or qualified authentication/custody")


def open_readonly(parent_fd, name):
    if not isinstance(name, str) or not name or name in (".", "..") or "/" in name or "\x00" in name:
        raise ValueError("one literal directory entry is required")
    return os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_CLOEXEC, dir_fd=parent_fd)


def inspect_file(fd, limit=131072):
    """Return independently calculated identity, preserving descriptor offset."""
    before = os.fstat(fd)
    if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1 or before.st_size > limit:
        raise ValueError("object is not a bounded unique regular file")
    hashed = hashlib.sha256()
    total = 0
    last = b""
    while part := os.pread(fd, 16384, total):
        total += len(part)
        if total > limit:
            raise ValueError("object grew beyond verification bound")
        hashed.update(part)
        last = part[-1:]
    after = os.fstat(fd)
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns,
        before.st_mode, before.st_uid, before.st_gid, before.st_nlink) != (
        after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns,
        after.st_mode, after.st_uid, after.st_gid, after.st_nlink):
        raise ValueError("object changed during independent observation")
    return {"device": before.st_dev, "inode": before.st_ino, "bytes": total,
            "sha256": hashed.hexdigest(), "mode": stat.S_IMODE(before.st_mode),
            "uid": before.st_uid, "gid": before.st_gid, "links": before.st_nlink,
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
