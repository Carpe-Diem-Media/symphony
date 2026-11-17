"""Finite, nonsecret development driver. Native host alone generates synthetic material.

This does not qualify an operational host permission or a patched Codex holder.
The binding and attempt are supplied by C02 in the integration test; no new attempt
entitlement is allocated here. No credential argument, file or Python RPC exists.
"""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import subprocess
import sys
import time

NATIVE = Path(__file__).resolve().parents[1]
FAULTS = {"none", "missing_permit", "wrong_attempt", "wrong_holder", "wrong_peer", "substituted_holder",
          "bootstrap_failure", "before_materialization", "partial_materialization", "after_materialization",
          "continuous", "launcher_loss", "parent_loss", "ambiguous_provider", "cleanup_failure",
          "observe_failure", "journal_failure", "post_materialization_journal_failure", "ancillary_fd", "manifest_unsealed", "manifest_wrong_identity", "manifest_wrong_binding", "controls_unavailable"}


def read_line(stream, deadline):
    data = bytearray()
    while time.monotonic() < deadline:
        if not select.select([stream], [], [], max(0, deadline - time.monotonic()))[0]:
            break
        byte = os.read(stream.fileno(), 1)
        if not byte:
            break
        if byte == b"\n":
            return data.decode("ascii")
        data.extend(byte)
        if len(data) > 2048:
            raise RuntimeError("Nonsecret native response exceeded its bound")
    return None


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def proc_start(pid):
    text = Path(f"/proc/{pid}/stat").read_text()
    return int(text[text.rindex(")") + 2:].split()[19])


def run(root, binding, attempt, fault, duration, selected_holder=None, pinned_codex=False):
    if len(binding) != 64 or any(c not in "0123456789abcdef" for c in binding):
        raise ValueError("Invalid binding")
    if not attempt or len(attempt) > 128 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in attempt):
        raise ValueError("Invalid attempt")
    if fault not in FAULTS or not 500 <= duration <= 5000:
        raise ValueError("Invalid synthetic test case")
    root = root.resolve()
    os.chmod(root, 0o700)
    if (root / "permission").exists() or (root / "events.jsonl").exists():
        raise ValueError("Refusing reused native evidence root")
    for name in ["home", "codex-home"]:
        (root / name).mkdir(mode=0o700)
    journal = root / "events.jsonl"
    journal.touch(mode=0o600, exist_ok=False)
    binding_file = root / "binding.json"
    if binding_file.exists():
        with binding_file.open("rb") as stream:
            os.fsync(stream.fileno())
    host_path, guard_path, holder = [NATIVE / "build" / name for name in ["host", "guard", "holder-probe"]]
    if pinned_codex and selected_holder is None:
        raise ValueError("Pinned Codex requires the exact explicit executable")
    if selected_holder is not None:
        holder = selected_holder.resolve()
    env = {"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"}
    start = time.monotonic()
    deadline = start + duration / 1000
    host = subprocess.Popen([str(host_path), str(root), fault, binding, attempt], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    guard = None
    actual_guard_pid = None
    parent_loss_verified = False
    guard_pidfd = None
    controls = {}
    native_exec = False
    try:
        if read_line(host.stdout, start + 2) != "HOST_LISTENING":
            raise RuntimeError("Native synthetic owner unavailable")
        guard_args = [str(guard_path), str(root), str(holder), digest(holder), binding, attempt, fault]
        if pinned_codex:
            guard_args.append("--pinned-codex")
        if fault == "parent_loss":
            guard_args = [sys.executable, "-I", str(Path(__file__).resolve()), "--parent-proxy", *guard_args]
        guard = subprocess.Popen(guard_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
        actual_guard_pid = guard.pid
        if fault == "parent_loss":
            identity_line = read_line(guard.stdout, start + 2)
            if not identity_line or not identity_line.startswith("GUARD_PID "):
                raise RuntimeError("Parent-loss process identity unavailable")
            actual_guard_pid = int(identity_line.split()[1])
            guard_pidfd = os.pidfd_open(actual_guard_pid)
        if read_line(guard.stdout, start + 2) != "WAITING_PERMISSION":
            raise RuntimeError("Native guard did not reach permission boundary")
        if fault != "missing_permit":
            holder_hash = "0" * 64 if fault == "substituted_holder" else digest(holder)
            guard_start = proc_start(actual_guard_pid) + (1 if fault == "wrong_peer" else 0)
            fields = ["C02_SYNTHETIC_NATIVE_V1", binding, attempt, holder_hash, digest(guard_path), str(actual_guard_pid),
                      str(guard_start), str(int(deadline * 1000))]
            fd = os.open(root / "permission", os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
            with os.fdopen(fd, "w") as stream:
                stream.write("\n".join(fields) + "\n")
                stream.flush()
                os.fsync(stream.fileno())
            directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
            os.fsync(directory)
            os.close(directory)
        guard.stdin.write(b"GO\n")
        guard.stdin.flush()
        ready = read_line(guard.stdout, deadline + .1)
        if ready:
            record = json.loads(ready)
            if record.get("ready") is not True or record.get("binding") != binding:
                raise RuntimeError("Native holder identity/readiness mismatch")
            controls = record["controls"]
            native_exec = True
            if fault in {"launcher_loss", "parent_loss"}:
                # Kill the actual native guard for launcher loss. For parent
                # loss kill its real parent process; PR_SET_PDEATHSIG must kill
                # guard and holder, observed independently by the native owner.
                guard.kill()
                if fault == "parent_loss":
                    guard.wait(timeout=.3)
                    parent_loss_verified = (actual_guard_pid != guard.pid and guard.returncode == -signal.SIGKILL
                                            and bool(select.select([guard_pidfd], [], [], .4)[0]))
        guard.wait(timeout=max(.2, deadline - time.monotonic() + .3))
        # Before materialization, no client may have connected. Stop only this
        # exact native owner process instead of waiting its startup interval.
        if not (root / "consumed").exists() and host.poll() is None:
            host.terminate()
        host.wait(timeout=max(.2, deadline - time.monotonic() + .4))
    finally:
        if guard_pidfd is not None:
            os.close(guard_pidfd)
        for process in [guard, host]:
            if process and process.poll() is None:
                process.kill()
                process.wait(timeout=1)
        for process in [guard, host]:
            if process:
                for stream in [process.stdin, process.stdout, process.stderr]:
                    if stream and not stream.closed:
                        stream.close()
    events = [json.loads(line) for line in journal.read_text().splitlines()]
    states = [event["state"] for event in events]
    consumed = (root / "consumed").exists()
    if consumed:
        # A separately executed restarted owner must deny before opening a
        # materialization socket. It must preserve the original claim.
        restarted = subprocess.run([str(host_path), str(root), "none", binding, attempt],
                                   capture_output=True, timeout=1, env=env)
        replay_refused = restarted.returncode == 0 and restarted.stdout == b"REUSE_REFUSED\n"
    else:
        replay_refused = (root / "permission").exists() and guard is not None and guard.poll() is not None
    stop = "TERMINATION_VERIFIED" in states
    disposition = "CONTROLLED_REFUSAL" if "DISPOSAL_VERIFIED" in states else ("QUARANTINED" if consumed else "REFUSED")
    return {"binding": binding, "attempt": attempt, "disposition": disposition, "native_exec": native_exec,
            "stop_verified": stop, "inference_succeeded": False, "controls": controls, "consumed": consumed,
            "materialization_count": states.count("SYNTHETIC_MATERIALIZED"), "replay_refused": replay_refused,
            "elapsed_ms": int((time.monotonic() - start) * 1000), "evidence_root": str(root),
            "parent_loss_verified": parent_loss_verified, "pinned_codex": pinned_codex, "qualified_host": False,
            "disposal_scope": "synthetic_process_and_channel_only"}


def main():
    parent = os.getppid()
    if ctypes.CDLL(None).prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
        raise RuntimeError("Native controller parent identity unavailable")
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--attempt", required=True)
    parser.add_argument("--holder", type=Path)
    parser.add_argument("--pinned-codex", action="store_true")
    parser.add_argument("--fault", choices=sorted(FAULTS), default="none")
    parser.add_argument("--duration-ms", type=int, default=2500)
    args = parser.parse_args()
    native = run(args.root, args.binding, args.attempt, args.fault, args.duration_ms, args.holder, args.pinned_codex)
    binding_file = args.root / "binding.json"
    binding = json.loads(binding_file.read_text()) if binding_file.exists() else None
    if binding_file.exists():
        with binding_file.open("rb") as stream:
            os.fsync(stream.fileno())
    correlation = args.root / "correlation.json"
    fd = os.open(correlation, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "w") as stream:
        json.dump({"scope": "native_synthetic_only", "binding": binding, "native": native}, stream, sort_keys=True)
        stream.flush()
        os.fsync(stream.fileno())
    directory = os.open(args.root, os.O_DIRECTORY)
    os.fsync(directory)
    os.close(directory)
    print(json.dumps(native, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--parent-proxy":
        child = subprocess.Popen(sys.argv[2:], stdin=sys.stdin, stdout=subprocess.PIPE, stderr=sys.stderr)
        print("GUARD_PID " + str(child.pid), flush=True)
        for data in child.stdout:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        raise SystemExit(child.wait())
    main()
