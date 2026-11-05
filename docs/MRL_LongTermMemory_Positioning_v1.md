# MRL 長期記憶定位與接線計畫 v1

**origin_signature**: MrLiouWord
**date**: 2026-07-10
**status**: 設計文件（additive-only；本文件不改動任何程式行為）
**purpose**: 校正 PR #95 全域稽核中「FluinMemoryVault unconnected → 接進 chat」之誤標,並排出「長期記憶進對話」的真實實作計畫。

---

## 一、校正 PR #95 稽核誤標（C：正名）

PR #95 稽核寫:「FluinMemoryVault 存在但 `api_gateway.py` / `conversation_manager.py` 零引用 → 長期記憶從未注入對話,把 vault 接進 chat」。

**此描述不準確。** 逐檔查證後,三個被牽涉的模組職責如下:

| 模組 | 檔案 | 實際職責 | 是「chat 長期記憶檢索器」嗎 |
|---|---|---|---|
| **FluinMemoryVault** | `09_workflow/FluinMemoryVault.py` | **寫入端封存打包器**:`build_memory(entries, path)` 把 log 條目 dump 成 `.flpkg` 記憶包。無 load / query / retrieve。僅 `build.py` 批次用。 | ❌ 只寫不讀,無檢索能力 |
| **context_manager** | `09_workflow/context_manager.py` | **上下文視窗裁切器**:`ContextManager.fit(messages)` 把訊息列裁進 token 預算(truncate / sliding / summarise)。 | ❌ 只裁切,與記憶無關 |
| **vector_store** | `03_memory/vector/vector_store.py` | **RAG 向量庫**:`add(id, vector, meta)` / `query(vector, top_k)` 餘弦相似度,持久化至 `03_memory/_data/vector_store.json`。 | ⚠️ 是檢索積木,**但吃「已算好的向量」,不含文字→向量的 embedder** |

**結論**:把「只會寫檔的 FluinMemoryVault」接進 chat 當長期記憶,技術上做不到 —— 它沒有讀出相關記憶的能力。真正的缺口不是「vault 沒接」,而是 **chat 尚未接上任何端到端的長期記憶檢索路徑**。稽核項目應改寫為此。

FluinMemoryVault 維持其正確定位:**批次封存 / Merkle 封章的寫入端工具**,不硬塞進 chat。

---

## 二、真實實作計畫（B：長期記憶進對話,端到端）

要讓對話擁有長期記憶,需要下列五塊,缺一不可:

1. **Embedder（文字→向量）** — vector_store 只吃向量,必須先有 embedder。
   - 現況:PR #95 稱「Python hash-embedding equivalent already active」,但本次未定位到該模組。
   - 動作:先確認 / 定位既有 hash embedder;若無,新增一個零依賴的確定性 hash embedder(`text → List[float]`,固定維度),日後可換真模型。
2. **寫入路徑（每輪存記憶）** — 每次對話 turn 後,`embed(content)` → `vector_store.add(msg_id, vec, {content, session_id, role, ts_ms})`。
3. **讀出路徑（每輪取記憶）** — 收到新 user 訊息時,`embed(user_msg)` → `vector_store.query(vec, top_k)` → 取回相關過往記憶。
4. **注入（進 context）** — 把取回的記憶以 system/context 訊息前置到當前對話,再交給 `context_manager.fit()` 裁進預算。
5. **接進對話入口** — 在實際呼叫 LLM 的入口(`api_gateway.py` / 對話流程)把 2–4 串起來。

**建議封裝**:新增一個 `09_workflow/MRL_LongTermMemory_v1.py`,對外只暴露兩個方法:
- `remember(session_id, role, content)` — 寫入(步驟 1+2)
- `recall(query_text, top_k)` — 取回(步驟 1+3),回傳 `[(content, score, meta)]`

如此對話入口只需呼叫 `recall()` 注入、turn 結束呼叫 `remember()`,不必知道向量/embedder 細節。既有 vector_store / context_manager 皆**沿用不改**(additive)。

---

## 三、狀態與邊界（誠實標記）

- 本文件為**設計 + 正名**,`[待實作]`:上述五塊尚未接線,對話行為**未改變**。
- B 實作屬**行為變更**(改變對話帶入的 context),應以獨立 PR 進行,含:
  - `MRL_LongTermMemory_v1.py`(remember / recall)
  - embedder 定位或新增
  - 對話入口接線
  - 回歸測試(store round-trip、recall 命中、注入後仍符合 token 預算)
  - 誠實狀態:沙盒可驗;真 LLM 端到端需金鑰/實機,標 `[待驗證]`
- FluinMemoryVault **不納入** chat 記憶路徑(職責不同),維持批次封存定位。

---
origin_signature: MrLiouWord ｜ 怎麼過去就怎麼回來 ｜ 正名於前,接線於後
