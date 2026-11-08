"""
test_mrliouword_integration_v1.py — Mrliouword 核心垂直流程整合測試

此測試驗證 runtime → trace → memory → API/CLI 的完整垂直切片：
1. Config 初始化（設定載入、MRLIOUWORD_ 環境變數支援）
2. Trace 發送（TraceEvent → MerkleChain commit）
3. Memory 儲存與恢復（MemoryStore → 寫入鏈 → 讀回）
4. Schema 簽章（embed_signature / verify_signature 往返）
5. Health 探針（HealthProbe.check() 所有子系統通過）
6. CLI 命令（mrliouword version / health / trace emit / memory store）
7. 跨模組整合流程（config → trace → memory → health 完整路徑）

所有測試均為沙盒可重現：使用 tempdir，不依賴外部服務或真實模型。
"""

from __future__ import annotations

import json
import os
import pathlib
import sys
import tempfile
import uuid
from typing import Any, Dict

import pytest

# ── sys.path 設定（使 mrliouword 及依賴模組可匯入） ───────────────────────────
_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _p in [
    str(_REPO_ROOT),
    str(_REPO_ROOT / "09_workflow"),
    str(_REPO_ROOT / "03_memory" / "merkle"),
    str(_REPO_ROOT / "03_memory" / "vector"),
]:
    if _p not in sys.path:
        sys.path.insert(0, _p)


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def tmp_data_dir(tmp_path: pathlib.Path) -> pathlib.Path:
    """提供獨立的臨時資料目錄（每個測試隔離）。"""
    return tmp_path


@pytest.fixture
def tracer(tmp_data_dir: pathlib.Path):
    from mrliouword.trace import Tracer
    return Tracer(data_dir=tmp_data_dir / "trace")


@pytest.fixture
def memory_store(tmp_data_dir: pathlib.Path):
    from mrliouword.memory import MemoryStore
    return MemoryStore(data_dir=tmp_data_dir / "memory")


# ── 1. Schema 模型測試 ────────────────────────────────────────────────────────

class TestSchemas:
    def test_trace_event_fields(self):
        from mrliouword.schemas import TraceEvent, ORIGIN_SIGNATURE, SCHEMA_VERSION
        event = TraceEvent(event_type="test.created", payload={"key": "val"})
        assert event.event_type == "test.created"
        assert event.payload == {"key": "val"}
        assert event.origin_signature == ORIGIN_SIGNATURE
        assert event.schema_version == SCHEMA_VERSION
        assert event.trace_id  # auto-generated UUID
        assert event.timestamp_ms > 0

    def test_trace_event_roundtrip(self):
        from mrliouword.schemas import TraceEvent
        event = TraceEvent(event_type="rt.start", payload={"x": 1})
        d = event.to_dict()
        restored = TraceEvent.from_dict(d)
        assert restored.event_type == event.event_type
        assert restored.trace_id == event.trace_id
        assert restored.payload == event.payload

    def test_memory_entry_fields(self):
        from mrliouword.schemas import MemoryEntry, ORIGIN_SIGNATURE
        entry = MemoryEntry(
            entry_id=str(uuid.uuid4()),
            content={"data": "hello"},
            tags=["L7", "test"],
        )
        assert entry.origin_signature == ORIGIN_SIGNATURE
        d = entry.to_dict()
        assert d["content"] == {"data": "hello"}
        assert "L7" in d["tags"]

    def test_health_status_ok(self):
        from mrliouword.schemas import HealthStatus
        status = HealthStatus(status="ok", version="1.0.0", subsystems={"config": "ok"})
        assert status.ok is True
        d = status.to_dict()
        assert d["status"] == "ok"

    def test_error_response_fields(self):
        from mrliouword.schemas import ErrorResponse
        err = ErrorResponse(error_code="E001", message="test error")
        d = err.to_dict()
        assert d["error_code"] == "E001"
        assert d["message"] == "test error"
        assert d["request_id"]  # auto-generated

    def test_embed_verify_signature_roundtrip(self):
        from mrliouword.schemas import embed_signature, verify_signature
        payload = {"event_type": "test", "value": 42}
        signed = embed_signature(payload)
        assert signed["_signature"] == "MrLiouWord"
        assert len(signed["_sig_hash"]) == 64
        assert verify_signature(signed) is True

    def test_verify_signature_tamper_detected(self):
        from mrliouword.schemas import embed_signature, verify_signature
        payload = {"event_type": "test", "value": 42}
        signed = embed_signature(payload)
        tampered = {**signed, "value": 99}
        assert verify_signature(tampered) is False

    def test_embed_signature_compat_with_mrl_utils(self):
        """Mrliouword embed_signature 與 MRL_utils.py 位元相容。"""
        from mrliouword.schemas import embed_signature as mw_embed
        from mrliouword.schemas import verify_signature as mw_verify
        sys.path.insert(0, str(_REPO_ROOT / "09_workflow"))
        from MRL_utils import embed_signature as mrl_embed
        from MRL_utils import verify_signature as mrl_verify

        payload = {"type": "compat_test", "n": 123}
        mrl_signed = mrl_embed(payload)
        mw_signed = mw_embed(payload)
        # 同一輸入 → 相同雜湊
        assert mrl_signed["_sig_hash"] == mw_signed["_sig_hash"]
        # 交叉驗證
        assert mrl_verify(mw_signed) is True
        assert mw_verify(mrl_signed) is True


# ── 2. Config 測試 ────────────────────────────────────────────────────────────

class TestConfig:
    def test_default_values(self):
        from mrliouword.config import MrliouwordConfig
        cfg = MrliouwordConfig()
        assert cfg.product_name == "Mrliouword"
        assert cfg.origin_signature == "MrLiouWord"

    def test_mrliouword_env_prefix_overrides(self, monkeypatch):
        from mrliouword.config import MrliouwordConfig
        monkeypatch.setenv("MRLIOUWORD_SYSTEM_DEBUG", "true")
        cfg = MrliouwordConfig()
        val = cfg.get("system.debug")
        assert val is True

    def test_mrl_env_prefix_still_works(self, monkeypatch):
        """MRL_ 舊前綴向後相容。"""
        from mrliouword.config import MrliouwordConfig
        monkeypatch.setenv("MRL_SYSTEM_DEBUG", "true")
        cfg = MrliouwordConfig()
        val = cfg.get("system.debug")
        assert val is True

    def test_mrliouword_prefix_beats_mrl(self, monkeypatch):
        """MRLIOUWORD_ 優先於 MRL_。"""
        from mrliouword.config import MrliouwordConfig
        monkeypatch.setenv("MRLIOUWORD_SYSTEM_DEBUG", "true")
        monkeypatch.setenv("MRL_SYSTEM_DEBUG", "false")
        cfg = MrliouwordConfig()
        assert cfg.get("system.debug") is True

    def test_get_with_default(self):
        from mrliouword.config import MrliouwordConfig
        cfg = MrliouwordConfig()
        val = cfg.get("nonexistent.key", default="fallback")
        assert val == "fallback"


# ── 3. Trace 測試 ─────────────────────────────────────────────────────────────

class TestTracer:
    def test_emit_returns_entry(self, tracer):
        from mrliouword.schemas import TraceEvent
        event = TraceEvent(event_type="runtime.start", payload={"module": "flowcore"})
        result = tracer.emit(event)
        assert result["event_type"] == "runtime.start"
        assert result["trace_id"] == event.trace_id
        assert result["merkle"]
        assert result["entry_id"]

    def test_chain_verify_after_emit(self, tracer):
        from mrliouword.schemas import TraceEvent
        for i in range(3):
            tracer.emit(TraceEvent(event_type=f"step.{i}", payload={"i": i}))
        assert tracer.verify() is True

    def test_recent_returns_latest_first(self, tracer):
        from mrliouword.schemas import TraceEvent
        events = [TraceEvent(event_type=f"evt.{i}", payload={}) for i in range(5)]
        for e in events:
            tracer.emit(e)
        recent = tracer.recent(limit=3)
        assert len(recent) == 3
        # 最新在前
        assert recent[0]["event_type"] == "evt.4"

    def test_emit_with_correlation_id(self, tracer):
        from mrliouword.schemas import TraceEvent
        corr_id = str(uuid.uuid4())
        event = TraceEvent(event_type="corr.test", payload={})
        result = tracer.emit(event, correlation_id=corr_id)
        assert result["entry_id"]

    def test_head_advances_on_commit(self, tracer):
        from mrliouword.schemas import TraceEvent
        head0 = tracer.head
        tracer.emit(TraceEvent(event_type="head.test", payload={}))
        assert tracer.head != head0


# ── 4. Memory 測試 ────────────────────────────────────────────────────────────

class TestMemoryStore:
    def test_store_and_restore(self, memory_store):
        content = {"type": "particle", "data": "mrliouword-test"}
        eid = memory_store.store(content)
        assert eid
        restored = memory_store.restore(eid)
        assert restored is not None
        assert restored.get("content", {}) == content or restored.get("data") == "mrliouword-test"

    def test_verify_after_store(self, memory_store):
        memory_store.store({"key": "val"})
        assert memory_store.verify() is True

    def test_size_increments(self, memory_store):
        assert memory_store.size == 0
        memory_store.store({"a": 1})
        assert memory_store.size == 1
        memory_store.store({"b": 2})
        assert memory_store.size == 2

    def test_restore_nonexistent_returns_none(self, memory_store):
        result = memory_store.restore("nonexistent-id-xyz")
        assert result is None

    def test_list_entries(self, memory_store):
        for i in range(3):
            memory_store.store({"i": i}, entry_type="fact")
        entries = memory_store.list_entries()
        assert len(entries) == 3
        assert all(e["entry_type"] == "fact" for e in entries)

    def test_signed_content_verifiable(self, memory_store):
        from mrliouword.schemas import verify_signature
        eid = memory_store.store({"signed": True})
        raw_entries = memory_store._chain.read_all()
        for raw in raw_entries:
            if raw.get("entry_id") == eid:
                payload = raw.get("payload", {})
                assert verify_signature(payload) is True
                break


# ── 5. API Health 測試 ────────────────────────────────────────────────────────

class TestHealthProbe:
    def test_check_returns_ok_status(self):
        from mrliouword.api import HealthProbe
        probe = HealthProbe()
        status = probe.check()
        assert status.status == "ok"
        assert status.product == "Mrliouword"

    def test_all_subsystems_pass(self):
        from mrliouword.api import HealthProbe
        probe = HealthProbe()
        status = probe.check()
        for name, val in status.subsystems.items():
            assert val == "ok", f"Subsystem {name!r} failed: {val}"

    def test_readiness_is_true(self):
        from mrliouword.api import HealthProbe
        probe = HealthProbe()
        assert probe.readiness() is True

    def test_build_health_response_format(self):
        from mrliouword.api import build_health_response
        resp = build_health_response()
        assert "status" in resp
        assert "product" in resp
        assert resp["product"] == "Mrliouword"
        assert "subsystems" in resp
        assert "schema_version" in resp


# ── 6. CLI 測試 ───────────────────────────────────────────────────────────────

class TestCLI:
    def test_version_command(self, capsys):
        from mrliouword.cli import main
        rc = main(["version"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["product"] == "Mrliouword"
        assert data["version"] == "1.0.0"

    def test_health_command(self, capsys):
        from mrliouword.cli import main
        rc = main(["health"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["status"] == "ok"

    def test_trace_emit_command(self, capsys, tmp_path, monkeypatch):
        monkeypatch.setenv("MRL_RUNTIME_MODE", "test")
        from mrliouword.cli import main
        rc = main(["trace", "emit", "cli.test", "--payload", '{"from": "cli"}'])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["event_type"] == "cli.test"

    def test_memory_store_command(self, capsys, tmp_path, monkeypatch):
        monkeypatch.setenv("MRL_RUNTIME_MODE", "test")
        from mrliouword.cli import main
        rc = main(["memory", "store", '{"hello": "mrliouword"}'])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert data["status"] == "stored"
        assert data["entry_id"]

    def test_config_show_command(self, capsys):
        from mrliouword.cli import main
        rc = main(["config", "show"])
        assert rc == 0
        out = capsys.readouterr().out
        data = json.loads(out)
        assert "system" in data


# ── 7. 垂直整合流程測試 ───────────────────────────────────────────────────────

class TestVerticalSlice:
    """
    驗證 runtime → trace → memory → health 完整垂直流程。

    此為最重要的整合測試：確保各層模組可以協作無誤。
    """

    def test_full_vertical_slice(self, tmp_data_dir: pathlib.Path):
        """config → trace → memory → health 完整路徑。"""
        from mrliouword.config import MrliouwordConfig
        from mrliouword.schemas import TraceEvent, embed_signature, verify_signature
        from mrliouword.trace import Tracer
        from mrliouword.memory import MemoryStore
        from mrliouword.api import HealthProbe

        # Step 1: 初始化設定
        cfg = MrliouwordConfig()
        assert cfg.product_name == "Mrliouword"
        correlation_id = str(uuid.uuid4())

        # Step 2: 發送 runtime 啟動追蹤事件
        tracer = Tracer(data_dir=tmp_data_dir / "trace")
        start_event = TraceEvent(
            event_type="runtime.start",
            payload={"module": "flowcore", "config_version": cfg.version},
            correlation_id=correlation_id,
        )
        trace_result = tracer.emit(start_event, correlation_id=correlation_id)
        assert trace_result["event_type"] == "runtime.start"
        assert tracer.verify() is True

        # Step 3: 將 runtime 事件寫入記憶層
        memory = MemoryStore(data_dir=tmp_data_dir / "memory")
        mem_content = {
            "type": "runtime_event",
            "trace_id": trace_result["trace_id"],
            "merkle": trace_result["merkle"],
            "event_type": "runtime.start",
            "correlation_id": correlation_id,
        }
        entry_id = memory.store(
            mem_content,
            entry_type="runtime_event",
            tags=["runtime", "L7"],
            layer="L7",
        )
        assert memory.verify() is True

        # Step 4: 驗證記憶可恢復
        restored = memory.restore(entry_id)
        assert restored is not None
        # 內容有 LAW-0 簽章
        assert verify_signature(restored) is True

        # Step 5: 發送追蹤記憶寫入事件
        mem_event = TraceEvent(
            event_type="memory.stored",
            payload={"entry_id": entry_id, "entry_type": "runtime_event"},
            correlation_id=correlation_id,
        )
        tracer.emit(mem_event)

        # Step 6: Health check
        probe = HealthProbe()
        health = probe.check()
        assert health.ok is True
        assert health.subsystems["memory_chain"] == "ok"
        assert health.subsystems["schemas"] == "ok"

        # Step 7: 驗證 trace 鏈記錄了兩個事件
        recent = tracer.recent(10)
        event_types = [r["event_type"] for r in recent]
        assert "runtime.start" in event_types
        assert "memory.stored" in event_types

    def test_schema_version_present_in_all_models(self):
        """所有核心資料模型都有 schema_version 欄位。"""
        from mrliouword.schemas import (
            TraceEvent, MemoryEntry, HealthStatus, ErrorResponse, SCHEMA_VERSION
        )
        import uuid
        models = [
            TraceEvent(event_type="t", payload={}).to_dict(),
            MemoryEntry(entry_id=str(uuid.uuid4()), content={}).to_dict(),
            HealthStatus(status="ok", version="1.0.0").to_dict(),
            ErrorResponse(error_code="E001", message="test").to_dict(),
        ]
        for model in models:
            assert "schema_version" in model
            assert model["schema_version"] == SCHEMA_VERSION

    def test_origin_signature_in_all_models(self):
        """所有核心資料模型都攜帶 origin_signature。"""
        from mrliouword.schemas import (
            TraceEvent, MemoryEntry, HealthStatus, ORIGIN_SIGNATURE
        )
        import uuid
        te = TraceEvent(event_type="t", payload={}).to_dict()
        me = MemoryEntry(entry_id=str(uuid.uuid4()), content={}).to_dict()
        hs = HealthStatus(status="ok", version="1.0.0").to_dict()
        for model in [te, me, hs]:
            assert model["origin_signature"] == ORIGIN_SIGNATURE
