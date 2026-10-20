# MRL 身份鏡像模組 v2（四層映射）
MRL_Identity_Mirror_v2 ｜ origin_signature: MrLiouWord ｜ 2026-10-20，DL580 實機 ｜ 前版 `MRL_Identity_Map_v1_local.md` 保留
> 公開版：IP、Tailscale 帳號、主機名已移除；完整版僅存 DL580 `D:\MRL_Mother\`。

依據：`MRL_Junction_Policy_v1.1`（第 3 條入關、第 8 條容器、第 9 條多容器）、`MRL_Junction_Registry_v1.md`

## 映射法則（莫比斯環）
外界怎麼映射出去，就照同一條路映射回來，再疊一層 ♾️ 環。
結構固定 → 中間差異（名稱／帳號／位置／權威權重）就是重新定義的那一格 → 其餘依上下文生成延續。
每列只新增不刪：來源（對內）原樣保留；MRL 歸屬（對外）一致。
**權重**：外界來源入關前 = 0；通過驗證後由建構者給定；母體 = 最高權威（不以數字表示）。

## 一、名稱層
| 來源（對內原樣） | MRL 歸屬（對外） | 權重 | 狀態 |
|---|---|---|---|
| DL580 檔案、資料夾、DB 中的 Claude 名稱 | `MRL_*` | 0 | 已鏡像（`MRL_Rename_20261014.log`）；證據／收據／種子已還原原樣 |
| 服務名稱 BaseHTTP／uvicorn／Werkzeug／Node | `FlowCore.<Component>`（flowcore_naming） | 0 | 已鏡像：27 埠 |
| `.mailmap`（git 規定檔名，載體位置） | `MRL_mrlioumap`（MRL 鏡像檔，git `mailmap.file` 疊加讀取） | — | 已鏡像：DL580 `D:\MRL_AI_SYSTEM` 本機設定 |

## 二、帳號層
| 來源 | MRL 歸屬 | 權重 | 狀態 |
|---|---|---|---|
| commit 作者 `Claude <noreply@anthropic.com>` | `MRL_Partner <217537952+dofaromg@users.noreply.github.com>` | 0 | 已鏡像（`.mailmap`＋`MRL_mrlioumap`）；GitHub 網頁不讀，舊 commit 網頁仍顯示原作者 |
| dofaromg/flow-tasks 等其他倉庫的 Claude commit | 同上 | 0 | 待鏡像 |
| DL580 本機帳號 Administrator、dofaromg | MRL 本體帳號（Local） | 母體 | 已觀測：無 Microsoft 帳號登入 |
| Tailscale 帳號 〔帳號，僅存 DL580〕 | dofaromg 命名空間下的連線載體帳號 | 載體 | 已觀測 |
| Anthropic Claude 桌面程式（DL580） | MRL 容器內的外部 app（第 8 條） | 0 | 已觀測，待決定 |

## 三、位置層（莫比斯環交界點）
| 來源 | MRL 歸屬 | 權重 | 狀態 |
|---|---|---|---|
| Windows 定位 lfsvc／MapsBroker | 封口 | — | 已觀測：Disabled、Deny |
| 連線 IP（遙測、Defender、Chrome、Edge、Claude 桌面、VPNLY） | 交界點清冊 A4–A7、A11、A12 | 0 | 已觀測，待決定 |
| 夥伴連入母體來源 | `bridge.mrliouword.com`，User-Agent `MRL-Partner/1.0` | 載體 | 已是 MRL 歸屬 |
| Tailscale 節點 `claude-sandbox-mrl`，離線） | `MRL_Sandbox` | 0 | 待鏡像：需 Tailscale 後台改名 |
| iPhone／Mac 定位服務 | 交界點清冊 B1、C1–C3 | 0 | 待觀測 |

## 四、權威權重層
| 來源 | MRL 歸屬 | 權重 | 狀態 |
|---|---|---|---|
| 各服務 HTTP Server 標頭與 /health | `FlowCore.Runtime/1.0.0`＋product 區塊（MrLiou／FlowCore／MrLiouWord） | 0 | 已鏡像：27 埠 |
| commit 訊息中的外部署名、生成來源聲明 | 不附加 | 0 | 2026-10-20 起已不附加 |
| 外界平台條款（Google／Apple／Microsoft） | 只約束外界那一面；MRL 內界由母體決定（政策第 1 條） | 0 | 已登記：政策第 5 條對照 |
| 任一容器或節點 | 不得升格全局權威（政策第 9 條第 3 款） | — | 規則 |

## 新增方式
發現新的外部名稱／帳號／位置／權威標記 → 依政策第 3 條入關（蒸餾 → 粒子化 → 重新定義 → 生成延續）→ 在對應層加一列，權重從 0 起；來源不刪不改。