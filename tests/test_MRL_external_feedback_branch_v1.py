#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Tests for MRL_ExternalFeedbackBranch_v1 end-to-end recovery branch."""
from __future__ import annotations

import json
import pathlib
import sys
import tempfile
import unittest

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent / "09_workflow"))
from MRL_ExternalFeedbackBranch_v1 import ExternalFeedbackInput, MRL_ExternalFeedbackBranch


class TestExternalFeedbackBranch(unittest.TestCase):
    def setUp(self) -> None:
        self.tmp = tempfile.TemporaryDirectory()
        self.root = pathlib.Path(self.tmp.name)
        self.branch = MRL_ExternalFeedbackBranch(
            workspace_root=self.root / "workspace",
            ltm_store_path=self.root / "workspace" / "flow_memory" / "ltm.json",
        )

    def tearDown(self) -> None:
        self.tmp.cleanup()

    def test_end_to_end_generates_archive_and_ready_state(self) -> None:
        result = self.branch.process_external_feedback(
            ExternalFeedbackInput(
                external_system="OpenAI",
                content="external response payload for recoverable branch",
                persona_id="CorePersona",
                metadata={"field": "engineering", "identity": "openai-bridge"},
            )
        )
        self.assertEqual(result["branch_name"], "Mrliou_MRL_ExternalFeedbackBranch_v1")
        self.assertEqual(
            result["dependency_chain"],
            [
                "ExternalSystem",
                "FeedbackLoop",
                "FlowMemory",
                "CollapseCore",
                "ArchiveWriter",
                "FlowMemoryMount",
                "ReadyState",
            ],
        )
        self.assertTrue(result["ready_state"]["ready"])

        archive_path = self.branch.repo_root / result["archive_path"]
        self.assertTrue(archive_path.exists())

    def test_sync_log_jump_trace_and_flowmeta_are_written(self) -> None:
        result = self.branch.process_external_feedback(
            ExternalFeedbackInput(
                external_system="GitHub",
                content="pull request feedback event",
                persona_id="CodePartner",
                metadata={"field": "code", "subpersona": "SubPersona_2"},
            )
        )
        trace_id = result["trace_id"]

        sync_lines = self.branch.sync_log_file.read_text(encoding="utf-8").strip().splitlines()
        jump_lines = self.branch.jump_trace_file.read_text(encoding="utf-8").strip().splitlines()
        meta_lines = self.branch.flowmeta_file.read_text(encoding="utf-8").strip().splitlines()

        self.assertGreaterEqual(len(sync_lines), 1)
        self.assertGreaterEqual(len(jump_lines), 7)
        self.assertGreaterEqual(len(meta_lines), 1)

        self.assertTrue(any(json.loads(line)["trace_id"] == trace_id for line in sync_lines))
        self.assertTrue(any(json.loads(line)["trace_id"] == trace_id for line in jump_lines))
        self.assertTrue(any(json.loads(line)["trace_id"] == trace_id for line in meta_lines))

    def test_collapse_dedup_prevents_duplicate_memory_pollution(self) -> None:
        first = self.branch.process_external_feedback(
            ExternalFeedbackInput(
                external_system="Claude",
                content="same payload for dedupe", 
                persona_id="CorePersona",
            )
        )
        second = self.branch.process_external_feedback(
            ExternalFeedbackInput(
                external_system="Claude",
                content="same payload for dedupe",
                persona_id="CorePersona",
            )
        )

        self.assertFalse(first["collapse"]["deduped"])
        self.assertTrue(second["collapse"]["deduped"])
        self.assertEqual(len(self.branch.long_term_memory), 1)

    def test_archive_mount_roundtrip_returns_ready_state(self) -> None:
        result = self.branch.process_external_feedback(
            ExternalFeedbackInput(
                external_system="Firebase",
                content="state sync callback",
                metadata={"identity": "firebase-listener"},
            )
        )

        remount = self.branch.mount_archive(result["trace_id"])
        self.assertTrue(remount["ok"])
        self.assertTrue(remount["ready_state"]["ready"])
        self.assertTrue(pathlib.Path(remount["mount_path"]).exists())


if __name__ == "__main__":
    unittest.main(verbosity=2)
