# Parent → Modal LTX video candidate integration — Rev42

**Date:** 2026-11-20  
**Branch/worktree:** `feature/fe-mobile-remediation` / `.codex-worktrees/fe`  
**Plan:** [PLAN_REVISION_42_PARENT_MODAL_VIDEO_CANDIDATE_INTEGRATION_20261120.md](../../plan/PLAN_REVISION_42_PARENT_MODAL_VIDEO_CANDIDATE_INTEGRATION_20261120.md)  
**Result:** Code and client contract connected; runtime video generation is not yet verified.

## What is connected

The Parent Expo flow now exposes a technical-preview action after an adult confirms the exact story revision. The mobile client calls the FEAT-081 backend, which validates ownership and the confirmed story/source/activity lineage, records an idempotent candidate job, stages the input manifest and source image, and dispatches through the existing Modal LTX worker. The user can revisit job status and, when ready, stream a private authenticated preview.

The existing Modal app/function are reused; no second app or model was created:

- Modal app: `sketch2life-srs23-dev-video`
- Function: `generate-silent-story-video`
- Worker profile: existing FEAT-067 LTX-2.5 deployment on L40S

The candidate path does not read or mutate quota/billing. It remains restricted to local/test, explicit feature enablement, `ai_provider=modal_dev`, synthetic-pilot mode, and an authenticated synthetic Parent/profile. The feature flag defaults off. The result is always a technical candidate: `CANDIDATE_READY`, `safety_validation=NOT_RUN`, `product_playable=false`; it cannot become product `VIDEO_READY` or unlock product completion/redo.

## HTTP contract

All routes are under `/v1/story-runs`, require an authenticated Parent, and enforce Parent ownership.

| Method and path | Purpose |
|---|---|
| `POST /{run_id}/video-generations` | Idempotently request one candidate. Requires `Idempotency-Key`; JSON contains only `expected_story_revision` and `expected_story_sha256`. Returns `202` with candidate ID/state. |
| `GET /{run_id}/video-generations/current` | Resume the current candidate status for the run. |
| `GET /{run_id}/video-generations/{video_candidate_id}` | Poll one persisted candidate job. |
| `GET /{run_id}/video-generations/{video_candidate_id}/preview` | Stream the owner-scoped private MP4 with `private, no-store` headers after candidate validation. |

The client cannot provide an image, prompt, storyboard, storage key, Modal call ID, or output URL. The server binds work to its stored confirmed story and drawing and to the saved activity selection.

## Files/areas wired

- Backend application port/service, durable repository, Modal adapter, versioned request/status schemas, authenticated router, OpenAPI projection, and additive Alembic migration.
- Compose and `.env.example` placeholders for the default-off candidate flag/provider and Modal token names. No actual `.env`, Modal Secret, token, or credential was read or changed.
- Parent API client/application port/use case/controller, story-screen entry action, progress/resume screen, and technical-preview screen.
- Focused backend and mobile contract/unit tests.

## Verification

- Backend focused unit/contract run: **19 passed** (candidate manifest, Modal adapter, app composition, OpenAPI catalog).
- Mobile typecheck: **passed**.
- Mobile tests: **126 passed across 15 files**; UI copy/recovery validator passed.
- Ruff on the new backend implementation/test files: **passed**.
- `git diff --check`: **passed**.
- Migration source is an additive Alembic head: `20261120_parent_video_candidate` (`story_run_lite`). **It was not applied to any database.**

These checks establish source-level wiring and contract consistency only. They do not establish that the local API, database, credentials, Modal dispatch, or Android runtime completed a video request.

## Not verified / remaining blockers

1. No Modal inference was sent in this implementation pass, so there is no new MP4, Modal call ID, or end-to-end timing to report. The approved request is conditional on a clean synthetic Parent story whose exact revision has been confirmed. The previously recorded Rev40 story was still a draft and was not eligible.
2. No authenticated emulator walkthrough was performed after adding this candidate screen. The mobile contract tests pass, but the complete UI → API → database → Modal → private preview path remains unverified.
3. No database migration was run. Runtime enablement requires the migration and local/test settings/credentials prepared by the owner in the root environment.
4. The current manifest represents the main subject entity; it does not yet map arbitrary story-mentioned props into the worker visual plan. A story that explicitly requires an extra object (for example, a leaf) can therefore produce a technically valid candidate that omits that object. Do not treat technical validation as proof of story fidelity.
5. Candidate safety/visual-consistency validation is intentionally `NOT_RUN`; the result is not product-playable.

No Modal app was deployed or stopped, no GPU request was made, no shared database was changed, and no commit/push was made.
