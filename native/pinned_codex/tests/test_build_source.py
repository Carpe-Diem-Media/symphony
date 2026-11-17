"""Offline admission regressions using disposable Git repositories and a build marker.

The marker replaces Cargo only in these fixture copies. Actual compilation and
holder execution are separate checks against the pinned real Codex source.
Run unchanged against the parent script to reproduce false admission.
"""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import subprocess
import tempfile
import unittest
from unittest.mock import patch

BUILD = Path(__file__).resolve().parents[1] / 'build.py'
GIT_ENV = {'PATH': '/usr/bin:/bin', 'LC_ALL': 'C', 'GIT_CONFIG_NOSYSTEM': '1',
           'GIT_CONFIG_SYSTEM': '/dev/null', 'GIT_CONFIG_GLOBAL': '/dev/null',
           'GIT_CONFIG_COUNT': '0', 'GIT_TERMINAL_PROMPT': '0'}


def git(root, *args, env=None):
    return subprocess.check_output(['/usr/bin/git', '-c', 'core.hooksPath=/dev/null',
                                    '-C', str(root), *args], env=env or GIT_ENV,
                                   stderr=subprocess.PIPE)


class BuildSourceTest(unittest.TestCase):
    def setUp(self):
        self.scratch = tempfile.TemporaryDirectory(prefix='codex-build-source-')
        self.addCleanup(self.scratch.cleanup)
        self.root = Path(self.scratch.name).resolve()
        self.repo = self.root / 'source'
        self.repo.mkdir()
        git(self.repo, 'init', '-q')
        git(self.repo, 'config', 'user.name', 'Offline Fixture')
        git(self.repo, 'config', 'user.email', 'fixture@invalid')
        (self.repo / 'codex-rs').mkdir()
        (self.repo / 'codex-rs/main.rs').write_text('before\n')
        (self.repo / 'tracked.txt').write_text('approved\n')
        (self.repo / 'link').symlink_to('tracked.txt')
        git(self.repo, 'add', '.')
        git(self.repo, 'commit', '-qm', 'base')
        commit = git(self.repo, 'rev-parse', 'HEAD').decode().strip()
        tree = git(self.repo, 'rev-parse', 'HEAD^{tree}').decode().strip()
        (self.repo / 'codex-rs/main.rs').write_text('after\n')
        (self.repo / 'codex-rs/added.rs').write_text('added\n')
        git(self.repo, 'add', '.')
        patch = git(self.repo, 'diff', '--cached', '--binary')
        patched_tree = git(self.repo, 'write-tree').decode().strip()
        git(self.repo, 'commit', '-qm', 'patch fixture')
        git(self.repo, 'checkout', '-q', '--detach', commit)
        self.pin = dict(commit=commit, tree=tree, patched_tree=patched_tree,
                        patch_sha256=hashlib.sha256(patch).hexdigest())
        self.tool = self.root / 'tool'
        self.tool.mkdir()
        shutil.copy2(BUILD, self.tool / 'build.py')
        (self.tool / 'codex-0.162.1.patch').write_bytes(patch)
        self.write_pin()
        self.bin = self.root / 'bin'
        self.bin.mkdir()
        cargo = self.bin / 'cargo'
        cargo.write_text('#!/bin/sh\nprintf "BUILD_REACHED\\n"\n')
        cargo.chmod(0o755)
        self.env = dict(GIT_ENV, PATH=str(self.bin) + ':/usr/bin:/bin')

    def write_pin(self):
        (self.tool / 'upstream.json').write_text(json.dumps(self.pin))

    def run_build(self, extra=None, source=None):
        env = dict(self.env, **(extra or {}))
        return subprocess.run(['/usr/bin/python3', '-I', str(self.tool / 'build.py'),
                               '--source', str(source or self.repo)], env=env,
                              capture_output=True, text=True, timeout=15)

    def refused(self, result):
        self.assertNotEqual(result.returncode, 0, result.stdout + result.stderr)
        self.assertNotIn('BUILD_REACHED', result.stdout + result.stderr)

    def other_clean_repo(self):
        other = self.root / 'other'
        subprocess.run(['/usr/bin/git', 'clone', '-q', '--no-hardlinks', str(self.repo), str(other)],
                       env=GIT_ENV, check=True, capture_output=True)
        return other

    def test_valid_checkout_passes_and_source_index_is_unchanged(self):
        index = (self.repo / '.git/index').read_bytes()
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('BUILD_REACHED', result.stdout)
        self.assertEqual(index, (self.repo / '.git/index').read_bytes())
        self.assertEqual((self.repo / 'codex-rs/added.rs').read_text(), 'added\n')

    def test_dirty_tracked_file_refuses(self):
        (self.repo / 'tracked.txt').write_text('unapproved\n')
        self.refused(self.run_build())

    def test_untracked_file_refuses(self):
        (self.repo / 'untracked').write_text('unapproved\n')
        self.refused(self.run_build())

    def test_ignored_untracked_file_refuses(self):
        (self.repo / '.git/info/exclude').write_text('hidden\n')
        (self.repo / 'hidden').write_text('unapproved\n')
        self.refused(self.run_build())

    def test_git_dir_and_work_tree_redirection_refuses(self):
        other = self.other_clean_repo()
        (self.repo / 'tracked.txt').write_text('unapproved\n')
        self.refused(self.run_build({'GIT_DIR': str(other / '.git'), 'GIT_WORK_TREE': str(other)}))
        self.assertEqual((other / 'codex-rs/main.rs').read_text(), 'before\n')

    def test_core_worktree_redirection_refuses(self):
        other = self.other_clean_repo()
        git(self.repo, 'config', 'core.worktree', str(other))
        (self.repo / 'tracked.txt').write_text('unapproved\n')
        self.refused(self.run_build())

    def test_assume_unchanged_cannot_hide_modified_bytes(self):
        git(self.repo, 'update-index', '--assume-unchanged', 'tracked.txt')
        (self.repo / 'tracked.txt').write_text('unapproved\n')
        self.assertEqual(git(self.repo, 'status', '--porcelain=v1'), b'')
        self.refused(self.run_build())

    def test_skip_worktree_cannot_hide_modified_bytes(self):
        git(self.repo, 'update-index', '--skip-worktree', 'tracked.txt')
        (self.repo / 'tracked.txt').write_text('unapproved\n')
        self.assertEqual(git(self.repo, 'status', '--porcelain=v1'), b'')
        self.refused(self.run_build())

    def test_index_and_config_environment_cannot_hide_changes(self):
        other = self.other_clean_repo()
        (self.repo / 'tracked.txt').write_text('unapproved\n')
        self.refused(self.run_build({'GIT_INDEX_FILE': str(other / '.git/index'),
                                    'GIT_CONFIG_COUNT': '1', 'GIT_CONFIG_KEY_0': 'core.worktree',
                                    'GIT_CONFIG_VALUE_0': str(other)}))

    def test_environment_config_is_isolated_for_valid_checkout(self):
        self.env.update(GIT_CONFIG_COUNT='1', GIT_CONFIG_KEY_0='core.worktree',
                        GIT_CONFIG_VALUE_0=str(self.root / 'missing'),
                        GIT_CONFIG_PARAMETERS="'core.worktree=/missing'",
                        GIT_OBJECT_DIRECTORY='/missing', GIT_COMMON_DIR='/missing')
        result = self.run_build()
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_path_substituted_git_cannot_fabricate_clean_source(self):
        fake = self.bin / 'git'
        marker = self.root / 'fake-git-calls'
        fake.write_text('#!/usr/bin/python3\nimport sys\nfrom pathlib import Path\n'
                        + 'with Path(' + repr(str(marker)) + ').open("a") as out: out.write("called\\n")\n'
                        + 'identities=' + repr({'HEAD': self.pin['commit'],
                                                'HEAD^{tree}': self.pin['tree']}) + '\n'
                        + 'if "rev-parse" in sys.argv:\n'
                        + ' for arg in sys.argv:\n'
                        + '  if arg in identities: print(identities[arg])\n')
        fake.chmod(0o755)
        (self.repo / 'tracked.txt').write_text('unapproved\n')
        fabricated = subprocess.check_output([str(fake), 'rev-parse', 'HEAD', 'HEAD^{tree}'])
        self.assertEqual(fabricated.decode().splitlines(), [self.pin['commit'], self.pin['tree']])
        self.assertEqual(subprocess.check_output([str(fake), 'status', '--porcelain=v1']), b'')
        calls = marker.read_bytes()
        self.refused(self.run_build())
        self.assertEqual(marker.read_bytes(), calls, 'Admission must never invoke PATH Git')

    def test_executable_mode_change_refuses_even_with_core_filemode_false(self):
        git(self.repo, 'config', 'core.filemode', 'false')
        (self.repo / 'tracked.txt').chmod(0o755)
        self.refused(self.run_build())

    def test_tracked_file_type_change_refuses(self):
        (self.repo / 'tracked.txt').unlink()
        (self.repo / 'tracked.txt').symlink_to('codex-rs/main.rs')
        self.refused(self.run_build())

    def test_changed_symlink_target_refuses(self):
        (self.repo / 'link').unlink()
        (self.repo / 'link').symlink_to('codex-rs/main.rs')
        self.refused(self.run_build())

    def test_missing_tracked_file_refuses(self):
        (self.repo / 'tracked.txt').unlink()
        self.refused(self.run_build())

    def test_wrong_patch_digest_refuses_before_mutation(self):
        with (self.tool / 'codex-0.162.1.patch').open('ab') as f:
            f.write(b'\n')
        self.refused(self.run_build())
        self.assertEqual((self.repo / 'codex-rs/main.rs').read_text(), 'before\n')

    def test_wrong_patched_tree_refuses_before_mutation(self):
        self.pin['patched_tree'] = '0' * 40
        self.write_pin()
        self.refused(self.run_build())
        self.assertEqual((self.repo / 'codex-rs/main.rs').read_text(), 'before\n')

    def test_gitlink_source_entry_refuses(self):
        git(self.repo, 'update-index', '--add', '--cacheinfo',
            '160000,' + self.pin['commit'] + ',submodule')
        git(self.repo, 'commit', '-qm', 'unsupported gitlink fixture')
        self.pin['commit'] = git(self.repo, 'rev-parse', 'HEAD').decode().strip()
        self.pin['tree'] = git(self.repo, 'rev-parse', 'HEAD^{tree}').decode().strip()
        self.write_pin()
        self.refused(self.run_build())
        self.assertEqual((self.repo / 'codex-rs/main.rs').read_text(), 'before\n')

    def test_unreadable_tracked_file_refuses(self):
        path = self.repo / 'tracked.txt'
        path.chmod(0)
        self.addCleanup(path.chmod, 0o644)
        self.refused(self.run_build())

    def test_actual_postpatch_bytes_are_checked_before_build(self):
        # Simulate a concurrent modification immediately after real Git applies
        # the patch. All Git operations themselves still use the real binary.
        spec = importlib.util.spec_from_file_location('pinned_build', self.tool / 'build.py')
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        original = module.git

        def tamper_after_apply(source, *args, **kwargs):
            result = original(source, *args, **kwargs)
            if args == ('apply', '-'):
                (source / 'codex-rs/added.rs').write_text('unapproved after apply\n')
            return result

        with patch.object(module, 'git', side_effect=tamper_after_apply):
            with self.assertRaisesRegex(ValueError, 'Source content mismatch'):
                module.prepare_source(self.repo, self.pin,
                                      (self.tool / 'codex-0.162.1.patch').read_bytes())

    def test_ordinary_linked_worktree_passes(self):
        linked = self.root / 'linked'
        git(self.repo, 'worktree', 'add', '-q', '--detach', str(linked), self.pin['commit'])
        result = self.run_build(source=linked)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn('BUILD_REACHED', result.stdout)


if __name__ == '__main__':
    unittest.main(verbosity=2)
