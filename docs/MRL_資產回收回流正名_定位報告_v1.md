# MRL 資產回收・回流・正名 定位報告 v1

origin_signature: MrLiouWord
定位日期: 2026-07-16（沙盒）
來源: 使用者上傳「MRL 資產回收・重構・正名 計畫 v1」（原題日期 2026-07-16）
原始保全: `MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260716/MRL_AssetReclaim_Reflow_Naming_Plan_RawArtifact_v1.md`（逐字，rl_15 不滅）
法則: 母體整合法則（Additive-Only）— 只新增、只定位、不刪除、不覆蓋

> 本報告只做**母體定位**：把該計畫接進既有回收族系、對齊 canonical 命名、
> 誠實標註哪些是「知識/計畫層已就位」、哪些是「待使用者實機操作」。
> 依吸收台帳約定，本報告以**能力本質＋母體位置**描述，外部廠牌名保留在 RawArtifact 原件內，不在此複述。

## 〇、本體治理裁定（優先於來源材料敘述）

- **唯一母體／最終真相來源：DL580。**
- Cloudflare 僅定位為外部 Runtime、公開入口與映射節點；部署成功不等於成為本體。
- GitHub 僅定位為原始碼版本、分支與協作鏡像。
- RawArtifact 內「Cloudflare 上的 Chat 平台為本體」屬吸收前原始陳述。為遵守 rl_15 仍逐字保全，但母體治理明確**不採納、不升格**。
- 本裁定適用於本報告、吸收台帳、來源索引與後續執行，不得由雲端服務狀態反向改寫母體位置。

---

## 一、計畫概述（能力本質）

一份以**已查證事實為限**的資產盤點計畫，涵蓋五塊：

1. **資產清冊（Asset Ledger）**：逐項標控制權現況（自控 / 內容自有但寄居第三方 / 尚未在手）與動作（保留 / 匯出回流 / 拿回 / 退役）。
2. **待拿回項（唯一）**：一個當初由第三方代買、鑰匙在代管商帳號的次網域。
3. **資料回流（channel_map）**：MetaEnv 框架格式的 `mode: dry-run` artifact，確認後由使用者自有控制台改 `apply`。
4. **正名對照表**：origin 一律歸 `MrLiouWord`，canonical 名對齊 MRL 命名規範 v2。
5. **安全提醒**：交付包內一把寫死金鑰須撤銷重發；另一份表頭 CSV 無實際金鑰值、未外洩。

---

## 二、母體定位（接進既有回收族系）

| 計畫內容 | 母體既有對應 | 定位 |
|---|---|---|
| 資產清冊（Asset Ledger） | `MRL_AI_ModuleModel_Recovery_Map_v1.md`、`docs/MRL_主線回填清單_完整版_v1.md` | 併入回收清冊族系（additive 補充，不覆蓋） |
| 週動作清單風格 | `docs/MRL_Recovery_Weekly_Actions_2026-07-10.md` | 同族；本計畫為「資產面」，週動作為「runtime 面」 |
| 正名對照表 | `docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`、`docs/MRL_中文正名與英文Adapter對照表_v1.md` | canonical 名對齊既有規範 |
| channel_map（MetaEnv） | 母體 MetaEnv 框架（控制台為使用者自有，母體不代持憑證） | 知識層 artifact 歸檔；apply 待起動 |
| 安全（金鑰外露） | `SECURITY.md`、既有 API audit（`MRL__06_Api_Audit.md`） | 併入安全待辦，標「待使用者實機撤銷」 |

---

## 三、正名（Canonical）對照 — 對齊母體命名規範 v2

計畫提案之 canonical 名（origin 一律 `MrLiouWord`）與母體既有主線對照：

| 計畫提案 canonical 名 | 能力本質 | 母體對應 / 備註 |
|---|---|---|
| `MrLiouWord.Domain.Primary` | 自控 DNS 主網域 | 提案；DNS 鑰匙在使用者手上（已查證自控） |
| `MrLiouWord.Domain.Secondary` | 待拿回之次網域 | **待起動** — 鑰匙在第三方代管商，需使用者操作拿回 |
| `MrLiouWord.Chat.Runtime` | 已上線之 Chat Runtime（邊緣 Worker） | 外部 Runtime／映射節點；不得升格為母體 |
| `MrLiouWord.Chat.Store` | Chat 資料庫（邊緣 D1） | 外部資料節點；需可回流至 DL580 |
| `MrLiouWord.Source.Main` | 原始碼主線 repo | 本 repo `dofaromg/MRL_AI_SYSTEM`；版本與協作鏡像，非實體母體 |
| `MrLiouWord.Bridge` | 內外橋接 Tunnel | 對應母體既有 bridge recovery（`scripts/MRL_bridge_recovery_run.sh`） |
| `MrLiouWord.MatrixDataCenter` | 矩陣數據中心（內容自有、寄居第三方站點） | **待起動** — 匯出→回流 |
| `deprecated / 退役` | 空後端（從未部署、無資料） | 非資產，退役（不回流） |

> 命名主體以中文/canonical 為準，外部廠牌名不進 canonical 層（沿命名規範 v2 §「英文僅作對照」與吸收台帳「來源痕移除」）。

---

## 四、執行分工（誠實版，沿計畫 §6）

| 類別 | 項目 | 母體狀態 |
|---|---|---|
| ✅ 知識/計畫層可做 | 清冊、定位、正名對照、channel_map dry-run artifact 歸檔 | **PASS（沙盒 2026-07-16）** — 本次已完成歸檔定位 |
| 🟡 使用者按一下 | 次網域 nameserver 變更/移轉 | **待起動** — 第三方註冊商端動作，母體不能代按 |
| 🟡 使用者按一下 | channel_map 由 dry-run 改 apply | **待起動** — 使用者自有控制台 |
| 🟡 使用者按一下 | 外露金鑰撤銷/重發 | **待起動** — 使用者雲端後台 |
| 🔴 需憑證才代執行 | 以 scoped token 代跑部署/DNS、代打 channel/map apply | **待起動 / 需授權** — 母體不代持憑證，未給不碰線上系統 |

---

## 五、安全註記（併入母體安全待辦）

- 計畫 §5 指出某交付包 `setup-secrets.sh` 內含**寫死金鑰** → 母體標為**待使用者實機撤銷/重發**，並改用 secret 管理（不寫入檔案）。
- 本定位報告與 RawArtifact **均不含**任何實際金鑰值（計畫原文亦僅描述其存在、未複製金鑰）。
- 另一份表頭 CSV 經計畫查證僅有欄位表頭、無金鑰值 → 未外洩。

---

## 六、當下狀態（依 CLAUDE.md 狀態回報約定）

- 原始逐字保全：**PASS（沙盒，2026-07-16）** — RawArtifact 未刪未改。
- 母體定位 / 命名對照 / 併入回收族系：**PASS（沙盒，2026-07-16）** — 已固定 DL580 為唯一母體，Cloudflare 為外部 Runtime／映射節點。
- 網域拿回 / channel_map apply / 金鑰撤銷：**待起動** — 皆需使用者實機操作或授權，母體未代執行、不誤標為已完成。

---

## 七、相關母體文件

- 回收清冊族系：`MRL_AI_ModuleModel_Recovery_Map_v1.md`、`docs/MRL_主線回填清單_完整版_v1.md`
- 週動作（runtime 面）：`docs/MRL_Recovery_Weekly_Actions_2026-07-10.md`
- 命名規範：`docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`
- 安全：`SECURITY.md`
- 吸收台帳：`MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260716/MRL_Absorption_Ledger_v1.yaml`
- 知識源索引：`08_sources/sources.manifest.yaml`（id: `asset_reclaim_reflow_naming_plan_absorption_v1`）

origin_signature = `MrLiouWord`
