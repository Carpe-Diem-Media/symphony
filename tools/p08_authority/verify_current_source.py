"""D02 R3 successor, source-only and not operationally enrolled.

Lifecycle: UNTRUSTED_INPUT -> TRUST_CONTEXT_SELECTED ->
SOURCE_REVIEW_AUTHENTICATED -> APPROVAL_CHAIN_AUTHENTICATED ->
GRANT_AUTHENTICATED -> EXECUTION_ADMISSION_CHECKED.

The operator independently authenticates accepted profile/review-authority
hashes and current facts before calling this API. Caller assertions are not an
operational trust boundary. No CLI installation or enrollment is provided.
All source checks precede grant authentication. Only the authenticated suffix
can attach authenticated_grant, preserving the shared gate's terminal refusal.
R2 remains immutable. Instance-local R3 schemas never replace gate.verify.
"""
import base64
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat
import struct
import subprocess
import tarfile

ROOT = Path(__file__).resolve().parent
MAX_RECORD = 16384
MAX_PROFILE = 1024 * 1024
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
FAMILY = "D02_CURRENT_SOURCE_REBIND_R3"
BASE_COMMIT = "47d770aa099c4aae8b70dea2b862aed148b5e383"
BASE_TREE = "6afa28cc5386944ec196e077f2c1f576dd8822e7"
C1_TREE = "101361b603828e111891b692f3881baeb748ec27"
PROJECTION_TREE = "600ed38175fde5ef9c81c38c0d47693ce6eba385"

class CurrentSourceVerifier:
    def __init__(self, legacy):
        self.Refusal = legacy.Refusal
        self.canonical = legacy.canonical
        self.sha256 = legacy.sha256
        self.contract = json.loads((ROOT / "record-schemas-current-source-r3.json").read_text("ascii"))
        self.SCHEMAS = self.contract["schemas"]
        self.PROFILE_RULES = json.loads((ROOT / "profile-requirements-current-source-r3.json").read_text("ascii"))
        self.SIGNABLE_FIXTURES = tuple(x["record"] for x in self.contract["signature_bindings"])


    def sha256(self, raw):
        return hashlib.sha256(raw).hexdigest()

    def _read_regular(self, path, limit, code):
        """Bound allocation before reading independently custodied record files."""
        try:
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK)
            try:
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode) or before.st_size > limit:
                    raise self.Refusal(code)
                raw = bytearray()
                while len(raw) <= limit:
                    block = os.read(fd, min(65536, limit + 1 - len(raw)))
                    if not block:
                        break
                    raw.extend(block)
                after = os.fstat(fd)
                if len(raw) > limit or (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                    raise self.Refusal(code)
                return bytes(raw)
            finally:
                os.close(fd)
        except OSError as error:
            raise self.Refusal(code) from error

    def _pairs(self, pairs):
        out = {}
        for key, value in pairs:
            if key in out:
                raise self.Refusal('FORMAT_INVALID')
            out[key] = value
        return out

    def _ascii_tree(self, value, depth=0):
        if depth > 32:
            raise self.Refusal('FORMAT_INVALID')
        if isinstance(value, dict):
            for key, child in value.items():
                if not isinstance(key, str) or not key.isascii() or any((ord(c) < 32 or ord(c) > 126 or c in '"\\' for c in key)):
                    raise self.Refusal('FORMAT_INVALID')
                self._ascii_tree(child, depth + 1)
        elif isinstance(value, list):
            for child in value:
                self._ascii_tree(child, depth + 1)
        elif isinstance(value, str):
            if not value.isascii() or any((ord(c) < 32 or ord(c) > 126 or c in '"\\' for c in value)):
                raise self.Refusal('FORMAT_INVALID')
        elif isinstance(value, int) and (not isinstance(value, bool)):
            if value < 0 or value > 18446744073709551615:
                raise self.Refusal('FORMAT_INVALID')
        else:
            raise self.Refusal('FORMAT_INVALID')

    def canonical(self, value):
        self._ascii_tree(value)
        try:
            return json.dumps(value, ensure_ascii=True, sort_keys=True, separators=(',', ':'), allow_nan=False).encode('ascii')
        except (TypeError, ValueError, UnicodeError):
            raise self.Refusal('FORMAT_INVALID')

    def _validate_schema(self, value, schema):
        if schema.get('type') == 'object':
            if not isinstance(value, dict) or set(value) != set(schema['required']):
                raise self.Refusal('FORMAT_INVALID')
            for key, child in value.items():
                self._validate_schema(child, schema['properties'][key])
            return
        typ = schema.get('type')
        if typ == 'array':
            if not isinstance(value, list):
                raise self.Refusal('FORMAT_INVALID')
            if 'minItems' in schema and len(value) < schema['minItems']:
                raise self.Refusal('FORMAT_INVALID')
            if 'maxItems' in schema and len(value) > schema['maxItems']:
                raise self.Refusal('FORMAT_INVALID')
            for item in value:
                self._validate_schema(item, schema['items'])
        elif typ == 'string':
            if not isinstance(value, str):
                raise self.Refusal('FORMAT_INVALID')
            if 'pattern' in schema and (not re.fullmatch(schema['pattern'], value)):
                raise self.Refusal('FORMAT_INVALID')
        elif typ == 'integer':
            if not isinstance(value, int) or isinstance(value, bool):
                raise self.Refusal('FORMAT_INVALID')
            if not schema.get('minimum', 0) <= value <= schema.get('maximum', 18446744073709551615):
                raise self.Refusal('FORMAT_INVALID')
        elif typ == 'boolean':
            if not isinstance(value, bool):
                raise self.Refusal('FORMAT_INVALID')
        elif typ:
            raise self.Refusal('FORMAT_INVALID')
        if 'const' in schema and value != schema['const']:
            raise self.Refusal('FORMAT_INVALID')
        if 'const' in schema and type(value) is not type(schema['const']):
            raise self.Refusal('FORMAT_INVALID')
        if 'enum' in schema and value not in schema['enum']:
            raise self.Refusal('FORMAT_INVALID')
        if isinstance(value, str) and 'maxLength' in schema and (len(value.encode('ascii')) > schema['maxLength']):
            raise self.Refusal('FORMAT_INVALID')

    def parse_record(self, raw, record_filename):
        if not isinstance(raw, bytes) or len(raw) > self._record_limit(record_filename):
            raise self.Refusal('FORMAT_INVALID')
        try:
            value = json.loads(raw.decode('ascii'), object_pairs_hook=self._pairs, parse_float=lambda _: (_ for _ in ()).throw(self.Refusal('FORMAT_INVALID')), parse_constant=lambda _: (_ for _ in ()).throw(self.Refusal('FORMAT_INVALID')))
        except self.Refusal:
            raise
        except Exception:
            raise self.Refusal('FORMAT_INVALID')
        self._ascii_tree(value)
        if self.canonical(value) != raw:
            raise self.Refusal('FORMAT_INVALID')
        try:
            schema = self.SCHEMAS[record_filename]
        except KeyError:
            raise self.Refusal('FORMAT_INVALID')
        self._validate_schema(value, schema)
        if any((isinstance(v, str) and k.endswith('_sha256') and (v == '0' * 64) for k, v in value.items())):
            raise self.Refusal('FORMAT_INVALID')
        return value

    def parse_profile(self, raw, profile_kind):
        limit = 16 * 1024 * 1024 if profile_kind == 'input-inventory' else MAX_PROFILE
        if not isinstance(raw, bytes) or len(raw) > limit:
            raise self.Refusal('FORMAT_INVALID')
        try:
            value = json.loads(raw.decode('ascii'), object_pairs_hook=self._pairs, parse_float=lambda _: (_ for _ in ()).throw(self.Refusal('FORMAT_INVALID')), parse_constant=lambda _: (_ for _ in ()).throw(self.Refusal('FORMAT_INVALID')))
        except self.Refusal:
            raise
        except Exception:
            raise self.Refusal('FORMAT_INVALID')
        self._ascii_tree(value)
        if self.canonical(value) != raw:
            raise self.Refusal('FORMAT_INVALID')
        if profile_kind not in self.PROFILE_RULES['profiles']:
            raise self.Refusal('FORMAT_INVALID')
        self._validate_profile(value, self.PROFILE_RULES['profiles'][profile_kind], profile_kind)
        return value

    def _record_limit(self, filename):
        rules = json.loads((ROOT / 'record-schemas-current-source-r3.json').read_text('ascii'))['canonical_byte_rules']
        if filename in ('build-input-approval.json', 'generated-input-approval.json'):
            return rules['manifest_max_bytes']
        if filename in ('native-execution-grant.json', 'generated-native-execution-grant.json'):
            return rules['generated_grant_max_bytes']
        if filename == 'compilation-result.json':
            return rules['compilation_result_max_bytes']
        return rules['other_record_max_bytes']

    def _validate_profile(self, value, rule, profile_kind):
        if not isinstance(value, dict) or set(value) != set(rule['required']):
            raise self.Refusal('FORMAT_INVALID')
        for field, descriptor in rule['types'].items():
            self._check_profile_value(field, value[field], descriptor, profile_kind)
        schema_value = rule['types'].get('schema', '')
        if schema_value.startswith('p08-') and value.get('schema') != schema_value:
            raise self.Refusal('FORMAT_INVALID')
        if profile_kind == 'rust-provenance-profile':
            fixed = {'policy_decision_id': '5f6773bc-83ef-498f-b468-bd49d809b914', 'certificate_sha256': 'e54b09a439647e006b4831eec9785cbaaf3e07ab371c3a6ee6a68e1bdb9fbc6b', 'manifest_sha256': 'a7c8774a5fd8441c997d94c029776cbc5eb111e9d72ab5d256fa69866644347e', 'manifest_signature_sha256': 'a9fed69b47daaaf29a6207af9df13aedb66d502ab0acc4ea557602edf87fd1aa', 'primary_fingerprint': '108f66205eaeb0aaa8dd5e1c85ab96e6fa1be5fe', 'signature_algorithm': 'RSA/SHA512 primary direct signature', 'signature_time': '2026-09-03T12:54:14Z'}
            if any((value.get(key) != expected for key, expected in fixed.items())):
                raise self.Refusal('PROVENANCE_INVALID')
            archives = {x['id']: x['sha256'] for x in value['archives']}
            if archives != {'cargo': 'ea1de9f9e23107d97ee2b41a72c552f34064a593da503789218387aee59f3ba4', 'rustc': 'e974f036b28565f37c0f3bd92ddefa809bee16c04f9dcf07b9ed96e05aaaf7c4', 'ruststd_host': 'fa3ff450172a16c026944030230c5069947af93c728d9179971d44e5e0cfb561', 'ruststd_musl': 'bd9f35880de21dab0e387e84009c00001ae7836a4ba565cb16823f13f75f325f'}:
                raise self.Refusal('PROVENANCE_INVALID')

    def _check_entry(self, value, kind):
        spec = self.PROFILE_RULES['common']['entry_types'][kind]
        if not isinstance(value, dict) or set(value) != set(spec['required']):
            raise self.Refusal('FORMAT_INVALID')
        for field, descriptor in spec['types'].items():
            item = value[field]
            if field not in ('symlink_chain', 'namespaces') and 'u64' not in descriptor and (not isinstance(item, str)):
                raise self.Refusal('FORMAT_INVALID')
            if isinstance(item, list):
                if field not in ('symlink_chain', 'namespaces') or len(item) > 32 or (all((isinstance(x, str) for x in item)) and len(item) != len(set(item))):
                    raise self.Refusal('FORMAT_INVALID')
                if 'hex64' in descriptor and any((not isinstance(x, str) or not HEX64.fullmatch(x) for x in item)):
                    raise self.Refusal('FORMAT_INVALID')
                continue
            if 'hex64' in descriptor and (not isinstance(item, str) or not HEX64.fullmatch(item) or item == '0' * 64):
                raise self.Refusal('FORMAT_INVALID')
            if 'hex40' in descriptor and (not isinstance(item, str) or not re.fullmatch('[0-9a-f]{40}', item)):
                raise self.Refusal('FORMAT_INVALID')
            if 'u64' in descriptor and (not isinstance(item, int) or isinstance(item, bool) or (not 0 <= item < 2 ** 64)):
                raise self.Refusal('FORMAT_INVALID')
            if isinstance(item, str) and (not item.isascii() or len(item.encode('ascii')) > 4096):
                raise self.Refusal('FORMAT_INVALID')
            if not isinstance(item, (str, int)) or isinstance(item, bool):
                raise self.Refusal('FORMAT_INVALID')
            if field in ('id', 'principal') and (not isinstance(item, str) or not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,127}', item)):
                raise self.Refusal('FORMAT_INVALID')
            if field in ('path', 'resolved_path') and (not isinstance(item, str) or not item or len(item) > 512):
                raise self.Refusal('FORMAT_INVALID')
        if kind == 'authority_key':
            expected = {'project-owner-issuer': sorted(('symphony.p08.r3.source-stage.v3', 'symphony.p08.r3.input-owner.v2', 'symphony.p08.r3.native-grant.v3')), 'independent-reviewer': sorted(('symphony.p08.r3.input-review.v3', 'symphony.p08.r3.build-result.v2', 'symphony.p08.r3.source-review.v1'))}
            if value['role'] not in expected or value['namespaces'] != expected[value['role']]:
                raise self.Refusal('FORMAT_INVALID')
            principal = value['principal']
            if not re.fullmatch('[A-Za-z0-9][A-Za-z0-9._-]{0,127}', principal) or any((token in value['public_key'] for token in ('cert-', '@cert-authority', '*', '?'))):
                raise self.Refusal('FORMAT_INVALID')
        if kind == 'argument':
            if value['index'] > 100000 or len(value['value'].encode('ascii')) > 4096:
                raise self.Refusal('FORMAT_INVALID')
        if kind == 'source_file':
            if value['mode'] not in ('100644', '100755') or value['path'].startswith('/') or any((x in ('', '.', '..') for x in value['path'].split('/'))):
                raise self.Refusal('FORMAT_INVALID')
        if kind in ('closure_regular_file', 'closure_symlink', 'installed_artifact'):
            for field in ('path', 'resolved_path'):
                if field in value and (not value[field].startswith('/') or value[field].startswith('//') or os.path.normpath(value[field]) != value[field]):
                    raise self.Refusal('FORMAT_INVALID')
        if kind == 'closure_regular_file' and (value['kind'] != 'regular' or not re.fullmatch('[0-7]{4}', value['mode'])):
            raise self.Refusal('FORMAT_INVALID')
        if kind == 'closure_symlink' and (value['kind'] != 'symlink' or '\x00' in value['target'] or len(value['target'].encode('ascii')) > 512):
            raise self.Refusal('FORMAT_INVALID')
        if kind == 'environment' and (not re.fullmatch('[A-Z_][A-Z0-9_]*', value['name']) or any((x in value['name'].lower() for x in ('proxy', 'token', 'secret', 'credential', 'agent', 'password', 'auth', 'cookie', 'session', 'preload', 'library_path', 'pythonpath'))) or value['name'].endswith(('_KEY', '_PASS'))):
            raise self.Refusal('FORMAT_INVALID')

    def _check_profile_value(self, field, value, descriptor, kind):
        if field in ('purpose', 'verdict') and descriptor in ('INPUT_REVIEW_ONLY', 'ACTION_PREFLIGHT_ONLY', 'MATCH', 'ACTIVE', 'SEALED_READ_ONLY') and (value != descriptor):
            raise self.Refusal('FORMAT_INVALID')
        if field == 'exit_code':
            if type(value) is not int or value != 0:
                raise self.Refusal('FORMAT_INVALID')
        elif 'hex64' in descriptor:
            if not isinstance(value, str) or not HEX64.fullmatch(value) or set(value) == {'0'}:
                raise self.Refusal('FORMAT_INVALID')
        elif 'hex40' in descriptor:
            if not isinstance(value, str) or not re.fullmatch('[0-9a-f]{40}', value) or set(value) == {'0'}:
                raise self.Refusal('FORMAT_INVALID')
        elif 'u64' in descriptor or descriptor.startswith('1794201657'):
            if not isinstance(value, int) or isinstance(value, bool) or (not 0 <= value < 2 ** 64):
                raise self.Refusal('FORMAT_INVALID')
            if descriptor.startswith('1794201657') and value != 1794201657:
                raise self.Refusal('FORMAT_INVALID')
            ceilings = {'approval_max_age_s': 86400, 'lease_max_s': 900, 'clock_skew_max_s': 30, 'action_observation_max_age_s': 60}
            if field in ceilings and value != ceilings[field]:
                raise self.Refusal('FORMAT_INVALID')
        elif field == 'keys':
            if not isinstance(value, list) or len(value) != 2:
                raise self.Refusal('FORMAT_INVALID')
            for entry in value:
                self._check_entry(entry, 'authority_key')
        elif kind == 'input-inventory' and field == 'entries':
            if not isinstance(value, list) or len(value) > 100000:
                raise self.Refusal('FORMAT_INVALID')
            for entry in value:
                if not isinstance(entry, dict) or entry.get('kind') not in ('regular', 'symlink'):
                    raise self.Refusal('FORMAT_INVALID')
                self._check_entry(entry, 'closure_regular_file' if entry['kind'] == 'regular' else 'closure_symlink')
            paths = [entry['path'] for entry in value]
            if paths != sorted(set(paths)):
                raise self.Refusal('FORMAT_INVALID')
        elif descriptor.startswith('array of') or descriptor.startswith('nonempty array') or descriptor.startswith('exact four'):
            if not isinstance(value, list) or len(value) > 100000:
                raise self.Refusal('FORMAT_INVALID')
            entry_kind = next((name for name in self.PROFILE_RULES['common']['entry_types'] if re.search('(?<![A-Za-z0-9_])' + re.escape(name) + '(?![A-Za-z0-9_])', descriptor)), None)
            if entry_kind:
                for entry in value:
                    self._check_entry(entry, entry_kind)
            elif 'command-profile' in descriptor:
                for entry in value:
                    self._validate_profile(entry, self.PROFILE_RULES['profiles']['command-profile'], 'command-profile')
            else:
                raise self.Refusal('FORMAT_INVALID')
            if descriptor.startswith('nonempty') and (not value):
                raise self.Refusal('FORMAT_INVALID')
            if descriptor.startswith('exact four') and len(value) != 4:
                raise self.Refusal('FORMAT_INVALID')
            if entry_kind == 'argument' and [item['index'] for item in value] != list(range(len(value))):
                raise self.Refusal('FORMAT_INVALID')
            if entry_kind == 'source_file' and [item['path'] for item in value] != sorted({item['path'] for item in value}):
                raise self.Refusal('FORMAT_INVALID')
            if entry_kind == 'environment' and [item['name'] for item in value] != sorted({item['name'] for item in value}):
                raise self.Refusal('FORMAT_INVALID')
            ids = [entry.get('id') for entry in value if isinstance(entry, dict) and 'id' in entry]
            if ids and (len(ids) != len(value) or ids != sorted(set(ids))):
                raise self.Refusal('FORMAT_INVALID')
        elif 'installed_artifact' in descriptor:
            self._check_entry(value, 'installed_artifact')
        elif isinstance(value, str):
            if not value or len(value.encode('ascii')) > 4096:
                raise self.Refusal('FORMAT_INVALID')
            if field == 'working_directory' and (not value.startswith('/') or os.path.normpath(value) != value):
                raise self.Refusal('FORMAT_INVALID')
            enum_values = {'purpose': ('INPUT_REVIEW_ONLY', 'ACTION_PREFLIGHT_ONLY'), 'verdict': ('MATCH', 'ACTIVE', 'SEALED_READ_ONLY'), 'authorization_scope': ('BUILD_ONLY', 'INDEPENDENT_REBUILD', 'BUILD_IDENTITY_TEST_EXECUTION', 'CODEC_TEST_EXECUTION'), 'mode': ('100644', '100755'), 'platform': ('linux/amd64',), 'role': ('toolchain', 'host-std', 'musl-std', 'crt'), 'self_contained': ('ON', 'OFF'), 'static_form': ('STATIC_PIE', 'STATIC_NON_PIE'), 'signature_algorithm': ('RSA/SHA512 primary direct signature',)}.get(field)
            if enum_values and value not in enum_values:
                raise self.Refusal('FORMAT_INVALID')
            if 'hex32' in descriptor and (not re.fullmatch('[0-9a-f]{32}', value)):
                raise self.Refusal('FORMAT_INVALID')
            if field == 'authorization_scope' and value not in ('BUILD_ONLY', 'INDEPENDENT_REBUILD', 'BUILD_IDENTITY_TEST_EXECUTION', 'CODEC_TEST_EXECUTION'):
                raise self.Refusal('FORMAT_INVALID')
            if field == 'schema' and descriptor.startswith('p08-') and (value != descriptor):
                raise self.Refusal('FORMAT_INVALID')
            if field == 'platform' and value != 'linux/amd64':
                raise self.Refusal('FORMAT_INVALID')
            if field == 'mode' and value not in ('100644', '100755'):
                raise self.Refusal('FORMAT_INVALID')
        else:
            raise self.Refusal('FORMAT_INVALID')

    def validate_enrollment(self, profile, now):
        try:
            self._validate_profile(profile, self.PROFILE_RULES['profiles']['verifier-enrollment-profile'], 'verifier-enrollment-profile')
        except self.Refusal:
            raise self.Refusal('STATUS_INVALID')
        if profile.get('schema') != 'p08-verifier-enrollment-3':
            raise self.Refusal('STATUS_INVALID')
        keys = profile.get('keys')
        if not isinstance(keys, list) or len(keys) != 2:
            raise self.Refusal('ROLE_MISMATCH')
        roles = {k.get('role') for k in keys if isinstance(k, dict)}
        principals = [k.get('principal') for k in keys if isinstance(k, dict)]
        if roles != {'project-owner-issuer', 'independent-reviewer'} or len(set(principals)) != 2:
            raise self.Refusal('ROLE_MISMATCH')
        wire_keys = []
        for key in keys:
            if now < key['not_before'] or now >= key['expires_at'] or key['not_before'] >= key['expires_at']:
                raise self.Refusal('APPROVAL_STALE')
            if not isinstance(key.get('public_key'), str) or not key['public_key'].startswith('ssh-ed25519 '):
                raise self.Refusal('SIGNER_UNAUTHORIZED')
            try:
                fields = key['public_key'].split(' ')
                if len(fields) != 2:
                    raise ValueError
                wire = base64.b64decode(fields[1], validate=True)
                offset = 0
                n = struct.unpack('>I', wire[offset:offset + 4])[0]
                offset += 4
                algorithm = wire[offset:offset + n]
                offset += n
                n = struct.unpack('>I', wire[offset:offset + 4])[0]
                offset += 4
                public = wire[offset:offset + n]
                offset += n
                if algorithm != b'ssh-ed25519' or len(public) != 32 or offset != len(wire):
                    raise ValueError
            except Exception:
                raise self.Refusal('SIGNER_UNAUTHORIZED')
            if not HEX64.fullmatch(key.get('fingerprint', '')) or hashlib.sha256(wire).hexdigest() != key['fingerprint']:
                raise self.Refusal('SIGNER_UNAUTHORIZED')
            wire_keys.append(wire)
        if len(wire_keys) != 2 or wire_keys[0] == wire_keys[1]:
            raise self.Refusal('ROLE_MISMATCH')
        return {k['role']: k for k in keys}

    def verify_signature(self, record_filename, raw, signature_path, profile, now, allowed_signers_root):
        if record_filename not in self.SIGNABLE_FIXTURES:
            raise self.Refusal('VERIFIER_UNAPPROVED')
        roles = self.validate_enrollment(profile, now)
        record = self.parse_record(raw, record_filename)
        role = 'independent-reviewer' if record_filename in ('input-review.json', 'compilation-result.json', 'source-review-attestation.json') else 'project-owner-issuer'
        key = roles[role]
        principal = key['principal']
        namespace = {'source-stage-acceptance.json': 'symphony.p08.r3.source-stage.v3', 'owner-input-decision.json': 'symphony.p08.r3.input-owner.v2', 'native-execution-grant.json': 'symphony.p08.r3.native-grant.v3', 'generated-native-execution-grant.json': 'symphony.p08.r3.native-grant.v3', 'input-review.json': 'symphony.p08.r3.input-review.v3', 'compilation-result.json': 'symphony.p08.r3.build-result.v2', 'source-review-attestation.json': 'symphony.p08.r3.source-review.v1'}.get(record_filename)
        if not namespace or namespace not in key['namespaces']:
            raise self.Refusal('ROLE_MISMATCH')
        signer_leaf = 'reviewer' if role == 'independent-reviewer' else 'owner'
        signer_file = Path(allowed_signers_root) / signer_leaf
        try:
            if not signature_path.is_file() or not signer_file.is_file():
                raise self.Refusal('VERIFIER_UNAPPROVED')
        except AttributeError:
            signature_path = Path(signature_path)
            if not signature_path.is_file() or not signer_file.is_file():
                raise self.Refusal('VERIFIER_UNAPPROVED')
        try:
            sigraw = self._read_regular(signature_path, 4096, 'SIGNATURE_INVALID')
        except OSError:
            raise self.Refusal('SIGNATURE_INVALID')
        if not sigraw or len(sigraw) > 4096:
            raise self.Refusal('SIGNATURE_INVALID')
        wire_key, sig_namespace = self._decode_sshsig(sigraw)
        try:
            fields = key['public_key'].split(' ')
            expected_wire = base64.b64decode(fields[1], validate=True)
        except Exception:
            raise self.Refusal('SIGNER_UNAUTHORIZED')
        fingerprint = hashlib.sha256(wire_key).hexdigest()
        if wire_key != expected_wire:
            other_keys = {hashlib.sha256(base64.b64decode(k['public_key'].split(' ')[1], validate=True)).hexdigest() for k in roles.values() if k is not key}
            if fingerprint in other_keys:
                raise self.Refusal('ROLE_MISMATCH')
            raise self.Refusal('SIGNER_UNAUTHORIZED')
        if sig_namespace != namespace:
            raise self.Refusal('SIGNATURE_INVALID')
        try:
            result = subprocess.run(['/usr/bin/ssh-keygen', '-Y', 'verify', '-f', str(signer_file), '-I', principal, '-n', namespace, '-s', str(signature_path)], input=raw, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=5, check=False, env={'PATH': '/nonexistent', 'LC_ALL': 'C.UTF-8', 'LANG': 'C.UTF-8'})
        except subprocess.TimeoutExpired as error:
            raise self.Refusal('SIGNATURE_VERIFIER_TIMEOUT') from error
        except OSError as error:
            raise self.Refusal('SIGNATURE_VERIFIER_UNAVAILABLE') from error
        if len(result.stdout) > 4096 or len(result.stderr) > 4096:
            raise self.Refusal('VERIFIER_UNAPPROVED')
        if result.returncode:
            raise self.Refusal('SIGNATURE_INVALID')
        return record

    def _decode_sshsig(self, raw):
        begin, end = (b'-----BEGIN SSH SIGNATURE-----', b'-----END SSH SIGNATURE-----')
        if not raw.startswith(begin + b'\n') or not raw.endswith(end + b'\n'):
            raise self.Refusal('SIGNATURE_INVALID')
        encoded = b''.join(raw[len(begin) + 1:-len(end) - 1].splitlines())
        try:
            data = base64.b64decode(encoded, validate=True)
        except Exception:
            raise self.Refusal('SIGNATURE_INVALID')

        def take_string(offset):
            if offset + 4 > len(data):
                raise self.Refusal('SIGNATURE_INVALID')
            size = int.from_bytes(data[offset:offset + 4], 'big')
            start, stop = (offset + 4, offset + 4 + size)
            if size > len(data) or stop > len(data):
                raise self.Refusal('SIGNATURE_INVALID')
            return (data[start:stop], stop)
        pos = 6
        if data[:pos] != b'SSHSIG' or pos + 4 > len(data) or int.from_bytes(data[pos:pos + 4], 'big') != 1:
            raise self.Refusal('VERIFIER_UNAPPROVED')
        pos += 4
        key_wire, pos = take_string(pos)
        namespace, pos = take_string(pos)
        reserved, pos = take_string(pos)
        hash_alg, pos = take_string(pos)
        signature, pos = take_string(pos)
        if pos != len(data) or reserved or hash_alg not in (b'sha256', b'sha512') or (not signature):
            raise self.Refusal('VERIFIER_UNAPPROVED')
        try:
            alg_len = int.from_bytes(key_wire[:4], 'big')
            alg = key_wire[4:4 + alg_len]
            key_len = int.from_bytes(key_wire[4 + alg_len:8 + alg_len], 'big')
            key_value = key_wire[8 + alg_len:8 + alg_len + key_len]
            if 8 + alg_len + key_len != len(key_wire) or alg != b'ssh-ed25519' or len(key_value) != 32:
                raise self.Refusal('VERIFIER_UNAPPROVED')
        except (IndexError, ValueError):
            raise self.Refusal('VERIFIER_UNAPPROVED')
        try:
            namespace.decode('ascii')
        except UnicodeError:
            raise self.Refusal('SIGNATURE_INVALID')
        return (key_wire, namespace.decode('ascii'))

    def _resolve_manifest_profiles(self, manifest, grant, raw_profiles):
        field_kinds = {'build_image_profile_sha256': 'build-image-profile', 'execution_profile_sha256': 'execution-profile', 'host_std_profile_sha256': 'component-profile', 'musl_std_profile_sha256': 'component-profile', 'crt_profile_sha256': 'component-profile', 'toolchain_profile_sha256': 'component-profile', 'linker_profile_sha256': 'linker-profile', 'rust_provenance_profile_sha256': 'rust-provenance-profile', 'source_inventory_sha256': 'source-inventory'}
        decoded = {}
        for field, kind in field_kinds.items():
            digest = manifest[field]
            raw = raw_profiles.get(digest)
            if raw is None:
                raise self.Refusal('INPUTS_INCOMPLETE')
            decoded[field] = self.parse_profile(raw, kind)
        execution = decoded['execution_profile_sha256']
        source_inventory = decoded['source_inventory_sha256']
        if source_inventory['commit'] != manifest['source_commit'] or source_inventory['tree'] != manifest['source_tree'] or manifest['source_commit'] == manifest['source_base_commit'] or (manifest['source_tree'] == manifest['source_base_tree']):
            raise self.Refusal('SOURCE_MISMATCH')
        candidates = [command for command in execution['commands'] if self.sha256(self.canonical(command)) == grant['command_profile_sha256']]
        if len(candidates) != 1 or candidates[0]['authorization_scope'] != grant['authorization_scope']:
            raise self.Refusal('COMMAND_NOT_APPROVED' if manifest['schema'] == 'p08-generated-input-approval-1' else 'EXECUTION_PROFILE_MISMATCH')
        if not candidates[0]['argv'] or candidates[0]['argv'][0]['value'] != candidates[0]['executable']['path']:
            raise self.Refusal('EXECUTABLE_PATH_MISMATCH')
        image = decoded['build_image_profile_sha256']
        if manifest['sbom_sha256'] != image['sbom_sha256'] or manifest['license_inventory_sha256'] != image['licenses_sha256']:
            raise self.Refusal('PROVENANCE_INVALID')
        for field, role, target in (('toolchain_profile_sha256', 'toolchain', 'x86_64-unknown-linux-gnu'), ('host_std_profile_sha256', 'host-std', 'x86_64-unknown-linux-gnu'), ('musl_std_profile_sha256', 'musl-std', 'x86_64-unknown-linux-musl'), ('crt_profile_sha256', 'crt', 'x86_64-unknown-linux-musl')):
            component = decoded[field]
            if component['role'] != role or component['target'] != target:
                raise self.Refusal('PROVENANCE_INVALID')
            for ref in component['entry_points']:
                if ref['inventory_sha256'] != component['files_inventory_sha256']:
                    raise self.Refusal('EXECUTABLE_INVENTORY_MISMATCH')
        linker = decoded['linker_profile_sha256']
        if linker['entry_point']['inventory_sha256'] != linker['files_inventory_sha256'] or linker['crt_profile_sha256'] != manifest['crt_profile_sha256']:
            raise self.Refusal('PROVENANCE_INVALID')
        for grant_field, manifest_field in (('observed_build_image_profile_sha256', 'build_image_profile_sha256'), ('observed_crt_profile_sha256', 'crt_profile_sha256'), ('observed_execution_profile_sha256', 'execution_profile_sha256'), ('observed_host_std_profile_sha256', 'host_std_profile_sha256'), ('observed_linker_profile_sha256', 'linker_profile_sha256'), ('observed_musl_std_profile_sha256', 'musl_std_profile_sha256'), ('observed_rust_provenance_profile_sha256', 'rust_provenance_profile_sha256'), ('observed_source_inventory_sha256', 'source_inventory_sha256'), ('observed_toolchain_profile_sha256', 'toolchain_profile_sha256')):
            if grant[grant_field] != manifest[manifest_field]:
                raise self.Refusal('ACTION_BINDING_MISMATCH')
        executable_ref = candidates[0]['executable']
        inventory_raw = raw_profiles.get(executable_ref['inventory_sha256'])
        if inventory_raw is None:
            raise self.Refusal('INPUTS_INCOMPLETE')
        inventory = self.parse_profile(inventory_raw, 'input-inventory')
        if self._digest_profile(inventory) != executable_ref['inventory_sha256']:
            raise self.Refusal('EXECUTABLE_INVENTORY_MISMATCH')
        decoded['input_inventory'] = inventory
        return {'command': candidates[0], 'execution_profile': execution, 'profiles': decoded, 'inventory': inventory}

    def _digest_profile(self, value):
        return self.sha256(self.canonical(value))

    def _observation(self, raw, purpose):
        expected = 'review-observation-report' if purpose == 'INPUT_REVIEW_ONLY' else 'action-observation-report'
        other = 'action-observation-report' if purpose == 'INPUT_REVIEW_ONLY' else 'review-observation-report'
        try:
            value = self.parse_profile(raw, expected)
        except self.Refusal as error:
            try:
                self.parse_profile(raw, other)
            except self.Refusal:
                raise error
            raise self.Refusal('OBSERVATION_PURPOSE_MISMATCH')
        if value['purpose'] != purpose:
            raise self.Refusal('OBSERVATION_PURPOSE_MISMATCH')
        return value

    def _require_sidecars(self, value, catalog):
        """Opaque control/report references still require retained exact bytes.

        Fixed historical contract/source/Policy-A identities are checked separately.
        No sidecar supplies code or an alternate trust root.
        """
        historical = {'certificate_sha256', 'manifest_sha256', 'manifest_signature_sha256'}
        if isinstance(value, dict):
            for field, child in value.items():
                if field.endswith('_sha256') and field not in historical:
                    if child not in catalog:
                        raise self.Refusal('INPUTS_INCOMPLETE')
                elif isinstance(child, (dict, list)):
                    self._require_sidecars(child, catalog)
        elif isinstance(value, list):
            for child in value:
                self._require_sidecars(child, catalog)

    def _verify_approval_chain(self, bundle, trusted_context):
        """Verify an exact bundle using independently installed operator inputs.

        `source_facts` supplies actual commit/tree/parent, base commit/tree, full
        base_inventory/observed_entries and inventory_sha256. `evidence_bytes`
        retains opaque reviewed sidecars by their raw SHA-256. Neither dictionary
        authenticates itself. The appointed operator establishes their provenance.

        Generated inputs additionally require producer_bundle, producer_context
        with its authenticated historical clock/status, and producer_facts. Those
        facts name operator_id, outcome, exit_code, completed_at and sealed_at and
        must affirm consumed, complete_audit, no_live_descendants,
        exclusive_fresh_outputs, inspection_authorized, continuous_custody and
        scope_observed. Historical permission is never current launch authority.
        """
        needed = {'profile', 'profiles', 'status', 'bundle_root', 'allowed_signers_root', 'accepted_profile_sha256'}
        if not isinstance(trusted_context, dict) or not needed.issubset(trusted_context):
            raise self.Refusal('STATUS_INVALID')
        if not isinstance(bundle, dict):
            raise self.Refusal('FORMAT_INVALID')
        status = trusted_context['status']
        status_fields = {'now_min', 'now_max', 'trust_epoch', 'clock_session_id', 'monotonic_ns', 'operator_id', 'enrollment_sha256', 'current_decisions_sha256', 'revocations_sha256', 'clock_evidence_sha256', 'register_observation_sha256', 'policy_a_evidence_sha256', 'revoked_ids'}
        if not isinstance(status, dict) or not status_fields.issubset(status):
            raise self.Refusal('STATUS_INVALID')
        now_min, now_max = (status['now_min'], status['now_max'])
        if not isinstance(now_min, int) or isinstance(now_min, bool) or (not isinstance(now_max, int)) or isinstance(now_max, bool) or (now_min < 0) or (now_max < now_min) or (now_max >= 2 ** 64) or (now_max - now_min > 30):
            raise self.Refusal('APPROVAL_STALE')
        if type(status['trust_epoch']) is not int or not 0 < status['trust_epoch'] < 2 ** 64 or type(status['monotonic_ns']) is not int or (not 0 <= status['monotonic_ns'] < 2 ** 64) or (not isinstance(status['clock_session_id'], str)) or (not re.fullmatch('[0-9a-f]{32}', status['clock_session_id'])) or (status['clock_session_id'] == '0' * 32) or (not isinstance(status['operator_id'], str)):
            raise self.Refusal('STATUS_INVALID')
        for field in ('enrollment_sha256', 'current_decisions_sha256', 'revocations_sha256', 'clock_evidence_sha256', 'register_observation_sha256', 'policy_a_evidence_sha256'):
            if not isinstance(status[field], str) or not HEX64.fullmatch(status[field]):
                raise self.Refusal('STATUS_INVALID')
        if not isinstance(status['revoked_ids'], list) or any((not isinstance(x, str) for x in status['revoked_ids'])):
            raise self.Refusal('STATUS_INVALID')
        roles = self.validate_enrollment(trusted_context['profile'], now_min)
        for role_key in roles.values():
            if now_min < role_key['not_before'] or now_max >= role_key['expires_at']:
                raise self.Refusal('APPROVAL_STALE')
        if any((name not in self.SCHEMAS and name not in ('review-observation.json', 'action-observation.json', 'status-report.json', 'source-inventory.json') and (not name.endswith('.profile.json')) for name in bundle)):
            raise self.Refusal('FORMAT_INVALID')
        records = {name: self.parse_record(raw, name) for name, raw in bundle.items() if name in self.SCHEMAS}
        manifests = [n for n in ('build-input-approval.json', 'generated-input-approval.json') if n in records]
        grants = [n for n in ('native-execution-grant.json', 'generated-native-execution-grant.json') if n in records]
        if len(manifests) != 1 or len(grants) != 1 or (not {'source-stage-acceptance.json', 'input-review.json', 'owner-input-decision.json'}.issubset(records)):
            raise self.Refusal('APPROVAL_MISSING')
        mname, gname = (manifests[0], grants[0])
        if mname.startswith('generated-') != gname.startswith('generated-') or (mname == 'generated-input-approval.json') != (gname == 'generated-native-execution-grant.json'):
            raise self.Refusal('EXECUTION_NOT_GRANTED')
        names = {'source-stage-acceptance.json', mname, 'input-review.json', 'owner-input-decision.json', gname}
        if mname == 'generated-input-approval.json':
            if 'compilation-result.json' not in bundle:
                raise self.Refusal('COMPILATION_RECEIPT_MISSING')
            names.add('compilation-result.json')
        if not names.issubset(bundle):
            raise self.Refusal('APPROVAL_MISSING')
        source, manifest, review, owner, grant = (records[x] for x in ('source-stage-acceptance.json', mname, 'input-review.json', 'owner-input-decision.json', gname))
        hashes = {name: self.sha256(bundle[name]) for name in names}
        profile = trusted_context['profile']
        trust_hash = self.sha256(self.canonical(profile))
        if trusted_context['accepted_profile_sha256'] != trust_hash or any((r.get('trust_profile_sha256') != trust_hash for r in (manifest, review, owner, grant, source))):
            raise self.Refusal('STATUS_INVALID')
        try:
            signer_owner = self._read_regular(Path(trusted_context['allowed_signers_root']) / 'owner', 4096, 'VERIFIER_UNAPPROVED')
            signer_reviewer = self._read_regular(Path(trusted_context['allowed_signers_root']) / 'reviewer', 4096, 'VERIFIER_UNAPPROVED')
        except OSError:
            raise self.Refusal('VERIFIER_UNAPPROVED')

        def exact_signer_line(role):
            key = roles[role]
            algorithm, encoded = key['public_key'].split(' ')
            namespaces = ','.join(sorted(key['namespaces']))
            return f'''{key['principal']} namespaces="{namespaces}" {algorithm} {encoded}\n'''.encode('ascii')
        if signer_owner != exact_signer_line('project-owner-issuer') or signer_reviewer != exact_signer_line('independent-reviewer') or self.sha256(signer_owner + signer_reviewer) != profile['allowed_signers_sha256']:
            raise self.Refusal('VERIFIER_UNAPPROVED')
        verifier_inventory_raw = trusted_context['profiles'].get(profile['verifier_inventory_sha256'])
        if verifier_inventory_raw is None:
            raise self.Refusal('VERIFIER_UNAPPROVED')
        verifier_inventory = self.parse_profile(verifier_inventory_raw, 'input-inventory')
        if profile['verifier_artifact']['path'] != '/usr/bin/ssh-keygen' or profile['verifier_artifact']['inventory_sha256'] != profile['verifier_inventory_sha256']:
            raise self.Refusal('VERIFIER_UNAPPROVED')
        self.verify_installed_artifact(profile['verifier_artifact'], verifier_inventory, trusted_context.get('sealed_roots', ()), actual_path='/usr/bin/ssh-keygen', actual_argv0='/usr/bin/ssh-keygen')
        if source['issuer_id'] != roles['project-owner-issuer']['principal']:
            raise self.Refusal('ROLE_MISMATCH')
        if manifest['issuer_id'] != source['issuer_id'] or manifest['reviewer_id'] != roles['independent-reviewer']['principal']:
            raise self.Refusal('ROLE_MISMATCH')
        if (review['reviewer_id'] != manifest['reviewer_id'] or owner['issuer_id'] != manifest['issuer_id'] or
                grant['issuer_id'] != manifest['issuer_id']):
            raise self.Refusal('ROLE_MISMATCH')
        if source['scope'] != 'SOURCE_PREPARATION_ONLY' or source['decision'] != 'ACCEPT':
            raise self.Refusal('ACCEPTANCE_UNAUTHENTICATED')
        if manifest['source_stage_acceptance_sha256'] != hashes['source-stage-acceptance.json'] or review['source_stage_acceptance_sha256'] != hashes['source-stage-acceptance.json'] or owner['source_stage_acceptance_sha256'] != hashes['source-stage-acceptance.json']:
            raise self.Refusal('CHAIN_MISMATCH')
        if review['manifest_sha256'] != hashes[mname] or owner['manifest_sha256'] != hashes[mname] or grant['manifest_sha256'] != hashes[mname]:
            raise self.Refusal('CHAIN_MISMATCH')
        if owner['review_report_sha256'] != hashes['input-review.json'] or grant['review_report_sha256'] != hashes['input-review.json']:
            raise self.Refusal('CHAIN_MISMATCH')
        signature_hashes = {}
        for filename in ('source-stage-acceptance.json', 'input-review.json', 'owner-input-decision.json', gname):
            sigpath = (Path(trusted_context['bundle_root']) / filename).with_suffix('.sshsig')
            try:
                sigraw = self._read_regular(sigpath, 4096, 'ACCEPTANCE_UNAUTHENTICATED' if filename == 'source-stage-acceptance.json' else 'APPROVAL_MISSING')
            except OSError:
                raise self.Refusal('ACCEPTANCE_UNAUTHENTICATED' if filename == 'source-stage-acceptance.json' else 'APPROVAL_MISSING')
            if not sigraw or len(sigraw) > 4096:
                raise self.Refusal('SIGNATURE_INVALID')
            signature_hashes[filename] = self.sha256(sigraw)
        if owner['review_signature_sha256'] != signature_hashes['input-review.json']:
            raise self.Refusal('CHAIN_MISMATCH')
        if grant['owner_signature_sha256'] != signature_hashes['owner-input-decision.json'] or grant['review_signature_sha256'] != signature_hashes['input-review.json']:
            raise self.Refusal('CHAIN_MISMATCH')
        if grant['owner_decision_sha256'] != hashes['owner-input-decision.json']:
            raise self.Refusal('CHAIN_MISMATCH')
        if manifest['source_commit'] != grant['source_commit'] or manifest['source_tree'] != grant['source_tree']:
            raise self.Refusal('SOURCE_MISMATCH')
        if source['source_commit'] != manifest['source_base_commit'] or source['source_tree'] != manifest['source_base_tree'] or source['source_parent'] != BASE_COMMIT:
            raise self.Refusal('SOURCE_MISMATCH')
        source_facts = trusted_context.get('source_facts')
        if not isinstance(source_facts, dict) or source_facts.get('commit') != manifest['source_commit'] or source_facts.get('tree') != manifest['source_tree'] or (source_facts.get('parent') != source['source_commit']) or (source_facts.get('inventory_sha256') != manifest['source_inventory_sha256']) or (source_facts.get('base_commit') != source['source_commit']):
            raise self.Refusal('SOURCE_MISMATCH')
        if grant['trust_epoch'] != status['trust_epoch'] or grant['run_id'] != status.get('run_id', grant['run_id']):
            raise self.Refusal('STATUS_INVALID')
        allowed_actions = ('BUILD_ONLY', 'INDEPENDENT_REBUILD') if mname == 'build-input-approval.json' else ('BUILD_IDENTITY_TEST_EXECUTION', 'CODEC_TEST_EXECUTION')
        if grant['authorization_scope'] not in allowed_actions:
            raise self.Refusal('EXECUTION_NOT_GRANTED')
        for name in names:
            raw = bundle[name]
            disk = Path(trusted_context['bundle_root']) / name
            try:
                if self._read_regular(disk, self._record_limit(name), 'CHAIN_MISMATCH') != raw:
                    raise self.Refusal('CHAIN_MISMATCH')
            except OSError:
                raise self.Refusal('CHAIN_MISMATCH')
            if name not in (mname, 'compilation-result.json'):
                self.verify_signature(name, raw, disk.with_suffix('.sshsig'), profile, now_min, trusted_context['allowed_signers_root'])
        authenticated_grant = {'grant_id': grant['grant_id'], 'run_id': grant['run_id'], 'nonce': grant['nonce'], 'authorization_scope': grant['authorization_scope'], 'trust_epoch': grant['trust_epoch']}
        try:
            for record in (manifest, review, owner, grant):
                if now_min < record['issued_at'] or now_max >= record['expires_at']:
                    raise self.Refusal('APPROVAL_STALE')
                if 'not_before' in record:
                    if not record['issued_at'] <= record['not_before'] < record['expires_at'] or now_min < record['not_before']:
                        raise self.Refusal('APPROVAL_STALE')
            if manifest['expires_at'] - manifest['issued_at'] > profile['approval_max_age_s'] or review['expires_at'] - review['issued_at'] > profile['approval_max_age_s'] or owner['expires_at'] - owner['issued_at'] > profile['approval_max_age_s']:
                raise self.Refusal('APPROVAL_STALE')
            if grant['expires_at'] - grant['issued_at'] > profile['lease_max_s'] or not 0 < grant['max_duration_s'] <= profile['lease_max_s']:
                raise self.Refusal('APPROVAL_STALE')
            ceiling = min(manifest['expires_at'], review['expires_at'], owner['expires_at'], *(key['expires_at'] for key in roles.values()))
            floor = max(manifest['not_before'], review['issued_at'], owner['not_before'], *(key['not_before'] for key in roles.values()))
            if grant['not_before'] < floor or grant['expires_at'] > ceiling or grant['not_before'] + grant['max_duration_s'] > grant['expires_at']:
                raise self.Refusal('APPROVAL_STALE')
            for record, role in ((source, 'project-owner-issuer'), (manifest, 'project-owner-issuer'), (review, 'independent-reviewer'), (owner, 'project-owner-issuer'), (grant, 'project-owner-issuer')):
                key = roles[role]
                if record['issued_at'] < key['not_before'] or record['issued_at'] >= key['expires_at']:
                    raise self.Refusal('APPROVAL_STALE')
            if not (source['issued_at'] <= manifest['issued_at'] and source['issued_at'] <= review['issued_at'] and (source['issued_at'] <= owner['issued_at'])):
                raise self.Refusal('CHAIN_MISMATCH')
            raw_profiles = trusted_context['profiles']
            if not isinstance(raw_profiles, dict):
                raise self.Refusal('CHAIN_MISMATCH')
            for digest, raw in raw_profiles.items():
                if not isinstance(raw, bytes) or self.sha256(raw) != digest:
                    raise self.Refusal('CHAIN_MISMATCH')
            resolved = self._resolve_manifest_profiles(manifest, grant, raw_profiles)
            evidence = trusted_context.get('evidence_bytes', {})
            if not isinstance(evidence, dict) or any((not isinstance(raw, bytes) or self.sha256(raw) != digest for digest, raw in evidence.items())):
                raise self.Refusal('INPUTS_INCOMPLETE')
            catalog = dict(raw_profiles, **evidence)
            catalog[self.sha256(signer_owner + signer_reviewer)] = signer_owner + signer_reviewer
            catalog[trust_hash] = self.canonical(profile)
            for raw in raw_profiles.values():
                try:
                    candidate = json.loads(raw)
                except (ValueError, UnicodeError):
                    continue
                if isinstance(candidate, dict) and candidate.get('schema') == 'p08-input-inventory-1':
                    for entry in candidate.get('entries', []):
                        catalog[self.sha256(self.canonical(entry))] = self.canonical(entry)
            if any((digest not in catalog for digest in (source['review_archive_sha256'], source['independent_review_sha256'], review['findings_sha256']))):
                raise self.Refusal('INPUTS_INCOMPLETE')
            self._require_sidecars(profile, catalog)
            for decoded in resolved['profiles'].values():
                self._require_sidecars(decoded, catalog)
            for component_field in ('host_std_profile_sha256', 'musl_std_profile_sha256', 'crt_profile_sha256', 'toolchain_profile_sha256', 'linker_profile_sha256'):
                component = resolved['profiles'][component_field]
                component_inventory = self._closed_profile(raw_profiles, component['files_inventory_sha256'], 'input-inventory')
                refs = component.get('entry_points', [component.get('entry_point')])
                for ref in refs:
                    self.verify_installed_artifact(ref, component_inventory, trusted_context.get('sealed_roots', ()))
            if mname == 'generated-input-approval.json':
                self._verify_generated_transition(bundle, trusted_context, records, manifest, grant, hashes, profile, roles, raw_profiles, resolved, status, now_min, now_max)
            base_entries = source_facts.get('base_inventory')
            current_entries = resolved['profiles']['source_inventory_sha256']['entries']
            if not isinstance(base_entries, list) or len(base_entries) != 459 or len(current_entries) != 459 or (source_facts.get('base_tree') != source['source_tree']):
                raise self.Refusal('SOURCE_MISMATCH')
            base_by_path = {entry.get('path'): entry for entry in base_entries if isinstance(entry, dict)}
            current_by_path = {entry.get('path'): entry for entry in current_entries if isinstance(entry, dict)}
            if len(base_by_path) != 459 or len(current_by_path) != 459 or set(base_by_path) != set(current_by_path):
                raise self.Refusal('SOURCE_MISMATCH')
            changed_paths = [path for path in base_by_path if base_by_path[path] != current_by_path[path]]
            identity_path = 'native/gate2/protocol/tests/locked_build_identity.rs'
            if changed_paths != [identity_path] or current_by_path[identity_path].get('sha256') != manifest['identity_test_sha256'] or source_facts.get('observed_entries') != current_entries:
                raise self.Refusal('SOURCE_MISMATCH')
            review_raw = raw_profiles.get(review['review_observation_sha256'])
            if review_raw is None:
                raise self.Refusal('OBSERVATION_UNAUTHENTICATED')
            review_observation = self._observation(review_raw, 'INPUT_REVIEW_ONLY')
            self._require_sidecars(review_observation, dict(catalog, **{hashes[mname]: bundle[mname]}))
            if review_observation['purpose'] != 'INPUT_REVIEW_ONLY' or review_observation['verdict'] != 'MATCH' or review_observation['manifest_sha256'] != hashes[mname] or (review_observation['review_id'] != review['review_id']) or (review_observation['reviewer_id'] != review['reviewer_id']) or (review_observation['source_commit'] != manifest['source_commit']) or (review_observation['source_tree'] != manifest['source_tree']) or (review_observation['trust_profile_sha256'] != trust_hash):
                raise self.Refusal('REVIEW_BINDING_INVALID')
            if not manifest['issued_at'] <= review_observation['observed_at'] <= review['issued_at'] <= owner['issued_at']:
                raise self.Refusal('REVIEW_BINDING_INVALID')
            if review['issued_at'] - review_observation['observed_at'] > profile['approval_max_age_s']:
                raise self.Refusal('REVIEW_OBSERVATION_STALE')
            self._match_observed_profiles(review_observation['profiles'], manifest, raw_profiles=raw_profiles)
            observation_hash = grant['action_observation_sha256']
            obs_raw = raw_profiles.get(observation_hash)
            if obs_raw is None:
                raise self.Refusal('OBSERVATION_UNAUTHENTICATED')
            observation = self._observation(obs_raw, 'ACTION_PREFLIGHT_ONLY')
            observation_catalog = dict(catalog)
            for filename, digest in hashes.items():
                observation_catalog[digest] = bundle[filename]
            observation_catalog[grant['command_profile_sha256']] = self.canonical(resolved['command'])
            observation_catalog[trust_hash] = self.canonical(profile)
            self._require_sidecars(observation, observation_catalog)
            if observation['purpose'] != 'ACTION_PREFLIGHT_ONLY' or observation['verdict'] != 'MATCH':
                raise self.Refusal('OBSERVATION_PURPOSE_MISMATCH')
            if observation['grant_id'] != grant['grant_id'] or observation['run_id'] != grant['run_id'] or observation['nonce'] != grant['nonce'] or (observation['manifest_sha256'] != hashes[mname]) or (observation['owner_decision_sha256'] != hashes['owner-input-decision.json']) or (observation['review_report_sha256'] != hashes['input-review.json']) or (observation['command_profile_sha256'] != grant['command_profile_sha256']) or (observation['authorization_scope'] != grant['authorization_scope']) or (observation['source_commit'] != manifest['source_commit']) or (observation['source_tree'] != manifest['source_tree']) or (observation['trust_profile_sha256'] != trust_hash) or (observation['clock_session_id'] != status['clock_session_id']) or (observation['observed_at'] > grant['issued_at']) or (observation['observed_at'] < observation['observation_started_at']) or (observation['observation_started_at'] < max(manifest['issued_at'], review['issued_at'], owner['issued_at'])):
                raise self.Refusal('ACTION_BINDING_MISMATCH')
            self._match_observed_profiles(observation['profiles'], manifest, grant, raw_profiles)
            if status['monotonic_ns'] < observation['completed_monotonic_ns'] or status['monotonic_ns'] - observation['completed_monotonic_ns'] > profile['action_observation_max_age_s'] * 1000000000 or now_max - observation['observed_at'] > profile['action_observation_max_age_s']:
                raise self.Refusal('ACTION_OBSERVATION_STALE')
            status_raw = raw_profiles.get(grant['status_report_sha256'])
            if status_raw is None:
                raise self.Refusal('STATUS_INVALID')
            status_report = self.parse_profile(status_raw, 'status-report')
            if status_report['verdict'] != 'ACTIVE' or status_report['trust_epoch'] != status['trust_epoch'] or status_report['run_id'] != grant['run_id'] or (status_report['enrollment_sha256'] != status['enrollment_sha256']) or (status_report['operator_id'] != status['operator_id']) or (not now_min <= status_report['observed_at'] <= now_max) or any((status_report[key] != status[key] for key in ('current_decisions_sha256', 'revocations_sha256', 'clock_evidence_sha256', 'register_observation_sha256', 'policy_a_evidence_sha256'))):
                raise self.Refusal('STATUS_INVALID')
            result_records = {'source-stage-acceptance.json': source, mname: manifest, 'input-review.json': review, 'owner-input-decision.json': owner, gname: grant}
            active_ids = {record.get(key) for record in result_records.values() for key in ('approval_id', 'decision_id', 'review_id', 'grant_id', 'run_id', 'nonce') if record.get(key)}
            if active_ids.intersection(status['revoked_ids']):
                raise self.Refusal('STATUS_INVALID')
            return {'records': result_records, 'roles': roles, 'profile_sha256': trust_hash, 'command': resolved['command'], 'execution_profile': resolved['execution_profile'], 'inventory': resolved['inventory'], 'profiles': resolved['profiles'], 'action_observation': observation, 'manifest': manifest, 'grant': grant}
        except self.Refusal as error:
            error.authenticated_grant = authenticated_grant
            raise

    def _closed_profile(self, raw_profiles, digest, kind):
        raw = raw_profiles.get(digest)
        if raw is None:
            raise self.Refusal('INPUTS_INCOMPLETE')
        value = self.parse_profile(raw, kind)
        if self.sha256(raw) != digest:
            raise self.Refusal('CHAIN_MISMATCH')
        return value

    def _verify_generated_transition(self, bundle, context, records, manifest, grant, hashes, profile, roles, raw_profiles, resolved, status, now_min, now_max):
        """Authenticate historical build provenance before accepting generated inputs.

        The caller supplies the producer bundle and its independently authenticated
        historical context. That context describes the producer's completion-time
        validity window. Current revocations still come from the current status.
        """
        producer_bundle = context.get('producer_bundle')
        producer_context = context.get('producer_context')
        producer_facts = context.get('producer_facts')
        if not isinstance(producer_bundle, dict) or not isinstance(producer_context, dict) or (not isinstance(producer_facts, dict)):
            raise self.Refusal('BUILD_PROVENANCE_MISMATCH')
        if 'generated-input-approval.json' in producer_bundle:
            raise self.Refusal('PROVENANCE_CYCLE_INVALID')
        producer = self.verify_bundle(producer_bundle, producer_context)
        pm = producer['manifest']
        pg = producer['grant']
        po = producer['records']['owner-input-decision.json']
        pr = producer['records']['input-review.json']
        if pm.get('schema') != 'p08-build-input-approval-3' or pg.get('schema') != 'p08-native-execution-grant-3':
            raise self.Refusal('PROVENANCE_INVALID')
        if pg['authorization_scope'] not in ('BUILD_ONLY', 'INDEPENDENT_REBUILD'):
            raise self.Refusal('PROVENANCE_INVALID')
        producer_ids = {pg[k] for k in ('grant_id', 'run_id', 'nonce')}
        producer_ids.update((pm['approval_id'], pr['review_id'], po['decision_id']))
        if producer_ids.intersection(status['revoked_ids']):
            raise self.Refusal('STATUS_INVALID')
        b = records['compilation-result.json']
        braw = bundle['compilation-result.json']
        bsignature = Path(context['bundle_root']) / 'compilation-result.sshsig'
        try:
            bsig_raw = self._read_regular(bsignature, 4096, 'COMPILATION_RECEIPT_MISSING')
        except OSError:
            raise self.Refusal('COMPILATION_RECEIPT_MISSING')
        if self.sha256(bsig_raw) != manifest['compilation_result_signature_sha256']:
            raise self.Refusal('COMPILATION_RECEIPT_UNAUTHENTICATED')
        if self.sha256(braw) != manifest['compilation_result_sha256']:
            raise self.Refusal('COMPILATION_RECEIPT_MISSING')
        try:
            producer_grant_signature = self._read_regular(Path(producer_context['bundle_root']) / 'native-execution-grant.sshsig', 4096, 'BUILD_PROVENANCE_MISMATCH')
        except (KeyError, OSError):
            raise self.Refusal('BUILD_PROVENANCE_MISMATCH')
        b_ids = {'producer_manifest_sha256': self.sha256(producer_bundle['build-input-approval.json']), 'producer_review_sha256': self.sha256(producer_bundle['input-review.json']), 'producer_owner_decision_sha256': self.sha256(producer_bundle['owner-input-decision.json']), 'producer_grant_sha256': self.sha256(producer_bundle['native-execution-grant.json']), 'producer_grant_signature_sha256': self.sha256(producer_grant_signature), 'producer_grant_id': pg['grant_id'], 'producer_run_id': pg['run_id'], 'producer_nonce': pg['nonce'], 'producer_command_profile_sha256': pg['command_profile_sha256'], 'source_commit': pm['source_commit'], 'source_tree': pm['source_tree'], 'trust_profile_sha256': producer['profile_sha256'], 'reviewer_id': pm['reviewer_id']}
        if any((b.get(field) != value for field, value in b_ids.items())):
            raise self.Refusal('BUILD_PROVENANCE_MISMATCH')
        if b['operator_id'] != producer_facts.get('operator_id') or b['reviewer_id'] != roles['independent-reviewer']['principal'] or b['reviewer_id'] != pm['reviewer_id'] or (producer_facts.get('outcome') != 'SUCCESS_ELIGIBLE_OUTPUTS') or (producer_facts.get('exit_code') != 0) or (not b['started_at'] <= b['completed_at'] <= b['issued_at']) or (b['completed_at'] != producer_facts.get('completed_at')) or (b['issued_at'] < producer_facts.get('sealed_at')) or (b['generated_inputs_profile_sha256'] != manifest['generated_inputs_profile_sha256']) or (b['source_commit'] != manifest['source_commit']) or (b['source_tree'] != manifest['source_tree']) or (manifest['issued_at'] < b['issued_at']) or (b['issued_at'] > now_max) or (not pg['not_before'] <= b['started_at'] <= b['completed_at'] < pg['expires_at']) or (b['completed_at'] - b['started_at'] > pg['max_duration_s']):
            raise self.Refusal('PRODUCER_NOT_ELIGIBLE')
        if producer_facts.get('continuous_custody') is not True:
            raise self.Refusal('GENERATED_CUSTODY_INVALID')
        if any((producer_facts.get(field) is not True for field in ('consumed', 'complete_audit', 'no_live_descendants', 'exclusive_fresh_outputs', 'inspection_authorized', 'scope_observed'))):
            raise self.Refusal('PRODUCER_NOT_ELIGIBLE')
        try:
            self.verify_signature('compilation-result.json', braw, bsignature, profile, now_min, context['allowed_signers_root'])
        except self.Refusal as error:
            raise self.Refusal('COMPILATION_RECEIPT_UNAUTHENTICATED') from error
        qhash = manifest['generated_inputs_profile_sha256']
        if b['generated_inputs_profile_sha256'] != qhash:
            raise self.Refusal('BUILD_PROVENANCE_MISMATCH')
        q = self._closed_profile(raw_profiles, qhash, 'generated-inputs-profile')
        ehash = q['compilation_evidence_sha256']
        evidence = self._closed_profile(raw_profiles, ehash, 'compilation-evidence-report')
        ihash = q['files_inventory_sha256']
        inventory = self._closed_profile(raw_profiles, ihash, 'input-inventory')
        custody = self._closed_profile(raw_profiles, q['custody_evidence_sha256'], 'generated-custody-report')
        generated_catalog = {**raw_profiles, **context.get('evidence_bytes', {})}
        for filename, raw in producer_bundle.items():
            generated_catalog[self.sha256(raw)] = raw
            if filename != 'build-input-approval.json':
                sigraw = self._read_regular((Path(producer_context['bundle_root']) / filename).with_suffix('.sshsig'), 4096, 'BUILD_PROVENANCE_MISMATCH')
                generated_catalog[self.sha256(sigraw)] = sigraw
        generated_catalog[pg['command_profile_sha256']] = self.canonical(producer['command'])
        for entry in inventory['entries']:
            generated_catalog[self.sha256(self.canonical(entry))] = self.canonical(entry)
        for value in (q, evidence, custody):
            self._require_sidecars(value, generated_catalog)
        producer_refs = {'producer_manifest_sha256': self.sha256(producer_bundle['build-input-approval.json']), 'producer_grant_sha256': self.sha256(producer_bundle['native-execution-grant.json']), 'compilation_evidence_sha256': ehash, 'files_inventory_sha256': ihash, 'custody_evidence_sha256': self.sha256(raw_profiles[q['custody_evidence_sha256']]), 'source_commit': pm['source_commit'], 'source_tree': pm['source_tree']}
        if any((q.get(k) != v for k, v in producer_refs.items())):
            raise self.Refusal('BUILD_PROVENANCE_MISMATCH')
        if custody['verdict'] != 'SEALED_READ_ONLY' or custody['producer_grant_sha256'] != producer_refs['producer_grant_sha256'] or custody['operator_id'] != producer_facts.get('operator_id') or (custody['sealed_at'] > b['issued_at']) or (custody['sealed_at'] < b['completed_at']) or (custody['inventory_sha256'] != ihash) or (evidence['output_inventory_sha256'] != ihash) or (evidence['custody_evidence_sha256'] != q['custody_evidence_sha256']) or (evidence['started_at'] != b['started_at']) or (evidence['exit_code'] != 0) or (evidence['completed_at'] != b['completed_at']) or (b['compilation_evidence_sha256'] != ehash) or any((evidence.get(k) != b.get(k) for k in ('producer_manifest_sha256', 'producer_review_sha256', 'producer_owner_decision_sha256', 'producer_grant_signature_sha256', 'producer_grant_sha256', 'producer_grant_id', 'producer_run_id', 'producer_nonce', 'producer_command_profile_sha256', 'source_commit', 'source_tree'))):
            raise self.Refusal('GENERATED_CUSTODY_INVALID')
        if not q['executables'] or [x['id'] for x in q['executables']] != sorted({x['id'] for x in q['executables']}):
            raise self.Refusal('GENERATED_TARGET_UNSUPPORTED')
        generated_refs = {self.canonical(x) for x in q['executables']}
        command_refs = {self.canonical(command['executable']) for command in resolved['execution_profile']['commands'] if command['authorization_scope'] in ('BUILD_IDENTITY_TEST_EXECUTION', 'CODEC_TEST_EXECUTION')}
        if self.canonical(resolved['command']['executable']) not in generated_refs or self.canonical(resolved['command']['executable']) not in command_refs:
            raise self.Refusal('COMMAND_NOT_APPROVED')
        if resolved['command']['authorization_scope'] not in ('BUILD_IDENTITY_TEST_EXECUTION', 'CODEC_TEST_EXECUTION'):
            raise self.Refusal('COMMAND_NOT_APPROVED')
        if any((x['id'] not in ('codec_test', 'locked_build_identity') for x in q['executables'])):
            raise self.Refusal('GENERATED_TARGET_UNSUPPORTED')
        if any((x['provenance_sha256'] != ehash for x in q['executables'])):
            for ref in q['executables']:
                if ref['provenance_sha256'] != ehash:
                    try:
                        self._closed_profile(raw_profiles, ref['provenance_sha256'], 'compilation-evidence-report')
                    except self.Refusal:
                        raise self.Refusal('PROVENANCE_CYCLE_INVALID')
            raise self.Refusal('BUILD_PROVENANCE_MISMATCH')
        if any((x['inventory_sha256'] != ihash for x in q['executables'])):
            raise self.Refusal('GENERATED_INPUT_MISMATCH')
        if not set((x['path'] for x in q['executables'])).issubset({x['path'] for x in inventory['entries']}):
            raise self.Refusal('EXECUTABLE_INVENTORY_MISMATCH')
        expected_scope = {'locked_build_identity': 'BUILD_IDENTITY_TEST_EXECUTION', 'codec_test': 'CODEC_TEST_EXECUTION'}
        if expected_scope[resolved['command']['executable']['id']] != grant['authorization_scope']:
            raise self.Refusal('COMMAND_NOT_APPROVED')
        if grant['observed_generated_inputs_profile_sha256'] != qhash:
            raise self.Refusal('ACTION_BINDING_MISMATCH')
        for ref in q['executables']:
            try:
                self.verify_installed_artifact(ref, inventory, context.get('sealed_roots', ()))
            except self.Refusal as error:
                raise self.Refusal('GENERATED_INPUT_MISMATCH') from error
        producer_manifest = pm
        for field in ('source_commit', 'source_tree', 'trust_profile_sha256', 'build_image_profile_sha256', 'host_std_profile_sha256', 'musl_std_profile_sha256', 'crt_profile_sha256', 'toolchain_profile_sha256', 'linker_profile_sha256', 'rust_provenance_profile_sha256', 'source_inventory_sha256'):
            if manifest.get(field) != producer_manifest.get(field):
                raise self.Refusal('BUILD_PROVENANCE_MISMATCH')
        if manifest['reviewer_id'] != roles['independent-reviewer']['principal']:
            raise self.Refusal('ROLE_MISMATCH')
        new_ids = {manifest['approval_id'], records['input-review.json']['review_id'], records['owner-input-decision.json']['decision_id'], grant['grant_id'], grant['run_id'], grant['nonce']}
        if len(new_ids) != 6 or new_ids.intersection(producer_ids):
            raise self.Refusal('CHAIN_MISMATCH')

    def _match_observed_profiles(self, observed, manifest, grant=None, raw_profiles=None):
        if not isinstance(observed, list):
            raise self.Refusal('OBSERVATION_UNAUTHENTICATED')
        required = {key.removesuffix('_sha256'): value for key, value in manifest.items() if key.endswith('_profile_sha256') and key != 'trust_profile_sha256' or key == 'source_inventory_sha256'}
        if grant and grant.get('observed_generated_inputs_profile_sha256'):
            required['generated_inputs_profile'] = grant['observed_generated_inputs_profile_sha256']
        actual = {item.get('id'): item.get('sha256') for item in observed if isinstance(item, dict)}
        if len(actual) != len(observed) or actual != required:
            raise self.Refusal('OBSERVATION_UNAUTHENTICATED')
        if raw_profiles is not None and any((item['bytes'] != len(raw_profiles.get(item['sha256'], b'')) for item in observed)):
            raise self.Refusal('OBSERVATION_UNAUTHENTICATED')

    def verify_installed_artifact(self, ref, inventory, sealed_roots, actual_path=None, actual_argv0=None):
        if not isinstance(ref, dict) or not isinstance(inventory, dict) or inventory.get('schema') != 'p08-input-inventory-1':
            raise self.Refusal('FORMAT_INVALID')
        self._check_entry(ref, 'installed_artifact')
        self._validate_profile(inventory, self.PROFILE_RULES['profiles']['input-inventory'], 'input-inventory')
        path = ref.get('path')
        if not isinstance(path, str) or not path.startswith('/') or path.startswith('//') or (os.path.normpath(path) != path):
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        if actual_path is not None and actual_path != path or (actual_argv0 is not None and actual_argv0 != path):
            raise self.Refusal('EXECUTABLE_PATH_MISMATCH')
        entries = inventory.get('entries')
        if not isinstance(entries, list):
            raise self.Refusal('FORMAT_INVALID')
        if ref.get('inventory_sha256') != self.sha256(self.canonical(inventory)):
            raise self.Refusal('EXECUTABLE_INVENTORY_MISMATCH')
        path_entries = [x for x in entries if isinstance(x, dict) and x.get('path') == path]
        if len(path_entries) != 1:
            raise self.Refusal('EXECUTABLE_INVENTORY_MISMATCH')
        entry = path_entries[0]
        if ref.get('path_entry_sha256') != self.sha256(self.canonical(entry)):
            raise self.Refusal('EXECUTABLE_INVENTORY_MISMATCH')
        real = Path(path)
        roots = [Path(sealed_roots)] if isinstance(sealed_roots, (str, os.PathLike)) else [Path(root) for root in sealed_roots]
        try:
            if not real.is_absolute() or not any((os.path.commonpath((str(real), str(root))) == str(root) for root in roots)):
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        except ValueError:
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        current = real.parent
        while current != current.parent:
            try:
                st_parent = current.lstat()
            except OSError:
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
            if not __import__('stat').S_ISDIR(st_parent.st_mode):
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
            current = current.parent
        chain = ref.get('symlink_chain')
        if not isinstance(chain, list) or len(chain) > 32 or len(chain) != len(set(chain)):
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        expected_chain = []
        target = real
        for _ in range(33):
            for parent in target.parents:
                try:
                    if not stat.S_ISDIR(parent.lstat().st_mode):
                        raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
                except OSError:
                    raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
            try:
                st = target.lstat()
            except OSError:
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
            if not __import__('stat').S_ISLNK(st.st_mode):
                break
            matches = [e for e in entries if e.get('path') == str(target)]
            if len(matches) != 1 or matches[0].get('kind') != 'symlink':
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
            if matches[0]['resolved_path'] != ref['resolved_path'] or matches[0]['resolved_sha256'] != ref['sha256']:
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
            expected_chain.append(self.sha256(self.canonical(matches[0])))
            link = os.readlink(target)
            if not link or '\x00' in link or (not link.isascii()) or (len(link.encode('ascii')) > 512):
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
            if matches[0].get('target') != link:
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
            candidate = Path(link) if os.path.isabs(link) else target.parent / link
            target = Path(os.path.normpath(candidate))
            try:
                inside_root = any((os.path.commonpath((str(target), str(root))) == str(root) for root in roots))
            except ValueError:
                inside_root = False
            if not inside_root:
                raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        else:
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        if chain != expected_chain:
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        endpoints = [e for e in entries if e.get('path') == str(target)]
        if len(endpoints) != 1:
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        endpoint = endpoints[0]
        if target != Path(ref.get('resolved_path', '')) or endpoint.get('kind') != 'regular' or ref.get('resolved_entry_sha256') != self.sha256(self.canonical(endpoint)) or (endpoint.get('sha256') != ref.get('sha256')) or (endpoint.get('bytes') != ref.get('bytes')):
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        if not __import__('stat').S_ISREG(st.st_mode):
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        if endpoint.get('mode') != format(stat.S_IMODE(st.st_mode), '04o'):
            raise self.Refusal('EXECUTABLE_INVENTORY_MISMATCH')
        flags = os.O_RDONLY | getattr(os, 'O_NOFOLLOW', 0) | getattr(os, 'O_CLOEXEC', 0)
        try:
            fd = os.open(target, flags)
        except OSError:
            raise self.Refusal('EXECUTABLE_RESOLUTION_INVALID')
        try:
            before = os.fstat(fd)
            if (before.st_dev, before.st_ino, before.st_mode, before.st_size) != (st.st_dev, st.st_ino, st.st_mode, st.st_size):
                raise self.Refusal('CUSTODY_FAILURE')
            digest = hashlib.sha256()
            total = 0
            while True:
                chunk = os.read(fd, 65536)
                if not chunk:
                    break
                total += len(chunk)
                if total > ref.get('bytes', -1):
                    raise self.Refusal('CUSTODY_FAILURE')
                digest.update(chunk)
            after = os.fstat(fd)
            if (before.st_dev, before.st_ino, before.st_mode, before.st_size, before.st_mtime_ns, before.st_ctime_ns) != (after.st_dev, after.st_ino, after.st_mode, after.st_size, after.st_mtime_ns, after.st_ctime_ns):
                raise self.Refusal('CUSTODY_FAILURE')
        finally:
            os.close(fd)
        if digest.hexdigest() != ref.get('sha256') or total != ref.get('bytes'):
            raise self.Refusal('EXECUTABLE_INVENTORY_MISMATCH')
        return entry
    def verify_bundle(self, bundle, trusted_context):
        """Authenticate independent source review before any grant is exposed.

        No real source acceptance or execution is produced by constructing a
        context. Its hashes, live facts and immutable custody must have been
        independently authenticated by the installed operator, as in R2.
        Missing authority refuses; there is no callback or R2 fallback.
        """
        self.authenticate_source_review(bundle, trusted_context)
        return self._verify_approval_chain(bundle, trusted_context)

    def _require(self, condition, reason):
        if not condition:
            raise self.Refusal(reason)

    def authenticate_source_review(self, bundle, context):
        """Return authenticated review metadata, never an execution receipt."""
        self._require(isinstance(bundle, dict) and isinstance(context, dict), 'FORMAT_INVALID')
        profile, status = context.get('profile'), context.get('status')
        self._require(isinstance(profile, dict) and isinstance(status, dict), 'STATUS_INVALID')
        self._require(context.get('accepted_profile_sha256') == self.sha256(self.canonical(profile))
                      and profile.get('record_family') == FAMILY, 'VERIFIER_FAMILY_UNAPPROVED')
        lower, upper = status.get('now_min'), status.get('now_max')
        self._require(type(lower) is int and type(upper) is int and
                      0 <= lower <= upper < 2**64 and upper-lower <= 30, 'STATUS_INVALID')
        roles = self.validate_enrollment(profile, lower)
        self._require(all(lower >= k['not_before'] and upper < k['expires_at'] for k in roles.values()),
                      'APPROVAL_STALE')
        authority = context.get('source_review_authority')
        rules = self.PROFILE_RULES['source_review_rules']
        self._require(isinstance(authority, dict) and set(authority) == set(rules['authority_fields']),
                      'SOURCE_REVIEW_AUTHORITY_MISSING')
        self._require(context.get('accepted_source_review_authority_sha256') ==
                      self.sha256(self.canonical(authority)), 'SOURCE_REVIEW_AUTHORITY_UNAUTHENTICATED')
        self._require(authority.get('schema') == 'p08-source-review-authority-1' and
                      type(authority.get('repository_id')) is int and authority['repository_id'] == 1368436395 and
                      authority.get('trust_profile_sha256') == context['accepted_profile_sha256'] and
                      authority.get('reviewer_fingerprint') == roles['independent-reviewer']['fingerprint'],
                      'SOURCE_REVIEW_AUTHORITY_MISMATCH')
        self._require(type(authority.get('not_before')) is int and type(authority.get('expires_at')) is int and
                      authority['not_before'] <= lower <= upper < authority['expires_at'],
                      'SOURCE_REVIEW_AUTHORITY_STALE')
        self._require(isinstance(status.get('revoked_ids'), list) and
                      all(isinstance(x,str) for x in status['revoked_ids']), 'STATUS_INVALID')
        self._require(not {authority.get('authority_id'), authority.get('reviewer_fingerprint')}.intersection(
                      status['revoked_ids']), 'SOURCE_REVIEW_AUTHORITY_REVOKED')
        for field in ('review_attestation_sha256', 'review_signature_sha256', 'review_archive_sha256'):
            self._require(isinstance(authority.get(field), str) and HEX64.fullmatch(authority[field]) and
                          authority[field] != '0'*64, 'SOURCE_REVIEW_AUTHORITY_MISMATCH')
        self._require(isinstance(authority.get('authority_id'), str) and
                      re.fullmatch('[0-9a-f]{32}', authority['authority_id']) and authority['authority_id'] != '0'*32,
                      'SOURCE_REVIEW_AUTHORITY_MISMATCH')
        name = 'source-review-attestation.json'
        raw = bundle.get(name)
        self._require(isinstance(raw, bytes) and self.sha256(raw) == authority['review_attestation_sha256'],
                      'SOURCE_REVIEW_UNAUTHENTICATED')
        attestation = self.parse_record(raw, name)
        self._require(attestation['reviewer_id'] == roles['independent-reviewer']['principal'] and
                      attestation['trust_profile_sha256'] == context['accepted_profile_sha256'] and
                      authority['not_before'] <= attestation['issued_at'] <= lower <= upper < attestation['expires_at']
                      <= authority['expires_at'] and attestation['expires_at']-attestation['issued_at'] <= profile['approval_max_age_s'],
                      'SOURCE_REVIEW_STALE_OR_MISMATCHED')
        self._require(attestation['review_id'] not in status['revoked_ids'], 'SOURCE_REVIEW_AUTHORITY_REVOKED')
        signer_root = context.get('allowed_signers_root')
        self._require(isinstance(signer_root, (str, os.PathLike)), 'VERIFIER_UNAPPROVED')
        owner_line = self._read_regular(Path(signer_root)/'owner',4096,'VERIFIER_UNAPPROVED')
        reviewer_line = self._read_regular(Path(signer_root)/'reviewer',4096,'VERIFIER_UNAPPROVED')
        lines = []
        for role in ('project-owner-issuer','independent-reviewer'):
            key = roles[role]
            lines.append((key['principal']+' namespaces="'+','.join(sorted(key['namespaces']))+'" '+key['public_key']+'\n').encode('ascii'))
        self._require([owner_line,reviewer_line] == lines and self.sha256(b''.join(lines)) == profile['allowed_signers_sha256'],
                      'VERIFIER_UNAPPROVED')
        inventory_raw = context.get('profiles',{}).get(profile['verifier_inventory_sha256'])
        self._require(isinstance(inventory_raw, bytes) and self.sha256(inventory_raw) == profile['verifier_inventory_sha256'],
                      'VERIFIER_UNAPPROVED')
        self._require(profile['verifier_artifact']['path'] == '/usr/bin/ssh-keygen', 'VERIFIER_UNAPPROVED')
        self.verify_installed_artifact(profile['verifier_artifact'], self.parse_profile(inventory_raw,'input-inventory'),
                                       context.get('sealed_roots',()),actual_path='/usr/bin/ssh-keygen',actual_argv0='/usr/bin/ssh-keygen')
        bundle_root = context.get('bundle_root')
        self._require(isinstance(bundle_root, (str, os.PathLike)), 'SOURCE_REVIEW_UNAUTHENTICATED')
        disk = Path(bundle_root)/name
        self._require(self._read_regular(disk,self._record_limit(name),'SOURCE_REVIEW_UNAUTHENTICATED') == raw,
                      'SOURCE_REVIEW_UNAUTHENTICATED')
        sig = disk.with_suffix('.sshsig')
        self._require(self.sha256(self._read_regular(sig,4096,'SOURCE_REVIEW_UNAUTHENTICATED')) == authority['review_signature_sha256'],
                      'SOURCE_REVIEW_UNAUTHENTICATED')
        self.verify_signature(name,raw,sig,profile,lower,signer_root)
        source = self.parse_record(bundle.get('source-stage-acceptance.json'), 'source-stage-acceptance.json')
        self._require(source['independent_review_sha256'] == self.sha256(raw) and
                      source['source_review_signature_sha256'] == authority['review_signature_sha256'] and
                      source['review_archive_sha256'] == attestation['archive_sha256'] == authority['review_archive_sha256'] and
                      attestation['issued_at'] <= source['issued_at'] <= lower and
                      source['issuer_id'] == roles['project-owner-issuer']['principal'], 'SOURCE_REVIEW_BINDING_MISMATCH')
        evidence = context.get('evidence_bytes')
        self._require(isinstance(evidence, dict), 'SOURCE_REVIEW_ARCHIVE_MISSING')
        archive = evidence.get(attestation['archive_sha256'])
        index_raw = evidence.get(attestation['archive_inventory_sha256'])
        self._require(isinstance(archive, bytes) and 0 < len(archive) <= rules['max_archive_bytes'] and
                      len(archive) == attestation['archive_bytes'] and self.sha256(archive) == attestation['archive_sha256'] and
                      isinstance(index_raw,bytes) and len(index_raw) <= MAX_PROFILE and
                      self.sha256(index_raw) == attestation['archive_inventory_sha256'], 'SOURCE_REVIEW_ARCHIVE_MISMATCH')
        self._verify_review_archive(archive,index_raw)
        self.verify_source_lineage(source,attestation,context.get('source_facts'))
        return attestation

    def _verify_review_archive(self, raw, index_raw):
        """Bounded read-only closure verification. Never extract an archive."""
        try:
            index = json.loads(index_raw.decode('ascii'),object_pairs_hook=self._pairs)
            self._require(self.canonical(index) == index_raw and isinstance(index,list) and
                          0 < len(index) <= self.PROFILE_RULES['source_review_rules']['max_archive_members'],
                          'SOURCE_REVIEW_ARCHIVE_MISMATCH')
            expected = {}
            for row in index:
                self._require(isinstance(row,dict) and set(row) == {'path','kind','mode','bytes','sha256'}, 'SOURCE_REVIEW_ARCHIVE_MISMATCH')
                path=row['path']
                self._require(isinstance(path,str) and not path.startswith('/') and len(path)<=512 and
                              all(x not in ('','.','..') for x in path.split('/')) and path not in expected,
                              'SOURCE_REVIEW_ARCHIVE_MISMATCH')
                expected[path]=row
            self._require(list(expected)==sorted(expected), 'SOURCE_REVIEW_ARCHIVE_MISMATCH')
            seen=set(); expanded=0
            with tarfile.open(fileobj=io.BytesIO(raw),mode='r:*') as archive:
                for member in archive:
                    self._require(member.name in expected and member.name not in seen and
                                  (member.isfile() or member.isdir()) and len(seen)<len(expected), 'SOURCE_REVIEW_ARCHIVE_MISMATCH')
                    row=expected[member.name];seen.add(member.name);expanded+=member.size
                    self._require(0<=member.size and expanded<=self.PROFILE_RULES['source_review_rules']['max_expanded_bytes'],
                                  'SOURCE_REVIEW_ARCHIVE_MISMATCH')
                    content=archive.extractfile(member).read(member.size+1) if member.isfile() else b''
                    self._require(row == {'path':member.name,'kind':'regular' if member.isfile() else 'directory',
                                         'mode':format(member.mode,'04o'),'bytes':member.size,'sha256':self.sha256(content)} and
                                  len(content)==member.size, 'SOURCE_REVIEW_ARCHIVE_MISMATCH')
            self._require(seen == set(expected), 'SOURCE_REVIEW_ARCHIVE_MISMATCH')
        except (ValueError, UnicodeError, OSError, tarfile.TarError, EOFError, RecursionError) as error:
            raise self.Refusal('SOURCE_REVIEW_ARCHIVE_MISMATCH') from error

    def git_object_id(self, kind, raw):
        self._require(isinstance(raw,bytes), 'SOURCE_MISMATCH')
        return hashlib.sha1(kind.encode('ascii')+b' '+str(len(raw)).encode('ascii')+b'\0'+raw).hexdigest()

    def source_tree(self, entries):
        """Recompute Git's recursive tree identity from a closed source inventory."""
        self._require(isinstance(entries,list) and 0<len(entries)<=459, 'SOURCE_MISMATCH')
        tree={}; paths=[]
        for entry in entries:
            self._check_entry(entry,'source_file');paths.append(entry['path']);cursor=tree
            for part in entry['path'].split('/')[:-1]:
                self._require(not isinstance(cursor.get(part),tuple), 'SOURCE_MISMATCH')
                cursor=cursor.setdefault(part,{})
            leaf=entry['path'].split('/')[-1]
            self._require(leaf not in cursor, 'SOURCE_MISMATCH')
            cursor[leaf]=(entry['mode'],entry['git_blob'])
        self._require(paths==sorted(set(paths)), 'SOURCE_MISMATCH')
        def digest(directory):
            raw=b''
            for name,value in sorted(directory.items(),key=lambda item:(item[0]+('/' if isinstance(item[1],dict) else '')).encode('ascii')):
                mode,oid=('40000',digest(value)) if isinstance(value,dict) else value
                raw+=mode.encode('ascii')+b' '+name.encode('ascii')+b'\0'+bytes.fromhex(oid)
            return self.git_object_id('tree',raw)
        return digest(tree)

    def _commit(self, raw, oid, tree, parent):
        self._require(isinstance(raw,bytes) and len(raw)<=65536 and self.git_object_id('commit',raw)==oid,
                      'SOURCE_COMMIT_MISMATCH')
        header=raw.split(b'\n\n',1)[0].splitlines()
        self._require([x for x in header if x.startswith(b'tree ')] == [b'tree '+tree.encode('ascii')] and
                      [x for x in header if x.startswith(b'parent ')] == [b'parent '+parent.encode('ascii')],
                      'SOURCE_ANCESTRY_MISMATCH')

    def verify_source_lineage(self, source, review, facts):
        """Check exact source objects supplied by the independently appointed observer.

        Source facts are not authenticated by this function. The external
        operator must observe actual repository objects, never applicant status.
        Hash-consistent synthetic commits remain synthetic source-test evidence.
        """
        self._require(isinstance(facts,dict), 'SOURCE_MISMATCH')
        self._require(type(facts.get('repository_id')) is int and facts['repository_id']==1368436395,
                      'REPOSITORY_ID_MISMATCH')
        self._require(facts.get('current_main_commit')==BASE_COMMIT and facts.get('current_main_tree')==BASE_TREE,
                      'SOURCE_MOVEMENT_REQUIRES_REVIEW')
        c0,c1,base=facts.get('base_inventory'),facts.get('observed_entries'),facts.get('protected_inventory')
        self._require(isinstance(base,list) and len(base)==445 and self.source_tree(base)==BASE_TREE and
                      isinstance(c0,list) and isinstance(c1,list) and len(c0)==len(c1)==459, 'SOURCE_MISMATCH')
        c0tree,c1tree=self.source_tree(c0),self.source_tree(c1)
        self._require(c0tree==source['source_tree']==review['c0_tree'] and
                      c1tree==C1_TREE==source['c1_tree']==review['c1_tree'] and
                      facts.get('base_tree')==c0tree and facts.get('tree')==c1tree and
                      source['source_parent']==BASE_COMMIT and source['source_commit']==facts.get('base_commit')==review['c0_commit'] and
                      source['c1_commit']==facts.get('commit')==review['c1_commit'] and
                      facts.get('parent')==source['source_commit'], 'SOURCE_MISMATCH')
        self._commit(facts.get('c0_commit_raw'),source['source_commit'],c0tree,BASE_COMMIT)
        self._commit(facts.get('c1_commit_raw'),source['c1_commit'],c1tree,source['source_commit'])
        self._require(source['source_commit'] not in (BASE_COMMIT,PROJECTION_TREE,C1_TREE,source['c1_commit']) and
                      source['c1_commit'] not in (BASE_COMMIT,PROJECTION_TREE,C1_TREE), 'SOURCE_COMMIT_MISMATCH')
        maps=[{x['path']:x for x in entries} for entries in (base,c0,c1)];bm,m0,m1=maps
        pinned={x['path']:x for x in self.contract['reviewed_composition']}
        identity=self.contract['historical_identity'];ip=identity['path']
        self._require(set(m0)==set(m1) and set(m0)-set(bm)==set(pinned) and
                      all(m0[p]==m1[p]==entry for p,entry in bm.items()) and
                      [p for p in m0 if m0[p]!=m1[p]]==[ip] and m0[ip]=={'mode':'100644',**identity} and
                      all(m1[p]==entry for p,entry in pinned.items()), 'SOURCE_MISMATCH')
        blobs=facts.get('source_bytes')
        self._require(isinstance(blobs,dict) and set(blobs)==set(m1) and sum(x['bytes'] for x in c1)<=128*1024*1024,
                      'SOURCE_BYTES_MISMATCH')
        for path,entry in m1.items():
            raw=blobs[path]
            self._require(isinstance(raw,bytes) and len(raw)==entry['bytes'] and self.sha256(raw)==entry['sha256'] and
                          self.git_object_id('blob',raw)==entry['git_blob'], 'SOURCE_BYTES_MISMATCH')
        old=facts.get('base_identity_bytes')
        self._require(isinstance(old,bytes) and len(old)==identity['bytes'] and self.sha256(old)==identity['sha256'] and
                      self.git_object_id('blob',old)==identity['git_blob'], 'SOURCE_BYTES_MISMATCH')
        t03=[x for x in self.contract['reviewed_composition'] if x['path'].endswith(('codec.ex','codec_test.exs','codec.rs','codec_test.rs'))]
        self._require(self.source_tree(sorted(base+t03,key=lambda x:x['path']))==PROJECTION_TREE and
                      review['t03_inventory_sha256']==self.sha256(self.canonical(t03)) and
                      review['c0_inventory_sha256']==self.sha256(self.canonical(c0)) and
                      review['c1_inventory_sha256']==self.sha256(self.canonical(c1)), 'SOURCE_REVIEW_BINDING_MISMATCH')
