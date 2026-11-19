# FEAT-066 PAY-0 — payment interface skeleton for the payment teammate (Draft 1)

- **Status:** DRAFT / NOT REVIEWED / NOT APPROVED / NOT LAUNCHED. This package plans a framework only. It authorizes no code, migration, command, stage, commit or push.
- **Date:** 2026-11-18. **Author:** coordinating Claude session (Opus 5.5). **Owner:** Person 2.
- **Purpose:** give the payment teammate (HieuNewBie) a fixed interface, a skeleton and a test harness, so that the MoMo adapter (then VNPAY) can be built without touching Billing core. The owner asked for this framework on 2026-11-18 ("khởi động lại làm khung payment đi").
- **Billing is still frozen** (owner, 2026-11-18). This package reopens only the payment interface and its skeleton. Billing core (B-1 to B-5) stays frozen unless the owner says otherwise (§9, PD-1).

## 1. Authority

| Input | Pin or location |
|---|---|
| Working SRS (D-209) | `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, 701,157 B, `B9B1F42D…` |
| Data table register | `features/FEAT-063-system-architecture-rearchitecture/artifacts/DATA_TABLE_REGISTER.md`, 171,609 B, `7CDFDBEC…`: lines 390–392 and 460–462 |
| Physical data dictionary (draft) | `.../artifacts/PHYSICAL_DATA_DICTIONARY_DRAFT_REV57_20261109.md`, 53,694 B, `DDBF2E7D…`: lines 91–96 (logical fields only; DDL still BLOCKED) |
| Billing contract | `plan/PLAN_L2_BILLING_CONTRACT_DRAFT7_20261118.md` (49,498 B, `216B33D7…`, closed without review by owner instruction): §1, §2, §7.4, §11 |
| Owner decisions | D-066-65 (O-PAY: "Tôi: contract + port + Billing trừ thanh toán", pending agreement with the payment teammate); D-066-68 (conventions); D-066-71 (CONV-1 envelope) |

**SRS clauses used:**

| Clause | Content |
|---|---|
| Line 167 | 10 included class slots; extra slots bought through MoMo/VNPAY |
| Line 205 | Provider callback to the backend; the redirect only shows status; signature, replay protection, dedupe and reconciliation through the sandbox |
| BR-28 (line 272) | VND monthly or yearly; MoMo and VNPAY are the V1 adapters; no VietQR |
| FR-B-01 to FR-B-05 (lines 587–591) | Price versions; subscription lifecycle with recurring MoMo/VNPAY adapters; signature verification, dedupe and in-transaction reconciliation; add-on capacity only after a verified payment, with proration; auto-renew off |
| FR-B-13 (line 599) | Top-up only after a verified, idempotent payment event, with immutable invoice and grant |
| §9.6 (line 811) | `/v1/payments/{provider}/callback` verifies the callback and drops duplicate events |
| Lines 936–937 | No provider credential reaches a browser or mobile client; callback signature verified; unique provider-event ref and receipt in the same transaction |
| Line 1028 | Unique provider event key; webhook receipt and invoice/subscription update in one idempotent transaction |
| AC-14 (line 1137) | Payment, capacity, grace, downgrade, proration and notice stay consistent; a redirect is not a payment |
| OI-09 (line 1221) | Merchant sandbox, recurring contract, callback signature and freshness, cancel, retry and failure reconciliation: open before P3 payment integration |
| `PaymentCallbackV1` (line 1744) | The logical adapter contract (§3.2 below) |
| §23.2 (lines 1863–1876) | Quote and invoice snapshot first; checkout through the adapter; the verified, deduplicated event updates attempt and invoice and activates capacity in one transaction |

## 2. Layers and ownership

| Layer | Owner | Contents |
|---|---|---|
| **Billing core** | The owner's lane (frozen; PD-1) | Price versions, subscriptions, capacity periods, quota, the quote (§3.4), and `PaymentFulfilmentPortV1` (§3.3) |
| **Payment** | HieuNewBie | Provider adapters (MoMo, then VNPAY); checkout start; callback intake; signature and freshness verification; durable receipts and dedupe; payment attempts and invoices; reconciliation; the calls into `PaymentFulfilmentPortV1` |
| **PAY-0 skeleton** (this package) | The owner's lane, built once | Ports, DTOs, domain types and states, the three payment tables, a fake provider, a provider contract-test suite, and route stubs behind a flag |

**Rules:**
- The two sides meet only through the ports in §3.
- The payment side never writes Billing core tables.
- Billing core never writes the three payment tables (Billing Draft 7 §2).

## 3. Interfaces

### 3.1 `PaymentProviderPortV1` (implemented once per provider by the payment teammate)

| Method | Input | Output | Notes |
|---|---|---|---|
| `start_checkout` | `CheckoutRequestV1`: payment attempt ID, invoice ID, amount (VND integer), currency `VND`, description code (no personal data), return URL, IPN URL, kind (`ONE_TIME` or `RECURRING`), idempotency key | `CheckoutSessionV1`: provider redirect URL or deep link, `merchant_order_ref`, provider `request_id`, `expires_at` | Never returns a credential. The redirect URL is shown to the client only |
| `verify_callback` | Raw body bytes, headers, received time | `PaymentCallbackV1` (§3.2) | Must check the signature and freshness. Never raises on a bad signature; returns `signature_outcome = INVALID` |
| `query_status` | `merchant_order_ref` | `ProviderStatusV1`: status, provider transaction ref, amount, event time | For reconciliation (OI-09); read-only |
| `acknowledge` | Processing outcome | The provider-format acknowledgement body and status | Called only after the durable receipt is written |

### 3.2 `PaymentCallbackV1` (SRS line 1744, logical contract)

| Field | Meaning |
|---|---|
| `provider` | `MOMO` or `VNPAY` |
| `raw_body_sha256` | Digest of the raw body; the raw body itself is not stored |
| `provider_event_ref` | The provider's event or transaction notification ID; unique per provider |
| `merchant_order_ref`, `provider_transaction_ref` | Links to the payment attempt |
| `amount`, `currency` | Checked against the attempt and the invoice |
| `provider_status` | Normalized: `SUCCEEDED`, `FAILED`, `CANCELLED`, `PENDING` |
| `event_time`, `received_time` | UTC |
| `signature_outcome` | `VALID`, `INVALID`, `UNCHECKED` |

### 3.3 `PaymentFulfilmentPortV1` (Billing core; Billing Draft 7 §7.4)

| Command | Called when | Dedupe |
|---|---|---|
| `activate_add_on_slots` | A verified successful payment of an add-on slot invoice | Unique (subscription, receipt, event type); the same receipt with a different content hash is refused |
| `issue_top_up_grant` | A verified successful payment of a quota top-up invoice | Grant source event unique |
| `record_renewal_outcome` | A verified renewal success or failure, or a provider cancellation | Unique (subscription, receipt, event type) |

Each command takes `invoice_id`, `provider_event_receipt_id` and `content_hash`. The payment side calls it inside the same transaction that marks the attempt and the invoice, or immediately after it through an idempotent retry (PD-5).

### 3.4 `BillingQuotePortV1` (Billing core, proposed)

`quote(scope, purpose, quantity, period)` returns a server-computed amount from the current price version, including SRS §23.2 proration. The payment side copies the result into the immutable `invoice_snapshot`. A client-supplied amount is never trusted (SRS §21.4).

## 4. Payment tables (written only by the payment side)

Logical columns come from the data register (lines 390–392). The physical DDL is still BLOCKED in the dictionary and is fixed in PAY-0's Task Approval.

| Table | Keys and constraints | Columns |
|---|---|---|
| `billing.invoices` | PK `invoice_id`; typed owner scope (`ORGANIZATION` or `PARENT_ACCOUNT`) and ref; optional FK `subscription_id`; unique `invoice_number` | `invoice_number`, `period_start`, `period_end`, `currency`, `subtotal`, `prorated_adjustment`, `total`, `status`, `due_at`, `paid_at`, `invoice_snapshot` (immutable), `created_at` |
| `billing.payment_attempts` | PK `payment_attempt_id`; FK `invoice_id`; unique provider request ref and merchant ref | `provider`, `merchant_order_ref`, `provider_transaction_ref`, `request_id`, `amount`, `currency`, `status`, `idempotency_key`, `initiated_at`, `completed_at`, `safe_failure_code` |
| `billing.provider_event_receipts` | PK `event_receipt_id`; unique (`provider`, `provider_event_ref`); zero or one target FK (`payment_attempt_id` or `subscription_id`) | `provider`, `provider_event_ref`, `signature_valid`, `payment_attempt_id_optional`, `subscription_id_optional`, `received_at`, `processed_at`, `processing_status`, `safe_error_code`, `payload_hash` |

**Rules (register):**
- An unverified or unresolved callback is stored with both target FKs empty.
- A verified and processed receipt has exactly one target.
- An invoice is resolved through its payment attempt.
- No raw secret, card or wallet data is stored, and the provider transaction ref alone is never proof of payment.

**States** (proposed for PAY-0; to agree with the payment teammate, PD-3):

| Entity | States |
|---|---|
| Invoice | `DRAFT` → `OPEN` → `PAID` or `VOID` |
| Payment attempt | `CREATED` → `REDIRECTED` → `SUCCEEDED`, `FAILED`, `CANCELLED` or `EXPIRED` |
| Receipt | `RECEIVED` → `VERIFIED` → `PROCESSED`, or `REJECTED` or `DUPLICATE` |

## 5. Flows

1. **Checkout** (an add-on slot, a renewal or a top-up):
   1. Billing core quotes (§3.4).
   2. The payment side creates an `OPEN` invoice with the snapshot and a `CREATED` attempt.
   3. `start_checkout` runs.
   4. The client receives only the redirect URL.
2. **Callback** (`POST /v1/payments/{provider}/callback`):
   1. Read the raw body, then `verify_callback`.
   2. **Write the receipt durably first**, whatever the signature outcome.
   3. A duplicate (`provider`, `provider_event_ref`) acknowledges with no new effect.
   4. With a valid signature and a matching amount, one transaction updates the attempt and the invoice and calls the matching `PaymentFulfilmentPortV1` command.
   5. Finally `acknowledge`.
   6. An invalid signature records a `REJECTED` receipt and changes nothing else.
3. **Browser return:** it only reads the attempt status. A return without a verified callback leaves the invoice `OPEN` and the UI shows "pending" (SRS §23.2, AC-14).
4. **Reconciliation:** a job calls `query_status` for attempts that stay `REDIRECTED` past a threshold. A provider-confirmed success goes through the same path as a verified callback.
5. **Recurring** (MoMo Subscription, VNPAY recurring, SRS line 1271): the renewal outcomes go through `record_renewal_outcome`. The exact provider contract is OI-09.

## 6. Routes

| Route | Purpose | Notes |
|---|---|---|
| `POST /v1/payments/{provider}/callback` | Provider IPN | The SRS path exactly, because providers are configured with it. Unauthenticated by bearer; authenticated by signature. Errors use the CONV-1 envelope except where the provider requires its own acknowledgement format |
| A checkout-start route under the billing namespace | Start a checkout for an invoice | The exact path follows C-D9 (interim `/api/<namespace>/v1`) and is fixed in PAY-0's Task Approval (PD-4). Requires an `Idempotency-Key`. School Manager only for organization scope; the Parent account for Parent top-up if the owner enables it (FR-B-13, Q193) |
| A status route for the browser return | Read the attempt and invoice status | Read-only |

In PAY-0 the routes exist behind a settings flag that is off by default, and they answer through the fake provider in `local` and `test` only.

## 7. PAY-0 skeleton deliverables (the later implementation slice)

| Area | Deliverable |
|---|---|
| Domain | Payment value types and state transitions, pure Python (`domain/billing/payments.py`), following the architecture validator's layering rules |
| Application | `PaymentProviderPortV1`, `PaymentFulfilmentPortV1`, `BillingQuotePortV1` as typed protocols (`application/ports/payments.py`); a `PaymentIntakeService` with checkout start, callback processing and reconciliation steps, wired to the ports |
| Infrastructure | Repositories for the three tables; `FakePaymentProvider` (deterministic HMAC with a test key read from settings, never committed); empty `payments/momo/` and `payments/vnpay/` packages for the payment teammate |
| Persistence | An Alembic migration for the three payment tables only, under the `billing` branch label (PD-2) |
| Contract tests | One suite parametrized over every provider adapter: <ul><li>a valid callback is accepted once;</li><li>an invalid signature is rejected and changes nothing;</li><li>a duplicate event has no second effect;</li><li>an out-of-order event does not double-activate;</li><li>an amount mismatch is rejected;</li><li>a stale event is rejected by freshness;</li><li>a browser return without a callback leaves the invoice open.</li></ul> The fake provider must pass it, and the MoMo adapter must pass it later |
| Settings | Merchant ID, partner code, callback URLs and secret references, read from settings or the environment. None in Git; the security validator applies |
| Fulfilment stub | Until Billing core exists, `PaymentFulfilmentPortV1` is a recording stub in tests only. No capacity or quota change happens in PAY-0 |

**Explicitly out of PAY-0:** Billing core tables and logic (frozen), real provider calls, MoMo or VNPAY code (the payment teammate's PAY-1 and PAY-2), notifications (FR-B-08), FE screens, Bruno.

## 8. Payment teammate's slices after PAY-0 (for planning)

| Slice | Content |
|---|---|
| PAY-1 | MoMo sandbox adapter: one-time payment, signature (HMAC as MoMo documents it), IPN handling, `query_status`; passes the contract suite |
| PAY-2 | MoMo recurring (Subscription), or VNPAY, as the team decides (OI-09) |
| PAY-3 | Reconciliation job and operator view of stuck attempts |

Each needs its own Task Approval and goes into the one-at-a-time BE queue.

## 9. Owner decisions needed (one at a time, with the SRS sentence)

| ID | Question | Recommendation |
|---|---|---|
| PD-1 | Does PAY-0 reopen only the payment interface and skeleton, with Billing core staying frozen? | Yes |
| PD-2 | Does PAY-0 create the three payment tables (`billing` branch label), or wait for B-1? | PAY-0 creates them, so the payment teammate is unblocked. B-1 later adds the core tables on the same branch label |
| PD-3 | The state names in §4, and invoice ownership: payment side (Billing Draft 7 §2) with the Billing core quote (§3.4) | As proposed. To agree with the payment teammate |
| PD-4 | The checkout and status route paths under C-D9 | `/api/billing/v1/...`, fixed in the Task Approval |
| PD-5 | Fulfilment call: inside the payment transaction, or after it through an idempotent retry? | Inside the same transaction, as SRS line 1028 asks. That needs Billing core in the same process and database, which it is |
| PD-6 | BE queue position of PAY-0 | After FR-C-08 and SEED-1, or before SEED-1 if the payment teammate is waiting. Owner's call |

**For the payment teammate** (to agree before PAY-1): the MoMo product (one-time against Subscription), sandbox merchant access (OI-09), the callback freshness window, and who owns the reconciliation threshold.

## 10. Not verified

- MoMo's and VNPAY's current wire formats, signature fields and IPN retry policy. They must come from the official documents (SRS line 1742 says the adapter contract is logical only).
- The physical column types. The dictionary marks them BLOCKED.
- Whether the architecture validator needs a new rule entry for `domain/billing`.

No code, migration, test or command was run for this draft.
