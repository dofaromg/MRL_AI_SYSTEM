# PR #155 Windows deployment preparation — R03

origin_signature: MrLiouWord
record_mode: APPEND_ONLY

## Fixed change and actual result

Parent commit: `5fe2f1f64e32ba329830c9a3eb9fd762de6c0119`.
The frozen 33-file recovery package and all R02 files are unchanged.
R03 adds a v3 CRUD client. Only the collection DELETE socket wait changes from
12 to 60 seconds; collection creation remains 60 seconds, other requests 12,
and every request remains capped by the remaining 180-second request budget.
This is a request budget, not a wall-clock bound for process/task guards.
Ownership, acknowledged-create-only cleanup, permanent owner-failure latch,
and no retry after an ambiguous DELETE remain unchanged.

Actual DL580 result: **DURABLE_SYNTHETIC_CRUD_PASS**. The fresh synthetic
collection returned GET 404, create 200, point write 200, exact readback 200,
DELETE ACK 200, final GET 404. All ten before/after ownership/source/auth
gates passed. No service-control operation was performed.
This closes the new single-client API CRUD acceptance; it does not rewrite
the earlier v1/v2 HOLD receipts or prove physical deletion of their storage.

Twelve fixtures passed on actual DL580 Python. The first runner used
`python -m unittest` and could not find the test module in this Python's
search path. It stopped before live CRUD. The second used the absolute test
file path; its successful fixture and actual-host receipts remain separate.
Use the absolute-file invocation below on this host.

## Existing deployed state and concrete next steps

| Component | Prepared action | Release condition | Recovery/backout |
| --- | --- | --- | --- |
| Recovery source | Keep `D:\MRL_Mother\Recovery\LocalAI_20261010_v2` pinned to be2f1d63; verify 33 files and manifest blob | Existing source remains 33/33 | Keep prior source directories; no in-place overwrite |
| Qdrant service | Reuse existing private instance; retain v3 as the acceptance tool | New v3 API CRUD receipt PASS; service verify remains PASS | No service change is needed for this client fix; stop using the candidate client to revert tooling |
| PR merge | Review and merge into current PR base `MRL_AI_SYSTEM/memory-system-rules-prep`, fixed base d7c848189ac97f5a5de9613c796d3bcf037338b6 | New R03 CI green, unchanged frozen payload, owner review of exact head and remaining production holds | Revert the R03 additive commit if needed, preserving its history; no force push |
| MCP persistent endpoint | Stage from verified recovery source using an isolated D: SDK environment; choose loopback binding, unused port, private credential and exact task identity before activation | Existing four SDK receipts cover isolated transport acceptance only; persistent task/boot/auth/consumer evidence still required | Stop/disable only a newly identified MCP task; retain source/environment/receipts |
| Watchdog | Preserve running v3 task and ASI source; investigate relative Node launch origin | Current cwd/source observation does not prove original launch cwd; no recovery bypass or fault injection yet | Preserve exported current task definition and existing helper before a later approved task update |
| Qdrant application wiring | Identify the actual existing consumer/config and add scoped local access | Consumer integration read/write receipt required | Restore exact previous consumer config; retain database |
| MetaEnv | Implement against preserved nine-path contract after mapping current owner/source | 7870 general health is not /api/v1/env/health; previous 404 remains open | Separate staged adapter; no replacement of current Bridge on health alone |
| MinIO/S3 | Reuse verified existing endpoint and scoped bucket credential, or select an installable deployment source | Endpoint/bucket and unique-object write/read/delete receipt required | Only delete acknowledged owned test object |
| OAuth/credential lifecycle | Map actual deployment, provider, callback, user session and retirement scope | Real login/session/logout and explicit retired-key rejection evidence | Preserve known-working provider/config/key until replacement acceptance |

The existing `.github/workflows/MRL_DL580_selfhosted_deploy.yml` targets
Linux/bash/systemd and push to `main`. It is not the Windows procedure.
The current PR base is not the literal `main` branch. R03 neither retargets
the PR nor enables that workflow as a Windows deployment mechanism.
A source merge and complete production recovery remain separate gates.

## Exact local candidate

Candidate directory:
`D:\MRL_Mother\Recovery\_operations\LocalAI_20261011_R03_360369fc0d594d4c9e70345a814cbe86`

```powershell
$Python = 'D:\MrlToolchain\python\python.exe'
$Candidate = 'D:\MRL_Mother\Recovery\_operations\LocalAI_20261011_R03_360369fc0d594d4c9e70345a814cbe86'
& $Python -B (Join-Path $Candidate 'test_MRL_qdrant_durable_crud_v3.py') -v
```

The live v3 test already passed; do not repeat it merely to recreate evidence.
Its complete receipt is retained at:
`D:\MRL_Mother\QdrantLocal\2d38cbbc0b4d4988a19f100c7b9f2d7d\state\durable_crud_4cb2bdb030bd4532a22a17a52eab32ff.json`

SHA-256: `4789aa2a2453a573ef6a215b1d4116fad0b7bcda6ecaf98541fd974fd2d9f292`, 3122 bytes.

The separate runner acceptance receipt is:
`D:\MRL_Mother\Recovery\_operations\LocalAI_20261011_R03_360369fc0d594d4c9e70345a814cbe86\attempt2_candidate_acceptance.json`

SHA-256: `835c90c85e9c6d591bcd131e9e658c5bfaff5ed92bae8cd3fbb6f3918542d02a`, 2206 bytes.

A read-only 3050 process observation is retained in the same candidate
directory as `process_3050_identity.json`: 919 bytes, SHA-256
`cc630187f100ea05bf616bdd0cac16a3cccd4587229e25cf9d36c24d2d675b65`.
The source resolved against the observed current cwd differs from ASI
(SHA-256 `e4b2b204773420f95e12f49837a9a3725da78a8e26ce348ea166e63b35c2b8a3`).
No raw command line, cwd, source body, key, data or log is included here.
This observation does not authorize ignoring that process during recovery.

## Remaining full-production gates

Watchdog fault recovery; Windows reboot continuity; Qdrant restart execution;
application-to-Qdrant integration; physical cleanup of historical uncertain
collections; MinIO/S3 operations; complete MetaEnv controller; production OAuth
and credential retirement remain unverified. Overall production is INCOMPLETE.
No reboot, production restart, task rewrite, formal MCP endpoint activation,
credential rotation, or PR merge was performed by R03 preparation.
