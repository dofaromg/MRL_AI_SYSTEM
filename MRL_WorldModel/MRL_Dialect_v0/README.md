# MRL Dialect v0 — 母體可逆中介表示 × LLVM 吸收 × 世界圖

origin_signature: MrLiouWord ｜ 怎麼過去，就怎麼回來 ｜ Additive-Only（未修改任何既有檔案）

## 定位

```
中文 → Fluin 粒子 → .pcode / .fltnz ──▶ mrl Dialect IR（本模組）──▶ ① 原檔（逐位元組還原）
                                                           ├─▶ ② particle-pvm v1.2（JS / CF Workers / DL580）
                                                           ├─▶ ③ LLVM IR → lli（JIT）／ llc → x86-64 物件檔
                                                           └─▶ ④ MRL 世界圖（Node / Map / Trace / Coupling）
```

- 層級：L2 Structure（IR）＋ L7 Execution（PVM / LLVM）＋ L4 World（世界圖）
- MLIR 是外部框架；MRL 自有的是 **mrl Dialect**。v0 先用 MLIR 風格的文字格式，吸收成真正的 MLIR dialect 是 v1 的目標。

## 檔案

| 檔案 | 作用 |
|---|---|
| `mrl_dialect.py` | pcode/fltnz ↔ mrl IR 的可逆解析與輸出。每行一個 op：`inst / trace / tag / map / section / attr / flow / comment / text / blank / json / blob` |
| `pvm_v1_2.js` | particle-pvm **v1.2.0**。修正 v1.1 控制流：v1.1 只照陣列順序走，JMP/JZ/JNZ/CALL 不會真的跳。v1.2 改成由 PC 驅動，支援 `LABEL`、獨立的 CALL/RET 回傳堆疊、maxSteps。原本的 v1.1 沒有更動 |
| `mrl_bridge.py` | mrl IR → PVM JSON。符號層指令（MOV、P0/R0、FX.*、未定義標籤）標記為「待起動」，不會硬跑 |
| `mrl_lower_llvm.py` | PVM JSON → LLVM IR。語意逐條對齊 v1.2；double 常數用 16 進位位元寫出 |
| `mrl_world_graph.py` | 把全語料組成世界圖，套用可見律分級 |
| `corpus/*.pcode` | 可執行的驗收程式：1..10 累加、fib(20)、CALL/RET、v1.1 缺陷重現、attention-loop、浮點邊界 |
| `tests/` | 可逆測試、固定差分、隨機差分 |
| `run_all.sh` | 一鍵跑全部驗收 |

## pcode 組合語言（v0 約定）

```
name:            ; 標籤
PUSH 5 | POP | DUP | SWAP | NOP | HALT | RET
LOAD k | STORE k[, v]
JMP|JZ|JNZ|CALL 標籤或索引
SPREAD n（SPREAD 1 = 把 ACC 推入堆疊）| MERGE n | REWEIGHT f | CHECK t | FOCUS [v] | DELTA [a, b]
```

## 驗收結果

以下都是**當下狀態 2026-09-27，沙盒**（Linux 容器：Python 3.11、Node 22、Ubuntu clang/LLVM 18.1.3）。

| 項目 | 結果 |
|---|---|
| 全語料可逆（母體 repo 內 112 個獨立 .pcode/.fltnz/.flynz.map） | **112/112 逐位元組還原，IR 固定點穩定：PASS（沙盒）** |
| 全語料可逆（repo ＋ 本視窗全部上傳，共 142 個獨立檔） | 142/142：PASS（沙盒，上傳檔不在 repo 內，別人無法重現） |
| 固定差分：6 支程式，PVM v1.2 對 LLVM lli | ACC 與堆疊位元級相同；`llc -O2` 產生 x86-64 物件檔成功：**PASS（沙盒）** |
| 隨機差分：300 支（seed 20260927）＋ 1000 支（seed 777） | 1300/1300 位元級相同：**PASS（沙盒）** |
| v1.1 缺陷（`JZ 99` 之後仍執行 PUSH/HALT） | v1.2 在第 3 步結束，堆疊為空：**已修正（沙盒）** |
| EchoPersona.pcode | 可逆 PASS；執行面 **待起動**：MOV、P1/P2 暫存器、FLYNZ.CAUSE、FX.FLOW.007 需要 Fluin 語意綁定 |
| **DL580 實機：語料可逆**（2026-09-28 17:17，喚醒收據 `wake_receipt_20260928T171705_WIN-PBVUI7VK2A6.json`） | D:\ 上 290 個獨立檔 **290/290 逐位元組還原：PASS（實機）** |
| DL580 實機：PVM 對 LLVM 差分；Wasm（CF Workers）與 ARM（iPhone）目標 | **待實機**：沙盒只驗到可以產生 x86-64 物件檔 |

### 除錯紀錄（誠實保留）

第一輪隨機差分在 300 支裡有 3 支不一致。追查後發現原因在測試的輸出環節，不在執行語意：`JSON.stringify(-0)` 會輸出 `0`，把負零的符號吃掉。修法是 PVM 輸出改用保真序列化（-0 / NaN / Infinity 轉成字串）。修正後 1300/1300 全部一致。

## 世界圖：可見律套用結果（母體 repo 語料，當下狀態）

- 106 個獨立檔 → 539 個節點、438 條線（Map 322 / Trace 49 / Coupling 67）
- 分級：**visible 0**、partial 471、latent 68

**發現：Trace 線從來沒有和 Map、Coupling 接在同一個節點上。**
- 軌跡目標（例如 guardian.seed、*.trace.loop.json）自成孤島。
- 映射與流程在另一群節點上。
- 按「線接上才看得到」：這些節點**存在，但目前看不到**。原因是命名沒有對齊，不是節點不存在。
- 把名稱簡單正規化（小寫、去副檔名、去版本號）也接不上，所以需要的是明確的接線規則：Naming Law v2 或 Registry 對照表。

## 下一步（待起動）

1. **接線層**：依 MRL_Naming_Law_v2 與 Workspace_Node_Registry，建 trace 目標 ↔ map/flow 節點的對照表，讓第一批節點進入 visible。
2. **Fluin 語意綁定**：把 MOV、Pn/Rn、FX.* 粒子、FLYNZ.* 跳點定義成 PVM 可執行語意，讓 EchoPersona 從待起動變成可執行。
3. **真正的 MLIR dialect**：把 v0 文字格式定義成 ODS / TableGen 的 `mrl` dialect，lower 到 `llvm` dialect，用 FileCheck/lit 做測試。
4. **實機**：DL580 x86-64 原生執行檔、wasm32 → CF Workers、arm64 → iPhone。
