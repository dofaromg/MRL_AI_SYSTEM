"""Pure fixtures for durable synthetic CRUD ownership; no disk writes or network."""
import importlib.util
import io
import json
from pathlib import Path
import types
import unittest
from unittest import mock

if "CLIENT_UNDER_TEST" in globals():
    client = CLIENT_UNDER_TEST
else:
    path = Path(__file__).resolve().with_name("MRL_qdrant_durable_crud_v3.py")
    spec = importlib.util.spec_from_file_location("mrl_durable_crud_tested", path)
    client = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(client)

INSTANCE = r"D:\MRL_Mother\QdrantLocal\2d38cbbc0b4d4988a19f100c7b9f2d7d"

class FakeAPI:
    def __init__(self, exists=False, create_status=200, bad_read=False, bad_delete=False):
        self.exists = exists
        self.create_status = create_status
        self.bad_read = bad_read
        self.bad_delete = bad_delete
        self.calls = []
        self.point = None
        self.collection = None
        self.deleted = False
    def __call__(self, method, route, body=None):
        self.calls.append((method, route))
        if method == "GET":
            return (200, {"status": "ok"}) if self.exists and not self.deleted else (404, None)
        if method == "PUT" and "/points" not in route:
            if self.create_status != 200:
                return self.create_status, None
            self.collection = route.split("?")[0]
            self.exists = True
            return 200, {"status": "ok", "result": True}
        if method == "PUT":
            self.point = json.loads(json.dumps(body["points"][0]))
            return 200, {"status": "ok", "result": {"status": "completed"}}
        if method == "POST":
            row = json.loads(json.dumps(self.point))
            if self.bad_read:
                row["vector"] = [1, 2, 3, 4]
            return 200, {"status": "ok", "result": [row]}
        if method == "DELETE":
            if self.bad_delete:
                return 500, None
            if route.split("?")[0] != self.collection:
                raise AssertionError("delete targets an unowned collection")
            self.deleted = True
            return 200, {"status": "ok", "result": True}
        raise AssertionError("unexpected method")

class DurableCRUDTests(unittest.TestCase):
    def test_only_fixed_d_instance_boundary(self):
        self.assertTrue(client.valid_instance(INSTANCE))
        for value in (INSTANCE.replace("D:", "C:"), INSTANCE + r"\..\other",
                      r"\\host\D$\MRL_Mother\QdrantLocal\2d38cbbc0b4d4988a19f100c7b9f2d7d",
                      INSTANCE.replace("QdrantLocal", "QdrantProbe")):
            with self.subTest(value=value):
                self.assertFalse(client.valid_instance(value))
    def test_source_hash_mismatch_never_executes(self):
        raw = b"raise AssertionError('unverified source executed')\n"
        with mock.patch("builtins.open", return_value=io.BytesIO(raw)), \
             mock.patch.object(client, "SERVICE_BYTES", len(raw)), \
             mock.patch.object(client, "SERVICE_SHA256", "0" * 64):
            with self.assertRaisesRegex(client.Hold, "service_source_hash_mismatch"):
                client.load_service(INSTANCE)
    def test_success_cleans_only_own_collection_and_exports_no_point(self):
        api = FakeAPI()
        guard = mock.Mock()
        result = client.exercise(api, guard)
        self.assertEqual(result["status"], "SYNTHETIC_CRUD_PASS")
        self.assertTrue(result["cleanup_confirmed"])
        self.assertTrue(api.deleted)
        deletes = [route for method, route in api.calls if method == "DELETE"]
        self.assertEqual(deletes, [api.collection + "?timeout=10"])
        self.assertEqual(guard.call_count, 12)
        encoded = json.dumps(result)
        self.assertNotIn(api.point["id"], encoded)
        self.assertNotIn(api.point["payload"]["probe_nonce"], encoded)
        self.assertNotIn(api.collection, encoded)
        self.assertNotIn("vector", encoded)
    def test_existing_collection_never_created_or_deleted(self):
        api = FakeAPI(exists=True)
        result = client.exercise(api, lambda: None)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual([method for method, route in api.calls], ["GET"])
        self.assertFalse(result["creation_acknowledged"])
    def test_unacknowledged_create_never_deleted(self):
        api = FakeAPI(create_status=500)
        result = client.exercise(api, lambda: None)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["creation_outcome_uncertain"])
        self.assertFalse(result["creation_acknowledged"])
        self.assertNotIn("DELETE", [method for method, route in api.calls])
    def test_failed_read_cleans_acknowledged_own_collection_but_remains_hold(self):
        api = FakeAPI(bad_read=True)
        result = client.exercise(api, lambda: None)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["cleanup_confirmed"])
        self.assertTrue(api.deleted)
        self.assertIn("synthetic_point_exact_readback_failed", result["errors"])
    def test_lost_owner_after_create_prevents_delete(self):
        api = FakeAPI()
        calls = 0
        def guard():
            nonlocal calls
            calls += 1
            if calls > 4:
                raise client.Hold("held_process_listener_boundary_changed")
        result = client.exercise(api, guard)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["creation_acknowledged"])
        self.assertFalse(result["cleanup_confirmed"])
        self.assertNotIn("DELETE", [method for method, route in api.calls])
    def test_transient_owner_failure_latches_and_never_cleans_up(self):
        api = FakeAPI()
        calls = 0
        def guard():
            nonlocal calls
            calls += 1
            if calls == 5:
                raise client.Hold("held_process_listener_boundary_changed")
        result = client.exercise(api, guard)
        self.assertEqual(result["status"], "HOLD")
        self.assertTrue(result["creation_acknowledged"])
        self.assertTrue(result["ownership_guard_failed"])
        self.assertFalse(result["cleanup_confirmed"])
        self.assertFalse(result["delete_attempted"])
        self.assertEqual(calls, 5)
        self.assertEqual([method for method, route in api.calls], ["GET", "PUT"])
    def test_ambiguous_delete_is_not_retried(self):
        api = FakeAPI(bad_delete=True)
        result = client.exercise(api, lambda: None)
        self.assertEqual(result["status"], "HOLD")
        self.assertFalse(result["cleanup_confirmed"])
        self.assertEqual(sum(method == "DELETE" for method, route in api.calls), 1)

    def test_create_wait_extended_only_within_overall_budget(self):
        route = "/collections/mrl_durable_" + "1" * 32
        opener = mock.Mock()
        def response(*args, **kwargs):
            result = io.BytesIO(b'{"status":"ok","result":true}')
            result.code = 200
            return result
        opener.open.side_effect = response
        service = types.SimpleNamespace(strict_json=json.loads)
        support = types.SimpleNamespace(NoRedirect=client.urllib.request.HTTPRedirectHandler)
        with mock.patch.object(client.time, "monotonic", return_value=100) as clock, \
             mock.patch.object(client.urllib.request, "build_opener", return_value=opener):
            request = client.http_client(service, support, "synthetic-test-key")
            cases = (
                ("PUT", route + "?timeout=10", {"vectors": {"size": 4, "distance": "Dot"}}, 60),
                ("PUT", route + "/points?wait=true&timeout=10", {"points": []}, 12),
                ("POST", route + "/points?timeout=10", {"ids": []}, 12),
                ("GET", route, None, 12),
                ("DELETE", route + "?timeout=10", None, 60),
            )
            for method, path, body, expected in cases:
                with self.subTest(method=method, route=path):
                    request(method, path, body)
                    self.assertEqual(opener.open.call_args.kwargs["timeout"], expected)
            clock.return_value = 278
            request("PUT", route + "?timeout=10", {"vectors": {"size": 4, "distance": "Dot"}})
            self.assertEqual(opener.open.call_args.kwargs["timeout"], 2)
            calls = opener.open.call_count
            clock.return_value = 280
            with self.assertRaisesRegex(client.Hold, "crud_deadline_exceeded"):
                request("GET", route)
            self.assertEqual(opener.open.call_count, calls)


    def test_delete_timeout_never_retried(self):
        api = FakeAPI()
        deletes = []
        def request(method, route, body=None):
            if method == "DELETE":
                deletes.append(route)
                raise TimeoutError("synthetic")
            return api(method, route, body)
        result = client.exercise(request, lambda: None)
        self.assertEqual(result["status"], "HOLD")
        self.assertEqual(len(deletes), 1)
        self.assertTrue(result["delete_attempted"])
        self.assertFalse(result["cleanup_confirmed"])
        self.assertIn("exception_TimeoutError", result["errors"])

    def test_delete_wait_capped_by_remaining_budget(self):
        opener = mock.Mock()
        response = io.BytesIO(b'{"status":"ok","result":true}')
        response.code = 200
        opener.open.return_value = response
        service = types.SimpleNamespace(strict_json=json.loads)
        support = types.SimpleNamespace(NoRedirect=client.urllib.request.HTTPRedirectHandler)
        with mock.patch.object(client.time, "monotonic", side_effect=[100, 278]), \
             mock.patch.object(client.urllib.request, "build_opener", return_value=opener):
            request = client.http_client(service, support, "synthetic-test-key")
            request("DELETE", "/collections/mrl_durable_" + "1"*32 + "?timeout=10")
            self.assertEqual(opener.open.call_args.kwargs["timeout"], 2)

if __name__ == "__main__":
    unittest.main()
