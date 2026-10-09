"""
selftest_r16_kernel_host.py — 常駐 ASI Kernel 宿主（7838）沙盒自測
origin_signature: MrLiouWord ｜ 2026-10-09
驗：原 kernel SHA 驗身、跨請求累積 tick、16 tick 出 Seal 並鏡像到 Inbox 頂層、
    timeline 雜湊鏈、queryAt、重啟後重放 decision 全吻合且 tick 接續、第二實例拒綁、SHA 不符拒啟。
"""
import json, os, shutil, subprocess, sys, tempfile, time, urllib.request, hashlib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
HOST = ROOT / "05_kernel" / "MRL_ASI_Kernel_Host.mjs"
NODE = os.environ.get("MRL_NODE") or shutil.which("node")
PORT = "17838"
tmp = Path(tempfile.mkdtemp(prefix="mrl_r16_"))
(tmp / "inbox").mkdir()
ENV = {**os.environ, "MRL_KERNEL_PORT": PORT, "MRL_KERNEL_OUT": str(tmp / "kernel"), "MRL_KERNEL_INBOX_TOP": str(tmp / "inbox")}
U = f"http://127.0.0.1:{PORT}"
res = []


def ok(n, c, d=""):
    res.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {n}" + (f" — {d}" if d else ""))


def get(p):
    with urllib.request.urlopen(U + p, timeout=3) as r:
        return json.loads(r.read())


def post(p, o):
    rq = urllib.request.Request(U + p, data=json.dumps(o).encode(), headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(rq, timeout=5) as r:
        return json.loads(r.read())


def start():
    p = subprocess.Popen([NODE, str(HOST)], env=ENV, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    for _ in range(50):
        try:
            return p, get("/health")
        except Exception:
            time.sleep(0.2)
    return p, None


INTENTS = ["reify", "query", "compute", "observe", "advance"]
p, h = start()
try:
    ok("health + kernel sha verified", h and h["kernel"]["sha_verified"] and h["service"] == "MRL_ASI_Kernel_Host")
    seals = []
    for i in range(20):
        r = post("/run", {"intent": INTENTS[i % 5], "text": f"母體語料 tick {i+1}"})
        if r.get("seal"):
            seals.append(r["seal"])
    ok("tick accumulates across requests (20)", r["data"]["tick"] == 20, r["data"]["tick"])
    ok("one seal at tick 16", len(seals) == 1 and seals[0]["tick"] == 16)
    ok("seal mirrored to inbox top", any(f.name.endswith(".flpkg") for f in (tmp / "inbox").iterdir()))
    seal = json.loads(next((tmp / "kernel" / "seals").iterdir()).read_text(encoding="utf-8"))
    ok("seal digest = sha256(JSON.stringify(manifest))",
       seal["digest"] == hashlib.sha256(json.dumps(seal["manifest"], separators=(",", ":"), ensure_ascii=False).encode()).hexdigest())
    v = get("/timeline/verify")
    ok("timeline chain ok 20", v["ok"] and v["total"] == 20)
    q = get("/timeline/query?tick=18")
    ok("queryAt(18) + nearest checkpoint 16", q["data"]["record"]["tick"] == 18 and q["data"]["nearest_checkpoint"]["tick"] == 16)
    rm = get("/reverse-mine?tick=5")
    ok("reverse-mine works", len(rm["data"]) == 5)
    try:
        post("/run", {"intent": "rm -rf"}); ok("bad intent rejected", False)
    except urllib.error.HTTPError as e:
        ok("bad intent rejected", e.code == 400)
    r2 = subprocess.run([NODE, str(HOST)], env=ENV, capture_output=True, text=True, timeout=10)
    ok("2nd instance refuses (exit 3)", r2.returncode == 3)
finally:
    p.terminate(); p.wait()

time.sleep(0.5)
p, h = start()
try:
    rs = h["restore"]
    ok("restart: replayed 20, decisions all match", rs["replayed"] == 20 and rs["decision_match"] == 20 and rs["chain_ok"], json.dumps(rs))
    ok("restart: tick restored = 20", h["tick"] == 20 and h["timeline_seq"] == 20)
    r = post("/run", {"intent": "observe", "text": "重啟後第一筆"})
    ok("restart: next tick = 21, chain continues", r["data"]["tick"] == 21 and get("/timeline/verify")["total"] == 21)
finally:
    p.terminate(); p.wait()

bad = tmp / "bad_kernel.mjs"
bad.write_text("export class MRLiouASIKernel {}", encoding="utf-8")
r3 = subprocess.run([NODE, str(HOST)], env={**ENV, "MRL_KERNEL_FILE": str(bad)}, capture_output=True, text=True, timeout=10)
ok("tampered kernel refused (exit 2)", r3.returncode == 2)

print(f"\n[selftest_r16] {sum(res)}/{len(res)} {'ALL PASS' if all(res) else 'FAIL'}")
sys.exit(0 if all(res) else 1)
