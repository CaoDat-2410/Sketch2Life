# Sprite visual cohesion follow-up — 2026-10-05

## Change under test

- The QA-passed `motion.walker-corgi.v2` local preview is positioned at normalized stage
  `(0.78, 0.58)`, scale `0.30`, for seconds `0–4`; it stays outside the synthetic source-dog
  region and no longer floats in the upper-left corner.
- Pixi now adds `AutoRigPlayer.getSubjectTranslation()` to the cycle position. That value is the
  same root-pose plus show-beat translation used to place the source cutout, so the companion
  sprite follows vertical/root movement without changing the cycle's frame timing.
- The previous screenshot `pixi-corgi-preview-before-grounding-20261005.png` is deliberately
  labeled as pre-fix evidence; it shows the original detached placement.

## Visual and interaction check

- Served `packages/art-renderer/dist-demo/mobile.html` through the local synthetic fixture at
  `http://127.0.0.1:8002/`; no live AI/provider call or child media was used.
- Browser rendered the original synthetic dog and the capability-read corgi sprite together.
  At `PAUSED 2.10s / 20s` and after seeking to `PAUSED 1.00s / 20s`, the sprite remained beside
  the dog's right side and clear of the status label. A fresh replay at `PLAYING 0.00s / 20s`
  followed by seek to `PLAYING 1.00s / 20s` also visibly showed the dog and sprite changing height
  together. They share the source translation; the source artwork remained centered and visible.
- Replayed, then sought while already playing; the bridge immediately showed `PLAYING 1.00s / 20s`,
  confirming the seek flush bypasses the 250 ms ordinary-progress throttle.
- Pixi diagnostics reported cycle `loading`, `decoded` (`4` frames), `ready`, `playing`, and
  frame progression. The browser screenshot was visually inspected inline during the run; the
  CUA browser surface did not provide a repository-file export, so no post-fix binary screenshot
  is claimed here.

## Regression results

- `pnpm -r test`: renderer 64, app mobile 7, UI mobile 22 — all passed.
- `pnpm -r typecheck`: renderer, app mobile, and UI mobile — all passed.
- Backend final rerun: `1,768 passed, 6 skipped`; the five initial P1 failures from the first
  typing-refactor run were fixed and all five focused regressions passed first. On Windows, pytest
  used an isolated workspace `--basetemp` and `PYTHONPATH` for repository-level fixture imports.
- Strict mypy: 193 source files, zero issues. Ruff check and formatter check pass for all changed
  Python files.
- Renderer demo production build, Ruff check/format, harness, skeleton, architecture, team
  allocation, and `git diff --check` passed.
- The current emulator's bundled artwork was confirmed earlier. Shared-motion Pixi composition
  in Android WebView is not claimed as emulator-verified; the visual acceptance above is the
  local browser renderer fixture.
