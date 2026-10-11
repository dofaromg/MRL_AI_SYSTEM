# origin_signature: MrLiouWord
# Reversible update of the existing MRL_Watchdog task; no service stop.
# v3 preserves Python startup environment and commits receipts before metadata reporting.
[CmdletBinding()]
param([Parameter(Mandatory=$true)][ValidatePattern('^[0-9a-f]{64}$')][string]$ExpectedHelperSha)
$ErrorActionPreference='Stop'
$Ops='D:\MRL_Mother\Recovery\_operations\LocalAI_20261010_R02_be2f1d63'
$Runtime=$Ops+'\active_watchdog_20261010_R01'
$Helper=$Runtime+'\MRL_active_runtime_watchdog_v3.py'
$Python='D:\MrlToolchain\python\python.exe'
$Original='D:\mrl\MRL_Watchdog.py'
$NewArguments='-B "'+$Helper+'" --run --runtime-root "'+$Runtime+'"'
$Mutated=$false
$ReceiptCommitted=$false
$Phase='PREFLIGHT'
$FailedChecks=@()
$BeforeXml=$null
function Hash-Text([string]$Text){return ([BitConverter]::ToString([Security.Cryptography.SHA256]::Create().ComputeHash([Text.Encoding]::UTF8.GetBytes($Text)))).Replace('-','').ToLower()}
function Hash-File([string]$Path){return (Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLower()}
function Assert-D([string]$Path){
 $f=[IO.Path]::GetFullPath($Path)
 if(-not $f.StartsWith('D:\',[StringComparison]::OrdinalIgnoreCase)){throw 'D_PATH_REQUIRED'}
 $p=$f
 while($p){if(Test-Path -LiteralPath $p){if(((Get-Item -LiteralPath $p -Force).Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0){throw 'REPARSE_PATH_REJECTED'}};$next=[IO.Path]::GetDirectoryName($p);if($next -eq $p){break};$p=$next}
}
function Write-Exclusive([string]$Path,[string]$Text){
 Assert-D $Path
 $b=[Text.UTF8Encoding]::new($false).GetBytes($Text)
 $f=[IO.File]::Open($Path,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
 try{$f.Write($b,0,$b.Length);$f.Flush($true)}finally{$f.Dispose()}
}
function File-Meta([string]$Path){return @{path=$Path;bytes=(Get-Item -LiteralPath $Path).Length;sha256=(Hash-File $Path)}}
function Owners([int]$Port){return @((Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction Stop | Select-Object -ExpandProperty OwningProcess -Unique)|Sort-Object)}
function Without-Allowed-Changes([xml]$Doc){
 foreach($xp in @("//*[local-name()='Actions']/*[local-name()='Exec']/*[local-name()='Arguments']","//*[local-name()='Settings']/*[local-name()='ExecutionTimeLimit']","//*[local-name()='Settings']/*[local-name()='RestartOnFailure']")){
  foreach($n in @($Doc.SelectNodes($xp))){[void]$n.ParentNode.RemoveChild($n)}
 }
 return $Doc.OuterXml
}
try{
 if($env:COMPUTERNAME -ine 'WIN-PBVUI7VK2A6'){throw 'EXPECTED_HOST_REQUIRED'}
 foreach($p in @($Ops,$Runtime,$Helper,$Python,$Original)){Assert-D $p}
 if((Hash-File $Python) -ne '624bbc0586d8855633b875e911883bbef8a0e8b8711e11126df480dd86f54181'){throw 'PYTHON_HASH_MISMATCH'}
 if((Hash-File $Helper) -ne $ExpectedHelperSha){throw 'HELPER_HASH_MISMATCH'}
 if((Hash-File $Original) -ne '2c327ed594594425a7a58d2082abc624a22531f7011d446dd2bd999172eff846'){throw 'ORIGINAL_WATCHDOG_CHANGED'}
 $t=Get-ScheduledTask -TaskName 'MRL_Watchdog' -TaskPath '\'
 if($t.State.ToString() -ne 'Ready'){throw 'TASK_NOT_READY'}
 if(@($t.Actions).Count -ne 1 -or $t.Actions[0].Execute -cne $Python){throw 'ACTION_BASELINE_CHANGED'}
 if((Hash-Text ([string]$t.Actions[0].Arguments)) -ne 'df680bfbf158ea9b5ec4197220ee29ecc94b00b8bf089b8d7f1d6248a85b7b80'){throw 'ARGUMENTS_BASELINE_CHANGED'}
 if(@($t.Triggers).Count -ne 1 -or $t.Triggers[0].CimClass.CimClassName -ne 'MSFT_TaskBootTrigger'){throw 'BOOT_TRIGGER_BASELINE_CHANGED'}
 if($t.Settings.ExecutionTimeLimit -cne 'PT72H' -or $t.Settings.RestartCount -ne 0){throw 'SETTINGS_BASELINE_CHANGED'}
 $infoBefore=Get-ScheduledTaskInfo -InputObject $t
 $BeforeXml=Export-ScheduledTask -TaskName 'MRL_Watchdog' -TaskPath '\'
 $backup=Join-Path $Ops 'MRL_Watchdog_before_active_runtime_20261010_R03.xml'
 Write-Exclusive $backup $BeforeXml
 $asi='D:\mrl\asi-engine\server.js';Assert-D $asi;$asiHash=Hash-File $asi
 if($asiHash -ne '4dfd3194b7519efb6eef7236024a3953d2dd8842c9dc38c52ec71c6c0c807f5e'){throw 'ASI_SOURCE_CHANGED'}
 $before7500=Owners 7500;$before7700=Owners 7700
 $actions=@($t.Actions);$actions[0].Arguments=$NewArguments
 $settings=$t.Settings;$settings.ExecutionTimeLimit='PT0S';$settings.RestartCount=3;$settings.RestartInterval='PT1M'
 $Phase='UPDATE'
 $Mutated=$true
 Set-ScheduledTask -TaskName 'MRL_Watchdog' -TaskPath '\' -Action $actions -Settings $settings|Out-Null
 $after=Get-ScheduledTask -TaskName 'MRL_Watchdog' -TaskPath '\'
 $infoAfter=Get-ScheduledTaskInfo -InputObject $after
 $AfterXml=Export-ScheduledTask -TaskName 'MRL_Watchdog' -TaskPath '\'
 $Phase='POST_UPDATE_GATES'
 $checks=[ordered]@{
  exact_arguments=([string]$after.Actions[0].Arguments -ceq $NewArguments)
  executable_unchanged=([string]$after.Actions[0].Execute -ceq $Python)
  unlimited_execution_time=($after.Settings.ExecutionTimeLimit -eq 'PT0S')
  process_restart_policy=($after.Settings.RestartCount -eq 3 -and $after.Settings.RestartInterval -eq 'PT1M')
  all_other_task_xml_unchanged=((Without-Allowed-Changes ([xml]$BeforeXml)) -ceq (Without-Allowed-Changes ([xml]$AfterXml)))
  original_source_preserved=((Hash-File $Original) -eq '2c327ed594594425a7a58d2082abc624a22531f7011d446dd2bd999172eff846')
  active_helper_hash_verified=((Hash-File $Helper) -eq $ExpectedHelperSha)
  asi_source_preserved=((Hash-File $asi) -eq $asiHash)
  inference_owner_preserved=((Owners 7500)-join ',') -ceq ($before7500-join ',')
  asi_owner_preserved=((Owners 7700)-join ',') -ceq ($before7700-join ',')
  task_not_started=($infoBefore.LastRunTime -eq $infoAfter.LastRunTime -and $after.State.ToString() -eq 'Ready')
  bridge_running=((Get-Service -Name 'MRL_Bridge').Status -eq 'Running')
  tunnel_running=((Get-Service -Name 'MRL_Tunnel').Status -eq 'Running')
 }
 $FailedChecks=@($checks.Keys|Where-Object {$checks[$_] -ne $true})
 if($FailedChecks.Count -ne 0){throw 'POST_UPDATE_GATE_FAILED'}
 $result=[ordered]@{
  schema='MRL_Active_Watchdog_Task_Install_R02_v3';origin_signature='MrLiouWord';record_mode='APPEND_ONLY'
  host=$env:COMPUTERNAME;observed_at_utc=[DateTime]::UtcNow.ToString('o');status='TASK_CONFIGURED'
  task='\MRL_Watchdog';checks=$checks;task_xml_backup=(File-Meta $backup);helper=(File-Meta $Helper)
  new_arguments_sha256=(Hash-Text $NewArguments);task_started=$false
  scope=@{inference_7500='REPORT_ONLY';bridge_7800='REPORT_ONLY';asi_7700='BOUNDED_START_ONLY_NO_STOP'}
  fault_recovery='UNVERIFIED';reboot_continuity='UNVERIFIED'
 }
 $Phase='COMMIT_RECEIPT'
 $receipt=Join-Path $Ops 'active_watchdog_task_install_receipt_v3.json'
 Write-Exclusive $receipt (($result|ConvertTo-Json -Depth 8)+[Environment]::NewLine)
 $ReceiptCommitted=$true
 $Phase='REPORT_RECEIPT_METADATA'
 $result['receipt']=File-Meta $receipt
}catch{
 $code=$_.Exception.Message
 if($code -notmatch '^[A-Z0-9_]+$'){$code='TASK_INSTALL_EXCEPTION'}
 $rolled=$false
 if($Mutated -and $BeforeXml -and -not $ReceiptCommitted){
  try{Register-ScheduledTask -TaskName 'MRL_Watchdog' -TaskPath '\' -Xml $BeforeXml -Force|Out-Null
   [xml]$current=Export-ScheduledTask -TaskName 'MRL_Watchdog' -TaskPath '\'
   [xml]$prior=$BeforeXml
   $rolled=($current.OuterXml -ceq $prior.OuterXml)
  }catch{$rolled=$false}
 }
 $terminal=[ordered]@{schema='MRL_Active_Watchdog_Task_Install_R02_v3';origin_signature='MrLiouWord';record_mode='APPEND_ONLY';observed_at_utc=[DateTime]::UtcNow.ToString('o');status='INSTALL_FAILED';failure_code=$code;failed_phase=$Phase;failed_checks=$FailedChecks;task_mutated=$Mutated;receipt_committed=$ReceiptCommitted;rollback_verified=$rolled;start_requested_by_installer=$false}
 if($ReceiptCommitted){$terminal.status='TASK_CONFIGURED_COMMITTED_REPORTING_ERROR'}
 try{
  $terminalPath=Join-Path $Ops ('active_watchdog_task_install_terminal_'+[Guid]::NewGuid().ToString('N')+'.json')
  Write-Exclusive $terminalPath (($terminal|ConvertTo-Json -Depth 8)+[Environment]::NewLine)
  $terminal['terminal_receipt_path']=$terminalPath
 }catch{}
 $result=$terminal
}
$result|ConvertTo-Json -Depth 8 -Compress
if($result.status -eq 'INSTALL_FAILED'){exit 1}
exit 0
