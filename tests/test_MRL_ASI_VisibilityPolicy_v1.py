from __future__ import annotations

import pathlib
import tempfile
import unittest

from MRL_ASI_EntryGate_v1 import REQUIRED_CLAUSES, EntryGate
from MRL_ASI_VisibilityPolicy_v1 import (
    PROTECTED_STUB,
    WORLD_PUBLIC,
    VisibilityDenied,
    VisibilityPolicy,
)
from MRL_ASI_WorldRuntime_v1_1 import ASIWorldRuntime


KEYS = {
    "earth-node-a": "mrl-test-secret-a-" + ("x" * 48),
    "earth-node-b": "mrl-test-secret-b-" + ("y" * 48),
}


class TestMRLASIVisibilityPolicy(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.tmp_path = pathlib.Path(self._tmp.name)

    def tearDown(self) -> None:
        self._tmp.cleanup()

    def gate_and_token(self):
        gate = EntryGate(
            trusted_keys=KEYS,
            quorum=2,
            ledger_path=self.tmp_path / "gate.jsonl",
        )
        token = gate.accept(
            subject_id="creator",
            subject_type="human",
            accepted_clauses=REQUIRED_CLAUSES,
            accepted=True,
        )
        return gate, token

    def test_removed_private_environment_parameter_denies_start(self) -> None:
        with self.assertRaises(VisibilityDenied) as raised:
            VisibilityPolicy({"MRL_PRIVATE_MODE": "false"})
        self.assertEqual(
            raised.exception.code,
            "REMOVED_PRIVATE_ENVIRONMENT_OPTION",
        )
        with self.assertRaises(VisibilityDenied):
            VisibilityPolicy({"MRL_CUSTOM_PRIVACY_MODE": "off"})

    def test_invalid_environment_visibility_denies_start(self) -> None:
        with self.assertRaises(VisibilityDenied):
            VisibilityPolicy({"MRL_DATA_VISIBILITY": "PRIVATE"})

    def test_non_protected_default_is_world_public(self) -> None:
        policy = VisibilityPolicy({})
        result = policy.normalize_record({"name": "public-knowledge", "value": 42})
        self.assertEqual(result["visibility"], WORLD_PUBLIC)

    def test_hidden_and_private_record_options_are_removed(self) -> None:
        policy = VisibilityPolicy({})
        for record in (
            {"visibility": "hidden"},
            {"private": False},
            {"nested": {"is_hidden": True}},
        ):
            with self.assertRaises(VisibilityDenied):
                policy.normalize_record(record)

    def test_personal_data_becomes_non_reversible_public_stub(self) -> None:
        policy = VisibilityPolicy({})
        raw_email = "private-person@example.invalid"
        result = policy.normalize_record({"email": raw_email, "note": "private"})
        self.assertEqual(result["visibility"], PROTECTED_STUB)
        self.assertEqual(result["protected_class"], "personal_data")
        self.assertFalse(result["raw_content_included"])
        self.assertNotIn(raw_email, str(result))
        self.assertTrue(result["transparency_stub"])

    def test_image_and_secret_are_system_protected_not_private_options(self) -> None:
        policy = VisibilityPolicy({})
        image = policy.normalize_record({"filename": "family.jpg", "raw": "bytes"})
        secret = policy.normalize_record({"api_key": "do-not-expose"})
        private_key = policy.normalize_record({"private_key": "key-material"})
        self.assertEqual(image["protected_class"], "images_and_visual_derivatives")
        self.assertEqual(secret["protected_class"], "secrets_and_security_controls")
        self.assertEqual(
            private_key["protected_class"],
            "secrets_and_security_controls",
        )
        self.assertNotIn("do-not-expose", str(secret))

    def test_asi_runtime_refuses_removed_environment_option_before_world_creation(self) -> None:
        gate, token = self.gate_and_token()
        world_path = self.tmp_path / "world"
        with self.assertRaises(VisibilityDenied):
            ASIWorldRuntime(
                entry_token=token,
                gate=gate,
                visibility_policy=VisibilityPolicy({"MRL_HIDDEN": "0"}),
                data_dir=world_path,
            )
        self.assertFalse(world_path.exists())

    def test_asi_runtime_stores_public_record_or_protected_stub_only(self) -> None:
        gate, token = self.gate_and_token()
        world = ASIWorldRuntime(
            entry_token=token,
            gate=gate,
            visibility_policy=VisibilityPolicy({}),
            data_dir=self.tmp_path / "world",
        )
        world.set_node("public", {"knowledge": "shared"})
        world.set_node("image", {"filename": "portrait.png", "raw": "pixels"})
        self.assertEqual(
            world.get_node("public")["data"]["visibility"],
            WORLD_PUBLIC,
        )
        protected = world.get_node("image")["data"]
        self.assertEqual(protected["visibility"], PROTECTED_STUB)
        self.assertFalse(protected["raw_content_included"])
        self.assertNotIn("pixels", str(protected))

        world.set_state("shared_state", {"answer": 42})
        self.assertEqual(
            world.get_state("shared_state")["visibility"],
            WORLD_PUBLIC,
        )


if __name__ == "__main__":
    unittest.main()
