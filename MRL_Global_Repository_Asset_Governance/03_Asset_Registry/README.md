# 03_Asset_Registry — P2b 全分支資產掃描結果

- 產出時間 (UTC)：2026-10-04T11:20:24Z
- 掃描分支數：230（含 default `MRL_AI_SYSTEM/memory-system-rules-prep`）
- 錯誤分支數：0
- 唯一 (blob_sha, canonical_path) 組合：**4,829**
- 唯一 canonical_path：4,442
- 唯一 blob_sha：2,664
- 跨分支共享 (branch_count ≥ 2)：4,635
- 單一非 default 分支獨有：194
- 僅 default 分支獨有：0

## 方法

對 `02_Branch_Registry/branch_registry.json` 中 230 條分支，各執行一次：

```bash
git -c core.quotePath=false ls-tree -r --long refs/remotes/origin/<branch_name>
```

`-c core.quotePath=false` 強制保留 CJK 原字（本 repo 內 42% 檔名為中文），否則同一檔會被 git 轉成 `\xxx` 八進位序列算成不同 entry。

ThreadPoolExecutor 20 條平行；每 20 分支回報一次 stderr。單筆失敗記下 `errors[branch]=reason` 繼續，不中斷。

記憶體內只建一個 dict `{(blob_sha, canonical_path): set(branch_name)}`；完成後依此派生出 4 份 JSON。

## 產出檔

| 檔名 | 條件 | 用途 |
| --- | --- | --- |
| `asset_branch_matrix.json` | `branch_count ≥ 2` | 跨分支共享資產的分佈矩陣（P2b 主產出） |
| `asset_registry.json` | default branch 全檔 | P2a 擴充 `branches_present` 為實際清單並補 `branch_present_count` |
| `unique_to_branch.json` | `branch_count == 1` 且非 default | 哪些檔只住在單一非 default 分支（P1b 的 unique_files 具體內容） |
| `only_in_default.json` | `branch_count == 1` 且是 default | default 專屬資產（可能需要分支吸收 / 母體待抽離） |

## Top 5 跨分支分佈（最常見資產）

- `01_schema/README.md` (ee2f976dd0…) → **230** 條分支
- `01_schema/action_request.schema.json` (c2fe6abb0b…) → **230** 條分支
- `01_schema/decision.schema.json` (dd3edde416…) → **230** 條分支
- `01_schema/runtime_trace.schema.json` (f7f6a2e9ae…) → **230** 條分支
- `01_schema/trace_record.schema.json` (9ae1160007…) → **230** 條分支

## Top 5 單一分支獨有檔案最多的分支

- `dl580-tunnel-recover-20261004` — 53 個獨有檔
- `claude/dl580-7700-engine-recovery-ex6mrc` — 30 個獨有檔
- `copilot/28729581812` — 17 個獨有檔
- `MrliouAI` — 13 個獨有檔
- `mrl/pr151-ios-hardening` — 12 個獨有檔

## P2c 建議

1. **跨分支熱點處理**：`asset_branch_matrix.json` top-N 的 `(blob_sha, canonical_path)` 基本上就是「所有分支都有」的框架檔（README、.gitignore、workflows 之類）；P2c lineage 可以直接以這些為「幹」錨點，分支間唯一的差異在它們上方的改動。
2. **分支私藏資料的回收路線**：`unique_to_branch.json` 的 top 分支裡藏著母體從未吸收的實驗模組 / 蒸餾材料，建議搭配 `MRL_Mother_Autonomous_Materials_v1` 蒸餾包流程逐個標「待起動」，由 Create Preflight 走 MAP_EXISTING | SUPPLEMENT_EXISTING | CREATE_NEW。
3. **default 專屬資產審計**：`only_in_default.json` total=**0** 是一個關鍵觀察 —— default (`MRL_AI_SYSTEM/memory-system-rules-prep`) 上的 3,770 個檔，每一個都至少在另一條分支上也存在。換句話說，default 並沒有「只住在 main 的獨家內容」；它收斂的所有產物都還掛在其他分支上，可用來追 lineage。P2c 可直接把 default 當成「所有合流分支的交集 ∪ 幾個 schema 幹」，不必擔心丟失孤兒檔。
4. **NeuralGraph 準備**：以 `asset_branch_matrix.json` 的 (sha, path, branches) 作為邊，搭配 `01_Repository_Inventory` 的 commit DAG，可直接餵給 `08_NeuralGraph_Engine` 建立「資產 ↔ 分支 ↔ commit」三層圖。

> 符合 CLAUDE.md 狀態回報約定：以上為「當下狀態 2026-10-04（沙盒 git 快取 refs/remotes/origin/*）」，尚未對照 DL580 母體實機 FS 做資產對位驗收；屬 **PARTIAL / 待實機對位**。
