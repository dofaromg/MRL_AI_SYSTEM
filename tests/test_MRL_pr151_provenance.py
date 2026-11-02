import ast
import fnmatch
import importlib.util
import json
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('verifier', ROOT / 'scripts/MRL_pr149_swiftui_verify.py')
verifier = importlib.util.module_from_spec(spec)
spec.loader.exec_module(verifier)


class ProvenanceTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)
        original = json.loads((ROOT / verifier.ORIGINAL_MANIFEST).read_bytes())
        for name in [verifier.ORIGINAL_MANIFEST, verifier.HARDENING_MANIFEST] + [e['path'] for e in original['files']]:
            target = self.root / name
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(ROOT / name, target)
        real_git = verifier.git
        self.git_patch = patch.object(verifier, 'git', side_effect=lambda _, *args: real_git(ROOT, *args))
        self.git_patch.start()
        self.addCleanup(self.git_patch.stop)

    def change_extension(self, change):
        path = self.root / verifier.HARDENING_MANIFEST
        manifest = json.loads(path.read_bytes())
        change(manifest)
        path.write_text(json.dumps(manifest))

    def test_baseline_and_explicit_derivatives(self):
        self.assertEqual(verifier.verify(self.root), (14, 3))

    def test_undeclared_asset_mutation_fails(self):
        path = self.root / 'MRL_Reference_Layer/MRL_SwiftUI_NavigationCookbook_Reference_v1.md'
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'Working asset mismatch'):
            verifier.verify(self.root)

    def test_derived_asset_mutation_fails(self):
        path = self.root / sorted(verifier.DERIVED_PATHS)[0]
        path.write_bytes(path.read_bytes() + b'changed')
        with self.assertRaisesRegex(ValueError, 'Working asset mismatch'):
            verifier.verify(self.root)

    def test_parent_lineage_mutation_fails(self):
        self.change_extension(lambda m: m['files'][0]['original'].update(source_blob='0' * 40))
        with self.assertRaisesRegex(ValueError, 'Lineage mismatch'):
            verifier.verify(self.root)

    def test_extra_derivative_fails(self):
        self.change_extension(lambda m: m['files'].append({'path': 'unrelated.swift'}))
        with self.assertRaisesRegex(ValueError, 'Only the three'):
            verifier.verify(self.root)

    def test_duplicate_derivative_fails(self):
        self.change_extension(lambda m: m['files'].append(m['files'][0]))
        with self.assertRaisesRegex(ValueError, 'Only the three'):
            verifier.verify(self.root)

    def test_missing_declaration_fails(self):
        (self.root / verifier.HARDENING_MANIFEST).unlink()
        with self.assertRaisesRegex(ValueError, 'Working asset mismatch'):
            verifier.verify(self.root)

    def test_original_manifest_is_immutable(self):
        path = self.root / verifier.ORIGINAL_MANIFEST
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'Original import manifest was changed'):
            verifier.verify(self.root)

    def test_every_original_asset_triggers_integrity_workflow(self):
        workflow = (ROOT / '.github/workflows/MRL_PR149_SwiftUI.yml').read_text()
        line = next(line for line in workflow.splitlines() if line.strip().startswith('paths:'))
        patterns = ast.literal_eval(line.split('paths:', 1)[1].strip())
        manifest = json.loads((ROOT / verifier.ORIGINAL_MANIFEST).read_bytes())
        for entry in manifest['files']:
            self.assertTrue(any(fnmatch.fnmatchcase(entry['path'], p) for p in patterns), entry['path'])


if __name__ == '__main__':
    unittest.main()
