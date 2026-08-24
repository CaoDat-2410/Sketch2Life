# FEAT-001 decisions

## Proposed decisions

1. Use React Native + TypeScript as the single mobile client.
2. Keep PixiJS + GSAP as a deterministic renderer inside a controlled WebView/bridge boundary for original-art animation.
3. Use a Python/FastAPI modular monolith with workers for orchestration and contracts.
4. Keep PostgreSQL, S3-compatible storage, Redis/RQ, and Docker provider-agnostic for development and later AWS deployment.
5. Run real AI models on Lightning AI, but execute development/evaluation only against fixtures/synthetic data.
6. Split MVP ownership into four workstreams with shared integration checkpoints.

## Decision pending

The project owner must approve or revise the plan before implementation begins.
