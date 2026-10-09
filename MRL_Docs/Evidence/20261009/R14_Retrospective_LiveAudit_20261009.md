# R14 · 復盤＋實測報告：MRL 世界模型本地伺服器（DL580）

origin_signature: MrLiouWord ｜ Additive-Only ｜ **當下狀態 2026-10-09 09:55–10:00 Asia/Taipei（實機 WIN-PBVUI7VK2A6）**

## 0. 實測方法（這份報告的數字從哪來）

- **通道**：bridge.mrliouword.com（Bridge 3.1.0）唯讀端點 `/MRL_ls`、`/MRL_cat`、`/MRL_sysinfo`，以及 `/MRL_run` 執行**唯讀**查詢（HTTP GET 本機 health、`Get-ScheduledTask`、`Get-NetTCPConnection`）。本輪**沒有寫入、沒有停止、沒有重啟**任何東西。
- **獨立驗算**：把 DL580 上的 `jump_ledger.jsonl`、`.fltnz`、guardian receipt 原始位元組拉回沙盒，用 Python 重新計算雜湊，不採信服務自己的回報。
- 母體主機：48 CPU、記憶體 1919.9 GB（用 10.2%）、主機 uptime 546,076 s（約 6.3 天）、Bridge 開機 2026-10-08T10:32Z。

## 1. 關於「7500 第一次經帳本留痕的生成」這句話

這句話**不是本對話中我寫的**。實測證據顯示「第一次」不成立：

| 來源 | 實測內容 |
|---|---|
| 7500 `/health` | `total_requests: 1`、`total_tokens_generated: 587`；**boot_time = 2026-10-07 13:30:38 (+08)**，程序 PID 20580 建立於同一時間 → 計數器只涵蓋這次啟動後 |
| `D:\mrl\inference\last_chat_result.txt`（2026-04-13 15:17Z） | `{"ok":true,"response":"Hello!", ... "mrl_ops":{"BIND":1,"AMPLIFY":3,"COLLAPSE":3,"SPAWN":1},"origin_signature":"MrLiouWord","session_id":"15461b79-…"}` → **2026-04-13 已有帶 origin_signature 與 session_id 的生成紀錄** |
| `D:\mrl\inference\law_test.txt`（2026-04-13 16:10Z） | world_deltas / persona_deltas（MRL_Analyst）/ particles_created → 同日已有生成並寫回世界狀態 |
| `D:\mrl\inference\` 檔案序列 | 2026-07-10 `patch_persist.py`、`patch_rag*.py`、`bak_…_citeprompt` 等多版 → 7 月已有持續的生成迭代 |
| `/catalog` | 在 7500 / 7900 / 3000 / 7825 皆回 404 → 「integrations.AI false→true」本輪**無法驗證**，需知道 /catalog 實際在哪個服務 |

結論：`requests 原本是 0` 只代表 **2026-10-07 13:30 這個程序實例**之前沒有請求；母體上的生成至少可追到 2026-04-13。以單一服務當下計數判定「第一次」屬於局部視角升格全局（違反喚醒規則）。

## 2. 本輪工程時間線（R13 → R14）

| 輪 | 時間 (+08) | 內容 | 結果 |
|---|---|---|---|
| R13 | 10-08 08:06 | 依截圖比對本體五段＋四節奏，補 Jump / Collapse / Guardian / Supervisor 四模組（純 stdlib） | 沙盒 54/54 |
| R13-A | 10-08 15:53 | 加 BOOTSTRAP.ps1；修 Start-Process redirect 參數衝突 | 實機：ZIP 不在 DL580，找不到 |
| R13-B | 10-08 22:17 | BOOTSTRAP_INLINE（ZIP base64 內嵌），從 GitHub raw 直接拉 | 實機：解壓 17 檔 OK；中文亂碼、wake 掛 |
| R13-C | 10-08 22:40 | 4 個 .ps1 加 UTF-8 BOM＋console UTF-8 | 實機：中文正常；7834 被占 |
| R13-D | 10-09 08:45 | Jump 7834→7837；獨占綁定＋綁前探測；Supervisor 以 service 名稱驗身；停止範圍只限本 pack 路徑 | 沙盒 17/17（真 HTTP 撞 port 重現） |
| R13-E | 10-09 09:10 | 改名前先離開目錄；仍占用則解到新版本目錄 | **實機：三服務驗身 ALIVE、Supervisor 6/6** |
| R13-F | 10-09 09:34 | 實機 Jump×2 → Collapse → Replay；Guardian 語料查詢 | **實機 PASS** |
| R14 | 10-09 09:55 | 本報告：全面唯讀實測＋獨立驗算 | 見下 |

git（分支 `dl580-tunnel-recover-20261004`）：`bd83729` R13 → `e29bb36` → `3ccc6a1` → `680a1ab` → `620c545` R13-D → `12119bb` R13-E → `dce536b` → `287ceb4` R13-F。

## 3. 實測現況（2026-10-09 ~09:57）

### 3.1 本 pack（MRL_WorldModel_Supplement_20261008_R01）

| 項目 | 實測 | 狀態 |
|---|---|---|
| 7837 MRL_Jump_Service v1.0.1 | LISTEN 127.0.0.1 PID 15632；health ALIVE uptime 1466 s | **實機 PASS** |
| 7835 MRL_Collapse_Service v1.0.1 | LISTEN 127.0.0.1 PID 14648；ALIVE | **實機 PASS** |
| 7836 MRL_AnalystGuardian_Agent v1.0.1 | LISTEN 127.0.0.1 PID 47244；ALIVE | **實機 PASS** |
| 排程任務 MRL_Jump_7837 / Collapse_7835 / Guardian_7836 / WorldModel_Supervisor | Running、SYSTEM、AtStartup、lastRun 09:31:31（lastResult 267009 = 執行中） | **實機 PASS** |
| 舊任務 MRL_Jump_7834 | Disabled（未刪除） | **實機 PASS** |
| Supervisor 週期報告 | `supervisor\` 54 份、每 60 秒一份；最新 `014415Z…015415Z` 皆 6/6 all_green、anomalies 0；7834 列 observe_only = MRL_Convergence_Runtime | **實機 PASS** |
| Jump ledger 雜湊鏈 | 2 筆（seed Mrl_Zero.Origin.v1）；**沙盒獨立重算 prev/this 全對**，tail `a8300445…` | **實機資料＋獨立驗算 PASS** |
| `.fltnz` 封存 | `collapse_0000000001_d88fffb76efb.fltnz` 941 B；FLTNZ-1、origin_signature；**獨立解壓重算 state_hash = manifest**；內含 jumps 與 ledger 完全一致 | **PASS** |
| Guardian receipt | `guardian_0000000001_b82711d581c6.json`；sha256 獨立重算一致；query「分析師守護者」hits 3；7816/7833/8788 live | **PASS** |
| **7833 WorldLoop 吸收 .fltnz** | `/recall?q=collapse_0000000001` 無此檔；WorldLoop 設定只觀測 `WorldLoop_Inbox` **最上層**（`glob("*")` 不遞迴、只收檔案），我寫在 `collapse\` 子目錄 | **FAIL — 我的設計錯誤** |
| 重開機後自動起來 | 未重開 | 待實機 |

### 3.2 母體其他服務（唯讀觀測，本 pack 不擁有）

| Port | 服務 / 程序 | 綁定 | 實測 |
|---|---|---|---|
| 3000 | node `dist\index.js` | `::` | LISTEN |
| 7500 | MRL_Particle_Inference_Engine 1.0.0（`MRL_Inference_API.worldrecall_v4.py`） | 0.0.0.0 | Qwen2.5-32B-Instruct loaded；6×V100-32GB（用 8.4–11.7 GB/張）；requests 1（自 10-07 13:30 起） |
| 7800 | MRL_Bridge_API 3.1.0 | 0.0.0.0 | pg true（198 tables）、redis true |
| 7812 | `MRL_Memory_Engine.cjs` | `::` | LISTEN |
| 7816 | MRL_ReasoningEngine 1.0.0 | 0.0.0.0 | ALIVE uptime 546,034 s；**排程 MRL_ReasoningEngine = Disabled**（由其他方式啟動） |
| 7825 | MRL_Module_Integration_20261001_R06（node） | 127.0.0.1 | LISTEN；`/health` 404 → 健康端點路徑待確認 |
| 7826 | MRL_flowcore_adapter.py | 127.0.0.1 | LISTEN；`/health` 401（需授權） |
| 7827 | MRL_FlowRhythm_Module 0.2.0 | 127.0.0.1 | **ALIVE，ledger_events 7**（R05/R07 模組，實機在跑） |
| 7833 | MRL_WorldLoop_Service 1.2.1 | 127.0.0.1 | cycles 2666、daemon_iter 3017、errors 0、last_seq 9810、recall docs entity 4848 / source 60075 |
| 7834 | MRL_Convergence_Runtime 1.0.1 | 127.0.0.1 | ALIVE，PID 23316 不變 |
| 7900 | MRL_FlowAgent_API 1.1.0 | 0.0.0.0 | 7 個資料庫 true、dict_loaded 10 |
| 8788 | ParticleGlobe（particle_globe_memory_system.py） | 127.0.0.1 | ALIVE |
| 18888 | WorldModel_Continuation_20260930_R01 | 127.0.0.1 | LISTEN（WorldLoop 的 world_url） |

### 3.3 全域資產治理層（R08–R12，repo 側）

491 repos / 1,520 branches / 3,389 nodes / 5,455 edges / 47 跨 repo HEAD 鏡像組（R12，commit `4363228`）。未變動。待辦不變：2 個同名私有 repo、467 個新 repo 的 commit date / asset tree、~650 個老 repo 名單。

## 4. 問題與缺口（如實）

**我造成的：**
1. `.fltnz` 寫在 `WorldLoop_Inbox\collapse\` 子目錄，WorldLoop 不遞迴 → **Collapse 與 WorldLoop 目前沒有接上**。README 原寫「7833 會自動吸收」是未驗證的假設，已由本報告更正。
2. Supervisor 每分鐘一個檔案 → 每天 1,440 檔、每年約 52 萬檔。符合只增不刪，但檔案數會失控；應改為每日一個 append-only jsonl。
3. 本輪部署過程的錯誤：選 port 撞到 7834、`HTTPServer` 預設允許同 port 雙綁、清除指令範圍太寬（Convergence 沒被停到是運氣）、.ps1 沒 BOM、改名前沒離開工作目錄、Supervisor 對 7834 的假陽性（`supervisor_2026-10-09T003532Z.json` 保留，以 R13-D Evidence 更正）。均已修正並實機驗過。

**觀測到的（非本 pack，供建構者判斷）：**
4. **C: 只剩 4.0 GB**（D: 3,200.7 GB）。BOOTSTRAP 的暫存寫在 `%TEMP%`（C:）。
5. 7500 / 7800 / 7816 / 7900 綁 `0.0.0.0`（非僅本機）；防火牆是否擋外部本輪未查。
6. 排程 `MRL_ReasoningEngine` 為 Disabled，7816 由其他方式啟動 → 重開機後是否會起來未知。
7. 7825 `/health` 404、7826 需授權 → R07 的 FlowRhythm→7825 整合本輪無法驗證。
8. `/catalog` 位置不明。

## 5. 建議下一步（需建構者決定，未執行）

1. **接上 Collapse → WorldLoop**：Collapse 在既有 `collapse\` 之外，**另寫一份到 `WorldLoop_Inbox` 最上層**（.fltnz 原檔＋一份可讀 `.md` 跳點摘要），不改 WorldLoop 設定。驗收：下一個 cycle 後 `/recall?q=collapse_0000000001` 命中。
2. Supervisor 改為每日一個 jsonl（舊檔保留）。
3. 方便時重開機一次，驗四個排程自動起來（含 7816 的啟動方式）。
4. 告訴我 /catalog 在哪個服務，我把「integrations.AI」那條實測核對。
5. 你文件裡自列的待辦（Build_20261007_d.md）：FlowRhythm 映射核准；核心 ParticleIR 26 個空白字元還原；8788 經緯度分類表待找回。

## 6. 版本雜湊

- ZIP `4f4feac63773ad2ecd7de7fde1aa5942491ae0d7c6d8d0451076becd5dfd77ca`
- BOOTSTRAP_INLINE.ps1 `cf1892be62d20f852209c584bea79967eae40258fdb15da62472e8d8fe9a5c25`
- 沙盒測試：selftest_r13d_ports 17/17、jump 10/10、collapse 13/13、guardian 15/15、e2e_unit 16/16

origin_signature: MrLiouWord ｜ 2026-10-09
