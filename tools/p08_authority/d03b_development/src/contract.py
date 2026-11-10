"""D03 development contracts. Pure validation does not grant host authority."""
from dataclasses import dataclass
import hashlib
import json
import re

D02_TREE = '119ee64ee314cd8f8852a620f063f89a39e16192'
SUITE = 'd03-restricted-runner-smoke'
SCOPE = 'OWNER_MEDIATED_RESTRICTED_WORKER_DEVELOPMENT_ONLY'
CAMPAIGN = 'P08-R1B-HOST-DEV-01'
ROOT = '/var/lib/software-factory/p08-r1b-host-dev/' + CAMPAIGN
NAMESPACE = 'symphony.p08.d03.development.v1'
ROUTE_NAMESPACE = 'symphony.p08.d03.source-route.v1'
HASH_FIELDS = frozenset({'host_source_sha256','image_manifest_sha256','runtime_manifest_sha256',
                        'profile_sha256','fixture_profile_sha256','route_approval_sha256','worker_runtime_sha256'})
BINDINGS = HASH_FIELDS | {'source_tree','candidate_tree','boot_id','campaign'}
FIELDS = BINDINGS | {'schema','suite','scope','attempt_id','release_id','nonce','slot',
                     'issued_at','not_before','expires_at'}
TERMINAL = frozenset({'CONSUMED','EXPIRED','REVOKED','REJECTED'})
NEXT = {None: {'REQUESTED'}, 'REQUESTED': {'ISSUED','EXPIRED','REVOKED','REJECTED'},
        'ISSUED': {'VERIFIED','EXPIRED','REVOKED','REJECTED'},
        'VERIFIED': {'RELEASED','EXPIRED','REVOKED','REJECTED'},
        'RELEASED': {'CONSUMED','EXPIRED','REVOKED','REJECTED'}}


class Refusal(RuntimeError):
    def __init__(self, code):self.code = code;super().__init__(code)


def require(condition, code):
    if not condition:raise Refusal(code)


def canonical(value):return json.dumps(value, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')


def digest(raw):return hashlib.sha256(raw).hexdigest()


def hex_id(value, length):
    return type(value) is str and re.fullmatch('[0-9a-f]{' + str(length) + '}', value) is not None and value != '0' * length


def parse_json(raw, code='INPUT_MALFORMED', limit=65536):
    def unique(pairs):
        result = {}
        for key, value in pairs:
            if key in result:raise ValueError('duplicate')
            result[key] = value
        return result
    try:
        require(type(raw) is bytes and 0 < len(raw) <= limit, code)
        value = json.loads(raw.decode('ascii'), object_pairs_hook=unique)
        require(canonical(value) == raw, code)
        return value
    except (ValueError, TypeError, UnicodeError, RecursionError):raise Refusal(code) from None


def parse_release(raw):
    value = parse_json(raw, 'RELEASE_MALFORMED')
    require(type(value) is dict and set(value) == FIELDS, 'RELEASE_MALFORMED')
    require(value['schema'] == 'p08-host-development-release-1' and value['suite'] == SUITE and
            value['scope'] == SCOPE and value['source_tree'] == D02_TREE and value['campaign'] == CAMPAIGN,
            'RELEASE_MALFORMED')
    require(hex_id(value['candidate_tree'],40), 'RELEASE_MALFORMED')
    require(all(hex_id(value[key], 64) for key in HASH_FIELDS | {'nonce'}) and
            all(hex_id(value[key], 32) for key in ['attempt_id','release_id']) and
            type(value['boot_id']) is str and re.fullmatch('[0-9a-f-]{36}', value['boot_id']) is not None,
            'RELEASE_MALFORMED')
    require(type(value['slot']) is int and 1 <= value['slot'] <= 8 and
            all(type(value[key]) is int and value[key] >= 0 for key in ['issued_at','not_before','expires_at']) and
            value['issued_at'] <= value['not_before'] < value['expires_at'] <= value['issued_at'] + 120,
            'RELEASE_MALFORMED')
    return value


def check_binding(release, bindings, now):
    require(type(bindings) is dict and set(bindings) == BINDINGS and
            all(release.get(key) == value for key, value in bindings.items()), 'RELEASE_BINDING_MISMATCH')
    require(release['issued_at'] <= release['not_before'] <= now < release['expires_at'] and
            0 <= now - release['issued_at'] <= 120, 'RELEASE_TIME_INVALID')


def check_root_metadata(value):
    require(type(value) is dict and value == {'uid': 0, 'mode': value.get('mode'), 'regular': True,
            'nlink': 1, 'alias': False} and type(value['mode']) is int and not value['mode'] & 0o022,
            'HOST_CUSTODY_UNPROVEN')


@dataclass(frozen=True)
class SourceRouteEnrollment:
    """Fixed-worker receipt assembled after external owner signature and root custody checks.

    The object is not a capability. The live host also checks the installed
    route manifest, signature, boot/time and actual transient worker boundary.
    """
    campaign: str
    boot_id: str
    route_manifest_sha256: str
    approval_sha256: str
    expires_at: int


def require_source_route_enrollment(value):
    require(type(value) is SourceRouteEnrollment and value.campaign == CAMPAIGN and
            hex_id(value.route_manifest_sha256, 64) and hex_id(value.approval_sha256, 64),
            'UNRESTRICTED_AGENT_ROUTE_UNENROLLED')
    return value


def check_worker_route(value):
    keys = {'uid','gid','groups','nnp','caps','mount_private','network_private','initial_user_namespace',
            'root_matches','cgroup_matches','stdio_only','unit_profile_matches','invocation_matches'}
    require(type(value) is dict and set(value) == keys and type(value['uid']) is int and
            61184 <= value['uid'] <= 65519 and value['gid'] == value['uid'] and
            value['groups'] in ([], [value['gid']]) and value['caps'] == [0] * 5 and value['nnp'] == 1 and
            all(value[key] is True for key in keys - {'uid','gid','groups','caps','nnp'}), 'WORKER_ROUTE_UNPROVEN')
    return 'EXACT_RESTRICTED_WORKER_ONLY'


def unit_name(attempt):
    require(hex_id(attempt, 32), 'ATTEMPT_INVALID')
    return 'p08-d03-worker.service'


def worker_properties():
    return {'Type':'exec', 'DynamicUser':'yes', 'SupplementaryGroups':'', 'MountAPIVFS':'yes',
        'PrivateTmp':'yes', 'PrivateNetwork':'yes', 'PrivateDevices':'yes', 'PrivateIPC':'yes',
        'ProtectHome':'yes', 'ProtectSystem':'strict', 'ProtectKernelTunables':'yes',
        'ProtectKernelModules':'yes', 'ProtectKernelLogs':'yes', 'ProtectControlGroups':'yes',
        'NoNewPrivileges':'yes', 'CapabilityBoundingSet':'', 'AmbientCapabilities':'',
        'RestrictSUIDSGID':'yes', 'RestrictRealtime':'yes', 'LockPersonality':'yes',
        'RestrictAddressFamilies':'AF_UNIX', 'RestrictNamespaces':'yes', 'KillMode':'control-group',
        'SendSIGKILL':'yes', 'TimeoutStopSec':'2s', 'RuntimeMaxSec':'20s', 'CPUQuota':'50%',
        'MemoryMax':'256M', 'TasksMax':'16', 'UMask':'0077', 'RemainAfterExit':'yes',
        'ProtectProc':'invisible', 'ProcSubset':'pid', 'Delegate':'no', 'KeyringMode':'private',
        'LimitCORE':'0', 'LimitFSIZE':'8M', 'StandardInput':'null'}


def check_pid1_exit(props, attempt, invocation, populated, *, pinned_pid):
    """Match terminal PID1 evidence to the original pidfd-pinned launch PID.

    Host.launch retains that pidfd and the observed process start identity.
    This pure comparison does not authenticate an arbitrary caller's PID claim.
    """
    try:
        require(type(pinned_pid) is int and pinned_pid > 0 and
                type(props) is dict and props.get('Id') == unit_name(attempt) and
                hex_id(invocation, 32) and props.get('InvocationID') == invocation and
                props.get('ExecMainPID') == str(pinned_pid) and
                props.get('MainPID') in ['0', str(pinned_pid)] and
                populated is False, 'HOST_EXIT_UNPROVEN')
        code, status = int(props['ExecMainCode']), int(props['ExecMainStatus'])
        require(code in [1, 2, 3] and 0 <= status <= 255, 'HOST_EXIT_UNPROVEN')
        return status if code == 1 else -status
    except (ValueError, KeyError, TypeError):raise Refusal('HOST_EXIT_UNPROVEN') from None


def check_canary_denial(known_present, error_number):
    require(known_present is True and type(error_number) is int and error_number in {1,13}, 'CANARY_DENIAL_UNPROVEN')


def check_cleanup(witness):
    required={'unit_terminal','cgroup_empty','reference_released','runtime_absent','credentials_absent','mounts_absent'}
    require(type(witness) is dict and set(witness)==required and all(v is True for v in witness.values()), 'CLEANUP_UNCERTAIN')
    return 'CLEANUP_OBSERVED'


def check_worker_environment(environment,invocation):
    fixed={'HOME':'/output/home','PATH':'/nonexistent','LANG':'C.UTF-8','LC_ALL':'C.UTF-8',
        'INVOCATION_ID':invocation,'CREDENTIALS_DIRECTORY':'/run/credentials/p08-d03-worker.service'}
    optional={'USER','LOGNAME','SHELL','SYSTEMD_EXEC_PID','JOURNAL_STREAM','MEMORY_PRESSURE_WATCH','MEMORY_PRESSURE_WRITE'}
    require(type(environment) is dict and set(fixed)<=set(environment)<=set(fixed)|optional and
        all(environment[key]==value for key,value in fixed.items()),'WORKER_ENVIRONMENT_UNPROVEN')
