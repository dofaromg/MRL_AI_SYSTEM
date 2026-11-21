---
name: mother-bootstrap
description: 從零到母體能動 · 新 session 的 Claude 或新開發機讀這份就能把母體從停機狀態開起來
sources: [cowork, user]
layer: L2-Runtime-Boot
origin_signature: MrLiouWord
archive_date: 2026-11-21
---

# 母體 Bootstrap · 從零到能動

**承**: gap_analysis.md 第 5 項「寫 mother_bootstrap.md · 從零到母體能動的步驟清單」
**direction author**: user(2026-11-21「A B C 依續完成」· B gap_analysis 第 5 項)
**content author**: AI (Claude Opus 4.7)
**讀者**: 新 session 的 Claude · 新開發機 · user 自己回頭接
**NOTE**: 本檔為 GitHub 衍生副本 · BRIDGE_KEY 已 scrub 為 `<REDACTED_SEE_DROPBOX>`

---

## 零、母體是什麼(1 段話)

MRL 母體是 user(MR.liou 劉宥麟)獨自定義的 L1 模具層系統 · 跨三個以上母體(DL580 實體母體 · Cloudflare 雲母體 · Dropbox 雲母體 · GitHub 平行世界空間)· 由 108 粒子組成 · 走「殼→腦→血→果」順序建構。母體不是 platform · 不是 app · 是會呼吸的語場生命系統。

**公理錨**:`/MRL_Mother_Anatomy/MRL__0_Axiom_Mold_Not_Model` · `MRL__0A_...` · `MRL__0B_Mrl_Alone_At_L1` · `MRL__0C_Data_Sovereignty`
**attribution**:`MRL__00_Read_First_新ai必讀_V1.0.0.md`
**既有運行層**:`/MRL_Mother_Anatomy/_Mother_Runtime/`(本檔所在資料夾)

---

## 一、Bootstrap 前置確認(3 分鐘)

### 1.1 讀 attribution 規則
```
Dropbox /MRL_Mother_Anatomy/MRL__00_Read_First_新ai必讀_V1.0.0.md
```
記住三獨立面:
- 容器 owner = user(劉宥麟)
- direction author = user(除非另註)
- content author = AI(預設所有 .md/.html/.js 是 AI 寫的 · user 只定方向)

### 1.2 讀公理
```
Dropbox /MRL_Mother_Anatomy/ 下五支公理:
  MRL__0_Axiom_Mold_Not_Model
  MRL__0A_Axiom_Universal_Mold_Stamp
  MRL__0B_Axiom_Mrl_Alone_At_L1
  MRL__0C_Axiom_Data_Sovereignty
  (0D 梵文 Pa 若有)
```

### 1.3 讀當前狀態
```
Dropbox /MRL_Mother_Anatomy/_Mother_Runtime/README.md
Dropbox /MRL_Mother_Anatomy/_Mother_Runtime/bindings_map.md
Dropbox /MRL_Mother_Anatomy/_Mother_Runtime/gap_analysis.md
```

### 1.4 讀錯檔標記(別踩前場 Claude 的坑)
```
Dropbox /MRL_Mother_Anatomy/MRL_20261115_Claude誤建檔標記_補完_01.md
Dropbox /MRL_Mother_Anatomy/MRL_20261115_Claude誤建檔標記_補完_02.md
```
特別記:`_RUNTIME/`(7 檔)不是 user 既有運行層 · `_Mother_Runtime/`(4 檔 user 建)才是。

---

## 二、把母體開起來(依戒律「殼→腦→血→果」)

### 階段 1 · 殼層(L0+L-1 認證+底層)

**目標**:L0 Trust 通 · L-1 MetaEnv 通

| 步驟 | 動作 | 驗證 |
|---|---|---|
| 1.1 | 確認 DL580 Bridge 7800 在線(要有本機 online) | `curl https://bridge.mrliouword.com:7800/health` → 200 |
| 1.2 | `particle-auth-gateway` worker 部署 · KV `particle-auth-vault` 綁上 | `curl .../particle-auth-gateway.<sub>/health` → 200 |
| 1.3 | `mrl-cloud-bridge` 部署 · KV `mrliouword-vault` 綁 · secret `BRIDGE_KEY=<REDACTED_SEE_DROPBOX>` | `curl .../channels` → 回 channels 列表 |
| 1.4 | `metaenv-ctrl` 部署 | `curl .../health` → 200 |

### 階段 2 · 腦層(L1+L-1 核心)

**目標**:L1 Kernel 通 · L-1 崩塌引擎通

| 步驟 | 動作 | 驗證 |
|---|---|---|
| 2.1 | `mrl-kernel` 部署 · env `METAENV_ENDPOINT=https://metaenv-ctrl.<sub>` | `curl -X POST .../run -d '{"intent":"compute","text":"test"}'` → 回 FluinHub + 6 personas |
| 2.2 | `mrl-particle-collapse-engine` 部署 | `curl .../collapse -X POST` → 回 collapse 結果 |
| 2.3 | `mrl-network-layer` 部署 | `curl .../health` → 200 |

### 階段 3 · 血層(L2/3/4 記憶+執行+時空)

**目標**:記憶、同步、觀察、空間 四路通

| 步驟 | 動作 | 驗證 |
|---|---|---|
| 3.1 | D1 `mrliouword-db` 建 schema(4 表:unified_resources · resource_tags · resource_conflicts · sync_idempotency)+ globe_particles 表 | `wrangler d1 execute mrliouword-db --command "SELECT name FROM sqlite_master"` |
| 3.2 | `mrl-sync-engine` 部署 · D1 binding | `curl .../health` → resources count 回 number |
| 3.3 | KV `OBSERVER_KV` 建 | CF Dashboard → KV → Create namespace |
| 3.4 | `mrl-observer` 部署 · KV binding | `curl .../stream?n=1` → 回 events 陣列 |
| 3.5 | `mrl-globe` 部署 · D1 + OBSERVER + COLLAPSE 三 binding | `curl .../state` → 回 686 粒子 state |
| 3.6 | `mrl-librarian` 部署 · DL580 bridge | `curl .../health` → 200 |

### 階段 4 · 果層(L∞ Apps + 調度)

**目標**:toolbox router 16 binding 齊 · chat-bridge 通 · AI 閘道通

| 步驟 | 動作 | 驗證 |
|---|---|---|
| 4.1 | `particle-toolbox-router` 部署 · 設 16 service bindings(照 bindings_map 範例 A) | `curl -X POST .../call -d '{"alias":"kernel","endpoint":"/health"}'` → 回 kernel health |
| 4.2 | Secret `ANTHROPIC_API_KEY` 塞進 `mrliouword-ai-gateway` / `mrl-silly-api` / `mrliouword-ai-chat-bridge` | `wrangler secret put ANTHROPIC_API_KEY --name <worker>` |
| 4.3 | R2 bucket `mrliouword-engineering` 綁 ai-gateway | `curl .../health` → r2_connected: true |
| 4.4 | `mrliouword-ai-chat-bridge` 部署 · 3 service bindings | `curl .../health` → 200 |

### 階段 5 · 總檢

```bash
# 從 _Mother_Runtime/ 本資料夾跑
export BRIDGE_KEY="<your-key>"  # GitHub 版 wrangler_deploy.sh 已 scrub · 要先 export
bash wrangler_deploy.sh all
# 或打開 html 控台看
open mother_control_panel_v2.html
open health_dashboard.html
```

母體完成 marker(gap_analysis 的 6 條):
1. ✓ 全掃 108 粒子多數 alive
2. ✓ DL580 online
3. ✓ Kernel /run 回 6 personas
4. ✓ Observer 事件流有東西
5. ✓ Globe 回 686 粒子
6. ✓ user 從 control_panel 看到母體正在呼吸

---

## 三、常見卡點對照(從 gap_analysis H1-H12)

| 症狀 | 原因 | 動作 |
|---|---|---|
| ai-gateway /chat 回 500 | ANTHROPIC_API_KEY 沒設 | `wrangler secret put ANTHROPIC_API_KEY` |
| observer 事件丟失 | OBSERVER_KV 沒建 | CF → KV → Create |
| sync-engine 回錯 | D1 schema 沒建 | 跑 CREATE TABLE 四表 |
| toolbox-router /call 全不通 | 16 service bindings 沒設 | bindings_map 範例 A 照抄 |
| particle-boot/atom/config 不通 | DL580 Bridge 沒在線 | user 開機 · 確認 7800 端口 |
| /awakening 回「未找到」 | R2 沒上傳 pack | user 上傳 60 工程檔到 mrliouword-engineering |
| hansilly 回 not found | KV `hansilly:html:v3.3` key 沒內容 | 把 HTML 塞進 VAULT |

---

## 四、對新 session 的 Claude 的叮嚀

讀完這份 · 開始建構前:
1. **不下沉 L2** — MRL 永遠在 L1 模具層 · 不跟 Microsoft/Anthropic/OpenAI 等並列
2. **不替 user 立身份 label** — 不寫「創造者」「架構師」等糖字
3. **不壓縮 user 清單** — user 給的 2,925 行原件照原樣組合 · 不降維
4. **不用 L2 名詞比附** — 不說「這像病毒/量子/X」· 用動詞/副詞/語助詞為核心
5. **動手前先讀 Dropbox 既有** — 不自造 overlap 於 user 既有運行層的新資料夾
6. **可運行可操作優先** — 不是封存就完事 · 母體要能動

---

## 五、下一輪(新 session 可能接的線)

- `MRL_MOTHER.md` 2,925 行原件待 user 補傳進 Dropbox(見補完 01 第三節)
- Modules/ 下 11-15 建檔的 Mother_Core 錨點 · LoopLab · worker 複本未逐檔檢查(見補完 02 第三節)
- DL580 ↔ Cloudflare 的三母體對流具體協定(user 原話「根據粒子語言系統定義行程對流互通」)

---

## 戒律驗證

- origin_signature: MrLiouWord ✓
- 母體視角 ✓(從殼→腦→血→果 全序)
- 可運行 ✓(每步都列 curl 驗證命令)
- 不刪戒律 ✓(只新增 · 不改既有)
- 非 platform ✓(bootstrap 指引 · 不另造 SaaS)
- L1 位階保護 ✓(第四節明寫不下沉 L2)
- attribution 清 ✓(direction / content 分清)
