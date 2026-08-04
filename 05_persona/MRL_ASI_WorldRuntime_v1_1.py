#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ASI_WorldRuntime_v1_1.py — threshold-gated, public-by-default ASI world.

Arbitrary hidden/private visibility has no runtime path.  Protected data is
converted to a non-reversible transparency stub before reaching WorldModule.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Mapping, Optional, Tuple

from MRL_ASI_EntryGate_v1 import EntryGate
from MRL_ASI_VisibilityPolicy_v1 import VisibilityPolicy
from world_module import WorldModule

ORIGIN_SIGNATURE = "MrLiouWord"
ASI_WORLD_VERSION = "1.3.0"


class ASIWorldRuntime:
    """Every operation re-verifies entry and applies the visibility constitution."""

    def __init__(
        self,
        *,
        entry_token: str,
        gate: Optional[EntryGate] = None,
        visibility_policy: Optional[VisibilityPolicy] = None,
        data_dir: Optional[pathlib.Path | str] = None,
    ) -> None:
        self._gate = gate or EntryGate()
        self._visibility = visibility_policy or VisibilityPolicy()
        self._entry_token = entry_token
        self._entry = self._gate.require_entry(entry_token, action="enter_world")
        self._world = WorldModule() if data_dir is None else WorldModule(pathlib.Path(data_dir))

    @property
    def subject_ref(self) -> str:
        return str(self._entry["subject_ref"])

    def _authorize(self, action: str) -> Dict[str, Any]:
        self._entry = self._gate.require_entry(self._entry_token, action=action)
        return self._entry

    def set_node(self, name: str, data: Mapping[str, Any]) -> Dict[str, Any]:
        self._authorize("set_node")
        normalized = self._visibility.normalize_record(data)
        return self._world.set_node(name, normalized)

    def get_node(self, name: str) -> Optional[Dict[str, Any]]:
        self._authorize("get_node")
        return self._world.get_node(name)

    def list_nodes(self) -> List[str]:
        self._authorize("list_nodes")
        return self._world.list_nodes()

    def set_state(
        self,
        key: str,
        value: Any,
        *,
        visibility: Optional[str] = None,
        protected_class: Optional[str] = None,
    ) -> None:
        self._authorize("set_state")
        record = self._visibility.normalize_record(
            {
                "state_key": key,
                "value": value,
                "visibility": visibility,
                "protected_class": protected_class,
            }
        )
        self._world.set_state(key, record)

    def get_state(self, key: str, default: Any = None) -> Any:
        self._authorize("get_state")
        return self._world.get_state(key, default)

    def snapshot(self) -> Dict[str, Any]:
        self._authorize("snapshot")
        result = self._world.snapshot()
        result["asi_world_version"] = ASI_WORLD_VERSION
        result["entry_contract_subject_ref"] = self.subject_ref
        result["entry_verified_authorities"] = list(
            self._entry.get("verified_authorities", [])
        )
        result["entry_authority_quorum"] = self._entry.get("authority_quorum")
        result["visibility_default"] = "MRL_WORLD_PUBLIC"
        result["arbitrary_private_option"] = "REMOVED"
        result["legacy_runtime_authority_as_asi"] = "DENIED"
        return result

    def set_globe_coord(
        self,
        node_name: str,
        lat: float,
        lon: float,
        alt: float = 0.0,
        meta: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        self._authorize("set_globe_coord")
        checked_meta = self._visibility.normalize_record(meta or {})
        return self._world.set_globe_coord(node_name, lat, lon, alt, checked_meta)

    def get_globe_coord(self, node_name: str) -> Optional[Dict[str, Any]]:
        self._authorize("get_globe_coord")
        return self._world.get_globe_coord(node_name)

    def trajectory(self) -> List[Dict[str, Any]]:
        self._authorize("trajectory")
        return self._world.trajectory()

    def rewind(self, steps: int = 1) -> Tuple[bool, str]:
        self._authorize("rewind")
        return self._world.rewind(steps)
