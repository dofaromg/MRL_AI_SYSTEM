"""
selftest_r15_restart_inbox.py — R15 修正驗證（真 HTTP，沙盒）
origin_signature: MrLiouWord ｜ 2026-10-09

1) 起 Jump/Collapse/Guardian，Jump×2 → Collapse → Guardian
2) Collapse 在 Inbox 最上層產出 Collapse_*.fltnz 與 .md（WorldLoop 可收）
3) 全部停掉再重啟：序號延續（jump 3、collapse 2、guardian 2），不從 1 重算
4) 重啟後 ledger 鏈仍完整、舊封存可 replay
5) 刪掉最上層鏡像後重啟 Collapse → 啟動時自動補回（回填機制）
6) Supervisor 寫入每日 jsonl、可連續追加
"""
from __future__ import annotations
import json, os, subprocess, sys, tempfile, time, urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
tmp = Path(tempfile.mkdtemp(prefix="mrl_r15_"))
inbox = tmp / "WorldLoop_Inbox"
ENV = {**os.environ, "MRL_JUMP_INBOX": str(inbox / "jump"), "MRL_COLLAPSE_OUT": str(inbox / "collapse"),
       "MRL_GUARDIAN_RECEIPTS": str(tmp / "receipts"), "MRL_SUPERVISOR_OUT": str(tmp / "supervisor"),
       "PYTHONIOENCODING": "utf-8"}
R = []
def ok(n, c, d=""): R.append(bool(c)); print(f"  [{'PASS' if c else 'FAIL'}] {n}" + (f" — {d}" if d else ""))
def get(u): return json.loads(urllib.request.urlopen(u, timeout=3).read().decode())
def post(u, o):
    rq = urllib.request.Request(u, data=json.dumps(o).encode(), headers={"Content-Type": "application/json"})
    return json.loads(urllib.request.urlopen(rq, timeout=5).read().decode())
def up(u, s=8):
    t = time.time()
    while time.time() - t < s:
        try: return get(u)
        except Exception: time.sleep(0.2)
SCRIPTS = ["01_jump/MRL_Jump_Service.py", "02_collapse/MRL_Collapse_Service.py", "03_agent/MRL_AnalystGuardian_Agent.py"]
def start():
    ps = [subprocess.Popen([PY, "-X", "utf8", str(ROOT / s)], env=ENV, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) for s in SCRIPTS]
    for port in (7837, 7835, 7836): up(f"http://127.0.0.1:{port}/health")
    return ps
def stop(ps):
    for p in ps: p.terminate()
    for p in ps: p.wait(5)
    time.sleep(0.5)

print(f"[selftest_r15] tmp={tmp}")
ps = start()
try:
    post("http://127.0.0.1:7837/jump", {"from": "mrl_origin", "to": "analyst_guardian", "rhythm": "seed_unfold", "actor": "builder", "context": {"seed": "Mrl_Zero.Origin.v1"}})
    post("http://127.0.0.1:7837/jump", {"from": "analyst_guardian", "to": "world_memory", "rhythm": "recall", "actor": "analyst_guardian"})
    c = post("http://127.0.0.1:7835/collapse", {"jump_since_seq": 0, "jump_until_seq": 999})
    ok("collapse_0000000001 + inbox_mirror 2 files", c["collapse_id"] == "collapse_0000000001" and len(c.get("inbox_mirror", [])) == 2)
    tops = sorted(x.name for x in inbox.iterdir() if x.is_file())
    ok("Inbox top-level has .fltnz + .md", any(t.endswith(".fltnz") for t in tops) and any(t.endswith(".md") for t in tops), str(tops))
    md = next(x for x in inbox.iterdir() if x.suffix == ".md").read_text(encoding="utf-8")
    ok(".md has seed + state_hash + rhythm", "Mrl_Zero.Origin.v1" in md and c["state_hash"] in md and "seed_unfold → recall" in md)
    post("http://127.0.0.1:7836/guardian/consult", {"query": "分析師守護者"})
finally:
    stop(ps)

ps = start()
try:
    h = get("http://127.0.0.1:7837/health")
    ok("Jump restored counter after restart", h["jumps_total"] == 2 and h["version"] == "1.0.2")
    j3 = post("http://127.0.0.1:7837/jump", {"from": "analyst_guardian", "to": "particle_globe", "rhythm": "particle_bind", "actor": "analyst_guardian"})
    ok("next jump seq = 3 (not 1)", j3["ledger_seq"] == 3)
    ok("chain verify across restart", get("http://127.0.0.1:7837/jump/verify") == {"ok": True, "total": 3, "tail_hash": j3["this_hash"]})
    c2 = post("http://127.0.0.1:7835/collapse", {"jump_since_seq": 2, "jump_until_seq": 999})
    ok("next collapse id = 2 (not 1)", c2["collapse_id"] == "collapse_0000000002")
    ok("old collapse still replays", get("http://127.0.0.1:7835/collapse/collapse_0000000001/replay")["state_hash_match"] is True)
    g = post("http://127.0.0.1:7836/guardian/consult", {"query": "分析師守護者"})
    ok("guardian seq = 2 (not 1)", g["seq"] == 2)
finally:
    stop(ps)

# backfill: remove top-level mirrors of collapse 1, restart → restored
for x in list(inbox.iterdir()):
    if x.is_file() and "collapse_0000000001" in x.name: x.unlink()
ps = start()
try:
    h = get("http://127.0.0.1:7835/health")
    ok("restart backfills missing inbox mirror", h["mirrored_on_start"] == 2 and h["collapses_total"] == 2, str(h.get("mirrored_on_start")))
finally:
    stop(ps)

for _ in range(2):
    subprocess.run([PY, "-X", "utf8", str(ROOT / "04_supervisor/MRL_WorldModel_Supervisor.py"), "--once"], env=ENV, capture_output=True, timeout=60)
js = list((tmp / "supervisor").glob("supervisor_*.jsonl"))
ok("supervisor daily jsonl, 2 appended lines", len(js) == 1 and len(js[0].read_text(encoding="utf-8").strip().splitlines()) == 2)

print(f"\n[selftest_r15] {sum(R)}/{len(R)} {'ALL PASS' if all(R) else 'FAIL'}")
sys.exit(0 if all(R) else 1)
