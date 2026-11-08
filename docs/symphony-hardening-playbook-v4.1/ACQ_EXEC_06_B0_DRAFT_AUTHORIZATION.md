# ACQ-EXEC-06 — Human Authorization: B0 Inert Source Drafting Only

You are the existing Codex source author for Symphony ACQ-EXEC-06.

**HUMAN DECISION: APPROVED — ONE CONVERSATIONAL SOURCE-DRAFTING SUBMISSION ONLY.**

This is a new, narrowly scoped authorization following independent Master Gate R2 adjudication on 6 November 2026.

It supersedes ACQ-EXEC-06 R2's proposed B0 hexadecimal-transport and external durable-CAS admission prerequisites **for this text-only drafting action only**. It does not change the accepted Gate A R0 preparation contract or ACQ-EXEC-05 R2 qualification lifecycle.

## 1. Exact authority and baseline

```ini
REPOSITORY=JCSchoeman96/symphony
MAIN_SHA=4971ddde384ef54b06498db438d2bfe36a0f108a
MAIN_TREE=540617e1c62af1550059113c5166bea315cc6015
POST_MERGE_RUN=42196718923
POST_MERGE_RESULT=SUCCESS

ACQ_EXEC_06_R2_ORIGINAL_SHA256=fcdc7a6302c975fc239a81c30c0c8b359393254e49a0e90d9f62139936404269
ACQ_EXEC_05_R2_PLAN_BLOB=1fd0af3e23287bab8939876589abc064c5655b45

AUTHOR=CURRENT_CODEX_CONVERSATION
HUMAN_AUTHORITY=PROJECT_OWNER
B0_SCOPE=INERT_CONVERSATIONAL_SOURCE_DRAFT_ONLY
B1_PERSISTENCE=NOT_AUTHORIZED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

The independent adjudication established that ordinary inert source drafting can be authorized separately from operational Gate A qualification.

The historical source-writing precedent, Plane decision `c746cd5a-faaf-4e70-a1c6-7d9274a134bb`, supports this boundary but grants no present permission.

## 2. Exactly authorized action

Produce one conversational draft submission containing:

**Artifact 1 — `qualification_authority.py`**

A complete, statically reviewable, interface-only Python source draft for the proposed external qualification-authority component.

**Artifact 2 — `source_review_packet.md`**

A companion draft explaining the source interfaces, lifecycle mapping, external dependencies, assumptions, incomplete controls and review obligations.

The intended future paths remain:

```text
/tmp/symphony-gate-a-authority-candidate-r1/
  qualification_authority.py
  source_review_packet.md
```

These are identification labels only. **Do not create these paths or any other filesystem artifact.**

Deliver both complete draft texts directly in your existing Codex conversation. Use clear source labels and code comments.

Proposed upper content limits:

```ini
SOURCE_MAX_INTENDED_UTF8_BYTES=131072
REVIEW_DOCUMENT_MAX_INTENDED_UTF8_BYTES=32768
SUBMISSIONS_AUTHORIZED=1
```

Do not claim exact byte identities until a later separately controlled capture and independent measurement.

## 3. Required source contract

The source draft must implement definitions or fail-closed external interfaces for:

- **Q04:** Authenticated external identity, registration, durable denial and CAS.
- **Q07:** Qualification supervision, one-use launch entitlement consumption and independent transition control.
- **Q11:** Exact evidence binding, external durable retention and authenticated acknowledgments.
- **Q14:** Uncertainty, finite externally authorized stopping, retention and terminal behavior.

Preserve the accepted ACQ-EXEC-05 R2 **L00–L22** state machine without replacing it with the B0/B1 authoring lifecycle.

Every meaningful state and transition must have explicit guards, owners, permitted effects, adverse outcomes and terminal behavior.

Specifically:

- No caller-provided boolean or local UID assertion may become authenticated authority.
- No fabricated durable store, ACK, entitlement, acceptance or reviewer verdict.
- No permissive fallback when external dependencies are absent.
- No retry after ambiguous consumption or launch.
- No terminal-state reopening or same-attempt repair.
- No automatic execution, process launch, file creation or service startup.
- No claim that local refusal proves an externally durable denial.
- No claim that transport delivery proves persistence or authorization.
- No claim that source review proves L04, L12 or L13 acceptance.

Where an actual external owner, trust mechanism, store or operating-system profile is unresolved, make it an explicit dependency and prevent operational advancement.

All operational interfaces remain unqualified.

## 4. Strictly prohibited effects

This grant does not authorize:

- Writing, replacing or deleting files or directories.
- Creating source archives, fixtures, logs, helper programs or staging files.
- Running, importing, compiling, linting or testing the candidate.
- Executing Python or other code to generate or validate the candidate.
- Running shell commands to persist or operate the candidate.
- Starting services, supervisor processes or operational qualification controls.
- Inspecting credentials or performing privileged operations.
- Creating a branch, commit, PR or CI run.
- Changing GitHub, Plane or governing repository documents.
- Invoking another authoring agent.
- Performing Gate A preparation, Gate A execution, Gate B work or Gate 2 activation.

Existing read-only governing evidence may inform the draft; this does not grant additional workstation mutation or execution permissions.

Ordinary platform transcript retention is not represented as a zero-effect or independently durable store.

## 5. Submission and authorization lifetime

This grant applies only to the **next single complete drafting submission** in the current author conversation.

The grant is consumed when that submission begins. It expires after that response is delivered, interrupted or abandoned.

The author must not start a second submission or silently continue an incomplete one.

If the complete source and companion document cannot fit within the available response capacity, report `B0_DRAFT_INCOMPLETE` and describe the limitation. Do not create a partial file on disk or continue under the consumed grant.

The output is a draft, not a frozen byte artifact. Markdown code fences are presentation delimiters, not independently approved payload bytes.

No author-computed or guessed hash constitutes independent evidence.

A subsequent exact-byte capture, raw-file review, correction, or persistence requires its own applicable human decision.

## 6. Required source review packet

The companion document must include:

1. Complete L00–L22 implementation mapping.
2. Q04/Q07/Q11/Q14 coverage.
3. External interface and dependency register.
4. Exact distinctions between local refusal, external denial, CAS receipt, evidence ACK and human acceptance.
5. Failure and uncertainty disposition matrix.
6. Explicit unimplemented operational mechanisms.
7. Static review checklist and expected adversarial findings.
8. Statements of what was not executed, created, qualified or authorized.

Do not insert invented source SHA-256, post-persistence inode, B1 receipt or review acceptance.

## 7. Final outcome

Conclude the submission with:

```ini
B0_CONVERSATIONAL_DRAFT=SUBMITTED|INCOMPLETE|BLOCKED
B0_EXACT_BYTES_FROZEN=NO
B0_INDEPENDENT_SOURCE_REVIEW=NOT_PERFORMED
B1_FILESYSTEM_PERSISTENCE=NOT_AUTHORIZED
SOURCE_EXECUTION=NOT_AUTHORIZED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

Choose exactly one B0 draft outcome.

**Deliver the two inert texts, or report an exact blocker. No filesystem action, independent acceptance or operational qualification follows from this authorization.**