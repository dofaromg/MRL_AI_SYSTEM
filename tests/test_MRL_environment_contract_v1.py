import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
CONTRACT = ROOT / "config" / "MRL_Environment_Contract_v1.json"
ENV_EXAMPLE = ROOT / ".env.mrl.example"


def load_contract():
    with CONTRACT.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def parse_env_example():
    values = {}
    for raw in ENV_EXAMPLE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        key, value = line.split("=", 1)
        values[key] = value
    return values


def test_canonical_account_and_product_identity():
    identity = load_contract()["canonical_identity"]
    assert identity["github_user"] == "dofaromg"
    assert identity["canonical_name"] == "Mrliou"
    assert identity["product"] == "MrliouAI"
    assert identity["namespace"] == "MRL_"
    assert identity["origin_signature"] == "MrLiouWord"
    assert identity["repository_owner_scope"] == "dofaromg/MRL_AI_SYSTEM"


def test_environment_defaults_match_canonical_identity():
    contract = load_contract()["environment_parameters"]
    env = parse_env_example()
    expected = {
        "MRL_PRODUCT_NAME": "MrliouAI",
        "MRL_SOURCE_OWNER": "Mrliou",
        "MRL_ORIGIN_SIGNATURE": "MrLiouWord",
        "MRL_NAMESPACE": "MRL_",
        "MRL_PLATFORM_DOMAIN": "mrliouword.com",
        "MRL_API_BASE_URL": "https://mrliouword.com",
        "NEXT_PUBLIC_MRL_PRODUCT_NAME": "MrliouAI",
        "NEXT_PUBLIC_MRL_API_BASE_URL": "https://mrliouword.com",
    }
    for key, value in expected.items():
        assert contract[key]["default"] == value
        assert env[key] == value


def test_secrets_are_blank_in_example():
    contract = load_contract()["environment_parameters"]
    env = parse_env_example()
    for key in ("MRL_DL580_ORIGIN", "MRL_BRIDGE_TOKEN"):
        assert contract[key]["secret"] is True
        assert contract[key]["default"] == ""
        assert env[key] == ""


def test_external_platforms_cannot_override_identity():
    policy = load_contract()["external_platform_policy"]
    assert policy["placement"] == "bottom_adapter_layer"
    assert policy["may_override_canonical_identity"] is False


def test_unauthorized_change_is_critical_suspected_ip_incident():
    policy = load_contract()["unauthorized_change_policy"]
    assert policy["severity"] == "CRITICAL"
    assert policy["owner_declared_policy"] is True
    assert {
        "UNAUTHORIZED_NAMING_CHANGE",
        "SUSPECTED_IP_INFRINGEMENT",
        "SUSPECTED_ACCOUNT_OR_REPOSITORY_ABUSE",
        "POTENTIAL_COORDINATED_PARTICIPATION",
    }.issubset(set(policy["classifications"]))
    assert {
        "block_merge",
        "block_deployment",
        "preserve_commit_diff_actor_timestamp_review_and_ci_evidence",
        "restore_canonical_identity",
        "open_governance_incident",
        "review_credentials_branch_protection_and_deployment_access",
        "prepare_evidence_package_for_legal_review",
    }.issubset(set(policy["actions"]))
