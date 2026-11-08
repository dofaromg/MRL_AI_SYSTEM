---
applyTo: "**/tests/**"
---

# MRL Test Instructions

Apply these rules to all test code in this repository.

## Principles
- Tests must verify real behavior, not implementation trivia.
- Prefer small, deterministic tests.
- Do not weaken assertions to make a suite pass.
- Do not skip or delete failing tests to force a green build; if a test is obsolete, explain why.
- Use existing project test conventions and fixtures.

## Coverage
- Add unit, integration, or end-to-end tests to close coverage gaps for the requested scope.
- For Python, prefer `pytest` conventions.

## Reporting
- List test files created or modified.
- Explain what behavior each test covers.
- Run relevant test commands and report failures honestly.
- Produce an MRL coverage table: Requested behavior | Test coverage | Missing tests | Risk | Status
