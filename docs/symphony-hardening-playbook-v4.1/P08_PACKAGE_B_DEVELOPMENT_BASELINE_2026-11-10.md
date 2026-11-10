# Package B development-source baseline checkpoint

This additive checkpoint records dormant, development-tested Package B source. The original Symphony owner issued `P08_PACKAGE_B_DEV_BASELINE_01` as a one-time sequencing exception allowing this source checkpoint to be published before formal R1b qualification. The exception covers the exact source, this document, one non-force branch push, one draft PR and the existing automatic PR-event CI effects. It grants no trusted execution or operational authority.

The owner states that the exact Package B static source and SF01 freeze were independently accepted, and adopts the retained development results for this checkpoint. This coding conversation prepared the source and publication. It is not the separately appointed Symphony ChatGPT Master Gate reviewer. The actual PR still requires that review and a later human merge decision.

## Governing authority and provenance

Read the [V4.1 authority index](README.md), [master roadmap](V4_1_MASTER_ROADMAP.md), [status ledger](HARDENING_STATUS_LEDGER.md), [canonical Gate 2 plan](../superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md), [P08 specification](GATE2_P08_HOST_EVIDENCE_SPEC.md) and earlier [Package A evidence checkpoint](P08_T04_D03_D04_SOURCE_EVIDENCE_CHECKPOINT_2026-11-09.md). Those records remain unchanged. The latest original-owner decision supplies this bounded source-publication exception; hashes and this derivative document cannot issue execution authority.

```ini
APPROVED_MAIN=9d05ef2707c58eb520aadd34660b41d6814871a4
APPROVED_MAIN_TREE=f91fd9227fb4379b93ccd56f45917b29ffb30b6d
HISTORICAL_V_COMMIT=d44d114ba5ff774fa8713aaa195fa37315a24852
HISTORICAL_V_TREE=8f4d2e96056c7b4f05c66cd324fd6f32f8bd1241
HISTORICAL_NINE_FILE_SCOPE_SHA256=320ced419294997d6e694d992b6f4fc788ae81f354f2988e602ea8087b502e5b
SF01_COMMIT=9b2b75ba67400ae1b8889218f4094096ad7762c0
SF01_PARENT=9d05ef2707c58eb520aadd34660b41d6814871a4
SF01_TREE=8e40b8880633dc42c090decd7596481b39e78931
SF02_COMMIT=a22247a190fbed7fc53500ad3e31c7876fdc2b5b
SF02_PARENT=9b2b75ba67400ae1b8889218f4094096ad7762c0
SF02_TREE=f81f4fb77e91eba62df08cb758527c83b88c79f1
```

SF01 preserved the accepted C01 source. SF02 changes only two lines in the portability test inventory helper so its package list, observed tree and baseline no longer share mutable fixture entries. All original test methods, assertions and the module-level `policy.install_write_audit()` call are preserved. Both source commits carry locally verified SSH signatures using the existing authorized account signer. SF01 was neither amended nor replaced.

The source-only SF02 tree contains 406 leaves: 395 inherited files and exactly eleven Package B additions. The separate signed documentation commit adds only this checkpoint, producing a 407-leaf PR tree. The actual documentation commit, PR HEAD/tree and GitHub synthetic merge identities must be recorded in the PR handoff after creation; they are not the SF02 source identity. A document cannot embed its own final Git tree without self-reference.

The historical C0 fixture also has 407 entries, but is a different input and identity. File counts do not establish equivalence. The refusal-only runner's complete source-inventory boundary is not updated or released by adding this document. Any future R1b profile must explicitly reconcile its exact approved source and integration-tree identities.

## Exact eleven-file source inventory

These are the reviewed SF02 source identities. Every Git mode is `100644`. The complete inherited tree is unchanged from approved main. The additional checkpoint document is excluded from this eleven-file source inventory.

```json
[
  {
    "path": "docs/symphony-hardening-playbook-v4.1/P08_T04_AUTHORITY_OPERATOR.md",
    "mode": "100644",
    "git_blob": "47d210d0435503deb8d5b03d32075687c0cf49ba",
    "bytes": 18141,
    "sha256": "e42fc2e1f10bbf6c59a4575568a21791bb4f2cc34688e6679dd999173d126a3a"
  },
  {
    "path": "tools/p08_authority/gate.py",
    "mode": "100644",
    "git_blob": "ec92e83978283a734b631bf763cca3e108058a31",
    "bytes": 21534,
    "sha256": "967339bbbc269aa89a9792fb3f956e5e4f18f551951a12e1976ba5af08187bf6"
  },
  {
    "path": "tools/p08_authority/profile-requirements.json",
    "mode": "100644",
    "git_blob": "fc6fd6e1b8776519f41ee7c1f25b2a0fc4ac311a",
    "bytes": 35511,
    "sha256": "0cf688495273e861c424def7e72afcd7b3841f1045ba456d974c3d5adc0af8e6"
  },
  {
    "path": "tools/p08_authority/qualification-vectors.json",
    "mode": "100644",
    "git_blob": "74fe31e05a7a2e0e8b46804b21afc68a00ab70cc",
    "bytes": 30938,
    "sha256": "84380bc0557e1a27b933734f015c0c382df618c1ba5669e30436780d1995f715"
  },
  {
    "path": "tools/p08_authority/record-schemas.json",
    "mode": "100644",
    "git_blob": "0f920aeeaf52f01b5b9e06c2ec220fcee2f2a52c",
    "bytes": 47739,
    "sha256": "349f8d1e405ed915481430100c6471dc91338186a645f1aa799fb95b6a0e7430"
  },
  {
    "path": "tools/p08_authority/verify.py",
    "mode": "100644",
    "git_blob": "7475f3a2a31d7f2a7af10a14a4dae565b4ff3e0f",
    "bytes": 74514,
    "sha256": "a01245e1ff8e439078655c8bfb08464c4a4b3eb382cae865ab9145b6827bb309"
  },
  {
    "path": "tools/tests/p08-portability-profiles.json",
    "mode": "100644",
    "git_blob": "22b4291b49dad0cbc314d4ce35093b83ec4dbf9b",
    "bytes": 4657,
    "sha256": "b36a5198b41d6c30a793b21a3954e0ed8cd833f6a590ac8b00b51e008efac092"
  },
  {
    "path": "tools/tests/p08_qualification_runner.py",
    "mode": "100644",
    "git_blob": "f631b8a4a8e49cef58d74450b64cc58a0f7f8ff7",
    "bytes": 32057,
    "sha256": "08f5cae8765fd8c5222bb86d5312dd2cdd3f0ed47934829414908ac273668e15"
  },
  {
    "path": "tools/tests/test_p08_authority_gate.py",
    "mode": "100644",
    "git_blob": "e51a12a4a78c0ab15a5591b62ee347a6c3eb6013",
    "bytes": 45561,
    "sha256": "86013652455743cecff6e301cd67e2567ae21cae3cee9cddd1cd210a83c26f57"
  },
  {
    "path": "tools/tests/test_p08_authority_portability.py",
    "mode": "100644",
    "git_blob": "8b9392dbc472fbc4c443f60a487b94de75e7d635",
    "bytes": 93329,
    "sha256": "c0ef7724a357bcd4ca2d13416a74bf48870aee1dd58208fd95ecaa65010077f3"
  },
  {
    "path": "tools/tests/test_p08_authority_verify.py",
    "mode": "100644",
    "git_blob": "044506aba43a60aa712224ee6fc58936031ece75",
    "bytes": 82869,
    "sha256": "360afac7f2f5f9e91a4ec73f2c45d5fd3ec4d83ce26a2fef3f8a534f64afe547"
  }
]
```

The six preserved historical blobs are `gate.py`, `profile-requirements.json`, `qualification-vectors.json`, `record-schemas.json`, `verify.py` and `test_p08_authority_gate.py` at the paths above. The three portability revisions are the operator document, qualification runner and verifier test module. The two added files are the portability profile description and portability test module. No frozen schema, gate or verifier behavior was rewritten. All fourteen unrelated historical T03/T04 additions are excluded; the old eight-commit lineage is not imported.

## Observed development execution

DEV-TEST-02 used the exact prospective tree now frozen as SF02. Its final applicable runs recorded 107 distinct development diagnostics, all passing:

- 35 of 35 gate methods.
- 35 of 35 verifier methods.
- 24 of 24 portability methods.
- 13 of 13 standalone runner diagnostics.

Final distinct totals were 107 executed, 107 PASS, zero FAIL, zero ERROR, zero skipped and zero blocked. The 24 previously blocked signed-fixture methods ran, followed by fresh reruns of the earlier 83 diagnostics. All 98 source scenario identifiers appeared in fresh final applicable logs without expected/actual mismatches. These observations remain specific to the source and development adapters. They do not transfer the historical 70-test/98-case PASS evidence to changed source.

All attempts remain visible. DEV-TEST-01 preserved the original PB15 shared-mutable-fixture failure. DEV-TEST-02 retained 110 actual method invocations: 109 PASS and one ERROR before the final corrected diagnostic runs. That ERROR came from the development write audit's handling of a directory-relative register open. An earlier worker refused before test execution, and two coordinator guards also stopped before unittest execution. Driver fixes, their exact differences, successful reruns and an initial packaging-scanner false positive are preserved. None is silently replaced by the final green totals.

The original R1a evidence directory exceeded its 33,554,432-byte limit by 909,099 bytes. That attempt and its archive remain blocked and unchanged. C01 separately corrected the inventory validator's universal size cap using the exact approved oversized inherited object. Repackaging did not retroactively qualify the original attempt.

## Development adapters and limits

The installed development interpreter was Python 3.14.4, SHA-256 `52e0a13e60a981d8c4b6478be2ba5176f69da07948a056bf49cf6f077e30cb41`. The approved `ssh-keygen` executable matched SHA-256 `2dd834413c9d3f4c0e3535b9fcf2e96e14c11f3d36fd23b6c5fc24e50411d051`. A matching version number, including B1 CI's Python version, does not prove the historical interpreter or full runtime closure is equivalent.

Disposable diagnostic copies omitted only the guarded test modules' import-time admission calls and supplied temporary output bindings. The verifier fixture binding received only the exact two owner-authorized payload identities through inherited read-only descriptors. Standalone selection drivers also executed exact reviewed method/helper ASTs. Test-method bodies and assertions were unchanged. Tracked production modules, gate/verifier implementations and the runner's refusal functions were not patched by these adapters. The official qualification launcher was not invoked.

Both historical fixture payloads matched their separately pinned lengths and SHA-256 values before use and at postchecks. No historical input was reconstructed, substituted or downloaded. Synthetic owner, reviewer and rogue Ed25519 roles used separate disposable keys in private per-attempt workspaces. No operational or Git signing keys were used for the development tests. The source-freeze commits later used the separately authorized existing Git signer.

Finite deadlines, resource limits, fixed command allowances and registered process cleanup bounded development execution. All 727 registered child processes were reaped and independently checked absent. These application-level controls and mock-based cases do not establish kernel filesystem/network confinement, arbitrary descendant containment, authentic operational custody or general host portability. Synthetic signed chains and a finite sentinel demonstrate only their observed source behavior under the development adapter.

## Retained private evidence identities

The following archives were remeasured and rehashed for this checkpoint. Only their names, lengths and hashes are public. Original archives, raw logs, private correction diffs, fixture payloads, private custody mappings and keys remain in original private custody. Listing an archive hash does not reproduce its contents, authenticate an owner decision or guarantee future availability.

```json
[
  {
    "name": "P08-T04-Package-B-R1a-001-e16cae9f-PRIVATE-review.zip",
    "bytes": 32970620,
    "sha256": "3c2a9b8534ff47a5810165a75b27d36c27756c677e0529f109e5c7f1efea700d",
    "purpose": "Original R1a attempt, blocked and preserved"
  },
  {
    "name": "P08-T04-Package-B-R1a-C01-8e40b888-PRIVATE-review.zip",
    "bytes": 3191695,
    "sha256": "0e2b8fd146456d7599c61698927332f1cbdc29f9f0504eeccf2bcabc26e49b09",
    "purpose": "C01 static source correction evidence"
  },
  {
    "name": "P08-T04-Package-B-SF01-9b2b75ba-PRIVATE-review.zip",
    "bytes": 1304797,
    "sha256": "4937116d27079fb17a420537e6063489b0b3473e9559db706fc0c1902f34d5a6",
    "purpose": "SF01 source freeze evidence"
  },
  {
    "name": "P08-Package-B-DEV-TEST-01-PRIVATE-results.zip",
    "bytes": 1294444,
    "sha256": "87b573e20044ea14245263d3fd8d314cadadef9e36e0c90cc03681895c5fdddf",
    "purpose": "DEV-TEST-01, including original PB15 failure"
  },
  {
    "name": "P08-Package-B-DEV-FIX-01-PRIVATE-results.zip",
    "bytes": 1592713,
    "sha256": "ad5cb041f9b1f0dc4d11e774e74d9aa8fb29add47e9b19dd4f261cda91fff467",
    "purpose": "DEV-FIX-01 source correction and 83 diagnostic passes"
  },
  {
    "name": "P08-Package-B-DEV-TEST-02-PRIVATE-results.zip",
    "bytes": 8047079,
    "sha256": "5f80881a4b37be5f294679a6ad2a79f580be43ae759a6fa82c00897534791387",
    "purpose": "DEV-TEST-02, final 107 distinct development passes"
  }
]
```

The DEV-TEST-02 archive passed CRC and 687 of 687 payload checksums. It excludes historical fixture bytes, generated private keys, the three original workstation-specific literals and inherited media payloads. All predecessor evidence and failures remain preserved. The original Symphony owner remains the evidence-decision custodian.

## Refusal-only release boundary and formal R1b

The external-release interface remains typed and refusal-only. Missing, malformed, unconfigured or unauthenticated release descriptions refuse. A candidate-controlled JSON approval, matching hash, author review record, configurable callback or selected trust anchor cannot grant admission. The descriptive profile is not an approval instance. No positive release-authentication mechanism, provider registration, successful admission constructor, execution token or test-only production bypass is supplied.

Formal R1b qualification is not complete or authorized by this publication exception. It still requires a separately accepted authentication protocol, independent custody and handoff, review of the corrected source identity, approved exact source/fixture profiles, the full pinned runtime closure, host observations, finite commands/probes, attempt slots and explicit human release of that exact attempt. Ordinary development unit-test execution through an adapter is not a formal launcher receipt or operational containment proof.

## PR checks and human merge gate

This PR publishes the independently reviewed Package B development-tested source checkpoint. It does not establish formal R1b qualification, positive release authentication, production authority or Gate 2 activation.

The owner authorized existing automatic PR-event CI for this exact candidate, including pinned Codex installation through the existing privileged workflow, namespace setup, Elixir dependency acquisition, B1 controls and established build/test jobs. There are no workflow, branch-protection or qualification-launcher activation changes. No manual workflow dispatch is authorized.

Required checks remain `make-all` and `validate-pr-description`, both from the GitHub Actions app, app ID `15368`, with strict current-base checking. Their actual conclusions and run/commit identities belong in the independent PR review. Those checks do not execute Package B Python qualification tests, and green CI cannot replace the retained development diagnostics or formal R1b.

The separate Master Gate reviewer must inspect the actual full PR diff, protected-main baseline, current HEAD/tree, synthetic merge identities, signatures, source inventory, this checkpoint, governing authority and required checks. The source preparer cannot substitute its own assessment for that review. Merge requires a subsequent explicit owner decision and human action. Only the actual merged protected-main commit and independently verified post-merge tree establish a new authoritative repository baseline. A draft PR or local signed commit is not a merged baseline.

```ini
CHECKPOINT_KIND=DORMANT_DEVELOPMENT_TESTED_SOURCE
OWNER_SEQUENCING_EXCEPTION=ONE_TIME_DEV_BASELINE_01
FORMAL_R1B_QUALIFICATION=NOT_COMPLETE
R1B_FORMAL_EXECUTION=NOT_AUTHORIZED
POSITIVE_RELEASE_AUTHENTICATION=UNCONFIGURED
PRIVATE_FIXTURE_PUBLICATION=PROHIBITED
OPERATIONAL_QUALIFICATION=NOT_AUTHORIZED
TRUSTED_INSTALLATION=NOT_AUTHORIZED
P09_ACTIVATION=NOT_AUTHORIZED
MERGE=REQUIRES_SEPARATE_EXACT_REVIEW_AND_HUMAN_ACTION
GATE2_ACTIVATION=NO
AUTH_07=SUSPENDED_UNCONSUMED
```
