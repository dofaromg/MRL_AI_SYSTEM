"""
隨機差分（fuzz）：隨機產生只含前向跳躍的 PVM 程式（保證終止），
比對 particle-pvm v1.2（Node）與 LLVM（lli）的 ACC 與堆疊是否位元級相同。
用法：python3 tests/test_fuzz_differential.py [數量] [seed]
origin_signature: MrLiouWord
"""
import json, os, random, subprocess, sys, tempfile
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.dirname(HERE); sys.path.insert(0, ROOT); sys.path.insert(0, HERE)
import mrl_lower_llvm as L
from test_llvm_differential import run_llvm, bits

OPS = ["NOP", "PUSH", "POP", "DUP", "SWAP", "LOAD", "STORE", "FOCUS", "SPREAD", "REWEIGHT", "CHECK", "DELTA", "MERGE", "JMP", "JZ", "JNZ", "HALT"]

def rnd_num(r):
    return r.choice([0, 1, -1, 0.5, 0.1, 0.3, 1 / 3, 2.5, -7.25, 1e-9, 123456.789, r.uniform(-10, 10)])

def gen(r, n):
    p = []
    for i in range(n):
        op = r.choice(OPS); ins = {"op": op}
        if op == "PUSH": ins["value"] = rnd_num(r)
        elif op in ("LOAD", "STORE"):
            ins["key"] = r.choice("abc")
            if op == "STORE" and r.random() < .5: ins["value"] = rnd_num(r)
        elif op == "FOCUS" and r.random() < .5: ins["target"] = rnd_num(r)
        elif op in ("SPREAD", "MERGE") and r.random() < .7: ins["count"] = r.randint(1, 4)
        elif op == "REWEIGHT" and r.random() < .7: ins["factor"] = rnd_num(r)
        elif op == "CHECK" and r.random() < .7: ins["threshold"] = rnd_num(r)
        elif op == "DELTA" and r.random() < .3: ins["a"], ins["b"] = rnd_num(r), rnd_num(r)
        elif op in ("JMP", "JZ", "JNZ"): ins["target"] = r.randint(i + 1, n + 2)  # 只往前跳 → 必終止
        p.append(ins)
    return p

def main(count=300, seed=20260927):
    r = random.Random(seed)
    progs = [gen(r, r.randint(5, 40)) for _ in range(count)]
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f: json.dump(progs, f)
    js = ("import {readFileSync} from 'fs'; import {ParticleVM} from '%s';"
          "const ps=JSON.parse(readFileSync(process.argv[1],'utf8'));"
          "console.log(JSON.stringify(ps.map(p=>{const s=new ParticleVM().execute(p).state;return {acc:s.registers.ACC,stack:s.stack}}),(k,v)=>typeof v===\"number\"?(Object.is(v,-0)?\"-0\":Number.isFinite(v)?v:String(v)):v))") % os.path.join(ROOT, "pvm_v1_2.js")
    out = subprocess.run(["node", "--input-type=module", "-e", js, f.name], capture_output=True, text=True, check=True)
    pvm = json.loads(out.stdout); os.unlink(f.name)
    bad = []
    for i, (p, a) in enumerate(zip(progs, pvm)):
        b = run_llvm(L.lower(p))
        same = bits(a["acc"]) == bits(b["acc"]) and len(a["stack"]) == len(b["stack"]) and all(bits(x) == bits(y) for x, y in zip(a["stack"], b["stack"]))
        if not same: bad.append({"i": i, "prog": p, "pvm": a, "llvm": b})
    print(json.dumps({"programs": count, "seed": seed, "bit_identical": count - len(bad), "mismatch": len(bad), "first_mismatch": bad[:1]}, ensure_ascii=False, indent=1))
    return 0 if not bad else 1

if __name__ == "__main__":
    a = sys.argv[1:]; sys.exit(main(int(a[0]) if a else 300, int(a[1]) if len(a) > 1 else 20260927))
