#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ASI_WorldRuntime_v1.py — contract-gated ASI facade for WorldModule.

The legacy L4 WorldModule remains available as historical/runtime material.
This ASI entry point never constructs or exposes a world object until the
current MRL_ASI_ENTRY_CONTRACT_V1_1 token has been verified.
"""

from __future__ import annotations

import pathlib
from typing import Any, Dict, List, Optional, Tuple

from MRL_ASI_EntryGate_v1 import EntryGate
from world_module import WorldModule

ORIGIN_SIGNATURE = "MrLiouWord"
ASI_WORLD_VERSION = "1.1.0"


class ASIWorldRuntime:
    """Fail-closed ASI world facade. Every operation is re-authorized."""

    def __init__(
        self,
        *,
        entry_token: str,
        gate: Optional[EntryGate] = None,
        data_dir: Optional[pathlib.Path | str] = None,
    ) -> None:
        self._gate = gate or EntryGate()
        self._entry_token = entry_token
        self._entry = self._gate.require_entry(entry_token, action="enter_world")
        self._world = WorldModule() if data_dir is None else WorldModule(pathlib.Path(data_dir))

    @property
    def subject_ref(self) -> str:
        return str(self._entry["subject_ref"])

    def _authorize(self, action: str) -> Dict[str, Any]:
        self._entry = self._gate.require_entry(self._entry_token, action=action)
        return self._entry

    def set_node(self, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
        self._authorize("set_node")
        return self._world.set_node(name, data)

    def get_node(self, name: str) -> Optional[Dict[str, Any]]:
        self._authorize("get_node")
        return self._world.get_node(name)

    def list_nodes(self) -> List[str]:
        self._authorize("list_nodes")
        return self._world.list_nodes()

    def set_state(self, key: str, value: Any) -> None:
        self._authorize("set_state")
        self._world.set_state(key, value)

    def get_state(self, key: str, default: Any = None) -> Any:
        self._authorize("get_state")
        return self._world.get_state(key, default)

    def snapshot(self) -> Dict[str, Any]:
        self._authorize("snapshot")
        result = self._world.snapshot()
        result["asi_world_version"] = ASI_WORLD_VERSION
        result["entry_contract_subject_ref"] = self.subject_ref
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
        return self._world.set_globe_coord(node_name, lat, lon, alt, meta)

    def get_globe_coord(self, node_name: str) -> Optional[Dict[str, Any]]:
        self._authorize("get_globe_coord")
        return self._world.get_globe_coord(node_name)

    def trajectory(self) -> List[Dict[str, Any]]:
        self._authorize("trajectory")
        return self._world.trajectory()

    def rewind(self, steps: int = 1) -> Tuple[bool, str]:
        self._authorize("rewind")
        return self._world.rewind(steps)
