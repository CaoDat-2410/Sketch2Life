# Part 6 — atomic repository/coordinator mini-plan

Scope: own07 single-process fixture; starts source only after parts1–4 review closes.
Reviewer: separate atomic_review agent, actual source and assertion review required.

A: one coordinator RLock boundary guards all07 store and mutable fact publications.
Lock order coordinator then store. Nested units share reentrant boundary; same-thread
external publication queues until outermost unit completes or rolls back, while other
threads block. Reads return copies/immutable values. Deferred callbacks drain in finally;
callback failure must not lose later queued publications or retain the lock.

Repository stages heads, immutable versions, correction records, scoped accepted receipts,
audit and exact supersession outbox. Capture repository generation before staging, compare
after before_commit hook and before publication; inner accepted unit wins over stale outer.
CAS uses old version and verifies one-step increase. Unique version/receipt/event identities
reject duplicates. Fault injection covers every write stage and final commit, preserving
the prior complete committed snapshot. Read-only/no-op units do not increment generation.

Files: infrastructure/knowledge_bundle/{__init__,coordination,fakes}.py;
tests/unit/test_knowledge_bundle_races.py (repository-only first). Root owns these files.
Ports/types come from completed parts1–4; application domain does not import infrastructure.

Verification: focused pytest with retained log/JUnit/exits, Ruff and strict mypy on affected
sources. No sleeps: Events/Barriers prove attempted publication, old facts in lock window,
publication after rollback, other-thread completion and lock release. Probe nested winner
actual state and receipts/outbox, not merely callback order. Handler-only race assertions
remain pending until parts5/8; do not mark whole Rxx PASS from this partial proof.

Acceptance: R01–R07/R09/R10/X03 repository oracles; final42row map binds actual integrated
assertions later. Durable/distributed fences, producer01–06 edits and real consumer08 remain
outside this part. Generation and publication safety changes stay within approved OD05.

Design review: atomic_review reviewed this design intent; no design P1/P2 reported at initial
review. B/C execution verdict remains NOT_RUN until implementation and independent review.

Pre-code refinement reviewed by atomic_review: Facts and Repository ports expose a readonly
opaque coordination_token. Service composition rejects differing identities before any work;
the token is the underlying own07 coordinator. This makes the promised shared fixture boundary
testable without a generic coordinator abstraction or a distributed/runtime guarantee. Queue
callbacks capture defensive copies before publication; getters and snapshots return copies.
Drain failures continue remaining queued work, preserve primary unit exceptions with a note,
and otherwise surface an ambiguous acknowledgement after an already committed unit.

## B/C checkpoint — 2026-10-20

25 repository/coordinator/adapter tests pass, zero skips. Ruff and strict mypy (normal and
fresh cache, typed dependency following) pass. Initial Ruff/style and an inappropriate
follow-imports=skip profile's Pydantic Any errors are retained in raw local receipts; corrected
profile preserves strict checking and typed Pydantic dependencies, without source suppressions.
Independent KB-A01/P2 exposed completed UoW aliasing committed state. Detached publication
copy and closed-unit guards fix both commit/rollback escapes; regressions execute. Reviewer
also removed generation guard and bypassed queued publication in isolated mutants: actual
tests failed as expected. Verdict PASS_WITH_INTEGRATION_NOTES; handler Rxx proof remains5/8.
Snapshot `8fb8622000b2dd7bb5e98423e4cd5c359aa1303c5696522f09312c1e1135a593`;
raw commands/JUnit/logs in local/part6-combined-retest; independent report in
INDEPENDENT_ATOMIC_REVIEW.md. No runtime/durable/multi-owner guarantee inferred.
