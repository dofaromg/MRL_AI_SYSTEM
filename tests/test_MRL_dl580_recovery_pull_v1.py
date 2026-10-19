"""
test_MRL_dl580_recovery_pull_v1.py — Issue #146 資料回收腳本離線測試（不連網、不呼叫真 rclone/git）
origin_signature: MrLiouWord
"""
from __future__ import annotations

import importlib.util
import json
import re
import pathlib
import subprocess
import tempfile
import unittest

_SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "scripts" / "MRL_dl580_recovery_pull_v1.py"
_spec = importlib.util.spec_from_file_location("MRL_dl580_recovery_pull_v1", _SCRIPT)
mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(mod)

_EXAMPLE = _SCRIPT.parent / "MRL_dl580_recovery_plan.example.json"


SHA = "a" * 40


class FakeRunner:
    def __init__(self, rc=0, raise_timeout=False):
        self.calls, self.rc, self.raise_timeout = [], rc, raise_timeout

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        if self.raise_timeout:
            raise subprocess.TimeoutExpired(cmd, kw.get("timeout") or 1)
        out = f"{SHA}\tHEAD\n" if "ls-remote" in cmd else ""
        return subprocess.CompletedProcess(cmd, self.rc, stdout=out, stderr="boom" if self.rc else "")


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

    def test_git_new_revision_gets_its_own_directory_and_old_is_untouched(self):
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "repo"
            (dst / "oldrev00000" / ".git").mkdir(parents=True)  # 先前已拉過的舊修訂
            r = FakeRunner()
            ok, _ = mod.pull_git({"url": "https://x/y.git"}, dst, r, 10)
            self.assertTrue(ok)
            cloned = [c for c in r.calls if c[:2] == ["git", "clone"]]
            self.assertEqual(len(cloned), 1)
            self.assertTrue(cloned[0][-1].endswith(SHA[:12]))
            self.assertTrue((dst / "oldrev00000" / ".git").exists())
            # 同一修訂第二次：不再 clone
            (dst / SHA[:12] / ".git").mkdir(parents=True)
            r2 = FakeRunner()
            self.assertTrue(mod.pull_git({"url": "https://x/y.git"}, dst, r2, 10)[0])
            self.assertFalse([c for c in r2.calls if c[:2] == ["git", "clone"]])

    def test_git_bad_remote_head_fails(self):
        class NoHead(FakeRunner):
            def __call__(self, cmd, **kw):
                self.calls.append(cmd)
                return subprocess.CompletedProcess(cmd, 0, stdout="", stderr="")
        with tempfile.TemporaryDirectory() as td:
            ok, err = mod.pull_git({"url": "https://x/y.git"}, pathlib.Path(td) / "r", NoHead(), 10)
        self.assertFalse(ok)
        self.assertIn("HEAD", err)

    def test_timeout_is_recorded_as_source_failure(self):
        with tempfile.TemporaryDirectory() as td:
            res = mod.pull([{"name": "a", "kind": "rclone", "remote": "dropbox:"}, 
                            {"name": "b", "kind": "git", "url": "https://x/y.git"}],
                           pathlib.Path(td), runner=FakeRunner(raise_timeout=True), timeout=5)
        self.assertFalse(res["a"]["ok"])
        self.assertIn("逾時", res["a"]["error"])
        self.assertFalse(res["b"]["ok"])  # 一個逾時不影響後面的來源繼續被嘗試

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
            (out / "repo" / "abc123def456" / ".git").mkdir(parents=True)
            (out / "repo" / "abc123def456" / "__init__.py").write_bytes(b"")
            (out / "repo" / "abc123def456" / ".git" / "config").write_text("x", encoding="utf-8")
            rows = mod.build_manifest(out, git_sources={"repo"}, runner=FakeRunner(rc=1))
            self.assertFalse([r for r in rows if r.get("zero_byte")])
            self.assertFalse([r for r in rows if ".git/" in r.get("path", "")])  # git 來源不逐檔雜湊 .git

    def test_dot_git_inside_rclone_source_is_hashed_as_data(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            (out / "cloud" / "proj" / ".git").mkdir(parents=True)
            (out / "cloud" / "proj" / ".git" / "config").write_text("data", encoding="utf-8")
            rows = mod.build_manifest(out, git_sources=set())
            self.assertIn("proj/.git/config", {r["path"] for r in rows})

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

    def test_verify_rejects_tampered_or_unlisted_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            out = self._store(td)
            m = mod.write_manifest(out, mod.build_manifest(out))
            # 刪掉清單裡的一列但仍是合法 JSONL → 雜湊不符必須被抓到
            lines = m.read_text(encoding="utf-8").splitlines()
            m.write_text("\n".join(lines[:-1]) + "\n", encoding="utf-8")
            res = mod.verify(out)
            self.assertFalse(res["ok"])
            self.assertIn("清單雜湊不符", res["error"])
        with tempfile.TemporaryDirectory() as td:
            out = self._store(td)
            mod.write_manifest(out, mod.build_manifest(out))
            (out / "SHA256SUMS").unlink()
            self.assertIn("缺少清單記錄", mod.verify(out)["error"])

    def test_verify_without_manifest_fails(self):
        with tempfile.TemporaryDirectory() as td:
            self.assertFalse(mod.verify(pathlib.Path(td))["ok"])


class CliTests(unittest.TestCase):
    def _plan(self, td, sources):
        p = pathlib.Path(td) / "plan.json"
        p.write_text(json.dumps({"sources": sources}), encoding="utf-8")
        return p

    def test_empty_source_is_not_success_unless_allowed(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            plan = self._plan(td, [{"name": "a", "kind": "rclone", "remote": "dropbox:"}])
            out = pathlib.Path(td) / "store"
            with mock.patch.object(mod.shutil, "which", return_value="/usr/bin/rclone"), \
                 mock.patch.object(mod.subprocess, "run", side_effect=lambda c, **k: subprocess.CompletedProcess(c, 0, "", "")):
                self.assertEqual(mod.main(["pull", "--plan", str(plan), "--out", str(out)]), 3)
                self.assertEqual(mod.main(["pull", "--plan", str(plan), "--out", str(out), "--allow-empty"]), 0)

    def test_zero_byte_needs_acknowledgement(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            plan = self._plan(td, [{"name": "a", "kind": "rclone", "remote": "dropbox:"}])
            out = pathlib.Path(td) / "store"
            (out / "a").mkdir(parents=True)
            (out / "a" / "empty.md").write_bytes(b"")
            (out / "a" / "real.md").write_text("x", encoding="utf-8")
            with mock.patch.object(mod.shutil, "which", return_value="/usr/bin/rclone"), \
                 mock.patch.object(mod.subprocess, "run", side_effect=lambda c, **k: subprocess.CompletedProcess(c, 0, "", "")):
                self.assertEqual(mod.main(["pull", "--plan", str(plan), "--out", str(out)]), 4)
                self.assertEqual(mod.main(["pull", "--plan", str(plan), "--out", str(out), "--accept-zero-byte"]), 0)


if __name__ == "__main__":
    unittest.main()
