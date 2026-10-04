"""Verify the independently pinned, immutable 14-asset source import."""
import hashlib
import json
from pathlib import Path

ORIGINAL_MANIFEST = "docs/MRL_PR149_SwiftUI_Provenance.json"
ORIGINAL_MANIFEST_SHA256 = "16406bd9aa9a3b32eeb62d73a4ddd7699bac9bec7493e1e8cae8af3da2cdc85c"


def check(condition, message):
    if not condition:
        raise ValueError(message)


def verify(root):
    raw = (root / ORIGINAL_MANIFEST).read_bytes()
    check(hashlib.sha256(raw).hexdigest() == ORIGINAL_MANIFEST_SHA256,
          "Original import manifest was changed")
    manifest = json.loads(raw)
    entries = {entry["path"]: entry for entry in manifest["files"]}
    check(len(entries) == len(manifest["files"]) == 14, "Expected 14 unique original assets")
    for path, entry in entries.items():
        data = (root / path).read_bytes()
        check(data and len(data) == entry["size"] and hashlib.sha256(data).hexdigest() == entry["sha256"],
              f"Working asset mismatch: {path}")
    return len(entries), 0


if __name__ == "__main__":
    count, _ = verify(Path(__file__).resolve().parents[1])
    print(f"PASS: {count}/14 source assets, sizes and SHA256; original inventory unchanged")
