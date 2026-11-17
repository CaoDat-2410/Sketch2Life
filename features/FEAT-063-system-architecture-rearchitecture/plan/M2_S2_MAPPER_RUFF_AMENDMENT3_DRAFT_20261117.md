# FEAT-063 M2-S2 Shared OpenAPI Mapper — Ruff Amendment 3 (DRAFT)

- **Status:** DRAFT / NOT APPROVED / NOT LAUNCHED. Kept outside the worktree: the worktree row set is frozen at 104 rows until the remaining command has run.
- **Date:** 2026-11-17. **Author:** coordinating Claude session (Fable 5.2). **Owner:** Person 2.
- **Amends:** approved Task Approval Draft 1 (SHA-256 `4EAEA5340B1369E2A484FE86DE04AD6A1D949C2E838295C17988B3BCEC9666C3`) as already amended by Amendments 1 and 2. Draft 1 is not edited.

## 1. Why

The single approved Ruff post check ran once and failed (approval record entry "Mypy post result: NO NEW DIAGNOSTICS, NOT CLEAN; Ruff post result: FAILED"; run root `backend/tmp/ruff-openapi-d10-post-6c55a97c01b8453ea7947ffb67035133`; `run-manifest.json` SHA-256 `20F01E9047C8B277F199B1FF81CA17CB4B91B5802A87039DB4C6184B063FC747`; `check-raw-output.txt` SHA-256 `EBC6500575D796667A0847914086504027921B4F5EF7E95779695F2C48760CFE`).

Ruff reported one diagnostic on the N path `backend/tests/contract/test_openapi_schema_catalog_mapping.py`: `I001`, "Import block is un-sorted or un-formatted". The post card requires zero diagnostics on that path. The other diagnostic in the run, `I001` on `tests/contract/test_openapi_contract_catalog.py`, is the baseline one and is not in scope. `app.py` has none.

The N file was written under this task and was not lint-checked before the one-shot run. That omission is the coordinating sessions'.

## 2. Requested change

Apply Ruff's own suggested fix for that diagnostic, taken from the failed run's raw output, to the N file. Its whole effect is one inserted blank line after `import pytest`:

```diff
 import pytest
+
 from sketch2life.interfaces.http import openapi_contract
```

- File before: 10,596 bytes, SHA-256 `A6E5C7918B2460B9F8CFE1682168B3A41F83662F936480653F3635BEF438CC70`, LF line endings.
- File after: 10,597 bytes, SHA-256 `102B7D26C7E5E791592A953A8EEB0BF3DDA0AAE765BDEB05AE5D12094497BF50`. A copy of the proposed content is at `D:\GitHub\Sketch2Life\tmp\m2-s2-mapper-evidence\amendment3-proposed-test_openapi_schema_catalog_mapping.py`.
- Computed read-only by `D:\GitHub\Sketch2Life\tmp\m2-s2-mapper-r8\compute_amendment3.py`: the unified diff has exactly one added line and no removed line; the Python syntax trees of the two versions are identical (`ast.dump` equal); the longest line is 99 characters (limit 100).

Nothing else changes. The baseline `I001` on the E test file is existing debt and is deliberately not touched.

## 3. Effect on existing evidence (disclosed deviation)

- The post export's source-state manifest pins the N file at its earlier hash, and both pytest invocations ran on that earlier content. After the change the N file has a different hash.
- This draft asks the owner to accept that without a new export, comparison or pytest invocation, on this basis: the change is one blank line; the syntax trees before and after are identical, so the module's behaviour under Python is unchanged; a test module is not an input of the schema export. The syntax-tree equality was computed; the conclusion about the earlier runs is reasoning, not a re-run.
- The alternative is to repeat pytest (and, for full consistency, the post export and comparison) after the edit. It removes the deviation and costs up to three more one-shot commands.
- The Mypy post check ran on `src/sketch2life` only and did not include the N file, so it is not affected.

## 4. Requested authorization

1. Approve the one-blank-line change in section 2 (the N file becomes exactly the content with SHA-256 `102B7D26C7E5E791592A953A8EEB0BF3DDA0AAE765BDEB05AE5D12094497BF50`).
2. Accept the deviation in section 3, or instead ask for the alternative.
3. Authorize **one** additional Ruff post check (ceiling 1, no retry) with the same approved card text, the same three paths and the same baseline manifest (SHA-256 `7C8B06FF1001E64C27DB163265DC98AD83A1B33385B4981A88CA130951CEADEC`).

## 5. Expected outcome and limits

- Expected, not verified: zero added signatures and zero diagnostics on the N path, so the run manifest reports `success` true. The card will still end with its NOT CLEAN stop, because the baseline `I001` on the E test file keeps the tool's exit code at 1. That outcome is "no new diagnostics, NOT CLEAN", the same shape as the Mypy post result; it is not a clean Ruff pass.
- The expectation rests on applying the tool's own fix and on the failed run having listed every diagnostic of the three paths. Ruff has not been run on the proposed content.
- Nothing in this draft has been independently reviewed.
- The first Ruff post run stays on record as failed.
- `OWNER_MODAL_CALL_APPROVED=NO`. M2-S2 remains PARTIAL / NOT COMPLETE.
