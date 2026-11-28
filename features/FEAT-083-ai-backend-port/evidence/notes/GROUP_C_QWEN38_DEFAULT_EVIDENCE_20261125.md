# Group C Qwen3.8 default evidence — 2026-11-25

## Workload changes

All eight switched workloads keep their registry entries disabled and now identify Qwen3.8-27B-FP8 as the default candidate, with the previous Qwen3.5-9B pin recorded as the code fallback.

| Workload | Default | Fallback |
| --- | --- | --- |
| `story.generate` | Activity-bound v4 backend adapter dispatches to the separate Qwen3.8 story worker. | The existing v1 Qwen3.5 worker remains selectable; v3 and rewrite-v2 inputs are projected to its exact v1 payload. |
| `storyboard.generate` | Uses the Qwen3.8 story worker, which returns story and storyboard together. | Uses the Qwen3.5 v1 story profile. |
| `parent.activity.suggest` | Shared text model pins and worker identity checks select Qwen3.8; admission is in L4. | Shared text pins restore Qwen3.5. |
| `teacher.sketch-deck.generate` | Shared text model pins and worker identity checks select Qwen3.8. | Shared text pins restore Qwen3.5. |
| `lesson.plan.suggest` | Shared text model pins and worker identity checks select Qwen3.8. | Shared text pins restore Qwen3.5. |
| `parent.topic-subjects.suggest` | Shared text model pins and worker identity checks select Qwen3.8. | Shared text pins restore Qwen3.5. |
| `parent.topic-subjects.validate` | Shared text model pins and worker identity checks select Qwen3.8. | Shared text pins restore Qwen3.5. |
| `drawing.analyze` | The drawing worker uses Qwen3.8 model pins and the existing multimodal loader. | The Qwen3.5 model pins, directory, and bfloat16 loader path remain selectable. |

## Settings and pins

- `SKETCH2LIFE_STORY_GENERATION_PROFILE` defaults to `v4_qwen38`; select `v1_qwen35` for the story fallback.
- `SKETCH2LIFE_MODAL_QWEN_PROFILE` defaults to `qwen38`; select `qwen35` for the shared text and drawing fallback. Set both fallback values to roll back all switched groups.
- Backend story model constants and StoryRun-lite reservation metadata follow the story profile: Qwen3.8 by default and the legacy Qwen3.5 pins under `v1_qwen35`.
- The owner-confirmed Qwen3.8 model revision is `c3a462cc3d38cf351f3b26cbd763469eeb74ef81`, stored under `MODEL_MOUNT/qwen3_8_27b_fp8/<revision>`.
- Code marks the revision as owner-confirmed on 2026-11-25 from the Modal volume listing. The FP8 kernel commit remains the named placeholder `QWEN38_FP8_KERNEL_COMMIT="unpinned"`. The Qwen3.8 story checkpoint manifest digest is also still `unpinned`. Startup succeeds with these defaults; default-false dispatch fails closed before a provider call until required pins are configured. The local/test-only `qwen38_allow_unpinned_dev` exception is documented below.
- The Qwen3.8 drawing loader uses `AutoProcessor` and `AutoModelForMultimodalLM`, as the existing worker does. Compatibility with the Qwen3.8 vision artifacts was NOT VERIFIED offline.

## Unpinned dev setting

`SKETCH2LIFE_QWEN38_ALLOW_UNPINNED_DEV` maps to the named setting `qwen38_allow_unpinned_dev` and defaults to `false` in Settings, `.env.example`, and Compose. `true` is refused outside `env=local` or `env=test`. With the setting off, the existing backend and worker guards fail closed before dispatch when either required pin is a placeholder. With it on, a placeholder kernel commit or story manifest sha256 may pass the dispatch gate; the backend passes the setting to the worker as `qwen38_allow_unpinned_dev` in the Modal worker input. The language/audio worker then calls `get_kernel("kernels-community/finegrained-fp8", trust_remote_code=["kernels-community/finegrained-fp8"], user_agent={"component": "sketch2life-fp8-bootstrap"})` without a `revision` argument, and skips checkpoint manifest digest equality only while the manifest pin is a placeholder. Valid 40-hex and 64-hex pins remain checked, and malformed non-placeholder values fail closed. Worker diagnostics report `pins: "unpinned-dev"` with the required warning when this path is active.

### Before production

Fill the Qwen3.8 FP8 kernel repo commit hash (40 hex) and the checkpoint manifest sha256 of qwen3_8_27b_fp8/c3a462cc3d38cf351f3b26cbd763469eeb74ef81, then turn the dev setting qwen38_allow_unpinned_dev off.

## Files changed in this scope

- `.env.example`, `compose.yaml`
- `backend/src/sketch2life/contracts/schemas/modal_ai.py`
- `backend/src/sketch2life/infrastructure/ai/modal_function_client.py`
- `backend/src/sketch2life/infrastructure/ai/story_generator_q38.py`
- `backend/src/sketch2life/infrastructure/config/settings.py`
- `backend/src/sketch2life/infrastructure/story_run_lite/repository.py`
- `backend/src/sketch2life/interfaces/http/app.py`
- `backend/tests/contract/test_parent_story_rewrites_route.py`
- `backend/tests/unit/test_modal_ai_source_literals.py`
- `backend/tests/unit/test_modal_qwen_profile.py`
- `backend/tests/unit/test_modal_story_function_client.py`
- `backend/tests/unit/test_story_generator_q38.py`
- `deployment/modal/srs_v23/README.md`
- `deployment/modal/srs_v23/contracts.py`
- `deployment/modal/srs_v23/drawing_vlm_app.py`
- `deployment/modal/srs_v23/language_audio_app.py`
- `deployment/modal/srs_v23/workloads.json`
- `deployment/modal/srs_v23/tests/test_qwen35_lesson_suggestion_contract.py`
- `deployment/modal/srs_v23/tests/test_story_workload_registry.py`

## Verification

- Backend default profile unit and contract selection: **512 passed**. This includes default startup, all switched registry entries, wrong active-model identity rejection, placeholder dispatch gates, both source literals, first-story selection binding, and the Parent story/activity contracts.
- Backend Qwen3.5 fallback selection: **65 passed** under `SKETCH2LIFE_MODAL_QWEN_PROFILE=qwen35` and `SKETCH2LIFE_STORY_GENERATION_PROFILE=v1_qwen35`.
- Modal suite: **132 passed, 4 deselected**. The deselected LMFE tests were `test_lmfe_token_data_excludes_model_eos_from_regular_tokens`, `test_vietnamese_characters_keep_json_parser_inside_bounded_string`, `test_lm_format_enforcer_accepts_only_structural_contract_shapes`, and `test_transformers5_compatible_prefix_adapter_enforces_json_tokens`.
- Qwen3.5 Modal fallback contract suite: **28 passed** with `SKETCH2LIFE_MODAL_QWEN_PROFILE=qwen35`.
- Syntax checks parsed 18 targeted Python files; `workloads.json` parsed; `git diff --check` passed.
- Tests use local fixtures/fakes. No database, provider, model download, deployment, Docker, or network call was made.

## Owner steps (not performed by any session)

- Deploy the Modal workloads with the Qwen3.8 images and configured pins, including the FP8 kernel commit and story checkpoint manifest digest.
- After deployment, run one real smoke call per workload group—story, `drawing.analyze`, and suggestions—before relying on Qwen3.8.

## Known limits

- The Qwen3.5 fallback exists only in code. Its weights were deleted from the Modal volume; running the fallback there requires downloading `qwen3_5_9b` again.
- The default Qwen3.8 first-story input includes the activity read from the stored selection, binds `activity_selection_sha256` to the stored selection hash and request fingerprint, and returns `409 PARENT_ACTIVITY_SELECTION_REQUIRED` when the selection is absent. The Qwen3.5 fallback converts to the legacy v1 input and therefore retains the old behavior without selected-activity context.
- Qwen3.8 drawing loader compatibility and runtime behavior remain NOT VERIFIED offline. All switched workloads remain disabled in `workloads.json`.
- `lmformatenforcer` and `imageio` are unavailable locally, so the Modal LMFE tests were NOT RUN; the four LMFE tests above were deselected and neither package was installed.

## Review round 2 — 2026-11-25

- The backend and Modal Q38 validators now accept selection snapshot sources `PINNED_LESSON`, `PUBLIC`, `SHARED`, and `AI_GENERATED_DRAFT`; they use stored activity bounds and permit nullable draft safety notes. The worker truncates prompt activity text to 400/1,200/400 characters for objective/instructions/safety.
- The legacy Parent route now builds v4 first-story input for Qwen3.8 and forwards its sentence-completeness rule; StoryRun-lite explicitly keeps its v1 input and matching client profile. Modal story composition is gated by local/test `modal_dev` settings.
- Runtime model identity comes from `Settings` or an injected workload profile for story, drawing, JSON, Parent route metadata, and StoryRun-lite metadata. Contact screening permits dates and short number runs while rejecting phone, email, and URL values in prompt fields. Q38 lifecycle logs omit the Modal SDK call ID; the return value and outcome errors retain it.
- Database-free default and Qwen3.5 fallback selections passed. The final default selection omitted the four LMFE cases and two out-of-scope route/OpenAPI failures; a PostgreSQL-gated test was skipped. No pin test was edited; pin literals remain `unpinned`.
- **NOT VERIFIED:** live Modal behavior, Qwen3.8 runtime compatibility, database behavior, and the four LMFE cases requiring `lmformatenforcer`. Route-level fallback identity checks in `parent_topic_suggestions.py`, `teacher_ai.py`, and `story_run_lite/photo_bridge.py` were not changed because those files are outside this round's allowlist. Both required pins remain `unpinned`; default-false dispatch stays fail-closed, with the local/test exception documented in the Unpinned dev setting section.
