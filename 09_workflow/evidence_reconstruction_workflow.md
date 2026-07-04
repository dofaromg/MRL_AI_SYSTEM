# Evidence Reconstruction Workflow

Layer: L7 LOOP  
Method: 先查資料 → 確認檔案存在 → 逐一驗證 → 收斂閉環 → 再擴展

---

## Purpose

Defines the canonical DAG for reconstructing evidence from sources, confirming
file integrity, validating chain continuity, and closing each audit loop before
expanding to the next scope. Every step writes to both the Merkle chain
(`03_memory/_data/memory_chain/`) and the operational JSONL trace
(`06_trace/traces/_data/`) before proceeding.

---

## Workflow DAG

```
[START]
    │
    ▼
[S1] 先查資料 — Query sources
    │  • Read 08_sources/sources.manifest.yaml
    │  • List expected seed fingerprints from 03_memory/flowseed_origin/seed_index.json
    │  • Identify target layer(s) for reconstruction
    │
    ▼
[S2] 確認檔案存在 — Confirm file existence
    │  • Assert each source path listed in manifest is reachable (local or Dropbox ref)
    │  • Missing file → emit WARN trace, halt expansion, enter [LOOP_INCOMPLETE]
    │  • All present → emit OK trace, advance
    │
    ▼
[S3] 逐一驗證 — Verify each entry
    │  • For every seed entry in seed_index.json:
    │      - Recompute SHA-256 of content (if local) or compare stored fingerprint
    │      - Cross-check with merkle chain (MerkleChain.verify())
    │      - Decision: PASS | MISMATCH | MISSING
    │  • MISMATCH / MISSING → route to [S_REPAIR]
    │  • All PASS → advance to S4
    │
    ├──► [S_REPAIR] Repair loop
    │        • Log repair event to trace stream
    │        • Attempt re-ingest via 07_ingest allowlist
    │        • Re-run S3 for repaired entries
    │        • If repair fails after 1 retry → escalate (REQUIRE_HUMAN)
    │
    ▼
[S4] 收斂閉環 — Convergence & closure
    │  • Commit verified snapshot entry to Merkle chain (layer L0)
    │  • Write closure record to JSONL trace:
    │      {
    │        trace_id: "<uuid>", created_at: "<ISO-8601 UTC>",
    │        persona_id: "<id>", action_id: "<id>", action_type: "workflow_close",
    │        decision: "ALLOW", rule_hits: [],
    │        merkle_root: "<sha256>", merkle_prev: "<sha256>",
    │        event: "reconstruction_closed", scope, verified_count
    │      }
    │  • Update head pointer in 03_memory/_data/memory_chain/head.txt
    │  • Mark loop as CLOSED in workflow state
    │
    ▼
[S5] 再擴展 — Expand scope
    │  • Determine next scope (next layer, next source, or next run window)
    │  • If more scopes remain → return to [S1] with updated scope
    │  • If all scopes complete → advance to [END]
    │
    ▼
[END] — Emit final summary trace record
```

---

## Step definitions

### S1 — 先查資料 (Query sources)

| Field | Value |
|-------|-------|
| input | `08_sources/sources.manifest.yaml`, `03_memory/flowseed_origin/seed_index.json` |
| output | `source_list[]`, `expected_fingerprints{}` |
| trace_tag | `workflow:S1:query` |
| layer | L0 ROOT |

### S2 — 確認檔案存在 (Confirm existence)

| Field | Value |
|-------|-------|
| input | `source_list[]` |
| output | `presence_map{ id → found|missing }` |
| trace_tag | `workflow:S2:confirm` |
| layer | L7 LOOP |
| halt_condition | any `missing` entry |

### S3 — 逐一驗證 (Verify each entry)

| Field | Value |
|-------|-------|
| input | `presence_map`, `expected_fingerprints{}` |
| output | `verification_results[ { id, status, computed_sha256 } ]` |
| trace_tag | `workflow:S3:verify` |
| layer | L6 REFLECT |
| retry_limit | 1 (then REQUIRE_HUMAN) |

### S4 — 收斂閉環 (Convergence & closure)

| Field | Value |
|-------|-------|
| input | `verification_results[]` |
| output | committed `ChainEntry`, closure JSONL record |
| trace_tag | `workflow:S4:close` |
| layer | L6 REFLECT → L0 ROOT (chain commit) |
| invariant | must commit before any expansion |

### S5 — 再擴展 (Expand)

| Field | Value |
|-------|-------|
| input | remaining scope queue |
| output | next scope (or terminal) |
| trace_tag | `workflow:S5:expand` |
| layer | L7 LOOP |

---

## Invariants

1. **No expansion before closure** — S5 must not be entered until S4 commits successfully.
2. **Audit-first** — every step transition writes a trace record before the step action executes.
3. **Repair is bounded** — maximum 1 automatic repair attempt per entry; escalate to REQUIRE_HUMAN otherwise.
4. **Fingerprint authority** — `seed_index.json` is the single source of expected fingerprints; never derive them at runtime without recording the derivation.
5. **Chain continuity** — the Merkle `prev` of the closure entry must equal the chain `head` at the time S4 runs.

---

## Integration points

| System | Role |
|--------|------|
| `08_sources/sources.manifest.yaml` | Source enumeration (S1) |
| `03_memory/flowseed_origin/seed_index.json` | Expected fingerprints (S1, S3) |
| `03_memory/merkle/memory_chain.py` | Canonical chain commits (S3, S4) |
| `06_trace/traces/_data/` | Operational JSONL trace (all steps) |
| `07_ingest/allowlist/` | Re-ingest gate for repair (S_REPAIR) |
| `06_trace/approvals/` | REQUIRE_HUMAN proof storage (S_REPAIR escalation) |
