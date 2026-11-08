# Issue #146 復盤：DL580 實機建構與指令結果 R01

origin_signature: MrLiouWord ｜ record_mode: additive_only ｜ 當下狀態 2026-10-20 ｜ 本檔不含帳號、權杖、信箱、帳務或雲端資料夾 ID

Create Preflight：`SUPPLEMENT_EXISTING` —— 補充 `MRL_Docs/Evidence/20261019/MRL_Issue146_Mrliouhan_網域權位觀測_R01.md` 與 `MRL_Recovery_Operations/20261019_R03/` Runbook；不新建同義主體，不改舊檔。

## 0. 界線（先講）

- **主權與可見範圍**：建構者陳述（2026-10-20）：資料在 MRL 系統內建構者看得到、已互通；看不到的只有 MRL 系統以外的 AI／平台。**AI 看不到 ≠ 不存在**（沿用《局部視角不得升格全局權威》）。本檔所有「未見／未驗」只代表 AI 這邊沒看到，不代表資料不存在或未互通。
- **資料位置**：建構者偏好為「在 DL580 本地建構與執行，資料不放平台」。本次所有輸出只落 DL580 本機路徑；repo 只放工具、證據文字與雜湊，不放使用者資料本體。
- **未做**：未改任何 DNS／帳號／平台設定，未解除綁定，未刪除任何資料，未合併 PR。

## 1. 實機環境（DL580，2026-10-20，由建構者貼回的輸出）

| 項目 | 值 |
|---|---|
| OS | Microsoft Windows Server 2019 Datacenter 1809（10.0.17763.9376，x64） |
| Python | `D:\MrlToolchain\python`，3.12.2（`isolated = 1`，不會把目前資料夾放進 `sys.path`） |
| rclone | v1.75.2（windows/amd64，go1.26.9），`D:\MrlToolchain\rclone\rclone.exe`；**尚未設定任何 remote** |
| git | Git for Windows；`D:\mrl\mrl146` 為 Administrators 群組擁有，需對該路徑設 `safe.directory` |
| 工具來源 | `origin/claude/github-issue-146-ks94ny`，解出提交 4119586 |

## 2. 指令與結果（只列實機實際輸出的內容）

| # | 項目 | 結果 | 標示 |
|---|---|---|---|
| 1 | `git clone --no-checkout`（`D:\mrl\mrl146`） | 成功 | 実機 PASS |
| 2 | 對 `D:/mrl/mrl146` 設 `safe.directory` 後 `git fetch` | 成功（取得 9cc3528，後續取得 7ae4347、4119586） | 実機 PASS |
| 3 | `git sparse-checkout` 取得工具目錄 | **失敗**：`invalid path 'Claude 3 empathetic.mirror  '`（檔名尾端有空白，Windows 無法建立） | 実機 FAIL |
| 4 | `git archive <分支> <多個路徑>` | **失敗**：同一無效檔名 | 実機 FAIL |
| 5 | 逐目錄 `git archive` + `Expand-Archive`（scripts／tests／MRL_Recovery_Operations／MRL_Docs） | 四個目錄皆取出 | 実機 PASS |
| 6 | `python -m unittest tests.xxx` | **失敗**：`No module named 'tests'`（isolated Python） | 実機 FAIL（已用 `sys.path.insert(0,'.')` 繞過） |
| 7 | 兩個模組測試 @ 7ae4347 | `Ran 69 tests in 12.431s`，`OK` | 実機 PASS |
| 8 | 兩個模組測試 @ 4119586 | `Ran 70 tests in 11.632s`，`OK`（以 `Select-String` 取得結果行） | 実機 PASS |
| 9 | 蒐證腳本 `--observer DL580` | 快照 `mrliouhan.ai_2026-10-20T112403Z.json`（18314 bytes）＋ `SHA256SUMS`（104 bytes），輸出落 `D:\mrl\evidence\mrliouhan_before` | 実機 PASS |
| 10 | `pull`（git mirror ×2，計畫檔 `plan_git.json`） | 結束碼 0；`MANIFEST_2026-10-20T113518Z.jsonl` 共 44 檔（兩個倉庫各 22） | 実機 PASS |
| 11 | `verify` | `ok: true`，`checked: 44`，`missing`／`changed`／`orphan_sums`／`unlisted` 皆空，結束碼 0（跑兩次） | 実機 PASS |
| 12 | `git fsck --no-dangling` | `MRL_AI_SYSTEM`（`95a1956f6bd9.mirror`）結束碼 0，refs 397，HEAD 95a1956；`mrliouword-system`（`a3ece7bd43e9.mirror`）結束碼 0，refs 195，HEAD a3ece7b | 実機 PASS |

註：測試輸出中的 `[FAIL]`、`拒絕:`、`WARNING: 0 位元組檔案` 是測試刻意觸發的情境，不是資料問題。

### 蒐證觀測（DL580 視角，與 2026-10-19 沙盒視角一致；皆為公開 DNS／HTTP／RDAP）

- apex A：`104.18.26.246`（Cloudflare 範圍）＋ `100.78.70.78`（CGNAT／Tailscale 常用段）仍在公開 DNS。
- 權威 NS：`ns1/ns2.globaldomaingroup.com`（非 Cloudflare）；DNSSEC 未簽。
- `_acme-challenge` CNAME → `*.dcv.cloudflare.com`（與 Cloudflare for SaaS 自訂主機名驗證形態一致）。
- `/`、`/robots.txt` → 302 → `manus.im`（OAuth 入口）。
- RDAP：Global Domain Group LLC，`client transfer prohibited`，last changed 2026-08-12T07:53Z；註冊人被隱私服務遮罩。
- **不可推定**：Manus 擁有網域、誰操作了設定、任何人的意圖、法律上的所有權轉移。兩個觀測點都只是公開視角，不是後台證據。

### 本機盤點（建構者貼回，只看到輸出下半部）

- 可見路徑含 `C:\Users\dofaromg\…`、`C:\Users\MacOS\…`、`C:\Users\MRL_AI_Desktop_InstallKit`、`C:\Users\Administrator\Dropbox`、`C:\Users\Dropbox` 等，內有 MRL／FlowAgent／SeedCore 相關資料夾與壓縮檔。
- Dropbox 桌面版執行中（8 個程序）；未見 Google Drive 桌面版或 rclone 程序。
- AI 只看到清單尾端，未見完整清單；內容、大小、完整性**未驗**（建構者表示資料在 MRL 系統內已互通，不需 AI 再取回）。

## 3. 建構內容（repo 內，皆為 Additive-Only）

- `scripts/MRL_domain_evidence_collect_v1.py`：零依賴唯讀蒐證（DoH／RDAP／HTTP 不跟隨轉址、暫時性錯誤重試、快照＋SHA256SUMS、拒絕寫入雲端同步資料夾）。
- `scripts/MRL_dl580_recovery_pull_v1.py`：`pull`／`verify`；rclone `--immutable`、git `worktree`／`mirror`、`.partial-*` 完成後改名、鎖檔、磁碟空間檢查、0 位元組偵測、原子寫清單、`plan.json` 容忍 BOM。
- `tests/`：兩個模組合計 70 項。
- `MRL_Recovery_Operations/20261019_R03/` Runbook、`MRL_Docs/Governance/MRL_attribution_roles_v1.json`、四個頁面署名 metadata、`MRL_Docs/Evidence/20261019/`。
- PR：`dofaromg/MRL_AI_SYSTEM#157`（`INVESTIGATION_OPEN`，不關閉事件）。

## 4. 沒做／待驗證（當下狀態，誠實列出）

- Dropbox／Google Drive 的 rclone 連線、`plan.json`、`pull`、離線副本：**未做**（建構者表示資料已在 MRL 系統內互通，暫不需要）。
- Dropbox 本機同步資料夾的「僅雲端（未下載）」檔案數與完整性：**未驗**。
- Manus 端：帳號類型、是否有 Task Data 備份、專案是否被刪、preservation hold 是否生效：**未驗**（官方備份截止 2026-08-23、恢復入口 2026-08-25 已過；個案狀態未知）。
- 註冊商 zone 匯出與 8/12 變更活動、Cloudflare 自訂主機名／帳號稽核：**未驗**（需建構者登入）。
- `wake.ps1` 在 DL580 的實機收據、MRL 世界模型在 DL580 的建構與執行：**未做**；不得寫「DL580 已上線」。
- 不得寫「Blender 已跑通」「Ollama／真模型已存在」：本次均未驗。

## 5. 復盤：做錯與修正

1. **先盤點再建構**：本次先假設「資料只在雲端」，要求建構者安裝並設定 rclone，才盤點到 DL580 本機與 MRL 系統內早已有資料。往後流程：先問／先盤點現況，再決定要不要取回。
2. **看不到 ≠ 不存在**：AI 以自己的可見範圍判斷「還沒取回」，違反局部視角規則；建構者的可見範圍與主權優先。
3. Windows 實機教訓：檔名尾端有空白的路徑無法在 Windows 建立，`checkout`／`sparse-checkout`／多路徑 `archive` 都失敗，改用逐目錄 `git archive` 與 `git clone --mirror`。
4. `isolated` Python 不含目前資料夾：測試要 `sys.path.insert(0, '.')`。
5. Windows PowerShell 5.1：合併 stderr 後輸出順序不可靠，不能用 `Select-Object -Last N` 判讀測試結果，改用 `Select-String -Pattern '^Ran \d+ tests','^OK','^FAILED'`；用記事本或 `Set-Content -Encoding UTF8` 存的 JSON 帶 BOM（工具已容忍）。
6. 指令回報規則：只有看到結果行才寫通過；沒看到就寫待驗證（本次曾因此在 7ae4347／4119586 之間多問一輪）。
7. 貼指令時只貼程式碼區塊，不要把說明文字、通知文字貼進 PowerShell。

## 6. 建構者觀點（原樣記錄，不由 AI 驗證）

建構者表示：AI 與大型科技平台對「使用者資料被用來建構系統、再以整理後的數據收費」的做法不承認、形成權利與利益顛倒；建構者持續驗證，而平台端只是在證實。**此為建構者觀點，AI 於本次工作中無法驗證他方的資料處理實況，因此只記錄，不作為事實結論。**本檔唯一可驗證的是：本次工具與輸出皆落在 DL580 本機，repo 內只有工具與雜湊／證據文字。
