"""
mrliouword.api — health/readiness 與輕量 API 探針

此模組提供 Mrliouword 服務的健康檢查與就緒探針介面，
以及發起 API 請求所需的基礎工具。

完整 API Gateway 實作請參考 09_workflow/api_gateway.py。
此模組提供的是可獨立測試的探針層（不需要啟動 HTTP server）。

設計原則：
- HealthProbe.check() 不依賴外部 HTTP server，可在任意環境執行
- 所有回應使用 mrliouword.schemas.HealthStatus（統一格式）
- API base path：/api/v1（符合 Mrliouword 命名規範）
"""

from __future__ import annotations

import pathlib
import sys
import time
from typing import Any, Dict, Optional

from mrliouword.schemas import HealthStatus, ORIGIN_SIGNATURE

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_WORKFLOW_DIR = _REPO_ROOT / "09_workflow"
if str(_WORKFLOW_DIR) not in sys.path:
    sys.path.insert(0, str(_WORKFLOW_DIR))

_MERKLE_DIR = _REPO_ROOT / "03_memory" / "merkle"
if str(_MERKLE_DIR) not in sys.path:
    sys.path.insert(0, str(_MERKLE_DIR))

_VECTOR_DIR = _REPO_ROOT / "03_memory" / "vector"
if str(_VECTOR_DIR) not in sys.path:
    sys.path.insert(0, str(_VECTOR_DIR))

# API base path（Mrliouword 命名規範）
API_BASE_PATH = "/api/v1"
PRODUCT_VERSION = "1.0.0"


class HealthProbe:
    """
    Mrliouword 健康探針。

    直接檢查核心子系統（config, memory chain, vector store）是否可用，
    無需啟動 HTTP server。

    範例::

        probe = HealthProbe()
        status = probe.check()
        print(status.status)      # "ok" | "degraded" | "error"
        print(status.subsystems)  # {"config": "ok", "memory_chain": "ok", ...}
    """

    def check(self) -> HealthStatus:
        """
        執行健康檢查，回傳 HealthStatus。
        各子系統獨立探測；單項失敗不影響其他項目。
        """
        subsystems: Dict[str, str] = {}

        # 1. Config subsystem
        try:
            from mrliouword.config import MrliouwordConfig
            cfg = MrliouwordConfig()
            cfg.get("system.name")
            subsystems["config"] = "ok"
        except Exception as exc:
            subsystems["config"] = f"error: {exc}"

        # 2. Memory chain subsystem
        try:
            from memory_chain import MerkleChain
            chain = MerkleChain(data_dir=_REPO_ROOT / "data" / "health_probe_tmp")
            chain.verify()
            subsystems["memory_chain"] = "ok"
        except Exception as exc:
            subsystems["memory_chain"] = f"error: {exc}"

        # 3. Vector store subsystem
        try:
            from vector_store import VectorStore
            VectorStore()
            subsystems["vector_store"] = "ok"
        except Exception as exc:
            subsystems["vector_store"] = f"error: {exc}"

        # 4. Schema validation subsystem
        try:
            from mrliouword.schemas import embed_signature, verify_signature
            sample = embed_signature({"test": "ping"})
            assert verify_signature(sample)
            subsystems["schemas"] = "ok"
        except Exception as exc:
            subsystems["schemas"] = f"error: {exc}"

        all_ok = all(v == "ok" for v in subsystems.values())
        any_error = any(v.startswith("error") for v in subsystems.values())

        if all_ok:
            status = "ok"
        elif any_error:
            status = "degraded"
        else:
            status = "ok"

        return HealthStatus(
            status=status,
            version=PRODUCT_VERSION,
            subsystems=subsystems,
        )

    def readiness(self) -> bool:
        """
        就緒探針（readiness probe）。
        返回 True 表示服務已就緒可接收流量，False 表示尚未就緒。
        """
        status = self.check()
        return status.ok


def build_health_response(probe: Optional[HealthProbe] = None) -> Dict[str, Any]:
    """
    建立符合 /api/v1/health 格式的回應 dict。
    可傳入自訂 probe 以覆蓋預設行為（方便測試）。
    """
    if probe is None:
        probe = HealthProbe()
    status = probe.check()
    return status.to_dict()
