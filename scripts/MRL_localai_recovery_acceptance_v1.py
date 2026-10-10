#!/usr/bin/env python3
"""MRL LocalAI recovery: read-only host/package evidence. origin_signature: MrLiouWord.
SUPPLEMENT_EXISTING: Verify -> Backfill. Does not reboot, restart, rotate keys,
read arbitrary mother files, or promote a transport check to whole-system PASS.
"""
from __future__ import annotations
import argparse
import datetime as dt
import hashlib
import json
import ntpath
import os
from pathlib import Path
import platform
import re
import subprocess
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

ORIGIN = "MrLiouWord"
EXPECTED_HOST = "WIN-PBVUI7VK2A6"
USER_AGENT = "MRL-Recovery-Validator/1.0 (+https://github.com/dofaromg/MRL_AI_SYSTEM)"
MAX_BODY = 65536
PS_METADATA = r"""
$ErrorActionPreference = 'Stop'
$boot = (Get-CimInstance Win32_OperatingSystem).LastBootUpTime.ToUniversalTime()
$tasks = @()
foreach ($name in @('MRL_ASI_Engine','MRL_Watchdog')) {
  $t = Get-ScheduledTask -TaskName $name -ErrorAction SilentlyContinue
  foreach ($task in @($t)) {
    if ($null -eq $task) { continue }
    $info = Get-ScheduledTaskInfo -InputObject $task
    $tasks += [ordered]@{
      name=$task.TaskName; path=$task.TaskPath; state=[string]$task.State
      enabled=[bool]$task.Settings.Enabled
      last_result=$info.LastTaskResult
      last_run_utc=$info.LastRunTime.ToUniversalTime().ToString('o')
      last_run_after_boot=($info.LastRunTime.ToUniversalTime() -ge $boot)
      boot_trigger=@($task.Triggers | Where-Object { $_.CimClass.CimClassName -eq 'MSFT_TaskBootTrigger' }).Count -gt 0
      action_count=@($task.Actions).Count
      action_absolute=@($task.Actions | ForEach-Object { [IO.Path]::IsPathRooted(([string]$_.Execute).Trim('"')) })
      action_node_matches=@($task.Actions | ForEach-Object { ([string]$_.Execute).Trim('"') -ieq 'D:\MrlToolchain\node\node.exe' })
      action_entry_matches=@($task.Actions | ForEach-Object { ([string]$_.Arguments).Trim().Trim('"') -ieq 'D:\mrl\asi-engine\server.js' })
    }
  }
}
$owners = @()
foreach ($conn in @(Get-NetTCPConnection -LocalPort 7700 -State Listen -ErrorAction SilentlyContinue)) {
  $proc = Get-CimInstance Win32_Process -Filter ("ProcessId=" + $conn.OwningProcess)
  if ($null -ne $proc) {
    $owners += [ordered]@{
      pid=$proc.ProcessId; bind=$conn.LocalAddress
      executable_matches=($proc.ExecutablePath -ieq 'D:\MrlToolchain\node\node.exe')
      entry_matches=([string]$proc.CommandLine -match '^\s*"?D:\\MrlToolchain\\node\\node\.exe"?\s+"?D:\\mrl\\asi-engine\\server\.js"?\s*$')
      started_utc=$proc.CreationDate.ToUniversalTime().ToString('o')
    }
  }
}
$services = @()
foreach ($name in @('MRL_Bridge','MRL_Tunnel')) {
  $s = Get-Service -Name $name -ErrorAction SilentlyContinue
  if ($null -ne $s) { $services += [ordered]@{name=$s.Name;status=[string]$s.Status} }
}
$files = @()
foreach ($p in @('D:\mrl\asi-engine\server.js','D:\MrlToolchain\node\node.exe')) {
  if (Test-Path -LiteralPath $p -PathType Leaf) {
    $f = Get-Item -LiteralPath $p
    $files += [ordered]@{path=$p;bytes=$f.Length;sha256=(Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLower()}
  }
}
[ordered]@{
  host=$env:COMPUTERNAME; windows_boot_utc=$boot.ToString('o')
  tasks=$tasks; owners_7700=$owners; services=$services; fixed_file_hashes=$files
  d_free_bytes=(Get-PSDrive -Name D).Free
} | ConvertTo-Json -Depth 9 -Compress
"""

def now():
    return dt.datetime.now(dt.timezone.utc).isoformat()

def check(name, state, **details):
    return {"check": name, "status": state, **details}

def safe_endpoint(value):
    p = urllib.parse.urlsplit(value)
    try:
        _ = p.port
    except ValueError:
        raise ValueError("INVALID_ENDPOINT")
    if not p.hostname or p.username or p.password or p.query or p.fragment:
        raise ValueError("INVALID_ENDPOINT")
    loopback = p.hostname.lower() in {"localhost", "127.0.0.1", "::1"}
    if p.scheme != "https" and not (p.scheme == "http" and loopback):
        raise ValueError("HTTPS_REQUIRED")
    return value.rstrip("/")

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None

def probe(url, key=None):
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}
    if key:
        if any(c in key for c in "\r\n"):
            return {"http_status": None, "error": "INVALID_HEADER"}, None
        headers["x-api-key"] = key
    result = {"endpoint": urllib.parse.urlsplit(url).path, "observed_at_utc": now()}
    try:
        req = urllib.request.Request(url, headers=headers)
        handlers = [NoRedirect()]
        if urllib.parse.urlsplit(url).hostname in {"localhost", "127.0.0.1", "::1"}:
            handlers.insert(0, urllib.request.ProxyHandler({}))
        with urllib.request.build_opener(*handlers).open(req, timeout=10) as response:
            raw = response.read(MAX_BODY + 1)
            result["http_status"] = response.status
            result["content_type"] = response.headers.get_content_type()
    except urllib.error.HTTPError as error:
        result.update(http_status=error.code, error="HTTP_ERROR")
        return result, None
    except Exception as error:
        result.update(http_status=None, error=type(error).__name__)
        return result, None
    if len(raw) > MAX_BODY:
        result["error"] = "RESPONSE_TOO_LARGE"
        return result, None
    result.update(response_bytes=len(raw), response_sha256=hashlib.sha256(raw).hexdigest())
    if result["content_type"] != "application/json":
        result["error"] = "EXPECTED_JSON"
        return result, None
    try:
        body = json.loads(raw)
    except (ValueError, UnicodeError):
        result["error"] = "INVALID_JSON"
        return result, None
    return result, body

def health_check(kind, metadata, body):
    good = metadata.get("http_status") == 200 and not metadata.get("error") and isinstance(body, dict)
    if kind == "ASI7700":
        good = good and body.get("status") == "PASS" and body.get("origin") == ORIGIN
    elif kind == "BRIDGE":
        good = good and body.get("service") == "MRL_Bridge_API"
        good = good and body.get("origin_signature") == ORIGIN
        good = good and all(body.get(k) is True for k in ("api", "pg", "redis"))
    else:
        raise ValueError("UNKNOWN_HEALTH_CONTRACT")
    safe = dict(metadata)
    if isinstance(body, dict):
        safe["service_version"] = body.get("version") if isinstance(body.get("version"), str) and re.fullmatch(r"\d+(?:\.\d+){1,3}", body["version"]) else None
    return check(kind + "_HEALTH", "PASS" if good else "FAIL", **safe)

def _utc(value):
    if not isinstance(value, str):
        return None
    try:
        parsed = dt.datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.astimezone(dt.timezone.utc) if parsed.tzinfo else None
    except (ValueError, TypeError):
        return None

def _records(value):
    return [item for item in value if isinstance(item, dict)] if isinstance(value, list) else []

def _task_state(value):
    # MSFT_TaskState may be returned as a name or enum value.
    state = str(value).strip().upper()
    return {"0": "UNKNOWN", "1": "DISABLED", "2": "QUEUED", "3": "READY", "4": "RUNNING"}.get(state, state)

def _bools(value):
    return [value] if isinstance(value, bool) else value if isinstance(value, list) else []

def _startup_task(task):
    count = task.get("action_count")
    absolute = _bools(task.get("action_absolute"))
    node = _bools(task.get("action_node_matches"))
    entry = _bools(task.get("action_entry_matches"))
    return (task.get("enabled") is True and task.get("boot_trigger") is True and
            _task_state(task.get("state")) in {"QUEUED", "READY", "RUNNING"} and
            type(count) is int and count > 0 and
            len(absolute) == len(node) == len(entry) == count and
            all(flag is True for flag in absolute) and
            any(n is True and e is True for n, e in zip(node, entry)))

def _task_ran_after_boot(task, boot, observed):
    last = _utc(task.get("last_run_utc"))
    state = _task_state(task.get("state"))
    try:
        result = int(task.get("last_result"))
    except (ValueError, TypeError):
        return False
    running = state == "RUNNING" and result in {0, 267009}
    complete = state == "READY" and result == 0
    return bool(last and boot and observed and boot <= last <= observed and
                task.get("last_run_after_boot") is True and (running or complete))

def classify_host(meta, expected=EXPECTED_HOST, previous=None, *, asi_healthy=False, observed_at=None):
    meta = meta if isinstance(meta, dict) else {}
    host = meta.get("host")
    host_ok = isinstance(host, str) and host.upper() == expected.upper()
    checks = [check("DL580_HOST", "PASS" if host_ok else "FAIL")]
    owner_records = meta.get("owners_7700")
    owners = _records(owner_records)
    ours = [p for p in owners if p.get("executable_matches") is True and p.get("entry_matches") is True]
    owner_ok = bool(owners) and len(ours) == len(owners) == len(owner_records)
    checks.append(check("ASI7700_PROCESS_OWNER", "PASS" if owner_ok else "FAIL", count=len(owners)))
    task_records = meta.get("tasks")
    tasks = _records(task_records)
    task_records_valid = isinstance(task_records, list) and len(tasks) == len(task_records)
    asi = [t for t in tasks if t.get("name") == "MRL_ASI_Engine"]
    startup = task_records_valid and bool(asi) and all(_startup_task(t) for t in asi)
    checks.append(check("ASI_STARTUP_CONFIGURATION", "PASS" if startup else "FAIL"))
    watchdog = [t for t in tasks if t.get("name") == "MRL_Watchdog"]
    checks.append(check("WATCHDOG_REGISTERED", "PASS" if task_records_valid and watchdog and all(t.get("enabled") is True for t in watchdog) else "FAIL"))
    checks.append(check("WATCHDOG_FAULT_RECOVERY", "UNVERIFIED", reason="Requires a bounded fault-and-recovery run; task existence is not that test."))
    previous = previous if isinstance(previous, dict) else {}
    old_meta = previous.get("host_metadata")
    old_meta = old_meta if isinstance(old_meta, dict) else {}
    old_host = old_meta.get("host")
    old_boot, boot = _utc(old_meta.get("windows_boot_utc")), _utc(meta.get("windows_boot_utc"))
    old_seen, seen = _utc(previous.get("observed_at_utc")), _utc(observed_at or now())
    prior_checks = {item.get("check"): item.get("status") for item in _records(previous.get("checks"))}
    previous_evidence = (
        previous.get("schema") == "MRL_LocalAI_Recovery_Acceptance_v1" and
        previous.get("execution_environment") == "DL580_WINDOWS" and
        previous.get("origin_signature") == ORIGIN and
        isinstance(old_host, str) and old_host.upper() == expected.upper() and
        prior_checks.get("ASI7700_HEALTH") == "PASS" and
        prior_checks.get("ASI7700_PROCESS_OWNER") == "PASS" and
        prior_checks.get("ASI_STARTUP_CONFIGURATION") == "PASS"
    )
    chronology = bool(old_boot and boot and old_seen and seen and old_boot <= old_seen < boot <= seen and old_boot < boot)
    current_processes = bool(boot and seen and ours and all(
        _utc(p.get("started_utc")) and boot <= _utc(p["started_utc"]) <= seen for p in ours))
    continuity = bool(previous_evidence and chronology and host_ok and startup and owner_ok and
                      asi_healthy is True and current_processes and
                      all(_task_ran_after_boot(t, boot, seen) for t in asi))
    checks.append(check("REBOOT_CONTINUITY", "PASS" if continuity else "UNVERIFIED",
                        reason="Requires chronological observations across a Windows boot, matching task/process ownership, and current ASI health."))
    return checks

def auth_identity_check(metadata, body, expected=EXPECTED_HOST):
    data = body.get("data", body) if isinstance(body, dict) else None
    host = data.get("hostname") if isinstance(data, dict) else None
    good = (metadata.get("http_status") == 200 and not metadata.get("error") and
            isinstance(body, dict) and body.get("ok") is True and
            isinstance(data, dict) and isinstance(host, str) and
            host.upper() == expected.upper() and data.get("origin_signature") == ORIGIN)
    return check("BRIDGE_CURRENT_KEY", "PASS" if good else "FAIL", **metadata)

def audit_files(root, manifest):
    entries = manifest.get("files", []) if isinstance(manifest, dict) else []
    if not isinstance(entries, list) or not entries:
        return check("SOURCE_PACKAGE", "FAIL", reason="EMPTY_MANIFEST", expected=0)
    seen, missing, mismatched = set(), [], []
    base = Path(root).resolve()
    for item in entries:
        if not isinstance(item, dict):
            mismatched.append("<invalid-entry>")
            continue
        rel = item.get("path", "")
        digest = item.get("sha256")
        size = item.get("bytes")
        if (not isinstance(rel, str) or not rel or rel in seen or "\\" in rel or
                ntpath.splitdrive(rel)[0] or ":" in rel or Path(rel).is_absolute() or
                any(part in {"", ".", ".."} for part in rel.split("/")) or
                type(size) is not int or size <= 0 or not isinstance(digest, str) or
                re.fullmatch(r"[0-9a-f]{64}", digest) is None):
            mismatched.append(rel if isinstance(rel, str) else "<invalid-path>")
            continue
        seen.add(rel)
        f = (base / rel).resolve()
        if not f.is_relative_to(base):
            mismatched.append(rel)
        elif not f.is_file():
            missing.append(rel)
        else:
            raw = f.read_bytes()
            if not raw or len(raw) != item.get("bytes") or hashlib.sha256(raw).hexdigest() != item.get("sha256"):
                mismatched.append(rel)
    return check("SOURCE_PACKAGE", "PASS" if not missing and not mismatched else "FAIL",
                 expected=len(entries), matched=len(entries)-len(missing)-len(mismatched),
                 missing=missing, mismatch=mismatched, coverage_percent=round(100*(len(entries)-len(missing)-len(mismatched))/len(entries), 2))

def _d_absolute(value):
    value = str(value)
    drive, tail = ntpath.splitdrive(value)
    if drive.upper() != "D:" or not ntpath.isabs(value) or ":" in tail:
        raise ValueError("RECEIPTS_REQUIRE_ABSOLUTE_D_DRIVE")
    return value

def _resolved_d(path):
    resolved = path.resolve(strict=True)
    _d_absolute(resolved)
    return resolved

def write_receipt(path, receipt):
    if os.name != "nt" or platform.node().upper() != EXPECTED_HOST:
        raise ValueError("RECEIPTS_REQUIRE_DL580_D_DRIVE")
    target = Path(_d_absolute(path))
    ancestor = target.parent
    while not ancestor.exists():
        parent = ancestor.parent
        if parent == ancestor:
            raise ValueError("D_DRIVE_ANCESTOR_UNAVAILABLE")
        ancestor = parent
    _resolved_d(ancestor)
    target.parent.mkdir(parents=True, exist_ok=True)
    parent = _resolved_d(target.parent)
    target = parent / target.name
    payload = (json.dumps(receipt, ensure_ascii=False, indent=2) + "\n").encode("utf-8")
    fd = os.open(target, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    with os.fdopen(fd, "wb") as handle:
        handle.write(payload)
        handle.flush()
        os.fsync(handle.fileno())
    raw = target.read_bytes()
    if raw != payload:
        raise OSError("RECEIPT_READBACK_MISMATCH")
    return {"file": str(target), "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()}

def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=str(Path(__file__).resolve().parents[1]))
    parser.add_argument("--manifest", default="deploy/dl580/recovery/MRL_LocalAI_Recovery_Manifest_v1.json")
    parser.add_argument("--expected-host", default=EXPECTED_HOST)
    parser.add_argument("--previous-receipt")
    parser.add_argument("--out")
    parser.add_argument("--stdout", action="store_true")
    args = parser.parse_args(argv)
    if os.name != "nt" or platform.node().upper() != EXPECTED_HOST or args.expected_host.upper() != EXPECTED_HOST:
        print(json.dumps({"origin_signature": ORIGIN, "status": "BLOCKED", "reason": "EXPECTED_DL580_WINDOWS_HOST", "observed_host": platform.node(), "platform": platform.system()}))
        return 2
    if not args.out and not args.stdout:
        args.out = "D:\\MRL_Mother\\EvidenceChain\\_reports\\MRL_LocalAI_Recovery\\" + dt.datetime.now(dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ_") + uuid.uuid4().hex + ".json"
    receipt = {"origin_signature": ORIGIN, "record_mode": "APPEND_ONLY", "schema": "MRL_LocalAI_Recovery_Acceptance_v1",
               "observed_at_utc": now(), "execution_environment": "DL580_WINDOWS", "checks": []}
    try:
        root = Path(args.repo_root).resolve()
        manifest_path = (root / args.manifest).resolve()
        if not manifest_path.is_relative_to(root):
            raise ValueError("MANIFEST_OUTSIDE_PACKAGE")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8-sig"))
        receipt["checks"].append(audit_files(root, manifest))
    except Exception as error:
        receipt["checks"].append(check("SOURCE_PACKAGE", "FAIL", reason=type(error).__name__))
    ps = Path(os.environ.get("SystemRoot", "C:\\Windows")) / "System32/WindowsPowerShell/v1.0/powershell.exe"
    meta = None
    previous = None
    try:
        import base64
        command = base64.b64encode(PS_METADATA.encode("utf-16-le")).decode("ascii")
        run = subprocess.run([str(ps), "-NoProfile", "-NonInteractive", "-EncodedCommand", command],
                             capture_output=True, timeout=35, check=True)
        meta = json.loads(run.stdout.decode("utf-8-sig"))
        if not isinstance(meta, dict):
            raise ValueError("HOST_METADATA_OBJECT_REQUIRED")
        receipt["host_metadata"] = meta
        if args.previous_receipt:
            previous_path = _resolved_d(Path(_d_absolute(args.previous_receipt)))
            previous = json.loads(previous_path.read_text(encoding="utf-8-sig"))
    except Exception as error:
        receipt["checks"].append(check("HOST_METADATA", "UNVERIFIED", reason=type(error).__name__))
    asi_healthy = False
    for kind, url in [("ASI7700", "http://127.0.0.1:7700/health"), ("BRIDGE", "http://127.0.0.1:7800/health")]:
        metadata, body = probe(url)
        health = health_check(kind, metadata, body)
        receipt["checks"].append(health)
        if kind == "ASI7700":
            asi_healthy = health["status"] == "PASS"
    if isinstance(meta, dict):
        receipt["checks"].extend(classify_host(meta, args.expected_host, previous, asi_healthy=asi_healthy, observed_at=now()))
    current_key = os.environ.get("MRL_BRIDGE_API_KEY", "")
    retired_key = os.environ.get("MRL_BRIDGE_RETIRED_API_KEY", "")
    url = "http://127.0.0.1:7800/MRL_sysinfo"
    anonymous, _ = probe(url)
    receipt["checks"].append(check("BRIDGE_ANONYMOUS_DENIED", "PASS" if anonymous.get("http_status") in (401, 403) else "FAIL", **anonymous))
    if current_key:
        auth, body = probe(url, current_key)
        receipt["checks"].append(auth_identity_check(auth, body, args.expected_host))
    else:
        receipt["checks"].append(check("BRIDGE_CURRENT_KEY", "UNVERIFIED", reason="MRL_BRIDGE_API_KEY_UNAVAILABLE"))
    if retired_key:
        old, _ = probe(url, retired_key)
        receipt["checks"].append(check("BRIDGE_RETIRED_KEY_DENIED", "PASS" if old.get("http_status") in (401,403) else "FAIL", **old))
    else:
        receipt["checks"].append(check("BRIDGE_RETIRED_KEY_DENIED", "UNVERIFIED", reason="NO_RETIRED_CREDENTIAL_SUPPLIED"))
    receipt["checks"].extend([
        check("GLOBAL_RETIRED_CREDENTIAL_RESIDUE", "UNVERIFIED", reason="Not inferred from one authenticated request."),
        check("OAUTH_REAL_SESSION", "UNVERIFIED", reason="Requires actual authenticated browser session evidence."),
    ])
    receipt["pass"] = sum(c["status"] == "PASS" for c in receipt["checks"])
    receipt["fail"] = sum(c["status"] == "FAIL" for c in receipt["checks"])
    receipt["unverified"] = sum(c["status"] == "UNVERIFIED" for c in receipt["checks"])
    receipt["status"] = "PASS" if receipt["fail"] == 0 and receipt["unverified"] == 0 else "INCOMPLETE"
    if args.out:
        try:
            artifact = write_receipt(args.out, receipt)
        except Exception as error:
            print(json.dumps({"status": "FAIL", "reason": type(error).__name__, "check": "RECEIPT_WRITE"}))
            return 1
        print(json.dumps({"origin_signature": ORIGIN, "status": receipt["status"], "pass": receipt["pass"], "fail": receipt["fail"], "unverified": receipt["unverified"], "receipt": artifact}))
    else:
        print(json.dumps(receipt, ensure_ascii=False))
    return 0 if receipt["status"] == "PASS" else 2

if __name__ == "__main__":
    sys.exit(main())
