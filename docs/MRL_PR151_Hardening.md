# PR151 iOS client hardening follow-up

origin_signature: MrLiouWord

## Scope and lineage

This follow-up starts at the immutable PR151 import commit
`5272acc107af4553e9f27b0a5dd2cbac7b26c827` and includes the workflow-only fix
`a8355c7b6f0cbaefc9aaf4897a5cfd0c9843f240`. The PR151 absorption branch changes
only the workflow path filter; all its 14 source assets stay byte-identical.

Two Swift files are explicitly derived in this separate follow-up. Their original
paths, source/last-change commits, source blobs, byte sizes and SHA256 remain in
`MRL_PR149_SwiftUI_Provenance.json`, which is unchanged. The new
`MRL_PR151_Hardening_Provenance.json` records the original entries alongside the
new byte sizes and SHA256. Original bytes remain available through
`git show 5272acc107af4553e9f27b0a5dd2cbac7b26c827:<original path>`.
No history, source blob or original manifest is rewritten.

The verifier checks all 14 original Git blobs and the immutable manifest, then
checks 12 unchanged working assets and exactly two declared derivatives. It does
not claim that the two hardened files are byte-identical to their imports.

## Runtime changes

- Reconstruction upload copies image data in 64 KiB chunks into a unique temporary
  multipart file and uses `URLSession.upload(for:fromFile:)`. The temporary file
  stays alive until the awaited request finishes and is removed on success,
  response/decode/network failure or cancellation. Partial files are removed if
  staging fails. Per-chunk autorelease pools prevent Objective-C temporary data
  from accumulating. This trades O(total payload) temporary disk space for bounded
  application-side payload memory; it does not measure URLSession's internal RAM.
- `ScanStore.load()` trusts the currently enumerated scan directory. Persisted
  model URLs below the old scan folder are rebased by path components, preserving
  nested names. External URLs and sibling directories remain unchanged. Reading
  does not rewrite JSON; an explicit later save persists current locations.
- Existing server routes, multipart field name `files`, scan headers and response
  schema are preserved. `PhotogramApp.swift` still uses `ScansListView`.

Apple API reference:
https://developer.apple.com/documentation/foundation/urlsession/upload(for:fromfile:delegate:)

## Dependency tree and package map

- PhotogramApp -> ScanStore -> Scan -> current Documents/Scans directory.
- ReconstructionBridgeView -> MRLReconstructionClient -> MRLMultipartBody ->
  FileHandle -> temporary multipart file -> URLSession upload -> existing server.
- SwiftPM `MRLScannerCore` -> the actual Scan.swift, MRLReconstructionClient.swift,
  MRLReconstructionJob.swift and FileManager+Tools.swift sources.
- SwiftPM `HardeningTests` -> MRLScannerCore -> Foundation/Combine/Darwin/XCTest.
- Original asset verifier -> immutable original manifest + import commit + explicit
  hardening manifest -> source and derived hashes.

No ZIP is part of this delivery. Package.swift is a regression-test package, not
an iOS application project or a replacement source manifest.

## Expected file list (10 paths relative to repository root)

1. `.github/workflows/MRL_PR149_SwiftUI.yml`
2. `.github/workflows/MRL_PR151_Hardening.yml`
3. `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/Package.swift`
4. `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/Tests/HardeningTests/HardeningTests.swift`
5. `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/ios/MRL_3DScanner_iOS/Models/Scan.swift`
6. `MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/ios/MRL_3DScanner_iOS/Reconstruction/MRLReconstructionClient.swift`
7. `docs/MRL_PR151_Hardening.md`
8. `docs/MRL_PR151_Hardening_Provenance.json`
9. `scripts/MRL_pr149_swiftui_verify.py`
10. `tests/test_MRL_pr151_provenance.py`

Per-file size and SHA256 for these delivered files are recorded in the follow-up
PR body, avoiding a self-referential hash of this document.

## Validation and limits

Commands:

```sh
python3 scripts/MRL_pr149_swiftui_verify.py
python3 -m unittest discover -s tests -p test_MRL_pr151_provenance.py -v
swift test --package-path MRL_3DScanner_iOS_DL580_ProductBridge_v1_1
```

The Python tests reject undeclared source changes, changed lineage, changed
original manifests, duplicate/extra derivatives and missing declarations; they
also ensure every manifested source path triggers the integrity workflow.
The Swift tests exercise multipart bytes/MIME/boundaries, filename header safety,
144 MiB staging under a 64 MiB RSS-growth budget, independent temporary files,
success/error/cancellation cleanup, empty scans, actual container relocation,
model descendants, external/sibling paths, and save/reload behavior.

The hardening workflow checks out the exact PR head, runs those tests, and
separately typechecks the actual core files against an iOS simulator SDK.
Swift/macOS/iOS execution is unavailable in the Linux editing environment; only
GitHub job results for the new exact head can establish those results.
The workflow does not launch an iOS app, validate NavigationStack UI, deploy a
backend, or contact DL580. NavigationStack remains inactive and no merge is
performed. CI and owner acceptance are separate from source delivery coverage.

## Mergeability observation (2026-10-04)

The supplied `mergeable=false` could not be reproduced. Before edits, the GitHub
REST PR snapshot returned `mergeable=true`, `mergeable_state=clean`, with base
`e4f7a1ec43f30bd1820ec0d20b1203b0a203b9a8` and head `5272acc...`.
Local `git merge-tree --write-tree` completed without conflicts against both that
base and the fetched canonical branch tip
`d836143fb4320e1359f2d3e4a8b0c4fec4d70b05`. The latter contains runtime PR150 and
FlowRhythm PR152 changes outside these iOS assets. There is no demonstrated file
conflict to resolve. The reason for a historical false response remains unknown;
no conflict repair or mainline rebase is invented. After the workflow-only commit,
the API reported `mergeable=true`, `mergeable_state=unstable` while checks updated;
that status is not evidence of a textual conflict or of completed validation.
