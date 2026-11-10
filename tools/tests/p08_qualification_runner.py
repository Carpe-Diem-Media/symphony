"""Offline launcher with a separate owner-issued development profile.

The historical R1a profile still always refuses. The new development profile
requires an independently owner-confirmed public key and signed exact release.
It supplies no production or formal R1b authority.

Adapted from the retained T03 seccomp-notification launcher. All subprocess
paths, argv forms and fixture effects are finite. The parent records every
exec decision. A denied exec makes the entire run fail. No library is built.
"""

import array
import ctypes
import errno
import hashlib
import json
import os
from pathlib import Path
import select
import signal
import socket
import sys
import time
import re
from dataclasses import dataclass
from enum import Enum
from typing import NoReturn

# R1a describes requirements only. No object below supplies execution authority.
PROFILE_ID = "PB-R1-LINUX-X86_64-EXACT1"
SOURCE_BASE_COMMIT = "9d05ef2707c58eb520aadd34660b41d6814871a4"
SOURCE_BASE_TREE = "f91fd9227fb4379b93ccd56f45917b29ffb30b6d"
RUNTIME_INVENTORY_SHA256 = "66b421203da530fb96bcdc459b4963a3dd9b5437a095e808bb55fa472950b09a"
RUNTIME_ENTRY_COUNT = 4324
PACKAGE_PATHS = ('docs/symphony-hardening-playbook-v4.1/P08_T04_AUTHORITY_OPERATOR.md',
 'tools/p08_authority/gate.py',
 'tools/p08_authority/profile-requirements.json',
 'tools/p08_authority/qualification-vectors.json',
 'tools/p08_authority/record-schemas.json',
 'tools/p08_authority/verify.py',
 'tools/tests/p08-portability-profiles.json',
 'tools/tests/p08_qualification_runner.py',
 'tools/tests/test_p08_authority_gate.py',
 'tools/tests/test_p08_authority_portability.py',
 'tools/tests/test_p08_authority_verify.py')
PRESERVED_FILES = {'tools/p08_authority/gate.py': {'bytes': 21534,
                                 'git_blob': 'ec92e83978283a734b631bf763cca3e108058a31',
                                 'mode': '100644',
                                 'sha256': '967339bbbc269aa89a9792fb3f956e5e4f18f551951a12e1976ba5af08187bf6'},
 'tools/p08_authority/profile-requirements.json': {'bytes': 35511,
                                                   'git_blob': 'fc6fd6e1b8776519f41ee7c1f25b2a0fc4ac311a',
                                                   'mode': '100644',
                                                   'sha256': '0cf688495273e861c424def7e72afcd7b3841f1045ba456d974c3d5adc0af8e6'},
 'tools/p08_authority/qualification-vectors.json': {'bytes': 30938,
                                                    'git_blob': '74fe31e05a7a2e0e8b46804b21afc68a00ab70cc',
                                                    'mode': '100644',
                                                    'sha256': '84380bc0557e1a27b933734f015c0c382df618c1ba5669e30436780d1995f715'},
 'tools/p08_authority/record-schemas.json': {'bytes': 47739,
                                             'git_blob': '0f920aeeaf52f01b5b9e06c2ec220fcee2f2a52c',
                                             'mode': '100644',
                                             'sha256': '349f8d1e405ed915481430100c6471dc91338186a645f1aa799fb95b6a0e7430'},
 'tools/p08_authority/verify.py': {'bytes': 74514,
                                   'git_blob': '7475f3a2a31d7f2a7af10a14a4dae565b4ff3e0f',
                                   'mode': '100644',
                                   'sha256': 'a01245e1ff8e439078655c8bfb08464c4a4b3eb382cae865ab9145b6827bb309'},
 'tools/tests/test_p08_authority_gate.py': {'bytes': 45561,
                                            'git_blob': 'e51a12a4a78c0ab15a5591b62ee347a6c3eb6013',
                                            'mode': '100644',
                                            'sha256': '86013652455743cecff6e301cd67e2567ae21cae3cee9cddd1cd210a83c26f57'}}
FIXTURE_IDENTITIES = {
    "BASE_SOURCE_INVENTORY": {"bytes": 112682,
        "sha256": "c78f7f6e73992b13f912dc18471c2395dce6738560842423f444cc38cfc839eb"},
    "BOOTSTRAP_REVIEW_ARCHIVE": {"bytes": 244274,
        "sha256": "956ae09a45c8d1ada5030d67cc32230fb6d5f2454ac8aa89f398488e380152a5"},
}
PROBE_IDS = ("PB-EXEC-DENY-01", "PB-NET-DENY-01", "PB-WRITE-DENY-01")


class PreparationRefusal(RuntimeError):
    """A typed source/profile refusal, never an execution approval."""

    def __init__(self, code: str):
        self.code = code
        super().__init__(code)


class ReleaseRefusalCode(str, Enum):
    ABSENT = "EXTERNAL_RELEASE_ABSENT"
    MALFORMED = "EXTERNAL_RELEASE_MALFORMED"
    UNCONFIGURED = "EXTERNAL_RELEASE_UNCONFIGURED"
    UNAUTHENTICATED = "EXTERNAL_RELEASE_UNAUTHENTICATED"


class ReleaseRefusal(PreparationRefusal):
    """R1a has no successful release result or admission token."""

    def __init__(self, reason: ReleaseRefusalCode):
        if type(reason) is not ReleaseRefusalCode:
            raise TypeError("release refusal requires a declared classification")
        self.reason = reason
        super().__init__(reason.value)


@dataclass(frozen=True, slots=True)
class UntrustedReleaseDescription:
    """Claimed identities only. Construction or parsing authenticates nothing."""

    profile_id: str
    candidate_commit: str
    candidate_tree: str
    source_inventory_sha256: str
    runtime_inventory_sha256: str
    attempt_id: str
    suite: str


_RELEASE_FIELDS = frozenset(UntrustedReleaseDescription.__dataclass_fields__)
_AUTHORITY_ASSERTIONS = frozenset(("approved", "authenticated", "status", "trust_anchor",
    "verifier", "callback", "provider", "approval", "accepted", "release_path"))


def _hex(value: object, length: int) -> bool:
    return type(value) is str and re.fullmatch("[0-9a-f]{" + str(length) + "}", value) is not None and value != "0" * length


def _unique_pairs(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("duplicate field")
        result[key] = value
    return result


def _check_description(value: UntrustedReleaseDescription) -> None:
    if (type(value) is not UntrustedReleaseDescription or
            value.profile_id != PROFILE_ID or value.suite not in ("verify", "gate", "portability") or
            any(not _hex(getattr(value, name), length) for name, length in (
                ("candidate_commit", 40), ("candidate_tree", 40),
                ("source_inventory_sha256", 64), ("runtime_inventory_sha256", 64), ("attempt_id", 32))) or
            value.candidate_commit == SOURCE_BASE_COMMIT or
            value.runtime_inventory_sha256 != RUNTIME_INVENTORY_SHA256):
        raise ReleaseRefusal(ReleaseRefusalCode.MALFORMED)


def parse_release_description(raw: bytes) -> UntrustedReleaseDescription:
    """Parse bounded untrusted claims without reading a path or choosing authority."""
    if type(raw) is not bytes or not 0 < len(raw) <= 65536:
        raise ReleaseRefusal(ReleaseRefusalCode.MALFORMED)
    try:
        value = json.loads(raw.decode("ascii"), object_pairs_hook=_unique_pairs)
    except (ValueError, UnicodeError, RecursionError):
        raise ReleaseRefusal(ReleaseRefusalCode.MALFORMED) from None
    if type(value) is not dict:
        raise ReleaseRefusal(ReleaseRefusalCode.MALFORMED)
    if _AUTHORITY_ASSERTIONS.intersection(value):
        raise ReleaseRefusal(ReleaseRefusalCode.UNAUTHENTICATED)
    if set(value) != _RELEASE_FIELDS or any(type(item) is not str for item in value.values()):
        raise ReleaseRefusal(ReleaseRefusalCode.MALFORMED)
    description = UntrustedReleaseDescription(**value)
    _check_description(description)
    return description


def require_authentic_release(description: UntrustedReleaseDescription | None = None) -> NoReturn:
    """Always refuse. No authenticator, trust anchor, callback or success path exists.

    A future protocol/custodian handoff requires independent acceptance and a
    separate source-change authorization before this boundary can admit anything.
    """
    if description is None:
        raise ReleaseRefusal(ReleaseRefusalCode.ABSENT)
    _check_description(description)
    raise ReleaseRefusal(ReleaseRefusalCode.UNCONFIGURED)


def require_execution_receipt(receipt: object = None) -> NoReturn:
    """A PASS log, direct unittest run or matching hash is ineligible evidence.

    R1a defines no authenticated receipt or external observer protocol.
    """
    raise ReleaseRefusal(ReleaseRefusalCode.UNAUTHENTICATED)


def require_independent_custody(observation: object = None) -> NoReturn:
    """Mode bits, same-UID files and caller assertions cannot establish custody."""
    raise PreparationRefusal("CUSTODY_UNESTABLISHED")


def select_profile(profile_id: str) -> str:
    """Select one fixed descriptive requirement set, never an authority source."""
    if type(profile_id) is not str or profile_id != PROFILE_ID:
        raise PreparationRefusal("PROFILE_UNSUPPORTED")
    return PROFILE_ID


def select_request(argv: list[str]) -> tuple[str, str]:
    if (type(argv) is not list or len(argv) != 4 or argv[0] != "--profile" or
            argv[2] != "--suite" or type(argv[3]) is not str or
            argv[3] not in ("verify", "gate", "portability")):
        raise PreparationRefusal("PROFILE_ARGUMENTS_INVALID")
    return select_profile(argv[1]), argv[3]


def fixture_bytes(logical_id: str) -> NoReturn:
    """No fixture mapping or file is read until a later authenticated release.

    There is deliberately no path argument, environment override, search,
    downloader, fixture staging operation or successful R1a implementation.
    """
    if type(logical_id) is not str or logical_id not in FIXTURE_IDENTITIES:
        raise PreparationRefusal("FIXTURE_INPUT_UNKNOWN")
    require_authentic_release()


def check_fixture_bytes(logical_id: str, raw: bytes | None) -> None:
    """Check supplied bytes as data only; this neither reads nor approves inputs."""
    if type(logical_id) is not str or logical_id not in FIXTURE_IDENTITIES:
        raise PreparationRefusal("FIXTURE_INPUT_UNKNOWN")
    if raw is None:
        raise PreparationRefusal("FIXTURE_INPUT_MISSING")
    expected = FIXTURE_IDENTITIES[logical_id]
    if type(raw) is not bytes or len(raw) != expected["bytes"] or hashlib.sha256(raw).hexdigest() != expected["sha256"]:
        raise PreparationRefusal("FIXTURE_INPUT_MISMATCH")


def _entries(items: object, count: int) -> dict[str, dict]:
    if type(items) is not list or len(items) != count:
        raise PreparationRefusal("SOURCE_INVENTORY_INVALID")
    result = {}
    for entry in items:
        if type(entry) is not dict or set(entry) != {"path", "mode", "bytes", "git_blob", "sha256"}:
            raise PreparationRefusal("SOURCE_INVENTORY_INVALID")
        path = entry["path"]
        if (type(path) is not str or not 0 < len(path) <= 1024 or not path.isascii() or
                any(ord(char) < 33 or ord(char) > 126 for char in path) or "\\" in path or
                any(part in ("", ".", "..") for part in path.split("/")) or path in result or
                entry["mode"] not in ("100644", "100755") or type(entry["bytes"]) is not int or
                entry["bytes"] < 0 or not _hex(entry["git_blob"], 40) or not _hex(entry["sha256"], 64)):
            raise PreparationRefusal("SOURCE_INVENTORY_INVALID")
        # Only this exact inherited identity exceeds the ordinary 16 MiB cap.
        # Metadata equality supplies no approval, custody or execution authority.
        if entry["bytes"] > 16777216 and entry != {
                "path": ".github/media/symphony-demo.mp4", "mode": "100644", "bytes": 30446771,
                "git_blob": "32b1f857f45eb901905ea24355b599fb417f53c5",
                "sha256": "0baa5f6276ea9a790d8072e690c547ed02afb3f95312266d3f27a923d4f58ec1"}:
            raise PreparationRefusal("SOURCE_INVENTORY_INVALID")
        result[path] = entry
    if list(result) != sorted(result):
        raise PreparationRefusal("SOURCE_INVENTORY_INVALID")
    for path in result:
        if any("/".join(path.split("/")[:i]) in result for i in range(1, len(path.split("/")))):
            raise PreparationRefusal("SOURCE_INVENTORY_INVALID")
    return result


def _tree_id(entries: dict[str, dict]) -> str:
    """Reproduce Git tree identity from declared metadata, not custody or approval."""
    root = {}
    for path, entry in entries.items():
        parts = path.split("/")
        node = root
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = entry

    def encode(node):
        rows = []
        for name, value in node.items():
            if "git_blob" in value and set(value) == {"path", "mode", "bytes", "git_blob", "sha256"}:
                rows.append((name.encode("ascii"), value["mode"].encode("ascii") + b" " + name.encode("ascii") + b"\0" + bytes.fromhex(value["git_blob"])))
            else:
                rows.append(((name + "/").encode("ascii"), b"40000 " + name.encode("ascii") + b"\0" + encode(value)))
        raw = b"".join(row[1] for row in sorted(rows))
        return hashlib.sha1(b"tree " + str(len(raw)).encode("ascii") + b"\0" + raw).digest()
    return encode(root).hex()


def check_source_inventory(inventory: dict, observed_entries: list[dict], base_entries: list[dict]) -> None:
    """Check complete metadata closure only. Success grants no execution admission.

    Observations are untrusted until a separately accepted external mechanism
    authenticates their source and custody. R1a supplies no such mechanism.
    """
    keys = {"schema", "base_commit", "base_tree", "candidate_commit", "candidate_tree", "package_files", "tree_files"}
    if (type(inventory) is not dict or set(inventory) != keys or
            inventory["schema"] != "p08-r1a-source-inventory-1" or
            inventory["base_commit"] != SOURCE_BASE_COMMIT or inventory["base_tree"] != SOURCE_BASE_TREE or
            not _hex(inventory["candidate_tree"], 40) or
            (inventory["candidate_commit"] is not None and
             (not _hex(inventory["candidate_commit"], 40) or inventory["candidate_commit"] == SOURCE_BASE_COMMIT))):
        raise PreparationRefusal("SOURCE_INVENTORY_INVALID")
    base = _entries(base_entries, 395)
    package = _entries(inventory["package_files"], 11)
    tree = _entries(inventory["tree_files"], 406)
    observed = _entries(observed_entries, 406)
    if (set(package) != set(PACKAGE_PATHS) or set(base).intersection(package) or
            set(tree) != set(base).union(package) or tree != observed or
            _tree_id(base) != SOURCE_BASE_TREE or _tree_id(tree) != inventory["candidate_tree"] or
            any(tree[path] != entry for path, entry in base.items()) or
            any(tree[path] != entry or entry["mode"] != "100644" for path, entry in package.items()) or
            any({key: package[path][key] for key in expected} != expected
                for path, expected in PRESERVED_FILES.items())):
        raise PreparationRefusal("SOURCE_INVENTORY_INVALID")


def check_runtime_inventory(raw: bytes | None, observed: dict) -> None:
    """Compare exact runtime metadata; no file reads or authority are supplied."""
    if raw is None:
        raise PreparationRefusal("RUNTIME_INPUTS_INCOMPLETE")
    if type(raw) is not bytes or len(raw) > 16777216 or hashlib.sha256(raw).hexdigest() != RUNTIME_INVENTORY_SHA256:
        raise PreparationRefusal("RUNTIME_INVENTORY_MISMATCH")
    try:
        inventory = json.loads(raw.decode("ascii"), object_pairs_hook=_unique_pairs)
        entries = inventory["entries"]
        if type(entries) is not list or len(entries) != RUNTIME_ENTRY_COUNT or type(observed) is not dict:
            raise ValueError("incomplete closure")
        expected = {}
        for item in entries:
            if (type(item) is not dict or set(item) != {"path", "bytes", "sha256"} or
                    type(item["path"]) is not str or not item["path"].startswith("/") or item["path"] in expected or
                    type(item["bytes"]) is not int or item["bytes"] < 0 or not _hex(item["sha256"], 64)):
                raise ValueError("invalid closure entry")
            expected[item["path"]] = {"bytes": item["bytes"], "sha256": item["sha256"]}
        if expected != observed or any(expected[path]["sha256"] != value for path, value in PINS.items()):
            raise ValueError("closure drift")
    except (KeyError, TypeError, ValueError, UnicodeError, RecursionError):
        raise PreparationRefusal("RUNTIME_INPUTS_INCOMPLETE") from None


REPO = Path(__file__).resolve().parents[2]
OUT = REPO / ".p08-authority-test-output"
PYTHON = "/usr/bin/python3.14"
SSH = "/usr/bin/ssh-keygen"
LIB = "/usr/lib/x86_64-linux-gnu/libseccomp.so.2.6.0"
PINS = {PYTHON: "52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41",
        SSH: "2dd834413c9d3f4c0e3535b9fcf2e96e14c11f3d36fd23b6c5fc24e50411d051",
        LIB: "df995d80c824876afc38528b5e71d258e1844eb524cd9d34f9a7898562fd99e7"}
NAMESPACES = ("symphony.p08.source-stage.v1", "symphony.p08.input-review.v1",
              "symphony.p08.input-owner.v1", "symphony.p08.native-grant.v1",
              "symphony.p08.build-result.v1")
SIGNED = ("source-stage-acceptance", "input-review", "owner-input-decision",
          "native-execution-grant", "generated-native-execution-grant", "compilation-result")
KEYS = tuple(str(OUT / "keys" / n) for n in ("owner", "reviewer", "rogue"))
SENTINELS = ("pass", "raise SystemExit(7)", "import time; time.sleep(2)",
             "from pathlib import Path; Path(" + repr(str(OUT / "sentinels" / "one.txt")) + ").write_text('one')")
SUITES = {name: [PYTHON, "-I", "-S", "-B", "-m", "unittest", "discover", "-s", str(REPO / "tools/tests"),
                 "-p", "test_p08_authority_" + name + ".py", "-v"] for name in ("verify", "gate", "portability")}
ENV = {"HOME": str(OUT / "home"), "TMPDIR": str(OUT / "tmp"), "TMP": str(OUT / "tmp"),
       "TEMP": str(OUT / "tmp"), "XDG_CACHE_HOME": str(OUT / "cache"), "LANG": "C.UTF-8",
       "PATH": "/nonexistent"}


def install_write_audit():
    """Audit Python file mutations; OpenSSH effects have separate exact argv limits.

    This is additional test evidence, not a kernel filesystem containment claim.
    Descriptor writes are permitted only because the reviewed runner controls
    inherited descriptors and the test source opens its own finite files.
    """
    require_authentic_release()
    if getattr(sys, '_p08_test_audit_installed', False):
        return
    fd = os.open(OUT / 'logs' / ('python-write-audit-' + str(os.getpid()) + '.jsonl'),
                 os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    root = str(OUT)
    def inside(path):
        if isinstance(path, int):
            return True
        actual = os.path.abspath(os.fsdecode(path))
        parent = os.path.realpath(os.path.dirname(actual))
        return os.path.commonpath((actual, root)) == root and os.path.commonpath((parent, root)) == root
    def audit(event, args):
        paths = []
        if event == 'open' and args[2] & (os.O_WRONLY | os.O_RDWR | os.O_CREAT | os.O_TRUNC | os.O_APPEND):
            paths = [args[0]]
        elif event in ('os.mkdir', 'os.remove', 'os.rmdir', 'os.chmod', 'os.truncate'):
            paths = [args[0]]
        elif event in ('os.rename', 'os.link'):
            paths = list(args[:2])
        elif event == 'os.symlink':
            paths = [args[1]]
        if paths:
            # dir_fd writes are reviewed register operations; a relative path
            # is resolved through the actual directory descriptor, not cwd.
            dirfd = args[3] if event == 'open' and len(args) > 3 else None
            allowed = all(inside(p) for p in paths)
            if event == 'open' and isinstance(paths[0], str) and not os.path.isabs(paths[0]):
                # Python's open audit does not expose dir_fd. These names are
                # limited to the gate's reviewed no-replace register files.
                allowed = bool(__import__('re').fullmatch(r'(?:\.lock|epoch\.json|(?:grant|run|nonce)-[0-9a-f]+\.json|event-[0-9a-f]+-[0-9]{2}\.json)', paths[0]))
            os.write(fd, (json.dumps({'event': event, 'paths': [str(p) for p in paths], 'allowed': allowed}) + '\n').encode('ascii'))
            if not allowed:
                raise PermissionError('test write outside approved root')
    sys.addaudithook(audit)
    sys._p08_test_audit_installed = True


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def permitted_argv(argv, suite, initial=False):
    if initial:
        return argv == SUITES[suite]
    if argv and argv[0] == PYTHON:
        return len(argv) == 6 and argv[1:5] == ["-I", "-S", "-B", "-c"] and argv[5] in SENTINELS
    if not argv or argv[0] != SSH:
        return False
    if len(argv) == 10 and argv[1:8] == ["-q", "-t", "ed25519", "-N", "", "-C", "p08-test-only"]:
        return argv[8] == "-f" and argv[9] in KEYS
    if len(argv) == 8 and argv[1:3] == ["-Y", "sign"] and argv[3] == "-f" and argv[5] == "-n":
        paths = {str(OUT / "fixtures/verify" / (stem + ".json")) for stem in SIGNED}
        return argv[4] in KEYS and argv[6] in NAMESPACES and argv[7] in paths
    if len(argv) == 11 and argv[1:3] == ["-Y", "verify"] and argv[3] == "-f" and argv[5] == "-I" \
            and argv[7] == "-n" and argv[9] == "-s":
        signers = {str(OUT / "fixtures/verify/signers" / role) for role in ("owner", "reviewer")}
        sigs = {str(OUT / "fixtures/verify" / sub / (stem + ".sshsig"))
                for stem in SIGNED for sub in ("", "producer")}
        return argv[4] in signers and argv[6] in ("test-owner", "test-reviewer", "test-rogue") \
            and argv[8] in NAMESPACES and argv[10] in sigs
    return False


def preflight() -> NoReturn:
    """No positive release exists. Refuse before any output, fixture or control effect.

    The former output-root JSON status is deliberately not read. Complete source,
    runtime and custody checks remain necessary after a future mechanism is
    separately specified, authorized, implemented and independently reviewed.
    """
    require_authentic_release()


class Cmp(ctypes.Structure):
    _fields_ = [("arg", ctypes.c_uint), ("op", ctypes.c_int), ("a", ctypes.c_uint64), ("b", ctypes.c_uint64)]


class Data(ctypes.Structure):
    _fields_ = [("nr", ctypes.c_int), ("arch", ctypes.c_uint32), ("ip", ctypes.c_uint64), ("args", ctypes.c_uint64 * 6)]


class Request(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint64), ("pid", ctypes.c_uint32), ("flags", ctypes.c_uint32), ("data", Data)]


class Response(ctypes.Structure):
    _fields_ = [("id", ctypes.c_uint64), ("val", ctypes.c_int64), ("error", ctypes.c_int32), ("flags", ctypes.c_uint32)]


def _read_cstring(fd, address):
    raw = os.pread(fd, 8192, address)
    end = raw.find(b"\0")
    if end < 0:
        raise RuntimeError("unbounded exec argument")
    return raw[:end].decode("ascii")


def _exec_request(request):
    if request.data.arch != 0xC000003E or request.data.nr != 59:
        raise RuntimeError("execveat or unsupported architecture")
    fd = os.open("/proc/" + str(request.pid) + "/mem", os.O_RDONLY | os.O_CLOEXEC)
    try:
        path = _read_cstring(fd, request.data.args[0])
        argv = []
        for i in range(128):
            ptr = int.from_bytes(os.pread(fd, 8, request.data.args[1] + i * 8), "little")
            if not ptr:
                return path, argv
            argv.append(_read_cstring(fd, ptr))
    finally:
        os.close(fd)
    raise RuntimeError("too many exec arguments")


def _filter(lib):
    lib.seccomp_init.argtypes = [ctypes.c_uint32]
    lib.seccomp_init.restype = ctypes.c_void_p
    lib.seccomp_syscall_resolve_name.argtypes = [ctypes.c_char_p]
    lib.seccomp_syscall_resolve_name.restype = ctypes.c_int
    lib.seccomp_rule_add.argtypes = [ctypes.c_void_p, ctypes.c_uint32, ctypes.c_int, ctypes.c_uint]
    lib.seccomp_rule_add.restype = ctypes.c_int
    lib.seccomp_load.argtypes = [ctypes.c_void_p]
    lib.seccomp_load.restype = ctypes.c_int
    lib.seccomp_notify_fd.argtypes = [ctypes.c_void_p]
    lib.seccomp_notify_fd.restype = ctypes.c_int
    ctx = lib.seccomp_init(0x7FFF0000)
    if not ctx:
        raise RuntimeError("seccomp init failed")
    def add(name, action=0x50001, *comparisons):
        nr = lib.seccomp_syscall_resolve_name(name.encode())
        if nr < 0 or lib.seccomp_rule_add(ctx, action, nr, len(comparisons), *comparisons):
            raise RuntimeError("seccomp rule failed " + name)
    for name in ("connect", "sendto", "sendmmsg", "io_uring_setup", "io_uring_enter", "io_uring_register",
                 "ptrace", "process_vm_writev", "mount", "umount2", "unshare", "setns", "bpf"):
        add(name)
    add("socket", 0x50001, Cmp(0, 1, 1, 0))  # only local AF_UNIX creation
    add("sendmsg", 0x50001, Cmp(2, 7, 0x20000000, 0x20000000))
    for flag in (0x80, 0x00020000, 0x02000000, 0x04000000, 0x08000000,
                 0x10000000, 0x20000000, 0x40000000):
        add("clone", 0x50001, Cmp(0, 7, flag, flag))
    add("clone3", 0x50026)  # ENOSYS, permitting libc fallback without namespace flags
    add("execve", 0x7FC00000)
    add("execveat", 0x7FC00000)
    if lib.seccomp_load(ctx):
        raise RuntimeError("seccomp load failed")
    nfd = lib.seccomp_notify_fd(ctx)
    if nfd < 0:
        raise RuntimeError("seccomp user notification missing")
    return nfd


def _cleanup_adopted(log):
    """Reap or terminate descendants orphaned by the finite suite leader."""
    deadline = time.monotonic() + 2
    found = False
    while True:
        children = Path('/proc/self/task/' + str(os.getpid()) + '/children').read_text('ascii').split()
        if not children:
            return found
        found = True
        for child in children:
            child_pid = int(child)
            try:
                os.kill(child_pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            log.write(json.dumps({"orphan_terminated": child_pid}) + '\n')
        while True:
            try:
                reaped, unused = os.waitpid(-1, os.WNOHANG)
            except ChildProcessError:
                break
            if not reaped:
                break
        if time.monotonic() > deadline:
            raise RuntimeError('descendant cleanup uncertain')
        time.sleep(0.01)


def main():
    development = None
    release = None
    if sys.argv[1:3] == ['--profile', 'PB-D01-OWNER-RELEASE-1']:
        # Fixed source-relative import. No provider callback or trust selector.
        import importlib.util
        spec = importlib.util.spec_from_file_location('p08_development_release',
            REPO / 'tools/tests/p08_development_release.py')
        development = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(development)
        attempt = development.select_request(sys.argv[1:])
        # Nothing below, including output creation and native loading, occurs
        # unless independently authenticated issuance and consumption succeed.
        release = development.prepare_launch(REPO, attempt)
        if OUT.exists() or OUT.is_symlink():
            raise development.Refusal('DEVELOPMENT_OUTPUT_ALREADY_EXISTS')
        OUT.mkdir(mode=0o700)
        for name in ('logs', 'tmp', 'home', 'cache'):
            (OUT / name).mkdir(mode=0o700)
        suite = development.SUITE
        SUITES[suite] = development.launcher_command(REPO, attempt)
        approval = {'scope_sha256': release['source_inventory_sha256']}
    else:
        profile_id, suite = select_request(sys.argv[1:])
        select_profile(profile_id)
        approval = preflight()
    return _run_suite(approval, suite, development, release)


def _run_suite(approval, suite, development=None, release=None):
    logpath = OUT / "logs" / (suite + "-exec-" + str(time.time_ns()) + ".jsonl")
    log = logpath.open("x", buffering=1)
    log.write(json.dumps({"profile": "OFFLINE_SYNTHETIC_ONLY", "suite": suite, "environment": ENV,
                          "source_scope_sha256": approval["scope_sha256"], "pins": PINS}) + "\n")
    lib = ctypes.CDLL(LIB, use_errno=True)
    # This launcher process adopts orphaned suite descendants. No system or
    # service setting changes, privilege or namespace operation is involved.
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(36, 1, 0, 0, 0):  # PR_SET_CHILD_SUBREAPER
        raise RuntimeError('bounded descendant adoption unavailable')
    stdio_path = OUT / "logs" / (suite + "-stdio-" + str(time.time_ns()) + ".log")
    stdio_fd = os.open(stdio_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    parent, child = socket.socketpair()
    pid = os.fork()
    if pid == 0:
        parent.close()
        log.close()
        os.setsid()
        if development is not None:
            import resource
            for kind, bound in ((resource.RLIMIT_CPU, 50), (resource.RLIMIT_AS, 1610612736),
                                (resource.RLIMIT_FSIZE, 8388608), (resource.RLIMIT_NOFILE, 128),
                                (resource.RLIMIT_CORE, 0)):
                resource.setrlimit(kind, (bound, bound))
        null_fd = os.open("/dev/null", os.O_RDONLY | os.O_CLOEXEC)
        os.dup2(null_fd, 0)
        os.dup2(stdio_fd, 1)
        os.dup2(stdio_fd, 2)
        # Standard descriptors now reference /dev/null and our exclusive log,
        # never inherited service/network sockets.
        # Drop inherited service sockets/descriptors before filtering or spawning.
        preserve = {0, 1, 2, child.fileno()}
        # D02 may pass one preconnected host-control descriptor. It is a
        # cooperative development adapter, never a production provider.
        host_fd = getattr(development, 'child_control_fd', None)
        if host_fd is not None:
            if type(host_fd) is not int or host_fd < 3:
                raise RuntimeError('invalid development host descriptor')
            preserve.add(host_fd)
        for path in Path("/proc/self/fd").iterdir():
            fd = int(path.name)
            if fd not in preserve:
                try:
                    os.close(fd)
                except OSError:
                    pass
        nfd = _filter(lib)
        child.sendmsg([b"F"], [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array("i", [nfd]))])
        child.close()
        os.close(nfd)
        # Fixture-only key generation is part of this reviewed child profile.
        import subprocess
        for key in (() if development is not None else KEYS):
            if not Path(key).exists():
                subprocess.run([SSH, "-q", "-t", "ed25519", "-N", "", "-C", "p08-test-only", "-f", key],
                               env=ENV, stdin=subprocess.DEVNULL, check=True)
        os.chdir(REPO)
        os.execve(PYTHON, SUITES[suite], ENV)
    os.close(stdio_fd)
    alive = True
    nfd = None
    suite_pidfd = None

    def terminate_leader():
        if development is not None:
            # A pidfd remains tied to this child even after exit. Never signal
            # a numeric process group after its leader has been reaped.
            if suite_pidfd is not None:
                try:
                    signal.pidfd_send_signal(suite_pidfd, signal.SIGKILL)
                except ProcessLookupError:
                    pass
            else:
                # Still our unreaped child if pidfd acquisition itself failed.
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
        else:
            try:
                os.killpg(pid, signal.SIGKILL)
            except ProcessLookupError:
                try:
                    os.kill(pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
    try:
        child.close()
        if development is not None:
            suite_pidfd = os.pidfd_open(pid)
            development.register_child(REPO, release, pid)
        parent.settimeout(5)
        message, ancillary, flags, address = parent.recvmsg(1, socket.CMSG_SPACE(4))
        if message != b"F" or not ancillary:
            terminate_leader()
            raise RuntimeError("seccomp setup not acknowledged")
        received = array.array("i")
        received.frombytes(ancillary[0][2][:4])
        nfd = received[0]
        parent.close()
        first = True
        denied = False
        deadline = time.monotonic() + 120
        previous_clock = time.time()
        while True:
            if development is not None:
                clock = time.time()
                if clock < previous_clock or clock >= release['expires_at']:
                    raise development.Refusal('RELEASE_EXPIRED_OR_CLOCK_CHANGED')
                previous_clock = clock
                development.check_revocation(REPO, release)
            done, result = os.waitpid(pid, os.WNOHANG)
            if done:
                alive = False
                code = os.waitstatus_to_exitcode(result)
                orphans = _cleanup_adopted(log)
                log.write(json.dumps({"suite_exit": code, "denied_exec": denied, "unexpected_orphans": orphans}) + "\n")
                print(json.dumps({"suite_exit": code, "denied_exec": denied, "unexpected_orphans": orphans, "stdio_log": str(stdio_path)}), flush=True)
                return 1 if denied or orphans else code
            if time.monotonic() > deadline:
                terminate_leader()
                os.waitpid(pid, 0)
                alive = False
                raise RuntimeError("finite suite deadline exceeded")
            if not select.select([nfd], [], [], 0.05)[0]:
                continue
            buf = bytearray(ctypes.sizeof(Request))
            try:
                import fcntl
                fcntl.ioctl(nfd, 0xC0502100, buf, True)
            except OSError as error:
                if error.errno in (errno.EINTR, errno.ENOENT):
                    continue
                raise
            request = Request.from_buffer_copy(buf)
            try:
                path, argv = _exec_request(request)
                initial = request.pid == pid and path == PYTHON and first
                command_allowed = (argv == SUITES[suite] if initial else
                    development.permitted_verification(argv, REPO, pid)) if development is not None else \
                    permitted_argv(argv, suite, initial=initial)
                permit = path in (PYTHON, SSH) and argv and path == argv[0] \
                    and digest(path) == PINS[path] and command_allowed
                if initial:
                    first = False
            except Exception:
                path, argv, permit = "<unreadable>", [], False
            log.write(json.dumps({"path": path, "argv": argv, "permitted": bool(permit)}) + "\n")
            denied |= not permit
            response = Response(request.id, 0, 0 if permit else -errno.EPERM, 1 if permit else 0)
            try:
                fcntl.ioctl(nfd, 0xC0182101, bytes(response))
            except OSError as error:
                if error.errno != errno.ENOENT:
                    raise
    finally:
        if alive:
            terminate_leader()
            try:
                os.waitpid(pid, 0)
            except ChildProcessError:
                pass
        _cleanup_adopted(log)
        if nfd is not None:
            os.close(nfd)
        if suite_pidfd is not None:
            os.close(suite_pidfd)
        parent.close()
        log.close()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
