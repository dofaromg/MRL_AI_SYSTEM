"""Tests for MRL-owned local-first routing and commercial value evidence."""

from __future__ import annotations

from llm_adapter import LLMAdapter, LLMRequest, LLMResponse
from MRL_ProviderValueGate_v1 import (
    MRLProviderValueGate,
    MRLProviderValueLedger,
)


class FixedAdapter(LLMAdapter):
    def __init__(self, label, *, ok=True, input_tokens=0, output_tokens=0):
        self.label = label
        self.ok = ok
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.calls = 0

    def complete(self, request):
        self.calls += 1
        return LLMResponse(
            text=f"{self.label}:{request.model}" if self.ok else "",
            model=request.model,
            ok=self.ok,
            error=None if self.ok else f"{self.label}_failed",
            input_tokens=self.input_tokens,
            output_tokens=self.output_tokens,
            elapsed_ms=7,
        )

    def name(self):
        return self.label


def _request(**extra):
    return LLMRequest(
        model="gemini-3.7-flash",
        messages=[{"role": "user", "content": "private commercial prompt"}],
        extra=extra,
    )


def test_local_is_default_even_when_external_exists():
    local = FixedAdapter("MRLLocal")
    external = FixedAdapter("GeminiExternal")
    gate = MRLProviderValueGate(
        local_adapter=local,
        local_model="qwen2.5-32b",
        external_adapter=external,
        external_enabled=True,
    )
    result = gate.execute(_request())
    assert result.route == "local"
    assert result.response.model == "qwen2.5-32b"
    assert local.calls == 1
    assert external.calls == 0


def test_sensitive_request_forces_local_when_external_requested():
    local = FixedAdapter("MRLLocal")
    external = FixedAdapter("GeminiExternal")
    gate = MRLProviderValueGate(
        local_adapter=local,
        local_model="qwen2.5-32b",
        external_adapter=external,
        external_enabled=True,
    )
    result = gate.execute(_request(mrl_sensitive=True), use_external=True)
    assert result.route == "local"
    assert result.reason == "sensitive_local_only"
    assert external.calls == 0


def test_external_requires_explicit_request_and_is_metered():
    local = FixedAdapter("MRLLocal")
    external = FixedAdapter("GeminiExternal", input_tokens=1_000_000, output_tokens=500_000)
    ledger = MRLProviderValueLedger(
        external_input_usd_per_million=1.0,
        external_output_usd_per_million=2.0,
    )
    gate = MRLProviderValueGate(
        local_adapter=local,
        local_model="qwen2.5-32b",
        external_adapter=external,
        external_enabled=True,
        ledger=ledger,
    )
    result = gate.execute(_request(), use_external=True)
    snapshot = ledger.snapshot()
    assert result.route == "external_material"
    assert external.calls == 1 and local.calls == 0
    assert snapshot["external_calls"] == 1
    assert snapshot["local_calls"] == 0
    assert snapshot["estimated_external_cost_usd"] == 2.0


def test_external_failure_recovers_to_local_and_records_both_events():
    local = FixedAdapter("MRLLocal")
    external = FixedAdapter("GeminiExternal", ok=False)
    ledger = MRLProviderValueLedger()
    gate = MRLProviderValueGate(
        local_adapter=local,
        local_model="qwen2.5-32b",
        external_adapter=external,
        external_enabled=True,
        ledger=ledger,
    )
    result = gate.execute(_request(), use_external=True)
    snapshot = ledger.snapshot()
    assert result.route == "local_fallback"
    assert result.response.ok is True
    assert external.calls == 1 and local.calls == 1
    assert snapshot["event_count"] == 2
    assert snapshot["external_calls"] == 1
    assert snapshot["local_calls"] == 1
    assert snapshot["fallback_count"] == 1


def test_ledger_retains_hash_not_prompt_or_secret():
    local = FixedAdapter("MRLLocal")
    ledger = MRLProviderValueLedger()
    gate = MRLProviderValueGate(
        local_adapter=local,
        local_model="qwen2.5-32b",
        ledger=ledger,
    )
    gate.execute(_request(api_key="must-not-be-stored"))
    snapshot = ledger.snapshot()
    event = snapshot["events"][0]
    assert len(event["request_sha256"]) == 64
    serialized = str(snapshot)
    assert "private commercial prompt" not in serialized
    assert "must-not-be-stored" not in serialized
    assert snapshot["product_name"] == "MrliouAI"
    assert snapshot["origin_signature"] == "MrLiouWord"
