# H-100 functional Codex holder offline Slice A checkpoint

## Source and authority

Publication task `H100_PC_SLICE_A_CHECKPOINT_PUBLICATION_01` preserves the
implementation from `H100_PC_FUNCTIONAL_HOLDER_SLICE_A_OFFLINE_01`. Its source
authority is the approved R1 plan and the extensions through the 43-entry
Routed Schema2 Closure inventory. Master Gate review of this publication is
pending.

```ini
PROTECTED_BASE_SHA=6bd3931e3f04b586ea5f7218c020a7788b4cb5cf
PROTECTED_BASE_TREE=8f8d717f06d760054bb1cae8e6f11fbbc25db471
IMPLEMENTATION_HEAD=19d8c116b48107eeab011ad2577d725124656920
IMPLEMENTATION_TREE=5f7653fe3961511d8f3718056460fbcad013ba5f
CORRECTION_DIFF_SHA256=9f8c39d2a4e17be2f21da59ff214d5becd861a0152e22f278c05644681c1c943
CUMULATIVE_DIFF_SHA256=103401d6e2d6e769f6a9da084c80eca2428c14eeb0e7f7fbc5b05436d8160f19
CODEX_VERSION=0.162.1
CODEX_UPSTREAM_COMMIT=092d3acd6bec3e3a14bdc7e7a2810ab628ab759d
CODEX_UPSTREAM_TREE=572cdecd45cd985f0ad80b63d8b86ffcb345f47a
CODEX_PATCH_SHA256=cf868ca409ad4d248c42cf97d293f53a419b0ad295e27f547dd45ccee4284e4b
CODEX_PATCHED_TREE=a085cec1ebf2a9592d8fe7dc54d57f519f08b2bf
CODEX_EXECUTABLE_SHA256=973a79cf4b70f36cac273cbe9af70b46c40418b3ba7db05d07bbe3aafa00899f
```

The implementation diff covers 13 Symphony paths. Reapplying both versions
of the embedded patch to the pinned upstream tree confirms 24 newly touched
upstream paths and an update to the existing `app-server/src/symphony_gate2.rs`
patch. All 25 changed upstream paths are authorized. The inherited patched
contents of `Cargo.lock` and `app-server/src/main.rs` match the baseline.

## Observed offline behavior

- The standalone holder starts a real Codex thread and turn. Core emits
  `SYMPHONY_PROVIDER_BOUNDARY_UNAVAILABLE` with `willRetry=false`, then
  `turn/completed` with `status="failed"` and the same thread and turn IDs.
  There is no final answer or successful C04 result.
- Direct probes refuse authentication, Responses HTTP, WebSocket entry and
  prewarm, retry and fallback before provider effects. Positive detector
  controls register effects locally. Poisoned configuration, hook, plugin,
  skill and MCP fixtures exercise the protected path without starting those
  services. Kernel checks and the canary fixture provide process evidence.
- The active-turn interrupt produces a real `interrupted` terminal. The
  routed synthetic stop check correlates guard reaping, host PID observation,
  closed channels and synthetic disposal to the consumed C01 attempt.
  A missing stop observation quarantines the attempt even after a real
  failed terminal. The ledger and runner deny replay. C04 remains
  noncompleted in all routed schema2 cases.
- The retained matrix reports 23 actual-binary and seven focused Rust passes.
  The final routed run passed four schema2 and three schema1 tests with exit
  zero. Formatting, strict Credo and Python syntax checks also passed.
  The prior packet records upstream Clippy warning provenance. The broad
  historical suites and hosted checks are separate evidence.

## Evidence and reproduction

The durable evidence archive is `H100-SLICE-A-ROUTED43-FINAL-REVIEW.tar.gz`
with SHA-256 `94cdc38519e5f5aec7cb46b85a197b9c801dcd2e8db9a3ec128d1c96077bc9cd`.
It contains the exact diffs, `AUTHORIZED_SOURCE_INVENTORY_43.json`,
`REVIEW_IDENTITIES_AND_RESULTS.json`, and
`ROUTED_CORE_AND_STOP_OBSERVATIONS.json` with matching event and stop journals.

Raw `sha256sum` and `wc -c` checks exited zero. Both the original and
transferred files match the retained inventory.

- `commands/focused-final.log`, 10,918 bytes,
  `5b50c91d3b20a15ec6e67e1fcae70a7180634a02456c56e89b5fd1384b13e762`.
- `commands/focused-final.json`, 1,968 bytes,
  `016e555a49c0ac7eda262b4d2f0389cb05fc3c490bdc4f18bee708de2b03a5ab`.

Use the argv, working directory and exit code in the command JSON to
reproduce the focused run with the outbound-denial wrapper, pinned
executable and synthetic fixture selection. The included prior archive
`prior-41-review.tar.gz`, SHA-256
`0d4794267bc40e437964a2cb7e1e2de089892beda3790c7dba7061e56a22301c`,
contains the offline Cargo build inputs, compiler output and earlier
binary/Rust commands. Build reproduction requires the exact pinned upstream
checkout and offline dependency cache. The executable is retained separately
under its digest. The evidence archive, runtime directories and binaries
are outside Git.

## Operational boundary

P01/P02/P03/P04/P05/P08 qualification remains separately governed. It includes
host authority and credentials, protected-holder and tool process separation,
PID namespace termination, and disposal and retained evidence qualification.
The synthetic stop proof covers the fixture's process and channel evidence.
Slice B tool brokering and Slice C provider transport remain outside this
checkpoint. Independent Master Gate review is required before any merge
decision. Automatic merge is prohibited.

```ini
OFFLINE_SLICE_A=FUNCTIONAL_VERIFICATION_COMPLETED
H100_PROGRAMME_ACCEPTANCE=NOT_GRANTED
OPERATIONAL_HOST_QUALIFICATION=NOT_GRANTED
REAL_CREDENTIAL_CUSTODY=NOT_QUALIFIED
LIVE_PROVIDER_EXECUTION=NOT_AUTHORIZED
GATE2_ACTIVATION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```
