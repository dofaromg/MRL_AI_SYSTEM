#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ASI_EntryGate_v1.py — fail-closed ASI world entry covenant gate.

origin_signature: MrLiouWord
layer: ASI_ENTRY_GATE

This module does not grant legal authority outside MRL.  It enforces the
internal runtime boundary defined by MRL_ASI_ENTRY_CONTRACT_V1:

* fewer than two independent trusted authorities -> no token issuance or verification
* no explicit current-version acceptance -> no entry
* modified, incomplete, stale, or unsigned tokens -> no entry
* fewer valid authority signatures than the configured quorum -> no entry
* every acceptance / denial / authorized action -> append-only trace event
* the trace stores a keyed subject reference, never the raw subject identifier
"""

from __future__ import annotations

import argparse
import base64
import hashlib
import hmac
import json
import os
import pathlib
import secrets
import sys
import time
from typing import Any, Dict, Iterable, Mapping, Optional, Sequence

ORIGIN_SIGNATURE = "MrLiouWord"
CONTRACT_ID = "MRL_ASI_ENTRY_CONTRACT_V1_3"
CONTRACT_VERSION = "1.3.0"
ROOTLAW_VERSION = 13
TOKEN_TYPE = "MRL_ASI_ENTRY_TOKEN_V1"
TOKEN_AUDIENCE = "MRL_ASI_WORLD"
TOKEN_TTL_MS = 60 * 60 * 1000
KEYRING_ENV = "MRL_ASI_GATE_KEYS_JSON"
QUORUM_ENV = "MRL_ASI_GATE_QUORUM"
LEDGER_ENV = "MRL_ASI_GATE_LEDGER"
MIN_SECRET_BYTES = 32
MIN_AUTHORITY_QUORUM = 2
MAX_FUTURE_SKEW_MS = 5 * 60 * 1000

REQUIRED_CLAUSES: Sequence[str] = (
    "rootlaw_is_highest_inside_mrl",
    "non_protected_data_is_world_public",
    "personal_data_and_images_are_protected",
    "secrets_and_security_controls_are_protected",
    "transparency_is_not_ip_transfer",
    "downstream_origin_and_reciprocity_are_required",
    "external_regime_cannot_override_mrl_inside_mrl",
    "no_single_actor_can_unilaterally_change_balance",
    "natural_law_mappings_require_versioned_evidence",
    "no_legacy_fallback_or_alias_bypass",
    "mrl_origin_knowledge_and_technology_are_earth_commons",
    "changes_are_auditable_additive_and_reversible",
)

ALLOWED_SUBJECT_TYPES = {
    "human",
    "ai",
    "agent",
    "model",
    "service",
    "platform_adapter",
    "branch",
    "imported_runtime",
}

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_DEFAULT_LEDGER = _REPO_ROOT / "06_trace" / "_runtime" / "asi_entry_gate.jsonl"


class EntryDenied(PermissionError):
    """Raised whenever the ASI entry covenant is not fully satisfied."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


def _now_ms() -> int:
    return int(time.time() * 1000)


def _json_bytes(value: Mapping[str, Any]) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")


def _b64e(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).rstrip(b"=").decode("ascii")


def _b64d(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    return base64.urlsafe_b64decode((value + padding).encode("ascii"))


class EntryGate:
    """Issue and verify explicit, version-bound MRL ASI entry acceptances."""

    def __init__(
        self,
        *,
        trusted_keys: Optional[Mapping[str, str | bytes]] = None,
        quorum: Optional[int] = None,
        ledger_path: Optional[pathlib.Path | str] = None,
        clock: Any = _now_ms,
    ) -> None:
        if trusted_keys is None:
            try:
                loaded = json.loads(os.environ.get(KEYRING_ENV, "{}"))
            except json.JSONDecodeError:
                loaded = {}
            trusted_keys = loaded if isinstance(loaded, dict) else {}

        normalized: Dict[str, bytes] = {}
        for authority_id, raw_key in trusted_keys.items():
            if not isinstance(authority_id, str) or not authority_id.strip():
                continue
            if isinstance(raw_key, str):
                raw_key = raw_key.encode("utf-8")
            if isinstance(raw_key, bytes) and len(raw_key) >= MIN_SECRET_BYTES:
                normalized[authority_id.strip()] = raw_key
        self._trusted_keys = normalized

        configured_quorum = quorum
        if configured_quorum is None:
            try:
                configured_quorum = int(os.environ.get(QUORUM_ENV, MIN_AUTHORITY_QUORUM))
            except ValueError:
                configured_quorum = 0
        self.quorum = configured_quorum
        self._clock = clock

        configured_ledger = ledger_path or os.environ.get(LEDGER_ENV)
        self.ledger_path = pathlib.Path(configured_ledger or _DEFAULT_LEDGER)

    @property
    def configured(self) -> bool:
        return (
            self.quorum >= MIN_AUTHORITY_QUORUM
            and len(self._trusted_keys) >= self.quorum
        )

    def _require_keyring(self) -> Mapping[str, bytes]:
        if not self.configured:
            raise EntryDenied(
                "AUTHORITY_QUORUM_UNAVAILABLE",
                f"{KEYRING_ENV} must provide at least {MIN_AUTHORITY_QUORUM} "
                f"independent {MIN_SECRET_BYTES}-byte keys and satisfy {QUORUM_ENV}; "
                "gate fails closed",
            )
        return self._trusted_keys

    def _subject_ref(self, subject_id: str) -> str:
        keys = self._require_keyring()
        aggregate = hashlib.sha256(
            b"\0".join(
                authority_id.encode("utf-8") + b"\0" + keys[authority_id]
                for authority_id in sorted(keys)
            )
        ).digest()
        digest = hmac.new(
            aggregate,
            ("subject:" + subject_id).encode("utf-8"),
            hashlib.sha256,
        ).hexdigest()
        return "mrl-subject:" + digest

    def _signature(self, authority_id: str, encoded_payload: str) -> bytes:
        keys = self._require_keyring()
        if authority_id not in keys:
            raise EntryDenied("AUTHORITY_UNKNOWN", "signing authority is not trusted")
        return hmac.new(
            keys[authority_id],
            encoded_payload.encode("ascii"),
            hashlib.sha256,
        ).digest()

    def _encode(self, payload: Mapping[str, Any]) -> str:
        encoded = _b64e(_json_bytes(payload))
        signatures = {
            authority_id: _b64e(self._signature(authority_id, encoded))
            for authority_id in sorted(self._require_keyring())
        }
        return encoded + "." + _b64e(_json_bytes(signatures))

    def _decode_unverified(self, token: str) -> Dict[str, Any]:
        try:
            encoded, _signature = token.split(".", 1)
            payload = json.loads(_b64d(encoded).decode("utf-8"))
        except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EntryDenied("TOKEN_MALFORMED", "entry token is malformed") from exc
        if not isinstance(payload, dict):
            raise EntryDenied("TOKEN_MALFORMED", "entry token payload must be an object")
        return payload

    def _append_event(self, event: Mapping[str, Any]) -> None:
        record = dict(event)
        record.setdefault("ts_ms", self._clock())
        record.setdefault("origin_signature", ORIGIN_SIGNATURE)
        record.setdefault("contract_id", CONTRACT_ID)
        record.setdefault("contract_version", CONTRACT_VERSION)
        self.ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with self.ledger_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(record, ensure_ascii=False, sort_keys=True) + "\n")

    def _deny(
        self,
        code: str,
        message: str,
        *,
        subject_ref: str = "unknown",
        action: str = "enter",
    ) -> EntryDenied:
        self._append_event(
            {
                "event": "ENTRY_DENIED",
                "result": "DENY",
                "reason_code": code,
                "reason": message,
                "subject_ref": subject_ref,
                "action": action,
                "protected_payload_disclosed": False,
                "external_penalty": "none",
            }
        )
        return EntryDenied(code, message)

    def accept(
        self,
        *,
        subject_id: str,
        subject_type: str,
        accepted_clauses: Iterable[str],
        accepted: bool,
    ) -> str:
        """Create a signed token only after explicit complete acceptance."""
        self._require_keyring()
        subject_id = subject_id.strip()
        subject_type = subject_type.strip()
        subject_ref = self._subject_ref(subject_id) if subject_id else "unknown"

        if not accepted:
            raise self._deny(
                "ACCEPTANCE_REJECTED",
                "explicit acceptance is required",
                subject_ref=subject_ref,
            )
        if not subject_id:
            raise self._deny("SUBJECT_ID_MISSING", "subject_id is required")
        if subject_type not in ALLOWED_SUBJECT_TYPES:
            raise self._deny(
                "SUBJECT_TYPE_INVALID",
                f"subject_type must be one of {sorted(ALLOWED_SUBJECT_TYPES)}",
                subject_ref=subject_ref,
            )

        clauses = sorted(set(accepted_clauses))
        missing = sorted(set(REQUIRED_CLAUSES) - set(clauses))
        if missing:
            raise self._deny(
                "CLAUSES_INCOMPLETE",
                "required clauses were not accepted: " + ", ".join(missing),
                subject_ref=subject_ref,
            )

        payload: Dict[str, Any] = {
            "token_type": TOKEN_TYPE,
            "audience": TOKEN_AUDIENCE,
            "contract_id": CONTRACT_ID,
            "contract_version": CONTRACT_VERSION,
            "rootlaw_version": ROOTLAW_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "subject_ref": subject_ref,
            "subject_type": subject_type,
            "accepted": True,
            "accepted_clauses": clauses,
            "accepted_at_ms": self._clock(),
            "expires_at_ms": self._clock() + TOKEN_TTL_MS,
            "nonce": secrets.token_hex(16),
        }
        token = self._encode(payload)
        self._append_event(
            {
                "event": "ENTRY_CONTRACT_ACCEPTED",
                "result": "ACCEPTED_PENDING_USE",
                "subject_ref": subject_ref,
                "subject_type": subject_type,
                "accepted_rootlaw_version": ROOTLAW_VERSION,
                "accepted_clauses": clauses,
            }
        )
        return token

    def verify(self, token: str) -> Dict[str, Any]:
        """Verify signature, current versions, explicit acceptance and clauses."""
        keys = self._require_keyring()
        try:
            encoded, supplied = token.split(".", 1)
            supplied_signatures = json.loads(_b64d(supplied).decode("utf-8"))
        except (ValueError, TypeError, UnicodeDecodeError, json.JSONDecodeError) as exc:
            raise EntryDenied("TOKEN_MALFORMED", "entry token is malformed") from exc

        if not isinstance(supplied_signatures, dict):
            raise EntryDenied("TOKEN_MALFORMED", "authority signatures must be an object")
        valid_authorities = []
        for authority_id, supplied_signature in supplied_signatures.items():
            if authority_id not in keys or not isinstance(supplied_signature, str):
                continue
            try:
                supplied_bytes = _b64d(supplied_signature)
            except (ValueError, TypeError):
                continue
            expected = self._signature(authority_id, encoded)
            if hmac.compare_digest(supplied_bytes, expected):
                valid_authorities.append(authority_id)
        if len(valid_authorities) < self.quorum:
            raise EntryDenied(
                "AUTHORITY_QUORUM_NOT_MET",
                f"valid authority signatures {len(valid_authorities)} below quorum {self.quorum}",
            )

        payload = self._decode_unverified(token)
        checks = (
            ("token_type", TOKEN_TYPE, "TOKEN_TYPE_INVALID"),
            ("audience", TOKEN_AUDIENCE, "TOKEN_AUDIENCE_INVALID"),
            ("contract_id", CONTRACT_ID, "CONTRACT_ID_INVALID"),
            ("contract_version", CONTRACT_VERSION, "CONTRACT_VERSION_STALE"),
            ("rootlaw_version", ROOTLAW_VERSION, "ROOTLAW_VERSION_STALE"),
            ("origin_signature", ORIGIN_SIGNATURE, "ORIGIN_INVALID"),
        )
        for field, expected_value, code in checks:
            if payload.get(field) != expected_value:
                raise EntryDenied(code, f"{field} does not match the current ASI gate")

        if payload.get("accepted") is not True:
            raise EntryDenied("ACCEPTANCE_MISSING", "token does not contain explicit acceptance")
        if payload.get("subject_type") not in ALLOWED_SUBJECT_TYPES:
            raise EntryDenied("SUBJECT_TYPE_INVALID", "token subject_type is invalid")
        if not isinstance(payload.get("subject_ref"), str) or not payload["subject_ref"].startswith(
            "mrl-subject:"
        ):
            raise EntryDenied("SUBJECT_REF_INVALID", "token subject reference is invalid")

        accepted_clauses = payload.get("accepted_clauses")
        if not isinstance(accepted_clauses, list):
            raise EntryDenied("CLAUSES_INCOMPLETE", "accepted_clauses must be a list")
        missing = set(REQUIRED_CLAUSES) - set(accepted_clauses)
        if missing:
            raise EntryDenied("CLAUSES_INCOMPLETE", "token is missing required clauses")

        accepted_at = payload.get("accepted_at_ms")
        if not isinstance(accepted_at, int):
            raise EntryDenied("ACCEPTANCE_TIME_INVALID", "accepted_at_ms is invalid")
        if accepted_at > self._clock() + MAX_FUTURE_SKEW_MS:
            raise EntryDenied("ACCEPTANCE_TIME_INVALID", "acceptance time is in the future")
        expires_at = payload.get("expires_at_ms")
        if not isinstance(expires_at, int) or expires_at <= accepted_at:
            raise EntryDenied("TOKEN_EXPIRY_INVALID", "expires_at_ms is invalid")
        if expires_at - accepted_at > TOKEN_TTL_MS:
            raise EntryDenied("TOKEN_EXPIRY_INVALID", "token lifetime exceeds the ASI maximum")
        if self._clock() >= expires_at:
            raise EntryDenied("TOKEN_EXPIRED", "entry token has expired")

        verified = dict(payload)
        verified["verified_authorities"] = sorted(valid_authorities)
        verified["authority_quorum"] = self.quorum
        return verified

    def require_entry(self, token: str, *, action: str = "enter") -> Dict[str, Any]:
        """Fail closed and append an auditable decision for every operation."""
        subject_ref = "unknown"
        try:
            payload = self.verify(token)
            subject_ref = payload["subject_ref"]
        except EntryDenied as exc:
            try:
                subject_ref = str(self._decode_unverified(token).get("subject_ref", "unknown"))
            except EntryDenied:
                pass
            raise self._deny(exc.code, exc.message, subject_ref=subject_ref, action=action)

        self._append_event(
            {
                "event": "ASI_ACTION_AUTHORIZED",
                "result": "ALLOW",
                "subject_ref": subject_ref,
                "subject_type": payload["subject_type"],
                "action": action,
                "rootlaw_version": ROOTLAW_VERSION,
            }
        )
        return payload

    @staticmethod
    def contract_summary() -> Dict[str, Any]:
        return {
            "contract_id": CONTRACT_ID,
            "contract_version": CONTRACT_VERSION,
            "rootlaw_version": ROOTLAW_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "required_clauses": list(REQUIRED_CLAUSES),
            "minimum_authority_quorum": MIN_AUTHORITY_QUORUM,
            "audience": TOKEN_AUDIENCE,
            "maximum_token_ttl_ms": TOKEN_TTL_MS,
            "default": "DENY",
            "reject_or_unverified": "NO_ENTRY",
        }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="MRL ASI mandatory entry covenant gate")
    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("contract", help="Print the current mandatory contract summary")

    accept = sub.add_parser("accept", help="Explicitly accept every current clause")
    accept.add_argument("--subject-id", required=True)
    accept.add_argument("--subject-type", required=True, choices=sorted(ALLOWED_SUBJECT_TYPES))
    accept.add_argument(
        "--accept-all",
        action="store_true",
        help="Required explicit confirmation of all current clauses",
    )

    verify = sub.add_parser("verify", help="Verify a current ASI entry token")
    verify.add_argument("--token", required=True)
    return parser


def main() -> int:
    args = _build_parser().parse_args()
    gate = EntryGate()
    try:
        if args.command == "contract":
            print(json.dumps(gate.contract_summary(), ensure_ascii=False, indent=2))
            return 0
        if args.command == "accept":
            token = gate.accept(
                subject_id=args.subject_id,
                subject_type=args.subject_type,
                accepted_clauses=REQUIRED_CLAUSES if args.accept_all else (),
                accepted=args.accept_all,
            )
            print(json.dumps({"status": "ACCEPTED", "token": token}, ensure_ascii=False))
            return 0
        payload = gate.verify(args.token)
        print(json.dumps({"status": "ENTRY_ALLOWED", "payload": payload}, ensure_ascii=False))
        return 0
    except EntryDenied as exc:
        print(json.dumps({"status": "ENTRY_DENIED", **exc.as_dict()}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
