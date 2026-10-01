# Pixi show offline implementation — 2026-10-01

## Scope and approval

- Feature: FEAT-030, Pixi sprite show and AI motion matching.
- Branch: `codex/pixi-ai-show-20261001`.
- Implemented against approved plan revision 4; pre-approval SHA-256:
  `04DD49A6AC903052BDD3DBB674EE85A5537C642330CFF9F09E5170662B98FEEA`.
- ADR: `../adr/ADR-030-08-pixi-show-planning.md`.
- No live Qwen/Lightning/SAM request, asset promotion, backend restart, emulator run, or Android
  visual acceptance was performed.

## Implementation record

- Added versioned `PixiShowIntentV1`, `PixiShowPlanV1`, `PixiRendererShowEnvelopeV1`, planner request,
  and `RendererLoadCommandV3` contracts. Existing V1/V2 wire contracts remain unchanged.
- Added provider-neutral planner port, deterministic allowlist/capability validator, renderer motion
  compiler, single-request Lightning/Qwen adapter, and bounded transient source-subject crop.
  Planner and Lightning show endpoint are independently disabled by default. Errors are typed,
  sanitized, and preserve the original; there is no automatic retry, V1 fallback, or substitute show.
- Added asset capability issuance that requires an approved, applied, rights-cleared, runtime-eligible
  catalog frame; Pixi checks content type, exact byte length, and SHA-256 before creating textures.
  Current catalog rights state yields no eligible runtime frames, so actual sprite composition
  intentionally remains unavailable.
- Replaced nearest-anchor/Voronoi mask splitting with bounded connected-color component proposals
  inside the verified parent mask. Anchors label only components supported by source boundary/area
  evidence; same-color silhouettes produce no part proposals. Synthetic tests prove containment and
  disjoint output, not real-world anatomy accuracy.
- Mobile consumes the new show envelope additively and dispatches the validated V3 renderer message.
  Static sprites support only visual notice/approach/interaction/settle beats; articulated behavior is
  rejected unless source-derived parts match the behavior class. The source remains the lead artwork.

## Existing asset gap audit

Catalog source: FEAT-028 `assets/generated/asset-catalog.v2.json`, catalog version 2.0.0. Metadata
reports 144 entries across 24 atlases/families, with 6 entries per family. Render-role counts are
69 `SUBJECT`, 51 `PROP`, 18 `ENVIRONMENT`, and 6 `EFFECT`. The entries are individual static frames;
the catalog does not define multi-frame walk, wing-flap, swim, crawl, or roll animation sequences.
The existing visual approval covers those 144 frames only; rights clearance/runtime eligibility
remain separate and pending.

| Behavior class | Catalog evidence | Motion-ready gap | First draft |
|---|---|---|---|
| Walker | People and multiple quadruped SUBJECT entries; all are single-pose frames | No authored walk cycle; whole static sprites cannot claim gait | Four-pose corgi-like quadruped sheet; review pending |
| Flyer | Songbird, butterfly, insects, and pteranodon SUBJECT entries; single poses | No authored wing-flap cycle | Four-pose songbird flap sheet; review pending |
| Swimmer | Fish and ocean-life SUBJECT entries; single poses | No swim cycle | No new draft in this increment |
| Crawler/slitherer | Snail, caterpillar, and other organic SUBJECT entries; single poses | No crawl/slither cycle | No new draft in this increment |
| Roller | Vehicle SUBJECT/PROP entries and sports props; single poses | No rolling/wheel cycle | No new draft in this increment |
| Stationary/scene support | Many static environment, prop, and effect entries | Static beat use remains rights/runtime-gated; no loops implied | Existing visual review does not clear runtime rights |

This metadata audit does not assert that every depicted animal supports a specific gait. The two new
draft sheets are in FEAT-028 `assets/generated/`; each frame still requires visual approval, frame
registration, provenance review, and rights clearance before it can be catalogued or referenced.

## Verification

- Backend: `.\backend\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider backend\tests --basetemp .codex-test-tmp-feat30-20261001-d --tb=short` — all tests completed at 100%; no failures. Task-created pytest scratch data was removed after the run.
- Part-mask focused regression: `.\backend\.venv\Scripts\python.exe -m pytest -q -p no:cacheprovider backend\tests\unit\test_part_masks.py` — 10 passed.
- `pnpm -r typecheck` — passed (renderer and mobile TypeScript).
- `pnpm -r test` — passed (53 renderer tests; 7 mobile tests; UI copy validator passed).
- `pnpm --filter @sketch2life/art-renderer build:demo` — passed.
- Focused backend Ruff — passed.
- `python -m py_compile tools\lightning_vision_v2_server.py` — passed.
- `python tools\validate_repository_security.py` — passed after removing task-created pytest scratch files.

## Remaining gates and limitations

- New dog/bird motion sheets are drafts, not visually approved, not per-frame catalog entries, not
  rights-cleared, and not runtime-eligible. Existing approved catalog frames also remain rights-gated.
- No full caregiver subject-reconfirmation round-trip was exercised for a planner subject disagreement;
  the backend emits `SUBJECT_RECONFIRMATION_REQUIRED`, but an end-to-end workflow reset/reconfirmation
  path must be completed before live planner activation.
- No live provider call, retention/privacy review, L4 latency/VRAM benchmark, actual sprite composition,
  emulator/device playback, or Android visual sign-off. Keep both runtime flags disabled until those
  gates and exact asset approvals are complete.
