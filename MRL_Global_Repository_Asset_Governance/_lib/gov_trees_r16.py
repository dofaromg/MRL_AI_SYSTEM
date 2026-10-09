#!/usr/bin/env python3
"""R16 治理層：467 新 repo 預設分支 HEAD 的 commit date 與資產樹（blob sha + 路徑；不下載檔案內容）。
經 session 匿名 git proxy：git fetch --depth 1 --filter=blob:none <head sha>。可續跑。origin_signature: MrLiouWord"""
import concurrent.futures as cf, json, subprocess, tempfile, shutil, os, time
from pathlib import Path
S = Path(__file__).resolve().parent
OUT = S / "gov_trees.jsonl"
rows = [json.loads(l) for l in open(S / "branches_new.final.jsonl")]
done = set()
if OUT.exists():
    done = {json.loads(l)["full_name"] for l in open(OUT) if l.strip()}

def head_of(r):
    m = r.get("repo_meta") or {}
    db = m.get("default_branch")
    br = r.get("branches") or []
    for b in br:
        if b["name"] == db: return db, b["sha"]
    return (br[0]["name"], br[0]["sha"]) if br else (None, None)

def one(r):
    fn = r["full_name"]; db, sha = head_of(r)
    rec = {"full_name": fn, "default_branch": db, "head_sha": sha}
    if not sha:
        rec.update(status="no_branches" if r["status"] == "ls_remote_ok" else r["status"]); return rec
    d = tempfile.mkdtemp(prefix="gt_")
    try:
        subprocess.run(["git", "init", "-q", d], check=True)
        g = lambda *a, **k: subprocess.run(["git", "-C", d, *a], capture_output=True, text=True, timeout=180, **k)
        p = g("fetch", "-q", "--depth", "1", "--filter=blob:none", f"https://github.com/{fn}", sha)
        if p.returncode:
            rec.update(status="fetch_failed", error=p.stderr.strip()[-300:]); return rec
        lg = g("log", "-1", "--format=%cI%x09%aI%x09%s", "FETCH_HEAD").stdout.strip().split("\t")
        rec.update(commit_date=lg[0], author_date=lg[1] if len(lg) > 1 else None, subject=(lg[2] if len(lg) > 2 else "")[:200])
        t = g("-c", "core.quotepath=off", "ls-tree", "-r", "FETCH_HEAD", env={**os.environ, "GIT_NO_LAZY_FETCH": "1"}).stdout
        assets = []
        for line in t.splitlines():
            meta, path = line.split("\t", 1)
            mode, typ, bsha = meta.split()
            if typ == "blob": assets.append([path, bsha, mode])
        rec.update(status="ok", asset_count=len(assets), assets=assets)
        return rec
    except Exception as e:
        rec.update(status="error", error=str(e)[:300]); return rec
    finally:
        shutil.rmtree(d, ignore_errors=True)

todo = [r for r in rows if r["full_name"] not in done]
print("todo", len(todo), flush=True)
with open(OUT, "a") as f, cf.ThreadPoolExecutor(8) as ex:
    for i, rec in enumerate(ex.map(one, todo), 1):
        f.write(json.dumps(rec, ensure_ascii=False) + "\n"); f.flush()
        if i % 25 == 0: print(i, time.strftime("%H:%M:%S"), flush=True)
print("done", flush=True)
