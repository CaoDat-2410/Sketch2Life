# BE2-03 A1 implementation evidence — 2026-10-17

State: **A1_CODE_COMPLETE_PENDING_CODEX_REVIEW**. Offline component only; full BE2-03 NOT_DONE.
No owner acceptance, runtime/model/provider claim, or Git action.

## Authority and identity

- Approval: owner approved plan revision 3 (`../../plan/PLAN_REV3_APPROVED.md`, SHA256
  e1fce645a5d8c98efe366865f5a8a1b9c81c8a48626723c4e73f0c646979d3e5) with D1–D11 as recommended;
  verbatim in `../../approvals/TASK_APPROVAL.md` (recorded 2026-10-17 19:58 +07:00).
- Worktree `.worktrees/be2-03-assistance-orchestration`, branch
  `feature/be2-03-assistance-orchestration`, HEAD f120c4f (stacked on BE2-02 C2; not dev), staged 0.
- Work order: A1 ACTIVE; BE2-02 PARKED at accepted C2; BE2-01 WAITING_STUDIO.

## What was built (batches A1.1–A1.5; paths under `backend/`)

| Batch | Files (all new) |
|---|---|
| A1.1 domain | `src/sketch2life/domain/assistance.py` |
| A1.2 contracts | `src/sketch2life/contracts/schemas/assistance_requests.py` |
| A1.3 ports/service | `src/sketch2life/application/ports/assistance.py`, `src/sketch2life/application/services/assistance.py` |
| A1.4 fakes/adapters/harness | `src/sketch2life/infrastructure/assistance/{__init__,fakes,adapters,harness}.py` |
| A1.5 fixture HTTP + examples | `src/sketch2life/interfaces/http/routers/assistance_requests.py`, `src/sketch2life/interfaces/http/assistance_requests_fixture_app.py`, `../features/FEAT-049-be2-assistance-orchestration/fixtures/h_ai_review/assistance_handoff_examples.json` |
| Tests | `tests/unit/test_assistance_{domain,service,chain,races}.py`, `tests/contract/test_assistance_{request_contracts,requests_api}.py` |

No existing source or test file was modified (`git diff --name-only -- backend/src backend/tests`
is empty); no `__init__` export was needed. Foundation/Vision behavior is consumed only through
existing ports: the BE2-01 service runs over `CoordinatedAiJobRepository` (decorator) with the
`AssistanceEligibility` decorator; BE2-02 receives BE2-03's `AssistancePinPort`; BE2-03 reads
BE2-02 through `VisionAnalysisOutcomes` with an injected scoped Teacher reader.

Key guarantees exercised through the real service chain (BE2-01 `AiJobService` + BE2-02
`VisionAnalysisService` + BE2-03 `AssistanceService` over their fakes):

- Shared `AssistanceCommitCoordinator`: each foundation write transaction is indivisible from
  hold through commit; assistance state and eligibility epoch publish together; eligibility
  reads state+epoch in one snapshot; lock order coordinator → store; same-thread publication
  inside a foundation unit is refused (`CoordinationError`) and must be requested, then runs
  after that unit exits; failures publish nothing and release the coordinator.
- Frozen schedule identity (`assist:<id>:1:vision`, requester principal, RequestRef), losing-link
  cleanup, target-scan trusted lookup, settlement axis; no resurrection; budget monotonic from
  any attempt's `started_at`; unknown evidence keeps an unconsumed hold.
- Handoff commit is the linearization point; handoff event + `SIMULATED_NO_PRODUCER` Sketch
  intent are written atomically; cancel after handoff is `INVALID_STATE`.
- Cache: supported current reads (`analysis_record` + `downstream_meaning` + exact bindings),
  original provenance in `cache_hit_of`; `record_observation` never called for a terminal job.

## Case → test mapping (plan §11)

| Cases | Test file |
|---|---|
| P01–P04, P06; N01–N11, N13, N14 (pre-handoff), N16, N18–N25; region/D5/admin | `tests/unit/test_assistance_service.py` |
| P05, P07, P08, P09; N14 (post-handoff), N15, N17; R03a, R03b, R04, R06, R07, R12, R13; unknown evidence | `tests/unit/test_assistance_chain.py` |
| R01 (nested + threads), R02, R05, R08a, R08b, R09, R10 (explicit cleanup + fence-only), R11 (both windows), R14, R15a, R15b (same-thread deferral + other-thread blocking), R16 (foundation and assistance commit failures; failed deferred publication); coordination direction guards | `tests/unit/test_assistance_races.py` |
| A1.1 invariants (D2 revision, §9.1 monotonic ledger, §8.3 digest/identity incl. same-revision movement, per-member age/consent, intent bounds) | `tests/unit/test_assistance_domain.py` |
| C01, C02, N12, N18 (contract), pinned handoff examples | `tests/contract/test_assistance_request_contracts.py` |
| C03 fixture API (202/200, replay, 401/400/412/413/415/422/428/429/404) and live-app route absence | `tests/contract/test_assistance_requests_api.py` |

R15a is asserted at the exact seam: first eligibility decision, cancel commit, stale hold,
re-decision, denied start, no `started_at`, no provider request. R15b asserts the start commit
precedes the assistance publication in the coordinator commit log.

## Actual checks (2026-10-17, Windows, existing Python 3.12.10 venv)

Runner (ignored): `../local/a1-implementation-20261017/run_checks.py`, one subprocess per group,
import origin asserted to this worktree's `backend/src`; external network blocked (loopback
allowed for the in-process TestClient); Pillow loaded process-locally from the base interpreter
site-packages and python-multipart from the already present ignored BE2-02 deps directory;
nothing installed; shared venv unchanged; no PostgreSQL/Redis/Studio/provider.

| Group | Files | Tests | Passed | Failed | Errors | Skipped |
|---|---|---|---|---|---|---|
| A1 new | 6 | 101 | 101 | 0 | 0 | 0 |
| BE2-01 regression (`test_ai_job_*` unit + contract) | 11 | 338 | 338 | 0 | 0 | 0 |
| BE2-02 regression (`test_vision_analysis_*`, `test_vision_context_*`, `test_analysis_*`, H-AI-REVIEW examples, context contracts) | 12 | 412 | 412 | 0 | 0 | 0 |

First runner attempt failed 74 tests only because its socket blocker also blocked loopback
(TestClient/asyncio self-pipe); the blocker was narrowed to external hosts and the full run
above is the result. Logs of both runs are in the ignored local folder.

| Static / repository check | Result |
|---|---|
| `ruff check` on 10 source + 6 test paths | PASS |
| `mypy --strict` on the 10 new source files | PASS |
| `mypy --strict --follow-imports=silent` on source + tests | PASS (silent: the live-route test imports the live app, whose unrelated pre-existing modules have mypy errors) |
| `tools/validate_harness.py`, `validate_repository_security.py`, `validate_architecture.py`, `validate_skeleton.py` | all exit 0, VALID |
| `git diff --check`; trailing-space/CR scan of 43 new files | clean |

## Finding fixed during implementation

- **IMPL-F1 (fixed before review):** the first cache gate did not check the BE2-02
  `accepted_status`/`downstream_meaning` state, so a BE2-02-only context move could still reuse
  an analysis. Caught by A1-N17 (`vision_meaning` variant); the gate now requires `accepted` and
  meaning ≠ `not_applicable`. No other test failed for a product reason.

## Routine implementation choices (within the approved plan)

- CMD-32 returns `202` with the request **as committed** (`scheduling`, `job_id` null); the
  scheduler runs after the commit, so receipt replay returns the identical body.
- Role/reason/intent validation (422) precedes scope checks; it reveals no other resource.
- Malformed owner audience (duplicate/mismatch) → 503 `DEPENDENCY_UNAVAILABLE`; audience size
  → 422; disabled policy → 403 with an `assistance.refused` audit event.
- CMD-33: a device on the same canvas but not bound to the individual target gets 403; a
  device elsewhere or a Teacher outside the class gets 404.
- Eligibility denial reasons `CANCELLED_BY_TEACHER`/`CANCELLED_BY_CHILD`/`CONTEXT_CHANGED`/
  `REQUEST_NOT_FOUND`; BE2-01 maps unknown codes to its generic public message.

## Limits and residual gates (not closed by A1)

- Fake protocol only: in-memory stores, one coordinator lock, org-wide coarse eligibility
  epoch (every terminal assistance transition makes other in-flight BE2-01 decisions retry,
  bounded by its decision rounds). No PostgreSQL isolation, real OwnerFence, durable receipts,
  outbox delivery, indexed job lookup or exactly-once provider claim.
- Owner facts, policy values (debounce 5 s, 3 per target, 20 per session) and the consumer
  `AssistancePolicyPort` are FIXTURE_ONLY / proposal to BE2-14; C2 enum mapping deferred (D9).
- Sketch stage is `SIMULATED_NO_PRODUCER`; no generation, moderation, review or Child release.
- Live API/auth, P4 composition (INTG-05), CMD-59 read model, UI and real provider/model remain.
- BE2-01 (WAITING_STUDIO), BE2-02 (IN_PROGRESS) and BE2-03 are not DONE.

Next: Codex code review of A1. Git publication and component acceptance are separate decisions.
