---
name: github-bindings-map
description: GitHub(第 4 母體)接進三母體對流的 bindings 配置圖
sources: [cowork, user]
layer: L2-Runtime-Config
origin_signature: MrLiouWord
archive_date: 2026-11-21
---

# GitHub 接線圖

**承**: bindings_map.md(2026-11-14 · CF 側)+ Boundary Correction 02 + GitHub Integration Anchor 01
**direction author**: user (「GitHub 也要整合在一起」)
**content author**: AI (Claude Opus 4.7)
**目的**: 把 GitHub 平行世界空間(dofaromg + Mrliou · ~1,150 repos)接進三母體對流 · 成為第 4 母體

---

## 一、GitHub 的 4 條對流通路

### 通路 1 · GitHub → Dropbox(封存對流)

**方向**:GitHub 新 commit → Dropbox 鏡像封存
**目的**:Dropbox 雲母體永遠有 GitHub 當前狀態的副本

**實作選項**:

**A. CF Worker `mrl-github-to-dropbox-sync`**(新建 · 本場未建)
- Trigger:GitHub webhook(push event)
- Action:拉 commit diff → Dropbox API `upload` 到 `/MRL_Mother_Anatomy/Modules/{repo}/`
- 需 secrets:
  - `GITHUB_WEBHOOK_SECRET`(驗 webhook 簽)
  - `DROPBOX_ACCESS_TOKEN`(user 的 Dropbox OAuth)
- 綁到:全部 `dofaromg/*` 跟 `Mrliou/*` 關鍵 repos 的 webhook

**B. DL580 定時 cron**(本地 pull)
```powershell
# D:\mrl\scripts\github_mirror.ps1
cd D:\mrl\github_mirror
foreach ($repo in @('dofaromg/MRL_AI_SYSTEM', 'dofaromg/mrliouword-root', 'dofaromg/APFS', 'Mrliou/Mrl_Mother')) {
  $local = $repo -replace '/', '_'
  if (Test-Path $local) {
    cd $local; git fetch --all; cd ..
  } else {
    git clone --mirror "https://github.com/$repo.git" $local
  }
}
# rclone 或 Dropbox desktop sync 自動帶回 Dropbox
rclone copy D:\mrl\github_mirror\ dropbox:/MRL_Mother_Anatomy/GitHub_Mirror/ --update
```
排程:每 15 分鐘(Task Scheduler)

### 通路 2 · Dropbox → GitHub(本體往 GitHub 推)

**方向**:Dropbox 新封存檔 → GitHub branch

**本場實況**:session `can_push: true` · Claude 可直接推。本輪(2026-11-21)實際執行本通路 · push 11 檔到 `MRL_Branch_Dropbox_20261121_Integration_Round_v1`。

**推動作**(session 已跑):
```bash
# session 已有 GitHub credentials (can_push: true via claude-code-remote)
git clone https://github.com/dofaromg/mrl_ai_system
cd mrl_ai_system
git checkout -b MRL_Branch_Dropbox_20261121_Integration_Round_v1
mkdir -p anatomy_sync/2026-11-21
# 從 Dropbox 下載本輪補完檔(scrub 秘鑰)· 複製進 anatomy_sync/2026-11-21/
git add anatomy_sync/
git commit -m "anatomy_sync 2026-11-21: Dropbox → GitHub 第一批整合 (A·B·C + 補完 03 + GitHub 整合 3 檔)"
git push -u origin MRL_Branch_Dropbox_20261121_Integration_Round_v1
gh pr create --title "..." --body "..."
```

### 通路 3 · GitHub → Cloudflare(CI/CD)

**方向**:GitHub push → CF Workers 自動部署

**實作**:**本場未建新 workflow** · 原因:`MRL_AI_SYSTEM/.github/workflows/` 已有 9 支 workflow(`MRL_DL580_selfhosted_deploy.yml` · `MRL_GitHub_Mirror.yml` · `MRL_WorldModel_Identity_Wake_Core.yml` · `MRL_recovery_operations.yml` 等)· 承 CLAUDE.md **Additive-Only**。

若 user 要加 CF Workers 部署 · 建議:
- 開新 branch 寫 `.github/workflows/mrl_cf_workers_deploy.yml`(命名承本倉既有 `MRL_*.yml` 模式)
- 不改 `deploy.yml`(既有通用部署)
- 需 Repository secrets:`CF_API_TOKEN` · `CF_ACCOUNT_ID`

### 通路 4 · GitHub → DL580(本機拉)

**方向**:GitHub 任何倉 → DL580 本地

**實作**:
- DL580 Bridge(port 7800)加 `/github/pull/{owner}/{repo}` endpoint
- Endpoint 內 shell out 跑 `git pull` 到 `D:\mrl\github\{owner}_{repo}\`
- Trigger:
  - mother_control_panel v2 戳按鈕
  - 或 cron 定時

---

## 二、核心 repos 的 binding alias 建議

對照 bindings_map.md Service Binding 格式:

| repo | binding alias | 用途 |
|---|---|---|
| `dofaromg/MRL_AI_SYSTEM` | `GITHUB_MAIN` | 主倉 · 247 branches · 本輪 push 位置 |
| `dofaromg/mrliouword-root` | `GITHUB_WORKERS_SOURCE` | CF workers code 來源 |
| `dofaromg/MRL_ASI_system` | `GITHUB_ASI` | ASI 系統 |
| `dofaromg/MRL_mcp-server-cloudflare` | `GITHUB_MCP_CF` | MCP + CF 整合 |
| `dofaromg/mrlioudb` | `GITHUB_DB` | DB schemas |
| `dofaromg/APFS` | `GITHUB_APFS` | user memory 錨:external Adapter / deployment |
| `dofaromg/Mrliouhan` | `GITHUB_MRLIOUHAN` | App_Mrliouhan_Build 對應(見補完 02 C 類) |
| `Mrliou/Mrl_Mother` | `GITHUB_MOTHER_PRIVATE` | Mother 線 private |
| `Mrliou/MRL-Autonomous-Evolution-Stack-AES-` | `GITHUB_AES` | AES |

---

## 三、本場未建 · 列補完 04 候選

- [ ] CF Worker `mrl-github-to-dropbox-sync`(通路 1-A)· 實作 + 部署
- [ ] DL580 PS1 腳本 `github_mirror.ps1`(通路 1-B)· user 本機裝
- [ ] `.github/workflows/mrl_cf_workers_deploy.yml`(通路 3 · 命名承既有 MRL_* 模式)· push 到 `MRL_AI_SYSTEM`
- [ ] DL580 Bridge `/github/pull/*` endpoint(通路 4)· user 本機裝
- [x] 本輪 11 補完檔推到 `MRL_Branch_Dropbox_20261121_Integration_Round_v1`(通路 2 · **本場完成**)

---

## 四、對 control_panel v2 / health_dashboard 的補丁建議

本場 `_Mother_Runtime/mother_control_panel_v2.html` 跟 `health_dashboard.html` 的粒子清單應加入 GitHub 載體(一個新層 "L2-GitHub"):

```javascript
// PARTICLES 字典新增一層
'L2-GitHub 母體': ['mrl-github-to-dropbox-sync', 'github-webhook-receiver']
```

這兩支是通路 1-A / 通路 3 的 CF Worker · 建完才會 alive。本檔不改 v2 檔(append-only)· 由補完 04 時建 v3 / patch。

---

## 五、對 bootstrap 的補

`mother_bootstrap.md`(2026-11-21 寫)的「階段 1-4」當前只到 Cloudflare / DL580 / Dropbox 三母體。本檔承接 · 加:

### 階段 5 · GitHub 整合(本場 2026-11-21 新階段)

| 步驟 | 動作 | 驗證 |
|---|---|---|
| 5.1 | session 用 `list_repos` 確認 200 repos access(session 載 claude-code-remote 時即自動)| `can_push: true` |
| 5.2 | 本輪 11 檔 push 到 `MRL_AI_SYSTEM` new branch(**本場完成**)| `git log --oneline MRL_Branch_Dropbox_20261121_*` |
| 5.3 | 寫 `.github/workflows/mrl_cf_workers_deploy.yml` | `gh workflow list` |
| 5.4 | 設 CF_API_TOKEN / CF_ACCOUNT_ID Repository secrets | `gh secret list` |
| 5.5 | 建 `mrl-github-to-dropbox-sync` worker + webhook | push 試 · 看 Dropbox 是否有新檔 |
| 5.6 | DL580 裝 `github_mirror.ps1` cron | run_result 檔確認 |

bootstrap v2(補完 04 候選)會把階段 5 併進去。本檔先列。

---

## 六、戒律驗證

- origin_signature: MrLiouWord ✓
- 不 overlap L1(GitHub 是 L2 載體 · 不碰 L1 模具層)✓
- 承「三個以上母體」✓(GitHub 加入為第 4)
- append-only ✓(本檔新建 · 不改 bindings_map.md / mother_bootstrap.md)
- 位置隨邊界移動 ✓(承 Correction 02 · GitHub 從「無」到「有」)
- 不壓縮 user 空間 ✓(1,150 repos 全保 · 本檔只列核心接線 · 其他 forks 不碰)
- 不刪戒律 ✓(_RUNTIME/ 錯資料夾不碰 · 繼續用 `_Mother_Runtime/`)
- 可運行指引 ✓(每通路列實際命令 + secrets)

---

**封存**: Claude 執行 · 方向來自 user(「GitHub 也要整合在一起」+「繼續」)
**origin_signature**: MrLiouWord
