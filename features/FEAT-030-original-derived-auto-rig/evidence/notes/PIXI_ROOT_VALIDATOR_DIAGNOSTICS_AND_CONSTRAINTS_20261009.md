# Pixi root-validator diagnostics and prompt constraints

Date: 2026-10-09 (Asia/Saigon)

## Runtime evidence

After `b3a7798` was pulled and Uvicorn restarted, the owner supplied a log showing activity ranking HTTP 200, followed by `/v4/pixi/show-plan` HTTP 502 and `MODEL_SCHEMA_INVALID schema_issues=root:value_error`.

## Findings and changes

- The generic root `value_error` means Pydantic's whole-show validator rejected a parsed output. Known invariants include unique selected IDs, final `SETTLE`, a two-second still tail, ordered/non-overlapping beats, and selected supplemental asset references.
- The prompt now says the final beat must be `SETTLE` and end no later than `durationSeconds - 2`, leaving the final two seconds with no beats. It also says to list each selected ID only once and include every supplemental beat ID.
- The log helper now maps only exact, fixed Pydantic validation messages to hard-coded reason codes such as `still_tail_too_short` and `selected_assets_not_unique`. It never writes the raw message, input, prompt, model output, image, or candidate data. Unknown root failures remain `root:value_error`.
- The server still makes one inference and fails closed with the same generic HTTP 502. No retry, output repair, fallback, or contract change was added.

## Verification and limits

- `python -m py_compile tools/lightning_vision_v2_server.py` passed.
- `git diff --check` passed for the implementation and FEAT-030 records.
- Tests and live model inference were not run. Deploy the commit and restart Uvicorn before the next synthetic request.
- No real child data or model output is included in this evidence.
