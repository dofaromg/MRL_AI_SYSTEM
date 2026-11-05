"""
差分測試：同一份 .pcode
  路徑 A：pcode → mrl Dialect → PVM JSON → particle-pvm v1.2（Node.js）
  路徑 B：pcode → mrl Dialect → PVM JSON → LLVM IR → lli（LLVM JIT）＋ llc 產生 x86-64 物件檔
兩條路徑的 ACC 與整個堆疊必須逐值相等（double 位元級相等）。
同時檢查：pcode 經 Dialect 可逆還原；EchoPersona 這類符號層程式被標記為「待起動」而非誤判執行。
origin_signature: MrLiouWord
"""
import glob
import json
import os
import shutil
import struct
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import mrl_bridge as B  # noqa: E402
import mrl_dialect as D  # noqa: E402
import mrl_lower_llvm as L  # noqa: E402

LLI = shutil.which("lli") or shutil.which("lli-18")
LLC = shutil.which("llc") or shutil.which("llc-18")


def bits(x):
    """double 位元樣式；NaN 一律視為同一類（JS 與 C 的 NaN payload 不保證相同）。"""
    f = float(x)
    if f != f:
        return "nan"
    return struct.unpack("<Q", struct.pack("<d", f))[0]


def run_pvm(prog):
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
        json.dump(prog, f)
    out = subprocess.run(["node", os.path.join(ROOT, "run_pvm.mjs"), f.name], capture_output=True, text=True, check=True)
    os.unlink(f.name)
    return json.loads(out.stdout.strip().splitlines()[-1])


def run_llvm(ll):
    with tempfile.TemporaryDirectory() as d:
        p = os.path.join(d, "m.ll")
        open(p, "w").write(ll)
        out = subprocess.run([LLI, p], capture_output=True, text=True, check=True).stdout.splitlines()
        obj = subprocess.run([LLC, "-O2", "-filetype=obj", p, "-o", os.path.join(d, "m.o")], capture_output=True, text=True)
    acc = float(out[0].split()[1])  # printf 的 -0 / nan / inf 由 float() 正確解析
    depth = int(out[1].split()[1])
    stack = [float(x) for x in out[2].split()] if depth else []
    return {"acc": acc, "stack": stack, "llc_x86_obj": obj.returncode == 0}


def main():
    files = sorted(glob.glob(os.path.join(ROOT, "corpus", "*.pcode")))
    extra = sys.argv[1:]
    rows, ok_all = [], True
    for path in files + extra:
        data = open(path, "rb").read()
        rt, ir = D.roundtrip(data, os.path.basename(path))
        prog, pending = B.to_pvm(D.parse_ir(ir))
        row = {"file": os.path.basename(path), "dialect_roundtrip": rt}
        if pending:
            row.update({"status": "待起動（符號層，需 Fluin 語意綁定）", "pending": sorted(set(pending))})
            rows.append(row)
            ok_all &= rt
            continue
        a = run_pvm(prog)
        b = run_llvm(L.lower(prog))
        same = bits(a["acc"]) == bits(b["acc"]) and len(a["stack"]) == len(b["stack"]) and all(
            bits(x) == bits(y) for x, y in zip(a["stack"], b["stack"]))
        row.update({"pvm_acc": a["acc"], "llvm_acc": b["acc"], "stack_depth": len(a["stack"]),
                    "pvm_steps": a["steps"], "bit_identical": same, "llc_x86_obj": b["llc_x86_obj"],
                    "status": "PASS（沙盒）" if same and rt and b["llc_x86_obj"] else "FAIL"})
        ok_all &= row["status"].startswith("PASS")
        rows.append(row)
    print(json.dumps(rows, ensure_ascii=False, indent=1))
    return 0 if ok_all else 1


if __name__ == "__main__":
    sys.exit(main())
