# Candidate CR08-01 — atomic video/foundation job participant

- State: OPEN_CANDIDATE; no shared owner adoption or migration change.
- Raised:2026-10-18; consumer BE2-08; foundation owner BE2-01, reviewer P4.
- Reference: dependency D03, approved revision1 P2. Parent C1 a3946e7.

## Existing surface

AiJobService.create_job owns authorization/eligibility decisions, scoped command
receipts/semantic dedup, owner fences, insert_job/outbox/audit intent under its
repository transaction. Owned video rows cannot be appended atomically by calling
this method and then committing a second repository. SQL job UoW exists but no
adopted video participant was located in the inspected baseline.

## Requested contract decision (not an implementation instruction)

Agree an authorized same-transaction participant for own video run/receipt rows,
or a separately approved recoverable-intent protocol whose states and recovery
are explicit. Do not expose unrestricted direct job-table writes or bypass
AiJobService authorization via pure domain job creation.

Candidate08 boundary: application/ports/knowledge_video.py AtomicVideoSubmission.
One logical submission must bind principal/org/session/key/body fingerprint,
canonical exact resolved pin digest and current owner/definition fences; commit
run + foundation job + dispatch + receipt/semantic/audit consistently. A durable
adapter must validate binding before commit, not only after returning a result.

## Conformance before actual atomicity claim

- Same-key same-body replay rechecks current authority; changed body conflicts.
- Exact semantic duplicate does not create another run/job/outbox.
- Fault after each staged insert has no accepted orphan/partial state, or explicit
  pending/recoverable state if that alternative is separately approved.
- Concurrent submissions/CAS conflict have an unambiguous winner and safe loser.
- Consent/source/audience/policy changes through commit cannot accept stale work.
- Worker handoff uses original request/attempt/profile/policy epoch provenance;
  recovery/cancellation never broadens to newer activation generations.
- Actual PostgreSQL transaction/restart evidence required, not fixture locks.

## Current implementation limit

Application guarded-create composition exists, plus explicitly fixture-only
run/job-intent/outbox/receipt staging. No actual BE2-01 job insertion, durable
submission bridge or production factory is supplied by that fixture. The CR does
not prevent other owned repository/media/HTTP work, but durable activation stays
gated until the chosen contract is adopted and tested. BE1/P4 wiring remains
owner-deferred; this record does not request credentials or provisioning.
