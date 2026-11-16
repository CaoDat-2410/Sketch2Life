# T2C — BE1 canvas, roster and current-turn adapter disposition

- Status: **BLOCKED before implementation**; this plan records the boundary and owner question only.
- Feature: FEAT-064 synthetic-only current-flow pilot.
- Parent scope: `plan/PLAN.md`, G4; goal prompt `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §§B4–B5, D-G4, E.
- Owner authorization: direct owner instruction to run G2–G6 in TREO KHÔNG COMMIT mode authorizes an append-only blocker disposition; it does not authorize widening the application-port boundary.

## Goal and bounded scope

T2C is intended to adapt BE1 `CanvasFacts`, `GroupRoster`, and `current_turn` to existing BE2 assistance owner facts, using the same canonical digest helper as T2B. The pilot audience remains exactly one participant and provider context remains `IMAGE_ONLY`. No Child/Teacher UI, provider, public route, migration, request gateway, or lifecycle persistence is in this task.

## Read-only findings

1. `backend/src/sketch2life/application/ports/assistance.py:141-175` defines `CanvasFacts`, `GroupRoster`, and `AssistanceOwnerPort`. Its independent calls are `canvas(organization_id, canvas_id)`, `roster(session_id, group_id)`, `members(organization_id, participant_ids, purpose_code)`, and `current_turn(canvas_id)`.
2. `backend/src/sketch2life/infrastructure/assistance/be1_fact_reader.py:71-92` defines a T2B request that requires `organization_id`, `class_id`, `session_id`, `child_id`, `purpose_ref`, a one-member audience, and `IMAGE_ONLY`; the source is only a protocol at lines 89-92.
3. `plan/T2B_REWORK_TO_OWNER_RECORD_PLAN_20261101.md` §5 explicitly excluded a PostgreSQL `BE1FactSource` implementation and T2C from T2B. `evidence/OWNER_DECISIONS_T2B_T3_20261101.md` records A4/A5 as deferred and A6 as T2B limited to `MemberFact` and `ContextDecision`.
4. The BE2 member-fact call has no `session_id`, `class_id`, or `purpose_ref` parameter. Resolving those from a child across sessions or equating the BE2 `purpose_code` with a BE1 `purpose_ref` would be an unsupported scope/purpose inference. Separate calls also provide no cross-call snapshot token; T7b's owner-fence boundary is BLOCKED.
5. B5.1 permits new adapter files under `backend/src/sketch2life/infrastructure/assistance/**`, but does not permit changing `application/ports/assistance.py` or adding runtime composition. Therefore a concrete, usable BE1→BE2 owner adapter cannot be completed within this task's authorized paths while preserving the T2B scoped-fact contract.

## Layer disposition

| Layer | Status | Evidence / reason |
|---|---|---|
| L1 contracts/domain | XONG-CHƯA REVIEW | Existing BE2 types are present; no contract change is authorized here. |
| L2 application | XONG-CHƯA REVIEW | Existing consumers require the current port; no edit is in scope. |
| L3 persistence | NOT DONE | BE1 rows exist, but the T2B scoped PostgreSQL fact source is explicitly absent; no persistence read path is authorized by this plan. |
| L4 adapter | BLOCKED | Current port call shape cannot bind the T2B session/purpose scope or prove a shared read boundary without a new contract/path. |
| L5 HTTP | NOT RUN | No route change. |
| L6 UI | DEFERRED-BY-OWNER | No UI code in this run. |
| L7 integration | BLOCKED | Depends on a scoped source/adapter and the later T7b fence for atomic acceptance. |

## Test and validation scope

No test was added or run: implementation is stopped before an adapter contract can be specified without guessing or widening the allowlist. There is no trustworthy red-test count; report `NOT RUN`, not a fabricated red/green result. If the owner resolves the question below, create a new task plan and tests before code.

## Owner question

Approve one of these concrete boundaries: (A) add a session-scoped owner-facts request/port that carries organization, class, session, canvas/group, audience, purpose reference, and one consistent BE1 snapshot, with its exact file paths and writer; or (B) specify an existing authoritative source and call-scoping rule that supplies those same fields without changing the port. Also identify the authoritative age-policy reference and region-policy revision source for `CanvasFacts`. Until then, T2C is BLOCKED and no facts are synthesized from child/session identifiers or policy literals.

## Allowlist and exclusions

This blocker disposition writes only this plan, the G4 blocker report, one append-only T2C approval entry, and the T2C ledger entry. No source, tests, application port, composition, migration, DB, route, UI, provider, network, or other task file is authorized by this plan.

