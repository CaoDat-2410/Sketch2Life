# Pixi schema-invalid prompt contradiction fix

Date: 2026-10-09 (Asia/Saigon)

## Runtime evidence

The owner confirmed Lightning had pulled and restarted commit `c74831e`. The latest supplied log showed activity ranking succeeded, followed by `POST /v4/pixi/show-plan` returning HTTP 502 and the new server code `MODEL_SCHEMA_INVALID`.

## Finding

The adaptive V4 prompt required `assetId`, `sceneThemeAssetId`, and `selectedAssetIds` to carry eligible IDs, then ended with “No ... asset IDs.” This directly contradicted the required output schema. The prompt also did not explicitly require `selectedAssetIds` to be a JSON array or say to return `[]` when empty.

## Changes made

- Removed the blanket prohibition on IDs. The prompt now forbids invented or unlisted IDs and repeats that IDs must match the eligible lists.
- Made the output shapes explicit: `selectedAssetIds` is always an array (`[]` when empty); subject beat `assetId` is JSON `null`; supplemental beat IDs also appear in `selectedAssetIds`; scene theme is an eligible environment ID or JSON `null`.
- Added a bounded `schema_issues` log summary for Pydantic failures. It contains only allowlisted schema field names, small array indices, and constrained error type codes. Unknown keys are replaced with `<other>`; values, messages, model output, prompt, image, and candidate content are excluded.
- Preserved the single inference, existing schema, generic HTTP 502, and no retry/fallback behavior.

## Verification and limits

- `python -m py_compile tools/lightning_vision_v2_server.py` passed.
- `git diff --check` passed for the implementation and FEAT-030 records.
- Tests and live model inference were not run. Lightning must pull this patch and restart Uvicorn before the contradiction fix and field diagnostics are active there.
- No real child data or model output is included in this evidence.
