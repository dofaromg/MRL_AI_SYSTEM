"""Offline regression tests for MRL LocalAI recovery acceptance.
No DL580 access, network requests, real subprocesses, or filesystem writes.
"""
from __future__ import annotations
import copy
import hashlib
import importlib.util
import io
import json
import ntpath
from pathlib import Path, PurePosixPath, PureWindowsPath
import types
import unittest
from unittest import mock
import urllib.error

_SPEC = importlib.util.spec_from_file_location(
    "_mrl_recovery_acceptance_test_target",
    Path(__file__).resolve().parents[1] / "scripts/MRL_localai_recovery_acceptance_v1.py",
)
MRL = importlib.util.module_from_spec(_SPEC)
_SPEC.loader.exec_module(MRL)


def statuses(checks):
    return {item["check"]: item["status"] for item in checks}


def metadata():
    return {
        "host": MRL.EXPECTED_HOST,
        "windows_boot_utc": "2026-10-10T10:00:00Z",
        "owners_7700": [{
            "pid": 77, "executable_matches": True, "entry_matches": True,
            "started_utc": "2026-10-10T10:00:30Z",
        }],
        "tasks": [{
            "name": "MRL_ASI_Engine", "enabled": True, "boot_trigger": True,
            "state": "Running", "action_count": 1,
            "action_absolute": [True], "action_node_matches": [True],
            "action_entry_matches": [True], "last_result": 267009,
            "last_run_utc": "2026-10-10T10:00:20Z", "last_run_after_boot": True,
        }, {"name": "MRL_Watchdog", "enabled": True}],
    }


def previous_receipt():
    return {
        "schema": "MRL_LocalAI_Recovery_Acceptance_v1",
        "execution_environment": "DL580_WINDOWS",
        "origin_signature": MRL.ORIGIN,
        "observed_at_utc": "2026-10-09T12:00:00Z",
        "host_metadata": {
            "host": MRL.EXPECTED_HOST,
            "windows_boot_utc": "2026-10-09T10:00:00Z",
        },
        "checks": [{"check": name, "status": "PASS"} for name in (
            "ASI7700_HEALTH", "ASI7700_PROCESS_OWNER", "ASI_STARTUP_CONFIGURATION",
        )],
    }


class HealthAndAuthTests(unittest.TestCase):
    def test_asi_exact_contract_and_none_bodies(self):
        good = {"status": "PASS", "origin": MRL.ORIGIN}
        self.assertEqual(MRL.health_check("ASI7700", {"http_status": 200}, good)["status"], "PASS")
        for body in (None, [], "PASS", {}, {"status": "PASS", "origin": "other"}):
            with self.subTest(body=body):
                self.assertEqual(MRL.health_check("ASI7700", {"http_status": 200}, body)["status"], "FAIL")
        self.assertEqual(MRL.health_check("ASI7700", {"http_status": 200, "error": "INVALID_JSON"}, good)["status"], "FAIL")

    def test_bridge_requires_all_component_booleans_and_origin(self):
        good = {"service": "MRL_Bridge_API", "origin_signature": MRL.ORIGIN,
                "api": True, "pg": True, "redis": True, "version": "3.1.0"}
        self.assertEqual(MRL.health_check("BRIDGE", {"http_status": 200}, good)["status"], "PASS")
        for key, value in (("api", 1), ("pg", False), ("redis", None),
                           ("origin_signature", "wrong"), ("service", "other")):
            with self.subTest(key=key):
                body = dict(good, **{key: value})
                self.assertEqual(MRL.health_check("BRIDGE", {"http_status": 200}, body)["status"], "FAIL")
        with self.assertRaises(ValueError):
            MRL.health_check("UNKNOWN", {"http_status": 200}, good)

    def test_auth_identity_flat_or_nested(self):
        identity = {"hostname": MRL.EXPECTED_HOST.lower(), "origin_signature": MRL.ORIGIN}
        for body in (dict(identity, ok=True), {"ok": True, "data": identity}):
            self.assertEqual(MRL.auth_identity_check({"http_status": 200}, body)["status"], "PASS")

    def test_auth_identity_malformed_fails_without_exception(self):
        for body in (None, [], "", {}, {"ok": True, "data": None},
                     {"ok": True, "data": []}, {"ok": True, "hostname": None},
                     {"ok": True, "hostname": 1},
                     {"ok": False, "hostname": MRL.EXPECTED_HOST, "origin_signature": MRL.ORIGIN},
                     {"ok": True, "hostname": "OTHER", "origin_signature": MRL.ORIGIN}):
            with self.subTest(body=body):
                self.assertEqual(MRL.auth_identity_check({"http_status": 200}, body)["status"], "FAIL")
        body = {"ok": True, "hostname": MRL.EXPECTED_HOST, "origin_signature": MRL.ORIGIN}
        for meta in ({"http_status": 401}, {"http_status": 403},
                     {"http_status": None}, {"http_status": 200, "error": "EXPECTED_JSON"}):
            self.assertEqual(MRL.auth_identity_check(meta, body)["status"], "FAIL")

    def test_probe_transport_failure_exposes_only_error_type(self):
        with mock.patch.object(MRL.urllib.request, "build_opener") as build:
            build.return_value.open.side_effect = RuntimeError("DO_NOT_EXPOSE_RESPONSE")
            detail, body = MRL.probe("http://127.0.0.1:7700/health")
        self.assertIsNone(body)
        self.assertEqual(detail["error"], "RuntimeError")
        self.assertNotIn("DO_NOT_EXPOSE_RESPONSE", json.dumps(detail))

    def test_probe_rejects_header_injection_before_open(self):
        with mock.patch.object(MRL.urllib.request, "build_opener") as build:
            detail, body = MRL.probe("http://127.0.0.1:7800/MRL_sysinfo", "test-only\r\nbad")
        build.assert_not_called()
        self.assertIsNone(body)
        self.assertEqual(detail["error"], "INVALID_HEADER")

    def test_loopback_probe_disables_proxy_and_bounds_response(self):
        response = mock.MagicMock()
        response.__enter__.return_value = response
        response.status = 200
        response.headers.get_content_type.return_value = "application/json"
        response.read.return_value = b'{"status":"PASS","origin":"MrLiouWord"}'
        with mock.patch.object(MRL.urllib.request, "build_opener") as build:
            build.return_value.open.return_value = response
            detail, body = MRL.probe("http://127.0.0.1:7700/health")
        handlers = build.call_args.args
        proxies = [h for h in handlers if isinstance(h, MRL.urllib.request.ProxyHandler)]
        self.assertEqual(len(proxies), 1)
        self.assertEqual(proxies[0].proxies, {})
        self.assertTrue(any(isinstance(h, MRL.NoRedirect) for h in handlers))
        request = build.return_value.open.call_args.args[0]
        self.assertEqual(request.get_header("User-agent"), MRL.USER_AGENT)
        response.read.assert_called_once_with(MRL.MAX_BODY + 1)
        self.assertEqual(body["status"], "PASS")
        self.assertNotIn("body", detail)
        self.assertEqual(detail["response_sha256"], hashlib.sha256(response.read.return_value).hexdigest())

    def test_probe_content_and_size_errors(self):
        for raw, content_type, error in (
            (b"x" * (MRL.MAX_BODY + 1), "application/json", "RESPONSE_TOO_LARGE"),
            (b"<html>challenge</html>", "text/html", "EXPECTED_JSON"),
            (b"{", "application/json", "INVALID_JSON"),
        ):
            with self.subTest(error=error):
                response = mock.MagicMock()
                response.__enter__.return_value = response
                response.status = 200
                response.headers.get_content_type.return_value = content_type
                response.read.return_value = raw
                with mock.patch.object(MRL.urllib.request, "build_opener") as build:
                    build.return_value.open.return_value = response
                    detail, body = MRL.probe("http://127.0.0.1:7700/health")
                self.assertIsNone(body)
                self.assertEqual(detail["error"], error)

    def test_redirect_and_http_denial_remain_non_pass(self):
        self.assertIsNone(MRL.NoRedirect().redirect_request(None, None, 302, "", {}, "https://other.invalid"))
        with mock.patch.object(MRL.urllib.request, "build_opener") as build:
            build.return_value.open.side_effect = urllib.error.HTTPError(
                "http://127.0.0.1:7800/MRL_sysinfo", 403, "denied", {}, None)
            detail, body = MRL.probe("http://127.0.0.1:7800/MRL_sysinfo")
        self.assertEqual(detail["http_status"], 403)
        self.assertIsNone(body)


class HostGateTests(unittest.TestCase):
    def run_gate(self, meta=None, previous=None, **kwargs):
        return statuses(MRL.classify_host(
            metadata() if meta is None else meta,
            previous=previous,
            observed_at="2026-10-10T12:00:00Z",
            **kwargs,
        ))

    def test_host_owner_and_startup_need_actual_evidence(self):
        states = self.run_gate()
        for name in ("DL580_HOST", "ASI7700_PROCESS_OWNER", "ASI_STARTUP_CONFIGURATION"):
            self.assertEqual(states[name], "PASS")
        self.assertEqual(states["WATCHDOG_REGISTERED"], "PASS")
        self.assertEqual(states["WATCHDOG_FAULT_RECOVERY"], "UNVERIFIED")
        self.assertEqual(states["REBOOT_CONTINUITY"], "UNVERIFIED")
        for bad in ({}, [], {"host": None}, {"host": MRL.EXPECTED_HOST, "owners_7700": None, "tasks": None}):
            self.assertNotEqual(self.run_gate(bad)["ASI7700_PROCESS_OWNER"], "PASS")

    def test_wrong_host_cannot_pass_host_gate(self):
        meta = metadata()
        meta["host"] = "OTHER_HOST"
        self.assertEqual(self.run_gate(meta)["DL580_HOST"], "FAIL")

    def test_owner_set_does_not_hide_mismatch_or_malformed_item(self):
        for extra in (None, {"executable_matches": False, "entry_matches": True}):
            meta = metadata()
            meta["owners_7700"].append(extra)
            self.assertEqual(self.run_gate(meta)["ASI7700_PROCESS_OWNER"], "FAIL")

    def test_task_state_enum_and_scalar_boolean_support(self):
        for state in (3, "3", "Ready", 4, "4", "Running"):
            with self.subTest(state=state):
                meta = metadata()
                task = meta["tasks"][0]
                task.update(state=state, action_absolute=True, action_node_matches=True,
                            action_entry_matches=True)
                self.assertEqual(self.run_gate(meta)["ASI_STARTUP_CONFIGURATION"], "PASS")
        for state in (0, 1, "Disabled", None):
            meta = metadata()
            meta["tasks"][0]["state"] = state
            self.assertEqual(self.run_gate(meta)["ASI_STARTUP_CONFIGURATION"], "FAIL")

    def test_cross_action_and_nonabsolute_startup_cannot_pass(self):
        meta = metadata()
        meta["tasks"][0].update(
            action_count=2, action_absolute=[True, True],
            action_node_matches=[True, False], action_entry_matches=[False, True])
        self.assertEqual(self.run_gate(meta)["ASI_STARTUP_CONFIGURATION"], "FAIL")
        for field, value in (("action_absolute", [False]), ("action_count", True),
                             ("action_entry_matches", []), ("enabled", False),
                             ("boot_trigger", False)):
            meta = metadata()
            meta["tasks"][0][field] = value
            self.assertEqual(self.run_gate(meta)["ASI_STARTUP_CONFIGURATION"], "FAIL")
        meta = metadata()
        meta["tasks"].append(None)
        self.assertEqual(self.run_gate(meta)["ASI_STARTUP_CONFIGURATION"], "FAIL")

    def test_real_chronology_with_current_health_can_pass_reboot(self):
        self.assertEqual(self.run_gate(previous=previous_receipt(), asi_healthy=True)["REBOOT_CONTINUITY"], "PASS")
        meta = metadata()
        meta["tasks"][0].update(state=3, last_result=0)
        self.assertEqual(self.run_gate(meta, previous_receipt(), asi_healthy=True)["REBOOT_CONTINUITY"], "PASS")

    def test_reboot_needs_current_health(self):
        for health in (False, None, 1):
            self.assertEqual(self.run_gate(previous=previous_receipt(), asi_healthy=health)["REBOOT_CONTINUITY"], "UNVERIFIED")

    def test_equal_or_backwards_boot_is_not_reboot(self):
        for prior_boot in ("2026-10-10T10:00:00+00:00", "2026-10-11T10:00:00Z"):
            old = previous_receipt()
            old["host_metadata"]["windows_boot_utc"] = prior_boot
            self.assertEqual(self.run_gate(previous=old, asi_healthy=True)["REBOOT_CONTINUITY"], "UNVERIFIED")
        old = previous_receipt()
        del old["host_metadata"]["windows_boot_utc"]
        old["host_metadata"]["boot_time"] = "2026-10-09T10:00:00Z"
        self.assertEqual(self.run_gate(previous=old, asi_healthy=True)["REBOOT_CONTINUITY"], "UNVERIFIED")

    def test_previous_receipt_requires_identity_observation_and_passing_evidence(self):
        for field, value in (
            ("schema", "other"), ("origin_signature", "other"),
            ("execution_environment", "LINUX"), ("observed_at_utc", None),
            ("observed_at_utc", "2026-10-10T11:00:00Z"),
            ("observed_at_utc", "2026-10-09T09:00:00Z"), ("checks", []),
            ("host_metadata", None),
        ):
            with self.subTest(field=field, value=value):
                old = previous_receipt()
                old[field] = value
                self.assertEqual(self.run_gate(previous=old, asi_healthy=True)["REBOOT_CONTINUITY"], "UNVERIFIED")

    def test_reboot_needs_process_and_task_observations_after_os_boot(self):
        changes = (
            ("owner", "started_utc", None),
            ("owner", "started_utc", "2026-10-10T09:59:59Z"),
            ("owner", "started_utc", "2026-10-10T12:00:01Z"),
            ("owner", "entry_matches", False),
            ("task", "last_run_utc", None),
            ("task", "last_run_utc", "2026-10-10T09:59:59Z"),
            ("task", "last_run_after_boot", False),
            ("task", "last_result", 1),
            ("task", "state", "Queued"),
        )
        for group, field, value in changes:
            with self.subTest(group=group, field=field):
                meta = metadata()
                target = meta["owners_7700"][0] if group == "owner" else meta["tasks"][0]
                target[field] = value
                self.assertEqual(self.run_gate(meta, previous_receipt(), asi_healthy=True)["REBOOT_CONTINUITY"], "UNVERIFIED")

    def test_off_host_main_blocks_before_any_host_or_network_operation(self):
        with mock.patch.object(MRL.platform, "node", return_value="OFF_HOST"), \
             mock.patch.object(MRL, "probe") as probe, \
             mock.patch.object(MRL.subprocess, "run") as run, \
             mock.patch.object(MRL, "write_receipt") as write, \
             mock.patch("sys.stdout", new_callable=io.StringIO) as output:
            result = MRL.main(["--stdout"])
        self.assertEqual(result, 2)
        self.assertEqual(json.loads(output.getvalue())["status"], "BLOCKED")
        probe.assert_not_called()
        run.assert_not_called()
        write.assert_not_called()


class MemoryPath:
    """Small deterministic filesystem double; never delegates to the real filesystem."""
    files = {}
    directories = set()
    resolutions = {}
    mkdir_calls = []

    def __init__(self, path):
        text = str(path)
        self.path = PureWindowsPath(text) if ntpath.splitdrive(text)[0] else PurePosixPath(text)

    def __str__(self):
        return str(self.path)

    def __fspath__(self):
        return str(self)

    def __eq__(self, other):
        return isinstance(other, MemoryPath) and self.path == other.path

    def __truediv__(self, other):
        return MemoryPath(self.path / str(other))

    @property
    def parent(self):
        return MemoryPath(self.path.parent)

    @property
    def name(self):
        return self.path.name

    def resolve(self, strict=False):
        resolved = MemoryPath(self.resolutions.get(str(self), str(self)))
        if strict and not resolved.exists():
            raise FileNotFoundError(str(resolved))
        return resolved

    def exists(self):
        return str(self) in self.files or str(self) in self.directories

    def is_file(self):
        return str(self) in self.files

    def is_absolute(self):
        return self.path.is_absolute()

    def is_relative_to(self, other):
        return self.path.is_relative_to(other.path)

    def read_bytes(self):
        return self.files[str(self)]

    def mkdir(self, parents=False, exist_ok=False):
        self.mkdir_calls.append(str(self))
        self.directories.add(str(self))


class FilesystemSafetyTests(unittest.TestCase):
    def setUp(self):
        MemoryPath.files = {"/package/core.js": b"actual-source\n"}
        MemoryPath.directories = {"/package", "D:\\", "D:\\evidence", "C:\\outside"}
        MemoryPath.resolutions = {}
        MemoryPath.mkdir_calls = []
        self.entry = {"path": "core.js", "bytes": len(MemoryPath.files["/package/core.js"]),
                      "sha256": hashlib.sha256(MemoryPath.files["/package/core.js"]).hexdigest()}
        self.path_patch = mock.patch.object(MRL, "Path", MemoryPath)
        self.path_patch.start()
        self.addCleanup(self.path_patch.stop)

    def audit(self, entries):
        return MRL.audit_files("/package", {"files": entries})

    def test_manifest_hash_and_size_actual_bytes(self):
        result = self.audit([self.entry])
        self.assertEqual((result["status"], result["matched"], result["coverage_percent"]), ("PASS", 1, 100.0))
        for key, value in (("sha256", "0" * 64), ("bytes", 1)):
            entry = dict(self.entry, **{key: value})
            self.assertEqual(self.audit([entry])["status"], "FAIL")
        MemoryPath.files["/package/core.js"] = b""
        self.assertEqual(self.audit([self.entry])["status"], "FAIL")

    def test_manifest_missing_duplicate_and_malformed_entries(self):
        missing = dict(self.entry, path="missing.js")
        self.assertEqual(self.audit([missing])["missing"], ["missing.js"])
        self.assertEqual(self.audit([self.entry, self.entry])["status"], "FAIL")
        for manifest in (None, [], {}, {"files": {}}, {"files": []}):
            self.assertEqual(MRL.audit_files("/package", manifest)["status"], "FAIL")
        for entry in (None, [], {}, dict(self.entry, bytes=True),
                      dict(self.entry, bytes=0), dict(self.entry, sha256=None),
                      dict(self.entry, sha256="A" * 64)):
            self.assertEqual(self.audit([entry])["status"], "FAIL")

    def test_manifest_rejects_absolute_drive_relative_ads_and_traversal(self):
        for rel in ("", "/outside", "../outside", "a/../core.js", "./core.js",
                    "a//core.js", "D:core.js", "D:/core.js", "core.js:ads", "a\\core.js", 7):
            with self.subTest(rel=rel):
                self.assertEqual(self.audit([dict(self.entry, path=rel)])["status"], "FAIL")
        MemoryPath.resolutions["/package/core.js"] = "C:\\outside"
        self.assertEqual(self.audit([self.entry])["status"], "FAIL")

    def test_d_absolute_rejects_c_unc_drive_relative_and_ads(self):
        for path in ("C:\\out.json", "\\\\host\\share\\out.json", "D:out.json",
                     "out.json", "\\out.json", "D:\\out.json:ads"):
            with self.subTest(path=path), self.assertRaises(ValueError):
                MRL._d_absolute(path)
        self.assertEqual(MRL._d_absolute("D:\\evidence\\out.json"), "D:\\evidence\\out.json")

    def test_receipt_refuses_wrong_host(self):
        with mock.patch.object(MRL.os, "name", "nt"), \
             mock.patch.object(MRL.platform, "node", return_value="OTHER"), \
             mock.patch.object(MRL.os, "open") as open_file:
            with self.assertRaises(ValueError):
                MRL.write_receipt("D:\\evidence\\out.json", {})
        open_file.assert_not_called()
        self.assertEqual(MemoryPath.mkdir_calls, [])

    def test_junction_to_c_rejected_before_mkdir(self):
        MemoryPath.resolutions["D:\\evidence"] = "C:\\outside"
        with mock.patch.object(MRL.os, "name", "nt"), \
             mock.patch.object(MRL.platform, "node", return_value=MRL.EXPECTED_HOST), \
             mock.patch.object(MRL.os, "open") as open_file:
            with self.assertRaises(ValueError):
                MRL.write_receipt("D:\\evidence\\new\\out.json", {})
        open_file.assert_not_called()
        self.assertEqual(MemoryPath.mkdir_calls, [])

    def test_receipt_exclusive_write_fsync_readback_and_no_overwrite(self):
        receipt = {"origin_signature": MRL.ORIGIN, "status": "INCOMPLETE"}
        saved = {}
        class Handle(io.BytesIO):
            def fileno(self):
                return 123
            def __exit__(self, *args):
                MemoryPath.files[saved["path"]] = self.getvalue()
                self.close()
                return False
        def fake_open(path, flags, mode):
            saved.update(path=str(path), flags=flags, mode=mode)
            if str(path) in MemoryPath.files and flags & MRL.os.O_EXCL:
                raise FileExistsError(str(path))
            return 123
        with mock.patch.object(MRL.os, "name", "nt"), \
             mock.patch.object(MRL.platform, "node", return_value=MRL.EXPECTED_HOST), \
             mock.patch.object(MRL.os, "open", side_effect=fake_open), \
             mock.patch.object(MRL.os, "fdopen", side_effect=lambda *_: Handle()), \
             mock.patch.object(MRL.os, "fsync") as fsync:
            result = MRL.write_receipt("D:\\evidence\\out.json", receipt)
            raw = MemoryPath.files["D:\\evidence\\out.json"]
            self.assertEqual(json.loads(raw), receipt)
            self.assertEqual(result["bytes"], len(raw))
            self.assertEqual(result["sha256"], hashlib.sha256(raw).hexdigest())
            self.assertTrue(saved["flags"] & MRL.os.O_CREAT)
            self.assertTrue(saved["flags"] & MRL.os.O_EXCL)
            fsync.assert_called_once_with(123)
            with self.assertRaises(FileExistsError):
                MRL.write_receipt("D:\\evidence\\out.json", {"changed": True})
            self.assertEqual(MemoryPath.files["D:\\evidence\\out.json"], raw)

    def test_receipt_readback_mismatch_fails(self):
        class Handle(io.BytesIO):
            def fileno(self):
                return 123
            def __exit__(self, *args):
                return False
        MemoryPath.files["D:\\evidence\\out.json"] = b"mismatched"
        with mock.patch.object(MRL.os, "name", "nt"), \
             mock.patch.object(MRL.platform, "node", return_value=MRL.EXPECTED_HOST), \
             mock.patch.object(MRL.os, "open", return_value=123), \
             mock.patch.object(MRL.os, "fdopen", return_value=Handle()), \
             mock.patch.object(MRL.os, "fsync"):
            with self.assertRaisesRegex(OSError, "READBACK_MISMATCH"):
                MRL.write_receipt("D:\\evidence\\out.json", {})


if __name__ == "__main__":
    unittest.main()
