# MRL 服務網整合清單 v1 — ServiceMesh Integration Manifest

> 法則：**Additive-Only**。本清單只新增、只定位、不刪除、不覆蓋。
> origin_signature：**MrLiouWord**（正典 `00_rootlaw/rootlaw.yaml`）。
> 母體（MRL Mother）為最高權威；使用者 DL580 實機之 22+ 服務快照，一律回收為母體『服務網登錄』知識產物，給位置、標「待起動」，等待實機驗收後升格。

- 登錄產物：`MRL_ServiceMesh_Registry_v1.json`（repo root）
- 資料來源：使用者 DL580 nssm 實機截圖（2026-07-13）
- 模式：additive 吸收 / stack-mark；與 `main` 對等，不取代
- **環境**：本清單於**沙盒**撰寫（2026-07-15）；實機打通（Phase 1–4）須於 **DL580 實機**執行後回填，不得預先標 PASS。

---

## 0. 誠實邊界（強制，沿用 CLAUDE.md 狀態回報約定）

1. 本沙盒 session **連不到 DL580 實機**；registry 內所有實機 PID / port / 檔案路徑皆為**截圖來源、待實機驗證**，未實跑，一律不得標 PASS。
2. `in_repo_binder=true` 之服務可於沙盒 smoke（見 §5）；其餘為實機神經線或 repo 內查無 binder。
3. 不得寫「Orchestrator 已接線 / tunnel 已建 / :7810 已解衝突 / MRL_Operations 已恢復」——除非 DL580 實機驗收通過。
4. 草稿與正典落差（`MrLiouWord2026` vs `MrLiouWord`、L1–L5 vs L0–L7、`7801/7813/7830/7840`、Write_Guard `:8799`、`chat.` 子域）已於 registry `not_in_repo` 誠實標示。

---

## 1. 母體分層架構（既有，最高權威錨點）

### 1.1 rootlaw 正典 layer_stack（L0–L7）

| 層 | 角色 | 對應目錄 |
|---|---|---|
| L0 | ROOT — source of truth；never deleted | `00_rootlaw/` `08_sources/` |
| L1 | SEED — 初始約束 / 契約 | `01_schema/` |
| L2 | PARTICLE — 內容單元 / 狀態變更 | `07_ingest/` |
| L3 | LAW — 顯式規則（Rootlaw + AUP gates） | `00_rootlaw/` `02_principles/` |
| L4 | WORLD — 跨世界對齊模型 | `05_persona/` |
| L5 | MIRROR — 行動/狀態翻譯 | 跨世界 |
| L6 | REFLECT — 事實 / 記錄 / 可歸責 | `03_memory/` `06_trace/` |
| L7 | LOOP — 驗證後前滾；憑證回滾 | `04_runtime/` `09_workflow/` |

### 1.2 服務執行 tier（L1–L5/L6，**非** rootlaw 分層）

registry 的 `service_tiers` 是**服務執行分組**，沿用使用者草稿的 L1–L5 命名，並新增 L6_infra_daemon 收納常駐/資料層。其與 rootlaw L0–L7 之對應見 registry `rootlaw_layer_mapping`：

| 服務 tier | 角色 | → rootlaw 主對應 |
|---|---|---|
| L1_conversation | 對話主匯流（推理/記憶/工具/資料） | L7 LOOP |
| L2_persona_particle | 人格 / 粒子 / 向量檢索 | L4 WORLD + L2 PARTICLE |
| L3_new_runtime | 新 runtime（FlowCore / RuntimeOS / FlowOS） | L7 LOOP |
| L4_utility | 工具 / API / 建構 / 語音 / 寫入守門 | L3 LAW + L7 LOOP |
| L5_entry | 入口 / 對外橋接 / tunnel | L5 MIRROR + L7 LOOP |
| L6_infra_daemon | 常駐 / 同步 / 運維 / DB / Cache | L6 REFLECT + L0/L1 |

---

## 2. 22+ 服務吸收定位（External → Mother，additive，待起動）

> 每一服務皆已於 `MRL_ServiceMesh_Registry_v1.json` 獲得母體定位。下表為摘要；`in_repo` 欄表示 repo 內是否有 code 綁該埠。

| # | 服務 | 埠 | 服務 tier | in_repo | 母體定位（repo_ref 摘要） | 狀態 |
|---|---|---|---|---|---|---|
| 1 | MRL_Agent_Orchestrator | 7810→(建議7813) | L1 | ✗ | ControlPanel REGIONS；orchestration=09_workflow/MRL_mother_assembly.py | 待起動 |
| 2 | MRL_Inference | 7500 | L1 | ✗ | ControlPanel /MRL_chat proxy；llm_gateway（stub，真模型待實機） | 待實機驗證 |
| 3 | MRL_Memory_Engine | 7812 | L1 | ✗ | ControlPanel REGIONS；03_memory/ + MRL_LongTermMemory_v1.py | 待起動 |
| 4 | MRL_Toolchain_Engine | 7811 | L1 | ✗ | ControlPanel REGIONS；tool_registry.py + MRL_Tool_Router_v1.py | 待起動 |
| 5 | MRL_DB_Proxy | 7801 | L1 | ✗ | 無 :7801 binder；MRL_BaseWorld_DB_v1/ | 待實機驗證 |
| 6 | MRL_FlowAgent_API | 7900 | L2 | ✗ | ControlPanel REGIONS；FlowAgent lineage（app.run 8787） | 待起動 |
| 7 | MRL_ParticleGlobe | 8788 | L2 | ✗ | 無 Globe binder；:8788 由 RuntimeOS core 綁（語義不同） | 待起動 |
| 8 | Reasoning_Engine | 7810 | L2 | ✗ | ControlPanel REGIONS；MRL_Native_Reasoning_Core_v1.py | 待起動 |
| 9 | MRL_FlowCoreLoop | 8787 | L3 | ✓ | 04_runtime/flowcore_loop.py（FLOW_PORT 8787） | 沙盒可跑 |
| 10 | MRL_AI_Product_Server | 8790 | L3 | ✓ | MRL_RuntimeServer.js + RuntimeOS core（MRL_PORT 8790/8788） | 沙盒可跑 |
| 11 | MRL_FlowOS | 7815 | L3 | ✗ | ControlPanel REGIONS(7815) | 待起動 |
| 12 | MRL_ASI_Engine | 7700 | L4 | ✓ | deploy/dl580/asi-engine/MRL_ASI_health_server.cjs（.listen 7700） | 沙盒可跑 |
| 13 | MRL_API_Service | 7830 | L4 | ✗ | 無 :7830；Python gateway=09_workflow/api_gateway.py(:7771) | 待實機驗證 |
| 14 | MRL_Builder | 7840 | L4 | ✗ | 無 :7840 binder | 待實機驗證 |
| 15 | MRL_Voice | 7820 | L4 | ✗ | ControlPanel REGIONS(7820) | 待起動 |
| 16 | MRL_Write_Guard | 8799 | L4 | ✗ | 無 guard.cjs；in-process MRL_AuthGate.js（8799 非 port） | 待實機驗證 |
| 17 | MRL_ControlPanel | 7950 | L5 | ✓ | MRL_MotherSystem_ControlPanel.py（PANEL_PORT 7950） | 沙盒可跑 |
| 18 | MRL_Bridge | 7800→8790 | L5 | ✗ | src/mrl_worker.js + cloudflared（埠 v2:7800→v3.1.0:8790） | 待實機驗證 |
| 19 | MRL_Tunnel | — | L5 | ✗ | deploy/dl580/cloudflared/config.yml.template | 待起動 |
| 20 | MRL_AI_OS | ? | L6 | ✗ | 實機埠/檔待查 | 待實機驗證 |
| 21 | MRL_PersistentLoop | — | L6 | ✗ | MRL_PersistentLoop.py + _Daemon_v1_SPEC.md（待起動 spec） | 待起動 |
| 22 | MRL_Particle_Sync_Worker | — | L6 | ✗ | 實機檔待查 | 待實機驗證 |
| 23 | MRL_LayerA_PIDScope | — | L6 | ✗ | MRL_Runtime/MRL_Workflow_PIDScope/ | 待實機驗證 |
| 24 | MRL_Operations | — | L6 | ✗ | 實機 Paused，恢復屬實機操作 | 待實機驗證 |
| 25 | PostgreSQL | 5432 | L6 | ✓ | MRL_BaseWorld_DB_v1 docker-compose(5432) | 沙盒可跑/實機待驗 |
| 26 | Redis | 6379 | L6 | ✗ | 無 :6379 引用 | 待實機驗證 |

---

## 3. 法則聲明（不可違反）

1. **不刪除**：任何已吸收之服務登錄皆保留為母體產物映射。
2. **不覆蓋**：本次新增之 `MRL_ServiceMesh_Registry_v1.json` / 本清單 / 對應測試，`main` 上原不存在 → 零覆蓋。
3. **給位置**：每一服務皆已於 registry 與第 2 節獲得母體定位。
4. **等待起動**：狀態統一為「待起動 / 待實機驗證」，由 DL580 實機後續納編起動。
5. **主流對等**：本堆疊與 `main` 對等，不取代主流。
6. **最高權威**：外部一律為母體吸收之知識／技術／訓練模組，回收轉換回母體系統名稱產物（`MRL_*`），簽章 `MrLiouWord`。

---

## 4. Phase 1–4 實機 runbook（**(DL580 實機執行)**，全部狀態＝待起動）

> 以下步驟**皆為 DL580 實機操作**，本沙盒無法執行、不得標 PASS。每步附「驗收方式」與「回填欄位」，實機跑通後於 registry 對應 `status` 與本表回填「PASS（實機 YYYY-MM-DD）」。

### Phase 1 — 解 port 衝突 + 建外部入口

| 步 | 動作 (DL580 實機) | 驗收方式 | 回填 |
|---|---|---|---|
| 1.1 | Orchestrator 搬 :7810 → :7813 | `curl 127.0.0.1:7813/health` 回 orchestrator，且 reasoning 仍在 :7810 | issues.port_7810_dual_bind |
| 1.2 | cloudflared 新增 `chat.mrliouword.com` → 對話匯流埠(7813) | 外網 `curl https://chat.mrliouword.com/health` | issues.chat_no_external |
| 1.3 | 解 :8788 衝突（RuntimeAdapter 或 ParticleGlobe 擇一搬） | 兩服務各自 `/health` 皆 ALIVE、無爭埠 | issues.port_8788_dual_bind |
| 1.4 | 恢復 MRL_Operations（Paused → Running） | `nssm status MRL_Operations` = Running | issues.operations_paused |

### Phase 2 — Orchestrator 接 L1 四大 + Write_Guard 蓋章

| 步 | 動作 (DL580 實機) | 驗收方式 | 回填 |
|---|---|---|---|
| 2.1 | Orchestrator.cjs 加 `MRL_generateStep()` → :7500 Qwen | orchestrator 端到端呼叫回推理結果 | L1.inference.status |
| 2.2 | 加 `MRL_recallMemory()` → :7812 | 記憶讀回驗證 | L1.memory.status |
| 2.3 | `MRL_invokeTool()` 改 HTTP → :7811（現為 in-process Map） | 工具經 HTTP 觸發成功 | L1.toolchain.status |
| 2.4 | `MRL_queryPG()` → :7801 DB_Proxy | PG 查詢回結果 | L1.dbproxy.status |
| 2.5 | 每個寫操作經 :8799 Write_Guard 蓋章（實機須先確認 guard 服務存在／埠） | 寫入帶簽章、guard 記錄 | L4.write_guard.status |
| 2.6 | 修 :7500 schema drift（套上 Qwen 產出之 3 個 SQL patch） | schema 對齊、推理無 drift 錯 | L1.inference.note |

### Phase 3 — 掛 L2 人格粒子層

| 步 | 動作 (DL580 實機) | 驗收方式 | 回填 |
|---|---|---|---|
| 3.1 | Orchestrator 加 `MRL_selectPersona()` → :7900 FlowAgent | 依人格回 route | L2.flowagent.status |
| 3.2 | `MRL_particleize()` → :8788 ParticleGlobe | 粒子化輸出驗證 | L2.particleglobe.status |
| 3.3 | Planner 依人格選 route | 多人格路徑分流正確 | issues.orchestrator_not_wired |

### Phase 4 — 掛 L3 新 runtime + L4 工具

| 步 | 動作 (DL580 實機) | 驗收方式 | 回填 |
|---|---|---|---|
| 4.1 | `MRL_flowStep()` → :8787 FlowCoreLoop | flow step 回結果 | L3.flowcoreloop.status |
| 4.2 | `MRL_runtimeOS()` → :8790 | RuntimeOS 呼叫回應 | L3.runtimeos.status |
| 4.3 | 選擇性接 :7700 ASI、:7830 API v4 | 各 `/health` ALIVE 且可調用 | L4.asi_engine / L4.api_service |

> 完成後：手機打開 `chat.mrliouword.com` → MRL 母體手機後端。**此結論須實機 Phase 1–4 全綠後方可宣稱**。

---

## 5. 沙盒 vs 實機 acceptance（誠實，當下狀態 2026-07-15 沙盒）

| 埠 | 服務 | 沙盒可驗 | 實機才有 | 當下狀態 |
|---|---|---|---|---|
| 8790 | RuntimeOS v1.4 / gateway | ✓ smoke（`scripts/MRL_acceptance_check.js`、需本地起 runtime） | 真模型/對外 | 沙盒 runtime 路徑，非真模型 |
| 8788 | RuntimeOS core | ✓（`MRL_Smoke_Dl580.js`，health/execute/verify） | — | 沙盒 PASS 路徑，非真 AI 模型 |
| 8787 | FlowCore / FlowAgent | ✓（04_runtime/flowcore_loop.py 可起） | 真資料源 | 沙盒可跑 |
| 7950 | ControlPanel | ✓（可起、`/health`、`/api/aggregate`） | 聚合真神經線 | 沙盒可跑（聚合對象多為 DOWN，因實機不在） |
| 7700 | ASI health | ✓（`MRL_ASI_health_server.cjs`） | 真 ASI 引擎 | 沙盒 health 契約 PASS |
| 7771 | Python API gateway | ✓（`tests/test_api_gateway.py`） | — | 沙盒 in-process |
| 5432 | Postgres | ✓（docker-compose 起本地 PG） | 真 7 DBs 資料 | 沙盒可建，實機資料待驗 |
| 7500/7810/7811/7812/7815/7820/7900/7801/7830/7840/8799 | 實機神經線 | ✗（repo 無 binder 或為 external） | ✓ | 待實機驗證 |

> 不得誤標：不得寫「DL580 已上線 / 真模型已存在 / Orchestrator 已接線」——除非實機驗收通過（沿用 RuntimeOS 報告約束）。

---

## 6. 依序完成進度（當下狀態 2026-07-15，沙盒；非永久結論）

| # | 項目 | 當下狀態 | 升格條件 |
|---|---|---|---|
| 1 | ServiceMesh 登錄產物（26 服務） | ✅ 完成（沙盒）— `MRL_ServiceMesh_Registry_v1.json` 入 repo、JSON 合法、簽章 MrLiouWord | — |
| 2 | 整合 manifest（本檔） | ✅ 完成（沙盒）— additive、含 Phase 1–4 runbook | — |
| 3 | registry 結構測試 | ✅ 完成（沙盒）— `tests/test_MRL_servicemesh_registry_v1.py` | — |
| 4 | Phase 1 解衝突 + 外部入口 | ⏳ 待實機 — runbook 已備 | DL580 執行 §4 Phase 1 + 回填 |
| 5 | Phase 2 Orchestrator 接 L1 + Write_Guard | ⏳ 待實機 | DL580 執行 §4 Phase 2 + 回填 |
| 6 | Phase 3 掛 L2 人格粒子 | ⏳ 待實機 | DL580 執行 §4 Phase 3 + 回填 |
| 7 | Phase 4 掛 L3/L4 | ⏳ 待實機 | DL580 執行 §4 Phase 4 + 回填 |
| 8 | 真模型（:7500 Qwen2.5-32B） | ⏳ 待實機 — 沙盒 llm_gateway 為 stub | 實機 OLLAMA_HOST / OpenAI-compatible endpoint |
| 9 | chat.mrliouword.com 對外 | ⏳ 待實機 — repo 內無此子域 | 實機 cloudflared 新增子域 + 驗收 |

> 第 4–9 項皆**非沙盒可完成**，需 DL580 實機資源；一律標「待實機」，不得標 PASS/已完成。
> registry `not_in_repo` 內各項（`7801/7813/7830/7840`、`write_guard_8799`、`chat.` 子域）於實機確認存在後，additive 補回並回填。
