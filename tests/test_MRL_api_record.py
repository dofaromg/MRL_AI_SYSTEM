"""test_MRL_api_record.py — MRL API 紀錄模組 (MRL_ApiRecord)
origin_signature: MrLiouWord

驗證：帳本 record / tail / summary / clear，欄位與 origin_signature，
以及帳本路徑可由 MRL_API_RECORD_PATH 覆寫（測試隔離）。
"""
from __future__ import annotations

import importlib
import pathlib
import sys

REPO = pathlib.Path(__file__).resolve().parent.parent
if str(REPO) not in sys.path:
    sys.path.insert(0, str(REPO))


def _fresh(tmp_path, monkeypatch):
    """以隔離帳本路徑載入模組。"""
    ledger = tmp_path / "records.jsonl"
    monkeypatch.setenv("MRL_API_RECORD_PATH", str(ledger))
    from mrliouword import api_record
    importlib.reload(api_record)
    api_record.clear()
    return api_record, ledger


def test_record_writes_entry_with_signature(tmp_path, monkeypatch):
    api_record, ledger = _fresh(tmp_path, monkeypatch)
    e = api_record.record(method="GET", path="/health", status=200, latency_ms=1.23)
    assert e["origin_signature"] == "MrLiouWord"
    assert e["product"] == "MrliouAI"
    assert e["mrl_kind"] == "MRL_ApiRecord"
    assert e["method"] == "GET" and e["path"] == "/health" and e["status"] == 200
    assert e["trace_id"].startswith("MRL-API-")
    assert ledger.exists() and ledger.read_text(encoding="utf-8").strip()


def test_trace_id_unique(tmp_path, monkeypatch):
    api_record, _ = _fresh(tmp_path, monkeypatch)
    ids = {api_record.record(method="GET", path="/x", status=200)["trace_id"] for _ in range(50)}
    assert len(ids) == 50, "trace_id 必須唯一（防碰撞）"


def test_tail_returns_recent(tmp_path, monkeypatch):
    api_record, _ = _fresh(tmp_path, monkeypatch)
    for i in range(10):
        api_record.record(method="GET", path=f"/p{i}", status=200)
    last3 = api_record.tail(3)
    assert len(last3) == 3
    assert [r["path"] for r in last3] == ["/p7", "/p8", "/p9"]


def test_summary_aggregates(tmp_path, monkeypatch):
    api_record, _ = _fresh(tmp_path, monkeypatch)
    api_record.record(method="GET", path="/health", status=200)
    api_record.record(method="GET", path="/health", status=200)
    api_record.record(method="POST", path="/api/chat", status=503)
    s = api_record.summary()
    assert s["total"] == 3
    assert s["by_path"]["/health"] == 2
    assert s["by_status"]["200"] == 2 and s["by_status"]["503"] == 1
    assert s["by_method"]["GET"] == 2 and s["by_method"]["POST"] == 1
    assert s["origin_signature"] == "MrLiouWord"


def test_telemetry_kind_recorded(tmp_path, monkeypatch):
    api_record, _ = _fresh(tmp_path, monkeypatch)
    api_record.record(method="POST", path="/api/mrl/telemetry/logs", status=200,
                      kind="telemetry", meta={"counts": {"consoleLogs": 2}})
    rec = api_record.tail(1)[0]
    assert rec["kind"] == "telemetry"
    assert rec["meta"]["counts"]["consoleLogs"] == 2


def test_clear_empties_ledger(tmp_path, monkeypatch):
    api_record, ledger = _fresh(tmp_path, monkeypatch)
    api_record.record(method="GET", path="/health", status=200)
    api_record.clear()
    assert not ledger.exists()
    assert api_record.tail(10) == [] and api_record.summary()["total"] == 0
