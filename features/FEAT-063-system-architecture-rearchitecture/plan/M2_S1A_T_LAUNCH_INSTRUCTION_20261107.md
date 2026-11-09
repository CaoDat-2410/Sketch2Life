# M2 S1a-T owner launch instruction

**Status: NOT LAUNCHED.** This file does not authorize or start the run. Do not launch S1a-T until the owner has reviewed and accepted a Baseline Run Closure Record for the pinned baseline specification, and the separate Baseline Run and S1a-T approval entries are present in `approvals/TASK_APPROVAL.md` as `APPROVED / NOT LAUNCHED`.

## Pinned artifacts

| Artifact | Repository path | SHA-256 |
|---|---|---|
| S1a-T approval specification | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_S1A_T_APPROVAL_SPEC_FINAL_20261107.md` | `9E739F6F47D6EF11D070C0D49950B098295E55CB210BA79B84B6101CA968B776` |
| Guarded owner launcher | `features/FEAT-063-system-architecture-rearchitecture/evidence/scripts/m2_s1a_t_owner_run_20261107.py` | `EE9F9CA13F872C4D9121BD0139AA6AEC644A35646FFB94A5EAD87F9A8A93F005` |
| Baseline specification | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_BASELINE_RUN_APPROVAL_FINAL_20261107.md` | `A671DBD85B9622CB754C5CECB807BBBBA2C920CD76F0A22ABBA44F4A12DC1A18` |
| Baseline owner launch instruction | `features/FEAT-063-system-architecture-rearchitecture/plan/M2_BASELINE_LAUNCH_INSTRUCTION_20261107.md` | `2E724D5BD238EE4EA87231D218680910053B35F72C570092C1B6739AF7D0D19F` |

Before running anything, recompute these SHA-256 values and every source pin in the S1a-T specification. Verify the branch and HEAD match that specification, the index is empty, the approval entries pin these exact artifacts, and an accepted Baseline Run Closure Record pins the baseline specification. If any check differs, stop. Do not read `.env` or print environment values.

## Owner-only launch

First complete the separately approved baseline using its launch instruction. Review its complete logs and record an accepted closure before considering S1a-T. The two phases are sequential; they must not run in parallel. S1a-T uses only `sketch2life_m2_s1a` on PostgreSQL 17 at loopback port 5433 as `postgres`. It never writes to or migrates `sketch2life`.

In a new PowerShell console at the repository root, run only after all approval and closure gates above pass. Do not set or clear database variables to get past the launcher. It checks the parent process environment without printing values and prompts for the database password using hidden terminal input.

```powershell
& '.\backend\.venv\Scripts\python.exe' '.\features\FEAT-063-system-architecture-rearchitecture\evidence\scripts\m2_s1a_t_owner_run_20261107.py' --run-postgres-test
```

The launcher requires Python 3.12 from the backend virtual environment, the pinned branch and HEAD, an empty Git index, the approved records and hashes, absent ignored output directories, and a clean inherited database environment. It performs a read-only identity/schema preflight, then invokes exactly one PostgreSQL integration test module through `cmd.exe /d /c`, with a 1,800-second ceiling and no retry. The test working directory, command, run ID, exit status, and separate stdout/stderr logs are recorded under the ignored run-specific folder `.claude/handoff/logs/M2_S1A_T_20261107/`. Temporary test artifacts and `basetemp` are under the ignored `tmp/M2_S1A_T_20261107/` folder.

Each test run uses the same UUID-hex run ID in these markers: organization IDs `synthetic-s1at-{run_id}-org...`, class IDs `synthetic-s1at-{run_id}-class...`, adult subject IDs `synthetic-s1at-{run_id}-teacher...`, profile display name prefix `Synthetic S1AT {run_id} `, and proof reference `s1at-run-{run_id}`. Child IDs keep the required `synthetic-` plus 24-hex format and are associated through the marked display name. After a complete run without sensitive output, the launcher performs only a read-only aggregate count of rows matching these markers. It does not select row values, clean up, or delete test rows.

## Stop and report

Stop immediately on any safe-stop code, pin or identity mismatch, output path collision, non-ignored output directory, secret/URI detected in pytest output, timeout, missing official pytest summary, interrupted process, or inventory failure. Do not retry, change the shell, alter flags, run Alembic, migrate, clean up, or switch databases. Keep raw logs local; do not paste secrets or database URLs into chat.

Return the run ID, exact log directory, launcher and Python version, command and working directory, pytest exit status, complete official pytest summary and failed/error node IDs, count-only inventory output, plus SHA-256 for each output file. Distinguish PASS, FAIL, SKIP, timeout, and NOT RUN; SKIP or NOT RUN is not PASS. An S1a-T result does not approve S1a-P or any later phase.

`OWNER_MODAL_CALL_APPROVED=NO`. No S1a-P, S1b, S2, S3, or M3–M6 phase is opened by this instruction.
