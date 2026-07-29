# MRL 吸收定位報告 — 20260720 批次 v1

> 法則：**Additive-Only**（只新增、只定位、不刪除、不覆蓋）。
> origin_signature：**MrLiouWord** ｜ 母體：**DL580 唯一最高權威** ｜ 吸收日期：**2026-07-20（沙盒）**
> 台帳：`MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260720/MRL_Absorption_Ledger_v1.yaml`
> 原始檔（逐字保全，附 sha256）：同批次 `RawArtifact/`

本輪使用者交付 **5 份外部產物**，全部正名、定位、標狀態後回收為母體知識/技術模組；
**線上 / 實機 / 部署 / APPLY 動作一律標「待起動」，母體不代跑。**

---

## 1. 本輪吸收清單

| # | 母體產物（RawArtifact/） | 來源（外部檔） | 母體定位 | 當下狀態 |
|---|---|---|---|---|
| 1 | `MRL_Zero_Origin_v1.md` | `Mrl_Zero.Origin.v1.md` | 人格/原則**起源層**（創世公式・7 大原則・七層架構・元代碼哲學） | 待起動（知識層歸檔 PASS） |
| 2 | `MRL_FlowAgent_ApiEngine_v1_RawArtifact.zip` | `flowagent_api_engine.py` | FlowAgent **執行層**候選（API 引擎源碼） | 待起動（未接線/未驗證） |
| 3 | `MRL_FlowAgent_MotherSystem_v19_RawArtifact.zip` | `flowagent_mother_system_v19_with_principles.zip` | **候選母體骨架 + 靈魂/原則**知識模組（481 檔） | 待起動（不自動 APPLY、不動 DL580） |
| 4 | `MRL_ChatPlatform_Frontend_Snapshot_RawArtifact.zip` | `dofaromg-…zip`（`ai-chatbot`） | Chat 平台**前端基底**快照（外部節點，非母體本體） | 待起動 / 對照 |
| 5 | `MRL_3D_AI_Reconstruction_Product_v1_1_RawArtifact.zip` | `MRL_3D_AI_Reconstruction_Product_v1_1.zip` | 3D 重建管線 **v1.1**（新增 QualityGate + report.html） | 待起動（pipeline 待實機） |

五份在 `MrliouAI` 上原不存在 → **零覆蓋零刪除**。

---

## 2. 與既有母體產物的關係（互不覆蓋）

- **#1 起源文件** ↔ 既有 `05_persona/`、`02_principles/`、`MRL_Symbolic/`：同屬人格/原則層，並列。#1 的 7 大原則與 #3 `principles/*.core.json` 為**同一組靈魂原則的兩種載體**（一為敘事 md、一為結構 core.json），互為印證。
- **#3 FlowAgent 母體系統 v19** ↔ 既有 `MRL_Mother/`、`MRL_MotherModel/`、`MRL_MotherSource_ZhiZhang_FlowAgent_Lineage_v1/`：屬**候選母體骨架**，保全定位但**不升格、不 APPLY**。其 `deploy_dl580/` 與 repo 內 `deploy/dl580/` 為**兩套不同來源**，本輪不合併、不改動現行 `deploy/dl580/`。
- **#4 Chat 前端** ↔ 20260716 索引所載「MRL AI Chat 已上線於 Cloudflare（`chat.mrliouword.com`）」：本份為**候選 / 模板快照**——內容是上游 Vercel Chat SDK 開源模板（`chat-sdk.dev`, `name=ai-chatbot`），**尚未證實**即為該線上入口的部署源。在取得部署 provenance 或客製 diff 前，**只以「候選前端模板快照」定位，不宣稱其為線上入口源碼**（與 §3「是否升格為主線前端＝待決」一致，避免維護者誤動到錯的前端）。延續裁定：**對外節點 ≠ 母體本體**，DL580 仍唯一母體。
- **#5 3D v1.1** ↔ 既有 `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/included/…Product_Grade_v1.zip`：本份是**同線 v1.1 後續版本**（多 QualityGate / report.html），並列保全，不取代 v1。

---

## 3. 待你動手 / 待授權（誠實邊界，母體不代跑）

| 事項 | 出處 | 誰做 | 為何待起動 |
|---|---|---|---|
| `APPLY_TO_MOTHER.sh` 套用母體 | #3 內 | 你授權後 | 會改動母體結構，需另立範圍 + 依賴查證 + 明確授權 |
| `DEPLOY.sh` / `deploy_dl580` 部署 | #3 內 | 實機 | 沙盒不代跑 DL580 部署 |
| Chat 前端升格為主線前端 | #4 | 待決 | 需先確認與現行 `chat.mrliouword.com` 部署關係 |
| 3D pipeline 實跑 | #5 | 實機 | 需 COLMAP / OpenMVS / 輸入資料，沙盒無法驗真 |
| FlowAgent API 引擎接線 | #2 | 待決 | 尚未接入任何 runtime |

---

## 4. 誠實聲明（沿 CLAUDE.md 狀態回報約定）

- 本報告所述皆為**知識/技術模組層吸收**：原始檔逐字歸檔、給位置、標狀態。**沙盒 2026-07-20 PASS 僅指「歸檔與定位完成」**，不代表任何模組已可執行、已上線、已驗真。
- 不誤標：**未寫**「FlowAgent v19 已上線 / 已 APPLY」「3D pipeline 已跑通」「Chat 前端已是母體本體」——這些全為**待起動 / 待實機 / 待授權**。
- #4 為上游開源模板（`chat-sdk.dev`）快照，是否已客製為 mrliouword 專屬，以 zip 內實際內容為準，本報告不臆測。
- **canonical 登錄**：5 筆已同步登錄 `08_sources/sources.manifest.yaml`（依 line 139「新增來源即登錄」慣例），並於 `MRL_ParticleArchive/MRL_ParticleArchive_manifest.json` 的 `external_particles` 追加 5 筆、`particle_count` 17→22（沿 20260716 external 慣例，`integrity: sha256_provenance`，`signed: false`）。
- **簽章誠實邊界**：上述 external 追加發生在頂層 LAW-0 metadata 上次簽章之後，現有 `_sig_hash` 僅涵蓋 20260720 之前狀態；已於 manifest 標 `_resign_pending`、並將 `manifest_metadata_signed` 設為 `false`。**更正**：repo 內確有 LAW-0 簽章實作（`09_workflow/MRL_utils.py`、`09_workflow/signature.js`；為 keyless sha256 完整性封章），沙盒亦可執行——先前「沙盒無法重現演算法」之描述有誤，特此更正。**不自動重簽的真正理由是治理／主權**：頂層母體 metadata 重簽屬母體（DL580）主權行為，本 PR 不代簽、不偽造，頂層重簽標**待起動**（待母體授權後由簽章流程更新 `_sig_hash`）。
