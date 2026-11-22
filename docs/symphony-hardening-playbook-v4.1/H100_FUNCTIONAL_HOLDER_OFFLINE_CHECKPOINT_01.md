# H-100 offline functional holder checkpoint

**Draft checkpoint. Slice C awaits hosted checks and independent review.**

This checkpoint records the offline Slice C implementation on top of the accepted Slice A and P05 fixture work. It preserves a successful synthetic Planner run, including two synthetic Responses requests, one brokered tracked-file read, verified process stop, C04 result readback in a fresh BEAM, and C01 replay refusal.

## Source identity

- Accepted base commit `2671732a9bf7f3264c7adc53cb7030286551df0e`.
- Initial checkpoint implementation tree `bd0f52ed8daa63b324eca2b024898dcf6b6f9127`.
- Corrected implementation-only tree `4f7a52c2b0552af296a10a07b5f6830554b203a0`.
- Corrected cumulative implementation diff SHA-256 `1ef343d28c63cdbebcfbbc22d506c7ed5ea1e255c5c3c14af80f9d982dc21034`.
- Pinned Codex 0.162.1 source commit `092d3acd6bec3e3a14bdc7e7a2810ab628ab759d`, tree `572cdecd45cd985f0ad80b63d8b86ffcb345f47a`.
- Current Codex patch SHA-256 `19c5491d4aeeea7f077667dbfc1a57993858c4a70a7bac7fc3f7d0ff6d2253e9`.
- Current patched Codex source tree `ee9e5f5611ec8372abe327bf9fe70df0002415e8`.
- Compiled holder SHA-256 `9d228faa5be1f64e95bb79c2954b5c673ab20cc565b9b37c70454d64f4c7edaa`.

The compiled holder and local evidence are retained outside Git.

## Verification and open requirements

The retained runs on the implementation tree passed all 13 routed Planner tests. The isolated repository run reported 2,618 tests, zero failures and six existing skips. All 16 earlier failure locations passed in a combined rerun. The earlier reservation-fence failure did not recur and its cause remains unresolved.

The independently reviewed schema correction completes group 2. The validator compares the complete prepared tool object with the serialization of the approved schema before changing the request ordinal or emitting an effect frame. The retained exact-source probe rejected all 40 malformed cases. The maintained Rust regression in `core/src/symphony_boundary/transport.rs` exercises both ordinals through the selected transport. It checks the ordinal, sequence and empty effect pipe after each rejected request, and checks that the pipe observer sees the first descriptor for a valid request. Adding that test changed the patched source tree. The offline rebuild produced the same holder bytes.

The current holder passed 20 routed tests and 40 Slice A/B compatibility tests. The routed suite includes normal and hyphen-prefixed attempts, contradictory final content refusal and fresh-BEAM C04 readback. It also checks that a completed or unresolved C01 attempt cannot be scheduled again.

The original R1 matrix uses these retained observations for the three continuation groups.

- Group 3. The routed controller exits after it writes the native acknowledgment and before it forwards that acknowledgment to the host. The native journal retains the acknowledgment, while the host journal retains pre-send intent. A second case drops the forwarded invocation permission after the native journal records it and leaves the host request ambiguous. Recovery closes admission and refuses replay in both cases.
- Group 4. The routed controller exits after sending synthetic headers, after sending response creation, after sending a completed tool-item frame, and after sending the final response body before its terminal frame. Recovery checks the observed stage in both journals, the request ordinal, and the quarantined C01 result in a fresh BEAM. A lost final stream keeps request 2 ambiguous and request 1 terminal.
- Group 7. Maintained component tests cover phase-specific expiration, continued incoming traffic after acknowledgment, permission revocation, retained home and exact cleanup binding. The native broker test expires or denies release of a started child. The routed missing-pidfd test records the actual tool PID, withholds release and leaves the result quarantined. Prior cancellation, parent-loss and write/sync fault evidence applies to the same implementation.

The initial draft reported 88.71% aggregate coverage. The schema-only update reported 88.72%. Both runs failed the fixed 90.00% hosted gate. The continuation adds maintained host-boundary, request-ledger and native lifecycle tests to the existing test partitions. Hosted results must be verified against the final PR head.

The approved encrypted independent backup destination was unavailable at verification. The complete local evidence archive passed extraction and hash readback. Its SHA-256 is `e2c0ff810406c03107d7797d9ffd6b18799485148d73f2daa84ab6f8fb6ed852`.

The evidence covers the selected synthetic profile. Production host qualification and authenticated provider execution remain outside this checkpoint. Merge requires separate approval after independent review of the exact final diff, the original requirements and required CI.
