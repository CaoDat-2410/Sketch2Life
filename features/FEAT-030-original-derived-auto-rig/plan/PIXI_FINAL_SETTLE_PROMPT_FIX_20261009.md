# Pixi final-beat SETTLE prompt fix

- Feature: FEAT-030 original-derived auto-rig
- Revision: 1
- Status: APPROVED — implemented locally; runtime retest pending
- Date: 2026-10-09
- Owner evidence: deployed Lightning log reports `MODEL_SCHEMA_INVALID schema_issues=root:final_beat_not_settle` for `/v4/pixi/show-plan`.
- Parent plan: `PIXI_RIG_CAPABILITY_PROMPT_FIX_20261009.md`.

## Finding

The V4 prompt says to end with SETTLE, but the deployed Qwen response still violates the Pydantic invariant requiring the final beat action to be exactly `SETTLE`. The backend correctly rejects that response with 502. The instruction currently appears before the request context and is not repeated as an indexed output requirement after the context.

## Scope

- Add request-derived machine-readable constraints for exactly three beats, final beat index 2, final action `SETTLE`, source-subject target, null asset ID, and the existing duration/still-tail limit.
- Repeat the exact indexed requirement at the end of the V4 prompt, after the JSON context, and distinguish it from the action whitelist for the first two beats.
- Keep Pydantic validation authoritative. Do not clamp or rewrite the response, retry, add another model call, change contracts, or substitute a plan.
- Preserve sanitized schema diagnostics and exclude prompts, images, and model output from logs/evidence.

## Acceptance criteria

1. The request context and final prompt lines state `beats[2].action == "SETTLE"` exactly.
2. The final beat is explicitly a `SOURCE_SUBJECT` beat with `assetId: null` and ends no later than the request's still-tail cutoff.
3. Output still uses exactly three ordered non-overlapping beats and the existing closed schema.
4. Invalid model output continues to fail closed with the existing safe `MODEL_SCHEMA_INVALID` response.

## Verification

- Run Python source compilation and `git diff --check` only.
- Do not run tests or make a live Lightning/provider request from this workstation.
- Runtime acceptance requires deploying the patch, restarting Uvicorn, and retrying with synthetic artwork.

## Boundaries

- This is a prompt clarification within the existing one-call Pixi planner and adaptive-art approval.
- No model output repair, retry, fallback, contract change, dependency, or provider activation is included.

## Implementation status — 2026-10-09

- Added a request-derived machine-readable final-beat constraint object and repeated the indexed `beats[2]` requirement after the complete JSON context.
- Python compilation and `git diff --check` passed. Tests and live inference were not run.
- Runtime acceptance remains pending deployment and synthetic-artwork retry.
