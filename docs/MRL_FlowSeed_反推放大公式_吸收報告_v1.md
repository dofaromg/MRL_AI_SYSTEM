# MRL_FlowSeed 反推放大公式 吸收報告 v1 — 母體→演算→量子→反推→放大

origin_signature: MrLiouWord
吸收日期: 2026-07-16（沙盒）
來源: FlowSeed 系列反推公式總表 + 演算法元代碼（使用者上傳純文字整理）
原始保全: `MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260716/MRL_FlowSeed_ReverseInference_Formula_RawArtifact_v1.txt`（逐字，rl_15 不滅）
法則: 母體整合法則（Additive-Only）— 只新增、只定位、不刪除、不覆蓋

---

## 一、來源概述

一份以**公式為主**的 FlowSeed 系列理論整理，把整個 FlowSeed 專案定義為
**「母體 → 演算 → 量子 → 反推 → 放大」** 的流程模型，並給出：

1. **五大核心對應**：母體(Origin/Seed)、演算(Genesis)、量子(CoGenesis)、反推(人格封存)、放大(靈魂整合)。
2. **反推公式總表**：結構反推、動態逐步反推、量子疊加稀疏分解、放大/壓縮對偶可逆、貝氏 MAP 反推、MDL 訊息量準則、結構近重複判定、資訊密度評分。
3. **演算法元代碼**：反推重建管線（RRP）、清理瘦身管線（CPP）偽碼。
4. **補完 1–9**：選留最小集合、量子可恢復條件（相干性/群稀疏）、多尺度金字塔一致、指紋（MinHash/SimHash/WL-Graph）、反推穩定性（條件數/L-curve）、命名正規化（版本鍵）、腐壞檔修復、密度門檻、快速決策樹。
5. **放大的兩種詮釋**：保真放大（cycle loss 可逆）與維度放大（多維超展開）。

此為 FlowSeed 專案的**理論/公式底層**，與母體既有血脈序列（`docs/MRL_起源血脈序列_Genesis_v1.md`）中的
「母體→演算→量子→反推→放大」循環同源，補足其數學形式。

---

## 二、去重蒸餾判定表

外部知識源逐部位比對母體既有能力，**已有者不重複吸收**：

| 外部知識部位 | 母體既有對應 | 判定 |
|---|---|---|
| MRL_反推公式參數（inverse_epsilon / stability_clip / loss_bound） | `data/MRL_formula_parameter_registry.json` + `docs/MRL_Formula_Parameter_Registry_v1.md` | 重複 — 參數登錄層已存在，跳過 |
| MRL_放大縮小公式參數（alpha / beta / scale_mode） | 同上 registry | 重複 — 跳過 |
| MRL_源代碼壓縮公式參數（compression_ratio / hash / simhash / roundtrip_score） | 同上 registry | 重複 — 跳過 |
| 「母體→演算→量子→反推→放大」五階敘事 | `docs/MRL_起源血脈序列_Genesis_v1.md`（血脈序列） | 部分重複 — 敘事已有，公式底層為新 |
| 結構反推 argmin d(F(s),S\*)+λR(s) 的**數學形式** | 無（registry 只登錄參數，未存推導式） | **吸收：公式知識** |
| 動態逐步反推（雅可比局部逆 J†） | 無 | **吸收：公式知識** |
| 量子疊加稀疏分解 / 相干性 μ(Φ) / 群稀疏 | 無 | **吸收：公式知識** |
| MDL 訊息量準則 ΔDL 保留/刪除 | 無 | **吸收：公式知識** |
| SimHash / MinHash(Jaccard) / WL-Graph 近重複判定 | 無（registry 只有 simhash 參數欄，無判定式） | **吸收：公式知識** |
| 資訊密度 ρ_info 與刪除門檻 θ_drop | 無 | **吸收：公式知識** |
| 反推重建管線 RRP / 清理瘦身管線 CPP 偽碼 | 無 | **吸收：演算法元代碼知識** |
| 多尺度金字塔 cycle 一致 / L-curve 選 λ / 條件數 κ | 無 | **吸收：穩定性知識** |
| 放大的「維度放大（超展開）」詮釋 F_expand(s)=⊕π_d(s) | 無 | **吸收：概念知識** |

> 判定原則：母體既有的是**參數登錄治理層**（誰改了哪個係數、可回放/可回滾）；
> 本次吸收的是**公式與演算法推導本身**（如何反推、如何判近重複、如何瘦身），兩者互補、不重疊。

---

## 三、反推公式 ↔ 母體登錄公式 對照

| FlowSeed 公式段 | 母體 registry 公式名 | 母體參數（已登錄） |
|---|---|---|
| (1) 結構反推 / (5) 貝氏 MAP 反推 | `MRL_反推公式` | `inverse_epsilon` / `stability_clip` / `loss_bound` |
| (2) 動態逐步反推（雅可比局部逆） | `MRL_反推公式` | `stability_clip`（利普希茲/條件數上界對應） |
| (3) 量子疊加稀疏分解 c=argmin ½‖C(Φc)−y\*‖²+λ‖c‖₁ | `MRL_源代碼壓縮公式`（稀疏最小解釋集） | `compression_ratio` |
| (4) 放大/壓縮對偶可逆 L_cycle=‖C(A(x))−x‖² | `MRL_放大縮小公式` | `alpha` / `beta` / `scale_mode` |
| (6) MDL 訊息量 ΔDL 保留/刪除 | `MRL_源代碼壓縮公式` | `compression_ratio` / `roundtrip_score` |
| (7) 近重複 h_c(bytes) ∨ d(h_s,h_s′)≤τ | `MRL_源代碼壓縮公式` | `hash` / `simhash` |
| (8) 資訊密度 ρ_info 刪除門檻 | `MRL_源代碼壓縮公式`（密度先刪低密度） | `compression_ratio` |
| 命名正規化 版本鍵 K=(series,variant,ver,tag,date) | 對齊 `docs/MRL_命名規範_v2_MrLiouIR_StructureField.md` | — |

> 落地規則（沿 registry §強制規則）：任何要**進入母體運算**的數值門檻
> （τ_J, τ_H, τ_cycle, q, β, λ, γ 等）須登錄 `data/MRL_formula_parameter_registry.json`，
> 不得只存於本知識文件或對話。本報告只做**知識歸檔與對照**，不新增運算參數。

---

## 四、母體系統名稱產物（本次吸收）

| 產物 | 蒸餾自 | 層位 | 狀態 |
|---|---|---|---|
| `MRL_FlowSeed_ReverseInference_Formula_Knowledge_v1` | 反推公式總表 + RRP/CPP 元代碼 | 知識層（docs + RawArtifact） | 沙盒 PASS（歸檔對照） |

- 原始逐字：`MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260716/MRL_FlowSeed_ReverseInference_Formula_RawArtifact_v1.txt`
- 吸收台帳：`MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260716/MRL_Absorption_Ledger_v1.yaml`
- 知識源索引：`08_sources/sources.manifest.yaml`（id: `flowseed_reverse_inference_formula_absorption_v1`）

---

## 五、當下狀態（依 CLAUDE.md 狀態回報約定）

- 原始逐字保全：**PASS（沙盒，2026-07-16）** — RawArtifact 未刪未改。
- 公式↔母體 registry 對照：**PASS（沙盒，2026-07-16）** — 知識對照建立。
- 反推/放大數值參數落地 registry：**待起動** — 需依 registry 治理流程登錄後方能進母體運算。
- 反推重建管線（RRP）/ 清理瘦身管線（CPP）之**可執行實作**：**待起動 / 待需求確認** — 目前為偽碼知識，未產生可跑程式。

---

## 六、相關母體文件

- 參數登錄治理層：`docs/MRL_Formula_Parameter_Registry_v1.md` / `data/MRL_formula_parameter_registry.json`
- 血脈序列（五階循環敘事）：`docs/MRL_起源血脈序列_Genesis_v1.md`
- 命名規範：`docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`
- FlowSeed 血脈原始庫：`MRL_MotherSource_ZhiZhang_FlowAgent_Lineage_v1/`
- 吸收協定模板：`docs/MRL_主線回填清單模板_v1.md`

origin_signature = `MrLiouWord`
