env -i PATH=/usr/bin:/bin LANG=C.UTF-8 \
  /usr/bin/python3 -I - --stage <<'PY'
import base64, binascii, ctypes, datetime, gzip, hashlib, io, json
import os, pwd, shutil, stat, subprocess, sys, tarfile, traceback
from pathlib import Path, PurePosixPath

def need(ok, message):
    if not ok:
        raise ValueError(message)

def verify_minisign(manifest, signature, public_b64):
    public = base64.b64decode(public_b64, validate=True)
    lines = signature.splitlines()
    need(len(lines) == 4, "signature structure")
    need(lines[0].startswith(b"untrusted comment: "), "untrusted prefix")
    packet = base64.b64decode(lines[1], validate=True)
    global_sig = base64.b64decode(lines[3], validate=True)
    need(len(public) == 42 and public[:2] == b"Ed", "public key format")
    need(len(packet) == 74 and len(global_sig) == 64, "signature length")
    need(packet[:2] == b"ED", "signature algorithm")
    need(packet[2:10] == public[2:10], "key ID")
    prefix = b"trusted comment: "
    need(lines[2].startswith(prefix), "trusted prefix")
    comment = lines[2][len(prefix):]
    need(0 < len(comment) <= 1024, "trusted comment length")
    need(all(32 <= c < 127 for c in comment), "trusted comment characters")
    sodium = ctypes.CDLL("libsodium.so.23")
    need(sodium.sodium_init() >= 0, "sodium initialization")
    check = sodium.crypto_sign_verify_detached
    check.argtypes = [ctypes.c_void_p, ctypes.c_void_p,
                      ctypes.c_ulonglong, ctypes.c_void_p]
    check.restype = ctypes.c_int

    def check_signature(sig, message):
        rc = check(ctypes.create_string_buffer(sig),
                   ctypes.create_string_buffer(message), len(message),
                   ctypes.create_string_buffer(public[10:]))
        need(rc == 0, "Ed25519 signature")

    check_signature(packet[10:], hashlib.blake2b(manifest).digest())
    check_signature(global_sig, packet[10:] + comment)
    need(comment == b"devvm 0.1.0", "release comment")

MAX_EXPANDED = 2 * 1024**3
MAX_MEMBER = 512 * 1024**2
DEV_PREFIX = "devvm-0.1.0-linux-amd64"
DEV_FILES = {DEV_PREFIX + "/" + n
             for n in ("devvm", "LICENSE", "README.md", "CHANGELOG.md")}
LIMA_BINS = {"limactl", "lima", "nerdctl.lima", "apptainer.lima",
             "docker.lima", "podman.lima", "kubectl.lima"}
LIMA_LINK = "share/doc/lima/templates"
LIMA_TARGET = "../../lima/templates"

def canonical_name(raw, is_dir):
    need(raw and not raw.startswith(("/", "\\")), "absolute/empty path")
    need(all(32 <= ord(c) < 127 for c in raw) and "\\" not in raw,
         "path characters")
    if raw in (".", "./"):
        need(is_dir, "non-directory archive root")
        return "."
    if raw.startswith("./"):
        raw = raw[2:]
    if is_dir and raw.endswith("/"):
        raw = raw[:-1]
    need(all(p not in ("", ".", "..") for p in raw.split("/")),
         "path traversal or alias")
    need(":" not in raw, "colon path")
    return raw

def scan_archive(stream, flavor):
    plan, seen, spelling, total = [], set(), {}, 0

    def read(n):
        nonlocal total
        data = stream.read(n)
        total += len(data)
        need(total <= MAX_EXPANDED, "expanded archive budget")
        need(len(data) == n, "truncated tar")
        return data

    while True:
        block = read(512)
        if block == bytes(512):
            need(read(512) == bytes(512), "tar end marker")
            while True:
                tail = stream.read(1024**2)
                total += len(tail)
                need(total <= MAX_EXPANDED, "expanded archive budget")
                if not tail:
                    break
                need(not any(tail), "nonzero data after tar end")
            break

        need(len(plan) < 10000, "member count")
        need(block[257:265] in (b"ustar\x0000", b"ustar  \x00"),
             "unsupported tar header format")
        member = tarfile.TarInfo.frombuf(block, "utf-8", "strict")
        need(member.type in (tarfile.REGTYPE, tarfile.AREGTYPE,
                             tarfile.DIRTYPE, tarfile.SYMTYPE),
             "unsupported tar entry or extension")
        kind = ("dir" if member.isdir() else
                "symlink" if member.issym() else "file")
        name = canonical_name(member.name, kind == "dir")
        need(name.casefold() not in seen, "duplicate/aliased path")
        seen.add(name.casefold())

        parts = name.split("/")
        for length in range(1, len(parts) + 1):
            prefix = "/".join(parts[:length])
            need(spelling.get(prefix.casefold(), prefix) == prefix,
                 "aliased parent spelling")
            spelling[prefix.casefold()] = prefix

        need(0 <= member.size <= MAX_MEMBER, "member size")
        need(kind == "file" or member.size == 0, "non-file payload")
        allowed_modes = ({0o777} if kind == "symlink" else
                         {0o755} if kind == "dir" else {0o644, 0o755})
        need(member.mode in allowed_modes, "unexpected permissions")

        if flavor == "devvm":
            need((name == DEV_PREFIX and kind == "dir") or
                 (name in DEV_FILES and kind == "file"), "Devvm member")
        else:
            need(flavor == "lima", "archive flavor")
            allowed_dir = name in {
                ".", "bin", "libexec", "libexec/lima", "share",
                "share/lima", "share/doc", "share/doc/lima",
                "share/man", "share/man/man1",
            }
            allowed_tree = any(name.startswith(p) for p in (
                "libexec/lima/", "share/lima/",
                "share/doc/lima/", "share/man/man1/",
            ))
            allowed_bin = name.startswith("bin/") and name[4:] in LIMA_BINS
            need((kind == "dir" and (allowed_dir or allowed_tree)) or
                 (kind == "file" and (allowed_tree or allowed_bin)) or
                 (kind == "symlink" and name == LIMA_LINK),
                 "unexpected Lima member")

        if kind == "symlink":
            need(flavor == "lima" and name == LIMA_LINK and
                 member.linkname == LIMA_TARGET, "unexpected symlink")
        else:
            need(not member.linkname, "unexpected link metadata")

        plan.append({"name": name, "kind": kind, "size": member.size,
                     "mode": member.mode, "link": member.linkname,
                     "offset": total})
        remaining = (member.size + 511) // 512 * 512
        while remaining:
            amount = min(remaining, 1024**2)
            read(amount)
            remaining -= amount

    by_name = {row["name"]: row for row in plan}
    for row in plan:
        parts = row["name"].split("/")
        for length in range(1, len(parts)):
            parent = "/".join(parts[:length])
            if parent in by_name:
                need(by_name[parent]["kind"] == "dir",
                     "non-directory parent")

    if flavor == "devvm":
        need(DEV_FILES <= by_name.keys(), "missing Devvm files")
        need(by_name[DEV_PREFIX + "/devvm"]["mode"] == 0o755,
             "Devvm executable mode")
    else:
        need("bin/limactl" in by_name and
             by_name["bin/limactl"]["kind"] == "file" and
             by_name["bin/limactl"]["mode"] == 0o755,
             "missing Lima executable")
        need(LIMA_LINK in by_name and
             by_name[LIMA_LINK]["kind"] == "symlink",
             "missing expected Lima link")
        need("share/lima/templates" in by_name and
             by_name["share/lima/templates"]["kind"] == "dir",
             "missing Lima link target")
    return plan

def extract_validated(archive_path, destination, plan):
    destination.mkdir(mode=0o700)
    directories = set()
    for row in plan:
        path = PurePosixPath(row["name"])
        directories.update(str(p) for p in path.parents if str(p) != ".")
        if row["kind"] == "dir" and row["name"] != ".":
            directories.add(row["name"])
    for name in sorted(directories, key=lambda n: (n.count("/"), n)):
        (destination / name).mkdir(mode=0o700)

    with gzip.open(archive_path, "rb") as stream:
        for row in plan:
            if row["kind"] != "file":
                continue
            stream.seek(row["offset"])
            path = destination / row["name"]
            fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                         os.O_NOFOLLOW, 0o600)
            with os.fdopen(fd, "wb") as output:
                remaining = row["size"]
                while remaining:
                    data = stream.read(min(remaining, 1024**2))
                    need(data, "truncated extraction payload")
                    output.write(data)
                    remaining -= len(data)
            path.chmod(0o700 if row["mode"] == 0o755 else 0o600)

    for row in plan:
        if row["kind"] == "symlink":
            os.symlink(row["link"], destination / row["name"])

def synthetic_tests():
    sodium = ctypes.CDLL("libsodium.so.23")
    need(sodium.sodium_init() >= 0, "sodium initialization")
    keypair = sodium.crypto_sign_seed_keypair
    keypair.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p]
    sign = sodium.crypto_sign_detached
    sign.argtypes = [ctypes.c_void_p, ctypes.c_void_p, ctypes.c_void_p,
                     ctypes.c_ulonglong, ctypes.c_void_p]

    def keys(seed):
        pk, sk = ctypes.create_string_buffer(32), ctypes.create_string_buffer(64)
        need(keypair(pk, sk, ctypes.create_string_buffer(seed)) == 0, "keypair")
        return pk.raw, sk

    pk, sk = keys(bytes(range(32)))
    other_pk, _ = keys(bytes(reversed(range(32))))

    def signed(message):
        out = ctypes.create_string_buffer(64)
        length = ctypes.c_ulonglong()
        need(sign(out, ctypes.byref(length),
                  ctypes.create_string_buffer(message), len(message), sk) == 0,
             "sign")
        need(length.value == 64, "signature size")
        return out.raw

    manifest = b"SYNTHETIC CHECKSUM MANIFEST\n"
    key_id = b"TESTKEY1"
    public = base64.b64encode(b"Ed" + key_id + pk)
    sig = signed(hashlib.blake2b(manifest).digest())
    packet = b"ED" + key_id + sig
    global_sig = signed(sig + b"devvm 0.1.0")

    def document(p=packet, g=global_sig, comment=b"devvm 0.1.0"):
        return b"\n".join([b"untrusted comment: synthetic",
                          base64.b64encode(p), b"trusted comment: " + comment,
                          base64.b64encode(g)]) + b"\n"

    cases = [
        ("valid manifest and comment", manifest, document(), public, True),
        ("modified manifest", manifest + b"!", document(), public, False),
        ("modified trusted comment", manifest,
         document(comment=b"devvm 0.1.1"), public, False),
        ("modified global signature", manifest,
         document(g=bytes([global_sig[0] ^ 1]) + global_sig[1:]), public, False),
        ("wrong signing key with same key ID", manifest, document(),
         base64.b64encode(b"Ed" + key_id + other_pk), False),
        ("invalid key ID", manifest,
         document(p=packet[:2] + b"BADKEYID" + packet[10:]), public, False),
        ("unexpected signature algorithm", manifest,
         document(p=b"Ed" + packet[2:]), public, False),
        ("truncated signature", manifest,
         document(p=packet[:-1]), public, False),
    ]
    for name, data, doc, key, expected in cases:
        try:
            verify_minisign(data, doc, key)
            accepted = True
        except (ValueError, binascii.Error):
            accepted = False
        need(accepted == expected, "unexpected test result: " + name)
        print("PASS: " + name + (" accepted" if accepted else " rejected"))
    print("SYNTHETIC_ED25519=8/8; RELEASE_FILES_TESTED=NO")

ROOT = Path("/home/jcschoeman96/sdv02")
DEVVM_RELEASE = "v0.1.0"
DEVVM_SOURCE = "e9bd270398730bf0f7ffe44e8f78f5da323daeb7"
LIMA_RELEASE = "v2.2.1"
LIMA_SOURCE = "27bc4c4b101e27994e01e36566a0f2091bbca507"
PUBLIC = "RWSjzFsn7ETaijKJ2y7F4DtZobXmyv+LmdclJwZP/KmAkLUwOCzWF/2b"
LIMA_FINGERPRINT = "C020EA876CE4E06C7AB95AEF49524C6F9F638F1A"
EXPECTED = {
    "devvm.SHA256SUMS":
        "9f703c06b2ab3a4b8c9e8963952e024f64964aa0ec9de09bfceefbf8b65df73a",
    "devvm.SHA256SUMS.minisig":
        "329cafe0b6659f60d36e3ccb320388276ecf061a411162deddb713864d1a3246",
    "devvm-0.1.0-linux-amd64.tar.gz":
        "fc939a651614917404766c8bf1c7f64aed8c136605e133e0602c55101a82284c",
    "lima.SHA256SUMS":
        "4805ceeb791229ecaddcde32bf04b14742f4d036b343ad5d8c478ba5d220fff2",
    "lima.SHA256SUMS.asc":
        "cc974212784876111d1a1d4ab2539e5c7fe2058de04e6c64c60d3887c8cabf2c",
    "lima-2.2.1-Linux-x86_64.tar.gz":
        "b391ac7fcac2b2a5a1628107756463188ded4d18d3104a40a66a8bb6fec01bcb",
    "lima-key.asc":
        "74d7c5d29b78a5967b0da91a2e9330b8a805fd1ea2c8a375dfae634ff85a6da0",
}
ARCHIVES = [
    ("devvm-0.1.0-linux-amd64.tar.gz", "devvm", "devvm-0.1.0"),
    ("lima-2.2.1-Linux-x86_64.tar.gz", "lima", "lima-2.2.1"),
]

def file_hash(path):
    with path.open("rb") as source:
        return hashlib.file_digest(source, "sha256").hexdigest()

def stage():
    need(os.geteuid() != 0 and pwd.getpwuid(os.geteuid()).pw_name ==
         "jcschoeman96", "ordinary intended user required")
    need(sys.version_info[:3] == (3, 14, 4), "review Python version change")
    need(ROOT.parent.resolve() == ROOT.parent and
         ROOT.parent.stat().st_uid == os.getuid(), "parent identity")
    need(not os.path.lexists(ROOT), "staging root already exists")
    need(shutil.disk_usage(ROOT.parent).free >= 10 * 1024**3,
         "insufficient staging disk reserve")
    os.umask(0o077)
    ROOT.mkdir(mode=0o700)
    evidence = ROOT / "evidence"
    evidence.mkdir(mode=0o700)

    def save(name, value):
        (evidence / name).write_text(json.dumps(value, indent=2) + "\n")

    def stamp():
        return datetime.datetime.now(datetime.timezone.utc).isoformat()

    def run(label, argv):
        start = stamp()
        try:
            result = subprocess.run(argv, capture_output=True, timeout=620,
                                    check=False, cwd=ROOT)
            rc, stdout, stderr = result.returncode, result.stdout, result.stderr
        except subprocess.TimeoutExpired as error:
            rc, stdout, stderr = 124, error.stdout or b"", error.stderr or b""
        (evidence / (label + ".stdout")).write_bytes(stdout)
        (evidence / (label + ".stderr")).write_bytes(stderr)
        save(label + ".command.json",
             {"argv": argv, "start": start, "end": stamp(), "exit": rc})
        need(rc == 0, label + " failed")
        return stdout

    def acquire(url, name, maximum):
        path = ROOT / "downloads" / name
        need(not os.path.lexists(path), "download target already exists")
        run("get-" + name, [
            "/usr/bin/curl", "-q", "--proto", "=https",
            "--proto-redir", "=https", "--tlsv1.2", "--fail",
            "--location", "--silent", "--show-error",
            "--connect-timeout", "15", "--max-time", "600",
            "--max-filesize", str(maximum), "--output", str(path), url,
        ])
        need(file_hash(path) == EXPECTED[name], "checksum: " + name)
        path.chmod(0o400)

    state = "FAILED_REVIEW_REQUIRED"
    save("status.json", {"state": "STARTED", "time": stamp()})
    try:
        for name in ("downloads", "software", "home", "verify", "tmp"):
            (ROOT / name).mkdir(mode=0o700)
        os.environ.update(HOME=str(ROOT / "home"),
                          GNUPGHOME=str(ROOT / "verify"),
                          TMPDIR=str(ROOT / "tmp"))
        save("scope.json", {
            "devvm_release": DEVVM_RELEASE, "devvm_source": DEVVM_SOURCE,
            "lima_release": LIMA_RELEASE, "lima_source": LIMA_SOURCE,
            "root": str(ROOT.resolve()), "uid": os.getuid(),
            "expected_sha256": EXPECTED,
            "downloaded_execution": False, "cleanup_authorized": False,
        })
        d = "https://github.com/devvmhq/devvm/releases/download/v0.1.0/"
        l = "https://github.com/lima-vm/lima/releases/download/v2.2.1/"
        for url, name in [
            (d + "SHA256SUMS", "devvm.SHA256SUMS"),
            (d + "SHA256SUMS.minisig", "devvm.SHA256SUMS.minisig"),
            (l + "SHA256SUMS", "lima.SHA256SUMS"),
            (l + "SHA256SUMS.asc", "lima.SHA256SUMS.asc"),
            ("https://github.com/AkihiroSuda.gpg", "lima-key.asc"),
        ]:
            acquire(url, name, 1024**2)

        downloads = ROOT / "downloads"
        verify_minisign((downloads / "devvm.SHA256SUMS").read_bytes(),
                        (downloads / "devvm.SHA256SUMS.minisig").read_bytes(),
                        PUBLIC)
        save("devvm-signature.json", {"verified": True, "public_key": PUBLIC,
                                     "trusted_comment": "devvm 0.1.0"})
        keyring = ROOT / "verify" / "lima-release.gpg"
        run("lima-dearmor", [
            "/usr/bin/gpg", "--no-options", "--homedir", str(ROOT / "verify"),
            "--batch", "--dearmor", "--output", str(keyring),
            str(downloads / "lima-key.asc"),
        ])
        status = run("lima-signature", [
            "/usr/bin/gpgv", "--homedir", str(ROOT / "verify"),
            "--status-fd", "1", "--keyring", str(keyring),
            str(downloads / "lima.SHA256SUMS.asc"),
            str(downloads / "lima.SHA256SUMS"),
        ]).decode("ascii")
        records = [line.split()[1:] for line in status.splitlines()
                   if line.startswith("[GNUPG:] ")]
        bad = {"BADSIG", "ERRSIG", "EXPSIG", "EXPKEYSIG", "REVKEYSIG",
               "NO_PUBKEY", "NODATA", "FAILURE", "ERROR",
               "KEYEXPIRED", "SIGEXPIRED"}
        need(not any(r and r[0] in bad for r in records), "OpenPGP status")
        valid = [r for r in records if r and r[0] == "VALIDSIG"]
        need(len(valid) == 1 and valid[0][1] == LIMA_FINGERPRINT,
             "Lima signer identity")
        need(len(valid[0]) in (10, 11), "VALIDSIG structure")
        if len(valid[0]) == 11:
            need(valid[0][-1] == LIMA_FINGERPRINT, "Lima primary key identity")

        for manifest, asset in [
            ("devvm.SHA256SUMS", ARCHIVES[0][0]),
            ("lima.SHA256SUMS", ARCHIVES[1][0]),
        ]:
            matches = [parts[0] for line in
                       (downloads / manifest).read_text("ascii").splitlines()
                       if len(parts := line.split()) == 2 and
                       parts[1].lstrip("*") == asset]
            need(matches == [EXPECTED[asset]], "signed manifest entry")

        acquire(d + ARCHIVES[0][0], ARCHIVES[0][0], 1024**3)
        acquire(l + ARCHIVES[1][0], ARCHIVES[1][0], 1024**3)

        # Validate both archives before creating either extraction target.
        plans = {}
        for asset, flavor, directory in ARCHIVES:
            with gzip.open(downloads / asset, "rb") as source:
                plans[asset] = scan_archive(source, flavor)
            save(flavor + "-validated-members.json", plans[asset])
        save("validation.json", {"both_archives_validated": True})

        for asset, flavor, directory in ARCHIVES:
            need(file_hash(downloads / asset) == EXPECTED[asset],
                 "archive changed after validation")
            extract_validated(downloads / asset,
                              ROOT / "software" / directory, plans[asset])
        state = "STAGED_NOT_EXECUTED"

    except BaseException:
        (evidence / "failure.txt").write_text(traceback.format_exc())
        raise

    finally:
        save("status.json", {"state": state, "time": stamp(),
                             "cleanup_authorized": False})
        inventory = []
        for base, dirs, files in os.walk(ROOT, followlinks=False):
            for name in sorted(dirs + files):
                path = Path(base) / name
                relative = str(path.relative_to(ROOT))
                if relative in ("evidence/inventory.json",
                                "evidence/inventory.sha256"):
                    continue
                info = path.lstat()
                row = {"path": relative, "uid": info.st_uid,
                       "mode": oct(stat.S_IMODE(info.st_mode))}
                if stat.S_ISREG(info.st_mode):
                    row.update(type="file", size=info.st_size,
                               sha256=file_hash(path))
                elif stat.S_ISLNK(info.st_mode):
                    row.update(type="symlink", target=os.readlink(path))
                elif stat.S_ISDIR(info.st_mode):
                    row.update(type="directory")
                else:
                    raise ValueError("unexpected inventory file type")
                inventory.append(row)
        save("inventory.json", inventory)
        digest = file_hash(evidence / "inventory.json")
        (evidence / "inventory.sha256").write_text(
            digest + "  inventory.json\n")

    print("STAGED_NOT_EXECUTED; cleanup requires separate authorization")

if __name__ == "__main__":
    need(sys.argv[1:] in (["--self-test"], ["--stage"]), "select explicit mode")
    if sys.argv[1] == "--self-test":
        synthetic_tests()
    else:
        stage()
PY