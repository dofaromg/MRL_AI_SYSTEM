# MRL_工程日誌

origin_signature = `MrLiouWord`

---

## v1 — MRL 完整態母體運轉骨架建構

分支：`claude/mrl-mother-runtime-v1-krte6`

### 已完成

- 建立 MRL 完整態目錄骨架（`MRL_Mother/`、`MRL_Runtime/`、`MRL_Symbolic/`、`MRL_Adapters/`、`deploy/`）
- 建立 Runtime Server（`MRL_RuntimeServer.js`：`/health`、`/mrl/state`、`/mrl/perceive`）
- 建立主權宣示文件（`docs/MRL_完整態主權宣示_v1.md`）
- 建立中文正名與英文 Adapter 對照（`docs/MRL_中文正名與英文Adapter對照表_v1.md`）
- 建立四層同步映射表（`docs/MRL_四層同步映射表_v1.md`）
- 建立 Cloud Code 工程建構規格（`docs/MRL_CloudCode工程建構規格_v1.md`）
- 建立 DL580 自運行部署規格（`docs/MRL_DL580自運行部署規格_v1.md`）
- 建立 Acceptance Check（`scripts/MRL_acceptance_check.js`）
- 建立 Runtime Bootstrap（`scripts/MRL_runtime_bootstrap.js`）
- 建立 DL580 部署檢查（`scripts/MRL_dl580_deploy_check.sh`）
- 建立母體定義檔與世界模組工程書

### 待驗證

- DL580 真實部署
- Tailscale / SSH / self-hosted runner 接線
- Runtime 長駐與 systemd

### 不回填

- 外部平台主體命名
- chatbot 命名
- Vercel 依賴

### 下一步

- 建立 DL580 deploy runner

---

## v4 — RuntimeParticle Compression + StructureField 硬正名

分支：`MRL_Branch_RuntimeParticle_Compression_v4`

### 已完成

- **硬正名（無 alias、無備注殘留）**：移除 v2 階段保留的相容層
  - `RuntimeScopeGraph` alias 移除；canonical 只剩 `RuntimeStructureField`
  - facade `.graph` alias 屬性移除；只剩 `.structureField`
  - 內部參數 `scopeGraph`→`structureField`；checkpoint 欄位 `graph`→`structureField`
  - acceptance `L.graph`/`cp.graph`→ canonical；grep 確認零 `scopeGraph`/`RuntimeScopeGraph`/`.graph` 殘留
  - A–F acceptance PASS（`npm run MRL_pidscope_acceptance`）
- 交付物：
  - `MRL_Symbolic/MRL_粒子語言層/MRL_Particle_Runtime_Expansion_v4.fltnz`（canonical：structurefield / perception）
  - `docs/MRL_Claude_Engineering_Handoff_v1.md`（誠實 exists-vs-target）
  - `docs/MRL_Runtime_Recovery_Checklist_v1.md`（`[x]/[~]/[ ]` 誠實標記）

### 待驗證（回主線條件，未達成 → 不回填母體定義檔/世界模組工程書）

- Runtime loop persistence（durable）
- Replay exactness（跨 session）
- Restore chain（durable）
- DL580 host validation / reboot survival

### 不回填

- 情緒性語句、未驗證人格敘述
- canonical `MetaIR` / `Graph` / `Attention`（僅 alias / 降級陳述）
- 把 target 模組寫成已完成

### 下一步

- RuntimeStructureField execution loop
- Replay / Restore durable acceptance
- Persistent Runtime convergence
