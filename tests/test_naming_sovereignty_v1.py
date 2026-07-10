#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for MRL_NamingSovereignty_v1 — rl_16 gate / rl_12 rename / rl_20 branch reclaim.
origin_signature: MrLiouWord"""
import contextlib
import io
import json
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "09_workflow"))
from MRL_NamingSovereignty_v1 import (  # noqa: E402
    ORIGIN_SIGNATURE,
    _build_argparser,
    _cmd_check,
    _cmd_reclaim,
    has_mrl_prefix,
    reclaim_name,
    scan,
)


class TestNamingSovereignty(unittest.TestCase):
    # rl_16 — MRL_ prefix gate
    def test_prefix_gate(self):
        self.assertTrue(has_mrl_prefix("MRL_AI"))
        self.assertFalse(has_mrl_prefix("vector_store"))
        self.assertFalse(has_mrl_prefix("claude/foo"))

    # rl_20 — vendor branch reclaimed to MRL_recovered/
    def test_reclaim_vendor_branch(self):
        r = reclaim_name("claude/whitelist-mrliouword-domain-xls2qt")
        self.assertTrue(r["reclaimed"])
        self.assertEqual(r["rule"], "rl_20")
        self.assertTrue(r["canonical"].startswith("MRL_recovered/"))
        self.assertNotIn("/whitelist-", r["canonical"])  # hyphens sanitized to underscore
        self.assertEqual(r["origin_signature"], ORIGIN_SIGNATURE)

    def test_reclaim_copilot_branch(self):
        r = reclaim_name("copilot/add-gpu-support")
        self.assertEqual(r["canonical"], "MRL_recovered/add_gpu_support")
        self.assertEqual(r["rule"], "rl_20")

    # rl_12 — plain external name renamed to MRL_<desc>
    def test_reclaim_plain_external(self):
        r = reclaim_name("vector store!!")
        self.assertEqual(r["canonical"], "MRL_vector_store")
        self.assertEqual(r["rule"], "rl_12")
        self.assertTrue(r["reclaimed"])

    def test_reclaim_cjk_name(self):
        r = reclaim_name("世界模組")
        self.assertEqual(r["canonical"], "MRL_世界模組")

    # already canonical — no-op
    def test_reclaim_already_mrl_is_noop(self):
        r = reclaim_name("MRL_AI")
        self.assertFalse(r["reclaimed"])
        self.assertEqual(r["canonical"], "MRL_AI")

    # rl_15 / rl_01 — original always preserved, never mutated
    def test_original_always_preserved(self):
        src = "codex/complete-unfinished-tasks"
        r = reclaim_name(src)
        self.assertEqual(r["preserved_original"], src)
        self.assertEqual(r["original"], src)

    # determinism — same input, same canonical
    def test_deterministic(self):
        a = reclaim_name("copilot/app")
        b = reclaim_name("copilot/app")
        self.assertEqual(a["canonical"], b["canonical"])

    # scan is read-only and only reports non-compliant names
    def test_scan_reports_only_noncompliant(self):
        names = ["MRL_AI", "copilot/app", "vector_store", "MRL_Globe_v2"]
        reports = scan(names)
        self.assertEqual(len(reports), 2)
        originals = {r["original"] for r in reports}
        self.assertEqual(originals, {"copilot/app", "vector_store"})

    def test_empty_name_raises(self):
        with self.assertRaises(ValueError):
            reclaim_name("   ")

    # ── regression: whitespace normalization consistency ──────────────────────
    def test_whitespace_padded_mrl_is_compliant_everywhere(self):
        r = reclaim_name(" MRL_AI ")
        self.assertFalse(r["reclaimed"], "padded MRL_ name must be treated compliant")
        self.assertEqual(r["canonical"], "MRL_AI")
        self.assertEqual(r["preserved_original"], " MRL_AI ", "raw input preserved verbatim")
        # scan must NOT report a compliant-after-strip name
        self.assertEqual(scan([" MRL_AI "]), [])

    # ── regression: sanitize-to-empty must be rejected, never degenerate ──────
    def test_punctuation_only_raises(self):
        for bad in ("!!!", "/", "   /   ", "copilot/---"):
            with self.assertRaises(ValueError, msg=f"{bad!r} must be rejected"):
                reclaim_name(bad)

    def test_no_degenerate_canonical_ever(self):
        # Whatever reclaim returns, canonical must never be a bare prefix.
        for name in ("vector_store", "世界模組", "claude/foo", "copilot/add-gpu"):
            c = reclaim_name(name)["canonical"]
            self.assertNotIn(c, ("MRL_", "MRL_recovered/"))
            self.assertTrue(c.startswith("MRL_"))

    def test_scan_reports_unreclaimable_as_error_without_crashing(self):
        reports = scan(["vector_store", "!!!"])
        by_original = {r["original"]: r for r in reports}
        self.assertTrue(by_original["!!!"]["error"])
        self.assertIsNone(by_original["!!!"]["canonical"])
        self.assertNotIn("error", by_original["vector_store"])

    # ── regression: batch collision detection (rl_02 resolves at apply-time) ──
    def test_scan_flags_collisions(self):
        reports = scan(["vector store!!", "vector_store", "claude/foo", "copilot/foo", "MRL_ok"])
        by_original = {r["original"]: r for r in reports}
        self.assertEqual(by_original["vector store!!"]["canonical"], "MRL_vector_store")
        self.assertEqual(by_original["vector_store"]["canonical"], "MRL_vector_store")
        self.assertTrue(by_original["vector store!!"]["collision"])
        self.assertTrue(by_original["vector_store"]["collision"])
        # claude/foo and copilot/foo both -> MRL_recovered/foo
        self.assertEqual(by_original["claude/foo"]["canonical"], "MRL_recovered/foo")
        self.assertTrue(by_original["copilot/foo"]["collision"])

    def test_scan_no_false_collision(self):
        reports = scan(["vector_store", "copilot/app"])
        self.assertTrue(all(not r["collision"] for r in reports))

    # ── CLI coverage: check is read-only + reports non-compliant; reclaim maps ─
    def _run_cli(self, argv):
        args = _build_argparser().parse_args(argv)
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            {"check": _cmd_check, "reclaim": _cmd_reclaim}[args.cmd](args)
        return json.loads(buf.getvalue())

    def test_cli_check_reports_only_noncompliant(self):
        out = self._run_cli(["check", "MRL_AI", " MRL_Padded ", "copilot/app", "vector_store"])
        self.assertIn("MRL_AI", out["compliant_mrl_prefixed"])
        self.assertIn(" MRL_Padded ", out["compliant_mrl_prefixed"])  # padded still compliant
        originals = {r["original"] for r in out["needs_reclamation"]}
        self.assertEqual(originals, {"copilot/app", "vector_store"})

    def test_cli_reclaim_maps_without_mutating_source(self):
        out = self._run_cli(["reclaim", "copilot/add-gpu-support"])
        self.assertEqual(out["canonical"], "MRL_recovered/add_gpu_support")
        self.assertEqual(out["preserved_original"], "copilot/add-gpu-support")
        self.assertEqual(out["origin_signature"], ORIGIN_SIGNATURE)


if __name__ == "__main__":
    unittest.main(verbosity=2)
