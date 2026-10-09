# ---- Force UTF-8 console (R13-C: PowerShell 5.1 ANSI/Big5 fix) ----
try {
    [Console]::OutputEncoding = [System.Text.Encoding]::UTF8
    $OutputEncoding = [System.Text.Encoding]::UTF8
    chcp 65001 > $null 2>&1
} catch { }
# ------------------------------------------------------------------

# install_services.ps1 — R13-D
# origin_signature: MrLiouWord ｜ 2026-10-09 ｜ Additive-Only
#
# 把 Jump(7837) / Collapse(7835) / Guardian(7836) / Supervisor 註冊為開機自動的排程任務並啟動。
#
# R13-D 變更：
#   - Jump 由 7834 移到 7837（7834 是建構者的 MRL_Convergence_Runtime）
#   - 舊的 MRL_Jump_7834 任務只「停用」不刪除（LAW-2）
#   - 只停「本 pack 自己的」python 程序（以命令列路徑辨識），不碰任何其他服務
#   - 註冊前探 port：有別人在聽就跳過那一個，不搶、不殺
#   - 起來後用 /health 的 service 名稱驗身，不再把別人的回應算成自己的
#   - 結尾跑 Supervisor --once；三個本體服務都驗身通過才 exit 0

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
$ORIG = "MrLiouWord"
$PACK_RE = 'MRL_WorldModel_Supplement_20261008_R01\\0[1-4]_[a-z]+\\MRL_[A-Za-z_]+\.py'

Write-Host "===== Install MRL WorldModel Supplement services (R13-D) =====" -ForegroundColor Cyan
Write-Host "origin_signature: $ORIG"
Write-Host "pack root: $ROOT"

# ── python 完整路徑（排程任務以 SYSTEM 執行，不依賴 PATH） ──
$py = $null
$cmd = Get-Command python -ErrorAction SilentlyContinue
if ($cmd) { $py = $cmd.Source }
if (-not $py -and (Test-Path "D:\MrlToolchain\python\python.exe")) { $py = "D:\MrlToolchain\python\python.exe" }
if (-not $py) { Write-Host "[FAIL] 找不到 python" -ForegroundColor Red; exit 1 }
Write-Host "python: $py"

$SVCS = @(
  @{ task="MRL_Jump_7837";     port=7837; script="01_jump\MRL_Jump_Service.py";               service="MRL_Jump_Service" },
  @{ task="MRL_Collapse_7835"; port=7835; script="02_collapse\MRL_Collapse_Service.py";       service="MRL_Collapse_Service" },
  @{ task="MRL_Guardian_7836"; port=7836; script="03_agent\MRL_AnalystGuardian_Agent.py";    service="MRL_AnalystGuardian_Agent" }
)
$OUR_TASKS = @("MRL_Jump_7834","MRL_Jump_7837","MRL_Collapse_7835","MRL_Guardian_7836","MRL_WorldModel_Supervisor")

function Get-Health($port) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -TimeoutSec 2 "http://127.0.0.1:$port/health"
    return ($r.Content | ConvertFrom-Json)
  } catch { return $null }
}

# ── 1) 停本 pack 的任務與程序（只限本 pack） ──
Write-Host "`n[1/5] 停本 pack 既有任務與程序（只限本 pack 路徑）..." -ForegroundColor Yellow
foreach ($t in $OUR_TASKS) {
  $task = Get-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
  if ($task) {
    Stop-ScheduledTask -TaskName $t -ErrorAction SilentlyContinue
    Write-Host "  停止任務 $t"
  }
}
$old = Get-ScheduledTask -TaskName "MRL_Jump_7834" -ErrorAction SilentlyContinue
if ($old) {
  Disable-ScheduledTask -TaskName "MRL_Jump_7834" | Out-Null
  Write-Host "  停用（不刪除）舊任務 MRL_Jump_7834 —— 7834 屬 MRL_Convergence_Runtime" -ForegroundColor DarkYellow
}
Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" | Where-Object {
  $_.CommandLine -match $PACK_RE
} | ForEach-Object {
  Write-Host ("  停止本 pack 程序 PID {0}: {1}" -f $_.ProcessId, $_.CommandLine)
  Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

# ── 2) port 預檢：有別人在聽就跳過，不搶 ──
Write-Host "`n[2/5] port 預檢..." -ForegroundColor Yellow
$toInstall = @()
foreach ($s in $SVCS) {
  $l = Get-NetTCPConnection -LocalPort $s.port -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1
  if ($l) {
    $p = Get-CimInstance Win32_Process -Filter "ProcessId=$($l.OwningProcess)" -ErrorAction SilentlyContinue
    $h = Get-Health $s.port
    $who = "?"
    if ($h -and $h.service) { $who = $h.service }
    Write-Host ("  {0} 被占用 PID {1} service={2} -> 跳過 {3}，不動它" -f $s.port, $l.OwningProcess, $who, $s.task) -ForegroundColor Red
    Write-Host ("     {0}" -f $p.CommandLine) -ForegroundColor DarkGray
  } else {
    Write-Host ("  {0} 空閒 -> {1}" -f $s.port, $s.task) -ForegroundColor Green
    $toInstall += $s
  }
}

# ── 3) 註冊並啟動 ──
Write-Host "`n[3/5] 註冊並啟動排程任務..." -ForegroundColor Yellow
function Register-PyTask($name, $script, $extra) {
  $full = Join-Path $ROOT $script
  if (-not (Test-Path $full)) { throw "script not found: $full" }
  $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if ($existing) { Unregister-ScheduledTask -TaskName $name -Confirm:$false }  # 同名重註冊（本 pack 自己的任務）
  $arg = "-X utf8 -B `"$full`""
  if ($extra) { $arg = "$arg $extra" }
  $action    = New-ScheduledTaskAction -Execute $py -Argument $arg -WorkingDirectory $ROOT
  $trigger   = New-ScheduledTaskTrigger -AtStartup
  $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest
  $settings  = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries `
               -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) `
               -ExecutionTimeLimit ([TimeSpan]::Zero)
  Register-ScheduledTask -TaskName $name -Action $action -Trigger $trigger -Principal $principal `
    -Settings $settings -Description "MRL WorldModel Supplement R13-D — $name  origin:MrLiouWord" | Out-Null
  Start-ScheduledTask -TaskName $name
  Write-Host "  registered & started: $name" -ForegroundColor Green
}
foreach ($s in $toInstall) { Register-PyTask $s.task $s.script "" }
Register-PyTask "MRL_WorldModel_Supervisor" "04_supervisor\MRL_WorldModel_Supervisor.py" "--interval 60"

# ── 4) 驗身：/health 的 service 名稱要對 ──
Write-Host "`n[4/5] 驗身（最多等 15 秒）..." -ForegroundColor Yellow
$allOk = $true
foreach ($s in $SVCS) {
  $okThis = $false
  for ($i = 0; $i -lt 15; $i++) {
    $h = Get-Health $s.port
    if ($h -and $h.service -eq $s.service) { $okThis = $true; break }
    Start-Sleep -Seconds 1
  }
  if ($okThis) {
    Write-Host ("  {0,-26} :{1}  ALIVE  v{2}" -f $s.service, $s.port, $h.version) -ForegroundColor Green
  } else {
    $allOk = $false
    $got = "no answer"
    if ($h) { $got = "answered by " + $h.service }
    Write-Host ("  {0,-26} :{1}  FAIL ({2})" -f $s.service, $s.port, $got) -ForegroundColor Red
  }
}

# ── 5) Supervisor 一次 ──
Write-Host "`n[5/5] Supervisor --once ..." -ForegroundColor Yellow
& $py -X utf8 -B (Join-Path $ROOT "04_supervisor\MRL_WorldModel_Supervisor.py") --once

Write-Host ""
if ($allOk) {
  Write-Host "全綠：Jump 7837 / Collapse 7835 / Guardian 7836 已由排程任務常駐。origin_signature: $ORIG" -ForegroundColor Cyan
  exit 0
} else {
  Write-Host "未全綠：看上面 FAIL 那一行。origin_signature: $ORIG" -ForegroundColor Red
  exit 1
}
