This is the complete B1-R1 conversational planning submission. Your approval authorizes this revision only. The lifecycle correction remains subject to a new exact received-byte identity and independent Master Gate review.

1. Authority and revision identity

   ```ini
   TASK=ACQ_EXEC_06_B1_R1_PLANNING_CORRECTION
   PREDECESSOR=B1-R0
   REPORTED_PREDECESSOR_BYTES=25416
   REPORTED_PREDECESSOR_SHA256=eb2d1597227814c4a29392a3843474bc0e83e1cea0255c60f5814fb73daa638e
   PREDECESSOR_MASTER_VERDICT=CHANGES_REQUESTED
   CORRECTION_AUTHORITY=PROJECT_OWNER_APPROVAL_IN_THIS_CONVERSATION
   CORRECTION_SCOPE=ONE_COMPLETE_CONVERSATIONAL_PLANNING_REVISION
   B1_F01=PENDING_INDEPENDENT_REVIEW
   ```

   The predecessor identity is supplied by the review report. I have not independently accessed that exact raw artifact. Its identity does not identify this revision.

   This submission leaves B1-R0 and the B0 artifacts unchanged. It grants no implementation, materialization, qualification, archive, publication or operational authority.

   Read-only inspection reconfirmed these local Git identities:

   ```ini
   REPOSITORY=JCSchoeman96/symphony
   BASE_MAIN_SHA=4971ddde384ef54b06498db438d2bfe36a0f108a
   BASE_MAIN_TREE=540617e1c62af1550059113c5166bea315cc6015
   ACQ_EXEC_05_R2_PLAN_BLOB=1fd0af3e23287bab8939876589abc064c5655b45
   ```

   This establishes the inspected local objects. It does not certify the current remote protected-main ref, CI or an operational environment.

   The accepted B0 entry remains:

   ```ini
   B0_STATIC_SOURCE_VERDICT=ACCEPTABLE_FOR_EXACT_BYTE_FREEZE_REVIEW
   B0_F01_TO_F04=CLOSED
   B0_R01_TO_R03=CLOSED
   B0_N01_TO_N03=CLOSED
   B0_E01=RESOLVED
   B0_E02=RESOLVED
   B0_SOURCE_REVISION_AUTHORIZED=NO
   ```

   These are accepted entry conditions supplied by the human. Original finding records and the independent decision must remain part of the future evidence chain.

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

   The reported ranges have the specified lengths. They are observations from the independent reviewer's runtime. They establish no attachment access, backing-object identity or custody in a future writer runtime.

   Before candidate creation, an authorized custodian must deliver the original raw export and both exact payload attachments into the actual receiving runtime. The custody record must identify their origin, attachment references, custodian, transfer mechanism, receiving runtime and backing objects.

   Rendered text, copied Markdown and reconstructed files are insufficient. Any ingress cache, download file or transport log requires an explicitly enumerated effect allowance. None is implicitly included in candidate creation.

   A separate reviewer must independently:

   - Establish all three received lengths and SHA-256 hashes.
   - Authenticate their relationship to the reviewed B0 submission.
   - Confirm the reported ranges against the received export.
   - Compare the complete source and companion slices with their respective attachments.
   - Check that the slices include the final LF immediately before each closing fence.
   - Record the attachment, backing-object and extraction evidence.

   In particular, the expected final LF positions are export offsets `60968` and `87326`. Their actual byte values must be independently checked in the receiving runtime.

   No trimming, newline conversion, dedentation, Unicode normalization or editor save is permitted.

   The reviewer must issue an authenticated input-custody acceptance before materialization. The accepted input objects must then remain protected against modification and substitution. The writer receives read-only descriptors for those same objects at offset zero.

   If the separate payload attachments do not yet exist, extracting and creating them requires its own exact authorization. This packet authorizes no such creation.

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

   Read-only inspection reconfirmed:

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

   PROPOSED_CANDIDATE_DIRECTORY=ABSENT_AT_INSPECTION
   CURRENT_UID=1000
   CURRENT_GID=1000
   ```

   Propose owner UID `1000`, GID `1000`. The directory would begin at `0700` and finish at `0500`. Each payload would be created at `0400`, without executable bits. These selections require explicit approval in the later grant.

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

   Inputs and dependencies must be exposed so that reading them does not cause undeclared metadata writes. Isolation setup, ingress and evidence-service effects need their own complete allowances.

   File modes alone do not exclude another process with the same UID or a privileged process. Continuous exclusion of unauthorized writers and substitution must be independently established through the selected isolation mechanism.

   Resulting identities must include host and namespace context, mount identity, device, inode, file type, link count, numeric ownership, permissions, size and relevant timestamps. A pathname or inode alone is insufficient.

4. Future writer, acknowledgments and synchronization

   No launcher or supervision mechanism has been selected and independently accepted. Describing the following contract does not qualify one.

   Read-only inspection reconfirmed the copying utility:

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

   The installed hashing, size and metadata applets also resolve to that uutils executable identity. The independent comparison utility is:

   ```ini
   CMP=/usr/bin/cmp
   CMP_BYTES=43592
   CMP_SHA256=82b923f0f12706950d696fb63fe3d8d8a4d2e559ec2a8a44f6c97ed2c56de44e
   ```

   These observations do not establish an immutable dependency closure. The later grant must bind the supervisor, utilities, loader, libraries, runtime data, kernel and isolation implementations, including resolved paths, bytes, hashes and immutable backing identities.

   Preserve these proposed limits:

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

   The later grant must approve and implement these limits, define their clock boundaries, and bind the exact stopping actions. Missing stop confirmation within the approved bound requires `UNCERTAIN`. It permits no broader process killing, cleanup or repair.

   The supervisor needs controlled access to the accepted inputs, held parent and candidate directories, current output, evidence destination, acknowledgment ingress and identified child. Its complete descriptor configuration remains unresolved.

   R0's descriptor list must not be treated as complete. It did not establish how authenticated acknowledgments reach the supervisor. The later grant must specify:

   - The actual acknowledgment transport and receiving interface.
   - Every descriptor's number, direction, inheritance and close-on-exec behavior.
   - The independently authenticated receipt format and verification implementation.
   - Binding to the exact grant, attempt, transition, previous state and effect checkpoint.
   - Freshness and replay exclusions.
   - Finite acknowledgment deadlines.
   - The durable evidence destination and receipt of durable acceptance.

   Sending a record or acknowledgment does not prove that the supervisor received and validated it. No next effect is allowed without that validation. No socket, descriptor number, signature scheme or receipt protocol is invented here.

   Each copy child would inherit only:

   - FD `0`, its accepted input at offset zero.
   - FD `1`, its exclusively created output.
   - FD `2`, the approved diagnostic channel.

   Other inherited descriptors must be closed. Runtime dependency reads remain limited to the approved immutable closure.

   The bounded materialization procedure would be:

   1. Confirm the independently acknowledged B1 entitlement consumption and the acknowledged entry into `WRITING`.
   2. Revalidate current authority, custody, isolation, identities and observation readiness.
   3. Create the candidate with `mkdirat` relative to the held parent, mode `0700`, without recursive creation. Open it with directory and no-follow requirements. Independently confirm its identity, ownership and permissions.
   4. Create `qualification_authority.py` relative to the held candidate directory using `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`, mode `0400`. Check its initial descriptor identity, ownership, type and link count.
   5. Launch exactly once:

      ```text
      /usr/lib/cargo/bin/coreutils/dd bs=65536 status=none
      ```

      Its input is the accepted source descriptor. Its output is the new source file descriptor. No pathname operands or conversions apply.

   6. Observe child termination and exit status zero. Confirm that no child or unauthorized writable alias remains. The supervisor checks the output descriptor and expected length `59880`, performs output synchronization, checks metadata again and closes its writable descriptor.
   7. Obtain independent acknowledgment of the completed source checkpoint before creating the companion.
   8. Create `source_review_packet.md` with the same exclusive flags and mode. Launch the identical command exactly once with the accepted companion descriptor.
   9. Observe termination and exit status zero. The supervisor checks length `26302`, synchronizes that output, checks metadata again and closes its writable descriptor.
   10. Obtain independent acknowledgment of the completed companion checkpoint.
   11. Change only the new candidate directory to mode `0500` through its held descriptor. Verify its identity and final metadata.
   12. Synchronize the candidate directory after both file synchronizations and the mode change. Then synchronize the parent directory containing the new candidate entry.
   13. Recheck the directory entries against held identities, ownership, permissions, sizes, link counts and custody observations. Confirm writer termination and closure of writable access.
   14. Obtain independent acknowledgment of the complete producer evidence before requesting `PRODUCER_COMPLETE`.

   The proposed synchronization semantics are successful `fsync` operations on each completed output, then the candidate directory, then its parent. The supervisor owns those operations. A copy utility's successful exit does not substitute for them.

   The later grant must bind the exact syscall or utility implementations, dependencies, error interpretation and close behavior. No such operations were executed here.

   Any synchronization error, failed metadata check, abnormal exit, observation gap or close ambiguity stops the sequence. No synchronization retry, second copy launch for the same payload or metadata repair follows automatically.

   The two files do not form an atomic transaction. A partial file, one complete file or an empty directory can remain after failure. Retained objects receive no automatic cleanup or promotion.

5. Independent B1 verification

   A separately appointed reviewer must obtain the accepted inputs and their custody evidence independently of the producer's report. Writer access must have ended, and custody must remain intact.

   Proposed read-only commands, with the independently identified candidate directory as the working directory, include:

   ```text
   /usr/bin/wc --bytes -- qualification_authority.py source_review_packet.md

   /usr/bin/sha256sum --binary -- qualification_authority.py source_review_packet.md

   /usr/bin/stat --format='%n|%F|%d|%i|%h|%u|%g|%a|%s|%y|%z' -- . qualification_authority.py source_review_packet.md

   /usr/bin/cmp -- /proc/self/fd/3 qualification_authority.py

   /usr/bin/cmp -- /proc/self/fd/4 source_review_packet.md

   /usr/bin/cmp --bytes=59880 --ignore-initial=1089:0 -- /proc/self/fd/5 qualification_authority.py

   /usr/bin/cmp --bytes=26302 --ignore-initial=61025:0 -- /proc/self/fd/5 source_review_packet.md
   ```

   Reviewer FDs `3`, `4` and `5` would refer to the independently accepted source, companion and export objects. The descriptor references do not authorize arbitrary symlink traversal.

   The entire export must first match its accepted length and hash. Entire candidate lengths must also match, because the bounded comparisons alone do not reject trailing bytes.

   The reviewer must independently establish:

   - Both exact lengths and SHA-256 hashes.
   - Whole-file equality with the accepted payload attachments.
   - Equality with the verified export slices and final LF boundaries.
   - Regular-file type, link count one, approved UID/GID and mode `0400`.
   - Candidate ownership and final mode `0500`.
   - Agreement between descriptors and directory entries.
   - The required synchronization sequence and observed results.
   - Complete entitlement, launch-count, authority and acknowledgment evidence.
   - Continuous custody and compliance with the complete effect allowance.

   The verifier's implementation and dependencies require approval. It must disclose observation limitations.

   Producer completion, producer hashes and exit status zero cannot issue independent acceptance. A separate authenticated B1 decision must identify the exact grant, attempt, objects and evidence.

6. Durability, recoverability and future indexing

   `/tmp` staging is volatile. It is not the durable archive. Successful synchronization on the observed `tmpfs` does not establish reboot or power-loss survival.

   Disposable staging may be authorized only after:

   - The project owner explicitly accepts its volatility.
   - A separate reviewer independently establishes recoverability of every required original and evidence record.
   - The grant identifies the retention owners and the evidence supporting that recovery claim.

   If future retrieval depends on B1 outputs, the archive and handoff design must be accepted before staging becomes their only retained copy. Required originals or evidence must not be discarded on the strength of staging-file existence.

   Restoring identical content later would not recreate the original staging inode or constitute a continuation of its attempt. Any new materialization requires new authority.

   Preserve this proposed future index location:

   ```text
   docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_EVIDENCE_INDEX.md
   ```

   The future index must bind:

   - Governing commit, tree and plan blob.
   - Original B0 export, payload identities and extraction ranges.
   - Original independent B0 review, finding and closure records.
   - Exact R1 received-byte identity and independent planning decision.
   - Human B1 grant, attempt identity and entitlement-consumption evidence.
   - Input custody, immutable dependencies, supervision and effect inventory.
   - Resulting file identities, synchronization observations and complete evidence.
   - Independent B1 verification decision and any adverse annotations.
   - Accepted archive and handoff design, retained object versions and recovery evidence.
   - Explicit nonauthorization of operational use.

   Durable publication, archive transfer, independent retrieval verification, GitHub indexing and Plane recording remain separate authorization boundaries.

   Recommend commit-pinned GitHub references and a narrowly scoped future ledger link. Existing Plane SGOV-2 remains the previously identified evidence owner:

   ```ini
   PLANE_WORKSPACE=symphony-development
   PLANE_PROJECT=f7317505-bc78-42ae-a902-1e3f0346bcff
   PLANE_WORK_ITEM=079ea0ea-dc3f-4a23-ac01-0a3e75e8c03b
   ```

   Any future mapping must be verified. No new issue, comment, attachment, state change, index, PR or publication is authorized by this submission.

7. Complete B1 lifecycle contract

   This contract governs a B1 planning case and its prospective materialization attempt. It does not replace, invoke or consume the Gate A L00–L22 lifecycle.

   The B1 materialization entitlement has its own kind, grant identity, attempt identity and consumption record. It is entirely separate from the Gate A L06 qualification-launch entitlement. Neither can substitute for, consume or restore the other.

   **Roles are requirements for later appointment.**

   - `H` is the project owner and human grant authority.
   - `P` is the authorized planner.
   - `M` is the independent Master Gate planning reviewer.
   - `S` is the future trusted supervisor.
   - `W` is the bounded copy process.
   - `V` is the independent B1 result verifier.
   - `C` is the independent custody, state-record and acknowledgment verification owner.

   Actual principals, authentication and permitted role combinations remain unresolved. `W` cannot decide acceptance, authenticate its own entitlement consumption or act as the independent verifier.

   **The nonterminal states are distinct.**

   - `P0 = PLANNING_AUTHORIZED`.
   - `P1 = SUBMITTED_IDENTITY_PENDING`.
   - `P2 = PLAN_REVIEW`.
   - `P3 = PLAN_ACCEPTED_BLOCKED`.
   - `O0 = GRANT_ISSUED`.
   - `O1 = ENTITLEMENT_CONFIRMED`.
   - `O2 = WRITING`.
   - `O3 = PRODUCER_COMPLETE`.
   - `O4 = INDEPENDENT_REVIEW`.

   States `P0`–`P3` are planning states. They confer no candidate creation or copy entitlement. No operational attempt exists before the exact human grant establishes `O0`.

   **The terminal states are absorbing.**

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

   They have no outgoing transitions, including self-transitions.

   A planning terminal does not imply that materialization occurred or that an operational entitlement was consumed.

   **Every listed transition inherits the following mandatory contract.**

   Before any forward transition, its initiating actor and independent verification owner must establish:

   - The exact current confirmed source state.
   - Submission, grant and attempt identities applicable to that phase.
   - The initiating actor's current authority.
   - Current validity, revocation and expiry observations.
   - All transition-specific guards and prerequisite evidence.
   - Confirmed acknowledgment of every required previous transition and checkpoint.
   - Absence of an unresolved adverse condition.

   Every transition requires an authenticated record binding its identifier, source, destination, actor, independent decision owner, evidence references, applicable identities, permitted effects and observed outcome.

   Its acknowledgment must bind that exact record and request. The receiving actor must validate its independent origin, identity, freshness and applicability before the next effect.

   These are semantic requirements. The actual receipt format, transport, authentication implementation, durable destination and commit point remain unresolved.

   A proposed record, a sent acknowledgment or a producer assertion is not a confirmed transition. The future mechanism must distinguish pending proposals from confirmed transitions and prove acknowledgment receipt and validation. Otherwise it is not grant-ready.

   A missing prerequisite while legitimately waiting permits no transition or effect. An attempted transition with invalid authority, a failed operation or an uncertain outcome follows the adverse rules below.

   For every transition, failure, interruption and ambiguity use the adverse transition from its actual confirmed nonterminal state. If the transition's commitment or current state cannot be established, `UNCERTAIN` takes precedence. No actor may guess the destination.

   **The normal and review-disposition transitions are exactly these twelve.**

   **B1-T01 has source `P0` and destination `P1`.**  
   `P` initiates delivery of the complete authorized revision. `C` independently verifies the approval scope and submission provenance. Guards require the one-revision planning approval, unchanged predecessor and B0 artifacts, and a complete conversational packet. The only substantive effect is delivery of that packet. Its authenticated submission record and receipt identify the revision and outstanding received-byte measurement. There is no filesystem or operational effect.

   **B1-T02 has source `P1` and destination `P2`.**  
   The authorized submission custodian initiates exact-artifact identification and review handoff. `C` independently verifies provenance and the received artifact's newly measured byte length and SHA-256. Guards require an unambiguous complete artifact and authority for the review handoff. Effects are limited to recording its identity and making that exact artifact available through approved channels to `M`. The acknowledgment must bind the new R1 identity. The R0 identity cannot satisfy this transition.

   **B1-T03 has source `P2` and destination `P3`.**  
   `M` initiates a positive planning disposition. `M` owns the independent content decision; `C` verifies its authenticity, exact-artifact binding and required owner acceptance of planning content. Guards require a complete positive review of this exact revision and no unresolved blocking planning defect. Effects record planning acceptance and the remaining grant prerequisites. The acknowledgment must explicitly state that no writing grant or entitlement is issued.

   **B1-T04 has source `P2` and destination `PLAN_CHANGES_REQUESTED`.**  
   `M` initiates a changes-requested decision. `M` owns that decision and `C` verifies its exact revision binding. Guards require a determinate, authenticated review disposition identifying the required corrections. Effects are limited to preserving the decision and findings. The record and acknowledgment terminate this revision's review case. They authorize no revision, repair or retry.

   **B1-T05 has source `P2` and destination `PLAN_REJECTED`.**  
   `M` initiates a determinate rejection. `M` owns the decision and `C` verifies its authenticity and artifact binding. Effects are limited to recording rejection and its reasons through approved channels. The acknowledged disposition is terminal and issues no operational authority.

   **B1-T06 has source `P3` and destination `O0`.**  
   `H` initiates issuance of an exact B1 materialization grant. `C` independently verifies the human authority, accepted plan and complete pre-grant evidence. Every mandatory pre-grant dependency must already be independently satisfied, including custody, launcher, immutable closure, principals, isolation, acknowledgment transport, synchronization implementation, stopping policy, complete effects, volatility acceptance and recoverability.

   The grant must bind a fresh attempt identity, exact destination, two payloads, two ordered copy-launch slots, permitted effects, finite limits, validity, observation permissions and adverse handling. Effects are limited to issuing and recording that grant and attempt. There is no entitlement consumption, creation or launch. Acknowledgment must confirm the exact grant. Prerequisite evidence alone cannot cause this transition.

   **B1-T07 has source `O0` and destination `O1`.**  
   `S` initiates consumption of the B1 materialization entitlement. `C` independently verifies the current grant, unused entitlement, attempt identity and consumption result. Guards require confirmed `O0`, current authority and a mechanism that prevents repeated consumption or restoration.

   Effects are limited to consuming one B1 attempt entitlement and recording that fact. No candidate is created. `S` must receive and validate independently authenticated confirmation of consumption before `O1` is usable. A missing or ambiguous confirmation requires `UNCERTAIN`, with no consumption retry.

   **B1-T08 has source `O1` and destination `O2`.**  
   `S` initiates the bounded materialization. `C` independently verifies confirmed consumption and all fresh launch guards. Guards include acknowledged `O1`, current authority, unchanged inputs and dependencies, absent destination, active enforcement and ready observation channels.

   `S` must receive and validate acknowledgment of entry into `WRITING` before the first creation. The only subsequent filesystem and process effects are the ordered procedure in §4. It permits at most one materialization attempt and at most two copy launches: source once, then companion once. The source checkpoint must be independently acknowledged before the companion is created or launched.

   Intermediate checkpoints are the expressly permitted actions within `O2`; they are not additional lifecycle transitions or opportunities to relaunch. A failed first copy leaves the second unstarted.

   **B1-T09 has source `O2` and destination `O3`.**  
   `S` initiates producer completion after the full procedure ends successfully. `C` independently checks the complete observations, launch counters, synchronization sequence, metadata checks, descriptor closure and absence of active writers. Guards require both specified copies, every required acknowledgment and no evidence gap.

   Effects are limited to recording producer completion and retaining custody with further writer effects denied. The acknowledgment binds the resulting objects and evidence. This transition issues no exact-byte acceptance.

   **B1-T10 has source `O3` and destination `O4`.**  
   `V` initiates independent result review under explicitly granted review authority. `C` verifies the reviewer's appointment, independence and exact review target. Guards require acknowledged producer completion, intact custody, accepted original inputs and complete evidence. Effects permit only the approved read-only verification and associated evidence records. No candidate mutation or repair is allowed.

   **B1-T11 has source `O4` and destination `STAGING_VERIFIED`.**  
   `V` initiates a positive independent B1 decision. `V` owns the verification decision; `C` independently verifies its authority, completeness and binding. Guards require all §5 checks to pass and every applicable state, custody, identity, authority and acknowledgment requirement to be confirmed.

   Effects are limited to recording exact-byte staging acceptance and its authenticated acknowledgment. This terminal disposition grants no archive transfer, publication, Gate A action or operational use.

   **B1-T12 has source `O4` and destination `B1_REVIEW_REJECTED`.**  
   `V` initiates a determinate negative verification decision. `V` owns the decision and `C` verifies its binding and evidence. Guards require a known review outcome without unresolved ambiguity. Effects preserve the rejection and reasons through approved channels. A known content, ownership or permission mismatch found by the completed review may support this rejection. Broken verification tooling or incomplete observations instead use the applicable adverse transition.

   **The adverse transition families are closed and individually identified.**

   Each registry entry below specifies its source and destination. Every member inherits the common transition contract and its family's actor, owner, guards, effects, acknowledgment and failure rules.

   For `B1-U`, an authorized detector reports uncertainty and `C` initiates and independently verifies the safety disposition. Its guard is uncertainty about effects, custody, identity, consumption, state commitment or acknowledgment. Effects immediately deny new forward actions and permit only preauthorized bounded stopping and evidence retention. The record must preserve the last confirmed state and all pending operations. Failure to record or acknowledge the terminal itself leaves eligibility denied and the disposition uncertain.

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

   For `B1-R`, `H` initiates revocation or withdrawal of applicable authority. `C` independently authenticates that decision and its scope. Guards require a determinate revocation and no higher-priority uncertainty. Effects deny forward actions, stop active work through the preauthorized bounded mechanism and preserve evidence. The terminal record and acknowledgment bind the revoked authority. Ambiguity before confirmed terminal entry uses `B1-U`.

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

   For `B1-E`, `C` initiates expiry disposition from independently verified time and an actual authority deadline. Guards require determinate expiry, no applicable revocation taking precedence and no uncertainty. Effects deny forward work and permit only approved stopping and retention. The terminal record and acknowledgment bind the deadline and time evidence. No expiry is inferred for the present correction approval.

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

   For `B1-A`, `C` initiates disposition upon independently established invalid authority, such as a wrong grant, unauthorized actor, scope mismatch or attempted use of another entitlement. Guards require a determinate defect, with uncertainty, revocation and expiry handled first. Effects deny further progress and preserve the authority evidence. The authenticated terminal record and acknowledgment identify the defect. They grant no substitute authority.

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

   For `B1-F`, the responsible actor reports a determinate procedure, command, control, dependency, synchronization or metadata failure, and `C` initiates and independently verifies disposition. Guards require known effects and exclusion of higher-priority adverse conditions. Effects stop the sequence, deny further launches and retain artifacts unchanged. The record and acknowledgment identify the failed operation and known effects. Any resulting uncertainty uses `B1-U`.

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

   For `B1-I`, the responsible actor reports interrupted work or required evidence that cannot be completed, and `C` initiates and independently verifies disposition. Guards require that effects, identities, custody and acknowledgment status remain determinate. Normal waiting for a future planning prerequisite is not this trigger. Effects stop forward work and retain incomplete evidence and artifacts. The record and acknowledgment distinguish completed, incomplete and unstarted operations. Unknown effects or acknowledgment status instead require `B1-U`.

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

   **Precedence and successor rules are mandatory.**

   While a case is nonterminal, uncertainty takes precedence. For otherwise determinate simultaneous adverse conditions, apply revocation, expiry, invalid authority, procedure failure and incompleteness in that order. Record all observed causes.

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

   Each nonterminal also permits only its six explicitly registered adverse transitions, subject to their guards. No unlisted transition is permitted.

   Missing or ambiguous acknowledgment after an attempted transition cannot restore the prior state's eligibility. The supervisor must stop forward progress. A late acknowledgment is retained evidence only.

   A confirmed terminal disposition never changes. Later observations, receipts or annotations must remain separate records. They cannot repair artifacts, authorize a retry, rewrite the disposition or transform a pending positive proposal into acceptance.

   A later adverse observation against `STAGING_VERIFIED` must be disclosed before any future reliance or authorization. It does not rewrite the historical terminal decision.

   If terminal recording is unavailable, the supervisor must still deny further effects. Missing terminal acknowledgment cannot restore eligibility. The future supervision mechanism must preserve that denial across restart.

   Stopping after terminal entry is limited to the already authorized containment actions for the identified active child. It confers no cleanup authority. An unconfirmed stop requires uncertainty handling.

   Any subsequent revision or materialization attempt requires separate human authority and a new case or attempt identity. It is not a transition out of this case. A retained occupied destination cannot be silently reused.

8. B1-F01 correction and preserved grant-readiness concerns

   B1-F01 is addressed in this proposed contract through twelve normal or review transitions, fifty-four individually identified adverse transitions, mandatory inherited record and acknowledgment requirements, explicit successors and absorbing terminals. Closure remains for independent Master Gate review.

   The additional concerns remain unresolved:

   - Acknowledgment transport now expressly requires a validated receiving path at the supervisor. The mechanism, descriptors, authenticated receipt format, replay controls and durable destination are not selected.
   - Synchronization now has an ordered owner and failure contract covering outputs, metadata, directory and parent. Exact implementations and their qualification remain unapproved.
   - Writer and supervision readiness still require an appointed launcher, immutable closure, principals, isolation, complete effects, finite stopping and independent observation. The contract itself proves none of those capabilities.

The separate unresolved-requirements register follows.

- **R01. Exact R1 review identity remains to be established.** An authorized custodian and independent reviewer must measure the actual received R1 artifact. This submission does not reuse the R0 identity or claim a hash for transport bytes not yet independently observed.

- **R02. Original review artifacts require custody verification.** Recover the exact reviewed R0 input, original Master findings and decision, and original B0 review and closure records. Their supplied identities and dispositions remain accepted reported inputs.

- **R03. Writer-runtime raw inputs remain unverified.** Establish actual access to the export and payload attachments, their backing objects, transfer effects and independent receiving-runtime hashes.

- **R04. Extraction observations require receiving-runtime confirmation.** The reported offsets are now known. Their applicability, complete slice equality and final LF bytes must still be independently established against the received export.

- **R05. Principal appointment remains open.** Name `H`, `P`, `M`, `S`, `V` and `C`, their authentication and independence requirements. Approve writer UID/GID, supplementary-group restrictions and reviewer access.

- **R06. Launcher and supervision remain unselected.** Identify an existing suitable implementation and accepted evidence. Any new implementation or qualification work requires separate explicit authority.

- **R07. Immutable dependency closure remains incomplete.** Installed utility observations are available read-only. Complete manifests, immutable backing identities and independent acceptance remain necessary.

- **R08. Isolation and parent guards remain open.** Approve the exact enforcement and setup effects. Repeat host, namespace, parent, mount, symlink, ACL and target-absence observations immediately before creation.

- **R09. Acknowledgment transport is a pre-grant blocker.** Specify the receive path, descriptor configuration, actual format, authentication, freshness, replay exclusions, deadlines and durable destination. Prove how the supervisor validates each required acknowledgment before the next effect.

- **R10. Transition commitment and restart behavior are pre-grant blockers.** Bind the implementation that distinguishes pending records from confirmed transitions and preserves terminal denial across interruption. Late receipts must not restore eligibility.

- **R11. Synchronization implementation remains unbound.** Approve exact output, directory and parent synchronization implementations, dependency identities, metadata checks, close semantics and failure dispositions.

- **R12. The complete effect inventory remains open.** Enumerate candidate effects and every separately authorized ingress, isolation, observation, logging and receipt-storage effect. No implicit additional writes are permitted.

- **R13. Finite stopping remains unqualified.** Bind limits, clock boundaries, acknowledgment deadlines, child identity, exact stop actions and independent stop confirmation. The proposed limits are not qualification results.

- **R14. Volatility acceptance and recoverability are mandatory pre-grant requirements.** Obtain explicit owner acceptance and independent recovery evidence for required originals and records. Accept the archive and handoff design before staging can become the only retained copy on which future retrieval depends.

- **R15. Exact human B1 authority remains absent.** After independent planning acceptance and satisfaction of every mandatory pre-grant requirement, the human must issue a grant bound to a fresh attempt and the complete closed operation.

- **R16. Result observations necessarily occur later.** Actual created-object identities, lengths, hashes, extraction equality, synchronization results, effects and custody continuity can only be established during and after an authorized attempt. Before grant issuance, the responsible observers and exact methods must already be accepted.

- **R17. Durable preservation and publication remain separate.** Archive transfer, retrieval verification, GitHub indexing, ledger edits and Plane recording need their own exact authorizations. No record was created here.

This submission consumes only the approved R1 conversational correction permission. No automatic continuation is authorized.

```ini
B1_R1_CORRECTION_GRANT=ISSUED_AND_CONSUMED_FOR_THIS_CONVERSATIONAL_SUBMISSION
B1_R1_RECEIVED_PACKET_BYTES=REQUIRES_NEW_INDEPENDENT_MEASUREMENT
B1_R1_RECEIVED_PACKET_SHA256=REQUIRES_NEW_INDEPENDENT_MEASUREMENT
B1_R1_MASTER_REVIEW=REQUIRED
B1_F01=PENDING_INDEPENDENT_REVIEW
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