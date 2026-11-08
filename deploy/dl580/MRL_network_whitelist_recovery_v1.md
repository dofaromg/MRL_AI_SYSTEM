# MRL_Network_Whitelist_Recovery_v1 — 雲端 session 網路放行與 bridge 復原

origin_signature = `MrLiouWord`
當下狀態：2026-07-06（沙盒 / Claude Code 雲端環境實測），**待放行後重驗**

---

## 現況（當下 2026-07-06，雲端 session 實測）

| 項目 | 狀態 |
|------|------|
| DL580 bridge 本體（`bridge.mrliouword.com`） | **活著**（使用者瀏覽器實測 `{"ok":true,"output":"PING"}`，實機） |
| 雲端 session → `bridge.mrliouword.com` | **封鎖**（agent proxy CONNECT tunnel 回 403，沙盒） |
| 雲端 session → `*.mrliouword.com` 全網域 | **封鎖**（bridge / dl580 / chat / 根網域皆 403，沙盒） |
| 7700 ASI Engine（`app\server.js`） | **紅**（面板顯示 DOWN，待診斷 — 見復原腳本 Phase 1） |
| bridge key | **舊 key 已在對話中曝光，待輪替作廢**（Phase 3） |
| 官網 OAuth / session | **待驗證**（Phase 4） |

> 結論：不是 DL580、不是 tunnel、不是 7700 的網路問題——是雲端環境的
> egress 網路政策把整個 `*.mrliouword.com` 擋在外面。依規不得繞過，只能放行。

---

## 放行步驟（使用者於環境設定操作，不在對話裡改）

1. 到啟動 session 的介面：claude.ai/code（網頁版）或 Claude Code 的
   **Environment settings / 環境設定**。
2. 找 **Network access（egress policy）** 設定。
3. 目前為受限政策 → 改為允許自訂網域，加入 **`mrliouword.com`（含子網域）**，
   或改用較寬鬆的網路政策。
4. 官方說明：<https://code.claude.com/docs/en/claude-code-on-the-web>
5. 放行後開新一輪對話（或重跑本 session），執行下方復原腳本。

---

## 放行後一次打完：復原腳本

腳本位置：`scripts/MRL_bridge_recovery_run.sh`

```bash
export MRL_BRIDGE_KEY=<目前有效的 bridge key>   # key 一律走環境變數，不得硬碼
bash scripts/MRL_bridge_recovery_run.sh all
```

| Phase | 內容 | 對應待辦 |
|-------|------|---------|
| 0 | bridge `/health` + `MRL_run` echo PING 連通性 | 前置 |
| 1 | 7700 診斷：netstat / node 命令列 / schtasks / 本機 health / log | ① 7700 為什麼紅 |
| 2 | 重啟 7700（schtasks 或 node 直啟），驗 `127.0.0.1:7700/health` | ① 復活 7700 |
| 3 | 產新 key、DL580 上換掉舊 key、驗「舊拒新通」 | ② key 輪替 |
| 4 | `mrliouword.com` 邊緣/轉發端點 + 登入端點狀態碼 | ③ 官網 OAuth |

Phase 1 的輸出會告訴你 Phase 2/3 需要的環境變數
（`MRL_7700_TASK` / `MRL_7700_HOME` / `MRL_BRIDGE_CONFIG` / `MRL_BRIDGE_TASK`），
可分段跑：`bash scripts/MRL_bridge_recovery_run.sh 1` → 設變數 → `... 2`。

---

## 驗收約定（沿用 CLAUDE.md / RuntimeOS 報告約束）

- 本文件所有「封鎖」結論為 **沙盒（雲端 session）當下狀態 2026-07-06**，
  放行後需重測，不是永久結論。
- 腳本每一 phase 以實際回應為準；沒實跑的項目一律維持「待驗證」。
- key 輪替完成的判準：**舊 key 被拒 + 新 key 回 NEWKEY（實機）**，缺一不可。

---

## Session re-test log（additive；只追加不覆蓋）

| 日期（環境） | 檢查 | 實測結果 | 判讀 |
|-------------|------|---------|------|
| 2026-07-06（雲端 session） | `MRL_BRIDGE_KEY` | 未設（`<unset>`） | key 走環境變數，尚未提供 → 無法過 Phase 0 `need_key` |
| 2026-07-06（雲端 session） | `curl https://bridge.mrliouword.com/health` | `CONNECT tunnel failed, response 403` | egress 政策擋 |
| 2026-07-06（雲端 session） | `curl https://mrliouword.com/health` | `CONNECT tunnel failed, response 403` | egress 政策擋（根網域也擋）|
| 2026-07-06（雲端 session） | agent proxy `/__agentproxy/status` | `recentRelayFailures`：`connect_rejected`「gateway answered 403 to CONNECT (policy denial or upstream failure)」，host `bridge.mrliouword.com:443` 與 `mrliouword.com:443` | **403 來自 gateway 的 CONNECT 拒絕，是本地 egress 政策，不是 DL580 / tunnel / 7700 的問題** |

> 判讀強化：403 出現在 **CONNECT tunnel 建立階段**（proxy relay `connect_rejected`），
> 代表封包還沒離開雲端環境就被本地政策擋下——與 DL580 本體、cloudflared tunnel、
> 7700 服務狀態無關。修法唯一路徑仍是上方「放行步驟」把 `mrliouword.com`
> （含子網域）加進 egress 白名單，放行後重跑 `scripts/MRL_bridge_recovery_run.sh all`。

---

## 實機修復記錄：7700 ASI Engine 復活（2026-07-06，DL580 實機，使用者 PowerShell 實跑）

繞道方案：雲端 egress 仍封鎖，但使用者本人就在 DL580 主機（`WIN-PBVUI7VK2A6`）上，
改以本機 PowerShell 直接執行 Phase 1/2（等效於復原腳本經 bridge 下的指令）。

### Phase 1 診斷（實機）

| 檢查 | 實測結果 | 判讀 |
|------|---------|------|
| `netstat -ano \| findstr :7700` | 無輸出 | 7700 無人監聽，服務死亡 |
| node 行程列表 | 有 bridge（`D:\mrl\bridge\server.js`）等 9 個行程，**無 ASI Engine** | 行程整個不在，非卡住 |
| `schtasks /query /tn "MRL_ASI_Engine" /v /fo LIST` | `Last Result: 1`；`Task To Run: node D:\mrl\asi-engine\server.js`；`Start In: N/A`；`Run As User: SYSTEM` | 排程存在但每次啟動即失敗 |
| 前景實跑 `D:\MrlToolchain\node\node.exe server.js` | `SyntaxError: Invalid or unexpected token`（第 1 行） | **根因：`D:\mrl\asi-engine\server.js` 檔案引號毀損**（疑為寫入時 shell 吞引號），Node 啟動即死 |
| 次要問題 | 排程用裸 `node`（SYSTEM PATH 無此指令）、無工作目錄 | 排程定義脆弱 |

### Phase 2 修復與驗證（實機）

修復步驟（additive：壞檔備份為 `server.js.broken-20260706`，不刪除）：

1. 重寫 `D:\mrl\asi-engine\server.js` 為零依賴版（Node 內建 `http`，不需 express；
   `/health` 回應維持 `{"status":"PASS","origin":"MrLiouWord"}` 原契約）。
   參考副本收錄於 `deploy/dl580/asi-engine/MRL_ASI_health_server.cjs`。
2. `schtasks /change /tn "MRL_ASI_Engine" /tr "D:\MrlToolchain\node\node.exe D:\mrl\asi-engine\server.js"`
   —— 改用完整 node 路徑，修掉裸 `node` 問題。
3. `schtasks /run /tn "MRL_ASI_Engine"` 由排程正式拉起。

> 路徑對齊註記：本文件前段與面板沿用的 `app\server.js` 為歷史紀錄路徑；
> **實機實際啟動檔為 `D:\mrl\asi-engine\server.js`**（排程已改完整路徑直啟）。
> `scripts/MRL_bridge_recovery_run.sh` Phase 2 的直啟進入點由 `MRL_7700_ENTRY`
> 環境變數控制（未設時沿用歷史預設 `app\server.js`）；在 DL580 實機上請設
> `MRL_7700_ENTRY=server.js` 與排程一致，其他部署維持各自實際進入點即可。

驗證（實機，2026-07-06）：

| 判準 | 實測結果 | 狀態 |
|------|---------|------|
| `netstat -ano \| findstr :7700` | `TCP 0.0.0.0:7700 LISTENING`（PID 13864）+ `[::]:7700 LISTENING` | **PASS（實機）** |
| `curl http://127.0.0.1:7700/health` | `{"status":"PASS","origin":"MrLiouWord"}` | **PASS（實機）** |
| 再次前景跑 server.js | `EADDRINUSE :::7700` | 反向確認：埠已被正式服務佔用（預期行為）|

> 當下狀態 2026-07-06：**Phase 1 / Phase 2 完成（實機 PASS，由排程拉起、開機自啟路徑已修）**。
> 待辦：Phase 3 bridge key 輪替（舊 key 已曝光，待作廢）、Phase 4 官網 OAuth 驗證、
> 追查 `\MRL_Watchdog` 為何未自動救回 7700。

---

## 實機記錄：Phase 3 key 輪替 / Phase 4 官網驗證（2026-07-08 台北時間；UTC 2026-07-07T17–18Z，DL580 實機）

### Phase 3 — bridge key 輪替

bridge 驗證機制（`D:\mrl\bridge\server.js`）：請求帶 `x-api-key` header 或 `?key=`
query，SHA-256 後與檔內 `API_KEY_HASH` 比對。原檔第 28 行以**明碼**硬寫舊 key。

輪替過程（additive：每輪均先備份 `server.js.bak_keyrotate*_20260708`）：

1. **第一輪**：改為只存新 key 的 SHA-256 雜湊（明碼自此不落地）、bridge 重啟成功
   （`/health` 回新 boot 時間）。但新 key 經 `Write-Host` 顯示於螢幕並隨截圖進入
   對話 → **視同曝光作廢**，執行第二輪。
2. **第二輪**：新 key 僅進剪貼簿（螢幕不顯示）→ `API_KEY_HASH` 換為第二輪雜湊
   → 收掉舊行程、`Start-Process` 重啟 bridge。

驗證（實機 2026-07-08 台北時間；bridge 回應 `_t` 為 `2026-07-07T18:35:58Z`）：

| 判準 | 實測結果 | 狀態 |
|------|---------|------|
| 曝光之第一輪 key | `HTTP 403` 拒絕 | **PASS（實機）** |
| 第二輪新 key | `{"ok":true,"cmd":"echo NEWKEY","output":"NEWKEY","_v":"3.1.0"}` | **PASS（實機）** |
| 原始明碼舊 key（已作廢，值不記錄） | `HTTP 403` 拒絕（首測誤打 `gcurl.exe` 未跑，2026-07-08 補實跑） | **PASS（實機）** |

> **Phase 3 結論（實機 2026-07-08）**：兩把舊 key 皆 403 被拒 + 新 key 回 NEWKEY
> ——依驗收約定「舊拒新通、缺一不可」，**key 輪替 PASS（實機）**。
> 新 key 僅存於使用者密碼管理器；server.js 僅存 SHA-256 雜湊，明碼不落地。
>
> 待辦：若官網 Worker / 控制面板 / 其他模組存有舊 bridge key，輪替後會 401/403，
> 需同步更新該處 secret。
>
> 安全加固待辦（採 CodeRabbit 建議）：bridge 目前同時接受 `x-api-key` header 與
> `?key=` query 兩種驗證路徑；key 進 URL 會落入 log / 瀏覽器歷史 / 截圖（本次
> 第一輪 key 即因此曝光）。建議在 DL580 的 `D:\mrl\bridge\server.js` 移除 `?key=`
> 路徑、只留 header 驗證——需先確認既有呼叫方（官網 Worker / 面板 / 排程）皆已
> 改用 header 再動手。`scripts/MRL_bridge_recovery_run.sh` 已改為 header 驗證。
>
> 安全加固待辦 2：`MRL_run` 目前以 GET query 收 `cmd`，Phase 3 的設定檔替換指令
> 會讓 key 內容隨 `cmd` 進入 URL / 行程參數。建議 bridge handler 改收 POST body
> 後，腳本 `mrl_run` 同步改為 POST——此為 DL580 伺服器端契約變更，需與既有
> 呼叫方一併調整，暫列待辦不在本 PR 內處理。

### Phase 4 — 官網端點（實機 2026-07-07/08）

| 端點 | 實測 | 狀態 |
|------|------|------|
| `/login` | HTTP 200 | PASS（實機，端點層） |
| `/auth/login` | HTTP 200 | PASS（實機，端點層） |
| `/api/auth/session` | HTTP 200 | PASS（實機，端點層） |
| SPA 頁面本體 | 正常送達（聊天頁 HTML/JS） | PASS（實機） |
| OAuth session 真登入 | 以使用者瀏覽器實登為最終判準 | 待驗證（實機瀏覽器） |
