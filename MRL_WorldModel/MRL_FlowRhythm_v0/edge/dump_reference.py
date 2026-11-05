"""
FlowRhythm edge 一致性驗收：由本體 flow_rhythm.py（權威）產出參考值，供 JS 載體逐位元組比對。
只用母體自己的 6 顆種子（同 tests/test_rhythm.py 的 E 段）。輸出寫到 argv[1]（臨時目錄），不碰 traces/。
origin_signature: MrLiouWord
"""
import json, os, sys, zipfile
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import flow_rhythm as F
L = F.load_lexicon(); LEX = F.LEX_DIR
FIX = "2025-07-23T19:41:36.746707Z"
runs = []
for n in ("下載 EchoPersona.pcode", "下載 EchoPersona.Sample.v1.flpkg", "下載 FluinCoreSeed.v1.flseed", "下載 Memory.Seed.Core.v1.flseed"):
    ch, _ = F.load_seed(os.path.join(LEX, n), L); runs.append((n.replace("下載 ", ""), ch, None))
with zipfile.ZipFile(os.path.join(LEX, "重新下載 FluinSim.DualSet.v1.flsim")) as z:
    for g in ("Group1_EchoPersona", "Group2_ConflictChange"):
        t = z.read(g + ".fltnz").decode("utf-8")
        runs.append((g, F.chain_from_fltnz(t), t))
out = []
for name, ch, src in runs:
    r = F.run(ch, L, F.Clock(FIX), name, allow_provisional=True)
    out.append({"name": name, "chain": ch, "fltnz_source": src, "trace_fltnz": r["trace_fltnz"],
                "final_sha256": r["final_sha256"], "narration": r["narration"],
                "packets": r["field"]["packets"]})
json.dump({"fixed_clock": FIX, "runs": out}, open(sys.argv[1], "w", encoding="utf-8"), ensure_ascii=False)
