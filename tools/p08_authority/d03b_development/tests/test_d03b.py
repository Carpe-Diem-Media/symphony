"""Inspected disposable filesystem and lifecycle regressions. No root authority."""
import copy,importlib.util,json,os,sqlite3,sys,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1]
import contract as c
import host,build_image
from custody_fixture import storage as ledger

class BoundaryTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory(dir=ROOT/'scratch');self.addCleanup(self.temp.cleanup);self.p=Path(self.temp.name)
 def release(self):
  return {key:'1'*64 for key in c.HASH_FIELDS}|{'source_tree':c.D02_TREE,'candidate_tree':'8'*40,'boot_id':'c5b62809-638c-421c-84fb-8b2f1663e6be','campaign':c.CAMPAIGN,'schema':'p08-host-development-release-1','suite':c.SUITE,'scope':c.SCOPE,'attempt_id':'2'*32,'release_id':'3'*32,'nonce':'4'*64,'slot':1,'issued_at':1000,'not_before':1000,'expires_at':1120}
 def test_output_reservation_precedes_any_launch(self):
  calls=[];release=self.release()
  class FixtureHost(host.Host):
   def __init__(self):pass
   def show(self,*args):return {'LoadState':'not-found'}
   def signature(self,*args):pass
   def check_live(self,*args):pass
   def run(self,*args):calls.append('UNSAFE_LAUNCH');raise c.Refusal('FIXTURE_LAUNCH')
   def recover(self,*args):return {'fixture':'absent'}
  def collision(*args):calls.append(Path(args[0]).name);raise c.Refusal('OUTPUT_COLLISION')
  with ledger.Register(self.p/'register') as reg,patch.object(host,'root_read',return_value=c.canonical(release)),patch.object(host,'exclusive_write',side_effect=collision):
   with self.assertRaises(c.Refusal):FixtureHost().launch(release['attempt_id'],reg)
   self.assertEqual([release['attempt_id']+'.stdout'],calls)
   self.assertEqual('CONSUMED',reg.get(release['attempt_id'])['state'])
 def test_native_command_interface_rejects_caller_argv(self):
  self.assertTrue(hasattr(host,'NativeOperation'),'typed native operation interface absent')
  self.assertFalse(hasattr(host.Host,'run'),'generic command execution still exposed')
  self.assertEqual(['CREATE','SHOW','STOP','UNREF','CLOSE'],[x.name for x in host.NativeOperation])
 def test_safe_export_rejects_aliases_and_specials(self):
  self.assertTrue(hasattr(build_image,'safe_export'),'bounded output export absent')
  canary=self.p/'canary';canary.write_bytes(b'known-present')
  (self.p/'link').symlink_to('canary');os.link(canary,self.p/'hard');os.mkfifo(self.p/'fifo')
  for name in ['link','hard','fifo','../canary']:
   with self.assertRaises(c.Refusal):build_image.safe_export(self.p,name,1024)
 def test_safe_export_regular_and_size_bound(self):
  self.assertTrue(hasattr(build_image,'safe_export'),'bounded output export absent')
  (self.p/'result.json').write_bytes(b'abc')
  self.assertEqual(b'abc',build_image.safe_export(self.p,'result.json',3))
  with self.assertRaises(c.Refusal):build_image.safe_export(self.p,'result.json',2)
 def test_image_identity_change_and_closed_inventory(self):
  self.assertTrue(hasattr(build_image,'verify_image'),'closed image comparison absent')
  (self.p/'a').write_bytes(b'one');(self.p/'a').chmod(0o644);entries=build_image.normalized(build_image.image_inventory(self.p))
  build_image.verify_image(self.p,entries)
  (self.p/'a').write_bytes(b'two')
  with self.assertRaises(c.Refusal):build_image.verify_image(self.p,entries)
 def test_image_hardlink_is_refused(self):
  (self.p/'a').write_bytes(b'a');os.link(self.p/'a',self.p/'b')
  with self.assertRaises(c.Refusal):build_image.image_inventory(self.p)
 def test_explicit_directory_modes_survive_umask(self):
  self.assertTrue(hasattr(build_image,'fixed_directory'),'explicit image directory helper absent')
  old=os.umask(0o777)
  try:build_image.fixed_directory(self.p/'image',0o755)
  finally:os.umask(old)
  self.assertEqual(0o755,(self.p/'image').stat().st_mode&0o777)
 def test_duplicate_execution_allocation_is_terminally_refused(self):
  with ledger.Register(self.p/'register') as reg:
   r=self.release();reg.request(r);reg.advance(r['attempt_id'],'ISSUED');reg.advance(r['attempt_id'],'VERIFIED');reg.consume(r['attempt_id'])
   reg.execution(r['attempt_id'],'LAUNCHING',{'token':'x'})
   with self.assertRaises(c.Refusal):reg.execution(r['attempt_id'],'LAUNCHING',{'token':'new'})
 def test_known_present_denial_requires_permission_errno(self):
  self.assertTrue(hasattr(c,'check_canary_denial'),'known-present canary assertion absent')
  c.check_canary_denial(True,13)
  for exists,code in [(False,13),(True,2),(True,None)]:
   with self.assertRaises(c.Refusal):c.check_canary_denial(exists,code)
 def test_cleanup_requires_all_conservative_witnesses(self):
  self.assertTrue(hasattr(c,'check_cleanup'),'conservative cleanup classifier absent')
  v={'unit_terminal':True,'cgroup_empty':True,'reference_released':True,'runtime_absent':True,'credentials_absent':True,'mounts_absent':True}
  c.check_cleanup(v)
  for key in v:
   with self.assertRaises(c.Refusal):c.check_cleanup(v|{key:False})

class AdditionalTests(unittest.TestCase):
 setUp=BoundaryTests.setUp
 release=BoundaryTests.release
 def test_output_symlink_cannot_redirect_exclusive_write(self):
  canary=self.p/'canary';canary.write_bytes(b'known-present');link=self.p/'stdout';link.symlink_to('canary')
  with patch.object(host,'root_chain',return_value=None):
   with self.assertRaises(FileExistsError):host.exclusive_write(link,b'redirected')
  self.assertEqual(b'known-present',canary.read_bytes())
 def test_safe_export_checks_registered_alias_types(self):
  for kind in ['symlink','hardlink','fifo']:
   directory=self.p/kind;directory.mkdir();canary=directory/'canary';canary.write_bytes(b'known-present');out=directory/'result.json'
   if kind=='symlink':out.symlink_to('canary')
   elif kind=='hardlink':os.link(canary,out)
   else:os.mkfifo(out)
   with self.assertRaises(c.Refusal):build_image.safe_export(directory,'result.json',1024)
 def test_closed_image_rejects_extra_and_missing_entries(self):
  (self.p/'a').write_bytes(b'a');(self.p/'a').chmod(0o644);expected=build_image.normalized(build_image.image_inventory(self.p))
  (self.p/'extra').write_bytes(b'new');(self.p/'extra').chmod(0o644)
  with self.assertRaises(c.Refusal):build_image.verify_image(self.p,expected)
  (self.p/'extra').unlink();(self.p/'a').unlink()
  with self.assertRaises(c.Refusal):build_image.verify_image(self.p,expected)
 def test_native_frames_refuse_duplicates_partial_and_extra_delimiters(self):
  import native_executor as n
  self.assertEqual({'Id':'fixed'},n.parse_frame(b'Id=fixed\nEND\n'))
  for raw in [b'Id=a\nId=b\nEND\n',b'Id=a\n',b'END\n',b'x'*32769,b'Id=x\r\nEND\n']:
   with self.assertRaises(c.Refusal):n.parse_frame(raw)
 def test_native_constructor_refuses_before_launch_for_current_account(self):
  import native_executor as n
  with self.assertRaises(c.Refusal):n.NativeExecutor()
 def test_full_execution_history_survives_restart(self):
  with ledger.Register(self.p/'register') as reg:
   r=self.release();a=r['attempt_id'];reg.request(r);reg.advance(a,'ISSUED');reg.advance(a,'VERIFIED');reg.consume(a)
   for state in ['LAUNCHING','RUNNING','EXIT_OBSERVED','CLEANING','FINISHED']:reg.execution(a,state,{'state':state})
  with ledger.Register(self.p/'register') as reg:
   self.assertEqual(['START_PENDING','LAUNCHING','RUNNING','EXIT_OBSERVED','CLEANING','FINISHED'],reg.execution_history(a))
   with self.assertRaises(c.Refusal):reg.execution(a,'LAUNCHING',{})
 def test_contradictory_execution_history_refuses(self):
  with ledger.Register(self.p/'register') as reg:
   r=self.release();a=r['attempt_id'];reg.request(r);reg.advance(a,'ISSUED');reg.advance(a,'VERIFIED');reg.consume(a)
  with sqlite3.connect(self.p/'register') as db:db.execute("UPDATE attempts SET execution='FINISHED'")
  with self.assertRaises(c.Refusal):ledger.Register(self.p/'register')
 def test_inaccessible_cleanup_path_is_not_absence(self):
  with patch.object(Path,'lstat',side_effect=PermissionError('fixture')):
   with self.assertRaises(c.Refusal):host.confirmed_absent(self.p/'unknown')


class ReviewRegressions(unittest.TestCase):
 setUp=BoundaryTests.setUp
 release=BoundaryTests.release
 def test_receipt_failure_cannot_leave_finished_register(self):
  self.assertTrue(hasattr(host,'publish_receipt'),'durable receipt publication boundary absent')
  with ledger.Register(self.p/'register') as reg:
   r=self.release();a=r['attempt_id'];reg.request(r);reg.advance(a,'ISSUED');reg.advance(a,'VERIFIED');reg.consume(a)
   for state in ['LAUNCHING','RUNNING','EXIT_OBSERVED','CLEANING']:reg.execution(a,state,{'launch_token':'7'*64})
   with patch.object(host,'exclusive_write',side_effect=OSError('disposable receipt failure')):
    with self.assertRaises(OSError):host.publish_receipt(reg,a,{'observed':True},self.p/'receipt.json')
   self.assertEqual('CLEANING',reg.get(a)['execution'])
   reg.reconcile(lambda row:{'cleanup':'fixture-only'})
   self.assertEqual('INTERRUPTED',reg.get(a)['execution'])
 def test_image_runtime_mismatch_refuses(self):
  self.assertTrue(hasattr(host,'check_image_runtime'),'image runtime provenance comparison absent')
  bindings={'worker_runtime_sha256':'1'*64};image={'runtime_input_sha256':'1'*64}
  host.check_image_runtime(image,bindings)
  with self.assertRaises(c.Refusal):host.check_image_runtime(image|{'runtime_input_sha256':'2'*64},bindings)
 def test_fixed_worker_route_cannot_claim_unrestricted_agent_disabled(self):
  bindings={'boot_id':'c5b62809-638c-421c-84fb-8b2f1663e6be'}
  v={'schema':'p08-source-route-owner-handoff-1','campaign':c.CAMPAIGN,'boot_id':bindings['boot_id'],
   'route_manifest_sha256':'1'*64,'source_session':'01a1c3c2-5be2-7173-bec3-90a2ee0ea021','route':'SYSTEMD_TRANSIENT_FIXED_COMMAND_ONLY',
   'unrestricted_tool_route':'DISABLED_BY_OWNER_FOR_CAMPAIGN','issued_at':1000,'expires_at':1100}
  with self.assertRaises(c.Refusal):host.parse_route_approval(c.canonical(v),bindings,1001)

class LiveDecisionComponents(unittest.TestCase):
 setUp=BoundaryTests.setUp
 release=BoundaryTests.release
 def fixture_host(self):
  import types
  h=object.__new__(host.Host);r=self.release();h.bindings={k:r[k] for k in c.BINDINGS};h.previous_clock=1000
  h.route=types.SimpleNamespace(expires_at=1120);h.settings={'valid_from':1000,'expires_at':1120}
  (self.p/'revocations').mkdir();return h,r
 def test_live_revocation_and_expiry_refuse(self):
  h,r=self.fixture_host();(self.p/'revocations'/r['attempt_id']).write_bytes(c.canonical({'attempt_id':r['attempt_id'],'release_id':r['release_id'],'decision':'REVOKED'}))
  with patch.object(host,'DEPLOYMENT',self.p),patch.object(host,'root_chain',return_value=None),patch.object(host,'root_read',side_effect=lambda path:Path(path).read_bytes()),patch.object(host.time,'time',return_value=1001):
   with self.assertRaises(c.Refusal) as caught:h.check_live(r)
   self.assertEqual('RELEASE_REVOKED',caught.exception.code)
  with patch.object(host.time,'time',return_value=1120):
   with self.assertRaises(c.Refusal):h.check_live(r)
 def test_clock_reversal_refuses(self):
  h,r=self.fixture_host()
  with patch.object(host.time,'time',return_value=999):
   with self.assertRaises(c.Refusal) as caught:h.check_live(r)
   self.assertEqual('HOST_CLOCK_CHANGED',caught.exception.code)
 def test_changed_named_file_identity_refuses_export(self):
  path=self.p/'result.json';path.write_bytes(b'known-present');original=os.read
  def replace(fd,limit):
   raw=original(fd,limit);other=self.p/'replacement';other.write_bytes(b'known-present');other.replace(path);return raw
  with patch.object(os,'read',side_effect=replace):
   with self.assertRaises(c.Refusal):build_image.safe_export(self.p,'result.json',1024)
 def test_valid_route_claim_is_limited_to_fixed_worker(self):
  v={'schema':'p08-source-route-owner-handoff-1','campaign':c.CAMPAIGN,'boot_id':'c5b62809-638c-421c-84fb-8b2f1663e6be',
   'route_manifest_sha256':'1'*64,'source_session':'01a1c3c2-5be2-7173-bec3-90a2ee0ea021','route':'SYSTEMD_TRANSIENT_FIXED_COMMAND_ONLY',
   'unrestricted_tool_route':'UNCHANGED_OUTSIDE_FIXED_WORKER','issued_at':1000,'expires_at':1100}
  record=host.parse_route_approval(c.canonical(v),{'boot_id':v['boot_id']},1001)
  self.assertEqual(c.CAMPAIGN,record.campaign)

class WorkerEnvironmentTests(unittest.TestCase):
 def test_unexpected_credentials_and_agent_environment_refuse(self):
  self.assertTrue(hasattr(c,'check_worker_environment'),'closed worker environment check absent')
  value={'HOME':'/output/home','PATH':'/nonexistent','LANG':'C.UTF-8','LC_ALL':'C.UTF-8','INVOCATION_ID':'5'*32,'CREDENTIALS_DIRECTORY':'/run/credentials/p08-d03-worker.service'}
  c.check_worker_environment(value,'5'*32)
  for key in ['SSH_AUTH_SOCK','AWS_ACCESS_KEY_ID','DOCKER_HOST','LD_PRELOAD']:
   with self.assertRaises(c.Refusal):c.check_worker_environment(value|{key:'synthetic'},'5'*32)
