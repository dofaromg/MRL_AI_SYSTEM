# install_kernel_task.ps1 — 註冊常駐 ASI Kernel 宿主 MRL_ASIKernel_7838（SYSTEM / 開機自啟）
# origin_signature: MrLiouWord ｜ 2026-10-09 ｜ Additive-Only：只新增此任務，不動其他任務
$ErrorActionPreference = 'Stop'
$Pack  = 'D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01\05_kernel'
$Node  = 'D:\MrlToolchain\node\node.exe'
$Out   = 'D:\MRL_Mother\WorldModel_Readiness_20261008\kernel'
$Task  = 'MRL_ASIKernel_7838'
New-Item -ItemType Directory -Force -Path $Out | Out-Null
$busy = Get-NetTCPConnection -LocalPort 7838 -State Listen -ErrorAction SilentlyContinue
if ($busy -and -not (Get-ScheduledTask -TaskName $Task -ErrorAction SilentlyContinue)) {
  Write-Output ('7838 已被 PID ' + $busy.OwningProcess + ' 佔用，且不是本任務 — 停止，不搶綁'); exit 3
}
$cmdArgs = '/c ""' + $Node + '" "' + $Pack + '\MRL_ASI_Kernel_Host.mjs" >> "' + $Out + '\kernel_host.log" 2>&1"'
$action  = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument $cmdArgs -WorkingDirectory $Pack
$trigger = New-ScheduledTaskTrigger -AtStartup
$set     = New-ScheduledTaskSettingsSet -StartWhenAvailable -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1) -ExecutionTimeLimit ([TimeSpan]::Zero) -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries
$pr      = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
if (Get-ScheduledTask -TaskName $Task -ErrorAction SilentlyContinue) {
  Write-Output ('任務 ' + $Task + ' 已存在 — 只重新啟動，不覆蓋')
} else {
  Register-ScheduledTask -TaskName $Task -Action $action -Trigger $trigger -Settings $set -Principal $pr -Description 'MRL ASI Kernel Host 7838 (origin_signature MrLiouWord)' | Out-Null
  Write-Output ('已註冊 ' + $Task)
}
Start-ScheduledTask -TaskName $Task
Start-Sleep -Seconds 4
try {
  $h = Invoke-RestMethod -Uri 'http://127.0.0.1:7838/health' -TimeoutSec 5
  Write-Output ('ALIVE ' + $h.service + ' v' + $h.version + ' kernel_sha_verified=' + $h.kernel.sha_verified + ' tick=' + $h.tick + ' seq=' + $h.timeline_seq + ' replayed=' + $h.restore.replayed + ' match=' + $h.restore.decision_match)
} catch { Write-Output ('health 未回應：' + $_.Exception.Message); Get-Content (Join-Path $Out 'kernel_host.log') -Tail 20 }
