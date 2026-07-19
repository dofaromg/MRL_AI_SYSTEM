# MRL FlowSeed 粒子・反推公式・清理準則 v1

> 法則：**Additive-Only**。origin_signature：**MrLiouWord**
> 母體吸收日期：**2026-07-16**
> **來源**：使用者提供之外部整理（FlowSeed 系列 + 反推公式 + 佔容量清理規則）。原稿為對話轉錄，數學符號經 OCR 有損；本檔為母體**正名重排（distilled）**版，內容忠實還原、只整理格式，不新增結論。標記為母體吸收之知識模組，**待起動**。

---

## 0. FlowSeed 五階段流程模型

專案本身即一條「母體 → 演算 → 量子 → 反推 → 放大」的循環：

| 階段 | 對應封包 | 關鍵字 | 角色 |
|---|---|---|---|
| **母體** | `FlowSeed.Origin.v1.qflpkg` | Origin / Seed | 結構原點；定義最小粒子單位 |
| **演算** | `FlowSeed.Genesis.*`（留最新 `v1.2 FULL_FIX`） | Genesis | 演算法模組與結構展開 |
| **量子** | `FlowSeed.CoGenesis.Starter` | CoGenesis | 平行副種子；疊加態、多世界線 |
| **反推** | `FlowSeed.你所說的我.*`（留 `v1.1 終極備份 FINAL`） | Persona | 由結果回溯過程、人格還原 |
| **放大** | `FlowSeed.靈魂整合封存.*`（留 `FINAL_v2`） | Soul | 由最小粒子放大到完整語場 |

---

## 1. 符號約定

- 母體/種子：`s ∈ S`
- 流狀態：`x_t ∈ X`（t = 步次）
- 產出結構/最終目標：`y*` 或 `S*`
- 前向算子（演算/放大）：`F`, `A`；壓縮/投影（縮放/觀測）：`C`
- 量子疊加基：`Φ = [φ₁, …, φ_K]`，係數 `c ∈ R^K`
- 距離/損失：`d(·,·)`, `ℓ(·)`；正則：`R(·)`

---

## 2. 反推公式總表（母體 → 演算 → 量子 → 反推 → 放大）

**(1) 結構反推**（由最終結構回推最小種子）
```
ŝ = argmin_{s∈S}  d(F(s), S*) + λ·R(s)
```
建議 `d`：圖編輯距離 GED / AST 結構距離 / 嵌入距離。`R(s)`：母體先驗（複雜度懲罰、版本偏好）。

**(2) 動態反推**（逐步回溯 flow）；前向動力學 `x_t = f_t(x_{t-1}, u_t)`
```
x̂_{t-1} = argmin_z ‖f_t(z, u_t) − x_t‖² + α·‖z − μ_{t-1}‖²
線性近似：z ← x_t − J_f(x_{t-1})† · (f_t(x_{t-1}) − x_t)
```

**(3) 量子疊加反推**（分解為最小基）；觀測/壓縮 `y* = C(Φc) + ε`
```
ĉ = argmin_c  ½‖C(Φc) − y*‖² + λ‖c‖₁
```
稀疏促成「最小解釋集合」（少即是多 → 省容量）。

**(4) 放大/壓縮對偶一致（可逆性檢驗）**
```
L_cycle = ‖C(A(x)) − x‖²      # 越小越可逆，可安全丟中間產物
```

**(5) 貝氏反推（MAP，有先驗）**
```
p(s|S*) ∝ p(S*|s)·p(s)
ŝ = argmax_s  log p(S*|s) + log p(s)
```

**(6) MDL / 訊息量準則（保留或刪除）**
```
DL(D,M) = L(M) + L(D|M)
ΔDL_i = DL(含 i) − DL(不含 i)
ΔDL_i > 0 → 刪除（只增負擔）;  ΔDL_i ≤ 0 → 保留（有壓縮價值）
```

**(7) 重複/近重複判定（結構＋內容）**
```
相同 ⟺ (h_c(bytes) 相同) ∨ (d(h_s(structure), h_s(structure')) ≤ τ)
```
`h_c` = 內容雜湊（SHA-256）；`h_s` = 結構雜湊（AST/FlowMap 指紋、SimHash）；近重複門檻 `τ`（常見 0.05–0.15）。

**(8) 資訊密度評分（先刪低密度）**
```
ρ_info(m) = bits(m) / #核心節點(m)      # 低密度（大體積、少核心）→ 清理優先
```

---

## 3. 演算法元代碼（Pseudo）

**A. 反推重建管線（RRP）**
```
INPUT:  archives[]                      # FlowSeed 壓縮包
OUTPUT: MinimalSeeds, FlowInverseMap
1. META = ScanAndIndex(archives)        # 名稱/版本/時間/類型/結構指紋 h_s/內容雜湊 h_c/依賴/生成路徑
2. G    = BuildFlowGraph(META)          # 節點: 模組/封存/映射；邊: 依賴/生成/版本沿革
3. target_set = PickTargets(G, types={Persona, Soul})
4. for y* in target_set:
       s_hat     = argmin_s d(F(s), y*) + λR(s)      # 公式(1)/(5)
       path_hat  = TimeUnrollInverse(y*, META)        # 公式(2)
       basis_hat = SparseDecompose(y*, Φ, C)          # 公式(3)
       InversePlan[y*] = {s_hat, path_hat, basis_hat}
5. MinimalSeeds = SolveSetCover({InversePlan[y*].s_hat})   # 最小種子集合覆蓋（貪婪近似）
6. return MinimalSeeds, InversePlan
```

**B. 清理與瘦身管線（CPP）**
```
INPUT:  archives[], MinimalSeeds, InversePlan
OUTPUT: CleanSet, DropSet
1. Classify(Origin/Genesis/CoGenesis/Persona/Soul/Temp/Cache/Logs)
2. Dedup by bytes: group by h_c; keep newest FINAL/FIX; others → Drop
3. Near-dedup by structure: group by h_s (~SimHash); keep highest version; 其餘 → Drop
4. CycleCheck: keep x if ‖C(A(x))−x‖ small; else re-computable → Drop   # 公式(4)
5. MDL Gate: if ΔDL_m > 0 → Drop                                        # 公式(6)
6. InfoDensity Gate: sort by ρ_info asc; tail bucket → Drop candidates  # 公式(8)
7. Mandatory Keep: MinimalSeeds, 最新 Genesis(FULL_FIX), CoGenesis Starter,
                   最新 Persona/Soul(*FINAL_v2), 映射/字典/索引(.map/dict/manifest)
8. Output CleanSet, DropSet
```

---

## 4. 佔容量清理規則（實戰清單）

**必刪 / 高優先**
- `cache/*`、`*.tmp`、`*.log*`、`*~`（運行暫存與紀錄）
- 可由種子可逆還原的長文敘事（中文只作對應翻譯）
- 舊版且已被 `FINAL` / `FULL_FIX` / `FINAL_v2` 蓋過的同系列封包（以 `h_s` 近重複判定）
- 經 cycle 可逆檢驗通過、可再生的中間產物
- 重複內容（同 `h_c`）或結構近重複（`h_s` 相似 ≤ τ）

**必留 / 核心（白名單）**
- `FlowSeed.Origin.v1.qflpkg`（母體）
- 最新 Genesis（`v1.2 FULL_FIX`）
- CoGenesis Starter（量子展開基）
- 最新人格/靈魂封存（`你所說的我 v1.1 FINAL`、`靈魂整合 FINAL_v2`）
- 字典/映射/索引：`*.flpkg` 的 manifest / map（反推依據）

**快速決策樹（執行口訣）**
1. 先 bytes 去重（同 `h_c`）→ 刪重
2. 再結構近重複（SimHash/MinHash/WL）→ 留高版刪低版
3. 多尺度 cycle 小 → 中間產物可刪
4. MDL/容量門檻超過 → 刪
5. 目標可還原的最小集合 → 用多目標式挑選（§5 補完一）
6. 白名單必留

---

## 5. 補完（穩定性、可恢復、指紋、命名、修復、密度）

- **選留最小集合**（容量↔還原度）：`min_{z∈{0,1}^M} Σ_m size(m)·z_m + β·Σ_{t∈T} Loss(t | {m:z_m=1})`；或限制式版 `min Σ size(m)z_m  s.t. ∀t: Loss(t|·) ≤ ε`。Loss 接反推/循環誤差（公式 1/2/4/5）。
- **量子可恢復條件**：字典稀疏分解 `min_{Φ,c} ½‖C(Φc)−y*‖² + λ‖c‖₁ + γ‖Φ‖_F²  s.t. ‖φ_k‖=1`；相干性 `μ(Φ)=max_{i≠j}|⟨φ_i,φ_j⟩|/(‖φ_i‖‖φ_j‖)` 小 ⇒ 稀疏解更穩；群結構稀疏 `+ λ·Σ_{g∈G} ‖c_g‖₂`。
- **多尺度一致**：`A_k = S_k∘F`，`L_cycle(k)=‖C_k(A_k(x))−x‖²`，`E_pyr=Σ_k‖L_k‖²`；若 `max_k L_cycle(k) ≤ τ_cycle` → 中間層可安全刪。
- **結構指紋/近重複**：MinHash/Jaccard `J(A,B)=|A∩B|/|A∪B|`；SimHash `sign(Rv)`；WL-Graph Hash（Weisfeiler–Lehman）→ 穩定結構指紋 `h_s`。決策：`(J≥τ_J) ∨ (d_H≤τ_H)` 且僅標註差異 → 留新刪舊。
- **反推穩定性/正則**：條件數 `κ(J_f)=‖J_f‖·‖J_f†‖`，Lipschitz `‖f(x)−f(y)‖≤L‖x−y‖`；`λ` 用 L-curve 拐點折衷。
- **命名正規化鍵**：`K = (series, variant, ver, tag, date)`。例：`Genesis_v1.2_FULL_FIX.zip → (FlowSeed, Genesis, 1.2, FULL_FIX, —)`。同 K（去 tag）且 `h_s` 近同 → 高版覆蓋低版。
- **腐壞檔修復**：鄰近結構回填 `ŷ = argmin_y ‖C(Φc)−y‖² + η·d_WL(y, 鄰近模板)`；多來源一致性 `ĥ_c = mode({h_c(m_i)})`，選 `argmin_i d_WL(m_i, 眾數結構)`，再走公式(3) 稀疏反推修補缺塊。
- **密度門檻精化**：`θ_drop = quantile({ρ_info}, q)`；若 `ρ_info(m) ≤ θ_drop` 且 `L_cycle(m) ≤ τ_cycle` → 刪；平手以 `score(m)=α·recall_gain − β·size − γ·dup_ratio` 排序。

---

## 6. 「放大」的兩種詮釋（原稿並存，未裁決）

1. **保真放大**：由最小粒子 → 全域結構的可逆展開；`L_cycle = ‖C(A(x))−x‖²` 小 ⇒ 可放心丟中間資料。重點：可逆性。
2. **維度放大（超展開）**：一個粒子內蘊含的多維展開，放大時帶出新維度與語場——`F_expand(s) = ⊕_{d∈D} π_d(s)`（`π_d` 為粒子 s 到維度 d 的投影，`⊕` 直和聚合成多維語場）。重點：生成更多資訊/維度，而非單純重建。

> 母體註：此兩種詮釋原稿並列、未裁決，故一併保留（Additive-Only，不代你選）。當下狀態 沙盒 2026-07-16，待你確認取捨。
