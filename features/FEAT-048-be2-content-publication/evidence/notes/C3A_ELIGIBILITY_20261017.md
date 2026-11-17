# C3a — current published-content eligibility, 2026-10-17

Branch: feature/be2-12-content-publication. Parent: 8478b36.
Scope: first cohesive part of approved C3, not full C3 or BE2-12 closure.

## Implementation

- Candidate typed owner boundary, current policy and source assessment contracts;
  no production default adapter and no caller-supplied identity/classification.
- Guard outside the entire storage transaction, retained through commit/rollback.
- Exact source assessment bound to organization/id/version/hash/policy; generic
  authorship, usage and moderation required. Child-derived/unknown fail closed.
- Scoped READ permission and current policy plus both exact effective review
  proofs required. Domain exact-proof validation is reused, not duplicated.
- SQL published-version enumeration keeps parent SHARE boundary; draft head does
  not substitute for published v1. Recall removes v1 but preserves history/hash.
- Requested audience checked; explicit version/hash never substitutes. Current
  policy/source/review denial fails closed rather than masking with older data.

## Actual checks

From backend, existing .venv Python, pytest -o addopts= -q on:
unit/test_learning_content_eligibility.py, unit/test_learning_content_domain.py,
contract/test_learning_content_commands.py,
unit/test_learning_content_persistence_shape.py,
unit/test_learning_content_c2_runner.py: **136 PASS, 0 skip, 8.88 seconds**.
New eligibility file contributes **44 cases**. Fixtures are explicitly labelled
component-only; they do NOT prove real owner authentication/revocation fencing.

Focused Ruff on four source files + two new test files: PASS. Focused strict
Mypy on four source files: PASS. Harness/architecture: PASS.
An initial validation attempt referenced a nonexistent shape-test path; pytest
ran no tests. Corrected to the existing unit test file before final PASS.
Initial focused lint/type findings (line length/narrow tuple inference and SQL
scalar annotation) were fixed before runtime. No failing attempt counted as PASS.

Owner-authorized portable PostgreSQL controller, with -IncludeC3Projection:

- PostgreSQL 17.11 official EDB Windows archive, same SHA256 as prior C2 runtime.
- New isolated loopback cluster, random private credentials, restricted test role.
- C2 runner exact 9-case inventory: **9 PASS, 0 skip, 8.52 seconds**, exit 0.
- New projection SQL case: **1 PASS, 0 skip, 1.40 seconds**, exit 0.
- Wrapper validates exact projection JUnit identity/count and rejects skip/errors.
- Existing Alembic path_separator warnings: 11 C2 + 1 projection; not hidden.
- Entire setup/start/bootstrap/test/stop/cleanup controller completed this time,
  unlike earlier C2's resumed setup. C2 historical receipts remain unchanged.

Private raw artifacts:

- .runtime/learning-content-c2/20261017-061933-584064/{summary.json,junit.xml,pytest.log}
- .runtime/local-pg-c2/lc-pg-7873cae85bc94d778bdcda1f8c0d6aad/
  {environment.json,c3-projection-junit.xml,server.log,control logs}

Portable root was removed after graceful shutdown; direct read-only checks found
the exact UUID directory absent and no listener at port 64379. Credentials,
cluster, downloaded ZIP and binaries were deleted (recreated only by rerunning
setup); sanitized metrics and private logs remain. No unrelated file removed.

## Limits and next checkpoint

SQL case proves owned persistence/projection behavior, NOT a fully wired resolver
using real owner adapters. New guard consistency obligations are documented in
plan/C3_BOUNDARY_CANDIDATE.md, still requiring owner contract conformance/adoption.
Current mutation orchestration, shared review-record responses, guarded receipt
replay, HTTP dispatcher/delegates, consumer pack and full lifecycle race suite
remain. No production-ready/DONE claim; no push/merge/deploy/package install.
