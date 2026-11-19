# PAY-0 Draft 4 — cold review record (round 4, 2026-11-18)

- **Artifact:** `plan/PLAN_PAY0_PAYMENT_INTERFACE_SKELETON_DRAFT4_20261118.md`, 58,201 B, SHA-256 `8D3ACD63DD1B8A49A954D2225CC1AAB3065C0300DB981A23C3653E48F011A3D4`.
- **Round granted by:** the owner, in chat on 2026-11-18 ("Draft 4 + round 4").
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only and wrote no files.
- **Pin check:** PASS. It covered Draft 4, the round-3, round-2 and round-1 records, Draft 3, the SRS, Billing Draft 7, the data register and the dictionary.
- **Verdict:** **NOT READY**. P1 = 0, P2 = 3, P3 = 9. Round 3 was 0 / 5 / 9.
- **D-171 item 11:** P1 + P2 fell from 5 to 3. A finding class repeats: RB-01 is a residual of QA-05 (double activation), and RB-02 is a mild repeat of the abuse class (PZ-03, QA-09). The stop condition is met. Round 5 would be the last allowed round. The reviewer notes that the three P2s are text edits only.
- **Lost-payment walk:** no path loses a verified payment without a durable record or an immediate warning. A hard process death between verify and commit emits no event; the provider retry and the periodic reconciliation cover it.

## Round-3 status

| Status | IDs |
|---|---|
| FIXED (12) | QA-01, QA-02, QA-03, QA-04, QA-06, QA-07, QA-08, QA-09, QA-10, QA-11, QA-13, QA-14 |
| PARTIAL (2) | QA-05 (RB-01, RB-03); QA-12 (RB-09) |

## Findings

| ID | Sev | Finding (short) | Repeats |
|---|---|---|---|
| RB-01 | P2 | The §5.3 late-success cell is superseded only when a newer invoice was paid, but the "Superseded" definition counts a newer attempt in `CREATED`, `PENDING` or `SUCCEEDED`. Read as the cell says, an old late success is fulfilled while a newer attempt is still open, and the newer one then fulfils again (SRS 1875). Fix: the cell uses the definition; add a case | QA-05 |
| RB-02 | P2 | A signature-proven `STALE` or `UNPROCESSABLE` callback with a known attempt writes no receipt, so each replay of a captured message opens a transaction, sets the hint, enqueues a provider `query_status` call and emits a warning, with no dedupe or limit; `reconcile_tries` does not reset, so replays can force a false `RECONCILE_EXHAUSTED`; the attempt provider is not checked against the route. Fix: always write the `signed:` receipt and act only when the insert is new | PZ-03, QA-09 (mild) |
| RB-03 | P2 | Two concurrent same-key checkouts: the second waits on the organization lock, then hits the one-open check and gets 409 `CHECKOUT_IN_PROGRESS` instead of the same 202 (SRS 1697). Fix: repeat the key lookup after taking the lock | New (from the QA-05 fix) |
| RB-04 | P3 | `build_error_body` sets `retryable` only for 429 and 5xx, so a 409 cannot be `retryable=true`; `retry_after_seconds` comes only from a `Retry-After` header | No |
| RB-05 | P3 | "One open checkout" is a NEW product rule, not SRS 1875; mark it as an interpretation; a flagged attempt blocks until an operator acts; the hint for a null or past `expires_at` is undefined | No |
| RB-06 | P3 | `ALREADY_STARTED` with a provider `PENDING` order and no stored session leaves an attempt `PENDING` without `expires_at`, which the expiry job never selects | No |
| RB-07 | P3 | The organization lock is delivered in PAY-0c but PAY-0b's callback path needs it; the step 3 write order is not stated | No |
| RB-08 | P3 | Receipt state should follow what changed, not the Billing result; "pending" should show only while the invoice is not `PAID` | No |
| RB-09 | P3 | Stale "PD-3" reference in §3.5; PD-2c bundles columns and the index; PD-7 is not a question | QA-12 (partial) |
| RB-10 | P3 | No fallback when a provider omits `event_time`; no setting for the per-provider counter; the warning job re-fires on `NEEDS_REVIEW` receipts until PAY-3 | No |

## Checks passed

- Every cited SRS line spot-checked; register lines 390–392 and 460–462 and dictionary lines 94–96 match; Draft 7 places match.
- Source facts confirmed: `modal_dev` guard (`settings.py:110`); `RegistrationRateLimiter` (`auth_registration.py:61`) and `request.client.host` (line 109); `app.py:812`; `CONV1_PREFIXES` lacks `/api/billing/v1`; `normalize_http_error` maps `IDEMPOTENCY_KEY_REQUIRED`; the four new codes are absent from the message sets.
- Governance: the draft authorizes nothing; English text; no dollar sign, secret or local absolute path; NEW items and I-1 to I-5 marked.

## Not verified

- Provider wire formats, IPN retry counts and timeouts, amount scaling, and whether callback and query transaction refs agree.
- PostgreSQL lock, wait and unique-conflict behaviour; multi-head Alembic acceptance; whether option A's Billing session takes a BE1 row lock through a foreign key.
- Nothing was run.

## Next

The owner decides between Draft 5 with round 5 (the last allowed) and stopping (rounds used: 4 of 5).
