# C3b — application command lifecycle and receipts

Date: 2026-10-17. Branch: feature/be2-12-content-publication. Parent: d09cb62.
Approved authority: revision 1/P1–P4 and separate portable PostgreSQL test approval.
This is C3 component/owned-runtime proof, not BE2-12 acceptance closure.

## Implemented

All eight DATA-33 content actions: create/edit/submit_review/record_review/
request_changes/publish/recall/archive. Current independent capabilities and
non-author review/publish separation, exact organization/id/version/hash,
separate record/review CAS and exact generic-library context/audience are checked.
Shared DATA-24 command/record is consumed unchanged. Review response includes
server ID/revision/reviewer/time/policy/effectiveness; body bytes are not in
receipts or history/outbox payloads. Edits do not carry approvals.

Atomic SQL state/proofs/receipt/history/outbox; guard retained through commit.
Scoped fingerprint includes full command and If-Match. Identical duplicate may
return recorded metadata with separate current revision/state only after current
guards. Changed request/precondition conflicts. Parent-lock receipt recheck
handles duplicates that waited for a winner. Unique create loser rolls back,
then validates the winner in a fresh read transaction; no blind write retry.
Revoked/replaced/context-stale reviews cannot authorize replay. Publication
replay after recall is denied. Recall remains possible with current recall
capability even after source/policy usage becomes unsafe. See full semantics in
plan/C3_COMMAND_SEMANTICS.md and candidate owner obligations in C3_BOUNDARY_CANDIDATE.md.

## Actual local checks

Existing backend .venv Python, pytest -o addopts= -q --tb=short, selected files:

- unit/test_learning_content_commands_service.py (47 new component cases)
- unit/test_learning_content_eligibility.py
- unit/test_learning_content_domain.py
- contract/test_learning_content_commands.py
- unit/test_learning_content_persistence_shape.py
- unit/test_learning_content_c2_runner.py
- contract/test_ai_job_contracts.py
- contract/test_ai_job_polling.py
- unit/test_ai_job_lifecycle.py

**293 PASS / 0 skip, 8.85s** (183 content component cases + 110 foundation).
Memory fixtures are explicitly component-only, never SQL/revocation proof.
Initial run: 37 PASS / 2 FAIL because two CAS/hash tests used an author without
recall capability; corrected the test principal to recaller. Permission denial
was correct and implementation was not weakened. Initial style findings fixed.
Focused production Mypy and focused source/test/runner Ruff PASS; architecture,
harness, security and whitespace checks PASS before checkpoint commit.

## Actual PostgreSQL 17.11 consolidated run

Portable controller with -IncludeC3Projection -IncludeC3Commands:

- C2 exact inventory: 9 PASS / no skip, 11.99s.
- C3a projection: 1 PASS / no skip, 2.62s.
- C3b source-pinned runner: 8 PASS / no skip, 10.24s.
- Wrapper/runner exits 0; C3b source hashes unchanged before/after test execution.
- Existing Alembic path_separator deprecation warnings: 11 + 1 + 8, not hidden.
- Synthetic source/authority/review ports are ASSUMED_CONTRACT. These SQL tests
  prove actual content SQL transactions and application orchestration, NOT real
  BE1/BE2-05 consistency/adoption. No external source/consent service is simulated
  as if its runtime were proven.

Cases: application publish/repository-connection reconstruction/replay/recall;
receipt failure rolls back all writes; simultaneous identical create forces
both first receipt reads to miss and recovers SQL unique winner; parameterized
edit-publish/review-publish/publish-recall; duplicate submit emits once; negative
review/resubmit preserves immutable proof history but clears effective context.
Application repository reconstruction is not an independent process restart
claim; C2 has a separate child-process test for persisted data.

Raw ignored receipts:

- .runtime/learning-content-c2/20261017-064816-624484/
- .runtime/learning-content-c3b/20261017-064839-418469/
- .runtime/local-pg-c2/lc-pg-8f77c11211244e6eafac615f2bd5fdc1/

## Cleanup and limits

Official EDB portable ZIP SHA256 matched prior approved runtime. Server bound
loopback only, role restricted to disposable test DB creation; random passwords
kept privately. Server stopped gracefully, exact temporary UUID root removed
including cluster/binaries/ZIP/credentials. Direct checks: root absent; port
50868 not listening. Logs remain private; recreating runtime requires setup again.
No system service/GPU/model/dependency install; no push/merge/deploy.

C4 sole dispatcher/HTTP/consumer pack, C5 audit/handoff and true owner adapter/
fencing integration remain. Do not mark whole BE2-12 DONE from these results.
