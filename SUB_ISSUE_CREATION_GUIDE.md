# Sub-Issue Creation Guide for Issue #11

## Summary

已為 Issue #11 (MRL_Final_Product_Checklist_v1) 創建 P0 核心實作的子議題模板。

## 已完成的工作

1. ✅ 分析了 Issue #11 的內容和需求
2. ✅ 根據「下一個工程動作建議」識別出 P0-2、P0-3、P0-4 需要優先實作
3. ✅ 創建了詳細的子議題模板，包含：
   - 完整的需求描述
   - 明確的驗收標準
   - 技術實作要點
   - 整合需求
   - 測試計劃
   - 完成定義 (DoD)

## 模板位置

```
.github/ISSUE_TEMPLATE_P0_CORE_IMPLEMENTATION.md
```

## 如何使用此模板創建 GitHub Issue

### 方法 1: 手動創建 (推薦)

1. 開啟瀏覽器，前往：
   ```
   https://github.com/dofaromg/MRL_AI_SYSTEM/issues/new
   ```

2. 複製模板內容：
   ```bash
   cat .github/ISSUE_TEMPLATE_P0_CORE_IMPLEMENTATION.md
   ```

3. 在 GitHub Issue 表單中：
   - **Title**: `[P0 Core] Implement Runtime Router + Memory Integration + Task Orchestrator`
   - **Body**: 貼上模板內容
   - **Labels**: 加入 `MRL`, `P0`, `sub-issue`
   - **Assignees**: 分配給 @dofaromg, @Claude, @Codex (如適用)
   - **Projects**: 如果有相關 project board，加入它

4. 在 Issue 描述中提及父議題：
   ```markdown
   Parent Issue: #11
   ```

5. 點擊 "Submit new issue"

### 方法 2: 使用 GitHub CLI (如果有權限)

```bash
gh issue create \
  --repo dofaromg/MRL_AI_SYSTEM \
  --title "[P0 Core] Implement Runtime Router + Memory Integration + Task Orchestrator" \
  --label "MRL,P0,sub-issue" \
  --body-file .github/ISSUE_TEMPLATE_P0_CORE_IMPLEMENTATION.md
```

### 方法 3: 在 Issue #11 中引用

如果無法直接創建 issue，可以在 Issue #11 中添加評論：

```markdown
## P0 Core Implementation Sub-Issue

我已經準備了 P0-2 + P0-3 + P0-4 的詳細實作計劃。

請參考：`.github/ISSUE_TEMPLATE_P0_CORE_IMPLEMENTATION.md`

或直接查看此分支的模板文件。

@dofaromg 請協助創建新的 sub-issue。
```

## 子議題涵蓋範圍

### P0-2 MRL_Runtime_Router
- API Gateway 接入真實 runtime
- LocalAdapter 支援 DL580 本地模型
- MockAdapter 僅限測試模式
- Runtime fallback 機制

### P0-3 MRL_MemoryLayer_Integration
- Conversation Manager 接入 Memory Layer
- 完整 trace 記錄
- Merkle chain 完整性驗證
- Session replay 功能

### P0-4 MRL_Task_Orchestrator
- 任務生命週期管理
- 狀態機實作 (QUEUED → RUNNING → DONE/FAILED → SEALED)
- Seal 機制
- Error trace 保留

## 相關檔案

已存在的實作（根據 repository memories）：
- `09_workflow/MRL_runtime_config.py` ✅
- `09_workflow/MRL_memory_integration.py` ✅
- `09_workflow/MRL_task_orchestrator.py` ✅
- `09_workflow/MRL_result_gating.py` ✅ (P0-5 會用到)

需要整合或修改的檔案：
- `09_workflow/api_gateway.py`
- `09_workflow/conversation_manager.py`
- `09_workflow/MRL_multi_agent.py`
- `09_workflow/scheduler.py`

## 預期成果

完成此子議題後：
1. `/chat` API 可以使用真實的 LLM runtime
2. 所有對話都會被完整記錄在 memory layer
3. 任務可以被追蹤、管理、seal
4. 系統可以在 production mode 下運行
5. 所有回應都包含完整的 metadata (trace_id, origin_signature, 等)

## 下一步

完成 P0 Core 後，繼續：
1. **P0-1** MRL_Product_Entry_UI - 使用者介面
2. **P0-5** MRL_Result_Gating - 結果權限控制

然後進入 P1 階段（產品營運）：
- P1-1 MRL_Auth_Account
- P1-2 MRL_Billing_Ledger
- P1-3 MRL_Admin_Console
- P1-4 MRL_Security_Boundary

## 聯絡資訊

如有問題，請在 Issue #11 或新創建的 sub-issue 中討論。

---

**Origin Signature:** MrLiouWord
**Created:** 2026-05-07
**Branch:** claude/create-sub-issue-for-issue-11
**Commit:** da052aa
