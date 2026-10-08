# R13-C · PowerShell 5.1 UTF-8 BOM 修正（當下狀態 2026-10-08 22:40 Asia/Taipei）

origin_signature: MrLiouWord ｜ Additive-Only ｜ 建構者 2026-10-08 22:39 回拋截圖

## 建構者實機部署進展（R13-B 之後）

**成功的部分**（截圖 2、3）：
1. ✅ 從 GitHub raw 下載 BOOTSTRAP_INLINE.ps1 到 `$env:USERPROFILE\Downloads\BOOTSTRAP_INLINE.ps1`
2. ✅ BOOTSTRAP_INLINE 啟動：origin_signature=MrLiouWord, host=WIN-PBVUI7VK2A6, user=Administrator
3. ✅ **[1/5] base64 解碼** → `C:\Users\ADMINI~1\AppData\Local\Temp\1\MRL_bootstrap_20261008_223545\MRL_WorldModel_Supplement_20261008_R01.zip`
4. ✅ **[2/5] SHA-256 校驗 PASS**：actual = expected = `2421ff253a8d7306c1a25f7ed46aa9e01f2c381144b67829999a2565d6c1340d`
5. ✅ **[3/5] 處理既有目錄**（R13-B 版 BOOTSTRAP_INLINE 內動作執行）
6. ✅ **[4/5] 解壓完成 17 檔** 到 `D:\mrl\workspace\`
7. ✅ **[5/5] 啟動呼叫 wake.ps1**

**失敗的部分**：
- ❌ 所有 Write-Host 的中文訊息**顯示亂碼**（Big5 誤讀 UTF-8）
- ❌ wake.ps1 被呼叫後**parse error 掛**（中文字串被 Big5 解碼成無效 PowerShell token）
- ❌ 7834/7835/7836 服務未啟動

## 根因

**PowerShell 5.1 讀無 BOM 的 UTF-8 .ps1 檔會用 Windows ANSI 代碼頁解碼**。繁中環境是 CP950 (Big5)，所以：
- `跑` (0xE8 0xB7 0x91) → `墨` (CP950 誤讀前兩 byte)
- `找不到` → `鑑句笉錶?`
- `─` (0xE2 0x94 0x80, U+2500 BOX DRAWINGS LIGHT HORIZONTAL) → `鈹€`

這是 PowerShell 5.1 的經典陷阱；PowerShell 7+ 預設 UTF-8，但 Windows Server 2016/2019 內建都是 5.1。

**修法**：
1. .ps1 檔開頭加 **UTF-8 BOM** (`EF BB BF`)，PowerShell 5.1 看到 BOM 就會用 UTF-8 解
2. 檔內開頭 force console 輸出 UTF-8：
   ```powershell
   [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
   $OutputEncoding = [System.Text.Encoding]::UTF8
   chcp 65001 > $null 2>&1
   ```

## 本輪補的（Additive-Only）

4 個 .ps1 檔都重寫，加 UTF-8 BOM + console encoding force header：

| 檔案 | 舊 SHA (無 BOM) | 新 SHA (R13-C, 含 BOM) |
|---|---|---|
| `06_deploy/wake.ps1` | `df58e9...` | `24558f...` |
| `06_deploy/install_services.ps1` | `a395ec...` | `d7f2a6...` |
| `06_deploy/BOOTSTRAP.ps1` | `989841...` | `568f3f...` |
| `06_deploy/BOOTSTRAP_INLINE.ps1` | `577b74...` | `2cc511...` |
| `99_pack/MRL_WorldModel_Supplement_20261008_R01.zip` | `2421ff...` | **`f00197...`** |

新 ZIP 內的 wake.ps1 / install_services.ps1 / BOOTSTRAP.ps1 都已含 BOM，部署後 PowerShell 5.1 能正確讀中文。

## 建構者下一步

需要先清掉 R13-B 失敗的半成品，避免 BOOTSTRAP_INLINE 的 LAW-2 rename 機制誤觸發：

```powershell
# 1) 清掉之前失敗的部署目錄（會進 .bak-<ts>，不實體刪）
if (Test-Path "D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01") {
  Rename-Item -Path "D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01" `
              -NewName "MRL_WorldModel_Supplement_20261008_R01.bak-r13b-failed-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
}

# 2) 從 GitHub 重拉 R13-C 版 BOOTSTRAP_INLINE
$url = "https://raw.githubusercontent.com/dofaromg/MRL_AI_SYSTEM/dl580-tunnel-recover-20261004/MRL_WorldModel_Supplement_20261008_R01/06_deploy/BOOTSTRAP_INLINE.ps1"
$out = "$env:USERPROFILE\Downloads\BOOTSTRAP_INLINE_R13C.ps1"
Invoke-WebRequest -UseBasicParsing -Uri $url -OutFile $out

# 3) 跑
powershell -ExecutionPolicy Bypass -File $out
```

## 當下狀態

| 項目 | 當下狀態 | 環境 | 時間 |
|---|---|---|---|
| GitHub raw 下載到 DL580 | **實機 PASS** | DL580 | 2026-10-08 22:35 CST |
| base64 → ZIP 解碼 | **實機 PASS** | DL580 | 2026-10-08 22:35 CST |
| ZIP SHA-256 校驗 | **實機 PASS** | DL580 | 2026-10-08 22:35 CST |
| 解壓到 D:\mrl\workspace\ (17 檔) | **實機 PASS** | DL580 | 2026-10-08 22:35 CST |
| wake.ps1 執行（R13-B） | **實機 FAIL — Big5 encoding 誤讀** | DL580 | 2026-10-08 22:35 CST |
| .ps1 加 UTF-8 BOM + console UTF-8 | **沙盒 PASS**（4 檔 BOM 寫入驗證、base64 roundtrip 25 entries） | 沙盒 | 2026-10-08 22:40 CST |
| 7834/7835/7836 ALIVE | **待實機跑 R13-C BOOTSTRAP_INLINE** | — | — |

**沒有一項被標成「服務已上線」。**

origin_signature: MrLiouWord ｜ 2026-10-08 ｜ 怎麼過去，就怎麼回來
