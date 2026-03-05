# 09_workflow

Workflow and orchestration definitions for FlowAgent (L7 LOOP layer).

## Purpose

This directory holds workflow DAGs, step definitions, and orchestration configs that wire together the layers below:

```
08_sources → 07_ingest → 03_memory → 04_runtime → 06_trace
```

## Planned artifacts

- `workflows/` — named workflow YAML definitions
- `steps/` — reusable step primitives
- `triggers/` — event-based trigger configs

## Kernel loop cycle

`Observe → Resolve → Mirror → Project → Verify → Iterate`

Each iteration is a workflow run; every step is traced through `06_trace` before execution.
