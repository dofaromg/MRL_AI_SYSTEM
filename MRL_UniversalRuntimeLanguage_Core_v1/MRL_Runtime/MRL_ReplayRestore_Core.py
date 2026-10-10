# MRL_ReplayRestore_Core
# origin_signature: MrLiouWord
# layer: MRL_Runtime
"""精確重播 / 精確回復 / 狀態回滾 / 時間軌跡。

模型：runtime 將每一步 op 記錄為 event；state 由事件序確定性折疊（fold）而成。
  replay(graph)            重播全事件 → 重建最終 state（與原 state hash 相同 = exact）
  restore(checkpoint)      由 checkpoint 還原 state
  rollback(events, n)      回滾至第 n 步
  exactness 由 state hash 比對判定。
"""

from __future__ import annotations

import copy
import hashlib
import json
from typing import Any, Dict, List

ORIGIN_SIGNATURE = "MrLiouWord"


def _state_hash(state: Dict[str, Any]) -> str:
    return hashlib.sha256(
        json.dumps(state, ensure_ascii=False, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _fold(events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """確定性折疊：事件序 → state。"""
    state: Dict[str, Any] = {"applied": [], "node_count": 0, "intent_tally": {}}
    for ev in events:
        state["applied"].append(ev["node_id"])
        state["node_count"] += 1
        intent = ev["intent"]
        state["intent_tally"][intent] = state["intent_tally"].get(intent, 0) + 1
    return state


class _LazyCheckpoint(dict):
    """與原版 {"step", "state", "hash"} 同形；state／hash 在讀取時才由共享的 applied 前綴物化。"""

    def __init__(self, step, applied_ref, n, node_count, tally):
        super().__init__(step=step)
        self._ref, self._n, self._nc, self._tally = applied_ref, n, node_count, tally

    def _materialize(self):
        if "state" not in self.keys():
            st = {"applied": list(self._ref[: self._n]), "node_count": self._nc, "intent_tally": dict(self._tally)}
            dict.__setitem__(self, "state", st)
            dict.__setitem__(self, "hash", _state_hash(st))

    def __getitem__(self, k):
        if k in ("state", "hash"):
            self._materialize()
        return dict.__getitem__(self, k)

    def get(self, k, default=None):
        if k in ("state", "hash"):
            self._materialize()
        return dict.get(self, k, default)

    def __iter__(self):
        self._materialize(); return dict.__iter__(self)

    def keys(self):
        return dict.keys(self)

    def items(self):
        self._materialize(); return dict.items(self)

    def values(self):
        self._materialize(); return dict.values(self)

    def __repr__(self):
        self._materialize(); return dict.__repr__(self)


class MRL_ReplayRestore_Core:
    def __init__(self, replay_structurefield: List[Dict[str, Any]]) -> None:
        # event = replay_structurefield step
        self.events: List[Dict[str, Any]] = list(replay_structurefield)
        self.checkpoints: Dict[int, Dict[str, Any]] = {}

    # ── 原始執行：折疊得 state，並沿途留 checkpoint ──
    def execute(self, checkpoint_every: int = 8) -> Dict[str, Any]:
        # v1.1（2026-10-10，建構者核准修核心）：checkpoint 改為延遲物化。
        # 原本每 8 步 deepcopy＋序列化整個 state（applied 隨步數增長）→ 總成本 O(n²)。
        # 現在只記 (step, applied 長度, intent_tally 小字典)；取用時才物化，內容與 hash 與原版逐位元組相同。
        state: Dict[str, Any] = {"applied": [], "node_count": 0, "intent_tally": {}}
        for i, ev in enumerate(self.events):
            state["applied"].append(ev["node_id"])
            state["node_count"] += 1
            intent = ev["intent"]
            state["intent_tally"][intent] = state["intent_tally"].get(intent, 0) + 1
            if i % checkpoint_every == 0:
                self.checkpoints[i] = _LazyCheckpoint(i, state["applied"], len(state["applied"]),
                                                      state["node_count"], dict(state["intent_tally"]))
        self.final_state = state
        self.final_hash = _state_hash(state)
        return state

    # ── 精確重播：由事件序重建，與原 final 比對 ──
    def replay(self) -> Dict[str, Any]:
        replayed = _fold(self.events)
        return {
            "state": replayed,
            "hash": _state_hash(replayed),
            "exact": _state_hash(replayed) == getattr(self, "final_hash", _state_hash(replayed)),
        }

    # ── 精確回復：由 checkpoint 還原並續播至尾，與原 final 比對 ──
    def restore(self, from_step: int | None = None) -> Dict[str, Any]:
        if not self.checkpoints:
            self.execute()
        if from_step is None:
            from_step = max(self.checkpoints.keys())
        cp = self.checkpoints[from_step]
        state = copy.deepcopy(cp["state"])
        for ev in self.events[from_step + 1:]:
            state["applied"].append(ev["node_id"])
            state["node_count"] += 1
            intent = ev["intent"]
            state["intent_tally"][intent] = state["intent_tally"].get(intent, 0) + 1
        return {
            "from_step": from_step,
            "state": state,
            "hash": _state_hash(state),
            "exact": _state_hash(state) == getattr(self, "final_hash", _state_hash(state)),
        }

    # ── 狀態回滾：回到第 n 步的 state ──
    def rollback(self, n: int) -> Dict[str, Any]:
        state = _fold(self.events[: n + 1])
        return {"rolled_back_to": n, "state": state, "hash": _state_hash(state)}

    # ── 時間軌跡：每步的 hash 序 ──
    def time_trace(self) -> List[Dict[str, Any]]:
        trace: List[Dict[str, Any]] = []
        state: Dict[str, Any] = {"applied": [], "node_count": 0, "intent_tally": {}}
        for i, ev in enumerate(self.events):
            state["applied"].append(ev["node_id"])
            state["node_count"] += 1
            state["intent_tally"][ev["intent"]] = state["intent_tally"].get(ev["intent"], 0) + 1
            trace.append({"step": i, "node_id": ev["node_id"], "hash": _state_hash(state)})
        return trace
