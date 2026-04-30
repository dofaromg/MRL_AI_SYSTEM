#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
api_gateway.py — REST API Gateway
origin_signature: MrLiouWord
layer: L7 LOOP  (Platform tier)
group: Y=1 MotherCore

Industry capability: HTTP REST API gateway that exposes all MRL_AGI
                     capabilities to external clients — the same pattern used
                     by OpenAI, Anthropic, and Google to serve their AI APIs.
MRL extension: every request is wrapped in an MRL trace record stamped with
               origin_signature; responses include the request_id for auditability.

Endpoints
---------
  GET  /health                       — health check + subsystem status
  POST /chat                         — single-turn or multi-turn chat completion
  GET  /sessions                     — list conversation sessions
  POST /sessions                     — create a new session
  GET  /sessions/{id}                — get session history
  DELETE /sessions/{id}              — delete a session
  POST /agent/run                    — run an agent task
  POST /eval                         — evaluate an output string
  POST /seal                         — seal text through the reversible chain
  GET  /tools                        — list registered tools
  POST /tools/{name}                 — call a tool by name
  GET  /templates                    — list prompt templates
  POST /templates                    — add / update a template
  POST /templates/{id}/render        — render a template
  GET  /config                       — get full config (secrets masked)
  POST /config                       — set a config key

Security
--------
  If ``require_auth`` is True in config, all requests must include:
    Authorization: Bearer <auth_token>

Usage
-----
    python 09_workflow/api_gateway.py serve
    python 09_workflow/api_gateway.py serve --host 0.0.0.0 --port 7771
"""

from __future__ import annotations

import argparse
import json
import pathlib
import sys
import time
import uuid
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Dict, Optional, Tuple
from urllib.parse import urlparse

ORIGIN_SIGNATURE = "MrLiouWord"
GATEWAY_VERSION = "1.0"

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent

# ── Ensure module search paths ────────────────────────────────────────────────

def _ensure_paths() -> None:
    for sub in [
        _REPO_ROOT / "09_workflow",
        _REPO_ROOT / "03_memory" / "merkle",
        _REPO_ROOT / "03_memory" / "vector",
        _REPO_ROOT / "05_persona",
    ]:
        p = str(sub)
        if p not in sys.path:
            sys.path.insert(0, p)

_ensure_paths()


def _try_import(module: str, attr: str) -> Any:
    try:
        import importlib
        mod = importlib.import_module(module)
        return getattr(mod, attr)
    except Exception:  # noqa: BLE001
        return None


# ─── Gateway state ────────────────────────────────────────────────────────────

class _GatewayState:
    """Singleton that holds the booted MotherAssembly and config."""

    def __init__(self) -> None:
        self.assembly: Any = None
        self.cfg: Any = None
        self._booted = False

    def boot(self) -> Dict[str, Any]:
        if self._booted:
            return {"already_booted": True}

        # Config
        ConfigManager = _try_import("config_manager", "ConfigManager")
        if ConfigManager:
            self.cfg = ConfigManager()

        # MotherAssembly
        MotherAssembly = _try_import("mother_assembly", "MotherAssembly")
        if MotherAssembly:
            self.assembly = MotherAssembly()
            report = self.assembly.boot()
        else:
            report = {"error": "MotherAssembly unavailable"}

        self._booted = True
        return report

    @property
    def require_auth(self) -> bool:
        if self.cfg:
            return bool(self.cfg.get("api.require_auth", False))
        return False

    @property
    def auth_token(self) -> str:
        if self.cfg:
            return str(self.cfg.get("api.auth_token", ""))
        return ""


_STATE = _GatewayState()


# ─── JSON helpers ─────────────────────────────────────────────────────────────

def _json_response(
    handler: "BaseHTTPRequestHandler",
    status: int,
    body: Any,
    request_id: str = "",
) -> None:
    if isinstance(body, dict) and request_id:
        body["request_id"] = request_id
        body["origin_signature"] = ORIGIN_SIGNATURE
    encoded = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(encoded)))
    handler.send_header("X-Request-Id", request_id)
    handler.end_headers()
    handler.wfile.write(encoded)


def _read_json_body(handler: "BaseHTTPRequestHandler") -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    length = int(handler.headers.get("Content-Length", 0))
    if length == 0:
        return {}, None
    raw = handler.rfile.read(length)
    try:
        return json.loads(raw.decode("utf-8")), None
    except json.JSONDecodeError as exc:
        return None, f"Invalid JSON: {exc}"


def _check_auth(handler: "BaseHTTPRequestHandler") -> bool:
    if not _STATE.require_auth:
        return True
    auth = handler.headers.get("Authorization", "")
    expected = f"Bearer {_STATE.auth_token}"
    return auth == expected


# ─── Request handler ──────────────────────────────────────────────────────────

class _Handler(BaseHTTPRequestHandler):

    def log_message(self, fmt: str, *args: Any) -> None:
        # Suppress default noisy access log
        pass

    def _request_id(self) -> str:
        return str(uuid.uuid4())

    def _trace_id(self) -> str:
        return str(uuid.uuid4())

    # ── Auth gate ─────────────────────────────────────────────────────────────

    def _require_auth(self, request_id: str) -> bool:
        if not _check_auth(self):
            _json_response(self, 401, {"error": "Unauthorized"}, request_id)
            return False
        return True

    # ── Routing ───────────────────────────────────────────────────────────────

    def do_GET(self) -> None:
        rid = self._request_id()
        if not self._require_auth(rid):
            return
        path = urlparse(self.path).path.rstrip("/")
        routes: Dict[str, Any] = {
            "/health":     self._get_health,
            "/sessions":   self._get_sessions,
            "/tools":      self._get_tools,
            "/templates":  self._get_templates,
            "/config":     self._get_config,
        }
        # Dynamic route: /sessions/{id}
        if path.startswith("/sessions/"):
            self._get_session(path.split("/sessions/")[1], rid)
            return
        fn = routes.get(path)
        if fn:
            fn(rid)
        else:
            _json_response(self, 404, {"error": f"Not found: {path}"}, rid)

    def do_POST(self) -> None:
        rid = self._request_id()
        if not self._require_auth(rid):
            return
        path = urlparse(self.path).path.rstrip("/")
        body, err = _read_json_body(self)
        if err:
            _json_response(self, 400, {"error": err}, rid)
            return

        routes: Dict[str, Any] = {
            "/chat":       lambda: self._post_chat(body, rid),
            "/sessions":   lambda: self._post_sessions(body, rid),
            "/agent/run":  lambda: self._post_agent_run(body, rid),
            "/eval":       lambda: self._post_eval(body, rid),
            "/seal":       lambda: self._post_seal(body, rid),
            "/learn/ingest_path": lambda: self._post_learn_ingest_path(body, rid),
            "/learn/ingest_url":  lambda: self._post_learn_ingest_url(body, rid),
            "/learn/query":       lambda: self._post_learn_query(body, rid),
            "/templates":  lambda: self._post_templates(body, rid),
            "/config":     lambda: self._post_config(body, rid),
        }
        # Dynamic: /templates/{id}/render
        if path.startswith("/templates/") and path.endswith("/render"):
            tid = path.split("/templates/")[1].split("/render")[0]
            self._post_template_render(tid, body, rid)
            return
        # Dynamic: /tools/{name}
        if path.startswith("/tools/"):
            tname = path.split("/tools/")[1]
            self._post_tool_call(tname, body, rid)
            return

        fn = routes.get(path)
        if fn:
            fn()
        else:
            _json_response(self, 404, {"error": f"Not found: {path}"}, rid)

    def do_DELETE(self) -> None:
        rid = self._request_id()
        if not self._require_auth(rid):
            return
        path = urlparse(self.path).path.rstrip("/")
        if path.startswith("/sessions/"):
            self._delete_session(path.split("/sessions/")[1], rid)
        else:
            _json_response(self, 404, {"error": f"Not found: {path}"}, rid)

    # ── GET handlers ──────────────────────────────────────────────────────────

    def _get_health(self, rid: str) -> None:
        if _STATE.assembly:
            status = _STATE.assembly.status()
        else:
            status = {"booted": False}
        _json_response(self, 200, {"status": "ok", "gateway_version": GATEWAY_VERSION, **status}, rid)

    def _get_sessions(self, rid: str) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        _json_response(self, 200, {"sessions": mgr.list_sessions()}, rid)

    def _get_session(self, session_id: str, rid: str) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        try:
            history = mgr.get_history(session_id)
            _json_response(self, 200, {"session_id": session_id, "messages": history}, rid)
        except KeyError:
            _json_response(self, 404, {"error": f"Session not found: {session_id}"}, rid)

    def _get_tools(self, rid: str) -> None:
        if _STATE.assembly and _STATE.assembly.tool_registry:
            schemas = _STATE.assembly.tool_registry.all_schemas()
            _json_response(self, 200, {"tools": schemas}, rid)
        else:
            _json_response(self, 503, {"error": "ToolRegistry unavailable"}, rid)

    def _get_templates(self, rid: str) -> None:
        if _STATE.assembly and _STATE.assembly.template_registry:
            ids = _STATE.assembly.template_registry.list_ids()
            _json_response(self, 200, {"templates": ids}, rid)
        else:
            _json_response(self, 503, {"error": "TemplateRegistry unavailable"}, rid)

    def _get_config(self, rid: str) -> None:
        if _STATE.cfg:
            _json_response(self, 200, {"config": _STATE.cfg.dump(mask_secrets=True)}, rid)
        else:
            _json_response(self, 503, {"error": "ConfigManager unavailable"}, rid)

    # ── POST handlers ─────────────────────────────────────────────────────────

    def _post_chat(self, body: Dict[str, Any], rid: str) -> None:
        """
        Single-turn or session-based chat completion via LLMGateway.

        Request body:
          message    : str  (required) — user message
          session_id : str  (optional) — continue an existing session
          model      : str  (optional) — LLM model name (default from config)
          system     : str  (optional) — system prompt (new sessions only)
        """
        message = body.get("message", "")
        if not message:
            _json_response(self, 400, {"error": "'message' is required"}, rid)
            return

        trace_id = self._trace_id()

        if _STATE.assembly is None:
            _json_response(
                self,
                503,
                {
                    "error": "MRL runtime unavailable (MotherAssembly not booted)",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        requested_model = str(body.get("model") or "").strip() or None
        cfg_default_model = (
            str(_STATE.cfg.get("llm.default_model", "")) if _STATE.cfg else ""
        ).strip() or None
        allow_mock = bool(_STATE.cfg.get("llm.allow_mock", False)) if _STATE.cfg else False

        if requested_model is None:
            if cfg_default_model is None:
                _json_response(
                    self,
                    400,
                    {
                        "error": "'model' is required unless llm.default_model is configured",
                        "engine": "mrl_runtime",
                        "runtime_origin": "local_mother_assembly",
                        "trace_id": trace_id,
                    },
                    rid,
                )
                return
            requested_model = cfg_default_model

        if requested_model.startswith("mock") and not allow_mock:
            _json_response(
                self,
                403,
                {
                    "error": "MockAdapter is test-only. Set llm.allow_mock=true to enable.",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        session_id = body.get("session_id")
        system_prompt = body.get("system", "")
        max_tokens = int(body.get("max_tokens", 1024))
        temperature = float(body.get("temperature", 0.7))

        try:
            result = _STATE.assembly.chat(
                message,
                session_id=session_id or None,
                model=requested_model,
                system_prompt=system_prompt or None,
                max_tokens=max_tokens,
                temperature=temperature,
            )
        except Exception as exc:  # noqa: BLE001
            _json_response(
                self,
                500,
                {
                    "error": "MRL runtime error",
                    "error_type": type(exc).__name__,
                    "error_detail": str(exc),
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        if isinstance(result, dict) and result.get("error"):
            _json_response(
                self,
                502,
                {
                    **result,
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        _json_response(
            self,
            200,
            {
                **(result if isinstance(result, dict) else {"result": result}),
                "engine": "mrl_runtime",
                "runtime_origin": "local_mother_assembly",
                "trace_id": trace_id,
            },
            rid,
        )

    def _post_sessions(self, body: Dict[str, Any], rid: str) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        system = body.get("system_prompt", "")
        label = body.get("label", "")
        sid = mgr.new_session(system_prompt=system, label=label)
        _json_response(self, 201, {"session_id": sid, "label": label}, rid)

    def _delete_session(self, session_id: str, rid: str) -> None:
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        ok = mgr.delete_session(session_id)
        if ok:
            _json_response(self, 200, {"deleted": session_id}, rid)
        else:
            _json_response(self, 404, {"error": f"Session not found: {session_id}"}, rid)

    def _post_agent_run(self, body: Dict[str, Any], rid: str) -> None:
        goal = body.get("goal", "")
        if not goal:
            _json_response(self, 400, {"error": "'goal' is required"}, rid)
            return

        trace_id = self._trace_id()
        if _STATE.assembly is None:
            _json_response(
                self,
                503,
                {
                    "error": "MotherAssembly unavailable",
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                },
                rid,
            )
            return

        # This endpoint is the product-grade task orchestrator entry.
        # For now we run synchronously but return a formal task envelope.
        task_id = str(uuid.uuid4())
        started_ms = int(time.time() * 1000)
        try:
            status = "RUNNING"
            result = _STATE.assembly.run_agent(goal)
            status = "DONE" if not (isinstance(result, dict) and result.get("error")) else "FAILED"
            ended_ms = int(time.time() * 1000)
            _json_response(
                self,
                200,
                {
                    "task_id": task_id,
                    "status": status,
                    "result": result,
                    "error_trace": result.get("error") if isinstance(result, dict) else None,
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                    "started_at_ms": started_ms,
                    "ended_at_ms": ended_ms,
                    "elapsed_ms": ended_ms - started_ms,
                },
                rid,
            )
        except Exception as exc:  # noqa: BLE001
            ended_ms = int(time.time() * 1000)
            _json_response(
                self,
                500,
                {
                    "task_id": task_id,
                    "status": "FAILED",
                    "result": None,
                    "error_trace": {
                        "error": str(exc),
                        "error_type": type(exc).__name__,
                    },
                    "engine": "mrl_runtime",
                    "runtime_origin": "local_mother_assembly",
                    "trace_id": trace_id,
                    "started_at_ms": started_ms,
                    "ended_at_ms": ended_ms,
                    "elapsed_ms": ended_ms - started_ms,
                },
                rid,
            )

    def _post_eval(self, body: Dict[str, Any], rid: str) -> None:
        output = body.get("output", "")
        if not output:
            _json_response(self, 400, {"error": "'output' is required"}, rid)
            return
        keywords = body.get("keywords", [])
        if _STATE.assembly:
            result = _STATE.assembly.evaluate(output, keywords=keywords)
            _json_response(self, 200, result, rid)
        else:
            _json_response(self, 503, {"error": "MotherAssembly unavailable"}, rid)

    def _post_seal(self, body: Dict[str, Any], rid: str) -> None:
        text = body.get("text", "")
        label = body.get("label", "api")
        if not text:
            _json_response(self, 400, {"error": "'text' is required"}, rid)
            return
        if _STATE.assembly:
            trace = _STATE.assembly.seal_text(text, label=label)
            _json_response(self, 200, trace, rid)
        else:
            _json_response(self, 503, {"error": "MotherAssembly unavailable"}, rid)

    def _post_learn_ingest_path(self, body: Dict[str, Any], rid: str) -> None:
        Learner = _try_import("MRL_learning_ingest", "ingest_path")
        if Learner is None:
            _json_response(self, 503, {"error": "Learning ingest unavailable"}, rid)
            return
        path = str(body.get("path") or "").strip()
        if not path:
            _json_response(self, 400, {"error": "path is required"}, rid)
            return
        label = str(body.get("label") or "")
        chunk_chars = int(body.get("chunk_chars") or 1400)
        overlap = int(body.get("overlap") or 200)
        store_raw = bool(body.get("store_raw", True))
        res = Learner(path, label=label, chunk_chars=chunk_chars, overlap=overlap, store_raw=store_raw)
        status = 200 if res.get("ok") else 400
        _json_response(self, status, res, rid)

    def _post_learn_ingest_url(self, body: Dict[str, Any], rid: str) -> None:
        Learner = _try_import("MRL_learning_ingest", "ingest_url")
        if Learner is None:
            _json_response(self, 503, {"error": "Learning ingest unavailable"}, rid)
            return
        url = str(body.get("url") or "").strip()
        if not url:
            _json_response(self, 400, {"error": "url is required"}, rid)
            return
        label = str(body.get("label") or "")
        chunk_chars = int(body.get("chunk_chars") or 1400)
        overlap = int(body.get("overlap") or 200)
        store_raw = bool(body.get("store_raw", True))
        timeout_s = int(body.get("timeout_s") or 15)
        res = Learner(url, label=label, chunk_chars=chunk_chars, overlap=overlap, store_raw=store_raw, timeout_s=timeout_s)
        status = 200 if res.get("ok") else 400
        _json_response(self, status, res, rid)

    def _post_learn_query(self, body: Dict[str, Any], rid: str) -> None:
        Learner = _try_import("MRL_learning_ingest", "query")
        if Learner is None:
            _json_response(self, 503, {"error": "Learning query unavailable"}, rid)
            return
        q = str(body.get("q") or "").strip()
        if not q:
            _json_response(self, 400, {"error": "q is required"}, rid)
            return
        k = int(body.get("k") or 5)
        res = Learner(q, k=k)
        status = 200 if res.get("ok") else 400
        _json_response(self, status, res, rid)

    def _post_tool_call(self, tool_name: str, body: Dict[str, Any], rid: str) -> None:
        if _STATE.assembly and _STATE.assembly.tool_registry:
            result = _STATE.assembly.tool_registry.call(tool_name, body)
            _json_response(self, 200, result, rid)
        else:
            _json_response(self, 503, {"error": "ToolRegistry unavailable"}, rid)

    def _post_templates(self, body: Dict[str, Any], rid: str) -> None:
        tid = body.get("id", "")
        text = body.get("text", "")
        desc = body.get("description", "")
        if not tid or not text:
            _json_response(self, 400, {"error": "'id' and 'text' are required"}, rid)
            return
        if _STATE.assembly and _STATE.assembly.template_registry:
            t = _STATE.assembly.template_registry.add(tid, text, desc)
            _json_response(self, 201, t.to_dict(), rid)
        else:
            _json_response(self, 503, {"error": "TemplateRegistry unavailable"}, rid)

    def _post_template_render(self, tid: str, body: Dict[str, Any], rid: str) -> None:
        variables = body.get("variables", {})
        if _STATE.assembly and _STATE.assembly.template_registry:
            try:
                rec = _STATE.assembly.template_registry.render_record(tid, variables)
                _json_response(self, 200, rec, rid)
            except KeyError as exc:
                _json_response(self, 404, {"error": str(exc)}, rid)
        else:
            _json_response(self, 503, {"error": "TemplateRegistry unavailable"}, rid)

    def _post_config(self, body: Dict[str, Any], rid: str) -> None:
        key = body.get("key", "")
        value = body.get("value")
        if not key:
            _json_response(self, 400, {"error": "'key' is required"}, rid)
            return
        if _STATE.cfg:
            _STATE.cfg.set(key, value)
            _STATE.cfg.save()
            _json_response(self, 200, {"key": key, "value": value}, rid)
        else:
            _json_response(self, 503, {"error": "ConfigManager unavailable"}, rid)


# ─── Server entry point ───────────────────────────────────────────────────────

def serve(host: str = "127.0.0.1", port: int = 7771) -> None:
    """Boot the MotherAssembly and start the HTTP server."""
    print(f"[MRL_AGI API] Booting MotherAssembly…")
    boot_report = _STATE.boot()
    ok_count = sum(1 for v in boot_report.get("subsystems", {}).values() if v == "ok")
    total = len(boot_report.get("subsystems", {}))
    print(f"[MRL_AGI API] Subsystems online: {ok_count}/{total}")
    print(f"[MRL_AGI API] Listening on http://{host}:{port}")
    print(f"[MRL_AGI API] origin_signature: {ORIGIN_SIGNATURE}")
    print(f"[MRL_AGI API] Press Ctrl+C to stop.\n")

    server = ThreadingHTTPServer((host, port), _Handler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\n[MRL_AGI API] Shutting down.")
        server.shutdown()


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="api_gateway — MRL_AGI REST API gateway",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Endpoints:
  GET  /health
  POST /chat              {"message": "...", "session_id": "...", "model": "..."}
  GET  /sessions
  POST /sessions          {"system_prompt": "...", "label": "..."}
  GET  /sessions/{id}
  DELETE /sessions/{id}
  POST /agent/run         {"goal": "..."}
  POST /eval              {"output": "...", "keywords": [...]}
  POST /seal              {"text": "...", "label": "..."}
  GET  /tools
  POST /tools/{name}      {<kwargs>}
  GET  /templates
  POST /templates         {"id": "...", "text": "...", "description": "..."}
  POST /templates/{id}/render  {"variables": {...}}
  GET  /config
  POST /config            {"key": "...", "value": ...}
""",
    )
    p.add_argument("--host", default="127.0.0.1")
    p.add_argument("--port", type=int, default=7771)
    return p


def main() -> None:
    args = _build_argparser().parse_args()
    serve(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
