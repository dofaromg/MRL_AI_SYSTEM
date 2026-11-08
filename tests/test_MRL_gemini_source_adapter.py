"""Contract tests for the closed-by-default Gemini external-source adapter."""

from __future__ import annotations

import MRL_Gemini_SourceAdapter_v1 as gemini
from MRL_Gemini_SourceAdapter_v1 import (
    MRLNativeGeminiSourceAdapter,
    register_gemini_source_adapter,
)
from MRL_OriginBoundary_Guard_v1 import verify_signature
from llm_adapter import LLMGateway, LLMRequest


def _request(**extra):
    return LLMRequest(
        model="gemini-3.7-flash",
        messages=[
            {"role": "system", "content": "Return concise text."},
            {"role": "user", "content": "synthetic smoke test"},
        ],
        max_tokens=64,
        temperature=0.2,
        extra=extra,
    )


def test_external_gate_is_closed_by_default(monkeypatch):
    called = {"network": False}

    def fake_post(*_args, **_kwargs):
        called["network"] = True
        return {}

    monkeypatch.delenv("MRL_GEMINI_EXTERNAL_ENABLED", raising=False)
    monkeypatch.setattr(gemini, "_http_post_json", fake_post)
    response = MRLNativeGeminiSourceAdapter(api_key="secret").complete(_request())
    assert response.ok is False
    assert response.error == "MRL_EXTERNAL_GATE_CLOSED"
    assert called["network"] is False


def test_sensitive_request_never_reaches_network(monkeypatch):
    called = {"network": False}

    def fake_post(*_args, **_kwargs):
        called["network"] = True
        return {}

    monkeypatch.setattr(gemini, "_http_post_json", fake_post)
    adapter = MRLNativeGeminiSourceAdapter(api_key="secret", enabled=True)
    response = adapter.complete(_request(mrl_sensitive=True))
    assert response.ok is False
    assert response.error == "MRL_SENSITIVE_LOCAL_ONLY"
    assert called["network"] is False


def test_missing_key_fails_without_network(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    called = {"network": False}

    def fake_post(*_args, **_kwargs):
        called["network"] = True
        return {}

    monkeypatch.setattr(gemini, "_http_post_json", fake_post)
    response = MRLNativeGeminiSourceAdapter(api_key="", enabled=True).complete(_request())
    assert response.ok is False
    assert response.error == "MRL_GEMINI_API_KEY_MISSING"
    assert called["network"] is False


def test_response_is_normalized_and_provenance_is_sealed(monkeypatch):
    captured = {}

    def fake_post(url, payload, headers, timeout=60):
        captured.update(url=url, payload=payload, headers=headers, timeout=timeout)
        return {
            "modelVersion": "gemini-3.7-flash-20260813",
            "candidates": [{
                "content": {"parts": [{"text": "external material result"}]},
                "finishReason": "STOP",
            }],
            "usageMetadata": {
                "promptTokenCount": 11,
                "candidatesTokenCount": 4,
            },
        }

    monkeypatch.setattr(gemini, "_http_post_json", fake_post)
    adapter = MRLNativeGeminiSourceAdapter(api_key="test-secret", enabled=True)
    response = adapter.complete(_request())

    assert response.ok is True
    assert response.text == "external material result"
    assert response.input_tokens == 11
    assert response.output_tokens == 4
    assert captured["headers"]["x-goog-api-key"] == "test-secret"
    assert "test-secret" not in captured["url"]
    assert captured["url"].endswith("/models/gemini-3.7-flash:generateContent")
    assert captured["payload"]["systemInstruction"]["parts"][0]["text"] == "Return concise text."

    boundary = response.raw["mrl_boundary"]
    assert boundary["source_external_name"] == "Google Gemini API"
    assert boundary["role"] == "material"
    assert boundary["origin"] == "MrLiouWord"
    assert verify_signature(boundary) is True
    serialized = str(response.raw)
    assert "synthetic smoke test" not in serialized
    assert "test-secret" not in serialized


def test_registration_is_explicit_model_only():
    gateway = LLMGateway()
    adapter = register_gemini_source_adapter(
        gateway,
        api_key="k",
        model="gemini-3.7-flash",
        enabled=False,
    )
    assert gateway.adapter_for("gemini-3.7-flash") is adapter

