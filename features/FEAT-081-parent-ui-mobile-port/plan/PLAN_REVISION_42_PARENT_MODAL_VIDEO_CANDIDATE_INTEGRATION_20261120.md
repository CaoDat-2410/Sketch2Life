# FEAT-081 — Plan Revision 42: connect the existing Modal LTX worker to Parent

**Status:** APPROVED by the owner's direct instruction on 2026-11-20 (Asia/Saigon): “nối cái đó vào đi”. This amendment also records the owner's earlier instruction that quota management is being handled separately and the dev flow may run temporarily without quota.

**Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>

**Product authority:** FEAT-063 canonical working SRS v2.7-draft, local amendments through Rev71. The SRS remains unsigned. This plan adds a **local/test synthetic candidate-preview path**; it does not redefine product admission, `VIDEO_READY`, safety, or playback requirements.

## 1. Audit finding and amendment boundary

The Modal app `sketch2life-srs23-dev-video` is already deployed and has real LTX-2.5/L40S scene and silent-story functions. FEAT-067 contains real candidate outputs. Do not rebuild or redeploy the worker just to create a second copy. The current FEAT-081 worktree is missing the Parent video dispatcher and UI actions; FEAT-067's Parent request/status service currently fails closed with `VIDEO_ADMISSION_DEPENDENCIES_UNAVAILABLE` and does not dispatch to Modal.

This amendment supersedes only Rev41's incorrect assumption that LTX must first be implemented. It narrows this slice to connecting the existing worker to the Parent flow. It permits a temporary **dev-only, synthetic-only, no-quota candidate run** because Billing admission is being implemented separately. It does not authorize a quota bypass in staging/production or treating a generated candidate as product-ready.

## 2. Goal

From the real Parent story screen, an adult can request a silent LTX candidate only after confirming the exact current story revision/hash. Backend loads the server-owned source drawing and confirmed storyboard, stages their hashed manifest and media to the existing Modal scratch volume, dispatches one idempotent LTX job, persists its state, stores the result in private MinIO, and serves it through an authenticated preview route. The Expo UI can resume status and show the generated candidate as a clearly labeled **technical preview**.

Target dev path:

`Parent reviews story → adult confirms exact revision/hash → request candidate → server verifies synthetic/dev gates → persist generation intent → stage source + manifest → Modal spawn → status polling/reconciliation → verify worker hashes and silent MP4 profile → private MinIO candidate → authenticated technical-preview playback`.

## 3. Invariants and limits

- Use only `generate-silent-story-video` from the existing deployed `sketch2life-srs23-dev-video` app. Preserve the pinned LTX-2.5 checkpoint, model profile, Modal volume names and the worker's versioned input/output contracts from FEAT-067. Do not call Wan, Lightning, FLUX, or the legacy session-video route.
- The client submits only `expected_story_revision`, `story_sha256`, and an idempotency key. It cannot choose the image, story, prompt, scene list, profile, storage key, Modal call ID, or output URL.
- Before dispatch, the backend verifies Parent ownership, active run, one attached source drawing, selected primary activity receipt, exact adult-confirmed story revision and hash, current run/input revisions, and profile data origin.
- No-quota dispatch is allowed only if all of these hold: `SKETCH2LIFE_ENV` is `local` or `test`; explicit dev-candidate feature flag is enabled; `ai_provider=modal_dev`; synthetic pilot is enabled; the resolved profile is `SYNTHETIC_DEV` or `SYNTHETIC_TEST`; and the caller is an authenticated Parent. Default the feature flag to false. Production/staging configuration must fail closed. The code must not read or write Billing quota or AI Policy receipts in this mode.
- This path yields `CANDIDATE_READY`, never `VIDEO_READY`. Candidate status must state `safety_validation=NOT_RUN` and `product_playable=false`. Do not enable normal playback, completion, quality redo, public URL or post-video product progression from this preview. The private preview endpoint is available only under the same local/test synthetic gates.
- Preserve original artwork and lineage. Verify the source hash before staging, the worker input manifest hash before dispatch, and the worker's output hash/manifest before storing. Do not log raw story text, drawing bytes, prompts, auth tokens, child/profile data, or storage credentials.
- Use asynchronous Modal spawn and durable status; do not hold an HTTP request open for the multi-minute inference. Idempotent replay returns the same generation and never starts a second GPU call. Polling must not reset adult-wait/activity timestamps.
- One live inference at most, only through the real Parent UI after all guards pass. No warm-up, duplicate tap, automatic retry, manual retry, or scene retry in this slice. If no clean, confirmed synthetic story is available, stop before Modal dispatch.
- Keep the existing technical validation. No safety or continuity gate may be weakened. The technical preview is not a substitute for automated safety; product playback remains blocked until the proper safety/consistency gates are implemented.
- Silent output follows the owner's video direction. The current SRS still describes narration/subtitles in its target pipeline; record that mismatch, but do not silently edit the SRS in this implementation slice.
- Do not edit the user's `.env`, credentials, Firebase config, or Modal secrets. Add placeholders/configuration wiring only to `.env.example` and Compose as needed.

## 4. Implementation sequence

### M0 — reconcile contracts and current database lineage

1. Use the FEAT-067 worker and result evidence as implementation input; review the exact input/output manifest schemas and required volume paths.
2. Compare FEAT-067's `story.video_generations` migration/table contract with the current FEAT-081 migration heads. Reuse compatible schema/contract pieces; write one additive migration only if the current branch lacks the required fields. Do not run a migration against a shared database.
3. Confirm the current source-drawing reference can be resolved through the existing private object-storage adapter and that output can be stored/read through private MinIO.

### M1 — backend dev-candidate orchestration

1. Add typed settings and a default-off `parent_video_dev_candidate_enabled` flag. Compose passes it from the single root `.env`; do not split configuration into per-service env files.
2. Add an application port for the LTX worker and a Modal adapter that uses the existing app/function names and Modal credentials already passed to the backend. Stage bounded files/manifests to the existing Modal scratch volume; keep provider calls out of domain/application rules.
3. Implement an idempotent Parent video-generation request and status service using durable state. Persist intent before dispatch; store the opaque Modal call reference internally; reconcile RUNNING/succeeded/failed without duplicate dispatch.
4. On completion, validate output hashes, manifest lineage, zero audio streams, dimensions/frame rate/duration/size and existing technical rules. Save the candidate to private MinIO. Provide an authenticated, owner-scoped, no-store preview stream that remains disabled outside local/test synthetic mode.
5. Keep product admission fail-closed outside the explicit dev candidate path. Never return a product `VIDEO_READY` state from this path.

### M2 — Parent Expo wiring

1. Add the real request/status/preview operations to the Parent API client and application port/use case, following the existing clean-architecture boundary.
2. Add a concise progress screen/state after adult story confirmation. Poll persisted status with bounded intervals, allow navigation away and resume, and present safe terminal errors without provider internals.
3. Add a separate technical-preview screen that streams the authenticated candidate and visibly labels it as a synthetic development preview. Do not show product completion/redo actions for this candidate.
4. Keep the current visual tokens/components and workflow ordering. Do not use the visual preview harness or hard-coded candidate/video fixtures.
5. Verify the request/status/preview route mapping with focused mobile and backend OpenAPI contract tests; these checks must not call Modal or create test media.

### M3 — record implementation evidence

1. Update the feature context/status and this evidence folder with the exact implemented contract, migration status, Modal function metadata, and any blockers.
2. Do not send a Modal request as part of this code-only slice unless the currently approved one-call synthetic UI allowance is still valid and a clean confirmed synthetic story is present. If it is used, call once from the real UI, capture safe request/call IDs and timings, and do not retry.
3. No commit, push, broad branch merge, Modal app stop, or unrelated service shutdown.

## 5. Acceptance criteria

- The existing deployed Modal worker is reused; no duplicate app or alternative model is created.
- Request and status endpoints are authenticated, Parent-owned, versioned, idempotent, and bound to the exact server-confirmed story and source-drawing hashes.
- Production/staging cannot enable the temporary no-quota candidate path; local/test additionally requires the explicit flag, `modal_dev`, synthetic pilot, and a synthetic profile.
- Invalid, unconfirmed, stale, real-profile, unauthorized, duplicate, or oversized inputs fail before Modal dispatch.
- A valid dev request persists one generation and uses Modal asynchronous spawn; API polling resumes from durable state and does not dispatch again.
- The completed MP4 is privately stored, owner-scoped, and only streamable as a labeled technical preview in local/test synthetic mode. It is not `VIDEO_READY` or product playback.
- Worker errors map to safe terminal codes; logs do not include prompts, raw story/image/profile content, tokens or secrets.
- The existing Android Parent UI exposes request, progress/resume and candidate preview as separate workflow states using current design components.
- No fixture output, quota ledger mutation, production bypass, SRS rewrite, or false safety/product-ready claim is introduced.

## 6. Authorized paths

- `apps/ui-mobile/src/parent/**`
- `backend/src/sketch2life/application/**`
- `backend/src/sketch2life/contracts/schemas/**`
- `backend/src/sketch2life/domain/**`
- `backend/src/sketch2life/infrastructure/ai/**`
- `backend/src/sketch2life/infrastructure/persistence/**`
- `backend/src/sketch2life/infrastructure/storage/**`
- `backend/src/sketch2life/interfaces/http/**`
- `backend/alembic/versions/**` (additive migration only)
- `deployment/modal/srs_v23/**` (only if source review finds a backward-compatible worker contract correction necessary; do not redeploy without checking first)
- `compose.yaml`, `.env.example`
- `features/FEAT-081-parent-ui-mobile-port/{CONTEXT.md,approvals/TASK_APPROVAL.md,status/STATUS.md,plan/**,evidence/**}`
- `backend/tests/unit/test_parent_video_candidate_manifest.py`
- `backend/tests/unit/test_modal_silent_story_video_adapter.py`
- `backend/tests/contract/test_openapi_contract_catalog.py`

No other paths are authorized by this plan.
