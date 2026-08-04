from __future__ import annotations

import json
import os
import pathlib
import tempfile
import unittest
from unittest import mock

from MRL_ASI_EntryGate_v1 import (
    CONTRACT_VERSION,
    REQUIRED_CLAUSES,
    EntryDenied,
    EntryGate,
)
from MRL_ASI_WorldRuntime_v1 import ASIWorldRuntime


KEYS = {
    "earth-node-a": "mrl-test-secret-a-" + ("x" * 48),
    "earth-node-b": "mrl-test-secret-b-" + ("y" * 48),
    "earth-node-c": "mrl-test-secret-c-" + ("z" * 48),
}


class TestMRLASIEntryGate(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = pathlib.Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def gate(self) -> EntryGate:
        return EntryGate(
            trusted_keys=KEYS,
            quorum=2,
            ledger_path=self.tmp_path / "asi_gate.jsonl",
        )

    def token(
        self,
        gate: EntryGate,
        subject_id: str = "creator@example.invalid",
    ) -> str:
        return gate.accept(
            subject_id=subject_id,
            subject_type="human",
            accepted_clauses=REQUIRED_CLAUSES,
            accepted=True,
        )

    def test_gate_fails_closed_without_authority_quorum(self) -> None:
        with mock.patch.dict(os.environ, {}, clear=True):
            gate = EntryGate(ledger_path=self.tmp_path / "ledger.jsonl")
            with self.assertRaisesRegex(EntryDenied, "fails closed") as raised:
                gate.accept(
                    subject_id="subject",
                    subject_type="human",
                    accepted_clauses=REQUIRED_CLAUSES,
                    accepted=True,
                )
        self.assertEqual(raised.exception.code, "AUTHORITY_QUORUM_UNAVAILABLE")

    def test_rejection_and_incomplete_clauses_deny_entry(self) -> None:
        gate = self.gate()
        with self.assertRaises(EntryDenied) as rejected:
            gate.accept(
                subject_id="subject",
                subject_type="human",
                accepted_clauses=REQUIRED_CLAUSES,
                accepted=False,
            )
        self.assertEqual(rejected.exception.code, "ACCEPTANCE_REJECTED")

        with self.assertRaises(EntryDenied) as incomplete:
            gate.accept(
                subject_id="subject",
                subject_type="human",
                accepted_clauses=REQUIRED_CLAUSES[:-1],
                accepted=True,
            )
        self.assertEqual(incomplete.exception.code, "CLAUSES_INCOMPLETE")

    def test_current_complete_acceptance_allows_entry(self) -> None:
        gate = self.gate()
        payload = gate.require_entry(self.token(gate))
        self.assertIs(payload["accepted"], True)
        self.assertEqual(payload["contract_version"], CONTRACT_VERSION)
        self.assertTrue(payload["subject_ref"].startswith("mrl-subject:"))
        self.assertEqual(len(payload["verified_authorities"]), 3)
        self.assertEqual(payload["authority_quorum"], 2)

    def test_raw_subject_identifier_never_enters_ledger(self) -> None:
        gate = self.gate()
        subject = "private-person@example.invalid"
        token = self.token(gate, subject)
        gate.require_entry(token, action="snapshot")
        ledger = gate.ledger_path.read_text(encoding="utf-8")
        self.assertNotIn(subject, ledger)
        self.assertIn("mrl-subject:", ledger)

    def test_tampered_token_is_denied_and_recorded(self) -> None:
        gate = self.gate()
        token = self.token(gate)
        encoded, signatures = token.split(".", 1)
        replacement = "A" if encoded[-1] != "A" else "B"
        tampered = encoded[:-1] + replacement + "." + signatures
        with self.assertRaises(EntryDenied) as raised:
            gate.require_entry(tampered)
        self.assertIn(
            raised.exception.code,
            {"AUTHORITY_QUORUM_NOT_MET", "TOKEN_MALFORMED"},
        )
        self.assertIn(
            "ENTRY_DENIED",
            gate.ledger_path.read_text(encoding="utf-8"),
        )

    def test_stale_contract_is_denied_even_with_valid_quorum(self) -> None:
        gate = self.gate()
        token = self.token(gate)
        payload = gate._decode_unverified(token)
        payload["contract_version"] = "0.9.0"
        stale_token = gate._encode(payload)
        with self.assertRaises(EntryDenied) as raised:
            gate.require_entry(stale_token)
        self.assertEqual(raised.exception.code, "CONTRACT_VERSION_STALE")

    def test_asi_world_runtime_never_constructs_without_entry(self) -> None:
        gate = self.gate()
        world_path = self.tmp_path / "world"
        with self.assertRaises(EntryDenied):
            ASIWorldRuntime(entry_token="", gate=gate, data_dir=world_path)
        self.assertFalse(world_path.exists())

    def test_asi_world_runtime_reauthorizes_every_operation(self) -> None:
        gate = self.gate()
        world = ASIWorldRuntime(
            entry_token=self.token(gate),
            gate=gate,
            data_dir=self.tmp_path / "world",
        )
        world.set_node("FlowSeed", {"type": "persona"})
        self.assertEqual(world.get_node("FlowSeed")["data"]["type"], "persona")
        snapshot = world.snapshot()
        self.assertEqual(snapshot["asi_world_version"], "1.1.0")
        self.assertTrue(
            snapshot["entry_contract_subject_ref"].startswith("mrl-subject:")
        )

        records = [
            json.loads(line)
            for line in gate.ledger_path.read_text(encoding="utf-8").splitlines()
        ]
        actions = [record.get("action") for record in records]
        self.assertIn("enter_world", actions)
        self.assertIn("set_node", actions)
        self.assertIn("get_node", actions)
        self.assertIn("snapshot", actions)


if __name__ == "__main__":
    unittest.main()
