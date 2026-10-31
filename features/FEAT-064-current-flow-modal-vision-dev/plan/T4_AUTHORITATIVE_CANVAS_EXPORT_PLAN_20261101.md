# T4 — authoritative canvas source export

- **Status:** APPROVAL PENDING until the matching append-only entry is recorded below this plan's hash in `approvals/TASK_APPROVAL.md`.
- **Feature:** FEAT-064 — current-flow Modal Vision dev pilot.
- **Group:** G2.
- **Task owner:** Person 2 / AnhKhoaa157.
- **Goal prompt:** `.claude/handoff/CODEX_GOAL_PILOT_T2C_TO_T12_20261101.md`, 2026-11-01; this is an owner-authorized local synthetic pilot task, not a live-provider approval.

## 1. Scope and decision basis

Implement the T4 authoritative source-export primitive from `plan/PLAN.md` and T0 contract freeze. It reads only server-accepted BE1 canvas operations and binds their canonical document and operation manifest to one organization/session/canvas/epoch/revision. The primitive is internal to BE1 for the next T5 artifact path; it does not add an HTTP endpoint or accept client JSON.

The export is fail-closed. It accepts only a server-profiled `CanvasOperationProfileV1` canvas whose persisted operations can be proven complete and ordered in the current epoch. It rejects missing or malformed operations, profile mismatch, revision gaps, mixed epochs, any checkpoint/restore history, empty canvases, and any aggregate state whose full operation history cannot be proven. This intentionally excludes restoring client-supplied checkpoint JSON into a Vision source.

The canonical source ref is derived from the canonical source digest. This task creates no durable artifact, no image, no admission receipt, and no Vision request. T5 owns the private render/artifact/admission handoff.

## 2. Layer matrix and gates

| Layer | T4 work | Gate before the next layer |
|---|---|---|
| L1 contracts/domain | Add strict typed BE1 export and operation-manifest response contracts; reuse the accepted T3 profile validator without changing its semantics. | Unit tests cover schema rejection, canonical serialization, order sensitivity, and stable SHA-256; Ruff and strict mypy on touched files; architecture validator. |
| L2 application | No application service/port change. | Not applicable. |
| L3 persistence/migration | Read the existing aggregate revision, operation rows, and checkpoint-existence fact in one SQL statement; no schema or migration change. | Isolated PostgreSQL test proves exact accepted-operation order and fails closed on unprovable history. No Alembic operation. |
| L4 infrastructure | No new infrastructure adapter. | Not applicable. |
| L5 HTTP/interface | Add an internal export builder in the existing BE1 canvas router module for T5 reuse; no public route, request body, or route-catalog change. Preserve existing authorization guards and all existing endpoint behavior. | Contract/integration tests; verify the exported scope, epoch, revision, and profile are server-derived. |
| L6 UI | DEFERRED-BY-OWNER. | No UI code or visual claim. |
| L7 integration | Add a bounded synthetic PostgreSQL test using the existing pilot fixture. | The test creates and cleans only its own `synthetic-` rows in the approved loopback `*_be1_acceptance` database. |

## 3. Exact allowlist

Product source:

- `backend/src/sketch2life/contracts/schemas/be1_runtime.py`
- `backend/src/sketch2life/interfaces/http/routers/be1_canvas.py`

Tests:

- `backend/tests/unit/test_canvas_source_export.py` (new)
- `backend/tests/integration/test_be1_synthetic_pilot_postgres.py` (add the T4 source-export case to the existing fixture module)

Task records:

- This plan.
- Append-only `features/FEAT-064-current-flow-modal-vision-dev/approvals/TASK_APPROVAL.md`.
- `features/FEAT-064-current-flow-modal-vision-dev/evidence/T4_AUTHORITATIVE_CANVAS_EXPORT_REPORT_20261101.md`.
- `features/FEAT-064-current-flow-modal-vision-dev/status/PILOT_GOAL_LEDGER_20261101.md` (T4 ledger entry only).

No other path is authorized by this task.

## 4. Explicit exclusions

- No new route, app-composition change, OpenAPI catalog change, client input, checkpoint/restore change, or modification of existing BE1 guards.
- No edit to `core_store.py`, `core_models.py`, `be1_models.py`, `be1_runtime.py`, `be1_artifacts.py`, `application/**`, or any migration.
- No render, Pillow use, artifact storage, image admission, Vision/AI job, worker, T6/T7/T8/T9 work, or FEAT-063/Rev36 change.
- No UI, npm, Modal/GPU/provider/network call, real child data, commit, stage, or push.

## 5. Export contract and failure behavior

The typed `CanvasSourceExportV1` contains:

- server-derived organization, session, canvas, profile ID/version, document epoch, and current aggregate revision;
- every accepted operation in strict `resulting_revision` order, with operation ID, participant, epoch, revision, canonical payload, and payload SHA-256;
- a complete operation manifest and its SHA-256;
- a canonical document SHA-256 and a source SHA-256 over the scope/profile/revision/document/manifest binding;
- an immutable source ref derived from the source digest.

Use UTF-8 JSON with `ensure_ascii=False`, sorted keys, and compact separators for canonical hashes. Read aggregate revision, matching operation rows, and checkpoint/restore-history existence from one SQL statement so the exported rows and revision share a PostgreSQL statement snapshot. Require operation revisions to be exactly `2..aggregate_revision`; revision 1 is the empty aggregate baseline. Require each operation to match the requested organization/session/canvas/current epoch and the server-owned profile, and revalidate its stored stroke payload. Do not trust a checkpoint snapshot as an operation source.

Return typed `CANVAS_SOURCE_UNAVAILABLE` (without partial content) when a row is absent or any completeness, profile, epoch, payload, checkpoint, or revision invariant fails. Do not return client-supplied canvas JSON or silently drop rows. The export primitive itself does not claim atomicity with changing eligibility or later AI acceptance; T6/T7 own freshness/fence behavior.

## 6. Test matrix

| Layer | Test | Expected red/green evidence |
|---|---|---|
| L1 | New unit tests for extra fields, invalid hashes, canonical order, digest stability, and scope/revision binding. | Red against missing contract/helper; green after minimal implementation. |
| L5/L7 | Synthetic profile creates a group/turn, appends at least two accepted strokes, exports them in revision order, and verifies every hash/ref from the returned canonical content. | Red before implementation; green on isolated PostgreSQL. |
| L5/L7 | Mutate only this fixture's history to produce a revision gap, mixed epoch, invalid profile payload, or checkpoint marker. | Each case returns the same fail-closed source-unavailable outcome with no partial export. |
| Regression | Existing G1 CPU/offline and PostgreSQL synthetic-pilot baselines. | No new failure relative to the recorded G1R baseline; all results reported literally. |

Every new test uses synthetic identifiers/data and blocks non-loopback sockets. Every Settings construction uses `_env_file=None`. PostgreSQL is restricted to the owner-approved disposable local `*_be1_acceptance` database; no DROP/TRUNCATE or cleanup beyond rows created by the test fixture. No migration runs in T4.

## 7. Risks and not-yet-claimed behavior

- Rejecting any checkpoint/restore history is conservative and may exclude canvases even when a checkpoint has a valid server-side checksum; supporting a checkpoint as a render source requires a separate contract and evidence.
- A single-statement database snapshot prevents mixing rows from different committed revisions, but it does not freeze eligibility, session state, or later acceptance. T5 must call the current guard, and T6/T7 must pin freshness before any provider work.
- The helper is internal and is not a client API. T5 must own the route/DTO, private artifact, render receipt, and admission contract.
- No visual parity, production readiness, provider call, or READY_FOR_T13 claim is made by T4.

## 8. Acceptance

T4 is `XONG-CHƯA REVIEW` only when the exact allowlist is respected; test-first red counts and final green counts are recorded; the canonical export rejects every unprovable input without partial output; the current G1R baseline does not regress; Ruff, strict mypy (zero new errors), all three repository validators, `git diff --check`, PostgreSQL synthetic test, and local protected-file hashes are reported from actual commands; and the evidence report and ledger contain plan/report/source/test hashes. Independent review is still required.
