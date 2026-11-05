# T11 — Teacher pending-analysis UI contract (documentation only)

- Group/task: G5 / T11, FEAT-064 synthetic-only current-flow pilot.
- Status: **read-only UI contract draft may be completed; route/DTO integration remains BLOCKED** because T9 and manifest O18 leave the Teacher pending route `NEW/TBD`.
- Authority: direct owner instruction in `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6; detailed scope in `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §§B5.2, D-G5, E.

## Objective

Document the future Teacher pending-analysis panel as a separate, read-only surface. It must not reuse the existing Sketch approval/correction behavior, imply Teacher approval, or expose internal consent, age, budget, provider, or raw analysis fields by default. The Teacher UI remains DEFERRED-BY-OWNER; this task does not implement or test it.

## Read-only contract boundary

- T0 requires verified Teacher identity, current assignment to the organization/class/session, exact request scope, and current disclosure/eligibility. The projection is pending/unconfirmed and disappears when authority is lost.
- T0 manifest O18 says the new Teacher pending panel/read route is `NEW/TBD`; no production endpoint or final DTO may be claimed.
- Existing `AssistanceRequestRecordV1` is a candidate internal/Teacher record with fields including age/consent references, intent, targets, budget, and policy metadata. It is not an approved UI projection. Existing `AiSuggestionReviewPage` concerns Sketch review and must retain its meaning.

## Output and acceptance

Create `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`, with a separate T11 section describing caller authorization, read-only meaning, minimum data that still needs owner approval, generic unavailable behavior, session pause/no-turn read semantics, and a conceptual synthetic example explicitly marked non-wire/non-live. State that exact route, DTO, cursor/pagination, error mapping, and display fields require owner freeze under O18/T9.

No L5 contract test can be run for an unassigned route; mark it NOT RUN. The draft is accepted for review only if it stays separate from Sketch approval, marks every proposed field as unapproved, and avoids claims of production availability.

## Exact allowlist

- Create this plan.
- Create `evidence/T10_T11_UI_HANDOFF_CONTRACT_DRAFT_20261101.md`.
- Append a T11 documentation-scope entry to `approvals/TASK_APPROVAL.md` pinning this plan hash.
- Append the T11 task result to `status/PILOT_GOAL_LEDGER_20261101.md`.

No UI, backend, route, schema, service, database, migration, provider, test, or composition files are authorized.
