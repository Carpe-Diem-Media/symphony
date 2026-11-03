# Repository archive note

This is research evidence, not current programme or execution authorization.
Read current authorization from live governing decisions and repository governance.
Statements in the archived body about then-current authorization or successor-baseline
rebinding are observations made when the research was performed. They do not revoke,
extend or reinterpret subsequently supplied authority, including separate P01 authority.

The Master Gate's later mandatory qualification-refinement decision is recorded in
[the refinement document](../GATE2_HERDR_QUALIFICATION_REFINEMENT_2026-11-03.md) and its
[derivative projection](../GATE2_HERDR_QUALIFICATION_REFINEMENT.json). The archived body's earlier planning-only and
deferred-integration dispositions are historical research, not the current decision.

The complete accepted source report body below is preserved byte-for-byte.
Source report SHA-256: `5fcc1dad84e2101e211e12e08e780825ce01056b1b786a60b7088d9d24d905a5`.
No Herdr execution, executed test result or implementation proof is asserted by archiving it.

<!-- BEGIN ARCHIVED_REPORT -->
# Herdr evaluation for Symphony Gate 2

Read-only architecture evaluation, 2026-11-03. Revised following the supplied Master-level research disposition. No implementation or execution authority is granted.

**Decision:** accept this evaluation as reference research. Keep the Gate 2 architecture and nine packages. The five ranked negative-control patterns are eligible for planning within existing Gate 2 qualification, before Gate 2 acceptance and subject to normal implementation authority. Defer runtime integration; direct code reuse remains unrecommended. Do not embed Herdr, run its daemon inside the Gate 2 trust boundary, or reuse its session/authority model.

Evidence labels distinguish `CONFIRMED_FROM_CODE`, `CONFIRMED_FROM_DOCS`, `INFERENCE` and `UNKNOWN`. Source-test references mean the test bodies were inspected, not executed.

## A. Exact baselines and authority

```text
SYMPHONY_REPOSITORY=JCSchoeman96/symphony
SYMPHONY_MAIN_SHA=86336d28671cfd6ac0a55c2ebe48094b8d8a8237
SYMPHONY_MAIN_TREE=4c362c8800c3ebb75408d1af015184f5beb04d5a
SYMPHONY_MAIN_PROTECTED=true
SYMPHONY_REQUIRED_CHECKS=make-all;validate-pr-description
SYMPHONY_REQUIRED_CHECK_APP_ID=15368 for both
SYMPHONY_REQUIRED_CHECKS_STRICT=true
SYMPHONY_ENFORCE_ADMINS=true

HERDR_REPOSITORY=https://github.com/herdrdev/herdr
HERDR_REF=master
HERDR_SHA=ee5bfb5041bb3e4a49d591c72308aae3c81ecdde
HERDR_TREE=d2fc8428a9ce5be7e1d89a10b62be3e289b479dd
HERDR_PACKAGE_VERSION=0.9.5
HERDR_LICENSE=Apache-2.0 for the root package
```

GitHub's live branch and protection APIs established the Symphony facts. The local checkout was at `c5b29a8417ae1d82db6e438716c1425ad6889761`. Protected main has moved, so this evaluation uses the new live baseline. PR #61 merged the scanner governance and canonical implementation plan at the reviewed live SHA. Its head was `4039f9c80d3a771ff516b42cb58d73864be24eaf`. Both required checks succeeded on that PR head. `make-all` and its isolation/coverage jobs also succeeded on the exact merge SHA. A PR-description check was not observed on the merge SHA; the PR-head result is not represented as a merge-head result.

Sources: [Symphony branch](https://api.github.com/repos/JCSchoeman96/symphony/branches/main), [protection](https://api.github.com/repos/JCSchoeman96/symphony/branches/main/protection), [merge](https://github.com/JCSchoeman96/symphony/commit/86336d28671cfd6ac0a55c2ebe48094b8d8a8237), [Herdr commit](https://github.com/herdrdev/herdr/commit/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde), [manifest](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/Cargo.toml).

The organization also has separate `herdr-core`, `herdr-app`, Nix and example repositories. The evaluated implementation is the pinned `herdr` repository, including its vendored sources and lockfile where relevant. This report does not certify unpinned companion repositories or a released binary.

### Accepted Symphony authority

Read in precedence order:

1. [V4.1 Master Roadmap](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/docs/symphony-hardening-playbook-v4.1/V4_1_MASTER_ROADMAP.md), including AttemptLineage, RuntimeAttempt, source-control authority, recovery and workspace ownership.
2. [Unified Execution Roadmap](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/docs/SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md), current hardening ledger, authority index and scoped governance projections.
3. [Inventory freeze acceptance](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/docs/symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_ACCEPTANCE_2026-11-02.md), immutable packet and reconciliation.
4. [Scanner governance addendum](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/docs/symphony-hardening-playbook-v4.1/GATE2_SCANNER_GOVERNANCE_ADDENDUM_2026-11-03.md), policy and scoped projection.
5. [Canonical implementation plan](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/docs/superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md), especially C, D, E, H, I, J1, J3, K and O.

The frozen packet contains 115 inventory entries and 26 obligations. Its combined freeze digest is `1458bb041215c6268f2c69c01ed4198357e9561fbdc17a62e7288d0817b61911`. I independently recomputed these committed file identities:

```text
FREEZE_PACKET_BLOB=6cf92dbad8507d4e6c7553392b163fcac02b897d
FREEZE_PACKET_BYTES=683322
FREEZE_PACKET_RAW_SHA256=a651b1574ec0a186f6b4cd9548787cf9b67009f6692268ce5a8d0669d9d0636a
PLAN_BLOB=bdb2840e5ea4ca8c8912d6cada3287078bbb3c72
PLAN_RAW_SHA256=a1d5cdba65c19a09e86ed814a595e8bbae0c9dcfc97afe021ab67826db09ff68
SCANNER_ADDENDUM_BLOB=1371606b208da8df4c8bcc69387bb86153fec7a2
SCANNER_ADDENDUM_RAW_SHA256=8b3aade539270bed6c7a4647ff00e5aaf3bcb79a08cc0e5cc3a45a9eb45be34b
SCANNER_POLICY_ID=GATE2_V1_CANDIDATE_VALIDATION
SCANNER_POLICY_VERSION=1.0.0
SCANNER_POLICY_BLOB=72632e9f2d92d176668286016f2ed3dfda500d85
SCANNER_POLICY_SHA256=0d67fe1c0c532294dd3e946618d5bfd40c3d5ce6f50804e4bd20823ae5f756b7
```

The scanner amendment supplies previously unbound policy for OB-015 and OB-019 and LC-09/10. It does not select or authorize a scanner implementation. The plan is approved at planning level. Its persisted applicability still names the predecessor baseline and requires explicit successor rebinding. Observing the G00 merge and verifying bytes does not supply that human decision. No separate post-merge rebinding decision was supplied or found in the pinned repository.

The programme-level H-100 authorization and the Gate 2 task's H-100 execution prohibition are distinct scopes. Neither authorizes H-100 in this investigation. Gate 2 remains incomplete and implementation remains unauthorized.

### Relevant production contracts

- `RuntimeAttempt.Identity.allocate/3` creates an opaque runtime attempt ID and binds work item, lineage generation, responsibility and runtime profile. `same?/2` checks all five fields. RuntimeAttempt remains volatile and belongs to the orchestrator's running state. [runtime_attempt.ex](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/elixir/lib/symphony_elixir/agent_runtime/runtime_attempt.ex).
- AttemptLineage is durable retry/safety history, not a provider session. A retry allocates a new RuntimeAttempt. Host/operator rearm changes lineage generation and preserves exhausted history. The roadmap sections 6.12 and 6.13 define this distinction.
- `AttemptLedger.begin_attempt/3`, `bind_runtime_attempt/3`, `release_authority_fence/3` and the other writers preserve durable fencing. The current schema does not prove resource cleanliness. P01/P08 add that proof without permitting legacy release bypasses. [attempt_ledger.ex](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/elixir/lib/symphony_elixir/agent_runtime/attempt_ledger.ex).
- `Workspace.Ownership` and `OwnershipLedger.reserve_sync/2`, `transition_sync/4` supply trusted ownership. Runtime-writable markers cannot authorize deletion. Existing ownership does not itself prove a fresh writable view. [ownership.ex](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/elixir/lib/symphony_elixir/workspace/ownership.ex).
- `RuntimeIsolation.admit/3` denies unproven remote containment. `verify/2` and `evidence/2` bind verification to runtime identity. `CredentialBoundary.routed_port_env/3` constructs a restricted environment, but environment assignment alone does not prove bearer nondisclosure. [runtime_isolation.ex](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/elixir/lib/symphony_elixir/agent_runtime/runtime_isolation.ex), [credential_boundary.ex](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/elixir/lib/symphony_elixir/credential_boundary.ex).
- `CandidateRef` has immutable repository/base/candidate/PR/observed-head identity. SourceControl rereads candidate/check/review/merge facts. Herdr's terminal status cannot replace these facts. [candidate_ref.ex](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/elixir/lib/symphony_elixir/source_control/candidate_ref.ex).
- `RecoveryLedger` explicitly excludes runtime attempts, sessions, PIDs, credentials and workspace paths from restored work-control facts. P01/P08 require new recovery generations, fresh observation and quarantine when ownership or cleanup is ambiguous. [recovery_ledger.ex](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/elixir/lib/symphony_elixir/work_control/recovery_ledger.ex).

## B. What Herdr mechanically is

`CONFIRMED_FROM_CODE`. Herdr is a Rust terminal workspace manager with a long-lived server, local JSON control API, separate client protocol, PTY processes, a terminal parser, agent detection, native session integration, persistence, Git worktree operations, plugins and SSH transports. `AppState`/`TerminalState` describe state; `TerminalRuntimeRegistry` owns runtime handles; panes attach terminals into workspace/tab layouts. It is not an implementation of Symphony's work-control authority model.

Relevant modules are `src/server/headless/`, `src/app/api/`, `src/api/schema.rs`, `src/pane.rs`, `src/terminal/`, `src/persist/`, `src/integration/` and `src/remote/`. [Operation registry](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/api/schema.rs), [terminal runtime registry](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/terminal/runtime_registry.rs).

`NOT_RELEVANT` to Gate 2 enforcement: terminal rendering, pane geometry, graphics, clipboard UX and product update presentation. They matter to TCB size if bundled, but do not contribute authority or containment mechanisms.

Herdr's names such as `HookAuthority`, `Done` and managed-agent identity refer to terminal/integration behavior. They are not Symphony lifecycle authority, attempt identity, acceptance or completion proof. A process can truthfully be idle or have exited without its resource obligations or provider effects being resolved.

## C. Gate 2 seam analysis

### A. Attempt boundary

`CONFIRMED_FROM_CODE`. Linux `process_start_token(pid)` reads `/proc/<pid>/stat` start time. `live_pane_process_group(shell_pid, pid, start_token)` checks the same start time, rejects zombie/dead states, and requires terminal-session membership. `AgentJobTracker` retains the identified process across shell job control, distinguishes an exited background agent, and detects a different same-kind foreground process. It avoids treating a surviving wrapper as the agent. [linux.rs, functions at lines 670-711](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/platform/linux.rs#L670), [background_agent.rs, AgentProcess and AgentJobTracker](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/pane/background_agent.rs).

Source tests include `live_pane_process_group_follows_the_agent_process_not_its_job`, `live_pane_process_group_rejects_processes_outside_the_pane_session` in `src/platform/mod.rs`; and `held_agent_pid_reused_by_another_process_reports_exit`, `held_agent_exit_is_reported_while_its_wrapper_survives`, `same_kind_agent_reusing_the_held_pid_replaces_it` in `src/pane.rs`.

This is a useful diagnostic identity pattern. It is not a complete Gate 2 identity mechanism. PID/start-time checks are sampled reads, not retained kernel process handles. They do not by themselves detect same-process `exec`, bind boot identity, prove executable identity, or prevent replacement between observation and effect. The shell PID itself is not fully incarnation-bound by this function. P04 already plans boot/PID-start/UID/executable/cgroup/namespace/FD identity, so Herdr adds adversarial test cases rather than a replacement design. `UNKNOWN`: the plan does not specify the exact stable kernel-handle acquisition, verification, signaling and wait algorithm. Refinement must close that observation-to-effect race, whether through pidfds or another mechanically justified sequence. Herdr supplies no ready-made solution.

`CONFIRMED_FROM_CODE`. `App::start_agent` validates that a pane has an available shell, reserves managed-agent state and submits an encoded command into the shell. That is a terminal-input launch. It is not a trusted direct app-server exec with a one-use materialization channel. Terminal IDs are distinct from public pane coordinates, but `TerminalId::alloc` uses time plus a counter and does not represent an OS process incarnation. [agents.rs, start_agent](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/app/agents.rs#L144), [terminal/id.rs](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/terminal/id.rs).

`CONFIRMED_FROM_CODE`. `agent.wait` pins terminal ID, optional resolved name and agent kind. `agent.prompt` with a wait records a sequence before submission, observes post-submission activity and uses a state-change lower bound to avoid returning the old idle state as completion. `handle_deferred_agent_api_request` starts its completion waiter before submitting input, so failure to start the waiter has no prompt effect. Tests include `agent_prompt_waiter_spawn_failure_fails_before_submitting` in `src/app/api/agents.rs`. [wait.rs, prompt_agent and wait_for_resolved_agent](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/api/wait.rs#L177), [prompt submission](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/app/api/agents.rs#L84).

The claim of fully atomic prompt-and-wait would be too strong. `prompt_agent` prereads a mutable target, then the app resolves it again during submission; the returned identity check happens after the prompt effect. A name rebound between these steps may receive input before the caller detects the mismatch. This is an inferred race from the call ordering, not an executed exploit. `tests/cli/agents.rs::agent_wait_pins_the_original_terminal_when_name_is_reused` proves later wait pinning, not atomic submission. The same file explicitly tests successful prompt-wait while an earlier turn is already working, so success need not identify the newly submitted turn. `agent_wait_identity_matches` compares terminal/name/kind, not PID-start or a fresh attempt nonce. Its named-agent fallback even permits a missing current agent label. `wait_for_resolved_agent` can use transient event status or a released-agent final status, including a return built from the initial snapshot. Same-kind replacement in a surviving terminal is not mechanically excluded by this predicate. These semantics are acceptable for interactive coordination but cannot decide Symphony completion, retry or cleanup.

`CONFIRMED_FROM_CODE`. `PaneRuntime::drop` shuts down the PTY actor and normally calls `shutdown_pane_processes`. Linux `session_processes` enumerates processes with a matching session ID once. Shutdown escalates HUP, TERM and KILL with 250 ms grace periods and tests PID liveness. The direct-child wait flag avoids one reaped-child ambiguity. Failure after escalation logs a warning. [pane.rs, shutdown path](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/pane.rs#L1702), [Linux session enumeration and signaling](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/platform/linux.rs#L801).

`INFERENCE`. A later fork, descendant changing session, PID reuse between enumeration and signal, inaccessible proc entry or server crash can defeat this as a complete absence proof. No durable attempt resource obligation, fence retention or quarantine follows from the shutdown function. A successful PTY close or child reap cannot release a Symphony fence. Symphony already has a stronger Linux PID-namespace supervisor that tracks and reaps `setsid` descendants and retains its home/fence on unconfirmed stop. H-080B evidence explicitly records the lack of a safe post-timeout observer; P08 must provide fresh reconciliation rather than infer later death. See [H-080B containment evidence](https://github.com/JCSchoeman96/symphony/blob/86336d28671cfd6ac0a55c2ebe48094b8d8a8237/docs/symphony-hardening-playbook-v4.1/H-080B_IMPLEMENTATION_EVIDENCE.md#L77) and `elixir/test/symphony_elixir/app_server_test.exs`, including escaped-descendant and unconfirmed-stop cases.

Linux foreground discovery does impose scan/task/byte/PID budgets and has tests for overflow and new-child discovery. Those protect observation cost. Incomplete discovery must become `UNKNOWN` under Symphony, never an empty scope or clean result. No reviewed launch path installs Gate 2-style cgroups, namespaces, distinct holder/tool UIDs, mount controls or egress rules. Windows uses process creation-time and process-tree APIs; its presence does not establish the selected Linux proof. SSH bridges execute/control another host's Herdr daemon; remote attachment is not remote containment proof.

**Verdict:** adapt identity-checking and waiter-setup patterns in Symphony-owned helpers and tests. Reject Herdr's shell launch, terminal status and shutdown as AttemptBoundary or CleanupVerifier implementations.

### B. Workspace and resource lifecycle

`CONFIRMED_FROM_CODE`. `src/worktree.rs` constructs ordinary `git worktree add/list/remove` operations. It supports an existing local branch or creates one from the requested base. `worktree.open` can return an already-open workspace. Worktree membership records repository and checkout paths; session snapshots retain those records. Workspace closure and checkout deletion are separate operations. Removal preserves the branch, uses Git's dirty-check refusal, and supports explicit force. [worktree.rs](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/worktree.rs), [deferred worktree API](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/app/api/worktrees/deferred.rs), [API documentation](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/docs/next/website/src/content/docs/socket-api.mdx#L344).

There are useful race precautions. Pending creates/removes are keyed by checkout path with operation IDs. Completion handlers recheck membership/source identity before updating state. Restore has `restored_worktree_space_membership_preserves_unavailable_checkout_and_rejects_replacement`. These checks prevent stale interactive operations from silently attaching unrelated workspace state.

They do not establish a durable, trusted resource reservation before Git effects. In-memory pending-operation maps disappear on crash. A Git command can complete before its application event or snapshot is committed. Reopening a checkout is intended behavior, not a cross-attempt freshness guarantee. Path canonicalization sometimes falls back to the original path. Normal agent processes retain host filesystem privileges and Git metadata access subject to ordinary user permissions.

Herdr therefore gives Symphony checkout-management examples, branch-preservation semantics and stale-operation tests. It does not give any of these Gate 2 proofs:

- A fresh writable view for every RuntimeAttempt.
- Attempt-private HOME/XDG/cache/temp/provider state.
- Absence of previous-attempt authority or writers.
- A runtime-denied writable common Git directory.
- Byte/inode/device/mount/FD/backing-reference accounting.
- Verified cleanup or durable quarantine before new allocation.

P02 already specifies preallocated ext4 loop images, private mount namespaces, filesystem/inode identities, bounded tmpfs and read-only runtime `.git`. Replacing that with worktrees would remove required controls. Worktree separation is a source-organization convenience; agents sharing a checkout, user account, common Git directory or daemon remain able to affect shared resources.

**Verdict:** `REFERENCE` for stale-operation and branch-preservation tests. `REJECT` as an AttemptWorkspace or security boundary. No material contribution to the selected storage implementation.

### C. Runtime recovery

The following are different mechanisms, all confirmed in the pinned code:

- **Client detach:** disconnects a client while the server still owns PTYs/processes. It is not server restart or fresh authorization.
- **Cold restore:** loads saved workspace/pane/session facts and creates new runtimes. It can launch native resume commands.
- **Agent-native resume:** `agent_resume::plan` generates `codex resume <session-id>` for `herdr:codex` session references. It reuses conversation state, not the original PID.
- **Live handoff:** the old Unix server transfers PTY descriptors and runtime metadata to a new server using `SCM_RIGHTS`. Existing processes survive. The manifest includes child PID, terminal/input state and hook state. Waits, subscriptions, in-flight requests and client sockets do not survive.
- **Abrupt server death:** ordinary Rust drop cleanup is not guaranteed. Cold snapshots and discovered surviving processes do not prove containment or restore safe authority.

Sources: [SessionConfig default](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/config/model.rs#L265), [resume plan](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/agent_resume.rs#L199), [pane_restore_startup](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/persist/restore.rs#L813), [pending launches](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/app/agent_resume.rs), [handoff protocol](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/server/handoff.rs), [transferred runtime state](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/handoff_runtime.rs).

`resume_agents_on_restore` defaults to `true`, with 100 ms startup spacing. It is disable-able through `[session] resume_agents_on_restore = false`. `resume_agents_on_restore_defaults_on_and_parses`, `restore_plan_respects_opt_in_and_allowlist`, `native_agent_restore_defers_runtime_launch` and the disabled-restore assertion in `restore_carries_persisted_agent_session_metadata` cover the configuration and restore paths. Source review does not prove an external Codex version can successfully resume every recorded session.

**Compatibility:** default cold resume is incompatible with Symphony. The automatic native-resume behavior is disable-able, but this setting is insufficient to make the daemon a Gate 2 boundary. Shell restoration, saved metadata, manual control methods, global homes, and live handoff remain separate behaviors. Existing process survival cannot restore RuntimeAttempt, grant, materialization or egress authority. Discovered resources must be fenced, reconciled, cleaned and verified or quarantined. Any new authorized work needs a new Symphony attempt and grant.

**Verdict:** `REJECT` automatic native resume and live runtime handoff across authority-owner restart. `REFERENCE` only for distinguishing durable session facts from live runtime handles.

### D. Host control channel

`CONFIRMED_FROM_CODE`. `integration::apply_pane_base_env` injects `HERDR_SOCKET_PATH` and, when resolvable, `HERDR_BIN_PATH`. `apply_pane_launch_env` also injects `HERDR_ENV=1` and managed workspace/tab/pane IDs. It removes several inherited outer-agent identity variables, but this is not a credential environment allowlist. `portable-pty` command construction starts from inherited environment. Provider integrations use user configuration directories unless explicitly overridden. [integration/env.rs](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/integration/env.rs#L29), [pane launch environment](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/pane.rs#L183), [vendored environment construction](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/vendor/portable-pty/src/cmdbuilder.rs#L139).

The Unix API socket is restricted to mode 0600. That separates host users; it does not separate agents running as the same user. `src/api/server.rs::handle_connection` dispatches JSON requests without a Symphony attempt/grant/role capability check. Peer description for server-stop logging is attribution, not per-attempt authorization. The pane IDs in environment are routing hints, not capability restrictions. [API server](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/api/server.rs), [socket permissions](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/ipc.rs#L362).

The exact method registry exposes these capability classes:

- Workspace create/get/list/focus/rename/move/close and metadata reporting.
- Worktree list/create/open/remove, including caller-selected branch/base/path and force removal.
- Tab create/list/get/focus/rename/move/close.
- Pane split/move/swap/close, layout apply/export, input, text/key sending, read and process information.
- Agent start/prompt/wait/read/send-keys/rename and cross-agent targeting.
- Session snapshots and event subscriptions.
- Server stop/live-handoff/config reload/agent-manifest reload and SSH-agent registration.
- Integration install/uninstall.
- Plugin link/enable/disable/action invoke/pane operations/log reads. Plugin command actions spawn host subprocesses.

The pinned [operation registry](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/api/schema.rs#L44) is the complete method-name catalog. There is no generic `config.set` in it; configuration authority includes reload plus configuration/manifest/plugin file access available to the daemon's user. Remote API/client bridges transport control to another daemon. They do not attenuate it into a Gate 2 grant. [Plugin command spawn](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/app/api/plugins/runtime.rs#L119), [remote API bridge](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/remote.rs#L15).

`INFERENCE`, directly supported by dispatch and permissions: an untrusted same-user Codex process with a reachable socket can read sibling terminal data, send commands into sibling shells, start supported agents, manipulate checkouts and invoke enabled plugin actions, subject to their normal validation and daemon privileges. This is host-user orchestration authority, not automatically root authority. It is already too broad for Gate 2. No exploit was executed.

The acceptable architecture is a small host-owned mechanism behind Symphony's typed API. RuntimeAttempt receives no Herdr socket path, endpoint FD, bind-mounted socket, SSH-agent forwarding or generic control proxy. Merely unsetting the path is insufficient if the endpoint remains reachable through filesystem or inherited descriptors. Distinct UIDs, namespace visibility, FD allowlists and host-socket denial must enforce the boundary. Helpers can execute only the current Symphony decision and cannot choose work, identity, retries, reuse, publication, acceptance or Done.

**Verdict:** `REJECT` the broad socket and user-level control model. `ADAPT` only selected internal mechanisms behind the already-planned narrow host boundary.

### E. Events and reconciliation

`CONFIRMED_FROM_CODE`. `EventHub` keeps an in-memory sequence and 512 retained events. `events_after_checked` reports history loss and lock unavailability separately. Subscription batching drains retained events in order and raises `events_lost` before emitting a misleading partial stream. The error instructs clients to resubscribe and resync with `session.snapshot`. Sequence state is not durable across daemon restart. [event_hub.rs](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/api/event_hub.rs), [subscriptions.rs, poll_batch and subscription_events_after](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/api/subscriptions.rs#L282).

`ActiveAgentStatusChangedSubscription::poll_snapshot` compares event sequence before and after its pane reread, deferring snapshot-derived output when concurrent events appeared. Setup captures sequence before probing so events during subscription creation are retained. Tests cover setup-window events, metadata expiry, initial-state ordering and history loss. Particularly useful are `subscriptions_report_history_loss_before_sending_a_partial_stream`, `subscriptions_report_history_loss_before_initial_agent_status`, `lagging_subscription_closes_without_interrupting_other_clients` in `src/api/server/subscription_socket_tests.rs`, and `agent_status_subscription_prefers_setup_window_events_over_initial_snapshot` in `src/api/subscriptions.rs`.

This partially resembles Symphony's event-as-wakeup rule. It does not implement that rule universally. Agent waits use unchecked `events_after`, accept some transient event statuses and can construct success from a retained final-status event. A Herdr snapshot is authoritative about Herdr state only, and even that state includes agent-reported or screen-derived observations. Neither event nor snapshot supplies authority to continue a Symphony attempt.

`INFERENCE`. A Symphony adaptation should use an owner/recovery epoch plus monotonic revision, mark caches stale on disconnect/gap/restart, and require current host/provider rereads before effects. Sequence-before/after checks detect interference; they do not alone make an external provider read linearizable. Capacity/resource/publication/credential intent still needs durable sync before its external effect. Herdr's JSON snapshots and transient pending maps do not replace those ledgers.

The planned `SubscriptionManager` owns account registration, immutable credential generations and refresh barriers. It is not an event subscription bus. Herdr event code contributes no implementation of that credential manager, ProviderEffect ledger or SourcePublicationBoundary.

**Verdict:** `ADAPT` checked loss/resync and setup-window tests; `REJECT` event-status-derived lifecycle success and transparent retry after ambiguous effects.

### F. Evidence and observability

`CONFIRMED_FROM_CODE`. `src/logging.rs` records structured event/subsystem/outcome, request IDs, pane/workspace IDs, spawn PIDs, exits, failures and restore outcomes. Process information can include foreground jobs, arguments and CWD. `SessionSnapshot` stores workspace membership, pane CWD, agent names, session references, resume arguments and launch arguments. Optional screen history is separate and disabled by default. [logging.rs](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/logging.rs), [snapshot.rs](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/persist/snapshot.rs), [history default](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/config/model.rs#L1082).

`persist::io::save_json_to_path` writes a temporary file, syncs contents, replaces the target and syncs the parent directory. It intentionally follows configuration symlinks. That is useful desktop persistence, not a root-owned immutable evidence store or a transaction journal for external effects. [persist/io.rs](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/persist/io.rs#L49).

Herdr does not produce the planned evidence binding across grant, RuntimeAttempt, fence epoch, exact resource set, current verification generation, executable/profile identity and fixed CleanupVerifier. Logs and restored metadata cannot establish resource absence or bearer nondisclosure. Persisted argv, resume commands, plugin stdout/stderr and optional terminal history require secret analysis before any use in Symphony. The Linux process detector also reads `/proc/<pid>/environ` for agent hints; it should not be transplanted into ordinary diagnostics near credential holders. This is not evidence that it logs complete environments, but it is an extra secret-reading capability. [process_agent_hint](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/platform/linux.rs#L788).

One useful implementation pattern is bounded diagnostic pipe drainage. `remote::process::read_output` retains at most limit+1 bytes per stream and drains excess to a sink. `CancellablePipe` stops waiting for EOF after child exit, even when a descendant inherited the pipe. Deadline/cancellation handling reaps the owned SSH child. Tests include `diagnostic_capture_drains_flooded_pipes_with_bounded_memory`, `child_exit_drains_output_without_waiting_for_inherited_pipes`, and `cancellation_and_timeout_reap_child_with_blocked_pipes`. [remote/process.rs](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/src/remote/process.rs#L112).

The original SSH ownership policy deliberately preserves shared descendants. A Gate 2 adaptation must instead retain their resource obligations and verify the attempt scope. Bounded capture is not redaction, truncation is not successful evidence, and stopping reads is not cleanup proof. Fixed-schema filtering and synthetic-secret tests remain required.

**Verdict:** `ADAPT` bounded drainage and failure tests; `REFERENCE` structured diagnostic attribution; `REJECT` raw session/history persistence as Gate 2 evidence.

## D. Conflict analysis

### H1. Codex session restoration

**Confirmed, default enabled, disable-able.** Source and tests establish `codex resume <id>` planning after cold restore. It is incompatible with automatic Gate 2 continuation. Disabling native resume is necessary if experimenting with Herdr outside this evaluation, but does not qualify the daemon. No such experiment is authorized here. Adopt no automatic session restoration.

### H2. HERDR_SOCKET_PATH

**Confirmed.** Managed processes receive the endpoint and normally share the server user's access. The capability includes sibling input, launch, checkout mutation and host plugin execution. Mode 0600 is not an agent boundary. Remove the entire reachability and delegation path in any derived mechanism, including FDs and forwarded endpoints.

### H3. Worktree isolation

**Mechanism confirmed; the alleged security claim is not established.** The reviewed worktree code and API documentation describe ordinary Git checkouts. The repository's contributor instructions use "isolated worktree" for development organization. I found no accompanying OS security boundary in worktree creation. Do not attribute a stronger isolation promise to Herdr, and do not treat its checkouts as Gate 2 containment.

### H4. Trusted computing base

`INFERENCE`, based on inspected module/dependency structure:

1. **Embedding wholesale:** would add terminal parsing/rendering integration, PTY management, process detection, persistence/restore, socket protocols, plugins, provider hooks, Git command execution and remote transports to the trusted process or its reachable dependencies. The pinned snapshot has 461 files under `src` and 297 named package entries in `Cargo.lock`. These are repository/lockfile size indicators, not a count of reachable or exploitable TCB components. The resulting proof burden is large and unrelated to much of Gate 2.
2. **Trusted daemon:** gains an OS process boundary, but Symphony must trust everything that can change host resources, inject sibling input, restore processes, load plugins, or mutate config under that daemon's user. IPC validation and restart reconciliation are added obligations. Running the same broad daemon as a more privileged account would increase consequences. A separate daemon is not a small TCB merely because it has a socket.
3. **Selected mechanisms:** native Symphony implementations and adversarial tests can have zero Herdr runtime/dependency TCB addition. Only the new helper code and its already-selected OS interfaces enter the existing proof programme. If expressive source is copied, only the reviewed extraction and dependencies should enter, with provenance and requalification.

**Recommendation:** use option 3. Do not embed or run Herdr as a Gate 2 trusted subsystem.

### Additional conflicts

- **H5, live handoff preserves too much:** PTY/process/hook-state transfer across server replacement conflicts with non-restoration. Its `SCM_RIGHTS` machinery also conflicts with the selected pipe-only, no-SCM_RIGHTS runtime broker. A separate authenticated daemon handoff protocol is not justification to expose descriptor transfer to RuntimeAttempt.
- **H6, advisory status becomes authority:** hook reports and terminal detection can establish Herdr agent states. Neither can authorize legal lifecycle transitions, retries, acceptance or Done in Symphony.
- **H7, shared ambient state:** inherited environment, user provider homes and SSH-agent integration conflict with private attempt state and holder/tool separation.
- **H8, cleanup uncertainty is a warning:** Herdr's shutdown warning is insufficient where Symphony must retain fencing and quarantine.
- **H9, reconnect/retry is not effect reconciliation:** handoff loses in-flight coordination. A transport reconnect cannot authorize replay of provider requests, Plane mutations or publication effects.

## E. Obligation mapping

These are relevance assessments, not satisfaction claims. Contribution labels apply to the reviewed mechanism; conflicts describe adopting the corresponding Herdr behavior unchanged.

- **OB-001, fresh workspace. `HERDR_CONTRIBUTION=CONFLICT`.** Reopening/reusing worktrees conflicts with fresh attempt-writable state. Membership validation is a reference test only. P02 remains responsible.
- **OB-002, attempt identity/fence. `HERDR_CONTRIBUTION=PARTIAL_MECHANISM`.** PID/start-token checks and terminal identity pins help observation. They lack full Symphony identity, durable fencing and current-grant admission. P01/P04/P08 remain responsible.
- **OB-003, recovery. `HERDR_CONTRIBUTION=CONFLICT`.** Automatic resume/live handoff cannot restore Symphony authority. Lost-history handling offers a separate reference for reread discipline, not recovery authorization.
- **OB-004, writable containment. `HERDR_CONTRIBUTION=CONFLICT`.** Ordinary user worktrees/homes and ambient state do not provide finite private storage or complete cleanup accounting.
- **OB-005, exact isolation proof. `HERDR_CONTRIBUTION=REFERENCE`.** Process/session/PID-reuse tests are useful negative controls. No Herdr launch or test reviewed supplies executable-bound Gate 2 isolation proof. The broad socket would be a conflict if included.
- **OB-006, bearer nondisclosure. `HERDR_CONTRIBUTION=CONFLICT`.** Inherited environment, same-user control and process-environment observation cannot replace holder/tool separation or BP-01 through BP-19. No nondisclosure proof was found.
- **OB-009, grant/materialization. `HERDR_CONTRIBUTION=NONE`.** No Symphony-equivalent fresh host grant, immutable credential-generation lease or one-use holder materialization was found. Native resume must not be mistaken for one.
- **OB-012, network isolation. `HERDR_CONTRIBUTION=NONE`.** SSH transport and socket permissions do not enforce the selected Responses route or deny descendant egress. Host API reachability is an additional conflict, not a network-isolation mechanism.
- **OB-020, diagnostic/evidence safety. `HERDR_CONTRIBUTION=PARTIAL_MECHANISM`.** Structured attribution, bounded drainage and lost-history reporting can improve diagnostics. Raw status/history/logs remain unqualified evidence.
- **OB-021, capacity/resource limits. `HERDR_CONTRIBUTION=PARTIAL_MECHANISM`.** Observation budgets and bounded capture prevent some diagnostic resource exhaustion. They do not enforce attempt/aggregate bytes, inodes, processes, memory, CPU, time or IO reservations.
- **OB-025, secret-safe evidence. `HERDR_CONTRIBUTION=REFERENCE`.** Use its drainage failure cases when designing synthetic-secret tests. No reviewed Herdr mechanism proves secret-safe evidence; retained argv/history/plugin output can conflict.

No mechanism earns `POTENTIAL_IMPLEMENTATION` for an entire obligation. The small candidates below are implementation patterns requiring Symphony-native authority and proof.

## F. Candidate mechanisms and comparison with the plan

All Herdr sources below refer to `ee5bfb5041bb3e4a49d591c72308aae3c81ecdde`. All Symphony plan references refer to `86336d28671cfd6ac0a55c2ebe48094b8d8a8237`. Classifications apply to mechanisms, not products.

### M1. Incarnation-aware process observation

```text
MECHANISM=PID/start-token/session checks and replacement tests
HERDR_SOURCE=src/platform/linux.rs::process_start_token,live_pane_process_group;
             src/pane/background_agent.rs::AgentJobTracker
TARGET_SYMPHONY_SEAM=AttemptBoundary;AttemptResourceLedger;HostBoundary/native helper;CleanupVerifier diagnostics
CURRENT_PLANNED_MECHANISM=P04 HolderIncarnation and P08 exact scope verification
CLASSIFICATION=ADAPT
RECOMMENDATION=Eligible for existing Gate 2 qualification planning;implementation requires normal authority
```

**Why / what Herdr does better:** concrete tests distinguish actual agent exit from wrapper survival, job suspension, PID reuse and same-kind replacement. They can make Symphony qualification more adversarial.

**What it does worse:** sampled terminal-session identity is weaker than the planned boot/PID-start/executable/UID/cgroup/namespace identity and cannot prove complete scope death. Same-process exec and observation-to-effect races remain.

**Authority impact / delta:** none permitted. Observations must match the current Symphony attempt/grant/fence and may only reduce authority on mismatch. They cannot choose the current attempt or release its fence.

**TCB impact / delta:** small Symphony helper/test additions; no Herdr daemon or terminal dependency. **Implementation complexity delta:** small test/observation addition; no simplification of mandatory containment or cleanup. **Lifecycle impact:** replacement/unknown identity fences or quarantines; it never restores an old attempt. **Provenance/license impact:** retain a source-to-test design reference; copied code would require the obligations in section G. No direct code reuse recommended.

### M2. Register waiters before effects and reject stale pre-effect state

```text
MECHANISM=waiter setup before prompt effect; post-submission revision lower bound
HERDR_SOURCE=src/app/api/agents.rs::handle_deferred_agent_api_request;
             src/api/wait.rs::prompt_agent,agent_wait_matches
TARGET_SYMPHONY_SEAM=AttemptBoundary operation admission;native helper readiness;ProviderEffect observation ordering
CURRENT_PLANNED_MECHANISM=durable intent and acknowledgement before effects;identity-bound callbacks
CLASSIFICATION=ADAPT
RECOMMENDATION=Eligible for existing Gate 2 qualification planning;implementation requires normal authority
```

**Why / better:** waiter-allocation failure happens before input submission; a post-effect observation cannot accidentally reuse pre-prompt idle. The source test injects waiter spawn failure.

**Worse:** terminal input, agent status and event sequences do not identify an inference effect. Prompt+wait is not an atomic OS/process transaction and offers no durable effect record.

**Authority delta:** zero. Bind operation nonce, full attempt/grant/fence/recovery identity and expected revision. A result only reports the authorized operation. **TCB delta:** a small Symphony-owned state machine/test, no Herdr API. **Complexity delta:** small failure-path improvement; existing durable ledgers remain. **Lifecycle impact:** setup failure causes no effect; possible-send uncertainty stays unresolved and must not replay. **Provenance/license impact:** design citation only unless code is copied. No direct reuse of PTY prompt code.

### M3. Explicit event-loss failure and resynchronization

```text
MECHANISM=checked retained history;setup-window cursor;snapshot interference check
HERDR_SOURCE=src/api/event_hub.rs::events_after_checked;
             src/api/subscriptions.rs::poll_batch,poll_snapshot
TARGET_SYMPHONY_SEAM=host observation/event consumers;reconciliation;operator projections
CURRENT_PLANNED_MECHANISM=durable ledgers plus fresh observation and recovery generations
CLASSIFICATION=ADAPT
RECOMMENDATION=Eligible for existing Gate 2 qualification planning;implementation requires normal authority
```

**Why / better:** a concrete, bounded history-loss error prevents partial-stream success. Setup-window and lagging-client tests cover easy-to-miss races. **Worse:** process-local cursors reset on restart; unchecked wait paths and transient-event success remain; snapshots do not prove Symphony authority.

**Authority delta:** zero. Events invalidate observations or identify what to reread. Only current owning stores and external authoritative reads determine facts used by Symphony. **TCB delta:** no Herdr runtime; a small consumer protocol/test addition. **Complexity delta:** modest, with clearer gap/reconnect behavior; no new event platform warranted. **Lifecycle impact:** gap/disconnect/restart makes caches stale and prevents decisions until reconciliation. **Provenance/license impact:** cite source/tests; copying the small event store is not justified when the owner/epoch semantics must change.

This recommendation does not target the credential `SubscriptionManager`; it has a different responsibility.

### M4. Identity checks before resource cleanup

```text
MECHANISM=check an observed resource identity before deleting its locator
HERDR_SOURCE=src/ipc.rs::SocketFileIdentity,socket_file_identity,remove_socket_file_if_owned;
             src/app/api/worktrees/deferred.rs::operation_id and membership guards
TARGET_SYMPHONY_SEAM=AttemptResourceLedger;AttemptWorkspace;CleanupVerifier
CURRENT_PLANNED_MECHANISM=trusted ownership plus stable allocation identity and exact cleanup evidence
CLASSIFICATION=REFERENCE
RECOMMENDATION=Eligible P02/P08 test-design reference;do not copy cleanup code
```

**Why / better:** demonstrates why a path or public pane slot is not an ownership identity, and why late operation completion needs an operation ID. **Worse:** Unix socket cleanup performs metadata comparison followed by path removal. It is not an atomic compare-and-unlink; metadata follows symlinks and check/use replacement remains possible. Inode reuse and crash recovery need stronger context. Worktree pending maps are volatile.

**Authority delta:** none. Only Symphony's trusted owner authorizes destruction. **TCB delta:** zero for a design/test reference. **Complexity delta:** no new abstraction; extend existing P02/P08 adversarial tests. **Lifecycle impact:** mismatch means stop and quarantine, never delete a replacement or declare absence. **Provenance/license impact:** reference only. Do not copy the path-based function into a security-critical cleanup implementation.

### M5. Bounded, cancellable diagnostic drainage

```text
MECHANISM=concurrent bounded stdout/stderr capture;drain excess;cancel blocked IO
HERDR_SOURCE=src/remote/process.rs::read_output,CancellablePipe,wait_with_output_limit
TARGET_SYMPHONY_SEAM=HostBoundary/native helper;P08 diagnostic channels;CleanupVerifier observability
CURRENT_PLANNED_MECHANISM=bounded pipe-only protocol and fixed-schema secret-safe host evidence
CLASSIFICATION=ADAPT
RECOMMENDATION=Eligible for existing Gate 2 qualification planning;implementation requires normal authority
```

**Why / better:** tests flooded pipes and inherited pipe writers, while keeping memory bounded and avoiding an artificial timeout caused by a full pipe. **Worse:** limits are optional on other entry points; the original SSH policy intentionally leaves shared descendants; output capture provides no secrecy guarantee.

**Authority delta:** zero. Diagnostic completion cannot discharge process/resource obligations. **TCB delta:** small native helper logic; no SSH subsystem required. **Complexity delta:** modest IO-handling work, potentially fewer deadlocks and clearer timeout failure. **Lifecycle impact:** truncation, cancellation or missing observations remains explicit; cleanup uncertainty retains the fence. **Provenance/license impact:** design adaptation with source/test citation. A later decision to copy expressive Rust would require an extraction review and license record. No current `REUSE` recommendation.

### Planned seams with no useful Herdr implementation

- **SubscriptionManager:** no contribution to verified registration, refresh serialization, immutable credential generations or account selection. Keep Symphony-native.
- **ProviderEffect ledger:** no durable inference possible-send/effect reconciliation equivalent. M2 only informs setup ordering.
- **SourcePublicationBoundary:** worktree commands and plugins have no bounded publisher authority, separate publication intent ledger or exact candidate acceptance chain.
- **CandidateStage/validator:** no implementation of the accepted scanner policy, sealed object stage, safety evidence or source-only promotion rule.
- **AttemptWorkspace storage and CleanupVerifier:** Git and PTY operations cannot replace selected ext4/cgroup/namespace/resource-reference proof.

## G. Licensing, provenance and explicit rejects

### Licensing

`CONFIRMED_FROM_CODE/DOCS`. Root `Cargo.toml` declares Apache-2.0 and root `LICENSE` contains that license. Symphony is also Apache-2.0. No root Herdr `NOTICE` was found. Vendored code has separate licenses, including MIT `portable-pty` and its copyright notice; Windows packaging has its own ConPTY license/notice. Root licensing must not be generalized to every bundled dependency. [Herdr license](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/LICENSE), [portable-pty license](https://github.com/herdrdev/herdr/blob/ee5bfb5041bb3e4a49d591c72308aae3c81ecdde/vendor/portable-pty/LICENSE.md).

There is no `REUSE` recommendation. If Symphony later copies expressive Herdr source, Apache section 4 requires a license copy, prominent modification notices, retained applicable source notices, and any applicable upstream NOTICE attribution. No root NOTICE was found; preserve file-specific and bundled notices actually copied. MIT-derived code requires its copyright and permission notice. Patent and trademark terms still apply. Recheck the exact extraction's licenses and dependencies.

For any future extraction, record repository URL, full commit/tree, source paths and symbols, file/blob hashes, license/notice copies, copied ranges, changes and rationale, destination paths, dependencies, tests and qualification evidence. Attribution alone does not make a security-incompatible mechanism safe. An independent Symphony implementation should still cite the design evidence; do not label copied code an independent rewrite.

### Explicit rejects

1. Herdr as the authority kernel, dispatcher, retry owner, account selector, lifecycle owner, candidate acceptor, publisher or Done authority.
2. Whole-product embedding or a trusted broad Herdr daemon for Gate 2.
3. Runtime access to the Herdr socket, sibling terminals, plugins, integrations, remote control or host service operations.
4. Automatic Codex native resume, restored grants/credentials, or live handoff as authority continuity.
5. Git worktrees as isolation or proof of fresh attempt storage; workspace reuse under an old grant.
6. PID/session enumeration, child exit, PTY close or warning-only teardown as cleanup evidence.
7. Hook reports, terminal labels, screen matches or Herdr Done as lifecycle/completion evidence.
8. Broad environment inheritance, shared provider homes or SSH-agent forwarding into RuntimeAttempt.
9. Raw terminal history, launch/resume argv or plugin output promotion into durable Gate 2 evidence.
10. Blind mutation/provider replay after reconnect, timeout, lost response or server replacement.
11. Herdr worktree/source operations as a substitute for CandidateRef, sealed candidate validation or SourcePublicationBoundary.

These are architectural rejects for the Symphony threat model, not claims that the mechanisms are defects in Herdr's intended interactive product.

## H. Ranked recommendations and Gate 2 qualification planning

The supplied Master-level disposition permits these patterns in existing Gate 2 qualification planning. They are eligible for the current Gate 2 work, before acceptance; they are not deferred wholesale until after V1. This report records proposed negative controls, not implemented tests or evidence of passing qualification. Writing or executing tests remains subject to the normal package and implementation authority.

1. **M1, process replacement negative controls. P04/P08.** Plan cases where the actual agent dies while its wrapper survives, the PID is reused, another process of the same agent kind appears, the process leaves the expected session, or a suspended/background process exits or changes. Exercise Symphony's stronger HolderIncarnation binding across observation, effect, signaling and wait. The expected result is rejection of a stale or replacement identity, with fencing and quarantine when ownership or termination remains uncertain. No surviving wrapper, process name, PID or old start token can establish current authority. Herdr's PID/start-token/session implementation remains weaker than the planned Symphony identity and is not adopted.
2. **M3, event gap and resynchronization. P08/operator observation and existing reconciliation owners.** Plan retained-history overflow, disconnect/reconnect, owner restart, and events arriving during snapshot acquisition. The expected result is explicit loss/staleness, invalidation of cached observations and a fresh authoritative owner/read before any authority-dependent decision. A partial stream must not appear complete. Keep observation/recovery generations distinct from credentials and add no EventBus subsystem.
3. **M2, pre-effect waiter ordering. P04.** Plan observer/readiness setup failure before submission, stale pre-effect idle/completion state, operation-identity mismatch, and a lost result after a possible effect. Preserve the existing order: durable intent, bound operation identity, established observer/readiness, possible effect, then evidence and reconciliation. The expected result is no effect when required readiness setup fails; no earlier or unrelated turn can satisfy the operation; a possible-send or ambiguous effect remains unresolved without blind replay. This adds a test/invariant to existing provider-effect work, not Herdr prompt semantics or a new subsystem.
4. **M5, bounded diagnostic drainage. P08/native helper qualification.** Plan simultaneous stdout/stderr floods, retained-output limits with excess drainage, descendants retaining inherited pipe writers, cancellation, timeouts and child reaping while pipes misbehave. The expected result is bounded retained memory, bounded completion/cancellation under the qualified contract, explicit truncation or missing-evidence outcomes, and no deadlock caused by a full pipe. Bounded handling does not prove redaction. Pipe closure or child reap does not prove complete process/resource cleanup. Truncated diagnostics cannot silently become successful evidence. Synthetic-secret and cleanup proofs remain separate.
5. **M4, resource replacement cleanup tests. P02/P08, lower priority.** Plan replacement of the object at a recorded locator between observation and destruction, including stale operation completion and path/identity mismatch. The expected result is refusal to delete the replacement or certify absence; uncertain ownership retains quarantine and blocks reuse. Use stable Symphony allocation identity and trusted ownership. Herdr's path-based compare-and-remove implementation remains rejected for the security-critical cleanup path.

The source symbols and existing Herdr test references for each pattern remain in sections C and F. These planning cases refine proof of controls already required by the frozen obligations; they neither add a package nor relax an acceptance contract. Any later proposal that changes architecture, authority or frozen obligation semantics requires its own governance review.

## I. Overall recommendation

```text
HERDR_EVALUATION_STATUS=ACCEPTED_AS_REFERENCE_RESEARCH
HERDR_STRATEGY=SELECTIVE_ADAPTATION
DIRECT_CODE_REUSE_RECOMMENDED=NO
HERDR_DAEMON_IN_GATE2_TCB=NO
HERDR_AUTHORITY_DELTA=NONE
```

Herdr contributes several concrete race and IO-handling patterns with useful tests. It does not replace a Gate 2 package or materially reduce the required isolation, credential, cleanup, recovery or publication proof. The smallest safe use is to plan the ranked negative controls within existing Gate 2 qualification, then implement any authorized adaptation in Symphony-native code. Test-pattern planning is eligible now; implementation and execution still require their normal authority. Wholesale integration would increase trusted code and reconciliation obligations while requiring removal of core Herdr behaviors.

## J. Gate 2 planning consequence and limits of proof

```text
GATE2_PLAN_CONSEQUENCE=REMAIN_UNCHANGED
HERDR_ARCHITECTURE_CHANGE=NO
GATE2_ARCHITECTURE_AMENDMENT_REQUIRED=NO
GATE2_PACKAGE_TOPOLOGY_CHANGE_REQUIRED=NO
GATE2_PACKAGE_TOPOLOGY=UNCHANGED
FROZEN_ARCHITECTURE_AND_NINE_PACKAGES=UNCHANGED

HERDR_RUNTIME_INTEGRATION=DEFER_TO_REFINEMENT
HERDR_CODE_REUSE=DEFER_OR_REJECT
HERDR_NEGATIVE_CONTROLS=ELIGIBLE_FOR_EXISTING_GATE2_QUALIFICATION
HERDR_TEST_PATTERN_ADOPTION=PERMITTED_FOR_EXISTING_GATE2_QUALIFICATION_PLANNING
HERDR_TEST_PATTERN_ADOPTION_CONDITION=SUBJECT_TO_NORMAL_IMPLEMENTATION_AUTHORITY

PRIORITY_PATTERNS=
  1_PROCESS_REPLACEMENT_NEGATIVE_CONTROLS
  2_EVENT_GAP_AND_RESYNC
  3_PRE_EFFECT_WAITER_ORDERING
  4_BOUNDED_DIAGNOSTIC_DRAINAGE
  5_RESOURCE_REPLACEMENT_CLEANUP_TESTS

IMPLEMENTATION_AUTHORIZED=NO
PROVIDER_EXECUTION_AUTHORIZED=NO
H100_EXECUTION_AUTHORIZED_BY_THIS_EVALUATION=NO
REPOSITORY_GOVERNANCE_CHANGE=NONE
```

`REMAIN_UNCHANGED` refers to the frozen architecture, authority model and nine-package topology. It does not defer all test-pattern use until after V1. The current plan already specifies stronger identity, durable intent, private storage, host API restrictions, recovery generations and cleanup evidence. Section H makes the five patterns available to existing package qualification planning before Gate 2 acceptance. No Herdr mechanism replaces a planned Gate 2 component.

The previous blanket `DEFER_HERDR_IDEAS_TO_REFINEMENT` disposition is superseded by the split above. Runtime integration, daemon use, code reuse and new runtime abstractions remain deferred or rejected for this Gate 2 design. Existing qualification can use the research without importing those mechanisms or enlarging the trusted computing base.

### Research acceptance and authority provenance

The user supplied a Master-level disposition accepting the report as reference research and permitting test-pattern adoption for existing Gate 2 qualification planning, subject to normal implementation authority. `HERDR_EVALUATION_STATUS=ACCEPTED_AS_REFERENCE_RESEARCH` records that supplied disposition. It is not inferred from GitHub CI, a merge, or this investigator's recommendation. No separate decision identifier or exact decision timestamp was supplied; none is invented. This report update persists that disposition only in this evaluation artifact outside the repository. It does not amend repository governance, authorize implementation, qualify any component or pass Gate 2.

### Successor-baseline rebinding prerequisite

A fresh live GitHub branch read during this revision confirmed protected main at `86336d28671cfd6ac0a55c2ebe48094b8d8a8237`, tree `4c362c8800c3ebb75408d1af015184f5beb04d5a`. The persisted canonical plan still names the predecessor applicability baseline and requires explicit successor-baseline rebinding under G00. The supplied research acceptance does not supply that rebinding or a P01 implementation decision. Keep explicit rebinding to the verified post-PR-61 baseline as a prerequisite before considering P01 implementation authorization. This update does not claim G00 complete.

### Separate QualityLayer evaluation

The supplied review identifies the QualityLayer evaluation as the next input to consider before broader Gate 2 adjustments concerning representation and verification of the 26 obligations and their evidence. No QualityLayer evaluation or findings were supplied here. That investigation remains separate and unevaluated in this report; no conclusion, implementation authority or new dependency for the already-permitted Herdr test-pattern planning is inferred from it.

**Investigation provenance:** three bounded GPT 6 Luna delegations requested `reasoningEffort=xhigh`. The process-identity review completed and its claims were checked against source. The control/recovery delegation failed with `failed to load workspace requirements`. The workspace/event/evidence delegation failed with `failed to load configuration: /home/jcschoeman96/.codex-t3/codex-c/config.toml:324:1: duplicate key`. The root investigator directly inspected all six seams, including the domains whose delegations failed. This report does not claim three completed independent reviews. No provider configuration was changed to repair those failures.

**Proof limits:** source and test bodies were inspected; Herdr was not built or run, and no provider/Codex execution, exploit, host socket connection or isolation qualification was performed. Existing GitHub CI results are reported only for their exact observed Symphony SHAs. No Herdr test is claimed to have passed during this investigation. Negative findings mean no such mechanism was found in the reviewed paths, not a formal proof of absence from every companion project. Plane read-only search found no dedicated Herdr issue; no tracker record or governance state was changed. Source snapshots and this report were written outside the Symphony repository. Existing untracked work was preserved.
