#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for MRL_NamingSovereignty_v1 — rl_16 gate / rl_12 rename / rl_20 branch reclaim.
origin_signature: MrLiouWord"""
import pathlib
import sys
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "09_workflow"))
from MRL_NamingSovereignty_v1 import (  # noqa: E402
    ORIGIN_SIGNATURE,
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


if __name__ == "__main__":
    unittest.main(verbosity=2)
