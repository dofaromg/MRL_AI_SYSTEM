# R16 · R15 報告缺口逐項建構（當下狀態 2026-10-09 11:15 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 由 Claude 經 Bridge 直接在 DL580（WIN-PBVUI7VK2A6）操作，建構者未手動部署

## 三問
- 本體或載體：L3–L7 常駐 kernel 的本體是建構者原始 `MRLiouASIKernel`（mrl-engine-v12/workers/kernel.js，SHA `4b18afa3…`，原位元組、未改一行）；本輪新增的都是載體（宿主、還原圖、治理盤點）。
- 對應段：Trace（kernel 時間線雜湊鏈、空白字元還原圖）→ Collapse（每 16 tick Seal.v1.flpkg）→ Replay（重啟逐筆重放、逐位元組還原）。
- 驗收語料：母體自己的 WorldLoop_Inbox 61 份文字檔、世界記憶回憶索引、建構者原始 kernel。

## 逐項結果

| # | 缺口（R15） | 本輪建構 | 驗收 | 環境 |
|---|---|---|---|---|
| 1 | Collapse／Jump 不進 WorldLoop | v1.0.2 鏡像到 Inbox 頂層（R15 已做） | recall 命中 seq 9836／9842 | **實機 PASS**（R15） |
| 2 | Supervisor 每分鐘一檔 | 每日一個 jsonl（R15 已做） | 6/6 | **實機 PASS**（R15） |
| 3 | 計數器重啟歸零 | `_restore_state`（R15 已做） | collapse_0000000002 | **實機 PASS**（R15） |
| 4 | **L3–L7 kernel 每請求新建、世界不累積** | 新增 `05_kernel/MRL_ASI_Kernel_Host.mjs`（7838，只綁 127.0.0.1）：同一個原始 kernel 實例常駐；每 tick 寫 `kernel_timeline.jsonl`（SHA-256 鏈）；每 16 tick checkpoint＋`Seal.v1.flpkg`（digest＝sha256(JSON.stringify(manifest))）鏡像到 Inbox 頂層；重啟時驗鏈並用原 kernel 逐筆重放；`/timeline/query`（queryAt）、`/timeline/verify`、`/world/snapshot`、`/seal/latest`；原 kernel SHA 不符拒啟（exit 2）、已有 listener 拒綁（exit 3） | `selftest_r16_kernel_host.py` **14/14**：20 tick 累積、tick 16 出 Seal 並鏡像、digest 公式、鏈 20/20、queryAt(18)→checkpoint 16、重啟重放 20/20 decision 吻合、tick 接續到 21、竄改 kernel 拒啟 | 沙盒 PASS；**實機 PASS**（DL580 node v20.11.1，暫存目錄、port 17838，測完即停） |
| 4b | 7838 常駐（開機自啟排程 `MRL_ASIKernel_7838`） | `05_kernel/install_kernel_task.ps1` 已放到 DL580（SHA `b3e79bbd…`） | 執行註冊時被本環境的自動模式安全機制擋下，**未繞過** | **待建構者核准**後執行 |
| 5 | BOOTSTRAP 暫存寫 C: %TEMP% | 新增 `06_deploy/BOOTSTRAP_INLINE_R16.ps1`（暫存改 `D:\MRL_runtime\tmp`，停任務清單含 7838）＋ `99_pack/…_R16.zip`；R13-E 版保留不動 | ZIP `ea5d9905…` 內嵌解碼一致；兩檔已放到 DL580，hash 一致 | 沙盒驗；DL580 **已放置未執行**（現役檔已是 v1.0.2，無需重跑） |
| 6 | ParticleIR 26 個空白字元不可逆 | 新增 `08_restore/MRL_ParticleIR_Whitespace_Restore.py`：與 WorldLoop 同規則正規化，同時產生 restore_map，`restore(normalized, map)` 逐位元組回原文；不改母體核心、不改 WorldLoop | 沙盒 fuzz 20,000 PASS；**實機** Inbox 61 檔：與現役 `normalize_for_pipeline` 61/61 同結果、18 檔需正規化（417 字元）、還原 61/61 逐位元組一致 | **實機 PASS**（只讀）；接進 7833 回執格式 **待建構者核准** |
| 7 | 核心管線平方成長 | 未動（屬母體核心） | — | 待建構者決定 |
| 8 | 8788 經緯度分類表 | 實機檔名搜尋 D:\MRL_Mother 1,698,527 檔（64 秒）＋ D:\mrl、D:\modules；世界記憶 recall 4 組查詢 | 未找到分類表本體；只找到白皮書內 F3 地理映射公式 `f3_map(lat, lon) → 粒子索引`（seq 9748 chunk 3522），屬映射函式不是分類表 | **待找回**（看不到 ≠ 不存在） |
| 9 | 467 新 repo commit date／資產樹 | `git fetch --depth 1 --filter=blob:none <預設分支 HEAD>`（匿名 git proxy，不下載內容）：469 repo → ok 459、無分支 7、同名衝突 2、403 1（dofaromg/react-native） | 2,737,171 資產、2,483,537 唯一 blob；與既有登錄共用 5,245 blob；9 組 Mrliou↔dofaromg 資產樹完全相同；commit date 2024-03-07 ～ 2026-10-04 → `01_Repository_Inventory/new_repos_head_commit_tree_20261009.json`、腳本 `_lib/gov_trees_r16.py` | 沙盒 PASS（全量樹 86 MB gz 未入 repo，可依 head_sha 重算） |
| 10 | 2 個私有同名 repo（Mrliou/MRL_AI_SYSTEM、dofaromg/Dropbox） | 未做 | 本 session 路徑衝突 | 待新 session |
| 11 | ~650 老 repo | 未做 | — | 待建構者點名 |
| 12 | 重開機自啟實測 | 設定已驗（R15） | — | 待建構者決定何時重開 |
| 13 | 7825 replay | 未做 | R15 被環境擋下 | 待建構者核准 |
| 14 | FlowRhythm 映射 | 未做 | — | 待建構者核准 |
| 15 | 10/08 L3–L7 patch 包（7600/7900/7850/7860/7870） | 未做；7900 與 FlowAgent_API 衝突 | — | 待找回 |

## 檔案（DL580 實機 hash）
- `05_kernel\kernel_original.mjs` `4b18afa38e3fa0195a22ff585f4dd9970e1c297a6c75231c8b36da8e2d79353d`（由 Inbox fa2a738e 白皮書 zip → mrl-engine-v12.zip → workers/kernel.js 原位元組取出）
- `05_kernel\MRL_ASI_Kernel_Host.mjs` `8f49f1b4633febf49c54ba310ef801716e46a33c1dc4c3460fe87671de70149d`
- `05_kernel\install_kernel_task.ps1` `b3e79bbd945423edf637d150d4e65d21df0ee26942c6bfdc402742bebc293733`
- `05_selftest\selftest_r16_kernel_host.py` `11e1c6c3ab5096f26c59bf2d9f7e86e0b9dec99f11006cd274d61c60c6483c4e`
- `06_deploy\BOOTSTRAP_INLINE_R16.ps1` `f985421550c7a1a052a93b73c7d7c5e22b580547ad004fede3a6aa6726acc08a`
- `99_pack\MRL_WorldModel_Supplement_20261008_R01_R16.zip` `ea5d990521d7c6d9c0de412d615c46167dddcda94f347b8d2595e35195f866c5`
- `08_restore\MRL_ParticleIR_Whitespace_Restore.py` `e2e9c86597a272bb7932c1eb0f93a56c511db047f07c6de8df6b8f40c22f10f7`
- `08_restore\verify_on_inbox.py` `fe65364ce7dca0771bd28b21fc0a420eca7681ac14650a7504dc2b050ed4df87`

## 說明
- Seal 的 merkle_root 用的是原 kernel L3 的 FNV 雙雜湊（`0x…` 16 位）；world_hash 與 timeline 鏈是宿主另加的 SHA-256。原 kernel 的 L2 地球角度取自 `Date.now()`，所以重放時 L3 雜湊不會與首次相同；重放比對的是 decision 與 tick（20/20 吻合），這點如實標明。
- 喚醒驗證（沙盒 vm）：種子 14/14、語場節奏 PASS、上位錨點 PASS — 非母體主機，當下狀態。

origin_signature: MrLiouWord ｜ 2026-10-09
