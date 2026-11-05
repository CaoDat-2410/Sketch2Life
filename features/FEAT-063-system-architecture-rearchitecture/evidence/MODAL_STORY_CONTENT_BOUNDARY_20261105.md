# Modal Parent story content/metadata boundary — execution report

**Date:** 2026-11-05 (Asia/Saigon)  
**Feature:** FEAT-063  
**Plan:** [`MODAL_STORY_CONTENT_BOUNDARY_20261105.md`](../plan/MODAL_STORY_CONTENT_BOUNDARY_20261105.md), revision 1  
**Plan SHA-256:** `DEEC2263B3148A855AE090D1A513B1D57174CD9800FAC9BA8BC0E3A3F6F23917`

## Outcome

The Parent story worker now returns a story accepted by its strict worker parser, backend `StoryRevisionDraftV1`, and the butterfly lifecycle validator. One synthetic request completed successfully; no video or other AI workload was called.

The preceding parser-alignment request had failed with the safe reason `SCENE_FIELDS_INVALID`. That reason grouped several possible scene-field violations; raw output was intentionally not retained, so the precise malformed field is unknown. This follow-up removes generated timing/index fields from the model's output responsibility and verifies the assembled public contract end to end.

## Implementation

- Qwen now emits only the story title, opening/middle/ending, and five scenes' narrative fields. A strict content parser rejects duplicate keys, extra/missing fields, invalid lengths, blank text, invalid anchors, and scene counts other than five.
- The server deterministically assigns scene indices 1–5, starts at 0/6,000/12,000/18,000/24,000 ms, and 6,000 ms per scene, for a 30,000 ms total. Five scenes are within the existing SRS/backend range of 5–15.
- The assembled object still passes the existing strict `_parse_story_output`; that parser, the backend contract, safety/fact checks, and public output schema were not loosened or changed.
- Constrained decoding now uses the content-only JSON Schema. No repair pass or second inference was added.

## Verification

- Focused tests: **46 passed** in 0.89 seconds.
- Ruff: passed.
- Python compilation: passed.
- The local `lm-format-enforcer==0.10.11` schema probe accepted valid content and rejected an extra key, four scenes, and an overlength title.
- Synthetic Modal call: `fc-01M6M4APDR5QMGF8VA6PKJ66M5`.
- Result: five scenes, 30,000 ms, backend schema validation passed, butterfly lifecycle validation passed.
- Model: `Qwen/Qwen2.5-7B-Instruct`, revision `a09a35458c702b33eeacc393d103063234e8bc28`; GPU: NVIDIA L40S.
- Dispatch to terminal result: **56.073 seconds**. Worker measured model load 16.645 s, constraint construction 3.412 s, and generation 26.137 s for 608 output tokens.
- The Modal app was stopped and verified with **zero tasks**. Scratch request files were removed; shared Volumes were retained.

## Scope and limits

This is one synthetic butterfly story verifying parser and contract compatibility. It does not establish story quality across other topics/age bands, general factual accuracy, production capacity, or video readiness. The adult review gate remains. No SRS, API, backend contract, model pin, or product enablement changed.

## Evidence assets

- `assets/modal_story_content_boundary_20261105/story_dispatch_intent.json`
- `assets/modal_story_content_boundary_20261105/story_result.json` (metadata and output hash only; no story text)
- `assets/modal_story_content_boundary_20261105/modal_function_logs.txt` (worker events and timings; no prompt or generated text)
- `assets/modal_story_content_boundary_20261105/local_validation.json`
- `scripts/run_modal_story_content_boundary_20261105.py`
