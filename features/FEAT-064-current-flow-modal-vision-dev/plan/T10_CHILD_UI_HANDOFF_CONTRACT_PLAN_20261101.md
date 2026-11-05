# T10 — Child UI handoff contract (documentation only)

- Group/task: G5 / T10, FEAT-064 synthetic-only current-flow pilot.
- Status: **contract draft may be completed; runtime/UI integration remains BLOCKED** by T9 and the source/request mismatch recorded below.
- Authority: direct owner instruction in `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6; detailed scope in `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §§B5.2, D-G5, E.

## Objective

Write the Child-side UI handoff contract for flush/ack → preview of the authoritative source → explicit request → actual status. Record request-reference persistence, no automatic resubmit, paused/no-turn behavior, candidate DTOs/errors, and payload limit. The UI remains DEFERRED-BY-OWNER; this task does not implement or test it.

## Read-only contract boundary

- Current candidate POST/cancel endpoints exist only in fixture composition under `/api/collaboration/v1`; the router docstring says it is not mounted by the production app and has no GET status endpoint.
- Current CMD-32 requires `checkpoint_ref`; T4/T5 produce an operation-derived `CanvasRenderHandoffV1` and reject checkpoint/restore history as source. The candidate command cannot bind that handoff. Do not translate the render handoff into a checkpoint or send a request using the candidate route as if it were the pilot API.
- T0 freezes the UI policy: store the request reference and idempotency key; a timeout or denied status read must not cause resubmit; a timer is never success. Status-own reads can occur in active or paused sessions without an active turn; a paused session accepts no new request; revoke/finished/rotated/foreign scopes deny with a generic unavailable result.

## Output and acceptance

Create `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`, with a dedicated T10 section and a synthetic illustrative example explicitly marked non-live. Include known candidate fields, candidate HTTP errors and `32 KiB` body cap; distinguish missing production source-preview/request/status routes and unresolved DTO mapping. Include paused/no-turn and lost-reply behavior.

The contract is accepted for review when it cites source paths, labels candidate versus proposed behavior, contains no live endpoint claim, gives no automatic retry path, and records unresolved questions. No L5 contract test can be run for an unmounted/nonexistent production route; record that test as NOT RUN.

## Exact allowlist

- Create this plan.
- Create `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`.
- Append a T10 documentation-scope entry to `approvals/TASK_APPROVAL.md` pinning this plan hash.
- Append the T10 task result to `status/PILOT_GOAL_LEDGER_20261101.md`.

No UI, backend, route, schema, service, database, migration, provider, test, or composition files are authorized.
