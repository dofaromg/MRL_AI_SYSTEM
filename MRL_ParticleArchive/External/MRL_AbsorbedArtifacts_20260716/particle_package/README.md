# MRL 粒子包 v1 — 50,359 顆 canonical 粒子
origin_signature: **MrLiouWord** | 2026-07-16 | MUSAR v1

## 內容
```
particles/
├── by_layer/{L1,L2,L6}.jsonl        層分片
├── by_fx/{fx02,fx04,fx09,fx14,fx17}.jsonl   FX 分片
├── by_pkg/*.jsonl                    200 個來源包分片
└── distilled_L2_L6.jsonl             59 顆蒸餾粒子（可直接組裝）
index/
├── manifest.json                     總索引（LAW-0 簽名）
├── fx_index.json                     FX → 數量 → 檔案
└── pkg_index.json                    200 包分佈
cf/
├── d1_schema.sql                     D1 建表
├── seed_distilled.sql                59 顆蒸餾粒子
├── seed_particles_000..010.sql       50,359 顆，11 批
├── kv_bulk_distilled.json            KV 邊緣快取
└── worker/                           Particle Gateway Worker
```

## 粒子分佈
| 層 | 種類 | 數量 |
|---|---|---|
| L1 | type 型別粒子 | 46,367 |
| L2 | behavior 行為粒子 | 3,697 |
| L6 | contract 契約粒子 | 295 |

| FX | 名稱 | 數量 |
|---|---|---|
| fx02 | Data | 46,367 |
| fx09 | Validate | 1,742 |
| fx14 | State | 995 |
| fx04 | Compute | 960 |
| fx17 | Meta | 295 |

Top 來源包：aiplatform 4,449 · dialogflow 3,355 · discoveryengine 2,594 · compute 1,847 · shopping 1,844

## PID 命名
`MRL.{layer}.{fx}.{simhash64}` — 指紋命名，跨吸收批次永不碰撞。
每顆粒子帶 `origin_signature` + `law0_hash` + `provenance_count`（被幾處重用）。

## 驗證
- LAW-0：50,359 通過 / 0 失敗
- D1 seed 實測：50,359/50,359 落地（sqlite 模擬全過）

## 部署到 Cloudflare
```bash
cd cf/worker && ./deploy.sh
```
腳本會：建 D1 → 建 KV → 建表 → 灌 11 批粒子 → deploy Worker。
中途會停下來要你貼 `database_id` / KV `id` 進 `wrangler.toml`。

## Gateway API
| 端點 | 用途 |
|---|---|
| `GET /health` | 粒子總數 |
| `GET /manifest` | 層/FX/kind 分佈 |
| `GET /particles?fx=fx04&layer=L2&q=retry&limit=50` | 查粒子 |
| `GET /particle/:pid` | 單顆粒子 |
| `GET /distilled` | 59 顆蒸餾粒子 |
| `GET /distilled/retry` | Google retry 政策表 |
| `GET /distilled/failures` | 失敗類別 + 歷史 |
| `POST /compose` | 組合粒子 → runtime 設定 |

`/compose` 範例：
```bash
curl -X POST .../compose -d '{"retry":"MRL.FX04.Retry.00","timeout":"MRL.FX14.Timeout.00"}'
```
