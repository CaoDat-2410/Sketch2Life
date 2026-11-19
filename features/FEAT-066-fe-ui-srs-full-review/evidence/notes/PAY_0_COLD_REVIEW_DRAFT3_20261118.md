# PAY-0 Draft 3 — cold review record (round 3, 2026-11-18)

- **Artifact:** `plan/PLAN_PAY0_PAYMENT_INTERFACE_SKELETON_DRAFT3_20261118.md`, 42,718 B, SHA-256 `721DBE84287B44714E447BA0227B0CF3760C4F590744D4B280373C47B70EA211`.
- **Round granted by:** the owner, in chat on 2026-11-18 ("Draft 3 + round 3").
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only and wrote no files.
- **Pin check:** PASS. It covered Draft 3, the round-2 record (`117B7F32…`), the round-1 record (`38C88823…`), Draft 2 (`195B0247…`), the SRS (`B9B1F42D…`), Billing Draft 7 (`216B33D7…`), the data register (`7CDFDBEC…`) and the dictionary (`DDBF2E7D…`).
- **Verdict:** **NOT READY**. P1 = 0, P2 = 5, P3 = 9. Round 2 was 1 / 6 / 7.
- **D-171 item 11:** P1 + P2 fell from 7 to 5, and the round-2 P1 (PZ-01) is fixed at its core. A finding class repeats at P2: QA-01 and QA-02 are the lost-or-unwarned verified payment class (PY-02, PZ-01), and QA-04 repeats the locking class (PZ-02, PZ-06). The stop condition is met, so a round 4 needs the owner's word. The reviewer notes that all five P2s are text fixes of a few lines and need no design change.
- **Coordinator spot-check:** two points are confirmed:
  - `normalize_http_error` turns a 422 `IDEMPOTENCY_KEY_REQUIRED` into 400 `INVALID_REQUEST` with a field error (`error_envelope.py`), so QA-07 is right;
  - SRS 1875 says duplicate or out-of-order callbacks must not charge or activate twice (QA-05).

## Round-2 status

| Status | IDs |
|---|---|
| FIXED (12) | PZ-01 (residuals QA-01..QA-03), PZ-02, PZ-03, PZ-04, PZ-05, PZ-08, PZ-09, PZ-10, PZ-11, PZ-12, PZ-13, PZ-14 |
| PARTIAL (2) | PZ-06 (QA-02, QA-04, QA-13); PZ-07 (QA-07) |

All 19 round-1 entries in §15 are mapped correctly.

## Findings

| ID | Sev | Finding (short) | Repeats |
|---|---|---|---|
| QA-01 | P2 | A signature-valid callback that is not `VALID` (`STALE`, or a field-check failure, which has no named outcome) leaves no durable trace. The `STALE` reconcile hint has no dedupe store and is best-effort. Fix: one class "signature valid, not applicable", a named outcome, and a durable `reconcile_requested_at` column on the attempt | PY-02 / PZ-01 |
| QA-02 | P2 | The SRS 2088 warning has no trigger on the unrecorded exits (`RETRY_LATER` after a VALID callback), and the periodic job needs the PD-9 scheduler. Retry exhaustion has no terminal flag. The warning predicate fires on routine `PENDING` receipts. Fix: an immediate warning event at each such exit; `RECONCILE_EXHAUSTED` flag; a tighter predicate; a settings validator instead of prose for the flag | PZ-01 (SRS 2088) |
| QA-03 | P2 | Option B cannot be implemented as written: no recovery job row or runner, no warning on stale `FULFILMENT_PENDING`, the `DUPLICATE` rule of step 4(a) contradicts re-triggering, and the `REFUSED` mapping assumes a rollback | PZ-06 |
| QA-04 | P2 | The lock and compare-and-set rule covers callbacks only. Worker and job transitions (start, session lost, sweep, expiry) can overwrite a `SUCCEEDED` committed by a concurrent callback. Fix: every job transition locks attempt then invoice and writes only `WHERE status = observed`, else re-evaluates through §5.3 | PZ-02 / PZ-06 |
| QA-05 | P2 | Several `OPEN` add-on invoices can exist for one organization (another key or another admin), each quoted against the same paid slots. If both are paid, slots are added twice (SRS 1875). Fix: one open checkout per (organization, purpose, billing period), and flag a late success when a newer invoice was paid | New |
| QA-06 | P3 | A `NEEDS_REVIEW` receipt keeps no observed amount, currency or refs, so an operator cannot see what was received. Re-drive is undefined (say PAY-3) | New |
| QA-07 | P3 | `IDEMPOTENCY_KEY_REQUIRED` is not a public code (it becomes 400 `INVALID_REQUEST`). The new codes are missing from the CONV-1 message sets, and PAY-0c does not list that edit. The `NO_PRICE_VERSION` citation to Draft 7 §9 is wrong | New |
| QA-08 | P3 | A unique conflict inside the review transaction should mean `DUPLICATE` with ack `ACCEPTED`, not `RETRY_LATER` | New |
| QA-09 | P3 | Body cap status and enforcement, the 429 body, the source IP behind a proxy, and the `STALE` hint over the limit are unspecified | Mild PZ-03 |
| QA-10 | P3 | PAY-0b tests a reconcile enqueue whose job is in PAY-0c. Missing cases: VALID `PENDING`, late success after `FAILED`/`EXPIRED`, option B. Receipt status for non-fulfil transitions is unstated | New |
| QA-11 | P3 | Not marked NEW: the receipt `processing_status` value set, the `purpose` request field, the status route path. `signature_valid` on reconciliation receipts is undefined | New |
| QA-12 | P3 | PD-3 and PD-9 each bundle several asks | PZ-14 (partial) |
| QA-13 | P3 | The nullable-column header is ambiguous; a `SUCCEEDED` event with no transaction ref is not rejected; expiry when the provider still says `PENDING` has no rule | New |
| QA-14 | P3 | If the enqueue after the checkout commit fails, the request outcome is unstated (return 202, log at error level, let the sweep recover) | PZ-06 (minor) |

## Lost-payment walk (reviewer §5)

- Recorded durably: unknown order, mismatches, fulfilment `REFUSED`, double payment, duplicates, redelivered reconcile jobs, and late success with invoice `VOID` → `PAID`.
- Not durable, recovered only by the provider retry and the periodic scheduler: main or review transaction failure, handler exception, signature-valid `STALE` or field-check failure (QA-01, QA-02).
- No path loses a payment with no recovery route once a scheduler exists, so no P1 was raised.
- Lock order (receipt, attempt, invoice, Billing subscription) is the same for callbacks and reconciliation; no deadlock found.

## Checks passed

- Every SRS line Draft 3 cites matches, including 399, 1012, 1679, 1873, 2088, 2137 and 2170. Register lines 390–392 and 460–462 and dictionary lines 94–96 match.
- Draft 7 §7.4 quotes, §9 codes and the §6.1 line references (line 32, line 157, §11 items 1 and 4) match.
- Source facts confirmed: the `SKETCH2LIFE_` prefix, the `modal_dev` guard (`settings.py:110`), `RegistrationRateLimiter` (`auth_registration.py:61`), `app.py:812`, `CONV1_PREFIXES` (no `/api/billing/v1` yet), the existing codes, the Alembic roots, and the validator rules.
- Governance: the package authorizes nothing; English text; no dollar sign, secret or local absolute path; D-066-65, D-066-66 and D-066-71 match.

## Not verified

- MoMo and VNPAY wire formats, IPN retry counts and timeouts, amount scaling, and whether a provider omits the currency.
- PostgreSQL behaviour of the unique-conflict, wait and rollback sequence.
- Whether the multi-head Alembic tests accept another root.
- Nothing was run.

## Next

The owner decides between Draft 4 with round 4 and stopping (rounds used: 3 of 5).
