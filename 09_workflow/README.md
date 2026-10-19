# Fluin Memory System & MRLIOU ASI MVP (09_workflow)

CLI-based memory recording and .flpkg builder for particle language, plus the
MRLIOU ASI MVP L0-L7 layer stack.

## MRLIOU ASI MVP — `api.js`

Node.js implementation of the full L0-L7 layer stack (version 1.3, sealed 2026-02-15).

| Layer | Class / Object | Responsibility |
|-------|---------------|----------------|
| L0 ROOT     | `L0` (frozen)   | Canonical signature `MrLiouWord`, canon `HCRA` |
| L1 SEED     | `L1`            | `exec(task, payload)` — exec gateway + log |
| L2 PARTICLE | `L2`            | `map(entry)` → `{ intent, payload, context_ok }` |
| L3 LAW      | `L3`            | Ring buffer with configurable limit (default 32) |
| L4 WORLD    | `L4`            | `write(k, v)` + `snapshot()` key-value store |
| L5 MIRROR   | `L5`            | `branch(item, side)` → α (trusted) / β (divergent) |
| L6 REFLECT  | `L6`            | `choose(decision, world_state)` with world hash |
| L7 LOOP     | `L7`            | `pack(trace)` → `{ leaf, root }`; `fold(items)` |

`MRLiouASI` is the unified runtime that wires all layers into a single `step(task, payload)` call executing the HCRA loop:

```
Observe (L1) → Resolve (L2) → Mirror (L3 + L5) → Verify (L6) → Loop (L7)
```

## LAW-0 Signature — `signature.js`

Implements the LAW-0 formula `T(e) = e'  ⟹  signature(e) = signature(e')`.

| Function | Purpose |
|----------|---------|
| `embedSignature(obj, sig?)` | Attach `_signature` + `_sig_hash` to a copy of `obj` |
| `extractSignature(obj)` | Read `{ signature, sig_hash }` from a signed object |
| `verifySignature(obj, expectedSig?)` | Re-hash and confirm the embedded signature |

## SEED(X) Compression — `seed.js`

Implements `SEED(X) = STORE(RECURSE(FLOW(MARK(STRUCTURE(X)))))`.

| Function | Pipeline step |
|----------|--------------|
| `structure(x)` | STRUCTURE — skeleton extraction |
| `mark(s)` | MARK — SHA-256 hash at every node |
| `flow(m)` | FLOW — flatten to token sequence |
| `recurse(f)` | RECURSE — back-reference duplicate hashes |
| `store(r, rootHash)` | STORE — produce `flpkg.seed` envelope |
| `seedCompress(x)` | Full pipeline in one call |
| `amplify(P_k, N_k, eta_k)` | `P_{k+1} = N_k · P_k · η_k` |
| `reverseProject(P0, N_seed, eta_seed)` | `δP₀ = P₀ / (N_seed · η_seed)` |

## .fltnz Reversible Chain Parser — `fltnz_parser.py`

Bidirectional txt ↔ fltnz ↔ map ↔ flpkg ↔ trace chain.
Design principle: 怎麼過去，就怎麼回來.

| Command | Purpose |
|---------|---------|
| `encode --src <file> --dst <out.fltnz>` | Tokenise text into a .fltnz envelope |
| `decode --src <in.fltnz> --dst <out.txt>` | Reconstruct original text from .fltnz |
| `verify --src <in.fltnz>` | Check checksum integrity |
| `pack   --src <in.fltnz> --dst <out.flpkg>` | Seal .fltnz into a .flpkg bundle |
| `unpack --src <in.flpkg> --dst <out.fltnz>` | Extract .fltnz from a .flpkg bundle |

```bash
python 09_workflow/fltnz_parser.py encode --src README.md --dst /tmp/readme.fltnz
python 09_workflow/fltnz_parser.py verify --src /tmp/readme.fltnz
python 09_workflow/fltnz_parser.py decode --src /tmp/readme.fltnz --dst /tmp/readme_out.txt
```

## MRL Librarian — `mrl_librarian.py`

T/X/Y/Z four-dimensional file index worker. Entry point for FileIndexGovernance (core group 5).

| Dimension | Meaning | Values |
|-----------|---------|--------|
| T | Temporal state | `principle` · `spec` · `prototype` · `runnable` · `entry` |
| X | Layer | `L0`–`L7` · `MetaEnv` · `Platform` |
| Y | Core group | `1`=MotherCore … `6`=PersonaHistory |
| Z | Relation depth | `0`=standalone · `1`=linked · `2`=hub |

```bash
python 09_workflow/mrl_librarian.py index              # rebuild index
python 09_workflow/mrl_librarian.py search --layer L3  # filter by layer
python 09_workflow/mrl_librarian.py search --group 3   # filter by core group
python 09_workflow/mrl_librarian.py search --state runnable
python 09_workflow/mrl_librarian.py query  --path 03_memory/merkle/memory_chain.py
```

## BlackHole Daily Distiller — `MRL_BlackHole_DailyDistiller_v1.py`

Daily read-only discovery of recently created, popular public GitHub repositories.
The report records source URLs, repository metadata, README headings, and a README
SHA-256; it does not import or execute external code. Integration candidates
remain `PENDING_HUMAN_REVIEW` and cannot be activated by this module.

```bash
python 09_workflow/MRL_BlackHole_DailyDistiller_v1.py \
  --since-days 7 --limit 20 --output /tmp/MRL_BlackHole_DailyDistillation.json
```

`.github/workflows/MRL_BlackHole_DailyDistiller.yml` runs this daily and uploads
the report as a workflow artifact. This is an engineering mirror output, not
proof of DL580 persistence or real-device runtime.

## Fluin memory CLI

| Script | Purpose |
|--------|---------|
| `record.py` | Record a user utterance to `logs/flmem.log` |
| `analyze.py` | Analyse recorded entries with `FluinAnalyzer` |
| `build.py` | Package entries into a `.flpkg` memory bundle |
| `FluinRecorder.py` | `record_input()` helper |
| `FluinAnalyzer.py` | `analyze_entry()` helper |
| `FluinMemoryVault.py` | `build_memory()` helper |
