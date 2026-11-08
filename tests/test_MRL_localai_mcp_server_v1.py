"""MRL fixed-source binding tests. No model/DL580 runtime claim is made.

origin_signature: MrLiouWord
Fixtures are the exact recovered repository originals. The file reader is replaced
with memory streams for deterministic mutation, missing-file, and path tests.
The network test uses the real v2 HTTP adapter with runtime_mode=false.
"""
from __future__ import annotations

from contextlib import contextmanager
import hashlib
import http.client
import io
import json
import os
from pathlib import Path
import sys
from types import SimpleNamespace
import unittest
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from MRL_localai_mcp_server_v1 import (  # noqa: E402
    ASSETS, SCHEMA, recovery_identity, create_mcp_server, local_health, main,
)
import MRL_localai_mcp_server_v1 as launcher  # noqa: E402
from MRL_MCPServerHarness_Streamable_v2 import ThreadedServer  # noqa: E402


def _fixtures():
    return {spec["path"]: (ROOT / spec["path"]).read_bytes() for spec in ASSETS}


@contextmanager
def _memory_assets(files):
    stats = {}
    class MemoryFile(io.BytesIO):
        def fileno(self):
            return id(self)
    def open_file(path, mode="r", *args, **kwargs):
        if mode != "rb" or path.name not in files:
            raise FileNotFoundError(path.name)
        value = files[path.name]
        stream = MemoryFile(value)
        stats[id(stream)] = SimpleNamespace(st_size=len(value), st_mtime_ns=1, st_ino=1)
        return stream
    with mock.patch.object(Path, "resolve", lambda self, strict=False: self.absolute()), \
         mock.patch.object(Path, "is_symlink", return_value=False), \
         mock.patch.object(Path, "open", open_file), \
         mock.patch.object(os, "fstat", side_effect=lambda fd: stats[fd]):
        yield


class TestFixedRecoveryBinding(unittest.TestCase):
    def test_original_size_sha256_and_git_blob_are_all_checked(self):
        with _memory_assets(_fixtures()):
            identity = recovery_identity(ROOT, runtime_mode=False)
        self.assertEqual(identity["schema"], SCHEMA)
        self.assertTrue(identity["hash_match"])
        self.assertFalse(identity["ready"])
        self.assertFalse(identity["runtime_mode"])
        self.assertEqual(identity["runtime_operational"], "NOT_ASSERTED")
        self.assertEqual({item["path"] for item in identity["assets"]},
                         {"metacode_core.js", "metacode_usage.js"})
        for item in identity["assets"]:
            self.assertEqual(item["size"], item["expected_size"])
            self.assertEqual(item["sha256"], item["expected_sha256"])
            self.assertEqual(item["git_blob_sha"], item["expected_git_blob_sha"])

    def test_one_byte_change_is_not_reported_as_original(self):
        files = _fixtures()
        value = files["metacode_core.js"]
        files["metacode_core.js"] = bytes([value[0] ^ 1]) + value[1:]
        with _memory_assets(files):
            identity = recovery_identity(ROOT, runtime_mode=False)
        self.assertFalse(identity["hash_match"])
        self.assertEqual(identity["assets"][0]["status"], "MISMATCH")
        self.assertFalse(identity["ready"])

    def test_missing_original_is_not_hidden_by_other_matching_file(self):
        files = _fixtures()
        del files["metacode_usage.js"]
        with _memory_assets(files):
            identity = recovery_identity(ROOT, runtime_mode=True)
        self.assertFalse(identity["hash_match"])
        self.assertEqual(identity["assets"][1]["status"], "MISSING")
        self.assertFalse(identity["ready"])

    def test_redirected_paths_are_rejected(self):
        with _memory_assets(_fixtures()), mock.patch.object(Path, "is_symlink", return_value=True):
            identity = recovery_identity(ROOT)
        self.assertTrue(all(item["status"] == "PATH_REDIRECTED" for item in identity["assets"]))
        self.assertFalse(identity["hash_match"])

    def test_matching_files_do_not_bypass_host_and_d_drive_gate(self):
        host = {"hostname": "fixture", "expected_hostname": launcher.EXPECTED_HOST,
                "matches": False, "windows": False, "repo_on_fixed_d": False}
        with _memory_assets(_fixtures()), mock.patch.object(
                launcher, "_host_metadata", return_value=host):
            identity = recovery_identity(ROOT, runtime_mode=True)
        self.assertTrue(identity["hash_match"])
        self.assertFalse(identity["ready"])

    def test_verify_only_does_not_start_transport(self):
        stdout = io.StringIO()
        with _memory_assets(_fixtures()), mock.patch.object(
                launcher, "ThreadedServer", side_effect=AssertionError("must not start")), \
                mock.patch("sys.stdout", stdout):
            code = main(["--verify-only"])
        report = json.loads(stdout.getvalue())
        self.assertEqual(code, 0)
        self.assertEqual(report["status"], "SOURCE_HASH_PASS")
        self.assertFalse(report["identity"]["runtime_mode"])
        self.assertFalse(report["identity"]["ready"])

    def test_runtime_preflight_rejects_wrong_host_before_listening(self):
        host = {"hostname": "fixture", "expected_hostname": launcher.EXPECTED_HOST,
                "matches": False, "windows": False, "repo_on_fixed_d": False}
        with _memory_assets(_fixtures()), mock.patch.object(
                launcher, "_host_metadata", return_value=host), mock.patch.object(
                    launcher, "ThreadedServer", side_effect=AssertionError("must not start")), \
                    mock.patch("sys.stdout", io.StringIO()):
            self.assertEqual(main(["--port", "0"]), 3)

    def test_default_catalog_has_fixed_identity_and_no_optional_probe(self):
        server = create_mcp_server(ROOT)
        result = server.handle_message({"jsonrpc": "2.0", "id": 1, "method": "tools/list"})
        tools = {tool["name"]: tool for tool in result["result"]["tools"]}
        self.assertEqual(set(tools), {"echo", "mrl_recovery_identity"})
        self.assertEqual(tools["mrl_recovery_identity"]["inputSchema"],
                         {"type": "object", "properties": {}, "required": [],
                          "additionalProperties": False})

    def test_real_http_identity_roundtrip_and_arbitrary_path_rejection(self):
        with _memory_assets(_fixtures()), ThreadedServer(
                create_mcp_server(ROOT, runtime_mode=False)) as server:
            conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=2)
            message = {"jsonrpc": "2.0", "id": 1, "method": "tools/call",
                       "params": {"name": "mrl_recovery_identity", "arguments": {}}}
            conn.request("POST", "/mcp", json.dumps(message),
                         {"Content-Type": "application/json"})
            response = conn.getresponse()
            self.assertEqual(response.status, 200)
            result = json.loads(response.read())["result"]
            conn.close()
            identity = json.loads(result["content"][0]["text"])
            self.assertFalse(result["isError"])
            self.assertTrue(identity["hash_match"])
            self.assertFalse(identity["runtime_mode"])
            self.assertFalse(identity["ready"])
            message["params"]["arguments"] = {"path": "/not-an-authorized-file"}
            conn = http.client.HTTPConnection("127.0.0.1", server.port, timeout=2)
            conn.request("POST", "/mcp", json.dumps(message),
                         {"Content-Type": "application/json"})
            result = json.loads(conn.getresponse().read())["result"]
            conn.close()
            self.assertTrue(result["isError"])

    def test_optional_health_probe_has_fixed_routes_and_never_returns_body(self):
        body = b'{"status":"PASS","origin":"MrLiouWord","secret":"PRIVATE_FIXTURE_BODY"}'
        instances = []
        def connection(host, port, timeout):
            self.assertEqual(host, "127.0.0.1")
            self.assertIn(port, (7700, 7800))
            conn = mock.Mock()
            conn.getresponse.return_value.status = 200
            conn.getresponse.return_value.read.return_value = body
            instances.append((port, conn))
            return conn
        with mock.patch.object(http.client, "HTTPConnection", side_effect=connection), \
             mock.patch.dict(os.environ, {}, clear=True):
            result = local_health()
        self.assertEqual([port for port, _ in instances], [7700, 7800])
        for _, conn in instances:
            self.assertEqual(conn.request.call_args.args[:2], ("GET", "/health"))
            conn.close.assert_called_once()
        self.assertNotIn("PRIVATE_FIXTURE_BODY", json.dumps(result))
        self.assertTrue(all(item["health_flag"] and item["origin_match"]
                            for item in result["services"]))
        self.assertTrue(all(item["body_sha256"] == hashlib.sha256(body).hexdigest()
                            for item in result["services"]))


if __name__ == "__main__":
    unittest.main(verbosity=2)
