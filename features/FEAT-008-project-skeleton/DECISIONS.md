# FEAT-008 decisions

1. Use React Native 0.87 bare skeleton and Node 22.13+ baseline.
2. Use pnpm workspace for JavaScript/TypeScript packages.
3. Use Python 3.12 with `pyproject.toml` and a `src/` package layout.
4. Keep PixiJS/GSAP in `packages/art-renderer`, not directly inside general React Native screens.
5. Provide only a health endpoint and protocol/config placeholders; product behavior remains feature-gated.
6. Use PostgreSQL, Redis, and MinIO in local Compose infrastructure.
