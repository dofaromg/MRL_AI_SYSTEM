# MRL_DL580Partner_Setup_v1 — Windows DL580 夥伴入口
# origin_signature=MrLiouWord
$ErrorActionPreference = "Stop"
$Pending = $false
function Write-Pending([string]$Message) {
    Write-Warning "待驗證：$Message"
    $script:Pending = $true
}

function Invoke-NativeCommand([scriptblock]$Command) {
    $ErrorActionPreference = "Continue"
    $PSNativeCommandUseErrorActionPreference = $false
    & $Command
    $script:NativeExitCode = $LASTEXITCODE
}

if ($env:OS -ne "Windows_NT") {
    throw "此入口只支援 Windows；Linux 請用 MRL_dl580_partner_setup.sh。"
}
foreach ($Dependency in @("git", "python", "curl.exe")) {
    if (-not (Get-Command $Dependency -ErrorAction SilentlyContinue)) {
        throw "缺少 $Dependency；請安裝 Git for Windows、Python 3 及 curl 後重跑。"
    }
}
$MrlHome = Invoke-NativeCommand { & git -C $PSScriptRoot rev-parse --show-toplevel }
if ($NativeExitCode -ne 0) { throw "請在母體 Git checkout 中執行此入口。" }
Write-Output "MRL_DL580Partner_Setup_v1 origin_signature=MrLiouWord"
Write-Output "node_role=DL580 母體自運行節點；Claude Code 為本機工程夥伴，非母體本體"

$Changes = Invoke-NativeCommand { & git -C $MrlHome status --porcelain }
if ($NativeExitCode -ne 0) { throw "無法檢查 checkout 狀態。" }
if ($Changes) {
    Write-Pending "checkout 有本地變更，略過更新。"
} else {
    Invoke-NativeCommand { & git -C $MrlHome rev-parse --verify '@{upstream}' 2>$null }
    if ($NativeExitCode -eq 0) {
        Invoke-NativeCommand { & git -C $MrlHome pull --ff-only }
        if ($NativeExitCode -ne 0) { Write-Pending "fast-forward 更新失敗，保留本地版本。" }
    } else {
        Write-Pending "checkout 沒有 upstream，略過更新。"
    }
}

# 僅啟用已安裝的服務，不改 sshd_config、驗證方式或防火牆。
$Ssh = Get-Service -Name sshd -ErrorAction SilentlyContinue
if (-not $Ssh) {
    Write-Pending "請管理員先安裝 Windows OpenSSH Server optional feature，再重跑。"
} else {
    try {
        if ($Ssh.StartType -ne "Automatic") {
            Set-Service -Name sshd -StartupType Automatic
        }
        if ($Ssh.Status -ne "Running") { Start-Service -Name sshd }
        if ((Get-Service -Name sshd).Status -ne "Running") {
            Write-Pending "SSH 尚未運行。"
        }
    } catch {
        Write-Pending "啟用 SSH 需要管理員權限；請管理員啟用 sshd 後，以日常帳號重跑。"
    }
}

$TsIp = ""
$Tailscale = Get-Command tailscale -ErrorAction SilentlyContinue
if (-not $Tailscale) {
    $TsPath = Join-Path $env:ProgramFiles "Tailscale\tailscale.exe"
    if (Test-Path $TsPath) { $Tailscale = $TsPath }
}
if ($Tailscale) {
    $Address = Invoke-NativeCommand { & $Tailscale ip -4 2>$null }
    if ($NativeExitCode -eq 0) { $TsIp = $Address | Select-Object -First 1 }
}
if (-not $TsIp) {
    Write-Pending "請先安裝 Tailscale 並登入 Tailnet，再重跑以取得私有位址。"
}

$Claude = Get-Command claude -ErrorAction SilentlyContinue
$LocalClaude = Join-Path $HOME ".local\bin\claude.exe"
if (-not $Claude -and (Test-Path $LocalClaude)) { $Claude = $LocalClaude }
if (-not $Claude) {
    $Installer = Join-Path ([System.IO.Path]::GetTempPath()) ([System.IO.Path]::GetRandomFileName() + ".ps1")
    try {
        Invoke-NativeCommand { & curl.exe -fsSL https://claude.ai/install.ps1 -o $Installer }
        if ($NativeExitCode -ne 0) { throw "官方安裝程式下載失敗。" }
        & $Installer
        $Claude = Get-Command claude -ErrorAction SilentlyContinue
        if (-not $Claude -and (Test-Path $LocalClaude)) { $Claude = $LocalClaude }
    } catch {
        Write-Pending "Claude Code 官方安裝失敗，請檢查官方 OS／架構需求及 Git Bash。"
    } finally {
        Remove-Item -LiteralPath $Installer -Force -ErrorAction SilentlyContinue
    }
}
if ($Claude) {
    Invoke-NativeCommand { & $Claude --version }
    if ($NativeExitCode -ne 0) { Write-Pending "Claude Code 無法執行。" }
} else {
    Write-Pending "找不到 Claude Code。"
}

Invoke-NativeCommand { & python (Join-Path $MrlHome "09_workflow\MRL_mother_assembly.py") status }
if ($NativeExitCode -ne 0) { Write-Pending "母體 status 未通過；請確認 Python 3 可用。" }

Write-Output "Secure ShellFish（手機也須登入同一 Tailnet，ACL 必須允許 SSH）："
if ($TsIp) { Write-Output "  Host: $TsIp" } else { Write-Output "  Host: 待取得 Tailscale IPv4" }
Write-Output "  Port: 22（預設；若原 SSH 使用其他埠，沿用原埠）"
Write-Output "  User: $(& whoami)"
$QuotedHome = $MrlHome.Replace("'", "''")
$ClaudePath = if ($Claude -is [System.Management.Automation.CommandInfo]) {
    if ($Claude.Source) { $Claude.Source } else { $Claude.Name }
} elseif ($Claude) { $Claude } else { "claude" }
$QuotedClaude = $ClaudePath.Replace("'", "''")
Write-Output "連上後於 PowerShell 執行：Set-Location '$QuotedHome'; & '$QuotedClaude'"
Write-Output "首次執行 claude 需自行登入；不更動電源策略、防火牆或既有 Runtime。"
Write-Output "母體／真模型／SSH 端到端均須實機驗收，本設定不代表 DL580 已上線。"
if ($Pending) {
    Write-Output "當下狀態：PARTIAL（有待處理項目，處理後可重跑）。"
    exit 1
}
Write-Output "當下狀態：本機設定檢查完成；手機連線及實機 Runtime 驗收 pending。"
