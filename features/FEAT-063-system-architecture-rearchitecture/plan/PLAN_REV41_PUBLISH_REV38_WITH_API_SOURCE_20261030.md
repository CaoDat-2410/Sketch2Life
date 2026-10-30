# Plan Rev41 — publish Rev38 with its API source on a branch

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED for the path-scoped commit and new-branch push below, under the owner's 2026-10-30 direct instruction to commit and push.
- Target branch: `codex/feat063-rev38-ui-mockups-20261030`, rooted at fetched `origin/dev` commit `01b25a7850d1887c67891bfa15e76c52c5c04938`.

## Reason for superseding Plan Rev40

The Rev38 screen/component indexes and evidence cite the Rev37 API contract catalog for mounted-versus-SRS-target labels. That catalog is not present on current `origin/dev`. Publishing Rev38 without its cited source would leave the review package with a broken provenance link. Rev41 supersedes Rev40 only to include the Rev37 API contract catalog as a read-only source artifact; it does not include Rev37 execution reports, scripts, test logs, or unrelated changes.

Local `dev` and `origin/dev` diverged after `origin/dev` was force-updated. Updating `origin/dev` from local `dev` would require a force push and could replace remote history. This plan publishes the scoped package on a new branch based on the fetched remote tip and does not rewrite or update `origin/dev`.

## Scope

- Apply only the Rev38 UI package and its FEAT-063 records to an isolated worktree based on current `origin/dev`.
- Include 23 screen drafts, nine component boards, shared synthetic artwork, prompts/motion notes, indexes, EV-063-31, Rev38 plan/approval, AC-33 consistency correction, and associated context/decision/source/status/evidence-index records.
- Include `artifacts/API_CONTRACT_CATALOG_FEAT063_REV37_20261030.md` solely as the source cited by Rev38. Its Git-normalized content SHA-256 is `4090833B7EC03A6FEE81E0F8AE7FD57F9C2C1A8901D969D13F3C3F5CAAD29C54`. Do not imply that Rev37 execution evidence or product-code changes are included.
- Include this publish plan, Plan Rev40 as superseded history, and their approval records.
- Exclude Rev37 execution evidence, plans, scripts, test logs and temporary files; Plan Rev39's obsolete direct-`dev` assumption; other features; unrelated staged/worktree changes; and all secrets or `.env` files.
- Create one commit: `feat(FEAT-063): add Rev38 UI mockup drafts`.
- Push only `codex/feat063-rev38-ui-mockups-20261030` to `origin`.

## Acceptance criteria

- **AC1 — Safe base:** the branch starts at the fetched `origin/dev` commit above; do not force-push or alter `origin/dev`.
- **AC2 — Exact scope:** the commit contains only the Rev38 package, its required API source catalog, the approved plans/records, and associated FEAT-063 updates.
- **AC3 — Conflict safety:** tracked Rev38 edits apply without unresolved conflicts or silently overwriting remote changes.
- **AC4 — Security:** run `python tools/validate_repository_security.py` before commit and again before push; stop if it rejects.
- **AC5 — Verify delivery:** confirm the commit exists on the new remote branch and report its hash and branch.

## Procedure

1. Record the plan hash and the owner's direct commit/push instruction in `approvals/TASK_APPROVAL.md`.
2. Use the isolated worktree based on fetched `origin/dev`; apply only the listed Rev38 deltas and copy the cited Rev37 catalog.
3. Review exact paths, approval hashes, provenance links, and generated-only asset location; run security validation.
4. Commit the scoped package, run security validation again, push the new branch, and verify the remote ref.

## Excluded

Force-pushing `dev`, merging or rebasing the 849/498 divergent histories, committing Rev37 execution outputs or product-code fixes, unrelated staged/worktree changes, visual promotion, product implementation, API/schema/database changes, tests/builds, or deployment.
