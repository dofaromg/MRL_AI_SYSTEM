# MRL_ApiRecord — bridge 生產級 API 紀錄中介層

`origin_signature: MrLiouWord` ｜ `product: MrliouAI` ｜ 對齊 **MRL_Bridge_API v3.x**（`D:\mrl\bridge` → `bridge.mrliouword.com`）

把 `bridge.mrliouword.com` 收到的每一個 API 呼叫，記進你現有的 **PostgreSQL**（自動建 `mrl_api_records` 表），吃你現有的 **`x-api-key`** 認證，蓋 `origin_signature`。零新依賴（沿用 bridge 既有 `pg` Pool / `redis`）。

## 上架（把檔案放進 `D:\mrl\bridge\MRL_ApiRecord\`，server.js 加 3 行）

```js
// server.js 最上方 require（你已有 const app = express(); const pool = new Pool(...); 等）
const mrlApiRecord = require('./MRL_ApiRecord/MRL_ApiRecord.cjs');

// 在你所有既有路由「之前」掛上（middleware 要先跑才能量到每個請求）：
mrlApiRecord.attach(app, {
  pool,                     // 你的 pg Pool（health 顯示 pg_tables:196 那個）
  redis,                    // 你的 redis client（可選；沒有就傳 null）
  apiKeyHash: API_KEY_HASH, // 你 server.js line 28 的 const API_KEY_HASH
});
```

完成。之後：
- **每個請求自動入帳** → `mrl_api_records`（method / path / status / latency_ms / authed / ip / bytes / trace_id / origin_signature）。
- 新增讀取端點（需 `x-api-key`，跟你其他端點同一把鑰匙）：
  - `GET /api/mrl/records?n=50` → 最近 n 筆
  - `GET /api/mrl/records/summary` → 總數 + 依 path / status 聚合

## 驗證（部署後，用你的金鑰）

```powershell
curl.exe -s "https://bridge.mrliouword.com/api/mrl/records/summary" -H "x-api-key: <你的KEY>"
# → {"ok":true,"origin_signature":"MrLiouWord","total":N,"by_path":{...},"by_status":{"200":..}}
curl.exe -s "https://bridge.mrliouword.com/api/mrl/records?n=20" -H "x-api-key: <你的KEY>"
```

或直接查資料庫：
```sql
SELECT ts, method, path, status, latency_ms, authed FROM mrl_api_records ORDER BY id DESC LIMIT 20;
```

## 設計對齊你現行 bridge（截圖 server.js）

| 你的 bridge | 本模組對齊 |
|---|---|
| `const API_KEY_HASH = crypto.createHash('sha256')...`（line 28） | `apiKeyHash` 直接吃，讀取端點用 SHA-256 比對 |
| `req.headers['x-api-key'] \|\| req.query.key`（line 174） | `checkAuth()` 同一取法 |
| `res.status(401).json({error:'API key required...'})`（line 178） | 401 訊息一致 |
| pg Pool（health `pg_tables:196`） | INSERT 進 `mrl_api_records`，冪等建表 |
| redis（health `redis:true`） | 可選即時計數 `mrl:api:total` / `mrl:api:status:*` |
| `origin_signature:"MrLiouWord"`, v3.1.0 | 每筆與每個回應都蓋 origin_signature |

## 安全

- 任何 pg / redis 失敗都**不中斷 bridge**（吞例外、退回 console）。
- 讀取端點強制 `x-api-key`；未帶或錯誤 → 401。
- INSERT 全參數化（無注入）。

## 驗證紀錄（當下狀態，沙盒）

mock Express + mock pg 邏輯測試 **11/11 PASS**（middleware 入帳、path/status/origin_signature、401 無鑰、200 帶鑰、summary 聚合、checkAuth）。`node --check` 通過。真實 bridge 上架後之線上行為待你實機驗收。
