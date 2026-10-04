"""
MRL_Mainline_Subline_Map.html — 單檔自含 SVG 視覺化
origin_signature: MrLiouWord ｜ 2026-10-04 ｜ Additive-Only ｜ 純 stdlib

輸入：branch_registry.json、branch_role_map.json、branch_lineage.json
輸出：MRL_Mainline_Subline_Map.html（inline CSS + SVG，離線可開）
"""
from __future__ import annotations
import html
import json
import os
import sys
from collections import defaultdict

ROLE_COLORS = {
    "ROOT_MAINLINE":          "#111827",
    "ACTIVE_MAINLINE":        "#0ea5e9",
    "SUB_MAINLINE":           "#8b5cf6",
    "FEATURE_BRANCH":         "#10b981",
    "RECOVERY_BRANCH":        "#f59e0b",
    "MIRROR_BRANCH":          "#9ca3af",
    "EXTERNAL_SOURCE_BRANCH": "#6366f1",
    "ARCHIVE_BRANCH":         "#78716c",
    "ORPHAN_BRANCH":          "#dc2626",
    "UNKNOWN_BRANCH":         "#d1d5db",
}
ROLE_ORDER = list(ROLE_COLORS)


def build(registry_path: str, role_map_path: str, lineage_path: str, out_path: str):
    reg = json.load(open(registry_path, encoding="utf-8"))
    role_map = json.load(open(role_map_path, encoding="utf-8"))
    lineage = {b["branch_name"]: b for b in json.load(open(lineage_path, encoding="utf-8"))}

    # Group by role, within role sort by (not fully_absorbed, -unique_files, name)
    rows = []
    for b in reg:
        bid = b["branch_id"]
        role = role_map.get(bid, {}).get("role", "UNKNOWN_BRANCH")
        lin = lineage.get(b["branch_name"], {})
        rows.append({
            "role": role, "name": b["branch_name"],
            "is_default": b.get("is_default"),
            "ahead": lin.get("ahead"), "behind": lin.get("behind"),
            "unique_files": lin.get("unique_files_count"),
            "absorbed": lin.get("is_fully_absorbed"),
            "last_date": (lin.get("last_commit_date") or "")[:10],
            "head": (b.get("head_sha") or "")[:12],
        })
    by_role = defaultdict(list)
    for r in rows:
        by_role[r["role"]].append(r)
    for role in by_role:
        by_role[role].sort(key=lambda r: (not r["is_default"], r["absorbed"] is True, -(r["unique_files"] or 0), r["name"]))

    counts = {r: len(by_role.get(r, [])) for r in ROLE_ORDER}
    absorbed = sum(1 for r in rows if r["absorbed"])
    unique_total = sum(r["unique_files"] or 0 for r in rows)
    repo_count = len({b["full_name"] for b in reg})

    cards = []
    for role in ROLE_ORDER:
        items = by_role.get(role, [])
        if not items:
            continue
        color = ROLE_COLORS[role]
        chips = []
        for r in items:
            tag = []
            if r["is_default"]: tag.append("default")
            if r["absorbed"]: tag.append("absorbed")
            tag_s = " ·".join(tag)
            chip = (
                f'<div class="chip" title="{html.escape(r["name"])}&#10;ahead={r["ahead"]} behind={r["behind"]} '
                f'unique_files={r["unique_files"]} last={r["last_date"]} head={r["head"]}">'
                f'<span class="dot" style="background:{color}"></span>'
                f'<span class="n">{html.escape(r["name"])}</span>'
                f'<span class="meta">↑{r["ahead"] if r["ahead"] is not None else "?"}·↓{r["behind"] if r["behind"] is not None else "?"}·{r["unique_files"] or 0}f</span>'
                f'{"<span class=\"tag\">" + tag_s + "</span>" if tag_s else ""}'
                f'</div>'
            )
            chips.append(chip)
        cards.append(f"""
        <section class="role-card">
          <header style="border-left:4px solid {color}">
            <h3>{html.escape(role)}</h3>
            <span class="count">{len(items)}</span>
          </header>
          <div class="chips">{''.join(chips)}</div>
        </section>""")

    legend_items = []
    for role in ROLE_ORDER:
        legend_items.append(
            f'<span class="lg"><span class="dot" style="background:{ROLE_COLORS[role]}"></span>'
            f'{html.escape(role)}<span class="n">{counts.get(role,0)}</span></span>'
        )

    out = f"""<!DOCTYPE html><html lang="zh-Hant"><head>
<meta charset="utf-8"><title>MRL Mainline / Subline Map</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{color-scheme:light dark;--bg:#f8fafc;--card:#fff;--fg:#111827;--mut:#6b7280;--br:#e5e7eb}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0b1220;--card:#111827;--fg:#f3f4f6;--mut:#9ca3af;--br:#1f2937}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,"Noto Sans TC",sans-serif}}
.wrap{{max-width:1200px;margin:0 auto;padding:24px 16px 48px}}
h1{{margin:0 0 4px;font-size:22px}}.subtitle{{color:var(--mut);margin:0 0 16px}}
.stats{{display:flex;flex-wrap:wrap;gap:16px;margin:0 0 20px}}
.stat{{background:var(--card);border:1px solid var(--br);border-radius:10px;padding:10px 14px;min-width:120px}}
.stat .k{{font-size:12px;color:var(--mut)}}.stat .v{{font-size:20px;font-weight:600;margin-top:2px}}
.legend{{display:flex;flex-wrap:wrap;gap:10px;margin:0 0 20px;padding:10px;background:var(--card);border:1px solid var(--br);border-radius:10px}}
.lg{{display:inline-flex;align-items:center;gap:6px;font-size:12px;color:var(--mut);padding:2px 6px}}
.lg .dot{{width:10px;height:10px;border-radius:50%}}.lg .n{{margin-left:4px;color:var(--fg);font-weight:600}}
.role-card{{background:var(--card);border:1px solid var(--br);border-radius:12px;margin:0 0 14px;overflow:hidden}}
.role-card header{{display:flex;align-items:center;gap:8px;padding:10px 14px;background:color-mix(in oklch,var(--card) 92%,transparent)}}
.role-card h3{{margin:0;font-size:15px;letter-spacing:0.3px}}
.role-card .count{{margin-left:auto;background:var(--br);padding:2px 8px;border-radius:999px;font-size:12px;color:var(--mut)}}
.chips{{display:flex;flex-wrap:wrap;gap:6px;padding:12px}}
.chip{{display:inline-flex;align-items:center;gap:6px;background:color-mix(in oklch,var(--bg) 60%,transparent);border:1px solid var(--br);border-radius:999px;padding:4px 10px;font-size:12px;max-width:100%}}
.chip .dot{{width:8px;height:8px;border-radius:50%;flex:0 0 auto}}
.chip .n{{font-weight:500;overflow:hidden;text-overflow:ellipsis;white-space:nowrap;max-width:260px}}
.chip .meta{{color:var(--mut);font-variant-numeric:tabular-nums}}
.chip .tag{{color:#0ea5e9;font-weight:600;font-size:11px;padding-left:4px;border-left:1px solid var(--br)}}
footer{{margin-top:20px;color:var(--mut);font-size:12px;text-align:center}}
</style></head><body><div class="wrap">
<h1>MRL Mainline / Subline Map</h1>
<p class="subtitle">{repo_count} repositories · {len(rows)} branches · origin_signature: MrLiouWord · 2026-10-04</p>
<div class="stats">
  <div class="stat"><div class="k">分支總數</div><div class="v">{len(rows)}</div></div>
  <div class="stat"><div class="k">完全吸收</div><div class="v">{absorbed}</div></div>
  <div class="stat"><div class="k">仍有獨有 commits</div><div class="v">{len(rows)-absorbed}</div></div>
  <div class="stat"><div class="k">∑ unique files</div><div class="v">{unique_total:,}</div></div>
</div>
<div class="legend">{''.join(legend_items)}</div>
{''.join(cards)}
<footer>每個 chip 的 title 顯示 ahead / behind / unique_files / last / head。離線靜態檔，無外部依賴。</footer>
</div></body></html>"""
    open(out_path, "w", encoding="utf-8").write(out)
    return {"branches": len(rows), "absorbed": absorbed, "unique_files_total": unique_total,
            "roles": counts}


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    s = build(
        HERE + "/02_Branch_Registry/branch_registry.json",
        HERE + "/05_Mainline_Subline_Resolver/branch_role_map.json",
        HERE + "/04_Lineage_Engine/branch_lineage.json",
        HERE + "/05_Mainline_Subline_Resolver/MRL_Mainline_Subline_Map.html",
    )
    print(json.dumps(s, ensure_ascii=False, indent=1))
