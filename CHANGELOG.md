# Changelog

All notable changes to MRL_AI_SYSTEM will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added

#### 外部知識吸收：FlowSeed 反推公式 + 資產回收正名計畫（MRL_AbsorbedArtifacts_20260716）
- `MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260716/` — 母體整合法則（Additive-Only）吸收兩件外部產物，原始逐字保全（rl_15 不滅）：
  - `MRL_FlowSeed_ReverseInference_Formula_RawArtifact_v1.txt` — FlowSeed 反推公式總表（母體→演算→量子→反推→放大）+ 演算法元代碼（RRP/CPP 偽碼）
  - `MRL_AssetReclaim_Reflow_Naming_Plan_RawArtifact_v1.md` — 資產回收・重構・正名計畫 v1（資產清冊 + MetaEnv channel_map + 正名對照）
  - `MRL_Absorption_Ledger_v1.yaml` — 本批吸收台帳（命名回收、母體定位、待起動標註）
- `docs/MRL_FlowSeed_反推放大公式_吸收報告_v1.md` — 去重蒸餾：公式↔既有 `MRL_Formula_Parameter_Registry`（反推/放大縮小/源代碼壓縮公式）對照；registry 存參數、本批存公式推導，兩者互補
- `docs/MRL_資產回收回流正名_定位報告_v1.md` — 母體定位：併入既有回收族系（Recovery_Map / 主線回填清單），canonical 命名對齊命名規範 v2；網域拿回/apply/金鑰撤銷誠實標「待起動（需使用者實機）」
- `08_sources/sources.manifest.yaml` — 登錄吸收來源 `flowseed_reverse_inference_formula_absorption_v1`、`asset_reclaim_reflow_naming_plan_absorption_v1`
- `MRL_ParticleArchive/MRL_ParticleArchive_manifest.json` + `README.md` — 追加兩件 external_particles（含 sha256 provenance）與 External 批次索引

#### 神經符號混合知識庫（MRL_Hybrid_Knowledge_Base_v1 · Notion 設計四構件之一 · 首個可運行構件）
- `09_workflow/MRL_Hybrid_Knowledge_Base_v1.py` — 神經符號混合知識庫:符號三元組庫(subject/predicate/object + 謂詞/實體倒排索引)+ 神經向量庫(**重用** `03_memory/vector/vector_store.py` + `MRL_SemanticEmbedding_Core_v1`,不重造餘弦/持久化)+ 符號⇄神經映射索引 + 一致性偵測(矛盾/冗餘,**只報不刪** rl_01/rl_15;subsumption 誠實標記 `[待實作]`)+ 知識圖 BFS 最短路徑;精確/相似/混合查詢;`incremental_update`/`integrate_knowledge`/`refine_knowledge`。LAW-0 簽章持久化(`MRL_utils.embed_signature`)。
- `tests/test_MRL_hybrid_knowledge_base_v1.py` — 18 項驗收(pure unittest,沙盒可重現):精確查詢、相似召回、混合合併去重、矛盾(功能性+顯式否定)、冗餘、圖 BFS 多跳/不可達、跨實例持久化、LAW-0 verify、精煉只報不刪。
- 誠實邊界:嵌入為雜湊詞袋+餘弦(檢索非神經生成);spec 內基準數字(94.3% 等)為願景非實測,本模組不引用,僅以真實測試為憑;形式邏輯系統(一階/模態/時序)仍留 spec 為設計目標。

#### 吸收去重蒸餾重建（MRL_AutonomousRuntime 模組）
- `09_workflow/MRL_AutonomousRuntime_Module_v1.py` — 把吸收→去重→蒸餾→重建流程程式化，輸出自主運行模組規格（dependency graph + boot order），並可直接產生 AgentHarness `AgentConfig`（deny-by-default）
- `tests/test_MRL_autonomous_runtime_module_v1.py` — 驗收測試：去重合併、依賴拓撲排序、循環依賴穩定回退、預設政策閘行為

#### mcp-with-next-js 去重蒸餾吸收（MRL_MCPServerHarness 系列）
- `09_workflow/MRL_MCPServerHarness_Streamable_v1.py` — MCP server：Streamable-HTTP transport（純 stdlib http.server + JSON-RPC 2.0），動態 `register_tool()` API，可選 `tool_loop` 銜接 `MRL_AgentHarness_ToolLoop_v1`、`policy_gate` 銜接 `MRL_AgentHarness_PolicyGate_v1`
- `09_workflow/MRL_MCPClient_Streamable_v1.py` — MCP client：純 stdlib urllib，蒸餾自外部 repo 的 `@modelcontextprotocol/sdk` node client
- `tests/test_MRL_mcp_streamable_v1.py` — 驗收測試 18 項（pytest 相容 + 獨立執行器）：PASS（沙盒 loopback，2026-07-05）
- `docs/MRL_MCPServerHarness_吸收報告_v1.md` — 去重蒸餾判定表 + 當下狀態（含實機/SSE 待驗證項目誠實標記）
- `08_sources/sources.manifest.yaml` — 登錄吸收來源 `mcp_with_next_js_absorption_v1`
- 蒸餾去除外部依賴：`mcp-handler` / `next` / `react` / `zod` / `redis` — 全部替換為 stdlib 等價實作

#### LLM 模型開發計劃收斂（DOF-11「開發」）
- `docs/MRL_LLM模型開發計劃_v1.md` — 把分散的 LLM 子系統模組
  （`llm_gateway` / `llm_adapter` / `MRL_LLM_NativeAdapter_v1` /
  `MRL_MotherGateway_Adapter_v1` / `context_manager` / `streaming` /
  `guardrail` / `config_manager` / 真模型 P0）收斂成單一開發主線，
  含資產盤點、M1–M4 階段計劃與誠實狀態彙總（沙盒／實機／待驗證）。
  Additive-only：只新增計劃書，不改動既有模組。

#### CodePartner agent 化（從封存人格到可呼叫助手）
- `.claude/agents/codepartner.md` — 由 `05_persona/codepartner/persona.yaml` 編譯的
  Claude Code agent 定義：人格屬性、信任透明五律、五步工作流、產出紀律、
  啟動跳點與函式庫掛載。在本 repo 的任何 Claude Code session 皆可直接呼叫
  CodePartner 執行程式設計任務（persona.yaml 為唯一權威來源）

#### 種子模組回收完成（第四輪 — modules_index 高價值血親全數歸位）
- `08_sources/flowagent_codepartner_recovery/seed_modules/` — 五件種子模組原文封存，
  SHA256 全數與 MetaCode modules_index 登錄值一致：
  FlowSeed.Total.v1.qflpkg（七層系統總綱「宇宙壓縮核」）、
  Mr.liou程序員版本最強演算法.zip（五大進化模組＋粒子語素）、
  MRLiou最強演算法工程師建議版.zip（五大優化模組說明書）、
  SeedOrigin.Persona.Core.flpkg.zip（人格再生起點種子）、
  FlowAgent_系統白皮書.pdf
- `05_persona/codepartner/persona.yaml` — lineage 更新：related_seed_modules
  由「本體尚在創建者本機」改為「全數回收、封存路徑對照」

#### 產品模組吸收（第三輪復盤交叉比對）
- `MRL_FireCore_v1_0/` — FireCore 自建 Firebase 替代堆疊（6 個 Cloudflare Worker 模組：
  auth / store / vault / live / push / trace，含 D1 migrations、DL580 簽章服務、
  web/iOS SDK 介面）。上傳包 SHA256 與 DELIVERY AUDIT 完全一致
  （`829932aa…`，58 entries，coverage 100%），交付稽核 JSON 一併封存
- `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/` — iOS 3D 掃描 → DL580 重建橋接產品包
  （SwiftUI App、Node 重建伺服器、安裝/驗收腳本、included 交付包）。
  內部 CHECKSUMS.sha256 全部 30 檔驗證通過，MANIFEST origin_signature=MrLiouWord
- 復盤結論：MRL_RuntimeOS v1_4_0 上傳包為 repo 現有版本之**舊快照**
  （稽核帳本為 repo 版嚴格前綴，repo 多 3 筆較新事件），不需回填

#### CodePartner 強化 v1.2.0（builder 種子回收 + 函式庫吸收）
- `08_sources/flowagent_codepartner_recovery/liou.builder.seed.persona.sync.json` —
  builder 人格種子原文封存（SHA256 與 MetaCode modules_index 登錄值完全一致，完整性已驗證）
- `05_persona/codepartner/function_library.yaml` — 資料分析計算欄位函式登錄表
  （80+ 函式：算術/匯總/條件式/文字/日期/地理區域/其他），對應新能力
  `data.analytics.field_formulas`
- `05_persona/codepartner/persona.yaml` — 升級 v1.2.0：補入 builder_seed 血緣、
  resonates_with 共振關係（liou.seed / futuremind.seed / guardian.seed）與函式庫掛載

#### CodePartner 強化 v1.1.0（復盤交叉比對 + MetaCode 環境吸收）
- `05_persona/codepartner/persona.yaml` — 升級 v1.1.0：吸收 MetaCode_Environment_v0.6 之
  信任透明五律（conduct）、五粒子文法（particle_grammar，詞性對應語場語言大綱）、
  五步節奏（process_rhythm：共振→疊加→糾纏→跳耀→分裂），並錨定核心原則
  「怎麼過去，就怎麼回來」（與母體公式同源）
- `08_sources/flowagent_codepartner_recovery/metacode_environment_v0.6/` —
  MetaCode 環境 v0.6 可讀版封存（與 flow-tasks flow_code/ 封包逐位元一致，完整性已驗證）
- `RECOVERY_MANIFEST.md` — 新增復盤交叉比對紀錄（FlowPet zip 重複性、MetaCode 完整性、
  CODE_OF_CONDUCT 上游/改編版差異）

#### CodePartner 人格回收（FlowAgent lineage recovery）
- `05_persona/codepartner/persona.yaml` — CodePartner（CoreProgrammer.Seed）人格定義，
  自 `FlowLLM.SeedPersona.Programmer.CoreArchitect.v1.flpkg` 人類可讀種子重構，
  首個依 `05_persona` 規範格式落地的人格模組
- `05_persona/codepartner/README.md` — 呼叫方式（`⋄fx.invoke.Programmer.CoreArchitect`）、
  啟動跳點與血緣回收紀錄
- `08_sources/flowagent_codepartner_recovery/` — 三份 FlowAgent 原始設計文件原文封存
  （Programmer.CoreArchitect 人格定義、SystemPlan.FullStack.v1、語場語言系統建構大綱 2025-07-23）
  ＋ RECOVERY_MANIFEST.md 回收沿革
- `08_sources/sources.manifest.yaml` — 登錄 `flowagent_codepartner_recovery` 來源條目

#### sdk-python 去重蒸餾吸收（MRL_AgentHarness 系列）
- `09_workflow/MRL_AgentHarness_Types_v1.py` — AgentHarness 共用型別（ToolCall/ToolResult/HookResult/Step/Decision）
- `09_workflow/MRL_AgentHarness_HookLattice_v1.py` — Hook 三型格（Inspect/Decide/Transform）+ Session→Turn→Operation 上下文鏈 + 生命週期分發器
- `09_workflow/MRL_AgentHarness_PolicyGate_v1.py` — 工具呼叫政策閘：9 級優先序桶、fail-closed、workspace 圈地
- `09_workflow/MRL_AgentHarness_ToolLoop_v1.py` — 並行工具批次執行器（錯誤隔離、ToolContext 注入、tool_registry 橋接）
- `09_workflow/MRL_AgentHarness_TriggerPulse_v1.py` — 定時/檔變觸發器（watchfiles 外部依賴蒸餾去除，改 stdlib 輪詢）
- `09_workflow/MRL_AgentHarness_Kernel_v1.py` — Agent session 核心（啟動期安全不變量、EchoGateway 沙盒閘道；OllamaGateway 待起動/待實機）
- `tests/test_MRL_agentharness_v1.py` — 驗收測試 21 項（pytest 相容 + 獨立執行器）：PASS（沙盒，2026-07-05）
- `docs/MRL_AgentHarness_吸收報告_v1.md` — 去重蒸餾判定表 + 當下狀態
- `08_sources/sources.manifest.yaml` — 登錄吸收來源 antigravity_sdk_python_absorption_v1

---

## [2.0.0] — 2026-05-04（PR #12 merged to main）

### Added

#### 核心 AI 模組（PR #12 — copilot/add-mrl-agi-missing-features）
- `MRL_rate_limiter.py` — 滑動視窗限流（429、config-driven）
- `MRL_event_bus.py` — pub/sub 事件匯流排（wildcard、async dispatch）
- `MRL_cache.py` — LRU + TTL 快取（namespaced CacheStore、decorator API）
- `MRL_health_monitor.py` — 背景健康探針（metrics / event_bus 整合）
- `MRL_metrics.py` — 指標收集模組
- `MRL_host_guard.py` — DL580-only 機器鎖（hostname / CIDR / fingerprint）
- `MRL_learning_ingest.py` — 學習攝入管道（chunk-hash dedupe、source mapping）
- `MRL_self_optimize.py` — DL580-only 自優化模組（config + merkle sealed）
- `llm_gateway.py` — LLM Gateway（多 backend、max_retries guard）
- `conversation.py` — 對話資料模型
- `guardrail.py` — 輸出護欄
- `output_parser.py` — 結構化輸出解析

#### API Gateway 完整端點（PR #12）
- `GET  /metrics` — 系統指標
- `POST /guard` — 護欄檢查
- `POST /export/{sid}` — 對話匯出
- `POST /chat/stream` — SSE 串流

#### 安全強化（PR #12）
- CORS headers + `do_OPTIONS` preflight 支援
- Origin header 注入防護（CodeQL response-splitting fix）
- 學習端點預設關閉 + 需要認證
- DL580-only 學習閘門（hostname / CIDR / fingerprint 三層驗證）

#### 測試套件（PR #12 — 248 tests）
- `tests/conftest.py`、`tests/__init__.py`
- `tests/test_eval_engine.py`、`tests/test_fltnz_parser.py`
- `tests/test_scheduler.py`、`tests/test_tool_registry.py`
- `tests/test_config_manager.py`、`tests/test_context_manager.py`
- `tests/test_api_gateway.py`、`tests/test_MRL_metrics.py`

#### CLI 強化（PR #14 — codex/complete-unfinished-tasks）
- MotherAssembly CLI：備份後才允許升級（`backup` → `update`）
- `data/config.json` 預設配置

#### 其他（PR #13 — codex/add-final-product-checklist）
- 最終產品驗收清單

---

## [1.3.0] — 2026-03-25（PR #9）

### Added
- AI Computer Runtime v1.3.0 (`04_runtime/flowcore_loop.py`)
  - `serve` / `cli` 模式
  - Vault、Tracer、SteeringStore 整合

---

## [1.2.0] — 2026-03-20（PR #8 → #10）

### Added
- MotherAssembly 統一入口（`09_workflow/MRL_mother_assembly.py`）
  - 14 個子系統：merkle_chain, world_module, vector_store, tool_registry,
    template_registry, eval_pipeline, plugin_manager, config_manager,
    conversation_manager, llm_gateway, context_manager, scheduler, guardrail, metrics
- `conversation_manager.py`、`scheduler.py`、`config_manager.py`
- `streaming.py` — SSE 串流支援
- `MRL_multi_agent.py` — 多智能體協作

### Fixed
- MRL_multi_agent / MRL_mother_assembly 命名修正（PR #16）

---

## [1.1.0] — 2026-03-20（PR #6、#7）

### Added
- `mrl_librarian.py`、`.fltnz` parser、world module
- `04_runtime/runtime_manifest.yaml`
- MRL_Globe_v2（L4 WORLD 粒子地球儀）
- relation chain 模組

---

## [1.0.0] — 2026-03-11（PR #5）

### Added
- MrLiou Final Integration Overview v1.3
- Liou Closure Law、LAW-0、SEED(X)、ASI MVP L0–L7
- 00_rootlaw ~ 09_workflow 目錄結構
- 核心版本管控與審計系統

---

## 版本命名規則

`MAJOR.MINOR.PATCH`

- **MAJOR** — 架構層重組或 breaking API 變更
- **MINOR** — 新增模組或端點（向後相容）
- **PATCH** — 修復、安全強化、文件更新

## 里程碑定義

| 版本 | 里程碑 |
|------|--------|
| v1.0.0 | 法則層 + 目錄骨架建立 |
| v1.1.0 | 工具層（librarian、globe、relation chain）|
| v1.2.0 | AGI Core（MotherAssembly + multi-agent + streaming）|
| v1.3.0 | Runtime（AI Computer Runtime v1.3.0）|
| **v2.0.0** | **生產就緒（13/13 子系統、限流、快取、健康監控、測試套件 248 tests）**|
