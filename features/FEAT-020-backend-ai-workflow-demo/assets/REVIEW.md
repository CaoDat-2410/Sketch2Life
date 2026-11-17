# FEAT-020 Asset Review Gate

**Status:** `GENERATED_PENDING_REVIEW`
**Scope:** static PixiJS asset catalog only; no PixiJS implementation.

The candidate SVGs are hand-authored vector assets in `generated/pixi/`. They are not yet approved for production/mobile reference. A future visual review must decide which files move to `approved/` and later `applied/`.

No runtime path may call AI/image generation to fill missing assets. Missing catalog entries must produce a typed catalog miss or a declared whole-drawing/non-rendered fallback.
