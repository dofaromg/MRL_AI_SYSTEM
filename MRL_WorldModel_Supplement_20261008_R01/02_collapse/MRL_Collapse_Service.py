"""
MRL_Collapse_Service.py — port 7835
origin_signature: MrLiouWord ｜ 2026-10-08 ｜ Additive-Only (LAW-2)

本體對應：Jump → Collapse → Trace → Replay 的第二拍 (Collapse)。
把一段 jump trace window 封存成一顆 .fltnz 能量球；可透過 /replay 復原。
.fltnz 寫到 D:\\MRL_Mother\\WorldLoop_Inbox\\collapse\\，不覆蓋。

Endpoints:
  GET  /health                       → ALIVE + stats
  POST /collapse                     → 封存一段 trace window
                                        body: {jump_since_seq, jump_until_seq, source_url?}
                                        回: {collapse_id, fltnz_path, state_hash}
  GET  /collapse/{id}/manifest       → 讀 envelope
  GET  /collapse/{id}/replay         → 復原 payload
  GET  /collapse/list                → 列出所有 .fltnz

依賴：純 stdlib
"""
from __future__ import annotations
import base64
import gzip
import hashlib
import json
import sys
import os
import re
import threading
import time
import urllib.request
import urllib.error
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs

ORIGIN_SIGNATURE = "MrLiouWord"
SERVICE_NAME = "MRL_Collapse_Service"
VERSION = "1.0.2"
DEFAULT_PORT = 7835

MOTHER_COLLAPSE = Path(os.environ.get(
    "MRL_COLLAPSE_OUT",
    r"D:\MRL_Mother\WorldLoop_Inbox\collapse"
))
# R15-1：WorldLoop 只觀測 Inbox 最上層（glob("*") + is_file），所以另寫一份到最上層
INBOX_TOP = Path(os.environ.get("MRL_COLLAPSE_INBOX_TOP", str(MOTHER_COLLAPSE.parent)))
JUMP_SERVICE_URL = os.environ.get("MRL_JUMP_URL", "http://127.0.0.1:7837")

_lock = threading.Lock()
_stats = {"collapses_total": 0, "started_at": time.time()}


def _ensure_dir():
    MOTHER_COLLAPSE.mkdir(parents=True, exist_ok=True)


def _fetch_jump_ledger(since: int, until: int) -> list:
    """從 Jump service 拉 ledger 區間；離線時容錯回 []。"""
    try:
        url = f"{JUMP_SERVICE_URL}/jump/ledger?since={since}&limit=10000"
        with urllib.request.urlopen(url, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        entries = data.get("entries", [])
        return [e for e in entries if since < e.get("ledger_seq", 0) <= until]
    except Exception:
        return []


def _collapse(payload: dict) -> dict:
    with _lock:
        _ensure_dir()
        since = int(payload.get("jump_since_seq", 0))
        until = int(payload.get("jump_until_seq", since + 1000000))
        jumps = _fetch_jump_ledger(since, until)

        # state_hash: 連接所有 jump 的 this_hash 做 sha256
        concat = "|".join(j.get("this_hash", "") for j in jumps) or "EMPTY"
        state_hash = hashlib.sha256(concat.encode("utf-8")).hexdigest()

        seq = _stats["collapses_total"] + 1
        collapse_id = f"collapse_{seq:010d}"

        body = {
            "jumps": jumps,
            "snapshot": {
                "node_states": payload.get("node_states", {}),
                "rhythm_pattern": [j.get("rhythm", "") for j in jumps],
            },
        }
        body_json = json.dumps(body, ensure_ascii=False).encode("utf-8")
        payload_b64 = base64.b64encode(gzip.compress(body_json)).decode("ascii")

        envelope = {
            "magic": "FLTNZ-1",
            "origin_signature": ORIGIN_SIGNATURE,
            "created_ts": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "collapse_id": collapse_id,
            "trace_window": {"jump_since_seq": since, "jump_until_seq": until},
            "manifest": {
                "jump_count": len(jumps),
                "state_hash": state_hash,
                "mother_source": payload.get("source_url", "DL580/jump_ledger"),
            },
            "payload_b64": payload_b64,
        }

        fname = f"{collapse_id}_{state_hash[:12]}.fltnz"
        fpath = MOTHER_COLLAPSE / fname
        # Additive-Only：若已存在，不覆寫，加 .dup-<ts>
        if fpath.exists():
            fpath = MOTHER_COLLAPSE / f"{collapse_id}_{state_hash[:12]}.dup-{int(time.time())}.fltnz"
        fpath.write_text(json.dumps(envelope, ensure_ascii=False, indent=1),
                         encoding="utf-8")
        inbox_paths = _mirror_to_inbox(envelope, jumps, fpath.stem)

        _stats["collapses_total"] = seq
        return {
            "collapse_id": collapse_id,
            "fltnz_path": str(fpath),
            "inbox_mirror": inbox_paths,
            "state_hash": state_hash,
            "jump_count": len(jumps),
        }


def _summary_md(envelope: dict, jumps: list) -> str:
    """給 WorldLoop 讀的可讀摘要（.md）：跳點節奏、種子、雜湊、還原入口。"""
    m = envelope["manifest"]
    lines = [
        f"# Collapse {envelope['collapse_id']} · 跳點崩解封存摘要",
        "",
        f"origin_signature: {envelope['origin_signature']}",
        f"collapse_id: {envelope['collapse_id']}",
        f"created_ts: {envelope['created_ts']}",
        f"state_hash: {m['state_hash']}",
        f"jump_count: {m['jump_count']}",
        f"trace_window: {envelope['trace_window']}",
        f"mother_source: {m.get('mother_source', '')}",
        "本體段落：Jump → Collapse（本檔）→ Trace / Replay（WorldLoop）",
        f"replay: GET http://127.0.0.1:{DEFAULT_PORT}/collapse/{envelope['collapse_id']}/replay",
        "",
        "## 跳點（Jump ledger 原序）",
        "",
        "| seq | from | to | rhythm | actor | context | this_hash |",
        "|---|---|---|---|---|---|---|",
    ]
    for j in jumps:
        ctx = json.dumps(j.get("context", {}), ensure_ascii=False)
        lines.append(f"| {j.get('ledger_seq')} | {j.get('from')} | {j.get('to')} | {j.get('rhythm')} | "
                     f"{j.get('actor')} | {ctx} | {j.get('this_hash', '')[:16]} |")
    lines += ["", f"節奏序列：{' → '.join(j.get('rhythm', '') for j in jumps)}", ""]
    return "\n".join(lines)


def _mirror_to_inbox(envelope: dict, jumps: list, base_name: str) -> list:
    """Additive-Only：已存在就不寫。回傳寫出的路徑。"""
    out = []
    day = envelope["created_ts"][:10].replace("-", "")
    stem = f"Collapse_{day}__{base_name}"
    INBOX_TOP.mkdir(parents=True, exist_ok=True)
    for ext, content in ((".fltnz", json.dumps(envelope, ensure_ascii=False, indent=1)),
                         (".md", _summary_md(envelope, jumps))):
        q = INBOX_TOP / (stem + ext)
        if not q.exists():
            q.write_text(content, encoding="utf-8")
            out.append(str(q))
    return out


def _decode_jumps(envelope: dict) -> list:
    body = json.loads(gzip.decompress(base64.b64decode(envelope["payload_b64"])).decode("utf-8"))
    return body.get("jumps", [])


def _restore_state():
    """R15-1：重啟後由既有 .fltnz 恢復序號；並把尚未鏡像到 Inbox 最上層的封存補上。"""
    _ensure_dir()
    mx = 0
    mirrored = []
    for q in sorted(MOTHER_COLLAPSE.glob("collapse_*.fltnz")):
        m = re.match(r"collapse_(\d+)_", q.name)
        if m:
            mx = max(mx, int(m.group(1)))
        try:
            env = json.loads(q.read_text(encoding="utf-8"))
            mirrored += _mirror_to_inbox(env, _decode_jumps(env), q.stem)
        except Exception as e:
            print(f"[{SERVICE_NAME}] mirror skip {q.name}: {e}", flush=True)
    _stats["collapses_total"] = mx
    _stats["mirrored_on_start"] = len(mirrored)


def _read_envelope(cid: str) -> dict | None:
    _ensure_dir()
    for p in MOTHER_COLLAPSE.glob(f"{cid}_*.fltnz"):
        return json.loads(p.read_text(encoding="utf-8"))
    return None


def _replay(cid: str) -> dict | None:
    env = _read_envelope(cid)
    if not env:
        return None
    try:
        body = json.loads(
            gzip.decompress(base64.b64decode(env["payload_b64"])).decode("utf-8")
        )
    except Exception as e:
        return {"ok": False, "error": f"decode_failed: {e}"}
    # 驗 state_hash
    concat = "|".join(j.get("this_hash", "") for j in body.get("jumps", [])) or "EMPTY"
    want = hashlib.sha256(concat.encode("utf-8")).hexdigest()
    got = env["manifest"]["state_hash"]
    return {
        "ok": want == got,
        "collapse_id": cid,
        "state_hash_match": want == got,
        "jump_count": len(body.get("jumps", [])),
        "snapshot": body.get("snapshot", {}),
    }


def _list_collapses() -> list:
    _ensure_dir()
    out = []
    for p in sorted(MOTHER_COLLAPSE.glob("collapse_*.fltnz")):
        try:
            env = json.loads(p.read_text(encoding="utf-8"))
            out.append({
                "collapse_id": env.get("collapse_id"),
                "created_ts": env.get("created_ts"),
                "state_hash": env.get("manifest", {}).get("state_hash"),
                "jump_count": env.get("manifest", {}).get("jump_count"),
                "fltnz_path": str(p),
            })
        except Exception:
            continue
    return out


_CID_RE = re.compile(r"/collapse/(collapse_\d+)/(manifest|replay)")  # 用 fullmatch，不需錨點


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
                "collapses_total": _stats["collapses_total"],
                "uptime_seconds": int(time.time() - _stats["started_at"]),
                "out_dir": str(MOTHER_COLLAPSE),
                "inbox_top": str(INBOX_TOP),
                "mirrored_on_start": _stats.get("mirrored_on_start", 0),
            })
        elif u.path == "/collapse/list":
            self._send({"ok": True, "origin_signature": ORIGIN_SIGNATURE,
                        "items": _list_collapses()})
        elif _CID_RE.fullmatch(u.path):
            m = _CID_RE.fullmatch(u.path)
            cid, action = m.group(1), m.group(2)
            if action == "manifest":
                env = _read_envelope(cid)
                if env is None:
                    self._send({"ok": False, "error": "not found"}, 404)
                    return
                env2 = {k: v for k, v in env.items() if k != "payload_b64"}
                self._send({"ok": True, "envelope": env2})
            else:  # replay
                res = _replay(cid)
                if res is None:
                    self._send({"ok": False, "error": "not found"}, 404)
                    return
                self._send(res)
        else:
            self._send({"ok": False, "error": "unknown path"}, 404)

    def do_POST(self):
        u = urlparse(self.path)
        if u.path == "/collapse":
            try:
                length = int(self.headers.get("Content-Length", "0"))
                raw = self.rfile.read(length) if length > 0 else b"{}"
                payload = json.loads(raw.decode("utf-8"))
                res = _collapse(payload)
                self._send({"ok": True, "origin_signature": ORIGIN_SIGNATURE, **res})
            except Exception as e:
                self._send({"ok": False, "error": str(e)}, 500)
        else:
            self._send({"ok": False, "error": "unknown path"}, 404)


class _ExclusiveHTTPServer(HTTPServer):
    """R13-D：禁止與其他程序共用 port。
    Python HTTPServer 預設 allow_reuse_address=1，Windows 上等於 SO_REUSEADDR，
    會讓兩個程序同時綁同一 port（2026-10-09 實機撞到 7834 MRL_Convergence_Runtime）。"""
    # R15：POSIX 的 SO_REUSEADDR 不允許兩個程序同綁，保留以避開 TIME_WAIT；Windows 改用獨占
    allow_reuse_address = (os.name != "nt")

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
    _restore_state()
    httpd = None
    for _attempt in range(37):                      # TIME_WAIT 退避：最多約 3 分鐘
        try:
            httpd = _ExclusiveHTTPServer((bind, port), _Handler)
            break
        except OSError as e:
            if _port_owner_alive(bind, port):
                print(f"[{SERVICE_NAME}] REFUSE: listener appeared on {bind}:{port}", flush=True)
                sys.exit(3)
            print(f"[{SERVICE_NAME}] bind retry {_attempt + 1}: {e}", flush=True)
            time.sleep(5)
    if httpd is None:
        sys.exit(4)
    print(f"[{SERVICE_NAME}] origin_signature={ORIGIN_SIGNATURE} "
          f"version={VERSION} bind={bind}:{port} out={MOTHER_COLLAPSE}",
          flush=True)
    httpd.serve_forever()


if __name__ == "__main__":
    port = int(os.environ.get("MRL_COLLAPSE_PORT", str(DEFAULT_PORT)))
    bind = os.environ.get("MRL_COLLAPSE_BIND", "127.0.0.1")
    serve(port, bind)
