# FEAT-066 PAY-0 — payment interface skeleton for the payment teammate (Draft 4)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package plans a framework only. It authorizes no code, migration, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 3 (42,718 B, `721DBE84…`). Its round-3 review was NOT READY with 0 P1, 5 P2 and 9 P3 (`evidence/notes/PAY_0_COLD_REVIEW_DRAFT3_20261118.md`, 6,887 B, `D25733EC…`). The owner chose "Draft 4 + round 4" in chat on 2026-11-18. §16 maps each round-3 finding to its fix; §14 and §15 keep the round-2 and round-1 maps.
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
| 1863–1876 (§23.2) | Quote and invoice first; the invoice stores the base price, added quantity, period start and end, remaining-time ratio, rounded VND amount and price version; proration = added slots × full-period price per slot × (remaining seconds / total seconds of the current provider period), half-up to whole VND, UTC timestamps; no activation before verification; duplicate or out-of-order callbacks never charge or activate twice (1875) |
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

Null rule: when `signature_outcome` is `VALID`, every field is non-null except `provider_transaction_ref`, which may be null only when `provider_status` is `FAILED` or `PENDING`. For any other outcome, only `provider`, `signature_outcome`, `raw_body_sha256` and `received_at` are guaranteed; the rest are filled when they could be parsed.

| Field | Meaning |
|---|---|
| `provider` | `MOMO` or `VNPAY`, from the route; must equal the attempt's provider |
| `signature_outcome` | `VALID`; `INVALID` (signature fails); `MALFORMED` (cannot be parsed, so no signature can be checked); `STALE` (signature valid, outside the freshness window); `UNPROCESSABLE` (**NEW**: signature valid, but a field check fails, for example an unmapped status, a missing currency, or `SUCCEEDED` with no transaction ref). §5.2 step 2 gives the order of checks. `STALE` and `UNPROCESSABLE` together are the **signature-proven, not applicable** class |
| `raw_body_sha256` | Digest of the exact signed bytes. The raw body is never stored or logged |
| `provider_event_ref` | The provider's native event ID when it has one. Otherwise **derived** as `merchant_order_ref` + `:` + `provider_transaction_ref` (or `-` when empty) + `:` + normalized status, so an empty transaction ID on a failure cannot collide across orders |
| `merchant_order_ref`, `provider_transaction_ref` | Links to the attempt |
| `amount_vnd`, `currency` | Checked against the attempt and the invoice snapshot |
| `provider_status` | `SUCCEEDED`, `FAILED`, `PENDING` |
| `event_time` | UTC, from the provider |
| `received_at` | UTC, from the backend |

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
| `UNAVAILABLE` | Transient (lock timeout, Billing down) | Main transaction rolls back; no row; immediate warning event (§5.2 step 6); ack `RETRY_LATER` |

The mapping assumes option A of §6 (one transaction). Option B is not specified in this draft (§6).

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
- **Interpretation I-4:** `NO_PRICE_VERSION` appears in Draft 7 §2, §7.3 and §11 item 1, but Draft 7 §9 gives it no HTTP mapping. PAY-0 maps both `NO_PRICE_VERSION` and `UNAVAILABLE` to 503 `BILLING_UNAVAILABLE`, and `NO_SUBSCRIPTION` to 409 `SUBSCRIPTION_RESTRICTED` (Draft 7 §9).

## 4. Payment tables (DDL by PAY-0 if PD-2a = yes; written only by the payment side)

All three tables live in schema `billing`, which SRS 1012 treats as one module with Billing core.

| Table | Keys and constraints | Columns |
|---|---|---|
| `billing.invoices` | PK `invoice_id`; typed owner scope and ref; unique `invoice_number`; `CHECK currency = 'VND'`; `subscription_id` a **soft ref** until B-1 adds the FK | Register (lines 390–392): `invoice_number`, `period_start`, `period_end`, `currency`, `subtotal`, `prorated_adjustment`, `total`, `status`, `due_at`, `paid_at`, `invoice_snapshot` (`InvoiceSnapshotV1`), `created_at` |
| `billing.payment_attempts` | PK `payment_attempt_id`; FK `invoice_id`, **unique** (one attempt per invoice in PAY-0); unique `merchant_order_ref`; unique provider `request_id`; **unique (`principal_account_id`, `operation`, `organization_id`, `idempotency_key`)**; **NEW partial unique (`organization_id`, `operation`) where `status` is `CREATED` or `PENDING`** (one open checkout per organization, §5.1) | Register: `provider`, `merchant_order_ref`, `provider_transaction_ref`, `request_id`, `amount`, `currency`, `status`, `idempotency_key`, `initiated_at`, `completed_at`, `safe_failure_code`. **NEW** (PD-2c): `principal_account_id`, `operation` (`ORG_SUBSCRIPTION_CHECKOUT`), `organization_id`, `request_fingerprint` (SHA-256 of the canonical request body), `checkout_claimed_at`, `checkout_tries`, `reconcile_requested_at`, `reconcile_tries`, `needs_review` (bool), `review_reason_code` |
| `billing.provider_event_receipts` | PK `event_receipt_id`; unique (`provider`, `provider_event_ref`); **0 or 1 target** (`CHECK` that at most one of `payment_attempt_id_optional` and `subscription_id_optional` is set), as in the register; `subscription_id_optional` a soft ref until B-1 | Register: `provider`, `provider_event_ref`, `signature_valid`, `payment_attempt_id_optional`, `subscription_id_optional`, `received_at`, `processed_at`, `processing_status`, `safe_error_code`, `payload_hash`. **NEW** (PD-2d), non-sensitive observed values for operator review: `observed_amount_vnd`, `observed_currency`, `observed_merchant_order_ref`, `observed_provider_transaction_ref`, `observed_provider_status` (all nullable) |

**Departures from the register, stated:**
- The register allows a receipt row for an unverified callback, with both FKs empty (line 392). PAY-0 writes **no receipt row for an unverified callback** (`INVALID` or `MALFORMED`), so a forged callback can never claim the unique key. Unverified callbacks become safe security events (§5.2), as SRS 2133–2135 asks. Asked as PD-2b.
- **`signature_valid` meaning (NEW reading):** true means "verified": either the callback signature was valid, or the row comes from an authenticated `query_status` answer. The source is visible in the event-ref prefix: native or derived ref (callback), `recon:` (reconciliation), `signed:` (signature-proven but not applicable, §5.2 step 3). It is never false in PAY-0.
- The NEW attempt columns and the partial unique index above. Asked as PD-2c.
- The NEW receipt columns above. Asked as PD-2d.

**DDL versus write ownership:** PAY-0 creates these tables (Alembic branch label `billing`, an independent root). Only the payment side writes them. B-1 later adds the core tables and the subscription FKs on the same branch label (§6.1 lists the Draft 7 edits).

**States:**

| Entity | States |
|---|---|
| Payment attempt (SRS line 400) | `CREATED`, `PENDING`, `SUCCEEDED`, `FAILED`, `EXPIRED` (transitions in §5.3). A provider cancellation is `FAILED` with a safe code. The checkout claim is a column, not a state, so the SRS state list is unchanged |
| Invoice | `OPEN` → `PAID` or `VOID`. `VOID` → `PAID` only through a late verified success (§5.3) |
| Receipt (`processing_status`; the value set is **NEW**, the register names only the column) | `PROCESSED` (a state change was applied, with or without fulfilment), `RECORDED_NO_EFFECT` (no state change), `NEEDS_REVIEW` (verified but not applicable). Written only for verified events |

## 5. Flows and safety rules

### 5.1 Checkout (SRS line 1677)

1. **Request:** `POST /api/billing/v1/organizations/{organization_id}/subscription/checkout` with an `Idempotency-Key` (§7 has the body).
2. **Synchronous part, one transaction:**
   - look up an attempt by (principal, `ORG_SUBSCRIPTION_CHECKOUT`, organization, key). If found with the same `request_fingerprint`, return the same 202 body. If found with another fingerprint, return 400 `INVALID_IDEMPOTENCY_KEY` (SRS 1697);
   - take the organization checkout lock (§5.3);
   - **one open checkout per organization (SRS 1875):** if the organization already has an attempt `CREATED` or `PENDING` for this operation, return 409 `CHECKOUT_IN_PROGRESS` (**NEW**) with `retryable=true` and `retry_after_seconds` until that attempt's `expires_at` (or the claim lease when it has none). The partial unique index of §4 enforces the same rule under concurrency: a conflicting insert rolls back and the request answers 409;
   - read `BillingQuoteInputsPortV1` and compute the quote;
   - create an `OPEN` invoice with the snapshot;
   - create a `CREATED` attempt (the unique keys are inserted here; a concurrent same-key insert conflicts, the transaction rolls back, and the request re-reads and answers as in the first point);
   - after commit, enqueue the `payment_checkout_start` job. If the enqueue fails, the request still returns 202, logs at error level, and the sweep (step 4) starts the attempt later;
   - return **202** (§7).
3. **Worker job `payment_checkout_start`** (SRS 752, 936):
   - claim the attempt with a compare-and-set: set `checkout_claimed_at` only where the status is `CREATED` and there is no claim younger than the lease (settings). A redelivered job that loses the claim does nothing (SRS 2170 RQ redelivery);
   - call `start_checkout` **outside any lock**, then apply its result under the job-transition rule of §5.4. `STARTED`: store the session and move the attempt `CREATED` → `PENDING`. `ALREADY_STARTED`: call `query_status` and pass a payment status through §5.2 step 4 as a `recon:` event; if the provider has no payment and the session was not stored, move the attempt `CREATED` → `FAILED` with `CHECKOUT_SESSION_LOST` and the invoice `OPEN` → `VOID` (the client starts a new checkout with a new key). `PROVIDER_REJECTED`: `CREATED` → `FAILED` with the safe code, invoice `VOID`. `UNAVAILABLE`: release the claim and let the sweep retry.
4. **Sweep job `payment_stuck_created_sweep`:** an attempt still `CREATED` past a threshold is re-enqueued, up to `payments_stuck_created_max_tries`. On the last try the sweep calls `query_status`: a provider payment goes through §5.2 step 4 with a `recon:` ref, never to `FAILED`; `NOT_FOUND` moves the attempt to `FAILED` (`CHECKOUT_NOT_STARTED`) and the invoice to `VOID`; `UNAVAILABLE` sets `needs_review` with `SWEEP_EXHAUSTED` and leaves the attempt `CREATED` (it keeps blocking a new checkout until an operator resolves it, PAY-3).

### 5.2 Callback (`POST /v1/payments/{provider}/callback`)

1. **Before verification:**
   - `provider` must be an enabled adapter; otherwise 404 with an empty body and no write;
   - the body is capped (settings, default 64 KiB): a `Content-Length` above the cap is refused at once, and the body is read as a stream that stops at the cap, so a missing or false header cannot bypass it. Over the cap: 413 with an empty body, a security event with outcome `OVERSIZE`, counted by the limiter. Verification is an HMAC over at most that many bytes, so it is cheap.
2. **`verify_callback`**, in this order: parse (failure → `MALFORMED`); signature over the exact bytes (failure → `INVALID`, whatever the age); freshness window (failure → `STALE`); field checks, including the null rule of §3.2 (failure → `UNPROCESSABLE`).
3. **Outcome other than `VALID`:**
   - **`INVALID` or `MALFORMED` (signature not proven):**
     - no database row;
     - a **safe security event** (counter and structured log with `provider`, `signature_outcome`, `raw_body_sha256`, source IP only);
     - the abuse limiter (§5.6) counts it; over the limit, the response is 429 with an empty body and a `Retry-After` header, and the security event is aggregated;
     - the provider-format rejection is returned. Nothing changes state (SRS 2133–2135).
   - **`STALE` or `UNPROCESSABLE` (signature proven, not applicable):** never counted by the limiter. In one small transaction:
     - if `merchant_order_ref` names an existing attempt, set its `reconcile_requested_at` (if not already set). This is the durable request that the reconciliation pass serves first (§5.4), and the dedupe store for the immediate hint;
     - if the attempt is unknown, or the outcome is `UNPROCESSABLE`, also insert a `NEEDS_REVIEW` receipt with `provider_event_ref` = `signed:` + `raw_body_sha256` (target = the attempt when known), the reason code, and the observed values that could be parsed. A redelivery of the same bytes is a unique conflict, which means `DUPLICATE`;
     - after commit, enqueue `payment_reconcile_one` when an attempt is known (best effort; the durable column covers a failed enqueue);
     - emit an immediate warning event `PAYMENT_SIGNED_CALLBACK_NOT_APPLIED` (provider, `raw_body_sha256`, outcome, reason code);
     - acknowledge: `STALE` with a known attempt → `REJECTED` (reconciliation recovers it); otherwise `ACCEPTED` once the receipt is committed. If this small transaction fails: warning event `PAYMENT_VALID_CALLBACK_UNRECORDED` at error level, and `RETRY_LATER`.
4. **`VALID`:** the limiter is never applied (SRS 995). In **one transaction** (the main transaction, with a timeout from settings that must stay below the provider's IPN timeout):
   - (a) insert the receipt. A unique conflict means the same verified event was already committed, so acknowledge `DUPLICATE` with no effect;
   - (b) resolve the attempt by `merchant_order_ref`; for a `SUCCEEDED` event take the organization checkout lock (§5.3); then lock the attempt (`SELECT … FOR UPDATE`) and its invoice. **Unresolvable** (no attempt) → go to step 5 with reason `UNKNOWN_ORDER`;
   - (c) check provider, amount and currency against the attempt and the invoice snapshot. **Mismatch** → go to step 5 with reason `PROVIDER_MISMATCH`, `AMOUNT_MISMATCH` or `CURRENCY_MISMATCH`. Capacity is unchanged, as SRS 2137 asks;
   - (d) apply the transition table of §5.3 to the locked state. Because the rows are locked, a concurrent second receipt (callback and reconciliation) waits and is then judged against the new state; no compare-and-set can fail half-way;
   - (e) fulfilment (option A of §6), mapped by `FulfilmentResultV1` (§3.3). `REFUSED` → step 5 with the refusal code; `UNAVAILABLE` → step 6.
5. **Review transaction (verified but not applicable):** roll back the main transaction, then in a **separate small transaction** insert the receipt as `NEEDS_REVIEW` with the safe reason code and the observed values (target = the attempt when known, none otherwise), and set `needs_review` and `review_reason_code` on the attempt when it exists. After commit, emit an immediate warning event `PAYMENT_NEEDS_REVIEW` (provider, event ref, reason code). Acknowledge `ACCEPTED` (the event is durably recorded; a provider retry would be a `DUPLICATE`).
   - A unique conflict inside the review transaction means a concurrent request already recorded the same event: acknowledge `DUPLICATE`.
   - Any other failure of the review transaction goes to step 6.
6. **Verified but unrecorded exit:** whenever a `VALID` callback ends with nothing committed (main transaction failure, fulfilment `UNAVAILABLE`, review transaction failure, or an exception after verification), emit an immediate warning event `PAYMENT_VALID_CALLBACK_UNRECORDED` at error level (provider, `provider_event_ref`, `raw_body_sha256`, reason code), and, when the attempt is known, try to set its `reconcile_requested_at` in a separate statement. Acknowledge `RETRY_LATER`, so the provider retries and the retry is processed as new. This event is the SRS 2088 signal for the case where no row exists for the periodic job to find.
7. **Acknowledge only after a transaction commits**, except `RETRY_LATER` and the unverified rejections of step 3.
8. **Exceptions:** the callback handler catches every exception, applies step 6 when the outcome was `VALID`, and returns `acknowledge(RETRY_LATER)` in the provider format, with no body echo. The app's plain-text 500 for non-CONV-1 paths (`app.py:812`) is never reached from this route.

### 5.3 Transition table (event status × attempt state, applied under the row lock)

| Event status ↓ / attempt → | `CREATED` | `PENDING` | `SUCCEEDED`, same `provider_transaction_ref` | `SUCCEEDED`, other `provider_transaction_ref` | `FAILED` | `EXPIRED` |
|---|---|---|---|---|---|---|
| `SUCCEEDED` | → `SUCCEEDED`, invoice `PAID`, fulfil (the provider has the money; the worker may have died before storing `PENDING`) | → `SUCCEEDED`, invoice `PAID`, fulfil | no change; fulfil returns `ALREADY_APPLIED` → `RECORDED_NO_EFFECT` | **double payment**: no change, no fulfil; review transaction with `DOUBLE_PAYMENT` | If another invoice for the same organization and purpose was paid after this attempt ended: no change, no fulfil; review transaction with `SUPERSEDED_LATE_SUCCESS` (the money needs an operator refund, PAY-3). Otherwise → `SUCCEEDED`, invoice `VOID` → `PAID`, fulfil, flag `LATE_SUCCESS` | same as `FAILED` |
| `FAILED` | → `FAILED`, invoice `VOID` | → `FAILED`, invoice `VOID` | `RECORDED_NO_EFFECT`, flag `FAILED_AFTER_SUCCESS` | `RECORDED_NO_EFFECT`, flag `FAILED_AFTER_SUCCESS` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` |
| `PENDING` | → `PENDING`, store `provider_transaction_ref` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` | `RECORDED_NO_EFFECT` |

- Every "flag" sets `needs_review` and `review_reason_code` on the attempt in the main transaction, and the receipt state is the one the fulfilment result gives.
- **Receipt state for cells without fulfilment:** a cell that changes state (`→ FAILED`, `→ PENDING`) writes the receipt as `PROCESSED`; a cell marked `RECORDED_NO_EFFECT` writes that state.
- **Superseded:** an ended attempt (`FAILED` or `EXPIRED`) is superseded when a newer attempt of the same organization and operation exists in `CREATED`, `PENDING` or `SUCCEEDED`. Paying the old one too would add slots twice (SRS 1875).
- **Organization checkout lock (NEW):** checkout (§5.1 step 2) and every `SUCCEEDED` event take a transaction-level PostgreSQL advisory lock keyed on (organization, operation) before any attempt row lock. So a new checkout and a late success for the same organization cannot interleave, and the quote of a new checkout always sees a committed late fulfilment. Lock order for callbacks: receipt insert, organization checkout lock, attempt, invoice, Billing subscription lock. The organization is read from the attempt without a lock first, then the lock is taken.
- A fulfilment after a late success may return `REFUSED` or `RECORDED_NO_EFFECT` (for example the period ended); both leave the attempt flagged. Refunds are an operator action and out of PAY-0.
- All acknowledgements in this table are `ACCEPTED`, except a receipt unique conflict (`DUPLICATE`) and a transient failure (`RETRY_LATER`).

### 5.4 Background jobs (deliverables, §9)

| Job | Trigger | Rule |
|---|---|---|
| `payment_checkout_start` | Enqueued after the checkout commit | §5.1 step 3 |
| `payment_stuck_created_sweep` | Periodic | §5.1 step 4 |
| `payment_reconcile_pending` | Periodic | First every attempt with `reconcile_requested_at` set, then attempts `PENDING` (or `CREATED` with a claim) older than the threshold: call `query_status`. `SUCCEEDED`, `FAILED`, `PENDING` go through §5.2 steps 4–6 with the event ref `recon:` + `merchant_order_ref` + `:` + `provider_transaction_ref` (or `-`) + `:` + status. A `recon:` ref that already exists is a `DUPLICATE`, so the job is idempotent. A terminal result clears `reconcile_requested_at`. Each call increments `reconcile_tries`, with backoff; at `payments_reconcile_max_tries` the attempt gets `needs_review` with `RECONCILE_EXHAUSTED` and a `PAYMENT_NEEDS_REVIEW` warning event |
| `payment_reconcile_one` | Enqueued by a signature-proven callback (§5.2 step 3) or step 6 | Same as above, for one attempt |
| `payment_expire` | Periodic | An attempt past `expires_at`: call `query_status` first. `SUCCEEDED` and `FAILED` go through §5.2 step 4; `NOT_FOUND` → `EXPIRED`, invoice `VOID` (a direct write under the job-transition rule); provider `PENDING` → leave it `PENDING` and retry until `payments_expire_grace_seconds` after `expires_at`, then set `needs_review` with `EXPIRY_PROVIDER_PENDING` (never expire an attempt the provider still holds open); `UNAVAILABLE` → try later, never expire blind |
| `payment_unreconciled_warning` | Periodic | Emits a warning metric and log for: every receipt in `NEEDS_REVIEW`; every attempt with `needs_review`; every attempt with a `SUCCEEDED` receipt (observed or applied) whose invoice is not `PAID` after 5 minutes (SRS 2088); every attempt whose `reconcile_requested_at` is older than 5 minutes. Routine `PENDING` receipts do not count |

**Job-transition rule (every worker and job write):** network calls (`start_checkout`, `query_status`) run outside any lock. The result is then applied in a transaction that takes the organization checkout lock when the result is `SUCCEEDED`, locks the attempt and then its invoice (`SELECT … FOR UPDATE`), and writes only if the attempt status still equals the status the job observed before its call (`WHERE status = observed`). If the status changed (for example a callback committed `SUCCEEDED` meanwhile), the job writes nothing itself and, when it holds a provider status, passes it through §5.2 step 4 as a `recon:` event, so the §5.3 table decides. Provider payment statuses (`SUCCEEDED`, `FAILED`, `PENDING`) always enter through §5.2 step 4, never by a direct status write. Direct writes are limited to outcomes that carry no provider payment status: the `start_checkout` results, `NOT_FOUND`, and the review flags.

**Runner:** PAY-0 delivers the job functions, the RQ enqueue for `payment_checkout_start` and `payment_reconcile_one`, and a one-shot command that runs the periodic jobs once. The **periodic scheduler** that calls that command is not in PAY-0; Draft 7 also leaves its sweep runner open. PD-9a and PD-9b ask for it. Until it exists, the provider's IPN retries and the immediate warning events of §5.2 are the only recovery and signal in a deployed environment. This is enforced, not only stated: the settings validator refuses `payments_enabled` outside `local` and `test` unless `payments_periodic_runner_configured` is true (§9).

### 5.5 Browser return

The status route reads only. Without a verified event the invoice stays `OPEN` and the UI shows "pending" (SRS 589, 1137, 1868). An attempt with `needs_review` shows "pending" as well, even when the money was received; the reason code is never shown to the client. Resolving and re-driving a `NEEDS_REVIEW` receipt (a re-drive cannot reuse the same event ref, which is unique) is an operator action in PAY-3.

### 5.6 Abuse limiter, logging and secrets

- **`CallbackAbuseLimiter`** (infrastructure component, NEW): an in-process token bucket keyed by (provider, source IP), and a per-provider counter, both counting **only the signature-not-proven outcomes** (`INVALID`, `MALFORMED`, `OVERSIZE`). It follows the existing in-process pattern of `RegistrationRateLimiter` (`interfaces/http/routers/auth_registration.py:61`). A signature-proven callback (`VALID`, `STALE`, `UNPROCESSABLE`) is never refused by it (SRS 995). The source IP is the direct peer address (`request.client.host`), the same rule `RegistrationRateLimiter` uses; trusting a forwarded header behind a proxy is a deployment item (not verified). A shared store (Redis) is out of PAY-0; with several API processes the limit is per process. Any edge or proxy rate limit outside the app must exempt or raise the limit for the callback path (not verified; deployment item).
- No body, headers, query string or credential is logged (SRS 942).
- Security events carry opaque refs, digests and the source IP only.
- Merchant IDs, partner codes, callback URLs and key references come from settings or the environment; none are in Git.
- The fake provider's test key is generated at run time (not an uppercase secret-like constant, so the security validator applies cleanly).
- A settings validator refuses the fake provider outside `local` and `test`, following the existing `modal_dev` pattern in `infrastructure/config/settings.py`.

## 6. Fulfilment transaction (PD-5)

SRS 1028 and 1869 ask for the receipt and the invoice/subscription update in one transaction. SRS 1012 places invoices, payments and provider receipts in the same `billing` module as subscriptions, so **option A is a transaction inside one module**. It conflicts only with Draft 7's own rules: §4 step 6 gives Billing core its own engine and pool, and §7.4 says the receipt is written by the payment side before it calls.

**This draft specifies option A only:** the payment intake and Billing core share one database session for the fulfilment call. Billing's `PaymentFulfilmentPortV1` accepts the caller's session. Lock order: receipt insert, organization checkout lock (§5.3), attempt, invoice, then the Billing subscription lock; no BE1 lock is held. `UNAVAILABLE` rolls back everything (§5.2 step 6).

**Not specified — option B (separate transactions with a recovery job):** it deviates from SRS 1028 and 1869, and would need its own receipt state, recovery job and runner, a stale-pending warning, a different duplicate rule for §5.2 step 4(a), and a `REFUSED` mapping after commit. If the owner refuses option A in PD-5, a further draft is needed before PAY-0b.

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
| `GET /api/billing/v1/payment-attempts/{payment_attempt_id}` (status; **NEW**, the SRS has no status path — needed by I-2) | Bearer + scope check | CONV-1 envelope for errors |

The checkout path is the C-D9 interim mapping of the SRS path `/v1/organizations/{org_id}/subscription/checkout` (PD-4). PAY-0 adds `/api/billing/v1` to `CONV1_PREFIXES`. All three routes are registered only when the settings flag is on (off by default), and work only with the fake provider in `local` and `test`.

**Checkout request `SubscriptionCheckoutRequestV1`** (SRS 1677: price version, billing period, desired capacity):

| Field | Rule |
|---|---|
| `purpose` (**NEW**; not in SRS 1677) | `ADD_ON_SLOTS` only in PAY-0; kept so renewal and top-up can share the contract later |
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
| 400 | `INVALID_REQUEST` with field error `Idempotency-Key` / `REQUIRED` (or `INVALID_FORMAT`) | Header missing or malformed. The route raises `IDEMPOTENCY_KEY_REQUIRED` and CONV-1 `normalize_http_error` turns it into this public form; `IDEMPOTENCY_KEY_REQUIRED` is never a public code |
| 400 | `INVALID_IDEMPOTENCY_KEY` | Same key, different body (SRS 1697) |
| 403 | `ACTION_NOT_ALLOWED` | In scope but not allowed to pay (PD-6) |
| 404 | `RESOURCE_NOT_FOUND` | Route off, organization or attempt out of scope |
| 409 | `PRICE_VERSION_CHANGED` (NEW) | Request version differs from the current one |
| 409 | `CHECKOUT_IN_PROGRESS` (NEW) | Another checkout of this organization is `CREATED` or `PENDING` (§5.1); `retryable=true` with `retry_after_seconds` |
| 409 | `SUBSCRIPTION_RESTRICTED` | `NO_SUBSCRIPTION` (Draft 7 §9 maps it here) |
| 409 | `INVALID_STATE_TRANSITION` | `desired_capacity` not above the paid slots, or `billing_period` differs |
| 503 | `BILLING_UNAVAILABLE` | Quote inputs `UNAVAILABLE` or `NO_PRICE_VERSION` (I-4), `retryable=true` |
| 503 | `PROVIDER_UNAVAILABLE` | The provider is disabled in settings |

`PRICE_VERSION_CHANGED`, `CHECKOUT_IN_PROGRESS`, `SUBSCRIPTION_RESTRICTED` and `BILLING_UNAVAILABLE` are not yet in the CONV-1 message sets (`MESSAGES` or `STATUS_MESSAGE_ONLY` in `error_envelope.py`), so the envelope coverage test would fail. PAY-0c adds a safe Vietnamese message for each (an edit to `error_envelope.py`, listed in §9).

## 8. Events

`PaymentEventV1` (SRS 783) and `PaymentVerifiedV1` (SRS 1847) are defined as DTOs in PAY-0, with the SRS field lists. They are emitted through an outbox only once Billing core and notifications exist. FR-B-08 notifications are out of scope.

## 9. PAY-0 deliverables, in three slices

Each slice gets its own Task Approval and one commit, and goes into the one-at-a-time BE queue.

| Slice | Deliverables |
|---|---|
| **PAY-0a Foundation** | Domain value types and the §5.3 transition table as pure functions (`domain/billing/payments.py`; the architecture validator already bans framework imports in `domain/`). The ports and DTOs of §3 (`application/ports/payments.py`). Alembic migration for the three tables (branch label `billing`, independent root; the multi-head Alembic tests must accept it). Repositories. `FakePaymentProvider` with `ProviderTestKit`; a fake `BillingQuoteInputsPortV1`; a recording fake `PaymentFulfilmentPortV1` that can return each `FulfilmentResultV1`. Settings of the table below with their validator |
| **PAY-0b Callback intake** | `PaymentIntakeService` callback path (§5.2, §5.3), `CallbackAbuseLimiter`, the callback route, security and warning events, the review transaction, the `reconcile_requested_at` write, and the provider contract suite. The reconcile hint goes through a `ReconcileEnqueuePortV1` that PAY-0b tests with a recording fake; the job itself is PAY-0c |
| **PAY-0c Checkout and jobs** | Checkout and status routes (§7), the organization checkout lock, the `CONV1_PREFIXES` addition, the new codes' messages in `error_envelope.py`, the jobs of §5.4 with the job-transition rule, the one-shot command, the RQ enqueue (the real `ReconcileEnqueuePortV1`) |

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
| `payments_expire_grace_seconds` | 3,600 |
| `payments_unreconciled_warning_seconds` | 300 (SRS 2088) |
| `payments_periodic_runner_configured` | `false`; while false, the validator refuses `payments_enabled` outside `local` and `test` (PD-9b) |
| `payments_return_url`, `payments_ipn_base_url` | empty; required when enabled with a real provider |

**Contract and integration cases.** Cases marked **PG** need a disposable PostgreSQL database (never the forbidden databases or ports); the others run on fakes.

- Callback (PAY-0b): valid once; invalid signature (no row, no effect, security event, counted by the limiter); stale with invalid signature (no row, no `reconcile_requested_at`); stale with valid signature and a known attempt (`reconcile_requested_at` set once, hint sent to the recording enqueue fake, ack `REJECTED`, not counted by the limiter); stale with valid signature and an unknown order (`signed:` `NEEDS_REVIEW` receipt); `UNPROCESSABLE` (for example `SUCCEEDED` with no transaction ref: `signed:` `NEEDS_REVIEW` receipt, warning event); malformed; duplicate verified event; forged first, then genuine (the genuine one succeeds); provider, amount and currency mismatch (`NEEDS_REVIEW` with observed values, capacity unchanged, ack `ACCEPTED`, warning event); unknown order (`NEEDS_REVIEW`, no target); fulfilment `REFUSED` (review transaction written); fulfilment `UNAVAILABLE` (no row, `RETRY_LATER`, `PAYMENT_VALID_CALLBACK_UNRECORDED` event); review transaction failing (same); unique conflict inside the review transaction (`DUPLICATE`); every cell of the §5.3 table, including a `VALID` `PENDING` event, late success after `FAILED` and after `EXPIRED` (fulfilled and flagged), and superseded late success (`NEEDS_REVIEW`, no fulfilment); receipt state `PROCESSED` for `→ FAILED` and `→ PENDING`; double payment; handler exception (provider-format `RETRY_LATER`, warning event); limiter never blocks a signature-proven callback while flooded with invalid ones; body cap by header and by stream (413, `OVERSIZE`); 429 body and `Retry-After`; disabled provider (404, no write); no body, header or query string in logs.
- **PG:** concurrent identical callbacks (one effect); callback and reconciliation for the same payment (one fulfilment); crash after verify and before commit (the retry succeeds); concurrent same-key checkouts (one invoice, one attempt); concurrent different-key checkouts for one organization (one open checkout, the other 409); late success racing a new checkout (no double activation); redelivered `payment_checkout_start` (one provider session); expiry racing a `SUCCEEDED` callback (the callback wins, no `VOID`).
- Checkout, status and jobs (PAY-0c): idempotent replay (same 202); key with another body (400 `INVALID_IDEMPOTENCY_KEY`); missing key (400 `INVALID_REQUEST` with the `Idempotency-Key` field error); `CHECKOUT_IN_PROGRESS`; price version changed; flag off (404); status of an attempt out of scope (404); half-up rounding at the .5 boundary; enqueue failure after commit (202, sweep recovers); `start_checkout` results `ALREADY_STARTED`, `PROVIDER_REJECTED`, `UNAVAILABLE`; stuck `CREATED` with a provider payment found by `query_status`, with `NOT_FOUND`, and with `UNAVAILABLE` on the last try (`SWEEP_EXHAUSTED`); reconcile served first for `reconcile_requested_at`; reconcile exhaustion (`RECONCILE_EXHAUSTED`); expiry with `query_status` `SUCCEEDED`, `NOT_FOUND`, and provider `PENDING` past the grace (`EXPIRY_PROVIDER_PENDING`); the warning predicate (fires for the four listed cases, not for routine `PENDING`); the new codes have messages (envelope coverage test); browser return without a callback (still `OPEN`).
- Settings: the fake provider is refused outside `local` and `test`; `payments_enabled` is refused outside `local` and `test` while `payments_periodic_runner_configured` is false.

**Out of PAY-0:**
- Billing core (frozen), including the real `BillingQuoteInputsPortV1`, the Billing side of `PaymentFulfilmentPortV1` (B-4), and the `PAYMENT_PENDING` subscription state (SRS 399);
- real provider calls and MoMo or VNPAY code (PAY-1 onward, by the payment teammate);
- the Parent top-up purchase route `POST /v1/video-quota/purchases` (SRS 1679, Q193 gate);
- refunds, the operator review screen and the re-drive of `NEEDS_REVIEW` receipts (PAY-3);
- the periodic scheduler (PD-9a, PD-9b) and a shared limiter store;
- option B of §6;
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
| PD-2c | Add the NEW `payment_attempts` columns and the one-open-checkout partial unique index of §4 to the register? | Yes |
| PD-2d | Add the NEW observed-value columns of `provider_event_receipts` (§4) to the register? | Yes |
| PD-3a | Does the quote stay payment-side, as D-066-65 says? | Yes |
| PD-3b | Add the new read-only Billing port `BillingQuoteInputsPortV1` (§3.5), with only a fake implementation until B-1? | Yes |
| PD-4 | Route paths as in §7 (C-D9 interim mapping of SRS 1677, plus the NEW status route)? | Yes |
| PD-5 | Accept option A for the fulfilment transaction (one session inside the `billing` module, with the Draft 7 edits of §6.1)? | Yes. A "no" needs a further draft (§6) |
| PD-6 | Who may start an organization checkout: "Admin billing" (SRS 1677) is still open in Draft 7 §7.5, and Parent top-up is gated by Q193 | Keep open. PAY-0 uses a permission hook, defaulting to School Manager for the fake flow only |
| PD-7 | Defaults of the §9 settings | Set with the payment teammate, from the provider documents |
| PD-8 | Queue position of PAY-0 in the one-at-a-time BE queue | After FR-C-08 and SEED-1, unless the payment teammate is blocked |
| PD-9a | Who builds the periodic job runner (shared with Draft 7's open sweep runner)? | Owner's lane, as a small separate slice after PAY-0c |
| PD-9b | Must the runner exist before `payments_enabled` may be on outside `local` and `test`? | Yes, enforced by the settings validator (§9) |

## 12. Interpretations

| ID | Interpretation |
|---|---|
| I-1 | Network-facing adapter methods run in the worker; `verify_callback` and `acknowledge` are pure and run in the API process (§3.1) |
| I-2 | The 202 carries the attempt and a status URL; the redirect arrives through the status route (§7) |
| I-3 | A verified but inapplicable callback is acknowledged as received once it is durably recorded as `NEEDS_REVIEW` (§5.2 steps 3 and 5) |
| I-4 | `NO_PRICE_VERSION` maps to 503 `BILLING_UNAVAILABLE` (§3.5) |
| I-5 | `signature_valid` means "verified", by a callback signature or by an authenticated status query (§4) |

## 13. Not verified

- MoMo and VNPAY wire formats: HTTP method, signed fields, native event IDs, amount scaling, IPN retry count and timeout. They come from the official documents (SRS 1742).
- PostgreSQL behaviour of the lock and unique-conflict sequence (to be shown by the PG cases).
- Whether the existing multi-head Alembic tests accept another root.
- Physical column types (BLOCKED in the dictionary).
- Any edge or proxy rate limit in front of the callback path, and whether a trusted proxy changes the source IP.
- Whether a provider omits the currency in callbacks (if so, the adapter supplies `VND` for that provider, or the callback becomes `UNPROCESSABLE`).

No code, migration, test or command was run for this draft.

## 14. Round-2 findings and their fixes

| Finding | Fixed in |
|---|---|
| PZ-01 (P1) | §5.2 steps 4(b), 4(c), 4(e) and 5 (review transaction, `NEEDS_REVIEW`, ack after durable record, `RETRY_LATER` when even that fails); §4 receipt target 0 or 1; §5.4 `payment_unreconciled_warning` (SRS 2088); §3.1 scaling note; I-3; cases |
| PZ-02 | §5.3 full transition table under the row lock; §3.3 `FulfilmentResultV1` and its mapping; double payment |
| PZ-03 | §5.2 steps 1–4 (verify first; the limiter counts only signature-not-proven outcomes and never refuses a signature-proven callback); §5.6 `CallbackAbuseLimiter` and its store; case "flooded" |
| PZ-04 | §3.5 `BillingQuoteInputsPortV1` with period, billing period, unit price and quantity basis; §3.4 snapshot fields; §6.1 |
| PZ-05 | §4 unique (principal, operation, organization, key) and NEW columns; §5.1 step 2 look-up first and conflict handling; PD-2c; cases |
| PZ-06 | §5.4 jobs table and runner; §5.1 claim compare-and-set; §3.1 `start_checkout` idempotency and results; `query_status` before failing or expiring; PD-9a and PD-9b; PAY-0c |
| PZ-07 | §7 request and response schemas, error table, I-2, callback path and exception rule (§5.2 step 8) |
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
| PY-02 (P1) | §5.2 steps 4–8; §6 (option A only); PG case "crash before commit"; completed by PZ-01 and QA-01/QA-02 |
| PY-03 | §5.2 steps 1–3; §5.6 |
| PY-04 | §6 and §6.1 |
| PY-05 | §3.3 invoice-level idempotency; §5.3 table under the row lock; §5.4 reconciliation ref |
| PY-06 | §3.5; PD-3a and PD-3b |
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

## 16. Round-3 findings and their fixes

| Finding | Fixed in |
|---|---|
| QA-01 (P2) | §3.2 `UNPROCESSABLE` and the null rule; §5.2 step 3 signature-proven class: durable `reconcile_requested_at`, `signed:` `NEEDS_REVIEW` receipt for an unknown order or `UNPROCESSABLE`, warning event; §4 NEW columns; §5.4 reconcile serves requested attempts first |
| QA-02 (P2) | §5.2 step 6 `PAYMENT_VALID_CALLBACK_UNRECORDED` at every verified-but-unrecorded exit; step 5 `PAYMENT_NEEDS_REVIEW`; §5.4 `RECONCILE_EXHAUSTED`, `SWEEP_EXHAUSTED`, tighter warning predicate; §9 `payments_periodic_runner_configured` validator; PD-9b |
| QA-03 (P2) | §6 specifies option A only; option B marked not specified, needing a further draft; `FULFILMENT_PENDING` removed; PD-5 is a single yes/no; §9 out of scope |
| QA-04 (P2) | §5.4 job-transition rule (network outside the lock; lock attempt then invoice; `WHERE status = observed`; provider statuses only through §5.2 step 4); §5.1 step 3 and §5.4 rows use it; PG case "expiry racing a callback" |
| QA-05 (P2) | §4 partial unique index; §5.1 step 2 one open checkout and 409 `CHECKOUT_IN_PROGRESS`; §5.3 superseded late success and the organization checkout lock; §6 lock order; PG cases |
| QA-06 | §4 NEW observed-value receipt columns (PD-2d); §5.5 re-drive is PAY-3; customer sees "pending" stated |
| QA-07 | §7 error table: missing key is 400 `INVALID_REQUEST` with the field error; new-code messages added to PAY-0c; I-4 replaces the wrong Draft 7 §9 citation |
| QA-08 | §5.2 step 5: a unique conflict in the review transaction means `DUPLICATE` |
| QA-09 | §5.2 steps 1 and 3 (413 by header and stream, `OVERSIZE`, 429 with empty body and `Retry-After`); §5.6 source IP rule; signature-proven callbacks are never counted, so no "`STALE` over the limit" case remains |
| QA-10 | §9 PAY-0b uses `ReconcileEnqueuePortV1` with a recording fake, the job is PAY-0c; added cases; §5.3 receipt state for cells without fulfilment |
| QA-11 | §4 `processing_status` value set marked NEW; §7 `purpose` and the status route marked NEW; §4 and I-5 `signature_valid` meaning and ref prefixes |
| QA-12 | §11 PD-3 split into 3a and 3b; PD-9 split into 9a and 9b; PD-5 made a single ask |
| QA-13 | §3.2 null rule (`SUCCEEDED` needs a transaction ref); §5.4 expiry with provider `PENDING` uses a grace period, then `EXPIRY_PROVIDER_PENDING` |
| QA-14 | §5.1 step 2: enqueue failure still returns 202, logs at error level, and the sweep recovers |
