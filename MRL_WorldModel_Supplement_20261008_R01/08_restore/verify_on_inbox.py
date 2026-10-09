# 實機驗：對 WorldLoop_Inbox 頂層所有可解碼文字檔，確認
#   (1) 本模組正規化結果 == WorldLoop 現役 normalize_for_pipeline 結果（同一 pipeline_text_sha256）
#   (2) restore(normalized, map) 逐位元組 == 原文
# 只讀，不寫任何母體檔。origin_signature: MrLiouWord
import sys, pathlib, json
HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(1, r"D:\mrl\workspace\MRL_RuntimeCivilization_20261007_R01")
import MRL_ParticleIR_Whitespace_Restore as R
import MRL_WorldLoop_Extract as EX
inbox = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else r"D:\MRL_Mother\WorldLoop_Inbox")
tot = applied = same = exact = 0; chars = 0; bad = []
for p in sorted(inbox.iterdir()):
    if not p.is_file() or p.stat().st_size > 16 * 1024 * 1024:
        continue
    try:
        t = p.read_bytes().decode("utf-8")
    except Exception:
        continue
    tot += 1
    n, m = R.normalize_with_map(t)
    wn, wnorm = EX.normalize_for_pipeline(t)
    if n == wn: same += 1
    else: bad.append(("diff_vs_worldloop", p.name))
    if m["nl"] or m["sp"]:
        applied += 1; chars += len(m["nl"]) + len(m["sp"])
    if R.restore(n, m) == t: exact += 1
    else: bad.append(("restore_fail", p.name))
print(json.dumps({"text_files": tot, "normalization_applied": applied, "chars_replaced": chars,
                  "same_as_worldloop": same, "restore_byte_exact": exact, "bad": bad[:10]}, ensure_ascii=False))
