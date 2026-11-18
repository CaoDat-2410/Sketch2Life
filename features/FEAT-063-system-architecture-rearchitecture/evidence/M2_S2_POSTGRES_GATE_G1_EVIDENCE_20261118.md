# FEAT-063 M2 — PostgreSQL acceptance gate G1 (reduced) — evidence report — 2026-11-18

- **Gate result: PASSED WITH DEVIATIONS (DV-1 to DV-19), on the second attempt. Awaiting independent review and the owner's acceptance.** This report is not an acceptance of M2-AT-08 or M2-AT-10.
- **Author:** coordinating Claude session (Fable 5.2), from the summary lines the owner pasted and from the output folder. The owner ran the gate; the session ran nothing against the database and never read the secret directory.
- **Review:** revision 2 of this report. Revision 1 (SHA-256 `0DA1DAAFDACD509D5798EBFB875A8D9581A9D4346FCD0006B1D5F1830CED3BC8`) was independently reviewed (Sonnet 5.5, high): report ACCURATE WITH NOTES, result SUPPORTED WITH NOTES, 0 P1 / 2 P2 / 9 P3 (`evidence/M2_S2_POSTGRES_GATE_G1_EVIDENCE_REVIEW_R3_20261118.md`). Revision 2 addresses those notes in wording and stated limits; no result value changed. Revision 2 itself is not re-reviewed.
- **Authority:** gate-run approval (`plan/M2_S2_POSTGRES_GATE_G1_GATE_RUN_TASK_APPROVAL_DRAFT1_20261118.md`, SHA-256 `10FDF73F2F155F3C83C784FDFB26401C0BCC9567B81FA564D1D6EE17A8766F08`) and the approval of a second attempt, both in `approvals/TASK_APPROVAL.md` (owner: "Duyệt chạy gate"; "Duyệt lượt 2"); approval record at the gate commit: 493,048 bytes, SHA-256 `7A4C4397448512C81F0EDF132B837F344C55F1B99DEC2ED4682702BE2F83B00C`.
- **Governing texts:** G1 Draft 2 (`plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT2_20261117.md`, `5CCA1171...`: decisions, DV-1 to DV-18, claim rule), the plan it carries (`plan/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT4_20261117.md`, `EBA29DEA...`), Stage B Draft 2 (`07F93EC6...`), and the gate-run draft above (DV-19, extended claim rule).

## 1. This was the second attempt

Gate attempt 1 (container `s2l-m2-s2-gate`, commit `a83bf4f0`) has **no result**: the container was stopped by the stop card while the test card was still running its twentieth item, and the test process was then interrupted. It is recorded as interrupted by an operator action, neither a pass nor a product failure, in `evidence/M2_S2_POSTGRES_GATE_G1_GATE_ATTEMPT_1_INTERRUPTED_20261118.md`. Its container, volume and outputs are kept. The cause was a card design that let two cards overlap; the driver was changed to run the steps in one process (`run-all`), that action was rehearsed once (rehearsal 5, 20 passed), and the owner approved one further attempt. Nothing in the product, the test file or the launcher changed between the attempts (the two commits differ only in the approval record and the attempt-1 record).

**How this relates to the approved rule.** The gate-run approval said that once the test step has started, anything other than a full pass is a FAILED gate with the one attempt consumed. Read literally, attempt 1 falls under that rule: its test step had started and it produced no pass. It is recorded instead as an operator interruption because no assertion failed and the database was taken away from outside; and the second attempt exists only because **the owner, told this, approved one more attempt**. This result is therefore the outcome of an owner-approved retry, not of the single attempt first approved. Attempt 1 gives no evidence of a defect in its twentieth item (the restart test) and no pass for it: that item was waiting at its first database read after the restart when the container went away.

## 2. Identity of the run

| Item | Value |
|---|---|
| Commit (`--expect-head`) | `67ef7d7c26f9e0a00872c23f2375900e538286fe` on `feature/feat063-m2-s2`. The driver checked HEAD and that no tracked file was modified before each step (not after the test); the session found the tracked tree clean after the run |
| Test file | `backend/tests/integration/test_m2_s2_g1_parent_story_postgres.py`, SHA-256 `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2` |
| Launcher | `backend/tests/integration/m2_s2_g1_launcher.py`, SHA-256 `00FED31506F1510192471A81DA321CC5EBFD68140E0A089125FF3D4B14959749` |
| Product file repaired before the gate | `backend/src/sketch2life/infrastructure/persistence/parent_story_repository.py`, SHA-256 `5E33C076A4A13439AB0D02A8D8088D543D277758E78076D709E23CB386CFBDA8` (checked by the session before and after the run) |
| Driver (scratch; copy kept in the output folder) | SHA-256 `02E2A45D6F271690382066476DB0F49451A6B1445F72624269FD6F340B732737` |
| Migrations | 31 files, manifest SHA-256 `8659E108D86135859A5F5EF8944A95CE9376DF818484B6744CCF474CFED9CAB6`, verified by the driver |
| `pyproject.toml` / `uv.lock` | `35F7635D77D80D787AB127C46D625C6FFE175F5C538759161E4B5B4549638AC2` / `830842CFAC04B5CA1EBDAA733E281F7D0AB9A4C94B19CFDF2B93E66854DBFB13` |
| Tools | Python 3.12.10; pytest 8.4.2; SQLAlchemy 2.1.6; Alembic 1.20.1; psycopg 3.3.6; uvicorn 0.54.0; httpx 0.28.1; FastAPI 0.162.0 |
| Image | `postgres@sha256:3540c0362c809df084ffac0ae69fe794515f9de92692f02178bcdce0ef0302ac`; server version number 170011 |
| Container and volume | `s2l-m2-s2-gate-2`, published only on `127.0.0.1:55440`; started 2026-11-17T18:03:30Z, stopped 18:04:00Z; **stopped and kept** |
| Database and role | `sketch2life_m2_s2_gate`, role `s2l_m2_gate` (not a superuser; owns the database) |
| Run marker | `53ef2c531e284bd2b9c5486e5e20910c` as printed by the driver. The driver and the test fixture stop on a mismatch; the value itself is in no output file, only in that printed line and in the secret directory |
| API | real application in a child process on `127.0.0.1:55450`; imported package path under this worktree |
| Command | one driver command: `<task interpreter> -I -B <driver> run-all --mode gate --index 2 --secret-dir <secret directory> --expect-head 67ef7d7c26f9e0a00872c23f2375900e538286fe`, run from `backend/`; it ended with `RUN-ALL complete` (the driver prints that only when no step stopped; its numeric exit code was not captured). Test step: `python -B -m pytest -o addopts= -p no:cacheprovider --basetemp=<output>/pytest-basetemp --tb=short -rA tests/integration/test_m2_s2_g1_parent_story_postgres.py` |

Pasted driver output: `PREFLIGHT OK gate-2 interpreter=3.12.10`; `CONTAINER UP s2l-m2-s2-gate-2 marker=53ef2c53... empty database confirmed`; `MIGRATED 13 heads, 10 version rows, 123 tables`; `RESULT {"run_label": "gate-2", "exit_code": 0, "timed_out": false, "passed_count": 20, "not_passed": {}, "all_passed_no_skips": true, "egress_blocked": null, "seconds": 21.5}`; `STOP exit=0 container=s2l-m2-s2-gate-2 (kept)`; `RUN-ALL complete`.

## 3. Result

**20 passed, 0 failed, 0 skipped, exit code 0, not timed out** (`20 passed in 20.69s`). The driver found neither generated password in the output files present when the test step ended; the two files the session added afterwards (section 5) were not part of that scan.

| Case (plan Draft 4 section 6 as amended) | Test | Outcome |
|---|---|---|
| 08-01a unique-index path, 10 executions | `test_08_01a_unique_index_path_is_deterministic` | PASSED |
| 08-01b natural race, 10 executions | `test_08_01b_concurrent_creates_leave_one_active_run` | PASSED |
| 08-02 create replay | `test_08_02_create_replay_returns_the_same_run_without_writes` | PASSED |
| 08-03 cancel | `test_08_03_cancel_marks_delete_pending_and_releases_the_owner` | PASSED |
| 08-03p cancel from `PREPARATION_REVIEW`, D-127 retention | `test_08_03p_cancel_from_preparation_review_keeps_inputs_and_assets` | PASSED |
| 08-04 cancel replay | `test_08_04_cancel_replay_returns_the_recorded_response` | PASSED |
| 08-05 same key, different request | `test_08_05_same_key_with_a_different_request_is_refused` | PASSED |
| 08-06 run revision | `test_08_06_run_revision_tracks_committed_state_changes` | PASSED |
| 08-07 stale revision | `test_08_07_stale_expected_revision_is_refused_without_a_write` | PASSED |
| 08-08 missing revision | `test_08_08_missing_expected_revision_is_a_request_error` | PASSED |
| 08-09 key reused on another run | `test_08_09_cancel_key_reused_on_another_run_is_refused` | PASSED |
| 08-14 cancel in FAILED, COMPLETED, DELETE_PENDING | `test_08_14_cancel_in_a_terminal_state_is_refused` | PASSED |
| 08-15 ownership and lock release | `test_08_15_ownership_and_lock_release` | PASSED |
| 08-16 job status | `test_08_16_job_status_is_readable_by_the_owner_only` | PASSED |
| Level R late-result guards, six calls | `test_level_r_late_results_are_refused_after_cancel` | PASSED |
| 10-01, 10-02 ages 36 and 120 | `test_10_01_02_run_is_created_at_both_age_bounds[36]`, `[120]` | PASSED, PASSED |
| 10-03, 10-04 ages 121 and 155 refused by the database | `test_10_03_04_database_refuses_out_of_range_ages[121]`, `[155]` | PASSED, PASSED |
| Restart leg | `test_restart_keeps_committed_state` | PASSED |

## 4. Observations from the outputs

- **Migration.** Empty database confirmed before the upgrade (no table, no version row). `alembic heads` printed exactly the 13 pinned heads (listed in G1 Draft 2 section 4; three of them are named in another revision's `depends_on`, which is why 10 version rows result). One `alembic upgrade heads`: 31 revisions applied; `alembic_version` holds exactly the 10 pinned rows (`20261017_lc_0001`, `20261018_ap_0009`, `20261018_kv_0001`, `20261018_vr_0001`, `20261019_ae_0001`, `20261019_pa_0001`, `20261019_vf_0001`, `20261109_m2_parent_profiles`, `20261110_ar_0001`, `20261112_parent_story_context`); 123 tables.
- **Table counts.** Before the test every table was empty except `alembic_version` (10). After: `be1_adult_identities` 40, `parent.child_profiles` 40, `parent.profile_revisions` 40, `story.runs` 41, `story.run_inputs` 32, `story.command_receipts` 42, `story.understanding_revisions` 1, `story.review_decisions` 1, `core_asset_metadata` 2, `core_asset_lineage` 1. `ai_jobs.job`, `ai_jobs.outbox` and `core_outbox_events` stayed at 0. No other table changed. These counts are identical to rehearsals 2 to 5.
- **Restart.** Process identifiers before the stop: 11388 (spawned by the test) and 36364 (reported by the launcher); after the start: 58880 and 5548. The two identifiers of a pair differ because the task interpreter starts the real interpreter as a child; the test ended the process tree, required both old identifiers gone and the port to refuse connections, then started a new process.
- **Server log** (error-level and shutdown lines saved by the session after the run with read-only `docker logs`, before anything else touched the container): 19 violations of `uq_story_run_active_parent`; two violations each of `ck_story_run_child_age_months` and `ck_parent_profile_revisions_age_months_36_120` (cases 10-03, 10-04); one `FATAL: role "root" does not exist` from the readiness check inside the container; shutdown lines of the image's initialisation restart and of the final stop. No other error-level line. The independent reviewer re-read the full container log: besides these it holds only benign initialisation and shutdown notices (a locale warning, the image's trust-authentication notice, a replication-launcher line), and no PANIC, deadlock, "could not" or timeout line.
- **Concurrency, an inference from that log.** The log carries no per-case tag. The first ten unique-index violations come from one database session at regular intervals, consistent with case 08-01a (one per execution, by design; it runs first). The next nine alternate between two database sessions, the second of which appears only there, consistent with case 08-01b. If that attribution is right, in at least nine of the ten natural-race executions the losing request passed the existence read and was then refused by the unique index under real two-connection concurrency. Nothing is concluded about the tenth execution. All ten returned one 201 and one 409 `ACTIVE_RUN_EXISTS`, since the test passed. The test itself does not measure overlap (DV-14).
- Both launcher log files are empty (0 bytes): the launcher logs at warning level and nothing was logged.
- Container start and stop times are in UTC (local time is seven hours ahead). The output files were written about 0.2 seconds before PostgreSQL logged the shutdown request, so the container stopped after the test had finished; no other gate or rehearsal container was running during the run.

## 5. Output files (scratch, repository-root `tmp/m2-s2-pg-gate/runs/gate-2/`, git-ignored)

| File | SHA-256 |
|---|---|
| `result.json` | `A71AF9637C3C104B64819931C5E164D8AC511653D169B00D1E5566D2C5FE29A8` |
| `pytest-output.txt` | `57F14D5493B6A8D256433F610C997DC9529B95732DA34E189A99586F1C000204` |
| `table-counts.json` | `0FF525FC7A681371F82D9365374DD0239B0E57BDA954635C3E6DC008912BD212` |
| `restart-process-ids.json` | `DA3CB7C6C72DB1E52A5420FFF190257A39E1848E24F751A08EEA5A02396089DD` |
| `probe-before-migration.json` | `28A798C2F2B06C9172A619B65A55566A1FCCCC0933CEC7339587BEC56291E881` |
| `probe-after-migration.json` | `7EFDC4B6ED0443C0E6C5B86CD62078EBCF7390D49E8E87A0BF18300AEC3087D5` |
| `alembic-upgrade.txt` | `421C29D2EEE447A04249AF84122CBBFB61AF1C831FCEFA5289FA5C7A4331E965` |
| `container-inspect.json` | `355FC499F18CA47443917395835F08D7CA9A82F7118665B735C9D0FA3852B170` |
| `container-log-filtered-lines.txt` (added by the session after the run) | `6BE1B252D3ACB81646E9EEFF266D332FDB8EACB2412F6274AEC948FF5962D265` |
| `g1_gate_driver_used_02E2A45D.py` (copy added by the session) | `02E2A45D6F271690382066476DB0F49451A6B1445F72624269FD6F340B732737` |

These files exist only on the owner's machine. They are not in the repository.

## 6. What this result shows, and what it does not

**Shown** (claim rule): gate G1 passed with deviations DV-1 to DV-19 — on one PostgreSQL 17 container migrated to the 13 pinned heads, through the composed Parent story-run routes served by a real process, with a synthetic token verifier and seeded data, **without an operating-system egress block**: the route cases 08-01 to 08-09 and 08-14 to 08-16, the D-127 cancel from `PREPARATION_REVIEW` with retention, the late-result guards at repository level, persistence across a real process stop and start, creation at 36 and 120 months, and refusal by the database of 121 and 155 months.

**Not shown:**

- Everything in DV-1 to DV-19. The full table with the baseline clause of each is in G1 Draft 2 section 3.1 (DV-1 to DV-18) and the gate-run draft section 4 (DV-19). In short:
  - DV-1 recovery after restart (only persistence is shown). DV-2 stale results after restart. DV-3 late results through the routes on PostgreSQL (repository level only). DV-4 a Teacher actor (Parent only).
  - DV-5 "job" is shown only as zero job and outbox rows; these commands create none.
  - DV-6 the `PREPARATION_REVIEW` state of case 08-03p is built by calling the product's repository methods from the test process, not through the provider routes; only the cancel goes through the route.
  - DV-7 the service-level refusal of out-of-range ages on PostgreSQL: the gate asserts that the database refuses them, the opposite of the baseline's "Test không giả định DB chặn 121". DV-8 locale; the product's own persist and serialize of profile revisions.
  - DV-9 the Firebase verifier and the production role adapter (synthetic verifier). DV-10 identities, profiles and the 08-01a holder row are inserted by SQL; the COMPLETED run is a route-created run changed by one SQL update.
  - DV-11 rehearsal containers were removed between rehearsals; both gate containers are kept. DV-12 M2-AT-09.
  - DV-13, DV-15, DV-19 the gate asserts more than the approved cases in three places (the loser's exact code; the code for cancel in a terminal state; `current_version` on a stale revision).
  - DV-14 overlap in the natural race is not guaranteed or measured by the test. DV-16 case 08-02 does not assert that a replayed create returns an identical body. DV-17 "không clamp" only indirectly, at 36 and 120. DV-18 "không coi là đã xóa" only indirectly (rows unchanged, state, purge state, owner read).
- S2 Draft 18 row 13 (the artwork-route error envelope) has no case in this gate.
- This is one passing gate run, on one machine, on one PostgreSQL minor version (17.11).
- Anything about M2-AT-09.
- Behaviour with a real provider.
- Create **with** a lesson version.
- The pending-receipt write used by story-revision reservation (product defect W3: fixed by reading and unit-tested offline, not exercised on PostgreSQL).
- Privileges of a separate runtime database role: the API ran as the role that owns the schema.
- Containment was by the literal loopback database URL, the driver's identity and marker probes, the cleared environment and a Python-level socket guard (blocking connects and name lookups only; it cannot see the database driver's native connections); no operating-system egress block was active. Inside the container the local socket uses trust authentication (image default); only the driver's own commands used it.

## 7. What the gate work found in the product

Rehearsal 1 exposed that `POST /v1/story-runs` without a lesson version failed on PostgreSQL for every caller; reading then found three related write defects. All four were repaired in commit `b430b67a` (`evidence/M2_S2_PARENT_STORY_POSTGRES_WRITE_DEFECTS_FIX_EVIDENCE_20261118.md`). Three are now exercised on PostgreSQL by this gate (create, the lesson-pin value in `attach_artwork`, the flush before the lineage insert); the fourth (W3) is not. M2-S2 had been closed on offline evidence while these defects existed.

## 8. History of runs

| Run | Commit | Result |
|---|---|---|
| Rehearsal 1 | `2bfa1ac0` | 3 passed, 17 failed: product defect W1 |
| Rehearsals 2, 3, 4 | `b430b67a` | 20 passed each |
| Gate attempt 1 | `a83bf4f0` | interrupted by an operator action; no result |
| Rehearsal 5 (`run-all`) | `a83bf4f0` | 20 passed |
| **Gate attempt 2** | `67ef7d7c` | **20 passed** |

## 9. Open for the owner

1. Independent review of revision 1 is done (see the header).
2. Acceptance decision: whether "gate G1 passed with deviations DV-1 to DV-19" is enough for the M2-AT-08 and M2-AT-10 rows of the S3 ledger.
3. M2-AT-09: gate G2 or a recorded deferral.
4. Kept resources on the owner's machine: containers and volumes `s2l-m2-s2-gate` (attempt 1) and `s2l-m2-s2-gate-2` (this result), rehearsal containers 4 and 5, the output folders and the secret directory. None is removed without the owner's word.
