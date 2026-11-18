# FEAT-066 L1 seed data design Draft 4 — cold review (round 3) — 2026-11-18

- **Reviewer:** Claude subagent with a fresh context, model Sonnet 5.5, told effort high. It worked read-only by instruction and was started on the owner's instruction ("Làm cả hai"). Scratch folder `tmp/feat066-seed-review-d4/`: created and left empty.
- **Pin reviewed:** `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT4_20261118.md`, 21,576 bytes, SHA-256 `0C2DB27D13F72CC0AF4BE75CEBFD32C3868762B81B841F3AAD52E89F574EF109`. These pins also matched: Billing Draft 7 (`216B33D7…`), Draft 3 (`FDF40929…`) and the root SRS (`B9B1F42D…`).
- **What the reviewer did not do (its statement):**
  - It ran no tests, builds, validators, Alembic, app, database, network or state-changing git commands.
  - It opened no `.env`, `.url` or Bruno `.bru` file, and not the gate secret directory.
  - It wrote nothing, and used the root SRS only.
- **Verdict:** NOT READY — **P1=0, P2=1, P3=6**. P1+P2 fell from 2 to 1.
- **Process note from the reviewer:** two finding classes repeat from round 2: guard hardening (S3-03 → S4-04) and column gaps (S3-07, which was P3 → S4-01, which is P2).
- **Coordinator's reading of D-171 item 11:** the rule stops the work and returns it to the owner when a finding repeats in two consecutive rounds, or when the P1+P2 count does not fall. The count fell, but the classes repeated, so **the next step is the owner's decision**.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Round-2 findings (reviewer)

| Finding | Status | Note |
|---|---|---|
| S3-01 | resolved | — |
| S3-02 | resolved with notes | see S4-02, S4-03 |
| S3-03 | partly | see S4-04 |
| S3-04 | resolved | — |
| S3-05 | mostly | see S4-06 |
| S3-06 | resolved | replay after the S3 advance is still undefined (S4-03) |
| S3-07 | resolved for the named columns | new gap S4-01 |
| S3-08 | resolved | one phrase left (S4-05) |

## P2 finding

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| S4-01 | §2 rule 4 column rules; §4.1 identity rows | `be1_adult_identities.account_role` (`parent`, `teacher`, `school_manager`, `platform_admin`) and `role_revision` are not mentioned. The source needs them: `has_active_parent_role` requires `account_role == "parent"`, and `be1_common` filters assignments by role. Without them, seeded adults would fail every role gate. | A column rule: set `account_role` per seeded adult, and set `role_revision = 1`. |

## P3 findings (summary)

| ID | Finding |
|---|---|
| S4-02 | E and G rely on an unstated Billing reading: that local auto roll-over applies only to ACTIVE subscriptions with no recorded outcome, not to GRACE. If it also applied to GRACE, G would never reach RESTRICTED. F's wording "grace starts at the failure time" conflicts with Billing line 104 ("starts grace at period end"), because `grace_until` is max-based. **Fix:** record both as assumptions under O-SEED-CLOCK and reword F. |
| S4-03 | The roll-over note names only A, B and C, but D, F and H also roll over lazily. The clock's end state after S3 is not stated. S3 can never satisfy §6 "second run creates none". **Fix:** name D, F and H; state the clock end state and the replayable stages (S1 and S2 only). |
| S4-04 | Guard gaps: (i) it does not reject `PGSERVICEFILE` and `PGOPTIONS`, which the repo's `composition.py` guard does. (ii) Any query string should be rejected, not only host/hostaddr. (iii) The client-side comparison can be passed by a loopback tunnel; add a live server-side check (`current_database()`, `inet_server_port()`, as in `verify_goal_database_owner`). (iv) Forbid importing `main.py`, `classroom_main.py`, `demo_main.py` and `story_run_lite_app.py`, which call `create_app()` at import. (v) Mention that the worktree-root `.env` is also a source for `SKETCH2LIFE_ENV`. |
| S4-05 | The L3 wording is still imprecise. A PUBLIC request is an `access_grants` row (`audience_kind = 'PUBLIC'`, state `PENDING_REVIEW`), not a version flag. `internal_visibility` is NOT NULL and not mentioned. |
| S4-06 | The fallback "existing local/synthetic verifier path" contradicts "no HTTP, no token". The 2 selected classes of the downgrade are not identified, and product-created classes have random IDs. **Fix:** say how the selected classes are identified, and keep only "extract the command". |

## Checks (reviewer)

- **Global-clock order:** consistent with Billing Draft 7.
  - E is set up before the advance, so its boundary applies the downgrade and the suspension reaches BE1 through the publisher and consumer.
  - G's `grace_until` (period end + 7 days) lies past E's period end, so one advance covers both.
  - D, F and H are set up after the advance, so D's boundary is never reached.
  - The A, B and C roll-over is acceptable.
  - S4 runs after S3.
- **Source matches:**
  - `SYNTHETIC_DEV` checks, the parent-group state check, the version review-state check, the grant states and `uq_story_run_active_parent`;
  - the settings `lru_cache` and `.env` precedence;
  - `create_core_engine(url)`;
  - the Alembic `S1A_P_ALEMBIC_DATABASE_URL` preference;
  - the SRS `SYNTHETIC_TEST` lines and the §23.3 seven-day grace.
- **No local paths and no implied approvals.** §3, §4.1, §4.3 and §4.5 are consistent.

## Not verified (reviewer)

- Billing code (none exists) and its period length.
- Alembic heads.
- Prerequisites for direct Story inserts.
- Whether BE1 commands are callable in-process.
- FE screens and how seeded adults sign in.

## Disposition by the coordinating session

Draft 4 is not edited. The repeat clause of D-171 item 11 applies, so the owner chooses the next step. Proposed options:

- **(a)** Draft 5 fixing S4-01 to S4-06, plus one more review round. This is round 4 of 5.
- **(b)** Draft 5 without review, with the residuals accepted by the owner.
