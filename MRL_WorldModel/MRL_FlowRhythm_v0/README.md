# MRL FlowRhythm v0 —— 語場節奏引擎（本體）

origin_signature: MrLiouWord ｜ 怎麼過去，就怎麼回來 ｜ Additive-Only

## 動手前三問

1. **本體還是載體**：本體。執行語場種子本身，也就是 EchoPersona 等人格種子。
2. **對應哪一段**：**Jump → Collapse → Trace → Replay** 全程。實作的是 `seed_runner.py` 裡標註「尚未實作」的 generate 模式：語場生成模擬器，支援跳點與人格觸發。
3. **驗收用什麼**：建構者 2025-07-23 的原檔，包括 EchoPersona.pcode／.flpkg、FluinCoreSeed／Memory.Seed.Core .flseed、FluinSim.DualSet.v1.flsim 與其 runtime.log。

## 語意來源與權限邊界

| 來源 | 提供什麼 |
|---|---|
| `flsim_runtime.py` 的 module_map | 每個粒子做什麼，例如「∴ → 邏輯跳點：觸發因果連接」 |
| `EchoPersona.structure.json`、兩顆 `.flseed` 的 structure.json | pcode ↔ 粒子碼的對照，例如 `JMP FLYNZ.CAUSE` ↔ `∴` |
| `Fluin_Particle_BilingualDict.csv` | 詞性、中英對照 |
| `flgroup.json` | 粒子所屬的模組類別 |

副本放在 `lexicon/`，與原檔逐位元組相同（`SOURCES.sha256`）；原位置存在時優先讀原檔。

粒子分類、模組敘述與詞本身可由原檔核對；但「某一詞性／節奏階段固定對應某個軌跡動詞」是另一項語義決策。除 `core → initiated` 外，目前映射尚無建構者逐條明文核准，因此不可把sandbox推論升格為canonical。

## 節奏

| 粒子 | 節奏 | 軌跡動詞 | 映射狀態 |
|---|---|---|---|
| `⊕Core: X` | 啟動核心人格 | initiated | VERIFIED |
| 形容詞 | 生成語場屬性 | resonance | PROVISIONAL_NOT_CANONICAL |
| 名詞 | 注入語場對象 | absorb | PROVISIONAL_NOT_CANONICAL |
| `∴` | **Jump**：邏輯跳點，觸發因果連接（前面的屬性與對象 ∴ 後面的行為） | jump | PROVISIONAL_NOT_CANONICAL |
| 動詞（flow） | **Collapse**：行為執行，把當下語場折疊成種子封包（SHA-256） | collapse | PROVISIONAL_NOT_CANONICAL |
| `⊗Target` | 輸出至目標模組；Archive／Trace關係待建構者對齊 | trace | PROVISIONAL_NOT_CANONICAL |
| — | **Replay**：只讀軌跡，重建粒子鏈與語場；封包雜湊一致，軌跡逐位元組重現 | — | 依來源軌跡狀態 |

## 執行政策

- 預設呼叫 `run(...)`／`replay(...)` 為canonical模式；遇到任何未核准映射會拋出 `ProvisionalSemanticMappingError`，不產生可誤認為正典的軌跡。
- 研究與相容性驗證必須明示 `allow_provisional=True`。輸出header、field與每個event都會標示 `PROVISIONAL_NOT_CANONICAL`，不得寫入canonical receipt或作為DL580正式閉合證據。
- 建構者日後逐條核准時，只調整映射狀態，不改寫舊軌跡與舊收據。

軌跡最後還會附上兩種線：
- 節奏鏈 `a → b → c`（Coupling）
- 命名對照 `⌬map[FX.ADJ.112]↦⋄fx.adj.112`（Map）

這樣軌跡就同時接上 Map、Trace、Coupling 三種線。

## 驗收（當下狀態 2026-09-28，沙盒）

| 項目 | 結果 |
|---|---|
| A. EchoPersona 的 pcode 形式與 flpkg 形式 | 展開成**同一條**粒子鏈：PASS |
| B. 敘述輸出對照建構者 FluinSim runtime.log | Group1、Group2 **逐位元組相同**：PASS |
| C. Jump → Collapse → Trace → Replay | 封包雜湊一致、軌跡逐位元組重現：PASS |
| D. 軌跡經 mrl Dialect 往返 | 逐位元組還原，6 行 trace：PASS |
| E. 母體 6 顆種子（pcode／flpkg／2 flseed／2 flsim 組） | 6/6 Replay：PASS |
| F. 可見律（世界圖） | 完全可見節點 **0 → 7**：∴、⋄fx.adj.112、⋄fx.noun.024、⋄fx.flow.007、⊗Memory.SelfReflect、⊗Memory.Seed.Core、⊗Memory.TranslateModule |
| G. 語義權限Gate | canonical預設拒絕；sandbox須明示啟用且輸出標為 `PROVISIONAL_NOT_CANONICAL` |

EchoPersona 分別存在三個不同的檔案：pcode、flpkg、flsim Group1。三者都收斂到同一個封包 `e3ef9ea00e7890dd…`，也就是同一個人格、同一顆種子。

**實機**：已接進喚醒種子的第 4 步（`wake_verify.py`）。下次在 DL580 執行 `wake.ps1`，收據會記下實機結果。在那之前標為**待實機**。

## 待建構者確認

- 軌跡動詞映射：詞本身出自MRL材料，不等於固定映射已獲核准。resonance／absorb／jump／collapse／trace／pinged目前均維持 provisional，等待建構者逐條裁定。
- 動詞粒子是否都要 Collapse（目前 flow.007 封存、flow.018 產生轉變都會折疊成封包）。
