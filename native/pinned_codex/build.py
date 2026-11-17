"""Verify exact source bytes, apply the pinned patch, then compile offline.

Admission progresses through UPSTREAM_VERIFIED, PATCH_RECONSTRUCTED and
PATCHED_SOURCE_VERIFIED before compilation. Any mismatch stops without repair.
A failed application or build retains its checkout for inspection, never retry.
The source must remain exclusively owned by this local build while it runs.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import stat
import subprocess
import tempfile

# Do not inherit repository, worktree, index, object or configuration selectors.
# Cargo receives its normal build environment separately, with Git selectors
# removed too, because build scripts can invoke Git themselves.
GIT_ENV = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_CONFIG_COUNT': '0', 'GIT_TERMINAL_PROMPT': '0', 'GIT_NO_LAZY_FETCH': '1'}
GIT = ['/usr/bin/git', '--no-optional-locks', '--no-replace-objects',
       '-c', 'core.hooksPath=/dev/null', '-c', 'core.fsmonitor=false']


def git(source, *args, data=None, index=None):
    env = dict(GIT_ENV)
    if index is not None:
        env['GIT_INDEX_FILE'] = str(index)  # Only our private reconstruction index.
    return subprocess.check_output([*GIT, *args], cwd=source, env=env, input=data)


def bind_worktree(source):
    root = git(source, 'rev-parse', '--show-toplevel').rstrip(b'\n')
    if Path(os.fsdecode(root)).resolve(strict=True) != source:
        raise ValueError('Effective Git worktree differs from requested source')
    if source.resolve(strict=True) != source or not source.is_dir():
        raise ValueError('Requested source directory changed')


def tree_entries(source, tree):
    entries = {}
    for record in git(source, 'ls-tree', '-rz', '--full-tree', tree).split(b'\0')[:-1]:
        metadata, name = record.split(b'\t', 1)
        mode, kind, oid = metadata.split(b' ')
        path = PurePosixPath(os.fsdecode(name))
        if (kind != b'blob' or mode not in (b'100644', b'100755', b'120000')
                or path.is_absolute() or not path.parts
                or any(part in ('.', '..', '.git') for part in path.parts)
                or str(path) != os.fsdecode(name) or path in entries):
            raise ValueError('Unsupported source tree entry')
        entries[path] = (mode, oid.decode('ascii'))
    return entries


def stable(st):
    return (st.st_dev, st.st_ino, st.st_mode, st.st_size, st.st_mtime_ns,
            st.st_ctime_ns, st.st_uid, st.st_gid)


def verify_contents(source, entries):
    """Hash filesystem bytes, never index stat/cache/assume/skip observations."""
    observed = set()

    def scan(directory):
        with os.scandir(directory) as children:
            for child in children:
                if directory == source and child.name == '.git':
                    continue
                path = Path(child.path)
                if child.is_dir(follow_symlinks=False):
                    scan(path)
                else:
                    observed.add(PurePosixPath(path.relative_to(source)))
    scan(source)
    if observed != set(entries):
        raise ValueError('Unexpected or missing source files, including ignored files')
    for relative, (mode, oid) in entries.items():
        path = source / relative
        if path.parent.resolve(strict=True) != path.parent:
            raise ValueError('Source parent is redirected')
        before = path.lstat()
        if mode == b'120000' and stat.S_ISLNK(before.st_mode):
            data = os.readlink(os.fsencode(path))
        elif mode in (b'100644', b'100755') and stat.S_ISREG(before.st_mode):
            if bool(before.st_mode & stat.S_IXUSR) != (mode == b'100755'):
                raise ValueError('Source executable mode mismatch')
            fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
            with os.fdopen(fd, 'rb') as stream:
                if stable(os.fstat(stream.fileno())) != stable(before):
                    raise ValueError('Source changed before read')
                data = stream.read()
                if stable(os.fstat(stream.fileno())) != stable(before):
                    raise ValueError('Source changed during read')
        else:
            raise ValueError('Source entry type mismatch')
        if stable(path.lstat()) != stable(before):
            raise ValueError('Source changed during verification')
        blob = hashlib.sha1(b'blob ' + str(len(data)).encode() + b'\0' + data).hexdigest()
        if blob != oid:
            raise ValueError('Source content mismatch')


def prepare_source(source, pin, patch):
    bind_worktree(source)
    identity = git(source, 'rev-parse', 'HEAD', 'HEAD^{tree}').decode().splitlines()
    if identity != [pin['commit'], pin['tree']]:
        raise ValueError('Pinned upstream identity mismatch')
    git(source, 'diff', '--cached', '--no-ext-diff', '--no-textconv', '--quiet', pin['commit'], '--')
    verify_contents(source, tree_entries(source, pin['tree']))
    if hashlib.sha256(patch).hexdigest() != pin['patch_sha256']:
        raise ValueError('Pinned patch digest mismatch')
    # This disposable index constructs the expected tree without changing the
    # source index or any flags. It only adds ordinary Git objects to this local
    # checkout. Compare the resulting tree before touching source file bytes.
    with tempfile.TemporaryDirectory(prefix='pinned-codex-patch-index-') as scratch:
        index = Path(scratch) / 'index'
        git(source, 'read-tree', pin['tree'], index=index)
        git(source, 'apply', '--cached', '-', data=patch, index=index)
        patched_tree = git(source, 'write-tree', index=index).decode().strip()
    if patched_tree != pin['patched_tree']:
        raise ValueError('Pinned patched tree mismatch')
    patched_entries = tree_entries(source, patched_tree)
    bind_worktree(source)
    verify_contents(source, tree_entries(source, pin['tree']))
    git(source, 'apply', '--check', '-', data=patch)
    git(source, 'apply', '-', data=patch)
    bind_worktree(source)
    verify_contents(source, patched_entries)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--source', type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve(strict=True)
    here = Path(__file__).resolve().parent
    pin = json.loads((here / 'upstream.json').read_text())
    prepare_source(source, pin, (here / 'codex-0.162.1.patch').read_bytes())
    env = {key: value for key, value in os.environ.items() if not key.startswith('GIT_')}
    env.update({key: value for key, value in GIT_ENV.items() if key != 'PATH'})
    env.update(CARGO_INCREMENTAL='0', CARGO_BUILD_JOBS='1', CARGO_NET_OFFLINE='true')
    subprocess.run(['cargo', '+stable', '--config', 'profile.dev-small.package.sha2.opt-level=3',
                    'build', '--offline', '--locked', '--profile', 'dev-small', '-p', 'codex-app-server',
                    '--bin', 'codex-app-server', '-j', '1'], cwd=source / 'codex-rs', env=env, check=True)
    target = Path(env.get('CARGO_TARGET_DIR', source / 'codex-rs/target'))
    print(target / 'dev-small/codex-app-server')


if __name__ == '__main__':
    try:
        main()
    except (OSError, ValueError, KeyError, subprocess.CalledProcessError) as error:
        raise SystemExit('Pinned source/build refused: ' + str(error)) from error
