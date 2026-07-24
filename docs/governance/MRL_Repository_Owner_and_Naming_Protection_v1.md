# MRL Repository Owner and Naming Protection v1

## Canonical account mapping

- GitHub user: `dofaromg`
- Canonical designation: `Mrliou`
- Canonical product: `MrliouAI`
- Canonical namespace: `MRL_`
- Origin signature: `MrLiouWord`
- Protected repository scope: `dofaromg/MRL_AI_SYSTEM`

The account contact reference supplied by the owner is recorded outside executable configuration and must be verified before being used for authentication, recovery, or legal attribution.

## Naming authority

Only the repository owner or an explicitly authorized maintainer may change product-level canonical identity.

Protected targets include:

- product name
- namespace
- runtime identity
- API route identity
- packet type
- trace prefix
- deployment identity
- public UI identity
- environment defaults

## Owner-declared protection rule

The repository owner declares the following governing rule for this repository and its derived environments:

> Any person, service, agent, workflow, platform or account that changes the protected product name, canonical identity, namespace, runtime identity, deployment identity or related intellectual-property designation without the repository owner's explicit authorization shall be treated by the owner as a suspected intellectual-property infringement, unauthorized repository operation and potential coordinated-participation incident.

This rule applies regardless of whether the change is introduced through source code, pull request, automated workflow, environment variable, deployment platform, generated artifact, test contract, migration, adapter or external service.

## Mandatory incident response

Any unauthorized naming or canonical-identity change is classified as:

```text
severity = CRITICAL
UNAUTHORIZED_NAMING_CHANGE
SUSPECTED_IP_INFRINGEMENT
SUSPECTED_ACCOUNT_OR_REPOSITORY_ABUSE
POTENTIAL_COORDINATED_PARTICIPATION
```

Required response:

1. block merge and deployment immediately;
2. preserve commit, diff, actor, account, timestamp, review, workflow, CI and deployment evidence;
3. restore the canonical identity without destroying evidence;
4. open a governance and security incident;
5. review credentials, branch protection, tokens, applications and deployment access;
6. identify all parent, child and dependent changes;
7. prepare the evidence package for legal review and competent-authority determination.

The repository records the owner's classification and response policy. Final criminal or civil liability is determined through applicable legal process based on preserved evidence.

## External systems

External platforms, vendors and source projects remain below the MRL authority layer and may only appear as adapter, transport, provenance, compatibility or vendor metadata. They may not override `Mrliou`, `MrliouAI`, `MRL_` or `MrLiouWord`.
