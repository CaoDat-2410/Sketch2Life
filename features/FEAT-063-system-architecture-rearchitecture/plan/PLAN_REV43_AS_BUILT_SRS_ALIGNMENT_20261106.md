# FEAT-063 Plan Rev43 — SRS alignment with the system under construction

- **Plan revision:** 43
- **Date:** 2026-11-06
- **Lifecycle:** REVIEW; documentation changes and scoped verification are complete. Owner authorization is recorded in root and feature approval registers; review evidence is `evidence/EV-063-33_AS_BUILT_SRS_ALIGNMENT_20261106.md`.
- **Change type:** Documentation and source-of-truth alignment only.
- **Canonical SRS:** `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`.

## Goal

Update the canonical SRS and its data-model companion so they show both (a) the intended product/architecture baseline and (b) what is currently present in backend code, the mounted local API, the inspected local database and the observed Modal development deployment. Keep these states distinct so incomplete implementation is not mistaken for a changed product requirement.

## Observed baseline to document

- Local API OpenAPI: 111 paths / 124 operations. Main app includes BE1 runtime, local/demo Parent/session/media/story/video endpoints, renderer endpoints and Lesson Library endpoints. The AI Jobs router is currently only mounted by its fixture app, not the main app.
- Local PostgreSQL: Alembic revision `20261028_ll_0001`; 41 application base tables (34 under `public`, 7 under `lesson`) plus Alembic bookkeeping. This is a local development snapshot, not a production inventory.
- Data Table Register source-derived target: 92 active + 48 legacy/read-only = 140 projected physical mappings. Preserve these as target counts; add the 41-table local snapshot separately.
- Backend code currently contains provider adapters from earlier Lightning-based slices. The Modal dashboard screenshot supplied by the owner shows three live dev apps for language/audio, video candidate, and FLUX image/line-sketch functions. Deployment alone does not prove the main backend is wired to those apps; record the integration gap and distinguish the video candidate from the SRS video target.
- Apply the owner's later direction: Qwen 3.5 VL for current language/vision development, FLUX.3 for line-sketch/lesson visuals, Whisper for Vietnamese speech-to-text, SAM 2 for optional drawing segmentation; keep video generation as a separate, not-yet-verified stage. Do not describe any of these as production-approved or benchmark-passed without evidence.
- Resolve SRS Q159 using the owner's explicit answer: Platform Admin and Teacher can initiate AI lesson/activity suggestion; Parent may edit an authorized draft only.

## Scope and file manifest

1. Update the SRS header/history, current AI model/deployment assumptions, Q159 role answer, and add a dated as-built implementation section.
2. Update the Data Table Register version and append a local database snapshot with exact table names, the distinction between observed and target counts, and the boundary between AI-facing context tables and AI job/policy persistence.
3. Update the canonical-SRS version pointer in `AGENTS.md`, `docs/context/SRS_AUTHORITY.md`, `docs/context/PROJECT_CONTEXT.md`, and `docs/context/SOURCE_REGISTER.md`.
4. Append Rev43 records to FEAT-063 `CONTEXT.md`, `DECISIONS.md`, `SOURCE_REGISTER.md`, `status/STATUS.md`, and `evidence/README.md`.
5. Add `evidence/EV-063-33_AS_BUILT_SRS_ALIGNMENT_20261106.md` with reproducible, non-secret read-only observations, code/API/DB findings, interpretation and limitations.
6. Record this plan's hash-identified owner authorization in root `approvals/TASK_APPROVAL.md` and FEAT-063 `approvals/TASK_APPROVAL.md`.

## Out of scope

- Changing, deleting or weakening any target Parent/Teacher/platform requirement except the already-answered Q159 role clarification and updating AI development model choices explicitly directed by the owner.
- Backend/frontend code, API implementation, database schema/data, migrations, tests, deployments, GPU calls, provider spend, Modal app start/stop, or `.env`/secret changes.
- Signing or representing the SRS as formally approved; the revised SRS remains a draft.
- Deleting, renaming or rewriting preserved historical SRS versions, old feature records, or unrelated dirty files.
- Staging, committing or pushing.

## Acceptance criteria

- **AC1:** The canonical SRS becomes v2.4-draft dated 2026-11-06, remains unsigned, preserves the v2.3 target requirements, and explicitly separates as-built code/API/database/deployment status from target behavior.
- **AC2:** The SRS and companion register report the observed 41 local application tables and current Alembic revision separately from the 92 active / 48 legacy target mapping; the full local table list and the AI/DB access boundary are recorded without claiming unobserved query usage.
- **AC3:** AI documentation reflects the owner's current Qwen 3.5 VL / FLUX.3 / Whisper / optional SAM 2 direction, retains video as a distinct pending verification stage, and does not falsely claim end-to-end Modal integration or production readiness.
- **AC4:** Q159 no longer appears unresolved: Platform Admin and Teacher may initiate AI suggestion; Parent may edit an authorized draft only.
- **AC5:** Canonical source pointers and FEAT-063 tracking/evidence records identify v2.4-draft without rewriting historical records.
- **AC6:** No runtime, API, database, model provider, secret, or unrelated file is changed; no commit/push occurs.
- **AC7:** `git diff --check` and a path-scoped diff review pass; the pre-existing AC-33 user edit and all unrelated staged/dirty changes are preserved.

## Verification

- Reconcile SRS statements against the current router composition and local OpenAPI snapshot.
- Record read-only database query, Alembic revision, count, schema split and table names. Do not write to the database.
- Review owner-supplied Modal dashboard evidence as a deployment observation only; no paid invocation is made.
- Check that old AI model wording is absent from current active model-choice sections while retained historical snapshots remain unchanged.
- Run `git diff --check` and inspect only paths in this plan. No test suite is needed for documentation-only work.

## Risks and handling

- Local DB and dashboard are environment-specific: label dates and environments, and do not claim production deployment.
- Some API handlers call legacy/provider adapters: describe code presence, API exposure and Modal integration as separate facts.
- AI provider/model details may change: pin exact model/revision in deployment config and require separate benchmark/license review before production approval.
- The worktree already contains unrelated staged/unstaged work and prior user edits in some target docs: append or make narrow edits only, never reset/reformat whole files.
