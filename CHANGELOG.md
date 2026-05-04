# Changelog

All notable changes to MRL_AI_SYSTEM will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

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
