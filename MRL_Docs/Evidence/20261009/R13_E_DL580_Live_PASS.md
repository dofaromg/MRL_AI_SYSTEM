# R13-E · DL580 實機部署驗身通過（當下狀態 2026-10-09 09:31 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 依據：建構者 2026-10-09 09:31 回拋 DL580 截圖（WIN-PBVUI7VK2A6）

## 實機輸出（install_services.ps1，由 BOOTSTRAP_INLINE R13-E 呼叫）

- python：`D:\MrlToolchain\python\python.exe`
- [1/5] 停止本 pack 任務 MRL_Jump_7834 / MRL_Collapse_7835 / MRL_Guardian_7836 / MRL_WorldModel_Supervisor；**停用（不刪除）舊任務 MRL_Jump_7834**
- [2/5] port 預檢：7837 / 7835 / 7836 皆空閒
- [3/5] 註冊並啟動：MRL_Jump_7837、MRL_Collapse_7835、MRL_Guardian_7836、MRL_WorldModel_Supervisor
- [4/5] 驗身（service 名稱比對）：
  - MRL_Jump_Service :7837 ALIVE v1.0.1
  - MRL_Collapse_Service :7835 ALIVE v1.0.1
  - MRL_AnalystGuardian_Agent :7836 ALIVE v1.0.1
- [5/5] Supervisor --once：ports_alive 6/6、all_green true、anomalies 0
  → `D:\MRL_Mother\WorldModel_Readiness_20261008\supervisor\supervisor_2026-10-09T013113Z.json`
- 結尾：「BOOTSTRAP 完成，三個本體服務驗身通過」

## 當下狀態

| 項目 | 狀態 | 環境 |
|---|---|---|
| Jump 7837 / Collapse 7835 / Guardian 7836 由 SYSTEM 排程任務常駐、service 名稱驗身 | **PASS** | **實機** 2026-10-09 09:31 |
| Supervisor 6/6、anomalies 0 | **PASS** | **實機** |
| 舊任務 MRL_Jump_7834 停用不刪 | **PASS** | **實機** |
| 7834 MRL_Convergence_Runtime 未受影響 | 截圖中未直接列出；Supervisor 僅 observe_only，未計入 6/6 | 待下一次輸出確認 |
| Jump→Collapse→Replay 實機走一輪 | **待實機** | — |
| Guardian 對建構者語料（分析師守護者）實機命中 | **待實機** | — |
| 重開機後排程自動起來 | **待實機** | — |

說明：Supervisor 的 6/6 中，7816 / 7833 / 8788 為 HTTP 200 判定（未做 service 名稱比對）；7837 / 7835 / 7836 為 service 名稱驗身。

## 版本

- git：`12119bb`（R13-E）於 `dl580-tunnel-recover-20261004`
- ZIP `4f4feac63773ad2ecd7de7fde1aa5942491ae0d7c6d8d0451076becd5dfd77ca`
- BOOTSTRAP_INLINE.ps1 `cf1892be62d20f852209c584bea79967eae40258fdb15da62472e8d8fe9a5c25`

origin_signature: MrLiouWord ｜ 2026-10-09
