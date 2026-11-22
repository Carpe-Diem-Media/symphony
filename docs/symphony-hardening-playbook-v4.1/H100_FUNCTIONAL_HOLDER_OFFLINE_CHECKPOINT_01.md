# H-100 offline functional holder checkpoint

**Work in progress. Slice C acceptance is blocked.**

This checkpoint records the offline Slice C implementation on top of the accepted Slice A and P05 fixture work. It preserves a successful synthetic Planner run, including two synthetic Responses requests, one brokered tracked-file read, verified process stop, C04 result readback in a fresh BEAM, and C01 replay refusal.

## Source identity

- Accepted base commit `2671732a9bf7f3264c7adc53cb7030286551df0e`.
- Initial checkpoint implementation tree `bd0f52ed8daa63b324eca2b024898dcf6b6f9127`.
- Corrected implementation-only tree `4f7a52c2b0552af296a10a07b5f6830554b203a0`.
- Corrected cumulative implementation diff SHA-256 `1ef343d28c63cdbebcfbbc22d506c7ed5ea1e255c5c3c14af80f9d982dc21034`.
- Pinned Codex patch SHA-256 `af8e4d734f0a2a72aeb737eeb8321090a2b2d860d6e83165e053869b299b8163`.
- Patched Codex source tree `53e47b83083fcac8da2cd07656db3a27bb588b91`.
- Compiled holder SHA-256 `9d228faa5be1f64e95bb79c2954b5c673ab20cc565b9b37c70454d64f4c7edaa`.

The compiled holder and local evidence are retained outside Git.

## Verification and open requirements

The retained runs on the implementation tree passed all 13 routed Planner tests. The isolated repository run reported 2,618 tests, zero failures and six existing skips. All 16 earlier failure locations passed in a combined rerun. The earlier reservation-fence failure did not recur and its cause remains unresolved.

Six of the nine original Slice C acceptance groups are verified for the selected offline profile. The independently reviewed correction completes group 2. The validator compares the complete prepared tool object with the serialization of the approved schema before changing the request ordinal or emitting an effect frame. The exact-source probe rejected all 40 malformed cases, and the rebuilt holder passed the 13 routed tests and 40 Slice A/B compatibility tests. The corrected implementation also passed the isolated repository run with 2,618 tests, zero failures and six existing skips.

The initial draft head reported 88.71% aggregate coverage against the required 90.00%. The hosted gate must pass on the final candidate before acceptance can be considered.

Three original groups remain partial.

- Group 3 needs integrated native acknowledgment and recovery evidence after a durable acknowledgment is present but host handoff is uncertain.
- Group 4 needs later response-stream process-loss evidence, including the gap between headers and response creation, completed tool items and the final stream.
- Group 7 needs phase-specific expiry, permission revocation and process-stop evidence, including missing pidfd and retained-home cases.

The approved encrypted independent backup destination was unavailable at verification. The complete local evidence archive passed extraction and hash readback. Its SHA-256 is `e2c0ff810406c03107d7797d9ffd6b18799485148d73f2daa84ab6f8fb6ed852`.

The evidence covers the selected synthetic profile. Production host qualification and authenticated provider execution remain outside this checkpoint. Merge requires separate approval after independent review of the exact final diff, the original requirements and required CI.
