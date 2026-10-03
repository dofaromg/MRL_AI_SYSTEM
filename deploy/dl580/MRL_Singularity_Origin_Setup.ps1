# MRL_Singularity_Origin_Setup.ps1 — DL580 端：奇異點（固定 IP）入口 ＋ Tunnel 備援
# origin_signature: MrLiouWord ｜ Additive-Only（不刪既有服務、不改既有 ingress，只新增）
#
# 雲端層已完成（2026-10-03）：
#   origin.mrliouword.com  A 220.132.58.129（proxied）＋ Cloudflare Access（只放行 mrliousilly 的 service token）
#   dl580.mrliouword.com 的 5 條 API 路徑同樣受 Access 保護
#   Worker mrliousilly：先打 origin，失敗再打 dl580（Tunnel）
#
# 本腳本在 DL580 做：
#   1. MRL_Platform（MRL_Platform_Server.py）以 NSSM 服務跑在 :7960（:8790 已屬 RuntimeOS v1.4.0）
#   2. HTTPS 入口：Caddy 於 :$EdgePort，TLS internal（zone SSL=Full 接受），反代 127.0.0.1:7960
#   3. Windows 防火牆：$EdgePort 只允許 Cloudflare IP 範圍（固定 IP 不對外裸露）
#   4. （-AddTunnelPathRule）既有 Tunnel config.yml 備份後，在 dl580 規則前「新增」5 條路徑 → :7960，重啟 MRL_Tunnel
#   5. 本機驗收並寫收據
# 路由器（需人工）：PPPoE 固定 IP 帳號撥號；TCP $EdgePort → DL580 LAN IP:$EdgePort 埠轉發。
#
# 用法（系統管理員 PowerShell，MRL_HOME 為 repo 根目錄）：
#   powershell -ExecutionPolicy Bypass -File deploy\dl580\MRL_Singularity_Origin_Setup.ps1 [-AddTunnelPathRule] [-EdgePort 443]
param(
  [int]$PlatformPort = 7960,
  [int]$EdgePort = 443,
  [string]$EdgeHost = "origin.mrliouword.com",
  [string]$EdgeHome = "D:\MRL_Edge",
  [string]$Nssm = "D:\nssm\nssm-2.24\win64\nssm.exe",
  [string]$Python = "D:\MrlToolchain\python\python.exe",
  [string]$TunnelConfig = "C:\Users\Administrator\.cloudflared\config.yml",
  # Cloudflare Origin CA 憑證（儀表板 SSL/TLS › Origin Server › Create Certificate，主機名 origin.mrliouword.com）
  [string]$OriginCertPath = "D:\MRL_Edge\origin.mrliouword.com.pem",
  [string]$OriginKeyPath  = "D:\MRL_Edge\origin.mrliouword.com.key",
  [switch]$AllowInternalTls,
  [switch]$AddTunnelPathRule
)
$ErrorActionPreference = "Stop"
$MrlHome = if ($env:MRL_HOME) { $env:MRL_HOME } else { (Resolve-Path (Join-Path (Split-Path -Parent $MyInvocation.MyCommand.Path) "..\..")).Path }
$rcpt = [ordered]@{ origin_signature="MrLiouWord"; environment="實機"; at=(Get-Date).ToUniversalTime().ToString("o"); steps=@() }
function Note($k, $v) { $rcpt.steps += [ordered]@{ step=$k; result=$v }; Write-Host ("[{0}] {1}" -f $k, ($v | ConvertTo-Json -Compress -Depth 4)) }
function PortOwner([int]$p) { $c = Get-NetTCPConnection -State Listen -LocalPort $p -ErrorAction SilentlyContinue | Select-Object -First 1; if ($c) { (Get-Process -Id $c.OwningProcess -ErrorAction SilentlyContinue).ProcessName } }
if (-not (Test-Path $Nssm)) { throw "找不到 NSSM：$Nssm" }
if (-not (Test-Path $Python)) { $Python = (Get-Command python -ErrorAction Stop).Source }

# 1. MRL_Platform :7960
$svc = Get-Service MRL_Platform -ErrorAction SilentlyContinue
if (-not $svc) {
  $own = PortOwner $PlatformPort
  if ($own) { throw "埠 $PlatformPort 已被 $own 使用，請改 -PlatformPort" }
  & $Nssm install MRL_Platform $Python (Join-Path $MrlHome "MRL_Platform_Server.py") | Out-Null
  & $Nssm set MRL_Platform AppDirectory $MrlHome | Out-Null
  & $Nssm set MRL_Platform AppEnvironmentExtra "MRL_PORT=$PlatformPort" "MRL_PLATFORM_DOMAIN=mrliouword.com" "MRL_DATA_ROOT=D:\MRL_runtime" | Out-Null
  & $Nssm set MRL_Platform Start SERVICE_AUTO_START | Out-Null
  New-Item -ItemType Directory -Force -Path "D:\MRL_runtime\logs" | Out-Null
  & $Nssm set MRL_Platform AppStdout "D:\MRL_runtime\logs\MRL_Platform.out.log" | Out-Null
  & $Nssm set MRL_Platform AppStderr "D:\MRL_runtime\logs\MRL_Platform.err.log" | Out-Null
  Note "platform_service" "installed"
} else {
  # 既有服務：埠必須與 -PlatformPort 一致，否則中止（避免 Caddy 反代到錯的埠）
  $envExtra = (& $Nssm get MRL_Platform AppEnvironmentExtra) -join " "
  $m = [regex]::Match($envExtra, "MRL_PORT=(\d+)")
  $svcPort = if ($m.Success) { [int]$m.Groups[1].Value } else { 8790 }
  if ($svcPort -ne $PlatformPort) { throw "既有 MRL_Platform 服務埠為 $svcPort，與 -PlatformPort $PlatformPort 不符；請用 -PlatformPort $svcPort 重跑，或先調整服務設定。" }
  Note "platform_service" "exists:$($svc.Status):port=$svcPort"
}
Start-Service MRL_Platform -ErrorAction SilentlyContinue
Start-Sleep -Seconds 4
# 本機防火牆：7960 不對外（只給本機反代／cloudflared）
if (-not (Get-NetFirewallRule -DisplayName "MRL_Platform_Block_$PlatformPort" -ErrorAction SilentlyContinue)) {
  New-NetFirewallRule -DisplayName "MRL_Platform_Block_$PlatformPort" -Direction Inbound -Protocol TCP -LocalPort $PlatformPort -Action Block -RemoteAddress Any | Out-Null
}

# 2. Caddy HTTPS 入口
$own = PortOwner $EdgePort
if ($own -and $own -ne "caddy") { throw "埠 $EdgePort 已被 $own 使用。改用 -EdgePort 8443，並通知雲端把 MRL_DL580_ORIGIN 改為 https://${EdgeHost}:8443" }
New-Item -ItemType Directory -Force -Path $EdgeHome | Out-Null
# 憑證：預設要求 Cloudflare Origin CA（配合 Full (strict)）；只有明示 -AllowInternalTls 才用自簽
if ((Test-Path $OriginCertPath) -and (Test-Path $OriginKeyPath)) {
  $TlsLine = "tls `"$OriginCertPath`" `"$OriginKeyPath`""
  Note "tls" "origin_ca"
} elseif ($AllowInternalTls) {
  $TlsLine = "tls internal"
  Note "tls" "WARN: internal（Cloudflare 僅能用 Full，非 strict；請盡快換 Origin CA）"
} else {
  throw "找不到 Origin CA 憑證：$OriginCertPath / $OriginKeyPath。請在 Cloudflare 儀表板 SSL/TLS › Origin Server 建立 origin.mrliouword.com 憑證存到上述路徑後重跑（或暫用 -AllowInternalTls）。"
}
$caddy = Join-Path $EdgeHome "caddy.exe"
if (-not (Test-Path $caddy)) {
  curl.exe -L "https://caddyserver.com/api/download?os=windows&arch=amd64" -o $caddy
}
@"
{
  admin off
  auto_https disable_redirects
}
https://${EdgeHost}:$EdgePort {
  $TlsLine
  @api path /health /api/mother/status /api/dl580/run /api/chat /api/monitor /mrl/perceive /api/mrl/runtime/convergence /mrl/state
  handle @api {
    reverse_proxy 127.0.0.1:$PlatformPort
  }
  handle {
    respond "MRL origin: path not exposed" 404
  }
  log {
    output file D:\MRL_runtime\logs\MRL_Edge_access.log
  }
}
"@ | Out-File -FilePath (Join-Path $EdgeHome "Caddyfile") -Encoding ascii
if (-not (Get-Service MRL_Edge -ErrorAction SilentlyContinue)) {
  & $Nssm install MRL_Edge $caddy run --config (Join-Path $EdgeHome "Caddyfile") --adapter caddyfile | Out-Null
  & $Nssm set MRL_Edge AppDirectory $EdgeHome | Out-Null
  & $Nssm set MRL_Edge Start SERVICE_AUTO_START | Out-Null
  Note "edge_service" "installed"
} else { Restart-Service MRL_Edge; Note "edge_service" "restarted" }
Start-Service MRL_Edge -ErrorAction SilentlyContinue

# 3. 防火牆：EdgePort 只放 Cloudflare
$ranges = @()
try { $ranges = (Invoke-WebRequest -Uri "https://www.cloudflare.com/ips-v4" -UseBasicParsing -TimeoutSec 15).Content -split "`n" | Where-Object { $_ -match "/" } | ForEach-Object { $_.Trim() } } catch {}
if ($ranges.Count -gt 0) {
  Get-NetFirewallRule -DisplayName "MRL_Edge_Cloudflare_$EdgePort" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
  New-NetFirewallRule -DisplayName "MRL_Edge_Cloudflare_$EdgePort" -Direction Inbound -Protocol TCP -LocalPort $EdgePort -Action Allow -RemoteAddress $ranges | Out-Null
  # 不另建 Block 規則（Windows 防火牆 Block 優先於 Allow，會連 Cloudflare 一起擋）；依預設入站封鎖，只放行上列範圍。
  $other = Get-NetFirewallPortFilter -Protocol TCP -ErrorAction SilentlyContinue | Where-Object { $_.LocalPort -eq "$EdgePort" } | Get-NetFirewallRule | Where-Object { $_.Enabled -eq "True" -and $_.Direction -eq "Inbound" -and $_.Action -eq "Allow" -and $_.DisplayName -ne "MRL_Edge_Cloudflare_$EdgePort" }
  # Codex P1 修補：既有放行規則或預設入站非封鎖時中止（否則固定 IP 可繞過 Access 直連）
  $any = Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True -ErrorAction SilentlyContinue |
    Where-Object { $_.DisplayName -ne "MRL_Edge_Cloudflare_$EdgePort" } | Where-Object {
      $pf = $_ | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue
      $pf -and ($pf.Protocol -in @("TCP", "Any")) -and ($pf.LocalPort -contains "$EdgePort" -or $pf.LocalPort -contains "Any")
    } | Where-Object { ($_ | Get-NetFirewallApplicationFilter -ErrorAction SilentlyContinue).Program -in @($null, "Any") }
  $loose = @(Get-NetFirewallProfile | Where-Object { $_.Enabled -ne $true -or $_.DefaultInboundAction -notin @("Block") })
  if ($any -or $loose.Count -gt 0) {
    Note "firewall_abort" @{ other_allow_rules=@($any | ForEach-Object { $_.DisplayName }); loose_profiles=@($loose | ForEach-Object { "$($_.Name):enabled=$($_.Enabled),inbound=$($_.DefaultInboundAction)" }) }
    Get-NetFirewallRule -DisplayName "MRL_Edge_Cloudflare_$EdgePort" -ErrorAction SilentlyContinue | Remove-NetFirewallRule
    Stop-Service MRL_Edge -ErrorAction SilentlyContinue
    throw "ABORT：埠 $EdgePort 另有放行規則，或防火牆設定檔未啟用／預設入站非封鎖。已停 MRL_Edge、撤回本腳本規則。請收窄或停用上列規則後重跑；路由器先不要開 $EdgePort 轉發。"
  }
  Note "firewall" @{ allow_cloudflare_ranges=$ranges.Count }
} else {
  Stop-Service MRL_Edge -ErrorAction SilentlyContinue
  Note "firewall" "WARN: 無法取得 Cloudflare IP 清單，未開放 $EdgePort，已停 MRL_Edge（安全預設）"
}

# 4. Tunnel 備援路徑（只新增）
if ($AddTunnelPathRule) {
  if (-not (Test-Path $TunnelConfig)) { Note "tunnel_rule" "SKIP: 找不到 $TunnelConfig" }
  else {
    $txt = Get-Content $TunnelConfig -Raw
    $want = '(?ms)^\s*-\s*hostname:\s*dl580\.mrliouword\.com\s*\r?\n\s*path:\s*\^/\(api/\(mother/status\|dl580/run\|chat\|monitor\)\|mrl/perceive\)\$\s*\r?\n\s*service:\s*http://localhost:' + $PlatformPort + '\b'
    if ($txt -match $want) { Note "tunnel_rule" "exists" }
    else {
      Copy-Item $TunnelConfig ($TunnelConfig + ".bak_" + (Get-Date -Format "yyyyMMdd_HHmmss"))
      $nl = "`r`n"
      $rule = '  - hostname: dl580.mrliouword.com' + $nl + '    path: ^/(api/(mother/status|dl580/run|chat|monitor)|mrl/perceive)$' + $nl + ('    service: http://localhost:{0}' -f $PlatformPort) + $nl
      $idx = $txt.IndexOf("  - hostname: dl580.mrliouword.com")
      if ($idx -lt 0) { Note "tunnel_rule" "SKIP: config 內找不到 dl580 規則，未修改" }
      else {
        $txt.Insert($idx, $rule) | Set-Content -Path $TunnelConfig -Encoding UTF8 -NoNewline
        foreach ($n in @("MRL_Tunnel", "cloudflared")) { if (Get-Service $n -ErrorAction SilentlyContinue) { Restart-Service $n -Force } }
        Note "tunnel_rule" "added_before_dl580_rule (backup kept)"
      }
    }
  }
}

# 5. 本機驗收
Start-Sleep -Seconds 6
foreach ($u in @("http://127.0.0.1:$PlatformPort/health", "http://127.0.0.1:$PlatformPort/api/mother/status")) {
  try { $r = Invoke-WebRequest -Uri $u -UseBasicParsing -TimeoutSec 15; Note "local $u" @{ status=[int]$r.StatusCode } } catch { Note "local $u" @{ status=0; error=$_.Exception.Message } }
}
try {
  $r = curl.exe -sk --resolve "${EdgeHost}:${EdgePort}:127.0.0.1" -o NUL -w "%{http_code}" "https://${EdgeHost}:$EdgePort/health"
  Note "edge_tls_local" @{ status=$r }
} catch { Note "edge_tls_local" $_.Exception.Message }
try { $wan = (Invoke-WebRequest -Uri "https://api.ipify.org" -UseBasicParsing -TimeoutSec 10).Content.Trim(); Note "egress_ip" @{ ip=$wan; expected="220.132.58.129"; match=($wan -eq "220.132.58.129") } } catch {}
Write-Host "路由器：請確認 PPPoE 用固定 IP 帳號（*@ip.hinet.net），並設 TCP $EdgePort → 本機 LAN IP:$EdgePort 埠轉發。"

$out = "D:\MRL_runtime\receipts"; New-Item -ItemType Directory -Force -Path $out | Out-Null
$f = Join-Path $out ("MRL_Singularity_Origin_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".json")
$rcpt | ConvertTo-Json -Depth 6 | Out-File $f -Encoding utf8
Write-Host "RECEIPT -> $f"
