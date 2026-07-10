# MRL_7700_Watchdog_and_Hardening_Runbook_v1

origin_signature = `MrLiouWord`
當下狀態：2026-07-10（沙盒撰寫，供實機執行）；**全部項目待實機 / 待瀏覽器驗收**

> 前情：7700 ASI Engine 已復活（Phase 1/2 PASS 實機 2026-07-06，PR #91）、
> bridge key 已輪替（Phase 3 PASS 實機 2026-07-08）、官網端點層 200（Phase 4）。
> 本 runbook 收攏 `MRL_network_whitelist_recovery_v1.md` 末尾列出的 **4 項殘留待辦**，
> 每項給出可直接執行的指令；這些都在 DL580 實機 / 使用者瀏覽器 / Cloudflare 上執行，
> 雲端 session（egress 被擋）無法代跑。依 CLAUDE.md：實跑過才標 PASS，其餘維持待驗證。

---

## 待辦 1：追查 `\MRL_Watchdog` 為何沒自動救回 7700

背景：7700 死亡 8 小時期間 watchdog 未把它拉回。watchdog 是 DL580 上的
schtasks 工作（非 repo 原始碼），需在實機上查其定義與紀錄。

```powershell
# 1a. 看 watchdog 工作定義（觸發器 / 動作 / 上次結果 / 執行身分）
schtasks /query /tn "\MRL_Watchdog" /v /fo LIST

# 1b. 找出 watchdog 實際跑的腳本，讀它怎麼探測 + 重啟 7700
#     （把下面路徑換成 1a "Task To Run" 顯示的實際檔案）
Get-Content "D:\mrl\watchdog\<watchdog腳本檔>" -Raw

# 1c. 看 watchdog 自己的 log（若有），對照 7700 死亡時段有沒有嘗試重啟
Get-ChildItem -Path D:\mrl\watchdog -Recurse -Filter *.log -EA SilentlyContinue |
  Sort-Object LastWriteTime -Descending | Select-Object -First 3 FullName,LastWriteTime
```

**診斷要點（對照 7700 修復根因）**：
- 7700 死因是 `server.js` 引號毀損 + schtasks 用**裸 `node`**（SYSTEM PATH 無此指令）。
  若 watchdog 的重啟動作也用裸 `node` 或指向舊的壞 `server.js`，它「救」也會失敗。
- 確認 watchdog 探測的是 `http://127.0.0.1:7700/health`、且重啟指令用**完整 node 路徑**
  `D:\MrlToolchain\node\node.exe D:\mrl\asi-engine\server.js`（與已修好的排程一致）。
- 若 watchdog 只探測「埠有無監聽」而不重啟、或重啟指向錯檔，就是它沒救回的原因。

**修法（additive，先備份再改）**：把 watchdog 重啟動作對齊已修好的
`MRL_ASI_Engine` 排程（完整 node 路徑 + 正確進入點）。修完實測：
手動 `taskkill` 掉 7700 → 等 watchdog 週期 → 確認自動回到 `/health` PASS。

> 判準：**人為殺掉 7700 後，watchdog 能在其週期內自動拉回 `/health`（實機）** 才標 PASS。

---

## 待辦 2：Phase 4 OAuth 真登入（使用者瀏覽器實登）

端點層已 200，但真 session 需帶真使用者 cookie，只能瀏覽器實登驗。

```
1. 瀏覽器開 https://mrliouword.com/login
2. 走完 OAuth / magic-link 流程
3. 登入後開 https://mrliouword.com/api/auth/session
   → 應回帶登入身分的 JSON（非未登入的空 session）
4. 重整聊天頁，確認可實際對話（端到端到真模型）
```

> 判準：**登入後 `/api/auth/session` 回真身分 + 聊天頁能對話（實機瀏覽器）** 才標 PASS。

---

## 待辦 3：Worker / 控制面板是否存有舊 bridge key（輪替後需同步）

key 已於 2026-07-08 輪替；任何仍拿舊 key 呼叫 bridge 的模組會 401/403。

```
# 3a. Cloudflare Worker（mrl-worker）環境變數
#     Dashboard → Workers & Pages → 該 worker → Settings → Variables
#     檢查 MRL_BRIDGE_API_KEY / MRL_BRIDGE_TOKEN 是否為新 key（或改用 header 免帶 key）

# 3b. 控制面板（DL580 上，7950）讀的是環境變數 MRL_BACKEND_KEY
[Environment]::GetEnvironmentVariable("MRL_BACKEND_KEY","User")   # 是否為新 key
[Environment]::GetEnvironmentVariable("MRL_BRIDGE_TOKEN","User")  # bridge 模組用

# 3c. 全機搜殘留舊 key 明碼（值不記錄；比對是否還有硬寫）
Get-ChildItem D:\mrl -Recurse -Include *.js,*.json,*.env,*.ps1 -EA SilentlyContinue |
  Select-String -Pattern "MrLiouWord2026" -List | Select-Object Path
```

> 判準：**所有呼叫方改用新 key（或 header），舊 key 明碼全機清零（實機）** 才標 PASS。
> 註：`MrLiouWord2026` 及第一輪曝光 key 皆已 403 作廢，此步是清殘留、防呼叫方壞掉。

---

## 待辦 4：bridge 安全加固（DL580 伺服器端，需先遷移呼叫方）

`D:\mrl\bridge\server.js` 目前雙路徑驗證（`x-api-key` header 與 `?key=` query）、
`MRL_run` 以 GET query 收 `cmd`。兩者都會讓機密進 URL → 落 log / 歷史 / 截圖
（第一輪 key 即因此曝光）。

**順序很重要——先遷移呼叫方，再收緊伺服器，否則會打斷現有流量：**

1. 確認所有呼叫方（Worker / 面板 / 排程 / 本 repo 腳本）都已改用
   `x-api-key` header（本 repo `scripts/MRL_bridge_recovery_run.sh` 已是 header）。
2. 於 `server.js` **移除 `?key=` query 驗證路徑**，只留 header。
3. 將 `MRL_run` 由 GET query 收 `cmd` 改為 **POST body 收 `cmd`**；
   呼叫端 `mrl_run` 同步改 `curl -X POST --data`。
4. 每步先備份 `server.js.bak_harden_<date>`（additive），改完實測 `/health` 與
   一筆 `MRL_run` 仍通。

> 判準：**`?key=` 路徑移除後舊式呼叫被拒、header + POST 路徑仍通（實機）** 才標 PASS。
> 此為伺服器端契約變更，風險較高，建議與呼叫方一次對齊後再動。

---

## 驗收約定（沿用 CLAUDE.md）

- 本 runbook 為**沙盒撰寫的執行指引**，所有判準未實跑前一律「待驗證 / 待實機 / 待瀏覽器」。
- 每項完成後，把實測輸出補回 `MRL_network_whitelist_recovery_v1.md` 的 re-test log（additive）。
- 不得把「待驗證」標為「PASS」；實機標「實機」、瀏覽器標「瀏覽器」，附當下日期。
