"""Pure protocol and negative admission tests; no issuer keys or signatures."""
import copy
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sys
import tempfile
import unittest


class DevelopmentReleaseTests(unittest.TestCase):
    def setUp(self):
        path = Path(__file__).with_name('p08_development_release.py')
        self.assertTrue(path.is_file(), 'owner-pinned development release protocol is not implemented')
        if 'p08_development_release' not in sys.modules:
            spec = importlib.util.spec_from_file_location('p08_development_release', path)
            module = importlib.util.module_from_spec(spec)
            sys.modules[spec.name] = module
            spec.loader.exec_module(module)
        self.p = sys.modules['p08_development_release']
        self.temp = tempfile.TemporaryDirectory(prefix='d01-negative-')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def refuses(self, code, fn, *args):
        with self.assertRaises(self.p.Refusal) as raised:
            fn(*args)
        self.assertEqual(code, raised.exception.code)

    def release(self):
        return {'schema':'p08-owner-development-release-1', 'task':self.p.TASK,
            'issuer':'ORIGINAL_SYMPHONY_OWNER','profile_id':self.p.PROFILE,
            'source_base_commit':self.p.BASE_COMMIT,'source_tree':'1'*40,
            'source_inventory_sha256':'2'*64,'runtime_inventory_sha256':'3'*64,
            'fixture_profile_sha256':self.p.FIXTURE_HASH,'command_sha256':'4'*64,
            'suite':self.p.SUITE,'attempt_id':'5'*32,'release_id':'6'*32,'nonce':'7'*64,
            'scope':self.p.SCOPE,'issued_at':1000,'not_before':1000,'expires_at':1300}

    def bindings(self, record=None):
        value=record or self.release()
        return {key:value[key] for key in self.p.BINDING_FIELDS}

    def test_missing_owner_anchor_refuses(self):
        self.refuses('OWNER_TRUST_ANCHOR_UNCONFIRMED', self.p.validate_anchor, None, None)

    def test_partial_or_malformed_anchor_refuses(self):
        for key,fingerprint in ((None,'SHA256:x'),('ssh-rsa AAAA','SHA256:x'),
                                ('ssh-ed25519 !!!!','SHA256:x'),(True,True)):
            self.refuses('OWNER_TRUST_ANCHOR_INVALID',self.p.validate_anchor,key,fingerprint)

    def test_caller_cannot_supply_an_anchor_to_authentication(self):
        with self.assertRaises(TypeError):
            self.p.authenticate(self.root, '5'*32, trust_anchor='author-selected')

    def test_author_controlled_register_cannot_supply_host_authority(self):
        self.refuses('DEVELOPMENT_HOST_CUSTODY_UNCONFIGURED',self.p.require_host_custody,self.root,self.release())
        with self.assertRaises(TypeError):
            self.p.require_host_custody(self.root,self.release(),approved=True)

    def test_environment_is_not_an_anchor(self):
        old=os.environ.get('P08_OWNER_APPROVED')
        os.environ['P08_OWNER_APPROVED']='1'
        try:self.refuses('OWNER_TRUST_ANCHOR_UNCONFIRMED',self.p.validate_anchor,None,None)
        finally:
            if old is None:os.environ.pop('P08_OWNER_APPROVED',None)
            else:os.environ['P08_OWNER_APPROVED']=old

    def test_duplicate_unknown_and_noncanonical_release_refuse(self):
        raw=self.p.canonical(self.release())
        for bad in (raw+b'\n',b'{"x":1,"x":2}',self.p.canonical(dict(self.release(),approved=True)),b'[]'):
            self.refuses('RELEASE_MALFORMED',self.p.parse_release,bad)

    def test_oversized_release_refuses(self):
        self.refuses('RELEASE_MALFORMED',self.p.parse_release,b'x'*65537)

    def test_wrong_issuer_scope_suite_and_profile_refuse(self):
        for key,value in (('issuer','SOURCE_PREPARER'),('scope','PRODUCTION'),('suite','gate'),
                          ('profile_id','author-profile'),('source_base_commit','0'*40)):
            self.refuses('RELEASE_MALFORMED',self.p.parse_release,self.p.canonical(dict(self.release(),**{key:value})))

    def test_booleans_invalid_hashes_and_unbounded_lease_refuse(self):
        for key,value in (('issued_at',True),('source_tree','x'*40),('attempt_id','../alias'),
                          ('expires_at',1901),('not_before',999)):
            self.refuses('RELEASE_MALFORMED',self.p.parse_release,self.p.canonical(dict(self.release(),**{key:value})))

    def test_exact_claims_parse_without_granting_authority(self):
        value=self.p.parse_release(self.p.canonical(self.release()))
        self.assertEqual(self.release(),value)
        self.assertIs(type(value),dict)
        self.assertNotIn('verified',value)

    def test_changed_binding_refuses_for_every_bound_field(self):
        for field in self.p.BINDING_FIELDS:
            expected=self.bindings();expected[field]='mismatch'
            self.refuses('RELEASE_BINDING_MISMATCH',self.p.validate_binding,self.release(),expected,1001)

    def test_future_expired_and_stale_release_refuse(self):
        self.refuses('RELEASE_NOT_YET_VALID',self.p.validate_binding,self.release(),self.bindings(),999)
        self.refuses('RELEASE_EXPIRED',self.p.validate_binding,self.release(),self.bindings(),1300)
        value=dict(self.release(),expires_at=1800)
        self.refuses('RELEASE_STALE',self.p.validate_binding,value,self.bindings(value),1301)

    def test_terminal_states_never_reopen(self):
        for state in ('CONSUMED','EXPIRED','REVOKED','REJECTED'):
            for target in ('REQUESTED','ISSUED','VERIFIED','RELEASED'):
                self.refuses('RELEASE_TRANSITION_INVALID',self.p.validate_transition,state,target)

    def test_transition_cannot_skip_verification_or_consumption(self):
        for source,target in ((None,'VERIFIED'),('REQUESTED','RELEASED'),('ISSUED','CONSUMED'),('VERIFIED','CONSUMED')):
            self.refuses('RELEASE_TRANSITION_INVALID',self.p.validate_transition,source,target)

    def test_journal_rejects_malformed_and_incomplete_history(self):
        path=self.root/'state';path.mkdir(mode=0o700)
        (path/'history.jsonl').write_bytes(b'{"state":"VERIFIED"}')
        self.refuses('RELEASE_HISTORY_INVALID',self.p.Journal,path,self.release())

    def test_journal_rejects_symlink_and_unsafe_directory(self):
        target=self.root/'real';target.mkdir(mode=0o700)
        alias=self.root/'alias';alias.symlink_to(target,target_is_directory=True)
        self.refuses('RELEASE_CUSTODY_UNCERTAIN',self.p.Journal,alias,self.release())
        target.chmod(0o755)
        self.refuses('RELEASE_CUSTODY_UNCERTAIN',self.p.Journal,target,self.release())

    def test_directory_ancestry_alias_and_missing_input_refuse(self):
        alias=self.root/'alias';alias.symlink_to(self.root,target_is_directory=True)
        self.refuses('RELEASE_CUSTODY_UNCERTAIN',self.p.check_directory_chain,alias)
        self.refuses('RELEASE_INPUT_MISSING',self.p.check_directory_chain,self.root/'missing')

    def test_one_use_marker_burns_attempt_even_without_history(self):
        path=self.root/'state'
        with self.p.Journal(path,self.release()) as journal:
            journal.reserve_once()
        with self.p.Journal(path,self.release()) as journal:
            self.refuses('RELEASE_REPLAYED',journal.reserve_once)

    def test_partial_marker_failure_does_not_restore_attempt(self):
        path=self.root/'state';path.mkdir(mode=0o700)
        (path/('release-'+'6'*32+'.json')).write_bytes(self.p.canonical(self.release()))
        with self.p.Journal(path,self.release()) as journal:
            self.refuses('RELEASE_REPLAYED',journal.reserve_once)

    def test_modified_marker_is_uncertainty_not_permission(self):
        path=self.root/'state';path.mkdir(mode=0o700)
        (path/('attempt-'+'5'*32+'.json')).write_bytes(b'not-json')
        with self.p.Journal(path,self.release()) as journal:
            self.refuses('RELEASE_REPLAYED',journal.reserve_once)

    def test_no_follow_and_bounded_public_input_reads(self):
        target=self.root/'input';target.write_bytes(b'x'*12)
        alias=self.root/'link';alias.symlink_to(target)
        self.refuses('RELEASE_INPUT_INVALID',self.p.read_regular,alias,16)
        self.refuses('RELEASE_INPUT_INVALID',self.p.read_regular,target,11)
        self.refuses('RELEASE_INPUT_MISSING',self.p.read_regular,self.root/'missing',16)

    def test_runtime_substitution_and_incomplete_inventory_refuse(self):
        path=self.root/'runtime';path.write_bytes(b'abc')
        entry={'path':str(path),'bytes':3,'sha256':hashlib.sha256(b'abc').hexdigest(),'mode':0o600}
        self.refuses('RUNTIME_CUSTODY_UNCERTAIN',self.p.check_runtime,
            {'schema':'p08-development-runtime-1','host':self.p.host_identity(),'entries':[entry]})

    def test_revocation_claim_requires_owner_signature(self):
        with self.assertRaises(TypeError):
            self.p.check_revocation(self.root,self.release(),approved=True)

    def test_dangling_revocation_entries_are_uncertainty_not_absence(self):
        handoff=self.root/'owner-handoff';handoff.mkdir()
        for name in ('revocation.json','revocation.sshsig'):
            (handoff/name).symlink_to(handoff/('missing-'+name))
        self.refuses('RELEASE_INPUT_INVALID',self.p.check_revocation,self.root/'candidate',self.release())

    def test_direct_receipt_and_callback_cannot_release(self):
        for field in ('verified','authenticated','callback','receipt','approved'):
            self.refuses('RELEASE_MALFORMED',self.p.parse_release,self.p.canonical(dict(self.release(),**{field:'yes'})))

    def test_baseline_inventory_is_closed_and_reconstructs_accepted_tree(self):
        path=Path(__file__).resolve().parents[3]/'owner-handoff/baseline-source.json'
        value=json.loads(path.read_bytes())
        self.assertEqual(407,len(self.p.baseline_entries(value)))
        self.assertEqual(self.p.BASE_TREE,self.p._tree_id(value['entries']))
        for bad in ({'schema':value['schema'],'entries':value['entries'][:-1]},
                    {'schema':value['schema'],'entries':value['entries']+[value['entries'][0]]}):
            self.refuses('SOURCE_INVENTORY_INVALID',self.p.baseline_entries,bad)

    def test_baseline_blob_mode_and_alias_substitution_refuse(self):
        path=Path(__file__).resolve().parents[3]/'owner-handoff/baseline-source.json'
        value=json.loads(path.read_bytes())
        for key,changed in [('git_blob','f'*40),('mode',0o600),('path','../alias'),('bytes',67108865)]:
            bad=copy.deepcopy(value);bad['entries'][0][key]=changed
            self.refuses('SOURCE_INVENTORY_INVALID',self.p.baseline_entries,bad)

    def test_real_candidate_inventory_is_closed_and_reproducible(self):
        root=Path(__file__).resolve().parents[2]
        value=self.p.source_inventory(root)
        self.assertEqual(409,len(value['entries']))
        self.assertEqual(value['tree'],self.p._tree_id(value['entries']))
        self.assertEqual(1,sum(entry['bytes']==30446771 for entry in value['entries']))

    def test_runtime_identity_mismatch_is_not_version_equivalence(self):
        entry=self.p._entry(Path(self.p.PYTHON));entry['sha256']='f'*64
        self.refuses('RUNTIME_IDENTITY_MISMATCH',self.p.check_runtime,
            {'schema':'p08-development-runtime-1','host':self.p.host_identity(),'entries':[entry]})

    def test_verifier_argv_is_bound_to_suite_process_and_namespace(self):
        root=self.root/'candidate';directory=self.root/'verification/123'
        argv=[self.p.SSH,'-Y','verify','-f',str(directory/'allowed-signers'),'-I',
              'symphony-owner-development','-n',self.p.NAMESPACE,'-s',str(directory/'release.sshsig')]
        self.assertTrue(self.p.permitted_verification(argv,root,123))
        self.assertFalse(self.p.permitted_verification(argv,root,124))
        for index,value in [(2,'sign'),(4,'/tmp/author-key'),(8,'production'),(10,'/tmp/other-signature')]:
            changed=argv.copy();changed[index]=value
            self.assertFalse(self.p.permitted_verification(changed,root,123))

    def test_unissued_workspace_never_admits_or_creates_output(self):
        candidate=self.root/'candidate';candidate.mkdir()
        expected='OWNER_TRUST_ANCHOR_UNCONFIRMED'if self.p.OWNER_CONFIRMED_PUBLIC_KEY is None else'RELEASE_INPUT_MISSING'
        self.refuses(expected,self.p.prepare_launch,candidate,'5'*32)
        self.assertEqual(['candidate'],sorted(path.name for path in self.root.iterdir()))

    def test_fixed_profile_suite_and_attempt_selection(self):
        args=['--profile',self.p.PROFILE,'--suite',self.p.SUITE,'--attempt','5'*32]
        self.assertEqual('5'*32,self.p.select_request(args))
        for index,value in [(1,'author-profile'),(3,'gate'),(4,'--public-key'),(5,'../attempt'),(5,'0'*32)]:
            bad=args.copy();bad[index]=value
            self.refuses('RELEASE_ARGUMENTS_INVALID',self.p.select_request,bad)
        self.refuses('RELEASE_ARGUMENTS_INVALID',self.p.select_request,args+['--approved'])


if __name__=='__main__':
    unittest.main(verbosity=2)
