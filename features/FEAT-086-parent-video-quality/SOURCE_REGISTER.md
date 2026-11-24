# FEAT-086 source register

## Current requirement authority

- `features/FEAT-063-system-architecture-rearchitecture/artifacts/SKETCH2LIFE_SYSTEM_ARCHITECTURE_SRS.md`, v2.7-draft Rev67, unsigned. Use FR-AI-02 through FR-AI-06 and FR-AI-13 as current targets; the SRS remains unchanged in this task.
- `docs/context/SRS_AUTHORITY.md` routes current product requirements to that SRS only.

## Implementation and evidence sources

- FEAT-085 `STATUS.md`, `CONTEXT.md`, and `evidence/RESULTS_PARENT_E2E_AFTER_HF_TOKEN_UPDATE_20261123.md`: real synthetic Parent candidate and playback evidence. The source turtle image is vector-like and the video was not a production safety review.
- FEAT-061 `assets/generated/crayon-controls-v1/03-house-and-sun.png`: existing synthetic crayon drawing.
- FEAT-061 `evidence/CRAYON_CONTROLS_PROVENANCE_20261029.json`: states the drawing was created by built-in ImageGen for synthetic diagnostics and is not authentic child artwork. Use this provenance when citing the input.
- Current code inspected: `deployment/modal/srs_v23/language_audio_app.py` story parser/prompt; `backend/src/sketch2life/application/services/parent_video_candidate_service.py` Parent-to-video manifest adapter and its internal prompt bound; `deployment/modal/srs_v23/story_visual_plan.py` LTX prompt compiler and worker-plan validation; `deployment/modal/srs_v23/video_app.py` scene conditioning; `apps/ui-mobile/src/parent/presentation/screens/VideoCandidateScreen.tsx` ready state.
- Focused contracts: `deployment/modal/srs_v23/tests/test_parent_story_output_contract.py`, `deployment/modal/srs_v23/tests/test_story_visual_plan.py`, `deployment/modal/srs_v23/tests/test_silent_video_prompt.py`, `deployment/modal/srs_v23/tests/test_video_app_contract.py`, and `backend/tests/unit/test_parent_video_candidate_manifest.py`.
- Current verification record: `evidence/RESULTS_REV2_20261124.md`. No live inference or new video was produced in Rev2.

## Technical references reviewed 2026-11-24

- Official LTX image-to-video guide: https://docs.ltx.io/open-source-model/usage-guides/image-to-video — describes motion after the first frame and source-image conditioning.
- Official LTX prompting guide: https://docs.ltx.io/open-source-model/usage-guides/prompting-guide/ — recommends action-focused I2V, single continuous take when appropriate, plausible motion; optional prompt enhancement adds an inference pass and latency.
- Official LTX 2.5 workflow collection: https://github.com/Lightricks/ComfyUI-LTXVideo/tree/master/example_workflows/2.5 — includes a distinct sparse-motion-track image-to-video workflow.
- Reviewed but not installed community prompt skill: https://github.com/benjiyaya/LTX-2.5-Agent-Prompt-Skill — MIT, an agent-side prompt-writing skill that emphasizes cinematic creative enhancement; not a Modal model adapter.
