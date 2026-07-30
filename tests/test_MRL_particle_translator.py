"""test_MRL_particle_translator.py — 粒子翻譯功能（文字 ⇄ 粒子語言）
origin_signature: MrLiouWord

驗證：to_particle 產出符號視圖 + 可逆封包 + 節奏 + 原子；
from_particle 無損還原；round-trip 一致（含空字串、中英混合、符號）。
"""
from __future__ import annotations

import importlib.util
import pathlib

REPO = pathlib.Path(__file__).resolve().parent.parent
PT = REPO / "MRL_UniversalRuntimeLanguage_Core_v1" / "MRL_Language" / "MRL_ParticleTranslator.py"


def _load():
    spec = importlib.util.spec_from_file_location("mrl_particle_translator", PT)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_module_exists():
    assert PT.exists(), "MRL_ParticleTranslator.py 必須存在"


def test_to_particle_shape():
    pt = _load()
    o = pt.to_particle("MrLiouWord 母體 粒子語言 translate 42")
    assert o["origin_signature"] == "MrLiouWord"
    assert o["mrl_kind"] == "MRL_ParticleTranslation"
    assert o["symbolic"].startswith("⊕Core:")
    assert "⋄fx." in o["symbolic"]
    assert isinstance(o["glyph_dict"], dict) and o["glyph_dict"]
    assert isinstance(o["atoms"], list)
    assert "particle_envelope" in o and o["verified_roundtrip"] is True


def test_glyph_deterministic():
    pt = _load()
    a = pt.to_particle("記憶")
    b = pt.to_particle("記憶 記憶")
    # 同詞恆得同粒子碼
    code_a = list(a["glyph_dict"].keys())[0]
    assert code_a in b["glyph_dict"]


def test_roundtrip_lossless():
    pt = _load()
    for t in ["hello world", "母體粒子語言", "MrLiou 123 感知",
              "a b c d e f g", "", "symbols: ⊕⋄∴ 中英 42"]:
        o = pt.translate(t, direction="roundtrip")
        assert o["roundtrip_ok"] is True, f"round-trip 失敗: {t!r}"
        assert pt.from_particle(o) == t


def test_from_particle_requires_envelope():
    pt = _load()
    import pytest
    with pytest.raises(ValueError):
        pt.from_particle({"no": "envelope"})
