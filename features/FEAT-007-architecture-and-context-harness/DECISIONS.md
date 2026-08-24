# FEAT-007 decisions

1. Python backend architecture is explicitly layered as domain -> application -> contracts/interfaces/infrastructure boundaries.
2. React Native is organized by feature slices and device/API adapters; server truth remains backend-owned.
3. PixiJS/GSAP is isolated behind a versioned WebView/bridge protocol.
4. Context is stored at project level in `docs/context/` and feature level in `features/FEAT-*/CONTEXT.md`.
5. Evidence is stored only inside the owning feature's `evidence/` folder and indexed with reproducibility metadata.
