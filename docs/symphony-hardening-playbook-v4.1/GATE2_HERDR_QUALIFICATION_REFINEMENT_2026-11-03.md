# Gate 2 Herdr qualification refinement, 2026-11-03

## Authority, scope and provenance

This document persists the supplied Master Gate acceptance of Herdr reference research
and the resulting mandatory Gate 2 qualification refinements. The research investigation
is complete. This is supplemental qualification authority, not a replacement for the
canonical implementation plan. The supplied decision, not a GitHub merge, CI result,
research recommendation or machine projection, selects these requirements.
No separate decision identifier or exact decision timestamp was supplied; none is invented.

This documentation candidate awaits independent Master Gate review and human merge.
It does not claim implementation, qualification or Gate 2 acceptance. The selected
refinements become mandatory when their target packages are implemented and reviewed;
they are not optional suggestions and do not authorize implementation now.

Read this document beneath the [V4.1 Master Roadmap](V4_1_MASTER_ROADMAP.md),
[Unified Execution Roadmap](../SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md),
[canonical Gate 2 plan](../superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md),
[immutable freeze packet](GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json),
and [scanner governance addendum](GATE2_SCANNER_GOVERNANCE_ADDENDUM_2026-11-03.md),
[policy](GATE2_V1_CANDIDATE_VALIDATION_1.0.0.json) and
[scanner projection](GATE2_SCANNER_GOVERNANCE_PROJECTION.json).
The [research archive](research/HERDR_GATE2_EVALUATION_2026-11-03.md) is evidence;
the [Herdr projection](GATE2_HERDR_QUALIFICATION_REFINEMENT.json) is a derivative
machine-readable record of this supplied decision. Neither becomes an independent
source of implementation or lifecycle authority.

Symphony remains the sole authority kernel. Herdr-derived machinery may only enforce
or execute a current Symphony decision. It cannot choose work, current RuntimeAttempt,
account/provider identity, legal lifecycle transitions or retries, resource reuse,
candidate acceptance, publication or Done.

## Verified materialization and research baselines

```ini
MAIN_SHA=86336d28671cfd6ac0a55c2ebe48094b8d8a8237
MAIN_TREE=4c362c8800c3ebb75408d1af015184f5beb04d5a
MAIN_PROTECTED=true
REQUIRED_CHECK_1=make-all
REQUIRED_CHECK_1_APP_ID=15368
REQUIRED_CHECK_2=validate-pr-description
REQUIRED_CHECK_2_APP_ID=15368
PLAN_BLOB=bdb2840e5ea4ca8c8912d6cada3287078bbb3c72
PLAN_SHA256=a1d5cdba65c19a09e86ed814a595e8bbae0c9dcfc97afe021ab67826db09ff68
HERDR_REPOSITORY=https://github.com/herdrdev/herdr
HERDR_REF=master
HERDR_SHA=ee5bfb5041bb3e4a49d591c72308aae3c81ecdde
HERDR_TREE=d2fc8428a9ce5be7e1d89a10b62be3e289b479dd
HERDR_PACKAGE_VERSION=0.9.5
HERDR_ROOT_LICENSE=Apache-2.0
```

The archive preserves the accepted research report body byte-for-byte after its
repository header. Its historical statements about then-current authorization and
successor rebinding are observations at research time, not current authorization.
Current programme authorization must be read from live governance. This materialization
does not re-adjudicate G00 rebinding or modify existing separately granted P01 authority.

```ini
SOURCE_REPORT_SHA256=5fcc1dad84e2101e211e12e08e780825ce01056b1b786a60b7088d9d24d905a5
RESEARCH_ARCHIVE_BLOB=af7a3af7907658d9deda3a72bf666ad0016adb95
RESEARCH_ARCHIVE_SHA256=d7ffba65cdb640a7a4e45313667ce20c64d3fe1d5284020722f556b6c14cc892
```

The investigation inspected source and test bodies. Preserve `CONFIRMED_FROM_CODE`,
`CONFIRMED_FROM_DOCS`, `INFERENCE` and `UNKNOWN` distinctions. Herdr was not built
or run, and its tests were not executed by this investigation. An analogous Herdr
test supplies no executed Symphony proof.

## Master Gate disposition

```ini
HERDR_RESEARCH_STATUS=ACCEPTED_AS_REFERENCE_RESEARCH
HERDR_STRATEGY=SELECTIVE_ADAPTATION
HERDR_RUNTIME_INTEGRATION=NO
HERDR_DAEMON_IN_GATE2_TCB=NO
HERDR_DIRECT_CODE_REUSE=NO
HERDR_AUTHORITY_MODEL_REUSE=NO
HERDR_SESSION_MODEL_REUSE=NO
HERDR_AUTHORITY_DELTA=NONE
GATE2_ARCHITECTURE_CHANGE=NO
GATE2_PACKAGE_TOPOLOGY_CHANGE=NO
GATE2_PACKAGE_TOPOLOGY=P01-P09
HERDR_QUALIFICATION_REFINEMENT=YES
```

## Mandatory qualification refinements

### Process incarnation and replacement

```ini
REFINEMENT_ID=G2-HERDR-Q01
NAME=PROCESS_INCARNATION_AND_REPLACEMENT_NEGATIVE_CONTROLS
PRIMARY_TARGET_PACKAGES=P04,P08
SOURCE_PATTERN=M1
IMPLEMENTATION_STATUS=NOT_IMPLEMENTED
QUALIFICATION_STATUS=NOT_PROVEN
```

Required invariants:

- A PID is never sufficient authority for a later signal, wait, termination decision or cleanup verdict.
- After process incarnation has been identified, any authority-reducing operation must use a stable kernel-bound process reference.
- For the selected Linux implementation, use pidfd unless a future implementation proposes an independently justified equivalent and returns to Master Gate for approval.
- PID/start-time remains corroborating identity evidence, not the effect handle.
- The stable handle must bind RuntimeAttempt identity, grant, holder incarnation, boot identity, UID, executable, cgroup, namespace and fence/recovery generation.
- Herdr PID/start-token/session identity is a test/reference source only; it is not the Gate 2 identity mechanism.

Mandatory negative controls:

- actual holder/agent dies while wrapper survives
- PID is reused
- same-kind process replaces old process
- unexpected exec/replacement
- process leaves expected process/session/cgroup identity
- suspended/background process exits or changes
- stale observation followed by attempted signal/wait/cleanup

Expected failure disposition:

- replacement/stale identity is never treated as current authority
- mismatch reduces authority
- uncertain termination/ownership requires fencing, cleanup_unverified and quarantine/block-reuse as applicable

Herdr source/test references at the pinned commit, inspected but not executed:

- `src/platform/linux.rs::process_start_token`
- `src/platform/linux.rs::live_pane_process_group`
- `src/pane/background_agent.rs::AgentJobTracker`
- `src/platform/mod.rs::live_pane_process_group_follows_the_agent_process_not_its_job`
- `src/pane.rs::held_agent_pid_reused_by_another_process_reports_exit`

### Explicit event loss and resynchronization

```ini
REFINEMENT_ID=G2-HERDR-Q02
NAME=EVENT_GAP_AND_RESYNCHRONIZATION
PRIMARY_TARGET_PACKAGES=P08
SOURCE_PATTERN=M3
IMPLEMENTATION_STATUS=NOT_IMPLEMENTED
QUALIFICATION_STATUS=NOT_PROVEN
SECONDARY_TARGET=EXISTING_RECONCILIATION_OWNERS
```

Required invariants:

- An event gap, disconnect, owner restart or observation-generation mismatch makes the cached observation STALE.
- A STALE observation cannot authorize an effect, release, cleanup verdict, retry or lifecycle success; a fresh authoritative reread/reconciliation is required.
- Events are wakeups/invalidation hints, never lifecycle authority.
- Do not treat a retained event as authoritative after its owning epoch is invalid.
- Do not add a Herdr-style EventBus subsystem.

Mandatory negative controls:

- retained-history overflow
- event gap
- disconnect/reconnect
- owner restart
- cursor/recovery-generation mismatch
- event arriving during snapshot/reread acquisition
- partial event history

Expected failure disposition:

- mark cached observation STALE and reject authority-dependent use
- require fresh authoritative reread/reconciliation
- never consume partial event history as complete truth

Herdr source/test references at the pinned commit, inspected but not executed:

- `src/api/event_hub.rs::events_after_checked`
- `src/api/subscriptions.rs::poll_batch`
- `src/api/subscriptions.rs::ActiveAgentStatusChangedSubscription::poll_snapshot`
- `src/api/server/subscription_socket_tests.rs::subscriptions_report_history_loss_before_sending_a_partial_stream`

### Observer and readiness before external effect

```ini
REFINEMENT_ID=G2-HERDR-Q03
NAME=PRE_EFFECT_OBSERVER_AND_READINESS_ORDERING
PRIMARY_TARGET_PACKAGES=P04
SOURCE_PATTERN=M2
IMPLEMENTATION_STATUS=NOT_IMPLEMENTED
QUALIFICATION_STATUS=NOT_PROVEN
```

Required invariants:

- Required effect order: durable intent; operation identity fixed; required observer/readiness established; possible-effect acknowledgement boundary; external invocation; attributable observation/reconciliation.
- Observer/readiness failure before effect means NO EFFECT.
- Stale or earlier completion CANNOT satisfy the new operation.
- A possible effect with a lost result remains ambiguous; NO blind replay.
- This supplements the existing ProviderRequestRecord/effect ledger and does not replace durable intent or possible-send recording.
- Do not adopt Herdr terminal prompt/wait semantics.

Mandatory negative controls:

- observer creation fails before submission
- readiness setup fails before submission
- stale pre-existing idle/completion state
- wrong operation identity
- earlier unrelated completion
- result lost after possible effect

Expected failure disposition:

- observer/readiness failure before effect produces no external effect
- reject stale, wrong-operation or unrelated completion
- retain possible-effect ambiguity and reconcile without blind replay

Herdr source/test references at the pinned commit, inspected but not executed:

- `src/app/api/agents.rs::handle_deferred_agent_api_request`
- `src/app/api/agents.rs::agent_prompt_waiter_spawn_failure_fails_before_submitting`
- `src/api/wait.rs::prompt_agent`
- `src/api/wait.rs::agent_wait_identity_matches`

### Bounded cancellable diagnostic drainage

```ini
REFINEMENT_ID=G2-HERDR-Q04
NAME=BOUNDED_CANCELLABLE_DIAGNOSTIC_DRAINAGE
PRIMARY_TARGET_PACKAGES=P08
SOURCE_PATTERN=M5
IMPLEMENTATION_STATUS=NOT_IMPLEMENTED
QUALIFICATION_STATUS=NOT_PROVEN
```

Required invariants:

- Keep retained memory bounded; continue drainage of excess where required.
- Bound cancellation/termination and prevent deadlock merely because a diagnostic pipe filled.
- Represent truncation and incomplete observation explicitly.
- TRUNCATED != COMPLETE_EVIDENCE
- PIPE_EOF != PROCESS_CLEAN
- CHILD_REAPED != RESOURCE_CLEAN
- BOUNDED_DRAINAGE != SECRET_REDACTION
- Synthetic-secret qualification remains separately mandatory.
- No Herdr SSH subsystem is adopted.

Mandatory negative controls:

- simultaneous stdout/stderr flood
- output exceeds retained limit
- descendant retains inherited pipe writer
- child exits while writer remains
- cancellation while pipe blocked
- timeout while pipe blocked
- owned child must still be reaped

Expected failure disposition:

- record explicit TRUNCATED, CANCELLED or INCOMPLETE outcomes as applicable
- do not promote truncated or incomplete diagnostics to complete evidence
- retain process/resource cleanup obligations independently of EOF or child reaping
- apply separate secret-disclosure and quarantine policy when required

Required diagnostic acquisition lifecycle:

Each row defines a transition contract. The final column gives terminal meaning
for terminal destinations and the current meaning for nonterminal destinations.
All transitions belong to the trusted diagnostic collector under a current
Symphony decision; this lifecycle supplies no new execution authority.

| Transition | Owner | Guard | Side effect | Failure transition | Restart interpretation | Terminal/current meaning |
|---|---|---|---|---|---|---|
| OPEN -> CAPTURING | Trusted diagnostic collector under the current Symphony decision. | A qualified bounded channel and current acquisition identity/readiness are established. | Begin bounded concurrent drainage of all required streams. | INCOMPLETE if setup, collector or channel state cannot be established. | Interrupted acquisition becomes INCOMPLETE on recovery; restore no capture authority. | Nonterminal acquisition has begun; no complete-evidence or cleanup claim exists. |
| CAPTURING -> CLOSED | Trusted diagnostic collector under the current Symphony decision. | All required streams reached qualified completion without truncation or incompleteness; completion metadata can be durably finalized. | Finalize and persist capture metadata with an untruncated transport-completion disposition. | INCOMPLETE if completion, attribution or metadata persistence is uncertain. | Retain CLOSED only from durable qualified completion facts; missing or ambiguous facts produce an INCOMPLETE recovered observation. Restore no capture authority. | Terminal capture-transport completion only. Evidence eligibility still requires its independent qualification and attribution checks; process/resource cleanup is not established. |
| CAPTURING -> TRUNCATED_DRAINING | Trusted diagnostic collector under the current Symphony decision. | The retained-byte bound is reached. | Record truncation, stop retaining additional payload, and continue bounded drainage where required. | INCOMPLETE if drainage, bounds, truncation recording or collector state becomes uncertain. | Retain the truncation fact and mark interrupted acquisition INCOMPLETE; do not resume capture or restore authority. | Nonterminal transport handling continues; diagnostic evidence is truncated and cannot be complete evidence. |
| TRUNCATED_DRAINING -> CLOSED | Trusted diagnostic collector under the current Symphony decision. | Drainage reaches qualified termination and the TRUNCATED disposition can be durably finalized. | Persist final transport metadata and the sticky TRUNCATED disposition. | INCOMPLETE if termination or disposition persistence cannot be verified. | Retain CLOSED with TRUNCATED only from durable facts; uncertainty produces an INCOMPLETE recovered observation while preserving known truncation. Never promote truncated output to complete evidence. | Terminal transport handling is complete; evidence remains truncated. CLOSED does not erase truncation or establish process/resource cleanup. |
| CAPTURING, TRUNCATED_DRAINING -> CANCELLED | Trusted diagnostic collector under the current Symphony decision. | The trusted owner issues a cancellation/deadline decision under the qualified bounded contract. | Cancel/drain and reap the owned child according to the collector ownership contract; persist cancellation and any prior truncation. Scope cleanup remains separately verified. | INCOMPLETE if the bounded cancellation/drain/reap contract or disposition persistence cannot be established; retain unresolved cleanup obligations. | Preserve CANCELLED and any known truncation. Uncertain recovery facts remain INCOMPLETE; restart must never reinterpret cancellation as CLOSED or complete evidence. | Terminal diagnostic acquisition was cancelled and is never complete evidence. Cancellation does not certify process/resource cleanliness. |
| OPEN, CAPTURING, TRUNCATED_DRAINING -> INCOMPLETE | Trusted diagnostic collector under the current Symphony decision. | Any nonterminal observation, channel or collector state becomes uncertain, including an interrupted acquisition discovered on restart. | Record an explicit incomplete disposition, preserve known truncation/cancellation facts, and retain unresolved resource obligations. | Remain INCOMPLETE on persistence/recovery failure; block evidence use and apply existing cleanup uncertainty/quarantine rules as applicable. | Preserve INCOMPLETE and restore no capture authority. Do not reinterpret it as CLOSED or complete evidence. | Terminal acquisition cannot satisfy an evidence requirement. A fresh qualified observation with current authorization and a new acquisition identity is required. |

Terminal/restart contract:

- CLOSED records capture transport termination, not a process/resource cleanup verdict or an automatic complete-evidence verdict.
- TRUNCATED, CANCELLED and INCOMPLETE facts cannot be erased by closure or restart. Evidence completion must not be inferred from a transport state.
- No acquisition authority is restored. A new acquisition requires a fresh acquisition identity and current Symphony authorization; it cannot relabel a prior terminal record.

Herdr source/test references at the pinned commit, inspected but not executed:

- `src/remote/process.rs::read_output`
- `src/remote/process.rs::CancellablePipe`
- `src/remote/process.rs::wait_with_output_limit`
- `src/remote/process.rs::diagnostic_capture_drains_flooded_pipes_with_bounded_memory`
- `src/remote/process.rs::child_exit_drains_output_without_waiting_for_inherited_pipes`

### Resource replacement during cleanup

```ini
REFINEMENT_ID=G2-HERDR-Q05
NAME=RESOURCE_REPLACEMENT_CLEANUP_NEGATIVE_CONTROLS
PRIMARY_TARGET_PACKAGES=P02,P08
SOURCE_PATTERN=M4
IMPLEMENTATION_STATUS=NOT_IMPLEMENTED
QUALIFICATION_STATUS=NOT_PROVEN
```

Required invariants:

- Observe authorized object A at locator X; object A disappears or moves; replacement object B appears at locator X; cleanup reaches locator X.
- DO NOT delete B.
- DO NOT certify A absent merely from locator state.
- Cleanup authority comes from stable Symphony allocation/ownership identity, not path equality.
- Do not copy Herdr path-based compare-and-remove into a security-critical cleanup boundary.

Mandatory negative controls:

- authorized object A at locator X disappears or moves before cleanup; replacement B occupies X
- replacement of workspace root
- replacement of backing image
- replacement of loop device
- replacement of filesystem/mount identity
- replacement of temporary/materialization object
- replacement of socket
- replacement of candidate-stage locator
- replacement of other stable resource locator where applicable

Expected failure disposition:

- do not delete replacement B
- do not certify object A absent from locator state alone
- identity mismatch requires cleanup uncertainty and quarantine/block reuse

Herdr source/test references at the pinned commit, inspected but not executed:

- `src/ipc.rs::SocketFileIdentity`
- `src/ipc.rs::socket_file_identity`
- `src/ipc.rs::remove_socket_file_if_owned`
- `src/app/api/worktrees/deferred.rs::handle_api_worktree_remove_finished`

## Explicit architectural rejects

These rejects are specific to Symphony Gate 2. They are not assertions that Herdr is
defective for its intended interactive product. RuntimeAttempt must not receive a
Herdr socket path, equivalent broad control endpoint, endpoint FD, sibling authority
or host orchestration authority. Removing an environment variable alone does not
prove the endpoint is inaccessible.

- `G2-HERDR-R01`: Herdr as Symphony authority kernel.
- `G2-HERDR-R02`: Herdr daemon inside Gate 2 trusted runtime.
- `G2-HERDR-R03`: runtime access to HERDR_SOCKET_PATH or an equivalent broad control endpoint, including endpoint FDs and sibling/orchestration authority.
- `G2-HERDR-R04`: automatic Codex resume.
- `G2-HERDR-R05`: live PTY/process handoff as authority continuity.
- `G2-HERDR-R06`: Git worktrees as isolation.
- `G2-HERDR-R07`: PID/session enumeration as cleanup proof.
- `G2-HERDR-R08`: child exit or PTY close as cleanup proof.
- `G2-HERDR-R09`: Herdr Done/idle/status as Symphony lifecycle authority.
- `G2-HERDR-R10`: shared inherited provider HOME/state.
- `G2-HERDR-R11`: SSH-agent forwarding into RuntimeAttempt.
- `G2-HERDR-R12`: raw terminal history/argv/plugin output as trusted evidence.
- `G2-HERDR-R13`: reconnect as permission to replay ambiguous external effects.
- `G2-HERDR-R14`: Herdr source/worktree operations as CandidateRef/publication replacement.

Restart may restore durable facts, attempt history and unresolved obligations. It
must not restore RuntimeAttempt, provider grant, credential materialization, process
authority or network authority, or infer authority from a surviving/restored session.

## Code reuse and licensing rule

```ini
HERDR_DIRECT_CODE_REUSE_RECOMMENDED=NO
HERDR_DESIGN_REFERENCE_PERMITTED=YES
```

Copying expressive Herdr source requires a separate extraction review before implementation.
That review must record at least:

- Herdr repository
- exact commit/tree
- source paths/symbols/blob identities
- copied ranges
- destination
- changes
- dependencies
- license
- NOTICE/file-specific notices
- test provenance
- qualification evidence

Do not infer that Herdr's root Apache-2.0 declaration covers every vendored dependency.
Retain applicable license, NOTICE and file-specific attribution obligations for the
exact extraction. Design inspiration and source-test reference do not require
bringing Herdr's runtime or dependencies into the trusted computing base.

## Relationship to the canonical Gate 2 plan and P01

```ini
CANONICAL_GATE2_PLAN_CHANGED_BY_THIS_PR=NO
GATE2_ARCHITECTURE_CHANGE=NO
GATE2_AUTHORITY_MODEL_CHANGE=NO
GATE2_PACKAGE_TOPOLOGY_CHANGE=NO
P01_CHANGE_REQUIRED=NO
P01_BLOCKED_BY_HERDR=NO
P01_AUTHORITY_CHANGED_BY_THIS_TASK=NO
```

The five refinements supplement future qualification in the existing P02/P04/P08
packages. P09 must verify, before Gate 2 acceptance, that applicable package evidence
includes the required controls and expected dispositions. Every refinement currently
remains NOT_IMPLEMENTED and NOT_PROVEN. Source review, research acceptance and this
materialization are not test passes or qualification evidence.

A package implementer may satisfy a refinement using a stronger mechanism. It may
not silently omit a control. If satisfying a refinement requires changing frozen
architecture, authority, credential ownership, publication semantics or package
topology, STOP and return to Master Gate. The pidfd-equivalent exception above also
requires Master Gate approval; an implementer cannot waive it locally.

This research does not block, grant, revoke or extend separately authorized P01 work.
No P01 implementation worktree, module or test is changed by this task. The canonical
plan and immutable inventory packet remain byte-identical. The derivative projection
records exact identities for those files and all three scanner-governance artifacts.

## QualityLayer and later synthesis

```ini
QUALITYLAYER_RESEARCH_STATUS=PENDING_MASTER_GATE_REVIEW
QUALITYLAYER_SYNTHESIS_COMPLETE=NO
CANONICAL_PLAN_AMENDMENT_DECISION=DEFER_UNTIL_HERDR_AND_QUALITYLAYER_SYNTHESIS
```

QualityLayer has not yet been synthesized into Gate 2. No QualityLayer conclusion
is asserted here. Its pending review does not block already-authorized P01 work.
When QualityLayer is reviewed, Master Gate will decide whether these documents
remain supplemental authority or whether a consolidated Gate 2 qualification
addendum/canonical-plan revision should be persisted. This task does not make that decision.

## Narrow materialization authority and execution locks

The following authority is limited to this research/governance documentation task.
The CI exception permits only the existing required GitHub Actions CI for this exact
Herdr documentation PR. It permits no local Codex, Herdr, scanner, provider or OAuth
execution. It does not authorize P02/P04/P08/P09 implementation, alter P01 authority,
consume AUTH-07, authorize H-100, pass Gate 2 or authorize merge. Programme-level H-100
authority and these task-specific locks remain separate scopes.

```ini
HERDR_RESEARCH_MATERIALIZATION_AUTHORIZED=YES
CREATE_WORKTREE_AUTHORIZED=YES
CREATE_GOVERNANCE_BRANCH_AUTHORIZED=YES
EDIT_HERDR_RESEARCH_AND_GOVERNANCE_DOCS_AUTHORIZED=YES
LOCAL_DOCUMENT_VALIDATION_AUTHORIZED=YES
COMMIT_HERDR_RESEARCH_DOCS_AUTHORIZED=YES
PUSH_HERDR_RESEARCH_BRANCH_AUTHORIZED=YES
OPEN_HERDR_RESEARCH_PR_AUTHORIZED=YES
HERDR_DOCS_PR_REQUIRED_CI_CODEX_EXECUTION_AUTHORIZED=YES
HERDR_DOCS_PR_REQUIRED_CI_CODEX_SCOPE=EXISTING_REQUIRED_GITHUB_ACTIONS_FOR_THIS_EXACT_HERDR_RESEARCH_GOVERNANCE_DOCUMENTATION_PR_ONLY
LOCAL_CODEX_EXECUTION_AUTHORIZED=NO
HERDR_EXECUTION_AUTHORIZED=NO
SCANNER_EXECUTION_AUTHORIZED=NO
PROVIDER_EXECUTION_AUTHORIZED=NO
OAUTH_EXECUTION_AUTHORIZED=NO
H100_EXECUTION_AUTHORIZED=NO
P02_IMPLEMENTATION_AUTHORIZED=NO
P04_IMPLEMENTATION_AUTHORIZED=NO
P08_IMPLEMENTATION_AUTHORIZED=NO
P09_IMPLEMENTATION_AUTHORIZED=NO
AUTH_07=SUSPENDED_UNCONSUMED
AUTH_07_CONSUMED=NO
MERGE_AUTHORIZED=NO
GATE_2_STATUS=INCOMPLETE
```

Independent Master Gate review is required. Merge remains human-only and is not
authorized by this materialization.
