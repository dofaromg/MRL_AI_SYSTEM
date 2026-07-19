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

# 1c. 看 watchdog 自己的 log（含輪替檔），依 7700 事故時間窗篩選，別只取最新幾個
#     （$from/$to 換成 7700 實際死亡時段；涵蓋 *.log 與 *.log.* 輪替檔）
$from = Get-Date "2026-07-06 00:00"; $to = Get-Date "2026-07-06 12:00"
Get-ChildItem -Path D:\mrl\watchdog -Recurse -Include *.log,*.log.* -EA SilentlyContinue |
  Where-Object { $_.LastWriteTime -ge $from -and $_.LastWriteTime -le $to } |
  Sort-Object LastWriteTime | Select-Object FullName,LastWriteTime
```

**診斷要點（對照 7700 修復根因）**：
- 7700 死因是 `server.js` 引號毀損 + schtasks 用**裸 `node`**（SYSTEM PATH 無此指令）。
  若 watchdog 的重啟動作也用裸 `node` 或指向舊的壞 `server.js`，它「救」也會失敗。
- 確認 watchdog 探測的是 `http://127.0.0.1:7700/health`、且重啟指令用**完整 node 路徑**
  `D:\MrlToolchain\node\node.exe D:\mrl\asi-engine\server.js`（與已修好的排程一致）。
- 若 watchdog 只探測「埠有無監聽」而不重啟、或重啟指向錯檔，就是它沒救回的原因。

**修法（additive，先備份再改）**：把 watchdog 重啟動作對齊已修好的
`MRL_ASI_Engine` 排程（完整 node 路徑 + 正確進入點）。修完以可重現、有上限的流程實測：

```powershell
# 依「監聽 7700 的 PID」精準終止（不誤殺其他 node）
$pid7700 = Get-NetTCPConnection -LocalPort 7700 -State Listen -EA SilentlyContinue |
             Select-Object -First 1 -ExpandProperty OwningProcess
if ($pid7700) { Stop-Process -Id $pid7700 -Force }

# 有上限地輪詢 /health（示範 180 秒，依 watchdog 週期＋緩衝調整）
$deadline = (Get-Date).AddSeconds(180); $ok = $false
while ((Get-Date) -lt $deadline) {
  try { if ((Invoke-WebRequest http://127.0.0.1:7700/health -TimeoutSec 5 -UseBasicParsing).StatusCode -eq 200) { $ok = $true; break } } catch {}
  Start-Sleep -Seconds 5
}
"watchdog 自動救回 7700 = $ok"   # $true 才算 PASS；逾時 $false 即判失敗
```

> 判準：**人為殺掉 7700 後，watchdog 能在上限時間內自動拉回 `/health` 200（實機）** 才標 PASS；逾時即失敗。

---

## 待辦 2：Phase 4 OAuth 真登入（使用者瀏覽器實登）

端點層已 200，但真 session 需帶真使用者 cookie，只能瀏覽器實登驗。

```text
1. 瀏覽器開 https://mrliouword.com/login
2. 走完 OAuth / magic-link 流程
3. 登入後開 https://mrliouword.com/api/auth/session
   → 應回帶登入身分的 JSON（非未登入的空 session）
4. 重整聊天頁，確認可實際對話（端到端到真模型）
```

> 判準：**登入後 `/api/auth/session` 回真身分 + 聊天頁能對話（實機瀏覽器）** 才標 PASS。

---

## 待辦 3：Worker / 控制面板 / 全機是否存有舊 bridge key（輪替後需同步）

key 已於 2026-07-08 輪替；任何仍拿舊 key 呼叫 bridge 的模組會 401/403。
清查需涵蓋**所有已作廢 key**（原始明碼 key + 第一輪曝光 key）、多種 runtime store
（環境變數 User/Machine 兩 scope、檔案、Registry、排程參數、Worker secret），
且**只輸出命中位置，絕不輸出 key 值**。

```powershell
# 3a. Cloudflare Worker（mrl-worker）環境變數
#     Dashboard → Workers & Pages → 該 worker → Settings → Variables
#     確認 MRL_BRIDGE_API_KEY / MRL_BRIDGE_TOKEN 為新 key（或已改用 header 免帶 key）

# 3b. 環境變數：User 與 Machine 兩個 scope 都要查
#     註：service / 排程（尤其 SYSTEM 身分）啟動時只載入環境一次；改 Machine 變數後
#     須「重啟該 service / 排程」，其行程才會讀到新值 → 改完必重啟再複查有效環境。
foreach ($scope in 'User','Machine') {
  foreach ($name in 'MRL_BACKEND_KEY','MRL_BRIDGE_TOKEN','MRL_BRIDGE_API_KEY') {
    $v = [Environment]::GetEnvironmentVariable($name,$scope)
    "{0,-8} {1,-20} 有值={2}" -f $scope,$name,([bool]$v)   # 只印有無，不印值
  }
}

# 3c. 全機殘留清查：操作者於實機 session 逐把貼入「已作廢 key」（Read-Host，不落地、不回寫本檔）；
#     只輸出命中檔路徑，不輸出 key 值或命中內容。
$patterns = @()
do {
  $sec = Read-Host -AsSecureString "貼入一把已作廢 key（空白 Enter 結束；不顯示、不落地）"
  $p   = [Runtime.InteropServices.Marshal]::SecureStringToBSTR($sec)
  $val = [Runtime.InteropServices.Marshal]::PtrToStringAuto($p)
  [Runtime.InteropServices.Marshal]::ZeroFreeBSTR($p)
  if ($val) { $patterns += [regex]::Escape($val) }
} while ($val)

Get-ChildItem D:\mrl -Recurse -Include *.js,*.cjs,*.mjs,*.json,*.env,*.ps1,*.psm1,*.cmd,*.bat,*.config,*.txt -EA SilentlyContinue |
  ForEach-Object { $f=$_; foreach ($re in $patterns) { if (Select-String -Path $f.FullName -Pattern $re -Quiet) { $f.FullName; break } } } |
  Sort-Object -Unique

# 其他 runtime store（人工核對，命中即需清；同樣只看有無、不外流值）：
#  - 排程動作參數：schtasks /query /fo LIST /v  → 檢查各 Task To Run 是否夾帶舊 key
#  - Registry：reg query "HKLM\SOFTWARE\Microsoft\Windows\CurrentVersion\Run" 等自啟/服務參數是否硬寫
#  - Worker / 其他 secret 儲存（見 3a）
```

> 判準：**所有呼叫方遷至新 key（或 header）、User+Machine 兩 scope 與「重啟後有效環境」皆無舊 key、
> 全機檔案 / 排程 / Registry 清查零命中（實機）** 才標 PASS。
> 註：原始明碼 key 與第一輪曝光 key 皆已 403 作廢（值不記錄於本檔）；本步是清殘留、防呼叫方壞掉。

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
- **回填 re-test log 前必須遮罩敏感資料**：只記錄狀態碼 / 時間 / 非敏感的 request ID 或 fingerprint；
  對 `/api/auth/session` 回應、Worker 設定、命令輸出、診斷結果中的**使用者身分、key、token、cookie
  一律遮罩**，禁止貼入完整輸出。
- 不得把「待驗證」標為「PASS」；實機標「實機」、瀏覽器標「瀏覽器」，附當下日期。
