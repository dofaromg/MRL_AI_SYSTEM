"""test_MRL_manus_logs_route_v1.py — /__manus__/logs 除錯日誌接收端點
origin_signature: MrLiouWord

背景：前端內嵌除錯收集器會定期 POST 除錯日誌（consoleLogs / networkRequests /
uiEvents）至 /__manus__/logs。此測試驗證 Cloudflare Worker (src/mrl_worker.js)
正確攔截該路由、以 MRL 母體結構化封裝、蓋 origin_signature 追蹤標記並回傳
200 { success: true, origin: "MrLiouWord" }，且 CORS / preflight 正確設置。

註：Worker 為 JS（ES Modules），本倉庫測試慣例以字串斷言檢查 JS 原始碼；
    此檔沿用同一慣例（見 tests/test_MRL_product_entry_ui.py）。
    當下狀態（沙盒靜態檢查）：驗證路由邏輯存在於原始碼；真實邊緣回應待實機
    Cloudflare 部署驗收。
"""
from __future__ import annotations

import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
WORKER_PATH = REPO / "src" / "mrl_worker.js"


def worker() -> str:
    return WORKER_PATH.read_text(encoding="utf-8")


# ── 1. 路由攔截：pathname + method 條件 ───────────────────────────────────────

def test_worker_intercepts_manus_logs_path():
    """必須攔截 pathname === "/__manus__/logs"。"""
    assert '"/__manus__/logs"' in worker(), "缺少 /__manus__/logs 路由攔截"


def test_worker_manus_logs_requires_post():
    """僅在 POST 方法時處理該路由。"""
    w = worker()
    assert 'request.method === "POST"' in w, "缺少 POST 方法判斷"


# ── 2. 安全解析 request.json() ────────────────────────────────────────────────

def test_worker_parses_json_safely():
    """必須以 await request.json() 解析，並以 try/catch 安全處理非法 JSON。"""
    w = worker()
    assert "await request.json()" in w, "缺少 await request.json() 解析"
    assert "try" in w and "catch" in w, "缺少 try/catch 安全解析"
    assert "MRL_INVALID_JSON" in w, "非法 JSON 應誠實回錯，不得謊報 success"


def test_worker_handles_expected_log_fields():
    """必須認得 consoleLogs / networkRequests / uiEvents 三種日誌欄位。"""
    w = worker()
    for field in ("consoleLogs", "networkRequests", "uiEvents"):
        assert field in w, f"缺少對日誌欄位 {field} 的處理"


# ── 3. MRL 結構化封裝與 origin_signature 追蹤 ────────────────────────────────

def test_worker_wraps_with_origin_signature():
    """依 MRL 架構結構化封裝，蓋 origin_signature 追蹤標記。"""
    w = worker()
    assert "MrLiouWord" in w, "缺少 origin_signature: MrLiouWord"
    assert "wrapManusLogs" in w, "缺少 MRL 結構化封裝函式 wrapManusLogs"
    assert "MRL_ManusDebugLogPacket" in w, "缺少 MRL 母體封包類別標記"
    assert "x-mrl-origin-signature" in w, "缺少 origin_signature 追蹤標頭"


# ── 4. 成功回應：200 + { success: true, origin: "MrLiouWord" } ────────────────

def test_worker_success_response_shape():
    """成功回傳 { success: true, origin: "MrLiouWord" }。"""
    w = worker()
    assert "success: true" in w, "成功回應需含 success: true"
    assert 'origin: ORIGIN_SIGNATURE' in w or 'origin: "MrLiouWord"' in w, (
        "成功回應需含 origin: MrLiouWord"
    )


# ── 5. CORS / preflight ──────────────────────────────────────────────────────

def test_worker_sets_cors_headers():
    """CORS 標頭須設置，避免前端 POST 遭跨域阻擋。"""
    w = worker()
    assert "access-control-allow-origin" in w, "缺少 CORS allow-origin"
    assert "access-control-allow-methods" in w, "缺少 CORS allow-methods"
    assert "access-control-allow-headers" in w, "缺少 CORS allow-headers"


def test_worker_handles_options_preflight():
    """POST JSON 前的 OPTIONS 預檢須放行。"""
    w = worker()
    assert 'request.method === "OPTIONS"' in w, "缺少 OPTIONS preflight 放行"


# ── 6. ES Modules 導出規範 ───────────────────────────────────────────────────

def test_worker_is_es_modules_default_export():
    """符合 Cloudflare Workers ES Modules 導出規範。"""
    w = worker()
    assert "export default" in w, "缺少 export default"
    assert "async fetch(request, env" in w, "缺少 async fetch(request, env, ...) 進入點"
