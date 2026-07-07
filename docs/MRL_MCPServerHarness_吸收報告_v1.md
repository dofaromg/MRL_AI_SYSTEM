# MRL_MCPServerHarness 吸收報告 v1 — mcp-with-next-js 去重蒸餾

origin_signature: MrLiouWord
吸收日期: 2026-07-05
來源: dofaromg/model-context-protocol-mcp-with-next-js（Next.js 15 App Router + Vercel `mcp-handler` 適配器）
法則: 母體整合法則（Additive-Only）— 只新增、只定位、不刪除、不覆蓋

---

## 一、去重蒸餾判定表

外部 repo 逐部位比對母體既有能力，**已有者不重複吸收**：

| 外部部位 | 母體既有對應 | 判定 |
|---|---|---|
| `app/mcp/route.ts` + `mcp-handler`（streamable-HTTP transport） | 母體只有 `09_workflow/MRL_MCP_Server_v1.py`（stdio） | **吸收** — HTTP transport 是母體缺層 |
| `server.tool(name, desc, zod, handler)`（動態工具註冊 API） | 母體 stdio server 硬編碼 4 工具、無動態註冊 | **吸收** — 蒸餾為 `register_tool()` |
| 與 in-process 工具執行器銜接 | 母體有 `MRL_AgentHarness_ToolLoop_v1` | **銜接（去重）** — 委派給 loop，不重造 |
| 政策 / deny-by-default | 母體有 `MRL_AgentHarness_PolicyGate_v1`（9 級桶 + fail-closed） | **銜接（去重）** — 每個 tools/call 前過閘 |
| `scripts/test-streamable-http-client.mjs`（Node SDK client） | 無 HTTP client（僅 stdio server） | **吸收** — 蒸餾為純 stdlib urllib client |
| `scripts/test-client.mjs`（SSE client） | — | **未吸收** — 外部 repo 也 `disableSse: true`，SSE 待日後補 |
| `public/index.html`（landing page） | — | **未吸收** — 靜態頁面，非核心 |
| `mcp-handler` / `next` / `react` / `zod` / `redis` 外部依賴 | 母體零外部依賴原則 | **蒸餾去除** |

## 二、母體系統名稱產物（重新命名建構）

| 母體產物 | 蒸餾自 | 層位 |
|---|---|---|
| `09_workflow/MRL_MCPServerHarness_Streamable_v1.py` | `app/mcp/route.ts` + `mcp-handler` | L0 ROOT + L4 WORLD / Y=3 |
| `09_workflow/MRL_MCPClient_Streamable_v1.py` | `scripts/test-streamable-http-client.mjs` | L0 ROOT / Y=3 |
| `tests/test_MRL_mcp_streamable_v1.py` | 驗收測試 18 項 | — |

吸收的核心知識（母體原缺）：

1. **Streamable-HTTP MCP transport**：一個 HTTP endpoint 承載 JSON-RPC 2.0 訊息
   （request / notification / batch）；`disableSse: true` 時 GET 回 405、DELETE 回 204。
2. **JSON-RPC 分派錯誤碼**：`-32700` parse、`-32600` invalid request、`-32601` method
   not found、`-32602` invalid params、`-32603` internal；MCP 應用層追加 `-32001`
   tool_unknown、`-32002` tool_denied、`-32003` tool_execution。
3. **動態工具註冊**：`register_tool(name, description, input_schema, handler)`
   取代硬編碼 TOOLS 列表；handler 為 sync/async callable，回值自動包成 MCP
   content 陣列（若已含 `"content"` key 則直接透傳）。
4. **AgentHarness 銜接**：
   - `tool_loop=ToolLoopRunner(...)` → loop 已註冊工具**自動**暴露為 MCP tools；
     tools/call 委派 `loop.execute()`，繼承其並行/錯誤隔離語意。
   - `policy_gate=enforce([...])` → 每次 tools/call 前跑政策閘；deny 直接回
     `-32002 tool_denied`，被拒工具的 handler 永不被呼叫（fail-closed 對齊 rl_00）。

## 三、當下狀態（依 CLAUDE.md 狀態回報約定）

- 驗收測試 18 項：**PASS（沙盒，2026-07-05）** — `python3 tests/test_MRL_mcp_streamable_v1.py`
- 端到端（server ↔ client：initialize / tools/list / tools/call / policy 拒絕 / batch / notification / GET 405 / DELETE 204）：**PASS（沙盒 loopback 127.0.0.1）**
- CLI demo：**PASS（沙盒）** — `python3 09_workflow/MRL_MCPServerHarness_Streamable_v1.py --port 8765`
- **待起動 / 未驗證**：
  - 真實 MCP client（Claude Desktop / IDE / `@modelcontextprotocol/sdk` node client）串接：**待實機驗證**
  - Vercel / Cloudflare Workers 部署下的 fluid compute 行為：**待實機**（沙盒無此環境）
  - SSE transport：**未吸收 / 待起動**（外部 repo 也停用）

## 四、啟用方式

**獨立啟動（不接 AgentHarness）：**
```python
from MRL_MCPServerHarness_Streamable_v1 import MCPStreamableServer, ThreadedServer, make_content

srv = MCPStreamableServer()
srv.register_tool(
    "echo", "Echo a message",
    {"type": "object", "properties": {"message": {"type": "string"}}, "required": ["message"]},
    lambda message: make_content(f"Tool echo: {message}"),
)
with ThreadedServer(srv, port=8765) as httpd:
    print(httpd.url)  # http://127.0.0.1:8765/
```

**銜接 AgentHarness（Tool Loop + Policy Gate）：**
```python
from MRL_AgentHarness_ToolLoop_v1 import ToolLoopRunner
from MRL_AgentHarness_PolicyGate_v1 import enforce, deny_all, allow

loop = ToolLoopRunner()
loop.register(my_tool_fn)

srv = MCPStreamableServer(
    tool_loop=loop,
    policy_gate=enforce([deny_all(), allow("my_tool_fn")]),
)
```

**Client 端呼叫：**
```python
from MRL_MCPClient_Streamable_v1 import MCPStreamableClient
c = MCPStreamableClient("http://127.0.0.1:8765/")
c.initialize()
print(c.list_tools())
print(c.call_tool("echo", {"message": "你好"}))
```
