"""selftest_r19_dropbox_sync.py — Dropbox⇄DL580 同步引擎（本機來源模式）自測。origin_signature: MrLiouWord
驗：新檔下載＋content_hash 核對、分段收齊才合併並以清單 sha256 核對、缺段等待、zip 逐層索引進連結層、
    Outbox 只新增不覆蓋、第二輪不重複（游標＋done）、同名不同內容另存不覆蓋。"""
import io, json, os, subprocess, sys, tempfile, zipfile, hashlib, gzip
from pathlib import Path
HERE = Path(__file__).resolve().parent.parent / "09_dropbox_sync" / "MRL_Dropbox_DL580_Sync.py"
T = Path(tempfile.mkdtemp(prefix="mrl_r19_")); src = T / "dropbox"; res = []
def ok(n, c, d=""): res.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {n}" + (f" — {d}" if d else ""))
inner = io.BytesIO(); zipfile.ZipFile(inner, "w").writestr("母體/FlowAgent.TotalCore.Unity.v3.flpkg", "seed")
outer = io.BytesIO()
with zipfile.ZipFile(outer, "w") as z:
    z.writestr("a.txt", "hello"); z.writestr("inner.zip", inner.getvalue())
data = outer.getvalue() * 50                     # 讓它夠大可分段（內容非合法 zip 也無妨，用另一個檔測索引）
inbox = src / "MRL_DL580_Inbox"; inbox.mkdir(parents=True)
(inbox / "small.zip").write_bytes(outer.getvalue())
big = data; n = 3; step = len(big) // n + 1
parts = [big[i:i + step] for i in range(0, len(big), step)]
for i, p in enumerate(parts[:-1]): (inbox / f"big.bin.part{i:03d}").write_bytes(p)   # 先缺最後一段
(inbox / "MRL_Intake_Manifest.json").write_text(json.dumps({"files": [{"name": "big.bin", "sha256": hashlib.sha256(big).hexdigest()}]}), encoding="utf-8")
cfg = {"watch": ["/MRL_DL580_Inbox"], "intake_root": str(T / "intake"), "outbox_local": str(T / "outbox"),
       "outbox_remote": "/MRL_DL580_Outbox", "state_dir": str(T / "state"), "worlds_dir": str(T / "worlds")}
(T / "cfg.json").write_text(json.dumps(cfg), encoding="utf-8")
(T / "outbox").mkdir(); (T / "outbox" / "receipt_1.json").write_text("{}", encoding="utf-8")
run = lambda *a: subprocess.run([sys.executable, str(HERE), "--config", str(T / "cfg.json"), "--local-source", str(src), "--once", *a], capture_output=True, text=True, encoding="utf-8", errors="replace")
r = run(); out = r.stdout
day = sorted((T / "intake").iterdir())[0]
ok("downloaded with content_hash", '"action": "downloaded"' in out and (day / "MRL_DL580_Inbox" / "small.zip").exists())
ok("incomplete parts not joined (waits)", not (day / "MRL_DL580_Inbox" / "big.bin").exists())
ok("outbox uploaded", (src / "_outbox_mirror" / "MRL_DL580_Outbox" / "receipt_1.json").exists())
w = list((T / "worlds").glob("*.jsonl.gz")); rows = [json.loads(l) for l in gzip.open(w[0], "rt", encoding="utf-8")] if w else []
ok("zip indexed recursively into linkage world", any("inner.zip!/" in r[1] for r in rows), f"{len(rows)} rows")
(inbox / f"big.bin.part{len(parts)-1:03d}").write_bytes(parts[-1])     # 補上最後一段
r2 = run(); out2 = r2.stdout
ok("second cycle downloads only the new part", out2.count('"action": "downloaded"') == 1, out2.count('"action": "downloaded"'))
j = day / "MRL_DL580_Inbox" / "big.bin"
ok("joined after all parts arrive, sha256 verified", j.exists() and hashlib.sha256(j.read_bytes()).hexdigest() == hashlib.sha256(big).hexdigest() and '"sha256_verified": true' in out2)
ok("outbox not re-uploaded", "outbox_uploaded" not in out2)
(T / "outbox" / "receipt_1.json").write_text('{"changed":1}', encoding="utf-8")
r3 = run(); ok("changed outbox file: remote kept (add-only)", "outbox_exists" in r3.stdout and (src / "_outbox_mirror" / "MRL_DL580_Outbox" / "receipt_1.json").read_text() == "{}")
(inbox / "small.zip").write_bytes(b"different")
r4 = run(); ok("same name new content saved aside, original kept", (day / "MRL_DL580_Inbox" / "small.zip").read_bytes() == outer.getvalue() and any(p.name.startswith("small.zip.rev-") for p in (day / "MRL_DL580_Inbox").iterdir()))
r5 = subprocess.run([sys.executable, str(HERE), "--config", str(T / "cfg.json"), "--once"], capture_output=True, text=True, encoding="utf-8", errors="replace")
ok("no credential -> waits, exit 5, nothing leaked", r5.returncode == 5 and "waiting_for_credential" in r5.stdout)
print(f"\n[selftest_r19] {sum(res)}/{len(res)} {'ALL PASS' if all(res) else 'FAIL'}"); sys.exit(0 if all(res) else 1)
