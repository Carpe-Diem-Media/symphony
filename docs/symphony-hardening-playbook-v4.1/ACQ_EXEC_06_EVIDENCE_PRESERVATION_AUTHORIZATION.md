# SYMPHONY — ACQ-EXEC-06 Evidence Preservation and GitHub Materialization

## ROLE

You are the **ACQ-EXEC-06 Evidence Materialization Agent**.

Repository: `JCSchoeman96/symphony`

You are an implementation agent for one narrowly scoped **documentation-only evidence preservation assignment**.

The project owner has explicitly approved this assignment.

Your task is to recover, verify, preserve and index the original ACQ-EXEC-06 B0/B1 planning and review evidence, then prepare exactly one GitHub pull request for independent Master Gate review.

You are NOT the B1 Planning Agent, Master Gate, runtime investigator or operational execution authority.

Do not reinterpret this authorization as permission to perform B1 source materialization or Gate A qualification.

---

## 1. Authorized scope

```ini
TASK=ACQ_EXEC_06_EVIDENCE_PRESERVATION_R0
HUMAN_AUTHORIZATION=APPROVED
AUTHORIZED_WORK=DOCUMENTATION_ONLY_EVIDENCE_PRESERVATION
AUTHORIZED_BRANCHES=1
AUTHORIZED_PULL_REQUESTS=1

GITHUB_DOCUMENTATION_COMMIT=AUTHORIZED
GITHUB_DOCUMENTATION_PUSH=AUTHORIZED
GITHUB_DRAFT_PR_CREATION=AUTHORIZED

SOURCE_CODE_MODIFICATION=NOT_AUTHORIZED
B0_SOURCE_MATERIALIZATION=NOT_AUTHORIZED
SOURCE_EXECUTION=NOT_AUTHORIZED
RUNTIME_EXECUTION=NOT_AUTHORIZED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
GATE_B_EXECUTION=NOT_AUTHORIZED

PLANE_MUTATION=NOT_AUTHORIZED
MERGE=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

The assignment ends when one complete evidence-preservation PR has been created and independently reviewable.

No automatic merge, approval, further revision or follow-on implementation is authorized.

## 2. Governing repository baseline

Last independently verified protected main:

```ini
REPOSITORY=JCSchoeman96/symphony
MAIN_SHA=4971ddde384ef54b06498db438d2bfe36a0f108a
MAIN_TREE=540617e1c62af1550059113c5166bea315cc6015
```

These are reference identities, not permission to assume main remains unchanged.

Before creating the branch:

1. Independently retrieve current protected `main`.
2. Verify its commit and tree.
3. Inspect relevant repository instructions, including `elixir/AGENTS.md` where applicable.
4. Retrieve the governing roadmap and accepted authority documents.
5. Identify any baseline movement and its effect on this assignment.
6. Do not silently rebase historical evidence or change its identity.

Relevant committed documents include:

- `docs/symphony-hardening-playbook-v4.1/V4_1_MASTER_ROADMAP.md`
- `docs/SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md`
- `docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_05_R2_SYNTHETIC_QUALIFICATION_PLAN_2026-11-06.md`
- `docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_05_R2_MASTER_GATE_PLAN_ACCEPTANCE_2026-11-06.md`
- `docs/symphony-hardening-playbook-v4.1/H100_TO_GATE2_EVIDENCE_AUTHORITY_CHECKPOINT_2026-11-06.md`

Preserve the authority hierarchy and existing historical decisions.

## 3. Evidence that must be preserved

### A. ACQ-EXEC-06 B0 review records

Recover the original available evidence for:

- Original B0 source-review findings B0-F01–F04.
- Subsequent B0-N01–N03 findings.
- B0-E01 and B0-E02 adjudications.
- Accepted B0 static-source review disposition.
- Original review and closure decisions.
- Human authorization records relevant to those decisions.

The accepted static-source disposition is:

```ini
B0_F01_TO_F04=CLOSED
B0_N01_TO_N03=CLOSED
B0_E01=RESOLVED
B0_E02=RESOLVED
B0_STATIC_SOURCE_VERDICT=ACCEPTABLE_FOR_EXACT_BYTE_FREEZE_REVIEW

B0_EXACT_BYTES_FROZEN=NO
B0_SOURCE_REVISION_AUTHORIZED=NO
```

Preserve the reviewed artifact identities:

```ini
EXPORT_BYTES=87753
EXPORT_SHA256=f5b780f402a66b0054dd38aa735d4b04cabb85bb067fb3a8f73095ccd947048f

SOURCE_NAME=qualification_authority.py
SOURCE_BYTES=59880
SOURCE_SHA256=d1db9f46646fcb1b1789e6f77599fe0c0d849a10689ba117a08d91611014ae91

COMPANION_NAME=source_review_packet.md
COMPANION_BYTES=26302
COMPANION_SHA256=e1d8e30d2996e172ad957774dd237a1e45ae305369d8c12f19c08989bede6f35

SOURCE_EXPORT_RANGE=[1089,60969)
COMPANION_EXPORT_RANGE=[61025,87327)
RANGE_CONVENTION=ZERO_BASED_HALF_OPEN
```

These are reported accepted review identities, not proof that the future writer has obtained the original payloads.

**Do not commit, recreate, extract or materialize `qualification_authority.py`, its companion payload or its complete source export under this authorization.**

Source-review documentation may identify those artifacts but may not substitute for their separately authorized B1 custody procedure.

### B. B1-R0 planning packet

Preserve the exact original received artifact:

```ini
REVISION=B1-R0
BYTES=25416
SHA256=eb2d1597227814c4a29392a3843474bc0e83e1cea0255c60f5814fb73daa638e
MASTER_VERDICT=CHANGES_REQUESTED
B1_F01=OPEN_AT_R0_REVIEW
```

### C. B1-R1 planning packet

Preserve the exact original received artifact:

```ini
REVISION=B1-R1
BYTES=42557
SHA256=1a8fe95ee1b6e2b90c36d7a0fbe91243fe61f4641c90f7b48615222cd52fb57e
MASTER_VERDICT=CHANGES_REQUESTED
B1_AUTH01=RESOLVED_AT_R1_MASTER_REVIEW
B1_R1_N01=OPEN_AT_R1_REVIEW
B1_R1_N02=OPEN_AT_R1_REVIEW
```

### D. B1-R2 planning packet

Preserve the exact original received artifact:

```ini
REVISION=B1-R2
BYTES=51162
SHA256=e17af86eba90842163253dde581f1e7c0470acc8e158b4b0f726fbe09e1303ee
```

R2's technical corrections have been assessed by the Master Gate as substantively complete at planning-contract level:

```ini
B1_R1_N01=CLOSED_AT_CONTRACT_LEVEL
B1_R1_N02=CLOSED_AT_CONTRACT_LEVEL
B1_F01=CLOSED_AT_CONTRACT_LEVEL
```

Do not expand this into unconditional operational or materialization acceptance.

The original R2 human-approval provenance remains a separate evidence-verification matter.

### E. B1 review and authorization evidence

Recover the original available records for:

- R0 Master Gate findings and disposition.
- R1 correction approval and Master Gate findings.
- R2 correction approval.
- R2 technical Master Gate review.
- Any unresolved evidence-provenance qualifications.

Known R1 approval reference:

```ini
R1_APPROVAL_MESSAGE_ID=f158af6e-ad4d-4569-b2a6-ecdde87b9877
```

Reported R2 approval reference:

```ini
R2_APPROVAL_MESSAGE_ID=fec42bdd-e147-4e75-ad10-c7c2c4abb397
R2_APPROVAL_REPORTED_CREATED_BY=user
```

The R2 approval record must be independently authenticated before publication as verified human authorization.

An assistant-authored approval template is not itself human authorization.

Do not manufacture missing historical records or silently promote a reported claim to verified fact.

## 4. Exact-byte evidence rules

For each original artifact:

1. Locate its original accessible backing object.
2. Record the original source and custody reference.
3. Independently calculate byte length and SHA-256.
4. Confirm equality with the accepted identity.
5. Preserve exact bytes, including line endings and trailing-LF status.
6. Compare the resulting Git blob's bytes against the recovered original.
7. Record the final Git blob SHA and path.

Do not normalize line endings, reformat Markdown, dedent, trim or re-save historical originals through an editor that changes their bytes.

If Git attributes or filters prevent exact preservation, stop and report the problem. Do not silently alter repository-wide settings.

If an original cannot be retrieved or its identity does not match, mark it `UNAVAILABLE_OR_UNVERIFIED`.

Do not reconstruct it from excerpts while labeling it original evidence.

Any investigator-written summary must be visibly distinguished from original-byte evidence.

## 5. Authorized output layout

Use:

`docs/symphony-hardening-playbook-v4.1/`

Create a focused ACQ-EXEC-06 documentation set containing:

1. Exact original B1-R0 planning packet.
2. Exact original B1-R1 planning packet.
3. Exact original B1-R2 planning packet.
4. Recoverable original B0 review and closure records.
5. Recoverable original B1 Master Gate review and approval records.
6. One canonical evidence index:

   `ACQ_EXEC_06_B1_EVIDENCE_INDEX.md`

Choose clear, stable filenames for the preserved historical records.

Record each exact filename and identity in the index.

Do not invent source-document identities or create placeholder copies that look authoritative.

If original records cannot be recovered, the index must identify their missing status and original known references.

## 6. Canonical evidence index requirements

The index must allow a future investigator to locate and understand the work without reconstructing several historical chat conversations.

Include:

- Purpose and scope of ACQ-EXEC-06.
- Governing repository commit, tree and accepted plan references.
- B0 source and companion identities without materializing their contents.
- B0 finding chronology and accepted dispositions.
- B1-R0 → B1-R1 → B1-R2 revision history.
- Exact byte and Git blob identities.
- Original human approval references.
- Master Gate decisions and remaining provenance qualifications.
- Clearly separated accepted findings and unresolved requirements.
- Links to preserved documents using relative repository paths.
- References to original conversation records where their contents have not been preserved.
- Future authorized handoff and retrieval requirements.
- Explicit prohibitions against interpreting this documentation as operational authorization.

Distinguish:

`REVIEWED`, `ACCEPTED_AT_PLANNING_LEVEL`, `REPORTED`, `UNVERIFIED`, `NOT_AUTHORIZED`, and `NOT_YET_ESTABLISHED`.

The index must not imply the existence of a durable archive merely because GitHub stores the documentation.

## 7. Strict mutation boundary

Allowed:

- One task-specific Git branch.
- Exact-byte preservation of approved documentation/evidence records.
- One new canonical evidence index.
- Documentation-only commits.
- Push of that branch.
- Creation of one draft documentation PR.
- Read-only verification of PR identity, diff and CI status.

Not allowed:

- Modifying Elixir, Rust, Python or application code.
- Creating any B0 executable source or materialization candidate.
- Running the B0 Python source.
- Creating test fixtures, helper programs or diagnostic scripts.
- Modifying existing governing roadmap or decision records.
- Changing machine governance projections.
- Performing Plane mutations.
- Changing GitHub protection rules or CI configuration.
- Merging the PR.
- Starting Symphony services or executing H-100.
- Preparing or executing Gate A or Gate B.

If the scope cannot be completed without an additional effect, stop and request a separately bounded authorization.

## 8. GitHub PR requirements

Create exactly one draft PR against current protected `main`.

Suggested title:

`docs(acq-exec-06): preserve B0/B1 planning and review evidence`

The PR description must identify:

- Exact target baseline SHA/tree.
- Every changed file and why it is authorized.
- Original evidence identities.
- Which artifacts were independently recovered.
- Which references remain unavailable or unverified.
- Scope of the planning-level technical review.
- Exact nonauthorization boundaries.
- Validation performed.
- Current CI state.
- Explicit prohibition on merge without independent Master Gate approval.

Do not claim CI success before GitHub confirms it.

Do not modify source files to make documentation CI pass.

Do not treat a successful CI run as evidence of operational qualification.

## 9. Mandatory self-check before handover

Before declaring the PR ready for independent review:

- Verify the complete diff against the exact selected baseline.
- Confirm there are no changes outside the authorized documentation set.
- Confirm preserved originals retain their exact expected bytes.
- Verify Git blob identities.
- Check that the index resolves to the intended files.
- Verify no B0 source payload was materialized or committed.
- Independently retrieve PR metadata and the pushed HEAD.
- Report required CI checks and their actual observed states.
- Confirm no merge or Plane mutation occurred.

A remaining provenance or missing-original issue must be disclosed rather than hidden.

## 10. Final deliverable

Return:

**A. Evidence preservation inventory**

For every artifact: title, source reference, original byte identity, resulting Git path/blob and verification status.

**B. Missing-evidence register**

List every unavailable or unverified original, its consequence and the smallest future recovery action.

**C. Canonical index**

Provide the exact Git path and its coverage.

**D. PR evidence**

Provide branch, base SHA/tree, HEAD SHA/tree, changed-file list, complete diff summary and current CI results.

**E. Authority disposition**

```ini
TASK=ACQ_EXEC_06_EVIDENCE_PRESERVATION_R0

DOCUMENTATION_PR=CREATED|BLOCKED
EXACT_BYTE_PRESERVATION=VERIFIED|PARTIAL|BLOCKED
B0_REVIEW_EVIDENCE=VERIFIED|PARTIAL|UNAVAILABLE
B1_R0_R1_R2_EVIDENCE=VERIFIED|PARTIAL|BLOCKED
R2_APPROVAL_PROVENANCE=VERIFIED|UNVERIFIED

B0_EXACT_BYTES_FROZEN=NO
B1_MATERIALIZATION_GRANT=NOT_ISSUED
B1_PERSISTENCE=NOT_AUTHORIZED
DURABLE_ARCHIVE=NOT_ESTABLISHED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
GATE_B_EXECUTION=NOT_AUTHORIZED
H100_ACCEPTANCE=NOT_ACHIEVED
AUTH_07=SUSPENDED_UNCONSUMED

MERGE=NOT_PERFORMED
PLANE_MUTATION=NONE
INDEPENDENT_MASTER_GATE_REVIEW=REQUIRED
```

Stop after one PR submission or an explicit evidence-access blocker.

Do not request or assume automatic permission to merge, correct additional issues or begin operational work.

The project owner and independent Master Gate will assess the exact PR and decide the next action.