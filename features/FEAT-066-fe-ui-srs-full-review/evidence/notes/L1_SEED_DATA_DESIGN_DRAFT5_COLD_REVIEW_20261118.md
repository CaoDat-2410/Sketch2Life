# FEAT-066 L1 seed data design Draft 5 — cold review (round 4) — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, told effort high. Read-only by instruction. Started on the owner's instruction "Draft 5 + review", which was round 4 of 5. Scratch folder `tmp/feat066-seed-review-d5/` was created and left empty.
- **Pin reviewed:** `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT5_20261118.md`, 25,609 bytes, SHA-256 `A549EC0B92072175315473DB8538A6A8E503470C44388F596D9B7176EA785CD3`. These also matched:
  - Draft 4 (`0C2DB27D…`) and its review record (`9B2220B5…`);
  - Draft 3 (`FDF40929…`);
  - roadmap Draft 4 (`63710A9F…`);
  - Billing Draft 7 (`216B33D7…`);
  - the root SRS (`B9B1F42D…`).
- **What the reviewer did not do (its statement):**
  - It ran no tests, builds, validators, linters, app, Alembic, database, Docker or network, and no state-changing git.
  - It opened no `.env`, `*.url`, Bruno `.bru` or secret file, and not the gate secret directory.
  - It used only reads, `git diff --no-index`, `sha256sum` and `grep`.
  - It wrote nothing to any repository.
- **Verdict:** READY WITH NOTES — **P1=0, P2=0, P3=4**. P1+P2 fell from 1 to 0.
  - Two notes repeat earlier classes at P3 level: column gaps (S5-01, S5-02) and guard wording (S5-03).
  - Each repeat is a one-sentence fix, and none breaks a role gate.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Round-3 findings (reviewer)

| ID | Status | Note |
|---|---|---|
| S4-01 | resolved | Matches the account-role check constraint, `be1_parent_role_adapter.py:38` and `be1_common.py:98-111`. |
| S4-02 | resolved with note | Readings (i) and (ii) are now assumptions. Billing line 104 is still ambiguous, so F's "no advance" is conditional. The plan flags this. |
| S4-03 | resolved with note | See S5-04. |
| S4-04 | mostly resolved | Residual in S5-03. |
| S4-05 | partly | See S5-01. |
| S4-06 | resolved | — |

## P3 findings

| ID | Finding | Smallest fix |
|---|---|---|
| S5-01 | Draft 5 dropped the coupling in which a PUBLIC grant sets its version to `review_state = PENDING_REVIEW` (`service.py:1124-1128`). It also omits `library_items.visibility` (NOT NULL), which `_recalculate_visibility` derives from ACTIVE grants (`service.py:1290-1310`). Non-PUBLIC grants need an APPROVED version, a non-null `audience_ref` and a `capability`. The §8 "value names" item is already answered: `ck_lesson_internal_visibility` allows PRIVATE or SCHOOL. | One column rule: set grant state, version `review_state` and lesson `visibility` as the product commands would. Drop the §8 item. |
| S5-02 | The grant inventory is ambiguous. There are two `PENDING_REVIEW` rows (L3 PUBLIC, and L1's first version), and the ACTIVE and REVOKED rows have no audience kind or capability. | List the grant rows with lesson, version, `audience_kind`, `capability` and state. |
| S5-03 | The live check compares only `current_database()` and `inet_server_port()`. The repository's `verify_goal_database_owner` also checks that `inet_server_addr()` is loopback and that `current_user` is the database owner. | Add the two checks and soften "a loopback tunnel therefore fails". |
| S5-04 | An S1 replay after S3 with a DO UPDATE upsert would reset S3 state: suspended classes and `capacity_version_seen`. | S1 inserts only when a row is absent. S1 and S2 replay only before S3 has run. |

## Checks (reviewer)

- Constraint checks match: `SYNTHETIC_DEV` without consent, `age_months` 36–155, the 36-character primary keys, the Parent-group states with the required `expires_at`, and the Alembic URL preference.
- The admission capacity is min(12, 10 + 2) = 12.
- The SRS `SYNTHETIC_TEST` naming and BR-31 (7 days) match.
- The four entry modules call `create_app()` at module level.
- In the settings loader the process environment wins over `.env`.
- The global-clock order still works against Billing Draft 7.
- No local paths and no implied approvals.

## Not verified (reviewer)

- Billing code, which does not exist yet.
- Whether the BE1 commands can be called in-process.
- How Billing roll-over and the sweep behave at runtime.
- Alembic heads.
- Story insert prerequisites.
- FE screens.
- One implementation detail: the deferred circular FK between Parent `child_profiles` and `profile_revisions` needs one transaction.

## Disposition by the coordinating session

Draft 5 is not edited, and the P3 notes stay open. The owner decides between two options:
- a Draft 6 with the four P3 fixes and no review, which would leave round 5 unused;
- accepting Draft 5 with these notes.
