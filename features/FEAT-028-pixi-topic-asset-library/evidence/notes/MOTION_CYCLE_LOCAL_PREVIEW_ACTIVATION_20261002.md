# Local Pixi sprite-cycle preview activation — 2026-10-02

## Decision and scope

The project owner directly authorized enabling new sprites in the runtime. This activation is a
server-controlled local/test preview only. It does not clear rights, change the production runtime
gate, or enable any cycle outside the explicit applied catalog. The full ImageGen-returned prompt
records are preserved in `MOTION_SPRITE_GENERATION_PROVENANCE_20261002.json`.

## Technical QA

- Reproduce with `backend/.venv/Scripts/python.exe features/FEAT-028-pixi-topic-asset-library/evidence/scripts/qa_motion_sprite_cycles.py` from the repository root.
- Input: the 37-cycle generated manifest, the 37-record prompt provenance file, generated source PNGs,
  and approved copies. Output: `../metrics/MOTION_CYCLE_QA_20261002.json`.
- The audit verifies provenance/output-ID and SHA-256 correspondence, generated/approved hash parity,
  canvas and grid crop geometry, alpha-channel/corner state, per-frame alpha bounds and non-empty
  count, minimum visible-edge inset, 32×32 alpha-shape IoU for sequential/loop-seam pairs, and
  normalized alpha-centroid drift as a placement-stability proxy. This proxy is not a semantic rig
  pivot measurement. It is deliberately used only as a local-preview filter.
- Technical preview thresholds: four non-empty frames; minimum alpha inset 1.5% of the smaller cell
  dimension; each adjacent/seam alpha IoU below 0.98; maximum normalized alpha-centroid drift 0.20;
  exact source/manifest/approved hashes and matching provenance output ID.
- Candidate results: `motion.walker-avian.v1` passes (23 px / 4.24% minimum inset, 4/4 frames,
  0.0342 max centroid delta); `motion.walker-corgi.v2` passes local preview checks (10 px / 1.64%,
  4/4 frames, 0.0878 centroid delta). Both PNGs in `assets/applied/` are byte-identical to the
  approved source sheets.
- `motion.flyer-songbird.v2` is blocked: normalized alpha-centroid drift is 0.2306 (threshold 0.20).
  Its approved source remains preserved; the temporary preview copy is preserved in
  `evidence/raw/` and is not in the applied catalog. The butterfly/caterpillar sheets have zero
  visible-edge inset in at least one frame, the goldfish falls below the inset threshold, the child
  sprite falls below the inset threshold, and the car has near-duplicate alpha poses. These remain
  unavailable rather than being silently substituted.
- This is a conservative local QA screen, not a statement that all other sheets are unusable. They
  require asset-specific alignment/repair and another review before a future activation.

## Runtime change

- Added `SKETCH2LIFE_PIXI_SPRITE_CYCLE_DEV_PREVIEW_ENABLED`, default `false`; application wiring
  honors it only for `SKETCH2LIFE_ENV=local|test`. Staging/production cannot open this path.
- In preview mode, the capability service requires the dedicated local-preview catalog and reads
  exact-hash-verified sheets from `assets/applied/`. The original strict manifest gates remain the
  only path when the flag is off. Manifest production `runtimeEligible` and rights values are not
  changed.
- The applied catalog contains only the walker-avian and walker-quadruped cycles. The existing
  closed subject/behavior compiler remains unchanged; no new model-provided IDs or behavior mapping
  are accepted.
- Safe backend logs identify the cycle, behavior class, frame count, and either
  `LOCAL_DEV_PREVIEW` or `CLEARED_RUNTIME`; no prompt, image payload, or capability is logged.

## Verification and remaining acceptance

Verification performed 2026-10-02:

- `backend/.venv/Scripts/python.exe -m pytest -p no:cacheprovider --basetemp=backend/.pytest-tmp-sprite-activation backend/tests/unit/test_pixi_motion_cycles.py backend/tests/unit/test_settings_security.py` — 22 passed.
- Focused Ruff check across the preview gate, HTTP wiring, tests, and QA script — passed.
- `qa_motion_sprite_cycles.py` — 37 provenance records verified; exactly the avian walker and corgi walker pass the preview thresholds; songbird flyer and other failing candidates stay blocked.
- Renderer suite: 57 tests passed; renderer typecheck and demo build passed. Mobile UI-copy/recovery test passed.
- Backend `GET /health` — HTTP 200. Metro Android bundle — HTTP 200, 8,393,141 bytes, app entry present.
- The app loaded the served Metro bundle on the running Android emulator without the earlier wrong-workspace-root or renderer-package-resolution failure. A complete image-to-Pixi session was not run to visible sprite playback in this verification, so Android motion acceptance and formal renderer verification remain pending.

The local preview cycles are available only when `SKETCH2LIFE_ENV=local|test` and
`SKETCH2LIFE_PIXI_SPRITE_CYCLE_DEV_PREVIEW_ENABLED=true`. The latter defaults off. During final
runtime inspection, the existing Pixi show planner was found disabled, which prevented the normal
flow from reaching the cycle issuer. The local backend was restarted with
`SKETCH2LIFE_PIXI_SHOW_PLANNER_ENABLED=true` as well; readiness probes do not submit an image or
invoke the planner. Proceeding through the image flow will use the already configured AI planner.
Staging and production remain on the existing strict manifest gates. No commit or push was made.

The app-root Metro configuration and `EXPO_NO_METRO_WORKSPACE_ROOT=1` startup setting were added
after reproducing two development-server failures: Metro first resolved the monorepo root instead
of `apps/ui-mobile`, then could not resolve the pnpm-linked shared renderer's `@babel/runtime`.
The corrected workspace package paths yielded a successful Android bundle. No credentials or child
media were included in evidence.
