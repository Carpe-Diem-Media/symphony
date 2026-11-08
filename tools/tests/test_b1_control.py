"""Synthetic B1 tests. All created objects belong to the explicit test root."""

import hashlib
import hmac
import importlib.util
import json
import os
from pathlib import Path
import tempfile
from unittest import mock
import unittest


TOOLS = Path(__file__).resolve().parents[1]


def load(name):
    spec = importlib.util.spec_from_file_location(name, TOOLS / (name + ".py"))
    if spec is None or spec.loader is None:
        return None
    try:
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        return module
    except FileNotFoundError:
        return None


control = load("b1_control")
verifier = load("b1_verify")


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=True,
                      allow_nan=False).encode("ascii")


def envelope(keys, actor, body):
    message = {"actor": actor, "body": body}
    return {**message, "mac": hmac.new(keys[actor], canonical(message), "sha256").hexdigest()}


def test_root():
    raw = os.environ.get("B1_TEST_ROOT")
    if not raw:
        raise RuntimeError("B1_TEST_ROOT must explicitly name the authorized artifact root")
    root = Path(raw)
    local = Path("/home/jcschoeman96/projects/symphony-b1-control-r0/.b1-control-test")
    runner = os.environ.get("RUNNER_TEMP")
    if root != local and not (runner and root.is_relative_to(Path(runner))
                              and root != Path(runner)):
        raise RuntimeError("test root is outside the authorized local/CI locations")
    if not root.is_absolute() or root.resolve() != root:
        raise RuntimeError("test root must be an absolute path without symlinks")
    return root


class ControlTests(unittest.TestCase):
    def setUp(self):
        self.assertIsNotNone(control, "the bounded B1 controller must be implemented")
        self.directory = tempfile.TemporaryDirectory(prefix="control-", dir=test_root())
        self.root = Path(self.directory.name)
        self.keys = {actor: os.urandom(32) for actor in ("H", "P", "M", "S", "V", "C")}
        self.receipts = []
        self.controller = control.Controller(self.root, self.keys, self.ack, reviewer=self.independent_review)
        self.addCleanup(self.controller.close)
        self.addCleanup(self.directory.cleanup)

    def ack(self, record):
        body = {"scope": "synthetic", "namespace": control.NAMESPACE,
                "case": record["case"], "sequence": record["sequence"],
                "record_sha256": hashlib.sha256(canonical(record)).hexdigest(),
                "expires": self.controller.clock() + 300}
        answer = envelope(self.keys, "C", body)
        self.receipts.append(answer)
        return answer

    def register(self, case="synthetic-case", approval="synthetic-approval"):
        body = {"scope": "synthetic", "namespace": control.NAMESPACE, "case": case,
                "authorization_id": approval, "revision": "synthetic-r0",
                "expires": 2000000000,
                "approval_ref": "synthetic-owner-approval", "predecessor": {
                    "case": "synthetic-predecessor", "state": "PLAN_CHANGES_REQUESTED",
                    "decision_sha256": "1" * 64, "artifact_sha256": "2" * 64},
                "governing": {"commit": "3" * 40, "tree": "4" * 40,
                              "plan_blob": "5" * 40}}
        return self.controller.register(envelope(self.keys, "H", body))

    def request(self, transition, evidence=None, case="synthetic-case"):
        actor = control.TRANSITIONS[transition][2]
        body = {"scope": "synthetic", "case": case, "transition": transition,
                "expected_head": self.controller.head, "evidence": evidence or {}}
        return self.controller.apply(envelope(self.keys, actor, body))

    def independent_review(self, context):
        parent = os.open(self.root, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
        records = os.open("records", os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC, dir_fd=parent)
        try:
            return verifier.review_result(parent, self.input_fds, context, records,
                                           self.keys["S"], self.keys["C"], self.keys["V"])
        finally:
            os.close(records)
            os.close(parent)

    def review_decision(self):
        receipt = self.independent_review(self.controller.review_context("synthetic-case"))
        result = receipt["body"]["result"]
        return {"complete": result["complete"], "mechanism_failed": result["mechanism_failed"],
                "positive": result["positive"], "evidence_sha256": control.digest(receipt["body"])}

    def test_complete_contract_registry(self):
        self.assertEqual(len(control.NONTERMINAL), 9)
        self.assertEqual(len(control.TERMINAL), 10)
        self.assertEqual(len(control.TRANSITIONS), 66)
        self.assertEqual(sum(k.startswith("B1-T") for k in control.TRANSITIONS), 12)
        for state in control.NONTERMINAL:
            for family in "UREAFI":
                self.assertEqual(control.TRANSITIONS[f"B1-{family}-{state}"][0], state)
        self.assertTrue(all(row[0] not in control.TERMINAL
                            for row in control.TRANSITIONS.values()))

    def test_registration_is_durable_and_unique(self):
        result = self.register()
        self.assertEqual(result["state"], "P0")
        self.assertTrue(list((self.root / "records").glob("*.json")))
        with self.assertRaises(control.Denied):
            self.register()

    def test_approval_cannot_register_another_case(self):
        self.register()
        with self.assertRaises(control.Denied):
            self.register("synthetic-another")

    def test_missing_initial_acknowledgment_denies_p0(self):
        self.controller.acknowledge = lambda record: None
        with self.assertRaises(control.Denied):
            self.register()
        self.assertNotIn("synthetic-case", self.controller.cases)
        self.assertTrue(self.controller.blocked)

    def test_initial_ack_after_authorization_expiry_cannot_establish_p0(self):
        def late_ack(record):
            self.controller.clock = lambda: 2000000001
            return self.ack(record)
        self.controller.acknowledge = late_ack
        with self.assertRaises(control.Denied):
            self.register()
        self.assertNotIn("synthetic-case", self.controller.cases)
        self.assertTrue(self.controller.blocked)

    def test_grant_expiry_while_consumption_ack_is_pending_denies_confirmation(self):
        self.to_writing(stop_at="O0")
        def late_ack(record):
            self.controller.clock = lambda: 2000000001
            return self.ack(record)
        self.controller.acknowledge = late_ack
        with self.assertRaises(control.Denied):
            self.request("B1-T07", {"entitlement": "synthetic-grant"})
        self.assertEqual(self.controller.cases["synthetic-case"]["state"], "O0")
        self.assertTrue(self.controller.blocked)

    def test_changed_or_replayed_receipt_denies_progress(self):
        self.register()
        old = self.receipts[-1]
        self.controller.acknowledge = lambda record: old
        with self.assertRaises(control.Denied):
            self.request("B1-T01", {"revision": "synthetic-r0"})
        self.assertEqual(self.controller.cases["synthetic-case"]["state"], "P0")
        self.assertTrue(self.controller.blocked)

    def test_unclean_restart_never_restores_eligibility(self):
        self.register()
        self.controller.close()
        with self.assertRaises(control.RecoveryRequired):
            control.Controller(self.root, self.keys, self.ack)

    def test_production_admission_is_closed_before_storage_effects(self):
        target = self.root / "production"
        with self.assertRaises(control.DeploymentNotQualified):
            control.open_production(target)
        self.assertFalse(target.exists())

    def fixtures(self):
        source, companion = b"synthetic source bytes only\n", b"synthetic companion only\n"
        export = b"prefix\n" + source + b"```\n" + companion + b"```\n"
        fds = {}
        bindings = {}
        for name, data in (("source", source), ("companion", companion), ("export", export)):
            path = self.root / name
            path.write_bytes(data)
            path.chmod(0o400)
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NOATIME | os.O_CLOEXEC)
            self.addCleanup(os.close, fd)
            fds[name] = fd
            bindings[name] = control.identify(fd)
        bindings["source"]["range"] = [7, 7 + len(source)]
        start = 7 + len(source) + 4
        bindings["companion"]["range"] = [start, start + len(companion)]
        self.input_fds = fds
        executable = os.open(os.environ["B1_COPY_EXECUTABLE"], os.O_RDONLY | os.O_CLOEXEC)
        self.addCleanup(os.close, executable)
        return fds, bindings, executable

    def to_writing(self, stop_at="O2"):
        self.register()
        if stop_at == "P0":
            return None, None
        self.request("B1-T01", {"revision": "synthetic-r0"})
        if stop_at == "P1":
            return None, None
        self.request("B1-T02", {"packet": {"bytes": 10, "sha256": "6" * 64}})
        if stop_at == "P2":
            return None, None
        self.request("B1-T03", {"decision": "7" * 64, "accepted": True})
        if stop_at == "P3":
            return None, None
        fds, bindings, executable = self.fixtures()
        grant = {"scope": "synthetic", "kind": "B1_MATERIALIZATION_SYNTHETIC",
                 "id": "synthetic-grant", "attempt": "synthetic-attempt",
                 "packet": {"bytes": 10, "sha256": "6" * 64}, "destination": "candidate",
                 "inputs": bindings, "executable": {**control.identify(executable),
                         "path": os.path.realpath(os.environ["B1_COPY_EXECUTABLE"])},
                 "expires": 2000000000,
                 "limits": {"wall_seconds": 30, "stop_seconds": 5, "memory_bytes": 134217728,
                            "file_bytes": 65536, "diagnostic_bytes": 4096},
                 "effects": ["candidate_directory", "two_payloads", "records", "two_copy_children",
                             "diagnostic_pipe", "bounded_stop"]}
        self.request("B1-T06", {"grant": grant})
        if stop_at == "O0":
            return fds, executable
        self.request("B1-T07", {"entitlement": "synthetic-grant"})
        if stop_at == "O1":
            return fds, executable
        self.request("B1-T08", {"ready": "synthetic-grant"})
        if stop_at in ("O3", "O4"):
            self.controller.copy("synthetic-case", fds, executable)
            self.request("B1-T09", {"producer_complete": True})
        if stop_at == "O4":
            self.request("B1-T10", {"review_authority": "8" * 64})
        return fds, executable

    def test_two_ordered_copies_and_positive_review(self):
        fds, executable = self.to_writing()
        result = self.controller.copy("synthetic-case", fds, executable)
        self.assertEqual(result["copies"], ["source", "companion"])
        candidate = self.root / "candidate"
        self.assertEqual((candidate / "qualification_authority.py").read_bytes(), b"synthetic source bytes only\n")
        self.assertEqual((candidate / "source_review_packet.md").read_bytes(), b"synthetic companion only\n")
        self.assertEqual(candidate.stat().st_mode & 0o777, 0o500)
        self.request("B1-T09", {"producer_complete": True})
        self.request("B1-T10", {"review_authority": "8" * 64})
        state = self.request("B1-T11", {"review": self.review_decision()})
        self.assertEqual(state["state"], "STAGING_VERIFIED")
        with self.assertRaises(control.Denied):
            self.controller.copy("synthetic-case", fds, executable)
        candidate.chmod(0o700)

    def test_unbacked_positive_review_digest_is_rejected(self):
        self.to_writing(stop_at="O4")
        sequence = self.controller.sequence
        with self.assertRaises(control.Denied):
            self.request("B1-T11", {"review": {"complete": True, "mechanism_failed": False,
                         "positive": True, "evidence_sha256": "9" * 64}})
        self.assertEqual(self.controller.cases["synthetic-case"]["state"], "O4")
        self.assertEqual(self.controller.sequence, sequence)

    def test_positive_review_requires_the_independent_result_interface(self):
        self.to_writing(stop_at="O4")
        decision = self.review_decision()
        self.controller.reviewer = None
        with self.assertRaises(control.Denied):
            self.request("B1-T11", {"review": decision})

    def test_foreign_result_binding_is_rejected_even_with_a_valid_verifier_signature(self):
        self.to_writing(stop_at="O4")
        original = self.independent_review(self.controller.review_context("synthetic-case"))
        changes = [("case", "synthetic-other"), ("initialization", "a" * 64),
                   ("head", "b" * 64), ("producer_head", "c" * 64),
                   ("review_authority", "d" * 64), ("grant.id", "synthetic-other-grant"),
                   ("grant.attempt", "synthetic-other-attempt"),
                   ("grant.destination", "other-candidate"), ("packet.sha256", "e" * 64),
                   ("candidate.inode", 1), ("parent.inode", 1)]
        sequence = self.controller.sequence
        for path, value in changes:
            with self.subTest(binding=path):
                body = json.loads(canonical(original["body"]))
                target = body["binding"]
                keys = path.split(".")
                for key in keys[:-1]:
                    target = target[key]
                target[keys[-1]] = value
                receipt = envelope(self.keys, "V", body)
                self.controller.reviewer = lambda context: receipt
                decision = {"complete": True, "mechanism_failed": False, "positive": True,
                            "evidence_sha256": control.digest(body)}
                with self.assertRaises(control.Denied):
                    self.request("B1-T11", {"review": decision})
                self.assertEqual(self.controller.sequence, sequence)
                self.assertEqual(self.controller.cases["synthetic-case"]["state"], "O4")

    def test_altered_verifier_result_is_rejected(self):
        self.to_writing(stop_at="O4")
        decision = self.review_decision()
        receipt = self.independent_review(self.controller.review_context("synthetic-case"))
        receipt["body"]["result"]["observations"]["source"]["sha256"] = "f" * 64
        self.controller.reviewer = lambda context: receipt
        with self.assertRaises(control.Denied):
            self.request("B1-T11", {"review": decision})

    def test_real_negative_result_cannot_be_presented_as_positive(self):
        self.to_writing(stop_at="O4")
        path = self.root / "candidate" / "qualification_authority.py"
        path.chmod(0o600)
        path.write_bytes(b"synthetic negative result\n")
        path.chmod(0o400)
        decision = self.review_decision()
        self.assertFalse(decision["positive"])
        decision["positive"] = True
        with self.assertRaises(control.Denied):
            self.request("B1-T11", {"review": decision})

    def test_payload_change_after_independent_observation_denies_acceptance(self):
        self.to_writing(stop_at="O4")
        decision = self.review_decision()
        def replace_after_review(context):
            receipt = self.independent_review(context)
            path = self.root / "candidate" / "qualification_authority.py"
            path.chmod(0o600)
            path.write_bytes(b"synthetic changed after verification\n")
            path.chmod(0o400)
            return receipt
        self.controller.reviewer = replace_after_review
        with self.assertRaises(control.Denied):
            self.request("B1-T11", {"review": decision})
        self.assertEqual(self.controller.cases["synthetic-case"]["state"], "O4")

    def test_replayed_result_after_journal_advancement_is_rejected(self):
        self.to_writing(stop_at="O4")
        decision = self.review_decision()
        receipt = self.independent_review(self.controller.review_context("synthetic-case"))
        self.register("synthetic-another-case", "synthetic-another-approval")
        self.controller.reviewer = lambda context: receipt
        with self.assertRaises(control.Denied):
            self.request("B1-T11", {"review": decision})

    def test_verifier_failure_remains_uncompleted_review(self):
        self.to_writing(stop_at="O4")
        decision = self.review_decision()
        def unavailable(context):
            raise OSError("synthetic independent observation failure")
        self.controller.reviewer = unavailable
        with self.assertRaises(control.Denied):
            self.request("B1-T11", {"review": decision})
        self.assertEqual(self.controller.cases["synthetic-case"]["state"], "O4")
        result = self.request("B1-F-O4", {"causes": ["procedure_failed"],
                              "review_mechanism_failed": True, "review_completed": False})
        self.assertEqual(result["state"], "FAILED")

    def test_accepted_result_is_retained_in_the_authenticated_transition(self):
        self.to_writing(stop_at="O4")
        decision = self.review_decision()
        self.request("B1-T11", {"review": decision})
        history = verifier.read_history(self.controller.records_fd, self.keys["S"], self.keys["C"])
        transition = next(event for event in reversed(history["events"])
                          if event["kind"] == "pending_transition")
        receipt = transition["payload"]["verification"]
        self.assertEqual(control.digest(receipt["body"]), decision["evidence_sha256"])
        self.assertTrue(receipt["body"]["result"]["positive"])
        self.assertEqual(receipt["body"]["binding"]["head"], transition["previous"])
        self.assertTrue(history["complete"])

    def test_missing_source_checkpoint_prevents_companion_creation(self):
        fds, executable = self.to_writing()
        normal_ack = self.ack
        def reject_source(record):
            if record["kind"] == "pending_checkpoint" and record["payload"].get("name") == "source":
                return None
            return normal_ack(record)
        self.controller.acknowledge = reject_source
        with self.assertRaises(control.Denied):
            self.controller.copy("synthetic-case", fds, executable)
        self.assertTrue((self.root / "candidate" / "qualification_authority.py").exists())
        self.assertFalse((self.root / "candidate" / "source_review_packet.md").exists())
        self.assertEqual(self.controller.cases["synthetic-case"]["copies"], ["source"])

    def test_input_substitution_is_rejected_before_candidate_creation(self):
        fds, executable = self.to_writing()
        (self.root / "source").chmod(0o600)
        (self.root / "source").write_bytes(b"substituted synthetic input\n")
        with self.assertRaises(control.Denied):
            self.controller.copy("synthetic-case", fds, executable)
        self.assertFalse((self.root / "candidate").exists())

    def test_existing_symlink_destination_is_never_adopted(self):
        fds, executable = self.to_writing()
        (self.root / "candidate").symlink_to("absent")
        with self.assertRaises(control.Denied):
            self.controller.copy("synthetic-case", fds, executable)
        self.assertTrue((self.root / "candidate").is_symlink())

    def test_expired_grant_denies_copy_without_creation(self):
        fds, executable = self.to_writing()
        self.controller.clock = lambda: 2000000001
        with self.assertRaises(control.Denied):
            self.controller.copy("synthetic-case", fds, executable)
        self.assertFalse((self.root / "candidate").exists())

    def test_dependency_substitution_is_rejected(self):
        fds, executable = self.to_writing()
        path = self.root / "different-executable"
        path.write_bytes(b"synthetic incorrect dependency")
        other = os.open(path, os.O_RDONLY)
        self.addCleanup(os.close, other)
        with self.assertRaises(control.Denied):
            self.controller.copy("synthetic-case", fds, other)
        self.assertFalse((self.root / "candidate").exists())

    def test_copy_timeout_stops_identified_child_and_denies_second_launch(self):
        fds, executable = self.to_writing()
        import time
        real_execve = os.execve
        def delayed_exec(*args):
            time.sleep(2)
            real_execve(*args)
        with mock.patch.object(control.os, "execve", delayed_exec):
            with self.assertRaises(control.Denied):
                self.controller.copy("synthetic-case", fds, executable, wall_seconds=0.05)
        self.assertFalse((self.root / "candidate" / "source_review_packet.md").exists())
        self.assertIsNone(self.controller.active_child)

    def test_all_six_adverse_families_from_p0_and_terminal_absorption(self):
        expected = {"U": ("uncertain", "UNCERTAIN"), "R": ("revoked", "REVOKED"),
                    "E": ("expired", "EXPIRED"), "A": ("authority_invalid", "AUTHORITY_INVALID"),
                    "F": ("procedure_failed", "FAILED"), "I": ("incomplete", "INCOMPLETE")}
        for family, (cause, destination) in expected.items():
            with self.subTest(family=family):
                case = "synthetic-case-" + family
                self.controller.clock = lambda: 1900000000
                self.register(case, "synthetic-approval-" + family)
                self.controller.clock = (lambda: 2000000001) if family == "E" else (lambda: 1900000000)
                result = self.request("B1-" + family + "-P0", {"causes": [cause]}, case)
                self.assertEqual(result["state"], destination)
                with self.assertRaises(control.Denied):
                    self.request("B1-T01", {"revision": "synthetic-r0"}, case)

    def test_uncertainty_defeats_failure(self):
        self.register()
        with self.assertRaises(control.Denied):
            self.request("B1-F-P0", {"causes": ["procedure_failed", "uncertain"]})
        self.assertEqual(self.request("B1-U-P0", {"causes": ["procedure_failed", "uncertain"]})["state"],
                         "UNCERTAIN")

    def test_every_adverse_transition_executes_from_its_actual_source(self):
        families = {"U": ("uncertain", "UNCERTAIN"), "R": ("revoked", "REVOKED"),
                    "E": ("expired", "EXPIRED"), "A": ("authority_invalid", "AUTHORITY_INVALID"),
                    "F": ("procedure_failed", "FAILED"), "I": ("incomplete", "INCOMPLETE")}
        count = 0
        for state in ("P0", "P1", "P2", "P3", "O0", "O1", "O2", "O3", "O4"):
            for family, (cause, destination) in families.items():
                with self.subTest(state=state, family=family):
                    rig = ControlTests("test_registration_is_durable_and_unique")
                    rig.setUp()
                    try:
                        rig.to_writing(stop_at=state)
                        if family == "E":
                            rig.controller.clock = lambda: 2000000001
                        evidence = {"causes": [cause]}
                        if state == "O4" and family == "F":
                            evidence.update(review_mechanism_failed=True, review_completed=False)
                        result = rig.request(f"B1-{family}-{state}", evidence)
                        self.assertEqual(result["state"], destination)
                        with self.assertRaises(control.Denied):
                            rig.request(f"B1-{family}-{state}", evidence)
                        count += 1
                    finally:
                        rig.doCleanups()
        self.assertEqual(count, 54)

    def test_planning_rejection_cases_remain_terminal(self):
        for transition, destination in (("B1-T04", "PLAN_CHANGES_REQUESTED"), ("B1-T05", "PLAN_REJECTED")):
            with self.subTest(transition=transition):
                rig = ControlTests("test_registration_is_durable_and_unique")
                rig.setUp()
                try:
                    rig.to_writing(stop_at="P2")
                    self.assertEqual(rig.request(transition, {"decision": "7" * 64})["state"], destination)
                    with self.assertRaises(control.Denied):
                        rig.request("B1-T03", {"decision": "8" * 64, "accepted": True})
                finally:
                    rig.doCleanups()

    def test_complete_negative_review_and_failed_review_have_disjoint_guards(self):
        self.to_writing(stop_at="O4")
        with self.assertRaises(control.Denied):
            self.request("B1-F-O4", {"causes": ["procedure_failed"],
                                      "review_mechanism_failed": False, "review_completed": True})
        path = self.root / "candidate" / "qualification_authority.py"
        path.chmod(0o600)
        path.write_bytes(b"synthetic known artifact defect\n")
        path.chmod(0o400)
        decision = self.review_decision()
        self.assertFalse(decision["positive"])
        result = self.request("B1-T12", {"review": decision})
        self.assertEqual(result["state"], "B1_REVIEW_REJECTED")

    def test_storage_sync_failure_leaves_unusable_pending_state(self):
        with mock.patch.object(control.os, "fsync", side_effect=OSError("synthetic fsync failure")):
            with self.assertRaises(OSError):
                self.register()
        self.assertTrue(self.controller.blocked)
        self.controller.close()
        with self.assertRaises(control.RecoveryRequired):
            control.Controller(self.root, self.keys, self.ack)

    def test_malformed_executable_binding_is_rejected_before_entitlement(self):
        self.to_writing(stop_at="P3")
        _, bindings, executable = self.fixtures()
        grant = {"scope": "synthetic", "kind": "B1_MATERIALIZATION_SYNTHETIC",
                 "id": "synthetic-grant", "attempt": "synthetic-attempt",
                 "packet": {"bytes": 10, "sha256": "6" * 64}, "destination": "candidate",
                 "inputs": bindings, "executable": {"sha256": "a" * 64}, "expires": 2000000000,
                 "limits": {"wall_seconds": 30, "stop_seconds": 5, "memory_bytes": 134217728,
                            "file_bytes": 65536, "diagnostic_bytes": 4096},
                 "effects": ["candidate_directory", "two_payloads", "records", "two_copy_children",
                             "diagnostic_pipe", "bounded_stop"]}
        with self.assertRaises(control.Denied):
            self.request("B1-T06", {"grant": grant})
        self.assertEqual(self.controller.cases["synthetic-case"]["state"], "P3")
        self.assertFalse(self.controller.cases["synthetic-case"]["consumed"])

    def test_copy_child_cannot_fork_a_descendant(self):
        fds, executable = self.to_writing()
        real_execve = os.execve
        def fork_attempt(*args):
            try:
                descendant = os.fork()
            except BlockingIOError:
                real_execve(*args)
            else:
                if descendant == 0:
                    os._exit(42)
                os.waitpid(descendant, 0)
                os._exit(44)
        with mock.patch.object(control.os, "execve", fork_attempt):
            result = self.controller.copy("synthetic-case", fds, executable)
        self.assertTrue(result["complete"])
        (self.root / "candidate").chmod(0o700)

    def test_launch_executes_the_accepted_descriptor(self):
        fds, executable = self.to_writing()
        real_execve = os.execve
        expected = control.identify(executable)
        def descriptor_exec(fd, arguments, environment):
            if fd != 3 or control.identify(fd) != expected:
                os._exit(45)
            real_execve(fd, arguments, environment)
        with mock.patch.object(control.os, "execve", descriptor_exec):
            result = self.controller.copy("synthetic-case", fds, executable)
        self.assertTrue(result["complete"])
        (self.root / "candidate").chmod(0o700)

    def test_wrong_actor_and_modified_authorization_have_no_effect(self):
        self.register()
        sequence = self.controller.sequence
        body = {"scope": "synthetic", "case": "synthetic-case", "transition": "B1-T01",
                "expected_head": self.controller.head, "evidence": {"revision": "synthetic-r0"}}
        with self.assertRaises(control.Denied):
            self.controller.apply(envelope(self.keys, "S", body))
        request = envelope(self.keys, "P", body)
        request["body"]["evidence"]["revision"] = "synthetic-forged"
        with self.assertRaises(control.Denied):
            self.controller.apply(request)
        self.assertEqual(self.controller.sequence, sequence)

    def test_planning_expiry_precedes_failure_and_denies_forward_progress(self):
        self.register()
        self.controller.clock = lambda: 2000000001
        with self.assertRaises(control.Denied):
            self.request("B1-T01", {"revision": "synthetic-r0"})
        with self.assertRaises(control.Denied):
            self.request("B1-F-P0", {"causes": ["procedure_failed"]})
        self.assertEqual(self.request("B1-E-P0", {"causes": ["expired"]})["state"], "EXPIRED")

    def test_double_consumption_and_gate_a_entitlement_are_rejected(self):
        self.to_writing(stop_at="O0")
        with self.assertRaises(control.Denied):
            self.request("B1-T07", {"entitlement": "L06"})
        self.request("B1-T07", {"entitlement": "synthetic-grant"})
        with self.assertRaises(control.Denied):
            self.request("B1-T07", {"entitlement": "synthetic-grant"})
        self.assertTrue(self.controller.cases["synthetic-case"]["consumed"])

    def test_fork_failure_never_refunds_a_launch_slot_or_restarts(self):
        fds, executable = self.to_writing()
        with mock.patch.object(control.os, "fork", side_effect=OSError("synthetic fork failure")):
            with self.assertRaises(control.Denied):
                self.controller.copy("synthetic-case", fds, executable)
        self.assertEqual(self.controller.cases["synthetic-case"]["copies"], ["source"])
        with self.assertRaises(control.Denied):
            self.controller.copy("synthetic-case", fds, executable)
        self.assertFalse((self.root / "candidate" / "source_review_packet.md").exists())

    def test_uncertain_stop_simulation_denies_progress(self):
        fds, executable = self.to_writing()
        # Simulate only the failed observation. No untracked real child is left.
        with mock.patch.object(self.controller, "_launch", side_effect=control.Denied(
                "UNCERTAIN: synthetic stop acknowledgment unavailable")):
            with self.assertRaises(control.Denied):
                self.controller.copy("synthetic-case", fds, executable)
        self.assertTrue(self.controller.blocked)
        self.assertEqual(self.controller.cases["synthetic-case"]["copies"], ["source"])

    def test_one_supervisor_holds_namespace_lock(self):
        with self.assertRaises(BlockingIOError):
            control.Controller(self.root, self.keys, self.ack)

    def test_result_snapshot_cannot_modify_authoritative_in_memory_grant(self):
        self.to_writing(stop_at="O0")
        result = self.request("B1-T07", {"entitlement": "synthetic-grant"})
        result["grant"]["destination"] = "forged"
        self.assertEqual(self.controller.cases["synthetic-case"]["grant"]["destination"], "candidate")


if __name__ == "__main__":
    unittest.main()
