#!/usr/bin/env python3
"""Host-local temporary Qdrant CRUD probe, revision 3. origin_signature: MrLiouWord.
Consumes an already completed official stage; never downloads or controls its PID.
Only newly created probe files/collection and the retained child handle are mutated.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import platform
import re
import secrets
import socket
import struct
import subprocess
import sys
import time
import urllib.error
import urllib.request
import uuid
import zipfile
from datetime import datetime, timezone

HOST = "WIN-PBVUI7VK2A6"
ORIGIN = "MrLiouWord"
COMMIT = "be2f1d63ed355bb972241cc0db4eeecceeb0f04d"
OPS = Path(r"D:\MRL_Mother\Recovery\_operations\LocalAI_20261010_R02_be2f1d63")
STAGE_ROOT = Path(r"D:\MRL_Mother\Dependencies\Qdrant")
STORAGE_PARENT = Path(r"D:\MRL_Mother\QdrantProbe")
STAGE_SCRIPT = Path(r"D:\MRL_Mother\Recovery\LocalAI_20261010_v2\deploy\dl580\recovery\MRL_Qdrant_Stage_v1.ps1")
STAGE_SCRIPT_HASH = "4bc2ef52912ec2453f226b5a0eb7fd3f6b64c76c7b2c00f876d8559378969848"
ARCHIVE_HASH = "7d86596f16c6e85d45a50312f5e16ccb51e059b62e3d7308110cb65b4c799a4d"
ARCHIVE_BYTES = 30243552
SOURCE_URL = "https://github.com/qdrant/qdrant/releases/download/v1.19.2/qdrant-x86_64-pc-windows-msvc.zip"
BASE = "http://127.0.0.1:6333"
VECTOR = [0.25, 0.5, 0.75, 1.0]
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
RUN_RE = re.compile(r"qdrant-v1\.19\.2-\d{8}T\d{6}Z-[0-9a-f]{32}\Z")

class ProbeFailure(Exception):
    pass

def require(condition, code):
    if not condition:
        raise ProbeFailure(code)

def utc():
    return datetime.now(timezone.utc).isoformat()

def digest_stream(f):
    h = hashlib.sha256()
    total = 0
    while True:
        b = f.read(1024 * 1024)
        if not b:
            break
        total += len(b)
        h.update(b)
    return h.hexdigest(), total

def file_digest(path):
    with open(path, "rb") as f:
        return digest_stream(f)

def strict_json(b):
    def no_duplicates(items):
        out = {}
        for k, v in items:
            require(k not in out, "json_duplicate_key")
            out[k] = v
        return out
    return json.loads(b.decode("utf-8-sig"), object_pairs_hook=no_duplicates)

DWORD = C.c_uint32
SIZE_T = C.c_size_t
HANDLE = C.c_void_p

class BasicLimits(C.Structure):
    _fields_ = [
        ("process_time", C.c_int64), ("job_time", C.c_int64),
        ("flags", DWORD), ("min_working", SIZE_T), ("max_working", SIZE_T),
        ("active_limit", DWORD), ("affinity", SIZE_T),
        ("priority", DWORD), ("scheduling", DWORD),
    ]

class IOCounts(C.Structure):
    _fields_ = [(x, C.c_uint64) for x in
                ("read_ops", "write_ops", "other_ops", "read_bytes", "write_bytes", "other_bytes")]

class ExtendedLimits(C.Structure):
    _fields_ = [("basic", BasicLimits), ("io", IOCounts),
                ("process_memory", SIZE_T), ("job_memory", SIZE_T),
                ("peak_process_memory", SIZE_T), ("peak_job_memory", SIZE_T)]

class TCP4(C.Structure):
    _fields_ = [(x, DWORD) for x in ("state", "local", "port", "remote", "remote_port", "pid")]

class TCP6(C.Structure):
    _fields_ = [("local", C.c_ubyte * 16), ("local_scope", DWORD),
                ("port", DWORD), ("remote", C.c_ubyte * 16),
                ("remote_scope", DWORD), ("remote_port", DWORD),
                ("state", DWORD), ("pid", DWORD)]

class WinAPI:
    def __init__(self):
        require(os.name == "nt", "windows_required")
        require(C.sizeof(C.c_void_p) == 8, "python_x64_required")
        self.k = C.WinDLL("kernel32", use_last_error=True)
        self.ip = C.WinDLL("iphlpapi", use_last_error=True)
        signatures = [
            ("GetFileAttributesW", [C.c_wchar_p], DWORD),
            ("GetDriveTypeW", [C.c_wchar_p], DWORD),
            ("CreateJobObjectW", [C.c_void_p, C.c_wchar_p], HANDLE),
            ("SetInformationJobObject", [HANDLE, C.c_int, C.c_void_p, DWORD], C.c_int),
            ("AssignProcessToJobObject", [HANDLE, HANDLE], C.c_int),
            ("TerminateJobObject", [HANDLE, C.c_uint], C.c_int),
            ("CloseHandle", [HANDLE], C.c_int),
            ("QueryFullProcessImageNameW", [HANDLE, DWORD, C.c_wchar_p, C.POINTER(DWORD)], C.c_int),
        ]
        for name, args, result in signatures:
            f = getattr(self.k, name)
            f.argtypes, f.restype = args, result
        self.ip.GetExtendedTcpTable.argtypes = [
            C.c_void_p, C.POINTER(DWORD), C.c_int, DWORD, C.c_int, DWORD]
        self.ip.GetExtendedTcpTable.restype = DWORD

    def path(self, value, exists=True):
        s = os.path.abspath(os.fspath(value))
        require(os.path.splitdrive(s)[0].upper() == "D:", "absolute_d_path_required")
        require(self.k.GetDriveTypeW("D:\\") == 3, "fixed_d_required")
        p = Path(s)
        for x in [*reversed(p.parents), p]:
            a = int(self.k.GetFileAttributesW(str(x)))
            if a == 0xffffffff:
                require(not exists and x == p and C.get_last_error() in (2, 3),
                        "d_path_missing_or_inaccessible")
            else:
                require(not (a & 0x400), "d_path_reparse_rejected")
        return p

    def listeners(self):
        out = []
        for af, row_cls in ((2, TCP4), (23, TCP6)):
            size = DWORD(0)
            r = self.ip.GetExtendedTcpTable(None, C.byref(size), False, af, 3, 0)
            require(r in (0, 122), "tcp_table_size_failed")
            for _ in range(3):
                require(4 <= size.value <= 16 * 1024 * 1024, "tcp_table_size_invalid")
                buf = C.create_string_buffer(size.value)
                r = self.ip.GetExtendedTcpTable(buf, C.byref(size), False, af, 3, 0)
                if r != 122:
                    break
            require(r == 0, "tcp_table_read_failed")
            count = DWORD.from_buffer_copy(buf.raw[:4]).value
            row_size = C.sizeof(row_cls)
            require(4 + count * row_size <= len(buf), "tcp_table_bounds_invalid")
            for i in range(count):
                row = row_cls.from_buffer_copy(buf.raw, 4 + i * row_size)
                ip = (socket.inet_ntop(socket.AF_INET, struct.pack("<I", row.local))
                      if af == 2 else socket.inet_ntop(socket.AF_INET6, bytes(row.local)))
                out.append((ip, socket.ntohs(row.port & 0xffff), int(row.pid)))
        return out

    def job(self):
        h = self.k.CreateJobObjectW(None, None)
        require(bool(h), "job_create_failed")
        limits = ExtendedLimits()
        limits.basic.flags = 0x2000  # JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE
        if not self.k.SetInformationJobObject(h, 9, C.byref(limits), C.sizeof(limits)):
            self.k.CloseHandle(h)
            raise ProbeFailure("job_limits_failed")
        return h

    def image(self, process):
        size = DWORD(32768)
        buf = C.create_unicode_buffer(size.value)
        require(self.k.QueryFullProcessImageNameW(int(process._handle), 0, buf, C.byref(size)),
                "child_image_query_failed")
        return self.path(buf.value)

def same_path(a, b):
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))

def under(path, parent):
    try:
        Path(path).relative_to(parent)
        return True
    except ValueError:
        return False

def verify_stage_header(d):
    require(isinstance(d, dict), "stage_receipt_not_object")
    for key, expected in {
        "schema": "MRL_Qdrant_Stage_v1",
        "origin_signature": ORIGIN,
        "status": "STAGED_VERIFIED",
        "source_url": SOURCE_URL,
        "source_release": "v1.19.2",
        "github_release_asset_id": 612861224,
        "archive_bytes": ARCHIVE_BYTES,
        "archive_sha256": ARCHIVE_HASH,
        "observed_client_host": HOST,
        "runtime_acceptance": "NOT_RUN",
        "storage_write_read_delete_acceptance": "NOT_RUN",
    }.items():
        require(type(d.get(key)) is type(expected) and d.get(key) == expected,
                "stage_identity_or_source_mismatch")
    require(d.get("server_started") is False and d.get("service_installed") is False,
            "stage_runtime_claim_invalid")
    require(isinstance(d.get("executable_sha256"), str) and
            HEX64.fullmatch(d["executable_sha256"]), "stage_exe_hash_invalid")
    require(type(d.get("extracted_file_count")) is int and
            1 <= d["extracted_file_count"] <= 512, "stage_file_count_invalid")
    require(isinstance(d.get("extracted_files"), list) and
            len(d["extracted_files"]) == d["extracted_file_count"], "stage_file_records_invalid")

def verify_stage(win, receipt_path):
    script = win.path(STAGE_SCRIPT)
    require(file_digest(script) == (STAGE_SCRIPT_HASH, 14160), "stage_script_source_mismatch")
    root = win.path(STAGE_ROOT)
    rp = win.path(receipt_path)
    require(rp.name == "stage-receipt.json" and same_path(rp.parent.parent, root) and
            RUN_RE.fullmatch(rp.parent.name), "stage_receipt_location_invalid")
    require(rp.stat().st_size <= 512 * 1024, "stage_receipt_size_invalid")
    raw = rp.read_bytes()
    d = strict_json(raw)
    verify_stage_header(d)
    stage = win.path(d["stage_directory"])
    require(same_path(stage, rp.parent), "stage_directory_mismatch")
    archive = win.path(stage / "qdrant-x86_64-pc-windows-msvc.zip")
    require(file_digest(archive) == (ARCHIVE_HASH, ARCHIVE_BYTES), "archive_reverification_failed")
    expanded = win.path(stage / "expanded")
    exe = win.path(d["executable_path"])
    require(under(exe, expanded) and exe.name.lower() == "qdrant.exe", "exe_location_invalid")
    evidence = {}
    for f in d["extracted_files"]:
        require(isinstance(f, dict) and isinstance(f.get("relative_path"), str) and
                type(f.get("bytes")) is int and f["bytes"] > 0 and
                isinstance(f.get("sha256"), str) and HEX64.fullmatch(f["sha256"]),
                "stage_file_record_invalid")
        name = f["relative_path"].replace("\\", "/").casefold()
        require(name not in evidence, "stage_file_record_duplicate")
        evidence[name] = f
    expected_paths = set()
    qdrant_count = 0
    with zipfile.ZipFile(archive, "r") as z:
        for entry in z.infolist():
            name = entry.filename.replace("\\", "/")
            pp = PurePosixPath(name)
            require(not pp.is_absolute() and ".." not in pp.parts and ":" not in name,
                    "archive_member_path_invalid")
            if entry.is_dir():
                continue
            require(0 < entry.file_size <= 1024 * 1024 * 1024, "archive_member_size_invalid")
            path = win.path(expanded.joinpath(*pp.parts))
            require(under(path, expanded), "archive_member_boundary_invalid")
            with z.open(entry, "r") as member:
                wanted = digest_stream(member)
            actual = file_digest(path)
            f = evidence.get(name.casefold())
            require(f is not None and actual == wanted == (f["sha256"], f["bytes"]),
                    "official_package_file_mismatch")
            expected_paths.add(os.path.normcase(str(path)))
            if path.name.lower() == "qdrant.exe":
                qdrant_count += 1
                require(same_path(path, exe) and actual[0] == d["executable_sha256"],
                        "official_exe_mismatch")
    observed_paths = set()
    for folder, dirs, files in os.walk(expanded, followlinks=False):
        for name in dirs:
            win.path(Path(folder) / name)
        for name in files:
            observed_paths.add(os.path.normcase(str(win.path(Path(folder) / name))))
    require(qdrant_count == 1 and observed_paths == expected_paths and
            len(expected_paths) == d["extracted_file_count"], "official_package_layout_mismatch")
    return exe, {
        "status": "STAGED_VERIFIED",
        "source_commit": COMMIT,
        "stage_script_sha256": STAGE_SCRIPT_HASH,
        "stage_receipt_sha256": hashlib.sha256(raw).hexdigest(),
        "archive_sha256": ARCHIVE_HASH,
        "archive_bytes": ARCHIVE_BYTES,
        "executable_sha256": d["executable_sha256"],
        "extracted_file_count": d["extracted_file_count"],
        "official_package_reverified": True,
    }

def listener_contract(rows, pid):
    own = [r for r in rows if r[2] == pid]
    on_port = [r for r in rows if r[1] == 6333]
    return own == [("127.0.0.1", 6333, pid)] and on_port == own


def owned_listener_metadata(rows, pid):
    # Only metadata belonging to our retained child, never the global table.
    own = sorted(r for r in rows if r[2] == pid)
    return {"owned_row_count": len(own),
            "rows_truncated": len(own) > 64,
            "rows": [{"local_address": ip, "local_port": port, "owning_pid": owner}
                     for ip, port, owner in own[:64]]}

def point_contract(d, point_id, nonce):
    if not isinstance(d, dict) or d.get("status") != "ok":
        return False
    rows = d.get("result")
    return (isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict)
            and rows[0].get("id") == point_id
            and isinstance(rows[0].get("vector"), list)
            and all(type(v) in (int, float) for v in rows[0]["vector"])
            and rows[0]["vector"] == VECTOR
            and rows[0].get("payload") == {"origin_signature": ORIGIN, "probe_nonce": nonce})


ERROR_PATTERNS = {
    "path_too_long": r"file.?name.{0,20}too long|path.{0,20}too long|os error\s*[:( ]*206\b|winerror\s*[:( ]*206\b",
    "path_not_found": r"path.{0,30}(?:not found|cannot find)|(?:os error|winerror)\s*[:( ]*3\b",
    "access_denied": r"access.{0,6}denied|permission denied|(?:os error|winerror)\s*[:( ]*5\b",
    "disk_full": r"no space left|disk.{0,10}full|not enough space|(?:os error|winerror)\s*[:( ]*112\b",
    "compressed_or_sparse": r"compressed|compression|sparse|file system limitation",
    "mapped_file": r"user.mapped|mapped section|\bmmap\b|memory.map",
    "invalid_argument": r"invalid argument|parameter is incorrect|(?:os error|winerror)\s*[:( ]*87\b",
    "rocksdb": r"\brocksdb\b",
    "wal": r"\bwal\b|write.ahead",
    "segment": r"\bsegments?\b",
    "already_exists": r"already exists",
    "validation": r"validation|invalid vector|vector dimension",
}

def value_kind(value):
    return {type(None): "null", bool: "boolean", int: "number", float: "number",
            str: "string", list: "array", dict: "object"}.get(type(value), "other")

def http_metadata(method, route, phase, status, raw=None, parsed=None):
    # No response text, error message, URL query, payload, path or key is exported.
    text = raw.decode("utf-8", errors="replace") if raw is not None and status >= 400 else ""
    classes = [k for k, pattern in ERROR_PATTERNS.items() if re.search(pattern, text, re.I)]
    codes = sorted({int(v) for v in re.findall(
        r"(?:os error|winerror|windows error)\s*[:( ]*(\d{1,6})\b", text, re.I)})
    d = parsed if isinstance(parsed, dict) else {}
    return {"method": method, "route": route, "phase": phase, "http_status": int(status),
            "response_bytes": len(raw) if raw is not None else None,
            "response_sha256": hashlib.sha256(raw).hexdigest() if raw is not None else None,
            "body_inspected": raw is not None,
            "json_top_type": value_kind(parsed),
            "json_status_type": value_kind(d.get("status")),
            "json_status_is_ok": d.get("status") == "ok",
            "result_type": value_kind(d.get("result")) if "result" in d else "absent",
            "result_is_true": d.get("result") is True,
            "error_keyword_classes": classes,
            "os_error_codes": codes[:16]}

def storage_metadata(win, root):
    root = win.path(root)
    longest = len(str(root))
    count = 1
    compressed_dirs = 0
    root_attrs = int(win.k.GetFileAttributesW(str(root)))
    for folder, dirs, files in os.walk(root, followlinks=False):
        p = win.path(folder)
        compressed_dirs += int(bool(int(win.k.GetFileAttributesW(str(p))) & 0x800))
        for name in dirs + files:
            p = win.path(Path(folder) / name)
            require(under(p, root), "storage_metadata_boundary_invalid")
            longest = max(longest, len(str(p)))
            count += 1
            if count >= 4096:
                return {"root_path_chars": len(str(root)), "longest_existing_path_chars": longest,
                        "entries_inspected": count, "truncated": True,
                        "root_compressed": bool(root_attrs & 0x800),
                        "compressed_directories": compressed_dirs}
    return {"root_path_chars": len(str(root)), "longest_existing_path_chars": longest,
            "entries_inspected": count, "truncated": False,
            "root_compressed": bool(root_attrs & 0x800),
            "compressed_directories": compressed_dirs}

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def write_exclusive(path, obj):
    body = (json.dumps(obj, sort_keys=True, ensure_ascii=True, indent=2) + "\n").encode("utf-8")
    # A unique run directory and xb prevent replacement of any existing receipt.
    with open(path, "xb") as f:
        f.write(body)
        f.flush()
        os.fsync(f.fileno())
    return hashlib.sha256(body).hexdigest(), len(body)

def run(receipt_arg):
    result = {
        "schema": "MRL_Qdrant_Native_Probe_R02_v3",
        "origin_signature": ORIGIN,
        "source_commit": COMMIT,
        "started_at_utc": utc(),
        "status": "FAILED",
        "execution_scope": "DL580_HOST_LOCAL_TEMPORARY_PROBE",
        "service_installed": False,
        "operational_service": "NOT_ASSERTED",
        "stage_process_controlled": False,
        "checks": {},
    }
    child = None
    job = None
    win = None
    run_dir = None
    storage_root = None
    logs = []
    created_here = False
    creation_outcome_uncertain = False
    collection = None
    key = None
    request = None
    stage = "host_preflight"
    try:
        require(os.name == "nt" and platform.node().casefold() == HOST.casefold(),
                "expected_windows_host_required")
        result["observed_client_host"] = platform.node()
        win = WinAPI()
        ops = win.path(OPS)
        require(ops.is_dir(), "operations_directory_required")
        run_dir = ops / ("qdrant_native_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
                         + "_" + uuid.uuid4().hex)
        win.path(run_dir, exists=False)
        run_dir.mkdir()
        win.path(run_dir)
        stage = "stage_receipt_reverification"
        exe, stage_meta = verify_stage(win, receipt_arg)
        result["stage"] = stage_meta
        result["checks"]["official_stage_verified"] = True
        stage = "local_config"
        # A short, new Mother-owned subtree avoids the observed MAX_PATH pressure.
        # Existing storage and NTFS compression attributes are never changed.
        parent = win.path(STORAGE_PARENT, exists=False)
        parent_created = False
        try:
            parent.mkdir()
            parent_created = True
        except FileExistsError:
            pass
        parent = win.path(parent)
        require(parent.is_dir(), "short_storage_parent_not_directory")
        storage_root = parent / uuid.uuid4().hex
        win.path(storage_root, exists=False)
        storage_root.mkdir()
        win.path(storage_root)
        result["owned_storage_root"] = str(storage_root)
        result["storage_parent_created"] = parent_created
        dirs = {n: storage_root / n for n in ("storage", "snapshots", "tmp")}
        for p in dirs.values():
            p.mkdir()
            win.path(p)
        result["storage_before_start"] = storage_metadata(win, storage_root)
        config = {
            "log_level": "INFO", "telemetry_disabled": True,
            "storage": {"storage_path": str(dirs["storage"]),
                        "snapshots_path": str(dirs["snapshots"]),
                        "temp_path": str(dirs["tmp"]),
                        "snapshots_config": {"snapshots_storage": "local"}},
            "service": {"host": "127.0.0.1", "http_port": 6333, "grpc_port": None,
                        "metrics_port": None, "enable_cors": False, "enable_tls": False},
            "cluster": {"enabled": False},
        }
        # This official build enables config's YAML parser only. The JSON-subset
        # document written below is valid YAML and must use the supported .yaml suffix.
        config_path = run_dir / "qdrant-test-config.yaml"
        config_hash, config_bytes = write_exclusive(config_path, config)
        require(file_digest(win.path(config_path)) == (config_hash, config_bytes),
                "config_readback_failed")
        result["config_sha256"] = config_hash
        result["config_bytes"] = config_bytes
        stage = "port_preflight"
        require(not any(r[1] == 6333 for r in win.listeners()), "port_6333_already_in_use")
        lease = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            lease.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
            lease.bind(("127.0.0.1", 6333))
        finally:
            lease.close()
        result["checks"]["port_6333_initially_free"] = True
        key = secrets.token_hex(32)
        removed = [k for k in os.environ if k.upper().startswith("QDRANT")]
        env = {k: v for k, v in os.environ.items()
               if not k.upper().startswith("QDRANT") and k.upper() not in ("RUN_MODE", "TEMP", "TMP")}
        # These child-only overrides preserve the loopback/D boundary even if
        # config loading fails. Null-valued gRPC/metrics remain explicit in YAML.
        env.update({
            "QDRANT__SERVICE__API_KEY": key,
            "QDRANT__SERVICE__HOST": "127.0.0.1",
            "QDRANT__SERVICE__HTTP_PORT": "6333",
            "QDRANT__CLUSTER__ENABLED": "false",
            "QDRANT__TELEMETRY_DISABLED": "true",
            "QDRANT__STORAGE__STORAGE_PATH": str(dirs["storage"]),
            "QDRANT__STORAGE__SNAPSHOTS_PATH": str(dirs["snapshots"]),
            "QDRANT__STORAGE__TEMP_PATH": str(dirs["tmp"]),
            "QDRANT__STORAGE__SNAPSHOTS_CONFIG__SNAPSHOTS_STORAGE": "local",
            "RUN_MODE": "mrl_recovery",
            "TEMP": str(dirs["tmp"]), "TMP": str(dirs["tmp"]),
        })
        result["config_format"] = "yaml_json_subset"
        result["checks"]["child_environment_loopback_and_d_storage"] = True
        result["inherited_qdrant_environment_keys_removed"] = len(removed)
        result["api_key_material_exported"] = False
        job = win.job()
        for name in ("qdrant.stdout.log", "qdrant.stderr.log"):
            logs.append(open(run_dir / name, "xb", buffering=0))
        stage = "native_start"
        child = subprocess.Popen(
            [str(exe), "--config-path", str(config_path), "--disable-telemetry"],
            cwd=str(run_dir), env=env, stdin=subprocess.DEVNULL,
            stdout=logs[0], stderr=logs[1], close_fds=True,
            creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP)
        result["owned_child_pid"] = child.pid
        # No PID reopening/killing: assignment and stop use the retained Popen process HANDLE.
        require(win.k.AssignProcessToJobObject(job, int(child._handle)), "job_assignment_failed")
        result["checks"]["owned_job_assigned"] = True
        require(same_path(win.image(child), exe), "child_executable_identity_mismatch")
        result["checks"]["child_executable_identity"] = True
        opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), NoRedirect())
        http_deadline = time.monotonic() + 150

        result["owned_listener_observations"] = []
        result["http_observations"] = []

        def observe_owned(rows, phase):
            summary = owned_listener_metadata(rows, child.pid)
            previous = result["owned_listener_observations"]
            if not previous or previous[-1]["metadata"] != summary:
                item = {"phase": phase, "metadata": summary}
                if len(previous) < 8:
                    previous.append(item)
                else:
                    previous[-1] = item
            return summary

        def owned_listener():
            require(child.poll() is None, "owned_child_not_running")
            rows = win.listeners()
            observe_owned(rows, "request_preflight")
            require(listener_contract(rows, child.pid), "owned_loopback_listener_required")

        def do_request(method, path, body=None, authenticated=True):
            owned_listener()
            require(path.startswith("/") and not path.startswith("//"), "fixed_route_required")
            remaining = http_deadline - time.monotonic()
            require(remaining > 0, "native_probe_deadline_exceeded")
            headers = {"User-Agent": "MRL-Recovery-Validator/1.0", "Accept": "application/json"}
            if authenticated:
                headers["api-key"] = key
            data = None
            if body is not None:
                headers["Content-Type"] = "application/json"
                data = json.dumps(body, separators=(",", ":")).encode("utf-8")
            req = urllib.request.Request(BASE + path, data=data, headers=headers, method=method)
            try:
                response = opener.open(req, timeout=min(10.0, remaining))
            except urllib.error.HTTPError as e:
                response = e
            with response:
                status = response.code
                route_path = path.split("?", 1)[0]
                route = ("version" if route_path == "/" else
                         "collections" if route_path == "/collections" else
                         "collection_exists" if route_path.endswith("/exists") else
                         "points" if route_path.endswith("/points") else "collection")
                def record_http(raw=None, parsed=None):
                    item = http_metadata(method, route, stage, status, raw, parsed)
                    if len(result["http_observations"]) < 32:
                        result["http_observations"].append(item)
                    else:
                        result["http_observations"][-1] = item
                if not authenticated:
                    record_http()
                    return status, None
                raw = response.read(256 * 1024 + 1)
                require(len(raw) <= 256 * 1024, "http_response_size_limit")
                try:
                    parsed = strict_json(raw)
                except Exception:
                    record_http(raw)
                    raise
                record_http(raw, parsed)
                return status, parsed

        request = do_request
        stage = "native_ready"
        ready_deadline = time.monotonic() + 45
        ready = False
        while time.monotonic() < ready_deadline:
            require(child.poll() is None, "native_start_exited")
            rows = win.listeners()
            observe_owned(rows, "native_ready")
            own = [r for r in rows if r[2] == child.pid]
            if own:
                require(listener_contract(rows, child.pid), "unexpected_native_listener")
                try:
                    code, info = request("GET", "/")
                    ready = (code == 200 and isinstance(info, dict)
                             and info.get("version") == "1.19.2")
                    if ready:
                        break
                except (urllib.error.URLError, TimeoutError, OSError):
                    pass
            time.sleep(0.25)
        require(ready, "native_version_ready_timeout")
        result["qdrant_version"] = "1.19.2"
        result["checks"]["owned_loopback_http_6333_only"] = True
        stage = "authentication"
        code, listing = request("GET", "/collections")
        require(code == 200 and isinstance(listing, dict) and listing.get("status") == "ok" and
                isinstance(listing.get("result"), dict) and
                isinstance(listing["result"].get("collections"), list), "authenticated_list_failed")
        require(len(listing["result"]["collections"]) == 0, "isolated_storage_not_empty")
        result["initial_collection_count"] = 0
        code, _ = request("GET", "/collections", authenticated=False)
        require(code in (401, 403), "missing_key_not_rejected")
        result["missing_key_http_status"] = code
        result["checks"]["api_key_positive_and_negative"] = True
        collection = "mrl_recovery_" + uuid.uuid4().hex
        point_id = str(uuid.uuid4())
        nonce = uuid.uuid4().hex
        path = "/collections/" + collection
        stage = "fresh_collection_precheck"
        code, exists = request("GET", path + "/exists")
        require(code == 200 and exists.get("status") == "ok" and
                exists.get("result", {}).get("exists") is False, "collection_not_new")
        stage = "create_collection"
        creation_outcome_uncertain = True
        code, created = request("PUT", path + "?timeout=10",
                                {"vectors": {"size": 4, "distance": "Dot"}})
        require(code == 200 and created.get("status") == "ok" and created.get("result") is True,
                "collection_create_failed")
        created_here = True
        creation_outcome_uncertain = False
        result["checks"]["new_collection_created"] = True
        stage = "upsert_point"
        code, write = request("PUT", path + "/points?wait=true&timeout=10", {
            "points": [{"id": point_id, "vector": VECTOR,
                        "payload": {"origin_signature": ORIGIN, "probe_nonce": nonce}}]})
        require(code == 200 and write.get("status") == "ok" and
                write.get("result", {}).get("status") == "completed", "point_write_not_completed")
        result["checks"]["uuid_vector4_write_completed"] = True
        stage = "retrieve_point"
        code, read = request("POST", path + "/points?timeout=10",
                             {"ids": [point_id], "with_payload": True, "with_vector": True})
        require(code == 200 and point_contract(read, point_id, nonce), "point_roundtrip_mismatch")
        result["checks"]["uuid_vector4_exact_readback"] = True
        result["storage_after_readback"] = storage_metadata(win, storage_root)
        stage = "delete_own_collection"
        code, deletion = request("DELETE", path + "?timeout=10")
        require(code == 200 and deletion.get("status") == "ok" and deletion.get("result") is True,
                "collection_delete_failed")
        code, exists = request("GET", path + "/exists")
        require(code == 200 and exists.get("status") == "ok" and
                exists.get("result", {}).get("exists") is False, "collection_cleanup_unconfirmed")
        created_here = False
        result["checks"]["own_collection_deleted_and_absent"] = True
        result["status"] = "NATIVE_CRUD_PASS"
    except Exception as e:
        result["status"] = "FAILED"
        result["failed_stage"] = stage
        result["failure_code"] = str(e) if isinstance(e, ProbeFailure) else "unexpected_exception"
        result["error_type"] = type(e).__name__
    finally:
        if created_here and request is not None and child is not None and child.poll() is None:
            try:
                # Cleanup has a separate bounded budget after the main probe deadline.
                http_deadline = time.monotonic() + 25
                own_path = "/collections/" + collection
                code, existence = request("GET", own_path + "/exists")
                require(code == 200 and existence.get("status") == "ok",
                        "finally_collection_existence_failed")
                if existence.get("result", {}).get("exists") is True:
                    code, deletion = request("DELETE", own_path + "?timeout=10")
                    require(code == 200 and deletion.get("result") is True and
                            deletion.get("status") == "ok", "finally_collection_delete_failed")
                    code, existence = request("GET", own_path + "/exists")
                require(code == 200 and existence.get("status") == "ok" and
                        existence.get("result", {}).get("exists") is False,
                        "finally_collection_cleanup_unconfirmed")
                created_here = False
                result["cleanup_after_failure"] = "OWN_COLLECTION_CONFIRMED_ABSENT"
            except Exception as e:
                result["cleanup_after_failure"] = "UNCONFIRMED"
                result["cleanup_error_type"] = type(e).__name__
        result["own_collection_may_remain_in_probe_storage"] = bool(created_here or creation_outcome_uncertain)
        if child is not None:
            try:
                if child.poll() is None:
                    child.terminate()  # retained HANDLE; never taskkill/PID termination
                child.wait(timeout=10)
            except Exception as e:
                result["stop_error_type"] = type(e).__name__
            finally:
                if job and win:
                    win.k.CloseHandle(job)  # kills only members of this private job
                    job = None
                try:
                    child.wait(timeout=5)
                except Exception:
                    pass
            stopped = child.poll() is not None
            result["owned_child_stopped"] = stopped
            if not stopped:
                result["status"] = "FAILED"
                result["failed_stage"] = "owned_child_stop"
        elif job and win:
            win.k.CloseHandle(job)
            job = None
        for f in logs:
            f.close()
        key = None
        if child is not None and win is not None:
            try:
                clear = not any(r[1] == 6333 for r in win.listeners())
                result["checks"]["http_6333_clear_after_owned_stop"] = clear
                if not clear:
                    result["status"] = "FAILED"
                    result["failed_stage"] = "post_stop_listener"
            except Exception as e:
                result["status"] = "FAILED"
                result["failed_stage"] = "post_stop_listener_verification"
                result["post_stop_error_type"] = type(e).__name__
        if storage_root is not None and win is not None:
            try:
                result["storage_after_owned_stop"] = storage_metadata(win, storage_root)
            except Exception as e:
                result["storage_metadata_status"] = "UNAVAILABLE"
                result["storage_metadata_error_type"] = type(e).__name__
        result["finished_at_utc"] = utc()
        result["service_left_running"] = False if child is None or child.poll() is not None else "UNCONFIRMED"
    if run_dir is not None:
        receipt = run_dir / "native-qdrant-receipt.json"
        try:
            sha, size = write_exclusive(receipt, result)
            return {"schema": result["schema"], "origin_signature": ORIGIN,
                    "status": result["status"], "receipt_path": str(receipt),
                    "receipt_sha256": sha, "receipt_bytes": size,
                    "failed_stage": result.get("failed_stage"),
                    "failure_code": result.get("failure_code"),
                    "owned_child_stopped": result.get("owned_child_stopped"),
                    "operational_service": "NOT_ASSERTED"}
        except Exception as e:
            return {"schema": result["schema"], "origin_signature": ORIGIN,
                    "status": "FAILED", "failed_stage": "receipt_write",
                    "error_type": type(e).__name__, "operational_service": "NOT_ASSERTED"}
    return {"schema": result["schema"], "origin_signature": ORIGIN,
            "status": "FAILED", "failed_stage": result.get("failed_stage"),
            "failure_code": result.get("failure_code"), "error_type": result.get("error_type"),
            "operational_service": "NOT_ASSERTED"}

def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--stage-receipt", required=True)
    args = ap.parse_args()
    summary = run(args.stage_receipt)
    print(json.dumps(summary, sort_keys=True, separators=(",", ":")), flush=True)
    return 0 if summary["status"] == "NATIVE_CRUD_PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
