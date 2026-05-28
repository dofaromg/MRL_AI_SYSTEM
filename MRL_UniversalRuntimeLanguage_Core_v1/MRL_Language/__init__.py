# MRL_Language layer
# origin_signature: MrLiouWord
"""語言層：UniversalParser → MetaIR → ParticleIR → PerceptionKernel。

Canonical 名稱對接（不得產生平行命名）：以下短名為「同一實作」之正式別名，
全 repo 對 MetaIR / ParticleIR 概念只指向這一份實作。
    MRL_MetaIR      → MRL_MetaIR_Compiler
    MRL_ParticleIR  → MRL_ParticleIR_Engine
    MRL_UniversalParser_Core 已為正式名（無別名）
"""

from . import MRL_MetaIR_Compiler, MRL_ParticleIR_Engine, MRL_PerceptionKernel, MRL_UniversalParser_Core

# Canonical 短名別名（單一真實來源，無平行實作）
MRL_MetaIR = MRL_MetaIR_Compiler
MRL_ParticleIR = MRL_ParticleIR_Engine

__all__ = [
    "MRL_UniversalParser_Core",
    "MRL_MetaIR_Compiler",
    "MRL_ParticleIR_Engine",
    "MRL_PerceptionKernel",
    "MRL_MetaIR",
    "MRL_ParticleIR",
]
