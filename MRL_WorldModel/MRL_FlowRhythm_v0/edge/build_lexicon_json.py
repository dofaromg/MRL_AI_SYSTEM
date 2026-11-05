"""
FlowRhythm edge 載體 —— 把建構者 2025-07 原檔的語意字典匯出為 JSON，給 Cloudflare Worker 承載。
origin_signature: MrLiouWord ｜ Additive-Only

本檔不定義任何新語意：直接呼叫 flow_rhythm.load_lexicon()（讀原檔），
只是把結果序列化。pcode_to_code 以「有序配對」輸出，保留 Python dict 插入順序，
因為軌跡尾端的 ⌬map 行依此順序輸出（逐位元組重現所需）。
"""
import hashlib, json, os, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
import flow_rhythm as F  # noqa: E402

OUT = os.path.join(HERE, "lexicon.v%s.json" % F.ENGINE_VERSION)


def main():
    L = F.load_lexicon()
    # 只記實際被讀的 8 個原檔；並與 lexicon/SOURCES.sha256 對照（副本 = 原檔）
    src_hashes = {}
    for line in open(os.path.join(ROOT, "lexicon", "SOURCES.sha256"), encoding="utf-8"):
        want, n = line.rstrip("\n").split("  ", 1)
        got = hashlib.sha256(open(os.path.join(F.LEX_DIR, n), "rb").read()).hexdigest()
        if got != want:
            raise SystemExit(f"原檔雜湊不符：{n}")
        src_hashes[n] = got
    doc = {
        "origin_signature": F.SIGN,
        "engine_version": F.ENGINE_VERSION,
        "generated_by": "MRL_FlowRhythm_v0/edge/build_lexicon_json.py → flow_rhythm.load_lexicon()",
        "lex_dir": os.path.relpath(F.LEX_DIR, F.REPO),
        "sources": L.sources,
        "source_sha256": src_hashes,
        "verb_of": F.VERB_OF,
        "verified_verb_kinds": sorted(F.VERIFIED_VERB_KINDS),
        "module_map": L.module_map,
        "kind": L.kind,
        "pcode_to_code": [[k, v] for k, v in L.pcode_to_code.items()],
    }
    with open(OUT, "w", encoding="utf-8", newline="\n") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)
        f.write("\n")
    print(OUT)


if __name__ == "__main__":
    main()
