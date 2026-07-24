"""test_MRL_debug_logs_route_v1.py — Mrliou 產品遙測日誌接收端點
origin_signature: MrLiouWord

驗證 Cloudflare Worker 以 MrliouAI / Mrliou 為產品與來源主體，攔截
POST /api/mrl/telemetry/logs，將 console/network/ui 日誌封裝為
MRL_DebugLogPacket，並禁止外部平台名稱升格進 canonical route、packet 或 trace。
"""
from __future__ import annotations

import pathlib
import re

REPO = pathlib.Path(__file__).resolve().parent.parent
WORKER_PATH = REPO / "src" / "mrl_worker.js"


def worker() -> str:
    return WORKER_PATH.read_text(encoding="utf-8")


def test_worker_intercepts_mrl_telemetry_logs_path():
    w = worker()
    assert '"/api/mrl/telemetry/logs"' in w
    pattern = re.compile(
        r'p\s*===\s*"/api/mrl/telemetry/logs"\s*&&\s*request\.method\s*===\s*"POST"'
        r'|request\.method\s*===\s*"POST"\s*&&\s*p\s*===\s*"/api/mrl/telemetry/logs"'
    )
    assert pattern.search(w), "MRL telemetry route must be POST-only"


def test_worker_uses_mrliou_product_and_source_identity():
    w = worker()
    assert 'const PRODUCT_NAME = "MrliouAI"' in w
    assert 'const SOURCE_OWNER = "Mrliou"' in w
    assert "product: PRODUCT_NAME" in w
    assert "source_owner: SOURCE_OWNER" in w
    assert 'origin_signature: ORIGIN_SIGNATURE' in w


def test_worker_uses_canonical_mrl_packet_naming():
    w = worker()
    assert "wrapMRLDebugLogs" in w
    assert 'mrl_kind: "MRL_DebugLogPacket"' in w
    assert 'return "MRL-DEBUG-"' in w
    assert 'console.log("MRL_DebugLogPacket"' in w


# 外部平台「產品名」禁列（Canonicalization Gate §4：外部名不得升格為 canonical 主體）。
# 只列產品/服務名；不含 cloudflare / workers — 那是 Transport/部署平台（gate §2 Adapter 層，允許）。
EXTERNAL_PLATFORM_NAMES = (
    "manus",
    "vercel",
    "openai",
    "chatgpt",
    "copilot",
    "coderabbit",
    "codex",
    "huggingface",
    "netlify",
    "heroku",
    "replit",
    "supabase",
    "firebase",
    "anthropic",
    "gemini",
    "sillytavern",
)


def test_worker_contains_no_external_platform_canonicalization():
    w = worker().lower()
    for name in EXTERNAL_PLATFORM_NAMES:
        assert name not in w, (
            f"external platform name {name!r} must not appear in product "
            "canonical route/packet/trace (MRL_Product_Canonicalization_Gate_v1 §4)"
        )


def test_worker_parses_json_safely():
    w = worker()
    assert "await request.json()" in w
    pattern = re.compile(r"try\s*\{[^}]*await\s+request\.json\(\)[^}]*\}\s*catch", re.DOTALL)
    assert pattern.search(w)
    assert "MRL_INVALID_JSON" in w


def test_worker_handles_expected_log_fields():
    w = worker()
    for field in ("consoleLogs", "networkRequests", "uiEvents"):
        assert field in w


def test_worker_guards_payload_size():
    w = worker()
    assert "content-length" in w
    assert "413" in w
    assert "MRL_PAYLOAD_TOO_LARGE" in w


def test_worker_trace_id_is_collision_resistant():
    w = worker()
    assert "crypto.randomUUID()" in w
    assert "mrlTraceId" in w


def test_worker_persists_full_payload_to_observability():
    w = worker()
    assert "emitPacketLog" in w
    assert "JSON.stringify(packet)" in w
    assert "MAX_LOG_CHARS" in w


def test_worker_sets_cors_and_origin_headers():
    w = worker()
    assert "access-control-allow-origin" in w
    assert "access-control-allow-methods" in w
    assert "access-control-allow-headers" in w
    assert "x-mrl-origin-signature" in w
    assert 'request.method === "OPTIONS"' in w


def test_worker_success_response_identifies_product_and_source():
    w = worker()
    assert "success: true" in w
    assert "product: PRODUCT_NAME" in w
    assert "source_owner: SOURCE_OWNER" in w
    assert "origin_signature: ORIGIN_SIGNATURE" in w


def test_worker_is_es_modules_default_export():
    w = worker()
    assert "export default" in w
    assert "async fetch(request, env" in w
