# ACQ-EXEC-06 — Explicit Human B0 Correction Authorization

**HUMAN DECISION: APPROVED**

I explicitly authorize the existing Codex source author to perform **one conversational source-only revision** addressing B0-F01 through B0-F04.

The approved input is the previously submitted complete `ACQ_EXEC_06_B0_CONVERSATIONAL_DRAFT.md`, SHA-256:

`8082fc8a1b03408c2db1c867dbb8872ad1fd5377be725085768b3f09af203973`

**Authorized corrections:**

- **B0-F01:** Correct structural validation of L01 bindings and existing-attempt previous-transition identities.
- **B0-F02:** Explicitly model pre-attempt request/denial identities without fabricating authority.
- **B0-F03:** Model the global external CAS and durable acknowledgment requirements.
- **B0-F04:** Clarify adverse-transition classifications and distinguish lifecycle transitions from local refusals.

Preserve the accepted ACQ-EXEC-05 R2 L00–L22 lifecycle and all existing fail-closed requirements.

**Authorized deliverables:** One complete revised conversational submission containing `qualification_authority.py`, `source_review_packet.md`, and an explanation of the exact corrections.

**Strict exclusions:** No filesystem changes, Python execution, imports, compilation, linting, tests, helper creation, GitHub/Plane mutations, operational qualification or additional authoring agents.

This authorization permits only this single conversational revision. It is consumed upon submission, interruption or abandonment. Further corrections require a separate authorization.

```ini
B0_CORRECTION_GRANT=HUMAN_APPROVED
B0_CORRECTION_SCOPE=B0-F01_TO_B0-F04_ONLY
B0_REVISION_SUBMISSIONS_AUTHORIZED=1
B0_SOURCE_EXECUTION=NOT_AUTHORIZED
B0_EXACT_BYTES_FROZEN=NO
B1_PERSISTENCE=NOT_AUTHORIZED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

Proceed only within this exact conversational correction scope. Return both complete revised artifacts for independent review.