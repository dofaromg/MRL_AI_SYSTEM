#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_MCPClient_Streamable_v1.py — MCP Client:Streamable-HTTP transport（純 stdlib）
origin_signature: MrLiouWord
layer: L0 ROOT (出入口)
group: Y=3 FlowAgentRuntime

吸收來源（母體吸收記錄）
----------------------
蒸餾自 dofaromg/model-context-protocol-mcp-with-next-js `scripts/test-streamable-
http-client.mjs`：外部腳本用 `@modelcontextprotocol/sdk` 的 `Client` +
`StreamableHTTPClientTransport` 連 `<origin>/mcp` 並呼叫 `client.listTools()`。

蒸餾去除的外部依賴：
  - `@modelcontextprotocol/sdk` → 純 stdlib urllib.request（HTTP POST JSON-RPC）
  - Node.js runtime               → Python 3

用途：
  1. 對外測試/健檢 MCP server 是否活著、tools/list 是否正確。
  2. 作為 MRL_MCPServerHarness 驗收測試的 in-process client。
  3. 母體之間互相以 MCP 呼叫時的 client 端（Y=3 FlowAgentRuntime）。

依賴：Python stdlib only（json, uuid, urllib.request, urllib.error）。
CLI：python3 09_workflow/MRL_MCPClient_Streamable_v1.py <url>
     python3 09_workflow/MRL_MCPClient_Streamable_v1.py <url> call <tool> k=v k2=v2
"""
from __future__ import annotations

import json
import urllib.error
import urllib.request
import uuid
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE

__all__ = ["MCPStreamableClient", "MCPClientError"]

PROTOCOL_VERSION = "2024-11-05"
CLIENT_NAME = "MRL_MCPClient_Streamable"
CLIENT_VERSION = "1.0.0"


class MCPClientError(Exception):
    """server 回 JSON-RPC error 時抛出，含 code/message/data。"""

    def __init__(self, code: int, message: str, data: Any = None) -> None:
        super().__init__(f"[{code}] {message}")
        self.code = code
        self.message = message
        self.data = data


class MCPStreamableClient:
    """對 MCP Streamable-HTTP endpoint 發 JSON-RPC 訊息的最小 client。

    無 session 狀態、無 SSE 訂閱（外部 repo 也 disableSse=True）；
    每個公開方法對應一次 HTTP POST。
    """

    def __init__(
        self,
        endpoint: str,
        *,
        timeout: float = 30.0,
        client_name: str = CLIENT_NAME,
        client_version: str = CLIENT_VERSION,
    ) -> None:
        self.endpoint = endpoint
        self.timeout = timeout
        self.client_name = client_name
        self.client_version = client_version
        self.server_info: Optional[Dict[str, Any]] = None
        self.protocol_version: Optional[str] = None

    # ─── 底層 POST ───────────────────────────────────────────────────────────
    def _post(self, message: Dict[str, Any]) -> Any:
        data = json.dumps(message, ensure_ascii=False).encode("utf-8")
        req = urllib.request.Request(
            self.endpoint,
            data=data,
            method="POST",
            headers={
                "Content-Type": "application/json; charset=utf-8",
                "Accept": "application/json",
                "User-Agent": f"{self.client_name}/{self.client_version}",
            },
        )
        try:
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                if resp.status == 204:
                    return None
                raw = resp.read()
                if not raw:
                    return None
                return json.loads(raw.decode("utf-8"))
        except urllib.error.HTTPError as e:
            body = e.read().decode("utf-8", errors="replace") if e.fp else ""
            raise MCPClientError(-32000, f"HTTP {e.code}: {e.reason}", body) from e

    def _rpc(self, method: str, params: Optional[Dict[str, Any]] = None) -> Any:
        """發送一個帶 id 的 JSON-RPC request 並回傳其 result；error 就抛。"""
        msg_id = uuid.uuid4().hex
        response = self._post(
            {
                "jsonrpc": "2.0",
                "id": msg_id,
                "method": method,
                "params": params or {},
            }
        )
        if not isinstance(response, dict):
            raise MCPClientError(-32603, f"server 回傳非物件: {response!r}")
        if response.get("id") != msg_id:
            raise MCPClientError(
                -32603,
                f"response id 不符（期待 {msg_id}，收到 {response.get('id')}）",
            )
        if "error" in response:
            err = response["error"] or {}
            raise MCPClientError(
                int(err.get("code", -32603)),
                str(err.get("message", "unknown error")),
                err.get("data"),
            )
        return response.get("result")

    def _notify(self, method: str, params: Optional[Dict[str, Any]] = None) -> None:
        """發送 notification（無 id、無回應）。"""
        self._post(
            {"jsonrpc": "2.0", "method": method, "params": params or {}}
        )

    # ─── MCP 公開方法 ───────────────────────────────────────────────────────
    def initialize(self) -> Dict[str, Any]:
        """MCP 握手：告知客戶端資訊，取回 server capabilities。"""
        result = self._rpc(
            "initialize",
            {
                "protocolVersion": PROTOCOL_VERSION,
                "clientInfo": {
                    "name": self.client_name,
                    "version": self.client_version,
                },
                "capabilities": {},
            },
        )
        if isinstance(result, dict):
            self.server_info = result.get("serverInfo")
            self.protocol_version = result.get("protocolVersion")
        # 依規範，client 應在 initialize 後送 notifications/initialized
        try:
            self._notify("notifications/initialized")
        except MCPClientError:
            # notification 失敗不阻斷 initialize 成功語意
            pass
        return result if isinstance(result, dict) else {}

    def ping(self) -> Dict[str, Any]:
        result = self._rpc("ping")
        return result if isinstance(result, dict) else {}

    def list_tools(self) -> List[Dict[str, Any]]:
        result = self._rpc("tools/list")
        if isinstance(result, dict) and isinstance(result.get("tools"), list):
            return result["tools"]
        return []

    def call_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """呼叫具名工具，回 server 的 result（通常含 content 陣列）。"""
        result = self._rpc(
            "tools/call",
            {"name": name, "arguments": arguments or {}},
        )
        return result if isinstance(result, dict) else {}


# ── CLI ──────────────────────────────────────────────────────────────────────
def _demo() -> None:
    import sys

    if len(sys.argv) < 2:
        print(
            "usage: MRL_MCPClient_Streamable_v1.py <url> [list|call <tool> k=v ...]",
            file=sys.stderr,
        )
        sys.exit(2)

    url = sys.argv[1]
    client = MCPStreamableClient(url)

    print(f"MRL_MCPClient_Streamable_v1 — origin_signature={ORIGIN_SIGNATURE}")
    print(f"→ initialize {url}")
    info = client.initialize()
    print(f"  server: {info.get('serverInfo')}")
    print(f"  protocol: {info.get('protocolVersion')}")

    if len(sys.argv) >= 3 and sys.argv[2] == "call":
        name = sys.argv[3]
        args: Dict[str, Any] = {}
        for pair in sys.argv[4:]:
            k, v = pair.split("=", 1)
            try:
                args[k] = json.loads(v)
            except (ValueError, json.JSONDecodeError):
                args[k] = v
        print(f"→ call {name} {args}")
        print(json.dumps(client.call_tool(name, args), ensure_ascii=False, indent=2))
    else:
        print("→ list_tools")
        for tool in client.list_tools():
            print(f"  - {tool.get('name')}: {tool.get('description')}")


if __name__ == "__main__":
    _demo()
