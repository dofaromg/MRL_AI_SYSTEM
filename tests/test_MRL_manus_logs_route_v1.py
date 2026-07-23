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
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
WORKER_PATH = REPO / "src" / "mrl_worker.js"


def worker() -> str:
    return WORKER_PATH.read_text(encoding="utf-8")


# ── 1. 路由攔截：pathname + method 條件（同一 if 子句）────────────────────────

def test_worker_intercepts_manus_logs_path():
    """必須攔截 pathname === "/__manus__/logs"。"""
    assert '"/__manus__/logs"' in worker(), "缺少 /__manus__/logs 路由攔截"


def test_worker_manus_logs_requires_post():
    """路由守衛必須把 /__manus__/logs 與 method === "POST" 綁在同一 if 條件，
    避免只檢查 'POST 有出現在檔案某處' 的偽陽性（Copilot 建議）。"""
    w = worker()
    # 同一條件式內同時出現 pathname 與 POST（容忍前後順序與空白）。
    pattern = re.compile(
        r'p\s*===\s*"/__manus__/logs"\s*&&\s*request\.method\s*===\s*"POST"'
        r'|request\.method\s*===\s*"POST"\s*&&\s*p\s*===\s*"/__manus__/logs"'
    )
    assert pattern.search(w), "路由條件須將 /__manus__/logs 與 POST 綁在同一 if 子句"


# ── 2. 安全解析 request.json() ────────────────────────────────────────────────

def test_worker_parses_json_safely():
    """必須以 try { ... await request.json() ... } catch 綁定的方式安全解析，
    而非檔案任意處出現 try/catch 即算過（Copilot 建議）。"""
    w = worker()
    assert "await request.json()" in w, "缺少 await request.json() 解析"
    # try 與其後最近的 catch 之間必須包住 await request.json()。
    pattern = re.compile(r"try\s*\{[^}]*await\s+request\.json\(\)[^}]*\}\s*catch", re.DOTALL)
    assert pattern.search(w), "await request.json() 必須被 try/catch 包住"
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


# ── 6. 硬化：大小防護 / 防碰撞 trace_id / 完整 payload 落地（審查回饋）─────────

def test_worker_guards_payload_size():
    """公開端點須有 body 大小上限，逾者回 413（Copilot 建議）。"""
    w = worker()
    assert "content-length" in w, "缺少 content-length 大小防護"
    assert "413" in w, "超大 body 應回 413"
    assert "MRL_PAYLOAD_TOO_LARGE" in w, "缺少 payload 過大錯誤標記"


def test_worker_trace_id_is_collision_resistant():
    """trace_id 須含 crypto.randomUUID() 隨機性，避免同毫秒碰撞（Codex/Copilot 建議）。"""
    w = worker()
    assert "crypto.randomUUID()" in w, "trace_id 須用 crypto.randomUUID() 防碰撞"
    assert "mrlTraceId" in w, "trace_id 應由 mrlTraceId() 產生（含後備）"


def test_worker_persists_full_payload_to_observability():
    """成功前須把完整封包（含 payload）落到 observability，而非只留計數（Codex P1）。"""
    w = worker()
    assert "emitPacketLog" in w, "缺少完整封包落地函式 emitPacketLog"
    # emitPacketLog 內須序列化整個 packet（含 payload），而非僅 counts。
    assert "JSON.stringify(packet)" in w, "須序列化完整 packet（含 payload），非只 counts"
    assert "MAX_LOG_CHARS" in w, "須有單筆 log 截斷上限，避免整筆遺失"


# ── 7. ES Modules 導出規範 ───────────────────────────────────────────────────

def test_worker_is_es_modules_default_export():
    """符合 Cloudflare Workers ES Modules 導出規範。"""
    w = worker()
    assert "export default" in w, "缺少 export default"
    assert "async fetch(request, env" in w, "缺少 async fetch(request, env, ...) 進入點"
