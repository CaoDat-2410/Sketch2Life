# FEAT-081 — Plan Revision 41: refresh remaining Parent UI and add the video flow

- **Status:** APPROVED by the owner's direct instruction on 2026-11-20 (Asia/Saigon): “fix các phần chưa phải UI bản mới và thêm luồng vid vào đi”.
- **Feature/worktree:** FEAT-081, branch `feature/fe-mobile-remediation`, worktree `<local-machine-path>
- **Product authority:** FEAT-063 canonical working SRS v2.7-draft, using the owner-provided Rev67 boundary. §§5–6, 9, 21 and Rev66–67 govern Parent ordering, adult script confirmation, video admission, silent video, safety/playback, and the pinned post-video activity list. The SRS remains unsigned. FEAT-081 records are implementation evidence only.
- **Starting evidence:** `evidence/PARENT_API_AUTH_FULL_E2E_REV24_20261119/REV32_AUTH_RECOVERY_AND_E2E/51-rev40-parent-catalog-and-story-e2e.md` and screenshots 39–50, plus live emulator capture `evidence/PARENT_UI_VIDEO_REV41_20261120/00-before.png`. The actual Expo app generated and persisted activity suggestions, selected one activity, and generated a five-scene story. The story screen uses the current purple Parent UI, but its prose includes model-generated character-count fragments such as “(149 ký tự)” and stray numeric suffixes. The fallback-copy fix is in source/bundle but was not confirmed on the emulator after bundle reload. The earlier evidence left the story at adult review; the current live screen displays an adult-confirmed badge, but that claim must be verified from the authenticated server state/hash before video admission. Parent video capability currently reports unavailable; the client operations return unavailable; `deployment/modal/srs_v23/video_app.py` validates an envelope then fails closed because LTX is not wired.

## 1. Goal

Bring the remaining active Parent workflow screens into alignment with the current Expo Parent UI, fix the story-output defect at its source, and implement the real authenticated Parent video path from adult-confirmed script to private playable result and post-video activities.

The target flow is:

`current Parent UI → selected/persisted primary activity → clean story revision → adult reviews and confirms its exact hash → real quota/compute admission → persisted video job → LTX-2.5 silent scene generation on Modal → consistency/technical and automatic safety gates → private playback in the app → pinned post-video activities → adult completes the run or requests a quality redo`.

Use the real Expo Android app, authenticated synthetic Parent/profile, real backend persistence, and actual Modal inference for any live model stage. Do not use the preview harness, fixtures, mock success, direct database writes, the legacy session-video API, or Wan as a substitute.

## 2. Product and safety invariants

- Parent keeps the current new UI design language, routes, copy style, and reusable components. The audit identifies only active screens that still use old layouts or stale unavailable states; do not replace the new UI with a fixture-like screen or a separate design.
- Preserve the required Parent order: image and subject/context review, exactly one selected primary activity before story, immutable story revision, then adult confirmation of that exact revision before video admission.
- Never mark the existing draft confirmed on the owner's behalf. The adult gate is an explicit UI action after reviewing the final story; video is not dispatched until that action is persisted by the backend.
- The video request is server-derived from the run's confirmed story revision/hash, selected activity receipt, source drawing asset/hash, and current context snapshot. The client cannot supply or override these references.
- Use the SRS LTX-2.5 target on Modal L40S at the pinned candidate `Lightricks/LTX-2.5@49b093a39c19169a8a81721dcc541e07e945232f`. Do not use Wan, FLUX, or the legacy session/story-video route.
- Video output is silent for this owner-requested slice. Do not invoke TTS or generate audio; defer narration to its separate future service. Prompts describe scene action/camera movement while preserving the child's original drawing as the visual reference.
- Keep existing schema, story, age, consent, safety, activity, and content gates. Do not weaken quality gates, repair model prose by silently deleting text, or show a video unless technical, consistency, and automatic safety validation all pass.
- Use real quota/compute admission. Do not bypass, edit, seed, or otherwise change quota/payment/billing in this plan. A request rejected before admission must not call Modal. A request accepted by admission follows the existing no-refund rule.
- Synthetic data only. Do not expose prompt, image, child/profile identifiers, tokens, or credentials in logs/evidence. Do not read or edit `.env`/secrets.
- Preserve all pre-existing staged, unstaged, and untracked work. No commit, push, branch/history change, destructive cleanup, or unrelated service shutdown.

## 3. Work sequence

### M0 — runtime and source audit

1. Inventory the actual Expo route/screens and compare them with the current shared UI components. Record which screens are already current, which still show stale/legacy copy or unavailable video controls, and which screens the video flow needs.
2. Confirm the emulator is running the real Expo application, not `ParentVisualPreviewHarness`. Verify the currently served API/OpenAPI and task-local Docker project without printing environment values or touching unrelated services.
3. Read the existing story-output response and worker code through privacy-safe paths. Trace character-count/numeric fragments to the prompt, constrained output, parser, mapping, or UI; do not infer the source from the screenshot alone. Verify the current story confirmation/hash from server-owned state; a client badge alone is not sufficient for dispatch.
4. Verify the existing Parent video route, billing admission, Story/AI Job persistence mappings, Modal staging path, result storage, and safety/consistency implementation. Compare them with SRS and the Data Table Register before choosing additive changes.

### M1 — align remaining Parent screens and fix story output

1. Update only active Parent screens that fail the M0 current-UI audit; use the existing `ui.tsx` tokens/components, preserve concise child-friendly Vietnamese copy, and keep the screen-per-workflow layout.
2. Make the activity fallback explanation render in the real reloaded Expo bundle without exposing internal model/catalog fields.
3. Correct the source of story character-count/numeric metadata leakage. Keep the current story JSON contract and semantic gates. Reject malformed prose at the worker/API boundary rather than stripping or rewriting accepted story text in the UI.
4. Make worker terminal-event logging agree with the correlated job outcome. Keep logs structured and content-free; do not add raw prompt, output, image, audio, child ID, or token fields.
5. Add focused regression tests for each corrected source path. Do not send a new Qwen call until offline checks pass; allow at most one UI-driven story rewrite on the existing synthetic run if needed to produce a fresh reviewable revision.

### M2 — authenticated Parent video contract and durable lifecycle

1. Add/version the Parent StoryRun video request, status, playback, complete, and quality-redo operations only where current routes are missing. Keep the API names and response schemas aligned with the established `/api/parent/v1/` contract and served OpenAPI.
2. Before accepting a request, verify Parent ownership, active run state, exact current script hash/revision is adult-confirmed, primary activity receipt is present, drawing/context hashes still match, the run is not stale/deleting, and an idempotency key is valid.
3. Execute the real admission sequence before dispatch. Persist video generation, ordered scene attempts, AI job references, terminal state, validated media asset refs, and lifecycle projections using the Story/AI Jobs/Billing/Core ownership boundaries in the Data Table Register. If source mappings are incomplete, update the matching DTR first, then add only additive migrations. Apply a migration only to a verified task-local disposable database.
4. Expose explicit pending, generating, safety-validation, ready, safety-blocked, failed, and reconciling states. A timeout or lost response must be reconciled by job ID; never submit a duplicate generation from the client automatically.
5. Return private short-lived playback access only after validation. Post-video activities come from the pinned run snapshot or exact accessible pinned lesson version; no new catalog query or AI fallback is allowed after video.

### M3 — real LTX-2.5 Modal worker and silent composition

1. Replace the fail-closed scaffold with the pinned official-compatible LTX-2.5 image-to-video path. Confirm model/license access and the existing Modal model-volume/secret by presence only; do not expose credential values.
2. Stage only the synthetic source drawing and the adult-confirmed, ordered storyboard through the approved isolated Modal transfer path. Function arguments carry opaque IDs, manifest hash, and bounded metadata—not raw media bytes or storage credentials.
3. Generate scenes from the original drawing/reference and the approved scene action; preserve scene order and source lineage. Use bounded function/job deadlines and structured safe logs. For this live acceptance run, send one video request with no manual retry, duplicate submission, warm-up, or scene retry.
4. Compose validated silent clips deterministically. No narration, TTS, music, or sound effects are generated in this slice.
5. Run the existing versioned technical, consistency, and automatic safety checks fail-closed. If there is no approved safety/consistency implementation or calibration suitable for the generated result, keep playback blocked and record the exact missing gate; do not invent a permissive threshold.

### M4 — Parent video UI

1. Replace the current unavailable capability result with the real Parent video capability, while still reflecting backend admission and gate errors accurately.
2. Add current-style progress/status UI with resumable status reads, clear stage/error copy, and no fake percent-complete or optimistic success.
3. Add the actual private playback screen with source/story context, captions only if present in the validated output, the pinned post-video activity list, and adult `Hoàn tất` / `Tạo lại` actions according to server state.
4. A quality redo hides the old playback only after the backend accepts the redo, returns to script review, and requires confirmation of the new exact story revision before another video request. Do not implement unapproved quota/refund behavior.

### M5 — verification and evidence

1. Run focused Modal contract/worker tests, backend Parent contract/service/repository tests, mobile tests and typecheck, plus repository diff/security checks relevant to this change.
2. Run the real Android UI path with the existing synthetic Parent/profile/artwork and persisted selected activity. No fixture or backend-only substitute.
3. If M1 needs a fresh story, make at most one Qwen story rewrite through the UI after offline checks. Stop at the adult script review screen and present the exact rendered result for adult confirmation; do not self-confirm.
4. After adult confirmation and successful real admission, make at most one silent LTX-2.5 video request from the UI, with no retry. If quota/admission, safety, Modal model access, or any earlier contract gate fails, capture the failing gate and stop before the next cost-bearing stage.
5. Capture Android screenshots for the updated active workflow and all AI-generated video outputs. Save sanitized API/worker logs, request/job/call IDs, UTC timings, model/checkpoint, state transitions, and failure codes under the feature evidence directory.
6. Stop only services/apps started or used by this plan after evidence capture. Leave unrelated Modal apps and user-owned services untouched.

## 4. Acceptance criteria

- Active Parent flow screens that were identified as old/stale use the current UI components and work at Android emulator resolution; the app is the real Expo app and each workflow step is a separate screen.
- The activity fallback copy is visible after a real app bundle reload and does not expose `candidate_activities`, raw model reasons, or implementation terms.
- Story prose contains no appended character-count/evaluator metadata. The backend/worker still enforces the existing strict story contract and safety rules; malformed output fails closed.
- Backend job logs show one consistent terminal result for the actual worker outcome without recording private payloads.
- Video cannot be requested before adult confirmation of the exact current story hash and successful server-side quota/compute admission. Invalid, stale, duplicate, unauthorized, or unconfirmed requests are rejected before Modal dispatch.
- A valid request uses the real pinned LTX-2.5 Modal worker, yields ordered silent scene output from the synthetic drawing, and enters `VIDEO_READY` only after technical/consistency/safety checks pass. Otherwise the exact failure/blocked state is visible and playback stays unavailable.
- The Parent can resume status after navigation, play the private validated output, see the correct pinned post-video activity list, and complete the run through the real UI.
- No fixture, fake success, data mutation outside authenticated routes, quota bypass, secret disclosure, or commit/push.

## 5. Bounded live-call authority

- The new owner request authorizes implementation and real UI verification of this slice. The existing unconsumed video-call authority in TASK_APPROVAL Addendum 41/42 remains capped at one real LTX request, scenes only as required by the confirmed storyboard, with no retries. This plan does not increase that call limit.
- Existing selected activity and source artwork are reused; no new drawing-understanding or activity inference is authorized. At most one story rewrite is allowed only to correct the visible output defect and only after offline checks.
- The exact adult-confirmation gate and real admission are mandatory. No provider request is made before both are verified.
- If no live entitlement is available, do not bypass quota. Record the server rejection and finish API/UI acceptance up to the pre-dispatch gate.

## 6. Authorized paths

- `apps/ui-mobile/src/parent/**`
- `apps/ui-mobile/tests/**` (Parent/video focused tests only)
- `backend/src/sketch2life/application/**` (Parent StoryRun video orchestration and required ports/services only)
- `backend/src/sketch2life/contracts/schemas/**` (versioned Parent video contracts only)
- `backend/src/sketch2life/domain/**` (video lifecycle/domain rules only)
- `backend/src/sketch2life/infrastructure/ai/**` (Modal LTX adapter and safe terminal outcome mapping only)
- `backend/src/sketch2life/infrastructure/persistence/**` (Parent Story/AI Job video persistence only)
- `backend/src/sketch2life/interfaces/http/**` (Parent video router/composition/OpenAPI only)
- `backend/tests/**` (focused Parent/video/Modal regression tests only)
- `backend/alembic/versions/**` (additive migration only if M0 proves one is needed; task-local disposable DB only)
- `deployment/modal/srs_v23/**` (LTX-2.5 worker, contracts, workload record, and focused tests only)
- `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` (only if a matching persistence mapping must be added)
- `features/FEAT-081-parent-ui-mobile-port/{CONTEXT.md,approvals/TASK_APPROVAL.md,status/STATUS.md,plan/**,evidence/**}`

No other paths are authorized by this plan.
