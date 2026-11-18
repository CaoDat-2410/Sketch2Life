# FEAT-066 L2 Billing contract Draft 5 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5. The caller set effort to high; the reviewer reported that it cannot see the effort setting. Read-only by instruction. Started on the owner's instruction ("xong tạo review đi"). Scratch folder `tmp/feat066-billing-review-d5/` was created and left empty.
- **Pin reviewed:** `plan/PLAN_L2_BILLING_CONTRACT_DRAFT5_20261118.md`, 36,181 bytes, SHA-256 `9BB4B3959C70DF5844C1E5C9737C9ED6C0A8964C912457B36EE86BDCE39A661A`. These also matched their pins:
  - Drafts 2, 3 and 4, and the Draft 2, 3 and 4 review records;
  - the questions document and the roadmap;
  - the adopted SRS in the root checkout (`B9B1F42D…`).
- **What the reviewer did not do (its statement):**
  - No file was changed outside the scratch folder.
  - No test, build, validator, linter, type checker, app, Alembic, database, Docker, network or fetch command was run.
  - Neither the gate secret directory nor any URL, `.env` or secret file was opened.
  - No state-changing git command was run. Only read-only commands were used (`sha256sum`, `sed`, `grep`, `git diff --no-index`).
- **Verdict:** NOT READY (narrowly) — **P1=0, P2=1, P3=5**. This is round 5 of at most 5 (D-171 item 11).
  - The P1+P2 count did not fall (1 → 1).
  - The create-against-downgrade class repeats for a third consecutive round (D3-01, F-01, F5-01).
  - By the rule, the work stops and returns to the owner.
  - The remaining P2 sits in the failure path, not in the main race.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 finding

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| F5-01 | §7.3 step 4 "Indeterminate"; §4 step 5(c); §12 | **The indeterminate-downgrade path has a lock-release gap.**<br>Step 4 writes `capacity_version_seen = NULL` "in a fresh transaction under the lock". By then the first transaction has ended and released the lock.<br>**Interleaving:** create C reads answer v0 and waits on the lock. Downgrade D's Billing call commits v1, but the response is lost. D ends its transaction. C takes the lock, sees stamp v0 and answer v0, and inserts against stale capacity. D then writes NULL.<br>**Result:** one class too many. D's retry then fails BE1's own check, so after the effective-time suspension the organization stays one over capacity.<br>The same hole opens, with no NULL ever written, if BE1's own commit fails or the process dies after Billing committed. This makes the §7.3 sentence "only makes admission stricter" false for creates that already hold a pre-schedule answer | (a) On timeout or lost response, write NULL inside the same lock-holding transaction and commit it, with no rollback in between.<br>(b) List commit failure or crash after the Billing commit as an accepted residual in §4 step 5 and §12. Define what a same-key retry does when Billing holds the schedule but BE1 validation now fails: an operator-visible conflict, not a silent refusal.<br>(c) Correct the "safe" sentence.<br>(d) Add a B-2 race test with this interleaving |

## P3 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| F5-02 | §7.3 step 4; §4 step 5(d) | NULL handling is unspecified in "max(current, returned)" and in the event consumer. A consumer that replaced NULL with a known lower version would hide an unknown later schedule. SQL `GREATEST` ignores NULL, so it would do exactly that | The consumer raises only non-null stamps and never turns NULL into a value. Downgrade success may replace NULL with the returned version |
| F5-03 | §6; §11 B-4/B-5; §7.3 | `CapacityVersionChangedV1` has no consuming slice and no contract (payload, ordering, idempotency) | Assign the consumer and the event contract to a slice. State that consumption is idempotent and max-based |
| F5-04 | §4 step 6; §7.3 | Pool starvation on the downgrade path. Creates waiting on the organization lock each hold a connection. The lock holder (the downgrade) needs a Billing connection, so a shared pool can stall until the pool or lock timeout | B-1 fixes a separate Billing pool or reserved capacity, and caps the number of lock waiters |
| F5-05 | §11 item 5 vs §7.3/§7.5 | §11 B-5 still lists "downgrade use case with `ActiveClassCountPortV1`", while §7.3/§7.5 drop that port. This was missed under F-04 | Delete the port from B-5 |
| F5-06 | §4 step 3 | The retry budget is ambiguous: "repeat step 2 once" appears for both the stamp check and the time check. Comparing Billing's `valid_until` with BE1 `clock_timestamp()` assumes one database clock | "At most one re-read in total". State the same-server clock assumption or a skew margin |

## Draft 4 findings (reviewer)

| Finding | Status | Note |
|---|---|---|
| F-01 | partly | Main interleavings closed; the indeterminate path is not (F5-01) |
| F-02 | resolved | See F5-03 |
| F-03 | partly | Lock-release gap remains (F5-01) |
| F-04 | partly | §11 contradiction (F5-05); pool gap (F5-04) |
| F-05 | resolved | Retry count: see F5-06 |
| F-06 | resolved | — |
| F-07 | resolved | — |
| F-08 | resolved | — |

## Checks (reviewer, paper analysis)

**Interleavings that hold:**
- A create that reads before the Billing commit and locks after the stamp commit re-reads.
- A create that reads after the Billing commit gets a stricter answer.
- A create that wins the lock first is counted by the downgrade.
- Concurrent downgrades serialize, and a max-based stamp is monotonic.

**Locking and capacity:**
- `FOR NO KEY UPDATE` under READ COMMITTED returns the latest committed stamp.
- It does not conflict with the key-share locks taken by class inserts.
- min(current, scheduled + selected) holds for creates admitted before the boundary.
- The null-stamp path respects the lock-order invariant; its only risk is the pool (F5-04).

**Source facts:**
- `get_db` opens a transaction with `SELECT 1`.
- The current create route has no key and no lock.
- `be1_organizations` has a `state` column.

**Other:**
- The D-066-63 quotations are verbatim. One trailing clause is dropped without an ellipsis, as noted before.
- The SRS lines match.
- The payment boundary is intact; there is no implied approval and no local absolute path.
- Draft 5 differs from Draft 4 only as stated.

## Not verified (reviewer)

- Real PostgreSQL behaviour and the deployed isolation level.
- The owner's chat selections.
- The register's Billing rows (not re-read).
- Alembic multi-head impact.
- Billing's engine and pool.
- The O-CONV mapping of a BE1 `lock_timeout`.

## Disposition by the coordinating session

Draft 5 is not edited. The review limit is reached, and the F5-01 class repeated for a third round. The next step is the owner's choice. No Draft 6 is written until the owner decides.
