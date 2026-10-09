# Pixi dynamic still-tail prompt bound

Date: 2026-10-09 (Asia/Saigon)

## Runtime evidence

After commit `18762db` was deployed, the owner supplied a Lightning log with `MODEL_SCHEMA_INVALID schema_issues=root:still_tail_too_short` for `/v4/pixi/show-plan`.

## Change

- The schema-safe logger identified the exact failed invariant without exposing the model's response.
- The V4 prompt now embeds the request's exact integer `renderer_duration_seconds`, the maximum end time for the final `SETTLE` beat (`duration - 2`), and the numeric interval held still by the renderer.
- The backend keeps its Pydantic check authoritative and still rejects invalid output. No timing is clamped or rewritten, and no retry, fallback, extra inference, or contract change was added.

## Verification and limits

- `python -m py_compile tools/lightning_vision_v2_server.py` passed.
- `git diff --check` passed for the implementation and FEAT-030 records.
- Tests and live model inference were not run. Runtime acceptance requires deploying this patch, restarting Uvicorn, and making a synthetic-image request.
- No real child data or model output is included in this evidence.
