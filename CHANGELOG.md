# Changelog

All notable changes to MRL_AI_SYSTEM will be documented in this file.

Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

---

## [Unreleased]

### Added（Issue #146 — Mrliouhan.ai × Manus 網域權位 SEV-1，事件仍 OPEN）
- `MRL_Docs/Evidence/20261019/MRL_Issue146_Mrliouhan_網域權位觀測_R01.md` — 沙盒唯讀觀測（RDAP／DNS／HTTP）、與舊紀錄的追加對照、假設 H1–H3、必查項進度（多項待查）
- `MRL_Docs/Evidence/20261019/snapshots/` — 「修正前」快照與 `SHA256SUMS`
- `MRL_Docs/Governance/MRL_attribution_roles_v1.json` — 權位／角色分離與頁面署名規則（`domain_owner`、`billing_party` 標 unverified）
- `scripts/MRL_domain_evidence_collect_v1.py` + `tests/test_MRL_domain_evidence_collect_v1.py` — 零依賴唯讀蒐證，輸出僅落本地並寫 SHA-256
- 4 個 repo 可控頁面（`MRL_Mother_Launch.js`、`MRL_Platform_Server.py`、`src/mrl_app.html`、WebConsole `index.html`）新增 author／canonical-authority／origin-signature／og:site_name metadata 與頁尾署名（純新增）

### Changed（Issue #146 — 模組穩定性；沙盒測試通過，DL580 實機待驗證）
- `scripts/MRL_domain_evidence_collect_v1.py`：暫時性網路錯誤（逾時、連線中斷、429／5xx）最多重試 3 次並記錄 `attempts`；3xx／4xx 不重試；快照與 `SHA256SUMS` 寫入後 fsync；`classify` 失敗不再丟失原始證據；輸出路徑在雲端同步資料夾時拒絕（exit 3）
- `scripts/MRL_dl580_recovery_pull_v1.py`：git 先在 `.partial-<sha>` 完成 clone＋checkout 才改名（中途失敗不留下「看似完整」的殘骸）、`GIT_TERMINAL_PROMPT=0`、rclone 預設重試、鎖檔防並行 pull（exit 5）、磁碟空間檢查（exit 6）、清單先寫暫存檔再追加雜湊再排他連結（斷電不留半成品）、`verify` 對畸形清單回報而非拋例外並列出 `unlisted`／`orphan_sums`
- `scripts/MRL_dl580_recovery_pull_v1.py`（CodeRabbit 追加）：Windows 唯讀 `.git/objects` 暫存目錄可清除、逾時也清暫存目錄並明確回報清不掉的情況、git 指令不繼承 `GIT_DIR` 等倉庫定位變數
- `scripts/MRL_dl580_recovery_pull_v1.py`：git 來源新增 `"mode": "mirror"`（`git clone --mirror`，無工作樹、保留全部 refs 與任何檔名）；起因是 DL580 實機（Windows）整個檢出被 `MRL_MotherSource_ZhiZhang_FlowAgent_Lineage_v1/母體/` 下 15 個結尾帶空白的檔名擋住。worktree 模式遇到此類失敗會提示改用 mirror；範例計畫檔的 GitHub 來源已改為 mirror；Runbook 補 Windows 取得腳本的 sparse checkout 步驟
- mirror 模式（CodeRabbit 追加）：mirror 備份存成 `<sha12>.mirror`，與 worktree 的 `<sha12>` 分開；目標已存在但不完整時回報不覆蓋；單一來源的檔案系統錯誤（`OSError`）只算該來源失敗，不中斷其餘來源與清單；真 git 的 mirror 測試改用 `git fast-import` 建立結尾空白的檔名，Windows 也能建出同樣的提交
- 證據檔 R01 追加 §7（Manus 官方服務變更的網域暫管機制與假設 H4，待查）；Runbook 補網域暫管與備份範圍注意事項
- 測試：兩個模組合計 52 項，含真實 git 本機倉庫整合測試與真實本機 HTTP 伺服器的「不跟隨轉址」測試

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
