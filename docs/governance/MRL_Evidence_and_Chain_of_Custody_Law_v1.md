# MRL Evidence and Chain of Custody Law v1

## Governing principle

```text
Evidence > Memory
```

No claim of ownership, completion, synchronization, deployment, recovery or incident attribution may rely on memory or narrative alone.

## Required evidence fields

Every evidence record must preserve, where available:

- repository and branch;
- commit SHA and parent SHA;
- tree SHA;
- author, committer, actor and application identity;
- timestamp;
- file path;
- complete diff or patch;
- file size;
- SHA-256 for exported artifacts;
- CI and workflow result;
- deployment result;
- environment delta;
- dependency impact;
- restore commit;
- reviewer and approval records.

## Chain-of-custody requirements

1. preserve the original before remediation;
2. never overwrite the sole evidence copy;
3. record every transfer, export and transformation;
4. hash exported evidence packages;
5. separate observed fact from inference;
6. retain source paths and provenance;
7. keep parent and child dependency links;
8. record missing or unavailable evidence explicitly.

## Evidence integrity prohibitions

- no placeholder evidence;
- no manifest-only substitution;
- no selective diff omission;
- no silent timestamp rewriting;
- no deletion of conflicting records;
- no claim of legal attribution without supporting evidence.

## Incident package completion

An evidence package is complete only when the file list, hashes, sizes, dependency tree and package map agree with the manifest and requested scope.
