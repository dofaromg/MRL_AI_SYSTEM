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
    "CANONICAL_PIPELINE",
]
