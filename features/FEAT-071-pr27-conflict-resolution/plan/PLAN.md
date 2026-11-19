# FEAT-071 plan revision 1 — PR #27 conflict resolution

- Revision: 1
- Status: APPROVED
- Implementation status: IN_PROGRESS
- Prepared and approved: 2026-11-16, Asia/Bangkok
- Product authority: canonical FEAT-063 SRS v2.7-draft Rev60, unsigned; no requirement changes in scope.

## Goal

Resolve the conflicts between PR #27 (`codex/fe-ui-web-remediation`) and its `dev` base in a reproducible merge commit on the PR branch. Preserve the separate feature scopes and leave the PR open and unmerged.

## Scope

- Resolve every path reported unmerged when integrating `dev` into PR #27.
- Keep the append-only approval records from both histories.
- Keep the consolidated web application in `apps/web`; preserve FEAT-063 changes from the deleted web source paths in their migrated equivalents where the approved web scope supports them.
- Preserve the complete `apps/mobile` tree from `dev` because mobile is outside FEAT-066/067 scope; retain its workspace and lockfile entries.
- Preserve the `apps/ui-mobile`, backend, API, and contract-test changes from `dev`.
- Add FEAT-071 plan, approval, decision, evidence, and status records; update the root approval register.

## Out of scope

- Merging PR #27 into `dev`, changing its base, force-pushing, rebasing, squashing, deployment, or product/SRS edits.
- New backend/API contracts, model/provider calls, credential changes, database changes, visual redesign, or changes unrelated to preserving the two parent histories.
- Automated application tests unless the owner asks for them. Repository governance/security/architecture validation and whitespace checks remain required before publishing.

## Steps

1. Capture the PR/base/common-ancestor SHAs and enumerate conflicts from a real isolated merge.
2. Resolve append-only governance records by retaining both sides; resolve backend contract tests by keeping both route assertions.
3. Keep old web app directories removed, carry applicable `dev` Teacher and school-admin behavior into the consolidated modules, and preserve the complete out-of-scope Android tree from `dev`.
4. Reconcile `package.json`, `pnpm-workspace.yaml`, and `pnpm-lock.yaml` with the retained apps and one active web app.
5. Review every resolved path, scan for conflict markers, record evidence, and run the required repository checks.
6. Publish only a fast-forward merge commit to the PR head ref. Confirm PR #27 remains open and unmerged.

## Acceptance criteria

1. The merge commit has PR head as first parent and the recorded `dev` SHA as second parent; no force update or rebase occurs.
2. Every originally unmerged path has an explicit resolution and rationale recorded in feature evidence.
3. Approval records from both parents remain intact and append-only; backend route coverage from both test changes remains present.
4. The consolidated web app remains the sole active web portal; relevant `dev` behavior is carried into its corresponding modules; `apps/mobile` and `apps/ui-mobile` source from `dev` are preserved.
5. Root package/workspace/lock files agree with the retained application trees and no unresolved conflict markers remain.
6. `validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, and `git diff --check` pass on the final candidate.
7. PR #27 remains open, unmerged, and targets `dev`; the new head is a normal descendant of the old PR head.

## Risks and mitigations

- The PR removes source paths that `dev` updated. Preserve the updated behavior in the consolidated destination or retain the complete out-of-scope app tree; do not accept a deletion solely because it is the PR side.
- The lockfile covers multiple mobile and web importers. Preserve the importer and package graph for every retained workspace app, then inspect it after reconciliation.
- Existing validation may report issues already present on either parent. Record baseline and final outcomes separately; do not hide failures as merge fallout.
- The PR branch has a pre-existing local linked worktree outside this task's writable root. Use an isolated task worktree and update the remote ref only with the recorded expected head SHA.

## Verification plan

- Inspect unmerged path list, conflict markers, parent tree diffs, and final commit parents.
- Run repository harness, security, architecture, and `git diff --check` commands from the final candidate tree.
- Do not run automated app tests/builds under the current feature approvals.

## Rev2 addendum — owner-authorized PR merge attempt

- Recorded: 2026-11-16 (Asia/Bangkok), after completion of Rev1.
- Trigger: the project owner directly changed the prior no-merge instruction in chat: “đc r :)))) lên dev r lỗi ci tính sau” (proceed to `dev` now; CI errors can be handled later).
- Scope: submit the standard GitHub merge operation for PR #27 into its existing `dev` base, using the current verified PR head SHA. Preserve the completed Rev1 merge commit and its two-parent history.
- CI disposition: the owner accepts proceeding while the current CI run is not green. Record known failures in evidence; do not wait for CI to pass before attempting the standard merge.
- Protection boundary: do not bypass required checks, branch protection, or GitHub's mergeability gates. If GitHub rejects the normal merge request, leave the PR open and report the exact blocker.
- No other scope changes: no force push, rebase, squashing, direct write to `dev`, product/SRS edit, or deployment.

### Rev2 acceptance criteria

1. GitHub confirms PR #27 is merged into `dev` through the standard merge API and reports the resulting merge SHA.
2. The PR head matches the SHA captured immediately before the merge attempt.
3. Existing CI failures are recorded as accepted by the owner's instruction; no checks are bypassed.
4. If the standard merge is blocked by repository policy, preserve the open PR and record that outcome instead of circumventing the gate.
