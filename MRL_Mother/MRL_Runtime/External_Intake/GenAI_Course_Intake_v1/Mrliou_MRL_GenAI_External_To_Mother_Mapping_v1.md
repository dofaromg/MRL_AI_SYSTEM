# MRL GenAI External → Mother Mapping v1

## 映射基本資訊

| 欄位 | 值 |
|------|-----|
| Mapping ID | MRL-MAP-GENAI-001 |
| Source Ref | MRL-EXT-GENAI-COURSE-001 |
| Source Title | Applied Generative AI for Digital Transformation |
| Created At | 2026-06-29 |
| Mapping Rule | external_absorbed_by_mother_only |

## 核心規則

> 外部概念只能被映射進 MRL 母體，不得反向定義或覆蓋 MRL 命名與架構。

## Overlap Level 說明

| Level | 意義 |
|-------|------|
| COMMON | 廣泛共有概念，有直接功能對應 |
| STRUCTURAL | 核心結構等效，外部概念與 MRL 元件有直接結構映射 |
| UNIQUE_SIMILARITY | 識別到相似性，但 MRL 實作有獨特特性；需更多證據確認 |
| EVIDENCE_REQUIRED | 潛在映射已標記，但需額外 runtime 證據才能確認 |

## 映射表

| External Concept | External Label | MRL Target | Overlap Level |
|-----------------|----------------|------------|---------------|
| External_GenAI | Generative AI | **Mrliou_MRL_Runtime** | STRUCTURAL |
| External_AI_Agent | AI Agent | **Mrliou_FlowAgent** | STRUCTURAL |
| External_Workflow | AI Workflow | **Mrliou_FlowComputer** | COMMON |
| External_RAG | Retrieval-Augmented Generation | **Mrliou_MRL_Knowledge_Index / Vector Memory** | UNIQUE_SIMILARITY |
| External_Governance | AI Governance | **Mrliou_MRL_LAW / AuditSupervisor** | STRUCTURAL |
| External_Enterprise_AI | Enterprise AI | **Mrliou_MRL_RuntimeOS** | STRUCTURAL |
| External_Automation | Automation | **Mrliou_MRL_RuntimeBridge** | COMMON |
| External_Digital_Transformation | Digital Transformation | **Mrliou_MRL_System_Reconstruction** | UNIQUE_SIMILARITY |

## 詳細映射說明

### External_GenAI → Mrliou_MRL_Runtime
- **Overlap Level**: STRUCTURAL
- **說明**: GenAI 執行是 MRL Runtime 的核心關注。外部課程的生成式 AI 概念被吸收為 Mrliou_MRL_Runtime 的能力參考。

### External_AI_Agent → Mrliou_FlowAgent
- **Overlap Level**: STRUCTURAL
- **說明**: FlowAgent 是 MRL 母體的標準 Agent 執行單元，源自 FlowAgent lineage 被吸收進 MRL 母體。

### External_Workflow → Mrliou_FlowComputer
- **Overlap Level**: COMMON
- **說明**: 工作流程編排直接對應 FlowComputer 執行模型。

### External_RAG → Mrliou_MRL_Knowledge_Index / Vector Memory
- **Overlap Level**: UNIQUE_SIMILARITY
- **說明**: RAG 模式與 MRL Vector Memory 檢索相似；完整結構等效性需要實機驗證。

### External_Governance → Mrliou_MRL_LAW / AuditSupervisor
- **Overlap Level**: STRUCTURAL
- **說明**: AI 治理是 MRL_LAW 與 AuditSupervisor 元件的職責範疇。

### External_Enterprise_AI → Mrliou_MRL_RuntimeOS
- **Overlap Level**: STRUCTURAL
- **說明**: 企業 AI 平台對應 Mrliou_MRL_RuntimeOS 架構層。

### External_Automation → Mrliou_MRL_RuntimeBridge
- **Overlap Level**: COMMON
- **說明**: 自動化執行透過 MRL_RuntimeBridge 橋接 MRL runtime 與外部系統。

### External_Digital_Transformation → Mrliou_MRL_System_Reconstruction
- **Overlap Level**: UNIQUE_SIMILARITY
- **說明**: 數位轉型概念映射到 MRL 的系統重建方法論；需要進一步 evidence chain 確認。

## 狀態標記

當下狀態（2026-06-29）：映射完整建立（沙盒），8 項外部概念全部映射至 MRL 母體元件。
