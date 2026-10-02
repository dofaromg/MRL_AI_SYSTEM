"""重新產生 SEED_SHA256SUMS（receipts 與 sums 本身除外）。origin_signature: MrLiouWord"""
import hashlib, os
SEED = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
rows = []
for dp, dns, fns in os.walk(SEED):
    dns[:] = sorted(d for d in dns if d not in ("receipts", "__pycache__"))
    for fn in sorted(fns):
        if fn == "SEED_SHA256SUMS":
            continue
        p = os.path.join(dp, fn)
        rel = os.path.relpath(p, SEED).replace(os.sep, "/")
        rows.append(f"{hashlib.sha256(open(p, 'rb').read()).hexdigest()}  {rel}")
open(os.path.join(SEED, "SEED_SHA256SUMS"), "w", encoding="utf-8", newline="\n").write("\n".join(rows) + "\n")
print(len(rows), "files")
