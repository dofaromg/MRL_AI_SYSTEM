# MRL_AI_SYSTEM

FlowAgent / MRL monorepo — compliance + trace + runtime + memory.

## Mother Core Assembly

The system is not a single file — it is a **Mother Core Assembly**: multiple
cores that together satisfy the formula:

```
MotherBody = MaxBoundary + MinPacket + ReversibleChain
```

Design principle: **怎麼過去，就怎麼回來** (the path forward is the path back).

### Six core groups

| # | Name | Role | Entry module |
|---|------|------|--------------|
| 1 | **MotherCore** | Origin signature, canonical law, FluidCore | `00_rootlaw/rootlaw.yaml` |
| 2 | **ParticleReversible** | Compression / expansion / rollback chain | `09_workflow/fltnz_parser.py` |
| 3 | **FlowAgentRuntime** | Persona, memory, language-field, CLI, containers | `04_runtime/flowcore_loop.py` |
| 4 | **WorldModule** | Particle globe, world state, trajectory | `05_persona/world_module.py` |
| 5 | **FileIndexGovernance** | T/X/Y/Z index, librarian, relation chain | `09_workflow/mrl_librarian.py` |
| 6 | **PersonaHistory** | System evolution, alignment, belief stabilisation | `ui/streamlit_app/app.py` |

## Directory structure

| Directory | Layer | Purpose |
|-----------|-------|---------|
| `00_rootlaw/` | L0 ROOT + L3 LAW | Immutable foundational invariants; supersede all other rules |
| `01_schema/` | L1 SEED | JSON Schema contracts for all data flowing through the system |
| `02_principles/` | L3 LAW | AUP-aligned guard rules and default policy settings |
| `03_memory/` | L6 REFLECT | Merkle chain (canonical) + vector store (semantic retrieval) |
| `04_runtime/` | L7 LOOP | FlowAgent kernel — heartbeat loop, trace writer, chain commits |
| `05_persona/` | L4 WORLD | Agent persona definitions, world module, and particle globe |
| `06_trace/` | L6 REFLECT | Dual-stream audit trail: canonical Merkle + operational JSONL |
| `07_ingest/` | L2 PARTICLE | Allowlists, denylists, and ingest source gates |
| `08_sources/` | L0 ROOT | Canonical source manifest (sealed spec mirror) |
| `09_workflow/` | L7 LOOP | Workflow DAGs, orchestration steps, librarian, .fltnz parser |
| `data/` | MetaEnv | Master summaries, module relation chain, librarian index |
| `ui/` | Platform | Streamlit dashboard |

## Key modules

### MRL core modules

| Module | Purpose |
|--------|---------|
| `09_workflow/mrl_librarian.py` | T/X/Y/Z indexed file librarian — rebuild with `python 09_workflow/mrl_librarian.py index` |
| `09_workflow/fltnz_parser.py` | Bidirectional txt↔fltnz↔map↔flpkg↔trace reversible chain parser |
| `05_persona/world_module.py` | World node / state / trajectory / particle-globe coordinate manager |
| `04_runtime/runtime_manifest.yaml` | TotalCore · Runtime · Container · CLI install & recovery spec |
| `data/relations/module_relations.yaml` | Canonical relation map linking all modules across core groups |
| `03_memory/merkle/memory_chain.py` | Append-only Merkle chain with `verify()` + `rollback()` |
| `09_workflow/api.js` | L0–L7 layer stack (Node.js, v1.3) |
| `09_workflow/signature.js` | LAW-0 signature law implementation |
| `09_workflow/seed.js` | SEED(X) compression pipeline |

### Industry-standard modules (新增)

| Module | Industry feature | MRL extension |
|--------|-----------------|---------------|
| `03_memory/vector/vector_store.py` | RAG — cosine-similarity vector store | entries stamped with origin_signature, sealable into MerkleChain |
| `09_workflow/tool_registry.py` | Tool / function calling | call records traceable to L7 trace format |
| `09_workflow/prompt_template.py` | Prompt template management | versioned templates persisted to `data/prompt_templates.json` |
| `09_workflow/agent_planner.py` | ReAct Plan→Act→Observe agent loop | trajectory steps compatible with WorldModule format |
| `09_workflow/eval_engine.py` | Output scoring / evaluation pipeline | safety scorer enforces L3 LAW deny-list |
| `09_workflow/plugin_manager.py` | Plugin discovery & lifecycle | plugins must declare TXYZ coordinates (layer + group) |

### MotherAssembly — 組合入口 (the combination)

| Module | Purpose |
|--------|---------|
| `09_workflow/mother_assembly.py` | **Unified system entry point** — boots and wires all 7 subsystems together. The combination (組合) is the system's biggest feature. |
| `09_workflow/plugins/` | Plugin directory — drop `*.py` files here following the plugin contract |

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
MetaEnv     variable environment: spawn / scale / snapshot / migrate
Platform    FluinHub / FlowCoreLoop / partner platforms / 3-D globe / AI chat
```

## Quick start

```bash
# 1. Build the librarian index (TXYZ coordinate map)
python 09_workflow/mrl_librarian.py index

# 2. Start the minimal runtime kernel
python 04_runtime/flowcore_loop.py

# 3. Encode a file into the reversible chain
python 09_workflow/fltnz_parser.py encode --src README.md --dst /tmp/readme.fltnz

# 4. Inspect world state
python 05_persona/world_module.py snap

# ── MotherAssembly (boots all 7 subsystems at once) ──────────────────────────

# 5. Boot and check status
python 09_workflow/mother_assembly.py boot
python 09_workflow/mother_assembly.py status

# 6. Run an agent task
python 09_workflow/mother_assembly.py run --goal "Summarise the repo structure"

# 7. Evaluate an output
python 09_workflow/mother_assembly.py eval \
    --output "The MRL system uses Merkle chains for immutable tracing." \
    --keywords "MRL,Merkle,tracing"

# 8. Seal text through the full reversible chain + MerkleChain
python 09_workflow/mother_assembly.py seal --text "Hello, MRL!" --label readme

# ── Individual industry modules ───────────────────────────────────────────────

# Vector store (RAG)
python 03_memory/vector/vector_store.py add --id doc1 --vec "0.1,0.9,0.3"
python 03_memory/vector/vector_store.py query --vec "0.1,0.8,0.3" --k 3

# Tool registry
python 09_workflow/tool_registry.py list
python 09_workflow/tool_registry.py call --tool add --args '{"a":3,"b":4}'

# Prompt templates
python 09_workflow/prompt_template.py add --id greet --text "Hello, {name}!"
python 09_workflow/prompt_template.py render --id greet --vars '{"name":"MRL"}'

# Agent planner demo
python 09_workflow/agent_planner.py demo

# Eval engine
python 09_workflow/eval_engine.py demo

# Plugin discovery
python 09_workflow/plugin_manager.py discover --dir 09_workflow/plugins
```

See `04_runtime/runtime_manifest.yaml` for the full install order and recovery protocol.
