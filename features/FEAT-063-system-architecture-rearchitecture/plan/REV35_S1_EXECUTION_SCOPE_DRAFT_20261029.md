# Rev35 S1 execution scope — draft

- Status: DRAFT
- Implementation status: NOT_STARTED
- Date: 2026-10-29, Asia/Saigon.
- Working branch: `feature/feat063-be-foundation`, baseline `4f07124289ec5ba283675dd4704649ce5e20a108`.
- Parent plan: `PLAN_REV35_BACKEND_SRS23_ALIGNMENT_20261029.md`, SHA-256 `D181BF43BDDABE3262AEFF990EC54F4CF69EAD92E5FEB774C634C80FD952F4BC`, awaiting implementation approval. Earlier plan and S1 inventory are retained for provenance. Rev35 governs in any conflict; approval must pin the final inventory hash and operation dispositions.

## Purpose and authority

The owner selected SRS2.3 and instructed continuing on the current merged branch. The branch contains the Modal configuration and CI repair; that history does not implement S1. Prepare S1 first, without changing runtime source until the exact subset and decisions below are approved. Earlier approvals remain unchanged.

## Proposed first slice

Add `classroom_writes_enabled` and `demo_flow_enabled`, both default true. Default route surface/behavior remains unchanged. Only an explicitly disabled flag changes behavior; do not change shared environment settings, frontend, database or provider configuration.

- Disabled classroom writes: approved collaboration commands return proposed HTTP410 with `FEATURE_RETIRED` in the existing Be1Error envelope, including request ID. Error choice remains owner decision Rev35 OD-2.
- Disabled demo flow: combined app omits `mount_demo_routers` contributions. Standalone demo profile remains unchanged. Registry, Lesson Library and health are preserved.
- Read preservation means the new fence does not block the route; existing authentication, scope, validation and dependency availability still apply. Do not promise HTTP200 for all reads or add HEAD/OPTIONS support implicitly.

## Runtime/test paths proposed for approval

| Path | Intended change |
| --- | --- |
| `backend/src/sketch2life/infrastructure/config/settings.py` | Two backward-compatible flags |
| `backend/src/sketch2life/interfaces/http/app.py` | Wire per-app settings/fence and combined-profile selection, preserve error envelope |
| `backend/src/sketch2life/interfaces/http/router_composition.py` | Opt-in omission of combined demo group |
| `backend/src/sketch2life/interfaces/http/routers/be1_runtime.py` | Scoped fence wiring if router dependencies are selected |
| `backend/src/sketch2life/interfaces/http/routers/be1_common.py` | Document410 for retired feature as well as unavailable artifact |
| `backend/tests/contract/test_legacy_flow_fences.py` (new) | Exact operation classification and flag/error/composition matrix |
| `backend/tests/contract/test_app_composition.py`, `backend/tests/unit/test_settings_security.py` | Default compatibility and environment parsing regressions as necessary |

Choose/freeze middleware versus router dependency before code; do not modify both indiscriminately. Tests may use injected infrastructure doubles only; no DB, Docker, running server, package installation or provider call. S2/S3, migrations, Parent profiles and AI job target changes remain outside this first slice.

## Static operation inventory for owner disposition

All locators below are relative to `backend/src/sketch2life/interfaces/http/routers/` at the pinned baseline. Prefixes:

- `B=/api/be1/v1`; `O=B/organizations/{organization_id}`; `S=O/sessions/{session_id}`.
- `G=S/groups/{group_id}`; `M=S/memberships/{membership_id}`; `C=O/classes/{class_id}`; `L=O/gallery/{gallery_id}`.

| Method | Path | Locator |
| --- | --- | --- |
| POST | O/sessions | be1_sessions.py:187 |
| POST | S/learning-stage/advance | be1_sessions.py:467 |
| POST | S/lobby | be1_sessions.py:872 |
| POST | S/start | be1_sessions.py:883 |
| POST | S/pause | be1_sessions.py:894 |
| POST | S/resume | be1_sessions.py:905 |
| POST | S/finish | be1_sessions.py:916 |
| POST | S/completion | be1_sessions.py:927 |
| POST | S/join | be1_sessions.py:1051 |
| POST | S/room-code/rotate | be1_sessions.py:1125 |
| POST | B/room-code/join | be1_sessions.py:1186 |
| POST | S/join-requests/{grant_id}/admit | be1_sessions.py:1270 |
| POST | S/join-requests/{grant_id}/revoke | be1_sessions.py:1383 |
| POST | S/device-grants/{grant_id}/refresh | be1_sessions.py:1443 |
| POST | S/groups | be1_sessions.py:1499 |
| PUT | G/members/{child_id} | be1_sessions.py:1550 |
| POST | G/control | be1_sessions.py:1651 |
| POST | M/progress | be1_sessions.py:1724 |
| POST | M/help | be1_sessions.py:1790 |
| POST | M/leave | be1_sessions.py:1851 |
| POST | G/turns/{child_id} | be1_sessions.py:1908 |
| POST | S/canvas/operations | be1_canvas.py:99 |
| POST | G/checkpoints | be1_canvas.py:267 |
| POST | G/restore | be1_canvas.py:448 |
| POST | S/artifacts | be1_artifacts.py:77 |
| POST | O/gallery | be1_records.py:81 |
| POST | L/publish | be1_records.py:197 |
| POST | L/annotations | be1_records.py:249 |
| POST | C/observations | be1_records.py:320 |

These 29 entries are candidates, not an approved denylist. `create_observation` is session-bound despite its class-level path. Review cleanup/security commands separately: finish, completion, grant revoke, membership leave and room-code rotation must have explicit owner disposition. Pre-cutover handling must not imply legacy writes remain allowed after the SRS read-only cutover; test active session/grant transitions and coordinate frontend migration and rollback.

Recommended preserved operations pending owner confirmation:

- POST `B/device-grants/{grant_id}/join-status` (`be1_sessions.py:1221`) is a semantic read despite POST; preserve polling with its current device checks.
- POST `O/data-requests` (`be1_records.py:431`) is a data lifecycle/privacy operation; preserve it rather than treating it as classroom collaboration.
- All six registry writes remain exempt: create/revoke assignment, create class/profile, record/revoke consent. They are not a way to bypass collaboration command fences.

Static counts: sessions27routes/22non-GET; canvas6/3; artifacts2/1; records8/5; registry11/6. Total54 module declarations plus two health declarations =56 classroom-profile declarations. There are37non-GET declarations: six registry exemptions, two operations needing the preserved disposition above and29remaining candidates. These are source counts, not requests executed against a runtime.

## Acceptance and verification proposed

1. Flags default true: existing route and behavior regressions pass, no environment or frontend changes.
2. For each owner-approved fenced operation, flag off returns410/FEATURE_RETIRED with existing request-id shape and no command side effects; no required DB/provider call for this test.
3. Exempt/read operations retain their current auth/scope contracts and are not globally retired by method or prefix alone; unknown routes retain existing behavior.
4. Combined/demo/classroom profile matrix confirms only the intended demo contributions disappear, while standalone demo and health behavior are preserved.
5. Focused tests, lint and repository checks pass; report actual results. No source implementation or runtime tests have run in this preparation step.

## Before implementation

Owner records the approved S1 subset, exact operation dispositions, error/default decisions and this scope hash together with the parent Rev35 hash. SRS section 12.3 migration, mapping, reconciliation and read-only gates apply before any real cutover; a local flag test alone is not cutover. No S2/S3 or Modal authorization is inferred. Git publication is not inferred from the earlier CI-only publication request.
