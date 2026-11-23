# FEAT-081 — Plan Revision 23: Parent activity, story, and video end-to-end

- **Status:** APPROVED by the owner's direct instruction on 2026-11-19 (Asia/Saigon): “bước chọn hoạt động, video đồ nữa thì sao, chạy full luồng end to end đi, đừng quan tâm quota”.
- **Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, worktree `<local-machine-path>
- **SRS authority:** FEAT-063 canonical working SRS v2.7-draft, Rev67, unsigned. §§6.2–6.3, 9.3–9.5, 21.5 and Rev66–67 control the Parent order, activity binding, story gates and LTX-2.5 target. Read `docs/context/SRS_AUTHORITY.md` and FEAT-063 `SOURCE_REGISTER.md`; historical FEAT-081 plans are implementation evidence only.
- **Starting evidence:** Rev22 Android run `evidence/ANDROID_DRAWING_CONFIDENCE_UI_REV22_20261119/` stopped at adult review for a synthetic turtle drawing. Reuse that existing run if the authenticated UI/runtime can safely resume it; do not repeat its drawing inference.

## 1. Goal

Complete and prove the real Parent Android path after drawing-understanding review:

`adult confirms subject → catalog-first activity suggestions → adult selects and persists one primary activity → Qwen creates a story bound to that selection receipt → adult reviews/confirms the exact story revision → backend admits a local synthetic video request without charging product quota → LTX-2.5 on Modal generates silent scene video from the child's drawing and confirmed storyboard → automated validation/safety → composed video is playable in the Parent UI → the run shows the lesson/activity content after video`.

Use the real Expo Android app, authenticated synthetic Parent/profile, real backend persistence, and real Modal inference. No fixture, visual-preview harness, mocked response, direct database mutation, or backend-only substitute is allowed.

## 2. Product and runtime invariants

- Keep the existing Parent order and required gates. Subject confirmation, selection of exactly one primary activity, and adult script confirmation are mandatory before video. Never skip a failed or unresolved gate.
- Use the activity catalog visible to the Parent: published/shared lesson versions the Parent may access. Send the eligible catalog candidates and the pinned profile/context, confirmed subject, and drawing-derived context to Qwen for ranking/selection. If the catalog has no suitable candidate, follow the existing three-draft fallback and quality gate; do not silently invent a catalog hit.
- Persist the selected activity as an immutable selection receipt/snapshot and bind story generation to its identifier/hash. Story content must describe it as a post-video activity, not an activity already performed.
- Use the exact confirmed drawing, story revision/hash, storyboard, and scene order for video. LTX prompts should describe motion/action and camera movement while preserving the drawing as the visual reference. Video is silent; narration is out of scope for this run.
- Use the SRS LTX-2.5 Modal target. Do not substitute Wan or the legacy session/story-video route. Keep automated video safety/quality gates fail-closed; adult script confirmation is not replaced by a new final adult-video gate.
- “Ignore quota” means bypass only product video-quota charging/admission for this local synthetic test. Any bypass must be explicit, disabled by default, restricted to local development and synthetic identity/profile, auditable, and impossible to activate in deployed/non-local environments. Do not remove production quota enforcement or alter billing data.
- No real child image, identity, consent record, or profile. Reuse the existing synthetic turtle run and image. If the run cannot be resumed through the authenticated UI/API, stop before new drawing inference or direct database edits and record the blocking cause.

## 3. Work sequence

### M0 — preflight and contract alignment

1. Read the FEAT-063 authority, SRS and source register; compare source routes to the served OpenAPI and verify the UI is the real Expo app.
2. Inspect the existing synthetic StoryRun through authenticated API/UI reads. Confirm its current subject-review state and exact source asset/hash. Do not mutate it outside supported routes.
3. Record the implementation gaps found before changing code: Parent activity routes/persistence, story binding, video API/job state, Modal worker/readiness, quota bypass boundary, and UI playback/activities.

### M1 — finish activity selection and story on Android

1. Resume the existing run in the Parent UI and explicitly confirm the suggested subject.
2. Request catalog-first activity suggestions once. Verify the returned catalog provenance, age/context filtering, quality gate, and immutable snapshot/hash.
3. Select one primary activity in the UI. Verify the server returns and persists a receipt bound to the current understanding/context/lesson hashes.
4. Generate one story revision from the selected activity receipt. Verify the strict story/storyboard schema and semantic gates, then review and confirm the exact revision/hash in the UI.
5. If these routes are missing from the currently served app, implement only the Parent contract/UI wiring needed to expose the existing source behavior. Do not use the unauthenticated demo/loopback StoryRun-lite APIs.

### M2 — provide a real local Parent video vertical slice

1. Implement/additive-wire an authenticated Parent video request and status/result path only if the current product route is absent. Bind admission to the confirmed script hash, activity receipt, drawing asset hash, and pinned context. Preserve idempotency and terminal/error states.
2. Add a local-only synthetic no-quota admission path, default OFF and guarded by environment + synthetic principal/profile. Never let the mobile client assert or choose the bypass.
3. Implement/deploy the LTX-2.5 Modal worker against the SRS pinned checkpoint/runtime and existing Modal model volume/secrets. Keep image-to-video conditioning, silent output, deterministic scene ordering, structured worker logs, and bounded worker timeout/retry behavior. Do not request model warm-up or extra inference outside the actual video request.
4. Generate all scenes in the confirmed storyboard (5–15 as validated by the existing story contract), with no provider retry in this single verification run. Compose the scenes and run the existing/approved technical and automated safety validations. Persist only a terminal READY result if every required gate passes; otherwise persist a diagnosable failure and do not expose playback.
5. Wire the real Parent UI to request/poll/reconcile the video job, display its progress/failure, play the returned video, and show the selected lesson activities after playback. No fixture media.

### M3 — real E2E evidence and cleanup

1. Run through the Android UI from the existing subject-review screen through a playable video and post-video activities. One activity-suggestion inference, one story inference, and one video request; no duplicate taps/retries. The video request may fan out only to the scenes in the confirmed storyboard.
2. Capture sanitized screenshots for each completed UI stage, safe request/worker logs, call IDs, hashes, HTTP results, and elapsed times in a new FEAT-081 evidence folder. Do not store credentials, raw provider payloads, or real child data.
3. Stop only processes/containers/Modal apps launched for this run. Leave unrelated stacks and already-live apps untouched.
4. Update FEAT-081 `CONTEXT.md`, `status/STATUS.md`, and evidence report with pass/fail per stage, exact blockers, and any outstanding requirement. No commit or push.

## 4. Acceptance criteria

- The existing real Android Parent run resumes without fixture or direct DB mutation, and the adult-confirmed subject is preserved.
- Activity suggestions are catalog-first and age/context eligible; exactly one primary activity selection is persisted with an immutable, hash-pinned receipt.
- A valid story draft is generated from that receipt, reviewed and confirmed by the adult. The confirmed story hash is the one admitted to video.
- One authenticated local synthetic video request bypasses only product quota charging. The worker actually invokes the pinned LTX-2.5 checkpoint on Modal; health-only, Wan, cached sample, mocked, or fixture output does not pass.
- Every storyboard scene is produced and composed into a valid silent video. Automated validation/safety passes before the authenticated Parent UI can play it. The UI then displays the lesson's activities.
- Logs and evidence make each failure attributable to a specific API, Modal call/worker stage, or validation gate. All test-owned services are stopped afterward.

## 5. Bounded execution and exclusions

- Synthetic turtle data only; no drawing-understanding repeat, no real child data, no production deployment, no consent-policy relaxation, and no direct DB writes.
- At most one activity-suggestion request, one story-generation request, and one Parent video request. No video scene retries in the evidence run. Fix code/contract issues offline before consuming a stage's one live call.
- No narration/TTS, subtitles, quota/payment purchase/refund testing, Teacher flow, SRS redesign, migration against shared/production databases, commit, or push.
- If LTX-2.5 cannot be legally/runtime accessed with the already-configured Modal environment, stop the live video attempt before substituting another model. Record the exact access/runtime blocker; do not claim end-to-end completion.

## 6. Authorized implementation paths

- This plan, `approvals/TASK_APPROVAL.md`, FEAT-081 `CONTEXT.md`, `status/STATUS.md`, and new evidence under `evidence/ANDROID_PARENT_ACTIVITY_STORY_VIDEO_E2E_REV23_20261119/`.
- Parent Expo modules under `apps/ui-mobile/src/parent/` and their focused tests.
- Parent backend contracts, application/domain services, persistence adapters, HTTP routers/composition, Alembic migration only if required for the additive Parent video lifecycle, and focused tests under `backend/`.
- `deployment/modal/srs_v23/video_app.py`, its versioned worker contracts/tests, `deployment/modal/srs_v23/workloads.json`, and local Docker/Compose wiring required to run the real Parent API.
- Do not edit `.env`/secrets, alter existing user data, replace the LTX target, or change unrelated feature/API behavior. Do not commit or push.

## Execution Amendment A1 — new synthetic Parent account and complete flow

- Trigger: the owner reiterated “chạy full luồng end to end đi” and answered “đăng ký đi” when the real emulator was waiting for Parent authentication.
- The new Parent account was registered through the real mobile UI. It has no access to the older Rev22 StoryRun, which belongs to a different Parent actor. Do not impersonate that actor, transfer the run, or edit its ownership.
- Continue end-to-end by creating one synthetic Parent profile in the real UI and a new run from the already-approved synthetic turtle drawing asset in `evidence/ANDROID_DRAWING_CONFIDENCE_UI_REV22_20261119/input/synthetic_turtle_drawing.png`. This uses no fixture response or mocked output; it requires one fresh Drawing VLM inference.
- Revised live-call bound: at most one drawing-understanding inference, one catalog-first activity suggestion inference, one story-generation inference, and one silent LTX-2.5 video request (which may fan out only to confirmed storyboard scenes). No automatic retry, duplicate submission, warmup, or scene retry.
- Keep existing synthetic-only no-product-quota admission, story/subject/safety gates, and all other Rev23 boundaries. Store no signup email/password or Firebase token in evidence. If profile creation, synthetic eligibility, or any gate fails, stop before spending the next live inference.
- This amendment supersedes only Rev23 §1 starting run, §2 starting evidence, §3 M0/M1 run-resumption steps, §4 existing-run criterion, and §5 prohibition on repeating drawing inference. All other Rev23 requirements and exclusions remain active.

## Execution Amendment A2 — recover from confirmed pre-dispatch Modal failure

- Trigger: the real UI attached the synthetic drawing to a new StoryRun, then the API returned HTTP 504. Sanitized backend logs show `NotFoundError` at `function_spawn`, `modal_call_id=None`; Modal `dev` showed the drawing app stopped. No Modal function call or model inference was created.
- Redeploy the existing `sketch2life-srs23-drawing-vlm-dev` app from its pinned source in Modal `dev`. Deployment is permitted only to register the existing functions; do not invoke a health/warm-up function or model during deploy.
- The current StoryRun already owns an immutable input revision and the UI correctly refuses to upload that drawing again. Close that unresolved run only through the authenticated, existing Parent `/v1/story-runs/{run_id}/cancel` route exposed in the real UI; the route marks it `DELETE_PENDING` and does not claim to stop a provider task. The observed `NotFoundError` with no call ID establishes that this particular request never dispatched.
- Start one new StoryRun through the UI, reusing the same synthetic artwork. This permits at most one actual Drawing VLM inference for the end-to-end path; the earlier request is recorded as a pre-dispatch failure and is not counted as an inference. No direct database edit, image replacement, duplicate inference, or automatic retry.
- Add the smallest clean-architecture Parent API/UI wiring needed to invoke the existing cancellation route for this unresolved photo-analysis run. Also classify a Modal `NotFoundError` occurring specifically at `function_spawn` as a terminal pre-dispatch `MODAL_FUNCTION_NOT_DEPLOYED` failure, not an ambiguous post-dispatch outcome; add a focused regression test. Other errors and post-dispatch outcomes remain fail-closed/ambiguous.
- This amendment does not expand the one-call-per-workload limits, video authorization, synthetic-only guard, fail-closed story/video gates, or cleanup requirements. If the fresh run cannot pass drawing recognition, stop before activity inference.

## Execution Amendment A3 — synchronize the active Parent branch with dev

- Trigger: the owner directly instructed on 2026-11-19 to inspect `dev`, bring its changes into this branch, and use them.
- Remote snapshot: `origin/dev` advanced from the last shared base `ba295f1113129fa233ddc762ef29fadd92b996e8` to `a43c2aee71160926b3d7979a0235f39d735ead1c` (13 commits, including the PR #31 merge). The delta includes FEAT-081 Parent StoryRun lifecycle/history, FEAT-063 cancel/delete wording and routes, mobile startup/auth updates, and the intervening FEAT-066/API integration work.
- Approved action: merge the complete fetched `origin/dev` snapshot into `feature/fe-mobile-remediation`, preserving existing commit IDs (no rebase/reset/history rewrite). A normal Git merge commit is authorized solely as the integration record; do not push.
- Preserve every pre-existing staged, unstaged, and untracked local change. Temporarily stash only if necessary to make the merge safe, then restore and resolve conflicts by retaining the approved Rev23 behavior while adopting compatible `dev` lifecycle/API improvements. Do not discard local changes or overwrite newer dev contracts without review.
- After merge, run the focused Parent/mobile/backend checks needed to establish integration, run `python tools/validate_repository_security.py` before creating the merge commit, and record the merged commit, conflict decisions, checks, and current E2E position in this feature's evidence and status.
- This amendment authorizes only synchronization of the fetched dev delta and the validation/evidence required for the already-approved Rev23 Parent E2E. No push, unrelated feature work, credential changes, real child data, direct database edits, or extra AI inference is authorized.
- Acceptance: all commits from the fetched `origin/dev` are reachable from the feature branch; pre-existing local work is restored; the working tree and tests show no accidental loss or cross-feature behavior change; the Parent flow can continue against the integrated contracts.

