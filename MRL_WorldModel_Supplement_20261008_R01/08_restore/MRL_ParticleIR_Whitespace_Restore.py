"""
MRL_ParticleIR_Whitespace_Restore.py — 管線前正規化的「逐位元組還原圖」
origin_signature: MrLiouWord ｜ 2026-10-09 ｜ v1.0.0 ｜ Additive-Only（不改母體核心、不改 WorldLoop）

問題（20261007_d「仍待建構者」）：核心 ParticleIR（09_workflow/fltnz_parser.py）對 26 個空白類字元
無法逐位元組還原，WorldLoop 送管線前以 normalize_for_pipeline() 換成 \\n／半形空白 —— 單向、不可逆。
本模組：用與 WorldLoop 完全相同的兩條規則正規化，同時產生 restore_map；
  restore(normalized, restore_map) == original（逐位元組），使「怎麼過去就怎麼回來」在這一段也成立。
段落：Trace（記錄被換掉的每一個字元與位置）→ Replay（逆向套回）。
"""
from __future__ import annotations
import hashlib
import json
import re

# 與 MRL_WorldLoop_Extract.py（R01）同一組規則，不另立標準
_PIPE_NL = re.compile("\r\n|[\r\x0b\x0c\x1c\x1d\x1e\x85\u2028\u2029]")
_PIPE_SP = re.compile("[\x1f\xa0\u1680\u2000-\u200a\u202f\u205f\u3000]")


def normalize_with_map(text: str):
    """回傳 (normalized, restore_map)。restore_map = {"nl": [[pos, orig], ...], "sp": [[pos, orig], ...]}"""
    nl, out, last, shift = [], [], 0, 0
    for m in _PIPE_NL.finditer(text):
        out.append(text[last:m.start()])
        nl.append([m.start() - shift, m.group(0)])     # 在中間文字（NL 已替換）裡 '\n' 的位置
        out.append("\n")
        shift += len(m.group(0)) - 1
        last = m.end()
    out.append(text[last:])
    mid = "".join(out)
    sp = [[m.start(), m.group(0)] for m in _PIPE_SP.finditer(mid)]   # 1 字換 1 字，位置不動
    norm = _PIPE_SP.sub(" ", mid)
    return norm, {"v": 1, "nl": nl, "sp": sp}


def restore(normalized: str, rmap: dict) -> str:
    chars = list(normalized)
    for pos, orig in rmap.get("sp", []):
        assert chars[pos] == " ", f"sp map mismatch at {pos}"
        chars[pos] = orig
    for pos, orig in reversed(rmap.get("nl", [])):
        assert chars[pos] == "\n", f"nl map mismatch at {pos}"
        chars[pos] = orig
    return "".join(chars)


def map_receipt(original: str, normalized: str, rmap: dict) -> dict:
    blob = json.dumps(rmap, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
    return {"kind": "MRL_ParticleIR_RestoreMap.v1", "origin_signature": "MrLiouWord",
            "original_sha256": hashlib.sha256(original.encode("utf-8")).hexdigest(),
            "pipeline_text_sha256": hashlib.sha256(normalized.encode("utf-8")).hexdigest(),
            "restore_map_sha256": hashlib.sha256(blob).hexdigest(),
            "newline_replaced": len(rmap["nl"]), "space_replaced": len(rmap["sp"])}


if __name__ == "__main__":
    import sys
    s = "a\r\nb\rc\u2028d\u3000e\xa0f\x1fg\r\n\r\n"
    n, m = normalize_with_map(s)
    assert restore(n, m) == s
    print("selfcheck ok", map_receipt(s, n, m), file=sys.stdout)
