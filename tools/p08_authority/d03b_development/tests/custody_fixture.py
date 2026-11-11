"""Same-UID disposable custody protocol model. NEVER an independent authority.

No live source imports this module. Its local journal/checkpoint exercise crash
ordering, not protection from a source preparer who controls the whole fixture.
The live Register remains refusal-only. Deleting/rolling back this entire model
cannot establish a new authentic enrollment in the live system.
"""
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import threading
from types import SimpleNamespace

import ledger
from contract import Refusal,canonical,digest,require

_LOCKS={}
_MODELS={}


class Custody:
    """Test authority with durable transitions and an independent-of-DB head."""
    def __init__(self,path):
        self.path=Path(path)
        self.root=self.path.parent/(self.path.name+'.custody-model')
        self.mutex=_LOCKS.setdefault(str(self.root),threading.RLock())
        self.fault=None

    def issue(self):
        require(not self.root.exists() and not self.path.exists(),'ENROLLMENT_ALREADY_EXISTS')
        self.root.mkdir(mode=0o700)
        value=digest(str(self.path).encode())
        grant=ledger.BootstrapGrant(value,value,str(self.path))
        self._write({'phase':'ISSUED','enrollment_id':value,'database_id':value,
                     'locator':str(self.path),'revision':-1,'sha256':'','identity':[]})
        return grant

    @contextmanager
    def lock(self):
        with self.mutex:
            require(self.root.is_dir() and not self.root.is_symlink(),'CUSTODY_UNAVAILABLE')
            fd=os.open(self.root/'lock',os.O_RDWR|os.O_CREAT|os.O_NOFOLLOW,0o600)
            try:
                fcntl.flock(fd,fcntl.LOCK_EX)
                yield
            finally:fcntl.flock(fd,fcntl.LOCK_UN);os.close(fd)

    def _sync(self):
        fd=os.open(self.root,os.O_RDONLY|os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)

    def _read(self):
        try:
            raw=(self.root/'journal').read_bytes()
            lines=raw.splitlines();require(bool(lines),'CUSTODY_HISTORY_MISSING')
            previous='0'*64
            for index,line in enumerate(lines):
                event=json.loads(line)
                require(set(event)=={'sequence','previous','state'} and event['sequence']==index and
                        event['previous']==previous,'CUSTODY_HISTORY_UNCERTAIN')
                previous=digest(line)
            receipt=json.loads((self.root/'receipt').read_bytes())
            require(receipt=={'sequence':len(lines)-1,'sha256':previous},'CUSTODY_RECEIPT_UNCERTAIN')
            return event['state']
        except (OSError,ValueError,KeyError,TypeError):raise Refusal('CUSTODY_RECEIPT_MISSING') from None

    def _write(self,state):
        path=self.root/'journal'
        raw=path.read_bytes() if path.exists() else b''
        lines=raw.splitlines()
        event={'sequence':len(lines),'previous':digest(lines[-1]) if lines else '0'*64,'state':state}
        line=canonical(event)
        fd=os.open(path,os.O_WRONLY|os.O_APPEND|os.O_CREAT|os.O_NOFOLLOW,0o600)
        try:os.write(fd,line+b'\n');os.fsync(fd)
        finally:os.close(fd)
        if self.fault=='lost_receipt':
            self.fault=None
            raise Refusal('SIMULATED_LOST_RECEIPT')
        temporary=self.root/'receipt.next'
        fd=os.open(temporary,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
        try:os.write(fd,canonical({'sequence':event['sequence'],'sha256':digest(line)}));os.fsync(fd)
        finally:os.close(fd)
        os.replace(temporary,self.root/'receipt');self._sync()

    def begin_bootstrap(self,grant,path):
        current=self._read()
        require(type(grant) is ledger.BootstrapGrant and
                current['phase']=='ISSUED' and grant==ledger.BootstrapGrant(
                    current['enrollment_id'],current['database_id'],current['locator']) and
                grant.locator==str(path),'BOOTSTRAP_INVALID')
        self._write(current|{'phase':'BOOTSTRAP'})

    def activate(self,grant,sha256,identity):
        current=self._read();require(current['phase']=='BOOTSTRAP','BOOTSTRAP_INVALID')
        if self.fault=='partial_bootstrap':raise Refusal('SIMULATED_PARTIAL_BOOTSTRAP')
        self._write(current|{'phase':'ACTIVE','revision':0,'sha256':sha256,'identity':list(identity)})

    def current(self,path):
        state=self._read()
        require(state['phase']=='ACTIVE' and state['locator']==str(path),'CUSTODY_NOT_ACTIVE')
        return ledger.RegisterCheckpoint(state['enrollment_id'],state['database_id'],state['locator'],
            state['revision'],state['sha256'],tuple(state['identity']),state['phase'])

    def check_release(self,claims):
        # Legacy storage fixtures intentionally omit source/profile fields.
        # The authenticated component validates the complete closed release.
        pass

    def reserve(self,checkpoint):
        require(self.current(self.path)==checkpoint,'CUSTODY_CHECKPOINT_CHANGED')
        self._write(self._read()|{'phase':'MUTATION_PENDING'})

    def abort(self,checkpoint):
        state=self._read()
        require(state['phase']=='MUTATION_PENDING' and state['revision']==checkpoint.revision and
                state['sha256']==checkpoint.sha256,'CUSTODY_ABORT_UNCERTAIN')
        self._write(state|{'phase':'ACTIVE'})

    def prepare(self,checkpoint,pending):
        state=self._read()
        require(state['phase']=='MUTATION_PENDING' and state['revision']==checkpoint.revision and
                state['sha256']==checkpoint.sha256,'CUSTODY_CHECKPOINT_CHANGED')
        self._write(state|{'phase':'INTERRUPTED','pending_revision':checkpoint.revision+1,'pending_sha256':pending})
        if self.fault=='after_prepare':raise Refusal('SIMULATED_INTERRUPTION')

    def complete(self,checkpoint,pending,identity):
        state=self._read()
        require(state['phase']=='INTERRUPTED' and state['revision']==checkpoint.revision and
            state['sha256']==checkpoint.sha256 and state['pending_sha256']==pending and
            state['pending_revision']==checkpoint.revision+1,'CUSTODY_COMMIT_UNCERTAIN')
        if self.fault=='after_commit_receipt':self.fault='lost_receipt'
        self._write({key:value for key,value in state.items() if not key.startswith('pending_')}|
            {'phase':'ACTIVE','revision':checkpoint.revision+1,'sha256':pending,'identity':list(identity)})

    def quarantine(self,reason):
        state=self._read()
        if state['phase'] in {'QUARANTINED','TERMINAL'}:return
        if reason=='MISSING_HISTORY':
            self._write(state|{'phase':'MISSING_HISTORY','reason':reason})
            state=self._read()
        self._write(state|{'phase':'QUARANTINED','reason':reason})

    def terminate(self):
        state=self._read();self._write(state|{'phase':'TERMINAL'})


def Register(path):
    """Explicitly synthetic enrollment adapter for pre-existing storage tests."""
    path=Path(path)
    key=str(path)
    if key not in _MODELS:
        authority=Custody(path);_MODELS[key]=authority
        if authority.root.exists():return ledger._RegisterStore(path,authority)
        grant=authority.issue()
        return ledger._RegisterStore.initialize(path,authority,grant)
    return ledger._RegisterStore(path,_MODELS[key])

storage=SimpleNamespace(Register=Register,Refusal=Refusal)
