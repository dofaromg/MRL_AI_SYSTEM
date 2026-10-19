from __future__ import annotations

import base64
import datetime as dt
import hashlib
import urllib.parse

import pytest

from MRL_BlackHole_DailyDistiller_v1 import daily_distillation


def test_daily_distillation_preserves_provenance_without_activating_code():
    readme_bytes = b"# Project\n\n## Runtime\n\nSupports trace and replay."
    calls = []

    def fetch_json(url, *, token=""):
        calls.append((url, token))
        if "/search/repositories?" in url:
            return {
                "items": [
                    {
                        "full_name": "owner/project",
                        "description": "A replay tool",
                        "language": "Python",
                        "topics": ["workflow"],
                        "stargazers_count": 42,
                        "created_at": "2026-10-18T00:00:00Z",
                        "updated_at": "2026-10-19T00:00:00Z",
                        "default_branch": "main",
                        "license": {"spdx_id": "MIT"},
                    }
                ]
            }
        return {
            "encoding": "base64",
            "content": base64.b64encode(readme_bytes).decode("ascii"),
        }

    report = daily_distillation(
        now=dt.datetime(2026, 10, 19, tzinfo=dt.timezone.utc),
        since_days=7,
        limit=5,
        token="test-token",
        fetch_json=fetch_json,
    )

    entry = report["repositories"][0]
    assert report["origin_signature"] == "MrLiouWord"
    assert report["search"]["created_since"] == "2026-10-12"
    assert urllib.parse.urlsplit(calls[0][0]).hostname == "api.github.com"
    assert all(token == "test-token" for _, token in calls)
    assert entry["source"]["readme_sha256"] == hashlib.sha256(readme_bytes).hexdigest()
    assert entry["source"]["license_spdx"] == "MIT"
    assert entry["repository_observation"]["readme_headings"] == ["Project", "Runtime"]
    assert entry["repository_observation"]["mrl_lifecycle_alignment"] == ["Jump", "Trace", "Replay"]
    assert entry["integration_candidate"]["status"] == "PENDING_HUMAN_REVIEW"
    assert entry["integration_candidate"]["activation_allowed"] is False
    assert report["execution_policy"]["external_repository_code_executed"] is False


def test_readme_failure_keeps_repository_observation():
    def fetch_json(url, *, token=""):
        if "/search/repositories?" in url:
            return {"items": [{"full_name": "owner/project", "stargazers_count": 3}]}
        raise RuntimeError("README unavailable")

    report = daily_distillation(fetch_json=fetch_json)

    assert report["count"] == 1
    assert "README unavailable" in report["repositories"][0]["repository_observation"]["readme_error"]
    assert report["repositories"][0]["source"]["readme_sha256"] is None


@pytest.mark.parametrize(
    ("since_days", "limit"),
    [(0, 1), (31, 1), (1, 0), (1, 31)],
)
def test_rejects_unbounded_search_parameters(since_days, limit):
    with pytest.raises(ValueError):
        daily_distillation(since_days=since_days, limit=limit)


def test_rejects_invalid_repository_names():
    report = daily_distillation(fetch_json=lambda *_args, **_kwargs: {"items": [{"full_name": "../bad"}]})
    assert report["count"] == 0
