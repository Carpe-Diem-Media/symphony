"""Apply the reviewed pinned patch to a clean local checkout and build offline.

No source acquisition, installation, credentials or executable startup. Cargo's
normal local compilation uses the already retrieved, locked dependencies.
"""
import argparse
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
args = parser.parse_args()
source = args.source.resolve()
here = Path(__file__).resolve().parent
pin = json.loads((here / 'upstream.json').read_text())
env = dict(os.environ, GIT_CONFIG_NOSYSTEM='1', GIT_CONFIG_GLOBAL='/dev/null', GIT_TERMINAL_PROMPT='0',
           CARGO_INCREMENTAL='0', CARGO_BUILD_JOBS='1', CARGO_NET_OFFLINE='true')


def git(*argv):
    return subprocess.check_output(['/usr/bin/git', '-c', 'core.hooksPath=/dev/null', *argv], cwd=source, env=env).decode().strip()


if git('rev-parse', 'HEAD') != pin['commit'] or git('rev-parse', 'HEAD^{tree}') != pin['tree']:
    raise SystemExit('Pinned upstream identity mismatch')
if git('status', '--porcelain=v1'):
    raise SystemExit('Refusing non-clean checkout; no implicit reset or repair')
patch = str(here / 'codex-0.162.1.patch')
subprocess.run(['/usr/bin/git', 'apply', '--check', patch], cwd=source, env=env, check=True)
subprocess.run(['/usr/bin/git', 'apply', patch], cwd=source, env=env, check=True)
subprocess.run(['cargo', '+stable', '--config', 'profile.dev-small.package.sha2.opt-level=3',
                'build', '--offline', '--locked', '--profile', 'dev-small', '-p', 'codex-app-server',
                '--bin', 'codex-app-server', '-j', '1'], cwd=source / 'codex-rs', env=env, check=True)
print(source / 'codex-rs/target/dev-small/codex-app-server')
