"""Cloud-only fixture tests; no DL580, filesystem writes, subprocesses or live network."""
import importlib.util
import importlib.machinery
import io
import json
from pathlib import Path
import types
import unittest
from unittest import mock
import xml.etree.ElementTree as ET

_SOURCE = Path(__file__).resolve().with_name("MRL_qdrant_local_service_v1.py")
if "SERVICE_UNDER_TEST" not in globals():
    spec = importlib.util.spec_from_file_location("mrl_qdrant_service_tested", _SOURCE)
    svc = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(svc)
else:
    svc = SERVICE_UNDER_TEST

INSTANCE = r"D:\MRL_Mother\QdrantLocal\0123456789abcdef0123456789abcdef"
KEY = "7" * 64
NS = {"t": "http://schemas.microsoft.com/windows/2004/02/mit/task"}

def manifest():
    records = [
        {"path": "runtime/" + svc.SELF_NAME, "bytes": 1, "sha256": "1" * 64},
        {"path": "runtime/" + svc.SUPPORT_NAME, "bytes": svc.SUPPORT_BYTES, "sha256": svc.SUPPORT_SHA256},
        {"path": "runtime/" + svc.TASK_NAME, "bytes": svc.TASK_BYTES, "sha256": svc.TASK_SHA256},
        {"path": "config.yaml", "bytes": 1, "sha256": "2" * 64},
        {"path": "task.xml", "bytes": 1, "sha256": "3" * 64},
        {"path": "bin/qdrant.exe", "bytes": 1, "sha256": "4" * 64},
    ]
    return {"schema": "MRL_Qdrant_Local_Instance_v1", "origin_signature": svc.ORIGIN,
            "instance_id": "0123456789abcdef0123456789abcdef", "instance_directory": INSTANCE,
            "expected_host": svc.HOST, "task_name": "MRL_Qdrant_Local_0123456789abcdef0123456789abcdef",
            "version": "1.19.2", "endpoint": "http://127.0.0.1:6333",
            "python_path": svc.PYTHON, "python_sha256": svc.PYTHON_SHA256, "python_bytes": svc.PYTHON_BYTES,
            "api_key_relative_path": "private/api-key.txt", "restart_count": 3,
            "restart_interval_seconds": 60, "files": records}

class BoundaryTests(unittest.TestCase):
    def test_exact_instance_accepted(self):
        self.assertTrue(svc.valid_instance(INSTANCE))
    def test_other_roots_and_traversal_rejected(self):
        for p in (INSTANCE.replace("D:", "C:"), INSTANCE + r"\..\other",
                  r"\\server\D$\MRL_Mother\QdrantLocal\0123456789abcdef0123456789abcdef",
                  INSTANCE.replace("QdrantLocal", "QdrantProbe"), INSTANCE + r"\extra"):
            with self.subTest(path=p):
                self.assertFalse(svc.valid_instance(p))
    def test_support_executes_the_one_verified_buffer_without_cache_loader(self):
        raw = b"EXECUTED_MARKER = 'verified-buffer'\n"
        stream = io.BytesIO(raw)
        original_read = stream.read
        reads = []
        def bounded_read(n):
            reads.append(n)
            return original_read(n)
        stream.read = bounded_read
        with mock.patch.object(svc, "SUPPORT_BYTES", len(raw)), \
             mock.patch.object(svc, "SUPPORT_SHA256", svc.sha(raw)), \
             mock.patch("builtins.open", return_value=stream) as open_file, \
             mock.patch.object(importlib.machinery.SourceFileLoader, "exec_module",
                               side_effect=AssertionError("cache loader must not run")) as loader:
            loaded = svc.load_support(r"D:\cloud-authored\pinned_support.py")
        open_file.assert_called_once_with(Path(r"D:\cloud-authored\pinned_support.py"), "rb")
        self.assertEqual(reads, [len(raw) + 1])
        loader.assert_not_called()
        self.assertEqual(loaded.EXECUTED_MARKER, "verified-buffer")
        self.assertEqual(loaded.__name__, "mrl_qdrant_pinned_support")
        self.assertEqual(loaded.__package__, "")
        self.assertEqual(loaded.__file__, r"D:\cloud-authored\pinned_support.py")
    def test_duplicate_json_keys_rejected(self):
        with self.assertRaises(svc.Hold):
            svc.strict_json(b'{"origin_signature":"MrLiouWord","origin_signature":"other"}')
    def test_manifest_valid_fixture(self):
        self.assertTrue(svc.manifest_contract(manifest(), INSTANCE))
    def test_manifest_identity_and_restart_tampering_rejected(self):
        changes = {"expected_host": "OTHER", "endpoint": "http://0.0.0.0:6333",
                   "origin_signature": "other", "restart_count": 999, "restart_interval_seconds": 1,
                   "python_path": r"C:\Python\python.exe", "version": "1.20.0",
                   "api_key_relative_path": "../key.txt"}
        for field, value in changes.items():
            m = manifest()
            m[field] = value
            with self.subTest(field=field):
                self.assertFalse(svc.manifest_contract(m, INSTANCE))
    def test_duplicate_or_escaping_file_records_rejected(self):
        for rel in ("../outside", "C:/outside", "/absolute", r"runtime\..\other"):
            m = manifest()
            m["files"][0]["path"] = rel
            with self.subTest(rel=rel):
                self.assertFalse(svc.manifest_contract(m, INSTANCE))
        m = manifest()
        m["files"].append(dict(m["files"][0]))
        self.assertFalse(svc.manifest_contract(m, INSTANCE))

class EnvironmentTests(unittest.TestCase):
    def test_guard_environment_preserved(self):
        original = {"PYTHONPATH": r"D:\legitimate_guard", "MRL_GUARD": "enabled", "TEMP": r"C:\old"}
        result = svc.child_environment(original, INSTANCE, KEY)
        self.assertEqual(result["PYTHONPATH"], original["PYTHONPATH"])
        self.assertEqual(result["MRL_GUARD"], "enabled")
        self.assertEqual(original["TEMP"], r"C:\old")
        self.assertTrue(result["TEMP"].startswith(INSTANCE))
        self.assertEqual(result["QDRANT__SERVICE__API_KEY"], KEY)
    def test_conflicting_qdrant_host_fails_closed(self):
        original = {"QDRANT__SERVICE__HOST": "0.0.0.0", "MRL_GUARD": "enabled"}
        with self.assertRaisesRegex(svc.Hold, "^conflicting_qdrant_environment$"):
            svc.child_environment(original, INSTANCE, KEY)
        self.assertEqual(original["QDRANT__SERVICE__HOST"], "0.0.0.0")
    def test_unknown_qdrant_override_is_not_silently_stripped(self):
        with self.assertRaises(svc.Hold):
            svc.child_environment({"QDRANT__SERVICE__GRPC_PORT": "6334"}, INSTANCE, KEY)
    def test_conflicting_inherited_key_never_echoed(self):
        with self.assertRaises(svc.Hold) as caught:
            svc.child_environment({"QDRANT__SERVICE__API_KEY": "PRIVATE-FIXTURE"}, INSTANCE, KEY)
        self.assertNotIn("PRIVATE-FIXTURE", str(caught.exception))
    def test_compatible_case_insensitive_override_preserved(self):
        original = {"qdrant__service__host": "127.0.0.1", "MRL_GUARD": "enabled"}
        result = svc.child_environment(original, INSTANCE, KEY)
        self.assertEqual(result["qdrant__service__host"], "127.0.0.1")
        self.assertNotIn("QDRANT__SERVICE__HOST", result)

class TaskPolicyTests(unittest.TestCase):
    def setUp(self):
        self.root = ET.fromstring(svc.task_xml(INSTANCE))
    def value(self, path):
        return self.root.find(path, NS).text
    def test_xml_accepts_utf8_file_and_utf16_bstr_transport(self):
        raw = svc.task_xml(INSTANCE)
        self.assertEqual(raw.splitlines()[0], b'<?xml version="1.0"?>')
        from_file = ET.fromstring(raw)
        from_bstr = ET.fromstring(raw.decode("utf-8").encode("utf-16"))
        self.assertEqual(ET.tostring(from_file), ET.tostring(from_bstr))
    def test_install_is_explicitly_disabled(self):
        self.assertEqual(self.value("t:Settings/t:Enabled"), "false")
    def test_system_principal_xml_avoids_invalid_serviceaccount_enum(self):
        self.assertEqual(self.value("t:Principals/t:Principal/t:UserId"), "S-1-5-18")
        self.assertEqual(self.value("t:Principals/t:Principal/t:RunLevel"), "HighestAvailable")
        self.assertIsNone(self.root.find("t:Principals/t:Principal/t:LogonType", NS))
        self.assertEqual(self.root.find("t:Actions", NS).attrib["Context"],
                         self.root.find("t:Principals/t:Principal", NS).attrib["id"])
    def test_fixed_private_action_no_isolation_or_shell(self):
        self.assertEqual(self.value("t:Actions/t:Exec/t:Command"), svc.PYTHON)
        args = self.value("t:Actions/t:Exec/t:Arguments")
        self.assertEqual(args, '-B "' + INSTANCE + '\\runtime\\' + svc.SELF_NAME
                         + '" supervise --instance "' + INSTANCE + '"')
        self.assertNotIn("-I", args)
        self.assertNotIn("-S", args)
        self.assertNotIn("_operations", args)
    def test_bounded_retries_and_unlimited_healthy_uptime(self):
        self.assertEqual(self.value("t:Settings/t:RestartOnFailure/t:Count"), "3")
        self.assertEqual(self.value("t:Settings/t:RestartOnFailure/t:Interval"), "PT1M")
        self.assertEqual(self.value("t:Settings/t:MultipleInstancesPolicy"), "IgnoreNew")
        self.assertEqual(self.value("t:Settings/t:ExecutionTimeLimit"), "PT0S")
        self.assertEqual(self.value("t:Triggers/t:BootTrigger/t:Delay"), "PT30S")
    def test_powershell_engine_absolute_even_with_shadowing_path(self):
        def get_system(buffer, size):
            buffer.value = r"C:\Windows\System32"
            return len(buffer.value)
        fake_win = types.SimpleNamespace(
            k=types.SimpleNamespace(GetSystemDirectoryW=get_system),
            path=lambda p: Path(p))
        output = json.dumps({"status": "ACL_PRIVATE", "origin_signature": svc.ORIGIN}).encode()
        response = types.SimpleNamespace(returncode=0, stdout=output, stderr=b"")
        with mock.patch.object(svc, "digest", return_value=(svc.TASK_SHA256, svc.TASK_BYTES)), \
             mock.patch.object(svc.subprocess, "run", return_value=response) as run, \
             mock.patch.dict(svc.os.environ, {"PATH": r"D:\untrusted-first"}, clear=False):
            svc.ps_call(fake_win, Path(INSTANCE) / svc.TASK_NAME, "AclCheck", INSTANCE, INSTANCE)
        command = run.call_args.args[0]
        self.assertEqual(command[0], r"C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
        self.assertNotIn("env", run.call_args.kwargs)
        self.assertNotIn("-NoProfile", command)
        self.assertNotIn("-ExecutionPolicy", command)
    def test_fixed_config_loopback_and_grpc_disabled(self):
        d = svc.service_config(INSTANCE)
        self.assertEqual(d["service"]["host"], "127.0.0.1")
        self.assertEqual(d["service"]["http_port"], 6333)
        self.assertIsNone(d["service"]["grpc_port"])
        self.assertIsNone(d["service"]["metrics_port"])
        self.assertFalse(d["cluster"]["enabled"])
        self.assertTrue(d["telemetry_disabled"])
        for field in ("storage_path", "snapshots_path", "temp_path"):
            self.assertTrue(d["storage"][field].startswith(INSTANCE))
            self.assertLess(len(d["storage"][field]), 100)
        self.assertNotIn("api_key", json.dumps(d))

class ProbeTests(unittest.TestCase):
    def setUp(self):
        self.support = types.SimpleNamespace(listener_contract=lambda rows, pid:
            rows == [("127.0.0.1", 6333, pid)])
        self.win = types.SimpleNamespace(listeners=lambda: [("127.0.0.1", 6333, 123)])
        self.responses = [(200, {"version": "1.19.2"}),
                          (200, {"status": "ok", "result": {"collections": [{"name": "PRIVATE-COLLECTION"}]}}),
                          (401, None)]
    def test_readonly_auth_probe_exports_only_count(self):
        with mock.patch.object(svc, "request_json", side_effect=self.responses) as request:
            receipt = svc.probe(self.support, self.win, 123, KEY)
        self.assertEqual(receipt["collection_count"], 1)
        self.assertEqual(receipt["missing_key_status"], 401)
        self.assertNotIn("PRIVATE-COLLECTION", json.dumps(receipt))
        self.assertNotIn(KEY, json.dumps(receipt))
        self.assertEqual([c.args[1] for c in request.call_args_list], ["/", "/collections", "/collections"])
    def test_foreign_or_public_listener_prevents_all_requests(self):
        for rows in ([("0.0.0.0", 6333, 123)], [("127.0.0.1", 6333, 999)]):
            self.win.listeners = lambda: rows
            with mock.patch.object(svc, "request_json") as request:
                with self.assertRaises(svc.Hold):
                    svc.probe(self.support, self.win, 123, KEY)
                request.assert_not_called()
    def test_missing_key_200_is_failure(self):
        self.responses[-1] = (200, {"status": "ok"})
        with mock.patch.object(svc, "request_json", side_effect=self.responses):
            with self.assertRaisesRegex(svc.Hold, "missing_key_not_denied"):
                svc.probe(self.support, self.win, 123, KEY)
    def test_wrong_version_is_failure(self):
        self.responses[0] = (200, {"version": "1.18.0"})
        with mock.patch.object(svc, "request_json", side_effect=self.responses):
            with self.assertRaisesRegex(svc.Hold, "version_mismatch"):
                svc.probe(self.support, self.win, 123, KEY)
    def test_listener_change_during_auth_is_failure(self):
        self.win.listeners = mock.Mock(side_effect=[
            [("127.0.0.1", 6333, 123)], [("127.0.0.1", 6333, 999)]])
        with mock.patch.object(svc, "request_json", side_effect=self.responses):
            with self.assertRaisesRegex(svc.Hold, "listener_changed"):
                svc.probe(self.support, self.win, 123, KEY)
    def test_arbitrary_read_route_rejected(self):
        with self.assertRaisesRegex(svc.Hold, "fixed_readonly_route_required"):
            svc.request_json(self.support, "/collections/private/points", KEY)

class SeparationTests(unittest.TestCase):
    def test_install_only_calls_disabled_install(self):
        fake_manifest = manifest()
        win = object()
        with mock.patch.object(svc, "validate_instance", return_value=(Path(INSTANCE), fake_manifest, KEY)), \
             mock.patch.object(svc, "ps_call", return_value={"status": "INSTALLED_DISABLED", "task": {"enabled": False}}) as ps, \
             mock.patch.object(svc, "persist_receipt", side_effect=lambda w, i, r: r), \
             mock.patch.object(svc, "verify") as verify:
            result = svc.control(object(), win, types.SimpleNamespace(command="install", instance=INSTANCE))
        self.assertEqual(ps.call_args.args[2], "Install")
        self.assertEqual(result["status"], "INSTALLED_DISABLED")
        self.assertFalse(result["files_removed"])
        verify.assert_not_called()
    def test_remove_preserves_files_and_keys(self):
        with mock.patch.object(svc, "validate_instance", return_value=(Path(INSTANCE), manifest(), KEY)), \
             mock.patch.object(svc, "ps_call", return_value={"status": "OWN_TASK_REMOVED"}) as ps, \
             mock.patch.object(svc, "persist_receipt", side_effect=lambda w, i, r: r):
            result = svc.control(object(), object(), types.SimpleNamespace(command="remove", instance=INSTANCE))
        self.assertEqual(ps.call_args.args[2], "Remove")
        self.assertFalse(result["data_removed"])
        self.assertFalse(result["keys_removed"])
    def test_process_creation_identity_not_pid_only(self):
        wanted = {"pid": 123, "created_filetime": 1234567, "image": r"D:\own\qdrant.exe"}
        self.assertTrue(svc.same_process_record(dict(wanted), wanted))
        changed = dict(wanted, created_filetime=1234568)
        self.assertFalse(svc.same_process_record(changed, wanted))

if __name__ == "__main__":
    unittest.main()
