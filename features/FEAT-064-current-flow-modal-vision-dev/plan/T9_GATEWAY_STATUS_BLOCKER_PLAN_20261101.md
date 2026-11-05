# T9 — request gateway, cancel and own-status blocker disposition

- Status: **BLOCKED before implementation** for the G4 gateway/status remainder. This does not reopen or invalidate the completed G1 Teacher pilot-profile route.
- Feature: FEAT-064 synthetic-only current-flow pilot.
- Owner authorization: direct instruction to execute G2–G6 in TREO KHÔNG COMMIT mode, under `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E.

## Intended G4 behavior

Request/cancel/status gateway: accept and return a stable request reference promptly; read Child-own status through a separate read guard while paused or after a turn closes; revoke remains deny; Child and Teacher do not retry/resubmit on `NOT_SENT_*`, UNKNOWN, or HOLD. No provider is called in this task.

## Read-only findings and blockers

1. `backend/src/sketch2life/interfaces/http/routers/assistance_requests.py` contains a 0.1-candidate submit/cancel router under `/api/collaboration/v1`; its module docstring states it is fixture composition only and never mounted by the production app. It has no status GET route.
2. `backend/src/sketch2life/contracts/schemas/assistance_requests.py` defines a candidate request/receipt envelope and a minimal Child view, but the gateway request/status integration is not a mounted classroom route. A future UI contract may describe this candidate only as non-live.
3. G3 T6/T7a/T7b/T7c are BLOCKED before implementation. There is no invocation guard, durable request/analysis store, atomic owner fence, or run ledger to back accepted request/status semantics. T8 is consequently BLOCKED as recorded in `plan/T8_GUARDED_WORKER_BLOCKER_PLAN_20261101.md`.
4. T0 manifest O18 lists the Teacher pending-analysis route as `NEW/TBD`; G5 may document a read-only contract draft but cannot make it a runtime route. The G1 Teacher pilot-profile endpoint is unrelated to pending analysis.

## Layer disposition

| Layer | Status | Reason |
|---|---|---|
| L1 contracts/domain | BLOCKED for final gateway/status semantics; candidate CMD-32/CMD-33 types exist. |
| L2 application | BLOCKED by T6/T7/T8; no durable request reference lifecycle. |
| L3 persistence | BLOCKED by T7a. |
| L4 adapter | BLOCKED by T2C/T8; no scoped current-fact gateway. |
| L5 HTTP | BLOCKED; no approved mounted request/status route surface. |
| L6 UI | DEFERRED-BY-OWNER. |
| L7 integration | BLOCKED by T6/T7/T8. |

## Tests, owner questions, and bounded writes

No request/status test was added or run because the authoritative route, guard, and durable lifecycle are absent. Candidate router tests do not prove production mounting or the intended Child-own status guard. This blocker-only disposition permits only this plan, the G4 blocker report, a separate append-only T9 blocker approval entry, and the T9 ledger entry. No route, composition, schema, service, DB, UI, or provider file may change.

Owner questions: resolve T6/T7/T8 dependencies; freeze exact request/cancel/status-own and Teacher-pending route paths, DTOs, authorization/error mapping and status fields; then approve their manifest paths and task plans. Until then T9 gateway/status remains BLOCKED.

