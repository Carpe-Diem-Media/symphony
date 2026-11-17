# Native C02 development slice

This directory contains executable local progress for `H100_PC_PILOT_NATIVE_C02_01`.
It is synthetic-only. `holder-probe` is not Codex, an app-server, an authenticated
model client or a qualified SIWC protected holder. Production C02 remains refused.
No operational access-material input is implemented.

The governing P04 contract is
[`J3/J4`](../../docs/superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md#j3-materialization-and-process-isolation).
The owner pilot compatibility amendment selects only the future one-use Planner
profile. It does not activate Gate 2 or general legacy authentication.

## What executes

The C host is the only process that generates synthetic material. A credential-free
C guard forks before materialization. The bootstrap verifies permission, connects
to a one-use Unix socket, receives synthetic bytes, closes that channel and
`execveat`s the exact SHA-256-verified, sealed ELF image. Its explicit environment
has fresh HOME/CODEX_HOME, LANG and synthetic ACCESS_TOKEN only. Neither the guard,
Python controller nor Symphony receives material. Nothing writes it to a file,
argument, event journal or generic Symphony RPC.

The probe synchronously disables core dumps and dumpability, sets no-new-privileges
and installs x86_64 seccomp before reading material. Fork, exec, ptrace and socket
creation are tested and denied. The probe cannot create child processes. This
single-thread probe filter is not a deployable policy for Codex/Tokio.
It reports nonsecret readiness and always refuses inference. The ambiguous-effect
fixture exits after intent; it never invokes a provider.

The host checks SO_PEERCRED, parent PID/start time, executable hashes, sealed-image
hash, namespace inodes and cgroup identity against the selected synthetic guard.
These same-UID observations are not root-owned permission, distinct host UID,
LSM, private procfs, tool separation or operational host authentication proof.

## States, guards and durable effects

The existing C01 consumed grant and RuntimeAttempt remain the attempt authority.
The native journal records subordinate observations, not a second entitlement.
Every event carries their nonsecret binding digest and existing attempt ID.

1. `HOST_PERMISSION_VALIDATED` requires the private 0600 permit, selected profile,
   binding, attempt, exact guard PID/start, hashes and unexpired absolute deadline.
2. `BOOTSTRAP_CREATED` records the single fork. It cannot be retried by the guard.
3. `MATERIALIZATION_INTENT` requires host peer validation and an exclusive,
   file-and-directory-synchronized `consumed` marker before any delivery.
4. `SYNTHETIC_MATERIALIZED` records one delivery. Partial or unrecordable delivery
   retains consumption and produces ambiguity or quarantine.
5. `CREDENTIAL_CHANNEL_CLOSED` requires host-observed EOF. Only its synchronized
   marker permits the guard to accept `HOLDER_READY`.
6. `HOLDER_READY` proves probe controls and identity, not authenticated inference.
   `INFERENCE_INTENT` must be synchronized before the one fixture request.
7. `INFERENCE_REFUSED` is the probe's controlled result. Missing output or continuous
   output past the immutable deadline cannot become success.
8. `TERMINATION_REQUESTED` kills only the guard's exact unreaped direct child.
   `GUARD_REAPED` requires waitpid. The independent host requires its bootstrap
   pidfd to become readable before `TERMINATION_VERIFIED`.
9. `DISPOSAL_VERIFIED` is limited to this synthetic process/channel scope. It
   requires controlled refusal and both stop observations. It is not P08 disposal
   qualification. Missing observations enter `QUARANTINED` and retain evidence.

The controller and guard use parent-death signals with parent rechecks. The parent
loss regression kills a real proxy parent and independently observes both guard
pidfd death and bootstrap pidfd death. Deadline processing reserves stopping time;
continuous output cannot reset it. Restart refuses the existing consumed marker
before reopening materialization. Missing or uncertain state never grants retry.
A host crash leaves the marker and journal for quarantine, not automatic recovery.

`binding.json` supplied by C02 and the final `correlation.json` are synchronized
before the result is returned. The correlation contains the full existing grant,
RuntimeAttempt, source/configuration/role/profile/permission selection and native
observations. Attempt directories are created exclusively and cannot be reused.
Failure to retain exact correlation refuses the C02 result. C04 continues to own
final attempt evidence and never reports this probe as a completed model turn.

## Offline verification

Requires already installed Linux x86_64, C17 compiler, OpenSSL headers/libcrypto,
Python 3, memfd sealing, close_range, pidfd, seccomp and procfs. No installation,
privileged command or network fetch belongs to these commands. Run all commands
through the retained task's `deny-provider-sockets.py` wrapper, for example:

```sh
python3 /absolute/review-packet/deny-provider-sockets.py make -C native/pilot_c02 check
```

The native tests use disposable directories and local synthetic material. They
cover identity/permit refusal, replay, descriptor injection, bootstrap crashes,
partial delivery, absolute deadlines, parent loss, ambiguous fixture intent and
cleanup/observation/journal failure. Elixir integration tests are in
`pilot_holder_interface_test.exs`; they additionally prove C01 consumption and C04
quarantine with full source/configuration and RuntimeAttempt correlation.

The test-only C02 option must match its harness pin. Non-test builds compile no
native execution implementation and return `pilot_holder_boundary_unavailable`.
Ordinary non-pilot routed execution retains its previous launcher.

## Remaining operational dependencies

A separate [pinned Codex patch](../pinned_codex/README.md) now adds an early protected
entry to the actual standalone app-server. This directory supports it through
explicit `--pinned-codex` mode with a sealed nonsecret manifest at FD4. The manifest
closes before runtime/protocol use. Default probe behavior remains unchanged.
The full operational holder, broker and qualified host integration remain absent.
The installed trusted CLI is a different artifact. No readiness or login response
can substitute for actual authenticated inference proof.
P01/P02/P03/P04/P05/P08 qualification remains required: host permission/registration,
protected custody and materialization, revocation/lifetimes, holder/tool UID and
proc/mount/network/LSM separation, thread-compatible holder restrictions, provider
effect evidence and independent disposal/restart recovery. This slice implements
no working operational API for these absent components. Their installation,
enrollment and privileged qualification need separate owner authority.
Do not run this synthetic host with real material or use it as a pilot launcher.
