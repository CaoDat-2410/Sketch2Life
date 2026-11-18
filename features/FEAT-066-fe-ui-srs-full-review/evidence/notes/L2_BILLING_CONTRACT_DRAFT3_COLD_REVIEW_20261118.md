# FEAT-066 L2 Billing contract Draft 3 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort set to high by the caller, read-only by instruction; started on the owner's instruction "Review Draft 3". Scratch folder `tmp/feat066-billing-review-d3/` created and left empty; one read-only `git log` and one `git status`.
- **Pin reviewed:** `plan/PLAN_L2_BILLING_CONTRACT_DRAFT3_20261118.md`, 23,167 bytes, SHA-256 `DE69DCEE453CF0044022FBA968E8229EB2E1CE5E88CC90123E7225661D94530B`. Drafts 1 and 2, both earlier review records, the roadmap, the questions document, the adopted SRS and the register matched.
- **What the reviewer did not do (its statement):** no file changed; no test, validator, build, app, database or network call; neither the gate secret directory nor the local database URL file opened.
- **Verdict:** NOT READY (narrowly) — **P1=0, P2=3, P3=9**. The P1 and P2 count fell from 9 to 3. The design change ("BE1 tự đếm lớp") is sound against the SRS and removes the root cause of most Draft 2 findings. Verified: UC-06 main flow line 1460 and precondition line 1458; §21.2 line 1649; §9.7 line 842; FR-T-02/03; FR-B-07; every SRS "reserv*" hit concerns AI Policy compute only; the register rows; the D-066-63 quotation; `settings.env` values; `be1_organizations` has a lockable row; no class-create receipt today; organizations only from `be1_bootstrap.py`.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| D3-01 | §4 step 4, §7.3, §12 | A class create that read the old capacity can commit after the downgrade's selection check (which reads BE1's count without BE1's lock), leaving the organization over capacity at the effective time (12 active, 2 selected, new capacity 10, one more created → 11 > 10). Draft 2's effective-time re-check (Draft 1 F-16) was dropped; §12 overstates "over-capacity impossible"; SRS §11.1 item 10 (line 1027) "Thay đổi capacity/tạo lớp chạy transaction với lock hoặc serializable enforcement" is not cited | Make the selection check atomic with creates (BE1 validates and records the selection under its organization lock, Billing commits only after BE1 accepts), or restore an effective-time re-check with a surplus rule; add the scheduling race to the B-2 tests; soften §12 |
| D3-02 | Header, §4.5 | The D-066-63 amendment scope is understated: besides the receipt/reservation sentence, D-066-63 says BE1 "must obtain a versioned, concurrency-safe admission result" and "a read-only capacity snapshot followed by an independent insert is insufficient"; Draft 3 is a versioned snapshot plus count-and-insert under a BE1 lock, which differs from that wording | List every sentence to amend; state the residual stale-capacity window and its handling; do not say "met as stated" |
| D3-03 | §2, §7.3, §11 | Outside local/test nothing supplies a price version, so `open_subscription` cannot run in staging/production, the bootstrap hook fails after the organization commit, and the B-2 "zero remaining" gate can never pass | State who supplies the first approved price version in staging/production and that B-2 is not enabled there until it exists; define bootstrap behaviour when `open_subscription` fails (operator error, repair through the existing-organizations command) |

## P3 findings (summary)

D3-04 the current handler already holds a session transaction and pooled connection when it would call Billing (`get_db` runs `SELECT 1`); end it before the port call and state the pool. D3-05 use `FOR NO KEY UPDATE` (not `FOR UPDATE`, which blocks FK key-share checks of other writers), count after the lock under READ COMMITTED, refuse a missing or inactive organization. D3-06 re-check the receipt under the lock; define the missing-key response (the existing session pattern uses 422/409 codes that differ from §21.4's 400); authorization before the receipt lookup. D3-07 after one re-read with `valid_until` still passed, fail 503; compare with database `now()`; define `valid_until` for terminal states. D3-08 "lower of current and scheduled" is stricter than needed while selected classes stay active; use min(current, scheduled + selected) or mark it as interpretation. D3-09 the `suspended` state needs BE1 read/write changes (current reads filter `state == "active"`, so a suspended class would become invisible, not read-only). D3-10 bootstrap is single-shot (repair only through the existing-organizations command); the content-hash column is missing from §2; the (group, class) unique is not literal in the register; idempotency of settle-generated events. D3-11 `CANCELED_BY_PROVIDER` outside `CANCEL_AT_PERIOD_END`; a downgrade scheduled at a failed renewal; the sweep runner both open and listed in B-5; reminders and FR-B-08 notifications not excluded explicitly. D3-12 the "404 out of scope" for class create is a behaviour change from the current 403 responses; mark it or defer to O-CONV.

## N-01 to N-21 (reviewer)

Resolved by removal: N-01, N-02, N-03, N-09. Resolved: N-05, N-06, N-07 (sweep open), N-10 (minor misattribution), N-11, N-13, N-14 (except D3-11a), N-15, N-16, N-17, N-21. Partial: N-04 (D3-04), N-08 (D3-10a), N-12 (D3-10b), N-18 (D3-03). N-19 not applicable. N-20 addressed with a stricter formula (D3-08). One regression of a Draft 1 fix: the downgrade effective-time re-check (D3-01).

## Not verified (reviewer)

The owner's chat selection; SRS header provenance; Alembic multi-head test impact; runtime behaviour (the D3-05 lock contention is from PostgreSQL semantics, untested); whether Billing shares BE1's engine and pool; deployment isolation level.

## Disposition by the coordinating session

Draft 3 is not edited. The three P2 findings have contained fixes within the chosen design; a Draft 4 is proposed to the owner.
