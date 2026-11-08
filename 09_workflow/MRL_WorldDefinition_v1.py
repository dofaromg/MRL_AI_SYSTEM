#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_WorldDefinition_v1.py — 世界定義層（World Definition Layer）
origin_signature: MrLiouWord
layer: L∞ WORLD DEFINITION

本模組實作「世界定義」的 11 個基本原語，作為世界模型（World Model）的最高定義層。
這些原語描述世界本身，而不是部署架構：

  World Definition
  │
  ├── Space（空間）    — 世界中的區域或領域
  ├── Time（時間）     — 時序標記或時間區間
  ├── Entity（實體）   — 存在於世界中的具體事物
  ├── Identity（身份） — 實體的唯一識別
  ├── State（狀態）    — 實體或系統的當前狀況
  ├── Relation（關係） — 兩個實體之間的關聯
  ├── Event（事件）    — 在特定時間點發生的事
  ├── Rule（規則）     — 約束或支配行為的法則
  ├── Memory（記憶）   — 過去狀態或事件的儲存記錄
  ├── Evolution（演化）— 隨時間的變化或轉換
  └── Observation（觀測）— 感知或測量的行為

設計原則：
  - 純 stdlib、零外部套件
  - Additive-only：只增加，不刪除
  - 所有操作均產生可追蹤記錄
  - origin_signature = MrLiouWord（全模組主權）

Usage:
    from MRL_WorldDefinition_v1 import WorldDefinition

    wd = WorldDefinition()
    wd.register_space("FlowSpace", {"dimension": 3, "type": "virtual"})
    wd.register_entity("FlowSeed", space_ref="FlowSpace", attrs={"role": "seed"})
    wd.emit_event("FlowSeed", "BORN", {"origin": "MrLiouWord"})
    snap = wd.snapshot()
"""

from __future__ import annotations

import hashlib
import json
import time
from typing import Any, Dict, List, Optional

from MRL_utils import ORIGIN_SIGNATURE


# ─── helpers ──────────────────────────────────────────────────────────────────

def _now_ms() -> int:
    return int(time.time() * 1000)


def _sha256(obj: Any) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _entry(kind: str, name: str, data: Dict[str, Any]) -> Dict[str, Any]:
    ts = _now_ms()
    payload = {"kind": kind, "name": name, "data": data,
               "created_at_ms": ts, "updated_at_ms": ts}
    payload["hash"] = _sha256(payload)
    return payload


# ─── WorldDefinition ──────────────────────────────────────────────────────────

class WorldDefinition:
    """
    世界定義層（World Definition Layer）。
    管理 11 個世界基本原語：Space, Time, Entity, Identity,
    State, Relation, Event, Rule, Memory, Evolution, Observation。
    所有操作均為 additive-only；無刪除介面。
    """

    def __init__(self) -> None:
        self.origin_signature: str = ORIGIN_SIGNATURE

        # --- 11 primitives -------------------------------------------------
        self._spaces:       Dict[str, Dict[str, Any]] = {}
        self._times:        Dict[str, Dict[str, Any]] = {}
        self._entities:     Dict[str, Dict[str, Any]] = {}
        self._identities:   Dict[str, Dict[str, Any]] = {}
        self._states:       Dict[str, Dict[str, Any]] = {}  # entity_ref -> {key: value}
        self._relations:    List[Dict[str, Any]] = []
        self._events:       List[Dict[str, Any]] = []
        self._rules:        Dict[str, Dict[str, Any]] = {}
        self._memories:     List[Dict[str, Any]] = []
        self._evolutions:   List[Dict[str, Any]] = []
        self._observations: List[Dict[str, Any]] = []

    # ── 1. Space（空間）─────────────────────────────────────────────────────

    def register_space(
        self,
        name: str,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """定義一個空間（Space）。"""
        entry = _entry("Space", name, attrs or {})
        self._spaces[name] = entry
        return entry

    def get_space(self, name: str) -> Optional[Dict[str, Any]]:
        return self._spaces.get(name)

    def list_spaces(self) -> List[str]:
        return sorted(self._spaces)

    # ── 2. Time（時間）──────────────────────────────────────────────────────

    def register_time(
        self,
        name: str,
        ts_ms: Optional[int] = None,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """定義一個時間標記（Time）。"""
        data: Dict[str, Any] = {"ts_ms": ts_ms if ts_ms is not None else _now_ms()}
        data.update(attrs or {})
        entry = _entry("Time", name, data)
        self._times[name] = entry
        return entry

    def get_time(self, name: str) -> Optional[Dict[str, Any]]:
        return self._times.get(name)

    def list_times(self) -> List[str]:
        return sorted(self._times)

    # ── 3. Entity（實體）────────────────────────────────────────────────────

    def register_entity(
        self,
        name: str,
        space_ref: Optional[str] = None,
        time_ref: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """定義一個實體（Entity）。可附掛空間 / 時間參照。"""
        data: Dict[str, Any] = {}
        if space_ref is not None:
            data["space_ref"] = space_ref
        if time_ref is not None:
            data["time_ref"] = time_ref
        data.update(attrs or {})
        entry = _entry("Entity", name, data)
        self._entities[name] = entry
        return entry

    def get_entity(self, name: str) -> Optional[Dict[str, Any]]:
        return self._entities.get(name)

    def list_entities(self) -> List[str]:
        return sorted(self._entities)

    # ── 4. Identity（身份）──────────────────────────────────────────────────

    def register_identity(
        self,
        entity_ref: str,
        owner: str,
        signature: Optional[str] = None,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """為一個實體定義其身份（Identity）。"""
        data: Dict[str, Any] = {
            "entity_ref": entity_ref,
            "owner": owner,
            "signature": signature or ORIGIN_SIGNATURE,
        }
        data.update(attrs or {})
        entry = _entry("Identity", entity_ref, data)
        self._identities[entity_ref] = entry
        return entry

    def get_identity(self, entity_ref: str) -> Optional[Dict[str, Any]]:
        return self._identities.get(entity_ref)

    # ── 5. State（狀態）─────────────────────────────────────────────────────

    def set_state(self, entity_ref: str, key: str, value: Any) -> Dict[str, Any]:
        """設定實體的狀態鍵值（State）。"""
        if entity_ref not in self._states:
            self._states[entity_ref] = {}
        self._states[entity_ref][key] = value
        record = {
            "kind": "State",
            "entity_ref": entity_ref,
            "key": key,
            "value": value,
            "ts_ms": _now_ms(),
        }
        record["hash"] = _sha256(record)
        return record

    def get_state(self, entity_ref: str) -> Dict[str, Any]:
        return dict(self._states.get(entity_ref, {}))

    # ── 6. Relation（關係）──────────────────────────────────────────────────

    def register_relation(
        self,
        from_entity: str,
        rel_type: str,
        to_entity: str,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """在兩個實體之間定義一個關係（Relation）。"""
        data: Dict[str, Any] = {
            "from_entity": from_entity,
            "rel_type": rel_type,
            "to_entity": to_entity,
        }
        data.update(attrs or {})
        entry = _entry("Relation", f"{from_entity}:{rel_type}:{to_entity}", data)
        self._relations.append(entry)
        return entry

    def query_relations(
        self,
        from_entity: Optional[str] = None,
        to_entity: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """查詢關係，可按來源或目標實體過濾。"""
        result = self._relations
        if from_entity is not None:
            result = [r for r in result if r["data"]["from_entity"] == from_entity]
        if to_entity is not None:
            result = [r for r in result if r["data"]["to_entity"] == to_entity]
        return list(result)

    # ── 7. Event（事件）─────────────────────────────────────────────────────

    def emit_event(
        self,
        entity_ref: str,
        event_type: str,
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """發射一個事件（Event）。"""
        data: Dict[str, Any] = {
            "entity_ref": entity_ref,
            "event_type": event_type,
            "payload": payload or {},
            "ts_ms": _now_ms(),
        }
        entry = _entry("Event", f"{entity_ref}:{event_type}", data)
        self._events.append(entry)
        return entry

    def query_events(
        self,
        entity_ref: Optional[str] = None,
        event_type: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        result = self._events
        if entity_ref is not None:
            result = [e for e in result if e["data"]["entity_ref"] == entity_ref]
        if event_type is not None:
            result = [e for e in result if e["data"]["event_type"] == event_type]
        return list(result)

    # ── 8. Rule（規則）──────────────────────────────────────────────────────

    def declare_rule(
        self,
        name: str,
        condition: str,
        action: str,
        priority: int = 0,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """聲明一條規則（Rule）。"""
        data: Dict[str, Any] = {
            "condition": condition,
            "action": action,
            "priority": priority,
        }
        data.update(attrs or {})
        entry = _entry("Rule", name, data)
        self._rules[name] = entry
        return entry

    def get_rule(self, name: str) -> Optional[Dict[str, Any]]:
        return self._rules.get(name)

    def list_rules(self, min_priority: int = 0) -> List[Dict[str, Any]]:
        """列出所有規則，可按優先級過濾，高優先級排前。"""
        rules = [r for r in self._rules.values()
                 if r["data"]["priority"] >= min_priority]
        return sorted(rules, key=lambda r: -r["data"]["priority"])

    # ── 9. Memory（記憶）────────────────────────────────────────────────────

    def record_memory(
        self,
        entity_ref: str,
        snapshot: Dict[str, Any],
        memory_type: str = "state_snapshot",
    ) -> Dict[str, Any]:
        """記錄一個記憶（Memory）快照。"""
        data: Dict[str, Any] = {
            "entity_ref": entity_ref,
            "memory_type": memory_type,
            "snapshot": snapshot,
            "ts_ms": _now_ms(),
        }
        entry = _entry("Memory", f"{entity_ref}@{data['ts_ms']}", data)
        self._memories.append(entry)
        return entry

    def recall_memories(self, entity_ref: str) -> List[Dict[str, Any]]:
        """回憶指定實體的所有記憶，按時序排列。"""
        return [m for m in self._memories if m["data"]["entity_ref"] == entity_ref]

    # ── 10. Evolution（演化）────────────────────────────────────────────────

    def record_evolution(
        self,
        entity_ref: str,
        before: Dict[str, Any],
        after: Dict[str, Any],
        description: str = "",
    ) -> Dict[str, Any]:
        """記錄一次演化（Evolution）：before → after。"""
        ts = _now_ms()
        data: Dict[str, Any] = {
            "entity_ref": entity_ref,
            "before": before,
            "after": after,
            "description": description,
            "ts_ms": ts,
            "delta_hash": _sha256({"b": before, "a": after}),
        }
        entry = _entry("Evolution", f"{entity_ref}@{ts}", data)
        self._evolutions.append(entry)
        return entry

    def query_evolutions(self, entity_ref: str) -> List[Dict[str, Any]]:
        return [e for e in self._evolutions if e["data"]["entity_ref"] == entity_ref]

    # ── 11. Observation（觀測）──────────────────────────────────────────────

    def observe(
        self,
        observer: str,
        target_ref: str,
        key: str,
        value: Any,
        attrs: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """記錄一次觀測（Observation）。"""
        ts = _now_ms()
        data: Dict[str, Any] = {
            "observer": observer,
            "target_ref": target_ref,
            "key": key,
            "value": value,
            "ts_ms": ts,
        }
        data.update(attrs or {})
        entry = _entry("Observation", f"{observer}→{target_ref}:{key}@{ts}", data)
        self._observations.append(entry)
        return entry

    def query_observations(
        self,
        observer: Optional[str] = None,
        target_ref: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        result = self._observations
        if observer is not None:
            result = [o for o in result if o["data"]["observer"] == observer]
        if target_ref is not None:
            result = [o for o in result if o["data"]["target_ref"] == target_ref]
        return list(result)

    # ── Snapshot ────────────────────────────────────────────────────────────

    def snapshot(self) -> Dict[str, Any]:
        """返回整個世界定義層的不可變快照。"""
        snap: Dict[str, Any] = {
            "origin_signature": self.origin_signature,
            "layer": "WorldDefinition",
            "primitives": {
                "Space":       {"count": len(self._spaces),       "names": self.list_spaces()},
                "Time":        {"count": len(self._times),        "names": self.list_times()},
                "Entity":      {"count": len(self._entities),     "names": self.list_entities()},
                "Identity":    {"count": len(self._identities)},
                "State":       {"entity_count": len(self._states)},
                "Relation":    {"count": len(self._relations)},
                "Event":       {"count": len(self._events)},
                "Rule":        {"count": len(self._rules),        "names": sorted(self._rules)},
                "Memory":      {"count": len(self._memories)},
                "Evolution":   {"count": len(self._evolutions)},
                "Observation": {"count": len(self._observations)},
            },
            "snapshot_at_ms": _now_ms(),
        }
        snap["hash"] = _sha256(snap)
        return snap
