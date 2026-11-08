"""反向：本體 Python Replay 讀 JS 載體寫出的軌跡（argv[1] JSON: [{name, trace}]）。"""
import json, os, sys
HERE = os.path.dirname(os.path.abspath(__file__)); sys.path.insert(0, os.path.dirname(HERE))
import flow_rhythm as F
L = F.load_lexicon(); res = {}
for it in json.load(open(sys.argv[1], encoding="utf-8")):
    r = F.replay(it["trace"], L, it["name"], allow_provisional=True)
    res[it["name"]] = r["trace_fltnz"] == it["trace"] and r["final_sha256"] == it["final_sha256"]
print(json.dumps(res, ensure_ascii=False))
