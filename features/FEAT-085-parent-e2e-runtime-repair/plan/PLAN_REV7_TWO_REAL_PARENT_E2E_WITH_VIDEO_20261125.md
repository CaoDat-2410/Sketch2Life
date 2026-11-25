# Plan Rev7 — two real Parent E2E runs with generated drawings and video

**Status:** APPROVED by the project owner's direct request on 2026-11-25.

## Objective

Repair the current root `dev` checkout's real Parent path and complete exactly two Android-emulator end-to-end runs. Each run must use a distinct topic and a separately generated synthetic drawing in a child-drawn/crayon style, pass the real backend and deployed Modal AI pipeline, produce an adult-reviewed story and a playable video, and preserve the resulting script, video, timings, and diagnostic evidence for the owner.

## Canonical behavior

- Use only the current FEAT-063 SRS named by `docs/context/SRS_AUTHORITY.md`; local feature reports are evidence, not product authority.
- Keep the required Parent order: consent/profile/context; optional topic or lesson and optional SVG guide; required drawing upload; VLM analysis and adult subject confirmation; one required activity choice before story; story generation/review; normal video admission and generation; safety/technical validation; playback.
- Use the current SVG guide/catalog implementation. Do not revive FLUX or make video/audio calls with the child's drawing beyond the existing contract.
- Use LTX-2.5 video pipeline and the configured Qwen 3.8 story/activity workers where those are the deployed current Modal versions; record actual model IDs/revisions from runtime evidence.

## Scope

1. Diagnose and repair only failures on the root-checkout Parent workflow and its isolated FEAT-085 API/Modal path. This includes the confirmed backend startup import mismatch (legacy FLUX provenance referenced by Parent AI route after FLUX removal), the missing drawing upload route in the task API image, and any UI error/loading/capture defect that blocks the two runs.
2. Keep upload, scan, storage, authentication, consent, profile scope, parser/schema, activity quality, adult review, video admission/quota, and video safety gates enabled. No gate bypass, direct database edits, fake responses, preview harness, fixture, or mocked AI.
3. Use the existing synthetic Parent account/profile and current in-progress run when valid; create only the second run and necessary synthetic test records. Generate two distinct child-style drawings, one per run, and import them into Android MediaStore through ADB. Select and submit them through the real Expo UI.
4. Complete two distinct real topics (first the topic bound to the existing drawing/run if still valid; second a different everyday topic and new generated drawing). For each, run actual drawing recognition, activity catalog/suggestion and selection, story generation and adult confirmation, video generation, safety/technical completion, and playback. If a product or infrastructure error occurs, capture its safe diagnostic, fix it, then use only the recovery action allowed by the current StoryRun state and idempotency contract.
5. Capture topic, subject, selected activity, confirmed story text/storyboard JSON, model/call IDs, per-stage elapsed time, video metadata and playable MP4, UI screenshots, and sanitized backend/Modal logs under `evidence/ANDROID_PARENT_TWO_E2E_20261125/`.
6. Verify runtime API routes and health before sending inference. Rebuild only the FEAT-085 API service with the existing project/volumes and `--no-deps` if required. Start only the Modal apps needed for drawing/story/activity/video; do not send warm-up or duplicate inference requests. Stop task-started Modal apps after both runs and verify task containers are stopped or healthy as intended; preserve model volumes and unrelated services.
7. Update FEAT-085 context, decisions, source register, and status with results and limitations. Do not commit or push.

## Acceptance criteria

- Root checkout `dev` is used; no `.codex-worktrees` checkout is started or modified.
- Two distinct Parent runs complete on Android through the real UI, with different topics and different independently generated child-style drawings.
- Each run has a recognized/confirmed subject, a selected activity, an accepted adult-reviewed script, and a newly generated video that passes the configured gates and plays in the Android UI.
- Artifacts include both original synthetic drawings, both final scripts/storyboards, both video files, runtime model/call/timing evidence, screenshots, and sanitized logs.
- No fixture/mocked response, quota/admission/safety bypass, credential disclosure, destructive seed cleanup, commit, or push.

## Stop conditions

- Stop the affected run on terminal worker/provider failure, safety rejection, unresolved identity/consent mismatch, uncertain outcome, or failed admission. Record the stable error and do not issue an automatic duplicate request.
- Do not silently weaken quality or safety gates. A needed policy change requires a separate owner decision.
- Do not change/delete existing users, profiles, consent, or unrelated database rows to force completion.

## Addendum B — align the generic upload schema used by the Parent UI

**Status:** Approved under Addendum 10's direct authorization to repair all blockers and complete two real Parent E2E runs.

**Observed failure:** The real UI's `POST /v1/upload-sessions` returned HTTP 503 before any drawing bytes or AI request were sent. The API's `core_upload_sessions` ORM expects nullable `organization_id`, `owner_scope_kind`, `owner_scope_ref`, and scan/validation columns, while the isolated task DB still had the older Lesson Library schema (`organization_id NOT NULL`; those columns absent). The endpoint converted the resulting database exception to generic `PROVIDER_UNAVAILABLE`, obscuring the migration mismatch.

**Approved scope:** Verify the migration's affected records and run only `20261119_uf_0001` (the generic upload typed-scope migration) against the isolated FEAT-085 database. Do not upgrade unrelated Alembic heads. Verify expected columns/constraints and no change to existing upload rows. Make the mobile upload orchestration classify a 503 from the upload-session-create stage as a typed pre-dispatch failure, show a clear one-time retry, and preserve the same idempotency keys. Add focused regression tests. Then retry the same active StoryRun via the Android UI once; the failed create request committed no upload session. Record safe SQLSTATE/error class and request timing without printing values, SQL parameters, credentials, or image bytes.

**Preservation:** No direct DB row edits/deletes, run recreation, duplicate AI request, fixture, or gate bypass. Preserve all existing users, profiles, consent, run state, data-service volumes, and unrelated containers. Stop on a terminal result or uncertain upload outcome; no commit or push.

**Acceptance:** `POST /v1/upload-sessions` succeeds from the real UI with the expected upload contract; the uploaded bytes are scanned and stored before any drawing inference; the run advances according to its existing state machine.

## Addendum 13 — compose the real Modal workers into the Parent StoryRun pipeline

**Status:** Approved by the project owner's direct instruction to fix all blockers and complete two real Parent end-to-end runs, including real Modal AI and video; this amendment narrows that work to a confirmed runtime omission.

**Observed failure:** The authenticated Android UI uploaded and attached the synthetic butterfly successfully (`POST /v1/upload-sessions` 201, part 200, complete 202, `POST /v1/story-runs/{id}/assets` 202). The run remains in `INPUT_PROCESSING`; the FEAT-085 API has no drawing-analysis worker call and Modal reports zero active tasks. Source inspection confirms `app.py` explicitly sets `application.state.drawing_analyzer = None` and `story_generator = None` unconditionally, even when the isolated local API uses `ai_provider=modal_dev`; the attach route therefore accepts the artwork but schedules no analyzer. This is the reason the UI spinner never completes.

**Approved scope:** Implement provider adapters for the existing `DrawingAnalyzerPort` and `StoryGeneratorPort` using the pinned current Modal drawing and story functions. Compose them only when `env` is `local` or `test` and `ai_provider` is `modal_dev`; keep provider-disabled/test fixture defaults unchanged. The drawing adapter must read only the attached normalized asset, verify media type/size/SHA-256 against the server-owned request, preserve the Modal input/output contract, map known terminal failures to recoverable drawing errors and unknown outcomes to reconciliation, and never log image bytes or content. The story adapter must pass only the reserved server-owned worker input through `ModalStoryFunctionClient`, preserve Qwen model/call provenance, and map terminal/unknown outcomes to the existing port errors. Add focused tests and runtime wiring coverage.

For the already attached run, add one authenticated, idempotent recovery path that can schedule the queued analysis after the adapter is enabled. The repository's existing compare-and-set `start_drawing_analysis` is the dispatch guard; replays must not start a second Modal call once the job is RUNNING, terminal, or unknown. Do not reupload or create a replacement run. Rebuild only the FEAT-085 API service, then continue from the same Android UI state and preserve existing upload/scan/consent/safety/admission behavior.

**Preservation:** No fixture/mock response in E2E, direct database writes, run/profile/consent deletion, duplicate inference after an uncertain outcome, unrelated migrations/containers, policy or quality-gate weakening, quota/admission bypass, credentials in logs, worktree, commit, or push.

**Acceptance:** The attached run advances from `INPUT_PROCESSING` only after a real Modal drawing result or a classified failure; the same API runtime composes the real Qwen story worker for the subsequent normally reserved story. Offline contract tests pass, deployed Modal app task/call evidence is captured, and all E2E actions remain on the Android UI.

## Addendum A — preserve parallel Story receipt operations during schema upgrade

**Status:** Approved under the project owner's direct request to fix all Parent E2E failures and complete two real runs (2026-11-25).

**Observed failure:** Applying the approved StoryRun video/review migration chain stopped transactionally at `20261120_b1_0001`: its replacement `ck_story_receipt_operation` omitted `GENERATE_ACTIVITY_SET` and `SELECT_ACTIVITY`, which already exist in retained synthetic receipt rows from the parallel Parent activity branch. PostgreSQL rejected the new check; no rows were modified.

**Scope:** Correct the unapplied StoryRun migration check sets and ORM check to preserve the union of existing Parent activity, story, and video operations through B1, VB2, and AS1. Add a regression assertion for the retained operation values. Apply only the Parent StoryRun/activity/video migration heads needed by this E2E task. Preserve all receipt rows and existing run state; do not bypass gates, edit DB rows, or alter unrelated migration branches.

**Acceptance:** The migration chain upgrades successfully with every pre-existing operation value still accepted; ORM and migration check sets agree; the active Parent run can be read through the authenticated API before any new run or inference is started.
