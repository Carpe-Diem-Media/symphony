This is the complete B1-R2 conversational planning packet. Its normative corrections are limited to B1-R1-N01 and B1-R1-N02. R0, R1 and the accepted B0 artifacts remain unchanged.

1. Authority and revision identity

   ```ini
   TASK=ACQ_EXEC_06_B1_R2_PLANNING_CORRECTION
   PREDECESSOR=B1-R1
   PREDECESSOR_BYTES=42557
   PREDECESSOR_SHA256=1a8fe95ee1b6e2b90c36d7a0fbe91243fe61f4641c90f7b48615222cd52fb57e
   PREDECESSOR_MASTER_VERDICT=CHANGES_REQUESTED
   B1_AUTH01=RESOLVED
   CORRECTION_SCOPE=B1_R1_N01_AND_B1_R1_N02_ONLY
   AUTHORIZED_SUBMISSIONS=1
   ```

   The predecessor identity and Master disposition are accepted inputs supplied with the R2 instruction. This turn did not independently measure the predecessor attachment.

   The project owner's explicit R2 approval states:

   > APPROVED — CONTINUE.  
   > I explicitly authorize ACQ_EXEC_06_B1_R2_PLANNING_CORRECTION for one complete conversational planning packet, strictly limited to correcting B1-R1-N01 and B1-R1-N02.

   Read-only retrieval established these approval-message references:

   ```ini
   APPROVAL_MESSAGE_ID=fec42bdd-e147-4e75-ad10-c7c2c4abb397
   APPROVAL_POSITION=192
   APPROVAL_CREATED_BY=user
   APPROVAL_CREATION_SOURCE=mobile
   APPROVAL_VISIBILITY=local
   APPROVAL_RECORD_UPDATED_AT=2026-11-07T18:02:19.931Z
   SCOPE_PROPOSAL_MESSAGE_ID=2c686279-a1fc-4d6e-a7d5-230578b78932
   SCOPE_PROPOSAL_POSITION=189
   ```

   The original approval and scope proposal are in:

   <t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/8aaf2d81-9dee-4937-a31b-700d50f26043>

   That approval permits this one conversational revision. It does not authorize external case-registration writes, materialization, qualification, archives, publication or operational use.

   The governing baseline remains:

   ```ini
   REPOSITORY=JCSchoeman96/symphony
   BASE_MAIN_SHA=4971ddde384ef54b06498db438d2bfe36a0f108a
   BASE_MAIN_TREE=540617e1c62af1550059113c5166bea315cc6015
   ACQ_EXEC_05_R2_PLAN_BLOB=1fd0af3e23287bab8939876589abc064c5655b45
   ```

   R1 recorded read-only verification of those local Git objects. This revision does not claim a fresh remote protected-main or CI certification.

   Preserve the accepted B0 entry:

   ```ini
   B0_STATIC_SOURCE_VERDICT=ACCEPTABLE_FOR_EXACT_BYTE_FREEZE_REVIEW
   B0_F01_TO_F04=CLOSED
   B0_R01_TO_R03=CLOSED
   B0_N01_TO_N03=CLOSED
   B0_E01=RESOLVED
   B0_E02=RESOLVED
   B0_SOURCE_REVISION_AUTHORIZED=NO
   ```

   Original review and finding records remain required evidence. Their accepted dispositions do not authorize editing the reviewed source.

   This packet describes a proposed lifecycle contract. It does not claim that external initialization or any B1 lifecycle transition was executed during its authoring.

2. Input custody and extraction equality

   Preserve these exact review targets:

   ```ini
   EXPORT_BYTES=87753
   EXPORT_SHA256=f5b780f402a66b0054dd38aa735d4b04cabb85bb067fb3a8f73095ccd947048f

   SOURCE_NAME=qualification_authority.py
   SOURCE_BYTES=59880
   SOURCE_SHA256=d1db9f46646fcb1b1789e6f77599fe0c0d849a10689ba117a08d91611014ae91

   COMPANION_NAME=source_review_packet.md
   COMPANION_BYTES=26302
   COMPANION_SHA256=e1d8e30d2996e172ad957774dd237a1e45ae305369d8c12f19c08989bede6f35

   REPORTED_SOURCE_EXPORT_RANGE=[1089,60969)
   REPORTED_COMPANION_EXPORT_RANGE=[61025,87327)
   RANGE_CONVENTION=ZERO_BASED_HALF_OPEN
   ```

   The ranges have the specified lengths. They are observations from the independent reviewer's runtime. They establish no attachment access, backing-object identity or custody in a future writer runtime.

   Before candidate creation, an authorized custodian must deliver the original raw export and both exact payload attachments into the actual receiving runtime. The custody record must identify their origin, attachment references, custodian, transfer mechanism, receiving runtime and backing objects.

   Rendered text, copied Markdown and reconstructed files are insufficient. Ingress caches, download files and transport logs require explicit effect allowances. None is implicitly included in candidate creation.

   A separate reviewer must independently:

   - Establish all three received lengths and SHA-256 hashes.
   - Authenticate their relationship to the reviewed B0 submission.
   - Confirm the reported ranges against the received export.
   - Compare the complete source and companion slices with their respective attachments.
   - Verify inclusion of the final LF immediately before each closing fence.
   - Record the attachment, backing-object and extraction evidence.

   The expected final LF positions are export offsets `60968` and `87326`. Their actual byte values must be independently checked in the receiving runtime.

   No trimming, newline conversion, dedentation, Unicode normalization or editor save is permitted.

   The reviewer must issue an authenticated input-custody acceptance before materialization. The accepted input objects must remain protected against modification and substitution. The writer receives read-only descriptors for those same objects at offset zero.

   If the separate payload attachments do not exist, extracting and creating them requires its own exact authorization. This packet authorizes no such creation.

3. Destination, ownership and allowed effects

   Retain this proposed staging destination:

   ```text
   /tmp/symphony-gate-a-authority-candidate-r1/
   ```

   Its only proposed children are:

   ```text
   qualification_authority.py
   source_review_packet.md
   ```

   R1 recorded these read-only observations:

   ```ini
   ROOT_UID=0
   ROOT_GID=0
   ROOT_MODE=0755
   ROOT_DEVICE=66306
   ROOT_INODE=2

   TMP_UID=0
   TMP_GID=0
   TMP_MODE=1777
   TMP_DEVICE=47
   TMP_INODE=1
   TMP_FILESYSTEM=tmpfs
   TMP_MOUNT_OPTIONS=rw,noatime,inode64

   PROPOSED_CANDIDATE_DIRECTORY=ABSENT_AT_R1_INSPECTION
   OBSERVED_UID=1000
   OBSERVED_GID=1000
   ```

   These historical observations do not satisfy future fresh guards.

   Propose owner UID `1000`, GID `1000`. The directory would begin at `0700` and finish at `0500`. Each payload would be created at `0400`, without executable bits. The later grant must explicitly approve those selections.

   The independent observer must freshly verify the host, boot, user namespace, mount namespace, parent-directory identities, mount identity, ownership, permissions, ACLs and relevant security metadata. Parent components must not resolve through unexpected symlinks.

   The supervisor must hold the verified parent open and use descriptor-relative operations. Any existing candidate entry, including a dangling symlink, rejects creation. There is no automatic reuse, alternate suffix, adoption or overwrite.

   The proposed filesystem allowance is limited to:

   - Creating the candidate directory.
   - Creating its two named payload files.
   - Updating `/tmp` through that directory entry and associated metadata.
   - Updating the new directory through its two entries, associated metadata and final mode change.
   - Writing the two new files and their associated metadata.

   It permits no other files, directories, temporary objects, logs, caches, manifests, scripts, fixtures, lockfiles, core files, renames, hardlinks or repository changes.

   The declared processes, buffers, descriptors and observation channels must also appear in the complete effect inventory. Persisted transition records, diagnostics and acknowledgments require separately identified destinations and write authority.

   Inputs and dependencies must be exposed so reading them does not cause undeclared metadata writes. Isolation setup, ingress and evidence-service effects require their own complete allowances.

   Modes alone do not exclude another process with the same UID or a privileged process. Continuous exclusion of unauthorized writers and substitution must be independently established through the selected isolation mechanism.

   Resulting identities must include host and namespace context, mount identity, device, inode, file type, link count, numeric ownership, permissions, size and relevant timestamps. A pathname or inode alone is insufficient.

4. Future writer, acknowledgments and synchronization

   No launcher or supervision mechanism has been selected and independently accepted. Describing this contract does not qualify one.

   R1 recorded the copying utility:

   ```ini
   UTILITY=uutils_coreutils
   VERSION=0.10.0
   ENTRY=/usr/bin/dd
   RESOLVED_ENTRY=/usr/lib/cargo/bin/coreutils/dd
   EXECUTABLE_BYTES=11807104
   EXECUTABLE_SHA256=f84e76ea4da1e0c4e92254bd0d7dccdabe2c8b3098e734f27997dae3ee5d8e02
   EXECUTABLE_UID=0
   EXECUTABLE_GID=0
   EXECUTABLE_MODE=0755
   ```

   The installed hashing, size and metadata applets were observed to resolve to that uutils executable identity. R1 also recorded:

   ```ini
   CMP=/usr/bin/cmp
   CMP_BYTES=43592
   CMP_SHA256=82b923f0f12706950d696fb63fe3d8d8a4d2e559ec2a8a44f6c97ed2c56de44e
   ```

   These observations do not establish an immutable dependency closure. The later grant must bind the supervisor, utilities, loader, libraries, runtime data, kernel and isolation implementations, including resolved paths, bytes, hashes and immutable backing identities.

   Preserve the proposed limits:

   ```ini
   WRITER_UID=1000
   WRITER_GID=1000
   UMASK=0077
   INITIAL_WORKING_DIRECTORY=/tmp
   COPY_WORKING_DIRECTORY=/tmp/symphony-gate-a-authority-candidate-r1
   ENVIRONMENT=LC_ALL=C;LANG=C;TZ=UTC
   INHERIT_OTHER_ENVIRONMENT=NO
   CORE_DUMPS=DISABLED
   WRITER_NETWORK=DENIED
   ACTIVE_COPY_PROCESSES_MAX=1
   COPY_LAUNCHES_MAX=2
   MATERIALIZATION_WALL_TIME_LIMIT_SECONDS=30
   COPY_MEMORY_LIMIT_MIB=128
   OUTPUT_FILE_SIZE_LIMIT_BYTES=65536
   PROPOSED_STOP_CONFIRMATION_LIMIT_SECONDS=5
   ```

   The later grant must approve and implement these limits, define their clock boundaries and bind the exact stopping actions. Missing stop confirmation within the approved bound requires `UNCERTAIN`. It permits no broader process killing, cleanup or repair.

   The supervisor needs controlled access to the accepted inputs, held parent and candidate directories, current output, evidence destination, acknowledgment ingress and identified child. Its complete descriptor configuration remains unresolved.

   The later grant must specify:

   - The acknowledgment transport and receiving interface.
   - Every descriptor's number, direction, inheritance and close-on-exec behavior.
   - The independently authenticated receipt format and verification implementation.
   - Binding to the exact grant, attempt, transition, previous state and effect checkpoint.
   - Freshness and replay exclusions.
   - Finite acknowledgment deadlines.
   - The durable evidence destination and receipt of durable acceptance.

   Sending a record or acknowledgment does not prove that the supervisor received and validated it. No next effect is allowed without that validation. No transport, descriptor number, signature scheme or receipt protocol is selected here.

   Each copy child would inherit only:

   - FD `0`, its accepted input at offset zero.
   - FD `1`, its exclusively created output.
   - FD `2`, the approved diagnostic channel.

   Other inherited descriptors must be closed. Runtime dependency reads remain limited to the approved immutable closure.

   The bounded materialization procedure remains:

   1. Confirm independently acknowledged B1 entitlement consumption and acknowledged entry into `WRITING`.
   2. Revalidate current authority, custody, isolation, identities and observation readiness.
   3. Create the candidate with `mkdirat` relative to the held parent, mode `0700`, without recursive creation. Open it with directory and no-follow requirements. Independently confirm its identity, ownership and permissions.
   4. Create `qualification_authority.py` relative to the held candidate directory using `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`, mode `0400`. Check its initial descriptor identity, ownership, type and link count.
   5. Launch exactly once:

      ```text
      /usr/lib/cargo/bin/coreutils/dd bs=65536 status=none
      ```

      Its input is the accepted source descriptor. Its output is the new source file descriptor. No pathname operands or conversions apply.

   6. Observe child termination and exit status zero. Confirm no child or unauthorized writable alias remains. The supervisor checks the output descriptor and expected length `59880`, synchronizes the output, checks metadata again and closes its writable descriptor.
   7. Obtain independent acknowledgment of the completed source checkpoint before creating the companion.
   8. Create `source_review_packet.md` with the same exclusive flags and mode. Launch the identical command exactly once with the accepted companion descriptor.
   9. Observe termination and exit status zero. The supervisor checks length `26302`, synchronizes that output, checks metadata again and closes its writable descriptor.
   10. Obtain independent acknowledgment of the completed companion checkpoint.
   11. Change only the new candidate directory to mode `0500` through its held descriptor. Verify its identity and final metadata.
   12. Synchronize the candidate directory after both file synchronizations and the mode change. Then synchronize the parent directory containing the new candidate entry.
   13. Recheck directory entries against held identities, ownership, permissions, sizes, link counts and custody observations. Confirm writer termination and closure of writable access.
   14. Obtain independent acknowledgment of the complete producer evidence before requesting `PRODUCER_COMPLETE`.

   The proposed synchronization semantics are successful `fsync` operations on each completed output, then the candidate directory, then its parent. The supervisor owns those operations. A successful copy exit does not substitute for them.

   The later grant must bind exact syscall or utility implementations, dependencies, error interpretation and close behavior. No such operations were executed here.

   Any synchronization error, failed metadata check, abnormal exit, observation gap or close ambiguity stops the sequence. No synchronization retry, repeated copy launch or metadata repair follows automatically.

   The two files do not form an atomic transaction. A partial file, one complete file or an empty directory may remain after failure. Retained objects receive no automatic cleanup or promotion.

5. Independent B1 verification

   A separately appointed reviewer must obtain the accepted inputs and custody evidence independently of the producer's report. Writer access must have ended, and custody must remain intact.

   Proposed read-only commands, with the independently identified candidate directory as working directory, include:

   ```text
   /usr/bin/wc --bytes -- qualification_authority.py source_review_packet.md

   /usr/bin/sha256sum --binary -- qualification_authority.py source_review_packet.md

   /usr/bin/stat --format='%n|%F|%d|%i|%h|%u|%g|%a|%s|%y|%z' -- . qualification_authority.py source_review_packet.md

   /usr/bin/cmp -- /proc/self/fd/3 qualification_authority.py

   /usr/bin/cmp -- /proc/self/fd/4 source_review_packet.md

   /usr/bin/cmp --bytes=59880 --ignore-initial=1089:0 -- /proc/self/fd/5 qualification_authority.py

   /usr/bin/cmp --bytes=26302 --ignore-initial=61025:0 -- /proc/self/fd/5 source_review_packet.md
   ```

   Reviewer FDs `3`, `4` and `5` would refer to independently accepted source, companion and export objects. Those descriptor references do not authorize arbitrary symlink traversal.

   The entire export must first match its accepted length and hash. Entire candidate lengths must also match, because bounded comparisons alone do not reject trailing bytes.

   The reviewer must independently establish:

   - Both exact lengths and SHA-256 hashes.
   - Whole-file equality with the accepted attachments.
   - Equality with the verified export slices and final LF boundaries.
   - Regular-file type, link count one, approved UID/GID and mode `0400`.
   - Candidate ownership and final mode `0500`.
   - Agreement between descriptors and directory entries.
   - The required synchronization sequence and observed results.
   - Complete entitlement, launch-count, authority and acknowledgment evidence.
   - Continuous custody and compliance with the complete effect allowance.

   The verifier implementation and dependencies require approval. The reviewer must disclose observation limitations.

   Producer completion, producer hashes and exit status zero cannot issue independent acceptance. A separate authenticated B1 decision must identify the exact grant, attempt, objects and evidence.

6. Durability, recoverability and future indexing

   `/tmp` staging is volatile. It is not the durable archive. Successful synchronization on the observed `tmpfs` does not establish reboot or power-loss survival.

   Disposable staging may be authorized only after:

   - The project owner explicitly accepts its volatility.
   - A separate reviewer independently establishes recoverability of every required original and evidence record.
   - The grant identifies retention owners and the evidence supporting that recovery claim.

   If future retrieval depends on B1 outputs, the archive and handoff design must be accepted before staging becomes their only retained copy. Required originals or evidence must not be discarded on the strength of staging-file existence.

   Restoring identical content later would not recreate the original staging inode or continue its attempt. New materialization requires new authority.

   Preserve the proposed future index location:

   ```text
   docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_EVIDENCE_INDEX.md
   ```

   The future index must bind:

   - Governing commit, tree and plan blob.
   - Original B0 export, payload identities and extraction ranges.
   - Original independent B0 review, finding and closure records.
   - Exact received planning-packet identities and independent decisions, including R2.
   - Human B1 grant, attempt identity and entitlement-consumption evidence.
   - Input custody, immutable dependencies, supervision and complete effects.
   - Resulting file identities, synchronization observations and evidence.
   - Independent B1 verification decision and adverse annotations.
   - Accepted archive and handoff design, retained object versions and recovery evidence.
   - Explicit nonauthorization of operational use.

   Durable publication, archive transfer, independent retrieval verification, GitHub indexing and Plane recording remain separate authorization boundaries.

   Recommend commit-pinned GitHub references and a narrowly scoped future ledger link. Existing Plane SGOV-2 remains the previously identified evidence owner:

   ```ini
   PLANE_WORKSPACE=symphony-development
   PLANE_PROJECT=f7317505-bc78-42ae-a902-1e3f0346bcff
   PLANE_WORK_ITEM=079ea0ea-dc3f-4a23-ac01-0a3e75e8c03b
   ```

   Any future mapping must be verified. This submission authorizes no new issue, comment, attachment, state change, index, PR or publication.

7. Complete B1 lifecycle contract

   Retain the twelve normal or review transitions and fifty-four adverse transitions. The external prerequisite below adds no transition.

   This contract governs a B1 planning case and its prospective materialization attempt. It does not replace, invoke or consume the Gate A L00–L22 lifecycle.

   The B1 materialization entitlement has its own kind, grant identity, attempt identity and consumption record. It is entirely separate from the Gate A L06 qualification-launch entitlement. Neither can substitute for, consume or restore the other.

   The retained roles are:

   - `H`, project owner and human grant authority.
   - `P`, authorized planner.
   - `M`, independent Master Gate planning reviewer.
   - `S`, future trusted supervisor.
   - `W`, bounded copy process.
   - `V`, independent B1 result verifier.
   - `C`, independent custody, state-record and acknowledgment verification owner.

   Actual principals, authentication and permitted role combinations remain unresolved. `W` cannot decide acceptance, authenticate its own entitlement consumption or act as independent verifier.

   The retained nonterminal states are:

   ```ini
   P0=PLANNING_AUTHORIZED
   P1=SUBMITTED_IDENTITY_PENDING
   P2=PLAN_REVIEW
   P3=PLAN_ACCEPTED_BLOCKED
   O0=GRANT_ISSUED
   O1=ENTITLEMENT_CONFIRMED
   O2=WRITING
   O3=PRODUCER_COMPLETE
   O4=INDEPENDENT_REVIEW
   ```

   States `P0`–`P3` are planning states. They confer no candidate creation or copy entitlement. No operational attempt exists before an exact human grant establishes `O0`.

   The retained terminal states are:

   ```text
   PLAN_CHANGES_REQUESTED
   PLAN_REJECTED
   STAGING_VERIFIED
   B1_REVIEW_REJECTED
   REVOKED
   EXPIRED
   AUTHORITY_INVALID
   FAILED
   INCOMPLETE
   UNCERTAIN
   ```

   Every terminal is absorbing, with no outgoing transition or self-transition. A planning terminal does not imply materialization or consumption of an operational entitlement.

   **External establishment is a mandatory prerequisite for P0.**

   Before any case may be asserted at `P0`, an independently established external initialization must satisfy all requirements below. This is a normative prerequisite outside the twelve-transition relation. It is not a thirteenth transition, a selected registry implementation or authority to create records now.

   `H` initiates establishment of the new planning case under the exact human planning authorization. `C` independently verifies the authorization, predecessor disposition, uniqueness evidence and initial record. `P` cannot establish P0 by declaring it in a packet.

   The external establishment must select and record:

   - An exact authoritative planning-case namespace scoped to `JCSchoeman96/symphony` and ACQ-EXEC-06 B1 planning.
   - A fresh unique case identity within that namespace.
   - The exact human planning authorization, its authenticated principal, content binding, scope and one-submission limit.
   - The authorized output revision and correction scope.
   - The immutable identity of the terminal predecessor review case.
   - Its exact terminal decision record and `CHANGES_REQUESTED` disposition.
   - The predecessor artifact identity of `42557` bytes and SHA-256 `1a8fe95ee1b6e2b90c36d7a0fbe91243fe61f4641c90f7b48615222cd52fb57e`.
   - The governing commit, tree and accepted plan blob.
   - The responsible initiation actor and independent verification owner.

   For R2, the human authorization reference must bind the approval and scope-proposal messages identified in §1. The predecessor case and terminal-decision identities must be independently recovered. The predecessor artifact hash alone cannot substitute for them.

   The namespace and case identity must not duplicate, reuse or conflict with an existing identity or alias. The exact planning authorization must not already be bound to a different planning case.

   Before confirming initialization, `C` must independently establish either authoritative absence followed by unique registration, or authoritative evidence of exactly one registration for this same new case. An absence observation alone is insufficient. A conflicting, reused or duplicate registration blocks P0. No automatic selection of another identity or registration retry is permitted.

   The external initialization must produce an initial durable state record with:

   - Its own immutable record identity and exact content binding.
   - The namespace, fresh case identity and all evidence references above.
   - Initial state `P0`.
   - The verified uniqueness result.
   - The initiation and independent verification principals.
   - Explicit absence of a B1 materialization grant or consumed B1 entitlement.
   - The approved durable evidence destination and custody.

   The new packet's final received-byte identity is acquired through B1-T02. Initialization must bind the authorized revision and scope without inventing that later output identity.

   Before P0 is usable, `P` must receive and validate an independently authenticated acknowledgment bound to the exact initial record, namespace, case identity, human authorization and predecessor decision. The applicable acknowledgment mechanism must also establish durable acceptance of that initial record.

   Every later actor must validate this initial record and acknowledgment as part of the case's evidence chain. A revision label such as `B1-R2`, an authoring approval alone, or an unacknowledged initialization request cannot satisfy the guard.

   Failure, conflict or uncertainty in external establishment denies entry into P0. No B1 transition may be invoked against an assumed initial case. Any authorized external observations must be retained without creating a fictional P0 or reopening a predecessor. A late initial acknowledgment cannot automatically restore eligibility after failed or uncertain establishment.

   R0 and R1 retain their terminal review cases and dispositions. R2 may reference their findings as correction inputs only. It must not reuse their case identities, reopen either case, or treat R2 authoring or review as continued operation of the same terminal case.

   This packet allocates no namespace or case identity, creates no external record and claims no successful initialization.

   **Every transition inherits the common contract.**

   Before any forward transition, its initiating actor and independent verification owner must establish:

   - Confirmed external initialization and the same immutable case identity throughout the evidence chain.
   - The exact current confirmed source state.
   - Submission, grant and attempt identities applicable to that phase.
   - The initiating actor's current authority.
   - Current validity, revocation and expiry observations.
   - All transition-specific guards and prerequisite evidence.
   - Confirmed acknowledgment of every required previous transition and checkpoint.
   - Absence of an unresolved adverse condition.

   Every transition requires an authenticated record binding its identifier, source, destination, actor, independent decision owner, case identity, evidence references, applicable identities, permitted effects and observed outcome.

   Its acknowledgment must bind that exact record and request. The receiving actor must validate independent origin, identity, freshness and applicability before the next effect.

   These remain semantic requirements. The receipt format, transport, authentication implementation, durable destination and commit point remain unresolved.

   A proposed record, sent acknowledgment or producer assertion is not a confirmed transition. The future mechanism must distinguish pending proposals from confirmed transitions and prove acknowledgment receipt and validation. Otherwise it is not grant-ready.

   An unregistered or unacknowledged initial case cannot be used by B1-T01 or any subsequent transition.

   A missing prerequisite while legitimately waiting permits no transition or effect. An attempted transition with invalid authority, a failed operation or an uncertain outcome follows the applicable adverse rule.

   For every transition, failure, interruption and ambiguity use the adverse transition from its actual confirmed nonterminal state. If commitment or current state cannot be established, `UNCERTAIN` takes precedence. No actor may guess a destination.

   **The normal and review transitions remain exactly these twelve.**

   **B1-T01 has source `P0` and destination `P1`.**  
   `P` initiates delivery of the complete authorized revision. `C` independently verifies confirmed external initialization, approval scope and submission provenance. Guards require the acknowledged initial case, one-revision planning approval, unchanged predecessors and B0 artifacts, and a complete conversational packet. The only substantive effect is delivery of that packet. Its authenticated submission record and receipt identify the case, revision and outstanding received-byte measurement. There is no filesystem or operational effect.

   **B1-T02 has source `P1` and destination `P2`.**  
   The authorized submission custodian initiates exact-artifact identification and review handoff. `C` independently verifies provenance and the received artifact's newly measured byte length and SHA-256. Guards require an unambiguous complete artifact and authority for review handoff. Effects are limited to recording its identity and making that exact artifact available through approved channels to `M`. The acknowledgment binds the new R2 identity. Neither predecessor identity can satisfy this transition.

   **B1-T03 has source `P2` and destination `P3`.**  
   `M` initiates a positive planning disposition. `M` owns the independent content decision; `C` verifies authenticity, exact-artifact binding and required owner acceptance of planning content. Guards require a complete positive review of this exact revision and no unresolved blocking planning defect. Effects record planning acceptance and remaining grant prerequisites. The acknowledgment explicitly states that no writing grant or entitlement is issued.

   **B1-T04 has source `P2` and destination `PLAN_CHANGES_REQUESTED`.**  
   `M` initiates a changes-requested decision. `M` owns that decision and `C` verifies exact revision binding. Guards require a determinate authenticated disposition identifying corrections. Effects preserve the decision and findings. The record and acknowledgment terminate this revision's review case. They authorize no revision, repair or retry.

   **B1-T05 has source `P2` and destination `PLAN_REJECTED`.**  
   `M` initiates determinate rejection. `M` owns the decision and `C` verifies authenticity and artifact binding. Effects are limited to recording rejection and reasons through approved channels. The acknowledged disposition is terminal and issues no operational authority.

   **B1-T06 has source `P3` and destination `O0`.**  
   `H` initiates an exact B1 materialization grant. `C` independently verifies human authority, the accepted plan and complete pre-grant evidence. Every mandatory pre-grant dependency must already be independently satisfied, including custody, launcher, immutable closure, principals, isolation, acknowledgment transport, synchronization implementation, stopping policy, complete effects, volatility acceptance and recoverability.

   The grant binds a fresh attempt identity, exact destination, both payloads, two ordered copy-launch slots, permitted effects, finite limits, validity, observation permissions and adverse handling. Effects are limited to issuing and recording the grant and attempt. There is no consumption, creation or launch. Acknowledgment confirms the exact grant. Prerequisite evidence alone cannot cause this transition.

   **B1-T07 has source `O0` and destination `O1`.**  
   `S` initiates B1 materialization-entitlement consumption. `C` independently verifies the current grant, unused entitlement, attempt identity and consumption result. Guards require confirmed `O0`, current authority and prevention of repeated consumption or restoration.

   Effects are limited to consuming one B1 attempt entitlement and recording that fact. No candidate is created. `S` must receive and validate independently authenticated consumption confirmation before `O1` is usable. Missing or ambiguous confirmation requires `UNCERTAIN`, without a consumption retry.

   **B1-T08 has source `O1` and destination `O2`.**  
   `S` initiates bounded materialization. `C` independently verifies confirmed consumption and fresh launch guards. Guards include acknowledged `O1`, current authority, unchanged inputs and dependencies, absent destination, active enforcement and ready observation channels.

   `S` must receive and validate acknowledgment of entry into `WRITING` before the first creation. Subsequent filesystem and process effects are limited to the ordered §4 procedure. It permits at most one materialization attempt and two copy launches: source once, then companion once. The source checkpoint must be independently acknowledged before companion creation or launch.

   Intermediate checkpoints are permitted actions within `O2`, not additional lifecycle transitions or opportunities to relaunch. A failed first copy leaves the second unstarted.

   **B1-T09 has source `O2` and destination `O3`.**  
   `S` initiates producer completion after the complete procedure succeeds. `C` independently checks observations, launch counters, synchronization, metadata checks, descriptor closure and absence of active writers. Guards require both specified copies, every required acknowledgment and no evidence gap.

   Effects record producer completion and retain custody with further writer effects denied. The acknowledgment binds resulting objects and evidence. It issues no exact-byte acceptance. A producer-stage failure cannot be carried forward into O4 by treating this guard as satisfied.

   **B1-T10 has source `O3` and destination `O4`.**  
   `V` initiates independent review under explicit review authority. `C` verifies appointment, independence and exact review target. Guards require acknowledged producer completion, intact custody, accepted original inputs and complete evidence. Effects permit only approved read-only verification and associated evidence records. No candidate mutation or repair is allowed.

   **B1-T11 has source `O4` and destination `STAGING_VERIFIED`.**  
   `V` initiates a positive independent B1 decision. `V` owns the decision; `C` independently verifies authority, completeness and binding. Guards require valid completion of the review, positive results for every §5 requirement and confirmation of applicable state, custody, identity, authority and acknowledgment evidence.

   Effects record exact-byte staging acceptance and its authenticated acknowledgment. This terminal grants no archive transfer, publication, Gate A action or operational use.

   **B1-T12 has source `O4` and destination `B1_REVIEW_REJECTED`.**  
   `V` initiates a complete, authenticated independent review decision that determinately rejects the artifacts. `V` owns the artifact-verification decision and `C` independently verifies its authority, completeness, event binding and evidence.

   Its guard requires valid completion of the required review procedure, observations and acknowledgments, with no review-mechanism failure that invalidates completion and no higher-priority adverse condition.

   An independently established content, ownership, permission or byte mismatch in that otherwise complete review is a negative artifact-verification result and belongs to B1-T12. Such a mismatch alone cannot satisfy B1-F-O4.

   Effects preserve the negative decision, every observed finding and its authenticated acknowledgment. They permit no repair, retry or alternative terminal classification.

   **The adverse families retain all fifty-four identifiers and pairs.**

   Every registry member below inherits the common contract and its family's actors, guards, effects, record, acknowledgment and failure rules. The O4-specific classification rule following the registry is mandatory.

   For `B1-U`, an authorized detector reports uncertainty and `C` initiates and independently verifies the safety disposition. Its guard is uncertainty about effects, state, custody, identity, observations, consumption or acknowledgment. Effects deny new forward actions and permit only preauthorized bounded stopping and evidence retention. The record preserves the last confirmed state and pending operations. Failure to record or acknowledge the terminal leaves eligibility denied and the disposition uncertain.

   ```ini
   B1-U-P0=P0,UNCERTAIN
   B1-U-P1=P1,UNCERTAIN
   B1-U-P2=P2,UNCERTAIN
   B1-U-P3=P3,UNCERTAIN
   B1-U-O0=O0,UNCERTAIN
   B1-U-O1=O1,UNCERTAIN
   B1-U-O2=O2,UNCERTAIN
   B1-U-O3=O3,UNCERTAIN
   B1-U-O4=O4,UNCERTAIN
   ```

   For `B1-R`, `H` initiates revocation or withdrawal of applicable authority. `C` independently authenticates the decision and scope. Guards require determinate revocation and no higher-priority uncertainty. Effects deny forward actions, stop active work through the preauthorized bounded mechanism and preserve evidence. The terminal record and acknowledgment bind the revoked authority. Ambiguity before confirmed terminal entry uses `B1-U`.

   ```ini
   B1-R-P0=P0,REVOKED
   B1-R-P1=P1,REVOKED
   B1-R-P2=P2,REVOKED
   B1-R-P3=P3,REVOKED
   B1-R-O0=O0,REVOKED
   B1-R-O1=O1,REVOKED
   B1-R-O2=O2,REVOKED
   B1-R-O3=O3,REVOKED
   B1-R-O4=O4,REVOKED
   ```

   For `B1-E`, `C` initiates expiry disposition from independently verified time and an actual authority deadline. Guards require determinate expiry, no applicable revocation taking precedence and no uncertainty. Effects deny forward work and permit only approved stopping and retention. The record and acknowledgment bind deadline and time evidence. No expiry is inferred for the present correction approval.

   ```ini
   B1-E-P0=P0,EXPIRED
   B1-E-P1=P1,EXPIRED
   B1-E-P2=P2,EXPIRED
   B1-E-P3=P3,EXPIRED
   B1-E-O0=O0,EXPIRED
   B1-E-O1=O1,EXPIRED
   B1-E-O2=O2,EXPIRED
   B1-E-O3=O3,EXPIRED
   B1-E-O4=O4,EXPIRED
   ```

   For `B1-A`, `C` initiates disposition upon independently established invalid authority, such as a wrong grant, unauthorized actor, scope mismatch or attempted use of another entitlement. Guards require a determinate defect, with uncertainty, revocation and expiry handled first. Effects deny progress and preserve authority evidence. The authenticated record and acknowledgment identify the defect. They grant no substitute authority.

   ```ini
   B1-A-P0=P0,AUTHORITY_INVALID
   B1-A-P1=P1,AUTHORITY_INVALID
   B1-A-P2=P2,AUTHORITY_INVALID
   B1-A-P3=P3,AUTHORITY_INVALID
   B1-A-O0=O0,AUTHORITY_INVALID
   B1-A-O1=O1,AUTHORITY_INVALID
   B1-A-O2=O2,AUTHORITY_INVALID
   B1-A-O3=O3,AUTHORITY_INVALID
   B1-A-O4=O4,AUTHORITY_INVALID
   ```

   For `B1-F`, the responsible actor reports a determinate procedure, command, control, dependency, synchronization or metadata failure, and `C` initiates and independently verifies disposition. Guards require known effects and exclusion of higher-priority adverse conditions. Effects stop the sequence, deny further launches and retain artifacts unchanged. The record and acknowledgment identify the failed operation and known effects. Resulting uncertainty uses `B1-U`.

   For O4 specifically, this family's guard is restricted to a determinate failure of the review procedure, tooling, required dependencies or independent controls that prevents or invalidates valid review completion for the same event. A valid completed artifact-verification decision must be absent. A known artifact metadata mismatch is expressly excluded from that mechanism-failure guard.

   ```ini
   B1-F-P0=P0,FAILED
   B1-F-P1=P1,FAILED
   B1-F-P2=P2,FAILED
   B1-F-P3=P3,FAILED
   B1-F-O0=O0,FAILED
   B1-F-O1=O1,FAILED
   B1-F-O2=O2,FAILED
   B1-F-O3=O3,FAILED
   B1-F-O4=O4,FAILED
   ```

   For `B1-I`, the responsible actor reports interrupted work or required evidence that cannot be completed, and `C` initiates and independently verifies disposition. Guards require effects, identities, custody and acknowledgment status to remain determinate. Normal waiting for a future planning prerequisite is not this trigger. Effects stop forward work and retain incomplete evidence and artifacts. The record and acknowledgment distinguish completed, incomplete and unstarted operations. Unknown facts require `B1-U`; an established higher-priority mechanism failure requires `B1-F`.

   ```ini
   B1-I-P0=P0,INCOMPLETE
   B1-I-P1=P1,INCOMPLETE
   B1-I-P2=P2,INCOMPLETE
   B1-I-P3=P3,INCOMPLETE
   B1-I-O0=O0,INCOMPLETE
   B1-I-O1=O1,INCOMPLETE
   B1-I-O2=O2,INCOMPLETE
   B1-I-O3=O3,INCOMPLETE
   B1-I-O4=O4,INCOMPLETE
   ```

   **Classification precedence permits one terminal outcome for an event.**

   The existing precedence remains uncertainty, revocation, expiry, invalid authority, procedure failure and incompleteness, followed by an eligible normal or review decision.

   At O4, apply it as follows:

   1. If a terminal disposition is already confirmed, make no transition. Retain later evidence as annotations.
   2. If effects, state, custody, identity, observations or acknowledgment status are ambiguous, use B1-U-O4.
   3. For otherwise determinate revocation, expiry or invalid authority, apply the retained adverse precedence.
   4. If a determinately failed review procedure, tool, required dependency or independent control prevents valid completion, use B1-F-O4. This condition excludes a valid completed independent artifact decision for the same event.
   5. If review is interrupted or required evidence is determinately incomplete without such a higher-priority failure, use B1-I-O4.
   6. A valid complete authenticated review uses B1-T11 for a positive artifact decision or B1-T12 for a determinate negative artifact decision.

   B1-T12 and B1-F-O4 are therefore disjoint. A wrong observed artifact value is not a failed observation mechanism. A failed mechanism that prevents valid review completion is not a complete negative artifact verdict.

   `V` must report every observed finding and the review's completion status. `C` must independently verify the classification and confirm that no terminal outcome has already been accepted for the same case and review event. Actors cannot select a different terminal merely by describing the same mismatch as a “metadata failure.”

   If conflicting reports prevent a determinate classification while the case remains nonterminal, B1-U-O4 applies. All findings and conflicting reports remain evidence even though only one terminal disposition is permitted.

   A producer-stage failure already recorded in an earlier state remains terminal there. It cannot be deferred into O4 or reclassified by reopening that case.

   **Successor and terminal rules remain unchanged.**

   The only normal successors are:

   - `P0` permits `P1`.
   - `P1` permits `P2`.
   - `P2` permits `P3`, `PLAN_CHANGES_REQUESTED` or `PLAN_REJECTED`.
   - `P3` permits `O0` only through B1-T06.
   - `O0` permits `O1`.
   - `O1` permits `O2`.
   - `O2` permits `O3`.
   - `O3` permits `O4`.
   - `O4` permits `STAGING_VERIFIED` or `B1_REVIEW_REJECTED`.

   Each nonterminal also permits only its six registered adverse transitions, subject to their guards. No unlisted transition is permitted.

   Missing or ambiguous acknowledgment after an attempted transition cannot restore the prior state's eligibility. The supervisor must stop forward progress. A late acknowledgment is retained evidence only.

   A confirmed terminal disposition never changes. Later observations, receipts or annotations remain separate records. They cannot repair artifacts, authorize retry, rewrite the disposition or turn a pending positive proposal into acceptance.

   A later adverse observation against `STAGING_VERIFIED` must be disclosed before future reliance or authorization. It does not rewrite the historical terminal decision.

   If terminal recording is unavailable, the supervisor must still deny further effects. Missing terminal acknowledgment cannot restore eligibility. The future mechanism must preserve that denial across restart.

   Stopping after terminal entry is limited to already authorized containment of the identified active child. It confers no cleanup authority. An unconfirmed stop requires uncertainty handling.

   Any subsequent revision or materialization attempt requires separate human authority and a new case or attempt identity. It is not a transition out of this case. A retained occupied destination cannot be silently reused.

8. Exact correction statement

   B1-R1-N01 is addressed by the external P0 establishment prerequisite. It specifies the namespace and fresh identity requirements, exact human authorization, terminal predecessor references, uniqueness guard, initiation actor, independent owner, durable initial record and authenticated confirmation. All subsequent transitions require that established case. No registry implementation, actual registration or thirteenth transition is introduced.

   B1-R1-N02 is addressed by mutually exclusive O4 guards and explicit precedence. A valid completed negative artifact review uses B1-T12. A determinate mechanism failure preventing valid completion uses B1-F-O4. Ambiguity uses B1-U-O4. Only one terminal outcome may be confirmed for the event, while every finding is retained.

   The twelve normal or review transitions and fifty-four adverse transitions remain. Their actors, one-use B1 entitlement, authenticated-record requirements, stopping policy, terminal absorption and separation from Gate A L06 are preserved.

   Neither correction satisfies an operational prerequisite. Acknowledgment transport, synchronization implementation, launcher, immutable closure, principals, isolation, complete effects, finite stopping, independent observation, volatility acceptance and recoverability remain unresolved.

The separate updated unresolved-requirements register follows.

- **R01. Exact R2 received-byte identity remains outstanding.** An authorized custodian and independent reviewer must measure the actual received R2 artifact. Neither predecessor identity identifies this submission.

- **R02. Independent Master review remains required.** N01 and N02 are proposed corrections pending review. B1-F01 remains open until Master closure. No planning acceptance follows from authoring approval.

- **R03. External planning-case establishment remains unperformed.** Select and independently establish the authoritative namespace, fresh case identity, uniqueness evidence, initial durable record and authenticated acknowledgment before asserting P0. This packet selects no registry implementation and creates no record.

- **R04. Exact predecessor-case evidence remains required.** Recover the immutable R1 terminal review-case and decision identities, its `CHANGES_REQUESTED` disposition and the predecessor lineage. The artifact hash cannot substitute for case and decision identities.

- **R05. Human authorization binding must enter the initial evidence chain.** The original R2 approval and scope-message references were recovered read-only. External initialization must independently bind their exact content, authenticated principal and scope to this one case. Authoring approval alone does not establish P0.

- **R06. Original B0 evidence remains required.** Preserve and recover the original source-review, finding and closure records. Their accepted dispositions are unchanged.

- **R07. Receiving-runtime raw inputs remain unverified.** Establish actual access to all three original attachments, backing identities, transfer effects and independent receiving-runtime lengths and hashes.

- **R08. Extraction observations require receiving-runtime confirmation.** Verify the reported ranges, complete slice equality and final LF bytes against the received export.

- **R09. Principal appointment remains open.** Name the actual actors, authentication and independence rules. Approve writer ownership, supplementary-group restrictions and reviewer access.

- **R10. Launcher and supervision remain unselected.** Identify a suitable existing implementation and independently accepted evidence. Any new implementation or qualification requires separate explicit authority.

- **R11. Immutable dependency closure remains incomplete.** Historical installed-tool observations do not establish complete manifests, immutable backing objects or independent acceptance.

- **R12. Isolation and fresh parent guards remain open.** Approve enforcement and setup effects. Re-establish host, namespace, parent, mount, symlink, ACL and target-absence observations before creation.

- **R13. Acknowledgment transport remains a pre-grant blocker.** Specify the receive path, descriptor configuration, format, authentication, freshness, replay exclusions, deadlines and durable destination. Establish validation before every next effect.

- **R14. State commitment and restart behavior remain unqualified.** Bind the mechanism distinguishing pending proposals from confirmed transitions, preserving terminal denial and preventing two terminal outcomes for the same event. The planning contract proves no implementation.

- **R15. Synchronization implementation remains unbound.** Approve exact output, directory and parent synchronization implementations, dependencies, metadata checks, close semantics and failure handling.

- **R16. The complete effect inventory remains open.** Enumerate candidate effects and separately authorized ingress, isolation, observation, logging and receipt-storage effects. No implicit additional writes are permitted.

- **R17. Finite stopping remains unqualified.** Bind limits, clock boundaries, acknowledgment deadlines, child identity, exact stop actions and independent stop confirmation.

- **R18. Volatility acceptance and recoverability remain mandatory.** Obtain explicit owner acceptance and independent recovery evidence for required originals and records. Accept the archive and handoff design before staging becomes the only retained copy needed for retrieval.

- **R19. Exact human B1 materialization authority remains absent.** After independent planning acceptance and satisfaction of all mandatory pre-grant requirements, the human must issue an exact grant for a fresh bounded attempt.

- **R20. Result observations necessarily occur later.** Created-object identities, lengths, hashes, equality, synchronization, effects and custody continuity require an authorized attempt. Before grant issuance, observers and methods must already be accepted.

- **R21. Durable preservation and publication remain separate.** Archive transfer, independent retrieval verification, GitHub indexing, ledger edits and Plane recording require their own exact authorizations.

This submission consumes only the approved single R2 conversational correction permission. No automatic revision or progression is authorized.

```ini
B1_R2_CORRECTION_GRANT=ISSUED_AND_CONSUMED_FOR_THIS_ONE_CONVERSATIONAL_SUBMISSION
B1_R2_RECEIVED_PACKET_BYTES=REQUIRES_FRESH_INDEPENDENT_MEASUREMENT
B1_R2_RECEIVED_PACKET_SHA256=REQUIRES_FRESH_INDEPENDENT_MEASUREMENT
B1_R2_MASTER_REVIEW=REQUIRED
B1_AUTH01=RESOLVED
B1_R1_N01=PENDING_INDEPENDENT_REVIEW
B1_R1_N02=PENDING_INDEPENDENT_REVIEW
B1_F01=OPEN_UNTIL_MASTER_CLOSURE
B1_PLANNING_CASE_INITIALIZATION=NOT_ESTABLISHED_BY_THIS_SUBMISSION
B1_MATERIALIZATION_GRANT=NOT_ISSUED
B0_SOURCE_REVISION_AUTHORIZED=NO
B0_EXACT_BYTES_FROZEN=NO
B1_PERSISTENCE=NOT_AUTHORIZED
DURABLE_ARCHIVE=NOT_ESTABLISHED
GITHUB_PLANE_EVIDENCE_INDEX=NOT_PUBLISHED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
GATE_B_ACTIVATION=NOT_AUTHORIZED
GATE_2_ACTIVATION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```