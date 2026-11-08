"""
test_MRL_dl580_recovery_pull_v1.py — Issue #146 資料回收腳本離線測試（不連網、不呼叫真 rclone/git）
origin_signature: MrLiouWord
"""
from __future__ import annotations

import importlib.util
import json
import os
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
    """模擬 rclone／git。fail_on：指令中含此子字串時回傳失敗（例如 "checkout"）。
    git clone 成功時會建立含 .git 的目錄，行為和真的 git 一致。"""

    def __init__(self, rc=0, raise_timeout=False, fail_on=None):
        self.calls, self.kws, self.rc, self.raise_timeout, self.fail_on = [], [], rc, raise_timeout, fail_on

    def __call__(self, cmd, **kw):
        self.calls.append(cmd)
        self.kws.append(kw)
        if self.raise_timeout:
            raise subprocess.TimeoutExpired(cmd, kw.get("timeout") or 1)
        rc = self.rc
        if self.fail_on and self.fail_on in cmd:
            rc = 1
        if rc == 0 and cmd[:2] == ["git", "clone"]:
            if "--mirror" in cmd:  # 裸倉庫：HEAD、objects，沒有 .git 也沒有工作樹
                (pathlib.Path(cmd[-1]) / "objects").mkdir(parents=True)
                (pathlib.Path(cmd[-1]) / "HEAD").write_text("ref: refs/heads/main\n", encoding="utf-8")
            else:
                (pathlib.Path(cmd[-1]) / ".git").mkdir(parents=True)
                (pathlib.Path(cmd[-1]) / "file.txt").write_text("x", encoding="utf-8")
        out = f"{SHA}\tHEAD\n" if "ls-remote" in cmd else ""
        err = getattr(self, "stderr", None) or ("boom" if rc else "")
        return subprocess.CompletedProcess(cmd, rc, stdout=out, stderr=err if rc else "")


class PlanTests(unittest.TestCase):
    def test_example_plan_is_valid(self):
        self.assertGreaterEqual(len(mod.load_plan(_EXAMPLE)), 4)

    def test_plan_with_utf8_bom_loads(self):
        with tempfile.TemporaryDirectory() as td:
            p = pathlib.Path(td) / "p.json"
            p.write_bytes(b"\xef\xbb\xbf" + json.dumps(
                {"sources": [{"name": "a", "kind": "git", "url": "https://a/b"}]}).encode("utf-8"))
            self.assertEqual(mod.load_plan(p)[0]["name"], "a")

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
            self.assertTrue(cloned[0][-1].endswith(mod.PARTIAL_PREFIX + SHA[:12]))
            self.assertTrue((dst / SHA[:12] / ".git").is_dir())
            self.assertFalse((dst / (mod.PARTIAL_PREFIX + SHA[:12])).exists())
            self.assertTrue((dst / "oldrev00000" / ".git").exists())
            # 同一修訂第二次：不再 clone
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


class StabilityTests(unittest.TestCase):
    def test_failed_checkout_leaves_no_complete_looking_directory(self):
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "repo"
            ok, _ = mod.pull_git({"url": "https://x/y.git"}, dst, FakeRunner(fail_on="checkout"), 10)
            self.assertFalse(ok)
            self.assertFalse((dst / SHA[:12]).exists())
            self.assertFalse((dst / (mod.PARTIAL_PREFIX + SHA[:12])).exists())
            # 下次重跑不會把殘骸當成已完成而跳過
            r = FakeRunner()
            self.assertTrue(mod.pull_git({"url": "https://x/y.git"}, dst, r, 10)[0])
            self.assertTrue([c for c in r.calls if c[:2] == ["git", "clone"]])
            self.assertTrue((dst / SHA[:12] / "file.txt").is_file())

    def test_stale_partial_from_crashed_run_is_replaced(self):
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "repo"
            stale = dst / (mod.PARTIAL_PREFIX + SHA[:12])
            (stale / ".git").mkdir(parents=True)
            self.assertTrue(mod.pull_git({"url": "https://x/y.git"}, dst, FakeRunner(), 10)[0])
            self.assertTrue((dst / SHA[:12]).is_dir())
            self.assertFalse(stale.exists())

    def test_git_never_prompts_for_credentials(self):
        with tempfile.TemporaryDirectory() as td:
            r = FakeRunner()
            mod.pull_git({"url": "https://x/y.git"}, pathlib.Path(td) / "repo", r, 10)
            self.assertTrue(r.kws)
            for kw in r.kws:
                self.assertEqual(kw["env"]["GIT_TERMINAL_PROMPT"], "0")

    def test_rclone_retries_and_user_args_can_override(self):
        cmd = mod.rclone_command({"remote": "d:", "path": "p", "extra_args": ["--retries", "9"]}, pathlib.Path("/x"))
        self.assertIn("--low-level-retries", cmd)
        self.assertLess(cmd.index("--retries"), len(cmd) - cmd[::-1].index("--retries") - 1)  # 預設在前
        self.assertEqual(cmd[-1], "9")  # 使用者參數在最後，可覆寫預設

    def test_partial_dirs_are_not_part_of_the_manifest(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            (out / "repo" / (mod.PARTIAL_PREFIX + "abc") / ".git").mkdir(parents=True)
            (out / "repo" / (mod.PARTIAL_PREFIX + "abc") / "half.txt").write_text("x", encoding="utf-8")
            (out / "repo" / "def456def456" / ".git").mkdir(parents=True)
            (out / "repo" / "def456def456" / "ok.txt").write_text("y", encoding="utf-8")
            rows = mod.build_manifest(out, git_sources={"repo"}, runner=FakeRunner(rc=1))
            paths = [r["path"] for r in rows]
            self.assertIn("def456def456/ok.txt", paths)
            self.assertFalse([p for p in paths if "half.txt" in p or "abc" in p])

    def test_lock_blocks_second_pull_and_is_released(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            with mod.pull_lock(out):
                with self.assertRaises(mod.PullLockHeld):
                    with mod.pull_lock(out):
                        pass
                self.assertTrue((out / mod.LOCK_NAME).exists())  # 第二把鎖失敗不可誤刪第一把
            self.assertFalse((out / mod.LOCK_NAME).exists())
            with mod.pull_lock(out):  # 釋放後可再取得
                pass

    def test_lock_released_even_when_pull_raises(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            with self.assertRaises(RuntimeError):
                with mod.pull_lock(out):
                    raise RuntimeError("boom")
            self.assertFalse((out / mod.LOCK_NAME).exists())

    def test_manifest_without_hardlink_support_falls_back_to_copy(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            (out / "a").mkdir()
            (out / "a" / "f.txt").write_text("hi", encoding="utf-8")
            with mock.patch.object(mod.os, "link", side_effect=OSError("no hardlinks")):
                m = mod.write_manifest(out, mod.build_manifest(out))
            self.assertTrue(m.is_file())
            self.assertTrue(mod.verify(out)["ok"])
            self.assertEqual([p.name for p in out.glob(".MANIFEST_tmp.*")], [])  # 暫存檔已清掉

    def test_crash_between_sums_and_manifest_leaves_verifiable_store(self):
        """模擬斷電：SHA256SUMS 已有一筆孤立記錄、清單檔不存在 → 既有資料仍可驗證，且孤立記錄被標出。"""
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            (out / "a").mkdir()
            (out / "a" / "f.txt").write_text("hi", encoding="utf-8")
            mod.write_manifest(out, mod.build_manifest(out))
            with (out / "SHA256SUMS").open("a", encoding="utf-8") as f:
                f.write("0" * 64 + "  MANIFEST_2099-01-01T000000Z.jsonl\n")
            res = mod.verify(out)
            self.assertTrue(res["ok"])
            self.assertEqual(res["orphan_sums"], ["MANIFEST_2099-01-01T000000Z.jsonl"])

    def test_verify_reports_malformed_manifest_instead_of_raising(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            (out / "a").mkdir()
            (out / "a" / "f.txt").write_text("hi", encoding="utf-8")
            m = mod.write_manifest(out, mod.build_manifest(out))
            bad = out / "MANIFEST_2099-01-01T000000Z.jsonl"
            bad.write_text("{not json\n", encoding="utf-8")
            with (out / "SHA256SUMS").open("a", encoding="utf-8") as f:
                f.write(f"{mod.sha256_file(bad)}  {bad.name}\n")
            res = mod.verify(out)
            self.assertFalse(res["ok"])
            self.assertIn("無法解析", res["error"])
            self.assertTrue(m.is_file())

    def test_verify_lists_unlisted_files_without_failing(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            (out / "a").mkdir()
            (out / "a" / "f.txt").write_text("hi", encoding="utf-8")
            mod.write_manifest(out, mod.build_manifest(out))
            (out / "a" / "new.txt").write_text("later", encoding="utf-8")
            res = mod.verify(out)
            self.assertTrue(res["ok"])
            self.assertEqual(res["unlisted"], ["a/new.txt"])

    def test_cli_refuses_when_lock_held_or_disk_low(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            plan = pathlib.Path(td) / "plan.json"
            plan.write_text(json.dumps({"sources": [{"name": "a", "kind": "rclone", "remote": "d:"}]}), encoding="utf-8")
            out = pathlib.Path(td) / "store"
            out.mkdir()
            (out / mod.LOCK_NAME).write_text("{}", encoding="utf-8")
            with mock.patch.object(mod.shutil, "which", return_value="/usr/bin/rclone"):
                self.assertEqual(mod.main(["pull", "--plan", str(plan), "--out", str(out)]), 5)
                self.assertTrue((out / mod.LOCK_NAME).exists())  # 別人的鎖不能被我們清掉
                (out / mod.LOCK_NAME).unlink()
                self.assertEqual(mod.main(["pull", "--plan", str(plan), "--out", str(out),
                                           "--min-free-gb", "99999999"]), 6)
                self.assertFalse((out / mod.LOCK_NAME).exists())


class WindowsCleanupAndEnvTests(unittest.TestCase):
    def test_rmtree_handler_clears_readonly_and_retries(self):
        """模擬 Windows：第一次刪除因唯讀失敗，處理器解除唯讀後必須重試。"""
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            f = pathlib.Path(td) / "obj"
            f.write_text("x", encoding="utf-8")
            func = mock.Mock(side_effect=[PermissionError("read-only"), None])
            mod._rmtree_onerr(func, str(f), None)
            self.assertEqual(func.call_count, 2)

    def test_rmtree_handler_gives_up_quietly_when_still_failing(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            f = pathlib.Path(td) / "obj"
            f.write_text("x", encoding="utf-8")
            func = mock.Mock(side_effect=PermissionError("locked"))
            mod._rmtree_onerr(func, str(f), None)  # 不丟例外；由 _force_rmtree 檢查目錄是否還在

    def test_force_rmtree_removes_tree_with_readonly_files(self):
        with tempfile.TemporaryDirectory() as td:
            d = pathlib.Path(td) / ".partial-x" / ".git" / "objects"
            d.mkdir(parents=True)
            f = d / "pack"
            f.write_text("x", encoding="utf-8")
            f.chmod(0o444)
            d.chmod(0o555)
            self.assertTrue(mod._force_rmtree(pathlib.Path(td) / ".partial-x"))
            self.assertFalse((pathlib.Path(td) / ".partial-x").exists())

    def test_uncleanable_partial_gives_clear_error_instead_of_confusing_clone_failure(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "repo"
            (dst / (mod.PARTIAL_PREFIX + SHA[:12])).mkdir(parents=True)
            r = FakeRunner()
            with mock.patch.object(mod, "_force_rmtree", return_value=False):
                ok, err = mod.pull_git({"url": "https://x/y.git"}, dst, r, 10)
            self.assertFalse(ok)
            self.assertIn("無法移除暫存目錄", err)
            self.assertFalse([c for c in r.calls if c[:2] == ["git", "clone"]])  # 沒有去 clone 到髒目錄

    def test_timeout_during_clone_cleans_partial_and_is_reported_per_source(self):
        class TimeoutOnCheckout(FakeRunner):
            def __call__(self, cmd, **kw):
                if "checkout" in cmd:
                    self.calls.append(cmd)
                    raise subprocess.TimeoutExpired(cmd, 1)
                return super().__call__(cmd, **kw)

        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            res = mod.pull([{"name": "repo", "kind": "git", "url": "https://x/y.git"}], out,
                           runner=TimeoutOnCheckout(), timeout=5)
            self.assertFalse(res["repo"]["ok"])
            self.assertIn("逾時", res["repo"]["error"])
            self.assertEqual([p.name for p in (out / "repo").iterdir()], [])  # 沒有殘留的半成品

    def test_git_env_drops_inherited_repo_location_variables(self):
        from unittest import mock
        polluted = {v: "/somewhere/else" for v in mod.GIT_LOCATION_VARS}
        with mock.patch.dict(mod.os.environ, polluted):
            env = mod._git_env()
        for v in mod.GIT_LOCATION_VARS:
            self.assertNotIn(v, env)
        self.assertEqual(env["GIT_TERMINAL_PROMPT"], "0")
        self.assertIn("PATH", env)  # 其餘環境照常繼承

    def test_git_head_and_pull_use_sanitized_env(self):
        from unittest import mock
        r = FakeRunner()
        with tempfile.TemporaryDirectory() as td, mock.patch.dict(mod.os.environ, {"GIT_DIR": "/x"}):
            mod.git_head(pathlib.Path(td), r)
            mod.pull_git({"url": "https://x/y.git"}, pathlib.Path(td) / "repo", r, 10)
        self.assertTrue(r.kws)
        for kw in r.kws:
            self.assertNotIn("GIT_DIR", kw["env"])


class MirrorModeTests(unittest.TestCase):
    def test_plan_accepts_mirror_and_rejects_unknown_mode(self):
        with tempfile.TemporaryDirectory() as td:
            def load(mode):
                p = pathlib.Path(td) / "p.json"
                p.write_text(json.dumps({"sources": [{"name": "a", "kind": "git", "url": "https://x/y.git", "mode": mode}]}),
                             encoding="utf-8")
                return mod.load_plan(p)
            self.assertEqual(load("mirror")[0]["mode"], "mirror")
            self.assertEqual(load("worktree")[0]["mode"], "worktree")
            with self.assertRaises(ValueError):
                load("sparse")

    def test_example_plan_uses_mirror_for_github_sources(self):
        modes = {s["name"]: s.get("mode") for s in mod.load_plan(_EXAMPLE) if s["kind"] == "git"}
        self.assertTrue(modes)
        self.assertTrue(all(m == "mirror" for m in modes.values()), modes)

    def test_mirror_uses_clone_mirror_without_checkout_and_is_idempotent(self):
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "repo"
            r = FakeRunner()
            self.assertTrue(mod.pull_git({"url": "https://x/y.git", "mode": "mirror"}, dst, r, 10)[0])
            clones = [c for c in r.calls if c[:2] == ["git", "clone"]]
            self.assertEqual(len(clones), 1)
            self.assertIn("--mirror", clones[0])
            self.assertFalse([c for c in r.calls if "checkout" in c])  # 沒有工作樹，沒有 checkout
            self.assertTrue((dst / f"{SHA[:12]}.mirror" / "HEAD").is_file())
            self.assertFalse((dst / SHA[:12]).exists())  # 不佔用 worktree 的目錄名
            self.assertFalse((dst / (mod.PARTIAL_PREFIX + SHA[:12])).exists())
            r2 = FakeRunner()
            self.assertTrue(mod.pull_git({"url": "https://x/y.git", "mode": "mirror"}, dst, r2, 10)[0])
            self.assertFalse([c for c in r2.calls if c[:2] == ["git", "clone"]])

    def test_worktree_failure_on_invalid_windows_path_suggests_mirror(self):
        with tempfile.TemporaryDirectory() as td:
            r = FakeRunner(fail_on="checkout")
            r.stderr = ("error: invalid path 'MRL/母體/echo.analyst '\n" * 30) + "fatal: unable to checkout working tree"
            ok, err = mod.pull_git({"url": "https://x/y.git"}, pathlib.Path(td) / "repo", r, 10)
            self.assertFalse(ok)
            self.assertIn('"mode": "mirror"', err)
            self.assertFalse(list((pathlib.Path(td) / "repo").iterdir()))  # 沒留下半成品

    def test_other_worktree_failures_do_not_get_the_windows_hint(self):
        with tempfile.TemporaryDirectory() as td:
            ok, err = mod.pull_git({"url": "https://x/y.git"}, pathlib.Path(td) / "repo",
                                   FakeRunner(fail_on="checkout"), 10)
            self.assertFalse(ok)
            self.assertNotIn("mirror", err)


    def test_switching_mode_does_not_collide_with_existing_worktree_backup(self):
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "repo"
            self.assertTrue(mod.pull_git({"url": "https://x/y.git"}, dst, FakeRunner(), 10)[0])  # 先用 worktree
            old = sorted(p.name for p in dst.iterdir())
            self.assertEqual(old, [SHA[:12]])
            marker = dst / SHA[:12] / "file.txt"
            before = marker.read_text(encoding="utf-8")
            self.assertTrue(mod.pull_git({"url": "https://x/y.git", "mode": "mirror"}, dst, FakeRunner(), 10)[0])
            self.assertEqual(sorted(p.name for p in dst.iterdir()), sorted([SHA[:12], f"{SHA[:12]}.mirror"]))
            self.assertEqual(marker.read_text(encoding="utf-8"), before)  # 既有備份沒被動

    def test_existing_incomplete_target_is_reported_not_renamed_over(self):
        with tempfile.TemporaryDirectory() as td:
            dst = pathlib.Path(td) / "repo"
            odd = dst / f"{SHA[:12]}.mirror"
            odd.mkdir(parents=True)
            (odd / "stray.txt").write_text("keep me", encoding="utf-8")
            r = FakeRunner()
            ok, err = mod.pull_git({"url": "https://x/y.git", "mode": "mirror"}, dst, r, 10)
            self.assertFalse(ok)
            self.assertIn("不會覆蓋", err)
            self.assertFalse([c for c in r.calls if c[:2] == ["git", "clone"]])
            self.assertEqual((odd / "stray.txt").read_text(encoding="utf-8"), "keep me")

    def test_unexpected_oserror_in_one_source_does_not_stop_the_others(self):
        from unittest import mock
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            real_rename = os.rename
            calls = {"n": 0}

            def flaky(a, b):
                calls["n"] += 1
                if calls["n"] == 1:
                    raise PermissionError("denied")
                return real_rename(a, b)

            sources = [{"name": "one", "kind": "git", "url": "https://x/1.git", "mode": "mirror"},
                       {"name": "two", "kind": "git", "url": "https://x/2.git", "mode": "mirror"}]
            with mock.patch.object(mod.os, "rename", side_effect=flaky):
                res = mod.pull(sources, out, runner=FakeRunner(), timeout=5)
            self.assertFalse(res["one"]["ok"])
            self.assertIn("檔案系統錯誤", res["one"]["error"])
            self.assertTrue(res["two"]["ok"])
            self.assertTrue(mod.build_manifest(out, git_sources={"one", "two"}, runner=FakeRunner()))  # 仍能產生清單

    def test_mirror_manifest_records_head_and_hashes_repo_files(self):
        with tempfile.TemporaryDirectory() as td:
            out = pathlib.Path(td)
            mod.pull_git({"url": "https://x/y.git", "mode": "mirror"}, out / "repo", FakeRunner(), 10)
            (out / "repo" / f"{SHA[:12]}.mirror" / "objects" / "obj1").write_bytes(b"data")
            (out / "repo" / (mod.PARTIAL_PREFIX + "zzz")).mkdir()  # 殘留暫存目錄不得進清單
            rows = mod.build_manifest(out, git_sources={"repo"}, runner=FakeRunner())
            paths = [r["path"] for r in rows]
            self.assertIn(f"{SHA[:12]}.mirror/(mirror HEAD)", paths)
            self.assertIn(f"{SHA[:12]}.mirror/objects/obj1", paths)   # 鏡像內容是資料，逐檔雜湊
            self.assertIn(f"{SHA[:12]}.mirror/HEAD", paths)
            self.assertFalse([p for p in paths if "zzz" in p])


@unittest.skipUnless(__import__("shutil").which("git"), "需要真的 git")
class RealMirrorIntegrationTests(unittest.TestCase):
    @staticmethod
    def _commit_with_trailing_space_name(remote: pathlib.Path) -> None:
        """用 git fast-import 直接寫入物件：檔名結尾帶空白的條目不經過工作樹與索引，
        所以任何作業系統（包含 Windows，那裡工作樹與索引都拒絕這種檔名）都能建出同樣的提交。"""
        env = mod._git_env()
        run = lambda *a, **k: subprocess.run(["git", "-C", str(remote), *a], check=True, capture_output=True, env=env, **k)
        run("init", "-q")
        run("symbolic-ref", "HEAD", "refs/heads/main")
        body = "結尾有空白的檔名".encode("utf-8")
        ok = b"ok"
        quoted = "".join(f"\\{b:03o}" if b > 127 else chr(b) for b in "母體/".encode("utf-8")) + "echo.analyst "
        stream = (b"commit refs/heads/main\ncommitter t <t@t> 1700000000 +0000\ndata 2\nc1\n"
                  + b"M 100644 inline ok.txt\ndata " + str(len(ok)).encode() + b"\n" + ok + b"\n"
                  + b'M 100644 inline "' + quoted.encode("ascii") + b'"\ndata ' + str(len(body)).encode() + b"\n" + body + b"\n")
        run("fast-import", "--quiet", input=stream)

    def test_mirror_preserves_windows_invalid_filename_and_verifies(self):
        with tempfile.TemporaryDirectory() as td:
            remote = pathlib.Path(td) / "remote"
            remote.mkdir()
            self._commit_with_trailing_space_name(remote)
            store = pathlib.Path(td) / "store"
            res = mod.pull([{"name": "repo", "kind": "git", "url": remote.as_uri(), "mode": "mirror"}], store, timeout=120)
            self.assertTrue(res["repo"]["ok"], res)
            (rev,) = [p for p in (store / "repo").iterdir()]
            self.assertTrue((rev / "HEAD").is_file())
            raw = subprocess.run(["git", "--git-dir", str(rev), "ls-tree", "-r", "--name-only", "-z", "HEAD"],
                                 capture_output=True, env=mod._git_env()).stdout
            names = raw.decode("utf-8").split("\0")
            self.assertIn("母體/echo.analyst ", names)  # 結尾空白的檔名完整保留
            rows = mod.build_manifest(store, git_sources={"repo"})
            self.assertTrue([r for r in rows if r["path"].endswith("(mirror HEAD)") and r["git_head"]])
            mod.write_manifest(store, rows)
            self.assertTrue(mod.verify(store)["ok"])


@unittest.skipUnless(__import__("shutil").which("git"), "需要真的 git")
class RealGitIntegrationTests(unittest.TestCase):
    """用本機倉庫跑真的 git：兩次不同 HEAD 的拉取各自成一個修訂目錄，舊的完全不動。"""

    @staticmethod
    def _git(repo, *args):
        subprocess.run(["git", "-C", str(repo), "-c", "user.email=t@t", "-c", "user.name=t", *args],
                       check=True, capture_output=True, env=mod._git_env())

    def test_two_heads_make_two_immutable_revisions(self):
        with tempfile.TemporaryDirectory() as td:
            remote = pathlib.Path(td) / "remote"
            remote.mkdir()
            self._git(remote, "init", "-q")
            (remote / "a.txt").write_text("v1", encoding="utf-8")
            self._git(remote, "add", ".")
            self._git(remote, "commit", "-qm", "c1")
            dst = pathlib.Path(td) / "store" / "repo"
            url = remote.as_uri()
            self.assertTrue(mod.pull_git({"url": url}, dst, subprocess.run, 120)[0])
            (rev1,) = [p for p in dst.iterdir()]
            self.assertTrue((rev1 / "a.txt").is_file())

            self.assertTrue(mod.pull_git({"url": url}, dst, subprocess.run, 120)[0])  # 同一 HEAD：不新增
            self.assertEqual(len(list(dst.iterdir())), 1)

            (remote / "a.txt").write_text("v2", encoding="utf-8")
            (remote / "b.txt").write_text("new", encoding="utf-8")
            self._git(remote, "add", ".")
            self._git(remote, "commit", "-qm", "c2")
            self.assertTrue(mod.pull_git({"url": url}, dst, subprocess.run, 120)[0])
            revs = sorted(p.name for p in dst.iterdir())
            self.assertEqual(len(revs), 2)
            self.assertEqual((rev1 / "a.txt").read_text(encoding="utf-8"), "v1")  # 舊修訂沒被動
            self.assertFalse((rev1 / "b.txt").exists())
            new = [dst / n for n in revs if n != rev1.name][0]
            self.assertEqual((new / "a.txt").read_text(encoding="utf-8"), "v2")

            store = pathlib.Path(td) / "store"
            rows = mod.build_manifest(store, git_sources={"repo"})
            heads = [r for r in rows if "git_head" in r]
            self.assertEqual(len(heads), 2)
            self.assertTrue(all(r["git_head"] for r in heads))
            mod.write_manifest(store, rows)
            self.assertTrue(mod.verify(store)["ok"])

    def test_unreachable_remote_fails_fast_without_prompt(self):
        with tempfile.TemporaryDirectory() as td:
            ok, err = mod.pull_git({"url": (pathlib.Path(td) / "nope").as_uri()},
                                   pathlib.Path(td) / "repo", subprocess.run, 60)
            self.assertFalse(ok)
            self.assertTrue(err)


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
