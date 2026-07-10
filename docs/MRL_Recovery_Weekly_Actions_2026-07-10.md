# MRL Recovery Weekly Actions — 2026-07-10 週

origin_signature: MrLiouWord
週別: W28 · 2026-07-08 ~ 2026-07-13
基底: `MrliouAI` @ `dbd26f0`（最新 default 分支 tip）
法則: 依 CLAUDE.md 每項 PASS 必附**執行地點**（沙盒 / DL580 實機 / Cloud endpoint）

---

## 底線規則（此檔所有勾選項都要遵守）

1. **每項 PASS 必附執行地點**：`(沙盒)` / `(DL580 實機)` / `(Cloud endpoint)`
2. **沒實跑寫「待驗證 / pending」**，不得把 P1/P2 拉高階
3. **CI 未回傳 status ≠ CI green**：不能寫「CI 通過」；要寫「CI status 未回傳，無法判定」
4. **Additive-only**：所有動作只追加，不動已合併主線 commit
5. **`MRL_7700_ENTRY` + `x-api-key` header** 是 DL580 進入點契約，query string 傳 key 一律不接受
6. **勾選項**：完成後在對應 `[ ]` 改為 `[x]`，並在該項下追加**執行地點 + 憑證**（log 路徑 / commit SHA / dashboard 截圖檔名）

---

## P0 — 本週必做

### 1. DL580 7700 ASI Engine 重開機後驗證（實機）

**執行地點**：DL580 Windows 實機（WIN-PBVUI7VK2A6）
**契約來源**：PR #91 merge commit `ddce340`

- [ ] `schtasks /Query /TN "MRL_ASI_Engine"` → 確認開機自啟已註冊
- [ ] `netstat -ano | findstr :7700` → 必見 `LISTENING`
- [ ] `curl -s http://127.0.0.1:7700/health -H "x-api-key: <new_key>"` → 必回 `{"status":"PASS","origin":"MrLiouWord"}`
- [ ] 舊 key 呼叫 → 必回 401/403（key rotation 驗收）

**判 PASS**：四項全過才寫「實機 PASS」；缺一項寫「部分 PASS」+ 說明缺哪一項。
**憑證**：於 `08_sources/DL580_EvidenceChain/` 追加 `MRL_7700_health_2026-07-10.log`。

### 2. MRL_Watchdog 未自救 7700 的 root cause（實機）

**執行地點**：DL580 實機（併入 P0-1 SSH session）

- [ ] 讀 watchdog config，確認 7700 是否在監控清單
- [ ] 讀 watchdog 過去 24h log，找 7700 down 時的觀察 / 動作
- [ ] 依查明結果，開 issue 或直接補 config PR

**判 PASS**：root cause 一句話寫在此檔（不需修 code 也算 PASS，能講清楚就 close）。

### 3. Bridge tunnel 放行後重跑 recovery（實機 + Cloud）

**前置阻塞**：Cloud session / egress 政策未放行 `mrliouword.com`（含子網域）
**執行地點**：DL580 實機 + Cloud endpoint

- [ ] **等網路端放行** `mrliouword.com` 含子網域
- [ ] `bash scripts/MRL_bridge_recovery_run.sh all`
- [ ] `curl -v https://bridge.mrliouword.com/health` → 必 200，不能 CONNECT 403
- [ ] `curl -v https://mrliouword.com/api/mother/status` → DL580 母體回應

**判 PASS**：`{"ok":true}` + 母體 status JSON 兩端都回應，才寫「Bridge v3.1.0 實機 PASS」。
**失敗處理**：仍 403 → 記錄「阻斷點在 CONNECT tunnel 階段」，**不誤標 DL580 掛掉**。

### 4. GitGuardian 歷史 key dashboard 標 resolved（Cloud dashboard）

**執行地點**：GitGuardian dashboard（cloud）

- [ ] 確認 repo tip 已遮蔽（已完成）
- [ ] 確認歷史 commit 內含的 key **已於 DL580 端輪替作廢**（不是 repo 端修就好）
- [ ] 在 GitGuardian 每條 alert 手動標 resolved + 附註「DL580 端已 rotate SHA-256 hash，不落地」

**判 PASS**：dashboard 全綠 + 輪替憑證截圖存 `08_sources/DL580_EvidenceChain/`。

---

## P1 — 本週能做就做（不阻其他項）

### 5. MCP HTTP bridge 真實 client 驗證（沙盒 → 遠端）

**依賴**：對外 endpoint 存在（DL580 tunnel 通過 P0-3，或 Cloudflare Worker 見 P2）
**執行地點**：沙盒 → DL580 / Cloud endpoint

- [ ] 選一種真 client 驗證（不只 loopback）：
  - [ ] Claude Desktop 掛 `MRL_MCPServerHarness_Streamable` endpoint → 能 `tools/list` 到 `echo`
  - [ ] 或 `@modelcontextprotocol/sdk` node client（外部 repo 的 `scripts/test-streamable-http-client.mjs`）
  - [ ] 或某 IDE MCP integration
- [ ] 成功 `tools/list` + 成功 `call_tool` 才寫「MCP HTTP bridge 實機 PASS」

**憑證**：client 端截圖或 log 存 `08_sources/`。

### 6. MetaCode 原檔尋回 or 重建版降級標註

**執行地點**：repo 文件層 + `05_persona/` 血緣

**兩條路二擇一**：

- [ ] **(A) 尋回**：查 `08_sources/` / `MRL_ParticleArchive/` / `MRL_MotherSource_*/` 內是否有 `metacode_core.js` 原檔封存
  - 找到 → SHA256 比對 modules_index 登錄值 → 一致才寫「原檔尋回 PASS」
- [ ] **(B) 降級**：找不到就在 recovery manifest / `MRL_ABSORPTION.md` 明標
  - 「當前 `metacode_core.js` 為**重建版**、非原檔、不宣稱 SHA 等同」

**判 PASS**：任一條路寫入 evidence，這條就 close。

---

## P2 — 這週不強求，維持「待起動 / 待驗證」

**不修改狀態、不誤標 PASS**：

| 項目 | 當下狀態 | 何時可以標 PASS |
|---|---|---|
| qdrant | MCP config 佔位、無 service 定義 | 部署真實例 + 有 embedding 寫入驗證 |
| MinIO | 同上 | 部署真實例 + 存取物件驗證 |
| MetaEnv | 未實機 | 實機環境變數注入 + 端點回應 |
| SSE transport（MCP）| 未吸收、外部 repo 也停用 | 實作 + 有真 SSE client 收得到事件 |
| Vercel 部署 MCP Harness | 未部署 | fluid compute 端點回 `tools/list` |
| Cloudflare Workers 部署 MCP Harness | 未部署 | 同上 |
| OAuth 真人登入 | 只有端點 HTTP 200，未驗真人流程 | 瀏覽器 real login + session cookie 帶回 |

---

## 執行順序建議

```
週一 → P0-1 DL580 7700 驗證 + P0-2 watchdog root cause
週二 → P0-4 GitGuardian dashboard 標 resolved
週三 → 等 P0-3 tunnel 放行（若已放 → 跑 recovery script）
週四 → P1-5 MCP 真 client（用剛 recovery 好的 tunnel endpoint）
週五 → P1-6 MetaCode 尋回 or 降級標註 + 週回顧
```

---

## 週末回顧模板（下週一填）

**已 PASS 項**：（列勾選項 + 執行地點）
**部分 PASS 項**：（缺哪塊）
**Blocked 項**：（阻在什麼）
**維持 P2 待起動項**：（明列，不誤標）
**下週優先**：（三項以內）

---

## 記錄

| 提案時 | 週別 | 覆蓋範圍 |
|---|---|---|
| 2026-07-10 | W28 | DL580 7700 + Bridge + GitGuardian + MCP 真 client + MetaCode 尋回/降級 |
