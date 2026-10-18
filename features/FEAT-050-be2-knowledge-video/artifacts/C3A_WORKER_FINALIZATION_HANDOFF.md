# C3a — worker/private staging/finalization recovery handoff

2026-10-18; parent9d2677d, approved revision1 P3. Owned application component,
NOT an actual foundation/storage adapter or production worker registration.

## Delivered

- VideoWorker requires explicit job type and admission; rejects mismatched job,
  attempt or capability. Admission None does not invoke the media pipeline and
  does not mean success. Foundation still owns retries/timeouts/progress/ACKs.
- VideoCompletionService revalidates original pin/operation/strategy, explicit
  current profile and validated media bytes/report before private staging.
  Original staging/completion keys are stable and separately namespaced from
  foundation completion receipt fingerprints. Exact stage scope/hash required.
- Current authority checks before/after stage and before finalization. These
  checks do NOT replace actual held commit fences in AtomicVideoFinalizer.
- Strict accepted receipt validation binds original job/attempt, actual enum
  states, native revisions/time/hash and exact finalized VideoRun/artifact.
  Accepted means historical ready_for_review, NOT Teacher approval or play grant.
- Lost stage ACK: pending original staging key; recover_stage queries retained
  original preparation without another render/stage. Missing/outage stays pending.
- Lost final ACK or receipt outage/mismatch: pending original completion key;
  reconcile queries receipt, no guessed rerender/retry/cleanup. Historical accepted
  receipts can be recovered after eligibility changes, but lookup must authenticate
  original backend recovery scope; this does not authorize current exposure.
- Verified stale/rejected results or pre-finalization authority failure request
  scoped quarantine. cleanup_state remains pending, including request failure.
  No claim of durable cleanup acknowledgement, completed deletion or actual purge.
- Closed local reason codes; no raw provider diagnostics, artifacts/URLs or
  capabilities returned. Local outcomes are not broker ACK/job-state mutations.

## Required actual adopters / conformance (still OPEN)

1. VideoWorkerAdmission: actual authorized foundation start, original request/type
   refs and capability; own run start through adopted same-UoW/recovery protocol.
   Settled duplicates must not call providers; ambiguous work recovered, not reset.
2. VideoPrivateStaging: durable original-scope journal/copy registration before or
   with effects, immutable private bytes, key/body dedup and authenticated lookup.
   Retain preparation metadata/bytes for recovery, with real retention policy.
3. AtomicVideoFinalizer: actual authorized foundation transaction with own run/job
   CAS, exact receipt/audit/outbox; current consent/source/audience/policy epoch/
   profile/kill fences held to commit. No sequential commits described as atomic.
4. Cleanup processor MUST atomically fence accepted references with finalization:
   accepted wins even when a concurrent worker commits after an absent lookup.
   A quarantine request alone must never hide/delete an accepted artifact.
   Test actual commit-vs-cleanup races/restarts; local mocks do not prove this.
5. Provider-specific input/script/output/cache/job-copy inventory and BE2-14
   lifecycle adoption remain pending. These ports do not complete that inventory.
6. Actual07/BE1/current authority/profile/library/decoder/provider bindings,
   production dispatch composition and separately gated actual SQL/runtime tests.

CR08-01/D01–D06 remain open. No foundation/shared migration or production binding
modified. P3 partially implemented, P4 consolidated runner/audit still pending;
actual P5 generation remains separately gated, whole08 NOT_DONE.

## Evidence

45 explicit fixture-only worker cases;374 cumulative08 cases. Broad1809 PASS
(374 own +1435 existing), zero failures/errors/skips,50 suites,639 backend source
inventory unchanged. Ruff/Mypy16 source files PASS. See own evidence E06 for
source digest/JUnit path and checks. Synthetic bytes/receipts/authority/staging
are not evidence of actual decode, durable atomicity, cleanup or generation.
