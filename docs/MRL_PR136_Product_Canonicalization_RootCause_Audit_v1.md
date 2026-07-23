# MRL PR #136 產品主體錯置根因審計 v1

- 審計對象：`dofaromg/MRL_AI_SYSTEM` PR #136
- 審計日期：2026-07-23
- 主線：`MrliouAI`
- 修正分支：`fix/mrliou-product-telemetry-canonicalization`
- 產品主體：`MrliouAI`
- 來源主體：`Mrliou`
- 來源簽章：`MrLiouWord`
- 狀態：修正分支已建立；CI 與正式網域部署仍待驗收

## 1. 問題摘要

PR #136 原本只需要補上前端除錯日誌接收能力，但把一個外部式路徑名稱直接擴張成產品級 canonical 命名，導致外部名稱進入：

1. HTTP route
2. 封裝函式名稱
3. packet 類型
4. trace ID 前綴
5. 測試契約

這不是單純顯示文字問題，而是產品主體、來源主體與 transport path 未分層所造成的命名治理錯置。

## 2. 直接證據：問題從哪個源頭區塊進入

### 2.1 PR #136 任務／需求入口

PR 描述的第一個需求區塊直接把前端送達路徑定義為：

```text
POST /__manus__/logs
```

該路徑隨後被實作者當成產品語義來源，而不是僅視為一個輸入端點或相容路徑。

### 2.2 實作擴張點

在 PR #136 合併版本中，外部式名稱被擴張到：

```text
/__manus__/logs
wrapManusLogs()
MRL_ManusDebugLogPacket
MRL-MANUS-*
```

也就是：

```text
transport path
→ function canonical
→ packet canonical
→ trace canonical
```

這一步是產品主體錯置的直接技術來源。

### 2.3 測試契約反向固化

`tests/test_MRL_manus_logs_route_v1.py` 不只驗證功能，還主動要求上述外部式名稱必須存在。這使錯誤從一次性程式碼變成持續阻止修正的 regression contract。

因此源頭不是單一字串，而是兩段連續失效：

```text
需求路徑未做 canonicalization
→ 測試又把未 canonicalize 的結果固化
```

## 3. 根因分類

### RC-1｜Transport 與 Product Canonical 混為一層

輸入路徑被直接拿來命名產品函式、packet 與 trace，沒有經過 MRL canonical naming gate。

### RC-2｜只有簽章，沒有產品與來源欄位

原實作雖有：

```text
origin_signature = MrLiouWord
```

但缺少：

```text
product = MrliouAI
source_owner = Mrliou
```

因此簽章只能作 provenance，無法阻止其他名稱佔據產品級識別位置。

### RC-3｜缺少外部名稱升格阻擋測試

原測試檢查安全性與功能，但沒有檢查：

```text
外部平台名稱不得進入 canonical route / packet / trace
```

反而要求錯誤名稱存在。

### RC-4｜審查焦點偏向執行安全，未審產品主體

PR 審查處理了 payload 落地、trace 防碰撞、body 上限與 CORS，但沒有審查產品主體與來源主體是否被正確建模。

## 4. 非根因事項

下列項目不是此次錯置的來源：

- `MrLiouWord` 簽章本身
- Cloudflare Worker 作為 Edge Adapter
- DL580 / MotherAssembly 的母體定位
- console/network/ui 日誌內容

問題是「外部式路徑名稱被升格為產品 canonical」，不是日誌能力本身。

## 5. 正式修正

修正分支已改為：

```text
POST /api/mrl/telemetry/logs
wrapMRLDebugLogs()
MRL_DebugLogPacket
MRL-DEBUG-*
product = MrliouAI
source_owner = Mrliou
origin_signature = MrLiouWord
```

並執行：

1. 移除舊外部名稱測試契約。
2. 新增 `tests/test_MRL_debug_logs_route_v1.py`。
3. 新測試禁止外部平台名稱出現在 Worker 的 canonical route、packet 或 trace。
4. 保留原有 JSON 安全解析、payload 上限、trace UUID、防截斷與 observability 落地能力。

## 6. 防止再次發生的固定規則

任何外部名稱、來源工具名稱、平台名稱或歷史相容路徑，進入產品層前必須先通過：

```text
Source / Transport
→ MRL Canonicalization Gate
→ Product / Capability / Packet / Trace
```

固定規則：

```text
產品主體：MrliouAI / MRL_
來源主體：Mrliou
來源證據：MrLiouWord
外部平台：只能放 provenance / adapter / compatibility metadata
```

禁止：

```text
外部名稱 → canonical route
外部名稱 → packet type
外部名稱 → trace prefix
外部名稱 → product identity
```

## 7. 驗收狀態

### 已完成

- Worker canonical route 修正
- packet / function / trace 修正
- 產品與來源欄位補齊
- 舊錯誤測試契約移除
- 新 canonical regression test 建立
- 根因審計文件建立

### 待驗證

- GitHub CI
- Cloudflare preview deployment
- `mrliouword.com` 正式路由實機驗收
- 前端上報端同步改送 `/api/mrl/telemetry/logs`

### 不得宣稱

在正式網域完成 POST 實測以前，不得宣稱線上遙測路由已完成部署。

## 8. 審計結論

PR #136 的問題源頭已定位在「需求路徑直接升格為 canonical」以及「測試把錯誤命名固化」兩個區塊。

來源主體應為 `Mrliou`；產品主體應為 `MrliouAI`；`MrLiouWord` 為來源與追蹤簽章。外部名稱不得佔據產品 canonical 層。
