# FEAT-081 — Plan Revision 49: clarify video loading and make one owner-directed candidate attempt

**Status:** APPROVED by the owner's direct 2026-11-20 request: “gọi thửu vid đi” and “fix nào gọi đc nhé, ngoài ra thì thêm loading state rõ hơn cho cái này”.  
**Product authority:** FEAT-063 canonical working SRS v2.7-draft / Rev67; unsigned. This plan is a synthetic development experiment and does not amend product requirements.  
**Feature/worktree:** FEAT-081, branch `feature/fe-mobile-remediation`.

## 1. Goal

Improve the Parent technical-video screen so a parent can tell what the video worker is doing, what happens next, and whether the app is still waiting. Then make one real silent LTX-2.5 technical-candidate request from the current Android Parent UI for the current synthetic run, and record the actual result.

The current story draft was inspected and contains mixed-script text (`các動作`) and awkward age phrasing. The owner has now explicitly asked to try video. This amendment permits that one synthetic technical experiment despite the known story-language defect; it does **not** mark the story as linguistically acceptable, alter the story, or weaken any product quality/safety rule.

## 2. Existing runtime facts

- Current synthetic StoryRun: `ff1021f5-e9e6-4343-9da3-ced08ad9de69`, on the Parent story-review screen in the real Expo app.
- Current artwork is the synthetic turtle image already recorded in `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/`.
- Story API returned revision 1 successfully. The actual visible mixed-script defect is recorded in the Rev46 run report and screenshot.
- Existing Parent candidate route requires an adult-confirmed story revision/hash, active synthetic profile, local/test environment, `modal_dev`, synthetic pilot, and the explicit candidate flag. It is idempotent and dispatches to the existing Modal LTX worker.
- `VideoCandidateScreen` currently has state labels and a 30-second poll, but the wait lacks a clear stage indicator and a distinct explanation while the first request is being dispatched.

## 3. Approved work and hard limits

1. Preserve the actual Parent UI → backend → deployed Modal path. Use the current account, profile, StoryRun, drawing, activity selection and story revision only.
2. The owner authorizes confirming the exact displayed revision **only to run this one synthetic technical video test**. Record this as an owner-directed test override, not as a successful story-quality review. Do not modify the story text or generate another story.
3. Make at most one video-candidate submit and at most one LTX inference. Do not send a second request if the first returns an uncertain result or has a Modal call ID. If a deterministic pre-dispatch defect prevents Modal from accepting the one request, capture its safe error and stop for a new bounded approval; do not create a second candidate or bypass idempotency.
4. Keep all existing authorization, ownership, current-run, source-hash, story revision/hash, synthetic-profile, local/test, `modal_dev`, feature-flag, and no-quota candidate guards. Do not add a quality-gate bypass to backend code or change SRS/product readiness semantics. Do not read or write quota/billing.
5. Reuse `sketch2life-srs23-dev-video`; do not deploy, warm, stop, or change Modal apps, secrets, model checkpoints, prompts, or the worker.
6. Make the video loading UI clearly reflect only the API's actual states: `STAGING`, `DISPATCHING`, `QUEUED`, `GENERATING`, `AWAITING_RECONCILIATION`, `CANDIDATE_READY`, and `FAILED`. Do not show fabricated percentages or unsupported model progress. While dispatch is pending, explain that one request is being sent and discourage duplicate taps. While a candidate is active, show the current phase, next phases, automatic status-check interval, and a manual status action. Terminal/unknown states must clearly say whether the app will retry; it must never submit a second generation automatically.
7. Use existing mobile design tokens and Vietnamese copy. Keep the progress view compact, accessible to screen readers, and visually consistent with the Parent creative screens.
8. Do not create accounts, profiles, runs, or fixtures. Do not edit `.env`, credentials, SRS, or migrations. Do not commit or push. Leave user and unrelated services running.

## 4. Implementation sequence

### M0 — preflight

- Confirm the task API, current authenticated Android session, current run/story revision, candidate table state, local synthetic-only configuration, Modal credential presence (boolean only), and deployed Modal app using read-only checks. Never print secrets or raw child/profile/story content into terminal logs.
- Review the candidate route/service/adapter and the current screen/controller wiring. Fix only a scoped defect that would prevent the single authorized UI submission while preserving every guard above.

### M1 — Parent video loading state

- Update `VideoCandidateScreen` and, if useful, a small presentation-level progress mapper.
- Show a clear initial dispatch state before a candidate response exists; render an indeterminate spinner, short Vietnamese explanation, and duplicate-submit warning.
- Map backend states into a compact ordered phase list; highlight the current phase, mark completed phases, and avoid percentage claims.
- For `AWAITING_RECONCILIATION`, state that the outcome is unknown and no new job will be sent; offer status refresh only. For `FAILED`, show the safe error code and stop. For `CANDIDATE_READY`, show technical metadata and the existing private preview action, retaining `safety_validation=NOT_RUN` and `product_playable=false` labels.
- Keep the existing 30-second status polling and expose that interval in the UI. Do not increase API polling frequency for this change.
- Add focused presentation-mapper coverage if a pure mapper is introduced. Run mobile typecheck and the focused existing/mobile checks needed for the change.

### M2 — one real video request

- Reload the active Expo bundle without signing out if possible. Review the exact visible synthetic story and use the Owner's explicit test-only instruction to confirm that exact revision through the UI, recording the confirmation as a technical test override rather than story quality acceptance.
- Submit once from the UI. Use the existing candidate request key/idempotency flow; do not call the product endpoint or Modal worker directly.
- Poll only the candidate status endpoint through the app. If a candidate reaches `CANDIDATE_READY`, open the authenticated private preview in the UI and capture the output. If dispatch fails before Modal assigns a call ID, record the exact safe error and stop; if a call ID exists, never retry.
- Do not claim the video passed story fidelity, consistency, safety, or product playback. Candidate metadata is a technical-preview result only.

### M3 — evidence and status

- Append screenshot, API request/correlation ID, candidate ID, Modal call ID if returned, state transitions, timings, and safe failure details to `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/`.
- Update FEAT-081 context/status and record that the story language defect remains unresolved even if the technical video completes.
- No commit, push, SRS edit, quota/billing operation, Modal app stop, or unrelated cleanup.

## 5. Acceptance criteria

- Parent video screen clearly explains initial dispatch and each actual backend state in Vietnamese, with accessible busy/status announcements, no false percentage, and no duplicate submit affordance.
- Focused UI checks and typecheck pass; the updated state is observed on the Android emulator.
- Exactly one Parent UI video request is submitted for the current synthetic StoryRun. If Modal accepts it, correlate the single call through the persisted status to technical candidate/preview; otherwise report the exact stop point.
- No second story inference, video retry, quota access, business-DB bypass, product-gate weakening, or false claim that the mixed-language story/video passed product quality or safety.

## 6. Authorized repository paths

- `apps/ui-mobile/src/parent/presentation/screens/VideoCandidateScreen.tsx`
- `apps/ui-mobile/src/parent/presentation/screens/videoCandidateProgress.ts` (only if a mapper is needed)
- `apps/ui-mobile/tests/**` (focused tests for this loading-state behavior)
- `backend/src/sketch2life/application/services/parent_video_candidate_service.py` (only a narrow pre-dispatch correction if M0 identifies one)
- `backend/src/sketch2life/infrastructure/ai/modal_silent_story_video.py` (only a narrow pre-dispatch adapter correction if M0 identifies one)
- `backend/src/sketch2life/interfaces/http/routers/parent_video_candidates.py` (only if a route defect blocks the approved UI path; no guard relaxation)
- `backend/tests/unit/test_parent_video_candidate_manifest.py`
- `backend/tests/unit/test_modal_silent_story_video_adapter.py`
- `features/FEAT-081-parent-ui-mobile-port/{CONTEXT.md,approvals/TASK_APPROVAL.md,status/STATUS.md,plan/**,evidence/**}`

No other repository paths are in scope.
