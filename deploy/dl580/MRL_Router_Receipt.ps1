# MRL_Router_Receipt.ps1 - DL580 router-side wiring receipt (read-only; changes nothing)
# origin_signature: MrLiouWord | Additive-Only
# ASCII-only on purpose: Windows PowerShell 5.1 reads BOM-less scripts as ANSI.
#
# What it records (from DL580, without touching the router):
#   1. default gateway, gateway reachability, router admin page reachability (status code only, no login)
#   2. DL580 LAN address: DHCP vs static, lease lifetime, MAC (for the DHCP reservation)
#   3. WAN egress IP vs the expected HiNet fixed IP (PPPoE fixed-IP account check)
#   4. local prerequisites for the TCP $EdgePort forward: listener, MRL_Edge_Cloudflare_<port> firewall rule, profiles
#   5. DNS of origin host (must resolve to Cloudflare proxy, never to the bare fixed IP)
#   6. hairpin probe: DL580 -> fixed IP:$EdgePort, TCP + HTTPS(SNI) + MRL /health body (inconclusive when it fails; most home routers do not hairpin)
#   7. manual answers read from the router admin page (skip with -NoPrompt)
#
# Usage (DL580, admin PowerShell, repo root):
#   powershell -ExecutionPolicy Bypass -File deploy\dl580\MRL_Router_Receipt.ps1
#   optional: -ExpectedWanIp 220.132.58.129 -ExpectedLanIp 192.168.0.162 -EdgePort 443 -NoPrompt
param(
  [string]$ExpectedWanIp = "220.132.58.129",
  [string]$ExpectedLanIp = "192.168.0.162",
  [int]$EdgePort = 443,
  [string]$EdgeHost = "origin.mrliouword.com",
  [string]$OutDir = $(if ($env:MRL_DATA_ROOT) { Join-Path $env:MRL_DATA_ROOT "receipts" } else { "D:\MRL_runtime\receipts" }),
  [switch]$NoPrompt
)
$ErrorActionPreference = "Continue"
$R = [ordered]@{
  origin_signature = "MrLiouWord"
  receipt = "MRL_Router_Receipt_v1"
  environment = "real-host"
  host = $env:COMPUTERNAME
  generated_at = (Get-Date).ToUniversalTime().ToString("o")
  read_only = $true
}
function Mask([string]$s) {
  if (-not $s) { return $s }
  $s = $s -replace '(?i)(key|token|secret|password|auth)=[^&\s"]+', '$1=***'
  return $s
}
function InCidr([string]$ip, [string]$cidr) {
  try {
    $parts = $cidr.Split("/"); $bits = [int]$parts[1]
    $ipB = [System.Net.IPAddress]::Parse($ip).GetAddressBytes(); [Array]::Reverse($ipB)
    $nB = [System.Net.IPAddress]::Parse($parts[0]).GetAddressBytes(); [Array]::Reverse($nB)
    $ipU = [uint64][BitConverter]::ToUInt32($ipB, 0); $nU = [uint64][BitConverter]::ToUInt32($nB, 0)
    $mask = if ($bits -le 0) { [uint64]0 } else { ([uint64]0xFFFFFFFF -shl (32 - $bits)) -band [uint64]0xFFFFFFFF }
    return (($ipU -band $mask) -eq ($nU -band $mask))
  } catch { return $false }
}
function Head([string]$url) {
  $o = [ordered]@{ url = $url }
  try { $r = Invoke-WebRequest -Uri $url -UseBasicParsing -TimeoutSec 6 -ErrorAction Stop; $o.status = [int]$r.StatusCode }
  catch { $resp = $_.Exception.Response; $o.status = if ($resp) { [int]$resp.StatusCode } else { 0 }; $o.error = (Mask $_.Exception.Message) }
  return $o
}

# 1. gateway
$cfgs = Get-NetIPConfiguration | Where-Object { $_.IPv4Address -and $_.NetAdapter.Status -eq "Up" }
$gws = @($cfgs | ForEach-Object { $_.IPv4DefaultGateway } | ForEach-Object { $_.NextHop } | Select-Object -Unique)
$gw = [ordered]@{ gateways = $gws; probes = @() }
foreach ($g in $gws) {
  $p = [ordered]@{ gateway = $g }
  $p.ping_ok = (Test-Connection -ComputerName $g -Count 2 -Quiet -ErrorAction SilentlyContinue)
  $arp = (arp -a) 2>$null | Select-String -SimpleMatch $g | Select-Object -First 1
  $p.arp = if ($arp) { $arp.ToString().Trim() } else { $null }
  $p.admin_http = Head "http://$g/"
  $p.admin_https = Head "https://$g/"
  $gw.probes += $p
}
$gw.note = "admin_http/https status is only proof the router answers; no login attempted."
$R.gateway = $gw

# 2. LAN address / DHCP / MAC
$lan = @()
foreach ($c in $cfgs) {
  foreach ($a in $c.IPv4Address) {
    $ipa = Get-NetIPAddress -InterfaceIndex $c.InterfaceIndex -IPAddress $a.IPAddress -AddressFamily IPv4 -ErrorAction SilentlyContinue
    $ipif = Get-NetIPInterface -InterfaceIndex $c.InterfaceIndex -AddressFamily IPv4 -ErrorAction SilentlyContinue
    $lan += [ordered]@{
      alias = $c.InterfaceAlias
      ipv4 = "$($a.IPAddress)/$($a.PrefixLength)"
      mac = $c.NetAdapter.MacAddress
      dhcp = if ($ipif) { "$($ipif.Dhcp)" } else { $null }
      origin = if ($ipa) { "$($ipa.PrefixOrigin)/$($ipa.SuffixOrigin)" } else { $null }
      valid_lifetime = if ($ipa) { "$($ipa.ValidLifetime)" } else { $null }
      is_expected = ($a.IPAddress -eq $ExpectedLanIp)
    }
  }
}
$R.lan = [ordered]@{
  expected = $ExpectedLanIp
  has_expected = (@($lan | Where-Object { $_.is_expected }).Count -gt 0)
  interfaces = $lan
  note = "dhcp=Enabled: add a DHCP reservation on the router bound to 'mac'. dhcp=Disabled: make sure the static address is outside the router DHCP pool."
}

# 3. WAN egress vs expected fixed IP
$wan = [ordered]@{ expected = $ExpectedWanIp; probe_errors = @() }
foreach ($svc in @("https://api.ipify.org", "https://ifconfig.me/ip")) {
  try {
    $txt = (Invoke-WebRequest -Uri $svc -UseBasicParsing -TimeoutSec 10).Content.Trim()
    $parsed = $null
    if ([System.Net.IPAddress]::TryParse($txt, [ref]$parsed) -and $parsed.AddressFamily -eq "InterNetwork") { $wan.egress_ip = $txt; $wan.source = $svc; break }
    else { $wan.probe_errors += [ordered]@{ source = $svc; error = ("not an IPv4 address: " + (Mask $txt.Substring(0, [Math]::Min(60, $txt.Length)))) } }
  } catch { $wan.probe_errors += [ordered]@{ source = $svc; error = (Mask $_.Exception.Message) } }
}
# null = no evidence (probe failed); true/false only when an egress address was actually obtained
$wan.match = if ($wan.egress_ip) { ($wan.egress_ip -eq $ExpectedWanIp) } else { $null }
$wan.note = "match=false usually means PPPoE is dialed with the dynamic account instead of the fixed-IP account (*@ip.hinet.net), or traffic leaves via another path (Tailscale exit node / VPN). match=null means the probe itself failed (see probe_errors): no conclusion, do not change PPPoE on that alone."
try { $wan.tracert_head = @((tracert -d -h 3 -w 1000 8.8.8.8 2>$null) | Select-Object -Skip 1 -First 5 | ForEach-Object { $_.Trim() } | Where-Object { $_ }) } catch {}
$R.wan = $wan

# 4. local prerequisites for the port forward
$pre = [ordered]@{ edge_port = $EdgePort }
$listen = @(Get-NetTCPConnection -State Listen -LocalPort $EdgePort -ErrorAction SilentlyContinue)
$pre.listening = ($listen.Count -gt 0)
$pre.listeners = @($listen | ForEach-Object { $proc = Get-Process -Id $_.OwningProcess -ErrorAction SilentlyContinue; [ordered]@{ address = $_.LocalAddress; pid = $_.OwningProcess; process = if ($proc) { $proc.ProcessName } else { $null } } })
$rule = Get-NetFirewallRule -DisplayName "MRL_Edge_Cloudflare_$EdgePort" -ErrorAction SilentlyContinue
$pre.firewall_rule = if ($rule) { [ordered]@{ name = $rule.DisplayName; enabled = "$($rule.Enabled)"; action = "$($rule.Action)"; remote = @((Get-NetFirewallAddressFilter -AssociatedNetFirewallRule $rule -ErrorAction SilentlyContinue).RemoteAddress | Select-Object -First 5) } } else { "missing" }
# same contract as MRL_Singularity_Origin_Setup.ps1 (Codex P1): any other enabled inbound allow rule that covers
# the port (TCP or Any protocol, explicit port or Any) and is not bound to a specific program counts as broad.
$pre.other_allow_rules_on_port = @(Get-NetFirewallRule -Direction Inbound -Action Allow -Enabled True -ErrorAction SilentlyContinue |
  Where-Object { $_.DisplayName -ne "MRL_Edge_Cloudflare_$EdgePort" } | Where-Object {
    $pf = $_ | Get-NetFirewallPortFilter -ErrorAction SilentlyContinue
    $pf -and ($pf.Protocol -in @("TCP", "Any")) -and ($pf.LocalPort -contains "$EdgePort" -or $pf.LocalPort -contains "Any")
  } | Where-Object { ($_ | Get-NetFirewallApplicationFilter -ErrorAction SilentlyContinue).Program -in @($null, "Any") } |
  ForEach-Object { $_.DisplayName })
$pre.profiles = @(Get-NetFirewallProfile -ErrorAction SilentlyContinue | ForEach-Object { [ordered]@{ name = $_.Name; enabled = "$($_.Enabled)"; default_inbound = "$($_.DefaultInboundAction)" } })
$loose = @(Get-NetFirewallProfile -ErrorAction SilentlyContinue | Where-Object { $_.Enabled -ne $true -or $_.DefaultInboundAction -notin @("Block") })
$pre.loose_profiles = @($loose | ForEach-Object { "$($_.Name):enabled=$($_.Enabled),inbound=$($_.DefaultInboundAction)" })
$pre.ready_for_forward = (
  $pre.listening -and
  ($null -ne $rule) -and
  ("$($rule.Enabled)" -eq "True") -and
  ($pre.other_allow_rules_on_port.Count -eq 0) -and
  ($loose.Count -eq 0)
)
$pre.note = "Do NOT add the router port forward until ready_for_forward=true (run MRL_Singularity_Origin_Setup.ps1 first). It requires: listener on the port, MRL_Edge_Cloudflare_<port> present and enabled, no other broad allow rule on the port, every profile enabled with default inbound Block. Forwarding to an unprotected listener exposes the fixed IP."
$R.prerequisites = $pre

# 5. DNS of the origin host (must be Cloudflare proxy addresses)
$dns = [ordered]@{ host = $EdgeHost }
try { $dns.a = @((Resolve-DnsName -Name $EdgeHost -Type A -ErrorAction Stop | Where-Object { $_.IPAddress }).IPAddress) } catch { $dns.error = $_.Exception.Message }
$dns.resolves_to_bare_fixed_ip = ($dns.a -contains $ExpectedWanIp)
# positive signal: every A answer must fall inside a Cloudflare IPv4 range (same source as the setup script's firewall rule)
$cfRanges = @()
try { $cfRanges = @((Invoke-WebRequest -Uri "https://www.cloudflare.com/ips-v4" -UseBasicParsing -TimeoutSec 15).Content -split "`n" | Where-Object { $_ -match "/" } | ForEach-Object { $_.Trim() }) } catch { $dns.ranges_error = (Mask $_.Exception.Message) }
$dns.cloudflare_ranges_loaded = ($cfRanges.Count -gt 0)
if ($cfRanges.Count -gt 0 -and $dns.a) {
  $dns.a_in_cloudflare = @($dns.a | ForEach-Object { $ip = $_; [ordered]@{ ip = $ip; cloudflare = (@($cfRanges | Where-Object { InCidr $ip $_ }).Count -gt 0) } })
  $dns.all_cloudflare = (@($dns.a_in_cloudflare | Where-Object { -not $_.cloudflare }).Count -eq 0)
} else { $dns.all_cloudflare = $null }
$dns.note = "all_cloudflare=true is the positive proxy signal (every A answer inside Cloudflare IPv4 ranges); resolves_to_bare_fixed_ip must be false. all_cloudflare=null means the range list could not be loaded -> CHECK, not PASS."
$R.dns = $dns

# 6. hairpin probe (inconclusive on failure)
$hp = [ordered]@{ target = "${ExpectedWanIp}:$EdgePort"; sni = $EdgeHost }
try { $t = Test-NetConnection -ComputerName $ExpectedWanIp -Port $EdgePort -WarningAction SilentlyContinue -ErrorAction Stop; $hp.tcp_ok = $t.TcpTestSucceeded } catch { $hp.tcp_ok = $false; $hp.error = $_.Exception.Message }
# a TCP accept alone could be the router admin UI or another host: require HTTPS with SNI and the MRL /health body
$hp.http_status = 0; $hp.origin_signature_seen = $false
if ($hp.tcp_ok) {
  $curl = Get-Command curl.exe -ErrorAction SilentlyContinue
  if ($curl) {
    $tmp = Join-Path $env:TEMP ("mrl_hairpin_" + [guid]::NewGuid().ToString("n") + ".txt")
    try {
      $code = & $curl.Source -sk --max-time 15 --resolve "${EdgeHost}:${EdgePort}:${ExpectedWanIp}" -o $tmp -w "%{http_code}" "https://${EdgeHost}:${EdgePort}/health" 2>$null
      $hp.http_status = [int]"$code"
      $body = if (Test-Path $tmp) { [string](Get-Content $tmp -Raw -ErrorAction SilentlyContinue) } else { "" }
      if (-not $body) { $body = "" }
      $flat = ($body -replace "\s+", " ")
      $hp.body_head = (Mask ($flat.Substring(0, [Math]::Min(160, $flat.Length))))
      $hp.origin_signature_seen = ($body -match "MrLiouWord")
    } catch { $hp.http_error = (Mask $_.Exception.Message) }
    finally { Remove-Item $tmp -ErrorAction SilentlyContinue }
  } else { $hp.http_error = "curl.exe not found" }
}
$hp.verified = [bool]($hp.tcp_ok -and ($wan.match -eq $true) -and ($hp.http_status -eq 200) -and $hp.origin_signature_seen)
$hp.note = "verified=true proves the forward end to end: TCP accepted, HTTPS with SNI answered 200, body carries origin_signature MrLiouWord, and WAN egress matches the fixed IP. tcp_ok alone is NOT proof. tcp_ok=false is INCONCLUSIVE from inside the LAN (no NAT hairpin); verify from outside instead (see runbook)."
$R.hairpin = $hp

# 7. manual answers from the router admin page
if (-not $NoPrompt) {
  Write-Host ""
  Write-Host "Router admin page - answer from what you SEE (y / n / ? for unknown). Nothing is changed."
  $m = [ordered]@{}
  $m.router_model        = Read-Host "Router model / firmware"
  $m.pppoe_account_fixed = Read-Host "PPPoE account ends with @ip.hinet.net (fixed IP)? [y/n/?]"
  $m.wan_ip_on_router    = Read-Host "WAN IP shown on the router status page"
  $m.dhcp_reservation    = Read-Host "DHCP reservation for DL580 MAC -> $ExpectedLanIp present? [y/n/?]"
  $m.forward_rule        = Read-Host "Port forward TCP $EdgePort -> ${ExpectedLanIp}:$EdgePort present? [y/n/?]"
  $m.other_forwards      = Read-Host "Any OTHER port forwards / DMZ / UPnP to DL580? [y/n/?]"
  $m.wan_ip_match        = ($m.wan_ip_on_router -eq $ExpectedWanIp)
  $R.manual = $m
} else { $R.manual = "skipped (-NoPrompt)" }

# verdict (hints only; the receipt is the evidence)
$v = [ordered]@{}
$v.wan_fixed_ip      = if ($wan.match -eq $true) { "PASS" } elseif ($wan.match -eq $false) { "FAIL: egress $($wan.egress_ip) != $ExpectedWanIp" } else { "UNKNOWN: no egress address obtained (see wan.probe_errors); not a mismatch, do not change PPPoE on this alone" }
$v.lan_expected      = if ($R.lan.has_expected) { "PASS" } else { "FAIL: $ExpectedLanIp not on any up interface" }
$v.forward_prereq    = if ($pre.ready_for_forward) { "PASS" } else { "PENDING: listener/firewall not ready (rule=" + $(if ($null -ne $rule) { "$($rule.Enabled)" } else { "missing" }) + ", other_allow=" + $pre.other_allow_rules_on_port.Count + ", loose_profiles=" + $loose.Count + "); do not forward yet" }
$v.dns_proxied       = if ($dns.resolves_to_bare_fixed_ip) { "FAIL: $EdgeHost resolves to the bare fixed IP (orange cloud off)" } elseif ($dns.a -and $dns.all_cloudflare -eq $true) { "PASS" } else { "CHECK: answers=$($dns.a -join ',') cloudflare_ranges_loaded=$($dns.cloudflare_ranges_loaded)" }
$v.hairpin           = if ($hp.verified) { "PASS" } elseif ($hp.tcp_ok) { "CHECK: TCP accepted but not verified (http=$($hp.http_status), signature=$($hp.origin_signature_seen), wan_match=$($wan.match)); something else may own the port" } else { "INCONCLUSIVE (verify from outside)" }
$R.verdict = $v

New-Item -ItemType Directory -Force -Path $OutDir | Out-Null
$file = Join-Path $OutDir ("MRL_Router_Receipt_" + (Get-Date -Format "yyyyMMdd_HHmmss") + ".json")
$R | ConvertTo-Json -Depth 8 | Out-File -FilePath $file -Encoding utf8
Write-Host ""
Write-Host "MRL_ROUTER_RECEIPT -> $file"
foreach ($k in $v.Keys) { Write-Host ("  {0,-16} {1}" -f $k, $v[$k]) }
