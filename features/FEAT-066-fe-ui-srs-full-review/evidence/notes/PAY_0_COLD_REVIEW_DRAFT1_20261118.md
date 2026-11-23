# PAY-0 Draft 1 — cold review record (round 1, 2026-11-18)

- **Artifact:** `plan/PLAN_PAY0_PAYMENT_INTERFACE_SKELETON_DRAFT1_20261118.md`, 15,542 B, SHA-256 `990A107B825FACF3AA421835FC92A94DDB94D89E45124D7ACD44769AAAB393B3`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only.
- **Pin check:** PASS. It covered the package, Billing Draft 7 (`216B33D7…`), the SRS (`B9B1F42D…`), the data register (`7CDFDBEC…`) and the dictionary (`DDBF2E7D…`).
- **Verdict:** **NOT READY**. P1 = 2, P2 = 12, P3 = 5.
- **Coordinator spot-check:** three points are confirmed:
  - D-066-65 assigns "quote, invoice, checkout, provider callbacks" to the payment teammate, with the owner's words "payment tk khác làm nên tôi ko đụng" (PY-06);
  - SRS lines 2133–2135 require signature verification before any state transition, and a safe security event on a bad signature (PY-01);
  - SRS line 400 gives the PaymentAttempt states as CREATED, PENDING, SUCCEEDED, FAILED, EXPIRED (PY-08).

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| PY-01 | P1 | Writing a receipt "whatever the signature outcome", with dedupe on (`provider`, `provider_event_ref`), lets a forged callback claim the key first. The genuine callback is then dropped as a duplicate |
| PY-02 | P1 | The receipt and the processing run in separate transactions, and "duplicate" means "a receipt exists". A crash between them loses the payment; SRS 1028 and 1869 require one transaction. There is no recovery for stuck receipts |
| PY-03 | P2 | No bound on unauthenticated writes: no provider allow-list before writing, no body cap, no per-provider abuse policy (SRS 995), no retention for rejected rows |
| PY-04 | P2 | The PD-5 "same transaction" recommendation contradicts Draft 7 §1 ("no cross-module SQL transaction") and §4 step 6 (Billing's own pool) without saying so. Lock order is not stated |
| PY-05 | P2 | No double-activation guard across a callback receipt and a reconciliation receipt. No compare-and-set; no late-event rules; the reconciliation event ref is undefined |
| PY-06 | P2 | Quote ownership conflicts with D-066-65 (quote belongs to payment) and with Draft 7 (no quote port) |
| PY-07 | P2 | Table creation conflicts with Draft 7 §2 and §11 (B-1 creates the payment tables; B-4 is the payment interface). The subscription FKs need B-1 tables |
| PY-08 | P2 | State names deviate from SRS line 400. A stored `DUPLICATE` state is impossible under the unique key |
| PY-09 | P2 | `verify_callback` and `PaymentCallbackV1` are imprecise: HTTP method and query string, outcome enum (STALE, MALFORMED), nullable fields, event-ref derivation, provider match, constant-time compare, key rotation |
| PY-10 | P2 | The fulfilment port is thinner than Draft 7 §7.4. `invoice_snapshot` is untyped; `content_hash` is undefined |
| PY-11 | P2 | Checkout gaps: 202 with the attempt (SRS 1677); the adapter runs in the worker (SRS 936, 752); idempotency-key scope and uniqueness; stuck `CREATED`; URLs from settings |
| PY-12 | P2 | The contract suite needs a per-adapter signed-callback builder, plus missing cases (provider mismatch, late events, races, crash recovery, squatting, no logging) |
| PY-13 | P2 | The actor rule is settled in the text but open in Draft 7 §7.5 and Q193 |
| PY-14 | P2 | No logging rule for body, headers or query string (SRS 942) |
| PY-15 | P3 | Citation fixes (`PaymentCallbackV1` at SRS line 1746; dictionary lines 94–96). The owner's request is not recorded. The D-066-65 amendment is not named |
| PY-16 | P3 | `CONV1_PREFIXES` lacks `/api/billing/v1`. The envelope versus provider-acknowledgement rule is missing |
| PY-17 | P3 | Validator notes: no new architecture rule needed; the fake key must not be an uppercase secret-like constant; the settings guard should follow the `modal_dev` pattern |
| PY-18 | P3 | Reconciliation defaults; a VND `CHECK`; the amount unit; the `PaymentEventV1` and `PaymentVerifiedV1` events; error codes |
| PY-19 | P3 | The local sandbox price-version dependency is not named |

## Next

Draft 2 (rounds used: 1 of 5).
