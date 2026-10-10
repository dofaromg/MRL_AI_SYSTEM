#!/usr/bin/env python3
"""D-only durable loopback Qdrant recovery service. origin_signature: MrLiouWord.
Cloud-authored source; runtime reads and secrets remain on WIN-PBVUI7VK2A6.
Commands are separate: stage -> install (disabled) -> start -> verify.
Stop disables only the verified own task; remove preserves every instance file.
"""
import argparse
import ctypes as C
import hashlib
import json
import ntpath
import os
from pathlib import Path, PurePosixPath
import platform
import re
import secrets
import subprocess
import sys
import threading
import types
import time
import urllib.error
import urllib.request
import uuid
from datetime import datetime, timezone
from xml.sax.saxutils import escape

ORIGIN = "MrLiouWord"
HOST = "WIN-PBVUI7VK2A6"
VERSION = "1.19.2"
PYTHON = r"D:\MrlToolchain\python\python.exe"
PYTHON_SHA256 = "624bbc0586d8855633b875e911883bbef8a0e8b8711e11126df480dd86f54181"
PYTHON_BYTES = 103192
PARENT = r"D:\MRL_Mother\QdrantLocal"
SELF_NAME = "MRL_qdrant_local_service_v1.py"
SUPPORT_NAME = "MRL_qdrant_native_probe_R02_v3.py"
SUPPORT_SHA256 = "e037408dab9ad3906c45feb86cd5a27dd4715841efb654b90a8208966cc74f2a"
SUPPORT_BYTES = 36514
TASK_NAME = "MRL_qdrant_local_service_task_v1.ps1"
TASK_SHA256 = "403cfac505a8ce59e39ee016901a23adbbb7e086f858b41034ef08067d0c3297"
TASK_BYTES = 8270
BASE = "http://127.0.0.1:6333"
HEX64 = re.compile(r"[0-9a-f]{64}\Z")
INSTANCE_RE = re.compile(r"D:\\MRL_Mother\\QdrantLocal\\[0-9a-f]{32}\Z", re.I)
MAX_RUNS = 512
MAX_LOG_BYTES = 1024 * 1024

class Hold(Exception):
    pass

def require(condition, code):
    if not condition:
        raise Hold(code)

def utc():
    return datetime.now(timezone.utc).isoformat()

def sha(data):
    return hashlib.sha256(data).hexdigest()

def digest(path):
    h, n = hashlib.sha256(), 0
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1024 * 1024), b""):
            h.update(b)
            n += len(b)
    return h.hexdigest(), n

def strict_json(raw):
    def pairs(items):
        out = {}
        for k, v in items:
            require(k not in out, "duplicate_json_key")
            out[k] = v
        return out
    return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=pairs)

def encode(obj):
    return (json.dumps(obj, ensure_ascii=True, sort_keys=True, indent=2) + "\n").encode("utf-8")

def path_equal(a, b):
    return ntpath.normcase(ntpath.abspath(str(a))) == ntpath.normcase(ntpath.abspath(str(b)))

def valid_instance(value):
    return bool(INSTANCE_RE.fullmatch(str(value))) and ntpath.basename(str(value)) == ntpath.basename(str(value)).lower()

def file_record(relative, data):
    return {"path": relative, "bytes": len(data), "sha256": sha(data)}

def source_record_valid(value):
    return (isinstance(value, dict) and set(value) == {"path", "bytes", "sha256"}
            and isinstance(value["path"], str) and value["path"] != ""
            and type(value["bytes"]) is int and value["bytes"] > 0
            and isinstance(value["sha256"], str) and bool(HEX64.fullmatch(value["sha256"]))
            and not PurePosixPath(value["path"]).is_absolute()
            and ".." not in PurePosixPath(value["path"]).parts
            and "\\" not in value["path"] and ":" not in value["path"])

def write_new(win, path, data):
    path = win.path(path, exists=False)
    require(not path.exists(), "exclusive_file_conflict")
    with open(path, "xb") as f:
        f.write(data)
        f.flush()
        os.fsync(f.fileno())
    require(digest(win.path(path)) == (sha(data), len(data)), "exclusive_write_hash_mismatch")
    return path

def read_small(win, path, limit):
    p = win.path(path)
    require(p.is_file() and p.stat().st_size <= limit, "bounded_file_required")
    return p.read_bytes()

def load_support(path):
    p = Path(path)
    # Verify and execute one bounded buffer. -B alone does not prohibit .pyc reads.
    with open(p, "rb") as f:
        raw = f.read(SUPPORT_BYTES + 1)
    require(len(raw) == SUPPORT_BYTES and sha(raw) == SUPPORT_SHA256,
            "support_source_hash_mismatch")
    module = types.ModuleType("mrl_qdrant_pinned_support")
    module.__file__ = str(p)
    module.__package__ = ""
    exec(compile(raw, str(p), "exec"), module.__dict__)
    return module

def require_host():
    require(os.name == "nt" and platform.node().upper() == HOST, "expected_windows_host_required")
    require(path_equal(sys.executable, PYTHON), "fixed_d_python_required")
    require(platform.python_version() == "3.12.2", "python_version_mismatch")
    require(digest(PYTHON) == (PYTHON_SHA256, PYTHON_BYTES), "python_image_mismatch")
    require(bool(C.windll.shell32.IsUserAnAdmin()), "elevated_admin_required")

def bootstrap(args):
    require_host()
    if args.command == "stage":
        support_path = args.probe_helper
    else:
        require(valid_instance(args.instance), "instance_boundary_invalid")
        support_path = str(Path(args.instance) / "runtime" / SUPPORT_NAME)
    support = load_support(support_path)
    win = support.WinAPI()
    win.path(PYTHON)
    win.path(Path(__file__).resolve())
    win.path(support_path)
    return support, win

def powershell_engine(win):
    # Resolve the OS engine through kernel32, never the current directory or PATH.
    get_system = win.k.GetSystemDirectoryW
    get_system.argtypes = [C.c_wchar_p, C.c_uint32]
    get_system.restype = C.c_uint32
    size = 32768
    buffer = C.create_unicode_buffer(size)
    used = int(get_system(buffer, size))
    require(0 < used < size and ntpath.isabs(buffer.value), "system_directory_query_failed")
    return ntpath.join(buffer.value, "WindowsPowerShell", "v1.0", "powershell.exe")

def ps_call(win, wrapper, operation, instance, target=None):
    wrapper = win.path(wrapper)
    require(digest(wrapper) == (TASK_SHA256, TASK_BYTES), "task_wrapper_hash_mismatch")
    cmd = [powershell_engine(win), "-NonInteractive", "-File", str(wrapper),
           "-Operation", operation, "-Instance", str(instance)]
    if target is not None:
        cmd.extend(["-Target", str(target)])
    p = subprocess.run(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                       stderr=subprocess.PIPE, timeout=35, check=False)
    require(len(p.stdout) <= 128 * 1024 and len(p.stderr) <= 128 * 1024, "task_output_limit")
    try:
        d = strict_json(p.stdout)
    except Exception:
        raise Hold("task_metadata_parse_failed") from None
    require(p.returncode == 0 and isinstance(d, dict) and
            d.get("origin_signature") == ORIGIN and d.get("status") != "FAILED",
            "task_or_acl_operation_failed")
    return d

def acl_check(win, wrapper, instance, target, protected=False):
    d = ps_call(win, wrapper, "AclCheck", instance, target)
    acl = d.get("acl", {})
    require(d.get("status") == "ACL_PRIVATE" and
            acl.get("private_system_admin_only") is True and acl.get("ace_count") == 2,
            "private_acl_required")
    require(not protected or acl.get("inheritance_protected") is True,
            "protected_root_acl_required")

def task_xml(instance):
    ident = ntpath.basename(str(instance))
    args = '-B "' + str(instance) + '\\runtime\\' + SELF_NAME + '" supervise --instance "' + str(instance) + '"'
    # COM RegisterTask uses logonType=5. XML deliberately omits invalid "ServiceAccount" enum.
    return ('<?xml version="1.0"?>\n'
        '<Task version="1.3" xmlns="http://schemas.microsoft.com/windows/2004/02/mit/task">'
        '<RegistrationInfo><Description>MrLiouWord isolated local Qdrant 1.19.2 recovery service '
        + ident + '</Description></RegistrationInfo>'
        '<Triggers><BootTrigger><Enabled>true</Enabled><ExecutionTimeLimit>PT0S</ExecutionTimeLimit>'
        '<Delay>PT30S</Delay></BootTrigger></Triggers>'
        '<Principals><Principal id="QdrantSystem"><UserId>S-1-5-18</UserId>'
        '<RunLevel>HighestAvailable</RunLevel></Principal></Principals>'
        '<Settings><MultipleInstancesPolicy>IgnoreNew</MultipleInstancesPolicy>'
        '<DisallowStartIfOnBatteries>false</DisallowStartIfOnBatteries>'
        '<StopIfGoingOnBatteries>false</StopIfGoingOnBatteries>'
        '<AllowHardTerminate>true</AllowHardTerminate><StartWhenAvailable>true</StartWhenAvailable>'
        '<RunOnlyIfNetworkAvailable>false</RunOnlyIfNetworkAvailable>'
        '<AllowStartOnDemand>true</AllowStartOnDemand><Enabled>false</Enabled>'
        '<Hidden>false</Hidden><RunOnlyIfIdle>false</RunOnlyIfIdle><WakeToRun>false</WakeToRun>'
        '<ExecutionTimeLimit>PT0S</ExecutionTimeLimit><Priority>7</Priority>'
        '<RestartOnFailure><Interval>PT1M</Interval><Count>3</Count></RestartOnFailure></Settings>'
        '<Actions Context="QdrantSystem"><Exec><Command>' + escape(PYTHON) + '</Command>'
        '<Arguments>' + escape(args) + '</Arguments><WorkingDirectory>' + escape(str(instance)) +
        '</WorkingDirectory></Exec></Actions></Task>\n').encode("utf-8")

def service_config(instance):
    return {"log_level": "WARN", "telemetry_disabled": True,
            "service": {"host": "127.0.0.1", "http_port": 6333,
                        "grpc_port": None, "metrics_port": None, "enable_tls": False},
            "cluster": {"enabled": False},
            "storage": {"storage_path": str(Path(instance) / "storage"),
                        "snapshots_path": str(Path(instance) / "snapshots"),
                        "temp_path": str(Path(instance) / "tmp"),
                        "snapshots_config": {"snapshots_storage": "local"}}}

def child_environment(environ, instance, key):
    """Preserve inherited guards. Any unapproved/conflicting QDRANT__ override is a HOLD."""
    expected = {
        "QDRANT__SERVICE__HOST": "127.0.0.1", "QDRANT__SERVICE__HTTP_PORT": "6333",
        "QDRANT__SERVICE__API_KEY": key, "QDRANT__SERVICE__ENABLE_TLS": "false",
        "QDRANT__CLUSTER__ENABLED": "false", "QDRANT__TELEMETRY_DISABLED": "true",
        "QDRANT__STORAGE__STORAGE_PATH": str(Path(instance) / "storage"),
        "QDRANT__STORAGE__SNAPSHOTS_PATH": str(Path(instance) / "snapshots"),
        "QDRANT__STORAGE__TEMP_PATH": str(Path(instance) / "tmp"),
    }
    for k, v in environ.items():
        if k.upper().startswith("QDRANT__"):
            require(k.upper() in expected and v == expected[k.upper()], "conflicting_qdrant_environment")
    out = dict(environ)
    # Retain spelling of preexisting Windows case-insensitive variables.
    for k, v in expected.items():
        matches = [old for old in out if old.upper() == k]
        if not matches:
            out[k] = v
    out["TEMP"] = str(Path(instance) / "tmp")
    out["TMP"] = str(Path(instance) / "tmp")
    return out

def receipt_base(operation, instance):
    return {"schema": "MRL_Qdrant_Local_Service_Receipt_v1", "origin_signature": ORIGIN,
            "operation": operation, "observed_host": HOST, "timestamp_utc": utc(),
            "instance_directory": str(instance), "endpoint": BASE,
            "public_endpoint_configured": False, "production_sla_asserted": False,
            "existing_services_modified": False, "secret_exported": False}

def persist_receipt(win, instance, receipt):
    name = "operation_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex + ".json"
    path = write_new(win, Path(instance) / "state" / name, encode(receipt))
    return {"status": receipt["status"], "origin_signature": ORIGIN,
            "operation": receipt["operation"], "instance_directory": str(instance),
            "receipt_path": str(path), "receipt_sha256": digest(path)[0],
            "receipt_bytes": path.stat().st_size, "secret_exported": False,
            "checks": receipt.get("checks", {}), "task": receipt.get("task"),
            "runtime": receipt.get("runtime"), "error_code": receipt.get("error_code")}

def stage(support, win, args):
    wrapper = win.path(args.task_helper)
    require(digest(wrapper) == (TASK_SHA256, TASK_BYTES), "task_wrapper_hash_mismatch")
    source = win.path(Path(__file__).resolve())
    exe, provenance = support.verify_stage(win, args.stage_receipt)
    stage_receipt = support.strict_json(win.path(args.stage_receipt).read_bytes())
    parent = win.path(PARENT, exists=Path(PARENT).exists())
    if not parent.exists():
        parent.mkdir()
    require(parent.is_dir(), "instance_parent_not_directory")
    instance = win.path(parent / uuid.uuid4().hex, exists=False)
    instance.mkdir(exist_ok=False)
    ps_call(win, wrapper, "AclNew", instance)
    acl_check(win, wrapper, instance, instance, protected=True)
    for name in ("runtime", "bin", "private", "storage", "snapshots", "tmp", "state", "logs"):
        win.path(instance / name, exists=False).mkdir(exist_ok=False)
    files = []
    for original, name in ((source, SELF_NAME), (win.path(args.probe_helper), SUPPORT_NAME), (wrapper, TASK_NAME)):
        raw = original.read_bytes()
        rel = "runtime/" + name
        write_new(win, instance / "runtime" / name, raw)
        files.append(file_record(rel, raw))
    private_wrapper = instance / "runtime" / TASK_NAME
    expanded = win.path(Path(args.stage_receipt).parent / "expanded")
    executable_relative = None
    for f in stage_receipt["extracted_files"]:
        rel = f["relative_path"].replace("\\", "/")
        pp = PurePosixPath(rel)
        require(not pp.is_absolute() and ".." not in pp.parts and ":" not in rel, "package_relative_path_invalid")
        original = win.path(expanded.joinpath(*pp.parts))
        require(digest(original) == (f["sha256"], f["bytes"]), "stage_changed_before_copy")
        dest = instance / "bin"
        for part in pp.parts[:-1]:
            dest = win.path(dest / part, exists=(dest / part).exists())
            if not dest.exists():
                dest.mkdir(exist_ok=False)
        target = win.path(dest / pp.name, exists=False)
        with open(original, "rb") as src, open(target, "xb") as dst:
            for chunk in iter(lambda: src.read(1024 * 1024), b""):
                dst.write(chunk)
            dst.flush()
            os.fsync(dst.fileno())
        require(digest(target) == (f["sha256"], f["bytes"]), "package_copy_hash_mismatch")
        files.append({"path": "bin/" + rel, "bytes": f["bytes"], "sha256": f["sha256"]})
        if path_equal(original, exe):
            executable_relative = "bin/" + rel
    require(executable_relative is not None, "copied_executable_missing")
    config = encode(service_config(instance))
    require(len(str(instance / "storage")) < 100, "short_storage_path_required")
    write_new(win, instance / "config.yaml", config)
    files.append(file_record("config.yaml", config))
    xml = task_xml(instance)
    write_new(win, instance / "task.xml", xml)
    files.append(file_record("task.xml", xml))
    # This key is never included in source, manifest, receipts, stdout, or command arguments.
    key = secrets.token_hex(32)
    write_new(win, instance / "private" / "api-key.txt", (key + "\n").encode("ascii"))
    acl_check(win, private_wrapper, instance, instance / "private" / "api-key.txt")
    manifest = {
        "schema": "MRL_Qdrant_Local_Instance_v1", "origin_signature": ORIGIN,
        "instance_id": instance.name, "instance_directory": str(instance),
        "expected_host": HOST, "task_name": "MRL_Qdrant_Local_" + instance.name,
        "version": VERSION, "endpoint": BASE, "executable_relative_path": executable_relative,
        "task_xml_sha256": sha(xml), "source_provenance": provenance,
        "python_path": PYTHON, "python_sha256": PYTHON_SHA256, "python_bytes": PYTHON_BYTES,
        "api_key_relative_path": "private/api-key.txt", "files": files,
        "restart_count": 3, "restart_interval_seconds": 60, "created_at_utc": utc(),
    }
    write_new(win, instance / "instance.json", encode(manifest))
    connection = {"origin_signature": ORIGIN, "endpoint": BASE, "api_key_header": "api-key",
                  "api_key_file": str(instance / "private" / "api-key.txt"),
                  "credential_contents_included": False, "version": VERSION,
                  "usage": "Read the key locally under the authorized SYSTEM/Admin identity."}
    write_new(win, instance / "connection.json", encode(connection))
    receipt = receipt_base("stage", instance)
    receipt.update(status="STAGED_PRIVATE_DISABLED", task_registered=False, server_started=False,
                   checks={"official_package_reverified": True, "copied_package_hashes_match": True,
                           "private_root_acl": True, "private_key_acl": True,
                           "short_storage_path": True, "source_copied_into_private_instance": True},
                   provenance=provenance, task_name=manifest["task_name"])
    return persist_receipt(win, instance, receipt)

def manifest_contract(m, instance):
    return (isinstance(m, dict) and m.get("schema") == "MRL_Qdrant_Local_Instance_v1"
            and m.get("origin_signature") == ORIGIN and m.get("expected_host") == HOST
            and m.get("instance_id") == ntpath.basename(str(instance))
            and path_equal(m.get("instance_directory", ""), instance)
            and m.get("task_name") == "MRL_Qdrant_Local_" + ntpath.basename(str(instance))
            and m.get("version") == VERSION and m.get("endpoint") == BASE
            and m.get("python_path") == PYTHON and m.get("python_sha256") == PYTHON_SHA256
            and m.get("python_bytes") == PYTHON_BYTES and m.get("api_key_relative_path") == "private/api-key.txt"
            and m.get("restart_count") == 3 and m.get("restart_interval_seconds") == 60
            and isinstance(m.get("files"), list) and 5 <= len(m["files"]) <= 1024
            and all(source_record_valid(f) for f in m["files"])
            and len({f["path"].casefold() for f in m["files"]}) == len(m["files"]))

def validate_instance(support, win, instance):
    require(valid_instance(instance), "instance_boundary_invalid")
    instance = win.path(instance)
    wrapper = instance / "runtime" / TASK_NAME
    acl_check(win, wrapper, instance, instance, protected=True)
    m = strict_json(read_small(win, instance / "instance.json", 512 * 1024))
    require(manifest_contract(m, instance), "instance_manifest_contract_mismatch")
    expected_required = {"runtime/" + SELF_NAME, "runtime/" + SUPPORT_NAME,
                         "runtime/" + TASK_NAME, "task.xml", "config.yaml"}
    observed = {f["path"] for f in m["files"]}
    require(expected_required <= observed, "immutable_source_records_missing")
    require(m["executable_relative_path"] in observed and
            m["executable_relative_path"].startswith("bin/") and
            PurePosixPath(m["executable_relative_path"]).name.lower() == "qdrant.exe",
            "immutable_executable_record_missing")
    for f in m["files"]:
        p = win.path(instance.joinpath(*PurePosixPath(f["path"]).parts))
        require(digest(p) == (f["sha256"], f["bytes"]), "instance_immutable_file_hash_mismatch")
    support_record = next(f for f in m["files"] if f["path"] == "runtime/" + SUPPORT_NAME)
    wrapper_record = next(f for f in m["files"] if f["path"] == "runtime/" + TASK_NAME)
    require((support_record["sha256"], support_record["bytes"]) == (SUPPORT_SHA256, SUPPORT_BYTES)
            and (wrapper_record["sha256"], wrapper_record["bytes"]) == (TASK_SHA256, TASK_BYTES),
            "pinned_runtime_source_mismatch")
    require(sha(read_small(win, instance / "task.xml", 128 * 1024)) == m["task_xml_sha256"],
            "task_xml_hash_mismatch")
    require(strict_json(read_small(win, instance / "config.yaml", 64 * 1024)) == service_config(instance),
            "fixed_config_contract_mismatch")
    provenance = m.get("source_provenance", {})
    require(provenance.get("official_package_reverified") is True and
            provenance.get("archive_sha256") == support.ARCHIVE_HASH and
            provenance.get("archive_bytes") == support.ARCHIVE_BYTES and
            provenance.get("source_commit") == support.COMMIT, "official_provenance_mismatch")
    exe_record = next(f for f in m["files"] if f["path"] == m["executable_relative_path"])
    require(exe_record["sha256"] == provenance.get("executable_sha256"), "official_image_hash_mismatch")
    for name in ("private", "storage", "snapshots", "tmp", "state", "logs", "runtime", "bin"):
        require(win.path(instance / name).is_dir(), "instance_directory_missing")
    acl_check(win, wrapper, instance, instance / "runtime" / SELF_NAME)
    acl_check(win, wrapper, instance, instance / "private" / "api-key.txt")
    key = read_small(win, instance / "private" / "api-key.txt", 128).decode("ascii").strip()
    require(bool(HEX64.fullmatch(key)), "private_key_format_invalid")
    return instance, m, key

class ProcessIdentity:
    def __init__(self, win):
        self.win = win
        self.k = win.k
        self.k.OpenProcess.argtypes = [C.c_uint32, C.c_int, C.c_uint32]
        self.k.OpenProcess.restype = C.c_void_p
        self.k.GetProcessTimes.argtypes = [C.c_void_p] + [C.POINTER(C.c_uint64)] * 4
        self.k.GetProcessTimes.restype = C.c_int
        self.k.GetCurrentProcess.argtypes = []
        self.k.GetCurrentProcess.restype = C.c_void_p
        self.k.CreateMutexW.argtypes = [C.c_void_p, C.c_int, C.c_wchar_p]
        self.k.CreateMutexW.restype = C.c_void_p
        self.k.ReleaseMutex.argtypes = [C.c_void_p]
        self.k.ReleaseMutex.restype = C.c_int
    def created(self, handle):
        times = [C.c_uint64() for _ in range(4)]
        require(self.k.GetProcessTimes(handle, *[C.byref(t) for t in times]), "process_creation_query_failed")
        return int(times[0].value)
    def opened(self, pid, expected_image, expected_created):
        require(type(pid) is int and pid > 0 and type(expected_created) is int and expected_created > 0,
                "process_record_invalid")
        h = self.k.OpenProcess(0x1000, False, pid)
        require(bool(h), "recorded_process_not_running")
        try:
            proxy = type("ReadOnlyProcess", (), {"_handle": h})()
            actual = {"pid": pid, "created_filetime": self.created(h), "image": str(self.win.image(proxy))}
            expected = {"pid": pid, "created_filetime": expected_created, "image": str(expected_image)}
            require(same_process_record(actual, expected), "recorded_process_identity_mismatch")
        except BaseException:
            self.k.CloseHandle(h)
            raise
        return h
    def mutex(self):
        h = self.k.CreateMutexW(None, True, "Global\\MRL_Qdrant_Local_6333")
        require(bool(h), "instance_mutex_failed")
        if C.get_last_error() == 183:
            self.k.CloseHandle(h)
            raise Hold("qdrant_supervisor_already_owns_mutex")
        return h

def same_process_record(actual, expected):
    return (type(actual.get("pid")) is int and actual.get("pid") == expected.get("pid")
            and type(actual.get("created_filetime")) is int
            and actual.get("created_filetime") == expected.get("created_filetime")
            and path_equal(actual.get("image", ""), expected.get("image", "")))

def request_json(support, path, key=None):
    require(path in ("/", "/collections"), "fixed_readonly_route_required")
    headers = {"User-Agent": "MRL-Qdrant-Local-Recovery/1.0"}
    if key is not None:
        headers["api-key"] = key
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), support.NoRedirect())
    req = urllib.request.Request(BASE + path, headers=headers, method="GET")
    try:
        response = opener.open(req, timeout=4)
    except urllib.error.HTTPError as e:
        response = e
    with response:
        raw = response.read(256 * 1024 + 1)
        require(len(raw) <= 256 * 1024, "http_response_limit")
        status = response.code
    if status >= 400:
        return status, None
    try:
        return status, strict_json(raw)
    except Exception:
        raise Hold("http_json_invalid") from None

def probe(support, win, child_pid, key):
    require(support.listener_contract(win.listeners(), child_pid), "listener_ownership_or_boundary_mismatch")
    status, body = request_json(support, "/")
    require(status == 200 and isinstance(body, dict) and body.get("version") == VERSION,
            "qdrant_version_mismatch")
    status, body = request_json(support, "/collections", key)
    require(status == 200 and isinstance(body, dict) and body.get("status") == "ok"
            and isinstance(body.get("result"), dict)
            and isinstance(body["result"].get("collections"), list), "qdrant_auth_read_failed")
    count = len(body["result"]["collections"])
    denied, ignored = request_json(support, "/collections")
    require(denied in (401, 403), "qdrant_missing_key_not_denied")
    require(support.listener_contract(win.listeners(), child_pid), "listener_changed_during_probe")
    return {"ready": True, "version": VERSION, "listener_loopback_only": True,
            "protected_api_status": status, "missing_key_status": denied,
            "collection_count": count, "collection_names_exported": False}

class BoundedLog:
    def __init__(self, stream, path):
        self.stream = stream
        self.file = open(path, "xb")
        self.written = 0
        self.discarded = 0
        self.thread = threading.Thread(target=self.drain, daemon=True)
    def drain(self):
        try:
            while True:
                chunk = self.stream.read(8192)
                if not chunk:
                    break
                keep = chunk[:max(0, MAX_LOG_BYTES - self.written)]
                self.file.write(keep)
                self.written += len(keep)
                self.discarded += len(chunk) - len(keep)
        finally:
            self.file.close()
    def start(self):
        self.thread.start()
    def finish(self):
        self.thread.join(timeout=5)

def run_id():
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid.uuid4().hex

def supervise(support, win, instance):
    instance, m, key = validate_instance(support, win, instance)
    require(path_equal(Path(__file__).resolve(), instance / "runtime" / SELF_NAME),
            "supervisor_must_run_private_copy")
    task = ps_call(win, instance / "runtime" / TASK_NAME, "Inspect", instance)["task"]
    require(task.get("enabled") is True and task.get("definition_verified") is True,
            "enabled_exact_task_required")
    identity = ProcessIdentity(win)
    own_mutex = identity.mutex()
    job, child, log = None, None, None
    ident = run_id()
    record = receipt_base("supervise", instance)
    record.update(run_id=ident, task=task, status="STARTING",
                  supervisor={"pid": os.getpid(), "created_filetime": identity.created(identity.k.GetCurrentProcess()),
                              "image": PYTHON})
    exit_code = 2
    try:
        require(len(list((instance / "state").glob("run_*_ready.json"))) < MAX_RUNS,
                "retained_run_record_capacity_reached")
        require(not any(port in (6333, 6334, 6335) for _, port, _ in win.listeners()),
                "qdrant_ports_already_in_use")
        env = child_environment(os.environ, instance, key)
        exe = win.path(instance.joinpath(*PurePosixPath(m["executable_relative_path"]).parts))
        config = win.path(instance / "config.yaml")
        job = win.job()
        child = subprocess.Popen([str(exe), "--config-path", str(config), "--disable-telemetry"],
            cwd=instance, env=env, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, creationflags=subprocess.CREATE_NO_WINDOW, close_fds=True)
        require(path_equal(win.image(child), exe), "owned_child_image_mismatch")
        require(win.k.AssignProcessToJobObject(job, int(child._handle)), "owned_child_job_assignment_failed")
        record["child"] = {"pid": child.pid, "created_filetime": identity.created(int(child._handle)),
                           "image": str(exe), "image_sha256": m["source_provenance"]["executable_sha256"],
                           "job_kill_on_close_assigned": True}
        log = BoundedLog(child.stdout, win.path(instance / "logs" / ("qdrant_" + ident + ".log"), exists=False))
        log.start()
        deadline, last_code = time.monotonic() + 45, "startup_timeout"
        while time.monotonic() < deadline:
            require(child.poll() is None, "owned_child_exited_during_startup")
            rows = win.listeners()
            owned = [r for r in rows if r[2] == child.pid]
            if owned:
                require(support.listener_contract(rows, child.pid), "unexpected_owned_startup_listener")
                try:
                    runtime = probe(support, win, child.pid, key)
                    break
                except (Hold, OSError, urllib.error.URLError) as e:
                    last_code = str(e) if isinstance(e, Hold) else "startup_network_not_ready"
            time.sleep(0.5)
        else:
            raise Hold(last_code)
        record.update(status="RUNNING_VERIFIED", runtime=runtime,
            checks={"private_source": True, "official_image": True, "owned_process": True,
                    "job_assigned": True, "loopback_only": True, "api_key_auth": True,
                    "missing_key_denied": True, "bounded_restart_policy": True})
        write_new(win, instance / "state" / ("run_" + ident + "_ready.json"), encode(record))
        consecutive = 0
        while True:
            time.sleep(15)
            require(child.poll() is None, "owned_child_exited")
            # A boundary/ownership violation is immediate; only read-health failures get 3 retries.
            require(support.listener_contract(win.listeners(), child.pid), "owned_listener_changed")
            try:
                probe(support, win, child.pid, key)
                consecutive = 0
            except (Hold, OSError, urllib.error.URLError):
                consecutive += 1
                require(consecutive < 3, "consecutive_health_failure")
    except BaseException as e:
        record.update(status="STOPPED_FAILURE", error_code=(str(e) if isinstance(e, Hold) else type(e).__name__))
    finally:
        if child is not None and child.poll() is None:
            if job:
                win.k.TerminateJobObject(job, 2)
            if child.poll() is None:
                child.terminate()
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # retained Popen handle only, never PID lookup/kill of another process.
                child.kill()
                child.wait(timeout=5)
        if job:
            win.k.CloseHandle(job)
        if log:
            log.finish()
            record["log"] = {"retained_bytes": log.written, "discarded_bytes": log.discarded,
                             "content_exported": False}
        record["owned_child_stopped"] = child is None or child.poll() is not None
        record["ended_at_utc"] = utc()
        try:
            write_new(win, instance / "state" / ("run_" + ident + "_end.json"), encode(record))
        finally:
            identity.k.ReleaseMutex(own_mutex)
            identity.k.CloseHandle(own_mutex)
    return exit_code

def latest_ready(win, instance):
    paths = sorted((instance / "state").glob("run_*_ready.json"), reverse=True)
    require(paths and len(paths) <= MAX_RUNS, "ready_record_missing_or_capacity")
    r = strict_json(read_small(win, paths[0], 128 * 1024))
    require(r.get("schema") == "MRL_Qdrant_Local_Service_Receipt_v1"
            and r.get("origin_signature") == ORIGIN and r.get("status") == "RUNNING_VERIFIED"
            and path_equal(r.get("instance_directory", ""), instance)
            and r.get("observed_host") == HOST, "ready_record_identity_mismatch")
    return r

def verify(support, win, instance):
    instance, m, key = validate_instance(support, win, instance)
    task = ps_call(win, instance / "runtime" / TASK_NAME, "Inspect", instance)["task"]
    require(task.get("enabled") is True and task.get("state") == 4
            and task.get("definition_verified") is True, "exact_task_not_running")
    ready = latest_ready(win, instance)
    child, supervisor = ready["child"], ready["supervisor"]
    exe = instance.joinpath(*PurePosixPath(m["executable_relative_path"]).parts)
    require(path_equal(child.get("image", ""), exe)
            and child.get("image_sha256") == m["source_provenance"]["executable_sha256"]
            and child.get("job_kill_on_close_assigned") is True,
            "ready_child_source_mismatch")
    identity = ProcessIdentity(win)
    h_supervisor = identity.opened(supervisor.get("pid"), PYTHON, supervisor.get("created_filetime"))
    h_child = None
    try:
        h_child = identity.opened(child.get("pid"), exe, child.get("created_filetime"))
        runtime = probe(support, win, child["pid"], key)
    finally:
        if h_child:
            win.k.CloseHandle(h_child)
        win.k.CloseHandle(h_supervisor)
    receipt = receipt_base("verify", instance)
    receipt.update(status="DURABLE_LOCAL_SERVICE_VERIFIED", task=task, runtime=runtime,
                   child=child, supervisor=supervisor,
                   checks={"private_instance_acl": True, "private_key_acl": True,
                           "source_hashes": True, "official_image": True,
                           "exact_task_running": True, "task_restart_policy": True,
                           "process_creation_identity": True, "loopback_only": True,
                           "api_key_auth": True, "missing_key_denied": True},
                   durability_scope="Boot-triggered SYSTEM task; actual reboot recovery not yet exercised.",
                   application_integration="NOT_ASSERTED", restart_execution_test="NOT_RUN")
    return persist_receipt(win, instance, receipt)

def control(support, win, args):
    instance, m, key = validate_instance(support, win, args.instance)
    if args.command == "verify":
        return verify(support, win, instance)
    operation = {"install": "Install", "start": "Start", "stop": "Stop", "remove": "Remove"}[args.command]
    metadata = ps_call(win, instance / "runtime" / TASK_NAME, operation, instance)
    if args.command == "start":
        deadline = time.monotonic() + 65
        while time.monotonic() < deadline:
            try:
                return verify(support, win, instance)
            except (Hold, OSError, urllib.error.URLError):
                time.sleep(1)
        raise Hold("scheduled_service_start_not_verified")
    receipt = receipt_base(args.command, instance)
    receipt.update(status=metadata["status"], task=metadata.get("task"),
                   data_removed=False, keys_removed=False, files_removed=False)
    if args.command == "stop":
        deadline = time.monotonic() + 15
        prior = None
        try:
            prior = latest_ready(win, instance)
        except Hold:
            pass
        while time.monotonic() < deadline:
            state = ps_call(win, instance / "runtime" / TASK_NAME, "Inspect", instance)["task"]
            own_listening = (prior is not None and any(pid == prior["child"]["pid"]
                             for _, _, pid in win.listeners()))
            if state.get("enabled") is False and state.get("state") not in (2, 4) and not own_listening:
                receipt["checks"] = {"own_task_disabled": True, "own_listener_stopped": True}
                break
            time.sleep(0.5)
        else:
            raise Hold("own_task_stop_not_verified")
    return persist_receipt(win, instance, receipt)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("stage")
    p.add_argument("--stage-receipt", required=True)
    p.add_argument("--probe-helper", required=True)
    p.add_argument("--task-helper", required=True)
    for name in ("install", "start", "verify", "supervise", "stop", "remove"):
        sub.add_parser(name).add_argument("--instance", required=True)
    args = parser.parse_args()
    try:
        support, win = bootstrap(args)
        if args.command == "supervise":
            return supervise(support, win, args.instance)
        result = stage(support, win, args) if args.command == "stage" else control(support, win, args)
        print(json.dumps(result, sort_keys=True))
        return 0
    except BaseException as e:
        # No traceback, raw HTTP/log text, env, key, or private file content is printed.
        print(json.dumps({"status": "HOLD", "origin_signature": ORIGIN, "operation": args.command,
                          "error_code": str(e) if isinstance(e, Hold) else type(e).__name__,
                          "secret_exported": False}, sort_keys=True))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
