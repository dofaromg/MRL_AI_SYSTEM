"""
MRL Dialect v0 — 母體可逆中介表示（Reversible IR）
origin_signature: MrLiouWord ｜ 怎麼過去，就怎麼回來

把 .pcode / .fltnz / 各種 MRL 文字封包 → mrl Dialect IR（MLIR 風格文字）→ 原檔，逐位元組還原。

分層：
  bytes ──parse_source──▶ Module(ops) ──print_ir──▶ IR 文字
  IR 文字 ──parse_ir──▶ Module(ops) ──emit_source──▶ bytes   （必須 == 原 bytes）

每一行對應一個 op；op 同時保存「結構欄位」（opcode / key / verb / target…）
與「版面欄位」（前後空白、分隔符、行尾），還原時由結構欄位重建，不是直接吐 raw。
"""
from __future__ import annotations

import base64
import json
import re
from dataclasses import dataclass, field
from typing import Dict, List, Optional

DIALECT_VERSION = "0.1.0"

# PVM v1.1 25 opcodes + EchoPersona 用到的 MOV
KNOWN_OPCODES = {
    "NOP", "PUSH", "POP", "DUP", "SWAP", "LOAD", "STORE", "CLONE", "DELETE",
    "FOCUS", "SPREAD", "REWEIGHT", "CHECK", "LINK", "UNLINK", "TRAVERSE",
    "HASH", "DELTA", "MERGE", "CALL", "RET", "JMP", "JZ", "JNZ", "HALT", "MOV",
}

# 每種 op 對應的 MRL 層（world model 掛載用）
LAYER_OF = {
    "blank": None, "text": None, "comment": "L0-Origin",
    "section": "L2-Structure", "attr": "L2-Structure",
    "tag": "Persona", "trace": "L3-Memory", "map": "L5-Field",
    "flow": "L5-Field", "inst": "L7-Execution",
    "blob": "L3-Memory", "json": "L2-Structure",
}


@dataclass
class Op:
    kind: str
    f: Dict[str, object] = field(default_factory=dict)   # 結構 + 版面欄位
    eol: str = "\n"                                       # "\n" / "\r\n" / "\r" / ""

    @property
    def layer(self) -> Optional[str]:
        return LAYER_OF.get(self.kind)


@dataclass
class Module:
    name: str
    ops: List[Op]
    bom: bool = False


# ───────────────────────── 行分類（parse） ─────────────────────────

RE_TRACE = re.compile(r"^(?P<pre>\s*)\[(?P<ts>\d{4}-\d{2}-\d{2}T[^\]]*)\](?P<s1>\s*)::(?P<verb>[^\s→:]+)(?P<arrow>→|->)(?P<s2>\s*)(?P<target>.*?)(?P<post>\s*)$")
RE_TAG = re.compile(r"^(?P<pre>\s*)::(?P<name>[^:\s]+)::(?P<s1>\s*)(?P<value>.*?)(?P<post>\s*)$")
RE_SECTION = re.compile(r"^(?P<pre>\s*)\[(?P<name>[^\[\]]+)\](?P<post>\s*)$")
RE_MAP = re.compile(r"^(?P<pre>\s*)⌬(?P<kind>[^\[\s]+)\[(?P<key>[^\]]*)\](?P<s1>\s*)↦(?P<s2>\s*)(?P<target>.*?)(?P<post>\s*)$")
RE_INST = re.compile(r"^(?P<pre>\s*)(?P<op>[A-Z][A-Z0-9_]+)(?P<rest>(?:\s.*)?)$")
RE_COMMENT = re.compile(r"^(?P<pre>\s*)(?P<mark>#+|//|;+)(?P<body>.*)$")
RE_ATTR = re.compile(r"^(?P<pre>\s*)(?P<key>[^\s:=：][^:=：]*?)(?P<s1>\s*)(?P<sep>:|=|：)(?P<s2>\s*)(?P<value>.*?)(?P<post>\s*)$")
RE_FLOW = re.compile(r"(→|->|↦|⇒)")


def _split_operands(rest: str):
    """把 '   P0, CORE.ECHO.PERSONA   ; comment' 拆成版面與結構。"""
    comment = None
    body = rest
    m = re.search(r"(\s*);(.*)$", rest)
    if m:
        body = rest[: m.start()]
        comment = {"lead": m.group(1), "text": m.group(2)}
    lead = re.match(r"^\s*", body).group(0)
    core = body[len(lead):]
    trail = re.search(r"\s*$", core).group(0)
    core = core[: len(core) - len(trail)] if trail else core
    operands, seps = [], []
    if core:
        parts = re.split(r"(\s*,\s*)", core)
        operands = parts[0::2]
        seps = parts[1::2]
    return {"lead": lead, "operands": operands, "seps": seps, "trail": trail, "comment": comment}


def operand_type(s: str) -> str:
    if re.fullmatch(r"[PR]\d+|ACC|PC|SP|FP|HP", s):
        return "reg"
    if re.fullmatch(r"-?\d+(\.\d+)?", s):
        return "num"
    if s.upper().startswith("FX."):
        return "particle"
    return "symbol"


def classify_line(line: str) -> Op:
    if line.strip() == "":
        return Op("blank", {"ws": line})
    m = RE_TRACE.match(line)
    if m:
        return Op("trace", m.groupdict())
    m = RE_TAG.match(line)
    if m:
        return Op("tag", m.groupdict())
    m = RE_MAP.match(line)
    if m:
        return Op("map", m.groupdict())
    m = RE_SECTION.match(line)
    if m and not re.match(r"\d{4}-\d{2}-\d{2}T", m.group("name")):
        return Op("section", m.groupdict())
    m = RE_INST.match(line)
    if m and m.group("op") in KNOWN_OPCODES:
        d = {"pre": m.group("pre"), "op": m.group("op")}
        d.update(_split_operands(m.group("rest")))
        return Op("inst", d)
    m = RE_COMMENT.match(line)
    if m:
        return Op("comment", m.groupdict())
    m = RE_ATTR.match(line)
    if m and len(m.group("key")) <= 48 and "→" not in m.group("key"):
        return Op("attr", m.groupdict())
    if RE_FLOW.search(line):
        parts = RE_FLOW.split(line)
        return Op("flow", {"parts": parts})
    return Op("text", {"raw": line})


def parse_source(data: bytes, name: str = "module") -> Module:
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError:
        return Module(name, [Op("blob", {"b64": base64.b64encode(data).decode()}, eol="")])
    bom = text.startswith("﻿")
    if bom:
        text = text[1:]
    s = text.lstrip()
    if s[:1] in "{[" and len(text) > 1:
        try:
            json.loads(text)
            return Module(name, [Op("json", {"raw": text}, eol="")], bom)
        except ValueError:
            pass
    ops: List[Op] = []
    parts = re.split(r"(\r\n|\n|\r)", text)
    lines, eols = parts[0::2], parts[1::2] + [""]
    if lines and lines[-1] == "" and eols[-1] == "" and len(lines) > 1:
        lines.pop(); eols.pop()
    for ln, e in zip(lines, eols):
        op = classify_line(ln)
        op.eol = e
        ops.append(op)
    if text == "":
        ops = []
    return Module(name, ops, bom)


# ───────────────────────── 還原（emit） ─────────────────────────

def _emit_inst(f) -> str:
    out = f["pre"] + f["op"] + f["lead"]
    for i, o in enumerate(f["operands"]):
        out += o
        if i < len(f["seps"]):
            out += f["seps"][i]
    out += f["trail"]
    if f["comment"] is not None:
        out += f["comment"]["lead"] + ";" + f["comment"]["text"]
    return out


def emit_line(op: Op) -> str:
    k, f = op.kind, op.f
    if k == "blank":
        return f["ws"]
    if k == "trace":
        return f"{f['pre']}[{f['ts']}]{f['s1']}::{f['verb']}{f['arrow']}{f['s2']}{f['target']}{f['post']}"
    if k == "tag":
        return f"{f['pre']}::{f['name']}::{f['s1']}{f['value']}{f['post']}"
    if k == "map":
        return f"{f['pre']}⌬{f['kind']}[{f['key']}]{f['s1']}↦{f['s2']}{f['target']}{f['post']}"
    if k == "section":
        return f"{f['pre']}[{f['name']}]{f['post']}"
    if k == "inst":
        return _emit_inst(f)
    if k == "comment":
        return f"{f['pre']}{f['mark']}{f['body']}"
    if k == "attr":
        return f"{f['pre']}{f['key']}{f['s1']}{f['sep']}{f['s2']}{f['value']}{f['post']}"
    if k == "flow":
        return "".join(f["parts"])
    if k in ("text", "json"):
        return f["raw"]
    raise ValueError(k)


def emit_source(mod: Module) -> bytes:
    if mod.ops and mod.ops[0].kind == "blob":
        return base64.b64decode(mod.ops[0].f["b64"])
    s = "".join(emit_line(o) + o.eol for o in mod.ops)
    if mod.bom:
        s = "﻿" + s
    return s.encode("utf-8")


# ───────────────────────── IR 文字（MLIR 風格） ─────────────────────────

_EOL_NAME = {"\n": "lf", "\r\n": "crlf", "\r": "cr", "": "none"}
_EOL_VAL = {v: k for k, v in _EOL_NAME.items()}


def _q(v) -> str:
    return json.dumps(v, ensure_ascii=False)


def print_ir(mod: Module) -> str:
    lines = [f"// mrl dialect v{DIALECT_VERSION} · origin_signature: MrLiouWord",
             f"mrl.module @{_q(mod.name)} attributes {{bom = {str(mod.bom).lower()}}} {{"]
    for o in mod.ops:
        attrs = ", ".join(f"{k} = {_q(v)}" for k, v in o.f.items())
        layer = o.layer or "none"
        lines.append(f"  mrl.{o.kind} {{{attrs}}} eol({_EOL_NAME[o.eol]}) layer({layer})")
    lines.append("}")
    return "\n".join(lines) + "\n"


RE_IR_OP = re.compile(r"^  mrl\.(?P<kind>\w+) \{(?P<attrs>.*)\} eol\((?P<eol>\w+)\) layer\((?P<layer>[^)]*)\)$")


def _parse_attrs(s: str) -> Dict[str, object]:
    out: Dict[str, object] = {}
    dec = json.JSONDecoder()
    i = 0
    while i < len(s):
        m = re.compile(r"\s*(\w+) = ").match(s, i)
        if not m:
            break
        key = m.group(1)
        val, end = dec.raw_decode(s, m.end())
        out[key] = val
        i = end
        if s[i:i + 2] == ", ":
            i += 2
    return out


def parse_ir(text: str) -> Module:
    rows = text.split("\n")
    head = rows[1]
    m = re.match(r'^mrl\.module @(?P<name>".*") attributes \{bom = (?P<bom>true|false)\} \{$', head)
    if not m:
        raise ValueError("bad module header")
    mod = Module(json.loads(m.group("name")), [], m.group("bom") == "true")
    for r in rows[2:]:
        if r == "}" or r == "":
            continue
        mm = RE_IR_OP.match(r)
        if not mm:
            raise ValueError(f"bad op line: {r[:80]}")
        mod.ops.append(Op(mm.group("kind"), _parse_attrs(mm.group("attrs")), _EOL_VAL[mm.group("eol")]))
    return mod


def roundtrip(data: bytes, name: str = "module"):
    """bytes → IR → bytes，回傳 (ok, ir_text)。"""
    ir = print_ir(parse_source(data, name))
    back = emit_source(parse_ir(ir))
    return back == data, ir
