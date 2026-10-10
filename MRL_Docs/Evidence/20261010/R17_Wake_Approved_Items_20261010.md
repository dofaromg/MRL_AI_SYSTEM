# R17 · 喚醒復盤＋建構者核准項目執行（當下狀態 2026-10-10 12:25 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 經 Bridge 直接操作 DL580（WIN-PBVUI7VK2A6）
依據：建構者 2026-10-10 12:08「都需要，主線目標一樣復盤不變」

## 喚醒（實機）
- Bridge 3.1.0 api／pg／redis true；DL580 開機時間 2026-10-03 02:13；C: 剩 3.0 GB（10/09 為 4 GB），D: 3,185 GB。
- 監聽：3000、7500、7700、7816、7825、7826、7827、7833、7834、7835、7836、7837、7900、8788、18888。7838 未常駐（見下）。
- 排程：Jump_7837／Collapse_7835／Guardian_7836／Supervisor／WorldLoop／Convergence 等 Running。
- `wake_verify.py`（D:\MRL_AI_SYSTEM 種子）背景執行中，收據產出後補記。上一份實機收據 2026-10-01 18:53。
- **另一位執行者今天在改 WorldLoop**：`MRL_WorldLoop_Service.py` 12:13:54 改為 v1.2.3（JSON 不合法改走 text 管線），另有 `.staged-v1_2_2`、`.bak-20261010-v1_2_2`。本輪因此不動 WorldLoop 服務檔。

## 逐項

| 項目 | 結果 | 環境 |
|---|---|---|
| 核心管線平方成長 | 找到原因：`MRL_ReplayRestore_Core.execute()` 每 8 步 deepcopy＋序列化整個 state（applied 隨步數增長）→ O(n²)。v1.1 改為延遲物化 checkpoint，內容與 hash 與原版逐位元組相同。沙盒：隨機 300/300 等價；60k 事件 105.6 s → 0.1 s；全管線 20,000 行 5.2 s → 0.92 s，replay／restore／structurefield／mrliouir／verification 全同 | 沙盒 PASS |
| 　部署到 DL580 | 先備份 `MRL_ReplayRestore_Core.py.bak-20261010-R17`（A622EDEA…＝原版），新檔已寫入，hash `f85eee0b…` 一致 | **實機已部署**；DL580 上的等價測試第二次執行被環境安全機制擋下 → **待實機驗** |
| 　生效 | 已在跑的 7833 仍用記憶體內舊版；下次 WorldLoop 重啟才載入 | 待重啟後驗 |
| ~650 老 repo＋2 私有同名 repo | DL580 本地 bare 鏡像（MRL_Reclaim_20260927）唯讀全量盤點：1,151 repo（ok 1,135、無分支 16）、6,362 分支、3,804,157 資產；**682 個不在先前登錄**（即先前看不到的老 repo）；先前登錄中 31 個不在鏡像（9/27 之後的 repo）。Mrliou/MRL_AI_SYSTEM（私有）：main、2026-05-01、90 資產；Mrliou/Dropbox、dofaromg/Dropbox：空 repo | **實機 PASS**（58 秒）；全量資產樹 `asset_trees.jsonl.gz`（119 MB）留在 DL580 `D:\MRL_Mother\Governance\MRL_Global_Repository_Asset_Governance_v1\R17_Mirror_Inventory_20261010\`；摘要入 repo `01_Repository_Inventory/dl580_mirror_inventory_1151_20261010.json` |
| 7838 常駐排程 | 再次執行 `install_kernel_task.ps1` 被環境安全機制以「未授權常駐」擋下，未繞過 | 待建構者在此 session 明確授權 |
| 7825 replay | 需要讀 DL580 上的軌跡檔；本輪讀取被擋 | 未做 |
| FlowRhythm 映射核准 | 未做（需讀 7825／7827 核准機制） | 未做 |
| 還原圖接進 7833 | WorldLoop 正由另一執行者修改中，不重疊動手 | 待協調 |
| 重開機實測 | 未做（需先確認 Bridge 自啟；且屬常駐／全機操作） | 未做 |

origin_signature: MrLiouWord ｜ 2026-10-10
