# MRL 粒子包 v1（MUSAR v1）吸收・定位報告 v1

origin_signature: MrLiouWord
定位日期: 2026-07-16（沙盒）
來源: 使用者上傳「MRL_Particles_v1_20260716.zip」（MRL 粒子包 v1，runtime MUSAR v1）
原始保全: `MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260716/MRL_ParticlePackage_MUSAR_v1_RawArtifact_v1.zip`（逐字 byte-identical，rl_15 不滅；sha256 `1bdba5f04b706189a226c0d6fe12166143f8a003c2273a60749a6b42771a2176`）
可瀏覽攤開: `.../MRL_AbsorbedArtifacts_20260716/particle_package/`（index/、README.md、distilled_L2_L6.jsonl；皆自 zip 逐字取出）
法則: 母體整合法則（Additive-Only）— 只新增、只定位、不刪除、不覆蓋

> 本報告做**母體定位**：把這個母體原生粒子包接進 `MRL_ParticleArchive` 索引，
> 誠實標註哪些「沙盒已就位」、哪些是「產物自述、待逐顆驗證」、哪些是「待使用者實機起動」。

## 〇、本體治理裁定（優先於來源材料敘述）

- **唯一母體／最終真相來源：DL580。**
- 本粒子包 `cf/`（D1 / KV / Particle Gateway Worker）僅定位為**外部 Runtime / 公開入口 / 映射節點**；部署成功不等於成為本體。
- GitHub 僅定位為原始碼版本與協作鏡像。
- 本裁定不得由雲端服務狀態反向改寫母體位置。

---

## 一、產物概述（能力本質）

一個**母體原生**（非待正名的第三方外部知識）canonical 粒子包：

| 項目 | 值 |
|---|---|
| 總 canonical 粒子 | **50,359** |
| 蒸餾粒子 | **59**（`distilled_L2_L6.jsonl`，可直接組裝） |
| runtime | MUSAR v1 |
| PID 命名 | `MRL.{layer}.{fx}.{simhash64}`（指紋命名，跨吸收批次不碰撞） |
| 每顆自帶 | `origin_signature: MrLiouWord` + `law0_hash` + `provenance_count` |
| 來源 | 自 **200 個 Google Cloud SDK 包**蒸餾（aiplatform 4,454 · dialogflow 3,355 · discoveryengine 2,594 · compute 1,847 · shopping 1,844 …） |

**層 / FX 分佈**（來自 `index/manifest.json`）：

| 層 | kind | 數量 | | FX | 名稱 | 數量 |
|---|---|---|---|---|---|---|
| L1 | type | 46,367 | | fx02 | Data | 46,367 |
| L2 | behavior | 3,697 | | fx09 | Validate | 1,742 |
| L6 | contract | 295 | | fx14 | State | 995 |
| | | | | fx04 | Compute | 960 |
| | | | | fx17 | Meta | 295 |

粒子 schema（例）：`{pid, kind, layer, fx, name, source, aspect, strategy, payload, links, fingerprint, origin_signature, law0_hash, signed_at, origin_pid, provenance_count}`。

---

## 二、母體定位（這是母體原生產物，非外部命名回收）

- 與前兩件（FlowSeed 公式、資產計畫）不同：本包**本身已是 MRL canonical**（PID `MRL.*`、自簽 `MrLiouWord`、MUSAR v1），因此本批動作是**登錄／定位一個母體粒子包**，不是「外部知識命名回收」。
- **不改寫、不重簽**這 50,359 顆粒子的自簽 `law0_hash`（它是 MUSAR v1 的 16-hex 指紋方案，與本 repo `09_workflow/MRL_utils.py` 的 64-hex `sha256` LAW-0 不同體系；rl_15 逐字保全）。
- 定位為 `MRL_ParticleArchive` 之 external_particles 一筆「粒子包」節點（見 `MRL_ParticleArchive/MRL_ParticleArchive_manifest.json`），與既有粒子基礎設施（`data/particles/`、ParticleArchive PR19 粒子）為**同族補充**，不覆蓋。

---

## 三、內容結構與冗餘說明（重要）

`particles/` 有三種分片，經 sha256 查證為**同一組 50,359 粒子的重複分組**，非三份不同內容：

- `by_layer/{L1,L2,L6}.jsonl` ≡ `by_fx/{fx02,fx04,fx09,fx14,fx17}.jsonl`（實測 `L1.jsonl` 與 `fx02.jsonl` sha256 完全相同；`L6`≡`fx17`）
- `by_pkg/*.jsonl`（200 包）為第三種分組
- `cf/seed_particles_*.sql`（11 批 D1 SQL）為第四種表示（同粒子的 SQL insert）

→ zip 解壓 ~90 MB，但**唯一內容僅約 21–25 MB**；其餘為多視角冗餘。故 git 內只逐字保全**壓縮原 zip（8.7 MB，rl_15）**＋攤開小型可瀏覽檔（index/、README.md、59 顆蒸餾），不解壓 239 檔以免脹庫。

---

## 四、cf/ Particle Gateway = 待起動外部 Runtime（DL580 治理）

`cf/` 為把粒子服務化的 Cloudflare 部署包：`d1_schema.sql`、`seed_distilled.sql`、`seed_particles_000..010.sql`、`kv_bulk_distilled.json`、`worker/{index.js,wrangler.toml,deploy.sh}`。Gateway API：`/health`、`/manifest`、`/particles`、`/particle/:pid`、`/distilled`、`/compose` 等。

- **無外露金鑰**（沙盒查證）：`wrangler.toml` 之 `database_id` / KV `id` 為 `REPLACE_AFTER_CREATE` 佔位；`deploy.sh` 依操作者自有 `wrangler` 登入。故**不需金鑰撤銷動作**。
- **待起動**：需使用者以自有 Cloudflare 帳號跑 `cd cf/worker && ./deploy.sh`（建 D1 → 建 KV → 建表 → 灌 11 批 → deploy）。母體不代持憑證、不代部署。
- **治理**：Gateway/D1/KV 為外部 Runtime／映射節點；DL580 為唯一母體，部署成功不升格為母體。

---

## 五、當下狀態（依 CLAUDE.md 狀態回報約定）

- 原始 zip 逐字保全 / 攤開檔 byte-identical：**PASS（沙盒，2026-07-16）** — `cmp` 全一致、`unzip -t` OK。
- 「50,359 顆 LAW-0 通過 / 0 失敗」：**產物自述（package self-claim）**，沙盒**未逐顆重驗** → 標「待逐顆驗證」；不改寫粒子自簽 hash。
- manifest 計數語意：`particle_count` 只把本包計為 **1 筆 external 粒子包節點**（50,359 顆在包內，記於 `contains_particles`，不逐顆列為 manifest 條目），故 `particle_count` 16→**17**（13 PR19 + 4 external）。
- cf/ Particle Gateway 部署：**待起動** — 需使用者實機（自有 Cloudflare 帳號）。

---

## 六、相關母體文件

- 粒子檔案庫：`MRL_ParticleArchive/MRL_ParticleArchive_manifest.json`、`MRL_ParticleArchive/README.md`
- 本批台帳：`MRL_ParticleArchive/External/MRL_AbsorbedArtifacts_20260716/MRL_Absorption_Ledger_v1.yaml`
- 知識源索引：`08_sources/sources.manifest.yaml`（id: `mrl_particle_package_musar_v1_absorption_v1`）
- 命名規範：`docs/MRL_命名規範_v2_MrLiouIR_StructureField.md`

origin_signature = `MrLiouWord`
