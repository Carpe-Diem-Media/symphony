"""Bounded, non-networked Responses fixture for the functional holder tests."""

import base64
import hashlib
import json
import re

SCHEMA = "H100-EFFECT-PIPE-1"
MAX_FRAME = 8192
MAX_TRANSCRIPT = 262144
MAX_BASE64_CHUNK = 6 * 1024
MODEL = "synthetic-planner-v1"
URL = "https://api.openai.com/v1/responses"
REQUEST_ID = re.compile(r"^[A-Za-z0-9_-]{1,128}$")
COMMON_KEYS = {"schema", "kind", "context_digest", "thread_id", "turn_id", "nonce",
               "ordinal", "sequence", "deadline_ms"}


def canonical(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")


def sha256(data):
    return hashlib.sha256(data).hexdigest()


def validate_descriptor(frame, expected):
    """Check the nonsecret request descriptor without receiving its body."""
    common = COMMON_KEYS
    request = {
        "request_id", "method", "url", "model", "body_sha256", "body_length",
        "content_type", "stream", "store", "parallel_tool_calls",
        "tool_schema_sha256", "prior_response_id", "tool_call_id",
        "tool_output_sha256", "tool_output_length", "descriptor_sha256",
    }
    if not isinstance(frame, dict) or set(frame) != common | request:
        raise ValueError("provider descriptor has an invalid field set")
    if (frame["schema"] != SCHEMA or frame["kind"] != "VALIDATE_DESCRIPTOR"
            or frame["context_digest"] != expected["context_digest"]
            or frame["thread_id"] != expected["thread_id"]
            or frame["turn_id"] != expected["turn_id"]
            or frame["nonce"] != expected["nonce"]
            or type(frame["ordinal"]) is not int or frame["ordinal"] not in (1, 2)
            or type(frame["sequence"]) is not int or frame["sequence"] < 1
            or type(frame["deadline_ms"]) is not int or frame["deadline_ms"] <= 0):
        raise ValueError("provider descriptor identity or bounds mismatch")
    if (frame["request_id"] is not None
            or frame["method"] != "POST" or frame["url"] != URL or frame["model"] != MODEL
            or not isinstance(frame["body_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", frame["body_sha256"])
            or type(frame["body_length"]) is not int or not 1 <= frame["body_length"] <= 1_048_576
            or frame["content_type"] != "application/json"
            or frame["stream"] is not True or frame["store"] is not False
            or frame["parallel_tool_calls"] is not False
            or not isinstance(frame["tool_schema_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", frame["tool_schema_sha256"])
            or not isinstance(frame["descriptor_sha256"], str)
            or not re.fullmatch(r"[0-9a-f]{64}", frame["descriptor_sha256"])):
        raise ValueError("provider descriptor is outside the synthetic request contract")
    descriptor_body = {key: value for key, value in frame.items()
                       if key not in common and key != "descriptor_sha256"}
    if sha256(canonical(descriptor_body)) != frame["descriptor_sha256"]:
        raise ValueError("provider descriptor digest mismatch")
    if frame["ordinal"] == 1:
        if any(frame[key] is not None for key in ("prior_response_id", "tool_call_id", "tool_output_sha256", "tool_output_length")):
            raise ValueError("first request cannot carry prior-response data")
    elif (not isinstance(frame["prior_response_id"], str)
          or not REQUEST_ID.fullmatch(frame["prior_response_id"])
          or not isinstance(frame["tool_call_id"], str)
          or not REQUEST_ID.fullmatch(frame["tool_call_id"])
          or not isinstance(frame["tool_output_sha256"], str)
          or not re.fullmatch(r"[0-9a-f]{64}", frame["tool_output_sha256"])
          or type(frame["tool_output_length"]) is not int
          or not 1 <= frame["tool_output_length"] <= 8192):
        raise ValueError("second request lacks bounded tool-output correlation")
    return {key: frame[key] for key in ("ordinal", "body_sha256", "body_length",
                                          "tool_schema_sha256", "prior_response_id", "tool_call_id",
                                          "tool_output_sha256", "tool_output_length")}


def transcript(ordinal, response_id, tool_call_id=None, workspace=None, *, incomplete=False, contradictory_final=False):
    """Encode only the three Responses events approved for each request."""
    if type(ordinal) is not int or ordinal not in (1, 2) or not REQUEST_ID.fullmatch(response_id):
        raise ValueError("invalid synthetic response identity")
    if ordinal == 1:
        if not isinstance(tool_call_id, str) or not REQUEST_ID.fullmatch(tool_call_id):
            raise ValueError("first response requires the correlated tool-call ID")
        if not isinstance(workspace, str) or not workspace.startswith("/"):
            raise ValueError("first response requires the bound workspace")
        arguments = canonical({"cmd": "/usr/bin/head -n 8 -- planner_input.txt", "workdir": workspace,
                               "login": False, "tty": False}).decode("utf-8")
        item = {"id": "fc-synthetic-1", "type": "function_call", "call_id": tool_call_id,
                "name": "exec_command", "arguments": arguments}
    else:
        item = {"id": "msg-synthetic-2", "type": "message", "role": "assistant", "phase": "final_answer",
                "status": "completed", "content": [{"type": "output_text",
                "text": "Plan: inspect the tracked input, verify its limits, and report the findings.",
                "annotations": []}]}
    terminal_item = item
    if contradictory_final:
        if ordinal != 2:
            raise ValueError("contradictory final answer requires the second response")
        terminal_item = dict(item, content=[
            dict(item["content"][0], text="Contradictory terminal fixture answer.")
        ])
    terminal = "response.incomplete" if incomplete else "response.completed"
    events = [
        {"type": "response.created", "response": {"id": response_id, "status": "in_progress", "model": MODEL}},
        {"type": "response.output_item.done", "response_id": response_id, "output_index": 0, "item": item},
        {"type": terminal, "response": {"id": response_id, "status": "incomplete" if incomplete else "completed",
                                        "model": MODEL, "end_turn": ordinal == 2, "output": [terminal_item]}},
    ]
    raw = b"".join(b"event: " + event["type"].encode("ascii") + b"\ndata: " + canonical(event) + b"\n\n"
                   for event in events)
    if len(raw) > MAX_TRANSCRIPT:
        raise ValueError("synthetic transcript exceeded its bound")
    raw_chunk = (MAX_BASE64_CHUNK // 4) * 3
    return [base64.b64encode(raw[offset:offset + raw_chunk]).decode("ascii")
            for offset in range(0, len(raw), raw_chunk)]
