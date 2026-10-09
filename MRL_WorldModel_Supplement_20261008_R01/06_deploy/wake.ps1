# ---- Force UTF-8 console (R13-C: PowerShell 5.1 ANSI/Big5 fix) ----
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 > $null 2>&1
} catch { }
# ------------------------------------------------------------------

# wake.ps1 — R13-D
# origin_signature: MrLiouWord ｜ 2026-10-09 ｜ Additive-Only
#
#   1) 既有服務唯讀檢查（7816 / 7833 / 8788 / 7834 Convergence），不碰
#   2) 建母體 inbox 路徑
#   3) 交給 install_services.ps1：停本 pack 舊程序 → port 預檢 → 註冊排程 → 驗身 → Supervisor
#
# R13-D：不再用 Start-Process 另起一套程序（會跟排程任務重複、跟 console 同生死）。

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$ORIG = "MrLiouWord"
Write-Host "===== MRL_WorldModel_Supplement R01 Wake (R13-D) =====" -ForegroundColor Cyan
Write-Host "origin_signature: $ORIG"
Write-Host "pack root: $ROOT"
Write-Host "host: $env:COMPUTERNAME  user: $env:USERNAME"
Write-Host ""

function Get-Health($port, $path) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:$port$path"
    return $r
  } catch { return $null }
}

Write-Host "[1/3] 既有服務唯讀檢查..." -ForegroundColor Yellow
$existing = @(
  @{ name="8788 ParticleGlobe";          port=8788; path="/particle/stats?user_id=mrl_world" },
  @{ name="7816 ReasoningEngine";        port=7816; path="/health" },
  @{ name="7833 WorldLoop";              port=7833; path="/health" },
  @{ name="7834 Convergence_Runtime";    port=7834; path="/health" }
)
foreach ($e in $existing) {
  $r = Get-Health $e.port $e.path
  if ($r) { $status = "ALIVE"; $color = "Green" } else { $status = "OFF/N/A"; $color = "DarkGray" }
  Write-Host ("  {0,-28} {1}" -f $e.name, $status) -ForegroundColor $color
}

Write-Host "`n[2/3] 建母體 inbox 路徑..." -ForegroundColor Yellow
$paths = @(
  "D:\MRL_Mother\WorldLoop_Inbox\jump",
  "D:\MRL_Mother\WorldLoop_Inbox\collapse",
  "D:\MRL_Mother\WorldModel_Readiness_20261008\supervisor",
  "D:\MRL_Mother\WorldModel_Readiness_20261008\guardian_receipts"
)
foreach ($p in $paths) {
  if (-not (Test-Path $p)) { New-Item -ItemType Directory -Path $p -Force | Out-Null }
  Write-Host "  $p"
}

Write-Host "`n[3/3] install_services.ps1 ..." -ForegroundColor Yellow
& powershell -ExecutionPolicy Bypass -File (Join-Path $ROOT "06_deploy\install_services.ps1")
exit $LASTEXITCODE
