#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for MRL_Hybrid_Knowledge_Base_v1 — 神經符號混合知識庫(符號庫 + 神經庫 + 映射 + 一致性 + 圖).
origin_signature: MrLiouWord"""
import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "09_workflow"))
from MRL_Hybrid_Knowledge_Base_v1 import (  # noqa: E402
    MRL_HybridKnowledgeBase,
    verify_signature,
)


class TestHybridKnowledgeBase(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.TemporaryDirectory()
        self.path = pathlib.Path(self.dir.name) / "hkb.json"

    def tearDown(self):
        self.dir.cleanup()

    def _kb(self):
        return MRL_HybridKnowledgeBase(store_path=self.path)

    # ── write / len ─────────────────────────────────────────────────────────
    def test_add_increases_count(self):
        kb = self._kb()
        self.assertEqual(len(kb), 0)
        kb.incremental_update("貓", "是", "動物")
        self.assertEqual(len(kb), 1)

    def test_add_empty_field_raises(self):
        kb = self._kb()
        with self.assertRaises(ValueError):
            kb.incremental_update("貓", "是", "   ")

    def test_add_is_idempotent(self):
        """同三元組重覆 add 不長 count(deterministic id 去重)。"""
        kb = self._kb()
        kb.incremental_update("貓", "是", "動物")
        kb.incremental_update("貓", "是", "動物")
        self.assertEqual(len(kb), 1)

    # ── exact query ──────────────────────────────────────────────────────────
    def test_exact_query_by_each_field(self):
        kb = self._kb()
        kb.incremental_update("貓", "是", "動物")
        kb.incremental_update("狗", "是", "動物")
        by_subj = kb.exact_query(subject="貓")
        self.assertEqual(len(by_subj), 1)
        self.assertEqual(by_subj[0]["object"], "動物")
        by_pred = kb.exact_query(predicate="是")
        self.assertEqual(len(by_pred), 2)
        by_obj = kb.exact_query(obj="動物")
        self.assertEqual(len(by_obj), 2)
        # 交集:subject + object 同時給
        both = kb.exact_query(subject="狗", obj="動物")
        self.assertEqual(len(both), 1)
        self.assertEqual(both[0]["subject"], "狗")

    # ── similarity query (neural side reused from vector_store) ───────────────
    def test_similarity_query_recalls_semantic_neighbor(self):
        kb = self._kb()
        kb.incremental_update("貓", "是", "動物", text="貓是一種溫馴的哺乳類動物")
        kb.incremental_update("引擎", "屬於", "機械", text="內燃機引擎是機械裝置")
        hits = kb.similarity_query("哺乳類動物", top_k=1)
        self.assertTrue(hits, "similarity query must return a hit")
        self.assertIn("哺乳類", hits[0]["text"], "closest neural doc must be the animal one")

    def test_similarity_empty_query_returns_empty(self):
        kb = self._kb()
        kb.incremental_update("貓", "是", "動物", text="貓是動物")
        self.assertEqual(kb.similarity_query("   "), [])

    # ── hybrid query merges + dedups ─────────────────────────────────────────
    def test_hybrid_query_merges_and_dedups(self):
        kb = self._kb()
        kb.incremental_update("貓", "是", "動物", text="貓是一種動物")
        kb.incremental_update("狗", "是", "動物", text="狗也是一種動物")
        res = kb.hybrid_query("貓 動物", top_k=5)
        self.assertTrue(res["exact"], "symbolic exact side must find facts")
        self.assertTrue(res["similar"], "neural side must find docs")
        ids = [f["fact_id"] for f in res["facts"]]
        self.assertEqual(len(ids), len(set(ids)), "merged facts must be de-duplicated")

    def test_hybrid_empty_query(self):
        kb = self._kb()
        self.assertEqual(kb.hybrid_query("  ")["facts"], [])

    # ── map index ────────────────────────────────────────────────────────────
    def test_neural_id_linked_to_fact(self):
        kb = self._kb()
        r = kb.incremental_update("貓", "是", "動物", text="貓是一種動物")
        self.assertIn("neural_id", r)
        hits = kb.similarity_query("動物", top_k=1)
        self.assertEqual(hits[0]["fact_id"], r["fact_id"],
                         "neural hit must carry its linked symbolic fact_id")

    # ── consistency (report only, never deletes) ─────────────────────────────
    def test_contradiction_functional_conflict(self):
        kb = self._kb()
        kb.incremental_update("天空", "顏色是", "藍色")
        kb.incremental_update("天空", "顏色是", "綠色")
        rep = kb.refine_knowledge()
        kinds = {c["type"] for c in rep["contradictions"]}
        self.assertIn("functional_conflict", kinds)

    def test_contradiction_explicit_negation(self):
        kb = self._kb()
        kb.incremental_update("貓", "是", "哺乳類")
        kb.incremental_update("貓", "不是", "哺乳類")
        rep = kb.refine_knowledge()
        kinds = {c["type"] for c in rep["contradictions"]}
        self.assertIn("negation_conflict", kinds)

    def test_negation_conflict_reported_once(self):
        """多個相異否定謂詞(不是/非是)對同一 (s,o,base) 只回報一次,不重覆。"""
        kb = self._kb()
        kb.incremental_update("貓", "是", "哺乳類")
        kb.incremental_update("貓", "不是", "哺乳類")
        kb.incremental_update("貓", "非是", "哺乳類")
        rep = kb.refine_knowledge()
        neg = [c for c in rep["contradictions"] if c["type"] == "negation_conflict"]
        self.assertEqual(len(neg), 1, "same (subject,object,base) negation must dedupe")

    def test_concurrent_incremental_update_is_thread_safe(self):
        """RLock 序列化並發 incremental_update:20 執行緒各寫一筆 → 恰 20 筆(不交錯毀損)。"""
        import threading
        kb = self._kb()

        def worker(i):
            kb.incremental_update(f"s{i}", "是", "x")

        threads = [threading.Thread(target=worker, args=(i,)) for i in range(20)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        self.assertEqual(len(kb), 20)
        # 並發後仍可 refine(只讀)且不改 len
        self.assertEqual(kb.refine_knowledge()["total_facts"], 20)

    def test_redundancy_detects_casing_whitespace_dup(self):
        kb = self._kb()
        kb.incremental_update("Alice", "knows", "Bob")
        kb.incremental_update("alice ", "KNOWS", " bob")
        rep = kb.refine_knowledge()
        self.assertTrue(rep["redundancies"], "normalized-equal triples must be flagged")

    def test_refine_never_deletes(self):
        """rl_01/rl_15:一致性精煉只報不刪 —— 前後 len 不變。"""
        kb = self._kb()
        kb.incremental_update("天空", "顏色是", "藍色")
        kb.incremental_update("天空", "顏色是", "綠色")
        before = len(kb)
        rep = kb.refine_knowledge()
        self.assertFalse(rep["mutated"])
        self.assertEqual(len(kb), before)
        self.assertIn("待實作", rep["subsumptions_note"])  # 誠實標記,不偽稱完成

    # ── knowledge graph BFS ──────────────────────────────────────────────────
    def test_path_between_multi_hop(self):
        kb = self._kb()
        kb.integrate_knowledge([
            ("貓", "是", "哺乳類", None),
            ("哺乳類", "是", "動物", None),
            ("動物", "是", "生物", None),
        ])
        path = kb.path_between("貓", "生物")
        self.assertIsNotNone(path)
        self.assertEqual(len(path), 3)
        self.assertEqual(path[0]["from"], "貓")
        self.assertEqual(path[-1]["to"], "生物")

    def test_path_between_unreachable(self):
        kb = self._kb()
        kb.incremental_update("貓", "是", "動物")
        kb.incremental_update("石頭", "是", "礦物")
        self.assertIsNone(kb.path_between("貓", "礦物"))

    # ── persistence + LAW-0 signature ────────────────────────────────────────
    def test_persists_across_instances(self):
        kb1 = self._kb()
        kb1.incremental_update("貓", "是", "動物", text="貓是一種動物")
        kb2 = self._kb()
        self.assertEqual(len(kb2), 1)
        self.assertEqual(kb2.exact_query(subject="貓")[0]["object"], "動物")
        # 神經側也持久化(姊妹檔),相似查詢在新實例仍可用
        self.assertTrue(kb2.similarity_query("動物", top_k=1))

    def test_persisted_payload_is_law0_signed(self):
        kb = self._kb()
        kb.incremental_update("貓", "是", "動物")
        with self.path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("_signature"), "MrLiouWord")
        self.assertTrue(verify_signature(data), "persisted payload must pass LAW-0 verify")

    def test_integrate_knowledge_batch(self):
        kb = self._kb()
        out = kb.integrate_knowledge([
            ("貓", "是", "動物", "貓是動物"),
            ("狗", "是", "動物", "狗是動物"),
        ])
        self.assertEqual(len(out), 2)
        self.assertEqual(len(kb), 2)
        self.assertEqual(len(MRL_HybridKnowledgeBase(store_path=self.path)), 2)


if __name__ == "__main__":
    unittest.main(verbosity=2)
