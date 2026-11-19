# FEAT-066 L2 — Billing module contract (capacity and video quota, without payment) — Draft 8

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Contract plan only: no code, schema, migration, test, database or command is authorized.
- **Why Draft 8:** Draft 7 (49,498 bytes, `216B33D7B146E97DD2E0E99F13B034FC852A42E0933C9B30E520FF58DAB12BD0`) is the contract of record of D-066-66 and was closed without review. Since then five decisions changed its inputs: D-066-67 (the three D-066-63 sentences amended), D-066-68 and D-066-71 (CONV-1 conventions built on the local branch `feature/feat066-conv1`, commit `2dddc607`), D-066-73 (PAY-0 skeleton approved, with its list of Draft 7 edits in PAY-0 Draft 6 §6.1) and D-066-74 (Billing unfrozen and built in the owner's lane; payers; MoMo). **Draft 8 applies those decisions only**; the capacity design, the version stamp, the downgrade use case and the accepted residuals of D-066-66 are unchanged. §14 lists every change. Draft 8 is not yet reviewed.
- **Draft 7 status line, kept for history:** reviewed in six rounds (latest, round 6: NOT READY 0 P1 / 1 P2 / 7 P3); Draft 7 not independently reviewed, by owner instruction; its F6 fixes are coordinator text edits.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2 (lane L2 of `plan/PLAN_MANAGER_API_GAP_CLOSURE_DRAFT4_20261118.md`, SHA-256 `63710A9F7B56B8294E5A6AA168CB6BB791B05D2EA54023FAEEB68F2796F4EEE6`).
- **Predecessors, unchanged:** Draft 6 (44,622 bytes, `E8E2BFFC8052BD05713B5FE48E7F8789477C1CBD1757495E5B974DBE7572488B`) and its review (Sonnet 5.5 high, owner-granted round 6: NOT READY 0 P1 / 1 P2 / 7 P3; `evidence/notes/L2_BILLING_CONTRACT_DRAFT6_COLD_REVIEW_20261118.md`, 6,456 bytes, `E8DAF3488DD2DB9183A2F39A97A8EC5E07F4DB0537E56098ED77150AA72BECF9`); Draft 5 (36,181 bytes, `9BB4B3959C70DF5844C1E5C9737C9ED6C0A8964C912457B36EE86BDCE39A661A`) and its review (Sonnet 5.5 high, round 5 of 5: NOT READY 0 P1 / 1 P2 / 5 P3; `evidence/notes/L2_BILLING_CONTRACT_DRAFT5_COLD_REVIEW_20261118.md`, 6,886 bytes, `9B0437766B69B2B5269954BEA8B7201DA423C0A20EF87A6E5E26C951FECDBB56`); Draft 4 (30,568 bytes, `D8D2B505156ED1915E99CD19FA3614841ECF02CF34A6114EA49C7FDC6CA718DC`) and its review (Sonnet 5.5 high: NOT READY 0 P1 / 1 P2 / 7 P3; `evidence/notes/L2_BILLING_CONTRACT_DRAFT4_COLD_REVIEW_20261118.md`, 5,226 bytes, `765E84D10E002E81D51125D49985821DB432D6FBA4D5928183BBFA03D4C5C64F`); Draft 3 (23,167 bytes, `DE69DCEE453CF0044022FBA968E8229EB2E1CE5E88CC90123E7225661D94530B`) and its review (Sonnet 5.5 high: NOT READY 0 P1 / 3 P2 / 9 P3; `evidence/notes/L2_BILLING_CONTRACT_DRAFT3_COLD_REVIEW_20261118.md`, 5,964 bytes, `768D465FDD34AA24963D32003B3AF303276124CDBD9FAAC74083756E96AEB864`); Draft 2 (22,639 bytes, `D5FBB6AA820447F3E94349A722163EB4C18149BC7A3A3AF162A99362338C7D9E`) and its review (Sonnet 5.5 high: NOT READY 0 P1 / 9 P2 / 12 P3; `evidence/notes/L2_BILLING_CONTRACT_DRAFT2_COLD_REVIEW_20261118.md`, 6,724 bytes, `39A8B76C5A789B78D67D355E9AF038758CB620812220A781BE385F41C9932D26`); Draft 1 (`3E8D243B...`) and its review (`A6D13BFD...`). Section 13 disposes of the Draft 2 to Draft 5 findings. **Review limit:** Draft 5 was round 5 of 5 (D-171 item 11) and its P2 repeated the create-against-downgrade class; the owner granted one extra round on 2026-11-18 ("Draft 6, review thêm"). **Draft 6 change:** the indeterminate downgrade keeps the BE1 lock until the unknown stamp is committed; every capacity-version bump is published to BE1; one re-read budget; separate Billing pool (§4, §7.3, §7.6). **Draft 7 change:** Billing timeouts strictly inside BE1's call timeout and the Billing session closed before the unknown stamp is written (F6-01); the residual bound restated; the stamp never lowered; downgrade replay by change group ref; audit sink, lock-waiter limiter and outbox keys stated (F6-02 to F6-07). The residuals of §4 step 5 (d) and (f) still need the owner's recorded acceptance (§12). **Draft 5 change (owner selection 2026-11-18, "dấu version"):** a BE1-side capacity version stamp closes the create-against-downgrade window (§4, §7.3).
- **Design change from Draft 2 (owner selection 2026-11-18, "BE1 tự đếm lớp", replacing Q-L2-2 "Port giữ chỗ"):** BE1 counts its own active classes inside its class-create transaction under a BE1 lock; Billing only answers the effective capacity with a version. This follows the adopted SRS literally: UC-06 main flow (line 1460) "Backend đọc sức chứa hiệu lực từ Billing → transaction tạo lớp khóa/kiểm tra slot còn trống → tạo lớp"; §21.2 line 1649 "Kiểm tra sức chứa hiệu lực trong transaction"; §9.7 line 842 "BE1 class state là projection đọc nhanh của capacity/suspension event hiệu lực; tạo lớp/run hỏi entitlement port có version". The SRS uses "reservation" only for AI Policy compute budget (FR-B-11 line 597, §9.7 line 837), never for class slots. All reservation, confirm, reconcile and backfill machinery of Draft 2 is removed.
- **Inputs:** owner answers Q-L2-1, Q-L2-3..9 (`plan/PLAN_L2_QUOTA_CONTRACT_QUESTIONS_DRAFT1_20261118.md`, 8,300 bytes, `779FDA62...`), the Draft 1 review answers recorded in Draft 2's header (counting rule, third payment command, empty payment tables, bootstrap and seed caller, seed price version, local auto-renewal), and the design change above. Adopted working SRS (701,157 bytes, `B9B1F42D...`, D-209); data table register `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md` (171,609 bytes, `7CDFDBEC...`) Billing rows (lines 387–395, 457–465, note 10); D-066-63.
- **Status of owner choices (Draft 8):** recorded as decision rows: D-066-66 (design, residuals (d) and (f) accepted, audit sink), D-066-67 (D-066-63 amended), D-066-68 and D-066-71 (conventions), D-066-73 (PAY-0), D-066-74 (Billing ownership, payers, MoMo). The Draft 7 text that follows in this bullet is kept for history. **Residual window:** capacity can change between Billing's answer and BE1's commit; §4 closes it with `valid_until` for time boundaries and the BE1 capacity version stamp for non-boundary decreases (a downgrade being scheduled; an immediate cancellation reported by the provider), with the accepted residuals stated in §4 step 5 (d) and (f). Kept unchanged: Billing owns capacity; fail closed; no direct read of Billing storage; idempotency. The §9.8 404/403 distinction is **built by CONV-1** (D-066-68 C-D4, D-066-71): uniform 404 `RESOURCE_NOT_FOUND` out of scope, 403 `ACTION_NOT_ALLOWED` for an in-scope refusal. The public code for Billing unavailable is 503 `BILLING_UNAVAILABLE` (D-066-66, Q-L2-3). SRS §11.1 item 10 (line 1027): "Thay đổi capacity/tạo lớp chạy transaction với lock hoặc serializable enforcement".
- **Payers and provider (D-066-74):** the School Manager pays for the school (subscription, capacity add-on, school video-quota top-up); the Parent pays for the Parent account (video-quota top-up). Teachers draw from the school capacity and the school quota of their occurrence; there is no Teacher-account pool (SRS 168, BR-38, FR-B-10). The V1 payment provider is MoMo only, a narrowing of SRS FR-B-02 and BR-28; the Billing ports stay provider-neutral.
- **Gate:** each slice of §11 needs its own Task Approval and an owner word to start. B-4 also needs the payment teammate's review of §7.4 and §7.7, which is the port review gate of PAY-0 (PAY-0 Draft 6 §2). Payment work is not in this plan beyond the Billing side of §7.4 and §7.7.
- **Source facts:** no Billing code, table or migration at `origin/dev` (`1c9148e8`) or at the CONV-1 commit `2dddc607`; organizations are created only by `backend/src/sketch2life/infrastructure/persistence/be1_bootstrap.py`; no organization-creation route; no class archive route; `be1_classrooms.state` defaults to `active`; BE1 has a session command-receipt pattern but none for class creation; `settings.env` takes `local`, `test`, `staging`, `production`.

## 1. Module boundary

- New bounded module `billing` in the backend (schema `billing`, own domain, ports, adapters). The owner's lane builds Billing core (D-066-65, D-066-74); the payment teammate builds payment on top (D-066-65 as amended by D-066-73); "this lane" in §2 means the owner's lane.
- **Payment tables in the same module:** `billing.invoices`, `billing.payment_attempts` and `billing.provider_event_receipts` live in schema `billing` (SRS 1012) and are created by PAY-0a (D-066-73 PD-2a). The fulfilment call of §7.4 runs in one database session shared with the payment intake (D-066-73 PD-5, option A); this is a transaction **inside** the `billing` module and does not break the no-cross-module rule below.
- **Lock order invariant (F-04):** a BE1 organization lock is always taken before a Billing subscription lock; Billing never calls a BE1 port that takes a BE1 lock inside a Billing command; the class-create path never holds a Billing lock.
- BE1 and Story use Billing only through versioned ports; Billing uses BE1 only through BE1 ports (organization list, active class count, actor scope). No module reads another's tables; no cross-module SQL transaction.
- Owner scope: `ORGANIZATION` or `PARENT_ACCOUNT`; no Teacher-account scope.
- Class records, class state (active, suspended) and the count of active classes are BE1 facts. Capacity, subscription state and quota are Billing facts.

## 2. Tables (Alembic branch label `billing`)

| Table | Owner | Rules |
|---|---|---|
| `billing.price_versions` | this lane (content: a commercial setting approved by the owner outside local/test) | Register columns. No price row is inserted by the migration. Local/test: a seed step guarded by `env in {local, test}` inserts one temporary version (`included_class_slots=10`, VND placeholders, temporary monthly video units of Q-L2-5, `approved_by='seed-local'`). Staging/production: the first approved price version is a commercial setting (SRS FR-B-01: prices "chưa chốt trong SRS"); since D-066-74 the owner's lane owns Billing, so the owner approves it (**interpretation** of D-066-74; Draft 7 named the payment teammate); until it exists, `open_subscription` refuses with `NO_PRICE_VERSION` and B-2 is not enabled in that environment |
| `billing.organization_subscriptions` | this lane | Register columns + **NEW** `capacity_version` (bigint, monotonic). One current per organization. Defaults on open: `ACTIVE`, `MONTHLY`, `auto_renew=true`, provider refs and `billing_admin_ref` null |
| `billing.capacity_periods` | this lane | Register columns; defaults on open `included_slots=10`, `paid_extra_slots=0`, `prorated_amount=0`, `state=ACTIVE` |
| `billing.subscription_events` | this lane | Register columns (including `capacity_change_group_ref_optional`) + **NEW** `source_event_receipt_id` (nullable FK to `billing.provider_event_receipts`) + **NEW** `target_paid_extra_slots` (nullable, downgrade) + **NEW** `prorated_amount` (nullable, add-on). + **NEW** `content_hash` (nullable; payment commands). Uniques: (capacity change group, affected class) — the register states "unique event/change-group"; this per-class reading is an interpretation, marked NEW; **NEW** (subscription, source event receipt, event type) |
| `billing.quota_scopes` **NEW** | this lane | One row per owner scope; serialization point for video-quota admission |
| `billing.video_quota_grants` | this lane | Register columns; **NEW** unique (scope, month) for `MONTHLY_INCLUDED` |
| `billing.video_quota_usage` | this lane | Register columns + **NEW** `request_fingerprint`; unique (scope, request idempotency) |
| `billing.outbox` **NEW** | this lane | `outbox_id`, `event_type`, `event_version`, `aggregate_ref`, `payload` (refs only), `idempotency_key` unique, `created_at`, `published_at` |
| `billing.invoices`, `billing.payment_attempts`, `billing.provider_event_receipts` | **payment side** | **Created by PAY-0a** (D-066-73 PD-2a), not by B-1, with the register columns plus the NEW columns of PD-2c and PD-2d and the one-open-checkout partial unique index of PD-2e; subscription references are soft refs. **B-1 adds the subscription foreign keys** on the same Alembic branch label. Only the payment side writes these tables |

BE1-side additions (BE1-owned): **NEW** column `be1_organizations.capacity_version_seen` (bigint, nullable; null = unknown; update rules in §4 step 7) in B-2; an operator audit sink for the downgrade audit events of §7.3 in B-5 — the core audit records of migration `20261014_0001` if their columns fit (NOT VERIFIED), otherwise a **NEW** BE1 table, unique per (event type, change group ref); a class-create command receipt in B-2 (following the existing BE1 session command-receipt pattern); in B-5 the `suspended` value for `be1_classrooms.state` (the column has no check constraint, so the value is storable) **plus** the read and write changes it needs: class list, class read and profile reads currently filter `state == "active"` and would hide a suspended class; they must show it read-only, and writes to it must be refused. All NEW items go to a data-table-register update approved with this plan.

## 3. Capacity rules

### 3.1 Counting

- **Capacity** (Billing) = `included_slots` + `paid_extra_slots` of the capacity period in effect (owner selection: "Slot = 10 + add-on").
- **Used** (BE1) = BE1 classes with state `active` (not `suspended`) in the organization, counted inside the create transaction.
- **Interpretation note:** SRS §23.1 line 1861 subtracts the selected suspended classes; this plan applies that subtraction to the set of active classes (suspended classes do not occupy a slot), not a second time to capacity. Recorded as an SRS wording clarification item.
- **Worked example:** 15 active classes on 10 + 5. Downgrade to 10 + 0 selecting 5 classes; at the effective time Billing's capacity becomes 10 and BE1 projects the 5 classes `suspended`: 10 active / 10 → full. If the projection reaches BE1 late, BE1 still counts 15 and refuses — the failure mode is a false refusal, never over-capacity.

### 3.2 Who may create (SRS §23.3)

Allowed in `ACTIVE`, `GRACE`, and `CANCEL_AT_PERIOD_END` within the paid period; refused in `RESTRICTED`, `CANCELED` and with no subscription. In `GRACE` the capacity is the last period's, extended to `grace_until`. While a downgrade is scheduled, Billing returns as **admission capacity** min(current capacity, scheduled capacity + number of selected classes): the selected classes are still active until the effective time and are counted by BE1, so this keeps every create consistent with the new capacity once they are suspended (D3-08). Example: 12 active, 2 selected, new capacity 10 → admission capacity 12; a 13th class is refused.

### 3.3 Capacity version

`capacity_version` increases with every capacity-affecting change (open, add-on, downgrade scheduled or applied, state change); every increase writes one `CapacityVersionChangedV1` outbox row in the same Billing transaction (§7.6). It is returned with every capacity answer together with `valid_until` (the next known boundary: period end, grace end or downgrade effective time). For `RESTRICTED`, `CANCELED` and no-subscription answers `valid_until` is null and `can_create` is false.

## 4. Class creation (BE1, SRS UC-06; owner selections "BE1 tự đếm lớp" and "dấu version")

1. **Authorization and receipt:** BE1 authorizes the School Manager for the organization first, with the CONV-1 guard (D-066-68 C-D4, D-066-71): 404 `RESOURCE_NOT_FOUND` when the organization is out of the caller's scope, 403 `ACTION_NOT_ALLOWED` for an in-scope caller without the School Manager role. A missing or malformed `Idempotency-Key` is refused by the CONV-1 rule (C-D5) as 400 `INVALID_REQUEST` with a field error `Idempotency-Key` / `REQUIRED` or `INVALID_FORMAT`; this is a **breaking change** for current callers and tests of the route, which send no key today (the FE side is MGR-9 M9-A). BE1 then checks its class-create receipt for (principal, `CREATE_CLASS`, organization, key): same key and fingerprint → the stored original 201; same key, different fingerprint → 400 `INVALID_IDEMPOTENCY_KEY`. Errors are not stored.
2. **Capacity answer, outside any BE1 transaction:** BE1 ends the request's existing session transaction and calls `CapacityEntitlementPortV1.read_effective_capacity(organization)` with a call timeout. Timeout, error or indeterminate answer → 503 `BILLING_UNAVAILABLE`, no class created. The answer carries admission capacity, `can_create`, `capacity_version` and `valid_until`.
3. **Transaction:** BE1 starts a new transaction with `SET TRANSACTION ISOLATION LEVEL READ COMMITTED` (set explicitly), `lock_timeout` and `statement_timeout`, and takes `SELECT ... FOR NO KEY UPDATE` on the organization row. Under the lock, in this order:
   - the organization must exist and be `active` (otherwise refused as not found);
   - the receipt is checked again (a concurrent same-key request that committed first is replayed);
   - **version stamp:** read `capacity_version_seen`. If it is null (unknown), BE1 calls `read_effective_capacity` once while holding the lock (bounded timeout; timeout → rollback and 503), stores the returned `capacity_version` in the column (rule 7a) and uses that answer. Otherwise, if the answer's `capacity_version` < `capacity_version_seen`, the answer is stale;
   - **time:** if `valid_until` is not null and is earlier than `clock_timestamp()` (not `now()`, which is the transaction start), the answer is stale. A null `valid_until` (terminal states, §3.3) counts as not passed;
   - **re-read budget (F5-06):** each request gets **at most one re-read in total**. A stale answer (stamp or time) when no re-read has been used → BE1 rolls back, repeats step 2 once and re-enters step 3; a stale answer when the re-read is used, or a null stamp met after a re-read, → 503 `BILLING_UNAVAILABLE`. The null-stamp call under the lock counts as the re-read;
   - if `can_create` is false → 409 `SUBSCRIPTION_RESTRICTED`;
   - count active classes; if count ≥ admission capacity → 409 `CLASS_CAPACITY_REACHED`;
   - otherwise insert the class, write the receipt, commit.
   A BE1 lock or statement timeout is not a Billing failure: it returns a retryable 503 in the CONV-1 envelope; its public code is fixed in the B-2 Task Approval.
4. **Concurrency:** all creates of one organization serialize on the organization row lock; two creates at the last slot give one 201 and one 409 (UC-06; FR-T-03; SRS §11.1 item 10). The downgrade use case takes the same lock and releases it only after a stamp that is at least the scheduled version, or null, is committed (§7.3), so a create holding an answer from before the schedule sees a newer or unknown stamp and re-reads.
5. **Residual window, by cause:** (a) time boundaries (period end, grace end, downgrade effective time) → `valid_until`; (b) add-on activation → capacity grows, safe; (c) a downgrade being scheduled → stamp committed under the shared lock (§7.3), including the timeout and lost-response cases; (d) an immediate `CANCELED_BY_PROVIDER` (§6) → its version bump reaches BE1 through `CapacityVersionChangedV1` (§7.6); until the consumer has raised the stamp, a create may still be admitted with a stale `can_create` — an extra class in a cancelled subscription, not an over-capacity class; **accepted**, §12; (e) a late suspension projection → false refusals only; (f) **BE1 process death, a failure of BE1's own commit, or a Billing commit that completes after BE1 gave up despite the timeout ordering (for example a driver-level cancellation whose outcome is unknown)** → the stamp does not reflect the schedule; until the `CapacityVersionChangedV1` for that schedule is consumed, **each** create holding a pre-schedule answer can be admitted (at most old admission capacity − count of them), so at the effective time the organization can exceed the new capacity by that number (F6-02); **accepted residual**, made visible by the effective-time check of §7.3 step 6, resolved by the operator, and listed in §12.
6. **Connections (F5-04):** the port call in step 2 happens while BE1 holds no transaction; the rare call in step 3 (null stamp) holds one BE1 connection for one bounded call. **Billing uses its own engine and connection pool** (same PostgreSQL server, schema `billing`), so a lock holder that calls Billing never waits for a connection held by creates queued on the organization lock; B-1 fixes the pool size. **One exception (D-066-73 PD-5):** the Billing side of `PaymentFulfilmentPortV1` (§7.4) runs in the caller's session, the payment intake's, so the receipt and the fulfilment commit together; that call holds no BE1 lock and is not on the class-create path. One per-process limiter, below the BE1 pool size, covers **every** organization-lock waiter (class creates from B-2; downgrades and the B-5 event consumers when they exist), so waiters on one organization lock cannot exhaust the BE1 pool.
7. **Stamp update rules (F5-02)** — `capacity_version_seen` is only ever written under the organization lock:
   a. **Fresh read under the lock** (create null-stamp path; downgrade success; downgrade replay through `read_scheduled_downgrade`): if the column is null, set it to the returned version; otherwise set max(current, returned) — **a non-null stamp is never lowered** (F6-03). Replacing null is safe because, with the timeout ordering of §7.3 step 4, every Billing call of an earlier lock holder has committed or rolled back before that holder released the lock; a later provider bump is residual (d).
   b. **Event consumer** (§7.6): `SET capacity_version_seen = event version WHERE capacity_version_seen IS NOT NULL AND capacity_version_seen < event version`. It never turns null into a value and never lowers the stamp. SQL `GREATEST` is not used (it ignores null).
   c. **Indeterminate downgrade:** set the column to null (§7.3 step 4).
   d. Nothing else writes the column.
8. **Clock assumption (F5-06):** `valid_until` is computed by Billing on the same PostgreSQL server that BE1 reads `clock_timestamp()` from (one database, two schemas); if Billing ever moves to another server, a skew margin is required (open, §12).

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
- **Settle idempotency:** settle-generated events carry no payment receipt; they are made idempotent by the subscription row lock plus a state guard (a transition is written only if the stored state is still the source state) and by the outbox `idempotency_key` (rule in §7.6).
- **Further rules (D3-11):** `CANCELED_BY_PROVIDER` reported while `ACTIVE` or `GRACE` → `CANCELED` at once (interpretation: the provider ended the agreement), bumps `capacity_version` (which writes `CapacityVersionChangedV1`, §7.6; BE1's stamp, §4 step 5d); the payment command that reports it is enabled only together with or after B-5 (the consumer); a downgrade scheduled for a period end at which renewal fails is applied at that boundary as scheduled (the new capacity also governs the grace period); a failure reported before period end starts grace at period end (max rule). Reminders and notifications of §23.3/§23.4 and FR-B-08 are excluded from this lane (notifications are not in the owner's lanes).
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

### 7.3 `SubscriptionAdminPortV1` (Billing) and the downgrade use case

| Operation | Caller | Effect |
|---|---|---|
| `open_subscription(organization)` | `be1_bootstrap.py` right after it creates an organization, and the seed | `ACTIVE` on the current price version, first period 10 + 0; idempotent per organization. `be1_bootstrap.py` is single-shot (a new organization each run; it aborts if the identity exists), so if `open_subscription` fails after the organization commit, bootstrap reports a clear operator error naming the organization, and the repair is `open_subscriptions_for_existing_organizations()`. Outside local/test it refuses with `NO_PRICE_VERSION` until the payment teammate has supplied an approved price version |
| `open_subscriptions_for_existing_organizations()` | operator command (B-1), re-runnable | Lists organization refs through BE1 `OrganizationListPortV1` and opens a subscription for each that has none; reports the remaining count. B-2 is enabled in an environment only when it reports zero remaining |
| `schedule_downgrade(organization, target_paid_extra_slots, selected class refs, change group ref)` | the downgrade use case below | Records the target count and one event per selected class (shared change group), effective at the next period boundary; bumps and returns `capacity_version` (writing `CapacityVersionChangedV1`, §7.6). Idempotent per change group ref: a retry with the same ref returns the same schedule and version without re-validating. While a schedule with another ref is `SCHEDULED`, it refuses with `ALREADY_SCHEDULED`. Billing applies its own `lock_timeout` and `statement_timeout`, whose sum is strictly below BE1's call timeout (§7.3 step 4) |
| `read_scheduled_downgrade(organization, change group ref)` **NEW** | the downgrade use case below | The downgrade with that ref in state `SCHEDULED` or `APPLIED`, else the organization's current `SCHEDULED` downgrade (another ref), else none: change group ref, state, target capacity, selected class refs, `capacity_version`; read-only |

**Downgrade use case (D3-01, F-01, F5-01; SRS §23.4, §11.1 item 10), inside BE1:**

1. BE1 opens a transaction (READ COMMITTED, `lock_timeout`, `statement_timeout`) and takes `FOR NO KEY UPDATE` on the organization row — the same lock as class creation. The change group ref is **derived from the client's idempotency key** (organization, principal, key), so a retry converges on the same schedule.
2. **Retry of an existing schedule first:** BE1 calls `read_scheduled_downgrade`. If the downgrade with this change group ref is `APPLIED`, BE1 applies rule 7a with its `capacity_version` and returns the stored outcome without re-validation (F6-06). If another ref is `SCHEDULED`, BE1 returns 409 `DOWNGRADE_ALREADY_SCHEDULED` (**NEW, proposal**; replacing a schedule is the open item below). If the downgrade with this ref is `SCHEDULED` (an earlier attempt committed in Billing), BE1 applies rule 7a with its `capacity_version` and then checks it against BE1's current count: if every selected class is active and active − selected ≤ target capacity, it commits and returns the stored outcome; **otherwise** (classes were created while BE1 did not know of the schedule, §4 step 5f) it commits the stamp, writes an operator-visible audit event `DOWNGRADE_SCHEDULE_OVER_CAPACITY` (organization, change group ref, surplus; written once per change group ref, repeats are no-ops) and returns 409 `DOWNGRADE_SELECTION_INSUFFICIENT` (**NEW, proposal**, naming per O-CONV) stating that the schedule exists and more classes must be selected — never a silent refusal. Replacing the selection is the open replace/cancel item below.
3. **New schedule:** BE1 counts its active classes directly (BE1 data; no port), checks that every selected class is active in the organization and that active − selected ≤ new capacity; otherwise 409 `DOWNGRADE_SELECTION_INSUFFICIENT` and nothing is scheduled.
4. Holding the lock, BE1 calls `schedule_downgrade`, bounded by a call timeout:
   - **Success:** set the stamp to the returned `capacity_version` (rule 7a) and commit.
   - **Billing refused** (validation): roll back; nothing is scheduled.
   - **Timeout ordering (F6-01):** `schedule_downgrade` runs in one Billing transaction on Billing's own connection, with `lock_timeout` + `statement_timeout` strictly below BE1's call timeout; BE1 treats the call as finished only after it has returned or raised **and** the Billing session used for it has been closed (transaction ended, connection returned). Then Billing has either committed or rolled back before BE1 writes anything; if BE1 cannot confirm that, the case is residual (f).
   - **Timeout, lost response or any answer that does not prove Billing did not commit:** after the Billing session is closed, BE1 **does not roll back**; in the same transaction, still holding the lock, it sets `capacity_version_seen = NULL` (rule 7c) and commits, then returns 503 `BILLING_UNAVAILABLE` (retryable; retry with the same key, which takes step 2). The lock is released only with null in place, so no create that waited on the lock can use a pre-schedule answer (F5-01 a).
   - **BE1's own commit fails, or the process dies, after Billing committed:** nothing is written in BE1; this is the accepted residual of §4 step 5f. It closes when BE1 consumes the schedule's `CapacityVersionChangedV1` or when a retry takes step 2.
5. Creates waiting on the lock then see a stamp that is at least the scheduled version, or null, and re-read Billing before admitting.
6. **Effective time:** `settle_due_transitions` applies the new capacity and writes `CapacityClassSuspensionScheduledV1` (refs only) to `billing.outbox`; BE1 consumes it idempotently under the organization lock, sets the selected classes `suspended`, then counts the remaining active classes; if they exceed the event's `new_capacity` (only possible through the residual of §4 step 5f), it writes the audit event `CAPACITY_OVER_LIMIT_AFTER_DOWNGRADE` (once per change group ref) for the operator, who resolves the surplus. No class is suspended automatically beyond the selection (no selection rule exists in the SRS); creates stay refused because count ≥ capacity.

The statement "a schedule that BE1 does not know about only makes admission stricter" holds only for creates that read Billing **after** the schedule committed; a create holding an earlier answer is protected by the stamp (steps 4 and 5) or falls under the residual of §4 step 5f. Holding the BE1 organization lock across one bounded Billing call is accepted for downgrades (rare); with Billing's own pool (§4 step 6) it holds one BE1 connection during that call. **Open:** replacing or cancelling a scheduled downgrade (for example after an add-on purchase, or to answer `DOWNGRADE_SELECTION_INSUFFICIENT`), and whether an add-on bought after scheduling survives into the next period.

### 7.4 `PaymentFulfilmentPortV1` — three commands called by the payment teammate

| Command | Input | Effect | Dedupe |
|---|---|---|---|
| `activate_add_on_slots` | organization, capacity period, added slots, `prorated_amount`, invoice ID, provider event receipt ID, content hash | Adds to the period's `paid_extra_slots` and `prorated_amount`; event `ADD_ON_ACTIVATED`. A period already ended: recorded, no capacity effect | unique (subscription, receipt, event type); same receipt with another content hash → refused |
| `issue_top_up_grant` | scope, units, invoice ID, provider event receipt ID, content hash | Appends a `PURCHASE` grant | grant source event unique |
| `record_renewal_outcome` | organization, outcome (`SUCCESS`, `FAILURE`, `CANCELED_BY_PROVIDER`), new period dates and `paid_extra_slots` on success, invoice ID, provider event receipt ID, content hash | §6 transitions | unique (subscription, receipt, event type) |

`subscription_events.event_type` values: `OPENED`, `PERIOD_STARTED`, `ADD_ON_ACTIVATED`, `RENEWAL_FAILED`, `GRACE_STARTED`, `RESTRICTED`, `RESTORED`, `CANCEL_SCHEDULED`, `CANCELED`, `DOWNGRADE_SCHEDULED`, `CLASS_SUSPENSION_SELECTED`, `DOWNGRADE_APPLIED`.

**Additions from D-066-73 (PAY-0 Draft 6 §3.3 and §6.1):**
- **Session:** each command accepts the caller's database session and does not commit it; the payment intake writes the provider event receipt in the **same transaction** as the call (option A), not before it. Lock order inside that transaction: receipt insert, the organization checkout advisory lock (payment side), payment attempt, invoice, then the Billing subscription lock; no BE1 lock is held.
- **Invoice-level idempotency (NEW):** every command is also keyed by `invoice_id`, so one invoice is fulfilled at most once even when two receipts (callback and reconciliation) report the same payment.
- **`content_hash`** = SHA-256 of the canonical JSON of the command's other inputs.
- **Result `FulfilmentResultV1` (NEW)**, returned by every command: `APPLIED`; `ALREADY_APPLIED` (same invoice already fulfilled); `RECORDED_NO_EFFECT` (for example a period already ended); `REFUSED(code)` (deterministic: another content hash for the same receipt, no subscription); `UNAVAILABLE` (transient: lock or statement timeout). The payment intake maps them as PAY-0 Draft 6 §3.3 states.
- **Recurring renewal via MoMo** (D-066-74): `record_renewal_outcome` is fed by the MoMo Subscription adapter (PAY-2); VNPAY recurring is out of scope.

This interface is reviewed by the payment teammate before B-4 (the PAY-0 port review gate).

### 7.5 BE1 ports used by Billing or the application

- `OrganizationListPortV1`: organization refs (for N-08).
- `ActiveClassCountPortV1`: not needed in this plan — the downgrade use case runs inside BE1 and counts BE1 data directly (§7.3); kept only as a candidate for read models.
- `QuotaScopeResolverPortV1`: verified actor → owner scope for the video-quota read (§8). The organization's billing admin is its **School Manager** (D-066-74; SRS 1677 "Admin billing"). Open: a Teacher assigned in several organizations (the SRS forbids a client-chosen owner ID).

### 7.6 Events from Billing to BE1 (F5-03)

| Event | Written | Payload (refs only) | Consumer (BE1, B-5) |
|---|---|---|---|
| `CapacityVersionChangedV1` **NEW** | in the same Billing transaction as every `capacity_version` increase (§3.3) | `organization_ref`, `capacity_version`, `cause` (`OPENED`, `ADD_ON_ACTIVATED`, `DOWNGRADE_SCHEDULED`, `DOWNGRADE_APPLIED`, `STATE_CHANGED`, `CANCELED_BY_PROVIDER`), `occurred_at` | Takes the organization lock and applies rule 7b; ignores duplicates and older versions |
| `CapacityClassSuspensionScheduledV1` | at the effective time (§7.3 step 6) | `organization_ref`, change group ref, selected class refs, `new_capacity`, `capacity_version` | §7.3 step 6 |

Both go through `billing.outbox`, are published at least once and in no guaranteed order. **Outbox key (F6-07), one rule for all rows:** `idempotency_key` = (organization, event type, `capacity_version`) for these two events; (subscription, event type, boundary time) for settle-generated rows that do not bump the version (§6). **Publisher:** the same periodic runner as the sweep (owner choice, open); until it runs, residuals (d) and (f) have no time bound (§12); every consumer is idempotent (rule 7b is max-based; the suspension consumer is keyed by change group ref). Publication and both consumers are built in B-5; the emitting rows are written from B-1 on.

### 7.7 `BillingQuoteInputsPortV1` (Billing, read-only, used by the payment side; **NEW**, D-066-73 PD-3b)

The quote is computed on the payment side (D-066-65, D-066-73 PD-3a) from inputs that only Billing knows (SRS 1871, 1873).

| Operation | Result `QuoteInputsV1` |
|---|---|
| `read(organization_id, purpose, at)` | `price_version_id`; `billing_period` (`MONTHLY` or `ANNUAL`); `unit_price_vnd_full_period` (full-period price per slot); `quantity_basis` (`SLOT`); `current_period_start` and `current_period_end` (the capacity period in effect, UTC); `current_paid_slots`; `outcome` (`OK`, `NO_SUBSCRIPTION`, `NO_PRICE_VERSION`, `UNAVAILABLE`). Settles due transitions first, like §7.1 |

PAY-0 uses only a fake implementation until B-4 builds this one. A later purpose `TOP_UP` (school or Parent quota top-up) adds the per-unit price from the same price version; its fields are fixed with B-3.

## 8. Public HTTP API (paths per D-066-68 C-D9: `/api/<namespace>/v1/...` as the interim mapping of the SRS `/v1` paths)

| Method and path | Actor | Response |
|---|---|---|
| `POST /api/be1/v1/organizations/{organization_id}/classes` (existing; changed in B-2) | School Manager | 201 / 409 `CLASS_CAPACITY_REACHED` / 409 `SUBSCRIPTION_RESTRICTED` / 503 `BILLING_UNAVAILABLE` / 400 `INVALID_IDEMPOTENCY_KEY` / 400 `INVALID_REQUEST` (missing key) / 404 out of scope / 403 in-scope refusal (CONV-1) |
| `GET /api/billing/v1/organizations/{organization_id}/subscription` (SRS §9.6 group; read only) | School Manager — UC-06 precondition: School Manager "có thể đọc subscription/sức chứa" (line 1458) | status, capacity, active class count (from BE1), available, `capacity_version` |
| `GET /api/billing/v1/video-quota` (SRS §21.2 line 1678 `GET /v1/video-quota`) | Parent (own account); assigned Teacher (the school quota of the occurrence's organization, read only); School Manager (the school quota) | granted, used, available, period (scope from the resolver) |

**Purchase routes are payment-side** (D-066-65): the organization checkout `POST /api/billing/v1/organizations/{organization_id}/subscription/checkout` (PAY-0, School Manager, D-066-74) and, later, the quota top-up purchase of SRS 1679 `POST /v1/video-quota/purchases` (Parent for the Parent account, School Manager for the school, D-066-74; planned with B-3 and the payment teammate). Billing serves them only through §7.4 and §7.7. `/api/billing/v1` joins `CONV1_PREFIXES` in whichever slice ships the first `/api/billing/v1` route.

## 9. Errors

SRS §9.8 envelope, built by CONV-1 (`interfaces/http/error_envelope.py`). `CLASS_CAPACITY_REACHED`, `SUBSCRIPTION_RESTRICTED`, `VIDEO_QUOTA_EXCEEDED` (409); `INVALID_IDEMPOTENCY_KEY` (400); `RESOURCE_NOT_FOUND` (404); `ACTION_NOT_ALLOWED` (403); **`BILLING_UNAVAILABLE` (503, NEW)**: CONV-1 sets `retryable=true` for every 503 and copies a `Retry-After` header into `retry_after_seconds`. `NO_SUBSCRIPTION` → 409 `SUBSCRIPTION_RESTRICTED`. `NO_PRICE_VERSION` → 503 `BILLING_UNAVAILABLE` (as PAY-0 I-4; Draft 7 proposed `retryable=false`, which the CONV-1 envelope cannot express for a 503). `DOWNGRADE_SELECTION_INSUFFICIENT` and `DOWNGRADE_ALREADY_SCHEDULED` (409, **NEW, proposals**) for the downgrade use case (§7.3). None of these new codes is yet in the CONV-1 message sets (`MESSAGES` or `STATUS_MESSAGE_ONLY`); the first slice that returns a code adds its safe Vietnamese message (B-2 for the class-create codes; PAY-0c already adds `SUBSCRIPTION_RESTRICTED` and `BILLING_UNAVAILABLE`, so B-2 reuses them if PAY-0c lands first).

## 10. Idempotency (SRS §21.4)

| Operation | Key scope | Replay | Mismatch |
|---|---|---|---|
| BE1 class create | principal + `CREATE_CLASS` + organization + key (BE1 receipt) | original 201 only; errors re-evaluated | 400 `INVALID_IDEMPOTENCY_KEY` |
| `admit_video_request` | scope + key (usage unique, fingerprint stored) | same usage | `IDEMPOTENCY_MISMATCH` → 400 `INVALID_IDEMPOTENCY_KEY` |
| `open_subscription` | organization | existing subscription | — |
| payment commands | provider event receipt + event type | no second effect | other content hash → refused |
| `schedule_downgrade` | change group ref | same schedule | refused |

## 11. Slices (each with its own Task Approval; one BE slice at a time)

**Queue (D-066-73 PD-8, D-066-75 CM-10):** FR-C-08 → SEED-1 → PAY-0a → PAY-0b → PAY-0c → C-M1 BE → B-1; the order of B-2 to B-5 after B-1 is set when B-1 is done. B-1 depends on PAY-0a (the payment tables exist).

1. **B-1 Foundation:** schema and migration (branch label `billing`; check the existing multi-head Alembic tests), the **subscription foreign keys on the payment tables that PAY-0a created** (no payment table is created here), `open_subscription` with `NO_PRICE_VERSION`, `open_subscriptions_for_existing_organizations`, the bootstrap call and its operator error, `settle_due_transitions`, `read_effective_capacity` (admission capacity rule of §3.2), `OrganizationListPortV1`, `read_scheduled_downgrade`, `CapacityVersionChangedV1` outbox rows on every version bump, env-guarded seed price version, Billing's own engine and pool (size fixed here), unit and contract tests.
2. **B-2 Class-create admission (BE1):** §4 flow (fresh transaction, `FOR NO KEY UPDATE`, receipt re-check, `valid_until`, timeouts), BE1 receipt, mapping, `GET .../subscription`, the per-process organization-lock limiter (§4 step 6), the stamp rules of §4 step 7, concurrency tests on a disposable PostgreSQL database: two creates at the last slot; a create racing a downgrade being scheduled; a create racing a downgrade taking effect; **a create that read its answer before a downgrade whose Billing call times out after committing (F5-01 interleaving: the create must re-read after the null stamp)**; the one-re-read budget. Enabled in an environment only when an approved price version exists there and the existing-organization run reports zero remaining.
3. **B-3 Video quota:** quota scopes, lazy grants, usage, `VideoQuotaPortV1` with contract tests, resolver port, `GET /api/billing/v1/video-quota`, and the `TOP_UP` purpose of §7.7 for the later top-up purchase route (payment side).
4. **B-4 Payment interface (Billing side):** the three commands of §7.4 with the caller's session, invoice-level idempotency, `content_hash` and `FulfilmentResultV1`; the real `BillingQuoteInputsPortV1` of §7.7. After the payment teammate's port review.
5. **B-5 Lifecycle and downgrade:** §6 transitions and settle rules, local roll-over, the downgrade use case of §7.3 (BE1 counts directly; replay through `read_scheduled_downgrade`; `DOWNGRADE_SELECTION_INSUFFICIENT` and `DOWNGRADE_ALREADY_SCHEDULED`; the audit sink and events; invoked only through an internal command for operators and tests until a downgrade route is decided — no public route in this plan), outbox publication, BE1 consumers of `CapacityVersionChangedV1` (rule 7b) and of the suspension event with the effective-time over-limit check, the `suspended` class state with its read-only visibility and write refusals, and the sweep runner once the owner has chosen it.
6. **Later:** Story saga connection; Platform Admin organization creation calling `open_subscription`; BE1 class archive and reactivation; auto-renew on/off and downgrade request routes.

## 12. Acceptance criteria and open items

Acceptance before B-1 approval: every element traces to the SRS, the register, D-066-63 as amended by D-066-67, or a decision row, with NEW items and interpretations marked; payment limited to the Billing side of §7.4 and §7.7; class creation and downgrade scheduling serialize on the same BE1 organization lock (SRS §11.1 item 10), and the remaining capacity-change window is limited as stated in §4 step 5 (residuals (d) and (f) accepted in D-066-66); double usage impossible by §5; idempotency per §10; no cross-module table access (the fulfilment session of §7.4 is inside the `billing` module).

**Settled since Draft 7** (no longer open): residuals (d) and (f) and the audit sink (D-066-66); the D-066-63 amendment (D-066-67); route prefix and 403/404 (D-066-68, built by CONV-1); missing key → 400 `INVALID_REQUEST` (C-D5); `NO_SUBSCRIPTION` → 409 and `NO_PRICE_VERSION` → 503 (§9); the billing-admin role = School Manager and the payers (D-066-74); who builds Billing (D-066-74); the payment tables' creator (PAY-0a, D-066-73).

Open items: the operator procedure for a surplus; the public names of `DOWNGRADE_SELECTION_INSUFFICIENT`, `DOWNGRADE_ALREADY_SCHEDULED` and the audit events; the downgrade route and an audit read route; the concrete timeout values (Billing sum strictly below the BE1 call timeout); a clock-skew margin if Billing ever leaves BE1's database server; the sweep and outbox publisher runner (the owner's lane builds it, D-066-73 PD-9a; it is shared with the PAY-0 jobs); Billing's pool size; the interpretations in §3.1, §3.2, §4, §6 and §2 (grace start, restore from RESTRICTED, add-on carry-over in local roll-over, `CANCELED_BY_PROVIDER` from ACTIVE/GRACE, per-class change-group unique, the admission-capacity formula min(current, scheduled + selected), the owner as approver of the staging/production price version); replacing or cancelling a scheduled downgrade; the breaking change of a required idempotency key for existing class-create callers; temporary video units and placeholder prices (SRS 168 review values); register update for NEW items, including the PAY-0 columns (D-066-73 PD-2b to PD-2e); SRS updates: §9.8 for `BILLING_UNAVAILABLE`, §23.1 wording, and FR-B-02/BR-28 for the MoMo-only V1; Teacher in several organizations; auto-renew and downgrade routes.

## 13. Disposition of the reviews

**Draft 6 review (F6-01 to F6-07) — fixed in text, not re-reviewed (owner instruction):**

| ID | Disposition |
|---|---|
| F6-01 | §7.3 step 4 timeout ordering and session closed before null; §7.3 table Billing timeouts; rule 7a rationale; residual (f) extended to a Billing commit after BE1 gave up; §12 |
| F6-02 | §4 step 5f bound restated (each stale create in flight); operator resolves the surplus (§7.3 step 6, §12) |
| F6-03 | Rule 7a: a non-null stamp is never lowered (max), also on the replay path |
| F6-04 | §7.6 suspension event carries `new_capacity`; §7.3 step 6 uses it |
| F6-05 | §2 audit sink (core audit records if they fit, else NEW table); B-5 invokes the use case through an internal command, no public route |
| F6-06 | §7.3 step 2 replay of an `APPLIED` downgrade returns the stored outcome; different ref → `DOWNGRADE_ALREADY_SCHEDULED`; audit events once per change group ref; `read_scheduled_downgrade` by ref |
| F6-07 | §4 step 6 one limiter for every organization-lock waiter; §7.6 publisher runner and one outbox-key rule; §6 points to it |

**Draft 5 review (F5-01 to F5-06):**

| ID | Disposition |
|---|---|
| F5-01 | (a) §7.3 step 4: on timeout or lost response the null stamp is committed in the lock-holding transaction, no rollback in between; (b) §4 step 5f and §12: commit failure or process death after the Billing commit is an accepted residual, closed by the event or a retry; §7.3 step 2 defines the same-key retry against an existing schedule (409 `DOWNGRADE_SELECTION_INSUFFICIENT` plus an operator audit event, never silent); §7.3 step 6 effective-time over-limit check; (c) the "stricter" sentence corrected after §7.3 step 6; (d) B-2 race test with this interleaving |
| F5-02 | §4 step 7: stamp update rules; the consumer never turns null into a value; no `GREATEST` |
| F5-03 | §7.6 event contract (payload, at-least-once, unordered, idempotent, max-based); §3.3 every bump emits; B-1 writes the rows, B-5 publishes and consumes; the provider-cancel command is enabled only with or after B-5 |
| F5-04 | §4 step 6: Billing's own engine and pool; per-process cap on concurrent creates; B-1 and B-2 |
| F5-05 | §11 B-5 no longer names `ActiveClassCountPortV1` |
| F5-06 | §4 step 3 one re-read in total, null-stamp call counts; §4 step 8 same-server clock assumption, skew margin open |

**Draft 4 review (F-01 to F-08):**

| ID | Disposition |
|---|---|
| F-01 | Owner selection "dấu version": §2 `capacity_version_seen`; §4 step 3 stamp comparison and re-read; §7.3 step 4 writes the stamp under the lock (unknown on indeterminate outcomes); header and §4 step 5 restated |
| F-02 | §4 step 5d and §6: immediate provider cancellation bumps the version and emits `CapacityVersionChangedV1`; remaining window accepted and listed |
| F-03 | §7.3 step 4 indeterminate outcome stated; change group ref from the client idempotency key; Billing-side timeouts; replace/cancel listed open |
| F-04 | §1 lock-order invariant; §7.3 counts in BE1 directly; §7.5 port note; §4 step 6 scoped to the create path, downgrade connection use stated in §7.3 |
| F-05 | §4 step 3 `clock_timestamp()`, explicit READ COMMITTED, null `valid_until` not passed |
| F-06 | Header: 404/403 deferred to O-CONV with interim 403; 503 `BILLING_UNAVAILABLE` named as an owner decision |
| F-07 | §4 step 1 and §12: interpretations marked; breaking change flagged; `NO_PRICE_VERSION` mapping proposed |
| F-08 | §1: module ownership follows the O-PAY selection, pending agreement |

**Draft 3 review (D3-01 to D3-12):**

| ID | Disposition |
|---|---|
| D3-01 | §7.3 downgrade use case under the BE1 organization lock; §3.2 admission capacity; §4 step 4–5; B-2 race tests; §12 softened, SRS §11.1 item 10 cited |
| D3-02 | Header: three D-066-63 sentences to amend, residual window, kept rules |
| D3-03 | §2 price version for staging/production from the payment teammate; `NO_PRICE_VERSION`; §7.3 bootstrap failure and repair; B-2 enable conditions |
| D3-04 | §4 step 2 ends the request transaction before the port call; step 6 pool |
| D3-05 | §4 step 3 `FOR NO KEY UPDATE`, READ COMMITTED count after the lock, organization existence and state |
| D3-06 | §4 steps 1 and 3: authorization first, missing key, receipt re-check under the lock |
| D3-07 | §4 step 3 database `now()`, second expiry → 503; §3.3 terminal states |
| D3-08 | §3.2 admission capacity min(current, scheduled + selected) |
| D3-09 | §2 BE1 additions and B-5: read-only visibility and write refusals for suspended classes |
| D3-10 | §7.3 bootstrap single-shot; §2 `content_hash`; per-class unique marked interpretation/NEW; §6 settle idempotency |
| D3-11 | §6 further rules; notifications excluded; B-5 sweep after owner choice |
| D3-12 | §4 step 1 and §8: current 403 kept until O-CONV |

**Draft 2 review (N-01 to N-21):**

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

## 14. Draft 8 changes (decisions applied; design unchanged)

| Place | Draft 7 | Draft 8 | Source |
|---|---|---|---|
| Header | owner choices not yet decision rows; D-066-63 to amend; 404/403 deferred to O-CONV | decision rows listed; 404/403 built by CONV-1; payers and MoMo stated; gate per slice plus the payment teammate's port review for B-4 | D-066-66, 67, 68, 71, 73, 74 |
| §1 | builder pending O-PAY | owner's lane builds Billing; payment tables in the same module; the fulfilment session is intra-module | D-066-65, 73 (PD-2a, PD-5), 74 |
| §2 `price_versions` | staging/production price from the payment teammate | commercial setting approved by the owner (interpretation) | D-066-74 |
| §2 payment tables | created empty by B-1 | created by PAY-0a with the NEW PD-2c/2d columns and the PD-2e index; B-1 adds the subscription FKs | D-066-73 PD-2a to 2e; PAY-0 Draft 6 §6.1 |
| §4 step 1 | interim 403; key rule as interpretation | CONV-1 404/403 guard and C-D5 key rule | D-066-68, 71 |
| §4 step 3 | "conventions slice's generic retryable error" | retryable 503 in the CONV-1 envelope; code fixed in the B-2 Task Approval | D-066-71 |
| §4 step 6 | Billing's own pool for every call | exception for the §7.4 fulfilment call (caller's session) | D-066-73 PD-5 |
| §7.4 | receipt written before the call; no result type | same-transaction receipt, lock order, invoice-level idempotency, `content_hash`, `FulfilmentResultV1`, MoMo recurring | D-066-73; PAY-0 Draft 6 §3.3, §6.1; D-066-74 |
| §7.5 | billing-admin role open | School Manager | D-066-74 |
| §7.7 | — | NEW `BillingQuoteInputsPortV1` | D-066-73 PD-3b |
| §8 | `/v1/...` paths; prefix per O-CONV; billing admin undefined | `/api/billing/v1/...` interim paths; actors per D-066-74; purchase routes are payment-side | D-066-68 C-D9, 73, 74 |
| §9 | envelope "fixed by the conventions slice"; `NO_PRICE_VERSION` with `retryable=false` proposed | CONV-1 envelope; 503 always retryable; `NO_PRICE_VERSION` → 503; message-set additions per slice | D-066-71; PAY-0 I-4 |
| §11 | B-1 creates empty payment tables; B-4 "after agreement" | queue stated; B-1 adds FKs only and depends on PAY-0a; B-3 adds `TOP_UP` quote inputs; B-4 Billing side of §7.4 and §7.7 | D-066-73, 75 |
| §12 | residuals, D-066-63 amendment, O-PAY, prefix and 404/403 open | moved to "settled since Draft 7"; runner owner stated; SRS update list adds FR-B-02/BR-28 | D-066-66, 67, 68, 73, 74 |

Not changed: §3 capacity rules, §4 steps 2–5 and 7–8, §5, §6, §7.1 to §7.3, §7.6, §10, §13 (review dispositions of Drafts 2 to 6).
