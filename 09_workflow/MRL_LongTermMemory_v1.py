#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_LongTermMemory_v1.py — 長期記憶引擎 (remember / recall)
origin_signature: MrLiouWord
layer: L5 MEMORY / RETRIEVAL
group: Y=3 FlowAgentRuntime

把母體既有的兩塊組合成「對話可用的長期記憶」,零新依賴、不改既有行為:
  - 文字 → 向量 : MRL_SemanticEmbeddingCore.embed
                  (09_workflow/MRL_SemanticEmbedding_Core_v1.py)
  - 向量 存/查   : VectorStore.add / query
                  (03_memory/vector/vector_store.py，持久化 JSON)

對外只暴露:
  remember(session_id, role, content)         -> stored entry
  recall(query_text, top_k)                   -> [{content, score, session_id, role, ts_ms, mem_id}]
  recall_as_context(query_text, top_k)        -> [conversation-compatible system messages]

誠實標註:embedder 為雜湊化詞袋 + 餘弦(檢索/統計,非神經嵌入、非生成模型)。
Additive：VectorStore / embedder / 對話流程皆沿用不改,本模組只做組合。

CLI
---
    python 09_workflow/MRL_LongTermMemory_v1.py remember --sid s1 --role user --content "你好"
    python 09_workflow/MRL_LongTermMemory_v1.py recall --query "打招呼" --k 3
"""
from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import uuid
from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"

_HERE = pathlib.Path(__file__).resolve().parent          # 09_workflow
_REPO_ROOT = _HERE.parent
# Import sibling modules without package plumbing (repo uses flat imports).
for _p in (str(_HERE), str(_REPO_ROOT / "03_memory" / "vector")):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from MRL_SemanticEmbedding_Core_v1 import MRL_SemanticEmbeddingCore  # noqa: E402
from vector_store import VectorStore  # noqa: E402

_EMBED_DIM = 256
_DEFAULT_STORE = _REPO_ROOT / "03_memory" / "_data" / "longterm_memory.json"


class MRL_LongTermMemory:
    """長期記憶:embedder + 持久向量庫,對外 remember / recall。"""

    def __init__(
        self,
        store_path: pathlib.Path = _DEFAULT_STORE,
        dim: int = _EMBED_DIM,
    ) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self._embedder = MRL_SemanticEmbeddingCore(dim=dim)
        self._store = VectorStore(store_path=pathlib.Path(store_path))

    # write
    def remember(self, session_id: str, role: str, content: str) -> Dict[str, Any]:
        """Embed *content* and persist it as a recallable memory. Returns the stored entry."""
        if not content or not content.strip():
            raise ValueError("cannot remember empty content")
        vec = self._embedder.embed(content)
        mem_id = f"mem-{session_id}-{uuid.uuid4().hex[:12]}"
        meta = {
            "content": content,
            "session_id": session_id,
            "role": role,
            "ts_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        return self._store.add(mem_id, vec, meta)

    # read
    def recall(
        self,
        query_text: str,
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """Return the memories most semantically relevant to *query_text*."""
        if not query_text or not query_text.strip():
            return []
        qvec = self._embedder.embed(query_text)
        hits = self._store.query(qvec, top_k=top_k, min_score=min_score)
        out: List[Dict[str, Any]] = []
        for doc_id, score, meta in hits:
            out.append({
                "content": meta.get("content", ""),
                "score": round(float(score), 6),
                "session_id": meta.get("session_id"),
                "role": meta.get("role"),
                "ts_ms": meta.get("ts_ms"),
                "mem_id": doc_id,
            })
        return out

    def recall_as_context(
        self,
        query_text: str,
        top_k: int = 3,
        min_score: float = 0.1,
    ) -> List[Dict[str, Any]]:
        """
        Recall memories and wrap them as ConversationSession-compatible ``system``
        messages, ready to prepend to a conversation before ``context_manager.fit()``.
        """
        msgs: List[Dict[str, Any]] = []
        for h in self.recall(query_text, top_k=top_k, min_score=min_score):
            msgs.append({
                "role": "system",
                "content": f"[long-term memory] {h['content']}",
                "ts_ms": h.get("ts_ms"),
                "origin_signature": ORIGIN_SIGNATURE,
                "meta": {
                    "is_recalled_memory": True,
                    "score": h["score"],
                    "mem_id": h["mem_id"],
                },
            })
        return msgs

    def __len__(self) -> int:
        return len(self._store)


def _cmd_remember(args: argparse.Namespace) -> None:
    ltm = MRL_LongTermMemory()
    entry = ltm.remember(args.sid, args.role, args.content)
    print(f"✅ remembered  mem_id={entry['id']}  total={len(ltm)}")


def _cmd_recall(args: argparse.Namespace) -> None:
    ltm = MRL_LongTermMemory()
    hits = ltm.recall(args.query, top_k=args.k)
    print(json.dumps(hits, ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="MRL_LongTermMemory — remember / recall")
    sub = p.add_subparsers(dest="cmd", required=True)

    r = sub.add_parser("remember", help="Store a message into long-term memory")
    r.add_argument("--sid", required=True)
    r.add_argument("--role", required=True)
    r.add_argument("--content", required=True)

    q = sub.add_parser("recall", help="Recall relevant memories")
    q.add_argument("--query", required=True)
    q.add_argument("--k", type=int, default=5)

    return p


def main() -> None:
    args = _build_argparser().parse_args()
    {"remember": _cmd_remember, "recall": _cmd_recall}[args.cmd](args)


if __name__ == "__main__":
    main()
