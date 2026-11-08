#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
test_MRL_autonomous_runtime_module_v1.py — 自主運行模組重建驗收
origin_signature: MrLiouWord

pytest 相容；沙盒無 pytest 時可獨立執行：
    python3 tests/test_MRL_autonomous_runtime_module_v1.py
"""
from __future__ import annotations

import asyncio
import pathlib
import sys

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
for _sub in [_REPO_ROOT, _REPO_ROOT / "09_workflow"]:
    if str(_sub) not in sys.path:
        sys.path.insert(0, str(_sub))

from MRL_AutonomousRuntime_Module_v1 import (  # noqa: E402
    AutonomousRuntimeBuilder,
    CapabilityMaterial,
)


def _run(coro):
    return asyncio.run(coro)


def test_distill_deduplicates_and_keeps_latest_version():
    builder = AutonomousRuntimeBuilder(
        [
            CapabilityMaterial(
                name="ToolLoop",
                version="1.0.0",
                entrypoint="pkg:toolloop",
                source="src-a",
                tags=("runtime",),
            ),
            CapabilityMaterial(
                name="toolloop",
                version="1.2.0",
                entrypoint="pkg:toolloop",
                dependencies=("PolicyGate",),
                source="src-b",
                tags=("loop",),
            ),
        ]
    )
    distilled = builder.distill()
    assert len(distilled) == 1
    item = distilled[0]
    assert item.canonical_name == "toolloop"
    assert item.selected_version == "1.2.0"
    assert item.absorbed_count == 2
    assert item.dependencies == ("policygate",)
    assert item.sources == ("src-a", "src-b")
    assert item.tags == ("loop", "runtime")


def test_rebuild_generates_dependency_boot_order():
    builder = AutonomousRuntimeBuilder(
        [
            CapabilityMaterial(name="A", version="1.0.0", entrypoint="a", dependencies=("B",)),
            CapabilityMaterial(name="B", version="1.0.0", entrypoint="b", dependencies=("C",)),
            CapabilityMaterial(name="C", version="1.0.0", entrypoint="c"),
        ]
    )
    spec = builder.rebuild()
    assert spec.boot_order == ("c", "b", "a")
    assert spec.dependency_graph["a"] == ("b",)


def test_rebuild_cycle_falls_back_to_stable_order():
    builder = AutonomousRuntimeBuilder(
        [
            CapabilityMaterial(name="A", version="1.0.0", entrypoint="a", dependencies=("B",)),
            CapabilityMaterial(name="B", version="1.0.0", entrypoint="b", dependencies=("A",)),
        ]
    )
    spec = builder.rebuild()
    assert spec.boot_order == ("a", "b")


def test_default_agent_config_is_deny_by_default_with_tool_allow():
    def add(a: int, b: int) -> int:
        return a + b

    builder = AutonomousRuntimeBuilder()
    config = builder.build_agent_config([add])

    async def main():
        resp_ok = await builder.run_once("TOOL:add a=2 b=5", config)
        resp_bad = await builder.run_once("TOOL:sub a=2 b=1", config)
        assert "add→7" in resp_ok.text
        assert "sub→錯誤:政策 'deny_all' 拒絕" in resp_bad.text

    _run(main())


if __name__ == "__main__":
    import traceback

    tests = [(n, f) for n, f in sorted(globals().items()) if n.startswith("test_") and callable(f)]
    passed, failed = 0, 0
    for name, fn in tests:
        try:
            fn()
            passed += 1
            print(f"PASS {name}")
        except Exception:
            failed += 1
            print(f"FAIL {name}")
            traceback.print_exc()
    print(f"\n{passed} passed, {failed} failed / {len(tests)} total")
    sys.exit(1 if failed else 0)
