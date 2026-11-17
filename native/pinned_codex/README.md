# Pinned standalone Codex holder

This patch builds the actual `codex-app-server` target from Codex 0.162.1, commit
`092d3acd6bec3e3a14bdc7e7a2810ab628ab759d`, tree
`572cdecd45cd985f0ad80b63d8b86ffcb345f47a`. It retains the full existing library and
ordinary entry path. It is a partial protected holder, not operational SIWC custody.
Production Symphony C02 still refuses execution until its host dependencies qualify.

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
   Every other request returns `SYMPHONY_HOST_UNQUALIFIED` and stops. There is no
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
It is not an authenticated qualified host manifest. The standalone entry only
runs a refusal path. Neither it nor its test manifest can authorize a real turn.
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
package/checksum/source changes. The installed development compiler is Rust1.98.1;
upstream requests1.95.0. No new toolchain was installed. This difference is retained
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

The selected branch refuses before thread/turn execution and cannot enable provider
egress. The installed ordinary Codex CLI is untouched. No signing, installation,
enrollment, publication, resource adoption, Gate2 activation or live pilot is implied.
