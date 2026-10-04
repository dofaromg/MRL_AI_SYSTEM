# PR149 runtime port and write security adaptation
origin_signature: MrLiouWord
canonical_base: e4f7a1ec43f30bd1820ec0d20b1203b0a203b9a8
source_commit: b07a7dec07d80700784d1cc8a78b545880bee6ab

Expected files: MRL_Platform_Server.py, MRL_RuntimeServer.js, deploy/dl580/MRL_dl580_start.sh, tests/MRL_pr149_runtime_test.py, this provenance record, .github/workflows/MRL_PR149_Runtime.yml (6).

Dependency tree: Node gateway -> existing express; Platform api_chat -> existing MotherAssembly; launcher -> existing bootstrap -> Node gateway. No source-branch runtime engine is imported.

Chat error dictionaries propagate ok:false. Base Express writes now require MRL_AUTH_REQUIRED=true plus a matching Bearer MRL_API_TOKEN, or explicit MRL_ALLOW_UNAUTHENTICATED_WRITES=true. Read routes remain accessible. Auth opt-in never overrides required authentication.

The base launcher does not start Python Platform, so the source's auto-increment hunk is inapplicable. MRL_RUNTIME_PORT explicitly selects the Node port while retaining the default port when absent. This does not start another service or alter an existing deployment.

pyproject.toml is absent in base and its source packaging targets mrliouword.cli, unrelated to these runtime repairs. The PEP517 repair is recorded as source-only/inapplicable, not silently copied; no packaging dependency is introduced.

Validation: Python unittest behavior matrix, Node syntax, Python compile, bash syntax, npm MRL_acceptance. No DL580 execution claimed.
