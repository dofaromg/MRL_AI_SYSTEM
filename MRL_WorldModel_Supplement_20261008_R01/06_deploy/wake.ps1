# wake.ps1 — DL580 一鍵喚醒 MRL_WorldModel_Supplement_R01
# origin_signature: MrLiouWord ｜ 2026-10-08 ｜ Additive-Only (LAW-2)
#
# 在 DL580 執行後：
#   1) 檢查已有 7816/7833/8788 是否 ALIVE（不碰它們）
#   2) 建母體路徑 D:\MRL_Mother\WorldLoop_Inbox\{jump,collapse}
#      和 D:\MRL_Mother\WorldModel_Readiness_20261008\{supervisor,guardian_receipts}
#   3) 用 Start-Process 起 Jump 7834 / Collapse 7835 / Guardian 7836
#   4) Supervisor 跑一次 --once，寫一份 readiness 收據
#   5) 全部 health 列出
#
# 不覆蓋任何已存在服務；若 7834/7835/7836 已占用，報錯退出不強殺。

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$ORIG = "MrLiouWord"
Write-Host "===== MRL_WorldModel_Supplement R01 Wake =====" -ForegroundColor Cyan
Write-Host "origin_signature: $ORIG"
Write-Host "pack root: $ROOT"
Write-Host "host: $env:COMPUTERNAME  user: $env:USERNAME"
Write-Host ""

function Test-PortAlive($port, $path = "/health") {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 `
         "http://127.0.0.1:$port$path"
    return $r.StatusCode -eq 200
  } catch { return $false }
}

function Assert-FreePort($port) {
  $busy = Get-NetTCPConnection -LocalPort $port -State Listen `
          -ErrorAction SilentlyContinue
  if ($busy) {
    throw "Port $port is already in use (PID=$($busy.OwningProcess)). 停下腳本以免覆蓋現有服務。"
  }
}

# 1) 檢查已有服務（唯讀）
Write-Host "[1/5] 既有服務唯讀檢查..." -ForegroundColor Yellow
$existing = @{
  "7816 ReasoningEngine" = (Test-PortAlive 7816)
  "7833 WorldLoop"       = (Test-PortAlive 7833)
  "8788 ParticleGlobe"   = (Test-PortAlive 8788 "/particle/stats?user_id=mrl_world")
}
$existing.GetEnumerator() | ForEach-Object {
  if ($_.Value) { $status = "ALIVE"; $color = "Green" }
  else          { $status = "OFF/N/A"; $color = "DarkGray" }
  Write-Host ("  {0,-25} {1}" -f $_.Key, $status) -ForegroundColor $color
}

# 2) 建母體路徑
Write-Host "`n[2/5] 建母體 inbox 路徑..." -ForegroundColor Yellow
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

# 3) 檢查 7834/7835/7836 未被占
Write-Host "`n[3/5] 檢查新端口是否空閒..." -ForegroundColor Yellow
foreach ($p in 7834, 7835, 7836) { Assert-FreePort $p }
Write-Host "  7834, 7835, 7836 都空閒"

# 4) 起三個服務
Write-Host "`n[4/5] 起 Jump / Collapse / Guardian..." -ForegroundColor Yellow
$logDir = Join-Path $ROOT "07_evidence\runtime_logs_$(Get-Date -Format 'yyyyMMdd_HHmmss')"
New-Item -ItemType Directory -Path $logDir -Force | Out-Null

$svcs = @(
  @{ name="Jump";     port=7834; script="01_jump\MRL_Jump_Service.py" },
  @{ name="Collapse"; port=7835; script="02_collapse\MRL_Collapse_Service.py" },
  @{ name="Guardian"; port=7836; script="03_agent\MRL_AnalystGuardian_Agent.py" }
)
foreach ($s in $svcs) {
  $script = Join-Path $ROOT $s.script
  $out = Join-Path $logDir "$($s.name)_stdout.log"
  $err = Join-Path $logDir "$($s.name)_stderr.log"
  # 注意：PowerShell Start-Process 的 -RedirectStandardOutput 必須配 -NoNewWindow
  # 不能跟 -WindowStyle 一起用；一次性 smoke test 可接受共享 console。
  Start-Process -FilePath "python" -ArgumentList $script `
                -NoNewWindow `
                -RedirectStandardOutput $out `
                -RedirectStandardError  $err `
                -PassThru | Out-Null
  Write-Host "  起 $($s.name) → log $out"
}
Start-Sleep -Seconds 4

# 5) 全部 health 確認
Write-Host "`n[5/5] 新服務 health 回測..." -ForegroundColor Yellow
foreach ($s in $svcs) {
  if (Test-PortAlive $s.port) {
    Write-Host ("  {0,-10} :{1}  ALIVE" -f $s.name, $s.port) -ForegroundColor Green
  } else {
    Write-Host ("  {0,-10} :{1}  FAIL (查 log)" -f $s.name, $s.port) -ForegroundColor Red
  }
}

# 6) Supervisor 跑一次收 readiness
Write-Host "`n[+] Supervisor --once..." -ForegroundColor Yellow
$sup = Join-Path $ROOT "04_supervisor\MRL_WorldModel_Supervisor.py"
& python $sup --once
Write-Host "`n完成。 origin_signature: $ORIG" -ForegroundColor Cyan
