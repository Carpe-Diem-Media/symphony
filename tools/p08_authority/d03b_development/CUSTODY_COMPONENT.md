# F09 custody component

This code is dormant development source. `ledger.Register` and
`HostRegisterCustody` still refuse with `REGISTER_CUSTODY_UNCONFIGURED`. The
qualification runner is unchanged. No installed loader selects this component.
These files grant no host execution, formal R1b or Gate 2 authority.

## Trust and storage

`custody._HostCustody` implements the existing internal `_RegisterStore`
interface. Its root, owner fingerprint and complete source/runtime/profile
bindings are installation inputs that a future trusted owner procedure must
confirm independently. They are not worker inputs or approval capabilities.
There is no environment selector, operational CLI or provider registration.

The owner signs a closed canonical enrollment using a separate owner-controlled
key. The enrollment binds its ID, database ID, actual root/anchor/lock file
identities, initial empty-anchor creation time, current boot, complete D03
`BINDINGS`, custodian fingerprint and a validity interval of at most one hour.
The owner must preallocate the anchor and lock before signing. Recovery never
creates either. Reusing the original certificate after truncation or replacement
does not authorize initialization. Duplicate first initialization refuses.

The fixed layout beneath that root is:

```text
owner/allowed             owner-confirmed public identity
owner/enrollment          canonical signed enrollment
owner/enrollment.sig      owner signature, enrollment namespace
authority/allowed         enrollment-pinned custodian public identity
authority/key             host-only checkpoint key, never worker-visible
authority/lock            preallocated, pinned, non-stealable flock inode
authority/anchor          protected append-only current-head witness
authority/receipt         signed projection of the current witness head
authority/receipt.sig     checkpoint signature
state/register.sqlite3    one-use release register
```

Directories require mode 0700. Files require 0600, one link, a regular inode
and the effective host UID. Reads check named and opened identities, length,
mtime and ctime. The future installed host must additionally establish stable
trusted ancestry, ACLs, external owner confirmation and isolation from the source
actor. Same-UID component fixtures cannot establish those properties.

Only three fixed signature operations exist. They verify owner enrollment,
verify the current checkpoint, or sign the exact current witness-head receipt.
The executable is pinned `/usr/bin/ssh-keygen`; keys, principals, namespaces and
arguments are fixed by each operation. Environment is cleared, descriptors are
closed, and each crypto child has a three-second deadline. Signing arbitrary
payloads or selecting an executable is unavailable.

## Freshness and rollback

The independently controlled host owns `authority/anchor` and its current
sequence. Every access rereads authenticated enrollment, the complete chained
witness, and its exact signed receipt under the pinned lock. A previously valid
checkpoint is insufficient when its sequence/hash differs from that witness.
The witness is bounded to 8 MiB; exhaustion refuses. Routine malformed, stale,
duplicate or terminal requests are checked before reservation and do not grow
the witness. There is no automatic truncation, rotation, reset or rearming.

The host appends and fsyncs its witness before publishing either receipt file.
Receipt loss, partial replacement or interruption therefore leaves a mismatch
or non-ACTIVE state. It never reconstructs an ACTIVE head from the register.
The host must retain the witness independently of register/checkpoint backups.

This protects the database/checkpoint pair against rollback only while the host
witness remains authoritative. An administrator who restores the entire witness
and its valid signed history can defeat freshness. Signatures alone do not
solve that problem. Current source-account Docker/libvirt access and sudo-group
membership prevent a claim of independent custody on this workstation. No
permission change, live enrollment or independence claim occurs here.

## Lifecycle and persistent ordering

All transitions belong to the trusted host. The original owner controls initial
enrollment, the public trust handoff, retirement and any later recovery decision.
No transition below grants new execution authority.

- `UNENROLLED`: no authentic initialized witness. Only owner preallocation and a
  verified, current enrollment may begin. Missing authority during recovery is
  refusal, not this initial state.
- `ENROLLMENT_PENDING`: first durable witness entry after signature, boot,
  identity and empty-anchor checks. Only `BOOTSTRAP_RESERVED` may follow normally.
- `BOOTSTRAP_RESERVED`: durable first-initialization reservation. The exact
  `BootstrapGrant` and fixed database locator may enter `BOOTSTRAPPING` once.
- `BOOTSTRAPPING`: recorded before creating SQLite. After schema creation,
  database/file/directory fsync and exact identity measurement, activation records
  revision zero and the semantic snapshot. Partial initialization cannot retry.
- `ACTIVE`: a complete matching database, witness and signed projection. Every
  SQL transaction rechecks the exact head before making an effect.
- `MUTATION_PENDING`: durable reservation immediately before the first SQL
  mutation. Read-only rejection checks happen first under the same locks. A
  process death here becomes `INTERRUPTED`, then quarantine on recovery.
- `INTERRUPTED`: before SQLite commit, the host records the proposed snapshot.
  Only the still-running exact transaction may acknowledge a completed SQL commit
  after fsync, producing revision `r+1`. Recovery never performs this transition.
  Missing acknowledgment blocks reuse even when SQLite committed successfully.
- `MISSING_HISTORY`: an enrolled register disappeared. The host records this
  reason and then enters `QUARANTINED`. It does not create a new register.
- `QUARANTINED`: terminal for inconsistent, lost or uncertain history. No reset,
  bootstrap, completion or automatic recovery is permitted.
- `RETIRED`: absorbing owner retirement. No further admission or re-enrollment
  exists in this component.

A narrowly defined known rejection before prepare may return a reserved intent
to ACTIVE only after observed SQL rollback, exact old snapshot and unchanged
file identity. The witness retains both reservation and abandonment. This is
not crash recovery, cannot change consumed history and cannot run after prepare
or an uncertain commit. Ordinary input rejections never reserve in the first
place. Interrupted or consumed releases never regain entitlement.

The complete witness validates closed states, transition order, revision/hash
progression, chained entries and nondecreasing clock observations. Missing,
expired, future, wrong-boot, mismatched or invalidly signed authority refuses.
Existing host checks retain signed release revocation, live expiry and exact
source/worker binding. Custody does not replace release signature verification.

## Verification boundary

`tests/f09_fixture.py` and `tests/f09_process_probe.py` are test-only. Operational
source never imports them. Fixtures generate disposable owner, custodian and
rogue Ed25519 keys under `scratch`. These same-UID keys exercise actual signature
verification and durable ordering, not independent host custody.

`run_tests.py` admits only inspected synthetic key/signature operations and the
fixed finite crash probe, in addition to the existing negative entry-point
checks. Its Python audit rejects sockets and out-of-workspace writes. It is not
kernel containment, and its audit does not mechanically sandbox crypto children.
No qualification admission call is removed by these tests.

The old host preparation tests reference historical D02 crypto paths. The
handoff records a separate diagnostic copy that changes only those fixture
location literals to newly generated synthetic bytes. It preserves all test
assertions and all production source bytes. Those three observations establish
fresh crypto behavior, not a rerun of the historical signature's exact bytes.

H01/H02 validators, launch logic, pidfd/start evidence, fixed native executor,
worker image builder and worker remain unchanged. Native tests use Rust's pure
test entry point, never `--session` or a system-bus self-test. Image preparation
copies and measures files only; it does not mount, install or execute a worker.

## Next host handoff

Before any live test, an independent reviewer must accept the exact source and
owner must confirm the public anchor and actual protected storage. A separately
reviewed fixed installation adapter must supply those confirmed inputs to this
component and existing `host.Host`; none is installed or positively enabled by
this change. The unchanged image builder still consumes a pinned historical
runtime manifest, so its input availability and current bytes must be rechecked.

The handoff includes a measured preparation image and native executable, but
root ownership, current-boot PID1 observations and the real restricted source
route remain unqualified. The first proposed test retains the existing fixed
`p08-d03-worker.service`, network-none DynamicUser profile, finite worker suite,
CPU 50%, memory 256 MiB, 16 tasks, runtime 20 seconds and stop timeout 2 seconds.
Its separately authorized effects and witness requirements are recorded in the
external handoff. No live command is runnable under this component grant.
