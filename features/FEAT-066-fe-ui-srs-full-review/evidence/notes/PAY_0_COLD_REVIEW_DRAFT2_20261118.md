# PAY-0 Draft 2 — cold review record (round 2, 2026-11-18)

- **Artifact:** `plan/PLAN_PAY0_PAYMENT_INTERFACE_SKELETON_DRAFT2_20261118.md`, 23,396 B, SHA-256 `195B0247464C57EF876357D653963A5A905E26EEED512903F2B90316CDAAA7ED`.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only and created no scratch files.
- **Pin check:** PASS. It covered Draft 2, the round-1 record (`38C88823…`), the SRS (`B9B1F42D…`), Billing Draft 7 (`216B33D7…`), the data register (`7CDFDBEC…`), the dictionary (`DDBF2E7D…`) and Draft 1 (`990A107B…`).
- **Verdict:** **NOT READY**. P1 = 1, P2 = 6, P3 = 7. Round 1 was 2 / 12 / 5.
- **D-171 item 11:** P1 + P2 fell from 14 to 7. However, a finding class repeats: PZ-01 is the same class as PY-02 (lost payment). PZ-02 (PY-05) and PZ-03 (PY-01/PY-03) also repeat. The stop condition is met, so a round 3 needs the owner's word.

## Round-1 status

| Status | IDs |
|---|---|
| FIXED (12) | PY-01, PY-04, PY-07, PY-08, PY-09, PY-10, PY-13, PY-14, PY-15, PY-16, PY-17, PY-18, PY-19 |
| PARTIAL (6) | PY-02 → PZ-01; PY-03 → PZ-03; PY-05 → PZ-02; PY-06 → PZ-04; PY-11 → PZ-05..PZ-07; PY-12 → PZ-13 |

PY-01 is fixed because only a signature-VALID callback inserts a receipt, so a forged callback can no longer claim the unique key.

## Findings

| ID | Sev | Finding (short) | Repeats |
|---|---|---|---|
| PZ-01 | P1 | A verified payment that cannot be applied is lost silently. An amount, currency or provider mismatch is stored as `IGNORED_LATE` and acknowledged `REJECTED`, and reconciliation repeats the same check. Under option A, a deterministic fulfilment refusal rolls back and leaves no row. The unresolvable-attempt case is undefined: the receipt target is "exactly one" in the draft but "0 or 1 FK" in the register. SRS 2088 (5-minute warning) and 2137 are not met. Fix: a durable `NEEDS_REVIEW` state, written in a separate small transaction, plus an operator warning | PY-02 |
| PZ-02 | P2 | The transition and conflict matrix is incomplete: SUCCEEDED while `CREATED` or `FAILED`; a second SUCCEEDED with another provider ref (double payment); a VALID PENDING callback; the second receipt after a failed CAS. The fulfilment port has no result type | PY-05 |
| PZ-03 | P2 | The per-provider limiter runs before verification with no key stated, so a forged flood can return 429 to genuine callbacks (SRS 995). No limiter component is a deliverable. Fix: verify first, then limit only non-VALID outcomes | PY-01/PY-03 |
| PZ-04 | P2 | `PriceVersionReadPortV1` cannot feed the quote: no period start or end, billing period, or quantity basis (SRS 1871, 1873) | PY-06 (partial) |
| PZ-05 | P2 | The idempotency key includes `invoice_id`, which does not exist before the request, so a replay creates a second invoice. Key it on (principal, operation, `organization_id`, key) and add a request fingerprint | PY-11 (dedupe class) |
| PZ-06 | P2 | The checkout worker, stuck-`CREATED` sweep, reconciliation, expiry and scheduler runner are not deliverables. No `CREATED→STARTING` CAS against RQ redelivery. No `query_status` before expiry | — |
| PZ-07 | P2 | Route contracts are not specified: checkout body (SRS 1677), 202 and status response fields, error codes. The polling choice is not marked as an interpretation. A plain-text 500 on non-CONV-1 paths (`app.py:812`) | — |
| PZ-08 | P3 | The Draft 7 text to amend is not listed. The payment tables share the `billing` schema, so the PD-5 "cross-module" framing is overstated | PY-04/PY-07 (partial) |
| PZ-09 | P3 | Event ref "transaction ID + status" can collide when the transaction ID is empty | — |
| PZ-10 | P3 | The receipt target is attempt-only; renewal events need the subscription target (register "0 or 1 FK") | — |
| PZ-11 | P3 | The order of the HMAC and freshness checks is not stated. A signature-valid STALE callback should trigger an immediate `query_status` | — |
| PZ-12 | P3 | Where `verify_callback` runs is not stated (SRS 752/936 against 1746). Record it as an interpretation | — |
| PZ-13 | P3 | Deliverables are loose: setting names and defaults; PostgreSQL required for the concurrency cases; missing test cases; split §9 into PAY-0a/b/c; transaction timeout below the provider IPN timeout | — |
| PZ-14 | P3 | PD-1 and PD-2 each bundle several asks. Missing: the CONV-1 dependency (local-only branch), the top-up route (SRS 1679) and the `PAYMENT_PENDING` state (SRS 399) in the out-of-scope list, and a review gate for the payment teammate | — |

## Checks passed

- All SRS lines cited in §1, register lines 390–392 and 460–462, dictionary lines 94–96, and Draft 7 §7.4 match.
- The D-066-65 wording and the Billing freeze match DECISIONS.
- Source facts confirmed: `CONV1_PREFIXES` (`error_envelope.py:16`), the `modal_dev` guard (`settings.py:110`), the independent Alembic branch roots, and the architecture and security validator rules.
- Governance: the package authorizes nothing, and the text is English with no dollar sign, secret or local absolute path.

## Not verified

- MoMo and VNPAY wire formats, IPN retry counts, IPN timeouts and amount scaling.
- PostgreSQL behaviour of the unique-conflict and lock sequence.
- Whether the multi-head Alembic tests accept another root.
- Nothing was run: no tests, validators or builds.

## Next

The owner decides between Draft 3 with round 3 and stopping (rounds used: 2 of 5).
