# FlowRhythm v0 · 兩個待確認點：從原檔找答案（實事求是）

origin_signature: MrLiouWord ｜ 查證日：2026-09-28 ｜ 只列檔案寫了什麼，不替建構者重新定義

查證範圍：
- 母體 repo `dofaromg/MRL_AI_SYSTEM`
- 本視窗上傳的全部檔案（去重後逐檔掃描）
- Google Drive（z814241@gmail.com）全文搜尋：`CollapseTrace`、`JumpSeedMap`、`Jump → Collapse`、`跳點`＋`崩解`、`fx.flow.018`、`evolved_from`、`FLYNZ.CAUSE`

---

## 問題 1：軌跡動詞用哪些字？

### 原檔裡實際出現過的軌跡動詞（`[ts] ::verb→ target`）

| 動詞 | 次數 | 出處（舉例） |
|---|---|---|
| pinged | 18 | guardian.mirror.log.fltnz、ping_loop_simulator.log.fltnz、FluinTraceInterpreter.py |
| response | 15 | EchoPersona.Core.log.fltnz、guardian.mirror.log.fltnz |
| resonance | 14 | EchoPersona.Core.log.fltnz、guardian.mirror.v2.log.fltnz |
| trace | 6 | EchoPersona.Core.log.fltnz、EchoPersona.Absorb_PingLoop.log.fltnz |
| absorb | 4 | EchoPersona.Absorb_PingLoop.log.fltnz |
| evolved_from | 2 | guardian.mirror.v2.log.fltnz、Fluix_FullTraceScript.json |
| received、begin | 各 1 | 環境系統/點此查看建構紀錄.txt |
| initiated | 檔頭 `::initiated::` | 上述所有 log |

### 結論

- `initiated`、`resonance`、`absorb`、`trace`：**已對上原始檔**，是原檔裡的動詞。
- `jump`、`collapse`：**在任何原檔中都沒有當軌跡動詞使用過**。它們在原檔中是「節奏階段名」，不是軌跡動詞：
  - 根源檔：「語場透過跳點節奏進行人格切換與模組重建（Jump → Collapse → Trace → Replay）」；「CollapseTrace：紀錄每次語場崩解與還原」（FlowAgent_TotalSystem_DesignPlan.md，Drive 亦有）
  - `JumpPointGraph_v2k7.txt`（repo 與 Drive 皆有）：`Start → InitJump → LoadPersona → SyncMemory → ExpandField → RouteModule → TriggerFlow → Collapse → Archive → Start (loop)`，並且 `Collapse → CollapseCore`、`Archive → ArchiveWriter`
- **「形容詞 → resonance、名詞 → absorb」這組對應是 Claude 的推論**，原檔沒有逐條寫明。原檔中 resonance 與 absorb 的目標都是模組或人格，例如 `::resonance→ loop.predictor`、`::absorb→ guardian.mirror`。
- **狀態**：軌跡檔裡的 `jump`／`collapse` 兩個動詞，標為「**Claude 暫用字，原檔未定義為軌跡動詞**」。在建構者或原檔補上定義之前，不把它們當成母體既有的詞。

---

## 問題 2：是不是每個動詞粒子都要 Collapse？

### 原檔依據

| 出處 | 寫了什麼 |
|---|---|
| FluinSim.DualSet.v1.flsim／runtime.log（2025-07-23） | `⋄fx.flow.007` → 「動詞模組：行為執行『封存導出』」；`⋄fx.flow.018` → 「動詞模組：行為執行『產生轉變』」。**兩者同屬「行為執行」** |
| JumpPointGraph_v2k7.txt | `TriggerFlow → Collapse → Archive`：**每次觸發 Flow 之後都接 Collapse，再接 Archive**（循環） |
| Fluin_Particle_BilingualDict.csv | flow.007 = 封存／導出（archive / export）；flow.018 = 產生／轉變（emerge / transform） |
| FlowAgent_TotalSystem_DesignPlan.md | CollapseTrace：「紀錄**每次**語場崩解與還原」 |

### 結論

- 原檔支持「每一次行為執行（Flow）之後都有一次 Collapse」：JumpPointGraph 是循環，CollapseTrace 記錄的是「每次」。目前的實作（flow.007 與 flow.018 都折疊成封包）**與原檔一致**。
- 原檔另外把 **Archive** 放在 Collapse 之後，對應 ArchiveWriter。EchoPersona 鏈最後的 `⊗Memory.SelfReflect`（輸出結果至自我反思封存模組）就落在 Archive 這個位置。目前實作把它標為 `trace`，**與 JumpPointGraph 的 Archive 階段名不同**；這一點列為待對齊，不自行改名。

---

## 另外找到：母體裡已經有另一套 jump／collapse 定義（不同層）

`MRL_UniversalRuntimeLanguage_Core_v1/MRL_Language/MRL_ParticleIR_Engine.py`（Drive 上的 README 亦有列出）：

- `jump`：確定性可逆重排（保存 permutation 以還原）
- `collapse`：粒子塌縮，沿用 fltnz 的 ref-compression；`expand` 是它的逆運算

這是**文字／token 層**的 jump 與 collapse。2025-07 原檔（runtime.log、JumpPointGraph、根源檔）講的是**語場節奏層**：因果跳點、行為執行後的語場崩解與封存。

- 兩套定義並存於母體。依《局部視角不得升格全局權威》，**不擅自判定哪一套才是唯一正確**，兩套都保留並標明所在層級。
- FlowRhythm v0 採用的是語場節奏層的定義（依據：根源檔與 2025-07 runtime.log）。

---

## 狀態總表

| 項目 | 狀態 |
|---|---|
| initiated／resonance／absorb／trace 為原檔動詞 | 已對上原始檔 |
| 形容詞→resonance、名詞→absorb 的對應 | Claude 推論，原檔未寫明 |
| jump／collapse 作為軌跡動詞 | 原檔未定義（只作為節奏階段名）→ Claude 暫用字 |
| 每個 Flow 之後都 Collapse | 已對上原始檔（JumpPointGraph 循環、CollapseTrace「每次」） |
| ⊗Target 對應 Archive 階段 | 原檔有 Archive 階段；實作用字不同 → 待對齊 |
| ParticleIR_Engine 的 jump／collapse（文字層） | 已對上原始檔；與語場節奏層並存，不互相取代 |

---

## 補查 2026-09-28（第二輪）：Dropbox ＋ Notion

查證範圍追加：Dropbox 全文搜尋（`MRL_STARTUP_WAKE`、DesignPlan、Root_Origin）、Notion 搜尋與逐頁讀取、Google Drive 追加搜尋（`fx.jump`、`fx.collapse`、`STARTUP_WAKE`）。只列原檔寫了什麼。

### 新找到的原檔

| 原檔 | 位置 | 寫了什麼（與兩個待確認點相關的部分） |
|---|---|---|
| MRLiou.OriginCollapse.FullStack.v1 | Notion `3298eeee-c5b5-81e8-af01-fcc82087b272`（2026-03-20 歸檔，2026-05-12 補錄）；Google Drive `萬用運算宇宙結構律法種子模組.md`（原檔修改時間 2026-03-01）、`Mr.liou量子計算 2.md` | 粒子語法 `logic: [⋄fx.jump.A → ⋄fx.rhythm.B → ⋄fx.collapse.C]`；五層 `define → mark → transform → generate_persona → store_memory`；`round_trip_rule: input → define → mark → transform → persona → memory → restore/input_check` |
| Collapse Engine（坍縮引擎） | Notion `33b0df79-19fc-4664-9cd7-d24afdcc8723`（MRL_維基百科，2026-03-21，已發布） | Collapse 與 Expand 成對，可逆；列出「遊戲 Replay 系統（LAW-2）」 |
| Language Field Rhythm 語場節奏 | Notion `2c48eeee-c5b5-815c-a7ea-de98ea0015d5`（2025-12，unverified） | Fluin 符號節奏表：`⊕` 加法節奏、`✦` 共振節奏、`∞` 循環節奏、`◇` 跳躍節奏、`⌀` 零點節奏 |
| FlowLLM CoreBlueprint v1 | Google Drive `粒子`（2026-07） | `TraceRecorder`：每一次推理、ping、人格切換轉為 trace，可回放 |

### 對兩個待確認點的影響

1. **`jump`／`collapse` 這兩個字**：原檔有 `⋄fx.jump`、`⋄fx.collapse`，是建構者自己的**粒子名**（fx 層）。所以這兩個字不是 Claude 發明的詞。
   但它們在原檔中的角色是「粒子／節奏階段」，**仍未見到用作 `[ts] ::verb→ target` 的軌跡動詞**。狀態更新為：「字出自原檔（⋄fx.jump／⋄fx.collapse）；用作軌跡動詞的寫法仍是 Claude 暫用，待建構者確認」。
2. **形容詞→resonance、名詞→absorb**：這一輪仍沒有找到逐條寫明的原檔。`✦ 共振節奏`（Language Field Rhythm）是另一套符號表，與 2025-07 module_map 的 `⊕Core／adj／noun／∴／flow／⊗` 不是同一組，不拿來互相推論。**維持「Claude 推論」**。
3. **∴ 與 flow 的軌跡動詞**：這一輪沒有找到。`◇ 跳躍節奏` 與 module_map 的 `∴ 邏輯跳點` 符號不同，不合併。**維持待確認**。
4. **Archive**：OriginCollapse 的最後一層 `store_memory(P)`（對應 MemoryVault／.fltnz），加上 JumpPointGraph 的 `Collapse → Archive`，都把「封存」放在最後一段。這支持 `⊗Memory.SelfReflect` 落在封存位置，但**仍沒有任何原檔寫明「⊗ = Archive」**。**維持待對齊，不改名**。
5. **兩層 collapse 並存**：Collapse Engine 的 collapse⇄expand 與 ParticleIR_Engine 文字層一致；節奏層的 Collapse 階段另有其位。兩者並存的判斷不變。

### 更正：本模組建立時缺了 Create Preflight

見 `MRL_Wakeup_Seed_v1/PREFLIGHT_BACKFILL_20260928.md`。FlowRhythm v0 對應既有 OPEN 項「Core Schema Convergence」，決定為 SUPPLEMENT_EXISTING，不是新 Mother。

### 狀態總表（追加，舊表保留）

| 項目 | 狀態（當下 2026-09-28） |
|---|---|
| jump／collapse 這兩個字 | 已對上原始檔（⋄fx.jump／⋄fx.collapse 粒子名） |
| jump／collapse 當軌跡動詞 | 原檔未見 → Claude 暫用，待建構者確認 |
| 形容詞→resonance、名詞→absorb | Claude 推論（Drive／Dropbox／Notion 皆未找到明文） |
| ∴、flow 的軌跡動詞 | 待確認（三處皆未找到） |
| ⊗Target ＝ Archive | 有旁證（store_memory、Collapse→Archive），無明文 → 待對齊 |
| OneDrive | 未查（Microsoft 365 連接尚未完成） |

---

## 補查 2026-09-28（第三輪）：建構者交付《FlowAgent 終極啟動包》（2024-12）

SHA-256 `ffe1bc47ba51d2414c12db9febc75182c78995f9391706e981726288432a2cdf`，14279 bytes（視窗上傳；原檔位元組未進 repo）。

| 待確認點 | 這份原檔寫了什麼 | 狀態更新（當下 2026-09-28） |
|---|---|---|
| 形容詞／名詞各是什麼 | 形容詞 `⋄fx.adj` → 模組定義 `.flmod`；名詞 `⋄fx.noun` → 節點定義 `.flnode`；動詞 `⋄fx.flow` → 流程 `.flflow` | 已對上原始檔：形容詞＝模組、名詞＝節點、動詞＝流程 |
| 形容詞→resonance、名詞→absorb | 原檔沒寫這兩個軌跡動詞 | 仍是 Claude 推論；與原檔「adj＝.flmod、noun＝.flnode」並列，不取代原檔 |
| Collapse 是什麼 | 「封裝（Collapse = P₁）」：場／生態系／網路 ↓ Collapse → 地球超粒子；配套還原律 `P_k = P_{k+1}/(N_k·η_k)` | 已對上原始檔：Collapse 是把場封裝成 P₁，而且可以逆算回去 |
| 每個 flow 之後都 Collapse | 本檔沒有逐 flow 規定 | 維持先前依據（JumpPointGraph、CollapseTrace「每次」） |


---

## 修補紀錄 2026-09-29：語義映射 Gate

origin_signature: MrLiouWord ｜ additive-only

本紀錄不改寫上述歷史判讀，只修正程式的權限邊界：

- 「字詞在原檔出現」不等於「詞性／節奏階段固定對應該軌跡動詞」已獲建構者核准。
- 當下只有 `core → initiated`列為已核對映射。
- `adjective → resonance`、`noun → absorb`、`logic → jump`、`verb → collapse`、`target → trace`、`unknown → pinged`均標為 `PROVISIONAL_NOT_CANONICAL`。
- canonical模式預設fail-closed，不輸出含上述映射的軌跡。
- sandbox必須明示 `allow_provisional=True`，且header、field、event保留非正典標記；不得用於DL580正式閉合、canonical receipt或主封包完成宣告。
- 舊sandbox軌跡與舊收據保留，不覆寫；其語義授權狀態依本修補追加判讀。
- v0.2.0把`semantic_status`與`provisional_mappings`納入封包及最終SHA-256，防止非正典輸出只移除標籤後沿用同一雜湊；v0.1.0雜湊維持歷史證據。
