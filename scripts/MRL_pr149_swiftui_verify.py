"""Verify immutable PR151 import plus explicitly declared derived source files."""
import hashlib
import json
from pathlib import Path
import subprocess

IMPORT_COMMIT = "5272acc107af4553e9f27b0a5dd2cbac7b26c827"
ORIGINAL_MANIFEST = "docs/MRL_PR149_SwiftUI_Provenance.json"
ORIGINAL_MANIFEST_SHA256 = "16406bd9aa9a3b32eeb62d73a4ddd7699bac9bec7493e1e8cae8af3da2cdc85c"
HARDENING_MANIFEST = "docs/MRL_PR151_Hardening_Provenance.json"
CLIENT_ROOT = "MRL_3DScanner_iOS_DL580_ProductBridge_v1_1/ios/MRL_3DScanner_iOS/"
DERIVED_PATHS = {CLIENT_ROOT + "Models/Scan.swift", CLIENT_ROOT + "Reconstruction/MRLReconstructionClient.swift", CLIENT_ROOT + "Views/ReconstructionBridgeView.swift"}


def check(condition, message):
    if not condition:
        raise ValueError(message)


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args])


def verify(root):
    manifest_bytes = (root / ORIGINAL_MANIFEST).read_bytes()
    check(hashlib.sha256(manifest_bytes).hexdigest() == ORIGINAL_MANIFEST_SHA256,
          "Original import manifest was changed")
    manifest = json.loads(manifest_bytes)
    entries = {entry["path"]: entry for entry in manifest["files"]}
    check(len(entries) == len(manifest["files"]) == 14, "Expected 14 unique original assets")
    derived = {}
    if (root / HARDENING_MANIFEST).exists():
        extension = json.loads((root / HARDENING_MANIFEST).read_bytes())
        check(extension["origin_signature"] == manifest["origin_signature"], "Origin mismatch")
        check(extension["source_import_commit"] == IMPORT_COMMIT, "Import parent mismatch")
        derived = {entry["path"]: entry for entry in extension["files"]}
        check(len(derived) == len(extension["files"]) == 3 and set(derived) == DERIVED_PATHS,
              "Only the three explicit hardening derivatives are allowed")
    git(root, "merge-base", "--is-ancestor", IMPORT_COMMIT, "HEAD")
    for path, entry in entries.items():
        original = git(root, "show", f"{IMPORT_COMMIT}:{path}")
        original_blob = git(root, "rev-parse", f"{IMPORT_COMMIT}:{path}").decode().strip()
        check(original_blob == entry["source_blob"], f"Original blob mismatch: {path}")
        check(original and len(original) == entry["size"] and
              hashlib.sha256(original).hexdigest() == entry["sha256"], f"Original bytes mismatch: {path}")
        expected = entry
        if path in derived:
            derivative = derived[path]
            check(derivative["original"] == entry, f"Lineage mismatch: {path}")
            expected = derivative["derived"]
        data = (root / path).read_bytes()
        check(data and len(data) == expected["size"] and
              hashlib.sha256(data).hexdigest() == expected["sha256"], f"Working asset mismatch: {path}")
    return len(entries), len(derived)


if __name__ == "__main__":
    originals, derived = verify(Path(__file__).resolve().parents[1])
    print(f"PASS: {originals}/14 original blobs preserved; {originals - derived} unchanged working assets; {derived} explicit derivatives")
