"""Finite synthetic gate tests. They confer no owner identity or custody claim."""

import copy
import importlib.util
import json
import os
from pathlib import Path
import socket
import stat
import tempfile
import time
import unittest
from unittest import mock
from p08_qualification_runner import install_write_audit

install_write_audit()

REPO = Path(__file__).resolve().parents[2]
OUT = REPO / ".p08-authority-test-output"
CASE_IDS = {
    'test_one_use_consumption_and_replay_exact_error':['N14'],
    'test_concurrent_consumers_have_one_winner':['GT01'],
    'test_partial_transaction_burns_all_three_identities':['GT02'],
    'test_crash_after_first_marker_does_not_allow_nonce_replay':['GT02'],
    'test_fsync_uncertainty_is_terminal':['GT02'],
    'test_missing_epoch_and_epoch_rollback_refuse':['GT03'],
    'test_replaced_lock_and_malformed_prior_history_refuse':['GT03'],
    'test_replaced_register_is_detected_before_reservation':['GT03'],
    'test_wrong_run_nonce_command_or_custody_refuses':['GT04','GT07'],
    'test_exact_sixty_second_freshness_boundary':['N34','P03','GT05'],
    'test_clock_session_backwards_and_unknown_refuse':['N35','GT06'],
    'test_current_status_requires_clock_baseline':['GT06'],
    'test_entire_utc_interval_must_be_inside_validity':['GT06'],
    'test_late_observation_burns_grant_without_launch':['N38','N39','GT07'],
    'test_authenticated_late_verifier_refusal_burns_all_ids':['N39'],
    'test_exec_failure_burns_grant_without_retry':['GT09'],
    'test_observed_revocation_terminates_finite_sentinel':['N23','GT09'],
    'test_status_source_change_terminates_even_without_revoked_id':['N23'],
    'test_clock_context_change_after_launch_terminates':['GT06'],
    'test_advancing_clock_context_completes_finite_sentinel':['GT06'],
    'test_fifo_history_is_rejected_without_blocking_open':['GT03'],
    'test_socket_records_refuse_with_typed_error':['GT03'],
    'test_finite_nonzero_sentinel_retains_failure':['N24'],
    'test_unknown_operator_installation_has_no_cli_path':['GT08','GT12'],
    'test_full_signed_fixture_executes_only_finite_sentinel':['GT10'],
    'test_bounded_network_or_unlisted_exec_request_is_not_admitted':['GT11'],
    'test_missing_external_policy_status_blocks_without_launch':['N17'],
    'test_invalid_historical_register_records_refuse_without_mutation':['GT03'],
    'test_history_scan_validates_all_records_before_replay':['GT03'],
    'test_valid_historical_register_shapes_remain_usable':['GT03'],
    'test_execute_invalid_history_refuses_without_event_or_launch':['GT03'],
}
_spec = importlib.util.spec_from_file_location("gate_under_test", REPO / "tools/p08_authority/gate.py")
gate = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(gate)


def checked_action():
    grant = {"grant_id": "1" * 32, "run_id": "2" * 32, "nonce": "3" * 64,
             "trust_epoch": 7, "issued_at": 900, "not_before": 900, "expires_at": 1800,
             "max_duration_s": 2, "source_commit": "4" * 40, "source_tree": "5" * 40,
             "command_profile_sha256": "6" * 64, "authorization_scope": "BUILD_ONLY",
             "observed_execution_profile_sha256": "7" * 64}
    status = {"now_min": 1000, "now_max": 1000, "trust_epoch": 7,
              "clock_session_id": "8" * 32, "monotonic_ns": 120_000_000_000,
              "enrollment_sha256": "9" * 64, "current_decisions_sha256": "a" * 64,
              "revocations_sha256": "b" * 64, "operator_id": "test-operator", "revoked_ids": []}
    report = {"schema": "p08-action-observation-1", "purpose": "ACTION_PREFLIGHT_ONLY",
              "clock_session_id": status["clock_session_id"], "completed_monotonic_ns": 100_000_000_000,
              "evidence_sha256": "c" * 64}
    observed = dict(grant, evidence_sha256=report["evidence_sha256"],
                    clock_session_id=status["clock_session_id"], monotonic_ns=status["monotonic_ns"])
    checked = {"grant": grant, "records": {"G": grant}, "roles": {
        "project-owner-issuer": {"not_before": 800, "expires_at": 1900},
        "independent-reviewer": {"not_before": 800, "expires_at": 1900}},
        "action_observation": report, "external_status": status}
    return checked, status, observed


class GateTests(unittest.TestCase):
    def setUp(self):
        self.case_observations = []
        self.temp = tempfile.TemporaryDirectory(prefix="gate-", dir=OUT / "tmp")
        self.root = Path(self.temp.name)
        self.root.chmod(0o700)
        path = self.root / "epoch.json"
        path.write_bytes(gate.verify.canonical({"epoch": 7}))
        path.chmod(0o600)
        self.checked, self.status, self.observed = checked_action()

    def tearDown(self):
        # Registers stay available as original test evidence. TemporaryDirectory
        # cleanup is detached so the transfer inventory can retain these facts.
        self.temp._finalizer.detach()
        result = self._outcome.result
        failed = any(test.id().startswith(self.id()) for test, unused in result.errors + result.failures)
        for case_id in CASE_IDS.get(self._testMethodName, []):
            with (OUT/'logs/gate-cases.jsonl').open('a',encoding='ascii') as stream:
                stream.write(json.dumps({'id':case_id,'test':self.id(),'expected':'ASSERTIONS_PASS',
                    'actual':'FAILED' if failed else 'ASSERTIONS_PASS','observations':self.case_observations,
                    'scope':'SYNTHETIC_SOURCE_GATE_ONLY'},sort_keys=True)+'\n')

    def refuses(self, code, function, *args, **kwargs):
        with self.assertRaises(gate.Refusal) as raised:
            function(*args, **kwargs)
        self.case_observations.append({'expected':code,'actual':raised.exception.code})
        self.assertEqual(code, raised.exception.code)
        return raised.exception

    @staticmethod
    def _history_record(grant=None, state="CONSUMED"):
        grant = grant or checked_action()[0]["grant"]
        return {"epoch": 7, "grant_id": grant["grant_id"], "nonce": grant["nonce"],
                "run_id": grant["run_id"], "state": state}

    def _write_history(self, directory, role, record, identifier=None, raw=None):
        identifier = identifier or record["nonce" if role == "nonce" else role + "_id"]
        name = role + "-" + identifier + ".json"
        path = directory / name
        path.write_bytes(gate.verify.canonical(record) if raw is None else raw)
        path.chmod(0o600)
        return path

    @staticmethod
    def _history_snapshot(directory):
        snapshot = {}
        for path in directory.iterdir():
            info = path.lstat()
            if not stat.S_ISREG(info.st_mode):
                raise AssertionError("unexpected nonregular history fixture")
            snapshot[path.name] = (info.st_ino, info.st_uid, stat.S_IMODE(info.st_mode), path.read_bytes())
        return snapshot

    def _assert_invalid_history(self, directory, label, candidate=None):
        checked, context, status, observed = self._execution_context()
        if candidate is not None:
            checked["grant"] = candidate
            checked["records"]["G"] = candidate
            observed.update({key: candidate[key] for key in ("grant_id", "run_id", "nonce")})
        with gate.OneUseRegister(directory, 7):
            before = self._history_snapshot(directory)
        for entry in ("consume", "execute"):
            with self.subTest(history=label, entry=entry), \
                    mock.patch.object(gate.subprocess, "Popen",
                                      side_effect=AssertionError("unexpected history launch")) as process:
                started = time.monotonic()
                if entry == "consume":
                    with gate.OneUseRegister(directory, 7) as register:
                        self.refuses("REGISTER_UNCERTAIN", register.consume, checked["grant"])
                else:
                    with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
                        self.refuses("REGISTER_UNCERTAIN", gate.execute, {}, context, directory,
                                     lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
                elapsed = time.monotonic() - started
                self.assertLess(elapsed, 1.0)
                process.assert_not_called()
                self.assertEqual(before, self._history_snapshot(directory))
                self.assertFalse(list(directory.glob("event-*.json")))
                self.case_observations.append({"history": label, "entry": entry,
                    "expected": "REGISTER_UNCERTAIN", "actual": "REGISTER_UNCERTAIN",
                    "seconds": elapsed, "history_unchanged": True, "launches": 0,
                    "directory": directory.relative_to(OUT).as_posix()})

    def test_one_use_consumption_and_replay_exact_error(self):
        with gate.OneUseRegister(self.root, 7) as register:
            register.consume(self.checked["grant"])
            self.refuses("GRANT_REPLAY", register.consume, self.checked["grant"])
        self.assertEqual(3, len(list(self.root.glob("*-*.json"))))

    def test_run_and_nonce_cannot_be_reused_under_new_grant(self):
        with gate.OneUseRegister(self.root, 7) as register:
            register.consume(self.checked["grant"])
            for key in ("grant_id", "run_id", "nonce"):
                changed = copy.deepcopy(self.checked["grant"])
                for other in ("grant_id", "run_id", "nonce"):
                    changed[other] = "d" * len(changed[other])
                changed[key] = self.checked["grant"][key]
                self.refuses("GRANT_REPLAY", register.consume, changed)

    def test_partial_transaction_burns_all_three_identities(self):
        with gate.OneUseRegister(self.root, 7) as register:
            write = register._write
            calls = 0
            def fail_second(name, record):
                nonlocal calls
                calls += 1
                if calls == 2:
                    raise OSError("synthetic write failure")
                write(name, record)
            with mock.patch.object(register, "_write", fail_second):
                self.refuses("REGISTER_UNCERTAIN", register.consume, self.checked["grant"])
            new = dict(self.checked["grant"], grant_id="e" * 32, run_id="f" * 32)
            self.refuses("GRANT_REPLAY", register.consume, new)

    def test_crash_after_first_marker_does_not_allow_nonce_replay(self):
        pid = os.fork()
        if pid == 0:
            with gate.OneUseRegister(self.root, 7) as register:
                write = register._write
                def crash(name, record):
                    write(name, record)
                    os._exit(17)
                register._write = crash
                register.consume(self.checked["grant"])
            os._exit(99)
        _, result = os.waitpid(pid, 0)
        self.assertEqual(17, os.waitstatus_to_exitcode(result))
        with gate.OneUseRegister(self.root, 7) as register:
            self.refuses("GRANT_REPLAY", register.consume,
                         dict(self.checked["grant"], grant_id="e" * 32, run_id="f" * 32))

    def test_fsync_uncertainty_is_terminal(self):
        with gate.OneUseRegister(self.root, 7) as register:
            with mock.patch.object(gate.os, "fsync", side_effect=OSError("synthetic fsync failure")):
                self.refuses("REGISTER_UNCERTAIN", register.consume, self.checked["grant"])
            self.refuses("GRANT_REPLAY", register.consume, self.checked["grant"])

    def test_concurrent_consumers_have_one_winner(self):
        children = []
        for _ in range(2):
            pid = os.fork()
            if pid == 0:
                try:
                    with gate.OneUseRegister(self.root, 7) as register:
                        register.consume(self.checked["grant"])
                    os._exit(0)
                except gate.Refusal as error:
                    os._exit(1 if error.code == "GRANT_REPLAY" else 9)
            children.append(pid)
        results = [os.waitstatus_to_exitcode(os.waitpid(pid, 0)[1]) for pid in children]
        self.assertEqual([0, 1], sorted(results))

    def test_missing_epoch_and_epoch_rollback_refuse(self):
        self.refuses("STATUS_INVALID", lambda: gate.OneUseRegister(self.root, 8).__enter__())
        (self.root / "epoch.json").unlink()
        self.refuses("REGISTER_INVALID", lambda: gate.OneUseRegister(self.root, 7).__enter__())

    def test_replaced_lock_and_malformed_prior_history_refuse(self):
        target = self.root / "elsewhere"
        target.write_bytes(b"")
        (self.root / ".lock").symlink_to(target)
        self.refuses("REGISTER_INVALID", lambda: gate.OneUseRegister(self.root, 7).__enter__())
        (self.root / ".lock").unlink()
        p = self.root / ("grant-" + "a" * 32 + ".json")
        p.write_bytes(b'{"epoch":7}')
        p.chmod(0o600)
        with gate.OneUseRegister(self.root, 7) as register:
            self.refuses("REGISTER_UNCERTAIN", register.consume, self.checked["grant"])

    def test_invalid_historical_register_records_refuse_without_mutation(self):
        candidate = dict(self.checked["grant"], grant_id="d" * 32, run_id="e" * 32,
                         nonce="f" * 64)
        malformed_cases = (
            ("unknown-state", "grant", self._history_record(state="UNRECOGNIZED_STATE"), None, None),
            ("event-state", "grant", self._history_record(state="LAUNCHED"), None, None),
            ("unhashable-state", "grant", self._history_record(state=[{}]), None, None),
            ("wrong-epoch", "grant", dict(self._history_record(), epoch=8), None, None),
            ("boolean-epoch", "grant", None, None,
             b'{"epoch":true,"grant_id":"' + b'1' * 32 + b'","nonce":"' + b'3' * 64
             + b'","run_id":"' + b'2' * 32 + b'","state":"CONSUMED"}'),
            ("invalid-identity", "grant", dict(self._history_record(), run_id="bad"), None, None),
            ("unknown-field", "grant", dict(self._history_record(), extra=7), None, None),
            ("missing-field", "grant", {k: v for k, v in self._history_record().items()
                                         if k != "state"}, None, None),
            ("noncanonical-bytes", "grant", self._history_record(), None,
             gate.verify.canonical(self._history_record()) + b'\n'),
            ("scalar-json", "grant", None, None, b'7'),
            ("array-dict-json", "run", None, None, b'[{"x":1}]'),
            ("mismatched-grant-filename", "grant", self._history_record(), "c" * 32, None),
            ("mismatched-run-filename", "run", self._history_record(), "c" * 32, None),
            ("mismatched-nonce-filename", "nonce", self._history_record(), "c" * 64, None),
        )
        for label, role, record, identifier, raw in malformed_cases:
            with self.subTest(history=label):
                scratch = Path(tempfile.mkdtemp(prefix="invalid-history-", dir=OUT / "tmp"))
                scratch.chmod(0o700)
                (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
                (scratch / "epoch.json").chmod(0o600)
                if record is not None and label.startswith("mismatched-"):
                    key = role + "_id" if role != "nonce" else "nonce"
                    record = dict(record, **{key: "9" * len(record[key])})
                if record is None:
                    # Keep the filename canonical for each malformed JSON value.
                    record = self._history_record()
                self._write_history(scratch, role, record, identifier, raw)
                self._assert_invalid_history(scratch, label, candidate)

    def test_history_scan_validates_all_records_before_replay(self):
        candidate = self.checked["grant"]
        match = self._history_record(candidate)
        malformed = dict(self._history_record(), run_id="9" * 32)
        for role, record in (("grant", match), ("run", malformed)):
            self._write_history(self.root, role, record)
        self._assert_invalid_history(self.root, "history-before-replay", candidate)

        for conflict in ("shared-run", "shared-nonce", "state"):
            scratch = Path(tempfile.mkdtemp(prefix="conflicting-history-", dir=OUT / "tmp"))
            scratch.chmod(0o700)
            (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
            (scratch / "epoch.json").chmod(0o600)
            first = self._history_record(dict(self.checked["grant"], grant_id="1" * 32,
                                               run_id="2" * 32, nonce="3" * 64))
            second_grant = dict(self.checked["grant"], grant_id="4" * 32,
                                run_id="5" * 32, nonce="6" * 64)
            second = self._history_record(second_grant)
            if conflict == "shared-run":
                second["run_id"] = first["run_id"]
            elif conflict == "shared-nonce":
                second["nonce"] = first["nonce"]
            else:
                second["grant_id"], second["run_id"], second["nonce"] = (
                    first["grant_id"], first["run_id"], first["nonce"])
                second["state"] = "REFUSED"
            self._write_history(scratch, "grant", first)
            self._write_history(scratch, "nonce", second)
            candidate = dict(self.checked["grant"], grant_id="7" * 32,
                             run_id="8" * 32, nonce="9" * 64)
            self._assert_invalid_history(scratch, conflict, candidate)

    def test_valid_historical_register_shapes_remain_usable(self):
        base = self.checked["grant"]
        same_role_value = "a" * 32
        same_role = dict(base, grant_id=same_role_value, run_id=same_role_value,
                         nonce="b" * 64)
        with gate.OneUseRegister(self.root, 7) as register:
            register.consume(same_role, "REFUSED")
        unrelated = dict(base, grant_id="c" * 32, run_id="d" * 32, nonce="e" * 64)
        with gate.OneUseRegister(self.root, 7) as register:
            register.consume(unrelated)
        markers = [path for path in self.root.glob("*-*.json")
                   if path.name.startswith(("grant-", "run-", "nonce-"))]
        self.assertEqual(6, len(markers))
        self.assertTrue(all(json.loads(path.read_bytes())["state"] in {"CONSUMED", "REFUSED"}
                            for path in markers))
        self.case_observations.append({"expected": "REFUSED_HISTORY_AND_SHARED_CROSS_ROLE_VALUE_ACCEPTED",
                                       "actual": "ACCEPTED"})

        scratch = Path(tempfile.mkdtemp(prefix="valid-partial-", dir=OUT / "tmp"))
        scratch.chmod(0o700)
        (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
        (scratch / "epoch.json").chmod(0o600)
        history = self._write_history(scratch, "run", self._history_record(same_role))
        original = history.read_bytes()
        with gate.OneUseRegister(scratch, 7) as register:
            register.consume(unrelated)
            for key in ("grant_id", "run_id", "nonce"):
                attempt = dict(base, grant_id="7" * 32, run_id="8" * 32, nonce="9" * 64)
                attempt[key] = same_role[key]
                self.refuses("GRANT_REPLAY", register.consume, attempt)
        self.assertEqual(original, history.read_bytes())
        self.assertEqual(4, len([p for p in scratch.iterdir()
                               if p.name.startswith(("grant-", "run-", "nonce-"))]))
        self.case_observations.append({"history": "valid-partial", "expected": "UNRELATED_ACCEPTED_REPLAY_DENIED",
                                       "actual": "UNRELATED_ACCEPTED_REPLAY_DENIED"})

    def test_execute_invalid_history_refuses_without_event_or_launch(self):
        checked, context, status, observed = self._execution_context()
        old_grant = dict(checked["grant"], grant_id="d" * 32, run_id="e" * 32,
                         nonce="f" * 64)
        malformed = dict(self._history_record(old_grant), state="UNCERTAIN")
        self._write_history(self.root, "grant", malformed)
        with gate.OneUseRegister(self.root, 7):
            before = self._history_snapshot(self.root)
        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked), \
                mock.patch.object(gate.subprocess, "Popen",
                                  side_effect=AssertionError("unexpected history launch")) as process:
            started = time.monotonic()
            self.refuses("REGISTER_UNCERTAIN", gate.execute, {}, context, self.root,
                         lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
            process.assert_not_called()
        self.assertLess(time.monotonic() - started, 1.0)
        self.assertEqual(before, self._history_snapshot(self.root))
        self.assertFalse(list(self.root.glob("event-*.json")))

    def test_exact_sixty_second_freshness_boundary(self):
        observed = dict(self.observed, monotonic_ns=160_000_000_000)
        accepted = gate.check_launch(copy.deepcopy(self.checked), copy.deepcopy(self.status), observed)
        self.case_observations.append({'predicate':'exact 60 seconds','expected':True,'actual':accepted})
        self.assertTrue(accepted)
        observed["monotonic_ns"] += 1
        self.refuses("ACTION_OBSERVATION_STALE", gate.check_launch, copy.deepcopy(self.checked),
                     copy.deepcopy(self.status), observed)

    def test_clock_session_backwards_and_unknown_refuse(self):
        for patch in ({"clock_session_id": "0" * 32}, {"monotonic_ns": 99_999_999_999},
                      {"monotonic_ns": 2**64}, {"monotonic_ns": None}):
            self.refuses("CLOCK_CONTEXT_INVALID", gate.check_launch, self.checked, self.status,
                         dict(self.observed, **patch))

    def test_current_status_requires_clock_baseline(self):
        invalid = (
            {"clock_session_id": "0" * 32},
            {"clock_session_id": None},
            {"monotonic_ns": "120000000000"},
            {"monotonic_ns": None},
            {"monotonic_ns": True},
            {"monotonic_ns": -1},
            {"monotonic_ns": 2**64},
            {"monotonic_ns": 119_999_999_999},
        )
        for patch in invalid:
            with self.subTest(patch=patch):
                self.refuses("CLOCK_CONTEXT_INVALID", gate.check_current, self.checked,
                             dict(self.status, **patch))
        for key in ("clock_session_id", "monotonic_ns"):
            missing = dict(self.status)
            missing.pop(key)
            with self.subTest(missing=key):
                self.refuses("CLOCK_CONTEXT_INVALID", gate.check_current, self.checked, missing)

    def test_fifo_history_is_rejected_without_blocking_open(self):
        for prefix in ("grant", "run", "nonce"):
            scratch = Path(tempfile.mkdtemp(prefix="fifo-case-", dir=OUT / "tmp"))
            scratch.chmod(0o700)
            (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
            (scratch / "epoch.json").chmod(0o600)
            with gate.OneUseRegister(scratch, 7) as register:
                register.consume(self.checked["grant"])
            fifo_name = prefix + "-" + "c" * (64 if prefix == "nonce" else 32) + ".json"
            os.mkfifo(scratch / fifo_name, 0o600)
            changed = dict(self.checked["grant"], grant_id="d" * 32, run_id="e" * 32,
                           nonce="f" * 64)
            real_open = gate.os.open
            guarded_opens = []

            def guarded_open(path, flags, *args, **kwargs):
                if path == fifo_name and (flags & os.O_ACCMODE) == os.O_RDONLY:
                    guarded_opens.append(flags)
                    self.assertTrue(flags & os.O_NONBLOCK,
                                    "FIFO history opens must use O_NONBLOCK")
                return real_open(path, flags, *args, **kwargs)

            started = time.monotonic()
            with mock.patch.object(gate.os, "open", side_effect=guarded_open):
                with gate.OneUseRegister(scratch, 7) as register:
                    self.refuses("REGISTER_INVALID", register.consume, changed)
            self.assertTrue(guarded_opens)
            self.assertLess(time.monotonic() - started, 1.0)
            markers = list(scratch.glob("*-*.json"))
            self.assertEqual(4, len(markers))
            self.assertEqual(3, sum(stat.S_ISREG(path.lstat().st_mode) for path in markers))
            self.case_observations.append({'position': prefix, 'type': 'FIFO',
                'expected': 'REGISTER_INVALID', 'actual': 'REGISTER_INVALID',
                'nonblocking_open_observed': bool(guarded_opens),
                'seconds': time.monotonic() - started, 'regular_history_entries_retained': 3})

        scratch = Path(tempfile.mkdtemp(prefix="fifo-epoch-", dir=OUT / "tmp"))
        scratch.chmod(0o700)
        os.mkfifo(scratch / "epoch.json", 0o600)
        real_open = gate.os.open
        guarded_opens = []

        def guarded_epoch_open(path, flags, *args, **kwargs):
            if path == "epoch.json" and (flags & os.O_ACCMODE) == os.O_RDONLY:
                guarded_opens.append(flags)
                self.assertTrue(flags & os.O_NONBLOCK,
                                "FIFO epoch opens must use O_NONBLOCK")
            return real_open(path, flags, *args, **kwargs)

        started = time.monotonic()
        with mock.patch.object(gate.os, "open", side_effect=guarded_epoch_open):
            self.refuses("REGISTER_INVALID", lambda: gate.OneUseRegister(scratch, 7).__enter__())
        self.assertTrue(guarded_opens)
        self.assertLess(time.monotonic() - started, 1.0)
        self.case_observations.append({'position': 'epoch', 'type': 'FIFO',
            'expected': 'REGISTER_INVALID', 'actual': 'REGISTER_INVALID',
            'nonblocking_open_observed': bool(guarded_opens), 'seconds': time.monotonic() - started})

        scratch = Path(tempfile.mkdtemp(prefix="directory-history-", dir=OUT / "tmp"))
        scratch.chmod(0o700)
        (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
        (scratch / "epoch.json").chmod(0o600)
        with gate.OneUseRegister(scratch, 7) as register:
            register.consume(self.checked["grant"])
        directory_name = "run-" + "b" * 32 + ".json"
        (scratch / directory_name).mkdir(mode=0o700)
        with gate.OneUseRegister(scratch, 7) as register:
            self.refuses("REGISTER_INVALID", register.consume,
                         dict(self.checked["grant"], grant_id="d" * 32,
                              run_id="e" * 32, nonce="f" * 64))

    def test_socket_records_refuse_with_typed_error(self):
        # AF_UNIX filesystem fixtures only. No listen, connect or traffic.
        self.assertEqual(REPO, Path.cwd())
        for position in ('epoch', 'history'):
            scratch = Path(tempfile.mkdtemp(prefix='socket-', dir=OUT / 'tmp'))
            scratch.chmod(0o700)
            if position == 'history':
                (scratch / 'epoch.json').write_bytes(gate.verify.canonical({'epoch': 7}))
                (scratch / 'epoch.json').chmod(0o600)
                with gate.OneUseRegister(scratch, 7) as register:
                    register.consume(self.checked['grant'])
            name = 'epoch.json' if position == 'epoch' else 'run-' + 'c' * 32 + '.json'
            with socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM) as fixture:
                # Relative spelling stays below the Unix socket path bound.
                fixture.bind((scratch / name).relative_to(REPO).as_posix())
                started = time.monotonic()
                if position == 'epoch':
                    self.refuses('REGISTER_INVALID', lambda: gate.OneUseRegister(scratch, 7).__enter__())
                else:
                    with gate.OneUseRegister(scratch, 7) as register:
                        self.refuses('REGISTER_INVALID', register.consume,
                            dict(self.checked['grant'], grant_id='d' * 32, run_id='e' * 32, nonce='f' * 64))
                elapsed = time.monotonic() - started
                self.assertLess(elapsed, 1.0)
                self.assertTrue(stat.S_ISSOCK((scratch / name).lstat().st_mode))
                self.case_observations.append({'position': position, 'type': 'AF_UNIX_SOCKET',
                    'expected': 'REGISTER_INVALID', 'actual': 'REGISTER_INVALID', 'seconds': elapsed})

    def _after_launch_clock_case(self, mutation):
        checked, context, status, observed = self._execution_context(
            "import time; time.sleep(2)")
        scratch = Path(tempfile.mkdtemp(prefix="clock-case-", dir=OUT / "tmp"))
        scratch.chmod(0o700)
        (scratch / "epoch.json").write_bytes(gate.verify.canonical({"epoch": 7}))
        (scratch / "epoch.json").chmod(0o600)
        shared_status = copy.deepcopy(status)
        calls = 0
        seen_launch = False
        mutated = False
        samples = []

        def current():
            nonlocal calls, seen_launch, mutated
            calls += 1
            launched = any(json.loads(path.read_text("ascii"))["state"] == "LAUNCHED"
                           for path in scratch.glob("event-*.json"))
            if calls > 1 and not mutated:
                shared_status["monotonic_ns"] += 1
            if launched:
                seen_launch = True
                if not mutated:
                    mutation(shared_status)
                    mutated = True
            samples.append({'session': shared_status.get('clock_session_id'),
                            'monotonic_ns': shared_status.get('monotonic_ns'),
                            'after_launch': launched})
            return shared_status

        def current_observation(unused):
            return dict(observed, monotonic_ns=shared_status["monotonic_ns"])

        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
            error = self.refuses("LEASE_TERMINATED", gate.execute, {}, context, scratch,
                                 current, current_observation)
        self.assertTrue(seen_launch)
        self.assertIsNotNone(error.__cause__)
        self.assertEqual("CLOCK_CONTEXT_INVALID", error.__cause__.code)
        self.assertLess(error.result["returncode"], 0)
        events = [json.loads(path.read_text("ascii"))
                  for path in sorted(scratch.glob("event-*.json"))]
        self.assertEqual("FAILED", events[-1]["state"])
        self.assertEqual("LEASE_TERMINATED:CLOCK_CONTEXT_INVALID", events[-1]["details"])
        markers = [path for path in scratch.glob('*.json')
                   if path.name.startswith(('grant-', 'run-', 'nonce-'))]
        self.assertEqual(3, len(markers))
        for path in markers:
            retained = json.loads(path.read_text('ascii'))
            self.assertEqual('CONSUMED', retained['state'])
            for key in ('grant_id', 'run_id', 'nonce'):
                self.assertEqual(checked['grant'][key], retained[key])
        with gate.OneUseRegister(scratch, 7) as register:
            self.refuses("GRANT_REPLAY", register.consume, checked["grant"])
        self.case_observations.append({"expected": "CLOCK_CONTEXT_INVALID_AFTER_LAUNCH",
                                       "actual_cause": error.__cause__.code,
                                       "returncode": error.result["returncode"],
                                       "samples": samples,
                                       "clock_sample": shared_status.get("monotonic_ns"),
                                       "session": shared_status.get("clock_session_id")})

    def test_clock_context_change_after_launch_terminates(self):
        cases = (
            lambda status: status.update(clock_session_id="0" * 32),
            lambda status: status.update(clock_session_id="e" * 32),
            lambda status: status.pop("clock_session_id"),
            lambda status: status.update(clock_session_id=None),
            lambda status: status.pop("monotonic_ns"),
            lambda status: status.update(monotonic_ns=True),
            lambda status: status.update(monotonic_ns=120_000_000_001),
        )
        for mutation in cases:
            with self.subTest(mutation=mutation):
                self._after_launch_clock_case(mutation)

    def test_advancing_clock_context_completes_finite_sentinel(self):
        checked, context, status, observed = self._execution_context("pass")
        shared_status = copy.deepcopy(status)
        samples = []

        def current():
            shared_status["monotonic_ns"] += 1
            samples.append(shared_status["monotonic_ns"])
            return shared_status

        def current_observation(unused):
            return dict(observed, monotonic_ns=shared_status["monotonic_ns"])

        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
            result = gate.execute({}, context, self.root, current,
                                  current_observation)
        self.assertEqual("COMPLETED", result["state"])
        self.assertTrue(samples)
        self.assertTrue(all(sample > status["monotonic_ns"] for sample in samples))
        self.assertEqual(sorted(samples), samples)
        self.case_observations.append({"expected": "COMPLETED_WITH_ADVANCING_CLOCK",
                                       "actual": result["state"], "samples": samples})

    def test_entire_utc_interval_must_be_inside_validity(self):
        self.refuses("CLOCK_CONTEXT_INVALID", gate.check_current, self.checked,
                     dict(self.status, now_max=1031))
        self.refuses("APPROVAL_STALE", gate.check_current, self.checked,
                     dict(self.status, now_min=1790, now_max=1800))
        self.refuses("APPROVAL_STALE", gate.check_current, self.checked,
                     dict(self.status, now_min=899, now_max=900))

    def test_wrong_run_nonce_command_or_custody_refuses(self):
        for key in ("grant_id", "run_id", "nonce", "source_commit", "source_tree",
                    "command_profile_sha256", "authorization_scope"):
            self.refuses("ACTION_BINDING_MISMATCH", gate.check_launch, self.checked, self.status,
                         dict(self.observed, **{key: "wrong"}))
        for key in ("evidence_sha256", "observed_execution_profile_sha256"):
            self.refuses("CUSTODY_FAILURE", gate.check_launch, self.checked, self.status,
                         dict(self.observed, **{key: "d" * 64}))

    def test_status_epoch_revocation_and_conflict_refuse(self):
        for patch in ({"trust_epoch": 6}, {"revoked_ids": ["grant"]}):
            self.refuses("STATUS_INVALID", gate.check_launch, self.checked,
                         dict(self.status, **patch), self.observed)
        self.refuses("STATUS_INVALID", gate.check_launch, self.checked,
                     dict(self.status, current_decisions_sha256="f" * 64), self.observed)

    def test_terminal_refusal_is_never_retried(self):
        with gate.OneUseRegister(self.root, 7) as register:
            register.consume(self.checked["grant"], "REFUSED")
            self.refuses("GRANT_REPLAY", register.consume, self.checked["grant"])

    def test_replaced_register_is_detected_before_reservation(self):
        with gate.OneUseRegister(self.root, 7) as register:
            previous = self.root.with_name(self.root.name + '-retained')
            self.root.rename(previous)
            self.root.mkdir(mode=0o700)
            self.refuses('REGISTER_UNCERTAIN', register.consume, self.checked['grant'])

    def test_authenticated_late_verifier_refusal_burns_all_ids(self):
        refusal = gate.Refusal('ACTION_OBSERVATION_STALE', self.checked['grant'])
        with mock.patch.object(gate.verify, 'verify_bundle', side_effect=refusal), \
                mock.patch.object(gate.subprocess, 'Popen') as process:
            self.refuses('ACTION_OBSERVATION_STALE', gate.execute, {}, {}, self.root,
                         lambda: copy.deepcopy(self.status), lambda _: copy.deepcopy(self.observed))
            process.assert_not_called()
        with gate.OneUseRegister(self.root, 7) as register:
            self.refuses('GRANT_REPLAY', register.consume, self.checked['grant'])

    def test_unknown_operator_installation_has_no_cli_path(self):
        self.refuses("INDEPENDENT_OPERATOR_INSTALLATION_NOT_APPROVED", gate.main)

    def test_missing_external_policy_status_blocks_without_launch(self):
        def unavailable():
            raise gate.Refusal('PROVENANCE_STALE')
        with mock.patch.object(gate.subprocess,'Popen') as process:
            self.refuses('PROVENANCE_STALE',gate.execute,{}, {},self.root,unavailable,lambda _: {})
            process.assert_not_called()

    def _execution_context(self, code="pass"):
        checked, status, observed = checked_action()
        raw = Path("/usr/bin/python3.14").read_bytes()
        entry = {"kind": "regular", "path": "/usr/bin/python3.14", "mode": "0755",
                 "bytes": len(raw), "sha256": gate.verify.sha256(raw)}
        inventory = {"schema": "p08-input-inventory-1", "entries": [entry]}
        invraw = gate.verify.canonical(inventory)
        ref = {"id": "fixture_python", "path": entry["path"], "resolved_path": entry["path"],
               "bytes": len(raw), "sha256": entry["sha256"], "provenance_sha256": "d" * 64,
               "inventory_sha256": gate.verify.sha256(invraw),
               "path_entry_sha256": gate.verify.sha256(gate.verify.canonical(entry)),
               "resolved_entry_sha256": gate.verify.sha256(gate.verify.canonical(entry)), "symlink_chain": []}
        checked["command"] = {"executable": ref, "working_directory": str(OUT), "argv": [
            {"index": i, "value": x} for i, x in enumerate([
                "/usr/bin/python3.14", "-I", "-S", "-B", "-c", code])]}
        checked["execution_profile"] = {"environment": [{"name": "PATH", "value": "/nonexistent"}]}
        context = {"status": status, "profiles": {gate.verify.sha256(invraw): invraw}, "sealed_roots": ["/usr"]}
        return checked, context, status, observed

    def test_late_observation_burns_grant_without_launch(self):
        checked, context, status, observed = self._execution_context()
        observations = iter([observed, dict(observed, monotonic_ns=160_000_000_001)])
        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked), \
                mock.patch.object(gate.subprocess, "Popen") as process:
            self.refuses("ACTION_OBSERVATION_STALE", gate.execute, {}, context, self.root,
                         lambda: copy.deepcopy(status), lambda _: next(observations))
            process.assert_not_called()
        with gate.OneUseRegister(self.root, 7) as register:
            self.refuses("GRANT_REPLAY", register.consume, checked["grant"])

    def test_exec_failure_burns_grant_without_retry(self):
        checked, context, status, observed = self._execution_context()
        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked), \
                mock.patch.object(gate.subprocess, "Popen", side_effect=OSError("synthetic exec failure")):
            with self.assertRaises(OSError):
                gate.execute({}, context, self.root, lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
        with gate.OneUseRegister(self.root, 7) as register:
            self.refuses("GRANT_REPLAY", register.consume, checked["grant"])

    def test_finite_nonzero_sentinel_retains_failure(self):
        checked, context, status, observed = self._execution_context("raise SystemExit(7)")
        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
            error = self.refuses("QUALIFICATION_FAILED", gate.execute, {}, context, self.root,
                         lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
        self.assertEqual(7,error.result['returncode'])
        self.assertEqual(b'',error.result['stdout'])
        self.case_observations.append({'expected_exit':7,'actual_exit':error.result['returncode']})
        self.assertTrue(list(self.root.glob("event-*.json")))

    def test_output_reader_enforces_exact_cap_without_an_extra_process(self):
        for overflow in (False, True):
            read_fd,write_fd=os.pipe();err_read,err_write=os.pipe()
            os.write(write_fd,b'x');os.close(err_write)
            out=os.fdopen(read_fd,'rb',buffering=0);err=os.fdopen(err_read,'rb',buffering=0)
            process=mock.Mock(stdout=out,stderr=err)
            process.poll.return_value=0
            chunks=iter((b'A'*65536,b'A' if overflow else b''))
            real_read=os.read
            def read(fd,count):
                if fd==read_fd:
                    chunk=next(chunks);self.assertLessEqual(len(chunk),count);return chunk
                return real_read(fd,count)
            try:
                with mock.patch.object(gate.os,'read',side_effect=read):
                    if overflow:
                        error=self.refuses('RESULT_LIMIT_EXCEEDED',gate._collect,process,self.checked,
                            lambda:copy.deepcopy(self.status),gate.time.monotonic()+1)
                        self.assertEqual(65536,len(error.output['stdout']))
                        self.assertTrue(error.output['truncated'])
                    else:
                        stdout,stderr=gate._collect(process,self.checked,lambda:copy.deepcopy(self.status),gate.time.monotonic()+1)
                        self.assertEqual(b'A'*65536,stdout);self.assertEqual(b'',stderr)
            finally:
                os.close(write_fd);out.close();err.close()

    def test_observed_revocation_terminates_finite_sentinel(self):
        checked, context, status, observed = self._execution_context("import time; time.sleep(2)")
        calls = 0
        def current():
            nonlocal calls
            calls += 1
            return dict(status, revoked_ids=["grant"] if calls >= 4 else [])
        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
            self.refuses("LEASE_TERMINATED", gate.execute, {}, context, self.root,
                         current, lambda _: copy.deepcopy(observed))

    def test_status_source_change_terminates_even_without_revoked_id(self):
        checked, context, status, observed = self._execution_context("import time; time.sleep(2)")
        calls = 0
        def current():
            nonlocal calls
            calls += 1
            return dict(status, current_decisions_sha256="f" * 64) if calls >= 4 else copy.deepcopy(status)
        with mock.patch.object(gate.verify, "verify_bundle", return_value=checked):
            self.refuses("LEASE_TERMINATED", gate.execute, {}, context, self.root,
                         current, lambda _: copy.deepcopy(observed))

    def test_bounded_network_or_unlisted_exec_request_is_not_admitted(self):
        # This exercises gate admission without issuing a prohibited syscall.
        # The separately reviewed seccomp runner also denies the OS effects.
        spec = importlib.util.spec_from_file_location("runner_policy", Path(__file__).with_name("p08_qualification_runner.py"))
        policy = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(policy)
        self.assertFalse(policy.permitted_argv(["/usr/bin/curl", "https://example.invalid"], "gate"))
        self.assertFalse(policy.permitted_argv(["/usr/bin/python3.14", "-I", "-S", "-B", "-c", "import socket"], "gate"))
        self.assertFalse(policy.permitted_argv(["/usr/bin/codex"], "gate"))
        self.assertFalse(policy.permitted_argv(["/usr/bin/cargo", "test"], "gate"))
        self.assertTrue(policy.permitted_argv(["/usr/bin/python3.14", "-I", "-S", "-B", "-c", "pass"], "gate"))

    def test_full_signed_fixture_executes_only_finite_sentinel(self):
        spec = importlib.util.spec_from_file_location("p08_verify_fixtures", Path(__file__).with_name("test_p08_authority_verify.py"))
        fixture = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(fixture)
        bundle, context = fixture.make_fixture()
        checked = gate.verify.verify_bundle(bundle, context)
        status = context["status"]
        report = checked["action_observation"]
        observed = {key: value for key, value in checked["grant"].items()
                    if key.startswith("observed_") or key in {"grant_id", "run_id", "nonce", "source_commit", "source_tree", "command_profile_sha256", "authorization_scope"}}
        observed.update(evidence_sha256=report["evidence_sha256"], clock_session_id=report["clock_session_id"],
                        monotonic_ns=status["monotonic_ns"])
        # The fixture epoch is an explicit synthetic operator setup, not self-enrollment.
        (self.root / "epoch.json").write_bytes(gate.verify.canonical({"epoch": checked["grant"]["trust_epoch"]}))
        result = gate.execute(bundle, context, self.root, lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
        self.assertEqual("COMPLETED", result["state"])
        self.assertEqual(0, result["returncode"])
        self.case_observations.append({'expected':'COMPLETED_ONCE_EXIT_0','actual':result['state']+'_ONCE_EXIT_'+str(result['returncode'])})
        self.refuses("GRANT_REPLAY", gate.execute, bundle, context, self.root,
                     lambda: copy.deepcopy(status), lambda _: copy.deepcopy(observed))
