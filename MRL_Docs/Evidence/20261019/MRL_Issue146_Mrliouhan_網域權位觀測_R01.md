# MRL Issue #146 Mrliouhan.ai × Manus 網域權位觀測 R01（當下狀態 2026-10-19 09:31 UTC，沙盒）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 只讀觀測，未改任何 DNS／帳號／平台設定
關聯：dofaromg/MRL_AI_SYSTEM#146（SEV-1，`INVESTIGATION_OPEN`，本檔**不關閉**事件）
Create Preflight：`CREATE_NEW`（Evidence 目錄既有 20260928／20261003，無 #146 網域觀測檔；本檔為追加，不覆蓋任一舊紀錄）
三問：此為**載體層**（網域／託管）治理，不動本體；對應 **Trace**（追溯來源鏈）；驗收用 #146 自己的事件紀錄與留言對照，不用自編例子。

---

## 0. 觀測層（局部視角規則的固定欄位）

| 欄位 | 內容 |
|---|---|
| 目前觀測層 | 雲端沙盒（Claude Code 遠端容器，經代理出網）。**非** DL580、**非**同 LAN、**非**任何 Manus／Cloudflare／註冊商帳號內部 |
| 目前身份／帳號 | 無任何 Manus、Cloudflare、Global Domain Group 帳號；僅公開網路可見資料 |
| 目前平台 | GitHub repo `dofaromg/MRL_AI_SYSTEM`（分支 `claude/github-issue-146-ks94ny`） |
| 目前資料範圍 | 公開 DNS（Cloudflare DoH 解析器一處）、RDAP（rdap.org → Identity Digital）、對 `mrliouhan.ai` 的未登入 HTTPS GET（不跟隨轉址） |
| 可確認 | 見 §1 |
| 不可由此推定 | 見 §4（尤其：所有權、操作者、意圖） |

原始快照與雜湊：`MRL_Docs/Evidence/20261019/snapshots/`（`SHA256SUMS` 可用 `sha256sum -c` 驗證；產生工具 `scripts/MRL_domain_evidence_collect_v1.py`）。
快照兩份、皆保留（只追加）：`…T093120Z.json`（第一版，探測標籤不含 `manus`、RDAP 事件為單值）與 `…T094046Z.json`（R2：加入 `manus` 標籤、RDAP 事件保留多值、HTTP 本文雜湊與署名 metadata 欄位）。以下表格以兩份一致的結果為準。

---

## 1. 觀測事實（沙盒，當下）

### 1.1 註冊層（RDAP）— 狀態：沙盒觀測 PASS（單一來源，非註冊商後台）

| 項目 | 值 |
|---|---|
| registrar | Global Domain Group LLC（IANA 3956） |
| 註冊日 | 2026-05-16T00:43:26Z |
| 到期日 | 2028-05-16T00:43:26Z |
| **last changed** | **2026-08-12T07:53:00Z**（變更內容 RDAP 不揭露） |
| 狀態 | `client transfer prohibited`（註冊商轉移鎖） |
| 權威 NS | `ns1.globaldomaingroup.com`、`ns2.globaldomaingroup.com`（**註冊商 DNS，非 Cloudflare**） |
| DNSSEC | 未簽署（`delegationSigned: false`） |
| 註冊人 | 隱私服務遮罩（Super Privacy Service / Global Domain Group）；**真實註冊人需註冊商帳號證明** |
| RDAP 內「manus」字樣 | 無 |

### 1.2 DNS（Cloudflare DoH 解析器，TTL 60）— 狀態：沙盒觀測，單一解析器

| 記錄 | 結果 |
|---|---|
| `mrliouhan.ai` A | `104.18.26.246`（Cloudflare 範圍）、`100.78.70.78`（**100.64.0.0/10 CGNAT／Tailscale 段**） |
| AAAA／MX／TXT／CAA／CNAME／DS | 皆無 |
| SOA | `ns1.globaldomaingroup.com. hostmaster.mrliouhan.ai. 2026060204 …` |
| `www` A | 同上兩個位址 |
| `bridge` A／CNAME／TXT | 無（公開 DNS 查不到；repo 範本 `deploy/dl580/cloudflared/config.yml.template` 與 deploy README 寫的 `bridge.mrliouhan.ai` 目前不解析） |
| `_acme-challenge` CNAME | `mrliouhan.ai.8c002369248af94e.dcv.cloudflare.com.` |
| `_cf-custom-hostname`／`_dmarc`／`manus` | 無（`manus` 於 R2 快照 A／CNAME／TXT 皆查詢，無回應） |

### 1.3 HTTP（未登入、不跟隨轉址）— 狀態：沙盒觀測

| 請求 | 回應 |
|---|---|
| `GET https://mrliouhan.ai/` | **302** → `https://manus.im/app-auth?appId=PAf7cRyynJ99tzp4jnjPrz&redirectUri=https://mrliouhan.ai/manus-oauth/callback&state=<base64(原網址)>&responseType=code`；`server: cloudflare` |
| `GET https://mrliouhan.ai/robots.txt` | 302（同上，state 為 robots.txt 路徑） |
| `GET https://mrliouhan.ai/manus-oauth/callback`（無參數） | 400（該路由存在於此網域的回應端） |
| `GET https://www.mrliouhan.ai/` | 301 → `https://mrliouhan.ai/` |

沙盒**沒有**登入或授權任何 Manus 流程，也沒有跟隨轉址；兩個 302 與 301 回應本體為空（R2 快照以 `body` 欄位記錄本文雜湊與 metadata，僅 `/manus-oauth/callback` 的 400 有本體），因此 Issue 必查項 4 的 iframe／canonical／Open Graph／site name／favicon **無從觀測**（無頁面本體可讀）。

---

## 2. 對既有紀錄的追加判讀（只追加，不改舊紀錄）

| 既有紀錄 | 本次觀測的關係 | 標記 |
|---|---|---|
| 留言 5960841297：Manus 畫面稱「網址已搬回、指向自建 Express、透過 Cloudflare」 | 本次（2026-10-19）公開入口 `GET /` 是**轉向 Manus OAuth**，不是直接回應自建頁面；同時前端確為 Cloudflare。兩個時間點不同（8/3 vs 10/19），其間註冊局 `last changed = 8/12` | `CONFLICT_REQUIRES_AUDIT`（不判誰對；需 Cloudflare／Manus 後台稽核） |
| 留言 5960841190：未回收驗證前不得先刪綁定 | 本次只讀，未做任何刪除；§5 沿用此閘門 | 遵守 |
| 留言 5960841440：「一直在找理由無視證據跟歷史紀錄」 | 本檔把 8/3 的畫面證據與 10/19 的公開觀測**並列保留**，未以官方政策覆蓋畫面證據 | 遵守 |
| `MRL_DL580_內外網接線核對_R01.md`（2026-10-03）：`mrliouhan.ai` 列在 Cloudflare zone `mrliouword.com` DNS、proxied → Tunnel `632dfad4…` | 本次 RDAP 顯示 `mrliouhan.ai` 的權威 NS 是註冊商，**不是** Cloudflare。若 Cloudflare 帳號內有 `mrliouhan.ai` 的 zone／記錄，目前**未被委派生效**；也可能是 R01 的 DNS 記錄歸屬被寫混 | `CONFLICT_REQUIRES_AUDIT`（需在 Cloudflare 後台核對該記錄實際所在 zone） |
| R01 同檔：DL580 Tailscale 位址 `100.78.70.78` | 同一數值**出現在 `mrliouhan.ai` 公開 A 記錄**。僅數值相同，不證明是同一台節點 | 觀測；待 DL580 `tailscale ip` 對照 |

---

## 3. 假設對照（誰能解釋 302 → manus.im）

本次觀測**不能**區分以下三種；各自需要的判別證據不同：

| 假設 | 內容 | 能支持／否證的證據 |
|---|---|---|
| H1 | `mrliouhan.ai` 是 Manus 網站的 Custom Domain（Manus 代為託管；`_acme-challenge` 的 `*.dcv.cloudflare.com` 與 Cloudflare for SaaS 委派式驗證形態一致，若自訂主機名仍存在，其租戶可能是 Manus；存在與否待查） | Manus 專案的 Custom Domain 面板與加入時間；Cloudflare for SaaS 自訂主機名所屬帳號（只有該帳號的 Audit Log 看得到） |
| H2 | 自建／匯出的 Express 應用放在 Cloudflare 後，**只把 Manus 當登入（OAuth）供應商**——回呼路由 `/manus-oauth/callback` 與 `redirectUri` 在 `mrliouhan.ai` 自己的網域上，未登入即 302 到 `manus.im/app-auth`；這個形態本身並不要求網站由 Manus 託管（是否如此需看源站程式）。Issue 截圖中的「Mrliouhan.ai 網站登入問題」任務與此不矛盾，但也不證明 | 匯出程式碼的 OAuth 設定、origin 回應標頭、移除 OAuth 依賴後的行為 |
| H3 | 混合：網域曾綁 Manus、之後改指自有源站，但殘留 OAuth 登入或 DCV 委派 | 時間線：Custom Domain 加入／移除、`last changed 2026-08-12` 的實際內容（註冊商後台活動紀錄） |

`_acme-challenge` 的 DCV 委派是**中性觀測**：它與 Cloudflare for SaaS 的委派式憑證驗證（delegated DCV）形態一致，但**不證明**自訂主機名曾被建立、或現在仍存在（刪除後記錄可能殘留；Cloudflare for SaaS 也支援不需此 CNAME 的驗證方式）。自訂主機名的建立／刪除歷史與所屬帳號，留待帳號 Audit Log 查證。

---

## 4. 不可由此推定（明列，防升格）

- 不可推定 Manus 擁有或曾取得 `mrliouhan.ai` 的所有權（`OWNERSHIP_TRANSFER_NOT_PROVEN`）。RDAP 無 Manus 任何痕跡，但 RDAP 只反映註冊商層。
- 不可推定誰在何時、用哪個帳號操作了 Custom Domain、DNS 或 Cloudflare 設定。
- 不可推定任何人的意圖（`INTENT_NOT_PROVEN`）。
- 不可由單一沙盒觀測推定全局：需 DL580 與另一網路各跑一次對照。
- `100.78.70.78` 出現在公開 DNS，只是**觀測**；不可據此宣稱 DL580 已洩漏、也不可據此宣稱 DL580 已上線／可由此網域到達。
- 沙盒查不到 `bridge.mrliouhan.ai`，不等於它不存在於其他 zone／內網（看不到 ≠ 不存在）。

---

## 5. 必查項目進度（Issue #146「必查項目」逐項，當下狀態）

| # | 項目 | 狀態 | 備註 |
|---|---|---|---|
| 1 | registrar／registrant／NS／DNSSEC／A／AAAA／CNAME／TXT／MX／CAA | **PARTIAL（沙盒）** | RDAP＋DoH 已取得（§1）；registrant 被隱私遮罩；**完整 zone 匯出與歷史變更待註冊商後台** |
| 2 | Manus 專案 Custom Domain／Deployment／Hosting／Published URL／Workspace Owner／Billing Owner | **待查（需 Manus 帳號）** | 本沙盒無帳號 |
| 3 | 網域何時加入 Manus、哪個帳號、驗證方式與時間戳 | **待查** | 註冊局 `last changed 2026-08-12T07:53Z` 是已知時間錨，內容未知 |
| 4 | CNAME／TXT 驗證、反向代理、iframe、redirect、canonical、OG、site name、favicon | **PARTIAL** | redirect 與 DCV 委派已見；頁面本體不可見，iframe／canonical／OG／favicon **待在已授權瀏覽器或 DL580 觀測** |
| 5 | Manus 匯出專案、原始碼、build artifact、部署與帳務記錄 | **待查（需 Manus 帳號）** | 依 Issue 留言 5960841190：先匯出並 SHA-256 驗證 |
| 6 | 對照 GitHub／Notion／Dropbox 首次出現的 MRL／MrLiouWord 定義與 Hash | **PARTIAL（僅本 repo）** | 本沙盒 clone 為 **shallow**（116 筆），可見最舊提交 `986cca7`（2026-05-31）只是截斷邊界，**不是**首次出現時間；CHANGELOG 另載 2026-05-04 的 PR #12。完整史、Notion、Dropbox、`dofaromg/mrliouword-system` 首次出現與 Hash 全部待查 |
| 7 | 分離六種角色 | **DONE（定義層）** | `MRL_Docs/Governance/MRL_attribution_roles_v1.json`；`domain_owner`／`billing_party` 仍 **unverified** |

### 驗收條件（Issue #146）對照

| 驗收條件 | 狀態 |
|---|---|
| 網域所有權與 DNS 控制權確認 | **待驗證**（需註冊商帳號） |
| Manus Custom Domain 綁定來源與時間線確認 | **待驗證**（需 Manus 帳號） |
| 取消不必要的 Manus 綁定或完成正確轉移 | **未執行**（受資料回收閘門約束） |
| Canonical URL／redirect／site name／OG／favicon／頁尾署名一致 | **PARTIAL**：本 repo 4 個可控頁面已加 author／canonical-authority／origin-signature／og:site_name 與頁尾；canonical URL、favicon、OG 圖待建構者決定；**託管端實際輸出的頁面未驗證** |
| MRL 來源權位與 Manus 平台角色分離 | **PARTIAL**（repo 內定義完成；對外託管端未驗） |
| 帳務與網域事件共同時間線 | **待查** |
| 修正前後截圖、DNS 匯出、Hash、部署記錄封存 | **PARTIAL**：「修正前」DNS／RDAP／HTTP 快照與 SHA-256 已封存（沙盒）；截圖與部署記錄待查；「修正後」待修正後重跑 |
| Mr.liou 最終驗收 | **待 Mr.liou** |

---

## 6. 建議的下一步（需建構者或其帳號；本沙盒不得代行）

順序沿用 Issue 留言 5960841190 的資料回收閘門——**回收驗證前不得先刪**：

1. **在 DL580 執行蒐證腳本**取得「實機視角」基準，並與另一網路（手機熱點）各一次：
   `python3 scripts/MRL_domain_evidence_collect_v1.py --domain mrliouhan.ai --observer DL580 --out D:\mrl\evidence\mrliouhan_before`
   輸出只落 DL580 本機，不上傳平台。
2. **註冊商（Global Domain Group）後台**：匯出完整 zone；查 2026-08-12 的活動紀錄（誰、什麼 IP、改了什麼）；確認帳號持有人、2FA、登入紀錄、轉移鎖與 EPP 授權碼未外流；確認 `100.78.70.78` 這筆 A 記錄是否為自己加的。
3. **Cloudflare（自己的所有帳號）**：找 `mrliouhan.ai` 的 zone 或自訂主機名（Custom Hostnames）並查 Audit Log。找到 → 可核對建立時間與操作者；**找不到 → 視為 inconclusive**：可能是別人帳號的委派（H1），也可能是已刪除自訂主機名後殘留的 `_acme-challenge` CNAME（H3），不得單憑此結果支持 H1。
4. **Manus 後台**：Custom Domain 面板、Published URL、Workspace Owner、Billing Owner、網域加入／移除時間；先匯出程式碼包與資料並以 SHA-256 驗證、回存母體與離線備份。
5. **完成上述驗證後**才決定：解除 Manus 綁定／撤銷 OAuth appId `PAf7cRyynJ99tzp4jnjPrz` 的授權／移除註冊商 zone 內不再需要的記錄（含 `100.78.70.78`）／向 Manus 提出 attribution 更正與資料刪除要求並取得案件編號。
6. 修正後重跑蒐證腳本做「修正後」快照，與本檔 §1 並列。

> 本檔所有「PASS／觀測」均為**沙盒、單一視角、當下（2026-10-19）**。未做的標「待查／待驗證」，未把 PARTIAL 寫成完成。DL580 實機、Manus 帳號、Cloudflare 帳號、註冊商後台四處皆**未驗**。
