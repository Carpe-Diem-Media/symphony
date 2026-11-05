# P08 Host Evidence, Cleanup and Quarantine — Implementation Plan v0.7

**PROPOSED — NOT ACCEPTED**

```ini
STATUS=PROPOSED_FOR_INDEPENDENT_MASTER_GATE_REVIEW
PLAN_VERSION=0.7
P08_IMPLEMENTATION_PLAN_ACCEPTED=NO
P08_IMPLEMENTATION_AUTHORIZED=NO
P08_DOCS_PR_AUTHORIZED=NO
P08_CI_AUTHORIZED=NO
P08_PRIVILEGED_EXECUTION_AUTHORIZED=NO
AUTH_07=SUSPENDED_UNCONSUMED
GATE2_ACTIVATION_AUTHORIZED=NO
```

This plan implements only the contracts in [Technical specification v0.7](../../symphony-hardening-playbook-v4.1/GATE2_P08_HOST_EVIDENCE_SPEC.md). It introduces no independent interface or authority. Current permission covers editing these two local documents only. Every implementation/test/provisioning/workflow/publication action below is a future task requiring its own authority. T01/T18 are explicitly read-only verification tasks; they never modify the accepted specification or candidate. Do not run make all, Codex/provider tests or privileged proof under this planning authorization.

## 1. Baseline, specification binding and execution gates

Accepted main is `30fc30ec27fbadd7277c470a6d6cdb52ced59a4e`, tree `dc58f0babebe8a28b3de492eb430a84398abc580`. Before any future implementation, read repository instructions, live SGOV-2 and current human authorization; verify live protected main, ordered parents, PR #62, run 41822564643 and specification section 1 governing blobs. Stop on movement pending applicability decision. Do not require planner worktree cleanliness; future code work requires its authorized isolated branch/worktree.

Compute SHA-256 of the exact specification bytes with `sha256sum docs/symphony-hardening-playbook-v4.1/GATE2_P08_HOST_EVIDENCE_SPEC.md`. The external acceptance/implementation authorization must name that digest, version and baseline. Recompute before work and every independent review. Any specification edit invalidates that binding and requires re-review. This plan does not put its own digest inside itself. Final handoff supplies both file hashes. This draft plan is bound to specification v0.7 SHA-256 `b510eb0c8459c126d3b310d3d5c7225f9d8dda4559a16ff6704842a6fb69568d`. Recalculate it before acceptance; any change invalidates this draft binding.

Authorization gates are separate: specification/plan acceptance; nonprivileged implementation; focused non-Codex tests; privileged disposable-host tests; dependency acquisition/build; installation/runner/reset provisioning; workflow edits and automatic CI; commit/push/PR; human merge; integrated OB-025/P09/activation. Absence of any required grant stops that task. No implicit execution choice or commit instruction is supplied.

## 2. Source and test inventory

All existing source is inspected at accepted main, not inferred from historical plans. Existing AttemptBoundary release refusal remains until the full verifier is qualified. Actual signature is gate2_release_result/4. Public release_gate2_authority_fence/4 remains boundary-routed. P01 stored structs and schema versions remain unchanged. The explicit new nested Gate 2 released-fence map in spec section 7.1a is accepted only by strengthened P08 validators; old requested and legacy records are not migrated.

Future focused Elixir tests live under `elixir/test/symphony_elixir/host_evidence/`, with required suites cleanup_evidence_authority_test.exs, host_evidence_redaction_test.exs and gate2_quarantine_recovery_test.exs. Native protocol tests live under `native/gate2/protocol/tests/`; privileged tests under `native/gate2/qualification/tests/`, including cleanup_verification.rs and secret_free_evidence.rs. Existing agent_runtime, orchestrator, suspension, logging and migration tests remain regression requirements. The native scaffold is absent in the accepted tree.

Runtime interface assertions must also verify section 7.1a root-bound fence observation digest and the exact A release representation.

No production crate/test file is created by the present documentation task. Future APIs are exactly specification sections 4–8. Root protocol has exactly 15 opcodes. New Elixir public functions require adjacent typespecs.

## 3. Dependency-ordered tasks

For each task, the named tests below mean concrete cases with the specification's required guard/failure outcomes. Test-first means add the focused case, observe the expected failure under authorized tests, implement the smallest contract change, rerun the focused case, then its applicable preservation tests. Do not broaden to privileged/integrated commands without separate authority.

### P08-T01. Baseline and scope

```text
TASK_ID=P08-T01
SPEC_REQUIREMENTS=P08-AUTH-001,P08-AUTH-005
DEPENDENCIES=NONE
FILES_TO_CREATE=NONE
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 1; spec section 1.3
PRECONDITIONS=Read-only verification authorized; exact accepted spec digest and dependency evidence available
IMPLEMENTATION_STEPS=Read-only verification of live GitHub SHA/tree/protection, accepted blobs, accepted specification hash and source using git show. Inspect historical provenance; do not edit the specification, tests or any candidate file. A needed specification correction requires a separately reviewed new revision/digest and authorization.
TESTS_TO_ADD=NONE
VERIFICATIONS_TO_PERFORM=baseline_exact_objects,historical_provenance_register
NEGATIVE_CONTROLS=MUST reverify exact accepted main/tree and governing blobs; stop on movement.; MUST record historical export mismatch and never treat R1-R4 as accepted authority.
EXPECTED_PASS_CONDITION=Existing exact-byte source/authority/evidence independently agrees; no candidate/specification mutation occurred
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Read existing source, accepted specification and exact evidence without editing.
- [ ] Recompute required identities and inspect the named verification/test results.
- [ ] Report disagreement as findings; create no source, test, specification or workflow changes.
- [ ] If a correction is needed, stop this task and return to separately authorized revision/implementation and renewed exact-head checks.


### P08-T02. P01 projections

```text
TASK_ID=P08-T02
SPEC_REQUIREMENTS=P08-CMP-001,P08-CMP-002,P08-CMP-003,P08-CMP-004
DEPENDENCIES=P08-T01
FILES_TO_CREATE=elixir/lib/symphony_elixir/host_evidence/p01_projection.ex
FILES_TO_MODIFY=elixir/lib/symphony_elixir/agent_runtime/attempt_grant.ex;elixir/lib/symphony_elixir/agent_runtime/cleanup_evidence_ref.ex;elixir/lib/symphony_elixir/agent_runtime/quarantine_disposition.ex
EXACT_INTERFACE_CONTRACT=spec section 2.1; spec section 2.1; spec section 2.2,5.3; spec section 2.2
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement pure exact projection/reverse mapping with unsupported-value failure; keep stored struct fields unchanged.
TESTS_TO_ADD=grant_ref_exact_namespace,stored_struct_fields_exact,historical_and_current_links,p01_id_128_129_256_257
NEGATIVE_CONTROLS=MUST preserve exact five-field GrantRef and deterministic P01 fingerprint.; MUST preserve exact Identity, Generation, AttemptResource and reference/disposition stored shapes.; MUST map all string-or-nil references losslessly; current links only in declared verified slots.; MUST support encodable 256-byte IDs and block broader values without rewrite or normalization.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T03. Canonical schemas

```text
TASK_ID=P08-T03
SPEC_REQUIREMENTS=P08-EVD-001,P08-EVD-002,P08-EVD-003
DEPENDENCIES=P08-T02
FILES_TO_CREATE=elixir/lib/symphony_elixir/host_evidence/codec.ex;native/gate2/protocol/src/codec.rs
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 5.1; spec section 5.2,6.1; spec section 5.3-5.4
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement the specification type registry and canonical codec in both languages. No production authority writer is enabled.
TESTS_TO_ADD=canonical_reject_corpus,all_record_fields_closed,golden_generation_and_revision
NEGATIVE_CONTROLS=MUST implement strict G2-CJSON-2 scalars/keys/order/bounds and reject ambiguous bytes.; MUST use the exact closed record registry and operation envelopes.; MUST preserve domain-separated identities, immutable creation generation and revision-bound snapshots.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T04. Native build bootstrap

```text
TASK_ID=P08-T04
SPEC_REQUIREMENTS=P08-QUAL-002
DEPENDENCIES=P08-T01
FILES_TO_CREATE=native/gate2/Cargo.toml;native/gate2/Cargo.lock;native/gate2/rust-toolchain.toml;native/gate2/client/Cargo.toml;native/gate2/helper/Cargo.toml;native/gate2/protocol/Cargo.toml;native/gate2/protocol/src/lib.rs;native/gate2/helper/src/main.rs
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 11.2
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Approve exact dependency closure and compiler distribution before build. Bootstrap static client/helper/protocol workspace and locked offline build identity. Packages are gate2-client, gate2-helper and gate2-protocol; binary outputs are evidence_client and attempt_boundary, with explicit paths client/src/main.rs and helper/src/main.rs. Only inert bootstrap entry points exist before guarded protocol implementation. Default test members are protocol/pure logic; privileged fixture tests require separate explicit targets.
TESTS_TO_ADD=locked_build_identity
NEGATIVE_CONTROLS=MUST bind source/toolchain/lockfile/dependencies/build image/binary identity before installation.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T05. Invocation and descriptor custody

```text
TASK_ID=P08-T05
SPEC_REQUIREMENTS=P08-INV-001,P08-INV-002,P08-INV-003
DEPENDENCIES=P08-T03,P08-T04
FILES_TO_CREATE=native/gate2/client/src/main.rs;native/gate2/helper/src/invocation.rs;elixir/lib/symphony_elixir/host_evidence/native_client.ex
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 3.1; spec section 3.1; spec section 3.2; spec sections 5.2b,5.2c,6.17a,6.18,7.1b as assigned below
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement fixed executable/stdio socket bootstrap, credentials/pidfds, descriptor close rules and bounded port handling. Privileged tests are separate. Implement the same-boundary/new-native-session handoff transport and reject adoption of ACTIVE/INTERRUPTED sessions under specification 6.18. Apply section 6.16a transport-only close acknowledgement and bounded no-write teardown.
TESTS_TO_ADD=fixed_installation_replacement,sudo_args_env_proxy_rejected,peer_pidfd_credentials_inheritance,handoff_startup_failure,handoff_live_old_helper,close_client_death_after_commit
NEGATIVE_CONTROLS=MUST use fixed root-owned executables/manifests/policy and pinned installation identities.; MUST restrict sudo to fixed digest command with empty arguments and qualified stdio behavior.; MUST enforce descriptor table, kernel credentials/pidfds, client liveness and ancillary rejection.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T06. Root store and session guards

```text
TASK_ID=P08-T06
SPEC_REQUIREMENTS=P08-INV-004,P08-INV-005,P08-INV-006,P08-EVD-004
DEPENDENCIES=P08-T05
FILES_TO_CREATE=native/gate2/helper/src/control.rs;native/gate2/helper/src/store.rs;native/gate2/protocol/src/operations.rs
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 3.3; spec section 6.1; spec section 3.3,6.1; spec section 3.3,7.3; spec sections 5.2b,5.2c,6.17a,6.18,7.1b as assigned below
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement pinned flock, root immutable chain/head and all common session/phase/error guards. Prohibit worker fork/exec/FD transfer. Implement AuthorityHandoff publication in close_session without another opcode, exact post-close-head adoption and policy-registry pin resolution under sections 5.2b/5.2c/6.18. Include IndexRestrictionReceipt validation in bind_snapshot and expose terminal records in query_settlement. Implement specification 6.5a explicit initial authorization consumption, retained replay history and UNUSED/CONSUMED/UNCERTAIN recovery; operation hashes and later evidence are insufficient. Apply specification 6.5b initial snapshot provenance and exact root/I digest cross-binding; initial snapshot bytes never authorize progress before durable I restriction. Implement sections 6.5c/6.16a authenticated restriction bytes/query and durable QUIESCENT before transport acknowledgement. Apply section 6.13a: query_settlement is read-only within the existing release session with current owner/G/session/sequence and exact expected-head checks; it never acquires another lock or mutates root state.
TESTS_TO_ADD=h1_pause_restart_h2_busy,all_15_opcode_guards,timeout_live_helper_blocks,immutable_publish_crash_windows,handoff_head_changed,handoff_wrong_purpose,bind_snapshot_without_restriction,acquisition_consumption_restrict_commit,acquisition_consumption_lost_reply,acquisition_consumption_history_missing,initial_snapshot_commitment_match,initial_snapshot_commitment_mismatch,restriction_root_index_digest_distinct,root_restriction_bytes_roundtrip,root_restriction_query_orphan,root_restriction_query_historical,close_quiescent_before_ack_crash,close_ack_lock_still_held,release_query_head_changed,release_second_helper_lock_busy
NEGATIVE_CONTROLS=MUST retain pinned exclusive root lock across timeout/restart with no stealing.; MUST frame bounded sessions and reject stale/duplicate/illegal-phase requests.; MUST treat partial writes/timeouts/ambiguous responses as closed, never termination proof.; MUST publish immutable objects/control with file and directory sync; orphans never confer authority.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T07. Acyclic generation protocol

```text
TASK_ID=P08-T07
SPEC_REQUIREMENTS=P08-GEN-001,P08-GEN-002,P08-GEN-003
DEPENDENCIES=P08-T06
FILES_TO_CREATE=native/gate2/helper/src/recovery.rs;elixir/lib/symphony_elixir/host_evidence/recovery_journal.ex
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 4.1; spec section 4.2; spec section 4.1,6
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement propose_generation then journal then begin_recovery; persist high-water and exact immutable plan. Resume only bound plans; never select target in begin_recovery.
TESTS_TO_ADD=proposal_journal_plan_acyclic,proposal_expiry_burn_conflict,opcode_vocabulary_and_schemas
NEGATIVE_CONTROLS=MUST reserve target generation durably before host target computation; bind journal before R mutation.; MUST bind reservation/source/session/expiry, burn abandoned sequences and forbid current-generation inference.; MUST define exactly 15 closed operations, with begin_recovery binding rather than selecting target.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T08. Staged R recovery

```text
TASK_ID=P08-T08
SPEC_REQUIREMENTS=P08-GEN-004,P08-GEN-005,P08-GEN-006,P08-REC-001,P08-REC-002,P08-REC-003
DEPENDENCIES=P08-T07
FILES_TO_CREATE=NONE
FILES_TO_MODIFY=elixir/lib/symphony_elixir/agent_runtime/attempt_boundary.ex;elixir/lib/symphony_elixir/agent_runtime/attempt_resource_ledger.ex
EXACT_INTERFACE_CONTRACT=spec section 4.3; spec section 4.4; spec section 4.1-4.4; spec section 4.3; spec section 4.3; spec section 4.4
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement staged APIs and source/target exact repair; no ordinary startup side effects in enrolled path. Keep dirty DETS maintenance-required.
TESTS_TO_ADD=staged_no_startup_side_effect,recovery_partial_rows_exact,recovery_activation_current_closed,dirty_dets_needs_repair,readonly_reopen_replacement,legacy_pending_no_journal
NEGATIVE_CONTROLS=MUST stage R read-only before generation mutation and preserve compatibility startup rejection.; MUST persist exact journal and apply/repair only before-or-after images without repeated increment.; MUST activate only closed current E/I/R agreement; owner repair requires another fresh generation.; MUST block dirty/unreadable DETS without automatic repair or history erasure.; MUST retain path lock and validate file/semantic identity across close/write-reopen.; MUST leave old unbound P01 pending markers maintenance-required.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T09. Process/resource observations

```text
TASK_ID=P08-T09
SPEC_REQUIREMENTS=P08-EVD-005
DEPENDENCIES=P08-T06,P08-T08
FILES_TO_CREATE=native/gate2/helper/src/observation.rs;native/gate2/helper/src/process.rs;native/gate2/helper/src/resources.rs
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 3.2,9
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement qualified fixture observers by stable allocation/object/process identity. Unsupported classes stay explicit; never perform runtime cleanup.
TESTS_TO_ADD=replacement_and_missing_history
NEGATIVE_CONTROLS=MUST use stable allocation/process/object identity and complete qualified reference coverage.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T10. Evidence provenance

```text
TASK_ID=P08-T10
SPEC_REQUIREMENTS=P08-EVD-006
DEPENDENCIES=P08-T03,P08-T09
FILES_TO_CREATE=native/gate2/helper/src/evidence.rs;elixir/lib/symphony_elixir/host_evidence/verifier.ex;elixir/lib/symphony_elixir/host_evidence/record.ex
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 2.3,5.3
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement natively constructed immutable evidence and independent host provenance verification, exact self-bindings and current profile checks.
TESTS_TO_ADD=forged_ref_index_object
NEGATIVE_CONTROLS=MUST independently resolve evidence provenance; shape-valid CleanupEvidenceRef is insufficient.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T11. Host evidence index

```text
TASK_ID=P08-T11
SPEC_REQUIREMENTS=P08-REL-001
DEPENDENCIES=P08-T08,P08-T10
FILES_TO_CREATE=elixir/lib/symphony_elixir/host_evidence/ledger.ex
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 7.1; spec sections 5.2b,5.2c,6.17a,6.18,7.1b as assigned below
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement non-authoritative private DETS mirror/index with captured boundary caller/epoch guards and synchronized rereads. Implement exact IndexRestriction/receipt and private DETS tags/head/history under section 7.1b. Advance the evidence-only branch only to QuarantineEvidenceIndex. Never fabricate an INDEXED receipt for initial restriction or overwrite unresolved history. Apply specification 6.5b initial snapshot provenance and exact root/I digest cross-binding; initial snapshot bytes never authorize progress before durable I restriction. Implement section 6.5c RootRestrictionProof as restrict_sync/3 third argument and the exact restriction-history wrapper. Use static declared terminal fixtures only for quarantine_evidence_index_repair_fixture; this is I reconciliation unit proof, not native or integrated evidence. Implement section 6.13a captured-boundary restrict_sync/3 wrapper, private restrict_write_sync/restrict_confirm_read calls and owner-bound in-memory token. Call the existing NativeClient same-session query between those ledger calls, then recheck actual I. Fixture-level native-client responses do not establish real channel/lock proof.
TESTS_TO_ADD=owner_epoch_receipt_forgery,index_restricted_first_record,index_restriction_sync_loss,index_restriction_partial_head,index_restriction_replay,index_restriction_conflict,index_restriction_stale_generation,quarantine_evidence_index_repair_fixture,restriction_receipt_cross_binding,root_restriction_bytes_tamper,root_restriction_wrong_receipt,release_post_index_sync_query,restrict_sync_no_owner_deadlock
NEGATIVE_CONTROLS=MUST enforce exact E/I/R/A writer principals and synchronized non-authoritative I mirrors.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T12. Verified resource commits

```text
TASK_ID=P08-T12
SPEC_REQUIREMENTS=P08-REL-002
DEPENDENCIES=P08-T10,P08-T11
FILES_TO_CREATE=NONE
FILES_TO_MODIFY=elixir/lib/symphony_elixir/agent_runtime/attempt_resource_ledger.ex
EXACT_INTERFACE_CONTRACT=spec section 7.2
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Add verify_fence_sync/4 and verify_snapshot_sync/4 with native provenance, exact revision and legal-transition guards. Do not enable allocation/destruction.
TESTS_TO_ADD=resource_verification_exact_revision
NEGATIVE_CONTROLS=MUST commit only guarded FENCING→FENCED or DESTROYING→ABSENT_VERIFIED with exact revisions.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T13. AttemptLedger release receipt

```text
TASK_ID=P08-T13
SPEC_REQUIREMENTS=P08-CMP-005,P08-REL-003
DEPENDENCIES=P08-T12
FILES_TO_CREATE=NONE
FILES_TO_MODIFY=elixir/lib/symphony_elixir/agent_runtime/attempt_ledger.ex
EXACT_INTERFACE_CONTRACT=spec section 2.3,7.4; spec section 7.1-7.2 including 7.1a
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Add boundary-only commit_gate2_release_sync/5 and exact released-receipt validation without weakening any generic writer/history guard.
TESTS_TO_ADD=gate2_history_no_downgrade,attempt_release_preparation_bound
NEGATIVE_CONTROLS=MUST retain A current/history binding and reject legacy downgrade through every writer.; MUST commit A only from boundary with exact prepared projection and verified R receipt.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T14. Release and admission guards

```text
TASK_ID=P08-T14
SPEC_REQUIREMENTS=P08-REL-004,P08-REL-005,P08-REL-006,P08-AUTH-002,P08-AUTH-003
DEPENDENCIES=P08-T11,P08-T12,P08-T13,P08-T16
FILES_TO_CREATE=elixir/lib/symphony_elixir/host_evidence/release.ex;elixir/test/symphony_elixir/host_evidence/gate2_admission_guards_test.exs
FILES_TO_MODIFY=elixir/lib/symphony_elixir/agent_runtime/attempt_boundary.ex;elixir/lib/symphony_elixir/orchestrator.ex;elixir/lib/symphony_elixir/work_control/suspension_recovery.ex
EXACT_INTERFACE_CONTRACT=spec section 6,7.2; spec section 7.4; spec section 7.3; spec sections 5.2b,5.2c,6.17a,6.18,7.1b as assigned below
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement resource acknowledgement before preparation, exact A receipt and two-stage completion. Audit all dispatch/clear/reuse/rearm readers; keep unconditional P08 dispatch denial. Implement section 6.17a terminal QUARANTINED evidence acquisition, retained root provenance and I agreement with byte-identical R/A. All release-only operations reject QUARANTINE_EVIDENCE. Implement specification 6.5a explicit initial authorization consumption, retained replay history and UNUSED/CONSUMED/UNCERTAIN recovery; operation hashes and later evidence are insufficient. Apply specification 6.5b initial snapshot provenance and exact root/I digest cross-binding; initial snapshot bytes never authorize progress before durable I restriction. Run quarantine_evidence_index_repair against the real authoritative terminal E producer and actual I store; include lost-response restriction-byte integration under section 6.5c. Implement section 6.13a real same-session post-I-sync query and E-query/I-R-A-read/E-query bracket before each complete_release action, with distinct JointRead IDs, no interleaving mutation and exact next-request expected-head checks. Assert blocked outcomes on lost reads, changed head/events and exhausted budgets.
TESTS_TO_ADD=release_order_resource_ack_first,released_a_missing_completion_denied,release_all_crash_boundaries,authorization_scope_denial,dormant_and_legacy_guards,quarantine_evidence_terminal,quarantine_evidence_no_resource_mutation,quarantine_evidence_interrupted_publication,acquisition_consumption_before_terminal,acquisition_consumption_orphan_uncertain,snapshot_bind_after_index_sync_only,restriction_to_snapshot_crash_windows,quarantine_evidence_index_repair,root_restriction_query_lost_reply,close_lost_response_query,release_post_index_sync_query_integration,release_completion_joint_queries_fresh,release_query_reply_lost,release_second_helper_lock_busy_integration
NEGATIVE_CONTROLS=MUST acknowledge resources before prepare, then A, completion, I completion and fresh settlement.; MUST require joint current quiescent agreement on every dispatch/reuse/clear/rearm path.; MUST cover every write/sync/publication boundary and uncertain old/new/corrupt result.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T15. Quarantine and disclosure

```text
TASK_ID=P08-T15
SPEC_REQUIREMENTS=P08-QUA-001,P08-QUA-002,P08-QUA-003
DEPENDENCIES=P08-T10,P08-T11,P08-T14
FILES_TO_CREATE=native/gate2/helper/src/quarantine.rs;elixir/lib/symphony_elixir/host_evidence/quarantine.ex;elixir/lib/symphony_elixir/host_evidence/disclosure.ex;elixir/test/symphony_elixir/host_evidence/quarantine_resolution_contract_test.exs
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 8.2; spec section 8.1; spec section 8.3; spec sections 5.2b,5.2c,6.17a,6.18,7.1b as assigned below
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement explicit begin/retain/release resolution variants, root reservation/terminal consumption/revocation and immutable disclosure histories. Close evidence-only quarantine acquisition exception without granting release. Implement section 6.18 installer handoff fixtures against an already existing epoch, expiry/head/issuer checks and one-use consumption. Keep administrative fixture provisioning behind separately authorized disposable-host execution. Implement resolution entry from the terminal evidence-only head. Verify section 6.16a same-owner committed handoff adoption after actual lock release without requiring a prior transport acknowledgement; reject changed owner.
TESTS_TO_ADD=quarantine_no_ack_release,decision_wrong_scope_revoked_replay,known_incomplete_restart_sticky,resolution_begin_pending,retain_without_proof,release_requires_release_decision,pending_restart_burned,epoch_handoff_roundtrip,handoff_boundary_restart,handoff_expired,handoff_installer_partial_sync,handoff_replayed_consumption,quarantine_evidence_later_resolution,close_handoff_adoption_without_ack
NEGATIVE_CONTROLS=MUST retain quarantine on cleanup/ownership/disclosure uncertainty and never resolve by acknowledgement.; MUST authenticate root-provisioned decision scope/revocation/one-use; no arbitrary decision ID authority.; MUST preserve known/possible/incomplete disclosure separately with sticky history and scope-specific resolution.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T16. Diagnostic and event handling

```text
TASK_ID=P08-T16
SPEC_REQUIREMENTS=P08-DIA-001,P08-DIA-002,P08-DIA-003,P08-DIA-004
DEPENDENCIES=P08-T05,P08-T10
FILES_TO_CREATE=native/gate2/helper/src/diagnostic_policy.rs;elixir/lib/symphony_elixir/host_evidence/diagnostic_policy.ex;elixir/lib/symphony_elixir/host_evidence/diagnostic_capture.ex;elixir/test/symphony_elixir/host_evidence/diagnostic_applicability_test.exs
FILES_TO_MODIFY=elixir/lib/symphony_elixir/codex/app_server.ex;elixir/lib/symphony_elixir/agent_runner.ex;elixir/lib/symphony_elixir/credential_boundary.ex;elixir/lib/symphony_elixir/log_file.ex
EXACT_INTERFACE_CONTRACT=spec section 10; spec section 10; spec section 10; spec section 10; spec sections 5.2b,5.2c,6.17a,6.18,7.1b as assigned below
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Implement bounded concurrent drainage, typed diagnostics and event invalidation. Audit all raw failure paths; preserve legacy redaction/rotation semantics. Implement the closed DiagnosticPolicy registry and fixed root-owned policy resolution from sections 5.2b/5.2c in both native and host verifiers. Test policy installation only as separately authorized root fixtures; ordinary codec tests use static bytes and cannot qualify installation.
TESTS_TO_ADD=flood_inherited_writer_cancel,synthetic_secret_all_host_sinks,event_gap_snapshot_race,diagnostic_terminal_meanings,resource_only_no_capture,required_capture_cannot_be_not_applicable,diagnostic_policy_missing,diagnostic_policy_replaced,diagnostic_policy_unqualified,diagnostic_policy_caller_digest,diagnostic_policy_partial_enrollment,diagnostic_policy_stale_profile,diagnostic_policy_replaced_during_observation
NEGATIVE_CONTROLS=MUST bound concurrent retention/drain/cancellation, record sticky truncation and preserve custody obligations.; MUST prevent raw captured payloads reaching logs/evidence/errors/core/temp/operator outputs.; MUST invalidate cached evidence on event loss/restart/cursor mismatch and reread authoritatively.; MUST preserve four diagnostic non-equivalences and terminal/restart states.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T17. CI and privileged qualification

```text
TASK_ID=P08-T17
SPEC_REQUIREMENTS=P08-AUTH-004,P08-QUAL-001,P08-QUAL-003,P08-QUAL-004,P08-QUAL-005
DEPENDENCIES=P08-T14,P08-T15,P08-T16
FILES_TO_CREATE=native/gate2/qualification/README.md;native/gate2/qualification/runner_profile.json;elixir/test/symphony_elixir/host_evidence/qualification_claim_test.exs
FILES_TO_MODIFY=.github/workflows/make-all.yml
EXACT_INTERFACE_CONTRACT=spec section 9,12.1; spec section 11.1; spec section 11.2; spec section 11.2
PRECONDITIONS=Exact spec digest accepted and this task scope separately authorized; dependency evidence current
IMPLEMENTATION_STEPS=Only under separate workflow/infrastructure/CI authorization, add exact native required jobs, aggregate failure guards, approved ephemeral host and external-reset proofs.
TESTS_TO_ADD=fixture_claim_not_production,limits_boundary_and_saturation,runner_capability_reset_isolation,aggregate_missing_privileged_denied,claim_scope_ob025_not_closed
NEGATIVE_CONTROLS=MUST partition fixture/host-only and integrated claims without production promotion.; MUST enforce candidate bounds and reject saturation without partial clean claims; accept only measured profile.; MUST qualify single-use privileged runner and external reset controller under separate authority.; MUST preserve existing required CI and make missing native proof non-successful.
EXPECTED_PASS_CONDITION=Every assigned contract assertion holds; all negative cases deny authority and preserve original durable facts
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Confirm the listed requirement assertions and source contracts before editing.
- [ ] Add the named focused negative and positive cases with actual persisted-state assertions.
- [ ] Under the matching test authorization, observe the pre-change failure, implement the selected contract and verify its outcome.
- [ ] Review the complete task diff and relevant legacy/P01 regressions; retain evidence without publishing.

### P08-T18. Independent acceptance

```text
TASK_ID=P08-T18
SPEC_REQUIREMENTS=P08-AUTH-002,P08-AUTH-003,P08-QUAL-005
DEPENDENCIES=P08-T17
FILES_TO_CREATE=NONE
FILES_TO_MODIFY=NONE
EXACT_INTERFACE_CONTRACT=spec section 1.4; spec section 1.4,7.4; spec section 12.1,12.3
PRECONDITIONS=Read-only verification authorized; exact accepted spec digest and dependency evidence available
IMPLEMENTATION_STEPS=Independently review complete exact-head diff and claim applicability, required CI, qualified host artifacts and all preservation tests. Prepare human acceptance/merge handoff without issuing authority.
TESTS_TO_ADD=NONE
TESTS_TO_REVIEW=authorization_scope_denial,dormant_and_legacy_guards,claim_scope_ob025_not_closed
NEGATIVE_CONTROLS=MUST NOT infer implementation, CI, privilege, publication, merge or activation authority.; MUST preserve dormant foundation, incomplete enforced, no grants/retry/rearm/provider/publication/Done.; MUST accept claims independently by exact scope/artifact/environment and retain integrated OB-025 incomplete.
EXPECTED_PASS_CONDITION=Existing exact-byte source/authority/evidence independently agrees; no candidate/specification mutation occurred
STOP_CONDITIONS=Authority missing; spec/source drift; unsupported host; unknown/malformed persisted state; failed focused/preservation test; new architectural choice
REVIEW_EVIDENCE=Exact diff/head/tree; assigned test IDs/results; relevant spec section; qualified profile and artifacts where required
```

- [ ] Read existing source, accepted specification and exact evidence without editing.
- [ ] Recompute required identities and inspect the named verification/test results.
- [ ] Report disagreement as findings; create no source, test, specification or workflow changes.
- [ ] If a correction is needed, stop this task and return to separately authorized revision/implementation and renewed exact-head checks.


## 3.1 Exact-candidate ordering and read-only tasks

T01 and T18 are verification-only tasks. Their TESTS_TO_ADD=NONE and no-file-change declarations override the generic test-first steps intended for implementation tasks. Baseline named checks are read-only verifications, not an instruction to add test files. Neither task may edit the accepted specification. A needed specification change stops execution and creates a separately reviewed revision/new digest before work can resume.

T14 implements authorization_scope_denial and dormant_and_legacy_guards. T17 implements claim_scope_ob025_not_closed before its final qualification/CI run. All tests, fixtures and workflow changes must exist before the candidate SHA/tree is frozen for that run. T17 records that exact candidate and verifies complete required evidence. T18 independently reads the same candidate and results without adding/running new candidate-changing tests. Findings requiring any source/test/workflow correction return to the appropriate implementation task, create a new candidate and require renewed T17 exact-head evidence before T18 repeats. No post-CI mutation inherits earlier certification.

## 4. Exact interfaces and test assertions

The specification is the sole API/schema definition, including section 7.1a argument/return contracts and the exact A nested released representation. Implementation must not infer fields from a historical plan. Specific assertions below refine test execution without changing semantics.

- Projection tests compare exact maps/structs and original strings, namespace and deterministic P01 grant fingerprint. Test 128/129/256/257-byte IDs, unsupported Unicode and integer overflow. Assert no write occurred on an unencodable record.
- Codec tests independently encode/decode the entire closed registry and all 15 operation request/response variants. Compare literal bytes/digests, not one serializer against itself. Reject duplicates before map conversion, alternative escaping, unknown keys, trailing bytes and over-depth/size inputs.
- Native adapter tests assert every section 12.3b error mapping without raw error text and preserve storage latches.
- Root tests pause H1 while lock held, kill/restart BEAM, attempt H2 and assert lock_busy and unchanged R. Resume H1 and prove it cannot manufacture a new owner's authority. Never time-steal the lock.
- Recovery tests assert event order PROPOSED receipt, target construction, journal file+directory sync, PLAN_BOUND receipt, first R write, I mirror, root commitment, actual reread, closed activation. begin_recovery must never call the generation chooser.
- Staged tests hash/inspect the existing file before/after read-only inspection, attempt competing openers and replacement between close/reopen, and assert no choose_startup_generation/ensure_metadata call. needs_repair must remain maintenance_required without repair.
- Partial-row tests enumerate every row split between exact before/after, both metadata values and marker presence. The final revision equals old+1, never old+2. Any third value or missing bound journal blocks.
- Resource tests retain object A handle while replacing locator with B. Assert no B deletion and no A absence verdict from path state. Wrapper survival, PID reuse, unexpected exec/cgroup/namespace changes fail identity. A pidfd alone cannot prove executable stability; require the qualified owner or controlled fixture no-exec/no-migration guard.
- Release tests assert resource acknowledgement before preparation, preparation before A write, A reread before root A ack, completion before I completion, and fresh joint read before settlement. A released with missing completion must deny every admission/clear/rearm reader.
- Decision tests attempt caller-shaped IDs, unauthorized issuer, wrong namespace/G/epoch/head/vector, revoked/consumed entry and uncertain consumption. All preserve quarantine. Known/incomplete disclosure and unrelated obligations cannot be erased by a resource-only decision. Test begin as a reserved nonterminal state; retain has no evidence fields; release requires its exact qualified proof and release-capable decision. Revocation, lost begin/final reply, duplicate terminal action and session restart cannot reuse a reservation. Evidence-only quarantine acquisition requires the separate root authorization digest; prepare/A commit/settlement stay forbidden and a later resolution decision binds the resulting head.
- Diagnostic tests validate NOT_APPLICABLE only for a qualified resource-only zero-channel policy, reject it for required/started captures and reject any fabricated CLOSED record. They then flood both streams, retain a descendant writer, cancel with blocked pipes, lose events during snapshot and inject synthetic secrets into all host error/log/temp/core/operator channels. Assert explicit truncation/cancellation/incompleteness and no raw promotion.

## 5. Test command boundaries

No commands in this section were executed during planning. After explicit nonprivileged test/build authorization, use focused commands, not make all:

```bash
cd elixir
mix test test/symphony_elixir/host_evidence/cleanup_evidence_authority_test.exs
mix test test/symphony_elixir/host_evidence/host_evidence_redaction_test.exs
mix test test/symphony_elixir/host_evidence/gate2_quarantine_recovery_test.exs
```

Future native pure tests use locked offline dependency input already approved:

```bash
cargo test --manifest-path native/gate2/Cargo.toml -p gate2-protocol --locked --offline
```

The selected workspace must name the protocol package gate2-protocol. This command runs no helper installation, sudo, provider or privileged fixture. Native integration binaries and privileged tests are not default test targets; qualification harness requires an explicit approved profile and authorization manifest and must reject their absence. No sudo command is part of ordinary test setup. mix tests must use fixture app-server seams and an execution tripwire that fails if a real Codex/provider process is requested. If existing harness startup can invoke Codex, stop and obtain the correct isolated focused-test harness/authorization before running.

## 6. Recovery and durability execution matrix

Automate every row in specification sections 4.5 and 7.3 with named boundary IDs. For every sync/write/publication boundary test old durable result, new durable result and invalid/partial result. Read actual E/I/R/A after restarting owners. An injected API success is never the expected answer by itself.

For generation tests retain proposal/plan/journal identities, source/target rows and root burn high-water. Cover proposal lost response, journal missing/unsynced/orphaned, plan missing/uncertain, pending marker before/after sync, every partial row position, metadata update before marker deletion, R complete/root incomplete, root complete/I unavailable, live H1 ownership and repeated owner restarts. Dirty DETS cases explicitly terminate maintenance_required; do not alter repair:false to obtain a green test.

For release tests retain exact object bytes, publication/head identities, I phases, R vector and A receipt at each boundary. Include orphan object, forged index, index unavailable, R success/A failure, A success/completion failure, previous-generation settlement, replayed IDs, revision conflict, concurrent admission and generic legacy writer attempts. Confirm every listed admission reader rejects the incomplete combination.

Unprivileged fault injection exercises ordering and logical outcomes. It does not prove power-loss durability. Real reset/FS/kernel behavior is P08-T17 and requires the approved single-use host/controller and privilege authority.

## 7. P01 and legacy preservation

Run separately authorized existing boundary/resource/attempt/migration/orchestrator/suspension suites against exact candidate. Assert whole-ledger schema handling, legacy pending rejection, sync/integrity latches, captured owner/name/monitor checks and Gate 2 history preservation. Retain dormant foundation and incomplete enforced modes. No source/provider/publication/Done/credential/retry authority may appear in the diff. A fixture may initialize future-owner states only through non-production test code; no runtime-configurable seed/manifest bypass is allowed.

## 8. CI, qualification and final review gates

P08-T17 requires separate workflow editing, CI, runner creation/root effects and external reset authority. Keep all accepted required jobs and checks, coverage/Dialyzer/isolation. Missing/skipped/unavailable privileged proof must make the required aggregate non-successful. Bind exact checkout SHA/tree, image, compiler/deps/lockfile/binaries, sudo, kernel/fs, measurements, controller logs, seeds and test/claim IDs. Host-only artifact labels cannot close production cleanup or integrated OB-025.

Independent final review requires complete diff, exact head/tree, accepted specification digest, authority register, all focused/preservation results and externally qualified evidence. Any code change after certification invalidates it. Human merge and postmerge acceptance remain separate. Do not open a documentation PR until explicitly authorized, including its automatic CI. Do not merge, consume AUTH_07 or activate Gate 2 from this plan.

## 9. Requirement coverage and remaining prerequisites

- P08-AUTH-001: P08-T01; `baseline_exact_objects`; GitHub SHA/tree/protection and blob comparison.
- P08-AUTH-002: P08-T14; `authorization_scope_denial`; Independent scope/diff review.
- P08-AUTH-003: P08-T14; `dormant_and_legacy_guards`; Exact-head preservation suite.
- P08-AUTH-004: P08-T17; `fixture_claim_not_production`; Claim-specific P02/P03/P04/P09 evidence.
- P08-AUTH-005: P08-T01; `historical_provenance_register`; Historical attachment reconciliation or explicit review disposition.
- P08-CMP-001: P08-T02; `grant_ref_exact_namespace`; Source field/fingerprint vectors.
- P08-CMP-002: P08-T02; `stored_struct_fields_exact`; Accepted source constructors and round trips.
- P08-CMP-003: P08-T02; `historical_and_current_links`; Historical/malformed/self-link corpus.
- P08-CMP-004: P08-T02; `p01_id_128_129_256_257`; ASCII/non-ASCII/overflow boundaries.
- P08-CMP-005: P08-T13; `gate2_history_no_downgrade`; All generic writer call-site audit.
- P08-INV-001: P08-T05; `fixed_installation_replacement`; Exact install image/modes/digests.
- P08-INV-002: P08-T05; `sudo_args_env_proxy_rejected`; Exact sudo/plugin/policy qualification.
- P08-INV-003: P08-T05; `peer_pidfd_credentials_inheritance`; Real kernel transport tests.
- P08-INV-004: P08-T06; `h1_pause_restart_h2_busy`; Real lock owner-death/delayed helper proof.
- P08-INV-005: P08-T06; `all_15_opcode_guards`; Independent request/response corpus.
- P08-INV-006: P08-T06; `timeout_live_helper_blocks`; Live helper and blocked I/O proof.
- P08-GEN-001: P08-T07; `proposal_journal_plan_acyclic`; Ordered call graph and fault trace.
- P08-GEN-002: P08-T07; `proposal_expiry_burn_conflict`; High-water/orphan/restart vectors.
- P08-GEN-003: P08-T07; `opcode_vocabulary_and_schemas`; Closed schema/phase cross-check.
- P08-GEN-004: P08-T08; `staged_no_startup_side_effect`; Real OTP caller/startup tests.
- P08-GEN-005: P08-T08; `recovery_partial_rows_exact`; Every pending/row/metadata sync fault.
- P08-GEN-006: P08-T08; `recovery_activation_current_closed`; Restart/owner replacement traces.
- P08-EVD-001: P08-T03; `canonical_reject_corpus`; Independent Rust/Elixir vectors.
- P08-EVD-002: P08-T03; `all_record_fields_closed`; Unknown/missing/duplicate field vectors.
- P08-EVD-003: P08-T03; `golden_generation_and_revision`; Independent digest calculations.
- P08-EVD-004: P08-T06; `immutable_publish_crash_windows`; Filesystem/reset matrix.
- P08-EVD-005: P08-T09; `replacement_and_missing_history`; Actual process/fs/device fixtures; integrated coverage deferred.
- P08-EVD-006: P08-T10; `forged_ref_index_object`; Producer/profile/index mismatch corpus.
- P08-REL-001: P08-T11; `owner_epoch_receipt_forgery`; Captured caller/monitor/name replacement tests.
- P08-REL-002: P08-T12; `resource_verification_exact_revision`; Qualified fence/absence proof and forbidden transition tests.
- P08-REL-003: P08-T13; `attempt_release_preparation_bound`; A response-loss and forged commit tests.
- P08-REL-004: P08-T14; `release_order_resource_ack_first`; Call-order trace and both complete_release variants.
- P08-REL-005: P08-T14; `released_a_missing_completion_denied`; Enumerated admission reader matrix.
- P08-REL-006: P08-T14; `release_all_crash_boundaries`; Reset/fault evidence, no global atomicity claim.
- P08-REC-001: P08-T08; `dirty_dets_needs_repair`; Qualified OTP read-only and unchanged-file proof.
- P08-REC-002: P08-T08; `readonly_reopen_replacement`; Competing opener and inode/row replacement tests.
- P08-REC-003: P08-T08; `legacy_pending_no_journal`; No bypass through staged caller authorization.
- P08-QUA-001: P08-T15; `quarantine_no_ack_release`; Lifecycle and mirror-failure matrix.
- P08-QUA-002: P08-T15; `decision_wrong_scope_revoked_replay`; Provisioning/consumption/reset proof.
- P08-QUA-003: P08-T15; `known_incomplete_restart_sticky`; Immutable predecessor and resolution tests.
- P08-DIA-001: P08-T16; `flood_inherited_writer_cancel`; Real pipes/processes and peak measurements.
- P08-DIA-002: P08-T16; `synthetic_secret_all_host_sinks`; Host-only synthetic-secret corpus; integrated deferred.
- P08-DIA-003: P08-T16; `event_gap_snapshot_race`; Gap/overflow/disconnect/reread race tests.
- P08-DIA-004: P08-T16; `diagnostic_terminal_meanings`; All diagnostic transition tests.
- P08-QUAL-001: P08-T17; `limits_boundary_and_saturation`; Exact-host peak/time/capacity measurements.
- P08-QUAL-002: P08-T04; `locked_build_identity`; Independent clean build/SBOM/reproducibility review.
- P08-QUAL-003: P08-T17; `runner_capability_reset_isolation`; Approved image/privilege/controller evidence.
- P08-QUAL-004: P08-T17; `aggregate_missing_privileged_denied`; Exact-head job graph/results and checkout proof.
- P08-QUAL-005: P08-T17; `claim_scope_ob025_not_closed`; Independent acceptance decision and retained artifacts.

All 49 specification requirements have a primary task and named test/proof mapping. The historical R4 attachment export mismatch, native dependency/toolchain closure, approved issuer/installer enrollment, runner/image/controller, sudo/kernel behavior, measured numerical profile and every executed qualification result remain external evidence prerequisites. No implementation result is claimed. Later P02/P03/P04/P09 and integrated OB-025 evidence remain deferred.

Next permitted action is independent Master Gate review of the two local drafts. Neither document is accepted or executable authority merely because it exists.

## v0.3 targeted correction tasks and evidence

This revision retains 49 requirements, 18 tasks and 15 opcodes. Specification section 13 extends the existing requirement-to-task proofs; it introduces no new architectural choice. T05/T06 implement handoff transport/root guards, T11 the exact initial I restriction, T14 the terminal evidence-only transaction, T15 the governed existing-epoch provisioning handoff, and T16 the trusted diagnostic-policy registry. T17 must include all of those tests before exact-candidate certification. T18 remains read-only and adds no tests or files.

The installer is the already selected separately authorized root administrative principal, not a new runtime component. T15 adds disposable-host provisioning fixtures to its existing native quarantine tests; T16 adds policy-installation fixtures to its diagnostic-policy tests. No production daemon, installer side effect during ordinary tests, new opcode or generic command entry point is permitted. Pure tests build canonical records from static fixtures; real ownership/lock/sudo/filesystem/clock behavior is proved only on the separately approved host. Native modules added in these tasks use the existing crate/dependency identity and qualification gates.

Before T17 freezes the candidate, inject every section 6.17a/6.18/7.1b crash point with both persisted outcomes, including split DETS row/head/history results. Record actual E reachability, I contents, R/A byte commitments, generation and denied admission. Repeat recovery without rewriting evidence. An expired handoff cannot extend evidence freshness. A missing policy cannot become NOT_APPLICABLE. Failed installer provisioning, a surviving old helper and conflicting historical index bytes must remain blocked. Static limit tests include all section 13 candidate additions; qualified measurement evidence must bind those same values and exact source/binary/profile digests.

Original-file acceptance remains separate from these document edits. Deliver the two original Markdown files and calculate hashes over their raw bytes, then independently verify the downloaded files before freezing an accepted digest. Text exports do not satisfy that gate. No tests, CI, native execution or privileged operations are authorized by this plan revision.

## Targeted v0.4 correction and review order

Specification section 6.5a defines the explicit initial ReleaseRecord.authorization_sha256 consumption field, its root-head commit boundary and conservative uncertain-write recovery. T06 implements root publication/history guards and T14 integrates interrupted-acquisition tests before T15's terminal-evidence resolution tests. T15 now declares T14 as a prerequisite. T17 includes all added consumption tests before exact-candidate CI; T18 remains read-only. Diagnostic policy qualification uses the single closed QualificationClaim schema. No production P01 type changes, new requirements, tasks or opcodes are introduced.

The original v0.3 Markdown-file identities were independently verified by Master Gate. This revision supplies new raw-file hashes for independent verification and acceptance; it does not inherit acceptance from those older identities. Only the two documentation artifacts may be edited under current authority. Tests, CI, native/privileged execution, publication and implementation remain separately unauthorized.

## Targeted v0.5 correction and dependency order

Section 6.5b selects a nonnull initial pre_snapshot_sha256 from before_resource.snapshot_sha256, with captured-boundary authoritative R provenance and exact post-I snapshot validation. T06 implements native guards; T11 constructs the separate I digest and receipt; T14 exercises mismatch, missing-I and crash boundaries using the real T16 diagnostic-eligibility implementation. T14 now depends explicitly on T16; T15 continues to depend on T14. Numeric task names do not override declared dependencies. T17 runs only after these tasks; T18 remains read-only.

restrict_release returns root_restriction_sha256, the initial immutable ReleaseRecord digest. I returns index_restriction_digest and uses index_restriction_sha256 in its closed receipts. These values and the root-head digest are distinct and cannot be substituted. Current closed-record validation uses P08-SPEC-0.7 and rejects unsupported proposed historical encodings. The specification defines all semantics; this plan adds no independent contract. The 49 requirements, 18 tasks and 15 opcodes remain unchanged. Only these two local documentation artifacts are currently authorized for editing; no CI, tests, privilege, publication or implementation follows.

## Targeted v0.6 correction and proof ownership

T06 implements RootRestrictionProof return/query and actual root reachability; T11 independently hashes/validates returned bytes through the revised restrict_sync/3 argument and persists the exact history wrapper. No host root-directory access or untyped assertion substitutes for that contract. T14 proves real lost-response/root/I behavior after its existing prerequisites. T11's quarantine_evidence_index_repair_fixture uses static explicitly identified terminal fixtures and cannot claim full integration; quarantine_evidence_index_repair belongs to T14 after its real producer exists. No cyclic dependency is added.

T05/T06 implement durable QUIESCENT before acknowledgement, bounded transport teardown and no subsequent application writes. T15 tests handoff provisioning/adoption only after actual exclusive lock acquisition; durable QUIESCENT or an acknowledgement alone never proves helper exit. T17 includes all new tests before candidate certification; T18 remains read-only. Specification sections 6.5c/6.16a define every semantic change. The 65,536-byte proof and entire response bounds require the existing static-limit/qualified-host measurements; no profile is qualified by this document edit.

The previous original-file identity hold is resolved for v0.5. The new exact v0.6 originals still require independent byte verification. Only these two documentation artifacts were authorized for revision. Acceptance, implementation, tests, privileged proof, CI and publication remain separate decisions.

## Targeted v0.7 active-session read path

Specification section 6.13a authorizes query_settlement in the already authenticated release session under the held root lock. T06 implements this permission with all existing owner/G/session/sequence/head guards. T11 implements the non-deadlocking public restrict_sync wrapper: private I write/sync/reread, boundary-owned native query, then private I confirmation/reread before outer success. The existing NativeClient module implements query_settlement_sync/3 with fixed namespace session ownership and a closed query request. No new opcode, task, helper, native lock or persistent authority record is added.

T14 implements real post-I-sync E reread and bracketed E/I/R/A rereads before record_completion and again before settle. T11's native-client fixture can prove wrapper ordering only; real channel/lock and complete-release evidence belong to T14 under separately authorized host proof. Tests cover changed heads, lost query responses, absent required reads, stale JointRead reuse, second-helper contention and owner-deadlock prevention. T17 includes all of these before final candidate certification; T18 remains read-only. Added queries consume existing frame/request/time budgets and must be measured within the still-unqualified numerical profile. At exhaustion, stop blocked rather than skip a mandatory read.

The plan remains bound to the exact v0.7 specification digest above. The 49 requirements, 18 tasks, acyclic dependency order and 15-operation vocabulary are unchanged. Original v0.7 Markdown bytes require independent re-review. CI, tests, implementation, privilege, publication and Gate 2 activation remain unauthorized.
