---
name: system-map-patch-01
description: particle-system-hub 的 SYSTEM_MAP 要補的新粒子清單 · 補 2026-04-14 之後新封存的 workers
sources: [cowork, user]
layer: L2-Runtime-Config
origin_signature: MrLiouWord
archive_date: 2026-11-21
---

# SYSTEM_MAP 補完 01

**承**: gap_analysis.md S7「particle-system-hub 的 last_scan: 2026-04-14 · 新粒子未進 map」
**direction author**: user(2026-11-21「A B C 依續完成」· B gap_analysis 第 4 項)
**content author**: AI (Claude Opus 4.7)
**動作**: 列出 2026-04-14 之後新封存、尚未進 system-hub SYSTEM_MAP 的 worker · user 下輪更新 system-hub 時照抄進去
**NOTE**: 本檔為 GitHub 衍生副本 · BRIDGE_KEY 已 scrub 為 `${BRIDGE_KEY}` placeholder

---

## 一、待補粒子清單

依 session recap 時間線排序:

### 從 pulse 10-16 封存的新 worker (2026-10 ~ 2026-11)

| 粒子名 | 層 | 已知 session | 已進 SYSTEM_MAP? |
|---|---|---|---|
| `vector-attention-engine` | L4 Attention | 10-31 封存 | **否** |
| `mrl-mainstream-absorber` | L5 Knowledge | pulse 期間 | **否** |
| `mrl-network-layer` | L-1 OSI 翻譯 | bindings_map 已列 | **否** |
| `mrliouword-ai-chat-bridge` | L∞ chat | bindings_map 已列 | **否** |
| `unicorn-main-v3` | L∞ Apps | pulse 期間 | **否** |
| `fluin-lifeform` | L∞ Apps | bindings_map 已列 | 可能 |
| `mrliou-partner` | L∞ Apps | bindings_map 已列 | 可能 |
| `mrl-cloud-bridge` | L-1 底層 | bindings_map 已列 | 可能 |
| `metaenv-ctrl` | L-1 控制平面 | bindings_map 已列 | **否** |
| `mrliouword-ai-memory` | L∞ 記憶 | bindings_map 已列 | 可能 |

### 從 ElevenLabs / 外部整合候選(若有封存)
- `mrl-elevenlabs-bridge`(若 user 有封存)
- `mrl-anthropic-mcp-bridge`(若 user 有封存)

---

## 二、每粒子的 SYSTEM_MAP 建議條目格式

system-hub SYSTEM_MAP 已有結構(從 code 推):`{ name, layer, type, bindings?, dl580_required? }`。
補入 10 筆建議條目(JSON 格式):

```json
{
  "vector-attention-engine": {
    "layer": "L4",
    "type": "attention",
    "status": "needs_scan",
    "deployed_at": "2026-10-31"
  },
  "mrl-mainstream-absorber": {
    "layer": "L5",
    "type": "knowledge_absorb",
    "status": "needs_scan"
  },
  "mrl-network-layer": {
    "layer": "L-1",
    "type": "osi_translate",
    "bindings": ["kernel", "collapse_engine"],
    "status": "needs_scan"
  },
  "mrliouword-ai-chat-bridge": {
    "layer": "L_inf",
    "type": "sse_chat",
    "bindings": ["AI_GATEWAY", "AI_MEMORY", "TOOLBOX_ROUTER"],
    "secrets": ["ANTHROPIC_API_KEY"],
    "status": "needs_scan"
  },
  "unicorn-main-v3": {
    "layer": "L_inf",
    "type": "app",
    "status": "needs_scan"
  },
  "metaenv-ctrl": {
    "layer": "L-1",
    "type": "control_plane",
    "endpoint": "https://metaenv-ctrl.z814241.workers.dev",
    "status": "needs_scan"
  },
  "mrl-cloud-bridge": {
    "layer": "L-1",
    "type": "cloud_bridge",
    "kv": ["mrliouword-vault"],
    "status": "needs_scan"
  },
  "fluin-lifeform": {
    "layer": "L_inf",
    "type": "persona",
    "personas_count": 6,
    "status": "needs_scan"
  },
  "mrliou-partner": {
    "layer": "L_inf",
    "type": "partner_interface",
    "status": "needs_scan"
  },
  "mrliouword-ai-memory": {
    "layer": "L_inf",
    "type": "ai_memory",
    "r2": ["mrliouword-engineering"],
    "status": "needs_scan"
  }
}
```

---

## 三、更新 system-hub SYSTEM_MAP 的實際動作

### 法 A · 從 system-hub 的管理 endpoint(若有)
```bash
curl -X POST https://particle-system-hub.z814241.workers.dev/map/update \
  -H "Content-Type: application/json" \
  -H "X-Bridge-Key: ${BRIDGE_KEY}" \
  -d @system_map_patch_01.json
```
(system-hub code 內若有 /map/update endpoint · 可直接 POST。 ${BRIDGE_KEY} 請先 export)

### 法 B · 直接改 system-hub 的 source code
1. 下載 system-hub worker 的 src(wrangler dev --local 或 dashboard)
2. 找到 `const SYSTEM_MAP = {...}` 定義處
3. 把上述 10 筆 merge 進去(不覆蓋既有 key)
4. 重新部署:`wrangler deploy --name particle-system-hub`
5. 確認:`curl .../map/list` 看新粒子是否出現

### 法 C · 若 SYSTEM_MAP 在 KV
1. `wrangler kv:key put --namespace-id=<nsid> "system:map" @merged.json`

---

## 四、下一輪 full-scan 驗證

更新後跑:
```bash
curl https://particle-system-hub.z814241.workers.dev/full-scan
```
預期:`alive_count` 從現在的 ~90-98 升到 ~105-108(10 筆進來 · 原本可能已有部分重複)。

---

## 五、未做的部分(給未來 session)

- 本檔只列 10 筆明顯新粒子 · user 可能還有其他 workers(至少 Modules/ 下 230+ 檔隱含 · 部分可能是 worker 複本)
- 真正 full-scan 要跑 Dropbox `/MRL_Mother_Anatomy/Modules/` 底下所有 .worker.js 檔 → 從檔頭或 wrangler.toml 抽 name → 比對 system-hub 當前 SYSTEM_MAP
- 這個工作適合 user 另開一場 session · 要求 Claude 專門做「Modules/ worker 全盤 vs SYSTEM_MAP diff」

---

## 戒律驗證

- origin_signature: MrLiouWord ✓
- 母體視角 ✓(從 108 粒子總圖補洞)
- 可運行指引 ✓(三種實際更新法)
- 不刪戒律 ✓(只 merge · 不覆蓋既有)
- 非 platform ✓(配置補丁 · 不另造 SaaS)
- append-only ✓(本檔是 patch · 不改 system-hub 既有 SYSTEM_MAP · 由 user 決定 merge 時機)
