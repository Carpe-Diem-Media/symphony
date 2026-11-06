# H-100 → Gate 2 — Evidence and Authority Checkpoint (2026-11-06)

**Checkpoint status:** Historical evidence reconciliation with explicit gaps; not a programme acceptance, execution grant, or proof qualification.
**Publication condition:** A branch or PR is not an accepted protected-main publication; a separately authorized human merge and exact post-merge verification are required.
**Scope:** Historical reconstruction and evidence index only. **No tests, implementation, resource operations, provider use, P08 qualification, H-100 execution, Gate 2 activation, or new authority**.
**Repository:** `JCSchoeman96/symphony`.
**Pinned review baseline:** `ced5239092ac368c5498644b2710ce0b19a294c5` / tree `126aa309502087acb6a5084a197159c142de63e5`.

## 1. Source provenance and epistemic limits

This checkpoint incorporates the **complete supplied text export** `Gate 2 Evidence.txt` as a reformatted investigator report in section 5, plus the scope interpretation and navigation here. The export was independently measured in the reviewer container at **41,309 UTF-8 bytes**, SHA-256 `581808ed5b9bd0048d76cf13b6007b8a9fb22058bcc6cb0a896921dc6e8bf40d`. The investigator named an original workstation Markdown at `/tmp/symphony-h100-gate2-reconciliation-2026-11-06.md`; **the exact original Markdown bytes were not supplied or independently compared with this export**. Do not assert byte identity between them.

The agent investigated the host read-only and reported `RECONCILIATION=INCOMPLETE_WITH_EXPLICIT_GAPS`. **Editorial correction to the reproduced export:** in the frozen R3 file inventory, `tests/init.py` was corrected to the authority-attested `tests/__init__.py` without changing its 75-byte size or SHA-256; the inventory line identifies Plane decision `3d925f87-6095-46a3-94f8-b1f3e33995d2`. This is an explicitly documented transcription correction, not a claim that the supplied export already contained the accurate path. Repository facts and scoped governance decisions are corroborated by the current protected GitHub history and the linked accepted records. Local workstation archives, root-protected directories, and claimed independent local reproductions **have not been re-executed or directly inspected by the author of this checkpoint**; their results are attributed to the supplied investigator's report, with exact hashes and paths retained for later inspection.

These evidence classes must not be conflated: `MERGED_AND_ACCEPTED` (exact scoped source changes), `INDEPENDENTLY_QUALIFIED_FOR_EXACT_PROFILE` (bounded historical fixture), `DESIGN_OR_CONTRACT_ACCEPTED_ONLY`, `DIAGNOSTIC_EVIDENCE_ONLY`, `HISTORICAL_FAILED_OR_STOPPED`, and `UNVERIFIED_OR_MISSING`. A checked PR, local fixture pass, or narrative does not imply successful H-100 or Gate 2 qualification.

## 2. Current authoritative interpretation

| Subject | Established scope | Not established |
|---|---|---|
| H-080B Linux isolation | Accepted for its exact earlier Linux/Codex 0.159.3 profile | Proof of the future patched Gate 2 app-server and host profile |
| H-120A / H-100 | H-120A accepted; H-100 historically authorised/active as a **programme** proof | A completed, independently accepted H-100 real lifecycle |
| H-100 application corrections | PRs [#52](https://github.com/JCSchoeman96/symphony/pull/52) and [#53](https://github.com/JCSchoeman96/symphony/pull/53) merged | H-100 provider response ambiguity or validated Done proof |
| Historical H-100 experiments | PRs [#54](https://github.com/JCSchoeman96/symphony/pull/54)–[#59](https://github.com/JCSchoeman96/symphony/pull/59) preserved as open branches and candidate evidence | Their integration into current `main`; any blanket approval to merge |
| Rust/systemd workstation proof | Investigator records a narrowly independently qualified v3 fixture | Production broker, completed firewall/lease controls or reboot reconciliation |
| Gate 2 inventory | G2-INV-2.1 freeze accepted: **115 entries, 26 obligations, 14 lifecycles, 19 bearer channels, 13 transfer claims** | 26 executed and accepted obligation results |
| SIWC subscription contract | Host-owned OAuth registration/refresh, one-use access materialization to Codex, Responses route selected | Real enrollment/refresh proof and all bearer nondisclosure channels |
| Gate 2 implementation | Dormant P01 and P08-T02 pure projections merged under scoped decisions | Enforced complete Gate 2 runtime, P09 qualification or activation |
| ACQ-EXEC-05 Gate A | R2 qualification **plan** accepted; R0 preparation **planning content** accepted | Gate A controls built/qualified, T01–T11 executed or independently accepted |
| ACQ-EXEC-05 Gate B | T12–T20 defined for a separately qualified successor | Authorization or execution; frozen R3 cannot stand in for the successor |

**Separate authorization scopes:** The accepted V4.1 programme projection retains `H-100=AUTHORIZED_ACTIVE_NOT_ACCEPTED` under `MG-2026-10-18-H120A-ACCEPT-H100-AUTH-01`. The later Gate 2 task lock states `H100_EXECUTION_AUTHORIZED=NO`. The latter does not revoke the historical programme decision, and the former does not authorize H-100 execution **inside the Gate 2 task**.

```ini
CHECKPOINT_AUTHORITY=NONE
H100_PROGRAMME_STATUS=AUTHORIZED_ACTIVE_NOT_ACCEPTED
H100_COMPLETED_LIVE_PROOF=NOT_ACCEPTED
GATE2_INVENTORY_FREEZE=ACCEPTED
GATE2_REFERENCE_TOPOLOGY=ACCEPTED_DESIGN_ONLY
GATE2_EXECUTABLE_QUALIFICATION=INCOMPLETE
GATE_A_R0=HUMAN_ACCEPTED_PLANNING_CONTENT_ONLY
GATE_A_PREPARATION=NOT_AUTHORIZED
GATE_A_CONTROL_QUALIFICATION=NOT_AUTHORIZED
GATE_A_EXECUTION=NOT_AUTHORIZED
GATE_B_EXECUTION=BLOCKED
P08_FULL_ACCEPTANCE=NOT_GRANTED
GATE2_ACTIVATION=NOT_AUTHORIZED
AUTH_07=SUSPENDED_UNCONSUMED
H110=NOT_AUTHORIZED
H120B=NOT_AUTHORIZED
OLD_H100_PRS_54_TO_59=OPEN_HISTORICAL_NO_MERGE_RECOMMENDATION
ORIGINAL_A1_RECORD=NOT_RECOVERED
ROOT_PROTECTED_DIAGNOSTIC_DIRS=12_NOT_INSPECTED
RECONCILIATION=INCOMPLETE_WITH_EXPLICIT_GAPS
```

## 3. Why the transition occurred

The October H-100 work established working application-side correlation and some bounded fixtures but did **not** establish safe real indeterminate-response handling or a complete lifecycle. Subsequent host-level experiments encountered real Linux authority and networking limits: user/network namespace ownership mismatch during nftables inspection, systemd user-start failures, incomplete low-privilege process identity observation, and an unproven relay reply-path restriction. Later fixed Rust/systemd and UID/network experiments improved the design evidence only for specific profiles. The November Gate 2 architecture therefore deliberately selected a more explicit trusted host boundary and SIWC credential-custody model; it did not retrospectively qualify the incomplete October attempts.

**Do not automatically merge or abandon PRs #54–#59.** They are neither current proof nor proven wholly obsolete. Any future reuse requires per-file applicability, exact diff, candidate lineage and CI/authority review. Historical checks on their old bases do not establish present-day merge readiness.

## 4. Next bounded decision and publication requirements

The investigator's recommended next **technical** milestone is an independently reviewed, **read-only Gate 1 authorization-readiness assessment** for ACQ-EXEC-05 R0. Bind the located original R0 Markdown identity, the frozen five-file R3 identities, and the accepted inert preparation evidence; classify Q01–Q16 and identify the smallest missing supervisor/collector/evidence-control contract requiring a future separately authenticated human grant. This recommendation does **not** itself grant any preparation, source execution or qualification.

Before a further H-100 revival or final Gate 2 acceptance claim, distinguish the remaining executable proofs: qualified Gate A and successor Gate B, exact Rust toolchain/install identity, holder/tool/process/network separation, 19 synthetic-secret bearer-channel controls, real SIWC registration/refresh/Responses restrictions, and end-to-end Plane→Symphony→Codex→GitHub→human merge→verified Done→downstream release.

For this **documentation-only checkpoint**, independently inspect the exact PR diff and CI, confirm the governing reference pins and keep the old roadmap, machine projections, ledger decision history, runtime and workflows unchanged. A future human merge of this document makes only a reviewable audit checkpoint available in `main`; it does **not** close any proof gap or authorize further phases.

### Governing navigation

- [V4.1 Master Roadmap](V4_1_MASTER_ROADMAP.md) — governing programme law.
- [Unified Execution Roadmap](../SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md) — H-100, H-110, H-120B proof requirements.
- [Current Hardening Status Ledger](HARDENING_STATUS_LEDGER.md) — derivative status and historical acceptance.
- [Post-H120A / Pre-H100 materialization](POST-H120A_PRE-H100_GOVERNANCE_MATERIALIZATION.md) — H-100 programme authorization.
- [Gate 2 inventory freeze acceptance](GATE2_INVENTORY_FREEZE_ACCEPTANCE_2026-11-02.md) and [immutable packet](GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json) — selected architecture and obligations.
- [Canonical Gate 2 implementation plan](../superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md) — accepted design, not execution authority.
- [P08 technical specification](GATE2_P08_HOST_EVIDENCE_SPEC.md) and [implementation plan](../superpowers/plans/2026-11-04-p08-host-evidence-implementation-plan.md) — accepted v0.7 documents with historical PROPOSED markers.
- [ACQ-EXEC-05 R2 acceptance record](ACQ_EXEC_05_R2_MASTER_GATE_PLAN_ACCEPTANCE_2026-11-06.md) — qualification plan only.
- Plane `SGOV-2` comment `224c2e4c-5842-414c-a7c8-836484f923b3` — R0 human planning-content acceptance only.

## 5. Full historical evidence reconciliation (investigator's report)

The section below retains the supplied investigator's detailed chronology, candidate identities, local artifacts, qualification classifications, gaps and all 26 obligation names. Headings and bullets were normalized for repository readability; this is **not** a claim that the original workstation `.md` was byte-for-byte published.

### Source report: Symphony H-100 to Gate 2 evidence reconciliation

Read-only investigation, 6 November 2026. No tests, Codex/provider workloads, privileged operations, credential reads, repository changes or tracker mutations were performed. Historical commands below are evidence, not instructions to execute them. File hashing and Git/API reads were inspection operations.

#### Finding and authority baseline

Current executable Gate 2 is not qualified. H-100 has no accepted end-to-end lifecycle proof. Existing work includes accepted application corrections, accepted dormant P01 and P08-T02 code, useful host experiments, an accepted P08 document contract, a source-only acquisition executor, and accepted qualification planning. These have different scopes.

Live GitHub independently confirms protected main ced5239092ac368c5498644b2710ce0b19a294c5, tree 126aa309502087acb6a5084a197159c142de63e5, with 423 recursive entries and truncated=false. This matches the supplied baseline. PR #68 merged at 2026-11-06T07:18:32Z. Its parents are 1c045ac215afee47e94d566bf3f3baa0751beb9d and 6fbd61e1ef4576978edbcdc43e6b1ad68d3915cd. Existing push CI 42180019882 reports success on that main SHA. Required contexts are make-all and validate-pr-description, GitHub Actions app 15368. This is repository CI evidence, not Gate 2 native/subscription qualification.

The local main checkout remains 1c045ac215afee47e94d566bf3f3baa0751beb9d, tree 4f1a87340ce0b93801620be4f602dc1cef0e92f8. It has a modified ledger and untracked plans/evidence. The two locally untracked ACQ-EXEC-05 documents are nevertheless committed on live main through PR #68. I read current authority through exact Git objects rather than treating local status as publication status.

Authority order follows elixir/AGENTS.md: Master Roadmap, Unified Roadmap, applicable accepted governance and scoped decisions. docs/superpowers/README.md denies automatic authority to planning files. There is no repository-root AGENTS.md. The user's read-only scope overrides generic instructions to run validation, branch or update Plane. No database-dependent work was needed.

Plane citations below mean project f7317505-bc78-42ae-a902-1e3f0346bcff, SGOV-2, item 079ea0ea-dc3f-4a23-ac01-0a3e75e8c03b, and the exact comment UUID, unless another item is stated. All 74 comments were retrieved, with next_page_results=false; the latest decision was 224c2e4c-5842-414c-a7c8-836484f923b3. An older ticket-body projection still says P01 acceptance is pending. Later exact decisions supersede that projection within their scopes.

### 1. Chronology and actual H-100 progress

- 18 October, authorization.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. MG-2026-10-18-H120A-ACCEPT-H100-AUTH-01 accepted H-120A and authorized the disposable H-100 proof. The Master Roadmap requires Planning through review/change-request/review, exact human merge, verified closure, fresh Plane Done reread and downstream satisfaction, plus cancellation, failure, indeterminate outcome and authority negatives. Authorization is not a result.
- First attempt.HISTORICAL_FAILED_OR_STOPPED. The attempt-2 manifest records ABORTED_PREFLIGHT and excludes attempt 1 from H-100 evidence. The expected original 2026-10-18-h100-real-disposable-live-proof.md, its approval identity and exact candidate were not recovered. A1 details are UNVERIFIED_OR_MISSING; no reconstructed plan is presented as its original bytes.
- 19 October, A2 correction.MERGED_AND_ACCEPTED. PR #52 integrated durable request identity and bounded dispatch-witness acknowledgement. The implementation record explicitly limits this to application handoff to Finch. It proves neither Plane receipt/commit nor encrypted-response suppression. October 22's A3 requalification record identifies A2 as a historical superseded runtime candidate.
- 22 October, A3 correction and stop.MERGED_AND_ACCEPTED. PR #53 accepts a complete Plane terminal page retaining a cursor. A3 acceptance is recorded in the retained requalification plan. Separately, HISTORICAL_FAILED_OR_STOPPED applies to the A3 live-proof plan's H100_INDETERMINATE_PROOF_NOT_SAFELY_EXECUTABLE. Acknowledged request handoff was insufficient to identify and suppress the exact encrypted response. A runtime preflight also failed SSH host verification because its SSH origin had no runtime host trust. The plan selected credential-free HTTPS observation; it did not prove that later steps ran.
- 22–25 October, experimental stack.DIAGNOSTIC_EVIDENCE_ONLY. PRs #54–#59 added dormant A4 transport, relation normalization, runtime-principal enforcement, relation-epoch/GitHub checkout evidence, security dependency changes and the host-relay qualification boundary. Q1–Q18 evidence on #54 reports a local TLS response-withholding fixture, no resubmission, identity/replay negatives, cleanup and a credential-free verified Plane TLS handshake. It is not a real Plane mutation lifecycle. An earlier duplicate request_fun fixture selected normal Req transport and returned a 404-class result against a synthetic path; that qualification was invalidated and restarted after a guard. Provider-side state change was not established.
- 25 October, two disposable resource preparations.DIAGNOSTIC_EVIDENCE_ONLY. The retained manifests record resource creation/read access and candidate CI. Attempt2's two items began Planning. The separate debecc32 item was created directly in Merging. A GitHub App installation-binding 403 stopped that preparation; later access qualification passed. Those records explicitly say H-100 was not executed. Live facts now show debecc32 PR #1 was subsequently merged by the owner, but its Plane item remains Merging. A disposable merge alone does not establish Symphony closure, validated Done or dependency release.
- 26–28 October, host qualification failures.HISTORICAL_FAILED_OR_STOPPED. A staged archive digest mismatch stopped the first install; the next install stopped on missing h100-egress 993:979. After separately authorized prerequisite setup and installation, Stage A failed closed. A targeted diagnosis measured nft list ruleset EPERM before mutation: CAP_NET_ADMIN existed in the service's private user namespace, while the network namespace was owned by the host user namespace. A delegated Architecture E launch then failed 217/USER. A no-delegation control started but retained the ownership mismatch. Later diagnostics rejected the proposed AppArmor explanation; the PrivatePIDs-only delta failed, without identifying the exact denied kernel operation.
- 27–28 October, r3/r4/r5 distinction.DIAGNOSTIC_EVIDENCE_ONLY applies to passing transient r3/r4 controller/gate fixtures bound to their own source packages. HISTORICAL_FAILED_OR_STOPPED applies to r5's measured authority-inspection failure: a capability-free host UID993 observer could read pidfd/stat/status/cgroup/cmdline, but exe/userns/netns links returned EACCES and the inspector returned identity:null. The independent r5 audit assessed integration C. Its separate Stage B finding is source-derived: dropping every relay-UID994 OUTPUT packet also drops SYN-ACK and approved reply traffic. That packet failure was not live-tested in the cited record.
- 28 October onward, factory feasibility. The fixed Rust/systemd lifecycle and later UID/network fixtures provided narrower evidence described below. They did not complete the stopped H-100 run or integrate a production Gate 2 boundary.
- 2–6 November, Gate 2 handover. Inventory freeze, canonical planning, P01, P08 documents/T02, inert native preparation, source-only acquisition work and qualification planning advanced in separate decisions. None accepted H-100 or activated Gate 2.

No inspected record proves the full H-100 Planning-to-validated-Done sequence, successful controlled indeterminate-response recovery, or downstream release. This conclusion is UNVERIFIED_OR_MISSING, rather than an assertion that no uninspected historical event could exist.

### 2. PR relationships, integration and disposition

Live status and Git ancestry were both checked. All eight heads are ancestors of #59; only #52/#53 are ancestors of current Symphony main. #54–#59 diverge from main at 62ba70e6fb97373c4a1cb680846aea985fc80d98. Their old successful CI does not qualify a merge against November main. GitHub's merge_commit_sha on an open PR is not evidence of a completed merge.

MERGED_AND_ACCEPTED, scoped to the source corrections:

- #52, main &lt;- remediation/h100-p0-submission-correlation; head 7d0b36ccf00d240e4155f1d2f4f723899ea89abb; merged ecbdc36fa816f8b24c1901e311c0f521a6c98a90; tree d8de3f2c9b9f99769449cb37ef5366f6ea988679; make-all run 39293731348 success.
- #53, main &lt;- remediation/a3-plane-terminal-cursor-compatibility-fresh-20261022; head eb20afe483bea24de09809ef2f659450e2ab952d; merged 62ba70e6fb97373c4a1cb680846aea985fc80d98; tree 1eb430d3788d6cff666207e2fdeb8540ae906611; make-all 39749620514 success.

DIAGNOSTIC_EVIDENCE_ONLY, for retained candidate work and historical CI, all currently open/unmerged:

- #54, main &lt;- remediation/a4-proof; head 532860d7494224f50de93cba15f855c95ba2adaf, tree 56d1e52fdf1ec16e556576a19c408266ea9344ff; make-all 39836181007 success.
- #55, main &lt;- fix/h100-plane-relation-normalization; head 98948318355894129506748fa591becf57aee125, tree a2cbbacaa2b4acb43c8d426d410e1ddbb117a93e; make-all 39927264249 success. Its head includes #54 despite targeting main.
- #56, fix/h100-plane-relation-normalization &lt;- fix/plane-runtime-principal-v1; head 2fc770407f10d547bcafae5b33d43019d9881852, tree d13803d5a26cbafd5c312a2e635c483ddd009c31; make-all 39951442523, attempt 2, success.
- #57, fix/plane-runtime-principal-v1 &lt;- remediation/pre-h100-correctness; head 12cd0fb318aacec143f5a7f717ea1bf3b25ffa65, tree bfbb05d04ce13e2a30a539045da62fe7cf32938f; make-all 39983960545, attempt 2, success.
- #58, remediation/pre-h100-correctness &lt;- security/pre-h100-security-dependencies; head 27c2d813092a438e46505a5ddd8f50c0f787770d, tree 73b6c50b7222ccfb6c02d8f183aa3dfbcbddc78b; make-all 40002262476 success.
- #59, docs/h100-p0-host-relay-design &lt;- implementation/h100-p0-host-relay; base 5b3ecadeafa3c43ece8fe43099be56892d11d410, base tree beb7ee7354ac7b53567c464fa130d420e1c0aa6f; head 18e3b80d4464a6582c2b3144acb2f1fcf80b337c, tree f21afe562df23b12beb04da2cdd2b8cc46e38bfb; make-all 40172768955 success. Its locked offline qualification covered 39 Hex packages and recorded mix.lock SHA256 d65e62a264cf259d3f3f177b2ef47ee958cad11e189d0720d3b65f38f88607df. The PR expressly says LOCAL_QUALIFICATION_ONLY=YES, H100_EXECUTED=NO.

Each run is directly addressable as https://github.com/JCSchoeman96/symphony/actions/runs/&lt;ID>. The GitHub run records identify these PR heads and their historical bases. No current synthetic-merge checkout/job-log certification was attempted for these old candidates, and no merge is recommended.

Disposition is UNVERIFIED_OR_MISSING for a formal decision closing/superseding #54–#59. A2 was explicitly superseded by A3; the r5 audit and correction proposal stopped that integration direction. I found no decision declaring every open PR's useful correction obsolete. Gate 2 planning supersedes neither their missing integration nor their CI applicability automatically. Preserve these branches as evidence until a human decides whether to archive the experimental transport and separately retain still-needed relation/principal/security corrections after exact-diff, current-authority and candidate-CI review. No branch or PR was changed.

### 3. Disposable resources and local evidence inventory

The following resources still exist according to live reads:

- Attempt2 Plane project a8248ef8-85d1-4e30-9bc6-39cdcce971d5, H100-PROOF-20261025-18e3b80-01, identifier H18E3. Primary 7bb9ac19-b4eb-41ac-89f2-4da3c9a91336 and dependent dba815d6-3e71-4b4a-8d7d-fc60ef3f78ca are both Planning, state 95be39a3-9078-400f-a3a3-e3bf573b138d. Disposable PR #1 remains open on exact 18e3b80... over 5b3ecade....
- Separate HDEBE project 0bbe6a77-5b93-438c-b49c-4b4b5b353131, item 9bfcf2ab-6660-4cf4-b3ea-d5895055b8ab, remains Merging, state 28c6deaf-a664-41ad-be06-af2696acba5c. Disposable PR #1 merged at 2026-10-25T14:16:57Z as 478ae373afeb12005908288301d845a82ded445e. The source candidate was the same 18e3b80.... This updates the older preparation manifest's PR status; it does not update its lifecycle-proof result.

These observations are DIAGNOSTIC_EVIDENCE_ONLY. No token was minted or inspected for this investigation.

Retained evidence locations:

- Repository-local docs/superpowers/evidence/ contains A4 Q1–Q18 and both October 25 resource manifests. The A3 rebind/requalification/live-proof plans retain the missing-original-plan and transport-stop boundaries.
- /home/jcschoeman96/projects/symphony-h100-artifacts/attempt2/qualification/ retains installation/Stage A/Architecture E/r3-r5 host diagnostics. The frozen source package is under attempt2/work/v5-r5/source/h100-attempt2-host-control; the independent r5 report binds package inventory 288c6f389355bdd943a4806067fc1686de293995061e1b1ba714b2be36af052b to candidate 18e3b80....
- .scratch/h100-r5-independent-audit/ retains the independent report, source hashes, process/authority/egress matrices, historical comparisons and the unreadable-directory list. .scratch/h100-architecture-correction/ is a proposal, not a qualified replacement. Its REVISION_SCOPE=B does not override the r5 audit's integration C.
- .scratch/software-factory-v1/spikes/ retains initial IPC/host-observation/native sources and result manifests. systemd-followup/ retains three manual attempts; final-validation/ retains selective UID/storage/resource/network/tool/local-model/parent-child archives, acceptance records and later diagnostic repairs.
- /tmp/symphony-p08-t04-preparation-1c045ac215af/evidence/ retains the inert native scaffold preparation command/trace/inventories. /tmp/p08-t04-lockfile-correction-report.json is its later correction report. /home/jcschoeman96/symphony-acq-exec-02/ contains the exact five frozen R3 source files. /tmp/symphony-gate-a-planning.jHWl9XzY/ACQ_EXEC_05_GATE_A_PREPARATION_AUTHORIZATION_PACKET_R0.md contains the original R0 Markdown.
- Registered historical worktrees include .worktrees/h100-a2-host-qualification at ecbdc36..., .worktrees/h100-attempt2-runtime and .worktrees/h100-p0-host-relay-implementation at 18e3b80..., and baseline/design worktrees at 5b3ecade.... The separate superpowers A2 comparator is at ecbdc36...; its fresh A3 remediation worktree is at eb20afe.... These are retained checkouts, not fresh execution attestations.

Report/evidence hashes and byte lengths are indexed in the final identity appendix. I did not inspect credential stores, raw process memory, unknown sensitive trace contents or mounted runtime images.

### 4. What workstation and subscription work actually proved

Fixed systemd/Rust lifecycle.INDEPENDENTLY_QUALIFIED_FOR_EXACT_PROFILE. Retained v3 analysis systemd-followup/evidence/manual-2026-10-28-je2_hz97/analysis.json records archive/source agreement and assessor_reproduced=true. Its exact manually launched executor-to-PID1-to-worker profile passed capability reduction, dummy-credential attachment, cgroup cleanup, SIGKILL/SIGTERM handling and numeric UID62956 reuse with distinct invocation IDs. Profile limits were 50% CPU, 256 MiB, 16 tasks, 20-second runtime and two-second stop timeout; private root/tmp/network/devices, protected home/system/cgroups, empty worker capabilities and NNP were configured. This does not include a production broker, persistent-workspace reuse, traffic enforcement, real provider workflow, lease expiry or crash/reboot reconciliation. The earlier noexec staging attempt failed before executor startup; the following v2 reached PID1 but failed worker CHDIR because umask masked image-directory modes. The later v3 review supersedes those failures only for its exact fixed fixture.

UID, mounts and networks.DIAGNOSTIC_EVIDENCE_ONLY. Final-validation archive i2gibhq8 records positive retained canaries, denial across reused UID aliases, builder/reviewer separation, output/symlink containment and resource bounds. Its own network criteria were blocked. Later w5clmw_j records none/mediated/public/project network fixtures, DNS, cleanup and project-crash revocation; the project's acceptance record marks those PASS and locks the mechanism. No independently reproduced w5 network run was found. Public-egress allowance remains capable of sending to public endpoints. Neither these results nor a packaging/manifest test proves the selected production process/mount/network boundary.

Historical administrator command identities, not run here:

text
sudo /usr/bin/python3 -I /home/jcschoeman96/projects/symphony/.scratch/software-factory-v1/spikes/systemd-followup/bundle/admin-probe.py
sudo /usr/bin/python3 -I /home/jcschoeman96/projects/symphony/.scratch/software-factory-v1/spikes/final-validation/bundle/continue-network-after-diagnostic.py


Codex versions.MERGED_AND_ACCEPTED applies to H-080B's original 0.159.3 Linux isolation work and later H-080C integration in their accepted phase scopes. H-080B evidence pins upstream commit 01fc69f4026735edfdf6789820549727a4867b11, root-owned installation and 72 actual-Codex/AppServer tests. H-080C evidence records local 0.162.1 behavior/isolation and 72 tests on the user-owned standalone binary. Its historical report leaves hosted root-path evidence pending, while later governance accepts H-080C at PR #46. These historical report stages must remain distinct. Neither phase qualifies the new standalone patched Gate 2 artifact. Freeze ET-005 explicitly requires separate 0.162.1 boundary evidence; the selected patch audit pins upstream commit 092d3acd6bec3e3a14bdc7e7a2810ab628ab759d, tree 572cdecd45cd985f0ad80b63d8b86ffcb345f47a.

SIWC enrollment, materialization and refresh.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. The frozen selected contract is SIWC_CHATGPT_PLAN_OAUTH_RESPONSES: persistent host/account/client registration; host-only state/nonce/PKCE callback and identity verification; host-only refresh custody; only access materializes into the authorized app-server. Host identity persists across restarts. Refresh is serialized and commits replacement access/refresh as one generation. Each attempt's credential generation is immutable; no in-holder replacement, holder rollover or refresh-driven resume is permitted. A later generation serves a later grant after the refresh barrier and verified local drain. The accepted request contract is HTTPS POST https://api.openai.com/v1/responses, store=false, stream=true; WebSocket and GET /v1/models are denied. A model catalog result is not an inference entitlement or route proof. These are selected contracts, not observed local enrollment/inference results.

App-server/tool separation.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. The selected standalone patched entry sets non-dumpability and seccomp before config/Tokio. A credential-free guard forks bootstrap before access receipt; tools launch through a separate helper under a different UID and nested PID/networkless namespaces, never by forking bearer-bearing memory. Built-in login/refresh, process RPC and unselected shell/MCP/hook/nested-agent paths are disabled. No exact installed production artifact implementing all of this was qualified in the inspected evidence.

Bearer nondisclosure.UNVERIFIED_OR_MISSING. Every frozen BP-01 through BP-19 check is explicitly NOT_EXECUTED. Required channels cover environment/proc/memory, ptrace/process_vm, credential and source/materialization copies, inherited/transferred FDs, RPC/config/log/crash/temp state, provider request/response, source/output and host-tool data. Each needs an intended-holder positive detector and unauthorized-reader negative control with a synthetic non-live secret. The packet says LOCAL_BEARER_NONDISCLOSURE=UNVERIFIED; retained raw Gate 2 lineage is partial and diagnostic only; r4 remains unaccepted. No actual bearer is reproduced here. Deleting a local copy or stopping a process does not prove provider invalidation of a copied token.

Other traces and workflows.DIAGNOSTIC_EVIDENCE_ONLY. Factory acceptance remains B with authenticated Codex/Cursor/OpenCode workflows unproven. The located 0.162.1 SQLite trace was startup-only: initialize, EOF and exit, local no-auth provider, no model turn or provider request. It is distinct from the unspecified partial Gate 2 trace. No evidence establishes actual SIWC enrollment/PKCE completion, durable refresh rotation, Responses routing or the complete nondisclosure suite under the selected boundary.

### 5. Gate 2 accepted decisions and exact scope

- Inventory freeze.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. PR #60 merged c5b29a8417ae1d82db6e438716c1425ad6889761. G2-INV-2.1 freezes 115 entries, 26 obligations, 14 lifecycles, 19 bearer channels and 13 evidence-transfer claims. Combined canonical hash is 1458bb041215c6268f2c69c01ed4198357e9561fbdc17a62e7288d0817b61911; inventory 7341b7faae506db873f3aa9915f8c162f2a7ebe284e872e78189f66c6ead5c9c; obligations c34f145948698ecd474c6ab8194537df4ad3ab8e8ad2c7070cc9ffde9142d686. The acceptance explicitly says no separate original decision ID/signatory/time was supplied. Do not invent one. This accepted inventory is not 26 passed obligations.
- Canonical plan/scanner.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. PR #61 merged 86336d28671cfd6ac0a55c2ebe48094b8d8a8237; the scanner addendum records Master planning approval and policy selection. PR #63 merged Herdr qualification refinements as 0c53c732bbf68641482741c98afb25e073721ad9. No runtime authority follows from either document publication.
- P01 / PR #62.MERGED_AND_ACCEPTED. Human decision a8b0c8ba-6844-4e47-ad98-f0ef326481fe on SGOV P01 item 8c89c281-fcf2-445f-b57a-d236cb159b6a accepts merge 30fc30ec27fbadd7277c470a6d6cdb52ced59a4e, tree dc58f0babebe8a28b3de492eb430a84398abc580. Post-merge CI 41822564643 succeeded. Scope is durable dormant resource intent/fencing/migration and fail-closed launch. It supplies no active grant, allocation or verified cleanup.
- P08 v0.7 / PR #66.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. Spec 226,832 bytes / SHA256 b510eb0c8459c126d3b310d3d5c7225f9d8dda4559a16ff6704842a6fb69568d; plan 68,919 bytes / ac6debd05e32572fbae567a7300d643110007a6729b1adf975ed8d66985d9b94. Merge ca0321896e2bc3edc75ab98a81be1f2aa217cf7f, tree 11ba25c640d6af00e857e7e4da02921b8702ad7e; post-merge CI 41986626466 succeeded. Later human acceptance b22a7324-e8f4-47fa-ae82-708658a165dc accepts those document hashes despite preserved PROPOSED markers. Separate 56b9cf89-f82a-4df3-a087-466485bb5be3 adopts that historical implementation baseline. Neither authorizes all P08 code.
- P08-T02 / PR #67.MERGED_AND_ACCEPTED. Grant 6229fc77-303f-4f61-a2ef-95f944d42653, corrective acceptance 9e83a623-b8dd-423a-b838-326e2675fcff, final pre-merge decision f4062aad-bf34-4b5b-9f50-3408dad71ba8, closure 476bb8f1-07f0-4dcb-9251-736906fdf6bc. Exact published head e6549b3fb899b10b605dd1198f975bd52a41b9b8; merge 1c045ac215afee47e94d566bf3f3baa0751beb9d; tree 4f1a87340ce0b93801620be4f602dc1cef0e92f8; post-merge CI 42035897552 succeeded. Scope is three-file pure P01 compatibility projections, not provenance/cleanup authority. Earlier fixture failures and scale timeout have unproven causes; later serial tests/CI passed. No cause is inferred from later passes.
- P08-T04 preparation.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. Initial offline lockfile preparation stopped on confined Cargo metadata effects and mode 0664 versus required 0644. Archive review fa214782-c7b9-46fc-aa77-3007a470ea0f verified the one-command trace and ten files, but withheld acceptance. Human correction 5b6bee04-b0b2-4f5a-8072-0d12a1843d64 allowed exactly those historical metadata effects and one mode change. Complete correction evidence then supported 4a1d9f29-2340-470b-8a99-7d74ee3df9c2, ACCEPTED_PREPARATION_ONLY. This closes the inert scaffold preparation gate only. Its locked_build_identity test is intentionally failing/unexecuted; no native build qualification exists. Partial build dossier d472365a-5095-4826-8b5b-e83834c053bd was not accepted as complete; completed dossier 4d26a5dc-c427-49e0-929e-78537c4b2b2d was accepted as reviewable research only, with build inputs still blocked.
- Frozen ACQ-EXEC-04 R3.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. Comment 3d925f87-6095-46a3-94f8-b1f3e33995d2 accepts exact five-file static source and its R2-to-R3 diff. It excludes imports/compile/lint/tests/fixtures/acquisition/publication and leaves the earlier sed-i staging deviation unratified. Operational entry points refuse; qualified_harness() raises SkipTest. Current local bytes match all five recorded hashes, but that does not prove continuous custody or historical staging compliance.
- ACQ-EXEC-05 R2.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. Initial review 6b7b9ebb-919d-4558-b2e5-1e6cb2275b0b requested fixes; R1 review 23e41f43-9891-418a-8585-46e96f17fa65 accepted F01–F03 at planning level but required lifecycle correction. Final 80924582-aa29-4da5-96af-7acbd63a8319 accepts only the 40,903-byte R2 qualification plan, SHA256 ae823f8f23f476fed092c0b120b8cea2e68bd8ef14053ac66eca89670cfcab4a. Gate A T01–T11 expects 11 methods, 104 explicit subtests and 240 overlapping loop observations. These are static expectations, not results. Gate B T12–T20 cannot run meaningfully against frozen R3's refusing/skipping interfaces.
- R2 documentation publication / PR #68.MERGED_AND_ACCEPTED, documentation only. Final pre-merge 36e2721d-3b1d-4f39-a2a0-22a9e30f068a and post-merge 4d16cc4e-484f-4ecb-b198-f2aed9931873 accept publication at the current main SHA/tree and successful run 42180019882. This is not executable qualification.
- Gate A R0 packet.DESIGN_OR_CONTRACT_ACCEPTED_ONLY. Latest human decision 224c2e4c-5842-414c-a7c8-836484f923b3 accepts planning content in an 83,125-byte text export, SHA256 00f298c510330c344bdffc31af1e5f23f9844d3ad3c483103a6eb752caf3b7a3. The now-located original Markdown is 84,693 bytes, SHA256 798eb99f523d0452961458760f301665dd637f47b3102c111dada0dfe25b5bdd. They are different artifacts. Matching the reported Markdown hash now does not turn the earlier export review into exact-byte Markdown acceptance. Q01–Q16 remain unresolved.

Current authorization is unambiguous: Gate A preparation, control qualification and execution NOT_AUTHORIZED; Gate B execution BLOCKED; P08-T04 full acceptance NOT_GRANTED; AUTH_07 SUSPENDED_UNCONSUMED; Gate 2 activation NOT_AUTHORIZED. The programme's historical H-100 AUTHORIZED_ACTIVE_NOT_ACCEPTED projection remains alongside the later scoped execution lock. They describe different authority scopes.

### 6. Minimum missing executable proofs and next action

These are the missing proof groups; old passing fixtures should be reused as bounded evidence rather than rerun merely to recreate history:

1. UNVERIFIED_OR_MISSING: independent qualification of the Gate A supervisor, durable attempt ledger, per-request gate, collector/module-origin observation, external immutable sink/ACK, source custody and stopping behavior. R0's unresolved prerequisites and exact environment/grants must be settled before execution. A Python producer's self-report or zero exit cannot replace independent acceptance.
2. UNVERIFIED_OR_MISSING: the exact frozen R3 Gate A T01–T11 source-contract run with complete nested/loop results and no skipped/missing cases. Gate B then requires a separately authorized successor, its own Gate A result and T12–T20 synthetic integration against qualified fixtures. Frozen R3 cannot substitute for that successor.
3. UNVERIFIED_OR_MISSING: approved complete Rust toolchain/target/CRT/linker/build-image closure and the intended native artifact's locked build identity, independent clean rebuild, installed-byte/profile binding and native failure/cleanup proofs. Inert Cargo.lock generation and the disposable Rust executor do not satisfy this.
4. UNVERIFIED_OR_MISSING: the selected patched Codex artifact's real process/storage/network/tool separation plus all 19 synthetic-secret nondisclosure channels, including host logs/crash and open/unlinked state. This is the absent OB-025 integrated qualification; ordinary isolation tests and startup traces cannot replace it.
5. UNVERIFIED_OR_MISSING: actual dedicated SIWC enrollment/account separation, persistent host identity, callback/PKCE verification, atomic generation/refresh crash behavior, access materialization, approved Responses-only egress and denial of unapproved routes under that exact artifact. Existing provider documentation supplies the contract; no accepted local executable result supplies these outcomes.
6. UNVERIFIED_OR_MISSING: integrated remaining obligations for fresh resources, exact publisher/candidate fencing, provider ambiguity/restart retention, authoritative cleanup/quarantine and exact human-merge/Done/dependency closure. Only the already accepted P01/T02 subcontracts may be counted as completed. Once separately authorized and qualified, the real H-100 proof is still needed; H-110/H-120B require their own authority.

Recommended next technical action: perform the read-only Gate 1 authorization-readiness assessment named by the latest R0 decision. Bind the original R0 bytes and exact frozen R3/scaffold identities, map existing artifacts to Q01–Q16, and isolate the smallest missing collector/supervisor/evidence-control contract requiring a future precise grant. This reuses the accepted R2/R0 work and retained fixtures. It does not reopen the architecture or issue an executable preparation grant. No such new work or mutation was performed here.

### 7. Explicit investigation gaps

The original A1 plan/approval and detailed preflight trace were not recovered. Twelve root-protected historical qualification directories were not inspected; their names are reproduced in the identity appendix. Missing authority is privileged read access to those retained records, not permission to rerun or repair anything. No elevation was attempted. Unknown raw traces and credential-bearing stores/memory were excluded by the user.

The exact original R0 text-export file was not located locally, so I cannot compare its bytes with Markdown; its independently reviewed export identity is established by the live decision. The original inventory approval lacks a separate decision ID, as its own acceptance document states. No accepted retained filesystem path for a completed Gate 2 bearer suite was found. The partial raw Gate 2 trace's full lineage remains unverified. Formal disposition of #54–#59 is absent. These gaps prevent claiming an exact reconstruction of every October event or current executable qualification.

### 8. Exact identity appendix

Raw SHA256 values below were recomputed read-only. Git identities refer to current main, not the dirty working copy. Paths below are absolute or relative to /home/jcschoeman96/projects/symphony. Archive hashes identify retained bytes; they do not broaden a reviewer decision.

#### Governing Git objects

- docs/symphony-hardening-playbook-v4.1/V4_1_MASTER_ROADMAP.md: 125,166 bytes; SHA256 d2966689ad6b9d50d52b5110c76698fdc8666cf748e921164cc34b3ad1edeaf9; Git blob 4b0528bdc0647d889b42ebc478081d5b873898fe.

- docs/SYMPHONY_V4_1_UNIFIED_EXECUTION_ROADMAP_v1.3.2.md: 126,911 bytes; SHA256 65035de28e939f746be1db1e01b1e6966f64a3fc2da101400553672289ead1d7; Git blob 5ef99584283850482df822e8935428477353797c.

- docs/symphony-hardening-playbook-v4.1/HARDENING_STATUS_LEDGER.md: 26,712 bytes; SHA256 9fe47f4a454c1e1b838a930c882665dd845da23a3650e15f98917e715f23c18f; Git blob 9830d546a803d6de8c5e24e1584c320945176afc.

- docs/symphony-hardening-playbook-v4.1/GATE2_INVENTORY_FREEZE_PACKET_1458bb041215c626.json: 683,322 bytes; SHA256 a651b1574ec0a186f6b4cd9548787cf9b67009f6692268ce5a8d0669d9d0636a; Git blob 6cf92dbad8507d4e6c7553392b163fcac02b897d.

- docs/superpowers/plans/2026-11-03-gate2-v1-implementation-plan.md: 231,932 bytes; SHA256 a1d5cdba65c19a09e86ed814a595e8bbae0c9dcfc97afe021ab67826db09ff68; Git blob bdb2840e5ea4ca8c8912d6cada3287078bbb3c72.

- docs/symphony-hardening-playbook-v4.1/GATE2_P08_HOST_EVIDENCE_SPEC.md: 226,832 bytes; SHA256 b510eb0c8459c126d3b310d3d5c7225f9d8dda4559a16ff6704842a6fb69568d; Git blob d4185d0f5aa4eacee3f7133db3a84648adffc160.

- docs/superpowers/plans/2026-11-04-p08-host-evidence-implementation-plan.md: 68,919 bytes; SHA256 ac6debd05e32572fbae567a7300d643110007a6729b1adf975ed8d66985d9b94; Git blob 83774a4185aab4908155abdc60a30a7081b76fbc.

- docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_05_R2_MASTER_GATE_PLAN_ACCEPTANCE_2026-11-06.md: 9,939 bytes; SHA256 a60a8ae12e2ee79e6f57ac65d130c0b00173fd90f1292699043fbeba1ea8f26d; Git blob d2b166f40774521d1a1f3d4370cd634237e71a52.

- docs/symphony-hardening-playbook-v4.1/ACQ_EXEC_05_R2_SYNTHETIC_QUALIFICATION_PLAN_2026-11-06.md: 40,903 bytes; SHA256 ae823f8f23f476fed092c0b120b8cea2e68bd8ef14053ac66eca89670cfcab4a; Git blob 1fd0af3e23287bab8939876589abc064c5655b45.

#### Local reports, archives and executable/source identities

- docs/superpowers/evidence/2026-10-22-a4-candidate-evidence.md: 6,518 bytes; SHA256 ba6ece09440d20e8c2ea36ff86032c0782e175ee2170bffe0495f53476d12ea7.

- docs/superpowers/evidence/2026-10-25-h100-attempt-2-preprovisioning-18e3b80-01.md: 10,073 bytes; SHA256 6fac8c3f1a557e33c978c3db29daee1c145347fd3324d539ae02e33da990a7b5.

- docs/superpowers/evidence/2026-10-25-h100-resource-preparation-debecc32.md: 13,506 bytes; SHA256 5224320d0611d13d1374f907ab32eb7664b601502a747760bcb3cf2279d0173c.

- .scratch/h100-r5-independent-audit/report.md: 52,725 bytes; SHA256 0ef4d9bac1c0e93c0961c8fda00bc8cabb1410530c6ed4b67743d8d3c4057b05.

- .scratch/h100-r5-independent-audit/historical-r5.md: 10,895 bytes; SHA256 ea902d6c0ad1506d180fa48c3e432ddaccaf364ee05293a3f5759e1453c9e3f6.

- .scratch/h100-architecture-correction/correction.md: 55,956 bytes; SHA256 0fcdbb4416355e8f8f40460d8be1d2a8dfc4b3e3a436d65579d7c2cfe2d93541.

- .scratch/software-factory-v1/final-validation-acceptance.json: 38,329 bytes; SHA256 709b41c82c9362986184bd244dbcf91ace63bcf3e69e9331db7019c5cd6a3494.

- .scratch/software-factory-v1/subscription-acceptance-reconciliation.md: 10,454 bytes; SHA256 4f5606ea2d381b749abcdd93353079a674fc1da2cc28db9a716204ed3f06b761.

- .scratch/software-factory-v1/provider-authentication-boundary.md: 4,379 bytes; SHA256 8b7c5148f620583c849015bf8b4a728f36904b3f83130f15a5dffa3f6f5f5cef.

- .scratch/software-factory-v1/spikes/systemd-followup/evidence/manual-2026-10-28-je2_hz97/analysis.json: 2,099 bytes; SHA256 07d260f50e6e9a6825307cc0c47a46a3ebed1813515e3b9b7bf4a477b4ef3efd.

- .scratch/software-factory-v1/spikes/systemd-followup/bundle/executor: 382,960 bytes; SHA256 222b6b13ec90a557eaa6f9e14aaee3f726d7bdc9f5686477d6a92640591b7a7b.

- .scratch/software-factory-v1/spikes/systemd-followup/source/executor.rs: 9,234 bytes; SHA256 42c51a84f3915ad1b8fe20ce8e23841b6363789579713e09b1f8d241ad7754e0.

- .scratch/software-factory-v1/spikes/systemd-followup/source/runtime.rs: 3,415 bytes; SHA256 8c6169d1f67e2f5f89a21ced670345ba48e8cc15b82cd48738d59f57e476d6ae.

- .scratch/software-factory-v1/spikes/final-validation/bundle/executor: 395,464 bytes; SHA256 656b4c9d645c20b8880dd6199d8b121d12aef1d0e0f3ab2bba9306dacbe4ce87.

- .scratch/software-factory-v1/spikes/final-validation/bundle/executor.rs: 12,390 bytes; SHA256 2d8dbe5a9a289e6596808ac4b7a2f3f04dbea01d2d372fe7c246d3ef50c813c6.

- .scratch/software-factory-v1/spikes/final-validation/evidence/i2gibhq8/original.tar: 3,614,720 bytes; SHA256 c4c91048e1ed00ecbb0367f54562a08b4cfd7b4325c2676d63a389e62d819d90.

- .scratch/software-factory-v1/spikes/final-validation/evidence/i2gibhq8/assessment.json: 6,831 bytes; SHA256 cb81cff69dcb5ea195d9f66a51ab4f56e12b04edea547e5951de05e9717c67e8.

- .scratch/software-factory-v1/spikes/final-validation/evidence/w5clmw_j/original.tar: 4,096,000 bytes; SHA256 cde8ce0eb4f26021cf228a7c5ba666613939a4339884b4d5e3793111fc3e3656.

- .scratch/software-factory-v1/spikes/final-validation/evidence/w5clmw_j/evidence.json: 2,269,770 bytes; SHA256 33cc37a352b9bb8a704bc534f62b4bca8a2891c60aa664995623c255c0b3d236.

- .scratch/software-factory-v1/spikes/final-validation/validation/substrate-acceptance-review.json: 9,976 bytes; SHA256 de39b699074f84e81c80a8107d6c08bc65543d3a4cfae43669acd91ba53c92e9.

- .scratch/software-factory-v1/spikes/final-validation/validation/sqlite-wal-persistence-research/evidence.md: 14,980 bytes; SHA256 76889a5f249aff4eca5b0c3bf1918ed81970ca6f6818628224988518ebf4b0e5.

- /tmp/p08-t04-lockfile-correction-report.json: 413,670 bytes; SHA256 f50dbc0289e3dfd596a53f8443c6420b4b12bd2f4f71ca33975e1694ea3d3e3a.

- /tmp/symphony-gate-a-planning.jHWl9XzY/ACQ_EXEC_05_GATE_A_PREPARATION_AUTHORIZATION_PACKET_R0.md: 84,693 bytes; SHA256 798eb99f523d0452961458760f301665dd637f47b3102c111dada0dfe25b5bdd.

Frozen R3 root is /home/jcschoeman96/symphony-acq-exec-02/. All five current files were regular, UID:GID 1000:1000, mode 0600, link count 1. This current observation does not prove historical custody.

- executor.py: 7,195 bytes; SHA256 ee39547d466a89a18354e66fbf2336ea647aaa58834cca4ea60badb6744b6660.

- journal.py: 31,597 bytes; SHA256 ff45a0799493c544705c97fa0c06311ba75fe74ee86531131ad045bf4213ed8e.

- synthetic_config.json: 452 bytes; SHA256 49c29a3c213b96a8b1bc117e23bfbfd0c41134d7436f2f038429a83b719d74a4.

- tests/__init__.py: 75 bytes; SHA256 cfa461f28b2af5b8c930ebe42f938d5d335800b53356031e4889ec1d290c066d. **Editorial correction:** the supplied investigator text export wrote `tests/init.py`; the accepted R3 source identity is `tests/__init__.py`, as attested in Plane SGOV-2 decision `3d925f87-6095-46a3-94f8-b1f3e33995d2` and the committed ACQ-EXEC-05 R2 acceptance record. The file size and digest are unchanged.

- tests/test_executor.py: 31,350 bytes; SHA256 6bd2d674a7af4acf1276540c5582e3da003d3fd47f68c567ea64646c745f6b8c.

P08-T04 reviewed archive p08-t04-preparation-deviation-evidence.zip has decision-attested SHA256 98b60c41977a7cbcd3d8154b99b76a3d744a848d9daeb7ad4ba7a7401f417eab. Its exact Cargo.lock is 264 bytes, SHA256 b05d465a4d9c6f2d56449a6a56ae99863e96bd192d629c127289694b6f388fe5, Git blob 69b4fe9f9dfd9ec7f10050ebc59228736fea9fe1. The independent review, rather than a fresh local build, establishes its preparation scope.

Systemd original manual archives: v3 sf-v1-systemd-followup-evidence-je2_hz97.tar, 112,640 bytes, SHA256 4635385061a3226091a32de5c2380eebf1da02451a7353a85780f6d94b9c09d6; v2 sf-v1-systemd-followup-evidence-cddnmf31.tar, 71,680 bytes, SHA256 ec77b4975c4b1c6bdf719405d305c3a75e5718bf8436e30fc3281ee9c4ef800a. These identities are retained in the reviewed analysis/index; their different outcomes are preserved.

#### Uninspected protected qualification directories

All entries share /home/jcschoeman96/projects/symphony-h100-artifacts/attempt2/qualification/. The retained audit reports permission denial. Privileged read authority was not sought.

- v5-r5-proof-runtime-integration-20261027T161700Z.

- v5-r5-execstartpre-context-20261027T194636499196Z.

- v5-r5-execstartpre-context-20261027T195055440511Z.

- v5-r5-inspector-peer-capture-20261027T171550Z.

- v5-r5-inspector-peer-capture-20261027T171733Z-e3e8d9.

- v5-r5-proof-runtime-integration-20261027T190131Z-namespace-fix-01.

- v5-r5-proof-runtime-integration-20261027T160845Z.

- v5-r5-peer-diagnostic-20261027T192641Z.

- v5-r5-execstartpre-context-20261027T194413Z.

- v5-r5-proof-runtime-integration-20261027T161500Z.

- v5-r5-execstartpre-context-20261027T194941816909Z.

- v5-r5-execstartpre-context-20261027T194815676186Z.

#### Frozen obligation register

These are required obligations, not a pass list. All were counted directly from the committed packet.

- OB-001: Fresh attempt workspace and owner binding.

- OB-002: Attempt grant and durable fence.

- OB-003: Restart discovery and quarantine records.

- OB-004: Attempt-private storage, hidden objects and capacity bounds.

- OB-005: Process/cgroup/namespace enforcement and version proof.

- OB-006: Bearer nondisclosure over every channel.

- OB-007: SIWC registration enrollment and account separation.

- OB-008: Credential-set generation, serialized refresh and crash-safe rotation.

- OB-009: Attempt access materialization and conditional cross-attempt reuse.

- OB-010: Revocation, reauth and secret-free operator state.

- OB-011: OAuth callback, state/nonce/PKCE and identity verification.

- OB-012: Model egress, DNS/TLS and /v1/models denial.

- OB-013: Five Plane tools and mutation reconciliation.

- OB-014: SourceControl read-only binding and unselected tool exclusion.

- OB-015: Writer fence, exact local candidate and safety validation.

- OB-016: Bounded host publisher and credential scope.

- OB-017: Publication record, restart reconciliation and fresh CandidateRef.

- OB-018: Checks/review/human merge/CompletionProof exact identity.

- OB-019: No generic output/handoff promotion; scanner unchanged.

- OB-020: Secret-free logs, crash/core, host evidence and diagnostics.

- OB-021: Process and host capacity bounds.

- OB-022: Persist topology selection and both H100 provenance/lock facts.

- OB-023: Claim-specific evidence transfer review.

- OB-024: T3Code evidence boundary.

- OB-025: Secret-free host diagnostics and evidence controls.

- OB-026: Provider request/effect record and ambiguous-result retention.

RECONCILIATION=INCOMPLETE_WITH_EXPLICIT_GAPS
