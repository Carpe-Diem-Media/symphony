ACQ-EXEC-06 — B1-R2 Narrow Planning Correction

STATUS: PROPOSED — REQUIRES EXPLICIT PROJECT-OWNER APPROVAL

Authority and scope

TASK=ACQ_EXEC_06_B1_R2_PLANNING_CORRECTION
PREDECESSOR=B1-R1
PREDECESSOR_BYTES=42557
PREDECESSOR_SHA256=1a8fe95ee1b6e2b90c36d7a0fbe91243fe61f4641c90f7b48615222cd52fb57e
PREDECESSOR_MASTER_VERDICT=CHANGES_REQUESTED
B1_AUTH01=RESOLVED
CORRECTION_SCOPE=B1_R1_N01_AND_B1_R1_N02_ONLY
AUTHORIZED_SUBMISSIONS_IF_APPROVED=1

Continue as the existing ACQ-EXEC-06 B1 Planning Agent.

Produce one complete revised B1-R2 conversational planning packet. Retain R0, R1 and all accepted B0 artifacts unchanged.

Correction 1 — B1-R1-N01

Complete the planning-case initialization contract.

Define the independently established prerequisite for entering "P0 = PLANNING_AUTHORIZED", including:

- Fresh unique planning-case identity and namespace.
- Reference to the exact human planning authorization.
- Reference to the terminal predecessor review case and its disposition.
- Absence or unique-registration guard preventing duplicate, reused or conflicting identities.
- Responsible initiation actor and independent verification owner.
- Initial durable state record, exact evidence binding and authenticated acknowledgment requirements.
- Explicit prohibition of reopening R0 or R1, or treating their findings as a continuation of the same terminal case.

A normative external-initialization prerequisite is sufficient. Do not invent a registry, implementation or a thirteenth normal lifecycle transition.

Ensure subsequent transitions cannot use an unregistered or unacknowledged initial case.

Correction 2 — B1-R1-N02

Make "B1-T12" and "B1-F-O4" guards unambiguously disjoint.

Reserve "B1-T12: O4 → B1_REVIEW_REJECTED" for a complete, authenticated independent review that produces a determinate negative artifact-verification decision.

An independently established content, ownership, permission or byte mismatch in an otherwise complete review belongs to this disposition.

Reserve "B1-F-O4: O4 → FAILED" for a determinate failure of the review procedure, tooling, required dependencies or independent controls, where the review cannot validly complete.

Preserve "B1-U-O4 → UNCERTAIN" whenever effects, state, custody, observations or acknowledgment status become ambiguous.

Explicitly establish classification precedence and prohibit selecting two terminal outcomes for the same confirmed event.

Retain every observed finding even when only one terminal disposition is permitted.

Preserve the accepted lifecycle work

Retain the existing 12 normal/review transitions, 54 adverse transitions, actors, guards, authenticated-record requirements, one-use B1 entitlement, stopping policy, terminal absorption and separate Gate A L06 authority.

Do not broaden the correction into a new lifecycle architecture.

Preserve outstanding writing-grant prerequisites

All receiving-runtime custody, principal, launcher, dependency, isolation, acknowledgment-transport, synchronization, stopping, volatility and recoverability requirements remain unresolved until independently established.

Do not claim they have been satisfied through this planning correction.

Restrictions

This action, if approved, permits conversational planning only.

Do not create or modify source files, staging objects, scripts, helpers, fixtures, logs, archives, GitHub or Plane records.

Do not import, compile, lint, test or execute any B0 source.

Do not materialize B1 artifacts or perform Gate A/B operations.

Do not consume AUTH_07.

Deliverables

Return the complete B1-R2 packet and the updated unresolved-requirements register, identifying exactly how N01 and N02 were corrected.

The new R2 packet needs fresh independent byte measurement and Master Gate review.

B1_R2_CORRECTION_GRANT=REQUIRES_EXPLICIT_HUMAN_APPROVAL
B1_R1_N01=PENDING_INDEPENDENT_REVIEW
B1_R1_N02=PENDING_INDEPENDENT_REVIEW
B1_F01=OPEN_UNTIL_MASTER_CLOSURE
B1_MATERIALIZATION_GRANT=NOT_ISSUED
B0_EXACT_BYTES_FROZEN=NO
B1_PERSISTENCE=NOT_AUTHORIZED
DURABLE_ARCHIVE=NOT_ESTABLISHED
GITHUB_PLANE_EVIDENCE_INDEX=NOT_PUBLISHED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED

Stop after one complete submission. No automatic revision or progression is permitted.