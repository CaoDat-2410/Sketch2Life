# Person 4 - Learning Explanation POC

Standalone learning-media resolver, generation adapter, validation, and fallback for Sprint 1.

## Current pipeline

```text
Learning Objective
  -> Asset Library
  -> Cache-first Resolver
      -> CACHE_HIT: reviewed asset
      -> MISS: Generation Brief
          -> Mock/Wan2.2 Generator
          -> FFmpeg Frame Sampling
          -> Qwen3-VL Content Validator
              -> GENERATED
              -> RETRY
              -> FALLBACK: reviewed still+narration
              -> BLOCK
```

## Run deterministic demos

From the repository root:

```bash
python features/FEAT-005-backend-experience/scripts/run_demo.py --case cache-hit
python features/FEAT-005-backend-experience/scripts/run_demo.py --case cache-miss
python features/FEAT-005-backend-experience/scripts/run_demo.py --case fallback
python features/FEAT-005-backend-experience/scripts/run_demo.py --case block
```

The demo uses synthetic fixtures and mock providers. It does not download models, call external services, or require a GPU.

## Run phase tests

The repository runtime currently may not include pytest. The frame-sampling, content-validation, fallback, pipeline, and generation tests can run with Python's standard unittest runner:

```bash
PYTHONPATH=features/FEAT-005-backend-experience/src \
python -m unittest discover \
  -s features/FEAT-005-backend-experience/tests \
  -p 'test_*.py'
```

The schema tests use pytest assertions and require the backend development dependencies for a full pytest run.

## Scope boundary

Included: reviewed asset library, cache-first resolution, generation brief, provider adapter, frame sampling, Qwen3-VL validation policy, retry, still+narration fallback, provenance contracts, fixture demos, tests, and benchmark hooks.

Excluded from this standalone Sprint 1 POC: FastAPI, PostgreSQL, S3, Redis/RQ, mobile playback, deployment, and E2E integration.

## Next step

Replace `MockGenerator` and `MockQwen3VLValidator` with provider adapters on Lightning AI. Keep the existing contracts and pipeline unchanged.
