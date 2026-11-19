# FEAT-063 M2 PostgreSQL gate G1 — gate attempt 1: INTERRUPTED BY AN OPERATOR ACTION, no result — 2026-11-18

- **Status:** record of an invalid gate attempt. **It is neither a pass nor a product failure.** Written by the coordinating Claude session (Fable 5.2) from the output folder and read-only Docker queries, after the owner reported the mistake ("chạy nhầm"). Not independently reviewed.
- **Authority of the attempt:** gate-run approval entry of 2026-11-18 in `approvals/TASK_APPROVAL.md` (owner: "Duyệt chạy gate"), one run.
- **Commit:** `a83bf4f026d2d5a7590587a10fa69109df428080` on `feature/feat063-m2-s2`. Pins as approved: test file `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2`, launcher `00FED31506F1510192471A81DA321CC5EBFD68140E0A089125FF3D4B14959749`, `parent_story_repository.py` `5E33C076A4A13439AB0D02A8D8088D543D277758E78076D709E23CB386CFBDA8`, driver `E963B585BFB59FEF3F5ACA70C7D18FCF4E8D9E4FFB0FEAD3AF2062EB70A97CD6`. The tracked tree was clean before and after.
- **Resources:** container and volume `s2l-m2-s2-gate`, database `sketch2life_m2_s2_gate` on `127.0.0.1:55440`, API on `127.0.0.1:55450`. The container is stopped and **kept**, with its volume and the output folder `tmp/m2-s2-pg-gate/runs/gate-1/` (repository root, git-ignored).

## What happened (times are local, from file timestamps and the container state)

| Time | Event | Source |
|---|---|---|
| 00:54:05 | Container created and started (card C1) | container state; `container-inspect.json` |
| 00:54:08 | Empty database confirmed | `probe-before-migration.json` |
| 00:54:21 to 00:54:23 | One guarded upgrade; 13 heads, 10 version rows, role not superuser, marker matches (card C2) | `migration-started.flag`, `alembic-upgrade.txt`, `probe-after-migration.json` |
| 00:54:25 | Test card C3 started: **the one-shot was consumed here** | `test-started.flag` |
| 00:54:29 | API launcher started | `launcher-1.log` |
| 00:54:40 | Second launcher start: the run had reached the restart test, the last of 20 items | `launcher-2.log`, `launcher-process.json` |
| 00:54:41 | **The container was stopped while the test card was still running** | container finish time `2026-11-17T17:54:41Z`; server log: `received fast shutdown request`, `terminating connection due to administrator command` |
| 00:55:15 | The test process, waiting for a database connection, was interrupted from the keyboard | `pytest-output.txt` ends with `KeyboardInterrupt` in the driver's connect call |

The stop at 00:54:41 is the stop card (C4) taking effect before the test card (C3) had finished: the cards were issued as separate commands and overlapped. This was an operator sequencing error, made possible by a card design that let two cards run at once.

## State of the evidence

- `pytest-output.txt` (SHA-256 `28C861FD5719D41DEBC0374CBA79E63E7D1AFD91C414EC8FDD2CCA9DF42AB2B0`): 20 collected; the progress line shows **19 items completed without a failure mark**; the 20th (the restart test) was in progress when the database went away. There is no summary, no per-test outcome list, no `result.json`, no `table-counts.json`, no `restart-process-ids.json`.
- Filtered container-log lines saved after the event by the session (read-only `docker logs`): `container-log-filtered-lines.txt`, SHA-256 `1C488AE48C7A2F64B396437FFD816E1309224DD9B670D81FD5326E55393037AB`: 19 violations of `uq_story_run_active_parent`, the four expected age-check violations, the readiness-check line, and the shutdown lines.
- A copy of the driver as used is kept in the output folder.

## What may and may not be said

- **No gate result exists.** The attempt is INTERRUPTED. It must not be reported as "19 of 20 passed" in any acceptance sense, and it is not a failed gate: no assertion failed, and the interruption came from outside the system under test.
- Under the approved rule the one-shot is consumed, because the test card had started. A further attempt needs a new, explicit owner approval.
- Nothing in this attempt suggests a product or test defect.

## Corrective change to the cards (scratch driver, not yet used)

The driver gained one action, `run-all`, which performs container start, migration and test strictly in sequence inside one process and stops the container afterwards whatever the outcome, so cards can no longer overlap. Gate attempts after the first get a numbered container and run label (`s2l-m2-s2-gate-2`, `gate-2`), so attempt 1 stays in place untouched. New driver hash: `02E2A45D6F271690382066476DB0F49451A6B1445F72624269FD6F340B732737` (24,443 bytes); Ruff and Mypy clean; only `--help` executed. The new action has not been run; it should be rehearsed once in rehearsal mode before any second gate attempt.

## Rehearsal 5: the `run-all` action, owner-run, 2026-11-18

Run by the owner under the rehearsal approval, with the revised driver (`02E2A45D...`), at commit `a83bf4f026d2d5a7590587a10fa69109df428080`, container `s2l-m2-s2-rehearsal-5`, as one command. Pasted output: `PREFLIGHT OK rehearsal-5`, `CONTAINER UP ... empty database confirmed`, `MIGRATED 13 heads, 10 version rows, 123 tables`, `RESULT {... "exit_code": 0, "passed_count": 20, "not_passed": {}, "all_passed_no_skips": true ...}`, `STOP exit=0 container=s2l-m2-s2-rehearsal-5 (kept)`, `RUN-ALL complete`.

Checked in the output folder `tmp/m2-s2-pg-gate/runs/rehearsal-5/`: 20 passed, none skipped (`20 passed in 19.34s`); no credential in outputs; every table empty before the test except `alembic_version` (10); table counts after the test identical to rehearsals 2 to 4; restart identifiers 11176 / 50664 → 13000 / 33564. `result.json` SHA-256 `9D2054EC33F7B529D81F6C68C074328F6F9D24BEC67D98EC74C3CD0F2E6FDE79`; `pytest-output.txt` SHA-256 `2D3C917E6069CE8E876997B8A8E6DC55DE14A024A88437EB7FE7EB9912908CA2`. The container stopped only after the test had finished, as designed.

This is the fourth full pass of the unchanged test file, launcher and product code (rehearsals 2, 3, 4, 5), and the first use of `run-all`. The numbered gate container name (`--index 2` in gate mode) has not been exercised; the read-only preflight shows it before anything is created.
