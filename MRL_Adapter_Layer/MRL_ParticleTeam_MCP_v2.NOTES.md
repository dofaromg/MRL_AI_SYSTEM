# MRL_ParticleTeam_MCP_v2 — 母體自生強化版註記

origin_signature: `MrLiouWord`
derives_from: `MRL_ParticleTeam_MCP_v1.ts`（MR.liou 原作;吸收保存,**保留不改**）
status: 強化派生;**未經 runtime 驗證**（需 Cloudflare/D1 + `ANTHROPIC_API_KEY`）;未部署,不宣稱上線

## 為什麼有 v2

v1 是「材料進母體」的**原始保存本**,依主權律不靜默改寫。code review(CodeRabbit / Copilot)對它提了
一組部署前強化。本檔 v2 是**母體自生**的強化派生,把那些強化實作為碼(v1 仍原樣保留於同層)。

## v2 相對 v1 的強化(逐條對應 review)

| 項目 | v1 | v2 |
|---|---|---|
| 端點驗證 | `/mcp`/`/sse`/`/dispatch` 無驗證 | Bearer(`env.MCP_ACCESS_TOKEN`);**未設 token → 503 fail-closed**(rl_00 deny-by-default) |
| CORS | `Access-Control-Allow-Origin: *` | 白名單(`env.MCP_ALLOWED_ORIGINS`);**無 wildcard** + `Vary: Origin` |
| callAgent 逾時 | 無 | `AbortController` + 30s;`finally` 清 timer |
| 回應形狀 | `data.content[0]?.text`(content undefined 會先丟) | `data.content?.[0]?.text` |
| 錯誤字串 | reason 直接插值(可能 `[object Object]`) | `errText()` 正規化 |
| `/dispatch` 錯誤 | 無 try/catch(繞過 CORS) | try/catch + `task` 驗證,錯誤帶 CORS 回 JSON |
| 平行 duration | 共用 `startTime`(每 agent 都=整批) | **每 agent 各自計時** |
| lint | `substr`;switch case 宣告洩漏 | `slice`;`agent_direct` 以 `{ }` block scope |
| 任務持久化 | instance `Map`,跨 request 失效 | **D1(`env.DB`)持久化**;無 DB → 誠實降級為 isolate 級 in-memory + 警示 |

## 審查後補強(CodeRabbit / Copilot)

- **型別自足**:新增最小 `D1Database` 介面(本 repo 無 workers-types),純 TS 亦可型別檢查。
- **任務狀態一致**:`dispatch` 的 synthesize/最終落庫包 try/catch,失敗改標 `failed` 並落庫,不再永久卡 `processing`。
- **型別驗證**:`Task.type` union 補 `full_team`;`dispatch` 對未知 type **fail-fast**(不再靜默退回 analyst)。
- **MCP 相容**:JSON-RPC notification(無 `id`)回 **204**;新增 `ping`;成功 `tools/call` 附 `isError: false`。
- **CORS 安全**:回填前對 `Origin` 去除 CR/LF(防 header-injection)。
- **D1 效能**:`ensureSchema` 以 per-isolate flag 只建一次,不在每次 put/get 跑 CREATE TABLE。

## 誠實邊界

- **未經 runtime 驗證**:本檔為靜態強化;沒有 Cloudflare/D1/金鑰無法端到端跑。沙盒僅做結構檢查
  (括號平衡、無 `substr`、無 wildcard ACAO)。要上線需在 Cloudflare 設 `MCP_ACCESS_TOKEN` /
  `MCP_ALLOWED_ORIGINS` / D1 binding,或 **re-home 至 DL580 runtime**(母體本體優先)。
- **model id** 仍為原碼值 `claude-sonnet-4-20250514`;接母體時建議改走母體 model gateway 統一解析。
- v1 為 byte source-of-record 的原始材料,**不刪、不取代**;v2 僅為並存的自生強化。

> 依 rl_11/rl_15:v1 材料不刪;v2 為母體自生強化,非母體外流。
