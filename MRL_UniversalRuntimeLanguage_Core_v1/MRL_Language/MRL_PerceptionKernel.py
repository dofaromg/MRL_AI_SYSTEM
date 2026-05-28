# MRL_PerceptionKernel
# origin_signature: MrLiouWord
# layer: MRL_Language
"""感知核心：正式主體詞為 Perception；Attention 僅作歷史層 / Adapter 層。

  MRL_PerceptionField_Core   — 感知場（節點 → 感知權重）
  MRL_PerceptionWeight_Map   — 權重映射（確定性，依 depth/intent/role）
  MRL_PerceptionKernel_Router — 路由器（依感知權重決定 runtime 觀察序）
"""

from __future__ import annotations

from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"

# Attention 為歷史層 / Adapter；不作為主體。
ATTENTION_LAYER = "history_adapter"

_ROLE_WEIGHT = {
    "definition": 1.0,
    "control_flow": 0.9,
    "invocation": 0.85,
    "dependency": 0.7,
    "binding": 0.6,
    "structure": 0.55,
    "container": 0.5,
    "sequence": 0.5,
    "enumeration": 0.45,
    "narrative": 0.4,
    "datum": 0.35,
    "statement": 0.3,
    "particle": 0.25,
}


class MRL_PerceptionWeight_Map:
    """確定性感知權重映射。"""

    @staticmethod
    def weight(node: Dict[str, Any]) -> float:
        role = node["semantic"]["role"]
        depth = int(node["context"]["depth"])
        base = _ROLE_WEIGHT.get(role, 0.3)
        # 越淺（越靠近主結構）感知權重越高
        return round(base / (1.0 + 0.1 * depth), 6)


class MRL_PerceptionField_Core:
    """感知場：對 MetaIR 全節點建立 (node_id → weight)。"""

    def __init__(self, metair: Dict[str, Any]) -> None:
        self.metair = metair
        self.field: Dict[str, float] = {
            n["node_id"]: MRL_PerceptionWeight_Map.weight(n)
            for n in metair.get("nodes", [])
        }

    def summary(self) -> Dict[str, Any]:
        vals = list(self.field.values()) or [0.0]
        return {
            "origin_signature": ORIGIN_SIGNATURE,
            "subject": "Perception",
            "attention_layer": ATTENTION_LAYER,
            "node_count": len(self.field),
            "max_weight": max(vals),
            "min_weight": min(vals),
        }


class MRL_PerceptionKernel_Router:
    """路由器：依感知權重產生 runtime 觀察序（高權重優先），保留原序為 tiebreak。"""

    def __init__(self, field: MRL_PerceptionField_Core) -> None:
        self.field = field

    def observation_order(self) -> List[str]:
        nodes = self.field.metair.get("nodes", [])
        return [
            n["node_id"]
            for n in sorted(
                nodes,
                key=lambda n: (-self.field.field[n["node_id"]], n["index"]),
            )
        ]


def observe(metair: Dict[str, Any]) -> Dict[str, Any]:
    """Observe 階段入口：建立感知場 + 觀察序。"""
    field = MRL_PerceptionField_Core(metair)
    router = MRL_PerceptionKernel_Router(field)
    return {
        "field_summary": field.summary(),
        "observation_order": router.observation_order(),
        "field": field.field,
    }
