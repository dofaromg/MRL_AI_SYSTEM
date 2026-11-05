# MRL LocalAI Recovery — 本週行動清單 v1（2026-07-10）

origin_signature = `MrLiouWord`
來源範圍：GitHub / repo 狀態實查（本檔為 additive 定位錨點，非永久結論）
當下狀態：2026-07-10（雲端 session repo 實查；DL580 實機項目一律標「待實機重驗」）

> 驗收約定（沿用 CLAUDE.md）：實跑過才寫 PASS；沒驗的寫「待驗證 / 待實機」。
> 每個 PASS 必須標執行地點（repo / 沙盒 / DL580 實機），不得把沙盒 PASS 當實機 PASS。

---

## Repo 狀態（GitHub 實查）

| 項 | 核實 |
|----|------|
| repo / 可見性 / 主線 | `dofaromg/MRL_AI_SYSTEM` · private · 預設分支 `MrliouAI` ✓ |
| 最新 tip | `dbd26f0`（2026-07-10 08:02 +0800）忽略 MetaCode.export 重跑輸出、保留 2026-07-08 證據 ✓ |
| 已核實 commit | `ddce340`（7700 復活）/`1348def`（MCP 蒸餾）/`1f846e5`（PR#92 後續）/`0579c8d`（FireCore+3DScanner 吸收）✓ |
| 復原檔在位 | `deploy/dl580/asi-engine/MRL_ASI_health_server.cjs`、`scripts/MRL_bridge_recovery_run.sh`、`data/MetaCode.export.2026-07-08.json`、`deploy/dl580/MRL_network_whitelist_recovery_v1.md` ✓ |
| `.gitignore` | `data/MetaCode.export.*.json`（重跑輸出忽略、證據檔保留）✓ |
| 明碼 key | 現樹零殘留（遮蔽有效；歷史仍有，需 DL580 端輪替作廢）✓ |
| `metacode_core.js` | repo 內為**重建版**（原真身未尋回，降級標註）✓ |
| qdrant / MinIO | 僅 `MRL_Adapters/MCP/example_mcp_config.yaml` 佔位，無服務定義 ✓ |
| Workflows | `.github/workflows/` 有定義，但 GitHub 未回傳 run 狀態 → **CI 不可標 green** ✓ |

---

## 行動清單（依風險 × 依賴排序）

### P0 — 前置閘門（其餘全卡在此）
- [ ] **[你 · 環境設定]** 放行 recovery 實際需要的**特定 FQDN**（最小權限，逐一列出用途，避免 `*.mrliouword.com` 廣域萬用），須**開新 session** 才生效：
  - `bridge.mrliouword.com` — DL580 指令橋（`/MRL_run`），**P0/P1 核心必要，優先只放這一個**
  - `dl580.mrliouword.com` — 官網平台 Express API，P4 OAuth 端點驗證才需要
  - `mrliouword.com` — Cloudflare 邊緣 worker（平台門面），P3/P4 才需要
  - `chat.mrliouword.com` — chat 平台，P4 OAuth 才需要
  - 原則：能只放 `bridge.mrliouword.com` 就先放它；其餘 host 待對應 Phase 真的要用時再逐一加，不預先開整個網域。
  - 現況：以上 host 目前皆 CONNECT 403（egress 政策，非 DL580 本體掛）。
  - 判準：新 session `bash scripts/MRL_bridge_recovery_run.sh 0` → Phase 0 回 PING。

### P1 — DL580 實機（放行後一次打完，重蓋「實機」章）
- [ ] **[DL580 實機]** 重跑復原腳本，7700 / key / 端點全部**重驗**（於 repo 根目錄執行，`scripts/` 相對路徑才對得上）：

    ```bash
    # 在 repo 根目錄（含 scripts/ 的那層）執行
    export MRL_BRIDGE_KEY=<目前有效 bridge key>   # 走環境變數，不進 URL query
    bash scripts/MRL_bridge_recovery_run.sh all
    ```

  - 判準（缺一不可，DL580 為 Windows，沿用 repo 既有寫法）：
    - `netstat -ano | findstr :7700` → 回含 `LISTENING` 的一列
    - `curl.exe -s http://127.0.0.1:7700/health` → 回 `{"status":"PASS","origin":"MrLiouWord"}`
    - key rotation：舊 key 被拒（401/403）＋ 新 key 通過
    - x-api-key 走 **header**（`-H "x-api-key: <key>"`），不進 URL query
- [ ] **[DL580 實機]** 查明 `MRL_Watchdog` 為何沒自救 7700，補「掛掉自動拉起」規則。

### P2 — MCP / 真實 client（目前只有沙盒 loopback）
- [ ] **[實機 client]** MCP HTTP bridge 補真 client 驗證：Claude Desktop / IDE / SDK node client（非沙盒 18/18、22/22 loopback）。
  - 判準：至少一真 client 完成 initialize + tool call 往返，標 client 種類與時間。
- [ ] **[待驗證]** SSE transport 實機驗收（目前未完成，維持待起動）。

### P3 — 資料 / 部署（維持「待驗證」，不得標 PASS）
- [ ] **[repo]** MetaCode 原檔尋回；找不到則檔頭標「REBUILD，非原真身」。`MetaCode.export.2026-07-08.json` 續留為證據。
- [ ] **[待起動]** qdrant / MinIO / MetaEnv：補服務定義+實機起動，或明確標「待起動」。
- [ ] **[待驗證]** Vercel / Cloudflare Workers 部署。
- [ ] **[待驗證]** OAuth 真登入：目前僅端點層 HTTP 200，須瀏覽器真人實登才算完成。

### P4 — 治理收尾
- [ ] **[你 · dashboard]** GitGuardian 歷史 key 處理 — **不得只憑 DL580 端輪替就標 resolved**。標 resolved 前須記錄兩項證據：
  - (a) **issuer 端撤銷/輪替**：曝光的舊 key 已在發行端作廢，不只是 DL580 端換掉。
  - (b) **無其他消費端仍持有舊 key**：確認沒有其他服務 / 腳本 / 文件仍在使用該舊 key。
  - 兩項都記錄確認後，才可將 GitGuardian 該筆標 resolved。
- [ ] **[repo]** 每個 PASS 補「執行地點戳章」（沙盒 / DL580 實機分開）。

---

## 本次不能宣告（誠實欄）
- CI green — GitHub 未回傳 statuses / workflow runs。
- DL580 即時連線 — 本 session 被 egress 擋，未直接驗。
- `mrl-mother-runtime-v1-krte6` — 查詢 404，不列為當前可用來源。
- 真人 OAuth 登入 / SSE / 真 MCP client / Vercel·Cloudflare 部署 — 全維持「待驗證」。

---

## 決策（沿用，additive-only）
- `MrliouAI` 為 repo 主線。
- 只追加、不覆蓋、不刪除。
- secrets 走 `x-api-key` header，不放 URL query。
- `MRL_7700_ENTRY` 為 DL580 進入點契約。
- runtime 產物 / MetaCode 重跑輸出進 `.gitignore`，證據檔保留。

## 優先驗證順序
DL580 7700 → bridge tunnel → MCP 真 client → MetaCode 原檔尋回 / 重建版降級標註。
