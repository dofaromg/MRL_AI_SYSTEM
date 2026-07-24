import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
REGISTRY = ROOT / "config" / "MRL_Canonical_Authority_Registry_v1.json"


def load_registry():
    with REGISTRY.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def test_root_authority_identity():
    registry = load_registry()
    root = registry["root_authority"]
    assert root["owner"] == "Mrliou"
    assert root["product"] == "MrliouAI"
    assert root["namespace"] == "MRL_"
    assert root["origin_signature"] == "MrLiouWord"
    assert root["mother_runtime"] == "DL580/MotherAssembly"


def test_layer_order_is_top_down_and_complete():
    registry = load_registry()
    expected = [
        "ROOT_AUTHORITY",
        "MRL_PRODUCT",
        "MRL_CAPABILITY",
        "MRL_RUNTIME",
        "MRL_INTERFACE",
        "MRL_ADAPTER",
        "EXTERNAL_SOURCE",
    ]
    assert registry["layer_order"] == expected
    ranks = [registry["layers"][name]["rank"] for name in expected]
    assert ranks == list(range(len(expected)))


def test_only_root_and_mrl_layers_may_define_canonical_identity():
    registry = load_registry()
    allowed = {
        name
        for name, layer in registry["layers"].items()
        if layer["may_define_canonical_identity"]
    }
    assert allowed == {
        "ROOT_AUTHORITY",
        "MRL_PRODUCT",
        "MRL_CAPABILITY",
        "MRL_RUNTIME",
    }


def test_external_systems_are_bottom_layers_only():
    registry = load_registry()
    layers = registry["layers"]
    assert layers["MRL_ADAPTER"]["rank"] > layers["MRL_INTERFACE"]["rank"]
    assert layers["EXTERNAL_SOURCE"]["rank"] > layers["MRL_ADAPTER"]["rank"]
    assert layers["MRL_ADAPTER"]["may_define_canonical_identity"] is False
    assert layers["EXTERNAL_SOURCE"]["may_define_canonical_identity"] is False
    assert registry["external_platform_policy"]["placement"] == "bottom"


def test_canonical_contract_is_mrl_owned():
    contract = load_registry()["canonical_contract"]
    assert contract["product"] == "MrliouAI"
    assert contract["source_owner"] == "Mrliou"
    assert contract["origin_signature"] == "MrLiouWord"
    assert contract["route_prefixes"] == ["/api/mrl/", "/mrl/"]
    assert contract["packet_prefix"] == "MRL_"
    assert contract["trace_prefix"] == "MRL-"


def test_external_platforms_cannot_be_promoted():
    policy = load_registry()["external_platform_policy"]
    forbidden = set(policy["forbidden_targets"])
    assert {
        "product",
        "canonical_route",
        "packet_type",
        "trace_prefix",
        "root_authority",
        "runtime_identity",
    }.issubset(forbidden)
