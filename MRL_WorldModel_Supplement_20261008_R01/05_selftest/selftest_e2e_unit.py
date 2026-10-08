"""
selftest_e2e_unit.py — Jump → Collapse → Replay 端到端（unit-level）
origin_signature: MrLiouWord ｜ 2026-10-08

直接 import 兩個模組；Collapse 的 _fetch_jump_ledger patch 成讀 Jump 的
真 ledger（都在 tmpdir）。不起 server，不打網路。
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "01_jump"))
sys.path.insert(0, str(ROOT / "02_collapse"))

jump_tmp = Path(tempfile.mkdtemp(prefix="mrl_jump_e2e_"))
coll_tmp = Path(tempfile.mkdtemp(prefix="mrl_coll_e2e_"))
os.environ["MRL_JUMP_INBOX"] = str(jump_tmp)
os.environ["MRL_JUMP_SEEDMAP"] = str(ROOT / "01_jump" / "jump_seedmap.json")
os.environ["MRL_COLLAPSE_OUT"] = str(coll_tmp)

import MRL_Jump_Service as J  # noqa
import MRL_Collapse_Service as C  # noqa


def ok(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    return cond


def main():
    print(f"[selftest_e2e] origin_signature={J.ORIGIN_SIGNATURE}")
    print(f"  jump_tmp={jump_tmp}")
    print(f"  coll_tmp={coll_tmp}")
    all_ok = True

    # 1) 連跳 5 次
    for i, (frm, to, rhythm) in enumerate([
        ("mrl_origin", "analyst_guardian", "seed_unfold"),
        ("analyst_guardian", "world_memory", "recall"),
        ("analyst_guardian", "particle_globe", "particle_bind"),
        ("world_memory", "worldloop", "stream"),
        ("worldloop", "analyst_guardian", "trace_return"),
    ], 1):
        r = J._append_jump({"from": frm, "to": to, "rhythm": rhythm,
                            "actor": "builder" if frm == "mrl_origin" else frm})
        all_ok &= ok(f"jump {i} appended", r["ledger_seq"] == i)

    # 2) verify chain
    v = J._verify_chain()
    all_ok &= ok("chain verify ok", v["ok"] is True, f"total={v['total']}")

    # 3) collapse 全部 5 跳
    def fake_fetch(since, until):
        return J._read_ledger(since=since, limit=10000)

    with patch.object(C, "_fetch_jump_ledger", side_effect=fake_fetch):
        res = C._collapse({"jump_since_seq": 0, "jump_until_seq": 100,
                           "node_states": {"analyst_guardian": "awake"},
                           "source_url": "DL580/e2e_test"})
    all_ok &= ok("collapse captured 5 jumps", res["jump_count"] == 5)
    all_ok &= ok("fltnz written", Path(res["fltnz_path"]).exists())

    # 4) replay 後 state_hash 要相同
    rp = C._replay(res["collapse_id"])
    all_ok &= ok("replay ok", rp["ok"] is True)
    all_ok &= ok("replay state_hash matches", rp["state_hash_match"] is True)
    all_ok &= ok("replay rhythm_pattern preserved",
                 rp["snapshot"]["node_states"]["analyst_guardian"] == "awake")

    # 5) 本體/載體邊界：直接呼叫 _append_jump 不會擋（內層不過濾），
    #    HTTP 層會過濾。驗證 HTTP layer 的邊界邏輯：載體 node 的 kind
    sm = J._load_seedmap()
    nodes = sm["nodes"]
    for carrier in ("world_memory", "worldloop", "particle_globe"):
        all_ok &= ok(f"{carrier} kind=載體", nodes[carrier]["kind"] == "載體")
    for ontic in ("mrl_origin", "analyst_guardian"):
        all_ok &= ok(f"{ontic} kind=本體", nodes[ontic]["kind"] == "本體")

    print(f"\n[selftest_e2e] {'ALL PASS' if all_ok else 'FAIL'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
