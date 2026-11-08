# MRL Naming Authority Law v1

## 1. Canonical names

```text
Owner = Mrliou
Product = MrliouAI
Namespace = MRL_
Origin signature = MrLiouWord
Primary branch = MrliouAI
```

## 2. Protected naming surfaces

This Law governs repository names, package names, runtime constants, environment variables, API routes, packet types, trace prefixes, deployment names, UI titles, manifests, registries, telemetry identifiers, generated artifacts and test contracts.

## 3. Authorized naming

A naming change requires explicit ROOT instruction, a reviewable diff, preserved prior state, migration mapping, compatibility impact analysis and rollback path.

## 4. Forbidden promotion

External platform, vendor, framework, source-project or tool names may not be promoted into canonical product identity, ROOT identity, namespace, runtime identity, route prefix, packet type, trace prefix or primary branch authority.

## 5. Compatibility aliases

Legacy or external names may exist only as:

- `compatibility_alias`
- `source_adapter`
- `provenance`
- `vendor_metadata`
- historical audit evidence

Every alias must point toward the MRL canonical name and must not reverse authority.

## 6. Unauthorized change

Any unapproved naming change is a CRITICAL incident and must trigger merge/deployment blocking, evidence preservation, canonical restoration, dependency tracing and access review.

## 7. Rename sequence

```text
Recover original
→ Inventory occurrences
→ Classify canonical vs provenance
→ Build dependency map
→ Define migration map
→ Rename canonical surfaces
→ Preserve aliases where required
→ Run regression gates
→ Synchronize mainline
→ Create identical backup
```
