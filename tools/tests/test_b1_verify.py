"""Independent synthetic verification tests; never load original B0 artifacts."""

import importlib.util
import hashlib
import os
from pathlib import Path
import tempfile
import unittest
from unittest import mock

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
                    "candidate": rig.controller.cases["synthetic-case"]["candidate"],
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
                    "candidate": rig.controller.cases["synthetic-case"]["candidate"],
                    "inputs": rig.controller.cases["synthetic-case"]["grant"]["inputs"]}
        report = verify.review_candidate(fd, inputs, expected)
        self.assertTrue(report["complete"])
        self.assertFalse(report["positive"])
        self.assertFalse(report["mechanism_failed"])
        self.assertIn("source payload is absent", report["findings"])
        candidate.chmod(0o700)

    def review_rig(self):
        rig = control_tests.ControlTests("test_registration_is_durable_and_unique")
        rig.setUp()
        self.addCleanup(rig.doCleanups)
        inputs, _ = rig.to_writing(stop_at="O4")
        parent = os.open(rig.root, os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, parent)
        return rig, inputs, parent, rig.controller.review_context("synthetic-case")

    def direct_review_rig(self):
        rig, inputs, parent, context = self.review_rig()
        candidate = os.open("candidate", os.O_RDONLY | os.O_DIRECTORY, dir_fd=parent)
        self.addCleanup(os.close, candidate)
        expected = {"uid": os.getuid(), "gid": os.getgid(), "candidate": context["candidate"],
                    "inputs": context["grant"]["inputs"]}
        return rig, inputs, candidate, expected

    def test_review_candidate_rejects_identical_bytes_in_another_inode(self):
        rig, inputs, candidate, expected = self.direct_review_rig()
        clone = self.root / "synthetic-source-clone"
        clone.write_bytes((rig.root / "source").read_bytes())
        clone.chmod(0o400)
        copied = os.open(clone, os.O_RDONLY | os.O_NOATIME | os.O_CLOEXEC)
        self.addCleanup(os.close, copied)
        self.assertNotEqual(os.fstat(copied).st_ino, os.fstat(inputs["source"]).st_ino)
        with self.assertRaises(verify.CustodyMismatch):
            verify.review_candidate(candidate, {**inputs, "source": copied}, expected)

    def test_review_candidate_rejects_original_permission_mismatch(self):
        rig, inputs, candidate, expected = self.direct_review_rig()
        (rig.root / "source").chmod(0o600)
        with self.assertRaises(verify.CustodyMismatch):
            verify.review_candidate(candidate, inputs, expected)

    def test_review_candidate_rejects_original_owner_binding_mismatch(self):
        _, inputs, candidate, expected = self.direct_review_rig()
        # Change the synthetic accepted binding; no privileged chown is needed.
        binding = {**expected["inputs"]["source"], "uid": os.getuid() + 1}
        expected = {**expected, "inputs": {**expected["inputs"], "source": binding}}
        with self.assertRaises(verify.CustodyMismatch):
            verify.review_candidate(candidate, inputs, expected)

    def test_review_candidate_rejects_a_different_reviewed_directory_identity(self):
        _, inputs, candidate, expected = self.direct_review_rig()
        expected = {**expected, "candidate": {**expected["candidate"], "inode": expected["candidate"]["inode"] + 1}}
        with self.assertRaises(verify.CustodyMismatch):
            verify.review_candidate(candidate, inputs, expected)

    def test_review_candidate_requires_complete_custody_bindings(self):
        _, inputs, candidate, expected = self.direct_review_rig()
        binding = {k: v for k, v in expected["inputs"]["source"].items() if k != "ctime_ns"}
        with self.assertRaises(verify.CustodyMismatch):
            verify.review_candidate(candidate, inputs, {**expected, "inputs": {**expected["inputs"], "source": binding}})

    def test_review_candidate_enforces_every_retained_input_metadata_field(self):
        _, inputs, candidate, expected = self.direct_review_rig()
        for field in ("device", "inode", "uid", "gid", "mode", "links", "mtime_ns", "ctime_ns"):
            with self.subTest(field=field):
                accepted = expected["inputs"]["source"]
                binding = {**accepted, field: accepted[field] + 1}
                with self.assertRaises(verify.CustodyMismatch):
                    verify.review_candidate(candidate, inputs, {**expected,
                        "inputs": {**expected["inputs"], "source": binding}})

    def test_review_candidate_requires_an_exact_candidate_binding(self):
        _, inputs, candidate, expected = self.direct_review_rig()
        with self.assertRaises(verify.CustodyMismatch):
            verify.review_candidate(candidate, inputs, {k: v for k, v in expected.items() if k != "candidate"})

    def test_review_candidate_unavailable_observation_has_no_completed_verdict(self):
        _, inputs, candidate, expected = self.direct_review_rig()
        with mock.patch.object(verify.os, "pread", side_effect=PermissionError("synthetic unavailable observation")):
            with self.assertRaises(verify.ObservationUncertain):
                verify.review_candidate(candidate, inputs, expected)

    def test_review_candidate_unstable_custody_has_no_completed_verdict(self):
        rig, inputs, candidate, expected = self.direct_review_rig()
        real_pread = os.pread
        changed = []
        def change_during_read(fd, length, offset):
            value = real_pread(fd, length, offset)
            if not changed:
                changed.append(True)
                (rig.root / "source").chmod(0o600)
            return value
        with mock.patch.object(verify.os, "pread", side_effect=change_during_read):
            with self.assertRaises(verify.ObservationUncertain):
                verify.review_candidate(candidate, inputs, expected)

    def test_review_candidate_detects_custody_change_after_initial_identity_check(self):
        rig, inputs, candidate, expected = self.direct_review_rig()
        real_equal = verify.equal_files
        changed = []
        def change_after_comparison(left, right):
            result = real_equal(left, right)
            if not changed:
                changed.append(True)
                (rig.root / "source").chmod(0o600)
            return result
        with mock.patch.object(verify, "equal_files", side_effect=change_after_comparison):
            with self.assertRaises(verify.ObservationUncertain):
                verify.review_candidate(candidate, inputs, expected)

    def test_review_candidate_rejects_an_actual_different_candidate_directory(self):
        _, inputs, _, expected = self.direct_review_rig()
        other = control_tests.ControlTests("test_registration_is_durable_and_unique")
        other.setUp()
        self.addCleanup(other.doCleanups)
        other.to_writing(stop_at="O4")
        foreign = os.open(other.root / "candidate", os.O_RDONLY | os.O_DIRECTORY)
        self.addCleanup(os.close, foreign)
        with self.assertRaises(verify.CustodyMismatch):
            verify.review_candidate(foreign, inputs, expected)

    def test_result_observer_returns_actual_artifacts_bound_to_current_lifecycle(self):
        rig, inputs, parent, context = self.review_rig()
        receipt = verify.review_result(parent, inputs, context, rig.controller.records_fd,
                                        rig.keys["S"], rig.keys["C"], rig.keys["V"])
        self.assertEqual(receipt["actor"], "V")
        self.assertEqual(receipt["body"]["binding"], context)
        result = receipt["body"]["result"]
        self.assertTrue(result["positive"])
        self.assertEqual(result["observations"]["source"]["sha256"],
                         hashlib.sha256((rig.root / "candidate" / "qualification_authority.py").read_bytes()).hexdigest())
        self.assertEqual(result["directory"]["inode"], (rig.root / "candidate").stat().st_ino)

    def test_result_observer_rejects_foreign_lifecycle_bindings(self):
        rig, inputs, parent, context = self.review_rig()
        for field in ("head", "initialization", "producer_head", "review_authority"):
            with self.subTest(field=field):
                changed = {**context, field: "f" * 64}
                with self.assertRaises(verify.InvalidEvidence):
                    verify.review_result(parent, inputs, changed, rig.controller.records_fd,
                                          rig.keys["S"], rig.keys["C"], rig.keys["V"])
        for field in ("id", "attempt", "destination"):
            with self.subTest(grant_field=field):
                changed = {**context, "grant": {**context["grant"], field: "synthetic-other"}}
                with self.assertRaises(verify.InvalidEvidence):
                    verify.review_result(parent, inputs, changed, rig.controller.records_fd,
                                          rig.keys["S"], rig.keys["C"], rig.keys["V"])

    def test_result_observer_rejects_original_input_substitution(self):
        rig, inputs, parent, context = self.review_rig()
        (rig.root / "source").chmod(0o600)
        with self.assertRaises(verify.InvalidEvidence):
            verify.review_result(parent, inputs, context, rig.controller.records_fd,
                                  rig.keys["S"], rig.keys["C"], rig.keys["V"])

    def test_result_observer_cannot_use_unconfirmed_review_intake(self):
        rig, inputs, parent, context = self.review_rig()
        (rig.root / "records" / f"{rig.controller.sequence:06d}.json").unlink()
        with self.assertRaises(verify.InvalidEvidence):
            verify.review_result(parent, inputs, context, rig.controller.records_fd,
                                  rig.keys["S"], rig.keys["C"], rig.keys["V"])


if __name__ == "__main__":
    unittest.main()
