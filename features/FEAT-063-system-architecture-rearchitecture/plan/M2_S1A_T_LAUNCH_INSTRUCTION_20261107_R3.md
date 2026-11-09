# M2 S1a-T owner launch instruction R3

**Status: NOT LAUNCHED — DO NOT LAUNCH.** This file does not authorize or start the run. Do not launch S1a-T until the owner has reviewed and accepted a Baseline Run Closure Record for the pinned baseline specification, and the separate Baseline Run and S1a-T approval entries are present in `approvals/TASK_APPROVAL.md` as `APPROVED / NOT LAUNCHED`.

## Pinned artifacts

| Artifact | Repository path | SHA-256 |
|---|---|---|
| S1a-T approval specification R3 | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107_R3.md` | `AE81C23DAB0894DE82688D7092EE8A19BD4EAF80FEA706808275FD5A14BB53FA` |
| Guarded owner launcher R3 | `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_t_owner_run_20261107_r3.py` | `A37A8CA798DC24BAE5913071BE5EBCBB7CB732444977C33F8894166EE90A7918` |
| Baseline specification | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_BASELINE_RUN_APPROVAL_FINAL_20261107.md` | `A671DBD85B9622CB754C5CECB807BBBBA2C920CD76F0A22ABBA44F4A12DC1A18` |
| Baseline owner launch instruction R2 | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_BASELINE_LAUNCH_INSTRUCTION_20261107_R2.md` | `C132EF91AD7C06A82EB27D09D82B0662E77CDD795B9BC2F935B281822EAA9178` |

Before running anything, recompute these SHA-256 values and every source pin in the S1a-T specification. Verify the branch and HEAD match that specification, the index is empty, the approval entries pin these exact artifacts, and an accepted Baseline Run Closure Record pins the baseline specification. If any check differs, stop. Do not read `.env` or print environment values.

## Owner-only launch

First complete the separately approved baseline using its launch instruction. Review its complete logs and record an accepted closure before considering S1a-T. The two phases are sequential; they must not run in parallel. S1a-T uses only `sketch2life_m2_s1a` on PostgreSQL 17 at loopback port 5433 as `postgres`. It never writes to or migrates `sketch2life`.

In a new PowerShell console at the repository root, run only after all approval and closure gates above pass. Do not set or clear database variables to get past the launcher. It checks the parent process environment without printing values and prompts for the database password using hidden terminal input. Before pytest, it records a read-only count for every non-system table. If any table has rows, it stops before pytest. Do not infer that the owner-reported empty database is verified until this pre-inventory completes.

```powershell
& '.\backend\.venv\Scripts\python.exe' '.\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s1a_t_owner_run_20261107_r3.py' --run-postgres-test
```


The launcher requires Python 3.12 from the backend virtual environment, the pinned branch and HEAD, an empty Git index, the approved records and hashes, absent ignored output directories, and a clean inherited database environment. It verifies target identity/schema and records per-table counts in `BEGIN READ ONLY`, then stops before pytest if any table is non-empty. Otherwise it invokes exactly one PostgreSQL integration test module through `cmd.exe /d /c`, with a 1,800-second ceiling and no retry. The test working directory, command, run ID, exit status, and separate stdout/stderr logs are recorded under the ignored run-specific folder `.claude/handoff/logs/M2_S1A_T_20261107/`. Temporary test artifacts and `basetemp` are under the ignored `tmp/M2_S1A_T_20261107/` folder.

Each test run uses the same UUID-hex run ID in these markers: organization IDs `synthetic-s1at-{run_id}-org...`, class IDs `synthetic-s1at-{run_id}-class...`, adult subject IDs `synthetic-s1at-{run_id}-teacher...`, profile display name prefix `Synthetic S1AT {run_id} `, and proof reference `s1at-run-{run_id}`. Child IDs keep the required `synthetic-` plus 24-hex format and are associated through the marked display name. If pytest has no official summary, the launcher writes exactly `NOT RUN: no official pytest summary`, does not open a post-run database connection, and exits 2. When a summary exists, it records per-table total counts and matching marker counts in a read-only transaction. Any non-marker table with rows, per-table total that differs from its marker count, or mismatch between total and marker rows is `UNKNOWN_ROWS_FOUND`, not PASS. It does not select row values, clean up, or delete test rows. The launcher is single-use until the owner separately decides how created rows may be handled.

## Stop and report

Stop immediately on any safe-stop code, pin or identity mismatch, output path collision, non-ignored output directory, secret/URI detected in pytest output, timeout, missing official pytest summary, interrupted process, or inventory failure. On timeout, process termination is considered confirmed only when `taskkill.exe /PID <pid> /T /F` exits 0, or exits 128 and the root process has exited. Otherwise the launcher reports `PROCESS_TERMINATION_UNCONFIRMED` and does not run post-inventory. If Ctrl+C interrupts `process.wait()`, the launcher attempts to terminate the process tree. Only confirmed termination writes `pytest.exit.txt=INTERRUPTED` and a runner status, skips post-inventory, and exits 2. Unconfirmed termination reports `PROCESS_TERMINATION_UNCONFIRMED`, does not write `pytest.exit.txt`, does not run post-inventory, and does not print `STOPPED_SAFELY`. It does not enumerate orphan child processes; that remains unverified. If the test output has no official summary, it writes exactly `NOT RUN: no official pytest summary` and makes no post-run DB connection. Do not retry, change the shell, alter flags, run Alembic, migrate, clean up, or switch databases. Keep raw logs local; do not paste secrets or database URLs into chat.

Return the run ID, exact log directory, launcher and Python version, command and working directory, pytest exit status, complete official pytest summary and failed/error node IDs, count-only inventory output, plus SHA-256 for each output file. Distinguish PASS, FAIL, SKIP, timeout, and NOT RUN; SKIP or NOT RUN is not PASS. An S1a-T result does not approve S1a-P or any later phase.

`OWNER_MODAL_CALL_APPROVED=NO`. No S1a-P, S1b, S2, S3, or M3–M6 phase is opened by this instruction.

## Revision 3 change record

Compared with R1 using `git diff --no-index`.

| Order | Location | Change |
|---:|---|---|
| 1 | Title/status and pins | Identify this as R3, retain the exact `DO NOT LAUNCH` gate, pin the R3 specification and launcher, and use Baseline Launch Instruction R2. |
| 2 | Owner-only launch | Point to the R3 launcher and add its all-table read-only pre-inventory; the invocation keeps `--run-postgres-test` (same flag as R1; this corrects the R2 truncation). |
| 3 | Post-run handling | Add per-table total/marker comparisons, the no-summary no-connection rule, preservation/no-cleanup behavior and single-use boundary. |
| 4 | Stop/report section | Add timeout termination confirmation and the confirmed/unconfirmed Ctrl+C paths. R1 already used “Stop and report”; this R3 wording also corrects the typo in R2. |
| 5 | Revision record | Add this R3 table after comparing R1 and R3 with `git diff --no-index`. |
