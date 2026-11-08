"""Independent synthetic verification tests; never load original B0 artifacts."""

import importlib.util
import os
from pathlib import Path
import tempfile
import unittest

import test_b1_control as control_tests
from test_b1_control import test_root


spec = importlib.util.spec_from_file_location("b1_verify", Path(__file__).resolve().parents[1]
                                           / "b1_verify.py")
try:
    verify = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(verify)
except FileNotFoundError:
    verify = None


class VerificationTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(verify, "the independent verifier must be implemented")
        self.directory = tempfile.TemporaryDirectory(prefix="verify-", dir=test_root())
        self.root = Path(self.directory.name)
        self.addCleanup(self.directory.cleanup)

    def test_complete_file_comparison_rejects_trailing_bytes(self):
        left, right = self.root / "left", self.root / "right"
        left.write_bytes(b"synthetic\n")
        right.write_bytes(b"synthetic\nextra")
        fds = [os.open(p, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME) for p in (left, right)]
        for fd in fds:
            self.addCleanup(os.close, fd)
        self.assertFalse(verify.equal_files(*fds))
        self.assertEqual(os.lseek(fds[0], 0, os.SEEK_CUR), 0)

    def test_no_follow_descriptor_open_rejects_symlink(self):
        (self.root / "target").write_bytes(b"synthetic\n")
        (self.root / "alias").symlink_to("target")
        fd = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        with self.assertRaises(OSError):
            verify.open_readonly(fd, "alias")

    def test_producer_completion_cannot_issue_acceptance(self):
        with self.assertRaises(verify.Unqualified):
            verify.production_acceptance({"producer_complete": True})

    def test_reader_authenticates_complete_pending_and_confirmed_history(self):
        rig = control_tests.ControlTests("test_registration_is_durable_and_unique")
        rig.setUp()
        self.addCleanup(rig.doCleanups)
        rig.register()
        fd = os.open(rig.root / "records", os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        report = verify.read_history(fd, rig.keys["S"], rig.keys["C"])
        self.assertTrue(report["complete"])
        self.assertEqual(report["records"], 3)
        self.assertEqual(report["head"], rig.controller.head)

    def test_reader_rejects_tampered_original_record(self):
        rig = control_tests.ControlTests("test_registration_is_durable_and_unique")
        rig.setUp()
        self.addCleanup(rig.doCleanups)
        rig.register()
        path = rig.root / "records" / "000002.json"
        path.chmod(0o600)
        original = path.read_bytes()
        path.write_bytes(original.replace(b"synthetic-r0", b"synthetic-r1"))
        path.chmod(0o400)
        fd = os.open(rig.root / "records", os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        with self.assertRaises(verify.InvalidEvidence):
            verify.read_history(fd, rig.keys["S"], rig.keys["C"])

    def test_pending_ack_loss_is_recoverable_as_unconfirmed_evidence(self):
        rig = control_tests.ControlTests("test_registration_is_durable_and_unique")
        rig.setUp()
        self.addCleanup(rig.doCleanups)
        rig.controller.acknowledge = lambda record: None
        with self.assertRaises(Exception):
            rig.register()
        fd = os.open(rig.root / "records", os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        report = verify.read_history(fd, rig.keys["S"], rig.keys["C"])
        self.assertFalse(report["complete"])
        self.assertEqual(report["pending"], 2)

    def test_independent_candidate_review_observes_positive_and_negative_results(self):
        rig = control_tests.ControlTests("test_registration_is_durable_and_unique")
        rig.setUp()
        self.addCleanup(rig.doCleanups)
        inputs, executable = rig.to_writing()
        rig.controller.copy("synthetic-case", inputs, executable)
        fd = os.open(rig.root / "candidate", os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        expected = {"uid": os.getuid(), "gid": os.getgid(),
                    "inputs": rig.controller.cases["synthetic-case"]["grant"]["inputs"]}
        report = verify.review_candidate(fd, inputs, expected)
        self.assertTrue(report["positive"])
        candidate = rig.root / "candidate"
        candidate.chmod(0o700)
        path = candidate / "qualification_authority.py"
        path.chmod(0o600)
        path.write_bytes(b"known bad synthetic bytes\n")
        path.chmod(0o400)
        candidate.chmod(0o500)
        report = verify.review_candidate(fd, inputs, expected)
        self.assertTrue(report["complete"])
        self.assertFalse(report["mechanism_failed"])
        self.assertFalse(report["positive"])
        candidate.chmod(0o700)

    def test_known_missing_payload_is_complete_negative_artifact_review(self):
        rig = control_tests.ControlTests("test_registration_is_durable_and_unique")
        rig.setUp()
        self.addCleanup(rig.doCleanups)
        inputs, executable = rig.to_writing()
        rig.controller.copy("synthetic-case", inputs, executable)
        candidate = rig.root / "candidate"
        candidate.chmod(0o700)
        (candidate / "qualification_authority.py").unlink()
        candidate.chmod(0o500)
        fd = os.open(candidate, os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, fd)
        expected = {"uid": os.getuid(), "gid": os.getgid(),
                    "inputs": rig.controller.cases["synthetic-case"]["grant"]["inputs"]}
        report = verify.review_candidate(fd, inputs, expected)
        self.assertTrue(report["complete"])
        self.assertFalse(report["positive"])
        self.assertFalse(report["mechanism_failed"])
        self.assertIn("source payload is absent", report["findings"])
        candidate.chmod(0o700)


if __name__ == "__main__":
    unittest.main()
