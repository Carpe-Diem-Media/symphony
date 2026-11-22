#!/usr/bin/env python3
"""Offline validation for the synthetic provider descriptor and SSE fixture."""

import base64
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

FIXTURE_PATH = Path(__file__).with_name("provider_fixture.py")
SPEC = importlib.util.spec_from_file_location("provider_fixture", FIXTURE_PATH)
fixture = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(fixture)


class ProviderEffectsTest(unittest.TestCase):
    def descriptor(self, ordinal=1):
        frame = {
            "schema": fixture.SCHEMA,
            "kind": "VALIDATE_DESCRIPTOR",
            "context_digest": "a" * 64,
            "thread_id": "thread-1",
            "turn_id": "turn-1",
            "nonce": "b" * 64,
            "ordinal": ordinal,
            "sequence": ordinal,
            "deadline_ms": 10_000,
            "request_id": None,
            "method": "POST",
            "url": fixture.URL,
            "model": fixture.MODEL,
            "body_sha256": "c" * 64,
            "body_length": 512,
            "content_type": "application/json",
            "stream": True,
            "store": False,
            "parallel_tool_calls": False,
            "tool_schema_sha256": "d" * 64,
            "prior_response_id": None if ordinal == 1 else "resp-1",
            "tool_call_id": None if ordinal == 1 else "call-1",
            "tool_output_sha256": None if ordinal == 1 else "e" * 64,
            "tool_output_length": None if ordinal == 1 else 42,
            "descriptor_sha256": None,
        }
        body = {key: value for key, value in frame.items()
                if key not in fixture.COMMON_KEYS
                and key != "descriptor_sha256"}
        frame["descriptor_sha256"] = fixture.sha256(fixture.canonical(body))
        return frame

    def test_descriptor_returns_only_allowlisted_nonsecret_fields(self):
        expected = {"context_digest": "a" * 64, "thread_id": "thread-1", "turn_id": "turn-1", "nonce": "b" * 64}
        retained = fixture.validate_descriptor(self.descriptor(), expected)
        self.assertEqual(retained["ordinal"], 1)
        self.assertNotIn("body", retained)
        self.assertNotIn("authorization", retained)

    def test_descriptor_rejects_endpoint_and_unknown_fields(self):
        expected = {"context_digest": "a" * 64, "thread_id": "thread-1", "turn_id": "turn-1", "nonce": "b" * 64}
        frame = self.descriptor()
        frame["url"] = "https://example.invalid/responses"
        with self.assertRaises(ValueError):
            fixture.validate_descriptor(frame, expected)
        frame = self.descriptor()
        frame["prompt"] = "must never cross the effect pipe"
        with self.assertRaises(ValueError):
            fixture.validate_descriptor(frame, expected)

    def test_second_descriptor_requires_tool_output_correlation(self):
        expected = {"context_digest": "a" * 64, "thread_id": "thread-1", "turn_id": "turn-1", "nonce": "b" * 64}
        frame = self.descriptor(2)
        self.assertEqual(fixture.validate_descriptor(frame, expected)["ordinal"], 2)
        frame["tool_output_sha256"] = None
        with self.assertRaises(ValueError):
            fixture.validate_descriptor(frame, expected)

    def test_transcripts_are_bounded_sse_and_have_real_terminal_shape(self):
        for ordinal, call_id in ((1, "call-1"), (2, None)):
            chunks = fixture.transcript(ordinal, f"resp-{ordinal}", call_id, "/disposable/workspace")
            self.assertTrue(chunks)
            raw = b"".join(base64.b64decode(chunk, validate=True) for chunk in chunks)
            self.assertLessEqual(len(raw), fixture.MAX_TRANSCRIPT)
            self.assertTrue(all(len(base64.b64decode(chunk)) <= fixture.MAX_FRAME for chunk in chunks))
            events = [json.loads(line[6:]) for line in raw.splitlines() if line.startswith(b"data: {")]
            self.assertEqual(events[0]["type"], "response.created")
            self.assertEqual(events[-1]["type"], "response.completed")
            self.assertEqual(events[-1]["response"]["id"], f"resp-{ordinal}")
            self.assertEqual(events[-1]["response"]["end_turn"], ordinal == 2)
            self.assertEqual(events[1]["item"], events[-1]["response"]["output"][0])
            self.assertEqual([line[7:].decode() for line in raw.splitlines() if line.startswith(b"event: ")],
                             [event["type"] for event in events])
            if ordinal == 2:
                self.assertEqual(events[1]["item"]["phase"], "final_answer")
        self.assertEqual(hashlib.sha256(b"fixture").hexdigest(), fixture.sha256(b"fixture"))

    def test_native_journal_requires_ordered_synced_single_use_transitions(self):
        binary = Path(__file__).resolve().parents[1] / "build/request-effect"
        self.assertTrue(binary.is_file(), "Build the native request-effect prerequisite")
        binding, attempt = "a" * 64, "provider-journal-test"
        holder, guard, manifest = "b" * 64, "c" * 64, "d" * 64
        descriptor, nonce = "e" * 64, "f" * 64
        with tempfile.TemporaryDirectory(prefix="native-effect-journal-") as scratch:
            root = Path(scratch)
            root.chmod(0o700)
            deadline = str(__import__("time").monotonic_ns() // 1_000_000 + 10_000)
            permission = ["C02_SYNTHETIC_SCHEMA2_V1", binding, attempt, holder, guard,
                          str(os.getpid()), "1", deadline, manifest]
            (root / "permission").write_text("\n".join(permission) + "\n")
            (root / "permission").chmod(0o600)

            def record(state):
                return subprocess.run([str(binary), str(root), binding, attempt, "request-1", state,
                                       descriptor, "1", "1", nonce], capture_output=True, check=False)

            for state, revision in (("PRE_SEND_INTENT", 1), ("POSSIBLE_SEND_ACK", 1),
                                    ("INVOCATION_PERMITTED", 2), ("OBSERVED_ACCEPTANCE", 2),
                                    ("TERMINAL_CONFIRMATION", 3)):
                result = subprocess.run([str(binary), str(root), binding, attempt, "request-1", state,
                                         descriptor, str(revision), "1", nonce], capture_output=True)
                self.assertEqual(result.returncode, 0, state)
            self.assertNotEqual(record("TERMINAL_CONFIRMATION").returncode, 0)
            journal = (root / "request-effect-request-1.jsonl").read_text().splitlines()
            self.assertEqual(len(journal), 5)
            self.assertTrue(all("body" not in line and "prompt" not in line and "token" not in line
                                for line in journal))


if __name__ == "__main__":
    unittest.main()
