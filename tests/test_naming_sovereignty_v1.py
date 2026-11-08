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
import MRL_NamingSovereignty_v1 as ns  # noqa: E402  real CLI entrypoint under test
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
        # assert the exact canonical (prefix removed + all segments sanitized)
        self.assertEqual(r["canonical"], "MRL_recovered/whitelist_mrliouword_domain_xls2qt")
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

    def test_namespace_only_prefix_rejected(self):
        # bare prefixes carry MRL_ but no identifier — must not pass as compliant no-ops
        for bad in ("MRL_", "MRL_recovered/", " MRL_ ", "MRL_recovered/  "):
            with self.assertRaises(ValueError, msg=f"{bad!r} must be rejected"):
                reclaim_name(bad)

    def test_malformed_prefixed_not_compliant(self):
        # MRL_-prefixed but the leaf isn't clean canonical (sanitize would change it) → rejected,
        # so it can't bypass reclamation/error reporting.
        for bad in ("MRL_!!!", "MRL_foo/bar", "MRL_recovered/foo/bar", "MRL_a b"):
            with self.assertRaises(ValueError, msg=f"{bad!r} must be rejected"):
                reclaim_name(bad)
        # and via scan(): surfaced as an error, never compliant
        reports = scan(["MRL_!!!", "MRL_AI"])
        by_original = {r["original"]: r for r in reports}
        self.assertTrue(by_original["MRL_!!!"]["error"])
        self.assertNotIn("MRL_AI", by_original)  # clean canonical is skipped (compliant)

    def test_valid_canonicals_are_idempotent(self):
        # reclaim outputs must themselves be recognised as clean canonicals (no re-churn)
        for good in ("MRL_AI", "MRL_vector_store", "MRL_世界模組", "MRL_recovered/add_gpu_support"):
            self.assertFalse(reclaim_name(good)["reclaimed"], f"{good!r} must be a no-op")
            self.assertEqual(scan([good]), [], f"{good!r} must be compliant in scan")

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

    def test_scan_duplicate_identical_input_is_not_collision(self):
        # same input twice → same canonical, but ONE distinct original → not a collision
        reports = scan(["vector_store", "vector_store"])
        self.assertEqual(len(reports), 2, "both inputs must be reported (non-vacuous)")
        self.assertEqual([r["original"] for r in reports], ["vector_store", "vector_store"])
        self.assertTrue(all(not r["collision"] for r in reports))

    def test_scan_degenerate_prefixed_is_error_not_compliant(self):
        # "MRL_" / "MRL_recovered/" carry the prefix but are namespace-only → error-reported
        reports = scan(["MRL_", "MRL_recovered/", "MRL_AI"])
        by_original = {r["original"]: r for r in reports}
        self.assertTrue(by_original["MRL_"]["error"])
        self.assertTrue(by_original["MRL_recovered/"]["error"])
        # the valid compliant name is skipped (not reported at all)
        self.assertNotIn("MRL_AI", by_original)

    def test_scan_collision_with_existing_compliant_name(self):
        # a proposal whose canonical is already occupied by a compliant MRL_ name collides
        reports = scan(["MRL_vector_store", "vector store!!"])
        # only the non-compliant one is reported, and it must be flagged colliding
        self.assertEqual(len(reports), 1)
        self.assertEqual(reports[0]["canonical"], "MRL_vector_store")
        self.assertTrue(reports[0]["collision"])

    # ── CLI coverage: drive the REAL main() entrypoint (argv), not a test-local dispatch ─
    def _run_cli(self, argv):
        buf = io.StringIO()
        old_argv = sys.argv
        sys.argv = ["MRL_NamingSovereignty_v1.py", *argv]
        try:
            with contextlib.redirect_stdout(buf):
                ns.main()
        finally:
            sys.argv = old_argv
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

    def test_cli_check_excludes_degenerate_from_compliant(self):
        out = self._run_cli(["check", "MRL_", "MRL_AI"])
        self.assertNotIn("MRL_", out["compliant_mrl_prefixed"])
        self.assertIn("MRL_AI", out["compliant_mrl_prefixed"])
        # "MRL_" surfaces as an error report, never silently compliant
        self.assertTrue(any(r.get("error") and r["original"] == "MRL_"
                            for r in out["needs_reclamation"]))

    def test_cli_reclaim_invalid_input_json_error_and_nonzero(self):
        buf = io.StringIO()
        old_argv = sys.argv
        sys.argv = ["MRL_NamingSovereignty_v1.py", "reclaim", "MRL_"]
        try:
            with contextlib.redirect_stdout(buf):
                with self.assertRaises(SystemExit) as cm:
                    ns.main()
        finally:
            sys.argv = old_argv
        self.assertNotEqual(cm.exception.code, 0, "invalid reclaim must exit non-zero")
        payload = json.loads(buf.getvalue())  # machine-readable, not a traceback
        self.assertTrue(payload["error"])
        self.assertEqual(payload["original"], "MRL_")


if __name__ == "__main__":
    unittest.main(verbosity=2)
