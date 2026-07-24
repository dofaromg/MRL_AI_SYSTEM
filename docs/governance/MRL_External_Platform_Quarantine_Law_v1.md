# MRL External Platform Quarantine Law v1

## Purpose

This Law prevents external platforms, vendors, frameworks, models, assistants, source projects and deployment systems from being promoted into MRL canonical authority.

## Quarantine position

External entities are restricted to the bottom layers:

```text
MRL_ADAPTER
→ EXTERNAL_SOURCE
→ ARCHIVE / PROVENANCE
```

## Allowed roles

- adapter
- transport
- hosting surface
- build service
- deployment service
- source reference
- provenance source
- compatibility layer
- vendor metadata
- imported material

## Forbidden authority

External entities may not define or override:

- ROOT owner;
- product identity;
- canonical namespace;
- origin signature;
- runtime identity;
- route prefix;
- packet type;
- trace prefix;
- primary branch;
- environment defaults;
- ownership registry;
- governance law.

## Intake procedure

Every external asset must pass through:

```text
Acquire
→ Hash
→ Preserve original
→ Record provenance
→ Classify
→ Quarantine
→ Map dependencies
→ Canonicalize
→ Integrate through MRL adapter
→ Verify
```

## Promotion gate

No external name, schema or identity may cross into a canonical MRL layer unless ROOT explicitly authorizes the exact promotion and the migration is documented, reversible and validated.

## Violation response

An unauthorized external-name promotion is a CRITICAL governance and security incident. Merge and deployment must be blocked, evidence preserved, canonical identity restored and all dependent branches and environments inspected.
