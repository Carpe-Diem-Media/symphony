"""External operator gate for an already authenticated P08 context.

The caller supplies independently installed trust, fresh status and custody
observations. None is read from an approval bundle or environment flag. The
command-line entry point refuses because this source stage enrolls no operator.
Register files are authority history. They are never reset after a failed run.
"""

import fcntl
import importlib.util
import json
import os
from pathlib import Path
import re
import signal
import selectors
import stat
import subprocess
import time

_spec = importlib.util.spec_from_file_location("p08_gate_verifier", Path(__file__).with_name("verify.py"))
verify = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(verify)
Refusal = verify.Refusal
_ID = re.compile(r"[0-9a-f]{32}\Z")
_NONCE = re.compile(r"[0-9a-f]{64}\Z")


def _require(condition, code):
    if not condition:
        raise Refusal(code)


def _directory(path):
    path = Path(path)
    _require(path.is_absolute() and str(path) == os.path.normpath(str(path)), "REGISTER_INVALID")
    for part in [path, *path.parents]:
        info = part.lstat()
        _require(stat.S_ISDIR(info.st_mode) and not stat.S_ISLNK(info.st_mode), "REGISTER_INVALID")
    info = path.stat()
    _require(info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o700, "REGISTER_INVALID")
    return path


def _read_fd(fd, limit):
    info = os.fstat(fd)
    _require(stat.S_ISREG(info.st_mode) and info.st_nlink == 1
             and info.st_uid == os.geteuid() and stat.S_IMODE(info.st_mode) == 0o600,
             "REGISTER_INVALID")
    raw = os.read(fd, limit + 1)
    _require(len(raw) <= limit, "REGISTER_INVALID")
    return raw


class OneUseRegister:
    """Conservative no-replace markers under independently controlled custody.

    The owner/operator establishes the directory and epoch separately. This
    class does not initialize a missing register. A partial transaction burns
    its identities because every later admission checks all three marker names.
    """

    def __init__(self, directory, epoch):
        self.path = _directory(directory)
        _require(type(epoch) is int and 0 < epoch <= 2**64 - 1, "STATUS_INVALID")
        self.epoch = epoch
        self.dir_fd = os.open(self.path, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
        self.lock_fd = None

    def __enter__(self):
        try:
            self.lock_fd = os.open(".lock", os.O_CREAT | os.O_RDWR | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                                   0o600, dir_fd=self.dir_fd)
            _read_fd(self.lock_fd, 0)
            until = time.monotonic() + 1.0
            while True:
                try:
                    fcntl.flock(self.lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                    break
                except BlockingIOError:
                    _require(time.monotonic() < until, "REGISTER_BUSY")
                    time.sleep(0.005)
            a = os.fstat(self.lock_fd)
            b = os.stat(".lock", dir_fd=self.dir_fd, follow_symlinks=False)
            _require((a.st_dev, a.st_ino) == (b.st_dev, b.st_ino), "REGISTER_INVALID")
            raw = self._read_existing("epoch.json", 128)
            _require(raw == verify.canonical({"epoch": self.epoch}), "STATUS_INVALID")
            return self
        except OSError as error:
            self.close()
            raise Refusal("REGISTER_INVALID") from error
        except BaseException:
            self.close()
            raise

    def __exit__(self, *unused):
        self.close()

    def check_custody(self):
        try:
            current = self.path.lstat()
            opened = os.fstat(self.dir_fd)
            _require(stat.S_ISDIR(current.st_mode) and current.st_uid == os.geteuid()
                     and stat.S_IMODE(current.st_mode) == 0o700
                     and (current.st_dev, current.st_ino) == (opened.st_dev, opened.st_ino),
                     "REGISTER_UNCERTAIN")
            current_lock = os.stat('.lock', dir_fd=self.dir_fd, follow_symlinks=False)
            opened_lock = os.fstat(self.lock_fd)
            _require((current_lock.st_dev, current_lock.st_ino) == (opened_lock.st_dev, opened_lock.st_ino),
                     "REGISTER_UNCERTAIN")
        except OSError as error:
            raise Refusal("REGISTER_UNCERTAIN") from error

    def close(self):
        if self.lock_fd is not None:
            os.close(self.lock_fd)
            self.lock_fd = None
        if self.dir_fd is not None:
            os.close(self.dir_fd)
            self.dir_fd = None

    def _read_existing(self, name, limit):
        # O_NONBLOCK must precede fstat: a FIFO can otherwise wait at open.
        try:
            fd = os.open(name, os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                         dir_fd=self.dir_fd)
            try:
                return _read_fd(fd, limit)
            finally:
                os.close(fd)
        except OSError as error:
            raise Refusal("REGISTER_INVALID") from error

    @staticmethod
    def _identities(grant):
        values = [grant.get("grant_id"), grant.get("run_id"), grant.get("nonce")]
        _require(all(isinstance(v, str) and p.fullmatch(v)
                     and any(c != "0" for c in v)
                     for v, p in zip(values, [_ID, _ID, _NONCE])), "FORMAT_INVALID")
        return ["grant-" + values[0] + ".json", "run-" + values[1] + ".json", "nonce-" + values[2] + ".json"]

    def _write(self, name, record):
        raw = verify.canonical(record)
        _require(len(raw) <= 8192, "REGISTER_INVALID")
        fd = os.open(name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                     0o600, dir_fd=self.dir_fd)
        try:
            offset = 0
            while offset < len(raw):
                written = os.write(fd, raw[offset:])
                _require(written > 0, "REGISTER_UNCERTAIN")
                offset += written
            os.fsync(fd)
        finally:
            os.close(fd)

    def validate_history(self):
        """Validate all consumption indexes before deciding replay or admission."""
        self.check_custody()
        # A previous crash can leave only one of the three index markers.
        # Identical partial indexes remain valid and burn all three identities.
        # Validate the entire history before returning a replay decision.
        entries = os.listdir(self.dir_fd)
        _require(len(entries) <= 10000, "REGISTER_INVALID")
        bindings = {}
        for previous in entries:
            if not previous.startswith(("grant-", "run-", "nonce-")):
                continue
            raw = self._read_existing(previous, 8192)
            try:
                old = json.loads(raw)
            except (ValueError, UnicodeError, RecursionError) as error:
                raise Refusal("REGISTER_UNCERTAIN") from error
            _require(isinstance(old, dict)
                     and set(old) == {"epoch", "grant_id", "nonce", "run_id", "state"}
                     and type(old["epoch"]) is int and old["epoch"] == self.epoch
                     and isinstance(old["state"], str) and old["state"] in ("CONSUMED", "REFUSED"),
                     "REGISTER_UNCERTAIN")
            try:
                old_names = self._identities(old)
            except Refusal as error:
                # _identities rejects malformed marker identifiers only.
                raise Refusal("REGISTER_UNCERTAIN") from error
            _require(previous in old_names and raw == verify.canonical(old), "REGISTER_UNCERTAIN")
            for key in ("grant_id", "run_id", "nonce"):
                identity = (key, old[key])
                _require(identity not in bindings or bindings[identity] == raw, "REGISTER_UNCERTAIN")
                bindings[identity] = raw
        return bindings

    def consume(self, grant, state="CONSUMED"):
        _require(state in {"CONSUMED", "REFUSED"}, "REGISTER_INVALID")
        names = self._identities(grant)
        history = self.validate_history()
        if any((key, grant[key]) in history for key in ("grant_id", "run_id", "nonce")):
            raise Refusal("GRANT_REPLAY")
        for name in names:
            try:
                os.stat(name, dir_fd=self.dir_fd, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise Refusal("GRANT_REPLAY")
        record = {"epoch": self.epoch, "grant_id": grant["grant_id"],
                  "nonce": grant["nonce"], "run_id": grant["run_id"], "state": state}
        try:
            for name in names:
                self._write(name, record)
                # The first marker is the reservation commit point and names
                # all three identities. Sync its directory entry before any
                # further state transition or possible launch.
                os.fsync(self.dir_fd)
        except (OSError, Refusal) as error:
            raise Refusal("REGISTER_UNCERTAIN") from error

    def event(self, grant, state, details=""):
        self.check_custody()
        _require(state in {"LAUNCHED", "COMPLETED", "FAILED", "REFUSED", "UNCERTAIN"}, "REGISTER_INVALID")
        self._identities(grant)
        for sequence in range(1, 17):
            name = "event-" + grant["grant_id"] + "-" + str(sequence).zfill(2) + ".json"
            try:
                self._write(name, {"details": details[:128], "epoch": self.epoch,
                                   "grant_id": grant["grant_id"], "state": state})
            except FileExistsError:
                continue
            os.fsync(self.dir_fd)
            return
        raise Refusal("REGISTER_INVALID")


def _observe_clock(checked, session, monotonic_ns):
    """Advance one attempt's clock floor without aliasing provider state."""
    baseline = checked.get("_clock_state")
    if baseline is None:
        initial = checked.get("external_status", {})
        _require(isinstance(initial, dict), "CLOCK_CONTEXT_INVALID")
        baseline = (initial.get("clock_session_id"), initial.get("monotonic_ns"))
    _require(isinstance(baseline, tuple) and len(baseline) == 2, "CLOCK_CONTEXT_INVALID")
    initial_session, previous_ns = baseline
    report = checked.get("action_observation", {})
    _require(isinstance(report, dict), "CLOCK_CONTEXT_INVALID")
    completed_ns = report.get("completed_monotonic_ns")
    _require(isinstance(initial_session, str) and _ID.fullmatch(initial_session)
             and isinstance(session, str) and _ID.fullmatch(session)
             and session == initial_session == report.get("clock_session_id"),
             "CLOCK_CONTEXT_INVALID")
    _require(type(completed_ns) is int and type(previous_ns) is int and type(monotonic_ns) is int
             and 0 <= completed_ns <= previous_ns <= monotonic_ns < 2**64,
             "CLOCK_CONTEXT_INVALID")
    checked["_clock_state"] = (initial_session, monotonic_ns)


def check_current(checked, status):
    """Check the entire current uncertainty interval without expiry grace."""
    _require(isinstance(status, dict), "STATUS_INVALID")
    lower, upper = status.get("now_min"), status.get("now_max")
    _require(type(lower) is int and type(upper) is int and 0 <= lower <= upper < 2**64
             and upper - lower <= 30, "CLOCK_CONTEXT_INVALID")
    _require(type(status.get("trust_epoch")) is int and status["trust_epoch"] == checked["grant"]["trust_epoch"],
             "STATUS_INVALID")
    _require(not status.get("revoked_ids", ["unknown"]), "STATUS_INVALID")
    baseline = checked.get("external_status", {})
    for key in ("enrollment_sha256", "current_decisions_sha256", "revocations_sha256", "operator_id",
                "clock_evidence_sha256", "register_observation_sha256", "policy_a_evidence_sha256"):
        if key in baseline:
            _require(status.get(key) == baseline[key], "STATUS_INVALID")
    for record in checked["records"].values():
        _require(record.get("issued_at", 0) <= lower, "APPROVAL_STALE")
        _require(lower >= record.get("not_before", 0), "APPROVAL_STALE")
        _require(upper < record.get("expires_at", 2**64 - 1), "APPROVAL_STALE")
    for key in checked["roles"].values():
        _require(lower >= key["not_before"] and upper < key["expires_at"], "APPROVAL_STALE")
    _observe_clock(checked, status.get("clock_session_id"), status.get("monotonic_ns"))
    return lower, upper


def check_launch(checked, status, observation):
    check_current(checked, status)
    report = checked["action_observation"]
    _require(report.get("purpose") == "ACTION_PREFLIGHT_ONLY", "OBSERVATION_PURPOSE_MISMATCH")
    _require(isinstance(observation, dict), "OBSERVATION_UNAUTHENTICATED")
    _require(report["clock_session_id"] == observation.get("clock_session_id") == status.get("clock_session_id"),
             "CLOCK_CONTEXT_INVALID")
    start, end = report["completed_monotonic_ns"], observation.get("monotonic_ns")
    _require(type(start) is int and type(end) is int and 0 <= start <= end <= 2**64 - 1,
             "CLOCK_CONTEXT_INVALID")
    _require(end - start <= 60_000_000_000, "ACTION_OBSERVATION_STALE")
    grant = checked["grant"]
    for key in ["grant_id", "run_id", "nonce", "source_commit", "source_tree", "command_profile_sha256", "authorization_scope"]:
        _require(observation.get(key) == grant[key], "ACTION_BINDING_MISMATCH")
    _require(observation.get("evidence_sha256") == report["evidence_sha256"], "CUSTODY_FAILURE")
    for key, value in grant.items():
        if key.startswith("observed_"):
            _require(observation.get(key) == value, "CUSTODY_FAILURE")
    for key in ["enrollment_sha256", "current_decisions_sha256", "revocations_sha256", "operator_id"]:
        _require(status.get(key) == checked["external_status"][key], "STATUS_INVALID")
    _observe_clock(checked, observation.get("clock_session_id"), end)
    return True


def _alive_group(group):
    """Read proc process groups; missing or malformed observations refuse."""
    found = []
    for path in Path("/proc").iterdir():
        if not path.name.isdecimal():
            continue
        try:
            raw = (path / "stat").read_text("ascii")
        except FileNotFoundError:
            continue
        except PermissionError as error:
            raise Refusal("PROCESS_OBSERVATION_UNCERTAIN") from error
        fields = raw[raw.rfind(")") + 2:].split()
        if len(fields) > 2 and int(fields[2]) == group:
            found.append(int(path.name))
    return found


def _collect(process, checked, status_provider, deadline):
    """Drain bounded output while continuing the lease and status checks."""
    output = [bytearray(), bytearray()]
    with selectors.DefaultSelector() as selector:
        for index, stream in enumerate((process.stdout, process.stderr)):
            os.set_blocking(stream.fileno(), False)
            selector.register(stream, selectors.EVENT_READ, index)
        try:
            while process.poll() is None or selector.get_map():
                try:
                    check_current(checked, status_provider())
                    _require(time.monotonic() < deadline, "LEASE_TERMINATED")
                except Refusal as error:
                    raise Refusal("LEASE_TERMINATED") from error
                if not selector.get_map():
                    time.sleep(0.005)
                for key, unused in selector.select(0.005):
                    remaining = 65536 - len(output[key.data])
                    try:
                        chunk = os.read(key.fd, min(65536, remaining + 1))
                    except BlockingIOError:
                        continue
                    if not chunk:
                        selector.unregister(key.fileobj)
                    else:
                        output[key.data].extend(chunk)
                        _require(len(output[key.data]) <= 65536, "RESULT_LIMIT_EXCEEDED")
        except BaseException as error:
            error.output = {'stdout':bytes(output[0][:65536]),'stderr':bytes(output[1][:65536]),
                            'truncated':any(len(part)>65536 for part in output)}
            raise
        finally:
            process.stdout.close()
            process.stderr.close()
    process.wait(timeout=2)
    return bytes(output[0]), bytes(output[1])


def execute(bundle, trusted_context, register_root, status_provider, observation_provider):
    """Validate, durably consume and execute one command in the external operator.

    Providers are appointed external observations, never guest callbacks. This
    API is exercised with synthetic providers by the bounded source tests.
    Operational installation and providers require separate owner acceptance.
    """
    current = status_provider()
    _require(isinstance(current, dict), "STATUS_INVALID")
    current = dict(current)
    context = dict(trusted_context, status=current)
    try:
        checked = dict(verify.verify_bundle(bundle, context))
    except Refusal as error:
        authenticated = error.authenticated_grant
        if authenticated is not None:
            # Only a cryptographically verified complete chain may burn IDs.
            # An authenticated late refusal is terminal even before launch.
            with OneUseRegister(register_root, authenticated["trust_epoch"]) as register:
                register.consume(authenticated, "REFUSED")
                register.event(authenticated, "REFUSED", error.code)
        raise
    checked["external_status"] = current
    checked.pop("_clock_state", None)
    grant = checked["grant"]
    command = checked["command"]
    argv = [x["value"] for x in command["argv"]]
    _require(argv and argv[0] == command["executable"]["path"], "EXECUTABLE_PATH_MISMATCH")
    consumed = False
    consumption_attempted = False
    process = None
    stdout, stderr = b'', b''
    with OneUseRegister(register_root, grant["trust_epoch"]) as register:
        # Corrupt pre-existing authority is a pre-admission refusal. It must
        # not append an execution event or attempt a refusal reservation.
        register.validate_history()
        try:
            check_launch(checked, status_provider(), observation_provider(checked))
            consumption_attempted = True
            register.consume(grant)
            consumed = True
            final_status = status_provider()
            check_launch(checked, final_status, observation_provider(checked))
            register.check_custody()
            inventory = verify.parse_profile(
                trusted_context["profiles"][command["executable"]["inventory_sha256"]], "input-inventory")
            verify.verify_installed_artifact(command["executable"], inventory, trusted_context["sealed_roots"],
                                             actual_path=argv[0], actual_argv0=argv[0])
            environment = {x["name"]: x["value"] for x in checked["execution_profile"]["environment"]}
            process = subprocess.Popen(argv, executable=argv[0], cwd=command["working_directory"],
                                       env=environment, close_fds=True, start_new_session=True,
                                       stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            # The finite action has no interactive input. Closing the pipe
            # supplies EOF without opening any filesystem output device.
            process.stdin.close()
            process.stdin = None
            register.event(grant, "LAUNCHED")
            deadline = time.monotonic() + grant["max_duration_s"]
            stdout, stderr = _collect(process, checked, status_provider, deadline)
            _require(not _alive_group(process.pid), "PROCESS_OBSERVATION_UNCERTAIN")
            _require(process.returncode == 0, "QUALIFICATION_FAILED")
            check_current(checked, status_provider())
            register.event(grant, "COMPLETED")
            return {"state": "COMPLETED", "returncode": 0, "stdout": stdout, "stderr": stderr,
                    "grant_id": grant["grant_id"], "run_id": grant["run_id"]}
        except BaseException as error:
            if getattr(error, "code", "") == "GRANT_REPLAY":
                raise
            if process is not None:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                process.wait(timeout=2)
                for stream in (process.stdout, process.stderr):
                    if stream is not None:
                        stream.close()
                error.result = dict(getattr(error,'output',{'stdout':stdout,'stderr':stderr,'truncated':False}),
                                    returncode=process.returncode,grant_id=grant['grant_id'],run_id=grant['run_id'])
            if not consumption_attempted:
                register.consume(grant, "REFUSED")
            details = getattr(error, "code", type(error).__name__)
            if details == "LEASE_TERMINATED" and isinstance(error.__cause__, Refusal):
                details += ":" + error.__cause__.code
            register.event(grant, "FAILED" if consumed else ("UNCERTAIN" if consumption_attempted else "REFUSED"),
                           details)
            raise


def main():
    raise Refusal("INDEPENDENT_OPERATOR_INSTALLATION_NOT_APPROVED")


if __name__ == "__main__":
    try:
        main()
    except Refusal as error:
        raise SystemExit(error.code)
