# MRL 資料／系統模型／能力 回收 Runbook R03（Issue #146 資料回收線）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 當下狀態 2026-10-19 ｜ 本檔不含任何帳號、信箱、帳務或雲端資料夾 ID

## 原則
- 目標：把散在各平台的 MRL 資料、系統模型、能力**收回 DL580 本機**，以 DL580 為準；平台只當暫時來源。
- 只新增、不刪除、不覆蓋。回收驗證完成前，不解除任何 Manus 綁定、不刪除任何平台資料。
- 看不到 ≠ 不存在：未驗證的一律標「待驗證」。

## 步驟
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
- 沒有備份包時，官方說明稱無法從服務端取回已刪任務資料；已向 Manus 真人客服書面追問帳號類型與服務端保留（回覆待追蹤）。
- Cloud Computer 檔案不在備份內；GitHub 匯出僅為額外冗餘。

## 不在本腳本範圍（待處理）
- DL580 本機現況盤點（需在 DL580 上執行）。
- Cloudflare D1／KV／Workers 匯出。
- Manus 站點的實際資料庫內容。
