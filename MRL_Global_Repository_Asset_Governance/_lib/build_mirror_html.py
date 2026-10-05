"""
MRL_CrossRepo_Mirror_Map.html — 跨 repo blob_sha mirror 視覺化
origin_signature: MrLiouWord ｜ 2026-10-05 ｜ Additive-Only ｜ 純 stdlib

輸入：duplicate_asset_groups_multi_repo.json
輸出：單檔自含 HTML
"""
from __future__ import annotations
import html, json, os
from collections import Counter, defaultdict


def build(dupes_path: str, out_path: str):
    d = json.load(open(dupes_path, encoding="utf-8"))
    groups = d.get("all_duplicate_groups", d.get("groups", []))
    # In this format each group has {blob_sha, size, count, repos, paths} not members
    # Normalize to common shape
    cross_groups = []
    for g in groups:
        repos = g.get("repos")
        paths = g.get("paths", [])
        if repos is None and "members" in g:
            # old format
            repos = sorted({m["full_name"] for m in g["members"]})
            paths = [m.get("canonical_path", "") for m in g["members"]]
            size = max(m.get("size", 0) for m in g["members"])
            is_cross = len(repos) >= 2
        else:
            size = g.get("size", 0)
            is_cross = len(repos) >= 2 if repos else False
        if is_cross:
            cross_groups.append({"blob_sha": g.get("blob_sha", ""), "size": size,
                                 "repos": sorted(set(repos)), "paths": paths[:5]})
    # Expand repo participations
    repo_pair = Counter()      # (repo_a, repo_b) → count of shared blobs
    repo_total = Counter()     # repo → how many groups it participates in
    size_by_group = []
    for g in cross_groups:
        repos = g["repos"]
        for r in repos:
            repo_total[r] += 1
        for i in range(len(repos)):
            for j in range(i+1, len(repos)):
                repo_pair[(repos[i], repos[j])] += 1
        size_by_group.append({
            "blob_sha": g.get("blob_sha", "")[:12],
            "size": g.get("size", 0),
            "repo_count": len(repos),
            "sample_path": g["paths"][0] if g.get("paths") else "",
            "repos": repos,
        })

    # Top 20 pairs
    top_pairs = repo_pair.most_common(20)
    # Top repos by participation
    top_repos = repo_total.most_common(20)
    # Top groups by repo_count (fan-out)
    top_fanout = sorted(size_by_group, key=lambda x: (-x["repo_count"], -x["size"]))[:30]
    # Top by size (big files duplicated across repos)
    top_size = sorted([g for g in size_by_group if g["size"] > 1024], key=lambda x: -x["size"])[:20]

    total_cross = len(cross_groups)
    total_pairs = len(repo_pair)
    total_repos_involved = len(repo_total)

    def row_pair(p, c):
        a, b = p
        return f'<tr><td>{html.escape(a)}</td><td>{html.escape(b)}</td><td class="n">{c}</td></tr>'

    def row_fanout(g):
        return (f'<tr><td class="n">{g["repo_count"]}</td>'
                f'<td class="n">{g["size"]:,}</td>'
                f'<td class="mono">{html.escape(g["blob_sha"])}</td>'
                f'<td class="path">{html.escape(g["sample_path"][:80])}</td></tr>')

    def row_size(g):
        return (f'<tr><td class="n">{g["size"]:,}</td>'
                f'<td class="n">{g["repo_count"]}</td>'
                f'<td class="mono">{html.escape(g["blob_sha"])}</td>'
                f'<td class="path">{html.escape(g["sample_path"][:80])}</td></tr>')

    def row_repo(r, c):
        return f'<tr><td>{html.escape(r)}</td><td class="n">{c}</td></tr>'

    out = f"""<!DOCTYPE html><html lang="zh-Hant"><head>
<meta charset="utf-8"><title>MRL Cross-Repo Mirror Map</title>
<meta name="viewport" content="width=device-width,initial-scale=1">
<style>
:root{{color-scheme:light dark;--bg:#f8fafc;--card:#fff;--fg:#111827;--mut:#6b7280;--br:#e5e7eb;--acc:#8b5cf6}}
@media(prefers-color-scheme:dark){{:root{{--bg:#0b1220;--card:#111827;--fg:#f3f4f6;--mut:#9ca3af;--br:#1f2937}}}}
body{{margin:0;background:var(--bg);color:var(--fg);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",system-ui,"Noto Sans TC",sans-serif}}
.wrap{{max-width:1200px;margin:0 auto;padding:24px 16px 48px}}
h1{{margin:0 0 4px;font-size:22px}}.subtitle{{color:var(--mut);margin:0 0 20px}}
.stats{{display:flex;flex-wrap:wrap;gap:16px;margin:0 0 24px}}
.stat{{background:var(--card);border:1px solid var(--br);border-radius:10px;padding:12px 16px;min-width:160px}}
.stat .k{{font-size:12px;color:var(--mut)}}.stat .v{{font-size:22px;font-weight:600;margin-top:2px}}
section{{background:var(--card);border:1px solid var(--br);border-radius:12px;margin:0 0 16px;overflow:hidden}}
section h2{{margin:0;padding:12px 16px;font-size:15px;border-bottom:1px solid var(--br);background:color-mix(in oklch,var(--card) 95%,transparent)}}
table{{width:100%;border-collapse:collapse;font-size:13px}}
th,td{{text-align:left;padding:8px 12px;border-bottom:1px solid var(--br)}}
th{{color:var(--mut);font-weight:600;font-size:12px}}
tr:last-child td{{border-bottom:none}}
td.n{{font-variant-numeric:tabular-nums;text-align:right;color:var(--mut)}}
td.mono{{font-family:ui-monospace,SF Mono,Menlo,monospace;color:var(--mut);font-size:12px}}
td.path{{font-family:ui-monospace,SF Mono,Menlo,monospace;font-size:12px;color:var(--fg);word-break:break-all}}
.hero{{background:color-mix(in oklch,var(--acc) 12%,var(--card));padding:16px 20px;margin:0 0 20px;border-radius:12px;border:1px solid var(--br)}}
.hero p{{margin:4px 0;color:var(--fg)}}
.hero strong{{color:var(--acc)}}
footer{{margin-top:20px;color:var(--mut);font-size:12px;text-align:center}}
</style></head><body><div class="wrap">
<h1>MRL Cross-Repo Mirror Map</h1>
<p class="subtitle">origin_signature: MrLiouWord · 2026-10-05 · based on blob_sha equivalence across 31 repos</p>

<div class="hero">
  <p><strong>重要發現</strong>：母體內容在 31 個 repo 間不是單向複製，而是**雪球**。</p>
  <p>• 10 個 repo 共用整包 <code>MRL_MotherSource_ZhiZhang_FlowAgent_Lineage_v1/</code> → 「母體 → mirror 分支」事實骨架</p>
  <p>• 17 個 repo 共用 <code>06_trace/chronicle/.gitkeep</code>、13 個共用 <code>03_memory/vector/.gitkeep</code> → scaffolding 大範圍 copy-paste</p>
  <p>• 神經圖收斂第一刀建議從 <code>MRL_MotherSource</code> 下</p>
</div>

<div class="stats">
  <div class="stat"><div class="k">跨 repo 共用 blob 分組</div><div class="v">{total_cross:,}</div></div>
  <div class="stat"><div class="k">涉及 repo 數</div><div class="v">{total_repos_involved}</div></div>
  <div class="stat"><div class="k">repo 配對數</div><div class="v">{total_pairs:,}</div></div>
</div>

<section>
  <h2>Top 20 repo 配對（共用 blob 數量）</h2>
  <table><thead><tr><th>Repo A</th><th>Repo B</th><th>Shared Blobs</th></tr></thead>
  <tbody>{''.join(row_pair(p, c) for p, c in top_pairs)}</tbody></table>
</section>

<section>
  <h2>Fan-out Top 30（一個 blob 散佈到最多 repo）</h2>
  <table><thead><tr><th>Repos</th><th>Size (B)</th><th>Blob SHA</th><th>Sample Path</th></tr></thead>
  <tbody>{''.join(row_fanout(g) for g in top_fanout)}</tbody></table>
</section>

<section>
  <h2>Top 20 大型跨 repo 共用檔（&gt;1KB）</h2>
  <table><thead><tr><th>Size (B)</th><th>Repos</th><th>Blob SHA</th><th>Sample Path</th></tr></thead>
  <tbody>{''.join(row_size(g) for g in top_size)}</tbody></table>
</section>

<section>
  <h2>Top 20 repo 參與（出現在最多共用組）</h2>
  <table><thead><tr><th>Repository</th><th>Shared Groups</th></tr></thead>
  <tbody>{''.join(row_repo(r, c) for r, c in top_repos)}</tbody></table>
</section>

<footer>這張圖以 git blob SHA-1 為同一性判準；若有 size &lt;= 1 的 .gitkeep 類 scaffolding，會自然聚在高 fan-out 區。</footer>
</div></body></html>"""
    open(out_path, "w", encoding="utf-8").write(out)
    return {
        "cross_groups": total_cross,
        "repos_involved": total_repos_involved,
        "top_pair": list(top_pairs[0]) if top_pairs else None,
        "max_fanout": top_fanout[0]["repo_count"] if top_fanout else 0,
    }


if __name__ == "__main__":
    HERE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    s = build(HERE + "/03_Asset_Registry/duplicate_asset_groups_multi_repo.json",
              HERE + "/06_CrossRepo_Deduplicator/MRL_CrossRepo_Mirror_Map.html")
    print(json.dumps(s, ensure_ascii=False, indent=1))
