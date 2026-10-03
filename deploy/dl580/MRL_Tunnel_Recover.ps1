# MRL_Tunnel_Recover.ps1 — 恢復既有 Cloudflare Tunnel 連線（不改 config、不改 DNS、不建新 Tunnel）
# origin_signature: MrLiouWord ｜ Additive-Only
# 依據：2026-05-22 / 2026-06-05 / 2026-07-07 / 2026-09-24 歷次 1033 皆為 DL580 端 cloudflared 未連線；
#       既有 Tunnel mrl-bridge 632dfad4（bridge→:7800、dl580→:3000），服務名 MRL_Tunnel（NSSM）。
# 用法（系統管理員 PowerShell）：powershell -ExecutionPolicy Bypass -File deploy\dl580\MRL_Tunnel_Recover.ps1
$ErrorActionPreference = "Continue"
$log = [ordered]@{ origin_signature="MrLiouWord"; at=(Get-Date).ToUniversalTime().ToString("o"); environment="實機"; steps=@() }
function Step($name, $obj) { $log.steps += [ordered]@{ step=$name; result=$obj }; Write-Host ("[{0}] {1}" -f $name, ($obj | ConvertTo-Json -Compress -Depth 4)) }

# 1. 本機服務先驗（Tunnel 斷 ≠ 服務斷）
foreach ($u in @("http://127.0.0.1:7800/health", "http://127.0.0.1:3000/health")) {
  try { $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 8; Step "local $u" @{ status=[int]$r.StatusCode } }
  catch { Step "local $u" @{ status=0; error=$_.Exception.Message } }
}

# 2. Tunnel 服務狀態
$svcs = @("MRL_Tunnel", "cloudflared") | ForEach-Object { Get-Service -Name $_ -ErrorAction SilentlyContinue } | Where-Object { $_ }
Step "services" @($svcs | ForEach-Object { @{ name=$_.Name; status="$($_.Status)"; start="$($_.StartType)" } })
Step "processes" @(Get-Process cloudflared -ErrorAction SilentlyContinue | ForEach-Object { @{ pid=$_.Id } })

# 3. 只做「啟動／重啟既有服務」；公網入口健康時不重啟（避免中斷既有 bridge／dl580 連線）
function PublicOk { try { $r = Invoke-WebRequest -Uri "https://bridge.mrliouword.com/health" -UseBasicParsing -TimeoutSec 15; return ([int]$r.StatusCode -eq 200) } catch { return $false } }
$publicOk = PublicOk
Step "public_before" @{ bridge_health_ok=$publicOk }
foreach ($s in $svcs) {
  if ($s.Status -ne "Running") {
    try { Start-Service -Name $s.Name -ErrorAction Stop; Step "start $($s.Name)" "ok" } catch { Step "start $($s.Name)" $_.Exception.Message }
  } elseif (-not $publicOk) {
    try { Restart-Service -Name $s.Name -Force -ErrorAction Stop; Step "restart $($s.Name)" "ok" } catch { Step "restart $($s.Name)" $_.Exception.Message }
  } else {
    Step "keep $($s.Name)" "running and public entry healthy; not restarted"
  }
}
if (-not $svcs) { Step "no_service" "找不到 MRL_Tunnel／cloudflared 服務；未自動建立（避免另開 Tunnel）。請回報此收據。" }

# 4. 等連線器上線後驗公網入口
Start-Sleep -Seconds 20
foreach ($u in @("https://bridge.mrliouword.com/health", "https://dl580.mrliouword.com/health")) {
  try { $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 15; Step "public $u" @{ status=[int]$r.StatusCode } }
  catch { $code = if ($_.Exception.Response) { [int]$_.Exception.Response.StatusCode } else { 0 }; Step "public $u" @{ status=$code; error=$_.Exception.Message } }
}

$out = if ($env:MRL_DATA_ROOT) { Join-Path $env:MRL_DATA_ROOT "receipts" } else { "D:\MRL_runtime\receipts" }
New-Item -ItemType Directory -Force -Path $out | Out-Null
$f = Join-Path $out ("MRL_Tunnel_Recover_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".json")
$log | ConvertTo-Json -Depth 6 | Out-File -FilePath $f -Encoding utf8
Write-Host "RECEIPT -> $f"
