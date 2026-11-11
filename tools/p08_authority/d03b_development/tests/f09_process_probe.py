"""Finite disposable crash/concurrency probe. Never imported by host source."""
import json
import os
from pathlib import Path
import resource
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
resource.setrlimit(resource.RLIMIT_NOFILE, (64, 64))


def main():
    import contract as c
    import custody
    import ledger
    assert len(sys.argv) == 3
    mode = sys.argv[1]
    assert mode in {'before_reserve', 'after_reserve', 'after_prepare', 'after_commit', 'after_ack', 'consume'}
    path = Path(sys.argv[2])
    assert path.resolve(strict=True) == path and path.is_relative_to(ROOT / 'scratch')
    value = c.parse_json(path.read_bytes())
    assert set(value) == {'root', 'pin', 'bindings', 'attempt'}
    root = Path(value['root'])
    assert root.resolve(strict=True) == root and root.is_relative_to(ROOT / 'scratch')
    # These are synthetic component inputs, never operational trust selection.
    a = custody._HostCustody(root, value['pin'], value['bindings'])
    with ledger._RegisterStore(root / 'state/register.sqlite3', a) as reg:
        if mode == 'before_reserve':
            a.reserve = lambda *_: os._exit(71)
        elif mode == 'after_reserve':
            original = a.reserve
            def reserve(*args): original(*args); os._exit(72)
            a.reserve = reserve
        elif mode == 'after_prepare':
            original = a.prepare
            def prepare(*args): original(*args); os._exit(73)
            a.prepare = prepare
        elif mode == 'after_commit':
            a.complete = lambda *_: os._exit(74)
        elif mode == 'after_ack':
            original = a.complete
            def complete(*args): original(*args); os._exit(75)
            a.complete = complete
        reg.consume(value['attempt'])
        print(json.dumps({'pid': os.getpid(), 'state': reg.get(value['attempt'])['state']}))


if __name__ == '__main__':
    try: main()
    except Exception as error:
        print(type(error).__name__ + ':' + str(error), file=sys.stderr)
        raise SystemExit(2)
