#!/usr/bin/env python3
# origin_signature: MrLiouWord
"""Metadata-only activation evidence; never starts/stops services or changes tasks."""
import contextlib
import ctypes
import datetime as dt
import hashlib
import json
import ntpath
import os
from pathlib import Path
import runpy
import stat
import subprocess
import sys
import uuid

HOST = "WIN-PBVUI7VK2A6"
OPS = r"D:\MRL_Mother\Recovery\_operations\LocalAI_20261010_R02_be2f1d63"
RUNTIME = OPS + r"\active_watchdog_20261010_R01"
HELPER = RUNTIME + r"\MRL_active_runtime_watchdog_v3.py"
HELPER_SHA = "c9d671083bba6d0f8300a1b2e78d983a04e411971f274cf435088f555f1efb0a"
PYTHON = r"D:\MrlToolchain\python\python.exe"
PYTHON_SHA = "624bbc0586d8855633b875e911883bbef8a0e8b8711e11126df480dd86f54181"
ORIGINAL = r"D:\mrl\MRL_Watchdog.py"
ORIGINAL_SHA = "2c327ed594594425a7a58d2082abc624a22531f7011d446dd2bd999172eff846"
ASI = r"D:\mrl\asi-engine\server.js"
ASI_SHA = "4dfd3194b7519efb6eef7236024a3953d2dd8842c9dc38c52ec71c6c0c807f5e"
NODE = r"D:\MrlToolchain\node\node.exe"
NODE_SHA = "bc585910690318aaebe3c57669cb83ca9d1e5791efd63195e238f54686e6c2ec"
ARGS_SHA = "badf0d31001a293c0a3a06fdf563444d24b1d3864c03468e7e26d6bafd9d4f06"
WATCHDOG_PID, INFERENCE_PID, ASI_PID = 41972, 20580, 13968
DAY = "20261010"
ACTIVATION_UTC = "2026-10-10T18:50:53+00:00"
SCHEMA = "MRL_active_runtime_watchdog_v3"
STATE = "ASI_HEALTH_OBSERVED_RECOVERY_HELD"
ORIGIN = "MrLiouWord"
MAX_LOG_BYTES = 8 * 1024 * 1024

class Gate(Exception):
    pass

def need(condition, code):
    if not condition:
        raise Gate(code)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def norm(value):
    return ntpath.normcase(ntpath.normpath(value))

def utc_now():
    return dt.datetime.now(dt.timezone.utc)

def strict_json(data):
    def pairs(items):
        result = {}
        for key, value in items:
            need(key not in result, "JSON_DUPLICATE_KEY")
            result[key] = value
        return result
    def invalid_constant(unused):
        raise Gate("JSON_NONFINITE_NUMBER")
    try:
        if type(data) is bytes:
            data = data.decode("utf-8")
        return json.loads(data, object_pairs_hook=pairs, parse_constant=invalid_constant)
    except Gate:
        raise
    except Exception:
        raise Gate("JSON_INVALID") from None

def stamp(value):
    need(type(value) is str, "TIMESTAMP_TYPE")
    try:
        result = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        raise Gate("TIMESTAMP_INVALID") from None
    need(result.tzinfo is not None and result.utcoffset() == dt.timedelta(0),
         "TIMESTAMP_NOT_UTC")
    return result

def aggregate_prefix(data, created_at, now):
    need(type(data) is bytes and 0 < len(data) <= MAX_LOG_BYTES, "LOG_SIZE")
    need(data.endswith(b"\n"), "LOG_PARTIAL_TAIL")
    lines = data.split(b"\n")[:-1]
    need(len(lines) >= 2 and all(0 < len(line) <= 65536 for line in lines),
         "LOG_RECORD_COUNT_OR_SIZE")
    activation = stamp(ACTIVATION_UTC)
    times = []
    max_relatives = 0
    for raw in lines:
        row = strict_json(raw)
        need(type(row) is dict, "LOG_RECORD_TYPE")
        expected = {
            "schema": SCHEMA, "origin_signature": ORIGIN, "mode": "ACTIVE",
            "executed_where": "DL580_WINDOWS_D", "state": STATE,
            "restart_eligibility": "HELD_UNRESOLVED_RELATIVE_PROCESS",
            "runtime_recovery": "NOT_ASSERTED", "process_starts_scope": "ASI_7700",
        }
        need(all(type(row.get(key)) is str and row[key] == value
                 for key, value in expected.items()), "LOG_CONTRACT")
        for key in ("source_hashes_verified", "asi_process_identity_verified",
                    "asi_health_observed"):
            need(row.get(key) is True, "LOG_HEALTH_OR_HASH_GATE")
        for key in ("process_starts", "inference_7500_actions",
                    "bridge_7800_actions", "attempts_reserved"):
            need(type(row.get(key)) is int and row[key] == 0, "LOG_NONZERO_OR_UNTYPED_ACTION")
        need(type(row.get("asi_owner_pid")) is int and row["asi_owner_pid"] == ASI_PID,
             "LOG_ASI_OWNER")
        relatives = row.get("unresolved_relative_process_count")
        need(type(relatives) is int and relatives >= 1, "LOG_RELATIVE_PROCESS_GATE")
        max_relatives = max(max_relatives, relatives)
        need(row.get("report_only") == {"7500": "LISTENING", "7800": "LISTENING"},
             "LOG_REPORT_ONLY_PORTS")
        when = stamp(row.get("checked_at_utc"))
        need(when >= created_at and when >= activation, "LOG_PRE_ACTIVATION_RECORD")
        need(when <= now + dt.timedelta(seconds=5), "LOG_FUTURE_RECORD")
        need(not times or when > times[-1], "LOG_TIMESTAMP_ORDER")
        times.append(when)
    span = (times[-1] - times[0]).total_seconds()
    need(span >= 30, "LOG_OBSERVATION_SPAN")
    need((now - times[-1]).total_seconds() <= 90, "LOG_STALE")
    return {
        "complete_prefix_bytes": len(data), "complete_prefix_sha256": sha(data),
        "complete_record_count": len(lines), "all_records_qualified": True,
        "first_record_at_utc": times[0].isoformat(),
        "last_record_at_utc": times[-1].isoformat(), "span_seconds": span,
        "state": STATE, "mode": "ACTIVE", "all_health_and_hash_gates_true": True,
        "process_starts": 0, "inference_7500_actions": 0,
        "bridge_7800_actions": 0, "attempts_reserved": 0,
        "maximum_unresolved_relative_process_count": max_relatives,
        "writer_pid_embedded_in_records": False,
        "writer_binding": "CORRELATED_WITH_VERIFIED_SINGLE_TASK_PROCESS",
    }

class LocalFiles:
    def __init__(self):
        need(sys.platform == "win32", "WINDOWS_REQUIRED")
        need(norm(sys.executable) == norm(PYTHON), "FIXED_D_PYTHON_REQUIRED")
        from ctypes import wintypes as w
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        self.k.GetComputerNameW.argtypes = [w.LPWSTR, ctypes.POINTER(w.DWORD)]
        self.k.GetComputerNameW.restype = w.BOOL
        self.k.GetDriveTypeW.argtypes = [w.LPCWSTR]
        self.k.GetDriveTypeW.restype = w.UINT
        self.k.GetFileAttributesW.argtypes = [w.LPCWSTR]
        self.k.GetFileAttributesW.restype = w.DWORD
        self.k.CreateFileW.argtypes = [w.LPCWSTR, w.DWORD, w.DWORD, w.LPVOID,
                                      w.DWORD, w.DWORD, w.HANDLE]
        self.k.CreateFileW.restype = w.HANDLE
        self.k.GetFinalPathNameByHandleW.argtypes = [w.HANDLE, w.LPWSTR, w.DWORD, w.DWORD]
        self.k.GetFinalPathNameByHandleW.restype = w.DWORD
        self.k.CloseHandle.argtypes = [w.HANDLE]
        self.k.CloseHandle.restype = w.BOOL
        buf, length = ctypes.create_unicode_buffer(256), w.DWORD(256)
        need(self.k.GetComputerNameW(buf, ctypes.byref(length))
             and buf.value.upper() == HOST, "EXPECTED_HOST_REQUIRED")
        need(self.k.GetDriveTypeW("D:\\") == 3, "D_FIXED_VOLUME_REQUIRED")
        self.check(OPS, directory=True)
        self.check(RUNTIME, directory=True)

    def check(self, path, directory=False):
        need(type(path) is str and path[:3].upper() == "D:\\"
             and ntpath.isabs(path) and ntpath.splitdrive(path)[0].upper() == "D:",
             "FIXED_D_PATH_REQUIRED")
        tail = path[3:]
        need(":" not in tail and "/" not in tail
             and all(part not in ("", ".", "..") for part in tail.split("\\")),
             "UNSAFE_PATH_COMPONENT")
        parts = tail.split("\\")
        for index in range(len(parts) + 1):
            current = "D:\\" + "\\".join(parts[:index])
            attrs = self.k.GetFileAttributesW(current)
            need(attrs != 0xffffffff and not attrs & 0x400, "MISSING_OR_REPARSE_PATH")
            if index < len(parts) or directory:
                need(bool(attrs & 0x10), "DIRECTORY_REQUIRED")
            else:
                need(not attrs & 0x10, "REGULAR_FILE_REQUIRED")

    def final_path(self, handle, path):
        buf = ctypes.create_unicode_buffer(32768)
        length = self.k.GetFinalPathNameByHandleW(handle, buf, len(buf), 0)
        need(0 < length < len(buf)
             and norm(buf.value.removeprefix("\\\\?\\")) == norm(path),
             "FINAL_PATH_MISMATCH")

    @contextlib.contextmanager
    def reader(self, path, share=1):
        import msvcrt
        self.check(path)
        handle = self.k.CreateFileW(path, 0x80000000, share, None, 3, 0x00200000, None)
        need(handle not in (None, ctypes.c_void_p(-1).value), "READ_HANDLE_UNAVAILABLE")
        try:
            self.final_path(handle, path)
            descriptor = msvcrt.open_osfhandle(handle, os.O_RDONLY | os.O_BINARY)
            handle = None
            with os.fdopen(descriptor, "rb") as stream:
                opened, current = os.fstat(stream.fileno()), os.stat(path, follow_symlinks=False)
                need(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1
                     and (opened.st_dev, opened.st_ino) == (current.st_dev, current.st_ino),
                     "FILE_IDENTITY_OR_LINKS")
                yield stream, opened
        finally:
            if handle is not None:
                self.k.CloseHandle(handle)

    def read(self, path, maximum, share=1, prefix_size=None, identity=None):
        with self.reader(path, share=share) as (stream, before):
            need(0 <= before.st_size <= maximum, "FILE_SIZE_LIMIT")
            count = before.st_size if prefix_size is None else prefix_size
            need(before.st_size >= count, "FILE_TRUNCATED")
            need(identity is None or identity == (before.st_dev, before.st_ino),
                 "FILE_IDENTITY_CHANGED")
            data = stream.read(count)
            after = os.fstat(stream.fileno())
            need(len(data) == count and after.st_size >= before.st_size, "FILE_CHANGED_DURING_READ")
            return data, (before.st_dev, before.st_ino)

    def write_receipt(self, value):
        import msvcrt
        self.check(OPS, directory=True)
        name = ("active_watchdog_activation_receipt_"
                + utc_now().strftime("%Y%m%dT%H%M%S%fZ") + "_" + uuid.uuid4().hex + ".json")
        path = OPS + "\\" + name
        payload = (json.dumps(value, ensure_ascii=True, sort_keys=True, indent=2)
                   + "\n").encode("utf-8")
        # Standard open preserves the installed Python audit/write-guard path.
        with open(path, "xb", buffering=0) as stream:
            self.final_path(msvcrt.get_osfhandle(stream.fileno()), path)
            self.check(path)
            opened, current = os.fstat(stream.fileno()), os.stat(path, follow_symlinks=False)
            need(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1
                 and (opened.st_dev, opened.st_ino) == (current.st_dev, current.st_ino),
                 "RECEIPT_FILE_IDENTITY")
            remaining = memoryview(payload)
            while remaining:
                written = stream.write(remaining)
                need(type(written) is int and written > 0, "RECEIPT_WRITE_NO_PROGRESS")
                remaining = remaining[written:]
            stream.flush()
            os.fsync(stream.fileno())
        actual, unused_id = self.read(path, 262144)
        need(actual == payload, "RECEIPT_READBACK_MISMATCH")
        return {"path": path, "bytes": len(payload), "sha256": sha(payload)}

PS_METADATA = r"""
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$t=Get-ScheduledTask -TaskName 'MRL_Watchdog' -TaskPath '\'
$i=Get-ScheduledTaskInfo -InputObject $t
$ps=@(Get-CimInstance Win32_Process -Filter "Name='python.exe' OR Name='pythonw.exe'" |
 ForEach-Object {[ordered]@{pid=[int]$_.ProcessId;exe=$_.ExecutablePath;command=$_.CommandLine;created=if($_.CreationDate){$_.CreationDate.ToUniversalTime().ToString('o')}else{$null}}})
[ordered]@{
 task=[ordered]@{state=$t.State.ToString();enabled=[bool]$t.Settings.Enabled;action_count=@($t.Actions).Count;execute=[string]$t.Actions[0].Execute;arguments=[string]$t.Actions[0].Arguments;last_run=$i.LastRunTime.ToUniversalTime().ToString('o');last_result=[long]$i.LastTaskResult;execution_limit=[string]$t.Settings.ExecutionTimeLimit;restart_count=[int]$t.Settings.RestartCount;restart_interval=[string]$t.Settings.RestartInterval}
 processes=$ps
 bridge=(Get-Service -Name 'MRL_Bridge').Status.ToString()
 tunnel=(Get-Service -Name 'MRL_Tunnel').Status.ToString()
}|ConvertTo-Json -Depth 6 -Compress
"""

def current_metadata(driver):
    done = subprocess.run([driver.ps, "-NoProfile", "-NonInteractive", "-Command", PS_METADATA],
                          capture_output=True, timeout=25, creationflags=0x08000000)
    need(done.returncode == 0 and 0 < len(done.stdout) <= 2097152, "LIVE_METADATA_COMMAND")
    data = strict_json(done.stdout.decode("utf-8-sig"))
    need(type(data) is dict and type(data.get("task")) is dict
         and type(data.get("processes")) is list, "LIVE_METADATA_FORMAT")
    task = data["task"]
    need(task.get("state") == "Running" and task.get("enabled") is True, "TASK_NOT_RUNNING")
    need(type(task.get("action_count")) is int and task["action_count"] == 1,
         "TASK_ACTION_COUNT")
    need(type(task.get("execute")) is str and norm(task["execute"]) == norm(PYTHON),
         "TASK_EXECUTABLE")
    need(type(task.get("arguments")) is str
         and sha(task["arguments"].encode("utf-8")) == ARGS_SHA, "TASK_ARGUMENTS_HASH")
    need(task.get("execution_limit") == "PT0S"
         and type(task.get("restart_count")) is int and task["restart_count"] == 3
         and task.get("restart_interval") == "PT1M", "TASK_SETTINGS")
    matches = []
    for proc in data["processes"]:
        need(type(proc) is dict and type(proc.get("pid")) is int
             and type(proc.get("command")) is str and bool(proc["command"])
             and type(proc.get("exe")) is str and bool(proc["exe"]),
             "PYTHON_PROCESS_VISIBILITY")
        argv = driver.argv(proc["command"])
        target = any(norm(arg) == norm(HELPER) for arg in argv[1:])
        if target:
            exact = (len(argv) == 6 and norm(argv[0]) == norm(PYTHON)
                     and argv[1] == "-B" and norm(argv[2]) == norm(HELPER)
                     and argv[3:5] == ["--run", "--runtime-root"]
                     and norm(argv[5]) == norm(RUNTIME)
                     and norm(proc["exe"]) == norm(PYTHON))
            need(exact, "WATCHDOG_PROCESS_ARGUMENTS")
            matches.append(proc)
    need(len(matches) == 1 and matches[0]["pid"] == WATCHDOG_PID,
         "WATCHDOG_PROCESS_COUNT_OR_PID")
    created = stamp(matches[0].get("created"))
    need(created >= stamp(ACTIVATION_UTC) - dt.timedelta(seconds=2),
         "WATCHDOG_PROCESS_PREDATES_ACTIVATION")
    need(data.get("bridge") == "Running" and data.get("tunnel") == "Running",
         "BRIDGE_OR_TUNNEL_NOT_RUNNING")
    return {
        "task_state": "Running", "task_enabled": True, "task_arguments_sha256": ARGS_SHA,
        "watchdog_process_count": 1, "watchdog_pid": WATCHDOG_PID,
        "watchdog_created_at_utc": created.isoformat(),
        "task_last_run_at_utc": task.get("last_run"),
        "task_last_result": task.get("last_result"),
        "bridge": "Running", "tunnel": "Running",
    }, created

def check_live(driver, module):
    snapshot = driver.snapshot()
    owners = lambda port: {c["pid"] for c in snapshot["connections"]
                           if c["port"] == port and c["listen"]}
    need(owners(7500) == {INFERENCE_PID}, "INFERENCE_OWNER_CHANGED")
    need(owners(7700) == {ASI_PID}, "ASI_OWNER_CHANGED")
    need(bool(owners(7800)), "BRIDGE_PORT_NOT_LISTENING")
    need(module["observation_candidate"](snapshot) == ASI_PID,
         "LIVE_ASI_IDENTITY_OR_RECOVERY_HOLD_CHANGED")
    need(driver.health() is True, "LIVE_ASI_HEALTH")
    return {"inference_7500_pid": INFERENCE_PID, "asi_7700_pid": ASI_PID,
            "asi_health_observed": True, "recovery_held": True}

def no_attempts(files):
    files.check(RUNTIME, directory=True)
    with os.scandir(RUNTIME) as entries:
        count = sum(entry.name.casefold().startswith("attempt-") for entry in entries)
    need(count == 0, "ATTEMPT_RECORD_PRESENT")
    return 0

def verify(files):
    with contextlib.ExitStack() as stack:
        source_meta = {}
        for name, path, expected, size in (
            ("watchdog_helper", HELPER, HELPER_SHA, 32301),
            ("python", PYTHON, PYTHON_SHA, 103192),
            ("original_watchdog", ORIGINAL, ORIGINAL_SHA, 1787),
            ("asi_entry", ASI, ASI_SHA, 355),
            ("node", NODE, NODE_SHA, None),
        ):
            stream, info = stack.enter_context(files.reader(path))
            need(info.st_size <= 134217728, "SOURCE_SIZE_LIMIT")
            data = stream.read()
            need(sha(data) == expected and (size is None or len(data) == size),
                 "FIXED_SOURCE_HASH_OR_SIZE")
            source_meta[name] = {"bytes": len(data), "sha256": expected}
        # The verified helper remains pinned against writes/replacement. Its main is not run.
        module = runpy.run_path(HELPER, run_name="MRL_activation_verified_source")
        need(module.get("SCHEMA") == SCHEMA and module.get("ORIGIN") == ORIGIN,
             "VERIFIED_MODULE_CONTRACT")
        driver = module["WindowsDriver"](RUNTIME)
        owner_bytes, unused_id = files.read(RUNTIME + r"\owner.json", 65536)
        need(strict_json(owner_bytes) == {
            "schema": SCHEMA, "origin_signature": ORIGIN,
            "node_sha256": NODE_SHA, "entry_sha256": ASI_SHA,
        }, "OWNER_MARKER_MISMATCH")
        no_attempts(files)
        before, created = current_metadata(driver)
        live_before = check_live(driver, module)
        log_path = RUNTIME + "\\observations-" + DAY + ".jsonl"
        raw, log_id = files.read(log_path, MAX_LOG_BYTES, share=3)
        observed_at = utc_now()
        summary = aggregate_prefix(raw, created, observed_at)
        after, after_created = current_metadata(driver)
        live_after = check_live(driver, module)
        need(after == before and after_created == created, "TASK_PROCESS_METADATA_CHANGED")
        need(live_after == live_before, "LIVE_OWNER_OR_HEALTH_CHANGED")
        repeated, unused_id = files.read(log_path, MAX_LOG_BYTES, share=3,
                                         prefix_size=len(raw), identity=log_id)
        need(repeated == raw, "OBSERVATION_PREFIX_CHANGED")
        no_attempts(files)
        return {
            "schema": "MRL_active_watchdog_activation_receipt_v1",
            "origin_signature": ORIGIN, "record_mode": "APPEND_ONLY",
            "status": "ACTIVE_MONITORING_PASS_RECOVERY_HELD",
            "host": HOST, "observed_at_utc": observed_at.isoformat(),
            "verified_at_utc": utc_now().isoformat(),
            "source_hashes_verified": source_meta,
            "observations": summary,
            "owner_marker": {"schema": SCHEMA, "valid": True,
                             "bytes": len(owner_bytes), "sha256": sha(owner_bytes)},
            "attempt_record_count": 0, "task_and_process": after,
            "current_services": live_after,
            "installation_reference": {
                "provenance": "CONTROLLER_REPORTED_METADATA",
                "configured_at_utc": "2026-10-10T18:49:49Z",
                "installer_receipt_bytes": 2118,
                "installer_receipt_sha256": "2e7ed8368f0b1568410b4d9c4562983d3403cec0d029e946c0ebc148c43a8726",
                "xml_backup_bytes": 1137,
                "xml_backup_sha256": "2e291e5878b7cb05b32b45597479baa5e748d459a9fc7960ea68b2bf94b67ab3",
            },
            "runtime_recovery": "HELD_UNRESOLVED_RELATIVE_PROCESS",
            "fault_recovery": "UNVERIFIED", "reboot_continuity": "UNVERIFIED",
            "service_start_stop_calls": 0, "task_mutation_calls": 0,
            "log_or_source_bodies_exported": False,
        }

def main():
    files = None
    try:
        files = LocalFiles()
        result = verify(files)
    except BaseException as exc:
        result = {
            "schema": "MRL_active_watchdog_activation_receipt_v1",
            "origin_signature": ORIGIN, "record_mode": "APPEND_ONLY",
            "status": "ACTIVE_MONITORING_NOT_VERIFIED",
            "error_code": str(exc) if isinstance(exc, Gate) else type(exc).__name__,
            "verified_at_utc": utc_now().isoformat(),
            "service_start_stop_calls": 0, "task_mutation_calls": 0,
            "fault_recovery": "UNVERIFIED", "reboot_continuity": "UNVERIFIED",
        }
    if files is not None:
        try:
            receipt = files.write_receipt(result)
        except BaseException as exc:
            print(json.dumps({"status": "ACTIVATION_RECEIPT_NOT_COMMITTED",
                              "error_code": str(exc) if isinstance(exc, Gate) else type(exc).__name__,
                              "evidence_status": result["status"],
                              "partial_new_receipt_possible": True,
                              "service_start_stop_calls": 0, "task_mutation_calls": 0},
                             sort_keys=True))
            return 1
        result["receipt"] = receipt
    print(json.dumps(result, ensure_ascii=True, sort_keys=True))
    return 0 if result["status"] == "ACTIVE_MONITORING_PASS_RECOVERY_HELD" else 1

if __name__ == "__main__":
    raise SystemExit(main())
