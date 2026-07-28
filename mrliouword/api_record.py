"""MRL API 紀錄模組 (MRL_ApiRecord) — 母體 API 呼叫 / 遙測紀錄帳本。

origin_signature: MrLiouWord ｜ product: MrliouAI ｜ Additive-Only。

職責：
  - record(...)  記錄每一次 API 呼叫（method / path / status / latency / trace_id / 來源），
                 以 JSONL 落地為帳本（append-only），線程安全。
  - tail(n)      讀回最近 n 筆紀錄。
  - summary()    聚合：總筆數、依 path / status / method 分佈。
  - clear()      清空帳本（測試/維運用）。

零外部依賴（Python 標準庫）。帳本路徑：環境變數 MRL_API_RECORD_PATH，
預設 data/mrl_api_records.jsonl。
"""
from __future__ import annotations

import json
import os
import pathlib
import threading
import time
from typing import Any

ORIGIN_SIGNATURE = "MrLiouWord"
PRODUCT = "MrliouAI"
SOURCE_OWNER = "Mrliou"
MRL_KIND = "MRL_ApiRecord"

_REPO = pathlib.Path(__file__).resolve().parent.parent
_LOCK = threading.Lock()
_counter = 0


def ledger_path() -> pathlib.Path:
    """帳本檔路徑（可由 MRL_API_RECORD_PATH 覆寫）。"""
    return pathlib.Path(
        os.environ.get("MRL_API_RECORD_PATH", str(_REPO / "data" / "mrl_api_records.jsonl"))
    )


def _next_trace_id() -> str:
    """防碰撞唯一識別：毫秒時間前綴 + 單調序號。"""
    global _counter
    _counter += 1
    return f"MRL-API-{int(time.time() * 1000):x}-{_counter:06x}"


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime()) + "Z"


def record(
    *,
    method: str,
    path: str,
    status: int,
    latency_ms: float | None = None,
    kind: str = "api_call",
    meta: dict[str, Any] | None = None,
    trace_id: str | None = None,
) -> dict[str, Any]:
    """記錄一筆 API 呼叫並落地帳本；回傳寫入的紀錄物件。

    任何 I/O 失敗都不得中斷呼叫端 —— 例外被吞掉但仍回傳紀錄物件。
    """
    entry: dict[str, Any] = {
        "origin_signature": ORIGIN_SIGNATURE,
        "product": PRODUCT,
        "source_owner": SOURCE_OWNER,
        "mrl_kind": MRL_KIND,
        "kind": kind,
        "trace_id": trace_id or _next_trace_id(),
        "ts": _now_iso(),
        "method": method,
        "path": path,
        "status": int(status),
        "latency_ms": round(latency_ms, 2) if isinstance(latency_ms, (int, float)) else None,
        "meta": meta or {},
    }
    line = json.dumps(entry, ensure_ascii=False)
    p = ledger_path()
    try:
        with _LOCK:
            p.parent.mkdir(parents=True, exist_ok=True)
            with p.open("a", encoding="utf-8") as fh:
                fh.write(line + "\n")
    except Exception:  # noqa: BLE001 — 紀錄失敗絕不影響主流程
        pass
    return entry


def _read_lines() -> list[str]:
    p = ledger_path()
    if not p.exists():
        return []
    with _LOCK:
        return p.read_text(encoding="utf-8").splitlines()


def tail(n: int = 50) -> list[dict[str, Any]]:
    """回讀最近 n 筆紀錄（最舊在前）。"""
    n = max(1, int(n))
    out: list[dict[str, Any]] = []
    for ln in _read_lines()[-n:]:
        try:
            out.append(json.loads(ln))
        except Exception:  # noqa: BLE001
            continue
    return out


def summary() -> dict[str, Any]:
    """聚合視圖：總數 + 依 path / status / method 分佈。"""
    by_path: dict[str, int] = {}
    by_status: dict[str, int] = {}
    by_method: dict[str, int] = {}
    total = 0
    for ln in _read_lines():
        try:
            e = json.loads(ln)
        except Exception:  # noqa: BLE001
            continue
        total += 1
        by_path[e.get("path", "?")] = by_path.get(e.get("path", "?"), 0) + 1
        s = str(e.get("status", "?"))
        by_status[s] = by_status.get(s, 0) + 1
        m = e.get("method", "?")
        by_method[m] = by_method.get(m, 0) + 1
    return {
        "origin_signature": ORIGIN_SIGNATURE,
        "product": PRODUCT,
        "mrl_kind": MRL_KIND,
        "total": total,
        "by_path": by_path,
        "by_status": by_status,
        "by_method": by_method,
    }


def clear() -> None:
    """清空帳本（測試/維運）。"""
    p = ledger_path()
    with _LOCK:
        if p.exists():
            p.unlink()
