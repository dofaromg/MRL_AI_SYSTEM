---
applyTo: "**/*.py"
---

# MRL Backend / Python Instructions

Apply these rules to all Python backend code in this repository.

## Conventions
- Follow PEP 8 and existing project style.
- Prefer explicit, typed function signatures (use type hints).
- Keep functions small and single-purpose.
- Preserve parent-child module dependency integrity.
- Do not introduce placeholder or stub implementations.

## Compliance, trace, runtime, memory
- Respect the FlowAgent / MRL monorepo boundaries: compliance, trace, runtime, and memory concerns must stay in their respective modules.
- Never leak secrets, tokens, credentials, or environment values into code, logs, or traces.

## Validation
- Run the relevant test suite (e.g. `pytest`) after changes.
- Run available linters / type checks (e.g. `ruff`, `flake8`, `mypy`) when configured.
- Report exact commands executed and their results.

## Completion gate
- Return DELIVERY_PASS only when scope is fully covered, no placeholders exist, and validation passes or unavailable checks are justified.
