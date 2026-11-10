"""Unprivileged real storage tests, no claim of host custody."""
import importlib.util
from pathlib import Path
import sys
import sqlite3
import tempfile
import threading
import unittest

ROOT = Path(__file__).resolve().parents[1]


class LedgerTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'src/ledger.py';self.assertTrue(path.is_file(), 'D03A durable register is absent')
        sys.path.insert(0, str(ROOT / 'src'))
        import ledger
        from custody_fixture import storage
        self.m = storage
        self.temp = tempfile.TemporaryDirectory(dir=ROOT / 'scratch');self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / 'state.sqlite3'

    def release(self, attempt='2' * 32, slot=1):
        return {'attempt_id': attempt, 'release_id': '3' * 32, 'nonce': '4' * 64, 'slot': slot}

    def consumed(self, ledger):
        value = self.release();ledger.request(value)
        ledger.advance(value['attempt_id'], 'ISSUED');ledger.advance(value['attempt_id'], 'VERIFIED')
        ledger.consume(value['attempt_id']);return value['attempt_id']

    def test_consume_is_durable_and_replay_cannot_launch(self):
        with self.m.Register(self.path) as ledger:
            attempt = self.consumed(ledger)
            with self.assertRaises(self.m.Refusal):ledger.consume(attempt)
        with self.m.Register(self.path) as ledger:
            self.assertEqual('CONSUMED', ledger.get(attempt)['state'])

    def test_consume_requires_verified(self):
        with self.m.Register(self.path) as ledger:
            value=self.release();ledger.request(value)
            with self.assertRaises(self.m.Refusal):ledger.consume(value['attempt_id'])

    def test_consumption_history_has_no_missing_transition(self):
        with self.m.Register(self.path) as ledger:
            attempt=self.consumed(ledger)
            self.assertEqual(['REQUESTED','ISSUED','VERIFIED','RELEASED','CONSUMED'],ledger.history(attempt))

    def test_slot_nonce_and_release_are_not_transferable(self):
        for field in ['slot','nonce','release_id']:
            path=Path(self.temp.name)/(field+'.sqlite3')
            with self.m.Register(path) as ledger:
                self.consumed(ledger)
                value=self.release('5'*32,2)
                value['release_id']='6'*32;value['nonce']='7'*64;value[field]=self.release()[field]
                with self.assertRaises(self.m.Refusal):
                    ledger.request(value);ledger.advance(value['attempt_id'],'ISSUED');ledger.advance(value['attempt_id'],'VERIFIED')
                    ledger.consume(value['attempt_id'])

    def test_restart_preserves_tombstone_and_interrupts_execution(self):
        with self.m.Register(self.path) as ledger:attempt=self.consumed(ledger)
        with self.m.Register(self.path) as ledger:
            ledger.reconcile(lambda row: {'host_observation':'NO_WORKER_STARTED'})
            self.assertEqual('CONSUMED',ledger.get(attempt)['state'])
            self.assertEqual('INTERRUPTED',ledger.get(attempt)['execution'])

    def test_ambiguous_recovery_stops_without_restoring_entitlement(self):
        with self.m.Register(self.path) as ledger:
            attempt=self.consumed(ledger)
            def uncertain(row):raise self.m.Refusal('RECOVERY_UNCERTAIN')
            with self.assertRaises(self.m.Refusal):ledger.reconcile(uncertain)
            with self.assertRaises(self.m.Refusal):ledger.consume(attempt)

    def test_partial_unconsumed_history_is_rejected_on_recovery(self):
        with self.m.Register(self.path) as ledger:
            value=self.release();ledger.request(value);ledger.advance(value['attempt_id'],'ISSUED')
            ledger.reconcile(lambda row: {})
            self.assertEqual('REJECTED',ledger.get(value['attempt_id'])['state'])

    def test_revoked_and_expired_attempts_stay_terminal(self):
        for state in ['EXPIRED','REVOKED','REJECTED']:
            with self.m.Register(Path(self.temp.name)/(state+'.sqlite3')) as ledger:
                value=self.release();ledger.request(value);ledger.advance(value['attempt_id'],state)
                with self.assertRaises(self.m.Refusal):ledger.advance(value['attempt_id'],'ISSUED')

    def test_concurrent_consumers_have_one_winner(self):
        with self.m.Register(self.path) as ledger:
            value=self.release();ledger.request(value);ledger.advance(value['attempt_id'],'ISSUED');ledger.advance(value['attempt_id'],'VERIFIED')
        barrier=threading.Barrier(2);results=[]
        def consume():
            with self.m.Register(self.path) as ledger:
                barrier.wait(timeout=3)
                try:ledger.consume(value['attempt_id']);results.append('CONSUMED')
                except self.m.Refusal:results.append('REFUSED')
        threads=[threading.Thread(target=consume) for unused in range(2)]
        for thread in threads:thread.start()
        for thread in threads:thread.join(5)
        self.assertTrue(all(not thread.is_alive() for thread in threads));self.assertEqual(['CONSUMED','REFUSED'],sorted(results))

    def test_corrupt_register_is_never_reset(self):
        self.path.write_bytes(b'broken database')
        with self.assertRaises(self.m.Refusal):self.m.Register(self.path)
        self.assertEqual(b'broken database',self.path.read_bytes())

    def test_failed_requested_slot_is_not_reallocated(self):
        with self.m.Register(self.path) as ledger:
            value=self.release();ledger.request(value);ledger.advance(value['attempt_id'],'REJECTED')
            with self.assertRaises(self.m.Refusal):ledger.request(self.release('8'*32))

    def test_missing_consumption_marker_refuses_reopen(self):
        with self.m.Register(self.path) as ledger:self.consumed(ledger)
        with sqlite3.connect(self.path) as database:database.execute('DELETE FROM used')
        with self.assertRaises(self.m.Refusal):self.m.Register(self.path)

    def test_missing_history_refuses_with_typed_uncertainty(self):
        with self.m.Register(self.path) as ledger:self.consumed(ledger)
        with sqlite3.connect(self.path) as database:database.execute('DELETE FROM events')
        try:self.m.Register(self.path)
        except Exception as error:self.assertIsInstance(error,self.m.Refusal)
        else:self.fail('missing history accepted')


if __name__ == '__main__':unittest.main(verbosity=2)
