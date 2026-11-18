# FEAT-066 L1 seed data design Draft 3 — cold review (round 2) — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5. The caller set effort to high; the reviewer reported that it cannot see the effort setting. It worked read-only by instruction. It was started on the owner's instruction ("Review cả hai"). Its scratch folder `tmp/feat066-seed-review-d3/` was created and left empty.
- **Pin reviewed:** `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT3_20261118.md`, 16,100 bytes, SHA-256 `FDF40929A431CDC01B7376D96BA6FBC5CB2096FD1D87796E3F8E5CC3A5F0CE7E`. These also matched:
  - Draft 2 (`0AF7B365…`) and Draft 1 (`E0EE5BED…`);
  - the round-1 record (`6B99D395…`);
  - roadmap Draft 4 (`63710A9F…`) and Billing Draft 7 (`216B33D7…`);
  - the root SRS (`B9B1F42D…`).
- **What the reviewer did not do (its statement):**
  - No tests, builds, validators, Alembic, app, database, network or state-changing git.
  - No secret, `.env`, `.url` or Bruno environment file opened, and the gate secret directory not opened.
  - Root SRS only.
  - Nothing written.
- **Verdict:** NOT READY — **P1=0, P2=2, P3=6**.
  - The P1+P2 count fell from 5 to 2.
  - Two S3 recipes cannot work as written: the G (RESTRICTED) timing, and how billing time is advanced.
  - The guard needs hardening.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Round-1 findings (reviewer)

| ID | Status | Note |
|---|---|---|
| S2-01 | resolved | State names: see S3-04 |
| S2-02 | resolved | See S3-05 |
| S2-03 | resolved as a table | Recipes for D–H: see S3-01, S3-02 |
| S2-04 | resolved | Arithmetic checked for A–E and H. D: 12 − 2 = 10 ≤ 10; admission min(12, 12) = 12. E: 10 active, 2 suspended; a further create returns 409 |
| S2-05 | partly | See S3-03 |
| S2-06 | partly | See S3-07 |
| S2-07 | partly | The 7-day claim is wrong (S3-01) |
| S2-08 | partly | See S3-02, S3-06 |
| S2-09 | resolved | State names, the one-active-run index and the ages match the code |
| S2-10 | resolved | — |
| S2-11 | resolved | — |
| S2-12 | resolved | — |

## P2 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| S3-01 | §4.1 G; §4.3 F/G | Billing §6 sets `grace_until` = max(failure time, period end) + 7 days. The failure time is billing "now", because `record_renewal_outcome` has no time argument.<br>A FAILURE recorded now therefore gives GRACE, not RESTRICTED. RESTRICTED needs billing time to pass `grace_until`.<br>Under local roll-over, "period end passed" is meaningless for F; the failure alone gives GRACE. | G: record FAILURE while ACTIVE, advance billing time past `grace_until`, then `settle_due_transitions`. Drop "period end passed" from F. The "set period dates by command" option of O-SEED-CLOCK cannot produce G. |
| S3-02 | §3; §7 O-SEED-CLOCK | Advancing billing time is not scoped to one organization. A global test clock would also apply D's scheduled downgrade, roll over every period and expire the S4 grants. "S3 and S4 are independent" is therefore false. | Require per-organization time control, or fix an order: advance for E and G first; then D, F and H; then S4. List it as a hard dependency. |

## P3 findings (summary)

| ID | Finding |
|---|---|
| S3-03 | Guard hardening:<br>- `get_settings()` and `get_core_database_settings()` are `lru_cache`d: set the variable before the first call, or call `cache_clear()`.<br>- `create_core_engine(database_url)` accepts an explicit URL.<br>- Alembic `env.py` prefers `S1A_P_ALEMBIC_DATABASE_URL`, so the runbook must unset it.<br>- `STORYRUN_LITE_DATABASE_URL` is a third URL source.<br>- Reject a missing host, a `host`/`hostaddr` query parameter and the `PG*` variables; compare the port too.<br>- Rule 3(c) should check the resolved `settings.env`, because an unset variable defaults to local.<br>- The drop/recreate step is outside the guard: say the seed never drops a database. |
| S3-04 | Parent group code states are lowercase. Group: `active`, `archived`. Member: `invited`, `active`, `revoked`, `expired`. Members need `expires_at` (NOT NULL). |
| S3-05 | Product creates and the downgrade command in S2/S3 need an authenticated School Manager principal; the mechanism is not stated. Product-created classes get random IDs, so only the `[SEED]` name marker applies to them. The S3 keys are not listed. |
| S3-06 | "Same month" is ambiguous: calendar month (`Asia/Ho_Chi_Minh`) versus subscription period, and settle runs at the start of every command. Payment receipt IDs must be deterministic. The change group ref derives from (organization, principal, key). |
| S3-07 | Column gaps:<br>- `be1_adult_identities.account_id` is a non-PK UUID and needs UUIDv5.<br>- Several PKs are `String(36)`, which limits `seed-` IDs.<br>- `parent.command_receipts` has no FK, so it is counted by principal.<br>- `revision_hash` comes from the domain snapshot function.<br>- `age_source` must be `SYNTHETIC_FIXTURE`.<br>- The time-limited `be1_synthetic_eligibility_proofs` table is not mentioned. |
| S3-08 | "L3 is SCHOOL with `review_state = PENDING_REVIEW` for PUBLIC" is unclear: `review_state` is on `library_versions`, and visibility is a separate column. |

## Checks (reviewer)

- **Tables, states and constraints** in `be1_models.py`, `lesson_library/tables.py`, `parent_models.py` and `story_run_lite/tables.py`.
- **Guard precedence:** the settings config gives the process environment precedence over `.env`, and the `S2L_` prefix is not read by Settings. This was read from source, not run.
- **No local absolute paths; nothing authorized.**
- **Billing:** no Billing writes, and the stamp is never written. The `ALREADY_SCHEDULED`, grace length, suspension prerequisites and provider-cancellation prerequisites are consistent with Billing Draft 7.

## Not verified (reviewer)

- Alembic heads and runtime behaviour.
- Billing code (none exists) and whether the period is monthly or yearly.
- Direct Story insert prerequisites.
- Q-L2-5.
- D-171 item 9.
- FE screens.
- How seeded adults sign in.

## Disposition by the coordinating session

Draft 3 is not edited. A Draft 4 that fixes S3-01 to S3-08 is proposed to the owner. Under D-171 item 11 this was round 2; the P1+P2 count fell, so a round 3 is allowed.
