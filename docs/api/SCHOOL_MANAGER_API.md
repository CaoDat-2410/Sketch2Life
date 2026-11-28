# School Manager API Reference

- **Integration tree:** `feature/backend-srs-api-and-fe-integration` (`297f2849f9db26bb142123da5e1673dcd58673ae`)
- **Date:** `2026-11-25`
- **Generator note:** Generated from code by agy and checked by Claude
- **Route counts by Status:**
  - `MERGED`: 63 (43 documented in detail + 20 `owner: Billing/Capacity`)
  - `pending merge (Phase D, planned)`: 6 (plus planned `T-6a`/`T-6b` extensions noted on existing `MERGED` routes)
  - **Total:** 69
- **Phase D and E additions:** `6` rows `PENDING-MERGE` (sources: working trees of the Phase D and E branches on 2026-11-25)

## How to read this file

- **Authentication & Role Scope:** All `/api/be1/v1/...`, `/api/lesson-library/v1/...`, `/v1/notifications`, `/v1/jobs/{job_id}`, and `/api/auth/v1/me` endpoints require a verified bearer token (`Authorization: Bearer <token>` resolved via `get_verified_adult`), EXCEPT `POST /api/auth/v1/password-recovery` (public) and `GET /api/be1/v1/health` (public). For School Manager (`school_manager` account role), BE1 organization routes require an active `school_admin` assignment row on `organization_id` (`require_assignment`, `be1_common.py`).
- **Error Envelope (CONV-1):** All route families documented in this file belong to `is_conv1_path` (`error_envelope.py`), returning the CONV-1 error body `Be1Error` (`code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds`, `field_errors`, `request_id`, plus `current_version` on `409 STALE_REVISION`; `be1_runtime.py`). Legacy HTTPException `422` with `INVALID_REQUEST` / `IDEMPOTENCY_KEY_REQUIRED` is normalized to `400 INVALID_REQUEST`; `*_NOT_FOUND` becomes `404 RESOURCE_NOT_FOUND`; `FORBIDDEN` becomes `403 ACTION_NOT_ALLOWED`.
- **Optimistic Concurrency & Idempotency:** Commands marked `Idempotency-Key required` accept a 1-128 character header (`parse_idempotency_key` checks visible ASCII) and fail with `400 INVALID_REQUEST` if missing/malformed or `409 INVALID_IDEMPOTENCY_KEY` on payload mismatch. Commands marked `If-Match required` expect strong-quoted integer ETags (`"<revision>"`) unless otherwise noted.
- **Privacy Boundaries:** School Managers receive **counts only** on class rosters (`Be1ClassRosterSummaryV1`), redacted consent lists (`Be1ConsentListManagerV1`), and opaque membership metadata on Parent groups (`ParentGroupMemberSummaryV1`). Child profile CRUD, revision histories, support-needs endpoints (`be1_registry.py`), classroom session rosters (`/roster`), pilot profiles (`/pilot-profiles`), and child portfolios (`/portfolio`) return `403 ACTION_NOT_ALLOWED` for School Manager and belong to `TEACHER_API.md`.
- **Phase Statuses:**
  - `MERGED`: present on integration commit `297f2849f9db26bb142123da5e1673dcd58673ae`.
  - `pending merge (Phase D, planned)`: planned in `API_INVENTORY_V4_20261125.md` (`T-6a`/`T-6b`/`T-6c`), not yet built in code.

## Table of Contents

1. [Auth, Scope Resolution & Service Health](#1-auth-scope-resolution--service-health)
2. [Organizations & Teacher Assignments](#2-organizations--teacher-assignments)
3. [Classes & Class Lifecycle](#3-classes--class-lifecycle)
4. [Class Profiles Summary & Consents](#4-class-profiles-summary--consents)
5. [Data Lifecycle Requests & Manager-Visible Reads](#5-data-lifecycle-requests--manager-visible-reads)
6. [Lesson Library Review, Staff Management & Sharing](#6-lesson-library-review-staff-management--sharing)
7. [Parent Groups](#7-parent-groups)
8. [Lesson Feedback](#8-lesson-feedback)
9. [Notifications](#9-notifications)
10. [Billing / Video Quota (External Owner)](#10-billing--video-quota-external-owner)
11. [Phase D Planned Routes (`T-6a`, `T-6b`, `T-6c`)](#11-phase-d-planned-routes-t-6a-t-6b-t-6c)

---

## 1. Auth, Scope Resolution & Service Health

Routes in `routers/auth_registration.py`, `routers/password_recovery.py`, and `routers/be1_runtime.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/auth/v1/me` | Resolve signed-in adult role/scope; activates `pending_verification` accounts and `pending_activation` `school_admin` assignments when `email_verified` is true | Header `Authorization: Bearer <token>` | `200` `CurrentAccountResponse` (`role`, `state`, `role_revision`, `scope`: `GrantedScopeResponse`; `auth_registration.py`); `Cache-Control: private, no-store` | `401 AUTH_REQUIRED`, `403 ACCOUNT_SETUP_UNAVAILABLE`, `403 EMAIL_VERIFICATION_REQUIRED`, `503 PROVIDER_UNAVAILABLE` | none | `FR-C-01`, `FR-O-09`, `UC-13` | `MERGED` |
| POST | `/api/auth/v1/password-recovery` | Public generic password recovery trigger writing a `password_recovery` outbox row for active/pending accounts | `PasswordRecoveryInput` (`email`; `platform_admin.py`); no auth header | `202` `{"status": "RECOVERY_REQUESTED"}` (`password_recovery.py`) | `400 INVALID_REQUEST`, `429 RATE_LIMITED` | none (rate-limited per client IP) | `UC-13`, `FR-O-09` | `MERGED` |
| GET | `/api/be1/v1/health` | BE1 runtime health check | none | `200` `{status, database, api}` (`be1_runtime.py`) | `503` (if DB unhealthy) | none | `UNVERIFIED: SRS id` | `MERGED` |

> **Note (`T-6a` planned reuse/change):** `API_INVENTORY_V4_20261125.md` marks `GET /api/auth/v1/me` as `REUSE` and `POST /api/auth/v1/password-recovery` as a small `CHANGED` extension in Phase D (adding a metadata audit row per `UC-13`); currently in `password_recovery.py` only `EmailDeliveryModel` is written.

---

## 2. Organizations & Teacher Assignments

Routes in `routers/be1_registry.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/be1/v1/organizations/{organization_id}` | Read organization summary for an assigned adult | Path `organization_id`; Bearer token | `200` `Be1OrganizationV1` (`contract`, `organization_id`, `display_name`; `be1_registry.py`) | `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND` | none | `FR-PL-01`, `FR-PL-02` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/me` | List caller's active assignments in the organization | Path `organization_id`; Bearer token | `200` `Be1AdultAssignmentsV1` (`contract`, `subject`, `organization_id`, `assignments[{role, class_id}]`; `be1_registry.py`) | `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND` | none | `FR-C-01` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/teacher-candidates` | List active Teacher candidates in the org eligible for class assignment (`school_admin` only) | Path `organization_id`; Query `limit` (1..100, default `25`), `cursor` | `200` `Be1TeacherCandidatePageV1` (`contract`, `items[{candidate_ref, display_name}]`, `next_cursor`; `be1_registry.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `503 IDENTITY_PROVIDER_UNAVAILABLE` | none | `FR-T-02`, `BR-05` | `MERGED` |
| POST | `/api/be1/v1/classes/{class_id}/assignments` | Assign the first active Teacher to an unassigned class (`school_admin` only) | Headers `Idempotency-Key`, `If-Match: "<assignment_revision>"`; `CreateAssignmentRequest` (`candidate_ref`; `be1_runtime.py`) | `200` `Be1AdultAssignmentV1` (`contract`, `assignment_id`, `candidate_ref`, `role`, `class_id`, `active`, `assignment_revision`; `be1_registry.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 CLASS_TEACHER_EXISTS`, `409 INVALID_STATE_TRANSITION`, `409 RESOURCE_CONFLICT` | `Idempotency-Key required`; `If-Match required` | `FR-T-02`, `BR-05`, `§21.2` | `MERGED` |

> **Note (`T-6b` planned change):** `API_INVENTORY_V4_20261125.md` (row 55) marks `POST /api/be1/v1/classes/{class_id}/assignments` as `CHANGED` in Phase D (`pending merge (Phase D, planned)` for the transfer path) to return `202 Be1TeacherAssignmentTransferAcceptedV1` when the class already has an active Teacher (`T-6b`). On integration (`be1_registry.py:379`), an occupied class currently returns `409 CLASS_TEACHER_EXISTS`.

---

## 3. Classes & Class Lifecycle

Routes in `routers/be1_registry.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/be1/v1/organizations/{organization_id}/classes` | List classes in organization (Manager sees `active`, `suspended`, `archived`, or `all`; default `active`) | Path `organization_id`; Query `state` (`active, suspended, archived, all`), `limit` (1..100, default `25`), `cursor` | `200` `Be1ClassListV1` (`contract`, `items[{class_id, display_name, state, class_revision, assignment_revision, has_active_teacher}]`, `next_cursor`; `be1_registry.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND` | none | `FR-T-02`, `FR-B-07` | `MERGED` |
| POST | `/api/be1/v1/organizations/{organization_id}/classes` | Create a new class in `active` state (`school_admin` only; checks effective organization class capacity under subscription/org lock and settles due downgrade suspensions) | Header `Idempotency-Key`; `CreateClassRequest` (`display_name`; `be1_runtime.py`) | `201` `Be1ClassV1` (`contract`, `class_id`, `display_name`, `state`, `assignment_revision`; `be1_registry.py`) | `400 INVALID_REQUEST`, `400 INVALID_IDEMPOTENCY_KEY`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 CLASS_CAPACITY_REACHED`, `409 RESOURCE_CONFLICT`, `503 PROVIDER_UNAVAILABLE` | `Idempotency-Key required` | `FR-T-02`, `§21.2` | `MERGED` |
| POST | `/api/be1/v1/classes/{class_id}/suspend` | Suspend an `active` class (`school_admin` only) | Headers `Idempotency-Key`, `If-Match: "<class_revision>"`; empty body | `200` `Be1ClassStateV1` (`contract`, `class_id`, `state: "suspended"`, `class_revision`; `be1_registry.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 INVALID_STATE_TRANSITION`, `409 RESOURCE_CONFLICT` | `Idempotency-Key required`; `If-Match required` | `FR-B-07`, `BR-32`, `§21.2` | `MERGED` |
| POST | `/api/be1/v1/classes/{class_id}/archive` | Archive an `active` or `suspended` class terminally (`school_admin` only) | Headers `Idempotency-Key`, `If-Match: "<class_revision>"`; empty body | `200` `Be1ClassStateV1` (`contract`, `class_id`, `state: "archived"`, `class_revision`; `be1_registry.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 INVALID_STATE_TRANSITION`, `409 RESOURCE_CONFLICT` | `Idempotency-Key required`; `If-Match required` | `FR-B-07`, `BR-32`, `§21.2` | `MERGED` |

---

## 4. Class Profiles Summary & Consents

Routes in `routers/be1_registry.py`. School Managers never see child names, IDs, or support-needs values in these responses.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/profiles` | Read active child count summary for Manager (readable across `active`, `suspended`, `archived`; Teacher gets `Be1ManagedProfileListV1`) | Path `organization_id`, `class_id`; Query `limit`, `cursor` (validated on query, ignored for `school_admin`) | `200` `Be1ClassRosterSummaryV1` (`contract`, `class_id`, `active_profile_count`; `be1_registry.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND` (OpenAPI `BE1_ERROR_RESPONSES` still lists `409`, though `T-7e` removed `409 CONSENT_NOT_EFFECTIVE` from this handler) | none | `FR-B-04`, `BR-21` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | List class consent statuses without child IDs or purpose refs (`school_admin` view) | Path `organization_id`, `class_id`; Query `limit` (1..100, default `25`), `cursor` | `200` `Be1ConsentListManagerV1` (`contract`, `items[{consent_id, state, effective}]`, `next_cursor`; `be1_registry.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-C-06`, `BR-11` | `MERGED` |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents` | Record class consent (`school_admin` or assigned `teacher`; class must be `active`) | Path `organization_id`, `class_id`; `RecordConsentRequest` (`class_id`, `child_id`, `purpose_ref`, `evidence_ref`; `be1_runtime.py`) | `201` `Be1ConsentV1` (`contract`, `consent_id`, `state`, `effective`; `be1_registry.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_STATE_TRANSITION`, `422 CLASS_SCOPE_MISMATCH` | none | `FR-C-06`, `BR-11` | `MERGED` |
| POST | `/api/be1/v1/organizations/{organization_id}/classes/{class_id}/consents/{consent_id}/revoke` | Revoke an existing consent record (`school_admin` or assigned `teacher`) | Path `organization_id`, `class_id`, `consent_id`; empty body | `200` `Be1ConsentV1` (`contract`, `consent_id`, `state: "revoked"`, `effective: false`; `be1_registry.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_STATE_TRANSITION` | none | `FR-C-06`, `BR-11` | `MERGED` |

---

## 5. Data Lifecycle Requests & Manager-Visible Reads

Organization data lifecycle requests are Manager-only (`routers/be1_records.py`). The remaining read routes in this section come from `routers/be1_sessions.py`, `routers/be1_canvas.py`, `routers/be1_artifacts.py`, `routers/be1_records.py`, `routers/pilot_assistance.py`, and `routers/jobs.py` where `school_admin` is authorized alongside class Teachers.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/be1/v1/organizations/{organization_id}/data-requests` | Create an organization data lifecycle export/purge request (`school_admin` only) | Path `organization_id`; `DataRequestCreate` (`request_type`, `target_ref`; `be1_runtime.py`) | `202` `Be1DataRequestV1` (`contract`, `request_id`, `state: "requested"`, `completion_claimed: false`; `be1_records.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-C-10` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/data-requests/{request_id}` | Poll an organization data lifecycle request status (`school_admin` only) | Path `organization_id`, `request_id` | `200` `Be1DataRequestV1` (`contract`, `request_id`, `request_type`, `target_ref`, `state`, `unresolved_items`, `completion_claimed`; `be1_records.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-C-10` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}` | Read session metadata (`require_assignment`; Manager and assigned class staff) | Path `organization_id`, `session_id` | `200` `session_response(record)` (`be1_sessions.py`) | `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND` | none | `FR-T-03` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/learning-stage` | Read shared session learning stage (`roles={"school_admin", "teacher"}`) | Path `organization_id`, `session_id` | `200` `Be1SharedLearningStageV1` (`contract`, `session_id`, `stage`, `stage_revision`, `lifecycle_state`, `entered_at`, `last_command_id`; `be1_sessions.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 LEARNING_STAGE_UNAVAILABLE` | none | `FR-T-04`, `§31.6` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/outcome` | Read recorded session outcome (`roles={"school_admin", "teacher"}`) | Path `organization_id`, `session_id` | `200` `Be1SessionOutcomeReadV1` (`contract`, `session_id`, `lifecycle_state`, `outcome: {value, reason_category, teacher_note, outcome_refs, stage_revision, created_at} or null`; `be1_sessions.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-T-05` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/join-requests` | List pending device join grants for a session (`roles={"school_admin", "teacher"}`) | Path `organization_id`, `session_id` | `200` `Be1PendingJoinListV1` (`contract`, `items[{grant_id, requested_at}]`; `be1_sessions.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-T-03`, `FR-CH-01` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/groups/{group_id}/checkpoints/latest` | Read latest group canvas checkpoint if group consent is effective (`roles={"school_admin", "teacher", "guide"}`) | Path `organization_id`, `session_id`, `group_id` | `200` `Be1CanvasCheckpointV1` (`contract`, `checkpoint_id`, `canvas_id`, `document_epoch`, `document_revision`, `checksum_sha256`, `snapshot`; `be1_canvas.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 CONSENT_NOT_EFFECTIVE` | none | `FR-C-06`, `FR-CH-04` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/artifacts/{asset_ref:path}` | Download session artifact bytes in `local`/`test` when contributor consents are effective (`require_assignment`) | Path `organization_id`, `session_id`, `asset_ref`; Query `version` (default `1`) | `200` raw artifact bytes + `ETag: "<sha256>"` + `Cache-Control: private, no-store` (`be1_artifacts.py`) | `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND`, `409 CONSENT_NOT_EFFECTIVE`, `410 ARTIFACT_INTEGRITY_FAILED`, `503 ARTIFACT_PROVIDER_UNCONFIGURED` | none | `FR-C-06`, `FR-C-09` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/gallery` | List published gallery items for a session when contributor consents are effective (`require_assignment`) | Path `organization_id`; Query `session_id` (`be1_records.py`) | `200` `Be1GalleryListV1` (`contract`, `items[{gallery_id, artifact_ref, audience, contributors, caption, annotations, created_at}]`; `be1_records.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND`, `409 CONSENT_NOT_EFFECTIVE` | none | `FR-C-06`, `FR-T-07` | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/sessions/{session_id}/teacher/assistance-requests/pending` | Read pending pilot assistance request metadata for active/paused session (`roles={"school_admin", "teacher"}`) | Path `organization_id`, `session_id` | `200` `TeacherPendingListV1` (`items[{assistance_id, request_revision, session_id, canvas_id, participant_id, requested_level, ...}]`; `pilot_assistance.py`) + `Cache-Control: no-store`, `Vary: Authorization` | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `§31.8` | `MERGED` |
| GET | `/v1/jobs/{job_id}` | Poll status of an AI job inside the signed-in actor's scope | Path `job_id`; optional Header `If-None-Match` | `200` `AiJobStatusV1` (`job_id`, `job_revision`, `state`, `result_refs`, `poll_after_ms`; `jobs.py`) or `304`; `ETag`, `Cache-Control: private, no-cache` | `304`, `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND`, `500 INTERNAL_SERVER_ERROR`, `503 DATABASE_UNAVAILABLE` | none (`If-None-Match` conditional read) | `§21.3`, `§16.75` (`l.1675`) | `MERGED` |

> **Scope note (Teacher-exclusive endpoints & classroom execution writes):**
> - **Explicitly denied (`403 ACTION_NOT_ALLOWED`) for School Manager:** `GET .../sessions/{session_id}/roster` (`roles={"teacher"}` + `require_class_teacher_row`), `GET .../classes/{class_id}/profiles/{child_id}/portfolio` (`require_class_teacher_row`), `GET .../pilot-profiles` (`Teacher`-only), and all child profile writes/revisions/moves/support-needs (`be1_registry.py`).
> - **Classroom execution writes:** Session lifecycle transitions, group creation/assignment/locking/turns, artifact uploads, gallery publish/annotate, and observations in `be1_sessions.py`, `be1_artifacts.py`, `be1_canvas.py`, and `be1_records.py` accept `roles={"school_admin", "teacher"}` at the RBAC layer via `require_assignment` but belong to the Teacher classroom workflow and are documented in `TEACHER_API.md`.

---

## 6. Lesson Library Review, Staff Management & Sharing

Routes in `routers/lesson_library.py` and schemas in `contracts/schemas/lesson_library.py`. All paths under `/api/lesson-library/v1` use the CONV-1 error envelope.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons` | List organization lessons visible to staff (School Manager sees all org lessons, including other Teachers' `PRIVATE` lessons) | Path `organization_id`; Query `state` (`ACTIVE, ARCHIVED`), `visibility` (`PRIVATE, SCHOOL, PUBLIC`), `limit` (1..100, default `25`), `cursor` | `200` `LessonPageV1` (`contract`, `items`: `LessonSummaryV1[]`, `next_cursor`; `schemas/lesson_library.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-T-09`, `FR-PL-05` | `MERGED` |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Read full lesson detail and current version (`_staff`) | Path `organization_id`, `lesson_id` | `200` `LessonDetailV1` (`lesson_id`, `organization_id`, `owner_kind`, `created_by`, `state`, `visibility`, `moderation_state`, `current_version`: `LessonVersionV1`, `revision`; `schemas/lesson_library.py`) + `ETag` | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-T-09`, `FR-PL-05` | `MERGED` |
| DELETE | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}` | Archive an organization lesson (Manager can archive any org lesson) | Headers `Idempotency-Key`, `If-Match: "<revision>"` (missing -> `400 INVALID_REQUEST`) | `200` `LessonDetailV1` (`state: "ARCHIVED"`, incremented `revision`; `schemas/lesson_library.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 INVALID_STATE_TRANSITION` | `Idempotency-Key required`; `If-Match required` | `FR-T-09`, `FR-PL-05` | `MERGED` |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/access-grants` | List lesson access grants and publication review queue (`_manager` only) | Path `organization_id`; Query `audience_kind`, `state`, `lesson_id`, `limit` (1..100, default `25`), `cursor` | `200` `LessonAccessGrantPageV1` (`contract`, `items`: `LessonAccessGrantV1[]`, `next_cursor`; `schemas/lesson_library.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-PL-05`, `BR-51` | `MERGED` |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/access-grants/{access_grant_id}/decision` | Approve or request changes on a `PUBLIC` `PENDING_REVIEW` access grant (`_manager` only; cannot approve own lesson) | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `DecideLessonAccessGrantRequestV1` (`contract`, `decision`: `APPROVE, REQUEST_CHANGES`, `reason` required for `REQUEST_CHANGES`; `schemas/lesson_library.py`) | `200` `LessonAccessGrantDecisionResponseV1` (`access_grant_id`, `state`: `ACTIVE, CHANGES_REQUESTED`, `approved_by`, `decided_at`, `revision`; `schemas/lesson_library.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 INVALID_STATE_TRANSITION` | `Idempotency-Key required`; `If-Match required` | `FR-PL-05`, `BR-51`, `AC-48` | `MERGED` |
| DELETE | `/api/lesson-library/v1/organizations/{organization_id}/lessons/{lesson_id}/access-grants/{access_grant_id}` | Revoke a lesson access grant (`_staff`; Manager can revoke any org grant) | Headers `Idempotency-Key`, `If-Match: "<revision>"` (missing -> `400 INVALID_REQUEST`) | `200` `LessonAccessGrantV1` (`state: "REVOKED"`, `revoked_at`, incremented `revision`; `schemas/lesson_library.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 INVALID_STATE_TRANSITION` | `Idempotency-Key required`; `If-Match required` | `FR-T-09`, `FR-PL-05` | `MERGED` |

---

## 7. Parent Groups

Routes in `routers/lesson_library.py` and schemas in `contracts/schemas/lesson_library.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | Create a parent group inside the organization (`_manager` only) | Header `Idempotency-Key`; `CreateParentGroupRequestV1` (`contract`, `display_name`; `schemas/lesson_library.py`) | `201` `ParentGroupV1` (`parent_group_id`, `organization_id`, `display_name`, `state`: `ACTIVE`, `created_at`; `schemas/lesson_library.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY` | `Idempotency-Key required` | `FR-PL-04`, `§21.2` | `MERGED` |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups` | List organization parent groups (`_manager` only) | Path `organization_id`; Query `limit` (1..100, default `25`), `cursor` | `200` `ParentGroupPageV1` (`contract`, `items`: `ParentGroupV1[]`, `next_cursor`; `schemas/lesson_library.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-PL-04`, `§21.1` | `MERGED` |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/invitations` | Invite a non-staff Parent using its subject or unambiguous account-ID alias (`_manager` only; rejects staff principals; duplicate detection recognizes aliases for one active Parent identity) | Header `Idempotency-Key`; `InviteParentToGroupRequestV1` (`contract`, `parent_principal_ref`; `schemas/lesson_library.py`) | `201` `ParentGroupInvitationV1` (`membership_id`, `parent_group_id`, `organization_id`, `state`: `INVITED`, `invited_at`, `expires_at`, `accepted_at`, `revision`; `schemas/lesson_library.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 INVALID_STATE_TRANSITION`, `409 INVITATION_EXISTS` | `Idempotency-Key required` | `FR-PL-04`, `§21.2` | `MERGED` |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members` | List opaque membership metadata and state counts (`INVITED`, `ACCEPTED`, `DECLINED`, `REVOKED`, `EXPIRED`; no Parent identity/contact/child fields; folds `403`/`404` into `404 RESOURCE_NOT_FOUND`) | Path `organization_id`, `parent_group_id`; Query `state` (`INVITED, ACCEPTED, DECLINED, REVOKED, EXPIRED`), `limit` (1..100, default `25`), `cursor` (max 1024 chars) | `200` `ParentGroupMemberPageV1` (`items`: `ParentGroupMemberSummaryV1[]`, `counts`: `ParentGroupMemberCountsV1 {invited, accepted, declined, revoked, expired, total}`, `next_cursor`; `schemas/lesson_library.py`); `Cache-Control: private, no-store` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `404 RESOURCE_NOT_FOUND` | none | `FR-PL-04`, `§21.1` | `MERGED` |
| DELETE | `/api/lesson-library/v1/organizations/{organization_id}/parent-groups/{parent_group_id}/members/{membership_id}` | Revoke a parent group membership (Manager org revoke or member Parent self-revoke using the active Parent subject/account alias; cross-referenced in [PARENT_API.md](./PARENT_API.md#7-lesson-library-reads-invitations-parent-groups--feedback)) | Headers `Idempotency-Key`, `If-Match: "<revision>"` (missing -> `428 PRECONDITION_REQUIRED`) | `200` `ParentGroupMembershipV1` (`organization_id`, `state: "REVOKED"`, incremented `revision`, `revision_source`; `schemas/lesson_library.py`) + `ETag` | `400 INVALID_REQUEST`, `400 INVALID_IDEMPOTENCY_KEY`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 STALE_REVISION`, `409 INVALID_STATE_TRANSITION`, `428 PRECONDITION_REQUIRED`, `503 PROVIDER_UNAVAILABLE` | `Idempotency-Key required`; `If-Match required` | `FR-PL-04`, `§21.2`, `§21.4` | `MERGED` |

---

## 8. Lesson Feedback

Routes in `routers/lesson_feedback.py` and service logic in `infrastructure/lesson_library/feedback.py`. Uses `platform_admin` helpers (`Key`, `revision`, `run`, `service`), NOT `AdminRoute` (no automatic `ETag` or `Cache-Control: no-store`).

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/lesson-library/v1/organizations/{organization_id}/feedback` | List organization lesson feedback threads (accessible to `school_admin`, `teacher`, `platform_admin`, `parent`) | Path `organization_id`; Query `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{total, limit, next_cursor, items[{thread_id, lesson_id, version_id, revision, created_at}]}` (`lesson_feedback.py`, `feedback.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `422 INVALID_CURSOR` | none | `UNVERIFIED: SRS id` | `MERGED` |
| GET | `/api/lesson-library/v1/organizations/{organization_id}/feedback/{thread_id}` | Read messages in a lesson feedback thread | Path `organization_id`, `thread_id`; Query `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{thread_id, organization_id, lesson_id, version_id, revision, limit, next_cursor, items[{message_id, body, from_you, created_at}]}` (`lesson_feedback.py`, `feedback.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `422 INVALID_CURSOR` | none | `UNVERIFIED: SRS id` | `MERGED` |
| POST | `/api/lesson-library/v1/organizations/{organization_id}/feedback/{thread_id}/replies` | Post a reply to a lesson feedback thread | Headers `Idempotency-Key`, `If-Match: "<revision>"` (missing -> `428`, invalid -> `422`); `FeedbackInput` (`body`; `schemas/platform_admin.py`) | `200` `{thread_id, revision}` (`lesson_feedback.py`, `feedback.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED` | `Idempotency-Key required`; `If-Match required` | `UNVERIFIED: SRS id` | `MERGED` |

---

## 9. Notifications

Routes in `routers/notifications.py` (`T-8a`) and schemas in `contracts/schemas/notifications.py`. Available to any active signed-in adult with a role (including School Manager). Note: `/v1/notifications/push-endpoints*` (`T-8b`) is Parent-only (`authorize_parent`) and belongs to `PARENT_API.md`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/v1/notifications` | Read caller's notification inbox, newest first | Query `limit` (`limit_query()`), `cursor` | `200` `NotificationPageV1` (`items`: `NotificationV1[]`, `next_cursor`, `unread_count` 0..100 where `100` means 100+; `schemas/notifications.py`); `Cache-Control: private, no-cache`, `Vary: Authorization` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACCOUNT_SCOPE_UNAVAILABLE`, `503 PROVIDER_UNAVAILABLE` | none | `FR-B-09`, `§21.1` | `MERGED` |
| POST | `/v1/notifications/read-all` | Mark all unread, unexpired inbox items of caller as read | Header `Idempotency-Key` (1-128 visible ASCII via `parse_idempotency_key`) | `200` `NotificationReadAllV1` (`marked_count`; `schemas/notifications.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACCOUNT_SCOPE_UNAVAILABLE`, `409 INVALID_IDEMPOTENCY_KEY`, `503 PROVIDER_UNAVAILABLE` | `Idempotency-Key required` | `FR-B-09`, `§21.2` | `MERGED` |
| POST | `/v1/notifications/{inbox_item_id}/read` | Mark one inbox item of caller as read | Path `inbox_item_id`; Header `Idempotency-Key` | `200` `NotificationV1` (`inbox_item_id`, `notification_type`, `template_version`, `safe_parameters`, `created_at`, `read_at`, `expires_at`; `schemas/notifications.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACCOUNT_SCOPE_UNAVAILABLE`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `503 PROVIDER_UNAVAILABLE` | `Idempotency-Key required` | `FR-B-09`, `§21.2` | `MERGED` |

---

## 10. Billing / Video Quota (External Owner)

Routes in `routers/be1_billing.py` accept `school_manager` (`scope_for_be1` selects single active org on `/api/be1/v1/billing/video-quota*`; org-scoped routes check `school_admin` assignment), and capacity routes (`T-CAP1`, built at `/capacity` rather than SRS l.812 `/subscription`) in `routers/be1_registry.py` (`read_organization_capacity` at line 771, `configure_organization_capacity` at line 825) delegate commercial subscription/capacity rules to the Billing/Capacity adapter. Per project ownership rules, these routes are listed with `owner: Billing/Capacity (not documented in detail here)` and their internals are not documented here.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/be1/v1/organizations/{organization_id}/capacity` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| PATCH | `/api/be1/v1/organizations/{organization_id}/capacity` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/billing/video-quota/payment-settings` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/billing/video-quota/products` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/billing/video-quota` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/billing/video-quota/invoices` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| POST | `/api/be1/v1/billing/video-quota/checkout` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| POST | `/api/be1/v1/billing/video-quota/invoices/{invoice_id}/reconcile` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| POST | `/api/be1/v1/billing/video-quota/invoices/{invoice_id}/cancel` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/video-quota` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/video-quota/products` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/video-quota/payment-settings` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/video-quota/teachers` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/video-quota/invoices` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| POST | `/api/be1/v1/organizations/{organization_id}/video-quota/invoices/{invoice_id}/reconcile` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| POST | `/api/be1/v1/organizations/{organization_id}/video-quota/invoices/{invoice_id}/cancel` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| POST | `/api/be1/v1/organizations/{organization_id}/video-quota/checkout` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| GET | `/api/be1/v1/organizations/{organization_id}/video-quota/allocations` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| POST | `/api/be1/v1/organizations/{organization_id}/video-quota/allocations` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |
| POST | `/api/be1/v1/organizations/{organization_id}/video-quota/allocations/reclaim` | owner: Billing/Capacity (not documented in detail here) | — | — | — | — | — | `MERGED` |

---

## 11. Phase D Planned Routes (`T-6a`, `T-6b`, `T-6c`)

Four planned `T-6a`/`T-6b` routes below now exist in the working tree of branch `feature/backend-srs-api-v4-d` (worktree `v4d`) and are marked `PENDING-MERGE` (plus the `POST /api/be1/v1/classes/{class_id}/assignments` occupied-class `202` transfer extension in Section 12). The remaining unbuilt routes (`T-6c` conflict/force-close, `T-6a` `account-activations` and `password-recovery` audit row) are listed under `### NOT BUILT YET`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| `POST` | `/api/be1/v1/organizations/{organization_id}/teacher-invitations` | `T-6a`: invite a Teacher into the organization via `password_setup` email outbox (`v4d` `backend/src/sketch2life/interfaces/http/routers/teacher_invitations.py:81-115`). | Headers: `Authorization`, `Idempotency-Key`. Path: `organization_id`. Body `TeacherInvitationRequest`: `{ email }`. | `202 Accepted`: `TeacherInvitationResponse { account_ref, status: "PENDING_VERIFICATION" }` (`Cache-Control: private, no-store`). | `400 INVALID_REQUEST` / `INVALID_IDEMPOTENCY_KEY`, `401`, `403`, `404 RESOURCE_NOT_FOUND`, `409 ACCOUNT_SETUP_UNAVAILABLE`, `422`, `503 IDENTITY_PROVIDER_UNAVAILABLE` / `DATABASE_UNAVAILABLE` / `SERVICE_UNAVAILABLE`. | Required (`Idempotency-Key`). | `UNVERIFIED: SRS id not in code` | `PENDING-MERGE` (`v4d`) |
| `POST` | `/api/be1/v1/organizations/{organization_id}/teacher-invitations/{account_ref}/resend` | `T-6a`: resend Teacher invitation `password_setup` email (`v4d` `backend/src/sketch2life/interfaces/http/routers/teacher_invitations.py:118-152`). | Headers: `Authorization`, `Idempotency-Key`. Path: `organization_id`, `account_ref`. | `202 Accepted`: `TeacherInvitationResponse { account_ref, status: "PENDING_VERIFICATION" }` (`Cache-Control: private, no-store`). | `400 INVALID_REQUEST` / `INVALID_IDEMPOTENCY_KEY`, `401`, `403`, `404 RESOURCE_NOT_FOUND`, `409 ACCOUNT_SETUP_UNAVAILABLE`, `422`, `503 IDENTITY_PROVIDER_UNAVAILABLE` / `DATABASE_UNAVAILABLE` / `SERVICE_UNAVAILABLE`. | Required (`Idempotency-Key`). | `UNVERIFIED: SRS id not in code` | `PENDING-MERGE` (`v4d`) |
| `DELETE` | `/api/be1/v1/classes/{class_id}/assignments/current` | `T-6b`: offboard current active Teacher assignment on a class (`v4d` `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:621-671`). | Headers: `Authorization`, `Idempotency-Key`, `If-Match` (strong `"<n>"`). Path: `class_id`. Empty body required (`_require_empty_offboard_body`). | `202 Accepted`: `Be1TeacherAssignmentTransferAcceptedV1 { contract, transfer_id, class_id, action: "OFFBOARD", state: "TRANSFER_PENDING", assignment_revision, status_url }`. | `400 INVALID_REQUEST` (non-empty body or missing/bad `If-Match`) / `INVALID_IDEMPOTENCY_KEY`, `401`, `403`, `404 RESOURCE_NOT_FOUND`, `409 STALE_REVISION` / `INVALID_STATE_TRANSITION` / `RESOURCE_CONFLICT`, `422`, `503`. | Required (`Idempotency-Key` + `If-Match`). | `UNVERIFIED: SRS id not in code` | `PENDING-MERGE` (`v4d`) |
| `GET` | `/api/be1/v1/classes/{class_id}/assignment-transfers/{transfer_id}` | `T-6b`: poll class Teacher reassignment or offboarding transfer status (`v4d` `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:674-727`). | Header: `Authorization`. Path: `class_id`, `transfer_id`. | `200 OK`: `Be1TeacherAssignmentTransferStatusV1 { contract, transfer_id, class_id, action, state, assignment_revision, created_at, updated_at, last_failure_code, status_url }` (`Cache-Control: private, no-store`). | `401`, `403`, `404 RESOURCE_NOT_FOUND`, `422`, `503`. | Read-only | `UNVERIFIED: SRS id not in code` | `PENDING-MERGE` (`v4d`) |

---

## Phase D and E additions (PENDING-MERGE)

`E4` (`T-BILLN1`, `owner: Billing/Capacity`): adds no HTTP routes; implements background `billing-notices` worker mode and 7 `BILLING_*` notification templates (`v4e` `backend/src/sketch2life/infrastructure/notifications/notification_worker.py:121-159`, `backend/src/sketch2life/application/services/notification_templates.py:46-103`, `backend/src/sketch2life/domain/billing_notice.py:26-100`).

| Method | Path | Purpose | Request | Response | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| `POST` | `/api/be1/v1/classes/{class_id}/assignments` | `T-6b` extension (`v4d`): returns `200 Be1AdultAssignmentV1` when unassigned, or starts `REASSIGN` saga returning `202` when class already has an active Teacher (`v4d` `backend/src/sketch2life/interfaces/http/routers/be1_registry.py:403-613`). | Headers: `Authorization`, `Idempotency-Key`, `If-Match`. Path: `class_id`. Body: `CreateAssignmentRequest { candidate_ref }`. | `200 OK`: `Be1AdultAssignmentV1`, or `202 Accepted`: `Be1TeacherAssignmentTransferAcceptedV1 { action: "REASSIGN", state: "TRANSFER_PENDING", ... }` (`ETag`, `Cache-Control: private, no-store`). | `400 INVALID_REQUEST` / `INVALID_IDEMPOTENCY_KEY`, `401`, `403`, `404 RESOURCE_NOT_FOUND`, `409 STALE_REVISION` / `INVALID_STATE_TRANSITION` / `RESOURCE_CONFLICT`, `422`, `503`. | Required (`Idempotency-Key` + `If-Match`). | `SRS §21.2 l.1650` | `PENDING-MERGE` (`v4d`) |
| `GET` | `/api/lesson-library/v1/organizations/{organization_id}/activities` | `E2` (`T-TCH2`): list published org activities for staff (`_staff`; shared with Teacher). See [TEACHER_API.md](./TEACHER_API.md#phase-d-and-e-additions-pending-merge) (`v4e` `backend/src/sketch2life/interfaces/http/routers/lesson_library.py:264-290`). | Header: `Authorization`. Path: `organization_id`. Query: `limit`, `cursor`. | `200 OK`: `TeacherActivityPageV1`. | `401`, `403`, `404`, `422 INVALID_REQUEST`, `503`. | Read-only | `UNVERIFIED: SRS id not in code` | `PENDING-MERGE` (`v4e`, cross-ref) |

### NOT BUILT YET

- `GET /api/be1/v1/organizations/{organization_id}/teachers/{teacher_ref}/active-story-run-conflict` (`T-6c`): planned endpoint; absent from `v4d`, `v4d2`, and `v4e`.
- `POST /api/be1/v1/organizations/{organization_id}/story-runs/{run_id}/force-close` (`T-6c`): planned endpoint; absent from `v4d`, `v4d2`, and `v4e`.
- `POST /api/auth/v1/password-recovery` (`T-6a` metadata audit row extension): deferred in `D_T-6A_PROMPT.md`; not added in `v4d`.
- `POST /api/auth/v1/account-activations` (`T-6a`): recommended dropped in `D_T-6A_PROMPT.md`; absent from `v4d`, `v4d2`, and `v4e`.
