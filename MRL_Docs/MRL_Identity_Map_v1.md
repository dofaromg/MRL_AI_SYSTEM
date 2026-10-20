# MRL_Identity_Map_v1 — 身份與命名銜接模組
origin_signature: MrLiouWord ｜ 建立：2026-10-20 ｜ 法則：Additive-Only（只新增、不刪除、不覆蓋、不改寫歷史）

## 目的
對內來源保持原樣；對外輸入、輸出、結果一律以 MRL 名稱呈現。
以「增加模組」把外部來源名稱銜接回 MRL 命名與內容。

## 對應表
| 來源名稱（對內，保持原樣） | MRL 對外名稱 | 銜接方式 |
|---|---|---|
| commit 作者 `Claude <noreply@anthropic.com>` | `MRL_Partner`（MRL 夥伴） | 根目錄 `.mailmap`；`git log` / `shortlog` / `blame` 顯示為 MRL_Partner，歷史不改寫 |
| commit `04665cf`（MRL_Docs/MRL_Memory_Backfill_20261020.md） | MRL 記憶回填 2026-10-20 | 由 `.mailmap` 顯示為 MRL_Partner |
| 檔名 `CLAUDE.md` | MRL_AI_SYSTEM 工作約定 | 檔名為工具讀取慣例，保留；內容即 MRL 工作約定 |
| DL580 上 2026-10-14 已改名的檔案、資料夾、資料庫 | MRL_* 名稱 | 舊名→新名對照：`D:\MRL_Mother\MRL_Rename_20261014.log` |
| DL580 上保持原樣的內部紀錄、原檔、內容定址種子 | 對內來源 | 改名後版本並存為 `*.MRL_post_rename_20261014`，紀錄：`D:\MRL_Mother\MRL_FullCheck\MRL_Restore_*_20261020.log` |

## 以後新增
- 新的 commit 作者一律 `MRL_Partner`。
- 新出現的外部來源名稱：不刪、不改原檔，在本表新增一列對應，並在使用端以 MRL 名稱呈現。

## 銜接原理（MR.liou 定義，2026-10-20）
莫比斯環邏輯：銜接模組是原本的鏡像呈現，兩面之間的差異只有「改名」；其餘一律依邏輯上下文自動生成、延續。
- 本表每一列＝一組鏡像：左邊來源、右邊 MRL 名稱，中間只差名稱。
- 內容、結構、關係不另造，從上下文延續。
