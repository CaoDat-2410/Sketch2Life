# Plan Rev33 — non-AI API workflow tests and local database migration

- Feature: FEAT-063 — whole-repository architecture redesign.
- Status: APPROVED for the exact local verification scope below by the project owner's direct request on 2026-10-29.
- Scope authority: the owner requested API tests for the implemented workflows, execution of the database migration, and exclusion of AI-related APIs.
- Prerequisite: Rev30 local Docker/MinIO storage foundation and Rev31 Lesson Library APIs are present on `dev`.

## Goal

Verify the local Docker/MinIO storage example and the non-AI Lesson Library HTTP workflows against PostgreSQL, then apply the additive Alembic migration to the confirmed local application database. Record results and any defects in feature-local evidence.

## Scope

1. Inspect the effective database target without printing credentials. Confirm the migration target is the local Compose PostgreSQL service and record the database/schema revision before applying changes. If configuration resolves outside the local Compose network, stop before migration.
2. Preserve the existing local application database and its data. Apply only the approved Lesson Library target with `alembic upgrade 20261028_ll_0001`, allowing Alembic to apply its declared BE1 prerequisite `20261024_0005`; do not apply unrelated independent AI/media heads, and do not drop, truncate, or recreate the persistent application database.
3. Create a separate disposable PostgreSQL database whose name contains `be1_acceptance` for integration tests. Apply the same Lesson Library target and its prerequisite there. Drop only this test database after the run if it was created by this task.
4. Add and run HTTP integration tests for the non-AI workflows using synthetic identities and content:
   - local storage example: upload, read-back byte equality, and delete from MinIO;
   - Teacher: create/list/read/update/version/archive lessons and enforce revision/idempotency rules;
   - lesson-source upload: create/resume/abort or complete a bounded upload, scan and deterministically parse a synthetic document, and reject invalid inputs;
   - Manager: review and publish a Teacher lesson, including denial for an unauthorized or self-approving Manager;
   - sharing and Parent access: invitation/group membership, acceptance, read/export, revocation, and access denial after revocation;
   - Platform Admin: moderate/hide a lesson with synthetic platform-admin identity and verify Parent discovery is removed.
5. Use the real local PostgreSQL and MinIO adapters. Override only the external identity verification boundary with test-only synthetic verified principals. Use ClamAV where its local service is healthy; if unavailable, report the upload-scanner workflow as blocked rather than silently treating a fake scan as production verification.
6. Keep all test data synthetic and isolated. Remove created MinIO objects through the API or test cleanup. Do not inspect, modify, or export child data.
7. Update FEAT-063 context/status and record reproducible commands, database revision, test results, environment boundaries, and limitations under `evidence/`.

## Acceptance criteria

- AC1: The migration target is demonstrably local; pre-migration and post-migration Alembic revisions are recorded without exposing credentials.
- AC2: `alembic upgrade 20261028_ll_0001` succeeds on the existing local application database and on the isolated acceptance database, applying only the target and its declared prerequisite. The existing application database is not reset or cleaned.
- AC3: HTTP tests exercise the storage and Lesson Library workflow transitions listed above with real SQL persistence and private MinIO storage.
- AC4: Authentication tests substitute only Firebase token verification; tenant/role authorization, route handlers, service logic, database transactions, upload parser and storage adapter remain under test.
- AC5: Negative cases verify stale revisions, invalid uploads, cross-organization access, unauthorized approval, revoked grants, and hidden lessons are denied safely.
- AC6: No AI generation, AI suggestion, line-sketch, Whisper/ASR, vision, video, model provider, or GPU endpoint is called or tested.
- AC7: All test inputs are synthetic, no child data is read or created, no actual `.env` is edited, and no external AWS/Firebase service is accessed.
- AC8: Evidence states each pass, failure, skip, and unverified boundary accurately.

## Execution sequence

1. Record this plan hash and the owner's direct authorization in `approvals/TASK_APPROVAL.md`.
2. Inspect Compose service/container state, local database target, existing schema/revisions, and available test dependencies without printing secret values.
3. Start only the required local Compose services; retain named volumes.
4. Apply the `20261028_ll_0001` target and its declared prerequisite to the confirmed local application database.
5. Create/migrate the isolated acceptance database and add/run the focused HTTP workflow tests.
6. Review failures, fix defects within this approved non-AI scope, and rerun the focused tests.
7. Clean up only resources created by this test run, write evidence, and update FEAT-063 context/status.

## Risks and controls

- The existing Postgres volume predates this plan and may contain useful local data. Never remove the volume or recreate the application database; inspect schema/revision first and use additive migrations only.
- Tests must not use the normal application database for fixtures. The integration fixture must enforce the `be1_acceptance` database-name guard.
- Parent/Teacher/Admin identities are synthetic; this run does not verify Firebase token issuance or external Firebase project configuration.
- A passing local test does not establish production readiness, AWS compatibility, or provider/AI behavior.
- Existing Rev31 plan exclusions on tests and database migration are superseded only for this exact local verification request; no live/remote database access is authorized.

## Explicitly excluded

AI or model APIs, AI suggestions, line-sketch generation, ASR/Whisper, image understanding, video generation, Modal/provider/GPU calls, real Firebase verification, AWS, remote/production databases, real child data, frontend tests, deployments, billing/quota provider flows, database reset/drop on the application database, Git commit, and Git push.
