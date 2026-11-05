#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ProviderValueGate_v1.py — local-first routing and commercial value ledger.

origin_signature: MrLiouWord
product: MrliouAI

The MRL core owns routing, policy, evidence, memory eligibility, fallback and
cost telemetry.  External models are optional material providers.  The ledger
stores hashes and operational metadata only; prompts, API keys and full model
responses are deliberately excluded.
"""

from __future__ import annotations

import hashlib
import json
import time
import uuid
from dataclasses import asdict, dataclass, field, replace
from typing import Any, Dict, List, Optional

from llm_adapter import LLMAdapter, LLMRequest, LLMResponse

try:
    from MRL_metrics import record as _record_metric
except ImportError:  # pragma: no cover - optional during isolated use
    def _record_metric(_subsystem: str, _latency_ms: int, *, ok: bool = True) -> None:
        return None


ORIGIN_SIGNATURE = "MrLiouWord"
PRODUCT_NAME = "MrliouAI"


def _request_fingerprint(request: LLMRequest) -> str:
    """Create a deterministic trace reference without retaining prompt text."""
    body = {
        "model": request.model,
        "messages": request.messages,
        "max_tokens": request.max_tokens,
        "temperature": request.temperature,
    }
    compact = json.dumps(body, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(compact.encode("utf-8")).hexdigest()


@dataclass(frozen=True)
class MRLProviderValueEvent:
    event_id: str
    timestamp_ms: int
    request_sha256: str
    route: str
    reason: str
    provider_name: str
    provider_role: str
    model: str
    ok: bool
    input_tokens: int
    output_tokens: int
    elapsed_ms: int
    fallback: bool
    estimated_external_cost_usd: float
    product_name: str = PRODUCT_NAME
    origin_signature: str = ORIGIN_SIGNATURE

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class MRLProviderValueLedger:
    """In-memory, exportable ledger for route, usage and external cost evidence."""

    def __init__(
        self,
        *,
        external_input_usd_per_million: float = 0.0,
        external_output_usd_per_million: float = 0.0,
    ) -> None:
        if external_input_usd_per_million < 0 or external_output_usd_per_million < 0:
            raise ValueError("pricing must be non-negative")
        self._input_price = float(external_input_usd_per_million)
        self._output_price = float(external_output_usd_per_million)
        self._events: List[MRLProviderValueEvent] = []

    def record(
        self,
        *,
        request: LLMRequest,
        response: LLMResponse,
        route: str,
        reason: str,
        provider_name: str,
        provider_role: str,
        fallback: bool = False,
    ) -> MRLProviderValueEvent:
        external_cost = 0.0
        if provider_role == "external_material":
            external_cost = (
                response.input_tokens * self._input_price / 1_000_000
                + response.output_tokens * self._output_price / 1_000_000
            )

        event = MRLProviderValueEvent(
            event_id=f"mrl_value_{uuid.uuid4().hex}",
            timestamp_ms=int(time.time() * 1000),
            request_sha256=_request_fingerprint(request),
            route=route,
            reason=reason,
            provider_name=provider_name,
            provider_role=provider_role,
            model=response.model,
            ok=response.ok,
            input_tokens=response.input_tokens,
            output_tokens=response.output_tokens,
            elapsed_ms=response.elapsed_ms,
            fallback=fallback,
            estimated_external_cost_usd=round(external_cost, 12),
        )
        self._events.append(event)
        return event

    def snapshot(self) -> Dict[str, Any]:
        external = [e for e in self._events if e.provider_role == "external_material"]
        local = [e for e in self._events if e.provider_role == "mrl_local"]
        return {
            "product_name": PRODUCT_NAME,
            "origin_signature": ORIGIN_SIGNATURE,
            "event_count": len(self._events),
            "local_calls": len(local),
            "external_calls": len(external),
            "fallback_count": sum(1 for e in self._events if e.fallback),
            "external_input_tokens": sum(e.input_tokens for e in external),
            "external_output_tokens": sum(e.output_tokens for e in external),
            "estimated_external_cost_usd": round(
                sum(e.estimated_external_cost_usd for e in external),
                12,
            ),
            "events": [e.to_dict() for e in self._events],
        }


@dataclass
class MRLProviderResult:
    response: LLMResponse
    route: str
    reason: str
    fallback: bool = False
    ledger_event_ids: List[str] = field(default_factory=list)
    product_name: str = PRODUCT_NAME
    origin_signature: str = ORIGIN_SIGNATURE

    def to_dict(self) -> Dict[str, Any]:
        return {
            "response": self.response.to_dict(),
            "route": self.route,
            "reason": self.reason,
            "fallback": self.fallback,
            "ledger_event_ids": list(self.ledger_event_ids),
            "product_name": self.product_name,
            "origin_signature": self.origin_signature,
        }


class MRLProviderValueGate:
    """
    Route through MRL policy, with local execution as the default and fallback.

    External execution requires all of the following:
      1. gate constructed with external_enabled=True;
      2. caller explicitly passes use_external=True;
      3. request is not sensitive;
      4. an external adapter is present.
    """

    def __init__(
        self,
        *,
        local_adapter: LLMAdapter,
        local_model: str,
        external_adapter: Optional[LLMAdapter] = None,
        external_enabled: bool = False,
        ledger: Optional[MRLProviderValueLedger] = None,
    ) -> None:
        self.local_adapter = local_adapter
        self.local_model = local_model
        self.external_adapter = external_adapter
        self.external_enabled = bool(external_enabled)
        self.ledger = ledger or MRLProviderValueLedger()

    def _local_request(self, request: LLMRequest) -> LLMRequest:
        local_extra = dict(request.extra)
        local_extra.pop("sensitive", None)
        local_extra.pop("mrl_sensitive", None)
        return replace(request, model=self.local_model, extra=local_extra)

    def _run_local(
        self,
        request: LLMRequest,
        *,
        reason: str,
        fallback: bool = False,
        prior_event_ids: Optional[List[str]] = None,
    ) -> MRLProviderResult:
        local_request = self._local_request(request)
        response = self.local_adapter.complete(local_request)
        event = self.ledger.record(
            request=local_request,
            response=response,
            route="local",
            reason=reason,
            provider_name=self.local_adapter.name(),
            provider_role="mrl_local",
            fallback=fallback,
        )
        _record_metric("mrl_provider_gate.local", response.elapsed_ms, ok=response.ok)
        event_ids = list(prior_event_ids or []) + [event.event_id]
        return MRLProviderResult(
            response=response,
            route="local_fallback" if fallback else "local",
            reason=reason,
            fallback=fallback,
            ledger_event_ids=event_ids,
        )

    def execute(
        self,
        request: LLMRequest,
        *,
        use_external: bool = False,
        sensitive: bool = False,
    ) -> MRLProviderResult:
        is_sensitive = bool(
            sensitive
            or request.extra.get("sensitive")
            or request.extra.get("mrl_sensitive")
        )
        if is_sensitive:
            return self._run_local(request, reason="sensitive_local_only")
        if not use_external:
            return self._run_local(request, reason="local_default")
        if not self.external_enabled:
            return self._run_local(request, reason="external_gate_closed")
        if self.external_adapter is None:
            return self._run_local(request, reason="external_adapter_unavailable")

        external_response = self.external_adapter.complete(request)
        external_event = self.ledger.record(
            request=request,
            response=external_response,
            route="external",
            reason="explicit_external_request",
            provider_name=self.external_adapter.name(),
            provider_role="external_material",
            fallback=False,
        )
        _record_metric(
            "mrl_provider_gate.external",
            external_response.elapsed_ms,
            ok=external_response.ok,
        )
        if external_response.ok:
            return MRLProviderResult(
                response=external_response,
                route="external_material",
                reason="explicit_external_request",
                ledger_event_ids=[external_event.event_id],
            )

        return self._run_local(
            request,
            reason="external_failed_local_recovery",
            fallback=True,
            prior_event_ids=[external_event.event_id],
        )


if __name__ == "__main__":
    print(json.dumps({
        "module": "MRL_ProviderValueGate_v1",
        "product_name": PRODUCT_NAME,
        "default_route": "mrl_local",
        "external_role": "external_material",
        "origin_signature": ORIGIN_SIGNATURE,
    }, ensure_ascii=False, indent=2))
