# MRL_ParticleTranslator
# origin_signature: MrLiouWord
# layer: MRL_Language (L2 PARTICLE)
"""粒子翻譯功能：自然語言 ⇄ 粒子語言（可逆）。

建於既有 MRL_ParticleIR_Engine（不另造可逆鏈）：
  - to_particle(text)   文字 → 粒子翻譯（可逆封包 + 粒子語言符號視圖 + 節奏 + 原子）
  - from_particle(pkt)  粒子翻譯 → 還原原文（走引擎 canonical decode，保證無損）
  - roundtrip 驗證：from_particle(to_particle(t)) == t

粒子語言符號視圖沿用母體 .fltnz 風格（⊕Core / ⋄fx.<type>.<nnn> / ∴），
每個詞映射到確定性粒子碼，附 glyph_dict 以供人讀與反查。
"""
from __future__ import annotations

import hashlib
import importlib.util
import pathlib
import re
from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"
PRODUCT = "MrliouAI"


def _load_engine():
    """載入同層 MRL_ParticleIR_Engine（可逆鏈後端）。"""
    here = pathlib.Path(__file__).resolve().parent
    cand = here / "MRL_ParticleIR_Engine.py"
    spec = importlib.util.spec_from_file_location("mrl_particle_engine", cand)
    mod = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(mod)
    return mod


_engine = _load_engine()

# 粒子碼類別（確定性啟發式）：數字 / 拉丁詞 / CJK 符 / 其他。
def _particle_type(word: str) -> str:
    if re.fullmatch(r"\d+", word):
        return "num"
    if re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", word):
        return "wrd"
    if re.search(r"[一-鿿]", word):
        return "sym"
    return "sig"


def _glyph_for(word: str) -> str:
    """確定性粒子碼 ⋄fx.<type>.<nnn>（同詞恆得同碼）。"""
    h = hashlib.sha256(word.encode("utf-8")).hexdigest()
    nnn = int(h[:4], 16) % 1000
    return f"⋄fx.{_particle_type(word)}.{nnn:03d}"


def _words(text: str) -> List[str]:
    # 以引擎 token 抽出 word 類（與可逆鏈同源），保序去空白。
    env = _engine.encode(text)
    toks = _engine._fltnz._decompress_tokens(env["tokens"])
    return [t["v"] for t in toks if t.get("t") == "word"]


def to_particle(text: str, label: str = "translate") -> Dict[str, Any]:
    """文字 → 粒子翻譯封包（可逆 + 符號視圖）。"""
    if not isinstance(text, str):
        raise TypeError("to_particle 需要字串")
    envelope = _engine.encode(text)                 # canonical 可逆封包
    words = _words(text)
    glyph_dict: Dict[str, str] = {}
    lines = [f"⊕Core: {label}"]
    seen = []
    for w in words:
        g = _glyph_for(w)
        glyph_dict[g] = w
        seen.append(g)
    # 以 ∴ 分節呈現（母體 .fltnz 風格）
    for i, g in enumerate(seen):
        sep = " ∴" if (i and i % 4 == 0) else ""
        lines.append(f"{sep}{g}    # {glyph_dict[g]}")
    symbolic = "\n".join(lines)
    src_hash = hashlib.sha256(text.encode("utf-8")).hexdigest()
    atoms = [{"atom_id": f"MRL_P_{i+1:04d}", "glyph": g, "semantic": glyph_dict[g]}
             for i, g in enumerate(seen)]
    verified = _engine.decode(envelope) == text
    return {
        "origin_signature": ORIGIN_SIGNATURE,
        "product": PRODUCT,
        "mrl_kind": "MRL_ParticleTranslation",
        "direction": "text_to_particle",
        "source_text": text,
        "source_hash": src_hash,
        "symbolic": symbolic,
        "glyph_dict": glyph_dict,
        "atoms": atoms,
        "rhythm": _engine.rhythm(text),
        "particle_envelope": envelope,
        "verified_roundtrip": verified,
    }


def from_particle(pkt: Dict[str, Any]) -> str:
    """粒子翻譯封包 → 還原原文（走 canonical envelope，保證無損）。"""
    if not isinstance(pkt, dict) or "particle_envelope" not in pkt:
        raise ValueError("from_particle 需要含 particle_envelope 的翻譯封包")
    return _engine.decode(pkt["particle_envelope"])


def translate(text: str, direction: str = "to_particle", label: str = "translate") -> Dict[str, Any]:
    """統一入口。direction: 'to_particle'（預設）或 'roundtrip'（附還原驗證）。"""
    pkt = to_particle(text, label=label)
    if direction == "roundtrip":
        pkt["restored_text"] = from_particle(pkt)
        pkt["roundtrip_ok"] = pkt["restored_text"] == text
    return pkt


if __name__ == "__main__":  # 簡易自測 / CLI
    import json
    import sys
    src = " ".join(sys.argv[1:]) or "MrLiouWord 母體 粒子語言 翻譯 test 123"
    out = translate(src, direction="roundtrip")
    print(out["symbolic"])
    print("--- roundtrip_ok:", out["roundtrip_ok"], "---")
    print(json.dumps({k: out[k] for k in ("source_hash", "rhythm", "verified_roundtrip")},
                     ensure_ascii=False))
