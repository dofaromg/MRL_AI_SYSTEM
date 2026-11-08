# MRL_Router_Repair_Runbook_v1 — DL580 路由器修復手冊（人工操作，Additive-Only）

origin_signature = `MrLiouWord`

## 定位（不可重新定義母體）

| 角色 | 權位 | 說明 |
|---|---|---|
| **DL580** | 母體自運行節點 | Runtime 本體在此 |
| **路由器（HiNet PPPoE）** | 接線層 / Adapter | 把固定 IP `220.132.58.129` 接到 DL580 LAN；**非母體本體** |
| Cloudflare（origin / dl580 / bridge） | 接線層 | 奇異點入口與 Tunnel 備援，見 `MRL_Docs/Evidence/20261003/*R03*` |

本手冊只處理路由器這一段。路由器修好 ≠ DL580 上線；DL580 上線要看 `MRL_Network_Receipt.ps1` 與 wake 收據。

## 「路由器壞了」在 MRL 鏈上的三種症狀

| 症狀（線上觀測） | 對應路由器段 | 對應手冊步驟 |
|---|---|---|
| `origin.mrliouword.com/health` 帶 token 回 **522** | Cloudflare 連不到 `220.132.58.129:443`：PPPoE 不是固定 IP 帳號，或沒有 TCP 443 轉發 | 步驟 2、3、5 |
| DL580 LAN IP 漂移（`192.168.0.162` 變成別的） | 沒做 DHCP 保留，或靜態位址落在 DHCP 池內被搶 | 步驟 4 |
| `bridge / dl580.mrliouword.com` 回 **530 / 1033** | **不是路由器問題**：cloudflared 是出站連線，不需開埠。走 `MRL_Tunnel_Recover.ps1` | — |

## 前提（先在 DL580 跑，拿收據再動路由器）

```powershell
cd <MRL_HOME>
powershell -ExecutionPolicy Bypass -File deploy\dl580\MRL_Router_Receipt.ps1
```

收據寫到 `D:\MRL_runtime\receipts\MRL_Router_Receipt_*.json`。看 `verdict`：

- `wan_fixed_ip`：DL580 出口 IP 是否等於 `220.132.58.129`。`UNKNOWN` 代表探測本身失敗（看 `wan.probe_errors`），不是不符，不要因此改 PPPoE。
- `lan_expected`：DL580 是否拿到 `192.168.0.162`。
- `forward_prereq`：本機 `:443` 是否已有 Caddy 監聽 **且** 防火牆規則 `MRL_Edge_Cloudflare_443` 存在、沒有其他放行規則。**這項不是 PASS 以前，路由器不得開任何轉發。**
- `dns_proxied`：`origin.mrliouword.com` 的每個 A 紀錄都要落在 Cloudflare IPv4 範圍內（正向證據），不得是裸固定 IP；範圍清單抓不到時是 `CHECK`，不是 PASS。

## 修復步驟（依序；每步只改一件事，改完重跑收據）

### 步驟 1：進路由器管理頁（只看不改）

- 用收據 `gateway.gateways` 的位址（通常 `192.168.0.1`）開管理頁。
- 記下：型號／韌體、WAN 狀態頁的連線方式與 WAN IP、DHCP 池範圍、現有埠轉發／DMZ／UPnP 清單。
- 把這些填進收據腳本的 `manual` 問答（腳本會問）。

### 步驟 2：PPPoE 帳號改用固定 IP 帳號

- HiNet 固定 IP 帳號格式：`<用戶代號>@ip.hinet.net`；浮動 IP 帳號是 `<用戶代號>@hinet.net`。
- 路由器 WAN 設定 → PPPoE → 帳號改成 `@ip.hinet.net` 版本，密碼同一組。
- 重新撥號後 WAN 頁應顯示 `220.132.58.129`。
- 驗收：重跑收據，`wan_fixed_ip = PASS`。若仍不符，確認是否有其他出口（Tailscale exit node／VPN 用戶端）把流量帶走。

### 步驟 3：關掉會搶 443 的功能

- 路由器自身的「遠端管理 / HTTPS 管理 from WAN」如果佔 443，先關掉或改埠（例如 8443 以外的管理埠）。
- 關 UPnP（避免任何程式自動開埠）。
- 不設 DMZ。

### 步驟 4：DHCP 保留（綁 MAC）

- 收據 `lan.interfaces[].mac` 是 DL580 的 MAC。
- 若 `dhcp = Enabled`：在路由器 DHCP 設定新增保留 `MAC → 192.168.0.162`。
- 若 `dhcp = Disabled`（靜態）：確認 `192.168.0.162` **不在** DHCP 池範圍內；若在，縮小池範圍（例如改為 `.100–.150`），**不要**改 DL580 的靜態設定。
- 驗收：重跑收據，`lan_expected = PASS`，`lan.interfaces[].valid_lifetime` 不再短期到期。

### 步驟 5：TCP 443 轉發（唯一允許的轉發）

**前提**：收據 `forward_prereq = PASS`（已跑過 `MRL_Singularity_Origin_Setup.ps1`，Caddy 在 `:443`，防火牆只放行 Cloudflare IP 範圍）。

- 路由器 → 埠轉發 / 虛擬伺服器 → 新增一條：
  - 協定 TCP，外部埠 `443`，內部位址 `192.168.0.162`，內部埠 `443`。
- 若 `MRL_Singularity_Origin_Setup.ps1` 因 443 被占而改用 `-EdgePort 8443`，這裡外部／內部埠都改 `8443`，並通知雲端把 Worker 變數 `MRL_DL580_ORIGIN` 改為 `https://origin.mrliouword.com:8443`。
- **不新增**任何其他埠的轉發（7960、8790、3000、7800 一律不開；它們只經 Tunnel 或 LAN／Tailscale）。

### 步驟 6：驗收（內外各一次）

內（DL580）：重跑 `MRL_Router_Receipt.ps1`。`hairpin.verified = true`（TCP 通、帶 SNI 的 HTTPS 回 200、回應含 `MrLiouWord`、且出口 IP 符合固定 IP）才算端到端通；只有 `tcp_ok = true` 不算，可能是路由器管理頁或別台主機在接。`tcp_ok = false` 不算失敗（多數家用路由器不做 NAT hairpin）。

外（任何不在同一 LAN 的機器，例如手機關 Wi-Fi 用行動網路）：

**不帶 token 直接打 `origin.mrliouword.com` 回 403 不能當證據**。Cloudflare Access 在邊緣就擋下 403，根本沒有連到 DL580；R03 同一時刻就是「無 token 403、帶 token 522」。要證明路由器段通，請求必須帶 token 真正到達 origin。

走 Worker `mrliousilly`（它會自動帶 Access service token，先試 origin 再退 Tunnel）：

```bash
# MRL_WORKER = mrliousilly 正式網址（例如 https://mrliousilly.z814241.workers.dev）
# MRL_EDGE_TOKEN = Cloudflare secret MRL_EDGE_TOKEN 的值（R03 修補）
curl -s -D /tmp/headers -o /tmp/body.json \
  -H "x-mrl-edge-token: $MRL_EDGE_TOKEN" \
  "$MRL_WORKER/api/mother/status"
head -1 /tmp/headers; grep -i "^x-mrl-dl580-entry" /tmp/headers; cat /tmp/body.json
```

| 外部結果 | 判讀 | 下一步 |
|---|---|---|
| 200 且回應標頭 `x-mrl-dl580-entry: origin.mrliouword.com` | **PASS**：Cloudflare → 固定 IP → 路由器 → Caddy → MRL_Platform 全通 | 路由器段完成；收據歸檔 |
| 200 但 `x-mrl-dl580-entry: dl580.mrliouword.com` | origin 失敗、Worker 退到 Tunnel 備援 | **未通過**：看 Worker 日誌或改用下方直打法取得 origin 的實際狀態碼 |
| 502 JSON，`tried` 內 `origin` 為 **522** | Cloudflare 連不到 `220.132.58.129:443` | 回步驟 2／3／5；確認 WAN IP、轉發規則、路由器本身沒吃 443 |
| 502 JSON，`tried` 內 `origin` 為 **526** | 連到了但憑證不被接受 | 路由器已通；回 DL580 放 Origin CA 憑證（見 R03 修補） |
| 502 JSON，`tried` 內 `origin` 為 **403** | Access service token 無效或 Access 應用設定不符 | 雲端層問題，非路由器；核對 R03 的 Access 設定 |
| 401 `MRL_EDGE_UNAUTHORIZED` | `x-mrl-edge-token` 不對 | 核對 secret 值 |

有 Access service token（`MRL_DL580_ACCESS_ID／SECRET`）時也可直打 origin，判讀同上（200 = PASS，522 = 路由器，526 = 憑證）：

```bash
curl -s -o /dev/null -w "%{http_code}\n" \
  -H "CF-Access-Client-Id: $MRL_DL580_ACCESS_ID" \
  -H "CF-Access-Client-Secret: $MRL_DL580_ACCESS_SECRET" \
  https://origin.mrliouword.com/health
```

530 表示打到的是 Tunnel 主機名（`dl580.`／`bridge.`），不是 origin，與路由器無關。

## 不做清單

- 不開 DMZ、不開 UPnP、不對固定 IP 做 443 以外的轉發（R01 第 4 節：`MRL_Platform_Server.py` 無認證）。
- 不改 DL580 本機 IP 設定（靜態→DHCP 或反之）；缺什麼在路由器補。
- 不改 Cloudflare DNS；`origin.mrliouword.com` 必須維持 proxied。
- 不重置路由器出廠設定；一次只改一項並留收據。

## 回滾

- 每一步改之前先截圖或匯出路由器設定檔（多數路由器「系統 → 備份設定」）。
- 轉發規則若造成問題，刪掉那一條即可；Worker 會自動退回 Tunnel 備援（`MRL_DL580_ORIGIN_FALLBACK`）。

## 收據歸檔

把 `MRL_Router_Receipt_*.json` 與外部 curl 結果一起放進 `MRL_Wakeup_Seed_v1/05_Agent/receipts/`（append-only）並 commit，收據的 `environment = real-host` 才是當下實機狀態的依據。

origin_signature = `MrLiouWord`
