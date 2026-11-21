# V3 T-8a plan, Draft 2: notification inbox (DDL-C inbox table, `GET /v1/notifications`, mark-read, producer port)

Date 2026-11-21. Goal v3 Phase C. Replaces Draft 1 after plan review R1 (0/3/6). Facts read at committed v3 tip 318780b6. Source: WP-8, DDL-C (§1.5), TD-14, TD-30, X-12 (OD-08), OD-13, OD-01; SRS l.1681, l.812, l.784 (`NotificationCommandV1`), l.1697, FR-B-09 l.595, FR-B-14 l.600, UC-15 l.1561, REG l.403-405, l.466-468. **Owner scope rule:** no capacity, subscription, quota, billing or payment code; no real e-mail or push, no provider call (the inbox is the source of truth). **T-8b is deferred**: only what T-8a needs is built; gaps in section 7. **Review rule: 2 reviews** (migration and a new client contract).

## Delta from review R1

| Finding | Fixed in |
|---|---|
| T8A-01 (P2) mark-read must keep a receipt (l.1697) | D5, section 5 tests |
| T8A-02 (P2) content rule is an allowlist | D7, tests |
| T8A-03 (P2) exact allowlist, `test_http_error_envelope.py`, stale OpenAPI text | section 7 |
| T8A-04 (P3) size measured in the PostgreSQL text form | D7, DDL |
| T8A-05 (P3) trigger id and dedupe key charset | D7, DDL |
| T8A-06 (P3) clock skew on `expires_at` | D6, D5, DDL |
| T8A-07 (P3) badge semantics | D4 |
| T8A-08 (P3) roles and absent identity | D3, tests |
| T8A-09 (P3) facts | section 1 |
| Coordinator: chain is the only child of `20261120_cls_0002`, which now exists (commit 9476f632) | section 4 |

## 1. HEAD facts (verified)

- No notification code, table or route exists. `core_outbox_events` is used by `lesson.parent_group_invited.v1` (`service.py:1587`, not re-read; irrelevant to the decision); no consumer writes an inbox.
- Identity: `be1_adult_identities` (`subject` PK, `account_id` UUID text, `issuer`, `state`, `account_role` parent, teacher, school_manager, platform_admin). Receipts: `be1_command_receipts` (`be1_models.py:68-92`, PK `(principal_ref, operation_scope, idempotency_key)`, `organization_id` nullable, `request_fingerprint` 64 hex, `response_json`), used by T-3a..T-7d (`lesson_occurrences/documents.py:587-608`).
- CONV-1 family helper `error_envelope.is_conv1_path` with `LESSON_OCCURRENCES_BASE`; cursor helpers `encode_cursor`/`decode_time_cursor`, `limit_query()` (25/100), `parse_idempotency_key` in `api_conventions.py`; body style `contract` literal. `openapi_srs_v22.py:225` says notifications are unavailable (stale once routes exist).
- Alembic at tip: **37 revisions** (36 + `20261120_cls_0002`), 14 heads by the down-only rule and 10 with `depends_on` (pinned in `test_synthetic_eligibility.py:463`). The BE1/lesson chain ends `... 20261119_oc_0001 -> 20261120_cls_0001 -> 20261120_cls_0002` (single head of that chain). Pending on the separate `frc08_lifecycle` branch: T-2c `20261120_b1_0001`, T-1a `20261120_vb_0002`.

## 2. Decisions

| ID | Decision | SRS basis |
|---|---|---|
| D1 | **DDL-C is split.** T-8a creates only `notifications.inbox_items`; `push_endpoints` and `delivery_attempts` wait for T-8b (second migration of the same package). IN_APP needs no delivery row. Q-1 if all three are wanted. | FR-B-09, UC-15 |
| D2 | Recipient = `be1_adult_identities.account_id` (opaque, no cross-owner FK) plus `recipient_role`. No e-mail, UID or issuer stored. | l.784, REG l.466 |
| D3 | The three routes are open to every active adult with a role (including Platform Admin: generic own-inbox read, it touches no teammate-owned admin scope); the recipient is always the caller. No identity (valid bearer, no row), inactive, issuer mismatch, no role, another user's item: uniform 404 `RESOURCE_NOT_FOUND`; no 403. | l.864-865, l.1681 |
| D4 | `NotificationV1 {contract, inbox_item_id, notification_type, template_version, safe_parameters, created_at, read_at, expires_at}`; hidden: recipient, role, organization ref, trigger id, dedupe key, hash. `NotificationPageV1 {contract, items, next_cursor, unread_count}`; `unread_count` is exact up to 100 and **the schema description says 100 means 100 or more**. Order `created_at desc, inbox_item_id desc`, keyset cursor (`encode_cursor` scope `notifications`), `limit` 25 default and 100 max (101 is 400), bad cursor 400 `INVALID_REQUEST`. Expired items hidden. Headers `Cache-Control: private, no-cache`, `Vary: Authorization`. | l.1640, l.1681 |
| D5 | **Mark-read with a durable receipt (T8A-01).** `POST /v1/notifications/{inbox_item_id}/read` (200 `NotificationV1`) and `POST /v1/notifications/read-all` (200 `NotificationReadAllV1 {contract, marked_count}`). `Idempotency-Key` required (400 if missing or malformed). Receipt in `be1_command_receipts` in the same transaction as the update: `principal_ref = principal.subject`; `operation_scope` the **constants** `POST /notifications/read` and `POST /notifications/read-all` (not containing the item id, so the same key on another item is refused); fingerprint = sha256 of canonical `{operation, inbox_item_id}`; `organization_id` NULL; `response_json` = the response body (no content). Same key and fingerprint replays the stored body (a read-all replay keeps the first `marked_count` and does not touch items that arrived later); other fingerprint is 400 `INVALID_IDEMPOTENCY_KEY`. The effect is monotone SQL: `UPDATE ... SET read_at = GREATEST(:now, created_at) WHERE read_at IS NULL AND recipient = caller AND (expires_at IS NULL OR expires_at > :now)`; read-all marks only items existing and unread at statement time. A concurrent first insert of the same receipt is resolved by the PK (IntegrityError, rollback, replay path). No ETag or `If-Match` (no revision; monotone field). | l.812, l.1697, C-D6 |
| D6 | **Producer port (l.784):** `NotificationCommandV1 {recipient_account_id, recipient_role, notification_type, template_version, trigger_id, dedupe_key, safe_parameters, organization_ref=None, expires_at=None}`; `NotificationProducerPort.enqueue(command) -> EnqueueResult {inbox_item_id, created}`. `SqlNotificationProducer(session, clock)` joins the **caller's transaction** (no commit) and sets `created_at` from the injected clock; it validates `expires_at > created_at` before writing (T8A-06) and runs the content validation of D7 itself, as the only writer. `INSERT ... ON CONFLICT (recipient_account_id, trigger_dedupe_key) DO NOTHING`; on conflict the stored `command_sha256` is compared: equal returns the existing id (`created=False`), different raises `NotificationDedupeConflict`. | l.784, FR-B-09 |
| D7 | **Content is an allowlist (T8A-02).** `safe_parameters`: at most 8 keys; keys `^[a-z][a-z0-9_]{0,31}$`; values are **ints, bools, or strings matching `^[A-Za-z0-9_.:-]{1,64}$`** (no spaces, no diacritics, so a person's display name or sentence cannot pass); compact JSON at most 1,536 bytes (below the CHECK, which measures the PostgreSQL text form with `", "` and `": "`, so the CHECK is never the first guard and a valid command cannot fail with a 500). A key denylist (name, child, story, transcript, media, url, email, token, endpoint, address) stays as defence in depth. `trigger_id` and `trigger_dedupe_key` use the charset `^[A-Za-z0-9._:-]{1,128}$` (validator and migration CHECK, T8A-05). `notification_type` `^[A-Z][A-Z0-9_]{2,63}$`; `template_version` 1..9999. Port docstring: parameters are codes, counts and opaque refs, never display text (display text belongs to the template version). | l.1681, FR-B-14 |
| D8 | No producer is wired (T-1d2, billing X-13, group invitation stay unconnected); tests act as producer. Android stays unavailable (X-12, OD-08). | OD-08, OD-13 |
| D9 | `NOTIFICATIONS_BASE = "/v1/notifications"` joins `is_conv1_path` on a whole segment (`/v1/notificationsfoo` excluded). T-8b paths are not registered (framework 404). | R10 |

## 3. Route and contract table

| Route | Actor | Request | Success | Errors |
|---|---|---|---|---|
| `GET /v1/notifications` | any active adult with a role (own inbox) | `limit`, `cursor` | 200 `NotificationPageV1` | 400; 401; 404 |
| `POST /v1/notifications/{inbox_item_id}/read` | same | `Idempotency-Key`, no body | 200 `NotificationV1` | 400 (key, id), `INVALID_IDEMPOTENCY_KEY`; 401; 404 |
| `POST /v1/notifications/read-all` | same | `Idempotency-Key`, no body | 200 `NotificationReadAllV1` | 400; 401; 404 |

Catalog: +3 `MOUNTED_OPERATIONS` entries (re-derive counts at implementation) and strict schemas `NotificationV1`, `NotificationPageV1`, `NotificationReadAllV1`.

## 4. DDL: `backend/alembic/versions/20261120_nt_0001_notifications_inbox.py`

`revision = "20261120_nt_0001"` (16 chars), **`down_revision = "20261120_cls_0002"`** (exists in the committed tree, commit 9476f632; it is the only child of that revision, nothing else chains on it), `branch_labels = None`, `depends_on = None`. At implementation run `alembic heads` and `git grep down_revision` once: if another task has added a child of `cls_0002`, chain after the single head of the chain that contains `20261110_ar_0001`. The frc08 branch (T-2c, T-1a) is not touched; head counts (14, 10) stay; revisions 37 now, 38 after this task (more once T-2c and T-1a land: re-count).
```
upgrade():
  op.execute(sa.schema.CreateSchema("notifications", if_not_exists=True))
  op.create_table("inbox_items",
    inbox_item_id String(36) PK; recipient_account_id String(36) NOT NULL;
    recipient_role String(24) NOT NULL; organization_ref String(128) NULL;
    notification_type String(64) NOT NULL; template_version Integer NOT NULL;
    trigger_id String(128) NOT NULL; trigger_dedupe_key String(128) NOT NULL;
    command_sha256 String(64) NOT NULL; safe_parameters JSONB NOT NULL default '{}'::jsonb;
    created_at timestamptz NOT NULL default now(); read_at timestamptz; expires_at timestamptz;
    UniqueConstraint(recipient_account_id, trigger_dedupe_key) uq_notif_inbox_dedupe;
    CHECK recipient_role IN ('parent','teacher','school_manager','platform_admin') ck_notif_inbox_role;
    CHECK notification_type ~ '^[A-Z][A-Z0-9_]{2,63}$' ck_notif_inbox_type;
    CHECK template_version BETWEEN 1 AND 9999 ck_notif_inbox_template;
    CHECK trigger_id ~ '^[A-Za-z0-9._:-]{1,128}$' AND trigger_dedupe_key ~ '^[A-Za-z0-9._:-]{1,128}$' ck_notif_inbox_keys;
    CHECK command_sha256 ~ '^[0-9a-f]{64}$' ck_notif_inbox_hash;
    CHECK jsonb_typeof(safe_parameters) = 'object' AND octet_length(safe_parameters::text) <= 2048 ck_notif_inbox_params;
    CHECK (read_at IS NULL OR read_at >= created_at) AND (expires_at IS NULL OR expires_at > created_at) ck_notif_inbox_times;
    schema="notifications")
  op.create_index("ix_notif_inbox_page", "inbox_items", [recipient_account_id, text("created_at DESC"), text("inbox_item_id DESC")], schema="notifications")
  op.create_index("ix_notif_inbox_unread", "inbox_items", [recipient_account_id], schema="notifications", postgresql_where=text("read_at IS NULL"))
downgrade():  # refuses while data exists, never deletes silently
  DO $$ ... IF EXISTS (SELECT 1 FROM notifications.inbox_items) THEN RAISE EXCEPTION 'T-8a downgrade refused: inbox rows exist' ... $$
  drop both indexes, drop_table inbox_items, DropSchema notifications
```
**Rollback command:** `alembic downgrade 20261120_cls_0002` (explicit revision; never `-1`, there are 14 heads). ORM mirror `infrastructure/notifications/tables.py` (`MetaData(schema="notifications")`), registered in `alembic/env.py`. Pinned tests: `test_synthetic_eligibility.py:463` (count +1, head counts unchanged) and, gate databases only (NOT CHECKABLE here), `test_m2_s2_g1_parent_story_postgres.py` `_EXPECTED_VERSION_ROWS` (BE1 chain head id becomes `20261120_nt_0001`). If Q-1 = all three tables, `push_endpoints` and `delivery_attempts` follow REG l.404-405 and the keys of l.467-468 (not recommended).

## 5. Authorization, state, tests

Guard order: bearer (401) -> identity by subject, active, issuer, role in the four (404) -> every query filtered by `recipient_account_id = caller`. Item states: unread -> read (terminal); expired is a read-time filter.
Unit: validator matrix (**Vietnamese name `Nguyen Be Lan`, spaced values, diacritics, sentence, URL, e-mail, forbidden keys, size, counts, bounds, trigger charset**); command hash canonical; producer with a fake session (new, duplicate same hash, duplicate other hash raises, `expires_at <= created_at` refused); cursor round trip and rejection; serializer hides recipient, trigger and hash; `is_conv1_path` cases; receipt fingerprint (item id inside, not in the scope string).
Contract: three catalog rows, strict schemas, 101 is 400, missing key 400, no push-endpoint route, route table (+3), CONV-1 error bodies, `unread_count` description.
PostgreSQL (fresh `frc08_v3_t8a_*`, `alembic upgrade heads`): migration up, each CHECK rejects a bad row, `compare_metadata` of the `notifications` schema is empty, downgrade to `20261120_cls_0002` when empty and refused with a row, up again; two users and four roles read only their own; another user's item read is the same 404 as unknown; valid bearer with no identity row 404; 60 items page 25/25/10 with no duplicate or gap and **stable under concurrent inserts**; unread count and cap; mark-read twice keeps the first `read_at`; **same key twice returns the same body; same key on another item is 400 `INVALID_IDEMPOTENCY_KEY`; read-all replay after a new insert returns the original `marked_count` and leaves the new item unread**; expired hidden and not markable; dedupe one row, other hash raises, two concurrent producers one row; no row holds an e-mail or URL.

## 6. Gaps recorded (deferred or open)

T-8b endpoints and tables; delivery attempts, retry, any worker; e-mail and Web Push (OD-13); Android provider (X-12); producers (T-1d2, X-13, invitation); `unread_only` filter and FE inbox and badge; retention sweeper; commit-order paging caveat (`created_at` is the producer clock, a long producer transaction can land behind a served page and appears on the next first-page read); seed S10 not built; stale `openapi_srs_v22.py:225` sentence left unchanged and recorded.

## 7. File allowlist (under `backend/`)

New: the migration; `src/sketch2life/application/ports/notifications.py`; `application/services/notifications.py`; `infrastructure/notifications/{__init__,tables,inbox_repository}.py`; `contracts/schemas/notifications.py`; `interfaces/http/routers/notifications.py`; tests `unit/test_notifications_domain.py`, `contract/test_notifications_routes.py`, `integration/test_t8a_notifications_postgres.py`; evidence `.../evidence/notes/V3_T_8A_EVIDENCE_20261119.md`.
Edit: `alembic/env.py`; `interfaces/http/router_composition.py` (**hot**); `interfaces/http/error_envelope.py` (**hot**); `interfaces/http/openapi_contract.py` (**hot**); `tests/unit/test_http_error_envelope.py` (add the router to `SCANNED_MODULES`, `test_conv1_families` gets the base); `tests/unit/test_synthetic_eligibility.py`; `tests/integration/test_m2_s2_g1_parent_story_postgres.py` (edit only, gate not run); `tests/contract/test_app_composition.py`; `tests/contract/test_openapi_contract_catalog.py` (**hot**). **Not touched:** `app.py`, settings, Core tables, story or billing code, `openapi_srs_v22.py`, web, mobile, Bruno, seeds, DECISIONS and approval files. Then unit+contract vs the 83-id base, PG run, ruff, mypy, validators, `git diff --check`.
FE impact: new reads only. Risks: chain placement (re-read heads); serial hot catalog files.

## 8. BLOCKED_OPEN and questions (defaults let the task run)

- **Q-1 (coordinator):** "DDL-C is approved as three tables; may T-8a create only `inbox_items`?" Default yes.
- **Q-2 (TD-14, TD-30):** "Are the two mark-read routes and the item shape of D4 accepted as the TD-14 shapes?" Default yes.
- Draft decisions numbered at implementation (D1-D9).
