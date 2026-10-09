# Pixi root-validator diagnostics and prompt constraints

- Feature: FEAT-030 original-derived auto-rig
- Revision: 1
- Status: APPROVED — implementation in progress
- Date: 2026-10-09
- Owner request: “vẫn bị 502, check log và fix”; the owner supplied the post-`b3a7798` log showing `MODEL_SCHEMA_INVALID schema_issues=root:value_error`.
- Parent plans: `PIXI_SHOW_TIMEOUT_AND_OUTPUT_VALIDITY_FIX_20261009.md` and `PIXI_SCHEMA_INVALID_PROMPT_CONTRADICTION_FIX_20261009.md`.

## Findings

- The returned JSON parsed and passed field-level checks far enough to fail a whole-show Pydantic validator (`root:value_error`). The current sanitized summary suppresses the fixed validator message, so the log cannot distinguish which invariant failed.
- The V4 prompt says to leave two seconds still, but does not explicitly bound the final beat's `endSeconds` to `durationSeconds - 2`.
- The schema requires `selectedAssetIds` to be unique, while the V4 prompt does not say to list each selected ID only once.

## Scope

- State the final `SETTLE` beat must end no later than `durationSeconds - 2`, with no beats in the final still interval.
- State that `selectedAssetIds` is a deduplicated array and every supplemental beat asset appears in it.
- Map only the known fixed Pydantic root-validator messages to hard-coded safe rule codes such as `still_tail_too_short` and `selected_assets_not_unique`. Do not log messages or model values.
- Preserve the single inference, no retry/repair/fallback, closed contract, and generic fail-closed HTTP response.

## Acceptance criteria

1. The prompt directly expresses the Pydantic final-still and unique-ID rules.
2. A root-level schema error is logged as one of the allowlisted rule codes when it matches a known validator; otherwise it remains `root:value_error`.
3. Logs contain no raw exception message, input value, model response, prompt, image, or candidate content.
4. No public contract or inference-call behavior changes.

## Verification

- Review the prompt against the `PixiShowIntentV1` root validator and the inherited beat rules.
- Run Python source compilation and `git diff --check` only; do not run tests or live model inference from this workstation.
- Runtime acceptance requires the owner to deploy this commit, restart Uvicorn, and make a synthetic-image request.

## Risks and limits

- `root:value_error` does not identify which validator failed. The prompt will remove two likely ambiguities, while the safe root-code map will identify a remaining known validator on the next request.
- No real child media or model output is included in repository evidence.
