# FEAT-081 — Plan Revision 22: verify drawing confidence fix in Android UI

- Status: APPROVED by the owner's direct instruction on 2026-11-19 (Asia/Saigon): “sửa r thì test lại trên UI đi, lựa ảnh nào phù hợp vs trẻ”.
- Feature/worktree: FEAT-081, branch `feature/fe-mobile-remediation`.
- Depends on: Plan Revision 21 / TASK_APPROVAL Addenda 38–39, which added the missing confidence field to the local Qwen drawing worker source.
- SRS authority: FEAT-063 canonical working SRS v2.7-draft, local amendments through Rev70; unsigned. AT-14 and AC-55 govern the visible candidate/confidence and adult-review behavior.

## 1. Goal

Verify through the real Parent Android UI that the deployed Qwen drawing worker now returns a candidate, visible features, and numeric confidence that the backend accepts and the UI displays. Use a child-friendly synthetic drawing, not a fixture or preview harness.

## 2. Test input and data

- Use `evidence/ANDROID_E2E_REV20_20261119/synthetic_turtle_drawing.png`: a simple, colorful, clearly identifiable turtle illustration with no child or personal data. It is appropriate for an early-childhood drawing prompt and matches the selected `Động vật` topic / `Rùa con` subject.
- Use an authenticated synthetic Parent and synthetic profile through the real app/API flow. If the prior failed StoryRun prevents a fresh run, create a fresh synthetic Parent/profile through the UI; do not edit the database or reuse the prior image-bound StoryRun.
- Select topic/object through the live UI/API where available, then select the image in Android Photo Picker. Do not inject a successful response, use a fixture, or call the AI route outside the UI.

## 3. Bounded execution

1. Run the focused offline drawing parser regression file.
2. Deploy only the updated Modal drawing app from this worktree. Do not invoke a GPU worker for health/warm-up.
3. Start the task-local backend/required infrastructure and Expo Metro; check API health from the task container.
4. Run one real Android UI drawing-understanding request. No retry or second inference. Stop at the understanding/review screen.
5. Capture sanitized screenshots and record request/Modal IDs, timestamps, HTTP result, confidence presence/range, UI presentation, and timing without raw image/model text or credentials.
6. Stop task-local Docker, Metro, the Modal drawing app, and the emulator started for this run. Leave the deployed video app and unrelated long-running stacks untouched.

## 4. Acceptance criteria

- The real Android app submits the synthetic turtle image through the Parent workflow and receives HTTP 200 for drawing understanding.
- Response includes `candidate_subject`, one to four `visible_features`, numeric finite `confidence` in `[0,1]`, `adult_confirmation_required: true`, and a review-required decision.
- The UI displays the candidate and confidence and still requires an adult to confirm/correct the subject.
- The flow does not report success if the worker/API contract fails. No retries are sent.
- Evidence identifies what was and was not verified; no child personal data or credentials are recorded.

## 5. Explicit exclusions

- No activity suggestion, story generation/revision, narration, video, quota, payment, consent changes, or database migration.
- No fixture, preview harness, direct database insert/edit, or raw backend-only substitute for the UI request.
- No tests beyond the named focused parser regression file, no commit, and no push.

## 6. Authorized paths

- Existing approved implementation: `deployment/modal/srs_v23/drawing_vlm_app.py`.
- This plan and `approvals/TASK_APPROVAL.md`.
- New evidence under `evidence/ANDROID_DRAWING_CONFIDENCE_UI_REV22_20261119/`.
- FEAT-081 `CONTEXT.md` and `status/STATUS.md`.
