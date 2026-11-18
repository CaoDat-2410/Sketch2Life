# FEAT-063 M2 — PostgreSQL acceptance gate for M2-AT-08, 09 and 10 — plan Draft 1

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Planning only. It authorizes no code or test edit, no database creation, migration or connection, no test run, no network access, no commit or push.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2. Not independently reviewed.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a` (pushed; draft PR #29). Uncommitted when this draft was written: `plan/M2_S3_TASK_APPROVAL_DRAFT7_20261117.md`, `evidence/M2_S3_DRAFT7_COLD_REVIEW_R1_20261117.md`, and this file.
- **Owner direction:** on 2026-11-17 the owner chose "Lập kế hoạch chạy" (plan the run) over deferring M2-AT-08, 09 and 10 by decision. That choice asks for this plan; it approves nothing in it.
- `OWNER_MODAL_CALL_APPROVED=NO`.

## 1. Why this gate exists

Cold review R1 of S3 Draft 7 (`evidence/M2_S3_DRAFT7_COLD_REVIEW_R1_20261117.md`) found, and the coordinating session confirmed by reading the source documents:

- The owner-accepted M2 planning baseline (D-151: `plan/M2_PARENT_TEACHER_FOUNDATION_PLAN_DRAFT10_20261106.md`, SHA-256 `7539D642FFD95A9A21C99A0C17C5095FF1443E19538017A92789F631D633E2B1`) states in its S3 row that only M2-AT-05, 06 and 07 may be NOT RUN or DEFERRED while S1b is deferred, and that every other M2-AT must run and pass. Its M2-AT-08 row is a PostgreSQL route test.
- M2-S2 was closed on offline evidence. Its approved scope forbade any claim of PostgreSQL or concurrency-under-PostgreSQL success. No record gives M2-AT-08, 09 or 10 a result.
- Therefore M2 cannot be closed by documentation alone. This gate produces the missing evidence, or shows a defect.

This gate does not reopen M2-S2. If it exposes a defect in S2 code, that is a new finding for the owner (section 8).

## 2. Which definition is tested (owner decision PG-D1)

Three documents define these rows, and they differ:

| Source | Status | M2-AT-08 | M2-AT-09 | M2-AT-10 |
|---|---|---|---|---|
| Foundation plan Draft 10, AT table | Owner-accepted planning baseline (D-151, with conditions C1 to C5) | Concurrent separate creates for one owner on PostgreSQL; cancel; restart; job ownership | Three assistance operations through the real route: auth, composition, dependency wiring | Locale and stored-age boundary; persistence and read |
| Foundation plan Draft 11, AT table | Self-described draft; pinned as an input by approved S1a specifications | Same text as Draft 10 | Same text as Draft 10 | Differs from Draft 10 in the path-parameter spelling |
| S2 plan Draft 18, section 4 (`plan/M2_S2_TASK_APPROVAL_DRAFT18_20261114.md`, SHA-256 `5CA09CC6F9D936C1BA74772251F4D3A9C0480F3E6F82818FE11114205FD3E331`) | The S2 plan whose scope the owner approved; it marks all of section 4 "future evidence only; NOT RUN" | A case table of 16 rows (section 3 below) | Three operations with their exact public results | New-run admission at trusted ages 36, 120, 121 and 155 months only |

Recommendation: test the **Draft 18 section 4 cases**, which are the most recent, the most specific and the ones the S2 code was written against, **on PostgreSQL through the composed routes**, which is what the Draft 10 rows add. Where the Draft 10 row asks for more than Draft 18 (process restart; job ownership; locale persistence), the owner decides per item (PG-D4, PG-D5). The texts of the Draft 10 and Draft 11 rows beyond what is quoted in the review record were read only in part for this draft.

## 3. Proposed case list

From Draft 18 section 4. "Offline" marks what the 84 passed tests already exercise without a database; none of it is PostgreSQL evidence.

**M2-AT-08 — Parent create concurrency, cancellation and durable status**

| # | Case | Expected |
|---|---|---|
| 08-01 | Two concurrent creates, same synthetic Parent, same payload, two distinct idempotency keys | One 201, one 409 `ACTIVE_RUN_EXISTS`; exactly one run and one `CREATE_RUN` receipt |
| 08-02 | Same-key create replay | The saved 201 for the existing run |
| 08-03 | Cancel success | 202; `DELETE_PENDING`; active-owner column cleared in the same transaction; receipt with `purge_state` PENDING |
| 08-04 | Same-key cancel replay after the revision advanced | The recorded 202, before any revision comparison |
| 08-05 | Same run, same key, different request | 400 `INVALID_IDEMPOTENCY_KEY` |
| 08-06 | `run_revision` read and increment | Equals `story.runs.revision`; +1 per committed state-changing command; unchanged by read, replay, no-op |
| 08-07 | Cancel with stale `expected_revision` | 409 `STALE_REVISION`; no write |
| 08-08 | Cancel without `expected_revision` | 400 `INVALID_REQUEST` with a field error; no change |
| 08-09 | Cross-run reuse of a cancel key | 400 `INVALID_IDEMPOTENCY_KEY` |
| 08-10 | Late story completion after cancel | 409 `INVALID_STATE_TRANSITION`; no change to run, revision or receipt |
| 08-11 | Late artwork-analysis success after cancel | 409 `PARENT_STORY_RUN_NOT_AWAITING_UNDERSTANDING`; no run change |
| 08-12 | Late failure or unknown outcome after cancel (artwork and story) | 409 `INVALID_STATE_TRANSITION`; no change |
| 08-13 | Artwork-route error envelope | Top-level code, safe message, correlation id, `retryable` false, null retry and field errors |
| 08-14 | Cancel in COMPLETED, FAILED, DELETE_PENDING | 409 each |
| 08-15 | Ownership and lock release | Non-owner cancel or read: 404 `RESOURCE_NOT_FOUND`; after cancel the run is not returned as active and the same Parent can create again |
| 08-16 | Job-status evidence through the two owner reads | `run_state`, `job_state`, `retryable`, `error_code` readable by the owner; 404 for a non-owner |

The 16 cases correspond one to one to the 16 rows of Draft 18's table. Draft 18 also has a code-reading transition table; it is background, not a case. Draft 18 marks its envelope row (08-13 here) as planned static acceptance. Case 08-13 as written in Draft 18 requires a message localized in Vietnamese whose exact wording Draft 18 leaves open; this gate asserts a non-empty safe message and records the wording item as OPEN, unless the owner fixes the wording first.

Cases 08-10 to 08-12 need a late provider result without calling a provider. They are driven by calling the application's result-recording path with synthetic results, as the offline tests do. Whether that satisfies "through the route" for those three cases is part of PG-D1.

**M2-AT-09 — three assistance compatibility operations**

| # | Case | Expected |
|---|---|---|
| 09-01 | First accepted submit, `POST /api/be1/v1/assistance-requests` | 202; receipt envelope and device view as listed in Draft 18; `meta.outcome` created; ETag, `Cache-Control: no-store`, `Vary: Authorization` |
| 09-02 | Status read after an accepted authoritative receipt | 200; `processing_state` `submitted_to_teacher` only with the authoritative receipt; `unknown` in the orphan case |
| 09-03 | Accepted cancel | 200; `meta.outcome` cancelled; device status cancelled; headers as above |

Draft 18 forbids monkeypatching the child-binding builder or replacing the route dependency under test. On PostgreSQL that means seeding real synthetic organisation, class, session, device and consent rows. The existing offline test `tests/integration/test_pilot_assistance_routes_t9.py` monkeypatches; it cannot serve as this evidence. `tests/integration/test_be1_synthetic_pilot_postgres.py` (about 3,400 lines) probably holds reusable seeding; it was not read for this draft.

**M2-AT-10 — trusted stored-age create boundary**

| # | Case | Expected |
|---|---|---|
| 10-01 | New run, trusted age 36 months | 201; `INPUT_PROCESSING`; one run row, one input row, one `CREATE_RUN` receipt; no AI job or outbox row |
| 10-02 | New run, trusted age 120 months | As 10-01 |
| 10-03 | New run, trusted age 121 months | 422 `INVALID_REQUEST`; no run, input or receipt row |
| 10-04 | New run, trusted age 155 months | As 10-03 |

Offline: the create-service unit tests cover out-of-range ages without a database (the collected test ids include 121 and 155; the in-range ids were not checked). On PostgreSQL the trusted age comes from a stored profile row; a profile aged 121 or 155 months has to exist in the test database, which the schema may or may not allow to be inserted. That is not verified and may force a decision.

## 4. Environment

Facts observed on this machine on 2026-11-17, read-only: PostgreSQL services for major versions 17 and 18 are running; Docker is installed; the lock-exact task interpreter has psycopg 3.3.6, SQLAlchemy 2.1.6 and Alembic 1.20.1; the repository marks database tests with `requires_postgres` and reads `SKETCH2LIFE_DATABASE_URL`.

Precedent in this feature: Gate A, Gate B and Gate P2 of S1a ran as owner-run pytest files against a dedicated database (`sketch2life_m2_s1a`, loopback, PostgreSQL 17, a pinned migration revision) with identity guards and before/after table counts in the test file itself. Gate A needed five approval corrections and Gate P2's first attempt failed. That database is pinned at revision `20261109_m2_parent_profiles`, which predates the story-run context migration `20261112_parent_story_context`; it cannot be used as it is.

Proposal:

- A **new disposable database** on loopback, used only for this gate, created empty and migrated with `alembic upgrade heads` from commit `7cc5cf74`. Not the M2 task database, not the Docker `s2l-int` scratch project, not production.
- Synthetic identities and data only. A test token verifier and a test Parent-role reader, as in Gate P2; the production BE1 role adapter stays NOT COVERED (D-190) unless the owner decides otherwise (PG-D3).
- No provider, Modal or external call. Dotenv guarded as in the closure verification (no `.env` in the worktree).
- Egress: the operating-system block used so far is an outbound rule on the interpreter. Whether a loopback connection to PostgreSQL still works under that rule is not known and must be probed before the gate (a connection attempt to the loopback port with the block active). If it does not, the owner decides between a rule that exempts loopback and running without the block.
- The database password never appears in a repository file, a command line recorded in the repository, or a chat message. It is supplied by the owner through an environment variable in the owner's shell.

## 5. Phases

| Phase | Content | Who | Gate |
|---|---|---|---|
| P0 | Owner decisions PG-D1 to PG-D6; cold review of this plan; approval of an exact allowlist | Owner; reviewer | No file changes before it |
| P1 | Write the test code: one new integration test file for AT-08 and AT-10, one for AT-09, each `requires_postgres`, each with database identity guards and before/after table counts. No source file is edited | Coordinating session, under the approved allowlist | Stop if a case cannot be written without changing source |
| P2 | Static checks on the new files only, before anything else runs: syntax, Ruff, Mypy. Lesson of the mapper task: a new file was not lint-checked before its one-shot run | Coordinating session | Zero diagnostics on the new files |
| P3 | Offline collection of the new files (`pytest --collect-only`, no database) | Coordinating session | Collects; every case of section 3 maps to at least one test; mapping table written |
| P4 | Rehearsal on a throwaway database that is not the gate database: full run, repeated as needed until the test code is stable. Not evidence | Owner-run, or the session with the owner present (PG-D2) | Exit when two consecutive runs agree |
| P5 | The gate: fresh disposable database, migrate, one run, outputs captured (JUnit, console, table counts, database identity, hashes of the test files and of the seven S2 source files) | Owner-run (PG-D2) | Ceiling 1; a failure is recorded, not retried |
| P6 | Evidence report; independent review (Sonnet 5.5 high or Opus 5.5 high); owner acceptance of the gate result | Coordinating session; reviewer; owner | — |
| P7 | S3 Draft 8, incorporating review R1 of Draft 7 and this gate's result | Coordinating session | — |

P4 exists because every earlier one-shot check in this lane that had no rehearsal failed on its first run.

## 6. Owner decisions needed

- **PG-D1 — definition.** Test the Draft 18 section 4 cases on PostgreSQL through the composed routes (recommended), with the late-result cases 08-10 to 08-12 driven by synthetic results; or name a different definition.
- **PG-D2 — who runs P4 and P5.** (a) Owner-run with prepared command cards, the coordinating session verifying outputs read-only, as in Gates A, B and P2 (recommended: the session then never holds database credentials); or (b) the session runs them with the owner supplying the connection through the environment.
- **PG-D3 — role adapter.** Keep the production BE1 Parent-role adapter NOT COVERED under D-190 (recommended, to keep the gate bounded), or include it.
- **PG-D4 — restart.** Draft 10's M2-AT-08 mentions restart. Options: (a) "durable status" means a new application instance and a new database connection read the same state (recommended; it tests persistence, which is what a restart proves); (b) a real operating-system process stop and start of a served API, which needs a process runner and more approval surface.
- **PG-D5 — remaining Draft 10 extras.** Job ownership beyond case 08-16, and locale persistence in M2-AT-10: in scope, or recorded as not covered by this gate.
- **PG-D6 — database host.** A new database on the local PostgreSQL 17 service (recommended; same major version as the earlier gates), or a Docker container.
- **PG-D7 — confirmation of the earlier provisional answers.** S3 Draft 7 recorded the owner's reply as accepting S3-D1, S3-D2 and S3-D4; the reviewer found that reading not defensible. They are provisional until the owner states them explicitly. They do not block this gate.

### Owner answers, 2026-11-17 (planning direction only; not an approval to write code, touch a database or run anything)

The coordinating session asked, in these words, "Chấp nhận các đề xuất PG-D1 đến PG-D6 để tôi gửi bản kế hoạch đi review?" The owner answered: "chấp nhận 6 đề xuất và thông tin thêm là postgreSQL chạy 5433 ở 17 và 5432 ở 18 nhưng ko xài 5432 vì 5432 xài ở docker".

- PG-D1 to PG-D6: the six recommendations above are accepted as the planning direction: Draft 18 section 4 cases on PostgreSQL through the composed routes, late-result cases driven by synthetic results; P4 and P5 owner-run with prepared command cards; the production BE1 role adapter stays NOT COVERED; restart means a new application instance and a new database connection; the other Draft 10 extras are recorded as not covered by this gate; a new database on the local PostgreSQL 17 service.
- Owner-supplied environment fact: PostgreSQL 17 listens on port 5433 and PostgreSQL 18 on port 5432; port 5432 is not to be used because it is used by Docker. The gate therefore targets loopback port 5433, major version 17. The session has not probed either port.
- Database names: the session proposed `sketch2life_m2_s2_gate` for the gate and `sketch2life_m2_s2_rehearsal` for the rehearsal. The owner asked what the database was called and did not object to these names, but did not state acceptance of them. They are proposals until the approval text fixes them.
- PG-D7 (explicit confirmation of S3-D1, S3-D2 and S3-D4) was not answered. Those three remain provisional.

## 7. Size and risk, stated plainly

- This is new test code of substantial size: 16 + 3 + 4 cases, with real seeding for the assistance routes. An estimate in lines or days is not offered; the assistance seeding was not read.
- Concurrency tests on a real database can be flaky. Case 08-01 needs two requests that truly overlap; the existing StoryRun-lite concurrency test shows one pattern (threads with events). A flaky gate is worse than no gate; P4 is where that is found.
- A case may fail because the code is wrong. S2 was closed without database evidence, so this is a real possibility, not a formality. Known candidates from the records: the active-owner partial unique index and its conflict mapping; receipt scope for cross-run key reuse (Draft 18 names a stop condition if the existing columns cannot support it); the 121 and 155 month profile rows.
- Section 3's expected results are transcribed from Draft 18. They were not compared with the code as it is at `7cc5cf74`.
- Earlier gates in this feature needed several correction rounds. This plan should be expected to need them too.

## 8. Stop conditions

Stop and return to the owner if: a case cannot be implemented without editing a source file; a case fails in rehearsal for a reason that is a product defect rather than a test defect; the test database is not the expected one (name, host, port, major version, migration heads); any table outside the expected set changes; a provider, Modal or external call would be needed; the egress block and the loopback database cannot both be had; or the definition chosen under PG-D1 turns out to conflict with a decision.

A product defect found here is reported with its evidence. Fixing it needs its own approval; this plan does not authorize source changes.

## 9. Not established by this draft

- The text of decisions D-151 conditions C1 to C5, D-190, D-196 and D-200 to D-202 was not re-read.
- The Draft 10 and Draft 11 AT rows were read only as far as quoted in the review record and one screen of Draft 10.
- The seeding helpers in the existing PostgreSQL tests, the migration chain needed for the assistance routes, and whether `alembic upgrade heads` succeeds on an empty database at this commit.
- Whether the "OpenAPI P3" gate for the two assistance POST operations named in the baseline's S3 row is touched by this gate. It is recorded here as a separate open S3 item.
- Whether co-owner work on another branch already contains PostgreSQL tests for these routes.
