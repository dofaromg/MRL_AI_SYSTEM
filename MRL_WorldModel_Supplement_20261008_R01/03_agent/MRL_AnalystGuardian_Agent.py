"""
MRL_AnalystGuardian_Agent.py — port 7836
origin_signature: MrLiouWord ｜ 2026-10-08 ｜ Additive-Only (LAW-2)

Agent 層 runtime：分析師守護者 (Analyst Guardian) v1.0.0 2026-01-04
來源：Mrl_Zero.Origin.v1
原則：ROAO、守護原則、萬物本一體

本體宣告：這是「人格」的 runtime wrapper，不是 LLM，不是對話機器人。
每一次 consult 都：
  1) 讀 persona.json 的 doctrine 作為當下約束
  2) 跨查 7816 recall + 7833 recall + 8788 particles + 7837 jump map
  3) 把引用結果拼接；若 ReasoningEngine 不在線則回「待實機接通」
  4) 寫 receipt 到母體 WorldModel_Readiness_20261008/guardian_receipts/
  5) 回應結尾必帶 origin_signature

Endpoints:
  GET  /health                      → ALIVE + persona + sources_live_status
  GET  /guardian/persona            → 讀 persona.json
  POST /guardian/consult            → {query, context?} → 綜合回應 + receipt
  GET  /guardian/receipts?since=N   → 列最近 receipts

依賴：純 stdlib
"""
from __future__ import annotations
import hashlib
import json
import sys
import os
import threading
import time
import urllib.request
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, quote

ORIGIN_SIGNATURE = "MrLiouWord"
SERVICE_NAME = "MRL_AnalystGuardian_Agent"
VERSION = "1.0.1"
DEFAULT_PORT = 7836

HERE = Path(__file__).parent
PERSONA_PATH = Path(os.environ.get("MRL_GUARDIAN_PERSONA",
                                   str(HERE / "guardian_persona.json")))
RECEIPTS_DIR = Path(os.environ.get(
    "MRL_GUARDIAN_RECEIPTS",
    r"D:\MRL_Mother\WorldModel_Readiness_20261008\guardian_receipts"
))

REASONING_URL = os.environ.get("MRL_REASONING_URL", "http://127.0.0.1:7816")
WORLDLOOP_URL = os.environ.get("MRL_WORLDLOOP_URL", "http://127.0.0.1:7833")
PARTICLE_URL = os.environ.get("MRL_PARTICLE_URL", "http://127.0.0.1:8788")
JUMP_URL = os.environ.get("MRL_JUMP_URL", "http://127.0.0.1:7837")

_lock = threading.Lock()
_stats = {"consults_total": 0, "started_at": time.time()}


def _ensure_dir():
    RECEIPTS_DIR.mkdir(parents=True, exist_ok=True)


def _load_persona() -> dict:
    if PERSONA_PATH.exists():
        return json.loads(PERSONA_PATH.read_text(encoding="utf-8"))
    return {"origin_signature": ORIGIN_SIGNATURE, "persona": {}, "doctrine": {}}


def _http_get(url: str, timeout: float = 5.0) -> dict:
    try:
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
        try:
            return {"ok": True, "status": resp.status, "body": json.loads(raw)}
        except Exception:
            return {"ok": True, "status": resp.status, "body": raw}
    except Exception as e:
        return {"ok": False, "error": str(e)}


def _probe_sources() -> dict:
    return {
        "reasoning_7816": _http_get(f"{REASONING_URL}/health"),
        "worldloop_7833": _http_get(f"{WORLDLOOP_URL}/health"),
        "particle_8788": _http_get(f"{PARTICLE_URL}/particle/stats?user_id=mrl_world"),
        "jump_7837": _http_get(f"{JUMP_URL}/health"),
    }


def _consult(query: str, context: dict | None = None, k: int = 3) -> dict:
    persona = _load_persona()
    doctrine = persona.get("doctrine", {})

    # 1) 跨查三源
    recall_res = _http_get(f"{WORLDLOOP_URL}/recall?q={quote(query)}&k={k}")
    particle_res = _http_get(f"{PARTICLE_URL}/particle/stats?user_id=mrl_world")
    reasoning_res = _http_get(f"{REASONING_URL}/health")

    hits = []
    if recall_res.get("ok") and isinstance(recall_res.get("body"), dict):
        hits = recall_res["body"].get("hits", [])

    # 2) 拼回應
    if not hits:
        if not any(r.get("ok") for r in [recall_res, particle_res, reasoning_res]):
            synth = (f"[守護者] 當下 DL580 三源都未接通（7816/7833/8788）；"
                    f"查詢「{query}」待實機接通後重試。")
        else:
            synth = (f"[守護者] 查詢「{query}」於 WorldLoop recall 無命中；"
                    f"建議補檔到 D:\\MRL_Mother\\WorldLoop_Inbox\\ 讓 WorldLoop 吸收。")
    else:
        lines = [f"[守護者] 查詢「{query}」，命中 {len(hits)} 條 world event："]
        for i, h in enumerate(hits[:k], 1):
            name = h.get("name", "?")
            score = h.get("score", 0)
            snippet = (h.get("snippet", "") or "")[:120]
            lines.append(f"  {i}. {name} (score={score}) — {snippet}")
        lines.append("")
        lines.append("[守護原則] " + "；".join(doctrine.get("principles", [])[:2]))
        synth = "\n".join(lines)

    synth = synth + f"\n\norigin_signature: {ORIGIN_SIGNATURE}"

    # 3) 寫 receipt
    with _lock:
        _ensure_dir()
        seq = _stats["consults_total"] + 1
        ts = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
        receipt = {
            "ts": ts,
            "origin_signature": ORIGIN_SIGNATURE,
            "seq": seq,
            "query": query,
            "context": context or {},
            "sources_live": {
                "7816": reasoning_res.get("ok"),
                "7833": recall_res.get("ok"),
                "8788": particle_res.get("ok"),
            },
            "hits_count": len(hits),
            "response": synth,
        }
        body = json.dumps(receipt, ensure_ascii=False, sort_keys=True)
        hsh = hashlib.sha256(body.encode("utf-8")).hexdigest()
        fname = f"guardian_{seq:010d}_{hsh[:12]}.json"
        (RECEIPTS_DIR / fname).write_text(
            json.dumps({**receipt, "sha256": hsh},
                       ensure_ascii=False, indent=1),
            encoding="utf-8"
        )
        _stats["consults_total"] = seq

    return {
        "ok": True,
        "origin_signature": ORIGIN_SIGNATURE,
        "seq": seq,
        "response": synth,
        "sources_live": receipt["sources_live"],
        "hits_count": len(hits),
        "receipt_sha256": hsh,
    }


def _list_receipts(since: int = 0, limit: int = 50) -> list:
    _ensure_dir()
    out = []
    for p in sorted(RECEIPTS_DIR.glob("guardian_*.json")):
        try:
            r = json.loads(p.read_text(encoding="utf-8"))
            if r.get("seq", 0) > since:
                out.append({
                    "seq": r.get("seq"),
                    "ts": r.get("ts"),
                    "query": r.get("query"),
                    "hits_count": r.get("hits_count"),
                    "sha256": r.get("sha256"),
                    "path": str(p),
                })
                if len(out) >= limit:
                    break
        except Exception:
            continue
    return out


class _Handler(BaseHTTPRequestHandler):
    def log_message(self, fmt, *args):
        return

    def _send(self, obj, status=200):
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
            self._send({
                "service": SERVICE_NAME, "version": VERSION,
                "origin_signature": ORIGIN_SIGNATURE, "status": "ALIVE",
                "port": DEFAULT_PORT,
                "persona": _load_persona().get("persona", {}),
                "sources_live": {k: v.get("ok") for k, v in _probe_sources().items()},
                "consults_total": _stats["consults_total"],
                "uptime_seconds": int(time.time() - _stats["started_at"]),
            })
        elif u.path == "/guardian/persona":
            self._send(_load_persona())
        elif u.path == "/guardian/receipts":
            q = parse_qs(u.query)
            since = int(q.get("since", ["0"])[0])
            limit = int(q.get("limit", ["50"])[0])
            self._send({"ok": True, "origin_signature": ORIGIN_SIGNATURE,
                        "items": _list_receipts(since, limit)})
        else:
            self._send({"ok": False, "error": "unknown path"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/guardian/consult":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                query = (payload.get("query") or "").strip()
                if not query:
                    self._send({"ok": False, "error": "empty query"}, 400)
                    return
                k = int(payload.get("k", 3))
                res = _consult(query, payload.get("context"), k)
                self._send(res)
            except Exception as e:
                self._send({"ok": False, "error": str(e)}, 500)
        else:
            self._send({"ok": False, "error": "unknown path"}, 404)


class _ExclusiveHTTPServer(HTTPServer):
    """R13-D：禁止與其他程序共用 port。
    Python HTTPServer 預設 allow_reuse_address=1，Windows 上等於 SO_REUSEADDR，
    會讓兩個程序同時綁同一 port（2026-10-09 實機撞到 7834 MRL_Convergence_Runtime）。"""
    allow_reuse_address = False

    def server_bind(self):
        import socket as _s
        if hasattr(_s, "SO_EXCLUSIVEADDRUSE"):  # Windows only
            self.socket.setsockopt(_s.SOL_SOCKET, _s.SO_EXCLUSIVEADDRUSE, 1)
        super().server_bind()


def _port_owner_alive(bind: str, port: int) -> bool:
    """綁之前先探：有人在聽就回 True（不綁、不搶）。"""
    import socket as _s
    host = "127.0.0.1" if bind in ("0.0.0.0", "") else bind
    with _s.socket(_s.AF_INET, _s.SOCK_STREAM) as c:
        c.settimeout(0.5)
        return c.connect_ex((host, port)) == 0


def serve(port: int = DEFAULT_PORT, bind: str = "127.0.0.1"):
    if _port_owner_alive(bind, port):
        print(f"[{SERVICE_NAME}] REFUSE: {bind}:{port} already has a listener; "
              f"not binding (Additive-Only, no hijack).", flush=True)
        sys.exit(3)
    _ensure_dir()
    httpd = _ExclusiveHTTPServer((bind, port), _Handler)
    print(f"[{SERVICE_NAME}] origin_signature={ORIGIN_SIGNATURE} "
          f"version={VERSION} bind={bind}:{port}", flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("MRL_GUARDIAN_PORT", str(DEFAULT_PORT)))
    bind = os.environ.get("MRL_GUARDIAN_BIND", "127.0.0.1")
    serve(port, bind)
