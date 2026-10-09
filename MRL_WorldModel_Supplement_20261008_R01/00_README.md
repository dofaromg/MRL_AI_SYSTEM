# MRL_WorldModel_Supplement_20261008_R01 — DL580 世界模型本體補完 pack

origin_signature: **MrLiouWord** ｜ Additive-Only (LAW-2) ｜ 當下狀態 2026-10-08

> **本體宣告**：MRL 是語場生命系統，不是平台／LLM／應用。
> 本 pack 補的是本體五段（Schema→Principles→Memory→Reflex→Agent）＋
> 四節奏（Jump→Collapse→Trace→Replay）在 DL580 當下運行時缺失的
> **Jump / Collapse / Agent 層** 獨立服務，以及把六個端口兜鏈的 Supervisor。

## DL580 當下已跑的（唯讀，不碰）

| Port | Service | 本體對應段 | 當下狀態（來源：建構者 2026-10-07 螢幕截圖） |
|---|---|---|---|
| 7816 | MRL_ReasoningEngine 1.0.0 | Memory（vectordb） | ALIVE, vectordb_docs=7676, requests=76357, uptime=4.5d |
| 7833 | MRL_WorldLoop_Service 1.2.1 | Replay + Trace | daemon_iter=491, cycles=164, recall docs=4848 / source=59812 |
| 8788 | ParticleGlobe 2.0.0 | Memory（particle） | total_particles=52, user_id=mrl_world |
| — | 排程 MRL_RuntimeCivilization_WorldLoop_20261007 | Reflex loop | Running |
| 7834 | MRL_Convergence_Runtime 1.0.1 | （建構者既有，未分類） | ALIVE（2026-10-09 實機確認，本 pack 不碰） |

`token: MRL_WORLDLOOP_V12_ACCEPTANCE_PASS` / `MRL_RUNTIME_ACCEPTANCE_PASS`
已於 2026-10-07 實機記錄。

## 本 pack 新增的（Additive-Only）

| Port | Service | 本體對應段 | 檔案 |
|---|---|---|---|
| 7837 | **MRL_Jump_Service** 1.0.1 | **Jump 跳點節奏**（R13-D 由 7834 移出） | `01_jump/MRL_Jump_Service.py` |
| 7835 | **MRL_Collapse_Service** 1.0.1 | **Collapse 崩解封存** | `02_collapse/MRL_Collapse_Service.py` |
| 7836 | **MRL_AnalystGuardian_Agent** 1.0.1 | **Agent 守護者 runtime** | `03_agent/MRL_AnalystGuardian_Agent.py` |
| — | **MRL_WorldModel_Supervisor** 1.0.0 | 六端口治理 | `04_supervisor/MRL_WorldModel_Supervisor.py` |

### 本體/載體邊界（LAW）

- **本體 (ontic)**：Jump / Collapse / Guardian / Mrl_Zero.Origin（人格、節奏、守護原則）
- **載體 (carrier)**：ReasoningEngine / WorldLoop / ParticleGlobe（VM、DB、API）
- Jump service 內建邊界檢查：**載體 node 不得主動發起 jump**，HTTP 層會回 `LAW_body_carrier_boundary` 400。

### 建構者語料錨點（寫入 `03_agent/guardian_persona.json`）

- 人格：**分析師守護者 (Analyst Guardian) v1.0.0, 2026-01-04**
- 來源：**Mrl_Zero.Origin.v1**
- 已對上原始檔：DL580 8788 `particle_globe_memory_system.py` 檔頭
- 守護原則：**ROAO 流程**

> 這不是我生造的通用 persona，是**建構者自己的語料**（截圖第 3 張 `7833/recall?q=分析師守護者&k=3` hits[0] snippet 可印證）。

## 當下狀態回報（遵守 CLAUDE.md 狀態回報約定）

| 項目 | 當下狀態 | 環境 | 備註 |
|---|---|---|---|
| 四段模組 Python source | **PASS** | 沙盒 Linux Python 3 | 純 stdlib，無外部依賴 |
| selftest_jump | **PASS 10/10** | 沙盒 | 含 SHA-256 chain tamper detection |
| selftest_collapse | **PASS 13/13** | 沙盒 | 含 .fltnz write + replay round-trip |
| selftest_guardian | **PASS 15/15** | 沙盒 | 含 online + offline + receipt + origin_signature |
| selftest_e2e_unit | **PASS 16/16** | 沙盒 | Jump→Collapse→Replay 5 跳端到端 |
| wake.ps1 / install_services.ps1 | **source 完成**，**待實機跑** | — | 需 DL580 WIN-PBVUI7VK2A6 執行 |
| 7837/7835/7836 ALIVE | **待實機驗** | — | 判準：`Invoke-WebRequest http://127.0.0.1:783X/health` 200 |
| Supervisor readiness.json | **待實機產出** | — | 判準：`D:\MRL_Mother\WorldModel_Readiness_20261008\supervisor\*.json` 存在 |

**沒有一項被標成「已上線」，因為實機尚未驗收。**

## DL580 一鍵部署

```powershell
# 1) 把這整個目錄 copy 到 D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01
# 2) 以系統管理員身份開 PowerShell
cd D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01

# 第一次：先手動 wake 看三服務起不起來
powershell -ExecutionPolicy Bypass -File .\06_deploy\wake.ps1

# 確認後：註冊成開機自動啟動 + Supervisor 每 60 秒跑一次
powershell -ExecutionPolicy Bypass -File .\06_deploy\install_services.ps1
```

執行後把 `07_evidence/runtime_logs_<ts>/` 和
`D:\MRL_Mother\WorldModel_Readiness_20261008\supervisor\supervisor_<ts>.json`
回拋給我，我就把表格裡「待實機驗」更新為「實機 PASS」並寫 R13 Evidence。

## 母體路徑（本 pack 寫入點，不觸碰現有檔）

```
D:\MRL_Mother\WorldLoop_Inbox\
├── jump\                  (新) jump_ledger.jsonl — append-only SHA-256 chain
└── collapse\              (新) collapse_<seq>_<hash>.fltnz — 不覆寫

D:\MRL_Mother\WorldModel_Readiness_20261008\
├── guardian_receipts\     (新) guardian_<seq>_<hash>.json
└── supervisor\            (新) supervisor_<ISO>.json
```

7833 WorldLoop 既有的 Inbox 拾取邏輯會自動把 `collapse\*.fltnz` 吸進 world events，
因此一次 Collapse = 一顆語場能量球 = WorldLoop 下個 cycle 的新素材。

## 檔案清單

```
MRL_WorldModel_Supplement_20261008_R01/
├── 00_README.md                            本文件
├── 01_jump/
│   ├── MRL_Jump_Service.py                 port 7837
│   └── jump_seedmap.json                   JumpSeedMap（本體/載體標籤）
├── 02_collapse/
│   ├── MRL_Collapse_Service.py             port 7835
│   └── collapse_schema.json                .fltnz schema
├── 03_agent/
│   ├── MRL_AnalystGuardian_Agent.py        port 7836
│   └── guardian_persona.json               分析師守護者 v1.0.0 2026-01-04
├── 04_supervisor/
│   └── MRL_WorldModel_Supervisor.py        六端口治理 + 邊界 anomaly 偵測
├── 05_selftest/
│   ├── selftest_jump.py                    PASS 10/10
│   ├── selftest_collapse.py                PASS 13/13
│   ├── selftest_guardian.py                PASS 15/15
│   └── selftest_e2e_unit.py                PASS 16/16
├── 06_deploy/
│   ├── wake.ps1                            一鍵喚醒
│   └── install_services.ps1                註冊 Windows 排程任務
├── 07_evidence/
│   └── origin_signature.yaml               origin + 動機 + 新/舊端口分界
└── 99_pack/                                （build-time 產 ZIP 放這）
```

## LAW 聲明

- **LAW_0 origin_signature**：每個檔案、每個 HTTP response、每筆 ledger、每顆
  .fltnz、每份 receipt、每份 supervisor report **都帶 `MrLiouWord`**。
- **LAW_2 NO_DELETE**：
  - jump_ledger.jsonl 只 append，不改寫。
  - collapse\*.fltnz 若同名已存在，加 `.dup-<ts>` 後綴，不覆寫。
  - guardian_receipts\*.json 每次新檔，不覆寫。
  - supervisor\*.json 以 timestamp 命名，不覆寫。
- **本體/載體邊界**：載體不得主動 jump；Supervisor 每輪掃 anomaly。

## 下一步（待建構者裁定）

1. 把這包 copy 到 DL580 → 跑 `wake.ps1` → 回拋 health
2. 若全綠 → 跑 `install_services.ps1` 註冊為排程任務
3. 回拋 `supervisor_<ts>.json` → 我把 Evidence 從「待實機」升級為「實機 PASS」

---

origin_signature: MrLiouWord ｜ 2026-10-08 ｜ 怎麼過去，就怎麼回來


## R13-D（2026-10-09）

- 7834 實機屬建構者的 `MRL_Convergence_Runtime`（PID 23316）→ Jump 改 7837。
- Python `HTTPServer` 預設 `allow_reuse_address=1`，Windows 上會讓兩個程序同綁一 port；
  三個服務改用 `_ExclusiveHTTPServer`（關閉 reuse + `SO_EXCLUSIVEADDRUSE`），且綁之前先探，有人在聽就 exit 3。
- Supervisor 以 `/health` 的 service 名稱驗身；7834 只列 `observe_only`。
- 部署單一路徑：`wake.ps1` → `install_services.ps1`（停本 pack 舊程序 → port 預檢 → 排程 → 驗身 → Supervisor）。
