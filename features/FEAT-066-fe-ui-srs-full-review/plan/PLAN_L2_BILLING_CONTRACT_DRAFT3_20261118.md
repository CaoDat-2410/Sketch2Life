# FEAT-066 L2 — Billing module contract (capacity and video quota, without payment) — Draft 3

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Contract plan only: no code, schema, migration, test, database or command is authorized. Not independently reviewed.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2 (lane L2 of `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, SHA-256 `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6`).
- **Predecessors, unchanged:** Draft 2 (22,639 bytes, `D5FBB6AA820447F3E94349A722163EB4C18149BC7A3A3AF162A99362338C7D9E`) and its review (Sonnet 5.5 high: NOT READY 0 P1 / 9 P2 / 12 P3; `evidence/notes/L2_BILLING_CONTRACT_DRAFT2_COLD_REVIEW_20261118.md`, 6,724 bytes, `39A8B76C5A789B78D67D355E9AF038758CB620812220A781BE385F41C9932D26`); Draft 1 (`3E8D243B...`) and its review (`A6D13BFD...`). Section 13 disposes of the Draft 2 findings.
- **Design change from Draft 2 (owner selection 2026-11-18, "BE1 tự đếm lớp", replacing Q-L2-2 "Port giữ chỗ"):** BE1 counts its own active classes inside its class-create transaction under a BE1 lock; Billing only answers the effective capacity with a version. This follows the adopted SRS literally: UC-06 main flow (line 1460) "Backend đọc sức chứa hiệu lực từ Billing → transaction tạo lớp khóa/kiểm tra slot còn trống → tạo lớp"; §21.2 line 1649 "Kiểm tra sức chứa hiệu lực trong transaction"; §9.7 line 842 "BE1 class state là projection đọc nhanh của capacity/suspension event hiệu lực; tạo lớp/run hỏi entitlement port có version". The SRS uses "reservation" only for AI Policy compute budget (FR-B-11 line 597, §9.7 line 837), never for class slots. All reservation, confirm, reconcile and backfill machinery of Draft 2 is removed.
- **Inputs:** owner answers Q-L2-1, Q-L2-3..9 (`plan/PLAN_L2_QUOTA_CONTRACT_QUESTIONS_DRAFT1_20261118.md`, 8,300 bytes, `779FDA62...`), the Draft 1 review answers recorded in Draft 2's header (counting rule, third payment command, empty payment tables, bootstrap and seed caller, seed price version, local auto-renewal), and the design change above. Adopted working SRS (701,157 bytes, `B9B1F42D...`, D-209); data table register `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` (171,609 bytes, `7CDFDBEC...`) Billing rows (lines 387–395, 457–465, note 10); D-066-63.
- **Status of owner choices:** selections in the coordinating session on 2026-11-18, **not yet decision rows**. **D-066-63 needs an owner amendment:** it asks the Billing owner to define "the exact receipt/reservation, expiry, recovery, and persistence contract"; under the UC-06 flow no receipt or reservation exists. Its other rules (Billing owns capacity; versioned, concurrency-safe admission; fail closed; no direct read of Billing storage; idempotency; 404/403) are kept and met as stated in §4.
- **Gate:** implementation starts only after the payment-interface agreement with the payment teammate (O-PAY) and after the owner choices are recorded. Payment work is not in this plan beyond the three commands of §7.4.
- **Source facts:** no Billing code, table or migration at `origin/dev` (`1c9148e8`); organizations are created only by `backend/src/sketch2life/infrastructure/persistence/be1_bootstrap.py`; no organization-creation route; no class archive route; `be1_classrooms.state` defaults to `active`; BE1 has a session command-receipt pattern but none for class creation; `settings.env` takes `local`, `test`, `staging`, `production`.

## 1. Module boundary

- New bounded module `billing` in the backend (schema `billing`, own domain, ports, adapters).
- BE1 and Story use Billing only through versioned ports; Billing uses BE1 only through BE1 ports (organization list, active class count, actor scope). No module reads another's tables; no cross-module SQL transaction.
- Owner scope: `ORGANIZATION` or `PARENT_ACCOUNT`; no Teacher-account scope.
- Class records, class state (active, suspended) and the count of active classes are BE1 facts. Capacity, subscription state and quota are Billing facts.

## 2. Tables (Alembic branch label `billing`)

| Table | Owner | Rules |
|---|---|---|
| `billing.price_versions` | this lane | Register columns. No price row is inserted by the migration. A local/test seed step (guarded by `env in {local, test}`) inserts one temporary version: `included_class_slots=10`, VND placeholders, temporary monthly video units (Q-L2-5), `approved_by='seed-local'` |
| `billing.organization_subscriptions` | this lane | Register columns + **NEW** `capacity_version` (bigint, monotonic). One current per organization. Defaults on open: `ACTIVE`, `MONTHLY`, `auto_renew=true`, provider refs and `billing_admin_ref` null |
| `billing.capacity_periods` | this lane | Register columns; defaults on open `included_slots=10`, `paid_extra_slots=0`, `prorated_amount=0`, `state=ACTIVE` |
| `billing.subscription_events` | this lane | Register columns (including `capacity_change_group_ref_optional`) + **NEW** `source_event_receipt_id` (nullable FK to `billing.provider_event_receipts`) + **NEW** `target_paid_extra_slots` (nullable, downgrade) + **NEW** `prorated_amount` (nullable, add-on). Uniques: (capacity change group, affected class) as in the register; **NEW** (subscription, source event receipt, event type) |
| `billing.quota_scopes` **NEW** | this lane | One row per owner scope; serialization point for video-quota admission |
| `billing.video_quota_grants` | this lane | Register columns; **NEW** unique (scope, month) for `MONTHLY_INCLUDED` |
| `billing.video_quota_usage` | this lane | Register columns + **NEW** `request_fingerprint`; unique (scope, request idempotency) |
| `billing.outbox` **NEW** | this lane | `outbox_id`, `event_type`, `event_version`, `aggregate_ref`, `payload` (refs only), `idempotency_key` unique, `created_at`, `published_at` |
| `billing.invoices`, `billing.payment_attempts`, `billing.provider_event_receipts` | **payment teammate** | Created empty by B-1 with register columns (column set agreed with the payment teammate first); only the payment side writes them |

BE1-side additions (in B-2, BE1-owned): a class-create command receipt (following the existing BE1 session command-receipt pattern) and a `suspended` value for `be1_classrooms.state` if not already allowed. All NEW items go to a data-table-register update approved with this plan.

## 3. Capacity rules

### 3.1 Counting

- **Capacity** (Billing) = `included_slots` + `paid_extra_slots` of the capacity period in effect (owner selection: "Slot = 10 + add-on").
- **Used** (BE1) = BE1 classes with state `active` (not `suspended`) in the organization, counted inside the create transaction.
- **Interpretation note:** SRS §23.1 line 1861 subtracts the selected suspended classes; this plan applies that subtraction to the set of active classes (suspended classes do not occupy a slot), not a second time to capacity. Recorded as an SRS wording clarification item.
- **Worked example:** 15 active classes on 10 + 5. Downgrade to 10 + 0 selecting 5 classes; at the effective time Billing's capacity becomes 10 and BE1 projects the 5 classes `suspended`: 10 active / 10 → full. If the projection reaches BE1 late, BE1 still counts 15 and refuses — the failure mode is a false refusal, never over-capacity.

### 3.2 Who may create (SRS §23.3)

Allowed in `ACTIVE`, `GRACE`, and `CANCEL_AT_PERIOD_END` within the paid period; refused in `RESTRICTED`, `CANCELED` and with no subscription. In `GRACE` the capacity is the last period's, extended to `grace_until`. While a downgrade is scheduled, admission uses the lower of current and scheduled capacity (so the selected classes always cover the excess).

### 3.3 Capacity version

`capacity_version` increases with every capacity-affecting change (open, add-on, downgrade scheduled or applied, state change). It is returned with every capacity answer together with `valid_until` (the next known boundary: period end, grace end or downgrade effective time).

## 4. Class creation (BE1, SRS UC-06; owner selection "BE1 tự đếm lớp")

1. **Receipt:** BE1 checks its class-create receipt for (principal, `CREATE_CLASS`, organization, idempotency key). Same key and fingerprint → the stored original 201 response. Same key, different fingerprint → 400 `INVALID_IDEMPOTENCY_KEY`. Errors are not stored; a retried request after an error is evaluated again.
2. **Capacity answer:** outside any BE1 transaction, BE1 calls `CapacityEntitlementPortV1.read_effective_capacity(organization)`, bounded by a call timeout. Timeout, error or indeterminate answer → 503 `BILLING_UNAVAILABLE`, no class created.
3. **Transaction:** BE1 opens its transaction with `lock_timeout` and `statement_timeout` set, locks the organization row (`SELECT ... FOR UPDATE` on `be1_organizations`), counts active classes, and compares with the answer: if the answer's `valid_until` has passed, it releases the lock and repeats step 2 once; if `can_create` is false → 409 `SUBSCRIPTION_RESTRICTED`; if count ≥ capacity → 409 `CLASS_CAPACITY_REACHED`; otherwise it inserts the class, writes the receipt and commits. A BE1 lock or statement timeout is not a Billing failure: it returns the conventions slice's generic retryable error, not `BILLING_UNAVAILABLE`.
4. **Concurrency:** all creates for one organization serialize on the organization row lock, so two concurrent creates at the last slot produce one 201 and one 409 (SRS UC-06 "các thao tác tạo lớp đồng thời được tuần tự hóa"; FR-T-03).
5. **D-066-63 mapping:** versioned → `capacity_version` and `valid_until`; concurrency-safe → BE1 lock over count and insert in one transaction (not an independent insert); fail closed → step 2; no direct read of Billing storage → port only.

Reactivating a suspended class (later, when BE1 has the command) runs the same steps.

## 5. Concurrency and time (Billing)

- Capacity and lifecycle commands for an organization lock its current subscription row.
- Video-quota admission ensures and locks the scope's `billing.quota_scopes` row (`INSERT ... ON CONFLICT DO NOTHING`, then `FOR UPDATE`); under the lock: replay check first, lazy monthly grant (unique (scope, month)), grant choice (current included first, then purchase FIFO), one usage row.
- Month boundaries and expiry use database time in `Asia/Ho_Chi_Minh`; timestamps stored in UTC.
- Every Billing call sets `lock_timeout` and `statement_timeout`; a timeout returns `UNAVAILABLE` to the caller.

## 6. Subscription lifecycle (SRS §23.3)

| From | Event | To |
|---|---|---|
| — | `open_subscription` | `ACTIVE`, first period |
| `ACTIVE` | renewal success | `ACTIVE`, next period |
| `ACTIVE` | renewal failure reported at time *f* | `GRACE`, `grace_until` = max(*f*, period end) + 7 days |
| `ACTIVE` | period end with no renewal outcome | `GRACE` from period end (**interpretation**: the SRS names only "Gia hạn thất bại"; treating a missing outcome as failure keeps "Hạn chế chỉ bắt đầu sau đủ 7 ngày ân hạn") |
| `GRACE` | renewal success | `ACTIVE`, next period |
| `GRACE` | `grace_until` passed | `RESTRICTED` |
| `ACTIVE` | auto-renew off (command later, §12) | `CANCEL_AT_PERIOD_END` |
| `CANCEL_AT_PERIOD_END` | period end | `RESTRICTED`, or `CANCELED` when the payment side reports `CANCELED_BY_PROVIDER` (§23.3 "RESTRICTED hoặc CANCELED theo provider") |
| `RESTRICTED` | renewal success | `ACTIVE`, next period (**interpretation**; the SRS lists restore within grace only) |

- **Next period's add-on slots** (N-06): the scheduled downgrade target if one is scheduled; otherwise the `paid_extra_slots` stated in the renewal outcome; in local/test auto-renewal, the previous period's value (**interpretation**).
- **Local and test only:** when `env in {local, test}`, a subscription rolls into a new period automatically at period end (owner selection). In `staging` and `production`, an organization with no renewal outcome goes to GRACE and then RESTRICTED; until the payment work exists, production use needs the payment side.
- **Settling time-based transitions** (N-07): `settle_due_transitions(organization)` persists due transitions (period end, grace expiry, downgrade effect, local roll-over) under the subscription lock with idempotent `subscription_events` rows and outbox entries. It runs (a) at the start of every Billing command and every `read_effective_capacity` call for that organization, and (b) in a periodic sweep over organizations with a due boundary. The sweep runner (existing worker, scheduled job or operator command) is an open owner choice; without it, BE1-visible effects (suspension projection) of organizations that make no calls are delayed. Public reads (`GET .../subscription`) derive the state without writing.
- **Runs:** in `RESTRICTED` and `CANCELED` (and with no subscription) new runs are refused for organization scope (§23.3; register line 397): `admit_video_request` returns `SUBSCRIPTION_RESTRICTED`. Parent-account quota is unaffected.

## 7. Ports (versioned)

### 7.1 `CapacityEntitlementPortV1` (Billing, used by BE1)

| Operation | Result |
|---|---|
| `read_effective_capacity(organization)` | `status`, `capacity`, `can_create` (status allows creation), `capacity_version`, `valid_until`; or `NO_SUBSCRIPTION` / `UNAVAILABLE`. Settles due transitions first |

### 7.2 `VideoQuotaPortV1` (Billing, used by Story when the video flow exists)

| Operation | Result |
|---|---|
| `admit_video_request(scope, request ref, key, fingerprint, contract version)` | `ACCEPTED` (usage, grant) / `QUOTA_EXCEEDED` / `SUBSCRIPTION_RESTRICTED` (organization scope, including no subscription — proposal) / `IDEMPOTENCY_MISMATCH` / `UNAVAILABLE`; same key returns the same usage |
| `read_balance(scope)` | granted, used, available, month; derived without writing (an absent current grant is shown with the units of the current price version) |

Grant rules (§23.5 line 1905): full included allowance in the first month, no prorate, no carry-over; `expires_at` = first instant of the next calendar month in `Asia/Ho_Chi_Minh`; units from the price version current at grant creation; purchase grants never expire and are used after the current included grant, FIFO; usage is never reversed.

### 7.3 `SubscriptionAdminPortV1` (Billing)

| Operation | Caller | Effect |
|---|---|---|
| `open_subscription(organization)` | `be1_bootstrap.py` (idempotently, including on a re-run for an organization that has none) and the seed | `ACTIVE` on the current price version, first period 10 + 0; idempotent per organization |
| `open_subscriptions_for_existing_organizations()` | operator command in B-1, re-runnable (N-08) | Lists organization refs through BE1 `OrganizationListPortV1` and opens a subscription for each that has none. Class creation with admission (B-2) is enabled only after this has run with zero remaining |
| `schedule_downgrade(organization, target_paid_extra_slots, selected class refs, change group ref)` | application use case for the School Manager (§23.4; route later, §12) | The use case first asks BE1 `ActiveClassCountPortV1` and refuses if active − selected > new capacity; Billing writes one event per selected class (shared change group, effective at next period) and the target count. At the effective time `settle_due_transitions` applies the new capacity and emits `CapacityClassSuspensionScheduledV1` (refs only) through `billing.outbox`; BE1 consumes it idempotently and sets the classes `suspended` |

### 7.4 `PaymentFulfilmentPortV1` — three commands called by the payment teammate

| Command | Input | Effect | Dedupe |
|---|---|---|---|
| `activate_add_on_slots` | organization, capacity period, added slots, `prorated_amount`, invoice ID, provider event receipt ID, content hash | Adds to the period's `paid_extra_slots` and `prorated_amount`; event `ADD_ON_ACTIVATED`. A period already ended: recorded, no capacity effect | unique (subscription, receipt, event type); same receipt with another content hash → refused |
| `issue_top_up_grant` | scope, units, invoice ID, provider event receipt ID, content hash | Appends a `PURCHASE` grant | grant source event unique |
| `record_renewal_outcome` | organization, outcome (`SUCCESS`, `FAILURE`, `CANCELED_BY_PROVIDER`), new period dates and `paid_extra_slots` on success, invoice ID, provider event receipt ID, content hash | §6 transitions | unique (subscription, receipt, event type) |

`subscription_events.event_type` values: `OPENED`, `PERIOD_STARTED`, `ADD_ON_ACTIVATED`, `RENEWAL_FAILED`, `GRACE_STARTED`, `RESTRICTED`, `RESTORED`, `CANCEL_SCHEDULED`, `CANCELED`, `DOWNGRADE_SCHEDULED`, `CLASS_SUSPENSION_SELECTED`, `DOWNGRADE_APPLIED`. The provider event receipt is written by the payment side before it calls. This interface and the payment table columns are agreed with the payment teammate before B-1.

### 7.5 BE1 ports used by Billing or the application

- `OrganizationListPortV1`: organization refs (for N-08).
- `ActiveClassCountPortV1`: active, non-suspended class count of an organization (for downgrade validation).
- `QuotaScopeResolverPortV1`: verified actor → owner scope for `GET /v1/video-quota`. Open: a Teacher assigned in several organizations (the SRS forbids a client-chosen owner ID); which BE1 role is the organization's billing admin.

## 8. Public HTTP API (prefix per O-CONV)

| Method and path | Actor | Response |
|---|---|---|
| `POST .../organizations/{org_id}/classes` (existing; changed in B-2) | School Manager | 201 / 409 `CLASS_CAPACITY_REACHED` / 409 `SUBSCRIPTION_RESTRICTED` / 503 `BILLING_UNAVAILABLE` / 400 `INVALID_IDEMPOTENCY_KEY` / 404 out of scope |
| `GET /v1/organizations/{org_id}/subscription` (SRS §9.6 group; read only) | School Manager — UC-06 precondition: School Manager "có thể đọc subscription/sức chứa" (line 1458); the SRS names "Admin billing" for checkout (line 1677), which is not this read | status, capacity, active class count (from BE1), available, `capacity_version` |
| `GET /v1/video-quota` (§21.2 line 1678) | Parent owner, assigned Teacher, organization billing admin | granted, used, available, period (scope from the resolver) |

## 9. Errors

SRS §9.8 envelope (fixed by the conventions slice). `CLASS_CAPACITY_REACHED`, `SUBSCRIPTION_RESTRICTED`, `VIDEO_QUOTA_EXCEEDED` (409); `INVALID_IDEMPOTENCY_KEY` (400); `RESOURCE_NOT_FOUND` (404); **`BILLING_UNAVAILABLE` (503, NEW)** with `retryable=true`, `Retry-After` and `retry_after_seconds` when known. `NO_SUBSCRIPTION` → 409 `SUBSCRIPTION_RESTRICTED` (proposal).

## 10. Idempotency (SRS §21.4)

| Operation | Key scope | Replay | Mismatch |
|---|---|---|---|
| BE1 class create | principal + `CREATE_CLASS` + organization + key (BE1 receipt) | original 201 only; errors re-evaluated | 400 `INVALID_IDEMPOTENCY_KEY` |
| `admit_video_request` | scope + key (usage unique, fingerprint stored) | same usage | `IDEMPOTENCY_MISMATCH` → 400 `INVALID_IDEMPOTENCY_KEY` |
| `open_subscription` | organization | existing subscription | — |
| payment commands | provider event receipt + event type | no second effect | other content hash → refused |
| `schedule_downgrade` | change group ref | same schedule | refused |

## 11. Slices (each with its own Task Approval; one BE slice at a time)

1. **B-1 Foundation:** schema and migration (branch label `billing`; check the existing multi-head Alembic tests), empty payment tables (agreed columns), `open_subscription`, `open_subscriptions_for_existing_organizations`, idempotent bootstrap call, `settle_due_transitions`, `read_effective_capacity`, `OrganizationListPortV1`, env-guarded seed price version, unit and contract tests.
2. **B-2 Class-create admission (BE1):** §4 flow, BE1 receipt, organization lock, timeouts, mapping, `GET .../subscription`, concurrency test on a disposable PostgreSQL database (two creates at the last slot; create racing a downgrade effect). Enabled only after B-1's existing-organization run reports zero remaining.
3. **B-3 Video quota:** quota scopes, lazy grants, usage, `VideoQuotaPortV1` with contract tests, resolver port, `GET /v1/video-quota`.
4. **B-4 Payment interface:** §7.4, after agreement.
5. **B-5 Lifecycle and downgrade:** §6 transitions, local roll-over, the sweep runner, `schedule_downgrade`, outbox publication, BE1 consumer of the suspension event, the `suspended` class state.
6. **Later:** Story saga connection; Platform Admin organization creation calling `open_subscription`; BE1 class archive and reactivation; auto-renew on/off and downgrade request routes.

## 12. Acceptance criteria and open items

Acceptance before B-1 approval: every element traces to the SRS, the register, D-066-63 (as amended) or an owner answer, with NEW items and interpretations marked; payment limited to three commands and empty tables; over-capacity impossible by §4 (BE1 lock) and double usage impossible by §5; idempotency per §10; no cross-module table access; owner choices recorded, D-066-63 amended, O-PAY agreed.

Open items: the sweep runner; the interpretations in §3.1 and §6 (grace start, restore from RESTRICTED, add-on carry-over in local roll-over); `NO_SUBSCRIPTION` mappings; temporary video units and placeholder prices; register update for NEW items; SRS §9.8 update for `BILLING_UNAVAILABLE` and §23.1 wording; Teacher in several organizations and the billing-admin role; auto-renew and downgrade routes; route prefix (O-CONV).

## 13. Disposition of the Draft 2 review

| ID | Disposition |
|---|---|
| N-01, N-02, N-03, N-09 | Removed with the reservation design; §4 has no cross-module confirm, reconcile or release |
| N-04 | §4 step 2 calls Billing outside the BE1 transaction; timeouts in §4 and §5 |
| N-05 | §6 grace start = max(failure time, period end) + 7 days; missing outcome marked interpretation |
| N-06 | §6 next-period add-on rule; `target_paid_extra_slots`; `paid_extra_slots` in the renewal outcome |
| N-07 | §6 `settle_due_transitions` with call-time and sweep triggers; sweep runner open |
| N-08 | §7.3 `open_subscriptions_for_existing_organizations`; idempotent bootstrap; B-2 enable condition |
| N-10 | §2 register column name and (group, class) unique |
| N-11 | §7.2 `read_balance` derives without writing |
| N-12 | §2 `request_fingerprint`, `source_event_receipt_id` FK, content hash, outbox columns; `BACKFILL` no longer exists |
| N-13 | §7.4 `prorated_amount`, event types, unique (subscription, receipt, event type) |
| N-14 | §11 item 6 and §12: auto-renew and downgrade routes later; `CANCELED_BY_PROVIDER` mapping in §6 |
| N-15 | §6 guard `env in {local, test}`; production behaviour stated |
| N-16 | §7.2 no-subscription result |
| N-17 | §10 original 201 only; code named |
| N-18 | §2 env-guarded seed price version, `approved_by` |
| N-19 | Not applicable (no reservations); D-066-63 amendment in the header |
| N-20 | §3.2 lower of current and scheduled capacity |
| N-21 | §8 actor justified by UC-06 line 1458 |
