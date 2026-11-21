---
origin_signature: MrLiouWord
title: MRL GitHub Integration Anchor 01
instituted: 2026-11-21
direction_author: user (「GitHub 也要整合在一起」)
content_author: AI (Claude Opus 4.7)
承接: MRL__Partner_Tool_Boundary_Correction_02.md · MRL__Three_Mothers_Axiom.md
mode: additive
---

# MRL GitHub Integration Anchor 01

## 一、GitHub 在母體架構中的位階

### user memory 已錨的空間事實(verbatim 不壓)
- top-level owner: `dofaromg`(HF / GitHub-style namespace · 空間 owner)
- 第二 GitHub owner: `Mrliou`(org)
- 總 ~1,150 repos(forks 包含)
- user 稱「GitHub 平行世界空間」· 「全球/全部 GitHub」在 user 口中 = 這個空間 · 不是其他人的 repo
- 主倉:`dofaromg/MRL_AI_SYSTEM` = 母體 canonical(user memory 錨)· 247 branches(本場 git ls-remote 實測)
- APFS 分支 = external Adapter / deployment branch under dofaromg(user memory 錨)

### 位階定位

GitHub 是 **第 4 母體** · 承 user 「三個以上母體」(見 `MRL__Three_Mothers_Axiom.md`):

| # | 母體 | 性質 |
|---|---|---|
| 1 | DL580 母體 | 實體 · HP DL580 G9(user 2026-10 memory 錨)|
| 2 | Cloudflare 雲母體 | ~187 workers / KV / D1 / R2 |
| 3 | Dropbox 雲母體 | 本體封存(`/MRL_Mother_Anatomy/`)|
| **4** | **GitHub 平行世界空間** | **dofaromg + Mrliou · ~1,150 repos · 本檔新接** |

**MRL 本體仍在 L1 模具層** · GitHub 作為載體(L2)之一 · 不下沉 L1 · 不與 L2 其他 AI 平台(Microsoft/Anthropic/OpenAI 等)並列。GitHub 是 user 的「平行世界空間」· 位階屬 L2 · 但 user 是這個空間的 owner · 不是 GitHub 公司的 tenant。

## 二、已確認核心 MRL repos(從 list_repos 200 筆篩)

### A 類 · MRL 本體線(dofaromg)

| repo | pushed | visibility | 性質 |
|---|---|---|---|
| `dofaromg/MRL_AI_SYSTEM` | 2026-11-08 | public | 母體 canonical · 247 branches |
| `dofaromg/mrliouword-system` | **2026-11-21** | public | 今天 push |
| `dofaromg/MRL_ASI_system` | 2026-11-02 | public | ASI system 線 |
| `dofaromg/mrliouword-root` | 2026-10-23 | public | root 線(workers code 來源之一)|
| `dofaromg/mrlioudb` | 2026-11-01 | public | DB 線 |
| `dofaromg/MRL_ts-rust` | 2026-10-22 | public(fork) | TS-Rust bridge |
| `dofaromg/Mrl_sqlite` | 2026-10-21 | public(fork) | SQLite |
| `dofaromg/MRL_mcp-server-cloudflare` | 2026-10-22 | public(fork) | MCP CF integration |
| `dofaromg/MrliouAI-box` | 2026-11-02 | **private** | AI box 線 |
| `dofaromg/Mrl_w01234567` | 2026-11-02 | **private** | w-system |
| `dofaromg/Mrl_ai-Assist` | 2026-11-02 | **private** | AI Assist |
| `dofaromg/flow-tasks` | 2026-11-18 | public | flow-tasks 主線 |
| `dofaromg/flow-tasks-01` | 2026-11-02 | **private** | flow-tasks 01 |
| `dofaromg/APFS` | 2026-07-06 | **private** | **user memory 錨:APFS 分支 = external Adapter / deployment** |
| `dofaromg/Mrliouhan` | 2026-08-11 | public(fork) | Mrliouhan 分支(本場 11-15 Modules/App_Mrliouhan_Build/ 的對應 GitHub)|
| `dofaromg/mrl-family-ai-platform` | 2026-08-04 | **private** | family platform |
| `dofaromg/mrl-ai-chatbot` | 2026-08-04 | **private** | chatbot |
| `dofaromg/Mrliou_AIworld` | 2026-08-06 | public | AI world |
| `dofaromg/MrlNexus` | 2026-07-17 | public(fork) | Nexus |
| `dofaromg/mrlcore` | 2026-07-18 | public(fork) | core |

### B 類 · MRL 本體線(Mrliou org)

| repo | pushed | visibility | 性質 |
|---|---|---|---|
| `Mrliou/mrliouword-system` | 2026-11-16 | public(fork) | mirror |
| `Mrliou/.MRL_AI_SYSTEM` | 2026-10-04 | public(fork) | mirror of main |
| `Mrliou/MRL-Autonomous-Evolution-Stack-AES-` | 2026-10-05 | internal | AES 線 |
| `Mrliou/Mrl_Mother` | 2026-09-19 | **private** | **Mother 線 private** |
| `Mrliou/MRL_AI_world` | 2026-09-23 | internal | AI world org 側 |
| `Mrliou/mrliouairules` | 2026-08-19 | public(fork) | rules 鏡像 |
| `Mrliou/flow-tasks` | 2026-09-19 | **private** | flow-tasks org private |
| `Mrliou/Dropbox` | 2026-08-18 | **private** | **Mrliou 側 Dropbox 鏡像倉** |
| `Mrliou/Mrliouai-mcp` | 2026-07-15 | public(fork) | MCP mirror |
| `Mrliou/MRL.t3code` | 2026-10-22 | public(fork) | T3 code |
| `Mrliou/open-remote-ssh` | 2026-07-16 | public(fork) | SSH |
| `Mrliou/Mrlopencode` | 2026-07-13 | public(fork) | opencode |

### C 類 · 向下吸收 L2 generic(forks)

200 筆中約 60+ 是 fork 自上游 · 承 user preference「向 L2 generic 下吸收好的邏輯/技術」:
- AI/ML: `anthropic-sdk-csharp` · `azure-docs-sdk-node` · `MRL-antigravity-sdk-python` · `megatron-bridge` · `Megatron-LM`
- 基礎設施: `clickhouse` · `botpress` · `seaweedfs` · `ClickHouse` · `nextjs` · `bazel` · `gradle`
- 工具: `eslint` · `rolldown` · `detect-package-manager` · `rtl_433`
- Claude 相關: `claude-cookbooks`(dofaromg + Mrliou 兩份)· `claude-code` · `claude-agents-skill` · `MRL-context-kit`

這些 fork 是 user「平行世界空間」的 cells(user 戒律:不刪檔案 · fork 是 cell / 粒子入口)。

### D 類 · 未列(list_repos 分頁限制)

list_repos 回 200 · `has_more: true`。user 原話 ~1,150 repos · 代表還有 **~950 未列**。需特定 repo 時用 `add_repo owner/name` 直掛。

## 三、GitHub 接進 108 粒子的接線點

### 接線 1 · GitHub ↔ Dropbox 雲母體
- 當前:Dropbox `/MRL_Mother_Anatomy/Modules/` 230+ 檔 vs GitHub `MRL_AI_SYSTEM` 247 branches · **兩邊未自動對流**
- 可做:`_Mother_Runtime/github_bindings_map.md` 通路 1 說明

### 接線 2 · GitHub ↔ Cloudflare Workers
- 當前:CF Workers deploy 主要透過 wrangler(本地)
- 可做:GitHub Actions `.github/workflows/deploy-workers.yml` + CF Pages/Workers Git integration

### 接線 3 · GitHub ↔ DL580 母體
- 當前:DL580 本地檔案 · 無自動 git sync
- 既有:`MRL_Branch_DL580_Workflow_PIDScope_v1` / `MRL_Branch_DL580_PIDScope_Layer_v1` 兩條 branch 已在 MRL_AI_SYSTEM
- 可做:DL580 cron `git pull` 到 `D:\mrl\github\{repo}\`

### 接線 4 · GitHub branches as 工作線
- `MRL_AI_SYSTEM` 247 branches · 每條是獨立工作線 · **不合併**(user 戒律不刪檔案)
- 關鍵 branches(本場 git ls-remote 讀到前 30):
  - `MRL_AI_SYSTEM/memory-system-rules-prep`
  - `MRL_AI_SYSTEM/multi-domain-sync-core-v1`
  - `MRL_Branch_MotherConvergence_Package_v1`
  - `MRL_Branch_MotherMatrix_Integration_Stack_v1`
  - `MRL_Branch_MotherSource_ZhiZhang_FlowAgent_Lineage_v1`
  - `MRL_Branch_RuntimeParticle_Compression_v4`
  - `MRL_Branch_Runtime_Convergence_API_v1`
  - `MRL_Branch_StructureField_Rename_Alignment_v1`
  - `MRL_absorb_reference_adapter_materials_v1`
  - `MRL_add_ai_computer_runtime`

## 四、本場未做 · 給 user 選

1. **掛 `MRL_AI_SYSTEM` 做 push access** — `add_repo owner:"dofaromg" repo:"MRL_AI_SYSTEM" access:"push"` → 本場 8 補完檔可推到新 branch
2. **寫 `.github/workflows/deploy-workers.yml`** → auto deploy workers
3. **列全部 ~1,150 repos** — list_repos 需另法迭代
4. **讀 `Mrliou/Mrl_Mother` private** — 要 `add_repo` 或 user 開權限
5. **GitHub ↔ Dropbox 雙向同步腳本** — 在 `_Mother_Runtime/` 寫 `github_sync.sh`

---

## 戒律驗證

- origin_signature: MrLiouWord ✓
- MRL 位階 L1 不下沉 ✓(GitHub 定為 L2 載體 · 但 user 是這空間 owner)
- 不壓縮 user 空間 ✓(1,150 repos 全保 · 本檔只列核心 MRL 線 · 其他全保)
- append-only ✓
- 承 user 原話 verbatim 引用 ✓(「平行世界空間」· 「三個以上母體」· 「位置隨邊界移動」)
- 不替 user 立新 label ✓(「第 4 母體」承 user「三個以上母體」· 非新造)
- 不刪 fork ✓(C 類承認 forks 是 cells)

**封存**: Claude 執行 · 方向來自 user(「GitHub 也要整合在一起」)
**origin_signature**: MrLiouWord
