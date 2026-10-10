# MRL_Adapters/MetaEnv — MetaEnv Control API 規格收錄

origin_signature: MrLiouWord
law: Additive-Only（不刪除、不覆蓋、給位置、待起動）

| 檔 | 內容 | 狀態 | 來源/誠實標註 |
|---|---|---|---|
| `MRL_MetaEnv_Control_API_v1_原件.yaml` | Mr.liou MetaEnv Control API v1.0.0 OpenAPI 3.1 規格**原件**（上傳檔名 `MR.LIOU_AGI______.txt`） | 保存原件 | 使用者上傳 2026-07-08；**原件第 110 行缺換行**（`/api/v1/snapshot/create` 黏於 `AttestCheckResponse` 之後），YAML 解析失敗，依 additive 保留不改 |
| `MRL_MetaEnv_Control_API_v1.yaml` | 同上之**修復版**（僅補回第 110 行換行，其餘一字未動）；9 端點：env spawn/health、policy apply/attest、snapshot create、channel map、reverse miner、guard lockdown、backtrace report | **待起動**（規格已可解析；伺服端未實跑） | 修復於沙盒 2026-07-08，`yaml.safe_load` 驗證通過（9 paths） |

## 對應母體構件

- 組裝計畫（`docs/MRL_ASI_Assembly_Plan_20260316_v2_1.md`）Notion 索引「MetaAPI 規格 — 9端點 OpenAPI」即本規格。
- 雲端對應 Worker：`metaenv-ctrl`（組裝計畫標 ✅ 200，MetaEnv 9端點）。
- 規格 servers 指向 `https://metaenv.local` / `http://localhost:8000`（內網/開發），
  與 DL580 現有 8000 埠服務（`mrl_asi_particle_engine_v2.py` :8000）是否同宿主待確認。

> 起動條件：對 `metaenv-ctrl`（或 DL580 本地控制器）逐端點實測（先 `GET /api/v1/env/health`），
> 實跑通過方可標 PASS（實機/沙盒註明）。
