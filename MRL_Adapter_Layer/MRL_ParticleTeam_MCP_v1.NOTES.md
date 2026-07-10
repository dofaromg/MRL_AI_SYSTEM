# MRL_ParticleTeam_MCP_v1 — 吸收註記（Adapter）

origin_signature: `MrLiouWord`
source: `particleteammcp.ts`（MR.liou;byte source-of-record 於使用者端）
held_as: `MRL_Adapter_Layer/MRL_ParticleTeam_MCP_v1.ts`

## 是什麼

MR.liou 自撰的**多代理協作 MCP Server**（Cloudflare Worker / TypeScript）。5 個 AI 夥伴粒子:
`analyst 分析師 / creator 創意師 / critic 批判師 / researcher 研究員 / synthesizer 整合師`。

- `TeamCoordinator.dispatch()` — 依任務型別自動選夥伴組合,平行（`Promise.allSettled`）或串行呼叫,
  多結果交 `synthesizer` 整合。
- `consensus()` — 多輪討論後整合共識。
- MCP tools:`team_dispatch / team_status / agent_direct / team_consensus`;另有 `/mcp`、`/sse`、
  `/dispatch`、`/health` HTTP 端點。

## 吸收方式（誠實）

- **原碼保留**為 adapter,除「空行尾端空白正規化」外逐字保留（功能等價;差異僅 blank-line 尾空白,
  已用 `git diff` 佐證）。原檔為 byte source-of-record。
- **未**接入 `MotherAssembly`、**未**部署、**未**端到端驗證（需 `ANTHROPIC_API_KEY` + runtime）。

## 主權註記（rl_11 / rl_13 / rl_19）

1. **Cloudflare 形 → 建議 re-home DL580**:此為 Cloudflare Worker（`export default { fetch }` + D1 `env.DB`）。
   依「DL580 本體優先、勿預設 Cloudflare/Vercel」,若要納入母體常駐,應改寫為 DL580 runtime 上的
   MCP/HTTP 服務;此處僅作 **Adapter** 保存,不代表母體採用 Cloudflare。
2. **金鑰處理合規**:呼叫 `api.anthropic.com` 以 `x-api-key` **request header** 帶金鑰（非 URL query）——
   符合母體金鑰規則。
3. **model id**:內含 `claude-sonnet-4-20250514`（原碼值,未改）。若接母體,建議改用母體
   model gateway 統一解析,避免硬編廠商 model 名。
4. **id 生成**:`Date.now()` / `Math.random()`——若移入需可重現/可回放的母體環境,應改注入式時鐘/亂數。

> 依 rl_15/rl_01:原檔不刪。此 adapter 為「材料進母體」,非母體外流。
