# MRL_RuntimeGraph_Builder
# origin_signature: MrLiouWord
# layer: MRL_Runtime
"""RuntimeGraph 建構：MetaIR → execution graph / replay graph / restore graph / world graph。

graph 結構（確定性）：
    nodes: [node_id, ...]
    edges: [(src, dst, kind), ...]   kind ∈ {seq, context}
    replay_graph:  依觀察序的 op 串列（可精確重播）
    restore_graph: checkpoint 標記點
    world_graph:   node_id → world 標籤
另提供 to_mermaid() / to_dot() / to_json() 視覺化輸出。
"""

from __future__ import annotations

import hashlib
import json
from typing import Any, Dict, List, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"


def build(metair: Dict[str, Any], observation_order: List[str] | None = None) -> Dict[str, Any]:
    nodes = metair.get("nodes", [])
    node_ids = [n["node_id"] for n in nodes]
    id_to_node = {n["node_id"]: n for n in nodes}

    edges: List[Tuple[str, str, str]] = []
    # 序列邊（執行順序）
    for a, b in zip(node_ids, node_ids[1:]):
        edges.append((a, b, "seq"))
    # 上下文邊（parent → child）
    for n in nodes:
        parent = n["context"]["parent"]
        if parent:
            edges.append((parent, n["node_id"], "context"))

    order = observation_order or node_ids
    replay_graph = [
        {"step": i, "node_id": nid, "intent": id_to_node[nid]["intent"], "hash": id_to_node[nid]["content_hash"]}
        for i, nid in enumerate(order)
        if nid in id_to_node
    ]
    # restore checkpoints：每個 definition 節點與每 8 步設一個 checkpoint
    restore_graph = [
        step["node_id"]
        for step in replay_graph
        if id_to_node[step["node_id"]]["semantic"]["role"] == "definition" or step["step"] % 8 == 0
    ]
    world_graph = {
        n["node_id"]: ("core_world" if n["semantic"]["role"] == "definition" else "context_world")
        for n in nodes
    }

    graph = {
        "graph_version": "1.0",
        "origin_signature": ORIGIN_SIGNATURE,
        "node_count": len(node_ids),
        "edge_count": len(edges),
        "nodes": node_ids,
        "edges": edges,
        "replay_graph": replay_graph,
        "restore_graph": restore_graph,
        "world_graph": world_graph,
    }
    graph["graph_hash"] = hashlib.sha256(
        json.dumps([graph["nodes"], graph["edges"]], ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()
    return graph


def to_mermaid(graph: Dict[str, Any], max_nodes: int = 60) -> str:
    lines = ["graph TD"]
    shown = set(graph["nodes"][:max_nodes])
    for (src, dst, kind) in graph["edges"]:
        if src in shown and dst in shown:
            arrow = "-->" if kind == "seq" else "-.->"
            lines.append(f'    {src}{arrow}{dst}')
    if len(graph["nodes"]) > max_nodes:
        lines.append(f'    note["... {len(graph["nodes"]) - max_nodes} more nodes truncated"]')
    return "\n".join(lines)


def to_dot(graph: Dict[str, Any]) -> str:
    lines = ["digraph MRL_RuntimeGraph {", '  rankdir=TB;']
    for (src, dst, kind) in graph["edges"]:
        style = "" if kind == "seq" else ' [style=dashed]'
        lines.append(f'  "{src}" -> "{dst}"{style};')
    lines.append("}")
    return "\n".join(lines)


def to_json(graph: Dict[str, Any]) -> str:
    return json.dumps(graph, ensure_ascii=False, indent=2)
