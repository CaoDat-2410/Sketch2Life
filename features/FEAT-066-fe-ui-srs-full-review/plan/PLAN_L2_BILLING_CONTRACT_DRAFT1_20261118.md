# FEAT-066 L2 — Billing module contract (capacity and video quota, without payment) — Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Contract plan only: no code, schema, migration, test, database or command is authorized. Not independently reviewed.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2 (lane L2 of `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, SHA-256 `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6`).
- **Inputs:** owner answers Q-L2-1 to Q-L2-9 in `plan/PLAN_L2_QUOTA_CONTRACT_QUESTIONS_DRAFT1_20261118.md` (8,300 bytes, SHA-256 `779FDA62C1CBA1E2FC21C75947C667D6DD61ECF02325792EBE9C24199A3580FE`); adopted working SRS (701,157 bytes, `B9B1F42D...`, D-209) §9.7, §9.8, §21.2, §21.4, §23.1–§23.5; the FEAT-063 data table register `artifacts/DATA_TABLE_REGISTER.md` (171,609 bytes, SHA-256 `7CDFDBECDC24E28BB08E62C98A33B338165350204447EBC59B86F5BE69899BC2`), Billing rows (lines 387–395 and 457–465); D-066-63 (fail closed; versioned concurrency-safe admission; no direct read of Billing storage).
- **Source fact:** no Billing code, table or migration exists in the backend at `origin/dev` (`1c9148e8`).
- **Not in this plan (payment teammate):** invoices, payment attempts, provider callbacks and their receipts, quotes, checkout, renewal charging, refunds, MoMo/VNPAY adapters. Only the two commands the payment work calls into Billing are specified (section 5.4).

## 1. Module boundary

- A new bounded module `billing` in the backend with its own PostgreSQL schema `billing`, domain, application ports and infrastructure adapters, following the repository's inward dependency rule (interfaces → application → domain; infrastructure implements ports).
- BE1 and Story use Billing only through versioned application ports; they never read or write `billing.*` tables, and Billing never reads BE1 or Story tables. No cross-module SQL transaction (SRS §9.7, §23.5).
- Owner scope is typed: `ORGANIZATION` (organization ref from BE1) or `PARENT_ACCOUNT` (Parent account ref). No Teacher-account scope (SRS §23.5; register note 10).

## 2. Tables

Owned and built by the owner in this lane (names and columns as in the data table register unless marked NEW):

| Table | Purpose | Key rules |
|---|---|---|
| `billing.price_versions` | Immutable commercial/policy versions: `included_class_slots=10`, slot prices, `parent_monthly_video_units_config`, `school_monthly_video_units_config` | Immutable; unique version and effective interval. Prices are set by the payment side; this lane reads `included_class_slots` and the monthly video units. The monthly units carry the temporary value chosen at implementation (Q-L2-5) |
| `billing.organization_subscriptions` | One current subscription per organization: status, period, `grace_until` | Unique partial "one current per organization". Created by Platform Admin with the organization (Q-L2-4); status transitions are written by Billing commands (section 5.3) |
| `billing.capacity_periods` | Inputs of a period: `included_slots`, `paid_extra_slots` | Unique (subscription, period_start). Effective capacity is derived, never stored |
| `billing.subscription_events` | Append-only history: state changes and per-class suspension selections with a shared change group | One row per suspended class |
| `billing.capacity_reservations` (**NEW**, not in the register) | Short-lived slot reservations for class creation (Q-L2-2) | `reservation_id`, organization ref, capacity snapshot version, `state` (`HELD`, `CONFIRMED`, `RELEASED`, `EXPIRED`), `class_ref` once confirmed, `idempotency_key_hash`, `expires_at`. Requires a register update approved with this plan |
| `billing.video_quota_grants` | Append-only entitlements: `MONTHLY_INCLUDED` or `PURCHASE` | Included grant expires at month end Asia/Ho_Chi_Minh; purchase grant never expires; unique source event for purchases; unique (scope, month) for included grants (lazy creation, Q-L2-6) |
| `billing.video_quota_usage` | Append-only usage ledger, one unit per accepted full-video request | Unique (owner scope, request idempotency); no FK to Story; kept after run deletion |

Read only by this lane, owned by the payment teammate: `billing.invoices`, `billing.payment_attempts`, `billing.provider_event_receipts` (referenced only through the IDs the payment commands pass in).

## 3. Derived values

- **Effective capacity** of an organization at time *t* = `included_slots` + `paid_extra_slots` of the capacity period containing *t* − classes whose suspension (from `subscription_events`) is effective at *t* (SRS §23.1 line 1861, §23.4).
- **Used slots** = confirmed reservations for classes that are active and not suspended, plus unexpired `HELD` reservations. Billing learns class activity only through confirmed reservations and the suspension events it writes itself; archiving a class releases its slot through the port in 5.1 (`release_class_slot`).
- **Can create a class** = subscription status in {`ACTIVE`, `GRACE`, `CANCEL_AT_PERIOD_END` within the paid period} and used slots < effective capacity. `RESTRICTED` and `CANCELED` block creation (SRS §23.3).
- **Video-quota balance** of a scope = units of valid grants (included grant of the current month not expired, plus purchase grants) − usage rows referencing them. Never stored (SRS §23.5 line 1906).

## 4. Concurrency

- All capacity commands for one organization serialize on a Billing-owned lock (row lock on the current subscription row), inside Billing's own transaction.
- Video-quota admission serializes per owner scope (lock on the scope's current included grant row, created lazily if absent) and inserts the usage row in the same Billing transaction.
- Reservations expire after a short fixed time (value chosen at implementation, for example 60 seconds); an expired `HELD` reservation no longer counts.

## 5. Ports (application interfaces, versioned)

### 5.1 `CapacityAdmissionPortV1` — used by BE1 class creation

| Operation | Input | Result |
|---|---|---|
| `reserve_class_slot` | organization ref, idempotency key, actor ref | `RESERVED` (reservation ID, capacity version, expires_at) / `CAPACITY_REACHED` / `SUBSCRIPTION_RESTRICTED` / `NO_SUBSCRIPTION` |
| `confirm_class_slot` | reservation ID, class ref | `CONFIRMED` / `EXPIRED` / `UNKNOWN_RESERVATION` |
| `release_class_slot` | reservation ID or class ref, reason | `RELEASED` (idempotent) |
| `read_capacity` | organization ref | effective capacity, used, available, subscription status, version (for read-only UI) |

BE1 flow for `POST .../classes` (SRS §21.2 line 1649): validate scope → `reserve_class_slot` → insert class in BE1's own transaction → `confirm_class_slot`. If the insert fails, `release_class_slot`. If confirm returns `EXPIRED`, BE1 must not keep an over-capacity class: it marks the class creation failed and removes or deactivates the class (exact compensation fixed in the capacity slice plan). Same idempotency key + same payload returns the original result (SRS §21.4).

Public mapping (owner answers and SRS §9.8): `CAPACITY_REACHED` → 409 `CLASS_CAPACITY_REACHED`; `SUBSCRIPTION_RESTRICTED` → 409 `SUBSCRIPTION_RESTRICTED`; Billing unreachable, timeout or indeterminate → **503 `BILLING_UNAVAILABLE`**, `retryable=true`, `Retry-After` when known, no class created (Q-L2-3; new code to be added to SRS §9.8). `NO_SUBSCRIPTION` → 409 `SUBSCRIPTION_RESTRICTED` (proposal; confirm in review).

### 5.2 `VideoQuotaPortV1` — used by Story's generation saga (connected later, Q-L2-8)

| Operation | Input | Result |
|---|---|---|
| `admit_video_request` | owner scope, request ref, idempotency key, contract version | `ACCEPTED` (usage ID, grant ID) / `QUOTA_EXCEEDED` / `UNAVAILABLE`; same key returns the same usage (SRS §23.5 line 1907) |
| `read_balance` | owner scope | granted, used, available, current period, grants summary |

Admission order: create the current month's included grant if absent (Q-L2-6) → use the current included grant first, then purchase grants FIFO → insert one usage row. Exhaustion maps to 409 `VIDEO_QUOTA_EXCEEDED` (SRS §9.8, §23.5 line 1908). No reversal of usage, ever.

### 5.3 `SubscriptionAdminPortV1` — used by Platform Admin organization setup and by the payment work's renewal outcome

| Operation | Caller | Effect |
|---|---|---|
| `open_subscription` | Platform Admin, when an organization is created (Q-L2-4); seed for local | Creates an `ACTIVE` subscription on the current price version and the first capacity period with 10 included slots, 0 paid extra |
| `record_renewal_outcome` | payment work (renewal success/failure after verified provider event) | `ACTIVE` → new period; failure → `GRACE` with `grace_until` = +7 days; restore in grace → `ACTIVE` (SRS §23.3). Idempotent by payment event ID |
| `expire_grace` | Billing itself when `grace_until` passes (checked lazily on any command or read) | `GRACE` → `RESTRICTED` |
| `schedule_downgrade` | School Manager downgrade with selected classes (SRS §23.4) | Writes one `subscription_events` row per selected class with a shared change group; effective at the next period |

### 5.4 `PaymentFulfilmentPortV1` — the two commands the payment teammate calls (Q-L2-7)

| Command | Input | Effect | Idempotency |
|---|---|---|---|
| `activate_add_on_slots` | organization ref, period, added slots, invoice ID, verified payment event ID | Increases `paid_extra_slots` for the period immediately (SRS §23.2 step 4) | payment event ID; a repeat changes nothing |
| `issue_top_up_grant` | owner scope, units, invoice ID, verified payment event ID | Appends a `PURCHASE` grant with no expiry (SRS §23.5) | payment event ID (unique source event) |

Both refuse an unverified event; verification is the payment side's job before the call. This interface must be agreed with the payment teammate before either side implements it.

### 5.5 Events

- `CapacityClassSuspensionScheduledV1` (Billing → BE1, versioned, idempotent): at the effective time, BE1 projects the selected classes read-only (SRS §23.4). Delivery through the existing outbox pattern; the exact outbox is fixed in the capacity slice plan.
- Subscription state changes are recorded in `subscription_events`; notifications (§23.4 reminders) are out of scope here (notifications are not in the owner's lanes).

## 6. Public HTTP API in this lane

| Method and path (prefix per O-CONV) | Actor | Response |
|---|---|---|
| `GET /v1/video-quota` (SRS §21.2 line 1678) | Parent owner, assigned Teacher (organization of the occurrence), organization billing admin | granted / used / available and the period; scope derived from the verified actor; no owner ID from the client |
| `GET .../organizations/{org_id}/capacity` (**NEW**, proposal for the School Manager class page) | School Manager of the organization | effective capacity, used, available, subscription status — read only |
| `POST .../organizations/{org_id}/classes` (existing route; changed by the capacity slice) | School Manager | 201 / 409 `CLASS_CAPACITY_REACHED` / 409 `SUBSCRIPTION_RESTRICTED` / 503 `BILLING_UNAVAILABLE` |

The Platform Admin `open_subscription` call is wired into the existing Platform Admin organization/account flow in its own slice; no new public route is proposed for it here.

## 7. Errors and envelope

All public errors use the SRS §9.8 envelope as fixed by the conventions slice (O-CONV). Codes used: `CLASS_CAPACITY_REACHED`, `SUBSCRIPTION_RESTRICTED`, `VIDEO_QUOTA_EXCEEDED` (all 409, existing in §9.8), `BILLING_UNAVAILABLE` (503, new), `INVALID_IDEMPOTENCY_KEY` (400), `RESOURCE_NOT_FOUND` (404 for out-of-scope).

## 8. Implementation slices (each with its own Task Approval, in the one-BE-slice-at-a-time queue)

1. **B-1 Billing foundation:** schema, migration (new Alembic revision on its own branch label), domain, repositories, `SubscriptionAdminPortV1.open_subscription`, `read_capacity`, unit and contract tests; seed support.
2. **B-2 Capacity admission:** `CapacityAdmissionPortV1`, BE1 class-create integration, public mapping, concurrency test on a disposable PostgreSQL database (two concurrent creates at the last slot), `GET .../capacity`.
3. **B-3 Video-quota ledger and read:** grants (lazy monthly), usage, `VideoQuotaPortV1` with contract tests, `GET /v1/video-quota`.
4. **B-4 Payment interface:** `PaymentFulfilmentPortV1` after agreement with the payment teammate.
5. **B-5 Subscription lifecycle:** renewal outcome, grace expiry, downgrade scheduling and the suspension event to BE1.
6. **Later (not this lane's timing):** connect `admit_video_request` to the Story saga when the video flow exists.

## 9. Acceptance criteria for the contract (before B-1 approval)

1. Every table, port operation, state and code traces to the SRS, the register, D-066-63 or an owner answer; NEW items are marked and listed for register update.
2. No payment responsibility is placed in this module beyond the two fulfilment commands.
3. Concurrency rules make over-capacity and double-use impossible under concurrent commands, stated per operation.
4. Idempotency is defined for every state-changing operation (key, scope, replay, mismatch → 400).
5. BE1 and Story never touch `billing.*` storage; Billing never touches theirs.

## 10. Open items

- The compensation when `confirm_class_slot` returns `EXPIRED` after the class insert (5.1).
- Reservation expiry value; included monthly units temporary value.
- `NO_SUBSCRIPTION` public mapping.
- Register update for `billing.capacity_reservations`; SRS §9.8 update for `BILLING_UNAVAILABLE` (both owner-approved documentation changes, not part of this plan).
- Agreement of section 5.4 with the payment teammate.
- Route prefix (O-CONV) and the conventions envelope.
- Whether `GET .../capacity` is wanted, or capacity is shown only through class-create errors.
