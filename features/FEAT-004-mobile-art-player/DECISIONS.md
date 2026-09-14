# FEAT-004 decisions

- The original drawing remains the source of truth for personalized art animation.
- Generated images cannot replace the child artwork.
- `DRAW_REVEAL`, transform-only, and simple fallback modes are preferred over distorted segmentation.
- Runtime code may reference only approved/applied visual assets.
- The standalone POC uses a synthetic SVG fixture solely for deterministic verification; it is not a product visual and cannot be promoted to runtime UI without the separate frontend asset gate.
- Motion-plan coordinates are normalized to the closed `[0, 1]` stage bounds, and each motion duration is limited to `[0.05, 30]` seconds before rendering.
