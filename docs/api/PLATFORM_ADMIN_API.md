# Platform Admin API Reference

- **Integration tree:** `feature/backend-srs-api-and-fe-integration` (`297f2849f9db26bb142123da5e1673dcd58673ae`)
- **Date:** `2026-11-25`
- **Generator note:** Generated from code by agy and checked by Claude
- **Route counts by Status:**
  - `MERGED`: 66 (42 documented in detail + 24 `owner: Billing/Capacity`)
  - `pending merge (Phase D, planned)`: 0
  - **Total:** 66

## How to read this file

- **Authentication & Role Authorization:** Every endpoint requires a verified bearer token (`Authorization: Bearer <token>`, resolved via `get_verified_adult`). Platform Admin routes (`service.identity()`) require an active `AdultIdentityModel` with `account_role == "platform_admin"`, except `/api/platform-admin/v1/inbox`, `/api/platform-admin/v1/inbox/{item_id}/read`, `/api/platform-admin/v1/preferences` (`identity(admin=False)`), and organization feedback routes (`LessonFeedbackService.authorize`). Content publishing/review/curation actions additionally require an active `content_admin` permission grant (`CONTENT_PERMISSION_REQUIRED`, `403`).
- **`AdminRoute` Headers (`routers/platform_admin.py`, `routers/platform_admin_accounts.py`):** All `/api/platform-admin/v1/...` routes use `AdminRoute` (`interfaces/http/admin_route.py`), which adds `Cache-Control: no-store`, `Vary: Authorization`, and on 2xx JSON dicts with positive integer `revision` sets `ETag: "<revision>"`.
- **Error Envelope & `If-Match`:**
  - `/api/platform-admin/v1/...` and `/api/lesson-library/v1/platform/...` belong to `CONV1_PREFIXES` (`error_envelope.py`) and return CONV-1 `Be1Error` (`code`, `message`, `correlation_id`, `retryable`, `retry_after_seconds`, `field_errors`, `request_id`, plus `current_version` on `409 STALE_REVISION`).
  - `routers/platform_admin.py` `revision()` dependency raises `428 PRECONDITION_REQUIRED` if `If-Match` is missing, `422 INVALID_REVISION` if not a quoted positive integer (`"<int>"`), and `AdminError` `409 STALE_REVISION` on mismatch.
  - `routers/lesson_library.py` `_strong_revision()` raises `400 INVALID_REQUEST` if `If-Match` is missing or malformed.
  - `/api/svg-catalog/v1/platform/...` (`routers/svg_catalog.py`) is **outside** `CONV1_PREFIXES` (`error_envelope.py`), returning FastAPI `{"detail": {"code": ..., "message": ...}}` errors.
- **Metadata-only Guarantee:** Platform Admin APIs exclude child names/profiles, raw AI prompts/outputs, signed media URLs, and raw secrets.
- **Billing, Capacity, Quota & Subscription Admin Routes:** Owned by Billing/Capacity; listed in [Section 10](#10-billing-capacity-quota--subscription-admin-external-owner) with `owner: Billing/Capacity`, method, and path only.

## Table of Contents

1. [Session, Inbox & Preferences](#1-session-inbox--preferences)
2. [Organizations](#2-organizations)
3. [Accounts, Permissions & Setup E-mail](#3-accounts-permissions--setup-e-mail)
4. [Audit Log & Retention](#4-audit-log--retention)
5. [Operations, Lifecycle, E-mail Deliveries & Settings](#5-operations-lifecycle-e-mail-deliveries--settings)
6. [Platform Lessons & Moderation](#6-platform-lessons--moderation)
7. [Activity Catalog](#7-activity-catalog)
8. [SVG Catalog — Platform Admin](#8-svg-catalog--platform-admin)
9. [Organization Feedback](#9-organization-feedback)
10. [Billing, Capacity, Quota & Subscription Admin (External Owner)](#10-billing-capacity-quota--subscription-admin-external-owner)

---

## 1. Session, Inbox & Preferences

Routes in `routers/platform_admin.py` and service logic in `infrastructure/platform_admin/service.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/session` | Read active Platform Admin identity and effective permission grants | Bearer token | `200` `{account_id, role, role_revision, items[{permission, active, effective, revision}]}` (`platform_admin.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED` | none | `FR-C-01`, `FR-PL-01` | `MERGED` |
| GET | `/api/platform-admin/v1/inbox` | List caller's admin inbox items and unread count (`identity(admin=False)`) | Query `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{unread_count, limit, next_cursor, items[{item_id, kind, is_read, created_at}]}` (`service.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `422 INVALID_CURSOR` | none | `FR-B-09`, `§21.1` | `MERGED` |
| POST | `/api/platform-admin/v1/inbox/{item_id}/read` | Mark one admin inbox item as read (`identity(admin=False)`) | Path `item_id`; Header `Idempotency-Key` | `200` `{item_id, is_read: true}` (`service.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY` | `Idempotency-Key required` | `FR-B-09`, `§21.2` | `MERGED` |
| GET | `/api/platform-admin/v1/preferences` | Read caller's notification locale & email preferences (`identity(admin=False)`) | Bearer token | `200` `{locale, email_notifications, revision}` (`service.py`) + `ETag` (if `revision > 0`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED` | none | `UNVERIFIED: SRS id` | `MERGED` |
| PUT | `/api/platform-admin/v1/preferences` | Update caller's locale and email notification preferences (`identity(admin=False)`) | Header `Idempotency-Key`; `PreferenceInput` (`locale`: `vi-VN, en-US`, `email_notifications`, `expected_revision`; `schemas/platform_admin.py`) | `200` `{locale, email_notifications, revision}` (`service.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION` | `Idempotency-Key required` (optimistic locking via JSON `expected_revision`) | `UNVERIFIED: SRS id` | `MERGED` |

---

## 2. Organizations

Routes in `routers/platform_admin.py` and service logic in `infrastructure/platform_admin/service.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/organizations` | Search and page organizations by display name, ID, or normalized state | Query `search` (max 120 chars), `state` (`active, paused, disabled`), `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{items[{organization_id, display_name, state, revision}], total, limit, next_cursor}` (`service.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `422 INVALID_CURSOR` | none | `FR-PL-01`, `FR-PL-02`, `§21.1` | `MERGED` |
| POST | `/api/platform-admin/v1/organizations` | Create a new organization in `active` state | Header `Idempotency-Key`; `OrganizationInput` (`display_name`; `schemas/platform_admin.py`) | `201` `{organization_id, display_name, state: "active", revision: 1}` (`service.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `409 INVALID_IDEMPOTENCY_KEY` | `Idempotency-Key required` | `FR-PL-01`, `FR-PL-02`, `§21.2` | `MERGED` |
| GET | `/api/platform-admin/v1/organizations/summary` | Read organization counts grouped by state (`active`, `paused`, `disabled`, `other`) | Bearer token | `200` `{total, active, paused, disabled, other}` (`service.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED` | none | `FR-PL-01`, `FR-PL-02` | `MERGED` |
| GET | `/api/platform-admin/v1/organizations/{organization_id}` | Read single organization detail | Path `organization_id` | `200` `{organization_id, display_name, state, revision, created_at}` (`service.py`) + `ETag` | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-PL-01`, `FR-PL-02` | `MERGED` |
| PATCH | `/api/platform-admin/v1/organizations/{organization_id}` | Update organization `display_name` and/or `state` | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `OrganizationUpdateInput` (`display_name`, `state`: `active, paused, disabled`; `schemas/platform_admin.py`) | `200` `{organization_id, display_name, state, revision}` (`service.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED` | `Idempotency-Key required`; `If-Match required` | `FR-PL-01`, `FR-PL-02`, `§21.2` | `MERGED` |

---

## 3. Accounts, Permissions & Setup E-mail

Routes in `routers/platform_admin_accounts.py` and `routers/platform_admin.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/accounts` | List adult accounts with optional role/state/search filters and cursor/deprecated-offset paging | Query `role` (`parent, teacher, school_manager, platform_admin`), `state` (`active, disabled, pending_verification`), `search` (1..120 chars), `limit`, `offset` (deprecated), `cursor` | `200` `AccountPageResponse` (`items`: `AccountResponse[{account_id, email, display_name, role, state, revision}]`, `total`, `limit`, `offset`, `next_cursor`; `platform_admin_accounts.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `503 IDENTITY_PROVIDER_UNAVAILABLE` | none | `FR-PL-01`, `FR-O-09`, `§21.1` | `MERGED` |
| POST | `/api/platform-admin/v1/accounts` | Provision a Firebase identity, assign role (and org assignment if `school_manager`), and enqueue `password_setup` outbox email | Header `Idempotency-Key`; `AccountCreateRequest` (`email`, `display_name`, `role`, `organization_id` iff `school_manager`; `platform_admin_accounts.py`) | `201` `AccountResponse` (`account_id`, `email`, `display_name`, `role`, `state: "pending_verification"`, `revision: 1`; `platform_admin_accounts.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 ACCOUNT_SETUP_UNAVAILABLE`, `503 IDENTITY_PROVIDER_UNAVAILABLE` | `Idempotency-Key required` | `FR-PL-01`, `FR-O-09`, `§21.2` | `MERGED` |
| PATCH | `/api/platform-admin/v1/accounts/{account_id}` | Change account role, access state, or `school_manager` org binding (prevents self-disable, self-demotion, or removing last active admin) | Header `Idempotency-Key`; `AccountUpdateRequest` (`role`, `state`, `organization_id`; `platform_admin_accounts.py`) | `200` `AccountResponse` (`account_id`, `email`, `display_name`, `role`, `state`, `revision`; `platform_admin_accounts.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 SELF_DISABLE_DENIED`, `409 SELF_ROLE_CHANGE_DENIED`, `409 LAST_PLATFORM_ADMIN`, `422 ORGANIZATION_REQUIRED`, `503 IDENTITY_PROVIDER_UNAVAILABLE`, `503 ACCOUNT_UPDATE_UNAVAILABLE` | `Idempotency-Key required` | `FR-PL-01`, `FR-C-01`, `§21.2` | `MERGED` |
| GET | `/api/platform-admin/v1/accounts/{account_id}/permissions` | Read content-admin permission grants and effective status for an account | Path `account_id` | `200` `{account_id, items[{permission, active, effective, revision}]}` (`service.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-PL-01`, `BR-51` | `MERGED` |
| PUT | `/api/platform-admin/v1/accounts/{account_id}/permissions/content-admin` | Grant or revoke `content_admin` permission for another active `platform_admin` account | Header `Idempotency-Key`; `PermissionInput` (`active`, `expected_revision`, `reason`; `schemas/platform_admin.py`) | `200` `{account_id, permission: "content_admin", active, revision}` (`service.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `403 SELF_PERMISSION_CHANGE_DENIED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `422 ACTIVE_PLATFORM_ADMIN_REQUIRED` | `Idempotency-Key required` (optimistic locking via JSON `expected_revision`) | `FR-PL-01`, `BR-51`, `§21.2` | `MERGED` |
| POST | `/api/platform-admin/v1/accounts/{account_id}/setup-email` | Enqueue a `password_setup` outbox email for an `active` or `pending_verification` account | Path `account_id`; Header `Idempotency-Key` | `202` `{delivery_id, state: "pending"}` (`service.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY` | `Idempotency-Key required` | `FR-O-09`, `§21.2` | `MERGED` |

---

## 4. Audit Log & Retention

Routes in `routers/platform_admin.py` and service logic in `infrastructure/platform_admin/service.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/audit` | Query metadata-only platform audit feed (child IDs, free text, payloads excluded) | Query `action` (max 128 chars), `organization_id` (max 128 chars), `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{total, limit, next_cursor, items[{audit_id, action, decision, resource_type, created_at, organization_id, resource_id?, actor_ref?}]}` (`service.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `422 INVALID_CURSOR` | none | `FR-C-10`, `FR-PL-01` | `MERGED` |
| GET | `/api/platform-admin/v1/audit/retention` | Read current platform audit retention policy and eligible count | Bearer token | `200` `{retention_days, revision, updated_by, updated_at, total_entries, eligible_count, oldest_entry_at, newest_entry_at, last_purged_at, last_purged_count}` (`service.py`) + `ETag` | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `503 AUDIT_RETENTION_POLICY_UNAVAILABLE` | none | `FR-C-10`, `FR-PL-01` | `MERGED` |
| PUT | `/api/platform-admin/v1/audit/retention` | Update platform audit retention policy (`retention_days` `1..36500` or `null` for indefinite) | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `AuditRetentionInput` (`retention_days`; `schemas/platform_admin.py`) | `200` `{retention_days, revision, updated_by, updated_at}` (`service.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED`, `503 AUDIT_RETENTION_POLICY_UNAVAILABLE` | `Idempotency-Key required`; `If-Match required` | `FR-C-10`, `FR-PL-01`, `§21.2` | `MERGED` |
| GET | `/api/platform-admin/v1/audit/retention/preview` | Preview eligible audit entry count and bounded batch size (`<= 500`) before purge | Bearer token | `200` `{retention_days, policy_revision, cutoff, candidate_count, batch_count, batch_limit: 500, oldest_candidate_at}` (`service.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `503 AUDIT_RETENTION_POLICY_UNAVAILABLE` | none | `FR-C-10` | `MERGED` |
| POST | `/api/platform-admin/v1/audit/retention/purge` | Purge up to `500` expired audit entries matching a previewed `cutoff` and `expected_count` | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `AuditPurgeInput` (`cutoff`, `expected_count` 1..500; `schemas/platform_admin.py`) | `200` `{deleted_count, cutoff, revision, purged_at}` (`service.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 AUDIT_RETENTION_INDEFINITE`, `409 AUDIT_RETENTION_CUTOFF_TOO_RECENT`, `409 AUDIT_RETENTION_PREVIEW_STALE`, `422 INVALID_RETENTION_CUTOFF`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED`, `503 AUDIT_RETENTION_POLICY_UNAVAILABLE` | `Idempotency-Key required`; `If-Match required` | `FR-C-10`, `§21.2` | `MERGED` |

---

## 5. Operations, Lifecycle, E-mail Deliveries & Settings

Routes in `routers/platform_admin.py` and read queries in `infrastructure/platform_admin/operations.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/operations` | Read metadata-only DB/Redis broker health, AI job counts, core outbox, email, and lifecycle summaries | Bearer token | `200` `{database, broker, queue, jobs, core_outbox, email, lifecycle}` (`operations.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED` | none | `FR-PL-01` | `MERGED` |
| GET | `/api/platform-admin/v1/lifecycle` | Page organization data lifecycle requests across orgs (`requested, running, awaiting_external_purge, completed, exception`) | Query `state`, `organization_id` (max 128 chars), `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{total, limit, next_cursor, items[{request_id, organization_id, request_type, state, unresolved_items, created_at, completed_at}]}` (`operations.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `422 INVALID_CURSOR` | none | `FR-C-10`, `§21.1` | `MERGED` |
| GET | `/api/platform-admin/v1/email-deliveries` | Page metadata-only email delivery outbox items (`pending, sending, sent, failed`) | Query `state`, `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{total, limit, next_cursor, items[{delivery_id, template, state, attempts, failure_code, created_at}]}` (`operations.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `422 INVALID_CURSOR` | none | `FR-O-09`, `§21.1` | `MERGED` |
| GET | `/api/platform-admin/v1/settings` | Read non-secret runtime feature flags (payments, sandbox, SMTP configured) and caller preferences | Bearer token | `200` `{environment, real_payments_enabled, momo_checkout_enabled, momo_sandbox_enabled, vnpay_checkout_enabled, vnpay_sandbox_enabled, monthly_auto_renew_enabled, billing_sandbox_enabled, smtp_configured, preferences}` (`platform_admin.py`) | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED` | none | `FR-PL-01` | `MERGED` |

---

## 6. Platform Lessons & Moderation

Platform lesson authoring/publishing routes in `routers/platform_admin.py` (`PlatformLessonService` in `infrastructure/lesson_library/platform_publication.py`) and cross-org moderation in `routers/lesson_library.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/lessons` | List `PLATFORM`-owned lessons filtered optionally by `review_state` | Query `state` (`DRAFT, PENDING_REVIEW, CHANGES_REQUESTED, APPROVED`), `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{items[], total, limit, next_cursor}` (`platform_publication.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `422 INVALID_CURSOR` | none | `FR-PL-05`, `BR-51`, `§21.1` | `MERGED` |
| GET | `/api/platform-admin/v1/lessons/{lesson_id}` | Read full detail of a `PLATFORM` lesson (`current_version`, `reviews`, `is_published_version`) | Path `lesson_id` | `200` `{lesson_id, is_author, reviews[{review_id, decision, reason}], revision, version_id, version_no, content_hash, review_state, visibility, moderation_state, is_published_version, content}` (`platform_publication.py`) + `ETag` | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-PL-05`, `BR-51` | `MERGED` |
| POST | `/api/platform-admin/v1/lessons` | Author version 1 (`DRAFT`, `PRIVATE`) of a new `PLATFORM` lesson | Header `Idempotency-Key`; `PlatformLessonWrite` (`content`: `LessonContentInputV1`; `schemas/platform_admin.py`) | `201` platform lesson detail (`platform_publication.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `409 INVALID_IDEMPOTENCY_KEY` | `Idempotency-Key required` | `FR-PL-05`, `§21.2` | `MERGED` |
| PATCH | `/api/platform-admin/v1/lessons/{lesson_id}` | Create a new `DRAFT` version of an existing `PLATFORM` lesson (original author only) | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `PlatformLessonWrite` (`content`: `LessonContentInputV1`; `schemas/platform_admin.py`) | `200` updated platform lesson detail (`platform_publication.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `403 AUTHOR_REQUIRED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED` | `Idempotency-Key required`; `If-Match required` | `FR-PL-05`, `§21.2` | `MERGED` |
| POST | `/api/platform-admin/v1/lessons/{lesson_id}/actions` | Submit (`submit`), independently review (`approve`/`request_changes`), publish (`publish`), `hide`, or `unpublish` a `PLATFORM` lesson (`approve`/`request_changes`/`publish`/`hide`/`unpublish` require active `content_admin` permission) | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `PublicationAction` (`action`, `version_id`, `content_hash`, `review_id?`, `reason?`; `schemas/platform_admin.py`) | `200` platform lesson detail (`+ review_id` on review decision; `platform_publication.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `403 AUTHOR_REQUIRED`, `403 CONTENT_PERMISSION_REQUIRED`, `403 REVIEW_PERMISSION_REVOKED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 CONTENT_HASH_MISMATCH`, `409 INVALID_STATE_TRANSITION`, `409 LESSON_RESTORE_REQUIRED`, `409 EXACT_REVIEW_REQUIRED`, `422 REASON_REQUIRED`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED` | `Idempotency-Key required`; `If-Match required` | `FR-PL-05`, `BR-51`, `AC-48`, `§21.2` | `MERGED` |
| PATCH | `/api/lesson-library/v1/platform/lessons/{lesson_id}/moderation` | Hide (`HIDDEN`) or restore (`VISIBLE`) any library lesson at platform moderation level (`lesson_library.py`) | Headers `Idempotency-Key`, `If-Match: "<revision>"` (missing -> `400 INVALID_REQUEST`); `ModerateLessonRequestV1` (`contract`, `state`: `HIDDEN, VISIBLE`, `reason`; `schemas/lesson_library.py`) | `200` `LessonModerationV1` (`lesson_id`, `state`, `reason`, `moderator_ref`, `decided_at`, `revision`; `schemas/lesson_library.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 INVALID_STATE_TRANSITION` | `Idempotency-Key required`; `If-Match required` | `FR-PL-05`, `AC-48` | `MERGED` |

---

## 7. Activity Catalog

Routes in `routers/platform_admin.py` and service logic in `infrastructure/learning_content/admin_catalog.py`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/catalog` | List platform activity catalog items (`draft, submitted, changes_requested, published, recalled, archived`) | Query `state`, `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{items[], total, limit, next_cursor}` (`admin_catalog.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `422 INVALID_CURSOR` | none | `FR-PL-05`, `§21.1` | `MERGED` |
| GET | `/api/platform-admin/v1/catalog/{record_id}` | Read single platform activity catalog item | Path `record_id` | `200` `{is_author, record_id, version, revision, content_hash, state, content, reviews[{review_id, dimension, decision}]}` (`admin_catalog.py`) + `ETag` | `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND` | none | `FR-PL-05` | `MERGED` |
| POST | `/api/platform-admin/v1/catalog` | Create a new `HUMAN_AUTHORED` activity catalog record | Header `Idempotency-Key`; `CatalogWrite` (`activity`: `LessonActivityInputV1`, `age_band`: `36-71, 72-107, 108-120`, `age_band_version`, `provenance`: `HUMAN_AUTHORED`; `schemas/platform_admin.py`) | `201` catalog item view (`admin_catalog.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `409 INVALID_IDEMPOTENCY_KEY` | `Idempotency-Key required` | `FR-PL-05`, `§21.2` | `MERGED` |
| PATCH | `/api/platform-admin/v1/catalog/{record_id}` | Create a revised version of an existing catalog record (original author only) | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `CatalogWrite` (`schemas/platform_admin.py`) | `200` updated catalog item view (`admin_catalog.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `403 AUTHOR_REQUIRED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED` | `Idempotency-Key required`; `If-Match required` | `FR-PL-05`, `§21.2` | `MERGED` |
| POST | `/api/platform-admin/v1/catalog/{record_id}/actions` | Run lifecycle action (`submit`, `review`, `publish`, `hide`, `archive`); non-`submit` actions require `content_admin` permission | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `CatalogAction` (`action`, `version`, `content_hash`, `dimension`: `safety, pedagogical`?, `decision`: `approve, request_changes`?, `reason?`; `schemas/platform_admin.py`) | `200` updated catalog item view (`admin_catalog.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `403 AUTHOR_REQUIRED`, `403 CONTENT_PERMISSION_REQUIRED`, `403 REVIEW_PERMISSION_REVOKED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `409 CONTENT_HASH_MISMATCH`, `422 REVIEW_DIMENSION_REQUIRED`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED` (plus mapped `domain.ContentError` 403/409 codes) | `Idempotency-Key required`; `If-Match required` | `FR-PL-05`, `BR-51`, `§21.2` | `MERGED` |

---

## 8. SVG Catalog — Platform Admin

Routes in `routers/svg_catalog.py` and schemas in `contracts/schemas/svg_engine.py`. Note: `/api/svg-catalog/v1` is **outside** `CONV1_PREFIXES` (`error_envelope.py`), so errors return FastAPI `{"detail": {"code": ..., "message": ...}}` rather than `Be1Error`.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| POST | `/api/svg-catalog/v1/platform/assets` | Create a platform-scoped SVG source asset (`platform_admin` only) | Bearer token; `SvgCatalogAssetCreateRequestV1` (`title_vi`, `topic_key`, `alt_text_vi`, `source_uri`, `license_id`, `license_uri`, `source_svg`; `schemas/svg_engine.py`) | `201` `SvgCatalogAssetResponseV1` (`catalog_entry_id`, `source_asset_ref`, `canonical_asset_ref`, `source_sha256`, `canonical_sha256`, `visibility_scope`: `PLATFORM`, `readiness`, `review_state`; `schemas/svg_engine.py`) | `401` (`get_verified_adult`), `403 FORBIDDEN`, `422` (Pydantic validation), `503 DEPENDENCY_UNAVAILABLE` (plus `SvgCatalogError` / `SvgCatalogPersistenceError` status/codes) | none | `UNVERIFIED: SRS id` | `MERGED` |
| POST | `/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/guide-revisions` | Create an immutable `SketchStrokeGuideV3` revision for a platform catalog entry | Path `catalog_entry_id`; `CreateSvgGuideRevisionRequestV1` (`guide`: `SketchStrokeGuideV3`; `schemas/svg_engine.py`) | `201` `SvgGuideRevisionReceiptV1` (`guide_revision_id`, `guide_ref`, `guide_revision`, `source_sha256`, `guide_sha256`, `guide`, `review_state`: `PENDING`; `schemas/svg_engine.py`) | `401`, `403 FORBIDDEN`, `404`, `422`, `503 DEPENDENCY_UNAVAILABLE` (plus `SvgCatalogError` / `SvgCatalogPersistenceError` codes) | none | `UNVERIFIED: SRS id` | `MERGED` |
| POST | `/api/svg-catalog/v1/platform/assets/{catalog_entry_id}/curation` | Record independent curator `APPROVE`/`REJECT` decision for a platform SVG asset (cannot curate own asset) | Path `catalog_entry_id`; `SvgCurationRequestV1` (`source_sha256`, `decision`: `APPROVE, REJECT`, `grouping_allowed`, `reason?`; `schemas/svg_engine.py`) | `200` `SvgReviewReceiptV1` (`review_id`, `catalog_entry_id`, `review_subject_kind`: `SOURCE_ASSET`, `review_kind`: `CURATOR`, `decision`, `source_sha256`, `grouping_allowed`, `reviewer_ref`, `created_at`; `schemas/svg_engine.py`) | `401`, `403 FORBIDDEN`, `403 INDEPENDENT_CURATION_REQUIRED`, `404`, `422`, `503 DEPENDENCY_UNAVAILABLE` (plus `SvgCatalogError` / `SvgCatalogPersistenceError` codes) | none | `UNVERIFIED: SRS id` | `MERGED` |

---

## 9. Organization Feedback

Routes in `routers/platform_admin.py` backed by `LessonFeedbackService` (`infrastructure/lesson_library/feedback.py`).

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/organizations/{organization_id}/feedback` | List feedback threads for an organization | Path `organization_id`; Query `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{total, limit, next_cursor, items[{thread_id, lesson_id, version_id, revision, created_at}]}` (`feedback.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `422 INVALID_CURSOR` | none | `UNVERIFIED: SRS id` | `MERGED` |
| GET | `/api/platform-admin/v1/organizations/{organization_id}/feedback/{thread_id}` | Read messages in an organization lesson feedback thread | Path `organization_id`, `thread_id`; Query `limit` (1..100, default `25`), `cursor` (max 768 chars) | `200` `{thread_id, organization_id, lesson_id, version_id, revision, limit, next_cursor, items[{message_id, body, from_you, created_at}]}` (`feedback.py`) | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `422 INVALID_CURSOR` | none | `UNVERIFIED: SRS id` | `MERGED` |
| POST | `/api/platform-admin/v1/organizations/{organization_id}/feedback/{thread_id}/replies` | Reply to an organization lesson feedback thread as Platform Admin | Headers `Idempotency-Key`, `If-Match: "<revision>"`; `FeedbackInput` (`body`; `schemas/platform_admin.py`) | `200` `{thread_id, revision}` (`feedback.py`) + `ETag` | `400 INVALID_REQUEST`, `401 AUTH_REQUIRED`, `403 ACTION_NOT_ALLOWED`, `404 RESOURCE_NOT_FOUND`, `409 INVALID_IDEMPOTENCY_KEY`, `409 STALE_REVISION`, `422 INVALID_REVISION`, `428 PRECONDITION_REQUIRED` | `Idempotency-Key required`; `If-Match required` | `UNVERIFIED: SRS id` | `MERGED` |

---

## 10. Billing, Capacity, Quota & Subscription Admin (External Owner)

Listed in `routers/platform_admin.py` only with `owner: Billing/Capacity`, HTTP method, and path per Part B ownership rules.

| Method | Path | Purpose | Request (key fields, headers) | Response (key fields, status) | Error codes | Idempotency | SRS ids | Status |
|---|---|---|---|---|---|---|---|---|
| GET | `/api/platform-admin/v1/billing/quota-products` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/quota-products` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| PUT | `/api/platform-admin/v1/billing/quota-products/{product_id}` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/quota-products/{product_id}/state` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/quota-invoices` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/quota-invoices/{invoice_id}/reconcile` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/quota` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/quota-payment-events` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/quota-products/{product_id}/events` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/sandbox/offers` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/sandbox/offers` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/sandbox/invoices` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/sandbox/invoices` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/sandbox/invoices/{invoice_id}/settle` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/sandbox/included-grants` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/sandbox/quota` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/sandbox/consume` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/sandbox/capacity-prices` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/sandbox/subscriptions` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/sandbox/subscriptions/quote` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| POST | `/api/platform-admin/v1/billing/sandbox/subscriptions/{subscription_id}/quote` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| PATCH | `/api/platform-admin/v1/billing/sandbox/subscriptions/{subscription_id}` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/billing/sandbox/capacity-prices` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
| GET | `/api/platform-admin/v1/organizations/{organization_id}/capacity-classes` | owner: Billing/Capacity | — | — | — | — | — | `MERGED` |
