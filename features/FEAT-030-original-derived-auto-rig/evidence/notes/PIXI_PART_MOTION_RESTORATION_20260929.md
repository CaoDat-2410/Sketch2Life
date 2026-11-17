# Pixi part-motion restoration — offline implementation evidence

- Evidence ID: E-030-FIX-008
- Plan: `plan/PIXIJ_PART_MOTION_RESTORATION_20260928.md`
- Owner approval: `approvals/TASK_APPROVAL.md`, Pixi part-motion restoration — 2026-09-28
- Status: PASS_OFFLINE_CHECKS; LIVE_MASK_QUALITY_AND_ANDROID_RETEST_PENDING
- Verification date: 2026-09-29 (Asia/Saigon)

## Diagnosis addressed

The old V2 player used one whole-subject cutout or a static rectangular butterfly mesh, so no
independently segmented wing/body pixels reached separate renderer targets. Its completion callback
then started an infinite idle, while the V2-to-V1 fallback lasted 4.2 seconds and scaled/rotated the
whole drawing. The AI worker accepted requested part roles but previously returned only a subject
mask.

## Implemented behavior

- SAM2.1 receives one parent prompt plus a bounded set of archetype-role box prompts in one
`segment_many` call, reusing the encoded image. A rejected part prompt is omitted without discarding
an otherwise valid parent mask. The backend adapter stores the parent and each returned part as
separate source-session artifacts.
- Backend checks part confidence, role/bone mapping, PNG identity, dimensions, subject containment,
overlap and coverage before allowing `FULL_AUTO_RIG`. Missing/invalid SAM parts trigger deterministic
archetype-anchored partitioning of the already verified subject mask. This fallback partitions only
existing source pixels; unsupported/generic/rigid/unknown silhouettes stay lower-tier.
- Renderer V2 fetches each part through its short-lived capability and verifies artifact provenance,
digest, dimensions, mask containment, overlap and coverage again. It composes a separate alpha-masked
Pixi texture per part and animates each around its matching skeleton pivot. Whole-subject fallback
translation never scales or rotates the artwork. A failed/partial load clears its Pixi layers before
the legacy renderer takes over.
- The default V2 plan is 20 seconds. Motion keyframes end at 14.4 seconds and the last 5.6 seconds
holds the neutral pose; the previous unbounded completion idle is removed. The fixed-camera V1 Pixi
fallback totals 20 seconds with two small in-frame translations followed by a still hold; there is
no `SCALE` or `ROTATE` motion.

## Offline verification

Commands run from the repository/backend virtualenv and workspace:

- From `backend/`: `.venv/Scripts/python.exe -m pytest -p no:cacheprovider --basetemp .pytest-tmp-feat030-doccheck tests/unit/test_auto_rig.py tests/unit/test_lightning_sam21.py tests/unit/test_sam21_runtime.py tests/unit/test_sam21_runtime_config.py tests/unit/test_part_masks.py` — **41 passed, 1 skipped**. The skipped mocked SAM inference test requires NumPy, which is an optional model-runtime dependency absent from this local virtualenv; all deterministic segmentation/package/adapter/config tests passed.
- `python -m ruff check` over changed backend domain, adapter, runtime and tests — **passed**. The Lightning worker file was linted with existing file-level `E402` bootstrap imports and an unrelated long prompt line excluded.
- Focused mypy over six changed backend source files and `sam21_runtime.py` (with optional import-not-found diagnostics disabled) — **passed, no issues**. A repository-wide mypy attempt remains non-clean due unrelated existing contract/service typing errors and missing optional model-runtime stubs.
- `pnpm --filter @sketch2life/art-renderer typecheck` — **passed**.
- `pnpm --filter @sketch2life/art-renderer test` — **39 passed**.
- `pnpm --filter @sketch2life/art-renderer build:demo` — **passed**.
- `pnpm --filter sketch2life-mobile exec tsc --noEmit -p tsconfig.json` — **passed**.
- `python tools/validate_harness.py` — not clean because FEAT-026 is missing its pre-existing
  `evidence/raw` and `evidence/metrics` directories; no unrelated feature files were created or
  changed to mask this repository-wide finding.

Synthetic tests verify disjoint source-mask partitions for butterfly, bird, flower, tree, fish and
biped; no invented anatomy for generic/rigid/unknown; three distinct butterfly Pixi sprites with a
wing keyframe and neutral final hold; invalid part handoff clears partial sprites; and the V1
fallback has fixed scale/rotation, <=0.004 normalized translation, and a 20-second rest-ending plan.

## Limitations

No Qwen/SAM/Lightning request was issued, SAM activation/benchmark gates were not changed, and no
Android emulator/device visual smoke was performed. Synthetic masks prove contract/composition
behavior, not that SAM role boxes reliably isolate real child-drawn anatomy, that the deterministic
partition looks natural on diverse sketches, that background seams are visually acceptable, or that
the full part-mask flow meets L4 latency/memory targets. Those remain owner-run acceptance checks.

## Follow-up — fallback crop and backend diagnostics

The screenshot showed the original-art fallback rendering a full-resolution source texture at
scale 1, so Pixi displayed only the center crop on a smaller stage. Both the whole-art fallback and
the V2 renderer now contain-fit the source at 88% of the available stage while preserving aspect
ratio. Backend logs now identify whether part masks resolved from SAM2.1, deterministic image
processing, or neither. No backend terminal/log session was attached to this task, so the screenshot
does not reveal which backend branch the user's run took; this remains to be confirmed in its next
Uvicorn log.

Follow-up offline verification on 2026-09-29: renderer suite **42 passed**, renderer typecheck and
production demo build passed; targeted backend auto-rig/SAM/part-mask suite **38 passed, 1 skipped**;
backend Ruff check and repository security validator passed. No live provider request or emulator
visual retest was performed.
