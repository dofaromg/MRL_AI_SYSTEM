#!/usr/bin/env python3
r"""Read-only probes for explicitly configured MRL recovery dependencies.

origin_signature: MrLiouWord
Environment URLs are base URLs, optionally including an existing proxy prefix:
  MRL_QDRANT_URL    GET /, /healthz, /readyz, /collections
  MRL_QDRANT_API_KEY  Optional existing credential, sent only in api-key.
  MRL_MINIO_URL     GET /minio/health/live and /minio/health/ready
  MRL_METAENV_URL   GET /api/v1/env/health from the existing canonical API.
No endpoint is guessed. Missing URLs remain UNVERIFIED. All redirects are refused;
HTTP is allowed only for literal loopback addresses; other hosts require HTTPS.
Response payloads, collection names, credentials, and environment IDs are never
printed or written into a receipt. This command performs no data writes to services.
A health/read-only success never establishes storage write/read/delete acceptance.

Use --stdout for metadata, or --out D:\...\unique.json for a new local receipt.
MetaEnv source: MRL_Adapters/MetaEnv/MRL_MetaEnv_Control_API_v1.yaml
at dofaromg/MRL_AI_SYSTEM commit 3c51612c2ddee1b3c561882c20474694dc497792.
That source defines no canonical identity field or authentication scheme.
"""
from __future__ import annotations
import argparse
import hashlib
import ipaddress
import json
import os
from pathlib import Path
import platform
import re
import socket
import sys
import tempfile
import time
from datetime import datetime, timezone
from urllib.error import HTTPError
from urllib.parse import urlsplit, urlunsplit
from urllib.request import HTTPRedirectHandler, Request, build_opener

sys.dont_write_bytecode = True
ORIGIN_SIGNATURE = "MrLiouWord"
MAX_BODY = 65536
NETWORK_TIMEOUT = 3.0
BODY_DEADLINE = 6.0


class ProbeError(Exception):
    def __init__(self, code, *, metadata=None):
        super().__init__(code)
        self.code = code
        self.metadata = metadata or {}


class NoRedirect(HTTPRedirectHandler):
    def redirect_request(self, request, fp, code, message, headers, newurl):
        return None


class SafeParser(argparse.ArgumentParser):
    def error(self, message):
        raise ProbeError("cli_arguments_invalid")


def require(condition, code):
    if not condition:
        raise ProbeError(code)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def encode(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True,
                      separators=(",", ":"), allow_nan=False).encode("utf-8")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds")


def safe_error(exc):
    value = {"error_type": type(exc).__name__}
    if isinstance(exc, ProbeError):
        value["error_code"] = exc.code
        value.update(exc.metadata)
    error_number = getattr(exc, "errno", None)
    if isinstance(error_number, int):
        value["os_error_number"] = error_number
    return value


def validate_base(value):
    require(bool(value) and value.strip() == value and len(value) <= 2048,
            "base_url_invalid")
    require(not any(ord(char) < 32 or ord(char) == 127 for char in value),
            "base_url_control_character")
    try:
        parsed = urlsplit(value)
        parsed.port
    except ValueError:
        raise ProbeError("base_url_parse_failed") from None
    require(parsed.scheme in ("http", "https") and bool(parsed.hostname),
            "base_url_scheme_or_host_invalid")
    require(parsed.username is None and parsed.password is None
            and not parsed.query and not parsed.fragment,
            "base_url_credentials_query_or_fragment_forbidden")
    try:
        loopback = ipaddress.ip_address(parsed.hostname).is_loopback
    except ValueError:
        loopback = False
    require(parsed.scheme == "https" or loopback, "http_requires_literal_loopback")
    return parsed


def endpoint(base, path):
    parsed = validate_base(base)
    return urlunsplit((parsed.scheme, parsed.netloc,
                       parsed.path.rstrip("/") + path, "", ""))


def request_metadata(url, headers=None):
    """Bounded GET; return a body only in memory for contract validation."""
    start = time.monotonic()
    request_headers = {
        "User-Agent": "MRL-Recovery-Validator/1.0",
        "Accept": "application/json, text/plain, */*",
        "Accept-Encoding": "identity",
    }
    request_headers.update(headers or {})
    request = Request(url, headers=request_headers, method="GET")
    try:
        response = build_opener(NoRedirect()).open(request, timeout=NETWORK_TIMEOUT)
    except HTTPError as exc:
        status = exc.code
        exc.close()
        code = "redirect_refused" if 300 <= status < 400 else "http_status_not_200"
        raise ProbeError(code, metadata={"http_status": status}) from None
    with response:
        require(response.status == 200, "http_status_not_200")
        require(response.geturl() == url, "redirect_refused")
        data = bytearray()
        while True:
            require(time.monotonic() - start <= BODY_DEADLINE, "response_deadline_exceeded")
            chunk = response.read1(min(4096, MAX_BODY + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
            require(len(data) <= MAX_BODY, "response_size_limit_exceeded")
        body = bytes(data)
        media_type = response.headers.get_content_type()
        content_type = media_type if media_type in ("application/json", "text/plain", "application/xml") else "other"
    return body, {
        "http_status": 200, "response_bytes": len(body),
        "response_sha256": sha(body),
        "elapsed_ms": round((time.monotonic() - start) * 1000),
        "content_type": content_type,
    }


def get_json(body):
    try:
        value = json.loads(body)
    except (ValueError, UnicodeError):
        raise ProbeError("response_invalid_json") from None
    require(isinstance(value, dict), "response_json_object_required")
    return value


def get_step(record, base, path, name, headers=None):
    try:
        body, metadata = request_metadata(endpoint(base, path), headers=headers)
    except Exception as exc:
        record["checks"].append({"name": name, "path": path, "status": "FAIL", **safe_error(exc)})
        raise
    item = {"name": name, "path": path, "status": "HTTP_RESPONSE_VERIFIED", **metadata}
    record["checks"].append(item)
    return body, item


def probe_qdrant(base, record, environ):
    key = environ.get("MRL_QDRANT_API_KEY", "")
    headers = {}
    if key:
        require(len(key) <= 4096 and key.isascii() and key.strip() == key
                and not any(ord(char) < 32 or ord(char) == 127 for char in key),
                "qdrant_api_key_invalid")
        headers["api-key"] = key
    record["api_key_header_configured"] = bool(key)
    body, item = get_step(record, base, "/", "instance_identity", headers)
    info = get_json(body)
    version = info.get("version", "")
    require(info.get("title") == "qdrant - vector search engine"
            and isinstance(version, str)
            and re.fullmatch(r"[0-9]+\.[0-9]+\.[0-9]+(?:[-+][A-Za-z0-9.-]+)?", version)
            and len(version) <= 64,
            "qdrant_instance_contract_mismatch")
    item.update(status="PASS", version=version)
    record["service_type_identity"] = "RESPONSE_CONTRACT_MATCH"
    for path, name, expected in (
        ("/healthz", "health", b"healthz check passed"),
        ("/readyz", "readiness", b"all shards are ready"),
    ):
        body, item = get_step(record, base, path, name, headers)
        require(body.strip() == expected, "qdrant_health_contract_mismatch")
        item["status"] = "PASS"
    body, item = get_step(record, base, "/collections", "collections_read_only", headers)
    catalog = get_json(body)
    result = catalog.get("result")
    require(catalog.get("status") == "ok" and isinstance(result, dict)
            and isinstance(result.get("collections"), list),
            "qdrant_collections_contract_mismatch")
    require(all(isinstance(entry, dict) and isinstance(entry.get("name"), str)
                for entry in result["collections"]), "qdrant_collections_contract_mismatch")
    item.update(status="PASS", collections_count=len(result["collections"]))
    record["probe_status"] = "PASS"


def probe_minio(base, record, environ):
    for path, name in (
        ("/minio/health/live", "liveness"),
        ("/minio/health/ready", "readiness"),
    ):
        _body, item = get_step(record, base, path, name)
        item["status"] = "PASS_HEALTH_HTTP_ONLY"
    record["service_type_identity"] = "UNVERIFIED_HEALTH_ENDPOINT_ONLY"
    record["probe_status"] = "PASS"
    record["scope"] = "Health endpoints only; no S3 authentication or object operation."


def probe_metaenv(base, record, environ):
    body, item = get_step(record, base, "/api/v1/env/health", "canonical_health_api")
    info = get_json(body)
    record["canonical_identity"] = "UNVERIFIED_NO_IDENTITY_FIELD_IN_SOURCE_API"
    record["authentication_contract"] = "NOT_DEFINED_IN_SOURCE_API"
    require("ok" not in info or isinstance(info["ok"], bool),
            "metaenv_ok_type_mismatch")
    require("env_id" not in info or info["env_id"] is None
            or isinstance(info["env_id"], str), "metaenv_env_id_type_mismatch")
    if "time" in info:
        require(isinstance(info["time"], str), "metaenv_time_type_mismatch")
        try:
            parsed = datetime.fromisoformat(info["time"].replace("Z", "+00:00"))
        except ValueError:
            raise ProbeError("metaenv_time_format_mismatch") from None
        require(parsed.tzinfo is not None, "metaenv_time_requires_timezone")
    if info.get("ok") is False:
        raise ProbeError("metaenv_reports_unhealthy")
    if info.get("ok") is True and "time" in info:
        item["status"] = "PASS_HEALTH_CONTRACT"
        record["probe_status"] = "PASS"
    else:
        item["status"] = "UNVERIFIED_HEALTH_SIGNAL_INCOMPLETE"
        record["probe_status"] = "UNVERIFIED"
    # Do not copy env_id, timestamps supplied by the server, or other response data.


def probe_all(environ):
    records = []
    for name, variable, operation in (
        ("qdrant", "MRL_QDRANT_URL", probe_qdrant),
        ("minio", "MRL_MINIO_URL", probe_minio),
        ("metaenv", "MRL_METAENV_URL", probe_metaenv),
    ):
        record = {
            "service": name, "endpoint_env": variable, "checks": [],
            "probe_status": "UNVERIFIED",
            "storage_write_read_delete_acceptance": "NOT_RUN",
        }
        base = environ.get(variable, "")
        if not base:
            record["reason"] = "ENDPOINT_NOT_CONFIGURED"
            records.append(record)
            continue
        try:
            validate_base(base)
            record["endpoint_sha256"] = sha(base.encode("utf-8"))
            operation(base, record, environ)
        except Exception as exc:
            record.update(probe_status="FAIL", **safe_error(exc))
        records.append(record)
    return records


def output_target(value):
    if value is None:
        return None
    require(os.name == "nt", "receipt_requires_windows_local_d_drive")
    import ctypes
    function = ctypes.windll.kernel32.GetDriveTypeW
    function.argtypes = [ctypes.c_wchar_p]
    function.restype = ctypes.c_uint
    require(function("D:\\") == 3, "receipt_d_drive_must_be_local_fixed")
    requested = Path(value)
    require(requested.is_absolute() and requested.drive.upper() == "D:"
            and requested.suffix.lower() == ".json", "receipt_requires_absolute_d_json_path")
    target = requested.resolve(strict=False)
    require(target.drive.upper() == "D:", "receipt_reparse_outside_d_drive")
    require(not target.exists(), "receipt_already_exists")
    target.parent.mkdir(parents=True, exist_ok=True)
    require(target.resolve(strict=False).drive.upper() == "D:", "receipt_reparse_outside_d_drive")
    return target


def save_exclusive(target, payload):
    require(os.name == "nt" and target.resolve(strict=False).drive.upper() == "D:",
            "receipt_requires_windows_local_d_drive")
    descriptor, name = tempfile.mkstemp(prefix=".mrl-dependency-", suffix=".tmp", dir=target.parent)
    temporary = Path(name)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(payload)
            stream.flush()
            os.fsync(stream.fileno())
        os.rename(temporary, target)  # Atomic, no replacement on Windows.
    finally:
        temporary.unlink(missing_ok=True)


def main(argv=None):
    parser = SafeParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--stdout", action="store_true")
    group.add_argument("--out")
    parser.add_argument("--expected-client-host")
    try:
        args = parser.parse_args(argv)
        if args.expected_client_host:
            require(socket.gethostname().casefold() == args.expected_client_host.casefold(),
                    "client_hostname_mismatch")
        target = output_target(args.out)
        receipt = {
            "schema": "MRL_recovery_dependency_probe_v1",
            "origin_signature": ORIGIN_SIGNATURE,
            "started_at_utc": now(),
            "observed_execution": {
                "hostname": socket.gethostname(), "os": platform.system(),
                "python": platform.python_version(),
            },
            "recovery_acceptance": "NOT_ASSERTED",
            "probe_scope": "Read-only health and explicitly listed API checks.",
            "services": probe_all(os.environ),
            "finished_at_utc": now(),
        }
        statuses = [record["probe_status"] for record in receipt["services"]]
        receipt["status"] = (
            "PROBE_FAILED" if "FAIL" in statuses else
            "PROBE_INCOMPLETE" if "UNVERIFIED" in statuses else "PROBE_COMPLETE"
        )
        receipt["missing_endpoint_count"] = sum(
            record.get("reason") == "ENDPOINT_NOT_CONFIGURED"
            for record in receipt["services"]
        )
        payload = encode(receipt) + b"\n"
        if target is not None:
            save_exclusive(target, payload)
            print(json.dumps({
                "status": receipt["status"], "receipt_written": True,
                "receipt_bytes": len(payload), "receipt_sha256": sha(payload),
                "observed_execution": receipt["observed_execution"],
            }, sort_keys=True))
        else:
            print(payload.decode("utf-8"), end="")
        return 0 if receipt["status"] == "PROBE_COMPLETE" else 2
    except KeyboardInterrupt:
        print(json.dumps({"status": "INTERRUPTED", "recovery_acceptance": "NOT_ASSERTED"}))
        return 130
    except Exception as exc:
        print(json.dumps({"status": "BLOCKED", "receipt_written": False, **safe_error(exc)},
                         sort_keys=True))
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
