"""
test_MRL_servicemesh_registry_v1.py — MRL 服務網登錄結構驗收
origin_signature: MrLiouWord
product: MRL_AI_SYSTEM

驗證 `MRL_ServiceMesh_Registry_v1.json`（DL580 22+ 服務快照吸收產物）之結構、
簽章、必填欄位、tier↔rootlaw 對應，並確保 in_repo_binder=true 之服務其 repo_ref
指到 repo 內真實存在的檔案（沙盒可跑；純結構驗收，不觸實機）。
"""
from __future__ import annotations

import json
import pathlib

import pytest

_REPO_ROOT = pathlib.Path(__file__).resolve().parent.parent
_REGISTRY = _REPO_ROOT / "MRL_ServiceMesh_Registry_v1.json"

ORIGIN_SIGNATURE = "MrLiouWord"
REQUIRED_SERVICE_FIELDS = {"name", "role", "in_repo_binder", "repo_ref", "status"}
ALLOWED_STATUS = {"沙盒可跑", "待起動", "待實機驗證", "沙盒可跑（docker-compose 定義）／實機待驗"}


@pytest.fixture(scope="module")
def registry():
    with _REGISTRY.open(encoding="utf-8") as fh:
        return json.load(fh)


@pytest.fixture(scope="module")
def services(registry):
    out = []
    for tier_key, tier in registry["service_tiers"].items():
        for svc_key, svc in tier["services"].items():
            out.append((tier_key, svc_key, svc))
    return out


# ─── 存在 / 可載入 / 簽章 ─────────────────────────────────────────────────────

def test_registry_file_exists():
    assert _REGISTRY.is_file(), "MRL_ServiceMesh_Registry_v1.json 不存在於 repo root"


def test_registry_is_valid_json(registry):
    assert isinstance(registry, dict)
    assert registry["schema"] == "MRL_ServiceMesh_Registry_v1"


def test_origin_signature_is_canonical(registry):
    # 正典簽章為 MrLiouWord，不得為草稿的 MrLiouWord2026
    assert registry["origin_signature"] == ORIGIN_SIGNATURE


def test_provenance_marks_pending_verification(registry):
    prov = registry["provenance"]
    assert "verification" in prov
    # 誠實：資料來源須標未實機驗證
    assert "待實機" in prov["verification"]


# ─── service_tiers 結構 ───────────────────────────────────────────────────────

def test_has_service_tiers(registry):
    tiers = registry["service_tiers"]
    assert isinstance(tiers, dict) and len(tiers) >= 5
    # 保留使用者草稿的 L1–L5 服務 tier 命名
    for expected in ("L1_conversation", "L2_persona_particle", "L3_new_runtime",
                     "L4_utility", "L5_entry"):
        assert expected in tiers, f"缺服務 tier {expected}"


def test_registry_covers_full_fleet(services):
    # 使用者截圖為 22+ 服務（含 infra）；登錄應涵蓋 ≥22
    assert len(services) >= 22, f"僅登錄 {len(services)} 服務，少於 22+ 全景"


def test_every_service_has_required_fields(services):
    for tier_key, svc_key, svc in services:
        missing = REQUIRED_SERVICE_FIELDS - set(svc)
        assert not missing, f"{tier_key}.{svc_key} 缺欄位 {missing}"


def test_every_service_status_is_honest(services):
    # 狀態只能是誠實三態之一；不得出現 PASS / 已完成 等誤標
    for tier_key, svc_key, svc in services:
        assert svc["status"] in ALLOWED_STATUS, \
            f"{tier_key}.{svc_key} 狀態 '{svc['status']}' 非允許誠實狀態"


def test_in_repo_binder_is_boolean(services):
    for tier_key, svc_key, svc in services:
        assert isinstance(svc["in_repo_binder"], bool), \
            f"{tier_key}.{svc_key}.in_repo_binder 須為 bool"


# ─── rootlaw 對應 ─────────────────────────────────────────────────────────────

def test_rootlaw_layer_mapping_present(registry):
    mapping = registry["rootlaw_layer_mapping"]
    assert isinstance(mapping, dict)
    # 每個服務 tier 皆須有 rootlaw L0–L7 對應
    for tier_key in registry["service_tiers"]:
        assert tier_key in mapping, f"tier {tier_key} 缺 rootlaw_layer_mapping 對應"


# ─── 誠實邊界：not_in_repo 記載草稿落差 ───────────────────────────────────────

def test_not_in_repo_records_known_gaps(registry):
    nir = registry["not_in_repo"]
    # 草稿與正典/實況落差須誠實記載
    for key in ("port_7801", "port_7830", "port_7840", "write_guard_8799",
                "signature_mismatch", "layer_scheme"):
        assert key in nir, f"not_in_repo 缺落差記載 {key}"


# ─── in_repo_binder=true 之 repo_ref 必須真的存在 ─────────────────────────────

def _extract_repo_paths(repo_ref: str):
    """從 repo_ref 文字中抽出看起來像 repo 相對路徑的 token（含 / 或已知副檔名）。"""
    import re
    candidates = set()
    for tok in re.split(r"[\s（）()、,;；：:]+", repo_ref):
        tok = tok.strip().strip("（）()").rstrip("。.,)")
        if not tok:
            continue
        # 只取含目錄分隔或明確檔名的 token
        if "/" in tok or tok.endswith((".py", ".js", ".cjs", ".json", ".yaml", ".yml", ".md")):
            # 去掉行內註記如 (MRL_PORT...) 之後的括號殘留
            candidates.add(tok)
    return candidates


def test_in_repo_true_services_reference_existing_files(services):
    """in_repo_binder=true 的服務，其 repo_ref 至少要指到一個真實存在的 repo 檔/目錄。"""
    for tier_key, svc_key, svc in services:
        if not svc["in_repo_binder"]:
            continue
        paths = _extract_repo_paths(svc["repo_ref"])
        assert paths, f"{tier_key}.{svc_key} in_repo_binder=true 但 repo_ref 無可解析路徑"
        found = False
        for p in paths:
            # 允許路徑前綴模糊（... 省略），取第一段實際目錄/檔比對
            base = p.split("...")[0].split("（")[0].strip("/")
            if not base:
                continue
            candidate = _REPO_ROOT / base
            # 目錄前綴存在即可（例如 MRL_RuntimeOS_.../ 這類省略寫法取第一段）
            if candidate.exists() or list(_REPO_ROOT.glob(base.split("/")[0] + "*")):
                found = True
                break
        assert found, f"{tier_key}.{svc_key} in_repo_binder=true 但 repo_ref 路徑 {paths} 均不存在於 repo"


# ─── in_repo_bound_ports 對照 ─────────────────────────────────────────────────

def test_in_repo_bound_ports_documented(registry):
    bound = registry["in_repo_bound_ports"]
    # 三個 Explore 報告確認 repo 內確有 binder 的核心埠
    for port in ("8790", "8788", "8787", "7950", "7700"):
        assert port in bound, f"in_repo_bound_ports 缺 {port}"
