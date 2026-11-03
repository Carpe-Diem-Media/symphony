# Gate 2 scanner governance addendum, 2026-11-03

## Decision and exact authority

This document persists the supplied Master Gate decision and its later acceptance
of the complete implementation plan. The decision is external human governance,
not an inference from a branch, PR, diagnostic trace or implementation result.
No separate decision identifier or exact decision timestamp was supplied; none is invented.

```ini
ORIGINAL_FREEZE_COMBINED_SHA256=1458bb041215c6268f2c69c01ed4198357e9561fbdc17a62e7288d0817b61911
SCANNER_AUTHORITY_STATUS=NO_PREEXISTING_ACCEPTED_AUTHORITY
SCANNER_SELECTION_REQUIRED=YES
SCANNER_GOVERNANCE_VERDICT=NEW_POLICY_SELECTED_BY_GOVERNANCE
FREEZE_EFFECT=AFFECTED_SCOPE_AMENDMENT
POLICY_ID=GATE2_V1_CANDIDATE_VALIDATION
POLICY_VERSION=1.0.0
POLICY_OWNER=TRUSTED_HOST_VALIDATOR
POLICY_SHA256=0d67fe1c0c532294dd3e946618d5bfd40c3d5ce6f50804e4bd20823ae5f756b7
SCANNER_EVIDENCE_SCHEMA=G2-SCAN-EVIDENCE-1.0.0
SCANNER_IMPLEMENTATION_ID=UNSELECTED
SCANNER_IMPLEMENTATION_AUTHORIZED=NO
NETWORK_AUTHORITY=NONE
CREDENTIAL_AUTHORITY=NONE
MUTATION_AUTHORITY=NONE
GENERIC_ARTIFACT_PROMOTION=DENIED
PROVIDER_PRIVATE_STATE_PROMOTION=DENIED
PROVIDER_PRIVATE_STATE_EXEMPTION=DENIED
IMPLEMENTATION_PLAN_APPROVED_BY_MASTER_GATE=YES
IMPLEMENTATION_AUTHORIZED=NO
```

The [policy JSON](GATE2_V1_CANDIDATE_VALIDATION_1.0.0.json) is the deterministic
policy representation. Hashing uses its exact UTF-8 bytes, recursively sorted keys, ASCII escapes,
comma/colon separators and no insignificant whitespace or final newline. The policy does not contain
its own digest. The [scoped projection](GATE2_SCANNER_GOVERNANCE_PROJECTION.json)
binds the policy, this addendum and the [canonical implementation plan](../superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md).

## Affected scope

This amendment supplies the previously unbound scanner policy for OB-015 and
OB-019, LC-09 and LC-10, the output safety validator/scanner, and ephemeral
candidate staging and safety validation. OB-016, OB-017 and OB-018 require
successful validation before publication authority can exist. Their semantics
are otherwise unchanged. No unrelated inventory row is reopened.

The immutable original packet remains
[GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json](GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json),
Git blob `6cf92dbad8507d4e6c7553392b163fcac02b897d`, 683322 bytes,
raw SHA-256 `a651b1574ec0a186f6b4cd9548787cf9b67009f6692268ce5a8d0669d9d0636a`.
Its embedded review marker and historical assertions remain untouched.

## Meaning of scanner-policy preservation

```ini
ORIGINAL_SCANNER_POLICY_REFERENCE_STATUS=UNBOUND
ORIGINAL_SCANNER_POLICY_CHANGED_ASSERTION=NOT_USABLE_AS_IMPLEMENTATION_AUTHORITY
SCANNER_POLICY_BASELINE_ESTABLISHED=YES
SCANNER_POLICY_BASELINE_ID=GATE2_V1_CANDIDATE_VALIDATION
SCANNER_POLICY_BASELINE_VERSION=1.0.0
```

The historical phrase "existing scanner and content checks" identified no accepted
executable, policy, digest or invocation contract. No `.scratch` material supplies
that missing authority. After this policy is merged and accepted, forward use of
`SCANNER_POLICY_CHANGED=NO` means no semantic change from the exact accepted
policy version and digest above. It does not rewrite the original packet.

Rules, exemptions, failure semantics, network or credential requirements, and
accepted object/content classes require a new policy version and governance
review when changed. Replacing an implementation without changing semantics
requires a new implementation identity/digest and fresh qualification evidence.

## Exact boundary and sequencing

This addendum does not pass Gate 2; authorize implementation, scanner implementation,
source publication, local Codex/provider execution or H-100; consume AUTH-07;
accept the diagnostic Gate 2 run or r4; change the selected reference topology;
or change human merge authority. A proposed implementation mechanism in the plan
is not a selected, installed or authorized scanner implementation.

The complete plan is approved at planning level and applies to protected-main
`c5b29a8417ae1d82db6e438716c1425ad6889761`, tree `792c0413b69a5ed4b2f40052c127bfc04f09a5af`. G00 persistence,
independent review, human merge, successor SHA/tree and policy/addendum blob/hash
verification, and explicit applicability rebinding must precede consideration of
any local implementation authorization. G00 is not complete merely because this
candidate document exists.

The separate V4.1 programme projection continues to report H-100 as
`AUTHORIZED_ACTIVE_NOT_ACCEPTED`. This task's `H100_EXECUTION_AUTHORIZED=NO`
neither revokes nor extends that programme decision.

## Documentation-only authority and preserved locks

This candidate is created under the supplied narrow G00 materialization authority:
worktree/branch, governance-document edits, local document and non-Codex governance
validation, commit, push and G00 PR creation. Required GitHub Actions CI for this
exact G00 PR alone may run its existing pinned Codex isolation proof. No local
Codex, inference, OAuth, scanner or Gate 2 execution is authorized.

```ini
GATE_2_STATUS=INCOMPLETE
IMPLEMENTATION_AUTHORIZED=NO
P01_IMPLEMENTATION_AUTHORIZED=NO
P06_IMPLEMENTATION_AUTHORIZED=NO
LOCAL_IMPLEMENTATION_AUTHORIZED=NO
LOCAL_FOCUSED_P01_TESTS_AUTHORIZED=NO
PROVIDER_EXECUTION_AUTHORIZED=NO
LOCAL_CODEX_EXECUTION_AUTHORIZED=NO
H100_EXECUTION_AUTHORIZED=NO
AUTH_07=SUSPENDED_UNCONSUMED
AUTH_07_CONSUMED=NO
G00_PR_REQUIRED_CI_CODEX_EXECUTION_AUTHORIZED=YES
G00_PR_REQUIRED_CI_CODEX_SCOPE=REQUIRED_GITHUB_ACTIONS_FOR_THIS_EXACT_G00_GOVERNANCE_DOCS_PR_ONLY
MERGE_AUTHORIZED=NO
```
