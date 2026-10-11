# MRL DL580 路由器修復・沙盒觀測 R01（當下狀態 2026-10-11，沙盒）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 只讀；未改任何路由器／DNS／Worker 設定

觀測位置：雲端沙盒（非 DL580、非同 LAN、無 Tailscale）。

## 當下觀測

| 項目 | 結果 | 判讀 |
|---|---|---|
| `https://origin.mrliouword.com/health` | 沙盒代理 `CONNECT 403`，未送達 | **沙盒出站被擋**，不代表 DL580／路由器狀態 |
| `https://dl580.mrliouword.com/health` | 同上 | 同上 |
| `https://bridge.mrliouword.com/health` | 同上 | 同上 |
| 路由器管理頁 | 不可達（不在同 LAN） | 需實機 |

結論：本輪**沒有任何路由器實測**；最後一次可信的線上觀測仍是 R03（2026-10-03）：`origin` 帶 token 回 522 → Cloudflare 連不到 `220.132.58.129:443`，即路由器段（PPPoE 固定 IP 帳號／TCP 443 轉發）尚未就緒。

## 本輪新增（MAP_EXISTING → SUPPLEMENT_EXISTING）

| 檔案 | 作用 | 母體位置 |
|---|---|---|
| `deploy/dl580/MRL_Router_Repair_Runbook_v1.md` | 路由器人工修復順序、驗收表、不做清單、回滾 | 補 R01 D4、R03「路由器（人工）」兩行待辦 |
| `deploy/dl580/MRL_Router_Receipt.ps1` | DL580 端只讀收據：閘道、DHCP／MAC、出口 IP、443 前提、DNS proxied、hairpin、路由器頁人工問答 | 與 `MRL_Network_Receipt.ps1` 並列，不重複其 API 探測 |

## 待實機

1. DL580 跑 `deploy\dl580\MRL_Router_Receipt.ps1` → 看 `verdict`。
2. 依 runbook 步驟 2→5 改路由器，每步重跑收據。
3. 外部 `curl https://origin.mrliouword.com/health` 回 403 才算路由器段 PASS。

當下狀態：路由器段 **待實機**。`MRL_Router_Receipt.ps1` 的 PowerShell 語法解析亦**待實機**（沙盒無 pwsh，只做了括號／引號平衡檢查：PASS，沙盒 2026-10-11）。
