# Mrliouword 外部材料盤點、去重蒸餾決策紀錄

**文件版本**：v1.0  
**日期**：2026-07-18  
**狀態**：當下狀態（沙盒分析）

---

## 一、盤點範圍

依問題描述，盤點下列 8 個同 owner 儲存庫：

| # | 儲存庫 | 存取狀態 | 備註 |
|---|--------|----------|------|
| 1 | `dofaromg/flow-tasks` | ❌ 404 Not Found | 無法存取，記錄為待處理 |
| 2 | `dofaromg/mrliouword-system` | ✅ 可讀 | 已分析 |
| 3 | `dofaromg/fastapi` | ❌ 404 Not Found | 無法存取，記錄為待處理 |
| 4 | `dofaromg/flow-tasks-01` | ❌ 未測試 | 可能與 flow-tasks 同狀況 |
| 5 | `dofaromg/Mrliou_L1_Gate_ParticleRuntime` | ❌ 404 Not Found | 無法存取，記錄為待處理 |
| 6 | `dofaromg/FirebaseUI-iOS` | ❌ 未測試 | 與母體核心無直接程式碼相依 |
| 7 | `dofaromg/growthbook-flags-sdk-example` | ❌ 未測試 | 外部技術驗證，非核心 |
| 8 | `dofaromg/tool-silk-` | ❌ 未測試 | 練習用途，非核心 |

---

## 二、已存取材料分析

### 2.1 `dofaromg/mrliouword-system`

**可讀狀態**：✅ 已成功讀取 README.md 及目錄結構

**架構洞見**：

| 面向 | 內容 | 吸收決策 |
|------|------|----------|
| 八層架構（L0–L7 + L∞） | 基於 Schumann × 黃金比例的頻率公式 `f(n) = 7.83 × φ^(n-1)` | **設計洞見**：已在 `MRL_AI_SYSTEM` 的 L0–L7 層級系統中體現；頻率數值為概念性，非計算基礎 |
| atom_t（40 bytes C 結構） | 原子粒子層底層結構 | **隔離決策**：C 結構屬低層記憶體佈局，不直接搬移；在 Python 層以 dict schema 等價抽象 |
| simhash64 | 語意指紋工具 | **待吸收**：可補充 `mrliouword.schemas` 的語意識別能力，需進一步評估 |
| Merkle Chain（merkle.py） | 與本系統 `03_memory/merkle/memory_chain.py` 功能等價 | **去重決策**：以 `MRL_AI_SYSTEM/03_memory/merkle/memory_chain.py` 為唯一真實來源；外部版本棄用 |
| 52 個粒子定義（particle_dict.json） | 粒子語言詞彙表 | **待盤點**：若定義未在本系統中登錄，可作為 `01_schema/` 補充材料 |
| Cloudflare Workers 服務 | mrliouword-private（記憶/人格/吸收/掃描）、particle-auth-gateway | **隔離決策**：Cloudflare 部署為邊緣端點，非 Python 核心；服務名稱符合 `mrliouword-*` 命名規範，保持 |
| D1 資料庫（mrliouword-db）、KV、R2 | 雲端儲存後端 | **隔離決策**：屬 Cloudflare 基礎設施層；Python 核心不直接依賴 CF-specific API |
| 核心簽名（origin_signature: "MrLiouWord"） | 與本系統 `ORIGIN_SIGNATURE = "MrLiouWord"` 完全一致 | **已整合**：位元相容，無需變更 |
| wake_keys / philosophy / constraints | 身分認同與哲學原則 | **已整合**：精神已體現於 `00_rootlaw/rootlaw.yaml` 及 `02_principles/` |

**蒸餾結論**：  
`mrliouword-system` 與 `MRL_AI_SYSTEM` 的核心資料結構（Merkle chain、origin_signature）已高度重疊。  
主要差異在於部署平台（Cloudflare Workers vs. Python stdlib HTTP server）。  
已蒸餾保留：命名規範、服務架構洞見、粒子定義方向。  
未直接搬移：C 結構、Cloudflare Worker 程式碼（授權狀態待確認）。

---

## 三、無法存取來源處理

### 3.1 `dofaromg/flow-tasks`（404）

**已知設計知識**（來自先前分析）：

| 知識點 | 來源 | 吸收決策 |
|--------|------|----------|
| STRUCTURE → MARK → FLOW → RECURSE → STORE 執行鏈 | 分析報告 | **設計洞見**：已在 `04_runtime/flowcore_loop.py` 中體現同等概念 |
| Particle Language Core | 分析報告 | **去重決策**：語言核心以本系統為唯一真實來源 |
| GKE/Kubernetes/Argo CD 部署 | 分析報告 | **待處理**：部署腳本可補充至 `deploy/` 目錄；需存取原始 YAML 才能安全吸收 |
| MongoDB 部署配置 | 分析報告（截斷） | **待處理**：無法讀取完整 StatefulSet 配置，暫不吸收 |

**待處理項目**：  
`P1-EXT-001`：待 `flow-tasks` 存取恢復後，吸收 Argo CD / Kubernetes 部署腳本  
`P1-EXT-002`：確認 MongoDB 配置完整性

### 3.2 `dofaromg/fastapi`（404）

**待處理項目**：  
`P2-EXT-003`：待存取恢復後，確認是否為 Mrliouword API Service 前身；若是，評估遷移至 `09_workflow/api_gateway.py` 的路徑

### 3.3 `dofaromg/Mrliou_L1_Gate_ParticleRuntime`（404）

**已知資訊**：v1.2.2、HTML + TypeScript 入口層

**待處理項目**：  
`P2-EXT-004`：待存取恢復後，確認 L1 Gate 入口職責範圍；評估是否整合至 `ui/` 或獨立為 `mrliouword-l1gate` 服務

---

## 四、去重決策表

| 資料結構 / 功能 | 外部來源 | 本系統現況 | 決策 | 唯一真實來源 |
|----------------|---------|----------|------|-------------|
| Merkle Chain 實作 | mrliouword-system/core/merkle.py | 03_memory/merkle/memory_chain.py | **去重** | `MRL_AI_SYSTEM/03_memory/merkle/memory_chain.py` |
| origin_signature 簽章機制 | mrliouword-system | 09_workflow/MRL_utils.py, mrliouword/schemas.py | **已整合** | `mrliouword/schemas.py`（新）+ `MRL_utils.py`（內部） |
| 粒子資料模型 | mrliouword-system/core/particle_dict.json | 01_schema/*.schema.json | **待補充** | `MRL_AI_SYSTEM/01_schema/`（擴充粒子定義） |
| API 服務入口 | flow-tasks（未存取） | 09_workflow/api_gateway.py | **本系統為準** | `MRL_AI_SYSTEM/09_workflow/api_gateway.py` |
| FlowAgent 執行鏈 | flow-tasks（未存取） | 04_runtime/flowcore_loop.py | **本系統為準** | `MRL_AI_SYSTEM/04_runtime/flowcore_loop.py` |
| 向量語意搜尋 | mrliouword-system（未詳） | 03_memory/vector/vector_store.py | **本系統為準** | `MRL_AI_SYSTEM/03_memory/vector/vector_store.py` |

---

## 五、後續優先清單

| 優先級 | ID | 項目 | 阻塞條件 |
|--------|-----|------|---------|
| P0 | EXT-000 | 確認 mrliouword-system 授權條款與程式碼所有權 | 無 |
| P1 | EXT-001 | 吸收 flow-tasks 的 Argo CD / K8s 部署腳本 | 需 repo 存取 |
| P1 | EXT-002 | 補充 01_schema/ 中的 52 粒子定義（來自 mrliouword-system） | 需確認定義完整性 |
| P2 | EXT-003 | 評估 fastapi repo 是否為 Mrliouword API Service 前身 | 需 repo 存取 |
| P2 | EXT-004 | 確認 L1 Gate 職責，評估入口層整合方案 | 需 repo 存取 |
| P3 | EXT-005 | 評估 FirebaseUI-iOS 作為 Mrliouword iOS Client | 需 repo 存取 + 授權確認 |
| P3 | EXT-006 | 評估 GrowthBook flags 整合方案（feature flag adapter） | 需業務需求確認 |

---

## 六、吸收原則聲明

本次吸收工作嚴格遵守以下規則：

1. **不盲目複製**：僅蒸餾設計洞見與契約，不搬移整個外部專案
2. **不搬移受限程式碼**：對授權不明材料，只記錄設計洞見
3. **位元相容**：已驗證 origin_signature 簽章機制位元相容（見 `tests/test_mrliouword_integration_v1.py::TestSchemas::test_embed_signature_compat_with_mrl_utils`）
4. **唯一真實來源**：每項功能已指定唯一真實來源，避免未來多版本分歧
5. **誠實標記**：無法存取的來源明確標記為「待處理」，不虛構其內容
