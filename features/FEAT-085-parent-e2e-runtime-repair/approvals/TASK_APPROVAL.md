# FEAT-085 task approval

## Plan Rev1 — Parent real E2E runtime repair

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in this conversation (2026-11-23): fix the unresolved Parent runtime and rerun the full end-to-end flow.
- **Approved scope:** The sequence, boundaries, focused source areas, synthetic-only data, real Expo/Backend/Modal execution, and evidence requirements in plan/PLAN_REV1_PARENT_E2E_RUNTIME_REPAIR_20261123.md.
- **Runtime authorization:** Start/restart the Android emulator and Metro; use existing synthetic Parent credentials privately from the ignored root .env; use healthy local Docker services; call real Modal AI/video workloads as needed, minimizing retries; create only synthetic data if a required record is absent.
- **Safety constraints:** No real-child data; never expose credentials/tokens; do not delete existing seed accounts or unrelated data; do not bypass auth, consent, schema, safety, or video admission; do not stop Docker services that were already running.
- **Delivery constraints:** No commit or push requested.

## Addendum 1 — current-branch backend runtime

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in this conversation (2026-11-23) to fix the blockers and complete the real Parent E2E.
- **Approved scope:** Build and run the backend from the active `feature/fe-mobile-remediation` worktree on an unused local port with a fresh isolated synthetic database and storage volumes. Apply this branch's current Alembic heads to that fresh DB. Update only the API URL value in the existing root `.env` after the new backend passes health and route checks.
- **Preservation:** Do not stop/recreate existing API containers, alter older database volumes, print or replace credential values, create extra `.env` files, or bypass identity/consent/schema/safety/admission gates.

## Addendum 2 — use the newly selected Modal workspace

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction on 2026-11-23: “chạy đi, vừa đổi modal workspace”, followed by authorization for full runtime access and instruction not to use Computer Use.
- **Approved scope:** Use the selected local Modal profile `hieuptse184252` for this task. The project `.env` and running FEAT-085 API currently resolve to `anhkhoa14155`, whose workspace returns `workspace ... is disabled`; the selected profile has no deployed apps or model volumes. Provision only the resources required to complete this Parent E2E in the selected `dev` environment: model/scratch volumes, the language/audio app for Qwen3.8 Parent activities/story, and the video app for the pinned LTX-2.5 candidate. Stage the pinned checkpoints through the existing Modal download functions and use the existing `huggingface-secret`; do not use FLUX or send narration.
- **Runtime handling:** Keep the existing root `.env` credential values unchanged. Pass the selected profile credentials only to the task runtime in memory, without printing or persisting them. Recreate only the isolated FEAT-085 API container if needed to use that profile. Do not recreate/stop unrelated services.
- **E2E boundaries:** Resume the existing synthetic run through the Android UI. Make at most one new request for each workload after the current deployment is ready. Keep authentication, consent, schemas, parser, quality, safety, and video admission gates enabled; no quota/payment bypass. Do not delete the run or seed account. Capture sanitized logs and UI evidence in this feature folder. No commit or push.

## Addendum 3 — repair the current activity output failure

- **Status:** APPROVED
- **Approver:** Project owner, standing direct instruction in this conversation to fix runtime bugs and continue until a video is generated, most recently “thử lại đi” (2026-11-23).
- **Observed failure:** The single activity inference on the newly selected workspace completed without timeout (Qwen3.8-27B-FP8, 1,949 output tokens, 356,234 ms), but the worker rejected only `fallback_activities[2].preparation_text` with safe reason `dangling_word`; API request `e9c0e399-88be-4fa4-b8ed-dcb53a246f22`, Modal call `fc-01M84DC0GTJ3P44TRAJ2C0WHD3`, run `c8ab4140-739e-496f-8b11-1c58e4a857a3`.
- **Approved scope:** Make a narrow prompt-only repair to require a short, complete preparation sentence that ends with its actual action/object rather than a dangling Vietnamese connector; add focused prompt-contract coverage; run the relevant offline checks; deploy only the language/audio app; then make one fresh Parent UI activity request for this existing synthetic run.
- **Preserved gates:** Do not weaken parser completeness, output schema, backend quality, outdoor setting, age, child-agency, adult-support, safety, privacy, authorization, or admission rules. Do not repeat drawing or delete/reseed the run. No new story/video request until the activity set is accepted. No commit or push.

## Addendum 4 — align child-agency recognition with explicit inquiry actions

- **Status:** APPROVED
- **Approver:** Project owner, standing direct instruction to fix the Parent E2E until video works, reiterated in the current conversation with “thử lại đi”.
- **Observed failure:** The second real activity request completed Qwen3.8 generation and worker parsing (1,555 tokens; 416,357 ms inference; 4,884-byte JSON), then the backend returned `PARENT_ACTIVITY_QUALITY_GATE_REJECTED` / `CHILD_AGENCY_NOT_EXPLICIT`. Request `82a93aeb-acdf-4e41-b67b-db7cee089d20`, Modal call `fc-01M84E2W0BZ61DN3H5TC0JFAC7`, run `c8ab4140-739e-496f-8b11-1c58e4a857a3`. Generated text is not retained, so this finding does not establish whether wording was absent or merely outside the matcher.
- **Approved scope:** Extend the backend matcher only to recognize explicit affirmative child-subject inquiry actions already covered by the separate exploration vocabulary (look closely, follow, listen, notice/discover, count, record, ask questions, and equivalent current markers). Require an explicit child actor and reject negated actions. Align the Qwen prompt with the accepted examples. Add focused positive and negative tests; run relevant offline checks; rebuild only the isolated FEAT-085 API and redeploy only the language/audio Modal app; then make one fresh activity request through the Android UI for the existing synthetic run. Update the task-owned API launcher to require the selected Modal profile and pass its credentials from local Modal CLI config into Compose memory only, without changing the shared `.env` or printing values. If accepted, continue the normal story review and video path under existing gates.
- **Preserved gates:** Do not infer the unseen generated text or weaken child agency, exploration, outdoor setting, adult support, age, context, safety, privacy, authorization, schema, parser, or video admission. Do not repeat drawing, delete/reseed the run, issue duplicate requests, bypass quota/admission, or commit/push. If another predicate fails, record its safe diagnostic before any further repair.

## Addendum 5 — repair root Expo startup and auth config

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction on 2026-11-24: “V THI GUI T LENH CHAY CAI MOI DI” and “KO CHAY WORKTREE DO”, followed by the root `apps/ui-mobile` startup error transcript.
- **Approved plan:** `plan/PLAN_REV2_ROOT_EXPO_STARTUP_AND_AUTH_CONFIG_20261124.md`.
- **Approved scope:** Modify only the main `<LOCAL_ROOT>` checkout's `apps/ui-mobile` dependency and root `pnpm-workspace.yaml`/`pnpm-lock.yaml` as needed to align all Metro packages directly imported by the Expo 52 adapter to 0.81.5 and declare the SDK-compatible dev client. Preserve the existing root `app.config.js` and `.env` reader unchanged. Stop only a verified old Metro process serving `.codex-worktrees\fe`; do not launch or modify that worktree. Verify the root Expo config and startup path, then give the owner the root PowerShell command.
- **Preservation:** Do not print or change `.env` values, bundle private credentials, touch Firebase accounts/backend data/Docker/Modal, modify unrelated dirty files, commit, or push.

## Addendum 6 — align the Parent Metro runtime for Android HMR

- **Status:** APPROVED
- **Approver:** Project owner, direct request “Bug này” with Android screenshots showing the 16 KB compatibility notice and `HMRClient.setup()` development-client failure (2026-11-24).
- **Approved plan:** `plan/PLAN_REV3_ANDROID_HMR_RUNTIME_ALIGNMENT_20261124.md`.
- **Approved scope:** Add exact `metro-runtime@0.81.5` to the root Parent app tooling dependencies, update pnpm lockfile, verify Metro resolution and reload the root Android development build while checking HMR logs.
- **Preservation:** Do not run or modify `.codex-worktrees\fe`; do not change Expo/RN version, native ABI, `.env`, Firebase/backend data, quota, or AI flows; do not commit or push. Treat the 16 KB notice as a separate compatibility issue and document it accurately.

## Addendum 7 — correct Android Babel helper resolution

- **Status:** APPROVED
- **Approver:** Project owner, direct request “Bug này” with Android screenshots of the startup failure (2026-11-24), continuing the approved request to repair both reported screens.
- **Observed cause:** After Metro runtime alignment, clean logcat exposed `_interopRequireDefault is not a function (it is Object)`. The bundle maps the CommonJS helper request to Babel Runtime's ESM helper file. Expo SDK 52 globally enables both `require` and `import` export conditions, while Metro also selects the syntax-specific condition per dependency.
- **Approved plan:** `plan/PLAN_REV4_ANDROID_HMR_ESM_CONDITION_FIX_20261124.md`.
- **Approved scope:** In the main checkout only, clear the global Metro resolver condition list in `apps/ui-mobile/metro.config.js`, preserve its platform-specific conditions and the Metro 0.81.5 pins, rebuild the bundle, launch the existing emulator app, and capture the result.
- **Preservation:** No dependency downgrade, Expo/RN/native ABI change, `.env`/Firebase/backend/AI/Modal change, worktree use, commit, or push. Keep the 16 KB warning explicitly separate.

## Addendum 8 — fix the Parent post-login safe-area crash

- **Status:** APPROVED
- **Approver:** Project owner, direct request on 2026-11-24 to inspect the post-login bug logs and fix it.
- **Confirmed failure:** Firebase sign-in and backend Parent-scope resolution both succeeded; rendering then failed because `ParentBottomBar` calls `useSafeAreaInsets()` without a root `SafeAreaProvider`.
- **Approved plan:** `plan/PLAN_REV5_POST_LOGIN_SAFE_AREA_PROVIDER_20261124.md`.
- **Approved scope:** Wrap the root Parent app in `SafeAreaProvider` in `apps/ui-mobile/App.tsx`, then verify the existing emulator's authenticated screen and sanitized logs.
- **Preservation:** Do not change credentials, Firebase/backend records, API contracts, auth flow, worktree, or commit/push.

## Addendum 9 — resume the real Parent drawing upload on Android

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction on 2026-11-25 to put the generated child-drawn butterfly into the emulator and run the Parent flow to diagnose the capture step, under the already-approved real Parent E2E scope in Plan Rev1 and Addendum 2.
- **Observed cause:** The current task API accepts run creation but returns `404` for `POST /v1/upload-sessions`; its image lacks the upload-session router present in the root source. Thus no image bytes or drawing inference have reached the worker.
- **Approved plan:** `plan/PLAN_REV6_PARENT_DRAWING_UPLOAD_RUNTIME_FIX_20261125.md`.
- **Approved scope:** Rebuild/recreate only the FEAT-085 API container from the root checkout with the existing Compose project and `--no-deps`; preserve all data services, volumes, root `.env`, Modal apps and unrelated containers. Verify route health, then continue the same authenticated run and selected synthetic image from Android once.
- **Preservation:** Do not create another run, repeat inference after a terminal result, bypass quota/safety/admission, change credentials or seed data, run migrations, change UI/source code, stop unrelated services, or commit/push. Do not expose auth tokens or child data.

## Addendum 10 — two real Parent E2E runs with video

- **Status:** APPROVED
- **Approver:** Project owner, direct request on 2026-11-25: “chạy và fix tất cả lỗi đi … chạy 2 lần e2e ko lỗi, 2 lần chạy khác chủ đề nhau, 2 tranh gen theo kiểu trẻ vẽ … đủ 2 run”.
- **Approved plan:** `plan/PLAN_REV7_TWO_REAL_PARENT_E2E_WITH_VIDEO_20261125.md`.
- **Scope update:** This direct request supersedes Rev6/Addendum 9's temporary “no video / no source change / one existing run only” restrictions for this task. It authorizes the scoped Parent API/UI fixes, two distinct generated synthetic child-style drawings, two real Android UI-to-backend-to-Modal Parent runs including normal video generation and playback, and saving scripts/videos/runtime evidence.
- **Preservation:** Keep authentication, consent, upload scanning, schema/parser, activity quality, adult review, quota/admission, technical/safety gates enabled. No fixtures, mocks, gate bypasses, direct DB edits, real-child data, seed-account deletion, credential disclosure, worktree usage, commit, or push. Preserve unrelated containers and volumes; start/stop only resources required by FEAT-085 and the requested runs.

## Addendum 11 — preserve Story receipt operations during migration

- **Status:** APPROVED
- **Approver:** Project owner's direct instruction on 2026-11-25 to fix all failures and complete two real Parent E2E runs; the migration failure is within the approved runtime repair scope.
- **Observed failure:** `20261120_b1_0001` attempted to narrow `story.command_receipts.ck_story_receipt_operation` and was rejected because retained rows use `GENERATE_ACTIVITY_SET` and `SELECT_ACTIVITY`.
- **Approved scope:** Update the unapplied B1/VB2/AS1 migration operation sets and the matching Story receipt ORM check so the existing operations survive the schema upgrade. Add a regression assertion, apply only required Parent StoryRun/activity/video migration heads, and verify the active run through the real API before proceeding.
- **Preservation:** No receipt/run deletion or direct DB row edits; do not weaken auth, consent, quality, quota/admission, video, or safety gates. No fixture, credential output, worktree, commit, or push.

## Addendum 12 — apply the missing generic upload scope migration

- **Status:** APPROVED under Addendum 10's direct authorization to repair all blockers and complete two real Parent E2E runs.
- **Observed failure:** The real UI's `POST /v1/upload-sessions` returned 503 before image bytes or AI inference. PostgreSQL's `core_upload_sessions` was still at the pre-`20261119_uf_0001` schema (`organization_id NOT NULL`, no typed owner-scope or scan-validation fields) while the API ORM inserts those fields. The route mapped the database exception to generic `PROVIDER_UNAVAILABLE`.
- **Approved scope:** Preflight the isolated FEAT-085 DB, apply only `20261119_uf_0001` for typed upload scope, verify columns/constraints and preserve existing rows. Add a stage-specific mobile error for upload-session-create 503s so the UI offers one safe retry with the same idempotency keys; add focused tests. Then retry the same active run through the Android UI once. Do not upgrade unrelated heads.
- **Preservation:** No direct DB row edits/deletes, run recreation, duplicate inference, fixture, or admission/safety bypass. Preserve existing profiles, consent, run state, volumes and unrelated containers. Capture sanitized SQLSTATE/error class and timings; do not print secret values, SQL parameters, or drawing bytes. No commit/push.

## Addendum 13 — compose real Modal analysis and story workers

- **Status:** APPROVED under Addendum 10's direct authorization to fix all blockers and complete two real Parent UI-to-Modal E2E runs including video.
- **Observed failure:** Android completed upload/scan and attached the butterfly asset, but `INPUT_PROCESSING` never advanced. Source sets `application.state.drawing_analyzer` and `story_generator` to `None` unconditionally; Modal app inventory showed no worker tasks. Thus the API returned 202 without scheduling drawing inference.
- **Approved scope:** Implement and compose real Modal-backed adapters for the existing drawing-analysis and story-generation ports only when the isolated API runs with `env=local|test` and `ai_provider=modal_dev`. Verify attached normalized object type/size/hash before drawing dispatch, preserve worker schema/model/call provenance, and map terminal versus unknown outcomes to existing port failures. Add one authenticated idempotent recovery dispatch for the already attached run, guarded by the repository's compare-and-set start operation so a replay cannot dispatch a running/terminal/unknown job. Add focused tests, rebuild only the FEAT-085 API container, and continue the same run through Android UI. No request fixture or fake inference is allowed for E2E.
- **Preservation:** Keep auth, consent, scan, parser/quality, quota/admission and video safety enabled. Do not edit/delete run/profile/consent rows, reupload or recreate the run, dispatch again after an unknown outcome, change unrelated containers/volumes, expose credentials or child image content, use a worktree, commit, or push.

## Addendum 14 — classify Modal's explicit pre-dispatch rejection

- **Status:** APPROVED under Addendum 10's direct authorization to fix all blockers and complete two real Parent E2E runs, including real Modal AI and video.
- **Approved plan:** `plan/PLAN_REV8_MODAL_REJECTED_DISPATCH_RECOVERY_20261125.md`.
- **Observed failure:** The drawing worker raised Modal SDK `ResourceExhaustedError` at `function_spawn`, with `modal_call_id=None`. The Modal app had zero active tasks. The current adapter treated every exception at this stage as an uncertain outcome, leaving the Parent UI waiting indefinitely.
- **Evidence basis:** Installed Modal Python SDK 1.6.3 returns a `FunctionCall` only after invocation creation returns a function-call ID. Modal's invocation documentation specifies that inputs exceeding platform limits are rejected with `ResourceExhaustedError`: https://modal.com/docs/guide/function-invocation-methods. This typed server rejection is a known no-call outcome; it does not authorize retrying timeouts, transport failures, or any post-call-ID outcome.
- **Approved scope:** Implement typed/log-safe handling for `ResourceExhaustedError` at `Function.spawn`, one bounded retry only after that explicit rejection, and a local/test-only audited CAS reconciliation for the exact existing run/revision so it can return to `QUEUED`. Resume through the existing authenticated Android recovery flow once. Keep all gates enabled, do not reupload, and stop if a second rejection or any ambiguous result occurs. Then continue the two-run E2E under Rev7.
- **Preservation:** No fixture, gate/quota/safety bypass, direct DB edit, deletion, unrelated container/data change, credential output, worktree, commit, or push. The existing prohibition on retry after an unknown/possibly accepted outcome remains unchanged.

## Addendum 15 — repair the drawing contract and app-resume state

- **Status:** APPROVED under Addendum 10's direct authorization to fix the Parent flow and complete two successful real runs.
- **Approved plan:** plan/PLAN_REV9_DRAWING_CONTRACT_AND_RESUME_FIX_20261125.md.
- **Observed failure:** The accepted Qwen3.8 drawing call completed with BOX_INVALID; the run has input revisions 1 and 2, so its one allowed drawing replacement is consumed. On app restart, the local retake counter reset and the capture view hid the server error when the local image URI was absent.
- **Approved scope:** Clarify box geometry in the worker prompt, emit safe box-specific diagnostic codes without relaxing the schema, restore retake usage from the server revision, and show the server error/status/close actions in the Android UI. Preserve the failed run and use the normal authenticated lifecycle path only after preserving its synthetic drawing evidence. Continue with two fresh runs using distinct topics and the two generated synthetic drawings.
- **Preservation:** Do not repeat the accepted Modal call, exceed the two-input limit, modify database rows directly, delete seed accounts, bypass any gate, expose secrets, use Computer Use, or commit/push.

## Addendum 16 — unblock the Android system photo picker

- **Status:** APPROVED under Addendum 10's direct authorization to fix all Parent E2E blockers and complete two real runs.
- **Observed failure:** Android 16's system image picker is available, but the app requests legacy `READ_EXTERNAL_STORAGE` first. The emulator reports that permission denied and the UI remains in a busy state instead of opening the picker.
- **Approved plan:** `plan/PLAN_REV10_ANDROID_PHOTO_PICKER_PERMISSION_20261125.md`.
- **Approved scope:** On Android API 33+, invoke Expo's system image picker without requesting broad media-library access; retain permission checks on iOS and Android API 32 or earlier. Add platform tests, typecheck, mobile tests, and verify selection through the real Android picker.
- **Preservation:** Camera permission and all server-side upload, malware scan, inference, quota, and safety gates remain unchanged. Do not access MediaStore directly from the app, modify run records, expose secrets, use Computer Use, or commit/push.

## Addendum 17 — clear stale capture intent when choosing a learning path

- **Status:** APPROVED under Addendum 10's direct authorization to fix all Parent E2E blockers and complete two real runs.
- **Observed failure:** Entering through the camera shortcut leaves `pendingCaptureSource=camera` set. Choosing the topic path does not clear it, so CaptureScreen auto-launches the camera and remains busy before the gallery action can run.
- **Approved plan:** `plan/PLAN_REV11_CLEAR_CAPTURE_INTENT_ON_LEARNING_PATH_20261125.md`.
- **Approved scope:** Clear the pending camera/gallery intent on explicit Topic or Lesson path selection; keep direct home shortcuts unchanged. Add a focused regression test and verify the photo picker on Android.
- **Preservation:** Do not change account/run data or skip server-side auth, consent, upload, scanning, inference, quota, or safety checks. No Computer Use, commit, or push.

## Addendum 18 — repair Parent create-run subject idempotency wiring

- **Status:** APPROVED under Addendum 10's direct authorization to fix all blockers and complete two real Parent UI-to-Modal E2E runs.
- **Approved plan:** `plan/PLAN_REV12_PARENT_RUN_IDEMPOTENCY_SUBJECT_FINGERPRINT_20261125.md`.
- **Observed failure:** The real Android UI's fresh `POST /v1/story-runs` returned HTTP 500 before creating a run or dispatching Modal because the application service passed `intended_drawing_subject` to `SqlParentStoryRunRepository.replay_create_run()`, whose persistence adapter signature did not accept it. Source review also found the fresh `create_run()` signature missing the same value.
- **Approved scope:** Align both repository signatures, persist the supplied subject in the existing context snapshot, and align idempotency fingerprint semantics; add focused regression tests; verify by authenticated API and sanitized logs that this failed attempt created no run/job/Modal call; rebuild only the FEAT-085 API with the existing Compose project and `--no-deps`; then resume the two approved real E2E runs from Android.
- **Preservation:** Keep authentication, consent, upload scanning, schema, AI parser/quality, activity, story review, quota/admission, safety, and video gates enabled. No direct DB edits, migrations unless proven necessary, fixture, repeated accepted AI request, seed/account deletion, credential disclosure, worktree, commit, or push.

## Addendum 19 — safely diagnose Modal pre-call resource rejection

- **Status:** APPROVED under Addendum 10's direct authorization to fix Parent E2E blockers and complete two real Android-to-Modal runs; the owner explicitly requested that failures be fixed and both runs finish.
- **Approved plan:** `plan/PLAN_REV13_MODAL_RESOURCE_EXHAUSTED_DIAGNOSTICS_20261125.md`.
- **Observed failure:** The synthetic bicycle drawing was uploaded and staged, but Modal `Function.spawn` returned `ResourceExhaustedError` twice with no `modal_call_id`. Modal shows the drawing app deployed on L40S; the function has no worker log for that attempt. Current API logs discard gRPC status/details, so the platform reason cannot yet be identified.
- **Approved scope:** Add an allowlisted, privacy-safe mapper for Modal status/details and focused tests; run repository security validation; rebuild only the FEAT-085 API using the existing Compose project and `--no-deps`; inspect the same run through authenticated UI/status; then allow exactly one resume of the same synthetic input through Android UI. Continue the approved two-run E2E only if the worker accepts the request.
- **Stop condition:** If the one resumed request is again rejected before a call ID, stop new inference and preserve the classified reason. If a call ID is returned, never retry that accepted call; continue by polling its existing run.
- **Preservation:** Keep auth, consent, upload scan, schema, parser/quality, activity, script review, quota/admission, video, and safety gates. Do not change Modal deployment/capacity/plan, billing, credentials, database rows, seed data, unrelated containers or volumes. No fixture, Computer Use, real-child data, worktree, commit, or push.

## Addendum 20 — one bounded retry to evaluate the Sandbox-limits notice

- **Status:** APPROVED
- **Approver:** Project owner, direct request on 2026-11-25: “v m thử gọi lại xem? phải do cái này ko? hay là bị gì nữa?” and provided the Modal CPU Sandbox limits notice.
- **Approved plan:** `plan/PLAN_REV14_ONE_MODAL_FUNCTION_RETRY_20261125.md`.
- **Approved scope:** Verify the current Modal CLI profile, SDK version, deployed drawing Function, and Android Parent state. Fix the observed stale prior-run idea carried into a new topic path (`beginTopicPath`) with a focused regression check. Then make at most one real drawing-analysis request through the authenticated Parent UI using synthetic child-style input. If accepted, poll that same call; if rejected before a call ID, stop and record the safe reason. Compare the result with the CPU Sandbox notice.
- **Preservation:** All consent, upload, schema, parser/quality, quota/admission, and safety gates stay enabled. No direct worker invocation, duplicate retry, video request, quota bypass, Modal deployment/capacity/billing or credential change, database edit, seed change, Computer Use, worktree, commit, or push.

## Addendum 21 — reload the edited environment and retry the Parent UI flow

- **Status:** APPROVED
- **Approver:** Project owner, direct request on 2026-11-25: “t vừa thử sửa env, lại xem”.
- **Approved plan:** `plan/PLAN_REV15_RELOAD_UPDATED_MODAL_ENV_AND_RETRY_20261125.md`.
- **Observed condition:** The owner edited the root `.env` after the FEAT-085 API container was started. A non-disclosing comparison confirmed the running API container's `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET` do not match the root `.env`.
- **Approved scope:** Recreate only Compose service `api` in the existing `fe085-parent-api` project so it reads the edited root `.env`; verify health and compare the two credential values using booleans only; then submit one real Parent Android UI request for the already attached synthetic butterfly drawing. If accepted, poll the same Modal call and continue the same Parent workflow under the existing Addendum 10 full-E2E authorization, preserving all gates. If rejected before a call ID, stop all new inference.
- **Preservation:** Do not print or write credentials, alter Modal deployment/limits/billing, recreate dependencies or volumes, send direct worker requests, duplicate an accepted/ambiguous call, bypass quota/safety, use real child data or fixtures, use Computer Use, commit, or push.

## Addendum 22 — restart the terminal synthetic run through Parent UI

- **Status:** APPROVED
- **Approver:** Project owner, direct request on 2026-11-25: “t vừa thử sửa env, lại xem”.
- **Approved plan:** `plan/PLAN_REV16_FRESH_PARENT_RETRY_AFTER_ENV_RELOAD_20261125.md`.
- **Observed constraint:** After reloading the edited root `.env`, the existing Parent run is terminal and offers only normal close/restart actions; it cannot be submitted again. The synthetic drawing has been preserved in FEAT-085 evidence.
- **Approved scope:** Close the exact terminal synthetic run using the app's normal “close and start again” action, create one fresh synthetic insect/butterfly run, attach the preserved synthetic drawing from Android picker, and send one UI analysis action through the re-created API. If accepted, poll that call and continue the existing authorized Parent E2E stages with all gates; if rejected before a call ID, stop inference.
- **Preservation:** No direct DB mutation, direct Modal worker request, duplicate accepted/ambiguous call, gate/quota bypass, credential output, Modal deployment/limit/billing change, real-child data, fixtures, Computer Use, commit, or push.

## Addendum 23 — repair persisted subject-confirmation handoff

- **Status:** APPROVED
- **Approver:** Project owner, direct instruction in the ongoing task on 2026-11-25 to fix Parent workflow failures and complete real end-to-end runs; the current turn explicitly asks to retry after editing the root `.env`.
- **Approved plan:** `plan/PLAN_REV17_SUBJECT_CONFIRMATION_PROJECTION_AND_ACTIVITY_HANDOFF_20261125.md`.
- **Observed evidence:** The fresh synthetic Parent run's drawing inference succeeded. The subject-confirmation POST returned 202 and the database contains `PREPARATION_REVIEW`, `SUBJECT/CONFIRM` at understanding revision 1. The mobile flow then failed before `GET /v1/activities` because the run read projection still exposes an unconfirmed candidate and the controller's immediate state update is asynchronous.
- **Approved scope:** Correct the backend read projection without mutating the immutable VLM snapshot; pass the confirmed run explicitly into mobile activity loading; add focused regression tests; rebuild only affected API/mobile pieces; resume the same run through activity, story, video and playback under existing gates. Do not submit another drawing inference.
- **Preservation:** No fixture output, direct DB write, direct worker request, duplicate accepted/ambiguous inference, quota/safety/consent bypass, Modal deployment/limit/billing edit, credentials in logs, real-child data, Computer Use, commit, or push.
