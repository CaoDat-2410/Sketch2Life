# Pixi schema-invalid prompt contradiction fix

- Feature: FEAT-030 original-derived auto-rig
- Revision: 1
- Status: APPROVED — implementation in progress
- Date: 2026-10-09
- Owner request: “bị 502 bad gateway, check log và fix đi”; the owner confirmed Lightning pulled and restarted commit `c74831e` and supplied a new log with `MODEL_SCHEMA_INVALID` and HTTP 502.
- Parent plan: `PIXI_SHOW_TIMEOUT_AND_OUTPUT_VALIDITY_FIX_20261009.md`.

## Findings

- The newly deployed server log classifies the failure at Pydantic schema validation. It does not include safe field-level diagnostics.
- The V4 prompt first asks the model to emit eligible IDs in `selectedAssetIds`, `sceneThemeAssetId`, and beat `assetId`, then ends by forbidding “asset IDs.” This is a direct instruction conflict and can cause an output that omits or mis-shapes required ID fields.
- The prompt describes the allowed values for `selectedAssetIds` but does not explicitly require a JSON array or say to use `[]` when none are selected.

## Scope

- Remove the contradictory blanket prohibition on asset IDs. Forbid only IDs not present in the supplied eligible lists.
- State the exact JSON shapes for `selectedAssetIds` (array, `[]` when empty), `sceneThemeAssetId` (eligible string or `null`), and beat asset IDs.
- When Pydantic rejects the output, add a bounded, sanitized summary containing only allowlisted schema field paths and error types. Never log values, messages, model output, prompt, image, or candidate data.
- Keep the existing single inference, closed schema, fail-closed HTTP 502, no retry, and no fallback behavior.

## Acceptance criteria

1. The prompt no longer forbids the eligible IDs it requires and clearly specifies JSON container/null types.
2. Invalid schema logs can identify a known field path and Pydantic error type, while arbitrary keys and all values are suppressed.
3. The HTTP response remains generic and safe; no public contract or model-call behavior changes.
4. No automatic retry, repair, or fallback scene is introduced.

## Verification

- Review the prompt against `PixiShowIntentV2` and the beat/asset schema.
- Compile the changed Python module and run `git diff --check`.
- Do not run tests or a live model request in this workstation session. The owner can rerun one synthetic-image attempt on Lightning after pulling the commit and restarting Uvicorn.

## Risks and limits

- The supplied log identifies schema rejection but not the precise field. The prompt contradiction is a concrete cause found by source review; the sanitized field summary will identify any remaining mismatch on the next request.
- No real-child data, model output, or secrets are included in code, logs, or evidence.
