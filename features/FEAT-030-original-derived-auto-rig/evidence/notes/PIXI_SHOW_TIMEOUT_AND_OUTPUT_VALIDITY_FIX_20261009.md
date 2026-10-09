# Pixi planner timeout and invalid-output fix

Date: 2026-10-09 (Asia/Saigon)

## Reported evidence

- The mobile screen reports that the server is taking longer than expected. The UI maps this state to `REQUEST_TIMEOUT`.
- The supplied Lightning excerpt reports `POST /v4/pixi/show-plan` as HTTP 502 with `code=MODEL_OUTPUT_INVALID`; preceding vision, segmentation, and activity-ranking calls returned HTTP 200.
- The excerpt does not contain the generated model response, and it does not identify whether JSON parsing, schema validation, or asset policy validation failed. No user image or model output was requested or copied into this evidence.

## Changes made

- Increased only the mobile `prepareRenderer` command deadline from 30 to 150 seconds, leaving the generic timeout and other requests unchanged. This gives the client 30 seconds of overhead beyond the existing 120-second server-side planner limit.
- Tightened the adaptive Pixi V4 prompt with the schema's allowed enum values, numeric/timing bounds, asset/theme rules, and a concise three-beat requirement.
- The planner parser now unwraps one optional outer JSON code fence and retains duplicate-key rejection and the same closed Pydantic schema.
- Sanitized planner failure logs now distinguish `MODEL_JSON_INVALID`, `MODEL_SCHEMA_INVALID`, `MODEL_POLICY_INVALID`, and an unexpected `MODEL_OUTPUT_UNCLASSIFIED` case. No model output, prompts, images, candidate content, or validation values are logged. HTTP failures remain fail-closed; no retry or substitute scene was added.

## Verification and limits

- `python -m py_compile tools/lightning_vision_v2_server.py` passed.
- `git diff --check` passed for the changed implementation and FEAT-030 records.
- Tests and live model inference were not run. This workstation cannot inspect the Lightning Studio process. The change must be present in the remote checkout and Uvicorn restarted before the new stage-specific log code can appear.
- Existing rights, privacy, provider, and Android visual acceptance gates remain unchanged.
