"""Actual protected app-server admission for the Slice B broker diagnostic."""
import base64
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import select
import subprocess
import sys
import tempfile
import time
import unittest

from test_functional_session import BINARY, GIT_ENV, HERE, canonical, context_for, digest

EXEC_WITH_PIPES = """
import fcntl, os, sys
sources = [fcntl.fcntl(int(fd), fcntl.F_DUPFD_CLOEXEC, 10) for fd in sys.argv[1:4]]
for index, fd in enumerate(sources, 4):
    os.dup2(fd, index, inheritable=True)
os.closerange(7, 1048576)
os.execv(sys.argv[4], sys.argv[4:])
"""


def native_driver():
    native_path = HERE.parents[1] / 'pilot_c02/tests/run_attempt.py'
    spec = importlib.util.spec_from_file_location('broker_native', native_path)
    native = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(native)
    return native


def read_bounded(stream, byte_count, deadline):
    output = bytearray()
    while len(output) < byte_count:
        if not select.select([stream], [], [], max(0, deadline - time.monotonic()))[0]:
            break
        chunk = stream.read(byte_count - len(output))
        if not chunk:
            break
        output.extend(chunk)
    return bytes(output)


class BrokerDiagnosticTest(unittest.TestCase):
    def native(self, mode):
        native = native_driver()
        parent = os.environ.get('SYMPHONY_SLICE_B_EVIDENCE')
        if parent:
            Path(parent).mkdir(parents=True, exist_ok=True)
        with tempfile.TemporaryDirectory(prefix='actual-broker-') as scratch:
            root = Path(scratch)
            manifest = context_for(root, BINARY, time.monotonic() + 5)
            try:
                outcome = native.run(root, manifest['binding'], manifest['attempt'], 'none', 5000,
                                     BINARY, True, schema2_manifest=manifest, broker_selftest=mode)
                native.sync_private_file(root / 'result.json', canonical(outcome))
                if mode == 'observe_helper_loss':
                    self.assertTrue(outcome['helper_loss_observed'], outcome)
                    self.assertEqual(outcome['disposition'], 'QUARANTINED', outcome)
                    self.assertTrue(outcome['consumed'])
                    self.assertTrue(outcome['replay_refused'])
                    self.assertIsNone(outcome['broker_result'])
                    states = [json.loads(line)['state'] for line in
                              (root / 'broker-events.jsonl').read_text().splitlines()]
                    self.assertEqual(states.count('START_INTENT_DURABLE'), 1)
                    self.assertNotIn('STOP_VERIFIED', states)
                    return
                self.assertEqual(outcome['disposition'], 'BROKER_SELFTEST_STOPPED', outcome)
                self.assertTrue(outcome['stop_verified'])
                self.assertTrue(outcome['native_disposal_verified'])
                self.assertTrue(outcome['replay_refused'])
                self.assertTrue(outcome['consumed'])
                self.assertEqual(outcome['materialization_count'], 1)
                self.assertFalse(outcome['inference_succeeded'])
                self.assertFalse(outcome['qualified_host'])
                report = outcome['broker_result']
                self.assertEqual(report.get('route'), 'selected_exec_command')
                self.assertTrue(report['other_tool_refused'])
                self.assertTrue(report['wrong_arguments_refused'])
                self.assertTrue(report['wrong_call_id_refused'])
                self.assertTrue(report['duplicate_refused'])
                self.assertEqual(mode == 'wait_for_stop', report['cancelled'])
                stdout = base64.b64decode(report['stdout'], validate=True)
                self.assertEqual(report['stdout_sha256'], digest(stdout))
                self.assertEqual(base64.b64decode(report['stderr'], validate=True), b'')
                if mode == 'run':
                    self.assertEqual(report['exit_status'], 0)
                    self.assertEqual(stdout, (root / 'workspace/planner_input.txt').read_bytes())
                else:
                    self.assertNotEqual(report['exit_status'], 0)
                    self.assertEqual(stdout, b'')
                journal = [json.loads(line) for line in (root / 'broker-events.jsonl').read_text().splitlines()]
                states = [event['state'] for event in journal]
                self.assertEqual(states.count('START_INTENT_DURABLE'), 1)
                self.assertEqual(states.count('STARTED'), 1)
                self.assertEqual(states.count('STOP_VERIFIED'), 1)
                self.assertLess(states.index('PERMITTED'), states.index('START_INTENT_DURABLE'))
                self.assertLess(states.index('START_INTENT_DURABLE'), states.index('STARTED'))
                if mode == 'run':
                    self.assertLess(states.index('STARTED'), states.index('OUTPUT_STREAMING'))
                    self.assertLess(states.index('OUTPUT_STREAMING'), states.index('EXIT_OBSERVED'))
                self.assertLess(states.index('EXIT_OBSERVED'), states.index('STOP_VERIFIED'))
            finally:
                if parent:
                    target = Path(tempfile.mkdtemp(prefix=self._testMethodName + '-', dir=parent))
                    for name in ('manifest.json', 'permission', 'events.jsonl', 'broker-events.jsonl',
                                 'broker-permit', 'broker-start-consumed', 'broker-stop-verified', 'result.json'):
                        source = root / name
                        if source.is_file():
                            native.sync_private_file(target / name, source.read_bytes())
                    subprocess.run(['/usr/bin/git', 'bundle', 'create', str(target / 'source.bundle'),
                                    '--all'], cwd=root / 'workspace', env=GIT_ENV, check=True)

    def test_native_broker_reads_exact_input_once(self):
        self.native('run')

    def test_native_broker_stops_a_held_child_before_exec(self):
        self.native('wait_for_stop')

    def test_native_broker_loss_retains_consumption_without_verified_stop(self):
        self.native('observe_helper_loss')

    def test_selected_protected_binary_enters_the_broker(self):
        self.direct_reply_case("eof")

    def test_compiled_backend_rejects_stop_before_exit(self):
        self.direct_reply_case("early_stop")

    def test_compiled_backend_rejects_duplicate_stop_before_eof(self):
        self.direct_reply_case("duplicate_stop")

    def direct_reply_case(self, reply_case):
        with tempfile.TemporaryDirectory(prefix='symphony-broker-test-') as scratch:
            root = Path(scratch)
            for name in ('home', 'codex-home'):
                (root / name).mkdir(mode=0o700)
            manifest = context_for(root, BINARY, time.monotonic() + 5)
            request_read, request_write = os.pipe()
            result_read, result_write = os.pipe()
            manifest_fd = os.memfd_create('symphony-broker-fixture', os.MFD_ALLOW_SEALING)
            proc = None
            with os.fdopen(request_read, 'rb', buffering=0) as requests:
                try:
                    manifest['deadline_ms'] = int((time.monotonic() + 4) * 1000)
                    native = native_driver()
                    native.seal_broker_inputs(
                        root, manifest, (requests.fileno(), request_write, result_read, result_write),
                        native.NATIVE / 'build/tool-broker', 'run')
                    os.write(manifest_fd, canonical(manifest))
                    os.lseek(manifest_fd, 0, os.SEEK_SET)
                    fcntl.fcntl(manifest_fd, fcntl.F_ADD_SEALS, fcntl.F_SEAL_WRITE |
                                fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
                    argv = [sys.executable, '-I', '-c', EXEC_WITH_PIPES, str(manifest_fd),
                            str(request_write), str(result_read), str(BINARY),
                            '--symphony-pilot-holder', manifest['binding'], manifest['attempt']]
                    proc = subprocess.Popen(argv, stdin=subprocess.PIPE,
                                            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                                            pass_fds=(manifest_fd, request_write, result_read),
                                            env={'HOME': str(root / 'home'),
                                                 'CODEX_HOME': str(root / 'codex-home'),
                                                 'LANG': 'C.UTF-8',
                                                 'ACCESS_TOKEN': 'SYNTHETIC-NONLIVE-' + '0' * 32})
                    os.close(request_write)
                    request_write = -1
                    with os.fdopen(os.pidfd_open(proc.pid), 'rb') as pidfd:
                        readable, _, _ = select.select([requests, pidfd], [], [], 5)
                        header = read_bounded(requests, 4, time.monotonic() + 1) if requests in readable else b''
                        payload = b''
                        if len(header) == 4:
                            length = int.from_bytes(header, 'big')
                            self.assertIn(length, range(1, 8193))
                            payload = read_bounded(requests, length, time.monotonic() + 1)
                        if payload and reply_case != "eof":
                            # Negative peer fixture only. No process identity or successful
                            # execution is claimed by these deliberately invalid frames.
                            shared = manifest["context"]["broker_selftest"]["binding"]
                            child = {"pid": 1234, "start_ticks": 5678}

                            def reply(operation, sequence, **fields):
                                raw = canonical(dict(shared, **child, operation=operation,
                                                     sequence=sequence, **fields))
                                return len(raw).to_bytes(4, "big") + raw

                            started = reply("STARTED", 1)
                            if reply_case == "early_stop":
                                os.write(result_write, started + reply("STOP_CONFIRMED", 2))
                            else:
                                os.write(result_write, started + reply("EXIT", 2, exit_code=0))
                                limit = time.monotonic() + 1.5
                                prefix = read_bounded(requests, 4, limit)
                                self.assertEqual(len(prefix), 4, "Holder did not send STOP_REQUEST")
                                size = int.from_bytes(prefix, "big")
                                self.assertIn(size, range(1, 8193))
                                stop = json.loads(read_bounded(requests, size, limit))
                                self.assertEqual(stop, dict(shared, operation="STOP_REQUEST", sequence=2))
                                os.write(result_write, reply("STOP_CONFIRMED", 3) +
                                         reply("STOP_CONFIRMED", 4))
                        os.close(result_write)
                        result_write = -1
                        try:
                            output, errors = proc.communicate(timeout=5)
                        except subprocess.TimeoutExpired:
                            proc.kill()
                            proc.communicate()
                            raise
                        stopped = bool(select.select([pidfd], [], [], 0)[0])
                    refusal = errors.decode('ascii', errors='replace').strip()
                    if not payload:
                        self.fail(f'No broker request. Holder exit={proc.returncode}, '
                                  f'pidfd_stop={stopped}, refusal={refusal}')
                    request = json.loads(payload)
                    self.assertEqual(request['operation'], 'START_READ')
                    self.assertEqual(request['attempt_id'], manifest['attempt'])
                    self.assertTrue(stopped)
                    self.assertEqual(proc.returncode, 78, output)
                    self.assertEqual(refusal, "SYMPHONY_BROKER_REFUSED")
                    self.assertNotIn(b'"status":"stop_verified"', output)
                finally:
                    if proc is not None and proc.poll() is None:
                        proc.kill()
                        proc.communicate(timeout=2)
                    for fd in (request_write, result_read, result_write, manifest_fd):
                        if fd >= 0:
                            os.close(fd)


if __name__ == '__main__':
    unittest.main()
