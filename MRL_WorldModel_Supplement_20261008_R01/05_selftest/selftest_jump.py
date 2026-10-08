"""
selftest_jump.py — Jump service unit-level selftest（不綁 port）
origin_signature: MrLiouWord ｜ 2026-10-08

直接 import MRL_Jump_Service 的內部函式，用 tmpdir 當 ledger inbox。
不起 HTTP server，不打網路。沙盒可跑。
"""
from __future__ import annotations
import json
import os
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
sys.path.insert(0, str(ROOT / "01_jump"))

tmp = Path(tempfile.mkdtemp(prefix="mrl_jump_test_"))
os.environ["MRL_JUMP_INBOX"] = str(tmp)
os.environ["MRL_JUMP_SEEDMAP"] = str(ROOT / "01_jump" / "jump_seedmap.json")

import MRL_Jump_Service as J  # noqa


def ok(name, cond, detail=""):
    tag = "PASS" if cond else "FAIL"
    print(f"  [{tag}] {name}" + (f" — {detail}" if detail else ""))
    return cond


def main():
    print(f"[selftest_jump] origin_signature={J.ORIGIN_SIGNATURE} inbox={tmp}")
    all_ok = True

    # 1) seedmap 讀得到
    sm = J._load_seedmap()
    all_ok &= ok("seedmap load", sm.get("origin_signature") == "MrLiouWord")
    all_ok &= ok("seedmap has analyst_guardian",
                 "analyst_guardian" in sm.get("nodes", {}))

    # 2) tail hash on empty = GENESIS
    all_ok &= ok("tail_hash on empty is GENESIS", J._tail_hash() == "GENESIS")

    # 3) append 3 jumps
    r1 = J._append_jump({"from": "mrl_origin", "to": "analyst_guardian",
                         "rhythm": "seed_unfold", "actor": "builder",
                         "context": {"seed": "Mrl_Zero.Origin.v1"}})
    r2 = J._append_jump({"from": "analyst_guardian", "to": "world_memory",
                         "rhythm": "recall", "actor": "analyst_guardian"})
    r3 = J._append_jump({"from": "analyst_guardian", "to": "particle_globe",
                         "rhythm": "particle_bind", "actor": "analyst_guardian"})

    all_ok &= ok("seq=1 2 3",
                 [r1["ledger_seq"], r2["ledger_seq"], r3["ledger_seq"]] == [1, 2, 3])
    all_ok &= ok("r1 prev=GENESIS", r1["prev_hash"] == "GENESIS")
    all_ok &= ok("r2 prev==r1 this", r2["prev_hash"] == r1["this_hash"])
    all_ok &= ok("r3 prev==r2 this", r3["prev_hash"] == r2["this_hash"])

    # 4) verify chain
    v = J._verify_chain()
    all_ok &= ok("chain verify ok", v.get("ok") is True, f"total={v.get('total')}")

    # 5) tamper detection：改一行後 verify 要失敗
    led = tmp / "jump_ledger.jsonl"
    lines = led.read_text(encoding="utf-8").splitlines()
    # 把第 2 行的 context 改掉
    rec2 = json.loads(lines[1])
    rec2["context"] = {"tampered": True}
    lines[1] = json.dumps(rec2, ensure_ascii=False)
    led.write_text("\n".join(lines) + "\n", encoding="utf-8")
    v2 = J._verify_chain()
    all_ok &= ok("tamper detected", v2.get("ok") is False,
                 f"broken_at_line={v2.get('broken_at_line')}")

    # 6) read_ledger since=1 should return 2 entries（but we tampered, still
    #    structurally parsable, length check only）
    xs = J._read_ledger(since=1)
    all_ok &= ok("read_ledger since=1 len==2", len(xs) == 2)

    print(f"\n[selftest_jump] {'ALL PASS' if all_ok else 'FAIL'}")
    sys.exit(0 if all_ok else 1)


if __name__ == "__main__":
    main()
