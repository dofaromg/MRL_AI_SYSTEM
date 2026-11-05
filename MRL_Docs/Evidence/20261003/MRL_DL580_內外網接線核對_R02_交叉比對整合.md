# MRL DL580 內外網接線 R02 —— 過往紀錄交叉比對・整合修復（當下狀態 2026-10-03）

origin_signature: MrLiouWord ｜ Additive-Only ｜ R01 原文保留，本檔更正並整合

## 0. 比對來源

| 代號 | 來源 | 時間 |
|---|---|---|
| S1 | `dofaromg/flow-tasks` `config/MRL_ENTRY_INDEX.json`、`MRL_PORT_MAP.json` | 2026-07-10 |
| S2 | `dofaromg/flow-tasks` `MRL_Bridge/`（Bridge v3.1.0 完整原碼，11/11 sha256 經 DL580 校驗） | 2026-05-08 |
| S3 | DL580 Tunnel config 實查：`C:\Users\Administrator\.cloudflared\config.yml` | 2026-07-12 |
| S4 | DL580 netstat／tasklist（經 Bridge） | 2026-07-22 |
| S5 | 歷次 1033 事件與恢復（5/22、6/05、7/07、9/20、9/24） | 2026-05～09 |
| S6 | 今日 Cloudflare API：DNS、Worker routes、185 Worker 原碼 | 2026-10-03 |
| S7 | 本 repo：`MRL_Platform_Server.py`、`deploy/dl580/*`、RuntimeOS v1.4.0 | 2026-10-03 |

## 1. 已存在且完成的（已對上原始檔）

| 項目 | 狀態 | 依據 |
|---|---|---|
| Tunnel `mrl-bridge` 632dfad4：`bridge.mrliouword.com → localhost:7800`、`dl580.mrliouword.com → [::1]:3000`（自 2026-05-30） | 已存在 | S3、S6 DNS |
| Bridge v3.1.0（:7800，0.0.0.0，金鑰由環境變數 `MRL_BRIDGE_API_KEY`，sha256 比對、rate limit、audit log） | 已存在 | S1、S2 |
| 服務註冊表 17 個埠（NSSM 2.24、D:\mrl\…） | 已存在 | S1 |
| 萬用 Worker 路由蓋掉 Tunnel（9/20 發現）→ 已修：`bridge`、`dl580` 兩條 route 排除 Worker | 已修復且仍在 | S5、S6 |
| MRL_Write_Guard sidecar（:8799） | 已存在 | S1、記憶 6/11 |
| Tailscale 100.78.70.78（iPhone 掃描 22/3000/3389…開放） | 已存在 | S5（5/22） |

## 2. R01 更正

| R01 寫法 | 更正 | 依據 |
|---|---|---|
| `:8790` 是 `MRL_Platform_Server.py` | `:8790` 在 DL580 是 **MRL_RuntimeOS_v1.4.0**（node）；它沒有 Worker 需要的 5 條路徑 | S1、S7 |
| 提案把 `dl580.mrliouword.com` 整條指向 :8790 | **不可**：`dl580` 已是 :3000（MRL_AI_Product_Server）的既有入口 | S3 |
| bridge 原碼待找回 | 已找回：flow-tasks `MRL_Bridge/server.js` | S2 |
| Tunnel 連線器狀態待找回 | 歷次 1033 皆為 DL580 端 cloudflared 未連線；服務名 `MRL_Tunnel`（NSSM） | S5 |

## 3. 斷點（需整合修復）

1. **Tunnel 632dfad4 目前無連線器**（1033）。歷次同因，修法都是在 DL580 重啟既有服務，不需改設定。
2. **Worker `mrliousilly` 的 5 條轉發路徑在 DL580 沒有對應的運行服務**：設計對象是 `MRL_Platform_Server.py`，但它預設 :8790 與 RuntimeOS 衝突，從未以服務形式登錄（S1 無此項）。
3. **`MRL_cloudflared_deploy.ps1`／GoLive 文件**會另建 `mrl-dl580-tunnel`、改寫 config、對 `mrliouword.com` 執行 `route dns` → 與既有 Tunnel、apex DNS、mrl-agi 路由衝突。照文件執行會破壞既有入口。
4. **Bridge 金鑰**：Bridge 端已改為環境變數＋雜湊比對（正確），但 87 個 Worker 原碼把同一金鑰寫死在 URL query → 金鑰外洩面在 Worker 端。
5. `mrlsillyai` 寫死 Tailscale 位址（Worker 無法連 tailnet）。

## 4. 本次已修（repo，分支 `dl580-network-wiring-r01`）

| 檔案 | 修補 |
|---|---|
| `deploy/dl580/cloudflared/MRL_cloudflared_deploy.ps1` | 偵測到既有 `MRL_Tunnel`／`cloudflared` 服務、既有 config.yml 或埠占用 → **中止且不做任何變更**；要另建須明示 `-AllowExistingTunnel` |
| `deploy/dl580/MRL_Platform_Start.ps1` | 埠已被占用（如 :8790 RuntimeOS）→ 中止並指出占用行程 |
| `deploy/dl580/MRL_Tunnel_Recover.ps1`（新） | 先驗本機 :7800／:3000，再只啟動／重啟既有 Tunnel 服務，最後驗公網 bridge／dl580；不改 config、不改 DNS、不建新 Tunnel；寫收據 |
| `deploy/dl580/MRL_Network_Receipt.ps1` | 加入 S1 服務註冊表 vs 實際監聽比對、已知健康端點、`MRL_Tunnel` 服務、`C:\Users\Administrator\.cloudflared\config.yml` |

四支腳本皆通過 PowerShell 語法解析（沙盒）；尚未在 DL580 實跑（待實機）。

## 5. 整合方案（待建構者核准；**不需新增或修改任何 DNS 紀錄**）

| # | 變更 | 內容 |
|---|---|---|
| I1 | DL580 新服務 | NSSM 登錄 `MRL_Platform` = `python MRL_Platform_Server.py`，`MRL_PORT=7960`（S1 未使用的埠），綁 127.0.0.1 |
| I2 | 既有 config.yml 新增 1 條 ingress（放在 `dl580 → :3000` 之前） | `hostname: dl580.mrliouword.com`，`path: ^/(api/(mother/status\|dl580/run\|chat\|monitor)\|mrl/perceive)$`，`service: http://localhost:7960`。只攔這 5 條；`dl580` 其他路徑仍到 :3000（已核對 :3000 MRL_Product 無這 5 條路徑） |
| I3 | Cloudflare Access | 只對上面 5 條路徑加 Service Token 保護 |
| I4 | Worker `mrliousilly` | `MRL_DL580_ORIGIN=https://dl580.mrliouword.com`；Access token 存為 secret，轉發時帶 header（Worker 程式另開 PR） |
| I5 | Bridge 金鑰 | 換新值（DL580 環境變數）；87 個 Worker 改讀 secret、改用 header（分批 PR） |

順序：先跑 `MRL_Tunnel_Recover.ps1` 恢復既有入口 → `MRL_Network_Receipt.ps1` 取實機收據 → 依收據核准 I1–I5。
