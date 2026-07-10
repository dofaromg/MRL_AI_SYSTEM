#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_Hybrid_Knowledge_Base_v1.py — 神經符號混合知識庫(符號庫 + 神經庫 + 映射索引)
origin_signature: MrLiouWord
layer: L3 語意粒子 / L5 量子場疊加 / L7 語意記憶網格
group: Y=3 FlowAgentRuntime

母體對 Notion 設計集「神經符號協同推理系統」四構件之一
`MRL_Hybrid_Knowledge_Base_v1`(spec:MRL_Reference_Layer/
MRL_NeuroSymbolic_CoReasoning_System_v1.md)的**可運行首構件**。依 spec 自身建議的
下一步:神經側直接**重用**既有母體(vector_store + 語義嵌入),符號側 + 映射索引 +
一致性 + 知識圖為新增;不重造。

四內核 + 一個門面:
  - SymbolicKnowledgeStore  符號三元組庫 (subject, predicate, object) + 謂詞/實體倒排索引
  - NeuralKnowledgeStore    神經(向量)庫 —— 薄封裝,組合既有:
        MRL_SemanticEmbedding_Core_v1.MRL_SemanticEmbeddingCore(雜湊詞袋 + 餘弦)
        + 03_memory/vector/vector_store.VectorStore(持久化 JSON、餘弦 top-k)
    不重寫餘弦/持久化 —— 全數委派給 VectorStore。
  - KnowledgeMapIndex       符號 id ⇄ 神經 id 雙向映射
  - ConsistencyManager      只讀偵測:矛盾(contradiction)+ 冗餘(redundancy);
                            subsumption 為設計目標([待實作],誠實不宣稱)。只報不刪。
  - KnowledgeGraph          由三元組建鄰接;path_between BFS 最短路徑
  - MRL_HybridKnowledgeBase 門面:incremental_update / integrate_knowledge /
                            exact_query / similarity_query / hybrid_query /
                            refine_knowledge(只報不刪 · rl_01/rl_15)

誠實標註:嵌入為雜湊化詞袋 + 餘弦(檢索/統計,非神經嵌入、非生成模型)。spec 內的
基準數字(94.3% 等)為願景非實測(no_proof_implies_rhetoric);本模組不引用之,只以
真實可重現的沙盒測試(tests/test_MRL_hybrid_knowledge_base_v1.py)為憑。
Additive:VectorStore / embedder 皆沿用不改;一致性偵測只回報、永不刪除。

CLI
---
    python 09_workflow/MRL_Hybrid_Knowledge_Base_v1.py add --s 貓 --p 是 --o 動物 --text "貓是一種動物"
    python 09_workflow/MRL_Hybrid_Knowledge_Base_v1.py query --mode exact --s 貓
    python 09_workflow/MRL_Hybrid_Knowledge_Base_v1.py query --mode similarity --q "哺乳類動物"
    python 09_workflow/MRL_Hybrid_Knowledge_Base_v1.py query --mode hybrid --q "貓 動物"
    python 09_workflow/MRL_Hybrid_Knowledge_Base_v1.py refine
    python 09_workflow/MRL_Hybrid_Knowledge_Base_v1.py path --from 貓 --to 生物
"""
from __future__ import annotations

import argparse
import hashlib
import json
import pathlib
import sys
import threading
import time
from collections import deque
from typing import Any, Dict, List, Optional, Tuple

_HERE = pathlib.Path(__file__).resolve().parent          # 09_workflow
_REPO_ROOT = _HERE.parent
# Import sibling modules without package plumbing (repo uses flat imports).
for _p in (str(_HERE), str(_REPO_ROOT / "03_memory" / "vector")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

# 母體源頭主權簽章 + LAW-0:單一真實來源為 09_workflow/MRL_utils.py(authority_invariance;
# 不在此重定義)。只在 MRL_utils 本身缺失時退回 ORIGIN_SIGNATURE,其餘匯入失敗一律 re-raise。
try:
    from MRL_utils import ORIGIN_SIGNATURE  # noqa: E402  單一真實來源
except ModuleNotFoundError as _exc:  # pragma: no cover - standalone fallback only
    if _exc.name != "MRL_utils":
        raise
    ORIGIN_SIGNATURE = "MrLiouWord"

# LAW-0 簽章工具:非 standalone-critical,失敗即 re-raise(不遮蔽單一來源缺陷)。
from MRL_utils import embed_signature, verify_signature  # noqa: E402
from MRL_SemanticEmbedding_Core_v1 import MRL_SemanticEmbeddingCore  # noqa: E402
from vector_store import VectorStore  # noqa: E402

_EMBED_DIM = 256
STORE_VERSION = "1.0"
_DEFAULT_STORE = _REPO_ROOT / "03_memory" / "_data" / "hybrid_kb.json"

_SEP = "\x1f"  # unit separator — 不出現在正常內容中,用於三元組雜湊


def _fact_id(subject: str, predicate: str, obj: str) -> str:
    """Deterministic id → identical (s,p,o) 冪等去重(同三元組同 id)。"""
    raw = _SEP.join((subject, predicate, obj)).encode("utf-8")
    return "fact-" + hashlib.sha1(raw).hexdigest()[:12]


def _neural_id(text: str) -> str:
    return "neural-" + hashlib.sha1((text or "").encode("utf-8")).hexdigest()[:12]


def _pred_polarity(predicate: str) -> Tuple[bool, str]:
    """(is_positive, base_predicate):剝除否定標記(not_ / 不 / 非)以偵測顯式否定對。"""
    p = predicate.strip()
    negative = p.startswith("not_") or ("不" in p) or ("非" in p)
    base = p[4:] if p.startswith("not_") else p
    base = base.replace("不", "").replace("非", "").strip(" _")
    return (not negative, base)


# ─── 符號三元組庫 ──────────────────────────────────────────────────────────────
class SymbolicKnowledgeStore:
    """(subject, predicate, object) 三元組庫 + 謂詞/實體倒排索引(精確查詢)。"""

    def __init__(self) -> None:
        self._facts: Dict[str, Dict[str, Any]] = {}
        self._by_predicate: Dict[str, set] = {}
        self._by_entity: Dict[str, set] = {}     # subject 與 object 都算實體

    def _index(self, fid: str, fact: Dict[str, Any]) -> None:
        self._by_predicate.setdefault(fact["predicate"], set()).add(fid)
        self._by_entity.setdefault(fact["subject"], set()).add(fid)
        self._by_entity.setdefault(fact["object"], set()).add(fid)

    def add(self, subject: str, predicate: str, obj: str) -> str:
        for name, val in (("subject", subject), ("predicate", predicate), ("object", obj)):
            if not isinstance(val, str) or not val.strip():
                raise ValueError(f"cannot add fact with empty {name}")
        fid = _fact_id(subject, predicate, obj)
        if fid not in self._facts:      # 冪等:同三元組不重複落庫
            fact = {
                "fact_id": fid,
                "subject": subject,
                "predicate": predicate,
                "object": obj,
                "ts_ms": int(time.time() * 1000),
                "origin_signature": ORIGIN_SIGNATURE,
            }
            self._facts[fid] = fact
            self._index(fid, fact)
        return fid

    def get(self, fact_id: str) -> Optional[Dict[str, Any]]:
        return self._facts.get(fact_id)

    def query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """精確查詢:對每個給定欄位取交集(用倒排索引);全 None → 全庫。"""
        candidate_sets: List[set] = []
        if subject is not None:
            candidate_sets.append({f for f in self._by_entity.get(subject, set())
                                   if self._facts[f]["subject"] == subject})
        if obj is not None:
            candidate_sets.append({f for f in self._by_entity.get(obj, set())
                                   if self._facts[f]["object"] == obj})
        if predicate is not None:
            candidate_sets.append(set(self._by_predicate.get(predicate, set())))
        if not candidate_sets:
            ids = list(self._facts.keys())
        else:
            ids = list(set.intersection(*candidate_sets)) if len(candidate_sets) > 1 \
                else list(candidate_sets[0])
        return [self._facts[i] for i in sorted(ids)]

    def all(self) -> List[Dict[str, Any]]:
        return [self._facts[i] for i in sorted(self._facts.keys())]

    def load_facts(self, facts: List[Dict[str, Any]]) -> None:
        for fact in facts:
            fid = fact.get("fact_id") or _fact_id(fact["subject"], fact["predicate"], fact["object"])
            self._facts[fid] = fact
            self._index(fid, fact)

    def __len__(self) -> int:
        return len(self._facts)


# ─── 神經(向量)庫 —— 薄封裝既有 embedder + VectorStore(不重造) ──────────────
class NeuralKnowledgeStore:
    """文字 → 向量(雜湊詞袋)→ 持久化 VectorStore;相似度查詢委派 VectorStore.query。"""

    def __init__(self, store_path: pathlib.Path, dim: int = _EMBED_DIM) -> None:
        self._embedder = MRL_SemanticEmbeddingCore(dim=dim)
        self._store = VectorStore(store_path=pathlib.Path(store_path))

    def add(self, doc_id: str, text: str, meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        if not text or not text.strip():
            raise ValueError("cannot add neural doc with empty text")
        vec = self._embedder.embed(text)
        payload = {"text": text, "origin_signature": ORIGIN_SIGNATURE}
        if meta:
            payload.update(meta)
        return self._store.add(doc_id, vec, payload)

    def search_similar(
        self, text: str, top_k: int = 5, min_score: float = 0.0
    ) -> List[Tuple[str, float, Dict[str, Any]]]:
        if top_k < 1:
            raise ValueError(f"top_k must be >= 1, got {top_k}")
        if not text or not text.strip():
            return []
        qvec = self._embedder.embed(text)
        return self._store.query(qvec, top_k=top_k, min_score=min_score)

    def get(self, doc_id: str) -> Optional[Dict[str, Any]]:
        return self._store.get(doc_id)

    def __len__(self) -> int:
        return len(self._store)


# ─── 映射索引:符號 id ⇄ 神經 id 雙向 ─────────────────────────────────────────
class KnowledgeMapIndex:
    def __init__(self) -> None:
        self._sym_to_neu: Dict[str, set] = {}
        self._neu_to_sym: Dict[str, set] = {}

    def link_items(self, symbolic_id: str, neural_id: str) -> None:
        self._sym_to_neu.setdefault(symbolic_id, set()).add(neural_id)
        self._neu_to_sym.setdefault(neural_id, set()).add(symbolic_id)

    def get_neural_ids(self, symbolic_id: str) -> List[str]:
        return sorted(self._sym_to_neu.get(symbolic_id, set()))

    def get_symbolic_ids(self, neural_id: str) -> List[str]:
        return sorted(self._neu_to_sym.get(neural_id, set()))

    def as_dict(self) -> Dict[str, List[str]]:
        return {sid: sorted(nids) for sid, nids in self._sym_to_neu.items()}

    def load(self, mapping: Dict[str, List[str]]) -> None:
        for sid, nids in (mapping or {}).items():
            for nid in nids:
                self.link_items(sid, nid)


# ─── 一致性管理(只讀 · 只報不刪 · rl_01/rl_15) ──────────────────────────────
class ConsistencyManager:
    def __init__(self, symbolic: SymbolicKnowledgeStore) -> None:
        self._sym = symbolic

    def contradictions(self) -> List[Dict[str, Any]]:
        """兩類矛盾:①功能性衝突(同 s,p 但 o 不同)②顯式否定對(同 s、同 o、同 base pred、極性相反)。"""
        out: List[Dict[str, Any]] = []
        facts = self._sym.all()

        # ① 功能性衝突:同 (subject, predicate) 卻有多個相異 object
        sp_to_objs: Dict[Tuple[str, str], set] = {}
        for f in facts:
            sp_to_objs.setdefault((f["subject"], f["predicate"]), set()).add(f["object"])
        for (subj, pred), objs in sp_to_objs.items():
            if len(objs) > 1:
                out.append({
                    "type": "functional_conflict",
                    "subject": subj,
                    "predicate": pred,
                    "objects": sorted(objs),
                })

        # ② 顯式否定對:同 subject、同 object、同 base predicate,但一正一負
        seen: Dict[Tuple[str, str, str], bool] = {}  # (subject, object, base) -> polarity
        for f in facts:
            pos, base = _pred_polarity(f["predicate"])
            key = (f["subject"], f["object"], base)
            if key in seen and seen[key] != pos:
                out.append({
                    "type": "negation_conflict",
                    "subject": f["subject"],
                    "object": f["object"],
                    "base_predicate": base,
                })
            else:
                seen[key] = pos
        return out

    def redundancies(self) -> List[Dict[str, Any]]:
        """冗餘:正規化(strip+lower)後相同三元組卻有相異 fact_id(如大小寫/空白差異)。"""
        norm_to_ids: Dict[Tuple[str, str, str], List[str]] = {}
        for f in self._sym.all():
            key = (f["subject"].strip().lower(),
                   f["predicate"].strip().lower(),
                   f["object"].strip().lower())
            norm_to_ids.setdefault(key, []).append(f["fact_id"])
        out: List[Dict[str, Any]] = []
        for key, ids in norm_to_ids.items():
            if len(ids) > 1:
                out.append({"type": "redundancy", "normalized": list(key),
                            "fact_ids": sorted(ids)})
        return out

    @staticmethod
    def subsumptions_note() -> str:
        # 誠實:subsumption(蘊涵/上下位)偵測需本體論階層,尚未實作;不以空回傳偽稱已完成。
        return "[待實作] subsumption detection requires an ontology hierarchy — DESIGN target, not implemented (no_proof)."


# ─── 知識圖:三元組 → 鄰接 → BFS 最短路徑 ─────────────────────────────────────
class KnowledgeGraph:
    def __init__(self, symbolic: SymbolicKnowledgeStore) -> None:
        self._adj: Dict[str, List[Tuple[str, str, str]]] = {}   # subject -> [(object, predicate, fact_id)]
        for f in symbolic.all():
            self._adj.setdefault(f["subject"], []).append(
                (f["object"], f["predicate"], f["fact_id"]))

    def path_between(self, a: str, b: str, max_depth: int = 6) -> Optional[List[Dict[str, str]]]:
        """有向 BFS 最短路徑 a→b;回傳邊列表 [{from,predicate,to,fact_id}] 或 None。"""
        if a == b:
            return []
        queue: deque = deque([(a, [])])
        visited = {a}
        while queue:
            node, path = queue.popleft()
            if len(path) >= max_depth:
                continue
            for (nxt, pred, fid) in self._adj.get(node, []):
                edge = {"from": node, "predicate": pred, "to": nxt, "fact_id": fid}
                if nxt == b:
                    return path + [edge]
                if nxt not in visited:
                    visited.add(nxt)
                    queue.append((nxt, path + [edge]))
        return None


# ─── 門面:神經符號混合知識庫 ─────────────────────────────────────────────────
class MRL_HybridKnowledgeBase:
    """符號庫 + 神經庫 + 映射索引 + 一致性 + 知識圖;精確/相似/混合查詢(執行緒安全)。"""

    def __init__(self, store_path: pathlib.Path = _DEFAULT_STORE, dim: int = _EMBED_DIM) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self._path = pathlib.Path(store_path)
        # 神經側持久化到同目錄的姊妹檔;單一 store_path 即可隔離整個 KB(便於測試)。
        self._vec_path = self._path.with_name(self._path.stem + "_vectors.json")
        self._symbolic = SymbolicKnowledgeStore()
        self._neural = NeuralKnowledgeStore(self._vec_path, dim=dim)
        self._map = KnowledgeMapIndex()
        self._lock = threading.RLock()
        self._load()

    # ── persistence(符號 + 映射;神經側由 VectorStore 自行持久化) ─────────────
    def _load(self) -> None:
        if not self._path.exists():
            return
        with self._path.open("r", encoding="utf-8") as f:
            data = json.load(f)
        if not verify_signature(data):
            # 誠實回報而非崩潰:簽章不符仍載入,但標記(rl_15 不刪、rl_09 由上層決策)。
            sys.stderr.write(
                f"⚠️  MRL_HybridKnowledgeBase: signature verify FAILED for {self._path} "
                "(loaded anyway; not deleted).\n")
        self._symbolic.load_facts(data.get("facts", []))
        self._map.load(data.get("links", {}))

    def _save(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "store_version": STORE_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "total_facts": len(self._symbolic),
            "facts": self._symbolic.all(),
            "links": self._map.as_dict(),
        }
        signed = embed_signature(payload)   # LAW-0 母體簽章
        with self._path.open("w", encoding="utf-8") as f:
            json.dump(signed, f, ensure_ascii=False, indent=2)

    # ── write ─────────────────────────────────────────────────────────────────
    def _ingest(self, subject: str, predicate: str, obj: str,
                text: Optional[str]) -> Dict[str, Any]:
        """單筆吸收(不落盤);回傳 {fact_id, neural_id?}。呼叫端負責存檔。"""
        fid = self._symbolic.add(subject, predicate, obj)
        result: Dict[str, Any] = {"fact_id": fid}
        if text and text.strip():
            nid = _neural_id(text)
            self._neural.add(nid, text, meta={"fact_id": fid})
            self._map.link_items(fid, nid)
            result["neural_id"] = nid
        return result

    def incremental_update(
        self, subject: str, predicate: str, obj: str, text: Optional[str] = None
    ) -> Dict[str, Any]:
        """新增一條三元組(符號);附 *text* 時同時進神經庫並建立映射。"""
        with self._lock:
            result = self._ingest(subject, predicate, obj, text)
            self._save()
        return result

    def integrate_knowledge(
        self, items: List[Tuple[str, str, str, Optional[str]]]
    ) -> List[Dict[str, Any]]:
        """批次吸收 (subject, predicate, object, text?);單次存檔(符號側)。"""
        out: List[Dict[str, Any]] = []
        with self._lock:
            for item in items:
                subject, predicate, obj = item[0], item[1], item[2]
                text = item[3] if len(item) > 3 else None
                out.append(self._ingest(subject, predicate, obj, text))
            self._save()
        return out

    # ── read ────────────────────────────────────────────────────────────────
    def exact_query(
        self,
        subject: Optional[str] = None,
        predicate: Optional[str] = None,
        obj: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        with self._lock:
            return self._symbolic.query(subject=subject, predicate=predicate, obj=obj)

    def similarity_query(
        self, text: str, top_k: int = 5, min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        with self._lock:
            hits = self._neural.search_similar(text, top_k=top_k, min_score=min_score)
        return [{"neural_id": nid, "score": round(float(score), 6),
                 "text": meta.get("text", ""), "fact_id": meta.get("fact_id")}
                for nid, score, meta in hits]

    def hybrid_query(self, text: str, top_k: int = 5) -> Dict[str, Any]:
        """混合查詢:符號精確(對文字內詞逐一 entity 命中)+ 神經相似,經映射索引去重。"""
        if not text or not text.strip():
            return {"exact": [], "similar": [], "linked": [], "facts": []}
        with self._lock:
            terms = [t for t in text.split() if t.strip()]
            exact: Dict[str, Dict[str, Any]] = {}
            for term in terms:
                for fact in self._symbolic.query(subject=term):
                    exact[fact["fact_id"]] = fact
                for fact in self._symbolic.query(obj=term):
                    exact[fact["fact_id"]] = fact

            similar = self._neural.search_similar(text, top_k=top_k)
            similar_out: List[Dict[str, Any]] = []
            linked: Dict[str, Dict[str, Any]] = {}
            for nid, score, meta in similar:
                similar_out.append({"neural_id": nid, "score": round(float(score), 6),
                                    "text": meta.get("text", ""),
                                    "fact_id": meta.get("fact_id")})
                for sid in self._map.get_symbolic_ids(nid):
                    fact = self._symbolic.get(sid)
                    if fact is not None:
                        linked[sid] = fact

        # 合併去重(符號精確 ∪ 相似命中所連結之符號事實),以 fact_id 為鍵。
        merged: Dict[str, Dict[str, Any]] = dict(exact)
        merged.update(linked)
        return {
            "exact": [exact[k] for k in sorted(exact)],
            "similar": similar_out,
            "linked": [linked[k] for k in sorted(linked)],
            "facts": [merged[k] for k in sorted(merged)],
        }

    def refine_knowledge(self) -> Dict[str, Any]:
        """一致性精煉:回報矛盾/冗餘;**只報不刪**(rl_01/rl_15,前後 len 不變)。"""
        with self._lock:
            cm = ConsistencyManager(self._symbolic)
            return {
                "contradictions": cm.contradictions(),
                "redundancies": cm.redundancies(),
                "subsumptions_note": ConsistencyManager.subsumptions_note(),
                "total_facts": len(self._symbolic),
                "mutated": False,   # 保證只讀
            }

    def graph(self) -> KnowledgeGraph:
        with self._lock:
            return KnowledgeGraph(self._symbolic)

    def path_between(self, a: str, b: str, max_depth: int = 6) -> Optional[List[Dict[str, str]]]:
        return self.graph().path_between(a, b, max_depth=max_depth)

    def __len__(self) -> int:
        with self._lock:
            return len(self._symbolic)


# ─── CLI ──────────────────────────────────────────────────────────────────────

def _cmd_add(args: argparse.Namespace) -> None:
    kb = MRL_HybridKnowledgeBase()
    result = kb.incremental_update(args.s, args.p, args.o, text=args.text)
    print(f"✅ added  fact_id={result['fact_id']}"
          + (f"  neural_id={result['neural_id']}" if "neural_id" in result else "")
          + f"  total={len(kb)}")


def _cmd_query(args: argparse.Namespace) -> None:
    kb = MRL_HybridKnowledgeBase()
    if args.mode == "exact":
        out: Any = kb.exact_query(subject=args.s, predicate=args.p, obj=args.o)
    elif args.mode == "similarity":
        if not args.q:
            print(json.dumps({"error": "similarity mode requires --q"}, ensure_ascii=False))
            raise SystemExit(1)
        out = kb.similarity_query(args.q, top_k=args.k)
    else:  # hybrid
        if not args.q:
            print(json.dumps({"error": "hybrid mode requires --q"}, ensure_ascii=False))
            raise SystemExit(1)
        out = kb.hybrid_query(args.q, top_k=args.k)
    print(json.dumps(out, ensure_ascii=False, indent=2))


def _cmd_refine(_args: argparse.Namespace) -> None:
    kb = MRL_HybridKnowledgeBase()
    print(json.dumps(kb.refine_knowledge(), ensure_ascii=False, indent=2))


def _cmd_path(args: argparse.Namespace) -> None:
    kb = MRL_HybridKnowledgeBase()
    path = kb.path_between(getattr(args, "from"), args.to)
    if path is None:
        print(json.dumps({"path": None, "reachable": False}, ensure_ascii=False, indent=2))
    else:
        print(json.dumps({"path": path, "reachable": True, "hops": len(path)},
                         ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MRL_HybridKnowledgeBase — 神經符號混合知識庫")
    sub = p.add_subparsers(dest="cmd", required=True)

    a = sub.add_parser("add", help="Add a (subject, predicate, object) fact [+ optional text]")
    a.add_argument("--s", required=True, help="subject")
    a.add_argument("--p", required=True, help="predicate")
    a.add_argument("--o", required=True, help="object")
    a.add_argument("--text", default=None, help="free text for the neural side (optional)")

    q = sub.add_parser("query", help="exact / similarity / hybrid query")
    q.add_argument("--mode", choices=("exact", "similarity", "hybrid"), default="hybrid")
    q.add_argument("--s", default=None, help="subject (exact)")
    q.add_argument("--p", default=None, help="predicate (exact)")
    q.add_argument("--o", default=None, help="object (exact)")
    q.add_argument("--q", default=None, help="query text (similarity / hybrid)")
    q.add_argument("--k", type=int, default=5)

    sub.add_parser("refine", help="Consistency report (contradictions / redundancies) — report only")

    pa = sub.add_parser("path", help="Shortest symbolic path between two entities (BFS)")
    pa.add_argument("--from", required=True, help="start entity")
    pa.add_argument("--to", required=True, help="end entity")

    return p


def main() -> None:
    args = _build_argparser().parse_args()
    {"add": _cmd_add, "query": _cmd_query, "refine": _cmd_refine, "path": _cmd_path}[args.cmd](args)


if __name__ == "__main__":
    main()
