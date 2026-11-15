# EV-063-107 — Parent guide drawn from the exact source SVG paths

**Date:** 2026-11-14<br>
**Plan:** Rev87.11-H, approved; it supersedes the V6 hand-authored geometry in Rev87.11-G.<br>
**SRS:** FEAT-063 v2.7-draft; §§1–31 unchanged, §32 records this as-built result only.

## Result

V6 did not meet the owner's request: its 24 custom paths and thick 512-unit strokes made the chicken look like a child's drawing and did not reproduce the pinned illustration. V6 and its evidence are preserved as history; the active pinned-chicken path is now V7.

V7 does not ask Qwen to redraw this supported topic. It loads the pinned Arcadia Gallus gallus SVG and uses the exact `d` geometry from all 77 source paths. The V7 manifest contains only provenance, path IDs, eight teaching labels/instructions, and stage order. The guide document converts source regions into unfilled line strokes; it does not add, simplify, scale, or substitute path geometry. The original colored illustration stays in a separate view.

## Route verification

The local Parent route was called through FastAPI TestClient inside the existing API Docker image. Only identity and database dependencies were overridden; the route implementation, source loader, sanitizer, contracts, and response serialization were real. A Modal-client guard failed the run if a Modal request was attempted.

| Check | Result |
|---|---|
| Request | `POST /api/parent/v1/ai/sketch-guides`, topic `gà mái` |
| HTTP / elapsed | 200 / 0.090 s |
| Response | `SvgTopicStrokeGuideSourceDraftV1`, engine 7.0.0 |
| Source / guide paths | 77 / 77 |
| Exact source `d` matches | 77/77 |
| Stage assignment | 77/77 paths, each exactly once across 8 steps |
| Modal dispatched | No |
| Persisted / review | Not persisted; adult review required |
| Source SHA-256 | `4f6397d5d32ff7ea58451cb5e5725c87501be155c0eb64f85c5821dfe99cb1ed` |
| V7 manifest SHA-256 | `22eb7e077416b64db52b65ede1a45b584e1315a96d1b7e1ac110118510e532c6` |
| Guide document SHA-256 | `29180d272469e9f25b964654943c12680f65c5010c6c67fdff978d3e051ab0e3` |

The route is a focused local contract check, not Firebase authentication, Android E2E, a published guide, or educator approval. Unsupported topics retain the existing Qwen/Modal route and its validation gates.

## Rendering and UI behavior

All eight cumulative route responses were rendered at 1024×1024 and visually inspected. The final guide clearly depicts the same left-facing chicken: matching outer silhouette, head/comb/beak, body, wing/tail, feather detail, and feet. It is line art, so it intentionally has no source fills; the unchanged full-color source is available separately and is never used as an underlay. The current step is blue, completed paths are dark, and future paths are hidden. After the animation finishes, the current step remains visible as a completed dark outline.

The source paths use lowercase relative curves and other SVG commands. The old mobile path-length estimator did not parse those commands, which could leave a dash animation incomplete. The estimator now handles absolute and relative move/line/curve/horizontal/vertical/smooth/arc/close commands. The new test measures all 77 paths from the pinned product dataset.

Generated evidence files in this folder:

- `parent-svg-guide-response.json` — actual route response.
- `parent-chicken-v7-step-1.svg` … `parent-chicken-v7-step-8.svg` and matching `*-1024.png` files — cumulative stages.
- `parent-chicken-v7-final-line-guide.svg` and `parent-chicken-v7-final-line-guide-1024.png` — completed line guide.
- `parent-chicken-v7-reference.svg` and `parent-chicken-v7-reference-1024.png` — separate original-color reference.
- `runtime-attempt.json` — status, timing, hashes, source identity and Modal dispatch state.
- `run_parent_chicken_v7_api.py`, `render_svg_evidence.ps1` — reproducible local route and render steps.

## Verification

- Backend: focused V7 unit and Parent route contract tests **9/9 passed** in a disposable container from the existing API image. The container installed pytest ephemerally and exited after testing. Backend `compileall` passed.
- Parent mobile: source-guide and SVG path-length tests **8/8 passed**. The path-length tests include all 77 paths in the pinned source SVG.
- `git diff --check`: passed for the scoped tracked files.
- Full mobile typecheck: still reports existing `EXPO_PUBLIC_*` environment declaration errors in `src/config/apiConfig.ts`, `src/demo/api.ts`, and `src/parent/infrastructure/config.ts`; no changed guide file is reported. `pnpm run typecheck` itself also hit a worktree `realpath` EPERM, so `tsc` was invoked directly.
- Not run: Android emulator/Firebase end-to-end. No Modal deploy/inference, GPU call, database operation, account/consent/seed change, `.env` edit, or shared-service restart.

## Boundary

The V7 guide covers only the pinned chicken aliases. This does not claim every topic's AI guide is fixed. The result remains an adult-reviewable private draft; no educator review or catalog publication is claimed. SRS §§1–31 remain unchanged and the SRS remains unsigned.
