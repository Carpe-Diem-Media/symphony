# ACQ-EXEC-06 — B1-R1 Planning Correction

**STATUS: PROPOSED — REQUIRES EXPLICIT PROJECT-OWNER APPROVAL**

## 1. Task

Correct the B1-R0 materialization authorization packet following the independent Master Gate review.

```ini
TASK=ACQ_EXEC_06_B1_R1_PLANNING_CORRECTION
INPUT_PACKET_BYTES=25416
INPUT_PACKET_SHA256=eb2d1597227814c4a29392a3843474bc0e83e1cea0255c60f5814fb73daa638e
MASTER_VERDICT=CHANGES_REQUESTED
B1_F01=OPEN
```

If explicitly approved, this grant permits one complete revised **conversational planning packet**.

No operational implementation, candidate materialization or filesystem writing is authorized.

## 2. Primary correction — B1-F01

Replace the incomplete lifecycle specification in §7 with an explicit, complete B1 lifecycle contract.

For every permitted transition, document:

- Transition identifier.
- Source state and destination state.
- Trigger and initiating actor.
- Independent decision and verification owner.
- Mandatory guards and prerequisite evidence.
- Exactly permitted effects.
- Required authenticated transition record and acknowledgment.
- Failure, interruption and ambiguity disposition.

Ensure that every nonterminal state has explicit permitted successors and every terminal state is absorbing.

Define the following behavior precisely:

1. Planning and review do not grant writing authority.
2. `PLAN_ACCEPTED_BLOCKED` cannot advance to `GRANT_ISSUED` until all mandatory pre-grant prerequisites are independently satisfied and the human issues an exact grant.
3. B1 writing entitlement consumption must be independently confirmed before any candidate creation.
4. That entitlement authorizes at most one bounded B1 materialization attempt containing two specified copy launches.
5. B1 entitlement is entirely separate from the Gate A L06 qualification-launch entitlement.
6. Forward transitions require confirmed previous-state, identity, authority and acknowledgment evidence.
7. Invalid authority, revocation, expiry, determinate failure and incomplete evidence deny further forward progress.
8. Ambiguity takes precedence wherever effects, custody, identity, consumption or acknowledgment become uncertain.
9. Late acknowledgments cannot restore eligibility.
10. Retained terminal observations or annotations cannot modify the terminal disposition, repair artifacts or authorize a retry.
11. Any subsequent attempt requires separate human authority and new attempt identity.
12. No unlisted transitions are permitted.

Clearly distinguish planning-level review dispositions from operational B1 attempt states.

Do not substitute the accepted Gate A L00–L22 lifecycle for the distinct B1 materialization lifecycle.

## 3. Preserve future grant blockers

Update the relevant sections of the packet to reflect the Master Gate review.

**Acknowledgment transport**

Require the future supervisor to specify how independently authenticated acknowledgments are received and validated before allowing the next effect.

The mechanism, descriptor configuration, authenticated receipt format, replay exclusions and durable evidence destination remain unresolved.

Do not invent an operational receipt mechanism.

**Synchronization**

Define the required sequence and responsibility for output synchronization, directory synchronization, metadata checks and failure handling.

The later grant must bind exact system-call or utility implementations and their dependencies.

Do not execute those operations.

**Writer and supervision**

Preserve the unresolved launcher, immutable dependency closure, principal appointment, isolation, complete effect inventory, finite stop policy and independent observation requirements.

Do not claim these prerequisites have been qualified merely because the planning contract now describes them.

## 4. Durability and retrieval

State explicitly that:

- `/tmp` staging is volatile and is not the durable archive.
- Disposable staging may be authorized only with explicit owner acceptance of volatility and independently established recoverability of required originals and evidence.
- If future retrieval depends on B1 outputs, the archive and handoff design must be accepted before staging becomes their only retained copy.
- Durable publication, archive transfer, independent retrieval verification, GitHub indexing and Plane recording remain separate authorization boundaries.

Preserve the proposed future evidence-index location, without creating it.

## 5. Preserve accepted B0 identities

```ini
B0_STATIC_SOURCE_VERDICT=ACCEPTABLE_FOR_EXACT_BYTE_FREEZE_REVIEW

EXPORT_BYTES=87753
EXPORT_SHA256=f5b780f402a66b0054dd38aa735d4b04cabb85bb067fb3a8f73095ccd947048f

SOURCE_BYTES=59880
SOURCE_SHA256=d1db9f46646fcb1b1789e6f77599fe0c0d849a10689ba117a08d91611014ae91

COMPANION_BYTES=26302
COMPANION_SHA256=e1d8e30d2996e172ad957774dd237a1e45ae305369d8c12f19c08989bede6f35
```

The independently reported export offsets are:

- Source: zero-based `[1089, 60969)`.
- Companion: zero-based `[61025, 87327)`.

These observations belong to the independent reviewer's runtime. Do not claim they establish writer-runtime custody.

## 6. Restrictions

Do not create or modify source files, candidate files, directories, scripts, fixtures, archives, GitHub or Plane records.

Do not execute, import, compile, lint or test the reviewed B0 source.

Do not perform a trial copy, qualify a launcher, prepare Gate A, execute Gate A or activate Gate B.

The original B1-R0 packet and B0 artifacts must remain unchanged.

## 7. Deliverables

Produce one complete revised **B1-R1 materialization authorization packet** and an updated unresolved-requirements register.

Explain precisely how B1-F01 was addressed and how the three additional grant-readiness concerns were preserved.

The new packet requires a new exact byte identity and independent Master Gate review.

```ini
B1_R1_CORRECTION_GRANT=NOT_YET_ISSUED
B1_F01=PENDING_INDEPENDENT_REVIEW
B1_MATERIALIZATION_GRANT=NOT_ISSUED
B0_EXACT_BYTES_FROZEN=NO
B1_PERSISTENCE=NOT_AUTHORIZED
DURABLE_ARCHIVE=NOT_ESTABLISHED
GITHUB_PLANE_EVIDENCE_INDEX=NOT_PUBLISHED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

Stop after the complete conversational submission. No automatic continuation is authorized.