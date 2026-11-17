"""Execute only the actual patched, pinned standalone Codex app-server."""
import fcntl
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest

BINARY = Path(os.environ['PINNED_CODEX_BINARY']).resolve()
ROOT = Path(__file__).resolve().parents[2] / 'pilot_c02'
BINDING = 'a' * 64
ATTEMPT = 'pinned-codex-existing-attempt'
MATERIAL = 'SYNTHETIC-NONLIVE-' + '0' * 32

# This launcher transfers only a sealed nonsecret manifest. Synthetic material
# is supplied by the isolated test environment; bootstrap tests use the native
# materialization owner instead. No owner environment or credential store is read.
LAUNCH = r'''
import os,sys,ctypes
fd=int(sys.argv[1]);binary=sys.argv[2]
if fd != 4:
 os.dup2(fd,4,inheritable=True);os.close(fd)
else:os.set_inheritable(4,True)
extra=os.environ.pop('TEST_EXTRA_FD','')
if extra:
 other=os.open('/dev/null',os.O_RDONLY)
 os.dup2(other,int(extra),inheritable=True)
 if other != int(extra):os.close(other)
if os.environ.pop('TEST_DENY_SECCOMP',''):
 class F(ctypes.Structure):_fields_=[('code',ctypes.c_ushort),('jt',ctypes.c_ubyte),('jf',ctypes.c_ubyte),('k',ctypes.c_uint)]
 class P(ctypes.Structure):_fields_=[('len',ctypes.c_ushort),('filter',ctypes.POINTER(F))]
 instructions=(F*7)(F(0x20,0,0,0),F(0x15,0,4,157),F(0x20,0,0,16),F(0x15,0,2,22),F(0x06,0,0,0x50001),F(0x06,0,0,0x7fff0000),F(0x06,0,0,0x7fff0000))
 program=P(7,instructions);libc=ctypes.CDLL(None)
 assert libc.prctl(38,1,0,0,0)==0 and libc.prctl(22,2,ctypes.byref(program),0,0)==0
os.execve(binary,[binary,*sys.argv[3:]],dict(os.environ))
'''


class ActualCodexHolderTest(unittest.TestCase):
    def direct(self, requests=(), change=None, sealed=True, extra=(), deny=False, extra_fd=None):
        with tempfile.TemporaryDirectory(prefix='pinned-codex-direct-') as scratch:
            root = Path(scratch)
            for name in ['home', 'codex-home']:
                (root / name).mkdir(mode=0o700)
            # Deliberately invalid config proves protected startup never loads it.
            # The home must be fresh, so put the poisoned config outside both homes.
            poisoned = root / 'managed-config.toml'
            poisoned.write_text('this is not valid TOML = [')
            manifest = dict(schema=1, profile='C02_PINNED_CODEX_SYNTHETIC_V1', binding=BINDING,
                            attempt=ATTEMPT, holder_sha256=hashlib.sha256(BINARY.read_bytes()).hexdigest(),
                            deadline_ms=int(time.monotonic() * 1000) + 4000, fault='none')
            if change:
                manifest.update(change)
            fd = os.memfd_create('nonsecret-codex-test-manifest', os.MFD_ALLOW_SEALING)
            try:
                os.write(fd, json.dumps(manifest).encode())
                os.lseek(fd, 0, os.SEEK_SET)
                if sealed:
                    fcntl.fcntl(fd, fcntl.F_ADD_SEALS, fcntl.F_SEAL_WRITE | fcntl.F_SEAL_GROW | fcntl.F_SEAL_SHRINK | fcntl.F_SEAL_SEAL)
                env = {'HOME': str(root / 'home'), 'CODEX_HOME': str(root / 'codex-home'), 'LANG': 'C.UTF-8',
                       'ACCESS_TOKEN': MATERIAL, 'CODEX_APP_SERVER_MANAGED_CONFIG_PATH': str(poisoned)}
                if extra_fd:
                    env['TEST_EXTRA_FD'] = str(extra_fd)
                if deny:
                    env['TEST_DENY_SECCOMP'] = '1'
                proc = subprocess.run(['/usr/bin/python3', '-I', '-c', LAUNCH, str(fd), str(BINARY),
                                       '--symphony-pilot-holder', BINDING, ATTEMPT, *extra],
                                      input=''.join(json.dumps(x) + '\n' for x in requests),
                                      capture_output=True, text=True, timeout=7, pass_fds=(fd,), env=env)
            finally:
                os.close(fd)
            self.assertNotIn(MATERIAL, proc.stdout + proc.stderr)
            self.assertNotIn('ACCESS_TOKEN=', proc.stdout + proc.stderr)
            self.assertEqual(list((root / 'home').iterdir()), [])
            self.assertEqual(list((root / 'codex-home').iterdir()), [])
            return proc

    @staticmethod
    def initialize():
        return {'id': 1, 'method': 'initialize', 'params': {'clientInfo': {'name': 'symphony-native-test', 'version': '1'}}}

    def native(self, fault='none', duration=5000):
        with tempfile.TemporaryDirectory(prefix='pinned-codex-bootstrap-') as scratch:
            proc = subprocess.run(['/usr/bin/python3', '-I', str(ROOT / 'tests/run_attempt.py'), '--root', scratch,
                                   '--binding', BINDING, '--attempt', ATTEMPT, '--holder', str(BINARY),
                                   '--pinned-codex', '--fault', fault, '--duration-ms', str(duration)],
                                  capture_output=True, text=True, timeout=12, env={'PATH': '/usr/bin:/bin', 'LANG': 'C.UTF-8'})
            self.assertEqual(proc.returncode, 0, proc.stdout + proc.stderr)
            record = json.loads(proc.stdout)
            journal = (Path(scratch) / 'events.jsonl').read_text()
            self.assertNotIn('SYNTHETIC-NONLIVE-', journal + proc.stdout + proc.stderr)
            if fault != 'missing_permit':
                self.assertTrue(record['replay_refused'])
            record['states'] = [x['state'] for x in map(json.loads, journal.splitlines())]
            return record

    def test_actual_app_server_enters_protected_path_and_uses_pinned_protocol(self):
        proc = self.direct([self.initialize(), {'id': 2, 'method': 'thread/start', 'params': {}}])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        ready, initialize, refusal = map(json.loads, proc.stdout.splitlines())
        self.assertEqual(ready['version'], '0.162.1')
        self.assertTrue(ready['controls']['protected_codex_entry'])
        self.assertTrue(ready['controls']['tokio_thread'])
        for name in ['fork_denied', 'exec_denied', 'ptrace_denied', 'inet_socket_denied', 'process_clone_denied', 'credential_fds_absent']:
            self.assertTrue(ready['controls'][name])
        self.assertIn('codex-app-server/0.162.1', initialize['result']['userAgent'])
        self.assertEqual(refusal['error']['message'], 'SYMPHONY_HOST_UNQUALIFIED')
        self.assertFalse(ready['qualified_host'])

    def test_unsealed_or_incorrect_manifest_refuses_before_readiness(self):
        for change, sealed in [(None, False), ({'holder_sha256': '0' * 64}, True),
                               ({'binding': 'b' * 64}, True), ({'attempt': 'wrong-attempt'}, True),
                               ({'extra': 'unauthorized'}, True), ({'deadline_ms': 1}, True)]:
            with self.subTest(change=change, sealed=sealed):
                proc = self.direct(change=change, sealed=sealed)
                self.assertEqual(proc.returncode, 78)
                self.assertEqual(proc.stdout, '')
                self.assertIn('SYMPHONY_', proc.stderr)

    def test_unavailable_kernel_control_refuses_before_readiness(self):
        proc = self.direct(deny=True)
        self.assertEqual(proc.returncode, 78)
        self.assertEqual(proc.stdout, '')
        self.assertIn('SYMPHONY_SECCOMP_REFUSED', proc.stderr)

    def test_selected_mode_never_falls_back_to_generic_cli_configuration(self):
        proc = self.direct(extra=['--listen', 'stdio://'])
        self.assertEqual(proc.returncode, 78)
        self.assertEqual(proc.stdout, '')
        self.assertIn('SYMPHONY_LAUNCH_FORM_REFUSED', proc.stderr)

    def test_process_tool_auth_config_and_turn_rpcs_cannot_execute(self):
        for method in ['process/spawn', 'command/exec', 'thread/shellCommand', 'mcpServer/add',
                       'account/login/start', 'config/value/write', 'turn/start', 'agent/spawn']:
            with self.subTest(method=method):
                proc = self.direct([self.initialize(), {'id': 2, 'method': method, 'params': {'command': 'unauthorized'}}])
                self.assertEqual(proc.returncode, 0, proc.stderr)
                result = json.loads(proc.stdout.splitlines()[-1])
                self.assertEqual(result, {'error': {'code': -32091, 'message': 'SYMPHONY_HOST_UNQUALIFIED'}, 'id': 2})

    def test_sensitive_request_is_not_reflected_or_persisted(self):
        proc = self.direct([self.initialize(), {'id': 2, 'method': 'turn/start', 'params': {'token': MATERIAL}}])
        self.assertEqual(proc.returncode, 0, proc.stderr)
        self.assertEqual(json.loads(proc.stdout.splitlines()[-1])['error']['message'], 'SYMPHONY_HOST_UNQUALIFIED')

    def test_unapproved_inherited_descriptors_refuse_before_readiness(self):
        for descriptor in [5, 1200]:
            with self.subTest(descriptor=descriptor):
                proc = self.direct(extra_fd=descriptor)
                self.assertEqual(proc.returncode, 78)
                self.assertEqual(proc.stdout, '')
                self.assertIn('SYMPHONY_DESCRIPTOR_REFUSED', proc.stderr)

    def test_native_bootstrap_executes_actual_codex_and_independently_stops(self):
        result = self.native()
        self.assertTrue(result['native_exec'])
        self.assertTrue(result['controls']['protected_codex_entry'])
        self.assertTrue(result['controls']['tokio_thread'])
        self.assertIn('CODEX_INITIALIZED_NOT_AUTHENTICATED', result['states'])
        self.assertTrue(result['stop_verified'])
        self.assertEqual(result['materialization_count'], 1)
        self.assertEqual(result['disposition'], 'CONTROLLED_REFUSAL')
        self.assertFalse(result['inference_succeeded'])

    def test_bootstrap_identity_and_manifest_refusals_are_terminal(self):
        for fault in ['missing_permit', 'bootstrap_failure', 'substituted_holder', 'wrong_attempt', 'manifest_unsealed',
                      'manifest_wrong_identity', 'manifest_wrong_binding', 'controls_unavailable']:
            with self.subTest(fault=fault):
                result = self.native(fault)
                self.assertFalse(result['native_exec'])
                self.assertNotEqual(result['disposition'], 'CONTROLLED_REFUSAL')

    def test_deadline_loss_and_ambiguous_cleanup_never_retry(self):
        for fault in ['continuous', 'launcher_loss', 'parent_loss', 'ambiguous_provider', 'cleanup_failure', 'observe_failure', 'after_materialization']:
            with self.subTest(fault=fault):
                result = self.native(fault, 3000)
                self.assertEqual(result['disposition'], 'QUARANTINED')
                self.assertTrue(result['consumed'])
                self.assertFalse(result['inference_succeeded'])

    def test_ordinary_version_path_is_unchanged(self):
        with tempfile.TemporaryDirectory(prefix='codex-version-only-') as root:
            proc = subprocess.run([str(BINARY), '--version'], capture_output=True, text=True, timeout=5,
                                  env={'HOME': root, 'CODEX_HOME': root, 'LANG': 'C.UTF-8'})
            self.assertEqual(proc.returncode, 0, proc.stderr)
            self.assertIn('0.162.1', proc.stdout)
            self.assertNotIn('SYMPHONY_', proc.stdout + proc.stderr)

if __name__ == '__main__':
    unittest.main(verbosity=2)
