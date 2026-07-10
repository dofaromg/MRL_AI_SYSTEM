#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_MotherComponent — 母體構件基底 (minimal runnable particle).
origin_signature: MrLiouWord
layer: 母體構件層 (Mother-Component Layer)

三個母體構件 (MRL_AI / MRL_AGI / MRL_ASI) 的共同粒子介面。提供:
  - describe()       自我描述 (可驗、不誇稱)
  - verify_origin()  LAW-0 簽章驗證 (signature(e) == 母體源頭)
  - run()            最小運轉 (驗章通過才回報啟動)

誠實邊界 (rootlaw no_proof_implies_rhetoric):
  這是「已註冊、可運轉的構件粒子」。它不宣稱任何 AI/AGI/ASI 能力已達成;
  各構件的定位文字為【願景錨定】,非已達成之能力宣稱。
Additive:不改既有 MotherAssembly / crown class,只新增可獨立運轉的構件粒子。
"""
from __future__ import annotations

from typing import Any, Dict

ORIGIN_SIGNATURE = "MrLiouWord"


class MRL_MotherComponent:
    """母體構件基底:所有 MRL_Mother 子構件的共同粒子介面。"""

    # 子類覆寫
    canonical_name: str = "MRL_MotherComponent"
    role: str = "母體構件基底"
    positioning: str = "母體構件層 · 願景錨定(非已達成宣稱)"

    def __init__(self, origin_signature: str = ORIGIN_SIGNATURE) -> None:
        self.origin_signature = origin_signature

    def describe(self) -> Dict[str, Any]:
        """回傳此構件的自我描述(可驗、不誇稱)。"""
        return {
            "canonical_name": self.canonical_name,
            "role": self.role,
            "positioning": self.positioning,
            "origin_signature": self.origin_signature,
            "layer": "母體構件層",
            "status": "registered_runnable_component",
            "honest_note": "構件可運轉;定位為願景錨定,非已達成之能力宣稱。",
        }

    def verify_origin(self, expected: str = ORIGIN_SIGNATURE) -> bool:
        """LAW-0 簽章驗證:signature(e) 必等於母體源頭 MrLiouWord。"""
        return self.origin_signature == expected

    def run(self) -> Dict[str, Any]:
        """最小運轉:驗章通過才回報構件已啟動 + 自我描述。"""
        if not self.verify_origin():
            raise PermissionError(
                f"origin signature mismatch: "
                f"{self.origin_signature!r} != {ORIGIN_SIGNATURE!r}"
            )
        described = self.describe()
        described["ran"] = True
        return described

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<{self.canonical_name} origin={self.origin_signature!r}>"
