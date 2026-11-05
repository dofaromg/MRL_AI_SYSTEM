#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""MRL World-Model machine-readable wake loader.

origin_signature: MrLiouWord
record_mode: additive_only

The .yaml inputs in v1 intentionally use JSON syntax, which is valid YAML 1.2,
so the loader has no third-party parser dependency.
"""

from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import pathlib
import sys
import uuid

ORIGIN_SIGNATURE = "MrLiouWord"


def _utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def _load_json_yaml(path: pathlib.Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        obj = json.load(f)
    if not isinstance(obj, dict):
        raise ValueError(f"{path}: expected object")
    return obj


def _sha256(path: pathlib.Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_manifest(repo_root: pathlib.Path, manifest_rel: str, pointer_rel: str) -> dict:
    manifest_path = repo_root / manifest_rel
    pointer_path = repo_root / pointer_rel

    checks = []
    errors = []

    for label, path in (("manifest", manifest_path), ("canonical_pointer", pointer_path)):
        exists = path.is_file()
        checks.append({"check": f"{label}_exists", "ok": exists, "path": str(path)})
        if not exists:
            errors.append(f"missing {label}: {path}")

    if errors:
        return {"checks": checks, "errors": errors, "manifest": None, "pointer": None}

    manifest = _load_json_yaml(manifest_path)
    pointer = _load_json_yaml(pointer_path)

    for label, obj in (("manifest", manifest), ("canonical_pointer", pointer)):
        ok = obj.get("origin_signature") == ORIGIN_SIGNATURE
        checks.append({"check": f"{label}_origin_signature", "ok": ok, "observed": obj.get("origin_signature")})
        if not ok:
            errors.append(f"{label}: origin signature mismatch")

    cp = manifest.get("canonical_pointer")
    cp_ok = cp == pointer_rel
    checks.append({"check": "canonical_pointer_binding", "ok": cp_ok, "observed": cp})
    if not cp_ok:
        errors.append("manifest canonical_pointer does not match loader pointer")

    required_sources = manifest.get("required_sources", [])
    if not isinstance(required_sources, list):
        errors.append("required_sources must be a list")
        required_sources = []

    source_results = []
    for src in required_sources:
        ref = src.get("ref")
        required = bool(src.get("required", False))
        path = repo_root / str(ref)
        exists = path.is_file()
        result = {
            "kind": src.get("kind"),
            "ref": ref,
            "required": required,
            "exists": exists,
            "sha256": _sha256(path) if exists else None,
        }
        source_results.append(result)
        checks.append({"check": "required_source", "ok": exists or not required, **result})
        if required and not exists:
            errors.append(f"missing required source: {ref}")

    wake_sequence = manifest.get("wake_sequence", [])
    sequence_ok = isinstance(wake_sequence, list) and len(wake_sequence) >= 8
    checks.append({"check": "wake_sequence_present", "ok": sequence_ok, "count": len(wake_sequence) if isinstance(wake_sequence, list) else 0})
    if not sequence_ok:
        errors.append("wake_sequence incomplete")

    mode_ok = manifest.get("record_mode") == "additive_only"
    checks.append({"check": "record_mode_additive_only", "ok": mode_ok})
    if not mode_ok:
        errors.append("record_mode must be additive_only")

    return {
        "checks": checks,
        "errors": errors,
        "manifest": manifest,
        "pointer": pointer,
        "sources": source_results,
    }


def write_trace(repo_root: pathlib.Path, trace_rel: str, result: dict) -> dict:
    trace_path = repo_root / trace_rel
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    trace = {
        "trace_id": f"wake-{uuid.uuid4()}",
        "created_at": _utc_now(),
        "origin_signature": ORIGIN_SIGNATURE,
        "event_type": "MRL_WORLD_MODEL_WAKE_VERIFY",
        "status": "PASS" if not result.get("errors") else "FAIL",
        "error_count": len(result.get("errors", [])),
        "errors": result.get("errors", []),
        "checks": result.get("checks", []),
        "canonical": (result.get("pointer") or {}).get("canonical", {}),
        "backfill_target": ((result.get("manifest") or {}).get("backfill") or {}).get("target"),
    }
    with trace_path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(trace, ensure_ascii=False, sort_keys=True) + "\n")
    return trace


def main() -> int:
    parser = argparse.ArgumentParser(description="MRL World-Model wake loader and verifier")
    parser.add_argument("--repo-root", default=str(pathlib.Path(__file__).resolve().parents[1]))
    parser.add_argument("--manifest", default="00_rootlaw/MRL_WAKE_MANIFEST.yaml")
    parser.add_argument("--pointer", default="00_rootlaw/canonical_pointer.yaml")
    parser.add_argument("--trace-out", default="06_trace/traces/wake_trace.jsonl")
    parser.add_argument("--no-write-trace", action="store_true")
    args = parser.parse_args()

    root = pathlib.Path(args.repo_root).resolve()
    result = validate_manifest(root, args.manifest, args.pointer)
    trace = None if args.no_write_trace else write_trace(root, args.trace_out, result)

    output = {
        "status": "PASS" if not result.get("errors") else "FAIL",
        "origin_signature": ORIGIN_SIGNATURE,
        "errors": result.get("errors", []),
        "checks": result.get("checks", []),
        "trace": trace,
    }
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0 if output["status"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
