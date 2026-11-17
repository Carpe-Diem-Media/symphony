"""Executable tests of the native slice. No Codex, credentials or network provider."""
import json
import os
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
BINDING = "a" * 64
ATTEMPT = "existing-runtime-attempt-01"


class NativeLifecycleTest(unittest.TestCase):
    def run_native(self, fault="none", duration=2500, long_path=False):
        runner = ROOT / "tests" / "run_attempt.py"
        self.assertTrue(runner.is_file(), "Executable native C02 slice is missing")
        with tempfile.TemporaryDirectory(prefix="c02-native-test-" + ("x" * 150 if long_path else "")) as scratch:
            result = subprocess.run(
                ["/usr/bin/python3", "-I", str(runner), "--root", scratch,
                 "--binding", BINDING, "--attempt", ATTEMPT,
                 "--fault", fault, "--duration-ms", str(duration)],
                capture_output=True, text=True, timeout=12,
                env={"PATH": "/usr/bin:/bin", "LANG": "C.UTF-8"},
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            evidence = json.loads(result.stdout)
            journal = (Path(scratch) / "events.jsonl").read_text()
            self.assertNotIn("SYNTHETIC-NONLIVE-", journal + result.stdout + result.stderr)
            self.assertNotIn("ACCESS_TOKEN=", journal + result.stdout + result.stderr)
            evidence["events"] = [json.loads(line) for line in journal.splitlines()]
            self.assertEqual(evidence["binding"], BINDING)
            self.assertEqual(evidence["attempt"], ATTEMPT)
            return evidence

    def test_native_materialization_exec_refusal_and_independent_stop(self):
        evidence = self.run_native()
        self.assertEqual(evidence["disposition"], "CONTROLLED_REFUSAL")
        self.assertTrue(evidence["native_exec"])
        self.assertTrue(evidence["stop_verified"])
        self.assertFalse(evidence["inference_succeeded"])
        states = [item["state"] for item in evidence["events"]]
        for state in ["HOST_PERMISSION_VALIDATED", "BOOTSTRAP_CREATED", "MATERIALIZATION_INTENT",
                      "SYNTHETIC_MATERIALIZED", "CREDENTIAL_CHANNEL_CLOSED", "HOLDER_READY",
                      "INFERENCE_INTENT", "INFERENCE_REFUSED", "TERMINATION_REQUESTED",
                      "GUARD_REAPED", "TERMINATION_VERIFIED", "DISPOSAL_VERIFIED"]:
            self.assertIn(state, states)
        self.assertLess(states.index("MATERIALIZATION_INTENT"), states.index("SYNTHETIC_MATERIALIZED"))
        self.assertLess(states.index("SYNTHETIC_MATERIALIZED"), states.index("CREDENTIAL_CHANNEL_CLOSED"))
        self.assertLess(states.index("CREDENTIAL_CHANNEL_CLOSED"), states.index("HOLDER_READY"))
        self.assertLess(states.index("INFERENCE_INTENT"), states.index("INFERENCE_REFUSED"))
        self.assertLess(states.index("TERMINATION_VERIFIED"), states.index("DISPOSAL_VERIFIED"))

    def test_deep_evidence_root_works_without_socket_path_truncation(self):
        evidence = self.run_native(long_path=True)
        self.assertEqual(evidence["disposition"], "CONTROLLED_REFUSAL")
        self.assertTrue(evidence["stop_verified"])

    def test_holder_kernel_controls_and_environment(self):
        evidence = self.run_native()
        controls = evidence["controls"]
        for name in ["nondumpable", "no_new_privs", "core_zero", "fork_denied", "exec_denied",
                     "ptrace_denied", "inet_socket_denied", "credential_fds_absent", "fresh_home"]:
            self.assertTrue(controls[name], name)
        self.assertEqual(evidence["materialization_count"], 1)
        self.assertTrue(evidence["replay_refused"])

    def test_missing_host_permission_never_materializes(self):
        evidence = self.run_native("missing_permit")
        self.assertEqual(evidence["disposition"], "REFUSED")
        self.assertEqual(evidence["materialization_count"], 0)
        self.assertFalse(evidence["native_exec"])

    def test_wrong_attempt_and_holder_refuse(self):
        for fault in ["wrong_attempt", "wrong_holder", "wrong_peer", "substituted_holder"]:
            with self.subTest(fault=fault):
                evidence = self.run_native(fault)
                self.assertNotEqual(evidence["disposition"], "CONTROLLED_REFUSAL")
                self.assertEqual(evidence["materialization_count"], 0)
                self.assertFalse(evidence["native_exec"])

    def test_failed_bootstrap_and_crash_before_materialization(self):
        for fault in ["bootstrap_failure", "before_materialization"]:
            with self.subTest(fault=fault):
                evidence = self.run_native(fault)
                self.assertEqual(evidence["materialization_count"], 0)
                self.assertFalse(evidence["native_exec"])
                self.assertNotEqual(evidence["disposition"], "CONTROLLED_REFUSAL")

    def test_partial_delivery_and_crash_after_materialization_quarantine(self):
        for fault in ["partial_materialization", "after_materialization"]:
            with self.subTest(fault=fault):
                evidence = self.run_native(fault)
                self.assertEqual(evidence["disposition"], "QUARANTINED")
                self.assertTrue(evidence["consumed"])
                self.assertTrue(evidence["replay_refused"])

    def test_deadline_is_absolute_despite_continuous_output(self):
        evidence = self.run_native("continuous", 700)
        self.assertEqual(evidence["disposition"], "QUARANTINED")
        self.assertTrue(evidence["stop_verified"])
        self.assertGreaterEqual(evidence["elapsed_ms"], 500)
        self.assertLess(evidence["elapsed_ms"], 1800)
        self.assertTrue(evidence["replay_refused"])

    def test_launcher_and_parent_loss_do_not_restore_permission(self):
        for fault in ["launcher_loss", "parent_loss"]:
            with self.subTest(fault=fault):
                evidence = self.run_native(fault, 1200)
                self.assertTrue(evidence["consumed"])
                self.assertTrue(evidence["stop_verified"])
                self.assertTrue(evidence["replay_refused"])
                self.assertEqual(evidence["disposition"], "QUARANTINED")
                ready = next(item["at_ms"] for item in evidence["events"] if item["state"] == "HOLDER_READY")
                stopped = next(item["at_ms"] for item in evidence["events"] if item["state"] == "TERMINATION_VERIFIED")
                self.assertLess(stopped - ready, 500)
                if fault == "parent_loss":
                    self.assertTrue(evidence["parent_loss_verified"])

    def test_ancillary_descriptor_transfer_is_refused(self):
        evidence = self.run_native("ancillary_fd")
        self.assertEqual(evidence["materialization_count"], 0)
        self.assertFalse(evidence["native_exec"])
        self.assertIn("HOST_PERMISSION_REFUSED", [item["state"] for item in evidence["events"]])

    def test_ambiguous_synthetic_provider_effect_never_replays(self):
        evidence = self.run_native("ambiguous_provider")
        self.assertEqual(evidence["disposition"], "QUARANTINED")
        states = [item["state"] for item in evidence["events"]]
        self.assertEqual(states.count("INFERENCE_INTENT"), 1)
        self.assertNotIn("INFERENCE_REFUSED", states)
        self.assertTrue(evidence["replay_refused"])
        self.assertFalse(evidence["inference_succeeded"])

    def test_missing_cleanup_observation_retains_quarantine(self):
        for fault in ["cleanup_failure", "observe_failure", "journal_failure", "post_materialization_journal_failure"]:
            with self.subTest(fault=fault):
                evidence = self.run_native(fault)
                self.assertEqual(evidence["disposition"], "QUARANTINED")
                self.assertNotIn("DISPOSAL_VERIFIED", [item["state"] for item in evidence["events"]])
                self.assertTrue(evidence["replay_refused"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
