"""Local stdio peer for AppServer provider-effect mailbox tests."""

import json
from pathlib import Path
import signal
import sys
import time


def send(message):
    print(json.dumps(message), flush=True)


def receive():
    return json.loads(input())


def notify(method, **params):
    send({"method": method, "params": {"threadId": thread, **params}})


spec = json.loads(Path(sys.argv[1]).read_text())
if spec["fault"] in {"stop", "invalid-stop"}:
    assert receive()["symphonyNativeControl"]["kind"] == "stop"
    send({"method": "turn/completed"})
    if spec["fault"] == "stop":
        send({"symphonyNativeControl": spec["stop"]})
    else:
        send({"method": "thread/started"})
    sys.stdin.buffer.readline()
    sys.exit(0)

common = spec["common"]
thread = common["thread_id"]
turn = common["turn_id"]
fault = spec["fault"]
sequence = 0


def exchange(ordinal, kind, fields):
    global sequence
    sequence += 1
    send({"symphonyProviderEffect": {
        **common, **fields, "kind": kind, "ordinal": ordinal, "sequence": sequence,
    }})
    response = receive()["symphonyProviderEffect"]
    assert response["ordinal"] == ordinal and response["sequence"] == sequence
    return response


start = receive()
assert start["method"] == "turn/start"
assert start["params"]["threadId"] == thread
if fault == "turn-start-error":
    send({"id": start["id"], "error": {"code": -32603, "message": "fixture refused turn"}})
    sys.exit(0)
if fault == "missing-turn-id":
    send({"id": start["id"], "result": {"turn": {}}})
    sys.exit(0)
send({"id": start["id"], "result": {"turn": {"id": turn}}})
notify("turn/started", turn={"id": turn})
notify("item/started", turnId=turn, item={"type": "agentMessage", "id": "message-1"})

if fault == "premature-final":
    notify("item/completed", turnId=turn,
           item={"type": "agentMessage", "phase": "final_answer", "id": "message-1", "text": "fixture"})
elif fault == "interrupted":
    notify("turn/completed", turn={"id": turn, "status": "interrupted"})
elif fault == "protocol-error":
    notify("error", turnId=turn)
elif fault == "invalid-frame":
    print("[]", flush=True)
elif fault == "wrong-turn":
    notify("turn/completed", turn={"id": "unrelated-turn", "status": "completed"})
elif fault == "oversized-frame":
    print(json.dumps({"message": "x" * 65536}), flush=True)
elif fault == "continuous":
    signal.signal(signal.SIGPIPE, signal.SIG_DFL)
    intent = exchange(1, "VALIDATE_DESCRIPTOR", spec["descriptors"][0])
    assert intent["kind"] == "PRE_SEND_INTENT"
    permission = exchange(1, "POSSIBLE_SEND_ACK", {
        key: intent[key] for key in ("request_id", "revision", "descriptor_sha256")
    })
    assert permission["kind"] == "INVOCATION_PERMITTED"
    while True:
        notify("turn/started", turn={"id": turn})
        time.sleep(0.02)
elif fault == "complete":
    for ordinal, descriptor in enumerate(spec["descriptors"], start=1):
        intent = exchange(ordinal, "VALIDATE_DESCRIPTOR", descriptor)
        assert intent["kind"] == "PRE_SEND_INTENT"
        permission = exchange(ordinal, "POSSIBLE_SEND_ACK", {
            key: intent[key] for key in ("request_id", "revision", "descriptor_sha256")
        })
        assert permission["kind"] == "INVOCATION_PERMITTED" and permission["revision"] == 2
        response = {"request_id": intent["request_id"], "response_id": f"response-{ordinal}"}
        assert exchange(ordinal, "OBSERVED_ACCEPTANCE", response)["stage"] == "accepted"
        terminal = {
            **response, "terminal_sha256": spec["terminal_sha256"], "terminal_length": 8,
        }
        assert exchange(ordinal, "TERMINAL_CONFIRMATION", terminal)["stage"] == "terminal"

    notify("item/completed", turnId=turn,
           item={"type": "agentMessage", "phase": "final_answer", "id": "message-1", "text": "fixture"})
    notify("turn/completed", turn={"id": turn, "status": "completed"})
else:
    raise AssertionError(fault)
