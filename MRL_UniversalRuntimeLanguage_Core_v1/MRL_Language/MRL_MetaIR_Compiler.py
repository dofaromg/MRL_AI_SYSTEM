# MRL_MetaIR_Compiler
# origin_signature: MrLiouWord
# layer: MRL_Language
"""MetaIR 編譯器：ParseResult → SemanticIR → ContextIR → IntentIR → MetaIR。

非單純 AST parser：在結構之上推導語意角色(Semantic)、上下文關係(Context)、
意圖(Intent)，再收斂為穩定可重現的 MetaIR（每節點具確定性 node_id 與 content hash）。
確定性保證：相同輸入永遠產生相同 MetaIR（replay/verify 之根據）。
"""

from __future__ import annotations

import hashlib
from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"

# unit.kind → 語意角色
_SEMANTIC_ROLE = {
    "heading": "structure",
    "list_item": "enumeration",
    "paragraph": "narrative",
    "object": "container",
    "array": "sequence",
    "scalar": "datum",
    "def": "definition",
    "class": "definition",
    "import": "dependency",
    "assign": "binding",
    "control": "control_flow",
    "call": "invocation",
    "stmt": "statement",
    "line": "statement",
}

# 語意角色 → 意圖
_INTENT = {
    "structure": "organize",
    "enumeration": "enumerate",
    "narrative": "describe",
    "container": "hold",
    "sequence": "order",
    "datum": "store",
    "definition": "declare",
    "dependency": "require",
    "binding": "assign",
    "control_flow": "branch",
    "invocation": "execute",
    "statement": "evaluate",
}


def _node_id(index: int, content_hash: str) -> str:
    return f"n{index:04d}_{content_hash[:8]}"


def _content_hash(text: str, kind: str) -> str:
    return hashlib.sha256(f"{kind}|{text}".encode("utf-8")).hexdigest()


def _semantic_role(kind: str) -> str:
    if kind.startswith("particle:"):
        return "particle"
    return _SEMANTIC_ROLE.get(kind, "statement")


def compile_metair(parse_result: Dict[str, Any]) -> Dict[str, Any]:
    """ParseResult → MetaIR（含 semantic/context/intent 三層收斂）。"""
    units: List[Dict[str, Any]] = parse_result.get("units", [])
    nodes: List[Dict[str, Any]] = []

    # 上下文堆疊：依 depth 維護 parent 關係
    parent_stack: List[str] = []  # (depth, node_id) 以 list 模擬
    depth_to_id: Dict[int, str] = {}

    for i, u in enumerate(units):
        text = u.get("text", "")
        kind = u.get("kind", "statement")
        depth = int(u.get("depth", 0))
        chash = _content_hash(text, kind)
        nid = _node_id(i, chash)

        role = _semantic_role(kind)            # SemanticIR
        intent = _INTENT.get(role, "evaluate") if not role == "particle" else "particle_flow"  # IntentIR

        # ContextIR：parent = 最近的較淺節點
        parent = None
        for d in range(depth - 1, -1, -1):
            if d in depth_to_id:
                parent = depth_to_id[d]
                break
        depth_to_id[depth] = nid
        # 清掉比目前更深的層級記錄（離開該 scope）
        for d in list(depth_to_id.keys()):
            if d > depth:
                del depth_to_id[d]

        nodes.append({
            "node_id": nid,
            "index": i,
            "semantic": {"kind": kind, "role": role},
            "context": {"depth": depth, "parent": parent},
            "intent": intent,
            "content": text,
            "content_hash": chash,
        })

    metair_hash = hashlib.sha256(
        "".join(n["node_id"] for n in nodes).encode("utf-8")
    ).hexdigest()

    return {
        "metair_version": "1.0",
        "origin_signature": ORIGIN_SIGNATURE,
        "lang": parse_result.get("lang"),
        "source_checksum": parse_result.get("raw_checksum"),
        "node_count": len(nodes),
        "metair_hash": metair_hash,
        "nodes": nodes,
    }
