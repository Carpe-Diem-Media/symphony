"""Pure contract tests use modeled observations, never live host authority."""
import copy
import importlib.util
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]


class ContractTests(unittest.TestCase):
    def setUp(self):
        path = ROOT / 'src/contract.py'
        self.assertTrue(path.is_file(), 'D03A host contract is absent')
        if 'contract' not in sys.modules:
            spec = importlib.util.spec_from_file_location('contract', path)
            module = importlib.util.module_from_spec(spec);sys.modules[spec.name] = module;spec.loader.exec_module(module)
        self.c = sys.modules['contract']

    def bindings(self):
        return {key: '1' * 64 for key in self.c.HASH_FIELDS} | {'source_tree': self.c.D02_TREE,'candidate_tree':'8'*40,
            'boot_id': 'c5b62809-638c-421c-84fb-8b2f1663e6be', 'campaign': 'P08-R1B-HOST-DEV-01'}

    def release(self):
        return self.bindings() | {'schema': 'p08-host-development-release-1', 'suite': self.c.SUITE,
            'scope': self.c.SCOPE, 'attempt_id': '2' * 32, 'release_id': '3' * 32,
            'nonce': '4' * 64, 'slot': 1, 'issued_at': 1000, 'not_before': 1000, 'expires_at': 1120}

    def refuses(self, code, operation, *args, **kwargs):
        with self.assertRaises(self.c.Refusal) as caught:operation(*args, **kwargs)
        self.assertEqual(code, caught.exception.code)

    def test_canonical_closed_release_parses(self):
        self.assertEqual(self.release(), self.c.parse_release(self.c.canonical(self.release())))

    def test_approval_or_extra_field_does_not_grant_authority(self):
        self.refuses('RELEASE_MALFORMED', self.c.parse_release, self.c.canonical(self.release() | {'approved': True}))

    def test_duplicate_noncanonical_or_oversized_json_refuses(self):
        for raw in [b'{"x":1,"x":2}', json.dumps(self.release()).encode(), b'x' * 65537, b'[]']:
            self.refuses('RELEASE_MALFORMED', self.c.parse_release, raw)

    def test_all_source_runtime_route_and_profile_bindings_are_exact(self):
        for key in self.bindings():
            changed = self.release() | {key: 'wrong'}
            self.refuses('RELEASE_BINDING_MISMATCH', self.c.check_binding, changed, self.bindings(), 1001)

    def test_valid_bounded_lease(self):self.c.check_binding(self.release(), self.bindings(), 1001)

    def test_expired_future_and_stale_lease_refuse(self):
        for now in [999, 1120, 1401]:self.refuses('RELEASE_TIME_INVALID', self.c.check_binding, self.release(), self.bindings(), now)

    def test_boolean_or_unbounded_lease_and_slot_refuse(self):
        for key, value in [('slot', True), ('slot', 9), ('expires_at', 2000), ('issued_at', True), ('attempt_id', '../x')]:
            self.refuses('RELEASE_MALFORMED', self.c.parse_release, self.c.canonical(self.release() | {key: value}))

    def test_suite_and_scope_cannot_be_transferred(self):
        for key in ['suite', 'scope']:
            self.refuses('RELEASE_MALFORMED', self.c.parse_release, self.c.canonical(self.release() | {key: 'production'}))

    def route(self):
        return {'uid': 62001, 'gid': 62001, 'groups': [62001], 'nnp': 1, 'caps': [0] * 5,
            'mount_private': True, 'network_private': True, 'initial_user_namespace': True,
            'root_matches': True, 'cgroup_matches': True, 'stdio_only': True,
            'unit_profile_matches': True, 'invocation_matches': True}

    def test_restricted_worker_observation_is_finite_scope_only(self):
        self.assertEqual('EXACT_RESTRICTED_WORKER_ONLY', self.c.check_worker_route(self.route()))

    def test_source_account_or_privileged_worker_refuses(self):
        for value in [self.route() | {'uid': 1000}, self.route() | {'groups': [62001, 987]},
                      self.route() | {'caps': [0, 1, 0, 0, 0]}, self.route() | {'nnp': 0}]:
            self.refuses('WORKER_ROUTE_UNPROVEN', self.c.check_worker_route, value)

    def test_each_uncertain_route_observation_refuses(self):
        for key in self.route():
            if key in ['uid', 'gid', 'groups', 'nnp', 'caps']:continue
            self.refuses('WORKER_ROUTE_UNPROVEN', self.c.check_worker_route, self.route() | {key: False})

    def test_worker_observation_cannot_certify_unrestricted_agent(self):
        self.refuses('UNRESTRICTED_AGENT_ROUTE_UNENROLLED', self.c.require_source_route_enrollment, None)
        self.refuses('UNRESTRICTED_AGENT_ROUTE_UNENROLLED', self.c.require_source_route_enrollment, {'approved': True})

    def test_root_custody_rejects_author_owned_symlink_and_writable_paths(self):
        valid = {'uid': 0, 'mode': 0o600, 'regular': True, 'nlink': 1, 'alias': False}
        self.c.check_root_metadata(valid)
        for key, value in [('uid', 1000), ('mode', 0o660), ('regular', False), ('nlink', 2), ('alias', True)]:
            self.refuses('HOST_CUSTODY_UNPROVEN', self.c.check_root_metadata, valid | {key: value})

    def test_pid1_exit_and_empty_cgroup_are_both_required(self):
        props = {'Id': self.c.unit_name('2' * 32), 'InvocationID': '5' * 32,
                 'MainPID': '0', 'ExecMainPID': '123', 'ExecMainCode': '1', 'ExecMainStatus': '0'}
        self.assertEqual(0, self.c.check_pid1_exit(props, '2' * 32, '5' * 32, False, pinned_pid=123))
        self.refuses('HOST_EXIT_UNPROVEN', self.c.check_pid1_exit, props, '2' * 32, '5' * 32, True, pinned_pid=123)
        for key in ['Id', 'InvocationID', 'ExecMainPID', 'ExecMainCode']:
            self.refuses('HOST_EXIT_UNPROVEN', self.c.check_pid1_exit, props | {key: 'wrong'}, '2' * 32, '5' * 32, False, pinned_pid=123)

    def test_actual_killed_status_is_preserved(self):
        props = {'Id': self.c.unit_name('2' * 32), 'InvocationID': '5' * 32,
                 'MainPID': '0', 'ExecMainPID': '123', 'ExecMainCode': '2', 'ExecMainStatus': '9'}
        self.assertEqual(-9, self.c.check_pid1_exit(props, '2' * 32, '5' * 32, False, pinned_pid=123))

    def test_profile_has_no_generic_admin_or_network_route(self):
        profile = self.c.worker_properties()
        for key in ['CapabilityBoundingSet', 'AmbientCapabilities', 'SupplementaryGroups']:self.assertEqual('', profile[key])
        self.assertEqual('AF_UNIX', profile['RestrictAddressFamilies'])
        self.assertEqual('20s', profile['RuntimeMaxSec'])
        self.assertEqual('256M', profile['MemoryMax'])
        self.assertEqual('16', profile['TasksMax'])
        self.assertEqual('control-group', profile['KillMode'])


if __name__ == '__main__':unittest.main(verbosity=2)
