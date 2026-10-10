#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Additive MCP HTTP/SSE transport for the existing MRL registry and policy gate.

origin_signature: MrLiouWord
derives_from: MRL_MCPServerHarness_Streamable_v1.py at
  dofaromg/MRL_AI_SYSTEM@3c51612c2ddee1b3c561882c20474694dc497792
The v1 source remains unchanged. This module has no third-party runtime dependency.

POST /mcp (and /) implements stateless Streamable HTTP, negotiating 2025-03-26.
GET /sse + POST /messages?session_id=... implements legacy HTTP+SSE.
Only the CLI demo registers echo. Importing this module does not boot MotherAssembly,
run DL580 commands, read user files, or provision services.

Limits bound request/response bytes, SSE sessions/queues, and HTTP connections.
Close/shutdown disconnects streams and idle sockets. Arbitrary registered synchronous
tools must provide their own cancellation/timeout; Python cannot forcibly stop them.
"""
from __future__ import annotations

import argparse
import hmac
import ipaddress
import json
import os
import queue
import secrets
import socket
import threading
import time
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from typing import Any, Optional
from urllib.parse import parse_qs, urlsplit

from MRL_MCPServerHarness_Streamable_v1 import (
    MCPStreamableServer as _V1Server,
    JsonRpcError,
    make_content,
)
from MRL_utils import ORIGIN_SIGNATURE

PROTOCOL_VERSION = "2025-03-26"
SERVER_NAME = "MRL_MCPServerHarness_Streamable"
SERVER_VERSION = "2.0.0"


@dataclass(frozen=True)
class TransportLimits:
    max_body_bytes: int = 262144
    max_response_bytes: int = 262144
    max_batch_messages: int = 16
    max_sse_sessions: int = 8
    max_queue_events: int = 16
    max_http_connections: int = 32
    socket_timeout: float = 10.0
    heartbeat_seconds: float = 5.0
    session_idle_seconds: float = 300.0

    def __post_init__(self) -> None:
        for field in self.__dataclass_fields__:
            if getattr(self, field) <= 0:
                raise ValueError(f"{field} must be positive")
        if self.max_response_bytes < 256:
            raise ValueError("max_response_bytes must be at least 256")
        if self.max_http_connections <= self.max_sse_sessions:
            raise ValueError("reserve HTTP connections for POST requests")


class MCPStreamableServerV2(_V1Server):
    """Reuse v1 tool registration/execution/policy; correct the transport contract."""

    def __init__(self, server_name: str = SERVER_NAME,
                 server_version: str = SERVER_VERSION,
                 tool_loop: Any = None, policy_gate: Any = None) -> None:
        super().__init__(server_name, server_version, tool_loop, policy_gate)
        # The old HTTP server serialized execution. Preserve that behavior even
        # when SSE now requires several concurrent HTTP handlers.
        self._tool_call_lock = threading.RLock()

    def _on_initialize(self, params: dict) -> dict:
        return {
            "protocolVersion": PROTOCOL_VERSION,
            "capabilities": {"tools": {}},
            "serverInfo": {
                "name": self.server_name, "version": self.server_version,
                "originSignature": ORIGIN_SIGNATURE,
                "origin_signature": ORIGIN_SIGNATURE,
            },
        }

    def _on_tools_call(self, params: dict) -> dict:
        if "arguments" in params and not isinstance(params["arguments"], dict):
            raise JsonRpcError(-32602, "tools/call arguments must be an object")
        with self._tool_call_lock:
            try:
                result = super()._on_tools_call(params)
            except JsonRpcError as exc:
                if exc.code != -32003:
                    raise
                # Tool execution failures are tool results, not protocol failures.
                return {**make_content("tool execution failed"), "isError": True}
        result = dict(result)
        result.setdefault("isError", False)
        return result

    def handle_message(self, message: Any) -> Optional[dict]:
        rid = message.get("id") if isinstance(message, dict) else None
        if not (rid is None or isinstance(rid, (str, int))) or isinstance(rid, bool):
            rid = None
        if (not isinstance(message, dict) or message.get("jsonrpc") != "2.0"
                or not isinstance(message.get("method"), str)
                or not message["method"]
                or ("id" in message and (
                    message["id"] is None or isinstance(message["id"], bool)
                    or not isinstance(message["id"], (str, int))))):
            return self._error_response(rid, -32600, "invalid JSON-RPC request")
        notification = "id" not in message
        params = message.get("params", {})
        if not isinstance(params, dict):
            return None if notification else self._error_response(
                rid, -32602, "params must be an object")
        try:
            method = message["method"]
            if method == "initialize":
                result = self._on_initialize(params)
            elif method in ("notifications/initialized", "initialized"):
                result = {}
            elif method == "ping":
                result = {}
            elif method == "tools/list":
                result = self._on_tools_list()
            elif method == "tools/call":
                result = self._on_tools_call(params)
            else:
                raise JsonRpcError(-32601, "method not found")
        except JsonRpcError as exc:
            return None if notification else self._error_response(
                rid, exc.code, exc.message, exc.data)
        except Exception:
            return None if notification else self._error_response(
                rid, -32603, "internal error")
        return None if notification else {"jsonrpc": "2.0", "id": rid, "result": result}


class _SSESession:
    def __init__(self, connection: socket.socket, limit: int) -> None:
        self.token = secrets.token_urlsafe(32)
        self.connection = connection
        self.events: queue.Queue[bytes] = queue.Queue(maxsize=limit)
        self.closed = threading.Event()
        self.work_lock = threading.Lock()
        self.last_activity = time.monotonic()

    def close(self) -> None:
        self.closed.set()
        try:
            self.connection.shutdown(socket.SHUT_RDWR)
        except OSError:
            pass


class _HTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    block_on_close = False

    def __init__(self, address: tuple, mcp: MCPStreamableServerV2,
                 limits: TransportLimits, api_key: Optional[str],
                 allowed_origins: tuple[str, ...], allowed_hosts: tuple[str, ...]):
        super().__init__(address, _RequestHandler)
        self.mcp = mcp
        self.limits = limits
        self.api_key = api_key
        self.allowed_origins = frozenset(allowed_origins)
        host, port = self.server_address[:2]
        defaults = {f"{host}:{port}", f"localhost:{port}"}
        self.allowed_hosts = frozenset(allowed_hosts) | defaults
        self.closed = threading.Event()
        self._sessions: dict[str, _SSESession] = {}
        self._sessions_lock = threading.Lock()
        self._connections: set[socket.socket] = set()
        self._connections_lock = threading.Lock()
        self._slots = threading.BoundedSemaphore(limits.max_http_connections)

    def process_request(self, request, client_address) -> None:
        if self.closed.is_set() or not self._slots.acquire(blocking=False):
            # No worker thread or request body is allocated when capacity is full.
            try:
                request.settimeout(0.2)
                request.sendall(
                    b"HTTP/1.1 503 Service Unavailable\r\n"
                    b"Content-Length: 0\r\nConnection: close\r\n\r\n")
            except OSError:
                pass
            self.shutdown_request(request)
            return
        with self._connections_lock:
            self._connections.add(request)
        try:
            super().process_request(request, client_address)
        except Exception:
            with self._connections_lock:
                self._connections.discard(request)
            self._slots.release()
            raise

    def process_request_thread(self, request, client_address) -> None:
        try:
            super().process_request_thread(request, client_address)
        finally:
            with self._connections_lock:
                self._connections.discard(request)
            self._slots.release()

    @property
    def active_sessions(self) -> int:
        with self._sessions_lock:
            return len(self._sessions)

    @property
    def active_connections(self) -> int:
        with self._connections_lock:
            return len(self._connections)

    def add_session(self, connection: socket.socket) -> Optional[_SSESession]:
        with self._sessions_lock:
            if self.closed.is_set() or len(self._sessions) >= self.limits.max_sse_sessions:
                return None
            session = _SSESession(connection, self.limits.max_queue_events)
            self._sessions[session.token] = session
            return session

    def get_session(self, token: str) -> Optional[_SSESession]:
        with self._sessions_lock:
            session = self._sessions.get(token)
            return session if session and not session.closed.is_set() else None

    def drop_session(self, token: str) -> None:
        with self._sessions_lock:
            session = self._sessions.pop(token, None)
        if session is not None:
            session.close()

    def close_connections(self) -> None:
        self.closed.set()
        with self._sessions_lock:
            sessions = list(self._sessions.values())
            self._sessions.clear()
        for session in sessions:
            session.close()
        with self._connections_lock:
            sockets = list(self._connections)
        for connection in sockets:
            try:
                connection.shutdown(socket.SHUT_RDWR)
            except OSError:
                pass

    def server_close(self) -> None:
        self.close_connections()
        super().server_close()


class _RequestHandler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"
    server_version = "MRL_MCP/2.0.0"
    sys_version = ""

    def setup(self) -> None:
        super().setup()
        self.connection.settimeout(self.server.limits.socket_timeout)

    def log_message(self, format: str, *args: Any) -> None:
        # Never log request URLs, authentication headers, or tool content.
        return

    def _send(self, status: int, payload: Optional[Any] = None,
              headers: Optional[dict] = None) -> None:
        data = b"" if payload is None else json.dumps(
            payload, ensure_ascii=False, allow_nan=False,
            separators=(",", ":")).encode("utf-8")
        self.send_response(status)
        if payload is not None:
            self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.send_header("Connection", "close")
        for key, value in (headers or {}).items():
            self.send_header(key, value)
        self.end_headers()
        self.close_connection = True
        if data:
            self.wfile.write(data)

    def _access(self) -> bool:
        if self.server.closed.is_set():
            self._send(503)
            return False
        host_values = self.headers.get_all("Host") or []
        if len(host_values) != 1 or host_values[0] not in self.server.allowed_hosts:
            self._send(403)
            return False
        origin = self.headers.get("Origin")
        if origin is not None and origin not in self.server.allowed_origins:
            self._send(403)
            return False
        expected = self.server.api_key
        keys = self.headers.get_all("x-api-key") or []
        if expected and (len(keys) != 1 or not hmac.compare_digest(
                keys[0].encode("utf-8"), expected.encode("utf-8"))):
            self._send(401)
            return False
        return True

    def _target(self):
        target = urlsplit(self.path)
        if target.scheme or target.netloc or target.fragment:
            return None
        return target

    def _session_token(self, target) -> Optional[str]:
        try:
            fields = parse_qs(target.query, strict_parsing=True, max_num_fields=1)
        except ValueError:
            return None
        values = fields.get("session_id")
        return values[0] if values and len(values) == 1 else None

    def _read_message(self):
        lengths = self.headers.get_all("Content-Length") or []
        if self.headers.get("Transfer-Encoding") is not None:
            self._send(400)
            return False, None
        if not lengths:
            self._send(411)
            return False, None
        if len(lengths) != 1 or not lengths[0].isascii() or not lengths[0].isdigit():
            self._send(400)
            return False, None
        length = int(lengths[0])
        if length > self.server.limits.max_body_bytes:
            self._send(413)
            return False, None
        media_type = self.headers.get("Content-Type", "").split(";", 1)[0].strip().lower()
        if media_type != "application/json":
            self._send(415)
            return False, None
        try:
            raw = self.rfile.read(length)
            if len(raw) != length:
                self._send(400)
                return False, None
            message = json.loads(raw.decode("utf-8"),
                                 parse_constant=lambda value: (_ for _ in ()).throw(
                                     ValueError("non-finite JSON number")))
        except (OSError, UnicodeError, ValueError):
            self._send(400, self.server.mcp._error_response(None, -32700, "parse error"))
            return False, None
        if isinstance(message, list) and len(message) > self.server.limits.max_batch_messages:
            self._send(413)
            return False, None
        return True, message

    @staticmethod
    def _messages(message: Any) -> list:
        # Empty batch is one invalid request, not an empty notification group.
        return message if isinstance(message, list) and message else [message]

    @staticmethod
    def _expects_response(message: Any) -> bool:
        return not (isinstance(message, dict) and message.get("jsonrpc") == "2.0"
                    and isinstance(message.get("method"), str)
                    and message["method"] and "id" not in message)

    def _dispatch(self, message: Any) -> list[dict]:
        return [response for item in self._messages(message)
                if (response := self.server.mcp.handle_message(item)) is not None]

    def _wire(self, response: Any) -> bytes:
        try:
            data = json.dumps(response, ensure_ascii=False, allow_nan=False,
                              separators=(",", ":")).encode("utf-8")
        except (TypeError, ValueError):
            data = b""
        if not data or len(data) > self.server.limits.max_response_bytes:
            rid = response.get("id") if isinstance(response, dict) else None
            # A caller-provided id is itself bounded before request execution below.
            data = json.dumps(self.server.mcp._error_response(
                rid, -32603, "response exceeds transport limit"),
                separators=(",", ":")).encode("utf-8")
        return data

    def do_POST(self) -> None:
        try:
            if not self._access():
                return
            target = self._target()
            if target is None or target.path not in ("/", "/mcp", "/messages"):
                self._send(404)
                return
            if self.headers.get("MCP-Protocol-Version", PROTOCOL_VERSION) != PROTOCOL_VERSION:
                self._send(400)
                return
            session = None
            if target.path == "/messages":
                token = self._session_token(target)
                session = self.server.get_session(token) if token else None
                if session is None:
                    self._send(404)
                    return
            ok, message = self._read_message()
            if not ok:
                return
            # Prevent an enormous echoed request id from evading the output cap.
            if any(isinstance(item, dict) and len(json.dumps(item.get("id"))) > 128
                   for item in self._messages(message)):
                self._send(400)
                return
            if session is None:
                responses = self._dispatch(message)
                if not responses:
                    self._send(202)
                else:
                    response = responses if isinstance(message, list) and message else responses[0]
                    self._send(200, json.loads(self._wire(response)))
                return
            with session.work_lock:
                if session.closed.is_set():
                    self._send(404)
                    return
                needed = sum(self._expects_response(item) for item in self._messages(message))
                if needed > session.events.maxsize - session.events.qsize():
                    # Check before invoking any tool; a full queue cannot cause a
                    # tool to execute and then receive a retryable delivery error.
                    self._send(429, headers={"Retry-After": "1"})
                    return
                session.last_activity = time.monotonic()
                for response in self._dispatch(message):
                    session.events.put_nowait(self._wire(response))
            self._send(202)
        except (BrokenPipeError, ConnectionResetError, TimeoutError, socket.timeout):
            self.close_connection = True

    def do_GET(self) -> None:
        if not self._access():
            return
        target = self._target()
        if target is None:
            self._send(404)
            return
        if target.path == "/health":
            self._send(200, {
                "status": "PASS", "origin_signature": ORIGIN_SIGNATURE,
                "server_name": self.server.mcp.server_name,
                "server_version": self.server.mcp.server_version,
                "protocol_version": PROTOCOL_VERSION,
                "active_sse_sessions": self.server.active_sessions,
            })
            return
        if target.path in ("/", "/mcp"):
            self._send(405, headers={"Allow": "POST"})
            return
        if target.path != "/sse":
            self._send(404)
            return
        if "text/event-stream" not in self.headers.get("Accept", ""):
            self._send(406)
            return
        session = self.server.add_session(self.connection)
        if session is None:
            self._send(503, headers={"Retry-After": "1"})
            return
        try:
            self.send_response(200)
            self.send_header("Content-Type", "text/event-stream")
            self.send_header("Cache-Control", "no-cache, no-transform")
            self.send_header("X-Accel-Buffering", "no")
            self.send_header("Connection", "keep-alive")
            self.end_headers()
            endpoint = f"/messages?session_id={session.token}"
            self.wfile.write(f"event: endpoint\ndata: {endpoint}\n\n".encode("utf-8"))
            self.wfile.flush()
            heartbeat = time.monotonic()
            while not session.closed.is_set() and not self.server.closed.is_set():
                now = time.monotonic()
                if now - session.last_activity > self.server.limits.session_idle_seconds:
                    break
                try:
                    data = session.events.get(timeout=min(
                        0.25, self.server.limits.heartbeat_seconds))
                except queue.Empty:
                    if now - heartbeat >= self.server.limits.heartbeat_seconds:
                        self.wfile.write(b": keep-alive\n\n")
                        self.wfile.flush()
                        heartbeat = now
                    continue
                self.wfile.write(b"event: message\ndata: " + data + b"\n\n")
                self.wfile.flush()
                heartbeat = time.monotonic()
        except (BrokenPipeError, ConnectionResetError, TimeoutError, socket.timeout, OSError):
            pass
        finally:
            self.close_connection = True
            self.server.drop_session(session.token)

    def do_DELETE(self) -> None:
        if not self._access():
            return
        target = self._target()
        if target is not None and target.path == "/messages":
            token = self._session_token(target)
            if not token or self.server.get_session(token) is None:
                self._send(404)
                return
            self.server.drop_session(token)
            self._send(204)
            return
        if target is not None and target.path in ("/", "/mcp"):
            self._send(405, headers={"Allow": "POST"})
        else:
            self._send(404)


class ThreadedServer:
    """Bounded, explicitly closable HTTP/SSE server; context manager for tests/CLI."""

    def __init__(self, mcp: MCPStreamableServerV2, host: str = "127.0.0.1",
                 port: int = 0, *, limits: Optional[TransportLimits] = None,
                 api_key: Optional[str] = None,
                 allowed_origins: tuple[str, ...] = (),
                 allowed_hosts: tuple[str, ...] = ()) -> None:
        if not ipaddress.ip_address(host).is_loopback and not api_key:
            raise ValueError("non-loopback listener requires api_key")
        self._httpd = _HTTPServer(
            (host, port), mcp, limits or TransportLimits(), api_key,
            allowed_origins, allowed_hosts)
        self._thread: Optional[threading.Thread] = None
        self._close_lock = threading.Lock()
        self._closed = False

    @property
    def port(self) -> int:
        return int(self._httpd.server_address[1])

    @property
    def url(self) -> str:
        host, port = self._httpd.server_address[:2]
        return f"http://{host}:{port}/mcp"

    @property
    def sse_url(self) -> str:
        return self.url.removesuffix("/mcp") + "/sse"

    @property
    def active_sessions(self) -> int:
        return self._httpd.active_sessions

    def start(self) -> "ThreadedServer":
        if self._closed:
            raise RuntimeError("server is closed")
        if self._thread is None:
            self._thread = threading.Thread(
                target=self._httpd.serve_forever,
                kwargs={"poll_interval": 0.05}, name="MRL-MCP-HTTP", daemon=True)
            self._thread.start()
        return self

    def close(self) -> None:
        with self._close_lock:
            if self._closed:
                return
            self._closed = True
            self._httpd.close_connections()
            if self._thread is not None:
                self._httpd.shutdown()
                self._thread.join(timeout=2.0)
            self._httpd.server_close()

    def __enter__(self) -> "ThreadedServer":
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        self.close()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    args = parser.parse_args()
    mcp = MCPStreamableServerV2()
    mcp.register_tool("echo", "Echo an acceptance probe without accessing user data",
                      {"type": "object", "properties": {"message": {"type": "string"}},
                       "required": ["message"]},
                      lambda message: make_content(f"Tool echo: {message}"))
    with ThreadedServer(mcp, host=args.host, port=args.port,
                        api_key=os.environ.get("MRL_MCP_API_KEY")) as server:
        print(json.dumps({"origin_signature": ORIGIN_SIGNATURE,
                          "server_name": SERVER_NAME, "server_version": SERVER_VERSION,
                          "streamable_http": server.url, "legacy_sse": server.sse_url}),
              flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
