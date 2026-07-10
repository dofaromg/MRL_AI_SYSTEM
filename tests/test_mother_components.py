#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for the three MRL_Mother runnable components (MRL_AI / MRL_AGI / MRL_ASI).

Ensures each shell is a real, runnable, origin-verified particle — not a
README-only \"completed_running\" claim (rootlaw no_proof_implies_rhetoric).
origin_signature: MrLiouWord"""
import pathlib
import sys
import unittest

_ROOT = pathlib.Path(__file__).resolve().parent.parent
_MOTHER = _ROOT / "MRL_Mother"
for _p in (_MOTHER, _MOTHER / "MRL_AI", _MOTHER / "MRL_AGI", _MOTHER / "MRL_ASI"):
    sys.path.insert(0, str(_p))

from mrl_ai import MRL_AI            # noqa: E402
from mrl_agi import MRL_AGI          # noqa: E402
from mrl_asi import MRL_ASI          # noqa: E402
from mrl_mother_component import (   # noqa: E402
    MRL_MotherComponent,
    ORIGIN_SIGNATURE,
)


class TestMotherComponents(unittest.TestCase):
    def setUp(self):
        self.components = [MRL_AI(), MRL_AGI(), MRL_ASI()]

    def test_are_mother_components(self):
        for c in self.components:
            self.assertIsInstance(c, MRL_MotherComponent)

    def test_verify_origin_true_for_canonical_signature(self):
        for c in self.components:
            self.assertTrue(c.verify_origin(), f"{c.canonical_name} must verify origin")

    def test_run_returns_output_and_marks_ran(self):
        for c in self.components:
            out = c.run()
            self.assertTrue(out["ran"])
            self.assertEqual(out["origin_signature"], ORIGIN_SIGNATURE)
            self.assertEqual(out["status"], "registered_runnable_component")

    def test_describe_carries_canonical_name_and_role(self):
        expected_role_token = {"MRL_AI": "感知", "MRL_AGI": "泛化", "MRL_ASI": "最高"}
        for c in self.components:
            d = c.describe()
            self.assertEqual(d["canonical_name"], c.canonical_name)
            self.assertIn(expected_role_token[c.canonical_name], d["role"])

    def test_run_rejects_wrong_origin(self):
        c = MRL_AI(origin_signature="NotMrLiou")
        self.assertFalse(c.verify_origin())
        with self.assertRaises(PermissionError):
            c.run()

    def test_honest_status_not_completed_claim(self):
        # The component must NOT parrot a \"completed_running\" achievement claim;
        # it must carry the anchored-vision honesty marker instead.
        for c in self.components:
            d = c.describe()
            self.assertNotIn("completed_running", str(d))
            self.assertIn("願景錨定", d["honest_note"])


if __name__ == "__main__":
    unittest.main(verbosity=2)
