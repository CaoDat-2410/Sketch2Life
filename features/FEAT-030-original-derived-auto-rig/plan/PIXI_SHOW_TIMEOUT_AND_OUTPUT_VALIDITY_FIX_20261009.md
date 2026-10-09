# Pixi planner timeout and output validity fix

- Feature: FEAT-030 original-derived auto-rig
- Revision: 1
- Status: APPROVED — implementation in progress
- Date: 2026-10-09
- Owner request: “bug như sau, check log và fix”, with the follow-up Lightning log reporting `MODEL_OUTPUT_INVALID` and HTTP 502.
- Parent scope: owner-approved adaptive Pixi scene planning in `PIXI_ADAPTIVE_ART_AND_TOPIC_SCENE_20261008.md`.

## Findings

- The mobile `prepareRenderer` command uses the generic 30-second timeout. The Lightning planner's bounded Qwen profile and backend transport allow up to 120 seconds, so the app can abort before the server finishes.
- The Lightning server returns `MODEL_OUTPUT_INVALID` when model output fails JSON parsing, closed-schema validation, or deterministic asset checks. The current planner prompt omits several exact schema enums and coordinate bounds, and its log intentionally collapses these failures into one code.

## Scope

- Give only the mobile renderer-preparation command a 150-second client deadline. Leave other API timeouts unchanged.
- Tighten the V4 planner prompt to enumerate schema-accepted values and numeric/timing constraints, request exactly three beats to keep the bounded response concise, and state exact asset/theme ID rules.
- Accept one optional outer `json` code fence while retaining strict JSON parsing, duplicate-key rejection, and the same Pydantic validation.
- Split invalid-output server logs into closed stage labels for JSON parsing, schema validation, and deterministic planner policy checks. Never log model output, prompt, crop, candidate descriptions, or validation values.
- Preserve one model call, no automatic retry, no contract changes, and the visible typed failure on invalid output.

## Acceptance criteria

1. `prepareRenderer` permits the existing server-side 120-second bounded call plus 30 seconds of transport/rendering overhead; other mobile requests keep their existing deadlines.
2. The V4 prompt states all allowed subject hints, behavior classes, actions, target roles and render strategies; valid coordinate, timing, asset and scene-theme constraints; and a concise three-beat output.
3. An optional single JSON code fence is normalized before strict parse. Duplicate keys, invalid schema values, invented asset IDs and invalid topic-scene combinations remain rejected.
4. Failure logs distinguish `MODEL_JSON_INVALID`, `MODEL_SCHEMA_INVALID`, and `MODEL_POLICY_INVALID` without recording user or model content; the HTTP failure remains safe and typed.
5. No extra AI call, automatic retry, fallback show, or public contract change is introduced.

## Verification plan

- Review only the diff for the mobile timeout, V4 planner prompt/parser, and sanitized failure-stage logs.
- Preserve the reported log category as actionable evidence; do not transmit the drawing or request raw model output.
- Runtime acceptance requires the owner to pull the change into Lightning, restart Uvicorn, and make one synthetic-image attempt. This workstation cannot inspect the remote Studio process.

## Risks and limits

- The current excerpt does not identify whether the invalid response was malformed JSON, schema-invalid, or disallowed asset selection. The new stage labels will distinguish these without exposing content.
- A larger client deadline prevents premature mobile abort but does not guarantee model output validity or remote runtime readiness.
