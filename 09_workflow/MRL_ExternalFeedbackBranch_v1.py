#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ExternalFeedbackBranch_v1.py — Restore existing mother external feedback branch.

Branch chain (engineering of existing lineage, not a new architecture):
ExternalSystem -> FeedbackLoop -> FlowMemory -> CollapseCore -> ArchiveWriter -> FlowMemoryMount -> ReadyState
"""
from __future__ import annotations

import hashlib
import json
import pathlib
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, Optional

from MRL_LongTermMemory_v1 import MRL_LongTermMemory
from MRL_utils import ORIGIN_SIGNATURE, embed_signature, verify_signature

BRANCH_NAME = "Mrliou_MRL_ExternalFeedbackBranch_v1"


@dataclass(frozen=True)
class ExternalFeedbackInput:
    external_system: str
    content: str
    persona_id: str = "CorePersona"
    metadata: Optional[Dict[str, Any]] = None


class MRL_ExternalFeedbackBranch:
    """Minimal runnable closed loop for the existing mother feedback branch."""

    def __init__(
        self,
        *,
        workspace_root: Optional[pathlib.Path] = None,
        ltm_store_path: Optional[pathlib.Path] = None,
    ) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.repo_root = pathlib.Path(__file__).resolve().parent.parent
        self.workspace_root = pathlib.Path(workspace_root or (self.repo_root / "data" / "external_feedback_branch_v1"))

        self.incoming_dir = self.workspace_root / "incoming"
        self.memory_dir = self.workspace_root / "flow_memory"
        self.archive_dir = self.workspace_root / "archive"
        self.mount_dir = self.workspace_root / "mount"
        self.index_dir = self.workspace_root / "index"

        self.sync_log_file = self.memory_dir / "SyncLog.jsonl"
        self.jump_trace_file = self.memory_dir / "JumpTrace.jsonl"
        self.flowmeta_file = self.memory_dir / "FlowMeta.jsonl"
        self.collapse_index_file = self.index_dir / "CollapseCore.index.json"
        self.signal_index_file = self.index_dir / "UniversalSignalMediaIndex.json"
        self.archive_index_file = self.index_dir / "ArchiveWriter.index.json"

        for p in [self.incoming_dir, self.memory_dir, self.archive_dir, self.mount_dir, self.index_dir]:
            p.mkdir(parents=True, exist_ok=True)

        store_path = pathlib.Path(ltm_store_path or (self.memory_dir / "longterm_memory.json"))
        self.long_term_memory = MRL_LongTermMemory(store_path=store_path)

    def process_external_feedback(self, payload: ExternalFeedbackInput) -> Dict[str, Any]:
        """Run ExternalSystem->...->ReadyState end-to-end."""
        if not payload.external_system or not payload.external_system.strip():
            raise ValueError("external_system is required")
        if not payload.content or not payload.content.strip():
            raise ValueError("content is required")

        trace_id = self._new_trace_id()
        now_ms = int(time.time() * 1000)
        content = payload.content.strip()
        content_hash = self._sha256_text(content)
        metadata = dict(payload.metadata or {})

        ingest_record = {
            "trace_id": trace_id,
            "step": "ExternalSystem",
            "external_system": payload.external_system,
            "source_fingerprint": self._source_fingerprint(payload.external_system, content, metadata),
            "content_sha256": content_hash,
            "ingested_at_ms": now_ms,
            "origin_signature": ORIGIN_SIGNATURE,
        }
        incoming_path = self.incoming_dir / f"{trace_id}.json"
        incoming_path.write_text(json.dumps(embed_signature(ingest_record), ensure_ascii=False, indent=2), encoding="utf-8")

        routing = self._route_modules(payload.external_system, payload.persona_id, metadata)
        collapse = self._collapse(content_hash=content_hash, trace_id=trace_id)

        self._append_jsonl(
            self.sync_log_file,
            {
                "trace_id": trace_id,
                "external_system": payload.external_system,
                "source_fingerprint": ingest_record["source_fingerprint"],
                "synced_at_ms": now_ms,
                "deduped": collapse["deduped"],
                "origin_signature": ORIGIN_SIGNATURE,
            },
        )

        for step, extra in [
            ("ExternalSystem", {"external_system": payload.external_system}),
            ("FeedbackLoop", {"feedback_channel": "FluinInput/SignalEncoder"}),
            ("FlowMemory", {"memory_zone": "FlowMemoryCore"}),
            ("CollapseCore", {"deduped": collapse["deduped"]}),
            ("ArchiveWriter", {}),
            ("FlowMemoryMount", {}),
            ("ReadyState", {}),
        ]:
            self._append_jsonl(
                self.jump_trace_file,
                {
                    "trace_id": trace_id,
                    "step": step,
                    "ts_ms": int(time.time() * 1000),
                    "origin_signature": ORIGIN_SIGNATURE,
                    **extra,
                },
            )

        self._append_jsonl(
            self.flowmeta_file,
            {
                "trace_id": trace_id,
                "external_system": payload.external_system,
                "persona_id": payload.persona_id,
                "routing": routing,
                "field_map": routing["FieldMap"],
                "identity_map": routing["IdentityMap"],
                "flow_bridge": routing["FlowBridge"],
                "ts_ms": int(time.time() * 1000),
                "origin_signature": ORIGIN_SIGNATURE,
            },
        )

        memory_entry = None
        if not collapse["deduped"]:
            memory_entry = self.long_term_memory.remember(
                session_id=f"external:{payload.external_system}",
                role="external_system",
                content=content,
            )

        archive = self._archive_writer(
            trace_id=trace_id,
            payload=payload,
            content_hash=content_hash,
            source_fingerprint=ingest_record["source_fingerprint"],
            routing=routing,
            collapse=collapse,
            memory_entry=memory_entry,
            incoming_path=incoming_path,
        )
        mount = self.mount_archive(trace_id)

        return {
            "branch_name": BRANCH_NAME,
            "trace_id": trace_id,
            "dependency_chain": [
                "ExternalSystem",
                "FeedbackLoop",
                "FlowMemory",
                "CollapseCore",
                "ArchiveWriter",
                "FlowMemoryMount",
                "ReadyState",
            ],
            "incoming_path": str(incoming_path.relative_to(self.repo_root)),
            "sync_log_path": str(self.sync_log_file.relative_to(self.repo_root)),
            "jump_trace_path": str(self.jump_trace_file.relative_to(self.repo_root)),
            "flowmeta_path": str(self.flowmeta_file.relative_to(self.repo_root)),
            "archive_path": str(pathlib.Path(archive["archive_path"]).relative_to(self.repo_root)),
            "collapse": collapse,
            "routing": routing,
            "mount": mount,
            "ready_state": mount["ready_state"],
            "origin_signature": ORIGIN_SIGNATURE,
        }

    def mount_archive(self, trace_id: str) -> Dict[str, Any]:
        archive_path = self.archive_dir / f"{trace_id}.json"
        if not archive_path.exists():
            return {"ok": False, "error": "archive not found", "trace_id": trace_id}

        archive_data = json.loads(archive_path.read_text(encoding="utf-8"))
        signature_ok = verify_signature(archive_data)
        required = [
            "trace_id",
            "external_system",
            "content_sha256",
            "source_fingerprint",
            "collapse",
            "routing",
            "flow_memory",
        ]
        has_required = all(k in archive_data for k in required)
        ready = bool(signature_ok and has_required)

        mount_record = {
            "trace_id": trace_id,
            "flow_memory_mount": {
                "archive_path": str(archive_path),
                "flowmeta_path": str(self.flowmeta_file),
                "jump_trace_path": str(self.jump_trace_file),
            },
            "ready_state": {
                "ready": ready,
                "name": "ReadyState",
                "signature_ok": signature_ok,
                "has_required_dependency_chain": has_required,
                "validated_at_ms": int(time.time() * 1000),
            },
            "origin_signature": ORIGIN_SIGNATURE,
        }

        mount_path = self.mount_dir / f"{trace_id}.json"
        mount_path.write_text(json.dumps(embed_signature(mount_record), ensure_ascii=False, indent=2), encoding="utf-8")
        return {"ok": True, "trace_id": trace_id, "mount_path": str(mount_path), "ready_state": mount_record["ready_state"]}

    def _route_modules(self, external_system: str, persona_id: str, metadata: Dict[str, Any]) -> Dict[str, Any]:
        signal_node = f"signal::{external_system.lower()}"
        self._upsert_signal_index(external_system=external_system, signal_node=signal_node)
        return {
            "UniversalSignalMediaIndex": {
                "source_type": "external_system",
                "source": external_system,
                "signal_node": signal_node,
            },
            "SignalNode": signal_node,
            "FlowBridge": {
                "bridge": "FlowBridge",
                "target": "FlowAgentCore",
            },
            "FlowSync": {
                "sync": "FlowSync",
                "mode": "feedback",
            },
            "FieldMap": {
                "field": metadata.get("field", "global"),
                "external_system": external_system,
            },
            "IdentityMap": {
                "persona_id": persona_id,
                "identity": metadata.get("identity", "ExternalFeedback"),
            },
            "PersonaGate": {
                "persona_id": persona_id,
                "subpersona": metadata.get("subpersona", "SubPersona_1"),
            },
        }

    def _collapse(self, *, content_hash: str, trace_id: str) -> Dict[str, Any]:
        index = self._load_json(self.collapse_index_file, default={"hash_to_trace": {}})
        hash_to_trace = index.setdefault("hash_to_trace", {})
        if content_hash in hash_to_trace:
            existing_trace = hash_to_trace[content_hash]
            self._write_json(self.collapse_index_file, index)
            return {
                "deduped": True,
                "existing_trace_id": existing_trace,
                "content_sha256": content_hash,
                "collapse_core": "CollapseCore",
            }

        hash_to_trace[content_hash] = trace_id
        self._write_json(self.collapse_index_file, index)
        return {
            "deduped": False,
            "existing_trace_id": None,
            "content_sha256": content_hash,
            "collapse_core": "CollapseCore",
        }

    def _archive_writer(
        self,
        *,
        trace_id: str,
        payload: ExternalFeedbackInput,
        content_hash: str,
        source_fingerprint: str,
        routing: Dict[str, Any],
        collapse: Dict[str, Any],
        memory_entry: Optional[Dict[str, Any]],
        incoming_path: pathlib.Path,
    ) -> Dict[str, Any]:
        archive_payload = {
            "branch_name": BRANCH_NAME,
            "trace_id": trace_id,
            "external_system": payload.external_system,
            "persona_id": payload.persona_id,
            "content_sha256": content_hash,
            "source_fingerprint": source_fingerprint,
            "routing": routing,
            "collapse": collapse,
            "flow_memory": {
                "sync_log": str(self.sync_log_file),
                "jump_trace": str(self.jump_trace_file),
                "flowmeta": str(self.flowmeta_file),
                "memory_entry_id": (memory_entry or {}).get("id"),
            },
            "reversible_contract": {
                "ingest_record": str(incoming_path),
                "archive_mount": "FlowMemoryMount",
                "ready_state": "ReadyState",
            },
            "created_at_ms": int(time.time() * 1000),
            "origin_signature": ORIGIN_SIGNATURE,
        }
        signed = embed_signature(archive_payload)
        archive_path = self.archive_dir / f"{trace_id}.json"
        archive_path.write_text(json.dumps(signed, ensure_ascii=False, indent=2), encoding="utf-8")

        index = self._load_json(self.archive_index_file, default={"traces": []})
        traces = index.setdefault("traces", [])
        traces.append(trace_id)
        self._write_json(self.archive_index_file, index)

        return {"archive_path": str(archive_path), "trace_id": trace_id}

    def _upsert_signal_index(self, *, external_system: str, signal_node: str) -> None:
        index = self._load_json(self.signal_index_file, default={"signals": {}})
        signals = index.setdefault("signals", {})
        signals[external_system] = signal_node
        self._write_json(self.signal_index_file, index)

    def _load_json(self, path: pathlib.Path, *, default: Dict[str, Any]) -> Dict[str, Any]:
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:  # noqa: BLE001
                return dict(default)
        return dict(default)

    def _write_json(self, path: pathlib.Path, data: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def _append_jsonl(self, path: pathlib.Path, record: Dict[str, Any]) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")

    def _new_trace_id(self) -> str:
        return f"extfb-{uuid.uuid4().hex[:12]}"

    def _source_fingerprint(self, external_system: str, content: str, metadata: Dict[str, Any]) -> str:
        src = json.dumps(
            {
                "external_system": external_system,
                "content_sha256": self._sha256_text(content),
                "metadata": metadata,
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        return self._sha256_text(src)

    @staticmethod
    def _sha256_text(text: str) -> str:
        return hashlib.sha256(text.encode("utf-8")).hexdigest()


def main() -> None:
    branch = MRL_ExternalFeedbackBranch()
    result = branch.process_external_feedback(
        ExternalFeedbackInput(
            external_system="OpenAI",
            content="FlowAgent external feedback branch seed event",
            persona_id="CorePersona",
            metadata={"field": "global", "identity": "Demo"},
        )
    )
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
