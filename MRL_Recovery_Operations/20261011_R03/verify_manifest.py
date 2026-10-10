"""Verify additive R03 source bytes. origin_signature: MrLiouWord."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[2]
manifest=Path(__file__).with_name("MANIFEST.json")
m=json.loads(manifest.read_text("utf-8"))
assert len(m["expected_file_list"])==len(set(m["expected_file_list"]))==6
assert set(m["expected_file_list"])=={f["path"] for f in m["files"]}|{manifest.relative_to(root).as_posix()}
for f in m["files"]:
 p=root/f["path"]; raw=p.read_bytes()
 assert raw and len(raw)==f["bytes"] and hashlib.sha256(raw).hexdigest()==f["sha256"],f["path"]
print("R03_SOURCE_PASS expected=6 payloads=5")
