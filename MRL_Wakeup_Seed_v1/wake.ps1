# MRL Wakeup Seed v1 - one-click wake on DL580 (origin_signature: MrLiouWord)
# ASCII-only on purpose: Windows PowerShell 5.1 reads BOM-less scripts as ANSI.
# 1) update repo  2) run wake_verify.py (default root D:\)  3) commit receipt (append-only)
$Repo   = "D:\MRL_AI_SYSTEM"
$Branch = "MRL_AI_SYSTEM/memory-system-rules-prep"
if (Test-Path "$Repo\.git") { git -C $Repo pull --rebase origin $Branch }
else { Write-Host "Repo not found at $Repo - clone it first (see 00_WAKE_ME_FIRST.md)"; exit 1 }
$py = (Get-Command python -ErrorAction SilentlyContinue).Source
if (-not $py) { $py = (Get-Command py -ErrorAction SilentlyContinue).Source }
if (-not $py) { Write-Host "Python not found. Install: winget install Python.Python.3.12"; exit 1 }
$env:PYTHONIOENCODING = "utf-8"
try { [Console]::OutputEncoding = [System.Text.Encoding]::UTF8 } catch {}
& $py "$Repo\MRL_Wakeup_Seed_v1\04_Reflex\wake_verify.py" @args
$code = $LASTEXITCODE
git -C $Repo add "MRL_Wakeup_Seed_v1/05_Agent/receipts"
git -C $Repo -c user.name=dofaromg -c user.email=dofaromg@users.noreply.github.com commit -m "MRL wake receipt (append-only)"
git -C $Repo push origin "HEAD:$Branch"
if ($LASTEXITCODE -ne 0) { Write-Host "Receipt is saved locally in receipts\ ; push failed but local copy is kept." }
exit $code
