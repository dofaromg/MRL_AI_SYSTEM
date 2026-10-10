# MRL LocalAI Recovery — 2026-10-10

- origin_signature: `MrLiouWord`
- disposition: `SUPPLEMENT_EXISTING / Verify → Backfill / APPEND_ONLY`
- source baseline: `d7c848189ac97f5a5de9613c796d3bcf037338b6` on `MRL_AI_SYSTEM/memory-system-rules-prep`.
- preserved recovery source: `MrliouAI@3c51612c2ddee1b3c561882c20474694dc497792`.
- runtime target: existing DL580, `WIN-PBVUI7VK2A6`, Windows, local fixed `D:\`.

## 1. What this change delivers

This is a source recovery and verification supplement to the existing MRL carrier/adapter. It does not define a new MRL mother, replace an existing runtime, or assert operational completion from a source test.

1. Restore the original MetaCode core and its matching original usage file at their original root filenames. Preserve the July export with its original filename. The reconstructed July core remains untouched on `MrliouAI`.
2. Restore the original MCP v1 dependency closure byte-for-byte; add v2 real Streamable HTTP and legacy HTTP/SSE transport without editing v1.
3. Add a DL580-only launcher with the actual `mrl_recovery_identity` tool, an official Python SDK client, and explicit receipt gates.
4. Restore both MetaEnv specification versions and the existing README. Add a read-only dependency probe and a verified Qdrant Windows staging script.
5. Add local process/task/health/auth/file-evidence validation and a safe public Bridge metadata wrapper.
6. Add scoped CI, the expected file manifest, and contemporaneous evidence. CI executes on a cloud runner; DL580 acceptance remains separately recorded.

All files in this change are additions relative to the exact baseline. No historical source is overwritten. No existing service, task, database, Bridge key, production route, or inference process is changed by creating this branch.

## 2. Exact MetaCode lineage

| Artifact | Source | Bytes | SHA-256 |
|---|---|---:|---|
| `metacode_core.js` | `dofaromg/flow-tasks`, first path commit `f4d7637a6a66fa0256508dd6759dc23efdae689d`, 2026-01-27T05:30:23Z | 15198 | `ae5da0117f32f9795a99d5e5774fa38e5f5314cacbd7e289eaa9b440bd6fa158` |
| `metacode_usage.js` | `flow-tasks/MRL_Mother/root_sources/metacode_usage.js`; identical to `MrliouAI` root usage | 14901 | `ee51df5d38dc914a947b6e3809e0e97969f90eedc844c23d05c36ae8409d6da8` |
| `data/MetaCode.export.2026-07-08.json` | unchanged historical `MrliouAI` export | 10846 | `68ed436faff00aee1458c73ba71b08ca18d6ab20ede9951a4f4dbf9829ff8bea` |

The original core is version `2.0.0-alpha`, with 592 newline characters (593 split lines), and is byte-identical at the current inspected `flow-tasks` ref `cb73e661a02eeb540db02398cb61eaa51c5e77e3`. Original source and later reconstruction are distinct provenance records. The historical export is preserved evidence; it is not relabeled as output of the newly recovered original core.

`data/.gitignore` ignores future `MetaCode.export.*.json` exports while retaining the named 2026-07-08 evidence. The smoke test runs the original seven usage scenarios with an in-memory filesystem by default. Only its explicit, guarded DL580 output mode writes the original five exports and a receipt into a new run directory.

```powershell
& 'D:\MrlToolchain\node\node.exe' --experimental-vm-modules scripts\MRL_metacode_recovery_smoke_v1.mjs --output-dir D:\MRL_Mother\EvidenceChain\MetaCode
```

## 3. Source package acceptance

`MRL_LocalAI_Recovery_Manifest_v1.json` defines `expected_file_list`, per-payload byte count/SHA-256/Git blob SHA, source lineage and the dependency graph. Its `files` array excludes the manifest itself to avoid a circular self-hash. The full expected list includes the manifest; its own Git blob identity is verified by the final Git tree/readback audit. Coverage refers to this explicitly scoped change, not every historical MRL file.

Before any DL580 execution, verify all manifest payloads against the exact recovery commit and confirm the checkout resolves to local `D:\`. Do not use a mutable branch name as the final provenance identifier. Do not run the older recovery script that prints/rotates credentials. Do not use the existing Linux/systemd deployment workflow as a Windows deployment procedure.

Preserve the existing DL580 `AGENTS.md` and local write-guard rules. Source package deployment, Python environments, pip caches, temporary files, outputs and evidence remain on `D:\`. Do not export DL580 file contents to the cloud. Return only the necessary status, counts, byte sizes, hashes and receipt references.

## 4. Read-only DL580 acceptance

The existing node target is `D:\MrlToolchain\node\node.exe` with entry `D:\mrl\asi-engine\server.js`. Expected tasks are `MRL_ASI_Engine` and `MRL_Watchdog`. These are expected identities from existing records, not a claim that the current process/task has been verified.

Use the existing Python 3.12 executable on D: or a new isolated D: virtual environment. `D:\MrlToolchain\python\python.exe` is the launcher's default parameter and must be checked on the actual host; it is not an asserted discovery.

```powershell
.\deploy\dl580\MRL_LocalAI_Recovery_Validate.ps1 -PythonExe 'D:\path\to\existing\python.exe'
```

The validator checks source hashes, Windows CIM boot time, 7700 owning process identity, exact task/action configuration, local ASI and Bridge response identity, and authenticated Bridge identity when the existing `MRL_BRIDGE_API_KEY` is configured in the process environment. It does not print that key. Anonymous access must be rejected. A retired key is tested only if separately provided as `MRL_BRIDGE_RETIRED_API_KEY`.

An existing task is not watchdog fault-recovery proof. A Bridge `boot_time` is not the Windows boot time. Reboot continuity requires a valid earlier local receipt and strictly later Windows boot evidence plus current checks; no reboot is triggered by this validator. It does not claim global credential-residue clearance or a real OAuth session.

```powershell
.\deploy\dl580\MRL_LocalAI_Recovery_Validate.ps1 -PythonExe 'D:\path\to\existing\python.exe' -PreviousReceipt 'D:\MRL_Mother\EvidenceChain\_reports\previous-actual-receipt.json'
```

Receipt writes are exclusive and confined to local D:. A non-PASS check produces an incomplete result and nonzero exit. Preserve that receipt; do not turn an incomplete check into PASS by omitting a prerequisite.

## 5. Official MCP SDK acceptance on DL580

Transport source: `09_workflow/MRL_MCPServerHarness_Streamable_v2.py`. MRL launcher: `scripts/MRL_localai_mcp_server_v1.py`. Client: `scripts/MRL_mcp_sdk_acceptance_v1.py`.

| Route | Behavior |
|---|---|
| `POST /mcp` | Stateless Streamable HTTP JSON-RPC; notifications return 202 |
| `GET /mcp` | 405; this server does not offer a long-lived modern GET stream |
| `GET /sse` | Legacy SSE endpoint event and subsequent message events |
| `POST /messages?session_id=...` | Posts into the allocated SSE session |

The server applies Host/Origin validation, bounded connections/sessions/queues/body sizes and backpressure before a tool side effect. It reuses existing v1 ToolLoop/PolicyGate/registry code. Binding beyond loopback requires an existing MCP key.

The official client pins `mcp==1.30.0` and `httpx==0.28.1`. These are direct dependency pins, not a complete transitive lock. Record the actually installed environment on D:. The client uses the official `ClientSession`, `streamable_http_client` and `sse_client`; no mock SDK substitutes for acceptance.

### Isolated dependency setup

Use a new, nonexisting run directory under D:. Configure `TEMP`, `TMP`, `PIP_CACHE_DIR` and `PYTHONPYCACHEPREFIX` there before venv/pip operations. Do not change the production inference environment. Example after selecting the verified local source and Python paths:

```powershell
$Source = 'D:\MRL_Mother\Recovery\LocalAI_20261010'
$BootstrapPython = 'D:\path\to\existing\python312.exe'
$Run = 'D:\MRL_Mother\EvidenceChain\_reports\mcp-' + [guid]::NewGuid().ToString('N')
if (Test-Path -LiteralPath $Run) { throw 'Run directory already exists' }
New-Item -ItemType Directory -Path $Run | Out-Null
$env:TEMP = Join-Path $Run 'tmp'
$env:TMP = $env:TEMP
$env:PIP_CACHE_DIR = Join-Path $Run 'pip-cache'
$env:PYTHONPYCACHEPREFIX = Join-Path $Run 'pycache'
New-Item -ItemType Directory -Path $env:TEMP,$env:PIP_CACHE_DIR,$env:PYTHONPYCACHEPREFIX | Out-Null
& $BootstrapPython -B -m venv (Join-Path $Run 'venv')
if ($LASTEXITCODE -ne 0) { throw 'venv failed' }
$Python = Join-Path $Run 'venv\Scripts\python.exe'
& $Python -B -m pip install --disable-pip-version-check -r (Join-Path $Source 'deploy\dl580\recovery\requirements-mcp-sdk.txt')
if ($LASTEXITCODE -ne 0) { throw 'SDK installation failed' }
& $Python -B -m pip freeze | Set-Content -LiteralPath (Join-Path $Run 'installed-python.txt') -Encoding UTF8
Set-Location -LiteralPath $Source
```

### Start one isolated test endpoint and exercise both transports

Select a free loopback port and use a separate ephemeral MCP test key. Do not reuse or rotate the production Bridge key. The child server inherits this process environment. The following scope is only the child created here; it does not touch 7700/7800 or any existing inference process.

```powershell
$Port = 8765
if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue) { throw 'Select a free test port' }
$env:MRL_MCP_API_KEY = [guid]::NewGuid().ToString('N') + [guid]::NewGuid().ToString('N')
$ServerScript = Join-Path $Source 'scripts\MRL_localai_mcp_server_v1.py'
$Server = Start-Process -FilePath $Python -ArgumentList @('-B', ('"' + $ServerScript + '"'), '--port', $Port) -WorkingDirectory $Source -PassThru
try {
  $Ready = $false
  for ($i=0; $i -lt 20; $i++) {
    if ($Server.HasExited) { throw 'MRL test server exited during preflight' }
    if (Get-NetTCPConnection -State Listen -LocalPort $Port -ErrorAction SilentlyContinue | Where-Object OwningProcess -eq $Server.Id) { $Ready=$true; break }
    Start-Sleep -Milliseconds 250
  }
  if (-not $Ready) { throw 'MRL test server readiness timed out' }
  foreach ($Transport in @('streamable-http','sse')) {
    $Route = if ($Transport -eq 'sse') { 'sse' } else { 'mcp' }
    $env:MRL_MCP_ENDPOINT = "http://127.0.0.1:$Port/$Route"
    foreach ($Tool in @('echo','mrl_recovery_identity')) {
      $Out = Join-Path $Run ($Transport + '-' + $Tool + '.json')
      & $Python -B scripts\MRL_mcp_sdk_acceptance_v1.py --transport $Transport --tool $Tool --expected-client-host WIN-PBVUI7VK2A6 --out $Out
      if ($LASTEXITCODE -ne 0) { throw ('MCP acceptance failed: ' + $Transport + '/' + $Tool) }
    }
  }
} finally {
  if ($Server -and -not $Server.HasExited) { $Server.Kill(); $null = $Server.WaitForExit(5000) }
  Remove-Item Env:MRL_MCP_API_KEY -ErrorAction SilentlyContinue
}
```

`echo` is auxiliary transport evidence. The MRL identity tool accepts only `{}` and reads only the two fixed original MetaCode files. It verifies size, SHA-256, Git blob and original source lineage on the actual Windows D: host. `runtime_operational` deliberately remains `NOT_ASSERTED`; source integrity does not demonstrate model inference or full world-model behavior.

Four successful receipts are needed for both transports and both tools. Check that each client session initialized, listed the expected tool, called it, validated the response, and closed the transport cleanly. The SDK default without `--tool` validates only handshake/catalog and must not be presented as a tool-call PASS.

## 6. Dependencies

### Qdrant

Official source: [Qdrant v1.19.2](https://github.com/qdrant/qdrant/releases/tag/v1.19.2), published 2026-10-05. Windows asset ID `612861224`, `qdrant-x86_64-pc-windows-msvc.zip`, 30,243,552 bytes, SHA-256 `7d86596f16c6e85d45a50312f5e16ccb51e059b62e3d7308110cb65b4c799a4d`.

```powershell
.\deploy\dl580\recovery\MRL_Qdrant_Stage_v1.ps1 -ExpectedClientHost WIN-PBVUI7VK2A6
```

This creates a new D: staging directory, verifies the archive, rejects unsafe ZIP entries/reparse paths, extracts exclusively and hashes the results. It does not launch Qdrant, create a Windows service or replace existing storage. Native Windows compatibility on this DL580, authenticated collection access and temporary collection create/query/delete remain actual-host gates.

### MinIO

[The official MinIO repository](https://github.com/minio/minio) currently states that this repository is no longer maintained and describes community distribution as source-only. The inspected latest release is `RELEASE.2025-10-15T17-29-55Z`, without downloadable release assets. Do not call an old binary a current maintained build. This supplement probes an existing MinIO service; it does not silently install an unmaintained build or choose another provider.

MinIO write/read/delete acceptance requires the existing endpoint, bucket policy, scoped credential and a uniquely named test object. A live/ready HTTP 200 alone does not prove object storage read/write.

### MetaEnv

The original and repaired YAML files are both restored. The original retains its recorded parse defect; the repaired specification parses with nine paths. That known original parse error is historical evidence, not a reason to rewrite the original file. The existing README describes a specification-only state and is preserved verbatim.

The probe uses the actual contract `GET /api/v1/env/health`, checks its response shape, and leaves canonical service identity unverified because that contract provides no identity assertion. Do not assume the recorded `localhost:8000` is MetaEnv; inspect the current owning process and use the actual configured endpoint.

### Read-only dependency probe

Configure only the existing verified endpoints in the local session: `MRL_QDRANT_URL`, optional `MRL_QDRANT_API_KEY`, `MRL_MINIO_URL`, `MRL_METAENV_URL`. Credentials are supplied in headers, never URLs or command arguments. Non-loopback endpoints require HTTPS and redirects are refused.

```powershell
& $Python -B scripts\MRL_recovery_dependency_probe_v1.py --expected-client-host WIN-PBVUI7VK2A6 --out (Join-Path $Run 'dependencies.json')
```

Missing configuration is UNVERIFIED, not PASS. Qdrant collection enumeration is read-only and omits names. MinIO health is not storage R/W. MetaEnv health is not completion of its nine controls.

## 7. Bridge and website observations

At 2026-10-10T17:03:36Z, the public Bridge health endpoint responded HTTP 200 with `MRL_Bridge_API`, version `3.1.0`, `MrLiouWord` and api/pg/redis all true. At 17:18:00Z, the same truthful MRL API client received HTTP 401 JSON from anonymous `/MRL_sysinfo`. This establishes public reachability and anonymous rejection, not authenticated management or global credential hygiene.

The initial default urllib user agent received Cloudflare error 1010; a truthful `MRL-Recovery-Validator/1.0` API user agent with `Accept: application/json` reached the existing route. No WAF, DNS or security configuration was changed.

The current connection has no usable existing Bridge management key and no callable DL580 remote management connector. Consequently, this change has not executed authenticated DL580 commands or written DL580 files. This is an access prerequisite, not a finding that DL580 is offline, and not a request for repeated owner authorization.

The observed public website routes `/`, `/login`, `/auth/login` and `/api/auth/session` all returned the same 12,430-byte HTML with SHA-256 `0696ec6899ac98a15b0fd5c38adf3dd0d415d31d1f615285eda29ad85a1d8332`. Browser inspection showed the public MrLiouWord v1.3.0 chat surface, including at `/login`, without an actual sign-in form. A catchall HTML 200 does not prove an OAuth callback or authenticated session.

Deployment completion therefore requires the actual production source commit, Worker/deployment identity, OAuth provider and registered callback, followed by a real user-owned browser login and session verification. The currently connected Vercel query returned no project for the exact MRL_AI_SYSTEM repository; that limited account result does not establish that no deployment exists elsewhere.

## 8. Completion gates and backfill

| Gate | Required evidence |
|---|---|
| Source delivery | Exact expected paths, all nonempty, size/hash/Git blob readback, dependency closure, actual commit and PR |
| CI engineering | Real official SDK HTTP/SSE echo runs, native source smoke and scoped regressions on the named cloud runner |
| DL580 source/identity | Actual D: source manifest, native MetaCode output receipts, Windows-host MRL identity calls |
| ASI startup/recovery | Current owned 7700 listener, real task actions, Windows boot evidence and a bounded verified watchdog recovery event |
| Bridge credential lifecycle | Authenticated identity, retired-key rejection where applicable, scoped residue review; no raw credentials in evidence |
| Dependencies | Actual configured endpoints, then separately scoped storage/control operations and cleanup receipts |
| OAuth/deployment | Actual production-source mapping, provider/callback and real signed-in session |

Append actual results to the existing MRL mother record with UTC time, environment, source commit, receipt path/hash and status. Preserve earlier observations. A source or CI PASS never changes a pending DL580/runtime gate by implication. Do not mark the whole recovery complete while these actual-host gates remain open.
