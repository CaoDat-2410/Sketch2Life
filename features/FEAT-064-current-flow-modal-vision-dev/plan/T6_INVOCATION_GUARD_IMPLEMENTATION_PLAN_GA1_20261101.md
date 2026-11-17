# T6 — per-attempt invocation guard and bounded HTTP transport (GOAL A1)

**Status:** Frozen implementation proposal; the append-only approval record is authoritative for execution status.

## Authority and inputs

- Owner-approved V4: `.claude/handoff/OWNER_DECISIONS_G3G4_V4_20261101.md`, SHA-256 `E11FFBCE0F655C010E679773D231D3E36930A0B960E705450499E2A2A69191F6`.
- Goal A1: `.claude/handoff/CODEX_GOAL_G3G4_A1_20261101.md`, SHA-256 `90B546430E1E1E2E8B40078EBD7FF2CA108D0F785C054C06620F2EBBF6902949`.
- Contract baseline: `evidence/T0_CONTRACT_FREEZE_20261031.md`; T7a ledger implementation is pinned by `plan/T7A_DURABLE_REPOSITORIES_LEDGER_PLAN_GA1_20261101.md` and its T7a report.
- Regression gate was cleared by the separately approved test-only revision-graph alignment: focused test 1 passed; offline suite 618 passed, 4 skipped, 0 failed. Evidence is in `evidence/GA1_REVISION_GRAPH_HEAD_ALIGNMENT_REPORT_20261101.md`. T6 does not rerun Gate 1 before implementation.

## Objective

Implement only the A1/V4 D3 invocation boundary for a future pilot caller. A caller creates a fresh guard and transport for one server-issued UUID `run_id`, `job_id`, and `attempt_id`. The guard uses the durable T7a `InvocationLedger`; the transport never retries or follows redirects. No worker, route, composition, provider operation, PostgreSQL run, or Modal call is part of T6.

## Contract decisions frozen by V4 D3

1. Add `InvocationGuardPort` to `application/ports/vision_analysis.py`; leave `ObservationRequest` and `application/services/vision_analysis.py` unchanged.
2. Add `NOT_SENT_GUARD_REFUSED`, `NOT_SENT_RUN_ALREADY_USED`, and `PROVIDER_OUTCOME_UNKNOWN` failure codes. A prior durable `SENT`/`UNKNOWN` invocation is surfaced as `PROVIDER_OUTCOME_UNKNOWN`, never as evidence that no call occurred.
3. Guard claim is unique by server-issued `run_id`; bind and check all four ledger fields `(run_id, job_id, attempt_id, organization_id)`. Persist `SENT` before the first HTTP request byte can be sent. Any ambiguous post-SENT condition is terminal `UNKNOWN`; never reset or reuse the claim.
4. New HTTP `JsonTransport` uses `http.client`, HTTPS except loopback HTTP for tests, one monotonic total deadline of 160 seconds for connect/request/response/decode, and a socket timeout recalculated from remaining time before connect/send/header/body-read operations. It caps response bytes at 1,000,000, does not follow redirects, and performs exactly one request. Test code may inject a shorter deadline.
5. A result is terminal `SUCCEEDED` or `FAILED` only after a complete HTTP 200 JSON object has been validated by the existing V2 adapter/bridge. Validate identity for both V2 success and failure (`correlation_id`, source image reference, and profile). Invalid/mismatched/partial JSON, non-200, reset, timeout, late response, or ledger-finalization uncertainty maps to `PROVIDER_OUTCOME_UNKNOWN` with `provider_invoked=True` after SENT.
6. Add `LIVE_LEGACY_BRIDGE` provenance. Only the guard decorator may relabel a bridge result as live, and only after the complete V2 success is accepted or a complete typed V2 failure is validated and durably finalized. Malformed or uncertain results remain UNKNOWN and are not labeled live.
7. Add `PILOT_VISION_RETRY_POLICY = JobRetryPolicy("pilot.vision_single_attempt.v1", 1, 0, 1, 0, 180000)`; do not change `FIXTURE_RETRY_POLICY`, `services/ai_jobs.py`, or worker composition.

## Implementation sequence and layers

| Step | Layer | Change | Acceptance evidence |
|---|---|---|---|
| T6.1 | L1 | Add invocation-guard protocol and the three closed failure codes; extend domain evidence enum/validation and analysis-result provenance literal for `live_legacy_bridge`. | Contract tests validate live provenance and require the existing complete model identity fields. |
| T6.2 | L4 | Add SQL-ledger-backed per-attempt guard using the T7a `InvocationLedger`; fail closed on invalid identity, duplicate claim, ledger errors, or failed `mark_sent`. Track only status/completion/hash metadata in memory; never retain headers or raw response bodies in the ledger. | Unit tests prove claim/SENT ordering, duplicate refusal, replay after SENT as UNKNOWN, and terminal state transitions. |
| T6.3 | L4 | Add `http.client` JSON transport; validate URL/path, prepare payload before claiming, establish connection under remaining deadline, persist SENT before `request()`, recalculate socket timeout for every blocking phase and response chunk, cap body, accept only HTTP 200 JSON objects, close every connection, and map all exceptions to the existing sanitized adapter exception types. | Loopback tests cover exactly one request, no redirect/retry, status/error/timeout/reset/truncation/malformed body, and slow-drip total deadline using a short injected timeout. |
| T6.4 | L4 | Add guarded `VisionObservationPort` decorator. No-send local/precheck failures remain no-send; guard refusals become the matching NOT_SENT code; after SENT, only complete HTTP 200 plus bridge-validated typed outcome can finalize success/failure. Every other path finalizes UNKNOWN when possible and returns UNKNOWN even if the wrapped bridge produced another failure. Mark accepted live success evidence as `LIVE_LEGACY_BRIDGE`. | Tests cover one-success call, guard refusal at zero calls, two-worker race at no more than one call, restart after SENT at zero additional calls, and bridge outcome override on uncertainty. |
| T6.5 | L4 | Add the fixed one-attempt pilot retry policy. | Tests assert exact policy ID, `max_attempts == 1`, `attempt_timeout_ms >= 180000`, and unchanged fixture policy values. |
| T6.6 | L7 | Run focused T6 tests and the established offline regression suite (618 passed/4 skipped baseline plus T6 tests); run Ruff, mypy, three validators, and `git diff --check`. Update report, append ledger status, and snapshot. | Actual outputs recorded; no regression outside the new tests. No PostgreSQL or provider execution. |

## Exact allowlist

- `backend/src/sketch2life/application/ports/vision_analysis.py`
- `backend/src/sketch2life/domain/vision_analysis.py`
- `backend/src/sketch2life/contracts/schemas/analysis_results.py`
- `backend/src/sketch2life/infrastructure/vision_analysis/invocation_guard.py` (new)
- `backend/src/sketch2life/infrastructure/vision_analysis/transport.py` (new)
- `backend/src/sketch2life/infrastructure/vision_analysis/pilot_policy.py` (new)
- `backend/src/sketch2life/infrastructure/vision_analysis/legacy_v2.py` (only for response identity validation on typed V2 failures)
- `backend/tests/unit/test_invocation_guard_transport_ga1.py` (new)
- This plan; append-only `approvals/TASK_APPROVAL.md`; new `evidence/T6_INVOCATION_GUARD_IMPLEMENTATION_REPORT_GA1_20261101.md`; append-only `status/PILOT_GOAL_LEDGER_20261101.md`; one new ignored `.claude/handoff/snapshots/GA1_*` snapshot.

No other path is allowed. If implementation requires another path, stop and request a new scope.

## Exclusions and safety boundary

- No edits to `application/services/vision_analysis.py`, any `ai_jobs` service/port/schema/policy, migration/schema, BE1 files, `core_store.py`, Modal deployment, route, worker, application composition, environment/token file, or external endpoint configuration.
- No PostgreSQL/DB operation for T6; the SQL ledger's persistence and state transitions were exercised under the separate T7a acceptance scope. T6 unit tests use an in-memory ledger double and loopback HTTP only.
- No Modal/GPU/provider call, external network, real-child data, stage, commit, push, stash, reset, or destructive cleanup.

## Acceptance criteria

1. A valid attempt persists a unique claim and `SENT` before the only outbound HTTP request. Reusing a run never sends again.
2. Guard refusal and pre-send validation/connection failure produce zero HTTP requests. If a previous attempt is durably SENT/UNKNOWN, surface UNKNOWN rather than a no-cost claim.
3. Exactly one accepted complete V2 success is recorded `SUCCEEDED`; a complete identity-matched typed V2 failure is `FAILED`; all ambiguous post-SENT outcomes are `UNKNOWN` and never retried.
4. The 160-second monotonic deadline covers connect through body decode; each socket operation receives only remaining time. Redirects and retries are absent. Slow-drip tests prove the total deadline rather than merely a per-read timeout.
5. No `ObservationRequest`, application service, fixture retry policy, T7a schema/migration, or nonallowlisted file changes.
6. Focused T6 tests pass. Offline regression result is exactly measured against the cleared 618/4 baseline plus new T6 tests; all skips/failures are reported. Ruff/mypy and all three validators return real verdicts; `git diff --check` is clean.
7. Evidence and ledger state `XONG-CHƯA REVIEW` only after all criteria and snapshot are complete; no independent review is claimed.

## Residual limitations

T6 supplies the per-attempt guard/transport components but does not wire a worker or caller; that belongs to a later, separately approved goal. Durable host witness and full-host rollback protection remain deferred. A `SENT` row surviving restart without terminal completion is UNKNOWN/HOLD and permanently blocks reuse. No live provider behavior or model quality is established.
