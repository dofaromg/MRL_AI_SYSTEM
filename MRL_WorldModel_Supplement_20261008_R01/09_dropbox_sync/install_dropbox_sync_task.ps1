# install_dropbox_sync_task.ps1 — 註冊 MRL_Dropbox_DL580_Sync（SYSTEM，每 10 分鐘一輪；只新增此任務，不動其他）
# origin_signature: MrLiouWord ｜ 2026-10-10
$ErrorActionPreference = 'Stop'
$Py   = 'D:\MrlToolchain\python\python.exe'
$Eng  = 'D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01\09_dropbox_sync\MRL_Dropbox_DL580_Sync.py'
$Log  = 'D:\MRL_Mother\WorldModel_Readiness_20261008\dropbox_sync\task_run.log'
$Task = 'MRL_Dropbox_DL580_Sync'
New-Item -ItemType Directory -Force -Path (Split-Path $Log) | Out-Null
New-Item -ItemType Directory -Force -Path 'D:\MRL_Mother\Outbox_Dropbox' | Out-Null
$arg = '/c ""' + $Py + '" -X utf8 "' + $Eng + '" --once >> "' + $Log + '" 2>&1"'
$action  = New-ScheduledTaskAction -Execute 'cmd.exe' -Argument $arg
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Minutes 10)
$set     = New-ScheduledTaskSettingsSet -StartWhenAvailable -MultipleInstances IgnoreNew -ExecutionTimeLimit (New-TimeSpan -Hours 2)
$pr      = New-ScheduledTaskPrincipal -UserId 'SYSTEM' -LogonType ServiceAccount -RunLevel Highest
if (Get-ScheduledTask -TaskName $Task -ErrorAction SilentlyContinue) { Write-Output ('任務已存在，不覆蓋：' + $Task) }
else { Register-ScheduledTask -TaskName $Task -Action $action -Trigger $trigger -Settings $set -Principal $pr -Description 'MRL Dropbox(雲本體) -> DL580 同步 (origin_signature MrLiouWord)' | Out-Null; Write-Output ('已註冊 ' + $Task) }
