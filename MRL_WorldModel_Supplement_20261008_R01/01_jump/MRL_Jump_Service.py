"""
MRL_Jump_Service.py — port 7834
origin_signature: MrLiouWord ｜ 2026-10-08 ｜ Additive-Only (LAW-2)

本體對應：Jump → Collapse → Trace → Replay 的第一拍 (Jump)。
不是 web router，是跳點節奏記錄器。每次 jump 寫 append-only ledger，
SHA-256 鏈，不可改寫 (LAW-0 origin_signature + LAW-2 NO_DELETE)。

Endpoints:
  GET  /health                 → ALIVE + stats
  GET  /jump/map               → 讀 JumpSeedMap
  POST /jump                   → 執行一次跳點
                                  body: {from, to, rhythm, context, actor}
                                  回: {jump_id, prev_hash, this_hash, ledger_seq}
  GET  /jump/ledger?since=N    → 讀 ledger
  GET  /jump/verify            → 驗 SHA-256 鏈完整性

依賴：純 stdlib (http.server, json, hashlib, pathlib, threading)
"""
from __future__ import annotations
import hashlib
import json
import os
import sys
import threading
import time
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ORIGIN_SIGNATURE = "MrLiouWord"
SERVICE_NAME = "MRL_Jump_Service"
VERSION = "1.0.0"
DEFAULT_PORT = 7834

# DL580 母體路徑（可被環境變數覆寫以利沙盒測試）
MOTHER_INBOX = Path(os.environ.get(
    "MRL_JUMP_INBOX",
    r"D:\MRL_Mother\WorldLoop_Inbox\jump"
))
SEEDMAP_PATH = Path(os.environ.get(
    "MRL_JUMP_SEEDMAP",
    str(Path(__file__).parent / "jump_seedmap.json")
))

_lock = threading.Lock()
_stats = {"jumps_total": 0, "started_at": time.time(), "last_hash": "GENESIS"}


def _ledger_path() -> Path:
    MOTHER_INBOX.mkdir(parents=True, exist_ok=True)
    return MOTHER_INBOX / "jump_ledger.jsonl"


def _load_seedmap() -> dict:
    if SEEDMAP_PATH.exists():
        return json.loads(SEEDMAP_PATH.read_text(encoding="utf-8"))
    return {"origin_signature": ORIGIN_SIGNATURE, "nodes": {}, "jumps": []}


def _tail_hash() -> str:
    p = _ledger_path()
    if not p.exists():
        return "GENESIS"
    last = None
    with p.open("rb") as f:
        for line in f:
            if line.strip():
                last = line
    if last is None:
        return "GENESIS"
    try:
        return json.loads(last)["this_hash"]
    except Exception:
        return "GENESIS"


def _append_jump(payload: dict) -> dict:
    """Append-only ledger with SHA-256 chain. NEVER rewrite."""
    with _lock:
        prev_hash = _tail_hash()
        seq = _stats["jumps_total"] + 1
        now = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        record = {
            "jump_id": f"jump_{seq:010d}",
            "ts": now,
            "origin_signature": ORIGIN_SIGNATURE,
            "from": payload.get("from"),
            "to": payload.get("to"),
            "rhythm": payload.get("rhythm", "unspecified"),
            "actor": payload.get("actor", "unknown"),
            "context": payload.get("context", {}),
            "ledger_seq": seq,
            "prev_hash": prev_hash,
        }
        body = json.dumps(record, ensure_ascii=False, sort_keys=True)
        this_hash = hashlib.sha256(body.encode("utf-8")).hexdigest()
        record["this_hash"] = this_hash

        with _ledger_path().open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

        _stats["jumps_total"] = seq
        _stats["last_hash"] = this_hash
        return record


def _verify_chain() -> dict:
    """Walk the ledger and verify SHA-256 chain. Returns ok/broken_at."""
    p = _ledger_path()
    if not p.exists():
        return {"ok": True, "total": 0, "note": "empty ledger"}
    prev = "GENESIS"
    seq = 0
    with p.open("r", encoding="utf-8") as f:
        for line_no, line in enumerate(f, 1):
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("prev_hash") != prev:
                return {"ok": False, "broken_at_line": line_no,
                        "expected_prev": prev, "got_prev": rec.get("prev_hash")}
            # recompute this_hash
            computed_body = {k: v for k, v in rec.items() if k != "this_hash"}
            body = json.dumps(computed_body, ensure_ascii=False, sort_keys=True)
            want = hashlib.sha256(body.encode("utf-8")).hexdigest()
            if want != rec.get("this_hash"):
                return {"ok": False, "broken_at_line": line_no,
                        "expected_hash": want, "got_hash": rec.get("this_hash")}
            prev = rec["this_hash"]
            seq += 1
    return {"ok": True, "total": seq, "tail_hash": prev}


def _read_ledger(since: int = 0, limit: int = 1000) -> list:
    p = _ledger_path()
    if not p.exists():
        return []
    out = []
    with p.open("r", encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            rec = json.loads(line)
            if rec.get("ledger_seq", 0) > since:
                out.append(rec)
                if len(out) >= limit:
                    break
    return out


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        # 靜音預設 access log
        return

    def _send_json(self, obj, status=200):
        body = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("X-MRL-Origin-Signature", ORIGIN_SIGNATURE)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        u = urlparse(self.path)
        if u.path == "/health":
            self._send_json({
                "service": SERVICE_NAME, "version": VERSION,
                "origin_signature": ORIGIN_SIGNATURE, "status": "ALIVE",
                "port": DEFAULT_PORT,
                "jumps_total": _stats["jumps_total"],
                "last_hash": _stats["last_hash"],
                "uptime_seconds": int(time.time() - _stats["started_at"]),
            })
        elif u.path == "/jump/map":
            self._send_json(_load_seedmap())
        elif u.path == "/jump/ledger":
            q = parse_qs(u.query)
            since = int(q.get("since", ["0"])[0])
            limit = int(q.get("limit", ["100"])[0])
            self._send_json({
                "ok": True, "origin_signature": ORIGIN_SIGNATURE,
                "since": since, "entries": _read_ledger(since, limit),
            })
        elif u.path == "/jump/verify":
            self._send_json(_verify_chain())
        else:
            self._send_json({"ok": False, "error": "unknown path"}, status=404)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/jump":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                # 本體/載體邊界檢查
                seedmap = _load_seedmap()
                frm = payload.get("from")
                nodes = seedmap.get("nodes", {})
                if frm and frm in nodes and nodes[frm].get("kind") == "載體":
                    self._send_json({
                        "ok": False,
                        "error": "LAW_body_carrier_boundary: 載體不得主動發起 jump",
                        "from_node": frm, "from_kind": "載體",
                    }, status=400)
                    return
                rec = _append_jump(payload)
                self._send_json({"ok": True, "origin_signature": ORIGIN_SIGNATURE,
                                 **rec})
            except Exception as e:
                self._send_json({"ok": False, "error": str(e)}, status=500)
        else:
            self._send_json({"ok": False, "error": "unknown path"}, status=404)


def serve(port: int = DEFAULT_PORT, bind: str = "127.0.0.1"):
    httpd = HTTPServer((bind, port), _Handler)
    print(f"[{SERVICE_NAME}] origin_signature={ORIGIN_SIGNATURE} "
          f"version={VERSION} bind={bind}:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("MRL_JUMP_PORT", str(DEFAULT_PORT)))
    bind = os.environ.get("MRL_JUMP_BIND", "127.0.0.1")
    serve(port, bind)
