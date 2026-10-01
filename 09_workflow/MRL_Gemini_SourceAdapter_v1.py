#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_Gemini_SourceAdapter_v1.py — Gemini external-source adapter for MrliouAI.

origin_signature: MrLiouWord
product: MrliouAI
role: external material / replaceable compute adapter

The adapter deliberately keeps the Gemini provider outside the MRL core:

* outbound calls are disabled by default;
* sensitive requests are rejected before network access;
* API keys are sent in a header and are never placed in URLs or trace data;
* responses are normalized to the existing MRL LLMResponse contract;
* external provenance is retained and sealed through MRL_OriginBoundaryGuard;
* prompts and raw provider responses are not copied into the trace envelope.

Only Python's standard library is used.  Gemini is a replaceable source of
compute, never the product identity or the canonical source of MRL memory.
"""

from __future__ import annotations

import hashlib
import json
import os
import time
import urllib.parse
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

from llm_adapter import LLMAdapter, LLMRequest, LLMResponse
from MRL_OriginBoundary_Guard_v1 import MRL_OriginBoundaryGuard


ORIGIN_SIGNATURE = "MrLiouWord"
PRODUCT_NAME = "MrliouAI"
PROVIDER_ROLE = "external_material"
DEFAULT_MODEL = "gemini-3.7-flash"
DEFAULT_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"
DEFAULT_TIMEOUT = 60


def _env_enabled(name: str) -> bool:
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _http_post_json(
    url: str,
    payload: Dict[str, Any],
    headers: Dict[str, str],
    timeout: int = DEFAULT_TIMEOUT,
) -> Dict[str, Any]:
    """POST JSON without a provider SDK.  Secrets stay in request headers."""
    data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data,
        method="POST",
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json",
            **headers,
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _content_to_text(content: Any) -> str:
    """Normalize the text-only subset of the existing MRL message contract."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        chunks: List[str] = []
        for item in content:
            if isinstance(item, str):
                chunks.append(item)
            elif isinstance(item, dict) and isinstance(item.get("text"), str):
                chunks.append(item["text"])
        return "\n".join(chunks)
    return str(content) if content is not None else ""


def _messages_to_gemini(
    messages: List[Dict[str, Any]],
) -> Tuple[str, List[Dict[str, Any]]]:
    """Convert MRL/OpenAI-style messages into Gemini generateContent input."""
    system_chunks: List[str] = []
    contents: List[Dict[str, Any]] = []

    for message in messages:
        role = str(message.get("role", "user"))
        text = _content_to_text(message.get("content", ""))
        if role == "system":
            system_chunks.append(text)
            continue
        gemini_role = "model" if role == "assistant" else "user"
        contents.append({"role": gemini_role, "parts": [{"text": text}]})

    return "\n\n".join(chunk for chunk in system_chunks if chunk), contents


def _response_text(response: Dict[str, Any]) -> Tuple[str, str]:
    candidates = response.get("candidates") or []
    if not candidates:
        return "", "no_candidate"
    first = candidates[0] or {}
    parts = ((first.get("content") or {}).get("parts") or [])
    text = "".join(
        part.get("text", "")
        for part in parts
        if isinstance(part, dict) and isinstance(part.get("text"), str)
    )
    return text, str(first.get("finishReason") or "stop").lower()


class MRLNativeGeminiSourceAdapter(LLMAdapter):
    """Gemini REST adapter whose external boundary is closed by default."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        *,
        base_url: str = DEFAULT_BASE_URL,
        enabled: Optional[bool] = None,
        timeout: int = DEFAULT_TIMEOUT,
        boundary_guard: Optional[MRL_OriginBoundaryGuard] = None,
    ) -> None:
        self._api_key = api_key or os.environ.get("GEMINI_API_KEY", "")
        self._base_url = base_url.rstrip("/")
        self._enabled = _env_enabled("MRL_GEMINI_EXTERNAL_ENABLED") if enabled is None else bool(enabled)
        self._timeout = timeout
        self._boundary_guard = boundary_guard or MRL_OriginBoundaryGuard()

    @property
    def enabled(self) -> bool:
        return self._enabled

    def _error(self, request: LLMRequest, code: str, t0: float) -> LLMResponse:
        return LLMResponse(
            text="",
            model=request.model,
            ok=False,
            error=code,
            finish_reason="error",
            elapsed_ms=int((time.time() - t0) * 1000),
            called_at_ms=int(t0 * 1000),
            raw={
                "provider_role": PROVIDER_ROLE,
                "product_name": PRODUCT_NAME,
                "origin_signature": ORIGIN_SIGNATURE,
            },
        )

    def complete(self, request: LLMRequest) -> LLMResponse:
        t0 = time.time()

        if not self._enabled:
            return self._error(request, "MRL_EXTERNAL_GATE_CLOSED", t0)

        sensitive = bool(
            request.extra.get("sensitive")
            or request.extra.get("mrl_sensitive")
        )
        if sensitive:
            return self._error(request, "MRL_SENSITIVE_LOCAL_ONLY", t0)

        if not self._api_key:
            return self._error(request, "MRL_GEMINI_API_KEY_MISSING", t0)

        if request.stream:
            return self._error(request, "MRL_GEMINI_STREAM_NOT_MAPPED", t0)

        if request.tools:
            return self._error(request, "MRL_GEMINI_TOOLS_NOT_MAPPED", t0)

        model = request.model or DEFAULT_MODEL
        if not model.startswith("gemini-"):
            return self._error(request, "MRL_GEMINI_MODEL_ID_REQUIRED", t0)

        system_text, contents = _messages_to_gemini(request.messages)
        payload: Dict[str, Any] = {
            "contents": contents,
            "generationConfig": {
                "maxOutputTokens": request.max_tokens,
                "temperature": request.temperature,
            },
        }
        if system_text:
            payload["systemInstruction"] = {"parts": [{"text": system_text}]}

        safe_model = urllib.parse.quote(model, safe="-._")
        url = f"{self._base_url}/models/{safe_model}:generateContent"

        try:
            provider_response = _http_post_json(
                url,
                payload,
                {"x-goog-api-key": self._api_key},
                timeout=self._timeout,
            )
            text, finish_reason = _response_text(provider_response)
            usage = provider_response.get("usageMetadata") or {}
            input_tokens = int(usage.get("promptTokenCount") or 0)
            output_tokens = int(usage.get("candidatesTokenCount") or 0)
            provider_model = str(provider_response.get("modelVersion") or model)

            provenance_payload = {
                "provider": "Google Gemini API",
                "provider_role": PROVIDER_ROLE,
                "provider_model": provider_model,
                "response_sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
                "finish_reason": finish_reason,
                "product_name": PRODUCT_NAME,
            }
            boundary_record = self._boundary_guard.intake_external(
                "Google Gemini API",
                provenance_payload,
            )

            return LLMResponse(
                text=text,
                model=provider_model,
                ok=True,
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                finish_reason=finish_reason,
                elapsed_ms=int((time.time() - t0) * 1000),
                called_at_ms=int(t0 * 1000),
                raw={
                    "mrl_boundary": boundary_record,
                    "provider_role": PROVIDER_ROLE,
                    "origin_signature": ORIGIN_SIGNATURE,
                },
            )
        except Exception as exc:  # noqa: BLE001
            # The key is not in the URL, payload, or returned error envelope.
            return self._error(
                request,
                f"MRL_GEMINI_EXTERNAL_ERROR:{type(exc).__name__}:{exc}",
                t0,
            )

    def name(self) -> str:
        return "MRLNativeGeminiSourceAdapter"


def register_gemini_source_adapter(
    gateway: Any,
    *,
    api_key: Optional[str] = None,
    model: str = DEFAULT_MODEL,
    enabled: Optional[bool] = None,
    base_url: str = DEFAULT_BASE_URL,
) -> MRLNativeGeminiSourceAdapter:
    """Register an explicit model ID; no global provider takeover or aliasing."""
    adapter = MRLNativeGeminiSourceAdapter(
        api_key=api_key,
        base_url=base_url,
        enabled=enabled,
    )
    gateway.register(model, adapter)
    return adapter


if __name__ == "__main__":
    print(json.dumps({
        "module": "MRL_Gemini_SourceAdapter_v1",
        "product_name": PRODUCT_NAME,
        "provider_role": PROVIDER_ROLE,
        "external_enabled_by_default": False,
        "origin_signature": ORIGIN_SIGNATURE,
    }, ensure_ascii=False, indent=2))
