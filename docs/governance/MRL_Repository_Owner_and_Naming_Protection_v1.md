# MRL Repository Owner and Naming Protection v1

## Canonical account mapping

- GitHub user: `dofaromg`
- Canonical designation: `Mrliou`
- Canonical product: `MrliouAI`
- Canonical namespace: `MRL_`
- Origin signature: `MrLiouWord`
- Protected repository scope: `dofaromg/MRL_AI_SYSTEM`
- Canonical primary branch: `MrliouAI`

## Naming authority

Only the repository owner or an explicitly authorized maintainer may change product-level canonical identity.

Protected targets include product name, namespace, runtime identity, API route identity, packet type, trace prefix, deployment identity, public UI identity, environment defaults, governance registries and branch authority.

## Owner-declared protection rule

The repository owner declares:

> Any person, service, agent, workflow, platform or account that changes the protected product name, canonical identity, namespace, runtime identity, deployment identity, branch authority or related intellectual-property designation without the repository owner's explicit authorization shall be treated by the owner as a suspected intellectual-property infringement, unauthorized repository operation and potential coordinated-participation incident.

This rule applies whether the change is introduced through source code, pull request, automated workflow, environment variable, deployment platform, generated artifact, test contract, migration, adapter, mirror or external service.

## Mandatory classification

```text
severity = CRITICAL
UNAUTHORIZED_NAMING_CHANGE
SUSPECTED_IP_INFRINGEMENT
SUSPECTED_ACCOUNT_OR_REPOSITORY_ABUSE
POTENTIAL_COORDINATED_PARTICIPATION
SUSPECTED_AUTHORITY_SUBSTITUTION
SUSPECTED_ENVIRONMENT_IDENTITY_DRIFT
```

## Mandatory incident response

1. block merge and deployment immediately;
2. preserve commit, tree, parent, diff, actor, account, timestamp, review, workflow, CI and deployment evidence;
3. restore canonical identity without destroying evidence;
4. open governance and security incidents;
5. review credentials, branch protection, tokens, applications and deployment access;
6. identify all parent, child and dependent changes;
7. inspect all affected branches, mirrors and environments;
8. prepare the evidence package for legal review and competent-authority determination.

## Governing chain

This policy is subordinate only to explicit ROOT instruction and must be read with:

- `GOVERNANCE.md`
- `MRL_Constitution_v1.md`
- `MRL_Root_Authority_and_Intellectual_Property_Protection_Treaty_v1.md`
- `MRL_Naming_Authority_Law_v1.md`
- `MRL_Evidence_and_Chain_of_Custody_Law_v1.md`
- `MRL_External_Platform_Quarantine_Law_v1.md`

## Legal process

The repository records the owner's classification, protection rule and mandatory response policy. Final criminal or civil liability is determined through applicable legal process based on preserved evidence.

## External systems

External platforms, vendors and source projects remain below the MRL authority layer and may only appear as adapter, transport, provenance, compatibility or vendor metadata. They may not override `Mrliou`, `MrliouAI`, `MRL_` or `MrLiouWord`.
