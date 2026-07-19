# MRL_PerceptionKernel
# origin_signature: MrLiouWord
# layer: MRL_Language
"""感知核心：正式主體詞為 Perception；Attention 僅作歷史層 / Adapter 層。

正式名稱（v2）：
  MRL_PerceptionKernel           — 入口 / 路由
  MRL_PerceptionField            — 感知場（節點 → 感知權重）
  MRL_PerceptionWeight           — 權重映射（確定性，依 depth/intent/role）
  MRL_PerceptionStructureField   — 感知結構場（感知場套用於 StructureField）
  MRL_PerceptionScore            — 跨節點感知分數（角色餘弦 × 深度衰減）
  MRL_PerceptionHead             — 單一感知頭（角色偏好視角）
  MRL_MultiPerceptionField       — 多頭感知場（並行多頭 → 融合感知向量）

舊名 MRL_PerceptionField_Core / MRL_PerceptionWeight_Map 保留為 compatibility alias。
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


class MRL_PerceptionWeight:
    """確定性感知權重映射。"""

    @staticmethod
    def weight(node: Dict[str, Any]) -> float:
        role = node["semantic"]["role"]
        depth = int(node["context"]["depth"])
        base = _ROLE_WEIGHT.get(role, 0.3)
        # 越淺（越靠近主結構）感知權重越高
        return round(base / (1.0 + 0.1 * depth), 6)


class MRL_PerceptionField:
    """感知場：對 MrLiouIR 全節點建立 (node_id → weight)。"""

    def __init__(self, mrliouir: Dict[str, Any]) -> None:
        self.mrliouir = mrliouir
        self.field: Dict[str, float] = {
            n["node_id"]: MRL_PerceptionWeight.weight(n)
            for n in mrliouir.get("nodes", [])
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

    def __init__(self, field: "MRL_PerceptionField") -> None:
        self.field = field

    def observation_order(self) -> List[str]:
        nodes = self.field.mrliouir.get("nodes", [])
        return [
            n["node_id"]
            for n in sorted(
                nodes,
                key=lambda n: (-self.field.field[n["node_id"]], n["index"]),
            )
        ]


# ── Compatibility aliases（舊名，非 canonical 主體）──
MRL_PerceptionWeight_Map = MRL_PerceptionWeight
MRL_PerceptionField_Core = MRL_PerceptionField
# 感知結構場：感知場套用於 StructureField（目前等同感知場，預留 StructureField 擴展）
MRL_PerceptionStructureField = MRL_PerceptionField


def observe(mrliouir: Dict[str, Any]) -> Dict[str, Any]:
    """Observe 階段入口：建立感知場 + 觀察序。"""
    field = MRL_PerceptionField(mrliouir)
    router = MRL_PerceptionKernel_Router(field)
    return {
        "field_summary": field.summary(),
        "observation_order": router.observation_order(),
        "field": field.field,
    }


# ─── 跨節點感知分數（Cross-node Perception Score） ────────────────────────────
# 規則：query 節點對 key 節點的感知強度 = 角色餘弦相似 × 深度接近度衰減。
# 設計：純確定性，無隨機，無外部依賴，可重現。

_ROLE_VEC: Dict[str, List[float]] = {
    # 每個角色以 8 維語意向量表示（維度：structure, control, data, relation, sequence,
    # narrative, execution, declaration；值均經 L2 正規化設計）
    "definition":   [0.1, 0.2, 0.0, 0.3, 0.0, 0.0, 0.1, 1.0],
    "control_flow": [0.0, 1.0, 0.0, 0.2, 0.0, 0.0, 0.3, 0.0],
    "invocation":   [0.0, 0.3, 0.0, 0.1, 0.0, 0.0, 1.0, 0.2],
    "dependency":   [0.1, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0, 0.3],
    "binding":      [0.0, 0.0, 0.6, 0.4, 0.0, 0.0, 0.2, 0.0],
    "structure":    [1.0, 0.1, 0.0, 0.2, 0.3, 0.0, 0.0, 0.1],
    "container":    [0.8, 0.0, 0.2, 0.1, 0.3, 0.0, 0.0, 0.0],
    "sequence":     [0.2, 0.1, 0.0, 0.0, 1.0, 0.0, 0.0, 0.0],
    "enumeration":  [0.3, 0.0, 0.2, 0.0, 0.8, 0.1, 0.0, 0.0],
    "narrative":    [0.1, 0.0, 0.1, 0.0, 0.2, 1.0, 0.0, 0.0],
    "datum":        [0.0, 0.0, 1.0, 0.2, 0.0, 0.1, 0.0, 0.0],
    "statement":    [0.1, 0.2, 0.3, 0.1, 0.1, 0.3, 0.2, 0.0],
    "particle":     [0.0, 0.0, 0.5, 0.0, 0.5, 0.0, 0.0, 0.0],
}
_DIM = 8


def _role_vec(role: str) -> List[float]:
    return _ROLE_VEC.get(role, [0.125] * _DIM)


def _dot(a: List[float], b: List[float]) -> float:
    return sum(x * y for x, y in zip(a, b))


def _norm(v: List[float]) -> float:
    import math
    return math.sqrt(sum(x * x for x in v)) or 1.0


def _cosine(a: List[float], b: List[float]) -> float:
    return _dot(a, b) / (_norm(a) * _norm(b))


class MRL_PerceptionScore:
    """跨節點感知分數（Cross-node Perception Score）。

    score(query_node, key_node) = 角色餘弦相似 × 深度接近度衰減。
    結果範圍：0.0 ~ 1.0（確定性，可重現）。
    Attention 為歷史詞 / Adapter；正式主體詞 = Perception。
    """

    @staticmethod
    def score(query_node: Dict[str, Any], key_node: Dict[str, Any]) -> float:
        """感知分數：query 節點對 key 節點的感知強度。"""
        import math
        q_role = query_node["semantic"]["role"]
        k_role = key_node["semantic"]["role"]
        cos = _cosine(_role_vec(q_role), _role_vec(k_role))
        # 深度接近度衰減：|depth_q - depth_k| 越大，感知越弱
        q_depth = int(query_node["context"]["depth"])
        k_depth = int(key_node["context"]["depth"])
        depth_decay = 1.0 / (1.0 + 0.5 * abs(q_depth - k_depth))
        return round(cos * depth_decay, 6)

    @staticmethod
    def score_matrix(nodes: List[Dict[str, Any]]) -> List[List[float]]:
        """全節點對感知分數矩陣（n × n，確定性）。"""
        n = len(nodes)
        return [
            [MRL_PerceptionScore.score(nodes[i], nodes[j]) for j in range(n)]
            for i in range(n)
        ]


class MRL_PerceptionHead:
    """單一感知頭（Single Perception Head）。

    每個頭持有一套角色投影偏好（role_bias），依偏好調整感知分數。
    多頭感知 = 不同角色偏好視角下的平行感知計算。
    """

    def __init__(self, role_bias: Dict[str, float]) -> None:
        """role_bias: 角色 → 放大係數（1.0 = 無偏；>1.0 = 偏好）。"""
        self.role_bias = role_bias

    def attend(
        self,
        query_node: Dict[str, Any],
        nodes: List[Dict[str, Any]],
    ) -> List[Dict[str, Any]]:
        """query_node 對所有 nodes 計算偏好感知分數，回傳 [(node_id, score), ...]（降序）。"""
        import math

        raw: List[Dict[str, Any]] = []
        for kn in nodes:
            base = MRL_PerceptionScore.score(query_node, kn)
            bias = self.role_bias.get(kn["semantic"]["role"], 1.0)
            raw.append({"node_id": kn["node_id"], "score": base * bias})

        # Softmax 正規化（對數穩定）
        vals = [r["score"] for r in raw]
        if vals:
            m = max(vals)
            exp_vals = [math.exp(v - m) for v in vals]
            z = sum(exp_vals) or 1.0
            for r, ev in zip(raw, exp_vals):
                r["score"] = round(ev / z, 6)

        raw.sort(key=lambda x: (-x["score"], x["node_id"]))
        return raw


# 預設四個感知頭（不同角色偏好視角，對應結構/控制/資料/敘事四類感知）
_DEFAULT_HEADS: List[Dict[str, float]] = [
    # 頭 0：結構偏好（structure, definition, container）
    {"structure": 1.5, "definition": 1.5, "container": 1.3},
    # 頭 1：控制偏好（control_flow, invocation）
    {"control_flow": 1.5, "invocation": 1.4},
    # 頭 2：資料偏好（datum, binding, dependency）
    {"datum": 1.5, "binding": 1.3, "dependency": 1.2},
    # 頭 3：敘事偏好（narrative, sequence, enumeration）
    {"narrative": 1.5, "sequence": 1.3, "enumeration": 1.2},
]


class MRL_MultiPerceptionField:
    """多頭感知場（Multi-Head Perception Field）。

    並行執行 N 個感知頭，各頭依自身角色偏好計算感知分數，
    最終融合（mean）為全節點感知向量。
    正式主體詞 = Perception；Attention 為歷史 / Adapter。
    """

    def __init__(
        self,
        mrliouir: Dict[str, Any],
        head_biases: List[Dict[str, float]] | None = None,
    ) -> None:
        self.mrliouir = mrliouir
        self.nodes = mrliouir.get("nodes", [])
        self.heads = [
            MRL_PerceptionHead(b) for b in (head_biases or _DEFAULT_HEADS)
        ]
        # 預計算感知場（per-node base weight）
        self._base_field = MRL_PerceptionField(mrliouir)

    def perceive(self, query_node: Dict[str, Any]) -> Dict[str, Any]:
        """對 query_node 執行多頭感知，回傳融合感知向量（node_id → fused_score）。"""
        head_outputs: List[List[Dict[str, Any]]] = [
            h.attend(query_node, self.nodes) for h in self.heads
        ]
        # 聚合：各頭分數取均值
        score_acc: Dict[str, float] = {}
        for head_out in head_outputs:
            for item in head_out:
                score_acc[item["node_id"]] = (
                    score_acc.get(item["node_id"], 0.0) + item["score"]
                )
        n_heads = len(self.heads) or 1
        fused = {nid: round(s / n_heads, 6) for nid, s in score_acc.items()}
        # 加乘基礎感知場權重（結構 × 感知）
        for nid in fused:
            base = self._base_field.field.get(nid, 0.0)
            fused[nid] = round(fused[nid] * (1.0 + base), 6)
        return {
            "query_node_id": query_node["node_id"],
            "head_count": len(self.heads),
            "fused_scores": fused,
            "top_node": max(fused, key=lambda k: fused[k]) if fused else None,
        }

    def full_field(self) -> Dict[str, Any]:
        """對所有節點執行多頭感知，回傳完整感知場（node_id → fused_score）。"""
        if not self.nodes:
            return {"node_count": 0, "field": {}}
        # 以 mean 對角線（自感知）為每節點的多頭感知強度
        full: Dict[str, float] = {}
        for n in self.nodes:
            result = self.perceive(n)
            full[n["node_id"]] = result["fused_scores"].get(n["node_id"], 0.0)
        return {
            "origin_signature": ORIGIN_SIGNATURE,
            "subject": "MultiPerception",
            "head_count": len(self.heads),
            "node_count": len(full),
            "field": full,
            "top_node": max(full, key=lambda k: full[k]) if full else None,
        }
