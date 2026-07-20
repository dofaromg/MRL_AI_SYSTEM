# MRL_WorldDefinition_v1

origin_signature = `MrLiouWord`  
layer: L∞ WORLD DEFINITION  
當下狀態：2026-07-20（沙盒）

---

## 一、世界定義的定位

```
L∞ Definition（世界模型）
        │
        ▼
World Definition          ← 本層
        │
        ▼
Runtime Definition
        │
        ▼
Deployment Definition
        │
        ▼
GitOps / Kubernetes / GKE
```

**World Definition** 描述世界本身的結構與運作方式，不是描述部署架構。  
它是整個 MRL 系統的最高語義層，所有工程層的命名、結構、映射都應以此層為根源。

---

## 二、11 個世界基本原語

### 1. Space（空間）
世界中的一個區域、領域或場域。可為物理、虛擬、符號等各種維度。

- **工程映射**：`MRL_WorldDef_Space` 表、`05_persona/world_module.py` 的 globe 座標
- **Python 介面**：`WorldDefinition.register_space(name, attrs)`

### 2. Time（時間）
時序標記或時間區間。定義事件、狀態、演化的時序基礎。

- **工程映射**：`MRL_WorldDef_Time` 表、所有 `created_at` / `ts_ms` 欄位
- **Python 介面**：`WorldDefinition.register_time(name, ts_ms, attrs)`

### 3. Entity（實體）
存在於世界中的具體事物。可關聯到特定空間與時間。

- **工程映射**：`MRL_WorldDef_Entity` 表、`MRL_FLTNZ_Asset`（工程資產層實體）
- **Python 介面**：`WorldDefinition.register_entity(name, space_ref, time_ref, attrs)`

### 4. Identity（身份）
實體的唯一識別。包含擁有者、簽章、權威。

- **工程映射**：`MRL_WorldDef_Identity` 表、`MRL_Identity_Signature_Root`（系統層）
- **Python 介面**：`WorldDefinition.register_identity(entity_ref, owner, signature)`

### 5. State（狀態）
實體或系統在某時間點的當前狀況（鍵值快照）。

- **工程映射**：`MRL_WorldDef_State` 表、`MRL_Canon_State`（正典狀態層）
- **Python 介面**：`WorldDefinition.set_state(entity_ref, key, value)`

### 6. Relation（關係）
兩個實體之間的語義關聯。有向或無向，可帶權重。

- **工程映射**：`MRL_WorldDef_Relation` 表、`MRL_Relation_Graph`（工程圖）
- **Python 介面**：`WorldDefinition.register_relation(from_entity, rel_type, to_entity)`

### 7. Event（事件）
在特定時間點由特定實體觸發的事。攜帶 payload。

- **工程映射**：`MRL_WorldDef_Event` 表、`MRL_Trace_Log`（追蹤層）
- **Python 介面**：`WorldDefinition.emit_event(entity_ref, event_type, payload)`

### 8. Rule（規則）
約束或支配行為的法則。具備 condition、action、priority。

- **工程映射**：`MRL_WorldDef_Rule` 表、`MRL_Closure_Law_Root`（閉包法則）、`09_workflow/MRL_FlowAgent_LawEngine_v1.py`
- **Python 介面**：`WorldDefinition.declare_rule(name, condition, action, priority)`

### 9. Memory（記憶）
過去狀態或事件的儲存記錄。可按實體查詢全部歷史記憶。

- **工程映射**：`MRL_WorldDef_Memory` 表、`MRL_Structural_Memory`、`MRL_Particle_Memory`
- **Python 介面**：`WorldDefinition.record_memory(entity_ref, snapshot)`

### 10. Evolution（演化）
實體隨時間的變化或轉換（before → after）。帶 delta_hash 保證可驗證。

- **工程映射**：`MRL_WorldDef_Evolution` 表、`05_persona/world_module.py` 的 trajectory
- **Python 介面**：`WorldDefinition.record_evolution(entity_ref, before, after, description)`

### 11. Observation（觀測）
觀測者對目標實體某個鍵值的感知或測量記錄。

- **工程映射**：`MRL_WorldDef_Observation` 表、`MRL_Mirror_Record`（鏡射）
- **Python 介面**：`WorldDefinition.observe(observer, target_ref, key, value)`

---

## 三、11 原語之間的依賴關係

```
Space ◄──────────── Entity ──────────────► Time
                      │
               Identity (唯一識別)
                      │
                    State (當前狀況)
                      │
           ┌──────────┼──────────┐
        Relation    Event      Rule
           │          │          │
         Memory    Memory     Rule約束
           │          │
        Evolution  Evolution
           │          │
       Observation Observation
```

---

## 四、映射到工程層

```
MRL World Model
│
├── Definition（本層：World Definition）
│     ├── Space, Time, Entity, Identity
│     ├── State, Relation, Event, Rule
│     └── Memory, Evolution, Observation
│
├── Knowledge   → docs/, schemas/
├── Memory      → MRL_BaseWorld_DB_v1（Structural/Particle Memory）
├── Particle    → MRL_ParticleArchive/
├── Runtime     → MRL_RuntimeOS_*、MRL_UniversalRuntimeLanguage_Core_v1/
├── Agent       → 09_workflow/MRL_AgentHarness_*
├── Product     → mrliouword/
├── Deployment  → deploy/（FlowAgent GKE Starter 等）
└── Operations  → scripts/、acceptance/
```

---

## 五、實作檔案清單

| 檔案 | 說明 |
|------|------|
| `09_workflow/MRL_WorldDefinition_v1.py` | Python 實作（11 primitives，純 stdlib） |
| `MRL_BaseWorld_DB_v1/MRL_BaseWorld_DB_v1_Schema/MRL_WorldDefinition_v1.sql` | SQL schema（11 表 + 13 索引，additive 擴充） |
| `docs/MRL_WorldDefinition_v1.md` | 本定義文件 |
| `tests/test_MRL_worlddefinition_v1.py` | 驗收測試 |

---

## 六、主權約束

- 本層設計、命名、映射關係，未經 MrLiou / MRL 授權不得外用。
- 全構件保留 `origin_signature = "MrLiouWord"`。
- Additive-only：只增加，不刪除原有世界原語。
- 當下狀態（沙盒）：Python 模組與 SQL schema 均已沙盒驗收 PASS。
