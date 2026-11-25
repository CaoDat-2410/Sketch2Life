# Plan Rev12 — repair Parent create-run subject idempotency wiring

**Status:** Approved under Addendum 10's direct authorization to repair blockers and complete two real Android Parent E2E runs.

## Observed failure

During the first fresh Android run (topic: transport; intended drawing subject: bicycle), the UI's `POST /v1/story-runs` returned HTTP 500 before a StoryRun was created or any Modal inference was dispatched. Sanitized API logs identify `TypeError: SqlParentStoryRunRepository.replay_create_run() got an unexpected keyword argument 'intended_drawing_subject'`. The application service and port already pass this normalized value; source review also found the fresh `create_run()` persistence signature missing it.

## Scope

1. Inspect the repository protocol, service, create/replay methods, and idempotency receipt fingerprint call sites.
2. Add the normalized intended drawing subject to both persistence method signatures and to the create-run fingerprint for fresh create and replay. Keep replay equivalence deterministic and ensure different intended subjects do not reuse the same idempotency receipt.
3. Persist a supplied subject in the existing application-owned context snapshot and include it in the existing snapshot hash; omit the optional key when no subject was supplied so old fingerprints/snapshots retain their exact shape. No schema migration is required.
4. Add focused regression coverage for fresh create/replay argument handling and fingerprint distinction, without mocking the real Android/Modal E2E.
5. Run focused backend tests, then rebuild only the FEAT-085 API container with the existing Compose project and `--no-deps`. Preserve database, Redis, MinIO, ClamAV, volumes, and unrelated containers.
6. Use authenticated API reads and sanitized logs to verify that the failed UI attempt created no run, upload session, job, or Modal call. Continue from Android with exactly one create request after the fix.
7. Record the failure, code repair, test output, and per-stage runtime evidence in this feature's evidence folder; keep both E2E runs and their drawings/scripts/videos separate.

## Acceptance

- The repository adapter accepts `intended_drawing_subject` on both create and replay paths and stores a supplied subject in the existing context snapshot.
- Idempotency fingerprints include the normalized intended subject consistently; a changed subject conflicts instead of replaying the wrong run.
- Focused tests pass, API health and route checks pass, and the failed HTTP 500 is confirmed to have dispatched no AI work.
- The Parent UI creates the first fresh run once and continues through authenticated upload, Modal drawing analysis, activity selection, reviewed story, normal video admission/generation, and playback.
- No fixture, direct DB mutation, synthetic gate bypass, duplicate accepted inference, credential exposure, worktree, commit, or push.
