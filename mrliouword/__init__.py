"""
mrliouword — 唯一權威母體系統 Python 套件
Mrliouword: The One Authoritative Mother System

此套件是 Mrliouword 系統的 Python 公開介面（canonical namespace）。
所有新程式應從此套件匯入，而非直接使用 09_workflow/ 內部模組。

舊有 MRL_* 模組保留作為相容別名，遷移路徑請參考：
  docs/mrliouword_migration_guide_v1.md

版本與命名規範：
  產品：Mrliouword
  Python namespace：mrliouword
  CLI：mrliouword
  環境變數前綴：MRLIOUWORD_（向後相容 MRL_）
  API base path：/api/v1
  服務名稱：mrliouword-*
"""

from __future__ import annotations

__version__ = "1.0.0"
__product__ = "Mrliouword"
__origin_signature__ = "MrLiouWord"

# ── Public surface ─────────────────────────────────────────────────────────────
from mrliouword.schemas import (
    ORIGIN_SIGNATURE,
    TraceEvent,
    MemoryEntry,
    HealthStatus,
    ErrorResponse,
    embed_signature,
    verify_signature,
)
from mrliouword.config import MrliouwordConfig
from mrliouword.memory import MemoryStore
from mrliouword.trace import Tracer
from mrliouword.api import HealthProbe

__all__ = [
    "__version__",
    "__product__",
    "__origin_signature__",
    "ORIGIN_SIGNATURE",
    "TraceEvent",
    "MemoryEntry",
    "HealthStatus",
    "ErrorResponse",
    "embed_signature",
    "verify_signature",
    "MrliouwordConfig",
    "MemoryStore",
    "Tracer",
    "HealthProbe",
]
