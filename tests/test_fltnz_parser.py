"""
Tests for fltnz_parser — bidirectional txt ↔ fltnz ↔ flpkg ↔ trace chain.
"""
import hashlib
import json

import pytest

import fltnz_parser as fp


# ─── Tokeniser ────────────────────────────────────────────────────────────────

class TestTokenise:
    def test_plain_words(self):
        tokens = fp._tokenise("hello world")
        types = [t["t"] for t in tokens]
        assert types == ["word", "ws", "word"]
        assert tokens[0]["v"] == "hello"
        assert tokens[2]["v"] == "world"

    def test_newlines_are_nl(self):
        tokens = fp._tokenise("a\nb")
        assert tokens[1]["t"] == "nl"
        assert tokens[1]["v"] == "\n"

    def test_crlf_normalised(self):
        tokens = fp._tokenise("a\r\nb")
        nl_tokens = [t for t in tokens if t["t"] == "nl"]
        assert len(nl_tokens) == 1
        assert nl_tokens[0]["v"] == "\n"

    def test_tabs_are_ws(self):
        tokens = fp._tokenise("a\tb")
        assert tokens[1]["t"] == "ws"

    def test_empty_string(self):
        assert fp._tokenise("") == []

    def test_only_whitespace(self):
        tokens = fp._tokenise("   ")
        assert all(t["t"] == "ws" for t in tokens)

    def test_punctuation_is_word(self):
        tokens = fp._tokenise("a, b.")
        words = [t["v"] for t in tokens if t["t"] == "word"]
        assert "a," in words
        assert "b." in words


# ─── Compress / Decompress ────────────────────────────────────────────────────

class TestCompressDecompress:
    def test_no_repetition(self):
        raw = fp._tokenise("hello world")
        compressed = fp._compress_tokens(raw)
        # No refs when all words are unique
        assert all(t["t"] != "ref" for t in compressed)

    def test_back_reference_created(self):
        raw = fp._tokenise("hello hello")
        compressed = fp._compress_tokens(raw)
        ref_tokens = [t for t in compressed if t["t"] == "ref"]
        assert len(ref_tokens) >= 1

    def test_roundtrip_simple(self):
        raw = fp._tokenise("the cat sat on the mat")
        compressed = fp._compress_tokens(raw)
        decompressed = fp._decompress_tokens(compressed)
        assert fp._tokens_to_text(decompressed) == "the cat sat on the mat"

    def test_roundtrip_no_repetition(self):
        raw = fp._tokenise("one two three")
        compressed = fp._compress_tokens(raw)
        decompressed = fp._decompress_tokens(compressed)
        assert fp._tokens_to_text(decompressed) == "one two three"

    def test_out_of_range_ref_raises(self):
        bad_tokens = [{"t": "ref", "v": 99}]
        with pytest.raises(ValueError, match="back-reference"):
            fp._decompress_tokens(bad_tokens)

    def test_ws_not_back_referenced(self):
        # Whitespace tokens should not be replaced by refs
        raw = fp._tokenise("a  b  c")  # double-space
        compressed = fp._compress_tokens(raw)
        # ws tokens must remain as-is (not ref)
        ws_tokens = [t for t in compressed if t["v"] == "  "]
        assert all(t["t"] == "ws" for t in ws_tokens)


# ─── Checksum ─────────────────────────────────────────────────────────────────

class TestChecksum:
    def test_sha256_deterministic(self):
        h1 = fp._sha256_text("hello")
        h2 = fp._sha256_text("hello")
        assert h1 == h2

    def test_sha256_correct(self):
        expected = hashlib.sha256("hello".encode("utf-8")).hexdigest()
        assert fp._sha256_text("hello") == expected

    def test_sha256_different_inputs(self):
        assert fp._sha256_text("hello") != fp._sha256_text("world")


# ─── Encode / Decode ──────────────────────────────────────────────────────────

class TestEncodeDecode:
    def test_encode_returns_required_keys(self):
        env = fp.encode("hello world")
        for key in ("fltnz_version", "origin_signature", "encoding", "checksum", "length", "tokens"):
            assert key in env

    def test_encode_version(self):
        env = fp.encode("x")
        assert env["fltnz_version"] == fp.FLTNZ_VERSION

    def test_encode_origin_signature(self):
        env = fp.encode("x")
        assert env["origin_signature"] == fp.ORIGIN_SIGNATURE

    def test_encode_checksum_matches(self):
        text = "The quick brown fox"
        env = fp.encode(text)
        assert env["checksum"] == fp._sha256_text(text)

    def test_encode_length(self):
        text = "hello"
        env = fp.encode(text)
        assert env["length"] == len(text.encode("utf-8"))

    def test_decode_roundtrip(self):
        original = "Hello, MRL!\nSecond line."
        env = fp.encode(original)
        assert fp.decode(env) == original

    def test_decode_roundtrip_unicode(self):
        original = "怎麼過去，就怎麼回來"
        env = fp.encode(original)
        assert fp.decode(env) == original

    def test_decode_checksum_mismatch_raises(self):
        env = fp.encode("hello")
        env["checksum"] = "badhash"
        with pytest.raises(ValueError, match="checksum mismatch"):
            fp.decode(env)

    def test_decode_no_checksum_skips_check(self):
        env = fp.encode("hello")
        del env["checksum"]
        # Should not raise; checksum check is skipped when key absent
        result = fp.decode(env)
        assert result == "hello"

    def test_decode_empty_string(self):
        assert fp.decode(fp.encode("")) == ""

    def test_encode_decode_multiword_repeated(self):
        text = "the fox and the fox"
        assert fp.decode(fp.encode(text)) == text


# ─── Map layer ────────────────────────────────────────────────────────────────

class TestMapLayer:
    def test_to_map_keys(self):
        env = fp.encode("hello world hello")
        m = fp.to_map(env)
        for key in ("map_version", "source_checksum", "total_tokens", "word_count", "unique_words", "word_positions"):
            assert key in m

    def test_to_map_word_positions(self):
        env = fp.encode("hello world hello")
        m = fp.to_map(env)
        assert "hello" in m["word_positions"]
        assert len(m["word_positions"]["hello"]) == 2

    def test_from_map_returns_original_envelope(self):
        env = fp.encode("hello world")
        m = fp.to_map(env)
        recovered = fp.from_map(m, env)
        assert recovered is env

    def test_from_map_checksum_mismatch_raises(self):
        env = fp.encode("hello world")
        other = fp.encode("different text")
        m = fp.to_map(env)
        with pytest.raises(ValueError, match="source_checksum"):
            fp.from_map(m, other)


# ─── Pack / Unpack ────────────────────────────────────────────────────────────

class TestPackUnpack:
    def test_pack_keys(self):
        env = fp.encode("test")
        bundle = fp.pack(env, label="my_label")
        for key in ("flpkg_version", "origin_signature", "label", "created_at_ms", "payload", "payload_type"):
            assert key in bundle

    def test_pack_label(self):
        env = fp.encode("test")
        bundle = fp.pack(env, label="mylabel")
        assert bundle["label"] == "mylabel"

    def test_pack_default_label(self):
        env = fp.encode("test")
        bundle = fp.pack(env)
        assert bundle["label"] == "unnamed"

    def test_pack_payload_type(self):
        env = fp.encode("test")
        bundle = fp.pack(env)
        assert bundle["payload_type"] == "fltnz"

    def test_unpack_roundtrip(self):
        env = fp.encode("hello")
        bundle = fp.pack(env)
        assert fp.unpack(bundle) == env

    def test_unpack_wrong_payload_type_raises(self):
        bundle = {"payload_type": "other", "payload": {}}
        with pytest.raises(ValueError, match="payload_type"):
            fp.unpack(bundle)


# ─── Seal / Unseal ────────────────────────────────────────────────────────────

class TestSealUnseal:
    def test_seal_keys(self):
        env = fp.encode("test")
        bundle = fp.pack(env)
        trace = fp.seal(bundle)
        for key in ("event_type", "origin_signature", "layer", "sealed_at_ms", "bundle_checksum", "bundle"):
            assert key in trace

    def test_seal_checksum_valid(self):
        env = fp.encode("test")
        bundle = fp.pack(env)
        trace = fp.seal(bundle)
        bundle_bytes = json.dumps(bundle, ensure_ascii=False, sort_keys=True).encode("utf-8")
        expected = hashlib.sha256(bundle_bytes).hexdigest()
        assert trace["bundle_checksum"] == expected

    def test_unseal_roundtrip(self):
        env = fp.encode("hello")
        bundle = fp.pack(env)
        trace = fp.seal(bundle)
        recovered_bundle = fp.unseal(trace)
        assert recovered_bundle == bundle

    def test_unseal_tampered_checksum_raises(self):
        env = fp.encode("hello")
        bundle = fp.pack(env)
        trace = fp.seal(bundle)
        trace["bundle_checksum"] = "badhash"
        with pytest.raises(ValueError, match="bundle_checksum mismatch"):
            fp.unseal(trace)

    def test_unseal_tampered_bundle_raises(self):
        env = fp.encode("hello")
        bundle = fp.pack(env)
        trace = fp.seal(bundle)
        trace["bundle"]["label"] = "tampered"
        with pytest.raises(ValueError, match="bundle_checksum mismatch"):
            fp.unseal(trace)


# ─── Full-chain helpers ───────────────────────────────────────────────────────

class TestFullChain:
    def test_text_to_trace_and_back(self):
        text = "Full chain test — 怎麼過去，就怎麼回來"
        trace = fp.text_to_trace(text, label="test")
        recovered = fp.trace_to_text(trace)
        assert recovered == text

    def test_text_to_trace_is_dict(self):
        trace = fp.text_to_trace("hello")
        assert isinstance(trace, dict)

    def test_trace_to_text_empty(self):
        trace = fp.text_to_trace("")
        assert fp.trace_to_text(trace) == ""

    def test_text_to_trace_label(self):
        trace = fp.text_to_trace("x", label="my_label")
        assert trace["bundle"]["label"] == "my_label"
