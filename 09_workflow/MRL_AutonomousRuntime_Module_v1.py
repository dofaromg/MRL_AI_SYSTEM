#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
MRL_AutonomousRuntime_Module_v1.py — 去重蒸餾重建為母體自主運行模組
origin_signature: MrLiouWord
layer: L7 LOOP
group: Y=3 FlowAgentRuntime

此模組把「吸收 → 去重 → 蒸餾 → 重建」流程落地為可執行程式：
1) 吸收外部材料（CapabilityMaterial）
2) 去重合併（同名+同 entrypoint 的多來源）
3) 蒸餾為母體 canonical 能力集合（DistilledCapability）
4) 重建成自主運行模組規格（AutonomousModuleSpec）

重建結果可直接產生 AgentHarness 的 AgentConfig（deny-by-default）。
"""
from __future__ import annotations

import asyncio
import dataclasses
from collections import defaultdict, deque
from typing import Any, Callable, Deque, Dict, List, Optional, Sequence, Set, Tuple

from MRL_utils import ORIGIN_SIGNATURE
from MRL_AgentHarness_Kernel_v1 import Agent, AgentConfig, ChatResponse, EchoGateway, ModelGateway
from MRL_AgentHarness_PolicyGate_v1 import Policy, allow, deny_all

__all__ = [
    "CapabilityMaterial",
    "DistilledCapability",
    "AutonomousModuleSpec",
    "AutonomousRuntimeBuilder",
]


def _norm(text: str) -> str:
    return text.strip().lower()


def _version_key(version: str) -> Tuple[int, ...]:
    clean = version.strip().lstrip("v")
    nums: List[int] = []
    for part in clean.split("."):
        if part.isdigit():
            nums.append(int(part))
        else:
            break
    return tuple(nums) if nums else (0,)


@dataclasses.dataclass(frozen=True)
class CapabilityMaterial:
    """吸收來源材料。"""

    name: str
    version: str
    entrypoint: str
    dependencies: Tuple[str, ...] = ()
    source: str = ""
    tags: Tuple[str, ...] = ()
    metadata: Dict[str, Any] = dataclasses.field(default_factory=dict)


@dataclasses.dataclass(frozen=True)
class DistilledCapability:
    """去重蒸餾後的 canonical 能力單元。"""

    canonical_name: str
    selected_version: str
    entrypoint: str
    dependencies: Tuple[str, ...]
    sources: Tuple[str, ...]
    tags: Tuple[str, ...]
    absorbed_count: int


@dataclasses.dataclass(frozen=True)
class AutonomousModuleSpec:
    """自主運行模組重建結果。"""

    module_name: str
    origin_signature: str
    capabilities: Tuple[DistilledCapability, ...]
    dependency_graph: Dict[str, Tuple[str, ...]]
    boot_order: Tuple[str, ...]


class AutonomousRuntimeBuilder:
    """吸收去重蒸餾重建管線。"""

    def __init__(self, materials: Optional[Sequence[CapabilityMaterial]] = None) -> None:
        self._materials: List[CapabilityMaterial] = list(materials or [])

    def absorb(self, material: CapabilityMaterial) -> None:
        self._materials.append(material)

    def absorb_many(self, materials: Sequence[CapabilityMaterial]) -> None:
        self._materials.extend(materials)

    @property
    def materials(self) -> Tuple[CapabilityMaterial, ...]:
        return tuple(self._materials)

    def distill(self) -> Tuple[DistilledCapability, ...]:
        buckets: Dict[Tuple[str, str], List[CapabilityMaterial]] = defaultdict(list)
        for item in self._materials:
            key = (_norm(item.name), _norm(item.entrypoint))
            buckets[key].append(item)

        distilled: List[DistilledCapability] = []
        for (name, entrypoint), group in buckets.items():
            selected = max(group, key=lambda m: _version_key(m.version))
            deps: Set[str] = set()
            sources: Set[str] = set()
            tags: Set[str] = set()
            for g in group:
                deps.update(_norm(d) for d in g.dependencies if d.strip())
                if g.source.strip():
                    sources.add(g.source.strip())
                tags.update(t.strip() for t in g.tags if t.strip())

            # 只保留可在本次蒸餾集合內解析的 canonical 依賴，避免外部殘留。
            deps_sorted = tuple(sorted(deps))
            distilled.append(
                DistilledCapability(
                    canonical_name=name,
                    selected_version=selected.version,
                    entrypoint=entrypoint,
                    dependencies=deps_sorted,
                    sources=tuple(sorted(sources)),
                    tags=tuple(sorted(tags)),
                    absorbed_count=len(group),
                )
            )

        distilled.sort(key=lambda c: c.canonical_name)
        return tuple(distilled)

    def rebuild(self, module_name: str = "MRL_AutonomousRuntime_v1") -> AutonomousModuleSpec:
        capabilities = self.distill()
        names = {c.canonical_name for c in capabilities}
        graph: Dict[str, Tuple[str, ...]] = {
            c.canonical_name: tuple(d for d in c.dependencies if d in names)
            for c in capabilities
        }
        boot_order = self._topological_order(graph)
        return AutonomousModuleSpec(
            module_name=module_name,
            origin_signature=ORIGIN_SIGNATURE,
            capabilities=capabilities,
            dependency_graph=graph,
            boot_order=boot_order,
        )

    @staticmethod
    def _topological_order(graph: Dict[str, Tuple[str, ...]]) -> Tuple[str, ...]:
        indegree: Dict[str, int] = {node: 0 for node in graph}
        reverse: Dict[str, List[str]] = {node: [] for node in graph}
        for node, deps in graph.items():
            for dep in deps:
                reverse.setdefault(dep, []).append(node)
                indegree[node] += 1

        queue: Deque[str] = deque(sorted([node for node, d in indegree.items() if d == 0]))
        ordered: List[str] = []
        while queue:
            node = queue.popleft()
            ordered.append(node)
            for nxt in sorted(reverse.get(node, [])):
                indegree[nxt] -= 1
                if indegree[nxt] == 0:
                    queue.append(nxt)

        if len(ordered) == len(graph):
            return tuple(ordered)

        # cycle fallback: 保留已解排序，再加上循環節點的穩定字典序。
        remain = sorted(node for node in graph if node not in ordered)
        return tuple(ordered + remain)

    @staticmethod
    def build_agent_config(
        tools: Sequence[Callable[..., Any]],
        *,
        gateway: Optional[ModelGateway] = None,
        policies: Optional[Sequence[Policy]] = None,
    ) -> AgentConfig:
        if policies is None:
            default_policies: List[Policy] = [deny_all()]
            for tool in tools:
                default_policies.append(allow(getattr(tool, "__name__", "tool")))
            policies = default_policies

        return AgentConfig(
            gateway=gateway or EchoGateway(),
            tools=list(tools),
            policies=list(policies),
        )

    @staticmethod
    async def run_once(prompt: str, config: AgentConfig) -> ChatResponse:
        async with Agent(config) as agent:
            return await agent.chat(prompt)


def _demo() -> None:
    materials = [
        CapabilityMaterial(
            name="ToolLoop",
            version="1.0.0",
            entrypoint="MRL_AgentHarness_ToolLoop_v1:ToolLoopRunner",
            source="sdk-python",
            tags=("runtime", "tool"),
        ),
        CapabilityMaterial(
            name="ToolLoop",
            version="1.1.0",
            entrypoint="MRL_AgentHarness_ToolLoop_v1:ToolLoopRunner",
            dependencies=("PolicyGate",),
            source="mother-patch",
            tags=("runtime", "tool"),
        ),
        CapabilityMaterial(
            name="PolicyGate",
            version="1.0.0",
            entrypoint="MRL_AgentHarness_PolicyGate_v1:enforce",
            source="sdk-python",
            tags=("law",),
        ),
    ]
    builder = AutonomousRuntimeBuilder(materials)
    spec = builder.rebuild()
    print(spec)

    def add(a: int, b: int) -> int:
        return a + b

    async def main() -> None:
        cfg = builder.build_agent_config([add])
        result = await builder.run_once("TOOL:add a=2 b=3", cfg)
        print(result.text)

    asyncio.run(main())


if __name__ == "__main__":
    _demo()
