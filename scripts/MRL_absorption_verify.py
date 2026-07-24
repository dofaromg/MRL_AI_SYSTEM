#!/usr/bin/env python3
# MRL_absorption_verify.py — 母體吸收完整性 / 一致性驗證器
# origin_signature = MrLiouWord
#
# 目的（補強 rl_15 粒子不滅 / 逐字保全 + 三方登錄一致）：
#   驗證某吸收批次的每件 RawArtifact —
#     1) 檔案存在，且逐字保全：實際 sha256 == 台帳 sha256
#     2) 三方登錄一致：台帳 ↔ 08_sources/sources.manifest.yaml ↔
#        MRL_ParticleArchive/MRL_ParticleArchive_manifest.json 的 external_particles
#        （同一路徑的 sha256 三處必須相同）
#
# 只讀不寫；不執行任何 APPLY / 部署 / 簽章。任何不一致以非 0 結束（誠實 exit code）。
#
# 用法：
#   python3 scripts/MRL_absorption_verify.py            # 預設驗 20260720 批次
#   python3 scripts/MRL_absorption_verify.py --batch 20260720
import sys, os, json, hashlib, argparse

try:
    import yaml
except ImportError:
    print("FAIL: 需要 pyyaml（pip install pyyaml）")
    sys.exit(2)

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _norm_relpath(path):
    return os.path.normpath(path).replace("\\", "/")


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def main():
    ap = argparse.ArgumentParser(description="MRL 吸收批次完整性/一致性驗證")
    ap.add_argument("--batch", default="20260720", help="批次日期，如 20260720")
    args = ap.parse_args()
    batch = args.batch

    bdir = os.path.join(REPO, "MRL_ParticleArchive", "External", f"MRL_AbsorbedArtifacts_{batch}")
    ledger_p = os.path.join(bdir, "MRL_Absorption_Ledger_v1.yaml")
    sources_p = os.path.join(REPO, "08_sources", "sources.manifest.yaml")
    pmani_p = os.path.join(REPO, "MRL_ParticleArchive", "MRL_ParticleArchive_manifest.json")

    print("MRL_ABSORPTION_VERIFY")
    print("origin_signature=MrLiouWord")
    print(f"batch={batch}")

    fails, passes = [], []
    def ok(m):   passes.append(m); print("PASS: " + m)
    def bad(m):  fails.append(m);  print("FAIL: " + m)
    def info(m): print("INFO: " + m)

    for p in (ledger_p, sources_p, pmani_p):
        if not os.path.isfile(p):
            print(f"FAIL: 缺檔 {os.path.relpath(p, REPO)}")
            sys.exit(2)

    ledger = yaml.safe_load(open(ledger_p, encoding="utf-8"))
    artifacts = ledger.get("artifacts") or ledger.get("absorbed_artifacts") or []
    if not artifacts:
        bad(f"台帳 {os.path.relpath(ledger_p, REPO)} 無 artifacts")
        _summary(fails, passes); sys.exit(1)

    sources = (yaml.safe_load(open(sources_p, encoding="utf-8")) or {}).get("sources", [])
    src_by_relpath = {}
    for s in sources:
        pth = s.get("path", "")
        if pth:
            src_by_relpath[_norm_relpath(pth)] = s

    pmani = json.load(open(pmani_p, encoding="utf-8"))
    ext = pmani.get("external_particles", [])
    ext_by_relpath = {}
    for e in ext:
        a = e.get("archived_as", "")
        if a:
            ext_by_relpath[_norm_relpath(a)] = e

    for a in artifacts:
        name = a.get("mother_name") or a.get("raw_artifact") or ""
        exp = (a.get("sha256") or "").strip().lower()
        if not name:
            bad(f"台帳項缺 mother_name: {a.get('kind','?')}"); continue

        fpath = os.path.join(bdir, "RawArtifact", name)
        if not os.path.isfile(fpath):
            bad(f"{name}: RawArtifact 檔不存在"); continue

        relpath = _norm_relpath(os.path.relpath(fpath, REPO))

        # 1) 逐字保全
        actual = sha256_file(fpath)
        if not exp:
            bad(f"{name}: 台帳未列 sha256（必填）")
            continue
        elif actual == exp:
            ok(f"{name}: 逐字保全 sha256 一致")
        else:
            bad(f"{name}: sha256 不符（台帳 {exp[:12]}… ≠ 實際 {actual[:12]}…）")

        # 2) 三方登錄一致
        s = src_by_relpath.get(relpath)
        if not s:
            bad(f"{name}: 未登錄於 08_sources/sources.manifest.yaml")
        elif exp and (s.get("sha256", "").lower() != exp):
            bad(f"{name}: sources.manifest sha256 與台帳不符")
        else:
            ok(f"{name}: 已登錄 sources.manifest（sha256 相符）")

        e = ext_by_relpath.get(relpath)
        if not e:
            bad(f"{name}: 未登錄於 external_particles")
        elif exp and (e.get("sha256", "").lower() != exp):
            bad(f"{name}: external_particles sha256 與台帳不符")
        else:
            ok(f"{name}: 已登錄 external_particles（sha256 相符）")

    # 誠實標註：頂層 LAW-0 metadata 重簽狀態（不視為錯誤，只回報）
    if "_resign_pending" in pmani:
        rp = pmani["_resign_pending"]
        info(f"external 追加後頂層 _sig_hash 標 _resign_pending（待母體 LAW-0 重簽）：批次 {rp.get('added_batch')}")

    # particle_count 一致性（= particles + external_particles）
    pc = pmani.get("particle_count")
    real = len(pmani.get("particles", [])) + len(ext)
    if pc == real:
        ok(f"particle_count 一致（{pc} = {len(pmani.get('particles', []))} PR + {len(ext)} external）")
    else:
        bad(f"particle_count={pc} 與實際 {real} 不符")

    _summary(fails, passes)
    sys.exit(0 if not fails else 1)


def _summary(fails, passes):
    print("-" * 40)
    if fails:
        print(f"MRL_ABSORPTION_VERIFY_FAIL：{len(fails)} 項不一致 / {len(passes)} 項 PASS")
    else:
        print(f"MRL_ABSORPTION_VERIFY_PASS：全部一致（{len(passes)} 項）")


if __name__ == "__main__":
    main()
