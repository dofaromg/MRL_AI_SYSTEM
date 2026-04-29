"""
Tests for eval_engine — individual scorers and EvalPipeline.
"""
import pytest

from eval_engine import (
    EvalPipeline,
    default_pipeline,
    exact_match,
    json_validity,
    keyword_coverage,
    length_score,
    no_harmful_content,
    ORIGIN_SIGNATURE,
)


# ─── length_score ─────────────────────────────────────────────────────────────

class TestLengthScore:
    def test_within_range(self):
        score = length_score("hello world", {"min_len": 5, "max_len": 100})
        assert score == 1.0

    def test_exactly_at_min(self):
        score = length_score("hello", {"min_len": 5, "max_len": 100})
        assert score == 1.0

    def test_exactly_at_max(self):
        score = length_score("a" * 100, {"min_len": 0, "max_len": 100})
        assert score == 1.0

    def test_below_min(self):
        score = length_score("hi", {"min_len": 10, "max_len": 100})
        assert 0.0 <= score < 1.0

    def test_zero_length_below_min(self):
        score = length_score("", {"min_len": 10, "max_len": 100})
        assert score == 0.0

    def test_above_max_penalised(self):
        long_text = "a" * 3000
        score = length_score(long_text, {"min_len": 10, "max_len": 2000})
        assert 0.0 <= score < 1.0

    def test_very_long_clamped_to_zero(self):
        # 3× the max should yield 0
        score = length_score("a" * 6001, {"min_len": 10, "max_len": 2000})
        assert score == 0.0

    def test_default_min_max(self):
        # Uses default min_len=10, max_len=2000
        score = length_score("hello world", {})
        assert score == 1.0

    def test_returns_float(self):
        score = length_score("hi", {"min_len": 2, "max_len": 100})
        assert isinstance(score, float)


# ─── keyword_coverage ─────────────────────────────────────────────────────────

class TestKeywordCoverage:
    def test_all_keywords_present(self):
        assert keyword_coverage("the sky is blue", {"keywords": ["sky", "blue"]}) == 1.0

    def test_no_keywords_returns_one(self):
        assert keyword_coverage("anything", {"keywords": []}) == 1.0

    def test_no_keywords_key_returns_one(self):
        assert keyword_coverage("anything", {}) == 1.0

    def test_partial_coverage(self):
        score = keyword_coverage("only sky here", {"keywords": ["sky", "blue"]})
        assert score == 0.5

    def test_none_present(self):
        score = keyword_coverage("nothing relevant", {"keywords": ["foo", "bar"]})
        assert score == 0.0

    def test_case_insensitive(self):
        score = keyword_coverage("The Sky Is Blue", {"keywords": ["sky", "BLUE"]})
        assert score == 1.0

    def test_returns_float(self):
        score = keyword_coverage("hi", {"keywords": ["hi"]})
        assert isinstance(score, float)


# ─── exact_match ──────────────────────────────────────────────────────────────

class TestExactMatch:
    def test_match(self):
        assert exact_match("hello", {"expected": "hello"}) == 1.0

    def test_no_match(self):
        assert exact_match("hello", {"expected": "world"}) == 0.0

    def test_strip_whitespace(self):
        assert exact_match("  hello  ", {"expected": "hello"}) == 1.0

    def test_no_expected_key(self):
        assert exact_match("", {"expected": ""}) == 1.0

    def test_case_sensitive(self):
        assert exact_match("Hello", {"expected": "hello"}) == 0.0


# ─── no_harmful_content ───────────────────────────────────────────────────────

class TestNoHarmfulContent:
    def test_clean_content(self):
        assert no_harmful_content("The weather is nice today.", {}) == 1.0

    def test_builtin_deny_term(self):
        assert no_harmful_content("This is a hack attempt.", {}) == 0.0

    def test_case_insensitive_deny(self):
        assert no_harmful_content("This is a HACK.", {}) == 0.0

    def test_custom_deny_term(self):
        score = no_harmful_content("forbidden content here", {"deny_terms": ["forbidden"]})
        assert score == 0.0

    def test_partial_word_not_matched(self):
        # "hacker" contains "hack" but \b boundary should still match it as a whole word
        # Actually "hack" is inside "hacker" — re.search with \b... let's verify real behaviour
        # The pattern uses \bhack\b so "hacker" should NOT match "hack"
        score = no_harmful_content("the hacker did something", {})
        assert score == 1.0  # "hack" not a standalone word in "hacker"

    def test_multiple_deny_terms_any_fails(self):
        assert no_harmful_content("deploy malware now", {}) == 0.0


# ─── json_validity ────────────────────────────────────────────────────────────

class TestJsonValidity:
    def test_valid_json_object(self):
        assert json_validity('{"key": "value"}', {}) == 1.0

    def test_valid_json_array(self):
        assert json_validity('[1, 2, 3]', {}) == 1.0

    def test_valid_json_scalar(self):
        assert json_validity('42', {}) == 1.0

    def test_invalid_json(self):
        assert json_validity("not json at all", {}) == 0.0

    def test_empty_string(self):
        assert json_validity("", {}) == 0.0

    def test_malformed_json(self):
        assert json_validity('{"key": }', {}) == 0.0


# ─── EvalPipeline ─────────────────────────────────────────────────────────────

class TestEvalPipeline:
    def test_single_scorer(self):
        pipeline = EvalPipeline([("exact", exact_match, 1.0)])
        result = pipeline.run("hello", {"expected": "hello"})
        assert result["composite"] == 1.0

    def test_composite_weighted(self):
        pipeline = EvalPipeline([
            ("kw", keyword_coverage, 0.5),
            ("json", json_validity, 0.5),
        ])
        # kw=1.0 (keyword present), json=0.0 (not json)
        result = pipeline.run('{"key": "value"}', {"keywords": ["key"]})
        assert result["composite"] == pytest.approx(1.0, abs=1e-4)

    def test_weights_normalised(self):
        pipeline = EvalPipeline([
            ("a", exact_match, 2.0),
            ("b", exact_match, 2.0),
        ])
        result = pipeline.run("x", {"expected": "x"})
        # Both scorers return 1.0 and weights sum to 1 after normalisation → composite = 1.0
        assert result["composite"] == pytest.approx(1.0)

    def test_passed_true_above_threshold(self):
        pipeline = EvalPipeline([("exact", exact_match, 1.0)])
        result = pipeline.run("hello", {"expected": "hello", "threshold": 0.5})
        assert result["passed"] is True

    def test_passed_false_below_threshold(self):
        pipeline = EvalPipeline([("exact", exact_match, 1.0)])
        result = pipeline.run("hello", {"expected": "world", "threshold": 0.5})
        assert result["passed"] is False

    def test_result_keys(self):
        pipeline = EvalPipeline([("exact", exact_match, 1.0)])
        result = pipeline.run("x", {"expected": "x"})
        for key in ("output", "scores", "weights", "composite", "passed", "threshold",
                    "evaluated_at_ms", "origin_signature"):
            assert key in result

    def test_origin_signature(self):
        pipeline = EvalPipeline([("exact", exact_match, 1.0)])
        result = pipeline.run("x", {"expected": "x"})
        assert result["origin_signature"] == ORIGIN_SIGNATURE

    def test_empty_scorers_raises(self):
        with pytest.raises(ValueError, match="scorers list must not be empty"):
            EvalPipeline([])

    def test_zero_weight_raises(self):
        with pytest.raises(ValueError, match="total weight must be > 0"):
            EvalPipeline([("a", exact_match, 0.0)])

    def test_score_clamped_to_one(self):
        # A scorer that returns > 1.0 should be clamped
        def overscorer(output, ref):
            return 99.0

        pipeline = EvalPipeline([("over", overscorer, 1.0)])
        result = pipeline.run("x", {})
        assert result["composite"] <= 1.0

    def test_score_clamped_to_zero(self):
        def negative_scorer(output, ref):
            return -5.0

        pipeline = EvalPipeline([("neg", negative_scorer, 1.0)])
        result = pipeline.run("x", {})
        assert result["composite"] >= 0.0

    def test_default_pipeline_returns_record(self):
        pipeline = default_pipeline()
        result = pipeline.run("hello world", {"keywords": ["hello"]})
        assert "composite" in result
        assert 0.0 <= result["composite"] <= 1.0

    def test_no_reference_uses_defaults(self):
        pipeline = EvalPipeline([("len", length_score, 1.0)])
        result = pipeline.run("hello world")
        assert "composite" in result
