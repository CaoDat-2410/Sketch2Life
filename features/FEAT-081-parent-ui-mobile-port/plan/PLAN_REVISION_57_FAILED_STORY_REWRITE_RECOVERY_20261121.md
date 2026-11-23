# Plan Revision 57 — Recover a quality-rejected Parent story on the same run

**Date:** 2026-11-21  
**Status:** APPROVED by owner reply “Approve Plan Rev57 (Recommended)” on 2026-11-21  
**Current product authority:** FEAT-063 canonical SRS v2.7-draft, §§1–31. Do not change the SRS until the owner approves the state-transition amendment below.

## 1. Why this amendment is needed

Revision 56's read-only eligibility check found that the existing synthetic run cannot accept the approved adult rewrite under the current backend contract:

| Evidence | Observed value |
|---|---|
| StoryRun | `b05c2b46-e760-4643-824b-b30b5387453f` |
| Run state / error / retryable | `FAILED` / `STORY_OUTPUT_INVALID` / `false` |
| Latest story revision | revision 1, status `FAILED` |
| Activity selection | persisted selection revision 1 for understanding revision 1 |
| Backend reservation rule | `reserve_story_revision` accepts only `PREPARATION_REVIEW` or `SCRIPT_REVIEW` |
| UI recovery | the history item is summary-only; home filters `FAILED` from resumable runs and shows no route back to the failed story |

The current SRS permits up to three adult-directed story rewrites (BR-13), but its StoryRun lifecycle marks `FAILED` terminal and describes rewrites only from `SCRIPT_REVIEW`. It does not say whether a deterministic story-output quality rejection may be rewritten on the same run. That product-state ambiguity must be decided before code changes or inference.

## 2. Approved state-transition amendment

**Recommended amendment:** permit a narrowly defined, adult-directed recovery from a deterministic story-output rejection on the same run. Preserve the failed revision; never replay its idempotency key; create a new immutable revision with a fresh key. Keep the existing three-rewrite maximum and every context, drawing, subject, activity, safety, consent, ownership, and quality gate.

The run may re-enter story generation only when all of these conditions hold:

1. The run is owned by the authenticated Parent and has not been deleted, abandoned, or superseded.
2. `run_state == FAILED`, `error_code == STORY_OUTPUT_INVALID`, and the latest persisted story revision is `FAILED`; provider-unknown/reconciliation, safety, consent, context, drawing, and unrelated failures remain terminal.
3. The confirmed context hash/revision, confirmed subject/understanding revision, original drawing, and persisted activity selection still match the failed revision.
4. The adult supplies a non-empty rewrite instruction and the command uses a fresh idempotency identity.
5. The backend atomically reacquires the Parent active-run lock. If another active run owns that lock, return a conflict before dispatching any AI work.
6. The failed revision remains immutable. The new attempt consumes the existing rewrite allowance; it does not bypass or reset the three-rewrite maximum. Another failure remains non-confirmable and is not automatically retried.

This requires a local SRS amendment to the StoryRun state-transition row and BR-13 clarification. It does not require a new database enum or migration if the existing `FAILED` and `STORY_GENERATING` values and constraints support the guarded transition. M0 must verify that assumption before implementation.

## 3. Proposed work after approval

### M0 — Reconfirm target and lock behavior (read-only)

- Re-read the canonical SRS, current API contract, repository transition, active-owner uniqueness constraint, and the exact existing run/revision/selection.
- Confirm no other active run holds the Parent lock and no provider outcome is unknown.
- Stop if the run identity, owner, activity binding, or current hashes do not match the evidence above.

### M1 — Record the approved product transition

- Add the narrowly scoped recovery exception to the current FEAT-063 SRS state-transition record and clarify that it counts toward the existing BR-13 rewrite cap.
- Keep all other `FAILED` causes terminal.
- Update FEAT-081 context/status with the approved decision and cross-reference this plan.

### M2 — Backend command and concurrency guard

- Extend story revision reservation only for the exact eligible failed-output case above.
- Revalidate subject/context/activity/drawing pins server-side.
- Reacquire the active-owner lock atomically before writing the new revision/outbox intent; return 409 without worker dispatch if another run owns the lock.
- Use the existing fresh idempotency identity and preserve the failed revision, prior receipts, hashes, and audit data.
- Add repository/API tests for the allowed transition, each rejected failure class, stale context/activity, missing instruction, duplicate identity, rewrite cap, concurrent active run, and retained revision immutability.

### M3 — Real Parent UI recovery

- Keep the failed run visible on Home with an explicit adult action to return to the failed story and provide a rewrite instruction. Do not route it through a new-run or photo-capture flow.
- Show the rewrite field only for the exact server-confirmed eligible failure; do not expose same-request retry or draft confirmation.
- Preserve the current synthetic run and selected activity in the current app session. If the source state is missing, use authenticated reads; never repeat drawing or activity inference.
- Add focused mobile tests for recovery routing and terminal states.

### M4 — Focused verification and one bounded live retest

- Run the repository tests, mobile typecheck/tests, security validator, and `git diff --check`; rebuild only the task API and deploy only the language/audio Modal app; verify health and no live Modal tasks first.
- Submit exactly one fresh adult-directed story rewrite from the real Android UI on the same run. No direct API/worker inference, new run/account/profile, drawing/activity repeat, quota/payment access, or gate bypass.
- If the story passes existing gates, show it to the adult. Only after adult confirmation may the conditional single silent video candidate from Addendum 103 proceed under its existing admission/safety/ownership gates.
- Stop on any failure or uncertain outcome. Capture sanitized API status, call ID, timing, and UI evidence. Stop only task-used Modal apps after verifying zero tasks; leave unrelated apps untouched.

## 4. Limits

- The owner approved this plan on 2026-11-21. Approval covers the narrow SRS/backend/UI recovery and one bounded same-run rewrite described here. No database migration, new run/account/profile, quota/payment call, or direct inference is authorized.
- No quality/safety/consent/admission gate is weakened. No raw model text, prompt, image, credential, token, or real-child data is stored in evidence.
- No commit or push.

## 5. Acceptance criteria

1. The approved SRS explicitly resolves the interaction between BR-13 rewrites and terminal `FAILED` state.
2. Only a deterministic `STORY_OUTPUT_INVALID` failed revision can use the guarded same-run rewrite path; all other failed states remain terminal.
3. Lock reacquisition is atomic and conflicts are rejected before AI dispatch.
4. The Parent UI exposes a truthful adult rewrite action for the eligible run and never exposes same-key retry or confirmation of a failed revision.
5. Offline tests pass and exactly one approved UI-driven story rewrite reaches either adult review or a fully diagnosed terminal failure.

## 6. Allowed files

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`
- `docs/context/SRS_AUTHORITY.md`
- `backend/src/sketch2life/application/ports/parent_story_runs.py`
- `backend/src/sketch2life/application/services/parent_story_runs.py`
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py`
- `backend/tests/unit/test_parent_story_revision_recovery.py` and focused contract coverage of the Parent story rewrite route/service
- `apps/ui-mobile/src/parent/presentation/screens/HomeScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx`
- focused files under `apps/ui-mobile/tests/`
- `features/FEAT-081-parent-ui-mobile-port/approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `status/STATUS.md`, this plan, and `evidence/PARENT_LOADING_E2E_REV53_20261121/`
