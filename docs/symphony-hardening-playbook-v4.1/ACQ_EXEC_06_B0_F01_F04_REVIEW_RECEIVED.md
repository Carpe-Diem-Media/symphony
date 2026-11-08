## ACQ-EXEC-06 — Full B0 source-draft review

The new attachment resolves the apparent truncation in the earlier text export. Both artifacts are now present and complete enough for substantive static review.

I independently measured the uploaded Markdown:

| Artifact                   | Measured size | Status                 |
| -------------------------- | ------------- | ---------------------- |
| Complete uploaded document | 54,560 bytes  | Verified               |
| Artifact 1 — Python draft  | 34,540 bytes  | Complete text received |
| Artifact 2 — review packet | 19,412 bytes  | Complete text received |

The two individual sizes represent the UTF-8 contents extracted from the Markdown code fences, not independently accepted original `.py` or `.md` files.

The attachment's SHA-256 is:

`8082fc8a1b03408c2db1c867dbb8872ad1fd5377be725085768b3f09af203973`

The earlier findings about missing Python definitions and a truncated L00–L22 table no longer apply to this complete attachment.

I have not imported, compiled or executed the candidate.

### Static source-review findings

The complete draft has several important strengths. It reproduces all 23 lifecycle entries, distinguishes the ten nonterminal and nine terminal states, and preserves separate Gate A and Gate B acceptance states. The code also includes the correct Gate A completeness figures: 11 methods, 104 explicit subtests and 240 overlapping loop observations.

Most importantly, the `QualificationAuthority` façade refuses all listed operational actions through `LocalProgressDenied`. Its abstract ports do not fabricate a durable store, trusted acknowledgment or launch permission. This is consistent with the authorized inert-drafting scope.&#x20;

ACQ_EXEC_06_B0_CONVERSATIONAL_DRAFT.md



However, I found three substantive design issues and one catalogue ambiguity.

| Finding                              | Severity | Assessment                                                                                                                                                                                                                                                                                                 |
| ------------------------------------ | -------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| B0-F01: Incomplete structural checks | P1       | `inspect_proposal_shape()` accepts L01 without a `BindingClaim`, even though L01 requires fresh attempt/run registration. It also does not require a previous-transition digest for existing-attempt transitions. The function does not grant authority, but it accepts structurally incomplete proposals. |
| B0-F02: Pre-attempt denial identity  | P1       | L00 describes durable denial, but the proposed data model does not explicitly require a unique request/denial identity before an attempt exists. Q04 needs this identity to distinguish and correlate denied requests.                                                                                     |
| B0-F03: Global CAS obligation        | P1       | `TransitionRule.owners` omits `LEDGER_OWNER` on several transitions. That can be legitimate if owners describe decision participants, but the mandatory externally enforced CAS and durable ACK for every applicable transition should be expressed as a separate global invariant.                        |
| B0-F04: Adverse-route ambiguity      | P2       | `adverse_routes` mixes lifecycle transition identifiers with local refusal descriptions. It also omits L15/L16 from several prelaunch transition hints. Clarify whether these are non-exhaustive examples or the complete permitted adverse relation.                                                      |

For B0-F01, the relevant contrast is between L01's required binding in the catalogue and the weaker local shape check.&#x20;

ACQ_EXEC_06_B0_CONVERSATIONAL_DRAFT.md

ACQ_EXEC_06_B0_CONVERSATIONAL_DRAFT.md



These are not demonstrated operational authority bypasses. The operational façade remains refusing. They are source-contract precision defects that should be corrected before giving this candidate positive static-source acceptance.

### Recommended disposition

```
B0_CONVERSATIONAL_DRAFT=COMPLETE_RECEIVED
B0_STATIC_REVIEW=CHANGES_REQUESTED
B0_FINDINGS=P1_3_P2_1
B0_EXACT_BYTES_FROZEN=NO
B1_PERSISTENCE=NOT_AUTHORIZED
SOURCE_EXECUTION=NOT_AUTHORIZED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

Because the previous one-submission B0 grant was consumed, the Codex author must not silently modify or supplement this draft.

I recommend one new, narrowly bounded conversational correction grant rather than another architecture-planning cycle.

# ACQ-EXEC-06 — Proposed B0 Source-Correction Grant

**For explicit project-owner approval. Not issued by this review.**

Authorize the existing Codex author to produce one complete revised conversational submission of `qualification_authority.py` and `source_review_packet.md`.

Accepted input: the complete B0 draft received as `ACQ_EXEC_06_B0_CONVERSATIONAL_DRAFT.md`, uploaded-document SHA-256 `8082fc8a1b03408c2db1c867dbb8872ad1fd5377be725085768b3f09af203973`.

The correction scope is limited to:

1. **B0-F01:** Resolve structurally missing L01 bindings, existing-attempt previous-digest claims and contradictory no-attempt binding shapes, without representing local shape validation as authenticated authorization.
2. **B0-F02:** Specify a distinct, untrusted pre-attempt request/denial identity and the external uniqueness/retention obligations. Do not fabricate a trusted denial record.
3. **B0-F03:** Explicitly model the global independently enforced CAS, previous-digest and durable-ACK obligations for applicable transitions, separate from decision-participant role labels.
4. **B0-F04:** Separate local refusal descriptions from lifecycle transition identifiers, and clarify the completeness and authority of adverse-transition hints.

Preserve the accepted ACQ-EXEC-05 R2 L00–L22 relation exactly. Do not introduce executable authority or operational implementations.

Deliver both complete revised drafts and an exact textual change explanation. Retain the earlier draft unchanged.

**No candidate filesystem writing, source execution, imports, compilation, linting, tests, helper creation, GitHub/Plane mutation or operational control qualification is authorized.**

This proposed grant permits only one complete conversational correction submission. It does not authorize exact-byte persistence or further automatic revisions.

If the complete corrected submission cannot be delivered, report it as incomplete and stop.

Required terminal status:

```
B0_REVISION=SUBMITTED|INCOMPLETE|BLOCKED
B0_SOURCE_EXECUTION=NOT_AUTHORIZED
B0_EXACT_BYTES_FROZEN=NO
B1_PERSISTENCE=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```

Recommendation: Authorize this tightly scoped correction, then bring back the revised complete draft. Once those findings are resolved, we can give a fresh independent reviewer the exact source and companion document for static acceptance, followed by a separately authorized byte-freeze and B1 persistence decision.