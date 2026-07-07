#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_MCPServerHarness_Streamable_v1.py — MCP Server:Streamable-HTTP transport
origin_signature: MrLiouWord
layer: L0 ROOT (出入口) + L4 WORLD
group: Y=3 FlowAgentRuntime

吸收來源（母體吸收記錄）
----------------------
蒸餾自 dofaromg/model-context-protocol-mcp-with-next-js（Next.js 15 App Router +
`mcp-handler` Vercel 適配器）。與母體既有模組分工（去重定位，不重疊）：

  - 09_workflow/MRL_MCP_Server_v1.py         — stdio transport（JSON-RPC over
                                                 stdin/stdout，硬編碼 4 工具）
  - 本模組（Streamable_v1）                   — HTTP transport（POST/GET/DELETE
                                                 到單一 endpoint，動態工具註冊，
                                                 與 AgentHarness ToolLoop/
                                                 PolicyGate 銜接）
  - 09_workflow/tool_registry.py             — 工具 schema 註冊簿（既有，不重造）
  - MRL_AgentHarness_ToolLoop_v1             — 並行工具批次執行器（既有，本模組
                                                 委派它執行工具）
  - MRL_AgentHarness_PolicyGate_v1           — 9 級優先序政策閘（既有，本模組
                                                 每個 tools/call 前過閘）

本次吸收的核心知識（母體原缺）：
1. **Streamable-HTTP MCP transport**：一個 endpoint 用 HTTP POST 承載 JSON-RPC
   訊息（request/response 一對一，無 SSE，無 session state）。
2. **動態工具註冊 API**：`register_tool(name, description, input_schema, handler)`
   取代母體既有的硬編碼 TOOLS 列表；handler 可為 sync/async callable。
3. **與 AgentHarness 銜接**：可選 `tool_loop` 參數，把 AgentHarness 已註冊的工具
   自動暴露為 MCP tools；可選 `policy_gate` 讓 MCP 工具呼叫也過母體政策閘
   （fail-closed 對齊 rl_00 deny-by-default）。

蒸餾去除的外部依賴（母體零外部依賴原則）：
  - `mcp-handler` (Vercel 適配器)  → 純 http.server + BaseHTTPRequestHandler
  - `next` / `react` / `react-dom` → 不需要（Next.js 路由是 mcp-handler 的載體）
  - `zod`                          → 直接用 JSON Schema dict
  - `redis` (SSE session state)    → 不需要（disableSse=True，無會話）

依賴：Python stdlib only（http.server, json, socket, threading, urllib.parse）。
CLI：python3 09_workflow/MRL_MCPServerHarness_Streamable_v1.py --port 8765
"""
from __future__ import annotations

import inspect
import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer
from typing import Any, Awaitable, Callable, Dict, List, Optional, Tuple, Union

from MRL_utils import ORIGIN_SIGNATURE

__all__ = [
    "ORIGIN_SIGNATURE",
    "PROTOCOL_VERSION",
    "ToolHandler",
    "ToolSpec",
    "MCPStreamableServer",
    "make_content",
    "make_error",
    "JsonRpcError",
]

# ── MCP 協議常數 ──────────────────────────────────────────────────────────────
PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "MRL_MCPServerHarness_Streamable"
SERVER_VERSION = "1.0.0"

# JSON-RPC 2.0 標準錯誤碼
_ERR_PARSE = -32700
_ERR_INVALID_REQUEST = -32600
_ERR_METHOD_NOT_FOUND = -32601
_ERR_INVALID_PARAMS = -32602
_ERR_INTERNAL = -32603
# MCP 應用層錯誤碼（自訂範圍）
_ERR_TOOL_UNKNOWN = -32001
_ERR_TOOL_DENIED = -32002
_ERR_TOOL_EXECUTION = -32003

ToolHandler = Callable[..., Union[Any, Awaitable[Any]]]


class JsonRpcError(Exception):
    """MCP handler 內部主動拋出以帶錯誤碼與訊息回應客戶端。"""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(message)
        self.code = code
        self.message = message
        self.data = data


class ToolSpec:
    """單一工具的宣告：name / description / input_schema / handler。

    input_schema 為 JSON Schema dict（等價外部 repo 的 zod shape）。
    """

    __slots__ = ("name", "description", "input_schema", "handler")

    def __init__(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.handler = handler

    def to_public(self) -> Dict[str, Any]:
        """回傳 tools/list 對外暴露的 JSON 表示。"""
        return {
            "name": self.name,
            "description": self.description,
            "inputSchema": self.input_schema,
        }


def make_content(text: str) -> Dict[str, Any]:
    """MCP tools/call result 用的內容陣列包裝（單一 text block）。"""
    return {"content": [{"type": "text", "text": text}]}


def make_error(code: int, message: str) -> Dict[str, Any]:
    """組 JSON-RPC error object。"""
    return {"code": code, "message": message}


# ── Server 核心 ──────────────────────────────────────────────────────────────
class MCPStreamableServer:
    """MCP Streamable-HTTP server：一個 HTTP endpoint 承載 JSON-RPC 訊息。

    與 AgentHarness 銜接（皆為可選）：
      - tool_loop  : ToolLoopRunner —— 若傳入，自動把 loop 已註冊工具暴露為
                     MCP tools；本模組委派它執行實際呼叫（並行/錯誤隔離皆繼承）。
      - policy_gate: PreToolCallDecideHook —— 若傳入，每個 tools/call 前過閘；
                     被拒即回 JSON-RPC error（deny-by-default 對齊 rl_00）。
    """

    def __init__(
        self,
        server_name: str = SERVER_NAME,
        server_version: str = SERVER_VERSION,
        tool_loop: Any = None,
        policy_gate: Any = None,
    ) -> None:
        self.server_name = server_name
        self.server_version = server_version
        self._tools: Dict[str, ToolSpec] = {}
        self._tool_loop = tool_loop
        self._policy_gate = policy_gate
        self._initialized = False
        # 若接了 tool_loop，把 loop 已註冊工具鏡射為 MCP 工具（description 從缺
        # 時以名稱代替；input_schema 從缺時給 free-form object）
        if tool_loop is not None:
            for name in getattr(tool_loop, "tool_names", []):
                if name in self._tools:
                    continue
                fn = tool_loop.get_public_callable(name)
                self._tools[name] = ToolSpec(
                    name=name,
                    description=(getattr(fn, "__doc__", None) or name).splitlines()[0],
                    input_schema={"type": "object"},
                    handler=None,  # None 表示走 tool_loop.execute()
                )

    # ─── 工具註冊 ────────────────────────────────────────────────────────────
    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: Dict[str, Any],
        handler: ToolHandler,
    ) -> None:
        """動態註冊工具（等價外部 repo 的 server.tool()）。"""
        if name in self._tools:
            raise ValueError(f"工具 '{name}' 已註冊")
        self._tools[name] = ToolSpec(name, description, input_schema, handler)

    @property
    def tool_names(self) -> List[str]:
        return list(self._tools.keys())

    # ─── MCP 方法分派 ────────────────────────────────────────────────────────
    def handle_message(self, message: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """吃單一 JSON-RPC message，回應對應 JSON-RPC response（notification
        回 None）。所有錯誤都轉為 JSON-RPC error，絕不拋例外。
        """
        if not isinstance(message, dict) or message.get("jsonrpc") != "2.0":
            return self._error_response(
                message.get("id") if isinstance(message, dict) else None,
                _ERR_INVALID_REQUEST,
                "非合法 JSON-RPC 2.0 訊息",
            )

        msg_id = message.get("id")
        method = message.get("method")
        params = message.get("params") or {}
        is_notification = msg_id is None

        try:
            if method == "initialize":
                result = self._on_initialize(params)
            elif method in ("notifications/initialized", "initialized"):
                self._initialized = True
                return None  # notification 無回應
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = self._on_tools_list()
            elif method == "tools/call":
                result = self._on_tools_call(params)
            else:
                if is_notification:
                    return None
                return self._error_response(
                    msg_id, _ERR_METHOD_NOT_FOUND, f"未知方法: {method!r}"
                )
        except JsonRpcError as e:
            if is_notification:
                return None
            return self._error_response(msg_id, e.code, e.message, e.data)
        except Exception as e:  # noqa: BLE001 — 分派層必須捕捉全部並回錯
            if is_notification:
                return None
            return self._error_response(
                msg_id, _ERR_INTERNAL, f"內部錯誤: {e!r}"
            )

        if is_notification:
            return None
        return {"jsonrpc": "2.0", "id": msg_id, "result": result}

    # ─── 具體 handler ────────────────────────────────────────────────────────
    def _on_initialize(self, params: Dict[str, Any]) -> Dict[str, Any]:
        # 客戶端可送 protocolVersion；為相容取交集或直接沿用伺服端版本
        client_pv = params.get("protocolVersion", PROTOCOL_VERSION)
        return {
            "protocolVersion": client_pv if isinstance(client_pv, str) else PROTOCOL_VERSION,
            "capabilities": {
                "tools": {name: {"description": spec.description}
                          for name, spec in self._tools.items()},
            },
            "serverInfo": {
                "name": self.server_name,
                "version": self.server_version,
                "originSignature": ORIGIN_SIGNATURE,
            },
        }

    def _on_tools_list(self) -> Dict[str, Any]:
        return {"tools": [spec.to_public() for spec in self._tools.values()]}

    def _on_tools_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        name = params.get("name")
        args = params.get("arguments") or {}
        if not isinstance(name, str) or not name:
            raise JsonRpcError(_ERR_INVALID_PARAMS, "tools/call 缺 name")
        if not isinstance(args, dict):
            raise JsonRpcError(_ERR_INVALID_PARAMS, "tools/call arguments 必須為 object")
        if name not in self._tools:
            raise JsonRpcError(_ERR_TOOL_UNKNOWN, f"未知工具: {name!r}")

        # ── 政策閘（可選）：與 MRL_AgentHarness_PolicyGate 銜接 ──────────
        if self._policy_gate is not None:
            verdict = self._policy_verdict(name, args)
            if not verdict.allow:
                raise JsonRpcError(
                    _ERR_TOOL_DENIED,
                    verdict.message or f"政策閘拒絕工具 '{name}'",
                )

        # ── 執行：優先走 tool_loop（並行/錯誤隔離）；否則直呼 handler ────
        spec = self._tools[name]
        try:
            if spec.handler is None and self._tool_loop is not None:
                result = self._run_via_tool_loop(name, args)
            else:
                result = self._run_direct(spec.handler, args)
        except JsonRpcError:
            raise
        except Exception as e:  # noqa: BLE001
            raise JsonRpcError(_ERR_TOOL_EXECUTION, f"工具 '{name}' 執行失敗: {e!r}")

        # 若 handler 已回 MCP content 結構（有 "content" key）就直接用；
        # 否則自動包一層 text content。
        if isinstance(result, dict) and "content" in result:
            return result
        return make_content(str(result))

    # ─── 政策閘同步橋接 ──────────────────────────────────────────────────────
    def _policy_verdict(self, name: str, args: Dict[str, Any]) -> Any:
        """把 async policy hook 以最小事件迴圈驅動出來（同步呼叫路徑）。

        MCP HTTP handler 執行緒不共享 event loop；為避免每次呼叫都新建/銷毀
        event loop 的成本，此處只在真的需要跑 async 時才起 loop。
        """
        # 延遲匯入避免循環相依（PolicyGate 可能沒被使用者載入）
        from MRL_AgentHarness_Types_v1 import ToolCall

        tool_call = ToolCall(name=name, args=dict(args))
        # HookContext 是簡單容器，不需要 loop
        from MRL_AgentHarness_HookLattice_v1 import HookContext

        coro = self._policy_gate.run(HookContext(), tool_call)
        if inspect.iscoroutine(coro):
            import asyncio

            return asyncio.new_event_loop().run_until_complete(coro)
        return coro

    def _run_via_tool_loop(self, name: str, args: Dict[str, Any]) -> Any:
        import asyncio

        loop = asyncio.new_event_loop()
        try:
            return loop.run_until_complete(self._tool_loop.execute(name, **args))
        finally:
            loop.close()

    def _run_direct(self, handler: ToolHandler, args: Dict[str, Any]) -> Any:
        result = handler(**args)
        if inspect.iscoroutine(result):
            import asyncio

            loop = asyncio.new_event_loop()
            try:
                return loop.run_until_complete(result)
            finally:
                loop.close()
        return result

    # ─── 錯誤回應組裝 ────────────────────────────────────────────────────────
    def _error_response(
        self, msg_id: Any, code: int, message: str, data: Any = None
    ) -> Dict[str, Any]:
        err = make_error(code, message)
        if data is not None:
            err["data"] = data
        return {"jsonrpc": "2.0", "id": msg_id, "error": err}


# ── HTTP handler ─────────────────────────────────────────────────────────────
class _MCPRequestHandler(BaseHTTPRequestHandler):
    """把 HTTP POST/GET/DELETE 折成 JSON-RPC 訊息交 server.handle_message。

    自 SDK 蒸餾：外部 repo 的 route.ts 匯出 { GET, POST, DELETE }。GET/DELETE
    在 disableSse=True 下沒有實質工作（無 SSE 訂閱、無 session 狀態），此處
    分別以 405/204 誠實回應（不假裝支援自己不做的事）。
    """

    server_version = f"{SERVER_NAME}/{SERVER_VERSION}"

    def _send_json(self, status: int, body: Dict[str, Any]) -> None:
        data = json.dumps(body, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_empty(self, status: int) -> None:
        self.send_response(status)
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_POST(self) -> None:  # noqa: N802 — stdlib callback name
        length = int(self.headers.get("Content-Length") or 0)
        raw = self.rfile.read(length) if length > 0 else b""
        try:
            message = json.loads(raw.decode("utf-8")) if raw else {}
        except (UnicodeDecodeError, json.JSONDecodeError) as e:
            self._send_json(
                200,
                {
                    "jsonrpc": "2.0",
                    "id": None,
                    "error": make_error(_ERR_PARSE, f"JSON 解析失敗: {e}"),
                },
            )
            return

        # 支援單一訊息或批次陣列（JSON-RPC 2.0 §6）
        mcp_server: MCPStreamableServer = self.server.mcp_server  # type: ignore[attr-defined]
        if isinstance(message, list):
            responses = [
                r for r in (mcp_server.handle_message(m) for m in message) if r is not None
            ]
            if not responses:
                self._send_empty(204)  # 全 notification，無回應
                return
            self._send_json(200, responses)  # type: ignore[arg-type]
            return

        response = mcp_server.handle_message(message)
        if response is None:
            self._send_empty(204)  # notification
            return
        self._send_json(200, response)

    def do_GET(self) -> None:  # noqa: N802
        # disableSse=True：無 SSE 訂閱可承接，回 405（誠實）
        self.send_response(405)
        self.send_header("Allow", "POST, DELETE")
        self.send_header("Content-Length", "0")
        self.end_headers()

    def do_DELETE(self) -> None:  # noqa: N802
        # 無 session 狀態可清；回 204 no content
        self._send_empty(204)

    def log_message(self, format: str, *args: Any) -> None:  # noqa: A002
        # 靜音預設 stderr log；如需 verbose 由呼叫端自行掛 hook
        return


# ── 便利入口：serve_forever / serve_in_thread ────────────────────────────────
def _pick_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def make_http_server(
    mcp_server: MCPStreamableServer, host: str = "127.0.0.1", port: int = 0
) -> HTTPServer:
    """把 MCPStreamableServer 掛到 HTTPServer；port=0 表示自動挑空 port。"""
    if port == 0:
        port = _pick_free_port()
    httpd = HTTPServer((host, port), _MCPRequestHandler)
    httpd.mcp_server = mcp_server  # type: ignore[attr-defined]
    return httpd


class ThreadedServer:
    """把 HTTPServer 起在背景執行緒的 context manager（測試/CLI 用）。"""

    def __init__(self, mcp_server: MCPStreamableServer, host: str = "127.0.0.1", port: int = 0) -> None:
        self._mcp = mcp_server
        self._host = host
        self._port = port
        self._httpd: Optional[HTTPServer] = None
        self._thread: Optional[threading.Thread] = None

    def __enter__(self) -> "ThreadedServer":
        self._httpd = make_http_server(self._mcp, self._host, self._port)
        self._thread = threading.Thread(
            target=self._httpd.serve_forever, name="MCPStreamableServer", daemon=True
        )
        self._thread.start()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        if self._httpd is not None:
            self._httpd.shutdown()
            self._httpd.server_close()
        if self._thread is not None:
            self._thread.join(timeout=2.0)

    @property
    def url(self) -> str:
        assert self._httpd is not None
        host, port = self._httpd.server_address
        return f"http://{host}:{port}/"

    @property
    def port(self) -> int:
        assert self._httpd is not None
        return int(self._httpd.server_address[1])


# ── CLI demo ─────────────────────────────────────────────────────────────────
def _demo() -> None:
    import sys

    port = 0
    for i, arg in enumerate(sys.argv):
        if arg == "--port" and i + 1 < len(sys.argv):
            port = int(sys.argv[i + 1])

    server = MCPStreamableServer()

    def echo(message: str) -> Dict[str, Any]:
        return make_content(f"Tool echo: {message}")

    server.register_tool(
        name="echo",
        description="Echo a message",
        input_schema={
            "type": "object",
            "properties": {"message": {"type": "string"}},
            "required": ["message"],
        },
        handler=echo,
    )

    print(f"MRL_MCPServerHarness_Streamable_v1 — origin_signature={ORIGIN_SIGNATURE}")
    print(f"tools: {server.tool_names}")

    with ThreadedServer(server, port=port) as httpd:
        print(f"serving at {httpd.url} — POST JSON-RPC or Ctrl+C to stop")
        import time

        try:
            while True:
                time.sleep(3600)
        except KeyboardInterrupt:
            print("shutting down")


if __name__ == "__main__":
    _demo()
