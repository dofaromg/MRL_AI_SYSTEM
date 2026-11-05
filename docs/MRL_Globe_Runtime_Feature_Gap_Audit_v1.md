# MRL Globe Runtime 功能差距審計 v1

> 法則：**Additive-Only**。origin_signature：**MrLiouWord**
> 母體吸收日期：**2026-07-16**（沙盒吸收；使用者外部審計之母體回收產物）
> 產品名稱固定：**MRL Globe Runtime** ｜ 上層產品固定：**MRL Family Globe** ｜ 來源簽章固定：**MrLiouWord**
>
> **本文件用途**：避免把「檔案存在」或「描述檔存在」再次誤報為完整功能（呼應 CLAUDE.md 誠實回報約定）。狀態分三層：**已完成（實測通過）／部分完成／尚缺**。

---

## 1. 本修補版已完成並通過測試（已完成）

- AI 導遊：世界包內容檢索、節點說明、意圖判斷、離線回答、DL580 模型轉接。
- 資料整理：將節點、導覽、路線、交通、注意事項與時間線整理為 RAG 文件。
- 行程規劃：依可用時間、起點、距離、偏好與交通模式產生有序站點。
- 建議：依 GPS／選定節點、偏好、距離與現有路線產生可解釋的下一站建議。
- Runtime API：`/api/guide`、`/api/ai/organize`、`/api/ai/plan`、`/api/ai/recommend`。
- Runtime UI：整理資料、四小時規劃、下一站建議與 AI 導遊結果列表。
- 語意縮放：L0 SPACE、L1 CITY、L2 DISTRICT、L3 ATTRACTION、L4 STREET、L5 INDOOR、L6 CONTENT。
- 世界定位：WGS84 正規化、ECEF 轉換、本地東北天偏移、GPS 精度與圍欄判斷。
- 離線多模式路線：步行、開車、單車、渡輪、巴士、輕軌篩選與路線顯示。
- 11 個內容插件均有可載入執行實例、世界掛載、內容查詢與 Runtime API。
- Builder 已有 KML、GeoJSON、照片上傳、驗證及 FLPKG 編譯介面。

## 2. 已有但仍屬部分完成（部分完成）

- **Camera／Zoom／Label／Navigation**：核心語意層已完成；室內樓層仍需實際資料才能顯示。
- **Route**：離線圖形與模式篩選已完成；尚未接入即時交通、船班與第三方 Directions 回傳。
- **Translation**：目前是字典與原文回退；尚未完成完整多語 UI。
- **AI Voice**：已有 SSML 產生能力，尚未接 TTS 播放服務。

## 3. 尚缺的原承諾功能（尚缺）

- 3D Tiles、Terrain、Elevation、Vector Tiles 的 MRL 資產管線。
- Panorama、Street View、Drone、3D Models 的載入與互動介面。
- 收藏、旅程分享、完整搜尋 UI、多語切換。
- Embedding 服務與向量索引。
- **DL580 實機 Qwen、GPS 手機現場、Mapbox 真實 Token/Tiles、外部 TLS 的驗收證據。**（皆待實機）

---

## 4. 母體定位（吸收）

| 項 | 母體定位 | 當下狀態 |
|---|---|---|
| MRL Globe Runtime | `MrLiouWord.Globe.Runtime`（MRL Family Globe 之 runtime） | 部分完成（沙盒）；§3 待實機 |
| Runtime API `/api/guide` 等 4 支 | L7 LOOP 執行面 | 已完成（實測） |
| 語意縮放 L0–L6 | 與 rootlaw L0–L7 為**不同體系**（Globe 空間語意 vs 母體治理分層），勿混 | 已完成 |
| §3 尚缺項 | 標「待起動／待實機」，補齊後升格 | 待起動 |

> 誠實邊界：§3 各項在取得實機/真 Token/驗收證據前，一律不得標「已完成」。當下狀態 沙盒 2026-07-16。
