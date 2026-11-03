# Gate 2 V1 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans only after a separate Master Gate implementation authorization. Steps use checkbox (`- [ ]`) syntax for tracking. This document grants no execution authority.

**Goal:** Implement the accepted Gate 2 reference topology through nine dependency-ordered packages after governance persistence, successor-baseline verification and explicit implementation authorization.

**Architecture:** Symphony remains the sole authority kernel. A trusted host attempt boundary owns resources, credentials, containment, semantic operations, source publication, validation, evidence and cleanup. The integrity-checked Codex app-server processes untrusted model input inside that boundary.

**Tech Stack:** Existing Elixir/OTP and DETS; proposed Rust native host helpers; Linux ext4/loop, namespaces, cgroup v2, AppArmor, seccomp and nftables; libsodium XChaCha20-Poly1305; pinned patched Codex 0.162.1 and reqwest 0.12; SIWC OAuth and Responses; Plane and GitHub host adapters.

**Governing spec:** [Original immutable freeze](../../symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json), [freeze acceptance](../../symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_ACCEPTANCE_2026-11-02.md), [Master Gate scanner addendum](../../symphony-hardening-playbook-v4.1/GATE2_SCANNER_GOVERNANCE_ADDENDUM_2026-11-03.md), and [candidate-validation policy 1.0.0](../../symphony-hardening-playbook-v4.1/GATE2_V1_CANDIDATE_VALIDATION_1.0.0.json), subordinate to the [V4.1 Master Roadmap](../../symphony-hardening-playbook-v4.1/V4_1_MASTER_ROADMAP.md) and [Unified Execution Roadmap](../../SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md).

**Status:** Complete canonical plan, approved by the Master Gate at planning level. This materialization incorporates the accepted A–O report, all accepted contract replacements and the TLS-fallback review requirement. No chat transcript or superseded report is needed to interpret it. G00 is a candidate until independent review, human merge, exact post-merge verification and applicability rebinding.

**Authority scopes:** The separate G00 documentation authorization permits materializing, validating, committing, pushing and opening this governance PR. It does not authorize any implementation task or future command in this plan. Only required GitHub Actions for this exact G00 PR may execute the existing pinned Codex CI proof. Local Codex, provider, scanner, P01 and H-100 execution remain unauthorized.

---

## A. Baseline verification

The independently verified planning and G00 starting baseline is:

```ini
REPOSITORY=JCSchoeman96/symphony
MAIN_SHA=c5b29a8417ae1d82db6e438716c1425ad6889761
MAIN_TREE=792c0413b69a5ed4b2f40052c127bfc04f09a5af
MAIN_PROTECTED=true

REQUIRED_CHECK_1=make-all
REQUIRED_CHECK_1_APP_ID=15368
REQUIRED_CHECK_2=validate-pr-description
REQUIRED_CHECK_2_APP_ID=15368
```

The merge has the expected two parents:

```ini
PRE_MERGE_MAIN=62ba70e6fb97373c4a1cb680846aea985fc80d98
REVIEWED_PR_HEAD=3b884dbcf85a5dee4b20baed26f4a0836381f97c
MERGE_TREE_EQUALS_REVIEWED_TREE=YES
```

The committed packet's bytes and canonical hashes were recomputed:

```ini
PACKET_PATH=docs/symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json
PACKET_GIT_BLOB=6cf92dbad8507d4e6c7553392b163fcac02b897d
PACKET_RAW_BYTES=683322
PACKET_RAW_SHA256=a651b1574ec0a186f6b4cd9548787cf9b67009f6692268ce5a8d0669d9d0636a

INVENTORY_SCHEMA_VERSION=G2-INV-2.1
INVENTORY_ENTRY_COUNT=115
OBLIGATION_COUNT=26
LIFECYCLE_COUNT=14
BEARER_PROOF_COUNT=19
EVIDENCE_TRANSFER_CLAIM_COUNT=13

INVENTORY_SHA256=7341b7faae506db873f3aa9915f8c162f2a7ebe284e872e78189f66c6ead5c9c
OBLIGATION_REGISTER_SHA256=c34f145948698ecd474c6ab8194537df4ad3ab8e8ad2c7070cc9ffde9142d686
COMBINED_FREEZE_SHA256=1458bb041215c6268f2c69c01ed4198357e9561fbdc17a62e7288d0817b61911
```

The read-only tree inventory established:

```ini
REGULAR_BLOB_PATHS=333
NONROOT_TREE_PATHS=58
CANDIDATE_ENTRIES_EXCLUDING_ROOT=391
SUM_OF_BLOB_BYTES_BY_PATH=37506911
LARGEST_BLOB_BYTES=30446771
SYMLINK_COUNT=0
GITLINK_COUNT=0
```

The tree counts above describe the pinned baseline, before these governance documents. They are workload measurements, not accepted limits. No scanner PASS or implementation proof is inferred from them. G00 changes governance documents only; existing untracked material is outside this candidate. Local scanner/Codex/OAuth/inference execution is prohibited.

## B. Authority reconciliation

Authority precedence is V4.1 Master Roadmap, accepted Unified Execution Roadmap, accepted repository governance/evidence, freeze acceptance and scoped projection, immutable packet as scoped by the Master Gate scanner amendment, pinned production source, current official external protocol facts, then historical proposals/diagnostics. The selected architecture, nine packages and obligation ownership are frozen.

Symphony alone decides work authority. Native helpers enforce a current Symphony decision; they cannot select work, restore authority, switch subscriptions or authorize completion.

Accepted controls retain their original meaning:

- **H-050D:** privileged Plane/GitHub operations and raw mutation credentials remain host-owned.
- **H-060A:** complete RuntimeAttempt identity and stale-event rejection.
- **H-060B:** restart recovery fails closed and does not restore live authority.
- **H-060C:** workspace destruction requires trusted ownership evidence.
- **H-080B:** accepted Linux isolation properties remain accepted for their exact tested configuration and executable. The new Gate 2 launcher, UID split, storage, egress and patched `0.162.1` require additional qualification.

The later ledger and Unified Roadmap acceptance correction governs H-080B status. Historical candidate wording in its evidence document does not revoke that acceptance.

The Master Gate scanner amendment supplies the previously missing policy authority:

```ini
POLICY_ID=GATE2_V1_CANDIDATE_VALIDATION
POLICY_VERSION=1.0.0
POLICY_OWNER=TRUSTED_HOST_VALIDATOR
SCANNER_EVIDENCE_SCHEMA=G2-SCAN-EVIDENCE-1.0.0

NETWORK_AUTHORITY=NONE
CREDENTIAL_AUTHORITY=NONE
MUTATION_AUTHORITY=NONE
```

It affects OB-015, OB-019, LC-09, LC-10 and the named staging/validator rows. It does not change provider architecture, publication ownership, output class or human merge authority.

The original packet remains immutable. Its historical scanner reference was unbound. Forward use of `SCANNER_POLICY_CHANGED=NO` will mean no semantic change from the accepted policy digest established through G00.

```ini
PROPOSED_SCANNER_IMPLEMENTATION_ID=symphony-g2-validator-rust-v1
SCANNER_IMPLEMENTATION_ID=UNSELECTED
SCANNER_IMPLEMENTATION_AUTHORIZED=NO
```

The proposed identifier does not become accepted merely by appearing here.

The provider contract remains frozen: host-managed SIWC credentials, access held by the selected app-server, public Responses route, no built-in ChatGPT authentication, no refresh RPC and no `/v1/models` requirement. Official documentation supplies external protocol facts, not proof of Symphony enforcement. [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference), [Accounts and sessions](https://developers.openai.com/siwc/token-sharing-open-source/profiles-and-sessions), [Codex app-server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server).

Historical r4, synthetic fixtures and retained traces remain within their original diagnostic or fixture scope. `ProviderObservation` and `ProviderDispatchWitness` remain work-control evidence, not OpenAI inference-effect evidence.

The H-100 programme authorization and this task's prohibition remain separate facts. Neither is rewritten.

## C. Current production seam map

Exact path abbreviations used throughout:

```text
L = elixir/lib/symphony_elixir/
T = elixir/test/symphony_elixir/
D = docs/symphony-hardening-playbook-v4.1/
N = native/gate2/
U = codex-rs/ in the pinned external upstream source
```

A prefixed path means literal concatenation. `N` is proposed new code.

### C1. Attempt authority and recovery

Current files:

```text
L/orchestrator.ex
L/agent_runtime/runtime_attempt.ex
L/agent_runtime/attempt_ledger.ex
L/work_control/recovery_ledger.ex
L/work_control/suspension_context.ex
L/work_control/suspension_recovery.ex
```

Relevant current symbols include:

```text
RuntimeAttempt.Identity.allocate/3, same?/2, valid?/1
AttemptLedger.open/3, current/2, put/2, begin_attempt/3
bind_runtime_attempt/3, release_authority_fence/3
release_suspension_fence/4, clear_in_flight/3, rearm/5
initialize_or_validate/1, initialize_records/2
validate_metadata/2, validate_stored_records/2, persist_safety/4
Orchestrator.allocate_runtime_attempt/4
bind_runtime_attempt_before_spawn/3
release_runtime_fence_after_task_down/3
```

AttemptLedger currently has ledger-wide schema 1. Metadata and all current/history records require that version. Current release validates identity and fence state, not resource cleanliness.

RuntimeAttempt remains volatile. Its `lineage_generation` is an opaque lineage string, not a recovery sequence.

Relevant tests:

```text
T/attempt_ledger_test.exs
T/runtime_attempt_identity_test.exs
T/runtime_attempt_production_path_test.exs
T/orchestrator_startup_reconciliation_test.exs
T/work_control_recovery_ledger_test.exs
T/suspension_recovery_test.exs
```

### C2. Runtime launch and credentials

Current files:

```text
L/agent_runner.ex
L/agent_runtime.ex
L/agent_runtime/codex.ex
L/agent_runtime/runtime_isolation.ex
L/codex/app_server.ex
L/codex/isolation_profile.ex
L/credential_boundary.ex
```

`AppServer.start_routed_local_port/4` launches through `unshare` and a resident Python guard. The guard forks and execs Codex with its environment. `CredentialBoundary.routed_port_env/3` therefore cannot safely carry `ACCESS_TOKEN`.

`RuntimeIsolation.admit/3`, `verify/2` and `evidence/2` own current isolation admission and executable-bound evidence.

Relevant tests include:

```text
T/app_server_test.exs
T/app_server_edge_test.exs
T/agent_runner_isolation_test.exs
T/runtime_isolation_test.exs
T/runtime_isolation_actual_codex_test.exs
T/credential_boundary_test.exs
T/credential_channel_enforcement_test.exs
```

### C3. Workspace

```text
L/workspace.ex
L/workspace/ownership.ex
L/workspace/ownership_ledger.ex
```

Relevant symbols are `create_for_issue`, `revalidate_owned_local_workspace`, `remove_recorded`, `OwnershipLedger.reserve_sync/2` and `transition_sync/4`.

OwnershipLedger establishes trusted ownership. It does not currently establish a new writable instance for every RuntimeAttempt.

Tests:

```text
T/workspace_ownership_test.exs
T/workspace_ownership_ledger_test.exs
T/workspace_and_config_test.exs
```

### C4. Semantic operations

```text
L/codex/dynamic_tool.ex
L/plane/agent_tool.ex
L/plane/adapter.ex
L/transition_coordinator.ex
L/work_control/transition_attempt.ex
L/work_control/transition_attempt_ledger.ex
```

Reuse `agent_tool_specs`, `execute`, `submit_controlled_transition`, `request_transition` and `reconcile_candidate`. TransitionAttemptLedger remains the Plane submit-once ledger.

Tests:

```text
T/plane_agent_tool_test.exs
T/dynamic_tool_test.exs
T/transition_attempt_ledger_test.exs
T/transition_coordinator_test.exs
T/transition_coordinator_crash_windows_test.exs
T/runtime_transition_authority_binding_test.exs
```

### C5. Source verification and completion

```text
L/source_control.ex
L/github/source_control.ex
L/source_control/agent_tool.ex
L/source_control/candidate_ref.ex
L/source_control/candidate_verification.ex
L/source_control/merge_verification.ex
L/work_control/completion_proof.ex
L/work_control/lifecycle_assessment.ex
```

Reuse CandidateRef's immutable five-field identity and SourceControl's fresh candidate/check/review/merge verification. Relevant symbols include `capture_candidate_ref`, `verify_candidate_unchanged`, `verify_required_checks`, `verify_merge`, `durable_candidate_evidence`, `reconcile_stored_evidence`, `with_merge_verification` and `completion_validated?`.

There is no current production publisher, SourceManifest, inference-effect ledger or accepted scanner implementation.

Tests:

```text
T/source_control_agent_tool_test.exs
T/source_control_candidate_ref_test.exs
T/github_source_control_test.exs
T/source_control_github_api_test.exs
T/source_control_merge_verification_test.exs
T/guard_class_source_control_test.exs
T/work_control_assessment_test.exs
```

### C6. Configuration, evidence and CI

```text
L/config.ex
L/config/schema.ex
L/log_file.ex
L/governance/check.ex
elixir/lib/symphony_elixir.ex
.github/workflows/make-all.yml
.github/actions/setup-linux-elixir/action.yml
```

Config is the workflow configuration entry. Governance.Check validates accepted projections. Existing PR CI installs and executes Codex `0.162.1`.

New durable domains remain separate from these existing large modules. Orchestrator coordinates them; it does not absorb their storage, crypto, scanner or reconciliation implementations.

## D. 26/26 obligation coverage matrix

Classification abbreviations:

```text
I=IMPLEMENTATION  C=CONFIGURATION  CH=CHARACTERIZATION
MP=MECHANICAL_PROOF  FI=FAILURE_INJECTION  RP=RECOVERY_PROOF
EB=EVIDENCE_BINDING  IR=INDEPENDENT_REVIEW
NP=NUMERICAL_POLICY_SELECTION  DP=DOCUMENTATION_PERSISTENCE
```

1. **OB-001. primary P02; secondary P01/P08/P09.**
   I/C/MP/RP/EB/IR. Extend H-060C with fresh workspace/resource identity and complete attempt binding. Acceptance requires failed cross-attempt reuse and restart tests.

2. **OB-002. primary P01; secondary P02/P04/P05/P08.**
   I/MP/FI/RP/EB/IR. Reuse identity/fence controls; add durable Gate 2 binding and operation admission. Acceptance requires no legacy release or record-rewrite bypass.

3. **OB-003. primary P01; secondary P06/P08.**
   I/FI/RP/EB/IR. Add resource/recovery records without misusing RecoveryLedger. Acceptance requires stable discovery, fresh recovery generation and ambiguous-owner quarantine.

4. **OB-004. primary P02; secondary P04/P08/P09.**
   I/C/CH/MP/FI/RP/NP/IR. Enforce bounded private storage and account for hidden/open/unlinked/mounted/backing objects. Acceptance requires verified absence or retained quarantine for every class.

5. **OB-005. primary P09; secondary P02/P04/P08.**
   CH/MP/FI/RP/EB/IR. Preserve H-080B and qualify the exact new launcher, patched runtime and host configuration.

6. **OB-006. primary P04; secondary P02/P03/P05/P06/P08/P09.**
   I/C/MP/FI/RP/EB/IR. Close BP-01 through BP-19 with holder/tool separation and synthetic-secret controls. Existing H-050D/H-080B do not supply this proof.

7. **OB-007. primary P03; secondary P01/P09.**
   I/C/MP/RP/EB/IR. Persist independent verified Symphony registrations. Acceptance rejects account/client/host substitution and imported T3Code state.

8. **OB-008. primary P03; secondary P04/P08.**
   I/FI/RP/EB/IR. Serialize refresh and atomically commit replacement credential sets. Acceptance covers every crash point and blocks uncertain rotation.

9. **OB-009. primary P04; secondary P01/P03/P08/P09.**
   I/MP/FI/RP/EB/IR. Fresh grant/materialization/holder/lease per attempt. Token-byte reuse requires prior clean and applicable nondisclosure proof.

10. **OB-010. primary P03; secondary P04/P08.**
    I/C/FI/RP/EB/IR. Persist revoked/uncertain/reauth state without secrets. No implicit account failover or attempt-level browser login.

11. **OB-011. primary P03; secondary P08/P09.**
    I/MP/FI/RP/IR. Validate callback/state/nonce/PKCE/client/OIDC/scopes before registration activation.

12. **OB-012. primary P04; secondary P03/P05/P09.**
    I/C/CH/MP/FI/RP/EB/IR. Enforce exact Responses method/URL, destination lease, TLS, no proxies/redirects and no descendant egress.

13. **OB-013. primary P05; secondary P01/P08/P09.**
    I/C/MP/FI/RP/EB/IR. Bind the five Plane tools to current authority; preserve submit-once and fresh reconciliation.

14. **OB-014. primary P05; secondary P01/P07/P09.**
    I/C/MP/EB/IR. Exact role-bound SourceControl read catalog; reject selectors and unselected adapters.

15. **OB-015. primary P06; secondary P02/P04/P07/P08/P09.**
    I/C/CH/MP/FI/RP/EB/IR. Fence writers, construct SourceManifest/candidate, seal Git-object stage, validate and reconfirm exact identity.

16. **OB-016. primary P06; secondary P01/P05/P07/P09.**
    I/C/MP/FI/EB/IR. Bounded host publisher, host-derived selectors and scoped credentials. Deny protected-base/force/runtime/Reviewer publication.

17. **OB-017. primary P06; secondary P01/P07/P08.**
    I/FI/RP/EB/IR. Separate PublicationLedger, intent before effects, fresh branch/PR reconciliation and no duplicate PR.

18. **OB-018. primary P07; secondary P05/P06/P09.**
    I/MP/FI/RP/EB/IR. Same candidate/tree/policy through checks, independent review, human merge and CompletionProof.

19. **OB-019. primary P06; secondary P02/P07/P08/P09.**
    I/C/MP/FI/EB/IR/DP. Only validated source candidate is durable output. No generic/private-state promotion or scanner-policy bypass.

20. **OB-020. primary P08; secondary P03/P04/P06/P09.**
    I/C/MP/FI/RP/EB/IR. Secret-free logs/crash/temp/evidence with exact attribution and quarantine on possible disclosure.

21. **OB-021. primary P02; secondary P03/P04/P06/P08/P09.**
    C/CH/MP/FI/NP/IR. Enforce bytes/inodes/process/memory/CPU/time/IO/concurrency and aggregate reservations. Missing accepted limits deny admission.

22. **OB-022. primary P09; secondary P01/P03.**
    DP/EB/IR. Preserve topology selection and both H-100 authority scopes.

23. **OB-023. primary P09; secondary every evidence-consuming package.**
    EB/IR/DP. Review ET-001 through ET-013 claim by claim. No historical proof expansion.

24. **OB-024. primary P03; secondary P09.**
    I/MP/EB/IR/DP. Transfer account separation only; reject shared/imported credentials, HOME, sessions and databases.

25. **OB-025. primary P08; secondary P03/P04/P05/P06/P09.**
    I/C/MP/FI/EB/IR. Synthetic-secret proof for diagnostics/config/core/operator evidence.

26. **OB-026. primary P04; secondary P01/P03/P08/P09.**
    I/MP/FI/RP/EB/IR. Dedicated inference-effect record, durable pre-send acknowledgement and unresolved-effect retention without replay.

### D1. Frozen obligation acceptance contracts

The exact frozen records remain requirements. Their scanner wording is scoped only by the governing addendum. The following accounts for every record beyond its title.

**OB-001 acceptance contract.** Primary P02. Inventory: G2-I-02-01, G2-I-02-02, G2-I-02-03.

- `acceptance_owner`: Trusted workspace owner
- `precondition`: Fresh grant and work item
- `authority_basis`: H-060C proves trusted workspace ownership, not fresh RuntimeAttempt writable isolation.
- `existing_evidence`: H-060C; workspace source
- `required_future_control_or_proof`: H-060C proves trusted workspace ownership, not fresh RuntimeAttempt writable isolation.
- `pass_condition`: Attempt-owned writable view binds attempt/generation/responsibility; no prior writer/view reuse.
- `failure_disposition`: Block dispatch; ambiguous ownership quarantined.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-002 acceptance contract.** Primary P01. Inventory: G2-I-01-01, G2-I-01-02, G2-I-01-03.

- `acceptance_owner`: Symphony authority owner
- `precondition`: Current route authorized
- `authority_basis`: RuntimeAttempt is volatile; AttemptLedger fence is durable and bound to its identity.
- `existing_evidence`: RuntimeAttempt/AttemptLedger; H-060A
- `required_future_control_or_proof`: RuntimeAttempt is volatile; AttemptLedger fence is durable and bound to its identity.
- `pass_condition`: All work/resources bind attempt ID, lineage, responsibility; stale events rejected; fence retained until clean proof.
- `failure_disposition`: Reject stale authority; retain fence/quarantine.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-003 acceptance contract.** Primary P01. Inventory: G2-I-01-04, G2-I-01-06, G2-I-15-01, G2-I-15-02, G2-I-15-03, G2-I-15-04.

- `acceptance_owner`: Trusted recovery owner
- `precondition`: Supervisor starts
- `authority_basis`: RecoveryLedger does not restore attempt/PID/token/path; new resource and publication recovery records required.
- `existing_evidence`: RecoveryLedger; H-060B/C
- `required_future_control_or_proof`: RecoveryLedger does not restore attempt/PID/token/path; new resource and publication recovery records required.
- `pass_condition`: Stable identity discovery; known FENCE/RECONCILE/CLEAN/VERIFY; ambiguous QUARANTINE/BLOCK_REUSE.
- `failure_disposition`: No reuse while ambiguous.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-004 acceptance contract.** Primary P02. Inventory: G2-I-03-01, G2-I-03-02, G2-I-03-03, G2-I-03-04, G2-I-03-05, G2-I-03-06, G2-I-03-07, G2-I-03-08, G2-I-03-09, G2-I-03-10, G2-I-03-11, G2-I-03-12, G2-I-03-13, G2-I-03-14, G2-I-03-15, G2-I-03-16.

- `acceptance_owner`: Trusted host attempt boundary
- `precondition`: Attempt allocation
- `authority_basis`: All HOME/XDG/temp/provider state is attempt-private, bounded, nonpromotable; open, deleted, alternate mount, snapshot, backup and swap classes dispositioned.
- `existing_evidence`: CredentialBoundary only sets environment variables
- `required_future_control_or_proof`: All HOME/XDG/temp/provider state is attempt-private, bounded, nonpromotable; open, deleted, alternate mount, snapshot, backup and swap classes dispositioned.
- `pass_condition`: Byte/inode limits owned; all inode/FD/mount/backing refs accounted and verified absent.
- `failure_disposition`: Uncertain cleanup -> quarantine.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-005 acceptance contract.** Primary P09. Inventory: G2-I-04-01, G2-I-04-02, G2-I-04-03, G2-I-04-04, G2-I-04-05, G2-I-04-06, G2-I-04-07, G2-I-04-08, G2-I-04-09, G2-I-04-10, G2-I-04-11, G2-I-04-12.

- `acceptance_owner`: Independent host verifier
- `precondition`: Pinned runtime/config selected
- `authority_basis`: H-080B accepted for 0.159.3; 0.162.1 and selected boundary need bound proof, without revoking H-080B.
- `existing_evidence`: H-080B evidence; current isolation profile
- `required_future_control_or_proof`: H-080B accepted for 0.159.3; 0.162.1 and selected boundary need bound proof, without revoking H-080B.
- `pass_condition`: All descendants/process/cgroup/namespace/network/resource classes observed; proof bound to 0.162.1.
- `failure_disposition`: Uncertain termination -> quarantine.
- `requires_host_privilege`: YES
- `codex_execution_required`: YES
- `provider_execution_required`: NO

**OB-006 acceptance contract.** Primary P04. Inventory: G2-I-05-05, G2-I-05-06, G2-I-05-07, G2-I-05-08, G2-I-08-01, G2-I-08-02, G2-I-08-03, G2-I-08-04, G2-I-08-05, G2-I-08-06, G2-I-08-07, G2-I-08-08, G2-I-08-09, G2-I-12-01, G2-I-12-02, G2-I-12-03, G2-I-12-04, G2-I-12-07.

- `acceptance_owner`: Independent host security reviewer
- `precondition`: Exact executable/config; synthetic non-live secret
- `authority_basis`: LOCAL_BEARER_NONDISCLOSURE=UNVERIFIED; cover child env, proc environ/mem, ptrace, process_vm, systemd credentials, copies, FDs/SCM_RIGHTS, RPC, diagnostics, logs, crash/core/temp, provider request/response, output and semantic tool arguments/results/logs.
- `existing_evidence`: NONE
- `required_future_control_or_proof`: LOCAL_BEARER_NONDISCLOSURE=UNVERIFIED; cover child env, proc environ/mem, ptrace, process_vm, systemd credentials, copies, FDs/SCM_RIGHTS, RPC, diagnostics, logs, crash/core/temp, provider request/response, output and semantic tool arguments/results/logs.
- `pass_condition`: Positive and negative controls show only selected app-server reads access token; refresh remains host-only.
- `failure_disposition`: Known/uncertain disclosure -> CLEANUP_UNVERIFIED -> QUARANTINED -> BLOCK_UNSAFE_REUSE; old token may remain valid.
- `requires_host_privilege`: YES
- `codex_execution_required`: YES
- `provider_execution_required`: NO

**OB-007 acceptance contract.** Primary P03. Inventory: G2-I-05-01, G2-I-05-02, G2-I-05-03.

- `acceptance_owner`: Trusted subscription manager
- `precondition`: Explicit host enrollment
- `authority_basis`: Persist one host registration per existing account/client; preserve verified identity and issued client.
- `existing_evidence`: Official SIWC docs; T3Code analogy only
- `required_future_control_or_proof`: Persist one host registration per existing account/client; preserve verified identity and issued client.
- `pass_condition`: Verified sub/client/host ID/scopes and separate record persist; no T3Code auth.json import.
- `failure_disposition`: Failure leaves registration inactive; no cross-account fallback.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-008 acceptance contract.** Primary P03. Inventory: G2-I-05-04, G2-I-05-05, G2-I-06-02, G2-I-06-03.

- `acceptance_owner`: Trusted credential owner
- `precondition`: Registered token set; refresh due by provider rule
- `authority_basis`: Near-expiry OAuth refresh rotates access+refresh pair; serialize per registration and durably commit replacement before retiring old set.
- `existing_evidence`: Official SIWC accounts/token docs
- `required_future_control_or_proof`: Near-expiry OAuth refresh rotates access+refresh pair; serialize per registration and durably commit replacement before retiring old set.
- `pass_condition`: Replacement generation atomic/recoverable; ambiguous/persist failure blocks dispatch.
- `failure_disposition`: No blind retry; CREDENTIAL_STATE_UNCERTAIN or REAUTH_REQUIRED.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-009 acceptance contract.** Primary P04. Inventory: G2-I-05-06, G2-I-05-07, G2-I-05-08.

- `acceptance_owner`: Trusted grant owner
- `precondition`: Valid selected registration and token claims
- `authority_basis`: Fresh grant/materialization/process per attempt; same upstream value only after prior clean and nondisclosure proof.
- `existing_evidence`: NONE
- `required_future_control_or_proof`: Fresh grant/materialization/process per attempt; same upstream value only after prior clean and nondisclosure proof.
- `pass_condition`: sub/aud/client/scope/iss/iat/exp/jti/nbf valid; prior writers/descendants/FDs/state/network absent; no disclosure.
- `failure_disposition`: Without proof or if suspected exposure, do not reuse; quarantine as required.
- `requires_host_privilege`: YES
- `codex_execution_required`: YES
- `provider_execution_required`: NO

**OB-010 acceptance contract.** Primary P03. Inventory: G2-I-05-09, G2-I-06-06, G2-I-16-01.

- `acceptance_owner`: Trusted subscription manager
- `precondition`: Terminal provider failure or explicit disconnect
- `authority_basis`: Revoked/unusable/ambiguous registration blocks work; operator sees reason/action without token.
- `existing_evidence`: Official SIWC recovery/accounts docs
- `required_future_control_or_proof`: Revoked/unusable/ambiguous registration blocks work; operator sees reason/action without token.
- `pass_condition`: Exception-only reauth; no attempt login and no automatic alternate subscription.
- `failure_disposition`: Block selected registration; local deletion is not remote revocation.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-011 acceptance contract.** Primary P03. Inventory: G2-I-06-01, G2-I-06-04, G2-I-06-05.

- `acceptance_owner`: Trusted subscription manager
- `precondition`: Host-level explicit enrollment/reauth
- `authority_basis`: Host-only SIWC enrollment validates exact callback, state, nonce, PKCE, client, JWKS identity and scope.
- `existing_evidence`: Official SIWC sign-in docs
- `required_future_control_or_proof`: Host-only SIWC enrollment validates exact callback, state, nonce, PKCE, client, JWKS identity and scope.
- `pass_condition`: Only verified token set persists.
- `failure_disposition`: Cancel/mismatch/exchange/identity/persist error leaves registration inactive.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-012 acceptance contract.** Primary P04. Inventory: G2-I-07-01, G2-I-07-02, G2-I-07-03, G2-I-07-04, G2-I-07-05, G2-I-07-06.

- `acceptance_owner`: Trusted network owner
- `precondition`: SIWC Responses config
- `authority_basis`: Permit POST /v1/responses; deny /v1/models, proxy and unrelated egress; OAuth/Plane/GitHub host paths separate.
- `existing_evidence`: Official SIWC endpoint docs; no current egress proof
- `required_future_control_or_proof`: Permit POST /v1/responses; deny /v1/models, proxy and unrelated egress; OAuth/Plane/GitHub host paths separate.
- `pass_condition`: DNS/TLS/route enforcement; descendants no raw sockets; app-server works with models route denied.
- `failure_disposition`: Unexpected endpoint/path -> block and quarantine.
- `requires_host_privilege`: YES
- `codex_execution_required`: YES
- `provider_execution_required`: NO

**OB-013 acceptance contract.** Primary P05. Inventory: G2-I-09-01, G2-I-09-02, G2-I-09-03, G2-I-09-04, G2-I-09-05, G2-I-14-02.

- `acceptance_owner`: Trusted Plane adapter/coordinator
- `precondition`: Current route and authority guard
- `authority_basis`: Typed Plane operations bind current attempt/responsibility; transition uses TransitionAttemptLedger, submit-once and fresh remote read.
- `existing_evidence`: Plane AgentTool/TransitionCoordinator
- `required_future_control_or_proof`: Typed Plane operations bind current attempt/responsibility; transition uses TransitionAttemptLedger, submit-once and fresh remote read.
- `pass_condition`: Bounded args/results; stale attempt rejected; ambiguity reconciled without blind retry.
- `failure_disposition`: Unresolved mutation suspends/escalates.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-014 acceptance contract.** Primary P05. Inventory: G2-I-09-06, G2-I-09-07, G2-I-10-01, G2-I-10-02.

- `acceptance_owner`: Trusted tool binder/SourceControl
- `precondition`: Selected role config
- `authority_basis`: Reviewer tool remains read-only; generic GitHub/API mutations and other adapters denied.
- `existing_evidence`: SourceControl AgentTool
- `required_future_control_or_proof`: Reviewer tool remains read-only; generic GitHub/API mutations and other adapters denied.
- `pass_condition`: Only named read tool appears and is repo/candidate bound.
- `failure_disposition`: Unexpected tool binding blocks dispatch.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-015 acceptance contract.** Primary P06. Inventory: G2-I-02-02, G2-I-11-01, G2-I-11-02, G2-I-11-03, G2-I-11-09.

- `acceptance_owner`: Trusted publisher/validator
- `precondition`: Bound Builder/Fixer handoff
- `authority_basis`: Host candidate construction starts after writers fenced; exact commit/tree receives existing safety scanning; private state excluded.
- `existing_evidence`: Scanner and SourceControl are separate existing responsibilities
- `required_future_control_or_proof`: Host candidate construction starts after writers fenced; exact commit/tree receives existing safety scanning; private state excluded.
- `pass_condition`: No writer survives; same exact tree is resolved, staged, validated and rechecked.
- `failure_disposition`: Fence/validation/identity uncertainty blocks publication.
- `requires_host_privilege`: YES
- `codex_execution_required`: YES
- `provider_execution_required`: NO

**OB-016 acceptance contract.** Primary P06. Inventory: G2-I-04-10, G2-I-11-04, G2-I-11-05.

- `acceptance_owner`: Trusted source-publication owner
- `precondition`: Durable authorized intent and writer fence
- `authority_basis`: Host derives repo/base/branch/PR; candidate branch only; no raw runtime GitHub credential, protected push or force push.
- `existing_evidence`: Supplied INV_SOURCE_PUBLISH_01; H-050D credential boundary
- `required_future_control_or_proof`: Host derives repo/base/branch/PR; candidate branch only; no raw runtime GitHub credential, protected push or force push.
- `pass_condition`: Only nonprotected host-managed branch and work-item PR are mutated.
- `failure_disposition`: Selector/base/repo mismatch rejects publication.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-017 acceptance contract.** Primary P06. Inventory: G2-I-01-06, G2-I-11-06, G2-I-11-07, G2-I-14-04, G2-I-15-03.

- `acceptance_owner`: Trusted publication recovery owner
- `precondition`: Record committed before mutation
- `authority_basis`: Persist publication intent separately from Plane ledger; reconcile push/PR ambiguity by fresh remote read, then capture CandidateRef/tree.
- `existing_evidence`: No current publication record/control
- `required_future_control_or_proof`: Persist publication intent separately from Plane ledger; reconcile push/PR ambiguity by fresh remote read, then capture CandidateRef/tree.
- `pass_condition`: Unique branch/PR association and exact SHA/tree corroborated; no duplicate PR/blind retry.
- `failure_disposition`: Unresolved -> block work item publication and escalate.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-018 acceptance contract.** Primary P07. Inventory: G2-I-10-01, G2-I-10-02, G2-I-10-03, G2-I-10-04, G2-I-10-05, G2-I-10-06.

- `acceptance_owner`: SourceControl, independent reviewer, human merge authority
- `precondition`: Fresh CandidateRef/tree
- `authority_basis`: Same candidate SHA/tree/policy binds checks/review; human exact merge then trusted tree verification.
- `existing_evidence`: Existing SourceControl and V1 human merge authority
- `required_future_control_or_proof`: Same candidate SHA/tree/policy binds checks/review; human exact merge then trusted tree verification.
- `pass_condition`: Any movement invalidates checks/review; merged tree matches candidate; CompletionProof bound.
- `failure_disposition`: No merge/mismatch -> no completion.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-019 acceptance contract.** Primary P06. Inventory: G2-I-03-07, G2-I-03-09, G2-I-11-08, G2-I-11-09.

- `acceptance_owner`: Trusted output owner
- `precondition`: Output request/candidate validation
- `authority_basis`: Only source candidate is durable V1 output; generic files/model text and provider state denied; no scanner changes.
- `existing_evidence`: Supplied output selection
- `required_future_control_or_proof`: Only source candidate is durable V1 output; generic files/model text and provider state denied; no scanner changes.
- `pass_condition`: Only exact validated tree enters GitHub candidate; outside files rejected.
- `failure_disposition`: Reject and keep state private.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-020 acceptance contract.** Primary P08. Inventory: G2-I-12-01, G2-I-12-02, G2-I-12-03, G2-I-12-04, G2-I-12-05, G2-I-12-06, G2-I-12-07.

- `acceptance_owner`: Trusted evidence owner
- `precondition`: Attempt/proof failure
- `authority_basis`: Evidence is nonsecret; stderr/core/temp handled; historical traces stay diagnostic.
- `existing_evidence`: App-server stderr partial; retained trace diagnostic
- `required_future_control_or_proof`: Evidence is nonsecret; stderr/core/temp handled; historical traces stay diagnostic.
- `pass_condition`: Redaction and cleanup evidence binds exact attempt/resource without token content.
- `failure_disposition`: Possible leak quarantines.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-021 acceptance contract.** Primary P02. Inventory: G2-I-02-02, G2-I-03-01, G2-I-03-07, G2-I-03-09, G2-I-04-02.

- `acceptance_owner`: Host capacity and admission owners
- `precondition`: Measured workload and host capacity
- `authority_basis`: Name bound owners for bytes/inodes/process/memory/CPU/time/IO/concurrency; values follow capacity evidence.
- `existing_evidence`: No numeric values selected; not blocker
- `required_future_control_or_proof`: Name bound owners for bytes/inodes/process/memory/CPU/time/IO/concurrency; values follow capacity evidence.
- `pass_condition`: Each boundary enforced; aggregate reserve/admission owner defined.
- `failure_disposition`: Deny admission if unconfigured/exhausted.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-022 acceptance contract.** Primary P09. Inventory: G2-I-01-01, G2-I-16-03.

- `acceptance_owner`: Governance documentation owner
- `precondition`: Governance freeze approval
- `authority_basis`: Selection supplied as authority input; main says H100 active while task lock bars its execution.
- `existing_evidence`: NONE
- `required_future_control_or_proof`: Selection supplied as authority input; main says H100 active while task lock bars its execution.
- `pass_condition`: Later repository record preserves both; task lock remains scope for this task.
- `failure_disposition`: No execution authority inferred.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-023 acceptance contract.** Primary P09. Inventory: G2-I-04-03, G2-I-10-01, G2-I-12-06.

- `acceptance_owner`: Independent governance reviewer
- `precondition`: Future proof plan cites evidence
- `authority_basis`: Historical, synthetic, r4, H080B and provider evidence stay within exact claim/version/topology.
- `existing_evidence`: NONE
- `required_future_control_or_proof`: Historical, synthetic, r4, H080B and provider evidence stay within exact claim/version/topology.
- `pass_condition`: Transfer and non-transfer listed; no historical evidence overstated.
- `failure_disposition`: Reject overbroad transfer.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-024 acceptance contract.** Primary P03. Inventory: G2-I-05-01, G2-I-05-02, G2-I-05-03.

- `acceptance_owner`: Independent reviewer
- `precondition`: Multiple Symphony registrations
- `authority_basis`: Only separate subscription identities coexistence concept transfers; auth files, shared DB/state/env mechanics do not.
- `existing_evidence`: Supplied T3Code operational analogy
- `required_future_control_or_proof`: Only separate subscription identities coexistence concept transfers; auth files, shared DB/state/env mechanics do not.
- `pass_condition`: Symphony-owned independent records; no cross-account client/token mix.
- `failure_disposition`: Reject import/shared state.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

**OB-025 acceptance contract.** Primary P08. Inventory: G2-I-12-01, G2-I-12-02, G2-I-12-03, G2-I-12-05, G2-I-12-07.

- `acceptance_owner`: Trusted host evidence owner
- `precondition`: Selected SIWC app-server and host logging configuration
- `authority_basis`: Existing stderr is only a byte channel; selected architecture requires secret-free redaction/retention and safe crash policy.
- `existing_evidence`: AppServer stderr source; no complete nondisclosure proof
- `required_future_control_or_proof`: Existing stderr is only a byte channel; selected architecture requires secret-free redaction/retention and safe crash policy.
- `pass_condition`: Synthetic secret controls show logs/config/core/operator evidence contain no token or refresh value; exact attempt/resource evidence remains attributable.
- `failure_disposition`: Known or uncertain disclosure -> CLEANUP_UNVERIFIED -> QUARANTINED -> block reuse.
- `requires_host_privilege`: YES
- `codex_execution_required`: YES
- `provider_execution_required`: NO

**OB-026 acceptance contract.** Primary P04. Inventory: G2-I-04-03, G2-I-07-01, G2-I-14-01.

- `acceptance_owner`: Trusted provider-effect evidence owner
- `precondition`: Authorized app-server request and exact RuntimeAttempt grant
- `authority_basis`: Provider request lifecycle requires secret-free local admission/send/response status and request/remote IDs where available; process loss does not prove cancellation.
- `existing_evidence`: No current selected provider-effect ledger
- `required_future_control_or_proof`: Provider request lifecycle requires secret-free local admission/send/response status and request/remote IDs where available; process loss does not prove cancellation.
- `pass_condition`: Record supports ADMITTED_LOCALLY/SENT_UPSTREAM/accepted-if-evidenced/stream/completed/failure/interrupted/ambiguous and safe restart reconciliation.
- `failure_disposition`: Uncertain outcome remains RESULT_AMBIGUOUS; do not infer cancellation or retry blindly.
- `requires_host_privilege`: YES
- `codex_execution_required`: NO
- `provider_execution_required`: NO

### D2. Complete 115-entry inventory crosswalk

Each entry retains every field of its exact frozen record. This crosswalk identifies its implementation owners and lifecycle without sampling or promoting a proposal mapping to production fact. The package acceptance contracts and H–K supply the future controls and proof. All resource/channel distinctions, hidden-copy classes and failure dispositions in each named frozen record remain mandatory.

- **G2-I-01-01** Symphony authorization decision and attempt-generation grant. Packages P01, P09; obligations OB-002, OB-022; lifecycles LC-01, LC-13. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: No grant creation by model. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-01-02** RuntimeAttempt live state. Packages P01; obligations OB-002, OB-003; lifecycles LC-01, LC-13. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: TYPED_METADATA_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-01-03** AttemptLedger authority fence and in-flight safety state. Packages P01; obligations OB-002, OB-003; lifecycles LC-01, LC-13. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: TYPED_METADATA_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-01-04** RecoveryLedger and SuspensionContext. Packages P01; obligations OB-003; lifecycles LC-01, LC-13. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: TYPED_METADATA_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-01-05** TransitionAttempt/TransitionAttemptLedger. Packages P05; obligations OB-013; lifecycles LC-01, LC-11, LC-13. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: TYPED_METADATA_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-01-06** SourcePublicationRecord. Packages P01, P06; obligations OB-003, OB-017; lifecycles LC-01, LC-10, LC-13. Authority owner: TRUSTED_HOST_SOURCE_PUBLICATION_BOUNDARY. Runtime visibility: Typed completion request/result only. Cleanup verification: Fresh GitHub corroboration of repo/base/branch/PR/head/tree. Failure/reuse: Ambiguous mutation -> block publication and escalate.
- **G2-I-01-07** Authorized subscription_registration_id bound to new attempt. Packages P01, P03, P04; obligations OB-002, OB-007, OB-009; lifecycles LC-01, LC-06, LC-07, LC-13. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: Nonsecret registration reference only. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-02-01** Workspace OwnershipLedger and ownership lifecycle. Packages P01, P02; obligations OB-001, OB-003; lifecycles LC-01, LC-02. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: TYPED_METADATA_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-02-02** Attempt-fresh writable workspace instance. Packages P02; obligations OB-001, OB-004; lifecycles LC-01, LC-02. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-02-03** Authorized checkout excluding writable .git authority. Packages P02, P06; obligations OB-001, OB-015; lifecycles LC-01, LC-02. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: Builder/Fixer workspace write only; Reviewer/Planner per role config. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-01** Per-attempt HOME. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-02** XDG_CONFIG_HOME and XDG_STATE_HOME. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-03** XDG_DATA_HOME. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-04** XDG_CACHE_HOME and tool/runtime cache. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-05** XDG_RUNTIME_DIR and temp. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-06** Codex provider-private state root. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-07** Codex SQLite main DB. Packages P02, P04, P06; obligations OB-004, OB-006, OB-019; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-08** SQLite SHM. Packages P02, P04, P06; obligations OB-004, OB-006, OB-019; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-09** SQLite WAL. Packages P02, P04, P06; obligations OB-004, OB-006, OB-019; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-10** Codex sessions, threads, attachments and downloads. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-11** Open-but-unlinked and renamed-but-open files. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-12** Deleted source with live attachment and O_TMPFILE/equivalent. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-13** Bind/alternate mounts, snapshots and backups. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-14** Swap/page-out and in-memory credential copies. Packages P04; obligations OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: TYPED_METADATA_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-03-15** Temporary atomic-write copies and filesystem links. Packages P02, P04; obligations OB-004, OB-006; lifecycles LC-01, LC-03. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: CURRENT_ATTEMPT_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-03-16** Shared caches, image/package layers and host binaries. Packages P02, P09; obligations OB-004, OB-005; lifecycles LC-01, LC-03. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: READ_ONLY_OR_DENIED. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-04-01** Symphony Orchestrator/authority owner. Packages P01; obligations OB-002, OB-003; lifecycles LC-01, LC-13. Authority owner: TRUSTED_HOST. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-02** Trusted attempt launcher/supervisor. Packages P04, P09; obligations OB-005, OB-006, OB-012; lifecycles LC-01, LC-13. Authority owner: TRUSTED_HOST_ENFORCEMENT. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-03** Codex app-server. Packages P04, P09; obligations OB-005, OB-006, OB-009, OB-012; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: UNTRUSTED_MODEL_EXECUTION_WITH_HOST_GRANTED_ACCESS_TOKEN. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-04** Shell/tool descendants. Packages P04, P09; obligations OB-005, OB-006, OB-012; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: UNTRUSTED_CHILD_PROCESS. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-05** Codex child agent if reachable. Packages P04, P09; obligations OB-005, OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: UNTRUSTED_NESTED_AGENT. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-06** Plane semantic adapter/coordinator. Packages P05; obligations OB-013; lifecycles LC-01, LC-13. Authority owner: TRUSTED_HOST_ADAPTER. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-07** SourceControl read/verifier. Packages P05, P07; obligations OB-014, OB-018; lifecycles LC-01, LC-13. Authority owner: TRUSTED_HOST_VERIFIER. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-08** SIWC credential and renewal owner. Packages P03; obligations OB-007, OB-008, OB-010, OB-011; lifecycles LC-01, LC-04, LC-05, LC-13. Authority owner: TRUSTED_HOST_CREDENTIAL_OWNER. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-09** Network enforcement owner. Packages P04; obligations OB-012; lifecycles LC-01, LC-13. Authority owner: TRUSTED_HOST_NETWORK_ENFORCEMENT. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-10** Host source-publication owner. Packages P06; obligations OB-015, OB-016, OB-017; lifecycles LC-01, LC-09, LC-10, LC-13. Authority owner: TRUSTED_HOST_SOURCE_PUBLICATION_BOUNDARY. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-11** Output safety validator/scanner. Packages P06; obligations OB-015, OB-019; lifecycles LC-01, LC-13. Authority owner: TRUSTED_HOST_VALIDATOR. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-04-12** Recovery/evidence verifier. Packages P01, P08; obligations OB-003, OB-020; lifecycles LC-01, LC-13, LC-14. Authority owner: TRUSTED_HOST_RECOVERY. Runtime visibility: ROLE_SCOPED. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-05-01** Persistent SIWC subscription registration per account. Packages P03; obligations OB-007, OB-010, OB-024; lifecycles LC-04, LC-05. Authority owner: TRUSTED_HOST_CREDENTIAL_OWNER. Runtime visibility: DENIED. Cleanup verification: Identity/client/scope/generation and persisted set verified. Failure/reuse: Uncertain rotation/disclosure -> block registration.
- **G2-I-05-02** Verified provider account identity per registration. Packages P03, P04; obligations OB-007, OB-009, OB-024; lifecycles LC-04, LC-05. Authority owner: TRUSTED_HOST_CREDENTIAL_OWNER. Runtime visibility: DENIED. Cleanup verification: Identity/client/scope/generation and persisted set verified. Failure/reuse: Uncertain rotation/disclosure -> block registration.
- **G2-I-05-03** Stable HOST_ID and issued CLIENT_ID. Packages P03; obligations OB-007, OB-011; lifecycles LC-04, LC-05. Authority owner: TRUSTED_HOST_CREDENTIAL_OWNER. Runtime visibility: DENIED. Cleanup verification: Identity/client/scope/generation and persisted set verified. Failure/reuse: Uncertain rotation/disclosure -> block registration.
- **G2-I-05-04** Credential-set generation/expiry/rotation/health metadata. Packages P03, P04; obligations OB-008, OB-009; lifecycles LC-05, LC-07. Authority owner: TRUSTED_HOST_CREDENTIAL_OWNER. Runtime visibility: DENIED. Cleanup verification: Identity/client/scope/generation and persisted set verified. Failure/reuse: Uncertain rotation/disclosure -> block registration.
- **G2-I-05-05** SIWC refresh token. Packages P03, P04; obligations OB-006, OB-008, OB-010; lifecycles LC-05, LC-07. Authority owner: TRUSTED_HOST_CREDENTIAL_OWNER. Runtime visibility: DENIED. Cleanup verification: Identity/client/scope/generation and persisted set verified. Failure/reuse: Uncertain rotation/disclosure -> block registration.
- **G2-I-05-06** Access token and documented claims. Packages P04; obligations OB-006, OB-009; lifecycles LC-05, LC-06, LC-07. Authority owner: TRUSTED_HOST_CREDENTIAL_OWNER. Runtime visibility: APP_SERVER_ONLY. Cleanup verification: Identity/client/scope/generation and persisted set verified. Failure/reuse: Uncertain rotation/disclosure -> block registration.
- **G2-I-05-07** Attempt access-token materialization to one app-server. Packages P04; obligations OB-006, OB-009; lifecycles LC-05, LC-06. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: APP_SERVER_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-05-08** Codex app-server credential holder and restart on renewal. Packages P03, P04, P09; obligations OB-005, OB-006, OB-008, OB-009; lifecycles LC-05, LC-06. Authority owner: TRUSTED_HOST_FOR_LIFECYCLE; CODEX_APPSERVER_FOR_ACTIVE_HOLDER. Runtime visibility: YES. Cleanup verification: Host observes containment empty and no live sockets/FDs. Failure/reuse: Unknown descendant/termination -> quarantine.
- **G2-I-05-09** Suspected disclosure, revocation, disconnect, REAUTH_REQUIRED. Packages P01, P03, P04; obligations OB-003, OB-006, OB-010; lifecycles LC-07, LC-14. Authority owner: TRUSTED_HOST_CREDENTIAL_OWNER. Runtime visibility: Nonsecret blocked reason only. Cleanup verification: Identity/client/scope/generation and persisted set verified. Failure/reuse: Uncertain rotation/disclosure -> block registration.
- **G2-I-06-01** Authorization endpoint. Packages P03; obligations OB-011; lifecycles LC-04. Authority owner: TRUSTED_HOST_SUBSCRIPTION_MANAGER. Runtime visibility: DENIED. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-06-02** Token exchange/refresh endpoint. Packages P03; obligations OB-008, OB-011; lifecycles LC-04, LC-05. Authority owner: TRUSTED_HOST_SUBSCRIPTION_MANAGER. Runtime visibility: DENIED. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-06-03** Refresh in-flight/rotation state. Packages P03; obligations OB-008; lifecycles LC-04, LC-05. Authority owner: TRUSTED_HOST_SUBSCRIPTION_MANAGER. Runtime visibility: DENIED. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-06-04** Loopback callback. Packages P03; obligations OB-011; lifecycles LC-04. Authority owner: TRUSTED_HOST_SUBSCRIPTION_MANAGER. Runtime visibility: DENIED. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-06-05** OIDC discovery and JWKS identity validation. Packages P03; obligations OB-011; lifecycles LC-04. Authority owner: TRUSTED_HOST_SUBSCRIPTION_MANAGER. Runtime visibility: DENIED. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-06-06** Revocation channel. Packages P03; obligations OB-010; lifecycles LC-04, LC-05. Authority owner: TRUSTED_HOST_SUBSCRIPTION_MANAGER. Runtime visibility: DENIED. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-07-01** OpenAI Responses endpoint. Packages P04; obligations OB-012; lifecycles LC-06, LC-08. Authority owner: TRUSTED_HOST_NETWORK_ENFORCEMENT. Runtime visibility: App-server only. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-07-02** OpenAI live model catalog. Packages P04; obligations OB-012; lifecycles LC-06, LC-08. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: App-server only. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-07-03** DNS for model host. Packages P04; obligations OB-012; lifecycles LC-06, LC-08. Authority owner: TRUSTED_HOST_NETWORK_ENFORCEMENT. Runtime visibility: DENIED_OR_TYPED_RESULT_ONLY. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-07-04** Provider TLS validation. Packages P04; obligations OB-012; lifecycles LC-06, LC-08. Authority owner: TRUSTED_HOST_NETWORK_ENFORCEMENT. Runtime visibility: DENIED_OR_TYPED_RESULT_ONLY. Cleanup verification: Host observes permitted route only and no old socket. Failure/reuse: Unknown egress/live socket -> quarantine.
- **G2-I-07-05** Proxy path. Packages P04; obligations OB-012; lifecycles LC-06, LC-08. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED_OR_TYPED_RESULT_ONLY. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-07-06** Unrelated attempt Internet. Packages P04; obligations OB-012; lifecycles LC-06, LC-08. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED_OR_TYPED_RESULT_ONLY. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-07-07** Plane host network. Packages P05; obligations OB-013; lifecycles LC-11. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: DENIED_OR_TYPED_RESULT_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-07-08** GitHub read/reconciliation. Packages P05, P07; obligations OB-014, OB-018; lifecycles LC-12, LC-13. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: DENIED_OR_TYPED_RESULT_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-07-09** GitHub publisher network. Packages P06; obligations OB-016, OB-017; lifecycles LC-10, LC-13. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: DENIED_OR_TYPED_RESULT_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-07-10** Host control plane. Packages P09; obligations OB-005; lifecycles LC-01, LC-13, LC-14. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED_OR_TYPED_RESULT_ONLY. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-07-11** Attempt loopback and host-local control endpoints. Packages P04, P09; obligations OB-005, OB-012; lifecycles LC-01, LC-13, LC-14. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-08-01** Host->app-server stdin / JSON-RPC. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: APP_SERVER_VISIBLE. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-08-02** App-server stdout / JSON-RPC result/events. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: HOST_VISIBLE. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-08-03** App-server stderr/diagnostic pipe. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: HOST_ONLY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-08-04** Tool-child stdio and launcher pipes. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: ATTEMPT_BOUND_CHILD_STDIO. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-08-05** Credential materialization channel. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: HOST_TO_ONE_CREDENTIAL_BEARING_APPSERVER. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-08-06** Workspace/output descriptors. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: ROLE_SCOPED_ATTEMPT. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-08-07** Inherited/transferred FD and SCM_RIGHTS. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: UNKNOWN_TRANSFER_DENIED. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-08-08** Pathname/abstract Unix socket and systemd control/notify. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: HOST_ONLY_OR_DENIED_UNLESS_SELECTED. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-08-09** Credential source/materialization copies. Packages P04; obligations OB-006; lifecycles LC-01, LC-06, LC-08, LC-13. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: HOST_SOURCE_AND_ONE_ATTEMPT_COPY. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-09-01** plane_get_current_work_item. Packages P05; obligations OB-013; lifecycles LC-11. Authority owner: TRUSTED_PLANE_ADAPTER. Runtime visibility: Role visible. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-09-02** plane_get_dependencies. Packages P05; obligations OB-013; lifecycles LC-11. Authority owner: TRUSTED_PLANE_ADAPTER. Runtime visibility: Role visible. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-09-03** plane_get_lifecycle_assessment. Packages P05; obligations OB-013; lifecycles LC-11. Authority owner: TRUSTED_PLANE_ADAPTER. Runtime visibility: Role visible. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-09-04** plane_get_authority_disposition. Packages P05; obligations OB-013; lifecycles LC-11. Authority owner: TRUSTED_PLANE_ADAPTER. Runtime visibility: Role visible. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-09-05** plane_request_lifecycle_transition. Packages P05; obligations OB-013; lifecycles LC-11. Authority owner: TRUSTED_PLANE_ADAPTER. Runtime visibility: Role visible. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-09-06** source_control_read_current_candidate_status. Packages P05; obligations OB-014; lifecycles LC-12. Authority owner: TRUSTED_SOURCECONTROL_OR_TOOL_BINDER. Runtime visibility: Role visible. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-09-07** Other adapters/generic API tools. Packages P05; obligations OB-014; lifecycles LC-12. Authority owner: TRUSTED_SOURCECONTROL_OR_TOOL_BINDER. Runtime visibility: DENIED. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-10-01** CandidateRef. Packages P05, P07; obligations OB-014, OB-018; lifecycles LC-10, LC-12. Authority owner: REMOTE_PROVIDER_FOR_FACTS; TRUSTED_HOST_FOR_VERIFICATION. Runtime visibility: Read-only typed facts. Cleanup verification: Fresh host corroboration. Failure/reuse: Mismatch/ambiguity blocks acceptance.
- **G2-I-10-02** Candidate tree/policy identity. Packages P06, P07; obligations OB-015, OB-018; lifecycles LC-12. Authority owner: REMOTE_PROVIDER_FOR_FACTS; TRUSTED_HOST_FOR_VERIFICATION. Runtime visibility: Read-only typed facts. Cleanup verification: Fresh host corroboration. Failure/reuse: Mismatch/ambiguity blocks acceptance.
- **G2-I-10-03** Required-check evidence. Packages P07; obligations OB-018; lifecycles LC-12. Authority owner: REMOTE_PROVIDER_FOR_FACTS; TRUSTED_HOST_FOR_VERIFICATION. Runtime visibility: Read-only typed facts. Cleanup verification: Fresh host corroboration. Failure/reuse: Mismatch/ambiguity blocks acceptance.
- **G2-I-10-04** Independent review provenance. Packages P07; obligations OB-018; lifecycles LC-12. Authority owner: REMOTE_PROVIDER_FOR_FACTS; TRUSTED_HOST_FOR_VERIFICATION. Runtime visibility: Read-only typed facts. Cleanup verification: Fresh host corroboration. Failure/reuse: Mismatch/ambiguity blocks acceptance.
- **G2-I-10-05** Human merge observation. Packages P07; obligations OB-018; lifecycles LC-12. Authority owner: REMOTE_PROVIDER_FOR_FACTS; TRUSTED_HOST_FOR_VERIFICATION. Runtime visibility: Read-only typed facts. Cleanup verification: Fresh host corroboration. Failure/reuse: Mismatch/ambiguity blocks acceptance.
- **G2-I-10-06** Merge verification/CompletionProof. Packages P07; obligations OB-018; lifecycles LC-10, LC-12. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: DENIED. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-11-01** Untrusted workspace source state. Packages P02, P06; obligations OB-001, OB-015; lifecycles LC-09, LC-10. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: Workspace write before fence only. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-11-02** Local Git object store/commit/tree construction. Packages P06; obligations OB-015; lifecycles LC-09, LC-10. Authority owner: TRUSTED_HOST_SOURCE_PUBLICATION_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Fresh GitHub corroboration of repo/base/branch/PR/head/tree. Failure/reuse: Ambiguous mutation -> block publication and escalate.
- **G2-I-11-03** Ephemeral candidate staging and safety validation. Packages P06; obligations OB-015, OB-019; lifecycles LC-09, LC-10. Authority owner: TRUSTED_HOST_SOURCE_PUBLICATION_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Fresh GitHub corroboration of repo/base/branch/PR/head/tree. Failure/reuse: Ambiguous mutation -> block publication and escalate.
- **G2-I-11-04** Host-managed candidate branch. Packages P06; obligations OB-016, OB-017; lifecycles LC-09, LC-10. Authority owner: TRUSTED_HOST_SOURCE_PUBLICATION_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Fresh GitHub corroboration of repo/base/branch/PR/head/tree. Failure/reuse: Ambiguous mutation -> block publication and escalate.
- **G2-I-11-05** Host PR create/update association. Packages P06; obligations OB-016, OB-017; lifecycles LC-09, LC-10. Authority owner: TRUSTED_HOST_SOURCE_PUBLICATION_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Fresh GitHub corroboration of repo/base/branch/PR/head/tree. Failure/reuse: Ambiguous mutation -> block publication and escalate.
- **G2-I-11-06** SourcePublicationRecord. Packages P01, P06; obligations OB-003, OB-017; lifecycles LC-09, LC-10. Authority owner: TRUSTED_HOST_SOURCE_PUBLICATION_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Fresh GitHub corroboration of repo/base/branch/PR/head/tree. Failure/reuse: Ambiguous mutation -> block publication and escalate.
- **G2-I-11-07** Fresh CandidateRef/tree capture. Packages P06, P07; obligations OB-017, OB-018; lifecycles LC-09, LC-10. Authority owner: REMOTE_PROVIDER_FOR_FACTS; TRUSTED_HOST_FOR_VERIFICATION. Runtime visibility: Read-only typed facts. Cleanup verification: Fresh host corroboration. Failure/reuse: Mismatch/ambiguity blocks acceptance.
- **G2-I-11-08** Generic result/handoff/arbitrary file export. Packages P06; obligations OB-019; lifecycles LC-09, LC-10. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-11-09** Provider-private state exclusion. Packages P02, P06; obligations OB-004, OB-019; lifecycles LC-03, LC-09. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-12-01** Existing Codex app-server stderr channel. Packages P04, P08; obligations OB-006, OB-020; lifecycles LC-13, LC-14. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: No evidence store access. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-12-02** Diagnostics/configuration dumps. Packages P04, P08; obligations OB-006, OB-020; lifecycles LC-13, LC-14. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: No evidence store access. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-12-03** Crash output/core dumps. Packages P04, P08; obligations OB-006, OB-020; lifecycles LC-13, LC-14. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: No evidence store access. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-12-04** Temporary credential/evidence copies. Packages P02, P04, P08; obligations OB-004, OB-006, OB-020; lifecycles LC-13, LC-14. Authority owner: TRUSTED_HOST_ATTEMPT_BOUNDARY. Runtime visibility: No evidence store access. Cleanup verification: Host verifies paths, FDs, mounts and copies absent; uncertainty quarantines. Failure/reuse: Unknown owner/disclosure/absence -> QUARANTINE + BLOCK_REUSE.
- **G2-I-12-05** Gate 2 secret-free host evidence/reference record. Packages P01, P08; obligations OB-003, OB-020; lifecycles LC-13, LC-14. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: No evidence store access. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-12-06** Retained synthetic/r4/diagnostic material. Packages P09; obligations OB-023; lifecycles LC-13, LC-14. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: No evidence store access. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-12-07** Secret-free log, diagnostic and operator-evidence filtering/retention control. Packages P04, P08; obligations OB-006, OB-020, OB-025; lifecycles LC-13, LC-14. Authority owner: TRUSTED_HOST_RECOVERY_BOUNDARY. Runtime visibility: No raw host evidence store access. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-14-01** Provider request/effect record. Packages P04; obligations OB-006, OB-009; lifecycles LC-08. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: TYPED_METADATA_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-14-02** Plane transition effect. Packages P05; obligations OB-013; lifecycles LC-11. Authority owner: TRUSTED_SYMPHONY_HOST. Runtime visibility: TYPED_METADATA_ONLY. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-14-03** GitHub candidate/check/merge observations. Packages P05, P07; obligations OB-014, OB-018; lifecycles LC-12. Authority owner: REMOTE_PROVIDER_FOR_FACTS; TRUSTED_HOST_FOR_VERIFICATION. Runtime visibility: Typed read result only. Cleanup verification: Fresh host corroboration. Failure/reuse: Mismatch/ambiguity blocks acceptance.
- **G2-I-14-04** GitHub push/PR mutation effect. Packages P06; obligations OB-016, OB-017; lifecycles LC-10. Authority owner: TRUSTED_HOST_SOURCE_PUBLICATION_BOUNDARY. Runtime visibility: Typed completion request/result only. Cleanup verification: Fresh GitHub corroboration of repo/base/branch/PR/head/tree. Failure/reuse: Ambiguous mutation -> block publication and escalate.
- **G2-I-14-05** Human exact-candidate merge. Packages P07; obligations OB-018; lifecycles LC-12. Authority owner: REMOTE_PROVIDER_FOR_FACTS; TRUSTED_HOST_FOR_VERIFICATION. Runtime visibility: Typed read result only. Cleanup verification: Fresh host corroboration. Failure/reuse: Mismatch/ambiguity blocks acceptance.
- **G2-I-15-01** Orphan discovery record. Packages P01; obligations OB-003; lifecycles LC-13, LC-14. Authority owner: TRUSTED_HOST_RECOVERY_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-15-02** Quarantine and unsafe-reuse block. Packages P01, P03; obligations OB-003, OB-010; lifecycles LC-13, LC-14. Authority owner: TRUSTED_HOST_RECOVERY_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-15-03** Publication restart reconciliation state. Packages P01, P06; obligations OB-003, OB-017; lifecycles LC-10, LC-13. Authority owner: TRUSTED_HOST_RECOVERY_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-15-04** Operator-resolution status. Packages P01, P03; obligations OB-003, OB-010; lifecycles LC-13, LC-14. Authority owner: TRUSTED_HOST_RECOVERY_BOUNDARY. Runtime visibility: DENIED. Cleanup verification: Host identity and remote/resource state verification. Failure/reuse: Ambiguous identity/effect -> quarantine/block reuse.
- **G2-I-16-01** Host SIWC credential and refresh store; RuntimeAttempt denied. Packages P04; obligations OB-006, OB-009; lifecycles LC-14. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-16-02** Raw Plane/GitHub credentials and API clients; RuntimeAttempt denied. Packages P05, P06; obligations OB-014, OB-016; lifecycles LC-14. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-16-03** Personal host files/service control plane; RuntimeAttempt denied. Packages P09; obligations OB-005, OB-022; lifecycles LC-14. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.
- **G2-I-16-04** Raw Git mutation/protected-base/merge admin capability; RuntimeAttempt denied. Packages P06, P07; obligations OB-016, OB-018; lifecycles LC-14. Authority owner: SEPARATE_HOST_OR_EXTERNAL_AUTHORITY. Runtime visibility: DENIED. Cleanup verification: Negative access proof required. Failure/reuse: Observed access -> quarantine.

The exhaustive inventory accounting is:

```text
I-01: 7   I-02: 3   I-03: 16  I-04: 12  I-05: 9
I-06: 6   I-07: 11  I-08: 9   I-09: 7   I-10: 6
I-11: 9   I-12: 7   I-14: 5   I-15: 4   I-16: 4
TOTAL: 115
```

There is no I-13 section.

```ini
OBLIGATIONS_TOTAL=26
OBLIGATIONS_MAPPED=26
OBLIGATIONS_UNMAPPED=0
```

## E. Implementation work packages

The nine-package decomposition is fixed. Detailed contracts in sections H through K are normative parts of the packages.

### P01. Dormant attempt-resource and fence foundation

```text
PACKAGE_ID: P01
NAME: Dormant attempt-resource and fence foundation
PRIMARY_OBLIGATIONS: OB-002, OB-003
SECONDARY_OBLIGATIONS: OB-001, OB-009, OB-013, OB-017, OB-020

PURPOSE:
Persist resource obligations and prevent Gate 2 release through legacy APIs,
without enabling allocation, runtime launch or clean release.

CURRENT_PRODUCTION_SEAM: C1 and C6.
CURRENT_SOURCE_FILES:
L/agent_runtime/attempt_ledger.ex; L/orchestrator.ex;
L/config.ex; L/config/schema.ex; elixir/lib/symphony_elixir.ex
CURRENT_SYMBOLS:
AttemptLedger open/validation/record writers/rearm/release;
Orchestrator bind-before-spawn and release-after-task-down.
CURRENT_TESTS:
T/attempt_ledger_test.exs; T/runtime_attempt_identity_test.exs;
T/work_control_recovery_ledger_test.exs; T/suspension_recovery_test.exs

FILES_TO_CREATE:
L/agent_runtime/attempt_grant.ex
L/agent_runtime/attempt_resource.ex
L/agent_runtime/recovery_generation.ex
L/agent_runtime/quarantine_disposition.ex
L/agent_runtime/cleanup_evidence_ref.ex
L/agent_runtime/attempt_resource_ledger.ex
L/agent_runtime/attempt_boundary.ex
L/agent_runtime/attempt_ledger_migration.ex
elixir/lib/mix/tasks/symphony.attempt_migrate.ex

FILES_TO_MODIFY:
Current files above; elixir/README.md; elixir/WORKFLOW.md

TEST_FILES_TO_CREATE_OR_MODIFY:
T/gate2_attempt_types_test.exs
T/gate2_attempt_resource_ledger_test.exs
T/gate2_attempt_boundary_test.exs
T/gate2_attempt_compatibility_test.exs
T/gate2_attempt_config_test.exs
T/gate2_attempt_migration_test.exs
T/attempt_ledger_test.exs

CONSUMED_INTERFACES:
Current RuntimeAttempt.Identity, route/authority decision and AttemptLedger lineage.
PRODUCED_INTERFACES:
P01 contracts below; resource/recovery records; schema migration receipt.

NEW_TYPES_OR_RECORDS:
AttemptGrant, AttemptResource, RecoveryGeneration, QuarantineDisposition,
CleanupEvidenceRef, permits/fence refs, MigrationRequest/Journal/Receipt.
PERSISTENCE_BACKEND:
Serialized DETS resource ledger; existing AttemptLedger; migration sidecar journal.
PERSISTED_IDENTITY:
Project/tracker, all five runtime identity fields, grant/resource IDs,
immutable boundary kind, revision and recovery generation.
PERSISTED_STATE_MACHINE:
H resource/grant lifecycle; I migration lifecycle.

LIFECYCLE_DELTA:
Durable obligations beside the existing fence; no restored live authority.
GUARDS:
Actual registered host caller, exact identity/generation/revision and ledger schema.
SIDE_EFFECTS:
Host ledger writes only; migration is separate offline maintenance.
FAILURE_TRANSITIONS:
Uncertain storage blocks admission; ownership conflict quarantines.
RESTART_RECONCILIATION:
New synchronized recovery generation; discover facts, restore no capability.
TERMINAL_MEANING:
P01 cannot establish cleanliness or release Gate 2 authority.

CREDENTIAL_IMPACT: References only.
NETWORK_IMPACT: None.
FILESYSTEM_IMPACT: Host ledgers/journal only.
PROCESS_CGROUP_NAMESPACE_IMPACT: None.
SOURCE_CONTROL_IMPACT: None.

MIGRATION_OR_BACKCOMPAT:
Exact whole-ledger model in I; legacy semantics preserved.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR:
No v2-to-v1 downgrade; incomplete migration blocks startup.

TEST_STRATEGY: Exact P01 tasks in K.
NEGATIVE_CONTROLS:
Marker removal, legacy release, forged/stale refs, mixed versions and wrong owner.
FAILURE_INJECTION:
DETS write/sync and every migration commit position.
RECOVERY_PROOF:
Partial transactions remain blocked; migration never exposes mixed record versions.
MECHANICAL_PROOF:
Foundation cannot allocate, launch, produce usable permit or clean release.
INDEPENDENT_REVIEW_REQUIREMENTS:
All record writers, rearm/history and release entry points.

REQUIRES_HOST_PRIVILEGE:
No elevated privilege for local source/tests; deployment maintenance separately authorized.
REQUIRES_CODEX_EXECUTION_LATER: NO for package acceptance.
REQUIRES_PROVIDER_EXECUTION_LATER: NO.
DEPENDENCIES: G00 before implementation authorization.
UNBLOCKS: P08 and independent P05 contract work.
ACCEPTANCE_CONDITION:
Legacy regression passes; Gate 2 remains dormant and cannot bypass its durable binding.
```

### E.1 Complete P01 contracts

These are proposed types and specifications, not implementation bodies.

Common bounded values:

```elixir
@type id :: String.t()
@type digest :: String.t()

@type reason ::
        :owner_unknown | :identity_conflict | :stale_generation
        | :fence_unverified | :cleanup_unverified | :possible_disclosure
        | :storage_uncertain | :external_effect_ambiguous
        | :operator_resolution_required
```

IDs are bounded nonempty opaque strings. SHA-256 digests are lowercase 64-character hex. Existing Git SHA-1 identities remain separately typed and validated.

The **single stable Gate 2 P01 error union** is:

```elixir
@type error ::
        :invalid_request | :unauthorized_caller | :boundary_unavailable
        | :gate2_dormant | :gate2_profile_incomplete
        | :namespace_mismatch | :identity_mismatch | :route_mismatch
        | :recovery_generation_mismatch | :stale_grant | :grant_not_found
        | :grant_not_active | :operation_denied | :permit_conflict
        | :resource_conflict | :resource_not_found | :revision_conflict
        | :transition_invalid | :binding_downgrade_denied
        | :gate2_boundary_required
        | :attempt_resource_verification_required
        | :quarantined | :ownership_ambiguous
        | :cleanup_verifier_unavailable | :cleanup_reference_missing
        | :cleanup_reference_invalid | :cleanup_reference_stale
        | :cleanup_resource_set_mismatch | :cleanup_not_verified
        | :external_effect_unresolved
        | :storage_unavailable | :storage_corrupt
        | :write_failed | :sync_failed
        | :migration_required | :migration_in_progress
        | :migration_lock_unavailable | :ledger_in_use
        | :migration_source_invalid | :migration_target_invalid
        | :migration_commit_uncertain | :migration_not_permitted
        | :unsupported_schema | :schema_mismatch
```

All new P01 domain APIs return this union. Existing raw legacy APIs retain their accepted legacy error vocabulary. New Gate 2 branches use the union above, including exactly `:attempt_resource_verification_required`.

Boundary adapters normalize old storage errors into `:storage_unavailable`, `:storage_corrupt`, `:write_failed` or `:sync_failed`; schema errors into `:unsupported_schema`/`:schema_mismatch`; and stale identity/fence failures into the matching identity/transition error. Raw exceptions or paths never become new public variants.

Struct schemas:

```elixir
# RecoveryGeneration
@type t :: %__MODULE__{
  schema_version: 1,
  project_namespace: String.t(),
  host_id: String.t(),
  boot_id: String.t(),
  sequence: pos_integer(),
  nonce: String.t()
}

# AttemptGrant
@type operation ::
        :workspace_read | :workspace_write | :tool_execute
        | :model_request | :plane_read | :plane_transition
        | :source_control_read

@type t :: %__MODULE__{
  schema_version: 1,
  grant_id: String.t(),
  project_namespace: String.t(),
  tracker_identity_sha256: String.t(),
  runtime_identity: RuntimeAttempt.Identity.t(),
  recovery_generation: RecoveryGeneration.t(),
  route_fingerprint: String.t(),
  subscription_registration_id: String.t(),
  credential_generation: pos_integer(),
  workspace_resource_id: String.t(),
  source_admission_policy_sha256: String.t(),
  process_policy_sha256: String.t(),
  network_policy_sha256: String.t(),
  tool_policy_sha256: String.t(),
  capacity_profile_sha256: String.t(),
  allowed_operations: [operation()],
  fence_epoch: pos_integer()
}

@type ref :: %{
  grant_id: String.t(),
  project_namespace: String.t(),
  runtime_identity: RuntimeAttempt.Identity.t(),
  fence_epoch: pos_integer(),
  grant_sha256: String.t()
}

# AttemptResource
@type class ::
        :workspace | :home | :xdg_config | :xdg_state | :xdg_data
        | :cache | :runtime_tmp | :provider_private | :process_scope
        | :mount_scope | :network_scope | :materialization
        | :candidate_stage

@type state ::
        :reserved | :allocating | :allocated | :active
        | :fencing | :fenced | :destroying | :absent_verified
        | :cleanup_unverified | :quarantined

@type t :: %__MODULE__{
  schema_version: 1,
  resource_id: String.t(),
  project_namespace: String.t(),
  grant_id: String.t(),
  runtime_identity: RuntimeAttempt.Identity.t(),
  class: class(),
  state: state(),
  revision: non_neg_integer(),
  stable_locator: String.t(),
  allocation_identity_sha256: String.t() | nil,
  capacity_profile_sha256: String.t(),
  owner_host_id: String.t(),
  creation_generation: RecoveryGeneration.t(),
  reconciliation_generation: RecoveryGeneration.t(),
  last_evidence_ref: String.t() | nil,
  quarantine: QuarantineDisposition.t()
}

# QuarantineDisposition
@type state ::
        :clear | :quarantined | :block_reuse
        | :operator_resolution_pending | :released_for_new_authorization
        | :remains_quarantined

@type t :: %__MODULE__{
  state: state(),
  reason: AttemptBoundary.reason() | nil,
  evidence_ref: String.t() | nil,
  generation: RecoveryGeneration.t(),
  resolution_ref: String.t() | nil
}

# CleanupEvidenceRef
@type t :: %__MODULE__{
  schema_version: 1,
  evidence_id: String.t(),
  evidence_sha256: String.t(),
  project_namespace: String.t(),
  grant_id: String.t(),
  runtime_identity: RuntimeAttempt.Identity.t(),
  fence_epoch: pos_integer(),
  resource_set_sha256: String.t(),
  verification_generation: RecoveryGeneration.t(),
  verifier_implementation_sha256: String.t()
}
```

Each value module has:

```elixir
@spec new(map()) :: {:ok, t()} | {:error, AttemptBoundary.error()}
```

These constructors validate shape only. They cannot create authoritative current generations, grants, classifications or cleanup evidence. AttemptGrant additionally has:

```elixir
@spec reference(t()) :: ref()
```

Boundary request/result schemas:

```elixir
@type authorization_request :: %{
  route_fingerprint: String.t(),
  subscription_registration_id: String.t(),
  credential_generation: pos_integer(),
  source_admission_policy_sha256: String.t(),
  process_policy_sha256: String.t(),
  network_policy_sha256: String.t(),
  tool_policy_sha256: String.t(),
  capacity_profile_sha256: String.t()
}

@type operation_request :: %{
  operation_id: String.t(),
  operation: AttemptGrant.operation(),
  resource_id: String.t() | nil,
  arguments_sha256: String.t()
}

@type operation_permit :: %{
  permit_id: String.t(),
  grant_ref: AttemptGrant.ref(),
  operation_id: String.t(),
  operation: AttemptGrant.operation(),
  resource_id: String.t() | nil,
  fence_epoch: pos_integer()
}

@type fence_request :: %{
  grant_ref: AttemptGrant.ref(),
  reason: :completion | :cancellation | :failure | :restart | :publication
}

@type fence_ref :: %{
  grant_ref: AttemptGrant.ref(),
  fence_epoch: pos_integer(),
  status: :requested | :verified,
  evidence_ref: String.t() | nil
}

@spec start_link(keyword()) :: GenServer.on_start()

@spec authorize(
  GenServer.server(), RuntimeAttempt.Identity.t(), authorization_request()
) :: {:ok, AttemptGrant.t()} | {:error, error()}

@spec authorize_operation(
  GenServer.server(), AttemptGrant.ref(), operation_request()
) :: {:ok, operation_permit()} | {:error, error()}

@spec fence(
  GenServer.server(), fence_request()
) :: {:ok, fence_ref()} | {:error, error()}

@spec reconcile_startup(
  GenServer.server()
) :: {:ok, RecoveryGeneration.t()} | {:error, error()}

@spec release(
  GenServer.server(), CleanupEvidenceRef.t() | nil
) :: :ok | {:error, error()}
```

Resource ledger:

```elixir
@opaque t :: GenServer.server()

@type transition :: %{
  to: AttemptResource.state(),
  generation: RecoveryGeneration.t(),
  allocation_identity_sha256: String.t() | nil,
  evidence_ref: String.t() | nil,
  cleanup_ref: CleanupEvidenceRef.t() | nil,
  quarantine: QuarantineDisposition.t()
}

@spec start_link(keyword()) :: GenServer.on_start()
@spec close(t()) :: :ok | {:error, AttemptBoundary.error()}

@spec reserve_sync(t(), AttemptResource.t()) ::
  {:ok, AttemptResource.t()} | {:error, AttemptBoundary.error()}

@spec transition_sync(t(), String.t(), non_neg_integer(), transition()) ::
  {:ok, AttemptResource.t()} | {:error, AttemptBoundary.error()}

@spec fetch(t(), String.t()) ::
  {:ok, AttemptResource.t()} | :not_found | {:error, AttemptBoundary.error()}

@spec list_for_grant(t(), String.t()) ::
  {:ok, [AttemptResource.t()]} | {:error, AttemptBoundary.error()}
```

New AttemptLedger entry points:

```elixir
@spec bind_gate2_fence_sync(
  AttemptLedger.t(), String.t(), AttemptGrant.ref()
) :: :ok | {:error, AttemptBoundary.error()}

@spec release_gate2_authority_fence(
  AttemptLedger.t(), String.t(),
  RuntimeAttempt.Identity.t(), CleanupEvidenceRef.t()
) :: :ok | {:error, AttemptBoundary.error()}
```

Authority and behavior:

- Actual OTP callers must match the registered Orchestrator owner or narrowly registered recovery owner and current owner epoch.
- Every grant/reference is resolved against durable records; a struct is not a capability.
- `reserve_sync/2` permits a new reservation or exact idempotent duplicate.
- `transition_sync/4` compares revision and generation and synchronizes before success.
- `authorize/3` and `authorize_operation/3` return `:gate2_dormant` in P01.
- `fence/2` can report only `:requested` in P01.
- `release/2` rejects nil with `:cleanup_reference_missing`, malformed references with `:cleanup_reference_invalid`, stale references with `:cleanup_reference_stale`, and otherwise returns `:cleanup_verifier_unavailable` in P01.
- P01 cannot advance resources to `:absent_verified`.
- No production verifier callback, supplied evidence body or test stub is accepted.

Configuration remains:

```text
agent.attempt_boundary.mode:
  legacy             default
  gate2_foundation   requires ledger schema 2; no launch/allocation/release
  gate2_enforced     rejected until all qualified components exist
```

Changing configuration cannot downgrade a durable Gate 2 binding.

### P02. Fresh workspace, storage and capacity

```text
PACKAGE_ID: P02
NAME: Fresh workspace, storage and capacity
PRIMARY_OBLIGATIONS: OB-001, OB-004, OB-021
SECONDARY_OBLIGATIONS: OB-002, OB-005, OB-006, OB-015, OB-019

PURPOSE:
Fresh bounded writable domains and authoritative source admission.

CURRENT_PRODUCTION_SEAM: C3; CredentialBoundary environment assignment.
CURRENT_SOURCE_FILES:
L/workspace.ex; L/workspace/ownership.ex;
L/workspace/ownership_ledger.ex; L/credential_boundary.ex;
L/config.ex; L/config/schema.ex
CURRENT_SYMBOLS:
create_for_issue; revalidate_owned_local_workspace; remove_recorded;
OwnershipLedger.reserve_sync/2 and transition_sync/4; routed_port_env/3.
CURRENT_TESTS:
T/workspace_ownership_test.exs; T/workspace_ownership_ledger_test.exs;
T/workspace_and_config_test.exs; T/credential_boundary_test.exs

FILES_TO_CREATE:
L/workspace/attempt_workspace.ex
L/workspace/source_admission_policy.ex
L/workspace/source_manifest.ex
L/agent_runtime/capacity_reservation.ex
N/src/storage.rs
N/src/capacity.rs
FILES_TO_MODIFY:
Current files above and P01 allocation integration.
TEST_FILES_TO_CREATE_OR_MODIFY:
T/attempt_workspace_test.exs; T/source_manifest_test.exs;
T/source_admission_policy_test.exs; T/attempt_capacity_test.exs;
N/tests/storage_lifecycle.rs; N/tests/capacity_bounds.rs

CONSUMED_INTERFACES:
P01 resource intent; H-060C ownership; host source-admission decision; P08 evidence.
PRODUCED_INTERFACES:
AttemptWorkspace allocate/fence/destroy; SourceAdmissionPolicy;
SourceManifest schema; capacity reserve/commit/release.
NEW_TYPES_OR_RECORDS:
AttemptWorkspaceRef, SourceAdmissionPolicy, SourceManifest,
CapacityReservation, NativeAllocationJournal.
PERSISTENCE_BACKEND:
OwnershipLedger plus resource/capacity DETS and root-owned allocation journal.
PERSISTED_IDENTITY:
Grant/resource/ownership IDs; filesystem UUID; backing inode; loop identity;
source-policy and capacity digests.
PERSISTED_STATE_MACHINE:
Workspace/resource and SourceManifest lifecycles in H.

LIFECYCLE_DELTA: Fresh resource per attempt.
GUARDS:
Durable intent/capacity before allocation; exact ownership before destruction.
SIDE_EFFECTS:
Preallocated ext4 loop images, private mounts and authorized checkout.
FAILURE_TRANSITIONS:
Unknown allocation/reference/classification -> cleanup-unverified or quarantine.
RESTART_RECONCILIATION:
Discover backing inode/device/UUID/mounts and source policy; restore no writer.
TERMINAL_MEANING:
Ownership release alone is not complete resource cleanup.

CREDENTIAL_IMPACT:
No refresh state; holder-private and tool-private roots separated.
NETWORK_IMPACT: None.
FILESYSTEM_IMPACT: Exact primitive in J.
PROCESS_CGROUP_NAMESPACE_IMPACT: Private role mount namespaces.
SOURCE_CONTROL_IMPACT:
Read-only runtime .git; explicit source admission, no add-all authority.

MIGRATION_OR_BACKCOMPAT:
Legacy workspace reuse stays legacy-only.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR:
No reuse on unsupported storage or uncertain ownership.

TEST_STRATEGY:
Disposable ext4/loop/mount fixtures and source-admission tests.
NEGATIVE_CONTROLS:
Aliases, nested Git metadata, unknown new paths, cross-attempt identity.
FAILURE_INJECTION:
ENOSPC/inodes, format/mount/unmount, journal/fsync and retained reference failures.
RECOVERY_PROOF:
Open-unlinked, WAL/SHM, alternate mounts and backing devices.
MECHANICAL_PROOF:
Finite byte/inode bounds and no previous writable view reuse.
INDEPENDENT_REVIEW_REQUIREMENTS:
Storage teardown, source admission and aggregate capacity.

REQUIRES_HOST_PRIVILEGE: YES for native fixtures/deployment.
REQUIRES_CODEX_EXECUTION_LATER: Only integrated proof.
REQUIRES_PROVIDER_EXECUTION_LATER: NO.
DEPENDENCIES: P01, P08.
UNBLOCKS: P04, P06, P09.
ACCEPTANCE_CONDITION:
Fresh bounded resources and complete identity/classification/cleanup accounting.
```

### P03. Host subscription and credential lifecycle

```text
PACKAGE_ID: P03
NAME: Host subscription and credential lifecycle
PRIMARY_OBLIGATIONS: OB-007, OB-008, OB-010, OB-011, OB-024
SECONDARY_OBLIGATIONS: OB-006, OB-009, OB-012, OB-020, OB-025

PURPOSE:
Verified account separation and crash-safe credential persistence/rotation.

CURRENT_PRODUCTION_SEAM: Config/CredentialBoundary; no current SIWC store.
CURRENT_SOURCE_FILES:
L/config.ex; L/config/schema.ex; L/credential_boundary.ex;
elixir/lib/symphony_elixir.ex
CURRENT_SYMBOLS:
settings/0; validate_settings/1; credential environment filtering.
CURRENT_TESTS:
T/config_identity_test.exs; T/credential_boundary_test.exs

FILES_TO_CREATE:
L/provider_auth/subscription_registration.ex
L/provider_auth/subscription_ledger.ex
L/provider_auth/subscription_manager.ex
N/src/bin/credential_vault.rs
N/src/oauth.rs
N/src/credential_store.rs
N/src/vault_key.rs
FILES_TO_MODIFY:
Configuration/application files and operator documentation.
TEST_FILES_TO_CREATE_OR_MODIFY:
T/subscription_registration_test.exs; T/subscription_rotation_test.exs;
N/tests/oauth_validation.rs; N/tests/credential_rotation.rs;
N/tests/vault_key_rotation.rs

CONSUMED_INTERFACES:
Explicit host enrollment/maintenance decisions; official OAuth/OIDC facts; P08 evidence.
PRODUCED_INTERFACES:
Enrollment/status/refresh/disconnect; credential-generation references;
host-only materialization.
NEW_TYPES_OR_RECORDS:
Registration, EnrollmentTransaction, CredentialSetGeneration,
RefreshIntent, CredentialRefreshBarrier, RevocationDisposition, VaultKeyManifest.
PERSISTENCE_BACKEND:
Secret-free metadata DETS; authenticated encrypted generation files and root journal.
PERSISTED_IDENTITY:
Registration/account/client/host/scopes; credential and vault-key generations.
PERSISTED_STATE_MACHINE:
Enrollment, refresh, upstream validity and vault-key lifecycle in H/J.

LIFECYCLE_DELTA:
Host registration survives attempts; key rotation differs from credential rotation.
GUARDS:
Exact account/client/claims; callback/PKCE; exclusive per-registration lock.
SIDE_EFFECTS:
Host-only auth traffic and encrypted atomic writes.
FAILURE_TRANSITIONS:
Inactive enrollment, uncertain credential state, revoked or reauth-required.
RESTART_RECONCILIATION:
Verify key/record/manifest/journal before selected registration can dispatch.
TERMINAL_MEANING:
Renewable registration is not an attempt grant; deletion is not remote revocation.

CREDENTIAL_IMPACT: Refresh remains native trusted-host-only.
NETWORK_IMPACT: Separate host OAuth/OIDC/JWKS/revocation channels.
FILESYSTEM_IMPACT: Exact vault format/key custody in J.
PROCESS_CGROUP_NAMESPACE_IMPACT: Short-lived host helpers, not runtime descendants.
SOURCE_CONTROL_IMPACT: None.

MIGRATION_OR_BACKCOMPAT:
No auth.json/T3Code/personal-HOME import.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR:
Key/AEAD/identity uncertainty blocks affected registration; no alternate account.

TEST_STRATEGY: Synthetic OAuth and non-live credential fixtures.
NEGATIVE_CONTROLS: Account/client/state/nonce/audience/key/header substitution.
FAILURE_INJECTION: Lost refresh, concurrent rotation, fsync/rename and key loss.
RECOVERY_PROOF: Every credential/key transaction position.
MECHANICAL_PROOF: No refresh bytes in runtime or ordinary evidence.
INDEPENDENT_REVIEW_REQUIREMENTS: OAuth, crypto custody and transaction ordering.

REQUIRES_HOST_PRIVILEGE: YES for installation/protected store.
REQUIRES_CODEX_EXECUTION_LATER: NO.
REQUIRES_PROVIDER_EXECUTION_LATER:
Only separately authorized real enrollment qualification.
DEPENDENCIES: P01, P08.
UNBLOCKS: P04, P09.
ACCEPTANCE_CONDITION:
Verified isolated registrations and recoverable rotation with uncertain state blocked; immutable grant generations, lifetime admission and verified drain-before-refresh are mandatory.
```

### P04. Holder, tool isolation, egress and provider effects

```text
PACKAGE_ID: P04
NAME: Holder, tool isolation, egress and provider effects
PRIMARY_OBLIGATIONS: OB-006, OB-009, OB-012, OB-026
SECONDARY_OBLIGATIONS: OB-002, OB-004, OB-005, OB-008, OB-020, OB-025

PURPOSE:
Only the intended holder receives access and model egress; all possible
inference effects receive prior durable intent.

CURRENT_PRODUCTION_SEAM: C2.
CURRENT_SOURCE_FILES:
L/codex/app_server.ex; L/codex/isolation_profile.ex;
L/agent_runtime/runtime_isolation.ex; L/agent_runner.ex;
L/credential_boundary.ex
CURRENT_SYMBOLS:
start_routed_local_port/4; routed_port_env/3; RuntimeIsolation admit/verify/evidence.
CURRENT_TESTS:
T/app_server_test.exs; T/agent_runner_isolation_test.exs;
T/credential_channel_enforcement_test.exs; T/runtime_isolation_actual_codex_test.exs

FILES_TO_CREATE:
L/provider_effect/request_record.ex
L/provider_effect/request_ledger.ex
L/agent_runtime/host_boundary.ex
N/src/bin/attempt_boundary.rs
N/src/launch.rs
N/src/tool_exec.rs
N/src/network.rs
N/src/hardening.rs
N/policy/apparmor/
N/policy/seccomp/
D/GATE2_CODEX_PATCH_MANIFEST.json
Upstream additions in G/J.
FILES_TO_MODIFY:
Current files above, configuration, and exact upstream list in G.
TEST_FILES_TO_CREATE_OR_MODIFY:
T/provider_request_ledger_test.exs; T/gate2_host_boundary_test.exs;
T/gate2_bearer_boundary_test.exs;
N/tests/holder_materialization.rs; N/tests/process_separation.rs;
N/tests/egress.rs; N/tests/provider_effect_crashes.rs

CONSUMED_INTERFACES:
P01 permits; P02 storage; P03 credential references; P05 tools; P08 evidence.
PRODUCED_INTERFACES:
Holder/tool execution, lease/fence, request acknowledgement and effect events.
NEW_TYPES_OR_RECORDS:
HolderIncarnation, ToolExecutionRef, NetworkLease, ProviderRequestRecord,
SendPermit, MaterializationDisposition.
PERSISTENCE_BACKEND:
Separate RequestLedger; native journal; immutable host evidence.
PERSISTED_IDENTITY:
Grant/attempt/holder/credential generation/request ordinal/endpoint/upstream IDs.
PERSISTED_STATE_MACHINE:
Provider grant, validity and effect lifecycle.

LIFECYCLE_DELTA:
Fresh holder/materialization/network capability per grant.
GUARDS:
Qualified executable/config; valid selected token; current permit; installed controls.
SIDE_EFFECTS:
Native containment, bootstrap delivery, brokered tools and permitted Responses requests.
FAILURE_TRANSITIONS:
Before invocation deny; after possible invocation retain ambiguity;
possible disclosure quarantines and blocks reuse.
RESTART_RECONCILIATION:
Revoke/discover/fence; restore no holder, token environment, permit or lease.
TERMINAL_MEANING:
Local death/cleanliness is not remote cancellation or invalidation.

CREDENTIAL_IMPACT:
Token reaches transient trusted bootstrap and selected app-server only;
resident guard never receives it.
NETWORK_IMPACT: J exact namespace/nftables/HTTP policy.
FILESYSTEM_IMPACT: Private holder/tool state; no credential file.
PROCESS_CGROUP_NAMESPACE_IMPACT: UID/PID/mount/net/cgroup/LSM/seccomp separation.
SOURCE_CONTROL_IMPACT: No runtime publication or mutation credentials.

MIGRATION_OR_BACKCOMPAT:
Gate 2 launcher/profile only; legacy launcher unchanged.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR:
Missing control, policy, helper, patch or proof denies Gate 2.

TEST_STRATEGY:
Synthetic secrets, local mock TLS provider and later exact-runtime proof.
NEGATIVE_CONTROLS: BP-01..19, routes/proxy/socket/FD/config/RPC bypasses.
FAILURE_INJECTION: Bootstrap/ack/send/stream/lease/teardown crashes.
RECOVERY_PROOF: No replay after possible send; no stale lease restoration.
MECHANICAL_PROOF:
Holder-only bearer/egress and prior durable intent for every possible request.
INDEPENDENT_REVIEW_REQUIREMENTS:
Completed source contract, Linux boundary and effect protocol.

REQUIRES_HOST_PRIVILEGE: YES.
REQUIRES_CODEX_EXECUTION_LATER: YES.
REQUIRES_PROVIDER_EXECUTION_LATER:
Only separately authorized live compatibility.
DEPENDENCIES: P01, P02, P03, P05, P08.
UNBLOCKS: P06 integrated handoff and P09.
ACCEPTANCE_CONDITION:
Exact audited profile works with all unauthorized channels denied and effects recorded.
```

### P05. Semantic operation and catalog closure

```text
PACKAGE_ID: P05
NAME: Semantic operation and catalog closure
PRIMARY_OBLIGATIONS: OB-013, OB-014
SECONDARY_OBLIGATIONS: OB-002, OB-006, OB-018, OB-025

PURPOSE: Bind existing tools without generic mutation authority.
CURRENT_PRODUCTION_SEAM: C4 and SourceControl AgentTool.
CURRENT_SOURCE_FILES:
L/plane/agent_tool.ex; L/plane/adapter.ex; L/codex/dynamic_tool.ex;
L/source_control/agent_tool.ex; L/transition_coordinator.ex;
L/work_control/transition_attempt_ledger.ex
CURRENT_SYMBOLS:
agent_tool_specs; execute; submit_controlled_transition;
request_transition; reconcile_candidate.
CURRENT_TESTS:
T/plane_agent_tool_test.exs; T/dynamic_tool_test.exs;
T/source_control_agent_tool_test.exs; T/transition_coordinator_crash_windows_test.exs
FILES_TO_CREATE: L/agent_runtime/tool_binding.ex
FILES_TO_MODIFY: Current files above.
TEST_FILES_TO_CREATE_OR_MODIFY:
T/gate2_tool_binding_test.exs and current tool/coordinator tests.

CONSUMED_INTERFACES: P01 permit; current work item/role; existing transition ledger.
PRODUCED_INTERFACES: ToolBinding and bounded request/result envelopes.
NEW_TYPES_OR_RECORDS: ToolBinding.
PERSISTENCE_BACKEND: Existing Plane ledger; grant stores tool-manifest digest.
PERSISTED_IDENTITY: Grant/attempt/role/tool/request/current work item.
PERSISTED_STATE_MACHINE: Existing Plane effect lifecycle plus current-grant guards.

LIFECYCLE_DELTA: No new semantic lifecycle owner.
GUARDS: Exact current authority, role, finite args and host selectors.
SIDE_EFFECTS: Existing controlled Plane transitions only.
FAILURE_TRANSITIONS: Deny stale/unselected tools; reconcile uncertain mutation.
RESTART_RECONCILIATION: Existing ledger and fresh Plane read.
TERMINAL_MEANING: Typed tool success is not merge/completion authority.

CREDENTIAL_IMPACT: Host Plane/GitHub credentials withheld.
NETWORK_IMPACT: Existing host transports.
FILESYSTEM_IMPACT: None.
PROCESS_CGROUP_NAMESPACE_IMPACT: None.
SOURCE_CONTROL_IMPACT: Named read-only tool.

MIGRATION_OR_BACKCOMPAT: Legacy adapters unchanged outside Gate 2 binding.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR: Manifest mismatch blocks dispatch.
TEST_STRATEGY: Exact catalog and coordinator fixtures.
NEGATIVE_CONTROLS: Selectors, arbitrary API bodies, wrong role/attempt.
FAILURE_INJECTION: Lost result, duplicate request, persistence error.
RECOVERY_PROOF: Fresh observation without resubmission.
MECHANICAL_PROOF: Five Plane tools and selected SourceControl read tool only.
INDEPENDENT_REVIEW_REQUIREMENTS: Semantic authority and channel review.

REQUIRES_HOST_PRIVILEGE: Host authority; no new elevated kernel operation.
REQUIRES_CODEX_EXECUTION_LATER: Integrated catalog proof only.
REQUIRES_PROVIDER_EXECUTION_LATER: NO for fixtures.
DEPENDENCIES: P01.
UNBLOCKS: P04, P07, P09.
ACCEPTANCE_CONDITION: Catalog/arguments/current-authority closure and safe reconciliation.
```

### P06. Source manifest, validation and bounded publication

```text
PACKAGE_ID: P06
NAME: Source manifest, validation and bounded publication
PRIMARY_OBLIGATIONS: OB-015, OB-016, OB-017, OB-019
SECONDARY_OBLIGATIONS: OB-003, OB-006, OB-018, OB-021, OB-025

PURPOSE:
Convert fenced authorized source into a validated exact candidate and reconcile
bounded GitHub mutations.

CURRENT_PRODUCTION_SEAM: C3/C5; no current publisher/scanner.
CURRENT_SOURCE_FILES:
L/workspace.ex; L/source_control.ex; L/github/source_control.ex;
L/source_control/candidate_ref.ex
CURRENT_SYMBOLS:
Workspace revalidation; capture_candidate_ref; fetch_pull_request;
fetch_git_commit; verify_candidate_unchanged; validate_tree_sha.
CURRENT_TESTS:
T/github_source_control_test.exs; T/source_control_candidate_ref_test.exs;
T/source_control_github_api_test.exs

FILES_TO_CREATE:
L/source_publication/publication_record.ex
L/source_publication/publication_ledger.ex
L/source_publication/boundary.ex
L/source_publication/candidate_stage.ex
L/source_publication/validation_evidence.ex
L/source_publication/validation_ledger.ex
L/source_publication/commit_recipe.ex
L/source_publication/metadata.ex
L/source_publication/commit_envelope_verifier.ex
L/pr_body_contract.ex
N/src/source_capture.rs
N/src/bin/candidate_validator.rs
N/src/candidate_stage.rs
N/src/validation.rs
N/src/containers.rs
N/src/binary_formats.rs
N/src/secret_rules.rs
N/src/publisher.rs
FILES_TO_MODIFY:
elixir/lib/mix/tasks/pr_body.check.ex;
L/workspace/source_manifest.ex; L/source_control.ex;
L/github/source_control.ex; L/config.ex; L/config/schema.ex;
P01/P08 handoff integration.
TEST_FILES_TO_CREATE_OR_MODIFY:
T/source_capture_test.exs; T/source_publication_boundary_test.exs;
T/source_publication_recovery_test.exs;
T/candidate_validation_evidence_test.exs;
N/tests/source_capture.rs; N/tests/candidate_validation.rs;
N/tests/container_validation.rs; N/tests/media_validation.rs;
N/tests/publication_reconciliation.rs

CONSUMED_INTERFACES:
Verified writer fence; SourceAdmissionPolicy; baseline; P08 evidence;
accepted scanner policy/implementation/limits.
PRODUCED_INTERFACES:
Sealed SourceManifest, CandidateStage, validation evidence,
bounded publish/reconcile and fresh CandidateRef/tree.
NEW_TYPES_OR_RECORDS:
SourceManifest; SourcePublicationRecord; StageIdentity; ValidationEvidence;
CommitRecipe; CommitEnvelopeEvidence; PublicationMetadata.
PERSISTENCE_BACKEND:
Publication/validation DETS indexes plus immutable host objects.
PERSISTED_IDENTITY:
Repo/work item/lineage/grant/publication generation;
baseline/manifest/commit/tree/stage/policy/implementation/PR.
PERSISTED_STATE_MACHINE:
SourceManifest plus LC-09/10.

LIFECYCLE_DELTA:
Fence before capture/construction; validate before push; reconcile uncertainty.
GUARDS:
Builder/Fixer host authorization; classified paths; exact immutable identities.
SIDE_EFFECTS:
Git objects, offline validation, candidate push and bound PR mutation.
FAILURE_TRANSITIONS:
Uncertain manifest or FAIL/UNCERTAIN scan denies publication;
unknown remote effect enters reconciliation.
RESTART_RECONCILIATION:
Separate record; fresh branch/PR reads; no duplicate PR or blind retry.
TERMINAL_MEANING:
Captured CandidateRef is not review/merge/completion.

CREDENTIAL_IMPACT:
Validator none; publisher scoped capability outside runtime.
NETWORK_IMPACT: Validator none; publisher fixed GitHub transport.
FILESYSTEM_IMPACT: Exact Git-object stage; no workspace-directory scan.
PROCESS_CGROUP_NAMESPACE_IMPACT: Isolated bounded validator.
SOURCE_CONTROL_IMPACT: Host-only candidate mutation; no force/protected-base push.

MIGRATION_OR_BACKCOMPAT:
Read-only SourceControl remains separate; packet immutable.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR:
Missing policy/implementation/limits/manifest/evidence denies publication.
TEST_STRATEGY:
Source operations, full-tree media/container fixtures and mock GitHub.
NEGATIVE_CONTROLS:
Unknown paths, private state, links, movement, stale PASS and selectors.
FAILURE_INJECTION:
Capture/scan/evidence failure and lost push/PR responses.
RECOVERY_PROOF:
Fresh exact remote corroboration.
MECHANICAL_PROOF:
SourceManifest -> exact commit recipe/envelope -> scanned tree -> pushed commit
and host-only PR metadata identity equality.
INDEPENDENT_REVIEW_REQUIREMENTS:
Source classification, scanner semantics and publication reconciliation.

REQUIRES_HOST_PRIVILEGE: YES.
REQUIRES_CODEX_EXECUTION_LATER: Integrated fencing proof only.
REQUIRES_PROVIDER_EXECUTION_LATER: NO for fixtures.
DEPENDENCIES: G00, P01, P02, P08; P04 for integrated handoff.
UNBLOCKS: P07, P09.
ACCEPTANCE_CONDITION:
Only a sealed manifest, verified commit envelope, immutable PASS-bound exact
candidate and locally validated host-rendered metadata can be published.
```

### P07. Exact candidate completion binding

```text
PACKAGE_ID: P07
NAME: Exact candidate completion binding
PRIMARY_OBLIGATIONS: OB-018
SECONDARY_OBLIGATIONS: OB-014, OB-015, OB-017, OB-019, OB-023

PURPOSE: Carry exact validation/publication identity through human merge/completion.
CURRENT_PRODUCTION_SEAM: C5.
CURRENT_SOURCE_FILES:
L/source_control.ex; L/github/source_control.ex;
L/source_control/candidate_ref.ex; L/source_control/candidate_verification.ex;
L/source_control/merge_verification.ex;
L/work_control/completion_proof.ex; L/work_control/lifecycle_assessment.ex
CURRENT_SYMBOLS:
durable_candidate_evidence; reconcile_stored_evidence; valid_review_provenance?;
verify_required_checks; verify_merge; with_merge_verification; completion_validated?.
CURRENT_TESTS:
T/source_control_candidate_ref_test.exs;
T/source_control_merge_verification_test.exs;
T/guard_class_source_control_test.exs; T/work_control_assessment_test.exs
FILES_TO_CREATE: L/source_control/candidate_validation_binding.ex
FILES_TO_MODIFY: Current files above.
TEST_FILES_TO_CREATE_OR_MODIFY:
T/candidate_validation_binding_test.exs and current verification/assessment tests.

CONSUMED_INTERFACES: P06 identities/evidence; existing check/review/merge facts.
PRODUCED_INTERFACES: CandidateValidationBinding and extended completion evidence.
NEW_TYPES_OR_RECORDS: CandidateValidationBinding.
PERSISTENCE_BACKEND: Existing work-control evidence plus immutable references.
PERSISTED_IDENTITY:
CandidateRef fingerprint/tree/manifest/publication generation;
scanner and source-control policy identities.
PERSISTED_STATE_MACHINE: LC-12.

LIFECYCLE_DELTA: Gate 2 completion requires validation binding.
GUARDS: Same candidate/tree/policy/checks/review/human merge.
SIDE_EFFECTS: Read-only observation and proof persistence.
FAILURE_TRANSITIONS: Movement/mismatch/absent merge -> HOLD/REJECTED.
RESTART_RECONCILIATION: Fresh remote facts; no review transfer.
TERMINAL_MEANING: Accepted proof alone enables validated Done/dependency satisfaction.

CREDENTIAL_IMPACT: Host read-only GitHub credentials.
NETWORK_IMPACT: Existing verifier transport.
FILESYSTEM_IMPACT: Evidence only.
PROCESS_CGROUP_NAMESPACE_IMPACT: None.
SOURCE_CONTROL_IMPACT: No publication or merge mutation.

MIGRATION_OR_BACKCOMPAT:
Five-field CandidateRef unchanged; versioned binding added alongside.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR:
Gate 2 cannot fall back to legacy completion evidence.
TEST_STRATEGY: Movement/replacement/merge-tree/restart fixtures.
NEGATIVE_CONTROLS: Wrong tree, stale review/policy, absent human merge.
FAILURE_INJECTION: Read/persistence failure between steps.
RECOVERY_PROOF: Stored seed is revalidated, never restored as acceptance.
MECHANICAL_PROOF: Same exact candidate and merge close CompletionProof.
INDEPENDENT_REVIEW_REQUIREMENTS: Exact identity and completion authority.

REQUIRES_HOST_PRIVILEGE: Host authority only.
REQUIRES_CODEX_EXECUTION_LATER: NO for fixtures.
REQUIRES_PROVIDER_EXECUTION_LATER: NO for fixtures.
DEPENDENCIES: P05, P06.
UNBLOCKS: P09.
ACCEPTANCE_CONDITION:
Replacement invalidates review; exact human merge/tree verification required.
```

### P08. Host evidence, cleanup and quarantine

```text
PACKAGE_ID: P08
NAME: Host evidence, cleanup and quarantine
PRIMARY_OBLIGATIONS: OB-020, OB-025
SECONDARY_OBLIGATIONS: OB-002, OB-003, OB-004, OB-006, OB-009, OB-017

PURPOSE: Fixed authoritative cleanup producer and secret-free evidence.
CURRENT_PRODUCTION_SEAM: Diagnostic handling and containment retention.
CURRENT_SOURCE_FILES:
L/codex/app_server.ex; L/credential_boundary.ex; L/log_file.ex;
L/orchestrator.ex; L/work_control/suspension_recovery.ex
CURRENT_SYMBOLS:
Diagnostic handling; redact; release-after-task-down; containment retention.
CURRENT_TESTS:
T/log_file_test.exs; T/app_server_edge_test.exs;
T/runtime_attempt_teardown_test.exs; T/suspension_recovery_test.exs
FILES_TO_CREATE:
L/host_evidence/record.ex
L/host_evidence/ledger.ex
L/host_evidence/cleanup_verifier.ex
L/host_evidence/quarantine.ex
N/src/evidence.rs
N/src/cleanup.rs
N/src/redaction.rs
FILES_TO_MODIFY: Current files and P01 release implementation.
TEST_FILES_TO_CREATE_OR_MODIFY:
T/cleanup_evidence_authority_test.exs;
T/host_evidence_redaction_test.exs; T/gate2_quarantine_recovery_test.exs;
N/tests/cleanup_verification.rs; N/tests/secret_free_evidence.rs

CONSUMED_INTERFACES: P01 resource snapshot and typed native observations.
PRODUCED_INTERFACES: Immutable CleanupEvidence/ref; safe diagnostics/quarantine.
NEW_TYPES_OR_RECORDS:
CleanupEvidence, resource observations, DisclosureDisposition, QuarantineResolution.
PERSISTENCE_BACKEND: Root-owned immutable objects and secret-free DETS index.
PERSISTED_IDENTITY: Grant/attempt/fence/resource-set/current generation/verifier.
PERSISTED_STATE_MACHINE: LC-13/14; immutable terminal generations.

LIFECYCLE_DELTA: Only fixed verifier can establish clean/absent.
GUARDS: Complete matching observations and current resource snapshot.
SIDE_EFFECTS: Fence/cleanup, observation, evidence persistence.
FAILURE_TRANSITIONS: Missing/stale/unknown -> quarantine/block-reuse.
RESTART_RECONCILIATION: New generation and re-observation.
TERMINAL_MEANING: Local clean is not cancellation/revocation/new authorization.

CREDENTIAL_IMPACT: No raw secrets in ordinary evidence.
NETWORK_IMPACT: No provider authority.
FILESYSTEM_IMPACT: Bounded evidence; no raw crash/temp promotion.
PROCESS_CGROUP_NAMESPACE_IMPACT: Positive scope/reference absence proof.
SOURCE_CONTROL_IMPACT: No candidate mutation.

MIGRATION_OR_BACKCOMPAT: Legacy release unchanged for legacy records.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR: Missing verifier prevents Gate 2 release.
TEST_STRATEGY: Real files/resources and synthetic secrets.
NEGATIVE_CONTROLS: Forged refs/indexes, wrong resource set, hidden references.
FAILURE_INJECTION: Evidence fsync/index/verifier/cleanup failure.
RECOVERY_PROOF: No PID/path/time-only release.
MECHANICAL_PROOF: Fixed root-owned evidence, not caller values, authorizes release.
INDEPENDENT_REVIEW_REQUIREMENTS: Evidence secrecy/authority and release ordering.

REQUIRES_HOST_PRIVILEGE: YES.
REQUIRES_CODEX_EXECUTION_LATER: Integrated diagnostic proof only.
REQUIRES_PROVIDER_EXECUTION_LATER: NO.
DEPENDENCIES: P01.
UNBLOCKS: P02, P03, P04, P06.
ACCEPTANCE_CONDITION: Uncertain cleanup retains authority fence and reuse block.
```

### P09. Qualification and governance evidence

```text
PACKAGE_ID: P09
NAME: Qualification and governance evidence
PRIMARY_OBLIGATIONS: OB-005, OB-022, OB-023
SECONDARY_OBLIGATIONS: All other obligations

PURPOSE: Qualify exact integrated controls and claim-specific evidence.
CURRENT_PRODUCTION_SEAM: Isolation evidence, Governance.Check and CI.
CURRENT_SOURCE_FILES:
L/codex/isolation_profile.ex; L/agent_runtime/runtime_isolation.ex;
L/governance/check.ex; .github/workflows/make-all.yml;
.github/actions/setup-linux-elixir/action.yml
CURRENT_SYMBOLS: admit/verify/evidence; Governance.Check.validate.
CURRENT_TESTS:
T/runtime_isolation_actual_codex_test.exs; T/governance_check_test.exs;
T/credential_channel_enforcement_test.exs
FILES_TO_CREATE:
D/GATE2_IMPLEMENTATION_QUALIFICATION_MANIFEST.json
D/GATE2_EVIDENCE_TRANSFER_REVIEW.md
D/GATE2_CAPACITY_CHARACTERIZATION.md
elixir/test/support/gate2_host_proof/
N/tests/integrated_boundary.rs
FILES_TO_MODIFY:
Current files and scoped Gate 2 evidence/projection documents; never frozen packet.
TEST_FILES_TO_CREATE_OR_MODIFY:
T/gate2_qualification_manifest_test.exs;
T/gate2_actual_codex_boundary_test.exs;
T/gate2_governance_projection_test.exs

CONSUMED_INTERFACES: Package evidence, approved profiles and G00.
PRODUCED_INTERFACES: Qualification manifest and obligation acceptance dossier.
NEW_TYPES_OR_RECORDS: QualificationIdentity and EvidenceApplicability.
PERSISTENCE_BACKEND: Version-controlled manifests and immutable host evidence.
PERSISTED_IDENTITY:
Symphony/upstream/patch/binary/helper/scanner/kernel/LSM/nftables/storage/
crypto/config/policy/capacity identities.
PERSISTED_STATE_MACHINE:
Unqualified -> characterized -> mechanically qualified -> independently reviewed.

LIFECYCLE_DELTA: Activation requires accepted complete qualification.
GUARDS: Separate execution authority and exact identity.
SIDE_EFFECTS: Future authorized proof and evidence persistence.
FAILURE_TRANSITIONS: Failed/uncertain claim blocks qualification.
RESTART_RECONCILIATION: Admission rechecks current facts.
TERMINAL_MEANING: Qualification is not Gate 2 acceptance or H-100 authority.

CREDENTIAL_IMPACT: Synthetic secrets by default.
NETWORK_IMPACT: Live traffic separately authorized.
FILESYSTEM_IMPACT: Bounded fixtures/evidence.
PROCESS_CGROUP_NAMESPACE_IMPACT: Exact integrated host proof.
SOURCE_CONTROL_IMPACT: Evidence persistence; no automatic merge.

MIGRATION_OR_BACKCOMPAT: Preserve accepted H-080B proof/CI.
ROLLBACK_OR_FAIL_CLOSED_BEHAVIOR: Identity mismatch disables Gate 2.
TEST_STRATEGY: K programme.
NEGATIVE_CONTROLS: All BP/ET controls and unsupported host/configuration.
FAILURE_INJECTION: Integrated crash/restart/teardown.
RECOVERY_PROOF: Resource/credential/request/publication recovery.
MECHANICAL_PROOF: Exact evidence for every obligation.
INDEPENDENT_REVIEW_REQUIREMENTS:
Security, scanner, publication, persistence and governance.

REQUIRES_HOST_PRIVILEGE: YES.
REQUIRES_CODEX_EXECUTION_LATER: YES.
REQUIRES_PROVIDER_EXECUTION_LATER: Only explicit live compatibility authority.
DEPENDENCIES: P01..P08, G00, accepted numerical profiles.
UNBLOCKS: Separate activation/acceptance decisions.
ACCEPTANCE_CONDITION: All 26 obligation dispositions accepted with exact evidence.
```

## F. Dependency DAG and sequencing

The hard governance prerequisite remains:

```text
Separate permission for governance PR and its Codex-triggering CI
→ persist scanner addendum/policy/projection
→ independent review
→ human merge
→ verify protected-main SHA/tree
→ verify exact policy/addendum blobs and hashes
→ verify original packet unchanged
→ explicitly rebind this plan to the successor baseline
→ consider implementation authorization
```

Required G00 governance files, in addition to this canonical plan:

```text
D/GATE2_SCANNER_GOVERNANCE_ADDENDUM_2026-11-03.md
D/GATE2_V1_CANDIDATE_VALIDATION_1.0.0.json
D/GATE2_SCANNER_GOVERNANCE_PROJECTION.json
```

The addendum references the exact combined freeze hash. The current narrow authorization permits this G00 governance PR and its required CI only. It grants no implementation PR authority. Human merge and successor-baseline rebinding remain pending.

Package hard dependencies:

```text
G00 → P01
P01 → P08
P01 → P05
P01 + P08 → P02
P01 + P08 → P03
P02 + P03 + P05 + P08 → P04
P02 + P08 → P06 pure scanner/publication fixtures
P04 → P06 integrated runtime handoff
P05 + P06 → P07
P01..P08 + accepted limits → P09
P09 → separate activation/acceptance consideration
```

P05 and P08 may proceed independently after P01. P02 and P03 may proceed in parallel after P08. P06's pure validator work does not require live provider execution.

P01 is still dormant. P08 remains the next mandatory slice before authoritative cleanup release exists.

## G. Exact file/module/interface touch map

Package file lists above are normative. New responsibilities remain outside Orchestrator.

The native implementation is a proposed Rust workspace:

```text
N/Cargo.toml
N/Cargo.lock
N/src/bin/attempt_boundary.rs
N/src/bin/credential_vault.rs
N/src/bin/candidate_validator.rs
```

It is installed as root-owned verified executables with root-owned, non-writable ancestors. It is not a privileged NIF or a new persistent daemon.

The **source-audited downstream patch set** is:

```text
U/app-server/src/main.rs
U/app-server/src/lib.rs
U/app-server/src/message_processor.rs
U/app-server/Cargo.toml

U/core/src/lib.rs
U/core/src/config/mod.rs
U/core/src/client.rs
U/core/src/exec.rs
U/core/src/unified_exec/process_manager.rs
U/core/src/tools/spec.rs
U/core/src/shell_snapshot.rs

U/http-client/src/client_builder.rs
U/http-client/src/route_aware_client_pool.rs
U/http-client/src/route_aware_client_pool/execution.rs
U/protocol/src/shell_environment.rs

U/exec-server/src/lib.rs
```

New upstream files:

```text
U/app-server/src/symphony_gate2.rs
U/core/src/symphony_boundary/mod.rs
U/core/src/symphony_boundary/transport.rs
U/core/src/symphony_boundary/hardening.rs
U/core/src/symphony_boundary/lease_resolver.rs
U/exec-server/src/symphony_backend.rs
```

The broker client belongs inside exec-server because `ExecProcessEventLog` is crate-private. This permits a complete `ExecProcess` implementation with retained reads, wakeups and pushed output events without exposing internal fields or returning a fake `tokio::process::Child`.

The selected core dispatch directly selects that backend. Consequently:

- `exec-server/src/environment.rs` is unchanged.
- The ordinary local `LocalProcess` backend is not used for Gate 2 tools.
- Existing `transport.rs`, `endpoint/session.rs`, `endpoint/responses.rs` and `core/src/exec_env.rs` are unchanged. The route-aware pool and its execution path change only for lease generation/deadline enforcement and the qualified no-replay transport contract.

The new strict standalone app-server entry avoids CLI/arg0 bootstrap. The Gate 2 runtime manifest identifies this exact artifact as the patched `0.162.1` app-server. Legacy CI/runtime artifact selection remains unchanged.

## H. Lifecycle and state-model deltas

All frozen lifecycle failure codes remain distinguishable. The following supplies owners, guards, effects, durable records, recovery and terminal meanings.

### Resource transition contract

```text
none → reserved
Owner: Boundary
Guard: unique current host-bound resource identity
Order: reserve and sync
Effect: none
Failure: storage block
Restart: discover intent
Terminal meaning: no allocation implied

reserved → allocating
Owner: P02
Guard: active complete grant and capacity reservation
Order: allocation intent synced before allocation
Effect: create planned resource
Failure: cleanup_unverified
Restart: discover actual resource by stable identity
Terminal meaning: nonterminal

allocating → allocated
Owner: P02
Guard: observed identity matches plan
Order: native evidence first, ledger sync second
Effect: expose host handle
Failure: quarantine
Restart: re-observe, never trust old handle
Terminal meaning: nonterminal

allocated → active
Owner: Boundary
Guard: current grant and complete controls
Order: active record synced before use permit
Effect: bounded use
Failure: fencing
Restart: active use is not restored
Terminal meaning: nonterminal

any usable state → fencing
Owner: Boundary
Guard: matching authority-reducing request
Order: disable permits and sync before enforcement
Effect: revoke leases and stop writers
Failure: cleanup_unverified
Restart: repeat fencing, not work
Terminal meaning: nonterminal

fencing → fenced
Owner: P08 verifier
Guard: positive exact writer/containment proof
Order: immutable evidence, then ledger sync
Effect: permit host capture/cleanup phase
Failure: cleanup_unverified
Restart: fresh verification
Terminal meaning: no surviving writer

fenced → destroying
Owner: P02 cleanup owner
Guard: trusted ownership
Order: destroy intent synced
Effect: normal unmount/detach/remove
Failure: cleanup_unverified
Restart: reconcile remaining references
Terminal meaning: nonterminal

destroying → absent_verified
Owner: P08 verifier
Guard: complete current absence evidence
Order: evidence persisted before ledger sync
Effect: none
Failure: cleanup_unverified
Restart: no authority restoration
Terminal meaning: this resource is absent under the bound observation

uncertain → quarantined
Owner: recovery owner
Guard: unresolved ownership/cleanup/disclosure
Order: quarantine synced
Effect: block unsafe reuse
Failure: host admission blocked if persistence fails
Restart: quarantine retained
Terminal meaning: terminal disposition for this generation
```

P01 permits reservation, fencing intent and quarantine only. Other producers return `:gate2_profile_incomplete` until installed and qualified.

### Complete domain lifecycles

- **LC-01 RuntimeAttempt:** Orchestrator owns `CREATED → PREPARED → RUNNING → QUIESCING → FENCED → CLEANING → CLEANUP_VERIFICATION → VERIFIED_CLEAN`. Matching grant/resource evidence guards each transition. Failures retain frozen failure codes and quarantine uncertainty. Restart restores no RUNNING state.

- **LC-02 Workspace:** Workspace/Ownership owns `reserved → provisioning → owned → release_pending → released`. Intent precedes allocation/destruction. Unknown identity or absence blocks reuse. `released` alone does not prove attempt cleanliness.

- **LC-03 Writable state:** P02 owns allocation/use/destruction; P08 owns absence verdict. Every object has stable ownership and finite bounds. Unknown FD/mount/backing references quarantine. Path absence is insufficient.

- **LC-04 Enrollment:** SubscriptionManager/vault owns the complete required sequence from UNREGISTERED through RENEWABLE. State/nonce/PKCE/client/identity/scopes guard activation. All callback/exchange/persistence failures leave inactive registration. Restart never launches authentication.

- **LC-05 Credential refresh:** Vault owns intent, refresh, replacement receipt, durable replacement commit and old-set retirement. The registration-wide admission/materialization lock and refresh barrier in J2a require verified drain before refresh. Uncertain response/commit blocks dispatch; rejection enters reauth recovery.

- **LC-06 Attempt provider grant:** Boundary owns authorization, materialization, activation, fencing and local-use disablement. Each state binds the single holder incarnation and immutable credential generation. No holder/token rollover or thread/resume occurs within a grant. Restart restores no environment or lease.

- **LC-07 Upstream validity:** SubscriptionManager distinguishes valid, expired/revoked, suspected exposure, reuse blocked and invalidation unconfirmed. Only actual provider evidence or verified expiry establishes stronger invalidity. Local deletion/death does not.

- **LC-08 Inference effect:** RequestLedger owns admission, possible send, evidenced send/acceptance, streaming and terminal result. Uncertain send/stream enters reconciliation, then unresolved ambiguity if no authoritative lookup exists. No automatic retry.

- **LC-09 Source output:** Publisher/validator own separate stages: writer fence, exact object, sealed stage, validation, identity reconfirmation and promotion. FAIL/UNCERTAIN/movement denies promotion.

- **LC-10 Publication:** PublicationLedger records intent before push/PR effect. Branch and PR ambiguity require fresh observation. Success ends at fresh CandidateRef capture, not merge/completion.

- **LC-11 Plane effect:** Existing TransitionCoordinator/ledger retain submit-once and fresh Plane reconciliation. Unresolved effect suspends/escalates.

- **LC-12 Review/merge/completion:** SourceControl, independent reviewer and human merger preserve exact candidate/tree/policy. Movement invalidates review/check bindings. Restart revalidates remote facts.

- **LC-13 Restart:** Recovery owner syncs a new generation before discovery, then fences/reconciles/cleans/verifies. Unknown ownership or observation completeness blocks reuse. A later contrary observation creates a new generation.

- **LC-14 Quarantine:** Trusted recovery/operator boundary owns blocked state and resolution. Operator acknowledgement is not cleanup proof. Release permits consideration of a fresh authorization only.

Additional explicit lifecycles:

- **SourceAdmissionPolicy:** `PROPOSED → HOST_AUTHORIZED → GRANT_BOUND → CLOSED`. Host authority guards approval; canonical policy is persisted before grant binding. Runtime suggestions cannot advance it. Revision requires a new authorization/grant.

- **SourceManifest:** `BASELINE_BOUND → WRITERS_FENCED → CAPTURING → CLASSIFIED → OBJECTS_BUILT → SEALED → STAGED → VALIDATED → IDENTITY_RECONFIRMED → CONSUMED`. Host capture owns construction, validator owns validation. Unknown classification enters `MANIFEST_UNCERTAIN`; definite forbidden material enters `MANIFEST_REJECTED`. Sealed records are immutable. Restart never resumes capture from a mutable workspace without a new fence/capture generation.

- **Migration:** `REQUESTED → SOURCE_VALIDATED → TARGET_STAGED → TARGET_VERIFIED → CANONICAL_REPLACED → COMMITTED`. Offline host maintenance owns it. Normal startup is blocked during an incomplete journal. Details are in I.

- **Vault key rotation:** `PREPARED → REENCRYPTING → MANIFEST_COMMITTED → OLD_KEY_RETIRED`. Vault maintenance owns it. It cannot alter credential generations or refresh automatically. Failure leaves a recoverable journal and blocks affected use.

## I. Persistence, schemas and recovery design

### I.1 Exact AttemptLedger model

Selected model: **explicit whole-ledger eager migration, atomically replacing the canonical DETS file**.

There is never a ledger containing mixed record versions.

Before migration:

```text
metadata schema = 1
all current/history records = schema 1
Gate 2 binding forbidden
```

After migration:

```text
metadata schema = 2
all current/history records = schema 2
each record has explicit boundary_binding
legacy and Gate 2 lineages may coexist as schema-2 records
```

Legacy-only projects may remain entirely schema 1 after deploying the new binary. Opening a ledger does not migrate it. Selecting `gate2_foundation` against schema 1 returns `:migration_required`.

Version-2 metadata retains exactly the existing metadata keys:

```text
schema_version
project_namespace
tracker_identity
```

This ensures the pinned old binary reaches its existing unsupported-version check and refuses schema 2.

Every v2 current/history record contains the existing record fields plus:

```text
boundary_binding =
  %{kind: :legacy}
or
  %{
    kind: :gate2,
    binding_version: 1,
    lineage_binding_id: opaque_id,
    resource_ledger_namespace: bounded_namespace
  }
```

The kind and Gate 2 binding identity are immutable for that lineage. Current grant references remain in the authority fence/resource ledger, so fresh attempts do not require changing the lineage discriminator.

Record construction uses the opened ledger's schema, not a global constant. `schema_version/0` reports the latest supported format; a new `schema_version/1` reports the opened ledger's format.

Migration transforms **all metadata, current and history rows**. Existing records receive schema 2 and `kind: :legacy`; their safety counters, identities, fence semantics and history facts are preserved.

### I.2 Migration transaction

The explicit maintenance command requires a stopped application, closed DETS handles and an exclusive host lock. It is not run by normal startup or workflow reload.

Proposed API:

```elixir
@type migration_request :: %{
  project_namespace: String.t(),
  tracker_identity_sha256: String.t(),
  authority_ref: String.t(),
  source_schema: 1,
  target_schema: 2
}

@type migration_receipt :: %{
  schema_version: 1,
  migration_id: String.t(),
  project_namespace: String.t(),
  source_records_sha256: String.t(),
  target_records_sha256: String.t(),
  current_record_count: non_neg_integer(),
  history_record_count: non_neg_integer(),
  target_schema: 2,
  committed: true
}

@spec migrate_v1_to_v2(
  Path.t(), migration_request()
) :: {:ok, migration_receipt()} | {:error, AttemptBoundary.error()}
```

The path must equal the configured host ledger path; it is not a runtime-selected source/destination.

Ordering:

1. Acquire the exclusive maintenance lock and verify application/DETS closure.
2. Open source with automatic repair disabled; validate the complete schema-1 ledger.
3. Compute a deterministic logical-record digest.
4. Persist/fsync a migration journal and parent directory.
5. Write a same-filesystem temporary DETS table containing complete schema-2 metadata/current/history.
6. Sync and close it; reopen read-only for complete validation and target logical digest.
7. Close all source/stage handles.
8. Atomically rename the verified stage over the canonical path.
9. Fsync the parent directory.
10. Persist/fsync the committed receipt and journal state.
11. Permit normal v2 startup.

The journal contains migration ID, namespace/tracker digest, schemas, source/target logical digests, stage basename, counts and phase. It contains no credentials.

The canonical replacement is the data commit point. The completion receipt is the admission barrier.

Crash behavior:

- Before replacement, canonical source remains wholly v1.
- After replacement, canonical source is wholly v2.
- An incomplete journal blocks normal startup in either case.
- Maintenance recovery validates the canonical file and journal before completing or aborting.
- Uncertain rename/directory-sync state returns `:migration_commit_uncertain`.
- Abandoned stages are never chosen merely because they exist.
- Abort is allowed only before replacement, with the unchanged valid v1 source.
- After replacement there is no downgrade. Repair proceeds forward.

For a new Gate 2 project, maintenance first creates/closes an empty valid v1 ledger, then uses the same migration protocol.

Old binaries refuse the upgraded metadata. Deployment must not restore the old file or run old binaries against a migrated project.

### I.3 Mixed projects, history and rearm

A schema-2 project may contain legacy lineages and Gate 2 lineages. Dispatch chooses semantics from the stored binding, never from a caller's requested mode.

All writers preserve the binding, including `put`, `persist_safety`, clear, close, history copying, both `fence_attempt` branches and rearm.

Legacy `rearm/5` remains valid for legacy records. For Gate 2 records it returns `:gate2_boundary_required`. A future Gate 2 rearm requires the complete release transaction and existing host rearm authority; it archives the old binding and creates a new Gate 2 lineage binding. It cannot produce a legacy current lineage for a Gate 2-bound work item.

V1 metadata with v2 records, v2 metadata with v1 records, unknown binding shapes, namespace mismatch or corrupt history all fail startup. No partial migration or automatic repair is attempted.

### I.4 SourceAdmissionPolicy and SourceManifest

The trusted construction policy is versioned separately from scanner policy:

```text
schema_version: G2-SOURCE-ADMISSION-1.0.0
policy_id, policy_version, policy_sha256
repository_identity
baseline_commit_sha, baseline_tree_sha
work_item_id
authority_ref
revision
tracked_path_permissions[]
new_path_permissions[]
intrinsic_exclusion_rules[]
capacity_profile_sha256
```

Each path permission has:

```text
canonical_path
permitted_operations
permitted_post_modes
source_class: source_text | source_binary | source_executable
maximum_bytes
```

New-path permissions are finite exact paths, not runtime-selected globs. They come from the trusted work-item/source authorization. If a new path was not authorized, runtime input may propose it, but cannot include it in the current candidate. A new host decision and fresh grant are required.

SourceManifest's sealed schema is:

```text
schema_version: G2-SOURCE-MANIFEST-1.0.0
manifest_id
manifest_sha256
repository_identity
git_object_format: sha1
baseline_commit_sha
baseline_tree_sha
candidate_commit_sha
candidate_tree_sha
work_item_id
runtime_identity:
  runtime_attempt_id
  work_item_id
  lineage_generation
  responsibility
  runtime_profile
grant_id
workspace_resource_id
workspace_ownership_id
workspace_allocation_identity_sha256
source_admission_policy_id/version/sha256
writer_fence_evidence_ref
capture_generation
revision
state
entries[]
excluded_entries[]
capture_evidence_ref
created_at
sealed_at
```

Each entry contains:

```text
canonical_path
operation: keep | add | modify | delete | mode_change
pre_image:
  mode
  git_blob_sha
  content_sha256
  byte_length
or null
post_image:
  mode
  git_blob_sha
  content_sha256
  byte_length
or null
source_class
classification: admitted_source
policy_rule_id
capture_object_identity_sha256
```

Excluded entries contain path digest, exclusion rule and disposition only. They never contribute bytes to the candidate.

Rename is represented as delete plus add. No rename heuristic grants authority.

Construction:

1. Resolve the exact trusted baseline and authorized path policy.
2. Fence all writers and establish the fence evidence.
3. Make the source view read-only.
4. Enumerate through the trusted root descriptor using `openat2` with beneath/no-symlink/no-magic-link restrictions.
5. Compare baseline paths with captured entries:
   - present with changed bytes: modify;
   - absent: delete;
   - absent from baseline but explicitly authorized: add;
   - same bytes with changed executable status: mode change;
   - unchanged: keep.
6. Capture bytes through stable descriptors, recording identity before/after read.
7. Construct explicit Git blobs/tree/commit without filters, hooks or add-all.
8. Bind resulting identities and persist the sealed manifest.
9. Build scanner stage only from that exact Git object graph.

Executable mode uses an explicit Git-mode rule. Only canonical `100644`/`100755` is emitted; setuid/setgid, unsupported object types and uncertain mode provenance are rejected. Content bytes are never normalized.

Intrinsic exclusions cover:

- `.git` metadata and aliases;
- all non-source resource mounts identified by AttemptResourceLedger;
- HOME/XDG/temp/provider-private/diagnostic/generic-output domains;
- external links, sockets, devices and unsupported filesystem objects.

Nested `.git` entries or a coherent nested/bare repository structure are not imported as source authority. They block capture pending resolution. Ordinary `.gitignore` and `.github` source are not confused with `.git`.

A file's suffix or runtime declaration does not establish source status. The final classifier is the trusted, digest-bound SourceAdmissionPolicy applied to the segregated source workspace. A README and arbitrary prose cannot be distinguished safely from bytes alone; exact path/operation authorization supplies that authority. Scanner content/secret rules still apply to admitted source.

Known non-source domains cannot become source merely through a path suggestion. Suspected copying of private/generic state, missing policy membership or ambiguous provenance yields `MANIFEST_UNCERTAIN` and publication denial.

Any baseline, writer fence, workspace allocation, path policy, captured byte, mode, manifest, commit or tree movement invalidates the generation. A sealed manifest is never edited into validity.

### I.5 Other durable authority records

All new records have a strict version, record ID, namespace, revision, identity digest and immutable history where applicable. Required payloads are:

- **CapacityReservation:** grant/resource IDs; capacity-profile digest; per-domain bytes/inodes; pids/memory/CPU/time/IO/FD limits; aggregate reservation ID; state and release evidence.
- **NativeAllocationJournal:** allocation/resource/grant IDs; planned FS UUID; backing inode identity; loop identity; namespace/mount IDs; phase and evidence refs.
- **SubscriptionRegistration:** registration/account/issuer/client/host/scopes; credential-generation reference; health/reauth/revocation state.
- **CredentialSetGeneration:** exact encrypted record/key identity, registration, generation, token timing and verified identity reference.
- **RefreshIntent:** registration, old generation, request ID, state, replacement reference and ambiguity disposition.
- **ToolBinding:** grant/role/work item, catalog/schema digests, bounds and selected candidate reference.
- **HolderIncarnation:** grant/runtime/credential generation, boot/PID-start/UID/cgroup/namespace/executable/profile/FD identities and state.
- **NetworkLease:** complete schema in J6, including resolver/nftables/client-pool/request generation agreement and boot-time expiry.
- **ProviderRequestRecord:** grant/holder/immutable credential generation, request UUID/ordinal/method/URL, lease ID/generation, resolver/nftables configuration digests, client pool ID, admission/possible-send/effect states, bounded upstream IDs and terminal/reconciliation evidence.
- **SourcePublicationRecord:** repo/work item/lineage/grant/series/publication generation, branch/base/manifest/commit/tree/stage/scan/recipe/envelope/metadata IDs, push/PR intent and observations, CandidateRef and ambiguity state. Complete additional schemas are in J9.
- **ValidationEvidence:** exact schema in J, including policy/implementation/commit/tree/stage identities and bounded rule results.
- **CleanupEvidence:** grant/runtime/fence/resource-set/current verification generation, positive observations, verifier identity, local-clean/disclosure dispositions and separate unresolved-effect refs.
- **CandidateValidationBinding:** CandidateRef fingerprint, tree, manifest/publication/validation/commit-recipe/envelope/metadata digests and source-control policy fingerprint.
- **QualificationIdentity/EvidenceApplicability:** exact component identities, claim IDs, evidence refs and independent acceptance dispositions.

References are resolved against their owning store. Possession of a reference or digest is not authority.

### I.6 Release and effect ordering

Gate 2 release remains:

1. Disable new permits durably.
2. Revoke local use and fence writers.
3. Persist complete cleanup evidence.
4. Fixed verifier resolves and checks the current resource-set/generation.
5. Persist resource/grant release-verification phase.
6. Release AttemptLedger using that same reference.
7. Persist release completion.

New admission requires agreement between the ledgers. A crash after fence release cannot reopen through legacy `begin_attempt`, rearm or release.

Inference, Plane and GitHub effects keep separate ledgers and reconciliation owners. Local resource release never erases an unresolved external effect.

## J. Credential, storage, network, scanner and publication design

### J1. Exact P02 Linux storage

Selected primitive: **fresh plain ext4 filesystems in fully preallocated regular files, attached through Linux loop devices**.

Per-attempt encryption is removed. Frozen authority requires isolation, bounds, ownership and cleanup; it does not require inventing a second storage-key lifecycle.

Allocation:

1. Reserve aggregate capacity and persist allocation intent.
2. Create a unique backing file under the root-owned resource store with `O_CREAT|O_EXCL|O_NOFOLLOW`, mode `0600`.
3. Use `fallocate(fd, 0, 0, approved_image_bytes)`. Sparse/truncate-only allocation is forbidden.
4. Fsync the backing file and parent directory.
5. Attach with `LOOP_CONFIGURE`, a finite size limit and `LO_FLAGS_AUTOCLEAR`.
6. Format ext4 with a preselected UUID, 4096-byte blocks, approved inode count, zero reserved-block percentage, internal journal and non-lazy inode/journal initialization.
7. Use a pinned root-owned mke2fs configuration and qualified feature set. Verify actual block/inode totals do not exceed the accepted bounds.
8. Persist observed loop/FS identity before mounting or exposing it.
9. Mount inside a recursively private mount namespace.

The byte cap is the finite block-device/image capacity. Inodes are capped by the formatted filesystem's verified inode total. No growth, resize or device access is available to runtime UIDs.

Source mounts use `nodev,nosuid,noatime`; executable source is allowed under role policy. Private HOME/XDG/cache/provider-state mounts additionally use `noexec`. Reviewer source is read-only. Runtime `.git` is a separately verified read-only mount.

Temporary/runtime mounts use tmpfs with explicit `size`, `nr_inodes`, ownership and `nodev,nosuid,noexec`. Swap is disabled on the qualified host; cgroups also set `memory.swap.max=0`.

No device-mapper arrangement or storage key exists in this design.

Allocation identity includes host/boot, allocation UUID, backing device/inode/birth identity, loop major/minor and `LOOP_GET_STATUS64` backing identity, filesystem UUID, namespace identity and mount IDs.

Restart uses the journal, loop ioctl/sysfs observations, mount information across relevant namespaces and process FD/mapping inventory. Path names alone are insufficient.

Teardown:

1. Revoke use and prove writers stopped.
2. Close known handles and inspect unknown references.
3. Use normal unmount, never lazy detach as proof.
4. Detach the loop and verify no loop mapping references the backing inode.
5. Remove the backing file, fsync its directory and prove no retained inode/device/mount reference remains.
6. Persist P08 absence evidence.

`EBUSY`, missing observation or an unknown reference means quarantine. Autoclear is a safeguard, not proof.

Backing storage must be an approved local, thick-provisioned ext4 host store. Unknown thin/COW/network/snapshot backing is unsupported until separately qualified. Backup/snapshot agents must exclude attempt stores.

There is **no cryptographic-erasure or physical secure-erasure claim**. Deleted blocks may remain on trusted host media. Runtime isolation denies raw-device access and later attempts receive newly created filesystems. Offline forensic erasure and malicious host root are outside this selected boundary.

Linux loop devices, fallocate allocation and ext4 inode/UUID controls are actual selected interfaces. [Loop](https://man7.org/linux/man-pages/man4/loop.4.html), [fallocate](https://man7.org/linux/man-pages/man2/fallocate.2.html), [mke2fs](https://man7.org/linux/man-pages/man8/mke2fs.8.html).

### J2. Exact P03 encryption and key custody

Selected primitive: **libsodium XChaCha20-Poly1305-IETF authenticated encryption** with a 32-byte master key and independently generated 24-byte nonce per record. [Construction and nonce guidance](https://doc.libsodium.org/secret-key_cryptography/aead/chacha20-poly1305/xchacha20-poly1305_construction).

Record format:

```text
magic: G2CRED1\0
header_length: unsigned 32-bit big-endian
canonical_header_json
ciphertext_length: unsigned 64-bit big-endian
ciphertext_with_authentication_tag
```

Authenticated header:

```text
schema_version: G2-CREDENTIAL-RECORD-1.0.0
algorithm: XCHACHA20-POLY1305-IETF
record_kind
record_id
host_id
registration_id
credential_generation
vault_key_id
nonce
```

The entire header is AEAD additional authenticated data. Payload contains the credential pair, ID token where required, timing, granted scope and verified identity data. No secret appears in the header or ordinary metadata.

Key custody:

- Explicit host vault initialization generates the key using kernel `getrandom`.
- Keys are never derived from host IDs, passwords, tokens or names.
- Key files live under `/var/lib/symphony/gate2/vault/keys/`, root-owned `0600`; directories are `0700`.
- Only the native vault opens them. They are never passed through BEAM, runtime env/argv or workspace.
- The stable host ID is authenticated and checked. Boot ID is audit metadata, not a decryption requirement, so restart/reboot preserves availability.
- Wrong host, missing key, authentication failure or corrupt header blocks the registration.
- No backup, snapshot or automatic restore is selected for the vault/key store. Restore requires governed recovery and stale-generation reconciliation.

Nonces use `getrandom`; duplicate nonce detection within a key's record inventory causes regeneration before encryption. RNG failure blocks the operation.

Atomic credential commit:

1. Persist refresh intent.
2. Receive the complete replacement pair in vault memory.
3. Encrypt to a new exclusive generation file.
4. Fsync file and directory.
5. Atomically replace the root-owned generation manifest.
6. Fsync directory.
7. Mark replacement committed.
8. Retire old generation according to the journal.

Credential-generation rotation does not rotate the vault key.

Vault-key rotation is separate host maintenance: generate/fsync new key, reencrypt all still-required records with fresh nonces, atomically commit the new manifest, then retire the old key only when no required record references it. Interrupted rotation resumes from its journal; it does not guess a key or refresh credentials.

Key loss requires exceptional reauthentication. Corruption is not repaired by dropping AEAD checks.

Key/token buffers use locked native memory and explicit zeroization; locking failure blocks handling. Core dumps are disabled. No claim is made that all allocator, kernel or TLS copies are physically erased. The protection model denies runtime access and ordinary secret persistence; trusted root remains a trusted principal.

### J2a. Immutable credential generations and registration refresh barrier

### Selected model

A Gate 2 grant's `credential_generation` is immutable.

There is no token replacement inside a running holder, no holder incarnation rollover within the same RuntimeAttempt, and no refresh-driven `thread/resume`.

Current SIWC documentation describes one-hour access tokens and replacement access and refresh tokens on refresh. Its app-server guidance describes restarting the app-server to use a replacement `ACCESS_TOKEN`. Symphony V1 instead bounds each attempt so that its selected access token can cover the entire authorized attempt. A replacement generation serves a later grant. [Token reference](https://developers.openai.com/siwc/token-sharing-open-source/token-reference), [Codex app-server](https://developers.openai.com/siwc/token-sharing-open-source/codex-app-server)

### Admission budget

Before creating or materializing a grant, P03 must establish:

```text
verified remaining access-token lifetime
    >= startup allowance
     + accepted maximum attempt wall time
     + cleanup allowance
     + clock-skew bound
     + safety margin
```

All five quantities are required fields in the accepted capacity profile:

```text
startup_allowance_ms
maximum_attempt_wall_time_ms
cleanup_allowance_ms
clock_skew_bound_ms
credential_safety_margin_ms
```

Missing, malformed or unaccepted values deny admission.

The host computes a conservative expiry deadline from authoritative token expiry information and its trusted clock assessment. It binds that decision to a monotonic deadline for the current boot. Clock uncertainty that prevents establishing sufficient lifetime blocks admission.

If a freshly issued token cannot cover the accepted budget, the profile is incompatible. Dispatch remains blocked. Repeated refresh is not a remedy.

The implementation must not assume every received token has exactly one hour remaining.

### Registration-wide serialization

Grant admission, pending materialization and refresh share the existing P03 registration-level serialized owner.

The owner cannot:

- Admit a grant after entering the refresh barrier.
- Refresh while an old-generation materialization reservation can still launch.
- Retire a generation while an active grant can still use it.
- Substitute another account or registration.

The additional durable record is:

```text
CredentialRefreshBarrier, schema_version = 1

barrier_id
registration_id
account_identity_digest
old_credential_generation
replacement_credential_generation
reason
state
revision

blocked_since
active_grant_ids
pending_materialization_ids
cleanup_evidence_refs
refresh_operation_id
replacement_commit_ref
failure_disposition
```

The record contains no token bytes. P03 owns it. P08 supplies authoritative cleanup references.

### Refresh lifecycle

| Transition | Owner, guard and durable ordering | Failure and restart behavior |
|---|---|---|
| `ACCESS_VALID → REFRESH_BARRIER` | P03 persists the barrier under the registration lock. | A failed durable write blocks further admission. |
| `REFRESH_BARRIER → NEW_ATTEMPT_ADMISSION_BLOCKED` | Confirm every admission/materialization path observes the barrier. | Any uncertain path keeps the registration blocked. |
| `NEW_ATTEMPT_ADMISSION_BLOCKED → ACTIVE_GRANTS_DRAINED` | Existing grants finish within their original deadlines or are fenced. P08 must verify local cleanup for all old-generation holders and materialization resources. | PID absence or elapsed time is insufficient. Quarantine prevents normal progression. |
| `ACTIVE_GRANTS_DRAINED → REFRESHING` | Persist refresh intent before sending. Respect provider refresh timing restrictions. | A lost response enters the existing uncertain credential-rotation state. No blind retry. |
| `REFRESHING → REPLACEMENT_DURABLY_COMMITTED` | Validate and atomically persist the complete replacement credential set. | Partial persistence leaves admission blocked. |
| `REPLACEMENT_DURABLY_COMMITTED → OLD_GENERATION_RETIRED` | Commit the active-generation pointer and retirement record using the reviewed vault transaction ordering. | Restart reconciles the committed pointer and journal. It does not infer success from file presence. |
| `OLD_GENERATION_RETIRED → ADMISSION_REOPENED` | Verify replacement integrity, identity and sufficient lifetime. | Any uncertainty keeps admission blocked. |
| `ADMISSION_REOPENED → ACCESS_VALID` | New grants may bind the replacement generation. | Old grants remain permanently non-reusable. |

"Drained" means verified local authority and resource cleanup. It does not claim upstream requests were cancelled or old bearers became invalid.

An ambiguous provider effect may remain retained after local cleanup. Refresh cannot clear that ambiguity or authorize replay of the affected work.

### Unexpected expiry or revocation

An authoritative authentication failure or loss of valid lifetime causes:

1. Request admission to close.
2. The attempt and network authority to be fenced.
3. Provider request records to preserve their actual observed outcomes.
4. Unresolved effects to enter `RESULT_AMBIGUOUS`.
5. Local cleanup and credential disposition to proceed through P08/P03.

No replacement token enters that holder. No automatic replay occurs after refresh.

Human reauthentication remains exceptional host-level recovery. The runtime cannot launch it.

### Stable host identity

Before first enrollment, the trusted host generates and durably persists:

```text
ext_agent_host_id = urn:uuid:<lowercase UUIDv4>
```

The UUID comes from the operating system cryptographic random source.

It is stable across host restarts, credential rotations and reauthentication. It contains no account identifier, hostname, PID or boot identifier. A cloned deployment must establish its own host identity and enrollment rather than reuse a copied vault.

This selects one of the provider-supported opaque host identity formats. [SIWC overview](https://developers.openai.com/siwc/token-sharing-open-source)

### Exact inference contract

P04 validates the serialized request before requesting the durable pre-send acknowledgment:

```ini
METHOD=POST
URL=https://api.openai.com/v1/responses
TRANSPORT=HTTPS_HTTP_STREAM
STORE=false
STREAM=true
WEBSOCKET=DENIED
GET_/v1/models=DENIED
```

Unsupported capabilities and fields are rejected rather than silently rewritten after request identity is established. The Gate 2 request builder permits only its qualified Responses request schema and selected tool forms.

The request record binds the credential generation, grant, network lease generation and validated request identity. Request construction cannot select a new account, route or credential generation.

These protocol requirements follow current SIWC inference documentation. They do not expand Symphony authority. [Models and inference](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference)

### Acceptance evidence

P03/P04 tests must prove:

- Admission at the exact lifetime threshold and denial below it.
- Missing timing configuration blocks admission.
- A fresh token with insufficient lifetime does not cause a refresh loop.
- Concurrent admission and refresh cannot cross the barrier.
- Pending materialization counts as old-generation authority.
- Missing or stale cleanup evidence prevents drain completion.
- Refresh cannot mutate a grant's credential generation.
- Expiry/revocation fences the holder without token reinjection.
- Restart at each refresh transaction boundary preserves admission blocking.
- Ambiguous inference remains ambiguous after successful refresh.
- Reauthentication preserves host identity and account separation.
- Unsupported request shapes fail before durable send authorization.

### J3. Materialization and process isolation

The accepted design remains:

```text
Orchestrator
→ per-attempt trusted native boundary
→ credential-free resident PID guard
→ transient trusted bootstrap
→ exact app-server exec
```

The bootstrap is forked before receiving token bytes. It opens a one-use host materialization channel after the fork. The host verifies grant, PID/start identity, UID, executable, cgroup and namespace.

Only access is sent. Bootstrap closes the channel and all unapproved FDs, builds the explicit environment and execs the holder. No token-bearing wrapper survives. The guard never receives token bytes or a credential descriptor.

The Gate 2 artifact is the standalone patched app-server from pinned `0.162.1`, avoiding CLI/arg0 bootstrap. At its synchronous entry, before config or Tokio creation, it applies non-dumpability and the holder seccomp policy.

Tools are created by the external per-attempt helper under a different UID, nested PID namespace and networkless namespace. They never fork from bearer-bearing memory.

Proc/memory controls remain:

- distinct holder/guard/tool UIDs and no shared supplemental groups;
- private proc view with `hidepid=2`;
- no holder PID visible inside tool PID namespace;
- AppArmor denial of proc environment/memory, cross-profile ptrace, credential paths and host sockets;
- seccomp denial of ptrace, process_vm, pidfd_getfd, kcmp, bpf/perf and namespace/privilege changes;
- holder denial of process-creating clone/fork/vfork and exec;
- thread creation permitted under the qualified thread flags;
- `clone3` handling is explicitly denied/falls back through the qualified thread path;
- no credential-bearing inherited/transferred FDs;
- pipe-only bounded broker/control protocol, no SCM_RIGHTS support;
- tool FD allowlist only;
- zero core limit, no core collector/kdump/hibernation/swap on qualified hosts.

Failure before verified readiness never enables provider egress. Failure afterward revokes use, retains effect ambiguity where needed and starts cleanup/quarantine.

### J4. Completed pinned Codex process/startup audit

Pinned source:

```ini
UPSTREAM_VERSION=0.162.1
UPSTREAM_COMMIT=092d3acd6bec3e3a14bdc7e7a2810ab628ab759d
UPSTREAM_TREE=572cdecd45cd985f0ad80b63d8b86ffcb345f47a
```

The audit found generic app-server startup unsuitable for Gate 2:

- `run_main_with_transport_options` loads startup/cloud configuration, creates environment services and initializes telemetry/analytics.
- `MessageProcessor::new` unconditionally starts model-refresh and turn-cost workers.
- `Environment::local` installs in-process `LocalProcess`.
- Ordinary local unified exec can bypass `ExecBackend`.
- App-server has no existing seccomp setup.
- `spawn_child_async` returns concrete `tokio::process::Child`; it is not a broker abstraction.

The selected contract therefore has a synchronous early branch in standalone `app-server/src/main.rs`, before `arg0_dispatch_or_else`, clap/config and runtime creation. New `symphony_gate2.rs` constructs only strict local services from a sealed host manifest.

A process-local, immutable Gate 2 context applies to all sessions in that holder. It cannot be changed by RPC or workflow overrides.

Process inventory:

1. **Classic exec. BROKERED.**
   `core/src/exec.rs::{execute_exec_request,exec}` takes an early Gate 2 backend path. It adapts bounded output, timeout, cancellation and termination through `ExecProcess`; no local Child is created.

2. **Unified exec. BROKERED.**
   `core/src/unified_exec/process_manager.rs` selects the Symphony backend for local execution even without snapshots. It never falls through to `codex_sandboxing::spawn_process`.

3. **App-server process RPCs. CONFIGURATION_DISABLED.**
   `message_processor.rs::dispatch_initialized_client_request` rejects `Process*`, `CommandExec*`, `OneOffCommandExec` and `ThreadShellCommand` before task dispatch. The separate process processor is not invoked.

4. **Shell snapshots. CONFIGURATION_DISABLED.**
   `core/src/shell_snapshot.rs::run_script_with_timeout` rejects Gate 2. The selected backend rejects snapshot prewarm/request options and never calls `exec-server/src/shell_snapshot.rs::capture_snapshot`.

5. **Hooks. CONFIGURATION_DISABLED.**
   Hook configuration is empty and immutable; no hook engine/registry command runner is registered. Relevant paths are `hooks/src/engine/command_runner.rs` and `hooks/src/registry.rs`.

6. **MCP stdio/helpers. CONFIGURATION_DISABLED.**
   No MCP servers are instantiated; MCP RPCs are rejected. `rmcp-client/src/stdio_server_launcher.rs` is unreachable.

7. **Skills/helpers. split classification.**
   Approved local skill text is untrusted input. Script commands selected through shell tools are BROKERED. Remote skill/plugin installation, refresh and helper launch are CONFIGURATION_DISABLED. Text cannot grant a host capability.

8. **Nested agents. CONFIGURATION_DISABLED.**
   Multi-agent tool specifications and `multi_agents`/`multi_agents_v2` spawn handlers are excluded. They cannot create a session lacking Gate 2 context.

9. **Apply patch. CONFIGURATION_DISABLED as a direct built-in.**
   The direct handler is not in the Gate 2 tool catalog. A shell-invoked patch command is BROKERED under tool UID/role mounts. The pinned direct handler itself is a filesystem operation, not an OS spawn.

10. **Repository/Git helpers. KERNEL_DENIED_AND_NOT_REQUIRED.**
    Direct helper paths in `git-utils`, `worktree`, rollout search and file search are not required capabilities. Optional metadata failure cannot become authority. Shell `git diff/status` may run through the broker with read-only `.git`; publication remains host-only.

11. **Shell/version probes. CONFIGURATION_DISABLED or KERNEL_DENIED_AND_NOT_REQUIRED.**
    Gate 2 uses the host-declared POSIX shell and disables PowerShell probing. Environment metadata comes from the sealed launch manifest, not child commands.

12. **Plugins/marketplaces/npm. CONFIGURATION_DISABLED.**
    No startup sync or install/upgrade service is created; related RPCs are rejected. Relevant paths include `core-plugins/src/startup_sync.rs`, marketplace install/upgrade and `npm_source.rs`.

13. **External auth/Bedrock/gateway helpers. CONFIGURATION_DISABLED.**
    Custom SIWC env provider only. External bearer commands, Bedrock credential helpers and runtime refresh/login are absent.

14. **Code-mode, remote executor/control, daemon/update helpers. CONFIGURATION_DISABLED.**
    Strict startup omits them. It does not call generic environment discovery, daemon/update or remote-control setup.

15. **Feedback doctor/platform/UI utilities. CONFIGURATION_DISABLED.**
    Their RPCs are rejected. Non-Linux/UI/test/benchmark binaries are outside the selected artifact path.

16. **Native sandbox/fs helpers inside the holder. KERNEL_DENIED_AND_NOT_REQUIRED.**
    Containment is installed by the host helper. Holder-side bwrap/sandbox/fs-helper process launch is not used.

17. **Tokio tasks and runtime threads. permitted in-process work.**
    They are not OS tool processes. The seccomp policy preserves required threads.

```ini
REQUIRED_DIRECT_SPAWN_COUNT=0
```

Kernel denial is a backstop for optional helper attempts. Required tool execution remains brokered and functional.

### J5. Network-producing subsystem audit

Before readiness, strict startup omits:

- cloud/startup config fetching and bootstrap factory resolution;
- remote environment discovery/connections;
- code-mode gRPC;
- OTel exporters/reloader and analytics clients;
- remote-control enrollment/transport;
- plugins/marketplace startup;
- MCP/apps connectors;
- runtime auth refresh/login/workload helpers;
- daemon/update checks.

`MessageProcessor` receives an explicit Gate 2 construction mode suppressing model-refresh, turn-cost and plugin workers. Background `/models` is not merely allowed to fail later.

After readiness:

- Responses HTTP is the sole permitted network subsystem.
- Models use the host-selected/bundled data; no catalog refresh.
- Realtime/WebSocket, memories, uploads/images, feedback, connectors, plugins, remote execution and account mutation are disabled.
- RPC admission is an allowlist of the host session operations required for initialize/thread/turn control. Config writes and optional service/process/auth RPCs are rejected before dispatch.

All configured HTTP factory consumers receive the same exact-URL policy. Unsupported SDK transports are denied. No fallback standalone factory is constructed in Gate 2.

The required patch changes now correspond to these closed source contracts. Runtime qualification tests the defined contract; it is not tasked with choosing missing architecture.

### J6. HTTP egress and provider effects

Retained Linux mechanism:

- dedicated holder netns and veth;
- root-owned nftables INPUT denial to host-local services;
- FORWARD permission only for TCP/443 to current approved IPv4/IPv6 provider sets;
- address-set check on every packet, including established traffic;
- no external interface in tool/guard namespaces;
- trusted host DNS, recorded TTL/CNAME evidence and timed nftables entries;
- atomic updates; stale-address removal revokes existing packet authority;
- no runtime DNS, proxy, raw socket or control-plane route.

Lease changes pause requests, revoke the old lease and close connections before a newly verified lease. Interrupted requests remain ambiguous.

Inside Codex:

- reuse `NetworkPolicy::restrict_to_endpoints`;
- exact `POST https://api.openai.com/v1/responses`, no query;
- reuse the pinned direct pool branch and no-redirect builder;
- strip proxy/custom trust environment and use qualified TLS trust;
- set request/stream retries to zero;
- add underlying reqwest `retry::never()` opt-in;
- wrap transport with durable host acknowledgement.

Before underlying invocation, RequestLedger synchronizes admission and `send_may_have_occurred=true`. This is conservative permission, not evidence of actual send.

`SENT_UPSTREAM` and `PROVIDER_ACCEPTED` require attributable evidence. Completion requires the terminal completed event. The effect ledger retains IDs/status, not prompts or response text.

A crash after possible invocation becomes ambiguous. Without a real authoritative same-request lookup, it remains unresolved. No process death, refresh, timeout or local deletion authorizes replay.

### Selected resolver and client contract

The patched Gate 2 client uses a custom implementation of reqwest's `Resolve` trait. It consumes an immutable host-issued `NetworkLease` snapshot.

The request URL remains:

```text
https://api.openai.com/v1/responses
```

The resolver supplies only the lease's approved socket addresses. The hostname remains intact for HTTP Host, TLS SNI and certificate verification.

There is no fallback to system DNS, network DNS, `/etc/hosts`, proxy resolution or another client builder.

The additional versioned record is:

```text
NetworkLease, schema_version = 1

lease_id
generation
host_id
host_boot_id
runtime_attempt_identity
grant_id
holder_identity
holder_network_namespace_identity

hostname = "api.openai.com"
scheme = "https"
port = 443
approved_ipv4_addresses
approved_ipv6_addresses

issued_boottime_ns
expires_boottime_ns
dns_observation_digest
resolver_configuration_digest
nftables_configuration_digest
client_pool_id

state
revision
```

Addresses are canonical, unique and sorted. An empty address set is invalid. IPv4-mapped IPv6 addresses and host-local, private, multicast, unspecified or otherwise prohibited destinations are rejected.

Expiry uses Linux `CLOCK_BOOTTIME`. Host and holder use the same kernel clock and do not create a time namespace. This prevents suspend from extending lease validity.

A grant binds the approved network policy. Each request admission binds a concrete lease generation. The grant's immutable credential generation is independent of network-lease renewal.

### Resolver behavior

`LeaseResolver::resolve` returns addresses only when all of these hold:

1. The requested hostname is exactly `api.openai.com`.
2. The lease belongs to the current grant, holder and host boot.
3. Its generation is active.
4. Its deadline has not expired.
5. Its resolver configuration matches the host-approved lease.

Every other result is an error. A resolution failure cannot invoke another resolver.

Endpoint enforcement separately requires HTTPS, port 443 and the exact permitted route. A resolver result cannot authorize another port or URL.

### Request admission and pooled connections

DNS checks alone do not protect reused connections. The selected implementation therefore checks the shared, revocable lease guard:

- Before asynchronous route selection.
- After route selection.
- Immediately before executing the prepared HTTP request.

The final check requires equality among:

```text
request lease generation
active host lease generation
resolver generation
nftables generation
client-pool generation
```

It also checks the absolute lease deadline.

Each lease generation owns a fresh `RouteAwareClientPool`. Clients and pools cannot migrate between generations. Existing pool keys based on proxy route do not serve as lease identity.

The durable provider request record gains:

```text
network_lease_id
network_lease_generation
resolver_configuration_digest
nftables_configuration_digest
client_pool_id
```

The host persists these bindings before acknowledging permission to send.

### Lease lifecycle

P04 owns this lifecycle. Only the trusted host can issue or activate a lease.

| Transition | Guard and durable ordering | Side effect and failure behavior |
|---|---|---|
| `LEASE_ACTIVE → LEASE_REFRESH_PENDING` | Persist renewal intent before changing authority. | Trusted host resolves the provider hostname. Resolution failure leaves no replacement authority. |
| `LEASE_REFRESH_PENDING → REQUEST_ADMISSION_PAUSED` | Persist pause, then revoke the current send guard. | New requests are denied. |
| `REQUEST_ADMISSION_PAUSED → OLD_CONNECTIONS_CLOSED` | Stop all users of the old pool and account for admitted requests. | Close the old pool and destroy remaining holder TCP sockets. Unresolved inference results remain ambiguous. |
| `OLD_CONNECTIONS_CLOSED → NEW_ADDRESS_SET_INSTALLED` | Verify old connections are gone. | Atomically replace nftables address sets and read back the installed configuration. |
| `NEW_ADDRESS_SET_INSTALLED → NEW_RESOLVER_GENERATION_INSTALLED` | Kernel configuration must match the replacement lease. | Construct a fresh resolver and fresh client pool. |
| `NEW_RESOLVER_GENERATION_INSTALLED → LEASE_ACTIVE` | Host and holder acknowledgments must identify the same unexpired generation. Persist activation before opening admission. | New sends may proceed. |
| Any state → `LEASE_BLOCKED` | Expiry, identity mismatch, failed verification or uncertain installation. | Deny sends and retain the fence. |
| Any live state → `LEASE_RETIRED` | Verified network cleanup. | The lease can never authorize another request. |

Closing client handles alone is insufficient evidence of connection closure. The native privileged boundary uses `NETLINK_SOCK_DIAG` with `SOCK_DESTROY` inside the holder network namespace and verifies the former connections are absent. Failure to establish closure fences and terminates the holder. It does not restart it within the grant.

The nftables rules enforce address membership and expiry on every packet, including established connections. There is no broad established-connection exception that preserves stale addresses.

A crash during renewal leaves admission closed. Restart recovery fences the holder, reconciles request effects and retires the interrupted lease. It never reconstructs active authority from a stored TTL or observed process alone.

Local socket destruction does not establish upstream cancellation.

### Downstream lease changes

Retain the reviewed strict Gate 2 entry path and existing endpoint-policy reuse. The complete patch list in section G includes these lease-specific changes:

```text
codex-rs/http-client/src/client_builder.rs
codex-rs/http-client/src/route_aware_client_pool.rs
codex-rs/http-client/src/route_aware_client_pool/execution.rs

new:
codex-rs/core/src/symphony_boundary/lease_resolver.rs
```

Responsibilities:

- `client_builder.rs`: carry the lease-aware resolver through the common reqwest builder, including custom-CA construction.
- `route_aware_client_pool.rs`: bind each pool to one immutable lease generation.
- `execution.rs`: enforce the final generation/deadline check before execution.
- `lease_resolver.rs`: implement the exact hostname-to-address contract and revocable lease guard.

No endpoint/session/response transport rewrite is added.

### Acceptance evidence

P04 and P09 must demonstrate:

- HTTPS succeeds against a local TLS fixture while external DNS is unavailable.
- Certificate validation and SNI still use the hostname.
- Unknown names and expired leases fail without a fallback lookup.
- Addresses outside the lease cannot be reached.
- A cached connection cannot bypass expiry or generation revocation.
- Expiry during asynchronous route selection prevents execution.
- Lease movement destroys old connections and creates a distinct pool.
- Partial nftables/resolver installation never opens admission.
- IPv4 and IPv6 obey the same rules.
- Interrupted streams retain their provider-effect ambiguity.

These are future tests and qualification requirements.

### TLS backend fallback and possible-send boundary

Gate 2 TLS transport must never perform a second inference invocation through TLS backend fallback after durable possible-send acknowledgment. P04 must either disable stock `retry_with_rustls` for Gate 2 and select the qualified backend before invocation, or mechanically prove that fallback is strictly pre-HTTP-send and cannot cross the RequestLedger possible-send transition. No post-boundary automatic replay is permitted.

The exact P04/P09 regression requirement is:

```text
gate2 transport never performs tls fallback after possible-send acknowledgement
```

Exercise the narrow stock negotiation-failure classifier, certificate/hostname/trust failures, ambiguous write failures and interruption after acknowledgment. Assert at most one inference invocation and retained ambiguity where applicable. Changing TLS backend cannot create a second SendPermit or reset the request ordinal.


### J7. Scanner binary/content contract

Selected answer is **B: structurally supported ordinary binary formats**, with complete raw-byte application of provenance, secret and size rules.

Disposition is explicit:

- Valid supported PNG/JPEG/MP4, completely inspected with all mandatory rules satisfied: eligible for PASS.
- Unrecognized opaque binary requiring unsupported inspection: UNCERTAIN.
- Supported archive/container completely and deterministically inspected: eligible for PASS.
- Encrypted container, unsupported compression or incomplete expansion: UNCERTAIN.
- Polyglot or multiple valid competing format interpretations: UNCERTAIN.
- Definite prohibited object/link/provenance/content/secret/size violation: FAIL.

No media exemption exists.

`binary_formats.rs` supplies bounded deterministic inspectors:

- PNG: signature, chunk boundaries/order/CRC and complete chunk coverage; inspect bounded decompressed ancillary metadata.
- JPEG: complete marker/segment coverage, scan framing and metadata/embedded thumbnail handling.
- MP4/ISO-BMFF: bounded box traversal, nested container boxes, sample/metadata extents and complete byte coverage.
- Encoded pixel/audio/video essence is media data, not a recursively extracted candidate-file archive. It still receives raw-byte rules.
- Embedded file containers or supported compressed metadata are recursively inspected under bounds.
- Unparsed required structure, ambiguous attachment semantics or extra competing container interpretation yields UNCERTAIN.

ZIP/TAR/gzip/bzip2/xz/zstd support remains. Inspection streams bytes without extraction or normalization.

Current protected media are:

```text
.github/media/elixir-screenshot.png
  blob 850a5e712d4092fc761652653a8a6f6613209373
  115378 bytes

.github/media/symphony-demo-poster.jpg
  blob 7dd6be2eabfad7fede4e132fc16618c8e5824c1e
  90558 bytes

.github/media/symphony-demo.mp4
  blob 32b1f857f45eb901905ea24355b599fb417f53c5
  30446771 bytes

elixir/priv/static/favicon.png
  blob 01a738fc29f12459c895d1f27d89a075e1825391
  17493 bytes
```

The protected tree has permitted Git modes and supported media classes. It therefore has no categorical media-policy obstacle to PASS. Required limits must accommodate at least its 391 entries, 37,506,911 raw blob bytes and 30,446,771-byte largest blob, plus approved inspection requirements. These are measured workload facts, not selected quotas.

No scanner was executed, and no actual PASS is claimed.

### J8. Scanner invocation/evidence

The validator reads a sealed Git-object bundle, accepted policy and bounded request:

```text
candidate_commit_sha
candidate_tree_sha
stage_identity
stage_bundle_sha256
policy_id/version/sha256
scanner_implementation_id/sha256
```

It has no credentials, network, source mutation or extraction authority.

Policy and effective limits use canonical UTF-8 JSON with recursively sorted keys, integer values, declared array order and no insignificant whitespace or final newline. Policy SHA-256 covers the exact policy-file bytes. Limits have a separate digest-bound profile that references that policy. The policy digest is `0d67fe1c0c532294dd3e946618d5bfd40c3d5ce6f50804e4bd20823ae5f756b7`. No mutable feed or runtime suppression exists.

Stable IDs remain under the seven frozen classes:

```text
G2.OBJECT_TYPE.*
G2.PATH_AND_LINK.*
G2.PROVENANCE.*
G2.CONTENT.*
G2.SECRET.*
G2.RESOURCE_SIZE.*
G2.DETERMINISM_AND_IDENTITY.*
```

Secret rules use deterministic byte patterns and structured parsers for private keys, supported credential families and credential/private-state structures. No synthetic-fixture exception is selected.

Evidence implements every required field:

```text
schema_version
policy_id, policy_version, policy_sha256
scanner_implementation_id, scanner_implementation_sha256
candidate_commit_sha, candidate_tree_sha
stage_identity, stage_tree_sha_before, stage_tree_sha_after
result, failure_classes, rule_results
entries_scanned, blobs_scanned, bytes_scanned
allowlist_hits, uncertainty_reasons
started_at, completed_at
```

Findings contain bounded codes, entry ordinals/path digests and rule IDs, never secret matches. Timestamps are host evidence metadata and do not affect classification.

The host persists evidence before publication, then freshly rechecks candidate/tree/stage/manifest identity. Any mismatch or evidence persistence failure invalidates PASS.

Implementation identity binds source, lockfile, build recipe/compiler/target and binary SHA-256. Replacement requires new identity/digest and qualification.

### J9. Publication/output

### Authority and output contract

All publication metadata is host-generated from typed, trusted records.

Runtime/model prose cannot supply:

- Commit parents or headers.
- Author or committer identity.
- Commit messages.
- Branch names.
- PR titles or bodies.

The metadata is the bounded protocol envelope for the source-control candidate. It does not create a generic text-output promotion channel.

### Commit recipe

Add `CommitRecipe`, schema version 1:

```text
recipe_id
recipe_sha256
repository_identity
work_item_identity
work_item_key
publication_series_generation
publication_generation

runtime_attempt_identity
grant_id
source_manifest_id
source_manifest_sha256
writer_fence_evidence_ref

authorized_source_baseline_commit_sha
authorized_source_baseline_tree_sha
candidate_tree_sha
parent_commit_sha

publication_identity_policy_sha256
author_name
author_email
committer_name
committer_email
author_timestamp
committer_timestamp
timezone

message_template_version
message_bytes_sha256
expected_commit_sha

state
revision
```

`work_item_key` is the full SHA-256 of the canonical repository identity and immutable work-item identity. Display text and issue titles are not inputs.

The fixed publication identity is:

```text
Symphony Gate 2 <symphony-gate2@users.noreply.github.com>
```

Any future identity change requires an accepted host publication-profile revision.

The host allocates and persists the commit timestamp once. Author and committer timestamps are identical, use UTC `+0000`, and remain unchanged during reconciliation.

The canonical commit permits exactly one parent and only the expected `tree`, `parent`, `author` and `committer` headers. Runtime Git configuration, hooks, signing helpers and additional headers cannot affect construction.

The message is exactly:

```text
Symphony Gate 2 candidate

Work-Item-Key: <64 lowercase hexadecimal characters>
Publication-Generation: <unsigned decimal generation>
```

It ends with one newline.

### Parent and branch rules

The initial candidate's parent is the exact authorized protected-base commit.

A Fixer replacement for the existing PR has the freshly reconciled prior candidate head as its parent. That prior head must be the exact authorized `SourceManifest` baseline. This produces a fast-forward update and preserves the prohibition on force push.

The PR target base is a separate trusted binding. Unexpected base movement pauses publication for reconciliation.

The branch format is:

```text
symphony/g2/<work_item_key>/s<publication_series_generation>
```

The host allocates the series once for the work item's active PR association. Individual replacement candidates increment `publication_generation` on that same branch.

An ambiguous push or PR response cannot allocate a new series or create a fallback PR.

### Commit-envelope verification

Add a trusted `CommitEnvelopeVerifier`. It reads the actual Git commit object and compares it with the durable recipe.

It verifies:

- Exact tree and single parent.
- Exact author, committer and timestamps.
- Exact permitted headers.
- Exact message bytes.
- Expected Git object identity.

It produces:

```text
CommitEnvelopeEvidence, schema_version = 1

evidence_id
recipe_sha256
candidate_commit_sha
candidate_tree_sha
parent_commit_sha
actual_commit_object_sha256
publication_identity_policy_sha256
result
bounded_failure_codes
```

This check is separate from scanner rule classification.

A usable validation binding requires:

```text
writer fence verified
AND commit envelope verified
AND scanner PASS
AND post-scan commit/tree/stage identity reconfirmed
```

The scanner's policy and tree-classification determinism remain unchanged. A commit-envelope failure denies publication without converting scanner evidence into another result.

### PR metadata record

Add `PublicationMetadata`, schema version 1:

```text
metadata_id
metadata_sha256
publication_record_id
repository_identity
work_item_key
publication_series_generation
publication_generation

branch_name
target_base_ref
target_base_commit_sha
candidate_commit_sha
candidate_tree_sha
commit_recipe_sha256
commit_envelope_evidence_ref
scanner_evidence_ref
candidate_validation_binding_ref

title_template_version
title
body_template_version
body
body_sha256

repository_pr_template_blob
pr_body_contract_identity
trusted_test_fact_refs

state
revision
```

Only the trusted publisher constructs this record. It persists the exact intended metadata before remote mutation.

The PR title is:

```text
Symphony candidate <first 12 work-item-key characters> p<generation>
```

The full work-item identity remains in the durable record and body. Truncated display text is never an authority key.

### Repository-compatible PR body

The host renderer uses the exact heading order required at the pinned baseline:

```markdown
#### Context

Publish a host-validated source candidate for the bound work item.

#### TL;DR

*Publish the exact candidate for independent review and human merge.*

#### Summary

- Candidate: `<candidate_commit_sha>`.
- Tree: `<candidate_tree_sha>`.
- Validation: `<scanner_evidence_digest>`.
- Work item: `<work_item_key>`.
- Publication generation: `<generation>`.

#### Alternatives

- Direct base updates are outside this publication capability.

#### Test Plan

- [ ] `make -C elixir all`; required CI result not yet observed.
- [x] Exact-tree validation; host evidence records PASS for this candidate.
```

Placeholders accept only validated hexadecimal or decimal values. They cannot contain Markdown, newlines or runtime text.

The checked validation item is permitted only after the publisher reads the matching durable PASS and identity-binding evidence. This example describes future behavior and does not claim validation has run now.

Test claims come only from trusted test-execution or CI-observation records bound to the exact candidate and relevant base identity. Raw runtime summaries, logs and claimed test results are excluded.

The initial body leaves required CI unchecked. Later host-generated updates may reflect freshly verified facts. A new candidate invalidates prior review and test acceptance where identity no longer matches.

### Reuse the PR-body validator

The current task is:

```text
elixir/lib/mix/tasks/pr_body.check.ex
Mix.Tasks.PrBody.Check
```

Its current template is:

```text
.github/pull_request_template.md
```

The implementation extracts the existing validation logic into:

```text
elixir/lib/symphony_elixir/pr_body_contract.ex
SymphonyElixir.PrBodyContract.validate/2
```

Both the Mix task and trusted publisher call that pure contract. Extraction preserves existing validation behavior and errors.

The publisher validates the rendered body locally before any GitHub mutation. It requires the accepted template and validator identities. Candidate changes to those files cannot redefine the publisher's contract automatically.

The current validator checks structure, required content and removal of template comments. The publisher separately checks factual bindings and permitted substitutions.

### Ordering and ambiguity

The publication sequence becomes:

```text
WRITERS_FENCED
→ SOURCE_MANIFEST_SEALED
→ COMMIT_RECIPE_DURABLE
→ LOCAL_COMMIT_CONSTRUCTED
→ COMMIT_ENVELOPE_VERIFIED
→ EXACT_TREE_STAGED
→ SCANNER_PASS
→ SAME_COMMIT_TREE_STAGE_RECONFIRMED
→ PR_METADATA_RENDERED_AND_LOCALLY_VALIDATED
→ PUBLICATION_METADATA_DURABLE
→ PUSH_INTENT_DURABLE
→ PUSH_IN_FLIGHT
→ REMOTE_HEAD_CONFIRMED
→ PR_MUTATION_INTENT_DURABLE
→ PR_MUTATION_IN_FLIGHT
→ PR_CONFIRMED
→ CANDIDATE_REF_CAPTURED
```

The commit recipe does not include scanner evidence or PR-body hashes. Those exist only after commit construction, so there is no digest cycle.

A lost push response requires authoritative remote-head observation.

A lost PR response requires fresh observation of the recorded repository, branch and PR association. The host compares title, body digest, head and base before recording confirmation.

Remote metadata mismatch enters `PUBLICATION_RECONCILIATION_REQUIRED`. It does not authorize blind overwrite, duplicate creation or acceptance of the differing metadata.

### Lifecycle ownership and terminal meaning

P06 owns recipes, metadata and publication records. SourceControl verification remains separate.

- Construction failures produce no remote authority.
- Validation failures retain immutable evidence and deny publication.
- Ambiguous mutation states retain the original intent and exact metadata.
- Restart resumes reconciliation, not mutation.
- `PR_CONFIRMED` means the exact intended remote candidate and metadata were freshly observed.
- It does not mean checks passed, review was accepted or merge was authorized.
- P07 still requires exact candidate checks, review, human merge and CompletionProof.

### Acceptance evidence

P06 tests must prove:

- Runtime prose cannot enter any durable metadata field.
- Git environment/configuration cannot change canonical commit construction.
- Wrong parent, extra parent, extra header, identity or message bytes deny publication.
- Initial and Fixer candidates obey their distinct authorized-baseline rules.
- Replacement candidates update the same branch and PR without force push.
- The rendered body passes the repository contract.
- Missing, stale or mismatched validation evidence prevents the checked validation claim.
- Unobserved tests remain unchecked.
- Template or validator identity drift blocks publication.
- Lost push/PR responses reconcile without duplicate mutation.
- Remote title/body/head/base mismatch prevents candidate capture.
- A replacement head invalidates prior review acceptance.

Only Builder/Fixer handoff can request host publication consideration. Reviewer publication remains denied. Only the exact validated source candidate may become durable output; generic result, handoff, provider-private and diagnostic material remains nonpromotable.


## K. Tests, characterization and proof programme

All commands below describe future work. None is authorized now.

### K1. P01 exact tasks

Each task follows red test, minimum change, focused pass, package regression, retained evidence and a separately authorized commit boundary.

**T1. Value schemas**

- [ ] Add the named failing tests and observe the stated red result.
- [ ] Make the minimum production change at the named paths/symbols.
- [ ] Run the focused command and the P01 package regression below.
- [ ] Retain the named evidence and commit only under separate authority.


- Test module/file: `SymphonyElixir.Gate2AttemptTypesTest`, `T/gate2_attempt_types_test.exs`.
- Names:
  - `"grant binds all five runtime identity fields"`
  - `"recovery generation is not lineage generation"`
  - `"cleanup reference shape is not cleanup authority"`
  - `"unknown and secret-bearing fields are rejected"`
- Assertions: complete identity, strict fields, no secret serialization, forged value grants no use.
- Expected red: missing modules/contracts.
- Production symbols: value constructors/reference.
- Minimum change: strict structs/specs/validation only.
- Focused: `mix test --no-start test/symphony_elixir/gate2_attempt_types_test.exs`.
- Evidence/commit: schema fixtures and contract tests.

**T2. Resource durability**

- [ ] Add the named failing tests and observe the stated red result.
- [ ] Make the minimum production change at the named paths/symbols.
- [ ] Run the focused command and the P01 package regression below.
- [ ] Retain the named evidence and commit only under separate authority.


- Module/file: `SymphonyElixir.Gate2AttemptResourceLedgerTest`, `T/gate2_attempt_resource_ledger_test.exs`.
- Names:
  - `"reservation is synchronized before success"`
  - `"duplicate exact reservation is idempotent"`
  - `"conflicting resource identity is rejected"`
  - `"transition rejects stale revision and generation"`
  - `"sync failure never acknowledges transition"`
- Assertions: reopen equality, no rejected revision change, storage uncertainty blocks use.
- Expected red: ledger absent.
- Symbols: `reserve_sync/2`, `transition_sync/4`, startup validation.
- Focused: `mix test --no-start test/symphony_elixir/gate2_attempt_resource_ledger_test.exs`.
- Evidence/commit: ledger and reopen/failure matrix.

**T3. Migration**

- [ ] Add the named failing tests and observe the stated red result.
- [ ] Make the minimum production change at the named paths/symbols.
- [ ] Run the focused command and the P01 package regression below.
- [ ] Retain the named evidence and commit only under separate authority.


- Module/file: `SymphonyElixir.Gate2AttemptMigrationTest`, `T/gate2_attempt_migration_test.exs`.
- Names:
  - `"new binary opens populated v1 without implicit migration"`
  - `"legacy-only project remains v1 until explicit maintenance"`
  - `"eager migration converts metadata current and history together"`
  - `"v2 project supports legacy and gate2 lineages without mixed versions"`
  - `"restart before replacement retains complete v1 and blocks pending journal"`
  - `"restart after replacement sees complete v2 and requires commit completion"`
  - `"old reader refuses upgraded metadata"`
  - `"history and rearm preserve boundary binding"`
  - `"metadata and record version mismatch is corruption"`
  - `"corrupt source or target cannot be committed"`
- Assertions: exact row counts/fields preserved; all versions uniform; no automatic downgrade; no startup during incomplete migration.
- Expected red: migration unsupported.
- Symbols: `AttemptLedgerMigration.migrate_v1_to_v2/2`, metadata/record validators and all record constructors.
- Minimum change: I's exact migration protocol.
- Focused: `mix test --no-start test/symphony_elixir/gate2_attempt_migration_test.exs`.
- Evidence/commit: migration crash-position and old-reader fixture results.

**T4. Legacy bypass closure**

- [ ] Add the named failing tests and observe the stated red result.
- [ ] Make the minimum production change at the named paths/symbols.
- [ ] Run the focused command and the P01 package regression below.
- [ ] Retain the named evidence and commit only under separate authority.


- Module/file: `SymphonyElixir.Gate2AttemptCompatibilityTest`, `T/gate2_attempt_compatibility_test.exs`.
- Names:
  - `"legacy release remains valid for legacy binding"`
  - `"legacy release rejects gate2 bound and already-released records"`
  - `"put cannot remove or replace gate2 binding"`
  - `"safety clear close fence and rearm cannot downgrade binding"`
- Assertions: stable `:attempt_resource_verification_required`; no mutation; complete writer-path coverage.
- Expected red: current identity-only release succeeds.
- Symbols: all AttemptLedger writers/releases/rearm.
- Focused: `mix test --no-start test/symphony_elixir/gate2_attempt_compatibility_test.exs`.
- Evidence/commit: bypass closure and writer checklist.

**T5. Dormant boundary/recovery**

- [ ] Add the named failing tests and observe the stated red result.
- [ ] Make the minimum production change at the named paths/symbols.
- [ ] Run the focused command and the P01 package regression below.
- [ ] Retain the named evidence and commit only under separate authority.


- Module/file: `SymphonyElixir.Gate2AttemptBoundaryTest`, `T/gate2_attempt_boundary_test.exs`.
- Names:
  - `"foundation cannot mint active grant or usable permit"`
  - `"foundation fence reports requested not verified"`
  - `"release rejects missing forged stale and matching-shaped references"`
  - `"configured callback cannot produce cleanup authority"`
  - `"startup syncs new generation and restores no active authority"`
  - `"partial grant binding and ambiguous ownership block reuse"`
- Assertions: no allocation/launch/provider call; exact error union; retained intent/fence.
- Expected red: boundary absent.
- Symbols: all six required boundary functions.
- Focused: `mix test --no-start test/symphony_elixir/gate2_attempt_boundary_test.exs`.
- Evidence/commit: dormant coordinator and recovery.

**T6. Configuration/integration**

- [ ] Add the named failing tests and observe the stated red result.
- [ ] Make the minimum production change at the named paths/symbols.
- [ ] Run the focused command and the P01 package regression below.
- [ ] Retain the named evidence and commit only under separate authority.


- Module/file: `SymphonyElixir.Gate2AttemptConfigTest`, `T/gate2_attempt_config_test.exs`.
- Names:
  - `"missing configuration preserves legacy default"`
  - `"foundation requires schema2 but never auto-migrates"`
  - `"foundation cannot launch runtime"`
  - `"enforced profile is rejected before qualification"`
  - `"reload cannot downgrade stored gate2 binding"`
- Assertions: legacy behavior preserved, no spawn/probe and no migration side effect.
- Expected red: profile guard absent.
- Symbols: Config/Schema, application wiring and Orchestrator pre-spawn guard.
- Focused: `mix test --no-start test/symphony_elixir/gate2_attempt_config_test.exs`.
- Evidence/commit: dormant integration/documentation.

Package regression, from `elixir/`:

```bash
mix test --no-start \
  test/symphony_elixir/gate2_attempt_types_test.exs \
  test/symphony_elixir/gate2_attempt_resource_ledger_test.exs \
  test/symphony_elixir/gate2_attempt_migration_test.exs \
  test/symphony_elixir/gate2_attempt_compatibility_test.exs \
  test/symphony_elixir/gate2_attempt_boundary_test.exs \
  test/symphony_elixir/gate2_attempt_config_test.exs \
  test/symphony_elixir/attempt_ledger_test.exs \
  test/symphony_elixir/runtime_attempt_identity_test.exs
```

These tests must not start Symphony, call runtime admission/probes or install cleanup-authority stubs.

### K2. Remaining reviewable task boundaries

- **P08:** evidence schema/index; native positive cleanup observations; safe diagnostic envelopes; release ordering/quarantine recovery.
- **P02:** source policy/manifest schema; ext4/loop allocation; aggregate capacity; hidden-reference teardown.
- **P03:** OAuth validation; encrypted record/key custody; credential commit; key rotation; account/recovery isolation.
- **P05:** exact tool catalog; permit/argument/result guards; submit-once crash reconciliation.
- **P04:** bootstrap; broker/UID/profile; nftables/DNS lease; strict startup; transport acknowledgement/retry closure; inference ledger; BP proof.
- **P06:** source capture; Git-object stage; secret/container/media inspection; evidence/reconfirmation; bounded publisher; lost-response reconciliation.
- **P07:** validation binding; replacement review invalidation; human merge/tree proof; restart revalidation.
- **P09:** qualification manifest; capacity selection; exact Codex/native proof; independent BP/ET/obligation disposition.

Each boundary uses the package's exact test files and produces a versioned evidence record before package acceptance.

Required SourceManifest tests include tracked modification/deletion, authorized add, unauthorized new path, executable-mode-only change, combined content/mode change, delete+add rename, `.git`/nested repo, private-domain alias, unknown classification, capture movement and restart-invalidated fence.

Storage tests include actual rounded inode totals, finite block capacity, fallocate failure, loop attachment identity, mount propagation, EBUSY, open-unlinked/WAL/SHM, alternate namespaces and retained backing reference.

Vault tests include nonce/header/ciphertext substitution, wrong host/key, key loss, restart, replacement-pair atomicity, interrupted key rotation and no fallback.

### K2a. Lease, refresh and publication metadata task contracts

These tasks belong to P03/P04/P06 and retain their existing package dependencies.
Every command here is a future implementation command, not authorized by G00.

- [ ] P03: extend `SymphonyElixir.SubscriptionRotationTest` in `T/subscription_rotation_test.exs` with lifetime-threshold, insufficient-fresh-lifetime, materialization-race, verified-drain, immutable-generation and restart-at-each-barrier tests. Expect red because the new owner/record does not exist. Extend SubscriptionManager and native credential-store transaction handling only. Run `mix test --no-start test/symphony_elixir/subscription_registration_test.exs test/symphony_elixir/subscription_rotation_test.exs`. Retain the barrier/rotation crash matrix. Commit boundary: complete registration admission/refresh interlock with synthetic credentials.
- [ ] P04: extend `N/tests/egress.rs` with unavailable-DNS success against a local TLS fixture, no fallback, hostname/SNI preservation, expired cached-connection denial, asynchronous-route expiry, mismatched generation and rollover pool-identity cases. Expect red because no lease resolver/pool guard exists. Modify the exact four downstream lease paths in G/J6 and host `network.rs`. Retain socket-destruction, nftables readback, resolver and request-generation evidence. Commit boundary: complete lease/resolver/pool rollover contract.
- [ ] P04: extend `N/tests/provider_effect_crashes.rs` and the patched upstream transport tests with `gate2 transport never performs tls fallback after possible-send acknowledgement`. Assert no second invocation for stock TLS fallback or ambiguous effects. Expect red while stock fallback remains reachable without the Gate 2 constraint. Modify the selected transport/execution path only. Retain invocation counts and durable request states. Commit boundary: complete no-replay enforcement and regression.
- [ ] P06: extend `SymphonyElixir.SourcePublicationBoundaryTest` in `T/source_publication_boundary_test.exs` with canonical recipe/header/parent/message, host-only substitutions and PR-body contract cases. Extend `T/source_publication_recovery_test.exs` with stable-series Fixer fast-forward, lost response and remote-metadata mismatch cases. Expect red because the metadata records/verifier do not exist. Implement the four additional P06 modules in G, share the current pure PR-body contract, then run `mix test --no-start test/symphony_elixir/source_publication_boundary_test.exs test/symphony_elixir/source_publication_recovery_test.exs`. Retain exact recipe/commit/body fixtures and reconciliation evidence. Commit boundary: complete bounded metadata construction and verification.

P03/P04/P06 regression additionally includes all existing package test paths in E. P09 binds `NETWORK_LEASE_RESOLVER_BINDING`, `IMMUTABLE_GRANT_CREDENTIAL_REFRESH_BARRIER` and `PUBLICATION_METADATA_BINDING` evidence to the exact implementation, configuration and candidate identities. Privileged, patched-Codex and live-provider tests remain separate authorization classes.

### K3. Scanner/capacity characterization

The future characterization command is:

```text
candidate-validator characterize
  --corpus-manifest <pinned corpus>
  --output <secret-free measurements>
```

It cannot publish or produce authoritative PASS.

The corpus includes:

- the exact protected-main tree;
- all four media blobs, especially the 30,446,771-byte MP4;
- representative source candidates and new files;
- many-small-file and large-file distributions;
- nested supported archives and compressed metadata;
- expansion/count attacks;
- unsupported/encrypted/polyglot content;
- synthetic secrets and malformed Git/path/mode inputs.

Mandatory fields:

```text
candidate_validation.limits.candidate_entries
candidate_validation.limits.total_tree_bytes
candidate_validation.limits.individual_blob_bytes
candidate_validation.limits.recursive_container_entries
candidate_validation.limits.recursive_expanded_bytes
```

Additional finite inspector memory/output/metadata bounds are recorded in the qualified profile.

The host capacity owner proposes each value using:

```text
ceil(1.25 × max(measured peak, approved planned-workload peak))
+ largest required atomic inspection unit
```

This margin is a reviewable proposal, not an accepted quota. Retain corpus/build identities, distributions, maxima, headroom calculation and approval reference.

Accepted values enter the separate effective validation-profile/configuration digest, which references the immutable policy digest. They do not rewrite policy 1.0.0. Missing, malformed or unverifiable limits yield UNCERTAIN and publication denial. Exceeding an approved limit yields SIZE_VIOLATION.

Writable/process domains have named owners:

- bytes/inodes: trusted storage owner;
- process/memory/CPU/IO/FDs: native supervisor/cgroups;
- wall time: trusted supervisor;
- attempt concurrency: Symphony admission;
- aggregate reservation/headroom: host capacity owner.

IO rate is not capacity. Missing accepted values deny admission.

### K4. Proof classes and CI

Execution remains separated:

1. Pure/ledger tests, no Codex/provider.
2. Privileged native fixtures, no Codex/provider.
3. Exact patched Codex with synthetic secrets/local mock provider.
4. Real provider compatibility under separate authority.

BP-01..19 require intended-holder positive detection and unauthorized-channel negative controls. "Nothing detected anywhere" is not proof.

Upstream tests must prove:

- no pre-readiness process/network action;
- worker suppression;
- forbidden RPC rejection before dispatch;
- brokered classic/unified exec;
- no local fallback;
- exact method/URL before DNS;
- no proxy/redirect/underlying retry;
- durable acknowledgement before invocation;
- `/models` denial without loss of selected operation.

Existing H-080B CI remains mandatory. New proof uses a qualified disposable Linux host and fails on missing controls. It does not skip into acceptance.

### K5. Complete bearer-channel and evidence-transfer registers

Every bearer channel requires a positive detector control in the intended holder and a negative unauthorized-channel control using a synthetic non-live secret. No live bearer is used without separate authority. Missing observation, known leakage or uncertainty retains quarantine and blocks unsafe reuse. P04 owns enforcement; P08 owns secret-free observation and P09 owns independent applicability review.

- **BP-01** child environment. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-02** /proc/<appserver>/environ. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-03** /proc/<appserver>/mem. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-04** ptrace. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-05** process_vm_readv or equivalent. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-06** systemd credential access. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-07** credential source copies. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-08** credential materialization copies. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-09** inherited FDs. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-10** transferred FDs and SCM_RIGHTS. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-11** app-server RPC. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-12** diagnostics/configuration dumps. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-13** logs/stderr. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-14** crash output/core dumps. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-15** temporary/open-unlinked state. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-16** provider request content. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-17** provider response content. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-18** output staging/source tree. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.
- **BP-19** semantic host-tool arguments/results/logs. Test the exact authorized holder and unauthorized readers/copies; retain bounded detection/denial evidence bound to attempt, executable, profile and resource. Failure follows CLEANUP_UNVERIFIED → QUARANTINED → BLOCK_UNSAFE_REUSE.

P09 must review every transferred claim below. None establishes selected implementation acceptance or new execution authority.

- **ET-001** H-050D, `ACCEPTED_HARDENING_AUTHORITY`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: HOST credential/channel constraint in original Symphony configuration. Transfer: Credential ownership stays host-side; runtime cannot redirect trusted credentialed transport. Does not prove SIWC materialization/nondisclosure/publisher. Non-transfer: SIWC, access-bearer confinement, new GitHub publisher are not tested claims. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-002** H-060A, `ACCEPTED_HARDENING_AUTHORITY`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: Attempt ID/work item/lineage/responsibility checks. Transfer: RuntimeAttempt identity and stale-event scope transfer; filesystem/process/token isolation does not. Non-transfer: No fresh workspace or process containment proof. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-003** H-060B, `ACCEPTED_HARDENING_AUTHORITY`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: RecoveryLedger lifecycle checkpoint. Transfer: Bound startup/suspension reconciliation transfers; no restore of live attempt, credential or new resource. Non-transfer: No Gate2 publication/quarantine resources. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-004** H-060C, `ACCEPTED_HARDENING_AUTHORITY`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: Workspace OwnershipLedger ownership and shutdown recovery. Transfer: Trusted workspace owner/lifecycle transfers; fresh attempt writable instance is not proved. Non-transfer: No RuntimeAttempt binding in ownership record. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-005** H-080B, `ACCEPTED_HARDENING_AUTHORITY`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: Original executable/config/platform evidence. Transfer: Accepted runtime isolation remains in scope for tested Codex 0.159.3; required 0.162.1 proof is separate. Non-transfer: SIWC bearer, selected egress, fresh workspace, publisher. H080B acceptance/design remain intact. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-006** Architecture E/A2, `SCOPED_DESIGN_OR_CHARACTERIZATION`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: Specific test topology. Transfer: Only tested platform/mount/state rationale transfers. Non-transfer: Production completeness, different executable, hidden objects, SIWC. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-007** v5/r4, `HISTORICAL_FIXTURE_NOT_ACCEPTED`, `NOT_ACCEPTED`. Original scope: Historical synthetic output fixture. Transfer: Fixture cases may inform later checks; R4 remains unaccepted. Non-transfer: Production output architecture, generic publication, Gate2 acceptance. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-008** Gate2 synthetic evidence, `SYNTHETIC_FIXTURE`, `DIAGNOSTIC_ONLY`. Original scope: Fixture assumptions and synthetic tests. Transfer: Only synthetic fixture behavior. Non-transfer: Host enforcement, actual provider credential, raw lineage acceptance. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-009** Retained Gate2 trace, `PARTIAL_RUN_LINEAGE`, `DIAGNOSTIC_ONLY`. Original scope: One retained diagnostic trace. Transfer: Troubleshooting context only; lineage partial, acceptance authority no. Non-transfer: Proof completion, Gate2 acceptance, execution authorization. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-010** Official OpenAI SIWC docs, `OFFICIAL_PROVIDER_CONTRACT_ONLY`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: Provider documentation current as 2026-11-02. Transfer: Registration/client/host identity, token claims/lifetimes/rotation/serialization, endpoint and app-server token/restart contract. Does not prove Symphony implementation. Non-transfer: Local persistence, atomicity implementation, nondisclosure, Gate2 execution. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-011** T3Code operations, `OPERATIONAL_ANALOGY_NOT_AUTHORITY`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: T3Code account separation. Transfer: Only separate subscription identities may coexist on a host. Non-transfer: auth.json import, shadow HOME, shared DB/session/config/env do not transfer. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-012** V1 source-control + supplied publisher decision, `NORMATIVE_V1_AUTHORITY_AND_SUPPLIED_GOVERNANCE`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: V1 exact candidate model and user-selected publication boundary. Transfer: CandidateRef/check/review/human merge remain; host publisher owner fixed. Existing SourceControl does not create commit/push/PR. Non-transfer: No publisher implementation or recovery record currently exists. Required new proof: YES for selected production integration; preserve original evidence limits.
- **ET-013** Pinned Unified Roadmap vs supplied Gate2 lock, `REPOSITORY_PROVENANCE_AND_TASK_AUTHORITY`, `TRANSFERS_WITH_BINDING_CONDITION`. Original scope: Roadmap provenance plus current task lock. Transfer: Main records H100 active; supplied lock prohibits H100 execution in this task; preserve both. Non-transfer: No H100/H110/H120B execution authorization from packet. Required new proof: YES for selected production integration; preserve original evidence limits.

## L. Migration, rollout and compatibility

The new binary supports whole v1 ledgers for legacy projects and whole v2 ledgers after explicit migration. It never mixes record versions or migrates during startup.

P01 local acceptance does not authorize deployment migration. Offline maintenance requires its own host authority.

Gate 2 remains dormant through P01 and P08. Later packages can be installed behind the incomplete-profile guard. Activation requires accepted G00, policy/implementation identities, numerical profiles and exact qualification.

Rollback cannot erase Gate 2 bindings, restore old ledger files or reinterpret v2 records as legacy. Unsupported hosts/configurations block admission.

No partially configured deployment may fall back to shared HOME, personal auth, broad egress, legacy release, unvalidated publication or legacy completion acceptance.

Accepted H-050D/H-060/H-080B behavior remains effective.

## M. Risk register

1. **Migration durability:** directory-sync/rename uncertainty requires maintenance recovery, never automatic selection.
2. **Optional upstream services:** strict startup and dispatch gates must remain sticky across session/config construction.
3. **Broker semantics:** output/event/cancellation parity needs exact interface tests; stock LocalProcess is not the boundary.
4. **Storage observation:** unknown namespace/FD/device references retain quarantine.
5. **Host provisioning:** unsupported backing storage, kernel or LSM capability blocks Gate 2.
6. **Vault key loss:** exceptional reauthentication is required; no decryption bypass or account fallback.
7. **Vault forensic limits:** root/key-file custody does not claim resistance to malicious root or offline physical recovery.
8. **Source admission availability:** legitimate unanticipated new paths require a new host decision/grant.
9. **Binary parser completeness:** unsupported or ambiguous formats yield UNCERTAIN; no media exemption.
10. **DNS churn:** stale-address revocation can interrupt inference; ambiguity blocks replay.
11. **Credential refresh uncertainty:** lost rotation result may require reauthentication.
12. **Evidence secrecy:** raw errors/snippets/path content cannot leak into ordinary evidence.
13. **Governance CI:** a governance-only PR still triggers Codex and needs separate execution authority.

These are implementation/qualification risks with explicit fail-closed behavior. No remaining architecture or authority contradiction was found.

## N. Recommended first implementation slice

The recommended first slice is **P01's dormant foundation**, including the exact migration contract and tests.

It is coherent without P08 because it cannot establish resource cleanliness, allocate resources, launch Codex or release Gate 2 authority.

Its acceptance boundary is:

```text
Legacy semantics remain valid.
Each ledger contains one record version.
Migration is explicit, whole-ledger and crash-recoverable.
Gate 2 binding survives every writer/history/rearm path.
Legacy APIs cannot release Gate 2 authority.
Foundation cannot produce active grants, usable permits or clean evidence.
Restart restores facts and blocks, never capability.
```

P08 remains the next mandatory slice.

Before P01 authorization, G00 must be persisted/accepted and applicability explicitly rebound. A future authorization must distinguish local edits, focused non-Codex tests, commits, deployment migration, push, PR creation, Codex CI and provider execution.

No such authorization is supplied here.

## O. Authorization statement

The internal contradiction scan checked the schema model, error vocabulary, authority-bearing record schemas, OS/storage/crypto selections, protected-tree binary disposition and source-audited patch list.

This is the complete canonical implementation plan approved by the Master Gate at planning level. It does not claim that implementation or proof has passed. The following locks apply to Gate 2 implementation, not to the separately authorized G00 documentation branch/commit/push/PR.

The retained trace remains diagnostic only. r4 remains unaccepted. Local bearer nondisclosure remains unverified. AUTH-07 remains suspended and unconsumed.

```ini
GATE_2_STATUS=INCOMPLETE

IMPLEMENTATION_PLAN_APPROVED_BY_MASTER_GATE=YES
IMPLEMENTATION_AUTHORIZED=NO
P01_IMPLEMENTATION_AUTHORIZED=NO
P06_IMPLEMENTATION_AUTHORIZED=NO

LOCAL_IMPLEMENTATION_AUTHORIZED=NO
LOCAL_FOCUSED_NON_CODEX_TESTS_AUTHORIZED=NO
LOCAL_FOCUSED_P01_TESTS_AUTHORIZED=NO

COMMIT_AUTHORIZED=NO
PUSH_AUTHORIZED=NO
OPEN_PR_AUTHORIZED=NO
PUSH_FOR_PR_CI_AUTHORIZED=NO

CODEX_EXECUTION_AUTHORIZED=NO
LOCAL_CODEX_EXECUTION_AUTHORIZED=NO
PROVIDER_EXECUTION_AUTHORIZED=NO

H100_EXECUTION_AUTHORIZED=NO

AUTH_07=SUSPENDED_UNCONSUMED
AUTH_07_CONSUMED=NO
```

The G00-only documentation authority is distinct:

```ini
G00_DOCUMENTATION_MATERIALIZATION_AUTHORIZED=YES
CREATE_WORKTREE_AUTHORIZED=YES
CREATE_GOVERNANCE_BRANCH_AUTHORIZED=YES
EDIT_GOVERNANCE_AND_PLAN_DOCS_AUTHORIZED=YES
LOCAL_DOCUMENT_VALIDATION_AUTHORIZED=YES
LOCAL_NON_CODEX_GOVERNANCE_TESTS_AUTHORIZED=YES
COMMIT_G00_DOCS_AUTHORIZED=YES
PUSH_G00_DOCS_BRANCH_AUTHORIZED=YES
OPEN_G00_PR_AUTHORIZED=YES
G00_PR_REQUIRED_CI_CODEX_EXECUTION_AUTHORIZED=YES
G00_PR_REQUIRED_CI_CODEX_SCOPE=REQUIRED_GITHUB_ACTIONS_FOR_THIS_EXACT_G00_GOVERNANCE_DOCS_PR_ONLY
MERGE_AUTHORIZED=NO
```

### Materialization self-review

- Spec coverage: all A–O sections, 26 primary obligations, 115 inventory entries, nine packages, 14 frozen lifecycles, 19 bearer channels and 13 evidence-transfer claims are accounted for. The accepted resolver, credential barrier and metadata contracts are integrated into their owning packages.
- Step scan: P01 tasks identify exact test names, red results, minimum symbols, commands, evidence and commit boundaries. All implementation checkboxes remain unchecked. No task execution is authorized by this document.
- Type consistency: the stable P01 error union includes `:attempt_resource_verification_required`; ledger versions are whole-file versions; credential generation is immutable; network generation is independently renewable; all authority-bearing records resolve through their owning stores.
- Review focus: exact baseline/packet, G00 successor rebind, dormant release, ledger migration, holder-only credentials, resolver/kernel/pool agreement, effect ambiguity, scanner semantics and host-only publication metadata.
- Proportion: retain the approved nine packages and exact contracts; do not split or redesign them during materialization. Frozen-record crosswalks supplement the immutable packet rather than duplicate its entire payload.

```ini
IMPLEMENTATION_PLAN_VERDICT=READY_FOR_GOVERNANCE_REVIEW
```
