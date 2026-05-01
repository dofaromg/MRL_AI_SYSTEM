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
  POST /chat/stream                  — SSE streaming chat completion
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
  GET  /metrics                      — MRL_metrics telemetry snapshot
  POST /guard                        — run guardrail check on text
  POST /export/{sid}                 — export session as Markdown

Security
--------
  If ``require_auth`` is True in config, all requests must include:
    Authorization: Bearer <auth_token>
  Rate limiting:
    Configure api.rate_limit_per_minute (0 = disabled) in config.

CORS
----
  All responses include Access-Control-* headers.
  Allowed origins configured via api.cors_origins (default ["*"]).

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
from typing import Any, Dict, List, Optional, Tuple
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


# ─── CORS helpers ─────────────────────────────────────────────────────────────

def _cors_origins() -> List[str]:
    """Return the list of allowed CORS origins from config."""
    if _STATE.cfg:
        val = _STATE.cfg.get("api.cors_origins", ["*"])
        if isinstance(val, list):
            return val
        return [str(val)]
    return ["*"]


def _add_cors_headers(handler: "BaseHTTPRequestHandler") -> None:
    """Add Access-Control-* headers to the response."""
    origins = _cors_origins()
    raw_origin = handler.headers.get("Origin", "")
    # Sanitise: strip CR/LF to prevent HTTP response-splitting injection
    origin = raw_origin.replace("\r", "").replace("\n", "").strip()
    if "*" in origins:
        handler.send_header("Access-Control-Allow-Origin", "*")
    elif origin and origin in origins:
        handler.send_header("Access-Control-Allow-Origin", origin)
    handler.send_header(
        "Access-Control-Allow-Methods",
        "GET, POST, DELETE, OPTIONS",
    )
    handler.send_header(
        "Access-Control-Allow-Headers",
        "Content-Type, Authorization, X-Request-Id",
    )
    handler.send_header("Access-Control-Max-Age", "86400")


# ─── Rate-limit helper ────────────────────────────────────────────────────────

def _get_client_key(handler: "BaseHTTPRequestHandler") -> str:
    """Derive a client key for rate limiting (IP or auth token)."""
    by = "ip"
    if _STATE.cfg:
        by = str(_STATE.cfg.get("api.rate_limit_by", "ip"))
    if by == "token":
        auth = handler.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            return auth[7:]
    # Fallback to IP
    return handler.client_address[0]


def _check_rate_limit(handler: "BaseHTTPRequestHandler", request_id: str) -> bool:
    """Return True if the request is allowed; send 429 and return False if throttled."""
    RateLimiter = _try_import("MRL_rate_limiter", "get_limiter")
    if RateLimiter is None:
        return True
    limiter = RateLimiter()
    key = _get_client_key(handler)
    allowed, info = limiter.check(key)
    if not allowed:
        retry_after = info.get("retry_after_s") or 60
        body: Dict[str, Any] = {
            "error": "Too Many Requests",
            "retry_after_s": retry_after,
            "limit": info.get("limit"),
            "window_seconds": info.get("window_seconds"),
        }
        encoded = json.dumps(body, ensure_ascii=False, default=str).encode("utf-8")
        handler.send_response(429)
        handler.send_header("Content-Type", "application/json; charset=utf-8")
        handler.send_header("Content-Length", str(len(encoded)))
        handler.send_header("Retry-After", str(int(retry_after) + 1))
        handler.send_header("X-Request-Id", request_id)
        _add_cors_headers(handler)
        handler.end_headers()
        handler.wfile.write(encoded)
        return False
    return True


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
    _add_cors_headers(handler)
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

    # ── CORS preflight ────────────────────────────────────────────────────────

    def do_OPTIONS(self) -> None:
        rid = self._request_id()
        self.send_response(204)
        _add_cors_headers(self)
        self.send_header("Content-Length", "0")
        self.send_header("X-Request-Id", rid)
        self.end_headers()

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
        if not _check_rate_limit(self, rid):
            return
        path = urlparse(self.path).path.rstrip("/")
        routes: Dict[str, Any] = {
            "/health":     self._get_health,
            "/sessions":   self._get_sessions,
            "/tools":      self._get_tools,
            "/templates":  self._get_templates,
            "/config":     self._get_config,
            "/metrics":    self._get_metrics,
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
        if not _check_rate_limit(self, rid):
            return
        path = urlparse(self.path).path.rstrip("/")
        body, err = _read_json_body(self)
        if err:
            _json_response(self, 400, {"error": err}, rid)
            return

        routes: Dict[str, Any] = {
            "/chat":       lambda: self._post_chat(body, rid),
            "/chat/stream": lambda: self._post_chat_stream(body, rid),
            "/sessions":   lambda: self._post_sessions(body, rid),
            "/agent/run":  lambda: self._post_agent_run(body, rid),
            "/eval":       lambda: self._post_eval(body, rid),
            "/seal":       lambda: self._post_seal(body, rid),
            "/templates":  lambda: self._post_templates(body, rid),
            "/config":     lambda: self._post_config(body, rid),
            "/guard":      lambda: self._post_guard(body, rid),
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
        # Dynamic: /export/{sid}
        if path.startswith("/export/"):
            sid = path.split("/export/")[1]
            self._post_export(sid, rid)
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
        if not _check_rate_limit(self, rid):
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

    def _get_metrics(self, rid: str) -> None:
        """Return the current MRL_metrics snapshot."""
        metrics_snapshot = _try_import("MRL_metrics", "snapshot")
        if metrics_snapshot:
            _json_response(self, 200, {"metrics": metrics_snapshot()}, rid)
        else:
            _json_response(self, 503, {"error": "MRL_metrics unavailable"}, rid)

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

        LLMGateway = _try_import("llm_adapter", "LLMGateway")
        LLMRequest = _try_import("llm_adapter", "LLMRequest")
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        CtxMgr = _try_import("context_manager", "ContextManager")

        model = body.get("model") or (
            _STATE.cfg.get("llm.default_model", "mock") if _STATE.cfg else "mock"
        )

        # Build or retrieve session
        session_id = body.get("session_id")
        if ConvMgr:
            mgr = ConvMgr()
            if not session_id:
                system = body.get("system", "")
                if not system and _STATE.cfg:
                    system = _STATE.cfg.get(
                        "conversation.default_system_prompt",
                        "You are MRL_AGI, a helpful AI assistant.",
                    )
                session_id = mgr.new_session(system_prompt=system)
            try:
                mgr.add_message(session_id, "user", message)
                history = mgr.get_history(session_id)
            except KeyError:
                _json_response(self, 404, {"error": f"Session not found: {session_id}"}, rid)
                return
        else:
            history = [{"role": "user", "content": message}]

        # Trim context
        if CtxMgr and _STATE.cfg:
            max_tok = int(_STATE.cfg.get("context.max_tokens", 4096))
            reserve = int(_STATE.cfg.get("context.reply_reserve", 512))
            cm = CtxMgr(max_tokens=max_tok, reply_reserve=reserve)
            history, _ = cm.fit(history)

        # LLM call
        reply_text = f"[MockAdapter] Echo: {message}"
        if LLMGateway and LLMRequest:
            gw = LLMGateway()
            req = LLMRequest(
                model=model,
                messages=[{"role": m["role"], "content": m["content"]} for m in history],
                max_tokens=int(body.get("max_tokens", 1024)),
                temperature=float(body.get("temperature", 0.7)),
            )
            resp = gw.complete(req)
            reply_text = resp.text if resp.ok else f"[LLM Error] {resp.error}"

        # Record assistant reply
        if ConvMgr and session_id:
            mgr.add_message(session_id, "assistant", reply_text)

        _json_response(self, 200, {
            "session_id": session_id,
            "reply": reply_text,
            "model": model,
        }, rid)

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
        if _STATE.assembly:
            result = _STATE.assembly.run_agent(goal)
            _json_response(self, 200, result, rid)
        else:
            _json_response(self, 503, {"error": "MotherAssembly unavailable"}, rid)

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

    def _post_guard(self, body: Dict[str, Any], rid: str) -> None:
        """
        Run guardrail checks on arbitrary text.

        Request body:
          text    : str   (required) — text to check
          stage   : str   (optional) — "input" | "output" (default "input")
          policy  : str   (optional) — "standard" | "strict" | "permissive"
        """
        text = body.get("text", "")
        if not text:
            _json_response(self, 400, {"error": "'text' is required"}, rid)
            return
        stage = body.get("stage", "input")
        policy = body.get("policy", "standard")

        InputGuardrail = _try_import("guardrail", "InputGuardrail")
        OutputGuardrail = _try_import("guardrail", "OutputGuardrail")

        if stage == "output" and OutputGuardrail:
            g = OutputGuardrail(policy)
            ok, violations = g.check(text)
        elif InputGuardrail:
            g = InputGuardrail(policy)
            ok, violations = g.check(text)
        else:
            _json_response(self, 503, {"error": "Guardrail unavailable"}, rid)
            return

        _json_response(self, 200, {
            "ok": ok,
            "stage": stage,
            "policy": policy,
            "violations": violations,
        }, rid)

    def _post_export(self, session_id: str, rid: str) -> None:
        """
        Export a conversation session as Markdown.

        URL: POST /export/{session_id}
        Response: plain Markdown text in the JSON field "markdown".
        """
        ConvMgr = _try_import("conversation_manager", "ConversationManager")
        if ConvMgr is None:
            _json_response(self, 503, {"error": "ConversationManager unavailable"}, rid)
            return
        mgr = ConvMgr()
        md = mgr.export_markdown(session_id)
        if not md:
            _json_response(self, 404, {"error": f"Session not found: {session_id}"}, rid)
            return
        _json_response(self, 200, {"session_id": session_id, "markdown": md}, rid)

    def _post_chat_stream(self, body: Dict[str, Any], rid: str) -> None:
        """
        Streaming chat completion via Server-Sent Events (SSE).

        Request body:
          message    : str  (required)
          session_id : str  (optional)
          model      : str  (optional)
          system     : str  (optional)
          max_tokens : int  (optional, default 1024)

        Response: text/event-stream
          data: {"chunk": "<token_text>"}\n\n
          ...
          data: [DONE]\n\n
        """
        message = body.get("message", "")
        if not message:
            _json_response(self, 400, {"error": "'message' is required"}, rid)
            return

        model = body.get("model") or (
            _STATE.cfg.get("llm.default_model", "mock") if _STATE.cfg else "mock"
        )
        system = body.get("system", "")
        if not system and _STATE.cfg:
            system = _STATE.cfg.get(
                "conversation.default_system_prompt",
                "You are MRL_AGI, a helpful AI assistant.",
            )

        messages: List[Dict[str, Any]] = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": message})

        LLMGateway = _try_import("llm_gateway", "LLMGateway")
        max_tokens = int(body.get("max_tokens", 1024))

        # Send SSE response headers
        self.send_response(200)
        self.send_header("Content-Type", "text/event-stream; charset=utf-8")
        self.send_header("Cache-Control", "no-cache")
        self.send_header("X-Accel-Buffering", "no")
        self.send_header("X-Request-Id", rid)
        _add_cors_headers(self)
        self.end_headers()

        def _send_chunk(data: str) -> None:
            line = f"data: {data}\n\n"
            self.wfile.write(line.encode("utf-8"))
            self.wfile.flush()

        try:
            if LLMGateway:
                gw = LLMGateway(model=model if model != "mock" else None)
                for chunk in gw.stream_chat(messages, max_tokens=max_tokens):
                    payload = json.dumps({"chunk": chunk}, ensure_ascii=False)
                    _send_chunk(payload)
            else:
                payload = json.dumps(
                    {"chunk": f"[MockAdapter] Echo: {message}"},
                    ensure_ascii=False,
                )
                _send_chunk(payload)
            _send_chunk("[DONE]")
        except BrokenPipeError:
            pass  # client disconnected — normal for SSE


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
