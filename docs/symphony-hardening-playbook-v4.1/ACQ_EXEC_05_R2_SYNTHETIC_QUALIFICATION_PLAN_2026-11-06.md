ACQ-EXEC-05 R2 is submitted for fresh independent Master Gate review. This complete revision adds the qualification-attempt lifecycle for R1-F04 and preserves R1’s F01–F03 contracts. No preparation or execution is authorized.

1. **Authority and scope**

   The governing review is Plane comment `23e41f43-9891-418a-8585-46e96f17fa65`, retrieved directly from SGOV-2. It confirms F01–F03 as resolved at planning-contract level and requests only the lifecycle correction.

   The independently reviewed R1 attachment has:

   ```text
   bytes=33257
   lines=592
   sha256=85d53d58ab3b1d92a2ab0ba357a13bf6e38edc62a2197cd2e827c19d0c476bdb
   ```

   R3 acceptance remains bounded by Plane comment `3d925f87-6095-46a3-94f8-b1f3e33995d2`:

   ```text
   R3_SOURCE_ACCEPTANCE=MASTER_ACCEPTED_SOURCE_ONLY
   R3_TEST_RESULTS=NONE
   ```

   The independent R1 review reports protected main at `1c045ac215afee47e94d566bf3f3baa0751beb9d`, tree `4f1a87340ce0b93801620be4f602dc1cef0e92f8`, with all eleven applicable authority blobs matching. This revision relies on that independently recorded verification and does not claim a fresh protected-main certification.

   This task performed read-only inspection. No acquisition module was imported, compiled, linted or executed. No control tooling, manifest, fixture or environment was created. No repository or tracker record was modified.

2. **Frozen source identity**

   The immutable source root remains:

   ```text
   /home/jcschoeman96/symphony-acq-exec-02
   ```

   Read-only hashing during this revision confirmed:

   ```text
   executor.py
   bytes=7195
   sha256=ee39547d466a89a18354e66fbf2336ea647aaa58834cca4ea60badb6744b6660

   journal.py
   bytes=31597
   sha256=ff45a0799493c544705c97fa0c06311ba75fe74ee86531131ad045bf4213ed8e

   synthetic_config.json
   bytes=452
   sha256=49c29a3c213b96a8b1bc117e23bfbfd0c41134d7436f2f038429a83b719d74a4

   tests/__init__.py
   bytes=75
   sha256=cfa461f28b2af5b8c930ebe42f938d5d335800b53356031e4889ec1d290c066d

   tests/test_executor.py
   bytes=31350
   sha256=6bd2d674a7af4acf1276540c5582e3da003d3fd47f68c567ea64646c745f6b8c
   ```

   No source modification, runtime replacement of refusals, fixture injection or monkeypatch of `qualified_harness()` is permitted.

3. **Qualification phases**

   Gate A comprises T01–T11 only. It qualifies bounded source-contract behavior for the exact source, interpreter, dependencies and environment identified in its evidence.

   Gate B comprises T12–T20. Frozen R3 cannot qualify it:

   - `qualified_harness()` always raises `SkipTest`.
   - Operational journal, publication, ownership, admission, authentication and transport interfaces refuse.
   - T13 and T14 require successful operations unavailable in R3.

   Gate B requires a separately authorized, independently reviewed successor implementation with new source identities. Repeat Gate A against that successor before Gate B. Success from changed source must never be attributed to frozen R3.

   A Gate A acceptance does not authorize Gate B preparation, execution or acceptance.

4. **Authorization matrix**

   These boundaries describe proposed future permissions. They issue none.

   - **Current planning permission:** read existing source and authority, inspect bytes and return this revision.
   - **Independent plan acceptance:** accepts the procedure only. It grants no writing, provisioning or execution.
   - **Gate A preparation grant:** separately names the attempt, exact control files, permitted preparation commands, immutable dependencies, isolation, manifests, evidence channels and limits.
   - **Control qualification permission:** separately authorizes any execution needed to qualify the collector, observers, evidence sink and interruption handling. It excludes acquisition-source execution unless explicitly included.
   - **Gate A execution grant:** separately binds this attempt, reviewed preparation packet, qualified controls, source identities and literal invocation. It permits one bounded run.
   - **Successor implementation grant:** separately authorizes enumerated Gate B implementation files and effects. It grants no fixture or test execution.
   - **Gate B preparation grant:** separately authorizes named fixed fixtures, disposable volumes, local TLS service, enforcement and observers.
   - **Gate B execution grant:** separately binds the successor, its independently accepted Gate A result, complete fixture/control manifests and literal case commands.
   - **Independent result acceptance:** requires positive independent review and an explicit human Master decision bound to the exact sealed evidence.

   Missing identities, unqualified controls or unresolved arguments block the associated transition.

   Rust acquisition, extraction, installation, native builds, unrelated P08 implementation, Git changes, publication, PR/CI activity, AUTH_07 consumption and Gate 2 activation remain excluded.

5. **Interpreter and dependency approval**

   Preserve the proposed Gate A interpreter:

   ```text
   implementation=CPython
   version=3.14.4
   executable=/usr/bin/python3.14
   resolved_path=/usr/bin/python3.14
   sha256=52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41

   installed_package_version=3.14.4-1ubuntu0.2
   architecture=amd64
   packages=
     python3.14
     python3.14-minimal
     libpython3.14-stdlib
     libpython3.14-minimal
   ```

   These installation identities remain workstation-reported inputs requiring independent verification and explicit approval. They are not observed interpreter execution or Master approval.

   Before execution, independently approve a closed dependency manifest covering:

   - Interpreter, standard library, extension modules, dynamic loader and shared libraries.
   - Bootstrap, collector, module observer and expected-case manifest.
   - Supervisor, evidence sink, acknowledgment mechanism and observation tools.
   - OS/kernel, mounts, filesystem and isolation policy.
   - Gate B’s additional transport, TLS, verifier, ledger, broker, fault injector and independent reviewer.

   Every file-backed dependency needs its resolved path, size, SHA-256 and immutable backing-object identity. Package versions alone are insufficient.

   No wildcard origins, dependency learning during acquisition tests, pip installation, user site packages, implicit plugins or alternate interpreter are permitted.

6. **Control tooling and literal Gate A command**

   Preserve R1’s proposed control paths:

   ```text
   /acq-exec-05-control/gate-a/acq_exec_05_gate_a.py
   /acq-exec-05-control/gate-a/manifest.json
   ```

   The control module remains unimplemented and unqualified. Preparation authority must enumerate these files and every additional dependency before creation. Completed bytes and digests require independent review before execution approval.

   The read-only manifest binds the attempt/run identity, source and dependency manifests, expected cases, observation policy, evidence protocol and limits.

   The literal future command is unchanged. Top-level Python statements begin at column one inside the quoted argument. No implicit dedentation applies.

```bash
/usr/bin/python3.14 -I -B -S -u -c '
import sys
if sys.version_info[:3] != (3, 14, 4):
    raise SystemExit("unapproved Python version")
sys.path.insert(0, "/acq-exec-05-control/gate-a")
from acq_exec_05_gate_a import main
raise SystemExit(main(
    manifest_path="/acq-exec-05-control/gate-a/manifest.json",
    source_root="/home/jcschoeman96/symphony-acq-exec-02",
    evidence_fd=3,
    acknowledgment_fd=4,
))
'
```

   This is an approval candidate, not an instruction to execute.

   The independent supervisor must verify identities before launch, provide write-only evidence FD 3 and read-only acknowledgment FD 4, capture stdout/stderr separately, and close other inherited descriptors except approved standard descriptors.

   It must enforce:

   ```text
   wall_clock_limit=120 seconds
   memory_limit=512 MiB
   process_limit=one test process
   additional_threads=denied
   child_processes=denied
   combined_stdout_stderr_limit=10 MiB
   structured_evidence_limit=finite value approved before execution
   ```

   Use an approved clean working directory and credential-free environment. Reaching a limit prevents qualification.

   Evidence pipes confer no acquisition session, writable journal capability or network permission. Early bootstrap failure cannot qualify Gate A.

7. **Selection and reviewed result collector**

   Select the eleven exact T01–T11 method names from the frozen expected manifest, in numeric order. Reject missing, duplicate or unexpected selection. Do not discover or invoke T12–T20.

   Preserve a reviewed collector extending the pinned `unittest.TestResult` behavior and handling:

   ```text
   startTestRun
   startTest
   addSubTest
   addSuccess
   addFailure
   addError
   addSkip
   addExpectedFailure
   addUnexpectedSuccess
   stopTest
   stopTestRun
   ```

   Preserve normal result and failfast semantics. Record every `addSubTest` callback, including `err is None`. Ordinary `TextTestRunner` output is supplementary.

   Each record contains:

   - Attempt/run, manifest and source identities.
   - Monotonic sequence and previous-record digest.
   - Exact method, subtest site and occurrence.
   - Detached typed parameters.
   - Outcome and relevant exception identity.
   - Associated module checkpoint.
   - External receipt/checkpoint identity.

   `err is None` means the context passed. Assertion exceptions mean failure; other exceptions mean error. Skips, expected failures and unexpected successes cannot qualify.

   Preserve exact types. Distinguish integers from booleans, retain bytes as hexadecimal data, encode floats exactly and preserve string escapes. Normalize the plain `object()` session by its declared ordinal; never use its address as a stable identity. Reject unsupported parameter types.

   Do not use producer serializers or validators to establish evidence validity.

   Durably retain and acknowledge every outcome externally before the callback returns. Missing acknowledgment, serialization failure or collector error stops the attempt.

8. **Expected 104-subtest manifest**

   Preserve the reviewed counts:

   ```text
   T01=0
   T02=2
   T03=13
   T04=4
   T05=0
   T06=0
   T07=59
   T08=5
   T09=7
   T10=6
   T11=8

   TOTAL_METHODS=11
   TOTAL_EXPLICIT_SUBTESTS=104
   ```

   Bind the ordered expansion to the frozen `tests/test_executor.py` digest:

   - T02, line 153: the two raw byte strings in lines 151–152.
   - T03, line 166: the thirteen `bad` URL strings in lines 159–165.
   - T04, line 171: the four raw byte strings in line 170.
   - T07, line 229: nine phases from lines 207–208 crossed with five changes from line 215, phase-major order. Forty-five cases.
   - T07, line 262: `authentication_outcome_missing` for each phase except `AUTHENTICATION_PENDING`. Eight cases.
   - T07, line 284: `PRODUCER_BLOCKED`, then `UNCERTAIN`, each with the three signals from line 251. Six cases.
   - T08, line 325: `1.5`, `-1`, integer `9007199254740992`, newline and U+00E9.
   - T09, line 344: seven dictionaries from lines 339–341, preserving integer `2` versus boolean `True`.
   - T10, line 369: `created`, `preflight`, `metadata`, `object_map`, `expectation_sha256`, `_EventChain__expected`.
   - T11, line 427: null, boolean true, empty dictionary and plain object.
   - T11, line 439: null, tuple `(1000,1000)`, the UID/GID dictionary and the four-field mismatching-identity dictionary.

   Use source order throughout. Each entry contains the exact method, source-site identity, ordinal and typed parameters.

   Materialize and independently review the full expected manifest under separate preparation authority without importing acquisition modules. Never derive expected entries from actual outcomes.

   Actual results remain absent. Qualification requires exact ordered identity and parameter equality, not merely count equality.

9. **Expected 240 loop-case observations**

   Preserve the source-observation contract for loops outside and overlapping explicit subtests:

   ```text
   T02 raw configurations                         2
   T03 valid URLs                                 2
   T03 invalid URLs                              13
   T04 raw JSON inputs                            4
   T06 object indexes                             7
   T07 hypothetical validation by active phase     9
   T07 observed failure phase/change combinations 45
   T07 active phase/signal combinations           27
   T07 late signals within those combinations     81
   T07 blocked/uncertain terminal signals          6
   T07 producer-complete wrong-phase repetitions   4
   T07 signals after completion invalidation       3
   T08 canonical values                           5
   T08 invalid calendar timestamps                2
   T08 invalid event types                        4
   T09 malformed transfer results                 7
   T10 prohibited attribute assignments            6
   T10 authentication outcomes                    5
   T11 invented sessions                          4
   T11 invented ownership evidence                4

   TOTAL_DECLARED_LOOP_CASES=240
   ```

   These overlap subtests and are separate evidence classes. Do not add them to the subtest count.

   The reviewed observer uses pinned source locations and declared loop variables through Python tracing. It must not modify test bodies, assertions or acquisition functions.

   Its location manifest identifies entry/completion boundaries, including the last iteration. Reaching a line alone does not prove an assertion passed. Completion records, associated subtest outcomes and successful parent-method results must agree.

   Independently qualify repeated `with` lines, handled exceptions, failfast exits and final iterations. Unqualified tracing blocks Gate A.

10. **Completeness and collection failures**

   Gate A success requires:

   - Eleven method starts and completed successful methods in order.
   - Exactly 104 passed explicit subtests with matching identities and parameters.
   - Exactly the declared 240 loop-case identities and completions.
   - No missing, duplicate, unexpected, skipped, failed or erroneous case.
   - Complete approved module-origin evidence.
   - Unchanged source and no prohibited effects.
   - Complete external checkpoints and observed exit code zero.

   Stop on the first failure or evidence defect. Preserve prior records. Mark unstarted expected cases `NOT_RUN` and entered scopes without outcomes `INCOMPLETE`; neither is a pass.

   `BaseException`, timeout, signal, truncation, broken evidence channel, storage exhaustion or lost acknowledgment prevents qualification. Section 18 determines the absorbing terminal state.

   Control qualification must separately exercise successful callbacks, failures, errors, skips, missing/duplicate cases, interrupted scopes and evidence loss. That work needs separate permission and creates no acquisition-test result.

11. **Complete module-origin evidence**

   Preserve R1’s origin contract independently of T01.

   Inventory the entire `sys.modules` mapping, including aliases, unexpected entries and `None` sentinels. Each entry contains:

   ```text
   module name and aliases
   classification
   __spec__.name
   __spec__.origin
   loader type and approved implementation identity
   __file__ and resolved path where present
   package search locations where present
   file size and SHA-256 where applicable
   immutable backing-object identity
   approved dependency-manifest entry
   validation outcome
   ```

   Validate:

   - Built-in modules against the approved built-in loader, module name and interpreter manifest.
   - Frozen modules against the approved frozen loader and named frozen-module inventory. Record associated `__file__` separately.
   - Python and extension files against exact module/path/digest/loader bindings under immutable custody.
   - Bootstrap `__main__` only as the declared `-c` pseudo-module bound to command bytes.
   - Other synthetic, namespace, missing-spec or sentinel entries only through explicit manifest entries.

   Reject unknown origins rather than omitting them.

   Required full snapshots remain:

   1. After trusted control bootstrap, before acquisition imports.
   2. Before and after acquisition import.
   3. At every method start and stop.
   4. At every subtest entry and outcome.
   5. On catchable exceptional exit.
   6. At normal finalization after collector formatting/reporting.

   Maintain a cumulative inventory. Validate additions, removals, aliases and identity changes. Unexplained removal or replacement prevents qualification.

   Before acquisition imports, install the reviewed audit observer for import/code-execution events and tracing observer for module additions. Correlate them with independent filesystem/native-library observations.

   Retain failed import attempts even if Python removes their module entries. Unresolved execution, unapproved extension loading or an observation gap prevents acceptance.

   Preload observer dependencies. Callbacks must not trigger untracked lazy imports. Audit/tracing provides evidence; approved mount and dependency custody enforces load boundaries. T01 and module metadata alone cannot prove custody.

12. **Origin evidence during interruption**

   Durably acknowledge every snapshot externally before the next approved checkpoint proceeds.

   The independent supervisor owns the evidence sink. The test process cannot rewrite or delete acknowledged records.

   On a catchable exception, the outer `finally` path attempts an exceptional snapshot. Exception-formatting imports also enter the inventory. Failure to produce that snapshot remains a defect.

   `SIGKILL`, interpreter failure or power loss may prevent finalization. In those cases:

   - Preserve the last acknowledged full snapshot, cumulative inventory, import observations and external records.
   - Externally record termination and the missing final checkpoint.
   - Enter `INCOMPLETE` when effects are determinate, or `UNCERTAIN` when they are not.
   - Never fabricate a final inventory or promote the attempt to review-ready success.

   Failure before the initial snapshot produces incomplete origin evidence. Separately qualify these paths before Gate A execution approval.

13. **Custody, isolation and allowed effects**

   Preserve the original files and directories. Do not chmod, rename, replace, hardlink, repair or write into them.

   A separately authorized owner must expose exact source bytes read-only at their existing absolute path inside isolation. Verify identities before launch and after termination, with concurrent substitution excluded throughout.

   Preserve the proposed roots:

   ```text
   /acq-exec-05/A/<run-id>/work
   /acq-exec-05/A/<run-id>/tmp
   /acq-exec-05/A/<run-id>/home

   /acq-exec-05/B/<run-id>/<case-id>/objects
   /acq-exec-05/B/<run-id>/<case-id>/events
   /acq-exec-05/B/<run-id>/<case-id>/tmp

   /acq-exec-05-fixtures/<fixture-set-id>
   /acq-exec-05-evidence/<run-id>
   ```

   Before preparation, expand identifiers and approve exact backing volumes, device/inode identities, ownership, modes and permitted writers.

   Gate A permits no network, listening socket, child process, object creation or journal publication. Persistent outputs are limited to approved evidence and stdout/stderr.

   Gate B permits only enumerated synthetic outputs and fault artifacts in approved disposable volumes. Control and fixture mounts remain read-only. Producer writes to the external evidence store remain denied.

   No host-home, repository, Rust toolchain or accepted P08 scaffold effects are permitted. Disposable storage does not imply cleanup permission.

14. **Gate A expected behavior**

   - T01 checks exact acquisition-module paths.
   - T02 checks configuration parsing and refusal after invalid or mutated inputs.
   - T03 checks canonical numeric-loopback HTTPS bases and listed rejections.
   - T04 rejects duplicates, unsupported numeric encodings, mixed versions and noncanonical event bytes.
   - T05 checks static canonical-byte and digest vectors.
   - T06 checks the pure seven-object model and metadata ordering.
   - T07 checks nine-phase hypothetical/consuming behavior, signals and terminal preservation.
   - T08 checks closed types, calendar validity and bounds.
   - T09 checks permanent termination after malformed transfer claims.
   - T10 checks immutable expectations and consuming authentication semantics.
   - T11 checks refusal of invented supervisor, admission and ownership claims.

   Acceptance proves only these bounded source contracts for the identified environment. It does not qualify operational supervision, transport, ledger authenticity or artifact acceptance.

15. **Gate B prerequisites, fixtures and commands**

   Gate B remains blocked for frozen R3.

   Before approval, independently review the successor, its accepted Gate A result, authentic supervision, writer exclusion, durable ledger, request enforcement, fixed fixtures, publication/synchronization behavior, observers and separate acceptance logic.

   Expand and approve Gate B’s exact method/nested-case, dependency and module-origin manifests.

   Fixtures must be independently reviewed and pre-generated, with exact filenames, sizes, SHA-256 values, provenance and interpretation. Include seven synthetic objects, metadata/signature variants, public keyring, TLS sets, status/revocation records, retained hash-test bytes and malformed evidence.

   No official Rust artifacts, real Rust trust material or usable distribution is authorized. No signing-key generation, implicit GnuPG home, agent or keyserver access occurs during tests. Only the fixture service holds its reviewed synthetic TLS private key.

   Use an independently controlled isolated network allowing approved numeric-loopback HTTPS only. Deny external routes, DNS, proxies, redirect following, retry and fallback. Separately demonstrate and observe denied external connection attempts.

   Future commands retain this contract:

   ```text
   <approved absolute Python executable> -I -B -S
       <approved absolute integration runner>
       --manifest <approved absolute manifest>
       --test <exact fully qualified method>
   ```

   These are not executable authorizations. Replace every placeholder with literal approved arguments and digests before granting execution.

16. **Independent enforcement and Gate B outcomes**

   Preserve Option A’s independent ownership separation and this order:

   1. Validate the exact grant, attempt, candidate, map, environment and policy.
   2. Atomically and durably consume the one-use grant and attempt externally.
   3. Bind the launch.
   4. Transfer approved writable capabilities.
   5. Publish and independently retain exact `OBJECT_STARTED` bytes.
   6. Durably commit the checkpoint and authenticate its ACK.
   7. Independently admit the exact request under current supervision.
   8. Transfer.

   Admission binds attempt, grant, sequence, index, literal URL, started-event digest, durable ACK and current supervisor identity. The producer has no bypass route.

   Uncertain consumption, launch, acknowledgment or supervision terminates the attempt. Qualify enforcement against a noncooperating producer.

   Expected Gate B results remain:

   - T12 refuses invalid publication inputs without changing the approved disposable directory.
   - T13 hashes retained original bytes under qualified ownership without changing offset or identity.
   - T14 performs seven ordered local HTTPS transfers, with authenticated metadata before request 4 and matching independently retained bytes/inventory.
   - T15 blocks redirects, HTTP failures and wrong effective URL without follow-up requests.
   - T16 blocks TLS, signature, signer, status and immediate-recheck failures before archive requests.
   - T17 blocks aliases, existing targets, changed storage, wrong ownership/mode and unapproved writers without overwrite or unapproved creation.
   - T18 retains independently observed interruption/fault evidence without cleanup, recovery or retry.
   - T19 independently denies premature/post-loss requests, replay and changed bindings.
   - T20 rejects forged, absent, corrupt or contradictory evidence.

   Preserve T18’s boundaries:

   ```text
   before link:
     pending only; UNCONFIRMED

   after link, before directory sync:
     pending and final; UNCONFIRMED

   after unlink, before directory sync:
     final only; UNCONFIRMED

   after link and directory sync:
     pending and final; CONFIRMED_AT_BOUNDARY

   after unlink and directory sync:
     final only; CONFIRMED_AT_BOUNDARY
   ```

   Process-kill observations do not prove power-loss survival. Stronger claims require separate crash/replay authority and qualification.

17. **Evidence retention and review**

   Begin external retention before launch. Preserve:

   - Grants, accepted plan, authority and complete manifests.
   - Literal commands, identities, environment, limits and descriptor policy.
   - Custody, mounts, writer exclusions and pre/post inventories.
   - Raw method, subtest and loop records, including successes.
   - Module snapshots, cumulative origins, import observations and failures.
   - Raw stdout/stderr, exit status, signals, limits and collection defects.
   - Original event/object bytes, partial files and aliases.
   - External consumption, launch, checkpoint, ACK and admission/denial history.
   - Independent network/filesystem and fault-boundary observations.
   - Lifecycle transitions, independent review and Master decisions.

   Freeze the sink’s framing, sequencing, hash-chain, persistence and acknowledgment protocol before execution. Acknowledge only after durable retention.

   Index exact artifact lengths and SHA-256 values. Preserve partial streams and malformed records. Never silently truncate, replace or repair evidence.

   The independent reviewer uses separately implemented logic and original retained bytes. Producer claims, collector summaries and exit code zero do not establish independent acceptance.

   Seal the qualification bundle before review. Record its complete artifact index, digest and final external checkpoint. Review may examine existing sealed artifacts and append reviewer reports. It may not repair the bundle by adding missing producer results, replacing bytes or repeating tests.

   Retain everything until explicit Master release.

18. **Formal qualification-attempt lifecycle**

   This lifecycle governs both gates independently. It is a proposed contract requiring later implementation and qualification.

   Each attempt has immutable:

   ```text
   attempt_id
   run_id
   gate_kind=A or B
   accepted_plan_identity
   source_manifest_identity
   preparation_grant_identity
   preparation_packet_identity when sealed
   execution_grant_identity when issued
   command_and_dependency_manifest_identity
   expected_case_manifest_identity
   evidence_bundle_identity when sealed
   ```

   Assign a fresh attempt identity under an explicit preparation grant. Do not create or start an executable attempt under current planning permission.

   `NOT_AUTHORIZED` also records a denied request. It is absorbing for that identity. Receiving permission later requires a new attempt rather than reopening the denied record.

   The nonterminal states are:

   ```text
   PREPARATION_AUTHORIZED
   PREPARING
   PREPARATION_REVIEW_PENDING
   PREPARED
   EXECUTION_AUTHORIZED
   LAUNCH_COMMITTED
   RUNNING
   EVIDENCE_COLLECTION
   EVIDENCE_READY_FOR_INDEPENDENT_REVIEW
   UNDER_INDEPENDENT_REVIEW
   ```

   The terminal, absorbing states are:

   ```text
   NOT_AUTHORIZED
   BLOCKED_PREREQUISITE
   FAILED
   INCOMPLETE
   UNCERTAIN
   CANCELLED
   REJECTED_INDEPENDENT_REVIEW
   INDEPENDENTLY_ACCEPTED_SOURCE_CONTRACT_ONLY
   INDEPENDENTLY_ACCEPTED_SYNTHETIC_INTEGRATION_ONLY
   ```

   The complete permitted transition relation is below. `N` means any nonterminal state; `T` means any terminal state. Guards and effects following the relation are normative.

   ```text
   ID    From                                      To
   L00   no attempt                                NOT_AUTHORIZED
   L01   no attempt                                PREPARATION_AUTHORIZED
   L02   PREPARATION_AUTHORIZED                    PREPARING
   L03   PREPARING                                 PREPARATION_REVIEW_PENDING
   L04   PREPARATION_REVIEW_PENDING                PREPARED
   L05   PREPARED                                  EXECUTION_AUTHORIZED
   L06   EXECUTION_AUTHORIZED                      LAUNCH_COMMITTED
   L07   LAUNCH_COMMITTED                          RUNNING
   L08   RUNNING                                   RUNNING
   L09   RUNNING                                   EVIDENCE_COLLECTION
   L10   EVIDENCE_COLLECTION                       EVIDENCE_READY_FOR_INDEPENDENT_REVIEW
   L11   EVIDENCE_READY_FOR_INDEPENDENT_REVIEW      UNDER_INDEPENDENT_REVIEW
   L12   UNDER_INDEPENDENT_REVIEW                  INDEPENDENTLY_ACCEPTED_SOURCE_CONTRACT_ONLY
   L13   UNDER_INDEPENDENT_REVIEW                  INDEPENDENTLY_ACCEPTED_SYNTHETIC_INTEGRATION_ONLY
   L14   UNDER_INDEPENDENT_REVIEW                  REJECTED_INDEPENDENT_REVIEW
   L15   N, before launch                          NOT_AUTHORIZED
   L16   N, before launch                          BLOCKED_PREREQUISITE
   L17   N                                         FAILED
   L18   N                                         INCOMPLETE
   L19   N                                         UNCERTAIN
   L20   N                                         CANCELLED
   L21   T                                         same T
   L22   N                                         same N
   ```

   No unlisted state change is permitted.

   The transition guards and effects are:

   - **L00:** A request lacks applicable preparation authority. Deny preparation and launch. Retain the denial without issuing capabilities.
   - **L01:** An explicit human preparation grant binds a fresh identity, accepted plan, gate and exact permitted effects. Durably register that binding once. Registration alone performs no preparation.
   - **L02:** Preparation authority remains valid, the approved owner is identified and required observation is ready. Perform only enumerated preparation effects. Acquisition tests remain denied.
   - **L03:** Preparation finishes within scope, with every effect accounted for. Stop preparation and seal its packet. Missing or contradictory prerequisites take an adverse transition instead.
   - **L04:** Independently accept the exact preparation packet and required separately qualified controls. Preserve the configuration. No execution authority follows.
   - **L05:** Receive and independently authenticate a fresh explicit human execution grant for this attempt, packet, command, dependencies, cases and limits. Bind it durably. Do not launch.
   - **L06:** Revalidate all identities, current authority, custody, isolation and observer readiness. Durably consume the one-use launch entitlement before launch. Failed or ambiguous consumption takes L19.
   - **L07:** Launch the approved command once and independently confirm its process identity. No second launch is allowed from this state. An uncertain launch outcome takes L19 and is never retried.
   - **L08:** Advance only to the next declared operation within the running command, with required acknowledgments and enforcement present. This permits neither restart nor an additional command.
   - **L09:** The approved runner exits zero without a latched defect, limit breach or loss. Deny further execution and collect remaining external evidence. Exit zero is not acceptance.
   - **L10:** Independently check complete expected identities, outcomes, origins, custody, effects, receipts and lifecycle history. Seal and durably acknowledge the bundle. Expose its exact identity through the approved review channel only.
   - **L11:** An independent reviewer accepts the exact sealed intake. Permit read-only assessment of existing evidence and append-only reviewer reports. No producer work, source change or bundle repair is permitted.
   - **L12:** Gate kind is A, the complete bounded contract is satisfied, independent review is positive, and an explicit authenticated human Master decision accepts this exact attempt and bundle. Record source-contract acceptance only.
   - **L13:** Gate kind is B, the reviewed successor and its Gate A prerequisite are valid, all integration requirements are satisfied, independent review is positive, and an explicit authenticated human Master decision accepts this exact attempt and bundle. Record synthetic-integration acceptance only.
   - **L14:** The independent review rejects the attempt, including a `CHANGES_REQUESTED` verdict, or Master explicitly rejects it. Retain the findings and deny continuation. A later human decision cannot promote that same rejected attempt.
   - **L15:** Required authority is refused, invalid or expires before launch. Deny new effects and retain the authority failure. Merely waiting for an execution grant while `PREPARED` is not a denial; it permits no launch.
   - **L16:** A prerequisite is known to be unavailable before launch. Retain the blocker and deny launch. Supplying it later requires a fresh attempt and authorization.
   - **L17:** A requirement demonstrably fails while effects and evidence remain determinate. Examples include a failed assertion, known identity mismatch, duplicate result or prohibited observed effect. Stop and deny further qualification work.
   - **L18:** A known interruption, skip, missing required result or truncated collection prevents completion while effects remain determinate. Retain partial evidence and mark absent results. No review-ready transition remains available.
   - **L19:** Consumption, launch, effects, custody, synchronization, evidence acknowledgment or supervision is ambiguous. Immediately deny capabilities and further requests, stop within the approved stopping policy and retain uncertainty. A later ACK or observation cannot reopen the attempt.
   - **L20:** Human cancellation or revocation occurs with determinate effects. Stop, preserve evidence and deny continuation. If effects are ambiguous, use L19 instead.
   - **L21:** Terminal-state annotations may retain late evidence, repeated denials, stopping confirmations or corrections. They cannot change the terminal state, repair the accepted bundle, authorize work or create acceptance.
   - **L22:** A nonterminal state may receive authorized observations or wait without changing phase. Such records grant no new effects, extend no expired authority and bypass no guard.

19. **Lifecycle enforcement, terminal handling and fresh attempts**

   An independently owned qualification ledger must enforce transitions through durable compare-and-set against the exact attempt, current state and previous transition digest. Producer callbacks cannot change authoritative qualification state.

   Every transition record must retain its trigger, actor, current authority, guard evidence, permitted effects, resulting state and durable checkpoint. Stale, duplicate, out-of-order or conflicting transitions deny further work.

   A required transition acknowledgment must be durable before the next effect. Missing or ambiguous acknowledgment takes L19. If durable terminal recording itself fails, the supervisor must still deny effects, stop and retain an external unresolved/uncertain record. Absence of a confirmed terminal record cannot restore eligibility.

   Adverse transitions take precedence over forward progress. When the same incident proves both a failure and uncertainty, classify it `UNCERTAIN` and retain the proved failure as a finding. Once any terminal state is recorded, it remains absorbing.

   Entering a terminal state immediately denies new preparation, launches, test operations and acquisition admissions. The independent supervisor may perform only the preauthorized stopping and retention actions needed to contain the existing process and preserve evidence. These may continue after terminal entry; they do not reopen execution.

   Stopping policy must be fixed in the preparation/execution grants. It must identify capability withdrawal, process termination, finite stopping deadline and retained observations. It permits no retry, recovery, cleanup or replacement attempt.

   Distinguish expected Gate B fault cases from qualification interruption. An approved T18 child-process kill may satisfy that case when the supervising runner and evidence remain complete. Loss of the qualification runner, supervisor or required evidence follows L18 or L19.

   Preparation rejection also terminates the attempt. A negative preparation assessment takes L16 for a known unavailable prerequisite, L17 for a proved failed requirement, or L19 for ambiguity. It cannot return to `PREPARING`.

   Independent review may clarify existing sealed artifacts. Discovery that required evidence is missing takes L18, ambiguity takes L19, and rejection takes L14. Neither supplementary producer evidence nor a repeated test may fill that attempt’s gaps.

   Acceptance requires both positive independent review and explicit human Master acceptance. Neither a proposed acceptance, elapsed time, Plane workflow state nor an execution grant satisfies L12 or L13.

   After any terminal outcome:

   - Never retry, resume, rearm or reclassify that attempt.
   - Never reuse its consumed launch entitlement.
   - Never insert later results to make it complete.
   - Preserve its full history and terminal disposition.
   - Require a new attempt/run identity, fresh explicit preparation and execution authority, new output/evidence directories and renewed guard checks for another run.
   - Existing immutable source, fixtures or control artifacts may be referenced only after fresh validation and explicit inclusion in the new grants. Old test outcomes cannot become new execution evidence.

   A historical accepted verdict also remains immutable. Later adverse findings must be appended and must block reliance on the challenged evidence pending separate Master disposition. They grant no new work and do not rewrite history.

   Gate A and Gate B use different attempt identities and grants. Gate A acceptance can be a prerequisite reference for Gate B; it cannot transition the Gate A attempt into a Gate B attempt.

20. **Human boundary and planner disposition**

   This revision closes R1-F04 only at the proposed contract level. Independent Master re-review must decide whether it resolves the finding.

   No executable attempt has been created by this plan. Plan acceptance, if later issued, does not move an attempt into `PREPARATION_AUTHORIZED`. That transition still requires its own exact human grant.

   ```text
   TERMINAL_PLANNER_DISPOSITION=
     READY_FOR_INDEPENDENT_QUALIFICATION_PLAN_RE_REVIEW

   REVISION=ACQ-EXEC-05-R2
   MASTER_REVIEW=23e41f43-9891-418a-8585-46e96f17fa65

   F01_COMMAND_CONTRACT=PRESERVED
   F02_SUBTEST_AND_LOOP_CONTRACT=PRESERVED
   EXPECTED_EXPLICIT_SUBTESTS=104
   EXPECTED_LOOP_CASE_OBSERVATIONS=240
   F03_MODULE_ORIGIN_CONTRACT=PRESERVED

   R1_F04=
     EXPLICIT_STATES_TRANSITIONS_GUARDS_EFFECTS_DEFINED
     ABSORBING_TERMINAL_STATES_DEFINED
     INDEPENDENT_MASTER_ACCEPTANCE_AND_REJECTION_DEFINED
     SAME_ATTEMPT_RETRY_RECLASSIFICATION_AND_GRANT_REUSE_DENIED

   FINDING_CLOSURE=INDEPENDENT_MASTER_REVIEW_PENDING
   CONTROL_IMPLEMENTATION_AND_QUALIFICATION=NOT_PERFORMED
   ACTUAL_TEST_RESULTS=NONE

   R3_SOURCE_ACCEPTANCE=PRESERVED
   GATE_A_PREPARATION=NOT_AUTHORIZED
   GATE_A_EXECUTION=NOT_AUTHORIZED
   GATE_B_PREPARATION=NOT_AUTHORIZED
   GATE_B_EXECUTION=BLOCKED
   GIT_PUBLICATION=NOT_AUTHORIZED
   P08_T04_FULL_TASK_ACCEPTANCE=NOT_GRANTED
   AUTH_07=SUSPENDED_UNCONSUMED
   AUTH_07_CONSUMED=NO
   GATE2_ACTIVATION=NOT_AUTHORIZED
   ```