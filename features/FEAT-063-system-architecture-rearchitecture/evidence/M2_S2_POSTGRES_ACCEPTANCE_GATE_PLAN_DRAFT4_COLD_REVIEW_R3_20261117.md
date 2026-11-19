# FEAT-063 M2 PostgreSQL acceptance gate plan Draft 4 — cold review R3 — 2026-11-17

- **Reviewer:** Claude subagent, fresh context, model Sonnet 5.5, effort high, read-only by instruction (no sandbox enforcement; network not sandbox-disabled). Started by the coordinating session (Fable 5.2) at the owner's instruction ("Review Draft 4").
- **Interruption:** the review stopped once on an API usage limit and was resumed in the same reviewer context at the owner's instruction ("Hãy thử lại"). The reviewer re-verified the pin after resuming and states that its findings come from the first pass and that nothing was lost. It lists what it did not re-read after resuming.
- **Pin reviewed:** `plan/M2_S2_POSTGRES_ACCEPTANCE_GATE_PLAN_DRAFT4_20261117.md`, 26,537 bytes, SHA-256 `EBA29DEA0E30370916DEF964E227484F1E2820FA3F9E5ED47F15D21E3B1C880B`, at HEAD `7cc5cf74d03c249d17b6c98c877ed3fb1a36b09a`. The reviewer states the pin matched at the start and after resuming, that it made no writes and connected to nothing.
- **Verdict:** READY WITH NOTES — P1=0, P2=5, P3=11. This is a verdict on the plan as a basis for an approval text. It is not an approval, and the five P2 items must be fixed before the owner approves.
- **This file** is the coordinator's condensed transcription of the reviewer's report, not the verbatim report.

## Status of the 16 findings of review R2 (on Draft 3)

Resolved: N1, N2 (by removal), N3, N5, N6 (one caveat, F10), N8, N9, N10, N12, N13, N16. Partly: N4 (F5), N7 (F4, F8), N11 (F2), N14 (F6), N15 (F5).

## Deviation table

The reviewer found every baseline clause in DV-1 to DV-12 quoted or paraphrased faithfully and every "why" true in the code, with two reservations: DV-6 is under-specified (F4) and DV-8 over-claims (F3). Missing or implicit deviations it lists:

- "không áp đặt loser status/error nếu contract chưa định nghĩa": the gate asserts exactly 409 `ACTIVE_RUN_EXISTS`; acceptable because D-199 defines it, but the plan should say so.
- "serialize/persist/read profile revision": the product's own persist and serialize are not exercised, because profiles are seeded.
- "không clamp": covered only implicitly.
- Case 08-01a is one request against a SQL holder, not two concurrent requests; 08-01b is the real race but an overlap is not guaranteed.
- Case 08-14 asserts an error code that S2 Draft 18 and D-199 leave unassumed: stronger than the approved case.
- "Replay không tạo side effect trùng": 08-02 lists no row-count assertion; create replay rebuilds its response from the current run, not from a stored body.
- "không coi là đã xóa": covered only indirectly.

The condition that no "ran and passed" statement is made without the owner's acceptance of the deviations is stated in section 1 only; the reviewer asks for it in section 9 and in the approval text.

## P2 findings

| ID | Finding | Reviewer's smallest fix |
|---|---|---|
| F1 | Application start-up in the combined profile always constructs the S3-compatible storage client; the client library's credential lookup can probe the cloud metadata address (reviewer's knowledge, not a run). That would trip the socket guard and the "non-loopback connection" stop condition at every launcher start. | Disable the metadata lookup and point the shared credential and configuration files at non-existent paths in the launcher environment; the guard raises an operating-system error subclass. |
| F2 | A Python-level socket guard cannot see connections the database driver makes in native code. PostgreSQL traffic is protected only by the literal-address URL, the probe, the cleared variables and the egress block. | Say so; clear further libpq variables (host address, password, service file, system configuration directory, TLS mode and the like). |
| F3 | Cases 10-01 and 10-02 and DV-8: reading a SQL-seeded profile revision back by SQL proves nothing about product code. | Compare the create response's profile-revision reference and context snapshot with the seeded row (a product read through the profile lookup); declare that product persist and serialize of profile revisions are not covered. |
| F4 | Case 08-03p, DV-6 and section 7: "understanding and asset rows seeded by SQL" does not match the schema. Assets are column groups on the run-input table, two references on the run row, and two linked metadata tables guarded by a trigger; an understanding row needs a specific snapshot shape, and a malformed seed turns the cancel response into a 500 on the one-shot run. | Build the state from the test process with the repository's own methods, declare it as repository-level seeding, and pin the retention row sets with a before and after comparison. |
| F5 | The plan does not say how the password reaches the container's bootstrap and the login role without appearing in container inspection output or process arguments; the client password-file format differs from the container's password-file format. | Name the mechanism (file bind mount for the bootstrap password; a role-creation step reading a file); scan saved inspection output. |

## P3 findings (summary)

F6 give the exact lock-wait query for 08-01a, a timeout, a `finally` rollback of the holder and a longer HTTP timeout. F7 use the literal loopback address and guard name resolution too. F8 state whether seeded terminal runs have the active owner cleared; note that 08-14 asserts more than the approved case. F9 pin the import path in every card; "exactly one URL" means the core database URL variable. F10 the launcher writes its own process identifier, compared with the one the test recorded; compare row contents, not only counts. F11 restate the acceptance condition in section 9. F12 there are two rows numbered D-127 in the decision record; cite the cancel one. F13 add the missing deviations. F14 the run marker is a mistake check, not tamper-proof; the in-container socket is trust by default. F15 the identifiers PG-D10 and PG-D11 are not found in section 10. F16 case 08-16 is trivial on a fresh run; use a seeded run with an error code. F17 clear the StoryRun-lite database URL variable as well.

## Case table (reviewer's reading)

Every case in section 6 is implementable as written or with the notes above. The reviewer traced each to file and line: the unique-index mechanism of 08-01a (no deadlock; the wait is observable by a non-superuser for sessions of its own role); 08-01b under any interleaving; cancel ordering (receipt, then revision, then state); the four repository guards preceding every write; the restart steps; the profile lookup and both age checks by constraint name. A leftover run from 08-01a has no current input revision, so that account must not be read afterwards.

## Notes by the coordinating session

- F9's premise that the interpreter's path file points at the root checkout comes from a memory index line about a different environment. The task interpreter used so far was created without installing the project. The import-path pin is still worth carrying.
- No finding was re-verified in code by the coordinating session after this review, except those already confirmed in the R2 record.

## Disposition

Not yet addressed. Draft 4 is not revised. The proposed next step is to carry F1 to F17 and the missing deviations into the gate's approval text rather than a fifth plan draft, after the read-only preparation of phase P0 (pinned migration list, exact seeding tables, image digest, loopback probe).
