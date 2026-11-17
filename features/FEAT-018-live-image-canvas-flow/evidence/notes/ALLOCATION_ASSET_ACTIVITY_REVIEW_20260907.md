# Allocation, Pixi asset, and activity review — 2026-09-07

## Findings

- ADR-0006 Sprint 1 allocation remains four independent contract streams. FEAT-018 is a separate integration allocation and must not inherit P3/P4 application ownership automatically.
- `packages/art-renderer` declares PixiJS 8 and GSAP 3, but currently exports only the protocol constant and bootstrap type. No Pixi scene/player, WebView bridge, or approved visual asset is present.
- The main repository has only `.gitkeep` under `data/curated-assets` and the feature asset folders. The controlled drawing available for fixtures is `features/FEAT-015-integration-readiness-review/fixtures/integration-fixture-v1/media/drawing.svg` plus narration audio.
- The reviewed P1 worktree contains a 100-activity MVP catalog, 20 learning objectives, and a 20-activity golden candidate catalog. Those catalog files are not promoted into the main runtime; the current app still hardcodes `ACT-0004` and `OBJ_MOVEMENT_COORDINATION`.
- Golden `ACT-0004` maps primarily to `OBJ_OBJECT_PERMANENCE` and secondarily to `OBJ_RECEPTIVE_LANGUAGE`, so the current fixture identity is semantically inconsistent and must be corrected before activity expansion.

## Proposed FEAT-018 allocation for approval

- Person 1: promote the versioned catalog/objective package, define the pilot activity set and mapping contract, and own Gate-B identity/version checks.
- Person 2: image quality validation, Qwen3-VL structured observation, missing-narration provenance, and observation-to-candidate mapping diagnostics.
- Person 3: PixiJS/GSAP scene player, WebView bridge, source-preserving reveal, asset manifest, and renderer evidence.
- Person 4: cache/fallback contracts, reviewed media lookup, device fixture matrix, and sanitized evidence. Backend/session orchestration and full E2E remain a separately approved shared integration task; they are not silently assigned to Person 4.

## Asset decision

- User-provided non-sensitive image is a runtime source artifact, kept outside Git and represented by hash/provenance only.
- Pixi pack must contain source texture reference, optional derived mask/regions, versioned scene/motion manifest, fallback still, and bridge protocol evidence.
- Generated frontend visuals, if needed, go through `assets/generated` -> review record -> `assets/approved` -> `assets/applied`; nothing is applied directly.

## Activity recommendation

- Do not add all 100 activities for the first live-image run. Promote and test 3-5 pilot records after correcting the ACT-0004 identity.
- Suggested pilots: ACT-0004 object permanence, ACT-0016 transfer between bowls, ACT-0019 handwashing sequence, ACT-0023 watering a plant, and ACT-0055 plant observation.
- Add more records only after catalog/objective mapping, explicit adult context (age/readiness/materials/supervision), and Gate-B version checks are working.
