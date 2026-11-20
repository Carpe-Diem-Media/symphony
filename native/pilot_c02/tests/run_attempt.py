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
import stat
import subprocess
import sys
import time

NATIVE = Path(__file__).resolve().parents[1]
SCHEMA2_PROFILE = "H100_FUNCTIONAL_CODEX_SYNTHETIC_V1"
SCHEMA2_REASON = "SYMPHONY_PROVIDER_BOUNDARY_UNAVAILABLE"
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


def canonical(value):
    return json.dumps(value, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")


def read_private_json(path, maximum=1_048_576):
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        info = os.fstat(fd)
        if not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid() or info.st_mode & 0o077 or info.st_size > maximum:
            raise ValueError("Unsafe or oversized schema2 input")
        raw = bytearray()
        while len(raw) <= maximum:
            chunk = os.read(fd, min(65536, maximum + 1 - len(raw)))
            if not chunk:
                break
            raw.extend(chunk)
        if len(raw) > maximum:
            raise ValueError("Oversized schema2 input")
        value = json.loads(raw)
        if not isinstance(value, dict):
            raise ValueError("Invalid schema2 input")
        return value
    finally:
        os.close(fd)


def schema2_manifest(root, binding, attempt, holder):
    binding_path = root / "binding.json"
    input_path = root / "schema2-input.json"
    bound = read_private_json(binding_path)
    supplied = read_private_json(input_path)
    context = supplied.get("context")
    cancel = supplied.get("cancel")
    if not isinstance(context, dict) or type(cancel) is not bool:
        raise ValueError("Invalid schema2 input shape")
    identity = bound.get("attempt")
    grant = bound.get("grant")
    profile = bound.get("profile")
    selection = bound.get("selection")
    if not all(isinstance(v, dict) for v in (identity, grant, profile, selection)):
        raise ValueError("Incomplete attempt binding")
    if identity.get("runtime_attempt_id") != attempt:
        raise ValueError("Schema2 attempt does not match its bound identity")
    holder_hash = digest(holder)
    expected = {
        "binding_id": binding,
        "attempt_id": attempt,
        "work_item_id": grant.get("work_item_id"),
        "project_id": grant.get("project_id"),
        "role": "Planner",
        "model_slug": profile.get("model"),
        "credential_generation": str(selection.get("credential_generation")),
        "holder_sha256": holder_hash,
        "holder_profile": SCHEMA2_PROFILE,
        "holder_profile_digest": selection.get("holder_profile_identity"),
        "permission_reference": selection.get("host_permission_ref"),
        "host_identity": selection.get("host_id"),
        "boot_identity": selection.get("host_boot_id"),
        "workspace": bound.get("workspace"),
        "home": str(root.resolve() / "home"),
        "codex_home": str(root.resolve() / "codex-home"),
        "configuration_digest": grant.get("config_identity"),
        "source_commit": grant.get("source_commit"),
        "source_tree": grant.get("source_tree"),
    }
    if context.get("binding_id") != binding or context.get("attempt_id") != attempt:
        raise ValueError("Schema2 context does not match the native attempt")
    if selection.get("holder_artifact_identity") != holder_hash:
        raise ValueError("Pinned executable does not match the bound holder artifact")
    for key, value in expected.items():
        if value is None or context.get(key) != value:
            raise ValueError("Schema2 context does not match its bound authority")
    grant_id = context.get("grant_id")
    if not isinstance(grant_id, str) or len(grant_id) != 64 or any(c not in "0123456789abcdef" for c in grant_id):
        raise ValueError("Invalid schema2 grant digest")
    if not isinstance(context.get("policy_text"), str) or not isinstance(context.get("prompt_text"), str):
        raise ValueError("Schema2 policy and prompt must be text")
    policy_root = context.get("policy_root")
    if not isinstance(policy_root, str) or not Path(policy_root).is_absolute() or str(Path(policy_root).resolve(strict=True)) != policy_root:
        raise ValueError("Schema2 policy root must be canonical")
    if hashlib.sha256(context["policy_text"].encode("utf-8")).hexdigest() != context.get("policy_digest"):
        raise ValueError("Schema2 policy digest mismatch")
    if hashlib.sha256(context["prompt_text"].encode("utf-8")).hexdigest() != context.get("text_digest"):
        raise ValueError("Schema2 prompt digest mismatch")
    if type(context.get("wait_for_interrupt")) is not bool or context["wait_for_interrupt"] != cancel:
        raise ValueError("Schema2 cancellation flag does not match its context")
    catalog = context.get("model_catalog")
    models = catalog.get("models") if isinstance(catalog, dict) else None
    if not isinstance(models, list) or not any(isinstance(model, dict) and model.get("slug") == context.get("model_slug") for model in models):
        raise ValueError("Schema2 model is absent from its catalog")
    context["model_catalog_digest"] = hashlib.sha256(canonical(context.get("model_catalog"))).hexdigest()
    context["context_digest"] = hashlib.sha256(canonical(context)).hexdigest()
    manifest = {"schema": 2, "profile": SCHEMA2_PROFILE, "binding": binding,
                "attempt": attempt, "holder_sha256": holder_hash, "fault": "none",
                "context": context}
    return manifest, cancel


def drive_schema2(stdin, stdout, deadline, prompt, cancel):
    events = []

    def send(frame):
        stdin.write(canonical(frame) + b"\n")
        stdin.flush()

    def receive():
        raw = bytearray()
        while time.monotonic() < deadline:
            remaining = max(0, deadline - time.monotonic())
            if not select.select([stdout], [], [], remaining)[0]:
                break
            byte = os.read(stdout.fileno(), 1)
            if not byte:
                break
            if byte == b"\n":
                break
            raw.extend(byte)
            if len(raw) > 65536:
                raise ValueError("Schema2 protocol frame exceeded its bound")
        if not raw or len(events) >= 7:
            raise TimeoutError("Bounded schema2 protocol frame missing")
        event = json.loads(raw.decode("utf-8"))
        if not isinstance(event, dict):
            raise ValueError("Invalid schema2 protocol frame")
        events.append(event)
        return event

    send({"id": 1, "method": "initialize", "params": {"clientInfo": {"name": "symphony-native-schema2", "version": "1"}}})
    if receive().get("id") != 1 or "result" not in events[-1]:
        raise ValueError("Schema2 initialize response mismatch")
    send({"method": "initialized", "params": {}})
    send({"id": 2, "method": "thread/start", "params": {}})
    reply, started = receive(), receive()
    thread = reply.get("result", {}).get("thread", {}).get("id")
    if reply.get("id") != 2 or not thread or started.get("method") != "thread/started" or started.get("params", {}).get("thread", {}).get("id") != thread:
        raise ValueError("Schema2 thread frames do not correlate")
    send({"id": 3, "method": "turn/start", "params": {"threadId": thread, "input": [{"type": "text", "text": prompt}]}})
    reply, started = receive(), receive()
    turn = reply.get("result", {}).get("turn", {}).get("id")
    if reply.get("id") != 3 or not turn or started.get("method") != "turn/started" or started.get("params", {}).get("threadId") != thread or started.get("params", {}).get("turn", {}).get("id") != turn:
        raise ValueError("Schema2 turn frames do not correlate")
    if cancel:
        send({"id": 4, "method": "turn/interrupt", "params": {"threadId": thread, "turnId": turn}})
        ack, terminal = receive(), receive()
        if ack.get("id") != 4 or ack.get("result") != {} or terminal.get("method") != "turn/completed" or terminal.get("params", {}).get("threadId") != thread:
            raise ValueError("Schema2 interrupt frames do not correlate")
        result_turn = terminal.get("params", {}).get("turn", {})
        if result_turn.get("id") != turn or result_turn.get("status") != "interrupted" or result_turn.get("error") is not None or result_turn.get("items") != []:
            raise ValueError("Schema2 interrupt terminal is invalid")
    else:
        error, terminal = receive(), receive()
        ep = error.get("params", {})
        turn_result = terminal.get("params", {}).get("turn", {})
        err = ep.get("error", {})
        if (error.get("method") != "error" or ep.get("threadId") != thread or ep.get("turnId") != turn or ep.get("willRetry") is not False or err.get("message") != SCHEMA2_REASON or err.get("codexErrorInfo") != "other" or terminal.get("method") != "turn/completed" or terminal.get("params", {}).get("threadId") != thread or turn_result.get("id") != turn or turn_result.get("status") != "failed" or turn_result.get("items") != [] or turn_result.get("error", {}).get("message") != SCHEMA2_REASON or turn_result.get("error", {}).get("codexErrorInfo") != "other"):
            raise ValueError("Schema2 controlled failure evidence is invalid")
    if any(e.get("method") in {"item/agentMessage/delta", "item/completed"} for e in events):
        raise ValueError("Schema2 emitted an item frame")
    return protocol_snapshot(events)


def protocol_snapshot(events):
    retained = []
    for event in events:
        frame = {}
        if type(event.get("id")) is int or (isinstance(event.get("id"), str) and len(event["id"]) <= 128):
            frame["id"] = event["id"]
        if isinstance(event.get("method"), str):
            frame["method"] = event["method"]
        for group in ("result", "params"):
            value = event.get(group)
            if not isinstance(value, dict):
                continue
            output = {}
            for key in ("threadId", "turnId", "willRetry"):
                if key in value:
                    output[key] = value[key]
            for nested in ("thread", "turn"):
                obj = value.get(nested)
                if isinstance(obj, dict):
                    selected = {key: obj[key] for key in ("id", "sessionId", "status") if key in obj}
                    if isinstance(obj.get("error"), dict):
                        selected["error"] = {key: obj["error"][key] for key in ("message", "codexErrorInfo") if key in obj["error"]}
                    if selected:
                        output[nested] = selected
            if isinstance(value.get("error"), dict):
                output["error"] = {key: value["error"][key] for key in ("message", "codexErrorInfo") if key in value["error"]}
            if output:
                frame[group] = output
        if frame:
            retained.append(frame)
    return retained


def run(root, binding, attempt, fault, duration, selected_holder=None, pinned_codex=False,
        *, schema2_manifest=None, drive_schema2=None):
    if len(binding) != 64 or any(c not in "0123456789abcdef" for c in binding):
        raise ValueError("Invalid binding")
    if not attempt or len(attempt) > 128 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in attempt):
        raise ValueError("Invalid attempt")
    if fault not in FAULTS or not 500 <= duration <= 5000:
        raise ValueError("Invalid synthetic test case")
    schema2 = schema2_manifest is not None
    if schema2 != (drive_schema2 is not None) or (schema2 and not pinned_codex):
        raise ValueError("Schema2 requires the pinned holder and an explicit synthetic RPC driver")
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
    manifest_digest = None
    if schema2:
        manifest = dict(schema2_manifest, deadline_ms=int(deadline * 1000))
        if (manifest["binding"], manifest["attempt"], manifest["holder_sha256"]) != (binding, attempt, digest(holder)):
            raise ValueError("Schema2 manifest identity does not match its native attempt")
        raw = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        manifest_digest = hashlib.sha256(raw).hexdigest()
        fd = os.open(root / "manifest.json", os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
        with os.fdopen(fd, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)
    host = subprocess.Popen([str(host_path), str(root), fault, binding, attempt], stdin=subprocess.DEVNULL,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env)
    guard = None
    actual_guard_pid = None
    parent_loss_verified = False
    guard_pidfd = None
    controls = {}
    native_exec = False
    protocol = None
    protocol_verified = False
    terminal = None
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
            profile = "C02_SYNTHETIC_SCHEMA2_V1" if schema2 else "C02_SYNTHETIC_NATIVE_V1"
            fields = [profile, binding, attempt, holder_hash, digest(guard_path), str(actual_guard_pid),
                      str(guard_start), str(int(deadline * 1000))]
            if schema2:
                fields.append(manifest_digest)
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
            if schema2 and fault not in {"launcher_loss", "parent_loss"}:
                try:
                    protocol = drive_schema2(guard.stdin, guard.stdout, deadline - .2)
                    if protocol and protocol[-1]["method"] == "turn/completed":
                        terminal = protocol[-1]["params"]["turn"]["status"]
                        protocol_verified = terminal in {"failed", "interrupted"}
                except (OSError, ValueError, KeyError, IndexError, TypeError, TimeoutError, AssertionError):
                    # Retain consumption and quarantine. Never retry the same turn.
                    protocol_verified = False
                finally:
                    guard.stdin.close()
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
        if schema2 and protocol_verified:
            # The relay has exited. Unexpected trailing protocol data invalidates
            # the claim even when native process and channel disposal succeeded.
            if not select.select([guard.stdout], [], [], 0)[0] or os.read(guard.stdout.fileno(), 1):
                protocol_verified = False
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
    disposed = "DISPOSAL_VERIFIED" in states
    if schema2 and (guard is None or guard.returncode != 0 or host.returncode != 0):
        disposed = False
    if disposed and (not schema2 or protocol_verified):
        disposition = "INTERRUPTED" if terminal == "interrupted" else "CONTROLLED_REFUSAL"
    else:
        disposition = "QUARANTINED" if consumed else "REFUSED"
    return {"binding": binding, "attempt": attempt, "disposition": disposition, "native_exec": native_exec,
            "stop_verified": stop, "inference_succeeded": False, "controls": controls, "consumed": consumed,
            "materialization_count": states.count("SYNTHETIC_MATERIALIZED"), "replay_refused": replay_refused,
            "elapsed_ms": int((time.monotonic() - start) * 1000), "evidence_root": str(root),
            "parent_loss_verified": parent_loss_verified, "pinned_codex": pinned_codex, "qualified_host": False,
            "disposal_scope": "synthetic_process_and_channel_only",
            **({"schema2": True, "scope": "SYNTHETIC_NATIVE_NOT_ROUTED_C01_QUALIFICATION",
                "protocol_evidence": protocol, "protocol_verified": protocol_verified,
                "native_disposal_verified": disposed, "manifest_sha256": manifest_digest,
                "guard_exit_code": guard.returncode if guard else None, "host_exit_code": host.returncode}
               if schema2 else {})}


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
    parser.add_argument("--schema2", action="store_true")
    parser.add_argument("--fault", choices=sorted(FAULTS), default="none")
    parser.add_argument("--duration-ms", type=int, default=2500)
    args = parser.parse_args()
    manifest = None
    driver = None
    if args.schema2:
        if not args.pinned_codex or args.holder is None or args.fault not in {"none", "observe_failure"}:
            raise ValueError("Schema2 requires the pinned holder and an approved stop observation fixture")
        manifest, cancel = schema2_manifest(args.root.resolve(), args.binding, args.attempt, args.holder.resolve())
        driver = lambda stdin, stdout, deadline: drive_schema2(
            stdin, stdout, deadline, manifest["context"]["prompt_text"], cancel)
    native = run(args.root, args.binding, args.attempt, args.fault, args.duration_ms, args.holder,
                 args.pinned_codex, schema2_manifest=manifest, drive_schema2=driver)
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
