"""
MRL_WorldModel_Supervisor.py
origin_signature: MrLiouWord ｜ 2026-10-08 ｜ Additive-Only (LAW-2)

本體角色：母體治理者。不綁 port，是一個每 N 秒跑一輪的 supervisor。
把 7816 / 7833 / 7834 / 7835 / 7836 / 8788 六個端口的健康狀態
寫到 WorldModel_Readiness_20261008/supervisor/<ISO>.json。

一輪做：
  1) health check 六端口（並行、500ms timeout）
  2) 讀 Jump ledger 近 10 筆 + /jump/verify
  3) 讀 Guardian receipts 近 5 筆
  4) 讀 Collapse list 近 5 筆
  5) 檢查本體/載體邊界：
     - 本體 = Jump / Collapse / Guardian / Mrl_Zero.Origin
     - 載體 = ReasoningEngine / WorldLoop / ParticleGlobe
     - 若有載體試圖寫 Jump ledger（actor 欄位），記 anomaly
  6) 寫 supervisor_<ISO>.json，不覆蓋，老檔只增

用法：
  python MRL_WorldModel_Supervisor.py --interval 60
  python MRL_WorldModel_Supervisor.py --once        # 跑一次就退
"""
from __future__ import annotations
import argparse
import json
import os
import sys
import time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ORIGIN_SIGNATURE = "MrLiouWord"
VERSION = "1.0.0"

OUT_DIR = Path(os.environ.get(
    "MRL_SUPERVISOR_OUT",
    r"D:\MRL_Mother\WorldModel_Readiness_20261008\supervisor"
))

ENDPOINTS = {
    "reasoning_7816": ("http://127.0.0.1:7816/health", "載體"),
    "worldloop_7833": ("http://127.0.0.1:7833/health", "載體"),
    "jump_7834": ("http://127.0.0.1:7834/health", "本體"),
    "collapse_7835": ("http://127.0.0.1:7835/health", "本體"),
    "guardian_7836": ("http://127.0.0.1:7836/health", "本體"),
    "particle_8788": ("http://127.0.0.1:8788/particle/stats?user_id=mrl_world",
                      "載體"),
}
EXTRAS = {
    "jump_verify": "http://127.0.0.1:7834/jump/verify",
    "jump_ledger_tail": "http://127.0.0.1:7834/jump/ledger?since=0&limit=10",
    "collapse_list": "http://127.0.0.1:7835/collapse/list",
    "guardian_receipts": "http://127.0.0.1:7836/guardian/receipts?limit=5",
}


def _get(url: str, timeout: float = 1.5) -> dict:
    try:
        t0 = time.time()
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
        ms = int((time.time() - t0) * 1000)
        try:
            body = json.loads(raw)
        except Exception:
            body = raw
        return {"ok": True, "status": resp.status, "latency_ms": ms, "body": body}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _check_boundary(ledger_body) -> list:
    """載體不得主動 jump。actor 欄位若 ∈ 載體清單，記 anomaly。"""
    anomalies = []
    carriers = {name for name, (_, kind) in ENDPOINTS.items() if kind == "載體"}
    carrier_names = {"MRL_ReasoningEngine", "MRL_WorldLoop_Service",
                     "ParticleGlobe", "reasoning_7816", "worldloop_7833",
                     "particle_8788"}
    if not isinstance(ledger_body, dict):
        return anomalies
    for e in ledger_body.get("entries", []):
        actor = e.get("actor", "")
        if actor in carrier_names:
            anomalies.append({
                "jump_id": e.get("jump_id"),
                "actor": actor,
                "note": "LAW_body_carrier_boundary: 載體發起 jump，違反本體/載體邊界",
            })
    return anomalies


def run_once() -> dict:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = time.strftime("%Y-%m-%dT%H%M%SZ", time.gmtime())
    report = {
        "origin_signature": ORIGIN_SIGNATURE,
        "supervisor_version": VERSION,
        "ts": ts,
        "ports": {},
        "extras": {},
        "boundary_anomalies": [],
        "summary": {},
    }

    with ThreadPoolExecutor(max_workers=10) as ex:
        futs = {ex.submit(_get, url): (name, kind)
                for name, (url, kind) in ENDPOINTS.items()}
        for fut in as_completed(futs):
            name, kind = futs[fut]
            report["ports"][name] = {"kind": kind, **fut.result()}

        futs2 = {ex.submit(_get, url): name for name, url in EXTRAS.items()}
        for fut in as_completed(futs2):
            name = futs2[fut]
            report["extras"][name] = fut.result()

    ledger = report["extras"].get("jump_ledger_tail", {}).get("body")
    report["boundary_anomalies"] = _check_boundary(ledger)

    alive = sum(1 for v in report["ports"].values() if v.get("ok"))
    total = len(report["ports"])
    report["summary"] = {
        "ports_alive": alive,
        "ports_total": total,
        "all_green": alive == total,
        "anomalies": len(report["boundary_anomalies"]),
    }

    out = OUT_DIR / f"supervisor_{ts}.json"
    out.write_text(json.dumps(report, ensure_ascii=False, indent=1),
                   encoding="utf-8")
    report["written_to"] = str(out)
    return report


def run_loop(interval: int):
    print(f"[Supervisor] origin_signature={ORIGIN_SIGNATURE} "
          f"interval={interval}s out={OUT_DIR}", flush=True)
    while True:
        try:
            r = run_once()
            s = r["summary"]
            print(f"[Supervisor {r['ts']}] alive={s['ports_alive']}/{s['ports_total']} "
                  f"anomalies={s['anomalies']} → {r['written_to']}", flush=True)
        except Exception as e:
            print(f"[Supervisor ERROR] {e}", file=sys.stderr, flush=True)
        time.sleep(interval)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--interval", type=int, default=60)
    ap.add_argument("--once", action="store_true")
    args = ap.parse_args()
    if args.once:
        r = run_once()
        print(json.dumps(r["summary"], ensure_ascii=False, indent=1))
        print(f"written: {r['written_to']}")
    else:
        run_loop(args.interval)
