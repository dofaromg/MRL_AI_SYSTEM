# MRL_AI_SYSTEM

FlowAgent / MRL monorepo — compliance + trace + runtime + memory.

## Directory structure

| Directory | Layer | Purpose |
|-----------|-------|---------|
| `00_rootlaw/` | L0 ROOT + L3 LAW | Immutable foundational invariants; supersede all other rules |
| `01_schema/` | L1 SEED | JSON Schema contracts for all data flowing through the system |
| `02_principles/` | L3 LAW | AUP-aligned guard rules and default policy settings |
| `03_memory/` | L6 REFLECT | Merkle chain (canonical) + vector store (semantic retrieval) |
| `04_runtime/` | L7 LOOP | FlowAgent kernel — heartbeat loop, trace writer, chain commits |
| `05_persona/` | L4 WORLD | Agent persona definitions and capability scopes |
| `06_trace/` | L6 REFLECT | Dual-stream audit trail: canonical Merkle + operational JSONL |
| `07_ingest/` | L2 PARTICLE | Allowlists, denylists, and ingest source gates |
| `08_sources/` | L0 ROOT | Canonical source manifest (sealed spec mirror) |
| `09_workflow/` | L7 LOOP | Workflow DAGs and orchestration step definitions |

## Design principles

- **Deny-by-default** — all external actions blocked unless explicitly allowlisted
- **Audit everything** — every action writes to both Merkle chain and JSONL before execution
- **Human override** — REQUIRE_HUMAN decisions never execute without a recorded proof
- **No hidden instructions** — all directives traceable to a source file in this repo
- **Mutual benefit** — actions must be justified and reversible

## Layer stack (L0–L7)

```
L0 ROOT     source of truth; never deleted
L1 SEED     initial constraints / contracts
L2 PARTICLE content units and state changes
L3 LAW      explicit rules (Rootlaw + compliance + AUP gates)
L4 WORLD    aligned models across worlds
L5 MIRROR   translation of actions/state across worlds
L6 REFLECT  facts, records, accountability
L7 LOOP     validate, then roll forward; rollback with proofs
```

