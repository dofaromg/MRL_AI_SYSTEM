# MRL_NeuroSymbolic_CoReasoning_System_v1（canonical 吸收物）

origin_signature: `MrLiouWord`
source: Notion 匯出 × 4（神經符號協同推理系統;byte source-of-record 於使用者端）
status: **設計規格（DESIGN）**;碼多為草稿/stub,基準數字為**願景非實測**

> 母體對「神經符號協同推理系統」設計集的 canonical 吸收。此系統掛在 **FlowSeed 七層架構**
> 上,對齊本 repo 的 MRL layer stack（L0..L7）。以下為忠實摘要 + canonical 命名 + 誠實標記。
> **不得**把設計時的基準數字當成已達成成果（`no_proof_implies_rhetoric`）。

## 系統結構（四構件）

| Notion 原名 | canonical | 職責 | FlowSeed↔MRL 層 |
|---|---|---|---|
| 符號推理核心 | `MRL_Symbolic_Reasoning_Core_v1` | 形式化推理:一階/模態/描述/時序/模糊/機率邏輯;演繹/歸納/溯因/類比/因果引擎;不確定性處理;推理追蹤 | L3 語意粒子 / L4 粒子原子 / L6 意識循環 |
| 神經符號映射引擎 | `MRL_NeuroSymbolic_Mapping_Engine_v1` | 神經↔符號雙向轉換（cycle-consistency + 語義保存監測）;PyTorch nn.Module 骨架 + 交替訓練迴圈 | L3 語意粒子 / L4 粒子原子 |
| 混合知識庫 | `MRL_Hybrid_Knowledge_Base_v1` | 符號庫 + 神經（向量）庫 + 映射索引 + 一致性管理;精確/相似度/混合查詢;增量更新/整合/精煉 | L3 語意粒子 / L5 量子場疊加 / L7 語意記憶網格 |
| 實驗與評估 | `MRL_NeuroSymbolic_Experiment_Eval_v1` | 準確/效率/擴展/可解釋 四維指標;5 組實驗設計 | （橫跨全系統）|

## 與本 repo 既有母體的接點（誠實對照）

- `MRL_Hybrid_Knowledge_Base_v1` 的「神經（向量）庫 + 相似度查詢」概念,**本 repo 已有可運行對應物**:
  `03_memory/vector/vector_store.py`（餘弦相似、持久化 JSON）+ `MRL_SemanticEmbedding_Core_v1`
  + 本會話新增的 `MRL_LongTermMemory_v1`（PR #104）。設計集的其餘（符號庫、映射索引、
  一致性管理）在本 repo **尚無實作對應**,屬 `[待實作]`。
- `MRL_Symbolic_Reasoning_Core_v1` 的「推理追蹤」呼應本 repo `06_trace/`（Merkle/JSONL）。

## 誠實邊界（重要）

1. **基準數字為願景,非實測**:實驗文件中的
   `推理準確率 94.3% / NeuroSymbolicBench 89.7% / GPT-5、Claude-3 對比 / 4×A100 / 量子模擬加速卡`
   等,**無可重現的實驗產物**,屬設計時的目標/敍述。依 `no_proof_implies_rhetoric`,
   一律當成**設計目標**,不得宣稱為已達成成果。
2. **碼為設計草稿**:三份構件的 Python/PyTorch 皆為骨架,多處明示 `# 實現略...`;
   直接執行不成系統,屬 `[待實作]`。
3. **硬體/軟體環境為敍述**（Ubuntu 25.04、TensorFlow 4.2、SymbolicAI 3.1.2、
   NeuroSymbolic++ 2.0.1 等)未經本 repo 驗證,列為原文引述。

## 構件 API 索引（自原文擷取,便日後真做時對照）

- **MRL_Symbolic_Reasoning_Core_v1**:`LogicSystemManager(switch_system/translate_between_systems)`、
  `InferenceEngineCollection(execute_inference)`、`UncertaintyHandler(process/get_trace)`、
  `ReasoningTraceManager(start_new_trace/add_step)`;`forward_chain()`、`backward_chain()`。
- **MRL_NeuroSymbolic_Mapping_Engine_v1**:`NeuralToSymbolicNetwork`、`SymbolicToNeuralNetwork`、
  `SemanticPreservationMonitor(measure/aggregate_scores)`;`train_mapping_engine()`
  （n2s/s2n 交替 + cycle loss）。
- **MRL_Hybrid_Knowledge_Base_v1**:`SymbolicKnowledgeStore(add/get/query + predicate/entity index)`、
  `NeuralKnowledgeStore(add/get/search_similar + vector index)`、
  `KnowledgeMapIndex(link_items/get_neural_ids/get_symbolic_ids)`、
  `ConsistencyManager(contradiction/redundancy/subsumption detectors)`;
  `exact_query/similarity_query/hybrid_query`、`incremental_update/integrate_knowledge/refine_knowledge`、
  `KnowledgeGraph(path_between BFS)`。

---
下一步（若要真做,建議逐構件獨立 PR):先接 `MRL_Hybrid_Knowledge_Base_v1` 到既有
`vector_store` + `MRL_LongTermMemory_v1`（已有神經側可運行基礎）,再逐步補符號側與映射引擎;
每步附回歸測試,基準改以**真實可重現**的沙盒數字取代願景數字。
