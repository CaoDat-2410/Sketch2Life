# V3 T-8a plan, Draft 1: notification inbox (DDL-C inbox table, `GET /v1/notifications`, mark-read, producer port)

Date 2026-11-19. Goal v3 Phase C. Facts read at HEAD 6696e888. Source: Draft 5 WP-8, DDL-C (§1.5), TD-14, TD-30, X-12 (OD-08), OD-13, OD-01 (DDL-C approved by name after a passed plan review); SRS §21.2 l.1681, §9.6 l.812, §9.5 l.784 (`NotificationCommandV1`), FR-B-09 l.595, FR-B-14 l.600, FR-C-11 l.503, UC-15 l.1561, REG l.403-405 and l.466-468. Status: plan, not implemented, not reviewed.
**Owner scope rule:** no capacity, subscription, quota, billing or payment code; **no real e-mail or push and no provider call**: the inbox is the source of truth and nothing here delivers. **T-8b (push endpoints) is deferred by the owner**; only what T-8a needs is built (section 7 lists the gaps). **Review rule: 2 reviews** (new migration and a new client contract).

## 1. HEAD facts (verified)

- No notification code, table or route exists (`grep notifications` finds REG/SRS text only). Core has `core_outbox_events` (used by `lesson.parent_group_invited.v1`, `_emit_group_invitation`, `service.py:1587`) but no consumer writes an inbox.
- Identity: `be1_adult_identities` (`subject` PK, `account_id` String(36) UUID, `issuer`, `state`, `account_role` in parent, teacher, school_manager, platform_admin). `get_verified_adult` returns the verified principal; routes load the identity by subject.
- Family envelope: `error_envelope.is_conv1_path` already lists `LESSON_OCCURRENCES_BASE`; a new base is added the same way. Cursor helpers `encode_cursor` / `decode_time_cursor` and `limit_query()` (default 25, max 100, above 100 is 400) exist in `api_conventions.py`. Body style of new `/v1` CONV-1 routes: `contract` literal.
- Alembic at HEAD: 36 revisions, 14 heads by the down-only rule and 10 with `depends_on` (pinned in `test_synthetic_eligibility.py:463`); the BE1/lesson chain is `20261110_ar_0001 -> 20261119_ar_0002 -> 20261119_uf_0001 -> 20261119_oc_0001 -> 20261120_cls_0001` (single head of that chain). Pending migrations before this task: T-7d `20261120_cls_0002` (child of `cls_0001`), T-2c `20261120_b1_0001` (child of `20261119_frc08_lifecycle_scope`), T-1a `20261120_vb_0002` (child of `b1_0001`); the last two sit on the separate `frc08_lifecycle` branch.
- `be1_runtime_router` holds no `/v1` family; `/v1/notifications` has no collision (`/v1/jobs/`, `/v1/lesson-occurrences`, `/v1/story-runs`, `/v1/upload-sessions`, `/v1/parent/profiles` are the other `/v1` prefixes).

## 2. Decisions

| ID | Decision | SRS basis |
|---|---|---|
| D1 | **DDL-C is split.** T-8a creates only `notifications.inbox_items` (section 4). `push_endpoints` and `delivery_attempts` stay unbuilt with T-8b (deferred); they are added later by a second migration of the same package. IN_APP needs no delivery attempt row: the inbox row is the delivery. Q-1 if the coordinator wants all three tables now (5.4 lists them). | FR-B-09, UC-15 alt. flow |
| D2 | **Recipient** = `be1_adult_identities.account_id` (opaque UUID, no FK across owners), with `recipient_role` as the role the notice targets. No e-mail address, UID or issuer is stored. | l.784, REG l.466 |
| D3 | `GET /v1/notifications` and the two mark-read routes are open to every active adult with a role (parent, teacher, school_manager, platform_admin): the recipient is always the caller; no id of another user is accepted. No identity, inactive, issuer mismatch or no role is the uniform 404 `RESOURCE_NOT_FOUND`; another user's item is the same 404. No 403 exists here. | l.864-865, l.1681 |
| D4 | **Item shape (TD-14 candidate):** `NotificationV1 {contract, inbox_item_id, notification_type, template_version, safe_parameters, created_at, read_at|null, expires_at|null}`. Not exposed: recipient, role, organization ref, trigger id, dedupe key, command hash. Page `NotificationPageV1 {contract, items, next_cursor, unread_count}`; `unread_count` is exact up to 100 (100 means 100 or more) for the badge. Order `created_at desc, inbox_item_id desc`; opaque keyset cursor (`encode_cursor` scope `notifications`); `limit` default 25, max 100; a malformed cursor is 400 `INVALID_REQUEST` (`cursor`, `INVALID_FORMAT`). Expired items (`expires_at <= now`) are hidden. Response headers `Cache-Control: private, no-cache`, `Vary: Authorization`. | l.1640, l.1681 |
| D5 | **Mark-read (TD-14):** `POST /v1/notifications/{inbox_item_id}/read` (200 `NotificationV1`) and `POST /v1/notifications/read-all` (200 `NotificationReadAllV1 {contract, marked_count}`). Both naturally idempotent: `UPDATE ... SET read_at = now() WHERE read_at IS NULL` (first write wins; a replay keeps the first `read_at`). Read-all marks only the caller's items that exist and are unread at statement time, not later inserts. Both require a valid `Idempotency-Key` (R11, 400 `INVALID_REQUEST` if missing or malformed) but **store no receipt**: the effect is monotone, so a replay converges to the same state and body. No ETag or `If-Match`: the inbox item has no revision (C-D7 transport per family, monotone field). Deviation from C-D6 recorded for the owner. Q-3. | l.812, l.1697 |
| D6 | **Producer port (l.784):** `application/ports/notifications.py`: frozen `NotificationCommandV1 {recipient_account_id, recipient_role, notification_type, template_version, trigger_id, dedupe_key, safe_parameters, organization_ref=None, expires_at=None}` and `NotificationProducerPort.enqueue(command) -> EnqueueResult {inbox_item_id, created}`. Adapter `SqlNotificationProducer(session)` joins the **caller's transaction** (no commit), so the producer's business write and the inbox row commit together. `INSERT ... ON CONFLICT (recipient_account_id, trigger_dedupe_key) DO NOTHING`; on conflict the stored `command_sha256` is compared: same hash returns the existing id with `created=False`, a different hash raises `NotificationDedupeConflict` (never silently dropped). | l.784, REG l.466, FR-B-09 |
| D7 | **Content rule:** `safe_parameters` is validated in the domain before any write: at most 8 keys; keys `^[a-z][a-z0-9_]{0,31}$`; values string (max 120), int or bool; keys named like `name`, `child`, `story`, `transcript`, `media`, `url`, `email`, `token`, `endpoint`, `address` and values containing `://` or `@` are refused; total JSON at most 2 KiB (also a CHECK). `notification_type` `^[A-Z][A-Z0-9_]{2,63}$`; `template_version` 1..9999. No child name, media, story, transcript or playback URL can enter. | l.1681, FR-B-14 |
| D8 | **No producer is wired.** The reminder (T-1d2), billing notices (X-13) and the group invitation event stay unconnected; the port, the table and the read side are the deliverable. Tests act as the producer. The Android provider stays unavailable (X-12, OD-08): nothing is stored or accepted for it. | OD-08, OD-13 |
| D9 | New `/v1/notifications` base joins the CONV-1 envelope (`is_conv1_path`, `NOTIFICATIONS_BASE` matched on a whole segment so `/v1/notificationsfoo` is excluded). The T-8b paths `/v1/notifications/push-endpoints...` are not registered; they return the framework 404 until T-8b. | R10 |

## 3. Route and contract table

| Route | Actor | Request | Success | Errors |
|---|---|---|---|---|
| `GET /v1/notifications` | any active adult with a role (own inbox) | query `limit` (1-100, default 25), `cursor` | 200 `NotificationPageV1` | 400 `INVALID_REQUEST` (limit, cursor); 401; 404 uniform |
| `POST /v1/notifications/{inbox_item_id}/read` | same | path id (UUID text), header `Idempotency-Key`, no body | 200 `NotificationV1` | 400 key or id; 401; 404 (also another user's, expired, unknown) |
| `POST /v1/notifications/read-all` | same | header `Idempotency-Key`, no body | 200 `NotificationReadAllV1` | 400 key; 401; 404 uniform |

Catalog: three entries in `MOUNTED_OPERATIONS` (+3 on what has landed; counts and the catalog pin test updated, **hot**); schemas `NotificationV1`, `NotificationPageV1`, `NotificationReadAllV1` (strict, no extra fields). No push-endpoint entry.

## 4. DDL: migration `backend/alembic/versions/20261120_nt_0001_notifications_inbox.py`

`revision = "20261120_nt_0001"` (16 chars), `down_revision = "20261120_cls_0002"` (T-7d; **re-run `alembic heads` at implementation**: use the single head of the chain that contains `20261110_ar_0001`; if T-7d is absent it is `20261120_cls_0001`), `branch_labels = None`, `depends_on = None`. It extends the BE1/lesson chain (accounts live there), so the head counts stay (14 by the down-only rule, 10 with depends) and revisions rise by one (36 at HEAD; 39 once T-2c, T-1a and T-7d land; 40 after this task; re-count). Does not touch the `frc08_lifecycle` branch.
```
upgrade():
  op.execute(sa.schema.CreateSchema("notifications", if_not_exists=True))
  op.create_table("inbox_items",
    Column inbox_item_id String(36) PK; recipient_account_id String(36) NOT NULL;
    recipient_role String(24) NOT NULL; organization_ref String(128) NULL;
    notification_type String(64) NOT NULL; template_version Integer NOT NULL;
    trigger_id String(128) NOT NULL; trigger_dedupe_key String(128) NOT NULL;
    command_sha256 String(64) NOT NULL;
    safe_parameters JSONB NOT NULL server_default '{}'::jsonb;
    created_at timestamptz NOT NULL server_default now(); read_at timestamptz; expires_at timestamptz;
    UniqueConstraint(recipient_account_id, trigger_dedupe_key, name="uq_notif_inbox_dedupe");
    CheckConstraint recipient_role IN ('parent','teacher','school_manager','platform_admin') ck_notif_inbox_role;
    CheckConstraint notification_type ~ '^[A-Z][A-Z0-9_]{2,63}$' ck_notif_inbox_type;
    CheckConstraint template_version BETWEEN 1 AND 9999 ck_notif_inbox_template;
    CheckConstraint length(trigger_id) >= 1 AND length(trigger_dedupe_key) >= 1 ck_notif_inbox_keys;
    CheckConstraint command_sha256 ~ '^[0-9a-f]{64}$' ck_notif_inbox_hash;
    CheckConstraint jsonb_typeof(safe_parameters) = 'object' AND octet_length(safe_parameters::text) <= 2048 ck_notif_inbox_params;
    CheckConstraint (read_at IS NULL OR read_at >= created_at) AND (expires_at IS NULL OR expires_at > created_at) ck_notif_inbox_times;
    schema="notifications")
  op.create_index("ix_notif_inbox_page", "inbox_items", ["recipient_account_id", sa.text("created_at DESC"), sa.text("inbox_item_id DESC")], schema="notifications")
  op.create_index("ix_notif_inbox_unread", "inbox_items", ["recipient_account_id"], schema="notifications", postgresql_where=sa.text("read_at IS NULL"))
downgrade():  # refuses while data exists (frc08 DTR precedent), never deletes silently
  op.execute("DO $$ BEGIN IF EXISTS (SELECT 1 FROM notifications.inbox_items) THEN RAISE EXCEPTION 'T-8a downgrade refused: inbox rows exist'; END IF; END $$")
  drop both indexes, op.drop_table("inbox_items", schema="notifications"), op.execute(sa.schema.DropSchema("notifications"))
```
**Rollback command:** `alembic downgrade 20261120_cls_0002` (explicit revision; never `-1`, there are 14 heads). ORM mirror: new `infrastructure/notifications/tables.py` (`NOTIFICATIONS_METADATA = MetaData(schema="notifications")`), registered in `alembic/env.py` (`target_metadata.append`, `_MANAGED_SCHEMAS.add("notifications")`). Pinned tests: `test_synthetic_eligibility.py:463` (revision count, head counts unchanged) and, on gate databases only (NOT CHECKABLE here), `test_m2_s2_g1_parent_story_postgres.py` `_EXPECTED_VERSION_ROWS` (the BE1 chain head id becomes `20261120_nt_0001`).
**If Q-1 = all three tables:** `push_endpoints` and `delivery_attempts` are added with the REG l.404-405 columns and the unique keys of REG l.467-468; not recommended, no code would use them.

## 5. Authorization and state

Guard order: bearer (401) -> identity loaded by subject, active, issuer equal, role in the four (404) -> query always filtered by `recipient_account_id = caller`. Item state machine: `unread` (read_at NULL) -> `read` (terminal, no un-read); `expired` is a read-time filter. Producer writes only the insert.

## 6. Tests

Unit: domain validator (D7 matrix: forbidden keys, values with `://` and `@`, size, counts, type and version bounds); command hash canonical and stable; producer port with a fake session (new, duplicate same hash, duplicate other hash raises); cursor round trip and rejection (scope, tamper, non-time key); item serializer exposes no recipient, trigger or hash; `is_conv1_path` for `/v1/notifications`, `/v1/notifications/x`, not `/v1/notificationsfoo`.
Contract: three catalog rows, schemas strict, `limit` 101 is 400, missing key is 400, no push-endpoint route, route table (+3), error bodies in the CONV-1 envelope.
PostgreSQL (fresh `frc08_v3_t8a_*`, `alembic upgrade heads`; `test_t8a_notifications_postgres.py`): migration up, constraints reject each bad row, `compare_metadata` of the `notifications` schema against the ORM is empty, downgrade to `20261120_cls_0002` works when empty and is refused with a row, up again; two users and four roles: each reads only its own items; another user's item `read` is the same 404 as an unknown id; paging 60 items with limit 25 gives 25/25/10 with no duplicate or gap, and **stable under concurrent inserts** (insert between pages: no repeat, no skip of older rows); unread_count and cap 100; mark-read twice keeps the first `read_at`; read-all marks only own unread, a later insert stays unread; expired hidden; dedupe: same key and hash is one row, same key other hash raises; two concurrent producers one row; Manager and Platform Admin read their own; inactive and no-role identity 404; no row stores an e-mail or URL.
Existing tests touched: `test_openapi_contract_catalog.py` (**hot**), `test_app_composition.py` (route table), `test_synthetic_eligibility.py`, `unit/test_error_envelope*` (new base), `test_m2_s2_g1_parent_story_postgres.py` (gate-only expectation, not run here). Then unit+contract vs the 83-id base, PG run, ruff, mypy, validators, `git diff --check`; `validate_skeleton.py` only if the structure check lists the new folders.

## 7. Allowlist, gaps, risks

New (under `backend/`): migration above; `src/sketch2life/application/ports/notifications.py`; `application/services/notifications.py` (validator, reader); `infrastructure/notifications/{__init__,tables,inbox_repository}.py`; `contracts/schemas/notifications.py`; `interfaces/http/routers/notifications.py`; tests `unit/test_notifications_domain.py`, `contract/test_notifications_routes.py`, `integration/test_t8a_notifications_postgres.py`; evidence `.../evidence/notes/V3_T_8A_EVIDENCE_20261119.md`.
Edit: `alembic/env.py`, `interfaces/http/router_composition.py` (mount, **hot**), `interfaces/http/error_envelope.py` (**hot**, `NOTIFICATIONS_BASE`), `interfaces/http/openapi_contract.py` (**hot**), the tests above. **Not touched:** `app.py`, settings, Core tables, billing or story code, web, mobile, Bruno, seeds (seed S10 IN_APP not built), DECISIONS and approval files.
**Gaps recorded (deferred or open):** T-8b push endpoint routes and tables; delivery attempts, retry and any worker; e-mail and Web Push (OD-13); Android provider (X-12); producers (T-1d2 reminder, billing X-13, group invitation); `unread_only` filter and a web or Android inbox screen; retention or expiry sweeper; commit-order paging caveat (`created_at` is transaction start time, so a very long producer transaction can land behind an already-fetched page; it appears on the next first-page read).
**FE impact:** new reads only; Android and web inbox and badge are later FE slices. **Risks:** R1 migration chain placement (re-read heads); R2 hot catalog files serial with other tasks; R3 `Idempotency-Key` without receipt (D5) may be questioned by review.

## 8. BLOCKED_OPEN and questions (defaults let the task run)

- **Q-1 (coordinator, DDL scope):** "DDL-C is approved as three tables; with T-8b deferred, may T-8a create only `inbox_items` and leave `push_endpoints` and `delivery_attempts` to a second DDL-C migration?" Default yes.
- **Q-2 (TD-14, TD-30 route shapes):** "Are `POST /v1/notifications/{id}/read` and `POST /v1/notifications/read-all` and the item shape of D4 accepted as the TD-14 shapes?" Default yes (technical decision recorded with the package).
- **Q-3 (reviewer):** "Mark-read requires an `Idempotency-Key` but keeps no receipt because the effect is monotone (D5). Accepted?" Default yes.
- Draft decisions numbered at implementation (D1-D9 above).
