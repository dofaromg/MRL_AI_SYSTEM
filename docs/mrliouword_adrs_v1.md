# Mrliouword 架構決策紀錄（ADR）

**文件版本**：v1.0  
**日期**：2026-07-18  

---

## ADR-001：權威產品正名定為 Mrliouword

**狀態**：已接受  
**日期**：2026-07-18

### 決策

將本系統的唯一權威產品正名定為 **Mrliouword**。

Python 套件命名空間：`mrliouword`  
CLI：`mrliouword`  
環境變數前綴：`MRLIOUWORD_`

### 背景

系統在歷史演進中出現了多個命名：`MRL`、`FlowAgent`、`ParticleRuntime`、`MrLiouWord`、`Mrliouword`。  
各儲存庫使用不同名稱，造成整合困難、文件不一致，且難以建立清晰的版本治理。

### 理由

- `Mrliouword` 已在 `mrliouword-system`、Cloudflare Workers 服務名稱（`mrliouword-private`）、域名（`mrliouword.com`）中廣泛使用
- 大小寫形式（`Mrliouword`）兼顧可讀性與品牌一致性
- 舊名稱（`MRL`、`FlowAgent`）繼續作為子系統標籤，不破壞現有程式碼

### 結果

- 建立 `mrliouword/` Python 套件作為公開介面
- `MRLIOUWORD_` 環境變數前綴優先，`MRL_` 保留向後相容
- `origin_signature = "MrLiouWord"` 維持不變（歷史格式，位元相容）

---

## ADR-002：母體邊界定義

**狀態**：已接受  
**日期**：2026-07-18

### 決策

`dofaromg/MRL_AI_SYSTEM` 是 Mrliouword 系統的**唯一權威母體**。  
其他儲存庫為部署、入口、實驗或舊版本，不得各自維護獨立的核心實作。

### 模組邊界（單向依賴）

```
mrliouword/schemas  →（被所有層依賴）
mrliouword/config   →（依賴 schemas + config_manager）
mrliouword/trace    →（依賴 schemas + memory_chain）
mrliouword/memory   →（依賴 schemas + chain + vector）
mrliouword/api      →（依賴 schemas + config + memory_chain + vector）
mrliouword/cli      →（依賴所有上層）
```

### 理由

- 防止各儲存庫各自實作重複的 Merkle chain、schema、API，造成維護地獄
- 單向依賴可靠保固模組邊界，避免循環依賴
- `mrliouword/schemas.py` 的零外部依賴設計保證最大可移植性

---

## ADR-003：外部材料吸收策略

**狀態**：已接受  
**日期**：2026-07-18

### 決策

吸收外部材料時，採用「蒸餾設計洞見」策略，**不**盲目複製整個外部專案。

### 規則

1. 先建立 inventory（見 `docs/mrliouword_external_inventory_v1.md`）
2. 功能等價的實作，以本系統版本為唯一真實來源
3. 只有明確授權（MIT/Apache/owner 確認）的程式碼才可直接搬移
4. 無法存取的來源標記為「待處理」，不虛構內容

### 已執行

- `mrliouword-system` 的 Merkle chain 概念：已去重，以本系統 `03_memory/merkle/memory_chain.py` 為準
- `mrliouword-system` 的 origin_signature：位元相容，無需重複實作
- 無法存取的 4 個儲存庫：誠實記錄為待處理

---

## ADR-004：config_manager.py 的 MRLIOUWORD_ 前綴支援

**狀態**：已接受  
**日期**：2026-07-18

### 決策

在 `09_workflow/config_manager.py` 中新增 `MRLIOUWORD_` 環境變數前綴支援，優先序高於原有 `MRL_` 前綴。

### 改動

```python
# Before (MRL_ only)
env_key = "MRL_" + key.upper().replace(".", "_")
env_val = os.environ.get(env_key)

# After (MRLIOUWORD_ > MRL_)
env_suffix = key.upper().replace(".", "_")
env_val = (
    os.environ.get("MRLIOUWORD_" + env_suffix)
    or os.environ.get("MRL_" + env_suffix)
)
```

### 理由

- 不破壞任何現有測試（MRL_ 仍可用）
- 新部署可使用 Mrliouword 正名前綴
- 過渡期兩種前綴均可使用，無需強制遷移

### 驗收

整合測試 `TestConfig::test_mrliouword_prefix_beats_mrl` 驗證 MRLIOUWORD_ 確實優先於 MRL_。

---

## ADR-005：mrliouword/ 套件設計原則

**狀態**：已接受  
**日期**：2026-07-18

### 決策

`mrliouword/` 套件採用「封裝層」設計，不重複實作底層邏輯。

### 原則

1. `schemas.py` — 零外部依賴（純 Python stdlib）
2. `config.py` — 封裝 `09_workflow/config_manager.py`，不重新實作設定邏輯
3. `trace.py` — 封裝 `03_memory/merkle/memory_chain.py`，不重新實作 Merkle 邏輯
4. `memory.py` — 封裝 chain + vector，統一記憶存取介面
5. `api.py` — 提供 in-process health probe，不啟動 HTTP server
6. `cli.py` — 委派底層模組，不重新實作業務邏輯

### 理由

- 避免重複實作，符合 Additive-Only 原則
- 封裝層可被獨立測試，不依賴服務啟動
- 底層模組可獨立迭代，不影響公開介面

---

## ADR-006：整合測試設計

**狀態**：已接受  
**日期**：2026-07-18

### 決策

建立 `tests/test_mrliouword_integration_v1.py` 作為核心垂直流程的可執行驗收測試。

### 覆蓋範圍

```
TestSchemas (8 tests)    — 資料模型、簽章往返、跨模組相容性
TestConfig (5 tests)     — 設定載入、MRLIOUWORD_ 前綴、向後相容
TestTracer (5 tests)     — 追蹤事件發送、Merkle 驗證、相關 ID
TestMemoryStore (6 tests) — 儲存/恢復/驗證/搜尋
TestHealthProbe (4 tests) — 健康檢查、子系統狀態
TestCLI (5 tests)         — CLI 命令驗收
TestVerticalSlice (3 tests) — config→trace→memory→health 完整路徑
```

**總計：36 個整合測試，沙盒全數通過（2026-07-18）**

### 原則

- 所有測試使用 `tmp_path` fixture，不寫入生產資料目錄
- 不依賴外部服務（Ollama、真實 LLM、DL580）
- 標記沙盒驗收，不宣稱已實機上線
