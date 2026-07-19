"""
mrliouword.memory — 儲存、重建、恢復與資料保留介面

提供 Mrliouword 正式命名的記憶層介面，整合：
- 03_memory/merkle/memory_chain.py（Merkle chain 持久化）
- 03_memory/vector/vector_store.py（語意向量搜尋）

設計原則：
- MemoryStore.store() 同時寫入 chain（不可變）與 vector store（可搜尋）
- 所有條目均攜帶 origin_signature 與 schema_version
- 支援 restore(entry_id) 取回任意歷史條目
"""

from __future__ import annotations

import pathlib
import sys
import uuid
from typing import Any, Dict, List, Optional

from mrliouword.schemas import MemoryEntry, ORIGIN_SIGNATURE, embed_signature

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# 加入 merkle 路徑
_MERKLE_DIR = _REPO_ROOT / "03_memory" / "merkle"
if str(_MERKLE_DIR) not in sys.path:
    sys.path.insert(0, str(_MERKLE_DIR))

# 加入 vector 路徑
_VECTOR_DIR = _REPO_ROOT / "03_memory" / "vector"
if str(_VECTOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VECTOR_DIR))

from memory_chain import MerkleChain  # noqa: E402
from vector_store import VectorStore  # noqa: E402


class MemoryStore:
    """
    Mrliouword 記憶儲存器。

    同時維護：
    - Merkle chain（append-only，不可篡改，用於審計與重建）
    - Vector store（語意搜尋，用於快速相似度查詢）

    data_dir 預設為 data/memory/mrliouword。

    範例::

        store = MemoryStore()
        entry_id = store.store({"type": "runtime_event", "content": "..."}, tags=["L7"])
        results = store.search([0.1, 0.2, ...], top_k=5)
        entry = store.restore(entry_id)
    """

    def __init__(
        self,
        data_dir: Optional[pathlib.Path] = None,
    ) -> None:
        if data_dir is None:
            data_dir = _REPO_ROOT / "data" / "memory" / "mrliouword"
        self._data_dir = pathlib.Path(data_dir)
        self._data_dir.mkdir(parents=True, exist_ok=True)

        self._chain = MerkleChain(data_dir=self._data_dir / "chain")
        self._vector = VectorStore(store_path=self._data_dir / "vectors.json")

    # ── 核心介面 ───────────────────────────────────────────────────────────────

    def store(
        self,
        content: Dict[str, Any],
        *,
        entry_id: Optional[str] = None,
        entry_type: str = "particle",
        tags: Optional[List[str]] = None,
        layer: str = "L6",
        embedding: Optional[List[float]] = None,
    ) -> str:
        """
        儲存記憶條目至 chain 與（可選）vector store。

        Parameters
        ----------
        content:
            要儲存的內容（任意 dict）。
        entry_id:
            唯一識別碼（預設自動生成 UUID）。
        entry_type:
            條目類型標籤（particle / event / trace / fact 等）。
        tags:
            附加標籤列表。
        layer:
            MRL 層級（L0–L7 等）。
        embedding:
            若提供，同時寫入 vector store 以支援語意搜尋。

        Returns
        -------
        str:
            entry_id（可用於後續 restore）。
        """
        eid = entry_id or str(uuid.uuid4())
        entry = MemoryEntry(
            entry_id=eid,
            content=content,
            entry_type=entry_type,
            prev_hash=self._chain.head,
            tags=tags or [],
            layer=layer,
            origin_signature=ORIGIN_SIGNATURE,
        )
        signed = embed_signature(entry.to_dict())
        self._chain.commit(
            payload=signed,
            entry_id=eid,
            tags=[entry_type, layer] + (tags or []),
            layer=layer,
            meta={"product": "Mrliouword", "origin_signature": ORIGIN_SIGNATURE},
        )
        if embedding is not None:
            self._vector.add(eid, embedding, meta={"entry_type": entry_type, "layer": layer})
        return eid

    def restore(self, entry_id: str) -> Optional[Dict[str, Any]]:
        """
        恢復指定 entry_id 的記憶條目。
        返回完整記錄（含 origin_signature 與 merkle hash）。
        """
        for raw in self._chain.read_all():
            if raw.get("entry_id") == entry_id:
                return raw.get("payload", raw)
        return None

    def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        min_score: float = 0.0,
    ) -> List[Dict[str, Any]]:
        """
        語意搜尋（需要 embedding）。
        """
        return self._vector.query(query_embedding, top_k=top_k, min_score=min_score)

    def verify(self) -> bool:
        """驗證 Merkle chain 完整性。"""
        ok, _errors = self._chain.verify()
        return ok

    def list_entries(self, limit: int = 50) -> List[Dict[str, Any]]:
        """列出最近 N 筆記錄（entry_id + timestamp + entry_type）。"""
        all_raw = self._chain.read_all()
        result = []
        for raw in reversed(all_raw[-limit:]):
            payload = raw.get("payload", {})
            result.append({
                "entry_id": raw.get("entry_id", ""),
                "timestamp_ms": raw.get("timestamp_ms", 0),
                "entry_type": payload.get("entry_type", ""),
                "layer": raw.get("layer", ""),
                "merkle": raw.get("merkle", ""),
            })
        return result

    @property
    def size(self) -> int:
        """鏈上條目總數。"""
        return len(self._chain.read_all())
