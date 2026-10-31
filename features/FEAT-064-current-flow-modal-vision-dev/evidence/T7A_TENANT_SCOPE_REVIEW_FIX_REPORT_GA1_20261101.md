# T7a tenant-scope review fix — GOAL A1

**Status:** FIX APPLIED; `XONG-CHƯA REVIEW`. The P2 finding from the independent M1/T7a review has a narrow implementation fix and regression coverage. T7a and GOAL A1 remain pending until a separate reviewer accepts this correction.

## Finding and correction

`SqlAssistanceUnitOfWork.put_receipt()` already checked that the receipt key belonged to its bound organization, but it did not check the organization embedded in `receipt.snapshot`. A foreign-organization snapshot could therefore be serialized into a receipt row scoped to the repository organization.

The repository now checks `receipt.snapshot.facts.organization_id` against its bound organization before constructing SQL values or calling the connection. A unit regression creates a valid repository-scoped key with a foreign-organization snapshot, uses a storage mock that fails if called, and confirms the method raises `ValueError` without executing SQL. No schema, migration, service, port, or route changed.

## Files changed

- `backend/src/sketch2life/infrastructure/assistance/sql_repository.py`
- `backend/tests/unit/test_pilot_vision_persistence_ga1.py`
- This report, the appended FEAT-064 ledger entry, and the GOAL A1 context note.

The source and test are within the approved T7a allowlist. No approval record was edited.

## Verification

| Check | Result |
|---|---|
| Focused T7a persistence unit module | **18 passed**, 0 failed |
| GA1 offline regression with M1, T7a, and T6 add-ons | **649 passed, 4 skipped, 0 failed**; `TEST_EXIT=0`, outer exit 0 |
| Ruff check | Passed for the two changed Python files |
| Ruff format check | Both files already formatted |
| mypy strict | No issues in the two changed Python files; external cache, non-incremental run |
| `validate_harness.py` | `HARNESS_VALID` |
| `validate_repository_security.py` | `REPOSITORY_SECURITY_VALID` (6,073 publishable files scanned) |
| `validate_architecture.py` | `ARCHITECTURE_VALID` |
| `git diff --check` | Passed for the changed tracked source, test, ledger, and context paths; the new report was separately checked for UTF-8/LF and trailing whitespace |

The GA1 runner was copied byte-for-byte from the approved bounded-resolver snapshot (SHA-256 `766225385A00C5E6537C000F5BA71E559E5BABCF58243E0DB199FE342D3C8E76`). It blocks external network access, clears database/provider configuration, and keeps pytest temporary files outside the repository. Command and output are retained in snapshot `GA1_T7A_TENANT_SCOPE_FIX_20261101T233641`.

The initial Ruff invocation could not create the repository-local cache, and the initial incremental mypy invocation returned an internal cache error. Both were rerun with caches under the system temporary directory and passed. PostgreSQL/Alembic, Modal, GPU, provider, and external network were not used.

## Review state

This report records implementation and verification only. It does not supersede the earlier independent review or claim independent acceptance. The reviewer must confirm that the organization check runs before storage and that the regression test covers the reported cross-organization payload case. Do not start A2 until the reviewer accepts T7a and the owner closes GOAL A1.

An independent read-only Codex review thread was requested under stable request ID `a1-t7a-tenant-scope-review-20261101-2338`. The thread bridge returned `outcome_unknown` with `InvalidMessage: did not receive a valid HTTP response`; `get_operation` remained unknown and thread listing returned the same transport error. No thread ID or review result was obtained, so no independent-review completion is claimed.
