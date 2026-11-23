"""Finite, nonsecret development driver. Native host alone generates synthetic material.

This does not qualify an operational host permission or a patched Codex holder.
The binding and attempt are supplied by C02 in the integration test; no new attempt
entitlement is allocated here. No credential argument, file or Python RPC exists.
"""
import argparse
import array
import base64
import ctypes
import fcntl
import hashlib
import importlib.util
import json
import os
import re
from pathlib import Path
import select
import signal
import socket
import stat
import subprocess
import sys
import struct
import time
import traceback
import uuid

NATIVE = Path(__file__).resolve().parents[1]
SCHEMA2_PROFILE = "H100_FUNCTIONAL_CODEX_SYNTHETIC_V1"
SCHEMA2_REASON = "SYMPHONY_PROVIDER_BOUNDARY_UNAVAILABLE"
RECOVERY_CUTS = {"native_ack_lost", "invocation_permission_lost", "response_headers_lost",
                 "response_created_lost", "tool_item_lost", "final_stream_lost"}
INTERACTIVE_FAULTS = {"lost_ack", "incomplete", "interrupt", "wrong_call", "wrong_output",
                      "contradictory_final", "missing_tool_pidfd"} | RECOVERY_CUTS
FAULTS = {"none", "missing_permit", "wrong_attempt", "wrong_holder", "wrong_peer", "substituted_holder",
          "bootstrap_failure", "before_materialization", "partial_materialization", "after_materialization",
          "continuous", "launcher_loss", "parent_loss", "ambiguous_provider", "cleanup_failure",
          "observe_failure", "journal_failure", "post_materialization_journal_failure", "ancillary_fd",
          "manifest_unsealed", "manifest_wrong_identity", "manifest_wrong_binding",
          "controls_unavailable"} | INTERACTIVE_FAULTS


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


def hex64(value):
    return (isinstance(value, str) and len(value) == 64
            and all(character in "0123456789abcdef" for character in value))


EFFECT_SCHEMA = "H100-EFFECT-PIPE-1"
EFFECT_MAX_FRAME = 8192
EFFECT_COMMON_KEYS = {"schema", "kind", "context_digest", "thread_id", "turn_id", "nonce",
                      "ordinal", "sequence", "deadline_ms"}


def _read_exact_fd(fd, size, deadline):
    data = bytearray()
    while len(data) < size:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([fd], [], [], remaining)[0]:
            raise TimeoutError("Provider effect frame deadline expired")
        chunk = os.read(fd, size - len(data))
        if not chunk:
            raise EOFError("Provider effect channel closed")
        data.extend(chunk)
    return bytes(data)


def read_effect_frame(fd, deadline):
    size = struct.unpack(">I", _read_exact_fd(fd, 4, deadline))[0]
    if not 0 < size <= EFFECT_MAX_FRAME:
        raise ValueError("Provider effect frame length is outside its bound")
    raw = _read_exact_fd(fd, size, deadline)

    def unique_pairs(pairs):
        value = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("Provider effect frame contains a duplicate key")
            value[key] = item
        return value

    frame = json.loads(raw.decode("utf-8"), object_pairs_hook=unique_pairs)
    if not isinstance(frame, dict) or frame.get("schema") != EFFECT_SCHEMA or not EFFECT_COMMON_KEYS <= set(frame):
        raise ValueError("Provider effect frame has an invalid common header")
    if (not isinstance(frame["context_digest"], str) or not hex64(frame["context_digest"])
            or not isinstance(frame["nonce"], str) or not hex64(frame["nonce"])
            or not isinstance(frame["thread_id"], str) or not frame["thread_id"]
            or not isinstance(frame["turn_id"], str) or not frame["turn_id"]
            or type(frame["ordinal"]) is not int or frame["ordinal"] not in (1, 2)
            or type(frame["sequence"]) is not int or frame["sequence"] < 1
            or type(frame["deadline_ms"]) is not int or frame["deadline_ms"] < 1):
        raise ValueError("Provider effect common header values are invalid")
    return frame


def write_effect_frame(fd, frame, deadline):
    raw = canonical(frame)
    if not 0 < len(raw) <= EFFECT_MAX_FRAME:
        raise ValueError("Provider effect frame exceeds its bound")
    data = memoryview(struct.pack(">I", len(raw)) + raw)
    while data:
        remaining = deadline - time.monotonic()
        if remaining <= 0 or not select.select([], [fd], [], remaining)[1]:
            raise TimeoutError("Provider effect write deadline expired")
        count = os.write(fd, data)
        if count <= 0:
            raise BrokenPipeError("Provider effect channel closed")
        data = data[count:]


def descriptor_digest(frame):
    return hashlib.sha256(canonical({key: value for key, value in frame.items()
                                     if key not in EFFECT_COMMON_KEYS and key != "descriptor_sha256"})).hexdigest()


def read_durable_receipt(root, name, required):
    path = root / name
    fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
    try:
        st = os.fstat(fd)
        if (not stat.S_ISREG(st.st_mode) or st.st_nlink != 1 or st.st_uid != os.getuid()
                or st.st_mode & 0o077 or st.st_size > 4096):
            raise ValueError("Native receipt has unsafe type or permissions")
        raw = bytearray()
        while len(raw) <= 4096:
            chunk = os.read(fd, 4097 - len(raw))
            if not chunk:
                break
            raw.extend(chunk)
        if len(raw) > 4096:
            raise ValueError("Native receipt exceeds its bound")
        value = json.loads(raw.decode("utf-8"))
        if not isinstance(value, dict) or set(value) != set(required):
            raise ValueError("Native receipt field set is invalid")
        return value, hashlib.sha256(raw).hexdigest()
    finally:
        os.close(fd)


def control_line(kind, receipt, receipt_sha256, host_exit_observed=False):
    if kind == "ready":
        payload = {"schema": "H100-NATIVE-CONTROL-1", "kind": kind, "sequence": 0,
                   "binding": receipt["binding"], "attempt": receipt["attempt"],
                   "context_digest": receipt["context_digest"], "receipt_sha256": receipt_sha256,
                   "holder_pid": receipt["holder_pid"], "guard_pid": receipt["guard_pid"]}
    else:
        payload = {"schema": "H100-NATIVE-CONTROL-1", "kind": kind, "sequence": 1,
                   "binding": receipt["binding"], "attempt": receipt["attempt"],
                   "context_digest": receipt["context_digest"], "receipt_sha256": receipt_sha256,
                   "guard_reaped": True,
                   "host_termination_observed": host_exit_observed,
                   "disposal_verified": receipt["disposal_verified"],
                   "journal_sha256": receipt["journal_sha256"]}
    return canonical({"symphonyNativeControl": payload}) + b"\n"


def _journal_effect(root, binding, attempt, request_id, state, descriptor_sha,
                   revision, ordinal, nonce):
    command = [str(NATIVE / "build/request-effect"), str(root), binding, attempt,
               request_id, state, descriptor_sha, str(revision), str(ordinal), nonce]
    result = subprocess.run(command, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                            stderr=subprocess.DEVNULL, timeout=1, check=False,
                            env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"})
    if result.returncode:
        raise ValueError("Native request effect journal refused the transition")


def read_host_broker_stop(root, binding, attempt):
    keys = {"schema", "binding", "attempt", "helper_stopped", "tool_stopped",
            "helper", "tool", "supervisor_pid", "operation_id"}
    deadline = time.monotonic() + 0.250
    while True:
        try:
            receipt, _ = read_durable_receipt(root, "functional-broker-stop.json", keys)
            break
        except FileNotFoundError:
            if time.monotonic() >= deadline:
                raise TimeoutError("Host broker stop receipt was not published")
            time.sleep(.002)
    for name in ("helper", "tool"):
        identity = receipt[name]
        if (not isinstance(identity, dict) or set(identity) != {"pid", "start_ticks"}
                or type(identity["pid"]) is not int or identity["pid"] < 2
                or type(identity["start_ticks"]) is not int or identity["start_ticks"] < 1):
            raise ValueError("Host broker stop receipt has an invalid process identity")
    if (receipt["schema"] != "H100-HOST-BROKER-STOP-1" or receipt["binding"] != binding
            or receipt["attempt"] != attempt or receipt["helper_stopped"] is not True
            or receipt["tool_stopped"] is not True or type(receipt["supervisor_pid"]) is not int
            or receipt["supervisor_pid"] < 2 or not isinstance(receipt["operation_id"], str)
            or not receipt["operation_id"]):
        raise ValueError("Host broker stop receipt does not prove this attempt")
    return receipt


def project_rpc_observation(value, thread_id, turn_id):
    """Select nonsecret v2 event metadata; reject contradictory evidence only."""
    method = value.get("method")
    if method not in ("turn/started", "turn/completed", "error", "item/started", "item/completed"):
        return None
    params = value.get("params")
    if not isinstance(params, dict):
        return None
    turn = params.get("turn")
    item = params.get("item")
    event_turn = turn.get("id") if isinstance(turn, dict) else params.get("turnId")
    if (not thread_id or not turn_id or params.get("threadId") != thread_id or event_turn != turn_id
            or params.get("turnId", turn_id) != turn_id):
        return {"method": method, "identity_rejected": True}
    event = {"method": method, "thread_id": thread_id, "turn_id": turn_id}
    if isinstance(item, dict):
        kind = item.get("type")
        if kind not in ("commandExecution", "functionCallOutput", "mcpToolCall", "dynamicToolCall",
                        "agentMessage", "userMessage", "reasoning", "plan"):
            return None
        event["item_type"] = kind
        for name in ("id", "callId", "tool", "name", "status"):
            field = item.get(name)
            if isinstance(field, str) and re.fullmatch(r"[A-Za-z0-9_.:-]{1,96}", field):
                event[name] = field
        if type(item.get("exitCode")) is int:
            event["exit_code"] = item["exitCode"]
        if item.get("phase") == "final_answer":
            event["phase"] = "final_answer"
    if isinstance(turn, dict) and turn.get("status") in ("inProgress", "completed", "interrupted", "failed"):
        event["status"] = turn["status"]
    error = params.get("error") if method == "error" else turn.get("error") if isinstance(turn, dict) else None
    if isinstance(error, dict):
        info = error.get("codexErrorInfo")
        if isinstance(info, dict) and len(info) == 1:
            info = next(iter(info))
        if isinstance(info, str) and re.fullmatch(r"[A-Za-z]{1,64}", info):
            event["error_type"] = info
        message = error.get("message")
        if isinstance(message, str) and re.fullmatch(r"SYMPHONY_[A-Z0-9_]{3,64}", message):
            event["reason"] = message
    if type(params.get("willRetry")) is bool:
        event["will_retry"] = params["willRetry"]
    return event


def relay_observed_rpc(line, value, events, thread_id, turn_id, request_1_terminal):
    # Forward the exact original frame before doing any observational work.
    os.write(1, line + b"\n")
    if len(events) < 64:
        observation = project_rpc_observation(value, thread_id, turn_id)
        if observation is not None:
            events.append(dict(observation, sequence=len(events) + 1,
                               after_request_1_terminal=request_1_terminal))


def read_strict_r1_stage(diagnostic):
    stage_names = {
        "R1_STREAM_ENTERED", "R1_STREAM_OPENED", "R1_STREAM_EVENT_OBSERVED",
        "R1_STREAM_COMPLETED", "R1_STREAM_VALIDATION_PASSED", "R1_TOOL_CONSTRUCTION_ENTERED",
        "R1_TOOL_CONSTRUCTION_PASSED", "R1_TOOL_DISPATCH_ENTERED", "R1_TOOL_DISPATCH_RETURNED",
    }
    failure_names = {
        "stream_open_error", "stream_event_error", "unexpected_stream_event", "completion_or_item_count",
        "output_item_missing", "tool_construction_error", "tool_call_missing", "tool_dispatch_error",
    }
    event_names = {
        "created", "output_item_added", "output_item_done", "completed",
        "output_text_delta", "tool_call_input_delta", "other",
    }
    for line in diagnostic.splitlines():
        if len(line) > 2048 or b'"H100_R1_STAGE_1"' not in line:
            continue
        try:
            record = json.loads(line)
        except (UnicodeDecodeError, ValueError):
            continue
        if not isinstance(record, dict) or record.get("schema") != "H100_R1_STAGE_1":
            continue
        stages = record.get("stages")
        failure = record.get("failure")
        counts = record.get("event_counts")
        if (not isinstance(stages, list) or not 1 <= len(stages) <= len(stage_names)
                or any(not isinstance(stage, str) or stage not in stage_names for stage in stages)
                or (failure is not None and (not isinstance(failure, str) or failure not in failure_names))
                or not isinstance(counts, dict) or set(counts) != event_names
                or any(type(count) is not int or not 0 <= count <= 2**32 - 1 for count in counts.values())
                or type(record.get("output_item_count")) is not int
                or record["output_item_count"] != counts["output_item_done"]
                or type(record.get("function_call_present")) is not bool
                or type(record.get("completion_seen")) is not bool
                or (record.get("end_turn") is not None and type(record["end_turn"]) is not bool)):
            continue
        return {key: record[key] for key in ("schema", "stages", "failure", "event_counts",
                 "completion_seen", "end_turn", "output_item_count", "function_call_present") if key in record}
    return None


def read_synthetic_effect_counts(diagnostic):
    keys = {"providerRefusals", "auth", "http", "websocket", "responses", "retry",
            "fallback", "discovery", "process"}
    records = []
    for line in diagnostic.splitlines():
        if len(line) > 512 or b'"symphonySyntheticCounts"' not in line:
            continue
        try:
            value = json.loads(line)
        except (ValueError, UnicodeDecodeError):
            return None
        if not isinstance(value, dict) or set(value) != {"symphonySyntheticCounts"}:
            return None
        counts = value["symphonySyntheticCounts"]
        if (not isinstance(counts, dict) or set(counts) != keys
                or any(type(count) is not int or not 0 <= count < 2**32 for count in counts.values())):
            return None
        records.append(counts)
    return records[0] if len(records) == 1 else None


def interactive_controller(guard, host, request_fd, reply_fd, root, manifest, deadline, fault, expected_output,
                           external_broker=False):
    """Relay RPC and typed effect messages over the one routed controller port."""
    context = manifest["context"]
    ready_keys = {"attempt", "binding", "context_digest", "fixture_sha256", "guard_pid",
                  "guard_start_ticks", "holder_pid", "holder_start_ticks", "kind", "nonce",
                  "scope", "sequence"}
    while time.monotonic() < deadline and not (root / "functional-ready.json").exists():
        time.sleep(.002)
    ready, ready_hash = read_durable_receipt(root, "functional-ready.json", ready_keys)
    if (ready["kind"] != "native-ready" or ready["scope"] != "SYNTHETIC_PIPE" or ready["sequence"] != 0
            or ready["binding"] != manifest["binding"] or ready["attempt"] != manifest["attempt"]
            or ready["context_digest"] != context["context_digest"]
            or ready["nonce"] != manifest["provider"]["nonce"]
            or ready["fixture_sha256"] != manifest["provider"]["fixture_sha256"]
            or ready["guard_pid"] != guard.pid or ready["holder_pid"] < 2):
        raise ValueError("Native functional ready receipt does not match the selected holder")
    os.write(1, control_line("ready", ready, ready_hash))
    input_buffer = bytearray()
    rpc_buffer = bytearray()
    pending_frames = []
    thread_start_id = None
    turn_start_id = None
    actual_thread_id = None
    actual_turn_id = None
    turn_response_emitted = False
    holder_sequence = 0
    host_stream_sequence = 0
    request_state = {}
    rpc_observations = []
    request_1_terminal = False
    stopped = False
    broker_processes = {}
    broker_pidfds = []
    provider_path = Path(__file__).resolve().with_name("provider_fixture.py")
    if digest(provider_path) != manifest["provider"]["fixture_sha256"]:
        raise ValueError("Provider fixture bytes changed after manifest binding")
    spec = importlib.util.spec_from_file_location("symphony_synthetic_provider_fixture", provider_path)
    provider_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(provider_module)

    def emit(frame):
        os.write(1, canonical({"symphonyProviderEffect": frame}) + b"\n")

    def send_holder(frame):
        write_effect_frame(reply_fd, frame, deadline)

    def check_common(frame):
        if (frame["context_digest"] != context["context_digest"]
                or frame["nonce"] != manifest["provider"]["nonce"]
                or frame["thread_id"] != actual_thread_id
                or frame["turn_id"] != actual_turn_id):
            raise ValueError("Provider effect frame has a stale or unbound session identity")

    def cut_recovery(checkpoint, ordinal):
        # Mark only a reached fixture checkpoint. A supervised process exit
        # leaves the actual journals and disposal checks to the runtime.
        if fault != checkpoint or ordinal != (2 if checkpoint == "final_stream_lost" else 1):
            return
        with (root / "recovery-checkpoint").open("xb") as stream:
            stream.write(canonical({"checkpoint": checkpoint, "ordinal": ordinal}))
            stream.flush()
            os.fsync(stream.fileno())
        os._exit(97)

    def write_fixture_stream(current, *, accepted=False):
        nonlocal host_stream_sequence
        descriptor = current["descriptor"]
        ordinal = descriptor["ordinal"]
        response_id = f"synthetic-response-{ordinal}"
        call_id = context["broker_selftest"]["binding"]["tool_call_id"] if ordinal == 1 else None
        if ordinal == 1 and fault == "wrong_call":
            call_id = "wrong_fixture_call_id"
        common = {"schema": EFFECT_SCHEMA, "context_digest": context["context_digest"],
                  "thread_id": actual_thread_id, "turn_id": actual_turn_id,
                  "nonce": manifest["provider"]["nonce"], "ordinal": ordinal,
                  "deadline_ms": descriptor["deadline_ms"]}
        if accepted:
            chunks = current.pop("pending_stream_chunks")
        else:
            current["response_id"] = response_id
            chunks = provider_module.transcript(ordinal, response_id, call_id, context["workspace"],
                                                incomplete=fault == "incomplete",
                                                contradictory_final=fault == "contradictory_final" and ordinal == 2)
            transcript_bytes = b"".join(base64.b64decode(item, validate=True) for item in chunks)
            current["terminal_sha256"] = hashlib.sha256(transcript_bytes).hexdigest()
            current["terminal_length"] = len(transcript_bytes)
            first_chunk = base64.b64decode(chunks[0], validate=True)
            created, delimiter, remainder = first_chunk.partition(b"\n\n")
            if not delimiter or not created.startswith(b"event: response.created\n"):
                raise ValueError("Fixture stream must begin with a complete response.created event")
            tail = [base64.b64encode(remainder).decode("ascii")] if remainder else []
            current["pending_stream_chunks"] = tail + chunks[1:]
            host_stream_sequence += 1
            send_holder(dict(common, kind="ACCEPTANCE", sequence=host_stream_sequence,
                             response_id=response_id))
            cut_recovery("response_headers_lost", ordinal)
            chunks = [base64.b64encode(created + delimiter).decode("ascii")]
        if accepted and fault == "tool_item_lost" and ordinal == 1:
            body = b"".join(base64.b64decode(chunk, validate=True) for chunk in chunks)
            first, delimiter, _ = body.partition(b"\n\n")
            if not delimiter or not first.startswith(b"event: response.output_item.done\n"):
                raise ValueError("Recovery fixture lacks the completed tool item")
            chunks = [base64.b64encode(first + delimiter).decode("ascii")]
        for data in chunks:
            host_stream_sequence += 1
            send_holder(dict(common, kind="SSE_CHUNK", sequence=host_stream_sequence, data=data))
        if accepted:
            cut_recovery("tool_item_lost", ordinal)
            cut_recovery("final_stream_lost", ordinal)
            host_stream_sequence += 1
            send_holder(dict(common, kind="TERMINAL", sequence=host_stream_sequence,
                             response_id=response_id, response_completed=True))
        else:
            cut_recovery("response_created_lost", ordinal)

    def process_rpc(line):
        nonlocal thread_start_id, turn_start_id
        value = json.loads(line)
        if not isinstance(value, dict):
            raise ValueError("Controller received a non-object RPC request")
        if value.get("method") == "thread/start" and (type(value.get("id")) is int or isinstance(value.get("id"), str)):
            thread_start_id = value["id"]
        if value.get("method") == "turn/start" and (type(value.get("id")) is int or isinstance(value.get("id"), str)):
            turn_start_id = value["id"]
        guard.stdin.write(line)
        guard.stdin.flush()

    def process_holder_frame(frame):
        nonlocal holder_sequence
        check_common(frame)
        sequence = frame["sequence"]
        if sequence <= holder_sequence:
            raise ValueError("Holder effect sequence did not advance")
        holder_sequence = sequence
        kind = frame["kind"]
        if kind == "VALIDATE_DESCRIPTOR":
            if frame["ordinal"] == 2:
                if fault == "wrong_output":
                    frame = dict(frame, tool_output_sha256=hashlib.sha256(b"wrong fixture output").hexdigest())
                broker = context["broker_selftest"]["binding"]
                if external_broker:
                    stop = read_host_broker_stop(root, manifest["binding"], manifest["attempt"])
                    stopped = stop["helper_stopped"] and stop["tool_stopped"]
                else:
                    states = [json.loads(line)["state"] for line in (root / "broker-events.jsonl").read_text().splitlines()]
                    stopped = ("STOP_VERIFIED" in states and len(broker_pidfds) == 3
                               and bool(select.select([broker_pidfds[2]], [], [], 0)[0]))
                if (not stopped
                        or frame["tool_call_id"] != broker["tool_call_id"]
                        or frame["tool_output_sha256"] != expected_output["sha256"]
                        or frame["tool_output_length"] != expected_output["length"]):
                    raise ValueError("Ordinal 2 lacks the selected stopped broker result")
            if frame.get("request_id") is not None:
                raise ValueError("New provider descriptor must not select its request identity")
            provider_module.validate_descriptor(frame, {
                "context_digest": context["context_digest"], "thread_id": actual_thread_id,
                "turn_id": actual_turn_id, "nonce": manifest["provider"]["nonce"]})
            digest_value = descriptor_digest(frame)
            if frame.get("descriptor_sha256") != digest_value:
                raise ValueError("Provider descriptor digest mismatch")
            request_state[frame["ordinal"]] = {"descriptor": frame, "descriptor_sha256": digest_value,
                                                "expected_response_sequence": sequence}
        elif kind in {"POSSIBLE_SEND_ACK", "OBSERVED_ACCEPTANCE", "TERMINAL_CONFIRMATION"}:
            current = request_state.get(frame["ordinal"])
            if not current:
                raise ValueError("Provider effect arrived before its descriptor")
            frame_digest = current["descriptor_sha256"]
            request_id = frame.get("request_id")
            if not isinstance(request_id, str) or not request_id:
                raise ValueError("Provider effect lacks the ledger request identity")
            current["request_id"] = request_id
            if kind == "POSSIBLE_SEND_ACK":
                if (frame.get("revision") != 1 or frame.get("descriptor_sha256") != frame_digest
                        or current.get("expected_response_sequence") is not None):
                    raise ValueError("POSSIBLE_SEND_ACK does not match its persisted intent")
                _journal_effect(root, manifest["binding"], manifest["attempt"], request_id,
                                kind, frame_digest, frame.get("revision"), frame["ordinal"],
                                manifest["provider"]["nonce"])
                cut_recovery("native_ack_lost", frame["ordinal"])
            elif kind == "OBSERVED_ACCEPTANCE":
                if frame.get("response_id") != current.get("response_id"):
                    raise ValueError("Observed acceptance changed the synthetic response ID")
            else:
                if (frame.get("response_id") != current.get("response_id")
                        or frame.get("terminal_sha256") != current.get("terminal_sha256")
                        or frame.get("terminal_length") != current.get("terminal_length")):
                    raise ValueError("Terminal confirmation does not match its bounded response")
            current["expected_response_sequence"] = sequence
        emit(frame)

    def process_host_frame(frame):
        nonlocal request_1_terminal
        if not isinstance(frame, dict) or set(frame) != {"symphonyProviderEffect"}:
            raise ValueError("Controller received an invalid provider response envelope")
        response = frame["symphonyProviderEffect"]
        check_common(response)
        kind = response["kind"]
        current = request_state.get(response["ordinal"])
        if kind in {"PRE_SEND_INTENT", "INVOCATION_PERMITTED", "DURABLE_OBSERVATION"}:
            if not current:
                raise ValueError("Host response arrived before request validation")
            if response.get("sequence") != current.get("expected_response_sequence"):
                raise ValueError("Host acknowledgment did not echo the holder sequence")
            request_id = response.get("request_id")
            if not isinstance(request_id, str) or not request_id:
                raise ValueError("Host response lacks the authoritative request identity")
            if kind == "PRE_SEND_INTENT":
                if response.get("revision") != 1 or response.get("descriptor_sha256") != current["descriptor_sha256"]:
                    raise ValueError("PRE_SEND_INTENT does not bind the validated descriptor")
                current["request_id"] = request_id
                current["expected_response_sequence"] = None
                _journal_effect(root, manifest["binding"], manifest["attempt"], request_id,
                                kind, current["descriptor_sha256"], 1, response["ordinal"],
                                manifest["provider"]["nonce"])
            elif response.get("request_id") != current.get("request_id"):
                raise ValueError("Host response changed the authoritative request ID")
            elif kind == "INVOCATION_PERMITTED":
                if response.get("revision") != 2 or not hex64(response.get("ack_nonce", "")):
                    raise ValueError("Invocation permission lacks its one-use acknowledgment")
                current["expected_response_sequence"] = None
                _journal_effect(root, manifest["binding"], manifest["attempt"], request_id,
                                kind, current["descriptor_sha256"], 2, response["ordinal"],
                                manifest["provider"]["nonce"])
            else:
                stage = response.get("stage")
                state = "OBSERVED_ACCEPTANCE" if stage == "accepted" else "TERMINAL_CONFIRMATION" if stage == "terminal" else None
                if state is None:
                    raise ValueError("Unknown durable provider observation stage")
                if (response.get("response_id") != current.get("response_id")
                        or (stage == "accepted") != ("pending_stream_chunks" in current)):
                    raise ValueError("Durable observation does not match the fixture stream phase")
                _journal_effect(root, manifest["binding"], manifest["attempt"], request_id,
                                state, current["descriptor_sha256"], 2 if stage == "accepted" else 3,
                                response["ordinal"], manifest["provider"]["nonce"])
                current["expected_response_sequence"] = None
        if kind == "INVOCATION_PERMITTED":
            cut_recovery("invocation_permission_lost", response["ordinal"])
            if fault == "lost_ack":
                return
        send_holder(response)
        if kind == "DURABLE_OBSERVATION" and stage == "terminal" and response["ordinal"] == 1:
            request_1_terminal = True
        if kind == "DURABLE_OBSERVATION" and stage == "accepted":
            write_fixture_stream(current, accepted=True)
        if kind == "INVOCATION_PERMITTED":
            if fault == "interrupt":
                process_rpc(canonical({"id": 4, "method": "turn/interrupt",
                    "params": {"threadId": actual_thread_id, "turnId": actual_turn_id}}) + b"\n")
                return
            write_fixture_stream(current)

    while time.monotonic() < deadline and not stopped:
        readers = [guard.stdout.fileno(), 0]
        if turn_response_emitted and not pending_frames:
            readers.append(request_fd)
        readable, _, _ = select.select(readers, [], [], min(.01, max(0, deadline - time.monotonic())))
        if not external_broker and not broker_pidfds and (root / "broker-events.jsonl").is_file():
            broker_processes, broker_pidfds = observe_broker_processes(root, guard.pid, time.monotonic() + .005)
            if broker_pidfds:
                sync_private_file(root / "broker-release", b"release\n")
                sync_private_file(root / "functional-broker-processes.json", canonical(broker_processes))
        if 0 in readable:
            chunk = os.read(0, 65536)
            if not chunk:
                raise EOFError("Routed controller port closed before explicit stop")
            input_buffer.extend(chunk)
            if len(input_buffer) > 262144:
                raise ValueError("Controller request queue exceeded its bound")
            while b"\n" in input_buffer:
                line, _, rest = input_buffer.partition(b"\n")
                input_buffer[:] = rest
                if not line:
                    continue
                value = json.loads(line.decode("utf-8"))
                control = value.get("symphonyNativeControl") if isinstance(value, dict) else None
                if control is not None:
                    if (set(control) != {"schema", "kind", "binding", "attempt", "sequence"}
                            or control.get("schema") != "H100-NATIVE-CONTROL-1"
                            or control.get("kind") != "stop" or control.get("binding") != manifest["binding"]
                            or control.get("attempt") != manifest["attempt"] or control.get("sequence") != 1):
                        raise ValueError("Invalid native stop envelope")
                    stopped = True
                    guard.stdin.close()
                    break
                if isinstance(value, dict) and "symphonyProviderEffect" in value:
                    process_host_frame(value)
                else:
                    process_rpc(line + b"\n")
        if guard.stdout.fileno() in readable:
            chunk = os.read(guard.stdout.fileno(), 65536)
            if not chunk:
                raise EOFError("Holder RPC stream closed before native stop")
            rpc_buffer.extend(chunk)
            if len(rpc_buffer) > 32768:
                raise ValueError("Holder RPC output exceeded its bound")
            while b"\n" in rpc_buffer:
                line, _, rest = rpc_buffer.partition(b"\n")
                rpc_buffer[:] = rest
                if not line:
                    continue
                value = json.loads(line.decode("utf-8"))
                relay_observed_rpc(line, value, rpc_observations, actual_thread_id,
                                   actual_turn_id, request_1_terminal)
                if value.get("id") == turn_start_id and "result" in value:
                    actual_turn_id = value.get("result", {}).get("turn", {}).get("id")
                    turn_response_emitted = True
                    for pending in pending_frames:
                        process_holder_frame(pending)
                    pending_frames.clear()
                elif value.get("id") == thread_start_id and "result" in value:
                    actual_thread_id = value.get("result", {}).get("thread", {}).get("id")
        if request_fd in readable:
            pending = read_effect_frame(request_fd, deadline)
            if turn_response_emitted:
                process_holder_frame(pending)
            else:
                pending_frames.append(pending)
                if len(pending_frames) > 1:
                    raise ValueError("Holder sent multiple effects before turn admission response")

    if not stopped:
        raise TimeoutError("Native controller stop was not received")
    for fd in (request_fd, reply_fd):
        try:
            os.close(fd)
        except OSError:
            pass
    guard.wait(timeout=max(.1, deadline - time.monotonic()))
    try:
        diagnostic = os.read(guard.stderr.fileno(), 4096) if select.select([guard.stderr], [], [], 0)[0] else b""
        codes = [code for code in ("SYMPHONY_CORE_EVIDENCE_REFUSED", "SYMPHONY_BROKER_REFUSED",
                                  "SYMPHONY_PROVIDER_CONTEXT_INVALID", "SYMPHONY_DISPOSAL_UNCONFIRMED",
                                  "SYMPHONY_DEADLINE", "SYMPHONY_FINAL_ANSWER_REFUSED")
                 if code.encode("ascii") in diagnostic.splitlines()]
        sync_private_file(root / "functional-rpc-observations.json", canonical({
            "attempt": manifest["attempt"], "request_1_terminal": request_1_terminal,
            "events": rpc_observations, "holder_codes": codes,
            "strict_r1_stage": read_strict_r1_stage(diagnostic),
            "synthetic_effect_counts": read_synthetic_effect_counts(diagnostic),
        }))
    except OSError:
        pass  # The diagnostic must not change the routed result.
    if guard.returncode != 0:
        raise RuntimeError("Native guard did not exit cleanly after controller stop")
    host_start = proc_start(host.pid)
    host_pidfd = os.pidfd_open(host.pid)
    try:
        host.wait(timeout=max(.1, deadline - time.monotonic()))
        host_exit_observed = bool(select.select([host_pidfd], [], [], 0)[0])
    finally:
        os.close(host_pidfd)
    if host.returncode != 0 or not host_exit_observed:
        raise RuntimeError("Native host exit was not observed after stop")
    stop_keys = {"attempt", "binding", "context_digest", "disposal_verified", "fixture_sha256",
                 "guard_pid", "guard_start_ticks", "holder_pid", "holder_start_ticks", "host_pid",
                 "host_start_ticks", "journal_sha256", "kind", "nonce", "scope", "sequence",
                 "termination_observed"}
    receipt, receipt_hash = read_durable_receipt(root, "functional-stop.json", stop_keys)
    if (receipt["kind"] != "native-stopped" or receipt["scope"] != "SYNTHETIC_PIPE"
            or receipt["sequence"] != 1 or receipt["binding"] != manifest["binding"]
            or receipt["attempt"] != manifest["attempt"]
            or receipt["context_digest"] != context["context_digest"]
            or receipt["fixture_sha256"] != manifest["provider"]["fixture_sha256"]
            or receipt["guard_pid"] != guard.pid or receipt["holder_pid"] != ready["holder_pid"]
            or receipt["host_pid"] != host.pid or receipt["host_start_ticks"] != host_start
            or receipt["disposal_verified"] is not True or receipt["termination_observed"] is not True):
        raise ValueError("Native stopped receipt does not prove this controller's cleanup")
    journal_raw = (root / "events.jsonl").read_bytes()
    journal_states = [json.loads(line)["state"] for line in journal_raw.splitlines()]
    if (hashlib.sha256(journal_raw).hexdigest() != receipt["journal_sha256"]
            or not {"CREDENTIAL_CHANNEL_CLOSED", "TERMINATION_VERIFIED", "GUARD_REAPED",
                    "DISPOSAL_VERIFIED", "FUNCTIONAL_STOP_RECEIPT_WRITTEN"} <= set(journal_states)):
        raise ValueError("Native stopped receipt lacks matching durable observations")
    if external_broker:
        stop = read_host_broker_stop(root, manifest["binding"], manifest["attempt"])
        if stop["helper_stopped"] is not True or stop["tool_stopped"] is not True:
            raise ValueError("Host broker stop was not independently observed")
    elif broker_pidfds:
        stopped_processes = {name: bool(select.select([fd], [], [], 0)[0])
                             for name, fd in zip(("holder", "helper", "tool"), broker_pidfds)}
        for fd in broker_pidfds:
            os.close(fd)
        if not all(stopped_processes.values()):
            raise ValueError("Native broker stop observations were incomplete")
        sync_private_file(root / "functional-broker-stop.json", canonical(stopped_processes))
    os.write(1, control_line("stopped", receipt, receipt_hash, host_exit_observed))
    return {"ready_receipt_sha256": ready_hash, "stopped_receipt_sha256": receipt_hash,
            "local_disposal_verified": True, "request_count": len(request_state)}


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
    context.pop("context_digest", None)
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


BROKER_SHELL = Path("/usr/bin/dash")
BROKER_HEAD = Path("/usr/bin/head")
BROKER_COMMAND = "/usr/bin/head -n 8 -- planner_input.txt"
BROKER_ARGV = [str(BROKER_SHELL), "-c", BROKER_COMMAND]
GIT_ENV = {"PATH": "/usr/bin:/bin", "GIT_CONFIG_GLOBAL": "/dev/null",
           "GIT_CONFIG_SYSTEM": "/dev/null", "GIT_CONFIG_NOSYSTEM": "1",
           "GIT_TERMINAL_PROMPT": "0", "GIT_NO_LAZY_FETCH": "1",
           "GIT_OPTIONAL_LOCKS": "0"}


def sync_private_file(path, data):
    fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(data)
        stream.flush()
        os.fsync(stream.fileno())
    fd = os.open(path.parent, os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(fd)
    finally:
        os.close(fd)


def record_controller_failure(root, stage, error):
    try:
        frames = [{"file": Path(frame.filename).name, "function": frame.name, "line": frame.lineno}
                  for frame in traceback.extract_tb(error.__traceback__)[-8:]]
        payload = {"schema": "H100-FUNCTIONAL-CONTROLLER-FAILURE-1", "stage": stage,
                   "exception_type": type(error).__name__, "frames": frames}
        sync_private_file(Path(root) / "functional-controller-failure.json", canonical(payload))
    except BaseException:
        pass


def sealed_memfd(path, name, expected_sha256, mode):
    raw = Path(path).read_bytes()
    if hashlib.sha256(raw).hexdigest() != expected_sha256:
        raise ValueError("Host broker input changed after permit binding")
    fd = os.memfd_create(name, os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
    try:
        view = memoryview(raw)
        while view:
            count = os.write(fd, view)
            if count <= 0:
                raise OSError("Could not write sealed broker input")
            view = view[count:]
        if mode is not None and (len(raw) < 4 or raw[:4] != b"\x7fELF" or os.fchmod(fd, mode)):
            raise ValueError("Host broker executable is not a valid ELF image")
        seals = (fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
        fcntl.fcntl(fd, fcntl.F_ADD_SEALS, seals)
        if fcntl.fcntl(fd, fcntl.F_GET_SEALS) & seals != seals:
            raise ValueError("Host broker input seals were not retained")
        return fd
    except BaseException:
        os.close(fd)
        raise


def seal_broker_inputs(root, manifest, pipes, binary, mode, expected_effect=None):
    """Build both ends of the exact bounded diagnostic permit from host inputs."""
    context = dict(manifest["context"])
    workspace = Path(context["workspace"])
    inside_evidence_root = workspace.is_relative_to(root)
    bound_workspace = None
    binding_path = root / "binding.json"
    if binding_path.exists():
        bound = read_private_json(binding_path)
        bound_workspace = bound.get("workspace")
    if (workspace != workspace.resolve(strict=True) or not workspace.is_dir()
            or (not inside_evidence_root and (expected_effect is None or bound_workspace != str(workspace)))):
        raise ValueError("Broker fixture checkout is outside the attempt")
    if manifest.get("fault") != "none" or context.get("role") != "Planner":
        raise ValueError("Wrong broker selftest role or launch")
    def git(*args):
        return subprocess.check_output(["/usr/bin/git", *args], cwd=workspace,
                                       env=GIT_ENV, timeout=1)
    git_dir = workspace / ".git"
    if git_dir.is_symlink() or not git_dir.is_dir():
        raise ValueError("Broker fixture requires a disposable local repository")
    if Path(git("rev-parse", "--show-toplevel").decode().strip()) != workspace:
        raise ValueError("Broker fixture worktree mismatch")
    if git("rev-parse", "HEAD", "HEAD^{tree}").decode().splitlines() != [
            context["source_commit"], context["source_tree"]]:
        raise ValueError("Broker fixture source identity mismatch")
    file = workspace / "planner_input.txt"
    if file.is_symlink() or not file.is_file() or file.stat().st_size > 1_048_576:
        raise ValueError("Broker fixture input type or size refused")
    tracked = git("ls-tree", context["source_commit"], "--", "planner_input.txt")
    if not tracked.startswith(b"100644 blob ") or not tracked.endswith(b"\tplanner_input.txt\n"):
        raise ValueError("Broker fixture input is not the approved tracked file")
    selected = file.read_bytes()
    if selected != git("show", context["source_commit"] + ":planner_input.txt"):
        raise ValueError("Broker fixture input bytes changed")
    if expected_effect is not None:
        lines = selected.split(b"\n", 8)
        expected_output = selected if len(lines) <= 8 else b"\n".join(lines[:8]) + b"\n"
        expected_effect.update(sha256=hashlib.sha256(expected_output).hexdigest(), length=len(expected_output))
    if binary != binary.resolve(strict=True) or binary.is_symlink() or not binary.is_file():
        raise ValueError("Broker executable identity unavailable")
    for executable in (BROKER_SHELL, BROKER_HEAD):
        target = executable.resolve(strict=True)
        if not target.is_file():
            raise ValueError("Broker tool executable identity unavailable")
        for component in (executable, *executable.parents, target, *target.parents):
            info = component.lstat()
            writable = not stat.S_ISLNK(info.st_mode) and info.st_mode & 0o022
            if info.st_uid != 0 or writable:
                raise ValueError("Broker tool executable ancestry refused")
    request_pipe = os.fstat(pipes[1])
    reply_pipe = os.fstat(pipes[2])
    binding = {
        "attempt_id": manifest["attempt"], "binding_digest": manifest["binding"],
        "channel_nonce": uuid.uuid4().hex, "deadline_ms": manifest["deadline_ms"],
        "file_sha256": hashlib.sha256(selected).hexdigest(), "grant_id": context["grant_id"],
        "holder_sha256": manifest["holder_sha256"], "holder_incarnation": uuid.uuid4().hex,
        "operation_id": uuid.uuid4().hex, "permit_id": uuid.uuid4().hex,
        "permit_revision": "1", "source_commit": context["source_commit"],
        "source_tree": context["source_tree"], "tool_call_id": uuid.uuid4().hex,
    }
    argv_sha256 = hashlib.sha256(canonical(BROKER_ARGV)).hexdigest()
    cwd_sha256 = hashlib.sha256(str(workspace).encode()).hexdigest()
    start = dict(binding, operation="START_READ", sequence=1, selector="planner_input_head8",
                 argv_sha256=argv_sha256, cwd_sha256=cwd_sha256, stdin=False, tty=False)
    stop = dict(binding, operation="STOP_REQUEST", sequence=2)
    helper_mode = "wait_for_stop" if mode == "observe_helper_loss" else mode
    lines = ["H100-BROKER-PERMIT-1", str(binding["deadline_ms"]), helper_mode, str(workspace),
             str(root), binding["file_sha256"], str(BROKER_SHELL), digest(BROKER_SHELL),
             digest(BROKER_HEAD)]
    if any("\n" in line or "\r" in line for line in lines):
        raise ValueError("Invalid broker fixture path")
    permit_bytes = b"\n".join([*(line.encode() for line in lines),
                               canonical(binding), canonical(start), canonical(stop), b""])
    permit_hash = hashlib.sha256(permit_bytes).hexdigest()
    binary_hash = digest(binary)
    sync_private_file(root / "broker-permit", permit_bytes)
    context["broker_selftest"] = {
        "binding": binding, "request_device": request_pipe.st_dev,
        "request_inode": request_pipe.st_ino, "reply_device": reply_pipe.st_dev,
        "reply_inode": reply_pipe.st_ino, "broker_sha256": binary_hash,
        "broker_permit_sha256": permit_hash, "mode": mode,
    }
    context.pop("context_digest")
    context["context_digest"] = hashlib.sha256(canonical(context)).hexdigest()
    manifest["context"] = context
    return binary_hash, permit_hash


def observed_identity(pid):
    status = Path(f"/proc/{pid}/status").read_text().splitlines()
    ppid = next(int(line.split()[1]) for line in status if line.startswith("PPid:"))
    return {"pid": pid, "start_ticks": proc_start(pid), "ppid": ppid}


def observe_broker_processes(root, guard_pid, deadline):
    """Open pidfds while the real child is still held behind its read gate."""
    while time.monotonic() < deadline:
        descriptors = []
        try:
            journal = (root / "broker-events.jsonl").read_text().splitlines()
            started = next((json.loads(line) for line in journal if '"STARTED"' in line), None)
            if started:
                events = [json.loads(line) for line in (root / "events.jsonl").read_text().splitlines()]
                holder = next(event["pid"] for event in events if event["state"] == "BOOTSTRAP_CREATED")
                helper = started["helper_pid"]
                tool = started["pid"]
                for pid in (holder, helper, tool):
                    descriptors.append(os.pidfd_open(pid))
                observations = {kind: observed_identity(pid) for kind, pid in
                                zip(("holder", "helper", "tool"), (holder, helper, tool))}
                if (observations["holder"]["ppid"] != guard_pid
                        or observations["helper"]["ppid"] != guard_pid
                        or observations["tool"]["ppid"] != helper
                        or observations["helper"]["start_ticks"] != started["helper_start_ticks"]
                        or observations["tool"]["start_ticks"] != started["start_ticks"]
                        or select.select(descriptors, [], [], 0)[0]):
                    raise RuntimeError("Broker process identity does not match the bound attempt")
                return observations, descriptors
        except (FileNotFoundError, ProcessLookupError, json.JSONDecodeError):
            pass
        except BaseException:
            for fd in descriptors:
                os.close(fd)
            raise
        for fd in descriptors:
            os.close(fd)
        time.sleep(.002)
    return {}, []


def broker_handoff_address(token):
    return "\0h100-broker-" + token


def set_handoff_timeout(channel, deadline):
    remaining = deadline - time.monotonic()
    if remaining <= 0:
        raise TimeoutError("Broker descriptor handoff deadline expired")
    channel.settimeout(remaining)


def handoff_broker_endpoints(listener, endpoint_fds, binding, attempt, parent_pid, deadline):
    """Deliver once to the controller running under the selected namespace parent."""
    with listener:
        try:
            set_handoff_timeout(listener, deadline)
            peer, _ = listener.accept()
            with peer:
                pid, uid, _ = struct.unpack("3i", peer.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12))
                if uid != os.getuid() or pid <= 1 or observed_identity(observed_identity(pid)["ppid"])["ppid"] != parent_pid:
                    raise ValueError("Broker descriptor handoff peer is outside the routed launch chain")
                set_handoff_timeout(peer, deadline)
                if peer.recv(256) != canonical([binding, attempt]):
                    raise ValueError("Broker descriptor handoff identity does not match")
                set_handoff_timeout(peer, deadline)
                if peer.sendmsg([b"broker-pipes-v1"], [(socket.SOL_SOCKET, socket.SCM_RIGHTS,
                                                       array.array("i", endpoint_fds))]) != len(b"broker-pipes-v1"):
                    raise OSError("Broker descriptor handoff was incomplete")
        finally:
            for fd in endpoint_fds:
                os.close(fd)


def receive_broker_endpoints(token, binding, attempt, selection, deadline):
    received = array.array("i")
    with socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET) as channel:
        set_handoff_timeout(channel, deadline)
        channel.connect(broker_handoff_address(token))
        set_handoff_timeout(channel, deadline)
        channel.sendall(canonical([binding, attempt]))
        set_handoff_timeout(channel, deadline)
        data, control, flags, _ = channel.recvmsg(32, socket.CMSG_SPACE(2 * received.itemsize),
                                                   socket.MSG_CMSG_CLOEXEC)
        try:
            for level, kind, value in control:
                if (level, kind) == (socket.SOL_SOCKET, socket.SCM_RIGHTS):
                    received.frombytes(value[:len(value) - len(value) % received.itemsize])
            if (data != b"broker-pipes-v1" or flags & (socket.MSG_TRUNC | socket.MSG_CTRUNC)
                    or len(control) != 1 or len(received) != 2):
                raise ValueError("Broker descriptor handoff did not provide exactly two endpoints")
            for fd, name, access in zip(received, ("request", "reply"), (os.O_WRONLY, os.O_RDONLY)):
                info = os.fstat(fd)
                if (not stat.S_ISFIFO(info.st_mode)
                        or fcntl.fcntl(fd, fcntl.F_GETFL) & os.O_ACCMODE != access
                        or info.st_dev != selection[name + "_device"]
                        or info.st_ino != selection[name + "_inode"]):
                    raise ValueError("Broker descriptor handoff delivered an unexpected pipe")
            return tuple(received)
        except BaseException:
            for fd in received:
                os.close(fd)
            raise


def host_supervisor_loop(root, binding, attempt, broker_image, permit_fd, request_read, reply_write,
                        request_write, reply_read, listener, deadline_ms, supervisor_pid, operation_id,
                        fault):
    """Run outside the PID namespace and record only pidfd-observed broker stops."""
    for fd in (0, 1, 2):
        try:
            os.close(fd)
        except OSError:
            pass
    os.environ.clear()
    parent_pid = os.getppid()
    parent_pidfd = os.pidfd_open(parent_pid)
    if ctypes.CDLL(None).prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent_pid:
        os._exit(90)
    for path in (root / "broker-events.jsonl", root / "broker-release"):
        if path.is_symlink():
            os._exit(91)
    null = os.open("/dev/null", os.O_RDWR)
    broker_pid = os.fork()
    if broker_pid == 0:
        try:
            if (ctypes.CDLL(None).prctl(1, signal.SIGTERM, 0, 0, 0) != 0
                    or os.getppid() != supervisor_pid):
                os._exit(92)
            sources = [fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 16)
                       for fd in (broker_image, permit_fd, request_read, reply_write)]
            os.dup2(null, 0)
            os.dup2(null, 1)
            os.dup2(null, 2)
            for source, target in zip(sources, (3, 4, 5, 6)):
                os.dup2(source, target, inheritable=True)
            keep = {3, 4, 5, 6}
            for candidate in range(7, min(os.sysconf("SC_OPEN_MAX"), 65536)):
                if candidate not in keep:
                    try:
                        os.close(candidate)
                    except OSError:
                        pass
            os.execve("/proc/self/fd/3", ["symphony-tool-broker"], {})
        except BaseException:
            os._exit(92)
    os.close(null)
    os.close(broker_image)
    os.close(permit_fd)
    os.close(request_read)
    os.close(reply_write)
    deadline = deadline_ms / 1000
    helper_pidfd = os.pidfd_open(broker_pid)
    tool_pidfd = None
    helper_start = proc_start(broker_pid)
    tool_identity = None
    try:
        handoff_broker_endpoints(listener, (request_write, reply_read), binding, attempt, parent_pid, deadline)
        while time.monotonic() < deadline and tool_pidfd is None:
            try:
                for line in (root / "broker-events.jsonl").read_text().splitlines():
                    event = json.loads(line)
                    if event.get("state") == "STARTED":
                        tool_pid = event.get("pid")
                        if type(tool_pid) is not int or tool_pid <= 1:
                            raise ValueError("Host broker recorded an invalid tool PID")
                        if fault == "missing_tool_pidfd":
                            sync_private_file(root / "tool-pidfd-fault.json",
                                              canonical({"state": "STARTED", "pid": tool_pid}))
                            raise OSError("Injected failure to open the tool pidfd")
                        candidate = os.pidfd_open(tool_pid)
                        try:
                            observed = observed_identity(tool_pid)
                            if (event.get("helper_pid") != broker_pid
                                    or event.get("helper_ppid") != supervisor_pid
                                    or event.get("helper_start_ticks") != helper_start
                                    or event.get("start_ticks") != observed["start_ticks"]
                                    or observed["ppid"] != broker_pid):
                                raise ValueError("Host broker process tree failed identity checks")
                            tool_identity = observed
                            tool_pidfd = candidate
                        finally:
                            if tool_pidfd is None:
                                os.close(candidate)
                        sync_private_file(root / "broker-release", b"release\n")
                        break
            except FileNotFoundError:
                pass
            time.sleep(.002)
        if tool_pidfd is None:
            raise TimeoutError("Host supervisor did not observe the broker read gate")
        while time.monotonic() < deadline:
            readable, _, _ = select.select([helper_pidfd, parent_pidfd], [], [], .01)
            if parent_pidfd in readable:
                for pidfd in (helper_pidfd, tool_pidfd):
                    try:
                        signal.pidfd_send_signal(pidfd, signal.SIGKILL)
                    except OSError:
                        pass
                raise RuntimeError("Host supervisor parent exited before broker stop")
            if helper_pidfd in readable:
                break
        if not select.select([helper_pidfd], [], [], 0)[0] or not select.select([tool_pidfd], [], [], 0)[0]:
            raise TimeoutError("Host supervisor did not observe both broker processes stop")
        states = [json.loads(line).get("state") for line in
                  (root / "broker-events.jsonl").read_text().splitlines()]
        if "STOP_VERIFIED" not in states:
            raise ValueError("Broker journal lacks its independent stop confirmation")
        helper = {"pid": broker_pid, "start_ticks": helper_start}
        _, status = os.waitpid(broker_pid, 0)
        if not os.WIFEXITED(status) or os.WEXITSTATUS(status) != 0:
            raise ValueError("Host broker exited without a clean stop status")
        stop = {"schema": "H100-HOST-BROKER-STOP-1", "binding": binding, "attempt": attempt,
                "helper_stopped": True, "tool_stopped": True, "helper": helper,
                "tool": {"pid": tool_identity["pid"], "start_ticks": tool_identity["start_ticks"]},
                "supervisor_pid": supervisor_pid, "operation_id": operation_id}
        sync_private_file(root / "functional-broker-stop.json", canonical(stop))
    except BaseException:
        try:
            signal.pidfd_send_signal(helper_pidfd, signal.SIGKILL)
        except OSError:
            pass
        if tool_pidfd is not None:
            try:
                signal.pidfd_send_signal(tool_pidfd, signal.SIGKILL)
            except OSError:
                pass
        os.close(parent_pidfd)
        try:
            os.waitpid(broker_pid, 0)
        except ChildProcessError:
            pass
        os._exit(93)
    finally:
        os.close(helper_pidfd)
        if tool_pidfd is not None:
            os.close(tool_pidfd)
    os._exit(0)


def host_broker_prelaunch(argv):
    if len(argv) < 3 or not Path(argv[0]).is_absolute():
        raise ValueError("Host broker mode requires an absolute unshare executable")
    unshare = argv[0]
    command = list(argv[1:])
    try:
        interactive_at = command.index("--interactive")
        root = Path(command[command.index("--root") + 1])
        binding = command[command.index("--binding") + 1]
        attempt = command[command.index("--attempt") + 1]
        holder = Path(command[command.index("--holder") + 1])
        duration = int(command[command.index("--duration-ms") + 1])
        fault = command[command.index("--fault") + 1]
    except (ValueError, IndexError) as exc:
        raise ValueError("Host broker command lacks its bound interactive driver arguments") from exc
    if not 500 <= duration <= 5000 or fault not in ({"none", "observe_failure"} | INTERACTIVE_FAULTS):
        raise ValueError("Host broker mode requires an approved bounded routed case")
    if "--broker-handoff" in command[interactive_at:]:
        raise ValueError("External broker descriptors are already present")
    manifest, _ = schema2_manifest(root.resolve(), binding, attempt, holder.resolve())
    manifest["deadline_ms"] = int((time.monotonic() + duration / 1000) * 1000)
    broker_pipes = (*os.pipe2(os.O_CLOEXEC), *os.pipe2(os.O_CLOEXEC))
    broker_image = NATIVE / "build/tool-broker"
    expected_effect = {}
    broker_hashes = seal_broker_inputs(root, manifest, broker_pipes, broker_image, "run", expected_effect)
    context = manifest["context"]
    # Pass the exact host-prepared context to the namespace-local controller.
    input_path = root / "schema2-input.json"
    supplied = read_private_json(input_path)
    supplied["context"] = manifest["context"]
    temp = root / ("schema2-input." + uuid.uuid4().hex)
    fd = os.open(temp, os.O_CREAT | os.O_EXCL | os.O_WRONLY | os.O_NOFOLLOW, 0o600)
    with os.fdopen(fd, "wb") as stream:
        stream.write(canonical(supplied))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(temp, input_path)
    directory = os.open(root, os.O_RDONLY | os.O_DIRECTORY)
    os.fsync(directory)
    os.close(directory)
    binding_record = manifest["context"]["broker_selftest"]["binding"]
    sync_private_file(root / "functional-broker-context.json", canonical({
        "schema": "H100-HOST-BROKER-CONTEXT-1", "binding": binding, "attempt": attempt,
        "operation_id": binding_record["operation_id"], "deadline_ms": manifest["deadline_ms"],
        "expected_output": expected_effect, "broker_sha256": broker_hashes[0],
        "permit_sha256": broker_hashes[1]}))
    request_read, request_write, reply_read, reply_write = broker_pipes
    broker_image_fd = sealed_memfd(broker_image, "symphony-tool-broker",
                                   broker_hashes[0], 0o500)
    permit_fd = sealed_memfd(root / "broker-permit", "symphony-tool-broker-permit",
                             broker_hashes[1], None)
    token = uuid.uuid4().hex + uuid.uuid4().hex
    listener = socket.socket(socket.AF_UNIX, socket.SOCK_SEQPACKET)
    listener.bind(broker_handoff_address(token))
    listener.listen(1)
    supervisor_pid = os.fork()
    if supervisor_pid == 0:
        host_supervisor_loop(root, binding, attempt, broker_image_fd, permit_fd,
                             request_read, reply_write, request_write, reply_read, listener,
                             manifest["deadline_ms"], os.getpid(), binding_record["operation_id"], fault)
    supervisor_identity = {"schema": "H100-HOST-SUPERVISOR-1", "pid": supervisor_pid,
                           "ppid": os.getpid(), "start_ticks": proc_start(supervisor_pid),
                           "binding": binding, "attempt": attempt}
    sync_private_file(root / "functional-host-supervisor.json", canonical(supervisor_identity))
    listener.close()
    for fd in (*broker_pipes, broker_image_fd, permit_fd):
        os.close(fd)
    # Neither unshare nor the namespace parent inherits a broker pipe endpoint.
    command[interactive_at + 1:] += ["--broker-handoff", token]
    os.execv(unshare, [unshare, *command])


def run(root, binding, attempt, fault, duration, selected_holder=None, pinned_codex=False,
        *, schema2_manifest=None, drive_schema2=None, broker_selftest=None,
        functional_provider=False, interactive=False, external_broker=None):
    if len(binding) != 64 or any(c not in "0123456789abcdef" for c in binding):
        raise ValueError("Invalid binding")
    if not attempt or len(attempt) > 128 or any(c not in "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_-" for c in attempt):
        raise ValueError("Invalid attempt")
    if fault not in FAULTS or not 500 <= duration <= 5000:
        raise ValueError("Invalid synthetic test case")
    schema2 = schema2_manifest is not None
    if broker_selftest not in (None, "run", "wait_for_stop", "observe_helper_loss"):
        raise ValueError("Invalid broker fixture mode")
    if schema2 != (drive_schema2 is not None or broker_selftest is not None or functional_provider) or (schema2 and not pinned_codex):
        raise ValueError("Schema2 requires the pinned holder and a selected synthetic driver")
    if broker_selftest and (drive_schema2 is not None or (fault != "none" and not functional_provider)):
        raise ValueError("Broker diagnostic must be explicitly selected in the fixture")
    if functional_provider and ((broker_selftest != "run" and external_broker is None) or not interactive):
        raise ValueError("Functional provider requires the selected read-only broker and interactive controller")
    if external_broker is not None and (len(external_broker) != 2 or broker_selftest is not None):
        raise ValueError("External broker requires exactly two inherited pipe descriptors")
    root = root.resolve()
    broker_context = None
    if external_broker is not None:
        broker_context = read_private_json(root / "functional-broker-context.json")
        if (broker_context.get("schema") != "H100-HOST-BROKER-CONTEXT-1"
                or broker_context.get("binding") != binding or broker_context.get("attempt") != attempt):
            raise ValueError("Host broker preparation receipt does not match this attempt")
    start = time.monotonic()
    deadline = (broker_context["deadline_ms"] / 1000 if broker_context is not None
                else start + duration / 1000)
    if deadline <= start or deadline > start + 5:
        raise ValueError("Host broker deadline is expired or exceeds the five second cap")
    if broker_context is not None:
        manifest_deadline_ms = broker_context.get("deadline_ms")
        if type(manifest_deadline_ms) is not int or not 1 <= manifest_deadline_ms <= (1 << 63) - 1:
            raise ValueError("Host broker deadline is invalid")
    else:
        manifest_deadline_ms = int(deadline * 1000)
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
    manifest_digest = None
    broker_pipes = ()
    provider_pipes = ()
    broker_hashes = ()
    if functional_provider and external_broker is not None:
        if (broker_context.get("operation_id") != schema2_manifest["context"].get("broker_selftest", {})
                   .get("binding", {}).get("operation_id")
                or broker_context.get("broker_sha256") != schema2_manifest["context"].get("broker_selftest", {})
                   .get("broker_sha256")
                or broker_context.get("permit_sha256") != schema2_manifest["context"].get("broker_selftest", {})
                   .get("broker_permit_sha256")):
            raise ValueError("Host broker preparation receipt does not match the selected manifest")
        expected_effect = broker_context.get("expected_output")
        if (not isinstance(expected_effect, dict) or set(expected_effect) != {"sha256", "length"}
                or not hex64(expected_effect.get("sha256", ""))
                or type(expected_effect.get("length")) is not int or expected_effect["length"] < 0):
            raise ValueError("Host broker expected output is invalid")
    else:
        expected_effect = {} if functional_provider else None
    broker_result = None
    helper_loss_observed = False
    broker_processes = {}
    broker_pidfds = []
    broker_pidfd_stops = {}
    broker_path = NATIVE / "build/tool-broker"
    if schema2:
        manifest = dict(schema2_manifest, deadline_ms=manifest_deadline_ms)
        if (manifest["binding"], manifest["attempt"], manifest["holder_sha256"]) != (binding, attempt, digest(holder)):
            raise ValueError("Schema2 manifest identity does not match its native attempt")
        if broker_selftest:
            broker_pipes = (*os.pipe2(os.O_CLOEXEC), *os.pipe2(os.O_CLOEXEC))
            try:
                broker_hashes = seal_broker_inputs(root, manifest, broker_pipes, broker_path, broker_selftest, expected_effect)
            except BaseException:
                for fd in broker_pipes:
                    os.close(fd)
                raise
        elif external_broker is not None:
            broker = manifest.get("context", {}).get("broker_selftest")
            if not isinstance(broker, dict) or not isinstance(broker.get("binding"), dict):
                raise ValueError("External broker inputs were not prepared by the host supervisor")
            broker_hashes = (broker["broker_sha256"], broker["broker_permit_sha256"])
        if functional_provider:
            fixture_path = Path(__file__).resolve().with_name("provider_fixture.py")
            if fixture_path.is_symlink() or not fixture_path.is_file():
                raise ValueError("Approved synthetic provider fixture is unavailable")
            manifest["provider"] = {"nonce": uuid.uuid4().hex + uuid.uuid4().hex,
                                    "fixture_sha256": digest(fixture_path)}
            provider_pipes = (*os.pipe2(os.O_CLOEXEC), *os.pipe2(os.O_CLOEXEC))
        raw = canonical(manifest)
        manifest_digest = hashlib.sha256(raw).hexdigest()
        sync_private_file(root / "manifest.json", raw)
    host_args = [str(host_path), str(root), fault, binding, attempt]
    if functional_provider:
        host_args.append(str(Path(__file__).resolve().with_name("provider_fixture.py")))
    host = subprocess.Popen(host_args, stdin=subprocess.DEVNULL,
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
        if broker_selftest:
            guard_args += [str(broker_path), *(str(fd) for fd in broker_pipes)]
        if external_broker is not None:
            guard_args += ["--external-broker", *(str(fd) for fd in external_broker)]
        if functional_provider:
            guard_args += ["--provider", *(str(fd) for fd in provider_pipes)]
        guard = subprocess.Popen(guard_args, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                                 stderr=subprocess.PIPE, env=env,
                                 pass_fds=(*broker_pipes, *provider_pipes, *(external_broker or ())))
        for fd in external_broker or ():
            os.close(fd)
        for fd in broker_pipes:
            os.close(fd)
        broker_pipes = ()
        if functional_provider:
            os.close(provider_pipes[1])
            os.close(provider_pipes[2])
            provider_pipes = (provider_pipes[0], provider_pipes[3])
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
                fields.extend(broker_hashes)
                if functional_provider:
                    fields.extend([manifest["context"]["context_digest"], manifest["provider"]["nonce"],
                                   manifest["provider"]["fixture_sha256"]])
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
            if functional_provider:
                protocol = interactive_controller(guard, host, *provider_pipes, root, manifest, deadline, fault,
                                                   expected_effect, external_broker is not None)
                provider_pipes = ()
                protocol_verified = protocol["local_disposal_verified"]
            elif broker_selftest:
                broker_processes, broker_pidfds = observe_broker_processes(root, actual_guard_pid, deadline - .35)
                if broker_pidfds:
                    if broker_selftest == "run":
                        sync_private_file(root / "broker-release", b"release\n")
                    elif broker_selftest == "wait_for_stop":
                        guard.stdin.write(b"C")
                        guard.stdin.flush()
                    else:
                        signal.pidfd_send_signal(broker_pidfds[1], signal.SIGKILL)
                        helper_loss_observed = bool(select.select(
                            [broker_pidfds[1]], [], [], max(0, deadline - .3 - time.monotonic()))[0])
                guard.stdin.close()
                response = read_line(guard.stdout, deadline)
                if response:
                    broker_result = json.loads(response)
                    protocol_verified = (
                        isinstance(broker_result, dict)
                        and broker_result.get("operation_id") == manifest["context"]["broker_selftest"]["binding"]["operation_id"]
                        and broker_result.get("status") == "stop_verified"
                        and broker_processes.get("tool", {}).get("pid") == broker_result.get("pid")
                        and broker_processes.get("tool", {}).get("start_ticks") == broker_result.get("start_ticks")
                    )
            elif schema2 and fault not in {"launcher_loss", "parent_loss"}:
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
        if interactive and not native_exec and select.select([guard.stderr], [], [], 0)[0]:
            diagnostic = os.read(guard.stderr.fileno(), 4096)
            codes = sorted(set(re.findall(rb"\bSYMPHONY_[A-Z0-9_]{3,64}\b", diagnostic)))
            if codes:
                sync_private_file(root / "functional-startup-refusal.json",
                                  canonical({"codes": [code.decode("ascii") for code in codes]}))
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
        for kind, fd in zip(("holder", "helper", "tool"), broker_pidfds):
            broker_pidfd_stops[kind] = bool(select.select([fd], [], [], 0)[0])
            os.close(fd)
        for fd in broker_pipes:
            os.close(fd)
        for fd in provider_pipes:
            try:
                os.close(fd)
            except OSError:
                pass
        for fd in external_broker or ():
            try:
                os.close(fd)
            except OSError:
                pass
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
    if broker_selftest and not functional_provider and ("BROKER_REAPED" not in states or
                            set(broker_pidfd_stops) != {"holder", "helper", "tool"} or
                            not all(broker_pidfd_stops.values())):
        disposed = False
    if disposed and (not schema2 or protocol_verified):
        disposition = ("BROKER_SELFTEST_STOPPED" if broker_selftest else
                       "INTERRUPTED" if terminal == "interrupted" else "CONTROLLED_REFUSAL")
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
               if schema2 else {}),
            **({"broker_result": broker_result, "helper_loss_observed": helper_loss_observed,
                "broker_processes": broker_processes, "broker_pidfd_stops": broker_pidfd_stops}
               if broker_selftest else {})}


def canonical_runtime_attempt_id(value):
    # A 16-byte unpadded base64url ID has two data bits in its final character.
    return re.fullmatch(r"[A-Za-z0-9_-]{21}[AQgw]", value) is not None


def normalize_controller_arguments(argv):
    normalized = []
    arguments = iter(argv)
    for argument in arguments:
        if argument != "--attempt":
            normalized.append(argument)
            continue

        value = next(arguments, None)
        if value is not None and value.startswith("-") and canonical_runtime_attempt_id(value):
            normalized.append(f"--attempt={value}")
        else:
            normalized.append(argument)
            if value is not None:
                normalized.append(value)
    return normalized


def parse_controller_args(argv):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--root", type=Path, required=True)
    parser.add_argument("--binding", required=True)
    parser.add_argument("--attempt", required=True, action="append")
    parser.add_argument("--holder", type=Path)
    parser.add_argument("--pinned-codex", action="store_true")
    parser.add_argument("--schema2", action="store_true")
    parser.add_argument("--interactive", action="store_true")
    parser.add_argument("--fault", choices=sorted(FAULTS), default="none")
    parser.add_argument("--duration-ms", type=int, default=2500)
    parser.add_argument("--broker-handoff")
    args = parser.parse_args(normalize_controller_arguments(argv))
    if len(args.attempt) != 1:
        parser.error("--attempt may only be supplied once")
    args.attempt = args.attempt[0]
    if not args.attempt or ((args.interactive or args.attempt.startswith("-"))
                            and not canonical_runtime_attempt_id(args.attempt)):
        parser.error("invalid runtime attempt ID")
    return args


def main():
    parent = os.getppid()
    if ctypes.CDLL(None).prctl(1, signal.SIGKILL, 0, 0, 0) != 0 or os.getppid() != parent:
        raise RuntimeError("Native controller parent identity unavailable")
    args = parse_controller_args(sys.argv[1:])
    manifest = None
    driver = None
    if args.interactive and not args.schema2:
        raise ValueError("Interactive mode requires schema2")
    if args.interactive and not hex64(args.broker_handoff):
        raise ValueError("Interactive functional mode requires the host-prepared external broker")
    if args.schema2:
        allowed_faults = {"none", "observe_failure"} | (INTERACTIVE_FAULTS if args.interactive else set())
        if not args.pinned_codex or args.holder is None or args.fault not in allowed_faults:
            raise ValueError("Schema2 requires the pinned holder and an approved stop observation fixture")
        manifest, cancel = schema2_manifest(args.root.resolve(), args.binding, args.attempt, args.holder.resolve())
        if not args.interactive:
            driver = lambda stdin, stdout, deadline: drive_schema2(
                stdin, stdout, deadline, manifest["context"]["prompt_text"], cancel)
    external_broker = None
    try:
        if args.interactive:
            prepared = read_private_json(args.root / "functional-broker-context.json")
            deadline_ms = prepared.get("deadline_ms")
            now = time.monotonic()
            if (prepared.get("binding") != args.binding or prepared.get("attempt") != args.attempt
                    or type(deadline_ms) is not int or not now < deadline_ms / 1000 <= now + 5):
                raise ValueError("Broker handoff deadline or preparation identity is invalid")
            selection = manifest["context"]["broker_selftest"]
            external_broker = receive_broker_endpoints(args.broker_handoff, args.binding, args.attempt,
                                                        selection, deadline_ms / 1000)
            sync_private_file(args.root / "functional-broker-handoff.json", canonical({
                "attempt": args.attempt, "request_inode": selection["request_inode"],
                "reply_inode": selection["reply_inode"], "controller_pid": os.getpid(),
            }))
        native = run(args.root, args.binding, args.attempt, args.fault, args.duration_ms, args.holder,
                     args.pinned_codex, schema2_manifest=manifest, drive_schema2=driver,
                     functional_provider=args.interactive, interactive=args.interactive,
                     external_broker=external_broker)
    except BaseException as exc:
        record_controller_failure(args.root, "native-controller", exc)
        raise
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
    if not args.interactive:
        print(json.dumps(native, sort_keys=True))


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--host-broker":
        host_broker_prelaunch(sys.argv[2:])
    elif len(sys.argv) > 1 and sys.argv[1] == "--parent-proxy":
        child = subprocess.Popen(sys.argv[2:], stdin=sys.stdin, stdout=subprocess.PIPE, stderr=sys.stderr)
        print("GUARD_PID " + str(child.pid), flush=True)
        for data in child.stdout:
            sys.stdout.buffer.write(data)
            sys.stdout.buffer.flush()
        raise SystemExit(child.wait())
    main()
