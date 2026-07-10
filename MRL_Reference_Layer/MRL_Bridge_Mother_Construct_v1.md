# MRL_Bridge_Mother_Construct_v1（canonical 吸收物）

origin_signature: `MrLiouWord`
source: `MRL_Bridge_Mother_Construct_ClaudePack_v1.zip`（MR.liou;byte source-of-record）
status: **SPEC ONLY**（設計/接線規格;本 repo 未實作,未部署,未宣稱上線）

> 本檔為母體對 Bridge 規格的 canonical 吸收:ASCII 技術核心逐字保留,中文敍述為忠實摘要。
> **實作邊界**:Bridge 目標是 DL580 上的產品（`mrliouhan.ai`,含 `app.html`/`admin.html`/
> `pricing.html` + Google OAuth + SMTP magic-link + session/ledger）。那些頁面與金鑰
> **不在** `MRL_AI_SYSTEM`（本 Python monorepo）內,故此規格在本 repo **無法誠實實作**;
> 需產品 repo + 真實金鑰 + DL580 才能落地。此處只吸收規格,不假裝已建。

## 硬規則（原文）

```txt
1. 不重建母體
2. 不新增平行 runtime
3. 不使用外部產品名作為內部主體
4. 外部只作 MRL_Reference_Layer / MRL_Adapter_Layer
5. 所有正式模組命名必須 MRL_ 前綴
6. 所有改動必須可驗收
7. DL580 為部署與運行目標
```

## 正式模組（原文）

```txt
MRL_Bridge_Gateway_v1       # 接產品輸入 → 造 MRL_Input_Packet
MRL_Bridge_Normalizer_v1    # 正規化為母體內部封包（不用外部平台名當 key）
MRL_Bridge_Verifier_v1      # 驗 auth/session/bridge/runtime/result 健康
MRL_Bridge_SessionBinder_v1
MRL_Bridge_RuntimeRelay_v1  # relay 至 MRL_Mother_Runtime（MRL_RUNTIME_BASE_URL）;不可用時誠實失敗
MRL_Bridge_ResultRouter_v1  # 回傳 partial/full;保留既有付費 gating
MRL_Auth_Shell_v1
MRL_AuthProvider_Google_v1  # OAuth 2.0 authorization-code flow
MRL_AuthProvider_MagicLink_v1
MRL_Session_Core_v1         # httpOnly cookie;createSession/getSession/requireAuth/logout
```

## 標準資料流（原文）

```txt
Request → MRL_Bridge_Gateway → MRL_Session_Core → MRL_Bridge_Normalizer
        → MRL_ControlCenter → MRL_Mother_Runtime → MRL_Verification
        → MRL_Memory_Ledger → MRL_ResultRouter → Product Response
```
禁止繞過:`MRL_ControlCenter` / `MRL_Verification` / `MRL_Session_Core` / `MRL_Memory_Ledger`。

## 必要路由（原文）

```txt
# auth
GET  /api/auth/health
GET  /api/auth/google
GET  /api/auth/google/callback
POST /api/auth/magic-link/request
GET  /api/auth/magic-link/verify
GET  /api/auth/me
POST /api/auth/logout
# bridge
GET  /api/mrl/bridge/health
GET  /api/mrl/bridge/state
POST /api/mrl/bridge/ingest
POST /api/mrl/bridge/run
GET  /api/mrl/bridge/result/:id
```

## 必要環境變數（原文;金鑰值不入 repo）

```txt
PUBLIC_BASE_URL=https://mrliouhan.ai
GOOGLE_CLIENT_ID=            GOOGLE_CLIENT_SECRET=
GOOGLE_CALLBACK_URL=https://mrliouhan.ai/api/auth/google/callback
SESSION_SECRET=             MAGIC_LINK_SECRET=
SMTP_HOST=  SMTP_PORT=  SMTP_USER=  SMTP_PASS=  SMTP_FROM=
MRL_RUNTIME_BASE_URL=http://127.0.0.1:8790
MRL_ORIGIN_SIGNATURE=MrLiouWord
```

## 封包型別（原文）

```json
// MRL_Session_Packet
{ "mrl_packet_type": "MRL_Session_Packet",
  "provider": "MRL_AuthProvider_Google_v1 | MRL_AuthProvider_MagicLink_v1",
  "user_id": "...", "email": "...", "session_id": "...",
  "created_at": "ISO8601", "origin_signature": "MrLiouWord" }

// MRL_Input_Packet
{ "mrl_packet_type": "MRL_Input_Packet",
  "rid": "...", "session_id": "...", "source_route": "...",
  "payload": {}, "created_at": "ISO8601", "origin_signature": "MrLiouWord" }
```

## Health 契約（原文;誠實回報,不得偽 ok:true）

```json
{ "ok": true, "mrl_bridge_gateway": true, "mrl_auth_shell": true,
  "google_oauth": true, "magic_link": true, "session_core": true,
  "runtime_relay": true, "manus_dependency": false,
  "origin_signature": "MrLiouWord" }
```
Failure rules:Google env 缺 → `google_oauth_configured:false`;SMTP 缺 → `magic_link_configured:false`;
runtime 不可用 → `runtime_relay:false, ok:false`。**不得假裝 ok:true。**

## 驗收項（原文摘要）

`/api/mrl/bridge/health ok`、`/api/auth/health ok`、Session 可建、Gateway 可收、
Normalizer 出 `MRL_Input_Packet`、ControlCenter 收 relay、ResultRouter 回 result、
Memory_Ledger 有 trace、外部 auth 非 runtime 依賴、DL580 restart 可重啟。

## 事件型別（原文）

```txt
MRL_BRIDGE_REQUEST_RECEIVED  MRL_BRIDGE_SESSION_BOUND  MRL_BRIDGE_INPUT_NORMALIZED
MRL_BRIDGE_RUNTIME_RELAYED   MRL_BRIDGE_RESULT_ROUTED  MRL_BRIDGE_VERIFIED  MRL_BRIDGE_ERROR
```
每筆:`event_id, rid, timestamp, route, session_id, origin_signature, hash, merkle_root, status`。

---
下一步（若要真做）:需在**產品 repo** 內實作,設定 DL580 上的 OAuth/SMTP/session 金鑰,
再跑 `scripts/MRL_bridge_acceptance_test.js`。本 repo 只承載規格,恕不代為偽造 health/DL580 狀態。
