"""Fresh same-UID cryptographic fixtures. Not independent enrollment evidence."""
import os
from pathlib import Path
import subprocess
import time

import contract as c

SSH = '/usr/bin/ssh-keygen'
ENV = {'PATH': '/nonexistent', 'HOME': '/nonexistent', 'LANG': 'C', 'LC_ALL': 'C'}
ENROLL_NS = 'symphony.p08.f09.enrollment.v1'
HEAD_NS = 'symphony.p08.f09.checkpoint.v1'


def command(argv, raw=None):
    p = subprocess.run(argv, input=raw, capture_output=True, timeout=5, env=ENV)
    if p.returncode:
        raise RuntimeError((argv[:3], p.returncode, p.stderr))
    return p.stdout


def write(path, raw):
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        os.fchmod(fd, 0o600)
        os.write(fd, raw)
        os.fsync(fd)
    finally:
        os.close(fd)


def identity(path):
    s = path.lstat()
    return [s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode]


class Fixture:
    def __init__(self, root):
        self.root = root
        root.mkdir(mode=0o700)
        for name in ['owner', 'authority', 'state']:
            (root / name).mkdir(mode=0o700)
        for name in ['owner/key', 'authority/key', 'owner/rogue']:
            command([SSH, '-q', '-t', 'ed25519', '-N', '', '-f', str(root / name)])
        for name in ['authority/anchor', 'authority/lock']:
            write(root / name, b'')
        self.bindings = {k: '1' * 64 for k in c.HASH_FIELDS} | {
            'source_tree': c.D02_TREE, 'candidate_tree': '8' * 40,
            'campaign': c.CAMPAIGN,
            'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip()}
        import host
        public = (root / 'owner/key.pub').read_text().split()
        self.pin = host.public_fingerprint(' '.join(public[:2]))
        custodian = (root / 'authority/key.pub').read_text().split()
        write(root / 'owner/allowed', ('p08-f09-owner ' + ' '.join(public[:2]) + '\n').encode())
        write(root / 'authority/allowed', ('p08-f09-custodian ' + ' '.join(custodian[:2]) + '\n').encode())
        now = int(time.time())
        self.enrollment = {'schema': 'p08-f09-enrollment-1', 'enrollment_id': 'a' * 64,
            'database_id': 'b' * 64, 'root_identity': identity(root),
            'anchor_identity': identity(root / 'authority/anchor'),
            'anchor_created_ns': (root / 'authority/anchor').stat().st_ctime_ns,
            'lock_identity': identity(root / 'authority/lock'), 'bindings': self.bindings,
            'custodian_fingerprint': host.public_fingerprint(' '.join(custodian[:2])),
            'not_before': now - 1, 'expires_at': now + 600}
        self.sign_enrollment()

    def sign_enrollment(self, rogue=False):
        raw = c.canonical(self.enrollment)
        for name in ['owner/enrollment', 'owner/enrollment.sig']:
            path = self.root / name
            if path.exists():
                path.unlink()
        write(self.root / 'owner/enrollment', raw)
        key = 'owner/rogue' if rogue else 'owner/key'
        write(self.root / 'owner/enrollment.sig', command(
            [SSH, '-Y', 'sign', '-f', str(self.root / key), '-n', ENROLL_NS], raw))

    def custody(self):
        import custody
        return custody._HostCustody(self.root, self.pin, self.bindings)

    def enroll(self):
        authority = self.custody()
        grant = authority.enroll()
        import ledger
        return ledger._RegisterStore.initialize(self.root / 'state/register.sqlite3', authority, grant)

    def release(self, **changes):
        now = int(time.time())
        return self.bindings | {'schema': 'p08-host-development-release-1', 'suite': c.SUITE,
            'scope': c.SCOPE, 'attempt_id': '2' * 32, 'release_id': '3' * 32,
            'nonce': '4' * 64, 'slot': 1, 'issued_at': now, 'not_before': now,
            'expires_at': now + 120} | changes

    def consumed(self, register):
        release = self.release()
        register.request(release)
        register.advance(release['attempt_id'], 'ISSUED')
        register.advance(release['attempt_id'], 'VERIFIED')
        register.consume(release['attempt_id'])
        return release
