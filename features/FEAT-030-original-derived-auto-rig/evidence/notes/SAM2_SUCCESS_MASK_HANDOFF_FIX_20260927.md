# SAM2 success → Pixi mask handoff runtime fix

- Evidence ID: E-030-FIX-006
- Timestamp: 2026-09-27 15:00 UTC
- Reviewer: Codex implementation review; owner requested diagnosis and fix.
- Input: owner screenshot with Lightning log `sam21_segmentation_completed status=SUCCEEDED target=anchor-entity-1 confidence=0.858` and Android intro stuck at `Đang mở…`/showing the original image.

## Diagnosis

SAM2 had produced a subject mask and the backend had stored its descriptor, but `Renderer V2` only checked for the descriptor. It never retrieved or decoded the mask. The subject-only package was therefore rendered using heuristic bbox/archetype crops rather than the SAM silhouette. Separately, renderer load exceptions were not consistently sent to the native screen, so the intro could remain at zero duration until its timeout.

## Changes

- Added a separate, short-lived `X-Rig-Mask-Capability` read path for the package's exact derived mask; both package and mask grants are bounded and session/hash checked.
- Added optional mask endpoint/capability/digest fields to the additive Renderer V2 launch/load contracts. Legacy V2 launch payloads remain parseable.
- The WebView now verifies source, package and mask SHA-256 values, source/mask dimensions and mask provenance before constructing cutout layers. The source drawing is never modified.
- `CUTOUT_MICRO_MOTION` now animates a SAM-derived subject layer instead of hard-coded butterfly wing slices. A background patch is permitted only after bounded corner samples validate near-uniform neutral paper; unsafe/invalid masks downgrade to V1.
- Metadata-only part proposals are explicitly kept below `FULL_AUTO_RIG` until independent part-mask assets are carried through the package and consumed by PixiJS.
- Added explicit duration-bearing fallback and playback-failure events so the mobile controls do not wait indefinitely at zero duration.

## Verification

Commands run from the repository root:

- `python -m pytest backend/tests/unit/test_auto_rig.py` — PASS, 23 tests. Includes the mask endpoint, digest/session capability, bounded replay and launch contract.
- `python -m ruff check ...` on changed Python files — PASS after formatting fixes.
- `pnpm --filter @sketch2life/art-renderer exec tsc --noEmit -p ../../apps/ui-mobile/tsconfig.json` — PASS.
- `pnpm --filter @sketch2life/art-renderer typecheck` — PASS.
- `pnpm --filter @sketch2life/art-renderer test` — PASS, 28 tests across 5 files.
- `pnpm --filter @sketch2life/art-renderer build:demo` — PASS; generated `dist-demo` is ignored build output.
- `python -m compileall -q` on changed backend modules — PASS.
- `python tools/validate_repository_security.py` — PASS.

## Limitations / follow-up

- `python -m pytest backend/tests/contract/test_live_image_demo_api.py -q` could not collect because this machine's Python environment lacks optional dependency `av` (PyAV). The new mask HTTP route itself is exercised through an isolated FastAPI test in the passing focused unit suite.
- `python tools/validate_harness.py` reports a pre-existing unrelated missing-path issue under `features/FEAT-026-current-system-srs` (`evidence/raw` and `evidence/metrics`); this task did not alter that feature.
- No Android emulator or live Lightning worker was available for visual retest in this run. The local source/build path is verified, but runtime confirmation on the owner's device is still required.
- Pytest emitted existing Starlette/httpx deprecation and cache-directory warnings; test assertions passed.
