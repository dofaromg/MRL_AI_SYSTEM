"""
selftest_collapse.py — Collapse service unit-level selftest
origin_signature: MrLiouWord ｜ 2026-10-08

Mock Jump service 回 ledger，然後跑 _collapse / _replay。
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
sys.path.insert(0, str(ROOT / "02_collapse"))

tmp = Path(tempfile.mkdtemp(prefix="mrl_collapse_test_"))
os.environ["MRL_COLLAPSE_OUT"] = str(tmp)

import MRL_Collapse_Service as C  # noqa


def ok(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    return cond


FAKE_JUMPS = [
    {"ledger_seq": 1, "jump_id": "jump_0000000001",
     "this_hash": "a" * 64, "rhythm": "seed_unfold"},
    {"ledger_seq": 2, "jump_id": "jump_0000000002",
     "this_hash": "b" * 64, "rhythm": "recall"},
    {"ledger_seq": 3, "jump_id": "jump_0000000003",
     "this_hash": "c" * 64, "rhythm": "particle_bind"},
]


def main():
    print(f"[selftest_collapse] origin_signature={C.ORIGIN_SIGNATURE} out={tmp}")
    all_ok = True

    with patch.object(C, "_fetch_jump_ledger", return_value=FAKE_JUMPS):
        r = C._collapse({"jump_since_seq": 0, "jump_until_seq": 10,
                         "node_states": {"analyst_guardian": "awake"},
                         "source_url": "test://fake"})
    all_ok &= ok("collapse returned id", r["collapse_id"] == "collapse_0000000001")
    all_ok &= ok("jump_count == 3", r["jump_count"] == 3)
    all_ok &= ok("state_hash is 64-hex len",
                 len(r["state_hash"]) == 64, r["state_hash"][:16])

    # fltnz 檔案真的在磁碟
    fp = Path(r["fltnz_path"])
    all_ok &= ok("fltnz written", fp.exists(), str(fp))
    env = json.loads(fp.read_text(encoding="utf-8"))
    all_ok &= ok("envelope magic", env.get("magic") == "FLTNZ-1")
    all_ok &= ok("envelope origin_signature",
                 env.get("origin_signature") == "MrLiouWord")

    # replay
    rp = C._replay("collapse_0000000001")
    all_ok &= ok("replay ok", rp.get("ok") is True)
    all_ok &= ok("replay state_hash_match", rp.get("state_hash_match") is True)
    all_ok &= ok("replay jump_count", rp.get("jump_count") == 3)
    all_ok &= ok("replay snapshot node_states carried",
                 rp.get("snapshot", {}).get("node_states", {}).get("analyst_guardian") == "awake")

    # list
    lst = C._list_collapses()
    all_ok &= ok("list has 1 item", len(lst) == 1)

    # 第二次 collapse 要產生新 id、不覆蓋
    with patch.object(C, "_fetch_jump_ledger", return_value=FAKE_JUMPS):
        r2 = C._collapse({"jump_since_seq": 0, "jump_until_seq": 10})
    all_ok &= ok("second collapse id = 2",
                 r2["collapse_id"] == "collapse_0000000002")
    all_ok &= ok("list has 2 items", len(C._list_collapses()) == 2)

    print(f"\n[selftest_collapse] {'ALL PASS' if all_ok else 'FAIL'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
