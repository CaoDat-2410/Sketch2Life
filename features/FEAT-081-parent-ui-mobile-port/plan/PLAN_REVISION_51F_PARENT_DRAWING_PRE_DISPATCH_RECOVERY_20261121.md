# FEAT-081 — Plan Revision 51F: Parent drawing pre-dispatch recovery

**Status:** APPROVED by the owner's direct 2026-11-21 instruction to check and fix Parent backend APIs as well as frontend behavior, then run the real Parent flow.
**Product authority:** FEAT-063 canonical working SRS v2.7-draft, local amendments through Rev71; unsigned. This plan does not amend product requirements.
**Feature/worktree:** FEAT-081, branch `feature/fe-mobile-remediation`; real Expo app on `emulator-5554`, driven with ADB only.

## 1. Observed failure

- The task Compose project was invoked from a worktree without explicitly loading the single root `<local-machine-path> The API therefore started with development auth and no Firebase project/credential. The SVG-guide request returned 503 before route execution. Recreating only the existing API service with the root env-file restored Firebase auth; the same UI guide request then returned 200 with five curated SVG stages.
- The same Parent UI created one StoryRun and read it back (`POST /v1/story-runs` 201; GET 200). The subsequent real drawing-analysis request returned 503. The UI read back the same run at `current_input_revision=1` and showed “no upload session”; it did not create another run. At that time the task-local MinIO container was `Exited (255)`, while PostgreSQL and ClamAV were healthy. MinIO has since been restarted. The exact backend 503 code was not visible in UI/logs because expected scanner/storage failures in the drawing route are not logged with a safe stage/code.
- `useParentController.analyzeDrawingForRun` currently locks further submissions by `runId` after any failed drawing request. That correctly protects ambiguous post-dispatch outcomes, but it also dead-ends the user after a typed failure that happened before image attachment/AI dispatch.

## 2. Scope

1. Add privacy-safe backend diagnostics for Parent drawing-analysis pre-dispatch failures. Log only request ID, fixed stage name, safe error code, and exception type where applicable. Do not log image bytes, base64, subject/topic, identity, provider error text, credentials or raw exception messages. Include the request ID with the typed response for the handled drawing-route failures.
2. Define an explicit allowlist of typed failures that prove the request did not reach AI inference (for example scanner unavailable, object storage unavailable, DB/runtime dependency unavailable, or Modal disabled before upload). Do not treat generic network errors, timeouts, unknown outcomes, worker failures, or any response after the input revision advances as safely retryable.
3. In the mobile controller, allow at most one manual retry for an allowlisted pre-dispatch failure only after reading the same StoryRun and confirming `current_input_revision == 1`. Retry uses the retained image and the same `runId`; it must not create a second StoryRun. Show a clear “Thử lại nhận diện tranh” action. Preserve the no-resubmit behavior for ambiguous/accepted AI dispatch and revision > 1.
4. Add focused backend and mobile tests for safe logging/error codes, the same-run retry path, one-retry bound, and the no-retry boundary for unknown outcomes or attached-image revisions.
5. Resume the current emulator flow with the existing synthetic Parent, profile, run and synthetic turtle image. The prior 503 is pre-dispatch (revision remained 1), so one UI retry after MinIO is healthy is permitted. Continue each AI workload at most once after a successful dispatch; proceed to story/video only if every normal SRS and safety gate passes.
6. Record exact route status, safe request IDs, elapsed time, service health, revision, Modal call ID if one exists, and final output/error in feature-owned evidence. Update FEAT-081 context/status after verification.

## 3. Limits

- Reuse the current account/profile/StoryRun and image. Do not create a second account, profile or run. Preserve all existing seed identities and entities; only the exact agent-created test account may be cleaned under Addendum 81, and only after safe Firebase↔BE1 correlation and supported content cleanup.
- No direct API/worker bypass for E2E, fixtures, preview harness, real child data, fabricated consent, direct business DB edits, migrations, DB reset/reseed, quota/payment access, quality/safety-gate relaxation, or video request before adult story review.
- Use the root `.env` only through `docker compose --env-file <local-machine-path>; do not print, copy or edit it. Recreate only the task API container when code/config changes require it. Start only task-local dependencies needed by the flow; preserve existing volumes and unrelated services.
- No Modal deployment, warm-up, app stop, or additional probe inference. Existing Addenda 80/81 per-workload/candidate limits remain in force. No commit or push.

## 4. Acceptance

- The backend identifies pre-dispatch scanner/storage/runtime failures with a safe request correlation and typed code, without logging image or identity data.
- With `current_input_revision == 1` and an allowlisted pre-dispatch error, the UI offers at most one explicit retry on the same StoryRun and reuses the selected image.
- Unknown/timeout/accepted outcomes and any revision above 1 never trigger another drawing request automatically or manually from this recovery action.
- Focused tests pass; the actual Android UI flow verifies the backend result and continues or records the terminal blocker. No duplicate run is created.

## 5. Authorized files

- `backend/src/sketch2life/interfaces/http/routers/parent_ai.py`
- focused backend test(s) under `backend/tests/contract/` or `backend/tests/unit/`
- `apps/ui-mobile/src/parent/presentation/navigation/useParentController.ts`
- `apps/ui-mobile/src/parent/presentation/screens/CaptureScreen.tsx`
- the existing selected-photo type definition under `apps/ui-mobile/src/parent/`
- focused mobile tests under `apps/ui-mobile/tests/`
- `features/FEAT-081-parent-ui-mobile-port/{CONTEXT.md,approvals/TASK_APPROVAL.md,status/STATUS.md,plan/**,evidence/**}`

No other paths are authorized by this amendment.
