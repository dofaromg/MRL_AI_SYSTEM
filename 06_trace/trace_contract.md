# Trace Contract

Layer: L6 REFLECT  
Version: 1  
Status: canonical

---

## Purpose

This document is the authoritative contract governing all trace records
produced by FlowAgent. It defines:

- **Dual-stream commitments** — what must be written and where
- **Required fields** — minimum fields every trace record must carry
- **Audit invariants** — conditions that must hold at all times

Every component that writes a trace (runtime kernel, workflow steps, ingest
gates, repair loops) must comply with this contract. Violations must be
surfaced as `REQUIRE_HUMAN` decisions before execution continues.

---

## Dual-stream commitments

FlowAgent maintains two parallel trace streams. **Both must be written before
any external action executes.** The two streams are complementary; neither
replaces the other.

### Stream 1 — Canonical Merkle chain

| Property | Value |
|----------|-------|
| Writer | `03_memory/merkle/memory_chain.py` → `MerkleChain.commit()` |
| Format | SHA-256 linked JSONL (`entries.jsonl`) + head pointer (`head.txt`) |
| Schema | `01_schema/trace_record.schema.json` |
| Location | `03_memory/_data/memory_chain/` (runtime-only, gitignored) |
| Purpose | Tamper-evident, immutable, rollback-safe record of every decision |
| Invariant | Chain must be verifiable at any time via `MerkleChain.verify()` |

Merkle input for each entry:

```json
{
  "entry_id": "<uuid>",
  "timestamp_ms": <epoch_ms>,
  "payload": { /* structured event */ },
  "prev": "<sha256_of_previous_entry>"
}
```

### Stream 2 — Operational JSONL trace

| Property | Value |
|----------|-------|
| Writer | `04_runtime/flowcore_loop.py` → `log_event()` (and workflow steps) |
| Format | Newline-delimited JSON (`runtime_trace.jsonl`) |
| Schema | `01_schema/runtime_trace.schema.json` |
| Location | `06_trace/traces/_data/` (runtime-only, gitignored) |
| Purpose | Fast operational lookup, debugging, replay without chain overhead |
| Invariant | Every Merkle entry must have a corresponding operational line |

---

## Required fields

Every trace record — regardless of stream — must carry the following fields:

| Field | Type | Description |
|-------|------|-------------|
| `trace_id` | string (UUID) | Globally unique identifier for this record |
| `created_at` | string (ISO-8601 UTC) | Timestamp of record creation |
| `persona_id` | string | ID of the agent persona that triggered the action |
| `action_id` | string | ID of the action request |
| `action_type` | string | Action category (`read`, `write`, `external_call`, etc.) |
| `decision` | string enum | `ALLOW` \| `DENY` \| `REQUIRE_HUMAN` \| `SKIP` |
| `rule_hits` | string[] | List of rule IDs that matched (from `02_principles/rules.aup_v1.yaml`) |
| `merkle_root` | string (sha256) | Merkle root for this entry |
| `merkle_prev` | string (sha256) | Previous Merkle root (`0`×64 for genesis) |

### Conditional fields

| Field | Required when | Description |
|-------|--------------|-------------|
| `approval_proof` | `decision == REQUIRE_HUMAN` | Human approval token, type, and timestamp |
| `execution_result` | action was executed | Success flag, error message, metadata |
| `repair_context` | entry produced by repair loop | Original trace_id that triggered repair |

---

## Audit invariants

The following invariants must hold at all times and are enforced by
`MerkleChain.verify()` and the compliance gate in `04_runtime/flowcore_loop.py`.

### I-1 Write-before-execute

> Both trace streams must be written successfully **before** any external
> action executes. If either write fails, the action is DENIED and the failure
> is itself recorded in the operational stream.

### I-2 Chain continuity

> For every entry `e` in the Merkle chain:
> `e.merkle == SHA-256({ entry_id, timestamp_ms, payload, prev })`
> `e.prev == head at time of commit`

Any discontinuity discovered by `verify()` constitutes a chain integrity
violation and must trigger an immediate REQUIRE_HUMAN escalation.

### I-3 Approval-before-execution (REQUIRE_HUMAN)

> No action with `decision == REQUIRE_HUMAN` may execute without a recorded
> `approval_proof` that:
> - contains a non-empty `token`
> - has `approved_at` ≤ current UTC time
> - was issued for this `trace_id` specifically

Expired or recycled approval tokens are void.

### I-4 No deletion or mutation

> Existing Merkle entries must never be deleted or overwritten. The only
> permitted correction mechanism is proof-based rollback
> (`MerkleChain.rollback(target_merkle)`), which truncates the chain to a
> verified prior state and records the rollback itself.

### I-5 Rule traceability

> Every `DENY` and `REQUIRE_HUMAN` decision must list at least one `rule_hits`
> entry traceable to a rule ID defined in `02_principles/rules.aup_v1.yaml`
> or `00_rootlaw/rootlaw.yaml`. Decisions with an empty `rule_hits` are
> treated as chain integrity violations.

### I-6 Dual-stream parity

> The count of operational JSONL lines must be ≥ the count of Merkle entries
> for any given time window. A Merkle entry with no corresponding operational
> line is admissible (e.g., offline write); the reverse is not — an
> operational line without a Merkle entry means the canonical record is
> missing.

---

## Approval proof schema

Approval records must conform to the `approval_proof` sub-schema defined in
`01_schema/trace_record.schema.json`:

```json
{
  "type": "CLI | NOTION | MOBILE",
  "token": "<opaque signature>",
  "approved_at": "<ISO-8601 UTC>"
}
```

Approval records are stored as files in `06_trace/approvals/` named
`<trace_id>.approval.json`.

---

## Schema references

| Schema file | Governs |
|-------------|---------|
| `01_schema/trace_record.schema.json` | Merkle chain entries (canonical) |
| `01_schema/runtime_trace.schema.json` | Operational JSONL records |
| `01_schema/action_request.schema.json` | Action request sub-object |
| `01_schema/decision.schema.json` | Decision sub-object |

---

## Compliance failures and escalation

| Failure | Automatic response | Human required |
|---------|--------------------|---------------|
| Write-before-execute violated | DENY action, log operational WARN | No |
| Chain continuity broken | Halt kernel, emit CRITICAL trace | Yes |
| REQUIRE_HUMAN without proof | DENY action unconditionally | Yes (to unblock) |
| Rule-less DENY/REQUIRE_HUMAN | Flag as integrity violation | Yes |
| Dual-stream parity deficit | Log operational gap record | If persistent |
