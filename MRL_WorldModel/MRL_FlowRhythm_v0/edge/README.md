# FlowRhythm v0 · 邊緣載體（edge）

origin_signature: MrLiouWord ｜ 怎麼過去，就怎麼回來 ｜ Additive-Only

1. **本體或載體**：載體。承載本體 `../flow_rhythm.py`（權威），自己不定義語意。
2. **對應哪一段**：Jump → Collapse → Trace → Replay 全程；補上 `src/mrl_worker.js` convergence 裡 `replay_restore_runtime: PENDING` 的邊緣那一段（只補邊緣，不改該狀態）。
3. **驗收語料**：母體 6 顆種子（EchoPersona.pcode／.flpkg、FluinCoreSeed／Memory.Seed.Core .flseed、FluinSim Group1／Group2），與 `tests/test_rhythm.py` E 段相同。

| 檔案 | 作用 |
|---|---|
| `build_lexicon_json.py` | 呼叫 `load_lexicon()` 讀 2025-07 原檔 → `lexicon.v0.2.0.json`；8 個原檔 SHA-256 須與 `../lexicon/SOURCES.sha256` 相符，否則中止 |
| `flow_rhythm.mjs` | JS 版節奏引擎（WebCrypto SHA-256），語義 Gate 與 Python 相同 |
| `conformance.mjs` | JS ⇄ Python 逐位元組驗收（`node conformance.mjs`） |
| `dump_reference.py`、`python_replay_check.py` | 驗收用：Python 出參考值／Python 反向 Replay JS 軌跡 |

Worker 端點（`src/mrl_worker.js`，POST 純文字）：
- `/api/rhythm/run` —— 輸入粒子語句 .fltnz；預設正典 → 遇 provisional 映射回 422
- `/api/rhythm/replay` —— 輸入 v0.2.0 軌跡；回傳 `byte_identical`、封包雜湊
- 加 `?sandbox=1` 才允許 provisional；輸出保留 `PROVISIONAL_NOT_CANONICAL`

## 驗收（當下狀態 2026-10-02，沙盒）

| 項目 | 結果 |
|---|---|
| H. JS run ＝ Python run（軌跡／封包／敘述），6/6 種子 | PASS |
| I. JS Replay 讀 Python 軌跡，逐位元組重現 | PASS |
| J. Python Replay 讀 JS 軌跡（反向） | PASS |
| K. 正典 fail-closed；竄改 status／刪授權行／竄改映射 → 拒絕 | PASS |
| L. v0.1.0 歷史軌跡判為歷史、不當 v0.2.0 Replay；`traces/` 前後雜湊不變 | PASS |
| wrangler dev 本機實跑兩端點（Group1：封包 `0a9f53a15181931d`，邊緣↔Python 雙向一致） | PASS（沙盒本機） |
| Cloudflare 線上部署 | 待部署（先前 API token 驗證失敗，待建構者換新 token） |
| DL580 實機 | 待實機 |

映射狀態沿用 `../EVIDENCE.md`：除 `core → initiated` 外皆 provisional，本載體不改變任何映射授權。

## 線上驗收（追加，當下狀態 2026-10-02，Cloudflare 線上）

部署：`https://mrl-mother-platform.z814241.workers.dev`（帳號 MRLiou，Version `0d4a5e50-9249-44f4-9d28-36675c15d39d`）。上表「待部署」一列保留為部署前紀錄。

| 項目 | 結果 |
|---|---|
| 正典 `/api/rhythm/run`（Group1）→ 拒絕 provisional 映射 | PASS（線上） |
| 線上 Replay 本體 Python 的 EchoPersona.pcode 軌跡：逐位元組、封包 `0a9f53a15181931d` | PASS（線上） |
| 線上 run Group1 → 本體 Python Replay 一致 | PASS（線上） |
| v0.1.0 歷史軌跡 → 判為歷史、拒絕 v0.2.0 Replay | PASS（線上） |
| DL580 實機 | 待實機 |

## 補位既有 particle-replay（追加，當下狀態 2026-10-02，Cloudflare 線上）

Create Preflight 補做：帳號 MRLiou 線上已有 183 個 Worker，其中 `particle-replay`（L7-Meta）就是 Replay 的既有母體位置 → 決定 **SUPPLEMENT_EXISTING**，不另立新位。
（先前部署的 `mrl-mother-platform` 是新建、version 1、未覆蓋任何東西；保留，不刪。）

- 既有 `particle-replay` v1.0.0 只做「讀 DL580 `mrl_map_trace_log` 列出序列」，沒有重新執行節奏；而且當下 bridge 回 `error code: 1033`（DL580 tunnel 未連線），原路由全部 degraded。
- 補位版本 `e083ebb3-c570-4aac-848e-63a940fd2562`：原碼一字不改、原路由照舊；新增 `/rhythm`、`POST /rhythm/replay`、`POST /rhythm/run`，不依賴 bridge。
- 前一版 `cf8ef762-723b-4cff-b331-72c807bbea11` 留在 Cloudflare 版本歷史，可回滾。
- 原碼內含 bridge 金鑰，不入 repo；`particle-replay/deploy.sh` 部署時從線上取回。

| 項目（線上 particle-replay） | 結果 |
|---|---|
| 6 顆母體種子：Python 本體軌跡 → 線上 Replay，逐位元組＋封包一致 | 6/6 PASS |
| Group1、Group2：線上 run → Python 本體 Replay 一致 | 2/2 PASS |
| 正典預設拒絕 provisional 映射 | PASS |
| v0.1.0 歷史軌跡判為歷史 | PASS |
| 原路由 `/` 回應與補位前相同；`/health` 仍為 bridge 1033 degraded（非本次造成） | 已核對 |
| DL580 `mrl_map_trace_log` 列 → 節奏重播 | 待 bridge 恢復後接（trace_data 格式待讀） |

## 位置更正（追加，當下狀態 2026-10-03）

建構者提供 Workers Builds 日誌：本 repo 已連到既有 Worker **`mrliousilly`**（CI 以 `mrliousilly` 覆寫 `wrangler.jsonc` 的 `mrl-mother-platform`）。`src/mrl_worker.js` 的既有母體位置是 `mrliousilly`，不是新開的 `mrl-mother-platform`。

- 每次推任何分支，CI 只跑 `wrangler versions upload`，產生**預覽版本**，不動正式流量。`mrliousilly` 的正式版本仍是 2026-07-05 的 `3579c66f-e77f-4be8-9242-513d10557b8a`。
- 本分支已產生預覽版本 571／572，別名 `flowrhythm-edge-carrier-v0-mrliousilly.z814241.workers.dev`；在該預覽上 `/api/rhythm/replay` 重播 EchoPersona 軌跡結果為 ok（線上預覽）。
- `mrl-mother-platform` 是重複位置，保留不刪，待建構者裁定。
- 要讓 `mrliousilly` 正式流量帶上 FlowRhythm：`wrangler versions deploy` 指到本分支版本，待建構者決定。
