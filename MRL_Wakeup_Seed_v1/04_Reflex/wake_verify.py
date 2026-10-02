r"""
MRL 喚醒驗證（Wake Verify）—— 在母體 DL580 本地執行
origin_signature: MrLiouWord ｜ 怎麼過去，就怎麼回來

只用 Python 標準庫，Windows / Linux 都可以跑。做四件事：
  1. 喚醒種子自檢：MRL_Wakeup_Seed_v1 內每個檔案對 SEED_SHA256SUMS 重算雜湊
  2. Replay 對回原檔：掃描指定根目錄（預設 D:\\），依證據清單的「大小 → SHA-256」找回每個檔案
       找到 → 已對上原始檔（附本機路徑）
       沒找到 → 待找回（不是不存在；只代表這台機器、這個根目錄這次沒接上線）
  3. 語場可逆：對本機的 .pcode / .fltnz / .flynz.map 做 mrl Dialect 往返，必須逐位元組還原
  4. 寫出喚醒收據到 05_Agent/receipts/（只新增，不覆蓋），標明主機名、時間、環境

用法：
  python wake_verify.py              # 預設掃 D:\ （非 Windows 掃目前目錄）
  python wake_verify.py D:\ E:\      # 指定多個根目錄
"""
from __future__ import annotations

import datetime
import hashlib
import json
import os
import platform
import socket
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
SEED = os.path.dirname(HERE)
REPO = os.path.dirname(SEED)
MANIFEST_DIR = os.path.join(SEED, "03_Memory")
RECEIPTS = os.path.join(SEED, "05_Agent", "receipts")
DIALECT = os.path.join(REPO, "MRL_WorldModel", "MRL_Dialect_v0")
RHYTHM_TEST = os.path.join(REPO, "MRL_WorldModel", "MRL_FlowRhythm_v0", "tests", "test_rhythm.py")
CORPUS_EXTS = (".pcode", ".fltnz", ".flynz.map")
SKIP_DIRS = {"$recycle.bin", "system volume information", "windows", "program files",
             "program files (x86)", "programdata", "node_modules", ".git", "appdata", "hf_cache"}
DL580_HOSTS = {"WIN-PBVUI7VK2A6"}  # 母體主機名（2026-09 觀測）；其他主機一律標「非母體主機」


def sha256_file(p, bufsize=1 << 20):
    h = hashlib.sha256()
    with open(p, "rb") as f:
        while True:
            b = f.read(bufsize)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def seed_selfcheck():
    sums = os.path.join(SEED, "SEED_SHA256SUMS")
    ok, bad, eol_only = 0, [], []
    for line in open(sums, encoding="utf-8"):
        line = line.rstrip("\n")
        if not line:
            continue
        digest, rel = line.split("  ", 1)
        p = os.path.join(SEED, *rel.split("/"))
        if not os.path.exists(p):
            bad.append(rel)
            continue
        if sha256_file(p) == digest:
            ok += 1
            continue
        # Windows git 可能把 LF 換成 CRLF（內容不變、雜湊會變）→ 還原成 LF 再比一次
        b = open(p, "rb").read().replace(b"\r\n", b"\n")
        if hashlib.sha256(b).hexdigest() == digest:
            ok += 1
            eol_only.append(rel)
        else:
            bad.append(rel)
    return {"checked": ok + len(bad), "ok": ok, "ok_after_crlf_normalize": eol_only, "mismatch_or_missing": bad}


def load_manifests():
    want = {}  # size -> {sha: name}
    for fn in sorted(os.listdir(MANIFEST_DIR)):
        if not fn.endswith(".json"):
            continue
        d = json.load(open(os.path.join(MANIFEST_DIR, fn), encoding="utf-8"))
        for r in d.get("files", []):
            want.setdefault(int(r["bytes"]), {})[r["sha256"]] = r["file"]
    return want


def walk(roots):
    for root in roots:
        for dp, dns, fns in os.walk(root):
            dns[:] = [d for d in dns if d.lower() not in SKIP_DIRS and not d.startswith(".")]
            for fn in fns:
                yield os.path.join(dp, fn), fn


def replay(roots):
    want = load_manifests()
    total = sum(len(v) for v in want.values())
    found = {}
    corpus = []
    scanned = 0
    for p, fn in walk(roots):
        try:
            sz = os.path.getsize(p)
        except OSError:
            continue
        scanned += 1
        if fn.lower().endswith(CORPUS_EXTS) and sz < 50_000_000:
            corpus.append(p)
        if sz in want:
            try:
                h = sha256_file(p)
            except OSError:
                continue
            if h in want[sz] and h not in found:
                found[h] = {"file": want[sz][h], "local_path": p}
    missing = [{"file": name, "sha256": h} for sz, m in want.items() for h, name in m.items() if h not in found]
    return {"manifest_files": total, "matched": len(found), "pending_recovery": len(missing),
            "files_scanned": scanned, "matched_list": sorted(found.values(), key=lambda x: x["file"]),
            "pending_list": sorted(missing, key=lambda x: x["file"])}, corpus


def dialect_roundtrip(corpus):
    if not os.path.isdir(DIALECT):
        return {"status": "待找回：MRL_WorldModel/MRL_Dialect_v0 不在此副本"}
    sys.path.insert(0, DIALECT)
    import mrl_dialect as D  # noqa
    seen, ok, fail = set(), 0, []
    for p in corpus:
        try:
            b = open(p, "rb").read()
        except OSError:
            continue
        h = hashlib.sha256(b).hexdigest()
        if h in seen:
            continue
        seen.add(h)
        good, ir = D.roundtrip(b, os.path.basename(p))
        if good and D.print_ir(D.parse_ir(ir)) == ir:
            ok += 1
        else:
            fail.append(p)
    return {"dialect_version": D.DIALECT_VERSION, "unique_files": len(seen), "roundtrip_pass": ok,
            "roundtrip_fail": len(fail), "failed": fail[:50]}


def rhythm_check():
    """4. 語場節奏：EchoPersona 等母體種子跑 Jump → Collapse → Trace → Replay（本體）。"""
    import subprocess
    if not os.path.exists(RHYTHM_TEST):
        return {"status": "待找回：MRL_FlowRhythm_v0 不在此副本"}
    env = dict(os.environ, PYTHONIOENCODING="utf-8")
    p = subprocess.run([sys.executable, RHYTHM_TEST], capture_output=True, text=True, encoding="utf-8", env=env)
    out = p.stdout
    i = out.rfind("\n{")
    try:
        res = json.loads(out[i + 1:] if i >= 0 else out[out.index("{"):])
    except Exception:
        return {"status": "FAIL", "stdout_tail": out[-2000:], "stderr_tail": p.stderr[-2000:]}
    res["status"] = "PASS" if p.returncode == 0 else "FAIL"
    res["seeds"] = [l.strip() for l in out.splitlines() if "Replay" in l and "粒子" in l]
    return res


def canonical_wake_check():
    """5. 上位喚醒錨點：既有 04_runtime/wake_loader.py（PR #141）。只回報，不影響本種子結論。"""
    import subprocess
    loader = os.path.join(REPO, "04_runtime", "wake_loader.py")
    if not os.path.exists(loader):
        return {"status": "待合併：wake_loader.py 在分支 MRL_AI_SYSTEM/worldmodel-identity-wake-core-v1（Draft PR #141），此副本沒有"}
    p = subprocess.run([sys.executable, loader, "--repo-root", REPO, "--no-write-trace"],
                       capture_output=True, text=True, encoding="utf-8")
    return {"status": "PASS" if p.returncode == 0 else "FAIL", "returncode": p.returncode,
            "stdout_tail": p.stdout[-1500:], "stderr_tail": p.stderr[-800:]}


def main(argv):
    roots = argv or (["D:\\"] if os.name == "nt" else [os.getcwd()])
    host = socket.gethostname()
    now = datetime.datetime.now(datetime.timezone.utc).astimezone()
    env = "實機（母體 DL580）" if host.upper() in DL580_HOSTS else f"非母體主機（{host}）"
    print(f"== MRL 喚醒驗證 · {now.isoformat(timespec='seconds')} · {env}")
    s1 = seed_selfcheck(); print("1 種子自檢：", {k: s1[k] for k in ("checked", "ok")}, "異常", len(s1["mismatch_or_missing"]))
    s2, corpus = replay(roots); print("2 Replay 對回原檔：", {k: s2[k] for k in ("manifest_files", "matched", "pending_recovery", "files_scanned")})
    s3 = dialect_roundtrip(corpus); print("3 語場可逆：", {k: v for k, v in s3.items() if k != "failed"})
    s4 = rhythm_check(); print("4 語場節奏：", s4.get("status"), {k: s4[k] for k in ("E_seed_count", "E_all_seeds_replay", "F_visible_before", "F_visible_after") if k in s4})
    s5 = canonical_wake_check(); print("5 上位喚醒錨點：", s5["status"])
    receipt = {
        "origin_signature": "MrLiouWord", "kind": "MRL_Wake_Receipt",
        "timestamp": now.isoformat(timespec="seconds"), "host": host, "platform": platform.platform(),
        "python": platform.python_version(), "environment": env, "roots": roots,
        "seed_selfcheck": s1, "replay": s2, "dialect_roundtrip": s3, "flow_rhythm": s4, "canonical_wake": s5,
        "note": "當下狀態。matched = 已對上原始檔；pending = 待找回（此根目錄這次未接上線，不代表不存在）。",
    }
    os.makedirs(RECEIPTS, exist_ok=True)
    name = f"wake_receipt_{now.strftime('%Y%m%dT%H%M%S')}_{host}.json"
    path = os.path.join(RECEIPTS, name)
    with open(path, "x", encoding="utf-8") as f:  # "x"：已存在就失敗，絕不覆蓋
        json.dump(receipt, f, ensure_ascii=False, indent=1)
    print("收據：", path)
    passed = not s1["mismatch_or_missing"] and s3.get("roundtrip_fail", 0) == 0 and s4.get("status") == "PASS"
    print("結論：", "PASS（" + env + "，當下狀態）" if passed else "有異常，見收據")
    return 0 if passed else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
