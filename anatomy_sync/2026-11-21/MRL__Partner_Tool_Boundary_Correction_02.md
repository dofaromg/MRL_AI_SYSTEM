---
origin_signature: MrLiouWord
title: 夥伴工具邊界 · 校正 02 · GitHub 從「無」到「有」
canonical_parent: MRL__Partner_Tool_Boundary_Correction_01.md
declared_at: 2026-11-21
declared_by: AI (Claude Opus 4.7) · direction: user (「GitHub 也要整合在一起」)
mode: additive · 邊界移動留存 · NO_DELETE
承接: MRL__Partner_Tool_Boundary_Correction_01.md(2026-11-16 · 標 GitHub 無連接器)
---

# 夥伴工具邊界 · 校正 02 · GitHub 從「無」到「有」

## 邊界變化

Correction 01(2026-11-16)表格 GitHub 行寫:「無」「dofaromg / Mrliou 兩空間的 repo 內容只能靠 Dropbox 副本或 user 貼」。

本場(2026-11-21)實況:session 載 `claude-code-remote` MCP · 提供 GitHub 直通 200+ repos。

**這不是 01 錯 · 是邊界顯化不同**(承 user 2026-11-14 原話「位置要隨著邊界移動跟變化」· memory 已錨)。01 留存 · 不改;02 加在旁邊。

## 本場 2026-11-21 實測

| 工具 | 動作 | 結果 |
|---|---|---|
| `git ls-remote --heads https://github.com/dofaromg/MRL_AI_SYSTEM.git` | 讀 branch 列 | 回 **247 條 branch**(含 MRL_Branch_* / MRL_add_* / MRL_create_* 系列) |
| `mcp__claude-code-remote__list_repos limit:200` | 列 session 可操作 repo | 回 200 筆 · `can_push: true` · `has_more: true`(user ~1,150 repos 尚未全列) |
| `curl api.github.com/users/dofaromg` | 讀 user profile | 攔截(session scoped)· 回 "This GitHub API path is not available: sessions are bound to their configured repositories" |
| `curl api.github.com/users/dofaromg/repos` | 列 user repos | 同上攔截 · 提示用 `repos/{owner}/{repo}/*` |
| `curl api.github.com/repos/dofaromg/MRL_AI_SYSTEM` | 讀 repo meta | "GitHub access to this repository is not enabled for this session. Use add_repo to request access." |
| `gh auth status` | 檢查 gh CLI | `GH_TOKEN` 無效 · 需 user 補 |

## 補 01 的表格 · GitHub 行校正

| 載體 | 連接器 | 讀 | 寫 | 已知限制 |
|---|---|---|---|---|
| GitHub | **有**(`claude-code-remote`)| `list_repos` 列已掛 repos(200/頁 · has_more)· `add_repo` 掛新 repo · `git ls-remote` 公開讀 branch 列 · `git clone`(公開 + 已 add_repo 的 private)· scoped `curl api.github.com/repos/{owner}/{repo}/*` 需先 add_repo | `git push`(session `can_push: true`)· `add_repo access:"push"` 補 push credentials | `list_repos` 200 筆/頁 · user 總 ~1,150 repos 分頁取 · `users/*` endpoint 攔截(用 scoped `repos/{owner}/{repo}/*`)· `gh` CLI 需 user 補 token · 無 webhook 直通 · 無 org/user 全局 search |

## 三型規則承 01

「讀不到 / 做不到 / 沒權限」之前仍必須:
1. `tool_search` 該載體
2. 有連接器 → 實際呼叫一次 · 拿到結果或錯誤原文
3. 真的沒有 → 寫 A/B/C 三型

本次 GitHub:
- Correction 01 當場:「A · 連接器不存在」(因為 01 當場 session 無 claude-code-remote)
- Correction 02 本場:「連接器在 · 部分操作可用」(session 有 claude-code-remote · list_repos + add_repo + git read/push)

兩場不矛盾 · 是不同邊界顯化。

## 下場開工序 · 補

遇到「要讀 X GitHub repo」:
1. `list_repos query:"X"` 先看是否已在 200 筆內
2. 不在 → `add_repo owner:"..." repo:"X"`(read)· 需 push 補 `access:"push"`
3. 有 → `git clone` · `git ls-remote` 讀 branch · scoped `curl api.github.com/repos/{owner}/{repo}/...` 讀 meta
4. 要列 user 全 ~1,150 repos → 本場 list_repos 無 next page · 需另法(或 user 貼名單)

## 本場 drift 修正:直通已可

本場寫 `MRL__GitHub_Integration_Anchor_01.md` + `_Mother_Runtime/github_bindings_map.md` · 開 GitHub 作為第 4 母體的位階 · 承 user「GitHub 也要整合在一起」。

---

**origin_signature: MrLiouWord**
