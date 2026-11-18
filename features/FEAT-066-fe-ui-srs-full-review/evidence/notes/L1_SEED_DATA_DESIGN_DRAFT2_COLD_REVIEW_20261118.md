# FEAT-066 L1 seed data design Draft 2 — cold review — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5. The caller set effort to high; the reviewer reported that it cannot see the effort setting. Read-only by instruction. Started on the owner's instruction ("làm theo đề xuất"). Scratch folder `tmp/feat066-seed-review-d2/` was created and left empty.
- **Pin reviewed:** `plan/PLAN_L1_SEED_DATA_DESIGN_DRAFT2_20261118.md`, 12,975 bytes, SHA-256 `0AF7B3655B9F69A26C4A839587AFE063E6E0489FD40DCF9E735E1397689FB629`. These also matched:
  - Draft 1 (`E0EE5BED…`);
  - Billing Draft 7 (`216B33D7…`);
  - roadmap Draft 4 (`63710A9F…`);
  - the A-1 register (`3F89EB1D…`);
  - the root SRS (`B9B1F42D…`).
- **What the reviewer did not do (its statement):**
  - No tests, builds, validators, Alembic, app, database, network or state-changing git.
  - No secret, `.env`, `.url` or Bruno environment file opened; the gate secret directory not opened.
  - Root SRS only.
  - Nothing written except the empty scratch folder.
- **Verdict:** NOT READY — **P1=0, P2=5, P3=7**. The design is sound and its safety rules are mostly right. The P2 items can be fixed without a redesign.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Location | Finding | Reviewer's smallest fix |
|---|---|---|---|
| S2-01 | §4.1 Parent groups | `lesson.parent_groups` and `lesson.parent_group_members` do not exist. The real tables are `be1_parent_groups` and `be1_parent_group_members` in the default schema (migration `20261028_ll_0001`; `lesson_library/tables.py`; `CORE_METADATA`) | Correct both names |
| S2-02 | §3; §4.1 Classes; §4.2 Stamp | Three conflicts:<br>(a) Product-path creates after B-2 write `capacity_version_seen` (Billing rule 7a), so the stamp cannot "stay null".<br>(b) After B-2, a create without a subscription or price version is refused, so S1 classes would need S2 first.<br>(c) The current create route uses `uuid4()` and takes no key, so "upsert by stable seed keys" needs B-2 keys or a lookup by name | Choose one design: S1 classes by direct SQL plus one real product create in S2 for the null-stamp path, or S2 before the S1 classes. State the idempotency key |
| S2-03 | §4.1 vs §4.3 | The S3 states (add-on, scheduled downgrade, suspended, GRACE, RESTRICTED, provider-canceled) need more organizations than A, B and C. C must stay ACTIVE at capacity, B is the isolation case, and a scheduled and an applied downgrade cannot coexist in one organization (`ALREADY_SCHEDULED`) | Add an organization-to-case table (for example D GRACE, E RESTRICTED, F canceled) and update the counts |
| S2-04 | §4.1/§4.2 vs §4.3 | Org A has 4 active classes in one place and 6 in another. With either count against target 10, selecting 2 classes is pointless, so a suspension demo needs active > new capacity | Use consistent numbers, for example 12 active on 10 + 2 with 2 selected |
| S2-05 | §2 rule 3 | The guard checks one environment variable, but product code and Billing's own pool build engines from settings (`SKETCH2LIFE_DATABASE_URL`, possibly via the root `.env`). They could write a database the guard never checked | Check the resolved URL. Pass it explicitly to every engine, the Billing pool and Alembic. Require `settings.env` in {local, test}. Name the variable and keep it distinct from the test variable |

## P3 findings (summary)

| ID | Finding |
|---|---|
| S2-06 | "Every row carries a marker" cannot hold for UUID-only or hash tables, or for Billing rows. Define the marker per table, with FK tracing and the count query |
| S2-07 | Missing dependencies:<br>(a) S4 also needs B-1 and S2 (price-version units, organization subscription).<br>(b) The suspended projection needs the outbox publisher or sweep runner and the BE1 consumer.<br>(c) RESTRICTED needs a period at least 7 days in the past.<br>(d) Provider cancellation also needs receipts |
| S2-08 | Seeded state decays: monthly grants expire, and local roll-over applies scheduled downgrades. State a re-seed or reset procedure, or mark the Bruno negatives as time-sensitive |
| S2-09 | StoryRuns "per Parent" fails for the Parent with no profile and for the delete-pending profile. Grant states in code are `PENDING_REVIEW`, `ACTIVE` and `REVOKED`, not "approved". "Superseded" is derived from `current_version_id`. The boundary ages 71, 72, 107 and 108 need a rationale (age bands left open by D-171 item 6 and Q-05) |
| S2-10 | SRS §9.7 says `SYNTHETIC_TEST`; the BE check constraint and D-171 use `SYNTHETIC_DEV`. Note the difference |
| S2-11 | Write paths are already known. The bootstrap scripts need a token or email and are single-shot. Class and profile creation are route functions with random IDs, and the profile route is local/test with `synthetic_pilot_enabled`. So S1 is mostly direct SQL, and `open_subscription` is called separately. Cite `bootstrap_local_pg.py` and the synthetic-pilot fixtures |
| S2-12 | Missing open points: the outbox publisher or sweep runner, and the guard's URL source |

## Checks (reviewer)

- **Tables:** all other §4.1 tables exist with the cited columns and checks.
- **Roles:** `account_role` values and assignment roles exist.
- **Data origin:** `SYNTHETIC_DEV` with null consent satisfies the constraint.
- **Ages:** the 36–120 check is on `parent.profile_revisions`.
- **One active run:** `uq_story_run_active_parent` is a partial unique index, and a DELETE_PENDING run clears the field.
- **Billing Draft 7 consistency holds:**
  - commands only, no direct writes;
  - env-guarded price step;
  - `open_subscription`;
  - the stamp is never written by the seed;
  - the downgrade runs through an internal command;
  - lazy grants;
  - provider cancellation only after B-5;
  - org C arithmetic gives 409.
- **Guard and safety:**
  - the guard refuses `be1_acceptance` databases;
  - synthetic only, no secrets, `upgrade heads`;
  - no local paths, no implied approval;
  - open points match the register;
  - the deliverables match the roadmap L1 gate.

## Not verified (reviewer)

- Alembic head state and runtime behaviour.
- The Q-L2-5 unit value.
- The wording of D-171 item 9.
- Whether direct StoryRun inserts need asset or metadata rows.
- Whether the core audit records fit as the audit sink.
- The register's Billing rows.
- FE screens.

## Disposition by the coordinating session

Draft 2 is not edited. A Draft 3 that fixes S2-01 to S2-12 is proposed to the owner. This was review round 1 for the seed design.
