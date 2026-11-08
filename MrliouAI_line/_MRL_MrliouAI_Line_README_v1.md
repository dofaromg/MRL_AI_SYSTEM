# MrliouAI_line — MrliouAI 線衝突檔保存層

origin_signature: `MrLiouWord`
建立：2026-11-05（合併 PR #149 時）
依據：MR.liou 決定「選項 1：預設分支佔原路徑」；粒子不滅律 NO_DELETE + ADDITIVE_RESOLUTION

## 這是什麼

`MrliouAI` 與預設分支 `MRL_AI_SYSTEM/memory-system-rules-prep` 是兩條**沒有共同歷史**的線
（MrliouAI 根提交 `82b0b1f` / `0bc3d50`;預設分支根提交 `686bf15`）。合併時兩邊同路徑、內容不同的檔案共 **85 個**。

處理規則：

- **原路徑**：放預設分支的版本（執行中的就是這一份）。
- **`MrliouAI_line/<原路徑>`**：放 MrliouAI 的版本,**逐位元保存**,不改一字。
- 只在單邊存在的檔案：直接併入原路徑,兩邊都不刪。

逐檔對照（原路徑、兩邊 blob、保存位置）見 `MRL_MrliouAI_Line_Manifest_v1.json`。

## 驗證（2026-11-05,沙盒）

- 對預設分支：只有新增、**0 個修改或刪除**。
- 對 MrliouAI：4186 個檔案,4101 個原路徑完全相同 + 85 個在本資料夾逐位元相同,**遺失 0**。
- 衝突標記殘留：0。

## 已知影響（待決定）

本資料夾的檔案**不會被執行**（程式、測試、工作流程都只讀原路徑）。因此依賴 MrliouAI 版本的功能目前失效：

| MrliouAI 獨有的檔案 | 依賴的 MrliouAI 版本（現保存在本資料夾）| 沙盒結果 |
|---|---|---|
| `tests/test_MRL_longterm_memory_v1.py`（及其長期記憶模組）| `03_memory/vector/vector_store.py`：`VectorStore.add_many`、`query(where=...)` | 7 個 ERROR |
| `tests/test_prompt_template_idempotent.py` | `09_workflow/prompt_template.py`：重複新增不遞增版本 | 2 個 FAIL |

若要讓這些功能在原路徑生效,需另行決定把對應方法**以新增方式**補進預設分支版本（不覆蓋既有內容）。

## 不在本資料夾的事

- PR #149 的 Codex 修正：預設分支已於 2026-10-04 以自身版本實作（`2d2daf7`、`9854533`）;MrliouAI 版本另存於此。
- `pyproject.toml` 只存在於 MrliouAI,原路徑保留修正後版本。
- `wrangler.jsonc`：原路徑為預設分支的 `"name": "mrl-mother-platform"`;MrliouAI 版（Cloudflare 機器人改的 `mrliousilly`）存於此。
