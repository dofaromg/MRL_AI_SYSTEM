"""
mrl Dialect → PVM 程式（JSON）橋接
origin_signature: MrLiouWord

pcode 組合語言寫法（v0 約定）：
  name:                 標籤（attr 且 value 為空、key 為識別字）
  PUSH 5                → {op:PUSH, value:5}
  STORE n, 5 / STORE n  → {op:STORE, key:n, value:5} / 用 ACC
  LOAD n                → {op:LOAD, key:n}
  JMP|JZ|JNZ|CALL x     → {op, target:x}（x 為標籤名或數字索引）
  SPREAD 3 / MERGE 2    → {count}
  REWEIGHT 1.05         → {factor}
  CHECK 0.7             → {threshold}
  FOCUS 0.5             → {target}
  DELTA [a, b]          → {a, b}
其他（MOV、暫存器 P0/R0、FX.* 粒子、未定義標籤）屬「符號層」，v0 標記為待起動、不執行。
"""
from __future__ import annotations

import re
from typing import Dict, List, Tuple

import mrl_dialect as D

EXEC_OPS = {"NOP", "PUSH", "POP", "DUP", "SWAP", "LOAD", "STORE", "FOCUS", "SPREAD",
            "REWEIGHT", "CHECK", "DELTA", "MERGE", "JMP", "JZ", "JNZ", "CALL", "RET", "HALT"}
ONE_ARG = {"PUSH": "value", "LOAD": "key", "JMP": "target", "JZ": "target", "JNZ": "target",
           "CALL": "target", "SPREAD": "count", "MERGE": "count", "REWEIGHT": "factor",
           "CHECK": "threshold", "FOCUS": "target"}
RE_IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_.]*")


def _num(s: str):
    return float(s) if re.fullmatch(r"-?\d+(\.\d+)?([eE]-?\d+)?", s) else None


def to_pvm(mod: D.Module) -> Tuple[List[Dict], List[str]]:
    """回傳 (program, pending)。pending 非空代表含符號層指令，v0 不執行。"""
    prog: List[Dict] = []
    pending: List[str] = []
    for o in mod.ops:
        if o.kind in ("blank", "comment"):
            continue
        if o.kind == "attr" and o.f["value"] == "" and o.f["sep"] == ":" and RE_IDENT.fullmatch(o.f["key"]):
            prog.append({"op": "LABEL", "name": o.f["key"]})
            continue
        if o.kind != "inst":
            pending.append(f"non-inst:{o.kind}")
            continue
        op, args = o.f["op"], list(o.f["operands"])
        if op not in EXEC_OPS:
            pending.append(f"symbolic-op:{op}")
            continue
        ins: Dict = {"op": op}
        if op == "STORE":
            ins["key"] = args[0]
            if len(args) > 1:
                ins["value"] = _num(args[1])
        elif op == "DELTA" and args:
            ins["a"], ins["b"] = _num(args[0]), _num(args[1])
        elif op in ONE_ARG and args:
            k = ONE_ARG[op]
            v = _num(args[0])
            ins[k] = v if v is not None else args[0]
            if k == "value" and v is None:
                pending.append(f"symbolic-operand:{op} {args[0]}")
        prog.append(ins)
    labels = {i["name"] for i in prog if i["op"] == "LABEL"}
    for i in prog:
        t = i.get("target")
        if i["op"] in ("JMP", "JZ", "JNZ", "CALL") and isinstance(t, str) and t not in labels:
            pending.append(f"unresolved-label:{t}")
    return prog, pending
