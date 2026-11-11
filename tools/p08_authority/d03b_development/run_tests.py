"""Unprivileged inspected tests only. This never admits a live host."""
import argparse,importlib.util,json,os,resource,sys,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parent
p=argparse.ArgumentParser();p.add_argument('--source',default=str(ROOT/'src'));p.add_argument('--pattern',default='test_*.py');p.add_argument('--names',nargs='*');a=p.parse_args()
sys.path.insert(0,a.source);sys.path.insert(0,str(ROOT/'tests'))
resource.setrlimit(resource.RLIMIT_CPU,(20,25));resource.setrlimit(resource.RLIMIT_CORE,(0,0));resource.setrlimit(resource.RLIMIT_NOFILE,(128,128))
os.environ['TMPDIR']=str(ROOT/'scratch');os.environ['TMP']=str(ROOT/'scratch');os.environ['TEMP']=str(ROOT/'scratch')
def inside(path):
 if isinstance(path,int):return True
 return Path(os.fsdecode(path)).absolute().is_relative_to(ROOT)
def synthetic_key_path(value):
 path=Path(value)
 return (path.is_absolute() and '..' not in path.parts and
   path.parent.resolve(strict=True)==path.parent and
   path.is_relative_to(ROOT/'scratch') and path.name in ['key','rogue','synthetic-issuer'])
def audit(event,args):
 if event.startswith('socket.') or event in ['os.system','os.fork','os.forkpty','os.exec']:raise PermissionError('development effect denied: '+event)
 if event=='open' and args[2] & (os.O_WRONLY|os.O_RDWR|os.O_CREAT|os.O_TRUNC|os.O_APPEND):
  if not inside(args[0]):raise PermissionError('write outside disposable workspace')
 if event in ['os.mkdir','os.remove','os.rmdir','os.chmod','os.chown','os.truncate','os.utime','os.rename','os.link','os.symlink']:
  paths=args[:2] if event in ['os.rename','os.link'] else args[1:2] if event=='os.symlink' else args[:1]
  if any(not inside(x) for x in paths):raise PermissionError('mutation outside disposable workspace')
 if event in ['subprocess.Popen','os.posix_spawn']:
  argv=args[1]
  # Only disposable synthetic keys may be created/signed by component tests.
  # This allowance is absent from the qualification launcher and live host.
  synthetic_key=(argv[:6]==['/usr/bin/ssh-keygen','-q','-t','ed25519','-N',''] and
    len(argv)==8 and argv[6]=='-f' and synthetic_key_path(argv[7]))
  synthetic_sign=(len(argv)==7 and argv[:4]==['/usr/bin/ssh-keygen','-Y','sign','-f'] and
    synthetic_key_path(argv[4]) and argv[5]=='-n' and
    argv[6] in ['symphony.p08.f09.enrollment.v1','symphony.p08.f09.checkpoint.v1','symphony.p08.d02.cooperative.v1'])
  permitted=(argv[:3]==['/usr/bin/ssh-keygen','-Y','verify'] or
    synthetic_key or synthetic_sign or
    (argv[:4]==['/usr/bin/python3.14','-I','-S','-B'] and
     ((Path(argv[4]).parent==ROOT/'src' and Path(argv[4]).name in ['host.py','worker.py']) or
      Path(argv[4])==ROOT/'tests/f09_process_probe.py')))
  if not permitted:raise PermissionError('unreviewed subprocess')
sys.addaudithook(audit)
for name in ['contract','ledger','build_image','host']:
 spec=importlib.util.spec_from_file_location(name,Path(a.source)/(name+'.py'));module=importlib.util.module_from_spec(spec);sys.modules[name]=module;spec.loader.exec_module(module)
suite=unittest.defaultTestLoader.discover(str(ROOT/'tests'),pattern=a.pattern)
if a.names:
 def flatten(s):
  for t in s:
   if isinstance(t,unittest.TestSuite):yield from flatten(t)
   else:yield t
 suite=unittest.TestSuite(t for t in flatten(suite) if t.id().split('.')[-1] in a.names)
result=unittest.TextTestRunner(verbosity=2).run(suite)
print(json.dumps({'methods':result.testsRun,'passed':result.testsRun-len(result.failures)-len(result.errors)-len(result.skipped),'failed':len(result.failures),'errors':len(result.errors),'skipped':len(result.skipped),'source':a.source,'classification':'UNPRIVILEGED_COMPONENT_FIXTURES_ONLY'}))
raise SystemExit(not result.wasSuccessful())
