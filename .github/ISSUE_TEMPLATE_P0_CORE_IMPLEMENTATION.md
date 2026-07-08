# [P0 Core] Implement Runtime Router + Memory Integration + Task Orchestrator

**Parent Issue:** #11 (MRL_Final_Product_Checklist_v1)
**Labels:** MRL, P0, sub-issue
**Priority:** P0 (Core Must-Have)
**Origin Signature:** MrLiouWord
**Repository:** dofaromg/MRL_AI_SYSTEM

## 目標

實作 P0-2、P0-3、P0-4 三個核心模組，將 MRL_AI_SYSTEM 從後端骨架轉變為可用產品。這些模組是最終產品的基礎，必須優先完成。

根據 issue #11 的「下一個工程動作建議」，這三個 P0 項目應該一起實作，形成完整的核心能力。

---

## P0-2 MRL_Runtime_Router

### 需求
- [ ] 將 `api_gateway.py` 的 `/chat` 端點實際接到 MRL 本地 runtime
- [ ] 支援 `LocalAdapter` 指向 DL580 本地模型或 OpenAI-compatible endpoint
- [ ] `MockAdapter` 僅允許測試模式，不可作為 production 預設
- [ ] 加入 runtime fallback：本地模型失敗時返回明確錯誤與 trace，不偽造成功

### 驗收標準
`/chat` 回應必須標明：
- `engine`: 使用的模型引擎
- `runtime_origin`: 執行來源
- `trace_id`: 追蹤 ID
- `origin_signature`: "MrLiouWord"
- `runtime_mode`: "production" / "development" / "test"

### 技術要點
- 使用 `MRL_RUNTIME_MODE` 環境變數控制 adapter 使用
- production 模式：僅允許 openai/anthropic/local adapter
- development 模式：允許所有 adapter
- test 模式：僅允許 mock/local adapter
- 所有錯誤必須有完整 trace
- 參考現有實作：`09_workflow/MRL_runtime_config.py`

### 相關檔案
- `09_workflow/api_gateway.py` - API Gateway 主檔
- `09_workflow/MRL_runtime_config.py` - Runtime 配置
- `09_workflow/llm_adapter.py` - LLM Adapter 介面
- `09_workflow/conversation_manager.py` - 對話管理器

---

## P0-3 MRL_MemoryLayer_Integration

### 需求
- [ ] `conversation_manager` 接入 `MRL_MemoryVaultPG` / `MRL_MemoryLayer`
- [ ] 每次 user / assistant / tool 事件寫入 trace
- [ ] 每個 session 建立 merkle / checksum / origin_signature
- [ ] 支援 replay：可由 session_id 還原對話與任務流程

### 驗收標準
提交一個任務後，必須可查到：
- `session` 記錄：包含 session_id, user_id, created_at
- `message` 記錄：包含 role (user/assistant/tool), content, timestamp
- `trace` 記錄：包含 trace_id, event_type, payload
- `memory` 記錄：包含 merkle_hash, checksum, origin_signature

### 技術要點
- 整合 merkle chain 進行完整性驗證
- 使用 `MerkleChain.commit()` 和 `read_all()` API
- 所有記錄必須帶 `origin_signature="MrLiouWord"`
- 支援從 session_id 完整重播對話
- 每個事件都應該被追蹤並可審計
- 參考現有實作：`09_workflow/MRL_memory_integration.py`

### 相關檔案
- `09_workflow/conversation_manager.py` - 對話管理器
- `09_workflow/MRL_memory_integration.py` - Memory 整合層
- `03_memory/merkle/memory_chain.py` - Merkle Chain 實作
- `03_memory/memory_vault_pg.py` - PostgreSQL Memory Vault

---

## P0-4 MRL_Task_Orchestrator

### 需求
- [ ] `multi_agent.py` 與 `scheduler.py` 組成正式任務引擎
- [ ] 任務狀態：`QUEUED` / `RUNNING` / `WAITING_TOOL` / `DONE` / `FAILED` / `SEALED`
- [ ] 任務結果可被 seal
- [ ] 失敗任務必須保留 `error_trace`

### 驗收標準
`/agent/run` 可執行一個多步任務並產出：
- `task_id`: 任務唯一識別 (UUID 格式)
- `status`: 任務狀態 (符合上述狀態機)
- `result`: 任務結果 (成功時)
- `error_trace`: 錯誤追蹤 (失敗時)
- `trace`: 完整執行追蹤
- `sealed_at`: seal 時間戳 (如果已 seal)

### 技術要點
- 完整的任務生命週期管理
- 狀態轉換：QUEUED → RUNNING → (WAITING_TOOL →) DONE/FAILED → SEALED
- 支援 seal 機制鎖定結果（sealed 後不可修改）
- 錯誤必須可追蹤，包含 stack trace 和 context
- 任務可以暫停、恢復、取消
- 參考現有實作：`09_workflow/MRL_task_orchestrator.py`

### 相關檔案
- `09_workflow/MRL_multi_agent.py` - Multi-Agent 系統
- `09_workflow/scheduler.py` - 任務調度器
- `09_workflow/MRL_task_orchestrator.py` - Task Orchestrator
- `09_workflow/api_gateway.py` - API Gateway (需新增 /agent/run 端點)

---

## 整合要求

完成上述三個模組後，整個系統必須能夠：

1. **接收請求** → API Gateway (`/chat`, `/agent/run`)
2. **路由執行** → Runtime Router (本地/遠端模型)
3. **記錄追蹤** → Memory Integration (完整 trace)
4. **任務管理** → Task Orchestrator (狀態管理)
5. **返回結果** → 帶有完整 metadata 的回應

### 端到端流程

```
User Request
    ↓
API Gateway (/chat or /agent/run)
    ↓
Runtime Router (檢查 MRL_RUNTIME_MODE, 選擇 adapter)
    ↓
Task Orchestrator (建立 task, 狀態: QUEUED → RUNNING)
    ↓
Multi-Agent / LLM Execution
    ↓
Memory Integration (寫入 trace, merkle commit)
    ↓
Task Orchestrator (更新狀態: DONE/FAILED)
    ↓
API Response (包含 trace_id, task_id, origin_signature)
```

---

## 測試要求

### Unit Tests
- [ ] `test_runtime_config.py` - 測試 runtime mode 控制
- [ ] `test_memory_integration.py` - 測試 memory trace 寫入
- [ ] `test_task_orchestrator.py` - 測試任務生命週期

### Integration Tests
- [ ] 測試 /chat 端點完整流程
- [ ] 測試 /agent/run 端點完整流程
- [ ] 測試 MockAdapter (test mode only)
- [ ] 測試 LocalAdapter (production mode)
- [ ] 測試錯誤處理和 trace 生成
- [ ] 測試 memory replay 功能
- [ ] 測試任務狀態轉換 (QUEUED → RUNNING → DONE)
- [ ] 測試 seal 機制

### 測試命令
```bash
# Unit tests
python -m pytest tests/ -v -k "runtime or memory or task"

# Integration tests
python -m pytest tests/integration/ -v

# 手動測試 API
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "test-123"}'
```

---

## 完成定義 (Definition of Done)

- [ ] 所有三個 P0 模組已實作並整合
- [ ] 所有驗收標準已通過
- [ ] 單元測試已撰寫並通過 (覆蓋率 > 80%)
- [ ] 整合測試已撰寫並通過
- [ ] API 文件已更新
- [ ] 內部文件已更新 (docs/)
- [ ] 可在 DL580 本地部署並運行
- [ ] 所有 API 回應包含必要的 metadata:
  - trace_id
  - origin_signature
  - runtime_mode
  - runtime_origin
  - engine
- [ ] Code review 已完成
- [ ] 無已知的 P0 blocking issues

---

## 文件更新需求

需要更新或新增的文件：
- [ ] `docs/P0_PRODUCTION_CORE.md` - 更新核心模組說明
- [ ] `docs/API.md` - 新增 /agent/run API 文件
- [ ] `docs/DEPLOYMENT.md` - 更新部署說明
- [ ] `README.md` - 更新功能清單

---

## 參考資料

### 現有實作
根據 repository memories，以下模組已經實作：
- `MRL_runtime_config.py` - Runtime mode 控制
- `MRL_memory_integration.py` - Memory 整合
- `MRL_task_orchestrator.py` - Task orchestrator
- `MRL_result_gating.py` - Result gating (P0-5 會用到)

### 相關文件
- `docs/P0_PRODUCTION_CORE.md` - P0 核心功能說明
- `docs/IMPLEMENTATION_SUMMARY.md` - 實作總結

---

## 下一步

完成此 issue 後，繼續：
- **P0-1** MRL_Product_Entry_UI - 產品級使用者介面
- **P0-5** MRL_Result_Gating - 結果分層與權限控制

---

**Estimated Effort:** 3-5 days
**Assignees:** @dofaromg, @Claude, @Codex
**Created:** 2026-05-07
**Origin Signature:** MrLiouWord
