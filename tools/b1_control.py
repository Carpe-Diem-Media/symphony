"""B1-R2 bounded controller, executable only for explicitly synthetic cases.

Production admission deliberately refuses until the external authentication,
custody, immutable dependencies, observation and isolation boundary is qualified.
Synthetic HMACs exercise binding and replay rules; they are not independent
human identity or a production trust mechanism. No source payload is imported.
"""

import fcntl
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import resource
import select
import signal
import stat
import time


NAMESPACE = "JCSchoeman96/symphony/ACQ-EXEC-06/B1/synthetic"
NONTERMINAL = ("P0", "P1", "P2", "P3", "O0", "O1", "O2", "O3", "O4")
TERMINAL = ("PLAN_CHANGES_REQUESTED", "PLAN_REJECTED", "STAGING_VERIFIED",
            "B1_REVIEW_REJECTED", "REVOKED", "EXPIRED", "AUTHORITY_INVALID",
            "FAILED", "INCOMPLETE", "UNCERTAIN")
# Each row names source, destination, initiating actor and required evidence.
# C authenticates durable acceptance independently of the initiating signature.
TRANSITIONS = {
    "B1-T01": ("P0", "P1", "P", ("revision",)),
    "B1-T02": ("P1", "P2", "C", ("packet",)),
    "B1-T03": ("P2", "P3", "M", ("decision", "accepted")),
    "B1-T04": ("P2", "PLAN_CHANGES_REQUESTED", "M", ("decision",)),
    "B1-T05": ("P2", "PLAN_REJECTED", "M", ("decision",)),
    "B1-T06": ("P3", "O0", "H", ("grant",)),
    "B1-T07": ("O0", "O1", "S", ("entitlement",)),
    "B1-T08": ("O1", "O2", "S", ("ready",)),
    "B1-T09": ("O2", "O3", "S", ("producer_complete",)),
    "B1-T10": ("O3", "O4", "V", ("review_authority",)),
    "B1-T11": ("O4", "STAGING_VERIFIED", "V", ("review",)),
    "B1-T12": ("O4", "B1_REVIEW_REJECTED", "V", ("review",)),
    "B1-U-P0": ("P0", "UNCERTAIN", "C", ("causes",)),
    "B1-U-P1": ("P1", "UNCERTAIN", "C", ("causes",)),
    "B1-U-P2": ("P2", "UNCERTAIN", "C", ("causes",)),
    "B1-U-P3": ("P3", "UNCERTAIN", "C", ("causes",)),
    "B1-U-O0": ("O0", "UNCERTAIN", "C", ("causes",)),
    "B1-U-O1": ("O1", "UNCERTAIN", "C", ("causes",)),
    "B1-U-O2": ("O2", "UNCERTAIN", "C", ("causes",)),
    "B1-U-O3": ("O3", "UNCERTAIN", "C", ("causes",)),
    "B1-U-O4": ("O4", "UNCERTAIN", "C", ("causes",)),
    "B1-R-P0": ("P0", "REVOKED", "H", ("causes",)),
    "B1-R-P1": ("P1", "REVOKED", "H", ("causes",)),
    "B1-R-P2": ("P2", "REVOKED", "H", ("causes",)),
    "B1-R-P3": ("P3", "REVOKED", "H", ("causes",)),
    "B1-R-O0": ("O0", "REVOKED", "H", ("causes",)),
    "B1-R-O1": ("O1", "REVOKED", "H", ("causes",)),
    "B1-R-O2": ("O2", "REVOKED", "H", ("causes",)),
    "B1-R-O3": ("O3", "REVOKED", "H", ("causes",)),
    "B1-R-O4": ("O4", "REVOKED", "H", ("causes",)),
    "B1-E-P0": ("P0", "EXPIRED", "C", ("causes",)),
    "B1-E-P1": ("P1", "EXPIRED", "C", ("causes",)),
    "B1-E-P2": ("P2", "EXPIRED", "C", ("causes",)),
    "B1-E-P3": ("P3", "EXPIRED", "C", ("causes",)),
    "B1-E-O0": ("O0", "EXPIRED", "C", ("causes",)),
    "B1-E-O1": ("O1", "EXPIRED", "C", ("causes",)),
    "B1-E-O2": ("O2", "EXPIRED", "C", ("causes",)),
    "B1-E-O3": ("O3", "EXPIRED", "C", ("causes",)),
    "B1-E-O4": ("O4", "EXPIRED", "C", ("causes",)),
    "B1-A-P0": ("P0", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-A-P1": ("P1", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-A-P2": ("P2", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-A-P3": ("P3", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-A-O0": ("O0", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-A-O1": ("O1", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-A-O2": ("O2", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-A-O3": ("O3", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-A-O4": ("O4", "AUTHORITY_INVALID", "C", ("causes",)),
    "B1-F-P0": ("P0", "FAILED", "C", ("causes",)),
    "B1-F-P1": ("P1", "FAILED", "C", ("causes",)),
    "B1-F-P2": ("P2", "FAILED", "C", ("causes",)),
    "B1-F-P3": ("P3", "FAILED", "C", ("causes",)),
    "B1-F-O0": ("O0", "FAILED", "C", ("causes",)),
    "B1-F-O1": ("O1", "FAILED", "C", ("causes",)),
    "B1-F-O2": ("O2", "FAILED", "C", ("causes",)),
    "B1-F-O3": ("O3", "FAILED", "C", ("causes",)),
    "B1-F-O4": ("O4", "FAILED", "C", ("causes",)),
    "B1-I-P0": ("P0", "INCOMPLETE", "C", ("causes",)),
    "B1-I-P1": ("P1", "INCOMPLETE", "C", ("causes",)),
    "B1-I-P2": ("P2", "INCOMPLETE", "C", ("causes",)),
    "B1-I-P3": ("P3", "INCOMPLETE", "C", ("causes",)),
    "B1-I-O0": ("O0", "INCOMPLETE", "C", ("causes",)),
    "B1-I-O1": ("O1", "INCOMPLETE", "C", ("causes",)),
    "B1-I-O2": ("O2", "INCOMPLETE", "C", ("causes",)),
    "B1-I-O3": ("O3", "INCOMPLETE", "C", ("causes",)),
    "B1-I-O4": ("O4", "INCOMPLETE", "C", ("causes",)),
}
PRECEDENCE = ("uncertain", "revoked", "expired", "authority_invalid",
              "procedure_failed", "incomplete")
MAX_RECORD_BYTES = 65536
MAX_RECORDS = 2048
MAX_INPUT_BYTES = 131072
FD_EXECUTION = os.execve in os.supports_fd


class Denied(RuntimeError):
    """No further effect is admitted by this request."""


class RecoveryRequired(Denied):
    """Existing history requires external reconciliation; never resume effects."""


class DeploymentNotQualified(Denied):
    """Production requires separately qualified external controls."""


def open_production(*args, **kwargs):
    """Refuse before opening storage or registering a production case."""
    raise DeploymentNotQualified("production authentication/custody/isolation are not qualified")


def canonical(value):
    """Exact ASCII framing, with no implicit numeric or Unicode normalization."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _hex(value, length=64):
    return isinstance(value, str) and re.fullmatch("[0-9a-f]{%d}" % length, value) is not None


def _name(value):
    return isinstance(value, str) and re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9_-]{0,95}", value)


def _check(condition, reason):
    if not condition:
        raise Denied(reason)


def _verify(envelope, actor, keys):
    _check(isinstance(envelope, dict) and set(envelope) == {"actor", "body", "mac"},
           "malformed authenticated envelope")
    _check(envelope["actor"] == actor and isinstance(envelope["body"], dict), "wrong actor")
    signed = {"actor": actor, "body": envelope["body"]}
    expected = hmac.new(keys[actor], canonical(signed), "sha256").hexdigest()
    _check(_hex(envelope["mac"]) and hmac.compare_digest(expected, envelope["mac"]),
           "invalid authentication")
    return envelope["body"]


def identify(fd):
    """Hash a bounded regular descriptor without changing its file offset."""
    before = os.fstat(fd)
    _check(stat.S_ISREG(before.st_mode) and before.st_nlink >= 1, "not a regular object")
    _check(before.st_size <= 32 * 1024 * 1024, "dependency exceeds inspection bound")
    hashed = hashlib.sha256()
    offset = 0
    while chunk := os.pread(fd, 65536, offset):
        hashed.update(chunk)
        offset += len(chunk)
        _check(offset <= 32 * 1024 * 1024, "object grew during inspection")
    after = os.fstat(fd)
    _check(_metadata(before) == _metadata(after), "object changed during inspection")
    return {**_metadata(before), "sha256": hashed.hexdigest()}


def _metadata(value):
    return {"device": value.st_dev, "inode": value.st_ino, "bytes": value.st_size,
            "uid": value.st_uid, "gid": value.st_gid, "mode": stat.S_IMODE(value.st_mode),
            "links": value.st_nlink, "mtime_ns": value.st_mtime_ns, "ctime_ns": value.st_ctime_ns}


def adverse(causes):
    """Return the single highest-priority adverse family for complete observations."""
    _check(isinstance(causes, list) and causes and len(set(causes)) == len(causes)
           and all(x in PRECEDENCE for x in causes), "invalid adverse causes")
    return "UREAFI"[next(i for i, name in enumerate(PRECEDENCE) if name in causes)]


class Controller:
    """One synthetic supervisor session and a bounded durable case namespace.

    Keys and the acknowledgment callback belong to a synthetic test rig. They
    confer no real principal separation. Reopening a used journal always denies
    effects; an independent verifier may still read it. No auto-recovery exists.
    """

    def __init__(self, root, keys, acknowledge, clock=time.time, *, reviewer=None):
        root = Path(root)
        allowed = os.environ.get("B1_TEST_ROOT")
        local = Path("/home/jcschoeman96/projects/symphony-b1-control-r0/.b1-control-test")
        runner = os.environ.get("RUNNER_TEMP")
        _check(allowed is not None and Path(allowed).is_absolute()
               and Path(allowed).resolve() == Path(allowed)
               and (Path(allowed) == local or (runner and Path(allowed).is_relative_to(Path(runner))
                    and Path(allowed) != Path(runner)))
               and root.is_absolute() and root.resolve() == root
               and root.is_relative_to(Path(allowed)) and root != Path(allowed),
               "synthetic storage must be inside B1_TEST_ROOT")
        _check(set(keys) == set("HPMSVC") and all(isinstance(k, bytes) and len(k) >= 32
               for k in keys.values()) and len(set(keys.values())) == 6,
               "distinct synthetic role keys are required")
        self.root = root
        self.keys = dict(keys)
        self.acknowledge = acknowledge
        self.reviewer = reviewer
        self.clock = clock
        self.cases = {}
        self.authorizations = set()
        self.grants = set()
        self.attempts = set()
        self.head = "0" * 64
        self.sequence = 0
        self.blocked = False
        self.active_child = None
        self.root_fd = -1
        self.records_fd = -1
        self.root_fd = os.open(root, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        try:
            fcntl.flock(self.root_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            info = os.fstat(self.root_fd)
            _check(info.st_uid == os.getuid() and stat.S_IMODE(info.st_mode) == 0o700,
                   "synthetic storage owner/mode mismatch")
            try:
                os.mkdir("records", mode=0o700, dir_fd=self.root_fd)
                os.fsync(self.root_fd)
            except FileExistsError:
                pass
            self.records_fd = os.open("records", os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                                      | os.O_CLOEXEC, dir_fd=self.root_fd)
            if os.listdir(self.records_fd):
                raise RecoveryRequired("used namespace: reconciliation required, no automatic restart")
            self._append("session", "", {"scope": "synthetic", "namespace": NAMESPACE})
        except BaseException:
            self.close()
            raise

    def close(self):
        """Close access without cleanup, replay, state repair or eligibility restoration."""
        for attr in ("records_fd", "root_fd"):
            fd = getattr(self, attr, -1)
            if fd >= 0:
                setattr(self, attr, -1)
                os.close(fd)

    def _append(self, kind, case, payload):
        _check(not self.blocked and self.records_fd >= 0, "supervisor is denied or closed")
        record = {"scope": "synthetic", "namespace": NAMESPACE, "sequence": self.sequence + 1,
                  "previous": self.head, "kind": kind, "case": case, "payload": payload}
        raw = canonical(record)
        signed = {"record": record, "mac": hmac.new(self.keys["S"], raw, "sha256").hexdigest()}
        data = canonical(signed) + b"\n"
        _check(len(data) <= MAX_RECORD_BYTES and self.sequence < MAX_RECORDS,
               "evidence storage bound exceeded")
        try:
            fd = os.open(f"{record['sequence']:06d}.json", os.O_WRONLY | os.O_CREAT | os.O_EXCL
                         | os.O_NOFOLLOW | os.O_CLOEXEC, 0o400, dir_fd=self.records_fd)
            try:
                offset = 0
                while offset < len(data):
                    count = os.write(fd, data[offset:])
                    if count <= 0:
                        raise OSError("short evidence write")
                    offset += count
                os.fsync(fd)
            finally:
                os.close(fd)
            os.fsync(self.records_fd)
        except BaseException:
            self.blocked = True
            raise
        self.sequence = record["sequence"]
        self.head = hashlib.sha256(raw).hexdigest()
        return record

    def _commit(self, kind, case, payload, *, valid_until=None):
        """Persist proposal, validate received C receipt, then persist confirmation."""
        proposal = self._append("pending_" + kind, case, payload)
        try:
            if kind in ("effect", "checkpoint"):
                current = self.cases[case]
                valid_until = min(current["expires"], current["grant"]["expires"])
            receipt = self.acknowledge(json.loads(canonical(proposal)))
            body = _verify(receipt, "C", self.keys)
            _check(set(body) == {"scope", "namespace", "case", "sequence", "record_sha256", "expires"}
                   and body["scope"] == "synthetic" and body["namespace"] == NAMESPACE
                   and body["case"] == case and type(body["sequence"]) is int
                   and body["sequence"] == proposal["sequence"]
                   and body["record_sha256"] == digest(proposal)
                   and type(body["expires"]) in (int, float) and self.clock() < body["expires"],
                   "stale, replayed or mismatching acknowledgment")
            _check(valid_until is None or self.clock() < valid_until,
                   "authority expired while acknowledgment was pending")
            return self._append("confirmed_" + kind, case,
                                {"proposal": digest(proposal), "receipt": receipt})
        except BaseException as error:
            self.blocked = True
            raise Denied("unconfirmed commitment: forward effects denied") from error

    def register(self, authorization):
        """Prospectively register one synthetic case under an unused owner approval."""
        body = _verify(authorization, "H", self.keys)
        _check(set(body) == {"scope", "namespace", "case", "authorization_id", "revision",
                            "approval_ref", "predecessor", "governing", "expires"}, "incomplete initialization")
        case = body["case"]
        _check(body["scope"] == "synthetic" and body["namespace"] == NAMESPACE
               and _name(case) and case.startswith("synthetic-")
               and _name(body["authorization_id"]) and body["authorization_id"].startswith("synthetic-")
               and _name(body["revision"]) and body["approval_ref"]
               and type(body["expires"]) in (int, float) and self.clock() < body["expires"],
               "invalid or expired initialization identity")
        _check(case not in self.cases and body["authorization_id"] not in self.authorizations,
               "case or authorization already registered")
        predecessor = body["predecessor"]
        _check(set(predecessor) == {"case", "state", "decision_sha256", "artifact_sha256"}
               and predecessor["case"] != case and predecessor["state"] == "PLAN_CHANGES_REQUESTED"
               and _hex(predecessor["decision_sha256"]) and _hex(predecessor["artifact_sha256"]),
               "terminal predecessor evidence is required")
        _check(set(body["governing"]) == {"commit", "tree", "plan_blob"}
               and all(_hex(v, 40) for v in body["governing"].values()), "invalid governing binding")
        self._commit("initialize", case, {"authorization": authorization, "state": "P0",
                                          "grant": None, "consumed": False}, valid_until=body["expires"])
        self.authorizations.add(body["authorization_id"])
        self.cases[case] = {"state": "P0", "initialization": digest(body), "revision": body["revision"],
                            "expires": body["expires"],
                            "packet": None, "grant": None, "consumed": False, "copies": [],
                            "complete": False}
        return json.loads(canonical(self.cases[case]))

    def apply(self, request):
        """Admit only the registered relation against the exact acknowledged head."""
        _check(isinstance(request, dict) and isinstance(request.get("body"), dict), "malformed request")
        submitted = request["body"]
        transition = submitted.get("transition")
        _check(transition in TRANSITIONS, "unlisted transition")
        source, destination, actor, required = TRANSITIONS[transition]
        body = _verify(request, actor, self.keys)
        _check(set(body) == {"scope", "case", "transition", "expected_head", "evidence"}
               and body["scope"] == "synthetic", "invalid transition framing")
        case = body["case"]
        _check(case in self.cases and not self.blocked, "unregistered or denied case")
        current = self.cases[case]
        _check(current["state"] == source and body["expected_head"] == self.head,
               "terminal, stale or wrong source state")
        evidence = body["evidence"]
        _check(isinstance(evidence, dict) and all(name in evidence for name in required),
               "missing transition evidence")
        verification = self._guards(transition, case, current, evidence)
        valid_until = None
        if transition.startswith("B1-T"):
            valid_until = min(current["expires"], current["grant"]["expires"]
                              if current["grant"] else current["expires"])
            if transition == "B1-T06":
                valid_until = min(valid_until, evidence["grant"]["expires"])
        payload = {"request": request, "source": source, "destination": destination}
        if verification is not None:
            payload["verification"] = verification
        self._commit("transition", case, payload, valid_until=valid_until)
        current["state"] = destination
        if transition == "B1-T02":
            current["packet"] = json.loads(canonical(evidence["packet"]))
        if transition == "B1-T06":
            current["grant"] = json.loads(canonical(evidence["grant"]))
            self.grants.add(current["grant"]["id"])
            self.attempts.add(current["grant"]["attempt"])
        if transition == "B1-T07":
            current["consumed"] = True
        if transition == "B1-T10":
            current["review_authority"] = evidence["review_authority"]
        return json.loads(canonical(current))

    def _guards(self, transition, case, current, evidence):
        family = transition.split("-")[1]
        expired = self.clock() >= min(current["expires"],
                                      current["grant"]["expires"] if current["grant"] else current["expires"])
        if family in "UREAFI" and len(family) == 1:
            causes = evidence["causes"]
            _check(adverse(causes) == family, "higher-priority adverse cause")
            _check(not expired or adverse(list(set(causes + ["expired"]))) == family,
                   "observed expiry defeats lower-priority adverse disposition")
            _check(family != "E" or expired, "expiry is not established")
            if current["state"] == "O4" and family == "F":
                _check(evidence.get("review_mechanism_failed") is True
                       and evidence.get("review_completed") is False,
                       "artifact mismatch is not review-mechanism failure")
            return
        _check(not evidence.get("causes") and not expired,
               "adverse observations or expiry defeat forward progress")
        grant = current["grant"]
        if grant:
            _check(self.clock() < grant["expires"], "grant expired")
        if transition == "B1-T01":
            _check(evidence["revision"] == current["revision"], "wrong authorized revision")
        elif transition == "B1-T02":
            packet = evidence["packet"]
            _check(set(packet) == {"bytes", "sha256"} and type(packet["bytes"]) is int
                   and 0 < packet["bytes"] <= MAX_INPUT_BYTES and _hex(packet["sha256"]),
                   "invalid received packet identity")
        elif transition in ("B1-T03", "B1-T04", "B1-T05"):
            _check(_hex(evidence["decision"]), "missing exact review decision")
            if transition == "B1-T03":
                _check(evidence["accepted"] is True, "planning decision is not positive")
        elif transition == "B1-T06":
            self._grant(evidence["grant"], current)
        elif transition == "B1-T07":
            _check(not current["consumed"] and evidence["entitlement"] == grant["id"],
                   "wrong or already consumed B1 entitlement")
        elif transition == "B1-T08":
            _check(current["consumed"] and evidence["ready"] == grant["id"], "unconfirmed entitlement")
        elif transition == "B1-T09":
            _check(current["complete"] and evidence["producer_complete"] is True,
                   "copy/synchronization/checkpoint evidence is incomplete")
        elif transition == "B1-T10":
            _check(_hex(evidence["review_authority"]), "no exact independent review authority")
        elif transition in ("B1-T11", "B1-T12"):
            review = evidence["review"]
            _check(set(review) == {"complete", "mechanism_failed", "positive", "evidence_sha256"}
                   and review["complete"] is True and review["mechanism_failed"] is False
                   and type(review["positive"]) is bool and _hex(review["evidence_sha256"])
                   and review["positive"] == (transition == "B1-T11"),
                   "review decision is incomplete or belongs to another disposition")
            return self._verified_review(case, current, review)

    def review_context(self, case):
        """Snapshot the exact O4 binding for a separately supplied synthetic observer."""
        _check(case in self.cases and not self.blocked, "unregistered or denied review case")
        current = self.cases[case]
        _check(current["state"] == "O4" and current["complete"], "independent review is not eligible")
        return json.loads(canonical({"scope": "synthetic", "namespace": NAMESPACE, "case": case,
                    "initialization": current["initialization"], "packet": current["packet"],
                    "grant": current["grant"], "parent": _metadata(os.fstat(self.root_fd)),
                    "candidate": current["candidate"], "outputs": current["outputs"],
                    "producer_head": current["producer_head"],
                    "review_authority": current["review_authority"], "head": self.head}))

    def _verified_review(self, case, current, decision):
        _check(callable(self.reviewer), "no independent result interface is configured")
        context = self.review_context(case)
        try:
            receipt = self.reviewer(json.loads(canonical(context)))
            body = _verify(receipt, "V", self.keys)
            _check(set(body) == {"scope", "namespace", "binding", "result"}
                   and body["scope"] == "synthetic" and body["namespace"] == NAMESPACE
                   and body["binding"] == context and digest(body) == decision["evidence_sha256"],
                   "independent result does not bind this candidate/lifecycle/decision")
            _check(self.review_context(case) == context, "lifecycle changed during independent observation")
            result = body["result"]
            _check(set(result) == {"complete", "mechanism_failed", "positive", "findings",
                                   "observations", "inputs", "directory", "evidence_sha256"}
                   and result["complete"] is True and result["mechanism_failed"] is False
                   and type(result["positive"]) is bool and result["positive"] == decision["positive"]
                   and isinstance(result["findings"], list) and result["positive"] == (not result["findings"])
                   and result["evidence_sha256"] == digest({k: v for k, v in result.items()
                                                            if k != "evidence_sha256"}),
                   "independent result is incomplete, inconsistent or altered")
            _check(set(result["inputs"]) == {"source", "companion", "export"},
                   "independent original-input observations are incomplete")
            for role, observed in result["inputs"].items():
                _check({k: v for k, v in observed.items() if k != "final_lf"}
                       == {k: v for k, v in current["grant"]["inputs"][role].items() if k != "range"},
                       "independent original-input observations do not match the grant")
            if result["positive"]:
                _check(set(result["observations"]) == {"source", "companion"},
                       "positive independent result omits a payload")
                _check(result["directory"] == context["candidate"],
                       "positive independent result does not identify the produced directory")
                for role, observed in result["observations"].items():
                    binding = current["grant"]["inputs"][role]
                    _check(observed["sha256"] == binding["sha256"] and observed["bytes"] == binding["bytes"]
                           and observed["mode"] == 0o400 and observed["links"] == 1
                           and observed["uid"] == current["candidate"]["uid"]
                           and observed["gid"] == current["candidate"]["gid"] and observed["final_lf"] is True,
                           "positive independent observations fail payload requirements")
                    _check({k: observed[k] for k in context["outputs"][role]} == context["outputs"][role],
                           "positive independent result does not identify the produced payload")
            _check(_metadata(os.fstat(self.root_fd)) == context["parent"], "review parent changed")
            directory = os.open(current["grant"]["destination"], os.O_RDONLY | os.O_DIRECTORY
                                | os.O_NOFOLLOW | os.O_CLOEXEC, dir_fd=self.root_fd)
            try:
                _check(_metadata(os.fstat(directory)) == result["directory"], "reviewed directory changed")
                for role, name in (("source", "qualification_authority.py"),
                                   ("companion", "source_review_packet.md")):
                    observed = result["observations"].get(role)
                    if observed is None:
                        _check(not result["positive"] and name not in os.listdir(directory),
                               "missing observation is not a current negative result")
                        continue
                    fd = os.open(name, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME
                                 | os.O_NONBLOCK | os.O_CLOEXEC, dir_fd=directory)
                    try:
                        _check(identify(fd) == {k: v for k, v in observed.items() if k != "final_lf"},
                               "reviewed payload changed or observations do not identify it")
                    finally:
                        os.close(fd)
                entry = os.stat(current["grant"]["destination"], dir_fd=self.root_fd, follow_symlinks=False)
                _check(_metadata(entry) == result["directory"], "reviewed entry was substituted")
            finally:
                os.close(directory)
            return json.loads(canonical(receipt))
        except Exception as error:
            raise Denied("independent result is unavailable, stale or mismatching; decision denied") from error

    def _grant(self, grant, current):
        _check(isinstance(grant, dict) and set(grant) == {"scope", "kind", "id", "attempt",
               "packet", "destination", "inputs", "executable", "expires", "limits", "effects"},
               "incomplete materialization grant")
        _check(grant["scope"] == "synthetic" and grant["kind"] == "B1_MATERIALIZATION_SYNTHETIC"
               and all(_name(grant[k]) and grant[k].startswith("synthetic-") for k in ("id", "attempt"))
               and grant["id"] not in self.grants and grant["attempt"] not in self.attempts
               and grant["packet"] == current["packet"] and _name(grant["destination"])
               and grant["destination"] != "records", "grant binding or uniqueness mismatch")
        _check(type(grant["expires"]) in (int, float) and self.clock() < grant["expires"], "expired grant")
        _check(grant["limits"] == {"wall_seconds": 30, "stop_seconds": 5, "memory_bytes": 134217728,
                                   "file_bytes": 65536, "diagnostic_bytes": 4096}, "unapproved limits")
        _check(grant["effects"] == ["candidate_directory", "two_payloads", "records", "two_copy_children",
                                    "diagnostic_pipe", "bounded_stop"], "unapproved effect allowance")
        _check(isinstance(grant["inputs"], dict) and set(grant["inputs"]) == {"source", "companion", "export"},
               "three original-input bindings are required")
        identity_fields = {"device", "inode", "bytes", "uid", "gid", "mode", "links",
                           "mtime_ns", "ctime_ns", "sha256"}
        for name, binding in grant["inputs"].items():
            fields = identity_fields | ({"range"} if name != "export" else set())
            _check(isinstance(binding, dict) and set(binding) == fields
                   and _hex(binding.get("sha256"))
                   and all(type(binding[k]) is int and binding[k] >= 0
                           for k in identity_fields - {"sha256"})
                   and 0 < binding["bytes"] <= MAX_INPUT_BYTES
                   and binding["links"] == 1 and binding["mode"] == 0o400,
                   "invalid bounded input binding")
        for name, binding in grant["inputs"].items():
            if name != "export":
                _check(binding["bytes"] <= 65536 and isinstance(binding.get("range"), list)
                       and len(binding["range"]) == 2
                       and all(type(x) is int for x in binding["range"])
                       and 0 <= binding["range"][0] < binding["range"][1] <= grant["inputs"]["export"]["bytes"]
                       and binding["range"][1] - binding["range"][0] == binding["bytes"], "invalid export range")
        executable = grant["executable"]
        _check(isinstance(executable, dict) and set(executable) == identity_fields | {"path"}
               and _hex(executable.get("sha256"))
               and all(type(executable[k]) is int and executable[k] >= 0
                       for k in identity_fields - {"sha256"})
               and 0 < executable["bytes"] <= 32 * 1024 * 1024
               and isinstance(executable["path"], str) and os.path.isabs(executable["path"])
               and os.path.realpath(executable["path"]) == executable["path"],
               "exact copy executable binding is required")

    def _fresh(self, case, deadline):
        current = self.cases[case]
        _check(not self.blocked and current["state"] == "O2" and current["consumed"]
               and self.clock() < min(current["expires"], current["grant"]["expires"])
               and time.monotonic() < deadline,
               "authority or materialization deadline ended")

    def copy(self, case, inputs, executable, *, wall_seconds=30):
        """Consume two synthetic copy slots, preserving partial objects on any loss.

        A shorter synthetic deadline may exercise stopping. No caller can extend
        the fixed thirty-second bound. Production never reaches this interface.
        """
        _check(case in self.cases and self.cases[case]["state"] == "O2"
               and not self.cases[case].get("started") and not self.blocked, "copy is not eligible")
        _check(type(wall_seconds) in (int, float) and 0 < wall_seconds <= 30, "invalid deadline")
        current = self.cases[case]
        grant = current["grant"]
        deadline = time.monotonic() + wall_seconds
        candidate_fd = -1
        try:
            _check(os.getuid() != 0 and os.geteuid() != 0,
                   "synthetic copying requires an unprivileged UID for RLIMIT_NPROC")
            self._active_expiry = min(current["expires"], grant["expires"])
            self._fresh(case, deadline)
            _check(set(inputs) == {"source", "companion", "export"}, "missing input descriptors")
            self._inputs(inputs, grant, executable)
            _check(all(os.lseek(fd, 0, os.SEEK_CUR) == 0 for fd in inputs.values()),
                   "accepted inputs must initially be at offset zero")
            self._commit("effect", case, {"name": "mkdir", "destination": grant["destination"]})
            current["started"] = True
            self._fresh(case, deadline)
            os.mkdir(grant["destination"], mode=0o700, dir_fd=self.root_fd)
            candidate_fd = os.open(grant["destination"], os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
                                   | os.O_CLOEXEC, dir_fd=self.root_fd)
            directory = os.fstat(candidate_fd)
            outputs = {}
            _check(directory.st_uid == os.getuid() and directory.st_gid == os.getgid()
                   and stat.S_IMODE(directory.st_mode) == 0o700, "candidate ownership/mode mismatch")
            for name, filename in (("source", "qualification_authority.py"),
                                   ("companion", "source_review_packet.md")):
                self._fresh(case, deadline)
                self._inputs(inputs, grant, executable)
                self._commit("effect", case, {"name": name + "_create", "entry": filename})
                self._fresh(case, deadline)
                output = os.open(filename, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                                 | os.O_CLOEXEC, 0o400, dir_fd=candidate_fd)
                try:
                    self._output(output, grant["inputs"][name], empty=True)
                    self._commit("effect", case, {"name": name + "_launch", "slot": len(current["copies"]) + 1})
                    self._fresh(case, deadline)
                    _check(os.lseek(inputs[name], 0, os.SEEK_CUR) == 0,
                           "copy input offset is not zero")
                    # Reserve before fork. An uncertain fork result never refunds a slot.
                    current["copies"].append(name)
                    observation = self._launch(inputs[name], output, executable, candidate_fd, deadline)
                    self._fresh(case, deadline)
                    self._output(output, grant["inputs"][name])
                    os.fsync(output)
                    self._output(output, grant["inputs"][name])
                    output_identity = _metadata(os.fstat(output))
                    outputs[name] = output_identity
                finally:
                    os.close(output)
                # Required acknowledgment occurs after synchronization and writer closure.
                self._commit("checkpoint", case, {"name": name, "output": output_identity,
                                                    "child": observation, "fsync": True,
                                                    "writer_closed": True})
            self._fresh(case, deadline)
            self._commit("effect", case, {"name": "finalize_directory"})
            self._fresh(case, deadline)
            os.fchmod(candidate_fd, 0o500)
            os.fsync(candidate_fd)
            os.fsync(self.root_fd)
            result = os.fstat(candidate_fd)
            entry = os.stat(grant["destination"], dir_fd=self.root_fd, follow_symlinks=False)
            _check((entry.st_dev, entry.st_ino) == (result.st_dev, result.st_ino)
                   == (directory.st_dev, directory.st_ino) and stat.S_IMODE(result.st_mode) == 0o500,
                   "candidate entry substitution")
            self._inputs(inputs, grant, executable)
            self._commit("checkpoint", case, {"name": "producer", "directory": _metadata(result),
                                                "sync_order": ["source", "companion", "directory", "parent"],
                                                "active_writers": False})
            current["candidate"] = _metadata(result)
            current["outputs"] = outputs
            current["producer_head"] = self.head
            current["complete"] = True
            return json.loads(canonical(current))
        except BaseException as error:
            if not self.blocked:
                try:
                    self._append("halt", case, {"reason": type(error).__name__,
                                 "last_confirmed_state": current["state"], "disposition": "requires_C_decision"})
                except BaseException:
                    pass
            self.blocked = True
            raise Denied("copy stopped; retain objects, no repair, retry or promotion") from error
        finally:
            if candidate_fd >= 0:
                os.close(candidate_fd)

    def _inputs(self, inputs, grant, executable):
        for name, fd in inputs.items():
            _check(fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY,
                   "input descriptor is writable")
            actual = identify(fd)
            expected = {k: v for k, v in grant["inputs"][name].items() if k != "range"}
            _check(actual == expected and actual["links"] == 1 and actual["mode"] == 0o400,
                   "input identity/custody changed")
        for name in ("source", "companion"):
            first, end = grant["inputs"][name]["range"]
            _check(os.pread(inputs["export"], end - first, first)
                   == os.pread(inputs[name], end - first, 0)
                   and os.pread(inputs["export"], 1, end - 1) == b"\n", "export equality/final LF mismatch")
        actual = identify(executable)
        expected = {k: v for k, v in grant["executable"].items() if k != "path"}
        path = grant["executable"]["path"]
        _check(isinstance(path, str) and os.path.isabs(path) and os.path.realpath(path) == path,
               "executable path is not canonical")
        entry = os.stat(path, follow_symlinks=False)
        _check(actual == expected and _metadata(entry) == _metadata(os.fstat(executable))
               and actual["mode"] & 0o111
               and not actual["mode"] & 0o7022 and os.pread(executable, 4, 0) == b"\x7fELF"
               and FD_EXECUTION
               and fcntl.fcntl(executable, fcntl.F_GETFL) & os.O_ACCMODE == os.O_RDONLY,
               "executable substitution or writable dependency")

    @staticmethod
    def _output(fd, expected, empty=False):
        info = os.fstat(fd)
        _check(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
               and stat.S_IMODE(info.st_mode) == 0o400
               and info.st_uid == os.getuid() and info.st_gid == os.getgid()
               and info.st_size == (0 if empty else expected["bytes"]), "output metadata mismatch")

    def _launch(self, input_fd, output_fd, executable_fd, directory_fd, deadline):
        read_fd, write_fd = os.pipe2(os.O_CLOEXEC)
        child = None
        try:
            child = os.fork()
            if child == 0:
                try:
                    os.setpgid(0, 0)
                    os.umask(0o077)
                    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
                    resource.setrlimit(resource.RLIMIT_AS, (134217728, 134217728))
                    resource.setrlimit(resource.RLIMIT_FSIZE, (65536, 65536))
                    resource.setrlimit(resource.RLIMIT_CPU, (30, 30))
                    # The synthetic dd must be single-threaded. No descendant may
                    # inherit a writer or escape direct-child stop observation.
                    resource.setrlimit(resource.RLIMIT_NPROC, (0, 0))
                    os.fchdir(directory_fd)
                    os.dup2(input_fd, 0)
                    os.dup2(output_fd, 1)
                    os.dup2(write_fd, 2)
                    # fd 3 exists only until exec. Native ELF execution uses
                    # the accepted object even if its pathname is replaced.
                    os.dup2(executable_fd, 3, inheritable=False)
                    maximum = resource.getrlimit(resource.RLIMIT_NOFILE)[0]
                    os.closerange(4, maximum)
                    # argv[0] selects dd in the explicitly bound BusyBox binary
                    # locally and GNU dd in CI. No dependency fallback is allowed.
                    # Production must qualify the loader/library closure too.
                    os.execve(3,
                              ["dd", "bs=65536", "status=none"],
                              {"LC_ALL": "C", "LANG": "C", "TZ": "UTC"})
                except BaseException as error:
                    os.write(2, (type(error).__name__ + ":" + str(getattr(error, "errno", ""))).encode("ascii"))
                    os._exit(127)
            self.active_child = child
            os.close(write_fd)
            write_fd = -1
            diagnostic = bytearray()
            while True:
                _check(time.monotonic() < deadline, "copy deadline reached")
                _check(self.clock() < self._active_expiry, "grant expired during child execution")
                readable, _, _ = select.select([read_fd], [], [], min(0.01, max(0, deadline - time.monotonic())))
                if readable:
                    diagnostic.extend(os.read(read_fd, 4097 - len(diagnostic)))
                    _check(len(diagnostic) <= 4096, "diagnostic bound exceeded")
                waited, status = os.waitpid(child, os.WNOHANG)
                if waited:
                    child = None
                    self.active_child = None
                    _check(os.WIFEXITED(status) and os.WEXITSTATUS(status) == 0,
                           "abnormal copy exit: " + str(os.waitstatus_to_exitcode(status))
                           + " diagnostic=" + diagnostic.hex())
                    return {"pid": waited, "exit": 0, "diagnostic_hex": diagnostic.hex(),
                            "writer_terminated": True}
        except BaseException:
            if child:
                self._stop(child)
            raise
        finally:
            os.close(read_fd)
            if write_fd >= 0:
                os.close(write_fd)

    def _stop(self, child):
        """Stop only the retained child PID; never kill a caller-supplied PID/group."""
        try:
            os.kill(child, signal.SIGKILL)
        except ProcessLookupError:
            pass
        stop_deadline = time.monotonic() + 5
        while time.monotonic() < stop_deadline:
            waited, _ = os.waitpid(child, os.WNOHANG)
            if waited:
                self.active_child = None
                return
            time.sleep(0.005)
        raise Denied("UNCERTAIN: child stop confirmation unavailable within five seconds")
