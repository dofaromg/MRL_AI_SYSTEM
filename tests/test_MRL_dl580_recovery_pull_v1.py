"""
test_MRL_dl580_recovery_pull_v1.py — Issue #146 資料回收腳本離線測試（不連網、不呼叫真 rclone/git）
origin_signature: MrLiouWord
"""
from __future__ import annotations

import importlib.util
import json
import pathlib
import subprocess
import tempfile
import unittest

_SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "MRL_dl580_recovery_pull_v1.py"
_spec = importlib.util.spec_from_file_location("MRL_dl580_recovery_pull_v1", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

_EXAMPLE = _SCRIPT.parent / "MRL_dl580_recovery_plan.example.json"


class FakeRunner:
    def __init__(self, rc=0):
        self.calls, self.rc = [], rc

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        return subprocess.CompletedProcess(cmd, self.rc, stdout="", stderr="boom" if self.rc else "")


class PlanTests(unittest.TestCase):
    def test_example_plan_is_valid(self):
        self.assertGreaterEqual(len(mod.load_plan(_EXAMPLE)), 4)

    def test_rejects_bad_plans(self):
        with tempfile.TemporaryDirectory() as td:
            def load(obj):
                p = pathlib.Path(td) / "p.json"
                p.write_text(json.dumps(obj), encoding="utf-8")
                return mod.load_plan(p)
            for bad in ({"sources": []},
                        {"sources": [{"name": "../x", "kind": "git", "url": "https://a/b"}]},
                        {"sources": [{"name": "a", "kind": "git", "url": "http://a/b"}]},
                        {"sources": [{"name": "a", "kind": "rclone", "remote": "dropbox"}]},
                        {"sources": [{"name": "a", "kind": "ftp"}]},
                        {"sources": [{"name": "a", "kind": "git", "url": "https://a/b"},
                                     {"name": "a", "kind": "git", "url": "https://a/c"}]}):
                with self.assertRaises(ValueError):
                    load(bad)


class SafetyTests(unittest.TestCase):
    def test_synced_folders_refused(self):
        self.assertTrue(mod.is_synced_path(pathlib.Path("/home/u/Dropbox/recovery")))
        self.assertTrue(mod.is_synced_path(pathlib.Path("C:/Users/u/OneDrive/x")))
        self.assertFalse(mod.is_synced_path(pathlib.Path("/data/mrl/recovery")))

    def test_commands_are_additive_only(self):
        r = FakeRunner()
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            mod.pull(mod.load_plan(_EXAMPLE), out, runner=r)
        flat = [" ".join(c) for c in r.calls]
        self.assertTrue(any("rclone copy" in c and "--immutable" in c for c in flat))
        for c in flat:
            for banned in ("sync", "move", "delete", "purge", "--force", "reset", " rm "):
                self.assertNotIn(banned, c)

    def test_git_existing_repo_uses_fetch(self):
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "repo"
            (dst / ".git").mkdir(parents=True)
            cmds = mod.build_commands({"name": "repo", "kind": "git", "url": "https://x/y.git"}, dst)
        self.assertEqual(cmds[0][3], "fetch")

    def test_failed_command_is_reported(self):
        with tempfile.TemporaryDirectory() as td:
            res = mod.pull([{"name": "a", "kind": "rclone", "remote": "dropbox:"}],
                           pathlib.Path(td), runner=FakeRunner(rc=1))
        self.assertFalse(res["a"]["ok"])
        self.assertIn("boom", res["a"]["error"])


class ManifestTests(unittest.TestCase):
    def _store(self, td):
        out = pathlib.Path(td)
        (out / "src1" / "sub").mkdir(parents=True)
        (out / "src1" / "a.txt").write_text("hello", encoding="utf-8")
        (out / "src1" / "sub" / "b.txt").write_text("world", encoding="utf-8")
        (out / "src1" / "empty.md").write_bytes(b"")
        return out

    def test_manifest_flags_zero_byte_and_hashes(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._store(td)
            rows = mod.build_manifest(out)
            by = {r["path"]: r for r in rows}
            self.assertTrue(by["empty.md"]["zero_byte"])
            self.assertFalse(by["a.txt"]["zero_byte"])
            self.assertEqual(by["a.txt"]["sha256"], mod.hashlib.sha256(b"hello").hexdigest())

    def test_empty_files_inside_git_repo_are_not_flagged(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            (out / "repo" / ".git").mkdir(parents=True)
            (out / "repo" / "__init__.py").write_bytes(b"")
            rows = mod.build_manifest(out, runner=FakeRunner(rc=1))
            self.assertFalse([r for r in rows if r.get("zero_byte")])

    def test_manifest_never_overwrites_and_sums_append(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._store(td)
            rows = mod.build_manifest(out)
            first = mod.write_manifest(out, rows)
            second = mod.write_manifest(out, rows)
            self.assertNotEqual(first, second)
            self.assertEqual(len((out / "SHA256SUMS").read_text(encoding="utf-8").splitlines()), 2)

    def test_verify_detects_change_and_missing_but_allows_new(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._store(td)
            mod.write_manifest(out, mod.build_manifest(out))
            self.assertTrue(mod.verify(out)["ok"])
            (out / "src1" / "new.txt").write_text("added later", encoding="utf-8")
            self.assertTrue(mod.verify(out)["ok"])  # 只新增不算異動
            (out / "src1" / "a.txt").write_text("tampered", encoding="utf-8")
            (out / "src1" / "sub" / "b.txt").unlink()
            res = mod.verify(out)
            self.assertFalse(res["ok"])
            self.assertEqual(res["changed"], ["src1/a.txt"])
            self.assertEqual(res["missing"], ["src1/sub/b.txt"])

    def test_verify_without_manifest_fails(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(mod.verify(pathlib.Path(td))["ok"])


if __name__ == "__main__":
    unittest.main()
