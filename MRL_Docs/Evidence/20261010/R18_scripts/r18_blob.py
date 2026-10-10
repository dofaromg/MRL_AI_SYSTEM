import zipfile, hashlib, io, json, sys
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
        out[prefix + name] = hashlib.sha1(b"blob %d\0" % len(b) + b).hexdigest()
        if name.lower().endswith(".zip") and depth < 3:
            try: walk(zipfile.ZipFile(io.BytesIO(b)), prefix + name + "!/", out, depth + 1)
            except Exception: pass
for z, o in [(sys.argv[1], sys.argv[2])]:
    out = {}; walk(zipfile.ZipFile(z), "", out, 0); json.dump(out, open(o, "w"), ensure_ascii=False); print(len(out))
