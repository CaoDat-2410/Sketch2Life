# FEAT-083 AI backend port — final report (2026-11-23)

## Scope and plan

Completed the Amendment 3 scope under plan SHA-256 `B1D2AF0BE53DC56927E15F27FE77CDC3EB41A30772A4FF640BB4848F9861CCBB`. The plan file and approval records were not changed. The integration line's Phase A Story and Parent activity contracts remain intact; Qwen3.8/v3 Story changes and ADR-0024 remain deferred.

## Ported files

### Backend implementation and catalog assets

- `backend/alembic/versions/20261113_svg_catalog_review.py`
- `backend/src/sketch2life/application/ports/parent_svg_guide.py`
- `backend/src/sketch2life/application/ports/svg_catalog.py`
- `backend/src/sketch2life/application/services/parent_svg_guide.py`
- `backend/src/sketch2life/application/services/parent_topic_suggestions.py`
- `backend/src/sketch2life/application/services/svg_catalog.py`
- `backend/src/sketch2life/contracts/schemas/parent_topic_suggestions.py`
- `backend/src/sketch2life/contracts/schemas/svg_engine.py`
- `backend/src/sketch2life/domain/svg_engine.py`
- `backend/src/sketch2life/infrastructure/catalog/svg_assets.py`
- `backend/src/sketch2life/infrastructure/persistence/svg_catalog_tables.py`
- `backend/src/sketch2life/infrastructure/svg/{__init__.py,arcadia_gallus_guide.py,openclipart_guide.py,openmoji_guide.py,renderer.py,sanitizer.py}`
- `backend/src/sketch2life/interfaces/http/routers/parent_topic_suggestions.py`
- `backend/src/sketch2life/interfaces/http/routers/svg_catalog.py`
- `backend/src/sketch2life/infrastructure/svg/data/arcadia_organism_strokes/{README.md,arcadia-gallus-source-path-sequence-v7.json,gallus-gallus-source.svg,gallus-gallus-v1.json}`
- `backend/src/sketch2life/infrastructure/svg/data/openclipart/{NOTICE.md,butterfly-color.svg,butterfly-guide.json,butterfly-line.svg,parent-guide-manifest.json,turtle-color.svg,turtle-guide.json,turtle-line.svg}`
- `backend/src/sketch2life/infrastructure/svg/data/openmoji/{ATTRIBUTION.md,CC-BY-SA-4.0-legalcode.txt,black-1F415.svg,black-1F422.svg,black-1F98B.svg,color-1F415.svg,color-1F422.svg,color-1F98B.svg,parent-guide-manifest.json}`
- New backend tests: `backend/tests/contract/test_parent_svg_guide_api.py`, `backend/tests/unit/test_parent_svg_guide_resolution.py`, `backend/tests/unit/test_parent_topic_suggestions.py`, and `backend/tests/unit/test_svg_reference_path_limits.py`.

### Modal additions

- `deployment/modal/srs_v23/story_image_guides.py`
- `deployment/modal/srs_v23/story_visual_plan.py`
- New tests: `deployment/modal/srs_v23/tests/test_parent_topic_subjects_contract.py`, `test_story_image_guides.py`, and `test_story_visual_plan.py`.

## Hand-merged and integration-wiring files

- `deployment/modal/srs_v23/contracts.py`: added the topic workload allowlist while retaining integration contracts.
- `deployment/modal/srs_v23/language_audio_app.py`: added topic validation and worker functions while retaining the existing activity worker.
- `deployment/modal/srs_v23/workloads.json`: added topic workload entries.
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`: added topic registrations to the integration client.
- `backend/alembic/env.py`: included the new migration metadata.
- `.env.example`, `compose.yaml`, and `backend/src/sketch2life/infrastructure/config/settings.py`: wired the approved catalog/guide configuration.
- `backend/src/sketch2life/interfaces/http/openapi_contract.py`, `openapi_srs_v22.py`, `router_composition.py`, and `routers/parent_ai.py`: registered the additive routes, catalog projection, and injected guide builders.

## Files restored to the integration version

These were restored before only the approved additive topic changes were merged back into mixed files:

- `deployment/modal/srs_v23/README.md`
- `deployment/modal/srs_v23/contracts.py` (then topic allowlist additions were merged)
- `deployment/modal/srs_v23/drawing_vlm_app.py`
- `deployment/modal/srs_v23/language_audio_app.py` (then topic functions were merged)
- `deployment/modal/srs_v23/worker_observability.py`
- `deployment/modal/srs_v23/workloads.json` (then topic entries were merged)
- `deployment/modal/srs_v23/video_app.py`
- `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `deployment/modal/srs_v23/tests/test_worker_observability.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py` (then topic registrations were merged)
- `backend/src/sketch2life/contracts/schemas/ai_story.py`
- `backend/tests/unit/test_ai_story_contracts.py`
- `backend/tests/unit/test_modal_story_function_client.py`

`docs/adr/ADR-0024-qwen38-fp8-development-story-candidate.md` and out-of-scope copied Modal tests were removed from this worktree.

## Existing tests edited and assertions changed

Only the following existing tests were edited:

### Sketch-guide route expectations

- `backend/tests/contract/test_app_composition.py::test_compatibility_app_preserves_baseline_route_surface`: include the approved FEAT-083 route paths in the expected route set.
- `backend/tests/unit/test_parent_ai_guard.py::test_every_ai_route_answers_the_404_before_the_provider_gate`: an authorized Parent reaches the curated guide and receives the unknown-guide 404; wrong-role and other provider-gate assertions remain.

### OpenAPI catalog assertions

- `backend/tests/contract/test_openapi_contract_catalog.py::test_swagger_ui_and_openapi_json_are_published`: include the approved projected catalog operations.
- `backend/tests/contract/test_openapi_contract_catalog.py::test_runtime_openapi_matches_all_mounted_rev37_operations_and_records_unmounted_candidates`: update operation/path counts and catalog membership.
- `backend/tests/contract/test_openapi_contract_catalog.py::test_runtime_openapi_operation_ids_are_non_empty_and_unique`: update the expected operation count.

### Migration graph/count assertions

- `backend/tests/unit/test_child_selection_ddl.py::test_the_graph_has_52_revisions_and_fifteen_heads`: expect 52 revisions.
- `backend/tests/unit/test_story_activity_ddl.py::test_one_more_revision_and_the_head_counts_stay_fifteen_and_ten`: expect 52 revisions and the SVG revision as a head.
- `backend/tests/unit/test_story_review_epoch_ddl.py::test_the_revision_is_the_only_child_of_the_story_head_and_precedes_svg_catalog`: expect the SVG revision as the child of the review-epoch revision.
- `backend/tests/unit/test_story_review_epoch_ddl.py::test_one_more_revision_and_the_head_counts_stay_fifteen_and_ten`: expect 52 revisions and the SVG revision as a head.
- `backend/tests/unit/test_story_video_migration.py::test_the_head_counts_stay_fifteen_and_ten`: expect the SVG revision as a head.
- `backend/tests/unit/test_synthetic_eligibility.py::test_head_counts_by_both_methods_match_the_derived_expectation`: expect 52 revisions.
- `backend/tests/unit/test_teacher_run_ddl.py::test_the_revision_is_the_only_child_of_the_story_head`: expect the SVG revision as the child of the review-epoch revision.

## Verification results

- Mypy ran in normal mode and with `--ignore-missing-imports` on 46 changed Python paths. The read-only integration baseline was checked on the 18 same paths that exist there; 28 added paths have no baseline counterpart.
- Normal mypy: 18 baseline findings and 19 worktree findings. The only added finding is the unresolved `cairosvg` import in `deployment/modal/srs_v23/story_image_guides.py`; no new real type errors were found. With `--ignore-missing-imports`, both sides report the same 12 normalized findings.
- Missing optional dependency/import diagnostics in the Modal workload include `cairosvg` (worktree-only), plus baseline-matching `torch`, `transformers`, `vieneu`, `lmformatenforcer`, and `lmformatenforcer.tokenenforcer`. `faster_whisper` is present but has no typing marker/stubs. These findings are environment/dependency noise; no packages were installed.
- A source and AST check found no `cairosvg` import or reference under `backend/src`. The Modal helper imports it inside rendering/probe functions, after module loading; no code change was needed.
- Reviewer-completed backend unit and contract comparison: 85 failing/error node IDs in the integration baseline and 78 in this worktree. Nine cases in `test_vision_v3_quality_benchmark.py` and `test_vision_v3_quality_execution.py` fail only in this worktree because their fixture file does not resolve here; they do not involve changed files. The other differences are baseline-side environment noise. The full suite was not rerun for this closeout.
- Reviewer-reported Ruff result: 17 findings in this worktree versus 21 in the baseline.
- `validate_harness`, `validate_architecture`, and `validate_repository_security` are VALID. Route comparison reports 15 new routes only.
- Focused migration suite: 188 passed. Alembic reports 15 down-only heads and 10 dependency-aware heads. Revision `20261113_svg_catalog_review` has parent `20261123_rv_0001`, extending the current Phase A Story/core chain.
- Modal suite: 115 passed, 2 skipped, and 2 failed because `lmformatenforcer` is unavailable.
- No provider or Firebase calls were made. No tests were rerun for this closeout.

## Limitations and checks not completed

- Online PostgreSQL migration validation was NOT RUN because password-free access to the `frc08` container was unavailable.
- CairoSVG's local module/type availability remains unresolved; this produces the single new normal-mode mypy missing-import diagnostic. The mypy commands themselves ran in both requested modes.
- Modal tests requiring `lmformatenforcer` could not pass locally; the prior Modal run ended with two dependency-related failures.
- The nine vision quality cases remain blocked by worktree fixture resolution as described above.

No files were staged, committed, or pushed.
