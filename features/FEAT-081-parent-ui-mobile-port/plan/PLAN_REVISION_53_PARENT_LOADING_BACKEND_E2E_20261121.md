# Plan Revision 53 — Parent AI loading, backend gate deployment, and real E2E

**Feature:** FEAT-081 Parent UI mobile port  
**Date:** 2026-11-21 (Asia/Saigon)  
**Status:** APPROVED by the owner’s direct request in this conversation  
**Branch/worktree:** `feature/fe-mobile-remediation`, under the repository’s FEAT-081 worktree  
**Canonical requirements:** FEAT-063 v2.7-draft, amendments through Rev71, especially §§7.2, 7.4, 21.5, 31.20–31.21. The SRS remains unsigned.

## 1. Goal

Continue the Parent workflow from the real Android UI, fix the backend/Modal activity text defect already found, make long-running AI waits unmistakable in the UI, deploy those changes to the task API and Modal dev app, then run one fresh synthetic Parent workflow without using quota endpoints. Use real APIs and Modal outputs; no preview harness, fixture response, or direct API/worker bypass.

The previous run has an invalid persisted activity suggestion set. Preserve it for evidence. Do not select it, repair it in the database, or reuse it for story/video. Start one new StoryRun from the real UI under the existing synthetic Parent/profile.

## 2. Observed baseline / M0

- Worktree branch is `feature/fe-mobile-remediation`; the worktree contains broad pre-existing changes. Edit only the files listed in §4 and preserve all unrelated work.
- Task API health at `http://127.0.0.1:58100/health` returns HTTP 200.
- Android emulator `emulator-5554` is online through `D:\AndroidStudio\platform-tools\adb.exe`.
- Modal `dev` currently lists `sketch2life-srs23-language-audio-dev` deployed with one task, `sketch2life-srs23-drawing-vlm-dev` deployed with zero tasks, and `sketch2life-srs23-dev-video` deployed with zero tasks.
- The prior StoryRun is at `PREPARATION_REVIEW`, with a successful activity job, one persisted `AI_GENERATED_FALLBACK` set, and no selected activity. Its cards show truncated Vietnamese sentence tails. The prior activity inference has already been consumed; it will not be repeated.
- Screenshot evidence: `evidence/PARENT_BACKEND_FRONTEND_FIX_E2E_20261121/screenshots/parent-activity-wait.png` shows only a small/blank busy button and stale empty-state copy while the call is running; `parent-activity-result.png` shows the malformed persisted result.

## 3. Implementation work

### M1 — Make AI waits clear and truthful on Parent Android

Add one reusable presentation component for a prominent, accessible, indeterminate AI wait state. It must use the existing Parent palette, a visible spinner/illustration, a clear title and explanatory copy, elapsed wall time, and a no-duplicate-request reminder. It must not invent a percentage or claim a backend phase that the API does not report. Elapsed time is local display only and must reset when a request ends.

Apply it to the Parent drawing-analysis, activity-suggestion, and story-generation waits. The activity screen must not show “Chưa có gợi ý / Hãy thử lại” while the request is still pending, and it must not replace the button label with a blank bar. The story screen must show a loading state before any failed/unknown-result retry copy. The capture screen must show that the selected drawing is being analyzed and prevent another analysis action until the current request resolves.

Pass the actual story operation (`generating`, `rewriting`, or `confirming`) from the Parent controller to the story screen so the status text matches the action in progress.

Keep the existing video candidate phases derived from server states. Improve only the request-dispatch/loading presentation if visual review finds it weak; no fake percentage or fabricated progress stage. Make controls/accessibility state accurately reflect `busy`.

Map a backend `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` response to concise Vietnamese copy that says the server discarded the invalid suggestion and did not save selectable activities. Any further request remains an explicit adult action; no automatic retry.

### M2 — Deploy and verify the backend/worker quality fix

Keep the current backend and worker corrections:

- Worker rejects obvious incomplete Vietnamese sentence tails before returning a fallback; structured sentence output has a separate body and terminator, with body limits leaving room for punctuation.
- Backend fallback quality gate applies the corresponding conservative sentence-tail check before persistence. A rejection fails the suggestion set with safe code `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` and diagnostic `ACTIVITY_TEXT_INCOMPLETE`; the invalid activity list must not become selectable or be persisted as a successful set.
- Catalog-selected published/shared teacher content is unchanged. Catalog lookup remains first; AI generates exactly three drafts only when no eligible candidates exist.

Deploy only `sketch2life-srs23-language-audio-dev` in Modal `dev` and rebuild only the task `api` service using the existing Compose configuration, preserving the current database and volumes. Do not migrate, reseed, reset, or edit `.env`/credentials. Confirm `/health`, mounted Parent activity route, Modal app deployment, and safe diagnostics without printing environment values or model/user content.

## 4. Expected source/evidence paths

Allowed source files for M1/M2:

- `apps/ui-mobile/src/parent/presentation/components/ParentAiLoadingState.tsx` (new reusable component)
- `apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/ActivityScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/StoryScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/ParentExpoApp.tsx` for the current story-operation status
- `apps/ui-mobile/src/parent/presentation/screens/VideoCandidateScreen.tsx` only if needed by visual review
- `apps/ui-mobile/src/parent/presentation/navigation/parentFlowV1.ts` for safe quality-gate error copy
- focused mobile tests for the loading states and error mapping
- `backend/src/sketch2life/application/services/parent_activity_suggestions.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- focused backend/worker tests for completeness and rejection-before-success
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py` for bounded worker terminal-log collection and allowlisted typed activity failures
- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py` for safe Parent activity failure mapping
- focused tests in `backend/tests/unit/test_modal_story_function_client.py` and `backend/tests/contract/test_parent_ai_late_result_guards.py`

Evidence and records:

- `evidence/PARENT_LOADING_E2E_REV53_20261121/RUN_REPORT.md`
- `evidence/PARENT_LOADING_E2E_REV53_20261121/screenshots/` for actual Android workflow checkpoints and AI outputs only
- append one dated result to `features/FEAT-081-parent-ui-mobile-port/status/STATUS.md` and `CONTEXT.md`

No SRS, database migration, Compose configuration, auth/account, SVG dataset, teacher flow, or unrelated UI changes are included.

## 5. Real E2E sequence and limits

Use ADB and the actual installed Expo app from this worktree. Reuse the existing authenticated synthetic Parent account, profile, and the existing synthetic turtle drawing source through the normal picker. Do not register accounts or create profiles. Create at most one new StoryRun through the UI; preserve the old failed run.

If the prior malformed run still holds the profile's active-run lock and prevents creating the one new run, close only that exact run through the existing authenticated Parent UI lifecycle action. The supported transition must retain its StoryRun, suggestion snapshot, assets and receipts; do not delete or edit database rows. If that lifecycle action is unavailable or does not preserve the run, stop and report the blocker rather than bypassing the lock.

Run the normal topic/subject → drawing analysis → adult subject/context confirmation → catalog query → activity suggestion → adult main-activity selection → story generation/review path. If the story is accurate, age-appropriate, follows the selected activity, and passes the existing adult review, confirm it in the synthetic test account and continue to the current Parent video candidate UI. Submit at most one video candidate and inspect the result only through the UI.

Bounded AI dispatch budget for this authorization:

- One drawing inference.
- Up to two activity fallback inferences total on the new run. A second is permitted only after the first is definitively rejected by the new quality gate and only after inspecting logs/output diagnostics; no retry after timeout, network uncertainty, accepted-but-unconfirmed Modal dispatch, or unknown outcome.
- One story inference; no rewrite/regeneration.
- At most one silent video candidate inference, only after adult story confirmation and all existing video/admission/safety gates. No retry after accepted or uncertain dispatch.
- Topic/subject catalog calls may use the real mounted endpoints. Do not invoke extra AI workloads unrelated to the selected standard catalog topic.

Quota handling: do not call, read, mutate, or purchase through quota/payment APIs. The task may use only the existing local/test synthetic video-candidate configuration previously authorized in Addendum 80; do not weaken guards or bypass production quota/safety policy. If the candidate path cannot run under existing synthetic-dev guards without a new policy change, record the blocker and stop.

No real child data, fabricated consent, direct business-DB edits, direct API/worker bypass, gate relaxation, secret output, seed deletion, or changes to other Modal apps. Keep the malformed previous activity set unchanged. No commit or push.

## 6. Acceptance criteria

1. During each synchronous AI wait, emulator screenshot shows a large/high-contrast indicator, meaningful Vietnamese status copy, elapsed time, and disabled duplicate action; no fake percentage or stale empty/error copy is present.
2. Video waiting uses actual candidate states and visibly distinguishes request dispatch from later server progress.
3. Focused worker/backend tests prove the observed incomplete outputs are rejected before a successful suggestion response/persistence; the normal catalog selection path remains unaffected.
4. The deployed Modal worker and task API report healthy/available; API health remains HTTP 200.
5. Real UI E2E logs correlation IDs, Modal call IDs, elapsed times, catalog counts, and final states without recording raw credentials, image data, or personal data.
6. If activity quality, story review, candidate, safety, or any required state gate fails, stop at that state and report it; do not claim full E2E success.
7. Save the report and screenshots under the feature-owned evidence path. Do not commit/push.

## 7. Rollback and cleanup

If the new UI changes fail typecheck/tests, revert only this task’s edits in the files listed in §4; preserve all unrelated worktree changes. If a worker deployment fails, leave the last known deployed app unchanged where possible and do not issue an AI request against a partially deployed worker. Preserve the existing synthetic account/profile/run. After the bounded run, stop only the Modal dev apps used by this task if they have no other active task; do not stop unrelated apps or Docker services.

## 8. Verification commands

- Mobile: focused component/screen tests, `pnpm --dir apps/ui-mobile typecheck`, then the mobile test suite.
- Backend/worker: focused Parent activity service/route and Modal parser/workload tests.
- Runtime: API `/health`, Modal `dev` app status, and one actual UI-driven request per authorized workload; no fixture/mock E2E.
- Final hygiene: `git diff --check`; report whether repository security validation passes and any pre-existing finding. No commit/push is planned.

## 9. Narrow continuation after the observed activity rejections

Three activity inferences on StoryRun `08657e31-ebd7-4a07-8f9b-5929b4dff23b` have now completed with definitive worker failures: the first two returned `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT` at `fallback_activities[0].objective` (104,741 ms and 116,124 ms); the third returned the same code at `fallback_activities[1].instructions_text.first_sentence` after 70,607 ms. All workers finished; none was a timeout or uncertain dispatch. Generated text and image/prompt content remain unlogged.

Before using a further permitted activity inference:

- Shorten generated fallback sentences further at the schema boundary (objective <=32 chars, preparation <=42, each instruction sentence <=32, safety <=42); preserve sentence punctuation, Vietnamese-language validation, age/topic/safety checks, exact three-activity requirement, and all existing quality gates.
- Tighten prompt instructions to simple sentence forms (`Trẻ + action + object` for objective; adult preparation and supervision stated directly), with short Vietnamese examples and an explicit ban on dangling clause endings. Do not accept or repair incomplete output, fabricate fallback text, change catalog-first selection, or relax the gate.
- Record only a safe tail reason category and character count for a rejected sentence field; never record generated text. Collect this worker diagnostic through the backend's allowlisted Modal event parser.
- For `parent.activity.suggest` only, give terminal Modal logs a bounded 10-second indexing window after a definite `call.get()` failure and preserve only allowlisted worker output-quality error codes. Do not retry or redispatch as part of log collection.
- Map the exact worker failure `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT` to API code `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` with safe diagnostic `ACTIVITY_TEXT_INCOMPLETE`, so the existing Vietnamese UI message is shown. Keep other worker/infrastructure failures distinguishable and do not mislabel them as quality rejection.
- Add focused parser/schema, typed-error, and API-mapping tests. Deploy only the language-audio Modal app and rebuild only task API as stated in §3.
- A further activity inference is allowed only after those changes pass focused tests and runtime health checks. It must be submitted from the real UI for the same StoryRun. If it times out or has uncertain dispatch, stop; do not retry it. Story and video limits in §5 remain conditional on the activity being accepted and selected through the UI.

This continuation is limited to the current synthetic run and the exact worker error above. A further activity inference may only be dispatched from the real UI after a substantive prompt/schema correction, focused test pass, and healthy deploy. Do not retry after timeout, network uncertainty, accepted-but-unconfirmed dispatch, or any failure other than this exact text-completeness rejection. All §5 data, account, quota, safety, candidate, and no-commit limits remain in force.

## 10. Continued owner-directed repair after the second rejection

The owner reiterated: continue fixing until the Parent workflow reaches end-to-end completion; quota/payment management is not a blocker. This supersedes the one-extra-inference cap in Addendum 92 only for definitive `MODAL_MODEL_OUTPUT_INCOMPLETE_TEXT` rejections on the same synthetic run. One of the three further inferences authorized by this section has now been used; two remain.

- Apply one new, substantive generation correction and verify it with focused tests before each UI inference. Allow at most three further activity fallback inferences total (five total including the two already consumed). Never auto-retry; each is one visible adult action through the Android UI. Stop immediately after an accepted activity set, any timeout/unknown outcome, or any different terminal error.
- Once an activity set is accepted, select one activity through the UI, run one story generation and the adult review, then submit at most one silent video candidate if the story is approved and all existing gates pass. No story rewrite or video retry.
- Keep catalog-first behavior, incomplete-text rejection, all age/safety/consent/admission controls, and the no-quota-API rule unchanged. Preserve every failed run/suggestion snapshot and never bypass the UI or edit business data.
