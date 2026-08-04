#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRL ASI World Runtime v1.4 with the canonical origin closed loop.

Every closed-loop operation first re-verifies the ASI entry covenant.  The
underlying pipeline ledger stores hashes only and exposes no hidden/private
visibility path.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, Mapping, Optional

from MRL_ASI_WorldRuntime_v1_1 import ASIWorldRuntime as _TransparencyRuntime
from MRL_OriginClosedLoop_v1 import OriginClosedLoop

ORIGIN_SIGNATURE = "MrLiouWord"
ASI_WORLD_VERSION = "1.4.0"


class ASIWorldRuntime(_TransparencyRuntime):
    """Official ASI facade: entry gate + transparency + origin closed loop."""

    def __init__(
        self,
        *,
        entry_token: str,
        gate: Any = None,
        visibility_policy: Any = None,
        data_dir: Optional[pathlib.Path | str] = None,
        closed_loop_dir: Optional[pathlib.Path | str] = None,
        closed_loop_source: Optional[pathlib.Path | str] = None,
    ) -> None:
        super().__init__(
            entry_token=entry_token,
            gate=gate,
            visibility_policy=visibility_policy,
            data_dir=data_dir,
        )
        if closed_loop_dir is None:
            if data_dir is None:
                closed_loop_dir = (
                    pathlib.Path(__file__).resolve().parent.parent
                    / "06_trace"
                    / "_runtime"
                    / "origin_closed_loop"
                )
            else:
                closed_loop_dir = pathlib.Path(data_dir) / "origin_closed_loop"
        options: Dict[str, Any] = {}
        if closed_loop_source is not None:
            options["source_path"] = closed_loop_source
        self._origin_closed_loop = OriginClosedLoop(closed_loop_dir, **options)

    def begin_origin_cycle(
        self,
        *,
        cycle_id: str,
        clean_snapshot_artifacts: Mapping[str, pathlib.Path | str],
        clean_snapshot_evidence: Mapping[str, pathlib.Path | str],
        parent_export_manifest_hash: Optional[str] = None,
    ) -> Dict[str, Any]:
        self._authorize("begin_origin_cycle")
        return self._origin_closed_loop.begin_cycle_from_files(
            cycle_id=cycle_id,
            clean_snapshot_artifacts=clean_snapshot_artifacts,
            clean_snapshot_evidence=clean_snapshot_evidence,
            parent_export_manifest_hash=parent_export_manifest_hash,
        )

    def complete_origin_stage(
        self,
        *,
        stage: str,
        artifacts: Mapping[str, pathlib.Path | str],
        evidence: Mapping[str, pathlib.Path | str],
    ) -> Dict[str, Any]:
        self._authorize("complete_origin_stage:" + stage)
        return self._origin_closed_loop.complete_stage_from_files(
            stage=stage,
            artifacts=artifacts,
            evidence=evidence,
        )

    def origin_cycle_status(self) -> Dict[str, Any]:
        self._authorize("origin_cycle_status")
        return self._origin_closed_loop.status()

    def verify_origin_cycle(self) -> Dict[str, Any]:
        self._authorize("verify_origin_cycle")
        return self._origin_closed_loop.verify()

    def snapshot(self) -> Dict[str, Any]:
        result = super().snapshot()
        result["asi_world_version"] = ASI_WORLD_VERSION
        result["origin_closed_loop"] = self._origin_closed_loop.status()
        result["origin_closed_loop_source_sha256"] = (
            "95a292718552570639b296a6ff157bee72740d6acf281ff07aa0d790ad73a7a3"
        )
        result["pipeline_presence_is_deployment_proof"] = False
        return result
