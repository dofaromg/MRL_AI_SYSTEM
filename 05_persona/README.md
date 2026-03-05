# 05_persona

Persona definitions for FlowAgent agents (L4 WORLD / L5 MIRROR layer).

## Purpose

Each persona defines an agent's identity, capability scope, and behavioural constraints. Personas are referenced by `persona_id` in every trace record and compliance decision.

## Planned fields (per persona file)

```yaml
id: <persona_id>
name: <human-readable name>
layer: L4
capabilities: []        # allowed action types
constraints: []         # extra rules beyond rootlaw
world: AI | Platform | Real
```

## Status

Persona definitions are in progress. See `00_rootlaw/rootlaw.yaml` for invariants that apply to all personas.
