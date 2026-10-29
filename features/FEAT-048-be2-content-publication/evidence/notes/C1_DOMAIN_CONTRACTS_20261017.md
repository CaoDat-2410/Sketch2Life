# C1 domain/contracts evidence — 2026-10-17

Authority: actual owner approval of plan revision 1/P1–P4, recorded in commit
17ee033. This checkpoint does not claim SQL/auth/provider/integration readiness.

## Implemented

- Pure immutable ContentVersion lifecycle, separate version/record/review
  revisions, canonical payload/hash, scoped capability and author separation.
- Exact safety/pedagogical proofs bound to target/hash/context/audience/policy;
  edit does not inherit review, request changes/resubmit clears prior review.
- Recall/archive retain bytes/hash/review lineage and terminal state.
- Typed content branch of DATA-33, all eight actions, strict payload/refs/age
  and shared ExactContentReviewCommandV1 use. No duplicate DATA-24 schema.
- Tests for wrong scope, self approval, bad types, old hashes/context/policy,
  source/purpose validation, immutability and retirement.
- Domain expects already verified/current authority from a future application
  port. These objects are not proof of authentication or commit-time revocation.

## Actual commands and results

Working directory backend, existing .venv/Scripts/python.exe; no install:

1. -m pytest tests/unit/test_learning_content_domain.py
   tests/contract/test_learning_content_commands.py:
   **79 passed in 0.43s**, no skip.
2. Same tests plus tests/contract/test_ai_job_contracts.py,
   tests/contract/test_ai_job_polling.py, tests/unit/test_ai_job_lifecycle.py:
   **189 passed in 7.29s**, no skip.
3. -m ruff check on new domain, schema and two test files: PASS.
   Initial one-character line-length finding corrected before final PASS.
4. -m mypy new domain package and schema: PASS, three source files.

No SQL migration/worker/runtime service or real provider executed. C2 persistence
and C3 current policy/source/authority integration remain necessary. CMD-48
delegate router and HTTP are C4; this content union is not the whole dispatcher.

## Review limitations

Focused author review, not independent cross-owner sign-off. Domain snapshots
and review proofs are trusted internal values; untrusted ingress is through
typed DTOs and application verification, which are not yet all wired.
SRS mandatory runtime/consumer acceptance remains incomplete.
