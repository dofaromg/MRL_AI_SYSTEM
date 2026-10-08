# install_services.ps1 — 把 Jump/Collapse/Guardian 註冊為 Windows 排程任務
# origin_signature: MrLiouWord ｜ 2026-10-08
#
# 註冊三個開機自動啟動的 ScheduledTask：
#   MRL_Jump_7834
#   MRL_Collapse_7835
#   MRL_Guardian_7836
# 以及一個每分鐘跑一次的 Supervisor：
#   MRL_WorldModel_Supervisor
#
# 以系統管理員身份執行。重跑是冪等（會先 Unregister 同名）。

$ErrorActionPreference = "Stop"
$ROOT = Split-Path -Parent $PSScriptRoot
Write-Host "===== Install MRL WorldModel Supplement services =====" -ForegroundColor Cyan
Write-Host "pack root: $ROOT"

function Register-PyService($name, $script, $argStr = "") {
  $full = Join-Path $ROOT $script
  if (-not (Test-Path $full)) { throw "script not found: $full" }
  $existing = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  if ($existing) {
    Unregister-ScheduledTask -TaskName $name -Confirm:$false
    Write-Host "  (removed old $name)"
  }
  if ($argStr) { $arg = "`"$full`" $argStr" } else { $arg = "`"$full`"" }
  $action = New-ScheduledTaskAction -Execute "python" -Argument $arg `
            -WorkingDirectory $ROOT
  $trigger = New-ScheduledTaskTrigger -AtStartup
  $principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" `
               -LogonType ServiceAccount -RunLevel Highest
  $settings = New-ScheduledTaskSettingsSet -AllowStartIfOnBatteries `
              -DontStopIfGoingOnBatteries -StartWhenAvailable `
              -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
  Register-ScheduledTask -TaskName $name -Action $action `
    -Trigger $trigger -Principal $principal -Settings $settings `
    -Description "MRL WorldModel Supplement R01 — $name  origin:MrLiouWord" | Out-Null
  Start-ScheduledTask -TaskName $name
  Write-Host "  registered & started: $name" -ForegroundColor Green
}

Register-PyService "MRL_Jump_7834"     "01_jump\MRL_Jump_Service.py"
Register-PyService "MRL_Collapse_7835" "02_collapse\MRL_Collapse_Service.py"
Register-PyService "MRL_Guardian_7836" "03_agent\MRL_AnalystGuardian_Agent.py"
Register-PyService "MRL_WorldModel_Supervisor" `
                   "04_supervisor\MRL_WorldModel_Supervisor.py" "--interval 60"

Write-Host "`nDone. 查 Task Scheduler → Task Scheduler Library，應看到 4 條 MRL_*"
Write-Host "origin_signature: MrLiouWord" -ForegroundColor Cyan
