# Personalized Drawing Exploration implementation evidence

Date: 2026-09-23
Branch: `codex/feat-018-pixi-exploration`
Scope: Pixi-only; video implementation excluded and owned by another task.

## Implemented

- Added `SubjectCandidateSetV1` with a maximum of three confirmed concrete subjects. Labels are
  short Vietnamese display labels and retain confidence, image/narration coverage, relation refs
  and source claim IDs.
- Added `SceneExplorationPlanV1` for source-grounded reveal, subject focus, relation focus and
  learning bridge beats. It is projected from the existing raw understanding, confirmed anchor
  set and approved `ExperienceSpecV1`; FEAT-003 and Qwen output contracts were not widened.
- Added `SceneFocusPlanV1` and `SourceRegionV1`. The only accepted 2.5D input is an explicitly
  supplied normalized region with extraction provenance. The live path currently emits the safe
  `FALLBACK_REQUIRED/NO_LOCALIZER` state unless a future approved localizer stores region hints in
  the session. No guessed coordinates are used.
- Extended the source-locked renderer protocol to allow multiple source-derived objects while
  retaining exactly one preserved original manifest asset. Pixi applies source crops, supports
  source-preserving motion layers and emits `FOCUS_CHANGED`/`DISCOVERED_ENTITY` events.
- Added child-friendly native discovery chips and lifecycle handling in `PixiIntroScreen`. The
  existing landscape Pixi -> video placeholder -> portrait activity order remains intact.

## Verification

- `python -m compileall -q backend/src/sketch2life` — passed.
- `python -m ruff check` on changed Python files — passed.
- `python -m pytest backend/tests/contract/test_renderer_contracts.py -q` — 5 passed.
- `pnpm --filter @sketch2life/art-renderer typecheck` — passed.
- `pnpm --filter @sketch2life/art-renderer test -- --run` — 11 passed.
- `pnpm --filter @sketch2life/art-renderer build:demo` — passed.
- `apps/ui-mobile/node_modules/.bin/tsc.cmd --noEmit -p apps/ui-mobile/tsconfig.json` — passed.
- `python tools/validate_repository_security.py` remains required before commit/push.

## Environment limitation

The broader backend/HTTP test collection could not start in this local shell because optional
image-admission dependency `av==18.1.0` is not installed. This is an environment prerequisite;
the renderer contract suite and all changed renderer TypeScript checks passed. No live Lightning
request was made.

## Explicit non-goals verified

No MP4, TTS, video worker/encoder/playback, video READY/retry state, auth, durable persistence,
mobile provider credential, generated replacement artwork, FEAT-003 change or FEAT-026 file was
added or staged by this implementation.
