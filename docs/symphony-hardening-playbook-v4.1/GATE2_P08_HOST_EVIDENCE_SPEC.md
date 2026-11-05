# P08 Host Evidence, Cleanup and Quarantine — Technical Specification v0.7

**PROPOSED — NOT ACCEPTED**

```ini
STATUS=PROPOSED_FOR_INDEPENDENT_MASTER_GATE_REVIEW
SPEC_VERSION=0.7
CONTRACT_REVISION=P08-SPEC-0.7
P08_SPEC_ACCEPTED=NO
P08_IMPLEMENTATION_AUTHORIZED=NO
P08_DOCS_PR_AUTHORIZED=NO
P08_CI_AUTHORIZED=NO
P08_PRIVILEGED_EXECUTION_AUTHORIZED=NO
AUTH_07=SUSPENDED_UNCONSUMED
GATE2_ACTIVATION_AUTHORIZED=NO
```

This specification states proposed requirements. MUST and MUST NOT describe the contract to be reviewed, not present execution permission. This document is self-contained. Earlier proposals are historical evidence only. The companion implementation plan may select implementation steps but cannot change these contracts.

## 1. Governance, verified baseline and authority

### 1.1 Exact baseline

```ini
REPOSITORY=JCSchoeman96/symphony
MAIN_SHA=30fc30ec27fbadd7277c470a6d6cdb52ced59a4e
MAIN_TREE=dc58f0babebe8a28b3de492eb430a84398abc580
MERGE_PARENT_1=0c53c732bbf68641482741c98afb25e073721ad9
MERGE_PARENT_2=a3fb88d9944caae74c7f24b23a1222f0bc9f3c47
P01_PR=62
P01_HEAD=a3fb88d9944caae74c7f24b23a1222f0bc9f3c47
P01_POSTMERGE_RUN=41822564643
P01_POSTMERGE_ATTEMPT=1
P01_ACCEPTANCE=HUMAN_ACCEPTED
REQUIRED_CHECKS=make-all,validate-pr-description
REQUIRED_CHECK_APP_ID=15368
```

Protected main, tree, ordered parents and required-check identities were reverified read-only before creating this draft. P01 CI is existing evidence, not a run performed by this task. A later implementer MUST reverify the exact baseline and stop on movement.

### 1.2 Governing source register

References below identify the accepted tree above. Local links are navigation, not permission to substitute later contents.

| Code | Governing source | Git blob |
|---|---|---|
| G1 | [Master roadmap](V4_1_MASTER_ROADMAP.md) | `4b0528bdc0647d889b42ebc478081d5b873898fe` |
| G2 | [Unified roadmap](../SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md) | `5ef99584283850482df822e8935428477353797c` |
| G3 | [Status ledger](HARDENING_STATUS_LEDGER.md) | `c500f7bdc4ed1086cde04eed0fd791f147075dbe` |
| G4 | [Canonical Gate 2 plan](../superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md), P08, OB-020/025, LC-13/14 and migration | `bdb2840e5ea4ca8c8912d6cada3287078bbb3c72` |
| G5 | [Herdr qualification refinement](GATE2_HERDR_QUALIFICATION_REFINEMENT_2026-11-03.md), Q01/Q02/Q04/Q05 | `1f33baa3a940b7c7731e677303b8987d43366462` |
| G6 | [Elixir instructions](../../elixir/AGENTS.md) | `d10332b7cbb6b902d82d6a08d876307514190bc1` |
| G7 | [Inventory packet](GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json) | `6cf92dbad8507d4e6c7553392b163fcac02b897d` |
| G8 | [Scanner addendum](GATE2_SCANNER_GOVERNANCE_ADDENDUM_2026-11-03.md) | `1371606b208da8df4c8bcc69387bb86153fec7a2` |
| G9 | [Scanner policy](GATE2_V1_CANDIDATE_VALIDATION_1.0.0.json) | `72632e9f2d92d176668286016f2ed3dfda500d85` |

Additional verified records are Herdr JSON `ebe3c1acca960ccb6a1f71bed02c9fee5804df16`, freeze acceptance `f0be29391fd584f665da816079536c0bbb33bcd2`, freeze reconciliation `437175de2dcc491185a3775b276608fa9a16405a`, inventory projection `1d4bfac04d7533049f6a07b0b6604680f9d9ded0`, scanner projection `d754155b5a1391a885d5c6ade6bd5066a969ac10`, programme projection `90b06bb63ba1950c916a0571ab0ce6fb297a5a98` and Herdr archive `af7a3af7907658d9deda3a72bf666ad0016adb95`.

Authority order is G1, G2, applicable explicit decisions/G3, G4 and supplemental G5/G6. Frozen inventory and scanner records retain their own scope. Plane projections do not issue implementation authority.

### 1.3 Review provenance and supersession

SGOV-2 is `079ea0ea-dc3f-4a23-ac01-0a3e75e8c03b` in project `f7317505-bc78-42ae-a902-1e3f0346bcff`. The charter, programme handoff and review `514f0a3a-7239-4651-8aa1-775ca6bec169` were read. Current user authority permits only these two local documentation artifacts. It supersedes the review's earlier no-local-writing restriction, without granting publication or execution.

Complete earlier assistant proposals were retrieved from <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/05a39e7c-0581-4b63-a9a2-efd6135be052>. The R4 assistant-message export is 53,479 UTF-8 bytes with SHA-256 `653415af6d4077f29ceff8192716a9f0d3d78d4fafc82ea6d369e3c7b96eaa4b`. The review identifies a different uploaded `R4 Plan.txt`, 52,431 bytes, SHA-256 `0eb8a7a3b8a72f5e0efd71c1bbbefe040f1cdf2cd5bfc47c20240e8facef90dc`. The attachment was not available through the attachment listing. These exports MUST NOT be represented as byte-identical. Resolving that historical export identity remains an evidence prerequisite for exact historical reconciliation; this specification does not depend on either export as normative authority.

This draft replaces all R1–R4 proposed type/operation definitions. In particular it removes the invented GrantRef policy field, 128-byte identifier restriction, generation-selection cycle, implicit descriptor inheritance, generic opcode bodies and conflated disclosure states. No earlier proposal was accepted.

### 1.3a Historical v0.2 review corrections and original-file identity

Review `27a6c32c-478d-49d5-9e10-1b5ae103c382` requested four contract corrections and held exact file identity. This revision adds explicit begin/retain/release resolution variants and root reservation semantics, a disjoint legitimate no-capture diagnostic variant, read-only T01/T18 and pre-CI placement of preservation/claim tests. Generation proposal/journal ordering, 15 opcodes, 49 requirement IDs and six golden fixtures remain unchanged.

Before editing, original local v0.1 Markdown bytes independently reproduced SHA-256 `6a2349519d3581c5ef032d8e60594e777a372402a0366e2452ef8646b42d1135` for the specification and `1b6b7f9efa5ba43e90fd2b14b1a68fd45ae367a2c853a9376d80eff0576770d5` for the plan. Review-uploaded text copies had different digests. No cause of conversion is asserted. Review/acceptance MUST hash the raw downloaded `.md` file, not rendered Markdown, copied chat or text export. The handoff supplies exact new sizes/hashes; the plan binds this revision's exact specification bytes. External independent verification of downloaded originals remains required before acceptance. This document does not contain its own digest.

### 1.3b Targeted v0.3 corrections

Review `4545e318-066a-4792-b9ed-0172136d26f3` requested an existing-epoch provisioning handoff, a terminal quarantine-evidence path, a closed initial I restriction and trusted diagnostic-policy materialization. Sections 5.2b, 6.16–6.18 and 7.1b define those contracts. The 49 requirements, 18 tasks, 15 opcodes and six resource-set/snapshot fixtures remain. No native execution or environment qualification is asserted.

Before this revision, the local original v0.2 specification was 154,241 bytes, SHA-256 `0fcd4ebd54710a81431d84d2bfcadd072ae8afef06fa9042835894062e2d75ba`; the plan was 54,576 bytes, SHA-256 `cb5d267b8de991fa393b8348756aed0571a4ec3f86989c32dd12188e49cafada`. Those bytes differ from the review's text exports. Exact acceptance requires independent hashing of the original `.md` downloads supplied with this revision. A local hash does not establish external receipt identity.

### 1.4 Scope and trusted owners

Trusted components are the installed root helper, installed native client, root installation/maintenance authority, captured `AttemptBoundary`, trusted Orchestrator and existing ledger owners. The host UID and BEAM code are trusted. Unix credentials authenticate that principal and executable, not an Erlang PID. BEAM caller guards authenticate internal owner processes. Runtime code MUST NOT share this principal; P04 must qualify that separation.

Post-bootstrap client/helper seccomp must deny execve, execveat, fork, vfork, clone and clone3; the client installs it only after its fixed child bootstrap. The helper never creates another process. Limits are enforced with qualified rlimits and checked allocations. Required observation syscalls are restricted by the reviewed fixed implementation; no runtime request selects a syscall policy.

The helper observes runtime resources and mutates only its evidence/control stores. It MUST NOT signal or spawn runtime processes, delete runtime objects, mount/unmount, change networking, issue grants, invoke providers or execute arbitrary commands. A test driver may perform separately authorized fixture effects; those are not helper capabilities.

P08 leaves `gate2_foundation` dormant and `gate2_enforced` incomplete. No settlement restores dispatch, automatic retry, lineage rearm, credential authority, publication, Done or upstream cancellation/revocation. P05 remains unauthorized. SGOV-13 dispatch exclusion remains unproven; SGOV-14 materialization stays separate. AUTH_07 remains suspended and unconsumed.

## 2. Existing P01 compatibility and source contracts

### 2.1 Accepted stored types

The accepted source is `elixir/lib/symphony_elixir/agent_runtime/`. The exact field sets are:

```text
RuntimeAttempt.Identity = runtime_attempt_id, work_item_id, lineage_generation,
                          responsibility, runtime_profile
RecoveryGeneration = schema_version, project_namespace, host_id, boot_id, sequence, nonce
AttemptGrant.ref = grant_id, project_namespace, runtime_identity, fence_epoch, grant_sha256
AttemptResource = schema_version, resource_id, project_namespace, grant_id,
  runtime_identity, class, state, revision, stable_locator,
  allocation_identity_sha256, capacity_profile_sha256, owner_host_id,
  creation_generation, reconciliation_generation, last_evidence_ref, quarantine
CleanupEvidenceRef = schema_version, evidence_id, evidence_sha256, project_namespace,
  grant_id, runtime_identity, fence_epoch, resource_set_sha256,
  verification_generation, verifier_implementation_sha256
QuarantineDisposition = state, reason, evidence_ref, generation, resolution_ref
```

Stored struct shape and schema version 1 remain unchanged for these types. AttemptLedger remains its accepted schema 2 for Gate 2 bindings. No startup migration or mixed-version ledger is permitted.

`AttemptGrant.reference/1` hashes a deterministic Erlang tuple, not JSON. In order it contains schema_version, grant_id, project_namespace, tracker_identity_sha256, identity tuple, generation tuple, route_fingerprint, subscription_registration_id, credential_generation, workspace_resource_id, source_admission_policy_sha256, process_policy_sha256, network_policy_sha256, tool_policy_sha256, capacity_profile_sha256, allowed_operations and fence_epoch. Identity tuple order is runtime_attempt_id, work_item_id, lineage_generation, responsibility, runtime_profile. Generation tuple order matches its field list above. The fingerprint is SHA-256 of `:erlang.term_to_binary(tuple, [:deterministic])`, lowercase hexadecimal. P08 preserves it; Rust treats it as an authenticated opaque commitment and MUST NOT recompute it from the reference.

Every old resource/attempt row is first validated against the accepted source rules before projection. RuntimeAttempt.Identity.valid?/1 alone permits values beyond strict Gate 2 constructors; P08 must use the exact accepted binding validation, not that looser predicate as a substitute.

A shape-valid reference is not a grant or cleanup provenance. Namespace, runtime identity, grant digest, fence epoch and current generation MUST agree with the existing binding and root registration.

Evidence matching MUST compare all runtime identity bytes exactly, even though RuntimeAttempt.Identity.same?/2 can normalize responsibility for other legacy callers. P08 does not change that legacy function or use its normalization as fingerprint equivalence.

P01 generation constructors accept broader IDs than fresh native generations. Preserve historical printable-ASCII values without lowercasing boot IDs/nonces. Fresh root generations use the fixed kernel boot UUID and 32 lowercase hex nonce. Unencodable historical values block P08 use without invalidating or rewriting the P01 record.

### 2.2 Wire conversion

P01 identifiers are binaries up to 256 bytes. The wire subset is printable ASCII, 1–256 bytes, with at least one non-space character. No trimming, case conversion, Unicode normalization, truncation or hash substitution is permitted. Non-ASCII or out-of-range P01 values return `unencodable_p01_value`. P01 integers beyond U64 are similarly retained but blocked for P08 evidence use.

Stored `last_evidence_ref`, quarantine `evidence_ref` and `resolution_ref` remain string-or-nil. Wire links use `EvidenceLink`. Nil maps to null; a historical string maps to prior with the exact bytes. Unknown historical IDs remain opaque and confer no provenance. Reverse mapping of prior returns the exact string.

Current links are allowed only in predicted post-snapshot slots declared in `EvidenceObject.self_bindings`. A verifier first checks the actual stored string equals the resolved current object ID, then normalizes that slot for hashing. Current links without that context reject. Standalone quarantine records allow prior/null only. A map found in a stored string field is corrupt, not a new schema. Neither malformed historical evidence nor an unresolvable prior ID may authorize release.

### 2.3 Existing interfaces and deliberate refusals

`AttemptBoundary.gate2_release_result/4`, `cleanup_resources_result/2`, `resolve_cleanup_reference/2` and `matching_resources/2` currently enforce the unimplemented-verifier boundary. P08 may replace that refusal only with the full qualified protocol below. Public `release_gate2_authority_fence/4` remains boundary-routed. `reserve_sync/2` and `transition_sync/4` remain owner-guarded.

The accepted `AttemptBoundary.init/1` injects startup recovery and removes a supplied generation before starting R. R currently opens, rejects pending recovery, selects a generation and calls `prepare_table`. That path cannot be reused for P08 staged inspection. Section 4 defines a separate path; compatibility startup retains its existing pending-marker rejection.

AttemptLedger generic writers and current/history records MUST retain Gate 2 bindings. Release receipt persistence is a proposed addition, not a claim that P01 already accepts released Gate 2 receipts.

## 3. Native invocation, descriptors and root custody

### 3.1 Fixed installation

```text
/usr/local/lib/symphony/gate2/p08-v2/evidence_client
/usr/local/lib/symphony/gate2/p08-v2/attempt_boundary
/etc/symphony/gate2/p08-v2/installation.json
/etc/sudoers.d/symphony-p08
/var/lib/symphony/gate2/control/<SHA256(namespace-bytes)>/owner.lock
/var/lib/symphony/gate2/objects/
```

Root owns all installation ancestors and policy. Executables are regular root-owned mode 0755; manifests/policy are root-owned mode 0444 or stricter. Control/object directories are mode 0700 and lock files mode 0600. Root registration pins executable digests/device/inode, client host UID/GID, host identity, lock device/inode, ledger registration, qualification and numerical profiles. No runtime-writable manifest, request path or environment value selects authority.

Selected sudo qualification candidate is 1.9.17p2. Its real package/plugins/policy digests must be approved. The policy template is:

```sudoers
Cmnd_Alias SYMPHONY_P08 = sha256:<qualified-helper-sha256> /usr/local/lib/symphony/gate2/p08-v2/attempt_boundary ""
Defaults!SYMPHONY_P08 env_reset, !use_pty, !log_input, !log_output, !intercept, fdexec=always
Defaults!SYMPHONY_P08 secure_path="/usr/sbin:/usr/bin:/sbin:/bin"
symphony-host ALL=(root:root) NOPASSWD:NOSETENV:NOLOG_INPUT:NOLOG_OUTPUT: SYMPHONY_P08
```

The digest placeholder is an installation input, never a deployable policy. Qualification must establish effective empty-argument restriction, disabled global I/O logging/PTY interception and preserved socket standard descriptors. The client uses fixed `/usr/bin/sudo -n -- <fixed-helper>`, no shell, no helper arguments, no `-E` or caller-selected sudo options. NOEXEC is not selected; reviewed native syscall restrictions prohibit post-bootstrap exec/fork. Helper clears environment and never trusts SUDO_USER, HOME, PATH or locale. Unsupported policy closes the gate.

### 3.2 Descriptor table

| Stage | Owned descriptors | Required action |
|---|---|---|
| BEAM | Client port pipes | No privileged socket descriptor exposed to runtime |
| Client bootstrap | BEAM pipes and AF_UNIX SOCK_STREAM socketpair C/H | Create with SOCK_CLOEXEC; enable SO_PASSCRED and SO_PASSPIDFD on both ends before child creation |
| Child setup | H plus temporary inherited descriptors | `clone3(CLONE_PIDFD)` gives parent child pidfd; close C; duplicate H to fd 0/1; close all >2; fd 2 is bounded administrative channel |
| Client parent | C, BEAM pipes, child pidfd | Close H; CLOEXEC on C/pidfds; no later fork/exec; non-dumpable and reviewed syscall restrictions |
| Sudo | H at fd 0/1 | No proxy/PTY; policy-qualified preservation across fixed exec |
| Root helper | H at fd 0/1 | Verify both refer to expected same socket; reject unexpected descriptors; authenticate before mutation |
| Authenticated helper | H, client pidfd, root lock, explicit observation/store FDs | No fork, exec or descriptor transfer; bounded FD inventory |
| Exit | Explicit descriptors | Close mutation/observation FDs first, lock last; client reaps its owned child |

SO_PEERCRED on a socketpair describes creation credentials. It is not root-server authentication. Helper obtains original creator handle with SO_PEERPIDFD and independently verifies live registered UID/GID, executable digest/device/inode, host boot, cgroup and namespaces. It rechecks liveness before every root commit. PID/start time only corroborate identity. pidfd pins an incarnation but does not prohibit exec; a positive stable-executable verdict additionally requires qualified owner confinement preventing exec/migration during the observation window, or the controlled fixture actor equivalent. Repeated /proc reads alone do not establish that guard.

Every payload fragment is received with `recvmsg(MSG_CMSG_CLOEXEC)` and validated kernel SCM_CREDENTIALS and SCM_PIDFD. Reject SCM_RIGHTS, unknown/duplicate ancillary data, MSG_CTRUNC/MSG_TRUNC, credential mismatch and unexpected sender incarnation; close every received FD on every error. Client authenticates root response using kernel sender pidfd, UID zero and exact helper executable. It cannot use socketpair creation credentials as root proof. After committing durable closure, helper waits only for final close acknowledgement or the close deadline; acknowledgement does not guard the durable QUIESCENT transition. After close_session response the only accepted frame is transport `{protocol:"G2-P08-SESSION-2",contract_revision:"P08-SPEC-0.7",session_id:Nonce,close_ack_sha256:Digest}`, bound to the response final head, with the same framing/credentials. This is a transport acknowledgement, not a sixteenth application opcode. It must arrive within the candidate 1-second close deadline; otherwise helper exits without further mutation and caller treats transport/lock completion as unconfirmed until authenticated reread and actual lock acquisition. A committed QUIESCENT head remains committed under section 6.16a. It counts against byte/frame budgets. Socket bytes, ancillary custody and sender continuity require exact-kernel qualification.

Client death, unexpected exec or inherited endpoint use invalidates further commits in that invocation. A successfully closed administrative handoff can be consumed by a later independently authenticated client of the same still-live boundary only under section 6.18; no pidfd or old session is reused. PID reuse cannot replace the original pidfd. Unsupported kernel identity evidence yields `unsupported_host`, never a positive verdict. Client reaps the original owned sudo child with waitid(P_PIDFD) where supported; that child handle is distinct from the helper sender handle if sudo retains a monitor process. Child reaping cannot certify helper exit. Resource pidfds are invocation-local; a later invocation must obtain fresh identity under trusted allocation/confinement history.

### 3.3 Root lock lifecycle

| State/transition | Owner/guard | Side effect and durable identity | Failure/restart/meaning |
|---|---|---|---|
| NEW → AUTHENTICATED | Helper; live qualified client | Session nonce, pinned installation | Any mismatch rejects before mutation |
| AUTHENTICATED → LOCKED | Helper; fixed non-replaceable lock inode | `flock(LOCK_EX|LOCK_NB)` on sole open description | Busy returns bounded denial; never steal/unlink |
| LOCKED → ACTIVE | Same helper and client, exact root head | Bounded protocol session | Timeout/client loss blocks; root lock remains until actual close/death |
| ACTIVE → QUIESCENT | All final metadata and QUIESCENT head synchronized; no acknowledgement guard | Durable closure commitment; no further application writes | Await bounded transport acknowledgement, then close mutation FDs and lock last; lost acknowledgement does not undo the head |
| ACTIVE → INTERRUPTED | Crash, partial frame or uncertainty before durable closure | Existing durable head remains authoritative | Next owner recovers closed; old events/evidence stale. A later transport failure cannot relabel an already committed QUIESCENT head |
| Any → STUCK_BLOCKED | Unconfirmed surviving helper | Existing kernel lock ownership | Separate authorized maintenance/reset; elapsed time never proves termination |

All trusted root administrative writers honor this advisory lock. No asynchronous mutation worker or inherited lock FD may outlive the helper. Root control is an immutable chain plus synchronized head pointer. Write/sync record, publish without replacement, sync directory, replace head, sync its directory. Only head rename has one-filesystem atomicity. E/I/R/A never share an atomic transaction. Unreachable objects cannot become authority by having a high sequence.

## 4. Root generation, acyclic recovery and staged R startup

### 4.1 Selected 15-operation protocol

Add `propose_generation` to the 14 corrected R4 names. `begin_recovery` now binds an already selected proposal; it never chooses a new target. The ordering is:

1. Boundary creates fresh owner epoch and starts closed. Helper authenticates and obtains root lock.
2. Staged R opens existing ledger read-only and inspects metadata/rows. No generation mutation occurs.
3. `propose_generation` commits a root proposal containing exact selected target Generation and source commitments, then returns its receipt.
4. Boundary calculates target metadata/rows using that exact target. It persists and synchronizes the complete immutable host journal and its directory.
5. `begin_recovery` binds proposal digest, journal digest and exact target commitments in durable root plan.
6. R validates root plan and same source, then applies only its bound transformation.
7. R synchronizes and rereads target rows/metadata with pending marker absent.
8. I synchronizes recovery mirror. `ack_recovery` records root generation commitment, gate CLOSED.
9. Boundary rereads E/I/R and activates only a closed generation-consistent state. A/history remain protected.

The host journal cannot precede generation selection. Resource mutation cannot precede root plan binding. The proposal does not itself advance current generation.

### 4.2 Proposal lifecycle

Root owner selects sequence greater than committed root generation, validated R sequence, and every previously reserved sequence. Nonce is fresh. Proposal identity includes reservation ID, target, source commitments, owner epoch, session, boot and monotonic expiry at or before session deadline. Root persists high-water reservation before returning success. Expiry bounds use, not lock lifetime.

`NONE → PROPOSED → PLAN_BOUND → R_APPLIED → MIRRORED → GENERATION_COMMITTED_CLOSED` is the normal lifecycle. `PROPOSED → ABANDONED` is allowed only when no plan was bound and source R is unchanged. Abandoned sequence is burned. `PLAN_BOUND` cannot be discarded to allocate another proposal over partially transformed rows.

A new session cannot bind an unbound old proposal. It records abandonment under lock, verifies unchanged source and makes a fresh proposal. Orphan journals are historical. A pending bound plan may be inspected/re-attested for repair under a new owner using `propose_generation` action `resume_bound`; it does not allocate a different target. After repair/commit, that new owner must establish another fresh closed generation before activation.

If high-water head persistence is uncertain, root validates its chain and scans bounded root-owned proposal objects for conservatively burned sequences. Unreachable proposals can raise only the burn bound, never current authority. Unexplained head rollback, overflow, conflicting target or exhausted scan capacity blocks maintenance. No sequence is reused after a successful proposal receipt. The proposal expiry and session deadline share the host CLOCK_MONOTONIC domain. A new boot/session invalidates unbound proposals regardless of the stored deadline. Expiry cannot abandon an already bound plan or release a surviving helper lock.

### 4.3 Staged APIs

Proposed ResourceLedger APIs, callable only by captured registered boundary and owner epoch:

```text
start_link_staged(opts)
inspect_staged(server, owner_epoch)
apply_recovery_plan_sync(server, journal, root_plan_receipt)
activate_staged_sync(server, root_generation_receipt, mirror_receipt)
close_staged(server, owner_epoch)
```

`start_link_staged` captures caller PID internally, monitors it and takes the existing path lock. It does not call ordinary init's choose_startup_generation, prepare_table, ensure_metadata or reconcile_generation. Only staged calls are accepted before activation; normal reads/writes/reservations/releases deny.

Staged inspection requires preexisting registered parent directories and MUST NOT invoke the ordinary open_table directory-creation path. Use explicit DETS `access: :read`, `repair:false`, `auto_save: :infinity`; reject an already open table/user. Hold path lock across read-only close and write reopen. Validate original file device/inode, size/change indicators and full semantic source commitments before close and after reopen. Reject symlinks, replacement, changed metadata/rows or another opener. A clean file may reopen for write only after root-plan receipt. A missing file requires root registration explicitly authorizing fresh-ledger creation with no conflicting A/I/E history; never infer empty from failure.

DETS `needs_repair`, unreadable/free-list corruption, close error or write-reopen failure becomes MAINTENANCE_REQUIRED. No automatic repair, force-open or backup restoration. Partial-row repair is available only if nonrepairing open and complete validation succeed. This is not a promise that an arbitrary BEAM crash leaves DETS inspectable.

Existing P01-compatible startup remains unchanged for unenrolled ledgers and rejects pending markers as before. Enrolled ordinary startup returns `staged_startup_required` before write-open. Enrollment is fixed root configuration, not workflow/runtime preference. Missing enrolled installation/store cannot cause compatibility fallback.

### 4.4 Host journal and exact transformation

Journal format is uncompressed deterministic Erlang external term, decoded only from trusted private storage after digest verification with safe term decoding and exact known structs/keys. No function, PID, port, reference, newly created atom or compressed external term is accepted. Rust never deserializes it. Root binds the raw SHA-256 plus canonical row commitments.

Exact journal tuple:

```text
{:p08_recovery_journal, 1, reservation_sha256, ledger_registration_sha256,
 source_metadata_or_nil, target_metadata,
 [{resource_id, source_AttemptResource_or_nil, target_AttemptResource}],
 source_pending_boolean, owner_epoch}
```

Metadata keys are exactly schema_version=1, project_namespace, host_id, current_generation. Sorted rows contain complete original structs, including exact locator bytes. Journal is private host metadata, never exported as ordinary evidence. Candidate limit is 1 MiB. Its publication uses write/sync, no-replace rename and directory sync.

For each existing row set state quarantined, revision old+1 with checked overflow, reconciliation_generation target. A clear quarantine becomes quarantined/stale_generation with nil refs and target generation. A non-clear quarantine is preserved exactly, including historical generation and string refs. Creation generation and allocation identity do not change. Row commitments hash canonical `StoredResourceProjection`, which hashes locator bytes and preserves every other field. Source null is allowed only for explicitly authorized empty creation.

Apply pending=true and sync; write exact target rows; write target metadata and sync; delete pending and sync; reread all rows and metadata. Exact repair accepts each row only if equal to its journal before or after image and metadata only if source or target. Unknown keys/third values block. Write target images idempotently without another revision increment.

An old P01 pending=true without root-bound journal is MAINTENANCE_REQUIRED. A malformed marker is corrupt. Neither can be bypassed by staged authorization. New owner repair grants no execution and must be followed by another fresh generation before closed activation.

### 4.5 Recovery crash matrix

All cases deny admission. Recovery owner is a new captured boundary under authenticated root lock; E head/chain/proposal/plan, host journal, full R and I are authoritative rereads. A is also checked for retained obligations.

| Boundary | Possible persisted result | Allowed recovery and terminal meaning |
|---|---|---|
| Before proposal persistence | Old E/R/I | Fresh proposal after source reread |
| Proposal record/head sync uncertain | Old/new head; orphan reservation possible | Validate chain, conservatively burn sequence; blocked if uncertain |
| Proposal durable before receipt | PROPOSED; R unchanged | New session abandons, burns, reproposes; no target inference |
| Before journal creation | PROPOSED only | Abandon unchanged-source proposal |
| Journal written before sync | Missing/partial/full file | No begin_recovery; incomplete file not authority |
| Journal file sync before directory sync | File may disappear on reset | No binding until verified durable publication |
| Journal durable, root plan absent | Orphan complete journal | Never apply R; abandon proposal on new session |
| Root plan publication/head uncertain | PROPOSED/PLAN_BOUND | R cannot write from uncertain receipt; root reread first |
| Root plan durable, R unchanged | PLAN_BOUND and source R | Exact apply or valid repair after qualified open |
| Pending write/sync uncertain | Marker absent/true, rows source | Only exact root-bound plan can proceed |
| Partial target rows | Mixture of before/after; metadata source/target | Exact target repair if nonrepairing open succeeds; otherwise maintenance |
| Target metadata, pending remains | Target rows/metadata; pending true | Verify exact target then delete/sync marker |
| Pending deletion/sync uncertain | Marker true/absent | Verify target and repeat exact deletion, never new transform |
| R complete, I mirror incomplete | Target R, pending root plan | Repair exact I mirror, no admission |
| R/I complete, root commit uncertain | Old current/new current with same plan | Reread E; root commit only exact bound target |
| Root committed, I missing after reset | E current, R target, I unavailable/old | Block; repair matching mirror if authoritative data intact, else maintenance |
| Root committed before activation | Consistent facts, no active boundary | New owner starts closed and advances fresh generation |
| H1 alive, H2 restart | H1 holds lock | H2 denies; no R startup mutation or lock stealing |
| Repeated restart during bound repair | Same immutable before/after images | At most one increment per plan; fresh generation only after exact repair |
| Conflicting proposal/journal/digest | Stores disagree | Quarantine/maintenance; never choose newest-looking file |

## 5. Canonical schema and evidence identity

All schemas below are closed. Field lists are exhaustive. `?T` means T or explicit null; `[T]` is a bounded array. No omission is permitted. Enum spellings are literal. Schema notation is normative; it is not a generic map allowance.

### 5.1 Scalar encoding and enums

`U64` is 0..18446744073709551615; `PositiveU64` excludes zero. JSON numbers have plain unsigned decimal syntax without leading zeroes. No floats/sign/exponent. `P01ID` is the subset defined in section 2. `Digest` is 64 lowercase hex; `Nonce` is 64 lowercase hex. Fresh generation nonce is 32 lowercase hex, while historical generation nonce is P01ID. New reservation/release/acquisition/decision IDs are Nonce. Boot IDs in historical wire generations preserve P01ID exactly; fresh root boot must match fixed kernel UUID. `Bool` is JSON true/false.

Canonical encoding is UTF-8 restricted to printable ASCII strings, with only quote/backslash escaping. Keys sort by underlying ASCII bytes; no whitespace/BOM/newline. Duplicate/unknown keys reject before map conversion. Integers, null and booleans have one syntax. Arrays sort by declared identity, not serializer accident. Decode consumes all bytes and canonical re-encode must match. Reject excessive nesting/frames before unbounded allocation.

```text
ResourceClass = workspace|home|xdg_config|xdg_state|xdg_data|cache|runtime_tmp|
 provider_private|process_scope|mount_scope|network_scope|materialization|candidate_stage
ResourceState = reserved|allocating|allocated|active|fencing|fenced|destroying|
 absent_verified|cleanup_unverified|quarantined
QState = clear|quarantined|block_reuse|operator_resolution_pending|
 released_for_new_authorization|remains_quarantined
QReason = owner_unknown|identity_conflict|stale_generation|fence_unverified|
 cleanup_unverified|possible_disclosure|storage_uncertain|external_effect_ambiguous|
 operator_resolution_required
ObservationKind = process_identity|writer_fence|namespace_inventory|mount_identity|
 filesystem_identity|backing_identity|loop_identity|socket_identity|reference_inventory|
 allocation_history|absence
ObservationStatus = verified_present|verified_fenced|verified_absent|unsupported|
 incomplete|identity_conflict|stale
DiagnosticState = OPEN|CAPTURING|TRUNCATED_DRAINING|CLOSED|CANCELLED|INCOMPLETE
DisclosureObservation = NOT_OBSERVED|NO_DISCLOSURE_OBSERVED|OBSERVATION_INCOMPLETE|
 POSSIBLE_DISCLOSURE|KNOWN_DISCLOSURE
DisclosureQualification = NOT_QUALIFIED|HOST_ONLY_PARTIAL|INTEGRATED_QUALIFIED
ReasonCode = unsupported_capability|missing_history|identity_mismatch|stale_generation|
 event_gap|timeout|cancelled|truncated|storage_uncertain|protocol_error|
 coverage_incomplete|possible_disclosure|known_disclosure|limit_exceeded
ErrorCode = invalid_request|unauthorized_caller|unsupported_host|unqualified_profile|
 unencodable_p01_value|lock_busy|client_dead|identity_conflict|stale_session|
 stale_generation|head_conflict|phase_conflict|replay_conflict|limit_exceeded|
 storage_unavailable|storage_corrupt|write_failed|sync_failed|maintenance_required|
 cleanup_unverified|decision_missing|decision_revoked|decision_consumed
```

Native errors are typed and never contain raw request, path, stderr, token or exception text. Elixir adapter maps new protocol errors to existing boundary error families where required, preserving storage failure latches. `lock_busy`, client/identity/generation/protocol/decision failures deny authority. Unknown errors map to boundary unavailable with gate closed.

### 5.2 Closed type registry

#### RuntimeIdentity

```text
{runtime_attempt_id:P01ID,work_item_id:P01ID,lineage_generation:P01ID,responsibility:P01ID,runtime_profile:P01ID}
```

#### Generation

```text
{schema_version:1,project_namespace:P01ID,host_id:P01ID,boot_id:P01ID,sequence:PositiveU64,nonce:P01ID}
```

#### GrantRef

```text
{grant_id:P01ID,project_namespace:P01ID,runtime_identity:RuntimeIdentity,fence_epoch:PositiveU64,grant_sha256:Digest}
```

#### EvidenceLink

```text
null | {kind:"prior",id:P01ID} | {kind:"current",id:null}
```

#### ObjectRef

```text
{evidence_id:P01ID,evidence_sha256:Digest}
```

#### SelfBinding

```text
{resource_id:P01ID,slot:"last_evidence_ref"|"quarantine_evidence_ref"}
```

#### QuarantineDispositionWire

```text
{state:QState,reason:?QReason,evidence_ref:EvidenceLink,generation:Generation,resolution_ref:?P01ID}
```

#### ResourceSetEntry

```text
{resource_id:P01ID,class:ResourceClass,project_namespace:P01ID,owner_host_id:P01ID,runtime_identity:RuntimeIdentity,creation_generation:Generation,fence_epoch:PositiveU64,grant_sha256:Digest,stable_locator_sha256:Digest,allocation_identity_sha256:?Digest,capacity_profile_sha256:Digest}
```

#### ResourceSet

```text
{schema:"G2-RSET-2",generation:Generation,grant_id:P01ID,resources:[ResourceSetEntry]}
```

#### ResourceSnapshotEntry

```text
{resource_id:P01ID,revision:U64,state:ResourceState,reconciliation_generation:Generation,last_evidence_ref:EvidenceLink,quarantine:QuarantineDispositionWire}
```

#### ResourceSnapshot

```text
{schema:"G2-SNAPSHOT-2",generation:Generation,resources:[ResourceSnapshotEntry]}
```

#### StoredResourceProjection

```text
{schema_version:1,resource_id:P01ID,project_namespace:P01ID,grant_id:P01ID,runtime_identity:RuntimeIdentity,class:ResourceClass,state:ResourceState,revision:U64,stable_locator_sha256:Digest,allocation_identity_sha256:?Digest,capacity_profile_sha256:Digest,owner_host_id:P01ID,creation_generation:Generation,reconciliation_generation:Generation,last_evidence_ref:EvidenceLink,quarantine:QuarantineDispositionWire}
```

#### LedgerMetadata

```text
{schema_version:1,project_namespace:P01ID,host_id:P01ID,current_generation:Generation}
```

#### FileIdentity

```text
{device:U64,inode:U64,size:U64,mtime_ns:U64,ctime_ns:U64}
```

#### NamespaceIdentity

```text
{kind:"mnt"|"pid"|"user"|"net"|"ipc"|"uts"|"cgroup",device:U64,inode:U64}
```

#### ProcessIdentity

```text
{manifest_entry_id:P01ID,boot_id:P01ID,pid:PositiveU64,start_ticks:U64,uid:U64,gid:U64,executable_sha256:Digest,executable_device:U64,executable_inode:U64,cgroup_identity_sha256:Digest,namespaces:[NamespaceIdentity],allocation_identity_sha256:Digest}
```

#### KernelHandleObservation

```text
{kind:"pidfd",identity:ProcessIdentity,acquired_monotonic_ns:U64,rechecked_monotonic_ns:U64,live:Bool,identity_match:Bool}
```

#### ManifestResource

```text
{resource_id:P01ID,class:ResourceClass,allocation_identity_sha256:Digest,locator_registration_id:P01ID,object_identity_sha256:Digest,owner_history_sha256:Digest,coverage_profile_sha256:Digest,processes:[ProcessIdentity]}
```

#### ResourceManifest

```text
{schema:"G2-MANIFEST-2",contract_revision:"P08-SPEC-0.7",namespace:P01ID,host_id:P01ID,grant_ref:GrantRef,creation_generation:Generation,source:"controlled_fixture"|"qualified_allocator",resources:[ManifestResource],diagnostic_policy_sha256:Digest,installer_record_sha256:Digest,qualification_profile_sha256:Digest}
```

#### Observation

```text
{resource_id:P01ID,kind:ObservationKind,ordinal:U64,status:ObservationStatus,source_manifest_sha256:Digest,observed_monotonic_ns:U64,allocation_identity_sha256:?Digest,process:?KernelHandleObservation,observed_identity_sha256:?Digest,reference_inventory_sha256:?Digest,coverage_profile_sha256:Digest,reason:?ReasonCode}
```

#### DiagnosticStream

```text
{stream:"stdout"|"stderr",retained_bytes:U64,observed_bytes:U64,discarded_bytes:U64,counter_saturated:Bool,truncated:Bool,eof:Bool}
```

#### DiagnosticRecord

```text
DiagnosticRecord = DiagnosticCaptureRecord | DiagnosticNotApplicableRecord
DiagnosticCaptureRecord = {kind:"CAPTURE",acquisition_id:Nonce,state:DiagnosticState,generation:Generation,diagnostic_policy_sha256:Digest,streams:[DiagnosticStream],cancelled:Bool,incomplete:Bool,reason:?ReasonCode}
DiagnosticNotApplicableRecord = {kind:"NOT_APPLICABLE",acquisition_id:Nonce,generation:Generation,diagnostic_policy_sha256:Digest,scope:"RESOURCE_ONLY",basis:"NO_RESOURCE_DIAGNOSTIC_CHANNEL_REQUIRED",channel_count:0,capture_started:false}
DiagnosticPolicy = {schema:"G2-DIAGNOSTIC-POLICY-2",contract_revision:"P08-SPEC-0.7",policy_id:Nonce,resource_only:Bool,required_streams:["stdout"|"stderr"],allow_no_capture:Bool,qualification_profile_sha256:Digest}
```

The variants are closed and disjoint. NOT_APPLICABLE has no state, stream, EOF, truncation or completed-capture fields. It is not CLOSED and cannot satisfy a diagnostic-completion requirement. Its policy digest is H(DIAGNOSTIC_POLICY, canonical DiagnosticPolicy). Required streams are unique and ordered stdout then stderr. Empty required_streams is valid only for resource_only=true with allow_no_capture=true. When zero channels are required and none was opened, the helper MUST select NOT_APPLICABLE, not an empty CAPTURE/CLOSED record. A CAPTURE record contains exactly the policy-required stream records in that order; an opened additional resource diagnostic channel makes coverage incomplete rather than silently disappearing.

A root-registered ResourceManifest binds diagnostic_policy_sha256. Helper and independent verifier select the variant from that exact qualified policy and actual acquisition facts, never request preference. NOT_APPLICABLE is valid only when the policy explicitly permits resource-only observation, requires zero resource diagnostic channels, and none was opened or captured. It cannot replace an interrupted, missing, required or already-started capture. A channel existed but was not collected is INCOMPLETE under CAPTURE, not NOT_APPLICABLE. Control framing and fixed administrative status channels are separately qualified invocation transport, not fictitious resource diagnostic capture.

For a valid NOT_APPLICABLE resource-only acquisition, the current DisclosureRecord is NOT_OBSERVED and NOT_QUALIFIED with null artifact/logging/qualification references. Existing sticky disclosure history is retained. This supplies no no-disclosure or integrated OB-025 proof. Unresolved disclosure still blocks settlement. A claim requiring diagnostics, secrecy qualification or integrated coverage rejects NOT_APPLICABLE even when its structure is valid.

#### DisclosureRecord

```text
{observation:DisclosureObservation,qualification:DisclosureQualification,scope:"host_only"|"integrated",acquisition_id:Nonce,generation:Generation,artifact_sha256:?Digest,logging_profile_sha256:?Digest,qualification_sha256:?Digest,predecessor_sha256:?Digest,known_disclosure_history:Bool,unresolved_disclosure_history:Bool,reason:?ReasonCode}
```

#### EvidenceObject

```text
{schema:"G2-EVIDENCE-2",contract_revision:"P08-SPEC-0.7",acquisition_id:Nonce,release_id:Nonce,purpose:"RELEASE"|"QUARANTINE_EVIDENCE",acquired_monotonic_ns:U64,completed_monotonic_ns:U64,invalidation_epoch:Nonce,generation:Generation,owner_epoch:Nonce,grant_ref:GrantRef,resource_set:ResourceSet,resource_set_sha256:Digest,pre_snapshot:ResourceSnapshot,post_snapshot:ResourceSnapshot,self_bindings:[SelfBinding],observations:[Observation],diagnostics:DiagnosticRecord,disclosure:DisclosureRecord,predecessors:[ObjectRef],verifier_implementation_sha256:Digest,installation_profile_sha256:Digest,qualification_profile_sha256:Digest}
```

#### CleanupEvidenceRefWire

```text
{schema_version:1,evidence_id:P01ID,evidence_sha256:Digest,project_namespace:P01ID,grant_id:P01ID,runtime_identity:RuntimeIdentity,fence_epoch:PositiveU64,resource_set_sha256:Digest,verification_generation:Generation,verifier_implementation_sha256:Digest}
```

#### Revision

```text
{resource_id:P01ID,revision:U64}
```

#### RowCommitment

```text
{resource_id:P01ID,before_sha256:Digest,after_sha256:Digest}
```

#### Commitment

```text
{schema:"G2-RECOVERY-MIRROR-2"|"G2-INDEX-2",sha256:Digest}
```

#### ResourceCommitment

```text
{generation:Generation,resource_set_sha256:Digest,snapshot_sha256:Digest,revisions:[Revision]}
```

#### GenerationProposal

```text
{schema:"G2-GENERATION-PROPOSAL-2",contract_revision:"P08-SPEC-0.7",reservation_id:Nonce,namespace:P01ID,host_id:P01ID,owner_epoch:Nonce,session_id:Nonce,source_head_sha256:?Digest,source_generation:?Generation,source_metadata_sha256:?Digest,source_rows_sha256:Digest,ledger_registration_sha256:Digest,ledger_identity:?FileIdentity,target_generation:Generation,reserved_sequence:PositiveU64,expires_monotonic_ns:U64}
```

#### RecoveryPlan

```text
{schema:"G2-RECOVERY-PLAN-2",contract_revision:"P08-SPEC-0.7",plan_id:Nonce,proposal_sha256:Digest,host_journal_sha256:Digest,ledger_registration_sha256:Digest,source_generation:?Generation,target_generation:Generation,source_metadata_sha256:?Digest,target_metadata_sha256:Digest,source_rows_sha256:Digest,target_rows_sha256:Digest,row_commitments:[RowCommitment],source_pending:Bool}
```

#### RecoveryMirror

```text
{schema:"G2-RECOVERY-MIRROR-2",contract_revision:"P08-SPEC-0.7",plan_sha256:Digest,generation:Generation,target_metadata_sha256:Digest,target_rows_sha256:Digest,owner_epoch:Nonce,pending_marker_absent:true}
```

#### AttemptReleaseProjection

```text
{release_id:Nonce,grant_ref:GrantRef,generation:Generation,binding_sha256:Digest,before_fence_sha256:Digest,released:true,evidence_id:P01ID,evidence_sha256:Digest,resource_set_sha256:Digest,post_snapshot_sha256:Digest}
```

#### AttemptReceipt

```text
{release_id:Nonce,grant_ref:GrantRef,generation:Generation,binding_sha256:Digest,before_fence_sha256:Digest,released:true,prepare_sha256:Digest,evidence_id:P01ID,evidence_sha256:Digest,resource_set_sha256:Digest,post_snapshot_sha256:Digest}
```

#### IndexReceipt

```text
{release_id:Nonce,generation:Generation,index_restriction_sha256:Digest,phase:"INDEXED"|"RESOURCE_VERIFIED"|"PREPARED"|"ATTEMPT_COMMITTED"|"COMPLETED",evidence_id:P01ID,evidence_sha256:Digest,root_commitment_sha256:Digest,resource_commitment_sha256:Digest,attempt_receipt_sha256:?Digest}
```

#### JointRead

```text
{read_id:Nonce,owner_epoch:Nonce,generation:Generation,root_head_sha256:Digest,index:IndexReceipt,resource:ResourceCommitment,attempt:AttemptReceipt,disclosure_record_sha256:Digest,qualification_profile_sha256:Digest,checked_monotonic_ns:U64}
```

#### ReleaseRecord

```text
{schema:"G2-RELEASE-2",contract_revision:"P08-SPEC-0.7",release_id:Nonce,generation:Generation,owner_epoch:Nonce,purpose:"RELEASE"|"QUARANTINE_EVIDENCE",retained_quarantine_sha256:?Digest,authorization_sha256:?Digest,phase:ReleasePhase,grant_ref:GrantRef,resource_set_sha256:Digest,pre_snapshot_sha256:Digest,post_snapshot_sha256:?Digest,evidence:?ObjectRef,resource_commitment:?ResourceCommitment,attempt_projection:?AttemptReleaseProjection,prepare_sha256:?Digest,actual_attempt_receipt_sha256:?Digest,completion_sha256:?Digest,predecessor_sha256:?Digest}
```

#### ResolutionDecision

```text
ResolutionDecision = RetainResolutionDecision | ReleaseResolutionDecision
RetainResolutionDecision = {schema:"G2-RESOLUTION-AUTHORITY-2",contract_revision:"P08-SPEC-0.7",decision_id:Nonce,issuer_id:P01ID,issuer_role:"HUMAN_MASTER_GATE",source_decision_sha256:Digest,provisioning_authorization_sha256:Digest,installer_identity_sha256:Digest,repository:"JCSchoeman96/symphony",namespace:P01ID,host_id:P01ID,installation_profile_sha256:Digest,generation:Generation,owner_epoch:Nonce,quarantine_sha256:Digest,resource_set_sha256:Digest,resource_snapshot_sha256:Digest,evidence_id:null,evidence_sha256:null,permitted_disposition:"remains_quarantined",unresolved_obligation_sha256:Digest,expected_root_head_sha256:Digest,handoff_sha256:Digest,expires_monotonic_ns:U64,one_use:true}
ReleaseResolutionDecision = {schema:"G2-RESOLUTION-AUTHORITY-2",contract_revision:"P08-SPEC-0.7",decision_id:Nonce,issuer_id:P01ID,issuer_role:"HUMAN_MASTER_GATE",source_decision_sha256:Digest,provisioning_authorization_sha256:Digest,installer_identity_sha256:Digest,repository:"JCSchoeman96/symphony",namespace:P01ID,host_id:P01ID,installation_profile_sha256:Digest,generation:Generation,owner_epoch:Nonce,quarantine_sha256:Digest,resource_set_sha256:Digest,resource_snapshot_sha256:Digest,evidence_id:P01ID,evidence_sha256:Digest,permitted_disposition:"released_for_new_authorization",unresolved_obligation_sha256:Digest,expected_root_head_sha256:Digest,handoff_sha256:Digest,expires_monotonic_ns:U64,one_use:true}
PendingResolution = {schema:"G2-RESOLUTION-PENDING-2",contract_revision:"P08-SPEC-0.7",decision_id:Nonce,decision_sha256:Digest,namespace:P01ID,host_id:P01ID,generation:Generation,owner_epoch:Nonce,session_id:Nonce,initial_quarantine_sha256:Digest,initial_root_head_sha256:Digest,resource_set_sha256:Digest,resource_snapshot_sha256:Digest,permitted_disposition:"released_for_new_authorization"|"remains_quarantined"}
```

permitted_disposition is a terminal permission, not the intermediate state. Both decision variants authorize only the explicit begin action into operator_resolution_pending plus their allowed terminal action. RetainResolutionDecision carries null evidence and cannot release. ReleaseResolutionDecision carries exact qualified evidence identity; its release may fail closed to retain, which reduces authority. No request may turn a retaining decision into a releasing decision. PendingResolution is separately content-addressed under RESOLUTION_PENDING; it never embeds its own digest.

#### QuarantineRecord

```text
{schema:"G2-QUARANTINE-2",contract_revision:"P08-SPEC-0.7",record_id:Nonce,generation:Generation,resource_ids:[P01ID],disposition:QuarantineDispositionWire,disclosure_record_sha256:?Digest,decision_id:?Nonce,decision_sha256:?Digest,predecessor_sha256:?Digest}
```

#### ResolutionRegistryEntry

```text
{decision_id:Nonce,decision_sha256:Digest,status:"AVAILABLE"|"REVOKED",provisioning_record_sha256:Digest,revocation_record_sha256:?Digest}
```

#### RootControl

```text
{schema:"G2-CONTROL-2",contract_revision:"P08-SPEC-0.7",namespace:P01ID,host_id:P01ID,control_revision:PositiveU64,predecessor_sha256:?Digest,generation:?Generation,reserved_sequence:U64,owner_epoch:Nonce,session_id:Nonce,session_state:"ACTIVE"|"QUIESCENT"|"INTERRUPTED",gate:"CLOSED"|"QUARANTINED"|"SETTLED",phase:RootPhase,proposal_sha256:?Digest,plan_sha256:?Digest,release_id:?Nonce,resource_set_sha256:?Digest,evidence:?ObjectRef,observation_sha256:?Digest,release_record_sha256:?Digest,quarantine_sha256:?Digest,pending_resolution_sha256:?Digest,consumed_decision_sha256:?Digest,authority_handoff_sha256:?Digest,quarantine_evidence_sha256:?Digest,operation_sha256:Digest,installation_profile_sha256:Digest,qualification_profile_sha256:Digest}
```

#### RootReceipt

```text
{record:RootControl,record_sha256:Digest}
```

#### QualificationClaim

```text
{schema:"G2-QUALIFICATION-2",contract_revision:"P08-SPEC-0.7",claim_id:P01ID,state:"PROPOSED"|"BUILT"|"ENVIRONMENT_QUALIFIED"|"TESTED"|"REVIEWED"|"ACCEPTED"|"REJECTED"|"BLOCKED",reason:?ReasonCode,scope:"host_only"|"integrated",package:"P08"|"P02"|"P03"|"P04"|"P06"|"P07"|"P09",source_sha:Hex40,source_tree:Hex40,artifact_sha256:Digest,environment_sha256:Digest,profile_sha256:Digest,test_ids:[P01ID],evidence_sha256:[Digest],independent_decision_sha256:?Digest}
```

`Hex40` is exactly 40 lowercase hexadecimal characters. ReleasePhase is RESTRICTED, SNAPSHOT_BOUND, OBSERVED, EVIDENCE_PUBLISHED, RESOURCE_VERIFIED, PREPARED, ATTEMPT_COMMITTED, COMPLETED, SETTLED or QUARANTINED. RootPhase adds PROPOSED, PLAN_BOUND, GENERATION_COMMITTED_CLOSED and ABANDONED. I may additionally record INDEXED as a host phase; it is not a root acknowledgement opcode.

All resource arrays/row commitments/revisions/self-bindings sort by resource_id, then slot. Namespace arrays sort by kind. Observation arrays sort by resource_id, kind, ordinal. CAPTURE stream arrays contain the policy-required streams in stdout/stderr order; NOT_APPLICABLE has no streams field. Predecessor ObjectRefs sort by evidence_id; qualification test IDs/digests sort lexicographically. Duplicate resource identities, kinds per process namespace, streams, test IDs or predecessor IDs reject. A source row list can be empty only for explicitly registered fresh creation, never to prove empty production cleanup.

### 5.2a Additional authority and receipt projections

```text
FenceReason = completion|cancellation|failure|restart|publication
BoundaryBinding = {kind:"gate2",binding_version:1,lineage_binding_id:P01ID,resource_ledger_namespace:P01ID}
BoundFenceProjection = {state:"bound",runtime_attempt:RuntimeIdentity,route_fingerprint:?P01ID,gate2_fence:{reference:GrantRef,status:"requested",requested_reason:?FenceReason}}
PreparedReleaseProof = {owner_epoch:Nonce,root_prepare_receipt:RootReceipt,resource_commitment:ResourceCommitment,attempt_projection:AttemptReleaseProjection,evidence:CleanupEvidenceRefWire}
FenceProof = {owner_epoch:Nonce,generation:Generation,resource_id:P01ID,expected_revision:U64,snapshot_sha256:Digest,observation:Observation,root_receipt:RootReceipt}
InstallationProfile = {schema:"G2-INSTALLATION-2",contract_revision:"P08-SPEC-0.7",host_id:P01ID,host_uid:U64,host_gid:U64,client_sha256:Digest,client_device:U64,client_inode:U64,helper_sha256:Digest,helper_device:U64,helper_inode:U64,sudo_sha256:Digest,sudo_plugins_sha256:Digest,sudo_policy_sha256:Digest,kernel_profile_sha256:Digest,filesystem_profile_sha256:Digest,numerical_profile_sha256:Digest,qualification_profile_sha256:Digest,namespace_registrations_sha256:Digest,issuer_registry_sha256:Digest,installer_registry_sha256:Digest,diagnostic_policy_registry_sha256:Digest}
NamespaceRegistration = {namespace:P01ID,host_id:P01ID,lock_device:U64,lock_inode:U64,ledger_registration_sha256:Digest,allocation_manifest_sha256:Digest,locator_registry_sha256:Digest,grant_registration_sha256:Digest,fresh_creation_authorized:Bool}
```

BoundaryBinding retains P01's stricter 1–128-byte trimmed nonempty lineage_binding_id/resource_ledger_namespace checks. Wider P01ID wire capacity never relaxes a field-specific accepted restriction. BoundFenceProjection represents an absent stored requested_reason as null; a malformed stored requested_reason is rejected by accepted validation, not normalized. Binding and fence digests are H(BINDING, canonical BoundaryBinding) and H(FENCE, canonical BoundFenceProjection). Receipt/projection/resource commitment digests use their matching labels above. Namespace registration digests bind fixed host-owned paths; requests never contain those paths. Root-owned grant registration bytes use this closed record:

```text
GrantRegistration = {schema:"G2-GRANT-REGISTRATION-2",contract_revision:"P08-SPEC-0.7",namespace:P01ID,grant_ref:GrantRef,source_admission_policy_sha256:Digest,process_policy_sha256:Digest,network_policy_sha256:Digest,tool_policy_sha256:Digest,capacity_profile_sha256:Digest,provisioning_authorization_sha256:Digest,scope:"fixture_only"|"integrated_owner"}
IssuerRegistration = {issuer_id:P01ID,role:"HUMAN_MASTER_GATE",source_authorization_sha256:Digest,active:Bool}
InstallerRegistration = {installer_id:P01ID,run_as_uid:0,source_authorization_sha256:Digest,audit_identity_sha256:Digest,active:Bool}
```

Registry files contain sorted unique arrays of these exact registrations, with file digests pinned by InstallationProfile. A grant registration authenticates a metadata commitment for the selected scope; P08 still does not issue/activate a grant. Integrated-owner entries cannot become qualified before their owning packages are accepted. Native root validates installation registry digests and each registered namespace without accepting a runtime replacement registry.

### 5.2b Closed authority and restriction records

These records follow G2-CJSON-2, including duplicate/unknown-key rejection and all field bounds in section 5.1. Arrays are sorted unique. Each record is at most 8,192 bytes, except DiagnosticPolicy and its registry as bounded below. There are no caller-selected paths. These are P08 wire records, not changes to accepted P01 structs.

```text
AuthorityHandoff = {schema:"G2-AUTHORITY-HANDOFF-2",contract_revision:"P08-SPEC-0.7",handoff_id:Nonce,namespace:P01ID,host_id:P01ID,generation:Generation,owner_epoch:Nonce,source_session_id:Nonce,source_head_sha256:Digest,purpose:"RESOLUTION"|"QUARANTINE_EVIDENCE",quarantine_sha256:Digest,resource_set_sha256:Digest,resource_snapshot_sha256:Digest,issued_monotonic_ns:U64,expires_monotonic_ns:U64,installation_profile_sha256:Digest}
IndexRestriction = {schema:"G2-INDEX-RESTRICTION-2",contract_revision:"P08-SPEC-0.7",namespace:P01ID,generation:Generation,owner_epoch:Nonce,release_id:Nonce,purpose:"RELEASE"|"QUARANTINE_EVIDENCE",retained_quarantine_sha256:?Digest,resource_set_sha256:Digest,root_restriction_head_sha256:Digest,root_release_record_sha256:Digest,previous_index_sha256:?Digest,phase:"RESTRICTED"}
IndexRestrictionReceipt = {record:IndexRestriction,index_restriction_sha256:Digest}
QuarantineEvidenceRecord = {schema:"G2-QUARANTINE-EVIDENCE-2",contract_revision:"P08-SPEC-0.7",release_id:Nonce,generation:Generation,owner_epoch:Nonce,quarantine_sha256:Digest,authorization_sha256:Digest,resource_set_sha256:Digest,pre_snapshot_sha256:Digest,evidence:ObjectRef,verdict:"VERIFIED"|"UNVERIFIED",reason:?ReasonCode,predecessor_head_sha256:Digest}
QuarantineEvidenceIndex = {schema:"G2-QUARANTINE-EVIDENCE-INDEX-2",contract_revision:"P08-SPEC-0.7",release_id:Nonce,generation:Generation,index_restriction_sha256:Digest,root_terminal_head_sha256:Digest,quarantine_evidence_sha256:Digest,evidence:ObjectRef,phase:"QUARANTINED"}
DiagnosticPolicyRegistration = {policy_sha256:Digest,canonical_file_sha256:Digest,qualification_profile_sha256:Digest,qualification_claim_sha256:Digest,source_acceptance_sha256:Digest,installer_identity_sha256:Digest}
DiagnosticPolicyRegistry = {schema:"G2-DIAGNOSTIC-POLICY-REGISTRY-2",contract_revision:"P08-SPEC-0.7",entries:[DiagnosticPolicyRegistration]}
```

Handoff uses H(AUTHORITY_HANDOFF). IndexRestriction uses H(INDEX_RESTRICTION), terminal quarantine evidence uses H(QUARANTINE_EVIDENCE), its index uses H(QUARANTINE_EVIDENCE_INDEX), and the policy registry uses H(DIAGNOSTIC_POLICY_REGISTRY). IndexRestrictionReceipt.index_restriction_sha256 hashes its record, never the enclosing receipt. DiagnosticPolicy uses H(DIAGNOSTIC_POLICY). Policy entries sort by policy_sha256; zero entries confer no eligibility. The registry has at most 64 entries and 32,768 canonical bytes. Each policy is at most 4,096 bytes. Each added record uses the existing version-2 hash domain and its own schema/revision; the six published resource-set/snapshot fixtures therefore do not change.

ResolutionDecision and quarantine acquisition authorization now require handoff_sha256 and expires_monotonic_ns. Their owner_epoch comes from the existing handoff, never an anticipated future session. Their expected_root_head_sha256 is the post-close RootControl digest that references that handoff. The handoff itself contains only the pre-close source head, avoiding a self-hash cycle. Decision expiry must be later than issuance and no later than handoff expiry. Current boot must equal Generation.boot_id.

IndexReceipt additionally requires index_restriction_sha256. It preserves the initial restriction throughout its release. RootControl's new nullable authority_handoff_sha256 and quarantine_evidence_sha256 fields default to null only when constructing a new v0.7 record. Missing fields in stored v0.7 bytes reject. Any contract_revision other than P08-SPEC-0.7 is unsupported and rejected, including historical proposed v0.3/v0.4/v0.5/v0.6 encodings; no implicit migration, default filling or rehashing is permitted. EvidenceObject.purpose and ReleaseRecord.purpose must agree. retained_quarantine_sha256 is nonnull exactly for QUARANTINE_EVIDENCE. No P01 field is added or truncated by this wire revision.

### 5.2c Trusted diagnostic-policy materialization and lookup

The separately authorized root installer materializes reviewed canonical DiagnosticPolicy bytes from the exact accepted policy artifact. Neither BEAM nor a provider supplies those bytes as authority. Before installation it verifies the human acceptance artifact, active installer registration and an accepted qualification claim binding the exact policy digest, qualification profile and permitted resource-only scope. An unqualified proposed policy may be archived but MUST NOT enter the active registry. Policy acceptance is a separate external decision; this specification does not qualify any policy.

The fixed directory is `/etc/symphony/gate2/p08-v2/diagnostic-policies/`. The file is `<policy_sha256>.json`, where the name is derived from the registered manifest digest, not a request path. Directory ancestors are root-owned and not group/other writable. Policies and `registry.json` are regular root-owned mode 0444, single-link files. InstallationProfile.diagnostic_policy_registry_sha256 pins the canonical registry. Registry entries bind both domain-separated policy digest and raw canonical-file SHA-256 plus the independently accepted claim and installer. Publication uses temporary file sync, no-replace rename, directory sync, then separately authorized installation-profile enrollment. A partial installation has no active pinned entry and blocks lookup. Runtime helper has no registry-write operation.

At startup and before a diagnostic eligibility verdict, helper independently opens the fixed directory and registered file with NOFOLLOW/CLOEXEC, verifies ancestry, owner, mode, file type, link count, length and both digests, rejects noncanonical bytes, and checks policy.profile against the exact active qualified profile. It checks the accepted claim's digest and scope against the pinned qualification records. It keeps the verified file descriptor through publication and rechecks file identity/content and registry/profile pins before publishing. All trusted policy installers honor the same exclusive namespace lock; installation-profile replacement requires a separately authorized closed maintenance state and invalidates outstanding handoffs/observations. No hot replacement during an acquisition is allowed. An unexpected administrative replacement outside that protocol is a trust-boundary failure, not an accepted input.

Qualification claim bytes are the closed QualificationClaim in section 5.2, installed at `/etc/symphony/gate2/p08-v2/qualification/claims/<qualification_claim_sha256>.json` with the same root ownership, 0444 regular-file, single-link and canonical-byte rules. The registry's qualification_claim_sha256 is H(QUALIFICATION, those bytes). Require state=ACCEPTED, scope=host_only for no-capture eligibility, package=P08, profile_sha256 equal to the resolved policy profile, artifact_sha256 equal to canonical_file_sha256, and independent_decision_sha256 equal to source_acceptance_sha256. That decision digest must resolve to exact original administrative decision bytes at `/etc/symphony/gate2/p08-v2/qualification/acceptances/<source_acceptance_sha256>.bin`, at most 65,536 bytes, root-owned mode 0444, regular and single-link. Its raw SHA-256 must equal source_acceptance_sha256. The enrolled root installer verifies the human issuer and exact policy/scope acceptance before materialization and attests that verification through the pinned registry entry and active installer registration, using the same administrative trust model as ResolutionDecision. Runtime verification checks this root attestation and archived bytes; it does not infer human authority by parsing arbitrary text or trusting a self-declared ACCEPTED field. The claim and decision archives are installed under separately approved root administrative authority before policy registry enrollment. They are never written by a runtime opcode. Claims/profile bytes precede policy registry construction; they do not contain the future registry or installation-profile digest. Missing or unverifiable archive provenance blocks enrollment and lookup. Full integrated qualification is never inferred from this host-only claim.

The independent host verifier reads the same fixed read-only root files and repeats canonical-byte, registry, profile and qualification-claim verification. It cannot accept a policy merely because its digest equals the caller or EvidenceObject digest. Missing file, missing accepted claim, wrong scope, changed inode/content/profile, malformed registry or unsupported identity checks return the existing typed unqualified_profile, unsupported_host or cleanup-verification failure. They invalidate the acquisition and retain closed/quarantined admission. No default policy, empty policy or inferred NOT_APPLICABLE is permitted. NOT_APPLICABLE requires a resolved accepted resource-only policy, allow_no_capture=true, required_streams=[], no opened channel, and no diagnostics/secrecy claim. CAPTURE remains independently required where the resolved policy requires streams.

Proof obligations map to P08-EVD-001/002 and P08-DIA-001/003/004. Tests must reject missing/replaced/unqualified policy, a caller-chosen digest, tampered registry, partial enrollment, stale profile, capture falsely represented as no-capture, and policy replacement between observation and publication. P08-T16 owns those tests; P08-T06 owns installation-profile resolution and mutation exclusion. Root fixture tests require separate privilege authorization.

### 5.3 Hashes, identity and cycles

For label L and canonical bytes B, `H(L,B)=SHA256("SYMPHONY-G2" || 0x00 || ASCII(L) || 0x00 || "2" || 0x00 || B)`. Labels are RESOURCE_SET, SNAPSHOT, EVIDENCE, CONTROL, RELEASE, QUARANTINE, MANIFEST, DIAGNOSTIC_DISPOSITION, DISCLOSURE_DISPOSITION, QUALIFICATION, GENERATION_PROPOSAL, RECOVERY_PLAN, RESOURCE_ROW, ROW_SET, METADATA, INDEX, OPERATION, RESOLUTION_DECISION, RESOLUTION_PENDING, DIAGNOSTIC_POLICY, RESOURCE_COMMITMENT, ATTEMPT_RECEIPT, ATTEMPT_PROJECTION, BINDING, FENCE, INSTALLATION, OBSERVATION, AUTHORITY_HANDOFF, INDEX_RESTRICTION, QUARANTINE_EVIDENCE, QUARANTINE_EVIDENCE_INDEX, DIAGNOSTIC_POLICY_REGISTRY. Raw SHA-256 is explicitly used only for opaque file/build/source commitments and journal bytes. `stable_locator_sha256` is SHA256 of exact locator bytes; it is not an ownership claim.

Resource-set hash input is exactly canonical ResourceSet, including immutable set creation generation, sorted complete members and their creation/allocation/grant/locator/capacity identities. Restart alone does not change it. Membership or immutable identity change creates a new set. ResourceSnapshot independently binds every revision, current reconciliation generation, state and quarantine. Evidence timestamps and observations use host CLOCK_MONOTONIC in the current boot, with acquired<=observed<=completed. At consumption, age from acquired must not exceed accepted snapshot age and invalidation_epoch must remain unchanged. Any gap, owner change or revision mutation invalidates the whole result. Timestamps alone are never identity or ownership proof.

Evidence ID is `ev2-` plus H(EVIDENCE, object bytes). CleanupEvidenceRef schema 1 describes the reference format; the resolver must require object schema G2-EVIDENCE-2 and contract revision P08-SPEC-0.7. Shape construction does not resolve provenance. Index/object mismatch, stale generation or unqualified producer rejects.

Post-snapshot hashing uses only declared current-link slots. Actual R string IDs must equal resolved evidence ID before normalization. A preparation hashes AttemptReleaseProjection without prepare_sha256. A actual receipt must separately equal that preparation digest. Completion hashes the full actual receipt. No record contains its own digest. ReleaseRecord at PREPARED has prepare_sha256=null; its H(RELEASE, bytes) is the preparation digest returned and later referenced by A/ATTEMPT_COMMITTED. ReleaseRecord at COMPLETED has completion_sha256=null; its H(RELEASE, bytes) is the completion digest. Only the later SETTLED record stores that prior completion digest. Response digests never flow back into the record that determines them. RootControl references separately hashed proposal/plan/release records, never its own future root receipt. Operation commitments hash the canonical request body before response construction.

Root resource manifests contain only IDs and digests. Root installation maps locator_registration_id to fixed qualified allocation-owned paths/handles and history. Requests cannot introduce that mapping. Production manifest source qualified_allocator is invalid until owner qualification exists. Controlled fixture source supports only fixture claims.

### 5.4 Golden fixture and compatibility procedures

Every fixture is literal bytes without a newline. Both languages must decode, reject ambiguity, re-encode identically and independently hash the original bytes. The following small fixtures isolate generation semantics; empty membership is a codec fixture only and cannot authorize release.

Fixture GF-01, label `RESOURCE_SET`, 229 bytes, expected digest `3dd66f38e18b6a43936fcda924905ce06c98e33610185b3271ddd6dd81ac2011`.

```json
{"generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"11111111111111111111111111111111","project_namespace":"p","schema_version":1,"sequence":1},"grant_id":"g","resources":[],"schema":"G2-RSET-2"}
```

Fixture GF-02, label `SNAPSHOT`, 218 bytes, expected digest `417352565cb4a674c474b50f87c0d289eba1dc601afb435ffc3c267d31435424`.

```json
{"generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"77777777777777777777777777777777","project_namespace":"p","schema_version":1,"sequence":7},"resources":[],"schema":"G2-SNAPSHOT-2"}
```

Fixture GF-03, label `SNAPSHOT`, 218 bytes, expected digest `4acc72072ec8e1bb60b23ba77c13d03c10134d6d4ab45a0d70911e78c3020900`.

```json
{"generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"88888888888888888888888888888888","project_namespace":"p","schema_version":1,"sequence":8},"resources":[],"schema":"G2-SNAPSHOT-2"}
```

GF-01 remains byte-identical after restart because creation generation stays one. GF-02 and GF-03 differ because current snapshot generation advances. Future tests must add nonempty resource fixtures, revision-only changes, self-reference mismatch, every scalar boundary, all operation bodies and cross-language rejection vectors. Alternative escapes, key order, duplicate/unknown keys, Unicode, oversized IDs, negative/exponential numbers and trailing bytes reject.

### 5.5 Nonempty creation/restart fixtures

These controlled byte fixtures do not establish allocation history or production cleanup. GF-04 membership stays unchanged across GF-05/GF-06; only the snapshot generation/revision/quarantine changes.

Fixture GF-04, label `RESOURCE_SET`, 1017 bytes, expected digest `bd1af514d31ae009ad58cef925972e4ac34f07b94cb075bf1ca13c2ad00f61b0`.

```json
{"generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"11111111111111111111111111111111","project_namespace":"p","schema_version":1,"sequence":1},"grant_id":"g","resources":[{"allocation_identity_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","capacity_profile_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","class":"runtime_tmp","creation_generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"11111111111111111111111111111111","project_namespace":"p","schema_version":1,"sequence":1},"fence_epoch":1,"grant_sha256":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","owner_host_id":"h","project_namespace":"p","resource_id":"x","runtime_identity":{"lineage_generation":"l","responsibility":"builder","runtime_attempt_id":"a","runtime_profile":"r","work_item_id":"w"},"stable_locator_sha256":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"}],"schema":"G2-RSET-2"}
```

Fixture GF-05, label `SNAPSHOT`, 752 bytes, expected digest `2a30b6c370a4e5938f18a2bb5b4e70f9762c153015b64ade86265128d5230bb6`.

```json
{"generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"77777777777777777777777777777777","project_namespace":"p","schema_version":1,"sequence":7},"resources":[{"last_evidence_ref":null,"quarantine":{"evidence_ref":null,"generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"77777777777777777777777777777777","project_namespace":"p","schema_version":1,"sequence":7},"reason":null,"resolution_ref":null,"state":"clear"},"reconciliation_generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"77777777777777777777777777777777","project_namespace":"p","schema_version":1,"sequence":7},"resource_id":"x","revision":4,"state":"destroying"}],"schema":"G2-SNAPSHOT-2"}
```

Fixture GF-06, label `SNAPSHOT`, 773 bytes, expected digest `8448ff40017ee446b6e4bf3fa26ec7ba634d84b60506d2b6406b4007efc63408`.

```json
{"generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"88888888888888888888888888888888","project_namespace":"p","schema_version":1,"sequence":8},"resources":[{"last_evidence_ref":null,"quarantine":{"evidence_ref":null,"generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"88888888888888888888888888888888","project_namespace":"p","schema_version":1,"sequence":8},"reason":"stale_generation","resolution_ref":null,"state":"quarantined"},"reconciliation_generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"88888888888888888888888888888888","project_namespace":"p","schema_version":1,"sequence":8},"resource_id":"x","revision":5,"state":"quarantined"}],"schema":"G2-SNAPSHOT-2"}
```

### 5.6 v0.3 variant shape examples

These canonical shape examples carry no real registration, decision or qualification. Authority guards remain mandatory. Adding state/streams to NOT_APPLICABLE, evidence fields to retain, omitting release proof or using a retaining decision for release MUST reject.

Resource-only no capture, schema-valid only.

```json
{"acquisition_id":"aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa","basis":"NO_RESOURCE_DIAGNOSTIC_CHANNEL_REQUIRED","capture_started":false,"channel_count":0,"diagnostic_policy_sha256":"bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb","generation":{"boot_id":"00000000-0000-0000-0000-000000000001","host_id":"h","nonce":"11111111111111111111111111111111","project_namespace":"p","schema_version":1,"sequence":1},"kind":"NOT_APPLICABLE","scope":"RESOURCE_ONLY"}
```

Retain request body without fresh proof, schema-valid only.

```json
{"action":"retain","decision_id":"cccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccccc","decision_sha256":"dddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddddd","pending_resolution_sha256":"eeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeeee","reason":"cleanup_unverified"}
```

## 6. Native operation contracts

### 6.1 Framing and common guards

Exactly 15 opcodes are defined below. All payloads use four-byte unsigned big-endian length followed by canonical JSON; frame limit excludes prefix. Hello is protocol bootstrap, not an opcode.

Hello request is `{protocol:"G2-P08-SESSION-2",contract_revision:"P08-SPEC-0.7",namespace:P01ID,owner_epoch:Nonce,intent:"recovery"|"release"|"query"|"quarantine"}`. Helper validates installation, client and namespace, acquires lock, then returns `{protocol:"G2-P08-SESSION-2",contract_revision:"P08-SPEC-0.7",session_id:Nonce,owner_epoch:Nonce,receipt:?RootReceipt,installation_profile_sha256:Digest}`. Null receipt is allowed only for explicitly registered pristine root state. Unknown/missing history does not create pristine state.

Request envelope is `{protocol:"G2-P08-SESSION-2",contract_revision:"P08-SPEC-0.7",session_id:Nonce,sequence:PositiveU64,opcode:Opcode,expected_head_sha256:?Digest,owner_epoch:Nonce,generation:?Generation,body:RequestType}`. Response envelope is the same protocol/revision/session/sequence/opcode plus `{status:"ok"|"error",receipt:?RootReceipt,body:?ResponseType,error:?ErrorCode}`. Success has nonnull body and null error; error has null body. An uncertain root write has null receipt and terminates mutation processing. Pre-authentication failure emits only a fixed exit/error classification, no attacker payload.

COMMON_AUTH: exact qualified client UID/GID/executable/ancestry and live incarnation, captured boundary caller and owner epoch, sole lock, current installation, correct intent/sequence/session, expected current head and legal phase. Envelope generation is committed current generation, nullable only before first commitment; target generation is explicitly in proposal/plan bodies, never smuggled as current. A new boundary recovery session may inspect old current generation without inheriting release authority. Generic host callers cannot supply native control attestations through public APIs.

COMMON_FAILURE: listed ErrorCode, closed or quarantined admission, no next mutation after protocol/storage uncertainty, no raw diagnostics. COMMON_RETRY: request sequence is never repeated; duplicate/out-of-order frames reject. After lost response query current root under a new authenticated lock; no blind effect replay. Same-session operation-specific logical repetition uses a new sequence only when explicitly allowed and exact payload commitments match. COMMON_RESTART: no session restored; a new boundary owner closes/invalidates observations; same-boundary QUIESCENT session adoption is limited to section 6.18; recovery follows section 4. Each operation's proof includes wrong fields, wrong phase/head/session/generation, unauthorized caller and lost response. Only query_settlement is a read-only application opcode; close_session and negative/quarantine results still write control metadata.

Root accepts R/I/A receipts only as authenticated trusted-boundary attestations. It checks them against its own recorded commitments and qualified evidence. It does not deserialize DETS. Boundary independently rereads actual stores, and future admission repeats that read. A caller-provided correctly shaped clean assertion never reaches this trust path.

### 6.2 `propose_generation`

```text
OPERATION=propose_generation
AUTHORIZED_CALLER=COMMON_AUTH; intent recovery
REQUIRED_SESSION_STATE=closed startup or pending bound recovery
REQUEST_SCHEMA={action:"new",reservation_id:Nonce,source_generation:?Generation,source_metadata_sha256:?Digest,source_rows_sha256:Digest,ledger_registration_sha256:Digest,ledger_identity:?FileIdentity} | {action:"resume_bound",plan_sha256:Digest,host_journal_sha256:Digest,inspection_rows_sha256:Digest}
RESPONSE_SCHEMA={proposal:GenerationProposal,proposal_sha256:Digest,plan:?RecoveryPlan,repair_required:Bool}
AUTHORITY_GUARDS=New action requires no conflicting bound plan and validated source; helper selects target, persists reservation/high-water, then returns. Resume requires the exact preexisting root plan and source/target row inspection; returns its original target and no new reservation.
PERSISTED_IDENTITY=GenerationProposal and RootControl PROPOSED, or re-attested existing PLAN_BOUND; no R mutation.
ORDERED_SIDE_EFFECTS=COMMON root publication order; GenerationProposal and RootControl PROPOSED, or re-attested existing PLAN_BOUND; no R mutation.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Exact logical repetition in same session returns existing proposal only; conflicting source rejects. New session abandons an unbound proposal and burns its sequence.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=New proposal is an expiring reservation, not committed current generation. Resume grants only exact fact repair.
NEGATIVE_TESTS=GEN-PROPOSAL-LOSS; GEN-ABANDON; GEN-RESUME; GEN-H1-H2
```

### 6.3 `begin_recovery`

```text
OPERATION=begin_recovery
AUTHORIZED_CALLER=COMMON_AUTH; intent recovery
REQUIRED_SESSION_STATE=PROPOSED
REQUEST_SCHEMA={plan:RecoveryPlan}
RESPONSE_SCHEMA={plan_sha256:Digest,target_generation:Generation,host_journal_sha256:Digest,phase:"PLAN_BOUND"}
AUTHORITY_GUARDS=Plan proposal digest, target and source must equal current reservation. Host journal has already synchronized and its after images use that target. Reject expired reservation or another session proposal.
PERSISTED_IDENTITY=Publish RecoveryPlan then RootControl PLAN_BOUND before any R write. Root trusts authenticated host journal durability attestation, not arbitrary caller metadata.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Publish RecoveryPlan then RootControl PLAN_BOUND before any R write. Root trusts authenticated host journal durability attestation, not arbitrary caller metadata.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Exact new-sequence repetition may return bound plan; changed journal or target rejects. Lost response requires query before R writes.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Exact plan makes subsequent R mutation possible while admission stays closed.
NEGATIVE_TESTS=GEN-JOURNAL-BIND; GEN-CONFLICT; GEN-ROOT-PLAN-LOSS
```

### 6.4 `ack_recovery`

```text
OPERATION=ack_recovery
AUTHORIZED_CALLER=COMMON_AUTH; intent recovery
REQUIRED_SESSION_STATE=PLAN_BOUND
REQUEST_SCHEMA={plan_sha256:Digest,host_journal_sha256:Digest,target_metadata_sha256:Digest,target_rows_sha256:Digest,pending_marker_absent:true,mirror:RecoveryMirror}
RESPONSE_SCHEMA={generation:Generation,recovery_commit_sha256:Digest,gate:"CLOSED",further_generation_required:Bool}
AUTHORITY_GUARDS=Exact plan and journal; target row/metadata rereads and synchronized mirror must agree. A prior-owner repaired plan sets further_generation_required=true.
PERSISTED_IDENTITY=Root records selected generation as committed, then closed boundary requires E/I/R reread before activation.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Root records selected generation as committed, then closed boundary requires E/I/R reread before activation.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Exact logical repetition reads existing commitment; no second increment. New owner must perform a fresh proposal after repair.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Durable current facts only; no restored runtime authority.
NEGATIVE_TESTS=GEN-ACK-LOSS; GEN-MIRROR-LOSS; GEN-REPEAT
```

### 6.5 `restrict_release`

```text
OPERATION=restrict_release
AUTHORIZED_CALLER=COMMON_AUTH; intent release
REQUIRED_SESSION_STATE=GENERATION_COMMITTED_CLOSED or current quiescent closed gate with no unresolved release; alternatively QUARANTINED with the exact section 6.17 authorization and no pending resolution
REQUEST_SCHEMA={release_id:Nonce,grant_ref:GrantRef,resource_set_sha256:Digest,before_resource:ResourceCommitment,before_attempt_fence_sha256:Digest,quarantine_acquisition_sha256:?Digest}
RESPONSE_SCHEMA={release_id:Nonce,root_restriction_sha256:Digest,root_restriction:RootRestrictionProof,gate:"CLOSED"|"QUARANTINED",phase:"RESTRICTED"}
# gate is QUARANTINED exactly when quarantine_acquisition_sha256 is nonnull; otherwise CLOSED.
AUTHORITY_GUARDS=Validate before_resource and the initial snapshot commitment under section 6.5b. Exact current generation, namespace, existing bound fence, qualified profile and no unresolved quarantine, except the evidence-only authorization in section 6.17. quarantine_acquisition_sha256 is null normally; otherwise it must resolve to the exact unexpired one-use root authorization and section 6.18 handoff with the unchanged post-close head and only evidence acquisition is allowed. A previous settled release cannot rearm a lineage.
PERSISTED_IDENTITY=Publish restriction and RootControl RESTRICTED; the initial immutable ReleaseRecord explicitly stores authorization_sha256 as defined in section 6.5a; I restriction must sync before snapshot use.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Publish restriction and RootControl RESTRICTED; the initial immutable ReleaseRecord explicitly stores authorization_sha256 as defined in section 6.5a; I restriction must sync before snapshot use.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Same ID/content may return restriction; ID/content conflict rejects. New session cannot resume release after owner restart.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Restriction persists independent of A fence.
NEGATIVE_TESTS=REL-RESTRICT; REL-REPLAY; AUTH-NAMESPACE
```

### 6.5a Durable acquisition-authorization consumption

ReleaseRecord.authorization_sha256 is a required nullable Digest in the v0.7 closed schema. It is null exactly when purpose=RELEASE. It equals the request's nonnull quarantine_acquisition_sha256 exactly when purpose=QUARANTINE_EVIDENCE. The helper resolves that digest to the provisioned authorization and independently checks its handoff, scope, expiry and one-use history before any restriction commit. Every successor ReleaseRecord for the same acquisition preserves the same digest. QuarantineEvidenceRecord.authorization_sha256 must equal this initial value; an object with a different or missing value rejects. No inferred value from operation_sha256 or later evidence may substitute for it.

The initial consumption record is the immutable ReleaseRecord with phase=RESTRICTED. Under the root lock the helper constructs it, synchronizes its file, publishes it without replacement and synchronizes its directory. It then constructs RootControl with release_record_sha256=H(RELEASE, those exact bytes), the same release_id, G/epoch and retained quarantine. It publishes/synchronizes that control record, replaces the root head and synchronizes the head directory before acknowledging restrict_release. Root head reachability is the consumption commit boundary. Quarantine remains blocked throughout. I persistence and evidence acquisition occur afterward; their absence cannot undo consumption.

Recovery owns classification under the authenticated exclusive root lock. It rereads the actual head and complete validated predecessor chain, resolves all referenced initial restriction ReleaseRecords and their authorization_sha256 fields, and verifies immutable bytes/digests. It also checks the separately provisioned authorization and any incomplete/orphan publication from the interrupted operation. Consumed identities remain discoverable through retained root history after generation advancement, quarantine resolution or later acquisitions. No compaction may discard this replay history without a separately reviewed authority-preserving format. Missing/corrupt/unavailable history is UNCERTAIN, never UNUSED.

| Durable outcome after lost response | Classification and recovery action | Admission and replay |
|---|---|---|
| No publication was attempted, stable validated head/chain contains no matching consumption, no unresolved write/orphan exists, and original handoff/head/scope remain valid | UNUSED. Classification alone neither executes nor retries the operation. A separately requested authorized invocation must recheck every guard. | Quarantine remains; expiry, changed head/G/owner or revocation still denies use. |
| Reachable initial RESTRICTED record contains exact authorization digest, even with no I restriction or terminal evidence | CONSUMED. Return the existing restriction identity as historical status; never start a second acquisition with that authorization. | Quarantine remains; recovery cannot clear consumption or resume stale observations. |
| A later reachable terminal record exists | CONSUMED. Check its authorization equals the initial restriction and retain the entire provenance chain. | Existing terminal quarantine semantics apply; no reuse. |
| File, directory or head sync was uncertain; old/new head may have persisted; an orphan restriction exists; or any relevant history is missing/conflicting | UNCERTAIN until actual persisted state is reconciled. A valid reachable matching restriction establishes CONSUMED. An orphan alone cannot establish authoritative consumption or unused status. Otherwise require maintenance; retain objects and block authorization use. Never roll back a head to manufacture UNUSED. | Quarantine remains and all replay/admission is denied. A new authorization cannot bypass the unresolved root transaction. |

After a host crash, root recovery validates and synchronizes the selected actual head and its directory before relying on that head's durability. A readable but unsynchronized head is not proof of agreement. If sync fails, classification remains UNCERTAIN. In-process query after a lost response likewise cannot clear a prior recorded storage uncertainty by merely reading bytes. There is no host-supplied clean assertion, registry AVAILABLE override or automatic retry.

P08-QUA-002 and P08-REL-004/005 require acquisition_consumption_restrict_commit, acquisition_consumption_lost_reply, acquisition_consumption_before_terminal, acquisition_consumption_orphan_uncertain and acquisition_consumption_history_missing. Inject failure before/after initial record file sync, publication/directory sync, control publication, head replacement and head-directory sync. Test both durable outcomes at each uncertain boundary. Assert exact authorization digest in reachable initial bytes, unchanged quarantine, no R/A effects and rejection of reuse across recovery/generation changes. T06 implements initial record publication and replay-history checks; T14 implements interrupted acquisition/recovery integration. T15 depends on T14 and reviews these identities in later resolution tests. These are future tests requiring the existing separate execution/privilege authorizations.

### 6.5b Initial snapshot provenance and distinct restriction identities

The selected construction keeps ReleaseRecord.pre_snapshot_sha256 nonnull in every phase. At RESTRICTED it equals restrict_release.before_resource.snapshot_sha256 exactly. Initial ReleaseRecord.resource_commitment is the exact before_resource value, not null. Its resource_set_sha256 equals both the request field and before_resource.resource_set_sha256. Its generation equals before_resource.generation and current committed G. The helper validates these equalities and the exact registered grant/namespace/qualified manifest and complete sorted revision vector before committing the restriction. This authenticates a captured-host commitment under the split trust model; it does not independently prove R contents or absence.

Before restrict_release, the captured boundary serializes namespace access, checks staged recovery is closed/consistent, and authoritatively rereads actual R membership, rows and revisions in the current generation. It constructs the canonical ResourceSnapshot and ResourceCommitment from that exact read, using H(SNAPSHOT, canonical snapshot) as snapshot_sha256. Missing, pending, corrupt or disagreeing rows block. This pre-restriction serialization computes a proposed commitment only. It cannot authorize observations, R verification, release or admission. A caller-supplied digest or cached snapshot cannot replace that R read. The native helper relies on the independently authenticated trusted host owner for this R attestation, as elsewhere in the E/I/R/A design; runtime bytes are not an authority source.

After the root restriction commits, I synchronizes its initial IndexRestriction and the boundary rereads it. Only then does the boundary reread actual R and pass its exact canonical before_snapshot to bind_snapshot. The helper verifies H(SNAPSHOT, before_snapshot) equals the initial ReleaseRecord.pre_snapshot_sha256 and initial resource_commitment.snapshot_sha256. It verifies snapshot generation, membership/resource-set digest and every revision against the initial resource_commitment and current registered manifest. The captured boundary independently checks that snapshot against actual R immediately before sending it. Any change or mismatch returns the existing head_conflict, stale_generation or identity_conflict result as applicable, preserves the restriction and blocks progress. No digest rebasing, in-place record editing or automatic fresh transaction is allowed. Both RELEASE and QUARANTINE_EVIDENCE use these rules.

The digest names have separate closed meanings:

* root_restriction_sha256 is H(RELEASE, canonical initial RESTRICTED ReleaseRecord). restrict_release returns this digest after the root-head commit. It is never an I digest or a root-head digest.
* root_restriction_head_sha256 is H(CONTROL, the committed initial RESTRICTED RootControl). The response envelope receipt identifies this record and digest; it must reference root_restriction_sha256 in release_record_sha256.
* index_restriction_sha256 is H(INDEX_RESTRICTION, canonical IndexRestriction). HostEvidence.Ledger.restrict_sync/3 returns it under the variable name index_restriction_digest only after I synchronization/reread. IndexRestrictionReceipt and later I records use the explicit field index_restriction_sha256. The helper cannot compute or return this during restrict_release because I constructs the record afterward, including previous_index_sha256.

Before constructing I, its owner requires the returned root_restriction_sha256 equal root_receipt.record.release_record_sha256 and the recomputed digest of the actual initial ReleaseRecord. It requires the envelope receipt's verified digest equal H(CONTROL, receipt.record). It sets IndexRestriction.root_release_record_sha256 to root_restriction_sha256 and root_restriction_head_sha256 to that receipt digest. namespace/G/epoch/release_id/purpose/retained quarantine/resource-set fields must match the root record and initial ReleaseRecord. previous_index_sha256 comes solely from the actual validated prior I terminal history under section 7.1b. It cannot be inferred from root_restriction_sha256.

At bind_snapshot, the helper recomputes index_restriction_sha256 from IndexRestrictionReceipt.record, checks all the preceding equality relationships against reachable root bytes and the current RESTRICTED head, and checks the initial snapshot commitment. The boundary has already synchronized and reread actual I before sending the receipt. A correctly hashed forged receipt is insufficient without both captured-owner and native authentication checks. The returned snapshot_commit_sha256 remains the distinct frozen snapshot-commitment identity defined by bind_snapshot; it cannot substitute for either restriction digest. All later IndexReceipt and QuarantineEvidenceIndex values retain the same index_restriction_sha256. Historical digest names/encodings are rejected under the current closed contract rather than accepted as aliases.

| Crash or mismatch | Persisted possibilities | Required disposition |
|---|---|---|
| Before/after root restriction commit, before I | Prior head or RESTRICTED with the exact proposed snapshot digest | Existing consumption uncertainty rules apply; no snapshot progress and no inferred I digest. |
| I row/head write or sync interrupted | Neither, partial or complete I restriction | Section 7.1b reconciliation; bind_snapshot requires synchronized actual I reread and exact receipt. |
| R changes between commitment read and bind | Initial root/I commitments remain; actual snapshot hash or revisions differ | Deny binding, retain closed/quarantined restriction; no overwrite or automatic retry. |
| SNAPSHOT_BOUND record published but head update uncertain | Orphan successor, prior RESTRICTED head or reachable SNAPSHOT_BOUND head | Reread/synchronize under root ownership; orphan alone cannot authorize observation. Owner restart invalidates observation continuity. |
| Bound reply lost or wrong root/I digest supplied | Exact predecessor/successor chain or mismatch | Only documented same-session exact idempotency is allowed; any disagreement blocks and cannot fabricate settlement. |

P08-EVD-002 and P08-REL-001/004/005 require initial_snapshot_commitment_match, initial_snapshot_commitment_mismatch, restriction_root_index_digest_distinct, restriction_receipt_cross_binding, snapshot_bind_after_index_sync_only and restriction_to_snapshot_crash_windows. T06 implements native equality/phase/hash controls, T11 I construction and predecessor controls, and T14 the integrated crash/negative tests after T16 diagnostic eligibility is available. Test both persisted outcomes around each write/sync, independently compute the two hashes, and assert no observation/R/A effect when I is absent or a commitment differs. Tests remain future separately authorized work.

### 6.5c Authenticated root restriction bytes and host verification

The selected read path uses the existing authenticated native channel. Root E permissions remain unchanged. restrict_release returns RootRestrictionProof with the initial immutable record, and query_settlement can return that same proof for its selected release_id. No new opcode, caller path or direct host E access is introduced.

```text
RootRestrictionProof = {initial_release_record:ReleaseRecord,restriction_receipt:RootReceipt,current_receipt:RootReceipt,reachable_from_current_head:true}
```

The proof is a closed G2-CJSON-2 record, at most 65,536 canonical bytes. It is not an independently authoritative persisted store and needs no new hash domain. Existing complete output-frame bounds still apply to the entire response, including optional evidence. Overflow returns limit_exceeded without truncation or successful proof. Qualification must measure maximum-size proof/combined-response handling within existing memory and time budgets. No production size/profile acceptance is asserted here.

Before sending the proof, helper rereads the immutable initial ReleaseRecord from E and verifies its H(RELEASE) digest. It rereads its committed RESTRICTED RootControl and verifies H(CONTROL), phase, release_id and record reference. Under the same root lock it validates that restriction receipt is the current head or a reachable predecessor of the actual current head. It returns both receipts and the exact closed representation of those bytes. The envelope receipt must equal proof.current_receipt in full. At initial restrict_release success, current_receipt equals restriction_receipt; the body root_restriction_sha256 equals H(RELEASE, initial_release_record). The helper returns no proof from an orphan, corrupt record or unavailable/unvalidated chain.

The captured boundary verifies kernel sender/client continuity, frame/revision/session/sequence, qualification and installation identity before decoding the response. It rejects unknown/duplicate fields and checks canonical re-encoding, then independently computes H(RELEASE) of initial_release_record and H(CONTROL) of both receipt records. It compares those results with the supplied digests, the restriction receipt's release_record_sha256 and root_restriction_sha256 when present. It checks initial phase=RESTRICTED, release/namespace/grant/G/epoch/purpose/quarantine/authorization identity, the proposed ResourceCommitment and snapshot digest against its actual captured R/A context. It checks current_receipt equals the current authenticated envelope receipt and the expected root head for that response. Initial success also requires current_receipt=restriction_receipt. Only then does it construct I input.

HostEvidence.Ledger.restrict_sync/3 now takes RootRestrictionProof as its third argument, preserving arity. It accepts only the captured boundary and repeats canonical-byte/hash, exact-context and receipt equality checks before constructing IndexRestriction under section 7.1b. It stores the original proof's initial bytes and restriction receipt as verified provenance in its existing immutable restriction-history payload; the history payload is exactly {restriction:IndexRestriction,root_proof:RootRestrictionProof}. Its authority-bearing IndexRestriction hash remains H(INDEX_RESTRICTION, restriction), not a hash of that wrapper. First history creation stores the first fully verified proof and is synchronized before active-row advancement. On idempotent reread/query, keep that immutable wrapper when its initial record, restriction receipt and restriction bytes match; do not overwrite it merely because a newer query has a different current_receipt. Independently validate the fresh query proof for current authority. Conflicting initial bytes or restriction receipt requires maintenance. Active I row tags/digests and namespace-head rules stay unchanged. History validation must check wrapper consistency; a wrapper alone never supplies current root authority.

This is independent host computation and semantic comparison within the split trusted-helper/host model. The host does not independently open root-only files, verify kernel facts by parsing JSON, or cryptographically establish root-chain membership. The qualified root helper independently reads E and attests reachability over the authenticated live channel; the host independently validates the returned bytes and their bindings against its own ledger context. A caller-shaped RootRestrictionProof, matching hashes alone or an unauthenticated cached response cannot enter restrict_sync.

For lost restrict_release response, do not repeat the effect. Acquire the existing lock in a fresh authenticated query session and call query_settlement with the original release_id. A nonnull release_id selects that exact reachable initial restriction; null selects the current head's release_id if any. Its root_restriction is null only when the selected release has no reachable committed restriction; a corrupt/incomplete chain returns an error, not a null proof of non-consumption. Query returns initial bytes and original restriction receipt plus the actual current receipt after root reachability verification. It never selects an orphan or treats a changed current head as the original head.

The boundary performs the same hash/context checks on query output and classifies current versus historical G/epoch/session state. A historical proof may support conservative consumption classification or exact I repair only where existing recovery authority permits it. It cannot resume old observations or authorize admission. Changed owner, ACTIVE/INTERRUPTED prior session, unresolved durability, stale generation or incomplete I history remains blocked under sections 4/6.5a/7.1b. Null proof alone cannot establish UNUSED; the complete existing consumption and uncertainty rules still apply. An unconfirmed live helper retains its lock and prevents this query.

P08-EVD-002 and P08-REL-001/004/005 require root_restriction_bytes_roundtrip, root_restriction_bytes_tamper, root_restriction_wrong_receipt, root_restriction_query_lost_reply, root_restriction_query_orphan and root_restriction_query_historical. T06 implements root read/reachability/response and corpus checks; T11 implements host proof/hash/history checks; T14 implements real lost-response and I integration. Tests must alter canonical record bytes independently of supplied hashes, swap each receipt and context, and assert refusal before any I restriction/snapshot progress. Fixture tests alone cannot qualify native reachability or the authenticated channel.

### 6.6 `bind_snapshot`

```text
OPERATION=bind_snapshot
AUTHORIZED_CALLER=COMMON_AUTH; intent release
REQUIRED_SESSION_STATE=RESTRICTED
REQUEST_SCHEMA={release_id:Nonce,resource_set:ResourceSet,before_snapshot:ResourceSnapshot,allocation_manifest_sha256:Digest,capacity_profile_sha256:Digest,index_restriction:IndexRestrictionReceipt}
RESPONSE_SCHEMA={release_id:Nonce,resource_set_sha256:Digest,pre_snapshot_sha256:Digest,snapshot_commit_sha256:Digest,phase:"SNAPSHOT_BOUND"}
AUTHORITY_GUARDS=Complete sorted membership and exact revisions/generation. Manifest is root registered and qualified; no caller-added locator/ownership. Validate IndexRestrictionReceipt under section 7.1b before binding or using the snapshot. Require the exact initial commitment and cross-receipt equalities in section 6.5b; mismatches never overwrite the restriction.
PERSISTED_IDENTITY=Publish a new immutable SNAPSHOT_BOUND ReleaseRecord preserving initial pre_snapshot_sha256, with predecessor_sha256 equal to root_restriction_sha256; publish its RootControl successor. No R/A change.
ORDERED_SIDE_EFFECTS=After durable I reread and exact section 6.5b equality checks, publish the SNAPSHOT_BOUND ReleaseRecord and RootControl under COMMON root publication ordering. No R/A change.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Exact same-session repeat only. Changed revision or membership requires abandon and fresh transaction, not overwrite.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Frozen input for observation, never absence proof.
NEGATIVE_TESTS=EVD-MEMBERSHIP; REL-REVISION; RES-HISTORY
```

### 6.7 `observe_fence`

```text
OPERATION=observe_fence
AUTHORIZED_CALLER=COMMON_AUTH; intent release
REQUIRED_SESSION_STATE=SNAPSHOT_BOUND
REQUEST_SCHEMA={release_id:Nonce,snapshot_commit_sha256:Digest,owner_fence_record_sha256:Digest}
RESPONSE_SCHEMA={release_id:Nonce,observation_sha256:Digest,verdict:"VERIFIED_FENCED"|"UNVERIFIED",reason:?ReasonCode}
AUTHORITY_GUARDS=Independently verify exact writer scope and stable process identities using qualified owner history; PID/EOF alone insufficient.
PERSISTED_IDENTITY=Publish bounded Observation under H(OBSERVATION, canonical bytes), bind its digest in RootControl.observation_sha256, then update head. VERIFIED_FENCED sets OBSERVED; UNVERIFIED closes/quarantines. No signal or confinement effect.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Publish bounded Observation under H(OBSERVATION, canonical bytes), bind its digest in RootControl.observation_sha256, then update head. VERIFIED_FENCED sets OBSERVED; UNVERIFIED closes/quarantines. No signal or confinement effect.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Observation is never replayed as fresh. Another acquisition requires fresh ID/observation after invalidation.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Writer absence in qualified scope only, not resource cleanliness.
NEGATIVE_TESTS=PROC-REPLACE; PROC-WRAPPER; EVD-EVENT-GAP
```

### 6.8 `observe_absence`

```text
OPERATION=observe_absence
AUTHORIZED_CALLER=COMMON_AUTH; intent release
REQUIRED_SESSION_STATE=OBSERVED with verified fence
REQUEST_SCHEMA={release_id:Nonce,snapshot_commit_sha256:Digest,fence_observation_sha256:Digest,destruction_owner_record_sha256:?Digest}
RESPONSE_SCHEMA={release_id:Nonce,verdict:"VERIFIED"|"UNVERIFIED",evidence:EvidenceObject,evidence_id:P01ID,evidence_sha256:Digest,publication_sha256:Digest,quarantine_evidence:?QuarantineEvidenceRecord,reason:?ReasonCode}
AUTHORITY_GUARDS=Exact allocation/object identity, current revision, full qualified reference coverage, diagnostic/disclosure applicability for the exact claim. CAPTURE must be complete and eligible when required. NOT_APPLICABLE is accepted only under the resource-only policy guards in section 5.2 and cannot satisfy diagnostic or integrated secrecy claims. Missing destruction/allocation history cannot prove absence.
PERSISTED_IDENTITY=Construct evidence natively; sync file, no-replace publish, sync directory, publish root provenance. For RELEASE, VERIFIED enters EVIDENCE_PUBLISHED and quarantine_evidence is null; failure object is historical/quarantined and cannot verify R. For QUARANTINE_EVIDENCE, publish the terminal record under section 6.17 and return nonnull quarantine_evidence; gate and phase are QUARANTINED for either verdict. No R verification is permitted on this path.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Construct evidence natively; sync file, no-replace publish, sync directory, publish root provenance. For RELEASE, VERIFIED enters EVIDENCE_PUBLISHED and quarantine_evidence is null; failure object is historical/quarantined and cannot verify R. For QUARANTINE_EVIDENCE, publish the terminal record under section 6.17 and return nonnull quarantine_evidence; gate and phase are QUARANTINED for either verdict. No R verification is permitted on this path.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=No blind repeat. Observation age/event invalidation requires new acquisition; uncertain publication requires root query.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Immutable scoped observation, still no A release.
NEGATIVE_TESTS=RES-REPLACE; EVD-FORGE; REL-OBJECT-SYNC; DIA-SECRET
```

### 6.9 `ack_resource_commit`

```text
OPERATION=ack_resource_commit
AUTHORIZED_CALLER=COMMON_AUTH; intent release
REQUIRED_SESSION_STATE=EVIDENCE_PUBLISHED
REQUEST_SCHEMA={release_id:Nonce,evidence_id:P01ID,evidence_sha256:Digest,actual_resource:ResourceCommitment,index_receipt:IndexReceipt}
RESPONSE_SCHEMA={release_id:Nonce,resource_ack_sha256:Digest,phase:"RESOURCE_VERIFIED"}
AUTHORITY_GUARDS=ReleaseRecord.purpose must be RELEASE; QUARANTINE_EVIDENCE rejects. Native verified object and exact predicted post-snapshot/revision vector. I INDEXED or RESOURCE_VERIFIED binds same object. Boundary has actually synced and reread R.
PERSISTED_IDENTITY=Publish trusted-host resource acknowledgement before preparation. Root does not independently parse R.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Publish trusted-host resource acknowledgement before preparation. Root does not independently parse R.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Exact repeat is read-idempotent; changed R or object rejects.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Committed R state acknowledged; no A authority.
NEGATIVE_TESTS=REL-R-ACK; REL-R-PARTIAL; REL-ORDER
```

### 6.10 `prepare_release`

```text
OPERATION=prepare_release
AUTHORIZED_CALLER=COMMON_AUTH; intent release
REQUIRED_SESSION_STATE=RESOURCE_VERIFIED
REQUEST_SCHEMA={release_id:Nonce,evidence_id:P01ID,evidence_sha256:Digest,resource_commit:ResourceCommitment,index_receipt:IndexReceipt,expected_attempt_release:AttemptReleaseProjection}
RESPONSE_SCHEMA={release_id:Nonce,prepare_sha256:Digest,expected_attempt_projection_sha256:Digest,phase:"PREPARED"}
AUTHORITY_GUARDS=Root resource acknowledgement already durable. Exact before-fence/binding and projection, evidence and I agreement. No future completion ID in projection.
PERSISTED_IDENTITY=Publish preparation and expected A projection. A remains fenced until its separate writer commits.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Publish preparation and expected A projection. A remains fenced until its separate writer commits.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Exact repeat returns preparation; changed projection rejects.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Preparation permits only exact boundary A commit, not admission.
NEGATIVE_TESTS=REL-ORDER; REL-A-PREPARE; REL-CYCLE
```

### 6.11 `ack_attempt_commit`

```text
OPERATION=ack_attempt_commit
AUTHORIZED_CALLER=COMMON_AUTH; intent release
REQUIRED_SESSION_STATE=PREPARED
REQUEST_SCHEMA={release_id:Nonce,actual_attempt_receipt:AttemptReceipt,actual_resource:ResourceCommitment,index_receipt:IndexReceipt}
RESPONSE_SCHEMA={release_id:Nonce,attempt_ack_sha256:Digest,actual_attempt_receipt_sha256:Digest,phase:"ATTEMPT_COMMITTED"}
AUTHORITY_GUARDS=Actual A receipt reread equals prepared projection plus exact preparation hash; R unchanged; I PREPARED or ATTEMPT_COMMITTED.
PERSISTED_IDENTITY=Root records authenticated host A acknowledgement; still closed.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Root records authenticated host A acknowledgement; still closed.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Lost A result must be reread, not release retried. Exact receipt repeat returns recorded acknowledgement.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=A may be released but admission remains denied.
NEGATIVE_TESTS=REL-A-LOST; REL-A-FORGE; REL-A-WITHOUT-COMPLETE
```

### 6.12 `complete_release`

```text
OPERATION=complete_release
AUTHORIZED_CALLER=COMMON_AUTH; intent release
REQUIRED_SESSION_STATE=ATTEMPT_COMMITTED for record_completion; COMPLETED for settle
REQUEST_SCHEMA={action:"record_completion",release_id:Nonce,joint_read:JointRead} | {action:"settle",release_id:Nonce,completion_sha256:Digest,joint_read:JointRead}
RESPONSE_SCHEMA={release_id:Nonce,completion_sha256:Digest,settlement_sha256:?Digest,phase:"COMPLETED"|"SETTLED"}
AUTHORITY_GUARDS=Fresh serialized actual E/I/R/A reread using the same-session bracketed queries in section 6.13a, exact current owner/G, complete coverage and resolved obligations. First action requires I ATTEMPT_COMMITTED. Settle requires I COMPLETED naming root completion and a new read_id.
PERSISTED_IDENTITY=Record completion first; host I completion sync next; second action writes SETTLED after fresh reread. Root settlement binds exact I completion commitment. Optional I settled cache never becomes prerequisite authority.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Record completion first; host I completion sync next; second action writes SETTLED after fresh reread. Root settlement binds exact I completion commitment. Optional I settled cache never becomes prerequisite authority.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Exact result query allowed; no old JointRead reused. Root/host disagreement blocks.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Settled resource/fence transaction only. P08 dispatch stays dormant.
NEGATIVE_TESTS=REL-COMPLETE-LOSS; REL-I-LOSS; REL-SETTLED-STALE
```

### 6.13 `query_settlement`

```text
OPERATION=query_settlement
AUTHORIZED_CALLER=COMMON_AUTH; intent query, recovery or release, including an already ACTIVE release session under its existing lock
REQUIRED_SESSION_STATE=any authenticated readable root phase
REQUEST_SCHEMA={release_id:?Nonce,include_evidence:Bool}
RESPONSE_SCHEMA={gate:"CLOSED"|"QUARANTINED"|"SETTLED",phase:RootPhase,release_id:?Nonce,evidence:?EvidenceObject,unresolved_transaction:Bool,generation:?Generation,owner_epoch:Nonce,proposal:?GenerationProposal,plan:?RecoveryPlan,pending_resolution:?PendingResolution,authority_handoff:?AuthorityHandoff,quarantine_evidence:?QuarantineEvidenceRecord,root_restriction:?RootRestrictionProof}
AUTHORITY_GUARDS=Existing exclusive root lock, authenticated same client/session/owner/current generation, next valid sequence and exact expected current head. ACTIVE release sessions may query without closing, changing intent or acquiring another lock. Section 6.13a defines mandatory read points. It returns authoritative reachable records only; old owner/generation facts explicitly cannot satisfy current admission.
PERSISTED_IDENTITY=No application mutation. Returns current receipts/proposal/plan for reconciliation; never selects newest orphan.
ORDERED_SIDE_EFFECTS=No publication or persistent mutation. Reread actual current root head and selected immutable objects under the held lock, verify digests/reachability, then return the authenticated current receipt and requested records. Never select an orphan.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Repeat read allowed within frame/session limits.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Observation of durable facts, no repair or release.
NEGATIVE_TESTS=REC-QUERY; REL-ORPHAN; GEN-RECEIPT-LOSS; REL-POST-I-QUERY; REL-QUERY-HEAD-CHANGED; REL-JOINT-READ-FRESH; REL-QUERY-REPLY-LOSS; REL-SECOND-HELPER-BUSY
```

### 6.13a Same-session root reads and exact release read points

query_settlement is read-only and legal in the existing authenticated release session, including ACTIVE release phases RESTRICTED through SETTLED. It uses the already-held root lock and existing channel; it neither changes intent nor opens another helper. Current owner/G/session, authenticated sender, request sequence, exact expected_head_sha256 and all numerical bounds still apply. A read advances only the volatile request sequence, not RootControl, phase or head. It cannot resolve quarantine, reconcile a write, clear uncertainty, refresh an observation, reset a deadline or turn historical evidence into current authority. A durable close still permits only the final transport acknowledgement, not another application query.

The helper freshly reads actual E bytes for every query instead of returning a cached prior response. It verifies the actual current head and selected immutable objects/reachability under the held lock before returning. In release intent, release_id must equal the active transaction and envelope G/owner must be current. Null release_id resolves only to that current head's release ID. An expected-head mismatch returns head_conflict and blocks further progress; it must not silently substitute a newer head. It remains legal for separately authorized query/recovery sessions to inspect historical selections under their existing rules, but those results cannot meet a live release read requirement.

#### Post-I-restriction read without a GenServer dependency cycle

HostEvidence.Ledger.restrict_sync/3 remains a synchronous public function executed in the captured boundary process, with the existing context and RootRestrictionProof arguments. Its implementation is a wrapper around two private ledger messages and an intervening NativeClient read. The ledger GenServer must not hold a handler open while waiting for a query that only its blocked boundary caller can issue.

1. The wrapper validates its captured-boundary identity and sends private `{:restrict_write_sync, context, root_restriction_proof}`. The ledger checks the existing caller/epoch/proof/prior-history guards, constructs/writes the exact I restriction and namespace head, synchronizes DETS and rereads those keys. It returns an internal candidate containing the restriction digest and an opaque reference confirmation token. This internal response is not the public restriction success or a snapshot permit.
2. The token is a fresh Erlang reference bound in ledger memory to the captured owner monitor, G/epoch/release ID, candidate I digest and expected initial root head. It is not a wire record or a persisted authority. Ledger restart, owner death or conflicting revision invalidates it; the already-written restriction remains blocking until governed reconciliation. No runtime caller can supply or select a token.
3. Now running again in the captured boundary, the wrapper calls the proposed internal `HostEvidence.NativeClient.query_settlement_sync(namespace, expected_head_sha256, request)` with `{release_id: current_release_id, include_evidence: false}`. NativeClient resolves only its existing registered session for that namespace and captured boundary. It checks caller PID/monitor, wire owner epoch/G and session identity, serializes the next request on the existing native channel and performs the authenticated query. It accepts no executable path, arbitrary opcode, callback or replacement session. This function returns `{:ok, current_root_receipt, query_body}` or the existing typed error. The returned records must satisfy section 6.5c proof checks and the exact initial restriction head, not merely share a release ID.
4. The wrapper sends private `{:restrict_confirm_read, token, fresh_root_receipt, fresh_root_restriction_proof}`. The ledger rechecks captured owner/token and the exact current root/proof binding, rereads actual I restriction/head/history and requires unchanged canonical bytes/digest. It consumes the token and returns confirmation. Only then may the public wrapper return `{:ok, index_restriction_digest}`.
5. A failed or lost query/confirmation returns an error, discards the in-memory candidate and leaves durable I/E restrictions blocked. bind_snapshot cannot be sent on that path. Exact I reconstruction or a later confirmation attempt must follow existing same-owner/recovery rules with a fresh token and new root query; no automatic effect retry is introduced.

NativeClient is the existing planned host_evidence/native_client.ex component owned by the captured boundary. Its namespace registration captures that boundary and live port/session once at authenticated bootstrap. Every call verifies this ownership and current G/epoch; a name replacement or stale registration rejects. The wrapper executes the native query after the ledger has replied to its private write call, so no ledger process performs privileged I/O and no blocked GenServer must call back into its owner. The private messages have fixed atom tags and closed tuple shapes above, remain caller-guarded, and add no native opcode or persistent format. Every outer restrict_sync failure leaves the transaction restricted regardless of the private write's result.

#### Fresh completion-time joint reads

After ack_attempt_commit commits ATTEMPT_COMMITTED and I ATTEMPT_COMMITTED has been synchronized/reread, boundary retains namespace serialization and the same native session. Immediately before complete_release(record_completion), it performs:

1. query_settlement with the exact current head/release/G/owner and include_evidence=true. Validate the actual E receipt/object/provenance and scope. Record this head and query sequence locally.
2. Authoritatively reread I ATTEMPT_COMMITTED, full current R membership/revision vector and actual A release receipt through their existing guarded owners. Validate qualification, diagnostic/disclosure applicability, resource/evidence identity and no unresolved covered obligations. Cached API results do not count.
3. query_settlement again in the same session with the first query's exact head as expected head. Require equal head, phase, G/epoch/release and object/provenance identity. Recheck that no resource revision, event cursor/invalidation epoch, owner or profile changed across the read interval. No other native mutation or ledger write is allowed in this interval.
4. Construct a fresh JointRead with new read_id, that actual E head, the actual I/R/A records and current checked_monotonic_ns. Send complete_release(record_completion) as the next native application request, with that same expected head. The helper independently checks current E and the existing split-model commitments. Host attestation is not a claim that the helper parses DETS.

After root COMPLETED and I COMPLETED are synchronized and reread, repeat all four steps with a new pair of actual E queries and a different JointRead.read_id before complete_release(settle). Require E phase COMPLETED and I COMPLETED naming the exact root completion. The first JointRead, earlier query responses and initial restriction proof cannot be reused for settlement. If another event, write or state change intervenes, invalidate the read and deny completion; do not adjust its commitments in place. The existing age, helper deadline, frame and request-count budgets cover these added reads. Exhaustion blocks; it does not omit a read or extend a deadline.

On lost query response or partial/uncertain framing, no success-shaped JointRead or I confirmation is produced. Existing protocol failure rules stop further mutations. A later query requires actual lock acquisition and authenticated state inspection; old ACTIVE/INTERRUPTED observations cannot be resumed through a new helper. A root head changed contrary to expected serialization is a conflict requiring blocked reconciliation, not newest-wins acceptance. A second helper started while H1 holds the lock must return lock_busy; elapsed timeout never supplies an alternate read path. Read-only calls cannot clear a prior uncertain sync.

P08-INV-005/006 and P08-REL-001/004/005 require release_post_index_sync_query, release_query_head_changed, release_completion_joint_queries_fresh, release_query_reply_lost, release_second_helper_lock_busy and restrict_sync_no_owner_deadlock. T06 owns legal same-session query phases, exact expected-head checks, read-only root behavior and lock-contention controls. T11 owns private write/query/confirm ordering, caller/token failure and post-sync actual I/E checks with fixture-level native-client responses. T14 owns real native-session post-I reads, both completion-time query pairs, lost-response/event invalidation and the second-helper test. Fixture-level proof cannot qualify the native lock/channel. These tests must record actual operation order and durable E/I/R/A states; absence of any required read is failure, not a skipped green result. Native/privileged execution remains separately unauthorized.

### 6.14 `record_quarantine`

```text
OPERATION=record_quarantine
AUTHORIZED_CALLER=COMMON_AUTH; intent quarantine or current active intent
REQUIRED_SESSION_STATE=any legal non-corrupt phase
REQUEST_SCHEMA={record_id:Nonce,resource_ids:[P01ID],reason:QReason,evidence_id:?P01ID,evidence_sha256:?Digest,disclosure_record_sha256:?Digest}
RESPONSE_SCHEMA={quarantine_sha256:Digest,gate:"QUARANTINED",state:"block_reuse"}
AUTHORITY_GUARDS=Current attribution; supplied evidence must resolve if cited. A trusted owner may reduce authority without positive cleanup proof.
PERSISTED_IDENTITY=Publish immutable quarantine then root QUARANTINED; boundary syncs I/R. Recording failure still latches admission blocked.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Publish immutable quarantine then root QUARANTINED; boundary syncs I/R. Recording failure still latches admission blocked.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=Exact duplicate may return prior quarantine; conflicts reject.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Unresolved obligations remain blocked; never acknowledged away.
NEGATIVE_TESTS=QUA-RECORD-LOSS; DIA-KNOWN; QUA-FORGE
```

### 6.15 `resolve_quarantine`

```text
OPERATION=resolve_quarantine
AUTHORIZED_CALLER=COMMON_AUTH; intent quarantine
REQUIRED_SESSION_STATE=QUARANTINED; begin requires no pending resolution; retain/release require same-session pending reservation
REQUEST_SCHEMA={action:"begin",decision_id:Nonce,decision_sha256:Digest,quarantine_sha256:Digest} | {action:"retain",decision_id:Nonce,decision_sha256:Digest,pending_resolution_sha256:Digest,reason:QReason} | {action:"release",decision_id:Nonce,decision_sha256:Digest,pending_resolution_sha256:Digest,current_resource:ResourceCommitment,fresh_evidence_id:P01ID,fresh_evidence_sha256:Digest}
RESPONSE_SCHEMA={action:"begin",decision_id:Nonce,decision_sha256:Digest,pending_resolution_sha256:Digest,disposition:"operator_resolution_pending"} | {action:"retain",decision_id:Nonce,decision_sha256:Digest,pending_resolution_sha256:Digest,resolution_sha256:Digest,disposition:"remains_quarantined"} | {action:"release",decision_id:Nonce,decision_sha256:Digest,pending_resolution_sha256:Digest,resolution_sha256:Digest,disposition:"released_for_new_authorization"}
AUTHORITY_GUARDS=Begin validates the exact unexpired section 6.18 handoff and post-close head, fixed root registry, approved issuer/provisioning, unrevoked/unspent decision and exact namespace/G/owner/current quarantine/initial head. It reserves that one-use decision and creates PendingResolution. Retain needs that exact reservation, still-valid unrevoked decision and a quarantine reason, not fresh evidence. Release additionally requires ReleaseResolutionDecision, exact current R vector and qualified fresh evidence equal to the decision, no unresolved covered obligation, unchanged same session/G/epoch and unrevoked authority. Outer expected_head always matches the current head; decision.expected_root_head is checked against PendingResolution.initial_root_head after begin.
PERSISTED_IDENTITY=Begin publishes PendingResolution and pending QuarantineRecord, sets RootControl.pending_resolution_sha256, gate QUARANTINED. R stays blocked; no resource verification is implied. Terminal actions publish exact result, consume the reserved decision in the same root head transition, clear pending pointer and retain the historical pending record.
ORDERED_SIDE_EFFECTS=COMMON publication order for begin, then host I pending mirror; no R authority reduction at begin. Retain commits remains_quarantined and gate QUARANTINED. Release commits released_for_new_authorization and gate CLOSED; host I/R terminal mirrors must agree before any future consideration. No A change or automatic settlement.
FAILURE_RESULTS=COMMON_FAILURE. Release proof failure returns an error and leaves pending quarantine intact; it never returns a success-shaped release or implicit retain. Caller may explicitly invoke retain with cleanup_unverified while the same reserved decision/session remains valid. Missing/revoked authority cannot release; record_quarantine may always strengthen/retain the block.
RETRY_POLICY=Same decision may have at most one begin reservation and one terminal result. Duplicate begin, changed variant or second terminal action rejects; query existing recorded result instead. Exact logical result reads do not re-spend the decision. No automatic replay after uncertain persistence.
RESTART_INTERPRETATION=Interrupted/expired/ended pending session cannot finish release in another session. Reservation is burned and conservatively abandoned to remains_quarantined under authenticated recovery or record_quarantine; all future release requires a new decision. Same-G owner restart still invalidates the old owner epoch.
TERMINAL_MEANING=Begin is explicitly nonterminal governance processing only. Retain is terminal denial without proof. Release is terminal permission to consider a separately authorized future action, never grant/rearm/dispatch.
NEGATIVE_TESTS=QUA-BEGIN-NO-OUTCOME; QUA-RETAIN-NO-PROOF; QUA-RETAIN-REJECT-EVIDENCE-FIELDS; QUA-RELEASE-RETAINING-DECISION; QUA-RELEASE-MISSING-PROOF; QUA-PENDING-REVOKE; QUA-PENDING-RESTART; QUA-DOUBLE-FINALIZE; QUA-DECISION; QUA-REPLAY; DIA-HISTORY
```

### 6.16 `close_session`

```text
OPERATION=close_session
AUTHORIZED_CALLER=COMMON_AUTH; intent current intent
REQUIRED_SESSION_STATE=any legal phase with known head
REQUEST_SCHEMA=CloseRequest | HandoffCloseRequest
# CloseRequest={expected_final_head_sha256:Digest,outcome:"QUIESCENT"|"ABANDONED"}
# HandoffCloseRequest={expected_final_head_sha256:Digest,outcome:"AUTHORITY_HANDOFF",purpose:"RESOLUTION"|"QUARANTINE_EVIDENCE",resource_set_sha256:Digest,resource_snapshot_sha256:Digest}
RESPONSE_SCHEMA={final_head_sha256:Digest,session_closed:true,gate:"CLOSED"|"QUARANTINED"|"SETTLED",authority_handoff:?AuthorityHandoff}
AUTHORITY_GUARDS=expected_final_head_sha256 names the pre-close current head, not the future close-record digest. Response final_head_sha256 names the newly published close head. QUIESCENT cannot make an unresolved transaction clean; ABANDONED retains blocked obligations. AUTHORITY_HANDOFF requires terminal QUARANTINED with no pending resolution or incomplete acquisition, exact current registered resource commitments and the current boundary incarnation; section 6.18 applies. Other variants return authority_handoff=null.
PERSISTED_IDENTITY=Synchronize terminal session state first, then reply and await bounded transport ack/deadline; close mutation descriptors and lock last. Section 6.16a defines response-loss semantics. Never transfer custody.
ORDERED_SIDE_EFFECTS=COMMON root publication order; Synchronize terminal session state first, then reply and await bounded transport ack/deadline; close mutation descriptors and lock last. Section 6.16a defines response-loss semantics. Never transfer custody.
FAILURE_RESULTS=COMMON_FAILURE; no positive result on guard failure
RETRY_POLICY=No further frame accepted. Missing final response treated uncertain and queried later.
RESTART_INTERPRETATION=COMMON_RESTART; old facts remain historical
TERMINAL_MEANING=Durable closure commitment, independent of transport acknowledgement; actual lock release must still be observed. No process/resource-clean implication.
NEGATIVE_TESTS=INV-CLOSE; INV-CLIENT-DEATH; GEN-H1-H2
```

### 6.16a Durable closure versus transport completion

QUIESCENT means that the root helper has synchronized a closure commitment under the current root head and will perform no further application mutation in that invocation. It does not mean that the client received a response, acknowledged it, the helper exited or the kernel lock was released. The close acknowledgement is exclusively a bounded transport teardown step. It is never a durable-state transition guard. The existing transport acknowledgement remains outside the 15 application opcodes.

The helper validates the close request and current client, publishes/synchronizes any handoff and terminal control/head, then enters a no-more-application-writes state. It sends the response and accepts only the exact final-head acknowledgement until the existing one-second deadline. On acknowledgement, EOF, client death or deadline it closes observation/mutation descriptors and the lock last, with no further root write. A missing acknowledgement cannot erase QUIESCENT, abandon a committed handoff or reopen the invocation. If the helper remains unresponsive while holding the lock, new helpers and installer remain blocked; no deadline proves lock release or permits stealing it.

After lost response or acknowledgement, the same live boundary may obtain a fresh authenticated lock and read-only query. The installer independently obtains that lock and rereads the actual synchronized head/handoff. A valid committed QUIESCENT head is eligible for the existing section 6.18 provisioning/adoption rules without proof of an acknowledgement. All G/owner/head/scope/expiry checks still apply. Actual exclusive lock acquisition proves that the previous lock description no longer excludes the new holder; the durable state alone does not. A new boundary epoch after client/BEAM death cannot consume the old handoff and must recover closed. No transport acknowledgement transfers process custody or restores an observation's validity.

| Failure point | Actual durable possibilities | Required handling |
|---|---|---|
| Before close-head synchronization | Old ACTIVE/INTERRUPTED head, or closure published with uncertain durability | No handoff/adoption from an unsynchronized head. Existing root recovery validates and synchronizes under lock or remains blocked. |
| After QUIESCENT head sync, before response | QUIESCENT/handoff committed; client has no receipt | Keep durable closure. Release lock only by actual teardown/death; query/reread after acquisition, never replay close blindly. |
| Response delivered, acknowledgement absent or client dies | Same committed QUIESCENT head | Bounded teardown without mutation; installer checks actual head/lock; new boundary cannot reuse epoch. |
| Ack received, before lock close, or helper paused | Same committed QUIESCENT head, old lock may remain held | Installer/H2 denied until actual lock acquisition succeeds; acknowledgement is not exit proof. |
| Host crash after close commitment | Durable closed head if synchronization succeeded | Validate actual E history and current boot/G/owner; old handoff cannot cross changed boot or epoch. No ack reconstruction. |

P08-INV-004/006 and P08-QUA-002 require close_quiescent_before_ack_crash, close_lost_response_query, close_client_death_after_commit and close_ack_lock_still_held. T06 owns native state/write/teardown assertions, T05 transport controls, and T15 the actual installer/handoff adoption after lock release. Test a pause immediately after head sync with no response or acknowledgement, and assert that current QUIESCENT survives while the old lock still blocks the installer. Then verify correct same-owner adoption and changed-owner denial. Privileged proof remains separately authorized.

### 6.17 Quarantine observation and denied authority

A quarantine acquisition uses release intent with root decision permitting evidence acquisition only. `restrict_release` may operate over unresolved quarantine only in that narrow evidence-only mode: the immutable restriction records the existing quarantine, and prepare_release/ack_attempt_commit/complete_release(settle) are forbidden. Fresh observations may document absence while the quarantine remains. `resolve_quarantine` then runs in a later quarantine session using a newly materialized decision bound to the resulting current head. Acquisition permission and resolution permission are separate root-provisioned decisions; neither is implied by request intent. This prevents a deadlock in which fresh evidence is required to resolve quarantine but observation is itself prohibited.

ResolutionDecision permits begin processing plus its terminal disposition; it does not itself permit evidence acquisition. A separate root manifest authorization for evidence-only acquisition is required and is the closed record `{schema:"G2-QUARANTINE-ACQUISITION-2",contract_revision:"P08-SPEC-0.7",authorization_id:Nonce,namespace:P01ID,host_id:P01ID,generation:Generation,owner_epoch:Nonce,quarantine_sha256:Digest,resource_set_sha256:Digest,source_decision_sha256:Digest,installer_identity_sha256:Digest,expected_root_head_sha256:Digest,handoff_sha256:Digest,expires_monotonic_ns:U64,one_use:true}`. Its root registry uses the same trusted ownership and at-most-once replay rule, with the section 6.18 epoch/head handoff and expiry checks. Unlike two-step resolution, evidence-only acquisition is reserved and consumed directly by restrict_release, without a PendingResolution; the root restriction records that consumption. It never enters AttemptLedger. Its identity is bound by restrict_release.quarantine_acquisition_sha256 in the restriction operation commitment. An evidence-only acquisition may read an already released historical A receipt instead of a currently requested fence; before_attempt_fence_sha256 is then H(ATTEMPT_RECEIPT, that exact historical receipt), selected unambiguously by the nonnull quarantine acquisition authorization. It cannot change A, bind a new attempt or continue to preparation/settlement. The root registry must contain exactly one matching available authorization; zero/multiple matches reject. This additional record grants no runtime execution.

#### 6.17a Evidence-only terminal protocol and recovery

QUARANTINE_EVIDENCE is a closed branch of the existing release vocabulary, not a releasing transaction. restrict_release consumes the exact provisioned acquisition authorization, records purpose=QUARANTINE_EVIDENCE and retained_quarantine_sha256 in ReleaseRecord, and keeps gate QUARANTINED while phase advances RESTRICTED, SNAPSHOT_BOUND and OBSERVED. RootControl.quarantine_sha256 remains the original blocking quarantine. Its gate never becomes CLOSED or SETTLED because of acquisition. A normal RELEASE has purpose=RELEASE, null retained quarantine and gate CLOSED during those phases.

I writes IndexRestriction before bind_snapshot. bind_snapshot verifies that receipt and the current immutable restriction. observe_fence only observes; it cannot promote R. observe_absence constructs EvidenceObject.purpose=QUARANTINE_EVIDENCE. Its post_snapshot equals pre_snapshot byte-for-byte and self_bindings=[], because this branch makes no R verification transition. Qualified observations may report scoped absence but never imply R's persisted verified state. Evidence cannot be supplied to commit_gate2_release_sync or the ordinary release verifier. A later governed resolution may consider it only after independently checking freshness, qualified scope and the actual unchanged/current resource vector; it cannot waive missing owner cleanup proof.

Under the same lock, observe_absence first synchronizes/publishes the evidence object and root publication provenance. It then publishes/synchronizes QuarantineEvidenceRecord binding exact object, authorization, retained quarantine, G/epoch and verdict. Finally it publishes/synchronizes RootControl with phase QUARANTINED, gate QUARANTINED, evidence set to the observed object and quarantine_evidence_sha256 set to H(QUARANTINE_EVIDENCE, record). quarantine_sha256 is unchanged, pending_resolution_sha256 is null and no settlement exists. Only that last reachable root head is the terminal evidence-acquisition commitment. The response carries that terminal root receipt and the exact quarantine_evidence record. VERIFIED means scoped observation only; UNVERIFIED retains reason and cannot support release. No diagnostics failure may be relabeled VERIFIED.

The captured I owner then persists QuarantineEvidenceIndex through the terminal branch of advance_sync/4, whose next-record union is IndexReceipt | QuarantineEvidenceIndex. It synchronizes and rereads it against the terminal root receipt and original restriction digest. R and A remain byte-for-byte unchanged. The branch never calls verify_fence_sync, verify_snapshot_sync, ack_resource_commit, prepare_release, ack_attempt_commit or either complete_release variant. These operations explicitly reject purpose=QUARANTINE_EVIDENCE, irrespective of phase or request shape. After actual E/I agreement, close_session may quiesce or create a RESOLUTION handoff. A later fresh quarantine-intent session enters resolve_quarantine(begin) from terminal QUARANTINED. It needs a newly provisioned decision bound to that final post-close/handoff head. Collecting evidence never clears quarantine.

| Failure boundary | Durable possibilities and authority | Recovery |
|---|---|---|
| Before restriction sync/response | Authorization unconsumed, or root restriction consumed despite lost response | Lock and reread. Never blindly replay; consumed acquisition cannot be reused. Quarantine remains. |
| After root restriction, before I restriction sync | I absent or exact restriction; E already quarantined | Same-owner exact I restriction reconstruction requires reachable root restriction. Restart conservatively invalidates acquisition. No snapshot before I reread. |
| During snapshot/fence | Root at preceding or new phase; I restricted; R/A unchanged | A current same-session exact retry only where existing operation permits. Owner restart invalidates all observations and retains quarantine. |
| During object/file/directory publication | Object absent, temporary, orphan, or provenance-published, but no terminal record/head | No current resolution proof. Retain object as historical. Close/recovery records interrupted acquisition, preserves quarantine and consumes authorization permanently. |
| After terminal record sync, before terminal head sync | Old root phase or exact terminal head, including uncertain write | Reread under lock. Only a reachable terminal head authorizes terminal I reconstruction; otherwise interrupted acquisition. |
| Terminal E, I absent or sync uncertain | I restriction or exact terminal index; R/A unchanged | Read repair only to exact QuarantineEvidenceIndex from reachable E, same generation, captured owner and validated original restriction. If its restriction/history is missing or corrupt, maintenance required; no fabricated predecessor. |
| E/I terminal, close/handoff or reply interrupted | Final head may remain terminal acquisition or quiescent/handoff successor | Query exact chain. No runtime authority results. New owner/generation treats evidence as historical and needs new current proof/decision. |
| Repeated restart, stale helper or conflict | Lock may still be held; prior authorization spent; quarantine persists | Never steal lock or reuse authorization. Closed recovery under section 4 after ownership is resolved; conflicting root/index bytes require maintenance. |

Tests quarantine_evidence_terminal, quarantine_evidence_no_resource_mutation, quarantine_evidence_interrupted_publication, quarantine_evidence_index_repair and quarantine_evidence_later_resolution must assert the exact root gate/phase, retained quarantine/object identities, I row and unchanged R/A bytes at every boundary, for both observation verdicts. P08-T14 owns terminal/persistence/admission tests including quarantine_evidence_index_repair against the real terminal producer. T11 owns only quarantine_evidence_index_repair_fixture using declared static terminal fixtures, which cannot establish integrated proof. T15 owns later resolution entry. These extend P08-REL-001/004/005/006 and P08-QUA-001/002; they add no requirement or opcode.

### 6.18 Existing-epoch authority handoff

P08 wire owner_epoch is a fresh nonce allocated once by the captured boundary incarnation before recovery. It survives orderly one-shot helper sessions while that boundary remains alive; session_id and authenticated native-client incarnation are fresh per invocation. Boundary restart always allocates another epoch and performs closed recovery. This does not replace P01's internal owner_epoch tuple `{owner_pid, generation}`. The wire nonce is an additional binding; both checks apply. A generation change independently invalidates prior authorizations even if the boundary survives. No prior native pidfd or session authority survives close.

The exact sequence is:

1. The existing boundary completes generation recovery and any interrupted acquisition conservatively. It has a known current quarantine and exact R snapshot. No future epoch is selected by the installer.
2. In the current authenticated helper session under the root lock, it sends close_session HandoffCloseRequest with the current pre-close head, purpose and exact resource commitments. Helper validates terminal quarantine, current generation/epoch, no pending resolution or acquisition and current qualified registration.
3. Helper constructs AuthorityHandoff with a fresh nonce, the existing epoch and source head. Its candidate lifetime is 300 seconds measured by CLOCK_MONOTONIC within the same boot. This is an upper bound on authority use, not a lock timeout; its production value requires numerical-profile approval. It publishes/synchronizes the handoff, then a QUIESCENT RootControl referencing its digest. Root gate/phase remain QUARANTINED. Response names this final head. Helper waits for the bounded close acknowledgement/deadline and closes the lock last. QUIESCENT is already durable; lost response/acknowledgement follows section 6.16a.
4. Boundary retains the receipt while remaining closed and alive. A separately authorized root installer independently acquires that same pinned lock, rereads the current head, handoff, root quarantine, registrations and source human decision. It requires exact final-head/handoff/G/epoch/scope match and unexpired handoff. It obtains owner_epoch from root bytes, not from an operator guess. The human decision must authorize that exact handoff/scope or an exact attested projection of it; a broad Plane ticket is insufficient.
5. Installer creates exactly one immutable matching ResolutionDecision or acquisition authorization with the handoff digest, current final head and expiry no later than the handoff. It writes/syncs the object, publishes no-replace and synchronizes the registry directory. That registry is the existing root attestation registry; provisioning never advances namespace RootControl or chooses an epoch. A duplicate identical object is idempotent only after complete byte reread. Conflicting ID or multiple usable matches block. Partial files or unsynchronized enrollment cannot authorize use.
6. Installer releases the lock. The same live boundary starts a fresh one-shot helper/client session with the same wire epoch and a new session_id. Hello authenticates and reads the head; hello does not write or consume the handoff. COMMON_AUTH permits adoption of a QUIESCENT prior session only when owner_epoch/G and exact expected head match. The first authorized mutation writes the new session_id and ACTIVE state together with its operation record. It never treats an ACTIVE or INTERRUPTED prior session as a valid handoff. Helper independently resolves the pinned registry. The first mutating operation must be resolve_quarantine(begin) or restrict_release with the matching acquisition authorization. Its outer expected head is the post-close head. It validates purpose, expiry, boot, exact G/epoch/quarantine/resource scope and current head, then durably reserves/consumes the decision under the existing operation ordering before acknowledging success. That root mutation invalidates the handoff for all other uses.
7. Resolution retains the existing begin/retain/release reservation rules. Acquisition consumes its authorization directly. The source handoff is retained as historical provenance. Obtaining new authority requires another terminal close/handoff and a new human-approved provisioning artifact; nothing is automatically renewed.

A harmless read-only query or failed pre-authentication startup does not change the head or consume authority. A failed native session with an unresolved live helper cannot be replaced while that helper holds the lock. After its death, only authenticated reread can determine whether consumption persisted. If the boundary died, the new epoch cannot consume the old object even before generation advancement; recovery must first close/invalidate the old root owner. Expired handoffs and expired decisions stay historical and cannot be refreshed in place. Installer failure before enrollment leaves no usable authority; failure after uncertain directory sync requires the installer to lock and reread exact bytes before declaring provisioning complete. No host self-enrollment is allowed. A changed head, generation, installation profile, quarantine or resource revision requires a fresh handoff, even when the decision has not been consumed.

The handoff transfers a bounded administrative provisioning opportunity, not lock custody or runtime authority. The installer never waits for a live helper while holding another namespace lock. Lock contention returns a typed blocked result under the existing deadline, leaves the root head unchanged and never steals or kills the owner. Repeated restart with H1 alive remains blocked. Source human approval may be prepared earlier, but exact root-scoped materialization occurs only after the recorded handoff.

Required controls under P08-INV-002/006, P08-QUA-002/003 and P08-GEN-006 are epoch_handoff_roundtrip, handoff_head_changed, handoff_wrong_purpose, handoff_boundary_restart, handoff_expired, handoff_installer_partial_sync, handoff_startup_failure, handoff_live_old_helper, and handoff_replayed_consumption. Assert root and I remain quarantined on every failure; no R/A change is permitted. T05/T06 implement transport/root custody cases; T15 implements issuer, reservation and installer fixture cases. These are proposed tests, not observed passes.

## 7. Release authority, writers and durability

### 7.1 Store contract

| Store | Trusted owner / run-as | Access and writers/readers | Authorization and durability | Restart/failure |
|---|---|---|---|---|
| Installation, manifests, decisions | Root administrative authority | Root immutable files; installer only; helper reads | Explicit human provisioning decision; pinned ancestry/digests; file/directory sync | Missing or modified profile blocks, never re-enroll automatically |
| E objects and root control | Qualified root helper | Root 0700 directories, 0600 objects; helper sole runtime writer/reader | Lock, current client, head/G/session checks; object/head sync | Corrupt/unavailable E blocks all admission |
| I evidence index/mirror | Captured boundary, trusted host UID | Private DETS; only captured boundary writes; verifier reads through owner | GenServer.from PID, registered name, owner epoch/monitor; DETS sync+reread | Cannot override root; missing/corrupt index denies |
| R resources | Captured boundary and staged recovery owner, host UID | Private DETS; existing ownership plus exact verification APIs | Expected revision/current G and verified native provenance; sync+reread | Pending/corrupt/uncertain rows block; staged repair only section 4 |
| A attempt binding/fence | Existing ledger owner and boundary-only commit, host UID | Existing schema-2 storage; generic writers preserve Gate 2 history | Registered boundary self-check for commit; exact preparation and R proof; durable write+reread | Released receipt alone never admits |
| Host journal | Captured boundary, host UID | Private immutable file; no runtime access | Root plan binds raw digest; safe exact decode; file+directory sync | Missing/changed journal blocks partial-row repair |

`HostEvidence.Ledger.restrict_sync/3`, `advance_sync/4`, `settlement_sync/3` accept only the captured boundary, not caller-provided owner IDs. Initial restrict_sync requests carry current owner epoch and RootRestrictionProof under section 6.5c; other internal requests carry the specified root receipt and are checked against independently reread E. A settlement mirror is non-authoritative. R verification updates require same captured owner and exact revisions. A `commit_gate2_release_sync/5` runs only in the registered boundary process and checks current binding, preparation, verified R proof and exact identity. Direct calls, forged shape-valid structs and name replacement without epoch do not authorize.

### 7.1a Exact host interfaces and A persisted release representation

New functions are proposed, not claims about accepted P01. Their return errors are typed boundary errors with protocol failure details retained only as nonsecret reason codes.

```text
HostEvidence.Ledger.restrict_sync(server, context, root_restriction_proof)
  -> {:ok, index_restriction_digest} | {:error, reason}
  context = {namespace, generation, owner_epoch, release_id, purpose, retained_quarantine_sha256, previous_index_sha256} as an exact internal record; section 7.1b defines its persisted representation.
HostEvidence.Ledger.advance_sync(server, expected_index_digest, next_index_receipt, root_receipt)
  -> {:ok, IndexReceipt} | {:error, reason}
HostEvidence.Ledger.settlement_sync(server, root_settlement_receipt, actual_joint_read)
  -> :ok | {:error, reason}
AttemptResourceLedger.verify_fence_sync(server, resource_id, expected_revision, FenceProof)
  -> {:ok, AttemptResource} | {:error, reason}
AttemptResourceLedger.verify_snapshot_sync(server, pre_snapshot, post_snapshot, verified_evidence)
  -> {:ok, ResourceCommitment} | {:error, reason}
AttemptLedger.commit_gate2_release_sync(ledger, issue_id, runtime_identity, cleanup_ref, PreparedReleaseProof)
  -> {:ok, AttemptReceipt} | {:error, reason}
```

`verified_evidence` is an internal verifier result containing the exact EvidenceObject, independently checked root publication receipt and CleanupEvidenceRefWire. The boundary constructs it; no public API accepts a caller assertion that verification succeeded. FenceProof requires root_receipt.record.observation_sha256 equal H(OBSERVATION, its exact observation), native verified_fenced status, matching resource/revision/G/owner scope and qualified manifest. An authenticated response digest alone without reachable root commitment is insufficient. The registered boundary caller is checked before accepting any such internal value. All receipt checks compare actual stored objects/revisions and current root provenance.

A retains its schema-2 top-level key set and exact boundary_binding. The new P08-only release replaces authority_fence with exactly this stored atom-keyed map, after boundary checks and one current-record persistence/sync:

```elixir
%{
  state: :released,
  runtime_attempt: exact_existing_identity,
  route_fingerprint: exact_existing_route_or_nil,
  gate2_fence: %{
    reference: exact_existing_grant_ref,
    status: :released,
    requested_reason: existing_reason_or_nil,
    release_receipt: exact_attempt_receipt
  }
}
```

`exact_attempt_receipt` is the fixed AttemptReceipt record converted through a known atom-key mapping; no dynamic atoms. The receipt's released=true says the fence commit occurred, not that I/E completed. in_flight remains unchanged at this commit. Any later clear requires current joint settlement and cannot restore eligibility in P08. Existing requested Gate 2 maps remain byte/shape compatible and are not rewritten at startup. Generic legacy records are unchanged. This explicit new nested P08 state requires strengthened Gate 2 released validators; the existing broad legacy released-fence predicate is insufficient for a Gate 2 binding. Every Gate 2 released record must retain the exact receipt, identity, namespace and binding. A record with this state but no receipt is invalid even if a legacy released predicate would accept it. Rollback to a binary that cannot validate new state is blocked, never a downgrade path.

The boundary-only writer compares current requested fence and binding, then writes once. A second call with the exact existing receipt may return that receipt only after authoritative reread; a different release/preparation cannot overwrite it. That read-idempotency does not allow automatic release retry after an ambiguous result.

### 7.1b Initial I restriction and transition contract

HostEvidence.Ledger.restrict_sync/3 retains its arity and returns {:ok, index_restriction_digest} only after synchronization and authoritative reread. The exact IndexRestriction in section 5.2b is the initial I row, not an INDEXED receipt. Context fields namespace, generation, owner_epoch and release_id have their named P01ID/Generation/Nonce types; purpose is RELEASE|QUARANTINE_EVIDENCE; retained_quarantine_sha256 and previous_index_sha256 are nullable Digest. The registered owner constructs context from independently read E/R/A, not a caller's authority assertion. The ledger obtains the exact immutable ReleaseRecord and root receipts from RootRestrictionProof delivered under section 6.5c, derives all other fields from that verified reachable root restriction, verifies their digests and checks equality of namespace/G/epoch/release/resource set/purpose/quarantine.

The private DETS key is {:p08_release, namespace, release_id}; its value is exactly {:p08_index_restriction_v3, canonical_bytes, index_restriction_digest}. Canonical bytes encode IndexRestriction; the digest is H(INDEX_RESTRICTION, bytes). Stored digest and re-encoded decoded bytes must agree. Later normal values are {:p08_index_receipt_v3, canonical_bytes, H(INDEX, bytes)} and terminal evidence-only values are {:p08_quarantine_evidence_index_v3, canonical_bytes, H(QUARANTINE_EVIDENCE_INDEX, bytes)}. The ledger keeps the exact immutable restriction-history wrapper defined in section 6.5c under {:p08_restriction_history, namespace, release_id}; it writes/syncs that history before advancing the active row. Any history/active mismatch blocks. These are I-only tags, not DETS schema changes to A or R.

previous_index_sha256 is null only for an independently verified first transaction in the registered namespace. Otherwise it names the exact prior terminal I record reread by the captured owner. An unresolved previous restriction, pending recovery, unsettled release, corrupt/missing history or stale generation cannot be overwritten with a new release ID. A quarantined terminal evidence-acquisition index may precede another explicitly authorized quarantine acquisition/resolution, but cannot enable ordinary admission or new attempt reuse. The current namespace head key {:p08_index_head, namespace} stores the active record digest. History and head disagreements always deny admission. No multi-key DETS atomicity is assumed.

Ordering is validate captured caller/current E and prior I; construct exact bytes; insert restriction active row and namespace head; DETS.sync; reread both plus the current root restriction through the same-session query sequence in section 6.13a before returning. restrict_sync/3 is a captured-boundary wrapper with separate private write and confirmation calls, not a ledger handler waiting on a blocked boundary. A crash may persist neither key, one key or both. Missing keys can be reconstructed only from the exact reachable root restriction plus verified prior terminal history and captured recovery authority; conflicting keys, unavailable history or corrupt bytes require maintenance. An uncertain sync produces no receipt. A logical retry is idempotent only for identical release ID, namespace/G/epoch/purpose/root commitments and previous index; it must reread/sync before returning the same digest. Different bytes under the same ID reject. An older G/owner is historical and cannot become current by rehashing.

bind_snapshot now requires IndexRestrictionReceipt in its closed request. Root validates record canonical bytes/hash and exact reachable restriction head/ReleaseRecord, registered namespace/G/epoch/purpose/resource set and current lock/session before snapshot acquisition. It trusts the captured host owner to attest I synchronization within the declared split TCB; it does not pretend to parse DETS. Boundary independently rereads actual I immediately before sending that receipt. Root-only receipt forgery by an arbitrary caller is insufficient because native caller authentication and captured boundary rights both apply.

For RELEASE, first advance_sync consumes expected_index_digest=index_restriction_digest and next IndexReceipt.phase=INDEXED with the same index_restriction_sha256, object and current publication proof. Subsequent normal phases preserve index_restriction_sha256 and existing ordering. For QUARANTINE_EVIDENCE, the only allowed advance is directly from the restriction to QuarantineEvidenceIndex against terminal root quarantine-evidence provenance; it never produces a normal INDEXED/RESOURCE_VERIFIED receipt. Every advance inserts/syncs immutable predecessor history before active row/head replacement, then syncs/rereads. Any partial result remains denied until exact E/history-based reconciliation; a successful DETS return alone proves no cross-store agreement. settlement_sync accepts only the ordinary RELEASE branch with actual joint reread.

Admission readers require complete E/I/R/A agreement under section 7.2. IndexRestriction, missing restriction history, partial head, stale row, evidence-only terminal row and uncertain sync all return blocked. No generated snapshot or API-shaped receipt can bypass this check. Tests index_restricted_first_record, index_restriction_sync_loss, index_restriction_partial_head, index_restriction_replay, index_restriction_conflict, index_restriction_stale_generation and bind_snapshot_without_restriction exercise both durable outcomes around each write/sync. P08-T11 owns the I tests; T14 owns admission denial and T06 owns native bind_snapshot rejection. They extend P08-REL-001/004/005 and P08-EVD-002.

### 7.2 Release ordering and lifecycle

Boundary serializes namespace, acquires authenticated root lock and validates E/I/R/A. Root restricts; I restriction syncs; boundary queries actual E in that same release session and confirms actual I under section 6.13a; snapshot binds; fence/absence observe; immutable object publishes and root provenance syncs; I indexes; R verified update syncs and is reread; **ack_resource_commit precedes prepare_release**; preparation binds expected A projection; boundary commits A; rereads A; ack_attempt_commit; first complete_release records completion after actual joint reread; I COMPLETED syncs; second complete_release settles after a fresh joint reread; close_session records quiescence.

Resource verification transitions are only FENCING→FENCED with current qualified writer proof, or DESTROYING→ABSENT_VERIFIED with complete absence proof and immutable indexed evidence. P08 never initiates destruction or allocation. A writer-fence-only workflow may persist FENCED through proposed `verify_fence_sync/4` using the native fence observation/root provenance, then close the transaction blocked without A release. That row change invalidates its old snapshot. A later destruction/absence workflow starts a new snapshot and transaction after the external owner acts. `verify_snapshot_sync/4` handles exact absence revision vectors and current object self-link normalization. Production P01 reservations lacking allocation history cannot be promoted into verified production cleanup. Test seeding of future-owner states is fixture-only and cannot be configured in production.

The release lifecycle owner is boundary plus root E. RESTRICTED/SNAPSHOT_BOUND/OBSERVED/EVIDENCE_PUBLISHED/RESOURCE_VERIFIED/PREPARED/ATTEMPT_COMMITTED/COMPLETED deny admission. SETTLED means only exact resource/fence transaction agreement. An interruption becomes closed/quarantined. No automatic release completion occurs across owner restart. A released old A receipt remains historical; fresh governed reconciliation is required and cannot rearm lineage.

### 7.3 Exhaustive release persistence matrix

At every below boundary inject both old and new durable outcomes after an uncertain write, plus partial/corrupt representation. No API return establishes agreement. Recovery owner reads actual E chain/head/object, I, full R vector and A receipt under lock. Same-owner read repair may repair exact non-authoritative mirrors; owner restart requires fresh closed generation and retains unresolved release quarantine.

| Crash boundary | Possible E/I/R/A result | Admission guard | Allowed recovery / terminal |
|---|---|---|---|
| Before restriction | Prior stores | No new current proof; serialization closed | Fresh read only |
| Restriction record write/sync | Old head, partial/orphan record | No committed transaction proof | Validate head, orphan historical |
| Restriction publication/directory sync | Object missing/present, old head | Object alone never gate authority | Retry exact publication only after reread |
| Restriction head rename/directory sync | Old/new E, I old | Uncertain outcome closes boundary | Root reread; missing commitment denies |
| I restriction write/sync | E restricted, I old/new | E denies independently | Repair exact mirror |
| Snapshot acquisition/binding | Incomplete or bound snapshot | No complete current observation | New acquisition after invalidation |
| Fence/absence observation | Partial/stale or complete | Missing coverage denies | Fresh observation, no blind replay |
| Evidence temporary write/sync | Missing/partial/full temp | Temp is not published authority | Historical staging only |
| Evidence no-replace rename/directory sync | Object absent/present | E completion absent | Verify object and root provenance |
| Publication control/head sync | Object valid, E old/new | Root/index agreement required | Orphan retained or exact provenance confirmed |
| I index write/sync | I absent/old/new | Missing index denies despite E object | Exact mirror repair or quarantine |
| R each row write before sync | Old/new/mixed R, A fenced | E not settled and A fenced | Exact transaction comparison; no arbitrary overwrite |
| R sync before reread | R may persist but inaccessible | API success insufficient | Validated reopen or block |
| Root resource ack sync | R verified, E published/acknowledged | No prepare/A release until ack confirmed | Root reread |
| Preparation write/publication/head sync | E before/prepared, A fenced | No A commit from uncertain preparation | Reread exact preparation |
| A write/sync | A fenced/released/invalid, E prepared | E completion absent | Authoritative A reread; no blind second release |
| A response lost/root ack uncertain | A released, E prepared/attempt committed | E/I settlement absent | Exact same live-owner reconciliation or restart quarantine |
| Completion record/head sync | E attempt committed/completed, I earlier | COMPLETED is not SETTLED | Exact current reread |
| I completion write/sync | E completed, I old/new | Second completion requires exact I completed | Mirror repair only |
| Final settlement write/head/directory sync | E completed/settled | Uncertain response unusable | Query and joint actual reread |
| Close record/response lost | E may settled but ACTIVE/quiescent uncertain | Admission requires quiescence/current owner | Query; restart invalidates old authority |
| Any corruption/missing store | Any readable subset | No empty-default/fallback | Block/maintenance; retain evidence |
| Stale G, reused release ID, conflicting revision | Inconsistent stores | Exact identity equality fails | Quarantine; no newest-wins selection |
| Concurrent dispatch or legacy clear | Transaction unresolved | Common guard and history reject | Denied, no automatic rearm |

### 7.4 Admission proof and source readers

All future admission/reuse readers must require accepted installation/numerical/coverage profiles, current owner/G, valid quiescent E SETTLED with no pending proposal/plan/release, independently verified exact object and I completion, exact R revisions/current G, exact A preparation/release receipt, resolved applicable quarantine/disclosure and preserved Gate 2 binding/history. This predicate is read under boundary namespace serialization; any revision/event gap/restart invalidates the result. It is not a durable permit. P08 adds unconditional dormant/incomplete dispatch denial even if it succeeds.

Guard Orchestrator dispatch_issue/2,/3,/4, dispatch_issue_from_provider/4, attempt_boundary_dispatch_decision/2, begin_durable_attempt/3, begin_checked_durable_attempt/3, active/provider/final/routable retry paths, restore_eligible_work_item_after_clean_release/2, release_runtime_fence_after_task_down/3 before disabled/suspension shortcuts and clear_attempt_in_flight/2. Also audit stale-in-flight reconciliation, release_terminal_pending_fence, clear_reconciled_in_flight_record, clear_resolved_in_flight_block, release_plane_attempt_ledger_recovery_blocks and release_resolved_suspension_authority. Audit every call site of A put/2, begin_attempt/2,/3, bind_runtime_attempt/3, clear_in_flight/2,/3, persist_safety/3,/4, legacy release APIs, close_lineage/2,/3, confirm_lineage_close/2 and rearm/5. R reservation/reuse and generation APIs enforce the same unresolved-state restriction. SuspensionRecovery.evaluate/2 retains security/durability suspension and resubmit=false. A bypass through history or a newly added writer is an acceptance failure.

## 8. Quarantine and disclosure

### 8.1 Governed decision authority

Human Master Gate issues the resolution. A separately authorized root installer verifies exact human decision, issuer identity and scope, retains its source digest and provisioning audit, and materializes immutable ResolutionDecision files under `/etc/symphony/gate2/p08-v2/resolutions/`. Helper trusts that root administrative attestation within the existing root TCB; it does not verify a Plane ID as authority or claim cryptographic human authentication. Approved issuer/installer enrollment is an external prerequisite. Host/runtime cannot create registry entries. No online Plane decision lookup or new daemon is introduced.

Root registry index is root-owned, synchronized and changed only under the same namespace lock. Provisioning/revocation does not rewrite the decision's expected root head. The helper validates the exact decision and initial head at begin; PendingResolution preserves those original bindings. Subsequent terminal requests use current outer expected_head, the pending digest and the saved initial decision binding, so begin does not make its own continuation stale.

### 8.2 Quarantine lifecycle and one-use authority

| Transition | Owner and guard | Side effect/identity | Restart and terminal meaning |
|---|---|---|---|
| clear/uncertain → quarantined → block_reuse | Trusted boundary/root; ownership/cleanup/disclosure uncertainty | Immutable quarantine and E/I/R block | Recording failure still denies |
| block_reuse/remains_quarantined → operator_resolution_pending | resolve_quarantine action begin, valid enrolled unspent decision, exact initial quarantine/head/G/epoch | Publish PendingResolution and pending QuarantineRecord; reserve decision in root chain, I mirrors; R remains blocked | Nonterminal processing only; no qualified proof asserted |
| pending → remains_quarantined | Explicit retain action with exact same-session reservation; no evidence fields or fresh proof required | Terminal root result consumes decision; gate QUARANTINED; I/R retain blocks | Terminal denial; a release-capable decision may fail closed this way |
| pending → released_for_new_authorization | Explicit release action, ReleaseResolutionDecision, exact fresh qualified proof/current vector and no unresolved covered obligations | Consume reservation, gate CLOSED/phase GENERATION_COMMITTED_CLOSED; mirror terminal result | Terminal future-consideration permission only |
| pending → conservatively abandoned/remains_quarantined | Session loss, expiry, revocation or restart; no release continuation | Authenticated recovery/record_quarantine records burned decision and retained block | Terminal denial; new decision needed |

The decision is reserved at successful begin and cannot be reserved again. Root chain history is the authority for RESERVED, CONSUMED or BURNED status; registry AVAILABLE does not override a prior reservation. Final result consumption and resolution share the single root head transition. A separate used-file is not authoritative. Begin write uncertainty may mean not reserved or reserved: reread, never infer permission. Terminal write uncertainty may mean still pending or terminal: reread, preserve quarantine until exact agreement. Neither uncertainty permits a second begin or release.

Retain accepts either decision variant because denial does not exceed its permission. It deliberately has no evidence fields; supplying them is an unknown-field error. Release accepts only the release variant and all proof fields are mandatory/non-null. Failed release remains pending until explicit retain, safe abandonment or a new governed process. Missing/revoked authorization never releases; authority-reducing record_quarantine remains available under its own caller guard. A new same-session terminal request after revocation cannot release. Retention after revoked authority is performed through record_quarantine, not by treating the revoked decision as still valid.

For final P01 dispositions resolution_ref stores the preexisting decision_id string. PendingResolution, decision digest and root consumption authenticate it. No object embeds its own future digest. A pending root record references its new pending quarantine record while the decision continues to bind the saved initial quarantine record. Host R does not change resource revision merely because begin occurred. Terminal mirror changes require exact root result; any mirror failure blocks future use. Read-only query can report a pending record but cannot resume an old session or burn it. Before another resolution, authenticated recovery or record_quarantine must make the safe abandonment durable; it cannot silently discard the reserved ID.

Known disclosure/credential/external-effect obligations cannot be cleared by a resource-only decision. Operator acknowledgement never supplies cleanup proof. Revocation is ordered under the root lock; an unmaterialized Plane change is not immediate host revocation. No quarantine resolution issues an A receipt, runtime grant, retry, lineage rearm or dispatch permission.

### 8.3 Disclosure lifecycle

Observation and qualification use the separate enums in section 5. A complete bounded detector may produce NO_DISCLOSURE_OBSERVED; incomplete coverage/interruption produces OBSERVATION_INCOMPLETE; suspicion POSSIBLE_DISCLOSURE; confirmed exposure KNOWN_DISCLOSURE. NOT_OBSERVED means no disclosure acquisition, not a negative result. It is permissible with DiagnosticNotApplicableRecord only under section 5.2 resource-only guards and cannot satisfy a disclosure qualification requirement. Host-only tests yield at most HOST_ONLY_PARTIAL. Integrated qualification requires exact patched artifact/logging profile and separate authority.

Each acquisition is immutable and has a new ID. A later clean scan cannot rewrite a known/incomplete prior record. known_disclosure_history is sticky forever. unresolved_disclosure_history stays true until an authenticated scope-specific decision and evidence resolve the obligation; this never erases known history. Restart preserves all known facts and marks interrupted current acquisition incomplete. Known/possible/incomplete disclosure makes cleanup unverified and blocks unsafe reuse. P01's existing possible_disclosure reason may represent the block while the immutable disclosure record preserves the exact distinction.

## 9. Resource observation and deferred coverage

| Resource class/support object | Stable authority and method | Required absence coverage | P08 claim |
|---|---|---|---|
| process_scope | Root registered fixture or later P04 allocation; pidfd, boot/UID/executable/cgroup/namespaces | Exact holder and descendants, prevented scope/reference escape | Controlled fixture only until P04 |
| mount_scope | Namespace handle, allocation and mount/filesystem identity | Every owning namespace and reference | Fixture observation; production deferred |
| workspace | P02 allocation, private filesystem/backing and pinned root | Writers, open/unlinked, mounts/backing/reference inventory | Production deferred |
| home | Distinct private allocation and owning filesystem | Same complete reference coverage | Production deferred |
| xdg_config | Exact attempt allocation | Same | Production deferred |
| xdg_state | Exact attempt allocation | Same | Production deferred |
| xdg_data | Exact attempt allocation | Same | Production deferred |
| cache | Exact private allocation/capacity and no sharing | Same | Production deferred |
| runtime_tmp | Allocation and pinned owning filesystem | Complete controlled writer/reference scope | Fixture only; no production transfer |
| provider_private | P03/P04 materialization/confinement | Credential copies/readers/private references | Unsupported production in P08 |
| network_scope | P04 lease/network registration | Exact namespaces/sockets/lease owner | Unsupported production in P08 |
| materialization | P03 identity/lifecycle and allocation | All copies/readers/destruction-owner proof | Deferred |
| candidate_stage | P06 stage/backing ownership | Sealed stage/writers/references | Deferred |
| backing image | Allocation plus device/inode/backing identity | Mount/loop/open references | Replacement fixture only |
| loop device | Allocation plus kernel device/backing association | Complete qualified owning scope | Fixture only |
| socket | Allocation plus inode/namespace | Qualified references, not path disappearance | Fixture only |
| open/unlinked object | Pinned original object and allocation history | Complete holder/reference scope | Unknown scope blocks |

The selected Linux observations use pinned proc directory/executable/namespace FDs, pidfds, cgroup v2 membership/events, qualified mountinfo and fdinfo reads, statx/fstat identities and qualified loop/backing kernel queries within registered owner scope. These are observations, not a global census. An unsupported ioctl, inaccessible namespace or unqualified reference inventory yields unsupported/incomplete. The helper cannot obtain coverage by modifying runtime confinement. No global absence from /proc enumeration alone. Scans contribute only inside a separately qualified confinement model with complete history and prevented reference escape. Freeze/cgroup emptiness alone does not prove no external FD/mount reference. Unsupported, inaccessible, replaced or over-limit evidence produces cleanup_unverified and quarantine. Reserved/null allocation identity is not proof of never allocated without owner history. An A→B replacement at X neither authorizes deleting B nor proves A absent.

## 10. Diagnostics, events and Herdr lifecycle requirements

Diagnostic applicability precedes the capture lifecycle. The trusted helper/verifier selects NOT_APPLICABLE only from a qualified resource-only policy with no required or opened resource diagnostic channel. That record is terminal applicability metadata, not successful capture, EOF or nondisclosure evidence. Every acquisition that requires or starts capture uses CAPTURE and the states below. A required but never collected channel becomes CAPTURE/INCOMPLETE. Restart of a started acquisition remains incomplete; it cannot become NOT_APPLICABLE. This leaves Herdr's actual capture state machine unchanged.

| Diagnostic transition | Guard and ordered effect | Failure/restart/terminal meaning |
|---|---|---|
| OPEN → CAPTURING | Qualified current acquisition/channels; concurrent drain stdout/stderr | Setup failure INCOMPLETE |
| CAPTURING → TRUNCATED_DRAINING | Retained limit reached; sticky truncated, discard excess, continue bounded drainage | Never complete evidence |
| CAPTURING → CLOSED | All required streams complete untruncated; disposition durably finalized | Transport completion only; not process/resource clean |
| TRUNCATED_DRAINING → CLOSED | Drainage ends and sticky truncation persists | Closed truncated remains incomplete evidence |
| capturing/draining → CANCELLED | Trusted cancellation/deadline; bounded drain and owned-child reap protocol | Failure INCOMPLETE, unresolved custody retained |
| any nonterminal → INCOMPLETE | Gap, channel/owner/persistence uncertainty | Terminal unusable acquisition; fresh ID/current authorization required |

Bound retained memory; continue concurrent drainage/discard where required. Counters saturate explicitly. Payload retention is volatile only; no raw payload in evidence/index/logs/exceptions/crash output. Disable client/helper core dumps in qualified host. Audit app-server emit_turn_event/6, emit_message/4, handle_response/4, log_non_json_stream_line/2, AgentRunner.run_worker_attempt/4, CredentialBoundary.redact/2 and all log sinks. Preserve legacy behavior; environment-derived redaction is not integrated proof.

```text
TRUNCATED != COMPLETE_EVIDENCE
PIPE_EOF != PROCESS_CLEAN
CHILD_REAPED != RESOURCE_CLEAN
BOUNDED_DRAINAGE != SECRET_REDACTION
```

Q01 requires stable process incarnation and replacement negatives, including actual holder death while wrapper survives. Q02 treats events only as hints: overflow, gap, partial history, disconnect/reconnect, owner restart, cursor/G mismatch or event during snapshot makes cache STALE and requires fresh authoritative reread. No EventBus is added. Q04 requires flood, descendant writer, blocked cancellation/deadline and owned-child reaping controls. Q05 requires replacement of workspace root, backing, loop, mount/filesystem, tmp/materialization, socket and candidate locator. P08 performs no runtime cleanup action and cannot close later owner claims with these fixtures.

## 11. Numerical, build and environment qualification

### 11.1 Candidate profile

All numbers remain unqualified candidates. Static enforcement does not establish workload fitness.

| Limit | Candidate | Qualification |
|---|---:|---|
| Retained bytes per stream / read buffer | 65,536 / 16,384 | Fixed allocations plus flood measurement |
| Input / output frame | 65,536 / 524,288 bytes | Prefix rejection, exact-boundary tests |
| Evidence / host journal | 262,144 / 1,048,576 bytes | Reject whole object; no coverage truncation |
| Resource / observation / process records | 64 / 512 / 128 | Reject over-limit complete acquisition |
| Reference inspections / predecessors / nesting | 4,096 / 8 / 8 | Static bounded loops and parser tests |
| Requests / total input / total output per session | 32 / 2 MiB / 8 MiB | Checked counters |
| Descriptors / address space / RSS | 2,048 / 128 MiB / 64 MiB | Limits plus measured actual peaks |
| Drain / caller cancellation / helper wall | 2 s / 1 s / 30 s | Caller bounds never prove kernel process death |
| Helper CPU / snapshot age | 10 s / 5 s | Exact host/monotonic time tests |
| Release concurrency / effect replay | 1 per namespace / 0 | Serialization and replay controls |
| Retained root objects / normal threshold | 4,096 / 3,840 | Reserve 256 failure records; exhaustion blocks |
| Evidence / index capacity | 2 GiB / 256 MiB | Filesystem/DETS overhead measurements |
| Recovery tries / job deadline | 3 per episode / 30 min | Then persistent block; no unbounded reconciliation |

Lengths and counts apply together. Max count does not promise every maximal ID tuple fits the frame. Rejection is whole-acquisition, never partial green. The retained-root-object count includes control, proposal, plan, release and evidence objects, so metadata cannot grow without a finite bound. Host journals share the qualified store capacity and their count is included in the retention profile. At capacity stop new acquisition and retain obligations; reserve exhaustion blocks maintenance without deleting evidence automatically. No automatic garbage collection or evidence overwrite is authorized by P08.

Measure at least 1,000 sessions per normal/max/saturation scenario with retained seeds on exact approved image. Record peak memory/FD/CPU/wall/drain/cancel/storage. All hard bounds must hold. Normal maximum cases target 25% memory/FD headroom, ≤20 s session, ≤750 ms cancellation response and ≤1.5 s drain. Violations require profile review, not automatic limit changes. Power-loss qualification injects every matrix boundary with old/new/corrupt outcomes; repeated resets supplement, never replace, state proof. Uninterruptible I/O remains blocked, not assumed killed.

### 11.2 Build identity and privilege boundary

Native scaffold does not exist in accepted tree. Future workspace is `native/gate2/`, with client/helper/protocol crates, locked dependencies, fixtures and qualification tests. Candidate Rust 1.98.1 and x86_64-unknown-linux-musl static target require approved distribution/linker/dependency/build-image digests. No floating Git deps, runtime downloads or unreviewed build scripts. Use locked offline builds after separately approved acquisition; record source SHA/tree, Cargo.lock, compiler/linker flags, dependency checksums, SBOM/licenses and output digests. Exact dependency closure is a build-input approval prerequisite, not implementer discretion to enlarge TCB.

Selected privileged runner is a dedicated single-use Ubuntu 24.04 x86_64 VM, group `symphony-gate2-qualification`, label `p08-host-v2`, candidate 4 vCPU/8 GiB RAM/16 GiB boot plus dedicated E/I volumes above. Names do not identify an approved image. Human-appointed Host Qualification Owner approves expanded disk digest, kernel package/build, local filesystem/options, sudo/plugins/policy and capability results. Independent infrastructure authority creates/destroys VM and controls external hard-reset/power-loss logs; guest cannot access controller credentials. One job then destruction even on failure.

Allowed separately authorized fixture-root effects are test users/cgroups/namespaces/processes, mount/loop/filesystem/socket/open-unlinked fixtures, exact binary/policy test installation, fault injection and external reset. No production mounts, provider credentials or real provider. Test driver effects never expand helper operations. Ordinary GitHub-hosted jobs build/test unprivileged logic; they are not this accepted privileged/durability environment.

Keep existing coverage partitions/aggregate, Dialyzer, static, transition, H070a and isolation jobs and validate-pr-description. Add `p08-native-build`, `p08-codec-and-protocol`, `p08-privileged-qualification` to make-all dependencies. Aggregate always checks every dependency == success; skipped/absent/cancelled/timeout is not success. Missing runner stays pending until explicit failure/deadline, never green. Protected environment approval binds exact SHA/tree/image. No pull_request_target execution of untrusted code on privileged runner. Existing Codex-invoking jobs require separate authorization before PR publication/CI.

Artifacts retain exact checkout SHA/tree, binary/build/image/kernel/sudo/fs profiles, claim/test IDs, seeds, all unsupported/failure outcomes, measurements and external reset records through package and P09 review. Missing evidence invalidates the claim. No runner/toolchain/policy/numeric qualification is claimed by this draft.

## 12. Acceptance, requirement register and traceability

### 12.1 Claim applicability

| Claim | Owner/package | Host-only proof | Integrated proof and current disposition |
|---|---|---|---|
| Codec/provenance/publication | Evidence owner/P08 | Independent vectors and root storage faults | Exact deployed producer still unqualified |
| E/I/R/A failure closure | Boundary/ledger owners/P08 | Controlled durable fixtures | Real owner coverage deferred |
| Process custody | Native observer/P08 | Q01 fixtures | P04 exact holder/confinement required |
| Diagnostics | Collector/P08 | Q04 bounded host tests | Exact patched Codex/logging required |
| Resource cleanup | Allocator/P02 and observer/P08 | Q05 replacement fixtures | Allocation/destruction history required |
| Credential lifecycle | P03 | No production claim | Materialization/copy/revocation proof deferred |
| Provider confinement/execution | P04 | No production execution | Exact integrated proof deferred |
| Publication/completion | P06/P07 | No authority supplied | Separate package proof |
| Final integrated acceptance | P09 | Package inventory only | Independent applicability and activation incomplete |

```ini
OB_025_HOST_ONLY_EVIDENCE=PARTIAL_ONLY
OB_025_INTEGRATED_QUALIFICATION=INCOMPLETE
```

### 12.2 Stable requirement register

Each requirement below incorporates the referenced specification section's full closed contract. The traceability matrix assigns its owner, implementation task, named automated test/proof and acceptance guard. No requirement is considered satisfied by this document's existence.

#### P08-AUTH-001

MUST reverify exact accepted main/tree and governing blobs; stop on movement. Contract: section 1. Governing source/rationale: G1/G2/G3. Required proof: `baseline_exact_objects` and GitHub SHA/tree/protection and blob comparison.

#### P08-AUTH-002

MUST NOT infer implementation, CI, privilege, publication, merge or activation authority. Contract: section 1.4. Governing source/rationale: G1/G4/current authorization. Required proof: `authorization_scope_denial` and Independent scope/diff review.

#### P08-AUTH-003

MUST preserve dormant foundation, incomplete enforced, no grants/retry/rearm/provider/publication/Done. Contract: section 1.4,7.4. Governing source/rationale: G4/P01. Required proof: `dormant_and_legacy_guards` and Exact-head preservation suite.

#### P08-AUTH-004

MUST partition fixture/host-only and integrated claims without production promotion. Contract: section 9,12.1. Governing source/rationale: G4/G5. Required proof: `fixture_claim_not_production` and Claim-specific P02/P03/P04/P09 evidence.

#### P08-AUTH-005

MUST record historical export mismatch and never treat R1-R4 as accepted authority. Contract: section 1.3. Governing source/rationale: R4-F02/G1. Required proof: `historical_provenance_register` and Historical attachment reconciliation or explicit review disposition.

#### P08-CMP-001

MUST preserve exact five-field GrantRef and deterministic P01 fingerprint. Contract: section 2.1. Governing source/rationale: AttemptGrant/G4. Required proof: `grant_ref_exact_namespace` and Source field/fingerprint vectors.

#### P08-CMP-002

MUST preserve exact Identity, Generation, AttemptResource and reference/disposition stored shapes. Contract: section 2.1. Governing source/rationale: Accepted P01. Required proof: `stored_struct_fields_exact` and Accepted source constructors and round trips.

#### P08-CMP-003

MUST map all string-or-nil references losslessly; current links only in declared verified slots. Contract: section 2.2,5.3. Governing source/rationale: P01/R3 review. Required proof: `historical_and_current_links` and Historical/malformed/self-link corpus.

#### P08-CMP-004

MUST support encodable 256-byte IDs and block broader values without rewrite or normalization. Contract: section 2.2. Governing source/rationale: P01/R3 review. Required proof: `p01_id_128_129_256_257` and ASCII/non-ASCII/overflow boundaries.

#### P08-CMP-005

MUST retain A current/history binding and reject legacy downgrade through every writer. Contract: section 2.3,7.4. Governing source/rationale: P01/G4. Required proof: `gate2_history_no_downgrade` and All generic writer call-site audit.

#### P08-INV-001

MUST use fixed root-owned executables/manifests/policy and pinned installation identities. Contract: section 3.1. Governing source/rationale: G4/R1 review. Required proof: `fixed_installation_replacement` and Exact install image/modes/digests.

#### P08-INV-002

MUST restrict sudo to fixed digest command with empty arguments and qualified stdio behavior. Contract: section 3.1. Governing source/rationale: R3/R4 reviews. Required proof: `sudo_args_env_proxy_rejected` and Exact sudo/plugin/policy qualification.

#### P08-INV-003

MUST enforce descriptor table, kernel credentials/pidfds, client liveness and ancillary rejection. Contract: section 3.2. Governing source/rationale: G5-Q01. Required proof: `peer_pidfd_credentials_inheritance` and Real kernel transport tests.

#### P08-INV-004

MUST retain pinned exclusive root lock across timeout/restart with no stealing. Contract: section 3.3. Governing source/rationale: R3-F01. Required proof: `h1_pause_restart_h2_busy` and Real lock owner-death/delayed helper proof.

#### P08-INV-005

MUST frame bounded sessions and reject stale/duplicate/illegal-phase requests. Contract: section 6.1. Governing source/rationale: R4-F02. Required proof: `all_15_opcode_guards` and Independent request/response corpus.

#### P08-INV-006

MUST treat partial writes/timeouts/ambiguous responses as closed, never termination proof. Contract: section 3.3,6.1. Governing source/rationale: G5-Q04. Required proof: `timeout_live_helper_blocks` and Live helper and blocked I/O proof.

#### P08-GEN-001

MUST reserve target generation durably before host target computation; bind journal before R mutation. Contract: section 4.1. Governing source/rationale: R4-F01. Required proof: `proposal_journal_plan_acyclic` and Ordered call graph and fault trace.

#### P08-GEN-002

MUST bind reservation/source/session/expiry, burn abandoned sequences and forbid current-generation inference. Contract: section 4.2. Governing source/rationale: R4-F01/G4. Required proof: `proposal_expiry_burn_conflict` and High-water/orphan/restart vectors.

#### P08-GEN-003

MUST define exactly 15 closed operations, with begin_recovery binding rather than selecting target. Contract: section 4.1,6. Governing source/rationale: R4-F01/F02. Required proof: `opcode_vocabulary_and_schemas` and Closed schema/phase cross-check.

#### P08-GEN-004

MUST stage R read-only before generation mutation and preserve compatibility startup rejection. Contract: section 4.3. Governing source/rationale: P01/R4-F03. Required proof: `staged_no_startup_side_effect` and Real OTP caller/startup tests.

#### P08-GEN-005

MUST persist exact journal and apply/repair only before-or-after images without repeated increment. Contract: section 4.4. Governing source/rationale: P01/R4-F01. Required proof: `recovery_partial_rows_exact` and Every pending/row/metadata sync fault.

#### P08-GEN-006

MUST activate only closed current E/I/R agreement; owner repair requires another fresh generation. Contract: section 4.1-4.4. Governing source/rationale: G4/G5-Q02. Required proof: `recovery_activation_current_closed` and Restart/owner replacement traces.

#### P08-EVD-001

MUST implement strict G2-CJSON-2 scalars/keys/order/bounds and reject ambiguous bytes. Contract: section 5.1. Governing source/rationale: R4-F02. Required proof: `canonical_reject_corpus` and Independent Rust/Elixir vectors.

#### P08-EVD-002

MUST use the exact closed record registry and operation envelopes. Contract: section 5.2,6.1. Governing source/rationale: R4-F02. Required proof: `all_record_fields_closed` and Unknown/missing/duplicate field vectors.

#### P08-EVD-003

MUST preserve domain-separated identities, immutable creation generation and revision-bound snapshots. Contract: section 5.3-5.4. Governing source/rationale: G4/G5-Q02/Q05. Required proof: `golden_generation_and_revision` and Independent digest calculations.

#### P08-EVD-004

MUST publish immutable objects/control with file and directory sync; orphans never confer authority. Contract: section 3.3,7.3. Governing source/rationale: G4/R2 review. Required proof: `immutable_publish_crash_windows` and Filesystem/reset matrix.

#### P08-EVD-005

MUST use stable allocation/process/object identity and complete qualified reference coverage. Contract: section 3.2,9. Governing source/rationale: G5-Q01/Q05. Required proof: `replacement_and_missing_history` and Actual process/fs/device fixtures; integrated coverage deferred.

#### P08-EVD-006

MUST independently resolve evidence provenance; shape-valid CleanupEvidenceRef is insufficient. Contract: section 2.3,5.3. Governing source/rationale: P01/G4. Required proof: `forged_ref_index_object` and Producer/profile/index mismatch corpus.

#### P08-REL-001

MUST enforce exact E/I/R/A writer principals and synchronized non-authoritative I mirrors. Contract: section 7.1. Governing source/rationale: R3-F02. Required proof: `owner_epoch_receipt_forgery` and Captured caller/monitor/name replacement tests.

#### P08-REL-002

MUST commit only guarded FENCING→FENCED or DESTROYING→ABSENT_VERIFIED with exact revisions. Contract: section 7.2. Governing source/rationale: P01/charter/G4. Required proof: `resource_verification_exact_revision` and Qualified fence/absence proof and forbidden transition tests.

#### P08-REL-003

MUST commit A only from boundary with exact prepared projection and verified R receipt. Contract: section 7.1-7.2. Governing source/rationale: P01/G4. Required proof: `attempt_release_preparation_bound` and A response-loss and forged commit tests.

#### P08-REL-004

MUST acknowledge resources before prepare, then A, completion, I completion and fresh settlement. Contract: section 6,7.2. Governing source/rationale: R4-F02. Required proof: `release_order_resource_ack_first` and Call-order trace and both complete_release variants.

#### P08-REL-005

MUST require joint current quiescent agreement on every dispatch/reuse/clear/rearm path. Contract: section 7.4. Governing source/rationale: G4/P01. Required proof: `released_a_missing_completion_denied` and Enumerated admission reader matrix.

#### P08-REL-006

MUST cover every write/sync/publication boundary and uncertain old/new/corrupt result. Contract: section 7.3. Governing source/rationale: R2/R4 reviews. Required proof: `release_all_crash_boundaries` and Reset/fault evidence, no global atomicity claim.

#### P08-REC-001

MUST block dirty/unreadable DETS without automatic repair or history erasure. Contract: section 4.3. Governing source/rationale: R4-F03/P01. Required proof: `dirty_dets_needs_repair` and Qualified OTP read-only and unchanged-file proof.

#### P08-REC-002

MUST retain path lock and validate file/semantic identity across close/write-reopen. Contract: section 4.3. Governing source/rationale: R4-F03. Required proof: `readonly_reopen_replacement` and Competing opener and inode/row replacement tests.

#### P08-REC-003

MUST leave old unbound P01 pending markers maintenance-required. Contract: section 4.4. Governing source/rationale: P01/R4-F03. Required proof: `legacy_pending_no_journal` and No bypass through staged caller authorization.

#### P08-QUA-001

MUST retain quarantine on cleanup/ownership/disclosure uncertainty and never resolve by acknowledgement. Contract: section 8.2. Governing source/rationale: G4/charter. Required proof: `quarantine_no_ack_release` and Lifecycle and mirror-failure matrix.

#### P08-QUA-002

MUST authenticate root-provisioned decision scope/revocation/one-use; no arbitrary decision ID authority. Contract: section 8.1. Governing source/rationale: R3 review/R4. Required proof: `decision_wrong_scope_revoked_replay` and Provisioning/consumption/reset proof.

#### P08-QUA-003

MUST preserve known/possible/incomplete disclosure separately with sticky history and scope-specific resolution. Contract: section 8.3. Governing source/rationale: G4-OB025/R3 review. Required proof: `known_incomplete_restart_sticky` and Immutable predecessor and resolution tests.

#### P08-DIA-001

MUST bound concurrent retention/drain/cancellation, record sticky truncation and preserve custody obligations. Contract: section 10. Governing source/rationale: G5-Q04. Required proof: `flood_inherited_writer_cancel` and Real pipes/processes and peak measurements.

#### P08-DIA-002

MUST prevent raw captured payloads reaching logs/evidence/errors/core/temp/operator outputs. Contract: section 10. Governing source/rationale: G4-OB020/025. Required proof: `synthetic_secret_all_host_sinks` and Host-only synthetic-secret corpus; integrated deferred.

#### P08-DIA-003

MUST invalidate cached evidence on event loss/restart/cursor mismatch and reread authoritatively. Contract: section 10. Governing source/rationale: G5-Q02. Required proof: `event_gap_snapshot_race` and Gap/overflow/disconnect/reread race tests.

#### P08-DIA-004

MUST preserve four diagnostic non-equivalences and terminal/restart states. Contract: section 10. Governing source/rationale: G5-Q04. Required proof: `diagnostic_terminal_meanings` and All diagnostic transition tests.

#### P08-QUAL-001

MUST enforce candidate bounds and reject saturation without partial clean claims; accept only measured profile. Contract: section 11.1. Governing source/rationale: G4-OB021. Required proof: `limits_boundary_and_saturation` and Exact-host peak/time/capacity measurements.

#### P08-QUAL-002

MUST bind source/toolchain/lockfile/dependencies/build image/binary identity before installation. Contract: section 11.2. Governing source/rationale: G4/R4 review. Required proof: `locked_build_identity` and Independent clean build/SBOM/reproducibility review.

#### P08-QUAL-003

MUST qualify single-use privileged runner and external reset controller under separate authority. Contract: section 11.2. Governing source/rationale: R4 review. Required proof: `runner_capability_reset_isolation` and Approved image/privilege/controller evidence.

#### P08-QUAL-004

MUST preserve existing required CI and make missing native proof non-successful. Contract: section 11.2. Governing source/rationale: G4/P01. Required proof: `aggregate_missing_privileged_denied` and Exact-head job graph/results and checkout proof.

#### P08-QUAL-005

MUST accept claims independently by exact scope/artifact/environment and retain integrated OB-025 incomplete. Contract: section 12.1,12.3. Governing source/rationale: G4-OB023/025/G5. Required proof: `claim_scope_ob025_not_closed` and Independent acceptance decision and retained artifacts.

### 12.3 Qualification claim lifecycle and acceptance guard

Owner is the independent acceptance owner, distinct from implementation evidence author. PROPOSED→BUILT requires exact build identity; BUILT→ENVIRONMENT_QUALIFIED requires approved host capabilities/image/privilege; ENVIRONMENT_QUALIFIED→TESTED requires complete retained test evidence; TESTED→REVIEWED requires independent applicability review; REVIEWED→ACCEPTED requires exact human acceptance. Any nonterminal stage may become REJECTED or BLOCKED on missing/stale evidence with an explicit reason. BLOCKED may return only to a freshly revalidated prerequisite stage; no automatic acceptance. ACCEPTED remains historical when a later identity invalidates applicability; a new claim is required. State owner records immutable QualificationClaim predecessors through evidence inventory; acceptance never changes runtime authority. Restart retains facts but not acceptance for changed artifacts/profiles. ACCEPTED is terminal only for its exact claim; source/binary/environment/profile movement requires a new claim and review. A host-only accepted claim cannot close an integrated obligation.

No lifecycle uses the word completion to prove more than its named domain: session closure is custody/transport closure, diagnostic CLOSED is transport termination, evidence publication is byte custody, release SETTLED is current store agreement, and qualification ACCEPTED is exact scoped external adjudication. None issues a runtime grant.

### 12.3a Explicit staged, evidence and resource state models

| Domain | Owner and state transitions | Guards and side effects | Durable identity, failure and restart | Terminal meaning |
|---|---|---|---|---|
| Staged R startup | Captured boundary/R: CLOSED_STARTUP→INSPECTING→SOURCE_VALIDATED→PLAN_BOUND→APPLYING→TARGET_SYNCED→MIRRORED→GENERATION_COMMITTED→CURRENT_GENERATION_CLOSED | Only section 4 staged APIs; proposal before target construction, plan before write, reread before activate | Root proposal/plan, exact journal, metadata/rows/marker; any failure STAGED_BLOCKED or MAINTENANCE_REQUIRED; no normal calls until activated | Closed consistent facts, no capability |
| Evidence acquisition | Helper/boundary: NEW→RESTRICTED→ACQUIRING→VALIDATED→PUBLISHED→INDEXED | Current owner/G/vector, qualified coverage, exact canonical bytes; object sync/publication/dir sync then I | Acquisition/release IDs, object digest/provenance/index; interruption INCOMPLETE or STALE; no acquisition restored | Immutable attributable bytes only |
| Writer observation | Native verifier: REQUIRED→OBSERVING→VERIFIED_FENCED or FENCE_UNVERIFIED | Stable identities and complete scope, no helper effect | Observation/root digest; any identity gap invalidates; restart fresh handles required | Qualified writer absence only |
| Resource absence | Native verifier: REQUIRED→OBSERVING→VERIFIED_ABSENT or CLEANUP_UNVERIFIED | Original allocation and complete reference coverage | Native evidence + exact vector; unsupported/replaced/incomplete remains quarantined | Original resource absent only in qualified scope |
| R verification commit | Boundary/R: FENCING→FENCED or DESTROYING→ABSENT_VERIFIED | Exact prior revision/native provenance and current G; durable write+reread | Last evidence string, revision and quarantine preserved; conflict/storage failure blocks | Resource-state fact, never dispatch |
| Generation reservation | Root: NONE→PROPOSED→PLAN_BOUND→GENERATION_COMMITTED_CLOSED; local R_APPLIED/MIRRORED milestones between plan and commit | Section 4 ordered protocol | Root phase remains PLAN_BOUND during local R/I milestones; expired unbound proposal ABANDONED with sequence burned; bound plan cannot be skipped | Current generation commitment, gate closed |

These stage names describe owner state; only RootPhase values declared in section 5 are persisted as root phases. MAINTENANCE_REQUIRED and STAGED_BLOCKED are staged owner dispositions, not invented clean resource states. Closing after any failure preserves unresolved obligations. Unsupported evidence cannot transition into a verified state.

### 12.3b Boundary error mapping

Native invalid_request and unencodable_p01_value map to boundary invalid_request; unauthorized_caller maps unchanged; unsupported_host/unqualified_profile map to cleanup_verifier_unavailable; lock_busy/client_dead/stale_session map to boundary_unavailable; identity_conflict maps to ownership_ambiguous; stale_generation maps to recovery_generation_mismatch; head_conflict/replay_conflict map to cleanup_reference_stale; phase_conflict maps to transition_invalid; limit_exceeded/cleanup_unverified map to cleanup_not_verified; decision_missing/revoked/consumed map to quarantined; maintenance_required maps to storage_unavailable. Storage errors map unchanged. Unknown native outcomes map to boundary_unavailable. A bounded internal diagnostic enum may retain the more specific nonsecret code, never raw payload. Existing P01 public function errors remain intact. For the new staged entry selection, staged_startup_required is an explicit new typed startup result and must be added to its typespec/normalizer; it is not a released state.

### 12.4 Requirements-to-test traceability

The named tests are required future tests, not executed results. T numbers refer to the companion plan. Acceptance guard for each row is exact contract proof, required qualification where named, and independent review of applicability. U denotes nonprivileged deterministic/OTP proof; P denotes separately authorized disposable-host proof; I denotes later integrated proof. A P or I requirement cannot be passed by skipping it in U.

| Requirement | Owner | Task | Automated test or read-only verification | Qualification evidence | Acceptance guard |
|---|---|---|---|---|---|
| P08-AUTH-001 | Planner/acceptance owner | P08-T01 | `baseline_exact_objects` | U: GitHub SHA/tree/protection and blob comparison | Exact scope; no missing/unsupported proof accepted |
| P08-AUTH-002 | Boundary/acceptance owner | P08-T14 | `authorization_scope_denial` | U: Independent scope/diff review | Exact scope; no missing/unsupported proof accepted |
| P08-AUTH-003 | Orchestrator owner | P08-T14 | `dormant_and_legacy_guards` | U: Exact-head preservation suite | Exact scope; no missing/unsupported proof accepted |
| P08-AUTH-004 | Qualification owner | P08-T17 | `fixture_claim_not_production` | U/P + deferred I: Claim-specific P02/P03/P04/P09 evidence | Exact scope; no missing/unsupported proof accepted |
| P08-AUTH-005 | Planner | P08-T01 | `historical_provenance_register` | U: Historical attachment reconciliation or explicit review disposition | Exact scope; no missing/unsupported proof accepted |
| P08-CMP-001 | Compatibility owner | P08-T02 | `grant_ref_exact_namespace` | U: Source field/fingerprint vectors | Exact scope; no missing/unsupported proof accepted |
| P08-CMP-002 | Compatibility owner | P08-T02 | `stored_struct_fields_exact` | U: Accepted source constructors and round trips | Exact scope; no missing/unsupported proof accepted |
| P08-CMP-003 | Codec owner | P08-T02 | `historical_and_current_links` | U: Historical/malformed/self-link corpus | Exact scope; no missing/unsupported proof accepted |
| P08-CMP-004 | Codec owner | P08-T02 | `p01_id_128_129_256_257` | U: ASCII/non-ASCII/overflow boundaries | Exact scope; no missing/unsupported proof accepted |
| P08-CMP-005 | AttemptLedger owner | P08-T13 | `gate2_history_no_downgrade` | U: All generic writer call-site audit | Exact scope; no missing/unsupported proof accepted |
| P08-INV-001 | Native installation owner | P08-T05 | `fixed_installation_replacement` | P: Exact install image/modes/digests | Exact scope; no missing/unsupported proof accepted |
| P08-INV-002 | Native installation owner | P08-T05 | `sudo_args_env_proxy_rejected` | P: Exact sudo/plugin/policy qualification | Exact scope; no missing/unsupported proof accepted |
| P08-INV-003 | Native client owner | P08-T05 | `peer_pidfd_credentials_inheritance` | P: Real kernel transport tests | Exact scope; no missing/unsupported proof accepted |
| P08-INV-004 | Root control owner | P08-T06 | `h1_pause_restart_h2_busy` | P: Real lock owner-death/delayed helper proof | Exact scope; no missing/unsupported proof accepted |
| P08-INV-005 | Protocol owner | P08-T06 | `all_15_opcode_guards` | P: Independent request/response corpus | Exact scope; no missing/unsupported proof accepted |
| P08-INV-006 | Boundary/native owner | P08-T06 | `timeout_live_helper_blocks` | P: Live helper and blocked I/O proof | Exact scope; no missing/unsupported proof accepted |
| P08-GEN-001 | Root generation owner | P08-T07 | `proposal_journal_plan_acyclic` | P: Ordered call graph and fault trace | Exact scope; no missing/unsupported proof accepted |
| P08-GEN-002 | Root generation owner | P08-T07 | `proposal_expiry_burn_conflict` | P: High-water/orphan/restart vectors | Exact scope; no missing/unsupported proof accepted |
| P08-GEN-003 | Protocol owner | P08-T07 | `opcode_vocabulary_and_schemas` | P: Closed schema/phase cross-check | Exact scope; no missing/unsupported proof accepted |
| P08-GEN-004 | ResourceLedger owner | P08-T08 | `staged_no_startup_side_effect` | P: Real OTP caller/startup tests | Exact scope; no missing/unsupported proof accepted |
| P08-GEN-005 | Recovery owner | P08-T08 | `recovery_partial_rows_exact` | P: Every pending/row/metadata sync fault | Exact scope; no missing/unsupported proof accepted |
| P08-GEN-006 | Boundary owner | P08-T08 | `recovery_activation_current_closed` | P: Restart/owner replacement traces | Exact scope; no missing/unsupported proof accepted |
| P08-EVD-001 | Codec owner | P08-T03 | `canonical_reject_corpus` | U: Independent Rust/Elixir vectors | Exact scope; no missing/unsupported proof accepted |
| P08-EVD-002 | Codec/protocol owner | P08-T03 | `all_record_fields_closed` | U: Unknown/missing/duplicate field vectors | Exact scope; no missing/unsupported proof accepted |
| P08-EVD-003 | Codec owner | P08-T03 | `golden_generation_and_revision` | U: Independent digest calculations | Exact scope; no missing/unsupported proof accepted |
| P08-EVD-004 | Root store owner | P08-T06 | `immutable_publish_crash_windows` | P: Filesystem/reset matrix | Exact scope; no missing/unsupported proof accepted |
| P08-EVD-005 | Native observer | P08-T09 | `replacement_and_missing_history` | P: Actual process/fs/device fixtures; integrated coverage deferred | Exact scope; no missing/unsupported proof accepted |
| P08-EVD-006 | Evidence verifier owner | P08-T10 | `forged_ref_index_object` | U: Producer/profile/index mismatch corpus | Exact scope; no missing/unsupported proof accepted |
| P08-REL-001 | Boundary/index owner | P08-T11 | `owner_epoch_receipt_forgery` | U: Captured caller/monitor/name replacement tests | Exact scope; no missing/unsupported proof accepted |
| P08-REL-002 | Resource verifier owner | P08-T12 | `resource_verification_exact_revision` | U: Qualified fence/absence proof and forbidden transition tests | Exact scope; no missing/unsupported proof accepted |
| P08-REL-003 | AttemptLedger owner | P08-T13 | `attempt_release_preparation_bound` | U: A response-loss and forged commit tests | Exact scope; no missing/unsupported proof accepted |
| P08-REL-004 | Release owner | P08-T14 | `release_order_resource_ack_first` | U: Call-order trace and both complete_release variants | Exact scope; no missing/unsupported proof accepted |
| P08-REL-005 | Orchestrator owner | P08-T14 | `released_a_missing_completion_denied` | U: Enumerated admission reader matrix | Exact scope; no missing/unsupported proof accepted |
| P08-REL-006 | Recovery/qualification owner | P08-T14 | `release_all_crash_boundaries` | P: Reset/fault evidence, no global atomicity claim | Exact scope; no missing/unsupported proof accepted |
| P08-REC-001 | Recovery owner | P08-T08 | `dirty_dets_needs_repair` | P: Qualified OTP read-only and unchanged-file proof | Exact scope; no missing/unsupported proof accepted |
| P08-REC-002 | ResourceLedger owner | P08-T08 | `readonly_reopen_replacement` | P: Competing opener and inode/row replacement tests | Exact scope; no missing/unsupported proof accepted |
| P08-REC-003 | Recovery owner | P08-T08 | `legacy_pending_no_journal` | P: No bypass through staged caller authorization | Exact scope; no missing/unsupported proof accepted |
| P08-QUA-001 | Quarantine owner | P08-T15 | `quarantine_no_ack_release`, `resolution_begin_pending`, `retain_without_proof` | U: Lifecycle and mirror-failure matrix | Exact scope; no missing/unsupported proof accepted |
| P08-QUA-002 | Root decision owner | P08-T15 | `decision_wrong_scope_revoked_replay`, `release_requires_release_decision`, `pending_restart_burned` | U: Provisioning/consumption/reset proof | Exact scope; no missing/unsupported proof accepted |
| P08-QUA-003 | Disclosure owner | P08-T15 | `known_incomplete_restart_sticky` | U: Immutable predecessor and resolution tests | Exact scope; no missing/unsupported proof accepted |
| P08-DIA-001 | Diagnostic owner | P08-T16 | `flood_inherited_writer_cancel` | P: Real pipes/processes and peak measurements | Exact scope; no missing/unsupported proof accepted |
| P08-DIA-002 | Diagnostic owner | P08-T16 | `synthetic_secret_all_host_sinks` | U/P + deferred I: Host-only synthetic-secret corpus; integrated deferred | Exact scope; no missing/unsupported proof accepted |
| P08-DIA-003 | Observation owner | P08-T16 | `event_gap_snapshot_race` | U: Gap/overflow/disconnect/reread race tests | Exact scope; no missing/unsupported proof accepted |
| P08-DIA-004 | Diagnostic owner | P08-T16 | `diagnostic_terminal_meanings`, `resource_only_no_capture`, `required_capture_cannot_be_not_applicable` | U: All diagnostic transition tests | Exact scope; no missing/unsupported proof accepted |
| P08-QUAL-001 | Qualification owner | P08-T17 | `limits_boundary_and_saturation` | P: Exact-host peak/time/capacity measurements | Exact scope; no missing/unsupported proof accepted |
| P08-QUAL-002 | Build owner | P08-T04 | `locked_build_identity` | U: Independent clean build/SBOM/reproducibility review | Exact scope; no missing/unsupported proof accepted |
| P08-QUAL-003 | Host qualification owner | P08-T17 | `runner_capability_reset_isolation` | P: Approved image/privilege/controller evidence | Exact scope; no missing/unsupported proof accepted |
| P08-QUAL-004 | CI owner | P08-T17 | `aggregate_missing_privileged_denied` | U: Exact-head job graph/results and checkout proof | Exact scope; no missing/unsupported proof accepted |
| P08-QUAL-005 | Independent Master Gate | P08-T17 | `claim_scope_ob025_not_closed` | U/P + deferred I: Independent acceptance decision and retained artifacts | Exact scope; no missing/unsupported proof accepted |

### 12.5 Open evidence and approval prerequisites

There is no unresolved selection between generation mechanisms: proposal precedes target computation and plan binding. The historical R4 attachment/export identity remains unreconciled. Exact native dependency closure/toolchain, sudo policy/kernel features, issuer/installer enrollment, image/controller, numerical measurements and every execution result remain unqualified. They block relevant implementation input approval, installation, execution or production claim, not permission to review this proposal. No assertion of successful test or environment qualification is made.

Next permitted action is independent review of these two local drafts. Exact revision acceptance, documentation PR/automatic CI, production implementation, privileged qualification, push/publication, human merge and eventual activation each require separate authority. No existing governance/status/scanner/inventory record is modified by this draft.

## 13. v0.3 review closure and proof register

The four corrections are design selections proposed for independent review, not accepted contracts or qualified outcomes. V02-F01 maps to sections 5.2b and 6.18; V02-F02 to sections 6.5/6.8/6.17a; V02-F03 to sections 5.2b/6.6/7.1b; V02-F04 to sections 5.2b/5.2c. Original-byte receipt remains an independent acceptance hold. No package scope or execution authority changes.

The following additional tests are normative extensions of the existing 49 requirement proofs and 18 tasks. Each test must assert durable bytes, root reachability and denied admission after every injected uncertain write, rather than rely on a successful API return.

| Requirements | Tasks | Additional automated/qualification proof | Acceptance guard |
|---|---|---|---|
| P08-INV-002/006, P08-GEN-006, P08-QUA-002/003 | T05, T06, T15 | Section 6.18 handoff roundtrip, wrong head/purpose, expired, failed startup/installer, restarted boundary, old helper and replay controls | Existing epoch is provisioned under a released lock and consumed once; no new runtime authority |
| P08-REL-001/004/005/006, P08-QUA-001/002 | T11, T14, T15 | Section 6.17a terminal evidence-only matrix and later governed resolution | Root remains QUARANTINED, evidence is retained, I agrees and R/A do not change |
| P08-REL-001/004/005, P08-EVD-002 | T06, T11, T14 | Section 7.1b restriction, partial key/head, stale generation, replay/conflict and snapshot-without-restriction tests | No snapshot use or admission without synchronized current restriction and actual reread |
| P08-EVD-001/002, P08-DIA-001/003/004 | T06, T16 | Section 5.2c missing/replaced/unqualified policy, caller digest, partial registry/profile and no-capture spoof tests | Exact root-installed accepted policy is resolved independently before eligibility |

The 300-second handoff lifetime, 4,096-byte policy, 64-entry/32,768-byte registry, 65,536-byte archived decision and 8,192-byte added-record bounds are candidate profile additions. Static parsing tests must reject limit+1, duplicate fields and overflow. The qualified-host measurement protocol in section 11 must include maximum-size lookups/handoffs and failure at each persistence boundary. Acceptance requires all operations remain within the existing memory, descriptor, framing and deadline budgets with those additions; otherwise the profile remains blocked pending a separately reviewed limit change. A 300-second authorization window does not extend helper execution or evidence-freshness deadlines. Expired observations require new proof even if the provisioning handoff remains valid.

External runner, toolchain/dependency closure, sudo/kernel behavior, installation/issuer provisioning and numerical profiles remain unqualified. OB_025_HOST_ONLY_EVIDENCE=PARTIAL_ONLY and OB_025_INTEGRATED_QUALIFICATION=INCOMPLETE. Neither this revision nor document validation authorizes production implementation, CI, privilege, publication, AUTH_07 consumption or Gate 2 activation.

## 14. Targeted v0.4 review corrections

The independently reviewed v0.3 original-file identities were specification SHA-256 `955613ed5ddcc9e5ce30cf56df67deba2a7469d8627f2582c4e5743891b33f2b`, 187,983 bytes, and plan SHA-256 `4e071fe0b485fa575005aaee3d4fb01d5497e22fccca43b7a79a481db3284fa2`, 59,628 bytes. Their identity hold is resolved; neither document was accepted. New v0.4 identities require independent readback.

V03-F01 adds the explicit nullable authorization_sha256 field to ReleaseRecord and section 6.5a's root-reachable consumption/recovery contract. This is a proposed P08 wire-schema correction, not a P01 type change or deployed migration. V03-F02 adds T14 as a T15 prerequisite. V03-F03 corrects the policy qualification reference to the sole closed type QualificationClaim. The 49 requirement IDs, 18 tasks, 15 opcodes and six canonical fixtures remain unchanged. No execution or publication authority follows from these corrections.

## 15. Targeted v0.5 review corrections

The reviewed v0.4 original specification was 194,390 bytes, SHA-256 `d5030746eccab224bab9ead40bf1a4fb46b7a59a1ad73bec35aafd869903086c`; its plan was 61,300 bytes, SHA-256 `5e915753e52abd9da5915e7ff02bb194afeed8ef1812f6ca3e9d40aa82c50c08`. Their independent identity verification does not imply acceptance of this revision.

V04-F01 selects the initial before_resource.snapshot_sha256 mapping and later exact bind validation in section 6.5b. V04-F02 gives root and I restrictions distinct digest fields and explicit cross-receipt checks. V04-F03 makes T16 a prerequisite of T14, preserving the acyclic graph and placing diagnostic eligibility before full transaction integration. V04-F04 makes current closed-record wording match P08-SPEC-0.7 and explicitly rejects unsupported historical encodings. These corrections preserve 49 requirements, 18 tasks, 15 opcodes, six existing canonical fixtures and all deferred qualification/authority boundaries. I wire field names change as specified; P01 stored types do not change. No implementation, qualification or publication is authorized.

## 16. Targeted v0.6 review corrections

The independently verified v0.5 originals were specification 203,058 bytes, SHA-256 `407f0474a21c8b6c6d003150390946ceb4651080ca852cc56ac05c7efc7ffd58`, and plan 63,309 bytes, SHA-256 `e61b36141c1341931053d3ab49f253e103cb03b299afd04852d51b172f48011c`. Their verified identity does not imply acceptance of v0.6.

V05-F01 adds RootRestrictionProof on the existing restrict_release/query_settlement responses and makes it restrict_sync/3's third argument, with exact host verification, history representation and lost-response rules in section 6.5c. V05-F02 defines QUIESCENT as durable closure independent of acknowledgement and separates actual kernel lock release in section 6.16a. V05-F03 assigns fixture-only I repair to T11 and actual terminal E/I integration to T14. Section 5.2b no longer carries a historical version heading. All 49 requirements, 18 tasks, 15 opcodes, six canonical fixtures, P01 compatibility and deferred qualification/authority restrictions remain.

## 17. Targeted v0.7 read-path correction

Master Gate independently verified v0.6 original identities: specification 215,824 bytes, SHA-256 `a3ba35f983e1be6100c7b28177f5f1ad538c61811e8ccc68028aa846ae0d61ef`; plan 66,093 bytes, SHA-256 `dc932dd72fd4e2c2ec5887438ffa5fd4c932e1173b038385dd4d0be7c1eebe9b`. Those identities and resolved findings do not confer acceptance on v0.7.

V06-F01 permits query_settlement in the already authenticated release session and defines exact post-I-sync and completion-time read ordering in section 6.13a. The captured-boundary restrict_sync wrapper releases its private ledger call before issuing the native query, then confirms actual I state, avoiding an owner callback deadlock. T06/T11/T14 own the additional controls. There are still 49 requirements, 18 tasks, 15 opcodes and six unchanged canonical fixtures. Root ownership, generation recovery, quarantine and release durability are preserved. All build/environment/numerical/integrated OB-025 qualification remains outstanding, and no execution, publication or activation authority is added.
