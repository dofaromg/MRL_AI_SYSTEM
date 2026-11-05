# MRL_AI_SYSTEM — 介紹與使用說明

> `origin_signature: MrLiouWord` ｜ 母體為最高權威 ｜ Additive-Only（只新增、只定位、不刪除、不覆蓋）

---

## 一、這是什麼（介紹）

**MRL 完整態母體運轉系統** —— Mr.liou 的統一 AI 母體。由你陸續交付的檔案匯集而成，
本包把它們**整理連接**成一個可導覽、可開機的整體，並附上一張**頂層粒子符號索引**。

系統的骨幹是 00–09 十層母體結構（根律法 → 綱要 → 原則 → 記憶 → 運行 → 人格 →
追跡 → 吸收 → 源料 → 工作流），核心為母體本體（MotherAssembly），對外由平台伺服器
與 Cloudflare Worker 邊緣門面（`mrliouword.com`）承接。所有產物皆蓋 `origin_signature: MrLiouWord`。

- **權位區分**：Worker/平台 = 邊緣門面（Adapter）；真母體運算在 DL580 自運行節點。
- **主權索引**：頂層粒子符號索引把每一個模組/粒子連到既有權威註冊表，不虛構。

---

## 二、包裡有什麼

| 檔案 | 作用 |
|---|---|
| `MRL_頂層粒子符號索引.md` | **主索引**（可讀）：骨幹 / 分區 / 主線節點 / 粒子庫 / 服務網格，一頁看全貌 |
| `MRL_頂層粒子符號索引.json` | 同上，機器可讀版 |
| `MRL_介紹與使用說明.md` | 本檔 |
| 其餘目錄/檔案 | 你原本交付的完整倉庫內容（母體骨幹、各 MRL_ 模組、src、data…），原樣保留 |

---

## 三、怎麼開機（使用說明）

### A. 對外平台（零依賴，最簡）
需要 Python 3.11+。解壓後在包根目錄執行：
```bash
python3 MRL_Platform_Server.py
# 預設 http://127.0.0.1:8790/
```
- `GET /`         → 產品 UI（登入器 + 模組）
- `GET /health`   → `{"ok":true,"origin_signature":"MrLiouWord","status":"running",...}`
- `GET /mrl/state`→ 母體狀態

換埠：`MRL_PORT=9000 python3 MRL_Platform_Server.py`
接真後端：設 `MRL_MOTHER_GATEWAY_URL=https://<你的DL580對外網址>` 再開機（未設則誠實回「DL580 未連」，不偷用外部模型）。

### B. Node 運行伺服器
需要 Node 18+：
```bash
node MRL_RuntimeServer.js
```

### C. Cloudflare Worker 邊緣門面
入口 `src/mrl_worker.js`，設定 `wrangler.jsonc`。部署到 `mrliouword.com` 需在
Cloudflare 綁定網域（route / custom domain）—— 此步在 Cloudflare 端設定，非本包內。

---

## 四、怎麼讀索引

1. 先開 `MRL_頂層粒子符號索引.md`。
2. 「母體骨幹 00–09」看整體分層；「頂層粒子符號分區」看各模組落點與職責。
3. 「母體主線節點」接 `MRL_MotherModel/module_registry.json`（含 `MRL.NODE.04.Particle` 的 220 來源計數）。
4. 「粒子檔案庫」接 `MRL_ParticleArchive/MRL_ParticleArchive_manifest.json`（每顆粒子有 `_sig_hash` 可驗簽）。
5. 「服務網格」接 `MRL_ServiceMesh_Registry_v1.json`。

---

## 五、法則備註（沿用 CLAUDE.md）

- **Additive-Only**：只新增、只定位，不刪除、不覆蓋。外部檔案一律視為母體吸收之知識，給位置、標來源，回收為母體名稱產物。
- **狀態誠實**：實跑過才寫 PASS；未驗的標「待驗證/待實機」。
- 本包內容皆為你既有倉庫檔案 + 本頁索引/說明；未改動任何原始檔案語義。

_origin_signature: MrLiouWord_
