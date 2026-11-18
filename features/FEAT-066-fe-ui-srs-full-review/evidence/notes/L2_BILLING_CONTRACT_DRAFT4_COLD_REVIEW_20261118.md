# FEAT-066 L2 Billing contract Draft 4 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort set to high by the caller, read-only by instruction; started on the owner's instruction "Review Draft 4". Scratch folder `tmp/feat066-billing-review-d4/` created and left empty.
- **Pin reviewed:** `plan/PLAN_L2_BILLING_CONTRACT_DRAFT4_20261118.md`, 30,568 bytes, SHA-256 `D8D2B505156ED1915E99CD19FA3614841ECF02CF34A6114EA49C7FDC6CA718DC`. Draft 3, the Draft 3 and Draft 2 review records, the roadmap, the questions document, the adopted SRS and the register matched.
- **What the reviewer did not do (its statement):** no repository file changed; no test, validator, build, app, Docker, database, network or fetch; neither the gate secret directory nor the local database URL file opened; lock claims are from PostgreSQL semantics, not from running anything.
- **Verdict:** NOT READY (narrowly) — **P1=0, P2=1, P3=7**. The P1 and P2 count fell from 3 to 1. The single P2 is the same class as Draft 3's D3-01 (create against downgrade): a finding repeated in two consecutive rounds, so the work returns to the owner.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 finding

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| F-01 | §4 steps 2–5; §7.3; header residual window; §12 | The shared lock does not close the create-against-downgrade race: a create reads Billing's capacity answer in step 2, before taking the BE1 lock; a downgrade can lock, validate, schedule and commit in between; the create then counts under the lock but uses the stale answer (`valid_until` is unchanged because the downgrade takes effect at the existing period end; `capacity_version` is returned but never compared). Example: 11 active, capacity 12; create reads 12; downgrade to 10 selecting 1 passes and Billing now answers 11; the create inserts → 12 active, 11 after suspension, against capacity 10 | The downgrade transaction writes the `capacity_version` returned by `schedule_downgrade` to a BE1-owned column on the organization row under the same lock; in step 3 the create compares the answer's version with that column and, if older, releases the lock and repeats step 2 once, else 503. Alternative: re-call Billing under the lock on every create. Keep the B-2 race test with this exact interleaving |

## P3 findings (summary)

F-02 the header's "only shrinking case" is wrong: `CANCELED_BY_PROVIDER` from ACTIVE/GRACE takes effect at once (small impact). F-03 downgrade failure semantics overstated: Billing may commit while BE1 reports an error (safe, stricter admission, but an indeterminate outcome); derive the change-group ref from the client idempotency key; Billing-side timeouts; replacing or cancelling a scheduled downgrade is an open item. F-04 state the lock-order invariant (BE1 organization lock before Billing subscription lock; Billing never calls a locking BE1 port inside a command); resolve who calls `ActiveClassCountPortV1`; §4 step 6 is false for the downgrade path, which holds a BE1 connection during the Billing call. F-05 use `clock_timestamp()` (PostgreSQL `now()` is the transaction start), set READ COMMITTED explicitly, define null `valid_until` as not passed. F-06 the header says the 404/403 distinction is kept, while B-2 ships the interim 403; name 503 `BILLING_UNAVAILABLE` among the owner decisions (D-066-63 left that mapping open). F-07 mark as interpretations: missing key → 400 `INVALID_REQUEST` (also a breaking change for current callers) and the admission-capacity formula; state the `NO_PRICE_VERSION` mapping. F-08 module and table ownership "this lane" should read "pending O-PAY" (the roadmap leaves who builds the Billing module to O-PAY).

## Checks (reviewer)

No deadlock in the design as written; `FOR NO KEY UPDATE` is right (no conflict with the key-share lock of the `be1_classrooms.organization_id` foreign key; no other writer of classrooms found); the admission-capacity formula is correct in all orders except the stale-answer case; receipt re-check plus the receipt primary key gives same-key replay; authorization-first and the interim 403 match the current code; ending the `get_db` transaction before the port call is needed and correct; the D-066-63 quotations are verbatim apart from two trailing clauses dropped without an ellipsis. D3-01 not fully resolved (F-01, F-03); D3-02 resolved (F-02 wording); D3-03 resolved; D3-04 resolved for the create path (F-04); D3-05 resolved (F-05 isolation); D3-06 resolved (F-07); D3-07 partly (F-05 clock); D3-08 to D3-11 resolved; D3-12 resolved (F-06 wording). Payment boundary intact; no implied approval; no local absolute paths; no SRS or register contradiction.

## Not verified (reviewer)

The owner's chat selection; Billing's engine and pool; runtime PostgreSQL behaviour and deployed isolation level; Alembic multi-head impact; the mapping of a BE1 `lock_timeout` (depends on O-CONV).

## Disposition by the coordinating session

Draft 4 is not edited. F-01 repeats the class of D3-01 in two consecutive rounds, so the fix approach goes to the owner before a Draft 5.
