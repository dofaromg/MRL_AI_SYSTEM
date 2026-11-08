"""Transport contract and resource-lifecycle regression tests.

origin_signature: MrLiouWord
These tests run local fixture tools only; they do not validate DL580 or real models.
Run: python -B -m unittest discover -s tests -p test_MRL_mcp_streamable_v2.py
"""
from __future__ import annotations

import http.client
import json
import pathlib
import socket
import sys
import time
import unittest
from urllib.parse import urlsplit

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parents[1] / "09_workflow"))
from MRL_MCPServerHarness_Streamable_v2 import (  # noqa: E402
    MCPStreamableServerV2, ThreadedServer, TransportLimits, make_content,
)
from MRL_AgentHarness_PolicyGate_v1 import enforce, deny_all, allow  # noqa: E402
from MRL_AgentHarness_ToolLoop_v1 import ToolLoopRunner  # noqa: E402


def _server(**kwargs):
    mcp = MCPStreamableServerV2()
    mcp.register_tool("echo", "fixture echo",
                      {"type": "object", "properties": {"message": {"type": "string"}},
                       "required": ["message"]},
                      lambda message: make_content(f"Tool echo: {message}"))
    kwargs.setdefault("limits", TransportLimits(
        heartbeat_seconds=0.02, session_idle_seconds=3.0, socket_timeout=1.0))
    return ThreadedServer(mcp, **kwargs)


def _request(server, method="POST", path="/mcp", payload=None, headers=None, raw=None):
    conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=2.0)
    body = raw if raw is not None else (
        json.dumps(payload).encode("utf-8") if payload is not None else b"")
    request_headers = {"Content-Type": "application/json", **(headers or {})}
    conn.request(method, path, body=body, headers=request_headers)
    response = conn.getresponse()
    status, response_headers, data = response.status, dict(response.getheaders()), response.read()
    conn.close()
    return status, response_headers, json.loads(data) if data else None


def _rpc(method, rid=1, **params):
    return {"jsonrpc": "2.0", "id": rid, "method": method, "params": params}


def _event(response):
    event_name, data = None, []
    while True:
        line = response.readline()
        if not line:
            return None, None
        line = line.decode("utf-8").rstrip("\r\n")
        if not line:
            if event_name or data:
                return event_name, "\n".join(data)
            continue
        if line.startswith("event:"):
            event_name = line[6:].strip()
        elif line.startswith("data:"):
            data.append(line[5:].lstrip())


def _open_sse(server, headers=None):
    conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=2.0)
    conn.request("GET", "/sse", headers={"Accept": "text/event-stream", **(headers or {})})
    response = conn.getresponse()
    if response.status != 200:
        raise AssertionError(f"SSE status {response.status}")
    name, endpoint = _event(response)
    if name != "endpoint" or not endpoint.startswith("/messages?session_id="):
        raise AssertionError((name, endpoint))
    return conn, response, endpoint


def _wait_until(predicate, timeout=1.5):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return True
        time.sleep(0.01)
    return predicate()


class TestStreamableHTTP(unittest.TestCase):
    def test_initialize_handshake_tool_roundtrip(self):
        with _server() as server:
            status, _, result = _request(server, payload=_rpc(
                "initialize", protocolVersion="2099-01-01",
                clientInfo={"name": "independent-fixture", "version": "1"}, capabilities={}))
            self.assertEqual(status, 200)
            self.assertEqual(result["result"]["protocolVersion"], "2025-03-26")
            self.assertEqual(result["result"]["capabilities"], {"tools": {}})
            self.assertEqual(result["result"]["serverInfo"]["origin_signature"], "MrLiouWord")
            status, _, result = _request(server, payload={
                "jsonrpc": "2.0", "method": "notifications/initialized"})
            self.assertEqual((status, result), (202, None))
            status, _, result = _request(server, payload=_rpc("tools/list"))
            self.assertEqual(result["result"]["tools"][0]["name"], "echo")
            status, _, result = _request(server, payload=_rpc(
                "tools/call", name="echo", arguments={"message": "probe"}))
            self.assertEqual(result["result"],
                             {"content": [{"type": "text", "text": "Tool echo: probe"}],
                              "isError": False})

    def test_unknown_and_malformed_messages_remain_distinct(self):
        with _server() as server:
            for value in (None, "", 5, {}, []):
                payload = {"jsonrpc": "2.0", "id": 1, "method": value}
                status, _, response = _request(server, payload=payload)
                self.assertEqual(status, 200)
                self.assertEqual(response["error"]["code"], -32600)
            _, _, response = _request(server, payload=_rpc("no/such/method"))
            self.assertEqual(response["error"]["code"], -32601)
            _, _, response = _request(server, payload={
                "jsonrpc": "2.0", "id": 2, "method": "tools/list", "params": []})
            self.assertEqual(response["error"]["code"], -32602)
            _, _, response = _request(server, payload={
                "jsonrpc": "2.0", "id": True, "method": "ping"})
            self.assertEqual(response["error"]["code"], -32600)

    def test_invalid_arguments_do_not_run_tool(self):
        calls = []
        mcp = MCPStreamableServerV2()
        mcp.register_tool("record", "fixture", {"type": "object"},
                          lambda: calls.append("called"))
        with ThreadedServer(mcp) as server:
            for value in (None, [], 0, False, ""):
                _, _, response = _request(server, payload=_rpc(
                    "tools/call", name="record", arguments=value))
                self.assertEqual(response["error"]["code"], -32602)
        self.assertEqual(calls, [])

    def test_notification_batch_does_not_invent_responses(self):
        with _server() as server:
            status, _, response = _request(server, payload=[
                {"jsonrpc": "2.0", "method": "notifications/initialized"}])
            self.assertEqual((status, response), (202, None))
            status, _, response = _request(server, payload=[
                _rpc("ping", rid=0), _rpc("ping", rid="b"),
                {"jsonrpc": "2.0", "method": "notifications/initialized"}])
            self.assertEqual([item["id"] for item in response], [0, "b"])
            _, _, response = _request(server, payload=[])
            self.assertEqual(response["error"]["code"], -32600)

    def test_parse_limits_and_protocol_header_before_tool_execution(self):
        limits = TransportLimits(max_body_bytes=512)
        with _server(limits=limits) as server:
            self.assertEqual(_request(server, raw=b"{")[0], 400)
            self.assertEqual(_request(server, raw=b"\xff")[0], 400)
            self.assertEqual(_request(server, raw=b"NaN")[0], 400)
            self.assertEqual(_request(server, raw=b"x" * 513)[0], 413)
            self.assertEqual(_request(server, payload=_rpc("ping"),
                                      headers={"Content-Type": "text/plain"})[0], 415)
            self.assertEqual(_request(server, payload=_rpc("ping"),
                                      headers={"MCP-Protocol-Version": "not-supported"})[0], 400)
            self.assertEqual(_request(server, payload=_rpc("ping", rid="x" * 200))[0], 400)

    def test_invalid_content_length_rejected_without_waiting_for_body(self):
        with _server() as server:
            for header in ("Content-Length: -1", "Content-Length: abc",
                           "Content-Length: 1\r\nContent-Length: 1",
                           "Transfer-Encoding: chunked\r\nContent-Length: 1"):
                with socket.create_connection(("127.0.0.1", server.port), timeout=1) as sock:
                    sock.sendall((
                        f"POST /mcp HTTP/1.1\r\nHost: 127.0.0.1:{server.port}\r\n"
                        f"{header}\r\nContent-Type: application/json\r\n\r\n").encode("ascii"))
                    self.assertIn(b" 400 ", sock.recv(256).split(b"\r\n")[0])

    def test_auth_origin_host_and_path_boundaries(self):
        with _server(api_key="fixture-key") as server:
            self.assertEqual(_request(server, payload=_rpc("ping"))[0], 401)
            headers = {"x-api-key": "fixture-key"}
            self.assertEqual(_request(server, payload=_rpc("ping"), headers=headers)[0], 200)
            self.assertEqual(_request(server, payload=_rpc("ping"),
                                      headers={**headers, "Origin": "https://untrusted.invalid"})[0], 403)
            self.assertEqual(_request(server, payload=_rpc("ping"),
                                      headers={**headers, "Host": "attacker.invalid"})[0], 403)
            self.assertEqual(_request(server, path="/not-an-endpoint",
                                      payload=_rpc("ping"), headers=headers)[0], 404)

    def test_connection_capacity_rejects_without_unbounded_worker_growth(self):
        limits = TransportLimits(max_sse_sessions=1, max_http_connections=2,
                                 socket_timeout=2.0)
        with _server(limits=limits) as server:
            sockets = [socket.create_connection(("127.0.0.1", server.port), timeout=2)
                       for _ in range(2)]
            try:
                for sock in sockets:
                    sock.sendall(b"GET /health HTTP/1.1\r\n")
                self.assertTrue(_wait_until(lambda: server._httpd.active_connections == 2))
                self.assertEqual(_request(server, method="GET", path="/health")[0], 503)
                self.assertEqual(server._httpd.active_connections, 2)
            finally:
                for sock in sockets:
                    sock.close()
            self.assertTrue(_wait_until(lambda: server._httpd.active_connections == 0))
            self.assertEqual(_request(server, method="GET", path="/health")[0], 200)

    def test_get_405_and_health_are_honest(self):
        with _server() as server:
            status, headers, _ = _request(server, method="GET")
            self.assertEqual((status, headers["Allow"]), (405, "POST"))
            self.assertEqual(_request(server, method="DELETE")[0], 405)
            status, _, health = _request(server, method="GET", path="/health")
            self.assertEqual(status, 200)
            self.assertEqual(health["server_version"], "2.0.0")
            self.assertEqual(health["active_sse_sessions"], 0)

    def test_bounded_response_does_not_return_unbounded_tool_content(self):
        mcp = MCPStreamableServerV2()
        mcp.register_tool("big", "fixture", {"type": "object"}, lambda: "x" * 2048)
        with ThreadedServer(mcp, limits=TransportLimits(max_response_bytes=512)) as server:
            _, _, response = _request(server, payload=_rpc("tools/call", name="big", arguments={}))
            self.assertEqual(response["error"]["code"], -32603)
            self.assertNotIn("x" * 100, json.dumps(response))

    def test_tool_failure_is_tool_error_and_policy_still_prevents_execution(self):
        dangerous_calls = []
        gate = enforce([deny_all(), allow("safe"), allow("boom")])
        mcp = MCPStreamableServerV2(policy_gate=gate)
        mcp.register_tool("safe", "fixture", {"type": "object"}, lambda: "ok")
        mcp.register_tool("dangerous", "fixture", {"type": "object"},
                          lambda: dangerous_calls.append(True))
        def boom():
            raise RuntimeError("fixture internal details")
        mcp.register_tool("boom", "fixture", {"type": "object"}, boom)
        with ThreadedServer(mcp) as server:
            _, _, result = _request(server, payload=_rpc("tools/call", name="safe", arguments={}))
            self.assertFalse(result["result"]["isError"])
            _, _, result = _request(server, payload=_rpc("tools/call", name="dangerous", arguments={}))
            self.assertEqual(result["error"]["code"], -32002)
            _, _, result = _request(server, payload=_rpc("tools/call", name="boom", arguments={}))
            self.assertTrue(result["result"]["isError"])
        self.assertEqual(dangerous_calls, [])

    def test_existing_tool_loop_is_reused(self):
        loop = ToolLoopRunner()
        def add(a, b):
            return a + b
        loop.register(add)
        with ThreadedServer(MCPStreamableServerV2(tool_loop=loop)) as server:
            _, _, response = _request(server, payload=_rpc(
                "tools/call", name="add", arguments={"a": 2, "b": 3}))
            self.assertEqual(response["result"]["content"][0]["text"], "5")


class TestLegacySSE(unittest.TestCase):
    def test_endpoint_event_request_reply_and_session_isolation(self):
        with _server() as server:
            c1, s1, ep1 = _open_sse(server)
            c2, s2, ep2 = _open_sse(server)
            try:
                self.assertNotEqual(ep1, ep2)
                self.assertEqual(_request(server, path=ep1,
                                          payload=_rpc("initialize", rid="first"))[0], 202)
                name, data = _event(s1)
                self.assertEqual((name, json.loads(data)["id"]), ("message", "first"))
                self.assertEqual(_request(server, path=ep2,
                                          payload=_rpc("tools/call", rid="second", name="echo",
                                                       arguments={"message": "sse-probe"}))[0], 202)
                name, data = _event(s2)
                response = json.loads(data)
                self.assertEqual((name, response["id"]), ("message", "second"))
                self.assertEqual(response["result"]["content"][0]["text"], "Tool echo: sse-probe")
                self.assertEqual(_request(server, method="GET", path="/health")[0], 200)
            finally:
                for conn, stream in ((c1, s1), (c2, s2)):
                    stream.close()
                    conn.close()
            self.assertTrue(_wait_until(lambda: server.active_sessions == 0))

    def test_deleted_session_cannot_execute_future_requests(self):
        with _server() as server:
            conn, stream, endpoint = _open_sse(server)
            try:
                self.assertEqual(_request(server, method="DELETE", path=endpoint)[0], 204)
                self.assertEqual(_request(server, path=endpoint, payload=_rpc("ping"))[0], 404)
                self.assertEqual(server.active_sessions, 0)
            finally:
                stream.close()
                conn.close()

    def test_invalid_session_and_accept_header_are_rejected(self):
        with _server() as server:
            self.assertEqual(_request(server, method="GET", path="/sse")[0], 406)
            for path in ("/messages", "/messages?session_id=missing",
                         "/messages?session_id=x&session_id=y"):
                self.assertEqual(_request(server, path=path, payload=_rpc("ping"))[0], 404)

    def test_session_capacity_is_bounded_and_recovers_after_close(self):
        with _server(limits=TransportLimits(max_sse_sessions=1, heartbeat_seconds=0.02)) as server:
            conn, stream, endpoint = _open_sse(server)
            try:
                status, _, _ = _request(server, method="GET", path="/sse",
                                        headers={"Accept": "text/event-stream"})
                self.assertEqual(status, 503)
                self.assertEqual(_request(server, method="DELETE", path=endpoint)[0], 204)
                conn2, stream2, _ = _open_sse(server)
                stream2.close()
                conn2.close()
            finally:
                stream.close()
                conn.close()

    def test_idle_session_is_removed(self):
        limits = TransportLimits(heartbeat_seconds=0.02, session_idle_seconds=0.15)
        with _server(limits=limits) as server:
            conn, stream, endpoint = _open_sse(server)
            try:
                self.assertTrue(_wait_until(lambda: server.active_sessions == 0))
                self.assertEqual(_request(server, path=endpoint, payload=_rpc("ping"))[0], 404)
            finally:
                stream.close()
                conn.close()

    def test_full_queue_rejects_before_tool_execution(self):
        # A real HTTP POST producer with a deliberately stalled stream consumer.
        # Only the consumer socket is held; no placeholder server/tool is used.
        calls = []
        mcp = MCPStreamableServerV2()
        mcp.register_tool("count", "fixture", {"type": "object"},
                          lambda: calls.append(True) or "ok")
        with ThreadedServer(mcp, limits=TransportLimits(max_queue_events=2)) as server:
            left, right = socket.socketpair()
            session = server._httpd.add_session(left)
            try:
                endpoint = "/messages?session_id=" + session.token
                for rid in (1, 2):
                    self.assertEqual(_request(server, path=endpoint, payload=_rpc(
                        "tools/call", rid=rid, name="count", arguments={}))[0], 202)
                self.assertEqual(_request(server, path=endpoint, payload=_rpc(
                    "tools/call", rid=3, name="count", arguments={}))[0], 429)
                self.assertEqual(len(calls), 2)
                self.assertEqual(session.events.qsize(), 2)
            finally:
                server._httpd.drop_session(session.token)
                left.close()
                right.close()

    def test_shutdown_closes_open_streams_and_is_idempotent(self):
        server = _server().start()
        conn, stream, _ = _open_sse(server)
        started = time.monotonic()
        server.close()
        server.close()
        self.assertLess(time.monotonic() - started, 2.0)
        self.assertEqual(server.active_sessions, 0)
        self.assertFalse(server._thread.is_alive())
        self.assertTrue(_wait_until(lambda: server._httpd.active_connections == 0))
        stream.close()
        conn.close()

    def test_unstarted_server_close_does_not_deadlock(self):
        server = _server()
        server.close()
        server.close()
        with self.assertRaises(RuntimeError):
            server.start()


if __name__ == "__main__":
    unittest.main(verbosity=2)
