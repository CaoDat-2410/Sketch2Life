# FEAT-030 implementation evidence — 2026-09-25

## Implemented

- Python contracts for preparation requests, jobs, archetypes, delivery tiers, mesh/bones/weights, validation, rig packages, V2 animation plans and V2 launch commands.
- Deterministic archetype registry covering butterfly, bird, flower, tree/branch, fish, biped, rigid, generic organic and unknown paths.
- Template mesh generation, bounded bone graphs, normalized weights, geometry validation and level-2 motion profiles.
- Gate-A idempotent preparation job with a replaceable segmentation port.
- Content-addressed package storage, short-lived two-read capability and hash-bearing HTTP response.
- Additive `PixiRendererLaunchV2`; V1 launch remains in the same result for rollback.
- TypeScript/Zod V2 contract mirror.
- PixiJS `MeshGeometry` player with CPU skinning and GSAP bone-keyframe animation.
- Source-derived foreground processing that removes only near-paper pixels for the safe cutout tier.
- Android prefers V2, keeps full-screen controls, uses friendly loading copy, and falls back to the original V1 reveal if the V2 package cannot load or validate.
- No tap-to-select behavior was reintroduced.

## Current delivery tiers

- When a benchmark-approved segmentation adapter supplies a validated region after Gate A, the package is `FULL_AUTO_RIG`.
- In the checked-in default composition no segmentation model is silently enabled. It produces `CUTOUT_MICRO_MOTION`, preserves the full source, and records `SEGMENTATION_ADAPTER_UNAVAILABLE`.
- Invalid geometry downgrades to `BBOX_VISUAL_FOCUS`; package/load failure uses V1 whole-drawing playback.

This limitation is intentional: the implementation does not reactivate the unreliable second Qwen localization call and does not claim a model benchmark that has not been run on the Lightning L4.

## Verification

### Full backend regression

- Command: `$env:PYTHONPATH='backend/src;.'; .\backend\.venv\Scripts\python.exe -m pytest backend/tests --basetemp <feature-local-temp> -q`
- Environment: Windows local workspace, Python 3.12 project virtual environment.
- Result: PASS, 100% suite completion; existing marked skips remained skips.
- Limitation: pytest emitted a pre-existing cache write warning for `backend/.pytest_cache`; tests themselves passed.

### Focused FEAT-030/backend contract tests

- Command: `.\.venv\Scripts\python.exe -m pytest tests/unit/test_auto_rig.py tests/contract/test_renderer_contracts.py tests/contract/test_live_image_demo_api.py::test_fake_only_image_session_completes_p1_gate_b_p4_handoff_feedback_and_gallery ... -q`
- Result: PASS, 18 tests in the recorded run before the additional segmentation-port case; the subsequent focused run also passed all 14 selected cases.
- Coverage: registry, unknown fallback, geometry/weights, motion targets, capability read bounds, Gate-A job idempotency, successful segmentation promotion, V1 contract regression and supervised-flow V2 package retrieval.

### Renderer/mobile

- `pnpm --filter @sketch2life/art-renderer typecheck` — PASS.
- `pnpm --filter @sketch2life/art-renderer test` — PASS, 14 tests.
- `pnpm --filter @sketch2life/art-renderer build:demo` — PASS.
- `pnpm --filter sketch2life-mobile exec tsc --noEmit` — PASS.
- `pnpm --filter sketch2life-mobile test` — `UI_COPY_AND_RECOVERY_VALID`.

### Repository security

- Command: `python tools/validate_repository_security.py`.
- Result: `REPOSITORY_SECURITY_VALID`; 1583 publishable files scanned in the final run.

## Required next evidence before enabling a live segmentation worker

1. Golden child-drawing/synthetic corpus manifest and rights review.
2. Candidate model/config/license record.
3. L4 Qwen-only, segmentation-only, sequential and attempted-concurrent VRAM/latency measurements.
4. Region/mask quality and rejection/fallback results by archetype.
5. Android visual recording and FPS/memory evidence for full-rig scenes.
