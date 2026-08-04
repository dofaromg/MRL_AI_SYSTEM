#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Canonical tokenless MRL URL component.

The URL identifies a layer and a content-addressed object.  It never grants
authority.  In particular, ``mrl://asi`` addresses contain no account, token,
session, credential, or raw environmental measurement.  Measured values and
their units/calibration live in the referenced FieldFrame whose SHA-256 is in
``src``.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence, Tuple
from urllib.parse import parse_qsl, urlencode, urlsplit

ORIGIN_SIGNATURE = "MrLiouWord"
COMPONENT_ID = "MRL_URL_V1"
COMPONENT_VERSION = "1.0.0"
SCHEME = "mrl"
FORMAT_VERSION = "1"

LAYERS = {"asi", "world", "projection", "source", "trace"}
FIELD_MODES = {"measured", "simulated", "inferred"}
_HEX64 = re.compile(r"^[0-9a-f]{64}$")
_IDENTIFIER = re.compile(r"^[a-z0-9](?:[a-z0-9._~-]{0,62}[a-z0-9])?$")
_CREDENTIAL_KEYS = {
    "token",
    "access_token",
    "api_key",
    "key",
    "secret",
    "credential",
    "auth",
    "authorization",
    "password",
    "session",
    "cookie",
    "subject",
    "account",
}


class MRLURLError(ValueError):
    """Fail-closed parsing or construction error."""

    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message

    def as_dict(self) -> Dict[str, str]:
        return {"code": self.code, "message": self.message}


def _validate_identifier(value: str, *, field: str) -> str:
    if not isinstance(value, str) or not _IDENTIFIER.fullmatch(value):
        raise MRLURLError(
            "IDENTIFIER_INVALID",
            f"{field} must be 1-64 characters of canonical lowercase ASCII",
        )
    return value


def _validate_source_hash(value: str) -> str:
    if not isinstance(value, str) or not _HEX64.fullmatch(value):
        raise MRLURLError(
            "SOURCE_HASH_INVALID",
            "src must be a lowercase 64-character SHA-256 digest",
        )
    return value


def _validate_route(layer: str, segments: Sequence[str]) -> Tuple[str, ...]:
    checked = tuple(
        _validate_identifier(segment, field=f"path segment {index}")
        for index, segment in enumerate(segments)
    )
    valid = False
    if layer == "asi":
        valid = (
            (len(checked) == 2 and checked[0] == "field")
            or (
                len(checked) == 4
                and checked[0] == "field"
                and checked[2] == "frame"
            )
            or (
                len(checked) == 6
                and checked[0] == "field"
                and checked[2] == "frame"
                and checked[4] == "po"
            )
        )
    elif layer == "world":
        valid = len(checked) == 3 and checked[1] == "node"
    elif layer == "projection":
        valid = (
            len(checked) == 4
            and checked[0] == "surface"
            and checked[2] == "resource"
        )
    elif layer == "source":
        valid = len(checked) == 2 and checked[0] == "object"
    elif layer == "trace":
        valid = len(checked) == 2 and checked[0] == "event"
    if not valid:
        raise MRLURLError(
            "ROUTE_INVALID",
            f"path does not match a canonical {layer} route",
        )
    return checked


@dataclass(frozen=True)
class MRLURL:
    """Parsed immutable MRL URL value object."""

    layer: str
    segments: Tuple[str, ...]
    source_hash: str
    field_mode: Optional[str] = None
    format_version: str = FORMAT_VERSION

    def __post_init__(self) -> None:
        if self.layer not in LAYERS:
            raise MRLURLError("LAYER_INVALID", f"unsupported MRL layer: {self.layer}")
        _validate_route(self.layer, self.segments)
        _validate_source_hash(self.source_hash)
        if self.format_version != FORMAT_VERSION:
            raise MRLURLError("FORMAT_VERSION_INVALID", "only MRL URL format v1 is accepted")
        if self.layer == "asi":
            if self.field_mode not in FIELD_MODES:
                raise MRLURLError(
                    "FIELD_MODE_REQUIRED",
                    "ASI addresses require measured, simulated, or inferred mode",
                )
        elif self.field_mode is not None:
            raise MRLURLError(
                "FIELD_MODE_FORBIDDEN",
                "mode belongs only to tokenless ASI FieldFrame addresses",
            )

    @property
    def is_tokenless_asi(self) -> bool:
        return self.layer == "asi"

    def to_url(self) -> str:
        query = [("v", self.format_version), ("src", self.source_hash)]
        if self.field_mode is not None:
            query.append(("mode", self.field_mode))
        return f"{SCHEME}://{self.layer}/{'/'.join(self.segments)}?{urlencode(query)}"

    def as_dict(self) -> Dict[str, Any]:
        return {
            "component_id": COMPONENT_ID,
            "component_version": COMPONENT_VERSION,
            "origin_signature": ORIGIN_SIGNATURE,
            "url": self.to_url(),
            "scheme": SCHEME,
            "layer": self.layer,
            "segments": list(self.segments),
            "format_version": self.format_version,
            "source_hash": self.source_hash,
            "field_mode": self.field_mode,
            "grants_authority": False,
            "asi_tokenless": self.is_tokenless_asi,
        }


def parse_mrl_url(value: str, *, require_canonical: bool = True) -> MRLURL:
    """Parse an MRL URL and reject ambiguous, credential-bearing forms."""
    if not isinstance(value, str) or not value or len(value) > 2048:
        raise MRLURLError("URL_INVALID", "MRL URL must be a non-empty string up to 2048 bytes")
    try:
        split = urlsplit(value)
        port = split.port
    except ValueError as exc:
        raise MRLURLError("URL_INVALID", "MRL URL authority is malformed") from exc

    if split.scheme != SCHEME:
        raise MRLURLError("SCHEME_INVALID", "MRL URLs require the mrl scheme")
    if split.username is not None or split.password is not None:
        raise MRLURLError("USERINFO_FORBIDDEN", "identity or credentials cannot appear in MRL URLs")
    if port is not None:
        raise MRLURLError("PORT_FORBIDDEN", "MRL component URLs are not network endpoints")
    if split.fragment:
        raise MRLURLError("FRAGMENT_FORBIDDEN", "hidden fragment semantics are not allowed")
    if split.netloc not in LAYERS or split.hostname != split.netloc:
        raise MRLURLError("LAYER_INVALID", "URL authority must be a canonical MRL layer")
    if not split.path.startswith("/") or split.path.endswith("/"):
        raise MRLURLError("PATH_INVALID", "path must be absolute without a trailing slash")
    if "%" in split.path:
        raise MRLURLError(
            "ENCODED_PATH_FORBIDDEN",
            "percent-encoded or Unicode identifiers are forbidden in canonical paths",
        )

    segments = tuple(part for part in split.path.split("/") if part)
    checked_segments = _validate_route(split.netloc, segments)
    try:
        pairs = parse_qsl(split.query, keep_blank_values=True, strict_parsing=True)
    except ValueError as exc:
        raise MRLURLError("QUERY_INVALID", "query string is malformed") from exc

    keys = [key for key, _value in pairs]
    if len(keys) != len(set(keys)):
        raise MRLURLError("QUERY_DUPLICATE", "duplicate query keys are forbidden")
    lowered = {key.lower() for key in keys}
    if lowered & _CREDENTIAL_KEYS:
        raise MRLURLError(
            "CREDENTIAL_IN_URL",
            "token, account, session, identity, or credential data is forbidden",
        )
    allowed = {"v", "src", "mode"} if split.netloc == "asi" else {"v", "src"}
    if set(keys) - allowed:
        raise MRLURLError("QUERY_KEY_FORBIDDEN", "unknown or layer-incompatible query key")
    query = dict(pairs)
    if query.get("v") != FORMAT_VERSION:
        raise MRLURLError("FORMAT_VERSION_INVALID", "v=1 is required")
    source_hash = _validate_source_hash(query.get("src", ""))
    field_mode = query.get("mode")

    parsed = MRLURL(
        layer=split.netloc,
        segments=checked_segments,
        source_hash=source_hash,
        field_mode=field_mode,
    )
    if require_canonical and parsed.to_url() != value:
        raise MRLURLError(
            "URL_NON_CANONICAL",
            "URL is valid in meaning but not in the one canonical serialized form",
        )
    return parsed


def canonicalize_mrl_url(value: str) -> str:
    return parse_mrl_url(value, require_canonical=False).to_url()


def build_asi_field(field_id: str, *, source_hash: str, mode: str) -> str:
    return MRLURL("asi", ("field", field_id), source_hash, mode).to_url()


def build_asi_frame(
    field_id: str,
    frame_id: str,
    *,
    source_hash: str,
    mode: str,
) -> str:
    return MRLURL(
        "asi",
        ("field", field_id, "frame", frame_id),
        source_hash,
        mode,
    ).to_url()


def build_asi_po(
    field_id: str,
    frame_id: str,
    po_id: str,
    *,
    source_hash: str,
    mode: str,
) -> str:
    return MRLURL(
        "asi",
        ("field", field_id, "frame", frame_id, "po", po_id),
        source_hash,
        mode,
    ).to_url()


def build_world_node(world_id: str, node_id: str, *, source_hash: str) -> str:
    return MRLURL("world", (world_id, "node", node_id), source_hash).to_url()


def build_projection_resource(
    surface_id: str,
    resource_id: str,
    *,
    source_hash: str,
) -> str:
    return MRLURL(
        "projection",
        ("surface", surface_id, "resource", resource_id),
        source_hash,
    ).to_url()


def build_source_object(source_id: str, *, source_hash: str) -> str:
    return MRLURL("source", ("object", source_id), source_hash).to_url()


def build_trace_event(event_id: str, *, source_hash: str) -> str:
    return MRLURL("trace", ("event", event_id), source_hash).to_url()


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Parse and canonicalize MRL URL v1")
    commands = parser.add_subparsers(dest="command", required=True)
    parse = commands.add_parser("parse")
    parse.add_argument("url")
    canonical = commands.add_parser("canonicalize")
    canonical.add_argument("url")
    return parser


def main() -> int:
    args = _parser().parse_args()
    try:
        if args.command == "canonicalize":
            result: Any = {"url": canonicalize_mrl_url(args.url)}
        else:
            result = parse_mrl_url(args.url).as_dict()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except MRLURLError as exc:
        print(json.dumps({"status": "DENIED", **exc.as_dict()}, ensure_ascii=False), file=sys.stderr)
        return 3


if __name__ == "__main__":
    raise SystemExit(main())
