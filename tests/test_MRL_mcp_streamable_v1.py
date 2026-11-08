#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_MRL_mcp_streamable_v1.py — MCP Streamable-HTTP server + client 驗收
origin_signature: MrLiouWord

pytest 相容；沙盒無 pytest 時可獨立執行：
    python3 tests/test_MRL_mcp_streamable_v1.py
"""
from __future__ import annotations

import asyncio
import json
import pathlib
import sys
import time
import urllib.request

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _sub in [_REPO_ROOT, _REPO_ROOT / "09_workflow"]:
    if str(_sub) not in sys.path:
        sys.path.insert(0, str(_sub))

from MRL_MCPServerHarness_Streamable_v1 import (  # noqa: E402
    MCPStreamableServer,
    ThreadedServer,
    make_content,
)
from MRL_MCPClient_Streamable_v1 import MCPClientError, MCPStreamableClient  # noqa: E402
from MRL_AgentHarness_ToolLoop_v1 import ToolLoopRunner  # noqa: E402
from MRL_AgentHarness_PolicyGate_v1 import (  # noqa: E402
    allow,
    allow_all,
    deny_all,
    enforce,
)


# ─── 共用 fixture ────────────────────────────────────────────────────────────
def _echo(message: str):
    return make_content(f"Tool echo: {message}")


def _make_server_with_echo() -> MCPStreamableServer:
    server = MCPStreamableServer(server_name="test-harness")
    server.register_tool(
        name="echo",
        description="Echo a message",
        input_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
        handler=_echo,
    )
    return server


# ─── 基本協議往返 ────────────────────────────────────────────────────────────
def test_initialize_returns_server_info_and_capabilities():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        client = MCPStreamableClient(httpd.url)
        info = client.initialize()
        assert info.get("serverInfo", {}).get("name") == "test-harness"
        assert info.get("serverInfo", {}).get("originSignature") == "MrLiouWord"
        assert "echo" in info.get("capabilities", {}).get("tools", {})
        assert client.protocol_version  # 已存下

def test_ping_returns_empty_dict():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        client = MCPStreamableClient(httpd.url)
        assert client.ping() == {}


def test_tools_list_exposes_registered_tool_schema():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        client = MCPStreamableClient(httpd.url)
        tools = client.list_tools()
        assert len(tools) == 1
        assert tools[0]["name"] == "echo"
        assert tools[0]["description"] == "Echo a message"
        assert tools[0]["inputSchema"]["required"] == ["message"]


def test_tools_call_returns_content_array():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        client = MCPStreamableClient(httpd.url)
        result = client.call_tool("echo", {"message": "你好母體"})
        assert result["content"][0]["type"] == "text"
        assert result["content"][0]["text"] == "Tool echo: 你好母體"


# ─── 錯誤處理 ────────────────────────────────────────────────────────────────
def test_unknown_method_returns_method_not_found():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        client = MCPStreamableClient(httpd.url)
        try:
            client._rpc("wallet/steal")
            assert False, "應拋 MCPClientError"
        except MCPClientError as e:
            assert e.code == -32601 and "wallet/steal" in e.message


def test_unknown_tool_returns_specific_error():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        client = MCPStreamableClient(httpd.url)
        try:
            client.call_tool("ghost")
            assert False, "應拋"
        except MCPClientError as e:
            assert e.code == -32001 and "ghost" in e.message


def test_malformed_params_return_invalid_params():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        # 手動送不合法 arguments（非物件）
        req = urllib.request.Request(
            httpd.url,
            data=json.dumps({
                "jsonrpc": "2.0", "id": "x", "method": "tools/call",
                "params": {"name": "echo", "arguments": "應是物件不是字串"},
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
        assert body["error"]["code"] == -32602


def test_malformed_json_returns_parse_error():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        req = urllib.request.Request(
            httpd.url,
            data=b"{not json",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
        assert body["error"]["code"] == -32700


def test_handler_exception_becomes_tool_execution_error():
    server = MCPStreamableServer()

    def boom() -> None:
        raise RuntimeError("演示炸")

    server.register_tool("boom", "raises", {"type": "object"}, boom)
    with ThreadedServer(server) as httpd:
        client = MCPStreamableClient(httpd.url)
        try:
            client.call_tool("boom")
            assert False
        except MCPClientError as e:
            assert e.code == -32003 and "boom" in e.message


# ─── notification / batch / GET / DELETE ─────────────────────────────────────
def test_notification_returns_204_no_response():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        req = urllib.request.Request(
            httpd.url,
            data=json.dumps({
                "jsonrpc": "2.0", "method": "notifications/initialized", "params": {}
            }).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 204
            assert resp.read() == b""


def test_batch_request_returns_matching_responses():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        batch = [
            {"jsonrpc": "2.0", "id": "a", "method": "tools/list"},
            {"jsonrpc": "2.0", "id": "b", "method": "ping"},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},  # 通知不回
        ]
        req = urllib.request.Request(
            httpd.url,
            data=json.dumps(batch).encode(),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = json.loads(resp.read())
        assert isinstance(body, list)
        assert len(body) == 2  # 只回兩個非通知
        ids = {r["id"] for r in body}
        assert ids == {"a", "b"}


def test_get_returns_405_because_sse_disabled():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        req = urllib.request.Request(httpd.url, method="GET")
        try:
            urllib.request.urlopen(req, timeout=5)
            assert False, "GET 應回 405"
        except urllib.error.HTTPError as e:
            assert e.code == 405


def test_delete_returns_204():
    with ThreadedServer(_make_server_with_echo()) as httpd:
        req = urllib.request.Request(httpd.url, method="DELETE")
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 204


# ─── Copilot review PR#92 回歸測試（三條修復） ─────────────────────────────
def test_empty_batch_returns_invalid_request():
    """JSON-RPC 2.0 §6：空陣列不合法，必須回 -32600（不得誤判為全 notification 回 204）。"""
    with ThreadedServer(_make_server_with_echo()) as httpd:
        req = urllib.request.Request(
            httpd.url,
            data=b"[]",
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=5) as resp:
            assert resp.status == 200  # error response 仍走 HTTP 200
            body = json.loads(resp.read())
        assert body["error"]["code"] == -32600
        assert body["id"] is None


def test_policy_verdict_no_event_loop_leak():
    """_policy_verdict 對每個 async policy_gate.run 建的 event loop 都必須 close，否則洩漏。

    連呼 30 次 tools/call，攔截 `warnings.catch_warnings` 內的
    `ResourceWarning: unclosed event loop`；出現即代表 loop 洩漏。
    """
    import warnings

    async def async_predicate(args):
        # 觸發 policy_gate.run 走 async 分支（回 coroutine）
        await asyncio.sleep(0)
        return True

    gate = enforce([allow("echo", when=async_predicate)])
    server = MCPStreamableServer(policy_gate=gate)
    server.register_tool("echo", "e", {"type": "object"}, _echo)

    with ThreadedServer(server) as httpd:
        client = MCPStreamableClient(httpd.url)
        # 攔截 asyncio 的 ResourceWarning: unclosed event loop
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter("always", ResourceWarning)
            for _ in range(30):
                client.call_tool("echo", {"message": "x"})
            # 硬化：若 coroutine 鏈有引用循環，refcount finalize 會遞延到 cyclic GC，
            # 導致 ResourceWarning 晚於 assert 才發出 → 誤判為無洩漏。強制 collect
            # 讓 cycle-hidden leaks 也被捕捉到。
            import gc

            gc.collect()
        leaked = [w for w in caught if "unclosed event loop" in str(w.message).lower()]
        assert not leaked, f"洩漏 {len(leaked)} 個未關閉 event loop"


def test_make_http_server_uses_os_atomic_port_allocation():
    """make_http_server(port=0) 直接讓 HTTPServer(host, 0) 由 OS 原子分配 port
    （條 3：刪除有 TOCTOU race 的 _pick_free_port helper）。
    """
    from MRL_MCPServerHarness_Streamable_v1 import make_http_server
    import MRL_MCPServerHarness_Streamable_v1 as mod

    # helper 已刪除（TOCTOU race 面向已移除）
    assert not hasattr(mod, "_pick_free_port"), "_pick_free_port 應已刪除"
    # port=0 仍可正確拿到實際 port（由 OS 原子分配）
    httpd = make_http_server(_make_server_with_echo(), host="127.0.0.1", port=0)
    try:
        assigned = httpd.server_address[1]
        assert isinstance(assigned, int) and assigned > 0
    finally:
        httpd.server_close()


def test_make_http_server_respects_host_parameter():
    """條 3 附帶：host 參數不會被 hardcoded 127.0.0.1 覆蓋（原 _pick_free_port 的另一個 bug）。"""
    from MRL_MCPServerHarness_Streamable_v1 import make_http_server

    httpd = make_http_server(_make_server_with_echo(), host="127.0.0.1", port=0)
    try:
        assert httpd.server_address[0] == "127.0.0.1"
    finally:
        httpd.server_close()


# ─── AgentHarness 銜接 ───────────────────────────────────────────────────────
def test_bridged_tool_loop_exposes_tools_to_mcp():
    """MRL_AgentHarness_ToolLoop 已註冊工具 → MCP client 可直接呼叫。"""
    loop = ToolLoopRunner()

    def add(a: int, b: int) -> int:
        return a + b

    loop.register(add)
    server = MCPStreamableServer(tool_loop=loop)

    with ThreadedServer(server) as httpd:
        client = MCPStreamableClient(httpd.url)
        assert "add" in [t["name"] for t in client.list_tools()]
        result = client.call_tool("add", {"a": 2, "b": 3})
        # loop 回原始 int，被自動包成 text content
        assert "5" in result["content"][0]["text"]


def test_policy_gate_denies_tool_call():
    """MRL_AgentHarness_PolicyGate deny → MCP 收到 -32002 tool_denied。"""
    gate = enforce([deny_all(), allow("safe")])
    server = MCPStreamableServer(policy_gate=gate)

    def safe() -> str:
        return "ok"

    def dangerous() -> str:
        raise AssertionError("被拒工具絕不可執行")

    server.register_tool("safe", "safe", {"type": "object"}, safe)
    server.register_tool("dangerous", "dangerous", {"type": "object"}, dangerous)

    with ThreadedServer(server) as httpd:
        client = MCPStreamableClient(httpd.url)
        # safe 過閘
        out = client.call_tool("safe")
        assert "ok" in out["content"][0]["text"]
        # dangerous 被 deny_all 攔下
        try:
            client.call_tool("dangerous")
            assert False, "應拋"
        except MCPClientError as e:
            assert e.code == -32002 and "deny_all" in e.message


def test_policy_gate_allow_all_lets_registered_tool_pass():
    gate = enforce([allow_all()])
    server = MCPStreamableServer(policy_gate=gate)
    server.register_tool("echo", "echo", {"type": "object"}, _echo)
    with ThreadedServer(server) as httpd:
        client = MCPStreamableClient(httpd.url)
        result = client.call_tool("echo", {"message": "透過閘"})
        assert result["content"][0]["text"] == "Tool echo: 透過閘"


# ─── server-side 直接呼叫 handle_message（不經 HTTP） ───────────────────────
def test_handle_message_direct_shape():
    """handle_message 應可獨立測試（不需 HTTP 層）。"""
    server = _make_server_with_echo()
    response = server.handle_message(
        {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {}}
    )
    assert response["result"]["serverInfo"]["name"] == "test-harness"
    # notification 無回應
    assert server.handle_message(
        {"jsonrpc": "2.0", "method": "notifications/initialized"}
    ) is None
    # 非 2.0
    resp = server.handle_message({"jsonrpc": "1.0", "id": 1, "method": "ping"})
    assert resp["error"]["code"] == -32600


def test_duplicate_registration_rejected():
    server = _make_server_with_echo()
    try:
        server.register_tool("echo", "again", {"type": "object"}, _echo)
        assert False, "重複註冊應拋"
    except ValueError:
        pass


# ─── 獨立執行器 ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import traceback

    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    passed, failed = 0, 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed / {len(tests)} total")
    sys.exit(1 if failed else 0)
