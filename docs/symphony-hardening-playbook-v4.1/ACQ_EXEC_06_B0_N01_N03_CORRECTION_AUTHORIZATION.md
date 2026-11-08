# ACQ-EXEC-06 — Explicit Human B0-N01–N03 Correction Authorization

**HUMAN DECISION: APPROVED**

I explicitly authorize the existing Codex author to perform **one conversational source-only correction submission**, limited to B0-N01, B0-N02 and B0-N03.

This approval is based on the fresh Independent Master Gate review, which returned `CHANGES_REQUESTED`.

## 1. Exact approved input

```ini
REPOSITORY=JCSchoeman96/symphony
INPUT_EXPORT_BYTES=77044
INPUT_EXPORT_SHA256=afe833789b46e045836b1372e4ac56a9dcfdb509bbcbacfbf143a7964b55f111
GOVERNING_R2_PLAN_BLOB=1fd0af3e23287bab8939876589abc064c5655b45

AUTHORIZED_AUTHOR=CURRENT_CODEX_CONVERSATION
CORRECTION_SCOPE=B0-N01_TO_B0-N03_ONLY
SUBMISSIONS_AUTHORIZED=1
```

Preserve the previous submission unchanged and retain all earlier B0-F01–F04 and B0-R01–R03 corrections.

## 2. Authorized corrections

### B0-N01 — Stage-specific sealed-artifact identities

Introduce structural requirements for:

- `preparation_packet_claim` at the applicable L03 sealing boundary and subsequent preparation-packet-dependent progression, including L04.
- `evidence_bundle_claim` at the applicable L10 sealing boundary and subsequent evidence-bundle-dependent progression, including L11–L14.

Preserve stage-aware behavior. Do not require sealed-artifact identities prematurely at L01, or block valid adverse transitions occurring before the relevant artifact exists.

Existing immutable bindings, independent verification, external CAS and durable ACK requirements must remain intact.

Local structural validation must never become operational authorization.

### B0-N02 — Evidence predecessor consistency

Define the first-record sequence and predecessor convention explicitly.

Require a valid predecessor identity for subsequent sequence claims and reject structurally inconsistent combinations.

Preserve independent verification of record contents, hash-chain continuity, authenticity and durability.

Do not introduce an operational evidence writer or acknowledgment producer.

### B0-N03 — Accepted §19 lifecycle obligations

Explicitly preserve:

- New attempt/run identities for any subsequent run.
- Fresh applicable preparation and execution grants.
- New output and evidence directories.
- Renewed guard checks and revalidation of previously retained immutable artifacts.
- Prohibition on recycling historical test outcomes as new execution evidence.
- The distinction between an authorized Gate B T18 child-process fault and interruption of the qualification runner, supervisor or required evidence.
- L18 for determinate incompleteness and L19 for ambiguous effects or observations.

These are source-contract definitions only. Do not implement Gate B fault injection or authorize any qualification execution.

## 3. Authorized deliverables

Produce **one complete conversational submission** containing:

1. Revised `qualification_authority.py`.
2. Revised `source_review_packet.md`.
3. A concise, exact explanation of the B0-N01–N03 corrections.

Preserve the accepted ACQ-EXEC-05 R2 L00–L22 lifecycle, the existing fail-closed operational façade and the earlier corrected findings.

The source must remain within 131,072 UTF-8 bytes. The companion review document must remain within 32,768 UTF-8 bytes.

## 4. Prohibited actions

No candidate filesystem writing, source execution, imports, compilation, linting, tests, helper creation, additional authoring agents, GitHub/Plane mutation, Gate A preparation, Gate A execution or Gate B execution.

This authorization is consumed by the single submission, interruption or abandonment.

No automatic continuation or supplementary revision is authorized.

If complete delivery is impossible, report the precise blocker and stop.

## 5. Required terminal status

```ini
B0_CORRECTION_GRANT=HUMAN_APPROVED
B0_CORRECTION_SCOPE=B0-N01_TO_B0-N03_ONLY
B0_REVISION_SUBMISSIONS_AUTHORIZED=1
B0_E01=EVIDENCE_PENDING
B0_E02=EVIDENCE_PENDING
B0_EXACT_BYTES_FROZEN=NO
B0_INDEPENDENT_SOURCE_ACCEPTANCE=NOT_GRANTED
B1_PERSISTENCE=NOT_AUTHORIZED
SOURCE_EXECUTION=NOT_AUTHORIZED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

Proceed only within this exact correction scope and return both complete revised artifacts for independent static review.