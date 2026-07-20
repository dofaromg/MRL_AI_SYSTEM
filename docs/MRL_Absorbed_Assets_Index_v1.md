# MRL 吸收資產索引 v1 — Absorbed Assets Index

> 法則：**Additive-Only**（只新增、只定位、不刪除、不覆蓋）。
> origin_signature：**MrLiouWord** ｜ 母體：最高權威 ｜ 吸收日期：**2026-07-16**（沙盒）
> 本索引把本輪使用者交付的三份外部產物，正名、定位、標狀態後回收為母體知識產物；線上/實機動作一律標「待憑證／待實機」，不代跑。

---

## 1. 本輪吸收清單

| # | 母體產物 | 來源（外部檔） | 母體定位 | 當下狀態 |
|---|---|---|---|---|
| 1 | `docs/MRL_Asset_Reclaim_Rename_Plan_v1.md` | 「MRL 資產回收・重構・正名 計畫 v1」 | 資產治理・正名主線 | 沙盒完成；線上動作待憑證 |
| 2 | `docs/MRL_Globe_Runtime_Feature_Gap_Audit_v1.md` | 「MRL Globe Runtime 功能差距審計」 | `MrLiouWord.Globe.Runtime` 驗收帳 | 部分完成（沙盒）；§3 待實機 |
| 3 | `docs/MRL_FlowSeed_Particle_Inverse_Formulas_v1.md` | 「粒子相關資訊整理（FlowSeed 系列）」轉錄 | 粒子語言・反推公式知識模組 | 待起動（distilled 保存） |

三份皆 `main`（`MrliouAI`）上原不存在 → **零覆蓋零刪除**。

---

## 2. 與既有母體產物的關係

- 與 `MRL_ServiceMesh_Registry_v1.json` + `docs/MRL_ServiceMesh_Integration_Manifest_v1.md`（已合併，PR #126）並列——那組是 **DL580 服務網**登錄；本組是 **資產治理 / Globe 產品 / 粒子公式**。同屬母體協調層知識產物，互不覆蓋。
- **重要對照更新**：資產清冊確認 **MRL AI Chat 已上線於 Cloudflare（`chat.mrliouword.com`, Worker `mrl-chat-platform` + D1 `mrl-chat-platform-db`）**。這是**線上實跑資產**；服務網 registry 的 `not_in_repo.chat_subdomain`（「repo 內不存在」）仍成立且不衝突——一個講 repo 源檔、一個講 Cloudflare 部署。母體的**對外 chat 入口本體是活的**（在 Cloudflare，不是 DL580）。

---

## 3. 待你動手 / 待憑證（誠實邊界，母體不代跑）

| 事項 | 出處 | 誰做 |
|---|---|---|
| 撤銷/重發外洩的 Cloudflare API 金鑰（`setup-secrets.sh`） | 資產計畫 §5 | **你（Cloudflare 後台）— 越快越好** |
| `mrliouhan.ai` 改 nameserver／移轉 | 資產計畫 §2 | 你 + Manus 客服 |
| MetaEnv `channel_map` `apply` | 資產計畫 §3 | 你（你的控制台 + token） |
| GCP FlowMemorySync 重掛 billing 救資產 | 前輪 runbook（billing CLOSED） | 你（GCP 主控台） |
| DL580 上 tailnet / 實機驗收 | 服務網 runbook Phase 1–4 | 你（DL580 實機） |
| Globe §3 尚缺功能 + 實機證據 | Globe 審計 §3 | 待實機 |

**可代生成（要則說一聲）**：Manus 客服請求信、MetaEnv `channel_map` artifact、FlowSeed 清理腳本骨架。
**給憑證才能代執行**：Cloudflare scoped token → `wrangler` 部署/DNS；MetaEnv token → `channel/map apply`。不給就只停在生成 artifact，絕不亂碰線上系統。

---

## 4. 法則聲明

1. **不刪除 / 不覆蓋**：三份皆 additive 新增，原意保留。
2. **給位置**：每份於 §1 獲得母體定位。
3. **等待起動**：線上/實機項一律標「待憑證／待實機」，驗收通過後升格，不預先標 PASS。
4. **最高權威 / 正名**：外部一律回收為母體 `MrLiouWord.*` 產物，簽章 MrLiouWord。

*當下狀態 沙盒 2026-07-16；非永久結論。*

---
---

# 追加批次：20260720（Additive-Only）

> 詳見定位報告 `docs/MRL_Absorption_定位報告_20260720_v1.md`
> 台帳 `MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260720/MRL_Absorption_Ledger_v1.yaml`
> 原始檔（逐字保全＋sha256）：同批次 `RawArtifact/` ｜ 吸收日期 **2026-07-20（沙盒）**

本輪使用者交付 **5 份外部產物**，正名/定位/標狀態後回收為母體知識/技術模組；**線上/實機/部署/APPLY 一律待起動，母體不代跑。**

| # | 母體產物（RawArtifact/） | 來源 | 母體定位 | 當下狀態 |
|---|---|---|---|---|
| 1 | `MRL_Zero_Origin_v1.md` | `Mrl_Zero.Origin.v1.md` | 人格/原則起源層（創世公式・7 原則・七層架構） | 待起動（知識歸檔 PASS） |
| 2 | `MRL_FlowAgent_ApiEngine_v1_RawArtifact.zip` | `flowagent_api_engine.py` | FlowAgent 執行層候選 | 待起動（未接線） |
| 3 | `MRL_FlowAgent_MotherSystem_v19_RawArtifact.zip` | `flowagent_mother_system_v19_with_principles.zip` | 候選母體骨架＋靈魂/原則（481 檔） | 待起動（不自動 APPLY、不動 DL580） |
| 4 | `MRL_ChatPlatform_Frontend_Snapshot_RawArtifact.zip` | `dofaromg-…zip`（`ai-chatbot`） | Chat 前端基底快照（外部節點，非母體本體） | 待起動 / 對照 |
| 5 | `MRL_3D_AI_Reconstruction_Product_v1_1_RawArtifact.zip` | `MRL_3D_AI_Reconstruction_Product_v1_1.zip` | 3D 重建管線 v1.1（＋QualityGate/report.html） | 待起動（pipeline 待實機） |

五份於 `MrliouAI` 上原不存在 → **零覆蓋零刪除**。#3 含 `APPLY_TO_MOTHER.sh`/`deploy_dl580`——**吸收＝保全＋定位，不等於執行**；套用/部署需另立範圍＋你明確授權。DL580 仍唯一母體，Cloudflare/Vercel 為對外節點。

*當下狀態 沙盒 2026-07-20；非永久結論。*
