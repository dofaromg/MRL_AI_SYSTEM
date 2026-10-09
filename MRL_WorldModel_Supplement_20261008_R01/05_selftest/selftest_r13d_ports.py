"""
selftest_r13d_ports.py — 重現 2026-10-09 實機 7834 撞 port 情境（真 HTTP，沙盒）
origin_signature: MrLiouWord ｜ 2026-10-09

1) 起一個假的 MRL_Convergence_Runtime 佔住 7834
2) 用預設 port 起 Jump(7837) / Collapse(7835) / Guardian(7836) 三個真 server（子程序）
3) 驗：三服務 /health 的 service 名稱正確
4) 驗：第二個 Jump 實例會「拒綁」(exit 3)，不會搶 7837
5) 驗：把 Jump 指到 7834 時也「拒綁」(exit 3)，7834 仍是 Convergence
6) Jump→Collapse→Replay 走真 HTTP 一輪
7) Supervisor：7834 只列 observe_only，jump_7837 以 service 名稱驗身
"""
from __future__ import annotations
import json
import os
import subprocess
import sys
import tempfile
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PY = sys.executable
tmp = Path(tempfile.mkdtemp(prefix="mrl_r13d_"))
ENV = {**os.environ,
       "MRL_JUMP_INBOX": str(tmp / "jump"),
       "MRL_COLLAPSE_OUT": str(tmp / "collapse"),
       "MRL_GUARDIAN_RECEIPTS": str(tmp / "receipts"),
       "MRL_SUPERVISOR_OUT": str(tmp / "supervisor"),
       "PYTHONIOENCODING": "utf-8"}
results = []


def ok(name, cond, detail=""):
    results.append(cond)
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}" + (f" — {detail}" if detail else ""))


def get(url, timeout=2):
    with urllib.request.urlopen(url, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def post(url, obj, timeout=3):
    req = urllib.request.Request(url, data=json.dumps(obj).encode("utf-8"),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return json.loads(r.read().decode("utf-8"))


def wait_up(url, secs=8):
    t0 = time.time()
    while time.time() - t0 < secs:
        try:
            return get(url, 1)
        except Exception:
            time.sleep(0.2)
    return None


class FakeConvergence(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def do_GET(self):
        b = json.dumps({"ok": True, "service": "MRL_Convergence_Runtime",
                        "version": "1.0.1", "origin_signature": "MrLiouWord"}).encode()
        self.send_response(200)
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)


def main():
    print(f"[selftest_r13d] tmp={tmp}")
    conv = HTTPServer(("127.0.0.1", 7834), FakeConvergence)
    threading.Thread(target=conv.serve_forever, daemon=True).start()

    procs = []
    try:
        for script in ("01_jump/MRL_Jump_Service.py",
                       "02_collapse/MRL_Collapse_Service.py",
                       "03_agent/MRL_AnalystGuardian_Agent.py"):
            procs.append(subprocess.Popen([PY, "-X", "utf8", str(ROOT / script)],
                                          env=ENV, stdout=subprocess.PIPE,
                                          stderr=subprocess.STDOUT))
        hj = wait_up("http://127.0.0.1:7837/health")
        hc = wait_up("http://127.0.0.1:7835/health")
        hg = wait_up("http://127.0.0.1:7836/health")
        ok("Jump on 7837", bool(hj) and hj.get("service") == "MRL_Jump_Service", str(hj and hj.get("version")))
        ok("Collapse on 7835", bool(hc) and hc.get("service") == "MRL_Collapse_Service")
        ok("Guardian on 7836", bool(hg) and hg.get("service") == "MRL_AnalystGuardian_Agent")

        # 4) 第二個 Jump 實例要拒綁
        r = subprocess.run([PY, "-X", "utf8", str(ROOT / "01_jump/MRL_Jump_Service.py")],
                           env=ENV, capture_output=True, text=True, timeout=10)
        ok("2nd Jump instance refuses (exit 3)", r.returncode == 3, r.stdout.strip()[:90])

        # 5) Jump 指到 7834 要拒綁，7834 仍是 Convergence
        r = subprocess.run([PY, "-X", "utf8", str(ROOT / "01_jump/MRL_Jump_Service.py")],
                           env={**ENV, "MRL_JUMP_PORT": "7834"},
                           capture_output=True, text=True, timeout=10)
        ok("Jump refuses 7834 (exit 3)", r.returncode == 3)
        ok("7834 still Convergence", get("http://127.0.0.1:7834/health").get("service") == "MRL_Convergence_Runtime")

        # 6) 真 HTTP 一輪 Jump→Collapse→Replay
        j1 = post("http://127.0.0.1:7837/jump", {"from": "mrl_origin", "to": "analyst_guardian",
                                                 "rhythm": "seed_unfold", "actor": "builder"})
        j2 = post("http://127.0.0.1:7837/jump", {"from": "analyst_guardian", "to": "world_memory",
                                                 "rhythm": "recall", "actor": "analyst_guardian"})
        ok("2 jumps via HTTP", j1.get("ok") and j2.get("ledger_seq") == 2)
        try:
            post("http://127.0.0.1:7837/jump", {"from": "worldloop", "to": "analyst_guardian",
                                                "actor": "MRL_WorldLoop_Service"})
            ok("carrier jump blocked (400)", False)
        except urllib.error.HTTPError as e:
            ok("carrier jump blocked (400)", e.code == 400)
        v = get("http://127.0.0.1:7837/jump/verify")
        ok("chain verify via HTTP", v.get("ok") is True and v.get("total") == 2)
        c = post("http://127.0.0.1:7835/collapse", {"jump_since_seq": 0, "jump_until_seq": 99})
        ok("collapse pulled 2 jumps from 7837", c.get("jump_count") == 2, c.get("collapse_id"))
        rp = get(f"http://127.0.0.1:7835/collapse/{c['collapse_id']}/replay")
        ok("replay state_hash_match", rp.get("state_hash_match") is True)
        g = post("http://127.0.0.1:7836/guardian/consult", {"query": "分析師守護者"})
        ok("guardian consult ok + signature", g.get("ok") and "MrLiouWord" in g.get("response", ""))

        # 7) Supervisor
        r = subprocess.run([PY, "-X", "utf8", str(ROOT / "04_supervisor/MRL_WorldModel_Supervisor.py"), "--once"],
                           env=ENV, capture_output=True, text=True, timeout=30)
        rep_files = sorted((tmp / "supervisor").glob("supervisor_*.json"))
        ok("supervisor wrote report", bool(rep_files))
        if rep_files:
            rep = json.loads(rep_files[-1].read_text(encoding="utf-8"))
            ports = rep["ports"]
            ok("supervisor: jump_7837 ok", ports["jump_7837"]["ok"] is True)
            ok("supervisor: collapse/guardian ok",
               ports["collapse_7835"]["ok"] and ports["guardian_7836"]["ok"])
            ok("supervisor: 7834 observe_only (not counted)",
               "convergence_7834" in rep.get("observe_only", {}) and "jump_7834" not in ports)
            ok("supervisor: our 3 本體 ports alive",
               sum(1 for k in ("jump_7837", "collapse_7835", "guardian_7836") if ports[k]["ok"]) == 3)
    finally:
        for p in procs:
            p.terminate()
        conv.shutdown()

    allp = all(results)
    print(f"\n[selftest_r13d] {sum(results)}/{len(results)} {'ALL PASS' if allp else 'FAIL'}")
    sys.exit(0 if allp else 1)


if __name__ == "__main__":
    main()
