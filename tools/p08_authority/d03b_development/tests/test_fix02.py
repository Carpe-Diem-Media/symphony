"""H02 regressions using actual validators/launch code and disposable test doubles.

PID1/route/signature/pidfd observations below are component fixtures, not host
custody or containment proof. Legacy call adaptation exists only for RED reuse.
"""
import inspect,json,os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
import contract as c
import host
from custody_fixture import storage
ROOT=Path(__file__).resolve().parents[1]
ATTEMPT='2'*32;INVOCATION='5'*32;PID=123;START='9000'


def release():
 return {key:'1'*64 for key in c.HASH_FIELDS}|{'source_tree':c.D02_TREE,'candidate_tree':'8'*40,
  'boot_id':'c5b62809-638c-421c-84fb-8b2f1663e6be','campaign':c.CAMPAIGN,'schema':'p08-host-development-release-1',
  'suite':c.SUITE,'scope':c.SCOPE,'attempt_id':ATTEMPT,'release_id':'3'*32,'nonce':'4'*64,'slot':1,
  'issued_at':1000,'not_before':1000,'expires_at':1120}


def properties():
 token=c.digest(c.canonical(release()))
 return {'Id':host.unit_name(ATTEMPT),'Description':'p08-d03:'+ATTEMPT+':'+token,
  'Transient':'yes','InvocationID':INVOCATION,'MainPID':str(PID),'ExecMainPID':str(PID),
  'ExecMainCode':'1','ExecMainStatus':'0','RootDirectory':str(host.DEPLOYMENT/'image'),
  'ControlGroup':'/system.slice/'+host.unit_name(ATTEMPT)}


def exit_contract(props,pinned=PID,populated=False):
 # Preserve the same regression definitions against the exact FIX-01 API.
 if 'pinned_pid' in inspect.signature(c.check_pid1_exit).parameters:
  return c.check_pid1_exit(props,ATTEMPT,INVOCATION,populated,pinned_pid=pinned)
 return c.check_pid1_exit(props,ATTEMPT,INVOCATION,populated)


class TerminalContractTests(unittest.TestCase):
 def terminal(self):return properties()|{'MainPID':'0'}
 def test_changed_exec_main_pid_refuses(self):
  with self.assertRaises(c.Refusal):exit_contract(self.terminal()|{'ExecMainPID':'456'})
 def test_replacement_positive_main_pid_refuses(self):
  with self.assertRaises(c.Refusal):exit_contract(self.terminal()|{'MainPID':'456'})
 def test_missing_main_pid_refuses(self):
  props=self.terminal();del props['MainPID']
  with self.assertRaises(c.Refusal):exit_contract(props)
 def test_missing_zero_or_malformed_exec_identity_refuses(self):
  for value in [None,'0','-1','','wrong','0123',True,123]:
   with self.subTest(value=value),self.assertRaises(c.Refusal):exit_contract(self.terminal()|{'ExecMainPID':value})
 def test_missing_invalid_or_unpinned_launch_pid_refuses(self):
  for pinned in [None,0,-1,True,'123']:
   with self.subTest(pinned=pinned),self.assertRaises(c.Refusal):exit_contract(self.terminal(),pinned)
 def test_stale_invocation_and_nonempty_cgroup_refuse(self):
  with self.assertRaises(c.Refusal):exit_contract(self.terminal()|{'InvocationID':'6'*32})
  with self.assertRaises(c.Refusal):exit_contract(self.terminal(),populated=True)
 def test_only_exact_or_zero_terminal_main_pid_is_allowed(self):
  for value in ['0',str(PID)]:self.assertEqual(0,exit_contract(self.terminal()|{'MainPID':value}))
  for value in [None,'-1','','wrong','0123',True,123]:
   with self.subTest(value=value),self.assertRaises(c.Refusal):exit_contract(self.terminal()|{'MainPID':value})
 def test_signal_and_nonzero_exit_results_keep_exact_pid(self):
  self.assertEqual(-9,exit_contract(self.terminal()|{'ExecMainCode':'2','ExecMainStatus':'9'}))
  self.assertEqual(7,exit_contract(self.terminal()|{'ExecMainStatus':'7'}))


class LaunchExitTests(unittest.TestCase):
 def attempt(self,changes=None,remove=(),observed=None,unexited=False,open_error=False):
  initial=properties();terminal=initial|{'MainPID':'0'}|(changes or {})
  for key in remove:terminal.pop(key,None)
  observation={'pid':PID,'start':START,'invocation':INVOCATION} if observed is None else observed
  outputs=[];calls=[];fd_opened=[];fd_closed=[];error=None;result=None
  class FixtureHost(host.Host):
   def __init__(self):
    self.observations=iter([{'LoadState':'not-found'},initial,initial.copy(),terminal])
    self.bindings={'candidate_tree':'8'*40}
   def show(self,*args):return next(self.observations)
   def signature(self,*args):pass
   def check_live(self,*args):pass
   def native(self,operation):
    calls.append(operation.name)
    return {'Created':'yes'} if operation is host.NativeOperation.CREATE else {'ReferenceReleased':'yes'}
   def observe(self,*args):return observation.copy()
   def populated(self,*args):return False
   def stop(self,*args):calls.append('STOP')
   def cleanup_witness(self,*args):return {key:True for key in ['unit_terminal','cgroup_empty','reference_released','runtime_absent','credentials_absent','mounts_absent']}
   def recover(self,*args):calls.append('RECOVER');return {'fixture':'NO_PID1_OR_WORKER_CREATED'}
  def opened(pid):
   fd_opened.append(pid)
   if open_error:raise OSError('synthetic pidfd open failure')
   # Real local descriptor, explicitly NOT a kernel pidfd in this test double.
   fd=os.open('/dev/null',os.O_RDONLY);fd_closed.append(fd);return fd
  def write(path,raw):outputs.append({'path':str(path),'raw':raw.decode()})
  if unexited:poll=iter([([],[],[]),([],[],[])])
  else:poll=iter([([],[],[]),([1],[],[])])
  with tempfile.TemporaryDirectory(dir=ROOT/'scratch') as directory:
   with storage.Register(Path(directory)/'register') as reg,\
     patch.object(host,'root_read',return_value=c.canonical(release())),\
     patch.object(host,'exclusive_write',side_effect=write),\
     patch.object(host.os,'pidfd_open',side_effect=opened),\
     patch.object(host.select,'select',side_effect=lambda *args:next(poll)),\
     patch.object(host.time,'monotonic',side_effect=iter([1000,1001,1023])):
    try:result=FixtureHost().launch(ATTEMPT,reg)
    except Exception as caught:error=caught
    row=reg.get(ATTEMPT);history=reg.execution_history(ATTEMPT)
   for fd in fd_closed:
    with self.assertRaises(OSError):os.fstat(fd)
  record={'test':self.id(),'initial':initial,'terminal':terminal,'observed':observation,
   'result':result,'error':str(error) if error else None,'execution':row['execution'],'state':row['state'],
   'history':history,'calls':calls,'outputs':outputs,'pidfd_open_arguments':fd_opened,'all_fixture_fds_closed':True,
   'classification':'UNPRIVILEGED_COMPONENT_DOUBLES_ONLY'}
  # Each subcase gets its own retained observation instead of overwriting logs.
  for index in range(100):
   path=ROOT/'evidence'/(self.id().replace('.','-')+'-'+str(index)+'.json')
   if not path.exists():break
  with path.open('x') as stream:json.dump(record,stream,indent=2);stream.write('\n')
  return record,error
 def refused(self,**kwargs):
  record,error=self.attempt(**kwargs)
  self.assertIsInstance(error,c.Refusal,record)
  self.assertEqual('CONSUMED',record['state'])
  self.assertEqual('INTERRUPTED',record['execution'])
  self.assertNotIn('FINISHED',record['history'])
  self.assertFalse(any(x['path'].endswith('/receipts/'+ATTEMPT+'.json') for x in record['outputs']))
  return record
 def test_changed_exec_pid_never_finishes(self):self.refused(changes={'ExecMainPID':'456'})
 def test_replacement_positive_main_pid_never_finishes(self):self.refused(changes={'MainPID':'456'})
 def test_missing_terminal_main_pid_never_finishes(self):self.refused(remove=['MainPID'])
 def test_missing_or_zero_exec_identity_never_finishes(self):
  self.refused(remove=['ExecMainPID']);self.refused(changes={'ExecMainPID':'0'})
 def test_stale_invocation_never_finishes(self):self.refused(changes={'InvocationID':'6'*32})
 def test_terminal_token_transient_image_cgroup_and_unit_remain_bound(self):
  for key,value in [('Description','foreign'),('Transient','no'),('RootDirectory','/foreign'),('ControlGroup','/foreign'),('Id','foreign.service')]:
   with self.subTest(key=key):self.refused(changes={key:value})
 def test_no_exit_receipt_before_original_pidfd_exit(self):self.refused(unexited=True)
 def test_missing_start_identity_cannot_fall_back_to_pid_number(self):
  self.refused(observed={'pid':PID,'invocation':INVOCATION})
 def test_invalid_start_identity_cannot_fall_back_to_pid_number(self):
  for value in ['0','',None,'wrong']:
   with self.subTest(value=value):self.refused(observed={'pid':PID,'start':value,'invocation':INVOCATION})
 def test_observed_pid_or_invocation_must_match_the_pin(self):
  self.refused(observed={'pid':456,'start':START,'invocation':INVOCATION})
  self.refused(observed={'pid':PID,'start':START,'invocation':'6'*32})
 def test_pidfd_open_failure_does_not_publish_success(self):
  record,error=self.attempt(open_error=True)
  self.assertIsInstance(error,OSError);self.assertEqual('INTERRUPTED',record['execution'])
  self.assertNotIn('FINISHED',record['history'])
 def test_valid_terminal_receipt_retains_original_process_pin(self):
  for main in ['0',str(PID)]:
   with self.subTest(main=main):
    record,error=self.attempt(changes={'MainPID':main});self.assertIsNone(error,record)
    self.assertEqual(0,record['result']);self.assertEqual('FINISHED',record['execution']);self.assertEqual([PID],record['pidfd_open_arguments'])
    receipts=[json.loads(x['raw']) for x in record['outputs'] if x['path'].endswith('/receipts/'+ATTEMPT+'.json')]
    self.assertEqual(1,len(receipts));receipt=receipts[0]
    self.assertEqual({'pid':PID,'start':START,'invocation':INVOCATION},
     {key:receipt['observed_worker'][key] for key in ['pid','start','invocation']})
    self.assertTrue(receipt['host_pidfd_exited']);self.assertEqual(str(PID),receipt['PID1']['ExecMainPID'])
