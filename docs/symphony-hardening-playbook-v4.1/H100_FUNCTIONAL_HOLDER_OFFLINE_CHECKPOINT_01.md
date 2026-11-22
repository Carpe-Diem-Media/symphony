# H-100 offline functional holder checkpoint

**Work in progress. Slice C acceptance is blocked.**

This checkpoint records the offline Slice C implementation on top of the accepted Slice A and P05 fixture work. It preserves a successful synthetic Planner run, including two synthetic Responses requests, one brokered tracked-file read, verified process stop, C04 result readback in a fresh BEAM, and C01 replay refusal.

## Source identity

- Accepted base commit `2671732a9bf7f3264c7adc53cb7030286551df0e`.
- Implementation tree `bd0f52ed8daa63b324eca2b024898dcf6b6f9127`.
- Cumulative implementation diff SHA-256 `6927314d2e311a951d33b18876c57b92241e0e2688e1fa5bc854e25571ae0090`.
- Pinned Codex patch SHA-256 `f23f54c25fa6d09d18fb01543484e334d99e6426ebf822d235c38b7c8019c60e`.
- Compiled holder SHA-256 `f326bbbbbc3cbf6d9a9f843eba112a14ad7d83e77117cd327ef4f7f39d70c854`.

The implementation diff covers 25 source, test and build-definition paths. This document is a separate commit. The compiled holder, journals, manifests, command logs and evidence archive are retained outside Git.

## Verification and open requirements

The retained runs on the implementation tree passed all 13 routed Planner tests. The isolated repository run reported 2,618 tests, zero failures and six existing skips. All 16 earlier failure locations passed in a combined rerun. The earlier reservation-fence failure did not recur and its cause remains unresolved.

Five of the nine original Slice C acceptance groups are verified for the selected offline profile. Group 2 is blocked on this source checkpoint. The prepared-request validator accepts an `exec_command` tool when `parameters` is a string and advances the request ordinal. A later local correction has a separate source identity and awaits independent review for integration into this branch.

Three original groups remain partial.

- Group 3 needs integrated native acknowledgment and recovery evidence after a durable acknowledgment is present but host handoff is uncertain.
- Group 4 needs later response-stream process-loss evidence, including the gap between headers and response creation, completed tool items and the final stream.
- Group 7 needs phase-specific expiry, permission revocation and process-stop evidence, including missing pidfd and retained-home cases.

The approved encrypted independent backup destination was unavailable at verification. The complete local evidence archive passed extraction and hash readback. Its SHA-256 is `e2c0ff810406c03107d7797d9ffd6b18799485148d73f2daa84ab6f8fb6ed852`.

The evidence covers the selected synthetic profile. Production host qualification and authenticated provider execution remain outside this checkpoint. Merge requires separate approval after independent review of the exact final diff, the original requirements and required CI.
