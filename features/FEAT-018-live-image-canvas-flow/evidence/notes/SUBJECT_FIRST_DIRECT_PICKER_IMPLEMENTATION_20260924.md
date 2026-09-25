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
- `backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_lightning_scene_localization.py -q` — 3 passed;
  validates PNG/JPEG `content_type`, unsupported-signature fail-closed behavior and digest mismatch.
- The exact adapter payload validates against Lightning `_LocalizationRequestV1`; Ruff and compileall
  passed after the contract fix.
- Lightning request-validation failures now log only the endpoint and rejected field locations and
  return a generic contract error body; image bytes, prompts, credentials and provider input are
  not logged.
- The later 503 regression was reproduced by code-path review: Qwen model loading succeeds for
  `/v2/vision`, while localization output parsing/validation/runtime failures were all collapsed
  into one generic 503. The route now records a closed reason token and accepts only bounded fenced
  or nested-region JSON variants, normalizes bounded percentage confidence and unique label matches,
  normalizes bounded percentage coordinates and clips edge-crossing boxes before applying the
  existing target/geometry checks. Model/runtime failures now return an empty-region fallback with
  HTTP 200; malformed input/auth/hash failures remain HTTP errors.
- `backend/.venv/Scripts/python.exe -m pytest backend/tests/unit/test_lightning_scene_localization.py backend/tests/contract/test_live_image_demo_api.py -q` — 23 passed.
- Full `backend/tests` was attempted but the host's shared pytest temporary directory returned
  Windows `Access denied`; the focused contract suite passed in the project virtualenv.

## Manual follow-up

The owner must restart the Lightning service with the updated `tools/lightning_vision_v2_server.py`
before a live localization smoke test. The smoke test consumes the existing owner-controlled quota;
Codex did not call Lightning.

## Rollback verification — 2026-09-25

The owner requested removal of the direct subject picker and its initial localization request. The
runtime now restores the three-topic Gate-A flow: the first topic direction is selected by default,
the adult can edit it, and the original artwork is not a tap target. The default API composition
does not wire `SceneLocalizationPort`, so the initial understanding request calls only `/v2/vision`.

Verification:

- `backend/.venv/Scripts/python.exe -m pytest backend/tests/contract/test_live_image_demo_api.py backend/tests/unit/test_lightning_scene_localization.py -q` — 23 passed.
- `apps/ui-mobile/node_modules/.bin/tsc.cmd --noEmit` — passed.
- `node apps/ui-mobile/scripts/validate-ui-copy.mjs` — passed.
- A duplicate-submit lock guards the initial understanding action; a contract test injects a localizer
  and confirms it receives zero calls during the initial understanding request.
