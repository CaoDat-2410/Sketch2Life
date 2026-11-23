# FEAT-066 PAY-0 — payment interface skeleton for the payment teammate (Draft 3)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package plans a framework only. It authorizes no code, migration, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 2 (23,396 B, `195B0247…`). Its round-2 review was NOT READY with 1 P1, 6 P2 and 7 P3 (`evidence/notes/PAY_0_COLD_REVIEW_DRAFT2_20261118.md`). The owner chose "Draft 3 + round 3" in chat on 2026-11-18. §14 maps each round-2 finding to its fix; §15 keeps the round-1 map.
- **Owner request:** "khởi động lại làm khung payment đi" (chat, 2026-11-18). The owner wants a framework that lets the payment teammate (HieuNewBie) build MoMo and then VNPAY.
- **Relation to D-066-65:** D-066-65 records the owner's words "payment tk khác làm nên tôi ko đụng", and assigns payment (quote, invoice, checkout, provider callbacks) to the payment teammate. **Building this skeleton in the owner's lane is therefore an amendment to D-066-65**, asked as PD-1. Billing core (B-1 to B-5) stays frozen.
- **Dependency:** PAY-0 uses the CONV-1 envelope (`interfaces/http/error_envelope.py`, `CONV1_PREFIXES`), which exists only in commit `2dddc607` on the local-only branch `feature/feat066-conv1` (D-066-71, CV-B). A PAY-0 branch must start from a queue tip that contains that commit.

## 1. Authority

| Input | Pin or location |
|---|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 B, `B9B1F42D…` |
| Data table register | `.../artifacts/DATA_TABLE_REGISTER.md`, 171,609 B, `7CDFDBEC…`, lines 390–392 and 460–462 |
| Physical data dictionary (draft) | `.../artifacts/PHYSICAL_DATA_DICTIONARY_DRAFT_REV57_20261109.md`, 53,694 B, `DDBF2E7D…`, lines 94–96. Logical fields only; the DDL is still BLOCKED |
| Billing contract | `plan/PLAN_L2_BILLING_CONTRACT_DRAFT7_20261118.md` (49,498 B, `216B33D7…`, closed without review): §1, §2, §4 step 6, §7, §7.4, §7.5, §9, §10, §11 |
| Decisions | D-066-65 (lanes, O-PAY), D-066-66, D-066-68 (conventions), D-066-71 (CONV-1 envelope; CV-B local-only branch) |

**SRS clauses used:**

| Line | Content |
|---|---|
| 167, 205 | MoMo and VNPAY; the callback goes to the backend; the redirect only shows status |
| BR-28 (272) | VND; MoMo and VNPAY are the V1 adapters; no VietQR |
| 399 | OrganizationSubscription states, including `PAYMENT_PENDING` (Billing core; out of PAY-0) |
| 400 | PaymentAttempt states: CREATED, PENDING, SUCCEEDED, FAILED, EXPIRED |
| 587–591, 599 | FR-B-01 to FR-B-05 and FR-B-13 |
| 752, 936 | Provider adapters run only in the backend worker; no credential reaches a client |
| 783, 1847 | `PaymentEventV1` and `PaymentVerifiedV1` |
| 811 | `/v1/payments/{provider}/callback` |
| 937, 1028, 1869 | Signature verified; unique provider event; receipt and invoice/subscription update in one idempotent transaction |
| 942 | No request body, Authorization header or payment credential in logs |
| 995 | A per-provider abuse and replay policy for payment callbacks; a valid retry is never refused because of the generic unauthenticated bucket |
| 1012 | Module `billing` holds rates, subscriptions, capacity, invoice/payment, provider receipts/events, grants and the usage ledger |
| 1137 (AC-14), 1221 (OI-09), 1271 | Acceptance; open merchant and recurring items; MoMo Subscription and VNPAY recurring documents |
| 1677 | `POST /v1/organizations/{org_id}/subscription/checkout`: actor "Admin billing"; input price version, billing period and desired capacity; returns "202 payment attempt/redirect instruction" |
| 1679 | `POST /v1/video-quota/purchases` (TO-BE, Q193 gate) — out of PAY-0 |
| 1680 | `POST /v1/payments/{provider}/callback`: provider format acknowledgement; no browser auth |
| 1697 | Key reuse with a different payload gives `INVALID_IDEMPOTENCY_KEY` |
| 1746 | `PaymentCallbackV1`: verify the signature on the exact bytes; freshness and replay; unique event ID; amount, currency and order checks; acknowledge after a durable receipt |
| 1863–1876 (§23.2) | Quote and invoice first; the invoice stores the base price, added quantity, period start and end, remaining-time ratio, rounded VND amount and price version; proration = added slots × full-period price per slot × (remaining seconds / total seconds of the current provider period), half-up to whole VND, UTC timestamps; no activation before verification; no double charge or double activation |
| 2088 | A bad-signature callback is a security event; a valid callback not reconciled within 5 minutes is a warning |
| 2133–2137 | Verify the signature and the event ID before any state transition; on a bad signature, reject, write a safe security event, and activate nothing; if the provider status and the internal invoice disagree, keep capacity unchanged and reconcile through an approved adapter |
| 2170 | Adapter integration tests include Redis/RQ redelivery and MoMo/VNPAY sandbox callbacks |

## 2. Layers and ownership

| Layer | Owner | Contents |
|---|---|---|
| **Billing core** | Owner's lane; **frozen** | Price versions, subscriptions, capacity, quota, the Billing side of `PaymentFulfilmentPortV1` (Draft 7 §7.4; slice B-4), and a read-only `BillingQuoteInputsPortV1` (§3.5, **NEW**; not in Draft 7 §7) |
| **Payment** | Payment teammate (D-066-65) | Quote and invoice (D-066-65), checkout, provider adapters, callback intake, receipts, attempts, reconciliation, and the calls into `PaymentFulfilmentPortV1` |
| **PAY-0 skeleton** | Owner's lane, built once, **if PD-1 = yes** | The ports and DTOs below, the payment tables' DDL, the intake service with the safety rules of §5, the jobs of §5.4, a fake provider and a provider contract-test kit, and the routes behind a flag. PAY-0 is the payment-side half of the "payment interface"; Draft 7's B-4 keeps the Billing-side half |

**Port review gate:** before the PAY-0a Task Approval is written, the payment teammate reviews §3, §4 and §5 and their answer is recorded. This is a precondition of the approval, not an owner decision.

## 3. Interfaces

### 3.1 `PaymentProviderPortV1` (one implementation per provider, by the payment teammate)

| Method | Runs in | Input | Output |
|---|---|---|---|
| `start_checkout` | Worker only | `CheckoutRequestV1`: `payment_attempt_id`, `invoice_id`, `amount_vnd` (integer VND), `kind` (`ONE_TIME` or `RECURRING`), `order_description_code` (no personal data), `return_url` and `ipn_url` (both from settings), `merchant_order_ref` | `CheckoutStartResultV1`: `STARTED` with `CheckoutSessionV1` (redirect URL or deep link, provider `request_id`, `expires_at`; no credential), or `ALREADY_STARTED` (the provider already holds this `merchant_order_ref`), or `PROVIDER_REJECTED(safe_code)`, or `UNAVAILABLE` |
| `query_status` | Worker only | `merchant_order_ref` | `ProviderStatusV1`: `NOT_FOUND`, `PENDING`, `SUCCEEDED`, `FAILED`, with `provider_transaction_ref`, `amount_vnd`, `currency`, `event_time`, `provider_status_code`; or `UNAVAILABLE` |
| `verify_callback` | API process | `RawCallbackV1`: HTTP method, raw query string, raw body bytes, headers, `received_at` | `PaymentCallbackV1` (§3.2). It **never raises** for bad input and does no network I/O |
| `acknowledge` | API process | `AckOutcome` (`ACCEPTED`, `DUPLICATE`, `REJECTED`, `RETRY_LATER`) | The provider-format status code and body. Pure; no network I/O |
| `test_kit` (tests only) | Tests | — | A `ProviderTestKit` with `build_signed_callback(fields, valid=True, age=...)` and `build_status(...)`, so the shared contract suite can drive any adapter (§9) |

**Interpretation I-1 (where adapters run):** SRS 752 and 936 say provider adapters run only in the backend worker. SRS 1746 requires the callback to be acknowledged after a durable receipt, inside the HTTP request. PAY-0 reads these together as: the network-facing methods (`start_checkout`, `query_status`) run only in the worker; `verify_callback` and `acknowledge` are pure functions (no network I/O, no credential leaves the process) and run in the API process.

**Adapter rules:**
- `start_checkout` is idempotent per `merchant_order_ref`. A repeated call must return `ALREADY_STARTED` or the same session, never open a second provider order.
- Signatures use a constant-time compare.
- Several active verification keys are allowed, for rotation.
- The amount unit is normalized to integer VND inside the adapter. A provider that scales amounts (to be verified from its documents) converts here. A scaling bug cannot lose a payment silently, because any amount mismatch becomes `NEEDS_REVIEW` (§5.2).

### 3.2 `PaymentCallbackV1` (SRS line 1746, logical contract)

| Field | Nullable when the outcome is not `VALID`? | Meaning |
|---|---|---|
| `provider` | No | `MOMO` or `VNPAY`, from the route; must equal the attempt's provider |
| `signature_outcome` | No | `VALID`, `INVALID`, `STALE`, `MALFORMED` (§5.2 step 2 gives the order of checks) |
| `raw_body_sha256` | No | Digest of the exact signed bytes. The raw body is never stored or logged |
| `provider_event_ref` | Yes | The provider's native event ID when it has one. Otherwise **derived** as `merchant_order_ref` + `:` + `provider_transaction_ref` (or `-` when empty) + `:` + normalized status, so an empty transaction ID on a failure cannot collide across orders |
| `merchant_order_ref`, `provider_transaction_ref` | Yes | Links to the attempt |
| `amount_vnd`, `currency` | Yes | Checked against the attempt and the invoice snapshot |
| `provider_status` | Yes | `SUCCEEDED`, `FAILED`, `PENDING` |
| `event_time` | Yes | UTC, from the provider |
| `received_at` | No | UTC, from the backend |

### 3.3 `PaymentFulfilmentPortV1` (Billing core side; Draft 7 §7.4, inputs quoted exactly)

| Command | Input (Draft 7 §7.4) | Dedupe (Draft 7) |
|---|---|---|
| `activate_add_on_slots` | organization, capacity period, added slots, `prorated_amount`, invoice ID, provider event receipt ID, content hash | Unique (subscription, receipt, event type); the same receipt with another content hash is refused |
| `issue_top_up_grant` | scope, units, invoice ID, provider event receipt ID, content hash | Grant source event unique |
| `record_renewal_outcome` | organization, outcome (`SUCCESS`, `FAILURE`, `CANCELED_BY_PROVIDER`), new period dates and `paid_extra_slots` on success, invoice ID, provider event receipt ID, content hash | Unique (subscription, receipt, event type) |

**Additions in PAY-0, to agree with the payment teammate and the Billing owner:**
- `content_hash` = SHA-256 of the canonical JSON of the command's other inputs.
- **Invoice-level idempotency:** every command is also keyed by `invoice_id` (one successful fulfilment per invoice). A callback receipt and a reconciliation receipt for the same payment therefore cannot both activate.
- **`FulfilmentResultV1`** (every command returns one):

| Result | Meaning | Intake mapping (§5.2) |
|---|---|---|
| `APPLIED` | Effect written | Receipt `PROCESSED`; ack `ACCEPTED` |
| `ALREADY_APPLIED` | Same invoice already fulfilled | Receipt `RECORDED_NO_EFFECT`; ack `ACCEPTED` |
| `RECORDED_NO_EFFECT` | Recorded with no capacity effect (Draft 7 §7.4: "A period already ended: recorded, no capacity effect") | Receipt `RECORDED_NO_EFFECT`, attempt flagged for review; ack `ACCEPTED` |
| `REFUSED(code)` | Deterministic refusal (for example another content hash for the same receipt, no subscription) | Main transaction rolls back; review transaction writes `NEEDS_REVIEW` (§5.2 step 5); ack `ACCEPTED` |
| `UNAVAILABLE` | Transient (lock timeout, Billing down) | Main transaction rolls back; no row; ack `RETRY_LATER` |

### 3.4 `InvoiceSnapshotV1` (SRS line 1871)

The snapshot holds:
- owner scope (`ORGANIZATION` or `PARENT_ACCOUNT`) and its ref;
- `purpose` (`ADD_ON_SLOTS`, `RENEWAL`, `TOP_UP`);
- the price version ID and `billing_period` (`MONTHLY` or `ANNUAL`);
- the full-period unit price per slot;
- the added quantity;
- `period_start` and `period_end` of the current provider period;
- the remaining-time ratio, as numerator and denominator in seconds;
- the rounded VND amount (half-up);
- `currency` = `VND`;
- `created_at`.

It is immutable once the invoice is `OPEN`.

### 3.5 Quote (payment side, D-066-65) and `BillingQuoteInputsPortV1` (Billing core, read-only, NEW)

- **The quote is payment-side**, as D-066-65 says. It computes the SRS 1873 proration itself from the inputs below.
- **`BillingQuoteInputsPortV1.read(organization_id, purpose, at)`** is a **new** Billing port; Draft 7 §7 has no price or period read port, and `read_effective_capacity` returns only capacity. Output `QuoteInputsV1`:

| Field | Meaning |
|---|---|
| `price_version_id` | Current price version for the organization's plan at `at` |
| `billing_period` | `MONTHLY` or `ANNUAL` |
| `unit_price_vnd_full_period` | Full-period price per slot |
| `quantity_basis` | `SLOT` (only value in PAY-0) |
| `current_period_start`, `current_period_end` | Current provider period of the organization's subscription (UTC) |
| `current_paid_slots` | Slots already paid in that period |
| `outcome` | `OK`, `NO_SUBSCRIPTION`, `NO_PRICE_VERSION`, `UNAVAILABLE` |

- The port belongs to Billing core and is still frozen. **Until B-1 exists**, PAY-0 provides only a fake implementation for local and test use, with a synthetic price version and period. The real add-on checkout therefore waits for B-1 (PD-3).
- A client-supplied amount is never trusted (SRS §21.4). The request's `price_version_id` is compared with the one read; a difference gives 409 `PRICE_VERSION_CHANGED` (§7).

## 4. Payment tables (DDL by PAY-0 if PD-2a = yes; written only by the payment side)

All three tables live in schema `billing`, which SRS 1012 treats as one module with Billing core.

| Table | Keys and constraints | Columns |
|---|---|---|
| `billing.invoices` | PK `invoice_id`; typed owner scope and ref; unique `invoice_number`; `CHECK currency = 'VND'`; `subscription_id` a **soft ref** until B-1 adds the FK | Register (lines 390–392): `invoice_number`, `period_start`, `period_end`, `currency`, `subtotal`, `prorated_adjustment`, `total`, `status`, `due_at`, `paid_at`, `invoice_snapshot` (`InvoiceSnapshotV1`), `created_at` |
| `billing.payment_attempts` | PK `payment_attempt_id`; FK `invoice_id`, **unique** (one attempt per invoice in PAY-0); unique `merchant_order_ref`; unique provider `request_id`; **unique (`principal_account_id`, `operation`, `organization_id`, `idempotency_key`)** | Register: `provider`, `merchant_order_ref`, `provider_transaction_ref`, `request_id`, `amount`, `currency`, `status`, `idempotency_key`, `initiated_at`, `completed_at`, `safe_failure_code`. **NEW** (PD-2c): `principal_account_id`, `operation` (`ORG_SUBSCRIPTION_CHECKOUT`), `organization_id`, `request_fingerprint` (SHA-256 of the canonical request body), `checkout_claimed_at`, `checkout_tries`, `needs_review` (bool), `review_reason_code` |
| `billing.provider_event_receipts` | PK `event_receipt_id`; unique (`provider`, `provider_event_ref`); **0 or 1 target** (`CHECK` that at most one of `payment_attempt_id_optional` and `subscription_id_optional` is set), as in the register; `subscription_id_optional` a soft ref until B-1 | Register: `provider`, `provider_event_ref`, `signature_valid`, `payment_attempt_id_optional`, `subscription_id_optional`, `received_at`, `processed_at`, `processing_status`, `safe_error_code`, `payload_hash` |

**Departures from the register, stated:**
- The register allows a receipt row for an unverified callback, with both FKs empty (line 392). PAY-0 writes **no receipt row for an unverified callback**, so a forged callback can never claim the unique key. Unverified callbacks become safe security events (§5.2), as SRS 2133–2135 asks. `signature_valid` is therefore always true in PAY-0. Asked as PD-2b.
- The NEW attempt columns above. Asked as PD-2c.

**DDL versus write ownership:** PAY-0 creates these tables (Alembic branch label `billing`, an independent root). Only the payment side writes them. B-1 later adds the core tables and the subscription FKs on the same branch label (§6.1 lists the Draft 7 edits).

**States:**

| Entity | States |
|---|---|
| Payment attempt (SRS line 400) | `CREATED`, `PENDING`, `SUCCEEDED`, `FAILED`, `EXPIRED` (transitions in §5.3). A provider cancellation is `FAILED` with a safe code. The checkout claim is a column, not a state, so the SRS state list is unchanged |
| Invoice | `OPEN` → `PAID` or `VOID`. `VOID` → `PAID` only through a late verified success (§5.3) |
| Receipt (only verified callbacks and confirmed reconciliation statuses) | `PROCESSED`, `RECORDED_NO_EFFECT`, `NEEDS_REVIEW`; and `FULFILMENT_PENDING` only under PD-5 option B |

## 5. Flows and safety rules

### 5.1 Checkout (SRS line 1677)

1. **Request:** `POST /api/billing/v1/organizations/{organization_id}/subscription/checkout` with an `Idempotency-Key` (§7 has the body).
2. **Synchronous part, one transaction:**
   - look up an attempt by (principal, `ORG_SUBSCRIPTION_CHECKOUT`, organization, key). If found with the same `request_fingerprint`, return the same 202 body. If found with another fingerprint, return 400 `INVALID_IDEMPOTENCY_KEY` (SRS 1697);
   - read `BillingQuoteInputsPortV1` and compute the quote;
   - create an `OPEN` invoice with the snapshot;
   - create a `CREATED` attempt (the unique key is inserted here; a concurrent same-key insert conflicts, the transaction rolls back, and the request re-reads and answers as in the first point);
   - enqueue the `payment_checkout_start` job after commit;
   - return **202** (§7).
3. **Worker job `payment_checkout_start`** (SRS 752, 936):
   - claim the attempt with a compare-and-set: set `checkout_claimed_at` only where the status is `CREATED` and there is no claim younger than the lease (settings). A redelivered job that loses the claim does nothing (SRS 2170 RQ redelivery);
   - call `start_checkout`. `STARTED`: store the session and move the attempt to `PENDING`. `ALREADY_STARTED`: call `query_status` and apply §5.3; if the provider has no payment and the session was not stored, mark the attempt `FAILED` with `CHECKOUT_SESSION_LOST` and the invoice `VOID` (the client starts a new checkout with a new key). `PROVIDER_REJECTED`: `FAILED` with the safe code, invoice `VOID`. `UNAVAILABLE`: release the claim and let the sweep retry.
4. **Sweep job `payment_stuck_created_sweep`:** an attempt still `CREATED` past a threshold is re-enqueued, up to a bounded number of tries. Before marking it `FAILED`, the sweep calls `query_status`; a provider payment found there goes through §5.3, never to `FAILED`.

### 5.2 Callback (`POST /v1/payments/{provider}/callback`)

1. **Before verification:**
   - `provider` must be an enabled adapter; otherwise 404 with no write;
   - the body is capped (settings, default 64 KiB). Verification is an HMAC over at most that many bytes, so it is cheap.
2. **`verify_callback`**, in this order: parse (failure → `MALFORMED`); signature over the exact bytes (failure → `INVALID`, whatever the age); freshness window (failure → `STALE`); field checks.
3. **Outcome other than `VALID`:**
   - no database row;
   - a **safe security event** (counter and structured log with `provider`, `signature_outcome`, `raw_body_sha256`, source IP only);
   - the abuse limiter (§5.6) counts it; over the limit, the response is 429 and the security event is aggregated;
   - the provider-format rejection is returned. Nothing changes state (SRS 2133–2135);
   - **`STALE` with a valid signature only:** if `merchant_order_ref` names an existing attempt (read-only lookup), enqueue an immediate `payment_reconcile_one` job for it, at most once per attempt per window, so a delayed genuine callback is recovered in seconds rather than at the next reconciliation pass.
4. **`VALID`:** the limiter is never applied (SRS 995). In **one transaction** (the main transaction, with a timeout from settings that must stay below the provider's IPN timeout):
   - (a) insert the receipt. A unique conflict means the same verified event was already committed, so acknowledge `DUPLICATE` with no effect;
   - (b) resolve the attempt by `merchant_order_ref` and lock it (`SELECT … FOR UPDATE`), then lock its invoice. **Unresolvable** (no attempt) → go to step 5 with reason `UNKNOWN_ORDER`;
   - (c) check provider, amount and currency against the attempt and the invoice snapshot. **Mismatch** → go to step 5 with reason `PROVIDER_MISMATCH`, `AMOUNT_MISMATCH` or `CURRENCY_MISMATCH`. Capacity is unchanged, as SRS 2137 asks;
   - (d) apply the transition table of §5.3 to the locked state. Because the rows are locked, a concurrent second receipt (callback and reconciliation) waits and is then judged against the new state; no compare-and-set can fail half-way;
   - (e) fulfilment, per PD-5, mapped by `FulfilmentResultV1` (§3.3). `REFUSED` → step 5 with the refusal code; `UNAVAILABLE` → roll back and acknowledge `RETRY_LATER`.
5. **Review transaction (verified but not applicable):** roll back the main transaction, then in a **separate small transaction** insert the receipt as `NEEDS_REVIEW` with the safe reason code (target = the attempt when known, none otherwise) and set `needs_review` and `review_reason_code` on the attempt when it exists. Acknowledge `ACCEPTED` (the event is durably recorded; a provider retry would be a `DUPLICATE`). If the review transaction also fails, acknowledge `RETRY_LATER` and store nothing, so the provider retries.
6. **Acknowledge only after a transaction commits.** A transient failure stores nothing and returns `RETRY_LATER`, so the provider's retry is processed as new and no payment is lost.
7. **Exceptions:** the callback handler catches every exception and returns `acknowledge(RETRY_LATER)` in the provider format, with no body echo. The app's plain-text 500 for non-CONV-1 paths (`app.py:812`) is never reached from this route.

### 5.3 Transition table (event status × attempt state, applied under the row lock)

| Event status ↓ / attempt → | `CREATED` | `PENDING` | `SUCCEEDED`, same `provider_transaction_ref` | `SUCCEEDED`, other `provider_transaction_ref` | `FAILED` | `EXPIRED` |
|---|---|---|---|---|---|---|
| `SUCCEEDED` | → `SUCCEEDED`, invoice `PAID`, fulfil (the provider has the money; the worker may have died before storing `PENDING`) | → `SUCCEEDED`, invoice `PAID`, fulfil | no change; fulfil returns `ALREADY_APPLIED` → `RECORDED_NO_EFFECT` | **double payment**: no change, no fulfil; review transaction with `DOUBLE_PAYMENT` | → `SUCCEEDED`, invoice `VOID` → `PAID`, fulfil, flag `LATE_SUCCESS` | same as `FAILED` |
| `FAILED` | → `FAILED`, invoice `VOID` | → `FAILED`, invoice `VOID` | `RECORDED_NO_EFFECT`, flag `FAILED_AFTER_SUCCESS` | `RECORDED_NO_EFFECT`, flag `FAILED_AFTER_SUCCESS` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` |
| `PENDING` | → `PENDING`, store `provider_transaction_ref` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` |

- Every "flag" sets `needs_review` and `review_reason_code` on the attempt in the main transaction, and the receipt state is the one the fulfilment result gives.
- A fulfilment after a late success may return `REFUSED` or `RECORDED_NO_EFFECT` (for example the period ended); both leave the attempt flagged. Refunds are an operator action and out of PAY-0.
- All acknowledgements in this table are `ACCEPTED`, except a receipt unique conflict (`DUPLICATE`) and a transient failure (`RETRY_LATER`).

### 5.4 Background jobs (deliverables, §9)

| Job | Trigger | Rule |
|---|---|---|
| `payment_checkout_start` | Enqueued after the checkout commit | §5.1 step 3 |
| `payment_stuck_created_sweep` | Periodic | §5.1 step 4 |
| `payment_reconcile_pending` | Periodic | Attempts `PENDING` (or `CREATED` with a claim) older than the threshold: call `query_status`. `SUCCEEDED`, `FAILED`, `PENDING` go through §5.2 steps 4–6 with the event ref `recon:` + `merchant_order_ref` + `:` + `provider_transaction_ref` (or `-`) + `:` + status. Bounded tries with backoff |
| `payment_reconcile_one` | Enqueued by a valid-signature `STALE` callback | Same as above, for one attempt |
| `payment_expire` | Periodic | An attempt past `expires_at`: call `query_status` first; `SUCCEEDED` goes through §5.3; `NOT_FOUND` or `FAILED` → `EXPIRED` (or `FAILED`), invoice `VOID`; `UNAVAILABLE` → try later, never expire blind |
| `payment_unreconciled_warning` | Periodic | Emits a warning metric and log for every receipt in `NEEDS_REVIEW` and every attempt with `needs_review`, and for any attempt that has a verified receipt but is not terminal after 5 minutes (SRS 2088) |

**Runner:** PAY-0 delivers the job functions, the RQ enqueue for `payment_checkout_start` and `payment_reconcile_one`, and a one-shot command that runs the periodic jobs once. The **periodic scheduler** that calls that command is not in PAY-0; Draft 7 also leaves its sweep runner open. PD-9 asks for it. Until it exists, the provider's IPN retries are the only recovery in a deployed environment, which is acceptable only while the flag is off outside `local` and `test`.

### 5.5 Browser return

The status route reads only. Without a verified event the invoice stays `OPEN` and the UI shows "pending" (SRS 589, 1137, 1868). An attempt with `needs_review` shows "pending" as well; the reason code is never shown to the client.

### 5.6 Abuse limiter, logging and secrets

- **`CallbackAbuseLimiter`** (infrastructure component, NEW): an in-process token bucket keyed by (provider, source IP), and a per-provider counter, both counting **only non-`VALID` outcomes**. It follows the existing in-process pattern of `RegistrationRateLimiter` (`interfaces/http/routers/auth_registration.py:61`). A `VALID` callback is never refused by it (SRS 995). A shared store (Redis) is out of PAY-0; with several API processes the limit is per process. Any edge or proxy rate limit outside the app must exempt or raise the limit for the callback path (not verified; deployment item).
- No body, headers, query string or credential is logged (SRS 942).
- Security events carry opaque refs, digests and the source IP only.
- Merchant IDs, partner codes, callback URLs and key references come from settings or the environment; none are in Git.
- The fake provider's test key is generated at run time (not an uppercase secret-like constant, so the security validator applies cleanly).
- A settings validator refuses the fake provider outside `local` and `test`, following the existing `modal_dev` pattern in `infrastructure/config/settings.py`.

## 6. Fulfilment transaction (PD-5)

SRS 1028 and 1869 ask for the receipt and the invoice/subscription update in one transaction. SRS 1012 places invoices, payments and provider receipts in the same `billing` module as subscriptions, so **option A is a transaction inside one module**. It conflicts only with Draft 7's own rules: §4 step 6 gives Billing core its own engine and pool, and §7.4 says the receipt is written by the payment side before it calls.

| Option | Content |
|---|---|
| **A (recommended)** | The payment intake and Billing core share one database session for this call only. Billing's `PaymentFulfilmentPortV1` accepts the caller's session. Lock order: attempt, then invoice, then the Billing subscription lock; no BE1 lock is held. `UNAVAILABLE` rolls back everything |
| B | Separate transactions. Step 4 commits the receipt as `FULFILMENT_PENDING`, and a recovery job retries the idempotent fulfilment until it returns a final result, mapped as in §3.3. A duplicate callback while still pending re-triggers the fulfilment. This deviates from SRS 1028 and 1869 |

### 6.1 Draft 7 edits needed (made only when Billing core is unfrozen)

| Draft 7 place | Today | Edit |
|---|---|---|
| §2 last table row (line 32) | B-1 creates the three payment tables empty | PAY-0 creates them; B-1 adds the subscription FKs |
| §11 item 1 (B-1) | "empty payment tables (agreed columns)" | Remove; add "subscription FKs on the payment tables" |
| §4 step 6 | Billing uses its own engine and pool | Exception for `PaymentFulfilmentPortV1` under option A (caller's session) |
| §7.4 last paragraph (line 157) | "The provider event receipt is written by the payment side before it calls" | Under option A, written in the same transaction as the call |
| §7.4 | Three commands, no result type | Add `FulfilmentResultV1` and the invoice-level key (§3.3) |
| §7 | No price or period read port | Add `BillingQuoteInputsPortV1` (§3.5) |
| §11 item 4 (B-4) | "Payment interface: §7.4, after agreement" | B-4 implements the Billing side of §3.3 and §3.5 only |

## 7. Routes and envelope

| Route | Auth | Body format |
|---|---|---|
| `POST /v1/payments/{provider}/callback` | Signature only; no bearer | The provider's acknowledgement format (SRS 1680), not the CONV-1 envelope. The path is the SRS path itself, in the M2 `/v1` route family (C-D9), and stays outside `CONV1_PREFIXES` by design |
| `POST /api/billing/v1/organizations/{organization_id}/subscription/checkout` | Bearer + billing permission (PD-6) | CONV-1 envelope for errors |
| `GET /api/billing/v1/payment-attempts/{payment_attempt_id}` (status) | Bearer + scope check | CONV-1 envelope for errors |

The checkout path is the C-D9 interim mapping of the SRS path `/v1/organizations/{org_id}/subscription/checkout` (PD-4). PAY-0 adds `/api/billing/v1` to `CONV1_PREFIXES`. All three routes are registered only when the settings flag is on (off by default), and work only with the fake provider in `local` and `test`.

**Checkout request `SubscriptionCheckoutRequestV1`** (SRS 1677: price version, billing period, desired capacity):

| Field | Rule |
|---|---|
| `purpose` | `ADD_ON_SLOTS` only in PAY-0 |
| `price_version_id` | The version the client was quoted; must equal the current one |
| `billing_period` | Must equal the subscription's period |
| `desired_capacity` | Total slots wanted; must exceed `current_paid_slots`; added slots = the difference |

**Checkout response 202 `CheckoutAcceptedV1`:** `payment_attempt_id`, `invoice_id`, `status` (`CREATED`), `amount_vnd`, `status_url`.

**Status response 200 `PaymentAttemptStatusV1`:** `payment_attempt_id`, `status`, `invoice_status`, `amount_vnd`, `redirect` (null until `PENDING`; otherwise `kind` `URL` or `DEEP_LINK` and `value`), `expires_at`, `safe_failure_code`.

**Interpretation I-2:** SRS 1677 returns "202 payment attempt/redirect instruction". Because `start_checkout` runs in the worker (I-1), the redirect is not known at 202 time. PAY-0 returns the attempt with a `status_url`, and the status response carries the redirect once the worker has it; the client polls.

**Errors (CONV-1 envelope; specific codes pass through `map_code`):**

| Status | Code | When |
|---|---|---|
| 400 | `INVALID_REQUEST` | Body or field invalid (non-echoing `field_errors`) |
| 400 | `IDEMPOTENCY_KEY_REQUIRED` | Header missing (CONV-1 remaps to 400) |
| 400 | `INVALID_IDEMPOTENCY_KEY` | Same key, different body (SRS 1697) |
| 403 | `ACTION_NOT_ALLOWED` | In scope but not allowed to pay (PD-6) |
| 404 | `RESOURCE_NOT_FOUND` | Route off, organization or attempt out of scope |
| 409 | `PRICE_VERSION_CHANGED` (NEW) | Request version differs from the current one |
| 409 | `SUBSCRIPTION_RESTRICTED` | No subscription (Draft 7 §9 maps `NO_SUBSCRIPTION` to it) |
| 409 | `INVALID_STATE_TRANSITION` | `desired_capacity` not above the paid slots, or `billing_period` differs |
| 503 | `BILLING_UNAVAILABLE` | Quote inputs `UNAVAILABLE` or `NO_PRICE_VERSION` (Draft 7 §9), `retryable=true` |
| 503 | `PROVIDER_UNAVAILABLE` | The provider is disabled in settings |

## 8. Events

`PaymentEventV1` (SRS 783) and `PaymentVerifiedV1` (SRS 1847) are defined as DTOs in PAY-0, with the SRS field lists. They are emitted through an outbox only once Billing core and notifications exist. FR-B-08 notifications are out of scope.

## 9. PAY-0 deliverables, in three slices

Each slice gets its own Task Approval and one commit, and goes into the one-at-a-time BE queue.

| Slice | Deliverables |
|---|---|
| **PAY-0a Foundation** | Domain value types and the §5.3 transition table as pure functions (`domain/billing/payments.py`; the architecture validator already bans framework imports in `domain/`). The ports and DTOs of §3 (`application/ports/payments.py`). Alembic migration for the three tables (branch label `billing`, independent root; the multi-head Alembic tests must accept it). Repositories. `FakePaymentProvider` with `ProviderTestKit`; a fake `BillingQuoteInputsPortV1`; a recording fake `PaymentFulfilmentPortV1` that can return each `FulfilmentResultV1`. Settings of the table below with their validator |
| **PAY-0b Callback intake** | `PaymentIntakeService` callback path (§5.2, §5.3), `CallbackAbuseLimiter`, the callback route, security events, the review transaction, and the provider contract suite |
| **PAY-0c Checkout and jobs** | Checkout and status routes (§7), the `CONV1_PREFIXES` addition, the jobs of §5.4 and the one-shot command, and the RQ enqueue |

**Settings** (env prefix `SKETCH2LIFE_`; defaults are placeholders until PD-7):

| Setting | Default |
|---|---|
| `payments_enabled` | `false` |
| `payments_fake_provider_enabled` | `false`; refused outside `local` and `test` |
| `payments_enabled_providers` | empty |
| `payments_callback_body_max_bytes` | 65,536 |
| `payments_callback_freshness_seconds` | 900 |
| `payments_callback_tx_timeout_ms` | 5,000 (must be below the provider IPN timeout; not verified) |
| `payments_invalid_callback_limit_per_minute` | 60 per (provider, source IP) |
| `payments_checkout_claim_lease_seconds` | 120 |
| `payments_stuck_created_seconds` / `payments_stuck_created_max_tries` | 300 / 3 |
| `payments_reconcile_after_seconds` / `payments_reconcile_max_tries` | 900 / 5 |
| `payments_unreconciled_warning_seconds` | 300 (SRS 2088) |
| `payments_return_url`, `payments_ipn_base_url` | empty; required when enabled with a real provider |

**Contract and integration cases.** Cases marked **PG** need a disposable PostgreSQL database (never the forbidden databases or ports); the others run on fakes.

- Callback: valid once; invalid signature (no row, no effect, security event); stale with invalid signature (no reconcile job); stale with valid signature (reconcile job enqueued once); malformed; duplicate verified event; forged first, then genuine (the genuine one succeeds); provider, amount and currency mismatch (`NEEDS_REVIEW`, capacity unchanged, ack `ACCEPTED`); unknown order (`NEEDS_REVIEW`, no target); fulfilment `REFUSED` (review transaction written); fulfilment `UNAVAILABLE` (no row, `RETRY_LATER`); review transaction failing (no row, `RETRY_LATER`); every cell of the §5.3 table; double payment; handler exception (provider-format `RETRY_LATER`); limiter never blocks `VALID` while flooded with invalid callbacks; body cap; disabled provider (404, no write); no body, header or query string in logs.
- **PG:** concurrent identical callbacks (one effect); callback and reconciliation for the same payment (one fulfilment); crash after verify and before commit (the retry succeeds); concurrent same-key checkouts (one invoice, one attempt); redelivered `payment_checkout_start` (one provider session).
- Checkout and status: idempotent replay (same 202); key with another body (400 `INVALID_IDEMPOTENCY_KEY`); missing key; price version changed; flag off (404); status of an attempt out of scope (404); half-up rounding at the .5 boundary; `start_checkout` results `ALREADY_STARTED`, `PROVIDER_REJECTED`, `UNAVAILABLE`; stuck `CREATED` with a provider payment found by `query_status`; expiry with `query_status` `SUCCEEDED`; browser return without a callback (still `OPEN`).
- Settings: the fake provider is refused outside `local` and `test`.

**Out of PAY-0:**
- Billing core (frozen), including the real `BillingQuoteInputsPortV1`, the Billing side of `PaymentFulfilmentPortV1` (B-4), and the `PAYMENT_PENDING` subscription state (SRS 399);
- real provider calls and MoMo or VNPAY code (PAY-1 onward, by the payment teammate);
- the Parent top-up purchase route `POST /v1/video-quota/purchases` (SRS 1679, Q193 gate);
- refunds and the operator review screen (PAY-3);
- the periodic scheduler (PD-9) and a shared limiter store;
- notifications, FE screens and Bruno.

## 10. Payment teammate's slices after PAY-0

| Slice | Content |
|---|---|
| PAY-1 | MoMo sandbox, one-time: signature as MoMo documents it, IPN, `query_status`; passes the contract suite |
| PAY-2 | MoMo Subscription or VNPAY recurring (OI-09); renewal receipts target the subscription |
| PAY-3 | Operator view of flagged, `NEEDS_REVIEW` and stuck attempts, and refunds |

Each needs its own Task Approval and goes into the one-at-a-time BE queue. **The real add-on checkout also needs Billing core B-1 and B-4**, which are frozen.

## 11. Owner decisions (one at a time, with the SRS sentence)

| ID | Question | Recommendation |
|---|---|---|
| PD-1 | Amend D-066-65 so that the owner's lane builds the PAY-0 skeleton, while the payment teammate still builds the adapters and the payment flows on top? | Yes, as requested; Billing core stays frozen |
| PD-2a | PAY-0 creates the three payment tables now, without subscription FKs? | Yes |
| PD-2b | Amend the register note at line 392: no receipt row for an unverified callback? | Yes |
| PD-2c | Add the NEW `payment_attempts` columns of §4 (idempotency, fingerprint, claim, review flag) to the register? | Yes |
| PD-3 | Quote stays payment-side (D-066-65), reading inputs through the new read-only `BillingQuoteInputsPortV1`, faked until B-1? | Yes |
| PD-4 | Route paths as in §7 (C-D9 interim mapping of SRS 1677)? | Yes |
| PD-5 | Fulfilment transaction: option A (one session inside the `billing` module; Draft 7 edits of §6.1) or B (recovery job)? | A |
| PD-6 | Who may start an organization checkout: "Admin billing" (SRS 1677) is still open in Draft 7 §7.5, and Parent top-up is gated by Q193 | Keep open. PAY-0 uses a permission hook, defaulting to School Manager for the fake flow only |
| PD-7 | Defaults of the §9 settings | Set with the payment teammate, from the provider documents |
| PD-8 | Queue position of PAY-0 in the one-at-a-time BE queue | After FR-C-08 and SEED-1, unless the payment teammate is blocked |
| PD-9 | Periodic job runner: who builds it and when (shared with Draft 7's open sweep runner) | Decide before PAY-0c; the flag stays off outside `local` and `test` until it exists |

## 12. Interpretations

| ID | Interpretation |
|---|---|
| I-1 | Network-facing adapter methods run in the worker; `verify_callback` and `acknowledge` are pure and run in the API process (§3.1) |
| I-2 | The 202 carries the attempt and a status URL; the redirect arrives through the status route (§7) |
| I-3 | A verified but inapplicable callback is acknowledged as received once it is durably recorded as `NEEDS_REVIEW` (§5.2 step 5) |

## 13. Not verified

- MoMo and VNPAY wire formats: HTTP method, signed fields, native event IDs, amount scaling, IPN retry count and timeout. They come from the official documents (SRS 1742).
- PostgreSQL behaviour of the lock and unique-conflict sequence (to be shown by the PG cases).
- Whether the existing multi-head Alembic tests accept another root.
- Physical column types (BLOCKED in the dictionary).
- Any edge or proxy rate limit in front of the callback path.

No code, migration, test or command was run for this draft.

## 14. Round-2 findings and their fixes

| Finding | Fixed in |
|---|---|
| PZ-01 (P1) | §5.2 steps 4(b), 4(c), 4(e) and 5 (review transaction, `NEEDS_REVIEW`, ack after durable record, `RETRY_LATER` when even that fails); §4 receipt target 0 or 1; §5.4 `payment_unreconciled_warning` (SRS 2088); §3.1 scaling note; I-3; cases |
| PZ-02 | §5.3 full transition table under the row lock; §3.3 `FulfilmentResultV1` and its mapping; double payment |
| PZ-03 | §5.2 steps 1–4 (verify first; limiter counts non-`VALID` only and never refuses `VALID`); §5.6 `CallbackAbuseLimiter` and its store; case "flooded" |
| PZ-04 | §3.5 `BillingQuoteInputsPortV1` with period, billing period, unit price and quantity basis; §3.4 snapshot fields; §6.1 |
| PZ-05 | §4 unique (principal, operation, organization, key) and NEW columns; §5.1 step 2 look-up first and conflict handling; PD-2c; cases |
| PZ-06 | §5.4 jobs table and runner; §5.1 claim compare-and-set; §3.1 `start_checkout` idempotency and results; `query_status` before failing or expiring; PD-9; PAY-0c |
| PZ-07 | §7 request and response schemas, error table, I-2, callback path and exception rule (§5.2 step 7) |
| PZ-08 | §6 reframed (one module, SRS 1012); §6.1 Draft 7 edit list |
| PZ-09 | §3.2 native event ID first; derived ref includes `merchant_order_ref`; §5.4 reconciliation ref |
| PZ-10 | §4 receipt target 0 or 1 with a `CHECK`; §10 PAY-2 subscription target |
| PZ-11 | §5.2 step 2 check order; step 3 valid-signature `STALE` triggers `payment_reconcile_one` |
| PZ-12 | §3.1 "Runs in" column and I-1 |
| PZ-13 | §9 three slices, settings names and defaults, PG requirement, added cases; §5.2 step 4 transaction timeout |
| PZ-14 | §11 PD-2 split into 2a–2c; dependency line in the header; §9 out-of-scope items (SRS 1679, SRS 399); §2 port review gate |

## 15. Round-1 findings (Draft 1) and where they are now

| Finding | Where |
|---|---|
| PY-01 (P1) | §4 departure (no receipt for unverified callbacks); §5.2 step 3; case "forged first, then genuine" |
| PY-02 (P1) | §5.2 steps 4–7; §6 option B; PG case "crash before commit"; completed by PZ-01 |
| PY-03 | §5.2 steps 1–3; §5.6 |
| PY-04 | §6 and §6.1 |
| PY-05 | §3.3 invoice-level idempotency; §5.3 table under the row lock; §5.4 reconciliation ref |
| PY-06 | §3.5; PD-3 |
| PY-07 | §2, §4 and §6.1; PD-2a |
| PY-08 | §4 states follow SRS line 400; the checkout claim is a column |
| PY-09 | §3.1 and §3.2 |
| PY-10 | §3.3 and §3.4 |
| PY-11 | §5.1, §5.4 and §7 |
| PY-12 | §3.1 `ProviderTestKit`; §9 cases |
| PY-13 | PD-6 kept open |
| PY-14 | §5.6 |
| PY-15 | §1 citations; owner request; PD-1 |
| PY-16 | §7 prefix and envelope rule; header dependency line |
| PY-17 | §5.6 and §9 validator notes |
| PY-18 | §4 VND check; §3.1 amount unit; §8 events; §9 settings; §7 error codes |
| PY-19 | §3.5 and §13 |
