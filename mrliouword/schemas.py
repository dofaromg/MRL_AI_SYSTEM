"""
mrliouword.schemas — 權威資料模型、版本、錯誤模型與相容規則

此模組是 Mrliouword 系統所有資料契約的唯一真實來源（Single Source of Truth）。
其他模組應從此處匯入型別定義，而非重複定義相同資料結構。

設計原則：
- 所有對外契約均有 schema_version 欄位
- 錯誤回應格式一致（error_code, message, request_id, timestamp_ms）
- LAW-0 簽章相容（embed_signature / verify_signature 與 MRL_utils.py 位元相容）
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional

# ── 權威產品簽章 ──────────────────────────────────────────────────────────────
ORIGIN_SIGNATURE: str = "MrLiouWord"
SCHEMA_VERSION: str = "1.0"
PRODUCT_NAME: str = "Mrliouword"


# ── LAW-0 簽章工具（與 09_workflow/MRL_utils.py 位元相容） ────────────────────

def _compact_json(obj: Dict[str, Any]) -> str:
    """等價 JS JSON.stringify：compact、ensure_ascii=False、保留插入序。"""
    return json.dumps(obj, separators=(",", ":"), ensure_ascii=False)


def embed_signature(
    obj: Dict[str, Any],
    sig: str = ORIGIN_SIGNATURE,
) -> Dict[str, Any]:
    """
    非破壞性地嵌入 LAW-0 母體簽章。
    新增 _signature 與 _sig_hash = sha256(sig + ":" + compact_json(obj))。
    與 09_workflow/MRL_utils.py embed_signature 位元相容。
    """
    if not isinstance(obj, dict):
        raise TypeError("embed_signature: obj must be a plain dict")
    base = _compact_json(obj)
    sig_hash = hashlib.sha256((sig + ":" + base).encode("utf-8")).hexdigest()
    return {**obj, "_signature": sig, "_sig_hash": sig_hash}


def verify_signature(
    obj: Dict[str, Any],
    sig: str = ORIGIN_SIGNATURE,
) -> bool:
    """
    驗證 LAW-0 簽章。去除 _signature/_sig_hash 後重算，與存儲值比較。
    """
    if not isinstance(obj, dict):
        return False
    stored_hash = obj.get("_sig_hash")
    stored_sig = obj.get("_signature")
    if stored_hash is None or stored_sig != sig:
        return False
    stripped = {k: v for k, v in obj.items() if k not in ("_signature", "_sig_hash")}
    base = _compact_json(stripped)
    expected = hashlib.sha256((sig + ":" + base).encode("utf-8")).hexdigest()
    return expected == stored_hash


# ── 核心資料模型 ──────────────────────────────────────────────────────────────

@dataclass
class TraceEvent:
    """
    結構化追蹤事件（runtime → trace 通用記錄格式）。
    schema_version: 用於向後相容遷移。
    """
    event_type: str
    payload: Dict[str, Any]
    trace_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    correlation_id: Optional[str] = None
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    layer: str = "L7"
    origin_signature: str = ORIGIN_SIGNATURE
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TraceEvent":
        return cls(
            event_type=data["event_type"],
            payload=data.get("payload", {}),
            trace_id=data.get("trace_id", str(uuid.uuid4())),
            correlation_id=data.get("correlation_id"),
            timestamp_ms=data.get("timestamp_ms", int(time.time() * 1000)),
            layer=data.get("layer", "L7"),
            origin_signature=data.get("origin_signature", ORIGIN_SIGNATURE),
            schema_version=data.get("schema_version", SCHEMA_VERSION),
        )


@dataclass
class MemoryEntry:
    """
    記憶儲存條目（記憶層統一記錄格式）。
    prev_hash：前向鏈結（Merkle chain）。
    schema_version: 用於向後相容遷移。
    """
    entry_id: str
    content: Dict[str, Any]
    entry_type: str = "particle"
    prev_hash: str = "0" * 64
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    tags: List[str] = field(default_factory=list)
    layer: str = "L6"
    origin_signature: str = ORIGIN_SIGNATURE
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class HealthStatus:
    """
    /health 回應格式（統一錯誤格式的健康檢查子集）。
    """
    status: str  # "ok" | "degraded" | "error"
    version: str
    product: str = PRODUCT_NAME
    origin_signature: str = ORIGIN_SIGNATURE
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    subsystems: Dict[str, str] = field(default_factory=dict)
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

    @property
    def ok(self) -> bool:
        return self.status == "ok"


@dataclass
class ErrorResponse:
    """
    統一錯誤回應格式（所有 API 端點的錯誤均使用此格式）。
    """
    error_code: str
    message: str
    request_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_ms: int = field(default_factory=lambda: int(time.time() * 1000))
    detail: Optional[Dict[str, Any]] = None
    schema_version: str = SCHEMA_VERSION

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


# ── 相容性別名（遷移用） ───────────────────────────────────────────────────────
# 舊程式使用 from mrliouword.schemas import MRL_ORIGIN_SIGNATURE 仍可正常運作
MRL_ORIGIN_SIGNATURE = ORIGIN_SIGNATURE
