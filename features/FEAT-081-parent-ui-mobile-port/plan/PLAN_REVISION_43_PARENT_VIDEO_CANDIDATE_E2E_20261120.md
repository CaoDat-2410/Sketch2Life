# FEAT-081 — Plan Revision 43: real Parent → Modal video candidate E2E

**Status:** APPROVED by the owner's direct instruction on 2026-11-20: “chạy thử đi, end to end, ko cần quota”.  
**Feature/worktree:** FEAT-081, `feature/fe-mobile-remediation`, `<local-machine-path>  
**Product authority:** FEAT-063 canonical working SRS v2.7-draft / local Rev67. The SRS remains unsigned.

## 1. Goal

Run the real Parent Expo application on `emulator-5554` through the currently implemented local synthetic flow and request one silent LTX-2.5 technical candidate from the already deployed Modal app. Verify the actual UI → task API → task-local Postgres/object storage → Modal → persisted candidate → authenticated preview path. Do not substitute fixtures or mocked provider responses.

The no-quota allowance is limited to the existing local/test, explicit-flag, `modal_dev`, synthetic-profile candidate lane from Plan Revision 42. It does not disable product billing/admission or safety gates and cannot be enabled in staging/production. A returned technical candidate remains `safety_validation=NOT_RUN`, `product_playable=false`, and is not product `VIDEO_READY`.

## 2. Preflight observed on 2026-11-20

- Android device `emulator-5554` is online; package `com.sketch2life.parentexpo.dev` is at Parent sign-in.
- Task API `127.0.0.1:58100` is healthy but its currently served OpenAPI has no video-generation routes; it must be refreshed from this worktree before UI verification.
- Task Compose project is `s2l-feat081-rev23`; its Postgres is a local container with one current consumer. Its named persistent volume originated in the earlier FEAT-081 Rev20 test project. Do not delete/replace it. Before migration, verify the target is still this local task database and inspect the migration plan; apply only necessary additive revisions, never destructive or unrelated migrations.
- Modal `dev` lists `sketch2life-srs23-dev-video` as deployed with zero tasks. Reuse its `generate-silent-story-video` function; do not deploy, warm, or stop the app.

## 3. Run sequence and gates

### M0 — Runtime refresh

1. Rebuild/recreate only `api` in project `s2l-feat081-rev23`, with the existing Compose files and `--no-deps`; preserve every other container, volume, and environment file.
2. Inspect Alembic current/head state without exposing credentials. Audit pending upgrade scripts. Apply only the additive migrations required by the real Parent flow and video-candidate table, and only to the verified task-local development database. If the database target is ambiguous or a required migration is destructive, stop before migration.
3. Confirm API health and the four Parent video routes from this task API. Confirm Modal credentials are present only as a boolean readiness check; never print values.
4. Reload the installed Parent app from the current Expo source without using the visual-preview harness.

### M1 — Real synthetic Parent path

1. Use a synthetic Parent account in the local/development authentication environment. If the UI requires a new account, create one only in that local test environment; generate a one-off password in memory, never save/log it, and do not create a platform production account.
2. Create/use a synthetic-only child profile; do not enter real child data or fabricate legal consent. The server must accept only the existing `SYNTHETIC_DEV`/`SYNTHETIC_TEST` basis for this lane.
3. In the real Parent UI, choose a theme and suggested drawing subject, use the SVG guide if available, attach a newly generated synthetic drawing (not a prerecorded API response), review/confirm the recognized subject, request/select one activity, request and review the story, then confirm the exact visible story revision/hash as the adult operator before video admission.
4. Preserve existing age, authorization, subject, activity, story schema, safety, ownership, and lineage checks. Do not insert business data directly into the database or call product endpoints from a script to skip the UI.

### M2 — One LTX candidate

1. Submit at most one video request from the real Parent UI after the server confirms the same story revision/hash and all synthetic/local gates pass.
2. Allow the existing worker to run; poll only the persisted candidate status. No warm-up, duplicate submit, auto/manual retry, alternate model, direct worker call, scene retry, or quota-ledger mutation.
3. If successful, open the authenticated private technical preview and record the video metadata, timing, request/call IDs, and visible output. Do not claim story fidelity, safety, or product readiness from technical validation alone.
4. If any AI stage fails, capture sanitized diagnostics and stop that stage; do not resend inference in this allowance. Fix source/runtime defects only when within the approved Rev42 scope, and request a new bounded allowance before another live inference.

### M3 — Evidence and cleanup

- Save only synthetic-run evidence in `evidence/PARENT_VIDEO_CANDIDATE_E2E_REV43_20261120/`: screenshots of relevant Parent workflow/result screens, safe API/worker logs, timestamps, durations, request IDs, Modal call ID, and a result matrix.
- Preserve task and unrelated apps/containers; do not stop Modal or Docker services at the end.
- Update FEAT-081 context/status with pass/fail and blockers. No commit, push, branch operations, real-data capture, `.env`/secret edits, or SRS changes.

## 4. Bounded inference allowance

- One pass through each needed Parent AI stage at most (topic/subject suggestion, drawing understanding, activity suggestion, story generation), and **at most one LTX video candidate request total**. Existing catalog/SVG results may avoid an AI call; do not make calls just to warm/cache models.
- Do not retry a failed inference. If a stage fails, stop downstream work and report its specific failure. The user authorizes skipping quota only for the gated local synthetic candidate path; no billing/quota row is read or mutated.
- If adult review identifies unsuitable, malformed, or visibly incorrect story content, do not confirm it just to reach video.

## 5. Acceptance

- The actual Expo app reaches the story-review state using server-created synthetic data and the real backend/Modal contracts.
- The adult confirms the exact story revision/hash; the server accepts one idempotent candidate request.
- A single existing Modal LTX function call is correlated with backend job status and, if technically valid, a private authenticated preview is playable in the technical-preview screen.
- All failures are recorded with safe code, stage, elapsed time, and correlated IDs. No fixture, unsafe retry, quota mutation/bypass outside the candidate lane, migration to a non-task database, or false product-ready claim occurs.

## 6. Authorized paths

- Runtime actions: only task project `s2l-feat081-rev23`, its already-running task-local services/database, `emulator-5554`, and existing Modal app `sketch2life-srs23-dev-video` in environment `dev`.
- Repository: `backend/**` only for approved runtime fixes/tests; `apps/ui-mobile/**` only for approved runtime fixes; additive `backend/alembic/versions/**` only if strictly required; `features/FEAT-081-parent-ui-mobile-port/{CONTEXT.md,approvals/TASK_APPROVAL.md,status/STATUS.md,plan/**,evidence/**}`.
- No modifications to `.env`, credentials, Modal secrets, Firebase service-account files, SRS, generated production data, or other Compose projects.

## 7. Owner clarification — use the single project-root `.env`

The owner pointed out that the configured `.env` is at `<local-machine-path> Inspection checked only the presence/non-empty status of required keys; no values were printed. The task Compose project is rooted at `.codex-worktrees/fe`, where no `.env` file exists. The earlier Compose invocation therefore used Compose defaults instead of the project's root configuration.

This clarification authorizes passing the root file explicitly as `docker compose --env-file <local-machine-path> when recreating only the task API. Compose may consume the values as runtime configuration, but tools/logs must never print them. Do not copy the file, move it, edit it, mount it into the repository, or create another env file. Keep the existing explicit local/test synthetic overrides for provider and candidate gates. After refresh, report only booleans for Firebase/Admin/Modal credential presence and the safe provider/feature-flag names/values.
