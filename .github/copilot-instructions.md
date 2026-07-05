# MRL Repository Operating Rules

This repository follows MRL_AuditSupervisor_v1 delivery discipline.

## Non-negotiable rules

- Never silently reduce scope.
- Never replace real implementation with a manifest, placeholder, stub, fake file, or empty file.
- Never claim completion before validation.
- Never rename requested files to avoid implementing their required content.
- Never modify unrelated areas unless required by dependency integrity.
- Never remove tests to make a task pass.
- Never expose secrets, tokens, credentials, private keys, or environment values.

## Required execution flow

Before implementation:
1. Capture the requested scope.
2. List expected files.
3. List expected dependency relationships.
4. Identify acceptance criteria.
5. Identify validation commands.

During implementation:
1. Keep changes minimal and scoped.
2. Preserve parent-child dependency integrity.
3. Update tests when behavior changes.
4. Update documentation when public behavior changes.

Before final response or PR:
1. Compare Requested vs Generated.
2. Report Missing, Extra, Mismatch, and Coverage.
3. Run available tests, linters, type checks, and build commands.
4. Report commands executed and results.
5. If validation cannot be run, state exactly why.

## Completion gate

A task is complete only if:
- Missing files = 0
- Empty files = 0
- Placeholder files = 0
- Required dependency chain is present
- Tests/build/linters pass or failures are clearly documented
- Coverage against requested scope is 100%

If any condition fails, mark the result as DELIVERY_FAIL, not DELIVERY_PASS.
