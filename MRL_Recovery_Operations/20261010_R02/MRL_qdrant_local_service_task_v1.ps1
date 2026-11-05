#requires -Version 5.1
# origin_signature: MrLiouWord
[CmdletBinding()]
param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('AclNew','AclCheck','Install','Inspect','Start','Stop','Remove')]
  [string]$Operation,
  [Parameter(Mandatory=$true)][string]$Instance,
  [string]$Target
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'
function Assert-DPath([string]$Value) {
  $p = [IO.Path]::GetFullPath($Value)
  if ($p -notmatch '^D:\\' -or $p.StartsWith('\\')) { throw 'd_path_required' }
  $d = New-Object IO.DriveInfo('D:\')
  if (-not $d.IsReady -or $d.DriveType -ne [IO.DriveType]::Fixed) { throw 'fixed_d_required' }
  $x = $p
  while ($x) {
    if (-not (Test-Path -LiteralPath $x)) { throw 'path_missing' }
    $item = Get-Item -LiteralPath $x -Force
    if (($item.Attributes -band [IO.FileAttributes]::ReparsePoint) -ne 0) { throw 'reparse_rejected' }
    $next = [IO.Path]::GetDirectoryName($x.TrimEnd('\'))
    if ($next -eq $x) { break }
    $x = $next
  }
  return $p
}
function Get-AclMetadata([string]$Value) {
  $p = Assert-DPath $Value
  $acl = Get-Acl -LiteralPath $p
  $allowed = @('S-1-5-18', 'S-1-5-32-544')
  $seen = New-Object 'System.Collections.Generic.HashSet[string]'
  $count = 0
  foreach ($r in $acl.Access) {
    $sid = $r.IdentityReference.Translate([Security.Principal.SecurityIdentifier]).Value
    if ($allowed -notcontains $sid -or
        $r.AccessControlType -ne [Security.AccessControl.AccessControlType]::Allow -or
        (($r.FileSystemRights -band [Security.AccessControl.FileSystemRights]::FullControl) -ne
          [Security.AccessControl.FileSystemRights]::FullControl)) { throw 'acl_not_private' }
    [void]$seen.Add($sid)
    $count++
  }
  if ($seen.Count -ne 2 -or $count -ne 2) { throw 'acl_principals_invalid' }
  return [ordered]@{ private_system_admin_only=$true; ace_count=$count
                    inheritance_protected=[bool]$acl.AreAccessRulesProtected }
}
function Duration-Seconds([string]$Value) {
  return [Xml.XmlConvert]::ToTimeSpan($Value).TotalSeconds
}
function Task-Metadata($Task, $Manifest) {
  $d = $Task.Definition
  if ($d.Actions.Count -ne 1 -or $d.Triggers.Count -ne 1) { throw 'task_shape_mismatch' }
  $a = $d.Actions.Item(1)
  $b = $d.Triggers.Item(1)
  $args = '-B "' + $Instance + '\runtime\MRL_qdrant_local_service_v1.py" supervise --instance "' + $Instance + '"'
  if ($a.Type -ne 0 -or $a.Path -ine 'D:\MrlToolchain\python\python.exe' -or
      $a.Arguments -cne $args -or $a.WorkingDirectory -ine $Instance) { throw 'task_action_mismatch' }
  if (@('SYSTEM','S-1-5-18','NT AUTHORITY\SYSTEM') -notcontains $d.Principal.UserId -or
      $d.Principal.LogonType -ne 5 -or $d.Principal.RunLevel -ne 1) { throw 'task_principal_mismatch' }
  if ($b.Type -ne 8 -or -not $b.Enabled -or (Duration-Seconds $b.Delay) -ne 30 -or
      (Duration-Seconds $b.ExecutionTimeLimit) -ne 0) { throw 'task_boot_trigger_mismatch' }
  $s = $d.Settings
  if ($s.MultipleInstances -ne 2 -or $s.RestartCount -ne 3 -or
      (Duration-Seconds $s.RestartInterval) -ne 60 -or (Duration-Seconds $s.ExecutionTimeLimit) -ne 0 -or
      -not $s.StartWhenAvailable -or -not $s.AllowDemandStart -or
      $s.DisallowStartIfOnBatteries -or $s.StopIfGoingOnBatteries -or
      $s.RunOnlyIfNetworkAvailable) { throw 'task_restart_policy_mismatch' }
  if ($Task.Path -ine ('\' + $Manifest.task_name)) { throw 'task_name_mismatch' }
  return [ordered]@{
    task_name=$Manifest.task_name; definition_verified=$true
    enabled=[bool]$Task.Enabled; state=[int]$Task.State; last_result=[long]$Task.LastTaskResult
    principal_system=$true; run_level='HighestAvailable'; boot_delay_seconds=30
    multiple_instances='IgnoreNew'; restart_count=3; restart_interval_seconds=60
    execution_time_limit='PT0S'; source_action_verified=$true
  }
}
try {
  if ([Environment]::MachineName -ine 'WIN-PBVUI7VK2A6') { throw 'wrong_host' }
  $id = [Security.Principal.WindowsIdentity]::GetCurrent()
  $principal = New-Object Security.Principal.WindowsPrincipal($id)
  if (-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    throw 'elevated_admin_required'
  }
  $Instance = Assert-DPath $Instance
  if ($Instance -notmatch '^D:\\MRL_Mother\\QdrantLocal\\[0-9a-f]{32}$') { throw 'instance_boundary_invalid' }
  if ($Operation -eq 'AclNew') {
    if (@(Get-ChildItem -LiteralPath $Instance -Force).Count -ne 0) { throw 'new_empty_instance_required' }
    $acl = New-Object Security.AccessControl.DirectorySecurity
    $acl.SetAccessRuleProtection($true,$false)
    foreach ($sidText in @('S-1-5-18','S-1-5-32-544')) {
      $sid = New-Object Security.Principal.SecurityIdentifier($sidText)
      $rule = New-Object Security.AccessControl.FileSystemAccessRule(
        $sid, [Security.AccessControl.FileSystemRights]::FullControl,
        [Security.AccessControl.InheritanceFlags]'ContainerInherit,ObjectInherit',
        [Security.AccessControl.PropagationFlags]::None,
        [Security.AccessControl.AccessControlType]::Allow)
      $acl.AddAccessRule($rule)
    }
    Set-Acl -LiteralPath $Instance -AclObject $acl
    $m = Get-AclMetadata $Instance
    if (-not $m.inheritance_protected) { throw 'new_acl_not_protected' }
    [ordered]@{status='ACL_PRIVATE'; origin_signature='MrLiouWord'; acl=$m} | ConvertTo-Json -Compress -Depth 5
    exit 0
  }
  if ($Operation -eq 'AclCheck') {
    $p = Assert-DPath $Target
    if ($p -ine $Instance -and -not $p.StartsWith($Instance + '\',[StringComparison]::OrdinalIgnoreCase)) {
      throw 'acl_target_outside_instance'
    }
    [ordered]@{status='ACL_PRIVATE'; origin_signature='MrLiouWord'; acl=(Get-AclMetadata $p)} |
      ConvertTo-Json -Compress -Depth 5
    exit 0
  }
  [void](Get-AclMetadata $Instance)
  $mp = Join-Path $Instance 'instance.json'
  $m = [IO.File]::ReadAllText((Assert-DPath $mp)) | ConvertFrom-Json
  if ($m.schema -ne 'MRL_Qdrant_Local_Instance_v1' -or $m.origin_signature -ne 'MrLiouWord' -or
      $m.instance_id -cne ([IO.Path]::GetFileName($Instance)) -or
      $m.task_name -cne ('MRL_Qdrant_Local_' + $m.instance_id)) { throw 'manifest_identity_mismatch' }
  $svc = New-Object -ComObject 'Schedule.Service'
  $svc.Connect()
  $folder = $svc.GetFolder('\')
  if ($Operation -eq 'Install') {
    $xmlPath = Assert-DPath (Join-Path $Instance 'task.xml')
    $xmlHash = (Get-FileHash -LiteralPath $xmlPath -Algorithm SHA256).Hash.ToLowerInvariant()
    if ($xmlHash -cne $m.task_xml_sha256) { throw 'task_xml_hash_mismatch' }
    $xml = [IO.File]::ReadAllText($xmlPath)
    # TASK_CREATE=2 only; never TASK_UPDATE or TASK_CREATE_OR_UPDATE.
    $t = $folder.RegisterTask($m.task_name,$xml,2,'SYSTEM',$null,5,
      'D:P(A;;GA;;;SY)(A;;GA;;;BA)')
    $tm = Task-Metadata $t $m
    if ($tm.enabled -or $tm.state -ne 1) { throw 'installed_task_not_disabled' }
    [ordered]@{status='INSTALLED_DISABLED'; origin_signature='MrLiouWord'; task=$tm} |
      ConvertTo-Json -Compress -Depth 5
    exit 0
  }
  $task = $folder.GetTask($m.task_name)
  $tm = Task-Metadata $task $m
  if ($Operation -eq 'Start') {
    $task.Enabled = $true
    if ($task.State -ne 4) { [void]$task.Run($null) }
    $tm = Task-Metadata $task $m
    $status='START_REQUESTED'
  }
  elseif ($Operation -eq 'Stop') {
    $task.Enabled = $false
    if ($task.State -eq 4 -or $task.State -eq 2) { $task.Stop(0) }
    $tm = Task-Metadata $task $m
    $status='STOP_REQUESTED_DISABLED'
  }
  elseif ($Operation -eq 'Remove') {
    if ($task.Enabled -or $task.State -eq 4 -or $task.State -eq 2) { throw 'disable_and_stop_before_remove' }
    $folder.DeleteTask($m.task_name,0)
    [ordered]@{status='OWN_TASK_REMOVED'; origin_signature='MrLiouWord'; task_name=$m.task_name
                data_removed=$false; keys_removed=$false} | ConvertTo-Json -Compress
    exit 0
  }
  else { $status='TASK_INSPECTED' }
  [ordered]@{status=$status; origin_signature='MrLiouWord'; task=$tm} |
    ConvertTo-Json -Compress -Depth 5
  exit 0
}
catch {
  $e = $_.Exception
  while ($null -ne $e.InnerException) { $e=$e.InnerException }
  [ordered]@{status='FAILED'; origin_signature='MrLiouWord'; operation=$Operation
             error_type=$e.GetType().Name; hresult=[long]$e.HResult} | ConvertTo-Json -Compress
  exit 2
}
