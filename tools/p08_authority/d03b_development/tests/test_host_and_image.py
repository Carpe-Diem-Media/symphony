"""Unprivileged preparation tests. No systemd launch or key enrollment."""
import base64
import importlib.util
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]


class HostPreparationTests(unittest.TestCase):
    def setUp(self):
        path=ROOT/'src/host.py';self.assertTrue(path.exists(),'trusted host adapter is absent')
        sys.path.insert(0,str(ROOT/'src'))
        import host
        self.h=host
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'scratch');self.addCleanup(self.temp.cleanup)

    def test_live_entry_refuses_nonroot_before_any_write(self):
        command=['/usr/bin/python3.14','-I','-S','-B',str(ROOT/'src/host.py'),'--attempt','2'*32]
        p=subprocess.run(command,capture_output=True,timeout=3,env={'PATH':'/nonexistent'})
        self.assertEqual(2,p.returncode);self.assertEqual(b'HOST_ROOT_REQUIRED\n',p.stderr)

    def test_author_owned_input_is_not_root_custody(self):
        path=Path(self.temp.name)/'approval.json';path.write_bytes(b'{}')
        with self.assertRaises(self.h.Refusal):self.h.root_read(path)

    def test_key_fingerprint_is_derived_from_exact_public_bytes(self):
        raw=(Path('/tmp/symphony-p08-r1b-d02/evidence/131400-d68252be/synthetic-allowed-signers').read_text().split())
        key=' '.join(raw[1:])
        self.assertTrue(self.h.public_fingerprint(key).startswith('SHA256:'))
        for value in ['ssh-rsa AAAA','ssh-ed25519 !!!!',key+' extra']:
            with self.assertRaises(self.h.Refusal):self.h.public_fingerprint(value)

    def test_launch_command_has_fixed_image_unit_and_no_caller_command(self):
        self.assertFalse(hasattr(self.h.Host,'run'))
        self.assertFalse(hasattr(self.h,'launch_argv'))
        self.assertEqual('p08-d03-worker.service',self.h.unit_name('2'*32))
        self.assertEqual(['CREATE','SHOW','STOP','UNREF','CLOSE'],[op.value for op in self.h.NativeOperation])
        with self.assertRaises(self.h.Refusal):self.h.unit_name('../bad')

    def test_installed_route_does_not_accept_an_approval_boolean(self):
        with self.assertRaises(self.h.Refusal):self.h.parse_route_approval(b'{"approved":true}',{},1000)

    def test_retained_synthetic_signature_can_be_verified_as_crypto_only(self):
        run=Path('/tmp/symphony-p08-r1b-d02/evidence/131400-d68252be')
        attempt='12858c43554f78783b6426c3a1fc0f04'
        result=self.h.verify_signature_component(
            Path('/tmp/symphony-p08-r1b-d02/host/requests')/(attempt+'.json'),
            Path('/tmp/symphony-p08-r1b-d02/host/requests')/(attempt+'.sig'),
            run/'synthetic-allowed-signers','d02-synthetic-issuer','symphony.p08.d02.cooperative.v1')
        self.assertEqual(0,result['exit_code'])

    def test_retained_signature_does_not_authorize_d03_namespace(self):
        run=Path('/tmp/symphony-p08-r1b-d02/evidence/131400-d68252be');attempt='12858c43554f78783b6426c3a1fc0f04'
        result=self.h.verify_signature_component(Path('/tmp/symphony-p08-r1b-d02/host/requests')/(attempt+'.json'),
            Path('/tmp/symphony-p08-r1b-d02/host/requests')/(attempt+'.sig'),run/'synthetic-allowed-signers',
            'd02-synthetic-issuer',self.h.NAMESPACE)
        self.assertNotEqual(0,result['exit_code'])

    def test_worker_entry_refuses_unrestricted_account(self):
        p=subprocess.run(['/usr/bin/python3.14','-I','-S','-B',str(ROOT/'src/worker.py'),'--attempt','2'*32],capture_output=True,timeout=3,env={'PATH':'/nonexistent'})
        self.assertEqual(2,p.returncode);self.assertEqual(b'WORKER_IDENTITY_UNPROVEN\n',p.stderr)

    def test_launch_before_invocation_persistence_has_guarded_recovery(self):
        token='7'*64;attempt='2'*32
        row={'attempt':attempt,'execution':'LAUNCHING','detail':json.dumps({'launch_token':token})}
        props={'Id':self.h.unit_name(attempt),'Description':'p08-d03:'+attempt+':'+token,
            'InvocationID':'3'*32,'Transient':'yes','RootDirectory':str(self.h.DEPLOYMENT/'image'),
            'ControlGroup':'/system.slice/'+self.h.unit_name(attempt),'LoadState':'loaded'}
        self.assertTrue(hasattr(self.h,'recovery_disposition'),'guarded crash recovery is absent')
        self.assertEqual('STOP_MATCHED_UNIT',self.h.recovery_disposition(row,props,True))
        with self.assertRaises(self.h.Refusal):self.h.recovery_disposition(row,props|{'Description':'foreign'},True)

    def test_missing_unit_requires_cgroup_absence_for_recovery(self):
        self.assertTrue(hasattr(self.h,'recovery_disposition'),'guarded crash recovery is absent')
        row={'attempt':'2'*32,'execution':'LAUNCHING','detail':json.dumps({'launch_token':'7'*64})}
        self.assertEqual('UNIT_AND_CGROUP_ABSENT',self.h.recovery_disposition(row,{'LoadState':'not-found'},False))
        with self.assertRaises(self.h.Refusal):self.h.recovery_disposition(row,{'LoadState':'not-found'},True)


class ImageTests(unittest.TestCase):
    def setUp(self):
        path=ROOT/'src/build_image.py';self.assertTrue(path.exists(),'image builder is absent')
        sys.path.insert(0,str(ROOT/'src'))
        import build_image
        self.b=build_image
        self.temp=tempfile.TemporaryDirectory(dir=ROOT/'scratch');self.addCleanup(self.temp.cleanup)
        self.path=Path(self.temp.name)/'image';self.path.mkdir(mode=0o755)

    def test_closed_inventory_measures_files_links_and_directories(self):
        (self.path/'app').mkdir();(self.path/'app/a').write_bytes(b'exact');(self.path/'app/b').symlink_to('a')
        (self.path/'app').chmod(0o755);(self.path/'app/a').chmod(0o644)
        entries=self.b.image_inventory(self.path)
        self.assertEqual(['app','app/a','app/b'],[e['path'] for e in entries])
        self.assertEqual(['directory','file','symlink'],[e['kind'] for e in entries])

    def test_escaping_symlink_refuses(self):
        (self.path/'bad').symlink_to('/etc/passwd')
        with self.assertRaises(self.b.Refusal):self.b.image_inventory(self.path)

    def test_special_file_refuses(self):
        os.mkfifo(self.path/'fifo')
        with self.assertRaises(self.b.Refusal):self.b.image_inventory(self.path)

    def test_forbidden_admin_payload_is_not_packaged(self):
        (self.path/'usr/bin').mkdir(parents=True);(self.path/'usr/bin/sudo').write_bytes(b'x')
        with self.assertRaises(self.b.Refusal):self.b.image_inventory(self.path)

    def test_ownership_remains_preparation_only(self):
        (self.path/'x').write_bytes(b'x')
        (self.path/'x').chmod(0o644)
        entries=self.b.image_inventory(self.path)
        self.assertEqual(os.getuid(),entries[0]['preparation_uid'])


if __name__=='__main__':unittest.main(verbosity=2)
