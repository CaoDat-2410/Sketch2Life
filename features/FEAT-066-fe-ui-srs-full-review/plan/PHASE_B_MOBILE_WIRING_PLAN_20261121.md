# FEAT-066 goal v3 Phase B - Android Parent wiring plan (2026-11-21)

Status: PLAN, implemented in the same change. Scope owner: Person 2 (task owner). Branch `claude/v3-phase-b-mobile-wiring-f8044d`, cut from `feature/fe-mobile-remediation` at `b1f83ff7` (Phase A wiring). Records (TASK_APPROVAL.md, DECISIONS.md) are not changed here.

Authority: SRS `SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md` (SHA-256 prefix `443A3CA3`, Vietnamese primary copy, canonical working copy per `docs/context/SRS_AUTHORITY.md`; lines cited as `l.N`). Backend contract: `feature/backend-srs-api-v3` range `bb73e958..00d5ee60` (read-only), the evidence notes `V3_<task>_EVIDENCE_*.md` and the Phase B report (item 7, FE hand-offs).

## 1. Starting point

- The nine-file minimum Android fix of integration commit `2a8a7ef1` is brought in first (`readSubjectConfirmationOutcome`, `INPUT_REVIEW` labels, terminal `ABANDONED`/`DELETED`, test `parentPhaseBContract.test.ts`); one conflict in `ParentApi.ts` (Phase A key helper) is resolved to the visible-ASCII 1-128 rule.
- Android still calls the synchronous legacy drawing route and has no code for ideas, transcripts, rewrites, video, playback or closeout states.

## 2. Wiring (scope of this change)

| # | Backend task | SRS | Android change |
|---|---|---|---|
| 1 | T-2b drawing attach | l.1664, l.983 | Upload the compressed photo through `/v1/upload-sessions` (`RUN_ARTWORK`, Phase A adapter), then `POST /v1/story-runs/{id}/assets` (202, no job ref); wait on `GET /v1/story-runs/{id}` until the VLM answer (`SUBJECT_REVIEW`) or `INPUT_REVIEW` with a failed job (one retake). The legacy `drawing-understandings` call is no longer used by the screen. |
| 2 | T-2c idea, transcript | l.1665, l.512, BR-23 | `RUN_AUDIO` upload, `POST /idea` (audio ref; text and correction are supported by the port), poll `GET /transcript` (PENDING to NEEDS_CONFIRMATION or FAILED), new transcript step: confirm one exact revision and hash (`/transcript-confirmation`) or send a correction; voice-only and typed-only flows. |
| 3 | T-2d subject 202 | l.1666, l.394, l.1413 | `RERUN_REQUESTED` no longer ends in a message: the controller waits (2-10 s) until the new understanding revision is in `SUBJECT_REVIEW`, adopts it and asks for the second confirmation; a failed rerun returns to the unchanged revision with a safe message. |
| 4 | T-2d, T-2d-fix rewrites | l.1668, FR-P-07, l.378 | `POST /story-rewrites` (202, revision 1..4, optional hash and hint), wait for `SCRIPT_REVIEW`; cap of three rewrites (409 `STORY_REWRITE_LIMIT_REACHED` means confirm or cancel); failed rewrite = `SCRIPT_REVIEW` + `job_state FAILED`, previous story intact, retry only when `retryable`. |
| 5 | T-1a, T-1b video | l.395, l.1670-1672 | New `video` step: request (`expected_revision`, `story_sha256`, reason on regeneration), `ADMISSION_PENDING` and in-flight states from the run detail, `VIDEO_UNSUITABLE` with a safe reason, `complete`, 409 codes (`VIDEO_QUOTA_EXCEEDED`, `SUBSCRIPTION_RESTRICTED`, `VIDEO_REGENERATION_LIMIT_REACHED`), 503 (`AI_COST_LIMIT_REACHED`, `PROVIDER_UNAVAILABLE`). After "unsuitable" the way back is rewrite, confirm script, request again. |
| 6 | T-1c playback, detail | l.1676, l.1691-1693, l.1811 | `POST /playback-token`, bearer plus `X-Playback-Token` header stream (never a URL token), 401 on the stream means one re-issue; run detail aggregate fields (`video`, `quota`, `timeline`) typed; no token in logs or errors. |
| 7 | T-1d1 closeout | l.383, l.1372 | `ABANDONED`, `COMPLETED` by idle, `FAILED`, deadline outcome back to `SCRIPT_REVIEW` with a failed generation (`VIDEO_DEADLINE_EXCEEDED`), `VIDEO_TECHNICAL_FAILURE`, `VIDEO_SAFETY_BLOCKED`: calm Vietnamese states, no replay after completion (T-1c-DEC-4). |
| 8 | T0.9 and keys | l.864-865, l.1639 | Idempotency-Key 1-128 visible ASCII on every `/v1/story-runs` command (was 256/200); 404 for a wrong role maps to the uniform not-found message and never to "forbidden". |

## 3. Design

- Dependencies point inward: pure readers and state classifiers in `application/` (`parentPhaseB.ts`, `parentRunUploads.ts`, `parentRunWait.ts`), HTTP in `infrastructure/http/ParentApi.ts`, device bytes and SHA-256 in a thin `infrastructure/device/` adapter (expo-file-system, expo-crypto) behind ports, screens only read view models.
- The run detail (`GET /v1/story-runs/{id}`) is the single source of truth for every wait; the job route is not used for story jobs because the backend omits the job reference from 202 bodies (Q-J) and returns it only for video, where the run detail already carries the job summary.
- Waits use the Phase A bounds (2 s to 10 s), pause while the app is in the background and stop on unmount; a second tap never sends a second command (retained action identity per signature).
- Out of scope: backend, `apps/web`, `apps/mobile`, real Firebase sign-in, any server, quota purchase, the first-story trigger (still blocked by the missing activity-selection API, recorded as an open question).

## 4. Checks

`apps/ui-mobile`: `npm test` (must print `UI_COPY_AND_RECOVERY_VALID`), `npm run typecheck`. Worktree root: `python tools/validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, `git diff --check`. One independent review (Sonnet 5.5, high), one round, P1/P2 fixed and re-checked once. No API, database, Docker or Firebase.

## 5. Commit and branch rule

One commit `feat(FEAT-066): goal v3 Phase B Android Parent wiring`; then `git merge --ff-only` of `feature/fe-mobile-remediation` in `.worktrees/mobile` only if that worktree is clean and still at `b1f83ff7`. No push.
