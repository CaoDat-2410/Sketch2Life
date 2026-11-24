# FEAT-081 — Plan Revision 40B: make Parent fallback copy user-safe

- **Status:** APPROVED under the owner's continuing 2026-11-20 request to keep fixing the real Parent workflow.
- **Parent plan:** Plan Revision 40/Addendum 64. The real activity set is already generated and persisted; this amendment does not authorize another activity inference.
- **Product authority:** FEAT-063 v2.7-draft, §§1–31; Parent activity fallback remains an adult-reviewed AI draft.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>

## 1. Evidence

- The one approved real UI activity request succeeded: catalog counts were zero, Qwen returned `NO_MATCH` with three fallback drafts, and the backend persisted all three.
- The UI renders the model's `no_match_reason` in every fallback activity card. It currently contains the internal field name `candidate_activities`; this exposes implementation language to the Parent/child and is unsuitable product copy.
- Result screenshot: `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/36-rev40-activity-result.png` and scrolled result `37-rev40-activity-result-scroll.png`.

## 2. Goal and implementation

- For `AI_GENERATED_DRAFT` activities, do not render the model-authored `match_reason` on each card.
- Replace the fallback-mode description with one short, stable Vietnamese explanation that says no suitable library activity was found and these are AI drafts for an adult to review. Do not mention `candidate_activities`, IDs, filters, model, prompts, or other implementation details.
- Keep catalog-match explanations, API contracts, persisted data, selection behavior, and all activity quality/safety rules unchanged. Do not regenerate the suggestion set.

## 3. Verification and continuation

- Run `pnpm --dir apps/ui-mobile test` and `pnpm --dir apps/ui-mobile typecheck`.
- Use the running Expo Fast Refresh on `emulator-5554` to verify the existing persisted three-card response no longer shows the technical wording; capture before/after UI evidence.
- Continue with one real selection and persistence from the already saved result, then one story request and adult review only under Plan Revision 40's existing unconsumed approval. This amendment adds no Modal inference allowance. Stop at the story review screen; video is conditional on its exact earlier authorization and all previous gates.
- No fixtures, mocks, new AI activity request, new account/profile/run/drawing, direct API/worker call, direct database edits, migration, quota/payment change, `.env`/secret/SRS change, unrelated service shutdown, commit, or push.

## 4. Exact file boundary

- `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx`
- `apps/ui-mobile/tests/parentSrsBehavior.test.ts`
- `features/FEAT-081-parent-ui-mobile-port/plan/PLAN_REVISION_40B_PARENT_ACTIVITY_FALLBACK_COPY_20261120.md`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`
- `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md`
- `features/FEAT-081-parent-ui-mobile-port/evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/`
