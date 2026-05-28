# MRL_Runtime layer
# origin_signature: MrLiouWord
"""運轉層：RuntimeGraph / PersistentLoop / ReplayRestore / Verification / WorldRuntime / DL580_Runtime。

Canonical 名稱對接（不得產生平行命名）：
    MRL_RuntimeGraph → MRL_RuntimeGraph_Builder
"""

from . import MRL_RuntimeGraph_Builder

# Canonical 短名別名（單一真實來源）
MRL_RuntimeGraph = MRL_RuntimeGraph_Builder

__all__ = [
    "MRL_RuntimeGraph_Builder",
    "MRL_RuntimeGraph",
]
