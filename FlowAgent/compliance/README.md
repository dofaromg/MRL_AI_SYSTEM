# MRL_AI_SYSTEM

## FlowAgent / MRL Compliance Layer v0.1

Goal: a deny-by-default guard + traceable audit log that aligns FlowAgent to AWS Acceptable Use Policy (AUP).

## Repository layout
- FlowAgent/
  - compliance/
    - schemas/
    - policies/
    - allowlist/
    - denylist/
    - traces/
    - approvals/

## Trace design (dual stream)
- Canonical: Merkle chain entry (MemoryEntry)
- Operational: runtime_trace_v1.jsonl

### Required metadata fields
- event_id
- rid
- tick
- persona_id
- action
- target
- decision (ALLOW/DENY/REQUIRE_HUMAN/REDACT)
- rule_hits
- merkle
- prev

## AUP rule pack (aws_aup_v1)
1) illegal_or_fraud: deny/require human for login/register/payment
2) rights_of_others: whitelist + PII/copyright gate for web fetch / file ingest
3) violence_terror_harm: content safety gate
4) child_exploitation: hard deny
5) security_integrity_availability: deny scan/probe/bruteforce
6) spam: require human + rate limit + consent

## Defaults
- allowlist: empty
- denylist: SCAN/PROBE/BRUTEFORCE
- approvals: required for any external action
- traces: jsonl with merkle reference
