"""
MRL FlowRhythm v0 —— 語場節奏引擎（Jump → Collapse → Trace → Replay）
origin_signature: MrLiouWord ｜ 怎麼過去，就怎麼回來

本體：實作 seed_runner.py 裡標註「尚未實作」的 generate 模式 ——
      「語場生成模擬器（未來支援跳點與人格觸發）」。
語意來源分層：粒子分類與模組敘述從建構者 2025-07 原始檔載入；
軌跡動詞的固定對應若無原檔明文，必須標為 provisional，正典模式預設拒絕
  - FluinSim.DualSet.v1.flsim / flsim_runtime.py 的 module_map（每個粒子「做什麼」）
  - EchoPersona.structure.json、*.flseed/structure.json（pcode ↔ 粒子碼 對照）
  - Fluin_Particle_BilingualDict.csv（詞性、中英）
  - flgroup.json（粒子 → 模組類別）

節奏（依根源檔 Jump → Collapse → Trace → Replay）：
  ⊕Core      → 啟動核心人格（initiated）
  adjective  → 生成語場屬性（resonance）
  noun       → 注入語場對象（absorb）
  ∴          → Jump：邏輯跳點，觸發因果連接（jump）
  verb/flow  → Collapse：行為執行，把當下語場折疊成種子封包（collapse，含 SHA-256）
  ⊗Target    → Trace：輸出結果至目標模組，寫出 .fltnz 軌跡行 [ts] ::verb→ target
  Replay     → 只讀軌跡，重建整條粒子鏈與語場，封包雜湊必須一致，軌跡逐位元組重現
"""
from __future__ import annotations

import ast
import csv
import datetime as _dt
import hashlib
import io
import json
import os
import re
import sys
import zipfile
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
_LEX_ORIG = os.path.join(REPO, "MRL_MotherSource_ZhiZhang_FlowAgent_Lineage_v1", "粒子字典ai", "工程師給的")
_LEX_COPY = os.path.join(HERE, "lexicon")   # 逐位元組副本（見 lexicon/SOURCES.sha256）
LEX_DIR = _LEX_ORIG if os.path.isdir(_LEX_ORIG) else _LEX_COPY
sys.path.insert(0, os.path.join(REPO, "MRL_WorldModel", "MRL_Dialect_v0"))
import mrl_dialect as D  # noqa: E402

ENGINE_VERSION = "0.2.0"
SIGN = "MrLiouWord"


# ───────────────────────── 語意字典：從建構者原檔載入 ─────────────────────────

@dataclass
class Lexicon:
    module_map: Dict[str, str] = field(default_factory=dict)   # 粒子 → 執行敘述（flsim_runtime.py）
    kind: Dict[str, str] = field(default_factory=dict)         # 粒子 → adjective/noun/logic/verb/target
    zh: Dict[str, str] = field(default_factory=dict)
    pcode_to_code: Dict[str, str] = field(default_factory=dict)  # "FX.ADJ.112" → "⋄fx.adj.112"
    group: Dict[str, str] = field(default_factory=dict)        # 粒子 → 模組類別（flgroup.json）
    sources: List[str] = field(default_factory=list)


def _read(p, mode="rb"):
    with open(p, mode) as f:
        return f.read()


def load_lexicon(lex_dir: str = LEX_DIR) -> Lexicon:
    L = Lexicon()
    # 1) flsim_runtime.py 的 module_map
    flsim = os.path.join(lex_dir, "重新下載 FluinSim.DualSet.v1.flsim")
    with zipfile.ZipFile(flsim) as z:
        src = z.read("flsim_runtime.py").decode("utf-8")
    m = re.search(r"^module_map\s*=\s*(\{.*\})\s*$", src, re.M)
    L.module_map = ast.literal_eval(m.group(1))
    L.sources.append("FluinSim.DualSet.v1.flsim/flsim_runtime.py")
    # 2) 雙語字典
    with open(os.path.join(lex_dir, "下載 Fluin_Particle_BilingualDict.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            L.kind[r["code"]] = r["type"]
            L.zh[r["code"]] = r["zh"]
    L.sources.append("Fluin_Particle_BilingualDict.csv")
    # 3) structure.json（EchoPersona + 兩顆 flseed）→ pcode 對照
    structs = [json.loads(_read(os.path.join(lex_dir, "下載 EchoPersona.structure.json")).decode("utf-8"))["sequence"]]
    for seed in ("下載 FluinCoreSeed.v1.flseed", "下載 Memory.Seed.Core.v1.flseed"):
        with zipfile.ZipFile(os.path.join(lex_dir, seed)) as z:
            structs.append(json.loads(z.read("structure.json").decode("utf-8")))
    for seq in structs:
        for e in seq:
            code, pc = e["code"], e.get("pcode", "")
            L.kind.setdefault(code, e.get("type", ""))
            ops = pc.split(None, 1)
            if len(ops) == 2:
                last = ops[1].split(",")[-1].strip()
                L.pcode_to_code[last] = code
    L.sources += ["EchoPersona.structure.json", "FluinCoreSeed.v1.flseed/structure.json", "Memory.Seed.Core.v1.flseed/structure.json"]
    # 4) flgroup.json
    g = json.loads(_read(os.path.join(lex_dir, "下載 flgroup.json")).decode("utf-8"))
    for cat, (mod, codes) in g.items():
        for c in codes:
            L.group[c] = f"{cat}{mod}"
    L.sources.append("flgroup.json")
    return L


# ───────────────────────── 種子 → 粒子鏈 ─────────────────────────

def chain_from_fltnz(text: str) -> List[str]:
    """粒子語句 .fltnz：一行一個粒子，# 之後是註解；⊕Core: 開頭是核心人格。"""
    out = []
    for line in text.splitlines():
        s = line.split("#", 1)[0].strip() if not line.lstrip().startswith("⊕") else line.split("#", 1)[0].strip()
        if not s or s.startswith("//"):
            continue
        out.append(s)
    return out


def chain_from_pcode(text: str, L: Lexicon) -> Tuple[List[str], List[str]]:
    """pcode（語場指令）→ 粒子鏈。對照表來自建構者的 structure.json。回傳 (chain, 未對上的指令)。"""
    mod = D.parse_source(text.encode("utf-8"), "pcode")
    chain, unmapped = [], []
    for o in mod.ops:
        if o.kind != "inst":
            continue
        op, args = o.f["op"], o.f["operands"]
        if op == "LOAD" and len(args) == 2 and args[1].upper().startswith("CORE."):
            name = ".".join(w.capitalize() for w in args[1].split(".")[1:])  # CORE.ECHO.PERSONA → Echo.Persona
            chain.append(f"⊕Core: {name}")
        elif op == "PUSH":
            continue  # 把已綁定的粒子推入語場；鏈上已由 MOV 表示
        elif args and args[-1] in L.pcode_to_code:
            chain.append(L.pcode_to_code[args[-1]])
        else:
            unmapped.append(f"{op} {', '.join(args)}")
    return chain, unmapped


def load_seed(path: str, L: Lexicon) -> Tuple[List[str], Dict]:
    name = os.path.basename(path)
    raw = _read(path)
    if raw[:2] == b"PK":
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            inner = next(n for n in ("seed.fltnz", "persona.seed.fltnz") if n in z.namelist())
            env = json.loads(z.read("env.medium.json").decode("utf-8")) if "env.medium.json" in z.namelist() else {}
            return chain_from_fltnz(z.read(inner).decode("utf-8")), {"source": name, "form": f"zip:{inner}", "env": env}
    text = raw.decode("utf-8")
    if name.lower().endswith(".pcode"):
        chain, unmapped = chain_from_pcode(text, L)
        return chain, {"source": name, "form": "pcode", "unmapped": unmapped}
    return chain_from_fltnz(text), {"source": name, "form": "fltnz"}


# ───────────────────────── 節奏執行：Jump → Collapse → Trace ─────────────────────────

def kind_of(tok: str, L: Lexicon) -> str:
    if tok.startswith("⊕"):
        return "core"
    if tok == "∴":
        return "logic"
    if tok.startswith("⊗"):
        return "target"
    return L.kind.get(tok, "unknown")


# 這些字可在原始 MRL 材料中找到，但「詞性／節奏階段 → 軌跡動詞」的
# 固定映射除 core→initiated 外，尚未取得建構者明文核准（見 EVIDENCE.md）。
# 因此探索模式可使用，但正典模式必須 fail-closed。
VERB_OF = {"core": "initiated", "adjective": "resonance", "noun": "absorb", "logic": "jump",
           "verb": "collapse", "target": "trace", "unknown": "pinged"}
VERIFIED_VERB_KINDS = {"core"}
SEMANTIC_VERIFIED = "VERIFIED"
SEMANTIC_PROVISIONAL = "PROVISIONAL_NOT_CANONICAL"
HASH_POLICY_FIELDS = ("semantic_status", "provisional_mappings")


class ProvisionalSemanticMappingError(ValueError):
    """正典輸出遇到未由建構者明文核准的軌跡動詞映射。"""


def packet_hash(packet: Dict) -> str:
    return hashlib.sha256(json.dumps(packet, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()


class Clock:
    """軌跡時間戳。fixed 給定時，每一拍 +1 微秒（可重現）；否則用當下 UTC。"""

    def __init__(self, fixed: Optional[str] = None, seq: Optional[List[str]] = None):
        self.t = _dt.datetime.fromisoformat(fixed.replace("Z", "+00:00")) if fixed else None
        self.seq = list(seq) if seq else None

    def now(self) -> str:
        if self.seq:
            return self.seq.pop(0)        # Replay：沿用軌跡上原本的時間戳
        if self.t is None:
            return _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        s = self.t.strftime("%Y-%m-%dT%H:%M:%S.%fZ")
        self.t += _dt.timedelta(microseconds=1)
        return s


def run(chain: List[str], L: Lexicon, clock: Optional[Clock] = None, title: str = "語場節奏",
        allow_provisional: bool = False) -> Dict:
    """執行節奏。

    預設為正典 fail-closed。只有明示 allow_provisional=True 的 sandbox／研究執行
    才能使用尚未由建構者明文核准的固定軌跡動詞映射；輸出會永久標記為非正典。
    """
    clock = clock or Clock()
    kinds = [kind_of(tok, L) for tok in chain]
    provisional = sorted({f"{k}->{VERB_OF[k]}" for k in kinds if k not in VERIFIED_VERB_KINDS})
    if provisional and not allow_provisional:
        raise ProvisionalSemanticMappingError(
            "canonical FlowRhythm refused provisional mappings: " + ", ".join(provisional)
        )
    semantic_status = SEMANTIC_PROVISIONAL if provisional else SEMANTIC_VERIFIED
    field_ = {"persona": None, "attributes": [], "objects": [], "jumps": [], "flows": [], "targets": [],
              "packets": [], "origin_signature": SIGN, "semantic_status": semantic_status,
              "provisional_mappings": provisional}
    events, pending_cause = [], None
    for tok in chain:
        k = kind_of(tok, L)
        verb = VERB_OF[k]
        detail = ""
        if k == "core":
            field_["persona"] = tok.split(":", 1)[1].strip()
        elif k == "adjective":
            field_["attributes"].append(tok)
        elif k == "noun":
            field_["objects"].append(tok)
        elif k == "logic":                                   # Jump
            pending_cause = {"cause": field_["attributes"] + field_["objects"], "gate": tok}
            field_["jumps"].append(pending_cause)
        elif k == "verb":                                    # Collapse
            if pending_cause is not None:
                pending_cause["effect"] = tok
                pending_cause = None
            field_["flows"].append(tok)
            snapshot = {kk: field_[kk] for kk in (
                "persona", "attributes", "objects", "jumps", "flows", *HASH_POLICY_FIELDS
            )}
            h = packet_hash(snapshot)
            field_["packets"].append({"flow": tok, "sha256": h})
            detail = f" #{h[:16]}"
        elif k == "target":                                  # Trace
            field_["targets"].append(tok)
        events.append({"ts": clock.now(), "verb": verb, "token": tok, "kind": k, "detail": detail,
                       "mapping_status": SEMANTIC_VERIFIED if k in VERIFIED_VERB_KINDS else SEMANTIC_PROVISIONAL,
                       "narration": L.module_map.get(tok, "未知模組")})
    final = packet_hash({kk: field_[kk] for kk in (
        "persona", "attributes", "objects", "jumps", "flows", "targets", *HASH_POLICY_FIELDS
    )})
    header = (f"# {title} · FlowRhythm v{ENGINE_VERSION} · origin_signature: {SIGN}"
              f" · semantic_status: {semantic_status}")
    trace_lines = [header, "::initiated::"] + [f"[{e['ts']}] ::{e['verb']}→ {e['token']}{e['detail']}" for e in events]
    body = [t for t in chain if not t.startswith("⊕")]
    if len(body) > 1:
        trace_lines.append(" → ".join(body))                                   # 節奏鏈（Coupling）
    for tok in chain:                                                          # 命名對照（Map）
        for pc, code in L.pcode_to_code.items():
            if code == tok:
                trace_lines.append(f"⌬map[{pc}]↦{code}")
    narration = "\n".join(f"[{e['token']}] → {e['narration']}" for e in events)
    return {"chain": chain, "field": field_, "events": events, "final_sha256": final,
            "semantic_status": semantic_status, "provisional_mappings": provisional,
            "trace_fltnz": "\n".join(trace_lines) + "\n", "narration": narration}


# ───────────────────────── Replay：只讀軌跡，重建一切 ─────────────────────────

def replay(trace_text: str, L: Lexicon, title: str = "語場節奏",
           allow_provisional: bool = False) -> Dict:
    mod = D.parse_source(trace_text.encode("utf-8"), "trace")
    ops = [o for o in mod.ops if o.kind == "trace"]
    chain = [re.sub(r" #[0-9a-f]{16}$", "", o.f["target"]) for o in ops]
    r = run(chain, L, Clock(seq=[o.f["ts"] for o in ops]), title,
            allow_provisional=allow_provisional)
    return {**r, "trace_ops": len(ops)}


def narrate_like_flsim(chain: List[str], L: Lexicon) -> str:
    """與建構者 FluinSim runtime.log 相同格式的敘述輸出（用來對照原始 log）。"""
    return "\n".join(f"[{t}] → {L.module_map.get(t, '未知模組')}" for t in chain)
