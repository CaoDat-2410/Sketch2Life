# Current runtime audit — 2026-09-25

## Scope

Read-only audit of the current supervised flow, mobile Pixi introduction, backend renderer preparation, schemas, renderer, storage primitives, AI adapter, and asset governance. No runtime files were modified.

## Findings

1. Gate B is approved in `ExperienceReviewScreen`, then mobile navigates to `PixiIntroScreen` and calls `prepareRendererIntro()`.
2. Backend `prepare_renderer()` constructs `ArtAnimationPlanV1`, `PixiArtAssetManifestV1`, and `PixiRendererLaunchV1` from the original image and optional validated focus regions.
3. The ordinary app composition intentionally injects no scene localizer. This avoids the previous second Qwen geometry request and leaves whole-drawing fallback active.
4. The generated V1 plan animates a sprite/crop with reveal, scale, movement, and rotation. It does not segment a subject, build a mesh, create bones, compute weights, or deform pixels.
5. The renderer fetches the original through a short-lived capability and builds Pixi sprites. GSAP drives the closed V1 motion DSL.
6. `RendererLoadCommandV1` has a small bridge envelope and original-source URI rules. Mesh arrays cannot safely be inlined through the current 4096-byte message limit.
7. Raw understanding entities do not contain boxes, masks, or keypoints. Existing Qwen output mapping accepts semantic observations only.
8. A localization port and Lightning adapter exist, but the endpoint has previously produced invalid geometry/503s and is disabled by default. It is not a segmentation implementation.
9. Job, artifact, and idempotency store abstractions can be reused, but there is no auto-rig job orchestration, worker, derived-artifact cache, or rig package capability.
10. Python runtime dependencies do not currently include a segmentation model, OpenCV, scikit-image, SciPy, or mesh/rigging libraries. The renderer has PixiJS, GSAP, and Zod only.
11. Current renderer completion is a local WebView bridge event. The backend session advances to handoff only when the later handoff command is invoked.
12. Approved supplemental assets and original-derived artifacts have different trust semantics. A dedicated derived-artifact category/policy is missing.

## Interpretation

The requested result is not a tuning change to existing Pixi motions. It is an additive cross-runtime subsystem. The safe migration path is a versioned V2 package loaded by capability, with V1 preserved as the final fallback and feature-flag rollback.

## Limitations

- No model benchmark or dependency installation was performed.
- No child media was inspected or stored.
- Latency and memory targets in the plan are provisional until measured on the Lightning L4 and target Android devices.
