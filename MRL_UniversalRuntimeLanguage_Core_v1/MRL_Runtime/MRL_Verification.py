# MRL_Verification
# origin_signature: MrLiouWord
# layer: MRL_Runtime
"""驗證層：roundtrip / proof / trace / runtime / world consistency 驗證。

對 RuntimeResult 執行六項驗收（與 acceptance/§10 對齊），全通過輸出：
    MRL_RUNTIME_ACCEPTANCE_PASS
"""

from __future__ import annotations

from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"
ACCEPTANCE_TOKEN = "MRL_RUNTIME_ACCEPTANCE_PASS"


def verify(result: Dict[str, Any]) -> Dict[str, Any]:
    checks: List[Dict[str, Any]] = []

    def add(name: str, passed: bool, detail: str) -> None:
        checks.append({"check": name, "pass": bool(passed), "detail": detail})

    graph = result.get("graph", {})
    add(
        "A_RuntimeGraph_build",
        graph.get("node_count", 0) > 0 and bool(graph.get("graph_hash")),
        f"node_count={graph.get('node_count')} graph_hash={str(graph.get('graph_hash'))[:8]}",
    )

    replay = result.get("replay", {})
    add("B_Replay_exactness", replay.get("exact") is True, f"replay.hash={str(replay.get('hash'))[:8]}")

    restore = result.get("restore", {})
    add("C_Restore_exactness", restore.get("exact") is True,
        f"from_step={restore.get('from_step')} restore.hash={str(restore.get('hash'))[:8]}")

    ploop = result.get("persistent_loop", {})
    add("D_PersistentLoop_survives_restart", ploop.get("survives_restart") is True,
        f"iteration={ploop.get('iteration')}")

    world = result.get("world", {})
    add("E_WorldRuntime_synchronization", world.get("synchronization_active") is True,
        f"world_count={world.get('world_count')}")

    rt = result.get("roundtrip", {})
    add("F_Verification_roundtrip_exact", rt.get("exact") is True,
        f"roundtrip checksum match={rt.get('exact')}")

    all_pass = all(c["pass"] for c in checks)
    return {
        "origin_signature": ORIGIN_SIGNATURE,
        "checks": checks,
        "passed": sum(1 for c in checks if c["pass"]),
        "total": len(checks),
        "acceptance": all_pass,
        "token": ACCEPTANCE_TOKEN if all_pass else "MRL_RUNTIME_ACCEPTANCE_FAIL",
    }
