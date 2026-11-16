# G4 — canvas facts, guarded worker and request/status blockers

- Group: G4, FEAT-064 synthetic-only current-flow pilot.
- Status: **XONG-CHƯA REVIEW as a blocker disposition**; T2C, T8, and the G4 remainder of T9 are **BLOCKED before implementation**.
- Scope: read-only contract/source inspection and blocker records only. No source, test, schema, migration, route, database, UI, or provider implementation was performed.
- Owner authorization: `.claude/handoff/CODEX_GOAL_RUN_PROMPT_20261101.md`, scope G2-G6, with the task-level authority recorded in `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md` §E. OwnerFenceV1 co-signatures remain unsigned; the owner’s §E.3 instruction means their absence is not itself used as a blocker.

## T2C — BE1 canvas, roster and current-turn facts

- Plan: `plan/T2C_BE1_CANVAS_OWNER_FACT_ADAPTER_PLAN_20261101.md`; SHA-256 `8E7EACF0C1E8C205A5FBB2FA49F60165A4271F55861A8F5475D5A1CA758064DF`.
- Approval: append-only T2C blocker-disposition entry in `approvals/TASK_APPROVAL.md`, pinning that hash.
- Findings: the existing owner port separates `canvas`, `roster`, `members`, and `current_turn`; its `members` call lacks session, class, and purpose-reference scope required by the T2B request. The current BE1 fact source is a protocol, not a PostgreSQL adapter. No single revision/snapshot token binds the separate reads. Mapping `purpose_code` to a BE1 `purpose_ref`, or selecting a session from a child identifier, would infer authority that the contract does not supply.
- Layer matrix: L1 existing contract XONG-CHƯA REVIEW; L2 current port shape XONG-CHƯA REVIEW but insufficient for scoped T2C; L3 NOT DONE; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED pending scoped source and T7b fence.
- Tests/PG: NOT RUN; implementation did not start, so there is no red count.
- Owner question: choose a session-scoped facts request that binds organization/class/session/canvas/group/audience/purpose and one BE1 snapshot, with paths and writer; or name the already-authoritative source and exact call-scoping rule. Also identify authoritative age-policy and region-policy revision sources.

## T8 — guarded worker

- Plan: `plan/T8_GUARDED_WORKER_BLOCKER_PLAN_20261101.md`; SHA-256 `7F3781DDA34BB22C7DBF55939085A575544FCB3DACD9C6C980268CDFA26DCF0E`.
- Approval: append-only T8 blocker-disposition entry in `approvals/TASK_APPROVAL.md`, pinning that hash.
- Disposition: BLOCKED by T6’s unresolved deadline/late-response/transport identity; T7a’s unresolved durable schema/method subset; T7b’s missing BE1-owned atomic fence/UoW; and T2C’s unscoped facts source. Without these boundaries, wiring a worker could bypass the approved invocation guard or produce an attempt from UNKNOWN/HOLD.
- Layer matrix: L1-L2 BLOCKED; L3 BLOCKED; L4 BLOCKED; L5 NOT RUN; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Tests/PG: NOT RUN; implementation did not start, so there is no red count. No provider call occurred.
- Owner questions: resolve T6 deadline, completion margin, cold-start and late response; freeze T7a’s schema owner/path/revision/method subset; define the BE1-owned T7b acceptance fence/UoW; resolve T2C scope. Then approve a new implementation plan.

## T9 — gateway, cancel, Child-own status remainder

- Plan: `plan/T9_GATEWAY_STATUS_BLOCKER_PLAN_20261101.md`; SHA-256 `50C39BA327F26103A822D8706E59046935FEE8EA0EB91D9A91806612A0998BBA`.
- Approval: append-only T9 blocker-disposition entry in `approvals/TASK_APPROVAL.md`, pinning that hash. The completed G1 Teacher pilot-profile route is unchanged.
- Findings: `routers/assistance_requests.py` documents a fixture-composition-only candidate submit/cancel router and has no status GET. Its presence does not establish a production-mounted request/status surface. T0 O18 still lists the Teacher pending route as NEW/TBD. Candidate DTOs are not treated as an approved live contract.
- Layer matrix: L1-L2 BLOCKED for final lifecycle semantics; L3 BLOCKED by T7a; L4 BLOCKED by T2C/T8; L5 BLOCKED; L6 DEFERRED-BY-OWNER; L7 BLOCKED.
- Tests/PG: NOT RUN; no production route contract was approved or implemented.
- Owner questions: resolve T6/T7/T8 dependencies; freeze exact request/cancel/Child-own-status and Teacher-pending paths, DTOs, fields, authorization/error mapping, and status lifecycle; approve the required route paths and plans.

## G4 verification and boundaries

| Check | Result |
|---|---|
| T2C/T8/T9 implementation tests | NOT RUN; each task stopped before implementation |
| PostgreSQL/Alembic | NOT RUN |
| Ruff/mypy | NOT RUN; no implementation Python files changed |
| Modal/GPU/provider/network | NOT RUN |
| UI/visual AC20 | DEFERRED-BY-OWNER / NOT RUN |
| `git diff --check` | clean |
| `python tools/validate_harness.py` | `HARNESS_VALID` |
| `python tools/validate_repository_security.py` | `REPOSITORY_SECURITY_VALID` (`6,029` publishable files scanned) |
| `python tools/validate_architecture.py` | `ARCHITECTURE_VALID` |
| New-file encoding/whitespace scan | UTF-8, LF, no BOM, no trailing whitespace: `4/4` |

No T2C facts, revisions, request route, or Teacher-pending route were synthesized. No co-owner signature is claimed. No stage, commit, or push occurred.
