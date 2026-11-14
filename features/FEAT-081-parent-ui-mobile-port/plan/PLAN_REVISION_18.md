# FEAT-081 Plan Revision 18 — Publish Rev67 Parent UI Alignment

## Owner instruction and goal

On 2026-11-15 the owner directly instructed Codex to push the completed Parent UI SRS Rev67 alignment changes so backend work can continue afterward. This plan scopes publication of that already-reviewed worktree change set as one new commit on `feature/fe-mobile-remediation`, followed by a push to `origin`.

## Exact publication scope

Stage only these FEAT-081 task paths:

- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`
- `apps/ui-mobile/src/parent/presentation/ParentVisualPreviewHarness.tsx`
- `apps/ui-mobile/src/parent/presentation/navigation/workflowTypes.ts`
- `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx`
- `apps/ui-mobile/tests/parentFlowV1.test.ts`
- `apps/ui-mobile/tests/parentSrsBehavior.test.ts`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/IMPLEMENTATION_REPORT_SRS_REV67_UI_ALIGNMENT_20261115.md`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_17.md`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_18.md`

Do not stage or change `CONTEXT.md`, `DECISIONS.md`, unrelated paths, or any other worktree content. Do not amend, rebase, squash, or rewrite existing commits.

## Publish procedure

1. Run the repository-mandated `python tools/validate_repository_security.py` before commit/push, as required by root `AGENTS.md`.
2. Stage only the exact paths listed above and inspect the staged diff and file list.
3. Create one commit with message `fix(FEAT-081): enforce Rev67 Parent flow gates`.
4. Push `feature/fe-mobile-remediation` to `origin` without force.

## Limits

- The owner authorized publishing the completed FE changes. Addendum 33 records this authorization and supersedes Addendum 32's no-stage/no-commit/no-push restriction for this exact allowlist.
- Only the repository security validator is run under this plan. Tests, typecheck, other validators, diff-check, install, Android build, emulator, backend, network inspection/fetch, and Modal remain out of scope. The requested Git push itself is the only network action.
- No code changes, API/backend contract changes, or additional implementation are included. Do not edit the supplied SRS or repository SRS authority register.
- Preserve all previously existing commits and all user-owned worktree content outside the allowlist.
