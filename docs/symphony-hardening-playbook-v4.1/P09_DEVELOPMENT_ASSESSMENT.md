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
