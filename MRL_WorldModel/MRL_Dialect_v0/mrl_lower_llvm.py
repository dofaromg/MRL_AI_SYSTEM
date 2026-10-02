"""
PVM 程式（由 mrl Dialect 橋接而來）→ LLVM IR（.ll）
origin_signature: MrLiouWord

語意逐條對齊 pvm_v1_2.js（JS number = IEEE double）：
  資料堆疊 [4096 x double]、ACC double、記憶體鍵 → 編譯期固定槽位、CALL/RET 用獨立回傳堆疊。
每條指令一個 basic block，控制流直接變成 br / 條件 br / switch。
結束時以 printf("%.17g") 輸出 ACC、堆疊深度與每個堆疊值，供與 PVM 差分比對。
"""
from __future__ import annotations

import struct
from typing import Dict, List

SUPPORTED = {"LABEL", "NOP", "PUSH", "POP", "DUP", "SWAP", "LOAD", "STORE", "FOCUS", "SPREAD",
             "REWEIGHT", "CHECK", "DELTA", "MERGE", "JMP", "JZ", "JNZ", "CALL", "RET", "HALT"}


def _d(x: float) -> str:
    """LLVM 雙精度常數，用 16 進位位元表示，保證與 JS 同一個 double。"""
    return "0x%016X" % struct.unpack("<Q", struct.pack("<d", float(x)))[0]


class _Gen:
    def __init__(self):
        self.lines: List[str] = []
        self.n = 0

    def t(self) -> str:
        self.n += 1
        return f"%t{self.n}"

    def e(self, s: str):
        self.lines.append("  " + s)

    def label(self, name: str):
        self.lines.append(f"{name}:")

    # 堆疊操作 helper
    def sp(self):
        v = self.t(); self.e(f"{v} = load i32, ptr @sp"); return v

    def slot(self, idx):
        p = self.t(); self.e(f"{p} = getelementptr [4096 x double], ptr @stk, i32 0, i32 {idx}"); return p

    def push(self, val):
        s = self.sp(); p = self.slot(s); self.e(f"store double {val}, ptr {p}")
        s2 = self.t(); self.e(f"{s2} = add i32 {s}, 1"); self.e(f"store i32 {s2}, ptr @sp")

    def top_or0(self):
        """回傳 (有無元素 i1, 值) —— len>0 ? top : 0"""
        s = self.sp(); c = self.t(); self.e(f"{c} = icmp sgt i32 {s}, 0")
        i = self.t(); self.e(f"{i} = sub i32 {s}, 1")
        i2 = self.t(); self.e(f"{i2} = select i1 {c}, i32 {i}, i32 0")
        p = self.slot(i2); v = self.t(); self.e(f"{v} = load double, ptr {p}")
        r = self.t(); self.e(f"{r} = select i1 {c}, double {v}, double 0.0")
        return c, r, s


def lower(prog: List[Dict]) -> str:
    for ins in prog:
        if ins["op"] not in SUPPORTED:
            raise ValueError(f"unsupported op for LLVM v0: {ins['op']}")
    labels = {ins["name"]: i for i, ins in enumerate(prog) if ins["op"] == "LABEL"}
    keys: Dict[str, int] = {}
    for ins in prog:
        if ins["op"] in ("LOAD", "STORE"):
            keys.setdefault(str(ins["key"]), len(keys))
    call_sites = [i for i, ins in enumerate(prog) if ins["op"] == "CALL"]
    N = len(prog)

    def tgt(x):
        if isinstance(x, (int, float)) and not isinstance(x, bool):
            return int(x)
        return labels.get(x)

    def blk(i):
        return f"b{i}" if 0 <= i < N else "done"

    g = _Gen()
    g.label("entry"); g.e(f"br label %{blk(0)}")
    for i, ins in enumerate(prog):
        op = ins["op"]; nxt = f"%{blk(i + 1)}"
        g.label(f"b{i}")
        if op in ("LABEL", "NOP"):
            pass
        elif op == "PUSH":
            g.push(_d(ins.get("value") if ins.get("value") is not None else 0))
        elif op == "POP":
            c, v, s = g.top_or0(); g.e(f"store double {v}, ptr @acc")
            s2 = g.t(); g.e(f"{s2} = select i1 {c}, i32 {s}, i32 1")
            s3 = g.t(); g.e(f"{s3} = sub i32 {s2}, 1"); g.e(f"store i32 {s3}, ptr @sp")
        elif op == "DUP":
            c, v, s = g.top_or0(); p = g.slot(s)
            # 只有 len>0 才推入：以條件寫入 + 條件加 sp 實作
            old = g.t(); g.e(f"{old} = load double, ptr {p}")
            w = g.t(); g.e(f"{w} = select i1 {c}, double {v}, double {old}"); g.e(f"store double {w}, ptr {p}")
            inc = g.t(); g.e(f"{inc} = zext i1 {c} to i32"); s2 = g.t(); g.e(f"{s2} = add i32 {s}, {inc}"); g.e(f"store i32 {s2}, ptr @sp")
        elif op == "SWAP":
            s = g.sp(); c = g.t(); g.e(f"{c} = icmp sge i32 {s}, 2")
            a = g.t(); g.e(f"{a} = sub i32 {s}, 1"); b = g.t(); g.e(f"{b} = sub i32 {s}, 2")
            a2 = g.t(); g.e(f"{a2} = select i1 {c}, i32 {a}, i32 0"); b2 = g.t(); g.e(f"{b2} = select i1 {c}, i32 {b}, i32 0")
            pa = g.slot(a2); pb = g.slot(b2); va = g.t(); g.e(f"{va} = load double, ptr {pa}"); vb = g.t(); g.e(f"{vb} = load double, ptr {pb}")
            g.e(f"store double {vb}, ptr {pa}"); g.e(f"store double {va}, ptr {pb}")
        elif op == "LOAD":
            p = g.t(); g.e(f"{p} = getelementptr [256 x double], ptr @mem, i32 0, i32 {keys[str(ins['key'])]}")
            v = g.t(); g.e(f"{v} = load double, ptr {p}"); g.e(f"store double {v}, ptr @acc")
        elif op == "STORE":
            p = g.t(); g.e(f"{p} = getelementptr [256 x double], ptr @mem, i32 0, i32 {keys[str(ins['key'])]}")
            if ins.get("value") is not None:
                g.e(f"store double {_d(ins['value'])}, ptr {p}")
            else:
                v = g.t(); g.e(f"{v} = load double, ptr @acc"); g.e(f"store double {v}, ptr {p}")
        elif op == "FOCUS":
            if ins.get("target") is not None:
                g.e(f"store double {_d(ins['target'])}, ptr @acc")
            else:
                _, v, _ = g.top_or0(); g.e(f"store double {v}, ptr @acc")
        elif op == "SPREAD":
            n = int(ins.get("count") or 3)
            a = g.t(); g.e(f"{a} = load double, ptr @acc"); q = g.t(); g.e(f"{q} = fdiv double {a}, {_d(n)}")
            for _ in range(n):
                g.push(q)
        elif op == "REWEIGHT":
            f = ins.get("factor") or 1.1
            c, v, s = g.top_or0(); i1 = g.t(); g.e(f"{i1} = sub i32 {s}, 1"); i2 = g.t(); g.e(f"{i2} = select i1 {c}, i32 {i1}, i32 0")
            p = g.slot(i2); old = g.t(); g.e(f"{old} = load double, ptr {p}")
            m = g.t(); g.e(f"{m} = fmul double {old}, {_d(f)}")
            w = g.t(); g.e(f"{w} = select i1 {c}, double {m}, double {old}"); g.e(f"store double {w}, ptr {p}")
        elif op == "CHECK":
            th = ins.get("threshold") or 0.7
            _, v, _ = g.top_or0(); c = g.t(); g.e(f"{c} = fcmp oge double {v}, {_d(th)}")
            r = g.t(); g.e(f"{r} = uitofp i1 {c} to double"); g.e(f"store double {r}, ptr @acc")
        elif op == "DELTA":
            s = g.sp()

            def at(back, argk):
                if ins.get(argk) is not None:
                    return _d(ins[argk])
                c = g.t(); g.e(f"{c} = icmp sge i32 {s}, {back}")
                i = g.t(); g.e(f"{i} = sub i32 {s}, {back}"); i2 = g.t(); g.e(f"{i2} = select i1 {c}, i32 {i}, i32 0")
                p = g.slot(i2); v = g.t(); g.e(f"{v} = load double, ptr {p}")
                r = g.t(); g.e(f"{r} = select i1 {c}, double {v}, double 0.0"); return r
            a = at(2, "a"); b = at(1, "b")
            r = g.t(); g.e(f"{r} = fsub double {b}, {a}"); g.e(f"store double {r}, ptr @acc")
        elif op == "MERGE":
            k = int(ins.get("count") or 2)
            s = g.sp(); c = g.t(); g.e(f"{c} = icmp slt i32 {s}, {k}")
            kk = g.t(); g.e(f"{kk} = select i1 {c}, i32 {s}, i32 {k}")
            base = g.t(); g.e(f"{base} = sub i32 {s}, {kk}")
            acc = "0x0000000000000000"
            for j in range(k):  # 依序由低到高累加（與 JS reduce 同順序）
                idx = g.t(); g.e(f"{idx} = add i32 {base}, {j}")
                inr = g.t(); g.e(f"{inr} = icmp slt i32 {j}, {kk}")
                i2 = g.t(); g.e(f"{i2} = select i1 {inr}, i32 {idx}, i32 0")
                p = g.slot(i2); v = g.t(); g.e(f"{v} = load double, ptr {p}")
                v2 = g.t(); g.e(f"{v2} = select i1 {inr}, double {v}, double 0.0")
                na = g.t(); g.e(f"{na} = fadd double {acc}, {v2}"); acc = na
            p = g.slot(base); g.e(f"store double {acc}, ptr {p}")
            s2 = g.t(); g.e(f"{s2} = add i32 {base}, 1"); g.e(f"store i32 {s2}, ptr @sp"); g.e(f"store double {acc}, ptr @acc")
        elif op in ("JMP", "JZ", "JNZ"):
            t = tgt(ins.get("target"))
            dest = f"%{blk(t)}" if t is not None else nxt
            if op == "JMP":
                g.e(f"br label {dest}"); continue
            a = g.t(); g.e(f"{a} = load double, ptr @acc")
            c = g.t(); g.e(f"{c} = fcmp {'oeq' if op == 'JZ' else 'une'} double {a}, 0.0")
            g.e(f"br i1 {c}, label {dest}, label {nxt}"); continue
        elif op == "CALL":
            t = tgt(ins.get("target"))
            r = g.t(); g.e(f"{r} = load i32, ptr @rsp"); p = g.t(); g.e(f"{p} = getelementptr [1024 x i32], ptr @rstk, i32 0, i32 {r}")
            g.e(f"store i32 {i + 1}, ptr {p}"); r2 = g.t(); g.e(f"{r2} = add i32 {r}, 1"); g.e(f"store i32 {r2}, ptr @rsp")
            g.e(f"br label %{blk(t) if t is not None else blk(i + 1)}"); continue
        elif op == "RET":
            r = g.t(); g.e(f"{r} = load i32, ptr @rsp"); c = g.t(); g.e(f"{c} = icmp sgt i32 {r}, 0")
            g.e(f"br i1 {c}, label %ret{i}, label %done")
            g.label(f"ret{i}")
            r2 = g.t(); g.e(f"{r2} = sub i32 {r}, 1"); g.e(f"store i32 {r2}, ptr @rsp")
            p = g.t(); g.e(f"{p} = getelementptr [1024 x i32], ptr @rstk, i32 0, i32 {r2}")
            a = g.t(); g.e(f"{a} = load i32, ptr {p}")
            cases = " ".join(f"i32 {cs + 1}, label %{blk(cs + 1)}" for cs in call_sites)
            g.e(f"switch i32 {a}, label %done [ {cases} ]"); continue
        elif op == "HALT":
            g.e("br label %done"); continue
        g.e(f"br label {nxt}")

    body = "\n".join(g.lines)
    return f"""; mrl dialect v0 → LLVM IR · origin_signature: MrLiouWord
@stk = internal global [4096 x double] zeroinitializer
@sp = internal global i32 0
@acc = internal global double 0.0
@mem = internal global [256 x double] zeroinitializer
@rstk = internal global [1024 x i32] zeroinitializer
@rsp = internal global i32 0
@fmt_acc = private constant [11 x i8] c"ACC %.17g\\0A\\00"
@fmt_sp = private constant [10 x i8] c"DEPTH %d\\0A\\00"
@fmt_v = private constant [6 x i8] c"%.17g\\00"
@fmt_sep = private constant [2 x i8] c" \\00"
@fmt_nl = private constant [2 x i8] c"\\0A\\00"
declare i32 @printf(ptr, ...)

define i32 @main() {{
{body}
done:
  %a = load double, ptr @acc
  call i32 (ptr, ...) @printf(ptr @fmt_acc, double %a)
  %s = load i32, ptr @sp
  call i32 (ptr, ...) @printf(ptr @fmt_sp, i32 %s)
  br label %pl
pl:
  %i = phi i32 [0, %done], [%i1, %pb]
  %c = icmp slt i32 %i, %s
  br i1 %c, label %pb, label %pe
pb:
  %p = getelementptr [4096 x double], ptr @stk, i32 0, i32 %i
  %v = load double, ptr %p
  call i32 (ptr, ...) @printf(ptr @fmt_v, double %v)
  call i32 (ptr, ...) @printf(ptr @fmt_sep)
  %i1 = add i32 %i, 1
  br label %pl
pe:
  call i32 (ptr, ...) @printf(ptr @fmt_nl)
  ret i32 0
}}
"""
