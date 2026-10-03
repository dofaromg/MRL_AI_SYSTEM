# MRL_Network_Receipt.ps1 — DL580 內網／公網接線收據（唯讀，不改任何設定）
# origin_signature: MrLiouWord ｜ Additive-Only
#
# 用法（DL580，系統管理員 PowerShell）：
#   powershell -ExecutionPolicy Bypass -File deploy\dl580\MRL_Network_Receipt.ps1
#   可選：-ExpectedWanIp 220.132.58.129 -ExpectedLanIp 192.168.0.162 -MrlPort 8790 -OutDir D:\MRL_runtime\receipts
#
# 只讀取、只測試：不改 IP／DHCP／防火牆／路由器／cloudflared／Tailscale。
# 輸出 JSON 收據；金鑰、token、query string 一律遮罩，不寫入收據。
# 單一路徑失敗只記錄該段，不判定整台 DL580 離線。
param(
  [string]$ExpectedWanIp = "220.132.58.129",
  [string]$ExpectedLanIp = "192.168.0.162",
  [int]$MrlPort = $(if ($env:MRL_PORT) { [int]$env:MRL_PORT } else { 7960 }),   # MRL_Platform（:8790 為 RuntimeOS，另於 known_health 探測）
  [string]$OutDir = $(if ($env:MRL_DATA_ROOT) { Join-Path $env:MRL_DATA_ROOT "receipts" } else { "D:\MRL_runtime\receipts" })
)
$ErrorActionPreference = "Continue"
$R = [ordered]@{
  origin_signature = "MrLiouWord"
  receipt = "MRL_Network_Receipt_v1"
  environment = "實機"
  host = $env:COMPUTERNAME
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
}

function Mask([string]$s) {
  if (-not $s) { return $s }
  $s = $s -replace '(?i)(key|token|secret|password|auth)=[^&\s"]+', '$1=***'
  $s = $s -replace '(?i)(Bearer\s+)[A-Za-z0-9._\-]+', '$1***'
  return $s
}
function Probe([string]$url, [string]$method = "GET", [string]$body = $null) {
  $o = [ordered]@{ url = (Mask $url); method = $method }
  try {
    $p = @{ Uri = $url; Method = $method; TimeoutSec = 12; UseBasicParsing = $true; ErrorAction = "Stop" }
    if ($body) { $p.Body = $body; $p.ContentType = "application/json" }
    $r = Invoke-WebRequest @p
    $o.status = [int]$r.StatusCode
    $o.body_head = (Mask ($r.Content.Substring(0, [Math]::Min(160, $r.Content.Length))))
  } catch {
    $resp = $_.Exception.Response
    if ($resp) { $o.status = [int]$resp.StatusCode } else { $o.status = 0 }
    $o.error = (Mask $_.Exception.Message)
  }
  return $o
}

# 1. 公網出口（WAN）
$wan = [ordered]@{ expected = $ExpectedWanIp }
foreach ($svc in @("https://api.ipify.org", "https://ifconfig.me/ip")) {
  try { $wan.egress_ip = (Invoke-WebRequest -Uri $svc -UseBasicParsing -TimeoutSec 10).Content.Trim(); $wan.source = $svc; break } catch {}
}
$wan.match = ($wan.egress_ip -eq $ExpectedWanIp)
$wan.note = "egress_ip 是 DL580 對外出口；路由器 WAN 介面位址仍須看路由器管理頁（PPPoE 帳號 *@ip.hinet.net）確認。若 egress 不符，可能撥的是浮動 IP 帳號或經其他出口（Tailscale exit node／VPN）。"
$R.wan = $wan

# 2. LAN 位址、DHCP／靜態、衝突
$lan = @()
Get-NetIPConfiguration | Where-Object { $_.IPv4Address -and $_.NetAdapter.Status -eq "Up" } | ForEach-Object {
  $ifx = $_.InterfaceIndex
  $ipif = Get-NetIPInterface -InterfaceIndex $ifx -AddressFamily IPv4 -ErrorAction SilentlyContinue
  $lan += [ordered]@{
    alias = $_.InterfaceAlias
    ipv4 = @($_.IPv4Address | ForEach-Object { "$($_.IPAddress)/$($_.PrefixLength)" })
    gateway = @($_.IPv4DefaultGateway | ForEach-Object { $_.NextHop })
    dns = @($_.DNSServer | Where-Object { $_.AddressFamily -eq 2 } | ForEach-Object { $_.ServerAddresses })
    dhcp = if ($ipif) { "$($ipif.Dhcp)" } else { $null }
    mac = $_.NetAdapter.MacAddress
  }
}
$hasExpected = $false
foreach ($l in $lan) { foreach ($a in $l.ipv4) { if ($a -like "$ExpectedLanIp/*") { $hasExpected = $true } } }
$arp = (arp -a) 2>$null | Select-String -SimpleMatch $ExpectedLanIp | ForEach-Object { $_.ToString().Trim() }
$R.lan = [ordered]@{
  expected = $ExpectedLanIp
  has_expected = $hasExpected
  interfaces = $lan
  arp_entries_for_expected = @($arp)
  note = "dhcp=Enabled 時需在路由器設 DHCP 保留（綁 mac）；dhcp=Disabled 為靜態，需確認該位址在路由器 DHCP 範圍之外，避免衝突。"
}

# 3. 監聽埠與行程（只列，不改）
$listen = Get-NetTCPConnection -State Listen -ErrorAction SilentlyContinue |
  Sort-Object LocalPort, LocalAddress -Unique | ForEach-Object {
    $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue
    [ordered]@{ address = $_.LocalAddress; port = $_.LocalPort; pid = $_.OwningProcess; process = if ($proc) { $proc.ProcessName } else { $null } }
  }
$R.listening = @($listen)
$R.listening_note = "address=0.0.0.0／:: 代表所有介面（含 LAN、Tailscale）都可連；127.0.0.1 代表只限本機。"

# 3b. 對照既有服務登錄（flow-tasks config/MRL_PORT_MAP.json，2026-07-10）：實際監聽 vs 登錄
$known = [ordered]@{
  "3000"="MRL_AI_Product_Server"; "5432"="MRL_PostgreSQL"; "6379"="mrl_redis"; "7500"="MRL_Inference";
  "7700"="MRL_ASI_Engine"; "7800"="MRL_Bridge"; "7801"="MRL_DB_Proxy"; "7810"="MRL_Agent_Orchestrator+ReasoningEngine";
  "7811"="MRL_Toolchain_Engine"; "7812"="MRL_Memory_Engine"; "7900"="MRL_FlowAgent_API"; "7950"="MRL_AI_OS(ControlPanel)";
  "8787"="MRL_FlowCoreLoop"; "8788"="MRL_ParticleGlobe+RuntimeAdapter"; "8790"="MRL_RuntimeOS_v1.4.0";
  "8799"="MRL_Write_Guard"; "20241"="MRL_Tunnel(cloudflared metrics)"
}
$reg = @()
foreach ($k in $known.Keys) {
  $hit = @($listen | Where-Object { "$($_.port)" -eq $k })
  $reg += [ordered]@{ port=[int]$k; registered=$known[$k]; listening=($hit.Count -gt 0);
    bind=@($hit | ForEach-Object { $_.address }); process=@($hit | ForEach-Object { $_.process }) }
}
$R.registry_vs_listening = $reg
# 已知健康端點（本機）
$R.known_health = @(
  (Probe "http://127.0.0.1:7800/health"),
  (Probe "http://127.0.0.1:3000/health"),
  (Probe "http://127.0.0.1:7700/health"),
  (Probe "http://127.0.0.1:8787/health"),
  (Probe "http://127.0.0.1:8790/api/mrl/health")
)

# 4. 各段入口測試：Worker 需要的 API（不只 /health）
$paths = @(
  @("GET", "/health", $null),
  @("GET", "/api/mother/status", $null),
  @("GET", "/api/monitor", $null),
  @("GET", "/api/mrl/runtime/convergence", $null),
  @("POST", "/api/chat", '{"message":"MRL network receipt ping"}'),
  @("POST", "/mrl/perceive", '{"q":"MRL network receipt ping"}')
  # /api/dl580/run 會跑 canonical 管線，收據不主動觸發；需要時另行手動驗收。
)
function Segment([string]$base) {
  $res = @()
  foreach ($p in $paths) { $res += (Probe ($base.TrimEnd("/") + $p[1]) $p[0] $p[2]) }
  return $res
}
$segments = [ordered]@{}
$segments["local_127"] = Segment "http://127.0.0.1:$MrlPort"
foreach ($l in $lan) { foreach ($a in $l.ipv4) {
  $ip = $a.Split("/")[0]
  if ($ip -like "192.168.*" -or $ip -like "10.*" -or $ip -like "172.*") { $segments["lan_$ip"] = Segment "http://${ip}:$MrlPort" }
} }

# Tailscale
$ts = [ordered]@{}
$tsExe = (Get-Command tailscale -ErrorAction SilentlyContinue).Source
if (-not $tsExe -and (Test-Path "C:\Program Files\Tailscale\tailscale.exe")) { $tsExe = "C:\Program Files\Tailscale\tailscale.exe" }
if ($tsExe) {
  $ts.ipv4 = (& $tsExe ip -4 2>$null | Select-Object -First 1)
  $ts.status_head = @((& $tsExe status 2>$null) | Select-Object -First 8)
  if ($ts.ipv4) { $segments["tailscale_$($ts.ipv4)"] = Segment "http://$($ts.ipv4):$MrlPort" }
} else { $ts.installed = $false }
$R.tailscale = $ts

# 公網：Tunnel 入口（不測固定 IP 直連埠，避免把未認證服務當成可用 API）
$segments["tunnel_bridge"] = @(Probe "https://bridge.mrliouword.com/health")
$segments["tunnel_dl580"] = @(Probe "https://dl580.mrliouword.com/health")
$R.segments = $segments

# 5. cloudflared（只讀）
$cf = [ordered]@{}
$svc = Get-Service -Name cloudflared -ErrorAction SilentlyContinue
$cf.service = if ($svc) { "$($svc.Status)" } else { "not_installed" }
$mt = Get-Service -Name MRL_Tunnel -ErrorAction SilentlyContinue
$cf.mrl_tunnel_service = if ($mt) { "$($mt.Status)" } else { "not_installed" }
$cf.processes = @(Get-Process cloudflared -ErrorAction SilentlyContinue | ForEach-Object { [ordered]@{ pid=$_.Id; started=$(try { $_.StartTime.ToString("o") } catch { $null }) } })
$cfHome = if ($env:CLOUDFLARED_HOME) { $env:CLOUDFLARED_HOME } else { "D:\cloudflared" }
foreach ($cand in @("C:\Users\Administrator\.cloudflared\config.yml", (Join-Path $cfHome "config.yml"), "C:\Windows\System32\config\systemprofile\.cloudflared\config.yml", (Join-Path $env:USERPROFILE ".cloudflared\config.yml"))) {
  if (Test-Path $cand) {
    $cf.config_path = $cand
    $cf.config = @(Get-Content $cand | Where-Object { $_ -notmatch '(?i)credentials|token|secret' } | ForEach-Object { Mask $_ })
    break
  }
}
$R.cloudflared = $cf

# 輸出
New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$file = Join-Path $OutDir ("MRL_Network_Receipt_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".json")
$R | ConvertTo-Json -Depth 8 | Out-File -FilePath $file -Encoding utf8
Write-Host "MRL_NETWORK_RECEIPT -> $file"
Write-Host ("WAN egress={0} expected={1} match={2}" -f $wan.egress_ip, $ExpectedWanIp, $wan.match)
foreach ($k in $segments.Keys) {
  $ok = @($segments[$k] | Where-Object { $_.status -ge 200 -and $_.status -lt 300 }).Count
  Write-Host ("  {0,-28} {1}/{2} 2xx" -f $k, $ok, @($segments[$k]).Count)
}
