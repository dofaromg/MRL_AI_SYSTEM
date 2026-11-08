"""
mrliouword.trace — 結構化事件、correlation/trace ID 傳遞

提供 Mrliouword 正式命名的追蹤介面，底層使用
03_memory/merkle/memory_chain.py 的 MerkleChain 作為持久化機制。

設計原則：
- 每個 TraceEvent 都有 trace_id（新）與 correlation_id（跨服務關聯）
- 追蹤記錄以 append-only 方式寫入，不可修改或刪除
- 所有記錄均攜帶 origin_signature，可驗證來源
"""

from __future__ import annotations

import pathlib
import sys
import tempfile
from typing import Any, Dict, List, Optional

from mrliouword.schemas import TraceEvent, ORIGIN_SIGNATURE, embed_signature

# 將 03_memory/merkle 加入 sys.path
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_MERKLE_DIR = _REPO_ROOT / "03_memory" / "merkle"
if str(_MERKLE_DIR) not in sys.path:
    sys.path.insert(0, str(_MERKLE_DIR))

from memory_chain import MerkleChain  # noqa: E402


class Tracer:
    """
    Mrliouword 結構化追蹤器。

    將 TraceEvent 持久化寫入 Merkle chain，並提供查詢介面。
    data_dir 預設為 data/traces/mrliouword（可使用 tempfile 在測試中覆蓋）。

    範例::

        tracer = Tracer()
        event = TraceEvent(event_type="runtime.start", payload={"module": "flowcore"})
        entry = tracer.emit(event)
        recent = tracer.recent(limit=10)
    """

    def __init__(
        self,
        data_dir: Optional[pathlib.Path] = None,
    ) -> None:
        if data_dir is None:
            data_dir = _REPO_ROOT / "data" / "traces" / "mrliouword"
        self._data_dir = pathlib.Path(data_dir)
        self._chain = MerkleChain(data_dir=self._data_dir)

    def emit(
        self,
        event: TraceEvent,
        *,
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        發送追蹤事件，寫入 Merkle chain。

        Parameters
        ----------
        event:
            TraceEvent 物件。
        correlation_id:
            跨服務關聯 ID（覆蓋 event.correlation_id）。

        Returns
        -------
        dict:
            已提交的 ChainEntry（含 merkle hash、entry_id）。
        """
        if correlation_id is not None:
            event = TraceEvent(
                event_type=event.event_type,
                payload=event.payload,
                trace_id=event.trace_id,
                correlation_id=correlation_id,
                timestamp_ms=event.timestamp_ms,
                layer=event.layer,
                origin_signature=event.origin_signature,
                schema_version=event.schema_version,
            )
        payload = embed_signature(event.to_dict())
        entry = self._chain.commit(
            payload=payload,
            entry_id=event.trace_id,
            tags=["mrliouword", event.event_type, event.layer],
            layer=event.layer,
            meta={"product": "Mrliouword", "origin_signature": ORIGIN_SIGNATURE},
        )
        return {
            "entry_id": entry.entry_id,
            "merkle": entry.merkle,
            "timestamp_ms": entry.timestamp_ms,
            "event_type": event.event_type,
            "trace_id": event.trace_id,
        }

    def recent(self, limit: int = 20) -> List[Dict[str, Any]]:
        """
        回傳最近 N 筆追蹤記錄（最新在前）。
        """
        all_entries = self._chain.read_all()
        return [
            {
                "entry_id": e.get("entry_id", ""),
                "merkle": e.get("merkle", ""),
                "timestamp_ms": e.get("timestamp_ms", 0),
                "event_type": e.get("payload", {}).get("event_type", ""),
                "layer": e.get("layer", "L7"),
            }
            for e in reversed(all_entries[-limit:])
        ]

    def verify(self) -> bool:
        """驗證整條 Merkle chain 完整性。"""
        ok, _msg = self._chain.verify()
        return ok

    @property
    def head(self) -> str:
        """當前 chain head（最新 merkle hash）。"""
        return self._chain.head
