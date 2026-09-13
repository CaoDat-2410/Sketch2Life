# FEAT-020 Implementation Addendum

**Status:** `IN_PROGRESS`

This addendum records the implementation state after approval of the final plan. The approved scope is a backend-only, real-AI workflow demo; UI, PixiJS runtime animation, and video generation remain explicitly deferred.

## Implemented slice

- A typed backend workflow orchestrator connects media validation, Vietnamese ASR, Qwen3-VL image understanding, P1 context/experience compilation, static PixiJS asset selection, Gate A/Gate B decisions, story/scene context, deferred video output, activity handoff, feedback, and history.
- A real-adapter CLI entrypoint is available through `python -m sketch2life.workflow_demo`.
- The CLI accepts replaceable image and WAV paths, supports `--age-mode all`, supports deterministic replay with `--seed`, and writes a sanitized typed result/error manifest.
- The workflow uses the committed golden P1 catalog and the static PixiJS asset catalog. It never generates PixiJS assets during a run and never replaces the child original.
- The real-AI E2E test is opt-in through `SKETCH2LIFE_RUN_REAL_AI_E2E=1`, so CI without model weights or credentials remains safe and deterministic at the test-discovery level.

## Runtime boundary

The Lightning Studio run must provide the real Qwen3-VL and faster-whisper runtime configuration required by the existing adapters. If either runtime is unavailable, the CLI returns a typed `RUNTIME_NOT_READY` manifest rather than silently switching to fixtures or fabricated AI output.

## Evidence

- Implementation decisions: `DECISIONS_IMPLEMENTATION.md`
- Local validation record: `evidence/implementation/LOCAL_VALIDATION.md`
- Test contract: `../../backend/tests/e2e/test_lightning_backend_workflow.py`
## Latest Lightning diagnosis (2026-09-13)

The real model now loads on the L4 and reaches output mapping. The first runtime blocker was an incompatible `huggingface-hub` version; after correction, the remaining typed outcome was `VISION_SCHEMA_INVALID / OUTPUT_MAPPING_FAILED`. Safe mapper diagnostics showed type/constraint failures on entity/action/relation/theme labels and identifiers. The implementation therefore removes the unsupported `enable_thinking` processor argument and strengthens the schema-first Vietnamese prompt. The next Lightning run is required to verify the real output path after this change.
The latest safe mapping diagnostic narrowed schema invalidity to only `relations.observation_id` and `themes.observation_id`; nested labels and action fields now pass their prior checks. Prompt v3 adds concrete valid relation/theme ID examples without coercing provider output.