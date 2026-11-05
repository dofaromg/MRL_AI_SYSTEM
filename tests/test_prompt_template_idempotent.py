#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Regression: TemplateRegistry.add() idempotent on unchanged content.
Root cause of data/prompt_templates.json version churn (9->12->244->332).
origin_signature: MrLiouWord"""
import pathlib, sys, tempfile, unittest
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "09_workflow"))
from prompt_template import TemplateRegistry


class TestAddIdempotent(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.dir.name) / "store.json"

    def tearDown(self):
        self.dir.cleanup()

    def test_readd_identical_does_not_bump_version(self):
        reg = TemplateRegistry(self.path)
        t1 = reg.add("greet", "Hello, {name}!", "desc")
        v1, ts1 = t1.version, t1.created_at_ms
        for _ in range(20):
            t = reg.add("greet", "Hello, {name}!", "desc")
        self.assertEqual(t.version, v1, "version must NOT bump on unchanged content")
        self.assertEqual(t.created_at_ms, ts1, "created_at_ms must NOT reset on unchanged content")

    def test_changed_text_bumps_version(self):
        reg = TemplateRegistry(self.path)
        reg.add("greet", "Hello, {name}!", "desc")
        t = reg.add("greet", "Hi, {name}!", "desc")
        self.assertEqual(t.version, 2)

    def test_changed_description_bumps_version(self):
        reg = TemplateRegistry(self.path)
        reg.add("greet", "Hello, {name}!", "d1")
        t = reg.add("greet", "Hello, {name}!", "d2")
        self.assertEqual(t.version, 2)

    def test_new_template_starts_at_version_1(self):
        reg = TemplateRegistry(self.path)
        self.assertEqual(reg.add("fresh", "X {y}", "").version, 1)

    def test_persisted_store_stable_across_reloads(self):
        # simulate repeated process restarts re-seeding the same template
        for _ in range(5):
            TemplateRegistry(self.path).add("system_intro", "You are {name}.", "std")
        final = TemplateRegistry(self.path).get("system_intro")
        self.assertEqual(final.version, 1, "restart re-seed must not inflate version")


if __name__ == "__main__":
    unittest.main(verbosity=2)
