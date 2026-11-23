# Parent E2E Rev55 — real Android + Modal checkpoint

Date: 2026-11-21 (Asia/Saigon). Runtime: task-local Docker project `s2l-feat081-rev23`, Expo app on `emulator-5554`. This run used the real Android UI and real Modal workers; no fixture or preview harness was used.

## Lifecycle event authorized and completed

- Addendum 102 authorized processing only the cancellation event for run `08657e31-ebd7-4a07-8f9b-5929b4dff23b`.
- The one-shot lifecycle consumer passed exact-run preflight, claimed only that run's one pending `StoryRunCancellationRequestedV1` event, purged the run-owned story content/assets under normal lifecycle rules, and finalized the tombstone as `DELETED`. The event is delivered and its lifecycle receipt completed. No account, profile, seed data, or unrelated run/event was changed.
- The previous section's `DELETE_PENDING` condition is a superseded checkpoint; it was resolved by the approved event processing.

## New synthetic Parent UI run

Synthetic profile: `SyntheticTurtleRev22`, 60 months. Artwork: generated synthetic turtle drawing already stored in this feature's evidence; no real child data.

| Local time (+07) | Step | Outcome and duration |
|---|---|---|
| 12:22–12:25 | Choose `Động vật` and intended subject `Rùa con` | Topic suggestions and drawing-subject suggestions returned HTTP 200 through UI. |
| 12:25–12:27 | Optional SVG drawing guide | UI request returned HTTP 200; six-step guide rendered, including final colored reference. Openclipart asset license recorded as CC0-1.0. |
| 12:27–12:29 | Attach synthetic drawing from Android gallery | Completed through the native Android picker. |
| 12:29:39–12:30:42 | Drawing understanding | Qwen/Qwen3.5-9B call `fc-01M7Y9A2SGYWMST1SW434QZ0HG`; API HTTP 200 in about 59.606 s. Candidate `con rùa`, advisory confidence 90%, visible turtle features. |
| 12:31–12:32 | Adult subject and context confirmation | Both authenticated UI confirmation requests returned HTTP 200. StoryRun `b05c2b46-e760-4643-824b-b30b5387453f` was created once (HTTP 201). |
| 12:32:49–12:36 | Catalog-first activity suggestions and selection | Catalog had 0 accessible and 0 age-eligible published/shared lesson activities. One Qwen/Qwen3.5-9B fallback call `fc-01M7Y9FXRGTEDQJ1B5CFDD3PVJ` completed in 123.521 s; endpoint HTTP 200, 3 suggestions persisted. Adult selected `Vận động mô phỏng con rùa`; selection endpoint HTTP 200. Existing quality gates passed; no gate was bypassed. |
| 12:38:01–12:40 approx. | Story generation | One Qwen/Qwen3.5-9B call `fc-01M7Y9SCQQP9RCJXARXQBDX25G`; inference 77.185 s, full worker 102.295 s. API `POST /api/parent/v1/ai/story-runs/{id}/story-revisions` returned HTTP 502 `STORY_OUTPUT_INVALID`. No timeout and no quota interaction. |

## Story failure diagnosis

The Modal worker classified the terminal result as `STORY_TEXT_INCOMPLETE` at `story.opening` (`stage=output_decode_and_parse`, `StoryOutputValidationError`). JSON was complete and the model generated 682 tokens of a 4096-token budget, so this was not token-budget exhaustion. The parsed `opening` had 140 characters and was incomplete; `middle` had 139 and was incomplete; `ending` had 74 and was complete. Scene actions were about 61–63 characters and incomplete; all five narrations (about 64–89 characters) were incomplete. Thus the prose-completion quality gate rejected the generated fields. The failure was not an API timeout, Docker crash, or missing Modal deployment.

The UI displayed a prominent purple processing card with an elapsed timer and “do not create again” guidance in `screenshots/82-story-inference-started.png`. After the terminal failure it showed a stale-draft warning, the safe reference `parent-mwpz8i3o-18wvl5ebcopq`, and `screenshots/83-story-failure.png` exposed a `Gửi lại cùng yêu cầu` action. That action was not pressed. The loading card is visually prominent, but the UI does not provide stage-by-stage progress; consider this a usability follow-up, not the cause of the model failure.

## Stop and cleanup

- Addendum 102's cap of one story inference and stop-at-failure rule was reached. No retry, rewrite, video candidate, quota/payment request, or inference bypass was made.
- At 12:47 +07, stopped only the task-used Modal apps `sketch2life-srs23-language-audio-dev` and `sketch2life-srs23-drawing-vlm-dev`, after confirming both had 0 tasks. Modal inventory verified both stopped. The unrelated `sketch2life-srs23-dev-video` app remains deployed with 0 tasks and was not touched.
- Evidence screenshots and UI XML snapshots are under `screenshots/` and the parent directory. No raw model output, prompt, credential, or child data was stored.
- No commit or push.

## Current outcome

Parent flow passed topic selection, optional SVG guide, image attachment, drawing understanding, adult subject/context confirmation, catalog-first lookup, AI fallback activity suggestions, and activity persistence. It stopped at the story quality gate. This is a **partial E2E**, not a completed Parent workflow; video was correctly not called because no valid adult-reviewable story existed. A further story attempt requires a new bounded approval after a code fix and focused verification.

## Rev56 — read-only rewrite eligibility check (2026-11-21)

The offline Rev56 changes and focused tests were already present in the worktree. The Android app remained on the real Parent flow; the task API at `127.0.0.1:58100/health` returned HTTP 200. No Modal app was redeployed and no new inference or mutating API request was sent.

Read-only verification of the exact synthetic run found:

| Field | Current value |
|---|---|
| StoryRun | `b05c2b46-e760-4643-824b-b30b5387453f` |
| `run_state` | `FAILED` |
| `error_code` | `STORY_OUTPUT_INVALID` |
| `retryable` | `false` |
| Latest story revision | revision 1, `FAILED` |
| Persisted activity selection | selection revision 1, understanding revision 1, activity index 2 |

The repository's `reserve_story_revision` accepts only `PREPARATION_REVIEW` or `SCRIPT_REVIEW`; it rejects this `FAILED` run before a worker call. The SRS state-transition row says `FAILED` is terminal and only describes rewrite from `SCRIPT_REVIEW`. BR-13 allows up to three rewrites but does not define whether a quality-rejected initial generation can be rewritten. Therefore the approved one-rewrite condition (“if the current API accepts it”) is not met. No story request was attempted.

The real UI confirms a second issue: `screenshots/85-story-run-history-state.png` shows the failed run only as a summary, with no resume action; `screenshots/86-story-screen-after-failure.png` shows the home error notice but no route back to the failed story. Current Home filters `FAILED` from resumable runs. The existing context and activity selection remain preserved on the server, but the UI cannot use them to submit the approved rewrite after navigating away.

**Stop:** no inference, no API rebuild, no Modal deploy, no video, no quota/payment call, no data change. Language/audio and drawing Modal apps remain stopped; unrelated video app remains untouched. Docker task API remains healthy. Screenshots 85–86 were captured from the real Android emulator and contain no model output or credentials.

This exposes an unresolved product-contract conflict: BR-13 rewrite allowance versus terminal `FAILED` state. Plan Rev57 and pending Addendum 104 document the narrow proposed exception and await owner decision. The approved Rev56 worker contract/UI changes remain unverified live. No commit or push.

## Rev57 — one approved same-run rewrite (2026-11-21)

Plan Rev57 and Addendum 104 were approved and implemented. The task API was rebuilt from the approved worktree and `/health` returned 200. Focused backend tests passed (21); mobile typecheck passed; all 142 mobile tests and UI-copy validation passed; focused Ruff and `git diff --check` passed.

Immediately before submission, read-only DB checks matched the approved recovery predicate: the exact run was `FAILED` / `STORY_OUTPUT_INVALID`, job and latest revision were `FAILED`, revision 1 was the only story revision, retryable was false, lock was released, current drawing/context/understanding/activity pins matched, and the Parent had no other active run. The adult entered and submitted the rewrite once from the real Android UI on `emulator-5554`; no direct API or worker inference was used. Evidence of the screen transition is in `screenshots/94-story-rewrite-loading.png` and `screenshots/96-after-504-outcome-unknown.png`. Temporary UI snapshots containing the adult instruction were removed; no raw prompt or model output is retained in evidence.

| Local time (+07) | Event | Result |
|---|---|---|
| 16:03:23 | Modal deploy | `sketch2life-srs23-language-audio-dev` deployed as v15 from the task worktree. No model inference was part of deployment. |
| 16:13:41 | Parent story request | API began scratch input upload (`job_ref=95ffca8f4157e655`, `generation_ref=ae9bbcdc80391042`, `attempt_ref=2b0b9868a84c232a`); upload completed in 5,151 ms. |
| 16:13:46–16:13:47 | Modal dispatch / API response | API logged `modal_worker_spawn_started`, then `parent_modal_outcome_unknown`; `modal_call_id=None`. UI endpoint returned HTTP 504. API request ID: `47dc5788-3852-45e1-b5b5-9dd2db1abc94`. |
| 16:15:01 | UI/status check | UI showed “Đang xác minh kết quả… Không gửi lại”; elapsed display was 01:29. DB showed `SCRIPT_GENERATION_UNKNOWN` / `STORY_OUTCOME_UNKNOWN`, job and revision 2 `AWAITING_RECONCILIATION`, `retryable=false`, no provider call ID, and the active-owner lock still held. |
| 16:18:23 | Modal cleanup | Confirmed zero Modal tasks, then stopped only the task-used language/audio app. It is now stopped with zero tasks. Drawing VLM remains deployed with zero tasks; video app was not touched. |

The Modal app log query returned no function-call/worker entries for this request, and inventory showed zero tasks. The available evidence does not establish whether the failure occurred during Modal dispatch/admission or before a GPU worker started; it is not evidence of a model-generated result or a proven GPU cold-start timeout. Because the API has no Modal call ID and the run is awaiting reconciliation with its lock held, the request must not be retried. No second story call, video call, quota/payment call, new run/account/profile, DB edit, or gate bypass occurred.

Repository verification: the security validator failed on pre-existing FEAT-081 historical artifacts (absolute machine paths and a non-placeholder secret assignment in an older evidence report). Those findings were not changed in this bounded task. No commit or push was made.

**Outcome:** the approved one-shot rewrite did not produce a confirmed story. The conditional video is not eligible because there is no story to review or confirm. This Parent E2E remains partial; the run is held in reconciliation and needs a separately approved recovery decision before any further mutation or inference.