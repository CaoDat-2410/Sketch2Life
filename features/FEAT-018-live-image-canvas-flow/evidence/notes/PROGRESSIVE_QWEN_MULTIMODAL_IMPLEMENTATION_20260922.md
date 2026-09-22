# FEAT-018 progressive Qwen multimodal implementation evidence

Date: 2026-09-22

Approved plan: `plan/PROGRESSIVE_QWEN_MULTIMODAL_RESPONSE_PLAN.md`

## Implemented behavior

- The Lightning Qwen adapter keeps the strict Vision V2 contract and allows one semantic-empty
  repair generation in addition to the existing bounded schema repair path.
- The live image workflow maps image plus ASR/typed-text evidence into the existing raw handoff,
  preserves source references, derives reviewed-alias fusion links, and records closed source
  conflicts.
- An admitted image with no grounded image claim cannot advance to Gate A. The terminal application
  state is `BLOCKED_NO_GROUNDED_CLAIMS` with reason `NO_GROUNDED_CLAIMS`.
- The backend creates a sanitized `understanding_progress` projection and exposes it through
  `GET /v1/sessions/{session_id}/understanding/progress` without returning raw provider output.
- A changed adult direction uses `REQUERY_UNDERSTANDING`, reuses the admitted artifact and stored
  narration input, increments one direction revision, and is capped at one changed-direction
  re-query per demo session.
- BaoVC consumes the backend topic and refuses to navigate into Gate A when the claim list or
  backend readiness flag is empty.

## Offline verification

- Full backend collection: `pytest -q backend/tests` — passed, six existing skips.
- Focused Qwen and FEAT-018 tests — passed, including semantic-empty repair, Gate-A blocking,
  multimodal fusion, topic bounds, re-query and progress polling.
- Ruff — passed for changed backend, Lightning server and focused tests.
- Mypy — passed for changed backend modules.
- Mobile TypeScript — `tsc --noEmit -p apps/ui-mobile/tsconfig.json` passed.
- `compileall`, `git diff --check`, and repository security validation — passed.

## Boundary

No Lightning/model request was made by Codex. The owner must perform the Android/Lightning smoke
matrix under the approved approximately 25-credit ceiling and record only sanitized outcomes.
