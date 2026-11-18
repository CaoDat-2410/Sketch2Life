# FEAT-063 M2 PostgreSQL gate G1 — rehearsal 1 result — 2026-11-18

- **Status:** rehearsal record, not gate evidence. Owner-run under the rehearsal approval of 2026-11-17 (`approvals/TASK_APPROVAL.md`, "Duyệt chạy thử, xác nhận digest"). Written by the coordinating Claude session (Fable 5.2) from the card summary lines the owner pasted and from the output folder. Not independently reviewed.
- **Commit under test:** `2bfa1ac09dd91a030870e4afae250c6f4d2e2434` on `feature/feat063-m2-s2`; test file `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2`, launcher `00FED31506F1510192471A81DA321CC5EBFD68140E0A089125FF3D4B14959749`, driver `E963B585BFB59FEF3F5ACA70C7D18FCF4E8D9E4FFB0FEAD3AF2062EB70A97CD6`. No file was changed during the run.
- **Resources:** container and volume `s2l-m2-s2-rehearsal-1`, database `sketch2life_m2_s2_rehearsal` on `127.0.0.1:55441`, API on `127.0.0.1:55451`, run marker `b736d44ffea64141a3e36afc36de63b5`. Egress flag not used. The container is stopped and kept.

## Cards

| Card | Summary line | Result |
|---|---|---|
| C0 `preflight` | `PREFLIGHT OK rehearsal-1 interpreter=3.12.10` | OK |
| C1 `container-up` | `CONTAINER UP s2l-m2-s2-rehearsal-1 marker=b736d44f... empty database confirmed` | OK |
| C2 `migrate` | `MIGRATED 13 heads, 10 version rows, 123 tables` | OK |
| C3 `test` | exit code 1, 3 passed, 17 failed, 15.3 s, not timed out | see below |
| C4 `container-stop` | `STOP exit=0 container=s2l-m2-s2-rehearsal-1 (kept)` | OK |

Output folder (scratch, repository-root `tmp/m2-s2-pg-gate/runs/rehearsal-1/`): `result.json` SHA-256 `867087C8C913A24A1148190B7A4A9608079A3AACEAFB782989AE74992E85232C`; `pytest-output.txt` SHA-256 `EF51D9941ADE66354C5FAEB935D8C5624B9970914E526FB7296A365715382E5B`.

## What the run established

- The cards work end to end on first use: container start with the mounted bootstrap password file, role and database creation, the run marker, the client password file with a passwordless URL, the single guarded `alembic upgrade heads`. Alembic printed exactly the 13 pinned heads and left exactly the 10 pinned version rows; all 31 migrations applied to an empty database as a non-superuser owner (123 tables).
- The launcher builds and serves the real application under the test environment without a source edit; the readiness check and the synthetic verifier work.
- **Passed (3 items):** `test_08_01a_unique_index_path_is_deterministic` (10 executions: the create waits on the unique index behind the held row and returns 409 `ACTIVE_RUN_EXISTS`; ten unique violations of `uq_story_run_active_parent` in the server log); `test_10_03_04_database_refuses_out_of_range_ages` at 121 and 155 (both check constraints by name).
- **Failed (17 items), one cause:** every create that should succeed returned 503 `PARENT_STORY_RUN_STORE_UNAVAILABLE`.

## Cause of the 17 failures: a second product defect

The stopped container's log (read with `docker logs`, read-only) shows, eighteen times:

```text
ERROR:  new row for relation "run_inputs" violates check constraint "ck_story_run_input_lesson_pin_snapshot"
```

`create_run` inserts `lesson_pin_snapshot=None` into a `JSONB` column (`parent_story_repository.py:103, 135`; column defined without `none_as_null` in `infrastructure/story_run_lite/tables.py`). SQLAlchemy's JSON type binds an explicit Python `None` as the JSON value `null`, not SQL NULL, unless `none_as_null` is set (`sqlalchemy/sql/sqltypes.py`, JSON bind processor). The check constraint requires both lesson-pin columns to be SQL NULL or both set; a JSON `null` with a NULL hash satisfies neither branch. The repository maps the integrity error to 503.

Effect: **on PostgreSQL, `POST /v1/story-runs` without a lesson version fails for every caller.** The offline tests do not exercise the PostgreSQL JSON binding, so S2 closed without seeing it. `attach_artwork` passes the same explicit `None` (`parent_story_repository.py:632-636`).

This is established by execution (the server's constraint error) plus reading (the binding rule). It is in pushed product code and outside this gate's approved scope; nothing was changed.

## Status of the first defect (`attach_artwork`, review finding H1)

Not reached. Case 08-03p failed at its first step, the create, with the 503 above. The `attach_artwork` reading is still unconfirmed by execution.

## Not established

- Anything about the 17 failed items beyond their first create call.
- The restart leg, the natural race (08-01b), all cancel cases, level R, and the two in-range M2-AT-10 cases: none ran past the create.
- Server log lines `FATAL: role "root" does not exist` come from the readiness check inside the container and are not a fault.

## Next (owner's decision)

No further rehearsal is useful until create works on PostgreSQL. The product defects (lesson-pin JSON `null`; the believed `attach_artwork` flush defect) need a separate, approved fix task, then new pins and a new commit, then rehearsal 2.
