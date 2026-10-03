import hashlib, json
from pathlib import Path
root = Path(__file__).resolve().parents[1]
manifest = json.loads((root / "docs/MRL_PR149_SwiftUI_Provenance.json").read_text())
for entry in manifest["files"]:
    data = (root / entry["path"]).read_bytes()
    assert data and len(data) == entry["size"]
    assert hashlib.sha256(data).hexdigest() == entry["sha256"], entry["path"]
print(f"PASS: {len(manifest['files'])} source assets, sizes and SHA256")
