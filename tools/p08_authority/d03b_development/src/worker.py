"""Fixed DynamicUser worker. Executes only after owner-mediated PID1 launch."""
import os
from pathlib import Path
import sys


def identity_guard():
    uid=os.geteuid()
    if not 61184 <= uid <= 65519 or os.getegid()!=uid or os.getgroups() not in ([],[uid]):
        raise RuntimeError('WORKER_IDENTITY_UNPROVEN')
    status=dict(line.split(':',1) for line in Path('/proc/self/status').read_text().splitlines() if ':' in line)
    if status['NoNewPrivs'].strip()!='1' or any(int(status[key].strip(),16) for key in ['CapInh','CapPrm','CapEff','CapBnd','CapAmb']):
        raise RuntimeError('WORKER_IDENTITY_UNPROVEN')
    if Path(__file__).resolve()!=Path('/app/worker.py') or Path('/app').stat().st_uid!=0:
        raise RuntimeError('WORKER_IMAGE_UNPROVEN')


def main(attempt):
    identity_guard()
    sys.path.insert(0,'/app')
    import contract as c
    import importlib.util
    import json
    import time
    c.require(c.hex_id(attempt,32),'ATTEMPT_INVALID')
    release_path=Path('/run/credentials')/c.unit_name(attempt)/'release.json'
    release=c.parse_release(release_path.read_bytes())
    c.require(release['attempt_id']==attempt and release['not_before']<=time.time()<release['expires_at'],'RELEASE_TIME_INVALID')
    # This public credential is delivered by PID1 from root-owned verified
    # input. It cannot sign, consume a second release or select a command.
    context=c.parse_json((release_path.parent/'context.json').read_bytes())
    c.require(set(context)=={'attempt_id','release_sha256','host_admission'} and context['attempt_id']==attempt and
        context['release_sha256']==c.digest(c.canonical(release)) and context['host_admission']=='CONSUMED_BEFORE_PID1_START',
        'HOST_CONTEXT_INVALID')
    out=Path('/output')
    for name in ['logs','tmp','home','cache']:(out/name).mkdir(mode=0o700)
    (out/'worker-identity.json').write_bytes(c.canonical({'uid':os.geteuid(),'gid':os.getegid(),'groups':os.getgroups(),
        'attempt':attempt,'invocation':os.environ.get('INVOCATION_ID'),'credentials_are_public':True}))
    # Gives the host a finite observation window. Missing that window refuses
    # verification; it never turns a missed observation into a PASS.
    time.sleep(0.5)
    spec=importlib.util.spec_from_file_location('d03_actual_d02_runner','/app/d02/p08_qualification_runner.py')
    runner=importlib.util.module_from_spec(spec);sys.modules[spec.name]=runner;spec.loader.exec_module(runner)
    runner.REPO=Path('/app');runner.OUT=out
    command=['/usr/bin/python3.14','-I','-S','-B','/app/finite_suite.py']
    runner.SUITES[c.SUITE]=command
    runner.ENV={'PATH':'/nonexistent','HOME':'/output/home','TMPDIR':'/output/tmp','TMP':'/output/tmp',
                'TEMP':'/output/tmp','XDG_CACHE_HOME':'/output/cache','LANG':'C.UTF-8','LC_ALL':'C.UTF-8'}
    class HostReleasedWorker:
        # The host owns live revocation and kills the whole cgroup. A worker
        # callback is not an authority source and cannot extend the lease.
        def register_child(self,root,claims,pid):
            c.require(Path('/proc/'+str(pid)+'/status').is_file(),'CHILD_IDENTITY_UNPROVEN')
        def check_revocation(self,root,claims):
            c.require(time.time()<claims['expires_at'],'RELEASE_TIME_INVALID')
        def permitted_verification(self,argv,root,pid):return False
    return runner._run_suite({'scope_sha256':release['host_source_sha256']},c.SUITE,HostReleasedWorker(),release)


if __name__=='__main__':
    try:
        identity_guard()
        if len(sys.argv)!=3 or sys.argv[1]!='--attempt':raise RuntimeError('WORKER_ARGUMENTS_INVALID')
        raise SystemExit(main(sys.argv[2]))
    except RuntimeError as error:print(str(error),file=sys.stderr);raise SystemExit(2)
