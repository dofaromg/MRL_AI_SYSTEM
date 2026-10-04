# PR151 absorption clarification (additive)

origin_signature: MrLiouWord

The 14 assets in `MRL_PR149_SwiftUI_Provenance.json` remain byte-identical to
import commit `5272acc107af4553e9f27b0a5dd2cbac7b26c827`.

`MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/docs/04_PATCH_NOTES_NavigationStack_v1.md`
is an unchanged historical source-package document. Its reference to
`CHECKSUMS.sha256`, `MANIFEST.json`, and file_count changing from 30 to 32 describes
that original full package only. These full-package manifests are not included
in PR151's client-only import. The actual imported subset is exactly the 14
assets recorded in `docs/MRL_PR149_SwiftUI_Provenance.json`; that inventory is
pinned independently in the verifier. This note adds context without rewriting
the imported patch-note bytes or their provenance.

The absorption workflow disables checkout credential persistence and checks out
the exact PR head. Regression cases reject deletion of an asset together with
its manifest entry, replacement of a path at the same count, and a missing asset.
Hardening runtime changes remain in the independent PR153 branch.

This continuation changes exactly four non-source-asset files:

- `.github/workflows/MRL_PR149_SwiftUI.yml`
- `scripts/MRL_pr149_swiftui_verify.py`
- `tests/test_MRL_pr149_swiftui_integrity.py`
- `docs/MRL_PR151_Import_Notes.md`
