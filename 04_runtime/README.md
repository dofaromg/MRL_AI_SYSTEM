# 04_runtime

FlowAgent execution kernel (L7 LOOP layer).

## Files

| File | Purpose |
|------|---------|
| `flowcore_loop.py` | Main kernel loop — heartbeat, trace writing, Merkle chain commits |

## Runtime data

Operational data written to gitignored paths:
- `06_trace/traces/_data/runtime_trace.jsonl` — JSONL operational trace
- `03_memory/_data/memory_chain/` — Merkle chain entries + head pointer

## Loop cycle

`Observe → Resolve → Mirror → Project → Verify → Iterate`

## Running

```bash
python 04_runtime/flowcore_loop.py
```
