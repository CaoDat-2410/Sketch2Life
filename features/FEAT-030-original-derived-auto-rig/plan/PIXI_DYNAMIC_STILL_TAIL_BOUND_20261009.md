# Pixi dynamic still-tail prompt bound

- Feature: FEAT-030 original-derived auto-rig
- Revision: 1
- Status: APPROVED — implementation in progress
- Date: 2026-10-09
- Owner request: follow-up log after `18762db` reports `MODEL_SCHEMA_INVALID schema_issues=root:still_tail_too_short`.
- Parent plan: `PIXI_ROOT_VALIDATOR_DIAGNOSTICS_AND_CONSTRAINTS_20261009.md`.

## Finding

- The server has a precise safe reason code confirming the model's final beat ends after the still-tail cutoff. The prompt states the cutoff symbolically (`durationSeconds minus 2`) while the actual duration is in the trailing JSON context.

## Scope

- Calculate the final still interval from the request's integer `renderer_duration_seconds` before constructing the V4 prompt.
- State the exact numeric required `durationSeconds`, final-beat `endSeconds` maximum, and still interval in plain prompt text. For example, for a 20-second show, the final beat must end by 18 seconds and there can be no beats in `[18, 20]`.
- Keep model output validation fail-closed. Do not clamp, rewrite, retry, or replace model output.
- Preserve the existing single inference, contract, and safe log behavior.

## Acceptance criteria

1. The prompt contains numeric duration and still-tail boundaries derived from the current request.
2. `MODEL_SCHEMA_INVALID` with `root:still_tail_too_short` remains a 502 if the model still violates the invariant.
3. No generated beat timing is silently modified and no additional model call is made.

## Verification

- Review the inserted numeric constraints against the Pydantic root validator.
- Run Python source compilation and `git diff --check` only; no tests or live model request from this workstation.
- Deploy to Lightning and make a synthetic-image attempt for runtime acceptance.

## Risks and limits

- The exact cutoff in the prompt reduces ambiguity but cannot guarantee model compliance; the backend validator remains authoritative.
- No real child data or model output is included in repository evidence.
