# Create Preflight 補做紀錄 · MRL_Wakeup_Seed_v1 ＋ MRL_FlowRhythm_v0

origin_signature: MrLiouWord ｜ record_mode: additive_only ｜ 補做日：2026-09-28（Asia/Taipei）
狀態：**當下狀態**。本檔只記錄查到的原檔與對應關係，不替建構者重新定義。

## 0. 為什麼要補做

建構者在 Notion 的已驗證規則（「🧭 MRL 世界模型工程導航」，Notion id `3c38eeee-c5b5-81ff-8ed4-c550121adddc`）規定，任何新建之前都要先做 Create Preflight：

```
Wake Memory → Origin Registry → Workspace Node Registry → Canonical Registry
→ Authority Registry → Existing Mother Position → MAP_EXISTING | SUPPLEMENT_EXISTING | CREATE_NEW
```

「MAP_EXISTING：直接沿用既有節點，禁止新建同義主體」；沒做 preflight 的 CREATE 要標 `PREFLIGHT_MISSING / DO_NOT_CREATE`。

**事實**：2026-09-27～28 建立 `MRL_Wakeup_Seed_v1/` 與 `MRL_WorldModel/MRL_FlowRhythm_v0/` 時，**沒有先做這個 preflight**。
依規則，這兩個目錄的建立行為標為 `PREFLIGHT_MISSING`。依 LAW-2（NO_DELETE），不刪除這兩個目錄，改在這裡補做 preflight，並把它們接回既有節點。

## 1. Preflight 逐段查證結果

| 段 | 查到的既有節點（原檔） | 位置 |
|---|---|---|
| Wake Memory | `MRL_STARTUP_WAKE.md`：`Top Index -> Governance / Rights -> Origin / Provenance -> Current Mode -> Task -> Gate -> Backfill`（2026-08-17） | Dropbox `/MRL_STARTUP_WAKE.md`（2026 bytes）；Google Drive `Mrliou_MRL_Startup_Wake_Rule_v1`（docx／pdf／gdoc 多份） |
| Wake Memory | 收斂紀錄：`Top Index -> Governance/Rights -> Origin/Provenance -> World/Domain/State -> Task -> Translation/Gate -> Verify -> Backfill`；「新視窗先載入本收斂紀錄＋MRL_STARTUP_WAKE.md，從未解工作接續，不要從零重建架構」 | Notion `3bf8eeee-c5b5-8172-9984-f3bb1608522b`（verified；fetch 回傳 is_archived=true，頁內自述 live restore anchor，G10 待核對） |
| Origin Registry | `MRLiou 粒子世界根源主鏈與完整三態循環建構紀錄 v1.0`：`dofaromg/----2 → 完整的粒子世界三態循環 → MRL_AI_SYSTEM → flow-tasks` | Notion `3b28eeee-c5b5-816e-911c-de4190d0b47c`（verified） |
| Canonical Registry | `00_rootlaw/canonical_pointer.yaml`：source_ref = `MRL_AI_SYSTEM/memory-system-rules-prep`（本分支），construction_ref = `MRL_AI_SYSTEM/worldmodel-identity-wake-core-v1` | GitHub 分支 `worldmodel-identity-wake-core-v1`，head `aa8bb83e6239b45203f8cba5c77af39168758d9a`，Draft PR #141（NOT_MERGED） |
| Canonical Registry | `00_rootlaw/MRL_WAKE_MANIFEST.yaml`（機器可讀 8 段喚醒序）、`04_runtime/wake_loader.py`、`06_trace/wake_trace.schema.json`、`06_trace/wake_verification_report.schema.json` | 同上分支 |
| Existing Mother Position（五段喚醒序的出處） | `FlowAgent · Wakeup Core Pack`（generated 2025-09-15）：`1) Schema 2) Principles 3) Memory 4) Reflex 5) Agent` | Dropbox `/MRL_FlowEditBridge_v0/MRL_FlowEditBridge_v0.2/MRL_Origin/FlowAgent_Wakeup_Core_v1.txt`（3452 bytes，另有 `_origin/`、`MRL_FlowEditBridge_v0 (2)/`、`Mrliou_agents (1)/Mrl_FlowAgent/` 多份同大小副本） |

## 2. 決定：SUPPLEMENT_EXISTING（不是 CREATE_NEW）

| 本次建立的東西 | 對應的既有節點 | 決定 | 說明 |
|---|---|---|---|
| `MRL_Wakeup_Seed_v1` 的五段順序 Schema → Principles → Memory → Reflex → Agent | 建構者 2025-09-15 的 `FlowAgent_Wakeup_Core_v1` 最小開機序 | **MAP_EXISTING** | 五段順序是建構者原有的，不是新發明。先前的 00_WAKE_ME_FIRST 沒有標出處，本檔補上。 |
| `MRL_Wakeup_Seed_v1` 整體 | Startup Wake（治理喚醒）＋ `MRL_WAKE_MANIFEST.yaml`（機器可讀喚醒，PR #141） | **SUPPLEMENT_EXISTING** | 上位錨點是 canonical_pointer ＋ WAKE_MANIFEST。Wakeup_Seed 補的是收斂紀錄列為 OPEN 的「DL580 current end-to-end runtime proof」：在 DL580 產生實機收據。它落在 8 段喚醒序的 `Verify → Backfill` 位置，**不取代**上位喚醒序。 |
| `04_Reflex/wake_verify.py` 收據 | `06_trace/wake_trace.schema.json`／`wake_verification_report.schema.json` | **SUPPLEMENT_EXISTING（待對齊）** | 收據欄位尚未對齊既有 schema。列為待辦，不自行改 schema。 |
| `MRL_WorldModel/MRL_FlowRhythm_v0` | 收斂紀錄 OPEN 項「Core Schema Convergence：Particle / FLTNZ / FLPKG / FlowSeed …」 | **SUPPLEMENT_EXISTING** | 它是 FLTNZ／FLPKG 種子節奏重播的一個可跑驗證，不是新的 Mother、不是新主線。 |
| `MRL_WorldModel/MRL_Dialect_v0` | 同上 ＋ ParticleIR_Engine（文字層） | **SUPPLEMENT_EXISTING** | 同上。 |

## 3. 讀取順序更正（給未來的 Claude）

1. 先讀上位錨點：Notion 收斂紀錄 `3bf8eeee-c5b5-8172-9984-f3bb1608522b` ＋ `MRL_STARTUP_WAKE.md`。
2. 再讀機器可讀喚醒：分支 `MRL_AI_SYSTEM/worldmodel-identity-wake-core-v1` 的 `00_rootlaw/canonical_pointer.yaml`、`00_rootlaw/MRL_WAKE_MANIFEST.yaml`，跑 `python 04_runtime/wake_loader.py --no-write-trace`。
3. 然後才是本目錄：依建構者 2025-09-15 的五段開機序讀 `01_Schema`…`05_Agent`，在 DL580 跑 `wake.ps1` 產生實機收據。

## 4. 本次實跑（沙盒）

- `wake_loader.py --no-write-trace`（分支 wake-core，head aa8bb83）：exit 0，manifest／canonical_pointer 存在、origin_signature 相符、5 個 required_sources 都在、wake_sequence 8 段、record_mode additive_only：**PASS（沙盒）— 當下狀態 2026-09-28**。
- 在 DL580 上：**待實機**。PR #141 尚未合併，本分支沒有 `wake_loader.py`；`wake_verify.py` 第 5 步會照實回報「待合併」。

## 5. 仍待辦（不自行宣告完成）

- PR #141 合併與 canonical promotion gate：建構者決定。
- 收據欄位對齊 `wake_trace.schema.json`：待做。
- Notion Origin Registry／Workspace Node Registry 回填本檔：待做（需在 Notion 寫入，未經建構者確認前不寫）。
- `FlowAgent_Wakeup_Core_v1.txt` 原檔位元組的 SHA-256：這次只讀到文字內容，未下載原位元組，雜湊待補。
