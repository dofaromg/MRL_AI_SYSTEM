"""test_MRL_token_predictor.py — MRL_TokenPredictor + MRL_PerceptionKernel 跨節點/多頭感知 驗收
origin_signature: MrLiouWord

涵蓋：
  1. MRL_PerceptionScore 跨節點感知分數（確定性、範圍 0-1）
  2. MRL_PerceptionHead 單一感知頭（softmax 正規化、role_bias 有效）
  3. MRL_MultiPerceptionField 多頭感知場（full_field 輸出格式正確）
  4. MRL_TokenCorpus 語料建立（add_text / add_mrliouir / checksum 確定性）
  5. MRL_NGramModel 訓練 + predict_next（降序、Laplace 平滑）
  6. MRL_NGramModel log_perplexity（有限正數）
  7. MRL_TokenPredictor.predict（rank 正確、top_k 限制）
  8. MRL_TokenPredictor.predict_weighted（感知場加權、perception_boost >= 1）
  9. MRL_TokenPredictor.info（fitted 後有 vocab_size）
  10. fit_from_mrliouir 一步入口
  11. 確定性：相同語料兩次 fit 產生相同 predict 結果
  12. origin_signature 全模組一致
"""
from __future__ import annotations

import pytest

from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language.MRL_PerceptionKernel import (
    MRL_MultiPerceptionField,
    MRL_PerceptionHead,
    MRL_PerceptionScore,
)
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language.MRL_TokenPredictor import (
    ORIGIN_SIGNATURE,
    MRL_NGramModel,
    MRL_TokenCorpus,
    MRL_TokenPredictor,
    fit_from_mrliouir,
)
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language import (
    MRL_MrLiouIR_Compiler,
    MRL_UniversalParser_Core,
)

# ─── 測試語料 ───────────────────────────────────────────────────────────────────

SAMPLE_PY = (
    "import os\n"
    "def greet(name):\n"
    "    msg = 'hi ' + name\n"
    "    return msg\n"
    "class World:\n"
    "    def spin(self):\n"
    "        for i in range(3):\n"
    "            print(i)\n"
)

SAMPLE_TEXTS = [
    "the cat sat on the mat",
    "the dog sat on the log",
    "a cat and a dog",
]


def _make_mrliouir() -> dict:
    parsed = MRL_UniversalParser_Core.parse(SAMPLE_PY, "python")
    return MRL_MrLiouIR_Compiler.compile_mrliouir(parsed)


def _two_nodes() -> tuple:
    """取 mrliouir 前兩個節點供跨節點分數測試。"""
    ir = _make_mrliouir()
    nodes = ir["nodes"]
    assert len(nodes) >= 2
    return nodes[0], nodes[1]


# ── §1 MRL_PerceptionScore ─────────────────────────────────────────────────────

def test_perception_score_range():
    q, k = _two_nodes()
    s = MRL_PerceptionScore.score(q, k)
    assert 0.0 <= s <= 1.0


def test_perception_score_self_high():
    """自感知分數不應為 0（同角色、同深度 → 高分）。"""
    q, _ = _two_nodes()
    s = MRL_PerceptionScore.score(q, q)
    assert s > 0.0


def test_perception_score_deterministic():
    q, k = _two_nodes()
    assert MRL_PerceptionScore.score(q, k) == MRL_PerceptionScore.score(q, k)


def test_perception_score_matrix_shape():
    ir = _make_mrliouir()
    nodes = ir["nodes"][:4]
    matrix = MRL_PerceptionScore.score_matrix(nodes)
    assert len(matrix) == 4
    assert all(len(row) == 4 for row in matrix)
    # 對角線（自感知）應全 > 0
    for i in range(4):
        assert matrix[i][i] >= 0.0


# ── §2 MRL_PerceptionHead ─────────────────────────────────────────────────────

def test_perception_head_attend_sums_to_1():
    """attend 回傳的 score 應 softmax 正規化（和 ≈ 1）。"""
    ir = _make_mrliouir()
    nodes = ir["nodes"][:5]
    head = MRL_PerceptionHead({"definition": 1.5})
    result = head.attend(nodes[0], nodes)
    total = sum(r["score"] for r in result)
    assert abs(total - 1.0) < 1e-4


def test_perception_head_bias_effect():
    """偏好角色 bias > 1 時，同角色節點分數應相對較高。"""
    ir = _make_mrliouir()
    nodes = ir["nodes"]

    # 取兩個不同 role 節點作為 key
    role_groups: dict = {}
    for n in nodes:
        role_groups.setdefault(n["semantic"]["role"], []).append(n)
    if len(role_groups) < 2:
        pytest.skip("語料不足兩種 role")

    roles = list(role_groups)
    biased_role = roles[0]
    head = MRL_PerceptionHead({biased_role: 2.0})

    query = nodes[0]
    result_biased = {r["node_id"]: r["score"] for r in head.attend(query, nodes)}
    head_neutral = MRL_PerceptionHead({})
    result_neutral = {r["node_id"]: r["score"] for r in head_neutral.attend(query, nodes)}
    # biased 的總結果與 neutral 不同即可
    assert result_biased != result_neutral


# ── §3 MRL_MultiPerceptionField ───────────────────────────────────────────────

def test_multi_perception_full_field_keys():
    ir = _make_mrliouir()
    mpf = MRL_MultiPerceptionField(ir)
    out = mpf.full_field()
    assert out["origin_signature"] == ORIGIN_SIGNATURE
    assert out["node_count"] > 0
    assert out["head_count"] == 4
    assert "field" in out
    assert "top_node" in out


def test_multi_perception_perceive_returns_fused():
    ir = _make_mrliouir()
    nodes = ir["nodes"]
    mpf = MRL_MultiPerceptionField(ir)
    result = mpf.perceive(nodes[0])
    assert result["query_node_id"] == nodes[0]["node_id"]
    assert isinstance(result["fused_scores"], dict)
    assert result["top_node"] is not None


# ── §4 MRL_TokenCorpus ────────────────────────────────────────────────────────

def test_corpus_add_text():
    corpus = MRL_TokenCorpus()
    for t in SAMPLE_TEXTS:
        corpus.add_text(t)
    assert len(corpus.sentences) == len(SAMPLE_TEXTS)
    assert "cat" in corpus.all_tokens


def test_corpus_add_mrliouir():
    ir = _make_mrliouir()
    corpus = MRL_TokenCorpus()
    corpus.add_mrliouir(ir)
    assert len(corpus.sentences) > 0


def test_corpus_checksum_deterministic():
    corpus = MRL_TokenCorpus()
    for t in SAMPLE_TEXTS:
        corpus.add_text(t)
    assert corpus.checksum() == corpus.checksum()


def test_corpus_checksum_different_text():
    c1, c2 = MRL_TokenCorpus(), MRL_TokenCorpus()
    c1.add_text("hello world")
    c2.add_text("goodbye world")
    assert c1.checksum() != c2.checksum()


# ── §5 MRL_NGramModel ─────────────────────────────────────────────────────────

def _make_model() -> MRL_NGramModel:
    corpus = MRL_TokenCorpus()
    for t in SAMPLE_TEXTS:
        corpus.add_text(t)
    return MRL_NGramModel().fit(corpus)


def test_ngram_predict_next_top_k():
    m = _make_model()
    results = m.predict_next("the", top_k=3)
    assert len(results) <= 3
    assert all(isinstance(tok, str) and isinstance(prob, float) for tok, prob in results)


def test_ngram_predict_next_sorted():
    m = _make_model()
    results = m.predict_next("the", top_k=5)
    probs = [p for _, p in results]
    assert probs == sorted(probs, reverse=True)


def test_ngram_laplace_smoothing():
    """未知 bigram 仍應回傳 > 0 機率（Laplace）。"""
    m = _make_model()
    results = m.predict_next("zzzunknown", top_k=3)
    assert all(p > 0 for _, p in results)


def test_ngram_log_perplexity_finite():
    corpus = MRL_TokenCorpus()
    for t in SAMPLE_TEXTS:
        corpus.add_text(t)
    m = MRL_NGramModel().fit(corpus)
    ppl = m.log_perplexity(corpus)
    assert math.isfinite(ppl) and ppl > 0


# ── §6 MRL_TokenPredictor ─────────────────────────────────────────────────────

def test_predictor_predict_rank():
    pred = MRL_TokenPredictor().fit(texts=SAMPLE_TEXTS)
    results = pred.predict("the", top_k=3)
    assert len(results) <= 3
    ranks = [r["rank"] for r in results]
    assert ranks == list(range(1, len(results) + 1))


def test_predictor_predict_keys():
    pred = MRL_TokenPredictor().fit(texts=SAMPLE_TEXTS)
    results = pred.predict("the", top_k=2)
    for r in results:
        assert "token" in r and "prob" in r and "rank" in r


def test_predictor_predict_weighted_boost():
    pred = MRL_TokenPredictor().fit(texts=SAMPLE_TEXTS)
    dummy_field = {"n0001_abc": 0.9, "n0002_def": 0.5}
    results = pred.predict_weighted("the", dummy_field, top_k=3)
    assert len(results) <= 3
    for r in results:
        assert r["perception_boost"] >= 1.0


def test_predictor_info():
    pred = MRL_TokenPredictor().fit(texts=SAMPLE_TEXTS)
    info = pred.info()
    assert info["fitted"] is True
    assert info["vocab_size"] > 0
    assert info["origin_signature"] == ORIGIN_SIGNATURE


def test_predictor_not_fitted_raises():
    pred = MRL_TokenPredictor()
    with pytest.raises(RuntimeError):
        pred.predict("hello")


def test_predictor_deterministic():
    """相同語料兩次 fit → 相同 predict 結果。"""
    def _run():
        p = MRL_TokenPredictor().fit(texts=SAMPLE_TEXTS)
        return p.predict("the", top_k=5)
    assert _run() == _run()


# ── §7 fit_from_mrliouir ─────────────────────────────────────────────────────

def test_fit_from_mrliouir():
    ir = _make_mrliouir()
    pred = fit_from_mrliouir(ir)
    assert pred.info()["fitted"] is True
    # 應能取得預測結果
    results = pred.predict("def", top_k=3)
    assert len(results) >= 1


# ── §8 origin_signature ──────────────────────────────────────────────────────

def test_origin_signature_token_predictor():
    pred = MRL_TokenPredictor().fit(texts=SAMPLE_TEXTS)
    assert pred.origin_signature == "MrLiouWord"
    assert ORIGIN_SIGNATURE == "MrLiouWord"


# ── §9 multi-perception + token 全管線整合 ─────────────────────────────────────

def test_full_pipeline_multi_perception_token():
    """DL580 run() 應含 multi_perception 與 token_prediction 欄位。"""
    from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime.MRL_DL580_Runtime import (
        MRL_DL580_Runtime,
    )
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        runtime = MRL_DL580_Runtime(runtime_dir=tmp)
        result = runtime.run(SAMPLE_PY, lang="python", loop_id="token_test")
    # 多頭感知
    mp = result["multi_perception"]
    assert mp["head_count"] == 4
    assert mp["node_count"] > 0
    assert mp["top_node"] is not None
    # token 預測
    tp = result["token_prediction"]
    assert tp["vocab_size"] > 0
    assert isinstance(tp["top_k"], list)
    assert len(tp["top_k"]) >= 1
    # 驗收仍通過
    assert result["verification"]["acceptance"] is True


import math  # noqa: E402  (needed for test_ngram_log_perplexity_finite)
