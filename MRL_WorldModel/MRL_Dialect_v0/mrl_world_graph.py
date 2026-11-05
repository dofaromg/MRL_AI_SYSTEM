"""
MRL 世界圖 v0 —— 由 mrl Dialect 全語料組出 Node / Map / Trace / Coupling
origin_signature: MrLiouWord

可見律：Node 存在不等於可見；Node + Map + Trace + Coupling 才可見。
  Map      ：⌬map / ⌬entry 映射、[section] 包含的 key、attr 的 key→value
  Trace    ：[ts] ::verb→ target 軌跡、::tag:: 標記
  Coupling ：→ 流程鏈、指令與運算元的連結
每個節點依它接上的線種類分級：
  visible   = Map + Trace + Coupling 三種都有
  partial   = 有一或兩種
  latent    = 只有 Node（存在但看不到 —— 待接線，不是不存在）
用法：python3 mrl_world_graph.py [root ...] > world_graph.json
"""
from __future__ import annotations

import collections
import hashlib
import json
import os
import re
import sys

import mrl_dialect as D

EXTS = (".pcode", ".fltnz", ".flynz.map")


def norm(s: str) -> str:
    s = re.sub(r"\s+#[0-9a-f]{12,64}$", "", str(s))  # 封包雜湊是屬性，不是另一個節點
    s = re.sub(r"\s+", " ", s).strip().strip("`'\"").strip()
    return s[:80]


class World:
    def __init__(self):
        self.nodes = {}
        self.edges = collections.Counter()

    def node(self, name, kind="symbol", src=None):
        name = norm(name)
        if not name:
            return None
        n = self.nodes.setdefault(name, {"kind": kind, "lines": set(), "sources": set()})
        if src:
            n["sources"].add(src)
        return name

    def edge(self, a, b, line, label):
        if a and b and a != b:
            self.edges[(a, b, line, label)] += 1
            self.nodes[a]["lines"].add(line)
            self.nodes[b]["lines"].add(line)

    def ingest(self, mod: D.Module, src: str):
        m = self.node(mod.name, "module", src)
        section = None
        for o in mod.ops:
            f = o.f
            if o.kind == "section":
                section = self.node(f["name"], "section", src)
                self.edge(m, section, "map", "contains")
            elif o.kind == "attr":
                k = self.node(f["key"], "key", src)
                self.edge(section or m, k, "map", "has")
                if f["value"]:
                    v = self.node(f["value"], "value", src)
                    self.edge(k, v, "map", f["sep"])
            elif o.kind == "map":
                a = self.node(f["key"], "key", src); b = self.node(f["target"], "symbol", src)
                self.edge(a, b, "map", "↦" + f["kind"])
            elif o.kind == "trace":
                t = self.node(f["target"], "symbol", src)
                self.edge(m, t, "trace", f["verb"])
            elif o.kind == "tag":
                if f["value"]:
                    v = self.node(f["value"], "tag:" + f["name"], src)
                    self.edge(m, v, "trace", f["name"])
            elif o.kind == "flow":
                parts = [p for p in f["parts"] if p not in ("→", "->", "↦", "⇒")]
                prev = None
                for p in parts:
                    cur = self.node(p, "symbol", src)
                    if prev and cur:
                        self.edge(prev, cur, "coupling", "→")
                    prev = cur or prev
            elif o.kind == "inst":
                for x in f["operands"]:
                    t = self.node(x, D.operand_type(x), src)
                    self.edge(m, t, "coupling", f["op"])

    def report(self):
        tiers = collections.Counter()
        out_nodes = []
        for name, n in self.nodes.items():
            lines = n["lines"]
            tier = "visible" if lines >= {"map", "trace", "coupling"} else ("partial" if lines else "latent")
            tiers[tier] += 1
            out_nodes.append({"id": name, "kind": n["kind"], "lines": sorted(lines), "tier": tier,
                              "sources": len(n["sources"])})
        out_nodes.sort(key=lambda x: (-len(x["lines"]), -x["sources"], x["id"]))
        edges = [{"from": a, "to": b, "line": l, "label": lab, "count": c}
                 for (a, b, l, lab), c in self.edges.most_common()]
        return {"origin_signature": "MrLiouWord", "law": "Node+Map+Trace+Coupling 才可見",
                "nodes": len(out_nodes), "edges": len(edges), "tiers": dict(tiers),
                "line_counts": dict(collections.Counter(e["line"] for e in edges)),
                "visible_nodes": [n for n in out_nodes if n["tier"] == "visible"],
                "node_list": out_nodes, "edge_list": edges}


def build(roots):
    w = World(); seen = set()
    for root in roots:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d not in (".git", "node_modules")]
            if dp.replace(os.sep, "/").endswith("MRL_Dialect_v0/corpus"):
                continue  # 本模組自己的測試程式不算入母體世界圖
            for fn in sorted(fns):
                if fn.lower().endswith(EXTS):
                    b = open(os.path.join(dp, fn), "rb").read()
                    h = hashlib.sha256(b).hexdigest()
                    if h in seen:
                        continue
                    seen.add(h)
                    w.ingest(D.parse_source(b, fn), h[:12])
    r = w.report(); r["unique_files"] = len(seen)
    return r


if __name__ == "__main__":
    roots = sys.argv[1:] or [os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))]
    print(json.dumps(build(roots), ensure_ascii=False, indent=1))
