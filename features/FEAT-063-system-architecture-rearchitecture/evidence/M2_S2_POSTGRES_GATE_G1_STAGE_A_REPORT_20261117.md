# FEAT-063 M2 PostgreSQL gate G1 — Stage A report — 2026-11-17

- **Status:** Stage A work complete; awaiting the owner. Nothing here is gate evidence: no test was executed, no database, container, socket or listening process was used.
- **Authority:** Stage A approval entry in `approvals/TASK_APPROVAL.md` (owner: "Duyệt chặng A"), on `plan/M2_S2_POSTGRES_GATE_G1_TASK_APPROVAL_DRAFT2_20261117.md`, SHA-256 `5CCA1171534E8A4FD431E7FF0FAB4E645F3DE4CFA3AA942F1BDA8F996745FE4C`. Approval record after that entry: 480,856 bytes, SHA-256 `3525632ECE9A43D4D1DE5E9D301430C1BF81C58131F8B71CBE226B1E56DDD0CE`.
- **Author:** coordinating Claude session (Fable 5.2). Not independently reviewed.
- **Worktree:** `.worktrees/m2-s2`, branch `feature/feat063-m2-s2`, HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a`. Nothing staged, committed or pushed.

## 1. Files written

| File | Bytes | SHA-256 |
|---|---:|---|
| `backend/tests/integration/test_m2_s2_g1_parent_story_postgres.py` | 47,233 | `19D737A220AFC415D8EE46CBA1443C6F6C9DFBBE604BFD4181D9347D8318594E` |
| `backend/tests/integration/m2_s2_g1_launcher.py` | 5,075 | `E251365CA0ABFA570BFB5CA0F02EFCC45B22FEEAAEDDC8091A7DCC10C8440E40` |

No existing source, test or configuration file was edited. Scratch (git-ignored, repository-root `tmp/m2-s2-pg-gate/`): the owner-run driver `g1_gate_driver.py`, 20,617 bytes, SHA-256 `5BD89F530B1557621E8EC19B79F13BB08342168920EB47B936E78141072E84E0`; the migration manifest `migration_file_hashes_7cc5cf74.txt` (31 lines), SHA-256 `8659E108D86135859A5F5EF8944A95CE9376DF818484B6744CCF474CFED9CAB6`; static-check outputs and caches.

## 2. Static checks (task interpreter: Python 3.12.10, Ruff 0.17.2, Mypy 1.20.2, pytest 8.4.2)

| Check | Runs used (ceiling 20) | Final result |
|---|---:|---|
| Syntax (`ast.parse`) on both files | 1 | OK |
| Ruff on both files | 3 | exit 0, "All checks passed!" (run 1: one `E501`; fixed) |
| Mypy, strict project configuration, on both files | 2 | exit 0, "no issues found in 2 source files" (run 1: three diagnostics in the two files; fixed) |
| Byte-level check | 1 | LF only, no trailing whitespace, single final newline in both |
| `pytest --collect-only`, all database and libpq variables unset | 1 | exit 0, 20 tests collected |
| `validate_harness`, `validate_repository_security`, `validate_architecture`, `git diff --check` | 1 each | exit 0 each |

Collection imports the product package and loads the launcher module by path (standard-library imports only at its top level). Neither file creates an engine, opens a connection or builds the application at import time.

The driver was checked with Ruff (rules E, F, B, I) and Mypy strict: clean. Only `--help` was executed.

## 3. Case map (Draft 4 section 6 as amended by Draft 2)

| Case | Test function | Notes |
|---|---|---|
| 08-01a | `test_08_01a_unique_index_path_is_deterministic` | 10 executions, fresh account each; holder row by SQL on a second connection; lock wait observed through `pg_blocking_pids`; DV-13, DV-14 |
| 08-01b | `test_08_01b_concurrent_creates_leave_one_active_run` | 10 executions; two requests released by a barrier |
| 08-02 | `test_08_02_create_replay_returns_the_same_run_without_writes` | Row contents compared, not only counts; DV-16 |
| 08-03 | `test_08_03_cancel_marks_delete_pending_and_releases_the_owner` | |
| 08-03p | `test_08_03p_cancel_from_preparation_review_keeps_inputs_and_assets` | State built with `attach_artwork`, `record_understanding`, `confirm_subject` on the product session factory; a failure of `attach_artwork` fails the test with a STOP message (review R1 G2) |
| 08-04 | `test_08_04_cancel_replay_returns_the_recorded_response` | |
| 08-05 | `test_08_05_same_key_with_a_different_request_is_refused` | |
| 08-06 | `test_08_06_run_revision_tracks_committed_state_changes` | |
| 08-07 | `test_08_07_stale_expected_revision_is_refused_without_a_write` | Also asserts `current_version` |
| 08-08 | `test_08_08_missing_expected_revision_is_a_request_error` | |
| 08-09 | `test_08_09_cancel_key_reused_on_another_run_is_refused` | |
| 08-14 | `test_08_14_cancel_in_a_terminal_state_is_refused` | FAILED via `fail_drawing_analysis`; COMPLETED via one SQL update on a route-created run; DV-15 |
| 08-15 | `test_08_15_ownership_and_lock_release` | |
| 08-16 | `test_08_16_job_status_is_readable_by_the_owner_only` | Active read and by-identifier read |
| Level R | `test_level_r_late_results_are_refused_after_cancel` | Six calls: understanding success; drawing failure and unknown; story completion; story failure and unknown |
| 10-01, 10-02 | `test_10_01_02_run_is_created_at_both_age_bounds` (36, 120) | DV-8, DV-17 |
| 10-03, 10-04 | `test_10_03_04_database_refuses_out_of_range_ages` (121, 155) | Both check constraints by name; DV-7 |
| Restart leg | `test_restart_keeps_committed_state` | Last in the file; DV-1, DV-2 |

Twenty collected items: eighteen functions, two of them parametrized twice.

## 4. Seeding statements (all in the test file; DV-9, DV-10)

1. `INSERT INTO be1_adult_identities (subject, account_id, issuer, state, account_role, role_revision) VALUES (..., 'active', 'parent', 1)` — one per test account.
2. `INSERT INTO parent.child_profiles (parent_profile_id, owner_issuer, owner_subject, state, current_revision_no, data_origin) VALUES (..., 'ACTIVE', 1, 'SYNTHETIC_DEV')` and `INSERT INTO parent.profile_revisions (profile_revision_id, parent_profile_id, revision_no, age_months, display_name, interests_summary, authored_by_issuer, authored_by_subject, revision_hash)` — one transaction per account.
3. Holder row for 08-01a: `INSERT INTO story.runs (run_id, actor_scope_kind, actor_scope_ref, profile_ref, run_state, revision, version, active_owner_parent_account_id)`; committed after the lock wait is observed; that account is not read again.
4. COMPLETED run for 08-14: `UPDATE story.runs SET run_state = 'COMPLETED', active_owner_parent_account_id = NULL, revision = revision + 1, version = version + 1` on a route-created run.
5. Refused inserts for 10-03 and 10-04 (the same two profile statements with 121 or 155 months, and a `story.runs` insert carrying that age); nothing is stored.

The test deletes nothing.

## 5. Differences from the approved text, for the owner's attention

- **Start-of-run emptiness check.** Draft 4 guard 6 says "no rows in any migrated table". The test checks emptiness of the fourteen tables it reads or writes and records counts of every table before and after in `table-counts.json`. Reason: whether any of the 31 migrations inserts reference rows was not established by reading; a blanket check could fail a correct database. To be confirmed in the first rehearsal.
- **Process identifiers.** The launcher reports its own identifier; the test also records the identifier of the process it spawned. On Windows a virtual-environment interpreter may be a redirector that starts a child, so the two can differ. The test terminates the process tree, then requires both identifiers to be gone and the port to refuse connections. It does not require the two identifiers to be equal (review R3 F10 asked to compare them).
- **Egress block.** The driver measures whether outbound traffic is blocked by attempting one connection to a documentation-only address (`192.0.2.1`), and can require the block with a flag. Loopback under the block is not probed separately; the first rehearsal with the flag shows it.

## 6. Not established

Everything listed in Draft 2 section 7 remains unestablished, in particular: whether the application serves from the launcher; whether `attach_artwork` works under the product session factory (G2); whether the client library accepts the password file with these URL forms; Alembic's actual head and version-row output; behaviour of abrupt termination on Windows; the assumption that the create and subject-confirmation receipts carry the run identifier in `resource_ref` (case 08-03p expects two such receipts).
