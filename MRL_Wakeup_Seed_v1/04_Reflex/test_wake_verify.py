import importlib.util
import json
import pathlib
import unittest


REPO = pathlib.Path(__file__).resolve().parents[2]
VERIFY_PATH = pathlib.Path(__file__).with_name("wake_verify.py")
SPEC = importlib.util.spec_from_file_location("wake_verify", VERIFY_PATH)
wake_verify = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(wake_verify)


class SchemaArtifactsTests(unittest.TestCase):
    def setUp(self):
        self.s1 = {"mismatch_or_missing": [], "timestamp": "2026-10-02T18:00:00+00:00"}
        self.s2 = {"pending_recovery": 0, "pending_list": []}
        self.s3 = {"roundtrip_fail": 0, "failed": []}
        self.s4 = {"status": "PASS"}
        self.s5 = {"status": "PASS"}
        self.canonical = {"repository": "dofaromg/MRL_AI_SYSTEM"}

    def assert_schema_shape(self, artifact, schema_path):
        schema = json.loads(schema_path.read_text(encoding="utf-8"))
        self.assertTrue(set(schema["required"]).issubset(artifact))
        self.assertEqual(set(artifact), set(schema["properties"]))
        for key, prop in schema["properties"].items():
            if "const" in prop:
                self.assertEqual(artifact[key], prop["const"])
            if "enum" in prop:
                self.assertIn(artifact[key], prop["enum"])

    def test_passed_verification_emits_both_existing_schema_shapes(self):
        report, trace = wake_verify.schema_artifacts(
            self.s1, self.s2, self.s3, self.s4, self.s5, "receipts/wake.json",
            canonical=self.canonical,
        )

        self.assertEqual(report["status"], "PASS")
        self.assertEqual(report["coverage"], 1)
        self.assertEqual(trace["status"], "PASS")
        self.assertEqual(trace["canonical"], self.canonical)
        self.assert_schema_shape(
            report, REPO / "06_trace/wake_verification_report.schema.json"
        )
        self.assert_schema_shape(trace, REPO / "06_trace/wake_trace.schema.json")

    def test_unavailable_checks_are_partial_not_passed(self):
        self.s2["pending_recovery"] = 1
        self.s2["pending_list"] = [{"file": "source.pcode"}]
        self.s3 = {"status": "待找回：dialect unavailable"}
        self.s4 = {"status": "待找回"}
        self.s5 = {"status": "PASS"}

        report, trace = wake_verify.schema_artifacts(
            self.s1, self.s2, self.s3, self.s4, self.s5, "receipts/wake.json"
        )

        self.assertEqual(report["status"], "PARTIAL")
        self.assertLess(report["coverage"], 1)
        self.assertIn("replay:source.pcode", report["missing"])
        self.assertEqual(trace["status"], "FAIL")
        self.assertEqual(trace["error_count"], 3)

    def test_failed_checks_are_recorded_as_mismatches(self):
        self.s1["mismatch_or_missing"] = ["seed.json"]
        self.s3 = {"roundtrip_fail": 1, "failed": ["EchoPersona.pcode"]}

        report, trace = wake_verify.schema_artifacts(
            self.s1, self.s2, self.s3, self.s4, self.s5, "receipts/wake.json"
        )

        self.assertEqual(report["status"], "FAIL")
        self.assertEqual(len(trace["errors"]), 2)
        self.assertIn("seed_selfcheck:seed.json", report["mismatch"])
        self.assertIn("dialect_roundtrip:EchoPersona.pcode", report["mismatch"])


if __name__ == "__main__":
    unittest.main()
