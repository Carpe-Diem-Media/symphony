Symphony — Repository-Wide Agent Instructions

These instructions apply to all agents working in this repository.

For Elixir-specific work, also follow "elixir/AGENTS.md".

Authority

The accepted Symphony V4.1 hardening playbook, Master Roadmap, governance records and explicitly approved task scope remain authoritative.

This file provides working instructions only. It does not authorize implementation, installation, signing, enrollment, merges, releases or lifecycle transitions.

MANDATORY — Durable Artifact Preservation

A machine reboot, agent termination, workspace cleanup or temporary-directory deletion MUST NOT cause loss of completed or accepted work.

Permanent artifact storage

Critical generated artifacts must be preserved outside temporary directories and disposable worktrees.

Preferred durable location, subject to local verification:

"/home/jcschoeman96/projects/symphony-artifacts/"

Critical artifacts include executable payloads, worker images, runtime evidence, manifests, review packets and accepted installation inputs.

Temporary storage may be used for intermediate operations but must never be the only retained location of important completed work.

Preservation before completion

Before reporting work as complete or ready for acceptance:

1. Preserve all required artifact bytes in persistent storage.
2. Verify exact hashes, complete inventories and relevant filesystem metadata.
3. Record the durable path and provenance in the handoff.
4. Verify that the saved copy remains independently readable.
5. Keep all required source material until preservation succeeds.

Missing or mismatched durable evidence blocks completion and acceptance.

Artifact lifecycle

Model all significant artifacts with explicit states, transition guards, side effects and terminal outcomes.

Normal lifecycle:

"CREATED → PRESERVING → VERIFIED → SUBMITTED → ACCEPTED → RETAINED"

Exceptional outcomes:

"PRESERVATION_FAILED", "VERIFICATION_FAILED", "RECOVERY_REQUIRED"

Cleanup lifecycle:

"RETAINED → CLEANUP_REQUESTED → OWNER_APPROVED → REMOVED"

Never automatically delete accepted artifacts. Never silently overwrite or replace an existing accepted identity.

Routine disposable intermediates may be removed only when they are not required evidence or the sole surviving copy.

Recovery and backups

If an accepted artifact is missing, stop dependent operations and search existing durable evidence before proposing reconstruction.

Re-establishment of changed bytes requires separate authorization.

Persistent storage must be supplemented by verified independent backups for recovery from storage-device failure.

Never preserve private signing keys, passwords, recovery codes or credentials in general-purpose artifact directories.

Agent handoff requirements

Every completed task must identify:

- Exact source commit/tree and applicable authority.
- Changed files and generated artifacts.
- Permanent artifact location and verification result.
- Tests and checks performed.
- Outstanding blockers and unresolved uncertainty.
- Explicitly authorized next action.

Do not claim success when required evidence is missing.

Runtime separation

This document governs agent conduct, not Symphony's executable runtime behavior.

Do not add these instructions as a runtime dependency or alter runtime packaging merely to introduce this file.

Any change affecting runtime source closure or immutable deployment identities requires independent review.

Merge discipline

No merge recommendation without independent verification of the exact PR diff, current CI and applicable authority references.

Human approval and formal acceptance remain separate from passing tests.