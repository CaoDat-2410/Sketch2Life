# PAY-0 Draft 5 — cold review record (round 5, the last allowed round, 2026-11-18)

- **Artifact:** `plan/PLAN_PAY0_PAYMENT_INTERFACE_SKELETON_DRAFT5_20261118.md`, 64,668 B, SHA-256 `9CAB3056A5B1D44DCC797F97E1082D218C092ECDD44BC392308E7940426E9ACF`.
- **Round granted by:** the owner, in chat on 2026-11-18 ("Draft 5 + round 5").
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only and wrote no files.
- **Pin check:** PASS (Draft 5, round-4 and round-3 records, Draft 4, SRS, Billing Draft 7, data register).
- **Verdict:** **NOT READY**. P1 = 0, P2 = 1, P3 = 7. Round 4 was 0 / 3 / 9.
- **D-171 item 11:** P1 + P2 fell from 3 to 1. RC-01 repeats the double-activation class (QA-05, RB-01). Five rounds are used, so no further cold round is allowed. The reviewer states that RC-01 is a one-sentence text fix and that nothing in Draft 5 loses a payment silently. The owner decides how to close.

## Round-4 status

All ten round-4 findings are FIXED (RB-01 to RB-10). RB-01 is fixed as stated, but the definition it points to has the adjacent gap RC-01.

## Findings

| ID | Sev | Finding (short) | Repeats |
|---|---|---|---|
| RC-01 | P2 | "Superseded" counts only newer attempts in `CREATED`, `PENDING` or `SUCCEEDED`. Two ended attempts A0 and A, both paid at the provider: A0's late success comes first and is fulfilled (A is `FAILED`, so it does not count); then A's late success comes, no newer attempt exists, so A is fulfilled too. Slots are added twice. Fix: also superseded when any other attempt of the same organization and operation reached `SUCCEEDED` after this attempt's `initiated_at`; "newer" defined by `initiated_at` with the id as tiebreak; add a case | QA-05, RB-01 |
| RC-02 | P3 | Other paths can still leave an attempt `PENDING` with no session and no `expires_at` (a `VALID` `PENDING` event on `CREATED`; sweep or reconcile `PENDING`; a `STARTED` result lost to the status race). It is warned (`RECONCILE_EXHAUSTED`), not silent, but blocks the organization until PAY-3 | RB-06 |
| RC-03 | P3 | "Terminal result" is undefined for reconciliation; a provider `PENDING` result counts a try, so a healthy unpaid attempt can reach `RECONCILE_EXHAUSTED`; no backoff setting | No |
| RC-04 | P3 | "Known attempt" in §5.2 step 3 should mean a same-provider attempt, so no hint is set on a mismatch | No |
| RC-05 | P3 | `build_error_body` sets `retryable` for 429, 502, 503 and 504 (not every 5xx); the 409 conclusion is right | No |
| RC-06 | P3 | §5.5 "paid because the capacity was activated" ignores a `PAID` invoice with `RECORDED_NO_EFFECT`; the §5.3 wording on where the §3.3 mapping applies conflicts with the `APPLIED` row | RB-08 |
| RC-07 | P3 | The repeated key lookup relies on READ COMMITTED (not stated); the line-189 "re-reads" clause is now unreachable | RB-03 |
| RC-08 | P3 | Skipping freshness for a provider without a timestamp departs from SRS 1746 and is not labelled a deviation; step 7 exceptions omit 404 and 413; `ReconcileEnqueuePortV1` not marked NEW; PD-2e sits out of order | No |

## Checks passed

- Focus A: every verified path ends in a durable receipt or an immediate warning; a replay of signed bytes is `DUPLICATE` with no side effect; `REJECTED` after a committed `STALE` receipt is consistent.
- Focus B: lock order (receipt, organization lock, attempt, invoice, Billing) has no cycle; same-key, different-key, late-success-versus-checkout and expiry-versus-callback races are coherent except RC-01.
- Focus C: a `STALE` `signed:` receipt cannot collide with later processing of the same event; PD, I-6, I-7, settings and §17 references are consistent.
- Fidelity: SRS 995, 1677, 1680, 1697, 1746, 1875, 2088, 2133–2137; Draft 7 §7.4; register lines 392 and 462; `build_error_body` and the `Retry-After` copy at `app.py` line 595; `CONV1_PREFIXES`; `settings.py:110`; `auth_registration.py:61`; `app.py:812`.
- Governance: authorizes nothing; English; no dollar sign, secret, CR byte or local absolute path; NEW items and I-1 to I-7 marked; owner decisions single-ask.

## Not verified

- Provider wire formats and IPN retry and timeout behaviour; PostgreSQL advisory-lock and READ COMMITTED behaviour; multi-head Alembic acceptance; whether option A's Billing session takes a BE1 row lock. Nothing was run.

## Next

Rounds used: 5 of 5. The owner decides between a Draft 6 that fixes RC-01 (and the P3 notes) without a further cold review, and stopping PAY-0 at Draft 5 with RC-01 recorded as open.
