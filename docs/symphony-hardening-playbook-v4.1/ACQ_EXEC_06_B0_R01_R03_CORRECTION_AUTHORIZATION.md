# ACQ-EXEC-06 — Explicit Human B0 Correction Grant

**HUMAN DECISION: APPROVED**

I explicitly authorize the existing Codex author to perform **one final conversational source-only correction submission**, limited to B0-R01, B0-R02 and B0-R03.

## 1. Exact approved input

The current revised B0 submission is identified by its independently measured text-export SHA-256:

`1814dd0068072453e02103a64d0549b300787807a089c4884e4073bb9ff09202`

The previous complete draft must remain unchanged.

B0-F01 through B0-F04 are corrected in text. Preserve those corrections.

## 2. Authorized corrections

**B0-R01 — Document size**

Reduce the intended `source_review_packet.md` UTF-8 payload to at most **32,768 bytes**.

Retain the complete L00–L22 mapping, Q04/Q07/Q11/Q14 requirements, global CAS/ACK obligations, dependencies, failure handling and authority restrictions.

Do not remove substantive requirements merely to meet the limit.

**B0-R02 — Historical verdict**

Correct the documented decision chronology:

- ACQ-EXEC-06 R1: `CHANGES_REQUESTED`.
- ACQ-EXEC-06 R2 final adjudication: `READY_FOR_NARROW_HUMAN_DECISION`.
- R2's final disposition applied only to a separately authorized conversational B0 drafting action.

No B1 or Gate A authorization follows.

**B0-R03 — L01/L05 sequencing**

Independently assess the accepted R2 authority for requiring `command_manifest_claim` and `expected_cases_claim` at L01.

Preserve the distinction:

- L01: Preparation grant, fresh identity, accepted plan, gate and exact preparation effects.
- L05: Separate authenticated execution grant binding the exact command, dependencies, cases and limits.

If the mandatory L01 fields introduce an unsupported prerequisite, correct the model.

If retained, provide the precise governing authority and distinguish planning metadata from execution authorization.

Do not weaken L05 or permit execution from an L01 binding.

## 3. Authorized output

Produce exactly one complete conversational submission containing:

1. Revised `qualification_authority.py`.
2. Revised `source_review_packet.md`.
3. Concise B0-R01–R03 correction and evidence summary.

Preserve the original L00–L22 transition relation and the existing fail-closed operational façade.

The source limit remains 131,072 UTF-8 bytes; the review-document limit remains 32,768 UTF-8 bytes.

Actual final byte identities remain subject to separately authorized capture and independent measurement.

## 4. Restrictions

No filesystem writes, candidate execution, imports, compilation, linting, tests, helper creation, other authoring agents, GitHub/Plane mutations, Gate A preparation or Gate A execution.

The grant is consumed by this single submission, interruption or abandonment. No automatic follow-up revision is permitted.

If the complete submission cannot be delivered within scope, report the exact blocker and stop.

## 5. Required status

```ini
B0_CORRECTION_GRANT=HUMAN_APPROVED
B0_CORRECTION_SCOPE=B0-R01_TO_B0-R03_ONLY
B0_REVISION_SUBMISSIONS_AUTHORIZED=1
B0_EXACT_BYTES_FROZEN=NO
B1_PERSISTENCE=NOT_AUTHORIZED
SOURCE_EXECUTION=NOT_AUTHORIZED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

Proceed only within this exact conversational correction grant. Return both complete revised artifacts for static review.