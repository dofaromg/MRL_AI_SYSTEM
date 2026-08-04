from __future__ import annotations

import hashlib
import json
import pathlib
import tempfile
import unittest

from MRL_ASI_EntryGate_v1 import REQUIRED_CLAUSES, EntryGate
from MRL_ASI_VisibilityPolicy_v1 import VisibilityPolicy
from MRL_ASI_WorldRuntime_v1_2 import ASIWorldRuntime
from MRL_OriginClosedLoop_v1 import (
    PIPELINE_STAGES,
    SOURCE_SHA256,
    ClosedLoopDenied,
    OriginClosedLoop,
    sha256_file,
)


REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
SOURCE_PATH = (
    REPO_ROOT
    / "08_sources"
    / "MRL_Origin_ClosedLoop"
    / "MRL_循環_OriginClosedLoop_v1.txt"
)
KEYS = {
    "earth-node-a": "mrl-test-secret-a-" + ("x" * 48),
    "earth-node-b": "mrl-test-secret-b-" + ("y" * 48),
}


class TestMRLOriginClosedLoop(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = pathlib.Path(self._tmp.name)
        self.loop = OriginClosedLoop(
            self.tmp_path / "state",
            source_path=SOURCE_PATH,
            clock_ns=iter(range(1, 1000)).__next__,
        )

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def proof_file(self, name: str, content: str) -> pathlib.Path:
        path = self.tmp_path / name
        path.write_text(content, encoding="utf-8")
        return path

    def begin(self, cycle_id: str = "cycle-001", parent: str | None = None):
        return self.loop.begin_cycle_from_files(
            cycle_id=cycle_id,
            clean_snapshot_artifacts={
                "snapshot": self.proof_file(f"{cycle_id}-snapshot.bin", "snapshot")
            },
            clean_snapshot_evidence={
                "snapshot_report": self.proof_file(
                    f"{cycle_id}-snapshot-proof.json", '{"result":"PASS"}'
                )
            },
            parent_export_manifest_hash=parent,
        )

    def finish(self):
        result = None
        for index, stage in enumerate(PIPELINE_STAGES[1:], start=1):
            result = self.loop.complete_stage_from_files(
                stage=stage,
                artifacts={
                    "stage_output": self.proof_file(
                        f"artifact-{index}.bin", f"artifact:{stage}"
                    )
                },
                evidence={
                    "stage_report": self.proof_file(
                        f"evidence-{index}.json", json.dumps({"stage": stage, "pass": True})
                    )
                },
            )
        return result

    def test_canonical_source_is_byte_exact(self) -> None:
        self.assertEqual(sha256_file(SOURCE_PATH), SOURCE_SHA256)
        self.assertEqual(SOURCE_PATH.stat().st_size, 3762)
        self.assertEqual(len(SOURCE_PATH.read_text(encoding="utf-8").splitlines()), 141)

    def test_stage_skip_and_empty_proof_fail_closed(self) -> None:
        self.begin()
        digest = hashlib.sha256(b"x").hexdigest()
        with self.assertRaises(ClosedLoopDenied) as skipped:
            self.loop.complete_stage(
                stage="DEDUP_MERGE",
                artifact_hashes={"output": digest},
                evidence_hashes={"report": digest},
            )
        self.assertEqual(skipped.exception.code, "STAGE_ORDER_VIOLATION")
        with self.assertRaises(ClosedLoopDenied) as empty:
            self.loop.complete_stage(
                stage="SEED_IMPORT",
                artifact_hashes={},
                evidence_hashes={"report": digest},
            )
        self.assertEqual(empty.exception.code, "ARTIFACT_EMPTY")

    def test_all_nine_stages_create_closed_export(self) -> None:
        self.begin()
        result = self.finish()
        self.assertEqual(result["status"], "CLOSED")
        self.assertRegex(result["export_manifest_hash"], r"^[0-9a-f]{64}$")
        manifest = pathlib.Path(result["export_manifest_path"])
        self.assertTrue(manifest.is_file())
        payload = json.loads(manifest.read_text(encoding="utf-8"))
        self.assertEqual(len(payload["stages"]), 9)
        self.assertEqual([item["stage"] for item in payload["stages"]], list(PIPELINE_STAGES))
        self.assertEqual(self.loop.verify()["status"], "VERIFIED")

    def test_next_cycle_requires_exact_previous_export_hash(self) -> None:
        self.begin()
        closed = self.finish()
        with self.assertRaises(ClosedLoopDenied) as mismatch:
            self.begin("cycle-002", parent="0" * 64)
        self.assertEqual(mismatch.exception.code, "PARENT_EXPORT_HASH_MISMATCH")
        started = self.begin("cycle-002", parent=closed["export_manifest_hash"])
        self.assertEqual(started["completed"]["stage"], "CLEAN_SNAPSHOT")

    def test_new_cycle_before_export_and_duplicate_id_are_denied(self) -> None:
        self.begin()
        with self.assertRaises(ClosedLoopDenied) as running:
            self.begin("cycle-002")
        self.assertEqual(running.exception.code, "PREVIOUS_CYCLE_NOT_CLOSED")
        self.finish()
        with self.assertRaises(ClosedLoopDenied) as duplicate:
            self.begin("cycle-001", parent=self.loop.status()["last_closed_export_manifest_hash"])
        self.assertEqual(duplicate.exception.code, "CYCLE_ID_DUPLICATE")

    def test_ledger_tamper_is_detected(self) -> None:
        self.begin()
        lines = self.loop.ledger_path.read_text(encoding="utf-8").splitlines()
        record = json.loads(lines[0])
        record["result"] = "ALTERED"
        lines[0] = json.dumps(record, ensure_ascii=False, sort_keys=True)
        self.loop.ledger_path.write_text("\n".join(lines) + "\n", encoding="utf-8")
        with self.assertRaises(ClosedLoopDenied) as tampered:
            self.loop.verify()
        self.assertEqual(tampered.exception.code, "LEDGER_EVENT_TAMPERED")

    def test_source_tamper_is_detected(self) -> None:
        altered = self.proof_file("altered-source.txt", "not canonical")
        with self.assertRaises(ClosedLoopDenied) as mismatch:
            OriginClosedLoop(self.tmp_path / "other-state", source_path=altered)
        self.assertEqual(mismatch.exception.code, "SOURCE_HASH_MISMATCH")

    def test_official_asi_facade_reauthorizes_closed_loop_actions(self) -> None:
        gate = EntryGate(
            trusted_keys=KEYS,
            quorum=2,
            ledger_path=self.tmp_path / "asi-entry.jsonl",
        )
        token = gate.accept(
            subject_id="test-subject",
            subject_type="human",
            accepted_clauses=REQUIRED_CLAUSES,
            accepted=True,
        )
        world = ASIWorldRuntime(
            entry_token=token,
            gate=gate,
            visibility_policy=VisibilityPolicy(environment={}),
            data_dir=self.tmp_path / "world",
            closed_loop_source=SOURCE_PATH,
        )
        world.begin_origin_cycle(
            cycle_id="facade-cycle",
            clean_snapshot_artifacts={
                "snapshot": self.proof_file("facade-snapshot.bin", "snapshot")
            },
            clean_snapshot_evidence={
                "report": self.proof_file("facade-report.json", '{"pass":true}')
            },
        )
        status = world.origin_cycle_status()
        self.assertEqual(status["active_cycle"]["next_stage"], "SEED_IMPORT")
        snapshot = world.snapshot()
        self.assertEqual(snapshot["asi_world_version"], "1.4.0")
        actions = [
            json.loads(line).get("action")
            for line in gate.ledger_path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertIn("begin_origin_cycle", actions)
        self.assertIn("origin_cycle_status", actions)
        self.assertIn("snapshot", actions)


if __name__ == "__main__":
    unittest.main()
