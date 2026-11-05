# MRL_Bridge_MCP — 原生 C MCP 伺服器（MinGW-W64 / Windows / stdio）

`origin_signature: MrLiouWord` (LAW-0) ｜ 純 C ＋ cJSON ＋ WinHTTP ｜ 對接你的 Bridge `127.0.0.1:7800`（`D:\mrl\bridge` / bridge.mrliouword.com）

讓 **Claude Desktop（或任何 MCP 客戶端）** 透過 8 個工具直接操作你的母體 Bridge：查 PostgreSQL、跑 DL580 指令、讀寫檔案、看粒子統計。JSON-RPC 2.0 走 newline-delimited stdio，零非系統 DLL、`-static`。

## 一、建置（Windows / MinGW-W64）

1. 依 `third_party/cjson/PLACE_cJSON_HERE.md` 放入 **cJSON v1.7.19**（`cJSON.c` + `cJSON.h`）。
2. 建置：
   ```
   make
   ```
   或一行 gcc：
   ```
   D:\MrlToolchain\mingw64\mingw64\bin\gcc.exe -O2 -Wall -Wextra -std=c11 -I. ^
     mrl_mcp_main.c mrl_mcp_jsonrpc.c mrl_mcp_tools.c mrl_http.c ^
     third_party\cjson\cJSON.c ^
     -o MRL_Bridge_MCP.exe -lwinhttp -static -s
   ```
   產物：`MRL_Bridge_MCP.exe`（零非系統 DLL）。

## 二、8 個工具 → Bridge 端點對應

| 工具 | 動作 | Bridge 端點 |
|---|---|---|
| `mrl_pg_query` | 跑 PostgreSQL 查詢（`{sql, params}`） | `POST /MRL_pg/query`（JSON body） |
| `mrl_run` | 在 DL580 執行 Windows 指令（`{cmd, timeout_sec?}`） | `GET /MRL_run?cmd=…` |
| `mrl_cat` | 讀檔（`{path}`） | `GET /MRL_cat?path=…` |
| `mrl_write` | 寫檔（`{path, content}`） | `GET /MRL_write?path=…&content=…` |
| `mrl_ls` | 列目錄（`{path}`） | `GET /MRL_ls?path=…` |
| `mrl_tables` | 列所有資料表 | `GET /MRL_tables` |
| `mrl_sysinfo` | 系統資訊 | `GET /MRL_sysinfo` |
| `mrl_particle_stats` | `mrl_particle`/`mrl_persona`/`mrl_memory` 列數合計 | 3× `POST /MRL_pg/query` |

> 端點路徑寫在 `mrl_mcp_tools.c` 最上方的 `MRL_EP_*` 常數 —— 若你 bridge server.js 的實際路由不同，改那幾行即可。GET 工具的參數一律 RFC 3986 percent-encode。

## 三、認證與 LAW-0

每個對 Bridge 的 WinHTTP 呼叫都帶：
- `x-api-key: MrLiouWord2026`（對齊 server.js `API_KEY_HASH`）
- `x-origin-signature: MrLiouWord`（LAW-0 provenance）

金鑰與端點常數在 `mrl_http.h`（`MRL_API_KEY`、`MRL_BRIDGE_HOST`、`MRL_BRIDGE_PORT`）。**切勿把金鑰寫進 log 或工具回傳文字。**

## 四、接進 Claude Desktop

把 `claude_desktop_config.example.json` 的 `mcpServers` 併進
`%APPDATA%\Claude\claude_desktop_config.json`（command 路徑用雙反斜線），重啟 Claude Desktop，看到鎚子圖示即成功。log 在 `%APPDATA%\Claude\logs\mcp-server-MRL_Bridge_MCP.log`。

## 五、Headless 煙霧測試（不用 Claude Desktop）

先確認 Bridge 本身活著：
```
curl.exe -s -H "x-api-key: MrLiouWord2026" "http://127.0.0.1:7800/MRL_tables"
```
再測 MCP 層（PowerShell）：
```
Get-Content .\smoke.jsonl | .\MRL_Bridge_MCP.exe
```
應看到：initialize 回你的 protocolVersion、tools/list 回 8 個工具、mrl_tables 回 Bridge 資料。

## 六、協定行為（依 MCP 2025-11-25）

- stdout **只**輸出 MCP 訊息；所有 log 走 stderr（`_setmode(_O_BINARY)` 防 CRLF 破壞解析）。
- `initialize` 回應 **echo 客戶端 protocolVersion**（allow-list 內），否則回 `2025-11-25`。
- `notifications/*` 靜默消費、不回覆；`ping` 回空 result。
- 協定錯誤（壞 JSON、未知方法）→ JSON-RPC error（-32700/-32601…）。
- **工具執行失敗**（Bridge 非 200 / 逾時 / 缺參數）→ 成功 result 但 `isError:true`（SEP-1303，讓模型可自我修正）。

## 七、驗證紀錄（當下狀態 2026-07-28，沙盒）

- 4 個 C 檔 `gcc -fsyntax-only -std=c11 -Wall -Wextra` **全通過**（portable 檔用真 cJSON API 對照；`mrl_http.c` 用 Win32 stub 對照）。
- **未在此環境完整編譯**（WinHTTP 為 Windows 專屬，此 Linux 沙盒無 winhttp.dll/mingw）。請在你的 `D:\MrlToolchain\mingw64` 依上方 Makefile 建置，並用 `smoke.jsonl` 實機驗收。

## 八、檔案

```
MRL_Bridge_MCP/
├── mrl_mcp_main.c        # stdio 迴圈、_O_BINARY、initialize/ping/tools 分發
├── mrl_mcp_jsonrpc.c/.h  # JSON-RPC 2.0：error/result/initialize 建構
├── mrl_mcp_tools.c/.h    # 8 工具 schema + dispatch + Bridge 呼叫
├── mrl_http.c/.h         # WinHTTP client + URL encoder（x-api-key/x-origin-signature）
├── third_party/cjson/    # 放 cJSON v1.7.19（見 PLACE_cJSON_HERE.md）
├── Makefile
├── smoke.jsonl
├── claude_desktop_config.example.json
└── README.md
```
