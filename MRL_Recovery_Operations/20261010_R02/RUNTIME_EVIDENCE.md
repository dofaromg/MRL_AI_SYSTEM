origin_signature: MrLiouWord

> This file retains the historical 18:42:48 checkpoint below. Current actual-host results are in sections 7–13; the latest metadata cutoff is 2026-10-10T19:53:07.982984+00:00.

# Recovery operations evidence — 2026-10-10 R02

**Record:** `MRL_Recovery_Operations_20261010_R02`  
**Evidence cutoff:** 2026-10-10 18:42:48 UTC  
**Overall status:** `INCOMPLETE`; the scoped successes below do not establish production deployment, watchdog fault recovery or reboot continuity.

This append-only addendum contains cloud-authored text based on immutable GitHub evidence and controller-supplied DL580 metadata. It reproduces no DL580 source-file bodies, credential values or raw process command lines. Later results belong in a new dated continuation.

## 1. Frozen package and cloud CI

The recovery payload remains the 33-path package at commit `be2f1d63ed355bb972241cc0db4eeecceeb0f04d`, based on `d7c848189ac97f5a5de9613c796d3bcf037338b6`. Its manifest contains 32 hashed payloads and excludes its own hash. This operations document is outside that payload; it does not change the frozen manifest or replace earlier evidence.

| Evidence | Verified value |
| --- | --- |
| PR | [MRL_AI_SYSTEM #155](https://github.com/dofaromg/MRL_AI_SYSTEM/pull/155), open at the cutoff; 33 changed files before this addendum |
| Frozen manifest | `deploy/dl580/recovery/MRL_LocalAI_Recovery_Manifest_v1.json`; Git blob `b35d3d62d2e141043a351d63337b73089b2fa96a` |
| Exact-head CI | [Run 38074221472](https://github.com/dofaromg/MRL_AI_SYSTEM/actions/runs/38074221472), `success`; 18:03:11–18:03:34 UTC |
| Cloud checks | 81 scoped regression tests; official SDK HTTP and SSE echo checks; original MetaCode smoke; two PowerShell parser checks. All passed. These are cloud-runner results. |

## 2. Actual DL580 source, MetaCode and MCP evidence

These earlier actual-host results are bound to source commit `3355126839ffe92149d5944865f7f1c39daa2e36`; they are not relabelled as execution of the later `be2f1d63...` revision.

- Host: `WIN-PBVUI7VK2A6`; isolated D: source and Python environment; Python 3.12.2, Node 20.11.1 and Windows PowerShell 5.1.
- Source verification: 33 expected and 33 matched files; missing, extra and mismatched counts were all zero. Receipt: 9,843 B, SHA-256 `354a3feda21791a58626e04b5baaf0bf6746f43f8d7779c072655dec2c0a8183`.
- Original MetaCode native run: `PASS`, with five outputs retained locally. Core: 15,198 B, SHA-256 `ae5da0117f32f9795a99d5e5774fa38e5f5314cacbd7e289eaa9b440bd6fa158`; usage: 14,901 B, SHA-256 `ee51df5d38dc914a947b6e3809e0e97969f90eedc844c23d05c36ae8409d6da8`.
- Official MCP SDK 1.30.0 / httpx 0.28.1: four actual-host runs passed during 17:51:59–17:52:17 UTC—Streamable HTTP and SSE, each with `echo` and `mrl_recovery_identity`; eight checks per run.
- Actual Windows PowerShell 5.1 parsed both recovery scripts successfully.
- Aggregate receipt: 12,962 B, SHA-256 `04457edf60c9cecc73dcfb5078b020cfbfa726625f945c39631c5ac56010fb11`; scoped runtime acceptance `PASS`, overall recovery `INCOMPLETE`.

Source: [immutable R01 evidence and its continuations](https://github.com/dofaromg/MRL_AI_SYSTEM/blob/be2f1d63ed355bb972241cc0db4eeecceeb0f04d/docs/recovery/MRL_LocalAI_Recovery_20261010_Evidence.json).

## 3. Existing ASI and original Watchdog preserved

| Item | Metadata and disposition |
| --- | --- |
| Existing ASI entry | `D:\mrl\asi-engine\server.js`; 355 B; SHA-256 `4dfd3194b7519efb6eef7236024a3953d2dd8842c9dc38c52ec71c6c0c807f5e`; port 7700 owner PID 13968 preserved. The different 934 B cloud reference was not copied over it. |
| Original Watchdog | `D:\mrl\MRL_Watchdog.py`; 1,787 B; SHA-256 `2c327ed594594425a7a58d2082abc624a22531f7011d446dd2bd999172eff846`; original bytes and scheduled-task arguments preserved. |
| Single-byte syntax candidate | 1,788 B; SHA-256 `52b4d3053f592f703f5ed4deadefc15b41a5a842e7763566b9c5206481c199f8`; only insertion is byte `0x5c` at original byte offset 1605. All other bytes remain identical; 47 LF retained. AST parse and compile passed. |
| Activation decision | `SYNTAX_REPAIRED_CANDIDATE`; not activated. Original configured targets are 7600 and 7800, with a bare exception handler; they do not provide the required current 7500/7700 monitoring coverage. `STATIC_TARGET_MISMATCH` remains the activation blocker. |

The candidate does not claim semantic equivalence or working fault recovery. Its cloud-authored validation helper is Git blob `7570945dcaea7190ba88175de234192f17c4da6d`, 12,786 B, SHA-256 `bd5e5d2774dad9468bd766221a96bcb3af86dc68432a82e98559c82403839c12`. The helper's eight synthetic gates passed without executing the Watchdog. Candidate persistence and its AST-outside-line gate require their own actual-host receipt; the helper's existence alone is not that receipt.

## 4. Qdrant native staging and scoped CRUD

The official [Qdrant v1.19.2 Windows x86_64 MSVC archive](https://github.com/qdrant/qdrant/releases/download/v1.19.2/qdrant-x86_64-pc-windows-msvc.zip) was staged with the fixed archive identity.

| Artifact | Size / SHA-256 |
| --- | --- |
| Official ZIP | 30,243,552 B; `7d86596f16c6e85d45a50312f5e16ccb51e059b62e3d7308110cb65b4c799a4d` |
| Extracted executable | `b25bcc612583333289b00754907639ee97cd28b8741d50f1b4ce0e2bd1ad12eb` |
| Stage receipt | 1,510 B; `c189ddf999bc975ab39c26073244519981b463eb246394411b70dc9ed9a54860` |
| v3 CRUD receipt | 7,860 B; `affc8a298f54746c269be66f61933106d51bd181531afa107ac129ff4f78b278` |

Stage receipt locator: `D:\MRL_Mother\Dependencies\Qdrant\qdrant-v1.19.2-20261010T181319Z-ab918a38546e45e8b8ad2a036fc91caa\stage-receipt.json`.

| Trial | Actual observation |
| --- | --- |
| v1, JSON configuration | Failed to establish the expected listener. No storage PASS recorded. |
| v2, YAML configuration | Authentication and loopback checks passed. Storage operations returned HTTP 500 / OS error 3. Observed deepest path length was 258; `LongPathsEnabled` was 0. These are recorded observations, not proof of a universal Qdrant limitation. |
| v3, shorter D: path | All 12 scoped CRUD checks passed during 18:36:15–18:36:24 UTC. The owned process was PID 52228; it was stopped after the test, and port 6333 was clear. |

`QDRANT_SCOPED_CRUD = PASS`; a persistent Qdrant service, automatic startup and reboot recovery are not established by this bounded test.

## 5. Current watchdog v2 checkpoint

The separate watchdog v2 effort has **23 mocked tests passing on Windows**. Its latest actual read-only dry-run is **`HOLD_PROCESS_VISIBILITY`**; ports 7500 and 7800 were observed listening, the source hash was verified, and the actual start count was **0**. Process visibility is under read-only diagnosis. Neither these mocks nor the blocked dry-run establishes activation or fault recovery.

## 6. Reserved continuation: controller's final watchdog evidence

**State at this cutoff: final activation evidence not recorded.** Append a new timestamped entry after the remaining checks; retain this checkpoint unchanged.

| Required field | Cutoff value |
| --- | --- |
| Final watchdog v2 source SHA-256 and byte size | `NOT_RECORDED_HERE` |
| Actual read-only dry-run result | `HOLD_PROCESS_VISIBILITY` |
| Resolved process identity / complete target whitelist | `NOT_VERIFIED` |
| Final task registration and activation evidence | `NOT_RECORDED` |
| Actual starts / stops attributable to v2 | 0 starts reported; no activation PASS |
| Existing 7500 inference and 7700 ASI preservation after activation | `NOT_YET_APPLICABLE` |
| Bounded real fault-recovery receipt | `NOT_RUN` |
| Reboot continuity receipt | `NOT_RUN` |

Any later PASS must identify the actual host, tested source hash, observation window and metadata-only receipt hash. Existing scoped successes remain separate from the remaining recovery gates.


## 7. Continuation — 2026-10-10 R02 actual-host execution

**This continuation supersedes only the current-status conclusions of the 18:42:48 checkpoint above. The earlier checkpoint and failed attempts remain intact. Overall deployment remains INCOMPLETE for the explicit external and recovery gaps in section 12.**

The fixed 33-file package at be2f1d63ed355bb972241cc0db4eeecceeb0f04d was separately staged at D:\MRL_Mother\Recovery\LocalAI_20261010_v2 and verified 33/33 at 18:09:52 UTC. Its D receipt is 9,843 B, SHA-256 6ead3fb8b0eceb4f5bc49ba745179ee705e629e061ad04ee3be4e99a0c4355d4. No frozen payload file is changed by this operations supplement.

The syntax candidate was persisted separately and its parse/compile, one-byte difference and inverse-patch checks were verified on D. The original Watchdog remained byte-identical. Candidate receipt SHA-256: fe1892a60cf65b3a1ce5f1f649ac2dc197606be284c243b30e234a03e1241ab6. The candidate was not executed because its old targets are not the active recovery contract.

## 8. Watchdog activation — monitoring PASS, recovery HELD

The cloud-authored MRL_active_runtime_watchdog_v3.py is 32,301 B, SHA-256 c9d671083bba6d0f8300a1b2e78d983a04e411971f274cf435088f555f1efb0a. Its 29 memory fixtures passed on the actual Windows host.

| Actual event | Verified metadata |
|---|---|
| Task configuration, 18:49:49 UTC | Existing MRL_Watchdog task arguments point to D Python -B and the separate v3 helper; no execution time limit; finite task retry policy. Original task XML was saved first. |
| XML backup | 1,137 B; SHA-256 2e291e5878b7cb05b32b45597479baa5e748d459a9fc7960ea68b2bf94b67ab3 |
| Installer receipt | 2,118 B; SHA-256 2e7ed8368f0b1568410b4d9c4562983d3403cec0d029e946c0ebc148c43a8726 |
| Activation | Task Running; single verified Watchdog PID 41972 |
| Complete qualified observations | 28 records, 18:50:54.425301–19:08:47.522761 UTC, spanning 1,073.09746 seconds |
| Health / source gates | All qualified records passed |
| Recovery actions | 0 process starts, 0 attempt reservations, 0 inference 7500 actions, 0 Bridge 7800 actions |
| Original service owners | Inference PID 20580 and ASI PID 13968 preserved |
| Activation receipt | 3,243 B; SHA-256 1b6bb1fa8e7665eabd15ecdb4c852def33874b03ed05b33b53e41bd4306a5e58 |

Status is ACTIVE_MONITORING_PASS_RECOVERY_HELD. The observation prefix is 19,264 B, SHA-256 455679f6bad2b7efd73b4f8d1148460b1289f0a94b7e07d3b4538794c559ba8f. Writer binding is correlation with the verified single task process; the log records do not themselves embed a PID.

The relative server.js process on port 3050 has unresolved startup provenance. ASI restart therefore remains HELD_UNRESOLVED_RELATIVE_PROCESS. No fault was injected and no host reboot was performed. A running monitor is not evidence of successful fault recovery.

## 9. Authenticated existing inference — actual response PASS

At 19:00:35–19:00:42 UTC, the existing inference service on port 7500 returned HTTP 200, api_ok=true and the exact one-character expected synthetic answer. The completion took 0.64 seconds. The request used max_tokens=8, temperature=0 and persist=false.

The existing authorization value was obtained and used only within the D host from the pinned local source; it was not exported. The source remained byte-identical and PID 20580 remained the owner. Process starts/stops: 0/0.

Receipt: D:\MRL_Mother\Recovery\_operations\LocalAI_20261010_R02_be2f1d63\inference_7500_synthetic_completion_20261010_R02.json; 1,125 B; SHA-256 b027bf865e872d1e6297daa383ec080def5fe7272c76d9917c00af6d0358225d. The earlier unauthenticated 403 attempt is not relabelled as success.

## 10. Permanent private Qdrant instance — actual start PASS

The persistent helper is MRL_qdrant_local_service_v1.py, 36,865 B, SHA-256 5964dbe32fcb3cad9672648aff5e6e6b40a8bfa5a7472c68da0834eeb155be4f, Git blob b6a2c13b45345a58caeaa55afe048fcf36fd734f. Source, official executable, ACL, exact scheduled task and child/supervisor creation identities are checked.

The first private instance fca6388e453e4c4a8319561470a42d84 was staged but task installation failed. Actual Task Scheduler COM validation rejected the UTF-8 encoding declaration in a BSTR XML string (8004131A, line 1 / column 40). Memory-only variants without that encoding declaration, or with UTF-16, validated successfully. No task or listener was created for that instance. Its files and failed output remain in D. The successor changes only that declaration in the service source; it does not overwrite the failed D copy.

| Current instance event | Receipt |
|---|---|
| Stage, 19:21:15 UTC | 1,476 B; SHA-256 46db577754d6879031a1e4e3f08f776d86c9e2f121d6279fd3dcf2dd275722e4 |
| Install disabled, 19:22:07 UTC | 1,041 B; SHA-256 24d8bd745776e7e2ab7c0c4044b2a6c84f3ade83daace193f78364f3f63ab780 |
| Start / verify, 19:23:50 UTC | 2,147 B; SHA-256 af8f7e961b7776e6791a52b69edad7457424feb2ffd48dce6513026d6facb98a |

Instance: D:\MRL_Mother\QdrantLocal\2d38cbbc0b4d4988a19f100c7b9f2d7d. Task: MRL_Qdrant_Local_2d38cbbc0b4d4988a19f100c7b9f2d7d. Qdrant child PID 18712, FILETIME "134361338213041841"; Python supervisor PID 5636, FILETIME "134361338164507244". These 64-bit values are serialized as strings to avoid JSON/JavaScript precision loss.

DURABLE_LOCAL_SERVICE_VERIFIED passed all ten gates: private instance/key ACL, source, official image, exact running task, retry policy, process creation identity, loopback-only listener, accepted key and rejected missing key. Only 127.0.0.1:6333 listens; authenticated /collections is 200 and no-key request is 401. The key is D-generated and private; neither key nor key hash is in exported receipts.

The task has SYSTEM identity, Boot delay 30 seconds, IgnoreNew, PT0S and three retries at 60-second intervals. These settings and initial operation are verified; actual service restart and host reboot execution are NOT_RUN. Application integration is NOT_ASSERTED.

## 11. Permanent storage read/write and timeout reconciliation

| Actual attempt | Result and immutable receipt |
|---|---|
| v1, 19:32:13–19:32:30 UTC | Fresh-name GET 404, create response TimeoutError, no create acknowledgement and no DELETE. Client HOLD. 2,270 B; SHA-256 b175d1640faae0142dcbadd9c97666c3e6151b322c1bb00b00f0316ccc8a6b6d |
| Subsequent v1 read-only diagnosis, 19:39:12 UTC | Unique matching name hash; green, optimizer ok, points 0, segments 8, indexed vectors 0, vectors size 4 / Dot. This empty collection is retained. |
| v2, 19:47:59–19:48:45 UTC | Create 200/acknowledged; point write 200/completed; exact point readback 200/PASS. DELETE response TimeoutError. Client remains HOLD. 2,713 B; SHA-256 4900e6d6df28330bf41e48fae9af4bd88ca370d370ca4ce9d49e95b34ed70c51 |
| Independent read-only reconciliation, 19:52:32 UTC | Same source, task, held child/supervisor identities, loopback and auth passed before/after. Full collection list: total 1, retained v1 hash matches 1, v2 hash matches 0. OBSERVED_API_ABSENT_AFTER_DELETE_TIMEOUT. 4,380 B; SHA-256 70b70cd12587f38a131a02ffc3fa06b75b63305aab15c6f2cb052fd6aa037516 |

Only one fresh UUID retry was performed. v2 is 15,154 B, SHA-256 6ba4236c031a8f2199a0501eccbd709f93c1522af7513c1a675bffd0f594b352. Its sole function change extends create-response socket timeout to 60 seconds and the HTTP request budget to 180 seconds; point PUT/POST, GET and DELETE remain 12 seconds. The ownership-failure latch and acknowledgement-based cleanup logic remain byte-identical. Actual-host fixtures passed 9/9 for v1 and 10/10 for v2.

Qdrant 1.19.2's [official dispatcher implementation](https://github.com/qdrant/qdrant/blob/016542aa5deb6c66380bb137badf73d54f742bde/lib/storage/src/dispatcher.rs) continues submitted non-consensus metadata operations after client cancellation; the cluster=false path does not apply the consensus wait_timeout. This supports the observed possibility of a collection operation completing after a client timeout. It does not establish the exact source of the initialization delay.

The [official collection list](https://github.com/qdrant/qdrant/blob/016542aa5deb6c66380bb137badf73d54f742bde/src/common/collections.rs) returns the complete credential-visible list without pagination. The observation used the same verified private full API key, not a narrower credential. The [official delete path](https://github.com/qdrant/qdrant/blob/016542aa5deb6c66380bb137badf73d54f742bde/lib/storage/src/content_manager/toc/collection_meta_ops.rs) removes the collection from its map before all teardown/background disk deletion completes.

Therefore the precise result is: **permanent-instance create, write and exact readback PASS; original v2 automated CRUD receipt HOLD due to DELETE response timeout; target absent from the API namespace in a later guarded observation.** There is no DELETE acknowledgement, no new DELETE request, and no claim that physical disk cleanup completed. The v1 uncertain empty collection remains untouched. No service was restarted during these probes.

Observation receipt: D:\MRL_Mother\QdrantLocal\2d38cbbc0b4d4988a19f100c7b9f2d7d\state\api_absence_observation_20261010_R02.json.

## 12. Remaining gates and handoff

| Remaining item | Concrete status / required input |
|---|---|
| ASI automatic recovery | 3050 relative server.js startup provenance is unresolved. Keep the recovery latch held until identity is established. |
| Fault / reboot continuity | Not exercised; source fixtures, active observations and task configuration do not establish recovery after a real fault or reboot. |
| Full single-client durable CRUD | Both historical client receipts remain HOLD; v2 read/write succeeded and API absence was later observed. DELETE ACK and physical cleanup remain unverified. |
| Application-to-Qdrant integration | New private endpoint/key metadata exists on D; existing application wiring was not changed or accepted. |
| MinIO / S3 | No actual service on 9000/9001 and no approved production endpoint/artifact. Requires a concrete storage endpoint or accepted deployment source/vendor. |
| MetaEnv controller | Existing 7870 Bridge health works; /api/v1/env/health returned 404. The full controller API contract is not implemented by that health endpoint. |
| Production OAuth | Existing site routes render chat HTML; provider/callback/session/logout wiring is not established. A successful site build is not an OAuth acceptance. |
| Credential retirement | Existing credentials were used locally as authorized; rotation/retirement of pre-existing credentials was not performed. |

Operations source CI separately checks the new manifest and static syntax, Watchdog 29 memory cases, Qdrant service 28, CRUD v1 9 and v2 10. The original 81-test recovery suite and 33-file payload remain separate. The exact new commit and CI run links are recorded in PR #155 and the append-only mother-page backfill after CI completes; this immutable evidence document does not attempt to self-reference its own future commit.

The machine-readable metadata projection is OPERATIONS_RUNTIME_EVIDENCE.json. Every claimed runtime result is limited to its receipt, source version and observed time. No D source/log bodies or credential values were exported.

## 13. Final preservation snapshot — 19:53:07 UTC

MRL_Watchdog and the Qdrant task are enabled and Running. MRL_Bridge and MRL_Tunnel services are Running. Original inference 7500 PID 20580 and ASI 7700 PID 13968 remain unchanged; Qdrant owns only 127.0.0.1:6333, PID 18712, with no 6334/6335 listener.

The original Watchdog, ASI entry and inference source hashes all match their pre-operation identities. This read-only snapshot performed no service control and exported no source/log bodies.

Receipt: D:\MRL_Mother\Recovery\_operations\LocalAI_20261010_R02_be2f1d63\runtime_final_preservation_snapshot_20261010_R02.json; 1,576 B; SHA-256 dc979fe4ec39761ea0029c8c92594e80085ff42f4229021c2fee6ac22712e940.
