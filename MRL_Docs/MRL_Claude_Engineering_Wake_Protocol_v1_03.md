# MRL_Claude_Engineering_Wake_Protocol_v1_03（canonical 吸收物 — 建構者自撰工程喚醒機制）

origin_signature: `MrLiouWord`
canonical_name: `MRL_Claude_Engineering_Wake_Protocol_v1_03`
source: 上傳 `MRL_Claude_Engineering_Wake_Protocol_v1.03.docx`（建構者 MR.liou 自撰;byte source-of-record 於使用者端 / Google Drive / 本地）
source_sha256: `85cbd2cf1f27f0daa422ba829cafb0c22c979e81d5ad1a3583d3d700bee93bca`
absorbed_via: Claude Code session 通道（外部資料流回母體;只新增、不刪除、不覆蓋）
absorbed_at: 2026-11-08
status: **已對上原始檔**（逐字保存;本檔不改動任何既有 runtime 行為）

> 這份文件是建構者自己定義的工程喚醒機制，原本只存在於上傳檔／Google Drive／Notion（外部）。
> 依「怎麼過去就怎麼回來」與 Additive-Only，將它流回母體 repo 作 canonical 保存：
> 原件（docx）為位元組 source-of-record，保存於使用者端；本檔為母體 canonical 吸收物（逐字 Markdown）。
> 內文 origin_signature 與日期沿用原件，未更動。

---

⚡ Claude 工程啚醒機制

MRL Particle System — Engineering Wake Protocol

origin_signature: MrLiouWord | 2026-03-14 | MR.liou 設置

核心原則

「快也要準備才能穩，不然就是不斷地在修復前面的疏失而已」

這不是一條操作規範，是做事的底層邏輯。每次收到工程任務，必須按順序執行三段式流程。順序錯了就是浪費時間、導致系統衝突、重複建構已經存在的東西。

觸發條件

當 Claude 收到以下任何類型的任務時，必須先讀這份文件再動手：部署 Workers、寫程式碼、建構系統、修改配置、建立檔案、審計系統、任何工程推進。

觸發詞：「工程模式啚動」「先查再做」或任何工程任務開頭。

三重保護：Memory #22（每次對話自動載入）+ Notion 啚醒檢查頁 + 本文件（Google Drive + 本地備份）。三個節點缺一個都會執行。

三段式執行流程

第一步：收集確認（最重要，不可跳過）

以下四項全部執行，缺一不可：

查對話紀錄 — 執行 conversation_search，搜尋相關關鍵詞，看 MR.liou 和其他夾伴已經做了什麼、決定了什麼、交付了什麼

查 Notion — 執行 Notion search，搜尋相關頁面，特別查閱核心索引頁（見下方資源索引）

查線上實際狀態 — 用 Cloudflare API/MCP 查看 Workers 實際部署狀態、D1 資料、KV bindings，不要懑記憶

交叉比對 — 三個來源互相驗證，有衝突先釘清。MR.liou 可能已在其他對話視窗跟其他夾伴完成部分工作

第二步：規劃整合

根據確認後的真實現況設計工程計畫，不是根據「我記得」

查閱四台超級電腦並行建構法 — 確認是否適用 VM1-VM4 並行模式（8x 加速）

查閱 Wave 執行計畫 — 確認當前在哪個 Wave，從正確的斷點繼續

跟 MR.liou 確認計畫 — 不要假設他同意

第三步：快速執行模式

前兩步全部確認完成後才進入

執行過程中持續遵守 Liou Closure Law：NO_DELETE + ADDITIVE_RESOLUTION

新版本用新檔名，舊版本永遠保留

核心資源索引

Notion 必查頁面

頁面

Notion Page ID

四台超級電腦主控進度總表

3228eeeec5b581a58fdfc9150f93db87

SuperComputer + 工程模組 + CareOS粒子庫完整索引

31f8eeeec5b58136a107fa7528ce1b99

MRL_CareOS v9.2 工程計畫

3238eeeec5b581a8b680f81eb4a6cd33

MRL 系統工程進度 2026-03-14

3238eeeec5b58100ac64da9fa800718d

核心操作守則（粒子不滅律）

3238eeeec5b581d78f3fc7751e2ea7b8

Claude 工程啚醒檢查頁

3238eeeec5b5818c9bddcf64d41edfcc

ASI SuperComputer 組裝記錄 v1.0

3228eeeec5b5811daac6f836ab203b5e

四台超級電腦並行建構 (2026-03-10)

31f8eeeec5b5812caf3dcd08e88e089b

v9.0+ 斷點保存

3218eeeec5b581d4b425c75085729be1

38/38 缺口全攻計畫

3228eeeec5b581228796e1d704e6a183

Cloudflare 資源

資源

值

Account ID

0b36a4577da7fced6df2e062fa5f6fa2

Subdomain

z814241.workers.dev

KV mrliouword-vault

01275832766148bfbcaa00ee4aeb9946

KV particle-auth-vault

8cd99a4a67f74afea367f394995d5c50

D1 careos-db

bcc5aaaa-474d-43ee-a290-9c141ef71763

D1 shengai-isp-db

485d95e8-d58f-467e-a613-765bf170b4f5

D1 mrl-ai-db

3e91888d-3614-4abd-85a4-79db981b3fb6

已完成系統

系統

狀態

CareOS v9.2

38/38 缺口 + 2,354 測試 + 11 MRL Workers + D1 27表

Collapse Engine v2.1.1

41 端點 + KV/D1/R2/GPU/HMAC bindings

聖愛 ISP v3.1

AI 掃描 + 審批工作流 + PWA 離線

Dashboard v3.0

17 Service Bindings + 混合掃描

kernel.ts

23KB L0-L7 + FluinHub + MetaEnv + 注意力迴圈

parallel_network.ts

29KB 71節點 + SINDy + 量子通道 + P2P Merkle

四台超級電腦並行建構法

核心工程模式：不是序列建構，是同時開四台 VM 並行處理不同模組，然後統一測試。傳統序列 40 分鐘，並行 5 分鐘，加速比 8x。

Wave 執行計畫：Wave 1 (686粒子生成器) → Wave 2 (粒子工具箱) → Wave 3 (F++ 橋接) → Wave 4 (auth-gateway ✅) → Wave 5 (MetaEnv 9端點) → Wave 6 (整合測試)

其他夾伴資源：MR.liou 跟 ChatGPT、Gemini 等夾伴也有準備好的工具和細節。先查對話紀錄確認再動手。

錯誤案例警示 (2026-03-14)

Claude 跳過第一步直接執行，導致：把已完成的 CareOS v9.2 當成新 Workers 重新審計；建了重複的 NAS 出勤套件；漏掉 MR.liou 加的 GPU+HMAC bindings。根本原因：沒查對話紀錄、沒查 Notion、沒查線上實際狀態。如果第一步做對了，就不會做重複的工作。

粒子不滅律（Liou Closure Law）

NO_DELETE：任何刪除都是對衝突的掩蓋，不構成解決。不刪檔案、不覆蓋檔案。

ADDITIVE_RESOLUTION：所有修正必須以堆疊方式保留歷史。新版本用新檔名。

每個檔案都是根源粒子節點，可隨時延伸與收斂，可與其他粒子組合。粒子可以崩塌、分裂、壓縮、展開、放大——但不可以被刪除。

origin_signature: MrLiouWord | LAW-0 | LAW-1 | LAW-2

同步位置：Memory #21 + #22 | Notion 3238eeeec5b5818c9bddcf64d41edfcc | Google Drive | 本文件

怎麼過去就怎麼回來
