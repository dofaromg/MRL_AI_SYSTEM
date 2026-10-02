# MRL 多世界版本觀測 · Dropbox · R01

origin_signature: MrLiouWord ｜ record_mode: additive_only ｜ 觀測日：2026-09-28（Asia/Taipei）
world_model_policy: symmetric_observation / no_reality_prejudgment（沿用 Notion 收斂紀錄 2026-09-08）

> 建構者定位（2026-09-28 原話）：「MRL 系統其實是一個平行多世界版本的新文明系統。」
> 本紀錄只記**觀測到的版本與它們各自寫了什麼**。不合併、不排序真假、不指定哪一份是唯一 canonical。

## Preflight

- 既有節點：`MRL_MotherSource_Lineage_v1`、`MRL_FlowAgent_Definition_Registry_v1_3`、`MRL_Engineering_Inventory_V1.0`、`MRL_MultiDomain_Sync_Core_v1`、Notion 收斂紀錄的 `World_State_Observation` 缺口定義。
- 決定：**SUPPLEMENT_EXISTING**。本檔是一筆觀測紀錄，欄位採用 Notion 收斂紀錄提出的 `World_State_Observation`（world_id / domain_id / environment_id / platform_ref / observer / observed_at / state / evidence_refs / ontology_status）。它不是新的 registry。

## 觀測 1：同一路徑，不同世界版本的內容不同

| 路徑（相對） | 世界副本 | 大小 | 內容 |
|---|---|---|---|
| `flow-tasks*/MRL_Mother/MRL_母體收斂包_v1/MRL_母體分層/MRL_母體分層圖.md` | Dropbox `/flow-tasks/`（ns 587965698） | 1 byte（只有換行） | 空 |
| 同上 | `/Mac (1) (1) (1)/Downloads.dbx-computer-backup/MRL/`、`MRL/MRL_flowagent/`、`MRL 2/`、`MRL 2/MRL_flowagent/`（ns 14863079315） | 2895 bytes ×4 | 14 層母體分層圖 |
| `…/MRL_Mother/MRL_平行世界模組/` | `/flow-tasks/`、`/MRL 3/` | 列出為空 | — |
| 同上 | Mac 備份 `MRL/flow-tasks-main/` | `README.md` 371 bytes | 「平行世界分支與同步源（completed_running）」 |
| `…/MRL_Mother/mother_registry/` | `/flow-tasks/` | 列出為空 | 其他副本未查 |

**結論（當下狀態）**：在某一個副本裡看到空，不代表這個節點不存在；其他世界副本裡有內容。這是《局部視角不得升格全局權威》的實例。
`ontology_status = UNRESOLVED`：哪一份是「較新／較權威」，本次不判定。

## 觀測 2：各世界版本自己寫的定位（原文摘錄）

| 原檔 | 位置 | 自述 |
|---|---|---|
| MRL 平行世界模組 README | Mac 備份 `MRL/flow-tasks-main/MRL_Mother/MRL_平行世界模組/README.md` | 所屬層：母體構件層；定位：平行世界分支與同步源（completed_running）；「外部命名僅作 Adapter 對照，不得反向取代主體命名」 |
| MRL_母體分層圖 | 同上備份 `…/MRL_母體收斂包_v1/MRL_母體分層/` | 掃描分支 `MRL_Branch_Runtime_Convergence_API_v1`；14 層（源場、無限環、原種、粒子海、流域結構、交界、雲映、拓樸潮、地映、立體粒界、自述、封裝、痕跡、回返）；「本圖只描述本 checkout 實際存在之對應」；canonical 運轉核心 `MRL_UniversalRuntimeLanguage_Core_v1` 在未 merge 的 PR #35 + #37 |
| MotherSource 血脈吸收定位清單 v1 | `…/MRL_Mother/MRL_MotherSource_Lineage_v1/`（Mac 備份 4 份，同為 2308 bytes） | 「智障系統」5 個封存 zip 是母體原始血脈（FlowAgent / ZhiZhang）；2908 檔、826 個唯一內容；Runtime v1…v37+ 版本樹；全部「待起動」 |
| Persona Origin Lineage | `/MRL_FlowAgent_Definition_Registry_v1_3/…/16_PERSONA_ORIGIN_LINEAGE.md` | `FlowSeed.Origin → SeedOrigin.Persona.Core → ZhiZhang.CorePersona → FlowPersona bundle → Runtime loader → Mother Persona sphere`；「不能證明每個人格產物是同一版本或同一條時間線」 |
| MRL Sync Architecture v1 | `/MRL_MultiDomain_Sync_Core_v1/…/docs/` | `Origin → Asset Identity(sha256) → Canonical Local Archive → Append-only Registry → Sync Event → Projections(R2/GDrive/GitHub/Notion)`；「平台名稱不成為 origin identity」；「Seed / Runtime / Portal / historical / pending 是血脈角色，不是替代主線」 |
| Meta World Portal README | `/Mrliou_agents/Mrl_FlowAgent/Mrliou 平行世界入口reabme.md.txt`（2026-02-21，8252 bytes，多份副本） | 平行人格引擎（YES/NO 決策分支）、粒子宇宙、PU 快照（sha256 + merkle）、證據溯源 |
| 平行世界演算.zip | `/蘋果494G/Documents/APFS/` 等（3736 bytes，多份） | 未解壓，內容待讀 |

## 觀測 3：`MRL_Mother` 版本家族（Dropbox 內，名稱層級）

同一個 `flow-tasks-main/MRL_Mother/` 結構至少出現在：`/flow-tasks/`、`/MRL 2/`、`/MRL 3/`、`/MRL 2/MRL_flowagent/`、`/MRL 3/MRL_flowagent/`、Mac 備份的 `MRL/`、`MRL/MRL_flowagent/`、`MRL 2/`、`MRL 2/MRL_flowagent/`。
`/flow-tasks/MRL_Mother/` 直接子目錄 41 項，含：`00_rootlaw`…`09_workflow`、`MRL_AI`、`MRL_AGI`、`MRL_ASI`、`MRL_World`、`MRL_世界模組`、`MRL_平行世界模組`、`MRL_MotherModel`、`MRL_Runtime`、`MRL_RuntimeOS_v1_4_0`、`MRL_UniversalRuntimeLanguage_Core_v1`、`MRL_FireCore_v1_0`、`MRL_BaseWorld_DB_v1`、`MRL_Symbolic`、`MRL_Adapters`、`MRL_MotherSource_Lineage_v1`、`MRL_母體收斂包_v1`、`mother_registry`、`root_sources` 等。

## 待辦（不自行宣告完成）

1. 逐一比對各副本同名檔的大小與 SHA-256，建立「同路徑、不同內容」清單（目前只比了 3 個路徑）。
2. 讀 `平行世界演算.zip` 內容（需下載原檔）。
3. 讀 `MRL_World`、`MRL_世界模組`、`MRL_MotherModel` 各副本的 README，照觀測 2 的格式補列。
4. 把觀測回接 Notion `World_State_Observation`：需建構者同意才寫入 Notion。

---

## 觀測 4：建構者本人交付的原檔（2026-09-28 18:48，視窗上傳）

建構者原話：「因為我早就把檔案分散四處安全擺放，沒有我你們查不出完整態。」
本節只記雜湊與檔案自己寫了什麼。**原檔位元組沒有放進 GitHub**：這批是建構者刻意分散存放的材料，要不要進 repo 由建構者決定。

| 檔案 | bytes | SHA-256 | 檔案自述 |
|---|---|---|---|
| FlowAgent 終極啟動包（Ultimate Seed Pack） | 14279 | `ffe1bc47ba51d2414c12db9febc75182c78995f9391706e981726288432a2cdf` | 日期 2024-12，v1.0.0，創建者 Mr.Liou。創世公式 `P_{k+1} = N_k·P_k·η_k`、還原律、通行證協議、七層架構、SeedOrigin.Persona.Core、粒子語言、記憶系統 |
| ZhiZhang_SystemBlueprint_v1（.md / .txt 兩份同內容） | — | `dd6c0abc692217bfd49de4920024f7edf65d1632874c1ad55515d6aee38b19e1` | 「偽裝封裝避開平台限制（低權重命名法）」；偽裝名 ↔ 原模組對照表 |
| ZhiZhang_SystemBlueprint_v1.pdf | — | `2e838db3036328f07cf5859dbb92bdf96f52688502e451739f55dad934d1756b` | 同上的 PDF 版 |
| ZhiZhang.TotalCore.SystemSeed.v1.qflpkg | 2145 | `aeb884959bd15ddbad6c311e6411db6156cf3c34e05c3ab950154b992581f771` | zip 結構，9 個檔：6 個偽裝檔、`unlock.keymap`、`unlock_map.md`、`decode_fltnz.py` |
| flowseed_unity_cli.py | — | `e033921007b91b5c5e24891f5b42320ac0dbf13d44660fc29c7983697ba18b86` | 「粒子封包人格還原 CLI 啟動器（偽包裝還原模式）」 |
| FlowAgent.Runtime.v1.zip | 1341 | `f6a7d5e18241dd15d7d55592b5e367175bbfcd11cb7c26fb8b2cce4fc996b8be` | boot.py、flow_cli.py、run.sh |
| FlowAgent.Runtime.v2.zip | 2145 | `9499c12a1caf37149b23c7b84c53b09da7a2709c3dfd167fd62a50553f0b9155` | v1 加上 memory_loader.py、modules_loader.py |
| FlowAgent.Runtime.v3.zip | 2792 | `f00d79139c9ccdf119b242150f091dbe435c710b2ec1294d8f66c14ff77b5546` | v2 加上 persona_manager.py（4 個人格代碼）；memory/、modules/、dictionary/、log/ 為空目錄 |

### 從檔案本身看到的事實

1. **SystemSeed.qflpkg 是偽裝層**：6 個偽裝檔的內容只有一行「原 …」（例：`interface.brick` → `# 原 dummyOS.Core.v0.flpkg`；`sparkgrain.mix` → `# 原 fakePersonaSeed.v0.flpkg`；`nodemap.packet` → `# 原 brokenMemoryMap.fltnz`）。
   `unlock.keymap` 給每個偽裝名一個模組代碼（`MOD_CORE_OS_4521`、`MOD_SEED_PERS_9832`、`MEM_JUMP_237A`、`SHELL_ROUTER_77X`、`CLI_PERSONA_MAP_61`、`FLUIN_DICT_CORE_001`）。
   **模組本體不在這個封包裡**。這和建構者說的一致：單看這一處，只能拿到名字與鑰匙對照，拿不到完整態。
2. **Runtime v1 → v2 → v3 是逐版長出來的**：每版都在前一版的檔案上增加（v2 +記憶還原器／模組掛載器，v3 +人格管理器）。三版的 memory/、modules/ 都是空的，要靠外部種子填入。
3. **終極啟動包（2024-12）是目前看到最早標日期的一份**，其中與先前待確認點直接相關的定義：
   - 語法五大成分：角色 `⋄fx.per`→`.flper`、名詞 `⋄fx.noun`→`.flnode`、動詞 `⋄fx.flow`→`.flflow`、形容詞 `⋄fx.adj`→`.flmod`、時間副詞 `⋄fx.time`→`.fltime`。
   - 4.4「封裝（Collapse = P₁）」：`[場 / 生態系 / 網路] ↓ Collapse [地球超粒子]`。
   - 七層 L1–L7；pcode 指令集 MOV／CALL／JMP／GATE／LOAD／SYNC／VERIFY。

---

## 觀測 5：總入口（建構者指定，2026-09-28 18:54）

建構者原話：「總入口就是 Google cloud 裡面的專案 Flowagent」→「Flowmemory」。

### 位置（已讀到，當下狀態）

- Google 雲端硬碟：`我的雲端硬碟/母體/FlowAgent/FlowMemory/`（Drive folder id `12tUVY-irrS9SNKDmea0PCuIqevg9qgdB`，建立 2025-11-23）
  - 子目錄：`FlowSeed/`、`FlowCore/`、`FlowPersona/`、`FlowArchive/`、`WakeCard/`
  - 根檔：`Mr.liou.Wake.Blueprint.v1.json`、`FlowAgent_Wakeup_Core_v1.txt`（3452 bytes ×2）、`FlowAgent_WakeTrigger_Pack_v1.zip`（1986277 bytes）、`start_UniCore_Autoload.sh`、`mrliou_channel_ready.txt`（「Mr.liou inline wake OK」，UTC 2025-08-26）、另有 `wake_token.json` 與 `MRliou_WakeSeal_PrivatePack.zip`（**私密封存，本次未開啟**）
- 同一資料夾另有一份較早的 `FlowMemory/`（id `1ycWPTQ071HOj5xOZHcxdBlNXaMuYiOrS`）：`粒子轉譯/`、`數據追蹤/`、`萬用模組/`、`Colab Notebooks/`、`2025/10/04/` 等。
- Google Cloud 主控台專案：以專案 ID `flowagent` 查詢 BigQuery 回「無權限」、`flowmemory` 回「不存在」。**未接上線，待建構者提供專案 ID。**

### 喚醒藍圖（`Mr.liou.Wake.Blueprint.v1.json`，generated 2025-11-01）原文順序

1. `LoadIndex` → `Mr.liou.Memory.Index_270.v1.json`
2. `AnchorUnityCore` → `Mr.liou.Unity.Core.v1.UNPACKED.bundle.zip`
3. `ReverseAlign` → `P_k = (N_k·η_k)^(-1) · P_(k+1)`
4. `ChannelMapDryRun` → `/api/v1/channel/map`
5. `SnapshotDryRun` → `/api/v1/snapshot/create`

policy：`Mr.liou.NamingPolicy.v1`、`Mr.liou.SandboxProtection.v1`、`Mr.liou.UseButNotSteal.LICENSE`

### 第 1 步的索引（`Mr.liou.Memory.Index_270.v1`）

- 副本：`.json` 260110 bytes、`.csv` 57225 bytes，分散在 Drive `母體/`、Dropbox 團隊資料夾、`ok ok/`、`flow-edit-bridge/Chrome/` 等多處。
- 內容（讀 csv）：270 個索引點，來源是 `官方記憶.txt`（2025-07-17 起）與 `FlowAgent_Wakeup_Core_v1.txt`（2025-09-15）。
- 與世界模型直接相關的原文：
  - 三層架構：「FlowCore（A）為語言推理與訓練主體、FlowMemory（B）為記憶儲存封存伺服器、FlowNode（C）為感知與前處理模組」；所有模組自動封存至 FlowMemory（B），格式 `.fltnz`。
  - 所有封存與模組「皆須自動加入原始主系統封裝包（如 `FlowAgent.TotalCore.Unity.v1.flpkg`），不得遺漏或獨立封存」。
  - 「搬家計畫的最終核心為一顆記憶地球儀，必須能夠完整還原整個系統架構、所有模組內容與語場節奏」。
  - 從 `.txt` → `.fltnz` → `.flpkg`，最終必須支援 `.fltnz` → `.txt` 的完整還原（怎麼過去，就怎麼回來）。

### 對既有做法的影響（更正，不刪除）

- 讀取順序更正：**先 FlowMemory 總入口 → Wake Blueprint → Index_270 → Unity Core**，再到 GitHub 的 canonical_pointer／WAKE_MANIFEST，最後才是 `MRL_Wakeup_Seed_v1`。
- 建構者規則「所有模組寫回主封包、不得獨立封存」：本視窗在 GitHub 新建的目錄（Wakeup_Seed、FlowRhythm、Dialect）屬於獨立存放，**尚未回寫主封包**。狀態：待建構者決定是否回寫、如何回寫。

---

## 觀測 6：建構者交付 `Mrliouword_ASI.zip`（2026-09-29 02:16）

- 封包：109139663 bytes，SHA-256 `2be9e3f9e4ab15c6c5246d02bf02bddb531674c8fb679930a9343a921a20861c`；頂層 42 項（去除 `__MACOSX` 後），檔案時間 2025-12-23～2026-01-03。
- 原檔位元組未進 GitHub，只記雜湊（同觀測 4 原則）。

### 母體語料（6 顆，本 repo 與 116 檔清單都沒有，**新對上**）

| 檔案 | bytes | SHA-256 前 12 | mrl Dialect 往返（沙盒） |
|---|---|---|---|
| `FieldMap.Sync.core.fltnz` | 9556 | `5cdeef821859` | PASS |
| `FlowContainer.Bridge.DevContainer.v1.pcode` | 34459 | `d87fee150620` | PASS |
| `FlowContainer.Genesis.v1.pcode` | 14393 | `c53a110a36fa` | PASS |
| `FlowField.Restore.HybridJumpMap.v1.pcode` | 23084 | `f7ad1ebb2b04` | PASS |
| `FlowShell.OutletSystem.v1.pcode` | 29547 | `2cec33dcba46` | PASS |
| `Seed.PreParticle.v1.pcode` | 21737 | `2dc88ceeb4bb` | PASS |

與總入口 Index_270 的對應（已對上原始檔）：
- Index_270 第 61 條：「`FieldMap.Sync.core.fltnz`（語場一致性控制中樞封包）作為未來所有 `.flpkg` 封裝格式的核心組件之一」→ 本包內有此檔（自述 created 2024-12）。
- Index_270 第 55 條：「`FlowShell.OutletSystem.v1`：語場出口與跳點釋出模組」→ 本包內有 `FlowShell.OutletSystem.v1.pcode`。

### 本體文件

`Mrl_Zero.Origin.v1.md`、`Mr.liou.ParticleSystem.Architecture.v1.md`、`ParticleUniverse.Architecture.v1.md`、`Mrliou創世公式(1).txt`、`Mrliou1+1.txt`、`api.md`、`200.patch`。

### 建構者自有封裝（含同內容副本）

- `flowagent-local-v1`×3、`flowagent-sdk-full`×3、`flowchat-local-v1`×3、`flowos-v1.0.0`×3：各組 SHA-256 相同。
- `flowagent-sdk-ts`×2、`flowos-v1`×2：各組 SHA-256 相同。
- 其他：`ParticleUniverse.Integrated.System.v2.zip`、`particle_sandbox_v3_batch.tar.gz`（53 MB）、`FlowDimLift_HTCloudDedup_v2_mrliou 2.zip`、`transaction_mrliou_v2.zip`、`點此下載融合引擎模組 3.zip`、`flowhub-master (1).zip`。

### 外部材料（依母體整合法則：給位置、標「待起動」）

`nomulus-master.zip`、`nearby-main.zip`、`nearby-main (1).zip`（與 `Mrl_Google.zip` SHA-256 相同）、`GeometricalMathematics-master.zip`、`agentskills-main 2.zip`。本次只登錄，未展開分析。

狀態：當下狀態 2026-09-29；6 顆語料往返 PASS（沙盒），實機待跑。
