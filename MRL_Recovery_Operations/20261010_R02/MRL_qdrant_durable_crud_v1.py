#!/usr/bin/env python3
"""Read/write/delete one synthetic collection in the verified durable local Qdrant.
origin_signature: MrLiouWord. Never starts, stops, restarts or kills a service.
Runtime source, credentials and receipts stay on the fixed DL580 D: host.
"""
import argparse
import ctypes as C
import hashlib
import json
import os
from pathlib import Path
import platform
import re
import secrets
import sys
import time
import types
import urllib.error
import urllib.request
import uuid

ORIGIN = "MrLiouWord"
HOST = "WIN-PBVUI7VK2A6"
PYTHON = r"D:\MrlToolchain\python\python.exe"
SERVICE_FILE = "MRL_qdrant_local_service_v1.py"
SERVICE_BYTES = 36865
SERVICE_SHA256 = "5964dbe32fcb3cad9672648aff5e6e6b40a8bfa5a7472c68da0834eeb155be4f"
SERVICE_GIT_BLOB = "b6a2c13b45345a58caeaa55afe048fcf36fd734f"
BASE = "http://127.0.0.1:6333"
INSTANCE_RE = re.compile(r"D:\\MRL_Mother\\QdrantLocal\\[0-9a-f]{32}\Z")
ROUTE_RE = re.compile(r"/collections/mrl_durable_[0-9a-f]{32}(?:/points)?(?:\?(?:wait=true&)?timeout=10)?\Z")
VECTOR = [0.25, 0.5, 0.75, 1.0]

class Hold(Exception):
    pass

def require(condition, code):
    if not condition:
        raise Hold(code)

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def valid_instance(value):
    return isinstance(value, str) and bool(INSTANCE_RE.fullmatch(value))

def load_service(instance):
    require(valid_instance(instance), "instance_boundary_invalid")
    p = Path(instance) / "runtime" / SERVICE_FILE
    with open(p, "rb") as f:
        raw = f.read(SERVICE_BYTES + 1)
    require(len(raw) == SERVICE_BYTES and sha(raw) == SERVICE_SHA256, "service_source_hash_mismatch")
    module = types.ModuleType("mrl_qdrant_durable_pinned_service")
    module.__file__, module.__package__ = str(p), ""
    exec(compile(raw, str(p), "exec"), module.__dict__)
    return module

def error_code(error):
    value = str(error)
    if isinstance(error, Hold) or type(error).__name__ in ("Hold", "ProbeFailure"):
        if re.fullmatch(r"[a-z][a-z0-9_]{0,95}", value):
            return value
    return "exception_" + type(error).__name__

def task_signature(task):
    names = ("task_name", "definition_verified", "enabled", "state", "principal_system",
             "run_level", "boot_delay_seconds", "multiple_instances", "restart_count",
             "restart_interval_seconds", "execution_time_limit", "source_action_verified")
    return {k: task.get(k) for k in names}

def exercise(request, guard):
    """An acknowledged create is the only transition granting delete ownership."""
    collection = "mrl_durable_" + uuid.uuid4().hex
    point_id, nonce = str(uuid.uuid4()), uuid.uuid4().hex
    route = "/collections/" + collection
    result = {"status": "HOLD", "checks": {}, "http": [], "errors": [],
              "synthetic_collection_sha256": sha(collection.encode("ascii")),
              "creation_acknowledged": False, "creation_outcome_uncertain": False,
              "delete_attempted": False, "cleanup_confirmed": False, "ownership_guard_failed": False}
    owned = False

    def guard_once():
        require(not result["ownership_guard_failed"], "ownership_guard_failure_latched")
        try:
            guard()
        except Exception:
            result["ownership_guard_failed"] = True
            raise

    def call(operation, method, suffix="", body=None):
        guard_once()
        status, parsed = request(method, route + suffix, body)
        result["http"].append({"operation": operation, "method": method, "status": status})
        guard_once()
        return status, parsed

    def ok_true(status, body):
        return status == 200 and isinstance(body, dict) and body.get("status") == "ok" and body.get("result") is True

    def delete_owned():
        require(owned and result["creation_acknowledged"], "delete_requires_acknowledged_own_create")
        # Mark before the request; an ambiguous response must not trigger a second delete.
        result["delete_attempted"] = True
        status, body = call("delete_own_collection", "DELETE", "?timeout=10")
        require(ok_true(status, body), "own_collection_delete_failed")
        result["checks"]["delete_acknowledged"] = True
        status, ignored = call("confirm_own_collection_absent", "GET")
        require(status == 404, "own_collection_absence_not_confirmed")
        result["checks"]["final_404"] = True
        result["cleanup_confirmed"] = True

    try:
        status, ignored = call("confirm_fresh_name_absent", "GET")
        require(status == 404, "fresh_collection_name_not_404")
        result["checks"]["initial_404"] = True
        result["creation_outcome_uncertain"] = True
        status, body = call("create_synthetic_collection", "PUT", "?timeout=10",
                            {"vectors": {"size": 4, "distance": "Dot"}})
        require(ok_true(status, body), "synthetic_collection_create_not_acknowledged")
        owned = True
        result["creation_acknowledged"] = True
        result["creation_outcome_uncertain"] = False
        result["checks"]["create_acknowledged"] = True
        point = {"id": point_id, "vector": VECTOR,
                 "payload": {"origin_signature": ORIGIN, "probe_nonce": nonce}}
        status, body = call("write_synthetic_point", "PUT", "/points?wait=true&timeout=10",
                            {"points": [point]})
        require(status == 200 and isinstance(body, dict) and body.get("status") == "ok"
                and isinstance(body.get("result"), dict)
                and body["result"].get("status") == "completed", "synthetic_point_write_failed")
        result["checks"]["point_write_completed"] = True
        status, body = call("read_synthetic_point", "POST", "/points?timeout=10",
                            {"ids": [point_id], "with_payload": True, "with_vector": True})
        rows = body.get("result") if isinstance(body, dict) else None
        require(status == 200 and isinstance(body, dict) and body.get("status") == "ok"
                and isinstance(rows, list) and len(rows) == 1 and isinstance(rows[0], dict)
                and rows[0].get("id") == point_id and rows[0].get("payload") == point["payload"]
                and isinstance(rows[0].get("vector"), list)
                and all(type(v) in (int, float) for v in rows[0]["vector"])
                and rows[0]["vector"] == VECTOR, "synthetic_point_exact_readback_failed")
        result["checks"]["point_exact_readback"] = True
        delete_owned()
        result["status"] = "SYNTHETIC_CRUD_PASS"
    except Exception as e:
        result["errors"].append(error_code(e))
    finally:
        if owned and not result["delete_attempted"] and not result["ownership_guard_failed"]:
            try:
                delete_owned()
            except Exception as e:
                result["errors"].append(error_code(e))
    return result

def http_client(service, support, key):
    deadline = time.monotonic() + 90
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}), support.NoRedirect())
    def request(method, route, body=None):
        require(method in ("GET", "PUT", "POST", "DELETE") and bool(ROUTE_RE.fullmatch(route)),
                "synthetic_route_not_allowlisted")
        remaining = deadline - time.monotonic()
        require(remaining > 0, "crud_deadline_exceeded")
        data = None if body is None else json.dumps(body, separators=(",", ":")).encode("utf-8")
        headers = {"api-key": key, "User-Agent": "MRL-Qdrant-Durable-CRUD/1.0"}
        if data is not None:
            headers["Content-Type"] = "application/json"
        req = urllib.request.Request(BASE + route, data=data, headers=headers, method=method)
        try:
            response = opener.open(req, timeout=min(12, remaining))
        except urllib.error.HTTPError as e:
            response = e
        with response:
            raw = response.read(256 * 1024 + 1)
            status = int(response.code)
        require(len(raw) <= 256 * 1024, "bounded_http_response_required")
        if status >= 400 or 300 <= status < 400:
            return status, None
        try:
            return status, service.strict_json(raw)
        except Exception:
            raise Hold("http_json_invalid") from None
    return request

def run(instance):
    require(os.name == "nt" and platform.node().upper() == HOST, "expected_windows_host_required")
    require(valid_instance(instance), "instance_boundary_invalid")
    service = load_service(instance)
    support, win = service.bootstrap(types.SimpleNamespace(command="verify", instance=instance))
    client_source_hash, client_source_bytes = service.digest(win.path(Path(__file__)))
    instance, manifest, key = service.validate_instance(support, win, instance)
    receipt = {"schema": "MRL_Qdrant_Durable_CRUD_Receipt_v1", "origin_signature": ORIGIN,
               "observed_host": HOST, "instance_directory": str(instance), "endpoint": BASE,
               "started_at_utc": service.utc(), "status": "HOLD", "checks": {}, "errors": [],
               "service_source_sha256": SERVICE_SHA256, "service_git_blob": SERVICE_GIT_BLOB,
               "client_source_sha256": client_source_hash, "client_source_bytes": client_source_bytes,
               "secret_exported": False, "key_hash_exported": False,
               "point_data_exported": False, "existing_collection_names_exported": False,
               "service_control_performed": False, "restart_test": "NOT_RUN",
               "reboot_test": "NOT_RUN", "application_integration": "NOT_ASSERTED"}
    handles = []
    identity = service.ProcessIdentity(win)
    try:
        wrapper = instance / "runtime" / service.TASK_NAME
        def inspect_task():
            task = service.ps_call(win, wrapper, "Inspect", instance)["task"]
            require(task.get("enabled") is True and task.get("state") == 4
                    and task.get("definition_verified") is True, "exact_task_not_running")
            return task_signature(task)
        task_before = inspect_task()
        ready = service.latest_ready(win, instance)
        child, supervisor = ready["child"], ready["supervisor"]
        exe = instance.joinpath(*service.PurePosixPath(manifest["executable_relative_path"]).parts)
        require(service.path_equal(child.get("image", ""), exe)
                and child.get("image_sha256") == manifest["source_provenance"]["executable_sha256"]
                and child.get("job_kill_on_close_assigned") is True, "ready_child_identity_invalid")
        handles.append(identity.opened(supervisor.get("pid"), service.PYTHON, supervisor.get("created_filetime")))
        handles.append(identity.opened(child.get("pid"), exe, child.get("created_filetime")))
        win.k.GetExitCodeProcess.argtypes = [C.c_void_p, C.POINTER(C.c_uint32)]
        win.k.GetExitCodeProcess.restype = C.c_int

        def guard():
            for handle, expected_created in zip(handles, (supervisor["created_filetime"], child["created_filetime"])):
                code = C.c_uint32()
                require(win.k.GetExitCodeProcess(handle, C.byref(code)) and code.value == 259,
                        "held_service_process_not_active")
                require(identity.created(handle) == expected_created, "held_process_creation_changed")
            require(support.listener_contract(win.listeners(), child["pid"]),
                    "held_process_listener_boundary_changed")

        guard()
        health_before = service.probe(support, win, child["pid"], key)
        guard()
        receipt["checks"].update(private_acl_and_source=True, exact_task_running=True,
                                 child_and_supervisor_identity=True, only_owned_loopback=True,
                                 authenticated_api=True, missing_key_denied=True)
        receipt["processes"] = {"child_pid": child["pid"], "supervisor_pid": supervisor["pid"],
                                "child_created_filetime": child["created_filetime"],
                                "supervisor_created_filetime": supervisor["created_filetime"],
                                "executable_sha256": child["image_sha256"]}
        outcome = exercise(http_client(service, support, key), guard)
        receipt["crud"] = outcome
        guard()
        after_instance, after_manifest, after_key = service.validate_instance(support, win, str(instance))
        require(after_manifest == manifest and service.path_equal(after_instance, instance),
                "instance_source_changed_after_crud")
        require(secrets.compare_digest(key, after_key), "private_key_changed_after_crud")
        require(inspect_task() == task_before, "task_changed_after_crud")
        health_after = service.probe(support, win, child["pid"], key)
        guard()
        receipt["checks"].update(source_stable_after=True, task_stable_after=True,
                                 held_processes_stable_after=True, auth_stable_after=True)
        receipt["http_auth"] = {"before": health_before["protected_api_status"],
                                "after": health_after["protected_api_status"],
                                "missing_key_before": health_before["missing_key_status"],
                                "missing_key_after": health_after["missing_key_status"]}
        if outcome["status"] == "SYNTHETIC_CRUD_PASS" and outcome["cleanup_confirmed"]:
            receipt["status"] = "DURABLE_SYNTHETIC_CRUD_PASS"
    except Exception as e:
        receipt["errors"].append(error_code(e))
    finally:
        for handle in reversed(handles):
            win.k.CloseHandle(handle)  # query handles only; never terminate or control a service
    receipt["ended_at_utc"] = service.utc()
    path = instance / "state" / ("durable_crud_" + uuid.uuid4().hex + ".json")
    service.write_new(win, path, service.encode(receipt))
    file_hash, size = service.digest(path)
    return {"status": receipt["status"], "origin_signature": ORIGIN,
            "instance_directory": str(instance), "receipt_path": str(path),
            "receipt_sha256": file_hash, "receipt_bytes": size, "checks": receipt["checks"],
            "crud_checks": receipt.get("crud", {}).get("checks", {}),
            "http": receipt.get("crud", {}).get("http", []),
            "errors": receipt["errors"] + receipt.get("crud", {}).get("errors", []),
            "secret_exported": False, "key_hash_exported": False, "service_control_performed": False}

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--instance", required=True)
    args = parser.parse_args()
    try:
        result = run(args.instance)
    except Exception as e:
        result = {"status": "HOLD", "origin_signature": ORIGIN, "error_code": error_code(e),
                  "secret_exported": False, "key_hash_exported": False,
                  "service_control_performed": False}
    print(json.dumps(result, sort_keys=True))
    return 0 if result["status"] == "DURABLE_SYNTHETIC_CRUD_PASS" else 2

if __name__ == "__main__":
    raise SystemExit(main())
