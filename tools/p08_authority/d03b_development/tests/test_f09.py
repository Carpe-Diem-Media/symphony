"""Disposable authenticated-custody components, never current-host qualification."""
import importlib.util
import unittest
from pathlib import Path
import os
import sqlite3
import tempfile
import subprocess
import sys
from unittest.mock import patch

import contract as c
import ledger
from f09_fixture import Fixture


class F09AvailabilityTests(unittest.TestCase):
    def test_authenticated_host_component_exists_without_enabling_live_register(self):
        root = Path(__file__).resolve().parents[1]
        self.assertTrue((root / 'src/custody.py').is_file(),
                        'F09 authenticated host custody component is missing')
        import ledger
        with self.assertRaisesRegex(ledger.Refusal, 'REGISTER_CUSTODY_UNCONFIGURED'):
            ledger.Register(root / 'scratch/not-enrolled.sqlite3')


class AuthenticatedCustodyTests(unittest.TestCase):
    def setUp(self):
        root = Path(__file__).resolve().parents[1]
        self.temp = tempfile.TemporaryDirectory(dir=root / 'scratch')
        self.addCleanup(self.temp.cleanup)
        self.f = Fixture(Path(self.temp.name) / 'host')
        self.path = self.f.root / 'state/register.sqlite3'

    def reopen(self):
        return ledger._RegisterStore(self.path, self.f.custody())

    def refuses(self, operation, *args):
        with self.assertRaises(c.Refusal):
            operation(*args)

    def test_valid_enrollment_restart_and_consumption(self):
        with self.f.enroll() as reg:
            release = self.f.consumed(reg)
        with self.reopen() as reg:
            self.assertEqual('CONSUMED', reg.get(release['attempt_id'])['state'])
            self.refuses(reg.consume, release['attempt_id'])
        with self.reopen() as reg:
            self.assertEqual(1, len(reg.rows()))

    def test_unauthorized_and_duplicate_enrollment(self):
        self.f.sign_enrollment(rogue=True)
        self.refuses(self.f.custody)
        self.assertEqual(b'', (self.f.root / 'authority/anchor').read_bytes())
        self.f.sign_enrollment()
        self.f.enroll().close()
        self.refuses(self.f.custody().enroll)

    def test_invalid_bootstrap_and_missing_register_never_initialize(self):
        a = self.f.custody()
        self.refuses(ledger._RegisterStore.initialize, self.path, a, True)
        self.f.enroll().close()
        self.path.unlink()
        self.refuses(self.reopen)
        self.assertFalse(self.path.exists())
        self.refuses(a.enroll)

    def test_old_database_current_checkpoint(self):
        reg = self.f.enroll(); old = self.path.read_bytes()
        self.f.consumed(reg); reg.close()
        self.path.write_bytes(old)
        self.refuses(self.reopen)

    def test_old_checkpoint_current_database(self):
        reg = self.f.enroll(); saved = self.saved_receipt()
        self.f.consumed(reg); reg.close()
        self.restore_receipt(saved)
        self.refuses(self.reopen)

    def saved_receipt(self):
        return {name: (self.f.root / 'authority' / name).read_bytes()
                for name in ['receipt', 'receipt.sig']}

    def restore_receipt(self, saved):
        for name, raw in saved.items():
            (self.f.root / 'authority' / name).write_bytes(raw)

    def test_entire_database_checkpoint_rollback_refuses_against_host_witness(self):
        reg = self.f.enroll(); saved = self.saved_receipt(); old = self.path.read_bytes()
        self.f.consumed(reg); reg.close()
        self.path.write_bytes(old); self.restore_receipt(saved)
        self.refuses(self.reopen)

    def test_changed_register_identity(self):
        self.f.enroll().close()
        other = self.path.with_name('replacement')
        other.write_bytes(self.path.read_bytes()); other.chmod(0o600); other.replace(self.path)
        self.refuses(self.reopen)

    def test_missing_or_malformed_receipt(self):
        self.f.enroll().close()
        (self.f.root / 'authority/receipt').unlink()
        self.refuses(self.reopen)
        (self.f.root / 'authority/receipt').write_bytes(b'{}')
        self.refuses(self.reopen)

    def test_signature_and_enrollment_identity_mismatch(self):
        self.f.enroll().close()
        self.f.enrollment['enrollment_id'] = 'c' * 64
        self.f.sign_enrollment()
        self.refuses(self.reopen)

    def test_bootstrap_partial_initialization_cannot_rearm(self):
        a = self.f.custody(); grant = a.enroll()
        with patch.object(a, 'activate', side_effect=c.Refusal('FAULT_AFTER_SQL_BOOTSTRAP')):
            self.refuses(ledger._RegisterStore.initialize, self.path, a, grant)
        self.refuses(self.reopen)
        self.refuses(a.enroll)

    def test_before_reservation_has_no_sql_effect(self):
        with self.f.enroll() as reg:
            with patch.object(reg.custody, 'reserve', side_effect=c.Refusal('FAULT_BEFORE_RESERVATION')):
                with self.assertRaisesRegex(c.Refusal, '^FAULT_BEFORE_RESERVATION$'):
                    reg.request(self.f.release())
            self.assertEqual([], reg.rows())
        with self.reopen() as reg:
            self.assertEqual([], reg.rows())

    def test_before_sql_commit_leaves_interrupted_authority(self):
        with self.f.enroll() as reg:
            with patch.object(reg.custody, 'prepare', side_effect=c.Refusal('FAULT_BEFORE_COMMIT')):
                self.refuses(reg.request, self.f.release())
            self.assertEqual([], reg.rows())
        self.refuses(self.reopen)

    def test_after_sql_commit_before_ack_cannot_retry(self):
        with self.f.enroll() as reg:
            r = self.f.release(); reg.request(r)
            reg.advance(r['attempt_id'], 'ISSUED'); reg.advance(r['attempt_id'], 'VERIFIED')
            with patch.object(reg.custody, 'complete', side_effect=c.Refusal('FAULT_AFTER_COMMIT')):
                self.refuses(reg.consume, r['attempt_id'])
            self.assertEqual('CONSUMED', reg.get(r['attempt_id'])['state'])
            self.refuses(reg.consume, r['attempt_id'])
        self.refuses(self.reopen)

    def test_lost_receipt_after_witness_commit(self):
        import custody
        with self.f.enroll() as reg:
            with patch.object(reg.custody, '_publish', side_effect=c.Refusal('LOST_RECEIPT')):
                self.refuses(reg.request, self.f.release())
        self.refuses(self.reopen)

    def test_revoked_and_expired_release_never_consumed(self):
        with self.f.enroll() as reg:
            r = self.f.release(); reg.request(r); reg.advance(r['attempt_id'], 'REVOKED')
            self.refuses(reg.consume, r['attempt_id'])
            expired = self.f.release(attempt_id='5' * 32, release_id='6' * 32, nonce='7' * 64,
                slot=2, issued_at=1, not_before=1, expires_at=2)
            self.refuses(reg.request, expired)
            self.assertEqual(0, reg.db.execute('SELECT count(*) FROM used').fetchone()[0])

    def test_each_stale_source_worker_binding_refuses(self):
        with self.f.enroll() as reg:
            for key in c.BINDINGS:
                self.refuses(reg.request, self.f.release(**{key: 'wrong'}))
            self.assertEqual([], reg.rows())

    def test_routine_rejected_inputs_do_not_consume_witness_capacity(self):
        with self.f.enroll() as reg:
            r = self.f.consumed(reg)
            anchor = self.f.root / 'authority/anchor'
            before = anchor.read_bytes()
            for _ in range(3):
                self.refuses(reg.request, self.f.release(worker_runtime_sha256='wrong'))
                self.refuses(reg.request, r)
                self.refuses(reg.consume, r['attempt_id'])
            self.assertEqual(before, anchor.read_bytes())

    def test_replayed_attempt_release_nonce_and_slot(self):
        with self.f.enroll() as reg:
            r = self.f.consumed(reg)
            self.refuses(reg.request, r)
            self.refuses(reg.request, r | {'attempt_id': '5' * 32})
            for index, change in enumerate([{'release_id': r['release_id']}, {'nonce': r['nonce']}], 2):
                other = self.f.release(attempt_id=str(index+3) * 32, release_id='6' * 32, nonce='7' * 64, slot=index) | change
                reg.request(other); reg.advance(other['attempt_id'], 'ISSUED'); reg.advance(other['attempt_id'], 'VERIFIED')
                self.refuses(reg.consume, other['attempt_id'])

    def test_custodian_unavailable_and_deadline(self):
        self.f.enroll().close()
        import custody
        import subprocess
        with patch.object(custody.subprocess, 'run', side_effect=subprocess.TimeoutExpired('ssh-keygen', 3)):
            self.refuses(self.reopen)

    def test_changed_lock_or_anchor_identity_refuses(self):
        self.f.enroll().close()
        path = self.f.root / 'authority/lock'; other = path.with_name('replacement')
        other.write_bytes(b''); other.chmod(0o600); other.replace(path)
        self.refuses(self.reopen)

    def test_replaced_anchor_and_corrupt_checkpoint_signature_refuse(self):
        self.f.enroll().close()
        path = self.f.root / 'authority/receipt.sig'
        path.write_bytes(b'NOT AN SSH SIGNATURE')
        self.refuses(self.reopen)
        anchor = self.f.root / 'authority/anchor'
        replacement = anchor.with_name('replacement')
        replacement.write_bytes(anchor.read_bytes()); replacement.chmod(0o600); replacement.replace(anchor)
        self.refuses(self.f.custody)

    def test_closed_enrollment_and_external_owner_pin(self):
        import custody
        self.refuses(custody._HostCustody, self.f.root, 'SHA256:wrong', self.f.bindings)
        changed = self.f.bindings | {'worker_runtime_sha256': 'f' * 64}
        self.refuses(custody._HostCustody, self.f.root, self.f.pin, changed)
        self.f.enrollment['approved'] = True
        self.f.sign_enrollment()
        self.refuses(self.f.custody)

    def test_authority_clock_reversal_refuses(self):
        import custody
        self.f.enroll().close()
        with patch.object(custody.time, 'time_ns', return_value=0):
            self.refuses(self.reopen)

    def test_symlink_hardlink_fifo_refuse_without_opening_special_payload(self):
        self.f.enroll().close()
        p = self.f.root / 'authority/receipt'; raw = p.read_bytes(); p.unlink()
        canary = p.with_name('canary'); canary.write_bytes(raw); canary.chmod(0o600)
        for kind in ['symlink', 'hardlink', 'fifo']:
            if kind == 'symlink': p.symlink_to('canary')
            elif kind == 'hardlink': os.link(canary, p)
            else: os.mkfifo(p)
            self.refuses(self.reopen); p.unlink()

    def test_truncating_anchor_cannot_reuse_first_enrollment(self):
        self.f.enroll().close()
        (self.f.root / 'authority/anchor').write_bytes(b'')
        self.refuses(self.f.custody().enroll)

    def test_retired_authority_is_absorbing(self):
        self.f.enroll().close(); a = self.f.custody()
        with a.lock(): a.retire()
        self.refuses(self.reopen); self.refuses(a.enroll)

    def test_active_enrollment_cannot_transition_back_to_bootstrap(self):
        self.f.enroll().close(); a = self.f.custody()
        with a.lock():
            state = a._read()
            self.refuses(a._write, state | {'phase': 'BOOTSTRAP_RESERVED'})
        with self.reopen() as reg:
            self.assertEqual([], reg.rows())

    def test_expired_or_future_enrollment_refuses_before_bootstrap(self):
        import time
        now = int(time.time())
        for start, end in [(now - 100, now), (now + 100, now + 200)]:
            self.f.enrollment.update(not_before=start, expires_at=end)
            self.f.sign_enrollment()
            self.refuses(self.f.custody)
            self.assertFalse(self.path.exists())

    def probe_command(self, mode, profile):
        return ['/usr/bin/python3.14', '-I', '-S', '-B',
            str(Path(__file__).with_name('f09_process_probe.py')), mode, str(profile)]

    def verified_profile(self):
        with self.f.enroll() as reg:
            r = self.f.release(); reg.request(r)
            reg.advance(r['attempt_id'], 'ISSUED'); reg.advance(r['attempt_id'], 'VERIFIED')
        profile = self.f.root / 'probe.json'
        profile.write_bytes(c.canonical({'root': str(self.f.root), 'pin': self.f.pin,
            'bindings': self.f.bindings, 'attempt': r['attempt_id']}))
        return profile, r

    def crash(self, mode, code, blocked):
        profile, r = self.verified_profile()
        p = subprocess.Popen(self.probe_command(mode, profile), stdout=subprocess.PIPE,
                             stderr=subprocess.PIPE, env={'PATH': '/nonexistent'}, close_fds=True)
        try: out, err = p.communicate(timeout=8)
        finally:
            if p.poll() is None: p.kill(); p.wait(timeout=2)
        self.assertEqual(code, p.returncode, (out, err))
        with self.assertRaises(ChildProcessError): os.waitpid(p.pid, os.WNOHANG)
        print('CRASH_PROBE', mode, 'pid', p.pid, 'exit', p.returncode, 'reaped')
        if blocked:
            self.refuses(self.reopen)
        else:
            with self.reopen() as reg:
                expected = 'CONSUMED' if mode == 'after_ack' else 'VERIFIED'
                self.assertEqual(expected, reg.get(r['attempt_id'])['state'])
                if mode == 'after_ack': self.refuses(reg.consume, r['attempt_id'])

    def test_process_death_before_reservation_has_no_consume_effect(self):
        self.crash('before_reserve', 71, False)

    def test_process_death_after_reservation_never_rearms(self):
        self.crash('after_reserve', 72, True)

    def test_process_death_after_prepare_before_sql_commit_never_rearms(self):
        self.crash('after_prepare', 73, True)

    def test_process_death_after_sql_commit_before_ack_never_rearms(self):
        self.crash('after_commit', 74, True)

    def test_process_death_after_ack_preserves_consumption(self):
        self.crash('after_ack', 75, False)

    def test_concurrent_process_duplicates_have_at_most_one_consumer(self):
        profile, r = self.verified_profile()
        children = []
        try:
            for _ in range(2):
                children.append(subprocess.Popen(self.probe_command('consume', profile),
                    stdout=subprocess.PIPE, stderr=subprocess.PIPE, env={'PATH': '/nonexistent'}, close_fds=True))
            results = [p.communicate(timeout=8) for p in children]
            codes = [p.returncode for p in children]
            self.assertEqual([0, 2], sorted(codes), results)
            for p in children:
                with self.assertRaises(ChildProcessError): os.waitpid(p.pid, os.WNOHANG)
            print('CONCURRENT_PROBES', [(p.pid, p.returncode) for p in children], results, 'reaped')
            with self.reopen() as reg:
                self.assertEqual('CONSUMED', reg.get(r['attempt_id'])['state'])
                self.assertEqual(1, reg.db.execute('SELECT count(*) FROM used').fetchone()[0])
        finally:
            for p in children:
                if p.poll() is None: p.kill(); p.wait(timeout=2)

    def test_no_operational_custody_selection_or_network_effect(self):
        import socket
        self.assertFalse(hasattr(ledger.HostRegisterCustody, 'register_provider'))
        with patch.dict(os.environ, {'P08_CUSTODY_APPROVED': 'true', 'P08_TRUST_ANCHOR': str(self.f.root)}):
            self.refuses(ledger.Register, self.path)
        with self.assertRaises(PermissionError): socket.socket()

    def test_crypto_operations_cannot_select_arbitrary_signing_scope(self):
        import custody
        self.f.enroll().close(); a = self.f.custody()
        self.refuses(a._crypto, ['-Y', 'sign'], b'arbitrary')
        with a.lock():
            self.refuses(a._crypto, custody._SignatureOperation.SIGN_CHECKPOINT,
                         c.canonical({'approved': True}))
