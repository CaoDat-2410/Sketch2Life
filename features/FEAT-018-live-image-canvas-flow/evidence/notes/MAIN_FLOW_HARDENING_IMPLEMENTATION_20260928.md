# FEAT-018 main-flow hardening — 2026-09-28

## Scope and provenance

- Plan: `features/FEAT-018-live-image-canvas-flow/plan/MAIN_FLOW_HARDENING_PLAN_20260928.md`.
- Approved plan SHA-256: `C15ED48934AB83D30908E69F1BB15E654AE430748885F8174422E93FAA1EA868`.
- Approval: project owner request to identify and fix potential main-flow issues, recorded in
  `approvals/TASK_APPROVAL.md`.
- Worktree base: `codex/feat-018-pixi-exploration`, commit `b24366e`; changes are not committed.
- Verification recorded: 2026-09-28 16:07 +07:00 (Asia/Ho_Chi_Minh); reviewer: Codex.
- Inputs: source inspection, deterministic synthetic contract tests and a mocked network timeout.
  No source image, real child data, provider credential or live AI call was used.

## Changes

- Added a synchronous single-flight guard around session mutations and image picker/upload handoff;
  narration validation now occurs before taking the request lock.
- Kept the same session ID/idempotency key for an identical command retried after an ambiguous
  transport/server outcome. A definitive response or changed command gets a new identity; backend
  contracts remain unchanged.
- Reset session-bound media, topic/correction/re-query, activity/checklist, renderer and feedback
  state only after session creation succeeds.
- Consolidated recording timekeeping, made start/stop/cancel transitions single-flight, capped
  duration at three minutes and cleared timers/recorders on failure or cancellation.
- Rejected unknown/conflicting image metadata before upload; only PNG/JPEG are accepted.
- Mapped displayed feedback observations to the five exact `FeedbackV1` enum values. Removed the
  unsupported free-text note field from the save flow and stated that free-text notes are not stored.
- Added prerequisite notices for direct dashboard entry into the activity and feedback gates.
- Prevented Pixi preparation from looping after a failure; added a deliberate retry control and
  changed the global modal's dismiss button to say “Đóng”.

## Verification

Results below were collected in the local Windows worktree on 2026-09-28:

- Mobile regression tests: `pnpm --filter @sketch2life/art-renderer exec vitest run --root ../../ apps/ui-mobile/tests` — 20 passed, including mocked lost-response retries.
- Mobile TypeScript: `pnpm --filter @sketch2life/art-renderer exec tsc --noEmit -p ../../apps/ui-mobile/tsconfig.json` — passed.
- UI copy/recovery: `pnpm --filter sketch2life-mobile test` — passed.
- Renderer suite: `pnpm --filter @sketch2life/art-renderer test` — 32 passed.
- Renderer production demo bundle: `pnpm --filter @sketch2life/art-renderer build:demo` — passed.
- Backend contract confirmation: `python -m pytest backend/tests/contract/test_mobile_workflow_contracts.py -q` — 10 passed; pytest emitted only a local cache-write permission warning.
- Android JS bundle: `pnpm --filter sketch2life-mobile exec expo export --platform android` — passed after the final app-code edit; Metro bundled `apps/ui-mobile/index.ts` (851 modules) and emitted `index-05606329964def9c6dcf75211a8a4d39.hbc` (3.04 MB).
- `git diff --check` — passed after implementation and evidence updates.

## Limits and remaining acceptance

- `adb` is unavailable in this environment, so emulator install/boot and full device journey were not
  verified. The successful Expo export verifies Metro bundling only, not native runtime behavior;
  owner device acceptance remains pending.
- No live Lightning/Qwen/SAM request was made. The owner-run synthetic-image acceptance boundary
  remains pending.
- Free-text parent notes remain intentionally unsupported by the current `FeedbackV1` contract.
- No repository security validator was run because this task did not commit or push changes.
