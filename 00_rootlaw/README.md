# 00_rootlaw

Foundational invariants for the MRL AI System (L0 ROOT + L3 LAW layer).

## Purpose

These rules are **immutable**. They supersede every other policy in the system and cannot be overridden at runtime. Extensions must be versioned amendments, never deletions.

## Key invariants

| ID | Rule |
|----|------|
| rl_00 | Deny-by-default — all external actions blocked unless explicitly allowed |
| rl_01 | No root deletion — canonical Merkle chain entries are never deleted |
| rl_02 | Human override required — REQUIRE_HUMAN actions wait for proof |
| rl_03 | Audit everything — every action writes to trace before execution |
| rl_04 | Mutual benefit — actions must be justified and reversible |
| rl_05 | No hidden instructions — all directives traceable to source |
| rl_06 | Child safety absolute — CSAM class hard-denied, no exceptions |

## Files

- `rootlaw.yaml` — canonical invariant definitions
