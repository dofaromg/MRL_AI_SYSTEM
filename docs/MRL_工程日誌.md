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
