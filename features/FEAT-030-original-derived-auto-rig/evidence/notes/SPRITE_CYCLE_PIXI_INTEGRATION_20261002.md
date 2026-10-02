# Sprite-cycle Pixi renderer integration — 2026-10-02

- Evidence ID: E-030-CYCLE-016.
- Feature/task: FEAT-030 additive sprite-cycle sidecar with FEAT-028 asset lifecycle.
- Owner approval: direct implementation request and visual approval are recorded in
  `../../approvals/TASK_APPROVAL.md`; the exact plan/hash is in the 2026-10-02 cycle integration entry.
- Environment: local Windows checkout, branch `codex/pixi-ai-show-20261001`; no Android device or
  emulator was used for this offline verification. Evidence finalized 2026-10-02 10:47:31 +07:00
  (Asia/Saigon).

## Implemented

- Kept V1/V2/V3 renderer contracts intact and added cycle-read V1, show-envelope V2, and renderer
  command V4 with closed behavior IDs, exact ordered frame IDs, bounded timing/scale/placement, and
  family compatibility checks in matching Python and TypeScript schemas.
- Backend cycle reads are allowlisted by the FEAT-028 manifest, require independent visual, rights,
  frame-QA, catalog, renderer, and runtime gates, verify the approved-copy hash/canvas/layout, crop
  exact atlas cells, cap PNG bytes, and issue short-lived read capabilities. Gate failure is a typed
  reason with no frame capabilities. Logs report safe gate decisions, capability issuance, and
  successful cycle-frame reads; tokens, image data, source IDs, crops, prompts, and URLs are omitted.
- The show compiler selects only deterministic subject/behavior-compatible cycles and safe stage
  corners outside padded source bounds/static companion sprites; it returns `NO_SAFE_PLACEMENT`
  instead of overlapping. The current show contract still has six coarse behavior values, so its
  deterministic selector intentionally covers only supported mappings (bird, insect, fish,
  quadruped, biped, vehicle). It does not invent plant/object/scene motion from `STATIONARY`; the
  29-class registry is not yet a per-beat AI selector contract.
- Pixi verifies response type, byte length, hash, and decoded dimensions; frame timing follows the
  existing playback clock (no second ticker), keeping seek/pause/replay deterministic. Teardown
  releases cycle containers/textures, including failure cleanup. Logs use `[pixi-cycle]` and safe
  reason codes only.

## Verification

- Full backend suite (exit 0; pytest storage outside the repository):

  ```powershell
  .\backend\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp "$env:TEMP\sketch2life-pytest-pixi-full-20261002" backend/tests -q --tb=short
  ```

- Focused cycle/asset/show tests: 25 passed:

  ```powershell
  .\backend\.venv\Scripts\python.exe -m pytest -p no:cacheprovider --basetemp "$env:TEMP\sketch2life-pytest-pixi-focused-20261002" backend/tests/unit/test_pixi_motion_cycles.py backend/tests/unit/test_pixi_motion_cycle_compiler.py backend/tests/unit/test_pixi_show_assets.py backend/tests/unit/test_pixi_show_planner.py -q --tb=short
  ```
- Focused cycle/asset/show tests — 25 tests passed, including all six independent runtime-gate
  failures before any capability is created, malformed requests, frame integrity/expiry, safe
  placement, compatible cycle selection, and no invented still-subject motion.
- `pnpm -r test` — renderer: 57 passed; mobile bridge: 7 passed; UI-copy validation passed.
- `pnpm -r typecheck` — renderer and `apps/mobile` typechecks passed. The `apps/ui-mobile` package has
  no typecheck script, so its touched bridge/context sources were separately checked with:

  ```powershell
  pnpm --filter @sketch2life/art-renderer exec tsc --noEmit -p ../../apps/ui-mobile/tsconfig.json
  ```

  This command passed.
- `pnpm --filter @sketch2life/art-renderer build:demo` — Vite demo build passed.
- Focused Ruff and `git diff --check` — passed. Ruff command:

  ```powershell
  .\backend\.venv\Scripts\python.exe -m ruff check backend/src/sketch2life/infrastructure/catalog/pixi_show_assets.py backend/src/sketch2life/contracts/schemas/pixi_motion_cycle.py backend/src/sketch2life/application/services/pixi_motion_cycle_compiler.py backend/tests/unit/test_pixi_motion_cycles.py backend/tests/unit/test_pixi_motion_cycle_compiler.py
  ```
- Source/approved asset integrity check — 37 sheets checked against manifest and each other; 0 hash
  mismatches (visual approval evidence is separately recorded under FEAT-028).
- `.\backend\.venv\Scripts\python.exe tools/validate_repository_security.py` — passed after removing a local machine path from
  the related evidence note.
- `.\backend\.venv\Scripts\python.exe tools/validate_harness.py` — global harness remains
  `HARNESS_INVALID` because FEAT-026, FEAT-033, and FEAT-034 lack unrelated required evidence
  subdirectories; FEAT-028 and FEAT-030 report no missing harness paths.

## Gate state and limitations

The checked-in expansion manifest remains closed: rights `REVIEW_REQUIRED`, crop/pivot/loop
`NOT_QA_VERIFIED`, catalog `NOT_REGISTERED`, renderer `NOT_VERIFIED`, runtime eligibility false.
Full prompt transcripts are not archived. Therefore no motion-cycle capability can currently be
issued for these sheets and no new sprite can play in a live app. No backend service, frontend, or
emulator was started for this verification; fresh Android visual acceptance and actual Pixi playback
remain unverified. Offline build/tests are not production or rights approval.
