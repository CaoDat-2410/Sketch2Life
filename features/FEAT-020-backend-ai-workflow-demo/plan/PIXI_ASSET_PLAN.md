# FEAT-020 PixiJS Asset Repository Plan

## Goal

Create a complete, traceable starter asset repository for the current workflow without implementing PixiJS or generating assets at runtime. The backend will only select asset IDs and emit render intents; a future PixiJS bridge will load the approved local files.

## Asset policy

- Prefer hand-authored SVG/vector assets and deterministic code-native shapes.
- Do not call ImageGen, an image API, or a generative model during PixiJS playback.
- Preserve the child’s original drawing as the identity/source asset. Decorative butterfly/flower assets never replace it.
- Every asset has a stable `assetId`, semantic role, version, source policy, and intended workflow stage.
- Assets are currently in `assets/generated/` and remain `GENERATED_PENDING_REVIEW` until visual approval.
- Do not copy them to `assets/approved/` or `assets/applied/` before visual approval.

## Asset groups

| Group | Purpose | Asset IDs |
|---|---|---|
| Original-art context | Non-destructive context around the preserved child drawing | `pixi.scene.butterfly`, `pixi.scene.flower`, `pixi.scene.sun`, `pixi.scene.grass` |
| Motion language | Deterministic reveal/flight emphasis | `pixi.motion.sparkle`, `pixi.motion.path-dots` |
| Learning/activity | Materials, goal, supervision, safety and feedback context | `pixi.activity.material-basket`, `pixi.activity.learning-goal`, `pixi.activity.adult-guide`, `pixi.activity.safety-shield`, `pixi.activity.feedback`, `pixi.activity.timer` |

## Backend selection behavior

The backend should emit only references such as `pixi.scene.butterfly` or `pixi.activity.learning-goal` in the story/scene and activity handoff contracts. It must not embed SVG markup, load PixiJS, or infer a missing asset by generating one. If an asset is unavailable, return `ASSET_CATALOG_MISS` and use a declared whole-drawing/non-rendered fallback.
