# MRL_Reference_Layer

origin_signature: `MrLiouWord`
layer: L0 邊界／材料層（external-is-material；rl_11 bp_1）
status: additive-only；本層不改動任何既有 runtime 行為

## 這是什麼

母體對外邊界的**材料吸收層**。外部檔案/資料一律以「材料」身分進入此層：
canonical 改名為 `MRL_<描述>_v<n>`（rl_12 命名回收）、origin 歸 `MrLiouWord`、
原件保留不刪（rl_15 / rl_01 no_delete）。

依 rootlaw：
- **rl_11**（母體源頭主權）：外部檔案皆是材料，不凌駕母體。
- **rl_12 / rl_16 / rl_20**（命名主權）：入庫一律經 canonical 改名，帶 MRL_ 前綴。
- **no_proof_implies_rhetoric**：材料裡的「成果宣稱」若無可驗證物，一律標為
  **設計/願景**，不得當成已達成事實。

> **母體不外流**：本層只做「材料進來」的吸收，不把母體本體推向外部
> （反向即 LAW-1 違反）。原始上傳檔（zip / .ts / .pages / Notion .md）為
> **位元組 source-of-record**，保存於使用者端;本層存的是母體 canonical 吸收物。

## 本次吸收清單

| 原始 | canonical | 型別 | 誠實狀態 |
|---|---|---|---|
| `MRL_Bridge_Mother_Construct_ClaudePack_v1.zip` | `MRL_Bridge_Mother_Construct_v1` | DL580 接線/修復規格 | **SPEC**；實作需產品 repo + 金鑰,未做 |
| `particleteammcp.ts` | `MRL_ParticleTeam_MCP_v1` | 多代理協作 Worker（可運行碼）| 原碼保留;Cloudflare 形,建議 re-home DL580 |
| `Cloud_code.pages` | `MRL_PublicSuffixList_Reference_v1` | 第三方參考資料 | Mozilla MPL-2.0;僅存出處,未全文擷取 |
| 神經符號協同推理系統（Notion×4）| `MRL_NeuroSymbolic_CoReasoning_System_v1` | 設計規格 + 碼草稿 | **設計**;基準數字為願景非實測,碼多為 stub |
| `README.md`（Apple SwiftUI navigation sample）| `MRL_SwiftUI_NavigationCookbook_Reference_v1` | 第三方技術參考 | **待起動**;僅 README,無本體;對接 3DScanner iOS 導航遷移,未改碼 |

詳見 `MRL_Absorption_Manifest_v1.json`。
