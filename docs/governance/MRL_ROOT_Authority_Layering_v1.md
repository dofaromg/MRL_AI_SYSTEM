# MRL ROOT Authority Layering v1

## Canonical ruling

```text
ROOT authority       = Mrliou
Canonical product    = MrliouAI
Canonical namespace  = MRL_
Origin signature     = MrLiouWord
Mother runtime       = DL580 / MotherAssembly
```

## Layer order

```text
L0 ROOT_AUTHORITY     Mrliou
L1 MRL_PRODUCT        MrliouAI / MRL_
L2 MRL_CAPABILITY     MRL capability modules
L3 MRL_RUNTIME        DL580 / MotherAssembly / runtime services
L4 MRL_INTERFACE      browser, app, API and control surfaces
L5 MRL_ADAPTER        adapters, transports and compatibility aliases
L6 EXTERNAL_SOURCE    vendors, platforms, imported tools and historical evidence
```

The direction of authority is strictly top-down. Lower layers may provide material, transport, interfaces, compatibility or evidence, but may not redefine any higher-layer canonical identity.

## Required placement of external systems

External platform names are allowed only in the bottom two layers:

- `MRL_ADAPTER`
- `EXTERNAL_SOURCE`

Permitted roles:

- source
- adapter
- transport
- provenance
- compatibility alias
- vendor metadata
- historical evidence

Forbidden promotions:

- external name → product identity
- external name → root authority
- external name → canonical API route
- external name → packet type
- external name → trace prefix
- external name → runtime identity

## Canonical runtime contract

Every canonical runtime object must resolve to:

```json
{
  "product": "MrliouAI",
  "source_owner": "Mrliou",
  "origin_signature": "MrLiouWord"
}
```

Canonical routes use `/api/mrl/` or `/mrl/`.
Canonical packet types use the `MRL_` prefix.
Canonical trace identifiers use the `MRL-` prefix.

## Authority flow

```text
Mrliou
  ↓
MrliouAI
  ↓
MRL capability/runtime/interface
  ↓
MRL adapter/transport
  ↓
external platform/source/evidence
```

No reverse authority flow is permitted.

## Enforcement

The machine-readable source of truth is:

`config/MRL_Canonical_Authority_Registry_v1.json`

The regression gate is:

`tests/test_MRL_authority_layering_v1.py`
