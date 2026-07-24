# MRL Change Control and Authorization Law v1

## Change classes

- `C0`: documentation clarification with no authority or runtime effect
- `C1`: implementation change within existing architecture
- `C2`: interface, environment or deployment change
- `C3`: canonical naming, ownership, architecture or authority change
- `C4`: destructive, history-rewriting or credential-control change

## Required authorization

`C3` and `C4` require explicit ROOT authorization. Automation, majority approval, platform defaults and maintainer convention are insufficient.

## Mandatory change record

Every controlled change must record:

- requested scope;
- expected file list;
- expected dependency tree;
- actor or automation identity;
- base branch and base commit;
- changed files;
- reason;
- validation commands or regression gates;
- migration and rollback path;
- synchronization targets;
- backup branch.

## Prohibited change methods

- silent direct replacement;
- deleting originals before recovery;
- using placeholders or manifests instead of actual files;
- mixing unrelated changes without disclosure;
- force-updating canonical branches without explicit authorization;
- altering tests to conceal unauthorized behavior;
- changing environment identity only in a deployment dashboard without repository synchronization.

## Completion gate

A change passes only when:

```text
Requested == Generated
Missing = 0
Unexpected = 0
Dependency integrity = PASS
Validation = PASS
Primary synchronization = PASS
Backup comparison = IDENTICAL
```
