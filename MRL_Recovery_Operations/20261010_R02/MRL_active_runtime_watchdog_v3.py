#!/usr/bin/env python3
# origin_signature: MrLiouWord
"""MRL active runtime watchdog: 7500/7800 report only; bounded ASI 7700 start.
Cloud-origin helper; the historical Watchdog.py is neither read nor changed.
Live mode requires the fixed Windows host and isolated D runtime directory.
"""
import argparse
import contextlib
import ctypes
import datetime as dt
import hashlib
import json
import ntpath
import os
from pathlib import Path
import stat
import subprocess
import sys
import time

HOST = "WIN-PBVUI7VK2A6"
NODE = r"D:\MrlToolchain\node\node.exe"
ENTRY = r"D:\mrl\asi-engine\server.js"
CWD = r"D:\mrl\asi-engine"
RUNTIME = r"D:\MRL_Mother\Recovery\_operations\LocalAI_20261010_R02_be2f1d63\active_watchdog_20261010_R01"
NODE_SHA = "bc585910690318aaebe3c57669cb83ca9d1e5791efd63195e238f54686e6c2ec"
ENTRY_SHA = "4dfd3194b7519efb6eef7236024a3953d2dd8842c9dc38c52ec71c6c0c807f5e"
SCHEMA = "MRL_active_runtime_watchdog_v3"
ORIGIN = "MrLiouWord"
MAX_ATTEMPTS = 3
PS_SCRIPT = r"""
$ErrorActionPreference='Stop'
[Console]::OutputEncoding=New-Object System.Text.UTF8Encoding($false)
$c=@(Get-NetTCPConnection -ErrorAction Stop |
 Where-Object {$_.LocalPort -in @(7500,7700,7800)} |
 Select-Object LocalPort,State,OwningProcess)
$p=@(Get-CimInstance Win32_Process -Filter "Name='node.exe'" -ErrorAction Stop |
 Select-Object ProcessId,ExecutablePath,CommandLine)
[ordered]@{connections=$c;processes=$p}|ConvertTo-Json -Depth 4 -Compress
"""

def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def norm(value):
    return ntpath.normcase(ntpath.normpath(value))

class Hold(Exception):
    pass

def node_environment():
    env = os.environ.copy()
    if any(k.upper() in ("NODE_OPTIONS", "NODE_PATH") and value
           for k, value in env.items()):
        raise Hold("HOLD_NODE_ENVIRONMENT")
    return env

def classify(snapshot):
    """No raw command lines, paths, or HTTP bodies leave the driver."""
    links = snapshot["connections"]
    procs = snapshot["processes"]
    exact, ambiguous = [], False
    for p in procs:
        argv = p.get("argv")
        if not argv or not p.get("exe"):
            ambiguous = True
            continue
        target = any(norm(a) == norm(ENTRY) for a in argv[1:])
        relative = any(ntpath.basename(a).lower() == "server.js"
                       and not ntpath.isabs(a) for a in argv[1:])
        if target:
            canonical = (len(argv) == 2 and norm(argv[0]) == norm(NODE)
                         and norm(p["exe"]) == norm(NODE))
            exact.append((p["pid"], canonical))
        ambiguous = ambiguous or relative
    asi_links = [c for c in links if c["port"] == 7700]
    listeners = {c["pid"] for c in asi_links if c["listen"]}
    report = {str(port): ("LISTENING" if any(
        c["port"] == port and c["listen"] for c in links) else "NO_LISTENER")
        for port in (7500, 7800)}
    if ambiguous:
        state = "HOLD_PROCESS_VISIBILITY"
    elif len(exact) > 1:
        state = "HOLD_MULTIPLE_ASI"
    elif exact:
        pid, canonical = exact[0]
        if not canonical:
            state = "HOLD_PROCESS_IDENTITY"
        elif not listeners:
            state = "HOLD_EXISTING_ASI_NO_LISTENER"
        elif listeners != {pid}:
            state = "HOLD_PORT_OWNER"
        else:
            state = "PRESENT"
    elif asi_links:
        state = "HOLD_PORT_OCCUPIED"
    else:
        state = "FREE"
    return state, report, exact[0][0] if len(exact) == 1 else None

def relative_processes(snapshot):
    return [p for p in snapshot["processes"] if p.get("argv") and any(
        ntpath.basename(a).lower() == "server.js" and not ntpath.isabs(a)
        for a in p["argv"][1:])]

def observation_candidate(snapshot):
    """Positive owner observation only; NEVER used to permit a start."""
    if classify(snapshot)[0] != "HOLD_PROCESS_VISIBILITY":
        return None
    if any(not p.get("argv") or not p.get("exe") for p in snapshot["processes"]):
        return None
    if not relative_processes(snapshot):
        return None
    targets = [p for p in snapshot["processes"] if any(
        norm(a) == norm(ENTRY) for a in p["argv"][1:])]
    if len(targets) != 1:
        return None
    p = targets[0]
    if (len(p["argv"]) != 2 or norm(p["argv"][0]) != norm(NODE)
            or norm(p["exe"]) != norm(NODE)):
        return None
    owners = {c["pid"] for c in snapshot["connections"]
              if c["port"] == 7700 and c["listen"]}
    return p["pid"] if owners == {p["pid"]} else None

def stable_health(driver, pid):
    if not driver.health():
        return False
    state, unused_report, observed_pid = classify(driver.snapshot())
    return state == "PRESENT" and observed_pid == pid

def cycle(driver, state, now, cooldown, dry=False):
    result = {"schema": SCHEMA, "origin_signature": ORIGIN, "checked_at_utc": utc(),
              "mode": "DRY_RUN" if dry else "ACTIVE", "process_starts": 0,
              "process_starts_scope": "ASI_7700",
              "inference_7500_actions": 0, "bridge_7800_actions": 0,
              "runtime_recovery": "NOT_ASSERTED", "restart_eligibility": "NOT_ASSERTED"}
    try:
        driver.check_node_environment()
        with driver.pinned_sources():
            result["source_hashes_verified"] = True
            snapshot = driver.snapshot()
            current, report, pid = classify(snapshot)
            result["report_only"] = report
            result["state"] = current
            if current == "PRESENT":
                observed = stable_health(driver, pid)
                result.update(asi_owner_pid=pid, asi_process_identity_verified=True,
                              asi_health_observed=observed,
                              restart_eligibility="NOT_NEEDED_EXISTING_ASI")
                result["state"] = "HEALTHY" if observed else "HOLD_HEALTH"
                return result
            if current == "HOLD_PROCESS_VISIBILITY" and relative_processes(snapshot):
                # Unresolved relatives continue to block every recovery action.
                result["restart_eligibility"] = "HELD_UNRESOLVED_RELATIVE_PROCESS"
                result["unresolved_relative_process_count"] = len(relative_processes(snapshot))
                candidate = observation_candidate(snapshot)
                if candidate is not None:
                    result.update(asi_owner_pid=candidate, asi_process_identity_verified=True)
                    observed = driver.health()
                    if observed:
                        observed = observation_candidate(driver.snapshot()) == candidate
                    result["asi_health_observed"] = observed
                    result["state"] = ("ASI_HEALTH_OBSERVED_RECOVERY_HELD" if observed
                                       else "HOLD_HEALTH_WITH_UNRESOLVED_RELATIVE_PROCESS")
                return result
            if current != "FREE":
                return result
            if state["attempts"] >= MAX_ATTEMPTS:
                result["state"] = "HOLD_RETRY_LIMIT"
                return result
            if state["attempts"] and now - state["last"] < cooldown:
                result["state"] = "HOLD_COOLDOWN"
                return result
            if dry:
                result["state"] = "WOULD_START_ASI"
                return result
            # Recheck under the same global mutex immediately before reserving.
            fresh, report, unused_pid = classify(driver.snapshot())
            result["report_only"] = report
            if fresh != "FREE":
                result["state"] = "HOLD_CHANGED_BEFORE_START"
                return result
            state["attempts"] += 1
            state["last"] = now
            driver.reserve(state)  # Durable before Popen; failures count too.
            child = driver.start()
            result["process_starts"] = 1
            result["owned_child_pid"] = child.pid
            result["state"] = "STARTED_PENDING"
            driver.startup_wait()
            seen, report, pid = classify(driver.snapshot())
            result["report_only"] = report
            if child.poll() is not None:
                result["state"] = "HOLD_CHILD_EXITED"
            elif (seen == "PRESENT" and pid == child.pid and stable_health(driver, pid)
                  and child.poll() is None):
                result["state"] = "STARTED_HEALTHY"
                result["runtime_recovery"] = "OWNED_ASI_HEALTH_OBSERVED"
            else:
                result["state"] = "HOLD_STARTUP_UNVERIFIED"
            # Never kill a child, including a child whose startup is unverified.
    except Hold as exc:
        result["state"] = str(exc)
    except Exception:
        result["state"] = "HOLD_DRIVER_ERROR"
    return result

class WindowsDriver:
    def __init__(self, runtime):
        if sys.platform != "win32":
            raise Hold("HOLD_HOST")
        if norm(runtime) != norm(RUNTIME):
            raise Hold("HOLD_RUNTIME_SCOPE")
        self.runtime = Path(runtime)
        self.k = ctypes.WinDLL("kernel32", use_last_error=True)
        from ctypes import wintypes as w
        self.k.GetComputerNameW.argtypes = [w.LPWSTR, ctypes.POINTER(w.DWORD)]
        host, capacity = ctypes.create_unicode_buffer(256), w.DWORD(256)
        if not self.k.GetComputerNameW(host, ctypes.byref(capacity)) or host.value.upper() != HOST:
            raise Hold("HOLD_HOST")
        self.k.GetFileAttributesW.argtypes = [w.LPCWSTR]
        self.k.GetFileAttributesW.restype = w.DWORD
        self.k.GetDriveTypeW.argtypes = [w.LPCWSTR]
        self.k.GetDriveTypeW.restype = w.UINT
        self.k.CreateFileW.argtypes = [w.LPCWSTR,w.DWORD,w.DWORD,w.LPVOID,w.DWORD,w.DWORD,w.HANDLE]
        self.k.CreateFileW.restype = w.HANDLE
        self.k.CloseHandle.argtypes = [w.HANDLE]
        self.k.CloseHandle.restype = w.BOOL
        self.k.GetFinalPathNameByHandleW.argtypes = [w.HANDLE,w.LPWSTR,w.DWORD,w.DWORD]
        self.k.GetFinalPathNameByHandleW.restype = w.DWORD
        self.k.CreateMutexW.argtypes = [w.LPVOID,w.BOOL,w.LPCWSTR]
        self.k.CreateMutexW.restype = w.HANDLE
        self.k.ReleaseMutex.argtypes = [w.HANDLE]
        self.k.GetSystemDirectoryW.argtypes = [w.LPWSTR,w.UINT]
        self.k.GetSystemDirectoryW.restype = w.UINT
        self.k.LocalFree.argtypes = [w.HLOCAL]
        self.k.LocalFree.restype = w.HLOCAL
        self.shell = ctypes.WinDLL("shell32", use_last_error=True)
        self.shell.CommandLineToArgvW.argtypes = [w.LPCWSTR,ctypes.POINTER(ctypes.c_int)]
        self.shell.CommandLineToArgvW.restype = ctypes.POINTER(w.LPWSTR)
        buf = ctypes.create_unicode_buffer(32768)
        n = self.k.GetSystemDirectoryW(buf, len(buf))
        if not n or n >= len(buf):
            raise Hold("HOLD_SYSTEM_DIRECTORY")
        self.ps = str(Path(buf.value) / "WindowsPowerShell" / "v1.0" / "powershell.exe")
        self.check_path(str(self.runtime.parent), directory=True)

    def check_node_environment(self):
        return node_environment()

    def check_path(self, path, directory=False):
        if not ntpath.isabs(path) or ntpath.splitdrive(path)[0].upper() != "D:":
            raise Hold("HOLD_PATH")
        tail = path[3:]
        if path[:3].upper() != "D:\\" or any(x in ("", ".", "..") for x in tail.split("\\")):
            raise Hold("HOLD_PATH")
        if ":" in tail or "/" in tail or self.k.GetDriveTypeW("D:\\") != 3:
            raise Hold("HOLD_PATH")
        parts = tail.split("\\")
        for i in range(len(parts) + 1):
            part = "D:\\" + "\\".join(parts[:i])
            attrs = self.k.GetFileAttributesW(part)
            if attrs == 0xffffffff or attrs & 0x400:
                raise Hold("HOLD_PATH_REPARSE_OR_MISSING")
            if (i < len(parts) or directory) and not attrs & 0x10:
                raise Hold("HOLD_PATH_TYPE")
        return path

    def argv(self, command):
        count = ctypes.c_int()
        pointer = self.shell.CommandLineToArgvW(command, ctypes.byref(count))
        if not pointer:
            raise Hold("HOLD_COMMAND_PARSE")
        try:
            return [pointer[i] for i in range(count.value)]
        finally:
            self.k.LocalFree(ctypes.cast(pointer, ctypes.c_void_p))

    @contextlib.contextmanager
    def mutex(self):
        ctypes.set_last_error(0)
        handle = self.k.CreateMutexW(None, True, r"Global\MRL_ActiveRuntimeWatchdog_ASI7700_v1")
        error = ctypes.get_last_error()
        if not handle:
            raise Hold("HOLD_MUTEX_UNAVAILABLE")
        if error == 183:
            self.k.CloseHandle(handle)
            raise Hold("HOLD_ALREADY_RUNNING")
        try:
            yield
        finally:
            self.k.ReleaseMutex(handle)
            self.k.CloseHandle(handle)

    @contextlib.contextmanager
    def pinned_sources(self):
        import msvcrt
        handles = []
        try:
            self.check_path(CWD, directory=True)
            for path, expected, size in ((NODE, NODE_SHA, None), (ENTRY, ENTRY_SHA, 355)):
                self.check_path(path)
                # Share-read only: neither replacement nor writing is allowed
                # while hash validation and launch/ownership checks are active.
                h = self.k.CreateFileW(path, 0x80000000, 1, None, 3, 0x00200000, None)
                if h in (None, ctypes.c_void_p(-1).value):
                    raise Hold("HOLD_SOURCE_LOCK")
                buf = ctypes.create_unicode_buffer(32768)
                n = self.k.GetFinalPathNameByHandleW(h, buf, len(buf), 0)
                if not n or n >= len(buf) or norm(buf.value.removeprefix("\\\\?\\")) != norm(path):
                    self.k.CloseHandle(h)
                    raise Hold("HOLD_SOURCE_FINAL_PATH")
                try:
                    fd = msvcrt.open_osfhandle(h, os.O_RDONLY | os.O_BINARY)
                except Exception:
                    self.k.CloseHandle(h)
                    raise
                f = os.fdopen(fd, "rb")
                handles.append(f)
                digest, length = hashlib.sha256(), 0
                for data in iter(lambda: f.read(1048576), b""):
                    digest.update(data)
                    length += len(data)
                if digest.hexdigest() != expected or (size is not None and length != size):
                    raise Hold("HOLD_SOURCE_HASH")
            yield
        finally:
            for f in reversed(handles):
                f.close()

    def snapshot(self):
        done = subprocess.run([self.ps, "-NoProfile", "-NonInteractive", "-Command", PS_SCRIPT],
                              capture_output=True, timeout=20, creationflags=0x08000000)
        if done.returncode or len(done.stdout) > 2097152:
            raise Hold("HOLD_SNAPSHOT")
        try:
            data = json.loads(done.stdout.decode("utf-8-sig"))
            links, processes = [], []
            for c in data["connections"]:
                links.append({"port": int(c["LocalPort"]), "pid": int(c["OwningProcess"]),
                              "listen": str(c["State"]).lower() in ("listen", "2")})
            for p in data["processes"]:
                command = p["CommandLine"]
                processes.append({"pid": int(p["ProcessId"]), "exe": p["ExecutablePath"],
                                  "argv": self.argv(command) if command else None})
            return {"connections": links, "processes": processes}
        except Exception:
            raise Hold("HOLD_SNAPSHOT_FORMAT") from None

    def health(self):
        import http.client
        conn = http.client.HTTPConnection("127.0.0.1", 7700, timeout=3)
        try:
            conn.request("GET", "/health", headers={"User-Agent": "MRL-Recovery-Validator/1.0"})
            response = conn.getresponse()
            body = response.read(4097)
            if response.status != 200 or len(body) > 4096:
                return False
            obj = json.loads(body)
            return isinstance(obj, dict) and obj.get("status") == "PASS" and obj.get("origin") == "MrLiouWord"
        except Exception:
            return False
        finally:
            conn.close()

    def initialize_storage(self):
        if not os.path.lexists(self.runtime):
            os.mkdir(self.runtime)
        self.check_path(str(self.runtime), directory=True)
        marker = self.runtime / "owner.json"
        expected = {"schema": SCHEMA, "origin_signature": ORIGIN, "node_sha256": NODE_SHA, "entry_sha256": ENTRY_SHA}
        if os.path.lexists(marker):
            if self.read_json(marker) != expected:
                raise Hold("HOLD_STORAGE_OWNER")
        else:
            self.write_new(marker, expected)

    def read_json(self, path):
        self.check_path(str(path))
        if path.stat().st_size > 65536:
            raise Hold("HOLD_STORAGE_FORMAT")
        try:
            return json.loads(path.read_bytes())
        except Exception:
            raise Hold("HOLD_STORAGE_FORMAT") from None

    def write_new(self, path, value):
        self.check_path(str(self.runtime), directory=True)
        with open(path, "x", encoding="utf-8", newline="\n") as f:
            json.dump(value, f, ensure_ascii=True, sort_keys=True)
            f.write("\n")
            f.flush()
            os.fsync(f.fileno())

    def load_state(self):
        state = {"attempts": 0, "last": 0.0}
        if not os.path.lexists(self.runtime):
            return state
        self.check_path(str(self.runtime), directory=True)
        for i in range(1, MAX_ATTEMPTS + 1):
            path = self.runtime / ("attempt-%02d.json" % i)
            if os.path.lexists(path):
                value = self.read_json(path)
                if (value.get("schema") != SCHEMA or value.get("origin_signature") != ORIGIN
                        or value.get("attempts") != i):
                    raise Hold("HOLD_ATTEMPT_RECORD")
                when = value.get("last")
                if not isinstance(when, (int, float)) or not 0 < when <= time.time() + 5:
                    raise Hold("HOLD_ATTEMPT_CLOCK")
                if state["attempts"] != i - 1:
                    raise Hold("HOLD_ATTEMPT_SEQUENCE")
                state = {"attempts": i, "last": float(when)}
        return state

    def reserve(self, state):
        self.write_new(self.runtime / ("attempt-%02d.json" % state["attempts"]),
                       {"schema": SCHEMA, "origin_signature": ORIGIN, **state})

    def record(self, result, io=os):
        self.check_path(str(self.runtime), directory=True)
        date = dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d")
        path = self.runtime / ("observations-" + date + ".jsonl")
        exists = io.path.lexists(path)
        if exists:
            self.check_path(str(path))
            before = io.stat(path, follow_symlinks=False)
            if not stat.S_ISREG(before.st_mode) or before.st_nlink != 1:
                raise Hold("HOLD_OBSERVATION_FILE")
        flags = os.O_WRONLY | os.O_APPEND | getattr(os, "O_BINARY", 0)
        flags |= getattr(os, "O_NOINHERIT", 0)
        if not exists:
            flags |= os.O_CREAT | os.O_EXCL
        fd = io.open(path, flags, 0o600)
        try:
            self.check_path(str(path))
            opened, current = io.fstat(fd), io.stat(path, follow_symlinks=False)
            if (not stat.S_ISREG(opened.st_mode) or opened.st_nlink != 1
                    or (opened.st_dev, opened.st_ino) != (current.st_dev, current.st_ino)
                    or (exists and (opened.st_dev, opened.st_ino)
                        != (before.st_dev, before.st_ino))):
                raise Hold("HOLD_OBSERVATION_FILE")
            data = (json.dumps(result, ensure_ascii=True, sort_keys=True) + "\n").encode("utf-8")
            while data:
                written = io.write(fd, data)
                if written <= 0:
                    raise Hold("HOLD_OBSERVATION_WRITE")
                data = data[written:]
            io.fsync(fd)
        finally:
            io.close(fd)

    def start(self):
        self.check_node_environment()  # Before even the read-only PS snapshot.
        for path in (NODE, ENTRY):
            self.check_path(path)
        self.check_path(CWD, directory=True)
        if classify(self.snapshot())[0] != "FREE":
            raise Hold("HOLD_CHANGED_AT_LAUNCH")
        env = self.check_node_environment()  # Preserve every permitted value.
        return subprocess.Popen([NODE, ENTRY], executable=NODE, cwd=CWD, env=env,
                                stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                stderr=subprocess.DEVNULL, close_fds=True,
                                creationflags=0x00000008 | 0x00000200)

    def startup_wait(self):
        time.sleep(2)

def self_test():
    def snap(port=True, process=True, target=True):
        links = [{"port": 7500, "pid": 10, "listen": True},
                 {"port": 7800, "pid": 11, "listen": True}]
        if port:
            links.append({"port": 7700, "pid": 99, "listen": True})
        procs = ([{"pid": 99, "exe": NODE, "argv": [NODE, ENTRY] if target else [NODE, ENTRY, "--extra"]}]
                 if process else [])
        return {"connections": links, "processes": procs}

    class Fake:
        def __init__(self, snapshots, health=True, bad_hash=False):
            self.snapshots = list(snapshots)
            self.healthy, self.bad_hash = health, bad_hash
            self.starts = self.reserves = self.health_calls = 0
        def check_node_environment(self):
            return {}
        @contextlib.contextmanager
        def pinned_sources(self):
            if self.bad_hash:
                raise Hold("HOLD_SOURCE_HASH")
            yield
        def snapshot(self):
            return self.snapshots.pop(0) if len(self.snapshots) > 1 else self.snapshots[0]
        def health(self):
            self.health_calls += 1
            return self.healthy
        def reserve(self, state):
            self.reserves += 1
        def start(self):
            self.starts += 1
            return type("Child", (), {"pid": 99, "poll": lambda self: None})()
        def startup_wait(self):
            pass

    checks = []
    def case(name, driver, expected, starts=0, state=None, dry=False):
        state = state if state is not None else {"attempts": 0, "last": 0}
        result = cycle(driver, state, 1000, 120, dry)
        ok = (result["state"] == expected and driver.starts == starts
              and driver.reserves == starts and result["inference_7500_actions"] == 0
              and result["bridge_7800_actions"] == 0)
        checks.append({"case": name, "pass": ok})
    case("healthy_zero_actions", Fake([snap()]), "HEALTHY")
    case("absent_exactly_one_start", Fake([snap(False, False), snap(False, False), snap()]),
         "STARTED_HEALTHY", 1)
    for port in (7500, 7800):
        s = snap()
        s["connections"] = [c for c in s["connections"] if c["port"] != port]
        case("report_only_%s_down" % port, Fake([s]), "HEALTHY")
    case("wrong_process_identity", Fake([snap(target=False)]), "HOLD_PROCESS_IDENTITY")
    case("wrong_health_identity", Fake([snap()], health=False), "HOLD_HEALTH")
    case("wrong_source_hash", Fake([snap()], bad_hash=True), "HOLD_SOURCE_HASH")
    case("existing_process_no_port", Fake([snap(False)]), "HOLD_EXISTING_ASI_NO_LISTENER")
    case("foreign_listener", Fake([snap(True, False)]), "HOLD_PORT_OCCUPIED")
    case("cooldown", Fake([snap(False, False)]), "HOLD_COOLDOWN",
         state={"attempts": 1, "last": 950})
    case("retry_limit", Fake([snap(False, False)]), "HOLD_RETRY_LIMIT",
         state={"attempts": 3, "last": 1})
    case("dry_run_no_start", Fake([snap(False, False)]), "WOULD_START_ASI", dry=True)
    case("race_existing_before_launch", Fake([snap(False, False), snap(False)]),
         "HOLD_CHANGED_BEFORE_START")
    s = snap(False, False)
    s["connections"].append({"port": 7700, "pid": 0, "listen": False})
    case("any_7700_tcp_entry_holds", Fake([s]), "HOLD_PORT_OCCUPIED")
    s = snap(False, False)
    s["processes"].append({"pid": 90, "exe": NODE, "argv": None})
    case("incomplete_process_visibility", Fake([s]), "HOLD_PROCESS_VISIBILITY")
    case("new_child_unhealthy_no_duplicate", Fake([snap(False, False), snap(False, False), snap(False)]),
         "HOLD_STARTUP_UNVERIFIED", 1)
    s = snap()
    s["connections"][-1]["pid"] = 98
    case("health_owner_changes", Fake([snap(), s]), "HOLD_HEALTH")
    relative = {"pid": 41, "exe": NODE, "argv": [NODE, "server.js"]}
    ambiguous = snap()
    ambiguous["processes"].append(relative)
    observer = Fake([ambiguous])
    state = {"attempts": 0, "last": 0}
    result = cycle(observer, state, 1000, 120, True)
    checks.append({"case": "canonical_health_observed_recovery_still_held",
                   "pass": result["state"] == "ASI_HEALTH_OBSERVED_RECOVERY_HELD"
                   and result["restart_eligibility"] == "HELD_UNRESOLVED_RELATIVE_PROCESS"
                   and result["asi_health_observed"] is True and result["asi_owner_pid"] == 99
                   and result["runtime_recovery"] == "NOT_ASSERTED"
                   and observer.starts == observer.reserves == 0})
    # Active mode also cannot reserve/start while an unresolved relative exists.
    case("active_observation_never_starts", Fake([ambiguous]),
         "ASI_HEALTH_OBSERVED_RECOVERY_HELD")
    absent = snap(False, False)
    absent["processes"].append(relative)
    blocked = Fake([absent])
    case("relative_unknown_free_port_never_recovers", blocked, "HOLD_PROCESS_VISIBILITY")
    checks.append({"case": "no_health_claim_without_canonical_owner",
                   "pass": blocked.health_calls == 0})
    case("relative_unknown_bad_health_stays_held", Fake([ambiguous], health=False),
         "HOLD_HEALTH_WITH_UNRESOLVED_RELATIVE_PROCESS")
    changed = snap()
    changed["processes"].append(relative)
    changed["connections"][-1]["pid"] = 98
    case("relative_observation_owner_race_fails", Fake([ambiguous, changed]),
         "HOLD_HEALTH_WITH_UNRESOLVED_RELATIVE_PROCESS")
    guarded = Fake([snap(False, False)])
    def environment_hold():
        raise Hold("HOLD_NODE_ENVIRONMENT")
    guarded.check_node_environment = environment_hold
    case("environment_holds_before_reservation", guarded, "HOLD_NODE_ENVIRONMENT")
    # Real launch adapter, replaced Popen and synthetic in-memory environment.
    adapter = object.__new__(WindowsDriver)
    adapter.check_path = lambda *a, **k: None
    adapter.snapshot = lambda: snap(False, False)
    captured, original_popen, original_env = [], subprocess.Popen, os.environ
    test_env = {"PATH": "synthetic", "NODE_OPTIONS": "", "NODE_PATH": "", "MRL_TEST_ONLY": "preserved"}
    def popen_stub(*a, **k):
        captured.append((a, k))
        return object()
    try:
        subprocess.Popen, os.environ = popen_stub, dict(test_env)
        adapter.start()
        a, k = captured[0]
        ok = (len(captured) == 1 and a == ([NODE, ENTRY],)
              and k["executable"] == NODE and k["cwd"] == CWD
              and k.get("shell", False) is False and k["close_fds"] is True
              and k["env"] == test_env)
        checks.append({"case": "launch_adapter_preserves_exact_environment", "pass": ok})
        for name in ("NODE_OPTIONS", "NODE_PATH"):
            os.environ = {**test_env, name: "synthetic-guard"}
            blocked = False
            try:
                adapter.start()
            except Hold as exc:
                blocked = str(exc) == "HOLD_NODE_ENVIRONMENT"
            checks.append({"case": name.lower() + "_holds_without_popen",
                           "pass": blocked and len(captured) == 1})
        os.environ = dict(test_env)
        adapter.snapshot = lambda: snap(False)
        blocked = False
        try:
            adapter.start()
        except Hold:
            blocked = True
        checks.append({"case": "real_launch_adapter_final_race_gate",
                       "pass": blocked and len(captured) == 1})
    finally:
        subprocess.Popen, os.environ = original_popen, original_env
    # Real observation writer with memory-only file descriptor operations.
    class MemoryIO:
        def __init__(self):
            self.flags, self.data, self.synced = 0, b"", False
            self.path = type("Paths", (), {"lexists": lambda self, p: False})()
        def open(self, path, flags, mode):
            self.flags, self.filename = flags, str(path)
            return 7
        def stat(self, *a, **k):
            return type("Info", (), {"st_mode": stat.S_IFREG | 0o600,
                        "st_nlink": 1, "st_dev": 1, "st_ino": 7})()
        def fstat(self, *a):
            return self.stat()
        def write(self, fd, data):
            self.data += data
            return len(data)
        def fsync(self, fd):
            self.synced = True
        def close(self, fd):
            pass
    memory = MemoryIO()
    adapter.runtime = Path(RUNTIME)
    adapter.record({"schema": SCHEMA, "origin_signature": ORIGIN, "state": "MOCK"}, memory)
    checks.append({"case": "observations_append_exclusive_new_fsync",
                   "pass": bool(memory.flags & os.O_APPEND)
                   and bool(memory.flags & os.O_EXCL) and not bool(memory.flags & os.O_TRUNC)
                   and memory.synced and memory.data.endswith(b"\n")
                   and json.loads(memory.data)["origin_signature"] == ORIGIN
                   and "observations-" in memory.filename})
    result = {"schema": SCHEMA, "origin_signature": ORIGIN, "executed_where": "MOCK_MEMORY_ONLY",
              "checks": checks, "passed": sum(c["pass"] for c in checks),
              "total": len(checks), "real_process_starts": 0,
              "dl580_runtime": "NOT_ASSERTED"}
    print(json.dumps(result, sort_keys=True))
    return 0 if all(c["pass"] for c in checks) else 1

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    modes = parser.add_mutually_exclusive_group(required=True)
    modes.add_argument("--self-test", action="store_true")
    modes.add_argument("--once", action="store_true")
    modes.add_argument("--run", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--runtime-root", default=RUNTIME)
    parser.add_argument("--cooldown-seconds", type=int, default=120)
    args = parser.parse_args()
    if args.self_test:
        return self_test()
    if args.dry_run and not args.once:
        parser.error("--dry-run requires --once")
    if not 60 <= args.cooldown_seconds <= 86400:
        parser.error("--cooldown-seconds must be 60..86400")
    result = None
    try:
        driver = WindowsDriver(args.runtime_root)
        if args.dry_run:
            result = cycle(driver, driver.load_state(), time.time(), args.cooldown_seconds, True)
            result["executed_where"] = "DL580_WINDOWS_D_READ_ONLY"
            print(json.dumps(result, sort_keys=True))
            return 0 if result["state"] in ("HEALTHY", "WOULD_START_ASI", "ASI_HEALTH_OBSERVED_RECOVERY_HELD") else 2
        with driver.mutex():
            driver.initialize_storage()
            state = driver.load_state()
            while True:
                result = cycle(driver, state, time.time(), args.cooldown_seconds)
                result["executed_where"] = "DL580_WINDOWS_D"
                result["attempts_reserved"] = state["attempts"]
                driver.record(result)
                if args.once:
                    print(json.dumps(result, sort_keys=True))
                    return 0 if result["state"] in ("HEALTHY", "STARTED_HEALTHY", "ASI_HEALTH_OBSERVED_RECOVERY_HELD") else 2
                time.sleep(30)
    except KeyboardInterrupt:
        return 130
    except Hold as exc:
        print(json.dumps({"schema": SCHEMA, "origin_signature": ORIGIN, "state": str(exc),
                          "process_starts": result.get("process_starts", 0) if result else 0}))
        return 2
    except Exception:
        print(json.dumps({"schema": SCHEMA, "origin_signature": ORIGIN, "state": "HOLD_DRIVER_ERROR",
                          "process_starts": result.get("process_starts", 0) if result else 0}))
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
