# origin_signature: MrLiouWord
# SUPPLEMENT_EXISTING: run the local read-only recovery validator on DL580.
[CmdletBinding()]
param(
  [string]$PythonExe = 'D:\MrlToolchain\python\python.exe',
  [string]$OutFile,
  [string]$PreviousReceipt
)
$ErrorActionPreference = 'Stop'
if ($env:COMPUTERNAME -ine 'WIN-PBVUI7VK2A6') { throw 'Expected DL580 host WIN-PBVUI7VK2A6.' }
$repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
if ([IO.Path]::GetPathRoot($repoRoot) -ine 'D:\') { throw 'Recovery source must be on D:.' }
if (-not (Test-Path -LiteralPath $PythonExe -PathType Leaf)) { throw 'Existing DL580 Python executable was not found.' }
$scriptPath = Join-Path $repoRoot 'scripts\MRL_localai_recovery_acceptance_v1.py'
$runArgs = @('-B', $scriptPath, '--repo-root', $repoRoot)
if ($OutFile) { $runArgs += @('--out', $OutFile) }
if ($PreviousReceipt) { $runArgs += @('--previous-receipt', $PreviousReceipt) }
& $PythonExe @runArgs
exit $LASTEXITCODE
