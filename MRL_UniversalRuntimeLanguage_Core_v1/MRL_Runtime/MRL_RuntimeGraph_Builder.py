# MRL_RuntimeGraph_Builder — COMPATIBILITY ALIAS（歷史名稱，非 canonical）
# origin_signature: MrLiouWord
# canonical 已遷移至 MRL_RuntimeStructureField；本檔僅為向後兼容 alias，請勿新增主體邏輯。
"""[DEPRECATED] RuntimeGraph / *Graph* 為歷史名稱 / Adapter / alias。

正式 canonical = StructureField（見 MRL_RuntimeStructureField）。
本模組原樣轉出 build / 視覺化函式，並提供舊鍵鏡射 (graph_hash / replay_graph / ...) 供兼容。
"""
from __future__ import annotations

from typing import Any, Dict

from .MRL_RuntimeStructureField import (  # noqa: F401
    ORIGIN_SIGNATURE,
    build as _build_structurefield,
    to_dot,
    to_json,
    to_mermaid,
)


def build(mrliouir: Dict[str, Any], observation_order=None) -> Dict[str, Any]:
    """[alias] 等同 MRL_RuntimeStructureField.build；額外鏡射舊 *graph* 鍵。"""
    sf = dict(_build_structurefield(mrliouir, observation_order))
    sf["graph_version"] = sf["structurefield_version"]
    sf["graph_hash"] = sf["structurefield_hash"]
    sf["edges"] = sf["relations"]
    sf["edge_count"] = sf["relation_count"]
    sf["replay_graph"] = sf["replay_structurefield"]
    sf["restore_graph"] = sf["restore_structurefield"]
    sf["world_graph"] = sf["world_structurefield"]
    return sf


__all__ = ["build", "to_mermaid", "to_dot", "to_json", "ORIGIN_SIGNATURE"]
