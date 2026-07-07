# MRL 系統 LLM 模型開發計劃 v1

> **根源權威**：Mr.liou ｜ canonical：`MRL_LLM模型開發計劃_v1` ｜ origin_signature: `MrLiouWord`
> **當下狀態**：2026-07-07（沙盒）｜ 本檔為 **開發計劃書**，不宣稱任一項已上線。
> **對應 Issue**：DOF-11「開發」（附件《MRL系統LLM模型開發計劃》）
> **母體整合法則**：Additive-Only —— 本檔只新增、只定位，不刪除、不覆蓋既有模組。

本文件把 MRL LLM 子系統既有的分散模組（gateway / adapter / native adapter /
context / streaming / guardrail / 真模型 P0）收斂成單一開發主線，並依 CLAUDE.md
狀態回報約定，逐項標明「當下狀態」（沙盒／實機／待驗證）。狀態會隨環境改變。

---

## 0. 現有資產盤點（實證，非計劃）

以下模組為 repo 內既存、可直接定位的 LLM 相關實體：

| 環節 | 模組 | 角色 | 當下狀態 |
|------|------|------|---------|
| 本地推論閘道 | [`09_workflow/llm_gateway.py`](../09_workflow/llm_gateway.py) | ollama / llamacpp / stub 自動偵測，零外部依賴 | 沙盒可跑（stub fallback 恆可用） |
| 統一 adapter 介面 | [`09_workflow/llm_adapter.py`](../09_workflow/llm_adapter.py) | OpenAI / Anthropic / Local / Mock 統一封裝 | 沙盒可跑（mock） |
| 零依賴原生 adapter | [`09_workflow/MRL_LLM_NativeAdapter_v1.py`](../09_workflow/MRL_LLM_NativeAdapter_v1.py) | 純 stdlib urllib，取代 openai / anthropic SDK 殼 | 沙盒 import 通；真端點待金鑰 |
| 母體 gateway 橋接 | [`09_workflow/MRL_MotherGateway_Adapter_v1.py`](../09_workflow/MRL_MotherGateway_Adapter_v1.py) | 對接母體 assembly 的 adapter 註冊 | 沙盒可跑 |
| 上下文管理 | [`09_workflow/context_manager.py`](../09_workflow/context_manager.py) | token 預算、截斷／滑窗／摘要策略 | 沙盒可跑 |
| 串流輸出 | [`09_workflow/streaming.py`](../09_workflow/streaming.py) | token-by-token，MRL trace 蓋章 | 沙盒可跑 |
| 安全護欄 | [`09_workflow/guardrail.py`](../09_workflow/guardrail.py) | pre/post 內容安全鏈，deny-by-default | 沙盒可跑 |
| 設定管理 | [`09_workflow/config_manager.py`](../09_workflow/config_manager.py) | `llm.*` 鍵（default_model / api_key / local_base_url / enable_local），env `MRL_` 覆寫 | 沙盒可跑 |
| 真模型 P0 指南 | [`MRL_真模型上線啟用_P0_v1.md`](./MRL_真模型上線啟用_P0_v1.md) | 端到端啟用路徑（設金鑰即上線） | 路徑就緒，**真答案待金鑰實證** |

回歸測試（既有）：`tests/test_llm_gateway.py`、`tests/test_MRL_llm_native_adapter.py`、
`tests/test_MRL_mother_gateway_adapter.py`、`tests/test_MRL_real_model_e2e.py`
（有金鑰自動實打，無金鑰 skip）。

> **誠實邊界**：SDK 殼已可由 `MRL_LLM_NativeAdapter_v1` 回收；但模型權重／雲端端點
> 本體仍是外部服務，無法收進 repo。真正母體主權路徑 = 指向本地端點
> （Ollama / llama.cpp，`base_url=localhost`）。此為既有模組已載明之邊界。

---

## 1. 開發目標（本計劃要達成什麼）

1. **單一入口收斂**：所有 LLM 呼叫統一經 `MotherGateway` → adapter，禁止散落直呼。
2. **本地優先、雲可選**：預設本地端點（零成本、離線）；雲端僅在設金鑰時啟用。
3. **不偽造**：無可用後端時明確拒絕或明示 stub，不以 mock 冒充真答案。
4. **全程可審計**：每次呼叫寫入 trace（origin_signature + trace_id + elapsed）。
5. **P0 真模型**：完成端到端真答案實證，達成「超越了才上線」關卡。

---

## 2. 階段計劃（Milestones）

### M1 — 收斂與對齊（當下可做）

- [ ] 盤點 `llm_gateway` / `llm_adapter` / `MRL_LLM_NativeAdapter_v1` 三者職責邊界，
      文件化「呼叫應走哪一條」的單一決策路徑（本檔第 0、1 節為起點）。
- [ ] 確認 `config_manager` 的 `llm.*` 鍵為唯一設定來源，補齊缺省值文件。
- [ ] 既有 LLM 測試在沙盒全綠（無金鑰路徑）作為基線。

**驗收（沙盒）**：`pytest -q tests/test_llm_gateway.py tests/test_MRL_llm_native_adapter.py` 綠。

### M2 — 本地真模型（離線、零成本）

- [ ] 實機啟動 Ollama / llama.cpp，`llm_gateway status` 回報非 stub 後端。
- [ ] `enable_local=true` + `local_base_url` 指向本地端點，`chat()` 回真答案。
- [ ] context_manager 的 token 預算策略對真模型 context window 校準。

**驗收（實機）**：本地端點回傳非 `[stub]` / 非 `[MockAdapter] Echo` 的真實答案。
> 未實機驗證前一律標「待實機 OLLAMA_HOST 驗收」。

### M3 — 雲端真模型（可選，設金鑰即啟用）

- [ ] 依 `MRL_真模型上線啟用_P0_v1` 設 `OPENAI_API_KEY` / `ANTHROPIC_API_KEY`。
- [ ] `test_MRL_real_model_e2e.py` 由 skip 轉為實打綠燈。
- [ ] guardrail 對真模型輸入／輸出鏈路生效。

**驗收（實機）**：E2E 綠 → 達成 P0「真模型端到端」。
> 在真答案實證前，標記「路徑就緒、待金鑰上線」，不宣稱已上線。

### M4 — 生產強化（持續）

- [ ] 串流（`streaming.py`）對真後端 token-by-token 驗證。
- [ ] 全量 origin_signature / trace_id 蓋章覆蓋所有 LLM 回應。
- [ ] 失敗重試 / 逾時 / 降級（真端點 → 本地 → stub）策略明文化與測試。
- [ ] 對照 [`MRL_主流交叉比對_v1`](./MRL_主流交叉比對_v1.md) 檢視能力打平／超越項。

---

## 3. 狀態彙總表（誠實）

| 里程碑 | 層次 | 當下狀態（2026-07-07） |
|--------|------|----------------------|
| M1 收斂對齊 | 沙盒 | 進行中 —— 本計劃書為起點 |
| M2 本地真模型 | 實機 | **待實機 OLLAMA_HOST 驗收** |
| M3 雲端真模型 | 實機 | **路徑就緒、待金鑰上線** |
| M4 生產強化 | 混合 | 待 M2/M3 後展開 |

> 本表為當下狀態快照，非永久結論；隨環境（沙盒／實機／金鑰）改變即更新。

---

## 4. 驗證指令（設好後可實跑）

```bash
# 後端狀態（沙盒回 stub；實機啟 Ollama 後回 ollama）
python3 09_workflow/llm_gateway.py status

# 本地真模型（需先啟 Ollama）
python3 09_workflow/config_manager.py set --key llm.enable_local --value true
python3 09_workflow/config_manager.py set --key llm.local_base_url --value http://localhost:11434/v1
python3 09_workflow/config_manager.py set --key llm.default_model --value llama3

# 端到端冒煙（有金鑰自動實打，無金鑰 skip）
python3 -m pytest -q tests/test_MRL_real_model_e2e.py -v
```

---

origin_signature = `MrLiouWord`
