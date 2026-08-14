# MRL Gemini External-Source Adapter

`origin_signature: MrLiouWord`  
`product: MrliouAI`  
`provider_role: external_material`

## Position

Gemini is a replaceable external compute and comparison source. It is not the
MRL product name, mother system, memory authority, routing authority, or source
of commercial ownership.

The durable commercial layer remains inside MrliouAI:

- MRL particle and response contracts;
- local-first routing and sensitive-data policy;
- Law-0 origin/provenance boundary;
- local memory eligibility and learning manifests;
- provider fallback and continuity;
- token, latency, failure and external-cost evidence.

Changing or removing Gemini must not change these MRL-owned layers.

## Runtime chain

```text
MRL request
  -> MRL_ProviderValueGate_v1 (local by default)
  -> MRL local model OR explicit Gemini source adapter
  -> MRL_OriginBoundaryGuard (external provenance retained)
  -> normalized MRL response + value ledger event
```

## Closed-by-default configuration

```text
GEMINI_API_KEY=<secret stored outside source control>
MRL_GEMINI_EXTERNAL_ENABLED=1
```

Both an enabled gate and an explicit `use_external=True` request are required.
Requests marked `sensitive` or `mrl_sensitive` never call the external adapter.
The API key is placed in the `x-goog-api-key` header and is never written into
the request URL, response envelope, provenance record, or value ledger.

## Files

- `09_workflow/MRL_Gemini_SourceAdapter_v1.py` — standard-library Gemini REST
  adapter, normalized response, external provenance seal.
- `09_workflow/MRL_ProviderValueGate_v1.py` — MRL-owned local-first policy,
  automatic local recovery, usage and configurable cost ledger.
- `tests/test_MRL_gemini_source_adapter.py` — no-network contract tests.
- `tests/test_MRL_provider_value_gate.py` — routing, sensitivity, recovery and
  no-prompt-retention tests.

## Learning boundary

Gemini responses are external material and are not automatically admitted to
MRL training or permanent memory. Model absorption must use Mr.liou-owned or
appropriately licensed datasets with provenance. External outputs may be used
for an explicitly permitted comparison/evaluation workflow, but the default
runtime path does not distill or fine-tune on them.
