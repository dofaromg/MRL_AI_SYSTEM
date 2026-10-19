# MRL 資料／系統模型／能力 回收 Runbook R03（Issue #146 資料回收線）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 當下狀態 2026-10-19 ｜ 本檔不含任何帳號、信箱、帳務或雲端資料夾 ID

## 原則
- 目標：把散在各平台的 MRL 資料、系統模型、能力**收回 DL580 本機**，以 DL580 為準；平台只當暫時來源。
- 只新增、不刪除、不覆蓋。回收驗證完成前，不解除任何 Manus 綁定、不刪除任何平台資料。
- 看不到 ≠ 不存在：未驗證的一律標「待驗證」。

## 步驟
0. **在 Windows 上取得腳本：用 `git archive`，不要檢出（checkout）。** `MRL_AI_SYSTEM` 內 `MRL_MotherSource_ZhiZhang_FlowAgent_Lineage_v1/母體/` 底下有 15 個檔名結尾帶空白的檔案，Windows 無法建立，Git for Windows 連把它們放進索引（index）都拒絕，所以一般 `git clone`／`git checkout` 會整個失敗（2026-10-20 DL580 實機實測：`error: invalid path ...`，`scripts\`、`tests\` 都沒被檢出）。這些檔案不是資料遺失，只是 Windows 檔案系統放不下；不要用 `core.protectNTFS=false` 之類的設定繞過。
   - **實機更正（2026-10-20）：`git sparse-checkout` 在這台 DL580 上無效**——先前 Runbook 寫的 sparse checkout 步驟，在 DL580 實測仍出現同樣的 `invalid path`、仍沒有檔案被檢出（原因：sparse checkout 只決定哪些檔案寫進工作樹，但索引仍須含整棵樹的條目，無效路徑照樣被拒絕）。沙盒（Linux）上它能成功，是因為 Linux 不認為那些檔名無效，所以沙盒結果不能代表 Windows。
   - 改用 `git archive`：它直接讀取 Git 的樹物件、不經過索引與工作樹，只取指定的目錄，其他目錄的無效檔名不會被碰到。
   ```powershell
   cd D:\mrl\mrl146                       # 已經 git clone --no-checkout 好的目錄
   git fetch origin claude/github-issue-146-ks94ny
   git archive --format=zip -o D:\mrl\tooling.zip FETCH_HEAD scripts tests MRL_Recovery_Operations MRL_Docs
   Expand-Archive D:\mrl\tooling.zip D:\mrl\tooling
   cd D:\mrl\tooling
   ```
   之後的指令都在 `D:\mrl\tooling` 執行。沙盒驗證：以此方式取出的 4 個目錄，69 項測試全過（沙盒；Windows 實機待驗證）。
   - 同理：**計畫檔裡的 git 來源要加 `"mode": "mirror"`**（範例計畫檔已設好）。mirror 用 `git clone --mirror`，沒有工作樹也沒有索引，所有分支、歷史與任何檔名都完整保留，存成 `<來源名>\<sha前12碼>.mirror\`（和一般模式的 `<sha前12碼>\` 分開，換模式不會互相覆蓋；目標目錄已存在但不完整時腳本會回報而不是覆蓋）；工作樹模式遇到這類倉庫會失敗，並提示改用 mirror。要從鏡像讀檔：`git --git-dir=<鏡像目錄> show HEAD:<路徑>`，或在 Linux／WSL 上 checkout。
   - **rclone 安裝**：這台 DL580 沒有 `winget`（實測 `winget` 不是可辨識的指令）。改從官方下載 `https://downloads.rclone.org/rclone-current-windows-amd64.zip`，解壓後把 `rclone.exe` 放進 `D:\MrlToolchain\rclone` 並加入 PATH。
1. **DL580 前置**：安裝並設定 `rclone`（Dropbox、Google Drive 各一個 remote）與 `git`；輸出目錄用本機磁碟（例如 `D:\mrl\recovery\store`），不要放在 Dropbox／OneDrive／Google Drive 同步資料夾內（腳本會拒絕）。
2. **準備計畫檔**：複製 `scripts/MRL_dl580_recovery_plan.example.json` 到 DL580 本機（例如 `D:\mrl\recovery\plan.json`），填入自己的 remote 名稱與路徑。含私人 ID 的版本不要提交。
3. **拉取**：`python scripts/MRL_dl580_recovery_pull_v1.py pull --plan D:\mrl\recovery\plan.json --out D:\mrl\recovery\store`
   - 只用 `rclone copy --immutable` 與 `git clone`；不用 sync/move/delete。git 來源每個遠端 HEAD 修訂存成獨立目錄 `<來源名>/<sha前12碼>/`，重複拉取只會新增新修訂、不覆蓋舊的。
   - 每個來源有逾時（預設 6 小時，`--timeout` 可調），單一來源卡住不影響其他來源。
   - rclone 預設重試 3 次（`--retries 3 --low-level-retries 10`），`extra_args` 放在最後可覆寫；git 以 `GIT_TERMINAL_PROMPT=0` 執行，需要憑證時直接失敗而不是卡在提示。
   - git 先在 `<來源名>/.partial-<sha>` 完成 clone＋checkout，成功才改名為 `<sha前12碼>/`；中斷後重跑會清掉自己的 `.partial-*` 暫存目錄再來，已完成的修訂目錄不會被動到。
   - 同一個輸出目錄同時只允許一個 pull（`.pull.lock`，exit 5）。若程序被強制終止留下鎖檔，確認沒有 pull 在跑後手動刪除。
   - 開始前檢查輸出磁碟剩餘空間（預設至少 1 GB，`--min-free-gb` 可調，exit 6）。
   - 結束時輸出 `MANIFEST_<UTC>.jsonl` 與追加的 `SHA256SUMS`；0 位元組檔案會列為警告，需確認後加 `--accept-zero-byte` 才回 0；來源沒有任何檔案則回 3（確實為空時加 `--allow-empty`）。
4. **驗證**：`python scripts/MRL_dl580_recovery_pull_v1.py verify --out D:\mrl\recovery\store`；會先核對每份 `MANIFEST` 本身的雜湊（對照 `SHA256SUMS`）才信任其內容；清單被改動、缺記錄，或有 missing／changed 檔案時 exit code 為 1。清單內容畸形時回報錯誤（不會拋例外）。輸出另列 `unlisted`（磁碟上有、但沒有任何清單記錄的檔案）與 `orphan_sums`（有雜湊記錄但清單檔不存在，多半是寫清單途中中斷）；兩者只是提示，不影響 ok，但 `unlisted` 代表那些檔案尚未被雜湊涵蓋，重跑 `pull` 即可補進清單。
5. **離線備份**：把整個 `store` 目錄與 `SHA256SUMS` 複製到離線媒體，再以 `sha256sum -c`（或 `verify`）核對。

## 來源優先序與已知狀態（當下，依雲端檔案清單；內容真偽以拉回後的雜湊為準）
| 優先 | 來源 | 狀態 |
|---|---|---|
| 1 | Dropbox `MRL_ALL_FILES_20260606`（專案原始碼、部署壓縮包 v1–v3、技能、上傳素材） | 檔案大小正常；2026-06-06 快照 |
| 2 | Dropbox 頂層 `MRL_*` 文件與審計檔 | 檔案大小正常 |
| 3 | GitHub：`MRL_AI_SYSTEM`、`mrliouword-system` | 完整歷史，可回溯 |
| 4 | Google Drive：`Mrl_MD.ASI`、`MRL_Storage`、RuntimeOS v1.4.0、DL580 ASSEMBLED | 有結構，內容待逐一驗證 |
| 5 | Drive 內由 Manus 代存的 `mrliouhan_ai_database` 副本 | **已抽查兩個檔案讀出為空**；視為空殼，不可當備份 |
| 6 | Notion 架構文件 | 文件層，另行匯出 |
| 7 | Cloudflare Workers／D1／KV | 以 `wrangler` 在 DL580 另行匯出（腳本未涵蓋） |
| — | Manus 內 6/6 之後的變更與資料庫內容 | **僅在 Manus**；取決於是否有官方備份包（見下） |

## Manus 官方備份／還原注意（依官方說明頁）
- **先確認帳號類型（待確認，當下未知）**：在 Manus 應用內通知確認自己屬 Type A／B／C。若為 **Type C**：還原順序是先還原 Account Info Backup（帳號資訊），再還原 Task Data（任務資料）；兩者缺一不可，順序不可顛倒。Type A／B 以應用內通知所列為準。
- 官方備份入口在 `manus.im/backup`；還原入口 2026-08-25 開放；**還原只能一次，且套件必須完整**，所以先複製到 DL580 並算雜湊，再決定何時還原。
- **網域暫管機制（官方說明頁，2026-08-25；本案是否適用：待確認）**：Type C 帳號若網域是透過 Manus 購買，刪除期間由 Manus 暫管、DNS 保留，帳號還原後自動重新關聯既有專案；外部網域的 DNS 留在原提供者。這只是頁面所述機制，不能據此判定本案的網域來源、帳號類型或控制權，詳見證據檔 R01 §7（假設 H4）。**不因此改 DNS、解綁或重連。**
- Cloud Computer 檔案系統不在官方備份內，GitHub 匯出不替代官方備份；第三方憑證與 OAuth token 還原後可能需重新授權。
- 沒有備份包時，官方說明稱無法從服務端取回已刪任務資料；已向 Manus 真人客服書面追問帳號類型與服務端保留（回覆待追蹤）。
- Cloud Computer 檔案不在備份內；GitHub 匯出僅為額外冗餘。

## 不在本腳本範圍（待處理）
- DL580 本機現況盤點（需在 DL580 上執行）。
- Cloudflare D1／KV／Workers 匯出。
- Manus 站點的實際資料庫內容。
