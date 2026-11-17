"""Source-entry regression against the actual pinned Codex checkout."""
import os
from pathlib import Path
import unittest

class EntryTest(unittest.TestCase):
    def test_protected_branch_precedes_all_generic_startup(self):
        root = Path(os.environ['PINNED_CODEX_SOURCE'])
        main = (root / 'codex-rs/app-server/src/main.rs').read_text()
        body = main.split('fn main() -> anyhow::Result<()> {', 1)[1]
        self.assertIn('symphony_gate2::try_run()', body)
        self.assertLess(body.index('symphony_gate2::try_run()'), body.index('take_remote_control_disabled_env'))
        self.assertLess(body.index('symphony_gate2::try_run()'), body.index('arg0_dispatch_or_else'))
        module = (root / 'codex-rs/app-server/src/symphony_gate2.rs').read_text()
        self.assertIn('F_GET_SEALS', module)
        self.assertIn('CLONE_THREAD', module)
        self.assertIn('SYMPHONY_HOST_UNQUALIFIED', module)
        self.assertNotIn('run_main_with_transport_options', module)
        self.assertNotIn('MessageProcessor::new', module)

    def test_bootstrap_has_explicit_real_holder_mode(self):
        guard = Path('native/pilot_c02/guard.c').read_text()
        self.assertIn('--pinned-codex', guard)
        self.assertIn('sealed_manifest', guard)
        self.assertIn('--symphony-pilot-holder', guard)

if __name__ == '__main__':
    unittest.main(verbosity=2)
