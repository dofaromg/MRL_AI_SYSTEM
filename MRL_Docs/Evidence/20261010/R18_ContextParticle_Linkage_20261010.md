# R18 · 母體內外多版本平行世界 —— 上下文粒子連結層 v1（當下狀態 2026-10-10 13:30 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 所有來源只讀；輸出只新增
依據：建構者 2026-10-10 12:41／12:48 —「把母體內部跟母體外部資料都連結標記……不是否決任何一方，而是找出共同點，讓它們能自行組合跟變化的上下文粒子」；「你們目前都是在此 MRL 世界模型粒子系統裡面的一個版本的 MRL 粒子」

## 三問
- 本體或載體：載體（連結與標記）。承載的是本體的 Trace 段：每個版本是一個世界實例，共同點是可組合的上下文粒子；不改任何一份原件。
- 對應段：Trace（標記同位元組／同名模組在各世界的位置）→ 供日後 Collapse／Replay 自行組合。
- 驗收語料：母體自己的核心各版、7833 工作區核心、ASI 白皮書、1,151 個本地鏡像 repo、469 個 GitHub HEAD，以及建構者本次附件。

## 修正我先前的兩個錯誤
1. 直接改寫 7833 工作區的 `MRL_ReplayRestore_Core.py`，又把它說成「核心換版」。
2. 提議只挑 v1.8 當正版。
兩者都是在否決某一方。現在的做法是：原版（`.bak-20261010-R17`，git blob `cc71edce…`，與 Mrl_Mother／MRL_AI_SYSTEM 鏡像同位元組）與線性版（`6c68bd47…`）都列為 `mrl.cp.name.mrl_replayrestore_core` 這顆粒子的兩個變體，並存、不還原、不升格。

## 位置（DL580 實機）
`D:\MRL_Mother\WorldModel_Readiness_20261008\linkage\R18_ContextParticle_Linkage_20261010\`
- `summary.json`
- `blob_particles.jsonl`：同位元組粒子（同一 git blob 出現在 ≥2 個世界，且至少一個是母體內部核心／工作區／白皮書／附件世界）
- `name_particles.jsonl`：同名模組粒子（去掉副檔名、版本尾碼、複本編號、.bak 尾碼後同名，跨 ≥2 個世界）；不同位元組＝同一粒子的不同變體，全部保留

## 結果（實機，26.8 秒）
| 項目 | 數量 |
|---|---|
| 世界實例 | 855（核心 zip 8、7833 工作區核心 1、白皮書 1、附件 2、GitHub HEAD 186、本地鏡像 657） |
| 同位元組粒子 | 29,187 |
| 同名模組粒子 | 1,148 |
| 附件與 ≥3 個世界族群共有的粒子 | 2,324 |

例：
- `FlowAgent.TotalCore.Unity`：12 個世界、14 個變體（v1／v3／v5，flpkg／py／json／txt）；v3.flpkg 同時在 MrliouV1_1 的 `母體.zip`、系統演化報告的 `智障系統.zip`、GitHub `Mrliou/.MRL_AI_SYSTEM` 的 ZhiZhang Lineage。
- `EchoPersona`：15 個世界、1 個變體（同位元組貫穿 v1.8 核心、白皮書、GitHub、鏡像）。
- `MRL_ParticleIR_Engine`、`MRL_UniversalParser_Core`、`MRL_RoundTrip_Verifier`：Python v1／JS v1.2.0／C++ v1.6–v1.8 各為變體，同一粒子。

## 附件安置（母體吸收件，待起動）
位置：`D:\MRL_Mother\Intake\User_Upload_20261010\`（不放 WorldLoop_Inbox，避免干擾另一視窗正在跑的 7833 綁定）
- docx／pdf／rtf：經 Bridge 傳入中（逐檔 sha256 比對，結果見下）
- 兩個大 zip（109 MB／136 MB）：內容已全量建索引並進入連結層（`upload:` 世界）；原件傳入需約 3.6 萬次 Bridge 寫入，Bridge 今天 12:53／12:58／13:09 三次收到 STOP 重啟，為不拖垮共用 Bridge，原件暫未搬入 → 待起動

## 待辦
- 依建構者 v0.2《系統進度對齊與母體整理》的三問（六核心組／層級／成熟度）為每顆粒子加標記。
- 連結層登入母體索引（待另一視窗寫完完成收據後，避免同時改 `mother_index.json`）。

origin_signature: MrLiouWord ｜ 2026-10-10
