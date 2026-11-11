"""Dormant host-owned F09 custody component. There is no operational loader.

Owner enrollment authenticates a particular host record, boot and source/profile
binding. A separately protected append-only host witness owns the current head;
the register and its signed checkpoint are projections, never freshness roots.
Rolling back the protected witness itself is outside this component's threat
boundary. Root ownership alone cannot exclude an unrestricted administrator.

Only a future independently reviewed host installer may supply the owner pin
and fixed root. This module has no CLI, provider registry, environment selector,
generic signing entry point or test-authority import. The public live Register
remains unconfigured. Same-UID tests establish ordering and authenticity only.
"""
from contextlib import contextmanager
from enum import Enum
import fcntl
import os
from pathlib import Path
import stat
import subprocess
import threading
import time

from contract import BINDINGS, Refusal, canonical, check_binding, digest, hex_id, parse_json, parse_release, require
from host import public_fingerprint
from ledger import BootstrapGrant, RegisterCheckpoint

SSH = '/usr/bin/ssh-keygen'
SSH_SHA256 = '2dd834413c9d3f4c0e3535b9fcf2e96e14c11f3d36fd23b6c5fc24e50411d051'
ENROLL_NS = 'symphony.p08.f09.enrollment.v1'
HEAD_NS = 'symphony.p08.f09.checkpoint.v1'
ENV = {'PATH': '/nonexistent', 'HOME': '/nonexistent', 'LANG': 'C', 'LC_ALL': 'C'}
PHASES = frozenset({'ENROLLMENT_PENDING', 'BOOTSTRAP_RESERVED', 'BOOTSTRAPPING',
    'ACTIVE', 'MUTATION_PENDING', 'INTERRUPTED', 'MISSING_HISTORY', 'QUARANTINED', 'RETIRED'})
ENROLL_FIELDS = frozenset({'schema', 'enrollment_id', 'database_id', 'root_identity',
    'anchor_identity', 'anchor_created_ns', 'lock_identity', 'bindings',
    'custodian_fingerprint', 'not_before', 'expires_at'})
STATE_FIELDS = frozenset({'phase', 'revision', 'sha256', 'identity', 'pending_sha256', 'reason'})
MAX_HISTORY = 8 * 1024 * 1024


class _SignatureOperation(Enum):
    VERIFY_ENROLLMENT = 1
    VERIFY_CHECKPOINT = 2
    SIGN_CHECKPOINT = 3


def _identity(path):
    s = path.lstat()
    return [s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode]


def _stable_file(s):
    return (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode, s.st_nlink,
            s.st_size, s.st_mtime_ns, s.st_ctime_ns)


def _transition(previous, state):
    """Validate both newly proposed writes and the complete retained history."""
    require(type(state) is dict and set(state) == STATE_FIELDS and state['phase'] in PHASES and
        type(state['revision']) is int and -1 <= state['revision'] < 2**63 and
        type(state['identity']) is list and all(type(v) is int for v in state['identity']) and
        type(state['reason']) is str and len(state['reason']) <= 64 and
        (state['pending_sha256'] == '' or hex_id(state['pending_sha256'], 64)), 'CUSTODY_STATE_INVALID')
    head = ('revision', 'sha256', 'identity')
    if previous is None:
        require(state == {'phase': 'ENROLLMENT_PENDING', 'revision': -1, 'sha256': '',
            'identity': [], 'pending_sha256': '', 'reason': ''}, 'CUSTODY_TRANSITION_INVALID')
        return
    before, after = previous['phase'], state['phase']
    allowed = {'ENROLLMENT_PENDING': {'BOOTSTRAP_RESERVED'},
        'BOOTSTRAP_RESERVED': {'BOOTSTRAPPING'}, 'BOOTSTRAPPING': {'ACTIVE'},
        'ACTIVE': {'MUTATION_PENDING'}, 'MUTATION_PENDING': {'INTERRUPTED', 'ACTIVE'},
        'INTERRUPTED': {'ACTIVE'}, 'MISSING_HISTORY': {'QUARANTINED'}}
    outgoing = allowed.get(before, set())
    if before not in {'MISSING_HISTORY', 'QUARANTINED', 'RETIRED'}:
        outgoing = outgoing | {'QUARANTINED', 'MISSING_HISTORY', 'RETIRED'}
    require(after in outgoing, 'CUSTODY_TRANSITION_INVALID')
    if after == 'ACTIVE' and before == 'BOOTSTRAPPING':
        require(state['revision'] == 0 and hex_id(state['sha256'], 64) and
            len(state['identity']) == 5 and state['pending_sha256'] == '', 'CUSTODY_STATE_INVALID')
    elif after == 'ACTIVE' and before == 'INTERRUPTED':
        require(hex_id(previous['pending_sha256'], 64) and state['pending_sha256'] == '' and
            state['revision'] == previous['revision'] + 1 and state['sha256'] == previous['pending_sha256'] and
            state['identity'] == previous['identity'], 'CUSTODY_COMMIT_UNCERTAIN')
    else:
        require(all(state[k] == previous[k] for k in head), 'CUSTODY_HEAD_CHANGED')
        if after == 'ACTIVE':
            require(before == 'MUTATION_PENDING' and previous['pending_sha256'] == '' and
                    state['pending_sha256'] == '', 'CUSTODY_ABORT_UNCERTAIN')
        elif after != 'INTERRUPTED':
            require(state['pending_sha256'] == previous['pending_sha256'], 'CUSTODY_HEAD_CHANGED')


class _HostCustody:
    """Internal fixed-layout host component, not an authority-selection API.

    The owner pin must arrive through trusted installation, never worker inputs.
    A valid certificate cannot make candidate-controlled storage independent.
    All methods run in the trusted host, under the same non-stealable lock.
    """
    def __init__(self, root, owner_pin, bindings):
        self.root = Path(root)
        self.path = self.root / 'state/register.sqlite3'
        self.owner_pin = owner_pin
        self.bindings = dict(bindings)
        self._mutex = threading.RLock()
        self._depth = 0
        self._authenticate()

    def _file(self, name, limit=65536):
        """Fixed internal names only; reject aliases and special files before open."""
        path = self.root / name
        before = path.lstat()
        require(stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and
            stat.S_IMODE(before.st_mode) == 0o600 and before.st_uid == os.geteuid()
            and before.st_size <= limit, 'CUSTODY_FILE_UNCERTAIN')
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
        try:
            raw = bytearray()
            while len(raw) <= limit:
                block = os.read(fd, min(65536, limit + 1 - len(raw)))
                if not block: break
                raw.extend(block)
            after = os.fstat(fd)
            require(_stable_file(before) == _stable_file(after) == _stable_file(path.lstat()) and len(raw) <= limit,
                    'CUSTODY_FILE_CHANGED')
            return bytes(raw)
        finally:
            os.close(fd)

    def _crypto(self, operation, raw):
        # No caller-selected executable, principal, key, namespace or flags.
        require(type(operation) is _SignatureOperation, 'CUSTODY_OPERATION_INVALID')
        if operation is _SignatureOperation.SIGN_CHECKPOINT:
            event, head = self._anchor()
            require(parse_json(raw) == {'sequence': event['sequence'], 'sha256': head,
                'enrollment': self.enrollment_sha256}, 'CUSTODY_SIGN_SCOPE_INVALID')
            arguments = ['-Y', 'sign', '-f', str(self.root / 'authority/key'), '-n', HEAD_NS]
        else:
            enrollment = operation is _SignatureOperation.VERIFY_ENROLLMENT
            prefix = 'owner' if enrollment else 'authority'
            arguments = ['-Y', 'verify', '-f', str(self.root / prefix / 'allowed'), '-I',
                'p08-f09-owner' if enrollment else 'p08-f09-custodian', '-n',
                ENROLL_NS if enrollment else HEAD_NS, '-s',
                str(self.root / ('owner/enrollment.sig' if enrollment else 'authority/receipt.sig'))]
        require(digest(Path(SSH).read_bytes()) == SSH_SHA256, 'CUSTODY_TOOL_CHANGED')
        try:
            result = subprocess.run([SSH] + arguments, input=raw, capture_output=True,
                                    timeout=3, env=ENV, close_fds=True)
        except (OSError, subprocess.TimeoutExpired):
            raise Refusal('CUSTODIAN_UNAVAILABLE') from None
        require(result.returncode == 0, 'CUSTODY_SIGNATURE_INVALID')
        return result.stdout

    def _authenticate(self):
        try:
            require(self.root.is_absolute() and self.root.resolve(strict=True) == self.root,
                    'CUSTODY_ROOT_UNCERTAIN')
            for directory in [self.root, self.root / 'owner', self.root / 'authority', self.root / 'state']:
                s = directory.lstat()
                require(stat.S_ISDIR(s.st_mode) and stat.S_IMODE(s.st_mode) == 0o700 and
                        s.st_uid == os.geteuid(), 'CUSTODY_ROOT_UNCERTAIN')
            allowed = self._file('owner/allowed').decode('ascii').split()
            require(len(allowed) == 3 and allowed[0] == 'p08-f09-owner' and
                    public_fingerprint(' '.join(allowed[1:])) == self.owner_pin,
                    'ENROLLMENT_TRUST_MISMATCH')
            raw = self._file('owner/enrollment')
            self._file('owner/enrollment.sig')
            self._crypto(_SignatureOperation.VERIFY_ENROLLMENT, raw)
            value = parse_json(raw, 'ENROLLMENT_INVALID')
            require(type(value) is dict and set(value) == ENROLL_FIELDS and
                value['schema'] == 'p08-f09-enrollment-1' and
                hex_id(value['enrollment_id'], 64) and hex_id(value['database_id'], 64) and
                value['bindings'] == self.bindings and set(self.bindings) == BINDINGS and
                value['root_identity'] == _identity(self.root) and
                value['lock_identity'] == _identity(self.root / 'authority/lock') and
                value['anchor_identity'] == _identity(self.root / 'authority/anchor'), 'ENROLLMENT_INVALID')
            self._file('authority/lock', 0)
            self._file('authority/anchor', MAX_HISTORY)
            now = int(time.time())
            require(type(value['not_before']) is int and type(value['expires_at']) is int and
                value['not_before'] <= now < value['expires_at'] and
                value['expires_at'] - value['not_before'] <= 3600, 'ENROLLMENT_EXPIRED')
            require(self.bindings['boot_id'] == Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                    'ENROLLMENT_BOOT_CHANGED')
            allowed = self._file('authority/allowed').decode('ascii').split()
            require(len(allowed) == 3 and allowed[0] == 'p08-f09-custodian' and
                public_fingerprint(' '.join(allowed[1:])) == value['custodian_fingerprint'],
                'CUSTODIAN_IDENTITY_MISMATCH')
            self.enrollment = value
            self.enrollment_sha256 = digest(raw)
        except (OSError, ValueError, TypeError, KeyError, UnicodeError):
            raise Refusal('CUSTODY_UNAVAILABLE') from None

    @contextmanager
    def lock(self):
        """No lock stealing or waiting on an unresponsive custodian."""
        with self._mutex:
            if self._depth:
                self._depth += 1
                try: yield
                finally: self._depth -= 1
                return
            fd = None
            try:
                self._authenticate()
                fd = os.open(self.root / 'authority/lock', os.O_RDWR | os.O_NOFOLLOW)
                require(list((lambda s: (s.st_dev, s.st_ino, s.st_uid, s.st_gid, s.st_mode))(os.fstat(fd)))
                        == self.enrollment['lock_identity'], 'CUSTODY_LOCK_CHANGED')
                try: fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError: raise Refusal('CUSTODIAN_BUSY') from None
                self._depth = 1
                yield
            except (OSError, ValueError, KeyError, TypeError):
                raise Refusal('CUSTODY_UNAVAILABLE') from None
            finally:
                self._depth = 0
                if fd is not None: os.close(fd)

    def _anchor(self):
        require(self._depth > 0, 'CUSTODY_LOCK_REQUIRED')
        self._authenticate()
        raw = self._file('authority/anchor', MAX_HISTORY)
        require(raw and raw.endswith(b'\n'), 'CUSTODY_HISTORY_MISSING')
        previous = '0' * 64
        previous_state = None
        previous_time = -1
        for sequence, line in enumerate(raw.splitlines()):
            event = parse_json(line, 'CUSTODY_HISTORY_UNCERTAIN')
            require(type(event) is dict and set(event) == {'sequence', 'previous', 'enrollment', 'time_ns', 'state'} and
                event['sequence'] == sequence and event['previous'] == previous and
                event['enrollment'] == self.enrollment_sha256 and type(event['time_ns']) is int and
                previous_time <= event['time_ns'] <= time.time_ns(), 'CUSTODY_HISTORY_UNCERTAIN')
            state = event['state']
            _transition(previous_state, state)
            previous_state, previous_time = state, event['time_ns']
            previous = digest(line)
        return event, previous

    def _read(self):
        event, head = self._anchor()
        raw = self._file('authority/receipt')
        self._file('authority/receipt.sig')
        receipt = parse_json(raw, 'CUSTODY_RECEIPT_INVALID')
        require(receipt == {'sequence': event['sequence'], 'sha256': head,
                           'enrollment': self.enrollment_sha256}, 'CUSTODY_RECEIPT_STALE')
        self._crypto(_SignatureOperation.VERIFY_CHECKPOINT, raw)
        return event['state']

    def _sync_directory(self):
        fd = os.open(self.root / 'authority', os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
        try: os.fsync(fd)
        finally: os.close(fd)

    def _publish(self, receipt):
        """Witness commit precedes projection. A missing projection never resets it."""
        raw = canonical(receipt)
        self._file('authority/key', 4096)
        signature = self._crypto(_SignatureOperation.SIGN_CHECKPOINT, raw)
        for name, payload in [('receipt', raw), ('receipt.sig', signature)]:
            tmp = self.root / 'authority' / (name + '.pending')
            fd = os.open(tmp, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
            try:
                os.fchmod(fd, 0o600)
                require(os.write(fd, payload) == len(payload), 'CUSTODY_WRITE_PARTIAL')
                os.fsync(fd)
            finally: os.close(fd)
            os.replace(tmp, self.root / 'authority' / name)
            self._sync_directory()

    def _write(self, state, first=False):
        if first:
            sequence, previous = 0, '0' * 64
            _transition(None, state)
        else:
            event, previous = self._anchor()
            sequence = event['sequence'] + 1
            _transition(event['state'], state)
        line = canonical({'sequence': sequence, 'previous': previous,
            'enrollment': self.enrollment_sha256, 'time_ns': time.time_ns(), 'state': state})
        require((self.root / 'authority/anchor').stat().st_size + len(line) + 1 <= MAX_HISTORY,
                'CUSTODY_HISTORY_FULL')
        fd = os.open(self.root / 'authority/anchor', os.O_WRONLY | os.O_APPEND | os.O_NOFOLLOW)
        try:
            opened = os.fstat(fd)
            require([opened.st_dev, opened.st_ino, opened.st_uid, opened.st_gid, opened.st_mode] ==
                _identity(self.root / 'authority/anchor') == self.enrollment['anchor_identity'] and
                opened.st_nlink == 1,
                    'CUSTODY_FILE_CHANGED')
            require(os.write(fd, line + b'\n') == len(line) + 1, 'CUSTODY_WRITE_PARTIAL')
            os.fsync(fd)
        finally: os.close(fd)
        self._sync_directory()
        self._publish({'sequence': sequence, 'sha256': digest(line), 'enrollment': self.enrollment_sha256})

    def enroll(self):
        """Owner preallocates/pins empty anchor before signing; never recreate it."""
        with self.lock():
            path = self.root / 'authority/anchor'
            require(self._file('authority/anchor', MAX_HISTORY) == b'' and
                path.stat().st_ctime_ns == self.enrollment['anchor_created_ns'] and
                not self.path.exists(), 'ENROLLMENT_ALREADY_USED')
            state = {'phase': 'ENROLLMENT_PENDING', 'revision': -1, 'sha256': '',
                     'identity': [], 'pending_sha256': '', 'reason': ''}
            self._write(state, first=True)
            self._write(state | {'phase': 'BOOTSTRAP_RESERVED'})
            return BootstrapGrant(self.enrollment['enrollment_id'], self.enrollment['database_id'], str(self.path))

    def begin_bootstrap(self, grant, path):
        state = self._read()
        expected = BootstrapGrant(self.enrollment['enrollment_id'], self.enrollment['database_id'], str(self.path))
        require(type(grant) is BootstrapGrant and grant == expected and path == self.path and
                state['phase'] == 'BOOTSTRAP_RESERVED', 'BOOTSTRAP_INVALID')
        self._write(state | {'phase': 'BOOTSTRAPPING'})

    def activate(self, grant, sha256, identity):
        state = self._read()
        require(state['phase'] == 'BOOTSTRAPPING' and grant == BootstrapGrant(
            self.enrollment['enrollment_id'], self.enrollment['database_id'], str(self.path)), 'BOOTSTRAP_INVALID')
        self._write(state | {'phase': 'ACTIVE', 'revision': 0, 'sha256': sha256, 'identity': list(identity)})

    def current(self, path):
        state = self._read()
        if state['phase'] == 'MUTATION_PENDING':
            # A recovered reservation is never replayed, even if SQL rolled back.
            self._write(state | {'phase': 'INTERRUPTED', 'reason': 'RECOVERY_NO_RESUME'})
            raise Refusal('CUSTODY_INTERRUPTED')
        require(path == self.path and state['phase'] == 'ACTIVE', 'CUSTODY_NOT_ACTIVE')
        return RegisterCheckpoint(self.enrollment['enrollment_id'], self.enrollment['database_id'], str(path),
            state['revision'], state['sha256'], tuple(state['identity']), 'ACTIVE')

    def check_release(self, claims):
        parsed = parse_release(canonical(claims))
        check_binding(parsed, self.bindings, int(time.time()))

    def reserve(self, checkpoint):
        require(self.current(self.path) == checkpoint, 'CUSTODY_CHECKPOINT_CHANGED')
        self._write(self._read() | {'phase': 'MUTATION_PENDING'})

    def abort(self, checkpoint):
        """Only an observed SQL rollback before prepare can abandon an intent.

        This never runs on restart or uncertain commit. History retains the
        reservation and abort, and the existing consumed set cannot change.
        """
        state = self._read()
        require(state['phase'] == 'MUTATION_PENDING' and state['pending_sha256'] == '' and
            state['revision'] == checkpoint.revision and state['sha256'] == checkpoint.sha256,
            'CUSTODY_ABORT_UNCERTAIN')
        self._write(state | {'phase': 'ACTIVE', 'reason': 'OBSERVED_SQL_ROLLBACK'})

    def prepare(self, checkpoint, pending):
        state = self._read()
        require(state['phase'] == 'MUTATION_PENDING' and state['revision'] == checkpoint.revision and
            state['sha256'] == checkpoint.sha256 and hex_id(pending, 64), 'CUSTODY_PREPARE_UNCERTAIN')
        self._write(state | {'phase': 'INTERRUPTED', 'pending_sha256': pending})

    def complete(self, checkpoint, pending, identity):
        state = self._read()
        require(state['phase'] == 'INTERRUPTED' and state['revision'] == checkpoint.revision and
            state['sha256'] == checkpoint.sha256 and state['pending_sha256'] == pending and
            tuple(identity) == checkpoint.identity, 'CUSTODY_COMMIT_UNCERTAIN')
        self._write(state | {'phase': 'ACTIVE', 'revision': checkpoint.revision + 1,
            'sha256': pending, 'pending_sha256': '', 'identity': list(identity), 'reason': ''})

    def quarantine(self, reason):
        require(reason in {'MISSING_HISTORY', 'REGISTER_UNCERTAIN', 'REGISTER_HISTORY_MISMATCH'},
                'CUSTODY_REASON_INVALID')
        state = self._anchor()[0]['state']
        if state['phase'] in {'QUARANTINED', 'RETIRED'}: return
        if reason == 'MISSING_HISTORY':
            state = state | {'phase': 'MISSING_HISTORY', 'reason': reason}
            self._write(state)
        self._write(state | {'phase': 'QUARANTINED', 'reason': reason})

    def retire(self):
        self._write(self._read() | {'phase': 'RETIRED', 'reason': 'OWNER_RETIREMENT'})
