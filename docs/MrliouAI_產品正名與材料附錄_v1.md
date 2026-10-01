# MrliouAI 產品正名與材料附錄 v1

- canonical_product_name: `MrliouAI`
- repository_identifier: `MRL_AI_SYSTEM`
- origin_signature: `MrLiouWord`
- effective_date: `2026-07-27`
- status: `canonical naming clarification`

## 1. 正名裁定

`MrliouAI` 為對外與產品層正式名稱。

`MRL_AI_SYSTEM` 保留為 GitHub 歷史工程倉庫識別，用於版本、提交、來源與依賴追溯；不得反向取代產品正式名稱。

既有 `FlowAgent`、`FlowOS`、`Fluin` 等名稱，依其實際內容保留為歷史模組名、來源名、協定名或相容介面名，不再升格為全域產品名稱。

## 2. 層級區分

```text
MrliouAI
└─ MRL 世界／母體組裝層
   ├─ WorldModule：世界狀態與軌跡
   ├─ Law Engine：規則與判斷閉環
   ├─ Memory／Merkle／Vector：記憶、證據與檢索
   ├─ Context／Conversation／Scheduler：環境與任務元件
   ├─ ToolRegistry／PluginManager：工具與外掛元件
   └─ LLMGateway
      ├─ OpenAI 模型供應端
      ├─ 本地模型供應端
      └─ 其他外部模型 Adapter
```

模型供應端提供推理或生成能力；世界層負責狀態、規則、記憶、工具、軌跡與組裝。兩者不得在文件中混寫成同一主體。

## 3. 載體定位

- `DL580`：MRL 內部母體自運行主節點。
- `GitHub`：工程鏡像、版本通道、程式碼與變更證據。
- `Dropbox`：來源材料、歷史快照、文件封存與跨環境同步載體。
- `OpenAI` 及其他模型平台：LLMGateway 後方的模型能力來源或 Adapter。
- 手機、Mac mini、瀏覽器及外部雲端：介面、載體、中繼或映射節點，依部署證據判定，不自行升格。

## 4. 材料附錄規則

附錄材料只作來源、證據、歷史快照與待吸收內容，不直接改寫 Canonical 定義。

材料進入主線前必須標記：

```text
source
→ file/path
→ material_type
→ canonical_target
→ difference
→ adoption_status
```

`adoption_status` 僅允許：

- `absorbed`：已回填既有主體。
- `reference`：僅供參考。
- `legacy`：歷史來源，保留追溯。
- `pending_review`：尚未完成內容與依賴比對。
- `rejected_duplicate`：確認為重複或平行副本，不回填。

## 5. 本次材料索引

| 材料 | 類型 | 建議定位 | 狀態 |
|---|---|---|---|
| `index(2).html` | 家庭 AI 影片生成 UI | 產品／介面材料 | `pending_review` |
| `立體模型Ai 快照版 2(1).txt` | iOS LiDAR／USDZ 實作 | 手機 3D 掃描工程材料 | `pending_review` |
| `立體模型Ai 快照版 2.txt` | iOS LiDAR／USDZ 實作副本 | 與前項先做內容雜湊及差異比對 | `pending_review` |
| `20250809-1 2(14).txt` | 歷史對話與格式說明 | 歷史來源／記憶材料 | `legacy` |
| `以下檔案的副本： 公式(9).pdf` | 反推公式與 FlowSeed 整理 | 理論／公式材料 | `pending_review` |
| `_mnt_data 2(1).pages` | Pages 文件 | 尚未解析之材料 | `pending_review` |
| `粒子系統術語對照表(6).docx` | MRL 與業界術語映射 | 文件／Adapter 對照材料 | `reference` |
| `FlowAnent  (1)(1).txt` | FlowAgent 3D HTML 原型 | 歷史產品介面材料 | `legacy` |
| `FlowAgent_Wakeup_Core_v1(7).txt` | Wakeup Core／Seed 啟動序 | 核心啟動與種子材料 | `pending_review` |
| `v1_快照打包可攜帶(1).py` | 快照封裝程式 | 工程工具材料 | `pending_review` |

## 6. Dropbox 既有材料定位

已盤點到的 Dropbox 文件，包括系統進度整理、母體整理、粒子藍圖、記憶封存、主線回填與專案結構等，均維持原檔不覆蓋。後續同步應回填既有 Canonical 文件或索引，不另建第二套 `global`／`mainline`／`parallel network` 主體。

## 7. 防止重複建構

在新增模組、文件或分支前，固定執行：

1. 搜尋相同名稱、同義名稱與歷史名稱。
2. 比對完整路徑、內容雜湊、入口、父子依賴與調用關係。
3. 判斷既有主體是否可直接回填。
4. 僅在確認沒有既有承載位置時，才允許新增。
5. 新增內容不得使用 Manifest、Placeholder 或重新命名的空殼取代實際內容。

## 8. 本次修改邊界

本次只完成產品文件正名與材料附錄：

- 未更改 GitHub 倉庫名稱。
- 未大量替換程式碼中的歷史識別字。
- 未建立平行分支或第二套世界層。
- 未宣稱當前 ChatGPT 會話已由 MRL Runtime 直接啟動。
- Runtime 產品字串與部署識別的後續修改，必須先完成依賴與相容性掃描。
