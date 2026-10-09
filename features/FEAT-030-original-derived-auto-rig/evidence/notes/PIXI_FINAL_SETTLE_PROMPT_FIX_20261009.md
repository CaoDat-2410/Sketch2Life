# Pixi final-beat SETTLE prompt fix

Date: 2026-10-09 (Asia/Saigon)

## Runtime evidence

After deploying the previous capability-prompt change, the owner supplied a Lightning log showing `/v4/pixi/show-plan` returned HTTP 502 with `MODEL_SCHEMA_INVALID schema_issues=root:final_beat_not_settle`. This identifies the final action invariant as the failure; it is not the earlier mask-capability rejection.

## Change

- Added request-derived prompt context for exactly three beats, final index 2, exact action `SETTLE`, source-subject target, null asset ID, still-tail cutoff, and `endingStill: true`.
- Repeated those exact indexed requirements after the JSON context at the end of the prompt, explicitly reserving the first two beat positions for strategy-supported actions.
- Kept the Pydantic validator authoritative. No response rewrite, retry, extra inference, fallback, contract change, or content logging was added.

## Verification and limits

- Command: `python -m py_compile tools/lightning_vision_v2_server.py` — passed.
- Command: `git diff --check -- tools/lightning_vision_v2_server.py features/FEAT-030-original-derived-auto-rig` — passed.
- Tests and live inference were not run. Runtime acceptance requires deploying the Lightning server change, restarting Uvicorn, and retrying with synthetic artwork.
