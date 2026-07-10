#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_MotherComponent — 母體構件基底 (minimal runnable particle).
origin_signature: MrLiouWord
layer: 母體構件層 (Mother-Component Layer)

三個母體構件 (MRL_AI / MRL_AGI / MRL_ASI) 的共同粒子介面。提供:
  - describe()        自我描述 (可驗、不誇稱)
  - signed_describe() LAW-0 embedSignature 後的自我描述 (竄改可偵測)
  - verify_origin()   LAW-0 驗證 (origin 相符 + sha256 簽章驗章)
  - run()             最小運轉 (驗章通過才回報啟動)

簽章來源:origin_signature 與 LAW-0 embed/verify 皆自 09_workflow/MRL_utils.py 匯入
(single source of truth;authority_invariance,不在此重定義)。standalone/測試若
無 09_workflow 於路徑,以位元相容 fallback 保底。

誠實邊界 (rootlaw no_proof_implies_rhetoric):
  這是「已註冊、可運轉的構件粒子」。它不宣稱任何 AI/AGI/ASI 能力已達成;
  各構件的定位文字為【願景錨定】,非已達成之能力宣稱。
  verify_origin 為 origin 身分相符 + LAW-0 sha256 完整性驗章,非公鑰認證邊界。
Additive:不改既有 MotherAssembly / crown class,只新增可獨立運轉的構件粒子。
"""
from __future__ import annotations

import pathlib
import sys
from typing import Any, Dict

# 讓 in-repo 與測試皆能匯入 09_workflow/MRL_utils.py;guarded insert 避免重複與擾動 import 序。
_HERE = pathlib.Path(__file__).resolve()
for _p in (str(_HERE.parents[1] / "09_workflow"), str(_HERE.parent)):
    if _p not in sys.path:
        sys.path.insert(0, _p)

try:
    from MRL_utils import ORIGIN_SIGNATURE, embed_signature, verify_signature  # noqa: E402
except Exception:  # pragma: no cover - fallback only when MRL_utils unavailable
    import hashlib as _hashlib
    import json as _json

    ORIGIN_SIGNATURE = "MrLiouWord"

    def _compact(obj: Dict[str, Any]) -> str:  # byte-compatible mirror of MRL_utils
        return _json.dumps(obj, separators=(",", ":"), ensure_ascii=False)

    def embed_signature(obj: Dict[str, Any], sig: str = ORIGIN_SIGNATURE) -> Dict[str, Any]:
        h = _hashlib.sha256((sig + ":" + _compact(obj)).encode("utf-8")).hexdigest()
        return {**obj, "_signature": sig, "_sig_hash": h}

    def verify_signature(obj: Dict[str, Any], expected_sig: str = ORIGIN_SIGNATURE) -> bool:
        ss, sh = obj.get("_signature"), obj.get("_sig_hash")
        if not ss or not sh or ss != expected_sig:
            return False
        base = {k: v for k, v in obj.items() if k not in ("_signature", "_sig_hash")}
        exp = _hashlib.sha256((expected_sig + ":" + _compact(base)).encode("utf-8")).hexdigest()
        return exp == sh


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

    def signed_describe(self) -> Dict[str, Any]:
        """LAW-0 embedSignature over describe():附 _signature/_sig_hash,竄改任一欄位皆可偵測。"""
        return embed_signature(self.describe(), self.origin_signature)

    def verify_origin(self, expected: str = ORIGIN_SIGNATURE) -> bool:
        """LAW-0 驗證:origin 身分相符 且 自我描述之 sha256 簽章驗章通過。

        非公鑰認證邊界;但相較裸字串比對,竄改 signed_describe() 任一欄位會使
        verify_signature 重雜湊比對失敗。
        """
        signed = embed_signature(self.describe(), self.origin_signature)
        return self.origin_signature == expected and verify_signature(signed, expected)

    def run(self) -> Dict[str, Any]:
        """最小運轉:驗章通過才回報構件已啟動 + 自我描述。"""
        if not self.verify_origin():
            raise PermissionError(
                f"origin signature mismatch/verify failed: "
                f"{self.origin_signature!r} != {ORIGIN_SIGNATURE!r}"
            )
        described = self.describe()
        described["ran"] = True
        return described

    def __repr__(self) -> str:  # pragma: no cover - trivial
        return f"<{self.canonical_name} origin={self.origin_signature!r}>"
