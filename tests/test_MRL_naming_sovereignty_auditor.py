"""test_MRL_naming_sovereignty_auditor.py — rl_20 命名主權稽核 (origin: MrLiouWord)"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "09_workflow"))
from MRL_Naming_Sovereignty_Auditor_v1 import audit_name, audit_batch

def test_vendor_prefix_violates():
    r = audit_name("claude/foo")
    assert not r["compliant"] and r["reclaim_to"] == "MRL_recovered/foo"

def test_copilot_violates():
    assert not audit_name("copilot/bar")["compliant"]

def test_mrl_compliant():
    assert audit_name("MRL_mother_system")["compliant"]

def test_main_compliant():
    assert audit_name("main")["compliant"]

def test_recovered_compliant():
    assert audit_name("MRL_recovered/x")["compliant"]

def test_legacy_canonical_violates():
    r = audit_name("MRL_RuntimeScopeGraph")
    assert not r["compliant"]  # ScopeGraph 歷史名
    assert r["reclaim_to"] == "MRL_RuntimeStructureField"


def test_non_mrl_name_reclaims_to_mrl_prefix():
    r = audit_name("vector_store")
    assert not r["compliant"]
    assert r["reclaim_to"].startswith("MRL_")


def test_mrl_without_underscore_is_not_compliant():
    r = audit_name("MRLinvalid")
    assert not r["compliant"]
    assert "non_mrl_naming" in r["violations"]

def test_batch():
    r = audit_batch(["claude/a","MRL_x","main","codex/b"])
    assert r["violations"] == 2 and r["compliant"] == 2
