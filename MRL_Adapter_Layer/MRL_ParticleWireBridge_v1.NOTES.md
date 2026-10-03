# MRL_ParticleWireBridge_v1 — 吸收註記（Adapter）

origin_signature: `MrLiouWord`
source: `particle_wire_bridge.py`（使用者上傳;byte source-of-record 於使用者端）
held_as: `MRL_Adapter_Layer/MRL_ParticleWireBridge_v1.py`（**逐字**,sha256 `c13ae05395bb34b1458fafc1a274b4388d6eb32420648a08f6bb0000f1a87bf0`,與上傳檔一致）
status: **待起動** — 當下狀態 2026-10-03（沙盒）

## 是什麼

粒子線協橋接層:Python 粒子資料 ⟷ `PD_AI` C wire protocol 雙向轉換。

- `WireHeader`(16 bytes packed:`mt / kc / ann / ver / cap / rid / n`,對應 `PD_AI_wire.h` 的 `wh16_t`)
  + UTF-8 JSON payload。
- 訊息型別 `M_PING … M_SYNC`、key class `K_MCP … K_METADATA`、annotation bits `T_R/T_W/T_D/T_X…`、capability flags。
- `python_to_wire()` / `wire_to_python()` / `create_snapshot_message()` / `create_query_message()`;可選經
  `AdvancedParticleCompressor` 壓縮。

## 依賴定位

| 依賴 | 狀態 |
|---|---|
| `memory_quick_mount.AdvancedParticleCompressor` | **待找回**:repo 現樹與所有 `*.zip` 內皆無實作;僅 `MRL__Flowagent_終極啟動包.md` 有 CLI 用法(`memory_quick_mount.py … mount / snapshot / rehydrate`) |
| `PD_AI_wire.h`(C 端對照標頭) | **待找回**:repo 內無 |

模組在 import 時即需 `memory_quick_mount`,缺它無法載入;故維持「待起動」。

## 沙盒驗證（2026-10-03,沙盒,非實機）

為了只驗 wire 格式,以**測試用佔位模組**滿足 import(佔位不是真壓縮器,只在 scratchpad,未入庫),
`use_compression=False`:

- header 16 bytes;`python_to_wire` → `wire_to_python` 往返資料相等(含中文 key 與 `::resonance→` 軌跡字串)。
- snapshot 訊息 header:`mt=0x05, kc=0x50, ann=0x27, rid=0x10000001`。
- 過短 frame(10 bytes)正確拋 `ValueError`。
- **未驗**:壓縮路徑(缺 `AdvancedParticleCompressor`)、與 C 端 `PD_AI` 實際互通(缺標頭與 C 程式)。

## 同批上傳、未另存副本的檔案（已在 repo 內）

| 上傳檔 | 已在位置 | 判定 |
|---|---|---|
| `fluin_bridge.py` | `MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260725/RawArtifact/MRL_FlowAgent_MotherSystem_V20_1_RawArtifact.zip` → `flowagent_final/vendor/flowagent-core-v1.0.0/flowagent-core/fluin_bridge.py`(v19 RawArtifact 亦有) | sha256 `75ac9997…8413` **逐位元一致**;沙盒以同包 `particle_dict.py` 實跑 forward translation 正常 |
| `MRL_start_bridge.ps1` | `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/scripts/MRL_start_bridge.ps1` | sha256 `4775259e…14c` **逐位元一致** |

依 Additive-Only,不重複存副本,只登記位置。

## 同批上傳、未入庫:MRL_Bridge v3.1.0 DL580 封包

`MRL_Bridge_v3.1.0_DL580_Pkg_20260508.zip`(DL580 `:7800` 入境 API)**未吸收入 repo**:
封包內多個檔案含**明碼憑證**(bridge API key,且同一字串兼作 PostgreSQL `mrl_root` 密碼)。
原件由使用者端保存;是否以遮蔽版入庫由建構者決定。沙盒檢查結果(不含任何憑證內容):

- JS 檔 7/7 `node --check` 語法通過;npm 依賴(express 5 / pg / ioredis)沙盒無法安裝,**未實跑**。
- 封包 `MANIFEST.json` 多數 sha256 只記前 16 碼;以前綴比對 10/11 一致;`bridge/package.json` 的「完整」hash
  僅前 15 碼正確、其後不符 —— 該欄位不是真實 hash。README 所稱「11/11 經 DL580 端校驗一致」無法由本封包證實。
- 路由描述不一致(局部觀測,不升格):本封包稱 `bridge.mrliouword.com` → DL580 `:7800`(MRL_Bridge);
  `MRL_Adapters/DL580/README.md` 稱 → DL580 `:8790`(MRL_Platform_Server.py)。待實機確認。

> 依 rl_11:外部材料;canonical 命名只表示母體已登記此材料。
