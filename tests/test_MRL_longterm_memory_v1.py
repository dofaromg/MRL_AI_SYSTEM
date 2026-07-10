#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for MRL_LongTermMemory_v1 — remember / recall over embedder + vector store.
origin_signature: MrLiouWord"""
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "09_workflow"))
from MRL_LongTermMemory_v1 import MRL_LongTermMemory


class TestLongTermMemory(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.dir.name) / "ltm.json"

    def tearDown(self):
        self.dir.cleanup()

    def _seed(self, ltm):
        ltm.remember("s1", "user", "durable replay across reboot exact state hash")
        ltm.remember("s1", "user", "the cat sat on the warm sunny windowsill")
        ltm.remember("s1", "user", "母體根源法則 origin_signature 命名主權")
        ltm.remember("s1", "user", "spam detection naive bayes tfidf classifier")

    def test_remember_increases_count(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        self.assertEqual(len(ltm), 0)
        ltm.remember("s1", "user", "hello world")
        self.assertEqual(len(ltm), 1)

    def test_recall_ranks_relevant_first(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        self._seed(ltm)
        hits = ltm.recall("reboot replay state hash exact", top_k=2)
        self.assertTrue(hits, "recall must return results")
        self.assertIn("durable replay", hits[0]["content"],
                      "most semantically relevant memory must rank first")

    def test_recall_cjk(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        self._seed(ltm)
        hits = ltm.recall("命名主權 origin_signature", top_k=1)
        self.assertTrue(hits)
        self.assertIn("命名主權", hits[0]["content"], "CJK query must recall CJK memory")

    def test_recall_empty_query_returns_empty(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        self._seed(ltm)
        self.assertEqual(ltm.recall("   "), [])

    def test_remember_empty_raises(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        with self.assertRaises(ValueError):
            ltm.remember("s1", "user", "   ")

    def test_persists_across_instances(self):
        ltm1 = MRL_LongTermMemory(store_path=self.path)
        ltm1.remember("s1", "user", "durable replay across reboot exact state hash")
        ltm2 = MRL_LongTermMemory(store_path=self.path)
        self.assertEqual(len(ltm2), 1)
        hits = ltm2.recall("reboot replay", top_k=1)
        self.assertTrue(hits)
        self.assertIn("durable replay", hits[0]["content"])

    def test_recall_as_context_shape_and_role(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        self._seed(ltm)
        msgs = ltm.recall_as_context("reboot replay state hash", top_k=2)
        self.assertTrue(msgs)
        m = msgs[0]
        self.assertEqual(m["role"], "system")
        # speaker attribution preserved in text + meta
        self.assertTrue(m["content"].startswith("[long-term memory | user]"))
        self.assertEqual(m["meta"]["recalled_role"], "user")
        self.assertTrue(m["meta"]["is_recalled_memory"])
        self.assertEqual(m["origin_signature"], "MrLiouWord")

    def test_recall_scoped_to_session(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        ltm.remember("alice", "user", "durable replay across reboot exact state hash")
        ltm.remember("bob", "user", "durable replay across reboot exact state hash")
        hits = ltm.recall("reboot replay state hash", top_k=5, session_id="alice")
        self.assertTrue(hits)
        self.assertTrue(all(h["session_id"] == "alice" for h in hits),
                        "recall must not leak other sessions' memories")

    def test_remember_many_single_batch(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        stored = ltm.remember_many([
            ("s1", "user", "hello there"),
            ("s1", "assistant", "general kenobi"),
        ])
        self.assertEqual(len(stored), 2)
        self.assertEqual(len(ltm), 2)
        # persisted (readable by a fresh instance)
        self.assertEqual(len(MRL_LongTermMemory(store_path=self.path)), 2)

    def test_top_k_must_be_positive(self):
        ltm = MRL_LongTermMemory(store_path=self.path)
        self._seed(ltm)
        for bad in (0, -1):
            with self.assertRaises(ValueError):
                ltm.recall("anything", top_k=bad)


if __name__ == "__main__":
    unittest.main(verbosity=2)
