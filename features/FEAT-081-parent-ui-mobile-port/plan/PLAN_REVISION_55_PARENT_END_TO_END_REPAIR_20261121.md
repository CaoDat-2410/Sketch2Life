# Plan Revision 55 — Parent story failure recovery and real end-to-end run

**Date:** 2026-11-21  
**Status:** Approved under the owner's direct request to keep fixing the Parent flow and continue until a real, no-quota end-to-end run works.  
**Canonical requirements:** FEAT-063 SRS v2.7-draft, §§1–31, as pointed to by `docs/context/SRS_AUTHORITY.md`.

## 1. Goal

Fix the story failure path exposed by the latest real Android UI request, prevent the model from filling every generated text field to its decoder boundary, keep loading and failure feedback clear, and complete one real Parent UI-to-Modal flow through a silent video candidate without quota or payment calls.

## 2. Evidence and diagnosis

- Reuse the existing synthetic Parent account and profile. The current StoryRun is `08657e31-ebd7-4a07-8f9b-5929b4dff23b`; its existing drawing is a synthetic turtle. Do not create or delete accounts/profiles or reseed data.
- The one authorized rewrite was sent from the real Android UI, Modal call `fc-01M7XZN3AX7PQPM0CQPQGQQJA0`. Qwen3.5-9B completed in 113.021 seconds of inference (139.739 seconds total worker time), at 12.175 tokens/sec, without timeout or token-budget exhaustion.
- Modal rejected the result with `STORY_TEXT_INCOMPLETE`: 17 fields ended without complete sentences; multiple fields reached their schema maximum (story sections 300 chars, action 180, visual prompt 240). The malformed draft shown in the UI is the prior, unconfirmed revision, not the rejected rewrite.
- The API then failed while recording the terminal worker error. `fail_story_revision` writes `updated_at` to `story.story_revisions`, but that table has no `updated_at` column. The transaction rolled back. Read-only inspection confirms the run remains `SCRIPT_GENERATING`, revision 2 remains `GENERATING`, and its idempotency receipt remains `PENDING`. Do not retry that receipt or confirm the prior draft.
- Screenshot `evidence/PARENT_LOADING_E2E_REV53_20261121/screenshots/43-story-rewrite-loading-top.png` verifies the clearer active loading card, spinner, elapsed time and no-repeat instruction. The current terminal screen still needs a clear, safe failure state.

## 3. Authorized implementation

1. **Persistence failure:** remove the nonexistent `story_revisions.updated_at` write in `fail_story_revision`; retain the existing atomic updates to revision, run and command receipt. Add a focused regression test proving a known terminal worker failure is stored and returns the provider's safe error response. Add safe SQLAlchemy diagnostics (exception class, SQLSTATE and constraint name only; never SQL parameters or generated text) if a storage failure recurs.
2. **Story generation bounds:** constrain the worker's generation-only schema to concise, complete content (story sections <=220 chars; scene action <=120; visual prompt <=160; narration <=120). Adjust prompt targets below those caps and require Vietnamese punctuation for story/action/narration. A visual prompt may be a concise English phrase without sentence punctuation, consistent with the backend contract. Preserve all scene-count, age, grounding, activity-order, language, safety and adult-review gates; do not weaken quality checks.
3. **Regression coverage:** add offline worker and backend tests for the revised bounds, valid Vietnamese completion, visual-prompt phrase handling, malformed-output rejection, and the failure-persistence column contract. Run focused tests, mobile typecheck/tests relevant to story error/loading copy, security validation and diff checks.
4. **Safe UI recovery:** show a specific Vietnamese error for terminal invalid story output; prevent confirmation of a stale/unconfirmed draft after a failed rewrite; keep the active loading state prominent and non-dismissible while waiting. Preserve the user's prior draft in history/evidence but visually label it as unavailable for confirmation when the server does not attest it as the current DRAFT.
5. **Resume-state correctness:** when the server reports a story job as `RUNNING`, `QUEUED` or `AWAITING_RECONCILIATION`, resume to the story screen with the prominent server-pending loading state. Do not render activity suggestions or enable another activity/story request, rewrite, or confirmation while that job is pending.
6. **Lifecycle recovery access:** from the pending story screen, expose a clear route to the existing Parent story history screen. Cancellation remains available only when the server summary says `can_cancel`; use its existing confirmation and authenticated UI request. Do not add a new cancellation endpoint or bypass the server capability.
7. **Current run recovery:** use the authenticated Parent UI lifecycle cancellation action for the stuck run only if the UI/API reports it cancelable. This preserves the run as a lifecycle tombstone; do not delete its account/profile or edit the database. Reuse the same synthetic profile and the existing synthetic turtle artwork from the app's media library where available. If the artwork is unavailable after cancellation, stop before creating a run and report the blocker.
8. **Real E2E:** after a healthy deploy, use only the real Android UI. Complete the existing Parent flow with one drawing inference, catalog-first activity selection and at most one activity fallback inference if the catalog is empty, one story generation plus at most one adult-directed rewrite only after a substantive fix, and one silent video candidate only after the adult confirms a valid story. Do not use visual preview harnesses, fixtures, direct AI API calls or worker `.remote()` calls.
9. **Lifecycle schema repair:** the first UI cancellation returned 503. Read-only inspection shows the task database is missing the exact `20261119_frc08_lifecycle_scope` revision and typed owner-scope columns used by the current repository. Its first upgrade attempt rolled back transactionally because the migration's operation CHECK omitted existing valid `GENERATE_ACTIVITY_SET` and `SELECT_ACTIVITY` receipts. Align the migration CHECK with the current runtime contract, add a regression test, then apply only this revision to the isolated `s2l-feat081-rev23` database. Do not use `upgrade heads` because the unrelated lesson-library head is pending; do not downgrade. Recheck Alembic current, required columns, API health, and cancellation from UI before creating a new run.
10. **Lifecycle diagnostics:** add allowlisted logging for a SQLAlchemy failure in the cancel/delete lifecycle transaction (exception class, SQLSTATE and constraint name only), reusing the existing safe diagnostic helper. Do not log SQL, parameters, receipt keys, account/run identifiers, or row content.

## 4. Limits and exclusions

- Do not call quota/payment APIs, read quota, bypass quota/admission, or weaken safety/consent/quality gates.
- No additional request is sent after timeout, uncertain dispatch or a different unexpected failure. Each additional inference requires its corresponding code fix, focused tests and healthy deployment first; no automatic retry.
- No database edits except the single forward migration explicitly pinned above; no other migrations, database writes, profile/account creation/deletion, or seed deletion. No `.env` modification, secret changes, or secret output. For the owner-authorized real UI pass only, the existing synthetic Parent seed credential may be read from the single root `.env` in process memory solely to sign into the emulator; never print, persist, attach, or include it in logs/evidence. No other secret access is allowed.
- Use only the existing language-audio Modal app and existing Parent video candidate app. Stop only task-owned Modal apps after confirming they have no live tasks. Leave unrelated apps/services alone.
- No commit or push.

## 5. Acceptance criteria

1. A terminal story-worker error updates the revision, StoryRun and idempotency receipt atomically; no 500 caused by the missing column.
2. Model output no longer needs to saturate long field limits; worker and backend agree on which fields require sentence punctuation; malformed or mixed-script prose remains rejected.
3. The real UI shows a prominent loading state and a safe terminal error, and never enables confirmation for a stale or invalid draft.
4. One real Parent UI flow reaches an adult-reviewed, confirmed story and the video candidate's actual terminal UI state, or records the first exact blocking API/worker error. No quota/payment request is made.
5. Evidence records screenshots, API status/error, Modal call IDs and timings without credentials, prompts, image bytes or raw worker output.
6. Resuming a server-pending story never routes to activity selection or permits duplicate generation; the existing history/cancel flow is reachable from the pending screen and honors server `can_cancel`.
7. The task database's lifecycle schema matches the deployed repository after the single pinned migration; the existing stuck run can be canceled through the UI and returns its lifecycle state without a generic 503.
8. The lifecycle migration accepts every operation in the current `story.command_receipts` contract, including activity suggestion and selection receipts, and retains the existing rows.

## 6. Allowed files

- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`
- `backend/src/sketch2life/contracts/schemas/ai_story.py`
- `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py`
- `backend/alembic/versions/20261119_frc08_lifecycle_scope.py`
- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx`
- `apps/ui-mobile/src/parent/presentation/components/ParentAiLoadingState.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- Focused backend lifecycle migration/repository/API tests and mobile story UI/controller tests only
- This plan, `approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `status/STATUS.md`, and `evidence/PARENT_LOADING_E2E_REV53_20261121/`


## Addendum 102 — process the exact canceled run and resume real Parent E2E

- **Status:** APPROVED by the owner's direct reply: “Cho phép worker xử lý đúng run này”.
- **Scope:** extend the prior one-run Parent E2E approval only to the exact cancellation event for run `08657e31-ebd7-4a07-8f9b-5929b4dff23b`, then continue the existing bounded fresh UI run.
- **Authorized lifecycle effect:** invoke the existing `Be1LifecycleConsumer` through a safe, one-shot worker path that is restricted to the exact run reference and its `StoryRunCancellationRequestedV1` event. Its normal lifecycle effect purges that run's story-owned content and run-owned assets/objects that are not referenced elsewhere, finalizes the run as `DELETED`, and retains the tombstone and lifecycle receipts. It must not delete the Parent account, profile, seed data, or unrelated run/event data.
- **Preflight/verification:** before claim, verify the isolated task Docker target, exact run state `DELETE_PENDING`, released active-owner lock, exact owner scope, and exactly one eligible pending event for that run. Claim only the target aggregate/event. After processing, verify the target event is delivered, the lifecycle receipt is completed, the run is `DELETED`, and no unrelated event was claimed or mutated. Stop on any mismatch or partial/unknown outcome; do not hand-edit database rows.
- **E2E continuation:** only after lifecycle completion, use the real Expo UI on `emulator-5554`, existing synthetic Parent identity/profile, and the existing synthetic turtle artwork source. Create at most one new StoryRun. Keep existing per-workload caps: one drawing inference, catalog-first activity selection with at most one fallback inference if the catalog is empty, one story inference (no rewrite), and at most one silent video candidate only after adult review and confirmation. Do not call/read/mutate quota/payment or bypass any existing admission, safety, consent, ownership, or quality gate. If the no-quota candidate path is not admitted by existing local synthetic guards, stop and report the exact gate.
- **Allowed implementation files:** `backend/src/sketch2life/application/ports/core_foundation.py`, `backend/src/sketch2life/infrastructure/persistence/outbox.py`, `backend/src/sketch2life/infrastructure/persistence/be1_lifecycle_consumer.py`, new `backend/tools/run_parent_lifecycle_once.py`, focused tests for exact aggregate claim and lifecycle worker preflight, this plan, `approvals/TASK_APPROVAL.md`, `CONTEXT.md`, `status/STATUS.md`, and `evidence/PARENT_LOADING_E2E_REV53_20261121/`.
- **Limits:** no other migration, database edit, direct SQL mutation, seed/account/profile deletion, additional run, fixture/preview harness, direct AI inference, quota/payment access or bypass, quality/safety/consent relaxation, unrelated service shutdown, commit, or push. Do not log or persist credentials, image bytes, prompts, or raw model output.
