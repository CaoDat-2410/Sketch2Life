# BE2-01 Phase A — independent implementation review

- Date: 2026-10-14, Asia/Saigon.
- Review result: **NEEDS_REVISION**. Existing checks reproduce PASS, but additional probes expose defects not covered by the current fixtures.
- Scope: Claude's additive Phase A code and contract/runner/handoff evidence, baseline b9204d8c9eb4f8a1ee6d4db4de5ee23672e0392c.
- Reviewer: Codex primary plus independent read-only lifecycle, HTTP/contracts and fakes/provider-copy review agents.
- Method: local source/SRS/plan/approval inspection, tests and fresh synthetic in-memory probes. No provider calls, dependency installs, code fixes, commits/push/deploy.
- Approval remains Phase A only; P1/P2/P4 schema/policy adoption is not granted by this review.

## Verification reproduced

Existing root backend/.venv was used, with PYTHONPATH pinned to this worktree backend/src and bytecode/cache writes disabled. Module origin was checked from source imports/probes. No dependencies were installed.

- New tests + four selected regression files: **172 passed, 1 skipped**. Skip: live application route import needs Pillow.
- Runner with HTTP: **171 checks, 0 failures**; results_sha256 matches Claude's recorded digest. Report counts 21 rows because it adds A-17-http to the 20 criteria. It retains a core A-17 NOT_RUN entry even though supplemental HTTP checks ran; read both records rather than interpreting count as 21 distinct acceptance criteria.
- These reproduce the declared cases, not the additional edge cases below. Current test PASS does not close the review findings.

Receipts: `../raw/codex_review_pytest.txt`, `codex_review_runner.txt`, `codex_review_runner_report.json`; metadata `../metrics/codex_review_pytest.json`, `codex_review_runner.json`. Fresh probe outputs: `codex_review_probes.json`, `codex_review_boundary_probes.json`.

## Findings requiring correction within Phase A

### R01 [P1] Rejected worker output can quarantine a foreign artifact

Location: `backend/src/sketch2life/application/services/ai_jobs.py:539–543`, quarantine helper at 653–655.

Start an organization-A job and obtain its valid job-scoped worker capability. Register a synthetic artifact for organization B. Supply B's artifact in A's completion with a wrong input hash. Completion returns INPUT_MISMATCH, but the foreign artifact is added to the quarantine map. Malformed foreign-output rejection follows the same unscoped path. Claimed refs are mutated before descriptor ownership/lineage checks; possessing capability for one job does not authorize mutation of other artifacts.

Fix: make quarantine scoped to organization and valid job/attempt/source lineage; validate refs before mutation, including rejection paths. Add cross-organization and same-organization/other-job tests; unknown/foreign refs must not modify other artifacts. Keep valid local unsafe outputs quarantined. Relevant: A-11/A-15/A-17, artifact provenance/access boundary.

### R02 [P2] Semantic dedup silently merges different targets/audiences/purposes

Location: `application/services/ai_jobs.py:254–274`; key shape `application/ports/ai_jobs.py:79–86`.

Create request for target A/session A/child A. Submit the same request_ref with a fresh command key but target B/session B/child B. Service returns the same job as deduplicated; stored scope remains A. Semantic key excludes target/purpose/session/subjects. Existing command fingerprint includes these but cannot protect a new key's semantic lookup.

Fix: bind business dedup to relevant immutable authorized scope, or reject inconsistent metadata for an existing request identity. Command receipts must remain principal-scoped; same valid scope can still dedup across authorized principals. Tests for target/session/subject/purpose changes and matching-scope duplicates. Relevant: A-03/A-04 and current audience/purpose checks.

### R03 [P2] Guard-failed completion consumes the active attempt's final receipt slot

Location: `application/services/ai_jobs.py:424–444`.

A valid success claim arriving while queued gets an INVALID_STATE receipt. After start, identical valid claim replays rejection and the job stays running. A wrong-input claim receives INPUT_MISMATCH; correcting it then raises COMPLETION_CONFLICT although the active job was never completed. The (job, attempt) completion slot stores nonmutating rejected submissions as if they were accepted final completion.

Fix: distinguish guard-failed diagnostic/rejection receipts from authoritative accepted completion. Invalid identity/context submission must not prevent a later valid completion of an unchanged active attempt. Preserve immutable accepted receipts and same accepted identity/different output conflict. Test queued→start replay and wrong input→corrected completion, as well as genuine duplicate/conflict/cancel/superseded cases. Relevant: A-05/A-11.

### R04 [P2] Malformed provider failure code persists a job that cannot be polled

Location: `application/services/ai_jobs.py:553–555`, wire code constraint `contracts/schemas/ai_jobs.py:31`.

Accept worker failure with code `http 503 from provider` and retryable false. Receipt is accepted and job persisted; Teacher CMD-44 returns HTTP500 because outbound failure.code fails ErrorCode validation. Worker dataclass itself validates neither code nor outcome; outbound validation happens after the invalid state exists.

Fix: validate/map worker outcome at the internal boundary before persistence. Unknown provider codes should become a safe typed application failure with redacted diagnostic, or explicit rejection that does not poison the active attempt. Add end-to-end worker-failure→poll test, including malformed/unknown/sensitive provider strings. Relevant: A-02/A-15.

### R05 [P2] Concurrent same-key purge dispatches twice and disagrees about receipt

Location: `application/services/provider_copy_lifecycle.py:74–83`; fake registry `infrastructure/ai_jobs/fakes.py:391–395`.

Two threads purge same organization/scope/key/copy with a barrier-controlled adapter. Both see no receipt and call the adapter. Results return receipt_fx_1 and receipt_fx_2; registry stores one while copy stores the other. setdefault silently loses the duplicate receipt but service applies its local value anyway.

Fix: fake atomic claim/lock/CAS boundary for the receipt identity and copy mutation; exactly one dispatch and one consistent result under concurrent same-key calls. This is fake semantics, not Phase B durable transactions. Relevant: A-18.

### R06 [P2] Replaying an older purge request after successful retry raises an error

Location: `application/services/provider_copy_lifecycle.py:81–83`.

Purge key p1 yields Pending/r1. Retry key p2 yields verified fixture Deleted/r2. Replay p1 tries to reapply old r1 to current deleted state and raises InvalidCopyTransition. Tests only replay p1 before p2.

Fix: replay immutable stored request result without mutating current newer copy state, or return a clearly documented current projection retaining original receipt identity. Deleted must remain final; replay must not raise or dispatch again. Add pending→retry deletion→old-key replay plus exception/pending retries. Relevant: A-18.

### R07 [P2] Candidate shape validator crashes on malformed enum values

Location: `contracts/schemas/ai_contract_candidates.py:280–283`.

Set request_reason=[] on a valid DATA-21 fixture. check_shape raises TypeError (unhashable list) instead of validation errors. DATA-27 strategy and DATA-28/33 action have the same issue for list/dict.

Fix: type-check enum values before membership lookup; malformed JSON should produce deterministic errors without exceptions. Add list/dict/null/numeric enum fixtures across affected shape specs. Relevant: A-02/A-19.

### R08 [P2] DATA-25 full validator accepts result refs on queued jobs

Location: `contracts/schemas/ai_jobs.py:124–125`.

Take succeeded_accepted fixture, change state to queued, clear started/completed timestamps and set poll_after_ms=2000, retain accepted disposition/result refs. Strict JSON validation accepts one result ref. Spec permits refs only for succeeded + accepted. Current service projection withholds queued refs; this is a boundary validator defect, not a proven public leak.

Fix: refs require both succeeded and accepted; constrain disposition/state consistency where source/spec defines it. Negative fixtures for non-success states with refs. Relevant: A-02/A-16.

### R09 [P2] Outbox dispatch omits current eligibility check

Location: `application/services/ai_jobs.py:361–375`.

Create queued job, revoke its subject through fake eligibility, call dispatch_outbox. It enqueues one message and leaves queued state. Worker start later cancels; provider execution is blocked there, but approved A-14 explicitly includes blocking revoked/ended/recalled/expired/killed work at dispatch.

Fix: recheck current eligibility before enqueue; settle/drop denied pending work without sending and without creating a new attempt. Test consent/session/recall/expiry/kill-switch between create/retry and dispatch, plus valid queue outage/replay behavior. Relevant: A-14.

### R10 [P2, lower consequence] Conditional polling never receives new time-based backoff hint

Location: `application/services/ai_jobs.py:523–529`.

Queued response says poll_after_ms=2000. Advance fake clock 60 seconds: unconditional response says 10000 but ETag unchanged. Conditional response with old tag is 304, hiding the updated guidance from a consumer following the handoff contract.

Fix: include the computed public hint in representation variant or supply refreshed polling guidance on 304 under a documented contract. Preserve authorization before conditional handling. Test time advancement + same revision + If-None-Match. Relevant: polling/ETag/hints, A-10.

### R11 [P3] Child projection validator lacks applicable terminal/failure invariants

Location: `contracts/schemas/ai_jobs.py:143–146`.

Strict Child schema accepts terminal succeeded with poll_after_ms=2000 and failed states with failure null. Full schema rejects those combinations. Current service emits valid payloads; schema consumers have inconsistent validation.

Fix: share applicable state/failure/poll consistency constraints without exposing adult fields; add Child negative fixtures. Relevant: A-02 and minimal role contract.

## Reproduction notes

Use existing interpreter with worktree backend/src on PYTHONPATH, no bytecode/cache writes. All data synthetic. Fresh harness for each case; direct probes call the same application/domain interfaces as fixture runner. Boundary output JSON records concrete observed values. Examples:

```python
# R02
h = build_fixture_harness()
a = h.service.create_job(h.create(key="a"))
b = h.service.create_job(h.create(key="b", target="target_fx_other",
                                 session_id="session_fx_other", subjects=("child_fx_other",)))
assert a.job_id == b.job_id  # current defect; scope B is discarded

# R03
h = build_fixture_harness()
j = h.service.create_job(h.create()).job_id
m = h.next_message()
claim = h.success_claim(m)
cap = h.capability(j)
first = h.service.accept_completion(cap, claim)  # INVALID_STATE
h.service.start_attempt(cap, j, m.attempt_id)
second = h.service.accept_completion(cap, claim)  # same rejected receipt

# R04
h = build_fixture_harness()
j = h.service.create_job(h.create()).job_id
m = h.start_next()
h.service.accept_completion(h.capability(j),
                            h.failure_claim(m, code="http 503 from provider", retryable=False))
# Teacher GET in isolated fixture TestClient(raise_server_exceptions=False) returns 500.
```

Other probes are attributable to the independent review agents and primary reproductions recorded in raw JSON. No probe patched production/tests. Initial local probe invocations had import/fixture-wrapper assumptions corrected before results; raw evidence contains the completed reproductions, not claims from those failed invocations.

## Next action and residual gates

Claude should fix R01–R10 inside the already-approved Phase A scope, address R11 in the same contract pass, and add meaningful regression fixtures/tests. Re-run affected component checks/runner and required repository gates; keep prior receipts and add actual post-fix evidence. Independent review needs a new pass against those changes before Phase A can be accepted.

P1/P2/P4 adoption and missing Pillow live-route check remain pending; no full backend/model/GPU/device/actual deletion/durable recovery claim. Phase B and other BE2 cards still need their own scope/decisions/approval. No additional Phase B approval is needed to correct these Phase A defects.
