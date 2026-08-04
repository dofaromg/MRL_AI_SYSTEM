#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRL origin-to-export closed-loop runtime.

This module turns the canonical Pipeline v0.1 handoff into a strict, auditable
state machine.  It records hashes only: protected payloads and raw artifacts do
not enter the public ledger.  Presence of this file is not deployment proof;
a cycle is complete only after all nine ordered stages and an export manifest
verify against the append-only hash chain.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
import pathlib
import re
import sys
import time
from typing import Any, Dict, Mapping, Optional, Sequence

ORIGIN_SIGNATURE = "MrLiouWord"
LAW_ID = "MRL_ORIGIN_CLOSED_LOOP_RUNTIME_V1"
RUNTIME_VERSION = "1.0.0"
PIPELINE_ID = "MRL_INTEGRATION_PIPELINE_V0_1"
PIPELINE_VERSION = "0.1"
SOURCE_SHA256 = "95a292718552570639b296a6ff157bee72740d6acf281ff07aa0d790ad73a7a3"
ZERO_HASH = "0" * 64

PIPELINE_STAGES: Sequence[str] = (
    "CLEAN_SNAPSHOT",
    "SEED_IMPORT",
    "ANALYST_BG_COMPILE",
    "DEDUP_MERGE",
    "PATCH_RECOVERY",
    "REBUILD_MESH_COHERENCE",
    "PERFECT_QUEUE",
    "BUILD_GLOBE",
    "EXPORT",
)

_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_SAFE_LABEL = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_SOURCE = (
    _REPO_ROOT
    / "08_sources"
    / "MRL_Origin_ClosedLoop"
    / "MRL_循環_OriginClosedLoop_v1.txt"
)
_DEFAULT_STATE_DIR = _REPO_ROOT / "06_trace" / "_runtime" / "origin_closed_loop"


class ClosedLoopDenied(RuntimeError):
    """Fail-closed rejection with a stable machine-readable code."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


def _canonical_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: pathlib.Path | str) -> str:
    digest = hashlib.sha256()
    with pathlib.Path(path).open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


class OriginClosedLoop:
    """Nine-stage append-only origin pipeline with exact export-to-origin link."""

    def __init__(
        self,
        state_dir: pathlib.Path | str = _DEFAULT_STATE_DIR,
        *,
        source_path: pathlib.Path | str = _DEFAULT_SOURCE,
        clock_ns: Any = time.time_ns,
    ) -> None:
        self.state_dir = pathlib.Path(state_dir)
        self.source_path = pathlib.Path(source_path)
        self.ledger_path = self.state_dir / "origin_closed_loop.jsonl"
        self.state_path = self.state_dir / "origin_closed_loop_state.json"
        self.exports_dir = self.state_dir / "exports"
        self._clock_ns = clock_ns
        self.state_dir.mkdir(parents=True, exist_ok=True)
        self.exports_dir.mkdir(parents=True, exist_ok=True)

        self._verify_source()
        if self.state_path.exists():
            try:
                loaded = json.loads(self.state_path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError) as exc:
                raise ClosedLoopDenied("STATE_INVALID", "state snapshot is invalid") from exc
            if not isinstance(loaded, dict):
                raise ClosedLoopDenied("STATE_INVALID", "state snapshot must be an object")
            self._state = loaded
        else:
            if self.ledger_path.exists() and self.ledger_path.stat().st_size:
                raise ClosedLoopDenied(
                    "STATE_SNAPSHOT_MISSING",
                    "ledger exists without its derived state snapshot; manual recovery required",
                )
            self._state: Dict[str, Any] = {
                "schema": "mrl.origin-closed-loop.state.v1",
                "source_sha256": SOURCE_SHA256,
                "pipeline_id": PIPELINE_ID,
                "pipeline_version": PIPELINE_VERSION,
                "event_count": 0,
                "last_event_hash": ZERO_HASH,
                "cycle_ids": [],
                "active_cycle": None,
                "last_closed_export_manifest_hash": None,
            }
            self._save_state()
        self.verify()

    def _verify_source(self) -> None:
        if not self.source_path.is_file():
            raise ClosedLoopDenied("SOURCE_MISSING", "canonical origin source is missing")
        observed = sha256_file(self.source_path)
        if observed != SOURCE_SHA256:
            raise ClosedLoopDenied(
                "SOURCE_HASH_MISMATCH",
                f"canonical origin source hash {observed} does not match {SOURCE_SHA256}",
            )

    def _save_state(self) -> None:
        temporary = self.state_path.with_suffix(".json.tmp")
        temporary.write_bytes(_canonical_bytes(self._state) + b"\n")
        os.replace(temporary, self.state_path)

    @staticmethod
    def _normalize_hash_map(name: str, values: Mapping[str, str]) -> Dict[str, str]:
        if not isinstance(values, Mapping) or not values:
            raise ClosedLoopDenied(f"{name.upper()}_EMPTY", f"{name} hashes are required")
        normalized: Dict[str, str] = {}
        for label, digest in values.items():
            label = str(label)
            digest = str(digest).lower()
            if not _SAFE_LABEL.fullmatch(label):
                raise ClosedLoopDenied(
                    "HASH_LABEL_INVALID",
                    f"{name} label must be a safe stable identifier",
                )
            if not _HEX64.fullmatch(digest):
                raise ClosedLoopDenied(
                    "HASH_INVALID",
                    f"{name} hash for {label} must be lowercase SHA-256",
                )
            normalized[label] = digest
        return dict(sorted(normalized.items()))

    @staticmethod
    def _hash_files(name: str, paths: Mapping[str, pathlib.Path | str]) -> Dict[str, str]:
        if not isinstance(paths, Mapping) or not paths:
            raise ClosedLoopDenied(f"{name.upper()}_EMPTY", f"{name} files are required")
        hashes: Dict[str, str] = {}
        for label, raw_path in paths.items():
            path = pathlib.Path(raw_path)
            if not path.is_file():
                raise ClosedLoopDenied(
                    "PROOF_FILE_MISSING",
                    f"{name} file for {label} does not exist",
                )
            hashes[str(label)] = sha256_file(path)
        return hashes

    def _append_event(self, event: Mapping[str, Any]) -> Dict[str, Any]:
        record: Dict[str, Any] = {
            "schema": "mrl.origin-closed-loop.event.v1",
            "event_index": int(self._state["event_count"]),
            "timestamp_ns": int(self._clock_ns()),
            "origin_signature": ORIGIN_SIGNATURE,
            "law_id": LAW_ID,
            "runtime_version": RUNTIME_VERSION,
            "source_sha256": SOURCE_SHA256,
            "pipeline_id": PIPELINE_ID,
            "pipeline_version": PIPELINE_VERSION,
            "previous_event_hash": self._state["last_event_hash"],
            **dict(event),
        }
        record["event_hash"] = _sha256_bytes(_canonical_bytes(record))
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")
            handle.flush()
            os.fsync(handle.fileno())
        self._state["event_count"] = record["event_index"] + 1
        self._state["last_event_hash"] = record["event_hash"]
        return record

    def _stage_entry(
        self,
        stage: str,
        artifacts: Mapping[str, str],
        evidence: Mapping[str, str],
    ) -> Dict[str, Any]:
        cycle = self._state["active_cycle"]
        event = self._append_event(
            {
                "event": "PIPELINE_STAGE_COMPLETED",
                "result": "PASS",
                "cycle_id": cycle["cycle_id"],
                "stage_index": PIPELINE_STAGES.index(stage),
                "stage": stage,
                "artifact_hashes": dict(artifacts),
                "evidence_hashes": dict(evidence),
                "protected_payload_included": False,
            }
        )
        entry = {
            "stage_index": PIPELINE_STAGES.index(stage),
            "stage": stage,
            "artifact_hashes": dict(artifacts),
            "evidence_hashes": dict(evidence),
            "event_hash": event["event_hash"],
        }
        cycle["completed_stages"].append(entry)
        cycle["next_stage"] = (
            PIPELINE_STAGES[len(cycle["completed_stages"])]
            if len(cycle["completed_stages"]) < len(PIPELINE_STAGES)
            else None
        )
        self._save_state()
        return entry

    def begin_cycle(
        self,
        *,
        cycle_id: str,
        clean_snapshot_artifact_hashes: Mapping[str, str],
        clean_snapshot_evidence_hashes: Mapping[str, str],
        parent_export_manifest_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Begin a cycle by completing stage 0 with observed hash evidence."""
        self.verify()
        if not _SAFE_LABEL.fullmatch(cycle_id):
            raise ClosedLoopDenied("CYCLE_ID_INVALID", "cycle_id is not a safe stable label")
        if cycle_id in self._state["cycle_ids"]:
            raise ClosedLoopDenied("CYCLE_ID_DUPLICATE", "cycle_id has already been used")
        active = self._state.get("active_cycle")
        if active and active.get("status") == "RUNNING":
            raise ClosedLoopDenied(
                "PREVIOUS_CYCLE_NOT_CLOSED",
                "the active cycle must reach EXPORT before another cycle begins",
            )

        expected_parent = self._state.get("last_closed_export_manifest_hash")
        if expected_parent is None:
            if parent_export_manifest_hash is not None:
                raise ClosedLoopDenied(
                    "GENESIS_PARENT_FORBIDDEN",
                    "the genesis cycle is anchored to the canonical source, not a prior export",
                )
        elif parent_export_manifest_hash != expected_parent:
            raise ClosedLoopDenied(
                "PARENT_EXPORT_HASH_MISMATCH",
                "next CLEAN_SNAPSHOT must point to the exact previous export manifest",
            )

        artifacts = self._normalize_hash_map(
            "artifact", clean_snapshot_artifact_hashes
        )
        evidence = self._normalize_hash_map(
            "evidence", clean_snapshot_evidence_hashes
        )
        self._state["cycle_ids"].append(cycle_id)
        self._state["active_cycle"] = {
            "cycle_id": cycle_id,
            "status": "RUNNING",
            "source_sha256": SOURCE_SHA256,
            "parent_export_manifest_hash": parent_export_manifest_hash,
            "completed_stages": [],
            "next_stage": "CLEAN_SNAPSHOT",
            "export_manifest_path": None,
            "export_manifest_hash": None,
        }
        self._save_state()
        entry = self._stage_entry("CLEAN_SNAPSHOT", artifacts, evidence)
        return {"cycle_id": cycle_id, "status": "RUNNING", "completed": entry}

    def begin_cycle_from_files(
        self,
        *,
        cycle_id: str,
        clean_snapshot_artifacts: Mapping[str, pathlib.Path | str],
        clean_snapshot_evidence: Mapping[str, pathlib.Path | str],
        parent_export_manifest_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        return self.begin_cycle(
            cycle_id=cycle_id,
            clean_snapshot_artifact_hashes=self._hash_files(
                "artifact", clean_snapshot_artifacts
            ),
            clean_snapshot_evidence_hashes=self._hash_files(
                "evidence", clean_snapshot_evidence
            ),
            parent_export_manifest_hash=parent_export_manifest_hash,
        )

    def complete_stage(
        self,
        *,
        stage: str,
        artifact_hashes: Mapping[str, str],
        evidence_hashes: Mapping[str, str],
    ) -> Dict[str, Any]:
        """Complete exactly the next stage; skips and reordering fail closed."""
        self.verify()
        cycle = self._state.get("active_cycle")
        if not cycle or cycle.get("status") != "RUNNING":
            raise ClosedLoopDenied("NO_ACTIVE_CYCLE", "there is no running cycle")
        expected = cycle.get("next_stage")
        if stage != expected:
            raise ClosedLoopDenied(
                "STAGE_ORDER_VIOLATION",
                f"expected {expected}, received {stage}",
            )
        if stage == "CLEAN_SNAPSHOT":
            raise ClosedLoopDenied(
                "STAGE_ZERO_REQUIRES_BEGIN",
                "CLEAN_SNAPSHOT is completed only by begin_cycle",
            )
        artifacts = self._normalize_hash_map("artifact", artifact_hashes)
        evidence = self._normalize_hash_map("evidence", evidence_hashes)
        entry = self._stage_entry(stage, artifacts, evidence)
        result: Dict[str, Any] = {
            "cycle_id": cycle["cycle_id"],
            "status": "RUNNING",
            "completed": entry,
        }
        if stage == "EXPORT":
            result.update(self._close_cycle())
        return result

    def complete_stage_from_files(
        self,
        *,
        stage: str,
        artifacts: Mapping[str, pathlib.Path | str],
        evidence: Mapping[str, pathlib.Path | str],
    ) -> Dict[str, Any]:
        return self.complete_stage(
            stage=stage,
            artifact_hashes=self._hash_files("artifact", artifacts),
            evidence_hashes=self._hash_files("evidence", evidence),
        )

    def _close_cycle(self) -> Dict[str, Any]:
        cycle = self._state["active_cycle"]
        if len(cycle["completed_stages"]) != len(PIPELINE_STAGES):
            raise ClosedLoopDenied("PIPELINE_INCOMPLETE", "all nine stages are required")
        manifest: Dict[str, Any] = {
            "schema": "mrl.origin-closed-loop.export-manifest.v1",
            "origin_signature": ORIGIN_SIGNATURE,
            "source_sha256": SOURCE_SHA256,
            "pipeline_id": PIPELINE_ID,
            "pipeline_version": PIPELINE_VERSION,
            "cycle_id": cycle["cycle_id"],
            "parent_export_manifest_hash": cycle["parent_export_manifest_hash"],
            "stages": copy.deepcopy(cycle["completed_stages"]),
            "ledger_head_at_export": self._state["last_event_hash"],
            "closed_loop_edge": "this_manifest_sha256 -> next CLEAN_SNAPSHOT parent",
        }
        manifest_bytes = _canonical_bytes(manifest) + b"\n"
        manifest_hash = _sha256_bytes(manifest_bytes)
        manifest_path = self.exports_dir / f"{cycle['cycle_id']}.manifest.json"
        if manifest_path.exists():
            raise ClosedLoopDenied(
                "EXPORT_MANIFEST_EXISTS",
                "an immutable export manifest already exists for this cycle",
            )
        manifest_path.write_bytes(manifest_bytes)
        close_event = self._append_event(
            {
                "event": "PIPELINE_CYCLE_CLOSED",
                "result": "CLOSED",
                "cycle_id": cycle["cycle_id"],
                "completed_stage_count": len(PIPELINE_STAGES),
                "export_manifest_hash": manifest_hash,
                "export_manifest_relative_path": str(
                    manifest_path.relative_to(self.state_dir)
                ),
                "next_required_parent_export_manifest_hash": manifest_hash,
                "protected_payload_included": False,
            }
        )
        cycle["status"] = "CLOSED"
        cycle["export_manifest_path"] = str(manifest_path)
        cycle["export_manifest_hash"] = manifest_hash
        cycle["closed_event_hash"] = close_event["event_hash"]
        self._state["last_closed_export_manifest_hash"] = manifest_hash
        self._save_state()
        return {
            "status": "CLOSED",
            "export_manifest_hash": manifest_hash,
            "export_manifest_path": str(manifest_path),
            "closed_event_hash": close_event["event_hash"],
        }

    def verify(self) -> Dict[str, Any]:
        """Verify source, ledger chain, derived state head, and last export."""
        self._verify_source()
        previous = ZERO_HASH
        count = 0
        if self.ledger_path.exists():
            for line_number, line in enumerate(
                self.ledger_path.read_text(encoding="utf-8").splitlines(), start=1
            ):
                try:
                    record = json.loads(line)
                except json.JSONDecodeError as exc:
                    raise ClosedLoopDenied(
                        "LEDGER_INVALID", f"ledger line {line_number} is invalid JSON"
                    ) from exc
                if not isinstance(record, dict):
                    raise ClosedLoopDenied("LEDGER_INVALID", "ledger record is not an object")
                supplied_hash = record.pop("event_hash", None)
                if record.get("event_index") != count:
                    raise ClosedLoopDenied("LEDGER_INDEX_INVALID", "ledger index is not contiguous")
                if record.get("previous_event_hash") != previous:
                    raise ClosedLoopDenied("LEDGER_CHAIN_BROKEN", "ledger previous hash mismatch")
                if record.get("source_sha256") != SOURCE_SHA256:
                    raise ClosedLoopDenied("SOURCE_HASH_MISMATCH", "ledger source anchor mismatch")
                expected_hash = _sha256_bytes(_canonical_bytes(record))
                if supplied_hash != expected_hash:
                    raise ClosedLoopDenied("LEDGER_EVENT_TAMPERED", "ledger event hash mismatch")
                previous = expected_hash
                count += 1
        if int(self._state.get("event_count", -1)) != count:
            raise ClosedLoopDenied("STATE_LEDGER_DIVERGED", "state event count differs from ledger")
        if self._state.get("last_event_hash") != previous:
            raise ClosedLoopDenied("STATE_LEDGER_DIVERGED", "state ledger head differs from ledger")
        if self._state.get("source_sha256") != SOURCE_SHA256:
            raise ClosedLoopDenied("SOURCE_HASH_MISMATCH", "state source anchor mismatch")

        active = self._state.get("active_cycle")
        if active and active.get("status") == "CLOSED":
            manifest_path = pathlib.Path(str(active.get("export_manifest_path")))
            if not manifest_path.is_file():
                raise ClosedLoopDenied("EXPORT_MANIFEST_MISSING", "closed export manifest is missing")
            observed = sha256_file(manifest_path)
            if observed != active.get("export_manifest_hash"):
                raise ClosedLoopDenied("EXPORT_MANIFEST_TAMPERED", "export manifest hash mismatch")
            if observed != self._state.get("last_closed_export_manifest_hash"):
                raise ClosedLoopDenied("STATE_EXPORT_DIVERGED", "state export hash mismatch")
        return {
            "status": "VERIFIED",
            "source_sha256": SOURCE_SHA256,
            "event_count": count,
            "ledger_head": previous,
            "active_cycle_status": active.get("status") if active else None,
            "last_closed_export_manifest_hash": self._state.get(
                "last_closed_export_manifest_hash"
            ),
        }

    def status(self) -> Dict[str, Any]:
        verified = self.verify()
        return {
            **verified,
            "pipeline_stages": list(PIPELINE_STAGES),
            "active_cycle": copy.deepcopy(self._state.get("active_cycle")),
        }


def _assignments(values: Sequence[str]) -> Dict[str, pathlib.Path]:
    result: Dict[str, pathlib.Path] = {}
    for value in values:
        if "=" not in value:
            raise ClosedLoopDenied("ARGUMENT_INVALID", "file arguments use LABEL=PATH")
        label, path = value.split("=", 1)
        result[label] = pathlib.Path(path)
    return result


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MRL Pipeline v0.1 closed-loop proof runtime")
    parser.add_argument("--state-dir", type=pathlib.Path, default=_DEFAULT_STATE_DIR)
    parser.add_argument("--source", type=pathlib.Path, default=_DEFAULT_SOURCE)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("status")
    commands.add_parser("verify")

    begin = commands.add_parser("begin")
    begin.add_argument("--cycle-id", required=True)
    begin.add_argument("--artifact", action="append", default=[], metavar="LABEL=PATH")
    begin.add_argument("--evidence", action="append", default=[], metavar="LABEL=PATH")
    begin.add_argument("--parent-export-hash")

    complete = commands.add_parser("complete")
    complete.add_argument("--stage", required=True, choices=PIPELINE_STAGES[1:])
    complete.add_argument("--artifact", action="append", default=[], metavar="LABEL=PATH")
    complete.add_argument("--evidence", action="append", default=[], metavar="LABEL=PATH")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        loop = OriginClosedLoop(args.state_dir, source_path=args.source)
        if args.command == "status":
            result = loop.status()
        elif args.command == "verify":
            result = loop.verify()
        elif args.command == "begin":
            result = loop.begin_cycle_from_files(
                cycle_id=args.cycle_id,
                clean_snapshot_artifacts=_assignments(args.artifact),
                clean_snapshot_evidence=_assignments(args.evidence),
                parent_export_manifest_hash=args.parent_export_hash,
            )
        else:
            result = loop.complete_stage_from_files(
                stage=args.stage,
                artifacts=_assignments(args.artifact),
                evidence=_assignments(args.evidence),
            )
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except ClosedLoopDenied as exc:
        print(json.dumps({"status": "DENIED", **exc.as_dict()}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
