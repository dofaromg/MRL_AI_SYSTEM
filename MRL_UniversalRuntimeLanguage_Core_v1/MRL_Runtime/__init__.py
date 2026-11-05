# MRL_Runtime layer
# origin_signature: MrLiouWord
"""運轉層：RuntimeStructureField / PersistentLoop / ReplayRestore / Verification / WorldRuntime / DL580_Runtime。

Canonical 名稱（v2，單一真實來源）：
    MRL_RuntimeStructureField  → MRL_RuntimeStructureField（結構場）

Compatibility alias（歷史名稱，非 canonical 主體）：
    MRL_RuntimeGraph           → MRL_RuntimeStructureField（= Graph Adapter）
"""

from . import MRL_RuntimeStructureField

# Canonical（單一真實來源）
# （MRL_RuntimeStructureField 本身即模組名）

# Compatibility alias layer（Graph = 歷史/Adapter，僅向後兼容）
from . import MRL_RuntimeGraph_Builder  # noqa: E402  (alias shim module)
MRL_RuntimeGraph = MRL_RuntimeStructureField

__all__ = [
    "MRL_RuntimeStructureField",
    # compatibility alias
    "MRL_RuntimeGraph",
    "MRL_RuntimeGraph_Builder",
]
