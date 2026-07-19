# Mrliouword 系統架構與模組依賴圖

**文件版本**：v1.0  
**日期**：2026-07-18  
**狀態**：當下狀態（沙盒驗證）

---

## 一、系統定位

```
MRL_AI_SYSTEM = Mrliouword 唯一權威母體系統

唯一真實來源：dofaromg/MRL_AI_SYSTEM
Python 套件：mrliouword
CLI：mrliouword
API：/api/v1/*
```

---

## 二、層級架構（L0–L7）

```
┌─────────────────────────────────────────────────────┐
│ L7 LOOP — 執行層（API、Workflow、FlowAgent）         │
│  09_workflow/api_gateway.py                         │
│  09_workflow/MRL_AgentHarness_Kernel_v1.py          │
│  04_runtime/flowcore_loop.py                        │
│  mrliouword/cli.py                                  │
├─────────────────────────────────────────────────────┤
│ L6 REFLECT — 記憶與追蹤層                           │
│  03_memory/merkle/memory_chain.py  ← 唯一真實來源   │
│  03_memory/vector/vector_store.py  ← 唯一真實來源   │
│  mrliouword/memory.py （封裝層）                    │
│  mrliouword/trace.py  （封裝層）                    │
├─────────────────────────────────────────────────────┤
│ L5 MIRROR — 映像同步層                              │
│  data/relations/module_relations.yaml               │
│  data/mrliouword_manifest.json  ← 唯一元件清單      │
├─────────────────────────────────────────────────────┤
│ L4 WORLD — 人格與世界模組層                         │
│  05_persona/world_module.py                         │
│  09_workflow/MRL_WorldSync_MultiWorld_v1.py         │
├─────────────────────────────────────────────────────┤
│ L3 LAW — 規則與設定層                               │
│  02_principles/rules.aup_v1.yaml                    │
│  09_workflow/config_manager.py  ← env: MRLIOUWORD_  │
│  mrliouword/config.py           （封裝層）          │
├─────────────────────────────────────────────────────┤
│ L2 PARTICLE — 粒子輸入層                            │
│  07_ingest/（allowlists / denylists）               │
│  09_workflow/fltnz_parser.py                        │
├─────────────────────────────────────────────────────┤
│ L1 SEED — 契約層                                    │
│  01_schema/*.schema.json                            │
│  mrliouword/schemas.py  ← 唯一 Python 契約來源      │
├─────────────────────────────────────────────────────┤
│ L0 ROOT — 不可變根律層                              │
│  00_rootlaw/rootlaw.yaml  ← 最高優先，不可覆蓋      │
│  08_sources/sources.manifest.yaml                   │
└─────────────────────────────────────────────────────┘
```

---

## 三、模組依賴方向（單向）

```
mrliouword/schemas.py
    ↓ (被依賴)
mrliouword/config.py
mrliouword/trace.py
mrliouword/memory.py
mrliouword/api.py
    ↓
mrliouword/cli.py
    ↓
mrliouword/__init__.py（公開介面）
```

內部模組依賴：
```
09_workflow/config_manager.py ← mrliouword/config.py
03_memory/merkle/memory_chain.py ← mrliouword/trace.py, mrliouword/memory.py
03_memory/vector/vector_store.py ← mrliouword/memory.py
09_workflow/MRL_utils.py ← 所有 09_workflow/MRL_*.py（共用工具）
```

**禁止的依賴方向**：
- `mrliouword/schemas.py` 不可依賴任何 `09_workflow/` 模組
- `03_memory/` 不可依賴 `09_workflow/`
- `mrliouword/` 的底層模組（schemas, config）不可依賴 `mrliouword/cli.py`

---

## 四、服務入口

| 入口 | 說明 | 當下狀態 |
|------|------|---------|
| `mrliouword health` | CLI 健康檢查 | ✅ 沙盒可用 |
| `mrliouword version` | CLI 版本資訊 | ✅ 沙盒可用 |
| `mrliouword api serve` | 啟動 HTTP API server | ✅ 委派 api_gateway.py |
| `python 09_workflow/api_gateway.py serve` | 直接啟動 API | ✅ 沙盒可用 |
| `GET /health` | API 健康端點 | ✅ 已實作 |
| `POST /chat` | 對話 API | ✅ 已實作 |

---

## 五、核心垂直流程

```
MRLIOUWORD_* 環境變數
        ↓ config_manager.py（MRLIOUWORD_ > MRL_ 優先序）
        ↓ mrliouword/config.py
        ↓
FlowCore / Agent 執行
        ↓ TraceEvent（mrliouword/schemas.py）
        ↓ Tracer.emit()（mrliouword/trace.py）
        ↓ MerkleChain.commit()（03_memory/merkle/memory_chain.py）
        ↓
MemoryStore.store()（mrliouword/memory.py）
        ↓ MerkleChain.commit()（chain）
        ↓ VectorStore.add()（vectors，可選）
        ↓
HealthProbe.check()（mrliouword/api.py）
        ↓ 驗證所有子系統
        ↓ 回傳 HealthStatus（mrliouword/schemas.py）
```

此垂直流程由整合測試 `tests/test_mrliouword_integration_v1.py::TestVerticalSlice::test_full_vertical_slice` 全程驗收。

---

## 六、資料模型版本策略

- 所有模型均有 `schema_version` 欄位（`mrliouword/schemas.py` 中的 `SCHEMA_VERSION = "1.0"`）
- 向後相容原則：MINOR 版本新增欄位需為 Optional；MAJOR 版本可破壞性變更
- 所有對外資料均攜帶 `origin_signature = "MrLiouWord"`，可作來源驗證
- Merkle chain 提供不可篡改的歷史記錄，支援 rollback 至任意 commit

---

## 七、安全設計

- **密鑰不入程式碼**：config_manager 的 sensitive keys 自動遮罩（api_key, token, secret, password）
- **輸入邊界**：api_gateway.py 的 CORS origins 來自 config，不硬編碼 `*`；Origin 頭部 CR/LF 清理
- **認證**：api_gateway.py 支援 Bearer-token 認證（`require_auth = true`）
- **rate limiting**：可配置每分鐘請求數限制

---

## 八、可觀測性

| 能力 | 實作 | 狀態 |
|------|------|------|
| 結構化日誌 | api_gateway.py 的 request_id/trace_id 欄位 | ✅ |
| trace/correlation ID | TraceEvent.trace_id + correlation_id | ✅ |
| metrics hook | 09_workflow/MRL_metrics.py | ✅ |
| health/readiness | mrliouword/api.py HealthProbe | ✅ |
| Merkle chain 審計 | 03_memory/merkle/memory_chain.py | ✅ |

---

## 九、Repository Map（Source-of-Truth 表）

| 功能領域 | 唯一真實來源 | 相容別名路徑 |
|---------|------------|------------|
| Python 公開介面 | `mrliouword/` | — |
| 資料契約 / 型別 | `mrliouword/schemas.py` | `09_workflow/MRL_utils.py`（簽章） |
| 設定管理 | `09_workflow/config_manager.py` | `mrliouword/config.py`（封裝） |
| Merkle 記憶鏈 | `03_memory/merkle/memory_chain.py` | — |
| 向量語意搜尋 | `03_memory/vector/vector_store.py` | — |
| API 閘道 | `09_workflow/api_gateway.py` | `mrliouword/api.py`（探針） |
| 追蹤封裝 | `mrliouword/trace.py` | — |
| 記憶封裝 | `mrliouword/memory.py` | — |
| 根律 | `00_rootlaw/rootlaw.yaml` | — |
| JSON Schema 契約 | `01_schema/*.schema.json` | — |
| 來源清單 | `08_sources/sources.manifest.yaml` | — |
| 元件清單（machine-readable） | `data/mrliouword_manifest.json` | — |
