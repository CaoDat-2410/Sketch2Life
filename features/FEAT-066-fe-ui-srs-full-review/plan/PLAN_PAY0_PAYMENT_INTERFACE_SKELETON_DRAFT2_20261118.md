# FEAT-066 PAY-0 — payment interface skeleton for the payment teammate (Draft 2)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. This package plans a framework only. It authorizes no code, migration, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Supersedes:** Draft 1 (15,542 B, `990A107B…`). Its round-1 review was NOT READY with 2 P1, 12 P2 and 5 P3 (`evidence/notes/PAY_0_COLD_REVIEW_DRAFT1_20261118.md`). §13 maps each finding to its fix.
- **Owner request:** "khởi động lại làm khung payment đi" (chat, 2026-11-18). The owner wants a framework that lets the payment teammate (HieuNewBie) build MoMo and then VNPAY.
- **Relation to D-066-65:** D-066-65 records the owner's words "payment tk khác làm nên tôi ko đụng", and assigns payment (quote, invoice, checkout, provider callbacks) to the payment teammate. **Building this skeleton in the owner's lane is therefore an amendment to D-066-65**, asked as PD-1. Billing core (B-1 to B-5) stays frozen.

## 1. Authority

| Input | Pin or location |
|---|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 B, `B9B1F42D…` |
| Data table register | `.../artifacts/DATA_TABLE_REGISTER.md`, 171,609 B, `7CDFDBEC…`, lines 390–392 and 460–462 |
| Physical data dictionary (draft) | `.../artifacts/PHYSICAL_DATA_DICTIONARY_DRAFT_REV57_20261109.md`, 53,694 B, `DDBF2E7D…`, lines 94–96. Logical fields only; the DDL is still BLOCKED |
| Billing contract | `plan/PLAN_L2_BILLING_CONTRACT_DRAFT7_20261118.md` (49,498 B, `216B33D7…`, closed without review): §1, §2, §4 step 6, §7.4, §7.5, §11 |
| Decisions | D-066-65 (lanes, O-PAY), D-066-66, D-066-68 (conventions), D-066-71 (CONV-1 envelope) |

**SRS clauses used:**

| Line | Content |
|---|---|
| 167, 205 | MoMo and VNPAY; the callback goes to the backend; the redirect only shows status |
| BR-28 (272) | VND; MoMo and VNPAY are the V1 adapters; no VietQR |
| 400 | PaymentAttempt states: CREATED, PENDING, SUCCEEDED, FAILED, EXPIRED |
| 587–591, 599 | FR-B-01 to FR-B-05 and FR-B-13 |
| 752, 936 | Provider adapters run only in the backend worker; no credential reaches a client |
| 783, 1847 | `PaymentEventV1` and `PaymentVerifiedV1` |
| 811 | `/v1/payments/{provider}/callback` |
| 937, 1028, 1869 | Signature verified; unique provider event; receipt and invoice/subscription update in one idempotent transaction |
| 942 | No request body, Authorization header or payment credential in logs |
| 995 | A per-provider abuse and replay policy for payment callbacks; a valid retry is never refused because of the generic unauthenticated bucket |
| 1137 (AC-14), 1221 (OI-09), 1271 | Acceptance; open merchant and recurring items; MoMo Subscription and VNPAY recurring documents |
| 1677 | `POST /v1/organizations/{org_id}/subscription/checkout`: "Admin billing"; returns 202 with the payment attempt and redirect instruction |
| 1680 | `POST /v1/payments/{provider}/callback`: provider format acknowledgement; no browser auth |
| 1697 | Key reuse with a different payload gives `INVALID_IDEMPOTENCY_KEY` |
| 1746 | `PaymentCallbackV1`: verify the signature on the exact bytes; freshness and replay; unique event ID; amount, currency and order checks; acknowledge after a durable receipt |
| 1863–1876 (§23.2) | Quote and invoice first; the invoice stores the base price, added quantity, period, remaining-time ratio, rounded VND amount and price version; no activation before verification; no double charge or double activation |
| 2133–2135 | Verify the signature and the event ID before any state transition; on a bad signature, reject, write a safe security event, and activate nothing |

## 2. Layers and ownership

| Layer | Owner | Contents |
|---|---|---|
| **Billing core** | Owner's lane; **frozen** | Price versions, subscriptions, capacity, quota, and the Billing side of `PaymentFulfilmentPortV1` (Draft 7 §7.4; slice B-4). A read-only `PriceVersionReadPortV1` (§3.5) |
| **Payment** | Payment teammate (D-066-65) | Quote and invoice (D-066-65), checkout, provider adapters, callback intake, receipts, attempts, reconciliation, and the calls into `PaymentFulfilmentPortV1` |
| **PAY-0 skeleton** | Owner's lane, built once, **if PD-1 = yes** | The ports and DTOs below, the payment tables' DDL, the intake service with the safety rules of §5, a fake provider and a provider contract-test kit, and route stubs behind a flag. PAY-0 is the payment-side half of the "payment interface"; Draft 7's B-4 keeps the Billing-side half |

## 3. Interfaces

### 3.1 `PaymentProviderPortV1` (one implementation per provider, by the payment teammate)

| Method | Input | Output |
|---|---|---|
| `start_checkout` | `CheckoutRequestV1`: `payment_attempt_id`, `invoice_id`, `amount_vnd` (integer VND), `kind` (`ONE_TIME` or `RECURRING`), `order_description_code` (no personal data), `return_url` and `ipn_url` (both from settings), `attempt_idempotency_key` | `CheckoutSessionV1`: redirect URL or deep link, `merchant_order_ref`, provider `request_id`, `expires_at`. No credential |
| `verify_callback` | `RawCallbackV1`: HTTP method, raw query string, raw body bytes, headers, `received_at` | `PaymentCallbackV1` (§3.2). It **never raises** for bad input |
| `query_status` | `merchant_order_ref` | `ProviderStatusV1`: normalized status, `provider_transaction_ref`, `amount_vnd`, `event_time`, `provider_status_code` |
| `acknowledge` | `AckOutcome` (`ACCEPTED`, `DUPLICATE`, `REJECTED`, `RETRY_LATER`) | The provider-format status code and body |
| `test_kit` (tests only) | — | A `ProviderTestKit` with `build_signed_callback(fields, valid=True, age=...)`, so the shared contract suite can sign callbacks for any adapter (§9) |

**Adapter rules:**
- Signatures use a constant-time compare.
- Several active verification keys are allowed, for rotation.
- The amount unit is normalized to integer VND inside the adapter. A provider that scales amounts (to be verified from its documents) converts here.

### 3.2 `PaymentCallbackV1` (SRS line 1746, logical contract)

| Field | Nullable when the outcome is not `VALID`? | Meaning |
|---|---|---|
| `provider` | No | `MOMO` or `VNPAY`, from the route; must equal the attempt's provider |
| `signature_outcome` | No | `VALID`, `INVALID`, `STALE` (outside the freshness window), `MALFORMED` |
| `raw_body_sha256` | No | Digest of the exact signed bytes. The raw body is never stored or logged |
| `provider_event_ref` | Yes | **Derived** as provider transaction ID + `:` + normalized status, so a later status for the same transaction is not taken for a duplicate |
| `merchant_order_ref`, `provider_transaction_ref` | Yes | Links to the attempt |
| `amount_vnd`, `currency` | Yes | Checked against the attempt and the invoice snapshot |
| `provider_status` | Yes | `SUCCEEDED`, `FAILED`, `PENDING` |
| `event_time` | Yes | UTC, from the provider |
| `received_at` | No | UTC, from the backend |

The freshness window comes from settings, with a default to be agreed with the payment teammate (PD-7).

### 3.3 `PaymentFulfilmentPortV1` (Billing core side; Draft 7 §7.4, inputs quoted exactly)

| Command | Input (Draft 7 §7.4) | Dedupe (Draft 7) |
|---|---|---|
| `activate_add_on_slots` | organization, capacity period, added slots, `prorated_amount`, invoice ID, provider event receipt ID, content hash | Unique (subscription, receipt, event type); the same receipt with another content hash is refused |
| `issue_top_up_grant` | scope, units, invoice ID, provider event receipt ID, content hash | Grant source event unique |
| `record_renewal_outcome` | organization, outcome (`SUCCESS`, `FAILURE`, `CANCELED_BY_PROVIDER`), new period dates and `paid_extra_slots` on success, invoice ID, provider event receipt ID, content hash | Unique (subscription, receipt, event type) |

**Additions in PAY-0, to agree with the payment teammate and the Billing owner:**
- `content_hash` = SHA-256 of the canonical JSON of the command's other inputs.
- **Invoice-level idempotency:** every command is also keyed by `invoice_id` (one successful fulfilment per invoice). A callback receipt and a reconciliation receipt for the same payment therefore cannot both activate.

### 3.4 `InvoiceSnapshotV1` (SRS line 1871)

The snapshot holds:
- owner scope (`ORGANIZATION` or `PARENT_ACCOUNT`) and its ref;
- `purpose` (`ADD_ON_SLOTS`, `RENEWAL`, `TOP_UP`);
- the price version ID;
- the base unit price;
- the added quantity;
- `period_start` and `period_end`;
- the remaining-time ratio, as numerator and denominator in seconds;
- the rounded VND amount (half-up);
- `currency` = `VND`;
- `created_at`.

It is immutable once the invoice is `OPEN`.

### 3.5 Quote (payment side, D-066-65) and `PriceVersionReadPortV1` (Billing core, read-only)

- **The quote is payment-side**, as D-066-65 says. It reads the current price version through a read-only `PriceVersionReadPortV1.current(scope_kind, at)`, and computes the SRS §23.2 proration itself.
- The port belongs to Billing core and is still frozen. **Until B-1 exists**, PAY-0 provides only a fake implementation for local and test use, with a synthetic price version. The real add-on checkout therefore waits for B-1 (PD-3).
- A client-supplied amount is never trusted (SRS §21.4).

## 4. Payment tables (DDL by PAY-0 if PD-2 = yes; written only by the payment side)

| Table | Keys and constraints | Columns (register lines 390–392) |
|---|---|---|
| `billing.invoices` | PK `invoice_id`; typed owner scope and ref; unique `invoice_number`; `CHECK currency = 'VND'`; `subscription_id` a **soft ref** until B-1 adds the FK | `invoice_number`, `period_start`, `period_end`, `currency`, `subtotal`, `prorated_adjustment`, `total`, `status`, `due_at`, `paid_at`, `invoice_snapshot` (`InvoiceSnapshotV1`), `created_at` |
| `billing.payment_attempts` | PK `payment_attempt_id`; FK `invoice_id`; unique `merchant_order_ref`; unique provider `request_id`; unique (principal, operation, `invoice_id`, `idempotency_key`) | `provider`, `merchant_order_ref`, `provider_transaction_ref`, `request_id`, `amount`, `currency`, `status`, `idempotency_key`, `initiated_at`, `completed_at`, `safe_failure_code` |
| `billing.provider_event_receipts` | PK `event_receipt_id`; unique (`provider`, `provider_event_ref`); exactly one target (`payment_attempt_id`); `subscription_id_optional` a soft ref until B-1 | `provider`, `provider_event_ref`, `signature_valid`, `payment_attempt_id_optional`, `subscription_id_optional`, `received_at`, `processed_at`, `processing_status`, `safe_error_code`, `payload_hash` |

**Departure from the register, stated:** the register allows a receipt row for an unverified callback, with both FKs empty (line 392). PAY-0 writes **no receipt row for an unverified callback**, so a forged callback can never claim the unique key (PY-01). Unverified callbacks become safe security events (§5.2), as SRS 2133–2135 asks. The register note needs a matching amendment; the owner decides it with PD-2.

**DDL versus write ownership:** PAY-0 creates these tables (Alembic branch label `billing`, an independent root). Only the payment side writes them. B-1 later adds the core tables and the subscription FKs on the same branch label.

**States:**

| Entity | States |
|---|---|
| Payment attempt (SRS line 400) | `CREATED` → `PENDING` → `SUCCEEDED`, `FAILED` or `EXPIRED`. A provider cancellation is `FAILED` with a safe code |
| Invoice | `OPEN` → `PAID` or `VOID` |
| Receipt (only verified callbacks) | `FULFILMENT_PENDING` → `PROCESSED`, or `IGNORED_LATE` (a late event recorded but not applied) |

## 5. Flows and safety rules

### 5.1 Checkout (SRS line 1677)

1. **Request:** `POST /api/billing/v1/organizations/{organization_id}/subscription/checkout`. This is the C-D9 interim mapping of the SRS path `/v1/organizations/{org_id}/subscription/checkout`. It requires an `Idempotency-Key`, scoped to (principal, operation, target). A reused key with a different payload gives 400 `INVALID_IDEMPOTENCY_KEY` (SRS 1697).
2. **Synchronous part:**
   - quote;
   - create an `OPEN` invoice with the snapshot;
   - create a `CREATED` attempt;
   - enqueue a worker job;
   - return **202** with `payment_attempt_id`.
3. **Worker** (SRS 752, 936): it calls `start_checkout`, stores the redirect, and moves the attempt to `PENDING`. The client polls the status route for the redirect instruction.
4. **Stuck `CREATED`:** an attempt still `CREATED` past a threshold (settings) is retried by the worker a bounded number of times, then `FAILED` with a safe code.

### 5.2 Callback (`POST /v1/payments/{provider}/callback`)

1. **Before any write:**
   - `provider` must be an enabled adapter; otherwise 404 with no write;
   - the body is capped (settings, default 64 KiB);
   - a per-provider rate limit applies, separate from the generic unauthenticated bucket (SRS 995).
2. `verify_callback`.
3. **Outcome other than `VALID`:** no database row. A **safe security event** is emitted (counter and structured log with `provider`, `signature_outcome`, `raw_body_sha256` only), and the provider-format rejection is returned. Nothing changes state (SRS 2133–2135).
4. **`VALID`:** in **one transaction**:
   - (a) insert the receipt. A unique conflict means the same verified event was already committed, so acknowledge `DUPLICATE` with no effect;
   - (b) resolve the attempt by `merchant_order_ref` and check the provider, amount and currency. On a mismatch, record the receipt as `IGNORED_LATE` with a safe code and acknowledge `REJECTED`;
   - (c) compare-and-set the attempt and invoice transition (for example `PENDING` → `SUCCEEDED` and `OPEN` → `PAID`);
   - (d) fulfilment, per PD-5.
5. **Acknowledge only after that transaction commits.** If the transaction fails, nothing is stored and the provider's retry is processed as new, so no payment is lost (PY-02).

### 5.3 Late and conflicting events

| Situation | Rule |
|---|---|
| `SUCCEEDED` after `EXPIRED` | The provider took the money, so accept and fulfil. Flag the attempt for operator review |
| `FAILED` after `SUCCEEDED` | Record as `IGNORED_LATE`; no state change |
| Two different receipts for the same successful payment (callback and reconciliation) | The invoice-level idempotency of §3.3 lets only one fulfil |

### 5.4 Reconciliation

- A job calls `query_status` for attempts `PENDING` longer than a threshold. Default: 15 minutes, with bounded retries and backoff, all from settings; PD-7.
- A confirmed status goes through §5.2 step 4, with a synthetic event ref `recon:` + provider transaction ID + `:` + status.
- An attempt past `expires_at` with no confirmed payment becomes `EXPIRED`.

### 5.5 Browser return

The status route reads only. Without a verified event the invoice stays `OPEN` and the UI shows "pending" (SRS 589, 1137, 1868).

### 5.6 Logging and secrets (SRS 942)

- No body, headers, query string or credential is logged.
- Security events carry opaque refs and digests only.
- Merchant IDs, partner codes, callback URLs and key references come from settings or the environment; none are in Git.
- The fake provider's test key is generated at run time (not an uppercase secret-like constant, so the security validator applies cleanly).
- A settings validator refuses the fake provider outside `local` and `test`, following the existing `modal_dev` pattern in `settings.py`.

## 6. Fulfilment transaction (PD-5)

SRS 1028 and 1869 ask for the receipt and the invoice/subscription update in one transaction. Draft 7 §1 says "no cross-module SQL transaction", and §4 step 6 gives Billing its own engine and pool. **These conflict.** Options:

| Option | Content |
|---|---|
| **A (recommended)** | The payment intake and Billing core share one database session for this call only. Billing's `PaymentFulfilmentPortV1` accepts the caller's session. This **amends Draft 7 §1 and §4 step 6** for this port alone. Lock order: payment rows (attempt, invoice) first, then the Billing subscription lock; no BE1 lock is held |
| B | Separate transactions. Step 4 commits the receipt as `FULFILMENT_PENDING`, and a recovery job retries the idempotent fulfilment until `PROCESSED`. A duplicate callback while still pending re-triggers the fulfilment instead of being ignored. This deviates from SRS 1028 and 1869 |

## 7. Routes and envelope

| Route | Auth | Body format |
|---|---|---|
| `POST /v1/payments/{provider}/callback` | Signature only; no bearer | The provider's acknowledgement format (SRS 1680), not the CONV-1 envelope |
| `POST /api/billing/v1/organizations/{organization_id}/subscription/checkout` | Bearer + billing permission (PD-6) | CONV-1 envelope for errors |
| `GET /api/billing/v1/payment-attempts/{payment_attempt_id}` (status) | Bearer + scope check (404 out of scope) | CONV-1 envelope for errors |

- PAY-0 adds `/api/billing/v1` to `CONV1_PREFIXES` in `interfaces/http/error_envelope.py`.
- The callback path stays outside it.
- All three routes sit behind a settings flag that is off by default, and work only with the fake provider in `local` and `test`.

## 8. Events

`PaymentEventV1` (SRS 783) and `PaymentVerifiedV1` (SRS 1847) are defined as DTOs in PAY-0, with the SRS field lists. They are emitted through an outbox only once Billing core and notifications exist. FR-B-08 notifications are out of scope.

## 9. PAY-0 deliverables (the later implementation slice)

| Area | Deliverable |
|---|---|
| Domain | Payment value types and state transitions (pure Python, `domain/billing/payments.py`). The architecture validator already bans framework imports in `domain/`, so no new rule is needed |
| Application | The ports of §3 as typed protocols (`application/ports/payments.py`). `PaymentIntakeService` implementing §5 (checkout, callback, late events, reconciliation steps) |
| Infrastructure | Repositories for the three tables; `FakePaymentProvider` with its `ProviderTestKit`; a fake `PriceVersionReadPortV1`; a recording fake `PaymentFulfilmentPortV1` (tests only); empty `payments/momo/` and `payments/vnpay/` packages |
| Persistence | Alembic migration for the three tables (branch label `billing`, independent root). No subscription FKs (soft refs) |
| HTTP | The three routes of §7 behind the flag; the `CONV1_PREFIXES` addition |
| Contract suite | Parametrized over adapters through `ProviderTestKit`. Cases: valid once; invalid signature (no row, no effect); stale; malformed; duplicate verified event; forged-first-then-genuine (the genuine one still succeeds); provider mismatch; amount mismatch; success after expiry; failed after success; concurrent identical callbacks (one effect); crash after verify and before commit (the retry succeeds); reconciliation and callback for the same payment (one fulfilment); browser return without a callback (still `OPEN`); no body or header in logs |
| Settings | Flags, thresholds, the freshness window, body cap, rate limits, URLs and key references |

**Out of PAY-0:**
- Billing core (frozen), including the real `PriceVersionReadPortV1` and the Billing side of `PaymentFulfilmentPortV1` (B-4);
- real provider calls and MoMo or VNPAY code (PAY-1 onward, by the payment teammate);
- notifications;
- FE screens;
- Bruno.

## 10. Payment teammate's slices after PAY-0

| Slice | Content |
|---|---|
| PAY-1 | MoMo sandbox, one-time: signature as MoMo documents it, IPN, `query_status`; passes the contract suite |
| PAY-2 | MoMo Subscription or VNPAY recurring (OI-09) |
| PAY-3 | Operator view of flagged and stuck attempts |

Each needs its own Task Approval and goes into the one-at-a-time BE queue. **The real add-on checkout also needs Billing core B-1 and B-4**, which are frozen.

## 11. Owner decisions (one at a time, with the SRS sentence)

| ID | Question | Recommendation |
|---|---|---|
| PD-1 | Amend D-066-65 so that the owner's lane builds the PAY-0 skeleton (ports, tables, intake safety rules, fake provider, test kit), while the payment teammate still builds the adapters and the payment flows on top? | Yes, as requested; Billing core stays frozen |
| PD-2 | PAY-0 creates the three payment tables now, without subscription FKs, and writes no receipt row for unverified callbacks (amending the register note at line 392)? | Yes |
| PD-3 | Quote stays payment-side (D-066-65), reading prices through a read-only Billing port that is faked until B-1? | Yes |
| PD-4 | Route paths as in §7 (C-D9 interim mapping of SRS 1677)? | Yes |
| PD-5 | Fulfilment transaction: option A (shared session, amending Draft 7 §1 and §4.6 for this port) or B (recovery job)? | A |
| PD-6 | Who may start an organization checkout: "Admin billing" (SRS 1677) is still open in Draft 7 §7.5, and Parent top-up is gated by Q193 | Keep open. PAY-0 uses a permission hook, defaulting to School Manager for the fake flow only |
| PD-7 | Defaults: freshness window, body cap, rate limit, reconciliation threshold and retries | Set with the payment teammate, from the provider documents |
| PD-8 | Queue position of PAY-0 in the one-at-a-time BE queue | After FR-C-08 and SEED-1, unless the payment teammate is blocked |

## 12. Not verified

- MoMo and VNPAY wire formats: HTTP method, signed fields, amount scaling, IPN retry policy. They come from the official documents (SRS 1742).
- Physical column types (BLOCKED in the dictionary).
- The local sandbox price version (Draft 7 §2): only the fake read port exists until B-1.

No code, migration, test or command was run for this draft.

## 13. Round-1 findings and their fixes

| Finding | Fixed in |
|---|---|
| PY-01 (P1) | §4 departure (no receipt for unverified callbacks); §5.2 step 3 (security event only); contract case "forged first, then genuine" |
| PY-02 (P1) | §5.2 steps 4–5 (one transaction; acknowledge after commit; failed transaction stores nothing); §6 option B recovery job; contract case "crash before commit" |
| PY-03 | §5.2 step 1 (provider allow-list, body cap, per-provider rate limit); no rows for invalid callbacks |
| PY-04 | §6 states the conflict, the two options and the lock order |
| PY-05 | §3.3 invoice-level idempotency; §5.2 compare-and-set; §5.3 late-event rules; §5.4 synthetic reconciliation ref |
| PY-06 | §3.5 quote is payment-side per D-066-65, with a read-only Billing port faked until B-1; PD-3 |
| PY-07 | §2 and §4 relation to B-1 and B-4; soft refs; DDL versus write ownership; PD-2 |
| PY-08 | §4 states follow SRS line 400; no stored duplicate state |
| PY-09 | §3.1 `RawCallbackV1`, constant-time compare, key rotation, amount normalization; §3.2 outcome enum, nullability, event-ref derivation, provider match |
| PY-10 | §3.3 Draft 7 inputs quoted, `content_hash` defined; §3.4 `InvoiceSnapshotV1` |
| PY-11 | §5.1 202, worker, idempotency scope and uniqueness, stuck `CREATED`; URLs from settings |
| PY-12 | §3.1 `ProviderTestKit`; §9 contract cases |
| PY-13 | PD-6 kept open (Draft 7 §7.5, Q193) |
| PY-14 | §5.6 logging rule |
| PY-15 | §1 citations; the owner request quoted; the D-066-65 amendment named (PD-1) |
| PY-16 | §7 prefix and envelope rule |
| PY-17 | §5.6 and §9 validator notes |
| PY-18 | §4 VND check; §3.1 amount unit; §8 events; §5.4 defaults (PD-7) |
| PY-19 | §3.5 and §12 sandbox price-version dependency |
