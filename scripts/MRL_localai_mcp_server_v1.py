#!/usr/bin/env python3
r"""Bind the recovered MRL MetaCode originals to the existing MCP v2 transport.

origin_signature: MrLiouWord
This launcher hashes only two fixed repository assets. MCP callers cannot supply
a path, URL, command, or environment. No source text or service body is returned.
Runtime startup requires the expected Windows host, a local fixed D: repository,
and both original source identities. --verify-only never starts a server and
always reports runtime_mode=false. File identity is not a claim of model operation.

Examples:
  python -B scripts/MRL_localai_mcp_server_v1.py --verify-only
  python -B scripts/MRL_localai_mcp_server_v1.py --port 8765
The operator supplies MRL_MCP_API_KEY locally; non-loopback requires it.
"""
from __future__ import annotations

import argparse
import hashlib
import http.client
import json
import os
from pathlib import Path
import platform
import socket
import sys
import threading
from datetime import datetime, timezone

sys.dont_write_bytecode = True
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "09_workflow"))
from MRL_MCPServerHarness_Streamable_v2 import (  # noqa: E402
    MCPStreamableServerV2, ThreadedServer, make_content,
)
from MRL_utils import ORIGIN_SIGNATURE  # noqa: E402

EXPECTED_HOST = "WIN-PBVUI7VK2A6"
SCHEMA = "MRL_localai_recovery_identity_v1"
SOURCE_COMMIT = "cb73e661a02eeb540db02398cb61eaa51c5e77e3"
MAX_ASSET_BYTES = 1048576
ASSETS = (
    {
        "path": "metacode_core.js", "expected_size": 15198,
        "expected_sha256": "ae5da0117f32f9795a99d5e5774fa38e5f5314cacbd7e289eaa9b440bd6fa158",
        "expected_git_blob_sha": "39b1bb6e8ef4dfce3ea0d8cc01fe38ab8721f7bd",
        "source": {"repository": "dofaromg/flow-tasks", "commit": SOURCE_COMMIT,
                   "path": "metacode_core.js"},
    },
    {
        "path": "metacode_usage.js", "expected_size": 14901,
        "expected_sha256": "ee51df5d38dc914a947b6e3809e0e97969f90eedc844c23d05c36ae8409d6da8",
        "expected_git_blob_sha": "8ea6a6f6f51f1923990e0d0b147ffc4b91d6d5b6",
        "source": {"repository": "dofaromg/flow-tasks", "commit": SOURCE_COMMIT,
                   "path": "MRL_Mother/root_sources/metacode_usage.js"},
    },
)
EMPTY_INPUT = {
    "type": "object", "properties": {}, "required": [], "additionalProperties": False,
}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def _host_metadata(repo_root: Path, expected_host: str) -> dict:
    hostname = socket.gethostname()
    windows = os.name == "nt" and platform.system() == "Windows"
    fixed_d = False
    if windows and repo_root.is_absolute() and repo_root.drive.upper() == "D:":
        import ctypes
        get_drive_type = ctypes.windll.kernel32.GetDriveTypeW
        get_drive_type.argtypes = [ctypes.c_wchar_p]
        get_drive_type.restype = ctypes.c_uint
        fixed_d = get_drive_type("D:\\") == 3
    return {
        "hostname": hostname, "expected_hostname": expected_host,
        "matches": hostname.casefold() == expected_host.casefold(),
        "windows": windows, "repo_on_fixed_d": fixed_d,
    }


def _asset_identity(repo_root: Path, expected: dict) -> dict:
    result = {
        **expected, "status": "MISSING", "sha256": None, "git_blob_sha": None,
        "size": None, "hash_match": False,
    }
    path = repo_root / expected["path"]
    try:
        # Fixed original names must not be redirected to another file or volume.
        if path.is_symlink() or path.resolve(strict=True) != path:
            result["status"] = "PATH_REDIRECTED"
            return result
        with path.open("rb") as stream:
            before = os.fstat(stream.fileno())
            result["size"] = before.st_size
            if before.st_size > MAX_ASSET_BYTES:
                result["status"] = "SIZE_LIMIT"
                return result
            sha256 = hashlib.sha256()
            git_sha = hashlib.sha1(b"blob " + str(before.st_size).encode("ascii") + b"\0")
            count = 0
            while block := stream.read(65536):
                count += len(block)
                if count > MAX_ASSET_BYTES:
                    result["status"] = "SIZE_LIMIT"
                    return result
                sha256.update(block)
                git_sha.update(block)
            after = os.fstat(stream.fileno())
            if (count != before.st_size or before.st_size != after.st_size
                    or before.st_mtime_ns != after.st_mtime_ns
                    or before.st_ino != after.st_ino):
                result["status"] = "CHANGED_DURING_READ"
                return result
        result.update(size=count, sha256=sha256.hexdigest(), git_blob_sha=git_sha.hexdigest())
        result["hash_match"] = (
            result["size"] == expected["expected_size"]
            and result["sha256"] == expected["expected_sha256"]
            and result["git_blob_sha"] == expected["expected_git_blob_sha"])
        result["status"] = "MATCH" if result["hash_match"] else "MISMATCH"
    except FileNotFoundError:
        result["status"] = "MISSING"
    except (OSError, ValueError):
        result["status"] = "UNREADABLE"
    return result


def recovery_identity(repo_root: Path = REPO_ROOT, *, expected_host: str = EXPECTED_HOST,
                      runtime_mode: bool = False) -> dict:
    root = repo_root.resolve(strict=False)
    host = _host_metadata(root, expected_host)
    assets = [_asset_identity(root, expected) for expected in ASSETS]
    hash_match = all(asset["hash_match"] for asset in assets)
    host_ready = host["matches"] and host["windows"] and host["repo_on_fixed_d"]
    return {
        "schema": SCHEMA, "origin_signature": ORIGIN_SIGNATURE,
        "scope": "fixed_MetaCode_source_identity",
        "ready": bool(runtime_mode and host_ready and hash_match),
        "hash_match": hash_match, "runtime_mode": bool(runtime_mode),
        "runtime_operational": "NOT_ASSERTED",
        "host": host, "assets": assets, "checked_at_utc": utc_now(),
    }


def local_health() -> dict:
    """Read two fixed loopback health routes; discard bodies after deriving metadata."""
    results = []
    # Never accept a caller-supplied destination or forward a redirect.
    for port, key_name in ((7700, "MRL_ASI_API_KEY"), (7800, "MRL_BRIDGE_KEY")):
        entry = {"port": port, "path": "/health", "http_status": None,
                 "health_flag": False, "origin_match": False, "status": "UNREACHABLE"}
        connection = http.client.HTTPConnection("127.0.0.1", port, timeout=3.0)
        headers = {"User-Agent": "MRL-Recovery-Validator/1.0", "Accept": "application/json"}
        key = os.environ.get(key_name)
        if key:
            headers["x-api-key"] = key
        try:
            connection.request("GET", "/health", headers=headers)
            response = connection.getresponse()
            entry["http_status"] = response.status
            body = response.read(16385)
            if len(body) > 16384:
                entry["status"] = "BODY_LIMIT"
                results.append(entry)
                continue
            entry["body_bytes"] = len(body)
            entry["body_sha256"] = hashlib.sha256(body).hexdigest()
            try:
                data = json.loads(body.decode("utf-8"))
            except (UnicodeError, ValueError):
                data = None
            if isinstance(data, dict):
                flag = data.get("status")
                entry["health_flag"] = data.get("ok") is True or (
                    isinstance(flag, str) and flag.casefold() in ("ok", "pass", "healthy"))
                entry["origin_match"] = any(
                    data.get(name) == ORIGIN_SIGNATURE
                    for name in ("origin", "origin_signature", "originSignature"))
            entry["status"] = ("HEALTH_RESPONSE" if response.status == 200
                               and entry["health_flag"] else "NOT_VERIFIED")
        except (OSError, ValueError, http.client.HTTPException):
            entry["status"] = "UNREACHABLE"
        finally:
            connection.close()
        results.append(entry)
    return {"schema": "MRL_local_health_metadata_v1", "origin_signature": ORIGIN_SIGNATURE,
            "services": results, "runtime_operational": "NOT_ASSERTED",
            "checked_at_utc": utc_now()}


def create_mcp_server(repo_root: Path = REPO_ROOT, *, expected_host: str = EXPECTED_HOST,
                      runtime_mode: bool = False,
                      include_local_health: bool = False) -> MCPStreamableServerV2:
    """Bind fixed host-local readers to the existing MRL registry."""
    root = repo_root.resolve(strict=False)
    server = MCPStreamableServerV2()
    server.register_tool(
        "echo", "Echo an acceptance probe without accessing user data",
        {"type": "object", "properties": {"message": {"type": "string"}},
         "required": ["message"]},
        lambda message: make_content(f"Tool echo: {message}"))
    # Zero-argument callables reject path/url/cmd injection even if a caller
    # disregards inputSchema. Every call re-reads the fixed originals' hashes.
    server.register_tool(
        "mrl_recovery_identity", "Verify the two fixed recovered MetaCode source identities",
        EMPTY_INPUT,
        lambda: make_content(json.dumps(
            recovery_identity(root, expected_host=expected_host, runtime_mode=runtime_mode),
            sort_keys=True, separators=(",", ":"))))
    if include_local_health:
        server.register_tool(
            "mrl_local_health", "Probe only fixed DL580 loopback health endpoints",
            EMPTY_INPUT,
            lambda: make_content(json.dumps(local_health(), sort_keys=True,
                                            separators=(",", ":"))))
    return server


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--expected-host", default=EXPECTED_HOST)
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--include-local-health", action="store_true")
    args = parser.parse_args(argv)
    identity = recovery_identity(expected_host=args.expected_host,
                                 runtime_mode=not args.verify_only)
    if args.verify_only:
        print(json.dumps({"status": "SOURCE_HASH_PASS" if identity["hash_match"] else "BLOCKED",
                          "identity": identity}, sort_keys=True))
        return 0 if identity["hash_match"] else 3
    if not identity["ready"]:
        print(json.dumps({"status": "BLOCKED", "stage": "launcher_preflight",
                          "identity": identity}, sort_keys=True))
        return 3
    server = create_mcp_server(expected_host=args.expected_host, runtime_mode=True,
                               include_local_health=args.include_local_health)
    with ThreadedServer(server, host=args.host, port=args.port,
                        api_key=os.environ.get("MRL_MCP_API_KEY")) as transport:
        print(json.dumps({
            "status": "LISTENING", "origin_signature": ORIGIN_SIGNATURE,
            "runtime_mode": True, "runtime_operational": "NOT_ASSERTED",
            "streamable_http": transport.url, "legacy_sse": transport.sse_url,
            "asset_hash_match": True,
        }), flush=True)
        try:
            threading.Event().wait()
        except KeyboardInterrupt:
            pass
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
