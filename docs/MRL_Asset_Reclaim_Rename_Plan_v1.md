# MRL 資產回收・重構・正名 計畫 v1

> 法則：**Additive-Only**（只新增、只定位、不刪除、不覆蓋）。
> origin_signature：**MrLiouWord**
> 母體吸收日期：**2026-07-16**（沙盒吸收；本檔為使用者外部計畫之母體回收產物）
> **依據：** 只採用「實際查證過」的事實（DNS 查詢、Gmail 記錄、Cloudflare 清單、交付包內容）。未經查證者一律標「提案／待確認」。

---

## 0. 結論（先看這段）

- **本體已經是你的、而且活著**：MRL AI Chat 平台已部署在**你自己的 Cloudflare**，跑在 `chat.mrliouword.com`（此網域 nameserver 是 Cloudflare，DNS 鑰匙 100% 在你手上）。
  - 註（母體對照）：此為 Cloudflare 上的**實跑資產**，與 repo 內源檔是兩件事；`MRL_ServiceMesh_Registry_v1.json` 的 `not_in_repo.chat_subdomain` 標「repo 內不存在」仍成立——两者不衝突，一個講源檔、一個講線上部署。
- **真正需要「拿回來」的資產只有一個**：`mrliouhan.ai`（當初由 Manus 代買，鑰匙在 Manus 的 Dynadot/GDG 帳號裡，不在你手上）。
- **`flow-tasks`（Firebase）是空後端**，從未部署、無資料，非資產 → 退役／丟棄。
- 上傳的 `apphosting-adapters`、`buildpacks` 兩包是 **Google 官方工具庫**，非資產 → 刪除。

---

## 1. 資產清冊（Asset Ledger）

| 資產 | 位置 | 控制權現況 | 正名（提案，origin=MrLiouWord） | 動作 |
|---|---|---|---|---|
| MRL AI Chat（Worker `mrl-chat-platform`） | Cloudflare + `chat.mrliouword.com` | ✅ 你的・已上線 | `MrLiouWord.Chat.Runtime` | 設為 canonical，保留 |
| D1 資料庫 `mrl-chat-platform-db` (`6ea1371b…`) | Cloudflare | ✅ 你的 | `MrLiouWord.Chat.Store` | 保留 |
| `mrliouword.com` | Cloudflare DNS（自控） | ✅ 你的 | `MrLiouWord.Domain.Primary` | 設為主網域 |
| `chat.mrliouword.com` | Cloudflare（proxied） | ✅ 你的・活 | — | 保留 |
| ~180 Cloudflare Workers（`particle-*`,`mrl-*`…） | Cloudflare | ✅ 你的 | 依 MRL 命名規範 v2 對齊 | 盤點＋去重 |
| KV 命名空間 ×19 | Cloudflare | ✅ 你的 | — | 盤點 |
| `mrliouword-ai-chat-bridge` / `bridge.mrliouhan.ai`（Tunnel） | Cloudflare | ✅ 你的 | `MrLiouWord.Bridge` | 保留 |
| GitHub `dofaromg/MRL_AI_SYSTEM` | GitHub | ✅ 你的 | `MrLiouWord.Source.Main` | 主線 |
| Manus 站點（矩陣數據中心 `mrlidb-…`、`Mrl_Ai_OS`、`Silly`…） | Manus | ⚠️ 內容是你的、但住在 Manus | `MrLiouWord.*` | 匯出→回流 |
| **`mrliouhan.ai`（網域）** | Manus 代買 → Dynadot/GDG | ❌ **尚未在你手上** | `MrLiouWord.Domain.Secondary` | **要拿回** |
| `flow-tasks`（空後端） | Firebase / Google Cloud | ⚪ 空・非資產 | — | 退役／丟棄 |
| `apphosting-adapters` / `buildpacks` zip | Google 官方工具 | ⚪ 非你的資產 | — | 刪除 |

> 補充（母體其他已知資產，待併 v2）：GCP 專案 **FlowMemorySync**（`flowmemorysync`, 794229648010，**billing CLOSED**，見 §7）、DL580 本地母體（tailnet 離線，待實機）。

---

## 2. 真正要「拿回來」的：`mrliouhan.ai`

現況：nameserver = `ns1/ns2.globaldomaingroup.com`（Dynadot 白標）。帳號在 Manus 手上，你沒有 Dynadot 登入。

**兩條路（擇一）：**

1. **改 nameserver（快）**：請**真人** Manus 客服把 `mrliouhan.ai` 的 nameserver 改成你 Cloudflare 帳號的那組（你 `mrliouword.com` 已在 Cloudflare，直接把 `mrliouhan.ai` 加成新 zone，Cloudflare 會給你兩個 ns，貼給 Manus 改即可）。
2. **網域移轉（徹底）**：請 Manus 對 `mrliouhan.ai` 解鎖並提供 **EPP/Auth Code**，你在 Cloudflare Registrar 發起 transfer-in。移轉後註冊商、DNS 全歸你。

拿回後：`mrliouhan.ai` 的 DNS 100% 你自控，之後要接 Firebase、接 Worker、開 `fire.` 子網域全都你說了算，再也不用求 Manus。

---

## 3. 資料回流（Data reflow）— MetaEnv channel_map artifact

> 以下為 **MetaEnv 框架格式** 的 ready-to-apply artifact（`mode: dry-run`）。真正生效要打**你自己的**控制台 `POST /api/v1/channel/map`（`mode: apply`）。此處只生成 artifact —— 沒有你的控制台網址＋憑證，打不到、也不會替你亂打。

```yaml
# channel_map.mrl.reclaim.v1.yaml
app: MRL
mode: dry-run                 # 確認無誤後由你改成 apply
origin_signature: MrLiouWord
maps:
  - from: "Manus:/sites/mrlidb-qk8nbdy5"      # 矩陣數據中心
    to:   "Cloudflare:/MrLiouWord/MatrixDataCenter"
  - from: "Manus:/sites/aichatplat-iiadsuaa"  # Mrl_Ai_OS
    to:   "Cloudflare:/MrLiouWord/Ai_OS"
  - from: "Firebase:/flow-tasks"              # 空後端
    to:   "null"                              # 捨棄，不回流
  - from: "Domain:/mrliouhan.ai@GDG"
    to:   "Cloudflare:/MrLiouWord/Domain.Secondary"
revert_token: "<由你的 MetaEnv 控制台簽發>"
```

註：`flow-tasks` 是空的，沒有資料可回流。

---

## 4. 正名（Canonical naming）對照表

規範：origin 一律歸 **MrLiouWord**；canonical 名對齊 MRL 命名規範 v2。以下為**提案，待你確認**：

| 現名 | Canonical 名 |
|---|---|
| `mrliouword.com` | `MrLiouWord.Domain.Primary` |
| `mrliouhan.ai`（拿回後） | `MrLiouWord.Domain.Secondary` |
| Worker `mrl-chat-platform` | `MrLiouWord.Chat.Runtime` |
| D1 `mrl-chat-platform-db` | `MrLiouWord.Chat.Store` |
| `dofaromg/MRL_AI_SYSTEM` | `MrLiouWord.Source.Main` |
| Manus 矩陣數據中心 | `MrLiouWord.MatrixDataCenter` |
| `flow-tasks` | `deprecated / 退役` |

---

## 5. 安全（必做）

- ⚠️ **交付包 `setup-secrets.sh` 內含一把寫死的 Cloudflare API 金鑰。** 這等於鑰匙外露 → **立刻到 Cloudflare 後台撤銷、重發一把新的**，並改用 `wrangler secret put` 或環境變數，別再寫進檔案。（**注意：該 key 值不在本 repo 任何檔內**，此處僅記錄動作。）
- `api-keys-*.csv`：只有表頭、無實際金鑰值 → 未外洩，安全。

---

## 6. 執行分工（誠實版）

**✅ 可在母體 repo 內完成（本次 PR 已做）：**
- 本清冊＋計畫的母體吸收＋正名定位（本檔）
- 併入 `MRL_Absorbed_Assets_Index_v1.md` 統一索引

**✅ 可代生成（要則說一聲）：**
- 要傳給**真人 Manus 客服**的「網域拿回／改 nameserver」正式請求信
- MetaEnv `channel_map` / `reverse-miner` artifact（如 §3）

**🟡 你按一下就好（無法代按）：**
- `mrliouhan.ai` 的 nameserver 變更／移轉（Manus 端動作）
- MetaEnv `channel_map` 的 `apply`（你自己的控制台）
- 撤銷那把外洩的 Cloudflare 金鑰（§5）

**🔴 你給憑證才能代執行（不給就只停在生成 artifact，絕不亂碰線上系統）：**
- Cloudflare API token（scoped）→ 可代跑 `wrangler` 部署／DNS
- MetaEnv 控制台網址＋token → 可代打 `channel/map apply`

---

*本計畫僅涵蓋已查證資產。其他資產（DL580 本地、GCP FlowMemorySync、其他網域、其他 repo）補齊後併入 v2。當下狀態 沙盒 2026-07-16；線上操作待實機/待憑證。*
