"""Durable register component; live enrollment/checkpoint authority is unconfigured.

_RegisterStore is an internal storage component, not an approval interface.
Its custody argument models the host protocol in disposable component tests.
The public Register cannot install an authority provider or accept a bootstrap
flag. Root ownership or a locally recreated marker is not enrollment evidence.
"""
from contextlib import contextmanager
from dataclasses import dataclass
import json
import os
from pathlib import Path
import sqlite3
import stat
import time

from contract import NEXT, TERMINAL, Refusal, canonical, digest, require


@dataclass(frozen=True)
class BootstrapGrant:
    """Descriptive binding only. Custody must authenticate/reserve it externally."""
    enrollment_id: str
    database_id: str
    locator: str


@dataclass(frozen=True)
class RegisterCheckpoint:
    """Descriptive receipt, never sufficient authority merely by construction."""
    enrollment_id: str
    database_id: str
    locator: str
    revision: int
    sha256: str
    identity: tuple
    phase: str


class HostRegisterCustody:
    """No authenticated enrollment or fresh monotonic-head protocol is deployed.

    No argument, environment value, local file, callback, or source flag selects
    a trust root. A separate accepted host protocol must replace this refusal.
    """
    def recover(self, path):
        raise Refusal('REGISTER_CUSTODY_UNCONFIGURED')

    def initialize(self, path):
        raise Refusal('REGISTER_CUSTODY_UNCONFIGURED')


class Register:
    """Live entry point. Positive enrollment/recovery is deliberately unavailable."""
    def __init__(self, path):
        HostRegisterCustody().recover(Path(path))

    @classmethod
    def initialize(cls, path):
        HostRegisterCustody().initialize(Path(path))


class _RegisterStore:
    TABLES = {'attempts','used','events','slots','execution_events','register_meta'}
    SCHEMA = """
        CREATE TABLE attempts(attempt TEXT PRIMARY KEY,claims TEXT NOT NULL,
            state TEXT NOT NULL,execution TEXT NOT NULL,detail TEXT NOT NULL);
        CREATE TABLE used(attempt TEXT PRIMARY KEY,release TEXT UNIQUE NOT NULL,
            nonce TEXT UNIQUE NOT NULL,slot INTEGER UNIQUE NOT NULL);
        CREATE TABLE events(attempt TEXT NOT NULL,sequence INTEGER NOT NULL,
            raw TEXT NOT NULL,PRIMARY KEY(attempt,sequence));
        CREATE TABLE execution_events(attempt TEXT NOT NULL,sequence INTEGER NOT NULL,
            raw TEXT NOT NULL,PRIMARY KEY(attempt,sequence));
        CREATE TABLE slots(slot INTEGER PRIMARY KEY,attempt TEXT UNIQUE NOT NULL);
        CREATE TABLE register_meta(id INTEGER PRIMARY KEY CHECK(id=1),
            database_id TEXT NOT NULL,revision INTEGER NOT NULL CHECK(revision>=0));
    """

    @staticmethod
    def locator(path):
        path=Path(path)
        require(path.is_absolute() and '..' not in path.parts and
                path.parent.resolve(strict=True)==path.parent,'REGISTER_LOCATION_UNCERTAIN')
        return path

    @staticmethod
    def identity(path):
        value=path.lstat()
        require(stat.S_ISREG(value.st_mode) and value.st_nlink==1 and
                stat.S_IMODE(value.st_mode)==0o600,'REGISTER_FILE_UNCERTAIN')
        return (value.st_dev,value.st_ino,value.st_uid,value.st_gid,value.st_mode)

    @classmethod
    def initialize(cls,path,custody,grant):
        """Reserve external bootstrap before any filesystem effect. Never recover here.

        A reserved/partial bootstrap stays non-ACTIVE after failure. Neither a
        missing database nor missing receipt is permission to repeat bootstrap.
        """
        path=cls.locator(path)
        require(type(grant) is BootstrapGrant and grant.locator==str(path),
                'BOOTSTRAP_INVALID')
        store=object.__new__(cls);store.path=path;store.custody=custody;store.db=None
        try:
            with custody.lock():
                custody.begin_bootstrap(grant,path)
                require(not any(Path(str(path)+suffix).exists() or Path(str(path)+suffix).is_symlink()
                    for suffix in ['', '-journal','-wal','-shm']),'BOOTSTRAP_COLLISION')
                fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW,0o600)
                try:os.fchmod(fd,0o600);os.fsync(fd)
                finally:os.close(fd)
                store._open();store.db.executescript(cls.SCHEMA)
                store.db.execute('INSERT INTO register_meta VALUES(1,?,0)',(grant.database_id,))
                store.sync()
                custody.activate(grant,store.snapshot(),cls.identity(path))
        except BaseException:
            store.close();raise
        store.close()
        return cls(path,custody)

    def _open(self):
        self.db=sqlite3.connect(self.path.as_uri()+'?mode=rw',uri=True,timeout=3,isolation_level=None)
        self.db.row_factory=sqlite3.Row
        self.db.execute('PRAGMA synchronous=FULL');self.db.execute('PRAGMA journal_mode=DELETE')

    def __init__(self,path,custody):
        self.path=self.locator(path);self.custody=custody;self.db=None
        try:
            with custody.lock():
                custody.current(self.path)  # Fresh authority, before touching SQLite.
                if not self.path.exists():
                    custody.quarantine('MISSING_HISTORY')
                    raise Refusal('REGISTER_HISTORY_MISSING')
                self.identity(self.path)
                require(not any(Path(str(self.path)+suffix).exists() for suffix in
                    ['-journal','-wal','-shm']),'REGISTER_PARTIAL')
                self._open();self.db.execute('BEGIN IMMEDIATE')
                self._check_head();self.validate();self.db.execute('COMMIT')
        except (sqlite3.Error,OSError,ValueError,KeyError,TypeError):
            try:self._quarantine()
            finally:self.close()
            raise Refusal('REGISTER_UNCERTAIN') from None
        except Refusal:
            try:self._quarantine()
            finally:self.close()
            raise

    def _quarantine(self):
        # Authority retains the reason and terminal state; it must never reset.
        with self.custody.lock():self.custody.quarantine('REGISTER_UNCERTAIN')

    def snapshot(self):
        tables={row[0] for row in self.db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        require(tables==self.TABLES,'REGISTER_UNCERTAIN')
        data={name:sorted([list(row) for row in self.db.execute('SELECT * FROM '+name)],key=canonical)
              for name in sorted(self.TABLES)}
        schema=[list(row) for row in self.db.execute(
            "SELECT type,name,tbl_name,sql FROM sqlite_master ORDER BY type,name")]
        return digest(canonical({'schema':schema,'tables':data}))

    def _check_head(self):
        checkpoint=self.custody.current(self.path)
        require(type(checkpoint) is RegisterCheckpoint and checkpoint.phase=='ACTIVE' and
            checkpoint.locator==str(self.path) and checkpoint.identity==self.identity(self.path),
            'REGISTER_CHECKPOINT_MISMATCH')
        meta=self.db.execute('SELECT database_id,revision FROM register_meta WHERE id=1').fetchone()
        require(meta is not None and tuple(meta)==(checkpoint.database_id,checkpoint.revision) and
                self.snapshot()==checkpoint.sha256,'REGISTER_HISTORY_MISMATCH')
        return checkpoint

    @contextmanager
    def transaction(self):
        """External prepare is durable before SQLite commit, completion follows fsync.

        A crash in either gap leaves INTERRUPTED custody, never a fresh grant.
        No automatic recovery advances an uncertain checkpoint.
        """
        with self.custody.lock():
            try:
                self.db.execute('BEGIN IMMEDIATE')
                try:checkpoint=self._check_head()
                except (Refusal,sqlite3.Error,OSError):
                    self.custody.quarantine('REGISTER_HISTORY_MISMATCH');raise
                yield
                self.db.execute('UPDATE register_meta SET revision=revision+1 WHERE id=1')
                pending=self.snapshot()
                self.custody.prepare(checkpoint,pending)
                self.db.execute('COMMIT');self.sync()
                self.custody.complete(checkpoint,pending,self.identity(self.path))
            except sqlite3.IntegrityError:
                if self.db.in_transaction:self.db.execute('ROLLBACK')
                raise Refusal('RELEASE_REPLAYED') from None
            except (sqlite3.Error,OSError,ValueError,KeyError,TypeError):
                if self.db.in_transaction:self.db.execute('ROLLBACK')
                self.custody.quarantine('REGISTER_UNCERTAIN')
                raise Refusal('REGISTER_UNCERTAIN') from None
            except BaseException:
                if self.db.in_transaction:self.db.execute('ROLLBACK')
                raise

    def validate(self):
        require(self.db.execute('PRAGMA quick_check').fetchone()[0] == 'ok', 'REGISTER_UNCERTAIN')
        for row in self.rows():
            history=self.history(row['attempt']);require(history and history[-1]==row['state'],'REGISTER_UNCERTAIN')
            claims=json.loads(row['claims'])
            execution_history=self.execution_history(row['attempt'])
            require((execution_history[-1] if execution_history else 'NOT_STARTED')==row['execution'],'REGISTER_UNCERTAIN')
            slot=self.db.execute('SELECT slot FROM slots WHERE attempt=?',(row['attempt'],)).fetchone()
            require(slot is not None and slot[0]==claims['slot'],'REGISTER_UNCERTAIN')
            used=self.db.execute('SELECT * FROM used WHERE attempt=?',(row['attempt'],)).fetchone()
            require((used is not None)==(row['state']=='CONSUMED'),'REGISTER_UNCERTAIN')
            if used is not None:
                require(dict(used)=={'attempt':row['attempt'],'release':claims['release_id'],
                        'nonce':claims['nonce'],'slot':claims['slot']},'REGISTER_UNCERTAIN')
        require(self.db.execute('SELECT count(*) FROM slots').fetchone()[0]==len(self.rows()) and
            self.db.execute('SELECT count(*) FROM used').fetchone()[0]==sum(row['state']=='CONSUMED' for row in self.rows()),
            'REGISTER_UNCERTAIN')

    def sync(self):
        fd=os.open(self.path,os.O_RDONLY|os.O_NOFOLLOW)
        try:os.fsync(fd)
        finally:os.close(fd)
        fd = os.open(self.path.parent, os.O_RDONLY | os.O_DIRECTORY)
        try:os.fsync(fd)
        finally:os.close(fd)

    def get(self, attempt):
        value = self.db.execute('SELECT * FROM attempts WHERE attempt=?', (attempt,)).fetchone()
        return dict(value) if value is not None else None

    def rows(self):return [dict(row) for row in self.db.execute('SELECT * FROM attempts')]

    def history(self, attempt):
        states=[];previous='0'*64
        for sequence, row in enumerate(self.db.execute('SELECT raw FROM events WHERE attempt=? ORDER BY sequence',(attempt,))):
            value=json.loads(row['raw'])
            require(set(value)=={'attempt','sequence','state','previous','time'} and value['attempt']==attempt and
                    value['sequence']==sequence and value['previous']==previous and
                    value['state'] in NEXT.get(states[-1] if states else None,set()), 'REGISTER_UNCERTAIN')
            states.append(value['state']);previous=digest(row['raw'].encode())
        return states

    def event(self, attempt, state):
        rows=self.db.execute('SELECT raw FROM events WHERE attempt=? ORDER BY sequence',(attempt,)).fetchall()
        raw=canonical({'attempt':attempt,'sequence':len(rows),'state':state,
            'previous':digest(rows[-1]['raw'].encode()) if rows else '0'*64,'time':time.time_ns()}).decode()
        self.db.execute('INSERT INTO events VALUES(?,?,?)',(attempt,len(rows),raw))

    def request(self, claims):
        with self.transaction():
            self.db.execute('INSERT INTO slots VALUES(?,?)',(claims['slot'],claims['attempt_id']))
            self.db.execute('INSERT INTO attempts VALUES(?,?,?,?,?)',
                (claims['attempt_id'],canonical(claims).decode(),'REQUESTED','NOT_STARTED','{}'))
            self.event(claims['attempt_id'],'REQUESTED')

    def advance(self, attempt, state):
        with self.transaction():
            row=self.get(attempt)
            require(row is not None and state in NEXT.get(row['state'],set()),'TRANSITION_INVALID')
            self.db.execute('UPDATE attempts SET state=? WHERE attempt=?',(state,attempt))
            self.event(attempt,state)

    def consume(self, attempt):
        with self.transaction():
            row=self.get(attempt)
            require(row is not None and row['state']=='VERIFIED','RELEASE_NOT_VERIFIED')
            claims=json.loads(row['claims'])
            self.db.execute('INSERT INTO used VALUES(?,?,?,?)',(attempt,claims['release_id'],claims['nonce'],claims['slot']))
            self.event(attempt,'RELEASED');self.event(attempt,'CONSUMED')
            self.db.execute('UPDATE attempts SET state=?,execution=? WHERE attempt=?',('CONSUMED','START_PENDING',attempt))
            self.execution_event(attempt,'START_PENDING',{})

    EXECUTION_NEXT={'NOT_STARTED':{'START_PENDING'},'START_PENDING':{'LAUNCHING','INTERRUPTED'},
        'LAUNCHING':{'RUNNING','INTERRUPTED'},'RUNNING':{'EXIT_OBSERVED','INTERRUPTED'},
        'EXIT_OBSERVED':{'CLEANING','INTERRUPTED'},'CLEANING':{'FINISHED','INTERRUPTED'}}

    def execution_event(self,attempt,state,detail):
        rows=self.db.execute('SELECT raw FROM execution_events WHERE attempt=? ORDER BY sequence',(attempt,)).fetchall()
        raw=canonical({'attempt':attempt,'sequence':len(rows),'state':state,'detail':detail,
            'previous':digest(rows[-1]['raw'].encode()) if rows else '0'*64}).decode()
        self.db.execute('INSERT INTO execution_events VALUES(?,?,?)',(attempt,len(rows),raw))

    def execution_history(self,attempt):
        states=[];previous='0'*64;last_detail={}
        for sequence,row in enumerate(self.db.execute('SELECT raw FROM execution_events WHERE attempt=? ORDER BY sequence',(attempt,))):
            value=json.loads(row['raw'])
            require(set(value)=={'attempt','sequence','state','detail','previous'} and value['attempt']==attempt and
                value['sequence']==sequence and value['previous']==previous and
                value['state'] in self.EXECUTION_NEXT.get(states[-1] if states else 'NOT_STARTED',set()),'REGISTER_UNCERTAIN')
            states.append(value['state']);last_detail=value['detail'];previous=digest(row['raw'].encode())
        row=self.get(attempt)
        require(row is not None and json.loads(row['detail'])==last_detail,'REGISTER_UNCERTAIN')
        return states

    def execution(self, attempt, state, detail):
        with self.transaction():
            row=self.get(attempt)
            require(row is not None and row['state']=='CONSUMED' and
                state in self.EXECUTION_NEXT.get(row['execution'],set()),'EXECUTION_TERMINAL')
            self.execution_event(attempt,state,detail)
            self.db.execute('UPDATE attempts SET execution=?,detail=? WHERE attempt=?',(state,canonical(detail).decode(),attempt))

    def reconcile(self, observe):
        """Live host supplies a fixed recovery observer, never a worker callback."""
        for row in self.rows():
            if row['state'] not in TERMINAL:self.advance(row['attempt'],'REJECTED')
            elif row['state']=='CONSUMED' and row['execution'] not in {'FINISHED','INTERRUPTED'}:
                evidence=observe(row)
                self.execution(row['attempt'],'INTERRUPTED',evidence)

    def close(self):
        if self.db is not None:self.db.close();self.db=None

    def __enter__(self):return self
    def __exit__(self,*unused):self.close()
