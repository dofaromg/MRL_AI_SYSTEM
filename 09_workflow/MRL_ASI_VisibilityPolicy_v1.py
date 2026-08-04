#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_ASI_VisibilityPolicy_v1.py — remove arbitrary hidden/private visibility.

Non-protected data has exactly one visibility in the MRL ASI layer:
MRL_WORLD_PUBLIC.  Protected data is derived by policy and represented by a
non-reversible public stub; it is never implemented as a generic private mode.
"""

from __future__ import annotations

import copy
import json
import os
import pathlib
import re
import uuid
from typing import Any, Dict, Mapping, Optional, Set

ORIGIN_SIGNATURE = "MrLiouWord"
WORLD_PUBLIC = "MRL_WORLD_PUBLIC"
PROTECTED_STUB = "PROTECTED_WITH_PUBLIC_STUB"
QUARANTINED = "QUARANTINED_FOR_REVIEW"

FORBIDDEN_VISIBILITY = {
    "HIDDEN",
    "PRIVATE",
    "UNLISTED",
    "INVISIBLE",
    "SECRET_PRIVATE",
    "LOCAL_ONLY",
}

REMOVED_ENVIRONMENT_PARAMETERS = {
    "MRL_HIDDEN",
    "MRL_HIDDEN_MODE",
    "MRL_PRIVATE",
    "MRL_PRIVATE_MODE",
    "MRL_UNLISTED",
    "MRL_INVISIBLE",
    "MRL_LOCAL_ONLY",
}

PROTECTED_CLASSES = {
    "personal_data",
    "images_and_visual_derivatives",
    "secrets_and_security_controls",
    "rights_restricted_third_party_material",
}

_IMAGE_EXTENSIONS = {
    ".jpg", ".jpeg", ".png", ".gif", ".webp", ".heic", ".heif",
    ".bmp", ".tif", ".tiff", ".svg", ".raw", ".dng", ".mp4", ".mov",
}
_SECRET_KEYS = {
    "password", "passwd", "api_key", "apikey", "private_key", "secret",
    "token", "access_token", "refresh_token", "recovery_code", "credential",
}
_PERSONAL_KEYS = {
    "full_name", "legal_name", "email", "phone", "address", "national_id",
    "passport_number", "health_data", "biometric", "face_embedding",
    "precise_location", "private_conversation",
}
_REMOVED_RECORD_OPTIONS = {
    "private", "is_private", "hidden", "is_hidden", "unlisted", "invisible",
}
_REMOVED_OPTION_TOKENS = {
    "private", "privacy", "hidden", "unlisted", "invisible", "localonly",
    "secretprivate", "cloak",
}
_EMAIL = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
_PHONE = re.compile(r"(?:\+?\d[\d\s\-().]{7,}\d)")
_TW_ID = re.compile(r"\b[A-Z][12]\d{8}\b")


class VisibilityDenied(PermissionError):
    def __init__(self, code: str, message: str) -> None:
        super().__init__(message)
        self.code = code
        self.message = message


class VisibilityPolicy:
    """Fail closed on removed options; derive protected stubs when needed."""

    def __init__(self, environment: Optional[Mapping[str, str]] = None) -> None:
        self.environment = dict(os.environ if environment is None else environment)
        self.validate_environment()

    def validate_environment(self) -> None:
        present = set(REMOVED_ENVIRONMENT_PARAMETERS & set(self.environment))
        for name in self.environment:
            canonical = re.sub(r"[^A-Z0-9]", "", name.upper())
            if name.upper().startswith("MRL") and any(
                token.upper() in canonical for token in _REMOVED_OPTION_TOKENS
            ) and not canonical.endswith(("KEY", "TOKEN", "SECRET", "CREDENTIAL")):
                present.add(name)
        present = sorted(present)
        if present:
            raise VisibilityDenied(
                "REMOVED_PRIVATE_ENVIRONMENT_OPTION",
                "removed hidden/private environment parameter present: " + ", ".join(present),
            )
        requested = self.environment.get("MRL_DATA_VISIBILITY")
        if requested is not None and requested.strip().upper() != WORLD_PUBLIC:
            raise VisibilityDenied(
                "INVALID_ENVIRONMENT_VISIBILITY",
                f"MRL_DATA_VISIBILITY only accepts {WORLD_PUBLIC}",
            )

    @staticmethod
    def _walk(value: Any):
        if isinstance(value, Mapping):
            for key, child in value.items():
                yield str(key).lower(), child
                yield from VisibilityPolicy._walk(child)
        elif isinstance(value, (list, tuple, set)):
            for child in value:
                yield from VisibilityPolicy._walk(child)
        else:
            yield "", value

    def assert_no_private_options(self, record: Mapping[str, Any]) -> None:
        for key, value in self._walk(record):
            canonical_key = re.sub(r"[^a-z0-9]", "", key.lower())
            option_like = key in _REMOVED_RECORD_OPTIONS or any(
                token in canonical_key for token in _REMOVED_OPTION_TOKENS
            )
            protected_content_key = key in _PERSONAL_KEYS or key in _SECRET_KEYS
            if option_like and not protected_content_key:
                raise VisibilityDenied(
                    "REMOVED_PRIVATE_RECORD_OPTION",
                    f"record option '{key}' has been removed from the ASI layer",
                )
            if "visibility" in canonical_key and value is not None:
                requested = str(value).strip().upper()
                if requested != WORLD_PUBLIC:
                    raise VisibilityDenied(
                        "REMOVED_VISIBILITY_VALUE",
                        f"visibility '{value}' is not a user-selectable ASI value",
                    )

    def detect_protected_class(self, record: Mapping[str, Any]) -> Optional[str]:
        explicit = record.get("protected_class")
        if explicit is not None:
            if explicit not in PROTECTED_CLASSES:
                raise VisibilityDenied(
                    "INVALID_PROTECTED_CLASS",
                    f"unknown protected_class: {explicit}",
                )
            return str(explicit)

        if record.get("rights_restricted") is True:
            return "rights_restricted_third_party_material"

        filename = str(record.get("filename", ""))
        mime_type = str(record.get("mime_type", "")).lower()
        if mime_type.startswith("image/") or mime_type.startswith("video/"):
            return "images_and_visual_derivatives"
        if pathlib.Path(filename.lower()).suffix in _IMAGE_EXTENSIONS:
            return "images_and_visual_derivatives"

        flattened_text = []
        for key, value in self._walk(record):
            if key in _SECRET_KEYS:
                return "secrets_and_security_controls"
            if key in _PERSONAL_KEYS:
                return "personal_data"
            if key in {"ciphertext", "encrypted_payload", "opaque_blob"}:
                return "secrets_and_security_controls"
            if isinstance(value, str):
                flattened_text.append(value)

        text = "\n".join(flattened_text)
        if _EMAIL.search(text) or _PHONE.search(text) or _TW_ID.search(text):
            return "personal_data"
        return None

    def resolve(
        self,
        *,
        requested_visibility: Optional[str] = None,
        protected_class: Optional[str] = None,
        review_required: bool = False,
    ) -> str:
        if requested_visibility is not None:
            requested = requested_visibility.strip().upper()
            if requested in FORBIDDEN_VISIBILITY:
                raise VisibilityDenied(
                    "REMOVED_VISIBILITY_VALUE",
                    f"visibility '{requested_visibility}' has been removed",
                )
            if requested != WORLD_PUBLIC:
                raise VisibilityDenied(
                    "INVALID_VISIBILITY_VALUE",
                    f"non-protected data only accepts {WORLD_PUBLIC}",
                )
        if protected_class is not None:
            if protected_class not in PROTECTED_CLASSES:
                raise VisibilityDenied("INVALID_PROTECTED_CLASS", protected_class)
            return PROTECTED_STUB
        if review_required:
            return QUARANTINED
        return WORLD_PUBLIC

    def normalize_record(self, record: Mapping[str, Any]) -> Dict[str, Any]:
        self.assert_no_private_options(record)
        protected_class = self.detect_protected_class(record)
        review_required = record.get("review_required") is True
        visibility = self.resolve(
            requested_visibility=record.get("visibility"),
            protected_class=protected_class,
            review_required=review_required,
        )

        if visibility == WORLD_PUBLIC:
            result = copy.deepcopy(dict(record))
            result["visibility"] = WORLD_PUBLIC
            result.setdefault("origin_signature", ORIGIN_SIGNATURE)
            return result

        object_id = str(record.get("object_id") or "mrl-protected:" + uuid.uuid4().hex)
        stub: Dict[str, Any] = {
            "object_id": object_id,
            "origin_signature": str(record.get("origin_signature") or ORIGIN_SIGNATURE),
            "visibility": visibility,
            "transparency_stub": True,
            "raw_content_included": False,
            "protected_class": protected_class or "pending_review",
            "withholding_reason": str(
                record.get("withholding_reason")
                or protected_class
                or "protection_status_requires_review"
            ),
            "review_state": "pending" if visibility == QUARANTINED else "classified",
        }
        if record.get("content_hash_safe_to_publish") is True:
            raw = json.dumps(record, ensure_ascii=False, sort_keys=True, default=str)
            import hashlib

            stub["content_hash"] = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        else:
            stub["content_hash_withheld"] = True
        return stub
