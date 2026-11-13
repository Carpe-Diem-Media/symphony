# P09 dormant assessment foundation

Task `P09_DEV_01` authorizes local source development and unprivileged component
tests on base `2ba7cb5f49399cbe41ea527af5abcdac0dda1281`, tree
`75d6df5e972bd253b272974dd8adec6452f5e00d`. It does not qualify P09, activate Gate 2
or accept H-100. The authority index in [README.md](README.md) distinguishes
historical G00 materialization locks from later scoped implementation grants.
The canonical plan's P01–P08, G00 and numerical-profile prerequisites still guard
integrated mechanical qualification.

## Interfaces and evidence limits

`SymphonyElixir.Gate2.QualificationIdentity.new/1` requires exactly the fields
listed by `fields/0`. Candidate, source-tree and upstream identities use 40
lowercase hex digits; every other field uses a SHA-256 digest of its exact
component or measurement record. The identity digest covers the fixed ordered
field/value pairs encoded as compact JSON. It is not a signature. Version names
and missing or wildcard bindings refuse.

`EvidenceApplicability.evaluate/3` checks the closed evidence envelope, equality
of identity declarations, explicit UTC cutoff, observation interval and SHA-256
of supplied bytes. Evidence bytes are nonsecret inputs, bounded to 1 MiB each.
The envelope fields are `claim_id`, `proof_class`, `identity`, `observed_at`,
`expires_at`, `scope`, `sha256` and `bytes`. Times are nonnegative signed-64-bit
UTC-second declarations, with `observed_at <= cutoff < expires_at`. Reversed,
future, stale or out-of-representation intervals refuse. The caller supplies the
cutoff; this is not an authenticated host clock. Claim labels are limited to six
bytes, proof-class labels to 32 and scope labels to 64. Envelope and identity
maps must have the exact field count before their keys are inspected.
Only fixed expected keys are checked; attacker-controlled keys are never sorted.

Only `DEVELOPMENT_COMPONENT` evidence can be characterized. The byte check
recomputes a digest; it does not trust a `PASS`, `verified` or `accepted` field.
Provenance and time remain declared inputs. Host proof, unsupported host/config
evidence and independent acceptance refuse. Matching bytes produce
`VERIFIED_BYTES` artifact integrity. The following remain separate and always
unverified in this component:

- `claim_applicability`, whether the artifact applies to the exact claim.
- `evidence_catalog_binding`, whether it applies to this catalog revision.
- `proof_status`, authenticated claim-specific mechanical proof.
- `independent_acceptance`, human acceptance under independent authority.

Relabeling or repeating identical bytes across different claims can characterize
bytes only. Changing the claimed catalog meaning and recomputing a digest cannot
verify applicability. A public digest identifies bytes; it authenticates neither
their origin nor their claims. Unsupported caller-supplied verification fields
refuse. No component test or JSON assertion supplies independent host custody or
human review. The later trusted claim verifier is not implemented here.

`Qualification.assess/3` owns claim/proof-slot validation. It returns every
OB-001–OB-026, ET-001–ET-013 and BP-01–BP-19 disposition. The versioned
[qualification manifest](GATE2_IMPLEMENTATION_QUALIFICATION_MANIFEST.json) pins
its source references and records all current evidence as missing/unverified.
Its proof classes follow canonical plan section D. BP requires both the
intended-holder positive control and the unauthorized-channel negative control.
ET limitations remain exact, including diagnostic-only and nonaccepted claims.
No transfer establishes a selected implementation proof.

The report contains the declared binding, cutoff, catalog digest and sanitized
per-proof metadata. It omits evidence payloads. Its assessment digest hashes OTP
deterministic external-term encoding without the digest field itself. JSON
round-trip key order does not confer authority. Evidence order does not affect
the report; any duplicate proof slot, including identical bytes, blocks it.
`requirements_sha256` identifies the catalog used to produce the report. It
does not bind the supplied evidence to that catalog or authenticate applicability.
The catalog and its digest are compiled from the same single read of its bytes.

## Bounded development inputs

`assess/3` accepts a proper list of at most 218 records, one per frozen proof slot.
Aggregate supplied payload bytes are limited to `218 * 1_048_576 = 228_589_568`.
This 218 MiB ceiling derives from the existing 1 MiB artifact ceiling and the
closed slot inventory. It introduces no independently chosen operational quota.
Repeated bytes count once per supplied record, even when binaries share storage.

The bounded walk examines at most 219 cons cells before grouping or artifact hashing.
Count overflow, aggregate overflow, an oversized artifact or an improper tail
rejects the entire collection. Bounded envelope, identity and metadata validation
also happens before grouping. No valid prefix is characterized. Within the
bound, duplicate slots still conflict. Empty and incomplete lists remain
unqualified. These limits constrain work over already allocated Elixir terms;
they are not a network decoder or a process-memory isolation mechanism.

The manifest records `DEVELOPMENT_PARSER_ONLY` and
`operational_capacity_authority=UNCONFIGURED`. The canonical plan's K3 requires
named owners, measurements and independent acceptance for operational capacity.
No accepted P09 host-capacity profile is supplied by this task, so operational
qualification remains refusal-only regardless of development characterization.

## Lifecycle and recovery

1. `UNQUALIFIED` is the initial state. Missing, invalid, conflicting, stale,
   mismatched or unsupported artifacts keep the assessment here.
2. `UNQUALIFIED → CHARACTERIZED` requires every OB proof-class slot, both BP
   control slots and every ET applicability/review artifact slot to have
   digest-verified supplied bytes with matching identity declarations and current
   declared intervals within the development input limits. This describes
   artifact bytes and declarations only. Claim applicability, evidence-to-catalog
   binding, proof verification and independent acceptance remain unverified.
   An `IR` artifact slot is not authenticated independent acceptance.
3. `CHARACTERIZED → MECHANICALLY_QUALIFIED` requires accepted predecessor and
   numerical-profile evidence plus claim-specific proof verifiers. This slice
   provides no such verifier, so the transition returns
   `:mechanical_verifier_unconfigured` even with complete component artifacts.
4. `MECHANICALLY_QUALIFIED → INDEPENDENTLY_REVIEWED` requires authenticated
   external acceptance of the exact identity and evidence manifest. This slice
   provides no acceptance interface, so it returns
   `:independent_review_unconfigured`. All skipped/reversed transitions refuse.

Assessment and transitions have no persistent or operational side effects.
Callers may save a report as a review artifact. `reload/4` recomputes from the
current identity, bytes and cutoff, ignoring saved state or acceptance claims.
Expiry or changed inputs can regress characterization to `UNQUALIFIED`.
Neither a report nor its digest is an execution entitlement. RuntimeIsolation,
IsolationProfile and Governance.Check do not consume this module.

## Verification and next dependency

Targeted unprivileged tests:

```sh
cd elixir
mise exec -- mix test test/symphony_elixir/gate2_qualification_manifest_test.exs test/symphony_elixir/gate2_governance_projection_test.exs test/symphony_elixir/runtime_isolation_test.exs test/symphony_elixir/governance_check_test.exs
```

The next P09 implementation dependency is a separately reviewed, claim-specific
proof-verification contract bound to accepted P01–P08/G00/numerical profiles and
current host observations. It must define trusted evidence provenance and
external review verification before either later lifecycle edge can open.
This foundation deliberately supplies neither a generic verifier callback nor a
caller-controlled approval flag. Real Codex/provider/host qualification remains
outside this task. Existing H-080B proof requirements are unchanged.

## P09-DEV-02 frozen-reference binding

Task `P09_DEV_02` authorizes a dormant local development increment on merged
main `4dc2cc0369874dc152931c38464e1fdfa87704f2`, tree
`a659f7c9d8e92ed920b9179bbb1cd22b4cd3dfd5`. It adds
`SymphonyElixir.Gate2.FrozenClaimBinding` without changing the frozen inventory,
qualification manifest, operational admission or either higher lifecycle guard.

The single supported selection is `ET-005` / `EB`, and the verified property is
**frozen-reference binding only**. The accepted freeze packet records H-080B's
original executable/configuration/platform scope and the need for separate
0.162.1 proof. The [freeze acceptance](GATE2_INVENTORY_FREEZE_ACCEPTANCE_2026-11-02.md)
establishes the accepted record. The canonical plan pins its raw bytes; K5 and
the merged catalogue define ET membership and EB/IR slots. The accepted source
record is the authoritative producer of this reference definition. There is no
authenticated producer of a new implementation proof in this slice.

Compilation verifies the exact raw SHA-256 pins of the packet, acceptance record,
canonical plan and merged P09 catalogue, then decodes the same reads. It compares
the catalogue's ET-005 projection and EB/IR membership with the pinned definition.
A future authorized catalogue revision requires a new reviewed verifier pin;
recomputing a caller-provided hash cannot select a new authority.

`reference/0` returns the fixed catalogue digest, full frozen ET-005 definition
and source descriptor. That metadata alone is not a verification result.
`evaluate/3` takes a list of at most one binding, a `QualificationIdentity` and
an explicit UTC cutoff. The binding has exactly these four fields:

- `catalog_sha256`, the pinned merged catalogue's exact raw identity.
- `definition`, the complete frozen ET-005 row, including inventory references,
  linked obligations, authority class, transfer limits and new-proof requirement.
- `source`, the exact descriptor returned by `reference/0`, including accepted
  source commit/tree, packet blob/digest and plan/acceptance digests.
- `evidence`, the existing closed eight-field development envelope. It must
  select ET-005/EB, bind every identity declaration and contain the exact accepted
  packet bytes. The existing 1 MiB artifact bound and UTC interval checks apply.

The list walk inspects at most two cells and refuses duplicates or conflicts
before hashing. Invalid shape, changed source, changed meaning, wrong catalogue,
wrong proof class or unsupported scope returns `REFUSED` with a fixed reason.
The byte-integrity check reuses `EvidenceApplicability`; a valid digest of some
other artifact remains insufficient. No producer name, success flag, callback,
runtime file path or expected-hash override is accepted.

The result keeps the properties separate:

- `artifact_integrity=VERIFIED_BYTES` means supplied bytes match their digest.
- `reference_binding=VERIFIED` and
  `reference_provenance=PINNED_ACCEPTED_RECORD` require those bytes to match the
  accepted packet, exact definition, source descriptor and catalogue as well.
  This identifies accepted content provenance, not the submitter or transport.
- `claim_applicability`, `run_provenance`, `proof_status`,
  `independent_acceptance` and `operational_host_qualification` remain
  `UNVERIFIED`, even after a reference binds. Matching qualification declarations
  do not independently measure the candidate or authenticate a host clock.

Each assessment begins `UNVERIFIED` and ends `REFERENCE_BOUND` only after all
guards pass; otherwise it ends `REFUSED`. Refusal is terminal for that assessment.
`reload/4` ignores saved state and recomputes from current records, bytes, identity
and cutoff. A reference can therefore become refused on expiry or replacement.
Evaluation has no persistent writes or runtime/host effects. Retrying recomputes
the same bounded checks and confers no execution entitlement.

The new result is not a qualification evidence envelope. Passing it to
`Qualification.assess/3` refuses; all 218 proof slots remain unverified. Neither
mechanical qualification nor independent review is opened. The next dependency
is still an independently reviewed proof producer/verifier contract, accepted
predecessor and numerical profiles, and exact applicable host observations.

Focused regression command:

```sh
cd elixir
mise exec -- mix test test/symphony_elixir/gate2_frozen_claim_binding_test.exs test/symphony_elixir/gate2_qualification_manifest_test.exs test/symphony_elixir/gate2_governance_projection_test.exs test/symphony_elixir/runtime_isolation_test.exs test/symphony_elixir/governance_check_test.exs
```

## P09-DEV-03 implementation-proof contract

The scoped owner task `P09_DEV_03` authorizes local source development and
unprivileged tests on main `90764cc8eabc051c529e7135427a9879c4a5584d`, tree
`d1c1503ec05d7aef03537478c1349526e6eb7eae`. It adds the dormant
`SymphonyElixir.Gate2.ImplementationProof` boundary for **ET-005/EB only**.
`EB` means `EVIDENCE_BINDING` under canonical plan section D. K5 preserves
H-080B's historical acceptance and separately requires proof for the selected
Codex 0.162.1 implementation. No frozen inventory or qualification slot changes.

### Authority and producer selection

The existing `FrozenClaimBinding.reference/0` owns the exact frozen claim,
catalogue and accepted source descriptors, including the pinned plan defining EB.
The new record must match that whole reference. Those version-controlled pins
authenticate reference content only. They cannot authenticate a new observation.

P08's [host-evidence specification](GATE2_P08_HOST_EVIDENCE_SPEC.md), sections
1.4, 2.3, 5 and 11, describes independently installed observer/custody and
qualification boundaries. Its header still identifies that specification as
proposed. It is not an accepted ET-005 implementation-proof producer. The
[P08 authority operator procedure](P08_T04_AUTHORITY_OPERATOR.md), sections
"Operator trust before verification" and "Refusal-only external release",
requires independent identity/custody and refuses caller-created receipts.
`AttemptBoundary` and the qualification runner retain their deliberate verifier
refusals. This increment reuses those trust limits and the existing P09 identity
and envelope; it introduces no replacement signing, installation or host protocol.

No accepted new-run ET-005 producer or substantive verifier is available.
Consequently **all implementation-proof verification refuses**. Neither a
process name, path, authority-record hash, self-declared signature, caller key,
test fixture nor an independently intact artifact establishes producer authority.

### Closed development record

`assess/3` receives Elixir terms, not raw JSON or a filesystem path. The record
has exactly nine string keys, with no extension or approval fields:

- `schema` is `P09-ET005-EB-IMPLEMENTATION-1`.
- `reference` equals `FrozenClaimBinding.reference/0` in full.
- `selected_implementation` is exactly `codex-cli 0.162.1`.
- `evidence` is the existing closed eight-field development envelope. Its claim
  is ET-005, proof class EB, scope DEVELOPMENT_COMPONENT, and all sixteen
  `QualificationIdentity` declarations must match the supplied current identity.
  These cover candidate, source tree, upstream, patch, executable, helper,
  scanner, kernel, LSM, networking, storage, crypto, configuration, policy,
  capacity and host-profile digests. Matching declarations are not measurements.
- `producer` has `component_sha256` and `authority_record_sha256`, both declared
  SHA-256 references. No key or authority can be selected through them.
- `observation` has `observation_id`, `run_id`, `attempt_id`, `started_at` and
  `completed_at`. The IDs are 64 lowercase hex declarations, using P08's nonce
  representation without claiming uniqueness or enrollment. Times use the
  existing nonnegative signed-64-bit UTC-second representation.
- `custody` has `evidence_id`, `evidence_sha256`, `custody_record_sha256` and
  `integrity_method`. The first two must match the observation ID and artifact
  digest. The custody-record digest is an untrusted reference. The only method
  is `SHA256_SUPPLIED_BYTES`, never a signature or custody-authentication method.
- `prerequisites` has exactly `p08_host_qualification`, `capacity_profile` and
  `independent_review`, each `UNVERIFIED`. This slice cannot accept a supplied
  predecessor, operational profile or review assertion.
- `claimed_result` is PASS, FAIL or UNCERTAIN. It is never a verified result.

The observation must satisfy `started_at <= completed_at = observed_at <= cutoff
< expires_at`. Future, reversed, missing, mismatched and expired declarations
refuse. The cutoff and interval are supplied declarations, not an authenticated
clock or an operational validity grant. No new operational lifetime is chosen.

At most one record is inspected, with at most two list cells examined before
hashing. Duplicate, conflicting, flooded, improper or non-list submissions
refuse as a whole. The existing 1 MiB artifact ceiling, fixed field counts,
fixed labels and digest/time representations bound development validation.
No caller keys are sorted or recursively enumerated. These checks constrain
already allocated terms, not a network decoder or accepted host capacity.

### Properties and lifecycle

`assess/3` can establish `artifact_integrity=VERIFIED_BYTES`,
`catalog_binding=MATCHED_PINNED_DEFINITION` and a current **declared** interval.
It cannot establish producer/custody/observation authenticity, replay protection,
actual implementation applicability, host/profile qualification, proof status,
independent acceptance or a verified result. Those properties remain UNVERIFIED.
Recomputing a digest after substitution may pass byte characterization; it never
passes proof verification. This distinction is exercised directly by tests.

The record lifecycle has these guarded transitions:

1. No record yields ABSENT. A single submitted record enters RECEIVED_UNTRUSTED.
2. Exact schema, frozen reference, selected implementation, identity, correlated
   metadata, declared interval and supplied-byte integrity yield STRUCTURALLY_VALID.
   Any failed guard yields REFUSED with a fixed machine-readable reason.
3. SOURCE_AUTHENTICATED requires an accepted independently controlled producer
   and custody verifier. The interface is unconfigured, so `verify/3` refuses
   with TRUSTED_IMPLEMENTATION_PRODUCER_UNCONFIGURED after structural success.
4. CLAIM_APPLICABLE additionally requires accepted exact host/profile and fresh,
   replay-protected observations. PROOF_VERIFIED additionally requires substantive
   ET-005/EB checks. Neither state is reachable here. Independent review remains
   separate even from those future states.

Verification always terminates REFUSED and preserves the achieved
`structural_state` and lifecycle path. A structural result is no execution token.
There are no persistent writes, host probes, processes, callbacks or operational
side effects. REFUSED is terminal for that assessment. A new call rechecks all
inputs; retry supplies neither authority nor a reset of consumed entitlement.

`reload/4` discards saved states, hashes, claimed PASS and acceptance flags, then
calls current verification. It rechecks the compiled pinned reference and current
supplied identity, bytes and cutoff. It does not independently observe the host
or reread deployment files. Changed inputs or expiry may regress the structural
state; no saved record can restore authentication. Without an authoritative
receipt store, cross-call replay detection is unverified. Repeated receipts,
including those presented from a fresh process with renewed IDs or times,
always refuse proof verification. No synthetic fixture is recorded as real proof.

`Qualification`, operational RuntimeIsolation and Governance.Check do not consume
this result. All 218 operational proof slots remain unverified, both higher
qualification edges remain closed, and qualification remains UNQUALIFIED.

### Next dependency and verification

The next dependency is an independently accepted ET-005/EB producer/verifier
contract bound to the actual installed producer, exact source/binary/configuration,
qualified host/profile, authenticated clock/custody and replay history, and
substantive new-implementation checks. P01-P08, accepted numerical profiles and
independent proof review remain prerequisites. No host execution, signing,
source publication, H-100 or Gate 2 authority follows from this component.

Focused command:

```sh
cd elixir
mise exec -- mix test test/symphony_elixir/gate2_implementation_proof_test.exs test/symphony_elixir/gate2_frozen_claim_binding_test.exs test/symphony_elixir/gate2_qualification_manifest_test.exs test/symphony_elixir/gate2_governance_projection_test.exs test/symphony_elixir/runtime_isolation_test.exs test/symphony_elixir/governance_check_test.exs
```

The existing complete local gate is `make all`. Its H-080B sandbox self-checks
exercise finite Python sentinels with network disabled; they do not start a model
turn or use a live provider, and they do not establish this ET-005 proof.
