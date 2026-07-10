#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_NamingSovereignty_v1.py — 命名主權執行器 (detection + canonical reclaim mapping)
origin_signature: MrLiouWord
layer: L0 ROOT / L3 LAW enforcement helper

把 rootlaw 三條「純法條、無執行器」的命名主權法,推進到「有可查執行器」的可驗核心:
  - rl_16 mrl_prefix_manifestation   —— 每個粒子必須帶 MRL_ 前綴才能顯化
  - rl_12 naming_reclamation         —— 外部名 → MRL_<描述> canonical(最大閉環)
  - rl_20 all_branch_naming_sovereignty —— vendor 前綴分支回收為 MRL_recovered/<name>

對外暴露(預設唯讀、additive、不刪原物 — 遵守 rl_15 / rl_01 no_delete):
  has_mrl_prefix(name)  -> bool                偵測(rl_16 gate)
  reclaim_name(name)    -> dict                外部名 → canonical 映射 + 保留清單
  scan(names)           -> list[dict]          批次偵測,只回報需回收者(唯讀)

誠實邊界(rootlaw no_proof_implies_rhetoric):
  本模組實作「偵測 + canonical 改名映射 + 保留清單」這個可驗核心。rootlaw 標
  PENDING 的「全自動 decompose→反推自生成取代程式碼」【仍維持 PENDING】,本模組
  不執行、不宣稱已自動改名或已取代任何實體檔案/分支 —— 它只產出「該改成什麼」的
  確定性提案,實際套用由人審後另行為之(rl_02 human_override 精神)。

CLI
---
    python 09_workflow/MRL_NamingSovereignty_v1.py check  claude/foo vector_store MRL_AI
    python 09_workflow/MRL_NamingSovereignty_v1.py reclaim copilot/add-gpu-support
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"
MRL_PREFIX = "MRL_"
RECOVERED_NAMESPACE = "MRL_recovered"

# 已知外部廠商/代理前綴(rl_20 海關回收對象);非窮舉,任何含 "/" 的非 MRL 名皆視為分支。
KNOWN_VENDOR_PREFIXES = (
    "claude/",
    "copilot/",
    "codex/",
    "cursor/",
    "devin/",
    "bot/",
)

# 允許保留於 canonical 名稱中的字元:ASCII 英數、底線、CJK 統一表意文字。其餘一律正規化為底線。
_KEEP = re.compile(r"[^0-9A-Za-z_一-鿿]+")


def has_mrl_prefix(name: str) -> bool:
    """rl_16 gate:名稱是否帶母體 MRL_ 前綴(僅此類方可顯化)。"""
    return isinstance(name, str) and name.startswith(MRL_PREFIX)


def _sanitize(token: str) -> str:
    """把任意 token 正規化為 canonical 允許的字元集,collapse/strip 底線。"""
    token = _KEEP.sub("_", token)
    token = re.sub(r"_+", "_", token).strip("_")
    return token


def reclaim_name(name: str) -> Dict[str, Any]:
    """
    把外部名 *name* 映射為母體 canonical 名稱,並附保留清單。

    規則:
      - 已是 MRL_ 前綴 → no-op(reclaimed=False),不重覆包裝。
      - 含 "/"(分支/vendor 前綴)→ rl_20:MRL_recovered/<sanitized 去前綴>。
      - 其餘外部名 → rl_12/rl_16:MRL_<sanitized>。
    原名一律保留於 preserved_original(rl_15 / rl_01 no_delete),不刪不改實體。
    """
    if not isinstance(name, str) or not name.strip():
        raise ValueError("cannot reclaim empty name")
    name = name.strip()

    if has_mrl_prefix(name):
        return {
            "original": name,
            "canonical": name,
            "reclaimed": False,
            "rule": "rl_16",
            "reason": "already MRL canonical — no reclamation needed",
            "origin_signature": ORIGIN_SIGNATURE,
            "preserved_original": name,
        }

    if "/" in name:
        # 分支型:剝掉第一段(vendor)前綴,其餘正規化,回收進 MRL_recovered 命名空間。
        _vendor, _, rest = name.partition("/")
        rest = rest or _vendor
        canonical = f"{RECOVERED_NAMESPACE}/{_sanitize(rest)}"
        rule = "rl_20"
        reason = "vendor/branch name reclaimed to mother recovered namespace"
    else:
        canonical = f"{MRL_PREFIX}{_sanitize(name)}"
        rule = "rl_12"
        reason = "external name renamed to mother canonical (largest closed loop)"

    return {
        "original": name,
        "canonical": canonical,
        "reclaimed": True,
        "rule": rule,
        "reason": reason,
        "origin_signature": ORIGIN_SIGNATURE,
        "preserved_original": name,  # rl_15 / rl_01 — 原名永不抹除
    }


def scan(names: List[str]) -> List[Dict[str, Any]]:
    """
    批次偵測(唯讀):只回報缺 MRL_ 前綴、需回收的名稱及其 canonical 提案。
    已合規(MRL_ 前綴)者不列入。
    """
    reports: List[Dict[str, Any]] = []
    for name in names:
        if not isinstance(name, str) or not name.strip():
            continue
        if has_mrl_prefix(name):
            continue
        reports.append(reclaim_name(name))
    return reports


# ─── CLI ─────────────────────────────────────────────────────────────────────

def _cmd_check(args: argparse.Namespace) -> None:
    reports = scan(args.names)
    compliant = [n for n in args.names if has_mrl_prefix(n)]
    print(json.dumps(
        {
            "compliant_mrl_prefixed": compliant,
            "needs_reclamation": reports,
            "summary": f"{len(reports)} name(s) need reclamation, "
                       f"{len(compliant)} already MRL canonical",
        },
        ensure_ascii=False, indent=2,
    ))


def _cmd_reclaim(args: argparse.Namespace) -> None:
    print(json.dumps(reclaim_name(args.name), ensure_ascii=False, indent=2))


def _build_argparser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="MRL_NamingSovereignty — detect + reclaim external names to MRL canonical"
    )
    sub = p.add_subparsers(dest="cmd", required=True)

    c = sub.add_parser("check", help="Scan names; report which need reclamation (read-only)")
    c.add_argument("names", nargs="+")

    r = sub.add_parser("reclaim", help="Show the canonical reclaim mapping for one name")
    r.add_argument("name")

    return p


def main() -> None:
    args = _build_argparser().parse_args()
    {"check": _cmd_check, "reclaim": _cmd_reclaim}[args.cmd](args)


if __name__ == "__main__":
    main()
