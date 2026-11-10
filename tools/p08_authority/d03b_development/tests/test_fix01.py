"""F09/H01 regressions. Legacy compatibility is only for the retained RED run."""
import json,sqlite3,tempfile,unittest
from pathlib import Path
import ledger,host
ROOT=Path(__file__).resolve().parents[1]

class FixTests(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'scratch');self.addCleanup(self.tmp.cleanup);self.path=Path(self.tmp.name)/'register.sqlite3'
 def register(self):
  if hasattr(ledger,'_RegisterStore'):
   from custody_fixture import storage
   return storage.Register(self.path)
  return ledger.Register(self.path)
 def claims(self):return {'attempt_id':'2'*32,'release_id':'3'*32,'nonce':'4'*64,'slot':1}
 def consume(self,reg):
  c=self.claims();reg.request(c);reg.advance(c['attempt_id'],'ISSUED');reg.advance(c['attempt_id'],'VERIFIED');reg.consume(c['attempt_id'])
 def test_missing_consumed_register_never_restores_entitlement(self):
  with self.register() as reg:self.consume(reg)
  self.path.unlink()
  with self.assertRaises(ledger.Refusal):
   with self.register() as reg:reg.request(self.claims())
  self.assertFalse(self.path.exists(),'recovery recreated a missing register')
 def test_recovery_never_implicitly_initializes_empty_path(self):
  with self.assertRaises(ledger.Refusal):ledger.Register(self.path)
  self.assertFalse(self.path.exists())
 def test_successful_path_requires_exact_attempt_token_identity(self):
  self.assertTrue(hasattr(host,'check_launch_identity'),'successful-path attempt/token guard absent')
  props=self.props();self.assertEqual('5'*32,host.check_launch_identity(props,'2'*32,'7'*64))
  for key,value in [('Description','foreign'),('Transient','no'),('InvocationID','0'*32),('Id','foreign.service'),('RootDirectory','/foreign'),('ControlGroup','/foreign')]:
   with self.assertRaises(ledger.Refusal):host.check_launch_identity(props|{key:value},'2'*32,'7'*64)
 def test_refreshed_same_pid_stale_incarnation_refuses(self):
  self.assertTrue(hasattr(host,'check_launch_identity'),'stable launch identity guard absent')
  before=self.props()
  for key,value in [('InvocationID','6'*32),('Description','stale'),('Transient','no'),('MainPID','124')]:
   with self.assertRaises(ledger.Refusal):host.check_launch_identity(before|{key:value},'2'*32,'7'*64,before)
 def props(self):
  return {'Id':host.unit_name('2'*32),'Description':'p08-d03:'+('2'*32)+':'+('7'*64),'Transient':'yes','InvocationID':'5'*32,
   'MainPID':'123','RootDirectory':str(host.DEPLOYMENT/'image'),'ControlGroup':'/system.slice/'+host.unit_name('2'*32)}

class CustodyRegressionTests(unittest.TestCase):
 def setUp(self):
  from custody_fixture import Custody
  self.Custody=Custody
  self.tmp=tempfile.TemporaryDirectory(dir=ROOT/'scratch');self.addCleanup(self.tmp.cleanup)
  self.path=Path(self.tmp.name)/'register.sqlite3';self.authority=Custody(self.path)
 def grant(self):return self.authority.issue()
 def initialize(self):return ledger._RegisterStore.initialize(self.path,self.authority,self.grant())
 def open(self):return ledger._RegisterStore(self.path,self.authority)
 def claims(self):return {'attempt_id':'2'*32,'release_id':'3'*32,'nonce':'4'*64,'slot':1}
 def verified(self,reg):
  c=self.claims();reg.request(c);reg.advance(c['attempt_id'],'ISSUED');reg.advance(c['attempt_id'],'VERIFIED')
 def consume(self,reg):self.verified(reg);reg.consume(self.claims()['attempt_id'])
 def test_explicit_bootstrap_and_fresh_authority_restart(self):
  with self.initialize() as reg:self.consume(reg)
  self.authority=self.Custody(self.path)
  with self.open() as reg:
   self.assertEqual('CONSUMED',reg.get(self.claims()['attempt_id'])['state'])
   self.assertEqual(4,self.authority.current(self.path).revision)
   with self.assertRaises(ledger.Refusal):reg.request(self.claims())
 def test_live_register_has_no_positive_provider_or_boolean(self):
  with self.initialize():pass
  before=self.path.read_bytes()
  with self.assertRaisesRegex(ledger.Refusal,'REGISTER_CUSTODY_UNCONFIGURED'):ledger.Register(self.path)
  with self.assertRaisesRegex(ledger.Refusal,'REGISTER_CUSTODY_UNCONFIGURED'):ledger.Register.initialize(self.path)
  with self.assertRaises(TypeError):ledger.Register(self.path,approved=True)
  self.assertEqual(before,self.path.read_bytes())
 def test_local_recreated_marker_does_not_authorize_live_register(self):
  (self.path.parent/'enrolled.json').write_text('{"approved":true}')
  with self.assertRaises(ledger.Refusal):ledger.Register(self.path)
  self.assertFalse(self.path.exists())
 def test_invalid_bootstrap_boolean_refuses_without_effects(self):
  self.grant()
  with self.assertRaisesRegex(ledger.Refusal,'BOOTSTRAP_INVALID'):
   ledger._RegisterStore.initialize(self.path,self.authority,True)
  self.assertFalse(self.path.exists());self.assertEqual('ISSUED',self.authority._read()['phase'])
 def test_fabricated_bootstrap_does_not_match_authority(self):
  from dataclasses import replace
  grant=self.grant()
  for bad in [replace(grant,database_id='f'*64),replace(grant,enrollment_id='e'*64)]:
   with self.assertRaises(ledger.Refusal):ledger._RegisterStore.initialize(self.path,self.authority,bad)
  self.assertFalse(self.path.exists())
 def test_wrong_bootstrap_locator_refuses(self):
  from dataclasses import replace
  grant=self.grant()
  with self.assertRaises(ledger.Refusal):
   ledger._RegisterStore.initialize(self.path,self.authority,replace(grant,locator=str(self.path)+'-other'))
  self.assertFalse(self.path.exists())
 def test_issued_but_not_bootstrapped_is_not_recovery(self):
  self.grant()
  with self.assertRaises(ledger.Refusal):self.open()
  self.assertFalse(self.path.exists())
 def test_partial_initialization_cannot_bootstrap_again(self):
  grant=self.grant();self.authority.fault='partial_bootstrap'
  with self.assertRaises(ledger.Refusal):ledger._RegisterStore.initialize(self.path,self.authority,grant)
  original=self.path.read_bytes();self.authority.fault=None
  self.assertEqual('BOOTSTRAP',self.authority._read()['phase'])
  with self.assertRaises(ledger.Refusal):ledger._RegisterStore.initialize(self.path,self.authority,grant)
  with self.assertRaises(ledger.Refusal):self.open()
  self.assertEqual(original,self.path.read_bytes())
 def test_existing_file_never_becomes_first_initialization(self):
  grant=self.grant();self.path.write_bytes(b'partial register')
  with self.assertRaises(ledger.Refusal):ledger._RegisterStore.initialize(self.path,self.authority,grant)
  self.assertEqual(b'partial register',self.path.read_bytes())
  self.assertEqual('BOOTSTRAP',self.authority._read()['phase'])
 def test_deleted_register_records_missing_history_then_quarantine(self):
  with self.initialize() as reg:self.consume(reg)
  self.path.unlink()
  with self.assertRaises(ledger.Refusal):self.open()
  events=[json.loads(line)['state']['phase'] for line in (self.authority.root/'journal').read_bytes().splitlines()]
  self.assertEqual(['MISSING_HISTORY','QUARANTINED'],events[-2:])
  self.assertFalse(self.path.exists())
 def test_same_inode_valid_database_rollback_is_refused(self):
  with self.initialize() as reg:
   old=self.path.read_bytes();inode=self.path.stat().st_ino;self.consume(reg)
  self.path.write_bytes(old)
  self.assertEqual(inode,self.path.stat().st_ino)
  with self.assertRaises(ledger.Refusal):self.open()
  self.assertEqual('QUARANTINED',self.authority._read()['phase'])
 def test_same_bytes_different_file_identity_refuses(self):
  with self.initialize():pass
  old=self.path.read_bytes();replacement=self.path.with_suffix('.replacement');replacement.write_bytes(old);replacement.chmod(0o600)
  replacement.replace(self.path)
  with self.assertRaises(ledger.Refusal):self.open()
 def test_corrupt_revision_or_history_cannot_restore_active(self):
  with self.initialize() as reg:self.consume(reg)
  with sqlite3.connect(self.path) as db:db.execute('UPDATE register_meta SET revision=0')
  with self.assertRaises(ledger.Refusal):self.open()
  self.assertEqual('QUARANTINED',self.authority._read()['phase'])
 def test_missing_custody_receipt_blocks_existing_database(self):
  with self.initialize() as reg:self.consume(reg)
  original=self.path.read_bytes();(self.authority.root/'receipt').unlink()
  with self.assertRaises(ledger.Refusal):self.open()
  self.assertEqual(original,self.path.read_bytes())
 def test_stale_custody_receipt_refuses(self):
  with self.initialize() as reg:
   receipt=(self.authority.root/'receipt').read_bytes();self.consume(reg)
  (self.authority.root/'receipt').write_bytes(receipt)
  with self.assertRaises(ledger.Refusal):self.open()
 def test_interrupted_prepare_prevents_retry_even_if_sqlite_rolled_back(self):
  with self.initialize() as reg:
   self.verified(reg);self.authority.fault='after_prepare'
   with self.assertRaises(ledger.Refusal):reg.consume(self.claims()['attempt_id'])
   self.assertEqual('VERIFIED',reg.get(self.claims()['attempt_id'])['state'])
   self.assertEqual('INTERRUPTED',self.authority._read()['phase'])
   self.authority.fault=None
   with self.assertRaises(ledger.Refusal):reg.consume(self.claims()['attempt_id'])
  with self.assertRaises(ledger.Refusal):self.open()
 def test_lost_receipt_after_sqlite_commit_never_reissues(self):
  with self.initialize() as reg:
   self.verified(reg);self.authority.fault='after_commit_receipt'
   with self.assertRaisesRegex(ledger.Refusal,'SIMULATED_LOST_RECEIPT'):reg.consume(self.claims()['attempt_id'])
   self.assertEqual('CONSUMED',reg.get(self.claims()['attempt_id'])['state'])
   with self.assertRaises(ledger.Refusal):reg.consume(self.claims()['attempt_id'])
  with self.assertRaises(ledger.Refusal):self.open()
 def test_terminal_custody_cannot_resume_or_bootstrap(self):
  with self.initialize() as reg:self.consume(reg)
  self.authority.terminate()
  with self.assertRaises(ledger.Refusal):self.open()
  with self.assertRaises(ledger.Refusal):self.authority.issue()
  self.assertEqual('TERMINAL',self.authority._read()['phase'])
 def test_sidecar_uncertainty_refuses_without_recovery(self):
  with self.initialize():pass
  sidecar=Path(str(self.path)+'-journal');sidecar.write_bytes(b'untrusted partial journal')
  original=self.path.read_bytes()
  with self.assertRaises(ledger.Refusal):self.open()
  self.assertEqual(original,self.path.read_bytes());self.assertTrue(sidecar.exists())
 def test_symlink_hardlink_fifo_never_opened_as_register(self):
  import os
  for kind in ['symlink','hardlink','fifo']:
   path=self.path.parent/(kind+'.sqlite3');authority=self.Custody(path);grant=authority.issue()
   with ledger._RegisterStore.initialize(path,authority,grant):pass
   if kind=='symlink':
    target=path.with_suffix('.target');path.rename(target);path.symlink_to(target)
   elif kind=='hardlink':os.link(path,path.with_suffix('.hardlink'))
   else:path.unlink();os.mkfifo(path)
   with self.assertRaises(ledger.Refusal):ledger._RegisterStore(path,authority)
 def test_mutation_checks_current_head_not_only_constructor(self):
  with self.initialize() as reg:
   with sqlite3.connect(self.path) as db:db.execute('UPDATE register_meta SET revision=7')
   with self.assertRaises(ledger.Refusal):reg.request(self.claims())
   self.assertIsNone(reg.get(self.claims()['attempt_id']))
 def test_restoring_database_does_not_clear_quarantine(self):
  with self.initialize() as reg:self.consume(reg)
  original=self.path.read_bytes();self.path.unlink()
  with self.assertRaises(ledger.Refusal):self.open()
  self.path.write_bytes(original);self.path.chmod(0o600)
  with self.assertRaises(ledger.Refusal):self.open()
  self.assertEqual('QUARANTINED',self.authority._read()['phase'])

 def test_missing_open_register_is_typed_and_never_recreated(self):
  with self.initialize() as reg:
   self.consume(reg);self.path.unlink()
   with self.assertRaises(ledger.Refusal):reg.request(self.claims()|{'attempt_id':'6'*32,'slot':2})
  self.assertFalse(self.path.exists())
  self.assertEqual('QUARANTINED',self.authority._read()['phase'])

class LaunchObservationTests(unittest.TestCase):
 def test_successful_launch_path_rechecks_pid1_token_and_incarnation(self):
  from unittest.mock import patch
  import os
  from custody_fixture import storage
  import contract as c
  release={key:'1'*64 for key in c.HASH_FIELDS}|{'source_tree':c.D02_TREE,'candidate_tree':'8'*40,
   'boot_id':'c5b62809-638c-421c-84fb-8b2f1663e6be','campaign':c.CAMPAIGN,'schema':'p08-host-development-release-1',
   'suite':c.SUITE,'scope':c.SCOPE,'attempt_id':'2'*32,'release_id':'3'*32,'nonce':'4'*64,'slot':1,
   'issued_at':1000,'not_before':1000,'expires_at':1120}
  token=c.digest(c.canonical(release));attempt=release['attempt_id']
  props=FixTests.props(self)|{'Description':'p08-d03:'+attempt+':'+token}
  class FixtureHost(host.Host):
   def __init__(self,observations):self.observations=iter(observations);self.effects=[]
   def show(self,*args):return next(self.observations)
   def signature(self,*args):pass
   def check_live(self,*args):pass
   def native(self,operation):self.effects.append(operation.name);return {'Created':'yes'}
   def observe(self,*args):return {'start':'synthetic-no-process'}
   def recover(self,*args):return {'fixture_only':'NO_PROCESS_CREATED'}
  with tempfile.TemporaryDirectory(dir=ROOT/'scratch') as directory:
   for index,change in enumerate([{'Description':'stale'},{'InvocationID':'6'*32},{'Transient':'no'},
     {'Id':'foreign.service'},{'MainPID':'124'},{'RootDirectory':'/foreign'},{'ControlGroup':'/foreign'}]):
    fixture=FixtureHost([{'LoadState':'not-found'},props,props|change])
    with storage.Register(Path(directory)/(str(index)+'.db')) as reg,\
      patch.object(host,'root_read',return_value=c.canonical(release)),\
      patch.object(host,'exclusive_write'),patch.object(host.os,'pidfd_open',side_effect=lambda pid:os.open('/dev/null',os.O_RDONLY)),\
      patch.object(host.select,'select',return_value=([],[],[])):
     with self.assertRaises(c.Refusal):fixture.launch(attempt,reg)
     self.assertEqual(['CREATE'],fixture.effects)
     self.assertEqual('CONSUMED',reg.get(attempt)['state'])
     self.assertEqual('INTERRUPTED',reg.get(attempt)['execution'])
     self.assertNotIn('RUNNING',reg.execution_history(attempt))
 def test_exit_observation_allows_zero_pid_but_not_changed_token(self):
  props=FixTests.props(self)
  self.assertEqual('5'*32,host.check_launch_identity(props|{'MainPID':'0'},'2'*32,'7'*64,props,require_pid=False))
  for change in [{'Description':'stale'},{'Transient':'no'},{'InvocationID':'6'*32}]:
   with self.assertRaises(ledger.Refusal):
    host.check_launch_identity(props|change|{'MainPID':'0'},'2'*32,'7'*64,props,require_pid=False)
