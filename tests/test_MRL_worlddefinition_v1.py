"""test_MRL_worlddefinition_v1.py (origin: MrLiouWord)

World Definition Layer（世界定義層）驗收測試。
驗證 11 個世界基本原語：
  Space, Time, Entity, Identity, State, Relation,
  Event, Rule, Memory, Evolution, Observation
以及 SQL schema 建表、origin_signature、additive 主權。
"""
from __future__ import annotations

import os
import pathlib
import sqlite3
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_WorldDefinition_v1 import WorldDefinition

_REPO = pathlib.Path(__file__).resolve().parent.parent
_SQL = (_REPO / "MRL_BaseWorld_DB_v1" /
        "MRL_BaseWorld_DB_v1_Schema" / "MRL_WorldDefinition_v1.sql")


# ─── Fixtures ─────────────────────────────────────────────────────────────────

@pytest.fixture
def wd() -> WorldDefinition:
    return WorldDefinition()


# ─── origin_signature ─────────────────────────────────────────────────────────

def test_origin_signature(wd: WorldDefinition) -> None:
    assert wd.origin_signature == "MrLiouWord"


# ─── 1. Space ─────────────────────────────────────────────────────────────────

def test_register_space(wd: WorldDefinition) -> None:
    r = wd.register_space("FlowSpace", {"dimension": 3})
    assert r["kind"] == "Space"
    assert r["name"] == "FlowSpace"
    assert r["data"]["dimension"] == 3
    assert "hash" in r


def test_list_spaces(wd: WorldDefinition) -> None:
    wd.register_space("Alpha")
    wd.register_space("Beta")
    assert wd.list_spaces() == ["Alpha", "Beta"]


def test_get_space_none(wd: WorldDefinition) -> None:
    assert wd.get_space("nonexistent") is None


# ─── 2. Time ──────────────────────────────────────────────────────────────────

def test_register_time(wd: WorldDefinition) -> None:
    r = wd.register_time("T0", ts_ms=1_000_000)
    assert r["kind"] == "Time"
    assert r["data"]["ts_ms"] == 1_000_000


def test_register_time_default_ts(wd: WorldDefinition) -> None:
    r = wd.register_time("T_now")
    assert r["data"]["ts_ms"] > 0


# ─── 3. Entity ────────────────────────────────────────────────────────────────

def test_register_entity(wd: WorldDefinition) -> None:
    wd.register_space("S1")
    r = wd.register_entity("FlowSeed", space_ref="S1", attrs={"role": "seed"})
    assert r["kind"] == "Entity"
    assert r["data"]["space_ref"] == "S1"
    assert r["data"]["role"] == "seed"


def test_list_entities(wd: WorldDefinition) -> None:
    wd.register_entity("E1")
    wd.register_entity("E2")
    assert "E1" in wd.list_entities()
    assert "E2" in wd.list_entities()


# ─── 4. Identity ──────────────────────────────────────────────────────────────

def test_register_identity(wd: WorldDefinition) -> None:
    r = wd.register_identity("FlowSeed", owner="MrLiou")
    assert r["kind"] == "Identity"
    assert r["data"]["owner"] == "MrLiou"
    assert r["data"]["signature"] == "MrLiouWord"


def test_register_identity_custom_signature(wd: WorldDefinition) -> None:
    r = wd.register_identity("E", owner="X", signature="CustomSig")
    assert r["data"]["signature"] == "CustomSig"


def test_get_identity_none(wd: WorldDefinition) -> None:
    assert wd.get_identity("nobody") is None


# ─── 5. State ─────────────────────────────────────────────────────────────────

def test_set_state(wd: WorldDefinition) -> None:
    r = wd.set_state("FlowSeed", "active", True)
    assert r["kind"] == "State"
    assert r["entity_ref"] == "FlowSeed"
    assert r["key"] == "active"
    assert r["value"] is True


def test_get_state(wd: WorldDefinition) -> None:
    wd.set_state("E", "color", "blue")
    wd.set_state("E", "speed", 42)
    s = wd.get_state("E")
    assert s["color"] == "blue"
    assert s["speed"] == 42


def test_get_state_empty(wd: WorldDefinition) -> None:
    assert wd.get_state("unknown") == {}


# ─── 6. Relation ──────────────────────────────────────────────────────────────

def test_register_relation(wd: WorldDefinition) -> None:
    r = wd.register_relation("A", "connects", "B")
    assert r["kind"] == "Relation"
    assert r["data"]["from_entity"] == "A"
    assert r["data"]["rel_type"] == "connects"
    assert r["data"]["to_entity"] == "B"


def test_query_relations_from(wd: WorldDefinition) -> None:
    wd.register_relation("X", "uses", "Y")
    wd.register_relation("Z", "uses", "Y")
    result = wd.query_relations(from_entity="X")
    assert len(result) == 1
    assert result[0]["data"]["from_entity"] == "X"


def test_query_relations_to(wd: WorldDefinition) -> None:
    wd.register_relation("A", "links", "C")
    wd.register_relation("B", "links", "C")
    result = wd.query_relations(to_entity="C")
    assert len(result) == 2


# ─── 7. Event ─────────────────────────────────────────────────────────────────

def test_emit_event(wd: WorldDefinition) -> None:
    r = wd.emit_event("FlowSeed", "BORN", {"origin": "MrLiouWord"})
    assert r["kind"] == "Event"
    assert r["data"]["event_type"] == "BORN"
    assert r["data"]["payload"]["origin"] == "MrLiouWord"


def test_query_events_by_entity(wd: WorldDefinition) -> None:
    wd.emit_event("E1", "START")
    wd.emit_event("E2", "START")
    wd.emit_event("E1", "STOP")
    result = wd.query_events(entity_ref="E1")
    assert len(result) == 2


def test_query_events_by_type(wd: WorldDefinition) -> None:
    wd.emit_event("A", "TICK")
    wd.emit_event("B", "TICK")
    wd.emit_event("C", "TOCK")
    result = wd.query_events(event_type="TICK")
    assert len(result) == 2


# ─── 8. Rule ──────────────────────────────────────────────────────────────────

def test_declare_rule(wd: WorldDefinition) -> None:
    r = wd.declare_rule("NoDelete", "always", "preserve", priority=100)
    assert r["kind"] == "Rule"
    assert r["data"]["condition"] == "always"
    assert r["data"]["priority"] == 100


def test_list_rules_sorted_by_priority(wd: WorldDefinition) -> None:
    wd.declare_rule("R_low", "x", "y", priority=1)
    wd.declare_rule("R_high", "x", "y", priority=99)
    wd.declare_rule("R_mid", "x", "y", priority=50)
    rules = wd.list_rules()
    priorities = [r["data"]["priority"] for r in rules]
    assert priorities == sorted(priorities, reverse=True)


def test_list_rules_min_priority_filter(wd: WorldDefinition) -> None:
    wd.declare_rule("RL", "x", "y", priority=5)
    wd.declare_rule("RH", "x", "y", priority=50)
    assert len(wd.list_rules(min_priority=10)) == 1


def test_get_rule_none(wd: WorldDefinition) -> None:
    assert wd.get_rule("nonexistent") is None


# ─── 9. Memory ────────────────────────────────────────────────────────────────

def test_record_memory(wd: WorldDefinition) -> None:
    r = wd.record_memory("FlowSeed", {"active": True})
    assert r["kind"] == "Memory"
    assert r["data"]["entity_ref"] == "FlowSeed"
    assert r["data"]["snapshot"]["active"] is True


def test_recall_memories(wd: WorldDefinition) -> None:
    wd.record_memory("E", {"v": 1})
    wd.record_memory("E", {"v": 2})
    wd.record_memory("other", {"v": 3})
    mems = wd.recall_memories("E")
    assert len(mems) == 2


# ─── 10. Evolution ────────────────────────────────────────────────────────────

def test_record_evolution(wd: WorldDefinition) -> None:
    r = wd.record_evolution("FlowSeed", {"v": 1}, {"v": 2}, description="increment")
    assert r["kind"] == "Evolution"
    assert r["data"]["entity_ref"] == "FlowSeed"
    assert r["data"]["description"] == "increment"
    assert "delta_hash" in r["data"]


def test_query_evolutions(wd: WorldDefinition) -> None:
    wd.record_evolution("E1", {}, {"x": 1})
    wd.record_evolution("E2", {}, {"x": 1})
    wd.record_evolution("E1", {"x": 1}, {"x": 2})
    assert len(wd.query_evolutions("E1")) == 2
    assert len(wd.query_evolutions("E2")) == 1


# ─── 11. Observation ──────────────────────────────────────────────────────────

def test_observe(wd: WorldDefinition) -> None:
    r = wd.observe("Sensor", "FlowSeed", "temperature", 37.0)
    assert r["kind"] == "Observation"
    assert r["data"]["observer"] == "Sensor"
    assert r["data"]["value"] == 37.0


def test_query_observations_by_observer(wd: WorldDefinition) -> None:
    wd.observe("ObsA", "T1", "k", 1)
    wd.observe("ObsA", "T2", "k", 2)
    wd.observe("ObsB", "T1", "k", 3)
    result = wd.query_observations(observer="ObsA")
    assert len(result) == 2


def test_query_observations_by_target(wd: WorldDefinition) -> None:
    wd.observe("O1", "Entity_X", "speed", 10)
    wd.observe("O2", "Entity_X", "color", "red")
    result = wd.query_observations(target_ref="Entity_X")
    assert len(result) == 2


# ─── Snapshot ─────────────────────────────────────────────────────────────────

def test_snapshot_structure(wd: WorldDefinition) -> None:
    wd.register_space("S")
    wd.register_entity("E")
    snap = wd.snapshot()
    assert snap["origin_signature"] == "MrLiouWord"
    assert snap["layer"] == "WorldDefinition"
    assert "primitives" in snap
    for primitive in ("Space", "Time", "Entity", "Identity", "State",
                      "Relation", "Event", "Rule", "Memory",
                      "Evolution", "Observation"):
        assert primitive in snap["primitives"], f"Missing primitive: {primitive}"
    assert "hash" in snap


def test_snapshot_counts(wd: WorldDefinition) -> None:
    wd.register_space("S1")
    wd.register_space("S2")
    wd.register_entity("E1")
    wd.emit_event("E1", "X")
    wd.emit_event("E1", "Y")
    snap = wd.snapshot()
    assert snap["primitives"]["Space"]["count"] == 2
    assert snap["primitives"]["Entity"]["count"] == 1
    assert snap["primitives"]["Event"]["count"] == 2


# ─── SQL Schema ───────────────────────────────────────────────────────────────

@pytest.mark.skipif(not _SQL.exists(), reason="SQL schema absent")
def test_worlddef_schema_creates_11_tables() -> None:
    """World Definition SQL schema 應建出 11 張表。"""
    con = sqlite3.connect(":memory:")
    con.executescript(_SQL.read_text(encoding="utf-8"))
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert len(tables) == 11


@pytest.mark.skipif(not _SQL.exists(), reason="SQL schema absent")
def test_worlddef_tables_are_mrl_named() -> None:
    con = sqlite3.connect(":memory:")
    con.executescript(_SQL.read_text(encoding="utf-8"))
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert all(t.startswith("MRL_WorldDef_") for t in tables)


@pytest.mark.skipif(not _SQL.exists(), reason="SQL schema absent")
def test_worlddef_all_11_primitives_present() -> None:
    expected = {
        "MRL_WorldDef_Space", "MRL_WorldDef_Time", "MRL_WorldDef_Entity",
        "MRL_WorldDef_Identity", "MRL_WorldDef_State", "MRL_WorldDef_Relation",
        "MRL_WorldDef_Event", "MRL_WorldDef_Rule", "MRL_WorldDef_Memory",
        "MRL_WorldDef_Evolution", "MRL_WorldDef_Observation",
    }
    con = sqlite3.connect(":memory:")
    con.executescript(_SQL.read_text(encoding="utf-8"))
    tables = {r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
    assert expected == tables


@pytest.mark.skipif(not _SQL.exists(), reason="SQL schema absent")
def test_worlddef_origin_signature_default() -> None:
    """每張表的 origin_signature 預設值應為 'MrLiouWord'。"""
    con = sqlite3.connect(":memory:")
    con.executescript(_SQL.read_text(encoding="utf-8"))
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    for table in tables:
        cols = {c[1]: c[4] for c in con.execute(
            f"PRAGMA table_info({table})").fetchall()}
        if "origin_signature" in cols:
            assert cols["origin_signature"] == "'MrLiouWord'", (
                f"{table}.origin_signature default should be 'MrLiouWord'"
            )


@pytest.mark.skipif(not _SQL.exists(), reason="SQL schema absent")
def test_worlddef_original_27_tables_intact() -> None:
    """原有 27 張 BaseWorld 表不受 WorldDef 擴充影響（各自獨立載入）。"""
    base_sql = _SQL.parent / "MRL_BaseWorld_DB_v1.sql"
    if not base_sql.exists():
        pytest.skip("base schema absent")
    con = sqlite3.connect(":memory:")
    con.executescript(base_sql.read_text(encoding="utf-8"))
    tables = [r[0] for r in con.execute(
        "SELECT name FROM sqlite_master WHERE type='table'").fetchall()]
    assert len(tables) == 27
