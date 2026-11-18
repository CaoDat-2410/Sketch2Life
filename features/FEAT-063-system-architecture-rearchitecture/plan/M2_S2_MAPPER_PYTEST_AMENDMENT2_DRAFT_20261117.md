# FEAT-063 M2-S2 Shared OpenAPI Mapper — Pytest Amendment 2 (DRAFT)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Kept outside the worktree: the worktree row set is frozen at 104 rows until the remaining commands have run.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2.
- **Amends:** approved Task Approval Draft 1 (SHA-256 `4EAEA5340B1369E2A484FE86DE04AD6A1D949C2E838295C17988B3BCEC9666C3`) as already amended by Comparator Amendment 1. Draft 1 is not edited.

## 1. Why

The single approved pytest invocation ran once and failed (approval record entry "pytest result: FAILED"; run root `backend/tmp/pytest-openapi-d10-04e6f233980749808b0b99316d7640d4`; `run-manifest.json` SHA-256 `D9465305EDB83D5323D6629BF27F954769D6C2EE4700410A1CAAE39B0D7E1BC7`; `pytest.junit.xml` SHA-256 `C990D8C697806274645B9B68236662BB34BB7EAC6A01DCCDD8AF9BF2231C98B7`). 23 tests: 22 passed, 1 failed.

The one failure is `tests/contract/test_openapi_contract_catalog.py`, line 437, in `test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates`:

```python
    assert len(spec["tags"]) == 19
```

The actual length is 20. Read-only observations by the coordinating session:

- The top-level `tags` list has 20 entries in both `runtime-pre.json` and `runtime-post.json`. The mapper fix does not touch that list, and the comparison confirmed that non-operation fields did not change.
- The literal 19 is in the committed file at HEAD `5de30674bc826591ad4b3cc00fca53c7597ead51` (line 436 there). It is not part of this task's edits.
- Earlier in the same test (line 235 at HEAD; the line number in the working file was not re-read) the test asserts `spec["tags"] == public_tags(TAG_DESCRIPTIONS)`, and that assertion passed in this run. The catalog is therefore the source of the 20 entries; the literal 19 is out of date against the catalog.
- The S2 report of 2026-11-14 records this test failing earlier, at line 307, on a missing `description`. That is the defect this task fixes, so line 437 was not reached before.
- In `runtime-post.json` all 20 tags have a description and the 151 operationIds are unique. These are the facts the three remaining statements of the test (lines 438–442) check; this is a prediction from the exported schema, not a test result.

## 2. Requested change

One line in an allowlisted E path, `backend/tests/contract/test_openapi_contract_catalog.py`, line 437:

```python
    assert len(spec["tags"]) == 20
```

Nothing else changes. No source file, no other test, no payload, no card text other than the launch of a second invocation.

## 3. Effect on existing evidence (disclosed deviation)

- The post export's `source-state.json` pins this file at 21,274 bytes, SHA-256 `6D7967B6D321FFE4762F9DAEAF0A331D3E543A765FAACB84ECACEB69988909F9`. After the change the file has a different hash, so the passed comparison describes the worktree before this one-line change.
- This draft asks the owner to accept that without a new export and comparison, on this basis: the file is a test module; the exporter builds the schemas from the application package and does not import test modules; the changed token is an integer literal inside one assertion. That basis is static reasoning, not an observed re-export.
- The alternative is one more post export and one more comparison after the edit (two extra runs, both with their own ceilings). It removes the deviation and costs two more one-shot commands.
- Task runner, child bootstrap and pytest bootstrap contain no pin of this file's hash (searched: no occurrence of its hash or of a pinned-input table in those three payloads), so the edit does not block a pytest invocation. The worktree row set stays at 104 rows because the path is already a modified row.
- Mypy post and Ruff post have not run yet; they will see the edited file. The change is one integer literal.

## 4. Requested authorization

1. Approve the one-line change in section 2.
2. Accept the deviation in section 3 (no new export or comparison), or instead ask for the alternative.
3. Authorize **one** additional pytest invocation (ceiling 1, no retry) with the same three selections, the same approved card text, the same comparator report (`field-delta-report.json` SHA-256 `E8F265F51410FD968AC1A14F1113ACB07C555BEBA23DFBDE0093A7679FFE5C6D`) and the same payloads.
4. Mypy post and Ruff post keep their original ceilings and each still need their own launch instruction.

## 5. Limits

- Nothing in this draft has been executed or independently reviewed.
- Assertions after line 437 in the failing test have never executed; a different failure there, or anywhere on the second run, would consume the additional ceiling.
- The first pytest run stays on record as failed. Criterion 10 ("exactly one invocation") is not met as written; with this amendment it becomes "two invocations, the first failed on an out-of-date literal, the second authorized by Amendment 2".
- `OWNER_MODAL_CALL_APPROVED=NO`. M2-S2 remains PARTIAL / NOT COMPLETE.
