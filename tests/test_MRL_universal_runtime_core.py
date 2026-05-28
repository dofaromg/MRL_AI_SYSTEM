"""
test_MRL_universal_runtime_core.py — MRL_UniversalRuntimeLanguage_Core_v1 驗收
origin_signature: MrLiouWord

涵蓋：parser 多語言、MetaIR 確定性、ParticleIR 可逆、Replay/Restore exact、
PersistentLoop 重啟存活、WorldRuntime 同步、Verification 六項 PASS、DB adapter。
"""
from __future__ import annotations

import pytest

from MRL_UniversalRuntimeLanguage_Core_v1 import ORIGIN_SIGNATURE, SOVEREIGNTY
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Language import (
    MRL_MetaIR_Compiler,
    MRL_ParticleIR_Engine,
    MRL_UniversalParser_Core,
)
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_DB.MRL_BaseWorld_DB_Adapter import (
    ATTACHMENT_POINTS,
    MRL_BaseWorld_DB_Adapter,
)
from MRL_UniversalRuntimeLanguage_Core_v1.MRL_Runtime.MRL_DL580_Runtime import MRL_DL580_Runtime

SAMPLE_PY = (
    "import os\n\n"
    "def greet(name):\n"
    "    msg = 'hi ' + name\n"
    "    return msg\n\n"
    "class World:\n"
    "    def spin(self):\n"
    "        for i in range(3):\n"
    "            print(i)\n"
)


def test_sovereignty_constants():
    assert ORIGIN_SIGNATURE == "MrLiouWord"
    assert SOVEREIGNTY["subject"] == "MRL_Mother_Runtime"
    assert SOVEREIGNTY["deploy_host"] == "DL580"
    assert "Cloudflare" in SOVEREIGNTY["external_mirror_layer"]
    assert SOVEREIGNTY["perception_is_subject"] is True


@pytest.mark.parametrize("lang,src", [
    ("python", "def f(x):\n    return x\n"),
    ("typescript", "export function f() {\n  return 1;\n}\n"),
    ("cpp", "#include <x>\nint main(){\n return 0;\n}\n"),
    ("json", '{"a":1,"b":[1,2]}'),
    ("markdown", "# H\n\n- a\n\ntext\n"),
])
def test_parser_multilang(lang, src):
    r = MRL_UniversalParser_Core.parse(src, lang)
    assert r["lang"] == lang
    assert r["unit_count"] >= 1
    assert r["origin_signature"] == "MrLiouWord"


def test_metair_deterministic():
    parsed = MRL_UniversalParser_Core.parse(SAMPLE_PY, "python")
    a = MRL_MetaIR_Compiler.compile_metair(parsed)
    b = MRL_MetaIR_Compiler.compile_metair(parsed)
    assert a["metair_hash"] == b["metair_hash"]
    assert a["node_count"] > 0


def test_particle_chain_reversible():
    text = "alpha beta\nbeta alpha gamma\n"
    trace = MRL_ParticleIR_Engine.to_particles(text)
    assert MRL_ParticleIR_Engine.from_particles(trace) == text
    env = MRL_ParticleIR_Engine.collapse(text)
    assert MRL_ParticleIR_Engine.expand(env) == text
    jumped, perm = MRL_ParticleIR_Engine.jump(text)
    assert MRL_ParticleIR_Engine.unjump(jumped, perm) == text


def test_db_adapter_local_emulation():
    db = MRL_BaseWorld_DB_Adapter().local_emulation()
    db.attach("Trace", "h1", "trace", "{}", 1)
    assert db.count("Trace") == 1
    assert set(ATTACHMENT_POINTS) == {
        "Canon", "Registry", "FLTNZ_Asset", "Memory_Sphere", "Proof", "Trace", "Mirror"
    }
    assert db.status()["prod_schema"]["tables"] == 27


def test_full_pipeline_acceptance_pass(tmp_path):
    runtime = MRL_DL580_Runtime(runtime_dir=str(tmp_path))
    result = runtime.run(SAMPLE_PY, lang="python", loop_id="pytest")
    v = result["verification"]
    # 全部六項
    assert v["total"] == 6
    assert v["passed"] == 6, v["checks"]
    assert v["acceptance"] is True
    assert v["token"] == "MRL_RUNTIME_ACCEPTANCE_PASS"
    # 個別保證
    assert result["replay"]["exact"] is True
    assert result["restore"]["exact"] is True
    assert result["persistent_loop"]["survives_restart"] is True
    assert result["world"]["synchronization_active"] is True
    assert result["roundtrip"]["exact"] is True
