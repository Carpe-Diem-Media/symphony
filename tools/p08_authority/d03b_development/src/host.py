"""Owner-mediated D03 host adapter. No daemon or generic worker-admin API.

Installation, owner trust/route enrollment and root execution require another
owner decision. No part of this module activates production Package B admission.
"""
import os
from pathlib import Path
import sys

DEPLOYMENT=Path('/var/lib/software-factory/p08-r1b-host-dev/P08-R1B-HOST-DEV-01')
if __name__=='__main__':
    if os.geteuid()!=0:print('HOST_ROOT_REQUIRED',file=sys.stderr);raise SystemExit(2)
    if Path(__file__).resolve()!=DEPLOYMENT/'src/host.py':
        print('HOST_DEPLOYMENT_UNPROVEN',file=sys.stderr);raise SystemExit(2)
    for path in [Path(__file__),*Path(__file__).parents]:
        s=path.lstat()
        if s.st_uid!=0 or s.st_mode&0o022 or path.is_symlink():
            print('HOST_CUSTODY_UNPROVEN',file=sys.stderr);raise SystemExit(2)

sys.path.insert(0,str(Path(__file__).resolve().parent))
import argparse
import base64
import fcntl
import hashlib
import json
import select
import stat
import subprocess
import time
from contract import (BINDINGS,CAMPAIGN,D02_TREE,HASH_FIELDS,NAMESPACE,ROOT,ROUTE_NAMESPACE,SUITE,
    Refusal,SourceRouteEnrollment,canonical,check_binding,check_pid1_exit,check_root_metadata,
    check_worker_route,digest,hex_id,parse_json,parse_release,require,require_source_route_enrollment,
    unit_name,worker_properties)
from ledger import Register
from native_executor import EXECUTOR,NativeExecutor,NativeOperation
from build_image import image_inventory,normalized

SSH='/usr/bin/ssh-keygen'
SSH_SHA256='2dd834413c9d3f4c0e3535b9fcf2e96e14c11f3d36fd23b6c5fc24e50411d051'
ENV={'PATH':'/nonexistent','HOME':'/nonexistent','LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
     'SYSTEMD_PAGER':'cat','SYSTEMD_COLORS':'0'}


def root_chain(path):
    path=Path(path)
    require(path.is_absolute() and path.resolve(strict=True)==path,'HOST_CUSTODY_UNPROVEN')
    for directory in [path,*path.parents]:
        s=directory.lstat()
        require(s.st_uid==0 and not s.st_mode&0o022 and not directory.is_symlink(),'HOST_CUSTODY_UNPROVEN')


def root_read(path,limit=1048576):
    path=Path(path)
    try:
        root_chain(path.parent)
        fd=os.open(path,os.O_RDONLY|os.O_NOFOLLOW|os.O_CLOEXEC|os.O_NONBLOCK)
        try:
            s=os.fstat(fd)
            check_root_metadata({'uid':s.st_uid,'mode':stat.S_IMODE(s.st_mode),'regular':stat.S_ISREG(s.st_mode),
                'nlink':s.st_nlink,'alias':path.is_symlink()})
            require(0<=s.st_size<=limit,'HOST_INPUT_SIZE')
            raw=os.read(fd,limit+1);after=os.fstat(fd)
            require(len(raw)==s.st_size and (s.st_dev,s.st_ino,s.st_size,s.st_mtime_ns,s.st_ctime_ns)==
                (after.st_dev,after.st_ino,after.st_size,after.st_mtime_ns,after.st_ctime_ns),'HOST_INPUT_CHANGED')
            return raw
        finally:os.close(fd)
    except OSError:raise Refusal('HOST_CUSTODY_UNPROVEN') from None


def public_fingerprint(key):
    try:
        require(type(key)is str and len(key)<256 and key.split(' ')==key.split() and
                len(key.split())==2 and key.split()[0]=='ssh-ed25519','OWNER_KEY_INVALID')
        blob=base64.b64decode(key.split()[1],validate=True)
        require(len(blob)==51 and blob[:19]==b'\x00\x00\x00\x0bssh-ed25519\x00\x00\x00\x20','OWNER_KEY_INVALID')
        return 'SHA256:'+base64.b64encode(hashlib.sha256(blob).digest()).decode().rstrip('=')
    except (ValueError,TypeError):raise Refusal('OWNER_KEY_INVALID') from None


def verify_signature_component(payload,signature,allowed,identity,namespace):
    """Crypto component only. The live caller separately requires root custody."""
    require(digest(Path(SSH).read_bytes())==SSH_SHA256,'VERIFIER_CHANGED')
    raw=Path(payload).read_bytes();require(0<len(raw)<=65536,'SIGNATURE_INPUT_SIZE')
    argv=[SSH,'-Y','verify','-f',str(allowed),'-I',identity,'-n',namespace,'-s',str(signature)]
    process=subprocess.run(argv,input=raw,env=ENV,capture_output=True,timeout=5)
    return {'argv':argv,'exit_code':process.returncode,'stdout':process.stdout.decode(),
            'stderr':process.stderr.decode(),'payload_sha256':digest(raw)}


def parse_route_approval(raw,bindings,now):
    value=parse_json(raw,'SOURCE_ROUTE_UNPROVEN')
    fields={'schema','campaign','boot_id','route_manifest_sha256','source_session',
            'route','unrestricted_tool_route','issued_at','expires_at'}
    require(type(value)is dict and set(value)==fields and value['schema']=='p08-source-route-owner-handoff-1' and
        value['campaign']==CAMPAIGN and value['boot_id']==bindings.get('boot_id') and
        value['route']=='SYSTEMD_TRANSIENT_FIXED_COMMAND_ONLY' and
        value['unrestricted_tool_route']=='UNCHANGED_OUTSIDE_FIXED_WORKER' and
        value['source_session']=='01a1c3c2-5be2-7173-bec3-90a2ee0ea021' and
        hex_id(value['route_manifest_sha256'],64) and type(value['issued_at'])is int and
        type(value['expires_at'])is int and value['issued_at']<=now<value['expires_at']<=value['issued_at']+600,
        'SOURCE_ROUTE_UNPROVEN')
    return SourceRouteEnrollment(CAMPAIGN,value['boot_id'],value['route_manifest_sha256'],digest(raw),value['expires_at'])


def properties(raw):
    result={}
    for line in raw.decode().splitlines():
        key,separator,value=line.partition('=')
        require(separator and key not in result,'PID1_REPLY_INVALID');result[key]=value
    return result


def recovery_disposition(row,props,cgroup_exists):
    detail=json.loads(row['detail']);attempt=row['attempt']
    if props.get('LoadState')=='not-found':
        require(cgroup_exists is False,'RECOVERY_UNCERTAIN')
        return 'UNIT_AND_CGROUP_ABSENT'
    token=detail.get('launch_token')
    require(hex_id(token,64) and props.get('Id')==unit_name(attempt) and props.get('Transient')=='yes' and
        props.get('Description')=='p08-d03:'+attempt+':'+token and hex_id(props.get('InvocationID'),32) and
        props.get('RootDirectory')==str(DEPLOYMENT/'image') and
        props.get('ControlGroup')=='/system.slice/'+unit_name(attempt),'RECOVERY_UNCERTAIN')
    if detail.get('invocation') is not None:
        require(detail['invocation']==props['InvocationID'],'UNIT_INCARNATION_UNCERTAIN')
    return 'STOP_MATCHED_UNIT'


def check_launch_identity(props,attempt,token,previous=None,require_pid=True):
    """Bind a stable PID1 incarnation to this exact consumed launch token."""
    require(hex_id(attempt,32) and hex_id(token,64),'UNIT_INCARNATION_UNCERTAIN')
    require(props.get('Id')==unit_name(attempt) and props.get('Transient')=='yes' and
        props.get('Description')=='p08-d03:'+attempt+':'+token and
        hex_id(props.get('InvocationID'),32) and props['InvocationID']!='0'*32 and
        props.get('RootDirectory')==str(DEPLOYMENT/'image') and
        props.get('ControlGroup')=='/system.slice/'+unit_name(attempt),'UNIT_INCARNATION_UNCERTAIN')
    if require_pid:
        require(type(props.get('MainPID')) is str and props['MainPID'].isdigit() and
                int(props['MainPID'])>0,'WORKER_OBSERVATION_MISSING')
    if previous is not None:
        fields=['Id','Transient','Description','InvocationID','RootDirectory','ControlGroup']
        if require_pid:fields.append('MainPID')
        require(all(props.get(key)==previous.get(key) for key in fields),'WORKER_OBSERVATION_CHANGED')
    return props['InvocationID']


class Host:
    """Live root-only adapter. No test mode, verifier callback or path selector."""
    def __init__(self):
        require(os.geteuid()==0,'HOST_ROOT_REQUIRED');os.umask(0o077)
        root_chain(DEPLOYMENT)
        for name in ['state','receipts','context','releases','revocations']:
            directory=DEPLOYMENT/name;root_chain(directory)
            require(directory.is_dir() and stat.S_IMODE(directory.stat().st_mode)==0o700,'HOST_CUSTODY_UNPROVEN')
        raw=root_read(DEPLOYMENT/'owner-settings.json');self.settings=parse_json(raw)
        s=self.settings
        require(type(s)is dict and set(s)=={'schema','public_key','fingerprint','bindings','tools','valid_from','expires_at'},'OWNER_SETTINGS_INVALID')
        require(s['schema']=='p08-d03-owner-settings-1' and s['public_key']is not None and s['fingerprint']is not None,
                'OWNER_TRUST_UNCONFIGURED')
        require(public_fingerprint(s['public_key'])==s['fingerprint'],'OWNER_KEY_MISMATCH')
        self.bindings=s['bindings'];require(type(self.bindings)is dict and set(self.bindings)==BINDINGS,'OWNER_SETTINGS_INVALID')
        require(self.bindings['source_tree']==D02_TREE and self.bindings['boot_id']==Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
                'HOST_BOOT_MISMATCH')
        require(type(s['valid_from'])is int and type(s['expires_at'])is int and
                s['valid_from']<=time.time()<s['expires_at']<=s['valid_from']+600,'CAMPAIGN_NOT_EFFECTIVE')
        expected=('symphony-owner-d03 '+s['public_key']+'\n').encode()
        require(root_read(DEPLOYMENT/'owner-allowed-signers',4096)==expected,'OWNER_KEY_MISMATCH')
        require(set(s['tools'])=={str(EXECUTOR),SSH,'/usr/bin/python3.14'},'HOST_TOOLS_INVALID')
        for path,identity in s['tools'].items():require(digest(root_read(path,67108864))==identity,'HOST_TOOL_CHANGED')
        self.verify_manifest('host-source-manifest.json','host_source_sha256',DEPLOYMENT/'src')
        self.verify_manifest('host-runtime-manifest.json','runtime_manifest_sha256',Path('/'))
        image_raw=root_read(DEPLOYMENT/'image-manifest.json',2097152)
        require(digest(image_raw)==self.bindings['image_manifest_sha256'],'IMAGE_IDENTITY_MISMATCH')
        image=parse_json(image_raw,limit=2097152)
        check_image_runtime(image,self.bindings)
        require(digest(root_read(DEPLOYMENT/'worker-runtime-input.json',2097152))==self.bindings['worker_runtime_sha256'],'WORKER_RUNTIME_MISMATCH')
        require(image.get('schema')=='p08-d03-worker-image-1' and image.get('source_tree')==D02_TREE and
                normalized(image_inventory(DEPLOYMENT/'image'))==image.get('entries'),'IMAGE_IDENTITY_MISMATCH')
        for path in (DEPLOYMENT/'image').rglob('*'):require(path.lstat().st_uid==0,'IMAGE_CUSTODY_UNPROVEN')
        root_chain(DEPLOYMENT/'image')
        require(digest(root_read(DEPLOYMENT/'profile.json'))==self.bindings['profile_sha256'] and
            digest(root_read(DEPLOYMENT/'fixture-profile.json'))==self.bindings['fixture_profile_sha256'],'PROFILE_MISMATCH')
        route_raw=root_read(DEPLOYMENT/'route-approval.json')
        require(digest(route_raw)==self.bindings['route_approval_sha256'],'SOURCE_ROUTE_UNPROVEN')
        self.signature(DEPLOYMENT/'route-approval.json',DEPLOYMENT/'route-approval.sig',ROUTE_NAMESPACE,digest(route_raw))
        self.route=require_source_route_enrollment(parse_route_approval(route_raw,self.bindings,time.time()))
        require(digest(root_read(DEPLOYMENT/'source-route-manifest.json'))==self.route.route_manifest_sha256,'SOURCE_ROUTE_UNPROVEN')
        self.previous_clock=time.time();self.records=[];self.executor=None

    def verify_manifest(self,name,binding,base):
        raw=root_read(DEPLOYMENT/name,2097152);require(digest(raw)==self.bindings[binding],'HOST_MANIFEST_MISMATCH')
        manifest=parse_json(raw,limit=2097152)
        require(type(manifest)is dict and set(manifest)=={'schema','files'} and type(manifest['files'])is list,'HOST_MANIFEST_INVALID')
        names=[]
        for entry in manifest['files']:
            require(type(entry)is dict and set(entry)=={'path','bytes','sha256'} and type(entry['path'])is str and
                entry['path'] and not entry['path'].startswith('/') and all(p not in ('','.','..') for p in entry['path'].split('/')),
                'HOST_MANIFEST_INVALID')
            value=root_read(base/entry['path'],67108864)
            require(len(value)==entry['bytes'] and digest(value)==entry['sha256'],'HOST_MANIFEST_MISMATCH');names.append(entry['path'])
        require(names==sorted(set(names)) and names,'HOST_MANIFEST_INVALID')
        if base==DEPLOYMENT/'src':require(set(names)=={str(p.relative_to(base)) for p in base.rglob('*') if p.is_file()},'HOST_MANIFEST_MISMATCH')

    def signature(self,payload,signature,namespace,expected_sha256):
        root_read(payload);root_read(signature,4096);root_read(DEPLOYMENT/'owner-allowed-signers',4096)
        value=verify_signature_component(payload,signature,DEPLOYMENT/'owner-allowed-signers','symphony-owner-d03',namespace)
        require(value['exit_code']==0,'OWNER_SIGNATURE_INVALID')
        require(value['payload_sha256']==expected_sha256 and digest(root_read(payload))==expected_sha256,'RELEASE_INPUT_CHANGED')
        return value

    def native(self, operation):
        require(type(operation) is NativeOperation,'HOST_COMMAND_INVALID')
        require(digest(root_read(EXECUTOR,67108864))==self.settings['tools'][str(EXECUTOR)],'HOST_TOOL_CHANGED')
        if self.executor is None:self.executor=NativeExecutor()
        value=self.executor.exchange(operation)
        self.records.append({'operation':operation.value,'reply':value})
        return value

    def show(self,attempt):
        unit_name(attempt)
        return self.native(NativeOperation.SHOW)

    def observe(self,attempt,props,invocation):
        pid=int(props.get('MainPID','0'));require(pid>0,'WORKER_OBSERVATION_MISSING')
        proc=Path('/proc')/str(pid)
        status=dict(line.split(':',1) for line in (proc/'status').read_text().splitlines() if ':' in line)
        uids=[int(v) for v in status['Uid'].split()];gids=[int(v) for v in status['Gid'].split()]
        require(len(set(uids))==len(set(gids))==1,'WORKER_ROUTE_UNPROVEN')
        from contract import check_worker_environment
        environment=dict(item.split('=',1) for item in (proc/'environ').read_bytes().decode('ascii').strip('\0').split('\0') if item)
        check_worker_environment(environment,invocation)
        cgroup='/system.slice/'+unit_name(attempt)
        descriptors={int(p.name):os.readlink(p) for p in (proc/'fd').iterdir()}
        expected_fds={0:'/dev/null',1:str(DEPLOYMENT/'receipts'/(attempt+'.stdout')),2:str(DEPLOYMENT/'receipts'/(attempt+'.stderr'))}
        required={'DynamicUser':'yes','NoNewPrivileges':'yes','CapabilityBoundingSet':'','AmbientCapabilities':'',
            'SupplementaryGroups':'','PrivateNetwork':'yes','PrivateDevices':'yes','ProtectSystem':'strict',
            'PrivateTmp':'yes','PrivateIPC':'yes','ProtectHome':'yes','ProtectControlGroups':'yes',
            'ProtectKernelTunables':'yes','ProtectKernelModules':'yes','ProtectKernelLogs':'yes',
            'RestrictSUIDSGID':'yes','RestrictRealtime':'yes','LockPersonality':'yes',
            'RestrictAddressFamilies':'AF_UNIX','KillMode':'control-group','RuntimeMaxUSec':'20000000',
            'TimeoutStopUSec':'2000000','ProtectProc':'invisible','ProcSubset':'pid',
            'KillMode':'control-group','Delegate':'no','RootDirectory':str(DEPLOYMENT/'image'),
            'TasksMax':'16','MemoryMax':'268435456'}
        cgroup_path=Path('/sys/fs/cgroup')/cgroup.lstrip('/')
        cpu=(cgroup_path/'cpu.max').read_text().split()
        require(len(cpu)==2 and all(value.isdigit() for value in cpu) and 0<int(cpu[0])*2<=int(cpu[1]) and
            (cgroup_path/'memory.max').read_text().strip()=='268435456' and
            (cgroup_path/'pids.max').read_text().strip()=='16','RESOURCE_PROFILE_UNPROVEN')
        value={'uid':uids[0],'gid':gids[0],'groups':[int(v) for v in status['Groups'].split()],
            'nnp':int(status['NoNewPrivs']),'caps':[int(status[key],16) for key in ['CapInh','CapPrm','CapEff','CapBnd','CapAmb']],
            'mount_private':os.readlink(proc/'ns/mnt')!=os.readlink('/proc/1/ns/mnt'),
            'network_private':os.readlink(proc/'ns/net')!=os.readlink('/proc/1/ns/net'),
            'initial_user_namespace':(proc/'uid_map').read_text().split()==['0','0','4294967295'],
            'root_matches':os.stat(proc/'root')[:3]==os.stat(DEPLOYMENT/'image')[:3],
            'cgroup_matches':(proc/'cgroup').read_text().strip()=='0::'+cgroup and props.get('ControlGroup')==cgroup,
            'stdio_only':descriptors==expected_fds,'unit_profile_matches':all(props.get(k)==v for k,v in required.items()),
            'invocation_matches':props.get('InvocationID')==invocation}
        check_worker_route(value)
        return {'route':value,'pid':pid,'start':(proc/'stat').read_text().rsplit(')',1)[1].split()[19],
                'invocation':invocation,'cgroup':cgroup,'profile':props,'cpu.max':cpu,'environment_names':sorted(environment)}

    def populated(self,attempt):
        path=Path('/sys/fs/cgroup/system.slice')/unit_name(attempt)
        if confirmed_absent(path):return False
        require(path.resolve(strict=True)==path,'CGROUP_UNCERTAIN')
        values=dict(line.split() for line in (path/'cgroup.events').read_text().splitlines())
        require(values.get('populated') in ['0','1'],'CGROUP_UNCERTAIN')
        return values['populated']=='1'

    def stop(self,attempt,invocation):
        props=self.show(attempt)
        require(props.get('InvocationID')==invocation,'UNIT_INCARNATION_UNCERTAIN')
        require(self.native(NativeOperation.STOP)=={'Stopped':'yes'},'HOST_STOP_UNCERTAIN')

    def recover(self,row):
        detail=json.loads(row['detail']);props=self.show(row['attempt'])
        cgroup=Path('/sys/fs/cgroup/system.slice')/unit_name(row['attempt'])
        disposition=recovery_disposition(row,props,not confirmed_absent(cgroup))
        if disposition=='UNIT_AND_CGROUP_ABSENT':return {'reason':disposition,'PID1':props,'previous':detail,'cleanup':self.cleanup_witness(row['attempt'])}
        invocation=props['InvocationID'];self.stop(row['attempt'],invocation)
        after=self.show(row['attempt'])
        require((confirmed_absent(cgroup) and after.get('LoadState')=='not-found') or
            (after.get('InvocationID')==invocation and not self.populated(row['attempt'])),'RECOVERY_UNCERTAIN')
        require(self.native(NativeOperation.UNREF)=={'ReferenceReleased':'yes'},'CLEANUP_UNCERTAIN')
        return {'reason':'RECOVERED_INTERRUPTED','PID1':after,'previous':detail,'cleanup':self.cleanup_witness(row['attempt'])}

    def launch(self,attempt,ledger):
        path=DEPLOYMENT/'releases'/(attempt+'.json')
        raw=root_read(path);release=parse_release(raw);require(release['attempt_id']==attempt,'RELEASE_BINDING_MISMATCH')
        require(self.show(attempt).get('LoadState')=='not-found','UNIT_COLLISION')
        require(ledger.get(attempt)is None,'RELEASE_REPLAYED');ledger.request(release)
        self.signature(path,path.with_suffix('.sig'),NAMESPACE,digest(raw));ledger.advance(attempt,'ISSUED')
        self.check_live(release);ledger.advance(attempt,'VERIFIED');ledger.consume(attempt)
        invocation=None;pidfd=None;observation=None
        token=digest(canonical(release))
        try:
            # Reserve protected root-owned, single-link outputs before PID1
            # opens them. No worker can replace names in this 0700 directory.
            for suffix in ['.stdout','.stderr']:exclusive_write(DEPLOYMENT/'receipts'/(attempt+suffix),b'')
            context=canonical({'attempt_id':attempt,'release_sha256':digest(canonical(release)),
                'host_admission':'CONSUMED_BEFORE_PID1_START'})
            exclusive_write(DEPLOYMENT/'context'/(attempt+'.json'),context)
            ledger.execution(attempt,'LAUNCHING',{'unit':unit_name(attempt),'launch_token':token})
            exclusive_write(DEPLOYMENT/'state/active-attempt',(attempt+'\n'+token+'\n').encode('ascii'))
            require(self.native(NativeOperation.CREATE)=={'Created':'yes'},'PID1_LAUNCH_FAILED')
            props=self.show(attempt);invocation=check_launch_identity(props,attempt,token)
            pid=int(props.get('MainPID','0'));require(pid>0,'WORKER_OBSERVATION_MISSING')
            pidfd=os.pidfd_open(pid)
            observation=self.observe(attempt,props,invocation)
            refreshed=self.show(attempt)
            check_launch_identity(refreshed,attempt,token,props)
            require(not select.select([pidfd],[],[],0)[0],'WORKER_OBSERVATION_CHANGED')
            # The original pidfd is still live after /proc observation, so this
            # start identity belongs to the pinned process, not a reused PID.
            require(type(observation) is dict and type(observation.get('pid')) is int and
                observation['pid']==pid and observation.get('invocation')==invocation and
                type(observation.get('start')) is str and observation['start'].isascii() and
                observation['start'].isdigit() and int(observation['start'])>0,
                'WORKER_PROCESS_IDENTITY_UNPROVEN')
            pinned_worker={'pid':pid,'start':observation['start'],'invocation':invocation}
            observation['launch_token']=token
            ledger.execution(attempt,'RUNNING',observation)
            deadline=time.monotonic()+22
            while time.monotonic()<deadline:
                self.check_live(release)
                if select.select([pidfd],[],[],0.05)[0]:break
            else:raise Refusal('WORKER_DEADLINE')
            props=self.show(attempt)
            check_launch_identity(props,attempt,token,refreshed,require_pid=False)
            exit_code=check_pid1_exit(props,attempt,invocation,self.populated(attempt),pinned_pid=pid)
            receipt={'attempt':attempt,'release_sha256':digest(canonical(release)),'source_tree':D02_TREE,'candidate_tree':self.bindings['candidate_tree'],'launch_token':token,
                'PID1':props,'observed_worker':observation,'pinned_worker':pinned_worker,'host_pidfd_exited':True,'cgroup_populated':False,
                'actual_PID1_exit':exit_code,'independent_unrestricted_agent_custody':False}
            ledger.execution(attempt,'EXIT_OBSERVED',receipt)
            ledger.execution(attempt,'CLEANING',receipt)
            self.stop(attempt,invocation)
            require(self.native(NativeOperation.UNREF)=={'ReferenceReleased':'yes'},'CLEANUP_UNCERTAIN')
            receipt['cleanup']=self.cleanup_witness(attempt)
            publish_receipt(ledger,attempt,receipt,DEPLOYMENT/'receipts'/(attempt+'.json'))
            return exit_code
        except BaseException:
            # Reconcile from the durable token even when the reply carrying
            # InvocationID was lost. Ambiguity stops without killing a foreign
            # unit or replenishing the consumed attempt.
            row=ledger.get(attempt)
            if row['execution'] not in {'FINISHED','INTERRUPTED'}:
                cleanup=self.recover(row);ledger.execution(attempt,'INTERRUPTED',cleanup)
            raise
        finally:
            if pidfd is not None:os.close(pidfd)

    def cleanup_witness(self,attempt):
        from contract import check_cleanup
        props=self.show(attempt)
        runtime=Path('/run/p08-d03-worker')
        witness={'unit_terminal':props.get('LoadState')=='not-found' or props.get('ActiveState') in {'inactive','failed'},
            'cgroup_empty':not self.populated(attempt),'reference_released':props.get('ReferenceHeld')=='no',
            'runtime_absent':confirmed_absent(runtime),'credentials_absent':confirmed_absent(Path('/run/credentials')/unit_name(attempt)),
            'mounts_absent':not any(str(runtime) in line or str(DEPLOYMENT/'image') in line for line in Path('/proc/self/mountinfo').read_text().splitlines())}
        check_cleanup(witness);return witness

    def check_live(self,release):
        now=time.time();require(now>=self.previous_clock,'HOST_CLOCK_CHANGED');self.previous_clock=now
        check_binding(release,self.bindings,now)
        require(now<self.route.expires_at and self.settings['valid_from']<=now<self.settings['expires_at'],'CAMPAIGN_EXPIRED')
        path=DEPLOYMENT/'revocations'/release['attempt_id']
        root_chain(path.parent)
        require(not path.is_symlink(),'REVOCATION_UNCERTAIN')
        if path.exists():
            value=parse_json(root_read(path));require(value=={'attempt_id':release['attempt_id'],'release_id':release['release_id'],'decision':'REVOKED'},'REVOCATION_UNCERTAIN')
            raise Refusal('RELEASE_REVOKED')


def check_image_runtime(image,bindings):
    require(type(image) is dict and image.get('runtime_input_sha256')==bindings.get('worker_runtime_sha256') and
        hex_id(bindings.get('worker_runtime_sha256'),64),'WORKER_RUNTIME_MISMATCH')


def publish_receipt(ledger,attempt,receipt,path):
    exclusive_write(path,canonical(receipt))
    ledger.execution(attempt,'FINISHED',receipt)


def confirmed_absent(path):
    try:Path(path).lstat();return False
    except FileNotFoundError:return True
    except OSError:raise Refusal('CLEANUP_UNCERTAIN') from None


def exclusive_write(path,raw):
    root_chain(Path(path).parent)
    fd=os.open(path,os.O_WRONLY|os.O_CREAT|os.O_EXCL|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:require(os.write(fd,raw)==len(raw),'HOST_WRITE_UNCERTAIN');os.fsync(fd)
    finally:os.close(fd)
    directory=os.open(Path(path).parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(directory)
    finally:os.close(directory)


def main():
    host=Host()
    parser=argparse.ArgumentParser();group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--attempt');group.add_argument('--reconcile',action='store_true');args=parser.parse_args()
    root_chain(DEPLOYMENT/'state')
    fd=os.open(DEPLOYMENT/'state/lock',os.O_CREAT|os.O_RDWR|os.O_NOFOLLOW|os.O_CLOEXEC,0o600)
    try:
        fcntl.flock(fd,fcntl.LOCK_EX|fcntl.LOCK_NB)
        register_path=DEPLOYMENT/'state/register.sqlite3'
        if register_path.exists() or register_path.is_symlink():root_read(register_path,8388608)
        with Register(register_path) as ledger:
            ledger.reconcile(host.recover)
            if args.reconcile:return 0
            return host.launch(args.attempt,ledger)
    finally:
        os.close(fd)
        if host.executor is not None:host.executor.close()


if __name__=='__main__':
    try:raise SystemExit(main())
    except (Refusal,OSError,ValueError,subprocess.SubprocessError) as error:
        print(getattr(error,'code','HOST_EFFECT_UNCERTAIN'),file=sys.stderr);raise SystemExit(2)
