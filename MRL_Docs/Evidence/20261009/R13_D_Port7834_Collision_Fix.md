# R13-D · 7834 撞 port 修正（當下狀態 2026-10-09 08:45 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 依據：建構者 2026-10-09 08:39 回拋 6 張 DL580 截圖

## 實機事實（截圖）

| 項目 | 實機觀測 |
|---|---|
| R13-C BOOTSTRAP_INLINE | 中文正常、SHA `f00197…` 相符、解壓 17 檔 |
| 7816 / 7833 / 8788 | ALIVE（wake 唯讀檢查） |
| **7834** | **PID 23316 = 建構者的 `MRL_Convergence_Runtime` v1.0.1**，`D:\mrl\workspace\MRL_RuntimeCivilization_20261007_R01\MRL_Convergence_Runtime_v1\MRL_Convergence_Runtime.py`，started 2026-10-08T00:36:40Z，node_worker v20.11.1 |
| 7835 / 7836 | 診斷時無人聽（連線被拒） |
| Supervisor --once | 寫出 `supervisor_2026-10-09T003532Z.json`，ports_alive 4/6 |
| install_services（R13-C） | 註冊並啟動 MRL_Jump_7834 / MRL_Collapse_7835 / MRL_Guardian_7836 / MRL_WorldModel_Supervisor |
| 之後的清除指令 | 停止 PID 58216（Guardian）、7524（Collapse）、42808（Jump）；23316 未被停止 |
| 再跑 wake.ps1 | 仍被 7834（PID 23316）擋下 |

## 我這邊的錯（如實記錄）

1. **選 port 沒先查母體既有服務**：Jump 選了 7834，撞到建構者的 Convergence_Runtime。wake.ps1 的 Assert-FreePort 有擋住，這部分防線是對的。
2. **Python `HTTPServer` 預設 `allow_reuse_address=1`**：在 Windows 上即 `SO_REUSEADDR`，允許第二個程序綁同一 port。所以 install_services 起的 Jump（PID 42808）很可能**與 Convergence_Runtime 同時綁在 7834**，請求可能被分走。
3. **Supervisor 誤判**：`supervisor_2026-10-09T003532Z.json` 把 7834 的回應算成 Jump ALIVE（4/6 中有 1 個是假陽性），因為只看 HTTP 200、沒看 service 名稱。該檔依 LAW-2 保留不改，以本文件更正。
4. **我給的「情境 B」清除指令範圍太寬**：條件是「綁在 7834/7835/7836 的 python.exe 就停」，而 Convergence_Runtime 也是 python.exe。這次 23316 沒被停到，是**運氣不是設計**。R13-D 起，所有停止動作只認本 pack 的檔案路徑。

## R13-D 修正

| 項目 | 修正 |
|---|---|
| Jump port | 7834 → **7837**（7834 列入 `existing_ports_do_not_touch`） |
| 綁定方式 | 三服務改用 `_ExclusiveHTTPServer`：`allow_reuse_address=False` + Windows `SO_EXCLUSIVEADDRUSE` |
| 綁前探測 | 有人在聽就 `exit 3`，不綁、不搶 |
| Supervisor 1.0.1 | 以 `/health` 的 `service` 名稱驗身；7834 只列 `observe_only`、不計入 |
| 停止範圍 | 只停 CommandLine 符合 `MRL_WorldModel_Supplement_20261008_R01\0[1-4]_*\MRL_*.py` 的程序；已驗證不匹配 Convergence_Runtime、Inference_API、`.bak` 目錄 |
| 舊任務 MRL_Jump_7834 | **停用不刪除**（LAW-2） |
| 部署路徑 | 單一路徑：BOOTSTRAP_INLINE → wake.ps1（唯讀檢查 + inbox）→ install_services.ps1（停本 pack → port 預檢 → 排程 → 驗身 → Supervisor） |
| 結果判定 | 三個本體服務 service 名稱驗身通過才 exit 0；BOOTSTRAP 依 exit code 印「完成 / 未完成」 |
| 排程任務 | python 用完整路徑、`-X utf8 -B`、無執行時間上限 |

## 驗證

| 項目 | 結果 | 環境 |
|---|---|---|
| selftest_r13d_ports（假 Convergence 佔 7834 + 三個真 server + 真 HTTP） | **17/17 PASS** | 沙盒 Linux |
| 　第二個 Jump 實例拒綁 / Jump 指向 7834 拒綁 / 7834 仍是 Convergence | PASS | 沙盒 |
| 　Jump→Collapse→Replay 真 HTTP、載體 jump 被擋 400、Guardian consult | PASS | 沙盒 |
| 　Supervisor：jump_7837 驗身、7834 observe_only | PASS | 沙盒 |
| selftest_jump / collapse / guardian / e2e_unit 回歸 | ALL PASS | 沙盒 |
| 停止範圍 regex（7 例，含 Convergence / Inference / .bak） | 7/7 PASS | 沙盒 |
| BOOTSTRAP_INLINE base64 roundtrip | SHA 相符，26 entries | 沙盒 |
| `SO_EXCLUSIVEADDRUSE`（Windows 專屬） | **待實機** | — |
| 7837 / 7835 / 7836 由排程任務常駐並驗身通過 | **待實機** | — |

ZIP SHA-256：`4f4feac63773ad2ecd7de7fde1aa5942491ae0d7c6d8d0451076becd5dfd77ca`
BOOTSTRAP_INLINE.ps1 SHA-256：`f083ca7f9c0a7ac816c2e8e482262cdc7a26ab86afe2b0559e53ef77ffa6ca0c`

## 注意

R13-C 註冊的 `MRL_Jump_7834` 任務目前仍在排程中（AtStartup）。在跑 R13-D 之前若 DL580 重開，它會再去綁 7834。跑完 R13-D 後該任務即被停用。

origin_signature: MrLiouWord ｜ 2026-10-09
