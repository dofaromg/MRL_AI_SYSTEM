# ---- Force UTF-8 console (R13-C: PowerShell 5.1 ANSI/Big5 fix) ----
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 > $null 2>&1
} catch { }
# ------------------------------------------------------------------

# BOOTSTRAP.ps1 — DL580 單檔自解壓 + 一鍵部署
# origin_signature: MrLiouWord ｜ 2026-10-08 ｜ Additive-Only
#
# 功能：不管你當下 cwd 在哪，不管 ZIP 在哪，這個單檔會：
#   1) 自動找 MRL_WorldModel_Supplement_20261008_R01.zip（Downloads / Desktop / 腳本旁）
#   2) 解到 D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01
#      （若已存在，先備份為 .bak-<ts>，不覆蓋）
#   3) cd 進去，跑 wake.ps1
#
# 用法（三種任一）：
#   A) 把這個 BOOTSTRAP.ps1 跟 ZIP 放同一目錄，右鍵 → 使用 PowerShell 執行
#   B) powershell -ExecutionPolicy Bypass -File <path>\BOOTSTRAP.ps1
#   C) powershell -ExecutionPolicy Bypass -File <path>\BOOTSTRAP.ps1 -ZipPath <完整 zip 路徑>

[CmdletBinding()]
param(
  [string]$ZipPath = "",
  [string]$Dest = "D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01",
  [switch]$NoWake
)

$ErrorActionPreference = "Stop"
$ZIP_NAME = "MRL_WorldModel_Supplement_20261008_R01.zip"
$ORIG = "MrLiouWord"

Write-Host "===== MRL WorldModel Supplement R01 BOOTSTRAP =====" -ForegroundColor Cyan
Write-Host "origin_signature: $ORIG"
Write-Host "host: $env:COMPUTERNAME  user: $env:USERNAME"
Write-Host ""

# 1) 找 ZIP
if (-not $ZipPath) {
  $candidates = @(
    (Join-Path $PSScriptRoot $ZIP_NAME),
    (Join-Path (Split-Path -Parent $PSScriptRoot) $ZIP_NAME),
    (Join-Path "$env:USERPROFILE\Downloads" $ZIP_NAME),
    (Join-Path "$env:USERPROFILE\Desktop" $ZIP_NAME),
    (Join-Path "D:\" $ZIP_NAME),
    (Join-Path "D:\mrl" $ZIP_NAME)
  )
  foreach ($c in $candidates) {
    if (Test-Path $c) { $ZipPath = $c; break }
  }
}

if (-not $ZipPath -or -not (Test-Path $ZipPath)) {
  Write-Host "[FAIL] 找不到 $ZIP_NAME" -ForegroundColor Red
  Write-Host "       找過：" -ForegroundColor DarkGray
  foreach ($c in $candidates) { Write-Host "        - $c" -ForegroundColor DarkGray }
  Write-Host "`n解法：把 ZIP 路徑帶進來，例如："
  Write-Host "  powershell -ExecutionPolicy Bypass -File .\BOOTSTRAP.ps1 -ZipPath 'C:\完整\路徑\$ZIP_NAME'" -ForegroundColor Yellow
  exit 1
}

Write-Host "[1/3] 找到 ZIP: $ZipPath" -ForegroundColor Green
$zipSha = (Get-FileHash -Algorithm SHA256 $ZipPath).Hash
Write-Host "       SHA-256: $zipSha" -ForegroundColor DarkGray
Write-Host "       （SHA 僅顯示，不校驗；若啟動失敗再比對）" -ForegroundColor DarkGray

# 2) 解壓（Additive-Only：目標已存在就先備份）
$DestParent = Split-Path -Parent $Dest
if (-not (Test-Path $DestParent)) {
  New-Item -ItemType Directory -Path $DestParent -Force | Out-Null
}
if (Test-Path $Dest) {
  $bak = "${Dest}.bak-$(Get-Date -Format 'yyyyMMdd_HHmmss')"
  Write-Host "[2/3] 目標已存在，先備份：" -ForegroundColor Yellow
  Write-Host "       $Dest → $bak"
  Rename-Item -Path $Dest -NewName (Split-Path -Leaf $bak)
}

Write-Host "[2/3] 解壓到 $DestParent ..." -ForegroundColor Green
Expand-Archive -Path $ZipPath -DestinationPath $DestParent -Force

if (-not (Test-Path $Dest)) {
  # 處理 zip 內可能已含同名目錄的情況（Expand-Archive 會展成 $DestParent\<pack name>\）
  # 若 zip 內只有檔案（無頂層目錄），要手動包一層
  $looseFiles = Get-ChildItem -Path $DestParent -Depth 0 |
    Where-Object { $_.Name -eq (Split-Path -Leaf $Dest) }
  if (-not $looseFiles) {
    Write-Host "[FAIL] 解壓後找不到預期目錄 $Dest" -ForegroundColor Red
    exit 2
  }
}

$filesCount = (Get-ChildItem -Path $Dest -Recurse -File).Count
Write-Host "       解壓完成，共 $filesCount 檔" -ForegroundColor Green

# 3) 跑 wake.ps1
if ($NoWake) {
  Write-Host "`n[3/3] -NoWake 指定，略過 wake.ps1；已解壓到 $Dest" -ForegroundColor Yellow
  exit 0
}

Set-Location $Dest
$wake = Join-Path $Dest "06_deploy\wake.ps1"
if (-not (Test-Path $wake)) {
  Write-Host "[FAIL] 找不到 $wake" -ForegroundColor Red
  exit 3
}

Write-Host "`n[3/3] 跑 wake.ps1 ..." -ForegroundColor Green
Write-Host "────────────────────────────────────────────" -ForegroundColor DarkGray
& powershell -ExecutionPolicy Bypass -File $wake
Write-Host "────────────────────────────────────────────" -ForegroundColor DarkGray
Write-Host "`n完成。origin_signature: $ORIG" -ForegroundColor Cyan
