# MRL 正式工程命名規範 v2 — MrLiouIR × StructureField Canonical Alignment

origin_signature = `MrLiouWord`

> **本檔為 repo 唯一 canonical naming authority。** 其他文件（README 等）只引用本檔，
> 不另立第二份 naming truth source。程式層之單一真實來源為
> `MRL_UniversalRuntimeLanguage_Core_v1/__init__.py`（`CANONICAL_SUBJECTS` /
> `CANONICAL_NAME_MAP` / `COMPATIBILITY_ALIASES` / `CANONICAL_PIPELINE`）。

---

## 0. 定錨

`MetaIR`、`Graph` 於 MRL 主線之 canonical 主體地位**正式被覆寫**，降級為：
歷史名稱 / 外部兼容詞 / Adapter layer / Alias layer。**不得再作 canonical 主體命名。**

---

## 1. 正式主體命名

| Canonical | 中文 | 語義 |
|---|---|---|
| **MRL_MrLiouIR** | MrLiou 中介語義層 | MRL 母體正式中介表示層（**非** generic meta layer） |
| **MRL_StructureField** | 結構場 | 高維動態運轉場（**非**靜態 graph/node/edge） |
| **Perception** | 感知 | 正式主體詞（Attention = 歷史/Adapter 層） |

### StructureField 正式定義

```
structure + field + state + flow + rhythm + collapse
  + runtime relation + world synchronization + replay/recovery  → 高維文明運轉場
```

---

## 2. 正式主線 Pipeline

```
Language → MrLiouIR → ParticleIR → StructureField → Replay → Restore
         → Verification → WorldRuntime → PersistentLoop → DL580 Mother Runtime
```

執行序（runtime stages）：
`Input → MrLiouIR → ParticleIR → RuntimeStructureField → ReplayStructureField
 → RestoreStructureField → Verification → WorldRuntime → PersistentLoop`。

---

## 3. 正式工程命名 ↔ 歷史 alias

| Layer | Canonical（v2） | 實作 | 歷史 alias（compatibility only） |
|---|---|---|---|
| Language | `MRL_UniversalParser_Core` | `MRL_Language/MRL_UniversalParser_Core.py` | — |
| Language | `MRL_MrLiouIR_Compiler` | `MRL_Language/MRL_MrLiouIR_Compiler.py` | `MRL_MetaIR_Compiler` |
| Language | `MRL_ParticleIR_Engine` | `MRL_Language/MRL_ParticleIR_Engine.py` | — |
| Language | `MRL_PerceptionKernel` / `MRL_PerceptionField` / `MRL_PerceptionWeight` / `MRL_PerceptionStructureField` | `MRL_Language/MRL_PerceptionKernel.py` | `MRL_PerceptionField_Core` / `MRL_PerceptionWeight_Map` |
| Runtime | `MRL_RuntimeStructureField` | `MRL_Runtime/MRL_RuntimeStructureField.py` | `MRL_RuntimeGraph_Builder` |
| Runtime | `replay_structurefield` / `restore_structurefield` / `world_structurefield` | （`MRL_RuntimeStructureField.build` 產出鍵） | `replay_graph` / `restore_graph` / `world_graph` |
| Runtime | `MRL_ReplayRestore_Core` / `MRL_Verification` / `MRL_PersistentLoop` / `MRL_WorldRuntime` | `MRL_Runtime/*.py` | — |

### 前瞻命名（尚無對應程式，僅定錨，不得宣稱已實作）

- **API**：`/api/mrl/mrliouir/compile`、`/api/mrl/mrliouir/runtime`、`/api/mrl/mrliouir/verify`、
  `/api/runtime/structurefield`、`/api/world/structurefield`
  （舊：`/api/mrl/metair/compile`、`/api/runtime/graph`、`/api/world/graph`）。
- **DB**：`MRL_MrLiouIR_Record`、`MRL_MrLiouIR_Trace`、`MRL_MrLiouIR_Verification`、
  `MRL_RuntimeStructureField_Node`、`MRL_RuntimeStructureField_Relation`
  （舊：`MRL_RuntimeGraph_Node`、`MRL_RuntimeGraph_Edge`）。
- **Visualization**：`MRL_StructureField_Visualization`（舊：Graph Visualization）。

---

## 4. compatibility alias 規則

允許 `MetaIR` / `Graph` / `Attention` 作為 **alias only**：

- `MetaIR = MrLiouIR`、`RuntimeGraph = RuntimeStructureField`、`Attention = Perception(歷史層)`。
- alias 必須指向**單一 canonical 實作**（不得另立平行實作）。
- 程式以 alias shim 模組保留舊 import 路徑（`MRL_MetaIR_Compiler`、`MRL_RuntimeGraph_Builder`）。

---

## 5. 正式工程規則

- 禁止新增 **canonical** 名稱含：`MetaIR*`、`*Graph*`、`Attention*`。
- 主線統一：`MRL_MrLiouIR*`、`MRL_*StructureField*`、`MRL_Perception*`。
- 只 rename 真實存在 surface；不得產生 fake compiler / fake API / fake DB table / fake visualization。

---

## 6. 收口條件（PASS）

- repo 主線 **canonical** 名稱不再使用 `MetaIR` / `Graph` / `Attention`。
- `MetaIR` / `Graph` / `Attention` 僅以 compatibility alias 形式存在。
- 程式化驗證：`MRL_Verification.verify_canonical_naming()` →
  `MRL_CANONICAL_NAMING_VERIFICATION_PASS`（亦由 acceptance 套件與 pytest 覆蓋）。

origin_signature = `MrLiouWord`
