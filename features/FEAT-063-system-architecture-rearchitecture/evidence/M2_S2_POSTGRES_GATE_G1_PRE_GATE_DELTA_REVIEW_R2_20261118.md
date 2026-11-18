# FEAT-063 M2 PostgreSQL gate G1 — pre-gate delta review R2 — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort high, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2) at the owner's instruction ("Review Sonnet").
- **Pins reviewed, at HEAD `b430b67a68e7934721f7ec9b44b96e9071cb989e`:** test file `BC3FBE628CEEA8E79CF6EDD96963F3EE45D6565FDDB65FD8C6888781476AF4A2`; launcher `00FED31506F1510192471A81DA321CC5EBFD68140E0A089125FF3D4B14959749`; scratch driver `E963B585BFB59FEF3F5ACA70C7D18FCF4E8D9E4FFB0FEAD3AF2062EB70A97CD6`; `parent_story_repository.py` `5E33C076A4A13439AB0D02A8D8088D543D277758E78076D709E23CB386CFBDA8`; `tests/unit/test_parent_story_repository_postgres_nulls.py` `63C58CF2201966E4C912B6FF924DFD3BD712A5F84590FFBFDCC1DD9C7756A076`; `plan/M2_S2_POSTGRES_GATE_G1_STAGE_B_TASK_APPROVAL_DRAFT2_20261117.md` `07F93EC6B4D33C8928D7D4674E46EAAB19C0279B2A74DE6D20EE78EAF06AB192`. The reviewer states all pins, HEAD and the migration manifest matched, the tracked tree was clean, and that it made no writes, ran nothing, used no Docker command and did not open the secret directory.
- **Question put to the reviewer:** is a one-shot gate run safe and meaningful — does the suite test the right things, is the product fix correct, do the rehearsal records match the raw outputs, is the driver ready in gate mode.
- **Verdicts:** test and launcher READY WITH NOTES; driver in gate mode READY WITH NOTES; product fix (commit `b430b67a`) READY. **P1=0, P2=2, P3=12.** No code change is required by either P2; both are decisions for the gate approval text.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Finding | Reviewer's smallest fix |
|---|---|---|
| J1 | The gate has exactly one run label (`gate-1`). Any failure after card C1 has created its folders consumes it, including infrastructure failures unrelated to the product (a Docker error after `docker run`, an Alembic timeout after the migration flag, a probe failure). The driver's message "choose a new --index" is impossible in gate mode, and the driver refuses to remove a gate container. Stage B Draft 2's "next attempt takes the next index" does not apply to the gate. | State in the gate approval what counts as consumption. Suggested: a failure before the test card starts is an infrastructure failure, after which the owner may clear the gate container, volume, secret folder and output folder under that approval; a failure at or after the test card consumes the one-shot. |
| J2 | The egress-block flag was never exercised: all four rehearsals ran without it, and the planned loopback probe under the block was not done. Requiring it for the gate could fail the run after its flag file is written. | Either do not require the block for the gate and state the lower containment, or run one more rehearsal with the flag first. |

## P3 findings (summary)

J3 case 08-01b cannot itself show that executions overlapped; the "9 of 10 overlapped" statement comes from the container log, which is in no retained output folder and could not be verified by the reviewer — save the log into the gate evidence if overlap is to be cited. J4 case 08-07 asserts `current_version`, which S2 Draft 18 does not ask for and no DV row covers. J5 the liveness helper returns "not alive" if the task list prints nothing; mitigated by the port checks. J6 the side-effect check is called in seven tests, not all; a side effect from another test would be attributed to a later one; the after-run table counts show the three tables at zero. J7 the test's forbidden-variable list is narrower than the driver's clearing; only matters outside the driver, where the file skips. J8 the source check ignores untracked files; the driver's own hash is not written to `result.json` — record it and keep a copy with the gate evidence. J9 on timeout only the direct child is killed. J10 the claim must not imply more than is shown: not covered on PostgreSQL are W3 (pending receipt), create **with** a lesson version, and grants of a separate runtime role (the API runs as the role that owns the schema); the fix-task approval entry still says W2 and W4 are by reading only, which rehearsal 2 has since verified. J11 the rehearsal records mix driver and pytest timings. J12 cases 10-01/02 compare the age in the stored context snapshot, not the run row's age column (as DV-17 allows).

## Assertion strength (reviewer's per-test reading)

No vacuous test found. Strongest: 08-01a (cannot pass without the unique index and the constraint-name mapping; the lock wait is observed). 08-01b proves at most one run, input and receipt per account but not overlap (DV-14). 08-02, 08-03, 08-04, 08-05, 08-08, 08-09, 08-15, 08-16 have no weak spot noted beyond J6. 08-14 reaches the state check in all three states (the correct revision is sent). 08-03p proves `PREPARATION_REVIEW` by a route read immediately before the cancel and compares the contents of all six retention row sets. Level R: codes match D-201 and D-202; compares the account's runs, inputs and receipts by content and the story-revision count. The restart test cannot pass with an in-process restart.

Coverage: every case of Draft 4 section 6 as amended is implemented; the test follows every DV row; no gap against the approved text.

## Product fix

Exactly four changes plus the import, correct and minimal; the flush is inside the existing `try`, so error mapping and transaction scope are unchanged. Four of the six unit tests fail against the pre-fix code by the reviewer's reading; two are positive controls. The W3 limit is stated accurately in the fix evidence, the fix task, the commit message and the rehearsal records.

## Rehearsal records against raw outputs

The records match `result.json`, `pytest-output.txt`, `table-counts.json`, `restart-process-ids.json`, the probe file and the Alembic output for rehearsals 2 to 4 (31 upgrade lines; role not superuser; server version number 170011; matching marker). The claim that W1, W2 and W4 are verified on PostgreSQL is supported by the row counts. Not verifiable by the reviewer: anything taken from container logs.

## Driver in gate mode

Read branch by branch: identical to rehearsal mode apart from names and ports; database, ports and API ports are inside the test fixture's allow-lists; index must be 1; container removal is refused for the gate. Untested by rehearsals: J1 and J2. The owner should run the read-only preflight card first; it may be repeated.

## Earlier findings H1 to H19

All confirmed fixed or handled as Stage B Draft 2 states, with these remarks: H5 and H6 fixes exist but their paths have never run; H7 lacks the driver hash (J8); H16 partial (J1, J9); H17 documentation only.

## Not read or not verified (reviewer)

Container logs; the Stage A report; the baseline lines directly (relied on Draft 4's quotation); parts of `app.py`; the StoryRun-lite repository; library source; whether the gate ports are free or a gate container exists.

## Notes by the coordinating session

- J3: the count of 19 unique violations was read by the coordinating session from `docker logs` of the rehearsal-2 and rehearsal-4 containers (read-only) and not saved. For the gate run the filtered log lines will be saved to the output folder before the container is touched again.
- The older fix-task approval entry is left as written (true when written); the later records supersede it on W2 and W4.

## Disposition

J1, J2, J3, J4, J8 and J10 are carried into the gate-run approval draft. No file was changed after the review.
