# ACQ-EXEC-06 — Definitions of Outstanding B0 Review Findings

**Review status:** `CHANGES_REQUESTED`

**Previously addressed:** B0-F01 through B0-F04 are corrected at the static source-text level.

**Outstanding:** B0-R01, B0-R02 and B0-R03.

## B0-R01 — Companion document exceeds approved size limit

**Severity:** P1 — Contract compliance

**Location:** Artifact 2, `source_review_packet.md`

**Finding:**

The extracted UTF-8 document content was measured at **34,170 bytes**, exceeding the previously established maximum of **32,768 bytes** by **1,402 bytes**.

This limit applies to the companion document's intended payload, excluding presentation code fences.

**Required correction if separately authorized:**

Reduce the document to no more than 32,768 UTF-8 bytes without losing:

- Complete L00–L22 lifecycle coverage.
- B0-F01–F04 corrections.
- Q04/Q07/Q11/Q14 obligations.
- Global CAS and acknowledgment requirements.
- External dependencies and failure dispositions.
- Explicit authority restrictions and unresolved controls.

**Closure criteria:** Independently measured final document payload is within the approved byte limit and retains all mandatory substantive requirements.

## B0-R02 — Incorrect historical Master Gate verdict

**Severity:** P1 — Authority provenance

**Location:** Artifact 2, `source_review_packet.md`, authority and governing references section.

**Finding:**

The companion document states:

`ACQ-EXEC-06 R2's independent verdict was CHANGES_REQUESTED.`

That incorrectly describes the final R2 adjudication.

The accurate distinction is:

- **ACQ-EXEC-06 R1:** `CHANGES_REQUESTED`.
- **ACQ-EXEC-06 R2 final independent adjudication:** `READY_FOR_NARROW_HUMAN_DECISION`.
- **Scope of R2 final adjudication:** Eligibility for a separate, explicit human authorization of one inert conversational B0 drafting action only.

The R2 adjudication did not approve B1 persistence, Gate A preparation, Gate A execution or operational qualification.

**Required correction if separately authorized:**

Correct the historical disposition and distinguish the R1 rejection, R2's earlier blocked grant proposal, and R2's final narrowly scoped independent decision.

**Closure criteria:** The document accurately records the decision chronology and does not imply broader authorization or independent source acceptance.

## B0-R03 — Potential premature L01 execution-manifest requirement

**Severity:** P1 — Lifecycle contract accuracy

**Location:** Artifact 1, `qualification_authority.py`, `BindingClaim` and L01/L05 contract definitions.

**Finding:**

The revised `BindingClaim` makes these fields mandatory at object construction:

- `command_manifest_claim`
- `expected_cases_claim`

However, the accepted ACQ-EXEC-05 R2 lifecycle separates two authority boundaries:

**L01 — Preparation registration**

Requires an explicit human preparation grant, fresh attempt identity, accepted plan, gate and exact permitted preparation effects, followed by durable registration. Registration does not authorize execution.

**L05 — Execution authorization**

Requires a separate authenticated human execution grant binding the exact attempt, prepared packet, command, dependencies, cases and limits. No launch follows merely from this authorization.

Making execution-specific fields mandatory for an L01 registration proposal may inadvertently require execution-stage information before preparation is eligible to begin.

This is a **potential sequencing defect**, not yet a proven violation. An accepted read-only plan may identify intended commands or cases earlier without granting permission to execute them.

**Required correction or justification if separately authorized:**

Determine whether the two fields are actually required by an accepted governing authority at L01.

If they are not required, adjust the proposal model so L01 can represent a complete and valid preparation binding without requiring execution-only information prematurely.

At L05, require the separately authenticated execution grant and exact command/case/dependency binding. Preserve immutable identity linkage, external CAS and acknowledgment obligations.

If retaining the mandatory fields at L01, supply the precise accepted authority establishing that requirement and explain why it cannot improperly block preparation or imply premature execution authority.

**Closure criteria:** The model faithfully preserves the L01/L05 separation, while neither omitting required preparation identities nor allowing execution authorization to be inferred from advance manifest metadata.

## Authorization boundary

```ini
B0_F01_TO_F04=CORRECTED_IN_TEXT
B0_R01=OPEN
B0_R02=OPEN
B0_R03=OPEN_REQUIRES_JUSTIFICATION_OR_CORRECTION
B0_STATIC_REVIEW=CHANGES_REQUESTED
B0_NEW_REVISION_AUTHORIZED=NO
B0_EXACT_BYTES_FROZEN=NO
B1_PERSISTENCE=NOT_AUTHORIZED
SOURCE_EXECUTION=NOT_AUTHORIZED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

These definitions may be used for read-only assessment and a later human authorization decision. They do not permit source modification or another conversational revision.