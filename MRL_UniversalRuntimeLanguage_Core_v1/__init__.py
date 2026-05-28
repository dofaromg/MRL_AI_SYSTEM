# MRL_UniversalRuntimeLanguage_Core_v1
# origin_signature: MrLiouWord
# 主體：MRL_Mother_Runtime；部署主體：DL580。
# Cloudflare / Cloudflared / XOOPZ / GitHub / Claude 皆為 MRL_External_Mirror_Layer，不得成為主體。
"""MRL_UniversalRuntimeLanguage_Core_v1 — Runtime Civilization Stack 核心。

正式 Runtime 管線（不允許 Prompt→LLM→Output）：

    Input → Observe → Parse → MetaIR → ParticleIR → RuntimeGraph
          → Verification → Replay → Restore → WorldRuntime → PersistentLoop
"""

ORIGIN_SIGNATURE = "MrLiouWord"
SYSTEM_NAME = "MRL_UniversalRuntimeLanguage_Core_v1"
SOVEREIGNTY_MODE = "權位區分模式"

# 主體 / 鏡像層權位定位（不可重新定義母體）
SOVEREIGNTY = {
    "subject": "MRL_Mother_Runtime",
    "deploy_host": "DL580",
    "external_mirror_layer": [
        "Cloudflare",
        "Cloudflared",
        "XOOPZ",
        "GitHub",
        "Claude",
    ],
    "perception_is_subject": True,   # 正式主體詞 = Perception
    "attention_is_history_adapter": True,  # Attention 僅作歷史層 / Adapter 層
}

# Canonical 名稱對接（不得產生平行命名）
# 左：正式 canonical 模組（單一真實來源）｜右：既有 repo 概念目錄（README 骨架，指向左側實作）
CANONICAL_NAME_MAP = {
    "MRL_UniversalParser_Core": "MRL_Language/MRL_UniversalParser_Core.py",
    "MRL_MetaIR": "MRL_Language/MRL_MetaIR_Compiler.py",
    "MRL_ParticleIR": "MRL_Language/MRL_ParticleIR_Engine.py（粒子層對應 MRL_Symbolic/MRL_粒子語言層）",
    "MRL_RuntimeGraph": "MRL_Runtime/MRL_RuntimeGraph_Builder.py（對應 MRL_Runtime/MRL_運轉圖譜）",
    "MRL_PerceptionKernel": "MRL_Language/MRL_PerceptionKernel.py（對應 MRL_Runtime/MRL_感知力核心）",
    "MRL_ReplayRestore": "MRL_Runtime/MRL_ReplayRestore_Core.py（對應 MRL_Runtime/MRL_回放回復）",
    "MRL_Verification": "MRL_Runtime/MRL_Verification.py（對應 MRL_Runtime/MRL_驗證層）",
    "MRL_WorldRuntime": "MRL_Runtime/MRL_WorldRuntime.py（對應 MRL_Runtime/MRL_多世界同步）",
}

CANONICAL_PIPELINE = [
    "Input",
    "Observe",
    "Parse",
    "MetaIR",
    "ParticleIR",
    "RuntimeGraph",
    "Verification",
    "Replay",
    "Restore",
    "WorldRuntime",
    "PersistentLoop",
]

__all__ = [
    "ORIGIN_SIGNATURE",
    "SYSTEM_NAME",
    "SOVEREIGNTY_MODE",
    "SOVEREIGNTY",
    "CANONICAL_NAME_MAP",
    "CANONICAL_PIPELINE",
]
