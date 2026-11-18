# FEAT-066 L2 — Billing module contract (capacity and video quota, without payment) — Draft 2

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Contract plan only: no code, schema, migration, test, database or command is authorized. Not independently reviewed.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2 (lane L2 of `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, SHA-256 `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6`).
- **Predecessor, unchanged:** Draft 1 (13,926 bytes, SHA-256 `3E8D243B45E6B4B8646515BD64E65F4F1FDABA110E0F2C064D48CB8C9D72F57E`) and its cold review (Sonnet 5.5 high: NOT READY, 0 P1 / 9 P2 / 11 P3; `evidence/notes/L2_BILLING_CONTRACT_DRAFT1_COLD_REVIEW_20261118.md`, 8,197 bytes, SHA-256 `A6D13BFD6F1AC131C75699D2B5E3602DC4BB1E81F3D50C194EC46298A6BD6C75`). Section 12 disposes of every finding.
- **Inputs:** owner answers Q-L2-1 to Q-L2-9 (`plan/PLAN_L2_QUOTA_CONTRACT_QUESTIONS_DRAFT1_20261118.md`, 8,300 bytes, `779FDA62...`) and the seven answers below; adopted working SRS (701,157 bytes, `B9B1F42D...`, D-209) §9.6, §9.7, §9.8, §21.2, §21.4, §23.1–§23.5; data table register `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` (171,609 bytes, `7CDFDBEC...`), Billing rows (lines 387–395, 457–465, note 10); D-066-63.
- **Status of the owner choices:** all owner answers used here (Q-L2-1..9 and the seven below) are selections in the coordinating session on 2026-11-18, **not yet decision rows**. They become binding when recorded.
- **Gate from the roadmap:** L2 implementation starts only after the Billing interface is agreed with the payment teammate (O-PAY). Payment work (quote, invoice processing, checkout, provider callbacks, charging, refunds) is not in this plan beyond the three commands of section 6.4.
- **Source facts:** no Billing code, table or migration exists at `origin/dev` (`1c9148e8`). Organizations are created only by `backend/src/sketch2life/infrastructure/persistence/be1_bootstrap.py`; no organization-creation route exists. BE1 has no class archive route. `be1_classrooms.state` defaults to `active`.

### Owner answers to the Draft 1 review (2026-11-18)

| Finding | Owner selection | Applied in |
|---|---|---|
| F-02 existing organizations and classes | "Backfill khi mở subscription" | §3.3, §6.1 `reconcile_class_slots`, B-1 |
| F-03 counting rule | "Slot = 10 + add-on, đếm lớp active" | §3.1 |
| F-05 renewal outcome command | "Thêm lệnh thứ 3" | §6.4 |
| F-06 payment-owned tables | "B-1 tạo sẵn bảng rỗng" | §2, B-1 |
| F-08 caller of `open_subscription` | "Bootstrap + seed" | §6.3, B-1 |
| F-08 first price version | "Seed giá trị tạm" | §2, B-1 |
| F-09 period end without payment | "Kỳ local tự gia hạn" | §5 |

## 1. Module boundary

- New bounded module `billing` in the backend with its own PostgreSQL schema `billing`, domain, application ports and infrastructure adapters; dependencies point inward.
- BE1 and Story use Billing only through versioned ports; Billing uses BE1 only through BE1 ports (active class list, actor scope). Nobody reads another module's tables; no cross-module SQL transaction (SRS §9.7, §23.5).
- Owner scope is typed: `ORGANIZATION` or `PARENT_ACCOUNT`. No Teacher-account scope.

## 2. Tables

Created by migration B-1 on a new Alembic branch label `billing`.

| Table | Owner | Purpose and rules |
|---|---|---|
| `billing.price_versions` | this lane (content: payment side later) | Immutable versions (register columns). B-1 seeds one temporary version: `included_class_slots=10`, VND amounts as configurable placeholders, `parent_monthly_video_units_config` and `school_monthly_video_units_config` as the temporary value of Q-L2-5. Real prices are set later by the payment side |
| `billing.organization_subscriptions` | this lane | Register columns plus **NEW** `capacity_revision` (bigint, monotonic). Unique partial "one current per organization". Defaults written by `open_subscription`: `status=ACTIVE`, `billing_period=MONTHLY`, `auto_renew=true`, `provider`, provider refs and `billing_admin_ref` null, `grace_until` null |
| `billing.capacity_periods` | this lane | Register columns; unique (subscription, period_start). Defaults on open: `included_slots=10`, `paid_extra_slots=0`, `prorated_amount=0`, `state=ACTIVE` |
| `billing.subscription_events` | this lane | Register columns plus **NEW** `payment_event_ref` (nullable) with a **NEW** unique index on it (dedupe for payment commands) and **NEW** `change_group_key` uniqueness per downgrade |
| `billing.capacity_reservations` **NEW** | this lane | Class-slot ledger: `reservation_id`, organization ref, `kind` (`CREATE`, `BACKFILL`, `REACTIVATE`), `state` (`HELD`, `CONFIRMED`, `RELEASED`, `EXPIRED`), `class_ref` (set on confirm), `actor_ref`, `operation`, `idempotency_key_hash`, `request_fingerprint`, `capacity_revision_at_reserve`, `expires_at`, timestamps. **NEW** unique (organization, actor, operation, key hash); unique (organization, class_ref) where state = `CONFIRMED` |
| `billing.quota_scopes` **NEW** | this lane | One row per owner scope; the serialization point for video-quota admission |
| `billing.video_quota_grants` | this lane | Register columns; **NEW** unique (owner scope, month) for `MONTHLY_INCLUDED`; unique source event for `PURCHASE` |
| `billing.video_quota_usage` | this lane | Register columns; unique (owner scope, request idempotency) |
| `billing.outbox` **NEW** | this lane | Billing-owned outbox for `CapacityClassSuspensionScheduledV1` (Core's outbox is Core-owned, §9.7) |
| `billing.invoices`, `billing.payment_attempts`, `billing.provider_event_receipts` | **payment teammate** | Created **empty** by B-1 with the register columns so foreign keys resolve; only the payment side writes them. Column set to be agreed with the payment teammate before B-1 |

All NEW items are listed for a data-table-register update approved together with this plan.

## 3. Capacity rules

### 3.1 Counting (owner selection F-03)

- **Capacity of a period** = `included_slots` + `paid_extra_slots` of the capacity period in effect.
- **Used** = classes holding a `CONFIRMED` reservation (kinds `CREATE`, `BACKFILL`, `REACTIVATE`), plus unexpired `HELD` reservations. A suspended class does not hold a slot: its reservation is `RELEASED` when the suspension takes effect; reactivating it needs a new `REACTIVATE` reservation (SRS §23.4: "Chuyển lớp/kích hoạt lại cần capacity").
- **Available** = capacity − used.
- **Interpretation note:** SRS §23.1 line 1861 reads "10 slot cơ bản cộng slot add-on đã thanh toán trong kỳ, trừ lớp được chọn tạm ngưng khi downgrade có hiệu lực". This plan reads the subtraction as "suspended classes are taken out of the active set", not as a second subtraction from capacity. Recorded as an SRS wording clarification item.
- **Worked example:** an organization has 15 active classes on 10 + 5 slots. It downgrades to 10 + 0 and selects 5 classes. At the effective time those 5 reservations are released: capacity 10, used 10, available 0. Creating a class is refused; reactivating one suspended class is refused until a slot frees.

### 3.2 Who may create (SRS §23.3)

Creation is allowed when the subscription is `ACTIVE`, `GRACE`, or `CANCEL_AT_PERIOD_END` within the paid period, and available > 0. `RESTRICTED` and `CANCELED` refuse with `SUBSCRIPTION_RESTRICTED`. In `GRACE` the capacity is that of the last period, extended to `grace_until`.

### 3.3 Existing organizations and classes (owner selection F-02)

`open_subscription` and `reconcile_class_slots` backfill: Billing asks BE1 (port `ActiveClassListPortV1`) for the organization's active class refs and writes one `BACKFILL` `CONFIRMED` reservation per class. If the backfilled count exceeds capacity, existing classes keep working but no class can be created until used < capacity. B-2 (admission) is enabled only after every existing organization has a subscription and has been backfilled.

### 3.4 Capacity revision

`capacity_revision` increases with every capacity-affecting command (open, add-on activation, downgrade effect, reservation state change). `reserve_class_slot` and `read_capacity` return it; reservations store it. Confirm does not require equality: the check under the lock (section 4) is authoritative.

## 4. Concurrency

- **Capacity:** every capacity command for an organization locks the organization's current subscription row (`SELECT ... FOR UPDATE`) in Billing's own transaction, then re-derives used and capacity.
- **Video quota:** every admission for a scope first ensures the `billing.quota_scopes` row (`INSERT ... ON CONFLICT DO NOTHING`), then locks it. Under that lock: replay check first (existing usage for the idempotency key returns the original result); create the current month's included grant if absent (unique (scope, month)); pick the grant (current included first, then purchase grants FIFO); insert one usage row. One lock per scope serializes month boundaries and the last purchase unit.
- **Time:** month boundaries and expiry use database time converted to `Asia/Ho_Chi_Minh`; stored timestamps are UTC.
- **Reservation expiry:** a short fixed time (value set in B-2, for example 60 seconds); expired `HELD` rows stop counting.

## 5. Subscription lifecycle (SRS §23.3; owner selection F-09)

| From | Event | To |
|---|---|---|
| — | `open_subscription` | `ACTIVE`, first period |
| `ACTIVE` | renewal success (`record_renewal_outcome`) | `ACTIVE`, next period |
| `ACTIVE` | renewal failure, or period end with no renewal success | `GRACE`, `grace_until` = period end + 7 days |
| `GRACE` | renewal success | `ACTIVE`, next period |
| `GRACE` | `grace_until` passed | `RESTRICTED` |
| `ACTIVE` | auto-renew turned off | `CANCEL_AT_PERIOD_END` |
| `CANCEL_AT_PERIOD_END` | period end | `RESTRICTED` or `CANCELED` as the payment side reports through `record_renewal_outcome`; `RESTRICTED` if nothing is reported |
| `RESTRICTED` | renewal success | `ACTIVE`, next period (interpretation: the SRS lists restore only within grace; restore from `RESTRICTED` is listed as an open item for confirmation) |

- **Local and test environments only:** a synthetic subscription opened by bootstrap or seed rolls automatically into a new period at period end (owner selection F-09), guarded by the environment setting; production follows the table.
- **Derived at read:** time-based transitions (period end, grace expiry) are derived when read and persisted only inside commands, under the lock, with one idempotent `subscription_events` row.
- **Effect on runs:** in `RESTRICTED` (and `CANCELED`) new runs are refused for the organization scope (SRS §23.3; register line 397): `admit_video_request` returns `SUBSCRIPTION_RESTRICTED`. Parent-account quota is not affected by an organization's subscription.

## 6. Ports (versioned)

### 6.1 `CapacityAdmissionPortV1` (used by BE1)

| Operation | Input | Result |
|---|---|---|
| `reserve_class_slot` | organization ref, actor ref, operation (`CREATE_CLASS` or `REACTIVATE_CLASS`), idempotency key, request fingerprint | `RESERVED` (reservation ID, capacity revision, `expires_at`) / `CAPACITY_REACHED` / `SUBSCRIPTION_RESTRICTED` / `NO_SUBSCRIPTION` |
| `confirm_class_slot` | reservation ID, class ref | `CONFIRMED` / `EXPIRED` (no slot free) / `UNKNOWN_RESERVATION`. Idempotent per (reservation, class ref). A late confirm on an expired reservation re-checks capacity under the lock and confirms if a slot is free |
| `release_class_slot` | reservation ID or class ref, reason | `RELEASED` (idempotent) |
| `reconcile_class_slots` | organization ref | Reads live active classes from BE1; releases `CONFIRMED` slots with no live class; adds `BACKFILL` slots for live classes with none; returns counts and an over-capacity flag |
| `read_capacity` | organization ref | capacity, used, available, subscription status, `capacity_revision` |

**BE1 class-create flow** (SRS §21.2 line 1649; F-01 fix): (1) BE1 checks its idempotency receipt — a replay returns the stored original response; (2) `reserve_class_slot` (Billing commits `HELD`); (3) BE1 opens its transaction, inserts the class and flushes, without committing; (4) `confirm_class_slot` (Billing commits `CONFIRMED`); (5) BE1 stores its receipt and commits. If (2) or (4) fails or is unavailable, BE1 rolls back: no class exists. If (5) fails after (4), BE1 calls `release_class_slot` (best effort) and `reconcile_class_slots` later removes any phantom slot. A crash between (4) and (5) leaves at most an over-count, never an over-capacity class.

### 6.2 `VideoQuotaPortV1` (used by Story; connected to the saga when the video flow exists, Q-L2-8)

| Operation | Input | Result |
|---|---|---|
| `admit_video_request` | owner scope, request ref, idempotency key, request fingerprint, contract version | `ACCEPTED` (usage ID, grant ID) / `QUOTA_EXCEEDED` / `SUBSCRIPTION_RESTRICTED` (organization scope) / `UNAVAILABLE`; same key returns the same usage; same key with another fingerprint → `IDEMPOTENCY_MISMATCH` |
| `read_balance` | owner scope | granted, used, available, current month, grant summary |

Grant rules (SRS §23.5 line 1905): full included allowance in the first month (no prorate), no carry-over; included grant `expires_at` = the first instant of the next calendar month in `Asia/Ho_Chi_Minh`; units from the price version current when the grant is created; purchase grants have no expiry and are used after the current included grant, FIFO. Usage is never reversed (line 1907).

### 6.3 `SubscriptionAdminPortV1`

| Operation | Caller | Effect |
|---|---|---|
| `open_subscription` | `be1_bootstrap.py` when it creates an organization, and the seed (owner selection F-08); a Platform Admin organization-creation route is later work outside L2 | `ACTIVE` subscription on the current price version, first period 10 + 0, then backfill (§3.3). Idempotent per organization (one current subscription) |
| `schedule_downgrade` | School Manager downgrade (SRS §23.4) | Validates that the selection leaves active classes ≤ new capacity; writes one `subscription_events` row per selected class with a shared change group; at the effective time re-checks the active count, releases the selected slots and emits `CapacityClassSuspensionScheduledV1` through `billing.outbox`. If classes created after scheduling would exceed the new capacity, creation is refused from the effective time until the School Manager adjusts the selection |

### 6.4 `PaymentFulfilmentPortV1` — three commands called by the payment teammate (Q-L2-7, F-05)

| Command | Input | Effect | Dedupe |
|---|---|---|---|
| `activate_add_on_slots` | organization ref, capacity period ref, added slots, invoice ID, verified payment event ID | Increases `paid_extra_slots` of that period at once (§23.2 step 4). If the named period has already ended, the event is recorded but does not change current capacity (any refund is payment-side) | `subscription_events.payment_event_ref` unique |
| `issue_top_up_grant` | owner scope, units, invoice ID, provider event receipt ID | Appends a `PURCHASE` grant, no expiry | grant source event unique |
| `record_renewal_outcome` | organization ref, outcome (`SUCCESS`, `FAILURE`, `CANCELED_BY_PROVIDER`), new period start/end on success, invoice ID, verified payment event ID | Applies the lifecycle of section 5 | `subscription_events.payment_event_ref` unique |

The payment side verifies the provider event before calling. This interface must be agreed with the payment teammate before B-1 (columns of the payment tables) and B-4 (commands).

### 6.5 BE1 ports used by Billing

- `ActiveClassListPortV1`: active, non-suspended class refs of an organization (for backfill and reconcile).
- `QuotaScopeResolverPortV1`: resolves a verified actor to the owner scope for `GET /v1/video-quota` — Parent → `PARENT_ACCOUNT`; assigned Teacher → `ORGANIZATION` of the current assignment; organization billing admin → `ORGANIZATION`. Open: a Teacher assigned in several organizations (the SRS forbids a client-chosen owner ID), and which BE1 role is the "billing admin" (permission resolver OPEN under FR-T-02 / §31.10).

## 7. Public HTTP API in this lane (prefix per O-CONV)

| Method and path | Actor | Response |
|---|---|---|
| `GET /v1/video-quota` (§21.2 line 1678) | Parent owner, assigned Teacher, organization billing admin | granted / used / available and period, scope from the resolver |
| `GET /v1/organizations/{org_id}/subscription` (SRS §9.6 route group "Đọc/cập nhật gói, capacity…"; read part only) | School Manager of the organization | subscription status, capacity, used, available, `capacity_revision` |
| `POST .../organizations/{org_id}/classes` (existing; changed in B-2) | School Manager | 201 / 409 `CLASS_CAPACITY_REACHED` / 409 `SUBSCRIPTION_RESTRICTED` / 503 `BILLING_UNAVAILABLE` / 400 `INVALID_IDEMPOTENCY_KEY` |

## 8. Errors

SRS §9.8 envelope as fixed by the conventions slice. `CLASS_CAPACITY_REACHED`, `SUBSCRIPTION_RESTRICTED`, `VIDEO_QUOTA_EXCEEDED` (409, existing); `INVALID_IDEMPOTENCY_KEY` (400); `RESOURCE_NOT_FOUND` (404, out of scope); **`BILLING_UNAVAILABLE` (503, NEW)** with `retryable=true`, the `Retry-After` header and the envelope field `retry_after_seconds` when known. `NO_SUBSCRIPTION` maps to 409 `SUBSCRIPTION_RESTRICTED` (proposal, to be confirmed).

## 9. Idempotency by operation (SRS §21.4)

| Operation | Key scope | Replay | Mismatch |
|---|---|---|---|
| BE1 `POST .../classes` | principal + `CREATE_CLASS` + organization + key; BE1 receipt stores the original response (receipt design in B-2) | original 201 / error | 400 `INVALID_IDEMPOTENCY_KEY` |
| `reserve_class_slot` | organization + actor + operation + key (unique index) | the existing reservation's outcome, including `CONFIRMED` with its class ref | `IDEMPOTENCY_MISMATCH` → BE1 returns 400 |
| `confirm_class_slot` | reservation + class ref | same result | different class ref on a confirmed reservation → refused |
| `admit_video_request` | owner scope + key | same usage | `IDEMPOTENCY_MISMATCH` → 400 |
| `open_subscription` | organization (one current) | existing subscription | — |
| payment commands | verified payment event ID | no second effect | same event ID with different content → refused and logged |
| `schedule_downgrade` | change group key | same schedule | refused |

## 10. Slices (each with its own Task Approval, in the one-BE-slice-at-a-time queue)

1. **B-1 Foundation:** `billing` schema and migration (branch label `billing`; existing multi-head Alembic tests may need an update — check in the slice), payment tables created empty (columns agreed first), temporary price version, `open_subscription`, backfill and `reconcile_class_slots`, `read_capacity`, `ActiveClassListPortV1`, bootstrap and seed callers, unit and contract tests.
2. **B-2 Capacity admission:** `CapacityAdmissionPortV1` in BE1 class creation with the flow of §6.1, the BE1 idempotency receipt, the public mapping, `GET .../subscription` (read), a concurrency test on a disposable PostgreSQL database. Enabled only after every existing organization is backfilled.
3. **B-3 Video-quota ledger and read:** quota scopes, lazy monthly grants, usage, `VideoQuotaPortV1` with contract tests, `QuotaScopeResolverPortV1`, `GET /v1/video-quota`.
4. **B-4 Payment interface:** the three commands of §6.4, after agreement with the payment teammate.
5. **B-5 Lifecycle:** section 5 transitions, local auto-renewal, downgrade scheduling and the suspension event to BE1 (BE1 consumer included).
6. **Later:** connect `admit_video_request` to the Story saga when the video flow exists; a Platform Admin organization-creation route that calls `open_subscription`; class archive/reactivate in BE1 using `release_class_slot` and `REACTIVATE` reservations.

## 11. Acceptance criteria for the contract (before B-1 approval)

1. Every table, operation, state and code traces to the SRS, the register, D-066-63 or an owner answer; NEW items and interpretations are marked and listed for register/SRS updates.
2. Payment responsibility is limited to the three commands and the empty payment tables.
3. Concurrency: over-capacity and double usage are impossible per §4 and §6.1; the remaining failure mode is a temporary over-count, removed by reconcile.
4. Idempotency is defined for every state-changing operation (§9).
5. BE1 and Story never touch `billing.*`; Billing never touches theirs.
6. The owner choices are recorded as decision rows and the O-PAY agreement exists before B-1 is approved.

## 12. Disposition of the Draft 1 review

| ID | Disposition |
|---|---|
| F-01 | §6.1 flow: confirm before BE1 commit; reconcile; idempotent and late confirm |
| F-02 | Owner selection; §3.3; `reconcile_class_slots`; B-1; B-2 enable condition |
| F-03 | Owner selection; §3.1 with interpretation note and worked example |
| F-04 | §9 table; reservation unique key; BE1 receipt in B-2 |
| F-05 | Owner selection; §6.4 third command with inputs and dedupe |
| F-06 | Owner selection; §2 payment tables created empty; dedupe column; past-period rule |
| F-07 | §4 scope-level lock with `billing.quota_scopes`, replay first, database time |
| F-08 | Owner selections; §6.3 bootstrap and seed caller; temporary price version in §2 and B-1 |
| F-09 | Owner selection; §5 lifecycle table, grace capacity, local auto-renewal, restricted runs |
| F-10 | §3.4 |
| F-11 | §7: SRS route group `/v1/organizations/{org}/subscription` |
| F-12 | §8: header and `retry_after_seconds` |
| F-13 | §6.5 resolver port; open points named |
| F-14 | §2 NEW constraints marked; release and reactivation in §3.1, §10 item 6 |
| F-15 | §5 "Derived at read" |
| F-16 | §6.3 downgrade validation and re-check; `billing.outbox` |
| F-17 | §6.2 grant rules |
| F-18 | Header (not yet decision rows; O-PAY gate); §11 item 6 |
| F-19 | §10: callers, backfill, agreement gates, Alembic note |
| F-20 | §2 defaults |

## 13. Open items

- Restore from `RESTRICTED` (interpretation in §5); `NO_SUBSCRIPTION` mapping; reservation expiry value; temporary video units and placeholder prices.
- Register update for the NEW tables, columns and constraints; SRS updates for `BILLING_UNAVAILABLE` and the §23.1 wording.
- Agreement with the payment teammate on the payment table columns and the three commands.
- Teacher with several organizations, and the billing-admin role, for `GET /v1/video-quota`.
- Route prefix (O-CONV).
