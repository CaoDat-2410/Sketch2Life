# Runtime Integration Sprint context

- Status: REVIEW
- Primary owner: integration allocation pending
- Goal: connect the four Sprint 1 workstreams through an application-owned runtime flow after FEAT-015 offline evidence.
- Scope: application/session state, HTTP/job contracts, artifact access, Android bridge wiring, and fixture-only E2E as approved in a later allocation.
- Non-goals: live provider rollout, production release, real child data, and production visual assets until separately approved.
- Dependencies: FEAT-015 revision-2 offline integration; P1 `ACT-0004` / `OBJ_MOVEMENT_COORDINATION` canonical identity; P2/P3/P4 standalone contracts; ADR-0006.
- Risks: contract drift, stale job completion, provider failure, asset provenance loss, and assigning integration work without balanced capacity review.

## Current baseline

FEAT-015 revision 2 has a synthetic package and an offline in-memory flow. It covers P2 fusion, Gate A/B, P1 filtering, P3 whole-drawing asset validation, P4 cache/fallback/block and eight scenario outcomes. It does not implement a production application state machine, API, queue, storage, Android flow or live provider.

## Review gate

Plan revision 1 and the proposed allocation are recorded as APPROVED in approvals/TASK_APPROVAL.md. The implementation remains bounded to fixture-only runtime and UI evidence; live provider, production API, Android release, cloud infrastructure and real data require a new approval.

## Implementation update — 2026-09-05

The first fixture-only runtime slice is implemented: application-owned session state, versioned local transport, local job semantics, Gate A/B, P1 identity locking, stale-version handling and idempotency. Seven tests pass. Device lifecycle evidence remains environment-limited; live provider, production API and cloud work remain excluded.

## Review update — 2026-09-05

Deep review passed after fixing replay rollback semantics and adding contract validation. FEAT-015/016 regression is 32 passed; Ruff, compileall, harness, architecture and security checks pass. The remaining evidence limitation is device lifecycle screenshots/APK execution.

## UI harness review update — 2026-09-05

The approved fixture-only client slice is now implemented. `AppRoot` renders a deliberate React Native fixture screen that carries one synthetic session through capture, deterministic P2 proposal, Gate A, P1/Gate B, renderer preview, P4 cache/fallback, activity handoff and feedback. The framework-free reducer and renderer lifecycle tests cover happy path, fallback handoff, duplicate commands and duplicate/out-of-order bridge events. Mobile Jest (6 tests), typecheck, lint, the FEAT-015/016 Python regression (32 tests), harness, architecture and security checks pass. Android device lifecycle screenshots/APK build and live AI remain separate follow-up work.



