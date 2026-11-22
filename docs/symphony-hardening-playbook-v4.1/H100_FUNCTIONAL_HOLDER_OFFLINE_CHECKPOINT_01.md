# H-100 offline functional holder checkpoint

**Draft checkpoint. Author-side verification is complete for the selected offline profile. Independent Slice C acceptance is pending.**

This checkpoint records the offline Slice C implementation on top of the accepted Slice A and P05 fixture work. It preserves a successful synthetic Planner run, including two synthetic Responses requests, one brokered tracked-file read, verified process stop, C04 result readback in a fresh BEAM, and C01 replay refusal.

## Source identity

- Accepted base commit `2671732a9bf7f3264c7adc53cb7030286551df0e`.
- Initial checkpoint implementation tree `bd0f52ed8daa63b324eca2b024898dcf6b6f9127`.
- Corrected implementation-only tree `4f7a52c2b0552af296a10a07b5f6830554b203a0`.
- Corrected cumulative implementation diff SHA-256 `1ef343d28c63cdbebcfbbc22d506c7ed5ea1e255c5c3c14af80f9d982dc21034`.
- Reviewed ledger correction commit `d72e03dc8ab423950c5dc99c227bad946eedacba`, tree `5cb1ec67f7f8e9fb9f1567224d3d0f995c81af78`.
- Reviewed two-file correction SHA-256 `043682c200eea1ca89fd5460730d4e46c095c4f554ff7731c45a6d35ef6d87cd`.
- Approved durable-close R2 implementation commit `1200fa1698645809918450221ea36304de04c8ca`, tree `c9a5c15a3a28f691a679ff127d321d79d100e901`.
- Reviewed four-file correction SHA-256 `5ef8bedefea4eca2c3f8088b10ba667ab1093db39fa844139baba90a84bbd841` against the prior published head `3e1afd8773462e66b87e02d681c2860119589a6f`.
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

The previous published head `09916f9` passed both required checks and reached 90.12% hosted aggregate coverage. The reviewed ledger correction passed 104 focused tests, 20 routed Planner tests and the full local run with 2,648 tests, zero failures, six existing skips and 90.08% aggregate coverage. Formatting, lint and Dialyzer also passed. The 90.00% threshold is unchanged. Both hosted checks must pass again on the published correction.

The ledger correction refreshes the journal and validates it under the existing append lock. It preserves one durable close event across concurrent or stale handles, refuses record updates after closure and leaves invalid journal bytes intact. For the original groups 3 and 4, all 12 Elixir process-loss cuts and six routed recovery checkpoints passed after the correction. Earlier native evidence remains applicable because the native implementation is unchanged. The author-side evidence now covers all nine original groups for the selected offline profile.

The approved durable-close correction requires a fresh read of the bound journal with closed admission and both terminal requests before AppServer publishes the original Codex completion event. It preserves a prior turn error if closure also fails. R2 uses the general stop handler to honor `defer_runtime_stop`. The routed AgentRunner fault fixture explicitly delegates stopping. The direct AppServer regression verifies stop before the original close error returns. The earlier run with delegation omitted remains in the evidence. The outer owner attempted a second stop and reported a containment timeout.

R2 passed 157 focused tests, 20 routed tests, four delegated close-fault cases, and the direct stop regression. The four fault cases verified cleanup, a failed C04 record in a fresh BEAM, and C01 replay refusal. The routed readback checked 19 journals and six recovery checkpoints. Formatting, specs, governance, strict Credo, development compilation and Dialyzer passed. The earlier durable-close candidate's full local run reported 2,652 tests, zero failures, six skips and 90.07% coverage. Fresh hosted `make-all` and `validate-pr-description` must pass on the documentation commit's tree, with aggregate coverage at or above 90.00%.

The approved encrypted independent backup destination was unmounted at verification. The local ledger review archive passed manifest and archive readback for all 175 payload files. Its SHA-256 is `7cf6bfa3c40442020a6ec75f8dcc3c112ff022f05cacb8830a5d1cb36e9bf6c5`.

Publication readback independently verified all 376 payload files in the retained R2 review archive against its manifest and their retained bytes. The archive is 323,603 bytes and its SHA-256 is `a451769038f851398d7c1ac4b84117543465bf30404cb3ced32951149304c9e9`.

The evidence covers the selected synthetic profile. Production host qualification and authenticated provider execution remain outside this checkpoint. Merge requires separate approval after independent review of the exact final diff, the original requirements and required CI.
