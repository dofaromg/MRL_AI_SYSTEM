#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Daily, evidence-preserving distillation of popular public GitHub repositories.

External repository content is treated as untrusted reference material. This
module records metadata and README structure only; it never downloads or runs
repository code, and every integration candidate remains pending human review.
"""

from __future__ import annotations

import argparse
import base64
import datetime as dt
import hashlib
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any, Callable
from urllib.parse import urlsplit

ORIGIN_SIGNATURE = "MrLiouWord"
API_ROOT = "https://api.github.com"
MAX_RESPONSE_BYTES = 2 * 1024 * 1024
_REPO_NAME = re.compile(r"^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+$")


def _request_json(url: str, *, token: str = "", timeout_s: int = 20) -> dict[str, Any]:
    parsed = urlsplit(url)
    if parsed.scheme != "https" or parsed.netloc != "api.github.com":
        raise ValueError("Only the HTTPS GitHub API host is allowed")

    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "MRL_AI_SYSTEM-BlackHole-Distiller",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if token:
        headers["Authorization"] = "Bearer " + token
    request = urllib.request.Request(url, headers=headers)
    try:
        opener = urllib.request.build_opener(_NoRedirectHandler)
        with opener.open(request, timeout=timeout_s) as response:
            payload = response.read(MAX_RESPONSE_BYTES + 1)
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"GitHub API returned HTTP {exc.code}") from exc
    if len(payload) > MAX_RESPONSE_BYTES:
        raise ValueError("GitHub API response exceeded the size limit")
    decoded = json.loads(payload.decode("utf-8"))
    if not isinstance(decoded, dict):
        raise ValueError("GitHub API returned an unexpected response")
    return decoded


class _NoRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def _readme_text(readme: dict[str, Any]) -> tuple[str, str]:
    if readme.get("encoding") != "base64" or not isinstance(readme.get("content"), str):
        return "", ""
    try:
        raw = base64.b64decode(readme["content"], validate=True)
        if len(raw) > MAX_RESPONSE_BYTES:
            return "", ""
        text = raw.decode("utf-8", errors="replace")
    except (ValueError, TypeError):
        return "", ""
    return text, hashlib.sha256(raw).hexdigest()


def _headings(text: str, limit: int = 12) -> list[str]:
    headings: list[str] = []
    in_code_fence = False
    for line in text.splitlines():
        if line.lstrip().startswith("```") or line.lstrip().startswith("~~~"):
            in_code_fence = not in_code_fence
            continue
        if in_code_fence:
            continue
        match = re.match(r"^\s{0,3}#{1,6}\s+(.+?)\s*#*\s*$", line)
        if match:
            title = re.sub(r"\s+", " ", match.group(1)).strip()
            if title and title not in headings:
                headings.append(title[:120])
                if len(headings) == limit:
                    break
    return headings


def _lifecycle_alignment(text: str) -> list[str]:
    checks = (
        ("Jump", r"\b(agent|workflow|pipeline|router|routing)\b"),
        ("Collapse", r"\b(compress|compression|serialize|serialization|archive)\b"),
        ("Trace", r"\b(trace|logging|observability|audit)\b"),
        ("Replay", r"\b(replay|restore|recovery|rollback|reproducible)\b"),
    )
    lowered = text.casefold()
    return [stage for stage, pattern in checks if re.search(pattern, lowered)]


def _distill_repository(
    repository: dict[str, Any],
    readme: dict[str, Any] | None,
    readme_error: str = "",
) -> dict[str, Any]:
    full_name = repository.get("full_name")
    if not isinstance(full_name, str) or not _REPO_NAME.fullmatch(full_name):
        raise ValueError("GitHub returned an invalid repository name")

    readme_text, readme_sha256 = _readme_text(readme or {})
    license_info = repository.get("license")
    license_key = license_info.get("spdx_id") if isinstance(license_info, dict) else None
    if not isinstance(license_key, str):
        license_key = None
    description = repository.get("description")
    if not isinstance(description, str):
        description = ""
    topics = repository.get("topics")
    if not isinstance(topics, list):
        topics = []
    topics = [topic[:80] for topic in topics if isinstance(topic, str)][:20]

    return {
        "source": {
            "repository": full_name,
            "url": f"https://github.com/{full_name}",
            "default_branch": str(repository.get("default_branch") or "")[:120],
            "license_spdx": license_key,
            "readme_sha256": readme_sha256 or None,
        },
        "repository_observation": {
            "description": description[:500],
            "language": str(repository.get("language") or "")[:80] or None,
            "topics": topics,
            "stars": int(repository.get("stargazers_count") or 0),
            "created_at": repository.get("created_at"),
            "updated_at": repository.get("updated_at"),
            "readme_headings": _headings(readme_text),
            "mrl_lifecycle_alignment": _lifecycle_alignment(
                f"{description}\n{' '.join(topics)}\n{readme_text}"
            ),
            "readme_error": readme_error[:240] or None,
        },
        "integration_candidate": {
            "status": "PENDING_HUMAN_REVIEW",
            "activation_allowed": False,
            "executable_source_imported": False,
            "requires_license_and_security_review": True,
        },
    }


def daily_distillation(
    *,
    now: dt.datetime | None = None,
    since_days: int = 7,
    limit: int = 20,
    token: str = "",
    fetch_json: Callable[..., dict[str, Any]] = _request_json,
) -> dict[str, Any]:
    if not 1 <= since_days <= 30:
        raise ValueError("since_days must be between 1 and 30")
    if not 1 <= limit <= 30:
        raise ValueError("limit must be between 1 and 30")
    observed_at = now or dt.datetime.now(dt.timezone.utc)
    if observed_at.tzinfo is None:
        observed_at = observed_at.replace(tzinfo=dt.timezone.utc)
    cutoff = (observed_at.astimezone(dt.timezone.utc) - dt.timedelta(days=since_days)).date()
    query = urllib.parse.urlencode(
        {
            "q": f"created:>={cutoff.isoformat()}",
            "sort": "stars",
            "order": "desc",
            "per_page": str(limit),
        }
    )
    search = fetch_json(f"{API_ROOT}/search/repositories?{query}", token=token)
    items = search.get("items")
    if not isinstance(items, list):
        raise ValueError("GitHub repository search response has no items list")

    results = []
    for repository in items[:limit]:
        if not isinstance(repository, dict):
            continue
        full_name = repository.get("full_name")
        if not isinstance(full_name, str) or not _REPO_NAME.fullmatch(full_name):
            continue
        readme: dict[str, Any] | None = None
        readme_error = ""
        try:
            encoded_name = urllib.parse.quote(full_name, safe="/")
            readme = fetch_json(f"{API_ROOT}/repos/{encoded_name}/readme", token=token)
        except Exception as exc:  # One unavailable README must not erase other observations.
            readme_error = f"{type(exc).__name__}: {exc}"
        try:
            results.append(_distill_repository(repository, readme, readme_error))
        except (TypeError, ValueError):
            continue

    return {
        "schema_version": "1.0",
        "module": "MRL_BlackHole_DailyDistiller_v1",
        "origin_signature": ORIGIN_SIGNATURE,
        "record_mode": "additive_only",
        "observed_at": observed_at.astimezone(dt.timezone.utc).isoformat(),
        "search": {"created_since": cutoff.isoformat(), "sort": "stars_desc", "limit": limit},
        "count": len(results),
        "repositories": results,
        "execution_policy": {
            "external_repository_code_executed": False,
            "candidate_activation_requires_human_review": True,
        },
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Distill recent popular public GitHub repositories")
    parser.add_argument("--since-days", type=int, default=7)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--output", type=pathlib.Path, help="Write JSON report to this path")
    parser.add_argument("--timeout", type=int, default=20)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    try:
        report = daily_distillation(
            since_days=args.since_days,
            limit=args.limit,
            token=os.environ.get("GH_TOKEN", os.environ.get("GITHUB_TOKEN", "")),
            fetch_json=lambda url, *, token="": _request_json(
                url, token=token, timeout_s=args.timeout
            ),
        )
        serialized = json.dumps(report, ensure_ascii=False, indent=2) + "\n"
        if args.output:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(serialized, encoding="utf-8")
        else:
            sys.stdout.write(serialized)
    except (OSError, RuntimeError, ValueError, urllib.error.URLError) as exc:
        print(f"distillation failed: {exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
