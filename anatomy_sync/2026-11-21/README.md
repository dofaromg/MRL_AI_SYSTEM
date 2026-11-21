# anatomy_sync / 2026-11-21 · Dropbox Integration Round

## 用途

把 Dropbox 雲母體 `/MRL_Mother_Anatomy/` 本輪(2026-11-21)新封存的 11 檔 · 以 **衍生副本** 形式推進 `dofaromg/MRL_AI_SYSTEM` 這個 GitHub 母體,作為第 4 母體整合的第一批實體落點。

承接:
- `MRL_Mother_Anatomy/MRL__GitHub_Integration_Anchor_01.md`(2026-11-21 · 定位 GitHub 為第 4 母體)
- `MRL_Mother_Anatomy/_Mother_Runtime/github_bindings_map.md`(通路 2 · Dropbox → GitHub)
- CLAUDE.md 的 **Additive-Only** 母體整合法則(只新增、不刪改)

## 本輪 11 檔清單(本資料夾下)

### 根層(5 檔 · 承補完 01-03 的補完線 + Boundary Correction 02 + GitHub Integration Anchor)

1. `MRL_20261115_Claude誤建檔標記_補完_02.md` — 15 檔誤建標記逐檔展開
2. `MRL_20261115_Claude誤建檔標記_補完_03_Modules_範圍檢查.md` — Mother_Core / LoopLab / Blood_Ledger 深讀結論:全部正規封存 · 無新誤建
3. `MRL_20261121_Mother_原件補傳錨_C.md` — 2,925 行原件補傳待辦錨
4. `MRL__Partner_Tool_Boundary_Correction_02.md` — 工具邊界 02:GitHub 從「無」→「有」
5. `MRL__GitHub_Integration_Anchor_01.md` — GitHub 位階定位 + 核心 MRL repos 清單 + 4 條接線點

### `_Mother_Runtime/`(6 檔 · gap_analysis 下一輪 5 項 + github_bindings_map)

6. `_Mother_Runtime/mother_control_panel_v2.html` — v1 補完 · 加 kernel /run 詳細 + DL580 五端口 + 流程圖 trace(**scrubbed**)
7. `_Mother_Runtime/wrangler_deploy.sh` — 關鍵 10 支 worker 部署驗證(**scrubbed**)
8. `_Mother_Runtime/health_dashboard.html` — real-time polling dashboard
9. `_Mother_Runtime/system_map_patch_01.md` — system-hub SYSTEM_MAP 補 10 筆新粒子(**scrubbed**)
10. `_Mother_Runtime/mother_bootstrap.md` — 從零到母體能動的步驟清單(**scrubbed**)
11. `_Mother_Runtime/github_bindings_map.md` — GitHub 4 條對流通路

## Scrub 說明(衍生副本的安全處理)

Dropbox 原檔保留 inline 的 BRIDGE_KEY secret 值(user 既有運行層 2026-11-14 bindings_map 的 verbatim 延續 · user 自己可見 Dropbox)。

**本倉為 public repo(`dofaromg/MRL_AI_SYSTEM` visibility: public)· GitHub 衍生副本把該 secret 字串替換為:**
- `${BRIDGE_KEY}`(shell 變數格式 · 需 env 提供)
- `<REDACTED_SEE_LOCAL_CONFIG>`(HTML / markdown 文字中)

**scrub 僅影響此 `anatomy_sync/` 下的衍生副本 · 不改 Dropbox 原檔**。user 要改 Dropbox 原檔需另做決定。

## Attribution

- **容器 owner**: user(劉宥麟)
- **direction author**: user(2026-11-21「GitHub 也要整合在一起」)
- **content author**: AI(Claude Opus 4.7)
- **commit author**: Claude (via claude-code-remote) `noreply@anthropic.com`
- **origin_signature**: MrLiouWord

## 戒律對位

| 戒律 | 本輪遵守方式 |
|---|---|
| Additive-Only(CLAUDE.md) | 只建新目錄 · 不碰既有 00_rootlaw~09_workflow + MRL_* |
| 不刪不覆蓋 | 既有 .github/workflows/ 9 支 workflow 全保 · 不加新 deploy-workers.yml |
| 不擅自壓縮 | 衍生副本保原內容 · 只 scrub secrets · 不改語意 |
| 不替 user 立 label | 各檔檔頭 attribution 從原檔抽 |
| L1 位階保護 | GitHub 定為 L2 載體 · MRL 本體仍在 L1 |
| 位置隨邊界移動 | Correction 02 明寫 GitHub 從「無」→「有」是邊界顯化 · 非 01 錯 |

## 下一輪候選(本輪未做)

- 本資料夾未加新 `.github/workflows/deploy-workers.yml`(避免與既有 9 支 workflow 衝突 · 待 user 決定是否要)
- CF Worker `mrl-github-to-dropbox-sync`(通路 1-A)未建
- DL580 `github_mirror.ps1`(通路 1-B)未裝
- Mrliou/Mrl_Mother private 未掛 add_repo

---

**origin_signature: MrLiouWord**
