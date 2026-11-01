# Gate 2 attempt-boundary proposal

Status: non-authoritative proposal and design history. The previous proof route has become unsuitable for the V1 objective. This document proposes a replacement; the replacement itself still requires evidence and approval. It does not change programme authority, runtime authority, trusted evidence, acceptance criteria, or execution authorization. See [the methodology authority boundary](../README.md).

```text
STATUS=PROPOSAL_ONLY
GATE_2_STATUS=INCOMPLETE
GATE_2_ACCEPTANCE_CRITERIA_CHANGED=NO
SCANNER_POLICY_CHANGED=NO
EXHAUSTIVE_PARSER_CLOSURE_PROPOSED_REQUIRED=NO
EXACT_SQLITE_TEARDOWN_CAUSALITY_PROPOSED_REQUIRED=NO
RETAINED_TRACE_ROLE=DIAGNOSTIC_ONLY
PROPOSED_PROOF_BOUNDARY=ATTEMPT_LOCAL_CONTAINMENT + BOUNDED_AUTHORITY + BOUNDED_STORAGE + HOST_VERIFIED_TEARDOWN + NEXT_ATTEMPT_INDEPENDENCE
IMPLEMENTATION_AUTHORIZED=NO
PRODUCTION_POLICY_CHANGED=NO
```

## Decision proposed

Remove exhaustive syscall-parser and lock-semantics closure, symbolic descriptor lineage, and proof of the exact internal SQLite shutdown sequence from the Gate 2 critical path. Retain all research packets and parser defects as a separate follow-on workstream. The 83-file retained trace is diagnostic and regression evidence only. Its task-lifetime identity remains insufficient for authoritative lineage, and the cause of WAL persistence remains narrowed, not identified.

Replace that proposed proof route with independent evidence that each attempt's authority, writable state, and descendants are bounded and disposed of by the Factory's outer boundary. This is a proposed change to acceptance criteria, not a claim that any criterion has passed. The existing artifact scan failure remains in force until a replacement policy and its implementation are reviewed and approved under the project's normal governance.

## Evidence already available and its limits

The research namespace containment report records provider-free fixture results for several process and broker-escape channels. It explicitly says the remaining host root was visible with inherited mount permissions and that broker/IPC coverage was not exhaustive. Those results are useful design evidence, not proof of production-wide containment. The underlying research reports are retained outside this repository and must be independently reviewed before reliance.

The diagnostic source currently rejects a regular file above 1,048,576 bytes at the artifact scan, with separate checks including file type, hard links and bounded reading. Its behavior must not be changed or bypassed merely on the basis of this proposal. The original research implementation and its artifact-scan tests are retained outside this repository and are not authority for a changed policy.

The preserved lock audit is incomplete, and parser 17ace is reference-only, not authoritative. Earlier fixture or historical reports with wider readiness claims do not supersede later review failures. The single authorized provider execution is already consumed; no Codex execution, recollection, authentication fallback or new run is authorized by this document.

## Proposed acceptance contract

1. **Identity and containment.** The host supervisor binds a unique attempt identity to a fresh workspace and private runtime, home, temporary storage, process and network domains. Enumerate every writable mount, external endpoint and inherited FD. Prove that provider state cannot reach any durable or cross-attempt store except explicitly controlled output channels. Test pathname traversal, symlinks, hard links, mount crossings and concurrent replacement; name alone must not grant a file an exemption.
2. **Credentials and authority.** Issue credentials only through the reviewed bounded mechanism. Prove attempt B cannot read, use, inherit or derive attempt A's credentials, inherited descriptors, tokens, socket access, or other authority. Establish revocation or expiry and broker-side enforcement where a credential can outlive its local file. Do not claim deleting files revokes a token or retracts data already sent to an external service.
3. **Quiescence and cleanup.** On success, error, timeout, cancellation and supervisor restart, stop or fence all descendants and prevent further writes, then destroy all attempt-owned writable stores. Verify absence from the trusted host side using identity-bound evidence; an attempt's own report is insufficient. Treat open-but-unlinked files, external bind mounts, child namespaces, external services and retained snapshots as separate state domains. Failed or unverifiable cleanup blocks reuse and quarantines the attempt rather than reporting success.
4. **Fresh-attempt independence.** Use two isolated provider-free fixture attempts. Attempt A creates random non-secret sentinels in every permitted writable state domain and obtains a synthetic capability; attempt B must neither observe those sentinels nor use that capability. Verify independently from the host and attempt B. Test deliberate escape and failure cases as well as the happy path. A sentinel failure is evidence of leakage; a pass establishes only the enumerated paths and channels.
5. **Resource bounds.** Enforce and verify per-attempt byte and inode limits over all writable backing stores, including temporary files and any retained output, plus process, memory, CPU, time and IO controls appropriate to the selected isolation mechanism. Trigger each relevant limit with provider-free fixtures and verify bounded host impact and reliable teardown. IO rate limits are not disk-capacity quotas. Aggregate and concurrent-attempt limits are required. Do not select numerical limits without measured workload and host-capacity evidence.
6. **Provider-internal state and artifact separation.** Classify an object as provider-private ephemeral state only by a trusted, attempt-owned namespace and policy context, not by the filename or a worker-supplied label. Candidate examples include state_5.sqlite and its -wal and -shm sidecars. Such files remain untrusted, may contain sensitive data, count against resource limits, are ineligible for artifact promotion or content-bearing logs, and must disappear with the attempt state. The policy does not depend on or assert that any particular sidecar is always legitimate.
7. **Durable output.** Define a narrow, separately staged output channel with explicit content, type, provenance, size and secret checks. Preserve existing rejection of unexpected files and dangerous filesystem objects until a replacement is demonstrably at least as protective. Output publication cannot begin until the attempt is fenced and the trusted scanner has safely resolved and validated the exact object being published.
8. **Evidence and independent review.** Bind test results to immutable revisions, configuration, platform, limit settings, identities and lifecycle events. Preserve negative outcomes, distinguish provider-free fixture evidence from provider execution, and have a separate reviewer verify each claim. No parser result is accepted as sole authority for containment or cleanup.

## Proposed sequence

1. Build a provider-free evidence matrix mapping each proposed obligation to existing fixture evidence, a gap, or a proposed test. Identify the implementation boundary and host-owned state without modifying production or the Gate 2 bundle.
2. Define the proposed storage and artifact-classification design, threat model, trusted supervisor behavior, quotas, cleanup and fencing state machine, and failure handling. Independently review the matrix and design, including symlink, hard-link, race and external-authority cases.
3. Submit the evidence and proposal for an explicit governance decision by the authoritative Gate 2 owner. Preserve the existing acceptance criteria, scanner policy and fail status until a replacement is approved.
4. Under separately granted implementation authority, implement and test the approved design in a disposable environment. Run provider-free adversarial fixtures first. A live provider run, if later needed, requires its own explicit authorization.
5. Independently review the implementation and evidence against the accepted criteria. Only the designated authority may change Gate 2 status. No claim of passing is made here.

## Follow-on research backlog

Preserve the current parser baseline and reference classifications, incomplete lock/source inventories, test plans and retained trace. Prioritize dup2 self-no-op, lock handoff causality, descriptor identity and lifecycle, close error outcomes, split/restart provenance and OFD/POSIX lock modeling only if the parser is to be reused. A collector v2 would need trustworthy task-lifetime identity and non-destructive per-lifetime evidence. Neither workstream is authorized for implementation by this proposal.

## Preserved locks

AUTHORIZED_RUN_COUNT=1; NEW_CODEX_EXECUTION=NO; CODEX_RECOLLECTION_ALLOWED=NO. SYMBOLIC_LINEAGE_WORK_AUTHORIZED=NO. WORKER_CANDIDATE_AUTHORITY=NONE; WORKER_REFRESH_PROMOTION=FORBIDDEN. PERSONAL_AUTH_FALLBACK=FORBIDDEN; API_AUTH_FALLBACK=FORBIDDEN. SUBSCRIPTION_ACCEPTANCE_PACKAGED=NO. H100_EXECUTION_AUTHORIZED=NO; AUTH_07=SUSPENDED_UNCONSUMED. Production, Gate 2 bundle, authoritative SQLite state and the retained trace remain unchanged.
