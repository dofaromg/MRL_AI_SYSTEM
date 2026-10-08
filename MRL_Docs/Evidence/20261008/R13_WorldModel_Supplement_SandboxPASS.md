# R13 · MRL 世界模型本體補完 pack（當下狀態 2026-10-08 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only (LAW-2) ｜ 建構者 2026-10-08 原話：
> 「夥伴把你說還沒有做的先完成，主線任務依然不變，完成 MRL 世界模型本地伺服器 dl580 內運行，把缺少的模組程式都補上。」

## 本輪做了什麼

走 **SUPPLEMENT_EXISTING** —— 不覆蓋 DL580 當下已跑的 7816/7833/8788，
補本體五段 + 四節奏缺的三個 service 和一個 supervisor。

### 建構者 2026-10-07 螢幕截圖 → DL580 當下運行事實（R13 依據）

| Port | Service | Version | 實機狀態（截圖） |
|---|---|---|---|
| 7816 | MRL_ReasoningEngine | 1.0.0 | ALIVE, vectordb_docs=7676, chains=4, requests=76,357, uptime=395,894s (≈4.5 天) |
| 7833 | MRL_WorldLoop_Service | 1.2.1 | cycles=164, daemon_iteration=491, border=0, errors=0, recall docs entity=4,848 / source=59,812, last_seq=9,762, anchor_match=true, mirror→7816 sent=7,649 / →8788 sent=52 |
| 8788 | ParticleGlobe | 2.0.0 | total_particles=52, top_tags=[["memory",52],["mrl_world",52],["MrLiouWord",52],["world_memory",52],["world模型",3]] |
| — | 排程任務 | — | `MRL_RuntimeCivilization_WorldLoop_20261007` = Running |
| — | token | — | `MRL_WORLDLOOP_V12_ACCEPTANCE_PASS` / `MRL_RUNTIME_ACCEPTANCE_PASS` |
| — | Inference_API | — | `python D:\mrl\inference\MRL_Inference_API.worldrecall_v4.py` |

### 建構者語料錨點

截圖第 3 張 `7833/recall?q=分析師守護者&k=3` 命中 2 筆：
- `MRL_WorldModel_Build_20261007_c.md` seq=9728 score=46.95
- `db3563b7-_____.pdf.extract.txt` seq=9707 score=41.48

其中 snippet 明確寫：
> 分析師守護者 (Analyst Guardian) v1.0.0, 2026-01-04, 來源 Mrl_Zero.Origin.v1；
> ROAO 流程、守護原則｜人格定義（本體：人格生成）。
> 已對上原始檔: DL580 8788 ParticleGlobe (particle_globe_memory_system.py 檔頭「Analyst Guardian - 分析師守護者」, 同為 2026-01-04)

**→ 這是建構者自己的 corpus，不是我生造的通用 persona。本 pack 的 Guardian 以此為 anchor。**

### 比對本體預期：缺的 3+1

| 本體段 | 四節奏 | DL580 現有 | 缺 |
|---|---|---|---|
| Memory | — | 7816 vectordb + 8788 particle | ✓ |
| Reflex | Trace / Replay | 7833 WorldLoop /recall + self_verify | ✓ |
| — | **Jump** | ❌ 無獨立 service | **補 7834** |
| — | **Collapse** | ❌ 無獨立 service | **補 7835** |
| Agent | — | ❌ 分析師守護者沒 runtime | **補 7836** |
| 治理 | — | ❌ 無跨端口 supervisor | **補 Supervisor** |

## 本 pack 補的（Additive-Only）

```
/home/claude/mrl_ai_system/MRL_WorldModel_Supplement_20261008_R01/
├── 00_README.md
├── 01_jump/
│   ├── MRL_Jump_Service.py              port 7834 — JumpSeedMap + ledger (append-only, SHA-256 chain)
│   └── jump_seedmap.json                本體/載體標籤 + 5 條預設 jumps
├── 02_collapse/
│   ├── MRL_Collapse_Service.py          port 7835 — Jump trace window → .fltnz 封存 → replay
│   └── collapse_schema.json             .fltnz schema (FLTNZ-1 magic + base64/gzip)
├── 03_agent/
│   ├── MRL_AnalystGuardian_Agent.py     port 7836 — ROAO 守護原則，跨查 7816/7833/8788
│   └── guardian_persona.json            分析師守護者 v1.0.0 2026-01-04（建構者語料錨點）
├── 04_supervisor/
│   └── MRL_WorldModel_Supervisor.py     6 端口健康 + 本體/載體邊界 anomaly 偵測
├── 05_selftest/
│   ├── selftest_jump.py                 PASS 10/10
│   ├── selftest_collapse.py             PASS 13/13
│   ├── selftest_guardian.py             PASS 15/15
│   └── selftest_e2e_unit.py             PASS 16/16（Jump→Collapse→Replay 5 跳端到端）
├── 06_deploy/
│   ├── wake.ps1                         DL580 一鍵喚醒三服務 + Supervisor --once
│   └── install_services.ps1             註冊成 Windows ScheduledTask（開機自動）
├── 07_evidence/
│   ├── origin_signature.yaml            LAW-0 + LAW-2 + 動機 + 新/舊端口分界
│   └── SHA256SUMS                       15 檔 + 1 ZIP 的 SHA-256
└── 99_pack/
    └── MRL_WorldModel_Supplement_20261008_R01.zip  (34K)
```

## 當下狀態回報（遵守 CLAUDE.md 狀態回報約定）

| 項目 | 當下狀態 | 環境 | 時間 |
|---|---|---|---|
| 4 個 Python module source | **PASS** | 沙盒 Linux Python 3.13 | 2026-10-08 |
| selftest_jump | **PASS 10/10** | 沙盒 unit | 含 SHA-256 chain tamper detection |
| selftest_collapse | **PASS 13/13** | 沙盒 unit | 含 .fltnz round-trip replay |
| selftest_guardian | **PASS 15/15** | 沙盒 unit | 含 online + offline + receipt + origin_signature |
| selftest_e2e_unit | **PASS 16/16** | 沙盒 unit | Jump→Collapse→Replay 5 跳 |
| wake.ps1 / install_services.ps1 | **source 完成** | 沙盒 | PowerShell 5.1 相容 |
| 7834/7835/7836 ALIVE | **待實機驗** | — | 判準：DL580 Invoke-WebRequest `/health` 200 |
| Supervisor readiness.json | **待實機產出** | — | 判準：`D:\MRL_Mother\WorldModel_Readiness_20261008\supervisor\*.json` |
| Jump→Collapse→Replay 實機鏈 | **待實機驗** | — | 判準：7834 /jump → 7835 /collapse → 7835 /collapse/{id}/replay 全 200 |
| Guardian 實機命中建構者語料 | **待實機驗** | — | 判準：7836 /guardian/consult?query=分析師守護者 回應含 hits ≥1 且附 origin_signature |

**沒有一項被標成「DL580 已上線」。**

## SHA-256 核對清單（LAW-2 不可改寫證據）

見 `07_evidence/SHA256SUMS`，含 15 檔 + 1 ZIP。

## 重要邊界（LAW）

1. **LAW_0 origin_signature**：所有 HTTP response header `X-MRL-Origin-Signature: MrLiouWord`；所有磁碟寫出的 ledger / fltnz / receipt / supervisor report 都含 `origin_signature: MrLiouWord`。
2. **LAW_2 NO_DELETE**：
   - `jump_ledger.jsonl` 只 append，SHA-256 chain
   - `collapse_*.fltnz` 同名存在 → 加 `.dup-<ts>` 後綴
   - `guardian_*.json`、`supervisor_*.json` 以 seq / timestamp 命名
3. **本體/載體邊界**：Jump service HTTP 層會擋載體 node（7816/7833/8788）主動發起 jump，回 400 `LAW_body_carrier_boundary`；Supervisor 每輪掃 ledger 的 actor 欄位。

## 不處理的（實機未驗，禁止標 PASS）

- Jump / Collapse / Guardian / Supervisor **在 DL580 上運行與否**
- Jump → Collapse → Replay 的 **實機端對端串連**
- 7836 /guardian/consult 的 **實機語料命中率**
- 新增 `D:\MRL_Mother\WorldLoop_Inbox\collapse\*.fltnz` 被 7833 WorldLoop **自動吸收**

這些都要等建構者在 DL580 跑 `wake.ps1` 回拋 output 和 supervisor_<ts>.json 後，
我才會更新 Evidence 的狀態為「實機 PASS」。

## 待建構者裁定

1. 把 ZIP 解到 `D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01` 跑 `wake.ps1`
2. 回拋 `07_evidence/runtime_logs_<ts>/` 和 `D:\MRL_Mother\WorldModel_Readiness_20261008\supervisor\supervisor_<ts>.json`
3. 若全綠 → 跑 `install_services.ps1` 掛成 ScheduledTask
4. 建構者 OK 的話，我會寫 R13-A「實機 PASS」Evidence 覆上

origin_signature: MrLiouWord ｜ 2026-10-08 ｜ 怎麼過去，就怎麼回來
