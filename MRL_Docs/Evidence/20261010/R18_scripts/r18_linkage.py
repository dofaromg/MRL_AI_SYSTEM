# R18 MRL 上下文粒子連結層 —— 母體內部／外部多版本平行世界的共同點標記（只讀所有來源，只新增輸出）
# origin_signature: MrLiouWord ｜ 2026-10-10 ｜ 不否決任何一方：每個版本都是一個世界實例，共同點成為可組合的上下文粒子
import os, io, re, json, gzip, zipfile, hashlib, time, collections
OUT = r"D:\MRL_Mother\WorldModel_Readiness_20261008\linkage\R18_ContextParticle_Linkage_20261010"
ST = r"D:\mrl\workspace\MRL_WorldModel_Supplement_20261008_R01\_r15_staging"
os.makedirs(OUT, exist_ok=True)
t0 = time.time()
def blob(b): return hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
def fixname(i):
    n = i.filename
    if i.flag_bits & 0x800: return n
    try: return n.encode("cp437").decode("utf-8")
    except Exception: return n
inst = collections.defaultdict(list)   # blob -> [(world, ref)]
paths = []                             # (world, path, blob)
worlds = collections.Counter()
def add(world, path, b):
    inst[b].append((world, path)); paths.append((world, path, b)); worlds[world] += 1
def zwalk(zf, world, prefix, depth):
    for i in zf.infolist():
        if i.is_dir(): continue
        n = fixname(i)
        if "__MACOSX" in n or n.split("/")[-1].startswith("._"): continue
        try: b = zf.read(i)
        except Exception: continue
        add(world, prefix + n, blob(b))
        if n.lower().endswith(".zip") and depth < 3:
            try: zwalk(zipfile.ZipFile(io.BytesIO(b)), world, prefix + n + "!/", depth + 1)
            except Exception: pass
# W-core：D:\ 根目錄各版核心（只讀）
for z in sorted(os.listdir("D:\\")):
    if z.startswith("MRL_UniversalRuntimeLanguage_Core") and z.endswith(".zip"):
        try: zwalk(zipfile.ZipFile("D:\\" + z), "core:" + z[:-4], "", 0)
        except Exception as e: print("skip", z, e)
# W-runtime：7833 用的工作區核心 v1（含原版 .bak 與現行檔）
RC = r"D:\mrl\workspace\MRL_RuntimeCivilization_20261007_R01\MRL_UniversalRuntimeLanguage_Core_v1"
for dp, dns, fns in os.walk(RC):
    dns[:] = [d for d in dns if d != "__pycache__"]
    for f in fns:
        p = os.path.join(dp, f)
        try: add("runtime:RuntimeCivilization_Core_v1", os.path.relpath(p, RC).replace("\\", "/"), blob(open(p, "rb").read()))
        except Exception: pass
# W-whitepaper：ASI 白皮書 v1.0.2（Inbox）
for z in os.listdir(r"D:\MRL_Mother\WorldLoop_Inbox"):
    if z.startswith("fa2a738e") and z.endswith(".zip"):
        zwalk(zipfile.ZipFile(os.path.join(r"D:\MRL_Mother\WorldLoop_Inbox", z)), "inbox:ASI_Whitepaper_v1_0_2", "", 0)
# W-upload：建構者 2026-10-10 附件（索引由 Claude 端計算，原件未搬入）
upload_meta = {}
for l in gzip.open(os.path.join(ST, "r18_upload_blobs2.jsonl.gz"), "rt", encoding="utf-8"):
    b, n, src, s256, size = json.loads(l)
    for code, p in src.items():
        add({"V1": "upload:MrliouV1_1.zip", "EV": "upload:Mrliou系統演化報告.zip"}[code], p, b)
    upload_meta[b] = {"sha256": s256, "size": size, "copies_in_upload": n}
# W-github：469 repo 預設 HEAD（只含與附件相同位元組者）
gh = json.load(gzip.open(os.path.join(ST, "r18_gh_hits.json.gz"), "rt"))
for b, refs in gh.items():
    for r in refs[:200]:
        repo, _, p = r.partition(":"); add("github_head:" + repo, p, b)
core_worlds = set(worlds)
# W-mirror：DL580 本地 bare 鏡像 1,151 repo（資產樹）
MT = r"D:\MRL_Mother\Governance\MRL_Global_Repository_Asset_Governance_v1\R17_Mirror_Inventory_20261010\asset_trees.jsonl.gz"
NAME_RE = re.compile(r"(?i)^(mrl|mrliou|mr\.liou|flow|fluin|particle|persona|seed|guardian|echo|mother|fltnz|flpkg)")
mirror_named = 0
for l in gzip.open(MT, "rt", encoding="utf-8"):
    r = json.loads(l); w = "mirror:" + r["full_name"]
    for p, b in r["assets"]:
        if b in inst or NAME_RE.match(p.split("/")[-1]):
            inst[b].append((w, p)); worlds[w] += 1
            if NAME_RE.match(p.split("/")[-1]): paths.append((w, p, b)); mirror_named += 1
# 粒子一：同位元組（同一 blob 出現在 ≥2 個世界，且至少一個是母體內部／附件／核心世界）
EMPTY = "e69de29bb2d1d6434b8b29ae775ad8c2e48c5391"  # 空檔，不成粒子
def fam(w): return w.split(":", 1)[0]
nb = 0
with open(os.path.join(OUT, "blob_particles.jsonl"), "w", encoding="utf-8") as f:
    for b, L in inst.items():
        ws = sorted({w for w, _ in L})
        if b == EMPTY or len(ws) < 2 or not any(w in core_worlds for w in ws): continue
        nb += 1
        f.write(json.dumps({"particle_id": "mrl.cp.blob." + b[:16], "kind": "same_bytes", "git_blob": b,
                            **upload_meta.get(b, {}), "world_count": len(ws),
                            "families": sorted({fam(w) for w in ws}),
                            "instances": [{"world": w, "ref": p} for w, p in L[:60]]}, ensure_ascii=False) + "\n")
# 粒子二：同名模組（去掉副檔名、版本尾碼、複本編號後同名，跨 ≥2 個世界）；不同位元組＝同一粒子的不同變體，全部保留
def stem(p):
    s = p.split("!/")[-1].split("/")[-1]
    s = re.sub(r"(?i)\.(bak|staged)[-_].*$", "", s)
    s = re.sub(r"\.(py|js|mjs|ts|cpp|hpp|h|c|json|md|txt|pcode|fltnz|flpkg|yaml|yml|ps1|sh|zip)$", "", s, flags=re.I)
    s = re.sub(r"(?i)([ _.-]?v\d+(?:[._]\d+)*|[ _-]?\(\d+\)| \d+|_\d{8}.*)$", "", s)
    return s.lower()
by = collections.defaultdict(list)
for w, p, b in paths:
    s = stem(p)
    if len(s) >= 4 and NAME_RE.match(s): by[s].append((w, p, b))
nn = 0
with open(os.path.join(OUT, "name_particles.jsonl"), "w", encoding="utf-8") as f:
    for s, L in sorted(by.items()):
        ws = sorted({w for w, _, _ in L})
        if len(ws) < 2: continue
        nn += 1
        variants = collections.Counter(b for _, _, b in L)
        f.write(json.dumps({"particle_id": "mrl.cp.name." + s, "kind": "same_module_name", "stem": s,
                            "world_count": len(ws), "variant_count": len(variants),
                            "families": sorted({fam(w) for w in ws}),
                            "variants": [{"git_blob": b, "instances": [{"world": w, "ref": p} for w, p, bb in L if bb == b][:20]}
                                         for b, _ in variants.most_common(40)]}, ensure_ascii=False) + "\n")
summary = {"kind": "MRL_ContextParticle_Linkage.v1", "origin_signature": "MrLiouWord", "generated": time.strftime("%Y-%m-%dT%H:%M:%S"),
           "principle": "母體＝多版本平行世界組合；不否決任何一方，只標記共同點（同位元組、同名模組）與差異（變體），讓各版本可自行組合",
           "worlds": len(worlds), "world_families": dict(collections.Counter(fam(w) for w in worlds)),
           "non_mirror_worlds": {w: worlds[w] for w in sorted(core_worlds)},
           "blob_particles": nb, "name_particles": nn, "mirror_named_files": mirror_named, "secs": round(time.time() - t0, 1),
           "sources_read_only": True, "notes": ["upload 世界的索引由 Claude 端計算（原件 245 MB 未經 Bridge 搬入）", "github_head 只列出與附件位元組相同者"]}
json.dump(summary, open(os.path.join(OUT, "summary.json"), "w", encoding="utf-8"), ensure_ascii=False, indent=1)
print(json.dumps(summary, ensure_ascii=False)[:3000])
