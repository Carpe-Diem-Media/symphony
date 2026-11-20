# Pinned standalone Codex holder

This patch builds the actual `codex-app-server` target from Codex 0.162.1, commit
`092d3acd6bec3e3a14bdc7e7a2810ab628ab759d`, tree
`572cdecd45cd985f0ad80b63d8b86ffcb345f47a`. It retains the full existing library and
ordinary entry path. It is a partial protected holder, not operational SIWC custody.
Production Symphony C02 still refuses execution until its host dependencies qualify.

## Slice A compilation checkpoint

The 39-entry offline source authority includes strict session construction and
its service consumers. The patch has an explicit schema2 synthetic feature,
immutable context validation, a real ThreadManager thread constructor and a
bridge to the existing core turn-input operation. Standard services are absent,
not constructed and shut down. Schema1 retains its earlier refusal contract.

Compilation and thread creation do not establish a functioning turn. The actual
turn-input implementation still unconditionally accesses the standard extension
registry in `core/src/session/turn_input.rs`. That file is outside the approved
39-entry inventory. The strict representation cannot satisfy this access. The
candidate must remain blocked until an independently authorized correction and
actual failed-terminal/stop regressions close this consumer dependency. No dummy
registry or duplicate turn-admission path is supplied to conceal it.

The previously accepted patch SHA-256 is
`59a9d0ebabd18de96f7f6552b307183fb11bc091b1152b04aef2c34f1255148a`, with patched
tree `39d3926e6c2a528c3039c2ff9368c1858b1d7f78`. Preserve those historical bytes.
The current `upstream.json` identifies the distinct Slice A draft patch.

A delegated formatter in this task invoked rustup outside the required denial
wrapper. It reported downloading seven Rust 1.95.0 components, and toolchain
files with task-time creation metadata were observed. Its exit and completion
were not captured. This violated the offline constraint. The retained incident
record must accompany review; no rollback was authorized or attempted. Further
checks use the existing stable binaries explicitly through the denial wrapper.

## Selected entry and lifecycle

The first operation in standalone `main` is `symphony_gate2::try_run`. A selected
`--symphony-*` launch never falls through to arg0, clap, configuration, environment
services, telemetry or generic MessageProcessor construction. The accepted exact
synthetic launch form is `--symphony-pilot-holder BINDING ATTEMPT`.

1. Synchronous entry installs zero core limits, non-dumpability, no-new-privileges
   and Linux x86_64 seccomp. Unavailable controls exit 78 with a stable code.
2. FD4 must hold a bounded, fully sealed nonsecret manifest. It binds the existing
   C01/RuntimeAttempt digest and attempt reference, exact executable SHA-256,
   selected synthetic profile and absolute CLOCK_MONOTONIC deadline. Unknown fields,
   identity drift, expiration or unexpected descriptors refuse. FD4 closes before
   runtime creation. Stdio must be pipes. No source or credential file is loaded.
3. Fresh HOME/CODEX_HOME must be empty private owned directories. Only synthetic
   material is accepted. Existing native bootstrap still forks before delivery,
   keeps the resident guard credential-free, closes its access channel and execs
   the exact sealed holder image with an explicit environment.
4. Kernel proof denies fork, exec, ptrace, network socket creation and process clone.
   Only exact pthread clone flags are permitted. The high-word check is at offset20
   of seccomp_data, within args[0], not the child stack at args[1]. clone3 returns
   ENOSYS for glibc fallback. A real Tokio worker must execute before native readiness.
5. Native readiness reports process controls and `qualified_host=false`. It is not
   host, authentication or inference readiness. The existing guard journals it only
   after independently observing credential-channel closure.
6. Initialize uses the pinned upstream InitializeParams/InitializeResponse types.
   In schema1, every other request returns `SYMPHONY_HOST_UNQUALIFIED` and stops. There is no
   provider, tool broker, auth refresh, local Child, hook, MCP, nested agent, snapshot,
   installer or model-refresh service in this selected branch. No denied request
   can reach generic startup. Configuration is immutable for the process lifetime.
7. Native guard records `CODEX_INITIALIZED_NOT_AUTHENTICATED`, then requests a thread
   and observes refusal. The existing intent event is synthetic intent only. No
   inference is performed. Continuous-output and ambiguous-effect cases are explicit
   synthetic manifest fixtures, never provider interactions.
8. The original absolute deadline and stopping reserve remain in force. Hash reads
   and protocol processing check the same deadline. The guard kills/reaps only its
   exact child; the independent host requires pidfd death. Uncertain disposal
   retains consumption, evidence and quarantine. Restart cannot materialize again.

The manifest is generated from the synthetic permit by the development guard.
It is not an authenticated qualified host manifest. The schema1 entry only
runs its earlier refusal path. Schema2 selects an offline synthetic lifecycle;
neither profile nor its test manifest authorizes live execution.
The existing C02 full binding, C01 one-use allowance and C04 terminal persistence
remain the attempt authority. No second RuntimeAttempt is allocated.

## Build and offline verification

Use the task's retained outbound-denial wrapper for compilation and tests. Source
acquisition and locked dependency retrieval are separate owner-authorized build
inputs. No installation script or package installation is part of this recipe.
`build.py` requires the exact upstream commit/tree and canonical worktree. Its
Git subprocesses use `/usr/bin/git` and a fixed environment without inherited Git
selectors or global/system configuration. A redirected local `core.worktree`
refuses admission. Ordinary linked worktrees remain supported.

Admission reads filesystem bytes, symlink targets, entry types and executable
modes against tree objects independently of index flags. It rejects missing,
changed, unsupported and unexpected files, including ignored untracked files.
The patch digest and resulting tree are pinned in `upstream.json`. A disposable
index reconstructs the patch tree before application; the source index and its
flags remain untouched. This adds Git objects but makes no index repairs.
The exact validated patch bytes are then applied to the same verified checkout.
Actual patched files must match the pinned patched tree before compilation.

The build progresses through `UPSTREAM_VERIFIED`, `PATCH_RECONSTRUCTED` and
`PATCHED_SOURCE_VERIFIED`. Any refusal exits without compilation or repair. Failed
application/build bytes remain available for inspection; the recipe never resets,
cleans or retries a checkout. Use an exclusively controlled source directory for
the duration of verification and compilation. This procedure does not freeze a
worktree against concurrent writes by its owner.

Run the admission regressions with the same outbound-denial wrapper:

```sh
python3 /absolute/review-packet/deny-provider-sockets.py \
  /usr/bin/python3 -I native/pinned_codex/tests/test_build_source.py
```

```sh
python3 /absolute/review-packet/deny-provider-sockets.py \
  python3 native/pinned_codex/build.py --source /absolute/clean/pinned/codex
python3 /absolute/review-packet/deny-provider-sockets.py \
  make -C native/pilot_c02 all
PINNED_CODEX_BINARY=/absolute/pinned/codex/codex-rs/target/dev-small/codex-app-server \
  python3 /absolute/review-packet/deny-provider-sockets.py \
  /usr/bin/python3 -I native/pinned_codex/tests/test_holder.py
```

The pinned release's lockfile still declares 161 local workspace packages as 0.0.0.
The retained patch reconciles only those versions to 0.162.1, with no external
package/checksum/source changes. The R1 development compiler was Rust1.98.1;
upstream requests1.95.0. No new toolchain was installed in that earlier build.
This difference is retained
in build evidence and is not an operational reproducibility qualification.
The build uses dev-small and optimizes SHA2 to keep exact self-identity verification
inside the existing finite budget. No timeout or admission rule is relaxed.

Tests exercise the actual built binary, not holder-probe. They cover native/Tokio
startup, sealed manifest and identity refusal, actual denial of seccomp installation,
process/tool/auth/config/turn rejection, bootstrap errors, parent loss, finite
termination, ambiguous cleanup and ordinary version-path compatibility. Existing
probe tests remain only regressions for the accepted earlier slice.
The Elixir interface suite selects the real artifact with `PINNED_CODEX_BINARY`;
its three native cases then prove C01/C04 correlation and refusal with that binary.
`PINNED_CODEX_EVIDENCE_ROOT` optionally retains each test attempt outside disposable
fixtures, including complete nonsecret binding/correlation and a C04 state observation.

## Outstanding controls

No authenticated inference is implemented or claimed. P01/P02/P03/P04/P05/P08 host
permission, protected custody, registration, lifetimes/revocation, distinct holder,
guard/tool UIDs and groups, private proc/hidepid, qualified AppArmor/mount/network
policy, external functional broker, Responses transport and independent disposal
remain unqualified. C03's operational PID-namespace proof is unchanged; these
synthetic tests do not substitute for it. Swap/core-collector/hibernation host
qualification is also not established by this build.

The schema1 branch refuses before thread/turn execution. Schema2 does not enable
provider egress and remains blocked before the required core terminal outcome. The installed ordinary Codex CLI is untouched. No signing, installation,
enrollment, publication, resource adoption, Gate2 activation or live pilot is implied.


### Reproduction and evidence limits

`build.py --source /absolute/clean/pinned/source --synthetic-functional` selects
the schema2 feature only after the same source-byte and patched-tree checks.
Use the explicit existing compiler, offline cache and outbound-denial wrapper
recorded in the retained command evidence. The standalone protected runtime uses
the pinned upstream 16 MiB worker stack budget. A prior default-stack binary
aborted on turn submission; its failed output and identity remain evidence.

`test_functional_session.py` executes the actual binary selected explicitly by
`PINNED_CODEX_BINARY`. Every case creates a new disposable source, binding and
attempt. Positive assertions require real thread and turn identifiers, a core
error, failed terminal status, no final answer and positive pidfd stop evidence.
Negative cases cover context drift, unsupported schema, expiry and protocol
mutation/replay. Missing deterministic cancellation coverage and an absent
feature-disabled executable are reported as blocked checks, never passing proof.

The schema2 direct-binary fixture does not exercise native host materialization
or C01 dispatch consumption. Schema1 native tests remain compatibility evidence.
Full schema2 bootstrap/host integration, retained C01 consumption and namespace
stop proof remain outstanding. Counter unit controls prove recorder wiring only;
zero counters on a path that never reaches the client do not prove client-entry
coverage or authenticated inference.

The crate-private state re-export and two standard-service test-fixture migrations
preserve the existing fixture assertions. Normal non-selected behavior retains
standard service construction. `Deref`/`DerefMut` compatibility may still panic
if strict execution touches standard fields; that is a known defect, not an
accepted guard. No functional Slice A acceptance or operational qualification is
claimed by this checkpoint.
