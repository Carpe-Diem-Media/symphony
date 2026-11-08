B1-R0 remains blocked for a writing grant. The proposal below defines the permitted operation, but the reviewed raw attachments, original B0 finding records, and an identified writer and evidence mechanism are still required.

This turn performed read-only inspection. No candidate, directory, script, helper or fixture was created. No candidate was run, imported, compiled, linted or tested. Git, GitHub and Plane were not changed.

1. Authority and verified baseline

   This packet is `ACQ_EXEC_06_B1_R0_MATERIALIZATION_AUTHORIZATION_PACKET`. Its scope is exact-byte capture and independent verification planning.

   Read-only inspection established that local `main` matches:

   ```ini
   REPOSITORY=JCSchoeman96/symphony
   BASE_MAIN_SHA=4971ddde384ef54b06498db438d2bfe36a0f108a
   BASE_MAIN_TREE=540617e1c62af1550059113c5166bea315cc6015
   ACQ_EXEC_05_R2_PLAN_BLOB=1fd0af3e23287bab8939876589abc064c5655b45
   ```

   The plan blob is present at its expected repository path. This verifies local Git objects. It does not certify the present remote protected-main ref or its CI.

   I read the repository authority index, the accepted R2 plan and acceptance record, and live Plane SGOV-2. The accepted R2 record preserves separate planning, preparation, execution and acceptance decisions.

   Your supplied B0 verdict and finding dispositions are accepted entry conditions. I did not independently recover their original records. None of the 74 returned SGOV-2 comments matched ACQ-EXEC-06, the supplied B0 identities or the B0 finding identifiers.

   The B0 authoring grant remains consumed. Copying reviewed bytes would confer no source revision authority.

2. Input custody

   The future custodian must deliver these exact binary attachments into the authorized writer's actual runtime:

   ```ini
   EXPORT_BYTES=87753
   EXPORT_SHA256=f5b780f402a66b0054dd38aa735d4b04cabb85bb067fb3a8f73095ccd947048f

   SOURCE_NAME=qualification_authority.py
   SOURCE_BYTES=59880
   SOURCE_SHA256=d1db9f46646fcb1b1789e6f77599fe0c0d849a10689ba117a08d91611014ae91

   COMPANION_NAME=source_review_packet.md
   COMPANION_BYTES=26302
   COMPANION_SHA256=e1d8e30d2996e172ad957774dd237a1e45ae305369d8c12f19c08989bede6f35
   ```

   These are accepted targets, not observed filesystem objects.

   Delivery must use the original raw bytes. Rendered chat, copied Markdown, screenshots and reconstructed text are insufficient. A path reported by another conversation does not establish access here.

   The custody record must identify the custodian, originating review message or attachment, attachment identifier, transfer mechanism, receiving runtime, receipt time and actual backing object. Any attachment-cache files, transport logs or download outputs must be enumerated in the ingress section of a later authorization. They are outside the candidate creation allowance below.

   Before candidate creation, a separate reviewer must independently:

   - Read all three received objects and establish their lengths and SHA-256 hashes.
   - Establish their relationship to the original reviewed submission.
   - Identify the exact source and companion byte ranges within the export.
   - Compare each entire range with its corresponding raw attachment.
   - Record the byte offsets, boundary bytes and extraction rule.
   - Confirm that each range includes the final LF immediately before its closing Markdown fence.

   Extraction must preserve every byte. No newline conversion, trimming, dedentation, Unicode normalization, BOM adjustment or editor save is permitted.

   The reviewer must issue an authenticated input-custody acceptance bound to those objects. Matching filenames or a producer's hash report cannot satisfy this guard.

   The accepted input objects must then remain under custody that excludes modification and substitution. The writer receives read-only descriptors for those same objects, at offset zero. If the separate payload attachments do not exist, their extraction and attachment creation require explicitly enumerated authority before that work occurs.

3. Destination, ownership and isolation

   Propose this exact staging destination:

   ```text
   /tmp/symphony-gate-a-authority-candidate-r1/
   ```

   Its only proposed children are:

   ```text
   qualification_authority.py
   source_review_packet.md
   ```

   Current read-only observations were:

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

   PROPOSED_CANDIDATE_DIRECTORY=ABSENT
   CURRENT_UID=1000
   CURRENT_GID=1000
   ```

   These are present observations, not future custody guarantees.

   Propose owner UID `1000`, GID `1000`, subject to explicit approval. The directory would begin at `0700` and finish at `0500`. Both payload files would be created at `0400`, without executable bits.

   Before writing, the independent observer must re-establish:

   - The actual host, boot, user namespace and mount namespace.
   - The ownership, modes, device and inode of `/` and `/tmp`.
   - The mount containing `/tmp`, its backing identity and relevant options.
   - That neither parent component is an unexpected symlink.
   - That no inherited ACL or other access rule grants unintended access.
   - That the proposed directory name is absent, including as a dangling symlink.

   The writer must hold the verified parent directory open and use descriptor-relative operations. It must not rely on a check followed by unrestricted pathname resolution.

   Any existing candidate directory or target is a rejection condition. No reuse, adoption, overwrite, alternate suffix or automatic destination selection is authorized.

   Isolation must exclude input substitution, dependency substitution and unauthorized concurrent mutation through writing and independent review. Modes alone cannot provide that guarantee against another process with the same UID or a privileged process. The enforcement mechanism and its setup effects remain unresolved.

   Resulting file identities must include host and namespace context, mount identity, device, inode, regular-file type, link count, numeric ownership, mode, size and relevant timestamps. An inode or pathname alone is insufficient.

4. Deterministic writing procedure

   This is a proposed operation contract. No suitable descriptor-controlling launcher has yet been identified and verified. The contract must not be executed through an improvised helper.

   Use no candidate interpreter. Copy the inputs as opaque bytes.

   Read-only inspection identified the installed copying utility:

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

   The installed `mkdir`, `chmod`, `sha256sum`, `wc` and `stat` entries resolve to applets backed by that same executable identity. They must not be described as GNU coreutils.

   A later grant must approve a complete immutable dependency manifest. The current `dd` dependency inspection identified the dynamic loader, libc, libsystemd, libselinux, libgcc_s, libm and libpcre2-8. Their current files were hashed read-only, but immutable exposure and independent approval have not been established. The selected launcher, verifier tools and any runtime data files must also enter that manifest. Package versions alone are insufficient.

   The proposed process conditions are:

   ```ini
   WRITER_UID=1000
   WRITER_GID=1000
   UMASK=0077
   INITIAL_WORKING_DIRECTORY=/tmp
   COPY_WORKING_DIRECTORY=/tmp/symphony-gate-a-authority-candidate-r1
   ENVIRONMENT=LC_ALL=C;LANG=C;TZ=UTC
   INHERIT_OTHER_ENVIRONMENT=NO
   SHELL_STARTUP_FILES=NONE
   CORE_DUMPS=DISABLED
   NETWORK=DENIED
   ACTIVE_COPY_PROCESSES_MAX=1
   COPY_LAUNCHES_MAX=2
   ATTEMPT_WALL_TIME_LIMIT_SECONDS=30
   COPY_MEMORY_LIMIT_MIB=128
   OUTPUT_FILE_SIZE_LIMIT_BYTES=65536
   ```

   The launcher must receive this environment directly. A shell command that clears variables after an unreviewed startup is insufficient.

   The launcher descriptor contract is:

   - FD `0` is closed.
   - FDs `1` and `2` are approved observer pipes.
   - FD `3` holds the accepted source input read-only.
   - FD `4` holds the accepted companion input read-only.
   - FD `5` holds the verified `/tmp` directory.
   - FD `6` holds the newly created candidate directory.
   - FD `7` holds only the output currently being written.
   - FD `8`, if used for a child pidfd, is restricted to that launched child.
   - Other inherited descriptors are closed.

   Each copy child receives only the input duplicated to FD `0`, its new output duplicated to FD `1`, and the approved diagnostic pipe at FD `2`. Loader descriptors may read only approved dependencies.

   The ordered operations would be:

   1. Verify the grant, input-custody acceptance, dependencies, isolation, observer readiness and fresh parent observations.
   2. Record consumption of the one-use attempt entitlement through the approved evidence channel before the first creation. Missing or ambiguous acknowledgment blocks creation.
   3. Create the candidate with `mkdirat` relative to FD `5`, mode `0700`, without recursive parent creation. Any existing entry stops the attempt.
   4. Open that directory with directory and no-follow requirements. Independently bind FD `6` to the newly created directory and verify its ownership and mode.
   5. Create `qualification_authority.py` relative to FD `6` using `O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC`, mode `0400`. Verify that the new object is a regular file, has one link and has the approved ownership.
   6. Launch exactly:

      ```text
      /usr/lib/cargo/bin/coreutils/dd bs=65536 status=none
      ```

      For this invocation, FD `0` is the accepted 59,880-byte source input at offset zero. FD `1` is its newly created output. There is no `if=` or `of=` pathname, conversion or output redirection.

   7. Require observed exit status zero. Synchronize the output, check its length and record its descriptor identity. Close the output without reopening it for writing.
   8. Create `source_review_packet.md` with the same exclusive flags and mode. Launch the identical command once, with the accepted 26,302-byte companion input at FD `0` and its new output at FD `1`.
   9. Require exit status zero, synchronize, check length and close that output.
   10. Set only the new candidate directory to mode `0500` through its held descriptor. Synchronize directory and parent metadata. Record final observations and end writer access.

   Every operation requires its stated guard and an observed successful result. A later grant must bind the exact launcher executable, implementation, dependencies and invocation that perform these operations. Those identities are currently missing.

   The complete proposed filesystem effect allowance is:

   - Create `/tmp/symphony-gate-a-authority-candidate-r1`.
   - Create its `qualification_authority.py`.
   - Create its `source_review_packet.md`.
   - Modify `/tmp` only through that directory entry and the associated directory metadata.
   - Modify the new directory through its two entries, associated metadata and its final mode change.
   - Write the two new files' contents and associated metadata.

   No other filesystem object may be created or modified under this allowance. It permits no temporary files, local logs, manifests, scripts, caches, lockfiles, core files, source revisions, renames, hardlinks or repository writes.

   The allowance also includes the declared transient descriptors, observer pipes, buffers and two sequential copy processes. Any persisted observer records need their own exact object names and write authority in the later evidence allowance. No unspecified logging service is implicitly approved.

   On interruption, the authorized launcher may stop its identified active child, close its descriptors and report the observed outcome through approved channels. Partial files and the directory remain in their observed state. No deletion, truncation, chmod repair, resumed copy, repeated launch or cleanup follows automatically.

   Two-file creation is not an atomic transaction. A failure can leave one complete file, a partial file or an empty directory. All such outcomes remain unaccepted.

5. Independent verification

   A separately appointed reviewer must conduct its own observations after writer access ends. It must obtain the original inputs and input-custody acceptance independently of the producer's completion report.

   With the candidate directory independently identified as its working directory, the proposed read-only checks include:

   ```text
   /usr/bin/wc --bytes -- qualification_authority.py source_review_packet.md

   /usr/bin/sha256sum --binary -- qualification_authority.py source_review_packet.md

   /usr/bin/stat --format='%n|%F|%d|%i|%h|%u|%g|%a|%s|%y|%z' -- . qualification_authority.py source_review_packet.md
   ```

   Whole-file comparisons would use:

   ```text
   /usr/bin/cmp -- /proc/self/fd/3 qualification_authority.py

   /usr/bin/cmp -- /proc/self/fd/4 source_review_packet.md
   ```

   Here, reviewer FDs `3` and `4` refer to independently obtained, accepted input objects. The `/proc` references are deliberate descriptor references. They do not authorize following arbitrary input symlinks.

   The installed comparison utility was observed as:

   ```ini
   CMP=/usr/bin/cmp
   CMP_VERSION=GNU_diffutils_3.12
   CMP_BYTES=43592
   CMP_SHA256=82b923f0f12706950d696fb63fe3d8d8a4d2e559ec2a8a44f6c97ed2c56de44e
   ```

   Its dependencies and those of all verification tools require approval before use in B1 verification.

   The reviewer must establish all of the following:

   - Exact individual lengths of `59880` and `26302`.
   - Exact supplied SHA-256 hashes.
   - Entire-file equality with the accepted raw attachments.
   - Equality with the independently identified export slices.
   - Correct final LF boundaries.
   - Regular-file type, link count one, approved UID/GID and mode `0400`.
   - Candidate-directory ownership and final mode `0500`.
   - Agreement between held-descriptor identities and directory entries.
   - Continuity of custody before, during and after copying.
   - Compliance with the complete effect allowance.
   - Complete launch, exit, interruption and evidence-channel observations.

   The reviewer must record any limitations of its observation coverage. Absence of an observed violation does not prove that unobserved effects were impossible.

   Acceptance requires a separate authenticated B1 verification decision bound to the attempt, grant, input acceptance, resulting object identities and evidence. A producer report, matching hashes alone or exit status zero cannot issue that decision.

6. Durability and future retrieval

   The proposed location is staging. `/tmp` is currently `tmpfs`; synchronization there does not establish survival across reboot or power loss.

   A successful B1 staging decision would establish only that the reviewed bytes were independently verified at the identified staging objects under the recorded custody. It would not establish a durable archive or operational qualification.

   Propose this future canonical evidence-index path:

   ```text
   docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_06_B1_EVIDENCE_INDEX.md
   ```

   It does not exist by authority of this packet. Future creation requires separate authorization.

   The index should bind:

   - The accepted governing commit, tree and exact R2 plan blob.
   - All three B0 byte identities and the exact extraction boundaries.
   - The original independent B0 verdict, finding records and closure decisions for F01–F04, R01–R03, N01–N03, E01 and E02.
   - The reviewed B1 packet and independent planning decision.
   - The human B1 grant, issuer, attempt identifier, validity and one-use consumption record.
   - Input custody, writer/dependency identities, resulting file identities and complete execution evidence.
   - The independent B1 verification decision.
   - Any adverse disposition or later challenge.
   - Durable object identifiers, retention owner, retention policy and independently observed retrieval results.
   - Explicit nonauthorization of operational use, Gate A preparation or execution, Gate B, Gate 2 and AUTH_07 consumption.

   Recommend a separately authorized durable evidence bundle that preserves the original export, both payloads and original review records. The archive decision must select the actual storage system, object versions, access controls, retention and recovery arrangements. An index or attachment link alone does not establish preservation.

   Before declaring an archive established, a separate reviewer must retrieve its objects through the intended future access route and repeat exact-byte verification.

   GitHub cross-references should use commit-pinned links to the accepted plan and future index. The hardening ledger should receive only a separately authorized, narrowly scoped index entry. Any documentation PR and automatically triggered CI need their own authorization.

   The verified existing Plane evidence owner is SGOV-2:

   ```ini
   PLANE_WORKSPACE=symphony-development
   PLANE_PROJECT=f7317505-bc78-42ae-a902-1e3f0346bcff
   PLANE_WORK_ITEM=079ea0ea-dc3f-4a23-ac01-0a3e75e8c03b
   ```

   Recommend cross-referencing that item unless later authority selects another existing record. Do not invent an ACQ-EXEC-06 issue or create a duplicate. Any Plane comment, attachment, link or state change requires separate authorization.

7. Lifecycle

   These are proposed B1 states, not changes to a tracker.

   - **`PLANNING`.** Read-only authority permits this packet. No creation entitlement exists.
   - **`PLAN_REVIEW`.** An independent reviewer examines the exact packet. Submission grants no writes.
   - **`PLAN_ACCEPTED_BLOCKED`.** Planning is accepted, but one or more grant prerequisites remain unresolved.
   - **`GRANT_ISSUED`.** An authenticated human decision binds the accepted packet, exact inputs, destination, principals, mechanisms, dependencies, effects, limits and evidence channels. Every pre-write dependency must be resolved.
   - **`ATTEMPT_CONSUMED`.** The independent evidence owner confirms one-use entitlement consumption before candidate creation. Ambiguous consumption cannot restore the entitlement.
   - **`WRITING`.** Only the guarded operations in section 4 are permitted.
   - **`PRODUCER_COMPLETE`.** The ordered procedure ended successfully and writer access ended. The candidate remains unaccepted.
   - **`INDEPENDENT_REVIEW`.** The separate reviewer performs the checks in section 5 under continuous custody.
   - **`STAGING_VERIFIED`.** A positive independent decision accepts the exact staged objects. This is terminal for this materialization attempt and grants no archive transfer or operational use.

   Adverse terminal states are:

   - **`FAILED`.** A determinate command, identity, permission, hash, equality or effect failure occurred.
   - **`INCOMPLETE`.** The attempt or required evidence did not finish, while known effects remain determinate.
   - **`UNCERTAIN`.** Effects, custody, identity, entitlement consumption or evidence acknowledgment are ambiguous.
   - **`REJECTED`.** Independent review declines acceptance.
   - **`CANCELLED` or `REVOKED`.** Applicable authority ends or is withdrawn. A live writer must stop through its preauthorized stopping mechanism.
   - **`EXPIRED`.** The grant's validity ends without an authorized successful disposition.

   Each transition must record the attempt, prior state, guard evidence, actor, authority reference, time and acknowledgment. Required records must reach the approved evidence channel before the next effect.

   Any adverse terminal stops forward progress. Retained objects receive only authorized observation and stopping actions. There is no automatic overwrite, repair, cleanup, retry, reuse or promotion.

   A future attempt requires a new identifier, fresh observations and new explicit authority. It cannot reuse a failed candidate or credit the failed attempt's partial results. If the proposed path has become occupied, resolving that condition requires a separate human disposition.

   Durability and publication are subsequent, separately authorized lifecycles. Neither follows automatically from `STAGING_VERIFIED`.

---

The separate unresolved-requirements register follows. “Read-only” identifies facts that can be investigated without candidate creation. It does not claim that the missing inputs or access are already available.

- **R01. Original input access remains missing.** The raw export and two payload attachments have not been supplied as accessible objects in this runtime. Their actual attachment references, backing objects and custodial lineage require read-only verification once provided. Any ingress writes need an explicit effect allowance.

- **R02. Original B0 review records remain missing.** Recover the independent verdict and original finding and closure records. Your stated accepted entry remains binding; this packet does not independently authenticate the absent originals.

- **R03. Exact extraction boundaries remain unknown.** Once the export is accessible, independently establish numeric byte offsets, unique fence boundaries, final LF inclusion and whole-slice equality. No offset may be guessed.

- **R04. The writer mechanism is unidentified.** Select an existing mechanism capable of descriptor-relative exclusive creation, controlled FD inheritance, clean execution, enforcement, stopping and observation. Its exact invocation and implementation need review. Preparing or qualifying a new helper would require separate authority.

- **R05. The immutable dependency closure is incomplete.** Current utility identities and shared-library hashes were observed read-only. The complete launcher, loader, library, verifier and runtime-data manifest, immutable backing identities and protection against replacement still require independent approval.

- **R06. The human principals require appointment.** Name the issuer, writer, input custodian, observer, independent reviewer and evidence owner. Confirm numeric writer ownership and the reviewer's access method without weakening candidate permissions.

- **R07. Destination and isolation require approval.** Approve the exact staging path and UID/GID proposal. Select the enforcement mechanism, credential and supplementary-group restrictions, mount exposure, concurrent-writer exclusion and all setup effects. None is assumed available.

- **R08. Parent and runtime observations require renewal.** Current `/tmp` observations are available. The independent observer must repeat them immediately before creation and bind them to the selected runtime. Later ref changes must not silently replace the accepted governing baseline.

- **R09. Evidence endpoints and effects are unspecified.** Identify exact receipt, diagnostic and decision destinations, owners, limits, acknowledgment behavior and persisted objects. Resolve automatic transport, audit and session logging effects. No unspecified log writes may enter the grant.

- **R10. One-use authorization mechanics are unresolved.** The grant must identify the attempt, validity period, consumption record and acknowledgment mechanism. A failure or ambiguous consumption must prohibit launch or relaunch.

- **R11. The exact B1 planning-review target needs binding.** Independent review must identify the actual packet it reviewed. A later export's length and hash must be measured from that export; they cannot be invented from this conversational response.

- **R12. Final execution and file observations necessarily come later.** Actual directory/file inodes, ownership, modes, lengths, hashes, copy exits, extraction equality and custody continuity can only be established during and after an authorized attempt. They are acceptance requirements. Before grant issuance, the responsible observer and exact observation method must already be approved.

- **R13. Durable preservation requires a separate decision.** Select the archive, retention owner, object versions, recovery procedure and retrieval verification. This does not block an explicitly limited staging grant, but it blocks any durable-archive claim.

- **R14. Publication requires separate authority.** GitHub index creation, ledger changes, PR/CI activity and Plane updates remain outside B1 materialization. Their exact scope and destination records must be authorized before publication.

- **R15. The B1 writing grant has not been issued.** No planning acceptance, local tool discovery or resolution of another register item can substitute for the authenticated human decision.

```ini
B1_R0_PACKET=BLOCKED
B0_SOURCE_REVISION_AUTHORIZED=NO
B0_EXACT_BYTES_FROZEN=NO
B1_MATERIALIZATION_GRANT=NOT_ISSUED
B1_PERSISTENCE=NOT_AUTHORIZED
DURABLE_ARCHIVE=NOT_ESTABLISHED
GITHUB_PLANE_EVIDENCE_INDEX=NOT_PUBLISHED
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
```