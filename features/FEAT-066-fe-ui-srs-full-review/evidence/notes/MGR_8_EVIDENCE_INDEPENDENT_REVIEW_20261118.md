# MGR-8 evidence — independent review record (2026-11-18)

- **Artifact under review:** `evidence/notes/MGR_8_ROOT_RUN_RESULTS_20261118.md` (6,785 B, SHA-256 `19A6E63C106EFF951A162CF4B48475FBF442EF3656A30D29F910FFC2CECE1601`), together with:
  - the MGR-8 entries appended to `CONTEXT.md`, `status/STATUS.md` and `approvals/TASK_APPROVAL.md`;
  - the three earlier `MGR_8_*` notes;
  - the uncommitted S-LL working-tree changes on the root M2 branch after merge `b93d7334`;
  - the owner-run logs under the git-ignored `tmp/feat066-phase-a/root-run/`.
- **Reviewer:** a separate subagent started by the coordinator session, on model Sonnet 5.5 (`claude-sonnet-5-5`) at high reasoning effort. Both were set explicitly, as the harness reviewer rule requires.
- **Reviewer's permissions:** read only. It ran no tests, validators, builds, database, Docker, network or state-changing git commands. It did not open secrets, `.env` files, Bruno environments or the firebase-auth helper. Its only writes were scratch files under the git-ignored `tmp/feat066-mgr8-evidence-review/`.
- **Verdict:** **PASS WITH NOTES**. P1 = 0, P2 = 0, P3 = 4.

## What the reviewer verified

1. **Pins.** Every size and SHA-256 in the note matches the working tree:
   - the six MGR-7 files, plus `app.py` and `test_app_composition.py`;
   - the note itself;
   - the three record files: `CONTEXT.md` 60,426 B / `5259348A…`, `STATUS.md` 52,714 B / `0FAB6F68…`, `TASK_APPROVAL.md` 41,171 B / `E202446E…`;
   - the three earlier notes: `15A091F3…`, `BCDACA87…`, `F20D31F4…`;
   - the five logs.

   The pinned files were last modified before the run.
2. **Logs agree with the note:**
   - d1: 8 passed in 0.74 s;
   - d2: 5 passed in 7.47 s;
   - d3: 6 passed and 1 failed in 22.58 s (the PDF upload test, 503 `DEPENDENCY_UNAVAILABLE`), and both MGR-7 integration tests passed;
   - comp: 7 passed in 5.14 s;
   - exit codes: 0, 0, 1, 0.

   The logs contain no database URL or secret.
3. **The root and manager-api working trees agree:**
   - The five non-catalog MGR-7 files are byte-identical.
   - In the catalog test, the MGR-7 lines are identical in both checkouts. The only other difference is the M2 base from `be5af631`.
4. **Scope:**
   - Only the six allowlisted source and test files and the three FEAT-066 record files are modified.
   - `service.py` maps the shared replay conflict to 400 `INVALID_IDEMPOTENCY_KEY`.
   - The router changes two `limit` defaults from 50 to 25.
   - The contract changes two `limit` descriptions and adds a 400 response to 11 operations.
   - The integration test adds the list-default test, the 400 assertion and the approved `account_role` fixture amendment.
5. **Merge claims:**
   - `backend/alembic`, `pyproject.toml` and `uv.lock` are unchanged against `dev` `1c9148e8`.
   - The parents of `b93d7334` are as described, and both `.gitattributes` blocks are present.
   - The claim that `.gitattributes` was the only conflict rests on the merge commit message; the reviewer did not re-run the merge.
6. **Paths and secrets:** there are no absolute paths, URLs, passwords or `.env` references in the note or the appended entries.
7. **Append-only:**
   - Each record file begins with its earlier bytes, both the HEAD version and the manager-api version.
   - The files are LF only.
   - The appended MGR-8 entries are 1,170 B, 818 B and 934 B.
8. **Conclusion:** VERIFIED is a fair reading.
   - Both MGR-7 behaviours are covered at runtime.
   - The catalog assertions pass.
   - The ClamAV limit, the single run and the absence of validators and lint are disclosed.
   - The 400 response is runtime-tested through the unit-level replay and one integration path. The catalog covers the other operations statically.

## Findings

| ID | Sev | Finding | Disposition |
|---|---|---|---|
| E-01 | P3 | The note says the PDF test failed "because ClamAV is not running at 127.0.0.1:3310". The appended `TASK_APPROVAL.md` and `CONTEXT.md` entries say the same in short form. The log shows only the 503 `DEPENDENCY_UNAVAILABLE`. The scanner raises that 503 for any `MalwareScannerUnavailable` error: a connection error, a timeout or a non-clean verdict. The earlier owner-run note records that ClamAV status "was not checked". | Corrected below. |
| E-02 | P3 | The note's Limits section leaves out a limit recorded in the earlier owner-run note: the root `backend/.venv` is not lock-exact (FastAPI 0.141.1 against 0.162.0 in `uv.lock`). | Corrected below. |
| E-03 | P3 | The note names the database `be1_acceptance`. The earlier owner-run note names it `s2l_be1_acceptance` (container `s2l-be1-acceptance`, port 5434). The test needs only the substring `be1_acceptance`. | Corrected below. |
| E-04 | P3 | The untracked `features/FEAT-066-brand-logo/` folder is unrelated to S-LL. | Handled at commit time: the S-LL commit stages explicit paths only and leaves that folder out. |

## Corrections

These corrections are recorded here. The root-run note and the appended record entries are not edited, because the `TASK_APPROVAL.md` entry pins the note's SHA-256. Read the note and the entries with these corrections:

- **E-01:** Read "because ClamAV is not running" (in the note, `TASK_APPROVAL.md` and `CONTEXT.md`) as "consistent with ClamAV not being reachable at 127.0.0.1:3310; ClamAV status was not checked". The disposition does not change: the failure is an environment limit outside the MGR-7 change.
- **E-02:** Add to the note's Limits section: "The interpreter is the root `backend/.venv`, which is not lock-exact (FastAPI 0.141.1 against 0.162.0 in `uv.lock`). d1, d2, d3 and comp ran on it."
- **E-03:** Read the database name `be1_acceptance` as the name substring that the test requires. The earlier owner-run note gives the full name: `s2l_be1_acceptance`, in container `s2l-be1-acceptance` on loopback port 5434. The root-run logs do not show the database name, so it is not verified from the logs that the root run used that same database. That rests on the owner's setup.

## Not verified by the reviewer

- No test was re-run.
- The owner's chat wording.
- Database state and container identity.
- ClamAV status.
- `PYTHONPATH=src` (the log is consistent with it, but the setting itself was not seen).
- The repository validators and `git diff --check`. The coordinator runs these before the commit.
- Whether the merge had any conflict other than `.gitattributes`.

## Outcome

G0 can close. The S-LL change (MGR-7 plus the MGR-8 records) can be committed as one task commit, on the owner's word. The owner gave that word in chat on 2026-11-18: "Làm G0 luôn", in answer to the question whether to write this record, commit S-LL and push it to PR #30.
