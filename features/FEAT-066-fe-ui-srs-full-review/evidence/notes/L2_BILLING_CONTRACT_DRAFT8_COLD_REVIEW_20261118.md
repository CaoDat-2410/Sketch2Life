# Billing contract Draft 8 — cold review record (2026-11-18)

- **Artifact:** `plan/PLAN_L2_BILLING_CONTRACT_DRAFT8_20261118.md`, 58,033 B, SHA-256 `BFD95D4D00981FEA2D5FEF1A7D77C86DE48B813F67D9809E8AA8FA13654C72C5`.
- **Round granted by:** the owner on 2026-11-18 (one review round for Draft 8; Draft 7 had used six rounds).
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly. It worked read-only.
- **Pin check:** PASS (Draft 8, Draft 7, DECISIONS 65,589 B, PAY-0 Draft 6, SRS, data register; worktree HEAD `2dddc607`).
- **Verdict:** **NOT READY**. P1 = 0, P2 = 3, P3 = 10. No decision is broken and no double-charge or over-activation path was found; the design is unchanged apart from the decision edits. All seven PAY-0 §6.1 edits and the D-066-74 and D-066-75 items are present.

## Findings

| ID | Sev | Finding (short) |
|---|---|---|
| B8-01 | P2 | §12 calls the audit sink settled (D-066-66), but §2 and §7.3 step 2 still carry the Draft 7 sink text ("if their columns fit (NOT VERIFIED)", a NEW table, a surplus field); D-066-66 fixes `core_audit_entries` with action, resource type and resource ID, no surplus, check-before-insert, no new unique |
| B8-02 | P2 | §7.3 `open_subscription` still says the payment teammate supplies the price version, against §2 |
| B8-03 | P2 | Invoice-level idempotency is prose only: §10, the §7.4 dedupe column and §2 uniques still key payment commands by receipt; no backing constraint |
| B8-04 | P3 | Header line 7 still says residuals (d) and (f) need acceptance; the "kept for history" sentence is wrong |
| B8-05 | P3 | "naming per O-CONV" in §7.3 step 2 is stale |
| B8-06 | P3 | §12 dropped "no time bound until the publisher runs" for residuals (d) and (f) |
| B8-07 | P3 | §7.7: "capacity period in effect" rewords PAY-0's "current provider period"; "settles due transitions first" makes a read-only port write; session or pool not stated; PD-3b says fake until B-1 while PAY-0 §6.1 and Draft 8 say B-4 |
| B8-08 | P3 | §7.4 lock order omits the quota-scope lock for a Parent top-up; no-invoice renewal outcomes; caller's session engine; title says "payment teammate" |
| B8-09 | P3 | The B-4 port review gate is mis-cited to PAY-0 §2; it is a Draft 8 addition |
| B8-10 | P3 | Teacher quota scope wording; multi-organization open item too narrow; the Q193 offer gate and `billing_admin_ref` not stated |
| B8-11 | P3 | Queue omits the PD-9a runner slice; B-2 to B-5 order "set when B-1 is done" has no source; B-1 could read as a second Alembic root; header omits D-066-75; C-M4's dependency on B-1/B-2 not mentioned |
| B8-12 | P3 | §9 "none of these codes" overstated (three exist); the B-2 timeout code is not an open item |
| B8-13 | P3 | MoMo recurring via PAY-2 stated as fact (OI-09 open); the C-D9 SRS reconciliation note is missing from the SRS-update list |

## Checks passed

Decision fidelity of §1, §2, §4 steps 1 and 6, §7.4, §7.7 fields, §8 routes and actors, §11 queue; payers and the no-Teacher-pool rule; the MoMo narrowing label; envelope behaviour in source (503 retryable, `Retry-After` copy, 409 not retryable, missing key → 400, `/api/billing/v1` not yet a CONV-1 prefix, Billing codes absent from the message sets); no lock-order cycle; no remaining "frozen", "conventions slice", "O-PAY" or old Billing `/v1` paths outside history; governance clean.

## Not verified

Races beyond the written lock orders; PAY-0 §5.2–§5.4 and §13–§18 line by line; Draft 8 §3, §5, §6, §7.1–§7.3 beyond the diff; earlier review notes; `price_versions.approved_by` semantics.

## Next

The owner granted one round. Draft 9 fixes these findings as text edits; the owner decides whether to approve it without a further round.
