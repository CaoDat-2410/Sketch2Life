# Subject-first direct picker implementation — 2026-09-24

Status: `IMPLEMENTED — OFFLINE VERIFIED`

Branch: `codex/feat-018-pixi-exploration`

## Scope

- Removed the normal three-card topic-direction UI path.
- Added a backend-only `SELECT_SUBJECT` workflow operation. It validates the tapped candidate id,
  composes one grounded Vietnamese sentence, preserves the source claim ids, and keeps Gate A
  pending until the adult reviews that sentence.
- Added bounded subject localization through `SceneLocalizationPort` and a Lightning `/v2/localize`
  endpoint. The mobile app receives only normalized regions; credentials remain backend-only.
- Added direct artwork hitboxes in the React Native Gate-A screen and reused the selected region in
  the later Pixi launch path.
- Added Pixi subject outlines for crop-based localization and a stronger source-preserving fallback
  reveal/zoom/drift/settle sequence. No video/MP4 work was added.

## Contract and safety evidence

- Subject ids must come from the semantic entity claims already accepted by Gate A.
- Localization regions are bounded to normalized source coordinates, limited to three targets and
  rejected when identity or geometry is invalid.
- Missing localization remains `FALLBACK_REQUIRED`; the app does not invent a hitbox.
- Provider output is parsed and bounded in the Lightning service; raw model output is not returned
  to the app or logged.

## Verification

- `backend/.venv/Scripts/python.exe -m pytest backend/tests/contract/test_live_image_demo_api.py -q` — 14 passed.
- `backend/.venv/Scripts/python.exe -m ruff check ...` on changed backend/server files — passed.
- `pnpm --dir packages/art-renderer run typecheck` — passed.
- `pnpm --dir packages/art-renderer test` — 11 passed.
- `pnpm --dir packages/art-renderer run build:demo` — passed; local ignored `dist-demo` rebuilt.
- `pnpm --dir apps/ui-mobile exec tsc --noEmit` — passed.
- `pnpm --dir apps/ui-mobile test` — passed.
- Full `backend/tests` was attempted but the host's shared pytest temporary directory returned
  Windows `Access denied`; the focused contract suite passed in the project virtualenv.

## Manual follow-up

The owner must restart the Lightning service with the updated `tools/lightning_vision_v2_server.py`
before a live localization smoke test. The smoke test consumes the existing owner-controlled quota;
Codex did not call Lightning.
