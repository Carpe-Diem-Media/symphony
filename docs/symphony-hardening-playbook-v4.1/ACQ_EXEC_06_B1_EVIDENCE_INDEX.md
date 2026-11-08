# ACQ-EXEC-06 B0/B1 evidence index

This investigator-authored index preserves the recoverable planning and review record for ACQ-EXEC-06. It is documentation for independent Master Gate review. It does not issue a B1 writing grant, freeze B0 bytes, reopen a terminal planning case or authorize operational use.

The [owner's evidence-preservation assignment](ACQ_EXEC_06_EVIDENCE_PRESERVATION_AUTHORIZATION.md) authorizes one documentation branch and one draft pull request. The assignment permits preservation of these historical records and this index. It excludes the B0 source, companion payload and complete source export. Historical source-authoring and planning approvals below remain limited to their original scopes.

Prepared on 2026-11-08. All 23 preserved originals are complete UTF-8 message bodies recovered through the original conversation backing records. Their metadata and the narrative in this index are new investigator observations. No pre-existing governing document is changed.

## Status meanings

- `REVIEWED` means a recovered review record identifies the exact review target and states its decision. It does not grant operational authority.
- `ACCEPTED_AT_PLANNING_LEVEL` describes a decision limited to a planning contract. It does not establish an implementation, qualified mechanism or permission to write.
- `REPORTED` means a specified source states a fact that this assignment has not independently established from the primary record.
- `UNVERIFIED` means a required identity, authorship or observation has not been authenticated for the stated purpose.
- `NOT_AUTHORIZED` means this assignment does not permit the action.
- `NOT_YET_ESTABLISHED` means the required evidence or capability has not been established here.
- `UNAVAILABLE_OR_UNVERIFIED` identifies a required original that could not be recovered or authenticated. No substitute original is created.
- `VERIFIED` in the inventory means byte equality to the identified recovered backing object. For the three B1 packets it also means equality to the supplied prior independent length and SHA-256. Verification of received bytes does not authenticate an external reviewer whose text arrived through a user-supplied relay.

## Governing baseline and authority

The evidence agent retrieved the live protected GitHub `main` ref and checked it independently through Git transport. At 2026-11-08 05:31:26 UTC the ref remained:

```ini
REPOSITORY=JCSchoeman96/symphony
SELECTED_BASE_MAIN_SHA=4971ddde384ef54b06498db438d2bfe36a0f108a
SELECTED_BASE_MAIN_TREE=540617e1c62af1550059113c5166bea315cc6015
BASELINE_MOVEMENT=NONE_OBSERVED
MAIN_PROTECTED=YES
REQUIRED_CHECKS=make-all,validate-pr-description
REQUIRED_CHECK_APP_ID=15368
```

The branch starts at that commit. Historical evidence keeps its original baseline references and bytes. A later movement of `main` would not rewrite those references or authorize an automatic branch update.

The repository authority order and accepted scoped decisions remain in force. Read the governing documents in that context:

- [Master roadmap](V4_1_MASTER_ROADMAP.md), Git blob `4b0528bdc0647d889b42ebc478081d5b873898fe`.
- [Unified execution roadmap](../SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md), Git blob `5ef99584283850482df822e8935428477353797c`.
- [Accepted ACQ-EXEC-05 R2 synthetic qualification plan](ACQ_EXEC_05_R2_SYNTHETIC_QUALIFICATION_PLAN_2026-11-06.md), Git blob `1fd0af3e23287bab8939876589abc064c5655b45`.
- [R2 Master Gate plan acceptance](ACQ_EXEC_05_R2_MASTER_GATE_PLAN_ACCEPTANCE_2026-11-06.md), Git blob `d2b166f40774521d1a1f3d4370cd634237e71a52`.
- [H-100 to Gate 2 authority checkpoint](H100_TO_GATE2_EVIDENCE_AUTHORITY_CHECKPOINT_2026-11-06.md), Git blob `75957f6d2a7f1a344db8ae48b36cfc04f8cbe10a`.

The accepted R2 plan has 40,903 bytes and SHA-256 `ae823f8f23f476fed092c0b120b8cea2e68bd8ef14053ac66eca89670cfcab4a`. These documents were inspected read-only. This index does not amend their decisions or machine governance projections.

## B0 artifact identities without payload preservation

The [original final B0 review](ACQ_EXEC_06_B0_STATIC_SOURCE_FINAL_REVIEW.md) reports the following accepted received-text identities:

```ini
EXPORT_BYTES=87753
EXPORT_SHA256=f5b780f402a66b0054dd38aa735d4b04cabb85bb067fb3a8f73095ccd947048f

SOURCE_NAME=qualification_authority.py
SOURCE_BYTES=59880
SOURCE_SHA256=d1db9f46646fcb1b1789e6f77599fe0c0d849a10689ba117a08d91611014ae91

COMPANION_NAME=source_review_packet.md
COMPANION_BYTES=26302
COMPANION_SHA256=e1d8e30d2996e172ad957774dd237a1e45ae305369d8c12f19c08989bede6f35

SOURCE_EXPORT_RANGE=[1089,60969)
COMPANION_EXPORT_RANGE=[61025,87327)
RANGE_CONVENTION=ZERO_BASED_HALF_OPEN
EXTRACTION_INCLUDES_FINAL_LF_BEFORE_CLOSING_FENCE=YES
```

These are `REVIEWED` identities from the earlier reviewer runtime. This assignment does not retrieve, extract, recreate or commit any of those three payloads. It does not establish custody in a future writer runtime. Paths and source-line links inside historical reviews remain historical references to excluded payloads.

The final accepted B0 disposition is:

```ini
B0_F01_TO_F04=CLOSED
B0_R01_TO_R03=CLOSED
B0_N01_TO_N03=CLOSED
B0_E01=RESOLVED
B0_E02=RESOLVED
B0_STATIC_SOURCE_VERDICT=ACCEPTABLE_FOR_EXACT_BYTE_FREEZE_REVIEW
B0_SOURCE_REVISION_AUTHORIZED=NO
B0_EXACT_BYTES_FROZEN=NO
```

### B0 review chronology

1. The [historical B0 draft authorization](ACQ_EXEC_06_B0_DRAFT_AUTHORIZATION.md) established the bounded source-authoring assignment. It is historical evidence, not a new grant.
2. The [full F01 through F04 review as received](ACQ_EXEC_06_B0_F01_F04_REVIEW_RECEIVED.md) records defects concerning genesis and predecessor binding, denial identities, shared external obligations and adverse-transition hints. The [F correction authorization](ACQ_EXEC_06_B0_F01_F04_CORRECTION_AUTHORIZATION.md) is preserved separately.
3. The [R01 through R03 findings as received](ACQ_EXEC_06_B0_R01_R03_FINDINGS_RECEIVED.md) and [R correction authorization](ACQ_EXEC_06_B0_R01_R03_CORRECTION_AUTHORIZATION.md) preserve the subsequent size and coverage, historical-boundary chronology and preparation-versus-execution binding issues.
4. The [N01 through N03 review as received](ACQ_EXEC_06_B0_N01_N03_REVIEW_RECEIVED.md) and [N correction authorization](ACQ_EXEC_06_B0_N01_N03_CORRECTION_AUTHORIZATION.md) preserve the seal, predecessor evidence and rerun-obligation findings.
5. The [earlier R2 boundary adjudication as received](ACQ_EXEC_06_R2_BOUNDARY_ADJUDICATION_RECEIVED.md) supplies the historical source-authoring-boundary decision relevant to B0-E02. Its R2 label predates and is distinct from B1-R2.
6. The [interim B0 evidence review](ACQ_EXEC_06_B0_EVIDENCE_INTERIM_REVIEW.md) closes N01 through N03 and resolves E02, while retaining E01 because a manual F-review transcription was insufficient primary evidence.
7. The [final B0 review](ACQ_EXEC_06_B0_STATIC_SOURCE_FINAL_REVIEW.md) resolves E01 after receipt of the full F review. It confirms the F, R and N closures and resolves E02 for the historical verdict's limited scope. Its acceptance permits consideration of a separate freeze process only.

The recovered user-supplied F, R, N and boundary texts are original received records in the identified conversations. This agent does not claim to have authenticated their earlier external authorship. The directly recovered final reviewer output records what that reviewer accepted. Both facts remain visible.

## B1 revision and review history

### R0

The [original B1-R0 packet](ACQ_EXEC_06_B1_R0_ORIGINAL.md) matches the 25,416-byte, `eb2d1597...` review target exactly. The [original R0 Master Gate review](ACQ_EXEC_06_B1_R0_MASTER_REVIEW.md) returns `CHANGES_REQUESTED` with `B1_F01=OPEN`. It identifies the incomplete B1 transition contract and retains acknowledgment transport, synchronization, launcher and volatility requirements as future grant blockers.

### R1

The [R1 correction proposal](ACQ_EXEC_06_B1_R1_CORRECTION_PROPOSAL.md), [assistant approval request](ACQ_EXEC_06_B1_R1_APPROVAL_REQUEST.md) and [actual user approval](ACQ_EXEC_06_B1_R1_HUMAN_APPROVAL.txt) precede the [original R1 packet](ACQ_EXEC_06_B1_R1_ORIGINAL.md). The packet matches the 42,557-byte, `1a8fe95e...` review target exactly.

The [received R1 pre-review](ACQ_EXEC_06_B1_R1_PRE_REVIEW_RECEIVED.md) raises an authorization-provenance concern because that reviewer had not yet seen the approval. Preserve that concern as history. The [later original R1 Master Gate review](ACQ_EXEC_06_B1_R1_MASTER_REVIEW.md) independently retrieves the original user approval and resolves `B1_AUTH01`.

That Master Gate review confirms 12 normal or review transitions and 54 adverse transitions. It still returns `CHANGES_REQUESTED`. B1-R1-N01 concerns initial planning-case establishment. B1-R1-N02 concerns overlapping terminal classifications. B1-F01 remains open at this review.

### R2

The [R2 proposal](ACQ_EXEC_06_B1_R2_CORRECTION_PROPOSAL.md), [assistant approval request](ACQ_EXEC_06_B1_R2_APPROVAL_REQUEST.md) and [actual user approval](ACQ_EXEC_06_B1_R2_HUMAN_APPROVAL.txt) precede the [original R2 packet](ACQ_EXEC_06_B1_R2_ORIGINAL.md). The packet matches the 51,162-byte, `e17af86e...` review target exactly.

The authorized R2 correction concerns only N01 and N02. The packet describes a separately authenticated initial planning-case prerequisite and disjoint completed-negative-review versus failed-review-procedure guards. Preserving that text is not a new technical adjudication.

The owner reports in the [current preservation authorization](ACQ_EXEC_06_EVIDENCE_PRESERVATION_AUTHORIZATION.md) that the Master Gate found the R2 technical corrections substantively complete:

```ini
REPORTED_DECISION_SCOPE=ACCEPTED_AT_PLANNING_LEVEL
REPORTED_B1_R1_N01=CLOSED_AT_CONTRACT_LEVEL
REPORTED_B1_R1_N02=CLOSED_AT_CONTRACT_LEVEL
REPORTED_B1_F01=CLOSED_AT_CONTRACT_LEVEL
PRIMARY_R2_TECHNICAL_MASTER_GATE_REPORT=UNAVAILABLE_OR_UNVERIFIED
```

The original R2 technical review was not recovered in this assignment. This index retains the owner's report as `REPORTED`, without promoting it to an independently authenticated primary decision. Neither that report nor verification of the R2 approval grants B1 materialization, persistence or operational acceptance.

### Human approval provenance

R1's approval message is `f158af6e-ad4d-4569-b2a6-ecdde87b9877`. The recovered backing record says `createdBy=user`, `creationSource=web`, `visibility=local`, with observed `updatedAt=2026-11-07T15:19:05.250Z`. It is position 98, after the position-96 request and before the position-170 R1 submission. The original R1 Master Gate review independently confirms this sequence.

R2's approval message is `fec42bdd-e147-4e75-ad10-c7c2c4abb397`. The recovered backing record says `createdBy=user`, `creationSource=mobile`, `visibility=local`, with observed `updatedAt=2026-11-07T18:02:19.931Z`. It is position 192, after the position-190 request and before the position-226 R2 submission. The explicit text authorizes one conversational correction limited to B1-R1-N01 and B1-R1-N02.

```ini
R1_APPROVAL_PROVENANCE=VERIFIED
R2_APPROVAL_PROVENANCE=VERIFIED
PROVENANCE_SCOPE=ORIGINAL_T3_USER_ORIGIN_RECORD_AND_BOUND_CONTEXT
INDEPENDENT_MASTER_GATE_REVIEW_OF_THIS_PRESERVATION=REQUIRED
```

These observations authenticate the original platform user-origin records available to this agent. They do not claim a separate cryptographic signature, an external identity attestation or a newly issued writing grant. The preserved assistant questions are not approvals.

## Recovery and byte-verification method

The evidence agent read the original conversation message items through T3's read-only records interface. Each inventory entry binds the full message body to its source conversation, position, item identifier and message identifier. The platform returns a text body, not a raw HTTP or JSON transcript export. The preserved bytes are that complete body's UTF-8 encoding. No metadata wrapper is presented as part of the original body.

All returned bodies were complete. The 51,162-byte R2 message required a second text range; the adjacent returned ranges were joined without inserting or deleting characters. Independent length and SHA-256 calculation matched the accepted R2 identity. The earlier volatile `/tmp/ACQ_EXEC_06_B1_R2_PLANNING_PACKET.md` export was absent when checked; its missing staging copy did not supply or reconstruct these bytes.

The agent calculated each recovered body's byte length, SHA-256, LF count, CR count, trailing-LF status and Git blob identity before preservation. It created the historical documentation files exclusively and compared their readback to the recovered body bytes. All 23 originals have zero CR bytes and no trailing LF. Their LF counts appear below. No editor normalization, trimming, dedenting or added preamble was applied.

For the three B1 packets, the independent prior review identities are supplied expectations. For the other records, this assignment establishes new recovery identities from the specified original backing objects. It does not invent a previously accepted hash. The eventual committed Git blobs must match these same recovered bytes; the PR handoff records that verification and the exact commit.

Git attributes and active filters were checked for the proposed evidence paths. Any filter or attribute that would change these bytes is a stopping condition. Whitespace findings in an unchanged historical original do not authorize editing it.

The index is newly authored and therefore has no historical original identity. Its committed blob and the PR's exact head identify the reviewed index. It does not attempt to include its own self-referential hash.

## Original-byte preservation inventory

All file links below are relative to this index. All originals are ordinary documentation files, not executable artifacts. The `git_blob` values identify their exact content and must agree with the staged and committed blobs. `observed_message_updated_at` is platform metadata, not an invented message-creation timestamp.

### 1. B1-R0 planning packet

[Preserved original](ACQ_EXEC_06_B1_R0_ORIGINAL.md)

VERIFIED original message bytes; matches the prior independent accepted length and SHA-256. Historical review disposition is CHANGES_REQUESTED.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=89
source_item_id=turn-item:provider:codex:native-item:msg_09047fd6a15fe0a8016aef3b70e2cc87d0b2eaf3a9ec15c554
source_message_id=message:provider:codex:native-item:msg_09047fd6a15fe0a8016aef3b70e2cc87d0b2eaf3a9ec15c554
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T14:55:48.197Z
encoding=UTF-8
bytes=25416
sha256=eb2d1597227814c4a29392a3843474bc0e83e1cea0255c60f5814fb73daa638e
git_blob=144585d7a950d407308e68d507e35617824a55a6
lf_bytes=392
cr_bytes=0
trailing_lf=NO
```

### 2. B1-R1 planning packet

[Preserved original](ACQ_EXEC_06_B1_R1_ORIGINAL.md)

VERIFIED original message bytes; matches the prior independent accepted length and SHA-256. Historical review disposition is CHANGES_REQUESTED.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=170
source_item_id=turn-item:provider:codex:native-item:msg_09047fd6a15fe0a8016aef436daf5487d0a8942c18d6ec920e
source_message_id=message:provider:codex:native-item:msg_09047fd6a15fe0a8016aef436daf5487d0a8942c18d6ec920e
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T15:29:40.566Z
encoding=UTF-8
bytes=42557
sha256=1a8fe95ee1b6e2b90c36d7a0fbe91243fe61f4641c90f7b48615222cd52fb57e
git_blob=415c99b827b426872dd36c8468f58350db459854
lf_bytes=648
cr_bytes=0
trailing_lf=NO
```

### 3. B1-R2 planning packet

[Preserved original](ACQ_EXEC_06_B1_R2_ORIGINAL.md)

VERIFIED original message bytes; matches the prior independent accepted length and SHA-256. The original R2 technical Master Gate report remains unavailable.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=226
source_item_id=turn-item:provider:codex:native-item:msg_09047fd6a15fe0a8016aef68f74bec87d08c985b4c88661742
source_message_id=message:provider:codex:native-item:msg_09047fd6a15fe0a8016aef68f74bec87d08c985b4c88661742
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T18:09:59.826Z
encoding=UTF-8
bytes=51162
sha256=e17af86eba90842163253dde581f1e7c0470acc8e158b4b0f726fbe09e1303ee
git_blob=63ecf479994fb2f08d53a82a2fcb99fcf6c491b6
lf_bytes=764
cr_bytes=0
trailing_lf=NO
```

### 4. B0-F01 through B0-F04 review as received

[Preserved original](ACQ_EXEC_06_B0_F01_F04_REVIEW_RECEIVED.md)

VERIFIED complete user-supplied received message. Its external reviewer authorship and first-generation export remain UNVERIFIED. This is the full text supplied to resolve B0-E01, not the rejected manual transcription.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/d659289d-0193-4653-9a11-44d940fd64ff>

```ini
source_position=130
source_item_id=turn-item:message:3142a0f9-5658-436e-b246-a41d4a33d3ef
source_message_id=3142a0f9-5658-436e-b246-a41d4a33d3ef
created_by=user
creation_source=web
visibility=local
observed_message_updated_at=2026-11-07T14:27:14.347Z
encoding=UTF-8
bytes=7480
sha256=4a4a9c04dd24fef4c19748376c5538e29bc297abc2dc5d2edf535ef6cf2e50a3
git_blob=3e64982383ab63016d191c21e32837d0f1c9e0c9
lf_bytes=105
cr_bytes=0
trailing_lf=NO
```

### 5. B0-N01 through B0-N03 review as received

[Preserved original](ACQ_EXEC_06_B0_N01_N03_REVIEW_RECEIVED.md)

VERIFIED complete user-supplied received message and matching original local text attachment. External first authorship remains REPORTED. See the additional attachment custody observation below.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/d659289d-0193-4653-9a11-44d940fd64ff>

```ini
source_position=81
source_item_id=turn-item:message:82ffdbd3-0671-44d2-b483-06de83499033
source_message_id=82ffdbd3-0671-44d2-b483-06de83499033
created_by=user
creation_source=web
visibility=local
observed_message_updated_at=2026-11-07T14:02:50.423Z
encoding=UTF-8
bytes=23029
sha256=57d163a5f5d4bac9f414acccf137c45857f94323872086562c0e95c37d4d1e9f
git_blob=ea80eb3108f051c57cbed442b8601d9615d2cf06
lf_bytes=244
cr_bytes=0
trailing_lf=NO
```

### 6. Earlier ACQ-EXEC-06 R2 boundary adjudication as received

[Preserved original](ACQ_EXEC_06_R2_BOUNDARY_ADJUDICATION_RECEIVED.md)

VERIFIED complete user-supplied received message. It concerns the earlier source-authoring boundary adjudication, not B1-R2. External reviewer authorship remains UNVERIFIED.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/d659289d-0193-4653-9a11-44d940fd64ff>

```ini
source_position=89
source_item_id=turn-item:message:e49a3459-4670-4097-8cbd-d7d5779a8fce
source_message_id=e49a3459-4670-4097-8cbd-d7d5779a8fce
created_by=user
creation_source=web
visibility=local
observed_message_updated_at=2026-11-07T14:03:23.085Z
encoding=UTF-8
bytes=25171
sha256=e4a6058af4500f08f5f8418b38a20b703888477145dec06d9f15ee8ffe70e4ad
git_blob=0e32cb2259e87ebe1533dee6dc7c6c8c6a2f5685
lf_bytes=330
cr_bytes=0
trailing_lf=NO
```

### 7. B0 interim evidence decision

[Preserved original](ACQ_EXEC_06_B0_EVIDENCE_INTERIM_REVIEW.md)

VERIFIED original reviewer output. It retains the interim B0-E01 limitation and must be read before the final closure.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/d659289d-0193-4653-9a11-44d940fd64ff>

```ini
source_position=128
source_item_id=turn-item:provider:codex:native-item:msg_082a2ea24c6670d5016aef3061e10487d08c47f01d4c4b4e91
source_message_id=message:provider:codex:native-item:msg_082a2ea24c6670d5016aef3061e10487d08c47f01d4c4b4e91
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T14:06:41.624Z
encoding=UTF-8
bytes=4829
sha256=35fff9ef86b030e71ddad3af66ea07df239bd4be58c7f19d72f7444777b3d70f
git_blob=0293121b1654678cc4b56d43e94e9f6d8ab732ff
lf_bytes=65
cr_bytes=0
trailing_lf=NO
```

### 8. B0 final static-source review

[Preserved original](ACQ_EXEC_06_B0_STATIC_SOURCE_FINAL_REVIEW.md)

VERIFIED original reviewer output. It records the accepted static-source disposition and the final finding closures with no freeze or execution grant.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/d659289d-0193-4653-9a11-44d940fd64ff>

```ini
source_position=140
source_item_id=turn-item:provider:codex:native-item:msg_082a2ea24c6670d5016aef359d232c87d087f7a035531b8f18
source_message_id=message:provider:codex:native-item:msg_082a2ea24c6670d5016aef359d232c87d087f7a035531b8f18
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T14:29:05.266Z
encoding=UTF-8
bytes=5250
sha256=16a3052dd8b9d31b72e3920a8885a73e4ce66b6f5a445dc62404ec2cf2c3a8c3
git_blob=5511cc44b57de4c46d5d53e4ba058040fe78ecc3
lf_bytes=68
cr_bytes=0
trailing_lf=NO
```

### 9. B1-R0 Master Gate review

[Preserved original](ACQ_EXEC_06_B1_R0_MASTER_REVIEW.md)

VERIFIED original reviewer output. It records CHANGES_REQUESTED and B1-F01 OPEN.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/75303d70-5165-47a4-9f6c-1164033a04e6>

```ini
source_position=83
source_item_id=turn-item:provider:codex:native-item:msg_0a9cef30a505247f016aef3fe9015c87d085912169173f90cf
source_message_id=message:provider:codex:native-item:msg_0a9cef30a505247f016aef3fe9015c87d085912169173f90cf
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T15:13:22.506Z
encoding=UTF-8
bytes=8694
sha256=c0ce3815daf7930e79aa1e616d26d0413c82a9da140c9c72941608afb7711c1c
git_blob=56319f273a88a1ac491aef265644b2571590542f
lf_bytes=84
cr_bytes=0
trailing_lf=NO
```

### 10. B1-R1 Master Gate review

[Preserved original](ACQ_EXEC_06_B1_R1_MASTER_REVIEW.md)

VERIFIED original reviewer output. It resolves B1-AUTH01 after retrieving the actual user approval, and leaves B1-R1-N01, B1-R1-N02 and B1-F01 open.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/75303d70-5165-47a4-9f6c-1164033a04e6>

```ini
source_position=121
source_item_id=turn-item:provider:codex:native-item:msg_0a9cef30a505247f016aef65899a3087d0a54a5b2f1a3c5c73
source_message_id=message:provider:codex:native-item:msg_0a9cef30a505247f016aef65899a3087d0a54a5b2f1a3c5c73
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T17:53:39.274Z
encoding=UTF-8
bytes=6633
sha256=ca3375e994123239bdb575708d76a4132defad591710ca4bdf6d5e3ea43fbe89
git_blob=b2e56b8bc642d1b1e530d3218a231fe356046140
lf_bytes=85
cr_bytes=0
trailing_lf=NO
```

### 11. B1-R1 correction proposal

[Preserved original](ACQ_EXEC_06_B1_R1_CORRECTION_PROPOSAL.md)

VERIFIED original user-origin proposal. Its proposed status alone did not issue a correction grant.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=91
source_item_id=turn-item:message:30583b4f-ad0e-4187-b8d1-58799cb02f45
source_message_id=30583b4f-ad0e-4187-b8d1-58799cb02f45
created_by=user
creation_source=web
visibility=local
observed_message_updated_at=2026-11-07T15:17:59.702Z
encoding=UTF-8
bytes=6283
sha256=68cca3cfb794edcb7b5fd0b6440d6df6b91b8d21d7ee45ef6235fa9f5646809b
git_blob=f37b49ba0cd39349644290f56e02f01350b17d5e
lf_bytes=146
cr_bytes=0
trailing_lf=NO
```

### 12. B1-R1 assistant request for approval

[Preserved original](ACQ_EXEC_06_B1_R1_APPROVAL_REQUEST.md)

VERIFIED original assistant output. This question is context for the following user approval and is not human authorization.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=96
source_item_id=turn-item:provider:codex:native-item:msg_09047fd6a15fe0a8016aef413d073487d0a9a527c383028c59
source_message_id=message:provider:codex:native-item:msg_09047fd6a15fe0a8016aef413d073487d0a9a527c383028c59
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T15:18:24.439Z
encoding=UTF-8
bytes=272
sha256=99f3c3cecd121943fc42770a1cf9f619fbc664197e5f1b1f2d6277a58e2128d8
git_blob=e795c81a2d6b2a69be605cf7bd9b5cbc3ddaab60
lf_bytes=2
cr_bytes=0
trailing_lf=NO
```

### 13. B1-R1 human approval

[Preserved original](ACQ_EXEC_06_B1_R1_HUMAN_APPROVAL.txt)

VERIFIED original user-origin approval in its proposal and request context. The approval precedes the R1 submission.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=98
source_item_id=turn-item:message:f158af6e-ad4d-4569-b2a6-ecdde87b9877
source_message_id=f158af6e-ad4d-4569-b2a6-ecdde87b9877
created_by=user
creation_source=web
visibility=local
observed_message_updated_at=2026-11-07T15:19:05.250Z
encoding=UTF-8
bytes=19
sha256=abc1eddf60e25e10e596ee21974fa00c62019bc57a46510e69688a83d336fa80
git_blob=23f7f35413783b45852cc2a9266fe534cc6f670c
lf_bytes=0
cr_bytes=0
trailing_lf=NO
```

### 14. B1-R2 correction proposal

[Preserved original](ACQ_EXEC_06_B1_R2_CORRECTION_PROPOSAL.md)

VERIFIED original user-origin proposal. It limits the correction to B1-R1-N01 and B1-R1-N02.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=189
source_item_id=turn-item:message:2c686279-a1fc-4d6e-a7d5-230578b78932
source_message_id=2c686279-a1fc-4d6e-a7d5-230578b78932
created_by=user
creation_source=mobile
visibility=local
observed_message_updated_at=2026-11-07T17:56:42.597Z
encoding=UTF-8
bytes=4297
sha256=7b666e5cc1238334227b4864c23177b91a5c4f1e90ad34f3168ca677d1c9653c
git_blob=87bb99893e1133ef3ef79458586d27a71b1e3dc2
lf_bytes=96
cr_bytes=0
trailing_lf=NO
```

### 15. B1-R2 assistant request for approval

[Preserved original](ACQ_EXEC_06_B1_R2_APPROVAL_REQUEST.md)

VERIFIED original assistant output. The question supplies context, not authority.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=190
source_item_id=turn-item:provider:codex:native-item:msg_09047fd6a15fe0a8016aef6669d96887d0ab230d073080727a
source_message_id=message:provider:codex:native-item:msg_09047fd6a15fe0a8016aef6669d96887d0ab230d073080727a
created_by=agent
creation_source=provider
visibility=local
observed_message_updated_at=2026-11-07T17:57:59.636Z
encoding=UTF-8
bytes=272
sha256=44df8d26841028acd4bd0f52e8bb68be8ded69e9c7babc446538b9ac284d69d0
git_blob=616369805c703d7b53b160f38a0f07246191c40d
lf_bytes=2
cr_bytes=0
trailing_lf=NO
```

### 16. B1-R2 human approval

[Preserved original](ACQ_EXEC_06_B1_R2_HUMAN_APPROVAL.txt)

VERIFIED original user-origin explicit approval for one conversational correction limited to B1-R1-N01 and B1-R1-N02. This is a separate message, not an assistant-authored approval template.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=192
source_item_id=turn-item:message:fec42bdd-e147-4e75-ad10-c7c2c4abb397
source_message_id=fec42bdd-e147-4e75-ad10-c7c2c4abb397
created_by=user
creation_source=mobile
visibility=local
observed_message_updated_at=2026-11-07T18:02:19.931Z
encoding=UTF-8
bytes=188
sha256=b78406a9052b3445b29c55efeae61bd03cf2dbbc3b907178720bbac7b5568d4a
git_blob=7af553bbdb9de703b3dea7f5511a7415c306d133
lf_bytes=1
cr_bytes=0
trailing_lf=NO
```

### 17. Evidence-preservation assignment and approval

[Preserved original](ACQ_EXEC_06_EVIDENCE_PRESERVATION_AUTHORIZATION.md)

VERIFIED original user-origin authorization for this documentation-only branch, commit, push and single draft PR. It also supplies the REPORTED R2 contract-level closure claim, not the missing primary review.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=245
source_item_id=turn-item:message:07af470f-c4bc-4269-b503-4e2e177cf861
source_message_id=07af470f-c4bc-4269-b503-4e2e177cf861
created_by=user
creation_source=web
visibility=local
observed_message_updated_at=2026-11-08T05:24:31.666Z
encoding=UTF-8
bytes=13491
sha256=b82582ba31f4e7739abbeac7bfe56dbdf03ff4fd7381c1cae1e9362491b0c8e1
git_blob=9b45ade363c35816c094dcaf1069915c0ddd8481
lf_bytes=403
cr_bytes=0
trailing_lf=NO
```

### 18. Historical B0 draft authorization

[Preserved original](ACQ_EXEC_06_B0_DRAFT_AUTHORIZATION.md)

VERIFIED original user-origin historical instructions. Preserving them does not renew the consumed source-authoring grant.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/74328534-c2fc-4b97-b21f-2132979cb3aa>

```ini
source_position=253
source_item_id=turn-item:message:068e7c5a-1672-4645-b68d-2d08ca1bce51
source_message_id=068e7c5a-1672-4645-b68d-2d08ca1bce51
created_by=user
creation_source=mobile
visibility=local
observed_message_updated_at=2026-11-06T13:19:23.723Z
encoding=UTF-8
bytes=7405
sha256=bd4835f318ccae03c89e29db1e7fdff78cced4e615da4510aa9748662ad38b59
git_blob=7bcac52e873ff1f15f4814193106de09a3287485
lf_bytes=166
cr_bytes=0
trailing_lf=NO
```

### 19. Historical B0-F01 through B0-F04 correction authorization

[Preserved original](ACQ_EXEC_06_B0_F01_F04_CORRECTION_AUTHORIZATION.md)

VERIFIED original user-origin historical instructions. No source revision is authorized by this preservation task.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/74328534-c2fc-4b97-b21f-2132979cb3aa>

```ini
source_position=301
source_item_id=turn-item:message:cc1724a8-ea4f-46ad-9d8e-ee5b4bb09937
source_message_id=cc1724a8-ea4f-46ad-9d8e-ee5b4bb09937
created_by=user
creation_source=mobile
visibility=local
observed_message_updated_at=2026-11-06T16:08:27.048Z
encoding=UTF-8
bytes=1973
sha256=7bdf5284eaca68e34e31ea62d961ebe176378b0ebdce3a6fb4c19ba7fca2b873
git_blob=de5b365f01cd3c559c93170116e674b004533f52
lf_bytes=37
cr_bytes=0
trailing_lf=NO
```

### 20. Historical B0-R01 through B0-R03 correction authorization

[Preserved original](ACQ_EXEC_06_B0_R01_R03_CORRECTION_AUTHORIZATION.md)

VERIFIED original user-origin historical instructions, retained with the received R findings and later closure.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/74328534-c2fc-4b97-b21f-2132979cb3aa>

```ini
source_position=333
source_item_id=turn-item:message:addad0b0-efd9-4647-b4c1-ca77517a23a3
source_message_id=addad0b0-efd9-4647-b4c1-ca77517a23a3
created_by=user
creation_source=mobile
visibility=local
observed_message_updated_at=2026-11-06T18:33:14.730Z
encoding=UTF-8
bytes=3344
sha256=d6c141d8d88c78f9448cbfef6c616083a0f3901fc4bff3808ab31d817e0a4916
git_blob=6f42e4fdbb08a25a1a08be3926bf7971a77b7a2e
lf_bytes=87
cr_bytes=0
trailing_lf=NO
```

### 21. Historical B0-N01 through B0-N03 correction authorization

[Preserved original](ACQ_EXEC_06_B0_N01_N03_CORRECTION_AUTHORIZATION.md)

VERIFIED original user-origin historical instructions, retained with the received N findings and later closure.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/74328534-c2fc-4b97-b21f-2132979cb3aa>

```ini
source_position=349
source_item_id=turn-item:message:f5d4d70b-4a70-48b4-a0f7-4f0e6679e2cb
source_message_id=f5d4d70b-4a70-48b4-a0f7-4f0e6679e2cb
created_by=user
creation_source=web
visibility=local
observed_message_updated_at=2026-11-07T04:08:12.581Z
encoding=UTF-8
bytes=4305
sha256=3043897c8b8be28002b4ea13b5062148ddd95c4096d2fa5ff72e0a6e9c71fec9
git_blob=f3578ff784ba694a883c1f179472640868ddfaf7
lf_bytes=101
cr_bytes=0
trailing_lf=NO
```

### 22. B0-R01 through B0-R03 findings as received

[Preserved original](ACQ_EXEC_06_B0_R01_R03_FINDINGS_RECEIVED.md)

VERIFIED original user-supplied received findings. External first reviewer authorship remains REPORTED.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/74328534-c2fc-4b97-b21f-2132979cb3aa>

```ini
source_position=329
source_item_id=turn-item:message:beb696d1-cd72-4a8f-8354-236bd6fb136e
source_message_id=beb696d1-cd72-4a8f-8354-236bd6fb136e
created_by=user
creation_source=web
visibility=local
observed_message_updated_at=2026-11-06T17:53:31.389Z
encoding=UTF-8
bytes=5176
sha256=3efaf99632445912a5ed7d09fcdcff94063ce9633ebae7f992968b4aa33fb335
git_blob=cda259fd8a5eec19d756e9f719d8db333aede521
lf_bytes=117
cr_bytes=0
trailing_lf=NO
```

### 23. B1-R1 pre-review as received

[Preserved original](ACQ_EXEC_06_B1_R1_PRE_REVIEW_RECEIVED.md)

VERIFIED complete user-supplied pre-review message. Its initial authorization concern is historical; the later original R1 Master Gate review resolves B1-AUTH01.

Original source conversation: <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

```ini
source_position=172
source_item_id=turn-item:message:8f368ffe-5293-4ce8-a2da-c3cd9f970fa9
source_message_id=8f368ffe-5293-4ce8-a2da-c3cd9f970fa9
created_by=user
creation_source=mobile
visibility=local
observed_message_updated_at=2026-11-07T17:36:02.543Z
encoding=UTF-8
bytes=6162
sha256=884bedd88b21060ef85f8ddfdab1c61156c218eee0743bd634e1e08e4ae2051b
git_blob=300a09021f64be60a99b1e05b022fa723541859f
lf_bytes=99
cr_bytes=0
trailing_lf=NO
```

### Additional attachment custody observation

The original N01 through N03 text attachment was accessible at:

```text
/home/jcschoeman96/.t3/userdata/attachments/d659289d-0193-4653-9a11-44d940fd64ff-5b331271-d813-4b01-8f58-2885b24243b9-txt.txt
```

Its measured length is 23,029 bytes and its SHA-256 is `57d163a5f5d4bac9f414acccf137c45857f94323872086562c0e95c37d4d1e9f`, equal to the received-message identity above. This path is a custody observation in this runtime, not a promise that another agent or machine can access it. The Git documentation copy provides the portable preserved record.

## Missing-evidence and qualification register

### M01. Original R2 technical Master Gate review

- Status is `UNAVAILABLE_OR_UNVERIFIED`.
- Known reference is the owner's report in [the preservation authorization](ACQ_EXEC_06_EVIDENCE_PRESERVATION_AUTHORIZATION.md), which supplies the contract-level N01, N02 and F01 closures.
- The inspected B1 reviewer conversation contains the original R0 and R1 decisions. Searches for R2 and the reported closure strings did not recover an original R2 technical decision. No exact message identifier, byte identity or source export for that decision is invented.
- Consequence is that this PR preserves the reported decision and its qualification, rather than claiming recovery of the primary R2 acceptance.
- Smallest future recovery action is for the owner to identify the original reviewer conversation/message or provide its original export. A separately authorized documentation update can authenticate that object, calculate its exact identity and preserve it. Re-running a review is not recovery of the historical decision.

### M02. Earlier external review authorship

- Status is `VERIFIED` for the received F, R, N and earlier boundary-adjudication bytes, and `REPORTED` or `UNVERIFIED` for their first external authorship.
- The inventory supplies exact user-origin backing records, and the N review also has a matching text attachment. The original external reviewer conversation exports were not independently authenticated here.
- Consequence is that the index must not relabel these relay records as independently recovered external originals. The original final B0 review remains directly recoverable and records the reviewer's closure decisions.
- Smallest future recovery action, if first-generation authorship is required, is to identify and authenticate each external review's original backing record or original export. Keep received copies and historical dispositions unchanged.

### M03. Historical embedded links

- Status is `REPORTED` for historical local-path and attachment references that occur inside preserved originals.
- Some links point to excluded B0 payloads or another runtime. Their portability is not established by this PR. Exact preservation requires retaining those original link strings.
- Consequence is that the index's relative links, source item references and Git blob identities are the navigation and custody record for the documentation actually preserved.
- Smallest future action is a separately authorized custody and retrieval process for any additional required object. This assignment does not copy source payloads to make old links resolve.

### M04. B0 payload custody and durable preservation

- Status is `NOT_YET_ESTABLISHED` in a future B1 writer runtime and `NOT_AUTHORIZED` for materialization under this assignment.
- The prior reviewed export, source and companion identities are preserved as references only. Their payloads are deliberately outside this documentation set.
- Consequence is that this PR cannot close B1 receiving-runtime custody, freeze or preservation prerequisites.
- Smallest future action is an exact, separately approved B1 custody and writing authorization after the outstanding grant requirements below are independently satisfied.

### M05. Independent acceptance of this preservation PR

- Status is `NOT_YET_ESTABLISHED`.
- This evidence agent's recovery measurements are review evidence. They are not a Master Gate approval of the resulting PR.
- Consequence is that no merge, historical finding reclassification or follow-on action follows from PR creation or CI success.
- Smallest future action is independent review of the exact PR head, its full diff, the inventory and the remaining qualifications.

## Outstanding B1 requirements and future handoff

The accepted or reported planning work describes requirements. This documentation does not qualify the future implementation. At minimum, the later grant bundle still needs independently established receiving-runtime custody and extraction equality, appointed principals, an exact launcher, immutable dependencies, isolation, a complete effect inventory, authenticated acknowledgment transport and durable receipt destination.

The future supervisor must specify the acknowledgment mechanism, descriptor configuration, receipt format, authentication and replay exclusions before admitting the next effect. The grant must bind exact synchronization implementations and dependencies, output and directory synchronization order, metadata checks and failure handling. Finite stopping, independent observation and confirmation of entitlement consumption must precede candidate creation.

B1 entitlement remains separate from the Gate A L06 qualification-launch entitlement. A future B1 grant may authorize at most one bounded attempt containing the two specified copy launches. This documentation issues neither entitlement and consumes neither one. No failed or uncertain candidate may be silently repaired, overwritten, rerun or promoted.

`/tmp` staging is volatile. It is not a durable archive. Disposable staging needs explicit owner acceptance of volatility and independently established recoverability of required originals and evidence. If future retrieval depends on B1 outputs, the archive and handoff design must be accepted before staging becomes their only retained copy.

A future canonical handoff must bind the governing commit and plan blob, exact B0 identities, original findings and review decisions, the exact B1 grant, resulting materialization evidence and an independent B1 verification decision. The handoff must retain explicit nonauthorization of operational use.

This index is the canonical proposed GitHub documentation reference for the recovered B0/B1 planning record. Reviewers can retrieve the preserved documentation by exact commit, path and blob identity, then compare bytes and hashes. GitHub storage of these documents does not establish the separately required durable archive for B0 payloads, B1 outputs or operational receipts.

Durable publication or archive transfer of those objects, independent retrieval verification, additional GitHub indexing and Plane recording remain separate authorization boundaries. A later authorized Plane reference should link the exact accepted index commit and Master Gate decision without copying secrets or implying operational acceptance. This assignment performs no Plane mutation and does not modify governing roadmaps or projections.

## Authority disposition

```ini
TASK=ACQ_EXEC_06_EVIDENCE_PRESERVATION_R0
DOCUMENTATION_SCOPE=ORIGINAL_RECORDS_AND_NEW_INDEX_ONLY
B0_REVIEW_EVIDENCE=PARTIAL
B1_R0_R1_R2_PACKET_BYTES=VERIFIED
R2_APPROVAL_PROVENANCE=VERIFIED
R2_TECHNICAL_MASTER_REVIEW_ORIGINAL=UNAVAILABLE_OR_UNVERIFIED
R2_CONTRACT_LEVEL_CLOSURES=REPORTED
INDEPENDENT_MASTER_GATE_REVIEW_OF_PR=REQUIRED

B0_SOURCE_REVISION_AUTHORIZED=NO
B0_EXACT_BYTES_FROZEN=NO
B1_MATERIALIZATION_GRANT=NOT_ISSUED
B1_PERSISTENCE=NOT_AUTHORIZED
DURABLE_ARCHIVE=NOT_ESTABLISHED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
GATE_B_EXECUTION=NOT_AUTHORIZED
H100_ACCEPTANCE=NOT_ACHIEVED
AUTH_07=SUSPENDED_UNCONSUMED
MERGE=NOT_AUTHORIZED_BY_THIS_ASSIGNMENT
PLANE_MUTATION=NONE
```

The PR handoff supplies the selected base and exact head commit/tree, changed-file list, blob verification results and the CI states actually observed. No automatic correction, merge or subsequent operational work is authorized.
