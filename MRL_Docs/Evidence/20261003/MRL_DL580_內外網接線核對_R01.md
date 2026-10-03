# MRL DL580 內網／公網接線核對 R01（當下狀態 2026-10-03 16:40 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 只讀核對，未改任何 DNS／路由／Worker 變數

觀測位置：雲端沙盒（**非** DL580、**非** 同 LAN、**無** Tailscale）。本機／LAN／Tailscale／路由器 WAN 四段須在 DL580 上執行 `deploy/dl580/MRL_Network_Receipt.ps1` 取得實機收據。單一路徑失敗不判定 DL580 離線。

## 1. 實際拓撲（依線上設定與 repo 原檔）

```
                       Cloudflare（zone mrliouword.com）
  ┌──────────────────────────────────────────────────────────────────────┐
  │ Worker routes                                                        │
  │   *.mrliouword.com/*  → mrl-agi（萬用路由，蓋住 app/flow/runtime/shell…）│
  │   bridge.mrliouword.com/*  → (無 Worker，例外放行)                    │
  │   dl580.mrliouword.com/*   → (無 Worker，例外放行)                    │
  │   careos.mrliouword.com/*  → careos-proxy → 再打 careos.mrliouword.com │
  │ DNS（proxied）                                                        │
  │   bridge / dl580 / mrliouhan.ai → Tunnel 632dfad4…  ← 現況 1033       │
  │   @ / www / app / careos / flow / runtime → Tunnel 5b9ff370…          │
  │   shell → Tunnel 77837636…                                            │
  │ Worker mrliousilly（正式 ad786326）: MRL_DL580_ORIGIN 未設 → 轉發路由 503 │
  │ 87 個 particle-* Worker → https://bridge.mrliouword.com/MRL_pg、/MRL_run │
  │ mrlsillyai → http://100.78.70.78:3001 / :8000（Tailscale 位址）        │
  └──────────────────────────────────────────────────────────────────────┘
                 │ cloudflared（outbound，免開公網埠）
  HiNet PPPoE 固定 IP 220.132.58.129（2026-05-23 配發）── 路由器 ── LAN
                                                         └─ DL580（歷史 192.168.0.162）
                                                              ├─ MRL_Platform_Server.py :8790（0.0.0.0，無認證）
                                                              ├─ bridge 服務（/MRL_pg、/MRL_run）埠待找回（文件提 7800）
                                                              ├─ Tailscale 100.78.70.78（:3001、:8000 待驗）
                                                              └─ cloudflared（D:\cloudflared）
```

## 2. 各段測試回執

| 段 | 測試 | 結果（當下） | 判讀 |
|---|---|---|---|
| 公網・bridge Tunnel | `https://bridge.mrliouword.com/` | 530 `error code: 1033` | Tunnel 632dfad4 無連線器在線；**不等於** DL580 離線 |
| 公網・dl580 Tunnel | `https://dl580.mrliouword.com/` | 530 `1033` | 同一條 Tunnel |
| 公網・careos | `https://careos.mrliouword.com/` | 530 | 經 careos-proxy；上游 Tunnel 5b9ff370 疑似不在線 |
| 公網・@／www／app／flow／runtime／shell／mrliouhan.ai | GET / | 200 | **由 Worker mrl-agi 萬用路由回應**，不是 DL580；不能拿來證明 Tunnel 通 |
| 公網・固定 IP 直連 | `220.132.58.129` :80/443/8443/7700/8000/8080 | 沙盒端 TCP 建立後 0 bytes／逾時 | 沙盒出口不可靠，**未判定**；依規則也不把固定 IP 當 API URL |
| Worker 轉發 | `mrliousilly` `/api/chat` | 503（MRL_DL580_ORIGIN 未設） | 預期 |
| Tunnel 連線器狀態（API） | `cfd_tunnel` | token 無 Tunnel 讀權限 → 待找回 | 需加 `Account › Cloudflare Tunnel › Read` |
| 本機 127.0.0.1:8790 | — | 待實機 | 收據腳本 |
| LAN 192.168.0.162:8790 | — | 待實機 | 收據腳本 |
| Tailscale 100.78.70.78 | — | 待實機（沙盒無 Tailscale） | 收據腳本 |
| 路由器 WAN = 220.132.58.129 | — | 待實機（看路由器 WAN 頁；腳本另記 DL580 出口 IP） | 收據腳本 |

## 3. API 對齊（Worker 需要什麼 vs 誰提供）

| Worker `mrliousilly` 轉發路徑 | `MRL_Platform_Server.py`（:8790） | bridge 服務（/MRL_pg） |
|---|---|---|
| GET /api/mother/status | ✅ | 未見 |
| POST /api/dl580/run | ✅ | 未見 |
| POST /api/chat | ✅ | 未見 |
| GET /api/monitor | ✅ | 未見 |
| POST /mrl/perceive | ✅ | 未見 |
| （particle-* 用）/MRL_pg、/MRL_run | ✗ | ✅（原碼不在 repo → 待找回） |

結論：**`MRL_DL580_ORIGIN` 不能直接設成 `https://bridge.mrliouword.com`**，除非實機證實 bridge 那條 ingress 指到 :8790 平台伺服器（或 bridge 服務也實作上面 5 條）。repo 範本 `deploy/dl580/cloudflared/config.yml.template` 寫的是 `bridge.mrliouhan.ai → localhost:8790`，與線上 `bridge.mrliouword.com` 吃 `/MRL_pg` 的現況不一致 → 待實機 config.yml 核對。

## 4. 安全觀察

- `MRL_Platform_Server.py` 綁 `0.0.0.0`、**無認證**：LAN／Tailscale 內任何主機都能呼叫 `/api/dl580/run`、`/api/chat`。公網只能經 Tunnel＋認證開放，**不可**在路由器對 220.132.58.129 做埠轉發。
- 87 個 Worker 原碼內寫死 bridge 固定金鑰並以 URL 帶 SQL（`/MRL_pg?key=…&sql=…`）；金鑰會進 Cloudflare／cloudflared 存取紀錄。建議換金鑰、改 Worker secret＋header。
- `mrlsillyai` 指向 Tailscale 位址 100.78.70.78：Cloudflare Worker 無法直連 Tailscale 網段，此路徑從邊緣必然不通（設計問題，非 DL580 離線）。

## 5. 設定差異（提案，**未套用**，待建構者核准）

| # | 位置 | 現況 | 提案 |
|---|---|---|---|
| D1 | DL580 cloudflared `config.yml`（Tunnel 632dfad4） | 待實機讀取 | 保留既有 `bridge.mrliouword.com`（/MRL_pg）不動；**新增**一條 hostname 指 `http://localhost:8790`（建議用既有 DNS `dl580.mrliouword.com`，它已指同一 Tunnel 且已排除 mrl-agi 路由 → 不需改 DNS） |
| D2 | Cloudflare Access | 無 | 對 `dl580.mrliouword.com` 加 Access 應用＋Service Token，只允許 Worker 帶 token 進入 |
| D3 | Worker `mrliousilly` | `MRL_DL580_ORIGIN` 未設 | 設 `MRL_DL580_ORIGIN=https://dl580.mrliouword.com`；Access service token 以 **secret** 存放，轉發時加 `CF-Access-Client-Id/Secret` header（Worker 需一小段程式，另開 PR） |
| D4 | 路由器 | 待實機 | DL580 做 DHCP 保留（綁 MAC）或確認靜態位址在 DHCP 範圍外；**不新增**任何對外埠轉發 |
| D5 | Cloudflare API token | 無 Tunnel 讀權限 | 加 `Account › Cloudflare Tunnel › Read`，以便從外部讀連線器狀態 |
| D6 | bridge 金鑰 | 固定字串寫在 87 個 Worker | 換新金鑰；Worker 改讀 secret（分批，另開 PR） |

DNS 與既有路由：上述 D1–D3 **不需要新增或修改任何 DNS 紀錄**。

## 6. 實機下一步

在 DL580（系統管理員 PowerShell）：

```powershell
cd <MRL_HOME>
powershell -ExecutionPolicy Bypass -File deploy\dl580\MRL_Network_Receipt.ps1
```

收據寫到 `D:\MRL_runtime\receipts\MRL_Network_Receipt_*.json`（已遮罩金鑰），內容：DL580 出口 IP 對 220.132.58.129、LAN 位址與 DHCP／靜態、ARP、全部監聽埠與行程、本機／LAN／Tailscale／Tunnel 各段對 Worker 所需 5 條 API 的實測、cloudflared 服務狀態與 ingress。腳本只讀，不改設定；`/api/dl580/run` 不主動觸發。
