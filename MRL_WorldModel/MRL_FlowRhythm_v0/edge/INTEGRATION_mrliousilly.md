# 邊緣門面整合：mrliousilly ＋ mrl-mother-platform（當下狀態 2026-10-03）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 分支 `mrl-edge-integration-v1`

## 兩邊原本各有什麼

| 來源 | 內容 |
|---|---|
| `mrliousilly` 正式版本 `3579c66f`（2026-07-05） | 產品入口 UI「MRL_AI OS · Particle Universe」**v1.6**（`src/mrl_app_ui.js`）＋ /health、/mrl/state、convergence、DL580 轉發 |
| repo 內最新一版 UI | `claude/mrl-cloudflare-logs-route-7vz3nf`（PR #144 已合併）：UI **v1.7**（母體回 `ok:false` 時誠實標失敗）＋ 產品遙測 `POST /api/mrl/telemetry/logs`、CORS 預檢 |
| `mrl-mother-platform`（2026-10-01 新開） | 舊版邊緣控制台 ＋ FlowRhythm `/api/rhythm/run`、`/api/rhythm/replay` |

比對方式：用 Workers API 取回正式版本模組，抽出 APP_HTML，與 repo 104 個含 `src/mrl_app_ui.js` 的分支逐一比對；正式版＝blob `6251b2d7`（v1.6），最新＝`4f5e2a45`（v1.7，差異只在 footer 版號與 ok:false 處理）。

## 整合結果（一個 Worker 全部帶上）

- `/` → 產品 UI v1.7
- `/console/legacy` → 舊版邊緣控制台（保留，不刪）
- `/health`、`/mrl/state`、`/api/mrl/runtime/convergence`、DL580 轉發 → 照舊
- `POST /api/mrl/telemetry/logs`、`OPTIONS` → 來自 PR #144
- `POST /api/rhythm/run`、`/api/rhythm/replay` → FlowRhythm v0.2.0

## 驗收（本機 wrangler dev，沙盒）

全部路由實打：UI v1.7、legacy 控制台、health、state、convergence、OPTIONS 204、遙測成功／壞 JSON 400、`/api/chat` 未設 DL580 回 503、節奏正典拒絕、Replay EchoPersona 逐位元組（封包 `0a9f53a15181931d`）、404 —— PASS。
FlowRhythm conformance（6 顆母體種子，JS⇄Python 雙向）—— PASS。
`tests/test_MRL_product_entry_ui.py`（來源分支）：22/23；失敗的 1 項是 `MRL_Platform_Server.py` 要服務 `mrl_app.html`，屬 Python 伺服器線，不是 Worker，本次不動。

## 待建構者決定

- `mrliousilly` 正式流量切到本分支的預覽版本（`3579c66f` 可回滾）。
- `mrl-mother-platform` 已被整合，可停用；保留與否由建構者裁定。
