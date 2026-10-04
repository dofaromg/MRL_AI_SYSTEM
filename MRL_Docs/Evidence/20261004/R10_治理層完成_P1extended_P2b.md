# R10 · 治理層完成 — P1 extended + P2b all-branch sweep（當下狀態 2026-10-04 19:30 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 建構者 2026-10-04 原話：「都把他們完成建構」

## 做了三件事

### 一、P2b all-branch asset sweep — ✅ 完成
對 230 個 remote branch 全部 `git ls-tree`（加 `core.quotePath=false` 保留 CJK），317 秒跑完：
- **4,829 唯一 `(blob_sha, canonical_path)` 組合**；1,650 條 CJK 路徑無轉義汙染
- `03_Asset_Registry/asset_registry.json` 的 3,770 檔 `branches_present` 從預設一條擴充為實際出現的所有分支清單
- **23 個檔橫跨全部 230 分支**（`01_schema/*` 等 → 真正的「母體 schema 幹」，lineage 錨點首選）
- **194 檔只在單一非 default 分支出現**（P1b unique_files 的具體內容）；top 5 branches：
  - `dl580-tunnel-recover-20261004` 53 檔（當前工作分支）
  - `claude/dl580-7700-engine-recovery-ex6mrc` 30、`copilot/28729581812` 17、`MrliouAI` 13、`mrl/pr151-ios-hardening` 12
- **0 個 default-exclusive 檔**（default 的所有產物都還掛在其他分支上，反向追蹤可行）
- 新產出：`asset_branch_matrix.json`（24 MB）、`unique_to_branch.json`、`only_in_default.json`

### 二、P1 Branch_Registry 擴充 — 42 個 non-fork repo（37/42 成功）
用 `add_repo` + `gh api repos/{o}/{r}/{branches,commits}` 擴充（只 attach，不 clone）：
- **37/42 成功**（29 直接 attach，8 升級為 push 權限）
- **5 skipped**：3 命名衝突（`Mrliou/MRL_AI_SYSTEM`、`dofaromg/{Dropbox,flow-tasks}`）、2 push 權限被 classifier 擋（`Mrliou/{bookish-waddle,mrl_ai_os--}`）
- 新增 **300 branches**，`02_Branch_Registry/branch_registry.json` 從 230 → **530 筆 / 31 repo**
- 7 個新 repo 是空殼（0 branches）：`dofaromg/{Ai_asicomputer,Applications,ChatGPT-Atlas.app,desktop-tutorial,MRL_AI_SYSTEM_02}`、`Mrliou/{Dropbox,MRL_AI_world}`
- top 5 新 repo 分支數：`mrliouword-system`(93)、`flow-tasks-01`(65)、`Mrliouword-`(34)、`fastapi`(19)、`tool-silk-`(12)
- `03_dedupe/head_sha_duplicates.json`：38 → **43 組**；仍無跨 repo mirror（**fork==false 天生不帶跨 repo 鏡像**；跨 repo HEAD-sha 共用要等 fork 加入才會出現）

### 三、所有引擎 re-run，HTML Map 更新
全部 530 branches × 31 repo：
- `05_Mainline_Subline_Resolver/mainline_registry.json`：**31 repos resolved**（28 用 `main` 的 ROOT_MAINLINE + MRL_AI_SYSTEM 的 ACTIVE_MAINLINE）
- archive_candidates：34 → **39**；unmerged_assets：71 → **128**
- `08_NeuralGraph_Engine/MRL_Branch_NeuralGraph.{json,graphml}`：401 nodes/895 edges → **1,027 nodes / 1,835 edges**
- `05_Mainline_Subline_Resolver/MRL_Mainline_Subline_Map.html` 標題與 chip 全重算

## 角色重分佈
| Role | 原（230 條） | 新（530 條） |
|---|---|---|
| ROOT_MAINLINE | 0 | **28**（新 repo 的 `main` branch） |
| ACTIVE_MAINLINE | 1 | 2 |
| SUB_MAINLINE | 2 | 2 |
| MIRROR_BRANCH | 154 | **368** |
| RECOVERY_BRANCH | 32 | 32 |
| ARCHIVE_BRANCH | 4 | 4 |
| FEATURE_BRANCH | 1 | 5 |
| UNKNOWN_BRANCH | 36 | 89 |

## 三個「原本卡住」項目的真實結論

### ✅ P2b all-branch sweep — 完成
不需要外部授權，純本地 git compute。

### ⚠️ P0 ~650 老 repo — 工具物理限制
`list_repos` 硬性 500 筆最近 pushed，過去 `pushed_at` ≥ 2026-02-28；更舊的看不到。
- 掃本 repo 內容找 owner/repo 引用：只找到 3 個候選（都是 API doc 的假陽性 `dofaromg/repos` 等）
- 真的要補完必須：（a）建構者直接點名老 repo，或（b）另一個授權路徑能列出 user/org 級 repo 列表
- **結論：這條本次工具組無法突破。**

### ⚠️ P1 剩 462 repo — 需逐個 `add_repo` 批准
- 本次已完成 fork==false 的 37/42（**非 fork 全部覆蓋到位，Mrliou 2 個公開 fork 與 3 個命名衝突 repo 除外**）
- 剩下 **457 個 fork repo** 大多是外部專案（例如 `fastapi`, `ClickHouse`, `botpress` 等的 fork），**對 MRL 治理圖的語意貢獻低**
- 若要跨 repo HEAD-sha 鏡像偵測，建議只 attach **MRL-named forks（約 100 個）**；剩餘 ~357 個外部 fork 可選擇性

## 檔位（新增 / 更新）
- `MRL_Global_Repository_Asset_Governance/02_Branch_Registry/{branches_raw.jsonl,branch_registry.json,branch_counts.json}` 擴充
- `MRL_Global_Repository_Asset_Governance/03_Asset_Registry/{asset_branch_matrix,asset_registry,unique_to_branch,only_in_default}.json`+README
- `MRL_Global_Repository_Asset_Governance/03_dedupe/head_sha_duplicates.json` 重算
- `MRL_Global_Repository_Asset_Governance/05_Mainline_Subline_Resolver/{mainline_registry,branch_role_map,archive_candidate_report,unmerged_asset_report}.json` + `MRL_Mainline_Subline_Map.html`
- `MRL_Global_Repository_Asset_Governance/08_NeuralGraph_Engine/MRL_Branch_NeuralGraph.{json,graphml}` 重算
- `_lib/build_map_html.py` 支援多 repo 標題

## 未宣稱
- P2b 僅對 **dofaromg/MRL_AI_SYSTEM** 的 230 分支做 asset sweep；其他 30 repo 的 asset 需各別 clone 或 gh api contents 才能擴充（P2b-ext）
- P1b lineage（merge_base / ahead / behind / unique_commits）只對 MRL_AI_SYSTEM 的 230 分支做本地 git compute；新 300 分支的 lineage 要 gh api compare（300 call，可做）或 clone 各 repo
