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

## Planned evidence groups

- Contract parity: Python and TypeScript golden fixtures, schema round trips, rejected-version fixtures.
- Model quality: authorized synthetic/golden drawings, exact model/config revision, masks/regions, IoU or reviewer score, failure taxonomy.
- Rig quality: topology, weights, deformation bounds, fold-over count, edge preservation, fallback reason.
- Performance: queue, model, geometry, package fetch, renderer load, first-motion, FPS, memory, package bytes, cache hit rate.
- Behavior: state-machine tests, idempotency, retries, timeouts, capability expiry, V1 fallback, old-client compatibility.
- Visual: screen recordings and screenshots on named Android devices/emulators, with source fixture and expected motion profile.
- Security/privacy: no credentials or child media in Git/logs; capability replay/expiry tests; artifact deletion and session isolation.

Every result must include command/input, environment/device/model/config, timestamp, output path, reviewer, interpretation, and limitations.
