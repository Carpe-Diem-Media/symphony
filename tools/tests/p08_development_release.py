"""Owner-issued development releases. No production or formal R1b authority.

The owner private key and signing capability must remain inaccessible to the
source-preparation account. Reuse the existing trusted host boundary; another
device or a new account hierarchy is not required.
Populate the two public pins only from an explicit original-owner confirmation,
then remeasure the request before the separate owner environment signs it.
There is no CLI, environment or release-record trust-anchor selector.
"""
import base64
import fcntl
import hashlib
import json
import os
import platform
from pathlib import Path
import re
import stat
import subprocess
import sys
import time
from dataclasses import dataclass

TASK = 'P08_R1B_D01_AUTHENTICATED_RUNNER_DEVELOPMENT'
BASE_COMMIT = '06db4d97e6313533431a1798b8325d4a179b5115'
BASE_TREE = '3b60b9723342fe7160cee5fdda75a18b7612357e'
BASELINE_INVENTORY_SHA256 = 'a113a132496803f7a0b1b2443ce6bff1fda0d037ffe8122d603dbacd702bd1cd'
PROFILE = 'PB-D01-OWNER-RELEASE-1'
SUITE = 'release-development'
SCOPE = 'DEVELOPMENT_RELEASE_TESTS_ONLY'
NAMESPACE = 'symphony.p08.runner-development.v1'
REVOCATION_NAMESPACE = 'symphony.p08.runner-development-revocation.v1'
PYTHON = '/usr/bin/python3.14'
SSH = '/usr/bin/ssh-keygen'
SSH_SHA256 = '2dd834413c9d3f4c0e3535b9fcf2e96e14c11f3d36fd23b6c5fc24e50411d051'
EXECUTABLE_PINS = {
    PYTHON:'52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41',
    SSH:SSH_SHA256,
    '/usr/lib/x86_64-linux-gnu/libseccomp.so.2.6.0':'df995d80c824876afc38528b5e71d258e1844eb524cd9d34f9a7898562fd99e7',
}
OWNER_CONFIRMED_PUBLIC_KEY = None
OWNER_CONFIRMED_FINGERPRINT = None
NATIVE_RUNTIME_PATHS = (
    '/usr/bin/git',
    '/usr/bin/python3.14',
    '/usr/bin/ssh-keygen',
    '/usr/lib/x86_64-linux-gnu/ld-linux-x86-64.so.2',
    '/usr/lib/x86_64-linux-gnu/libX11.so.6.4.0',
    '/usr/lib/x86_64-linux-gnu/libXau.so.6.0.0',
    '/usr/lib/x86_64-linux-gnu/libXdmcp.so.6.0.0',
    '/usr/lib/x86_64-linux-gnu/libXext.so.6.4.0',
    '/usr/lib/x86_64-linux-gnu/libXft.so.2.3.6',
    '/usr/lib/x86_64-linux-gnu/libXrender.so.1.3.0',
    '/usr/lib/x86_64-linux-gnu/libXss.so.1.0.0',
    '/usr/lib/x86_64-linux-gnu/libbrotlicommon.so.1.2.0',
    '/usr/lib/x86_64-linux-gnu/libbrotlidec.so.1.2.0',
    '/usr/lib/x86_64-linux-gnu/libbz2.so.1.0.4',
    '/usr/lib/x86_64-linux-gnu/libc.so.6',
    '/usr/lib/x86_64-linux-gnu/libcrypto.so.3',
    '/usr/lib/x86_64-linux-gnu/libdb-5.3.so',
    '/usr/lib/x86_64-linux-gnu/libexpat.so.1.11.2',
    '/usr/lib/x86_64-linux-gnu/libffi.so.8.2.0',
    '/usr/lib/x86_64-linux-gnu/libfontconfig.so.1.16.1',
    '/usr/lib/x86_64-linux-gnu/libfreetype.so.6.20.5',
    '/usr/lib/x86_64-linux-gnu/libgdbm.so.6.0.0',
    '/usr/lib/x86_64-linux-gnu/liblzma.so.5.8.3',
    '/usr/lib/x86_64-linux-gnu/libm.so.6',
    '/usr/lib/x86_64-linux-gnu/libncursesw.so.6.6',
    '/usr/lib/x86_64-linux-gnu/libpanelw.so.6.6',
    '/usr/lib/x86_64-linux-gnu/libpcre2-8.so.0.14.0',
    '/usr/lib/x86_64-linux-gnu/libpng16.so.16.57.0',
    '/usr/lib/x86_64-linux-gnu/libreadline.so.8.3',
    '/usr/lib/x86_64-linux-gnu/libseccomp.so.2.6.0',
    '/usr/lib/x86_64-linux-gnu/libselinux.so.1',
    '/usr/lib/x86_64-linux-gnu/libsqlite3.so.0.8.6',
    '/usr/lib/x86_64-linux-gnu/libssl.so.3',
    '/usr/lib/x86_64-linux-gnu/libtcl8.6.so',
    '/usr/lib/x86_64-linux-gnu/libtinfo.so.6.6',
    '/usr/lib/x86_64-linux-gnu/libtk8.6.so',
    '/usr/lib/x86_64-linux-gnu/libuuid.so.1.3.0',
    '/usr/lib/x86_64-linux-gnu/libxcb.so.1.1.0',
    '/usr/lib/x86_64-linux-gnu/libz.so.1.3.1',
    '/usr/lib/x86_64-linux-gnu/libzstd.so.1.5.7',
)
FIXTURE_PROFILE = {'schema':'p08-development-fixtures-1','logical_inputs':[],
                   'historical_private_inputs':False,'signing_keys_in_test_workspace':False}


def canonical(value):
    return json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=True).encode('ascii')


FIXTURE_HASH = hashlib.sha256(canonical(FIXTURE_PROFILE)).hexdigest()
BINDING_FIELDS = ('task','issuer','profile_id','source_base_commit','source_tree',
    'source_inventory_sha256','runtime_inventory_sha256','fixture_profile_sha256',
    'command_sha256','suite','attempt_id','scope')
FIELDS = set(BINDING_FIELDS)|{'schema','release_id','nonce','issued_at','not_before','expires_at'}
TERMINAL = {'CONSUMED','EXPIRED','REVOKED','REJECTED'}
NEXT = {None:{'REQUESTED'},'REQUESTED':{'ISSUED','EXPIRED','REVOKED','REJECTED'},
        'ISSUED':{'VERIFIED','EXPIRED','REVOKED','REJECTED'},
        'VERIFIED':{'RELEASED','EXPIRED','REVOKED','REJECTED'},
        'RELEASED':{'CONSUMED','EXPIRED','REVOKED','REJECTED'}}
NEW_PATHS = ('tools/tests/p08_development_release.py','tools/tests/test_p08_development_release.py')
CHANGED_PATHS = ('tools/tests/p08_qualification_runner.py',)+NEW_PATHS


class Refusal(RuntimeError):
    def __init__(self,code):
        self.code=code
        super().__init__(code)


def _require(condition,code):
    if not condition:raise Refusal(code)


def _hex(value,length):
    return type(value)is str and re.fullmatch('[0-9a-f]{'+str(length)+'}',value)is not None and value!='0'*length


def _pairs(pairs):
    result={}
    for key,value in pairs:
        if key in result:raise ValueError('duplicate field')
        result[key]=value
    return result


def _json(raw,limit,code):
    try:
        if type(raw)is not bytes or not 0<len(raw)<=limit:raise ValueError('size')
        value=json.loads(raw.decode('ascii'),object_pairs_hook=_pairs)
        if canonical(value)!=raw:raise ValueError('noncanonical')
        return value
    except (ValueError,TypeError,UnicodeError,RecursionError):
        raise Refusal(code)from None


def parse_release(raw):
    value=_json(raw,65536,'RELEASE_MALFORMED')
    _require(type(value)is dict and set(value)==FIELDS,'RELEASE_MALFORMED')
    fixed={'schema':'p08-owner-development-release-1','task':TASK,'issuer':'ORIGINAL_SYMPHONY_OWNER',
           'profile_id':PROFILE,'source_base_commit':BASE_COMMIT,'fixture_profile_sha256':FIXTURE_HASH,
           'suite':SUITE,'scope':SCOPE}
    _require(all(value[k]==v for k,v in fixed.items()),'RELEASE_MALFORMED')
    _require(all(_hex(value[k],length)for k,length in [('source_tree',40),('source_inventory_sha256',64),
        ('runtime_inventory_sha256',64),('command_sha256',64),('attempt_id',32),('release_id',32),('nonce',64)]),'RELEASE_MALFORMED')
    _require(all(type(value[k])is int and 0<=value[k]<2**63 for k in ('issued_at','not_before','expires_at')),
             'RELEASE_MALFORMED')
    _require(value['issued_at']<=value['not_before']<value['expires_at']<=value['issued_at']+900,'RELEASE_MALFORMED')
    return value


def validate_anchor(public_key,fingerprint):
    if public_key is None and fingerprint is None:raise Refusal('OWNER_TRUST_ANCHOR_UNCONFIRMED')
    try:
        if type(public_key)is not str or type(fingerprint)is not str:raise ValueError('type')
        kind,encoded=public_key.split(' ')
        wire=base64.b64decode(encoded,validate=True)
        if kind!='ssh-ed25519' or len(wire)!=51 or wire[:19]!=b'\0\0\0\x0bssh-ed25519\0\0\0\x20':raise ValueError('wire')
        actual='SHA256:'+base64.b64encode(hashlib.sha256(wire).digest()).decode().rstrip('=')
        if actual!=fingerprint:raise ValueError('fingerprint')
        if actual in ('SHA256:sWE9nA1UTKO4v7OSrRTuXx+fzN8kBCcYGdkR2EKAvXQ',
                      'SHA256:i244MzRQgsC3DSJQvFdfJHrYR/CxS+dFDbmS14cNWBA'):raise ValueError('existing account key')
        return public_key
    except (ValueError,TypeError,UnicodeError):
        raise Refusal('OWNER_TRUST_ANCHOR_INVALID')from None


def validate_binding(release,expected,now):
    _require(type(expected)is dict and set(expected)==set(BINDING_FIELDS)and
             all(release[k]==expected[k]for k in BINDING_FIELDS),'RELEASE_BINDING_MISMATCH')
    _require(type(now)is int,'RELEASE_CLOCK_UNCERTAIN')
    _require(now>=release['not_before'],'RELEASE_NOT_YET_VALID')
    _require(now<release['expires_at'],'RELEASE_EXPIRED')
    _require(0<=now-release['issued_at']<=300,'RELEASE_STALE')


def validate_transition(previous,target):
    _require(target in NEXT.get(previous,set()),'RELEASE_TRANSITION_INVALID')


def read_regular(path,limit):
    try:
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC)
    except FileNotFoundError:raise Refusal('RELEASE_INPUT_MISSING')from None
    except OSError:raise Refusal('RELEASE_INPUT_INVALID')from None
    try:
        before=os.fstat(fd)
        _require(stat.S_ISREG(before.st_mode)and before.st_nlink==1 and before.st_size<=limit,'RELEASE_INPUT_INVALID')
        raw=bytearray()
        while len(raw)<=limit:
            block=os.read(fd,min(65536,limit+1-len(raw)))
            if not block:break
            raw.extend(block)
        after=os.fstat(fd)
        identity=lambda s:(s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)
        _require(len(raw)<=limit and identity(before)==identity(after),'RELEASE_INPUT_INVALID')
        return bytes(raw)
    finally:os.close(fd)


class Journal:
    """Development durability and replay protection, not independent OS custody.

    Journal contents cannot supply authority: the launcher always independently
    checks the owner signature and exact current bindings before using them.
    """
    def __init__(self,path,release):
        self.path=Path(path);self.release=release;self.lock=None;self.dirfd=None
        self.binding=hashlib.sha256(canonical(release)).hexdigest();self.events=[]
        try:
            if not self.path.exists():self.path.mkdir(mode=0o700)
            s=self.path.lstat()
            _require(stat.S_ISDIR(s.st_mode)and s.st_uid==os.geteuid()and stat.S_IMODE(s.st_mode)==0o700,
                     'RELEASE_CUSTODY_UNCERTAIN')
            self.dirfd=os.open(self.path,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
            self.directory_identity=(s.st_dev,s.st_ino)
            self.lock=os.open('.lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_NONBLOCK|os.O_CLOEXEC,0o600,dir_fd=self.dirfd)
            try:fcntl.flock(self.lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
            except BlockingIOError:raise Refusal('RELEASE_REGISTER_BUSY')from None
            history=self.path/'history.jsonl'
            if history.exists()or history.is_symlink():
                raw=read_regular(history,1048576)
                _require(not raw or raw.endswith(b'\n'),'RELEASE_HISTORY_INVALID')
                previous=None;previous_hash='0'*64
                for index,line in enumerate(raw.splitlines()):
                    event=_json(line,65536,'RELEASE_HISTORY_INVALID')
                    _require(type(event)is dict and set(event)=={'sequence','previous','binding','state','time'},'RELEASE_HISTORY_INVALID')
                    _require(event['sequence']==index and event['previous']==previous_hash and event['binding']==self.binding and
                             type(event['time'])is int,'RELEASE_HISTORY_INVALID')
                    try:validate_transition(previous,event['state'])
                    except Refusal:raise Refusal('RELEASE_HISTORY_INVALID')from None
                    self.events.append(event);previous=event['state'];previous_hash=hashlib.sha256(line).hexdigest()
            self.check_custody()
        except BaseException:
            self.close();raise

    def check_custody(self):
        s=self.path.lstat();a=os.fstat(self.dirfd);b=os.stat('.lock',dir_fd=self.dirfd,follow_symlinks=False);c=os.fstat(self.lock)
        _require((s.st_dev,s.st_ino)==self.directory_identity==(a.st_dev,a.st_ino)and
                 stat.S_ISREG(b.st_mode)and b.st_nlink==1 and (b.st_dev,b.st_ino)==(c.st_dev,c.st_ino),
                 'RELEASE_CUSTODY_UNCERTAIN')

    @property
    def state(self):return self.events[-1]['state']if self.events else None

    def advance(self,target):
        self.check_custody();validate_transition(self.state,target)
        event={'sequence':len(self.events),'previous':hashlib.sha256(canonical(self.events[-1])).hexdigest()if self.events else'0'*64,
               'binding':self.binding,'state':target,'time':int(time.time())}
        fd=os.open('history.jsonl',os.O_WRONLY|os.O_CREAT|os.O_APPEND|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=self.dirfd)
        try:
            _require(stat.S_ISREG(os.fstat(fd).st_mode)and os.fstat(fd).st_nlink==1,'RELEASE_CUSTODY_UNCERTAIN')
            raw=canonical(event)+b'\n';_require(os.write(fd,raw)==len(raw),'RELEASE_REGISTER_UNCERTAIN');os.fsync(fd)
        finally:os.close(fd)
        os.fsync(self.dirfd);self.events.append(event)

    def reserve_once(self):
        self.check_custody()
        names=['attempt-'+self.release['attempt_id']+'.json','release-'+self.release['release_id']+'.json','nonce-'+self.release['nonce']+'.json']
        for name in names:
            try:os.stat(name,dir_fd=self.dirfd,follow_symlinks=False)
            except FileNotFoundError:continue
            raise Refusal('RELEASE_REPLAYED')
        try:
            for name in names:
                fd=os.open(name,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600,dir_fd=self.dirfd)
                try:
                    raw=canonical(self.release);_require(os.write(fd,raw)==len(raw),'RELEASE_CONSUMPTION_UNCERTAIN');os.fsync(fd)
                finally:os.close(fd)
            os.fsync(self.dirfd)
        except OSError:raise Refusal('RELEASE_CONSUMPTION_UNCERTAIN')from None

    def close(self):
        if self.lock is not None:os.close(self.lock);self.lock=None
        if self.dirfd is not None:os.close(self.dirfd);self.dirfd=None

    def __enter__(self):return self
    def __exit__(self,*unused):self.close()


def _entry(path,relative=None):
    s=path.lstat()
    _require(stat.S_ISREG(s.st_mode)and not path.is_symlink(),'SOURCE_CUSTODY_UNCERTAIN')
    raw=read_regular(path,67108864)
    after=path.lstat()
    _require((s.st_dev,s.st_ino,s.st_mode,s.st_uid,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==
             (after.st_dev,after.st_ino,after.st_mode,after.st_uid,after.st_size,after.st_mtime_ns,after.st_ctime_ns),
             'SOURCE_CUSTODY_UNCERTAIN')
    result={'path':relative or str(path),'mode':stat.S_IMODE(s.st_mode),'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
    if relative:
        # This development candidate is inside an exclusive 0700 directory.
        # Group bits on a leaf do not give another user traversal authority.
        # Record those bits separately rather than altering host permissions.
        base=path.parents[len(Path(relative).parts)-1];custody=base.lstat()
        _require(s.st_uid==os.geteuid()and not s.st_mode&0o002 and
                 custody.st_uid==os.geteuid()and stat.S_IMODE(custody.st_mode)==0o700,
                 'SOURCE_CUSTODY_UNCERTAIN')
        result['filesystem_mode']=result['mode']
        # Git records executable versus ordinary files. A private worktree's
        # umask may remove read bits without changing its Git tree identity.
        result['mode']=0o755 if s.st_mode&0o111 else 0o644
        result['git_blob']=hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    return result


def check_runtime(inventory):
    _require(type(inventory)is dict and set(inventory)=={'schema','entries','host'}and inventory['schema']=='p08-development-runtime-1'and
             type(inventory['entries'])is list and 0<len(inventory['entries'])<=20000,'RUNTIME_CUSTODY_UNCERTAIN')
    _require(inventory['host']==host_identity(),'RUNTIME_HOST_MISMATCH')
    required_paths=runtime_paths();allowed_paths=set(required_paths);seen=[]
    for entry in inventory['entries']:
        _require(type(entry)is dict and set(entry)=={'path','mode','bytes','sha256'},'RUNTIME_CUSTODY_UNCERTAIN')
        _require(type(entry['path'])is str and type(entry['mode'])is int and entry['mode']in(0o644,0o755)and
                 type(entry['bytes'])is int and 0<=entry['bytes']<=67108864 and _hex(entry['sha256'],64),
                 'RUNTIME_CUSTODY_UNCERTAIN')
        path=Path(entry['path']);s=path.lstat()
        _require(path.is_absolute()and str(path.resolve())==str(path)and s.st_uid==0 and not s.st_mode&0o022 and
                 str(path)in allowed_paths,'RUNTIME_CUSTODY_UNCERTAIN')
        _require(_entry(path)==entry,'RUNTIME_IDENTITY_MISMATCH');seen.append(str(path))
    _require(seen==required_paths,
             'RUNTIME_CUSTODY_UNCERTAIN')
    by_path={entry['path']:entry['sha256']for entry in inventory['entries']}
    _require(all(by_path[path]==identity for path,identity in EXECUTABLE_PINS.items()),'RUNTIME_PIN_MISMATCH')


def host_identity():
    _require(os.geteuid()!=0 and platform.system()=='Linux'and platform.machine()=='x86_64','RUNTIME_HOST_UNSUPPORTED')
    return {'system':platform.system(),'release':platform.release(),'machine':platform.machine(),
            'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text('ascii').strip(),
            'uid':os.geteuid(),'gid':os.getegid(),'groups':sorted(os.getgroups())}


def runtime_paths():
    # This finite profile covers the installed stdlib, its observed native
    # dependency closure, C locale and local resolver/account configuration.
    # It is not a claim about arbitrary imports or the historical R2 runtime.
    paths=set(NATIVE_RUNTIME_PATHS)
    for directory in ('/usr/lib/python3.14','/usr/lib/locale/C.utf8'):
        for path in Path(directory).rglob('*'):
            if path.is_file():paths.add(str(path.resolve(strict=True)))
    paths.update(('/etc/ld.so.cache','/etc/nsswitch.conf','/etc/passwd','/etc/group'))
    return sorted(paths)


def _tree_id(entries):
    root={}
    for entry in entries:
        parts=entry['path'].split('/');node=root
        for part in parts[:-1]:node=node.setdefault(part,{})
        node[parts[-1]]=entry
    def digest(node):
        raw=bytearray()
        for name,value in sorted(node.items(),key=lambda item:(item[0]+('/'if'git_blob'not in item[1]else'')).encode()):
            mode,identity=(format(stat.S_IFREG|value['mode'],'o'),value['git_blob'])if'git_blob'in value else('40000',digest(value))
            raw.extend(mode.encode()+b' '+name.encode()+b'\0'+bytes.fromhex(identity))
        return hashlib.sha1(b'tree '+str(len(raw)).encode()+b'\0'+raw).hexdigest()
    return digest(root)


def source_inventory(root):
    root=Path(root)
    check_directory_chain(root)
    raw=read_regular(root.parent/'owner-handoff/baseline-source.json',1048576)
    baseline=baseline_entries(_json(raw,1048576,'SOURCE_INVENTORY_INVALID'))
    expected=set(baseline)|set(NEW_PATHS);observed=set()
    for directory,dirs,files in os.walk(root,followlinks=False):
        if Path(directory)==root:dirs[:]=[x for x in dirs if x!='.p08-authority-test-output']
        for name in files:
            relative=str((Path(directory)/name).relative_to(root))
            if relative!='.git':observed.add(relative)
        _require(all(not(Path(directory)/d).is_symlink()for d in dirs),'SOURCE_CUSTODY_UNCERTAIN')
    _require(observed==expected,'SOURCE_INVENTORY_INVALID')
    entries=[_entry(root/path,path)for path in sorted(expected)]
    for entry in entries:
        if entry['path']not in CHANGED_PATHS:
            _require(all(entry[key]==baseline[entry['path']][key]for key in ('mode','bytes','git_blob','sha256')),
                     'SOURCE_IDENTITY_MISMATCH')
        else:_require(entry['mode']==0o644,'SOURCE_IDENTITY_MISMATCH')
    return {'schema':'p08-development-source-1','base_commit':BASE_COMMIT,'base_tree':BASE_TREE,
            'tree':_tree_id(entries),'entries':entries}


def check_directory_chain(path):
    path=Path(path)
    try:
        _require(path.is_absolute()and path.resolve(strict=True)==path,'RELEASE_CUSTODY_UNCERTAIN')
        for directory in (path,*path.parents):
            s=directory.lstat()
            _require(stat.S_ISDIR(s.st_mode)and s.st_uid in(0,os.geteuid())and
                     (not s.st_mode&0o022 or directory==Path('/tmp')and s.st_uid==0 and s.st_mode&stat.S_ISVTX),
                     'RELEASE_CUSTODY_UNCERTAIN')
    except FileNotFoundError:raise Refusal('RELEASE_INPUT_MISSING')from None
    except OSError:raise Refusal('RELEASE_CUSTODY_UNCERTAIN')from None


def baseline_entries(value):
    _require(type(value)is dict and set(value)=={'schema','entries'}and
             value['schema']=='p08-development-baseline-1'and type(value['entries'])is list and
             len(value['entries'])==407,'SOURCE_INVENTORY_INVALID')
    _require(hashlib.sha256(canonical(value)).hexdigest()==BASELINE_INVENTORY_SHA256,'SOURCE_INVENTORY_INVALID')
    names=[]
    for entry in value['entries']:
        _require(type(entry)is dict and set(entry)=={'path','mode','bytes','sha256','git_blob'},'SOURCE_INVENTORY_INVALID')
        path=entry['path']
        _require(type(path)is str and path and not path.startswith('/')and
                 all(part not in ('','.','..','.git')for part in path.split('/'))and
                 type(entry['mode'])is int and entry['mode']in (0o644,0o755)and
                 type(entry['bytes'])is int and 0<=entry['bytes']<=67108864 and
                 _hex(entry['sha256'],64)and _hex(entry['git_blob'],40),'SOURCE_INVENTORY_INVALID')
        names.append(path)
    _require(names==sorted(set(names))and _tree_id(value['entries'])==BASE_TREE,'SOURCE_INVENTORY_INVALID')
    return {entry['path']:entry for entry in value['entries']}


def launcher_command(root,attempt):
    _require(_hex(attempt,32),'RELEASE_ARGUMENTS_INVALID')
    bootstrap=("import sys,unittest; sys.path.insert(0,"+repr(str(root/'tools/tests'))+"); "
        "import p08_development_release as d; d.install_suite_audit("+repr(str(root))+","+repr(attempt)+"); "
        "s=unittest.defaultTestLoader.discover("+repr(str(root/'tools/tests'))+",pattern='test_p08_development_release.py'); "
        "r=unittest.TextTestRunner(verbosity=2).run(s); raise SystemExit(0 if r.wasSuccessful() else 1)")
    return [PYTHON,'-I','-S','-B','-c',bootstrap]


def select_request(args):
    _require(type(args)is list and len(args)==6 and
             args[:4]==['--profile',PROFILE,'--suite',SUITE]and args[4]=='--attempt'and _hex(args[5],32),
             'RELEASE_ARGUMENTS_INVALID')
    return args[5]


def _verify_owner_signature(root,raw,signature,namespace):
    key=validate_anchor(OWNER_CONFIRMED_PUBLIC_KEY,OWNER_CONFIRMED_FINGERPRINT)
    _require(0<len(signature)<=4096,'OWNER_SIGNATURE_INVALID')
    _require(hashlib.sha256(read_regular(Path(SSH),16777216)).hexdigest()==SSH_SHA256,'SIGNATURE_VERIFIER_MISMATCH')
    control=root.parent/'verification';control.mkdir(mode=0o700,exist_ok=True)
    directory=control/str(os.getpid());directory.mkdir(mode=0o700,exist_ok=True)
    check_directory_chain(directory)
    public=directory/'allowed-signers';sigpath=directory/('revocation.sshsig'if namespace==REVOCATION_NAMESPACE else'release.sshsig')
    public_raw=('symphony-owner-development namespaces="'+NAMESPACE+','+REVOCATION_NAMESPACE+'" '+key+'\n').encode('ascii')
    for path,data in ((public,public_raw),(sigpath,signature)):
        if path.exists():_require(read_regular(path,4096)==data,'RELEASE_CUSTODY_UNCERTAIN')
        else:
            fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
            try:_require(os.write(fd,data)==len(data),'RELEASE_CUSTODY_UNCERTAIN');os.fsync(fd)
            finally:os.close(fd)
    argv=[SSH,'-Y','verify','-f',str(public),'-I','symphony-owner-development','-n',namespace,'-s',str(sigpath)]
    env={'PATH':'/nonexistent','HOME':str(root.parent),'LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
    p=subprocess.run(argv,input=raw,capture_output=True,env=env,timeout=5,check=False)
    _require(len(p.stdout)<=4096 and len(p.stderr)<=4096,'OWNER_SIGNATURE_INVALID')
    evidence={'argv':argv,'exit_code':p.returncode,'stdout':p.stdout.decode('ascii','backslashreplace'),
              'stderr':p.stderr.decode('ascii','backslashreplace'),'input_sha256':hashlib.sha256(raw).hexdigest()}
    (directory/('verification-'+str(time.time_ns())+'.json')).write_bytes(canonical(evidence))
    _require(p.returncode==0,'OWNER_SIGNATURE_INVALID')


def check_revocation(root,release):
    handoff=root.parent/'owner-handoff';path=handoff/'revocation.json';signature=handoff/'revocation.sshsig'
    present=os.path.lexists(path);signature_present=os.path.lexists(signature)
    _require(present==signature_present,'OWNER_REVOCATION_UNCERTAIN')
    if not present:return
    raw=read_regular(path,65536);value=_json(raw,65536,'OWNER_REVOCATION_INVALID')
    _require(type(value)is dict and set(value)=={'schema','release_id','attempt_id','nonce','revoked_at'}and
             value['schema']=='p08-owner-development-revocation-1'and
             all(value[k]==release[k]for k in ('release_id','attempt_id','nonce'))and
             type(value['revoked_at'])is int and 0<=value['revoked_at']<=int(time.time()),'OWNER_REVOCATION_INVALID')
    _verify_owner_signature(root,raw,read_regular(signature,4096),REVOCATION_NAMESPACE)
    raise Refusal('RELEASE_REVOKED')


def authenticate(root,attempt):
    # This is deliberately first: no request JSON can configure or approve a key.
    validate_anchor(OWNER_CONFIRMED_PUBLIC_KEY,OWNER_CONFIRMED_FINGERPRINT)
    _require(_hex(attempt,32),'RELEASE_ARGUMENTS_INVALID')
    root=Path(root);handoff=root.parent/'owner-handoff'
    check_directory_chain(root);check_directory_chain(handoff)
    raw=read_regular(handoff/'release.json',65536);release=parse_release(raw)
    _verify_owner_signature(root,raw,read_regular(handoff/'release.sshsig',4096),NAMESPACE)
    runtime_raw=read_regular(handoff/'runtime-inventory.json',16777216)
    runtime=_json(runtime_raw,16777216,'RUNTIME_INVENTORY_INVALID');check_runtime(runtime)
    source=source_inventory(root)
    expected={key:release[key]for key in BINDING_FIELDS}
    expected.update(source_tree=source['tree'],source_inventory_sha256=hashlib.sha256(canonical(source)).hexdigest(),
        runtime_inventory_sha256=hashlib.sha256(runtime_raw).hexdigest(),fixture_profile_sha256=FIXTURE_HASH,
        command_sha256=hashlib.sha256(canonical(launcher_command(root,attempt))).hexdigest(),attempt_id=attempt)
    validate_binding(release,expected,int(time.time()));check_revocation(root,release)
    return release


def prepare_launch(root,attempt):
    root=Path(root)
    release=authenticate(root,attempt)
    require_host_custody(root,release)
    with Journal(root.parent/'authority-state',release)as journal:
        _require(journal.state is None,'RELEASE_REPLAYED')
        journal.advance('REQUESTED');journal.advance('ISSUED');journal.advance('VERIFIED')
        # Re-read exact source/runtime/owner records at the final admission point.
        try:
            _require(authenticate(root,attempt)==release,'RELEASE_BINDING_MISMATCH')
            journal.advance('RELEASED');journal.reserve_once();journal.advance('CONSUMED')
        except BaseException as error:
            state={'RELEASE_EXPIRED':'EXPIRED','RELEASE_REVOKED':'REVOKED'}.get(getattr(error,'code',None),'REJECTED')
            if journal.state not in TERMINAL:journal.advance(state)
            raise
    return release


def require_host_custody(root,release):
    """The existing trusted host must own consumption and launcher receipts.

    A source-account-writable journal/child.json can be reset or forged by that
    account. It is useful development state, never independent host authority.
    No installed, owner-appointed host handoff was established by the read-only
    inventory. A public-key pin alone must not enable this unqualified path.
    There is deliberately no callback, Boolean or JSON override for this gate.
    """
    raise Refusal('DEVELOPMENT_HOST_CUSTODY_UNCONFIGURED')


def register_child(root,release,pid):
    record={'attempt_id':release['attempt_id'],'release_sha256':hashlib.sha256(canonical(release)).hexdigest(),
            'parent':os.getpid(),'parent_start':_process_start(os.getpid()),'child':pid,'child_start':_process_start(pid)}
    path=root.parent/'authority-state'/'child.json'
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        raw=canonical(record);_require(os.write(fd,raw)==len(raw),'RELEASE_REGISTER_UNCERTAIN');os.fsync(fd)
    finally:os.close(fd)


def _process_start(pid):
    raw=Path('/proc/'+str(pid)+'/stat').read_text('ascii')
    return int(raw[raw.rfind(')')+2:].split()[19])


def install_suite_audit(root,attempt):
    root=Path(root);release=authenticate(root,attempt)
    with Journal(root.parent/'authority-state',release)as journal:
        _require(journal.state=='CONSUMED','EXECUTION_RECEIPT_INVALID')
    record=_json(read_regular(root.parent/'authority-state/child.json',65536),65536,'EXECUTION_RECEIPT_INVALID')
    _require(record=={'attempt_id':attempt,'release_sha256':hashlib.sha256(canonical(release)).hexdigest(),
        'parent':os.getppid(),'parent_start':_process_start(os.getppid()),'child':os.getpid(),'child_start':_process_start(os.getpid())},
        'EXECUTION_RECEIPT_INVALID')
    install_output_audit(root/'.p08-authority-test-output')


def install_output_audit(output):
    """Python write checks only. This is not kernel filesystem containment."""
    output=Path(output).resolve(strict=True)
    original_open=os.open
    log=original_open(output/('write-audit-'+str(os.getpid())+'.jsonl'),
        os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    write_flags=os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND
    def absolute(path,dir_fd=None):
        path=Path(os.fsdecode(path))
        if not path.is_absolute():
            base=Path.cwd()if dir_fd in (None,-1)else Path('/proc/self/fd/'+str(dir_fd)).resolve(strict=True)
            if dir_fd not in (None,-1):
                _require(stat.S_ISDIR(os.fstat(dir_fd).st_mode),'DEVELOPMENT_WRITE_DENIED')
            path=base/path
        return Path(os.path.abspath(path))
    def allowed(path,dir_fd=None,follow_leaf=False):
        path=absolute(path,dir_fd)
        target=path.resolve()if follow_leaf else path.parent.resolve()/path.name
        permit=target==output or output in target.parents
        os.write(log,canonical({'path':str(path),'resolved':str(target),'allowed':permit})+b'\n')
        _require(permit,'DEVELOPMENT_WRITE_DENIED')
        return path
    def guarded_open(path,flags,mode=0o777,*,dir_fd=None):
        if flags&write_flags:
            # CPython's open audit event omits dir_fd. Convert the checked
            # directory-relative write to its exact absolute spelling first.
            path=allowed(path,dir_fd,True);dir_fd=None
        return original_open(path,flags,mode,dir_fd=dir_fd)
    os.open=guarded_open
    def audit(event,args):
        if event=='open'and not isinstance(args[0],int)and args[2]&write_flags:allowed(args[0],follow_leaf=True)
        elif event in ('os.remove','os.rmdir'):allowed(args[0],args[1])
        elif event in ('os.mkdir','os.chmod'):allowed(args[0],args[2],event=='os.chmod')
        elif event=='os.truncate'and not isinstance(args[0],int):allowed(args[0],follow_leaf=True)
        elif event in ('os.rename','os.link'):
            allowed(args[0],args[2]);allowed(args[1],args[3])
        elif event=='os.symlink':allowed(args[1],args[2])
    sys.addaudithook(audit)


def permitted_verification(argv,root,suite_pid):
    # Child authentication can only invoke the pinned verifier on its own public
    # handoff copy. No signing operation or selectable verifier is admitted.
    directory=root.parent/'verification'/str(suite_pid)
    return (len(argv)==11 and argv[:4]==[SSH,'-Y','verify','-f']and
        argv[4]==str(directory/'allowed-signers')and argv[5:8]==['-I','symphony-owner-development','-n']and
        argv[8]in(NAMESPACE,REVOCATION_NAMESPACE)and argv[9]=='-s'and
        argv[10]==str(directory/('revocation.sshsig'if argv[8]==REVOCATION_NAMESPACE else'release.sshsig')))


# D02 describes a host-owned protocol. The production provider remains absent.
# CooperativeHostChannel is solely the explicitly authorized test-double
# transport. Same-UID peer credentials do not establish independent custody.
HOST_OPERATIONS = frozenset({'CONSUME','REGISTER_CHILD','CHILD_READY','POLL','COMPLETE'})
HOST_STATES = frozenset({'REQUESTED','ISSUED','VERIFIED','RELEASED','CONSUMED','EXPIRED','REVOKED','REJECTED'})


@dataclass(frozen=True)
class HostReply:
    operation: str
    attempt_id: str
    generation: str
    state: str
    record: dict
    error: str | None


def parse_host_reply(raw,request_id,attempt,operation,generation):
    value=_json(raw,65536,'HOST_REPLY_INVALID')
    expected={'schema':'p08-host-reply-1','request_id':request_id,'attempt_id':attempt,
              'op':operation,'generation':generation,'authority_class':'COOPERATIVE_DEVELOPMENT_ONLY'}
    _require(type(value)is dict and set(value)==set(expected)|{'state','record','error'}and
             all(value[key]==item for key,item in expected.items())and
             type(value['state'])is str and value['state']in HOST_STATES and
             type(value['record'])is dict and (value['error']is None or type(value['error'])is str and
             re.fullmatch('[A-Z_]{1,80}',value['error'])is not None),'HOST_REPLY_INVALID')
    _require(value['error']is not None or value['state']=='CONSUMED','HOST_REPLY_INVALID')
    return HostReply(operation,attempt,generation,value['state'],value['record'],value['error'])


class ProductionHostHandoff:
    """No authority provider, endpoint, callback or trust selector is installed."""
    def exchange(self,operation,attempt,payload):
        raise Refusal('DEVELOPMENT_HOST_CUSTODY_UNCONFIGURED')


class CooperativeHostChannel:
    """Finite preconnected test transport, never an independent authority claim.

    The host process owns signature verification, binding, state, consumption,
    live status and receipts. Each operation and reply has an exact schema and
    correlation identity. The child inherits only its dedicated connection;
    it cannot connect to arbitrary Unix sockets through the execution filter.
    """
    def __init__(self,connection,peer_pid,peer_start,generation):
        import socket
        import struct
        _require(_hex(generation,32),'HOST_PEER_INVALID')
        pid,uid,gid=struct.unpack('3i',connection.getsockopt(socket.SOL_SOCKET,socket.SO_PEERCRED,12))
        _require(pid==peer_pid and uid==os.geteuid()and _process_start(pid)==peer_start,'HOST_PEER_INVALID')
        self.connection=connection;self.generation=generation
        self.peer_pid=peer_pid;self.peer_start=peer_start
        connection.settimeout(15)

    def exchange(self,operation,attempt,payload):
        import socket
        _require(type(operation)is str and operation in HOST_OPERATIONS and
                 _hex(attempt,32)and type(payload)is dict,'HOST_REQUEST_INVALID')
        request_id=os.urandom(16).hex()
        raw=canonical({'schema':'p08-host-request-1','op':operation,'attempt_id':attempt,
                       'request_id':request_id,'payload':payload})
        _require(len(raw)<=65536,'HOST_REQUEST_INVALID')
        try:
            _require(_process_start(self.peer_pid)==self.peer_start,'HOST_PEER_INVALID')
            _require(self.connection.sendmsg([raw])==len(raw),'HOST_SERVICE_UNAVAILABLE')
            response,unused,flags,address=self.connection.recvmsg(65537)
            _require(response and not flags&socket.MSG_TRUNC,'HOST_SERVICE_UNAVAILABLE')
        except (OSError,ValueError):
            raise Refusal('HOST_SERVICE_UNAVAILABLE')from None
        reply=parse_host_reply(response,request_id,attempt,operation,self.generation)
        if reply.error:raise Refusal(reply.error)
        return reply

    def close(self):
        self.connection.close()
