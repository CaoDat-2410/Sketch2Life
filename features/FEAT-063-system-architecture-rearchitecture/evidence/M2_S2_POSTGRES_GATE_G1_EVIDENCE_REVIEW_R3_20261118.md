# FEAT-063 M2 PostgreSQL gate G1 — evidence report — independent review R3 — 2026-11-18

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort high, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2) at the owner's instruction ("Review Sonnet").
- **Pin reviewed:** `evidence/M2_S2_POSTGRES_GATE_G1_EVIDENCE_20261118.md`, 13,579 bytes, SHA-256 `0DA1DAAFDACD509D5798EBFB875A8D9581A9D4346FCD0006B1D5F1830CED3BC8`, at HEAD `67ef7d7c26f9e0a00872c23f2375900e538286fe`. The reviewer states the pin and HEAD matched; that it made no writes, changed no container, ran no test, connected to no database and never opened the secret directory; one attempted shell redirect into scratch was denied by the permission check and nothing was written. It used read-only Docker queries (`ps -a`, `inspect`, `logs`) and a JSON-parsing snippet.
- **Verdicts:** the report is **ACCURATE WITH NOTES**; the gate result (20 of 20 passed, second attempt) is **SUPPORTED WITH NOTES** by the raw evidence. **P1=0, P2=2, P3=9.**
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## P2 findings

| ID | Finding | Reviewer's smallest fix |
|---|---|---|
| K1 | The report does not say what the approved result-handling rule would have made of gate attempt 1. The gate-run draft's section 6 says anything other than a full pass from the test card is FAILED, with the ceiling consumed. Attempt 1 wrote its start flag and produced no result; it was recorded as interrupted, "neither a pass nor a product failure", and the report states that as fact. The owner did approve attempt 2 afterwards, so attempt 2 was permitted; but the owner should see that this is an owner-approved reclassification and retry, not a literal application of the rule. | One sentence in section 1 saying so. |
| K2 | The "not shown" list says "everything in DV-1 to DV-19" but glosses only some of them. Unmentioned: DV-6 (the `PREPARATION_REVIEW` state is built with repository methods from the test process, not through routes), DV-10 (SQL-seeded identities, profiles, the holder row, the COMPLETED run), DV-16 (no body equality in 08-02), DV-17 ("không clamp" only indirectly), DV-18 (retention shown indirectly), DV-13, DV-15, DV-19 (assertions stronger than the approved cases). Also unmentioned: S2 Draft 18 row 13 (artwork-route error envelope) is covered by no case. The owner is asked to accept the deviations on this report. | A one-line gloss per deviation, or an explicit pointer to the deviation table, plus one line on row 13. |

## P3 findings (summary)

K3 the "9 of 10 overlapped" statement is an inference from the log, stated as fact. K4 "nothing else" in the server-log paragraph covers only error-level and shutdown lines; the full log also has benign initialisation notices (a locale warning, the trust-authentication notice, a replication-launcher line at shutdown). K5 "tracked tree unmodified before and after": the driver checks before each step, not after the test; the "after" is the session's check. K6 the driver's credential scan ran before the two files the session added afterwards. K7 the run marker cannot be checked against any output file (it is only in the pasted line and the secret directory). K8 the 13 head names and the reason for 10 version rows are not given; the driver command line and exit code are not quoted. K9 in the attempt-1 record, the interrupt landed in the session fixture's teardown connect, not in the test body; conclusion unchanged. K10 "launcher logs empty (warning level)" is cryptic; the files are 0 bytes. K11 times are UTC in the report and local in the attempt-1 record. Not stated in the report: a single run on one PostgreSQL minor version (17.11); the socket guard cannot see the driver's native connections; the container's local socket uses trust authentication.

## What the reviewer re-verified independently

- All ten output-file hashes of the report's section 5; test, launcher, product, driver, manifest (all 31 migration hashes), `pyproject.toml`, `uv.lock`; the hashes of the governing drafts, the approval record (493,048 bytes) and the attempt-1 record.
- Result: exit 0, 20 PASSED lines, `20 passed in 20.69s`, no other outcome word; the 20 outcomes map to the cases as tabulated; the driver's `all_passed_no_skips` logic is trustworthy for this output.
- Migration: 31 upgrade lines; the 10 version rows by name; 123 tables; empty database before.
- Table counts before and after, identical to rehearsals 2 to 5 (compared by parsing every `table-counts.json`); the three job and outbox tables at 0.
- Process identifiers; the launcher's reported identifier equals the new reported one.
- Container: bound only to `127.0.0.1:55440`; image digest; started 18:03:30Z, finished 18:04:00Z, exit 0, restart count 0. **The container stopped after pytest finished**: output files were written at 01:03:57.97 to 01:03:58.79 local time and PostgreSQL logged the shutdown request at 01:03:58.93.
- **No overlap with any other container**: gate-1 ended 17:54:41Z, rehearsal-5 17:59:00Z, rehearsal-4 17:33:38Z; all exited. No second invocation (single-line flag files, one set of launcher logs).
- Between the attempts nothing under `backend/` changed (`git diff a83bf4f0 67ef7d7c` touches the approval record and the attempt-1 record only).
- Server log re-read from the container: 19 unique-index violations, two violations of each age check, one readiness `FATAL`, the shutdown lines; **no other ERROR, FATAL or PANIC, no deadlock, "could not" or timeout line**.

## The 08-01b overlap inference (reviewer's analysis)

Supported: the first ten unique violations are on one backend process at about 90 ms intervals (consistent with 08-01a, which runs first); the next nine come at about 50 ms intervals and alternate between two backend processes, the second of which appears only there. So in at least nine executions the losing request passed the existence read before the winner committed and was then refused by the unique index, under real two-connection concurrency. Not supported: the log has no per-case tag (the split rests on count, order and process pattern); "the winner was in flight" is stronger than the log proves; "the tenth was refused by the earlier read" is inferred from the absence of a violation.

## Gate attempt 1 (reviewer's analysis)

The account is accurate against the raw files and the container state, and it is recorded, not hidden. Attempt 1 gives no evidence of a defect in the twentieth item and no pass for it: the item had passed its stop, identifier and port checks and was waiting at its first database read when the container went away; the rest never ran. The same item passed in rehearsals 2 to 5 and in gate attempt 2 on identical hashes.

## Claims

No over-claim found. The header and section 6 use the approved claim wording; the report nowhere implies that M2-AT-08 or M2-AT-10 "ran and passed" without deviations. Section 7 on the S2 closure is accurate.

## Not read or not verifiable (reviewer)

The secret directory and the run marker's value; the owner's pasted output and chat words (the approval entries were relied on); the full test file (fixtures and key cases were read); parts of plan Draft 4 and of the pre-gate review.

## Disposition by the coordinating session

K1 to K8 and the three unstated limits are addressed in a revision of the evidence report (new hash recorded in the acceptance entry). K9 to K11 need no change. The reviewed pin above is the version before that revision; the revision changes wording and adds limits, and changes no result value.
