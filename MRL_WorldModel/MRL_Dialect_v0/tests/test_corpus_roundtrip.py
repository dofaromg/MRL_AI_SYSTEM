"""
全語料可逆測試：每個 .pcode / .fltnz / .flynz.map 檔
  bytes → mrl Dialect IR → bytes，必須逐位元組相同；IR 再印一次也必須相同（固定點）。
用法：python3 tests/test_corpus_roundtrip.py [root ...]   （預設：母體 repo 根目錄）
origin_signature: MrLiouWord
"""
import collections
import hashlib
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import mrl_dialect as D  # noqa: E402

EXTS = (".pcode", ".fltnz", ".flynz.map")


def collect(roots):
    seen = {}
    for root in roots:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in (".git", "node_modules")]
            for fn in fns:
                if fn.lower().endswith(EXTS):
                    p = os.path.join(dp, fn)
                    b = open(p, "rb").read()
                    seen.setdefault(hashlib.sha256(b).hexdigest(), (p, b))
    return seen


def main(roots):
    files = collect(roots)
    kinds = collections.Counter()
    fails = []
    for h, (p, b) in sorted(files.items(), key=lambda x: x[1][0]):
        ok, ir = D.roundtrip(b, os.path.basename(p))
        ir2 = D.print_ir(D.parse_ir(ir))
        if not ok or ir2 != ir:
            fails.append(p)
        for o in D.parse_ir(ir).ops:
            kinds[o.kind] += 1
    report = {
        "dialect_version": D.DIALECT_VERSION,
        "unique_files": len(files),
        "roundtrip_pass": len(files) - len(fails),
        "roundtrip_fail": len(fails),
        "failed": fails,
        "op_kinds": dict(kinds.most_common()),
    }
    print(json.dumps(report, ensure_ascii=False, indent=1))
    return 0 if not fails and files else 1


if __name__ == "__main__":
    roots = sys.argv[1:] or [os.path.abspath(os.path.join(HERE, "..", "..", ".."))]
    sys.exit(main(roots))
