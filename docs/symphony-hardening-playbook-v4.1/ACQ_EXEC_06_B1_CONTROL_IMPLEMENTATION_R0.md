# B1 control implementation R0

Status: B1-F01 correction candidate. Exact-commit review and CI evidence must be
read from the draft PR. Production admission remains closed under the bounded
implementation grant.

## Scope and design

The implementation preserves B1-R2's nine nonterminal states, ten absorbing
terminal states, twelve normal/review transitions and fifty-four adverse
transitions. It does not initialize a historical case or implement Gate A.

`tools/b1_control.py` owns the transition admission rules, exclusive durable
records, acknowledgment validation and two ordered descriptor-based copies.
`tools/b1_verify.py` independently reads artifact descriptors and journal bytes;
it does not import the producer's acceptance logic. Production admission is
closed until separately qualified external custody, authentication, observation
and isolation controls exist. Synthetic MAC keys demonstrate protocol behavior
only. Holding those keys in one test process establishes no principal separation.

The existing provider/runtime DETS ledgers do not implement this contract and
would couple this bounded mechanism to application startup. They are not reused.
The existing fixed Rust/systemd probe launches a different operation. Its old
qualification does not qualify this implementation. Existing Linux file
descriptors, exclusive creation, flock, fsync, fork/exec and process groups supply
the bounded local operations; no database or service is added.

The six allowed paths are the two modules, their two test modules, this document
and `.github/workflows/b1-control.yml`. Implementation choices and the final
effect inventory are recorded here without editing historical authority.

## State and commitment interface

`TRANSITIONS` explicitly lists the complete 66-row relation. Its rows bind the
source, destination, initiating actor and required evidence. `NONTERMINAL` and
`TERMINAL` list all nine and ten states. No row originates at a terminal state.
The twelve normal rows cover planning, grant issuance, consumption, writing,
producer completion, review intake and the two completed review decisions.
The remaining rows cover all six adverse families from every nonterminal state.

`register(H_envelope)` prospectively establishes a synthetic P0 only after C
acknowledges the durable initialization proposal. The proposal includes namespace,
case, unused human authorization identity, authorized revision, approval reference,
terminal predecessor decision and artifact hashes, governing Git identities,
finite validity and explicit absence of grant/consumption. Uniqueness holds within
the locked synthetic journal. It does not prove uniqueness in an external
authoritative registry. The tests never register an actual planning case.

`apply(actor_envelope)` requires the exact confirmed journal head and source
state. HMAC-SHA256 authenticates distinct synthetic H/P/M/S/V/C role keys.
The signed request binds the case, transition and evidence. The C receipt binds
the exact proposal digest, sequence, namespace, case and expiry. Every next
state/effect waits for receipt validation and a synchronized confirmation record.
An unsigned callback return, stale receipt, altered request or lost acknowledgment
cannot confirm a transition. Keys in one process establish no independent actors.

T06 requires an unused synthetic B1 grant and attempt, the received plan identity,
three complete descriptor identities, export ranges, exact executable identity,
literal destination entry, finite expiry, limits and the complete effect allowance.
T07 consumes that B1 entitlement once. Gate A L06 cannot substitute for it. T08
confirms writing readiness before directory creation. Creation authority never
follows from matching bytes alone.

Adverse priority is uncertainty, revocation, expiry, invalid authority, procedure
failure and incompleteness. Observed expiry also defeats lower-priority requests
and forward progress. T12 requires a complete, determinate negative artifact
review. F-O4 requires failed review machinery and an incomplete review. U-O4
takes precedence when the disposition is uncertain. A producer cannot issue V's
review decision, and no decision grants Gate A execution.

Records use exclusive `0400` sequence files, canonical JSON, a predecessor digest
and supervisor MAC. Each file and the records directory are synchronized before
return. Pending and confirmed records remain distinct on disk. A used journal
always denies controller restart, including after a clean close. There is no
automatic replay, state repair, refunded slot or terminal reopening. On a copy
failure, the controller retains partial objects and records a halt when storage
still works. It denies further effects. A failed record write or acknowledgment
may leave only pending or incomplete bytes. No terminal transition is invented
when C cannot confirm it. External reconciliation remains required in that case.

## Copy and independent observation

`copy(case, input_fds, executable_fd)` accepts O2 only. Input bindings include
device/inode, UID/GID, mode, link count, size, timestamps and SHA-256. Inputs must
be read-only descriptors of `0400` regular files with one link. Whole export
slices and their final LF must match. Initial offsets must be zero. Repeated
observations use `pread` and do not reset consumed offsets.

The controller holds the parent directory descriptor, exclusively creates the
new `0700` directory and two `0400` files through relative no-follow operations,
and reserves source then companion launch slots before fork. Only descriptors
0, 1 and 2 survive exec. Descriptor 3 carries the verified native ELF executable
to `execve` and closes on exec. No source is imported or executed. The fixed
argument vector is `dd bs=65536 status=none`; its input/output are the inherited
payload descriptors. The environment contains only C locale and UTC settings.

Each successful child must exit zero within the materialization deadline. The
controller checks output metadata, fsyncs the file, closes its writer and receives
the checkpoint acknowledgment before creating the next payload. It then sets
the directory to `0500`, fsyncs directory then parent, rechecks identities and
receives the producer checkpoint acknowledgment. These are syscall observations,
not proof of storage-device persistence after power loss.

Limits are 30 seconds across copying, a separate five-second stop-confirmation
bound, 128 MiB child address space, 65,536-byte output, 4,096-byte diagnostics,
zero core size and 30 CPU seconds per child. A shorter synthetic wall limit is
available for stopping tests. Copying requires an unprivileged UID. The child
sets the hard process limit to zero, so the selected utility cannot create
descendants or threads. Stop sends SIGKILL only to the retained child PID and
confirms `waitpid`; failure to confirm is uncertain and cannot enable another
launch. This does not supervise a child after abrupt controller death.

`b1_verify.py` imports no producer module. Its descriptor reader independently
hashes complete files, compares full bytes and export slices, verifies final LF,
metadata and entry identity, and reports exact entry inventory. Known missing or
mismatching payloads yield a completed negative artifact report. An inability to
observe yields an exception, not T12. `read_history` authenticates journal framing,
hash chains and C receipts, and exposes unmatched pending evidence. It is not an
independent reimplementation of all transition guards. The appointed verifier
must assess grant, lifecycle, synchronization and custody evidence separately.
`production_acceptance` refuses without effects.

### B1-F01 correction

The original 40-test candidate accepted a syntactically valid positive decision
digest without obtaining its corresponding independent result. The owner found
this in review. The prior completion claim and exact-HEAD certification do not
apply to the corrected candidate.

T11 and T12 now require a configured result observer. `review_context(case)`
identifies the exact synthetic namespace, case, initialization, received packet,
full grant and attempt, parent, candidate, both producer output identities,
acknowledged producer checkpoint, review authority and current O4 journal head.
The controller sends that context to the observer instead of accepting a supplied
digest as verification. An absent observer denies the decision.

`b1_verify.review_result` reads and authenticates the actual journal, requires the
confirmed path through O4 and the two ordered launch/checkpoint records, checks
the full grant and producer bindings, opens the named candidate relative to the
observer's held parent, verifies all three accepted input identities and calls
the independent candidate reviewer. It signs the full context and actual result
with the synthetic V key. Candidate or payload metadata changes since the producer
checkpoint enter the negative findings. This adds no lifecycle transition.

The controller validates V authentication, exact context equality, the complete
result hash and its agreement with the decision. It checks the lifecycle again
and re-observes the live directory and complete payload identities before
proposing the terminal transition. The full V receipt enters the pending T11/T12
record and therefore C's acknowledgment and the durable confirmation. A bare
digest, foreign attempt, stale head, altered result, missing observation or changed
payload cannot satisfy the guard. Completed negative results remain T12; failed
observation cannot become a completed artifact rejection.

The observer is a synchronous synthetic callback and its keys remain in one test
process. The tests demonstrate result/content/lifecycle binding, not production
principal separation, independent key custody or a qualified receipt transport.
Production admission and acceptance remain unconditional denials.

## Synthetic effects and dependencies

Local test effects are confined to
`/home/jcschoeman96/projects/symphony-b1-control-r0/.b1-control-test/`.
Each test owns a temporary `0700` namespace beneath it. The modules reject a
synthetic storage root outside that allowance or an explicit child of RUNNER_TEMP
in CI. Test effects are fixture files and symlinks, a records directory, bounded
JSON records, the synthetic candidate and its two files, chmod/unlink operations
for negative tests and cleanup, descriptor locks, anonymous diagnostic pipes,
fork/exec/wait, process limits and bounded stop simulations. There are no sockets,
external requests, database services, operational inputs or production records.
Synthetic role keys stay in memory and are not committed or logged.

One journal admits at most 2,048 files of at most 65,536 bytes each, including
framing and MAC, for a maximum 128 MiB of record bytes. Each input is at most
131,072 bytes and each payload at most 65,536 bytes. The bound is per synthetic
namespace; the fixed test suite creates and cleans its namespaces sequentially.
Diagnostics stay in memory and enter authenticated checkpoints as bounded hex.
Independent result observation adds read-only journal/input/candidate descriptor
opens, full bounded reads and current metadata checks. The existing terminal
transition record retains the bounded full V result; no separate store, socket,
service, dependency or authoritative case is introduced.
Tests remove only their own synthetic objects, including retained failure objects.
Production failure handling would preserve those objects instead.

Local interpreter: CPython 3.14.4, `/usr/bin/python3.14`, SHA-256
`52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41`.
Local copy utility: BusyBox 1.37.0, `/usr/bin/busybox`, SHA-256
`df12634c17fcdca839ae5dc47d7627b7558511f7645de7c99ccf097a0f28ed5b`.
Its fixed `argv[0]` selects dd. The host's uutils 0.10.0 dd rejects descriptor
execution and requires a thread when path-executed. The zero-process limit makes
that implementation incompatible. It is not silently used as a fallback.
CI explicitly selects GNU `/usr/bin/dd` on Ubuntu 24.04 and reports its version
and byte identity. These are two synthetic dependency configurations, neither
an accepted operational closure.

Only Python's standard library is used. No package installation, lockfile,
database or application startup is needed locally. CI pins checkout and
setup-python to immutable action commits, requests exactly CPython 3.14.4 x64,
and fails if unavailable. It has only `contents: read` permission and no provider
credentials. Test execution uses `-I -B`, logs the exact candidate HEAD/tree,
interpreter and chosen RUNNER_TEMP child, and writes its report inside that root.
The report includes hashes of loaded module files and mapped libraries. It is
an observed dependency list, not an immutable or exhaustive execution closure.
The Actions interpreter installation and action setup use runner-managed paths
under the separately authorized CI dependency-acquisition allowance.

## Verification and review

The local command is:

```sh
B1_TEST_ROOT=/home/jcschoeman96/projects/symphony-b1-control-r0/.b1-control-test \
B1_COPY_EXECUTABLE=/usr/bin/busybox \
/usr/bin/python3.14 -I -B -m unittest discover -s tools/tests -p 'test_b1_*.py' -v
```

All 53 tests passed locally. Subtests execute all 54 adverse rows from their
actual source states; normal paths exercise all twelve normal/review rows and
all ten terminal outcomes. Tests include lost/replayed ACKs, duplicate approval,
double consumption, Gate A substitution, wrong actor, altered request, expiry,
terminal absorption, concurrent supervisor lock, restart denial, failed fsync,
failed fork, immutable launch-slot reservation, timeout stopping, descendant
prevention, descriptor execution, dependency/input substitution, symlink refusal,
missing checkpoint, independent byte mismatch and missing-payload rejection.
Late initial/consumption acknowledgments cannot confirm expired authority.
The uncertain-stop case simulates unavailable observation without abandoning a
real child. It is not evidence of host-level death supervision.
The installed actionlint 1.7.12 accepted the new workflow. Optional external
shellcheck and pyflakes integrations were disabled; no tool was installed.
B1-F01 first reproduced as a failing bare-digest regression. The corrected suite
uses actual independent results for both positive and negative terminal decisions.
It also rejects missing observers, modified results, foreign case/grant/attempt/
candidate/parent/plan bindings, stale heads, input substitution, unconfirmed review
intake and post-observation payload changes. It verifies full-result retention in
the authenticated transition. Prior passing CI belongs only to the earlier commit;
the correction needs its own CI run and independent review.

An independent read-only implementation review identified a pathname execution
race and incorrect missing-payload classification. The corrected launcher uses
the accepted executable descriptor, and regression tests cover both corrections.
Final exact-HEAD CI and review evidence belongs to the draft PR and handover.
The unchanged repository CI remains required. Local Elixir builds were not run
because they would create artifacts outside the owner's approved test root.

## Remaining qualification and deployment prerequisites

1. Independently review the exact six-file diff and CI candidate under Master Gate,
   then obtain a separate human merge decision. No merge is authorized here.
2. Select and qualify the authoritative prospective P0 registry, global case and
   approval uniqueness, authenticated human identity, predecessor evidence and
   durable acceptance. Synthetic journal uniqueness cannot establish these.
3. Appoint separated H/P/M/S/V/C principals and qualify authentication, protected
   keys, receipt freshness, finite receive deadlines and durable receipt custody.
   The synchronous synthetic callback has no independently supervised receive
   deadline and cannot be reused as a production transport.
4. Establish protected custody of all three original B0 objects and immutable
   launcher, interpreter, loader/library, kernel and isolation bindings. Qualify
   descriptor inheritance, access controls and copy-tool compatibility on the
   selected host. Same-UID chmod and HMAC keys do not establish these controls.
5. Qualify external supervision across controller death, descendant prevention,
   bounded stopping and independently observed checkpoints. A Python callback or
   a second object in one process supplies no independent observation.
6. Qualify storage fsync behavior, independent initial/transition acknowledgments,
   irreversible entitlement recording, restart exclusion and an external adverse
   reconciliation channel when this journal cannot confirm a disposition.
7. Establish a retained evidence store, independent retrieval and authorized
   retention owners for originals, outputs, receipts and dependency manifests.
   A temporary synthetic directory or future `/tmp` candidate is not an archive.
8. Recover the missing original R2 review or retain its explicit unavailable
   status. Obtain fresh current authority and an exact separate materialization
   grant before any real initialization, entitlement, candidate or payload effect.

`open_production` and `production_acceptance` always fail before storage effects.
No flag enables them. Replacing these denials requires separately authorized,
reviewed deployment integration and qualification. This candidate claims only
implementation readiness for that independent qualification.

## Authority

Base commit: `c4195ba245e3e8478b89ef3a8527f20c4a57148d`.
Base tree: `bcc8e0d1f1e3b0c6a090cb3f5f4af267e3570db8`.
B1-R2 blob: `63ecf479994fb2f08d53a82a2fcb99fcf6c491b6`.
Accepted ACQ-EXEC-05 R2 blob: `1fd0af3e23287bab8939876589abc064c5655b45`.

The original R2 technical Master Gate report remains unavailable or unverified.
Its reported contract-level disposition is not a recovered original review.
This implementation grant does not authorize an operational B1 case, entitlement,
candidate, installation, protected-host qualification, Gate A/B or AUTH_07.
