# FEAT-030 evidence index

## Current evidence

| Evidence ID | Criterion/task | Type | Artifact | Status |
|---|---|---|---|---|
| E-030-AUDIT-001 | Establish current renderer and supervised-flow baseline | Architecture review | `notes/CURRENT_RUNTIME_AUDIT_20260925.md` | COMPLETE_FOR_PLANNING |
| E-030-IMPL-001 | V2 contracts, package capability, rig registry, Pixi CPU skinning, Android preference/fallback | Implementation/test review | `notes/IMPLEMENTATION_20260925.md` | PASS_WITH_RECORDED_LIMITATION |
| E-030-FIX-002 | Android HTTP WebView package-integrity compatibility | Runtime diagnosis and regression tests | `notes/ANDROID_WEBVIEW_SHA256_FIX_20260926.md` | PASS_PENDING_VISUAL_RETEST |
| E-030-REV3-003 | Functional controls, 12-second motion, subject isolation and butterfly part composition | Implementation and regression review | `notes/REVISION3_PART_AWARE_BASELINE_20260926.md` | PASS_PENDING_ANDROID_VISUAL_REVIEW |
| E-030-R4-PLAN-004 | Single-L4 AI-assisted semantic-part rigging candidate and delivery plan | Source/architecture review | `notes/REVISION4_AI_SEGMENTATION_PLAN_20260926.md` | APPROVED_AND_IMPLEMENTED_WITH_BENCHMARK_PENDING |
| E-030-R4-IMPL-005 | Typed SAM2.1 worker route, backend adapter, bounded prompt proposal and mask provenance | Unit/contract review | `notes/REVISION4_SAM21_IMPLEMENTATION_20260926.md` | PASS_UNIT_TESTS_BENCHMARK_PENDING |
| E-030-FIX-006 | SAM2-success mask handoff, verified Pixi cutout motion and explicit renderer failure/fallback lifecycle | Focused backend/renderer regression, typecheck and bundle build | `notes/SAM2_SUCCESS_MASK_HANDOFF_FIX_20260927.md` | PASS_LOCAL_CHECKS_PENDING_ANDROID_LIGHTNING_VISUAL_RETEST |
| E-030-FIX-007 | Early bootstrap, idempotent native-to-WebView launch replay, startup failure reporting and stage-aware timeout | Emulator root-cause reproduction, renderer unit/type checks, mobile typecheck and bundle build | `notes/PIXI_STARTUP_HANDSHAKE_FIX_20260928.md` | PASS_LOCAL_CHECKS; POST-FIX_ARTIFACT_FLOW_PENDING |
| E-030-FIX-008 | SAM2.1 part-mask handoff, deterministic mask partition fallback, separate Pixi part sprites, 20s multi-beat/rest timeline, contain-fit framing and backend mask-source diagnostics | Focused synthetic backend/runtime/renderer tests, typecheck and production demo build | `notes/PIXI_PART_MOTION_RESTORATION_20260929.md` | PASS_OFFLINE_CHECKS; LIVE_MASK_QUALITY_AND_ANDROID_RETEST_PENDING |
| E-030-FIX-009 | Consume verified `CUTOUT_MICRO_MOTION` packages without requiring part masks; preserve strict `FULL_AUTO_RIG` gate | Android console diagnosis, renderer tests/typecheck/build, backend restart and HTTP probes | `notes/CUTOUT_TIER_CONSUMPTION_FIX_20260929.md` | PASS_LOCAL_CHECKS; FRESH_ANDROID_FLOW_PENDING |
| E-030-FIX-010 | Mask-bounded cutout inpainting, no automatic V2-to-V1 fallback, Gate-A/Gate-B/Pixi loading surfaces and earlier package preparation | Android logcat diagnosis, renderer/mobile tests and checks, bundle build and backend probes | `notes/NO_V1_FALLBACK_PRELOAD_INPAINT_20260929.md` | PASS_LOCAL_CHECKS; FRESH_ANDROID_VISUAL_AND_WEBGL_RETEST_PENDING |
| E-030-FIX-011 | High-pigment cutout edge artifacts; likely color contamination during inpainting, mask-vs-renderer attribution still unverified | Owner screenshot review and source inspection; no matching live source/mask logs | `notes/HEAVY_PIGMENT_CUTOUT_DIAGNOSIS_20260929.md` and `notes/INTEGRATED_MASK_AND_CUTOUT_QUALITY_20260929.md` | SYNTHETIC_IMPLEMENTATION_AND_OFFLINE_TESTS_PASS; REAL_DRAWING_AND_ANDROID_RETEST_PENDING |

## Planned evidence groups

- Contract parity: Python and TypeScript golden fixtures, schema round trips, rejected-version fixtures.
- Model quality: authorized synthetic/golden drawings, exact model/config revision, masks/regions, IoU or reviewer score, failure taxonomy.
- Rig quality: topology, weights, deformation bounds, fold-over count, edge preservation, fallback reason.
- Performance: queue, model, geometry, package fetch, renderer load, first-motion, FPS, memory, package bytes, cache hit rate.
- Behavior: state-machine tests, idempotency, retries, timeouts, capability expiry, V1 fallback, old-client compatibility.
- Visual: screen recordings and screenshots on named Android devices/emulators, with source fixture and expected motion profile.
- Security/privacy: no credentials or child media in Git/logs; capability replay/expiry tests; artifact deletion and session isolation.

Every result must include command/input, environment/device/model/config, timestamp, output path, reviewer, interpretation, and limitations.

Documentation-only mask-quality diagnosis (no model/runtime call):
[SAM 2.1 mask-quality audit](notes/SAM21_MASK_QUALITY_DIAGNOSIS_20260929.md) is the pre-implementation
baseline. The approved integrated workstream and current offline evidence are in
[`SAM21_MASK_ACCURACY_AND_AUTO_RIG_QUALITY_PLAN_20260929.md`](../plan/SAM21_MASK_ACCURACY_AND_AUTO_RIG_QUALITY_PLAN_20260929.md)
and [the implementation record](notes/INTEGRATED_MASK_AND_CUTOUT_QUALITY_20260929.md). Live SAM/L4,
real mask references and Android visual acceptance remain unverified.
