# Current system audit — 2026-09-29

## Scope and sources

- User-provided five screenshots in the current request; inspected in conversation, not copied into the repository.
- `features/FEAT-029-master-srs/artifacts/Sketch2Life_Master_SRS.md` business rules BR-001, BR-009–014, BR-023; B7 entities/relationships; B21 mobile profile/recommendation screens.
- `apps/ui-mobile/src/screens/Flow1Screens.tsx`, `apps/ui-mobile/src/screens/Flow2Screens.tsx`, `apps/ui-mobile/src/context/AppContext.tsx`, and `apps/ui-mobile/src/demo/api.ts`.
- `backend/src/sketch2life/contracts/schemas/child_learning_profile.py` and `backend/src/sketch2life/interfaces/http/routers/supervised_flow.py`.
- `features/FEAT-022-catalog-coverage-expansion/CONTEXT.md`, status and catalog audit script.

## Reproducible observations

1. Backend log from the already-running local service:
   - `POST /v1/sessions` → 201.
   - `POST .../media/image` → 200.
   - `POST .../understanding` → 200.
   - `POST .../gate-a/confirm` → 200.
   - `POST .../p1/context-options` → 422 (three attempts).
   This localizes the observed failure to request validation at the profile-aware P1 options boundary, not to general backend reachability. The server log does not include request body or a sanitized validation issue path; the offending field is therefore **not yet identified**.
2. `apps/ui-mobile/src/demo/api.ts::toError` handles the project's `failure` envelope only. When a FastAPI 422 body has the default `detail` form, it returns `INVALID_RESPONSE` with “Backend returned an unreadable response.” This explains the screenshot's generic modal, but not the underlying rejected field.
3. The current profile schema restricts interest/dislike values to uppercase bounded identifiers, progress to hard-coded `ACT-*`/`OBJ_*` pairs, supervision to `NONE|NEARBY|DIRECT`, and readiness/materials to IDs. The mobile form shows the fixed interest chips, three hard-coded progress examples, all 20 readiness items, and a material search capped at 10 visible matches.
4. Current workflow passes profile progress as completed activity IDs and sets the P1 supervision level to the selected candidate's minimum. This is not the same as confirmation that an adult is participating or available to supervise that concrete activity.
5. Read-only service checks at audit time: `GET http://127.0.0.1:8000/health` → 200 (`status: ok`); `GET http://127.0.0.1:8081/status` → 200 (`packager-status:running`).
6. Android check: `D:\AndroidStudio\platform-tools\adb.exe` returned “no devices/emulators found.” No current frame-time, interaction-latency, or emulator error-log measurement was possible.
7. Read-only catalog report: `backend\.venv\Scripts\python.exe backend/tools/audit_child_profile_catalog.py` with `PYTHONPATH=backend/src;.` → 300 profiles, 94 concepts, 20 objectives, readiness on 100/300 templates, materials and supervision on 300/300, 40 material registry options, 14 templates with prerequisite activity IDs, and no historical child progress records in the catalog. FEAT-022 selectable-count target is already reached; production qualification remains distinct from count/review eligibility.
8. Existing worktree had unrelated modified/untracked FEAT-029, FEAT-018/020/030 notes/plans, pytest temp folders, `runtime-output/`, and FEAT-031 work before FEAT-033 was created. They were preserved and not modified by this audit.

## Interpretation

- The API/UI error wording is a confirmed client error-mapping bug; the profile-aware P1 request rejection is confirmed, while its exact Pydantic/header cause is still unknown.
- Backend and Metro being reachable does not prove the flow contract is healthy.
- The supplied form currently exposes internal catalog IDs as broad chip lists, and static progress examples can imply history that does not exist.
- The SRS's supervision and readiness requirements must remain hard rules even as their UI input is redesigned.
- Existing evidence does not establish emulator lag as an app defect. It establishes that the profile screen has a large static selection surface; performance must be measured on a connected device before/after.

## Commands/checks

- Read-only backend/Metro health probes described above.
- Read-only catalog audit command described above.
- ADB availability/resumed-activity/log probe attempted; no device was attached, so device-specific checks could not run.
