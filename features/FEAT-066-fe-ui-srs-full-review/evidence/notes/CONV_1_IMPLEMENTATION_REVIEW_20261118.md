# CONV-1 implementation — independent review record (2026-11-18)

- **Reviewed:**
  - the evidence note `CONV_1_IMPLEMENTATION_EVIDENCE_20261118.md` at 14,478 B, `6E1DD47204424F45A11754D5AA20467194BEBB14329798ECEA18713945A39555`;
  - the uncommitted diff in `.worktrees/conv1` (branch `feature/feat066-conv1`, base `08439b22`);
  - the owner-run logs.
- **Checked against:** package Draft 5 (`3FCF4741…`), D-066-71 and the CONV-1 Task Approval entry.
- **Reviewer:** a separate subagent. Model Sonnet 5.5, reasoning effort high, both set explicitly; the reviewer reports that it cannot verify the effort from inside. It worked read-only and wrote no scratch files.
- **Pin checks:** all match:
  - the note;
  - all 21 changed files;
  - all 8 logs and the audit output;
  - `TASK_APPROVAL.md` unchanged at 43,578 B.

  `git status` shows exactly the 21 files, and `git diff --check` is clean. The timeline confirms that run 2 tested the final source; only the test 24 edit came later, and run 3 covered it.
- **Verdict:** **CHANGES REQUIRED (small)**. P1 = 0, P2 = 1, P3 = 5.

## Findings

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| CI-01 | P2 | `test_m2_s1a_teacher_postgres.py:269–272` still expected the route message "Class already has an active Teacher". Under CV-3 the body carries the 409 status message, so the test would fail; it never ran because it needs the forbidden database | **Fixed:** it now expects `STATUS_MESSAGES[409]`. The file is now `F7731114…`. Lint is clean and `diff --check` is clean |
| CI-02 | P3 | Some CONV-1-edited assertions never ran, because a pre-existing failure stops the test earlier: the `Be1Error` property set, `missing_reason == 400`, the PDF test's later assertions, and `be1_api_smoke.py` | **Fixed:** listed in evidence §7 |
| CI-03 | P3 | The fixture scope amendment appears only in the evidence note. The two auth-test edits were not disclosed | **Partly fixed:** the auth edits are now disclosed in evidence §3 item 6. Recording the amendment in `TASK_APPROVAL.md` waits for an explicit owner instruction (the coordinator's earlier attempt was blocked by the safety check) |
| CI-04 | P3 | BE1 kept 422s appear only in the grouped `default` description, while Lesson Library shows an explicit 422 row. This matches the package; test 14 does not assert presence | No change |
| CI-05 | P3 | Test 14 does not cover the legacy plain-text 500 header. The frozen-family check uses an unmatched route | No change (optional hardening) |
| CI-06 | P3 | The `/tmp` temp-file breach (disclosed), plus style nits | Acknowledged |

## Checks the reviewer passed

- The envelope never echoes input, route text or paths. The 422→400 remap is limited to the stated codes.
- The code mapping matches §3.2 item 2b.
- The 404/403 guard logic is correct, and test 15 asserts the uniform 404 body.
- The Lesson Library self-revoke widening is safe.
- No new existence oracle was found.
- The `X-Request-ID` rules hold. The 413 change is limited to the Lesson Library branch.
- The OpenAPI kept-422 lists were cross-checked against every 422 raise site, and existing 400 rows are merged.
- The frozen families are untouched, and no route, migration or dependency changed.
- Test edits stay within the approved limits, apart from the disclosed amendment.
- The log counts and the failure classification match. None of the remaining failures is plausibly caused by CONV-1.
- mypy error counts for the changed files equal the base.

## Not verified by the reviewer

- Tests that need the forbidden `m2_s1a` database.
- Behaviour on the lock-exact FastAPI.
- `be1_api_smoke.py`, which needs a live server.
- That the late test 24 edit touched only the t3 hunk; this is very likely, since run 2 passed the other edits.
