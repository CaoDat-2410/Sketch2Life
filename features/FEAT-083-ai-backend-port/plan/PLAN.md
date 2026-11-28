# FEAT-083 — Port the AI backend pieces of `codex/parent-modal-e2e-20261123` under goal v4 Phase A

- Implementation status: APPROVED_NOT_STARTED
- Owner: Project owner (Person 2, AI Understanding lane); backend co-owned with CaoDat.
- Worktree: `.worktrees/aiport1` (branch `codex/aiport1-backend-ai-20261123`), based on `origin/feature/backend-srs-api-and-fe-integration` at `4b961c27`.
- Source: `origin/codex/parent-modal-e2e-20261123` at `77635688` (CaoDat, 2026-11-23). Check record: `tmp/ai-parent-modal-check/AI_PARENT_MODAL_CHECK_20261123.md` (local, not committed).
- Prepared: 2026-11-23.

## Authority

- Product requirements: only the FEAT-063 canonical working SRS (v2.7-draft) named in `docs/context/SRS_AUTHORITY.md` at the base commit. This plan does not change the SRS, its pinned hashes or any SRS authority pointer. CaoDat's SRS Rev70–Rev73 edits are not ported; their adoption is a separate owner decision.
- Decision (owner, 2026-11-23): **Phase A wins.** The Phase A routes, `story.activity_selections`, migrations `20261123_as_0001` and `20261123_rv_0001`, and the `/v1` contract in `tmp/phase-v4/PHASE_A_FINAL_ROUTE_LIST_20261123.md` stay as they are. The AI part of CaoDat's branch is plugged in beneath them.

## Goal

Bring the AI backend pieces of CaoDat's commit into the integration line without duplicating or breaking Phase A: the Modal workloads and client, the SVG guide engine and catalog, and the Parent topic/drawing-subject suggestions.

## Scope (in order)

1. **Modal workloads** — `deployment/modal/srs_v23/*` (contracts, drawing_vlm_app, language_audio_app, story_image_guides, story_visual_plan, video_app, worker_observability, workloads.json, README, tests) and `docs/adr/ADR-0024-qwen38-fp8-development-story-candidate.md`, as in `77635688`.
2. **Modal client and story contracts** — `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`, `contracts/schemas/ai_story.py`, tests `test_modal_story_function_client.py`, `test_ai_story_contracts.py`. Take wholesale only if the integration line did not change the file since merge base `d40f0514`; otherwise hand-merge. Exclude `modal_silent_story_video.py` and its test.
   - **Amendment 2 (2026-11-23): items 1 and 2 are narrowed to additive changes only.** Take or hand-merge only what adds the new topic-subject workloads, the sketch-guide/SVG guide support, `story_image_guides.py`, `story_visual_plan.py` and the tests of those pieces, plus `video_app.py` only where it leaves every existing contract unchanged. Keep unchanged: the existing Parent activity worker input/output contract and parsing, the existing Story v1 worker input/output and `ai_story.py` v1 behaviour, the existing Qwen model pin for story and activity workloads, and `parent_activity_suggestions.py`. Defer to a follow-up task: the Qwen3.8-FP8 move for story and activity workloads, the v3 story input that requires a primary activity and its hash, the stricter sentence-completeness validation of story drafts, and `docs/adr/ADR-0024-qwen38-fp8-development-story-candidate.md` (the ADR is not adopted here). Where an imported file mixes additive and deferred changes, hand-merge the additive part only and record the split in the evidence notes. Do not invent Phase A activity data to satisfy a deferred contract.
3. **SVG engine and catalog** — `domain/svg_engine.py`, `contracts/schemas/svg_engine.py`, `application/ports/svg_catalog.py`, `application/services/svg_catalog.py`, `application/services/parent_svg_guide.py`, `infrastructure/catalog/svg_assets.py`, `infrastructure/persistence/svg_catalog_tables.py`, `infrastructure/svg/**` with its licence and attribution files, `interfaces/http/routers/svg_catalog.py`, migration `20261113_svg_catalog_review.py`, the metadata line in `alembic/env.py`, and the SVG tests.
   - Fix the layering rule: the application service must not import `infrastructure.*`; add a port and inject the builders from the composition root.
   - Re-parent the migration onto a real current head of our chain (record the choice and reason); it must not touch `ck_story_receipt_operation`. Record the new head count (before: 15 down-only / 10 dependency-aware) and update hard-coded migration-count tests from the real numbers.
   - Register the router and the OpenAPI catalogue entries by hand-merging into our current files.
   - **Amendment 1 (2026-11-23): replace the existing legacy AI route `POST /api/parent/v1/ai/sketch-guides`** (`parent_ai.py`, workload `parent.sketch-guide.generate`) with the catalog-first SVG guide route from the source commit (same path and method; request and response contract change; no AI fallback, an unknown topic returns 404). It is not a Phase A route. Port only this route from `parent_ai.py`; the activity routes and every other `parent_ai.py` change stay out. Mobile consumers (`ParentApi.ts`) are adapted in the follow-up mobile task.
4. **Topic suggestions** — `application/services/parent_topic_suggestions.py`, `contracts/schemas/parent_topic_suggestions.py`, `interfaces/http/routers/parent_topic_suggestions.py`, the settings flag `parent_topic_subject_ai_enabled` (default false), placeholders in `.env.example` and `compose.yaml` (default false), and their tests. Keep the local/test + `modal_dev` + flag gate, the private-text filter and the strict worker-output check; replace the module-level `get_settings()` call with the app-state settings used by neighbouring routers. The route prefix `/api/parent/v1/topics/*` may stay; mobile rewiring is a separate task.

## Out of scope

- Parent activity suggestions/selection (CaoDat tables, routes, migration `20261114_parent_activity_selection`, `parent_ai.py` activity routes; the `sketch-guides` route is the one allowed `parent_ai.py` change, Amendment 1) and his edit to `20261119_frc08_lifecycle_scope`.
- Parent video candidate (route, service, repository, ports, schemas, migration `20261120_parent_video_candidate`, LTX adapter, its settings flag).
- `registrations/complete` and Firebase provisioner/verifier changes.
- `parent_story_repository.py`, `story_run_lite/tables.py`, `outbox.py`, `be1_lifecycle_consumer.py`.
- All `apps/ui-mobile/**`, all `features/**/evidence/**` from the source commit, `.pytest-*` directories and symlinks, SRS and SRS-authority/source-register/data-table-register edits.
- Any change to Phase A routes or tables.

## Constraints

- No real AI provider, Firebase or paid API call; tests use fakes. Tests that need a key or network are skipped and reported.
- No secrets, tokens, model weights, raw child media, absolute local paths, symlinks or `.pytest-*` directories in Git.
- PostgreSQL only as a fresh `frc08_*` database on container `frc08-pg-20261119110418`; never ports 5432/5433, never `sketch2life_m2_s1a`, never read container passwords. If no password-free access exists the PostgreSQL step is reported NOT RUN.
- Do not edit `approvals/TASK_APPROVAL.md` records or any other feature's records. Do not touch `.worktrees/v4` or any other worktree.
- One finished task is one commit. No commit or push unless the owner asks.

## Acceptance criteria

1. `python tools/validate_repository_security.py`, `python tools/validate_architecture.py`, `python tools/validate_harness.py` and `git diff --check` pass in `.worktrees/aiport1`.
2. Backend `tests/unit` + `tests/contract`: no failing node ID that does not also fail on `origin/feature/backend-srs-api-and-fe-integration` (same venv, both runs recorded; known environment failures: missing `imageio`, `lmformatenforcer`).
3. Modal tests under `deployment/modal/srs_v23/tests` pass, except those that need `lmformatenforcer`.
4. `ruff check` and `mypy` on the ported files: no new findings against a baseline run on the integration line.
5. The Alembic chain loads (`alembic heads`) with the new head count recorded; migration-count tests match the real numbers; no change to `ck_story_receipt_operation`.
6. Phase A routes and OpenAPI paths are unchanged. The route diff against the base is limited to the added SVG-catalog and topic routes plus the one replaced legacy route `POST /api/parent/v1/ai/sketch-guides` (Amendment 1).
7. (Amendment 2) The existing Parent activity worker contract tests, the existing Story v1 contract tests and the existing Modal story/activity tests pass unchanged: no test that passes on the integration line may be edited to pass here, except the migration-count tests, the OpenAPI catalogue test for the added routes, and (Amendment 3) the minimal edits to existing tests that assert the behaviour of the one replaced legacy route `POST /api/parent/v1/ai/sketch-guides` (for example the route-surface and provider-gate tests), limited to that route's assertions and listed by name in the evidence notes. Ruff and mypy findings on the changed files do not exceed the integration baseline.
8. The run log under `E:\AI_LOG\CODEX\AIPORT1-backend-ai\` lists ported files, hand-merged files, the chosen migration parent, test numbers, anything NOT RUN, and open questions.

## Follow-ups (not part of this plan)

- AIPORT2: port the new Parent mobile screens onto the current mobile line and rewire to `/v1`.
- AI-generated activity set written into `story.activity_selections` with `source_kind = 'AI_DRAFT'`.
- LTX worker call from the Phase A `video-generations` path.
- Owner decision on SRS Rev70–Rev73 and the pinned hashes.
