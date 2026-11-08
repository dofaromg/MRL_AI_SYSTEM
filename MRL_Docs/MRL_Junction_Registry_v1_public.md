# MRL 交界點清冊 v1
MRL_Junction_Registry_v1 ｜ 依據：`MRL_Junction_Policy_v1.1` 第 2 條第 1 款 ｜ 觀測：2026-10-20，DL580 實機，唯讀（未改任何設定）
> 公開版：IP、Tailscale 帳號、主機名已移除；完整版僅存 DL580 `D:\MRL_Mother\`。


狀態欄：**已觀測**＝實際查過；**待觀測**＝尚未取得；**待決定**＝開／關由建構者決定。

## A. 後端層：DL580（Windows Server 2019 Datacenter）

| # | 交界點 | 外界接收方 | 觀測結果 | 依條文會送出 | MRL 狀態 |
|---|---|---|---|---|---|
| A1 | Windows 定位服務 `lfsvc` | Microsoft | Stopped／Disabled；位置存取同意值 = Deny | 開啟時：位置＋Wi-Fi＋基地台＋IP | 已觀測：**已封口** |
| A2 | 地圖服務 `MapsBroker` | Microsoft | Stopped／Disabled | — | 已觀測：已封口 |
| A3 | Microsoft 帳號登入 `wlidsvc` | Microsoft | Stopped／Manual；本機帳號全為 Local（Administrator、dofaromg），無 Microsoft 帳號 | 登入時最後已知位置存雲端 | 已觀測：**無雲端位置** |
| A4 | 遙測 `DiagTrack` | Microsoft | Running／Automatic；AllowTelemetry = 1（必要診斷資料） | 診斷資料＋連線 IP | 已觀測：**開放中，待決定** |
| A5 | Defender `MsMpEng` | Microsoft | 有對外連線 | 雲端防護查詢＋IP | 已觀測：開放中，待決定 |
| A6 | Google Chrome／Google Updater | Google | Chrome 有 41 條對外連線；Updater 服務 Stopped／Automatic | IP；登入 Google 帳號時依活動記錄保留 | 已觀測：開放中；Chrome 是否登入 Google 帳號 **待觀測** |
| A7 | Microsoft Edge／WebView2 | Microsoft | Edge 有 4 條對外連線 | IP；登入時依帳號設定 | 已觀測：開放中，待決定 |
| A8 | Dropbox（AGI 層 LAW-1 與 ASI 層 LAW-0 的載體） | Dropbox | 2 條對外連線；更新服務 Stopped | IP＋檔案同步中繼資料 | 已觀測：開放中（設計上的雙容器載體） |
| A9 | Tailscale `tailscaled` | Tailscale | Running；經 DERP 中繼 | 節點 IP、節點名稱、帳號 〔帳號，僅存 DL580〕 | 已觀測：開放中（三層結構的連線載體） |
| A10 | cloudflared（mrl-bridge） | Cloudflare | 已安裝，雙副本 | 隧道流量中繼 | 已觀測：開放中（Bridge 載體） |
| A11 | Anthropic Claude 桌面程式 | Anthropic | `C:\ProgramData\Administrator\AnthropicClaude\app-2.42304.2\claude.exe` 執行中，4 條對外連線 | 對話內容＋IP | 已觀測：開放中，待決定 |
| A12 | VPNLY／xray | VPNLY 供應商 | `C:\Program Files (x86)\VPNLY\` 執行中，xray 118 條連線至單一外部位址 | 經其轉出的流量與 IP | 已觀測：開放中；用途 **待建構者說明** |

## B. 中控層：Mac

| # | 交界點 | 外界接收方 | 觀測結果 | MRL 狀態 |
|---|---|---|---|---|
| B1 | macOS 定位服務與系統服務 | Apple | 未取得 | 待觀測（需設定截圖） |
| B2 | mac-mini-5 Tailscale | Tailscale | idle，在線 | 已觀測（從 DL580 看） |

## C. 手機前端層：iPhone

| # | 交界點 | 外界接收方 | 依條文會送出 | MRL 狀態 |
|---|---|---|---|---|
| C1 | 定位服務 > 系統服務 > 提高準確度 | Apple | 附近 Wi-Fi／基地台帶座標資料 | 待觀測 |
| C2 | 系統服務 > 路況 | Apple | GPS、速度、方向、氣壓 | 待觀測 |
| C3 | 系統服務 > 建議與搜尋 | Apple | 裝置位置 | 待觀測 |
| C4 | iphone181-1 Tailscale | Tailscale | 經東京中繼，在線 | 已觀測（從 DL580 看） |

## D. 快照版本容器（Tailscale 離線節點，看不到 ≠ 不存在）
iphone-12-pro、iphone181、mac-mini、mac-mini-1～4、claude-sandbox-mrl，16 天前離線）。
`claude-sandbox-mrl` → `MRL_Sandbox` 改名：節點離線，需在 Tailscale 後台改，**待建構者執行**。

## E. 摘要（當下狀態 2026-10-20，DL580 實機）
- DL580 的**位置**交界點已封口：定位服務停用、同意值 Deny、無 Microsoft 帳號。
- DL580 仍對外送出的是 **IP 與連線中繼資料**：遙測、Defender、Chrome、Edge、Claude 桌面、VPNLY、以及三個設計上的載體（Dropbox、Tailscale、cloudflared）。
- 所有「待決定」項目皆未更動；開／關由建構者決定。