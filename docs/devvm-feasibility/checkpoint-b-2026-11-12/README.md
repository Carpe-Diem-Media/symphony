# Devvm Checkpoint B evidence for independent review

Status: author-produced evidence, submitted for independent review. This packet is non-authoritative.
It does not amend the Master Roadmap, enroll a worker, accept an integration, or authorize a later phase.
Governing authority remains the [V4.1 Master Roadmap](../../symphony-hardening-playbook-v4.1/V4_1_MASTER_ROADMAP.md).

## Result and scope

One operator-authorized staging run on 2026-11-12 authenticated and privately extracted Devvm v0.1.0
and Lima v2.2.1. It exited 0 and reported STAGING_COMPLETE_BINARIES_NOT_EXECUTED.
Downloaded binaries were never invoked. No image build or VM operation occurred.
Checkpoint C0 and Checkpoint C1 remain HOLD.

[CHECKPOINT_B_RESULTS.ini](CHECKPOINT_B_RESULTS.ini) is the historical staging result.
Its source/GitHub/no-change fields describe that run, before this separately authorized documentation PR.
[RESEARCH_AND_GATES.md](RESEARCH_AND_GATES.md) explains the unresolved bootstrap boundary.

## Start the review here

- [Execution, timestamps and exact script hashes](evidence/independent-review/stage-process.json).
- [Reviewed R1 script](evidence/independent-review/reviewed-r1.sh) and
  [executed script](evidence/independent-review/executed-checkpoint-b.sh).
  The only change is two replacements of STAGED_NOT_EXECUTED with
  STAGING_COMPLETE_BINARIES_NOT_EXECUTED.
- [Eight synthetic crypto cases and their output](evidence/independent-review/synthetic-tests.json).
  These tests alone do not authenticate release files.
- [Actual release signature, hash, payload and metadata verification](evidence/independent-review/verification.json).
- [Devvm archive members](evidence/independent-review/devvm-actual-archive-members.json) and
  [Lima archive members](evidence/independent-review/lima-actual-archive-members.json).
- [Minisign result](evidence/devvm-signature.json),
  [OpenPGP machine-readable result](evidence/lima-signature.stdout), and
  [OpenPGP diagnostic output](evidence/lima-signature.stderr).
- [Supplemental audit failures and permission correction](evidence/independent-review/supplemental-evidence-mode-correction.json).

The scripts are historical evidence stored as non-executable text. Do not run their staging mode during review.
No downloaded binary archive, extracted executable, authentication file or private key is included.

## Observed results

The staging run lasted from 05:25:09 to 05:25:24 UTC and ran once.
All seven approved downloads matched the authenticated expected SHA-256 values.
Both Devvm Minisign signatures passed. Lima OpenPGP verification returned exit 0 with signer
C020EA876CE4E06C7AB95AEF49524C6F9F638F1A.

The Devvm archive contained four regular files. Lima contained 198 regular files, 14 directories
and one relative symlink. The verification pass compared every extracted regular file with its archive payload.
Extracted directories were 0700, files 0600 or 0700, and ownership was UID 1000.
Lima's share/doc/lima/templates link resolved to share/lima/templates within its own extraction root.

Five supplemental audit files initially inherited mode 0664. Three failed audit/check attempts are
recorded, including an incorrect 0644 assumption. Staging was not rerun. The final retained
inventory covered 289 records and passed verification.

## Owner decision on correction provenance

The owner decision is the user message titled `Owner Decision — SYMPHONY_DEVVM_05_R1`, position 48
in `t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/b0edc717-14bb-4f31-88ec-19d5affde10b`,
recorded at `2026-11-12T06:56:45.510Z`. The approving authority is the user identifying the message
as the owner decision. It states `APPROVE LIMITED HISTORICAL-PROVENANCE EXCEPTION` and
`I accept a narrowly scoped evidence exception for the five supplemental Checkpoint B audit files whose pre-correction SHA-256 values were not recorded.`
Its scope and exclusions are stated below; it does not establish any other acceptance or authority.

The independent investigator recovered the original staging-session activity. At
position 323, an attempt expecting mode 0644 failed before its permission-changing loop. At position
325, a scan recorded these five files as mode 0664 and owned by UID 1000. At position 327, the
recorded Python operation checked each path's type, ownership and mode, called `Path.chmod(0o600)`,
and checked the resulting modes:

- `evidence/independent-review/devvm-actual-archive-members.json`
- `evidence/independent-review/gpgv.stderr`
- `evidence/independent-review/gpgv.stdout`
- `evidence/independent-review/lima-actual-archive-members.json`
- `evidence/independent-review/verification.json`

These paths are relative to `/home/jcschoeman96/sdv02`. The operation printed
`{"audit_files_hardened": 5, "staged_payload_changes": 0}` and its activity item was marked
completed at `2026-11-12T05:30:06.210Z`. The correction record timestamps itself
`2026-11-12T05:30:06.176123+00:00`. The activity view did not separately capture a numeric exit
status or effective UID. The guard used `os.getuid()` and the preceding scan reported UID 1000;
neither is a separate effective-UID record.

No pre-correction content hashes were found for these files. Their current bytes and permissions
match the independently verified final inventory, but historical byte equality cannot be proven.
The owner's exception accepts that uncertainty for the five supplemental files only; it does not
claim the missing evidence was recovered. It does not waive release signature, archive hash,
extracted payload, final inventory or artifact-preservation requirements. Full-payload preservation
and an independently verified backup remain mandatory before formal Checkpoint B acceptance.
The exception does not authorize C0, C1, a merge or changes to F09 or P08 authority.

The original staging evidence remains unchanged. The original session activity is available at
`t3-thread://v2/fdfd1f03-53cf-41e7-8d37-6f5313c72d55/5fd373fe-43e0-4811-8eb1-bcc007cbb219`.
The recorded operation did not target the staged payloads or original staging inventory. Current
payload integrity was independently checked, but the records do not prove the absence of every
unrecorded historical host action.

## Source and evidence identities

The staging entry main was 2ba7cb5f49399cbe41ea527af5abcdac0dda1281,
tree 75d6df5e972bd253b272974dd8adec6452f5e00d.
The local checkout used for source inspection remained
ea696d1453dfef81c869cdc4fbda77bfa135a416,
tree d854d294f83124bd2ba4351dfd30fa7da3af6cd9.
The intervening main change affected AGENTS.md only.
See [source-baseline.json](evidence/independent-review/source-baseline.json).

The executed shell script SHA-256 is
e3963737564282b6c0265c380a0609e1121704ee159ef46687511feb12860863.
The reviewed R1 shell script SHA-256 is
7bb1f92021f84523122edc216715c37e2094a32b92c9bdf2fd31428786e3727b.
The final host-retained inventory SHA-256 is
840c380bddfa4c80bfbd5b70c9820a178a4c66046389d1568c531c209c489387.

[EVIDENCE_SELECTION.json](EVIDENCE_SELECTION.json) maps each copied file to its retained source and hash.
Copied files are byte-identical. This is a selected public proof packet, not a complete copy of the
host directory. Original inventories include hashes for omitted payloads and local-only records.

The complete staging directory remains at /home/jcschoeman96/sdv02 and was not modified by publication.
The review packet also has a verified durable copy outside the disposable worktree.
Its path is recorded in [PUBLICATION.json](PUBLICATION.json).
A pushed Git commit supplies an off-host copy of the published packet.
Independent backup of the full locally staged software remains unverified.

Git preserves text bytes and executable flags, not the original host UID or private permission bits.
The Unix metadata in the evidence describes the original host files, not a reviewer's Git checkout.

## Safe offline integrity checks

Run from this packet directory:

~~~bash
sha256sum --check SHA256SUMS
(cd evidence && sha256sum --check inventory.sha256 checkpoint-b-inventory.sha256)
~~~

These commands verify packet bytes and the two retained inventory documents.
They do not verify omitted host files or rerun release staging.

## Independent review checklist

- [ ] Verify the packet checksum manifest and copied-source mappings.
- [ ] Confirm the exact reviewed/executed script difference and the eight synthetic cases.
- [ ] Review the signed release manifests, trusted keys and signer fingerprint.
- [ ] Check actual archive inventories against both validation plans.
- [ ] Review the recorded payload comparison, ownership, modes and internal symlink.
- [ ] Review the supplemental evidence failures and corrected final inventory.
- [ ] Preserve the distinction between staging success and runtime containment.
- [ ] Keep C0/C1, remote admission, F09, P08 and programme acceptance outside this decision.

## Validation limits and artifact lifecycle

The packet was checked for byte integrity, JSON validity, script syntax, recorded outcomes, local links
and publication-sensitive material. The existing PR-body checker was run directly with installed Elixir.
The complete make -C elixir all gate was not run: this checkout has no project dependencies and that
target begins with dependency acquisition, which remains outside the authorized installation boundary.
No runtime or workflow code changed. CI and exact-candidate independent review remain required.

The host actor creates a packet from verified owned source files, preserves it in durable storage,
and marks its bytes VERIFIED only after matching inventories. Publishing a branch and PR makes it
SUBMITTED, not ACCEPTED. A trusted owner must decide acceptance separately.
Hash or preservation failures stop publication. Retained source and packet files are never
automatically deleted; removal requires a separate owner-approved cleanup decision.
