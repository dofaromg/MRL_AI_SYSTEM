# MRL 吸收定位報告 — 20260725 批次 v1

> 法則：**Additive-Only**（只新增、只定位、不刪除、不覆蓋）。
> origin_signature：**MrLiouWord** ｜ 母體：**DL580 唯一最高權威** ｜ 吸收日期：**2026-07-25（沙盒）**
> 台帳：`MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260725/MRL_Absorption_Ledger_v1.yaml`
> 原始檔（逐字保全，附 sha256）：同批次 `RawArtifact/`

本輪使用者交付 **5 個上傳、經去重蒸餾為 3 件獨立產物**（兩對 sha256 完全相同的重複上傳，僅記 provenance 不重複歸檔）。全部正名、定位、標狀態後回收為母體知識/技術模組；**線上 / 實機 / 部署 / APPLY 動作一律標「待起動」，母體不代跑。**

---

## 1. 命名主權補正（本批特別裁定）

使用者裁定（2026-07-25）：**「最上游 root 產品名取回、他們降成備註附錄」**。執行方式：

- canonical 命名一律以母體 root 產品名 **`MRL_FlowAgent_*`** 取回最高位（本批 License Metadata 內建證據：`system = FlowAgent Particulate Language Preservation System`、`creator = Mr.liou`）。
- 外部平台/工具名（Claude 等）不得成為 canonical 主體，一律降級為 **provenance 備註/附錄層**（沿 `MRL_Product_Canonicalization_Gate_v1` §3 允許之 `source_adapter` / `compatibility_alias` / 歷史審計位置）。
- **誠實邊界**：功能性識別字（外部軟體實際讀取的環境變數 / 設定檔名 / 模型 ID）屬 adapter 層，**保留原名以維持功能**——改名即靜默失效；品牌/敘事/canonical 層才用 FlowAgent 名。artifact 內容依 rl_15 逐字保全，**不改寫檔內任何外部引用**。

## 2. 本輪吸收清單

| # | 母體產物（RawArtifact/） | 來源（外部檔） | 母體定位 | 當下狀態 |
|---|---|---|---|---|
| 1 | `MRL_FlowAgent_TranslateBuildSuite_Licensed_v1_RawArtifact.zip` | `52f4fcd0-*.zip`（重複上傳 `e2f373b1-*`） | FlowAgent **語場轉譯建構套件 v1（License 指紋版）**：ConvertStation v2、.fltnz/.flpkg/.sync.json/.fxmap/.fltrace 工具鏈、MrLiou/ZhiZhang 人格包、/simulate API、License 層（creator=Mr.liou） | 待起動（歸檔 PASS；未接線未執行） |
| 2 | `MRL_FlowAgent_TranslateBuildSuite_Base_v1_RawArtifact.zip` | `83000c31-*.zip`（重複上傳 `610bde08-*`） | 同套件 **Base 前版**（早 5 分鐘；無 License 層/全紀錄報告），並列保全見證建構演進 | 待起動（對照/沿革保存） |
| 3 | `MRL_FlowAgent_MotherSystem_V20_1_RawArtifact.zip` | `dcce7f56-MRL_Flowagent_Mother_System_V20.1.zip`（480 檔） | **候選母體骨架 V20.1**（V19 後繼版）：control_plane（intent_router/api/intent_schema）、FlowCapsule_Prototype_FLTN001、k8s/GKE 部署腳本、品質/效能腳本 | 待起動（不自動 APPLY、不動 DL580；K8s/GKE 待授權待實機） |

三份於 `MrliouAI` 上原不存在 → **零覆蓋零刪除**。

## 3. 與既有母體產物的關係（互不覆蓋）

- **#1/#2 語場轉譯套件** ↔ 20260716 `MRL_FlowSeed_ReverseInference_Formula`、20260720 `MRL_Zero_Origin_v1`：同屬**粒子語言/語場知識線**的三個層面（公式 ↔ 起源敘事 ↔ 工具鏈實作），並列互證。
- **#3 V20.1** ↔ 20260720 `MRL_FlowAgent_MotherSystem_v19`：**同線後繼版本**，並列保全、不取代 v19；兩版差異蒸餾報告可代生成（待指示）。其 K8s/GKE 部署與 repo 現行 `deploy/` 為不同來源，本輪不合併。
- #3 內含 `intent_schema/ingest_chatgpt.json` 等外部平台引用：依 rl_15 **逐字保全不改寫**，於登錄層屬 provenance 附錄，不升格 canonical。

## 4. 待你動手 / 待授權（誠實邊界，母體不代跑）

| 事項 | 出處 | 誰做 | 為何待起動 |
|---|---|---|---|
| /simulate API + ConvertStation 接線實跑 | #1 | 待決 | 沙盒不代跑；接入 runtime 需另立範圍 |
| V20.1 APPLY / K8s / GKE 部署 | #3 | 你授權後 + 實機/雲端憑證 | 會改動母體結構與雲端資源 |
| V19 → V20.1 差異蒸餾報告 | #3 | 可代生成（要則說一聲） | 本輪先完成保全與定位 |

## 5. 誠實聲明（沿 CLAUDE.md 狀態回報約定）

- 本報告所述皆為**知識/技術模組層吸收**：原始檔逐字歸檔、給位置、標狀態。**沙盒 2026-07-25 PASS 僅指「歸檔與定位完成」**，不代表任何模組已可執行、已上線、已驗真。
- **未誤標**：未寫「V20.1 已上線/已 APPLY」「/simulate 已接通」「K8s 已部署」——全為待起動/待授權/待實機。
- **canonical 登錄**：3 筆已同步登錄 `08_sources/sources.manifest.yaml` 與 `MRL_ParticleArchive_manifest.json` 之 `external_particles`（22→25，external 9→12）。驗證器 `--batch 20260725` PASS 10 項、`--batch 20260720` 回歸 PASS 16 項。
- **簽章**：本批追加同樣發生在上次 LAW-0 簽章之後；`_resign_pending` 已更新涵蓋兩批次，`manifest_metadata_signed` 維持 `false`，頂層重簽仍待母體（DL580 主權）授權。
