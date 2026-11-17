# FEAT-063 M2 PostgreSQL gate G1 — rehearsal 2 result — 2026-11-18

- **Status:** rehearsal record, not gate evidence. Owner-run under the rehearsal approval of 2026-11-17. Written by the coordinating Claude session (Fable 5.2) from the card summary lines the owner pasted and from the output folder. Not independently reviewed.
- **Commit under test:** `b430b67a68e7934721f7ec9b44b96e9071cb989e` on `feature/feat063-m2-s2` (the fix of the four PostgreSQL write defects). Pins unchanged: test file `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2`, launcher `00FED31506F1510192471A81DA321CC5EBFD68140E0A089125FF3D4B14959749`, driver `E963B585BFB59FEF3F5ACA70C7D18FCF4E8D9E4FFB0FEAD3AF2062EB70A97CD6`. The worktree was clean at that commit before and after the run.
- **Resources:** container and volume `s2l-m2-s2-rehearsal-2`, database `sketch2life_m2_s2_rehearsal` on `127.0.0.1:55441`, API on `127.0.0.1:55451`, run marker `4148afc1350141729914f32fbe1cdba7`. Egress flag not used. The container is stopped and kept. The rehearsal-1 container and volume were removed first with card C5.

## Cards

| Card | Summary line | Result |
|---|---|---|
| C5 (rehearsal 1) | `REMOVED container exit=0 volume exit=0` | OK |
| C0 `preflight` | `PREFLIGHT OK rehearsal-2 interpreter=3.12.10` | OK |
| C1 `container-up` | `CONTAINER UP s2l-m2-s2-rehearsal-2 marker=4148afc1... empty database confirmed` | OK |
| C2 `migrate` | `MIGRATED 13 heads, 10 version rows, 123 tables` | OK |
| C3 `test` | `exit_code 0, passed_count 20, not_passed {}, all_passed_no_skips true, 25.3 s` | **20 passed** |
| C4 `container-stop` | `STOP exit=0 container=s2l-m2-s2-rehearsal-2 (kept)` | OK |

Cards C1 and C3 were each entered a second time by mistake. The driver refused both (`STOP: container ... already exists`; `STOP: the test run was already started for this database (ceiling 1)`); nothing ran twice.

Output folder (scratch, repository-root `tmp/m2-s2-pg-gate/runs/rehearsal-2/`): `result.json` SHA-256 `4BB6F63BE3D731FB60DD7DA05321733409C8C3609EF16DF1741F06E606F70701`; `pytest-output.txt` SHA-256 `9B0177CB357DCC5608E6615E91211044946FFCE14FA42E9F74B7796F6F9DE65C` (last line: `20 passed in 24.36s`). `result.json` records no credential in any output, the imported package path under this worktree, and the tool versions (Python 3.12.10, pytest 8.4.2, SQLAlchemy 2.1.6, Alembic 1.20.1, psycopg 3.3.6, uvicorn 0.54.0, httpx 0.28.1, FastAPI 0.162.0).

## Read from the outputs

- **All 20 items passed, none skipped**: every route case, the cancel from `PREPARATION_REVIEW`, the six repository-level late-result calls, both in-range and both out-of-range age cases, and the restart leg.
- **Fix verified on PostgreSQL for W1, W2 and W4.** Creates succeed (W1). Case 08-03p reached `PREPARATION_REVIEW` through `attach_artwork`: after the run `core_asset_metadata` holds 2 rows, `core_asset_lineage` 1, `story.understanding_revisions` 1, `story.review_decisions` 1 (W2, W4). W3 (the pending receipt) is not exercised by this gate and stays unverified on PostgreSQL.
- **Concurrency.** The server log has 19 violations of `uq_story_run_active_parent`: 10 from case 08-01a (one per execution, as designed) and 9 from case 08-01b. So in 9 of the 10 natural-race executions the losing request reached the unique index while the winner was in flight; in the tenth the loser was refused by the earlier existing-run read. Both paths gave 409 `ACTIVE_RUN_EXISTS`.
- **Restart.** Old process identifiers 55064 (spawned) and 41180 (reported by the launcher), new 43676 and 58744. The spawned and reported identifiers differ, which confirms that the task interpreter is a redirector that starts the real interpreter as a child; the tree termination ended both, the port refused connections, and the new process served the same state.
- **Database content.** Before the run every table was empty except `alembic_version` (10 rows). After: `be1_adult_identities` 40, `parent.child_profiles` 40, `parent.profile_revisions` 40, `story.runs` 41, `story.run_inputs` 32, `story.command_receipts` 42, plus the four tables above. `ai_jobs.job`, `ai_jobs.outbox` and `core_outbox_events` stayed at 0. No other table changed.
- **Other server-log errors:** the four expected check violations of the out-of-range age cases, and one `FATAL: role "root" does not exist` from the readiness check inside the container. Nothing else.
- Both launcher logs are empty (warning level; no error was logged).

## Standing

This is the first full pass. The exit rule asks for at least three consecutive full passes on unchanged pins, so two more rehearsals (indexes 3 and 4) are needed before the gate run can be requested. The gate run itself is not approved.

Deviations DV-1 to DV-18 apply to what a pass shows. This record claims nothing about M2-AT-08 or M2-AT-10.
