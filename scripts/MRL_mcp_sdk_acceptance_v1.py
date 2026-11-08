#!/usr/bin/env python3
r"""MRL official MCP SDK acceptance for an existing, explicitly selected endpoint.

origin_signature: MrLiouWord
Run with Python 3.12 on the intended client host. This command starts no server,
changes no credential, and never prints tool payloads or credentials. A PASS covers
only the selected transport, observed host, endpoint, and checks in this receipt.
It does not claim that all DL580 recovery work or a real model is operational.

Environment:
  MRL_MCP_ENDPOINT  Exact /mcp or /sse URL; no query, fragment, or userinfo.
  MRL_MCP_API_KEY   Existing x-api-key credential; mandatory for every route.
Examples (the endpoint and key must already be configured in the local session):
  python -B scripts/MRL_mcp_sdk_acceptance_v1.py --transport streamable-http \
    --tool echo --stdout
  python -B scripts/MRL_mcp_sdk_acceptance_v1.py --transport sse --tool echo \
    --expected-client-host WIN-PBVUI7VK2A6 \
    --out D:\MRL_Mother\EvidenceChain\_reports\mcp-sse-unique.json

Dependencies are pinned in deploy/dl580/recovery/requirements-mcp-sdk.txt.
Official sources:
  https://pypi.org/project/mcp/1.30.0/
  https://github.com/modelcontextprotocol/python-sdk/tree/v1.30.0
  https://modelcontextprotocol.io/specification/2025-03-26/basic/lifecycle
"""
from __future__ import annotations

import argparse
import asyncio
import hashlib
import importlib.metadata
import ipaddress
import json
import logging
import os
from pathlib import Path
import platform
import secrets
import socket
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from urllib.parse import urlsplit

sys.dont_write_bytecode = True

ORIGIN_SIGNATURE = "MrLiouWord"
DIRECT_PINS = {"mcp": "1.30.0", "httpx": "0.28.1"}
SERVER_NAME = "MRL_MCPServerHarness_Streamable"
SERVER_VERSION = "2.0.0"
PROTOCOL_VERSION = "2025-03-26"
REQUEST_TIMEOUT = 15.0
TOTAL_TIMEOUT = 45.0
MAX_TOOL_PAGES = 100
MAX_TOOLS = 10000


class AcceptanceError(Exception):
    def __init__(self, code: str, *, blocked: bool = False):
        super().__init__(code)
        self.code = code
        self.blocked = blocked


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's normal error can repeat a supplied argument, including data.
        raise AcceptanceError("cli_arguments_invalid", blocked=True)


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def digest(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def require(condition: bool, code: str, *, blocked: bool = False) -> None:
    if not condition:
        raise AcceptanceError(code, blocked=blocked)


def check(receipt: dict, name: str, **metadata) -> None:
    receipt["checks"].append({"name": name, "status": "PASS", **metadata})


def safe_error(exc: BaseException) -> dict:
    """Retain error types and numeric codes, never exception messages or bodies."""
    errors = []
    pending = [exc]
    while pending and len(errors) < 16:
        item = pending.pop()
        children = getattr(item, "exceptions", None)
        if children:
            pending.extend(children)
            continue
        value = {"type": type(item).__name__}
        if isinstance(item, AcceptanceError):
            value["code"] = item.code
            value["blocked"] = item.blocked
        response = getattr(item, "response", None)
        status = getattr(response, "status_code", None)
        if isinstance(status, int):
            value["http_status"] = status
        error_number = getattr(item, "errno", None)
        if isinstance(error_number, int):
            value["os_error_number"] = error_number
        protocol_error = getattr(item, "error", None)
        code = getattr(protocol_error, "code", None)
        if isinstance(code, int):
            value["mcp_error_code"] = code
        errors.append(value)
    return {"errors": errors}


def parse_cli(argv=None):
    parser = SafeParser(description=__doc__)
    parser.add_argument("--transport", required=True,
                        choices=("streamable-http", "sse"))
    parser.add_argument("--tool", choices=("echo", "mrl_recovery_identity"),
                        help="Run a source-verified echo or read-only original-asset identity check.")
    parser.add_argument("--arguments",
                        help='Optional JSON: echo requires only "message"; identity requires {}.')
    parser.add_argument("--expected-server-name", default=SERVER_NAME)
    parser.add_argument("--expected-server-version", default=SERVER_VERSION)
    parser.add_argument("--expected-client-host",
                        help="Require the observed client hostname to match.")
    target = parser.add_mutually_exclusive_group(required=True)
    target.add_argument("--stdout", action="store_true",
                        help="Print only the metadata receipt; write no receipt file.")
    target.add_argument("--out",
                        help="New .json receipt path on the local fixed D: drive.")
    return parser.parse_args(argv)


def configuration(args, environ) -> tuple[str, dict, dict | None]:
    endpoint = environ.get("MRL_MCP_ENDPOINT", "")
    api_key = environ.get("MRL_MCP_API_KEY", "")
    require(bool(endpoint) and endpoint.strip() == endpoint and len(endpoint) <= 2048,
            "endpoint_missing_or_invalid", blocked=True)
    require(not any(ord(ch) < 32 or ord(ch) == 127 for ch in endpoint),
            "endpoint_control_character", blocked=True)
    try:
        parsed = urlsplit(endpoint)
    except ValueError:
        raise AcceptanceError("endpoint_url_invalid", blocked=True) from None
    require(parsed.scheme in ("http", "https") and bool(parsed.hostname),
            "endpoint_scheme_or_host_invalid", blocked=True)
    require(parsed.username is None and parsed.password is None
            and not parsed.query and not parsed.fragment,
            "endpoint_must_not_contain_credentials_query_or_fragment", blocked=True)
    try:
        parsed.port
        loopback = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        # A hostname is acceptable for HTTPS. Invalid ports still fail below.
        loopback = False
        try:
            parsed.port
        except ValueError:
            raise AcceptanceError("endpoint_port_invalid", blocked=True) from None
    require(parsed.scheme == "https" or loopback,
            "plain_http_requires_literal_loopback", blocked=True)
    require(0 < len(api_key) <= 4096 and api_key.strip() == api_key and api_key.isascii()
            and not any(ord(ch) < 32 or ord(ch) == 127 for ch in api_key),
            "api_key_missing_or_invalid", blocked=True)
    require(bool(args.expected_server_name) and bool(args.expected_server_version),
            "expected_identity_missing", blocked=True)
    require(args.arguments is None or args.tool is not None,
            "arguments_require_an_allowlisted_tool", blocked=True)
    tool_args = None
    if args.tool == "echo":
        if args.arguments is None:
            tool_args = {"message": "MRL-SDK-ACCEPTANCE-" + secrets.token_hex(12)}
        else:
            require(len(args.arguments.encode("utf-8")) <= 1024,
                    "echo_arguments_too_large", blocked=True)
            try:
                tool_args = json.loads(args.arguments)
            except (ValueError, TypeError):
                raise AcceptanceError("echo_arguments_invalid_json", blocked=True) from None
        require(isinstance(tool_args, dict) and set(tool_args) == {"message"},
                "echo_arguments_must_contain_only_message", blocked=True)
        message = tool_args["message"]
        require(isinstance(message, str) and 0 < len(message.encode("utf-8")) <= 512,
                "echo_message_invalid", blocked=True)
    elif args.tool == "mrl_recovery_identity":
        if args.arguments is not None:
            require(len(args.arguments.encode("utf-8")) <= 1024,
                    "identity_arguments_too_large", blocked=True)
            try:
                identity_args = json.loads(args.arguments)
            except (ValueError, TypeError):
                raise AcceptanceError("identity_arguments_invalid_json", blocked=True) from None
            require(isinstance(identity_args, dict) and not identity_args,
                    "identity_arguments_must_be_empty_object", blocked=True)
        tool_args = {}
    return endpoint, {
        "x-api-key": api_key, "User-Agent": "MRL-Recovery-Validator/1.0",
    }, tool_args


def dependency_versions() -> dict:
    require(sys.version_info >= (3, 12), "python_3_12_or_later_required", blocked=True)
    found = {}
    for name, expected in DIRECT_PINS.items():
        try:
            found[name] = importlib.metadata.version(name)
        except importlib.metadata.PackageNotFoundError:
            raise AcceptanceError("required_dependency_missing_" + name, blocked=True) from None
        require(found[name] == expected, "dependency_version_mismatch_" + name, blocked=True)
    return found


def prepare_destination(value: str | None) -> Path | None:
    if value is None:
        return None
    require(os.name == "nt", "receipt_requires_windows_local_d_drive", blocked=True)
    import ctypes
    drive_type = ctypes.windll.kernel32.GetDriveTypeW
    drive_type.argtypes = [ctypes.c_wchar_p]
    drive_type.restype = ctypes.c_uint
    require(drive_type("D:\\") == 3, "receipt_d_drive_must_be_local_fixed", blocked=True)
    requested = Path(value)
    require(requested.is_absolute() and requested.drive.upper() == "D:"
            and requested.suffix.lower() == ".json",
            "receipt_requires_absolute_d_json_path", blocked=True)
    target = requested.resolve(strict=False)
    require(target.drive.upper() == "D:", "receipt_reparse_outside_d_drive", blocked=True)
    require(not target.exists(), "receipt_already_exists", blocked=True)
    target.parent.mkdir(parents=True, exist_ok=True)
    target = target.resolve(strict=False)
    require(target.drive.upper() == "D:", "receipt_reparse_outside_d_drive", blocked=True)
    return target


def write_receipt_exclusive(target: Path, payload: bytes) -> None:
    """On Windows, rename publishes atomically and fails if the target exists."""
    require(os.name == "nt" and target.resolve(strict=False).drive.upper() == "D:",
            "receipt_requires_windows_local_d_drive", blocked=True)
    descriptor, temporary_name = tempfile.mkstemp(
        prefix=".mrl-receipt-", suffix=".tmp", dir=target.parent,
    )
    temporary = Path(temporary_name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        # Deliberately use Windows os.rename, never os.replace.
        os.rename(temporary, target)
    finally:
        temporary.unlink(missing_ok=True)


def verify_recovery_identity(data: dict) -> dict:
    """Validate the server's metadata against fixed, independently recovered originals."""
    expected = {
        "metacode_core.js": {
            "sha256": "ae5da0117f32f9795a99d5e5774fa38e5f5314cacbd7e289eaa9b440bd6fa158",
            "git_blob_sha": "39b1bb6e8ef4dfce3ea0d8cc01fe38ab8721f7bd",
            "size": 15198, "source_path": "metacode_core.js",
        },
        "metacode_usage.js": {
            "sha256": "ee51df5d38dc914a947b6e3809e0e97969f90eedc844c23d05c36ae8409d6da8",
            "git_blob_sha": "8ea6a6f6f51f1923990e0d0b147ffc4b91d6d5b6",
            "size": 14901, "source_path": "MRL_Mother/root_sources/metacode_usage.js",
        },
    }
    require(isinstance(data, dict)
            and data.get("schema") == "MRL_localai_recovery_identity_v1"
            and data.get("origin_signature") == ORIGIN_SIGNATURE,
            "recovery_identity_schema_or_origin_mismatch")
    require(all(data.get(name) is True for name in ("ready", "hash_match", "runtime_mode")),
            "recovery_identity_not_ready")
    require(data.get("runtime_operational") == "NOT_ASSERTED",
            "recovery_identity_runtime_scope_mismatch")
    observed = data.get("host")
    require(isinstance(observed, dict)
            and all(observed.get(name) is True for name in ("matches", "windows", "repo_on_fixed_d")),
            "recovery_identity_server_host_gate_failed")
    for name in ("hostname", "expected_hostname"):
        require(isinstance(observed.get(name), str)
                and observed[name].casefold() == "win-pbvui7vk2a6",
                "recovery_identity_server_hostname_mismatch")
    assets = data.get("assets")
    require(isinstance(assets, list) and len(assets) == len(expected)
            and all(isinstance(asset, dict) for asset in assets),
            "recovery_identity_asset_count_mismatch")
    require(all(isinstance(asset.get("path"), str) for asset in assets)
            and {asset["path"] for asset in assets} == set(expected),
            "recovery_identity_asset_paths_mismatch")
    for asset in assets:
        reference = expected[asset["path"]]
        require(asset.get("hash_match") is True and asset.get("status") == "MATCH",
                "recovery_identity_asset_hash_gate_failed")
        for field in ("sha256", "git_blob_sha", "size"):
            require(asset.get(field) == reference[field]
                    and asset.get("expected_" + field) == reference[field],
                    "recovery_identity_original_bytes_mismatch")
        source = asset.get("source")
        require(isinstance(source, dict)
                and source.get("repository") == "dofaromg/flow-tasks"
                and source.get("commit") == "cb73e661a02eeb540db02398cb61eaa51c5e77e3"
                and source.get("path") == reference["source_path"],
                "recovery_identity_source_lineage_mismatch")
    return {
        "original_asset_count": len(assets),
        "original_bytes_match": True,
        "server_host_gate_match": True,
        "runtime_operational": "NOT_ASSERTED",
        "identity_payload_sha256": digest(canonical(data)),
    }


async def inspect_session(read_stream, write_stream, args, tool_args, receipt):
    from mcp import ClientSession
    from mcp.types import Implementation, PaginatedRequestParams

    async with ClientSession(
        read_stream, write_stream,
        read_timeout_seconds=timedelta(seconds=REQUEST_TIMEOUT),
        client_info=Implementation(name="MRL_mcp_sdk_acceptance_v1", version="1.0.0"),
    ) as session:
        receipt["current_stage"] = "initialize"
        initialized = await session.initialize()
        # initialize() is the SDK handshake and also sends notifications/initialized.
        require(initialized.protocolVersion == PROTOCOL_VERSION,
                "negotiated_protocol_mismatch")
        check(receipt, "initialize", protocol_version=initialized.protocolVersion)

        receipt["current_stage"] = "service_identity"
        identity = initialized.serverInfo.model_dump(mode="json", by_alias=True)
        require(identity.get("name") == args.expected_server_name
                and identity.get("version") == args.expected_server_version,
                "server_identity_mismatch")
        signatures = [identity[key] for key in ("originSignature", "origin_signature")
                      if key in identity]
        require(bool(signatures) and all(value == ORIGIN_SIGNATURE for value in signatures),
                "origin_signature_missing_or_mismatch")
        check(receipt, "service_identity", identity_sha256=digest(canonical(identity)))

        receipt["current_stage"] = "tools_list"
        require(initialized.capabilities.tools is not None, "tools_capability_missing")
        tools = {}
        cursor = None
        seen_cursors = set()
        pages = 0
        for pages in range(1, MAX_TOOL_PAGES + 1):
            page = await session.list_tools(
                params=PaginatedRequestParams(cursor=cursor) if cursor is not None else None,
            )
            for tool in page.tools:
                require(tool.name not in tools, "duplicate_tool_name")
                tools[tool.name] = tool
                require(len(tools) <= MAX_TOOLS, "tool_count_limit_exceeded")
            cursor = page.nextCursor
            if cursor is None:
                break
            require(cursor not in seen_cursors, "pagination_cursor_cycle")
            seen_cursors.add(cursor)
        else:
            raise AcceptanceError("pagination_page_limit_exceeded")
        catalog = [tools[name].model_dump(mode="json", by_alias=True, exclude_none=True)
                   for name in sorted(tools)]
        check(receipt, "tools_list", tools_count=len(tools), pages=pages,
              catalog_sha256=digest(canonical(catalog)), echo_available="echo" in tools,
              recovery_identity_available="mrl_recovery_identity" in tools)

        if args.tool == "echo":
            receipt["current_stage"] = "echo_tool"
            require("echo" in tools, "echo_tool_missing")
            schema = tools["echo"].inputSchema
            properties = schema.get("properties", {})
            required_fields = schema.get("required", [])
            require(schema.get("type") == "object"
                    and isinstance(properties, dict)
                    and isinstance(properties.get("message"), dict)
                    and properties["message"].get("type") == "string"
                    and isinstance(required_fields, list)
                    and "message" in required_fields,
                    "echo_input_schema_mismatch")
            result = await session.call_tool("echo", arguments=tool_args)
            require(not result.isError and len(result.content) == 1,
                    "echo_result_error_or_shape_mismatch")
            item = result.content[0]
            require(item.type == "text"
                    and item.text == "Tool echo: " + tool_args["message"],
                    "echo_result_mismatch")
            result_data = result.model_dump(mode="json", by_alias=True, exclude_none=True)
            check(receipt, "echo_tool", arguments_sha256=digest(canonical(tool_args)),
                  result_sha256=digest(canonical(result_data)),
                  result_bytes=len(canonical(result_data)))
        elif args.tool == "mrl_recovery_identity":
            receipt["current_stage"] = "mrl_recovery_identity_tool"
            require("mrl_recovery_identity" in tools, "recovery_identity_tool_missing")
            schema = tools["mrl_recovery_identity"].inputSchema
            require(schema.get("type") == "object"
                    and schema.get("properties") == {}
                    and schema.get("required") == []
                    and schema.get("additionalProperties") is False,
                    "recovery_identity_input_schema_mismatch")
            result = await session.call_tool("mrl_recovery_identity", arguments={})
            require(not result.isError and len(result.content) == 1
                    and result.content[0].type == "text",
                    "recovery_identity_result_shape_mismatch")
            raw_text = result.content[0].text
            require(len(raw_text.encode("utf-8")) <= 32768, "recovery_identity_result_too_large")
            try:
                identity_data = json.loads(raw_text)
            except (ValueError, TypeError):
                raise AcceptanceError("recovery_identity_result_invalid_json") from None
            check(receipt, "mrl_recovery_identity_tool",
                  **verify_recovery_identity(identity_data))
        else:
            receipt["checks"].append({"name": "tool_call", "status": "NOT_REQUESTED"})
        receipt["current_stage"] = "session_close"


async def run_transport(endpoint, headers, args, tool_args, receipt):
    import httpx
    from mcp.client.sse import sse_client
    from mcp.client.streamable_http import streamable_http_client

    receipt["current_stage"] = "transport_connect"
    timeout = httpx.Timeout(REQUEST_TIMEOUT, read=30.0)
    async with asyncio.timeout(TOTAL_TIMEOUT):
        if args.transport == "streamable-http":
            async with httpx.AsyncClient(
                headers=headers, timeout=timeout, follow_redirects=False,
            ) as client:
                async with streamable_http_client(
                    endpoint, http_client=client, terminate_on_close=True,
                ) as (read_stream, write_stream, _get_session_id):
                    await inspect_session(read_stream, write_stream, args, tool_args, receipt)
        else:
            async with sse_client(
                endpoint, headers=headers, timeout=REQUEST_TIMEOUT, sse_read_timeout=30.0,
            ) as (read_stream, write_stream):
                await inspect_session(read_stream, write_stream, args, tool_args, receipt)
    check(receipt, "transport_context_closed")


def main(argv=None) -> int:
    # SDK transport exceptions may log response bodies or endpoint/session details.
    # This standalone verifier emits its own metadata-only diagnostics instead.
    logging.disable(logging.CRITICAL)
    receipt = {
        "schema": "MRL_mcp_sdk_acceptance_v1",
        "origin_signature": ORIGIN_SIGNATURE,
        "started_at_utc": utc_now(),
        "observed_execution": {
            "hostname": socket.gethostname(),
            "os": platform.system(),
            "python": platform.python_version(),
        },
        "scope": "Selected MCP SDK transport on the observed client host.",
        "dl580_recovery_claim": "NOT_ASSERTED",
        "roots_list": "SERVER_TO_CLIENT_FEATURE_NOT_REQUESTED",
        "status": "BLOCKED",
        "checks": [],
        "current_stage": "configuration",
    }
    args = None
    destination = None
    exit_code = 3
    try:
        args = parse_cli(argv)
        receipt["transport"] = args.transport
        endpoint, headers, tool_args = configuration(args, os.environ)
        receipt["endpoint_sha256"] = digest(endpoint.encode("utf-8"))
        receipt["authenticated_header_configured"] = True
        if args.expected_client_host is not None:
            require(socket.gethostname().casefold() == args.expected_client_host.casefold(),
                    "client_hostname_mismatch", blocked=True)
            check(receipt, "expected_client_hostname")
        destination = prepare_destination(args.out)
        check(receipt, "configuration")
        receipt["current_stage"] = "dependencies"
        check(receipt, "dependencies", versions=dependency_versions())
        receipt["status"] = "FAIL"
        asyncio.run(run_transport(endpoint, headers, args, tool_args, receipt))
        receipt["status"] = "PASS"
        exit_code = 0
    except KeyboardInterrupt:
        receipt["status"] = "INTERRUPTED"
        receipt["checks"].append({
            "name": receipt["current_stage"], "status": "INTERRUPTED",
        })
        exit_code = 130
    except Exception as exc:
        metadata = safe_error(exc)
        blocked = any(item.get("blocked") for item in metadata["errors"])
        receipt["status"] = "BLOCKED" if blocked else "FAIL"
        receipt["checks"].append({
            "name": receipt["current_stage"], "status": receipt["status"], **metadata,
        })
        exit_code = 3 if blocked else 2
    receipt.pop("current_stage", None)
    receipt["finished_at_utc"] = utc_now()
    payload = canonical(receipt) + b"\n"
    if args is not None and args.out:
        if destination is None:
            print(json.dumps({"status": "BLOCKED", "receipt_written": False,
                              "diagnostic": receipt["checks"][-1:]}, sort_keys=True))
            return 3
        try:
            write_receipt_exclusive(destination, payload)
        except Exception as exc:
            print(json.dumps({"status": "BLOCKED", "receipt_written": False,
                              "verification_status": receipt["status"],
                              **safe_error(exc)}, sort_keys=True))
            return 3
        print(json.dumps({
            "status": receipt["status"], "receipt_written": True,
            "receipt_sha256": digest(payload), "receipt_bytes": len(payload),
            "observed_execution": receipt["observed_execution"],
        }, sort_keys=True))
    else:
        print(payload.decode("utf-8"), end="")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
