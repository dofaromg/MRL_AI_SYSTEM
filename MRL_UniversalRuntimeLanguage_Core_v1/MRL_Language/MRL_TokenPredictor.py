# MRL_TokenPredictor
# origin_signature: MrLiouWord
# layer: MRL_Language (L2 PARTICLE + L4 PERCEPTION)
"""Token 預測核心：基於粒子語言層的 N-gram 確定性 token 預測。

設計原則：
  - 純 stdlib，零外部依賴，確定性，可重現。
  - 使用 fltnz particle（word/ws/nl）作為 token 單位。
  - 模型：Unigram + Bigram（Laplace 平滑）。
  - 感知場加權：可選傳入 MRL_PerceptionField 提升高感知節點相關 token 的機率。
  - 正式主體詞 = Particle Token；不使用外部 LLM/神經網路詞彙表。

主要類別：
  MRL_TokenCorpus      — 從文字或 MrLiouIR 節點內容建立 token 語料
  MRL_NGramModel       — Unigram + Bigram N-gram 語言模型（Laplace 平滑）
  MRL_TokenPredictor   — 組合入口：fit → predict / predict_weighted
"""

from __future__ import annotations

import hashlib
import json
import math
import re
from typing import Any, Dict, List, Optional, Tuple

ORIGIN_SIGNATURE = "MrLiouWord"

# ─── 斷詞（與 fltnz_parser 對齊：word/ws/nl） ─────────────────────────────────

_TOKEN_RE = re.compile(r"(\n|\r\n|\r|[ \t]+|\S+)")


def _tokenise(text: str) -> List[str]:
    """text → word token 串列（過濾 ws/nl，保留 word）。"""
    tokens: List[str] = []
    for m in _TOKEN_RE.finditer(text or ""):
        val = m.group(0)
        if val.strip() and val not in ("\n", "\r\n", "\r"):
            tokens.append(val)
    return tokens


# ─── MRL_TokenCorpus ──────────────────────────────────────────────────────────

class MRL_TokenCorpus:
    """從文字列表或 MrLiouIR 節點建立 token 語料（純 word token，確定性）。"""

    def __init__(self) -> None:
        self.sentences: List[List[str]] = []

    def add_text(self, text: str) -> None:
        """依換行切句，每句斷 word token。"""
        for line in text.splitlines():
            toks = _tokenise(line)
            if toks:
                self.sentences.append(toks)

    def add_mrliouir(self, mrliouir: Dict[str, Any]) -> None:
        """從 MrLiouIR 節點 content 欄位建立語料。"""
        for node in mrliouir.get("nodes", []):
            toks = _tokenise(node.get("content", ""))
            if toks:
                self.sentences.append(toks)

    @property
    def all_tokens(self) -> List[str]:
        return [t for s in self.sentences for t in s]

    def checksum(self) -> str:
        """語料指紋（確定性，供驗收）。"""
        return hashlib.sha256(
            json.dumps(self.sentences, ensure_ascii=False).encode("utf-8")
        ).hexdigest()


# ─── MRL_NGramModel ───────────────────────────────────────────────────────────

_BOS = "<BOS>"   # 句首標記
_EOS = "<EOS>"   # 句尾標記


class MRL_NGramModel:
    """Unigram + Bigram N-gram 語言模型（Laplace 平滑，確定性）。

    predict_next(context_token) → [(token, prob), ...]（降序，確定性）。
    """

    def __init__(self) -> None:
        self._unigram: Dict[str, int] = {}     # token → count
        self._bigram: Dict[str, Dict[str, int]] = {}  # prev → {next → count}
        self._vocab_size: int = 0
        self._total_tokens: int = 0
        self._fitted: bool = False

    def fit(self, corpus: "MRL_TokenCorpus") -> "MRL_NGramModel":
        """從語料訓練模型。"""
        for sentence in corpus.sentences:
            seq = [_BOS] + sentence + [_EOS]
            for tok in seq:
                self._unigram[tok] = self._unigram.get(tok, 0) + 1
            for prev, nxt in zip(seq, seq[1:]):
                bg = self._bigram.setdefault(prev, {})
                bg[nxt] = bg.get(nxt, 0) + 1
        self._vocab_size = len(self._unigram)
        self._total_tokens = sum(self._unigram.values())
        self._fitted = True
        return self

    def unigram_prob(self, token: str) -> float:
        """Unigram 機率（Laplace 平滑）。"""
        count = self._unigram.get(token, 0)
        return (count + 1.0) / (self._total_tokens + self._vocab_size)

    def predict_next(
        self, context_token: str, top_k: int = 5
    ) -> List[Tuple[str, float]]:
        """給定 context_token，預測下一個 token（Bigram + Laplace 平滑）。

        回傳：[(token, prob), ...] 降序，長度 = top_k。
        """
        if not self._fitted:
            raise RuntimeError("MRL_NGramModel: call fit() before predict_next()")
        bg = self._bigram.get(context_token, {})
        # 候選集：bigram 見過的 + unigram 全詞表
        candidates = set(bg.keys()) | set(self._unigram.keys())
        total_bg = sum(bg.values()) + self._vocab_size  # Laplace 分母
        scored: List[Tuple[str, float]] = []
        for tok in candidates:
            if tok in (_BOS,):
                continue
            cnt = bg.get(tok, 0)
            prob = (cnt + 1.0) / total_bg
            scored.append((tok, prob))
        scored.sort(key=lambda x: (-x[1], x[0]))  # 機率降序，同分以字母序 tiebreak
        return scored[:top_k]

    def log_perplexity(self, corpus: "MRL_TokenCorpus") -> float:
        """計算語料的 log perplexity（越低越好；確定性評估指標）。"""
        if not self._fitted:
            raise RuntimeError("not fitted")
        log_sum = 0.0
        count = 0
        for sentence in corpus.sentences:
            seq = [_BOS] + sentence + [_EOS]
            for prev, nxt in zip(seq, seq[1:]):
                bg = self._bigram.get(prev, {})
                total_bg = sum(bg.values()) + self._vocab_size
                cnt = bg.get(nxt, 0)
                prob = (cnt + 1.0) / total_bg
                log_sum += math.log(prob)
                count += 1
        if count == 0:
            return float("inf")
        return round(-log_sum / count, 6)


# ─── MRL_TokenPredictor ───────────────────────────────────────────────────────

class MRL_TokenPredictor:
    """Token 預測核心：結合 N-gram 語言模型 + 感知場加權。

    使用方式：
        pred = MRL_TokenPredictor()
        pred.fit(["line one", "line two"])
        results = pred.predict("context_token", top_k=5)
        # 或感知場加權（需傳入 perception_field dict: node_id → weight）
        results_w = pred.predict_weighted("context_token", perception_field, top_k=5)
    """

    def __init__(self) -> None:
        self.origin_signature = ORIGIN_SIGNATURE
        self.corpus = MRL_TokenCorpus()
        self.model = MRL_NGramModel()
        self._fitted: bool = False

    def fit(
        self,
        texts: Optional[List[str]] = None,
        mrliouir: Optional[Dict[str, Any]] = None,
    ) -> "MRL_TokenPredictor":
        """從文字列表 + MrLiouIR 建立語料並訓練模型。"""
        corpus = MRL_TokenCorpus()
        for t in (texts or []):
            corpus.add_text(t)
        if mrliouir:
            corpus.add_mrliouir(mrliouir)
        self.corpus = corpus
        self.model = MRL_NGramModel().fit(corpus)
        self._fitted = True
        return self

    def predict(
        self, context_token: str, top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """純 N-gram 預測（不加感知場）。

        回傳：[{"token": ..., "prob": ..., "rank": ...}, ...] 降序。
        """
        if not self._fitted:
            raise RuntimeError("MRL_TokenPredictor: call fit() first")
        raw = self.model.predict_next(context_token, top_k=top_k)
        return [
            {"token": tok, "prob": round(p, 6), "rank": i + 1, "perception_boost": 1.0}
            for i, (tok, p) in enumerate(raw)
        ]

    def predict_weighted(
        self,
        context_token: str,
        perception_field: Dict[str, float],
        top_k: int = 5,
    ) -> List[Dict[str, Any]]:
        """感知場加權預測：N-gram 機率 × 感知場權重（以 token 字串比對 content 欄位）。

        perception_field: node_id → weight（來自 MRL_PerceptionField.field）。
        匹配策略：若某個 node 的 content 包含 context_token，其 weight 視為 boost。
        """
        if not self._fitted:
            raise RuntimeError("MRL_TokenPredictor: call fit() first")
        raw = self.model.predict_next(context_token, top_k=top_k * 3)  # 取多些後再 boost 排序

        # 建立 token → perception_boost 映射：
        # 若 next_token 出現在 perception_field 中 weight 最高的節點之 content，boost > 1。
        # 此處以簡單策略：perception_field 所有 node weight 平均作為 token boost（無 node 文字索引時）。
        avg_weight = (sum(perception_field.values()) / len(perception_field)) if perception_field else 1.0

        boosted: List[Dict[str, Any]] = []
        for tok, prob in raw:
            # 感知 boost：若 token 長度較長（較有語意）且有感知場，給輕微 boost
            boost = 1.0 + (avg_weight * 0.1 * min(1.0, len(tok) / 8.0))
            boosted.append({"token": tok, "prob": prob * boost, "perception_boost": round(boost, 4)})

        boosted.sort(key=lambda x: (-x["prob"], x["token"]))
        return [
            {"token": r["token"], "prob": round(r["prob"], 6), "rank": i + 1,
             "perception_boost": r["perception_boost"]}
            for i, r in enumerate(boosted[:top_k])
        ]

    def info(self) -> Dict[str, Any]:
        """回傳模型基本資訊（可驗、確定性）。"""
        return {
            "origin_signature": ORIGIN_SIGNATURE,
            "fitted": self._fitted,
            "vocab_size": self.model._vocab_size,
            "total_tokens": self.model._total_tokens,
            "sentence_count": len(self.corpus.sentences),
            "corpus_checksum": self.corpus.checksum() if self._fitted else None,
        }


# ─── 便捷入口：fit_from_mrliouir ─────────────────────────────────────────────

def fit_from_mrliouir(mrliouir: Dict[str, Any]) -> MRL_TokenPredictor:
    """從 MrLiouIR 直接建構並訓練 predictor（一步入口）。"""
    return MRL_TokenPredictor().fit(mrliouir=mrliouir)
