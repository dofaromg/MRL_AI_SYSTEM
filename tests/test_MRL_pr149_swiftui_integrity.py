"""Regression cases shared by the absorption and hardening branches."""
import importlib.util
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
IMPORT = '5272acc107af4553e9f27b0a5dd2cbac7b26c827'
spec = importlib.util.spec_from_file_location('import_verifier', ROOT / 'scripts/MRL_pr149_swiftui_verify.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class ImportIntegrityTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.root = Path(directory.name)
        manifest = json.loads((ROOT / verifier.ORIGINAL_MANIFEST).read_bytes())
        self.assets = [e['path'] for e in manifest['files']]
        for path in [verifier.ORIGINAL_MANIFEST] + self.assets:
            target = self.root / path
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(subprocess.check_output(['git', '-C', str(ROOT), 'show', f'{IMPORT}:{path}']))
        if hasattr(verifier, 'git'):
            real_git = verifier.git
            git_patch = patch.object(verifier, 'git', side_effect=lambda _, *args: real_git(ROOT, *args))
            git_patch.start()
            self.addCleanup(git_patch.stop)

    def test_complete_original_inventory_passes(self):
        self.assertEqual(verifier.verify(self.root), (14, 0))

    def test_removing_asset_and_manifest_row_together_fails(self):
        path = self.root / verifier.ORIGINAL_MANIFEST
        manifest = json.loads(path.read_bytes())
        removed = manifest['files'].pop()
        (self.root / removed['path']).unlink()
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Original import manifest was changed'):
            verifier.verify(self.root)

    def test_replacing_a_path_without_changing_count_fails(self):
        path = self.root / verifier.ORIGINAL_MANIFEST
        manifest = json.loads(path.read_bytes())
        old = self.root / manifest['files'][0]['path']
        new = self.root / 'replacement.swift'
        old.rename(new)
        manifest['files'][0]['path'] = new.name
        path.write_text(json.dumps(manifest))
        with self.assertRaisesRegex(ValueError, 'Original import manifest was changed'):
            verifier.verify(self.root)

    def test_missing_asset_with_unchanged_manifest_fails(self):
        (self.root / self.assets[0]).unlink()
        with self.assertRaises(FileNotFoundError):
            verifier.verify(self.root)


if __name__ == '__main__':
    unittest.main()
