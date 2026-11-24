# Parent → Modal video candidate E2E — Rev43

**Date:** 2026-11-20 (Asia/Saigon)  
**Target:** `emulator-5554`, task API `127.0.0.1:58100`, Compose project `s2l-feat081-rev23`, Modal `dev`.  
**Plan/approval:** Plan Revision 43, TASK_APPROVAL Addendum 70.  
**Initial pre-env checkpoint:** E2E stopped at authentication/runtime configuration. This checkpoint was superseded by the real run recorded in “Latest run outcome” below.

## Run log

| Check | Result |
|---|---|
| Android emulator | `emulator-5554` online; Parent Expo package open at sign-in. Screenshot: [`00-parent-sign-in-blocker.png`](00-parent-sign-in-blocker.png). |
| Task API refresh | Rebuilt/recreated only `s2l-feat081-rev23-api-1` from the current FEAT-081 worktree with `--no-deps`; other services were left running. |
| API health | `GET /health` → HTTP 200, `status=ok`. |
| Parent video routes | OpenAPI now exposes the expected 4 request/current/detail/preview routes. |
| Candidate DB migration | Applied only `20261120_parent_video_candidate` to the local task Postgres. It adds `story.video_candidate_jobs`; no row/business data was seeded or edited. Alembic reports the candidate revision as current head. |
| Authenticated route guard | Unauthenticated candidate `POST` → HTTP 401, as expected. |
| Runtime candidate gates | `env=local`, synthetic pilot=true, candidate flag=true, provider=`modal_dev`. |
| Backend identity configuration | `auth_provider=development`; Firebase project ID and Firebase Admin credential are absent in the container. The app is at sign-in, so no authenticated Parent identity can be established through the configured backend. |
| Modal credentials in API container | `MODAL_TOKEN_ID` absent and `MODAL_TOKEN_SECRET` absent. The host Modal CLI can list the deployed `sketch2life-srs23-dev-video` app, but those host credentials are not present in the API container. |
| Modal workload | Existing LTX app remains deployed with 0 tasks. No worker call, warm-up, or deploy occurred. |

## Why the flow stopped

The required local runtime identity and dispatch credentials are missing. A UI registration would attempt Firebase Authentication, while the backend is configured for `development` and lacks its Firebase project/Admin credential; continuing could create an external Firebase account without a matching backend identity. The backend also has no Modal token pair, so it cannot dispatch the candidate to the deployed worker. The run stopped before account creation, profile creation, any AI stage, or quota access.

No user secret was read, printed, copied, or changed. No Firebase account was created. No quota was charged or changed. No AI/Modal inference was sent, so there is no candidate video, request ID, Modal call ID, inference time, or video result to report.

## Required local `.env` configuration to resume

Set these in the single project-root `.env` (do not paste secret values into chat):

```dotenv
SKETCH2LIFE_AUTH_PROVIDER=firebase
SKETCH2LIFE_FIREBASE_PROJECT_ID=sketch2life-dev
SKETCH2LIFE_FIREBASE_ADMIN_JSON_BASE64=<base64 of the Firebase Admin service-account JSON>
MODAL_TOKEN_ID=placeholder
MODAL_TOKEN_SECRET=placeholder
```

The Android app also needs the existing public Firebase client settings and an emulator-reachable API URL (`http://10.0.2.2:58100`). After the root `.env` is updated, restart only the task API and Expo bundle, then resume the synthetic Parent flow. Keep the no-quota candidate flag/provider local-only and synthetic-only. Do not share the Firebase Admin JSON or Modal token values in chat.

## Services/data left in place

- The task API was rebuilt and is healthy with the candidate route registered.
- The additive candidate migration is applied to the local task database.
- The task Postgres/Redis/MinIO/ClamAV services remain running, as do unrelated existing projects.
- The Modal LTX app remains deployed with no live tasks.
- No source-code fix, `.env` change, commit, or push was made during this blocked E2E attempt.

## Latest run outcome after loading the project-root .env

The earlier “stopped at authentication/runtime configuration” section above records the preflight before the root .env was explicitly passed to Compose. It is a historical checkpoint, superseded by this real emulator run. The root file was loaded with the approved --env-file path; required values were checked only as booleans and were not printed or copied.

**Result: PARTIAL — stopped at activity suggestions under the approved no-retry boundary.** No story or video candidate was generated.

| Stage | Result |
|---|---|
| Parent registration and login | Firebase registration returned HTTP 201. The immediate role lookup returned 401 with InvalidIdTokenError although safe claim diagnostics matched the configured project and showed an unexpired token. A second login on the same synthetic account succeeded; /api/auth/v1/me returned HTTP 200. No second account was created. |
| Synthetic profile | Created a synthetic-only profile named E2EChild, age 60 months. No real child data or fabricated legal consent was used. |
| Topic and drawable subject | Catalog-backed topic and subject endpoints returned HTTP 200. The UI displayed three rotating topic cards and three ocean subjects; selected topic Đại dương and subject Rùa biển. |
| Optional SVG guide | The single guide lookup returned HTTP 404 (CURATED_SVG_GUIDE_NOT_FOUND) for Rùa biển. The selected source catalog has no guide for this subject. The optional guide was turned off and the flow continued; no guide inference was sent. |
| Drawing understanding | One real Parent UI request reached Modal Qwen/Qwen3.5-9B. It completed in 42.34 seconds and returned subject “con rùa” at 90% confidence with shell, head, four small legs, and bubbles identified. The adult confirmed the subject and context in the UI. |
| Activity suggestion | Catalog-first lookup found zero accessible lessons, zero age-eligible activities, and sent zero catalog candidates. The app attempted its one Qwen fallback request; Modal returned NotFoundError before issuing a Modal call ID. The Parent API returned HTTP 504 and the UI showed an error. No retry was sent. |
| Modal dev app inventory | The configured environment lists sketch2life-srs23-drawing-vlm-dev and sketch2life-srs23-dev-video. It does not list sketch2life-srs23-language-audio-dev, which owns the activity suggestion workload. |
| Story and video | Not called. The flow stopped after the failed activity stage as required by this plan. No LTX request or video candidate exists for this run. |
| Quota and cleanup | No quota ledger was read or changed. No video request was sent. The failed activity invocation uploaded a 704-byte request to the Modal scratch volume, then failed before a call ID; no cleanup event was observed. The temporary object was left untouched. |

### Correlation and timings

- StoryRun: 16002cde-42b1-4198-a7d0-a04de85fea9b.
- Drawing request: d76f14c9-0b87-487c-b41b-4cba6b1c7ec3; job af02a711c788d6fc; attempt 4955b9d1df15f2f0; Modal call fc-01M7VY8CNDZ2YS4PSBE0XRGPXY.
- Drawing worker: scratch upload 9.461 seconds; model load 13.270 seconds; API/Modal elapsed 42.34 seconds. Model revision c202236235762e1c871ad0ccb60c8ee5ba337b9a.
- Activity request: a9b4086d-b5e3-4351-82f8-93043e63e646; job 73a0ea1b76c77ba5; attempt 4695293748d093a6; exception NotFoundError; Modal call ID absent; API result HTTP 504.
- Drawing observability gap: the remote call succeeded and the UI rendered valid JSON, but the API snapshot reported no terminal worker event and ended at constrained_decoder_setup.

### Evidence

- Synthetic image: [input drawing](input/synthetic-sea-turtle-drawing-rev43.png).
- Screens: [drawing ready](screenshots/04-drawing-ready.png), [drawing pending](screenshots/05-drawing-analysis-pending.png), [drawing result](screenshots/06-drawing-analysis-result.png), [context snapshot](screenshots/07-context-snapshot.png), [activity start](screenshots/08-activity-selection-start.png), [activity error](screenshots/09-activity-suggestion-error.png).
- Sanitized event record: [run-events.md](logs/run-events.md).

### Exact blocker and next gate

The activity fallback targets the language/audio Modal app, but that app is not deployed in the currently configured dev environment/account. The upload/spawn attempt failed with NotFoundError before Modal accepted a function call. Deploying that app and making another activity inference are outside this run’s approved one-attempt/no-deploy boundary. A new bounded approval is required before deployment and one fresh activity inference. Do not proceed to story/video until an activity set is successfully returned and selected.

## Superseding continuation — Rev45 after explicit deployment approval

**Plan / approval:** Plan Revision 45; Addendum 74. This section supersedes the stopped-after-activity outcome above. The earlier activity failure had no Modal call ID, so it consumed no model inference.

### Modal deployment

- Deployed `deployment/modal/srs_v23/language_audio_app.py` to Modal `dev` after the owner authorized deployment.
- First CLI invocation failed at terminal output encoding (`charmap`) after the Modal app record was created; one UTF-8-corrected retry (`PYTHONUTF8=1`) succeeded.
- Read-only inventory confirmed `sketch2life-srs23-language-audio-dev` deployed as app `ap-3jclT2On5Hd1hVbRMuJ6dk`, with zero tasks at inventory time. The earlier failed record `ap-CJbgxaJCsQFdvo8QvvgvlT` was stopped and had zero tasks. No warm-up/readiness function was invoked by deployment.
- Existing drawing and video apps remained deployed. No other app was changed.

### Real Parent UI continuation

| Stage | Result |
|---|---|
| Activity suggestions | PASS. One request from the real Android UI returned HTTP 200 and three AI-generated fallback drafts; no published/age-eligible catalog activity existed. Modal call `fc-01M7W257RZTNZF7QG01ZX1N7X3`; worker elapsed 114.349 s, service log elapsed 116.081 s. Request `0ea6399b-a71b-4a00-843a-bd4adbaa6503`. |
| Activity selection | PASS. The UI persisted **“Phân loại thẻ rùa”**. This is the activity described in the story; the earlier selection summary saying “Vận động mô phỏng rùa” was inaccurate. |
| Story generation | PASS. One successful Qwen3.5 Modal inference returned HTTP 200. Modal call `fc-01M7W2G6BHQ09QMF5DA2HV40SM`; worker elapsed 147.754 s; request `a887c371-d189-4fae-aa78-8ef622c3791c`. A preceding HTTP 409 was rejected before the successful inference; it did not produce a Modal call. |
| Adult story review | PASS. The real UI displayed the Vietnamese draft **“Khám Phá Hình Dáng Con Rùa”** with five scenes about observing turtle-shell shapes and sorting turtle cards. The adult operator confirmed it; `POST /v1/story-runs/{run_id}/script-confirmation` returned HTTP 200. |
| Server state | PASS, read-only verification. StoryRun `16002cde-42b1-4198-a7d0-a04de85fea9b`: `SCRIPT_REVIEW`, job `SUCCEEDED`, no error, version 8. Revision 1 is `CONFIRMED`, hash `2539c2363244b8114b306663e3f3e8b307d1b6e2374380c3abee30d311988349`; selected activity `Phân loại thẻ rùa`; zero video-candidate rows at the check. |
| Video candidate | NOT SENT YET. No LTX inference or candidate row exists. While inspecting UI wiring, the Expo app was force-stopped/relaunched to verify the current bundle; it returned to sign-in. The video worker remains deployed, and no video request was sent. Manual Parent sign-in is required before resuming the same server-side run. |

The Metro bundle is served from the active `feature/fe-mobile-remediation` worktree and contains the real `StoryScreen → VideoCandidateScreen` route and `/video-generations` API path. The local video adapter targets deployed Modal app `sketch2life-srs23-dev-video`. The task API has `modal_dev`, the synthetic pilot gate, the local video-candidate gate, and both Modal token fields configured (presence only; values were not printed). The video flow itself remains unverified.

No quota/billing records were read or changed. No direct API call skipped the UI. No new account, profile, run, drawing inference, video attempt, retry, fixture, or real child data was used. No `.env`, secret, migration, SRS, commit, or push change was made for this continuation.

## Rev46 — Real Parent flow resumed; story review blocked video

**Execution boundary:** Rev46 approval and its amendments authorize one synthetic Parent account/profile/run, one inference each for drawing, activity and story, and at most one silent video candidate only after the adult reviews and confirms a suitable story. All product operations below were initiated from the actual Expo Android UI (`emulator-5554`) against the task API and deployed Modal workers. No fixture or direct product API/worker bypass was used. Quota/billing was not accessed.

### Outcome

| Stage | Result |
|---|---|
| Parent account | Reused the synthetic account registered through the Expo sign-up UI earlier in this execution. No second account was created. Firebase login and `/api/auth/v1/me` succeeded after the separately approved token-clock-skew correction. |
| Profile | The first create attempt failed with a database `DataError`; safe diagnostics were added under the approved amendment. The UI list was verified empty, then the same synthetic values were submitted once: `E2E Profile R46`, age 60 months, interests “rùa biển, động vật”, no fabricated gender or consent. UI read-back succeeded; profile ID `f37bfa36-44be-4176-a474-b767bf26c183`. |
| Topic, subject and input art | Selected theme `Đại dương` and subject `Rùa biển`; chose the synthetic turtle drawing from Android Photo Picker. Source: `synthetic-sea-turtle-drawing-rev43.png`, SHA-256 `96983E11AB3DEF971E2842A2309C350CCEAAE11786BA9BC37C01ABA7C8F66477`, 1024×1024. Optional SVG guide stayed off; no guide inference was sent. |
| StoryRun/context | Created StoryRun `ff1021f5-e9e6-4343-9da3-ced08ad9de69` in the UI. Subject and context confirmation each returned HTTP 200. |
| Drawing understanding | PASS. `POST /api/parent/v1/ai/drawing-understandings` returned HTTP 200 through Modal Qwen3.5-9B. Request `43f20076-a63d-473e-8c13-a029552501c6`; Modal call `fc-01M7WDZA1DC13HPM3R3B567F7H`; elapsed 40.498 s. UI identified “con rùa” at 90% confidence and the adult confirmed it. |
| Activity suggestion and selection | PASS with AI fallback. Backend catalog preparation found `accessible_lesson_count=0`, zero age-eligible activities, and sent zero catalog candidates. The one allowed Qwen3.5-9B fallback returned HTTP 200 with three suggestions; request `6a010e64-9d03-45e2-98b5-e47606977380`, Modal call `fc-01M7WE5DQA3P56YDFY3XZ0ZPZ7`, 134.546 s, suggestion set `d9a63010-3c14-45dc-8dee-37eb71842de5`. The adult selected “Vận động mô phỏng rùa”; the UI persisted the selection with HTTP 200. |
| Story generation | API/model PASS; adult-review quality FAIL. One Qwen3.5-9B request returned HTTP 200, revision 1; request `c1e79b24-39eb-450a-8ec0-8e0aa986482a`, Modal call `fc-01M7WEFR1BV3P2WNN4M3ZV2PSD`, API elapsed 134.394 s. The UI displayed “Khám phá thế giới với con rùa”, but the Vietnamese story contains mixed-script text (`các動作`) and awkwardly addresses the child as “bé 60 tháng tuổi”. This is not suitable for adult confirmation. |
| Video | **NOT SENT.** The story was not confirmed, so the approved precondition for the single silent LTX candidate was not met. No video candidate was created and no LTX inference was dispatched. |

### Stop reason and evidence

This run stops at adult story review because the generated text violates the Vietnamese V1 language requirement. The successful HTTP 200 means the worker and response contract returned; it does not mean the story passed product quality review. Under the approved no-retry boundary, do not rewrite/regenerate the story or call video without a new bounded approval. The emulator remains on the story-review screen.

- Story-review capture: [rev46-story-review-mixed-language.png](screenshots/rev46-story-review-mixed-language.png).
- Synthetic input: [synthetic-sea-turtle-drawing-rev43.png](input/synthetic-sea-turtle-drawing-rev43.png).
- Sanitized event/correlation timeline: [run-events.md](logs/run-events.md).
- No quota/payment access, second account, duplicate profile/run, AI retry, video call, `.env`/credential edit, migration, commit, or push was performed in this continuation.
