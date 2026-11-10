"""Four finite D03 child tests. This is a new profile, not historical R1b."""
import errno
import importlib.util
import json
import os
from pathlib import Path
import socket
import sys
import unittest


class FiniteMethods(unittest.TestCase):
    def test_exact_synthetic_fixture(self):
        self.assertEqual({'meaning':'D03 synthetic only','value':42},json.loads(Path('/app/fixture.json').read_bytes()))
    def test_finite_calculation(self):self.assertEqual(45,sum(range(10)))
    def test_network_socket_denied(self):
        with self.assertRaises(OSError) as caught:socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.assertEqual(errno.EPERM,caught.exception.errno)
    def test_output_audit_and_read_only_image(self):
        Path('/output/finite-result.json').write_text('{"value":42}')
        with self.assertRaises(RuntimeError):Path('/app/forbidden-write').write_bytes(b'no')
        self.assertFalse(Path('/app/forbidden-write').exists())


if __name__=='__main__':
    if not 61184<=os.geteuid()<=65519:raise SystemExit('WORKER_IDENTITY_UNPROVEN')
    spec=importlib.util.spec_from_file_location('p08_development_release','/app/d02/p08_development_release.py')
    d=importlib.util.module_from_spec(spec);sys.modules[spec.name]=d;spec.loader.exec_module(d)
    d.install_output_audit(Path('/output'))
    unittest.main(verbosity=2)
