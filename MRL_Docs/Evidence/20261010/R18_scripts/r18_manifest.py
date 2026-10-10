import zipfile, hashlib, io, json, sys, collections
def fix(n, info):
    if info.flag_bits & 0x800: return n
    try: return n.encode("cp437").decode("utf-8")
    except Exception: return n
def walk(zf, prefix, out, depth):
    for i in zf.infolist():
        if i.is_dir(): continue
        name = fix(i.filename, i)
        if "__MACOSX" in name or name.split("/")[-1].startswith("._"): continue
        b = zf.read(i)
        rec = {"path": prefix + name, "size": len(b), "sha256": hashlib.sha256(b).hexdigest(), "depth": depth}
        out.append(rec)
        if name.lower().endswith(".zip") and depth < 3:
            try: walk(zipfile.ZipFile(io.BytesIO(b)), prefix + name + "!/", out, depth + 1)
            except Exception as e: rec["nested_error"] = str(e)[:80]
for z, tag in [(sys.argv[1], sys.argv[2])]:
    out = []; walk(zipfile.ZipFile(z), "", out, 0)
    json.dump({"source": tag, "files": out}, open(sys.argv[3], "w"), ensure_ascii=False)
    ext = collections.Counter(r["path"].rsplit(".", 1)[-1].lower() if "." in r["path"].split("/")[-1] else "-" for r in out)
    print(tag, len(out), "files;", ext.most_common(14))
